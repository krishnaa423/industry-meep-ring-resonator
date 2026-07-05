from __future__ import annotations

import importlib
import sys


MODULES = ["meep", "gdspy", "numpy", "matplotlib"]


def collect_environment_report() -> dict[str, object]:
    packages: dict[str, dict[str, str]] = {}

    for module_name in MODULES:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            packages[module_name] = {
                "status": "missing",
                "detail": f"{type(exc).__name__}: {exc}",
            }
            continue

        packages[module_name] = {
            "status": "ok",
            "version": getattr(module, "__version__", "unknown"),
        }

    return {
        "python_version": sys.version.split()[0],
        "packages": packages,
    }


def format_environment_report(report: dict[str, object]) -> str:
    lines = [f"python {report['python_version']}"]

    packages = report["packages"]
    for module_name in MODULES:
        module_report = packages[module_name]
        if module_report["status"] == "ok":
            lines.append(f"{module_name} OK {module_report['version']}")
        else:
            lines.append(f"{module_name} MISSING {module_report['detail']}")

    return "\n".join(lines)


def main() -> int:
    report = collect_environment_report()
    print(format_environment_report(report))

    all_present = all(
        package_report["status"] == "ok"
        for package_report in report["packages"].values()
    )
    return 0 if all_present else 1


if __name__ == "__main__":
    raise SystemExit(main())
