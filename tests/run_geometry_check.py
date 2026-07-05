from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import meep as mp

from geometry import (
    SimulationSpec,
    build_meep_simulation,
    build_simulation_geometry,
    write_geometry_artifacts,
)
from design import MaterialModel, ResonatorBaseline


def main() -> int:
    design = ResonatorBaseline()
    spec = SimulationSpec()
    simulation, geometry = build_meep_simulation(design=design, spec=spec)
    summary = write_geometry_artifacts(design=design, spec=spec)

    preview_path = Path(summary["preview_png_path"])
    json_path = Path(summary["summary_json_path"])

    assert preview_path.exists(), preview_path
    assert json_path.exists(), json_path

    expected_geometry = build_simulation_geometry(design=design, spec=spec)
    materials = MaterialModel()

    assert abs(geometry.cell_size_x_um - expected_geometry.cell_size_x_um) < 1e-12
    assert abs(geometry.cell_size_y_um - expected_geometry.cell_size_y_um) < 1e-12
    assert geometry.bus_width_um == design.waveguide_width_um
    assert geometry.waveguide_center_y_um == -5.0
    assert abs(geometry.bus_right_x_um - (0.5 * geometry.cell_size_x_um - geometry.pml_thickness_um)) < 1e-12
    assert geometry.bus_left_x_um < min(geometry.ring_center_x_ums)
    assert min(geometry.ring_center_y_ums) > geometry.waveguide_center_y_um
    assert geometry.cell_size_x_um > geometry.bus_length_um
    assert geometry.cell_size_y_um > max(geometry.ring_center_y_ums) - geometry.waveguide_center_y_um

    assert len(simulation.geometry) == 1 + 2 * design.ring_count * design.ring_row_count
    assert simulation.resolution == spec.resolution
    assert simulation.cell_size.x == geometry.cell_size_x_um
    assert simulation.cell_size.y == geometry.cell_size_y_um

    bus = simulation.geometry[0]
    assert isinstance(bus, mp.Block)
    assert abs(bus.center.x - geometry.bus_center_x_um) < 1e-12
    assert abs(bus.size.x - geometry.bus_length_um) < 1e-12
    assert abs(bus.size.y - design.waveguide_width_um) < 1e-12
    for index, (ring_center_x_um, ring_center_y_um) in enumerate(geometry.ring_centers_um):
        ring_outer = simulation.geometry[1 + 2 * index]
        ring_inner = simulation.geometry[2 + 2 * index]
        assert isinstance(ring_outer, mp.Cylinder)
        assert isinstance(ring_inner, mp.Cylinder)
        assert abs(ring_outer.center.x - ring_center_x_um) < 1e-12
        assert abs(ring_inner.center.x - ring_center_x_um) < 1e-12
        assert abs(ring_outer.center.y - ring_center_y_um) < 1e-12
        assert abs(ring_inner.center.y - ring_center_y_um) < 1e-12
        assert abs(ring_outer.radius - geometry.ring_outer_radius_um) < 1e-12
        assert abs(ring_inner.radius - geometry.ring_inner_radius_um) < 1e-12

    with json_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    assert manifest["core_index"] == materials.core_index
    assert abs(manifest["cladding_epsilon"] - materials.cladding_epsilon) < 1e-12
    assert manifest["resolution"] == spec.resolution
    assert manifest["waveguide_center_y_um"] == -5.0
    assert manifest["ring_count"] == design.ring_count

    print(f"Geometry preview written to {preview_path}")
    print(f"Geometry summary written to {json_path}")
    print("Geometry check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
