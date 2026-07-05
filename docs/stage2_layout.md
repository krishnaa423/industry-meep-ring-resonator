# Stage 2 Layout

Stage 2 turns the baseline ring resonator parameters into a real `gdspy`
layout, writes a GDS file, and saves a lightweight preview figure.

## Geometry convention

- the bus waveguide is centered on `y = 0`
- the ring is centered above the bus waveguide
- the bus waveguide runs from left to right
- the vertical gap is measured from the top of the bus waveguide to the bottom
  of the ring outer edge

## Baseline layout values

- bus length: `30.0 um`
- bus width: `1.0 um`
- ring width: `1.0 um`
- ring gap: `0.2 um`
- ring radius: about `4.93 um`
- ring outer radius: about `5.43 um`
- ring inner radius: about `4.43 um`
- ring center y-position: about `6.13 um`

## Generated artifacts

Running the Stage 2 generator writes:

- `docs/gds/ring_resonator_layout.gds`
- `docs/figures/ring_resonator_layout.svg`
- `docs/reports/stage2_layout_summary.json`

## Verification strategy

The Stage 2 check does three things:

1. regenerates the layout artifacts
2. reopens the written GDS with `gdspy`
3. checks the bus length, bus width, ring size, and ring-to-bus gap against the
   expected parameter values
