import json
import clr
clr.AddReference('RevitAPI')
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import StructuralType
request = json.loads('{"dry_run":false,"geometry":{"base_elevation_m":0.0,"centroid":[12.004872330529107,36.60296827888961],"dimensions_m":[10.864101615137756,13.27722557505166],"footprint":[[7.567949192431123,42.83861278752583],[7.583320968108539,42.99468504513874],[7.628845566422093,43.144759533417904],[7.702773502589086,43.28306897394151],[7.802263767481885,43.40429821247507],[7.923493006015441,43.50378847736787],[8.061802446539051,43.57771641353486],[8.211876934818221,43.623241011848414],[8.367949192431123,43.63861278752583],[13.845174767482785,43.63861278752583],[14.001247025095688,43.623241011848414],[14.151321513374857,43.57771641353486],[14.289630953898467,43.50378847736787],[14.410860192432024,43.40429821247507],[14.51035045732482,43.28306897394151],[14.584278393491815,43.144759533417904],[14.62980299180537,42.99468504513874],[14.645174767482786,42.83861278752583],[14.645174767482786,37.36138721247417],[14.62980299180537,37.205314954861265],[14.584278393491815,37.0552404665821],[14.534112784025902,36.961387212474165],[17.632050807568877,36.961387212474165],[17.78812306518178,36.94601543679675],[17.93819755346095,36.900490838483194],[18.07650699398456,36.826562902316205],[18.197736232518114,36.727072637423404],[18.297226497410914,36.605843398889846],[18.371154433577907,36.46753395836624],[18.416679031891462,36.31745947008707],[18.432050807568878,36.16138721247417],[18.432050807568878,32.69728559733642],[18.416679031891462,32.54121333972351],[18.371154433577907,32.391138851444346],[18.297226497410914,32.25282941092074],[18.197736232518114,32.13160017238718],[18.07650699398456,32.03210990749438],[17.93819755346095,31.958181971327388],[17.78812306518178,31.912657373013833],[17.632050807568877,31.897285597336417],[14.167949192431124,31.897285597336417],[14.167949192431124,31.16138721247417],[14.152577416753708,31.00531495486127],[14.107052818440152,30.8552404665821],[14.033124882273158,30.71693102605849],[13.933634617380362,30.595701787524934],[13.812405378846805,30.496211522632134],[13.674095938323195,30.42228358646514],[13.524021450044026,30.376758988151586],[13.367949192431123,30.36138721247417],[8.367949192431123,30.36138721247417],[8.21187693481822,30.376758988151586],[8.061802446539051,30.42228358646514],[7.923493006015441,30.496211522632134],[7.802263767481885,30.595701787524934],[7.702773502589086,30.71693102605849],[7.628845566422093,30.8552404665821],[7.583320968108539,31.00531495486127],[7.567949192431123,31.16138721247417],[7.567949192431123,36.16138721247417],[7.583320968108539,36.31745947008707],[7.628845566422093,36.46753395836624],[7.702773502589086,36.605843398889846],[7.802263767481885,36.727072637423404],[7.844076198160294,36.76138721247417],[7.802263767481885,36.79570178752493],[7.702773502589086,36.91693102605849],[7.628845566422093,37.0552404665821],[7.583320968108539,37.205314954861265],[7.567949192431123,37.36138721247417]],"height_m":3.2,"interior_rings":[],"rotation_degrees":0.0,"top_elevation_m":3.2},"height_m":3.2,"idempotency_key":"1f3228e7-2829-4e3a-b23e-d0f459520e50","logical_id":"MASS-RES_PAV_D_COMMUNAL","properties":{"area_projection_m2":111.44848985981048,"coordinate_site_mode":"LOCAL_NORMALIZED_STUDY_NOT_SURVEYED","design_scenario":"STUDY","geometry_source":"NORMALIZED_METRIC_REFERENCE_NOT_SURVEY","height_basis":"PROVISIONAL_ASSUMPTION: 3.20m per floor for R04 visual study only","name":"MASS-RES_PAV_D_COMMUNAL","source_area_m2":111.44848985981048,"source_solution_id":"AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"},"semantic_capability":"revit.create_mass"}')
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
