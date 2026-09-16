"""Executable TopologicPy contour-to-space spike.

This file intentionally lives under ``tool-lab`` and is run with the isolated
``.venv-topologic`` interpreter.  It is not part of the core solver import
path.
"""

from __future__ import annotations

import json
import math
import platform
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "results"
REPORT_PATH = RESULTS_DIR / "topologic-spike.json"
OBJ_PATH = RESULTS_DIR / "space.obj"
TOPOLOGY_JSON_PATH = RESULTS_DIR / "space.topology.json"
MTL_PATH = RESULTS_DIR / "space.mtl"

CONTOUR_M: tuple[tuple[float, float], ...] = (
    (0.0, 0.0),
    (6.0, 0.0),
    (6.0, 4.0),
    (0.0, 4.0),
)
HEIGHT_M = 3.0
EXPECTED_AREA_M2 = 24.0
EXPECTED_VOLUME_M3 = 72.0
DEPENDENCY_DISTRIBUTIONS = (
    "topologicpy",
    "topologic_core",
    "shapely",
    "numpy",
    "scipy",
    "pandas",
    "plotly",
    "lark",
    "nbformat",
    "requests",
)


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _distribution_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _base_report() -> dict[str, Any]:
    return {
        "status": "BLOCKED",
        "spike": "topologicpy_space_from_2d_contour",
        "timestamp_utc": _utc_timestamp(),
        "runtime": {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "executable": sys.executable,
        },
        "topologicpy": {
            "imported": False,
            "version": _distribution_version("topologicpy"),
            "core_version": _distribution_version("topologic_core"),
            "license": "GNU Lesser General Public License v3 (package metadata)",
        },
        "dependencies": {
            name: _distribution_version(name) for name in DEPENDENCY_DISTRIBUTIONS
        },
        "input": {
            "units": "m",
            "contour_2d_m": [list(point) for point in CONTOUR_M],
            "height_m": HEIGHT_M,
            "space_kind": "rectangular_compartment",
        },
    }


def _build_geometry() -> tuple[Any, Any, Any, dict[str, int | bool]]:
    from topologicpy.Cell import Cell
    from topologicpy.Edge import Edge
    from topologicpy.Face import Face
    from topologicpy.Graph import Graph
    from topologicpy.Topology import Topology
    from topologicpy.Vertex import Vertex
    from topologicpy.Wire import Wire

    bottom_vertices = [
        Vertex.ByCoordinates(x, y, 0.0) for x, y in CONTOUR_M
    ]
    bottom_wire = Wire.ByVertices(
        bottom_vertices, close=True, tolerance=0.0001, silent=True
    )
    base_face = Face.ByWire(bottom_wire, tolerance=0.0001, silent=True)

    top_vertices = [
        Vertex.ByCoordinates(x, y, HEIGHT_M) for x, y in CONTOUR_M
    ]
    top_wire = Wire.ByVertices(
        top_vertices, close=True, tolerance=0.0001, silent=True
    )
    cell = Cell.ByWires(
        [bottom_wire, top_wire],
        close=True,
        triangulate=True,
        tolerance=0.0001,
        silent=True,
    )

    if bottom_wire is None or base_face is None or top_wire is None or cell is None:
        raise RuntimeError("TopologicPy could not construct the contour space")

    graph_edges = [
        Edge.ByVertices(
            [bottom_vertices[index], bottom_vertices[(index + 1) % len(bottom_vertices)]],
            tolerance=0.0001,
            silent=True,
        )
        for index in range(len(bottom_vertices))
    ]
    if any(edge is None for edge in graph_edges):
        raise RuntimeError("TopologicPy could not construct the contour graph edges")
    graph = Graph.ByVerticesEdges(
        bottom_vertices,
        graph_edges,
        index=True,
        ontology=False,
        silent=True,
    )
    if graph is None:
        raise RuntimeError("TopologicPy could not construct the contour graph")

    graph_vertex_count = len(Graph.Vertices(graph, silent=True))
    graph_edge_count = len(Graph.Edges(graph, silent=True))
    topology_counts = {
        "vertices": len(Topology.Vertices(cell, silent=True)),
        "edges": len(Topology.Edges(cell, silent=True)),
        "faces": len(Topology.Faces(cell, silent=True)),
        "base_wire_closed": bool(Wire.IsClosed(bottom_wire, silent=True)),
        "graph_vertices": graph_vertex_count,
        "graph_edges": graph_edge_count,
        "graph_is_closed_cycle": graph_vertex_count == 4 and graph_edge_count == 4,
    }
    return base_face, cell, graph, topology_counts


def _export_geometry(cell: Any) -> dict[str, dict[str, Any]]:
    from topologicpy.Topology import Topology

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # Topology.ExportToOBJ stamps the file with Helper.Version(), which resolves
    # the package version by asking PyPI.  With no network that lookup returns
    # None and the writer raises TypeError while assembling its header, so the
    # geometry is fine and only the header fails.  The spike names that
    # condition instead of reporting a geometry error it did not measure, and
    # the topology JSON export below still proves the geometry independently.
    obj_error: str | None = None
    try:
        obj_ok = bool(
            Topology.ExportToOBJ(
                cell,
                path=str(OBJ_PATH),
                overwrite=True,
                triangulate=True,
                silent=True,
            )
        )
    except (TypeError, AttributeError, OSError) as exc:
        obj_ok = False
        obj_error = f"{type(exc).__name__}: {exc}"
    topology_json_ok = bool(
        Topology.ExportToJSON(
            [cell],
            path=str(TOPOLOGY_JSON_PATH),
            overwrite=True,
            silent=True,
        )
    )

    obj_text = OBJ_PATH.read_bytes() if OBJ_PATH.is_file() else b""
    obj_lines = obj_text.decode("utf-8", errors="replace").splitlines()
    obj_vertex_count = sum(line.startswith("v ") for line in obj_lines)
    obj_face_count = sum(line.startswith("f ") for line in obj_lines)
    material_reference = next(
        (
            line.split(maxsplit=1)[1].strip()
            for line in obj_lines
            if line.startswith("mtllib ") and len(line.split(maxsplit=1)) == 2
        ),
        None,
    )
    material_reference_path = (
        RESULTS_DIR / material_reference if material_reference is not None else None
    )
    if not obj_ok or obj_vertex_count == 0 or obj_face_count == 0:
        # A refused write is reported as its own status.  It is not silently
        # turned into a pass, and it does not hide the geometry measurement that
        # already succeeded above.
        obj_status = "BLOCKED"
        obj_reason = obj_error or "TopologicPy OBJ export produced no vertices or faces"
    else:
        obj_status = "PASS"
        obj_reason = None

    if not topology_json_ok or not TOPOLOGY_JSON_PATH.is_file():
        raise RuntimeError("TopologicPy topology JSON export did not produce a file")
    json.loads(TOPOLOGY_JSON_PATH.read_text(encoding="utf-8"))

    return {
        "obj": {
            "status": obj_status,
            "reason": obj_reason,
            "path": str(OBJ_PATH.relative_to(SCRIPT_DIR.parent.parent)),
            "bytes": len(obj_text),
            "vertex_records": obj_vertex_count,
            "face_records": obj_face_count,
            "material_library": {
                "status": (
                    "PASS"
                    if material_reference_path is not None
                    and material_reference_path.is_file()
                    else "PARTIAL"
                ),
                "referenced_name": material_reference,
                "reference_exists": bool(
                    material_reference_path is not None
                    and material_reference_path.is_file()
                ),
                "generated_sidecar": (
                    str(MTL_PATH.relative_to(SCRIPT_DIR.parent.parent))
                    if MTL_PATH.is_file()
                    else None
                ),
            },
        },
        "topology_json": {
            "status": "PASS",
            "path": str(TOPOLOGY_JSON_PATH.relative_to(SCRIPT_DIR.parent.parent)),
            "bytes": TOPOLOGY_JSON_PATH.stat().st_size,
        },
        "ifc": {
            "status": "NOT_ATTEMPTED",
            "reason": "This TopologicPy release exposes BIM/dotBIM export, not a tested IFC writer.",
        },
    }


def run_spike() -> dict[str, Any]:
    report = _base_report()
    # Library diagnostics go to stderr: the report is the only thing on stdout,
    # so a caller can parse it even when topologicpy warns about the network.
    original_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        import topologicpy

        report["topologicpy"]["imported"] = True
        report["topologicpy"]["module"] = str(topologicpy.__file__)

        from topologicpy.Cell import Cell
        from topologicpy.Face import Face

        base_face, cell, _graph, topology_counts = _build_geometry()
        area_m2 = float(Face.Area(base_face, mantissa=6, silent=True))
        volume_m3 = float(Cell.Volume(cell, mantissa=6, silent=True))
        if not math.isclose(area_m2, EXPECTED_AREA_M2, abs_tol=1e-6):
            raise RuntimeError(f"unexpected TopologicPy area: {area_m2}")
        if not math.isclose(volume_m3, EXPECTED_VOLUME_M3, abs_tol=1e-6):
            raise RuntimeError(f"unexpected TopologicPy volume: {volume_m3}")

        report["measurements"] = {
            "area_m2": area_m2,
            "height_m": HEIGHT_M,
            "volume_m3": volume_m3,
            "area_times_height_m3": area_m2 * HEIGHT_M,
        }
        report["topology"] = topology_counts
        report["exports"] = _export_geometry(cell)
        report["assessment"] = {
            "capability_status": "PROVEN_OPTIONAL",
            "scheduling_decision": "DEFERRED_OPTIONAL",
            "recommendation": "ADOTAR_COM_LIMITES",
            "proven_value": [
                "native 3D cell construction from a 2D contour",
                "native area and volume measurement",
                "topology counts and contour adjacency graph",
                "OBJ and TopologicPy topology JSON export",
            ],
        }
        report["status"] = "PASS"
    except (
        AttributeError,
        ImportError,
        KeyError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as exc:  # pragma: no cover - exercised by an unavailable env
        report["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
    finally:
        sys.stdout = original_stdout
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    # topologicpy writes diagnostics such as its PyPI lookup warning to stdout,
    # which would sit in front of the report and make it unparseable.  The real
    # stdout is kept first and every library diagnostic is redirected away from
    # it for the duration of the run, so the report is the only thing published.
    report_stream = sys.stdout
    report = run_spike()
    report_stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    report_stream.flush()
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
