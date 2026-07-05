from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from spectrum import (
    BaselineRunSpec,
    baseline_artifact_paths,
    build_baseline_run_geometry,
    run_baseline_simulation,
)
from geometry import SimulationSpec
from design import ResonatorBaseline


DATA_DIR = Path(__file__).resolve().parents[1] / "docs" / "data"
FIGURES_DIR = Path(__file__).resolve().parents[1] / "docs" / "figures"
REPORTS_DIR = Path(__file__).resolve().parents[1] / "docs" / "reports"


@dataclass(frozen=True)
class TransmissionCompareSpec:
    monitor_offset_from_right_edge_um: float = 0.75
    monitor_span_scale: float = 2.0
    artifact_stem: str = "transmission_comparison"
    summary_stem: str = "transmission_summary"


def transmission_artifact_paths(
    spec: TransmissionCompareSpec | None = None,
) -> dict[str, Path]:
    spec = spec or TransmissionCompareSpec()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    comparison_dir = REPORTS_DIR if "check" in spec.artifact_stem else FIGURES_DIR
    return {
        "comparison_plot": comparison_dir / f"{spec.artifact_stem}.png",
        "transmission_plot": REPORTS_DIR / "normalized_transmission.png",
        "csv": DATA_DIR / f"{spec.artifact_stem}.csv",
        "json": REPORTS_DIR / f"{spec.summary_stem}.json",
    }


def make_transmission_run_spec(
    design: ResonatorBaseline | None = None,
    simulation_spec: SimulationSpec | None = None,
    baseline_run_spec: BaselineRunSpec | None = None,
    compare_spec: TransmissionCompareSpec | None = None,
    artifact_stem: str = "",
    summary_stem: str = "",
    plot_title: str = "",
) -> BaselineRunSpec:
    design = design or ResonatorBaseline()
    simulation_spec = simulation_spec or SimulationSpec()
    baseline_run_spec = baseline_run_spec or BaselineRunSpec()
    compare_spec = compare_spec or TransmissionCompareSpec()

    geometry, run_geometry = build_baseline_run_geometry(
        design=design,
        simulation_spec=simulation_spec,
        run_spec=baseline_run_spec,
    )
    ring_right_edge_um = max(geometry.ring_center_x_ums) + geometry.ring_outer_radius_um
    monitor_center_x_um = max(
        ring_right_edge_um + 0.75,
        geometry.bus_right_x_um - compare_spec.monitor_offset_from_right_edge_um,
    )
    monitor_center_x_um = min(
        monitor_center_x_um,
        geometry.bus_right_x_um - 0.1,
    )

    return BaselineRunSpec(
        source_frequency_width_per_um=baseline_run_spec.source_frequency_width_per_um,
        flux_frequency_width_per_um=baseline_run_spec.flux_frequency_width_per_um,
        flux_sample_count=baseline_run_spec.flux_sample_count,
        source_offset_from_bus_edge_um=baseline_run_spec.source_offset_from_bus_edge_um,
        monitor_offset_from_bus_edge_um=geometry.bus_right_x_um - monitor_center_x_um,
        source_size_scale=baseline_run_spec.source_size_scale,
        monitor_size_scale=compare_spec.monitor_span_scale,
        field_decay_check_interval=baseline_run_spec.field_decay_check_interval,
        field_decay_by=baseline_run_spec.field_decay_by,
        artifact_stem=artifact_stem,
        summary_stem=summary_stem,
        plot_title=plot_title,
        plot_dir_name="reports",
    )


def load_flux_csv(csv_path: Path) -> list[dict[str, float]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            {
                "wavelength_um": float(row["wavelength_um"]),
                "frequency_per_um": float(row["frequency_per_um"]),
                "output_flux": float(row["output_flux"]),
                "normalized_output_flux": float(row["normalized_output_flux"]),
            }
            for row in reader
        ]


def run_transmission_comparison(
    design: ResonatorBaseline | None = None,
    simulation_spec: SimulationSpec | None = None,
    baseline_run_spec: BaselineRunSpec | None = None,
    compare_spec: TransmissionCompareSpec | None = None,
) -> dict[str, object]:
    design = design or ResonatorBaseline()
    simulation_spec = simulation_spec or SimulationSpec()
    baseline_run_spec = baseline_run_spec or BaselineRunSpec()
    compare_spec = compare_spec or TransmissionCompareSpec()

    reference_run_spec = make_transmission_run_spec(
        design=design,
        simulation_spec=simulation_spec,
        baseline_run_spec=baseline_run_spec,
        compare_spec=compare_spec,
        artifact_stem="reference_flux",
        summary_stem="reference_run_summary",
        plot_title="Reference waveguide flux",
    )
    ring_run_spec = make_transmission_run_spec(
        design=design,
        simulation_spec=simulation_spec,
        baseline_run_spec=baseline_run_spec,
        compare_spec=compare_spec,
        artifact_stem="ring_flux",
        summary_stem="ring_run_summary",
        plot_title="Waveguide plus ring flux",
    )

    reference_summary = run_baseline_simulation(
        design=design,
        simulation_spec=simulation_spec,
        run_spec=reference_run_spec,
        include_ring=False,
    )
    ring_summary = run_baseline_simulation(
        design=design,
        simulation_spec=simulation_spec,
        run_spec=ring_run_spec,
        include_ring=True,
    )

    reference_rows = load_flux_csv(Path(reference_summary["csv_path"]))
    ring_rows = load_flux_csv(Path(ring_summary["csv_path"]))
    if len(reference_rows) != len(ring_rows):
        raise RuntimeError("Reference and ring flux spectra have different sample counts.")

    frequencies = np.array([row["frequency_per_um"] for row in reference_rows], dtype=float)
    wavelengths = np.array([row["wavelength_um"] for row in reference_rows], dtype=float)
    reference_flux = np.array([row["output_flux"] for row in reference_rows], dtype=float)
    ring_flux = np.array([row["output_flux"] for row in ring_rows], dtype=float)
    transmission = np.divide(
        ring_flux,
        reference_flux,
        out=np.zeros_like(ring_flux),
        where=np.abs(reference_flux) > 1.0e-12,
    )

    paths = transmission_artifact_paths(compare_spec)
    write_comparison_plot(
        destination=paths["comparison_plot"],
        frequencies_per_um=frequencies,
        reference_flux=reference_flux,
        ring_flux=ring_flux,
    )
    write_transmission_plot(
        destination=paths["transmission_plot"],
        frequencies_per_um=frequencies,
        transmission=transmission,
    )
    write_comparison_csv(
        destination=paths["csv"],
        wavelengths_um=wavelengths,
        frequencies_per_um=frequencies,
        reference_flux=reference_flux,
        ring_flux=ring_flux,
        transmission=transmission,
    )

    geometry, run_geometry = build_baseline_run_geometry(
        design=design,
        simulation_spec=simulation_spec,
        run_spec=ring_run_spec,
    )

    summary = {
        **asdict(design),
        **asdict(simulation_spec),
        **asdict(compare_spec),
        "bus_right_x_um": geometry.bus_right_x_um,
        "ring_right_edge_um": max(geometry.ring_center_x_ums) + geometry.ring_outer_radius_um,
        "monitor_center_x_um": run_geometry.monitor_center_x_um,
        "monitor_center_y_um": run_geometry.monitor_center_y_um,
        "monitor_size_y_um": run_geometry.monitor_size_y_um,
        "reference_csv_path": reference_summary["csv_path"],
        "reference_plot_path": reference_summary["plot_path"],
        "ring_csv_path": ring_summary["csv_path"],
        "ring_plot_path": ring_summary["plot_path"],
        "comparison_plot_path": str(paths["comparison_plot"]),
        "transmission_plot_path": str(paths["transmission_plot"]),
        "comparison_csv_path": str(paths["csv"]),
        "summary_json_path": str(paths["json"]),
        "transmission_min": float(np.min(transmission)),
        "transmission_max": float(np.max(transmission)),
    }

    with paths["json"].open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return summary


def write_comparison_plot(
    destination: Path,
    frequencies_per_um: np.ndarray,
    reference_flux: np.ndarray,
    ring_flux: np.ndarray,
) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(frequencies_per_um, reference_flux, label="straight waveguide", linewidth=1.5)
    axis.plot(frequencies_per_um, ring_flux, label="with ring resonators", linewidth=1.5)
    axis.set_xlabel("frequency (1/um)")
    axis.set_ylabel("output flux")
    axis.set_title("Output flux with and without ring resonators")
    axis.grid(True, alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def write_transmission_plot(
    destination: Path,
    frequencies_per_um: np.ndarray,
    transmission: np.ndarray,
) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(frequencies_per_um, transmission, linewidth=1.5)
    axis.set_xlabel("frequency (1/um)")
    axis.set_ylabel("normalized transmission")
    axis.set_title("Transmission ratio with ring / straight waveguide")
    axis.grid(True, alpha=0.25)
    figure.tight_layout()
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def write_comparison_csv(
    destination: Path,
    wavelengths_um: np.ndarray,
    frequencies_per_um: np.ndarray,
    reference_flux: np.ndarray,
    ring_flux: np.ndarray,
    transmission: np.ndarray,
) -> None:
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "wavelength_um",
                "frequency_per_um",
                "reference_flux",
                "ring_flux",
                "normalized_transmission",
            ]
        )
        for wavelength, frequency, reference, ring, ratio in zip(
            wavelengths_um,
            frequencies_per_um,
            reference_flux,
            ring_flux,
            transmission,
            strict=True,
        ):
            writer.writerow([wavelength, frequency, reference, ring, ratio])
