# v9 spacing-control audit

Design `2026-10-06_all_chords_v9`; display 1100 × 1100; scale 5 pixels/unit.

All nine configurations share consecutive visible baseline distances (px): `68.771644, 74.952524, 74.952526, 181.596196, 74.952526, 74.952524, 68.771644`.

| Set | Family | Target curvature (/px) | Each nearest-neighbor radius (px) | Maximum interval error (px) | Overall spread (px) |
|---|---|---:|---:|---:|---:|
| curvature_maxima | circle | 0.005 | 93.378144 | 1.42e-14 | 400.000000 |
| curvature_maxima | cubic | 0.005 | 92.874206 | 1.14e-13 | 572.364828 |
| curvature_maxima | parabola | 0.005 | 93.107986 | 9.95e-14 | 509.827208 |
| curvature_maxima | quartic | 0.005 | 92.886536 | 1.28e-13 | 553.994930 |
| curvature_maxima | quintic | 0.005 | 92.889994 | 2.56e-13 | 552.399593 |
| original | cubic | 0.000 | 90.798098 | 7.11e-14 | 573.628750 |
| original | line | 0.000 | 90.798098 | 9.95e-14 | 618.949584 |
| original | quartic | 0.000 | 90.826360 | 5.68e-14 | 503.708509 |
| original | quintic | 0.000 | 90.798098 | 8.53e-14 | 541.072927 |

Pixel-grid audit: 288 distinct unperturbed reference geometries (4 counterbalance groups × 9 configurations × 8 contexts). These include reference geometries for original contexts that do not have their own recorded baseline trials. Maximum interval error after integer-pixel drawing: **1.229064 px**. Maximum corresponding-interval difference across configurations at the same context/group: **1.833209 px**. These are rounding measurements, not perceptual thresholds.

The shared central gap is 181.596196 px. Target-to-neighbor radii are equal within each configuration; they are not equal across all configurations. Original radii differ from the circle by up to 2.580045 px. Overall spread and arc lengths are not equated. Perturbations intentionally change distances.

All 24 tests passed, including 1100-pixel rendering of all recorded conditions across all four groups, legacy isolation, original coefficient/scale preservation, target alignment, perturbation rules, trial counts and per-trial CSV writes.

Original controls retain 17 trials/family, with their only baseline at context 1 and only repetition-1 starting assignments. See [ORIGINAL_CONTROLS.md](../ORIGINAL_CONTROLS.md). Historical participant data are untouched.
