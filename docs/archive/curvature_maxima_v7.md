# Matched curvature: polynomial maxima and a semicircle

Current new-stimulus version: `2026-10-04_matched_semicircle_v7`.

## Running the experiment

Run `run_exp.py` in PyCharm. Set `ENABLE_CURVATURE_MAXIMA = True` for 68 retained original trials plus 240 matched trials. Set it to `False` for 108 original conditions repeated twice. Command-line overrides are `--curvature-maxima` and `--no-curvature-maxima`. Combined mode contains 308 recorded trials; original-only mode contains 216. Both have 20 unrecorded practice trials. Conditions are shuffled together.

The addition now uses ONE curvature reference, not the former low/high levels. The original parabola's displayed midpoint curvature is 0.005 per pixel, corresponding to a 200-pixel local radius. The generator derives its local curvature (0.025 per unit), sampling positions, and perturbation reference spacings from `generate_function_points('parabola', target_index=4)` with the standard strength and fixed irregular spacing. The standard display scale is 5 pixels per unit. Matching is relative to the original 800-pixel setup, not calibrated visual angle.

## New trial allocation

For each of quadratic (x²), semicircle, cubic (x³), quartic (x⁴), and quintic (x⁵):

| Treatment | Allocation | Trials per family |
|---|---|---:|
| Single-dot perturbation | 8 visible dots × 2 signs × 2 starting sides | 32 |
| No perturbation | 8 matched dot-context settings × 2 starting sides | 16 |
| Total | 8 contexts × 3 treatments × 2 starting sides | 48 |

Five families give **240 matched trials**. Replace the original parabola's and circle's 17 midpoint trials each with 48 matched trials each. Remove all six original off-center baselines. Thus 108 − 17 − 17 − 6 = **68 original trials remain** (line, cubic, quartic and quintic, 17 each), giving **308 recorded trials**: 224 perturbed and 84 baseline. There are also 20 practice trials (328 trials in a full session). No repetitions or matched baselines have been reduced. The disabled mode still restores all 108 original conditions twice, or 216 recorded trials.

For each dot context, its baseline and two signs share rotation, reflection, translation, starting side and starting distance. The second repetition flips only starting side. The baseline does not perturb a dot: its context ID identifies which perturbation pair it controls. This gives 16 baseline observations per family, eight from each starting side. Positive/negative treatments are also equally represented from each side. Corresponding contexts match across all five families.

This allocation follows the comparisons needed, rather than a target total of 108. Two starts reduce dependence on the initial response position. A baseline for every context permits baseline subtraction without mixing poses; it also allows testing whether positive and negative effects are symmetric. Conditions are shuffled together, not displayed as adjacent triples. These are controlled measurements per participant, not independent participants or a statistical power calculation. Participant sample size still needs to be planned from the effect or equivalence bound of interest.

Two-way partitions contain 137 and 171 trials (120 matched trials in each) and preserve baseline/sign triples. Each participant should complete both partitions if this within-participant allocation is intended.

### Suggested response contrasts

Within each family, context and starting side, denote signed final error by R−, R0 and R+. Compare R+−R0 and R−−R0, and estimate signed sensitivity as (R+−R−)/(2δ), where δ is that dot's perturbation magnitude in pixels. Average the two starting sides after inspecting starting-side effects. The four primary contrasts compare x² with semicircle, x³, x⁴ and x⁵, respectively. Do not count the 16 baseline trials as 16 different curve families or independent participants.

The new x² now has exactly the same allocation, pose assignment, analytic-normal perturbations and starting-side protocol as semicircle/x³/x⁴/x⁵. The original parabola generator supplies only its curvature and spacing reference. Original midpoint parabola and circle conditions are absent from combined mode, preventing duplication. All original off-center baselines are removed from combined mode.

## Participant assignment and counterbalancing

In `run_exp.py`, set `PARTICIPANT_ID` to a unique value such as P001, P002, P003, P004. `SESSION_ID` distinguishes sessions. The same settings and seed reproduce the same sequence in `run_exp.py` and `check_exp.py`. Reusing the default `pilot` identity repeats its sequence; it is not a participant-registration system.

The order seed is a stable SHA-256-derived integer based on the design seed, participant ID and session ID. It is independent of the geometry seed, so order changes do not accidentally change matched geometry. `--order-seed` permits an explicit reproducible override.

Four counterbalance groups cycle each visible dot through the four combinations of ±15-degree rotation and reflected/unreflected shape. Within a group, all five families and baseline/sign treatments remain matched. Across groups, every dot receives all four poses. Numeric-suffix IDs P001–P004 map to groups 0–3, P005–P008 repeat that cycle. IDs without numeric suffix use a deterministic hash; that does not guarantee equal group sizes. Use sequential IDs or `COUNTERBALANCE_GROUP` / `--counterbalance-group` to maintain equal group sizes, including after exclusions. Groups are assigned per participant, not separately per trial or session.

CSV and manifests record `order_seed`, `counterbalance_group` and `pose_combination`. Original trials retain their existing geometry; the four-group pose crossing applies to the matched block. Counterbalancing removes the fixed dot/pose association across a balanced participant sample, not within a single participant.

See `ANALYSIS_PLAN.md` for prespecified outcome definitions and decisions intentionally left open before confirmatory collection.

## Geometry

The generator is `curvature_maxima.py`; it is imported by `run_exp.py` and can be run directly for a numeric audit.

1. For polynomial families, begin with `y = u**n`, n = 2, 3, 4, 5. Select the analytic absolute-curvature maximum: u = 0 for n = 2; for n > 2 use the positive branch `((n-2)/(n²(2n-1)))**(1/(2n-2))`.
2. Align the target tangent horizontally and uniformly scale both axes so target curvature equals 0.005 per pixel. Do not flatten one coordinate independently.
3. For the circle, use a genuine **200-pixel radius semicircle**, spanning exactly 180 degrees. In tangent-aligned coordinates it is `x = R sin(theta), y = R(1 − cos(theta))`, with theta from −π/2 to +π/2. The missing midpoint is theta = 0. Its curvature is 1/R = 0.005 per pixel everywhere: it has no unique curvature maximum.
4. Resample ALL five families at common signed arc-length offsets. Preserve the old irregular ratios, but reduce the half-window from 389.893 to **314.159 pixels** (πR/2). Keeping the old window would require a 223.4-degree circular arc, not a semicircle. This changes the sampled extent of each polynomial; it does not change its target curvature or stretch its shape. The missing point is index 4 with four samples on each side.
5. Apply a common translation derived from the joint bounding box of all five families. Apply matched reflection/rotation and small additional translation afterward. Corresponding contexts have identical target positions across families.
6. Render all matched configurations at 5 pixels per unit. Check actual perturbed anchors and baseline bounds; reject a display that cannot fit rather than silently rescale a family.

Signed offsets along the generating curve, in displayed pixels, are approximately:

`[-314.159, -245.044, -169.646, -94.248, 0, 94.248, 169.646, 245.044, 314.159]`.

These are distances ALONG the curve, not distances from screen center. The nearest visible neighbors straddle a **188.496-pixel arc-length gap**. Corresponding dots have equal arc-distance positions across families, but generally different chord distances and spatial coordinates. The hidden target's curvature, tangent, sampling window and experimental allocation are matched; the entire visible local neighborhood is not identical.

## Perturbations and matching

For each visible index, use the original parabola's local mean adjacent chord spacing multiplied by `--small-fraction` (default 8/60). The same actual displacement applies to corresponding indices on ALL five matched families. At the standard display scale, magnitudes range from approximately **11.433 to 13.936 pixels** across visible indices. Magnitude varies by index, not family. These amplitudes are intentionally preserved from v6: they are calculated from the ORIGINAL parabola reference spacing, not the newly shortened sampling window. Thus 13.3% is not the fraction of each new contour’s current spacing.

New perturbation directions remain analytic local normals. The original block uses normals estimated from sampled points. Consequently matching curvature and displacement magnitudes does not guarantee identical perturbation directions to the original block. The new-family comparisons share the same analytic-normal rule.

Rotation, reflection, initial distance and small target translation are matched across families and signs at each dot. Repetition flips starting side. Starting distances range from 45–85 pixels; extra translations range ±2 local units per axis before display rotation. Dot-index poses are balanced across the design, not fully crossed with each dot. Every dot context has its own matched baseline at each starting side; the four participant groups cross dot identity with pose across participants. A single participant still supplies only one pose per dot context.

Target curvature is matched, but local curvature away from the target, chord distances, symmetry and distant shape differ. This is a test of whether the matched target geometry and sampling suffice for similar responses. It is not an identical-local-neighborhood test of distant context alone. Prespecify equivalence bounds if claiming invariance. One nonzero perturbation magnitude per index does not test linearity.

## Participant controls and submission rule

Every trial starts at **30 pixels per movement** (`FINE_ADJUSTMENT_DEFAULT = False`). Keys 1/2/3 select 1/10/30 pixels. Reversing direction also refines the effective step automatically.

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
- Window close: exit. Esc never exits; it only cancels active jump-number entry.

Navigation clamps at the first/last trial. Revisiting a trial resets it to its specified initial position. `--start-trial N` selects an initial trial. Other design flags, including `--no-curvature-maxima`, are shared with run_exp.py. `--dry-run` prints the inventory without creating CSVs.

## Recording and validation

Participant mode retains synchronous updates of BOTH CSVs after each accepted trial. Rejected attempts and incomplete trials do not create rows. Practice is excluded. Existing data are untouched.

Use `stimulus_set` and `design_version` to separate original and new data. The new `curvature_level` is `parabola_reference`; `reference_stimulus`, `reference_curvature_px`, sample arc offsets, sample parameters, analytic curvatures, display scale, pose and perturbation basis are recorded. For circle rows, `sample_parameter_kind = circle_angle_radians`, `circle_radius_px = 200`, `circle_arc_span_rad = π`, and `target_location_rule = constant_curvature_arc_midpoint`. For every matched row, `matched_arc_half_window_px = 314.159…`. The `curvature_maxima` stimulus-set label is retained for compatibility; the circle target is a constant-curvature midpoint. The existing three-point curvature estimate need not equal the hidden point's analytic curvature; use the analytic field to audit matching.

Run `python -m unittest test_experiment -q` for checks of geometry, reference matching, arc spacing, repetitions, partitions, per-trial recording, all three submission methods, fine-mode requirements and experimenter navigation/no-recording behavior. Rendered examples are in `docs/curvature_maxima_preview.png` and `docs/check_exp_preview.png`.

The previous two-level design is preserved in `docs/archive/curvature_maxima_v3.md` for interpreting earlier recordings.

Earlier v4 and v5 allocations are archived in `docs/archive/`. Version v6 added a matched quadratic and counterbalancing. Its specification is archived in `docs/archive/curvature_maxima_v6.md`. Version v7 adds the matched semicircle, replaces original circle midpoint trials, shortens the shared arc window for all five families and recalculates the common translation. Do not pool versions without accounting for these changes.

## Audit of the reported trial 3

In the former v5 default sequence (seed 63), trial 3 was `quintic_target3_standard`, an original off-center baseline. It deliberately hides index 3, not index 4, and starts the response 70 pixels from the reference along the target normal. It was not a curvature-maximum trial. The third practice trial was a parabola, not a quintic. Legacy-mode tests verify that this historical off-center reference is index 3, that the response moves on the line through that point, and that its starting displacement is correct. No centering bug was found in that condition. Order now depends on participant settings, so identify stimuli by `trial_uid`, not trial number alone. New matched trials all hide index 4 with four samples on each side in arc length; their asymmetric shape need not put that point at the bounding-box or screen center.

### Current allocation revision

Off-center trials have been removed from combined mode. Current geometry is version v7; manifests contain 308 trials, all targeting index 4. Historical CSVs are unchanged. Do not pool earlier matched polynomial data with v7 as identical stimuli: their visible sampling windows differ. Legacy original-only mode retains its historical 216-trial allocation.

## October 4 controls and practice revision

Z/Up now follows screen up and /Down screen down, with outward-pointing guide arrows. Baseline-normal response signs are preserved in CSVs via explicit mapping fields. All 20 practice trials are unperturbed and show three-level reference-agreement feedback for 1.5 seconds. Those control and feedback changes are retained in v7; the semicircle revision changes geometry and allocation as described above. See [PRACTICE_FEEDBACK.md](PRACTICE_FEEDBACK.md) for the normalized thresholds, limitations and paper wording.
