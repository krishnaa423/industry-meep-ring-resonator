from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from meep_baseline_run import BaselineRunSpec, run_baseline_simulation
from meep_geometry import SimulationSpec


def main() -> int:
    summary = run_baseline_simulation(
        simulation_spec=SimulationSpec(resolution=16),
        run_spec=BaselineRunSpec(
            flux_sample_count=41,
            source_frequency_width_per_um=0.24,
            flux_frequency_width_per_um=0.24,
            field_decay_check_interval=30.0,
            field_decay_by=1.0e-4,
        ),
    )

    plot_path = Path(summary["plot_path"])
    csv_path = Path(summary["csv_path"])
    json_path = Path(summary["summary_json_path"])

    assert plot_path.exists(), plot_path
    assert csv_path.exists(), csv_path
    assert json_path.exists(), json_path

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 41
    first_row = rows[0]
    last_row = rows[-1]
    assert float(first_row["wavelength_um"]) < float(last_row["wavelength_um"])

    with json_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    assert manifest["resolution"] == 16
    assert manifest["source_center_x_um"] < 0.0
    assert manifest["monitor_center_x_um"] > 0.0
    assert manifest["peak_flux"] >= manifest["minimum_flux"]
    assert manifest["wavelength_max_um"] > 1.9

    print(f"Flux plot written to {plot_path}")
    print(f"Flux CSV written to {csv_path}")
    print("Stage 4 check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
