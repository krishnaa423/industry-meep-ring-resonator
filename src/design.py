from __future__ import annotations

from dataclasses import asdict, dataclass
from math import pi


@dataclass(frozen=True)
class MaterialModel:
    core_index: float = 2.0
    cladding_index: float = 1.44

    @property
    def core_epsilon(self) -> float:
        return self.core_index**2

    @property
    def cladding_epsilon(self) -> float:
        return self.cladding_index**2


@dataclass(frozen=True)
class ResonatorBaseline:
    wavelength_um: float = 1.55
    effective_index: float = 1.8
    azimuthal_mode_number: int = 36
    waveguide_width_um: float = 0.8
    ring_waveguide_width_um: float = 0.8
    waveguide_thickness_um: float = 1.0
    ring_gap_um: float = 0.05
    ring_count: int = 5
    ring_to_ring_gap_um: float = 1.0
    ring_row_count: int = 2
    ring_row_gap_um: float = 0.05
    ring_radius_override_um: float | None = None

    @property
    def target_frequency_per_um(self) -> float:
        return 1.0 / self.wavelength_um

    @property
    def ring_radius_um(self) -> float:
        if self.ring_radius_override_um is not None:
            return self.ring_radius_override_um
        return (
            self.azimuthal_mode_number * self.wavelength_um
            / (2.0 * pi * self.effective_index)
        )

    @property
    def ring_circumference_um(self) -> float:
        return 2.0 * pi * self.ring_radius_um


def baseline_summary() -> dict[str, float | int]:
    materials = MaterialModel()
    design = ResonatorBaseline()
    return {
        **asdict(materials),
        "core_epsilon": materials.core_epsilon,
        "cladding_epsilon": materials.cladding_epsilon,
        **asdict(design),
        "target_frequency_per_um": design.target_frequency_per_um,
        "ring_radius_um": design.ring_radius_um,
        "ring_circumference_um": design.ring_circumference_um,
    }


def format_baseline_summary() -> str:
    summary = baseline_summary()
    ordered_keys = [
        "core_index",
        "core_epsilon",
        "cladding_index",
        "cladding_epsilon",
        "wavelength_um",
        "target_frequency_per_um",
        "effective_index",
        "azimuthal_mode_number",
        "waveguide_width_um",
        "ring_waveguide_width_um",
        "waveguide_thickness_um",
        "ring_gap_um",
        "ring_count",
        "ring_to_ring_gap_um",
        "ring_row_count",
        "ring_row_gap_um",
        "ring_radius_um",
        "ring_circumference_um",
    ]
    return "\n".join(f"{key}: {summary[key]}" for key in ordered_keys)


def main() -> None:
    print(format_baseline_summary())


if __name__ == "__main__":
    main()
