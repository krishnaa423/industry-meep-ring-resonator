from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import meep as mp
import numpy as np

from geometry import (
    FIGURES_DIR,
    REPORTS_DIR,
    SimulationGeometry,
    SimulationSpec,
    build_meep_geometry_objects,
    build_simulation_geometry,
)
from design import MaterialModel, ResonatorBaseline


DATA_DIR = Path(__file__).resolve().parents[1] / "docs" / "data"


@dataclass(frozen=True)
class BaselineRunSpec:
    source_frequency_width_per_um: float = 0.30
    flux_frequency_width_per_um: float = 0.30
    flux_sample_count: int = 181
    source_offset_from_bus_edge_um: float = 2.0
    monitor_offset_from_bus_edge_um: float = 2.0
    source_size_scale: float = 1.5
    monitor_size_scale: float = 1.5
    field_decay_check_interval: float = 50.0
    field_decay_by: float = 1.0e-6
    artifact_stem: str = "output_flux_spectrum"
    summary_stem: str = "run_summary"
    plot_title: str = "Baseline ring resonator transmission"
    plot_dir_name: str = "reports"


@dataclass(frozen=True)
class BaselineRunGeometry:
    source_center_x_um: float
    source_center_y_um: float
    source_size_y_um: float
    monitor_center_x_um: float
    monitor_center_y_um: float
    monitor_size_y_um: float
    target_frequency_per_um: float


def baseline_artifact_paths(
    artifact_stem: str,
    summary_stem: str,
    plot_dir_name: str,
) -> dict[str, Path]:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    plot_dir = Path(__file__).resolve().parents[1] / "docs" / plot_dir_name
    plot_dir.mkdir(parents=True, exist_ok=True)
    return {
        "plot": plot_dir / f"{artifact_stem}.png",
        "csv": DATA_DIR / f"{artifact_stem}.csv",
        "json": REPORTS_DIR / f"{summary_stem}.json",
    }


def build_baseline_run_geometry(
    design: ResonatorBaseline | None = None,
    simulation_spec: SimulationSpec | None = None,
    run_spec: BaselineRunSpec | None = None,
) -> tuple[SimulationGeometry, BaselineRunGeometry]:
    design = design or ResonatorBaseline()
    simulation_spec = simulation_spec or SimulationSpec()
    run_spec = run_spec or BaselineRunSpec()

    geometry = build_simulation_geometry(design=design, spec=simulation_spec)
    source_center_x_um = (
        geometry.bus_left_x_um + run_spec.source_offset_from_bus_edge_um
    )
    monitor_center_x_um = (
        geometry.bus_right_x_um - run_spec.monitor_offset_from_bus_edge_um
    )

    run_geometry = BaselineRunGeometry(
        source_center_x_um=source_center_x_um,
        source_center_y_um=geometry.waveguide_center_y_um,
        source_size_y_um=run_spec.source_size_scale * geometry.bus_width_um,
        monitor_center_x_um=monitor_center_x_um,
        monitor_center_y_um=geometry.waveguide_center_y_um,
        monitor_size_y_um=run_spec.monitor_size_scale * geometry.bus_width_um,
        target_frequency_per_um=design.target_frequency_per_um,
    )
    return geometry, run_geometry


def build_baseline_simulation(
    design: ResonatorBaseline | None = None,
    simulation_spec: SimulationSpec | None = None,
    run_spec: BaselineRunSpec | None = None,
    include_ring: bool = True,
) -> tuple[mp.Simulation, object, SimulationGeometry, BaselineRunGeometry]:
    design = design or ResonatorBaseline()
    simulation_spec = simulation_spec or SimulationSpec()
    run_spec = run_spec or BaselineRunSpec()
    materials = MaterialModel()
    geometry, run_geometry = build_baseline_run_geometry(
        design=design,
        simulation_spec=simulation_spec,
        run_spec=run_spec,
    )
    geometry_objects, cladding = build_meep_geometry_objects(
        geometry=geometry,
        materials=materials,
        include_ring=include_ring,
    )

    source = mp.Source(
        mp.GaussianSource(
            frequency=run_geometry.target_frequency_per_um,
            fwidth=run_spec.source_frequency_width_per_um,
        ),
        component=mp.Ez,
        center=mp.Vector3(run_geometry.source_center_x_um, run_geometry.source_center_y_um),
        size=mp.Vector3(0.0, run_geometry.source_size_y_um, 0.0),
        amplitude=1.0,
    )

    simulation = mp.Simulation(
        cell_size=mp.Vector3(geometry.cell_size_x_um, geometry.cell_size_y_um, 0.0),
        boundary_layers=[mp.PML(geometry.pml_thickness_um)],
        geometry=geometry_objects,
        sources=[source],
        default_material=cladding,
        resolution=geometry.resolution,
        dimensions=2,
    )

    flux_monitor = simulation.add_flux(
        run_geometry.target_frequency_per_um,
        run_spec.flux_frequency_width_per_um,
        run_spec.flux_sample_count,
        mp.FluxRegion(
            center=mp.Vector3(
                run_geometry.monitor_center_x_um,
                run_geometry.monitor_center_y_um,
                0.0,
            ),
            size=mp.Vector3(0.0, run_geometry.monitor_size_y_um, 0.0),
        ),
    )

    return simulation, flux_monitor, geometry, run_geometry


def run_baseline_simulation(
    design: ResonatorBaseline | None = None,
    simulation_spec: SimulationSpec | None = None,
    run_spec: BaselineRunSpec | None = None,
    include_ring: bool = True,
) -> dict[str, object]:
    design = design or ResonatorBaseline()
    simulation_spec = simulation_spec or SimulationSpec()
    run_spec = run_spec or BaselineRunSpec()

    simulation, flux_monitor, geometry, run_geometry = build_baseline_simulation(
        design=design,
        simulation_spec=simulation_spec,
        run_spec=run_spec,
        include_ring=include_ring,
    )
    paths = baseline_artifact_paths(
        artifact_stem=run_spec.artifact_stem,
        summary_stem=run_spec.summary_stem,
        plot_dir_name=run_spec.plot_dir_name,
    )
    source_to_monitor_distance_um = abs(
        run_geometry.monitor_center_x_um - run_geometry.source_center_x_um
    )
    decay_wait_time = max(
        run_spec.field_decay_check_interval,
        1.25 * source_to_monitor_distance_um * design.effective_index,
    )

    monitor_point = mp.Vector3(
        run_geometry.monitor_center_x_um,
        run_geometry.monitor_center_y_um,
        0.0,
    )
    simulation.run(
        until_after_sources=mp.stop_when_fields_decayed(
            decay_wait_time,
            mp.Ez,
            monitor_point,
            run_spec.field_decay_by,
        )
    )

    frequencies = np.array(mp.get_flux_freqs(flux_monitor), dtype=float)
    flux_values = np.array(mp.get_fluxes(flux_monitor), dtype=float)
    wavelengths = 1.0 / frequencies
    normalized_flux = flux_values / flux_values.max() if flux_values.max() != 0 else flux_values

    order = np.argsort(wavelengths)
    wavelengths = wavelengths[order]
    frequencies = frequencies[order]
    flux_values = flux_values[order]
    normalized_flux = normalized_flux[order]

    write_flux_csv(
        destination=paths["csv"],
        wavelengths_um=wavelengths,
        frequencies_per_um=frequencies,
        flux_values=flux_values,
        normalized_flux=normalized_flux,
    )
    write_flux_plot(
        destination=paths["plot"],
        wavelengths_um=wavelengths,
        normalized_flux=normalized_flux,
        plot_title=run_spec.plot_title,
    )

    summary = {
        **asdict(design),
        **asdict(simulation_spec),
        **asdict(run_spec),
        **asdict(geometry),
        **asdict(run_geometry),
        "core_index": MaterialModel().core_index,
        "cladding_index": MaterialModel().cladding_index,
        "wavelength_min_um": float(wavelengths.min()),
        "wavelength_max_um": float(wavelengths.max()),
        "peak_flux": float(flux_values.max()),
        "minimum_flux": float(flux_values.min()),
        "decay_wait_time": float(decay_wait_time),
        "plot_path": str(paths["plot"]),
        "csv_path": str(paths["csv"]),
        "summary_json_path": str(paths["json"]),
    }

    with paths["json"].open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return summary


def write_flux_csv(
    destination: Path,
    wavelengths_um: np.ndarray,
    frequencies_per_um: np.ndarray,
    flux_values: np.ndarray,
    normalized_flux: np.ndarray,
) -> None:
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "wavelength_um",
                "frequency_per_um",
                "output_flux",
                "normalized_output_flux",
            ]
        )
        for wavelength, frequency, flux, normalized in zip(
            wavelengths_um,
            frequencies_per_um,
            flux_values,
            normalized_flux,
            strict=True,
        ):
            writer.writerow([wavelength, frequency, flux, normalized])


def write_flux_plot(
    destination: Path,
    wavelengths_um: np.ndarray,
    normalized_flux: np.ndarray,
    plot_title: str,
) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(wavelengths_um, normalized_flux, linewidth=1.6)
    axis.set_xlabel("wavelength (um)")
    axis.set_ylabel("normalized output flux")
    axis.set_title(plot_title)
    axis.grid(True, alpha=0.25)
    figure.tight_layout()
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def format_baseline_run_summary(
    design: ResonatorBaseline | None = None,
    simulation_spec: SimulationSpec | None = None,
    run_spec: BaselineRunSpec | None = None,
) -> str:
    summary = run_baseline_simulation(
        design=design,
        simulation_spec=simulation_spec,
        run_spec=run_spec,
    )
    ordered_keys = [
        "target_frequency_per_um",
        "source_center_x_um",
        "monitor_center_x_um",
        "wavelength_min_um",
        "wavelength_max_um",
        "peak_flux",
        "minimum_flux",
        "plot_path",
        "csv_path",
        "summary_json_path",
    ]
    return "\n".join(f"{key}: {summary[key]}" for key in ordered_keys)
