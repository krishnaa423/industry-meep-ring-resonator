from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import meep as mp

from ring_layout import FIGURES_DIR, REPORTS_DIR, build_layout_geometry
from stage1_baseline import MaterialModel, ResonatorBaseline


@dataclass(frozen=True)
class SimulationSpec:
    resolution: int = 24
    pml_thickness_um: float = 1.0
    x_margin_um: float = 3.0
    y_margin_um: float = 5.0
    waveguide_center_y_um: float = -5.0


@dataclass(frozen=True)
class SimulationGeometry:
    cell_size_x_um: float
    cell_size_y_um: float
    waveguide_center_y_um: float
    bus_length_um: float
    bus_width_um: float
    ring_center_x_um: float
    ring_center_y_um: float
    ring_radius_um: float
    ring_inner_radius_um: float
    ring_outer_radius_um: float
    pml_thickness_um: float
    resolution: int


def stage3_artifact_paths() -> dict[str, Path]:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "png": FIGURES_DIR / "stage3_meep_geometry.png",
        "json": REPORTS_DIR / "stage3_geometry_summary.json",
    }


def build_simulation_geometry(
    design: ResonatorBaseline | None = None,
    spec: SimulationSpec | None = None,
) -> SimulationGeometry:
    design = design or ResonatorBaseline()
    spec = spec or SimulationSpec()
    layout_geometry = build_layout_geometry(design=design)

    x_extent = 0.5 * layout_geometry.bus_length_um + spec.x_margin_um + spec.pml_thickness_um
    ring_center_y_um = layout_geometry.ring_center_y_um + spec.waveguide_center_y_um
    ring_top = ring_center_y_um + layout_geometry.outer_ring_radius_um
    ring_bottom = spec.waveguide_center_y_um - 0.5 * layout_geometry.bus_width_um
    y_lower = ring_bottom - spec.y_margin_um - spec.pml_thickness_um
    y_upper = ring_top + spec.y_margin_um + spec.pml_thickness_um

    cell_size_x_um = snap_length_to_grid(2.0 * x_extent, spec.resolution)
    cell_size_y_um = snap_length_to_grid(y_upper - y_lower, spec.resolution)

    return SimulationGeometry(
        cell_size_x_um=cell_size_x_um,
        cell_size_y_um=cell_size_y_um,
        waveguide_center_y_um=spec.waveguide_center_y_um,
        bus_length_um=layout_geometry.bus_length_um,
        bus_width_um=layout_geometry.bus_width_um,
        ring_center_x_um=layout_geometry.ring_center_x_um,
        ring_center_y_um=ring_center_y_um,
        ring_radius_um=layout_geometry.ring_radius_um,
        ring_inner_radius_um=layout_geometry.inner_ring_radius_um,
        ring_outer_radius_um=layout_geometry.outer_ring_radius_um,
        pml_thickness_um=spec.pml_thickness_um,
        resolution=spec.resolution,
    )


def snap_length_to_grid(length_um: float, resolution: int) -> float:
    return round(length_um * resolution) / resolution


def build_meep_simulation(
    design: ResonatorBaseline | None = None,
    spec: SimulationSpec | None = None,
) -> tuple[mp.Simulation, SimulationGeometry]:
    design = design or ResonatorBaseline()
    spec = spec or SimulationSpec()
    geometry = build_simulation_geometry(design=design, spec=spec)
    geometry_objects, cladding = build_meep_geometry_objects(geometry=geometry)

    simulation = mp.Simulation(
        cell_size=mp.Vector3(geometry.cell_size_x_um, geometry.cell_size_y_um, 0.0),
        boundary_layers=[mp.PML(geometry.pml_thickness_um)],
        geometry=geometry_objects,
        default_material=cladding,
        resolution=geometry.resolution,
        dimensions=2,
    )

    return simulation, geometry


def build_meep_geometry_objects(
    geometry: SimulationGeometry,
    materials: MaterialModel | None = None,
) -> tuple[list[mp.GeometricObject], mp.Medium]:
    materials = materials or MaterialModel()

    core = mp.Medium(index=materials.core_index)
    cladding = mp.Medium(index=materials.cladding_index)

    bus = mp.Block(
        size=mp.Vector3(geometry.bus_length_um, geometry.bus_width_um, mp.inf),
        center=mp.Vector3(0.0, geometry.waveguide_center_y_um, 0.0),
        material=core,
    )
    ring_outer = mp.Cylinder(
        radius=geometry.ring_outer_radius_um,
        center=mp.Vector3(geometry.ring_center_x_um, geometry.ring_center_y_um, 0.0),
        material=core,
    )
    ring_inner = mp.Cylinder(
        radius=geometry.ring_inner_radius_um,
        center=mp.Vector3(geometry.ring_center_x_um, geometry.ring_center_y_um, 0.0),
        material=cladding,
    )

    return [bus, ring_outer, ring_inner], cladding


def geometry_summary(
    design: ResonatorBaseline | None = None,
    spec: SimulationSpec | None = None,
) -> dict[str, float | int]:
    design = design or ResonatorBaseline()
    spec = spec or SimulationSpec()
    materials = MaterialModel()
    geometry = build_simulation_geometry(design=design, spec=spec)
    paths = stage3_artifact_paths()
    return {
        **asdict(materials),
        "core_epsilon": materials.core_epsilon,
        "cladding_epsilon": materials.cladding_epsilon,
        **asdict(design),
        **asdict(spec),
        **asdict(geometry),
        "preview_png_path": str(paths["png"]),
        "summary_json_path": str(paths["json"]),
    }


def write_geometry_artifacts(
    design: ResonatorBaseline | None = None,
    spec: SimulationSpec | None = None,
) -> dict[str, float | int]:
    simulation, _ = build_meep_simulation(design=design, spec=spec)
    summary = geometry_summary(design=design, spec=spec)
    paths = stage3_artifact_paths()

    simulation.init_sim()

    figure, axis = plt.subplots(figsize=(8, 5))
    simulation.plot2D(
        ax=axis,
        labels=False,
        show_sources=False,
        show_monitors=False,
        eps_parameters={"alpha": 0.9},
        boundary_parameters={"alpha": 0.25, "hatch": "/"},
    )
    axis.set_title("Meep geometry preview")
    figure.tight_layout()
    figure.savefig(paths["png"], dpi=180)
    plt.close(figure)

    with paths["json"].open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return summary


def format_geometry_summary(
    design: ResonatorBaseline | None = None,
    spec: SimulationSpec | None = None,
) -> str:
    summary = geometry_summary(design=design, spec=spec)
    ordered_keys = [
        "cell_size_x_um",
        "cell_size_y_um",
        "bus_length_um",
        "bus_width_um",
        "ring_radius_um",
        "ring_inner_radius_um",
        "ring_outer_radius_um",
        "ring_center_y_um",
        "pml_thickness_um",
        "resolution",
        "preview_png_path",
        "summary_json_path",
    ]
    return "\n".join(f"{key}: {summary[key]}" for key in ordered_keys)
