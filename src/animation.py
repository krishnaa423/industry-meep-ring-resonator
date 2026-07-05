from __future__ import annotations

import json
import io
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import meep as mp
import numpy as np
from PIL import Image

from spectrum import BaselineRunSpec, build_baseline_simulation
from geometry import FIGURES_DIR, REPORTS_DIR, SimulationSpec
from design import ResonatorBaseline


@dataclass(frozen=True)
class FieldAnimationSpec:
    sample_interval_time: float = 6.0
    until_time: float = 180.0
    frame_duration_ms: int = 120
    dpi: int = 120
    artifact_stem: str = "field_propagation"


def animation_artifact_paths(artifact_stem: str) -> dict[str, Path]:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "gif": FIGURES_DIR / f"{artifact_stem}.gif",
        "json": REPORTS_DIR / f"{artifact_stem}_summary.json",
    }


def run_field_animation(
    design: ResonatorBaseline | None = None,
    simulation_spec: SimulationSpec | None = None,
    run_spec: BaselineRunSpec | None = None,
    animation_spec: FieldAnimationSpec | None = None,
    include_ring: bool = True,
) -> dict[str, object]:
    design = design or ResonatorBaseline()
    simulation_spec = simulation_spec or SimulationSpec()
    run_spec = run_spec or BaselineRunSpec()
    animation_spec = animation_spec or FieldAnimationSpec()

    simulation, _, geometry, _ = build_baseline_simulation(
        design=design,
        simulation_spec=simulation_spec,
        run_spec=run_spec,
        include_ring=include_ring,
    )
    paths = animation_artifact_paths(animation_spec.artifact_stem)

    simulation.init_sim()
    epsilon = simulation.get_array(center=mp.Vector3(), size=simulation.cell_size, component=mp.Dielectric)
    frames: list[np.ndarray] = []

    def capture_frame(sim: mp.Simulation) -> None:
        frame = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Ez)
        frames.append(np.array(frame))

    simulation.run(
        mp.at_every(animation_spec.sample_interval_time, capture_frame),
        until=animation_spec.until_time,
    )

    if not frames:
        raise RuntimeError("No field frames were captured for animation.")

    write_field_gif(
        destination=paths["gif"],
        epsilon=epsilon,
        frames=frames,
        frame_duration_ms=animation_spec.frame_duration_ms,
        dpi=animation_spec.dpi,
    )

    summary = {
        **asdict(design),
        **asdict(simulation_spec),
        **asdict(run_spec),
        **asdict(animation_spec),
        "include_ring": include_ring,
        "cell_size_x_um": geometry.cell_size_x_um,
        "cell_size_y_um": geometry.cell_size_y_um,
        "frame_count": len(frames),
        "gif_path": str(paths["gif"]),
        "summary_json_path": str(paths["json"]),
    }

    with paths["json"].open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return summary


def write_field_gif(
    destination: Path,
    epsilon: np.ndarray,
    frames: list[np.ndarray],
    frame_duration_ms: int,
    dpi: int,
) -> None:
    gif_frames: list[Image.Image] = []
    for ez_field in frames:
        figure, axis = plt.subplots(figsize=(8, 4.5))
        axis.imshow(epsilon.T, origin="lower", cmap="Greys", alpha=0.35, aspect="auto")
        axis.imshow(ez_field.T, origin="lower", cmap="RdBu", alpha=0.9, aspect="auto")
        axis.set_xticks([])
        axis.set_yticks([])
        axis.set_title("Ez field propagation")
        figure.tight_layout()
        buffer = io.BytesIO()
        figure.savefig(buffer, format="png", dpi=dpi)
        buffer.seek(0)
        image = Image.open(buffer).convert("RGB")
        gif_frames.append(image)
        plt.close(figure)

    gif_frames[0].save(
        destination,
        save_all=True,
        append_images=gif_frames[1:],
        duration=frame_duration_ms,
        loop=0,
    )
