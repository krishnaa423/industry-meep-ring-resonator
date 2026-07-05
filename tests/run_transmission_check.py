from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from spectrum import BaselineRunSpec
from geometry import SimulationSpec, build_simulation_geometry
from transmission import TransmissionCompareSpec, run_transmission_comparison
from design import ResonatorBaseline


def main() -> int:
    summary = run_transmission_comparison(
        simulation_spec=SimulationSpec(resolution=16),
        baseline_run_spec=BaselineRunSpec(
            flux_sample_count=41,
            source_frequency_width_per_um=0.24,
            flux_frequency_width_per_um=0.24,
            field_decay_check_interval=30.0,
            field_decay_by=1.0e-4,
        ),
        compare_spec=TransmissionCompareSpec(
            monitor_offset_from_right_edge_um=0.75,
            monitor_span_scale=2.0,
            artifact_stem="transmission_comparison_check",
            summary_stem="transmission_summary_check",
        ),
    )

    comparison_plot = Path(summary["comparison_plot_path"])
    transmission_plot = Path(summary["transmission_plot_path"])
    comparison_csv = Path(summary["comparison_csv_path"])
    summary_json = Path(summary["summary_json_path"])

    assert comparison_plot.exists(), comparison_plot
    assert transmission_plot.exists(), transmission_plot
    assert comparison_csv.exists(), comparison_csv
    assert summary_json.exists(), summary_json

    expected_geometry = build_simulation_geometry(
        design=ResonatorBaseline(),
        spec=SimulationSpec(resolution=16),
    )
    assert summary["monitor_center_x_um"] > summary["ring_right_edge_um"]
    assert abs(summary["bus_right_x_um"] - expected_geometry.bus_right_x_um) < 1e-12

    with comparison_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 41

    with summary_json.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    assert manifest["monitor_center_x_um"] == summary["monitor_center_x_um"]
    assert manifest["transmission_max"] >= manifest["transmission_min"]

    print(f"Comparison plot written to {comparison_plot}")
    print(f"Transmission plot written to {transmission_plot}")
    print("Transmission check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
