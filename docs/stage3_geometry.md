# Stage 3 Meep Geometry

Stage 3 builds the Meep simulation geometry from the same baseline parameters
used for the Stage 2 `gdspy` layout.

## Modeling choice

The GDS file remains the design artifact, but the Meep geometry is built
directly from the same shared parameter set rather than imported from GDS.

That keeps the simulation setup simple while ensuring the layout and Meep model
stay synchronized.

## Meep geometry contents

- background material: silica cladding with `n = 1.44`
- bus waveguide: one `mp.Block`
- ring outer body: one `mp.Cylinder`
- ring inner hole: one `mp.Cylinder` filled with cladding material
- boundary condition: `1.0 um` PML on all sides

## Baseline simulation-domain values

- resolution: `24` pixels per micron
- cell width: `36.0 um`
- cell height: about `16.07 um`
- x margin beyond the bus: `3.0 um` plus PML
- y margin beyond the structure: `3.0 um` plus PML

## Generated artifacts

Running the Stage 3 builder writes:

- `docs/figures/stage3_meep_geometry.png`
- `docs/reports/stage3_geometry_summary.json`

## Verification strategy

The Stage 3 check verifies:

1. the geometry preview artifact is produced
2. the Meep cell size matches the derived geometry calculation
3. the simulation contains the expected three geometry objects
4. the bus width and ring radii match the baseline design values
