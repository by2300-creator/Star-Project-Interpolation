# Curvature maxima matched to the original parabola

Current new-stimulus version: `2026-09-30_parabola_reference_v5`.

## Running the experiment

Run `run_exp.py` in PyCharm. Set `ENABLE_CURVATURE_MAXIMA = True` for 108 original trials once plus 144 new trials. Set it to `False` for 108 original conditions repeated twice. Command-line overrides are `--curvature-maxima` and `--no-curvature-maxima`. Combined mode contains 252 recorded trials; original-only mode contains 216. Both have 20 unrecorded practice trials. Conditions are shuffled together.

The addition now uses ONE curvature reference, not the former low/high levels. The original parabola's displayed midpoint curvature is 0.005 per pixel, corresponding to a 200-pixel local radius. The generator derives its local curvature (0.025 per unit), sampling positions, and perturbation reference spacings from `generate_function_points('parabola', target_index=4)` with the standard strength and fixed irregular spacing. The standard display scale is 5 pixels per unit. Matching is relative to the original 800-pixel setup, not calibrated visual angle.

## New trial allocation

For each of cubic (x³), quartic (x⁴), and quintic (x⁵):

| Treatment | Allocation | Trials per family |
|---|---|---:|
| Single-dot perturbation | 8 visible dots × 2 signs × 2 starting sides | 32 |
| No perturbation | 8 matched dot-context settings × 2 starting sides | 16 |
| Total | 8 contexts × 3 treatments × 2 starting sides | 48 |

Three families give **144 new trials**. Together with 108 original trials, this gives **252 recorded trials** (192 perturbed, 60 baseline), plus 20 practice trials. No new quadratic trials are added: the original parabola already targets its curvature maximum. Turning the addition off still restores 216 original-only trials.

For each dot context, its baseline and two signs share rotation, reflection, translation, starting side and starting distance. The second repetition flips only starting side. The baseline does not perturb a dot: its context ID identifies which perturbation pair it controls. This gives 16 baseline observations per family, eight from each starting side. Positive/negative treatments are also equally represented from each side. Corresponding contexts match across all three families.

This allocation follows the comparisons needed, rather than a target total of 108. Two starts reduce dependence on the initial response position. A baseline for every context permits baseline subtraction without mixing poses; it also allows testing whether positive and negative effects are symmetric. Conditions are shuffled together, not displayed as adjacent triples. These are controlled measurements per participant, not independent participants or a statistical power calculation. Participant sample size still needs to be planned from the effect or equivalence bound of interest.

Two-way partitions contain 126 trials each and preserve baseline/sign triples. Each participant should complete both partitions if this within-participant allocation is intended.

### Suggested response contrasts

Within each family, context and starting side, denote signed final error by R−, R0 and R+. Compare R+−R0 and R−−R0, and estimate signed sensitivity as (R+−R−)/(2δ), where δ is that dot's perturbation magnitude in pixels. Average the two starting sides after inspecting starting-side effects. Compare these profiles across x³, x⁴ and x⁵. Do not count the 16 baseline trials as 16 different curve families or independent participants.

The original x² is the curvature reference, but its baseline count, poses and sampled-normal perturbation rule differ from the new block. A direct x²-versus-new-family causal contrast is therefore less controlled than comparisons among the three new families. Reusing x² avoids duplicate trials but does not remove those differences.

## Geometry

The generator is `curvature_maxima.py`; it is imported by `run_exp.py` and can be run directly for a numeric audit.

1. Begin with `y = u**n`, n = 3, 4, 5.
2. Select the analytic absolute-curvature maximum. The positive branch is `((n-2)/(n²(2n-1)))**(1/(2n-2))`.
3. Align its tangent horizontally and uniformly scale both axes so peak curvature equals the original parabola reference. Do not flatten one coordinate independently.
4. Resample around the peak using the original parabola's signed analytic arc-length offsets. The missing point is exactly index 4 with four fixed points on each side.
5. Apply a common translation derived from the joint bounding box of all three families. This fits the longer reference window without family-dependent scaling. Apply matched reflection/rotation and small additional translation afterward.
6. Render all new configurations at 5 pixels per unit. Check actual perturbed anchors and baseline bounds; reject a display that cannot fit rather than silently rescale a family.

Signed offsets along the generating curve, in displayed pixels, are approximately:

`[-389.893, -304.116, -210.542, -116.968, 0, 116.968, 210.542, 304.116, 389.893]`.

These are distances ALONG the curve, not radial distances from screen center. The nearest visible neighbors straddle a 233.936-pixel arc-length gap. The original parabola supplies these distances; the three new families retain different spatial dot coordinates.

## Perturbations and matching

For each visible index, use the original parabola's local mean adjacent chord spacing multiplied by `--small-fraction` (default 8/60). The same actual displacement applies to corresponding indices on ALL three new families. At the standard display scale, magnitudes range from approximately **11.433 to 13.936 pixels** across visible indices. Magnitude varies by index, not family.

New perturbation directions remain analytic local normals. The original block uses normals estimated from sampled points. Consequently matching curvature and displacement magnitudes does not guarantee identical perturbation directions to the original block. The new-family comparisons share the same analytic-normal rule.

Rotation, reflection, initial distance and small target translation are matched across families and signs at each dot. Repetition flips starting side. Starting distances range from 45–85 pixels; extra translations range ±2 local units per axis before display rotation. Dot-index poses are balanced across the design, not fully crossed with each dot. Every dot context has its own matched baseline at each starting side; dot identity and pose are still not fully crossed, so spatial influence profiles remain conditional on these poses.

Target curvature is matched, but local curvature away from the target, chord distances, symmetry and distant shape differ. This is a test of whether the matched target geometry and sampling suffice for similar responses. It is not an identical-local-neighborhood test of distant context alone. Prespecify equivalence bounds if claiming invariance. One nonzero perturbation magnitude per index does not test linearity.

## Participant controls and submission rule

Every trial starts at **10 pixels per movement** (`FINE_ADJUSTMENT_DEFAULT = False`). Keys 1/2/3 select 1/5/10 pixels. Reversing direction also refines the effective step automatically.

Enter, Space and mouse Next all use the same gate. Submission is allowed only when:

1. The current effective step is 1 pixel, AND
2. At least one actual 1-pixel-mode movement has occurred during the trial.

Selecting key 1 without moving is not sufficient. After a fine movement, switching back to a coarse step blocks submission again until fine mode is restored. Fine adjustments reached through direction reversals count. A blocked attempt leaves the stimulus and response unchanged and displays “Cannot proceed yet”. Once eligible, it displays “Ready to proceed”. No in-trial step-size or pixel readout is shown. The same rule applies during practice.

Held Enter/Space protection and trial-tagged keyboard submission events remain in place. CSV fields include `fine_moves`, `submission_step_px`, `blocked_submissions`, `initial_step_px`, and `input_version`. This gate enforces use of the control, not perceptual care; it is not proof that every setting is accurate.

## Experimenter viewer: check_exp.py

Run `check_exp.py` directly in PyCharm. It uses the same trial builder, geometry and renderer but skips practice, bypasses the fine-step gate and writes **no participant CSVs**.

- Curve family, stimulus set, repetition, condition and perturbed index/sign are shown.
- A red circle/cross shows the unperturbed generating-curve reference answer (not a uniquely correct completion of the perturbed display).
- C places the adjustable dot at that reference.
- Left/Right: previous/next trial, without submission restrictions.
- Page Up/Page Down: skip backward/forward 10 trials.
- Home/End: first/last trial.
- G, then a number and Enter: jump directly to a trial (Esc cancels number entry).
- Enter/Space/Next: advance at any movement step, even without moving.
- Esc or window close: exit.

Navigation clamps at the first/last trial. Revisiting a trial resets it to its specified initial position. `--start-trial N` selects an initial trial. Other design flags, including `--no-curvature-maxima`, are shared with run_exp.py. `--dry-run` prints the inventory without creating CSVs.

## Recording and validation

Participant mode retains synchronous updates of BOTH CSVs after each accepted trial. Rejected attempts and incomplete trials do not create rows. Practice is excluded. Existing data are untouched.

Use `stimulus_set` and `design_version` to separate original and new data. The new `curvature_level` is `parabola_reference`; `reference_stimulus`, `reference_curvature_px`, sample arc offsets, polynomial parameters, analytic curvatures, display scale, pose and perturbation basis are recorded. The existing three-point curvature estimate need not equal the hidden point's analytic curvature; use the analytic field to audit matching.

Run `python -m unittest test_experiment -q` for checks of geometry, reference matching, arc spacing, repetitions, partitions, per-trial recording, all three submission methods, fine-mode requirements and experimenter navigation/no-recording behavior. Rendered examples are in `docs/curvature_maxima_preview.png` and `docs/check_exp_preview.png`.

The previous two-level design is preserved in `docs/archive/curvature_maxima_v3.md` for interpreting earlier recordings.

The preceding quadratic/cubic/quartic allocation is archived in `docs/archive/curvature_maxima_v4.md`. Version v5 changes the family set and shared display translation; do not pool historical versions without accounting for these changes.
