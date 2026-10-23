# New participant: interpretation of the 20:12 session

## Main conclusion

The recording is complete and internally consistent. The responses contain shape-dependent patterns, particularly a persistent quartic offset and a large direction effect for the parabola. However, coarse adjustment behavior and three questionable baseline observations limit the conclusions. This is one participant with one response per condition, so the findings describe this session rather than establish a population effect or a reliable interpolation model.

## Data and checks

Sources: `data/pilot_identification_s1_20260925_201233_021660_trials.csv` and its matching `_presses.csv`, using design `2026-09-25_midpoint_single_v2`.

- Both files contain 108 matching, unique trials: 96 single-dot perturbations and 12 baselines. Each shape has 16 midpoint perturbation trials, one midpoint baseline and one off-center baseline.
- The condition sequence matches the current default design. Regenerating all displayed mathematical coordinates agrees to approximately 7 × 10^-15 units.
- Replaying all recorded movement and step-selection actions reconstructs every final screen position to within approximately 4 × 10^-13 pixels. Recomputing the signed response from screen coordinates also agrees. There is no detected discrepancy between the two CSVs and the recorded final positions.
- Median completion time is 2.34 seconds per trial. Summed trial times are 4.53 minutes; this excludes practice, instructions, and between-trial delays.
- The CSV participant identifier is still `pilot`, session `s1`. Treat the filename timestamp as the distinguishing session identifier; these labels alone do not distinguish this new participant from the previous pilot.
- Practice is not recorded, so these files cannot establish whether practice improved performance.

## What a response means

Zero is the hidden point on the original, unperturbed curve. Positive values mean the participant placed the adjustable dot toward the Z marker; negative values mean toward the slash marker. These signs refer to the curve's response axis, not always screen up/down. Distances are pixels.

A nonzero response in a perturbed trial is not automatically an error: changing a visible dot can legitimately change the participant's preferred completion. Absolute distance measures departure from the original reference, not accuracy relative to a uniquely correct perturbed contour.

Perturbations have one nonzero magnitude: 13.33% of each dot's local spacing, or 8.80–16.83 pixels depending on shape and dot. There is no independent dose–response series in this session. Comparing different pixel magnitudes would also compare different geometries and dot locations.

## Responses by shape and direction

These summaries use only the 16 perturbed midpoint trials per shape. Each direction mean averages eight different perturbed dots, with one observation per dot. The last column subtracts the negative-direction mean from the positive-direction mean.

| Shape | Mean signed response (px) | Mean absolute departure (px) | Negative perturbation mean (px) | Positive perturbation mean (px) | Difference (px) |
|---|---:|---:|---:|---:|---:|
| Line | 2.50 | 3.13 | 1.88 | 3.13 | 1.25 |
| Parabola | 14.69 | 15.94 | 24.38 | 5.00 | -19.38 |
| Cubic | -0.31 | 7.19 | -1.25 | 0.63 | 1.88 |
| Quartic | 33.13 | 33.13 | 31.88 | 34.38 | 2.50 |
| Quintic | -6.88 | 8.75 | -8.13 | -5.63 | 2.50 |
| Circle | 0.25 | 11.50 | -4.50 | 5.00 | 9.50 |

### Quartic: a persistent displacement

All 16 perturbed midpoint responses are positive, ranging from +10 to +45 pixels. Their mean is +33.13 pixels, while the two perturbation-direction means differ by only 2.50 pixels. Thus, the most prominent pattern is a common offset across perturbation conditions, rather than a uniform response to perturbation sign.

This could reflect a preferred completion that differs from the generating quartic, or a task/control strategy. The midpoint baseline was submitted without movement, so a reliable baseline estimate is unavailable. It would be premature to call this a confirmed baseline perceptual bias or evidence for a particular curvature rule.

### Parabola: the largest direction contrast

The negative perturbations yield a mean response of +24.38 pixels, versus +5.00 for positive perturbations. Seven of the eight matched dot pairs show a negative positive-minus-negative contrast. The midpoint baseline is +20 pixels, so the participant also shows an offset without perturbation on that one baseline trial.

The pattern is not explained by starting-side imbalance within the matched pairs: each dot's positive and negative trials have the same initial side, rotation and baseline geometry. Nevertheless, one observation per sign cannot separate a stable influence pattern from order effects and response variability. Perturbations use each visible dot's local normal while responses use the target's normal; negative contrasts should not automatically be called visual repulsion.

### Circle: local influence is plausible

The overall signed mean is close to zero, but the mean absolute departure is 11.50 pixels. Positive and negative responses cancel in the signed average. Opposite perturbations of the immediate neighbors (dots 3 and 5) produce response differences of +40 and +20 pixels. This is compatible with local visible points influencing the interpolated location, although dot 6 has a -20-pixel contrast and the estimates need repetition.

### Line: relatively small departures in perturbed trials

The mean absolute departure is 3.13 pixels. Immediate-neighbor perturbations each produce a +10-pixel contrast. Several distant-dot pairs produce zero contrast. This is compatible with stronger local influence, but the -20-pixel contrast at dot 1 and unusable line baselines show why a smooth, reliable influence function cannot yet be inferred.

### Cubic and quintic: cancellation hides individual effects

The cubic signed mean is nearly zero, while individual responses range from -20 to +10 pixels. Quintic responses have a modest negative mean (-6.88 pixels). Both have positive and negative dot-specific contrasts that largely cancel when averaged. Similar overall means or plots would not demonstrate that participants perceive the two families as equivalent.

## Dot-specific influence

For each shape and visible dot, compute the response to positive perturbation minus the response to negative perturbation. This avoids subtracting an unreliable baseline. The two conditions are matched on initial side, rotation, reversal and scale. Dot indices are zero-based; the adjustable target is dot 4, so dots 3 and 5 are its immediate neighbors.

| Shape | Dot 0 | Dot 1 | Dot 2 | Dot 3 | Dot 5 | Dot 6 | Dot 7 | Dot 8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Line | 0 | -20 | 5 | 10 | 10 | 5 | 0 | 0 |
| Parabola | -10 | -40 | -30 | 10 | -30 | -20 | -20 | -15 |
| Cubic | 10 | -10 | 20 | 10 | 20 | -20 | -20 | 5 |
| Quartic | 0 | 0 | -5 | 30 | 15 | -15 | -10 | 5 |
| Quintic | 10 | -10 | 20 | 0 | 20 | -10 | 0 | -10 |
| Circle | 8 | 10 | 0 | 40 | 20 | -20 | 8 | 10 |

Values are response differences in pixels. Across all 48 pairs, 22 are positive, 18 negative and eight effectively zero. Of the 12 immediate-neighbor pairs, ten are positive, one zero and one negative. This is a useful descriptive hint of local influence, not an independent-subject statistical test.

`matched_influences.csv` also reports a normalized finite-difference estimate: `(positive response − negative response) / (2 × perturbation magnitude)`. A value of 0.5 means a two-direction stimulus separation of 20 pixels corresponds to a response separation of 10 pixels. With just one magnitude and no repeated settings, these are exploratory estimates, not established derivatives or evidence of linearity.

## Baselines and response quality

| Shape | Midpoint baseline (px) | Off-center baseline (px) |
|---|---:|---:|
| Line | +70: no movement | +100: moved farther from reference |
| Parabola | +20 | 0 |
| Cubic | 0 | -10 |
| Quartic | -70: no movement | +40 |
| Quintic | +5 | +15 |
| Circle | 0 | +10 |

Three trials require particular attention:

- Trial 16, line midpoint: zero moves, +70 pixels, 550 ms. This is the starting position.
- Trial 17, quartic midpoint: zero moves, -70 pixels, 13 ms. This is also the starting position. Accidental or carried-over submission is plausible; the files do not establish the cause.
- Trial 85, line off-center: three `up` movements take the dot from +70 to +100 pixels, farther from the reference. This merits checking task understanding or an accidental response, but it is not a demonstrated recording error.

All raw trials are retained. The main shape/direction analysis uses all 96 perturbed trials and therefore does not depend on excluding these baselines. Baseline-subtracting the line and quartic midpoint data would introduce artificial shifts of -70 and +70 pixels respectively. Do not use those baseline corrections.

Each off-center condition has only one observation and a different orientation/reversal setup from its midpoint counterpart. These data do not isolate an off-center effect or provide an off-center perturbation influence function.

## Adjustment behavior and interpretation limits

- There are 906 recorded movement events: 810 at 10-pixel steps and 96 at 5-pixel steps. No 1-pixel movements occur.
- Fourteen trials contain manual step selections, all selecting the large step (15 selections total).
- Ninety of 108 trials have no direction reversals. Ninety-four endpoints (87.0%) lie on multiples of 10 pixels.
- Endpoints at +2 and +12 pixels do not demonstrate fine adjustment: the complete replay reproduces them without 1-pixel steps, because movement can be clamped at a marker before returning.

The enlarged perturbations can produce visible response contrasts, but coarse response steps remain a measurement bottleneck. A 10-pixel response difference may represent only one extra movement. A zero contrast can reflect rounding rather than no perceptual influence. A near-zero mean across trials can also conceal large positive and negative responses.

This session alone cannot show that increasing perturbation magnitude improved measurement: the previous session used a different participant and design. It cannot establish a cubic-versus-quintic model preference, linearity across magnitudes, or population-level significance. No participant-level significance tests or confidence intervals are reported.

## Practical next steps

1. Before further main data collection, investigate rapid consecutive submissions and consider requiring a fresh confirmation action for each trial. The 13-ms baseline makes this a concrete issue to check.
2. Verify during practice that the participant can deliberately use 1-pixel movements and identify which direction moves toward their intended placement. This session's practice outcomes are unavailable.
3. Repeat baselines and each positive/negative condition across blocks, counterbalancing starting side across repeats. Repetition is needed to separate consistent influence from trial noise and to estimate repeatability.
4. Assign unique participant identifiers. Keep this session as a pilot with its quality flags documented.
5. Investigate the quartic offset and parabola direction pattern in additional participants before changing the curve geometry or perturbation magnitude again.

The current experiment code and source recordings were not changed during this analysis.
