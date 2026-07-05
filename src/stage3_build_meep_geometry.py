from __future__ import annotations

from meep_geometry import format_geometry_summary, write_geometry_artifacts


def main() -> None:
    write_geometry_artifacts()
    print(format_geometry_summary())


if __name__ == "__main__":
    main()
