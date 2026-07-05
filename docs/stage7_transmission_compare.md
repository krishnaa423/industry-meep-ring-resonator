# Stage 7 Transmission Comparison

Stage 7 computes transmission using two simulations with the same source and
the same right-side flux cut:

1. a straight-waveguide reference run with no ring resonator
2. a ring-resonator run with the resonator restored

## Meep workflow

This follows the Meep tutorial pattern for transmittance spectra:

- define a flux region after constructing the `Simulation`
- run a normalization case to obtain the reference transmitted power
- run the structure case and compare the transmitted flux spectrum

## Geometry changes for transmission

- the waveguide right edge reaches the start of the right PML
- the output monitor is a constant-`x` line cut near the right end
- the monitor sits to the right of the ring resonator

## Generated artifacts

- `docs/reports/stage7_reference_flux.png`
- `docs/reports/stage7_ring_flux.png`
- `docs/figures/transmission_comparison.png`
- `docs/reports/stage7_normalized_transmission.png`
- `docs/data/transmission_comparison.csv`
- `docs/reports/stage7_reference_run_summary.json`
- `docs/reports/stage7_ring_run_summary.json`
- `docs/reports/stage7_transmission_summary.json`

## Verification strategy

The Stage 7 check verifies:

1. the right waveguide edge reaches the right PML start
2. the flux cut is to the right of the resonator
3. the comparison and transmission plots are created
4. the combined CSV and summary JSON are created
