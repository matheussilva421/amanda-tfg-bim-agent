import clr

clr.AddReference("RevitAPI")

from Autodesk.Revit.DB import (  # noqa: E402
    BuiltInCategory,
    BuiltInParameter,
    CurveLoop,
    DirectShape,
    ElementId,
    GeometryCreationUtilities,
    GeometryObject,
    Line,
    Transaction,
    TransactionStatus,
    XYZ,
)
from System.Collections.Generic import List  # noqa: E402


document = globals().get("doc") or globals().get("document") or globals().get(
    "__document__"
)
if document is None:
    raise RuntimeError("Horizun Python context did not expose the active Document")
if document.Title != "AMANDA-RUN-003-PAVILION-CANONICAL-STUDY":
    raise RuntimeError("The active document is not the RUN-003 study target")

element = document.GetElement(ElementId(328657))
if element is None or not isinstance(element, DirectShape):
    raise RuntimeError("Expected administrative DirectShape 328657 was not found")
if element.Category.Id.Value != ElementId(BuiltInCategory.OST_Mass).Value:
    raise RuntimeError("Element 328657 is not categorized as Mass")
if element.Name != "MASS-ADMIN_ACOLHIMENTO":
    raise RuntimeError("Element 328657 no longer identifies the administrative mass")

mark = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
if mark is None or mark.AsString() != "MASS-ADMIN_ACOLHIMENTO":
    raise RuntimeError("Administrative mass identity mark does not match the expected source")

millimetres_per_foot = 304.8
millimetres_to_feet = 1.0 / millimetres_per_foot


def bbox_mm(shape):
    bounds = shape.get_BoundingBox(None)
    return {
        "min": [
            float(bounds.Min.X) * millimetres_per_foot,
            float(bounds.Min.Y) * millimetres_per_foot,
            float(bounds.Min.Z) * millimetres_per_foot,
        ],
        "max": [
            float(bounds.Max.X) * millimetres_per_foot,
            float(bounds.Max.Y) * millimetres_per_foot,
            float(bounds.Max.Z) * millimetres_per_foot,
        ],
    }


before = bbox_mm(element)
expected_before = {
    "min": [-6655.034, -52918.336, 0.0],
    "max": [6655.034, -35081.664, 6400.0],
}
for side in ("min", "max"):
    for axis, expected in enumerate(expected_before[side]):
        if abs(before[side][axis] - expected) > 1.0:
            raise RuntimeError("Administrative mass changed since the P6 rehearsal")

corners_mm = [(-5000.0, -52000.0), (5000.0, -52000.0), (5000.0, -32000.0), (-5000.0, -32000.0)]
corners = [
    XYZ(x * millimetres_to_feet, y * millimetres_to_feet, 0.0)
    for x, y in corners_mm
]
profile = CurveLoop()
for index in range(len(corners)):
    profile.Append(Line.CreateBound(corners[index], corners[(index + 1) % len(corners)]))

solid = GeometryCreationUtilities.CreateExtrusionGeometry(
    List[CurveLoop]([profile]), XYZ.BasisZ, 6400.0 * millimetres_to_feet
)
shapes = List[GeometryObject]()
shapes.Add(solid)

transaction = Transaction(document, "P6-T01: reconcile administrative mass to Board 02")
transaction.Start()
try:
    element.SetShape(shapes)
    transaction.Commit()
finally:
    if transaction.GetStatus() == TransactionStatus.Started:
        transaction.RollBack()

after = bbox_mm(element)
expected_after = {
    "min": [-5000.0, -52000.0, 0.0],
    "max": [5000.0, -32000.0, 6400.0],
}
for side in ("min", "max"):
    for axis, expected in enumerate(expected_after[side]):
        if abs(after[side][axis] - expected) > 0.1:
            raise RuntimeError("DirectShape geometry did not match the requested 10 x 20 m envelope")

__output__ = {
    "status": "self_reported_verified",
    "summary": "Updated the existing administrative mass footprint to 10 x 20 m while preserving its id and 6.4 m study height.",
    "created_ids": [],
    "modified_ids": [int(element.Id.Value)],
    "deleted_ids": [],
    "verification": {
        "checked": True,
        "evidence": [
            "same element id and unique id retained",
            "category=Mass and mark=MASS-ADMIN_ACOLHIMENTO",
            "x bounds=-5000..5000 mm",
            "y bounds=-52000..-32000 mm",
            "z bounds=0..6400 mm",
            "transaction committed",
        ],
    },
    "warnings": [],
}
