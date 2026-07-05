from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import meep as mp

from layout import FIGURES_DIR, REPORTS_DIR, build_layout_geometry
from design import MaterialModel, ResonatorBaseline


@dataclass(frozen=True)
class SimulationSpec:
    resolution: int = 24
    pml_thickness_um: float = 1.0
    x_margin_um: float = 3.0
    y_margin_um: float = 6.5
    waveguide_center_y_um: float = -5.0
    bus_left_clearance_um: float = 2.0


@dataclass(frozen=True)
class SimulationGeometry:
    cell_size_x_um: float
    cell_size_y_um: float
    waveguide_center_y_um: float
    bus_center_x_um: float
    bus_length_um: float
    bus_width_um: float
    bus_left_x_um: float
    bus_right_x_um: float
    ring_count: int
    ring_row_count: int
    ring_center_x_ums: tuple[float, ...]
    ring_center_y_ums: tuple[float, ...]
    ring_centers_um: tuple[tuple[float, float], ...]
    ring_radius_um: float
    ring_inner_radius_um: float
    ring_outer_radius_um: float
    pml_thickness_um: float
    resolution: int


@dataclass(frozen=True)
class FluxLineOverlay:
    center_x_um: float
    center_y_um: float
    size_y_um: float


def geometry_artifact_paths() -> dict[str, Path]:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "png": FIGURES_DIR / "simulation_layout.png",
        "json": REPORTS_DIR / "geometry_summary.json",
    }


def build_simulation_geometry(
    design: ResonatorBaseline | None = None,
    spec: SimulationSpec | None = None,
) -> SimulationGeometry:
    design = design or ResonatorBaseline()
    spec = spec or SimulationSpec()
    layout_geometry = build_layout_geometry(design=design)

    x_extent = 0.5 * layout_geometry.bus_length_um + spec.x_margin_um + spec.pml_thickness_um
    ring_center_y_ums = tuple(
        ring_center_y_um + spec.waveguide_center_y_um
        for ring_center_y_um in layout_geometry.ring_center_y_ums
    )
    ring_centers_um = tuple(
        (ring_center_x_um, ring_center_y_um)
        for ring_center_y_um in ring_center_y_ums
        for ring_center_x_um in layout_geometry.ring_center_x_ums
    )
    ring_top = max(ring_center_y_ums) + layout_geometry.outer_ring_radius_um
    ring_bottom = spec.waveguide_center_y_um - 0.5 * layout_geometry.bus_width_um
    y_lower = ring_bottom - spec.y_margin_um - spec.pml_thickness_um
    y_upper = ring_top + spec.y_margin_um + spec.pml_thickness_um

    cell_size_x_um = snap_length_to_grid(2.0 * x_extent, spec.resolution)
    cell_size_y_um = snap_length_to_grid(y_upper - y_lower, spec.resolution)
    bus_left_x_um = -0.5 * cell_size_x_um + spec.pml_thickness_um + spec.bus_left_clearance_um
    bus_right_x_um = 0.5 * cell_size_x_um - spec.pml_thickness_um
    bus_length_um = bus_right_x_um - bus_left_x_um
    bus_center_x_um = 0.5 * (bus_left_x_um + bus_right_x_um)

    return SimulationGeometry(
        cell_size_x_um=cell_size_x_um,
        cell_size_y_um=cell_size_y_um,
        waveguide_center_y_um=spec.waveguide_center_y_um,
        bus_center_x_um=bus_center_x_um,
        bus_length_um=bus_length_um,
        bus_width_um=layout_geometry.bus_width_um,
        bus_left_x_um=bus_left_x_um,
        bus_right_x_um=bus_right_x_um,
        ring_count=layout_geometry.ring_count,
        ring_row_count=layout_geometry.ring_row_count,
        ring_center_x_ums=layout_geometry.ring_center_x_ums,
        ring_center_y_ums=ring_center_y_ums,
        ring_centers_um=ring_centers_um,
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
    include_ring: bool = True,
) -> tuple[mp.Simulation, SimulationGeometry]:
    design = design or ResonatorBaseline()
    spec = spec or SimulationSpec()
    geometry = build_simulation_geometry(design=design, spec=spec)
    geometry_objects, cladding = build_meep_geometry_objects(
        geometry=geometry,
        include_ring=include_ring,
    )

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
    include_ring: bool = True,
) -> tuple[list[mp.GeometricObject], mp.Medium]:
    materials = materials or MaterialModel()

    core = mp.Medium(index=materials.core_index)
    cladding = mp.Medium(index=materials.cladding_index)

    bus = mp.Block(
        size=mp.Vector3(geometry.bus_length_um, geometry.bus_width_um, mp.inf),
        center=mp.Vector3(geometry.bus_center_x_um, geometry.waveguide_center_y_um, 0.0),
        material=core,
    )
    geometry_objects: list[mp.GeometricObject] = [bus]

    if include_ring:
        for ring_center_x_um, ring_center_y_um in geometry.ring_centers_um:
            ring_outer = mp.Cylinder(
                radius=geometry.ring_outer_radius_um,
                center=mp.Vector3(ring_center_x_um, ring_center_y_um, 0.0),
                material=core,
            )
            ring_inner = mp.Cylinder(
                radius=geometry.ring_inner_radius_um,
                center=mp.Vector3(ring_center_x_um, ring_center_y_um, 0.0),
                material=cladding,
            )
            geometry_objects.extend([ring_outer, ring_inner])

    return geometry_objects, cladding


def build_flux_line_overlay(geometry: SimulationGeometry) -> FluxLineOverlay:
    ring_right_edge_um = max(geometry.ring_center_x_ums) + geometry.ring_outer_radius_um
    monitor_offset_from_right_edge_um = 0.75
    monitor_span_scale = 2.0
    center_x_um = max(
        ring_right_edge_um + 0.75,
        geometry.bus_right_x_um - monitor_offset_from_right_edge_um,
    )
    center_x_um = min(center_x_um, geometry.bus_right_x_um - 0.1)
    return FluxLineOverlay(
        center_x_um=center_x_um,
        center_y_um=geometry.waveguide_center_y_um,
        size_y_um=monitor_span_scale * geometry.bus_width_um,
    )


def geometry_summary(
    design: ResonatorBaseline | None = None,
    spec: SimulationSpec | None = None,
) -> dict[str, float | int]:
    design = design or ResonatorBaseline()
    spec = spec or SimulationSpec()
    materials = MaterialModel()
    geometry = build_simulation_geometry(design=design, spec=spec)
    flux_line = build_flux_line_overlay(geometry)
    paths = geometry_artifact_paths()
    return {
        **asdict(materials),
        "core_epsilon": materials.core_epsilon,
        "cladding_epsilon": materials.cladding_epsilon,
        **asdict(design),
        **asdict(spec),
        **asdict(geometry),
        **{f"flux_line_{key}": value for key, value in asdict(flux_line).items()},
        "preview_png_path": str(paths["png"]),
        "summary_json_path": str(paths["json"]),
    }


def write_geometry_artifacts(
    design: ResonatorBaseline | None = None,
    spec: SimulationSpec | None = None,
) -> dict[str, float | int]:
    simulation, _ = build_meep_simulation(design=design, spec=spec)
    summary = geometry_summary(design=design, spec=spec)
    paths = geometry_artifact_paths()
    flux_line = build_flux_line_overlay(build_simulation_geometry(design=design, spec=spec))

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
    flux_y_min = flux_line.center_y_um - 0.5 * flux_line.size_y_um
    flux_y_max = flux_line.center_y_um + 0.5 * flux_line.size_y_um
    axis.plot(
        [flux_line.center_x_um, flux_line.center_x_um],
        [flux_y_min, flux_y_max],
        color="crimson",
        linewidth=2.0,
        linestyle="--",
    )
    axis.text(
        flux_line.center_x_um + 0.3,
        flux_y_max + 0.3,
        "flux cut",
        color="crimson",
        fontsize=9,
        ha="left",
        va="bottom",
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
        "bus_center_x_um",
        "bus_length_um",
        "bus_width_um",
        "bus_left_x_um",
        "bus_right_x_um",
        "ring_radius_um",
        "ring_inner_radius_um",
        "ring_outer_radius_um",
        "ring_center_y_ums",
        "pml_thickness_um",
        "resolution",
        "preview_png_path",
        "summary_json_path",
    ]
    return "\n".join(f"{key}: {summary[key]}" for key in ordered_keys)
