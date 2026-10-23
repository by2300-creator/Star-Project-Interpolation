# Experimental rationale: Why these dots, conditions, and controls?

This document explains the experiment in plain language, based on the current Python code. It separates **what the program currently does** from **what still needs testing or stronger control**. No prior knowledge of the project is assumed.

## 1. The question we want to answer

When people see scattered points that suggest a smooth path, how do they decide where the path should pass between those points?

Imagine a string of stars outlining a curve. One star is missing from its original place. A participant moves an adjustable star to the place that looks right. We then slightly move one of the other stars and ask whether the participant's chosen position changes.

This allows us to ask:

- Do the closest dots have the greatest influence?
- Can a distant dot still affect the setting?
- Does a dot's influence depend on how the surrounding shape bends?
- Do two displaced dots have effects that add together?
- If a dot is displaced much farther, does the participant stop treating it as part of the same path?

The main working idea is that **people may use one general rule for making a smooth contour, with the surrounding geometry changing how that rule responds to each dot**. The experiment collects evidence for this idea; it does not assume that the idea is already correct.

## 2. A few useful words

| Term | Plain meaning in this experiment |
|---|---|
| Stimulus | The pattern shown on one trial |
| Trial | One opportunity to adjust the movable dot and submit a response |
| Contour | The path or outline suggested by the dots |
| Interpolation | Estimating a missing position between known positions |
| Target | The position the participant is asked to adjust |
| Baseline | The original pattern before any fixed dots are deliberately displaced |
| Perturbation | A small, deliberate displacement of a fixed dot |
| Manipulation | Something the experimenter changes to test a question |
| Control | Something held constant, matched, or balanced to make comparisons easier to interpret |
| Curvature | How strongly a path bends at a location |
| Curvature variation | How the amount of bending changes along the path |
| Normal | A direction perpendicular to the estimated path at a point |
| Influence | How much the participant's setting changes when a particular fixed dot moves |
| Segmentation | Treating a dot as belonging to a different object or as outside the contour |

“Controls” below primarily means experimental controls, not keyboard buttons. The participant's keyboard controls are described separately.

## 3. What a participant actually sees and does

The display contains eight fixed white dots and one adjustable white dot in a circular dark area. There is no connecting curve, equation, coordinate grid, or visible label naming the curve family.

The participant moves the adjustable dot until it appears to belong to the smooth path suggested by the other dots. The adjustable dot travels on one line, marked by two green indicators. The participant submits a setting with Enter, Space, or Next.

The hidden original point is a reference used by the program. It is not shown as an answer to copy. The program records how far the submitted setting lies from that reference.

**Important interpretation:** the generating curve gives us a consistent reference, but its hidden point is not automatically the only perceptually reasonable completion of a sparse pattern. A systematic difference from it may be interesting behavior, rather than a simple mistake.

## 4. The overall structure

There are two separately run blocks:

| Block | Main purpose | Default size |
|---|---|---|
| Identification | Measure which fixed dots influence interpolation under small changes | 252 trials |
| Segmentation | Explore responses when a fixed dot is displaced much farther | 150 trials |

Running `run_exp.py` normally starts identification. Segmentation requires `--block segmentation`. The program does not automatically run both blocks in sequence.

These questions are separated because a small adjustment to a plausible contour may be processed differently from a large displacement that makes a dot look unrelated to it.

## 5. Manipulation 1: The underlying shape

### What changes?

Six curve families generate the original patterns:

| Family | Default equation before display transformations | Geometric role |
|---|---|---|
| Line | `y = 0` | No bending anywhere |
| Parabola | `y = 0.75 × x²` | A bowl with changing bending |
| Cubic | `y = 0.80 × x³` | An S-shape whose bending changes direction |
| Quartic | `y = 0.90 × x⁴` | A bowl with a very flat middle and more bending farther away |
| Quintic | `y = x⁵` | An S-shape with an especially flat middle |
| Circle | A semicircle | Constant curvature along the underlying curve |

The polynomial domain initially runs from −1 to +1. The straight line is equivalent in shape to a rotated `y = x`. After generation, the curves are sampled, normalized, optionally reflected, and rotated.

### Why change the shape?

A straight row, a circle, and an S-shaped pattern provide different geometric surroundings. If a particular dot has different influence in these surroundings, a single fixed influence pattern may be insufficient to explain behavior.

The curve names are convenient ways to generate shapes. The intended explanation concerns bending, spacing, and distance, rather than the idea that people identify an equation and apply a separate rule to it.

### What this comparison does not isolate

Changing family changes several geometric properties at once. The current circle and polynomial patterns are not deliberately matched to have the same target curvature and spacing. A family difference alone therefore cannot establish that curvature variation, specifically, caused the response difference.

Likewise, these are individual polynomial-generated contours, not fitted cubic or quintic splines. Showing an `x⁵` curve does not demonstrate that an observer uses a quintic spline rule.

## 6. Manipulation 2: Target 3 versus target 4

### What changes?

There are nine sampled positions, numbered **0 through 8**. The target number identifies which original position is replaced by the adjustable dot.

| Condition | Position in ordinary counting | Distance along the original curve | Remaining fixed dots |
|---|---|---|---|
| Target 3 | Fourth point | 35% of the way along | Points 0, 1, 2, 4, 5, 6, 7, 8 |
| Target 4 | Fifth point | 50% of the way along | Points 0, 1, 2, 3, 5, 6, 7, 8 |

Only one target is adjustable on a trial. The percentages describe distance along the original curve, not a percentage of screen width. Reflection and rotation can change where these points appear on screen without changing their indices.

### Why include the midpoint?

At the center of the underlying line, cubic, quartic, and quintic curves, analytic curvature is zero. Their surroundings still differ: the line stays straight, while the polynomial curves bend away from the center in different ways.

This gives a useful comparison: **can surrounding shape matter even when bending at the hidden point itself is the same?**

The curvature estimated from three sampled dots can differ from the exact curvature of the generating equation. These should not be treated as interchangeable measurements.

### Why include an off-center target?

The midpoint is a special location. It may provide symmetry and, for several families, zero curvature. Target 3 checks interpolation in a different neighborhood, with an unequal number of fixed dots on either side and potentially different local bending.

It asks whether findings at the midpoint also appear away from that special location.

### What is not perfectly controlled?

Target location changes several things together: local geometry, distance to endpoints, and the distribution of surrounding dots. In the current generator, target 3 and target 4 also receive separately assigned rotations and opposite reflection states within a family at the standard level.

Consequently, a raw target-3 versus target-4 difference is not a pure isolated effect of target location. A stricter comparison would show the same baseline orientation/reflection at both target locations and balance those display versions separately. That extension is not currently implemented.

## 7. Manipulation 3: Which fixed dot is displaced?

### What changes?

In identification, each of the eight fixed dots is displaced in its own trials. The adjustable target is never also selected as a perturbed fixed dot.

### Why test every fixed dot?

This measures the reach of the interpolation process. A response might depend mostly on immediate neighbors, on several nearby dots, or on points much farther away.

Testing only the closest dot would miss possible long-distance influences. Testing all fixed positions produces a map of how influence changes with position along the contour.

### How should distance be interpreted?

A point index is a position label, not a physical distance. The spacing is uneven, and different curves can have different lengths. The data therefore include coordinate and distance measures so researchers can compare influence with actual geometric distance, rather than index difference alone.

The recorded arc-distance estimate uses the lengths of straight segments connecting sampled points. It approximates distance along a smooth curve.

## 8. Manipulation 4: Opposite displacement directions

### What changes?

Each single-dot displacement is tested in both directions along that dot's baseline normal: one positive and one negative.

Positive is a consistent mathematical direction along the local normal, not always upward on the screen. On a bent path, different dots' normals can point in different directions.

### Why use both signs?

A person might place the target away from its original position even when no fixed dot moves. Using opposite shifts helps distinguish this general tendency from sensitivity to the displaced dot.

For illustration, suppose a fixed dot shifts by +2 internal units and the average target response is +1 unit. A −2-unit shift produces an average response of −1 unit. The response changes by 2 units while the manipulated dot changes by 4 units, giving an estimated influence of 0.5.

The comparison is:

```text
influence = change in average response / change in fixed-dot position
```

This is an example, not a result from participant data. Actual displacement values must be used because the same spacing fraction can correspond to different distances across points and shapes.

An influence can be positive, close to zero, or negative. It is not a percentage of attention, and influences need not add up to one.

### The critical control: matched baselines

The positive and negative trials for the same dot use the same original coordinates, target, strength, sampling, reflection, rotation, and scale. They also have the same requested starting side within a repetition.

Otherwise, a response difference could come from a changed shape or starting position rather than the direction of the displacement.

## 9. Manipulation 5: Displacement size

### Default identification size

The small shift is **4% of the displaced dot's local baseline spacing**. Local spacing is the average of the adjacent straight-line point distances; an endpoint uses its one adjacent distance.

If that spacing corresponds to 50 screen pixels, the shift is 2 pixels. The program uses a proportion so the perturbation is scaled to the neighborhood rather than using an identical pixel displacement everywhere.

### Why small shifts?

The intention is to probe the response close to the original shape. In that neighborhood, a simple influence estimate may summarize how the setting changes.

However, **4% is a pilot setting, not a proven boundary of a linear response regime**. The default block uses only one nonzero small magnitude. It cannot establish that doubling the shift doubles the response. That proportionality question requires additional small magnitudes.

### Optional segmentation sizes

The larger-shift block uses 8%, 16%, 32%, and 64% of local spacing, in both directions.

For target 4 it perturbs points 3 and 5, the immediate neighbors, and point 0, the selected distant endpoint. The code chooses the farthest index; where the two endpoints tie, it selects the first one. It does not test both distant endpoints in this default block.

Larger shifts may reveal a change in how a dot contributes to interpolation. A weakening influence is compatible with exclusion from the contour, but it is not by itself proof of exclusion. Other nonlinear response rules could produce similar changes.

There is no direct “does this dot belong?” response. Membership probabilities and a segmentation threshold would have to be inferred using an explicitly specified model and sufficient repeated data.

## 10. Manipulation 6: One displaced dot versus two

### What changes?

Identification includes four conditions where both immediate neighbors of the target are displaced:

| Pattern | First neighbor | Second neighbor |
|---|---|---|
| 1 | Negative | Negative |
| 2 | Negative | Positive |
| 3 | Positive | Negative |
| 4 | Positive | Positive |

Both shifts are calculated from the same original pattern. One displacement does not redefine the normal or spacing used for the other.

### Why include these trials?

They ask whether effects approximately add together. Suppose shifting one neighbor changes the response by +1 unit and shifting the other changes it by +2 units. A simple additive prediction is approximately +3 units when both shifts occur together, after accounting for the baseline setting.

This is often called **superposition**. A mismatch could suggest interaction between dots or a response rule that changes with the combined geometry.

### What needs caution?

The current starting-side assignment balances the four paired patterns overall, but does not make every paired trial and both corresponding single-dot trials share the same starting side. The unperturbed baseline also has only one starting side per repetition.

Therefore, starting-position effects can contaminate a direct comparison of paired and single responses. Additional repetitions reverse starting side; analysis should account for starting side, and a stronger design would fully balance it within the comparisons of interest. The presence of paired trials alone does not establish additivity.

## 11. Control condition: No fixed dots are displaced

Each original pattern has an unperturbed baseline trial.

This measures where the participant places the target when all eight fixed dots remain on the original curve. It supplies a reference for asking whether displacements alter the setting.

For example, if someone normally places the target 3 pixels toward Z, a perturbed response of 4 pixels is a change of about 1 pixel from that tendency, not necessarily a 4-pixel perturbation effect.

One baseline trial per pattern is a noisy estimate of an individual's tendency. Repetition is needed for stable estimates. “Baseline trial” also does not mean a blank screen or a participant-free comparison: the participant still makes the same adjustment.

## 12. Controls in stimulus construction

### A. Same number and appearance of dots

All current experimental trials use eight fixed dots plus one adjustable dot. The dots are isotropic: they have no arrows or oriented bars telling the observer which way the contour points. Dot radius is 2 pixels, and the task uses white dots on a dark display.

This keeps point count and explicit orientation cues consistent. Older project data may have eight total points instead of nine; those are a different stimulus design.

### B. Same sampling fractions

The default curve positions are:

```text
0%, 11%, 23%, 35%, 50%, 65%, 77%, 89%, 100%
```

These fractions are shared across families and kept fixed within matched comparisons. Spacing does not change randomly between positive and negative conditions.

This is a **relative sampling control**. It does not make every gap equally long, or make absolute gap lengths identical across families. Longer and more curved paths can still have different spacing after endpoint normalization.

### C. Shape-preserving normalization

The program translates, rotates, and uniformly scales each original curve so its endpoints occupy a common internal frame. Uniform scaling enlarges both coordinate directions together rather than stretching the shape in only one direction.

This controls endpoint separation in internal units. It does not independently match total path length, enclosed area, curvature, or all screen-pixel distances across families.

### D. One display scale per matched comparison

The display scale is based on the original baseline and the largest planned displacement fraction for the block. Space is reserved so displaced dots remain inside the display.

A positive or negative perturbation therefore cannot shrink or enlarge its own entire stimulus. This prevents an unwanted size change from accompanying the manipulated dot movement.

Different baselines or blocks can still receive different scales. In particular, the large-displacement block reserves more room. Use recorded scale and displacement values when comparing across blocks.

### E. Normals are based on the original pattern

Displacement directions and the target's movement line are anchored to the baseline geometry. Moving a fixed dot does not rotate the target's adjustment line on that trial.

This helps keep the response dimension constant across matched conditions. These directions are estimated from sampled neighboring points; they are approximations to the underlying curve's exact perpendiculars.

## 13. Controls against orientation and starting-position effects

### Rotation

Each baseline is assigned a rotation between −22.5° and +22.5°. All matched conditions retain that rotation. This provides orientation variation without changing orientation inside a sign comparison.

It does not establish rotation invariance. The default does not show each identical baseline at several independently crossed rotations. A direct orientation experiment would require that additional comparison.

### Reflection

Baseline contours can be reflected, reversing the direction in which they bend. Reflection is assigned by the design and held fixed within a baseline; it is not newly randomized on each presentation.

This introduces multiple display configurations. It is not a full independent reflection manipulation, since reflection is linked to family and target in the current assignment.

### Starting side

The target starts approximately +70 or −70 pixels from its reference position along the response line. Both starting sides occur equally often in the full default identification block: 126 trials each.

This reduces an overall imbalance in the direction from which participants approach a setting. Each positive/negative single-dot pair starts from the same side, helping protect that comparison.

Overall balance does not remove every anchoring effect. A starting position can affect a final judgment, and some starts are shortened near the movement boundary. Both requested and actual starting offsets are saved. Repeated conditions reverse the requested starting side; the default of one repetition does not show both sides for every condition.

## 14. Controls in the response procedure

### One-dimensional movement

The participant can move only along the target's baseline normal. This produces one signed response value that can be compared across trials, rather than a free two-dimensional placement.

The tradeoff is that the task measures interpolation under that constraint. It does not measure which two-dimensional position a participant would freely choose. The green markers also provide information about the allowed axis; they are part of the task, not a cue-free display.

### Same controls and step-size rule

Z/Up moves toward the Z marker, and / or Down moves toward the / marker. Keys 1, 2, and 3 select 1-, 5-, and 10-pixel steps. Reversals reduce movement size for finer adjustment. The same rule applies across conditions.

This standardizes the motor task, but pixel resolution and adjustment strategy can still affect measured responses. The 1-pixel step is relevant when experimental shifts themselves span only a few pixels.

### Practice and feedback

Participants receive an instruction screen and one unrecorded line practice trial using the same movement mechanism. This provides an opportunity to understand the controls before experimental collection.

The program does not currently enforce a practice accuracy criterion or ensure that a participant tried every control. Submission feedback confirms progression; it does not reveal the hidden original point or score perceptual accuracy.

### Timing

The target setting, elapsed trial time, movement count, and adjustment sequence are recorded. There is no imposed response deadline in the current trial loop.

Reaction time includes deliberation and adjustment. It is not a pure measure of how quickly someone first perceived the curve. Individual keypress timestamps are not recorded.

## 15. Trial-order and session controls

Trials are shuffled so families and displacement conditions are not presented as a simple predictable sequence. A recorded seed makes the order reproducible.

The default seed is 63. Repeating the default settings repeats the order and assigned baseline rotations; changing only the participant label does not generate a new order. Shuffling reduces fixed grouping of conditions but does not, by itself, balance all learning, fatigue, or carryover effects across participants.

The default identification count is:

```text
6 families × 2 target locations = 12 baselines
1 unperturbed + 16 single-dot + 4 paired-dot trials = 21 trials per baseline
12 × 21 = 252 trials
```

The optional default segmentation count is:

```text
6 families × 1 target location = 6 baselines
1 unperturbed + (3 fixed-dot locations × 4 sizes × 2 signs) = 25 per baseline
6 × 25 = 150 trials
```

Optional partition settings split the default identification design into two 126-trial sessions while keeping each baseline's matched conditions together. This is a session-management option, not an automatic break schedule. Individual partitions should not be assumed to retain every balance of the full design. If the same participant completes both partitions, their ordering should be planned deliberately.

## 16. What is measured, and why are there two CSVs?

### Trial table: the stimulus and final response

The file ending in `_trials.csv` contains one row per submitted trial. It records:

- Participant/session labels and trial identity.
- The family, target, displacement condition, orientation, and starting position.
- Original and displaced point coordinates.
- The submitted target position and its signed distance from the original hidden point.
- Timing, movement count, scale, and geometric measurements.

The main measure is `response_normal_px` or its internal-unit version, `response_normal_units`. Positive means toward the Z marker; negative means toward the / marker. “Positive” is not always upward on screen and does not mean better performance.

This table supports the main question: how do the stimulus changes relate to final settings?

### Press table: the adjustment sequence

The file ending in `_presses.csv` also has one row per submitted trial. It stores adjustment actions in order, such as `up_0`, `down_1`, and `step_small_1`. The suffix is the cumulative reversal count, not a timestamp or movement distance.

This helps researchers examine how settings were reached and whether patterns of adjustment differ across conditions. It is not a continuous movement recording.

### Why save after every trial?

Both CSVs are created before the welcome screen and updated before the next experimental trial starts. This preserves completed trials if the session is stopped early. An unfinished trial and practice are not saved as experimental responses.

Rows should match across the files by trial identity within the run. The two files are saved separately, so a disk/process failure between saves can leave unequal row counts. Check them before analysis. Across runs, preserve participant, session, and run filename information because trial labels can repeat.

See `README.md` for the fuller column guide.

## 17. What the present design can reasonably investigate

With enough repeated observations and appropriate analysis, the current task can investigate:

1. **Directional sensitivity:** whether opposite movements of a fixed dot produce different target settings.
2. **Spatial reach:** whether that sensitivity varies with the dot's distance from the target.
3. **Geometry dependence:** whether influence patterns differ across contours and relate to measured geometric features.
4. **Approximate additivity:** whether selected paired displacements behave like the sum of corresponding single-dot effects, accounting for baseline and starting side.
5. **Responses to larger disruptions:** whether response patterns change across larger displacement sizes.

The software records the ingredients for these analyses. It does not automatically fit models, establish statistical significance, estimate sample-size needs, or demonstrate a particular perceptual mechanism.

## 18. What remains outside the current controls

The following distinctions matter when describing conclusions:

| Desired conclusion | Why the current design alone is insufficient |
|---|---|
| Curvature variation specifically causes an effect | Family changes alter several geometric properties; explicit curvature-matched contrasts are absent |
| People use a rotation-invariant rule | The same geometry is not systematically tested across several crossed orientations |
| Response is proportional to small displacement | Identification has only one nonzero small magnitude |
| Intermediate influence means partial membership | A mean can also combine trials with different response strategies; repeated response distributions are needed |
| A dot is definitely excluded from the contour | No direct membership judgment is collected; nonlinear interpolation could explain a reduced effect |
| Humans use a particular spline or smoothness objective | Candidate observer models have not been fitted and compared on held-out responses |
| Target location alone caused a difference | Target changes geometry and neighbor arrangement and is linked to reflection/rotation assignments |
| Starting-position bias has been eliminated | Overall balance is not complete within-condition balance, and boundary clipping is possible |

These are limits of interpretation, not reasons that the pilot cannot be useful. The pilot can identify reliable effects, practical task problems, useful displacement sizes, and the additional controls required for a focused follow-up.

## 19. Conditions to standardize during data collection

These are procedural controls for the experimenter; the program does not enforce them:

- **Viewing distance and monitor setup:** the same pixel pattern can subtend a different visual size on another monitor or at another distance.
- **Display scaling, brightness, and room lighting:** these affect how visible small dots and small displacements are.
- **Instructions and practice:** use the same explanation and verify understanding consistently.
- **Breaks and session length:** plan them consistently to manage fatigue; the default trial loop does not schedule them.
- **Vision and correction:** define relevant participant requirements and record them consistently.
- **Order and repeat policy:** plan seeds, partitions, block order, and repetition counts in advance.
- **Analysis rules:** decide how to handle incomplete sessions, unusually fast submissions, boundary settings, and inconsistent data before interpreting effects.

The current display uses an 800 × 800 pixel window by default. That is a software size, not a calibrated physical or visual-angle size.

## 20. The rationale in one paragraph

We show a sparse contour with one adjustable point, deliberately move selected fixed dots, and measure how the participant's setting changes. Matched positive and negative shifts make each dot's influence easier to identify. Multiple point locations reveal the spatial extent of that influence; multiple shapes and target locations reveal whether it depends on surrounding geometry. Baseline and paired trials provide references for bias and additivity, while a separate larger-shift block explores changes beyond small perturbations. Fixed presentation and response rules make comparisons more interpretable, but the current pilot still requires stronger geometric matching, within-condition balancing, repetitions, and model comparisons before it can establish a specific theory of human interpolation.
