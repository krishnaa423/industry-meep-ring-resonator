# Meep Ring Resonator

FDTD simulation of a dielectric ring resonator side-coupled to a waveguide.

## Result

`src/ring_resonator.py` defines a 2D Meep model with a Gaussian source in the
bus waveguide, dielectric ring geometry, and field-frame capture. In a Meep
environment it writes field frames and can be post-processed into
`results/ez_field.gif`.

## Run

```bash
conda install -c conda-forge pymeep imagemagick
python src/ring_resonator.py
```

This project is meant to show photonics simulation setup: geometry, source
placement, PML boundaries, flux monitors, and time-domain visualization.
