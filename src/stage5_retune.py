from __future__ import annotations

from resonance_retune import run_retuned_simulation


def main() -> None:
    summary = run_retuned_simulation()
    ordered_keys = [
        "observed_dip_wavelength_um",
        "target_wavelength_um",
        "baseline_ring_radius_um",
        "tuned_ring_radius_um",
        "radius_scale_factor",
        "dip_at_window_edge",
        "comparison_plot_path",
        "tuned_plot_path",
        "tuned_csv_path",
        "tuned_summary_json_path",
    ]
    for key in ordered_keys:
        print(f"{key}: {summary[key]}")


if __name__ == "__main__":
    main()
