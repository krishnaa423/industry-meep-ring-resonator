"""Meep ring-resonator sketch with field-frame output."""

from pathlib import Path

try:
    import meep as mp
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install pymeep from conda-forge before running.") from exc


def main() -> None:
    results = Path("results")
    results.mkdir(exist_ok=True)

    resolution = 32
    cell = mp.Vector3(16, 10, 0)
    pml_layers = [mp.PML(1.0)]
    silicon = mp.Medium(index=3.45)

    geometry = [
        mp.Block(mp.Vector3(mp.inf, 0.45, mp.inf), center=mp.Vector3(), material=silicon),
        mp.Cylinder(radius=1.55, center=mp.Vector3(0, 2.0), material=silicon),
        mp.Cylinder(radius=1.05, center=mp.Vector3(0, 2.0), material=mp.air),
    ]
    sources = [
        mp.Source(
            mp.GaussianSource(frequency=0.22, fwidth=0.06),
            component=mp.Ez,
            center=mp.Vector3(-6.5, 0),
            size=mp.Vector3(0, 0.4),
        )
    ]
    sim = mp.Simulation(
        cell_size=cell,
        boundary_layers=pml_layers,
        geometry=geometry,
        sources=sources,
        resolution=resolution,
    )
    sim.run(mp.at_every(2, mp.output_png(mp.Ez, "-Zc dkbluered")), until=180)


if __name__ == "__main__":
    main()
