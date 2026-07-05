from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from resonance_retune import build_tuned_design, run_retuned_simulation


def main() -> int:
    tuned_design, recommendation = build_tuned_design()
    summary = run_retuned_simulation()

    comparison_plot = Path(summary["comparison_plot_path"])
    recommendation_json = Path(summary["recommendation_json_path"])
    tuned_summary_json = Path(summary["tuned_summary_json_path"])
    tuned_csv = Path(summary["tuned_csv_path"])
    tuned_plot = Path(summary["tuned_plot_path"])

    assert comparison_plot.exists(), comparison_plot
    assert recommendation_json.exists(), recommendation_json
    assert tuned_summary_json.exists(), tuned_summary_json
    assert tuned_csv.exists(), tuned_csv
    assert tuned_plot.exists(), tuned_plot

    assert summary["tuned_ring_radius_um"] < summary["baseline_ring_radius_um"]
    assert abs(tuned_design.ring_radius_um - recommendation.tuned_ring_radius_um) < 1e-12
    assert 0.6 < summary["radius_scale_factor"] < 0.9

    with recommendation_json.open("r", encoding="utf-8") as handle:
        recommendation_payload = json.load(handle)

    assert recommendation_payload["dip_at_window_edge"] is True
    assert recommendation_payload["tuned_ring_radius_um"] == summary["tuned_ring_radius_um"]

    print(f"Retune comparison plot written to {comparison_plot}")
    print(f"Tuned spectrum written to {tuned_plot}")
    print("Stage 5 check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
