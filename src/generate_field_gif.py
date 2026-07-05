from __future__ import annotations

from animation import run_field_animation


def main() -> None:
    summary = run_field_animation()
    ordered_keys = [
        "frame_count",
        "gif_path",
        "summary_json_path",
    ]
    for key in ordered_keys:
        print(f"{key}: {summary[key]}")


if __name__ == "__main__":
    main()
