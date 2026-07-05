# Stage 4 Baseline Run

Stage 4 adds the first actual time-domain simulation run.

## Source choice

The baseline run uses a broadband Gaussian `Ez` source centered on the target
frequency for `1550 nm`.

This is a practical choice for the first transmission spectrum because one run
can cover a wavelength window around the design target.

## Monitor choice

A single flux monitor is placed near the right side of the bus waveguide.

At this stage the saved spectrum is a direct output-flux readout and a simple
normalization by the peak flux inside that same run for plotting convenience.

That means it is a useful first diagnostic, but it is not yet a reference-run
normalized transmission spectrum.

## Baseline run settings

- source center frequency: `1 / 1.55 = 0.645161 1/um`
- source frequency width: `0.30 1/um`
- flux monitor frequency width: `0.30 1/um`
- flux monitor samples: `181`
- source amplitude: `1.0`
- monitor location: near the right side of the bus waveguide
- stop condition: Meep runs until the `Ez` field decays at the monitor point

## Generated artifacts

Running the Stage 4 baseline command writes:

- `docs/reports/stage4_output_flux_spectrum.png`
- `docs/data/stage4_output_flux_spectrum.csv`
- `docs/reports/stage4_run_summary.json`

## Verification strategy

The Stage 4 check runs a lighter simulation and verifies:

1. the plot, CSV, and JSON outputs are created
2. the CSV has the requested number of spectral samples
3. the source is on the left and the monitor is on the right
4. the recorded peak flux is not below the minimum flux
5. the widened wavelength window extends beyond `1.9 um`
