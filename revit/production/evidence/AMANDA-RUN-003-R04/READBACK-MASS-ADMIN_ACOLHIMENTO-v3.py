import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import ElementId, Options, PlanarFace, Solid

document = globals().get('doc') or globals().get('document') or globals().get('__document__')
if document is None:
    raise RuntimeError('Horizun Python context did not expose the active Document')
expected_element_id = 328657
element = document.GetElement(ElementId(expected_element_id))
if element is None:
    raise RuntimeError('mass geometry readback could not find the written element')

M_TO_FT = 3.280839895013123
solids = [
    item for item in element.get_Geometry(Options())
    if isinstance(item, Solid) and item.Faces.Size > 0
]
if len(solids) != 1:
    raise RuntimeError('mass geometry readback requires exactly one non-empty solid')
horizontal_faces = [
    face for face in solids[0].Faces
    if isinstance(face, PlanarFace)
    and abs(abs(face.FaceNormal.Z) - 1.0) < 1e-8
]
if len(horizontal_faces) < 2:
    raise RuntimeError('mass geometry readback found no horizontal base and top faces')

bottom_face = min(horizontal_faces, key=lambda face: face.Origin.Z)
top_face = max(horizontal_faces, key=lambda face: face.Origin.Z)
base_elevation_m = float(bottom_face.Origin.Z) / M_TO_FT
height_m = (float(top_face.Origin.Z) - float(bottom_face.Origin.Z)) / M_TO_FT
if height_m <= 0:
    raise RuntimeError('mass geometry readback returned a non-positive extrusion height')

rings = []
for curve_loop in bottom_face.GetEdgesAsCurveLoops():
    ring = []
    for curve in curve_loop:
        for point in curve.Tessellate():
            xy = [float(point.X) / M_TO_FT, float(point.Y) / M_TO_FT]
            if not ring or abs(ring[-1][0] - xy[0]) > 1e-9 or abs(ring[-1][1] - xy[1]) > 1e-9:
                ring.append(xy)
    if len(ring) < 3:
        raise RuntimeError('mass geometry readback found an incomplete profile ring')
    if abs(ring[0][0] - ring[-1][0]) > 1e-9 or abs(ring[0][1] - ring[-1][1]) > 1e-9:
        ring.append(list(ring[0]))
    if len(ring) < 4:
        raise RuntimeError('mass geometry readback found a degenerate closed profile ring')
    rings.append(ring)

def signed_area(ring):
    return sum(
        ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
        for i in range(len(ring) - 1)
    ) / 2.0

def canonical_ring(ring, clockwise):
    points = ring[:-1]
    if (signed_area(ring) < 0) != clockwise:
        points = list(reversed(points))
    start = min(
        range(len(points)),
        key=lambda index: (points[index][0], points[index][1]),
    )
    points = points[start:] + points[:start]
    return points + [list(points[0])]

if not rings:
    raise RuntimeError('mass geometry readback returned no profile rings')
rings.sort(key=lambda ring: abs(signed_area(ring)), reverse=True)
footprint = canonical_ring(rings[0], False)
interior_rings = [canonical_ring(ring, True) for ring in rings[1:]]
interior_rings.sort(key=lambda ring: (ring[0][0], ring[0][1]))
__output__ = {
    'status': 'self_reported_verified',
    'element_id': int(element.Id.Value),
    'unique_id': str(element.UniqueId),
    'geometry': {
        'footprint': footprint,
        'interior_rings': interior_rings,
        'base_elevation_m': base_elevation_m,
        'height_m': height_m,
    },
    'verification': {
        'checked': True,
        'evidence': [
            'element_id=%s' % int(element.Id.Value),
            'unique_id=%s' % str(element.UniqueId),
            'non_empty_solid_count=%s' % len(solids),
            'profile_ring_count=%s' % len(rings),
            'base_elevation_m=%s' % base_elevation_m,
            'height_m=%s' % height_m,
        ],
    },
}
