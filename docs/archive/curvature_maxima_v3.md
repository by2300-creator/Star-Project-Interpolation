# Curvature-matched midpoint interpolation

Implemented September 29, 2026. New stimulus version: `2026-09-29_curvature_maxima_v3`.

## Question

Does matching curvature at a missing point produce similar human interpolation across different contour configurations? The missing point remains the fifth of nine positions, with four visible dots on either side. For the new stimuli, it lies at an analytic maximum of absolute curvature, rather than at the original polynomial origin.

This tests whether the specified local properties are sufficient for invariant responses. It does not make the visible neighborhoods identical or isolate a pure distant-context effect.

## Running and switching

Run `run_exp.py` in PyCharm as usual. Near the top of that file:

```python
ENABLE_CURVATURE_MAXIMA = True
FINE_ADJUSTMENT_DEFAULT = True
```

- New design on: 108 original conditions once + 108 new conditions = 216 recorded trials.
- New design off: original 108 conditions twice = 216 recorded trials.
- Both modes: 20 gradual practice trials, 236 adjustments total. Trials from the two sets are mixed, not presented as consecutive 108-trial blocks.
- Command line: `--curvature-maxima` / `--no-curvature-maxima` override the code switch.
- For one legacy repetition: `--no-curvature-maxima --repetitions 1`.
- Combined mode requires the standard original targets, strength and spacing, and disallows `--repetitions`. Conflicting options raise an error instead of silently changing the scientific design.
- Optional segmentation is separate and retains its former settings. The maxima switch applies only to identification.
- Two-way partitioning preserves 108 trials per partition, with full conditions for assigned configurations.

`curvature_maxima.py` contains the new generator and trial builder. Running it directly prints a numeric audit. It is imported by `run_exp.py`, and requires only the project's existing NumPy/Pandas dependencies.

## New trial allocation

| Factor | Count |
|---|---:|
| Families: quadratic (`parabola`), cubic, quartic | 3 |
| Matched target curvature levels | 2 |
| Visible dots perturbed singly | 8 |
| Signs per dot | 2 |
| Additional baseline trials per family/level | 2 |

Total: **3 × 2 × (8 × 2 + 2) = 108**. There are 96 perturbed trials and 12 baselines. Each new baseline configuration is observed twice with opposite initial sides. Each nonzero condition appears once. Original trials retain their six families, midpoint perturbations and off-center baselines, but only one repetition when the addition is enabled.

The two curvature levels are practical pilot choices, not literature-validated optimum values. Keeping 108 added trials trades repeated nonzero conditions for a second curvature level. Do not claim high individual repeatability from this allocation.

## How the curves are made

1. Start with the pure polynomial `y = u**n`, for n = 2, 3 or 4.
2. Curvature is `n(n-1)u**(n-2) / (1+n²u**(2n-2))**1.5`. The quadratic peak is at u = 0. For n > 2, the selected positive peak is `((n-2)/(n²(2n-1)))**(1/(2n-2))`.
3. Translate that point to a local origin and rotate its analytic tangent horizontally.
4. Uniformly scale by the ratio of the original peak curvature to the desired curvature. This preserves the polynomial curve under a similarity transformation. There is no vertical-only flattening and no endpoint renormalization.
5. Integrate arc length and sample at -60, -45, -30, -15, 0, 15, 30, 45, 60 local units. The analytic peak is exactly index 4. The curve is extended as needed, rather than moving existing dot indices approximately.
6. Apply matched reflection, rotation and small translation, shared across families and levels for each condition position. Display with one fixed 5 px/unit scale.

| Level | Target curvature magnitude, local units | Displayed curvature magnitude | Radius at target |
|---|---:|---:|---:|
| Low | 0.008 | 0.0016 per pixel | 625 pixels |
| High | 0.016 | 0.0032 per pixel | 312.5 pixels |

Adjacent arc-length spacing is 75 pixels, including the intervals leading to the missing point. The missing interval is therefore 150 pixels of generating-curve arc length. Straight-line dot distances can differ between families. The low and high levels share sampling distances, while curvature changes.

The renderer refuses a display that cannot fit the matched set at its fixed scale. It never silently shrinks just one contour. These are pixel-based controls; visual-angle claims require monitor and viewing-distance calibration.

## Perturbation and nuisance controls

- New single-dot perturbations use the analytic local normal of the unperturbed curve. The target moves along its analytic normal, avoiding a family-dependent three-dot tangent estimate at the peak.
- Magnitude is 13.33% of the common 15-unit arc spacing by default: **2 units = 10 pixels for every perturbed dot**. This differs from the original block's percentage of each dot's local chord spacing. `perturbation_magnitude_basis` records the distinction.
- Signs at the same dot share baseline geometry, pose, displacement magnitude, target translation and starting position.
- Rotation alternates -15/+15 degrees across dot slots. Reflection is balanced across those slots. Assignments are identical across families and curvature levels. They are not a fully crossed orientation experiment; point-specific effects remain conditional on their assigned pose.
- Both baseline settings share one pose and translation. They differ in starting side only. Their pose is not matched separately to every perturbed-dot condition; use opposite-sign contrasts as the primary influence estimate.
- Initial distances vary deterministically between 45 and 85 pixels in the new set. The two signs and corresponding family/level conditions share them.
- The target position is translated by up to 4 units (20 pixels) per axis before display rotation, keeping it away from a fixed center cue. Translation is shared within matching comparisons.
- Same target index, count of visible dots, dot appearance, display scale and response procedure across the new set.

## Response procedure improvements

Both sets and practice now start with 1-pixel movements. Key 3 selects 10-pixel movements; key 2 selects 5; key 1 restores 1. The previous direction-reversal refinement remains. Set `FINE_ADJUSTMENT_DEFAULT = False` to restore coarse initial steps.

Enter/Space must be released before another keyboard confirmation can occur. Synthetic keyboard submission events are tagged with a trial token, and stale tokens are rejected. This addresses a plausible source of extremely rapid accidental submissions; it does not prove the cause of the prior pilot's 13-ms trial. Mouse Next remains available. No arbitrary reaction-time exclusion or forced movement is imposed.

The original stimuli themselves are unchanged, but the default input step now differs from earlier sessions. The input version and initial step are recorded, so historical sessions should not be treated as procedurally identical without accounting for this change.

## Recording

Both CSVs are still created before the welcome screen and updated synchronously after every completed experimental trial. Practice remains excluded. Historical participant CSVs are untouched.

Both tables include `stimulus_set`, `curvature_level` and `repetition`. New trial rows additionally include:

- `matched_curvature_units`, `target_analytic_curvature_px` and `target_arc_curvature_derivative` (zero at the selected peak).
- `target_location_rule`, `curvature_peak_parameter`, `sample_parameters`, `sample_arc_offsets` and `sample_analytic_curvatures`.
- `requested_display_scale`, actual `display_scale_px_per_unit`, `normalization_scale`.
- Perturbation magnitude/direction basis, reference spacing and actual signed perturbations.
- Target translation, matched pose ID and baseline repeat number.
- `initial_step_px` and `input_version`.

The existing sampled curvature fields remain available. They describe finite three-point geometry and need not equal the analytic curvature at the hidden maximum. Use the new analytic field to audit the curvature match.

For baseline bias across reflected conditions, align responses to bending direction, for example multiply the normal response by the sign of analytic target curvature. For perturbation influence, divide the positive-minus-negative response difference by twice the actual displacement; reflections affect both local-normal perturbation and response coordinates. Do not pool signed raw positions across arbitrary reflections without a declared convention.

## Interpretation and remaining limitations

The added design matches target curvature and arc sampling, not all nearby geometry. Nearest-dot chord distances, curvature away from the target, endpoint locations and whole-shape symmetry still differ. Those differences are documented components of the contour configurations. A detected family effect would show that the matched properties were insufficient, not necessarily that distant context caused the effect.

An identical-nearest-dots/different-outer-context experiment is not included: it would require abandoning pure polynomial families and allocating extra conditions. Multiple small perturbation magnitudes and grouping judgments are also not part of this 108-trial addition. The current addition retains one perturbation magnitude and does not establish linearity.

Original and new blocks differ in sampling, target rule and perturbation definition. The primary invariance comparison is **between the three new families within the same curvature level**, not a raw original-versus-new difference.

For an invariance claim, prespecify meaningful equivalence bounds on baseline bias and influence differences. A nonsignificant difference alone is not evidence of equivalence. The pilot should guide measurement precision and the participant/repetition allocation needed for a confirmatory study.

## Validation

`python -m unittest test_experiment -q` verifies both modes, unique trial IDs, partitions, paired signs and starts, analytic peaks, independently integrated arc spacing, common displayed curvature and perturbation displacement, screen bounds, fine movement, stale keyboard submissions and per-trial persistence of both CSVs.

`docs/curvature_maxima_preview.png` shows rendered example screens for the six configurations. Physical-display piloting is still needed to assess perceptual difficulty and adequacy of practice.
