# Analysis plan: matched-curvature experiment

Status: proposed analysis definitions, not a completed preregistration or power analysis.
This document does not set a participant recruitment target or an equivalence threshold.

## Question and primary comparisons

At target curvature 0.005 per pixel, do different contour configurations produce equivalent signed interpolation biases and dot-perturbation sensitivities? The four primary comparisons are **x² versus semicircle, x² versus x³ maximum, x² versus x⁴ maximum, and x² versus x⁵ maximum**. Treat other pairs, including quartic–quintic, as secondary/exploratory unless separately prespecified. Their weak visual contrast remains by explicit design choice; similarity for that pair alone is weak evidence for general invariance.

Use version `2026-10-06_all_chords_v9` rows with stimulus_set = curvature_maxima for primary matched comparisons: five families × 48 trials = 240. The semicircle has constant curvature, not a unique maximum. All share the same target curvature, consecutive visible baseline chord distances, per-index perturbation magnitudes and nuisance settings. Target-to-neighbor radii are balanced within families and differ by at most 0.51 pixels across families. Overall spread, nonconsecutive distances, arc lengths and curvature away from the target differ, so this does not isolate distant context alone. Analyze influence by dot index with the actual recorded sampling geometry; do not assume v7 arc offsets. Retained original midpoint controls answer separate questions; do not pool them into matched baselines. Off-center trials are excluded from combined mode. Practice is not recorded. The four-group pose assignment must remain balanced across included participants. Conditions from one participant are repeated observations, not independent participants.

## Outcome definitions fixed in the design

Use response_normal_px as the signed final displacement from the generating-curve reference along the recorded response axis (positive along the baseline normal; screen-up controls now log a separate sign mapping). The reference is not assumed to be the unique perceptually correct answer to a perturbed display.

For each participant, family, matched_pose_id and repetition (starting side), identify the baseline R0 and the negative/positive responses R− and R+. Use the recorded sign in perturbation_pattern and actual displacement magnitude δ in pixels, not row order.

- Baseline bias: R0.
- Positive shift: R+ − R0.
- Negative shift: R− − R0.
- Signed sensitivity: (R+ − R−) / (2δ). This measures response pixels per perturbation pixel at the tested magnitude; it is a finite difference, not proof of a linear mechanism.
- Asymmetry: (R+ + R−)/2 − R0. Report this to detect unequal effects of the two signs.

Compare each dot's sensitivity across families; do not collapse the eight-dot profile into a single average that could hide opposing differences. Inspect both starting sides before averaging them. Keep missing triples marked missing; do not substitute a baseline from another pose. The recorded signed axis is identical across families within a context, but reflection changes bending direction: account for pose/reflection when pooling signed biases. Counterbalancing group and starting side must be represented in the analysis.

## Decisions to settle before confirmatory data collection

1. Define the smallest meaningful family difference in bias (pixels or calibrated visual angle) and sensitivity (response pixels per perturbation pixel). Use substantive justification and pilot precision, not a threshold chosen to make results equivalent.
2. The four contrasts against x² are primary. Specify simultaneous inference/multiple-comparison handling across these contrasts, outcomes and dots, and whether the claim concerns the full profile or individual dots. Equivalence of an averaged profile is not equivalence at every dot.
3. Estimate participant count using participant-level variability and within-participant covariance from an independent pilot, with the intended equivalence bounds and analysis. Trial count is not participant sample size.
4. Prespecify exclusion rules, missing-trial handling, breaks, and session duration after observing pilot usability. Fine-step compliance alone is not evidence of careful interpolation.
5. Select the final repeated-measures or hierarchical model and verify its operating characteristics by simulation before using it for confirmatory claims.

Until these decisions are made, describe results as pilot estimates with uncertainty. A nonsignificant difference alone does not establish equivalence. No arbitrary bounds, participant count, or automatic participant exclusions are installed in the program.

## Reproducibility

Record participant_id, session_id, design_version, random_seed (geometry), order_seed, counterbalance_group, pose_combination, trial_uid, matched_pose_id and repetition. Assign sequential IDs P001, P002, ... or explicitly balance groups 0–3. Reusing an ID/session reproduces its sequence; switching order-seed does not change pose assignment. Use the same participant/session/group settings in check_exp.py when inspecting a participant's trial. Both partitions must be completed when claiming the full within-participant allocation; they contain 137 and 171 trials, respectively.

## October 4 protocol boundary

New sessions use stable screen-direction controls and graded unperturbed practice, documented in PRACTICE_FEEDBACK.md. Use input_version, control_up_normal_sign, step_sizes_px, practice_protocol_version and practice_feedback_received when comparing sessions. Do not treat historical no-feedback participants as receiving the new training.

## Semicircle geometry revision

Version v7 has 308 recorded trials and 20 practice trials. Earlier v6 matched contours used a longer arc sampling window, and its original semicircle was not curvature-matched. Historical pilot responses cannot be treated as observations of the same five v7 stimuli. Participant sample-size planning and equivalence margins remain required; adding trials is not a power analysis.

## October 6 spacing and display boundary

Version v8 preserves 308 recorded trials and 20 practice trials, but resamples the polynomial contours to match consecutive visible chord distances. It uses the configured 1100-pixel window at the same 5-pixel-per-unit stimulus scale. Record `screen_size_px`, `sampling_rule`, actual `sample_arc_offsets`, baseline chord distances and residual target-neighbor differences. Integer-pixel rendering introduces small rounding differences. Do not pool v7 and v8 polynomial samples as identical stimuli. Overall spread remains family-dependent; adding spread as a covariate does not by itself separate its effect from family in these fixed configurations.

## v9 controlled-original comparisons

The retained line/cubic/quartic/quintic now share the seven visible baseline intervals, target tangent/location, per-index perturbation magnitudes, analytic-normal rule and repetition-1 context assignments with the primary configurations. They retain their zero target curvature, legacy polynomial coefficients and similarity scales. Their overall spread and nearest-neighbor radii still differ by geometry.

These 68 trials remain secondary: each family has one baseline at context 1 and a positive/negative perturbation pair at each of eight contexts, using only repetition-1 starts. Estimate symmetric finite-difference sensitivity from each matched positive/negative pair. For contexts 2–8, do not compute context-matched baseline shifts or asymmetry by borrowing the context-1 baseline. There are no within-context opposite-start repetitions for these original controls. Curvature, local contour geometry and sampled extent differ between the original and maximum conditions, so their contrast does not isolate curvature alone.

Use `geometry_protocol`, `baseline_context_scope`, `matched_reference_repetition`, target curvature and design version to identify the protocol. The controlled-original IDs differ from legacy IDs. The five primary configurations keep their v8 geometry to numerical precision and full 48-trial allocation; the combined protocol is tagged v9. Prior original data are different stimuli and must not be pooled as identical observations.
