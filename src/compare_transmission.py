from __future__ import annotations

from transmission import run_transmission_comparison


def main() -> None:
    summary = run_transmission_comparison()
    ordered_keys = [
        "bus_right_x_um",
        "ring_right_edge_um",
        "monitor_center_x_um",
        "reference_plot_path",
        "ring_plot_path",
        "comparison_plot_path",
        "transmission_plot_path",
        "comparison_csv_path",
        "summary_json_path",
    ]
    for key in ordered_keys:
        print(f"{key}: {summary[key]}")


if __name__ == "__main__":
    main()
