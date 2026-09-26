import json
import clr
clr.AddReference('RevitAPI')
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import StructuralType
request = json.loads('{"dry_run":false,"geometry":{"base_elevation_m":0.0,"centroid":[-13.71871783955378,7.385430665906449],"dimensions_m":[11.442640687119287,10.915624033326704],"footprint":[[-18.721320343559643,6.584828670455935],[-18.705948567882228,6.740900928068838],[-18.660423969568672,6.890975416348007],[-18.58649603340168,7.029284856871617],[-18.48700576850888,7.150514095405173],[-18.445193337830474,7.184828670455935],[-18.48700576850888,7.2191432455066975],[-18.58649603340168,7.3403724840402536],[-18.660423969568672,7.478681924563864],[-18.705948567882228,7.628756412843033],[-18.721320343559643,7.784828670455935],[-18.721320343559643,11.657812016663351],[-18.705948567882228,11.813884274276255],[-18.660423969568672,11.963958762555423],[-18.58649603340168,12.102268203079033],[-18.48700576850888,12.22349744161259],[-18.365776529975324,12.322987706505387],[-18.227467089451714,12.396915642672381],[-18.077392601172544,12.442440240985936],[-17.921320343559643,12.457812016663352],[-14.048336997352227,12.457812016663352],[-13.892264739739323,12.442440240985936],[-13.742190251460155,12.396915642672381],[-13.648336997352226,12.346750033206474],[-13.554483743244298,12.396915642672381],[-13.404409254965127,12.442440240985936],[-13.248336997352226,12.457812016663352],[-9.37535365114481,12.457812016663352],[-9.219281393531906,12.442440240985936],[-9.069206905252738,12.396915642672381],[-8.930897464729128,12.322987706505387],[-8.809668226195571,12.22349744161259],[-8.710177961302774,12.102268203079033],[-8.63625002513578,11.963958762555423],[-8.590725426822225,11.813884274276255],[-8.575353651144809,11.657812016663351],[-8.575353651144809,7.784828670455935],[-8.590725426822225,7.628756412843033],[-8.63625002513578,7.478681924563864],[-8.686415634601687,7.384828670455935],[-8.078679656440357,7.384828670455935],[-7.922607398827455,7.369456894778519],[-7.772532910548286,7.323932296464965],[-7.634223470024676,7.250004360297972],[-7.51299423149112,7.150514095405173],[-7.413503966598321,7.029284856871617],[-7.339576030431328,6.890975416348007],[-7.294051432117773,6.740900928068838],[-7.2786796564403575,6.584828670455935],[-7.2786796564403575,4.834828670455935],[-7.294051432117773,4.678756412843033],[-7.339576030431328,4.528681924563863],[-7.413503966598321,4.390372484040253],[-7.51299423149112,4.269143245506697],[-7.634223470024676,4.169652980613899],[-7.772532910548286,4.0957250444469055],[-7.922607398827455,4.050200446133351],[-8.078679656440357,4.034828670455935],[-10.078679656440357,4.034828670455935],[-10.23475191405326,4.050200446133351],[-10.384826402332429,4.0957250444469055],[-10.478679656440358,4.145890653912812],[-10.572532910548286,4.0957250444469055],[-10.722607398827455,4.050200446133351],[-10.878679656440358,4.034828670455935],[-12.878679656440358,4.034828670455935],[-12.878679656440358,2.3421879833366486],[-12.894051432117774,2.186115725723746],[-12.93957603043133,2.036041237444577],[-13.013503966598323,1.8977317969209668],[-13.11299423149112,1.7765025583874103],[-13.234223470024677,1.6770122934946123],[-13.372532910548287,1.603084357327619],[-13.522607398827455,1.5575597590140642],[-13.678679656440359,1.5421879833366485],[-17.921320343559643,1.5421879833366485],[-18.077392601172544,1.5575597590140644],[-18.227467089451714,1.6030843573276194],[-18.365776529975324,1.6770122934946123],[-18.48700576850888,1.7765025583874106],[-18.58649603340168,1.897731796920967],[-18.660423969568672,2.036041237444577],[-18.705948567882228,2.186115725723746],[-18.721320343559643,2.3421879833366486]],"height_m":3.2,"interior_rings":[],"rotation_degrees":0.0,"top_elevation_m":3.2},"height_m":3.2,"idempotency_key":"46c38285-0f6f-4c28-9d24-3caff25baffc","logical_id":"MASS-RES_PAV_B","properties":{"area_projection_m2":103.34521690854359,"coordinate_site_mode":"LOCAL_NORMALIZED_STUDY_NOT_SURVEYED","design_scenario":"STUDY","geometry_source":"NORMALIZED_METRIC_REFERENCE_NOT_SURVEY","height_basis":"PROVISIONAL_ASSUMPTION: 3.20m per floor for R04 visual study only","name":"MASS-RES_PAV_B","source_area_m2":103.34521690854359,"source_solution_id":"AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"},"semantic_capability":"revit.create_mass"}')
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
