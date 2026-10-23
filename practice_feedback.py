"""Prespecified training tolerances, not estimates of visual acuity or JND."""
import math

PRACTICE_PROTOCOL_VERSION = '2026-10-04_unperturbed_feedback_v1'
GOOD_FRACTION = 0.05
MODERATE_FRACTION = 0.15
FEEDBACK_DURATION_MS = 1500


def evaluate_feedback(error_px, reference_spacing_px):
    """Absolute target error / mean target-to-neighbor chord distance."""
    if not math.isfinite(error_px) or not math.isfinite(reference_spacing_px) or reference_spacing_px <= 0:
        raise ValueError('Feedback requires finite error and positive local spacing.')
    ratio = abs(error_px) / reference_spacing_px
    if ratio <= GOOD_FRACTION + 1e-12:
        level, sentence = 'good', 'Good: your point is close to the reference.'
    elif ratio <= MODERATE_FRACTION + 1e-12:
        level, sentence = 'moderate', 'Moderate: your point is a little away from the reference.'
    else:
        level, sentence = 'needs_adjustment', 'Needs adjustment: your point is far from the reference.'
    return dict(level=level, sentence=sentence, absolute_error_px=abs(float(error_px)),
                normalized_error=ratio, reference_spacing_px=float(reference_spacing_px),
                good_limit_px=GOOD_FRACTION*reference_spacing_px,
                moderate_limit_px=MODERATE_FRACTION*reference_spacing_px)
