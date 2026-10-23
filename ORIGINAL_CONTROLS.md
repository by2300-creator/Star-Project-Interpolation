# Controls for the retained original configurations

## What changed?

In the default combined experiment, the original line, cubic, quartic and quintic now use the same seven straight-line distances between consecutive visible dots as the five matched configurations. The generator is `original_controls.py`, called automatically by `run_exp.py` and `check_exp.py`.

Shared visible intervals, in pixels:

`68.772, 74.953, 74.953, 181.596, 74.953, 74.953, 68.772`

The large central interval bridges the missing midpoint. Distances match in intended coordinates; integer-pixel drawing introduces small rounding differences. Moving a dot in a perturbation trial necessarily changes some intervals.

## What remains original?

- The line remains straight.
- The cubic and quintic target remains the central inflection point.
- The quartic target remains its flat center.
- All four target curvatures remain zero.
- Polynomial coefficients and the legacy uniform scales are preserved. Only sample positions, alignment and the controlled trial settings change. Samples can extend beyond the former endpoint parameter where needed; the underlying polynomial is unchanged.

The resampled endpoints are not subsequently resized to 600 pixels. Doing that would undo the spacing match. Target tangents are aligned horizontally before the common display rotation, and the target receives the same common translation as the five matched configurations.

## Shared perturbations, poses and starts

For each of eight dot contexts, copy the corresponding matched-family repetition-1 rotation, reflection, small translation, starting side and starting distance. Both perturbation signs use the same context. The four participant groups rotate the same four pose combinations across contexts. Corresponding baseline target coordinates match across all nine configurations.

Perturbation magnitudes use the same original-parabola spacing reference as the five matched families (approximately 11.433–13.936 pixels). They are not recomputed from each controlled original's own spacing. Directions use the analytic local normal of that original curve. Different local slopes still imply different displacement directions in screen coordinates.

## Allocation and baseline limitation

Each original family retains **16 perturbation trials + 1 baseline = 17 trials**. The baseline uses context 1, matching the negative and positive trials for visible index 0. It does not match the pose/start/translation of the other seven contexts. Metadata explicitly records `baseline_context_scope = context_1_only`.

For any context, `(R+ − R−)/(2δ)` remains a within-context signed sensitivity estimate. For contexts 2–8, baseline-subtracted changes and baseline-relative asymmetry do not have a context-matched baseline. Do not borrow the context-1 baseline and describe it as matched. Original controls also lack the second starting-side repetition present in the five primary families.

Total allocation is unchanged: **68 controlled-original + 240 matched = 308 recorded**, plus **20 practice**. Original controls remain secondary comparisons.

## What is not matched?

| Controlled original | Each target-to-neighbor distance (px) | Overall spread (px) |
|---|---:|---:|
| Line | 90.798 | 618.950 |
| Cubic | 90.798 | 573.629 |
| Quartic | 90.826 | 503.709 |
| Quintic | 90.798 | 541.073 |

Overall spread means the greatest distance between two fixed visible dots. The semicircle has target-to-neighbor distance 93.378 pixels and spread 400 pixels. Equal central gap cannot imply equal target-to-neighbor radius for both a straight line and a curve. The five matched families' 0.51-pixel radius tolerance therefore does not apply to the original controls. Their two radii are instead checked for equality within each configuration.

Arc lengths, nonconsecutive distances, overall spread and higher-order shape properties remain different. These stimuli compare configurations under a shared visible-spacing rule, not isolated global spread or isolated curvature effects.

## Recording and running

Run `run_exp.py` in PyCharm with the addition enabled. The configured window is **1100 × 1100 pixels**, with fixed scale **5 pixels per unit**. The participant controls, practice and two-CSV per-trial recording are retained.

Current combined version: `2026-10-06_all_chords_v9`. Controlled originals retain `stimulus_set = original` and add `geometry_protocol = spacing_controlled_original`, `target_parameter = 0`, `matched_reference_repetition = 1`, and `baseline_context_scope = context_1_only`. Their stimulus/trial IDs start with `controlled_original_`. Shared spacing metadata and actual arc offsets are recorded. The cubic's target curvature derivative is nonzero, even though its target curvature is zero; the metadata preserves this distinction.

Historical data are untouched. Legacy-only mode (`--no-curvature-maxima`), segmentation and practice retain their previous generators. Tests check coefficient/scale preservation, target alignment, normals, spacing, context assignment, 1100-pixel bounds across all four groups, and both CSVs.

[View all nine configurations](docs/original_controls_preview.png) and [read the numerical audit](docs/spacing_control_audit.md).
