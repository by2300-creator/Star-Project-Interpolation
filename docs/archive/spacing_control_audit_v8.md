# v8 spacing-control audit

Design: `2026-10-06_matched_chords_v8`. Display: 1100 × 1100 pixels; fixed scale 5 px/unit.

Consecutive visible baseline intervals (px): `68.771644, 74.952524, 74.952526, 181.596196, 74.952526, 74.952524, 68.771644`.

| Family | Target-to-neighbor distance, each side (px) | Maximum visible-interval error (px) | Overall spread (px) | Left arc extent (px) | Right arc extent (px) |
|---|---:|---:|---:|---:|---:|
| parabola | 93.107986 | 7.11e-14 | 509.827208 | 312.769790 | 312.769790 |
| circle | 93.378144 | 1.42e-14 | 400.000000 | 314.159265 | 314.159265 |
| cubic | 92.874206 | 1.14e-13 | 572.364828 | 312.628086 | 312.345421 |
| quartic | 92.886536 | 1.28e-13 | 553.994930 | 312.179411 | 312.343465 |
| quintic | 92.889994 | 2.56e-13 | 552.399593 | 312.196405 | 312.340465 |

Pixel-grid check: all 320 matched baseline trials across counterbalance groups 0–3, default geometry seed 63. Largest error of an integer-rendered interval from its intended value: **1.229064 px**. Largest corresponding-interval difference between families at the same context/start/group: **1.833209 px**. These figures describe coordinate rounding, not observer sensitivity.

All five baseline interval patterns match in continuous coordinates. Nearest-neighbor radius differs by up to 0.503938 px from the circle reference, and is equal on both sides within each family. Arc extents and overall spread are intentionally not equated.

Perturbations still move one dot along its analytic normal, changing the relevant distances. Intended-coordinate matching describes unperturbed geometry. All matched trials, including both signs, are checked for display bounds in test_experiment.py. The separate original/practice generators are not subject to the v8 spacing rule.

Run `python curvature_maxima.py` for the intended-coordinate audit, and `python -m unittest test_experiment -q` for geometry, renderer, counterbalancing and recording validation.
