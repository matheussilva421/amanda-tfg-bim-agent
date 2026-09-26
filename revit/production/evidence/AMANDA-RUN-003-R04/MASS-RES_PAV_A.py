import json
import clr
clr.AddReference('RevitAPI')
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import StructuralType
request = json.loads('{"dry_run":false,"geometry":{"base_elevation_m":0.0,"centroid":[-13.378290946961023,37.296275834605574],"dimensions_m":[9.32820323027551,12.376379275306132],"footprint":[[-17.664101615137756,33.36181036234694],[-17.64872983946034,33.51788261995984],[-17.603205241146785,33.66795710823901],[-17.529277304979793,33.80626654876262],[-17.429787040086993,33.92749578729617],[-17.387974609408587,33.96181036234694],[-17.429787040086993,33.996124937397695],[-17.529277304979793,34.117354175931254],[-17.603205241146785,34.25566361645486],[-17.64872983946034,34.40573810473403],[-17.664101615137756,34.56181036234693],[-17.664101615137756,38.02591197748469],[-17.64872983946034,38.181984235097595],[-17.603205241146785,38.33205872337676],[-17.529277304979793,38.470368163900375],[-17.429787040086993,38.591597402433926],[-17.387974609408584,38.62591197748469],[-17.429787040086993,38.660226552535455],[-17.529277304979793,38.781455791069014],[-17.603205241146785,38.91976523159262],[-17.64872983946034,39.06983971987179],[-17.664101615137756,39.22591197748469],[-17.664101615137756,42.38818963765307],[-17.64872983946034,42.544261895265976],[-17.603205241146785,42.69433638354514],[-17.529277304979793,42.83264582406875],[-17.429787040086993,42.95387506260231],[-17.308557801553437,43.05336532749511],[-17.170248361029827,43.1272932636621],[-17.020173872750657,43.17281786197565],[-16.864101615137756,43.18818963765307],[-13.701823954969376,43.18818963765307],[-13.545751697356472,43.17281786197565],[-13.395677209077304,43.1272932636621],[-13.301823954969375,43.07712765419619],[-13.207970700861448,43.1272932636621],[-13.057896212582278,43.17281786197565],[-12.901823954969377,43.18818963765307],[-9.739546294800997,43.18818963765307],[-9.583474037188093,43.17281786197565],[-9.433399548908925,43.1272932636621],[-9.295090108385315,43.05336532749511],[-9.173860869851758,42.95387506260231],[-9.074370604958961,42.83264582406875],[-9.000442668791967,42.69433638354514],[-8.954918070478412,42.544261895265976],[-8.939546294800996,42.38818963765307],[-8.939546294800996,39.22591197748469],[-8.954918070478412,39.06983971987179],[-9.000442668791967,38.91976523159262],[-9.054873797553709,38.81793175217423],[-8.979826127249344,38.81054020180727],[-8.829751638970176,38.765015603493715],[-8.691442198446566,38.69108766732673],[-8.57021295991301,38.591597402433926],[-8.470722695020212,38.470368163900375],[-8.396794758853218,38.33205872337676],[-8.351270160539663,38.181984235097595],[-8.335898384862247,38.02591197748469],[-8.335898384862247,34.56181036234693],[-8.351270160539663,34.40573810473403],[-8.396794758853218,34.25566361645486],[-8.470722695020212,34.117354175931254],[-8.57021295991301,33.996124937397695],[-8.691442198446566,33.896634672504895],[-8.829751638970176,33.822706736337906],[-8.979826127249344,33.77718213802435],[-9.135898384862248,33.761810362346935],[-11.37516359859463,33.761810362346935],[-11.324997989128725,33.66795710823901],[-11.27947339081517,33.51788261995984],[-11.264101615137754,33.36181036234694],[-11.264101615137754,31.611810362346937],[-11.27947339081517,31.455738104734035],[-11.324997989128725,31.305663616454865],[-11.39892592529572,31.167354175931255],[-11.498416190188516,31.0461249373977],[-11.619645428722073,30.9466346725049],[-11.757954869245683,30.872706736337907],[-11.908029357524851,30.82718213802435],[-12.064101615137755,30.811810362346936],[-14.064101615137755,30.811810362346936],[-14.220173872750658,30.82718213802435],[-14.370248361029827,30.872706736337907],[-14.464101615137755,30.922872345803814],[-14.557954869245684,30.872706736337907],[-14.708029357524852,30.82718213802435],[-14.864101615137756,30.811810362346936],[-16.864101615137756,30.811810362346936],[-17.020173872750657,30.82718213802435],[-17.170248361029827,30.872706736337907],[-17.308557801553437,30.9466346725049],[-17.429787040086993,31.0461249373977],[-17.529277304979793,31.167354175931255],[-17.603205241146785,31.305663616454865],[-17.64872983946034,31.455738104734035],[-17.664101615137756,31.611810362346937]],"height_m":3.2,"interior_rings":[],"rotation_degrees":0.0,"top_elevation_m":3.2},"height_m":3.2,"idempotency_key":"8a955a23-4575-40ed-a060-4428b98de2bf","logical_id":"MASS-RES_PAV_A","properties":{"area_projection_m2":103.03851580584713,"coordinate_site_mode":"LOCAL_NORMALIZED_STUDY_NOT_SURVEYED","design_scenario":"STUDY","geometry_source":"NORMALIZED_METRIC_REFERENCE_NOT_SURVEY","height_basis":"PROVISIONAL_ASSUMPTION: 3.20m per floor for R04 visual study only","name":"MASS-RES_PAV_A","source_area_m2":103.03851580584713,"source_solution_id":"AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"},"semantic_capability":"revit.create_mass"}')
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
