# Curvature maxima matched to the original parabola

Current new-stimulus version: `2026-09-29_parabola_reference_v4`.

## Running the experiment

Run `run_exp.py` in PyCharm. Set `ENABLE_CURVATURE_MAXIMA = True` for 108 original trials once plus 108 new trials. Set it to `False` for 108 original conditions repeated twice. Command-line overrides are `--curvature-maxima` and `--no-curvature-maxima`. Both modes contain 216 recorded trials plus 20 unrecorded practice trials. Conditions are shuffled together.

The addition now uses ONE curvature reference, not the former low/high levels. The original parabola's displayed midpoint curvature is 0.005 per pixel, corresponding to a 200-pixel local radius. The generator derives its local curvature (0.025 per unit), sampling positions, and perturbation reference spacings from `generate_function_points('parabola', target_index=4)` with the standard strength and fixed irregular spacing. The standard display scale is 5 pixels per unit. Matching is relative to the original 800-pixel setup, not calibrated visual angle.

## New trial allocation

For each of quadratic (`parabola`), cubic, and quartic:

- 8 visible dots × 2 perturbation signs × 2 repetitions = 32 perturbed trials.
- 4 baseline trials (2 per repetition).
- Total: 36 trials per family; 3 × 36 = **108 new trials**.

Each corresponding repeated condition starts on the opposite side, while pose, sampling, and perturbation remain matched. The two baseline settings within each repetition also have opposite starts. Thus there are two baseline observations per starting side per family. Original conditions appear only once in combined mode. Two-way partitions preserve 108 trials each by splitting new repetitions while retaining their baseline and sign pairs.

## Geometry

The generator is `curvature_maxima.py`; it is imported by `run_exp.py` and can be run directly for a numeric audit.

1. Begin with `y = u**n`, n = 2, 3, 4.
2. Select the analytic absolute-curvature maximum. For n = 2 this is u = 0; otherwise the positive branch is `((n-2)/(n²(2n-1)))**(1/(2n-2))`.
3. Align its tangent horizontally and uniformly scale both axes so peak curvature equals the original parabola reference. Do not flatten one coordinate independently.
4. Resample around the peak using the original parabola's signed analytic arc-length offsets. The missing point is exactly index 4 with four fixed points on each side.
5. Apply a common translation derived from the joint bounding box of all three families. This fits the longer reference window without family-dependent scaling. Apply matched reflection/rotation and small additional translation afterward.
6. Render all new configurations at 5 pixels per unit. Check actual perturbed anchors and baseline bounds; reject a display that cannot fit rather than silently rescale a family.

Signed offsets along the generating curve, in displayed pixels, are approximately:

`[-389.893, -304.116, -210.542, -116.968, 0, 116.968, 210.542, 304.116, 389.893]`.

These are distances ALONG the curve, not radial distances from screen center. The nearest visible neighbors straddle a 233.936-pixel arc-length gap. The quadratic baseline matches the original parabola's relative dot coordinates to numerical precision, up to rigid pose/translation/reflection. Its screen location is not intended to be identical.

## Perturbations and matching

For each visible index, use the original parabola's local mean adjacent chord spacing multiplied by `--small-fraction` (default 8/60). The same actual displacement applies to corresponding indices on ALL three new families. At the standard display scale, magnitudes range from approximately **11.433 to 13.936 pixels** across visible indices. Magnitude varies by index, not family.

New perturbation directions remain analytic local normals. The original block uses normals estimated from sampled points. Consequently the new quadratic baseline and magnitude reference match the original, but the exact perturbed displacement direction need not be identical. The new-family comparisons share the same analytic-normal rule.

Rotation, reflection, initial distance and small target translation are matched across families and signs at each dot. Repetition flips starting side. Starting distances range from 45–85 pixels; extra translations range ±2 local units per axis before display rotation. Dot-index poses are balanced across the design, not fully crossed with each dot. Baselines use one pose, so opposite-sign contrasts are preferable to baseline subtraction across unmatched poses.

Target curvature is matched, but local curvature away from the target, chord distances, symmetry and distant shape differ. This is a test of whether the matched target geometry and sampling suffice for similar responses. It is not an identical-local-neighborhood test of distant context alone. Prespecify equivalence bounds if claiming invariance. One nonzero perturbation magnitude per index does not test linearity.

## Participant controls and submission rule

Every trial starts at **10 pixels per movement** (`FINE_ADJUSTMENT_DEFAULT = False`). Keys 1/2/3 select 1/5/10 pixels. Reversing direction also refines the effective step automatically.

Enter, Space and mouse Next all use the same gate. Submission is allowed only when:

1. The current effective step is 1 pixel, AND
2. At least one actual 1-pixel-mode movement has occurred during the trial.

Selecting key 1 without moving is not sufficient. After a fine movement, switching back to a coarse step blocks submission again until fine mode is restored. Fine adjustments reached through direction reversals count. A blocked attempt leaves the stimulus and response unchanged and displays: “Use 1-pixel moves before submitting. Press 1, then Z or /.” A persistent step-size indicator explains the current mode. The same rule applies during practice.

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
