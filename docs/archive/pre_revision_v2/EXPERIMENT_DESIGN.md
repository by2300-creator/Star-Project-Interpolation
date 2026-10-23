# Geometry-Conditioned Human Contour Interpolation

## Purpose and working hypothesis

The six curve families are stimulus generators, not candidate psychological variables. The experiment tests whether a local interpolation operator changes with the geometry around a missing sample and whether the same geometry predicts the later transition from interpolation to segmentation.

The working hypotheses are:

1. **Small-perturbation linearity.** For sufficiently small displacements, participant response is approximately a local linear function of the visible-point displacements. The signed influence of visible point $i$ is a Jacobian element,

   \[
   J_i(g) = \frac{\partial r}{\partial \delta_i},
   \]

   where $g$ is the baseline geometry and $r$ is the participant's signed setting along the target normal. $J_i$ may be positive, zero, or negative; it is not a normalized attention weight.

2. **Geometry-conditioned operator.** The signed influence field is not invariant across baseline contours. Local normalized curvature, curvature variation/inconsistency, turning-angle structure, relative arc distance, and spacing should predict how $J_i(g)$ changes across line, polynomial, and circular contours.

3. **Function-independent generalization.** Once local geometry is known, the generating label (line, parabola, cubic, quartic, quintic, or semicircle) should add little held-out predictive value. A model trained without one curve family should predict that family's human influence field without being told its equation.

4. **Geometry-conditioned segmentation.** At larger displacements, the local linear interpolation regime should give way to probabilistic inclusion/exclusion of the displaced point. The 50% inclusion threshold, Δ₅₀, should depend on geometric disruption rather than on physical displacement alone.

5. **Mixture versus graded response.** Intermediate mean influence may reflect either continuously graded membership or a mixture of included and excluded trials. The full response distribution and its variance, not only the condition mean, will distinguish these accounts.

This framing incorporates the main correction from the shared conversation: “curvature inconsistency causes downweighting” is too close to the earlier graded-membership proposal. The intended contribution is instead that **local geometry changes the signed Jacobian itself** and predicts the probabilistic boundary at which that Jacobian no longer applies. This remains a working novelty claim and should be checked with a formal citation-chain/database review before preregistration or publication.

## What is manipulated

| Factor | Implemented levels | Role |
|---|---|---|
| Experimental block | identification; segmentation | Separates local linear interpolation from nonlinear membership/segmentation |
| Curve family | line, $x^2$, $x^3$, $x^4$, $x^5$, semicircle | Spans different local geometry; not treated as the primary psychological explanation |
| Target location | index 3 (off-center), index 4 (arc midpoint) in identification | Estimates more than one row of the local operator and separates target curvature from surrounding geometry |
| Perturbed-point location | every visible point in identification; three diagnostic distances in segmentation | Estimates the signed influence field and its spatial extent |
| Perturbation sign | − and + along the point's baseline contour normal | Enables a symmetric-difference estimate of signed influence |
| Perturbation magnitude | 0 and 0.04 local spacings in identification; 0, 0.08, 0.16, 0.32, and 0.64 local spacings in segmentation | Probes the linear regime and the transition to segmentation |
| Perturbation pattern | single point; selected two-point patterns | Identifies $J_i$ and tests superposition |
| Reflection | reflected or unreflected, fixed within a matched baseline | Removes dependence on one curvature polarity/display configuration |
| Display rotation | continuous −22.5° to +22.5°, fixed within a matched baseline | Reduces orientation-specific strategies |
| Curve strength | standard by default; optional low/high for polynomial families | Allows later separation of local geometry from polynomial degree without duplicating line/circle stimuli |
| Starting side | ±70 px along the target normal | Measures and controls motor/anchoring bias |

The code assumes **nine total dots: eight visible anchors and one adjustable/hidden sample**, matching the latest “设计插值假设” discussion. Older data used eight total; do not pool them silently.

## What is controlled

1. **Matched baselines.** Every baseline, negative, positive, and paired perturbation associated with one `stimulus_id` uses exactly the same unperturbed coordinates, target, reflection, rotation, strength, and spacing profile. The previous program regenerated a different random curve for each sign, which made the symmetric comparison uninterpretable.

2. **Sampling.** Samples are selected at fixed normalized arc-length fractions shared by every curve family:

   `0.00, 0.11, 0.23, 0.35, 0.50, 0.65, 0.77, 0.89, 1.00`.

   Index 4 is the exact arc midpoint. This preserves the diagnostic contrast in which the analytic target curvature of the line, cubic, quartic, and quintic is zero while their surrounding curvature fields differ. Index 3 supplies an off-center target. An equal-arc profile and a seeded jittered-arc profile are also available for later control/generalization studies.

3. **Retinal extent.** Each baseline receives only a similarity transform: translation, rotation, and uniform scaling. Its endpoint chord is standardized. Display scale is computed from the unperturbed baseline and reused after perturbation, so a displaced point cannot resize its own trial.

4. **Perturbation direction and units.** A point moves along its baseline contour normal, not vertically in screen coordinates. Magnitude is a fraction of that point's local spacing, not an arbitrary number of pixels. The actual local-unit and pixel displacements are recorded.

5. **Response dimension.** The adjustable dot is constrained to the contour normal through the true hidden sample. The primary dependent variable is the signed projection onto that normal. This removes a second motor degree of freedom and makes signs comparable across rotations and families.

6. **Correct answer.** The correct location is the actual unperturbed hidden sample for every family. The previous implementation used the aperture center for every non-circle curve, which was generally not on the hidden curve point.

7. **Starting position.** Positive and negative trials in the same symmetric pair start from the same side. Starting side is balanced across the complete design and reverses across repeated conditions.

8. **Presentation.** Curve equations, axes, and family names are not shown. Conditions are randomized. A fixed baseline can be divided across complementary sessions without breaking its matched sign/pair structure.

9. **Recorded nuisance variables.** Rotation, reflection, starting side, display scale, reaction time, movement count, reversal count, baseline coordinates, displayed coordinates, and button sequences are retained for quality control and sensitivity analyses.

The following must still be controlled procedurally: viewing distance, monitor calibration, visual angle, dot luminance/contrast, ambient lighting, fixation/eccentricity, and participant inclusion/exclusion rules. Pixel values should be converted to visual angle before confirmatory collection.

## Experimental blocks and default trial counts

### A. Identification block

For each of 6 curve families × 2 target locations, the default block contains:

- 1 unperturbed baseline;
- 8 visible points × 2 signs = 16 single-point trials at 0.04 local spacings;
- 4 two-point sign patterns on the nearest points bracketing the target.

This is 21 trials per matched baseline and 252 trials in the complete block. The command-line session partition divides it into two complementary, balanced 126-trial sessions while keeping each matched baseline intact. A participant can complete both sessions, or partitions can be counterbalanced across participants.

The 0.04 level is a **pilot value**, not an established threshold. It must be accepted as “small” only if the paired trials support superposition within a preregistered equivalence margin.

### B. Segmentation block

The interactive program defaults to target index 4 and contains, for every family:

- 1 unperturbed baseline;
- 3 diagnostic visible-point locations;
- 4 nonzero magnitudes × 2 signs at each point.

This gives 25 trials per family and 150 trials. Supplying `--targets 3,4` produces the full 300-trial map. Repetitions should be increased, or concentrated near pilot-estimated transition magnitudes, when the goal is to distinguish mixture from graded membership. The current default is suitable for locating that transition, not for a definitive distributional test.

The segmentation block is intentionally separate from identification. Large perturbations must not be used to estimate the small-signal Jacobian.

## Primary measures saved for analysis

- signed and absolute response along the target normal, in pixels and local units;
- reaction time, move count, reversals, starting side, and complete press sequence;
- exact baseline and displayed coordinates for all nine samples;
- signed Menger curvature, dimensionless curvature $K_i = \kappa_i s_i$, turning angle, local spacing, and signed arc distance for every point;
- analytic target curvature for the generating curve and discrete curvature available from visible samples;
- baseline local curvature mean, magnitude, variance, inconsistency, turning variance, and spacing variation;
- perturbation-induced RMS/max curvature disruption, turning disruption, and change in local curvature variance/inconsistency;
- exact perturbation indices, signs, magnitudes, condition type, regime, target, family, rotation, reflection, and seeds.

## Planned analyses after data collection

### 1. Quality control and baseline bias

- Plot responses, reaction times, moves, and reversals by participant and trial order.
- Estimate each participant's baseline bias $b_g = E[r\mid\delta=0,g]$.
- Test starting-side, rotation, reflection, practice/order, and display-scale effects. Keep them as nuisance terms if meaningful.
- Apply preregistered lapse, response-time, and incomplete-trial criteria without filtering on the direction of the response error.

### 2. Estimate the signed influence field

For point $i$ in baseline geometry $g$, estimate

\[
\hat J_i(g) = \frac{\bar r(+\Delta_i,g)-\bar r(-\Delta_i,g)}{2\Delta_i},
\]

using the recorded actual displacement in local units. Estimate uncertainty hierarchically across trials and participants rather than treating participant means as independent raw observations.

First visualize $\hat J$ as a function of signed arc distance. Negative values must be retained. Do not constrain influences to be positive or to sum to one.

### 3. Test local linearity and superposition

For a paired perturbation of points $i$ and $j$, compare the observed baseline-adjusted response with the sum of the two matched single responses:

\[
S_{ij} = [r_{ij}-b_g]-[r_i-b_g]-[r_j-b_g].
\]

Use an equivalence test or a hierarchical model with a preregistered smallest effect of interest. A nonsignificant ordinary null-hypothesis test is not evidence that the linear approximation is adequate.

### 4. Test the geometry-conditioned operator hypothesis

Fit a hierarchical model for trial response or for $\hat J$ with predictors such as:

- signed/absolute arc distance from target;
- target and pointwise dimensionless curvature;
- local curvature variance and inconsistency;
- perturbation-induced curvature and turning disruption;
- local spacing and turning angle;
- interactions of distance with curvature-field statistics;
- participant random intercepts and slopes, plus stimulus-level effects.

Compare a fixed influence field against a geometry-conditioned field. The confirmatory test is held-out predictive performance, not only coefficient significance.

### 5. Compare computational models

At minimum compare:

1. global polynomial regression;
2. quadratic $C^1$, cubic $C^2$, and quartic $C^3$ spline benchmarks;
3. minimum turning-angle-variance interpolation;
4. a fixed local signed kernel;
5. the proposed geometry-conditioned signed Jacobian;
6. for large perturbations, the geometry-conditioned Jacobian plus a segmentation gate.

Use participant-held-out and trial-held-out prediction. The strongest generalization test is leave-one-curve-family-out cross-validation: train on five families and predict the complete influence field of the sixth without refitting family-specific parameters. Report predictive log density/error with uncertainty and inspect calibration, not just in-sample $R^2$.

### 6. Model the interpolation-to-segmentation transition

Fit a hierarchical inclusion model such as

\[
p(z=1)=\operatorname{logit}^{-1}(\alpha + \beta_1|\Delta| + \beta_2G + \beta_3d + \ldots),
\]

where $G$ is measured geometric disruption and $d$ is point distance. A trial-level mixture can then use an excluded component centered near baseline and an included component centered near $b_g + J_i(g)\Delta_i$.

Estimate Δ₅₀ by geometry and test whether equal physical displacements produce different inclusion probabilities when their geometric disruption differs. Compare this mixture against a continuous graded-influence model using held-out predictive criteria and posterior predictive checks for variance and bimodality.

### 7. Power and preregistration

Use pilot estimates of within-participant variance, $J_i$, superposition residuals, and Δ₅₀ to simulate the hierarchical analysis and choose participant/repetition counts. Preregister the linearity equivalence margin, primary geometry predictors, model comparison metric, exclusions, confirmatory target/point locations, and the precise held-out generalization test.

## Running and checking the design

Install the dependencies in `requirements.txt`, then generate a complete manifest without opening the task:

```text
python run_exp.py --dry-run --block identification
```

Run the two complementary identification sessions:

```text
python run_exp.py --block identification --partition-count 2 --partition-index 1 --session-id 1 --participant-id P001
python run_exp.py --block identification --partition-count 2 --partition-index 2 --session-id 2 --participant-id P001
```

Run the default 150-trial segmentation pilot at the midpoint target:

```text
python run_exp.py --block segmentation --participant-id P001 --session-id 3
```

Automated geometry, display, movement, and CSV checks are in `test_experiment.py` and can be run with:

```text
python -m unittest -v test_experiment
```

Normal interactive runs create exactly two CSVs before the welcome screen, under the `data` folder next to `run_exp.py`, independently of PyCharm's working directory:

- `<participant>_<block>_s<session>_<timestamp>_trials.csv`: one row per submitted experimental trial, including geometry and response.
- `<participant>_<block>_s<session>_<timestamp>_presses.csv`: one matching row with the ordered key sequence and cumulative reversals.

Both files initially contain headers; they gain rows after Next/Enter/Space submits an experimental trial. Practice is unrecorded. Esc/window close preserves completed trials; the unfinished trial is not submitted. Files are replaced atomically individually after each trial. The two files are not a single transaction: if the process or disk fails between replacements, compare `trial_uid` across them. Default timestamps prevent overwrites; an explicit existing output prefix raises an error.

A manifest is optional (`--manifest /path/manifest.csv`) or generated by `--dry-run`. It describes the planned trials, not proof that they were completed.

### PyCharm

Open `run_exp.py` and choose Run. Use the existing interpreter at `../.venv/bin/python` (relative to this project); it has numpy, pandas, and pygame. The system Python inspected on this machine lacks numpy. If using another interpreter, install `requirements.txt` into that interpreter. No command-line parameters are necessary. Set `--participant-id P001 --session-id 1` in the Run Configuration for participant collection; the default is labeled `pilot`. Full output paths appear in the Run console.

### Latest chat: interpretation and remaining design limits

The central question is which common geometric smoothness rule explains the signed influence field across curve families. Curvature magnitude and curvature variation are distinct; the polynomial degree of a stimulus does not identify the degree of an observer's spline. Candidate comparisons should include coordinate bending energy, geometric curvature energy/elastica, curvature-variation energy, and minimum angle variance. These are analysis models, not curves drawn as answers for participants.

The current executable is an interpolation pilot. Segmentation remains an optional separate block. It uses isotropic dots and does not add detection or orientation-cue tasks. It implements matched signs, all visible perturbation locations, paired superposition probes, midpoint/off-center targets, and rotation/reflection.

Specific limits before a confirmatory study:

- Circle-versus-polynomial curvature-matched pairs are not explicitly constructed. Standard family comparisons do not isolate curvature variation by themselves.
- Rotation is fixed within each matched baseline; repeated orientations of the same geometry are needed for a clean coordinate-versus-geometric invariance test.
- One small magnitude does not test homogeneity across magnitudes. Default single repetitions do not establish a response distribution or segmentation threshold.
- Normal directions are estimated from baseline point secants; curvature uses three-point circumcircles, and arc distances use chord sums. These discrete quantities approximate the underlying continuous geometry.
- `target_dkappa_ds_baseline` and `local_dkappa_ds_rms_baseline` differentiate raw discrete curvature along chord arc length. Existing spacing-weighted curvature inconsistency columns are retained but must not be interpreted as pure curvature variation: unequal spacing can change them on a circle.
- “Correct” coordinate columns denote the hidden generating-curve sample, not an established perceptual answer. Positive response is toward the Z marker along the baseline left normal, which is not necessarily upward on screen.
- Starting offsets can be clipped by the aperture; compare requested `initial_offset_px` with `actual_initial_offset_px` during analysis. Response time ends at submission, before the confirmation flash.

Validation uses the real Pygame trial loop with SDL's dummy display and synthetic key/click events, covers every default identification and segmentation condition, and checks geometry invariance, display bounds, response signs, and incremental CSV persistence. A six-family render was also visually inspected. This does not replace an in-person PyCharm/monitor pilot.

