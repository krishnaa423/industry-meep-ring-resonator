from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from meep_baseline_run import BaselineRunSpec, run_baseline_simulation
from meep_geometry import FIGURES_DIR, REPORTS_DIR, SimulationSpec
from stage1_baseline import ResonatorBaseline


DATA_DIR = Path(__file__).resolve().parents[1] / "docs" / "data"
BASELINE_SUMMARY_PATH = REPORTS_DIR / "stage4_run_summary.json"
BASELINE_CSV_PATH = DATA_DIR / "stage4_output_flux_spectrum.csv"


@dataclass(frozen=True)
class RetuneRecommendation:
    target_wavelength_um: float
    observed_dip_wavelength_um: float
    baseline_ring_radius_um: float
    tuned_ring_radius_um: float
    radius_scale_factor: float
    dip_at_window_edge: bool


def stage5_artifact_paths() -> dict[str, Path]:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "comparison_plot": FIGURES_DIR / "stage5_retuned_comparison.png",
        "recommendation_json": REPORTS_DIR / "stage5_retune_recommendation.json",
        "summary_json": REPORTS_DIR / "stage5_retune_summary.json",
    }


def load_baseline_summary(summary_path: Path | None = None) -> dict[str, object]:
    summary_path = summary_path or BASELINE_SUMMARY_PATH
    with summary_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_spectrum_rows(csv_path: Path | None = None) -> list[dict[str, float]]:
    csv_path = csv_path or BASELINE_CSV_PATH
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


def make_retune_recommendation(
    summary_path: Path | None = None,
    csv_path: Path | None = None,
) -> RetuneRecommendation:
    baseline_summary = load_baseline_summary(summary_path)
    rows = load_spectrum_rows(csv_path)

    min_index = min(range(len(rows)), key=lambda index: rows[index]["output_flux"])
    min_row = rows[min_index]
    dip_at_window_edge = min_index in {0, len(rows) - 1}

    target_wavelength_um = float(baseline_summary["wavelength_um"])
    baseline_ring_radius_um = float(baseline_summary["ring_radius_um"])
    observed_dip_wavelength_um = float(min_row["wavelength_um"])
    radius_scale_factor = target_wavelength_um / observed_dip_wavelength_um
    tuned_ring_radius_um = baseline_ring_radius_um * radius_scale_factor

    return RetuneRecommendation(
        target_wavelength_um=target_wavelength_um,
        observed_dip_wavelength_um=observed_dip_wavelength_um,
        baseline_ring_radius_um=baseline_ring_radius_um,
        tuned_ring_radius_um=tuned_ring_radius_um,
        radius_scale_factor=radius_scale_factor,
        dip_at_window_edge=dip_at_window_edge,
    )


def build_tuned_design(
    summary_path: Path | None = None,
    csv_path: Path | None = None,
) -> tuple[ResonatorBaseline, RetuneRecommendation]:
    recommendation = make_retune_recommendation(summary_path=summary_path, csv_path=csv_path)
    tuned_design = ResonatorBaseline(ring_radius_override_um=recommendation.tuned_ring_radius_um)
    return tuned_design, recommendation


def run_retuned_simulation(
    summary_path: Path | None = None,
    csv_path: Path | None = None,
) -> dict[str, object]:
    paths = stage5_artifact_paths()
    tuned_design, recommendation = build_tuned_design(summary_path=summary_path, csv_path=csv_path)

    tuned_summary = run_baseline_simulation(
        design=tuned_design,
        run_spec=BaselineRunSpec(
            artifact_stem="stage5_tuned_flux_spectrum",
            summary_stem="stage5_tuned_run_summary",
            plot_title="Retuned ring resonator transmission",
        ),
    )

    baseline_rows = load_spectrum_rows(csv_path)
    tuned_rows = load_spectrum_rows(DATA_DIR / "stage5_tuned_flux_spectrum.csv")
    write_comparison_plot(
        destination=paths["comparison_plot"],
        baseline_rows=baseline_rows,
        tuned_rows=tuned_rows,
    )

    recommendation_payload = asdict(recommendation)
    with paths["recommendation_json"].open("w", encoding="utf-8") as handle:
        json.dump(recommendation_payload, handle, indent=2, sort_keys=True)
        handle.write("\n")

    retune_summary = {
        **recommendation_payload,
        "comparison_plot_path": str(paths["comparison_plot"]),
        "recommendation_json_path": str(paths["recommendation_json"]),
        "tuned_plot_path": tuned_summary["plot_path"],
        "tuned_csv_path": tuned_summary["csv_path"],
        "tuned_summary_json_path": tuned_summary["summary_json_path"],
        "tuned_wavelength_min_um": tuned_summary["wavelength_min_um"],
        "tuned_wavelength_max_um": tuned_summary["wavelength_max_um"],
        "tuned_peak_flux": tuned_summary["peak_flux"],
        "tuned_minimum_flux": tuned_summary["minimum_flux"],
    }

    with paths["summary_json"].open("w", encoding="utf-8") as handle:
        json.dump(retune_summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return retune_summary


def write_comparison_plot(
    destination: Path,
    baseline_rows: list[dict[str, float]],
    tuned_rows: list[dict[str, float]],
) -> None:
    baseline_wavelengths = np.array([row["wavelength_um"] for row in baseline_rows], dtype=float)
    baseline_flux = np.array([row["normalized_output_flux"] for row in baseline_rows], dtype=float)
    tuned_wavelengths = np.array([row["wavelength_um"] for row in tuned_rows], dtype=float)
    tuned_flux = np.array([row["normalized_output_flux"] for row in tuned_rows], dtype=float)

    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(baseline_wavelengths, baseline_flux, label="baseline", linewidth=1.5)
    axis.plot(tuned_wavelengths, tuned_flux, label="retuned", linewidth=1.5)
    axis.axvline(1.55, color="black", linestyle="--", linewidth=1.0, alpha=0.6)
    axis.set_xlabel("wavelength (um)")
    axis.set_ylabel("normalized output flux")
    axis.set_title("Baseline vs retuned spectrum")
    axis.grid(True, alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(destination, dpi=180)
    plt.close(figure)
