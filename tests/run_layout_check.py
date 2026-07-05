from __future__ import annotations

import json
import sys
from pathlib import Path

import gdspy


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from layout import build_layout_geometry, write_layout_artifacts
from design import ResonatorBaseline


def combined_bbox(polygons: list) -> tuple[float, float, float, float]:
    x_min = min(polygon[:, 0].min() for polygon in polygons)
    x_max = max(polygon[:, 0].max() for polygon in polygons)
    y_min = min(polygon[:, 1].min() for polygon in polygons)
    y_max = max(polygon[:, 1].max() for polygon in polygons)
    return x_min, x_max, y_min, y_max


def main() -> int:
    summary = write_layout_artifacts()
    gds_path = Path(summary["gds_path"])
    svg_path = Path(summary["svg_path"])
    json_path = Path(summary["json_path"])

    assert gds_path.exists(), gds_path
    assert svg_path.exists(), svg_path
    assert json_path.exists(), json_path

    library = gdspy.GdsLibrary(infile=str(gds_path))
    cell = library.top_level()[0]
    polygons_by_spec = cell.get_polygons(by_spec=True)

    bus_polygons = polygons_by_spec[(1, 0)]
    ring_polygons = polygons_by_spec[(2, 0)]

    bus_x_min, bus_x_max, bus_y_min, bus_y_max = combined_bbox(bus_polygons)
    ring_x_min, ring_x_max, ring_y_min, ring_y_max = combined_bbox(ring_polygons)

    design = ResonatorBaseline()
    geometry = build_layout_geometry(design=design)

    assert abs((bus_x_max - bus_x_min) - geometry.bus_length_um) < 0.05
    assert abs((bus_y_max - bus_y_min) - geometry.bus_width_um) < 0.05
    expected_ring_span_x_um = (
        2.0 * geometry.outer_ring_radius_um
        + (geometry.ring_count - 1)
        * (2.0 * geometry.outer_ring_radius_um + geometry.ring_to_ring_gap_um)
    )
    expected_ring_span_y_um = (
        2.0 * geometry.outer_ring_radius_um
        + (geometry.ring_row_count - 1)
        * (2.0 * geometry.outer_ring_radius_um + geometry.ring_row_gap_um)
    )
    assert abs((ring_x_max - ring_x_min) - expected_ring_span_x_um) < 0.1
    assert abs((ring_y_max - ring_y_min) - expected_ring_span_y_um) < 0.1
    assert abs(0.5 * (ring_y_max + ring_y_min) - sum(geometry.ring_center_y_ums) / len(geometry.ring_center_y_ums)) < 0.05
    assert ring_y_min > bus_y_max
    assert abs(ring_y_min - bus_y_max - geometry.ring_gap_um) < 0.05
    assert len(ring_polygons) >= geometry.ring_count * geometry.ring_row_count

    with json_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    assert manifest["bus_length_um"] == geometry.bus_length_um
    assert manifest["ring_count"] == geometry.ring_count
    assert abs(manifest["ring_radius_um"] - geometry.ring_radius_um) < 1e-12

    print(f"GDS written to {gds_path}")
    print(f"SVG preview written to {svg_path}")
    print("Layout check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
