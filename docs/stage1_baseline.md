# Stage 1 Baseline

Stage 1 fixes the environment and the initial unit system before any geometry
generation or Meep runs.

## Environment

Verified Conda environment:

- path: `/Users/krishnaa/miniconda/envs/meep`
- Python: `3.12.13`
- Meep: `1.33.0`
- gdspy: `1.6.13`
- numpy: `2.5.1`
- matplotlib: `3.11.0`

## Units

The working length scale is `1 um`.

- `lambda0 = 1.55 um`
- `f0 = 1 / 1.55 = 0.645161 1/um`
- Meep speed of light: `c = 1`

## Material interpretation

The user description mixed permittivity-style and refractive-index-style
language, so Stage 1 locks the baseline to refractive indices:

- silicon nitride core: `n = 2.0`, so `epsilon = 4.0`
- silica background: `n = 1.44`, so `epsilon = 2.0736`

If later we decide to use a different effective 2D material model, this file
should be updated together with the code.

## Provisional geometry baseline

These are starting values, not tuned final values:

- bus waveguide width: `1.0 um`
- ring waveguide width: `1.0 um`
- waveguide thickness input for documentation: `1.0 um`
- ring-to-bus gap: `0.2 um`
- effective index for resonance estimate: `1.8`
- azimuthal mode number: `36`

Using

`m * lambda0 = n_eff * 2 * pi * R`

gives a first-pass ring radius of about `4.93 um`.

## Why `1.0 um` width for now

The right width is still a simulation question. Stage 1 uses `1.0 um` as a
deliberately simple first guess because:

- it is on the same scale as the requested `1.0 um` thickness
- it avoids starting with an extremely narrow layout
- it keeps the first GDS and Meep geometry easy to inspect

Once the baseline transmission run exists, width can be revisited alongside the
gap sweep.
