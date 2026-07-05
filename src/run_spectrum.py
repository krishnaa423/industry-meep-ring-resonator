from __future__ import annotations

from spectrum import run_baseline_simulation


def main() -> None:
    summary = run_baseline_simulation()
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
    for key in ordered_keys:
        print(f"{key}: {summary[key]}")


if __name__ == "__main__":
    main()
