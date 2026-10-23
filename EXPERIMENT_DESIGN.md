# Geometry-conditioned contour interpolation: original design

## September 30 update: combined design is now the default

The default now includes **68 spacing-controlled original trials plus 240 matched trials**, or **308 recorded trials plus 20 practice trials**. The matched x², semicircle, x³, x⁴ and x⁵ each have 32 perturbation trials and 16 matched baselines at target curvature 0.005 per pixel. The semicircle has radius 200 pixels and spans 180 degrees; version v8 matches all seven straight-line intervals between consecutive visible dots, including the 181.596-pixel central gap. Nearest-neighbor radii are balanced within each family and differ by at most 0.51 pixels across families. Overall spread and arc lengths still differ. The display is 1100 × 1100 pixels with fixed 5-pixel-per-unit stimulus scale. The old 17 midpoint x² and 17 circle trials are replaced, and all six off-center baselines are removed. Both starting-side repetitions remain. Version v8 retains participant-specific ordering and four pose-counterbalance groups. Set a unique sequential `PARTICIPANT_ID` in run_exp.py and keep groups balanced. See [CURVATURE_MAXIMA_DESIGN.md](CURVATURE_MAXIMA_DESIGN.md) for the current protocol and [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md) for pending confirmatory decisions. Disabling the addition restores the original 216 recorded trials. Version v9 extends the visible-distance rule, analytic-normal perturbations and repetition-1 context assignments to the four retained original families. Their target curvature remains zero and their one baseline covers only context 1. See [ORIGINAL_CONTROLS.md](ORIGINAL_CONTROLS.md). The original-design explanation below describes the legacy generator, not the default combined-mode sampling.

The remainder describes the **original-only mode**, including its former default repetition and movement settings.

Design version: `2026-09-25_midpoint_single_v2`.

This revision implements the requested changes following the first 252-trial pilot. The prior design descriptions are preserved in `docs/archive/pre_revision_v2/`. The pilot CSVs and their analysis remain historical data from the earlier design.

## Hypothesis and scope

The experiment asks how the influence of each visible point depends on surrounding contour geometry. Curve families are stimulus generators, not separate assumed psychological rules. A signed influence can be positive, negative, or zero.

Identification now measures single-point effects only at the midpoint. Off-center targets provide unperturbed interpolation settings. There are no simultaneous two-point trials, so this revision does not test superposition. The optional segmentation block remains separately selected.

## Literature basis for the perturbation change

[Hon, Maloney & Landy (1997), *The influence function for visual interpolation*, Experiment I, printed p. 413 / PDF page 5](https://www.cns.nyu.edu/~msl/papers/honetal97.pdf) reports 4 and 8 arcminute perturbations at the larger scale, with approximately 1 degree between samples. Thus the relative sizes are approximately 4/60 = 6.7% and 8/60 = 13.3%. The methods page was visually checked because text extraction incorrectly rendered “min” as “mm.”

The new default is **8/60 of each point's local baseline spacing**. This selects the larger relative size from that experiment, compared with the earlier pilot's 4%. It gives approximately 8.8–16.8 pixels in this project's default identification stimuli; actual displacements remain recorded.

This is an approximate relative-size adaptation. The paper used approximate arc spacing and shallow parabolas; this program uses mean adjacent chord distances and multiple families, with individual normal directions. No monitor/viewing-distance calibration is assumed, so a project pixel is not equated with an arcminute. A larger shift can improve measurability but is not automatically in a linear regime for every contour. `--small-fraction` remains available for deliberate changes.

The chat “设计插值假设” also describes larger segmentation perturbations (5, 8, 11, 22, 44 arcminutes). Those are a different part of the original study and are not automatically imported into identification.

## Default recorded identification conditions

Nine total dots: eight fixed and one adjustable. Indices are 0–8.

| Target | Conditions per family | Trials per family |
|---|---|---:|
| 3: 35% along the curve | One unperturbed baseline only | 1 |
| 4: 50% along the curve | One baseline + each of 8 fixed dots perturbed in both signs | 17 |
| Total | No paired-dot perturbations | 18 |

Six families × 18 = **108 recorded trials** per repetition: 12 baselines and 96 single-dot trials. The default two repetitions give **216 trials: 24 baselines and 192 single-dot trials**, with starts balanced 108/108. Each repeated condition flips starting side while preserving geometry. Positive and negative trials at a fixed point retain the same requested starting side within a repetition. Both repetitions are shuffled together. The default seed is 63.

Baseline trials already existed and are retained for both targets. There is no distinct geometric baseline for “perturb point 1 by zero” versus “perturb point 2 by zero,” so duplicate zero-displacement point labels are not added.

Every non-midpoint target supplied through `--targets` receives only baseline trials, including in the optional segmentation builder. Segmentation has 150 midpoint trials per repetition at fractions 0.08, 0.16, 0.32, 0.64, giving 300 trials with the default two repetitions. Requesting segmentation targets 3,4 gives 156 trials per repetition, or 312 by default.

Two default identification partitions have 108 trials each (54 per repetition) and preserve complete matched baselines. Changing target/strength settings can change partition balance.

## Stimulus controls retained

- Families: line, parabola, cubic, quartic, quintic, circle.
- Main polynomial coefficients: 0, 0.75, 0.80, 0.90, 1.00 respectively; main circle remains a semicircle.
- Sampling fractions: 0, .11, .23, .35, .50, .65, .77, .89, 1.
- Similarity normalization sets endpoints to a common local frame.
- Reflection and rotation are fixed within matched baseline conditions.
- Single-point shifts use the baseline sampled normal and baseline local spacing.
- Display scale reserves room for the largest planned shift and is fixed within matched comparisons.
- Response is constrained to the baseline normal at the hidden sample.
- Requested starting offsets remain ±70 px, subject to boundary clipping; actual offsets are recorded.
- Main movement increments remain 10, 5, 1 px; direction reversals refine movement.

These controls do not match all geometric variables across families. Target 3 and target 4 have different reflection/rotation assignments. The two default repetitions use opposite starting sides, so their differences include starting-side effects as well as response variability. A baseline offset measures departure from the generating curve; it is not automatically an error in perceived interpolation.

## Twenty progressive practice trials

Practice uses the same materializer, nine-dot display, sampling, rotation/reflection rules, movement line, perturbation routine, controls and submission behavior as the real task. It contains baselines and single-point shifts; off-center practice is always unperturbed.

The depth factor increases linearly from **0.10 on trial 1 to 0.90 on trial 20**. Families are interleaved in three passes through line, circle, parabola, cubic, quartic, quintic, followed by circle and parabola. Thus trial 3 is a shallow parabola and trial 20 is a nearly full-depth parabola.

For polynomial practice, the dense curve is first aligned with its endpoint chord, its perpendicular depth is multiplied by the factor, and it is resampled along arc length. This avoids coefficient/normalization interactions that can make a supposedly shallow sampled S-curve deeper. The line remains straight.

For circle practice, the factor sets sagitta/half-chord, and the half-angle is `2*atan(factor)`. This generates a genuine shallow circular arc, becoming deeper with practice. It is not an ellipse produced by flattening a semicircle. Real trials still use factor 1, a semicircle.

Progression is relative to each family, not a promise that curvature rises across every adjacent pair of different families. Practice stays shallower than the corresponding real baseline. Practice responses are not written to the two experimental CSVs. `--skip-tutorial` skips all 20 practice trials when explicitly selected.

## Marker and visibility repair

The old triangles pointed toward the aperture center even when the response line did not pass through that center. Each triangle now points toward the opposite marker, exactly along the movement axis. Labels are placed beside that axis.

The adjustable dot is drawn after both markers and their labels. Near a marker, it has a small black surround so its white center remains visible on top of the green triangle, including at an endpoint. This changes layering, not the assigned starting position. Z still moves toward the Z marker; positive recorded response still means toward Z, not necessarily upward on screen.

## Recording and use

Run `run_exp.py` directly from PyCharm with the project interpreter. Default flow: instructions, 20 practice trials, 216 recorded trials. The `--repetitions` option defaults to 2 and also doubles the optional segmentation block (150 to 300 midpoint trials; 156 to 312 with targets 3,4). Practice remains 20 trials per launch.

Two timestamped CSVs are created before the welcome screen and updated synchronously after every submitted experimental trial. Each new row includes `design_version`. Existing files are not overwritten. Practice is excluded; completed rows survive an exit during a later trial.

For details of CSV fields and controls, see `README.md`. For plain-language experimental rationale, see `experimental_rationale.md`.

Run checks with:

```text
python -m unittest -v test_experiment
```

Tests cover the revised trial inventory, sign matching, off-center baseline-only rule, gradual practice depth, constant circular curvature, display bounds, normal-response signs, marker orientation, dot-over-marker visibility, all 20 practice trials before recording, and per-trial persistence of both CSVs. Automated display checks use SDL's dummy driver; a physical-display participant pilot remains necessary to judge perceptual difficulty and whether the larger perturbations remain contour-compatible.
