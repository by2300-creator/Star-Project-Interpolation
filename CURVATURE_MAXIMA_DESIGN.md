# Matched curvature: polynomial maxima and a semicircle

Current combined-design version: `2026-10-06_all_chords_v9`.

## Running the experiment

Run `run_exp.py` in PyCharm. Set `ENABLE_CURVATURE_MAXIMA = True` for 68 spacing-controlled original trials plus 240 matched trials. Set it to `False` for 108 original conditions repeated twice. Command-line overrides are `--curvature-maxima` and `--no-curvature-maxima`. Combined mode contains 308 recorded trials; original-only mode contains 216. Both have 20 unrecorded practice trials. Conditions are shuffled together.

The target curvature remains **0.005 per pixel**, corresponding to a 200-pixel local radius. The original parabola generator supplies the curvature reference and perturbation amplitudes. Version v8 samples the five matched curves by **straight-line distances between consecutive visible dots**, replacing v7's common arc-length positions.

The configured display is **1100 × 1100 pixels** (`SCREEN_VALUE = 1100`). Both run_exp.py and check_exp.py use this setting. Stimuli still render at **5 pixels per local unit**: increasing the display area does not enlarge the curves, perturbations or movement steps. Pixel dimensions do not specify visual angle; use consistent monitor settings and viewing distance in the physical setup.

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

CSV and manifests record `order_seed`, `counterbalance_group` and `pose_combination`. In v9, retained original trials use the same spacing rule and repetition-1 dot-context assignments as the matched block, including the four-group pose crossing. Their target curvature remains zero, and their one baseline covers context 1 only. Counterbalancing removes the fixed dot/pose association across a balanced participant sample, not within a single participant.

See `ANALYSIS_PLAN.md` for prespecified outcome definitions and decisions intentionally left open before confirmatory collection.

## Geometry

The generator is `curvature_maxima.py`; it is imported by `run_exp.py` and can be run directly for a numeric audit.

1. For polynomial families, begin with `y = u**n`, n = 2, 3, 4, 5. Select the analytic absolute-curvature maximum: u = 0 for n = 2; for n > 2 use the positive branch `((n-2)/(n²(2n-1)))**(1/(2n-2))`.
2. Align the target tangent horizontally and uniformly scale both axes so target curvature equals 0.005 per pixel. Do not flatten one coordinate independently.
3. For the circle, use a genuine **200-pixel radius semicircle**, spanning exactly 180 degrees. In tangent-aligned coordinates it is `x = R sin(theta), y = R(1 − cos(theta))`, with theta from −π/2 to +π/2. The missing midpoint is theta = 0. Its curvature is 1/R = 0.005 per pixel everywhere: it has no unique curvature maximum.
4. Keep the v7 semicircle samples as the spacing reference. For each polynomial, find the two nearest neighbors with **equal distances from the hidden target**, then solve for that distance so their mutual straight-line gap matches the circle's central gap exactly.
5. Starting from those neighbors, walk outward along the unchanged polynomial, locating each next sample at the same straight-line distance as its corresponding semicircle interval. A deterministic bracketed root solver places the samples; it does not move them off their generating curves. This matches all seven intervals between consecutive visible dots. The hidden target remains at index 4, with four samples on each side.
6. Apply a common translation derived from the joint bounds of all five sampled configurations, then matched reflection/rotation and small translation. Corresponding contexts have identical target locations across families.
7. Render at a fixed 5 pixels per unit. Check bounds without resizing individual families.

The seven matched distances between consecutive VISIBLE dots, in pixels, are:

`[68.772, 74.953, 74.953, 181.596, 74.953, 74.953, 68.772]`.

The large middle interval is the gap between indices 3 and 5, spanning the hidden target. It is not an ordinary within-side interval. Sampling is deliberately irregular, but the seven-distance pattern is identical across the five families before perturbation.

Target-to-neighbor distance is equal on the two sides WITHIN each family, but slightly different BETWEEN families:

| Family | Each target-to-neighbor distance (px) | Overall spread (px) |
|---|---:|---:|
| x² | 93.108 | 509.827 |
| Semicircle | 93.378 | 400.000 |
| x³ maximum | 92.874 | 572.365 |
| x⁴ maximum | 92.887 | 553.995 |
| x⁵ maximum | 92.890 | 552.400 |

Overall spread is the largest distance between any two visible fixed dots. It remains different by configuration. Matching every pairwise distance would remove the shape difference; this design matches consecutive visible distances only. Near-target dot coordinates and their implied directions are not identical across families.

The generator rejects an intended-coordinate visible-interval error above 0.000001 pixels, or a target-to-neighbor deviation above 0.51 pixels from the circle reference. These are numerical/geometric checks, **not established perceptual thresholds**. The renderer places dot centers on integer pixels; this adds small rasterization differences. The all-group 1100-pixel audit separately checks those rounding errors, so intended-coordinate matching must not be described as exact screen-pixel matching.

Arc lengths are now allowed to differ. `sample_arc_offsets` records each family's ACTUAL signed analytic arc distances in local units (multiply by the recorded display scale for pixels). `reference_arc_half_window_px` describes the semicircle reference only. The former `matched_arc_half_window_px` field is blank for v8. The semicircle remains a true 180-degree arc with radius 200 pixels.

See [docs/spacing_control_audit.md](docs/spacing_control_audit.md) for the numerical/rendering audit.

## Perturbations and matching

For each visible index, use the original parabola's local mean adjacent chord spacing multiplied by `--small-fraction` (default 8/60). The same actual displacement applies to corresponding indices on ALL five matched families. At the standard display scale, magnitudes range from approximately **11.433 to 13.936 pixels** across visible indices. Magnitude varies by index, not family. These amplitudes are intentionally preserved from v6: they are calculated from the ORIGINAL parabola reference spacing, not the new sampling positions. Thus 13.3% is not the fraction of each new contour’s current spacing.

New perturbation directions remain analytic local normals. The v9 controlled original block also uses analytic local normals and the same per-index amplitudes. Legacy-only and segmentation modes retain their sampled-normal protocol. Corresponding local normals can point differently because curve slopes differ; the direction RULE is shared. Controlled originals retain zero target curvature. See `ORIGINAL_CONTROLS.md` for their 17-trial allocation and baseline limitation.

Rotation, reflection, initial distance and small target translation are matched across families and signs at each dot. Repetition flips starting side. Starting distances range from 45–85 pixels; extra translations range ±2 local units per axis before display rotation. Dot-index poses are balanced across the design, not fully crossed with each dot. Every dot context has its own matched baseline at each starting side; the four participant groups cross dot identity with pose across participants. A single participant still supplies only one pose per dot context.

Target curvature and consecutive visible baseline chord distances are matched. Local curvature away from the target, nonconsecutive distances, total spread, arc length, symmetry and distant shape still differ. Perturbing a dot necessarily changes adjacent distances; the strict matching describes the unperturbed reference displays, not the intentionally perturbed displays. This is a test of whether the matched target geometry and sampling suffice for similar responses. It is not an identical-local-neighborhood test of distant context alone. Prespecify equivalence bounds if claiming invariance. One nonzero perturbation magnitude per index does not test linearity.

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

Use `stimulus_set` and `design_version` to separate original and new data. The new `curvature_level` is `parabola_reference`; `reference_stimulus`, `reference_curvature_px`, sample arc offsets, sample parameters, analytic curvatures, display scale, pose and perturbation basis are recorded. For circle rows, `sample_parameter_kind = circle_angle_radians`, `circle_radius_px = 200`, `circle_arc_span_rad = π`, and `target_location_rule = constant_curvature_arc_midpoint`. The `curvature_maxima` stimulus-set label remains for compatibility. New fields include `sampling_rule`, `reference_visible_chords_px`, `baseline_visible_chords_px`, `visible_chord_max_error_px`, `target_neighbor_distances_px`, `target_neighbor_reference_px`, `target_neighbor_max_error_px`, `baseline_spread_px`, and `screen_size_px`. List fields are JSON arrays. They describe baseline geometry; the existing point coordinates retain the actual perturbations. The existing three-point curvature estimate need not equal the hidden point's analytic curvature; use the analytic field to audit matching.

Run `python -m unittest test_experiment -q` for checks of geometry, reference matching, arc spacing, repetitions, partitions, per-trial recording, all three submission methods, fine-mode requirements and experimenter navigation/no-recording behavior. Rendered examples are in `docs/curvature_maxima_preview.png` and `docs/check_exp_preview.png`.

The previous two-level design is preserved in `docs/archive/curvature_maxima_v3.md` for interpreting earlier recordings.

Earlier v4 and v5 allocations are archived in `docs/archive/`. Version v6 added a matched quadratic and counterbalancing. Its specification is archived in `docs/archive/curvature_maxima_v6.md`. Version v7 adds the matched semicircle, replaces original circle midpoint trials, shortens the shared arc window for all five families and recalculates the common translation. Do not pool versions without accounting for these changes.

## Audit of the reported trial 3

In the former v5 default sequence (seed 63), trial 3 was `quintic_target3_standard`, an original off-center baseline. It deliberately hides index 3, not index 4, and starts the response 70 pixels from the reference along the target normal. It was not a curvature-maximum trial. The third practice trial was a parabola, not a quintic. Legacy-mode tests verify that this historical off-center reference is index 3, that the response moves on the line through that point, and that its starting displacement is correct. No centering bug was found in that condition. Order now depends on participant settings, so identify stimuli by `trial_uid`, not trial number alone. New matched trials all hide index 4 with four samples on each side in arc length; their asymmetric shape need not put that point at the bounding-box or screen center.

### Current allocation revision

Off-center trials have been removed from combined mode. Current combined protocol is version v9; manifests contain 308 trials, all targeting index 4. Historical CSVs are unchanged. Do not pool earlier sampled configurations as identical stimuli: their visible sampling positions differ. Legacy original-only mode retains its historical 216-trial allocation.

## October 4 controls and practice revision

Z/Up now follows screen up and /Down screen down, with outward-pointing guide arrows. Baseline-normal response signs are preserved in CSVs via explicit mapping fields. All 20 practice trials are unperturbed and show three-level reference-agreement feedback for 1.5 seconds. Those control and feedback changes are retained in v8; the semicircle revision changes geometry and allocation as described above. See [PRACTICE_FEEDBACK.md](PRACTICE_FEEDBACK.md) for the normalized thresholds, limitations and paper wording.

## October 6 spacing revision

Version v8 replaces arc-distance matching with consecutive visible chord-distance matching and balanced nearest-neighbor radii. It preserves all 308 recorded trials, 20 practice trials, five-family allocation, target curvatures, perturbation amplitudes, starting sides and counterbalancing. The shared translation is recomputed for the new samples. The v7 specification is archived in `docs/archive/curvature_maxima_v7.md`. Screen size is 1100 pixels; stimulus scale remains 5. Existing participant files are untouched. Separate v8 from earlier stimulus versions in analysis.

## Spacing-controlled originals: v9

`original_controls.py` now resamples the retained line, cubic, quartic and quintic at their original zero-curvature midpoint. It uses the same seven visible intervals and balances the two nearest-neighbor radii, preserving the old polynomial coefficients and similarity scales. It then aligns the target tangent and target position with the matched configurations. The old 600-pixel endpoint normalization is NOT reapplied after resampling.

All 68 original trials retain their allocation (16 singles plus one baseline per family). Perturbation magnitudes, analytic-normal rule, pose, target translation and starting offset match the corresponding repetition-1 context of the five-family block. The single baseline belongs to context 1; it is not a baseline for contexts 2–8. The resulting session still has 308 recorded trials and 20 practice trials. Matched-family geometry is preserved to numerical precision; its version tag changes to v9 to identify the revised combined protocol.

`geometry_protocol = spacing_controlled_original` identifies revised original rows; `stimulus_set = original` is retained. `baseline_context_scope = context_1_only`, `matched_reference_repetition = 1`, and `target_parameter = 0` document their interpretation. New original trial/stimulus IDs have a `controlled_original_` prefix. Previous originals and participant files are not changed. Disabling the addition restores the unchanged historical 216-trial mode; practice and segmentation remain unchanged.

The near-neighbor tolerance of 0.51 pixels describes the five curved matched families only. Controlled originals have target-to-neighbor distances near 90.8 pixels (up to 2.58 pixels below the semicircle), as required by their flat/inflection geometry at the same central gap. Overall spread is still not equated. See [ORIGINAL_CONTROLS.md](ORIGINAL_CONTROLS.md).
