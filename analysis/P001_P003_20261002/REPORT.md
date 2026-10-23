# P001–P003: interpolation pilot findings

Analysis date: 2 October 2026. Three participants, 277 retained trials each, 831 recorded observations total. This is a descriptive pilot analysis. The independent participant count is **three**, not 831.

## Main conclusion

The clearest shared pattern is **stronger positive influence from the two dots immediately beside the missing target**. This supports a common tendency to rely heavily on nearby contour evidence. However, unperturbed placements and detailed perturbation profiles differ across configurations. These data do **not establish invariance from matched maximum curvature**, and they do not identify a unique human spline algorithm.

There are promising findings to follow up, particularly the cubic's baseline bias relative to the other matched families. Interpretation must account for three participants, an incomplete counterbalance cycle, a change in P003's movement controls, and a large retained P002 response.

## 1. P002 repair and provenance

The requested boundary was implemented as follows:

- Earlier run `P002_identification_s1_20261001_164256_025570`: retain trials **1–12**.
- Later run `P002_identification_s1_20261001_170310_286302`: retain trials **13–277**.
- Trial **13 comes from the later run**, avoiding duplication.
- Apply the same selection to trial responses and button-press sequences.
- Keep the later run's filenames for both final CSVs.

The early files contained 22 rows each and the later files contained 277. All overlapping trial IDs matched, and the recorded baseline coordinates, rotations, reflections, perturbations, starting offsets, order seed and group matched between runs. The merged files each contain exactly 277 consecutive trial numbers and 277 unique trial IDs. Values were copied as CSV strings, preserving numerical precision. Different press-column widths were reconciled by retaining the union of columns and leaving absent entries blank.

There are now only two active P002 CSVs directly in `data/`. All four pre-merge files, source/output hashes and a merge audit are in `data/archive/P002_before_merge_20261002/`. Earlier trials 13–22 and later trials 1–12 are excluded from analysis, as requested. Any prior exposure during the interrupted run cannot be undone by merging; P002's experience was not identical to an uninterrupted session.

## 2. Completeness and recording checks

Each participant has the intended allocation:

| Component | Per participant | Across three participants |
|---|---:|---:|
| Matched x²–x⁵: 32 perturbations + 16 baselines per family | 192 | 576 |
| Original line, cubic, quartic, quintic, circle: 16 perturbations + 1 baseline per family | 85 | 255 |
| Total | 277 | 831 |

All targets are index 4. No practice trials enter this analysis. All matched target curvatures have recorded absolute magnitude **0.005 per pixel**. Each matched participant × family × dot-context × starting-side combination has its baseline and both perturbation signs: **192 complete triples across the dataset**.

Every retained press sequence was replayed from its recorded initial position. The largest difference from the recorded final coordinates was **2.3 × 10⁻¹³ pixels**, numerical rounding only. Press counts, direction reversals, fine movements and final step size also agree with the trial records. All 831 responses include actual fine movement and finish at 1-pixel steps. Signed responses independently recomputed from the screen coordinates agree with the CSV values.

These checks support recording consistency. They do not prove every participant response was perceptually careful.

## 3. Important protocol difference

| Participant | Counterbalance group | Verified step sizes, px | Median response time | Sum of recorded trial times |
|---|---:|---|---:|---:|
| P001 | 0 | 10 / 5 / 1 | 7.38 s | 36.35 min |
| P002 | 1 | 10 / 5 / 1 | 6.95 s | 39.30 min |
| P003 | 2 | 30 / 10 / 1 | 2.40 s | 13.15 min |

Step schemes were checked against the full press replay; the 30-pixel initial step is also explicitly recorded for P003. P003 uses fewer movements (median 8 versus 14 and 15) and responds much faster. This cannot be attributed solely to skill, care, or motor step size because participant and protocol differ together. The input-version label is unchanged despite the control change, so that label alone is insufficient to identify the protocol.

The time totals exclude practice, unrecorded transitions, breaks and P002's discarded rows. They are not total appointment durations. Groups 0, 1 and 2 are represented once each; group 3 is absent. The planned four-group counterbalancing is therefore incomplete, and individual differences are confounded with group at this sample size.

## 4. How responses were measured

The primary outcome is final displacement from the generating curve's hidden reference point, measured in pixels along the permitted movement line. Positive raw displacement means toward the Z marker. This reference is a geometric benchmark, not a uniquely correct perceptual answer for a perturbed display.

For baselines, reflections can cancel opposite raw signs. To compare bending-related bias, multiply the signed response by the sign of target curvature. **Positive curvature-aligned bias means toward the local bending/concavity side; negative means away.** Absolute deviations are reported separately.

For each matched baseline/negative/positive triple:

`sensitivity = (positive-perturbation response − negative-perturbation response) / (2 × perturbation magnitude)`

A sensitivity of 0.7 means that a 20-pixel difference between the two perturbation positions corresponds to a 14-pixel difference in the response settings. Positive sensitivity means following the signed perturbation; negative means an opposing response. This is a finite difference at the tested magnitude, not proof of a linear response rule. The two starting-side estimates are averaged for participant profiles. Participants receive equal weight in group summaries.

The matched displacements range from **11.43 to 13.94 pixels**, depending on dot position. The original block ranges from **8.80 to 16.83 pixels**. This dataset does not vary magnitude independently at a fixed dot; it cannot establish a dose-response curve. Baseline-subtracted shifts and asymmetry are provided in `matched_triplets.csv`.

## 5. Finding: nearest dots have the strongest shared positive influence

| Participant | Mean sensitivity, nearest dots 3 and 5 | Mean sensitivity, other six dots |
|---|---:|---:|
| P001 | 0.866 | 0.016 |
| P002 | 0.679 | 0.126 |
| P003 | 0.653 | −0.150 |

The across-participant nearest-dot mean is **0.733**. The nearest-dot advantage appears in all three participants, including the two participants who shared the original movement controls.

Do not interpret the other-dot signed mean near zero as absence of influence: positive and negative effects cancel. Mean absolute profile sensitivities for those other dots are **0.277, 0.535 and 0.351**, respectively, compared with **0.866, 0.679 and 0.657** for the nearest dots. Thus a more accurate description is strong local positive influence with additional variable, sometimes opposing influences elsewhere.

![Individual and mean perturbation profiles](</Users/yangbolin/PyCharmMiscProject/Let's move stars! Interpolation Project/analysis/P001_P003_20261002/influence_profiles.png>)

### Mean sensitivity at each visible dot

| Matched family | 0 | 1 | 2 | 3, nearest | 5, nearest | 6 | 7 | 8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| x² | 0.20 | −0.49 | −0.23 | 1.02 | 0.61 | 0.07 | 0.04 | −0.01 |
| x³ | 0.18 | 0.28 | −0.27 | 1.13 | 0.55 | −0.49 | −0.03 | 0.37 |
| x⁴ | 0.64 | −0.54 | −0.41 | 0.97 | 0.40 | −0.25 | 0.02 | −0.08 |
| x⁵ | −0.25 | 0.06 | 0.04 | 0.65 | 0.53 | 0.88* | 0.00 | 0.19 |

*The x⁵ dot-6 mean is strongly affected by P002 trial 10; see Section 7. These profiles are descriptive and noisy, not estimated population weights with demonstrated precision.*

## 6. Finding: matched curvature does not yield identical baseline placements in this pilot

Curvature-aligned mean baseline displacement, pixels; 16 observations per participant/family:

| Family | P001 | P002 | P003 | Mean of participants |
|---|---:|---:|---:|---:|
| x² | −2.06 | −0.88 | −10.69 | −4.54 |
| x³ | +4.00 | +6.75 | +9.44 | +6.73 |
| x⁴ | −3.12 | −9.13 | −6.00 | −6.08 |
| x⁵ | +3.69 | −7.12 | −5.12 | −2.85 |

The cubic is displaced toward its local bending side on average for all three participants, while quadratic and quartic biases go in the other direction. The cubic-minus-quadratic differences are **6.06, 7.63 and 20.12 pixels**. Cubic-minus-quartic differences are **7.12, 15.88 and 15.44 pixels**. The direction of both contrasts remains present in P001 and P002 alone.

This is a useful preliminary signal that matching peak curvature does not fix the perceived interpolation setting. It is not yet a population-level rejection of invariance, and it does not isolate distant context: nearby dot geometry and curvature away from the hidden point also differ between configurations.

Mean absolute baseline deviations, averaged equally across participants, are **7.84 px for x², 10.25 px for x³, 9.10 px for x⁴ and 8.59 px for x⁵**. These numbers combine systematic bias and variability across poses and starting sides; they are not pure sensory precision estimates and do not justify a stable ranking of the curve families.

![Baseline placements and starting-side differences](</Users/yangbolin/PyCharmMiscProject/Let's move stars! Interpolation Project/analysis/P001_P003_20261002/baseline_and_starting_side.png>)

Quartic and quintic do not produce identical settings: their curvature-aligned mean differences are **6.81, 2.00 and 0.88 pixels** (quintic minus quartic). However, the visual contrast is weak by design, the participant estimates vary, and no equivalence bounds were set. Neither equivalent behavior nor a reliable difference is established for that pair.

## 7. Large responses, starting side, and time course

### P002 trial 10 is retained, but influential

This valid early-run response is a negative dot-6 perturbation on the matched quintic. Its final response is **−153.50 px**, compared with a starting offset of −76.50 px. It lasted 41.18 seconds and included 28 fine movements. Its press sequence reproduces the final position, so it is not a merge or coordinate-recording discrepancy. That does not reveal why the participant chose it.

The matching positive response is +2.50 px and the baseline is +10.50 px. This produces one sensitivity estimate of **6.262**, strongly affecting the quintic dot-6 profile. The main results retain it because the user identified trials 1–12 as valid and no response-exclusion rule was prespecified.

As an explicitly post-hoc diagnostic, omitting this entire triple changes P002's mean sensitivity for the six non-nearest dots from **0.126 to −0.005**. Their nearest-dot mean stays **0.679**. This shows that the strongest local-influence finding survives this diagnostic, while a claim of strong quintic outer-dot influence would be unstable. No source data were removed for this diagnostic.

### Starting side and repeated settings

For matched baselines, positive-start minus negative-start mean differences range from **−6.95 to −1.32 px** across P001's families, **−10.32 to +3.43 px** for P002, and **+0.43 to +5.43 px** for P003. They are not uniformly positive, so there is no consistent group-wide pull toward the starting side. Individual variation makes it sensible to retain both starting sides. These differences also include trial-to-trial response variability; a single paired observation per context does not isolate a stable starting-position effect.

P002 speeds up from a 9.41-second median in the first trial quarter to 5.17 seconds in the last. Their median absolute deviation also falls from 14.35 to 6.00 pixels. This could reflect familiarization, trial composition or other session effects; it is not evidence of a causal learning effect. P001's timings are comparatively stable, while P003 is faster throughout. The quarter plot and underlying values are supplied separately.

## 8. Secondary original-block findings

The retained original block has only one baseline and one observation per sign/dot per participant. It should remain secondary to the matched block.

Original quartic baseline responses are **+21, +26 and +41 px** in the recorded Z direction for P001–P003. Original line baselines are **+1, +1 and +3 px**. This suggests that some configurations elicit considerable systematic displacement while straight-line completion is close to the generating reference in these observations. Each number is a single trial, not a stable per-person bias estimate.

Original perturbation profiles also vary substantially by participant. P001's original circle has deviations of 79 and 68 pixels on two perturbed trials, affecting the circle summary. Do not compare original and matched block means as a clean curvature manipulation: their geometry, pose allocation, baseline density and perturbation-normal rules differ. Full original profiles are in `original_influence_profiles.csv`.

## 9. What the data support, and what they do not

**Supported as descriptive pilot observations:**

1. Recording is internally consistent, the intended allocation is complete, and fine adjustment was used.
2. The nearest visible dots exert the clearest shared positive perturbation influence.
3. Cubic baseline settings differ directionally from quadratic and quartic settings in all three participants, despite equal target curvature.
4. Individual responses and control protocols matter; some profile details depend strongly on single responses.

**Not established:** population equivalence or invariance; a reliable quartic–quintic difference; stable rankings of all dot influences; a dose-response relation; or a unique B-spline/human-visual-spline mechanism. There are no confirmatory p-values or equivalence claims here. Trial counts do not replace independent participants, and the original analysis plan left equivalence bounds and sample size unresolved.

## 10. Next steps grounded in this pilot

- Choose and document one movement-step scheme for subsequent collection. Treat these three participants as a pilot if the main protocol changes; do not silently pool P003's altered controls with a supposedly uniform protocol.
- Complete balanced counterbalance cycles, including group 3. One participant per group will still be insufficient to separate individual variation from group effects reliably.
- Keep both starting sides and the matched baselines. Record and review large deviations, but settle exclusion rules before confirmatory analysis rather than choosing them to improve the result.
- Define meaningful equivalence margins separately for baseline displacement and perturbation sensitivity. Plan participant numbers using independent pilot estimates and the intended repeated-measures analysis; three participants do not support a dependable final power estimate.
- Treat the cubic-versus-quadratic/quartic baseline pattern as a candidate finding to replicate. Treat detailed outer-dot differences, especially the quintic dot-6 peak, as provisional.

## Files and reproducibility

The three final trial filenames and their paired press files are listed in `metrics.json`. Derived tables and figures are stored beside this report; raw P001 and P003 files were not changed. `analyze.py` reproduces the recording audit, matched triples, participant summaries, contrasts, diagnostics and plots from the active merged files. No trials were excluded from primary results after the user-specified P002 merge.

Key supporting tables: `participant_quality.csv`, `baseline_summary.csv`, `matched_triplets.csv`, `participant_influence_profiles.csv`, `family_contrasts.csv`, `starting_side_effects.csv`, `largest_deviations.csv`, and `outlier_sensitivity_check.csv`. The P001/P002-only profile table permits inspection without the participant whose controls changed; this is a diagnostic subset, not a replacement primary dataset.
