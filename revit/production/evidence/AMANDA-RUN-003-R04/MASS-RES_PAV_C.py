import json
import clr
clr.AddReference('RevitAPI')
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import StructuralType
request = json.loads('{"dry_run":false,"geometry":{"base_elevation_m":0.0,"centroid":[12.601975571155082,7.494546838761182],"dimensions_m":[9.864101615137756,8.921320343559643],"footprint":[[8.067949192431122,5.46066017177982],[8.083320968108538,5.616732429392723],[8.128845566422093,5.766806917671892],[8.202773502589087,5.905116358195502],[8.302263767481884,6.026345596729058],[8.423493006015441,6.125835861621857],[8.561802446539051,6.19976379778885],[8.711876934818221,6.245288396102405],[8.867949192431123,6.26066017177982],[10.867949192431123,6.26066017177982],[11.024021450044026,6.245288396102405],[11.174095938323195,6.19976379778885],[11.267949192431123,6.149598188322943],[11.361802446539052,6.19976379778885],[11.511876934818222,6.245288396102405],[11.667949192431124,6.26066017177982],[12.443112791025754,6.26066017177982],[12.392947181559848,6.354513425887749],[12.378796313214933,6.401162587093785],[12.332050807568876,6.3965585566420655],[8.867949192431123,6.3965585566420655],[8.71187693481822,6.411930332319481],[8.561802446539051,6.457454930633036],[8.423493006015441,6.531382866800029],[8.302263767481884,6.6308731316928275],[8.202773502589086,6.752102370226384],[8.128845566422093,6.890411810749994],[8.083320968108538,7.040486299029163],[8.067949192431122,7.196558556642065],[8.067949192431122,10.66066017177982],[8.083320968108538,10.816732429392724],[8.128845566422093,10.966806917671892],[8.202773502589087,11.105116358195502],[8.302263767481884,11.22634559672906],[8.423493006015441,11.325835861621856],[8.561802446539051,11.39976379778885],[8.711876934818221,11.445288396102406],[8.867949192431123,11.460660171779821],[12.332050807568876,11.460660171779821],[12.48812306518178,11.445288396102406],[12.638197553460948,11.39976379778885],[12.732050807568877,11.349598188322943],[12.825904061676805,11.39976379778885],[12.975978549955975,11.445288396102406],[13.132050807568877,11.460660171779821],[17.132050807568877,11.460660171779821],[17.28812306518178,11.445288396102406],[17.43819755346095,11.39976379778885],[17.57650699398456,11.325835861621856],[17.697736232518114,11.22634559672906],[17.797226497410914,11.105116358195502],[17.871154433577907,10.966806917671892],[17.916679031891462,10.816732429392724],[17.932050807568878,10.66066017177982],[17.932050807568878,6.660660171779821],[17.916679031891462,6.504587914166918],[17.871154433577907,6.354513425887749],[17.797226497410914,6.216203985364139],[17.697736232518114,6.094974746830583],[17.57650699398456,5.995484481937784],[17.43819755346095,5.921556545770791],[17.28812306518178,5.8760319474572364],[17.132050807568877,5.860660171779821],[14.478207552533888,5.860660171779821],[14.528373161999795,5.766806917671892],[14.57389776031335,5.616732429392723],[14.589269535990766,5.46066017177982],[14.589269535990766,3.3393398282201776],[14.57389776031335,3.183267570607275],[14.528373161999795,3.033193082328106],[14.454445225832801,2.894883641804496],[14.354954960940004,2.7736544032709394],[14.233725722406447,2.674164138378141],[14.095416281882837,2.600236202211148],[13.945341793603669,2.5547116038975934],[13.789269535990766,2.539339828220178],[11.667949192431124,2.539339828220178],[11.51187693481822,2.5547116038975934],[11.361802446539052,2.6002362022111485],[11.223493006015442,2.674164138378141],[11.102263767481885,2.77365440327094],[11.002773502589086,2.894883641804496],[10.98801969007297,2.922486083594359],[10.867949192431123,2.9106601717798206],[8.867949192431123,2.9106601717798206],[8.71187693481822,2.9260319474572363],[8.561802446539051,2.9715565457707913],[8.423493006015441,3.045484481937784],[8.302263767481884,3.1449747468305826],[8.202773502589086,3.2662039853641387],[8.128845566422093,3.4045134258877487],[8.083320968108538,3.554587914166918],[8.067949192431122,3.7106601717798204]],"height_m":3.2,"interior_rings":[],"rotation_degrees":0.0,"top_elevation_m":3.2},"height_m":3.2,"idempotency_key":"e0a44f70-067f-4715-828b-e250a8883791","logical_id":"MASS-RES_PAV_C","properties":{"area_projection_m2":74.08684873079702,"coordinate_site_mode":"LOCAL_NORMALIZED_STUDY_NOT_SURVEYED","design_scenario":"STUDY","geometry_source":"NORMALIZED_METRIC_REFERENCE_NOT_SURVEY","height_basis":"PROVISIONAL_ASSUMPTION: 3.20m per floor for R04 visual study only","name":"MASS-RES_PAV_C","source_area_m2":74.08684873079702,"source_solution_id":"AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"},"semantic_capability":"revit.create_mass"}')
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
