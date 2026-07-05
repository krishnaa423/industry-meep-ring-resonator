from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import gdspy
import matplotlib.pyplot as plt

from design import ResonatorBaseline


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
GDS_DIR = DOCS_DIR / "gds"
FIGURES_DIR = DOCS_DIR / "figures"
REPORTS_DIR = DOCS_DIR / "reports"


@dataclass(frozen=True)
class LayoutSpec:
    bus_end_margin_um: float = 4.0
    ring_layer: int = 2
    bus_layer: int = 1
    layer_datatype: int = 0
    ring_polygon_points: int = 256


@dataclass(frozen=True)
class LayoutGeometry:
    bus_length_um: float
    bus_width_um: float
    ring_width_um: float
    ring_gap_um: float
    ring_count: int
    ring_to_ring_gap_um: float
    ring_row_count: int
    ring_row_gap_um: float
    ring_center_x_ums: tuple[float, ...]
    ring_center_y_ums: tuple[float, ...]
    ring_centers_um: tuple[tuple[float, float], ...]
    ring_radius_um: float
    inner_ring_radius_um: float
    outer_ring_radius_um: float


def build_layout_geometry(
    design: ResonatorBaseline | None = None,
    layout: LayoutSpec | None = None,
) -> LayoutGeometry:
    design = design or ResonatorBaseline()
    layout = layout or LayoutSpec()

    outer_ring_radius_um = design.ring_radius_um + 0.5 * design.ring_waveguide_width_um
    inner_ring_radius_um = design.ring_radius_um - 0.5 * design.ring_waveguide_width_um
    ring_outer_diameter_um = 2.0 * outer_ring_radius_um
    ring_pitch_um = ring_outer_diameter_um + design.ring_to_ring_gap_um
    array_span_um = ring_outer_diameter_um + (design.ring_count - 1) * ring_pitch_um
    first_ring_center_y_um = (
        0.5 * design.waveguide_width_um
        + design.ring_gap_um
        + outer_ring_radius_um
    )
    ring_center_y_ums = tuple(
        first_ring_center_y_um
        + row_index * (2.0 * outer_ring_radius_um + design.ring_row_gap_um)
        for row_index in range(design.ring_row_count)
    )
    first_center_x_um = -0.5 * array_span_um + outer_ring_radius_um
    ring_center_x_ums = tuple(
        first_center_x_um + index * ring_pitch_um
        for index in range(design.ring_count)
    )
    ring_centers_um = tuple(
        (ring_center_x_um, ring_center_y_um)
        for ring_center_y_um in ring_center_y_ums
        for ring_center_x_um in ring_center_x_ums
    )
    bus_length_um = array_span_um + 2.0 * layout.bus_end_margin_um

    return LayoutGeometry(
        bus_length_um=bus_length_um,
        bus_width_um=design.waveguide_width_um,
        ring_width_um=design.ring_waveguide_width_um,
        ring_gap_um=design.ring_gap_um,
        ring_count=design.ring_count,
        ring_to_ring_gap_um=design.ring_to_ring_gap_um,
        ring_row_count=design.ring_row_count,
        ring_row_gap_um=design.ring_row_gap_um,
        ring_center_x_ums=ring_center_x_ums,
        ring_center_y_ums=ring_center_y_ums,
        ring_centers_um=ring_centers_um,
        ring_radius_um=design.ring_radius_um,
        inner_ring_radius_um=inner_ring_radius_um,
        outer_ring_radius_um=outer_ring_radius_um,
    )


def build_layout_library(
    design: ResonatorBaseline | None = None,
    layout: LayoutSpec | None = None,
) -> tuple[gdspy.GdsLibrary, gdspy.Cell, LayoutGeometry]:
    design = design or ResonatorBaseline()
    layout = layout or LayoutSpec()
    geometry = build_layout_geometry(design=design, layout=layout)

    library = gdspy.GdsLibrary(unit=1.0e-6, precision=1.0e-9)
    cell = library.new_cell("RING_RESONATOR")

    half_length = 0.5 * geometry.bus_length_um
    half_width = 0.5 * geometry.bus_width_um

    bus = gdspy.Rectangle(
        (-half_length, -half_width),
        (half_length, half_width),
        layer=layout.bus_layer,
        datatype=layout.layer_datatype,
    )
    cell.add(bus)
    for ring_center_x_um, ring_center_y_um in geometry.ring_centers_um:
        ring = gdspy.Round(
            center=(ring_center_x_um, ring_center_y_um),
            radius=geometry.outer_ring_radius_um,
            inner_radius=geometry.inner_ring_radius_um,
            number_of_points=layout.ring_polygon_points,
            layer=layout.ring_layer,
            datatype=layout.layer_datatype,
        )
        cell.add(ring)

    return library, cell, geometry


def ensure_output_directories() -> None:
    for directory in (GDS_DIR, FIGURES_DIR, REPORTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def artifact_paths() -> dict[str, Path]:
    ensure_output_directories()
    return {
        "gds": GDS_DIR / "ring_resonator_layout.gds",
        "svg": REPORTS_DIR / "ring_resonator_layout.svg",
        "json": REPORTS_DIR / "layout_summary.json",
    }


def layout_summary(
    design: ResonatorBaseline | None = None,
    layout: LayoutSpec | None = None,
) -> dict[str, float | int | str]:
    design = design or ResonatorBaseline()
    layout = layout or LayoutSpec()
    geometry = build_layout_geometry(design=design, layout=layout)
    paths = artifact_paths()

    return {
        **asdict(design),
        **asdict(layout),
        **asdict(geometry),
        "gds_path": str(paths["gds"]),
        "svg_path": str(paths["svg"]),
        "json_path": str(paths["json"]),
    }


def write_layout_artifacts(
    design: ResonatorBaseline | None = None,
    layout: LayoutSpec | None = None,
) -> dict[str, float | int | str]:
    design = design or ResonatorBaseline()
    layout = layout or LayoutSpec()
    library, cell, _ = build_layout_library(design=design, layout=layout)
    summary = layout_summary(design=design, layout=layout)
    paths = artifact_paths()

    library.write_gds(paths["gds"])
    write_layout_svg(cell=cell, destination=paths["svg"])

    with paths["json"].open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return summary


def write_layout_svg(cell: gdspy.Cell, destination: Path) -> None:
    polygon_sets = cell.get_polygons(by_spec=False)

    figure, axis = plt.subplots(figsize=(8, 4))
    for polygon in polygon_sets:
        axis.fill(polygon[:, 0], polygon[:, 1], alpha=0.55, linewidth=0.8)

    axis.set_aspect("equal")
    axis.set_xlabel("x (um)")
    axis.set_ylabel("y (um)")
    axis.set_title("Ring resonator layout")
    axis.grid(True, alpha=0.25)

    bbox = cell.get_bounding_box()
    if bbox is not None:
        padding_x = 1.0
        padding_y = 1.0
        axis.set_xlim(bbox[0, 0] - padding_x, bbox[1, 0] + padding_x)
        axis.set_ylim(bbox[0, 1] - padding_y, bbox[1, 1] + padding_y)

    figure.tight_layout()
    figure.savefig(destination, format="svg")
    plt.close(figure)


def format_layout_summary(
    design: ResonatorBaseline | None = None,
    layout: LayoutSpec | None = None,
) -> str:
    summary = layout_summary(design=design, layout=layout)
    ordered_keys = [
        "bus_length_um",
        "waveguide_width_um",
        "ring_waveguide_width_um",
        "ring_gap_um",
        "ring_count",
        "ring_to_ring_gap_um",
        "ring_row_count",
        "ring_row_gap_um",
        "ring_radius_um",
        "inner_ring_radius_um",
        "outer_ring_radius_um",
        "ring_center_y_ums",
        "gds_path",
        "svg_path",
        "json_path",
    ]
    return "\n".join(f"{key}: {summary[key]}" for key in ordered_keys)
