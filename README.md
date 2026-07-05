# Meep Ring Resonator

This repository contains a compact Meep + `gdspy` workflow for a 2D bus
waveguide coupled to a two-row array of ring resonators near the telecom
wavelength of `1.55 um`.

The current design uses:

- one straight bus waveguide
- five lower-row ring resonators coupled directly to the bus
- five upper-row ring resonators coupled to the lower row
- a broad Gaussian source launched from the left
- a right-side flux monitor that measures transmitted power after the
  resonators

The goal is to show how selected frequencies are pulled out of the propagating
wave and stored in the ring array. In the transmission comparison, dips in the
output spectrum indicate frequencies that are being filtered away from the bus
and coupled into the resonators.

## Final visuals

The main output figures are:

- `docs/figures/simulation_layout.png`
- `docs/figures/transmission_comparison.png`
- `docs/figures/field_propagation_no_rings.gif`
- `docs/figures/field_propagation.gif`

The layout figure shows the bus waveguide, both resonator rows, the simulation
cell, and the vertical flux-cut line used for the transmission measurement.

The transmission figure overlays the measured output flux for:

- the straight-waveguide reference case with no resonators
- the resonator-loaded case

The two GIFs show the `Ez` field propagation:

- `field_propagation_no_rings.gif` is the baseline case where energy stays in
  the straight waveguide
- `field_propagation.gif` shows the resonator-loaded structure where power is
  pulled into the ring oscillators and circulates there

## Current geometry

All lengths use Meep's normalized units with `1 unit = 1 um`.

### Materials

- core refractive index: `2.0`
- cladding refractive index: `1.44`

### Bus and rings

- straight waveguide width: `0.8 um`
- ring waveguide width: `0.8 um`
- ring radius: `4.9338 um`
- ring inner radius: `4.5338 um`
- ring outer radius: `5.3338 um`
- bus-to-lower-ring gap: `0.05 um`
- lower-row ring count: `5`
- upper-row ring count: `5`
- horizontal ring-to-ring gap: `1.0 um`
- vertical lower-row to upper-row gap: `0.05 um`

### Placement

- waveguide center line: `y = -5.0 um`
- lower ring row center: `y = 0.7838 um`
- upper ring row center: `y = 11.5014 um`
- simulation cell size: `73.3333 um x 37.25 um`

### Source and monitor

- target wavelength: `1.55 um`
- Gaussian source center frequency: `0.645161 1/um`
- Gaussian source frequency width: `0.30 1/um`
- flux-cut center: `x = 34.9167 um`, `y = -5.0 um`
- flux-cut span: `1.6 um`

## Why there are two ring rows

The lower row is the primary set of resonators that couples directly to the bus
waveguide and removes energy from the through path.

The upper row is not directly coupled to the bus. Instead, it couples to the
lower row and gives the captured energy another place to circulate. In practice
this strengthens the resonance trapping and deepens the transmission dips.

In the current design, that second row is the main reason the normalized
transmission develops a much deeper minimum than the single-row versions.

## Code layout

The code is now organized by job rather than by stage number:

- `src/design.py`
  Defines the shared geometry and material parameters with small dataclasses.
- `src/layout.py`
  Builds the GDS and SVG layout artifacts.
- `src/geometry.py`
  Builds the Meep simulation geometry and the layout preview image.
- `src/spectrum.py`
  Runs a single broadband spectrum simulation.
- `src/transmission.py`
  Runs the reference and resonator cases and compares their output flux.
- `src/animation.py`
  Generates the field propagation GIFs.
- `src/tuning.py`
  Keeps the optional resonance-retuning workflow.

The small script entrypoints are:

- `src/generate_layout.py`
- `src/preview_geometry.py`
- `src/run_spectrum.py`
- `src/compare_transmission.py`
- `src/generate_field_gif.py`
- `src/retune_resonance.py`

## How to run

The intended Conda environment is `meep`.

```bash
/Users/krishnaa/miniconda/bin/conda activate meep
```

### Build the layout

```bash
/Users/krishnaa/miniconda/envs/meep/bin/python src/generate_layout.py
```

### Build the geometry preview

```bash
/Users/krishnaa/miniconda/envs/meep/bin/python src/preview_geometry.py
```

### Run a single broadband spectrum

```bash
/Users/krishnaa/miniconda/envs/meep/bin/python src/run_spectrum.py
```

### Compare transmission with and without resonators

```bash
/Users/krishnaa/miniconda/envs/meep/bin/python src/compare_transmission.py
```

### Generate field animations

```bash
/Users/krishnaa/miniconda/envs/meep/bin/python src/generate_field_gif.py
```

## Checks

The repository still keeps lightweight verification scripts under `tests/`:

- `tests/run_design_check.py`
- `tests/run_layout_check.py`
- `tests/run_geometry_check.py`
- `tests/run_spectrum_check.py`
- `tests/run_tuning_check.py`
- `tests/run_transmission_check.py`

Examples:

```bash
/Users/krishnaa/miniconda/envs/meep/bin/python tests/run_design_check.py
/Users/krishnaa/miniconda/envs/meep/bin/python tests/run_transmission_check.py
```

## Generated files

The important generated files are:

- `docs/gds/ring_resonator_layout.gds`
- `docs/figures/simulation_layout.png`
- `docs/figures/transmission_comparison.png`
- `docs/figures/field_propagation_no_rings.gif`
- `docs/figures/field_propagation.gif`

Diagnostic CSV and JSON outputs are kept under:

- `docs/data/`
- `docs/reports/`

## Interpretation

This project uses a broad Gaussian source so one simulation can probe a band of
frequencies around the `1.55 um` target instead of a single monochromatic tone.

If the resonator-loaded output flux drops below the straight-waveguide reference
at a particular frequency, that frequency is being filtered by the resonator
network. The deeper the dip, the more strongly that frequency is being coupled
out of the bus and into the rings.
