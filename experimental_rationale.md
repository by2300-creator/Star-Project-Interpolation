# Experimental rationale: current stimuli, manipulations, and controls

## September 30 addition: invariance across contour configurations

The default now includes **68 spacing-controlled original trials plus 240 matched trials**, or **308 recorded trials plus 20 practice trials**. The matched x², semicircle, x³, x⁴ and x⁵ each have 32 perturbation trials and 16 matched baselines at target curvature 0.005 per pixel. The semicircle has radius 200 pixels and spans 180 degrees; version v8 matches all seven straight-line intervals between consecutive visible dots, including the 181.596-pixel central gap. Nearest-neighbor radii are balanced within each family and differ by at most 0.51 pixels across families. Overall spread and arc lengths still differ. The display is 1100 × 1100 pixels with fixed 5-pixel-per-unit stimulus scale. The old 17 midpoint x² and 17 circle trials are replaced, and all six off-center baselines are removed. Both starting-side repetitions remain. Version v8 retains participant-specific ordering and four pose-counterbalance groups. Set a unique sequential `PARTICIPANT_ID` in run_exp.py and keep groups balanced. See [CURVATURE_MAXIMA_DESIGN.md](CURVATURE_MAXIMA_DESIGN.md) for the current protocol and [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md) for pending confirmatory decisions. Disabling the addition restores the original 216 recorded trials. Version v9 extends the visible-distance rule, analytic-normal perturbations and repetition-1 context assignments to the four retained original families. Their target curvature remains zero and their one baseline covers only context 1. See [ORIGINAL_CONTROLS.md](ORIGINAL_CONTROLS.md). The original-design explanation below describes the legacy generator, not the default combined-mode sampling.

See [CURVATURE_MAXIMA_DESIGN.md](CURVATURE_MAXIMA_DESIGN.md) for the complete current allocation, controls, remaining confounds and CSV interpretation. `ENABLE_CURVATURE_MAXIMA = False` restores the original 108 conditions repeated twice. Practice remains 20 trials. Both modes start coarse, require fine movement and fine mode before submission, and guard against held/stale keyboard confirmations. The experimenter viewer `check_exp.py` bypasses the submission rule and shows the reference answer.

**The sections below describe the original design retained as the comparison set and off-switch mode.** Their two-repetition counts apply when the addition is disabled, and their coarse-start description now also requires the fine-adjustment submission rule above.

Current revision: `2026-09-25_midpoint_single_v2`. This document describes the revised experiment, not the earlier 252-trial pilot. The previous explanation is preserved in `docs/archive/pre_revision_v2/experimental_rationale.md`.

## 1. What question does the experiment ask?

When a set of dots suggests a smooth path, how do people decide where the path should pass between them? We measure this by asking participants to move one dot until it seems to belong to the path.

Then we deliberately shift a different, fixed dot. If that change alters the participant's setting, the displaced dot has influenced the perceived completion. By trying different dots and different shapes, we can study how that influence depends on the surrounding geometry.

The intended explanation concerns the shape people infer, not their ability to recognize polynomial equations. A curve's name is a way to generate stimuli, not a label shown to participants or an assumed mental rule.

## 2. Important terms in ordinary words

| Term | Meaning |
|---|---|
| Stimulus | The visual pattern shown on one trial |
| Trial | One adjustment followed by a submitted setting |
| Target | The original point replaced by the adjustable dot |
| Baseline | A condition in which none of the fixed dots is displaced |
| Perturbation | A deliberate displacement of a fixed dot |
| Manipulation | Something the experiment changes to ask a question |
| Control | Something held constant, matched, or balanced to make comparisons interpretable |
| Curvature | How strongly a path bends at a location |
| Curvature variation | How the amount of bending changes along the path |
| Normal | A direction perpendicular to the estimated contour at a point |
| Influence | How much a fixed-dot shift changes the target setting |

## 3. Participant experience

The screen shows eight fixed white dots and one movable white dot inside a dark circular area. A connecting curve is not drawn. The participant imagines the path and positions the movable dot where it seems to fit.

The target moves along one line, indicated by green endpoint markers. Z or Up moves toward the Z marker; / or Down moves toward the / marker. Keys 1, 2, and 3 select 1-, 5-, and 10-pixel steps. Switching movement direction automatically reduces the step size. Enter, Space, or Next submits the setting.

The program does not show the hidden generating-curve position as a correct answer. It records departure from that position as a consistent reference. A systematic departure may reflect an interesting perceptual completion rather than an ordinary accuracy failure.

## 4. Shape manipulation: six curve families

The main experiment uses a line, parabola, cubic, quartic, quintic, and semicircle. Polynomial coefficients before normalization are 0, 0.75, 0.80, 0.90, and 1.00 respectively.

These shapes supply different bending patterns:

- The line stays straight everywhere.
- The circle has constant curvature.
- The parabola changes its bending along a bowl-shaped path.
- The quartic has an especially flat central region, then bends more strongly away from the middle.
- Cubic and quintic shapes have an S-like structure but different distributions of bending.

This provides a useful range of surrounding geometries. However, changing family changes more than one property at a time. A difference between a circle and a polynomial does not by itself isolate curvature variation as the cause. The current design does not explicitly match all families for target curvature and spacing.

These are samples of individual polynomial curves and circular arcs, not fitted spline algorithms. A quintic stimulus does not establish that participants use a quintic interpolation rule.

## 5. Target-location manipulation: target 3 and target 4

Nine original positions are numbered 0–8. There is only one adjustable dot on a trial.

| Target | Which point? | Place along the original curve | Current conditions |
|---|---|---|---|
| 3 | Fourth point | 35%, off-center | Baseline only |
| 4 | Fifth point | 50%, midpoint | Baseline and single-dot perturbations |

Percentages refer to distance along the curve, not screen width. Rotation can change the point's screen location without changing its index.

### Why retain the off-center target?

The midpoint is a special location with particular symmetry and, in several families, zero exact curvature. An off-center baseline asks where participants interpolate away from that special position.

The revised off-center trials measure **unperturbed completion only**. They no longer estimate how each fixed dot influences an off-center response. This is the consequence of removing all off-center perturbations as requested.

### Why concentrate perturbations at the midpoint?

It gives one consistent target location for mapping the eight fixed dots' influences across all six shapes. The line, cubic, quartic, and quintic have zero analytic curvature at the midpoint, while their surrounding neighborhoods differ. This helps motivate a test of surrounding geometry.

Exact mathematical curvature and curvature estimated from three visible samples are different quantities. The latter can be nonzero even when the generating curve's exact midpoint curvature is zero.

Target comparisons also retain limitations: target location changes neighbor arrangement and local geometry, and the two target configurations have separate rotation/reflection assignments. A response difference is not automatically caused by location alone.

## 6. Perturbed-point manipulation: every fixed point, one at a time

For target 4, points 0, 1, 2, 3, 5, 6, 7, and 8 each receive their own positive and negative perturbation trials. The target itself is never selected as a perturbed fixed point.

This asks how far influence extends along the contour. Immediate neighbors may matter strongly, while more distant points may have weaker, absent, or even negative influence. Testing only immediate neighbors would not reveal this spatial pattern.

Point labels describe order, not equal physical distance. Analysis should use the saved coordinates and spacing measures when comparing influence with distance.

## 7. Perturbation magnitude: why it increased

The earlier pilot used 4% of local spacing, corresponding to approximately 2.64–5.60 pixels. That session showed frequent coarse responses: 200 of 252 settings were on 10-pixel multiples, and only 18 trials used any 1-pixel movement. Small effects were therefore difficult to resolve with the adjustment behavior observed.

The new default is **13.3% of baseline local spacing**, selected using the upper relative perturbation size in the original influence-function study referenced in “设计插值假设.” The original units and derivation are documented and linked in `EXPERIMENT_DESIGN.md`.

In this project's default display, the new displacements are approximately 8.8–16.8 pixels. They are not a fixed pixel amount: a point with a larger baseline gap gets a proportionally larger shift.

This is a pilot choice supported by the source comparison and the earlier recording. It is not proof that responses will be linear at this size on every shape. The original study used different contours and display calibration. The current program does not equate pixels with visual angle.

Only one nonzero identification magnitude is used by default. Consequently, the revised block cannot test whether doubling perturbation doubles the response. Testing proportionality requires additional magnitudes.

## 8. Opposite signs and matched comparisons

Each selected fixed point shifts in both directions along its original normal. “Positive” is a mathematical direction, not necessarily upward on the screen.

To estimate influence, compare the setting in the positive trial with the setting in its matched negative trial, and divide by the difference in actual fixed-point displacement. For example, a 2-unit response difference across a 4-unit displacement difference gives an influence estimate of 0.5. This is an illustration, not a predicted result.

Matched trials retain the same original coordinates, family strength, target, sampling, orientation, reflection, display scale, and requested starting side. This reduces alternative explanations for their response difference.

Influence can be positive, zero, or negative. It is not a probability or percentage of attention, and influences need not sum to one.

## 9. Unperturbed baselines: already present and retained

Every shape has one midpoint baseline and one off-center baseline per repetition. The participant makes the same adjustment, but all eight fixed points remain on the original contour.

The baseline helps identify a general tendency in the perceived completion. If someone places a target 30 pixels from the generating curve even without perturbation, a similar offset on a perturbed trial should not be labeled a 30-pixel perturbation effect.

Zero displacement at fixed point 1 produces the same stimulus as zero displacement at fixed point 2. There is therefore one baseline condition per shape/target, not eight identical baseline labels. Each baseline condition now appears twice, like every perturbed condition.

One observation per condition is a pilot setting. Repeated settings are needed to distinguish reliable completion biases from response variability.

## 10. Two-dot perturbations have been removed

The earlier design included four conditions that moved both neighbors of the target. Those trials tested whether their effects added together.

There are now **no simultaneous two-dot perturbations** in identification or practice. This reduces trial count and focuses the experiment on individual-dot effects. The revised data cannot directly test superposition or interaction between two simultaneous perturbations. Old paired-trial CSV fields remain for compatibility with earlier data.

## 11. Why twenty gradual practice trials?

The goal is to introduce the real task and shape families gradually. Practice uses the same nine-dot display, movement controls, response constraint, sampling method, rotation/reflection, and submission behavior as experimental trials.

The 20 trials interleave all six families. Shape depth increases from 10% at the beginning to 90% at the end, relative to the main family. The first parabola appears on trial 3 and is quite shallow; the final parabola on trial 20 is close to, but flatter than, its experimental version.

For polynomials, the program flattens the normalized contour perpendicular to its endpoint chord and then resamples it. Reducing the raw coefficient alone was insufficient because normalization and sampling could make an S-shaped practice contour unexpectedly deep.

For circles, practice uses shallow genuine circular arcs with increasing depth. Flattening a semicircle vertically would create an ellipse, so that shortcut is not used. The straight-line family remains straight because it has no bending to increase.

This progression is defined within each family. Since families alternate, one trial's numerical curvature need not exceed the previous trial's curvature. Practice includes baseline and single-dot conditions, with no off-center perturbations.

Practice is unrecorded and does not show a correct-answer contour. It teaches the task without adding practice settings to the experimental dataset. It also does not enforce an arbitrary accuracy criterion or require participants to use a certain number of keypresses. Fine adjustment remains available but must still be checked in the next pilot.

## 12. Visual controls and the green-marker repair

All experimental conditions use the same dot color and radius. Equations, axes, and family names are not displayed. The markers show the allowed response direction, so the task measures constrained interpolation rather than unrestricted two-dimensional placement.

Previously, the green triangles pointed toward the display center. When the movement line missed that center, the triangles could point in a different direction from the actual path. They now point toward the opposite marker, following the movement axis exactly.

The white adjustable dot is drawn on top of markers and labels, with a small dark surround when near an arrow. Thus a dot at an endpoint remains visible. This does not move the start position to an arrow; it fixes the drawing order wherever overlap occurs.

The key mapping and CSV response sign are unchanged. Z selects the Z endpoint, and positive recorded response means toward that endpoint.

## 13. Other controls retained

### Sampling and normalization

All families use the same normalized arc fractions: 0, .11, .23, .35, .50, .65, .77, .89, 1. Baseline endpoint separation is standardized using shape-preserving translation, rotation and uniform scaling.

These controls do not make every gap identical in pixels or equate total path length across families. Local spacing is based on neighboring chord distances.

### Baseline geometry and display scale

Normals and spacing come from the original contour. A perturbation does not redefine its own direction or rotate the target's response line. Display scale reserves space for the largest planned shift and stays the same within matched conditions.

### Starting positions

Requested starts remain ±70 pixels, balanced 108/108 in the complete default identification design. Opposite-sign single-dot pairs begin on the same side within each repetition. Repeating a condition flips the starting side while retaining the stimulus geometry. Actual starting positions can be clipped near a boundary and are saved.

Overall balance does not eliminate within-condition anchoring. The exact ±70 start and 10-pixel coarse step also remain capable of producing a seven-move path to the reference. This has not been changed beyond the user's requested revision and remains a pilot consideration.

### Orientation and order

Baseline rotation ranges from −22.5° to +22.5°, with reflection assigned by family/target. These are fixed within matched comparisons. Trial order is shuffled with a recorded seed; the default is 63. Changing only the participant label does not change that order.

This provides variation but is not a fully crossed test of orientation invariance. Repetitions, orientation controls, viewing distance, monitor calibration, breaks, and inclusion rules still require an explicit collection protocol.

## 14. Current trial counts

For each of six families, per repetition:

- 1 off-center baseline.
- 1 midpoint baseline.
- 8 fixed points × 2 signs = 16 midpoint single-dot trials.

Therefore: **6 × 18 × 2 repetitions = 216 recorded trials**, preceded by **20 unrecorded practice trials**. The normal complete run contains **236 adjustment trials** in total. This gives 24 baselines and 192 single-dot trials. Both repetitions are shuffled together, and the CSV repeat number identifies them. Repetitions multiply the recorded design; practice remains a 20-trial introduction per launch. Two observations provide a first check of consistency, but because starting side flips between repeats, differences may include starting-side effects as well as response variability.

The optional segmentation block remains separate, with 150 midpoint trials per repetition, or 300 with the default two repetitions. Its larger magnitude series is unchanged. If off-center targets are explicitly requested there, they are baseline-only as well: targets 3,4 produce 312 recorded trials with two repetitions.

Optional two-way identification partitioning gives 108 recorded trials per partition with two repetitions while retaining complete matched baselines. Practice runs on each launch unless explicitly skipped. Use `--repetitions 1` if the former 108-trial full-session length is needed.

## 15. Recording and interpretation

The two CSVs are created before the welcome screen and updated after each submitted experimental trial, before the next one begins. Practice and incomplete trials do not create experimental rows.

The trial table stores the stimulus, geometry, submitted position, signed normal response, timing, movement count, and version. The press table stores ordered adjustment actions and cumulative reversal counts. Both now include `design_version = 2026-09-25_midpoint_single_v2` so future data can be distinguished from the original pilot.

Use the actual signed displacements when estimating influence. Large absolute departures from the generating contour and large perturbation effects are different observations. Family comparisons can motivate geometry-based models, but do not by themselves identify which smoothness rule a participant uses.

The next pilot should check whether the larger displacements are visible yet remain part of a coherent contour, whether practice improves use of fine controls, and whether repeated settings become stable enough for influence estimates. The program implements the experiment; it does not automatically establish these properties.

For running instructions and the CSV field guide, see `README.md`. For the magnitude source, implementation details, and verification commands, see `EXPERIMENT_DESIGN.md`.
