# Meep Ring Resonator

This repo is being rebuilt from scratch as a simple Meep + `gdspy` workflow for
a 2D side-coupled ring resonator near the telecom wavelength of 1550 nm.

Current status: Stages 1 through 6 are complete. The environment is verified,
the unit system is fixed, the `gdspy` layout is generated, the matching Meep
geometry preview is built, the baseline spectrum run is in place, and a first
radius-retuning loop plus field-propagation animation are now implemented.

## Repo layout

- `src/` for plain Python scripts and shared helpers
- `docs/` for design notes and generated reports
- `tests/` for lightweight verification scripts

This repo is intentionally not packaged as a Python module. Scripts are meant to
be run directly from the repository root.

## Environment

The intended Conda environment is `meep`.

```bash
/Users/krishnaa/miniconda/bin/conda activate meep
```

Stage 1 verified these packages in that environment:

- `pymeep 1.33.0`
- `gdspy 1.6.13`
- `numpy 2.5.1`
- `matplotlib 3.11.0`

To rerun the environment check:

```bash
/Users/krishnaa/miniconda/envs/meep/bin/python tests/run_stage1_check.py
```

## Unit convention

The project uses Meep's normalized units with a chosen length scale of
`1 unit = 1 um`.

- target wavelength: `lambda0 = 1.55 um`
- target frequency: `f0 = 1 / lambda0 = 0.645161 1/um`
- speed of light in Meep units: `c = 1`

## Stage 1 baseline assumptions

The baseline geometry values are intentionally conservative starting points, not
final optimized photonics dimensions.

- core material: silicon nitride with `n = 2.0`, so `epsilon = 4.0`
- cladding/background: silica with `n = 1.44`, so `epsilon = 2.0736`
- provisional waveguide width: `1.0 um`
- provisional ring waveguide width: `1.0 um`
- provisional ring-to-bus gap sweep center: `0.2 um`
- provisional effective index for resonance estimate: `n_eff = 1.8`
- provisional ring radius: about `4.93 um` from the resonance condition with
  azimuthal mode number `m = 36`

The width is still a design variable. For now, `1.0 um` is a practical first
pass because it matches the requested thickness scale and should be easy to
simulate before we tighten the design with actual transmission results.

## Stage 1 files

- [src/check_environment.py](src/check_environment.py)
- [src/stage1_baseline.py](src/stage1_baseline.py)
- [docs/stage1_baseline.md](docs/stage1_baseline.md)
- [tests/run_stage1_check.py](tests/run_stage1_check.py)

## Stage 2 files

- [src/ring_layout.py](src/ring_layout.py)
- [src/stage2_generate_gds.py](src/stage2_generate_gds.py)
- [docs/stage2_layout.md](docs/stage2_layout.md)
- [tests/run_stage2_check.py](tests/run_stage2_check.py)

Stage 2 writes these generated artifacts:

- `docs/gds/ring_resonator_layout.gds`
- `docs/figures/ring_resonator_layout.svg`
- `docs/reports/stage2_layout_summary.json`

To generate and verify the layout:

```bash
/Users/krishnaa/miniconda/envs/meep/bin/python src/stage2_generate_gds.py
/Users/krishnaa/miniconda/envs/meep/bin/python tests/run_stage2_check.py
```

## Stage 3 files

- [src/meep_geometry.py](src/meep_geometry.py)
- [src/stage3_build_meep_geometry.py](src/stage3_build_meep_geometry.py)
- [docs/stage3_geometry.md](docs/stage3_geometry.md)
- [tests/run_stage3_check.py](tests/run_stage3_check.py)

Stage 3 writes these generated artifacts:

- `docs/figures/stage3_meep_geometry.png`
- `docs/reports/stage3_geometry_summary.json`

To generate and verify the baseline Meep geometry:

```bash
/Users/krishnaa/miniconda/envs/meep/bin/python src/stage3_build_meep_geometry.py
/Users/krishnaa/miniconda/envs/meep/bin/python tests/run_stage3_check.py
```

## Stage 4 files

- [src/meep_baseline_run.py](src/meep_baseline_run.py)
- [src/stage4_run_baseline.py](src/stage4_run_baseline.py)
- [docs/stage4_baseline_run.md](docs/stage4_baseline_run.md)
- [tests/run_stage4_check.py](tests/run_stage4_check.py)

Stage 4 writes these generated artifacts:

- `docs/figures/stage4_output_flux_spectrum.png`
- `docs/data/stage4_output_flux_spectrum.csv`
- `docs/reports/stage4_run_summary.json`

To run and verify the first baseline spectrum:

```bash
/Users/krishnaa/miniconda/envs/meep/bin/python src/stage4_run_baseline.py
/Users/krishnaa/miniconda/envs/meep/bin/python tests/run_stage4_check.py
```

## Stage 5 files

- [src/resonance_retune.py](src/resonance_retune.py)
- [src/stage5_retune.py](src/stage5_retune.py)
- [docs/stage5_retune.md](docs/stage5_retune.md)
- [tests/run_stage5_check.py](tests/run_stage5_check.py)

Stage 5 writes these generated artifacts:

- `docs/figures/stage5_tuned_flux_spectrum.png`
- `docs/data/stage5_tuned_flux_spectrum.csv`
- `docs/figures/stage5_retuned_comparison.png`
- `docs/reports/stage5_tuned_run_summary.json`
- `docs/reports/stage5_retune_recommendation.json`
- `docs/reports/stage5_retune_summary.json`

To run and verify the first retuning pass:

```bash
/Users/krishnaa/miniconda/envs/meep/bin/python src/stage5_retune.py
/Users/krishnaa/miniconda/envs/meep/bin/python tests/run_stage5_check.py
```

## Stage 6 files

- [src/field_animation.py](src/field_animation.py)
- [src/stage6_generate_field_gif.py](src/stage6_generate_field_gif.py)
- [docs/stage6_field_animation.md](docs/stage6_field_animation.md)

Stage 6 writes these generated artifacts:

- `docs/figures/stage6_field_propagation.gif`
- `docs/figures/stage6_field_propagation_preview.png`
- `docs/reports/stage6_field_propagation_summary.json`

## Next stages

1. Add field-frame export so the waveguide-to-ring coupling can be animated.
2. Improve the spectrum pipeline with explicit transmission normalization.
3. Add a multi-gap comparison plot of power vs frequency for different gaps.
