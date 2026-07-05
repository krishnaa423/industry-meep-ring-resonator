from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from check_environment import collect_environment_report, format_environment_report
from stage1_baseline import baseline_summary, format_baseline_summary


def main() -> int:
    environment_report = collect_environment_report()
    print(format_environment_report(environment_report))
    print()
    print(format_baseline_summary())

    missing_modules = [
        module_name
        for module_name, package_report in environment_report["packages"].items()
        if package_report["status"] != "ok"
    ]
    if missing_modules:
        raise SystemExit(f"Missing required modules: {', '.join(missing_modules)}")

    summary = baseline_summary()

    assert abs(summary["target_frequency_per_um"] - (1.0 / 1.55)) < 1e-12
    assert summary["core_epsilon"] == 4.0
    assert abs(summary["cladding_epsilon"] - 1.44**2) < 1e-12
    assert summary["waveguide_width_um"] == 1.0
    assert 4.8 < summary["ring_radius_um"] < 5.1

    print()
    print("Stage 1 check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
