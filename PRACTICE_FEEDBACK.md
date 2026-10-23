# Practice feedback and stable movement controls

Protocol: `2026-10-04_unperturbed_feedback_v1`. Input mapping: `2026-10-04_screen_up_down_v2`.

## Movement

Z and Up move toward the upper screen endpoint of the response line. Slash and Down move toward the lower endpoint. The line remains the baseline contour normal; no geometry, perturbation or starting position is changed. A perfectly horizontal response line uses Z/Up for left and Slash/Down for right. Green triangles now point outward, in the movement direction toward their respective endpoint, rather than inward in the opposite direction. The response dot remains drawn above the triangles.

The current step sizes are 30, 10 and 1 pixels, preserving the setting already present before this revision. Tutorial values come directly from those settings. Esc remains disabled as an exit shortcut; closing the window exits.

## Three feedback levels

After each accepted practice response, show one sentence for 1.5 seconds. Keyboard and mouse input during that interval do not advance or submit a trial. The window-close button still works.

Let **e** be the absolute response displacement from the generating curve's hidden reference, in display pixels. Let **s** be the mean of the two unperturbed straight-line distances from that reference to its immediately adjacent dots, also in display pixels. Compute **e/s** from the actually rendered scale.

| Level | Rule | If s = 100 pixels | Participant sentence |
|---|---|---|---|
| Good | e/s ≤ 0.05 | ≤5 pixels | Good: your point is close to the reference. |
| Moderate | 0.05 < e/s ≤ 0.15 | >5 to 15 pixels | Moderate: your point is a little away from the reference. |
| Needs adjustment | e/s > 0.15 | >15 pixels | Needs adjustment: your point is far from the reference. |

For the current 20 midpoint practice trials at the standard 800-pixel display, local spacing ranges approximately 90.0–128.2 pixels: the good upper limit is approximately 4.5–6.4 pixels, and the moderate upper limit 13.5–19.2 pixels. These limits vary with the displayed geometry rather than participant performance.

The numerical cutoffs are configurable in `practice_feedback.py`. The program does not display a correct-answer dot or a connecting curve during feedback. It displays only the corresponding sentence, and advances automatically after the same duration at every level. No performance-dependent repeat, exclusion or admission criterion is applied.

## Why this rule is defensible—and its limits

These are **prespecified operational training tolerances**, not established human acuity thresholds, standard deviations, or universally validated boundaries for good perception. The narrow 5% band and broader 15% band provide explicit small/moderate/large deviations relative to the local stimulus scale, with a threefold tolerance difference. Normalization avoids making the grade depend solely on monitor pixel count or the curve's local sample spacing. Uniformly scaling both stimulus and response error leaves the grade unchanged. This does not replace visual-angle calibration when comparing monitors or viewing distances.

No universal 5/15-pixel cutoff is inferred from prior publications. Research on contour localization shows that precision depends on the geometric arrangement of visible evidence, supporting caution about a single universal pixel tolerance: [Local determinants of contour interpolation](https://pmc.ncbi.nlm.nih.gov/articles/PMC3063128/). The 5%/15% choices here are a transparent protocol decision, not thresholds measured in that study or optimized to make P001–P003 perform well. Further pilot work can assess whether the categories are useful, but do not retune them participant by participant during a study.

## Why practice is now unperturbed

The 20-trial gradual progression, families, sampling, rotation/reflection and movement mechanism remain. Practice no longer displaces any fixed dot. This provides a defined generating-curve reference for graded familiarization; scoring perturbed displays against an undisplaced answer would reward resistance to the manipulation being measured. The feedback revision alone left the then-current 277 recorded trials unchanged. The subsequent v7 semicircle revision has 308 recorded trials and changes matched sampling geometry; the same 20-trial practice and feedback protocol remains.

Even an unperturbed dotted display permits multiple possible interpolating curves. Feedback therefore describes agreement with the generating reference, not a unique perceptual truth. This is supervised familiarization and may teach a preference for the reference. That influence is part of the protocol and must be reported. Feedback studies show learning can depend on the feedback arrangement, but do not validate these exact cutoffs: [The role of feedback in learning a vernier discrimination task](https://pubmed.ncbi.nlm.nih.gov/9327060/).

Use the same 20-trial progression, feedback rules and movement controls for a confirmatory participant cohort. Do not silently pool these new sessions with earlier no-feedback sessions as though training were identical.

## Recording and analysis

Practice remains outside the two experimental CSVs. Its per-trial results are held in `Canvas.practice_feedback_history` during execution for testing/inspection, not saved as participant outcome rows. Experimental rows record the practice protocol version, whether feedback was received, the two cutoff fractions and feedback duration. `--skip-tutorial` sets `practice_feedback_received` false. The experimenter viewer still bypasses practice and supplies no performance feedback.

Keyboard mapping and scientific response direction are kept separate:

- `response_normal_px` retains the original baseline-normal sign used by the perturbation analysis. It does not change sign merely because keyboard endpoints swap.
- `response_screen_up_px` is positive toward Z/screen up.
- `control_up_normal_sign` is +1 when screen-up follows the baseline normal and −1 otherwise. Thus `response_normal_px = response_screen_up_px × control_up_normal_sign`.
- `ref_up_*` and `ref_down_*` identify the actual Z and slash endpoints for replay.
- `input_version`, `response_sign_convention` and the full `step_sizes_px` array document the controls. Existing CSVs are not rewritten.

For older sessions, the Z marker followed the baseline-normal direction and could be lower on screen. Historical reports remain correct for their recorded protocol. New analyses must read the mapping fields rather than assume every `up` press adds positively to `response_normal_px`.

## Suggested methods wording

“Participants completed 20 unperturbed practice trials progressing from shallow to more curved contours. After each response, a three-level message was displayed for 1.5 s. Absolute displacement from the generating-curve reference was normalized by the mean target-to-adjacent-dot chord distance in the displayed stimulus. Errors at or below 5% were labeled good, errors above 5% and at or below 15% moderate, and errors above 15% as needing adjustment. These prespecified tolerances were used for familiarization, not participant exclusion or claims about perceptual acuity. No performance feedback was provided during the recorded experimental trials.”
