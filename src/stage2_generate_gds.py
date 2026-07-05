from __future__ import annotations

from ring_layout import format_layout_summary, write_layout_artifacts


def main() -> None:
    write_layout_artifacts()
    print(format_layout_summary())


if __name__ == "__main__":
    main()
