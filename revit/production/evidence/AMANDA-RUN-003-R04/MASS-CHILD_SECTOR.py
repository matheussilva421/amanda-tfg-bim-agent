import json
import clr
clr.AddReference('RevitAPI')
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import StructuralType
request = json.loads('{"dry_run":false,"geometry":{"base_elevation_m":0.0,"centroid":[-33.0,-10.0],"dimensions_m":[10.441620172685639,9.048469228349536],"footprint":[[-27.779189913657184,-14.524234614174768],[-27.779189913657184,-5.475765385825232],[-38.22081008634282,-5.475765385825232],[-38.22081008634282,-14.524234614174768]],"height_m":3.2,"interior_rings":[],"rotation_degrees":0.0,"top_elevation_m":3.2},"height_m":3.2,"idempotency_key":"d073c793-f45f-414e-80f1-11798c33c63d","logical_id":"MASS-CHILD_SECTOR","properties":{"area_projection_m2":94.48067882665977,"coordinate_site_mode":"LOCAL_NORMALIZED_STUDY_NOT_SURVEYED","design_scenario":"STUDY","geometry_source":"NORMALIZED_METRIC_REFERENCE_NOT_SURVEY","height_basis":"PROVISIONAL_ASSUMPTION: 3.20m per floor for R04 visual study only","name":"MASS-CHILD_SECTOR","source_area_m2":94.48067882665977,"source_solution_id":"AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"},"semantic_capability":"revit.create_mass"}')
logical_id = request['logical_id']
semantic_capability = request['semantic_capability']
geometry = request.get('geometry') or {}
properties = request.get('properties') or {}
M_TO_FT = 3.280839895013123
def element_id_value(element_id):
    return int(element_id.Value)
def property_value(name, default=None):
    return properties.get(name, request.get(name, default))
def to_xyz(value):
    values = list(value)
    while len(values) < 3:
        values.append(0.0)
    return XYZ(float(values[0]) * M_TO_FT, float(values[1]) * M_TO_FT, float(values[2]) * M_TO_FT)
def metric_box(origin, width_m, depth_m, height_m):
    p = to_xyz(origin)
    x = float(width_m) * M_TO_FT
    y = float(depth_m) * M_TO_FT
    z = max(float(height_m) * M_TO_FT, 0.001)
    loop = CurveLoop()
    loop.Append(Line.CreateBound(p, p + XYZ(x, 0, 0)))
    loop.Append(Line.CreateBound(p + XYZ(x, 0, 0), p + XYZ(x, y, 0)))
    loop.Append(Line.CreateBound(p + XYZ(x, y, 0), p + XYZ(0, y, 0)))
    loop.Append(Line.CreateBound(p + XYZ(0, y, 0), p))
    return GeometryCreationUtilities.CreateExtrusionGeometry(List[CurveLoop]([loop]), XYZ.BasisZ, z)
def make_direct_shape(category, solid):
    shape = DirectShape.CreateElement(document, ElementId(category))
    shapes = List[GeometryObject]()
    shapes.Add(solid)
    shape.SetShape(shapes)
    return shape
def built_in_parameter(element, built_in):
    # The bridge projects some document elements as plain Element, Material
    # or View, and those projections carry no get_Parameter attribute; an
    # unguarded read killed every Python route with AttributeError.
    reader = getattr(element, 'get_Parameter', None)
    if reader is None:
        return None
    try:
        return reader(built_in)
    except Exception:
        return None
def built_in_string(element, built_in):
    parameter = built_in_parameter(element, built_in)
    if parameter is None:
        return None
    try:
        return parameter.AsString()
    except Exception:
        return None
def set_mark(element):
    parameter = built_in_parameter(element, BuiltInParameter.ALL_MODEL_MARK)
    if parameter is not None and not parameter.IsReadOnly:
        parameter.Set(logical_id)
def set_name(element, value):
    if value is None:
        return
    try:
        element.Name = str(value)
    except Exception:
        pass
document = globals().get('doc') or globals().get('document') or globals().get('__document__')
if document is None:
    raise RuntimeError('Horizun Python context did not expose the active Document')
existing = []
if semantic_capability != 'revit.assign_material':
    expected_name = property_value('view_name') or property_value('sheet_id') or property_value('table_name') or property_value('name')
    for candidate in FilteredElementCollector(document).WhereElementIsNotElementType():
        marked = built_in_string(candidate, BuiltInParameter.ALL_MODEL_MARK) == logical_id
        named = expected_name is not None and hasattr(candidate, 'Name') and candidate.Name == str(expected_name)
        if marked or named:
            existing.append(candidate)
if existing:
    __output__ = {'status': 'self_reported_verified', 'logical_id': logical_id, 'element_id': element_id_value(existing[0].Id), 'created': False, 'semantic_capability': semantic_capability}
else:
    transaction = Transaction(document, 'Amanda ' + semantic_capability + ' ' + logical_id)
    transaction.Start()
    try:
        created = None
        created_id = None
        mark_created = True
        footprint = geometry.get('footprint')
        interior_rings = geometry.get('interior_rings') or []
        base_elevation_m = float(geometry.get('base_elevation_m') or 0.0)

        def mass_xyz(value):
            point = to_xyz(value)
            return XYZ(point.X, point.Y, point.Z + base_elevation_m * M_TO_FT)

        if footprint:
            profile_rings = [footprint, *interior_rings]
        else:
            profile = geometry.get('profile')
            if profile and profile[0] and isinstance(profile[0][0], (list, tuple)):
                profile_rings = profile
            else:
                profile_rings = [profile] if profile else []
        if not profile_rings or any(not ring or len(ring) < 3 for ring in profile_rings):
            raise ValueError('create_mass requires a closed metric footprint')
        profile_loops = List[CurveLoop]()
        for ring in profile_rings:
            loop = CurveLoop()
            for index in range(len(ring)):
                            loop.Append(Line.CreateBound(mass_xyz(ring[index]), mass_xyz(ring[(index + 1) % len(ring)])))
            profile_loops.Add(loop)
        height_m = float(geometry.get('height_m') or geometry.get('height') or request.get('height_m') or 0.01)
        if height_m <= 0:
            raise ValueError('create_mass height must be positive')
        solid = GeometryCreationUtilities.CreateExtrusionGeometry(profile_loops, XYZ.BasisZ, height_m * M_TO_FT)
        created = make_direct_shape(BuiltInCategory.OST_Mass, solid)
        set_name(created, property_value('name', logical_id))
        if created is None:
            raise RuntimeError('route did not create a Revit element')
        if mark_created:
            set_mark(created)
        if created_id is None:
            created_id = element_id_value(created.Id)
        transaction.Commit()
    finally:
        if transaction.GetStatus() == TransactionStatus.Started:
            transaction.RollBack()
    __output__ = {'status': 'self_reported_verified', 'logical_id': logical_id, 'element_id': created_id, 'created': True, 'semantic_capability': semantic_capability}
