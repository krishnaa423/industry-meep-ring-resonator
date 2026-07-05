# Stage 5 Retuning

Stage 5 uses the observed spectrum from Stage 4 to propose and test a smaller
ring radius.

## Retuning rule

For a first pass, the retuning assumes the resonance wavelength scales roughly
linearly with ring radius:

`lambda ~ R`

So the tuned radius is estimated with

`R_tuned = R_baseline * lambda_target / lambda_observed`

## Why this helps

The baseline resonance dip stayed at the long-wavelength edge of the widened
scan window, which means the original ring was still too large for a 1550 nm
target.

Reducing the ring radius is the simplest first correction.

## Generated artifacts

Running the retuning stage writes:

- `docs/reports/stage5_tuned_flux_spectrum.png`
- `docs/data/stage5_tuned_flux_spectrum.csv`
- `docs/reports/stage5_retuned_comparison.png`
- `docs/reports/stage5_tuned_run_summary.json`
- `docs/reports/stage5_retune_recommendation.json`
- `docs/reports/stage5_retune_summary.json`

## Verification strategy

The Stage 5 check verifies:

1. the retune recommendation is written
2. the tuned radius is smaller than the baseline radius
3. the tuned spectrum artifacts are created
4. the retune comparison plot is created
