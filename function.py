"""Generate controlled contour samples for the interpolation experiment.

Curve family is a stimulus generator, not the intended psychological
explanatory variable. Every family is sampled at the same normalized
arc-length fractions and then similarity-normalized, so function degree is not
silently substituted for point spacing or retinal size.
"""

from __future__ import annotations

import math
import random
from typing import Sequence

import numpy as np
import pandas as pd

from geometry import geometry_features


END_HALFSPAN = 60.0
NUM_POINTS = 9  # eight visible anchors plus one adjustable/hidden sample

SUPPORTED_FUNCTIONS = ("line", "parabola", "cubic", "quartic", "quintic", "circle")

# Fixed irregular knots are used for operator identification. They are fixed
# across families, so spacing can be modeled without changing unpredictably
# from trial to trial. Equal-arc and jittered profiles are also available.
# Index 4 is exactly at the arc-length midpoint.  This preserves the diagnostic
# x^3/x^4/x^5 zero-target-curvature contrast, while index 3 supplies an
# off-center row of the interpolation Jacobian.
FIXED_IRREGULAR_FRACTIONS = np.array([0.0, 0.11, 0.23, 0.35, 0.50, 0.65, 0.77, 0.89, 1.0])
EQUAL_ARC_FRACTIONS = np.linspace(0.0, 1.0, NUM_POINTS)

DEFAULT_CURVE_STRENGTH = {
    "line": 0.0,
    "parabola": 0.75,
    "cubic": 0.80,
    "quartic": 0.90,
    "quintic": 1.00,
    "circle": 1.00,  # semicircle; smaller strengths give shallower circular arcs
}

STRENGTH_MULTIPLIERS = {"low": 0.70, "standard": 1.00, "high": 1.30}


def _normalize_endpoints_similarity(
    x_vals: np.ndarray,
    y_vals: np.ndarray,
    end_halfspan: float = END_HALFSPAN,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Translate, rotate, and uniformly scale endpoints to (+/- halfspan, 0)."""
    p0 = np.array([float(x_vals[0]), float(y_vals[0])])
    p1 = np.array([float(x_vals[-1]), float(y_vals[-1])])
    midpoint = 0.5 * (p0 + p1)
    points = np.column_stack((x_vals, y_vals)) - midpoint
    chord = p1 - p0
    chord_length = float(np.linalg.norm(chord))
    if chord_length <= 1e-12:
        raise ValueError("Curve endpoints coincide; cannot normalize the stimulus.")

    angle = math.atan2(float(chord[1]), float(chord[0]))
    cosine, sine = math.cos(-angle), math.sin(-angle)
    rotation = np.array([[cosine, -sine], [sine, cosine]])
    points = points @ rotation.T
    scale = (2.0 * float(end_halfspan)) / chord_length
    points *= scale
    return points[:, 0], points[:, 1], scale


def _dense_curve(
    function_type: str, strength: float, reversed_curve: bool
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return a dense ordered curve before display normalization."""
    function_type = str(function_type).lower().strip()
    if function_type == "circle":
        if not 0 < strength <= 1:
            raise ValueError("Circular arc strength must be in (0, 1].")
        # strength is sagitta / half-chord: 1 gives a semicircle.
        # Changing angular span preserves a true circle, unlike flattening y.
        half_angle = 2.0 * math.atan(strength)
        theta = np.linspace(math.pi / 2 + half_angle, math.pi / 2 - half_angle, 6001)
        parameter = theta
        x_vals = np.cos(theta)
        y_vals = np.sin(theta) - math.cos(half_angle)
    else:
        u = np.linspace(-1.0, 1.0, 6001)
        parameter = u
        x_vals = u
        if function_type == "line":
            y_vals = np.zeros_like(u)
        elif function_type == "parabola":
            y_vals = strength * u**2
        elif function_type == "cubic":
            y_vals = strength * u**3
        elif function_type == "quartic":
            y_vals = strength * u**4
        elif function_type == "quintic":
            y_vals = strength * u**5
        else:
            raise ValueError(f"Unsupported function_type: {function_type}")

    if reversed_curve:
        y_vals = -y_vals
    return (
        np.asarray(x_vals, dtype=float),
        np.asarray(y_vals, dtype=float),
        np.asarray(parameter, dtype=float),
    )


def _sample_fractions(profile: str, seed: int | None = None) -> np.ndarray:
    profile = str(profile).lower().strip()
    if profile == "fixed_irregular":
        return FIXED_IRREGULAR_FRACTIONS.copy()
    if profile == "equal_arc":
        return EQUAL_ARC_FRACTIONS.copy()
    if profile != "jittered_arc":
        raise ValueError("spacing_profile must be fixed_irregular, equal_arc, or jittered_arc.")

    rng = np.random.default_rng(seed)
    fractions = EQUAL_ARC_FRACTIONS.copy()
    fractions[1:-1] += rng.uniform(-0.025, 0.025, size=NUM_POINTS - 2)
    fractions[1:-1] = np.sort(fractions[1:-1])
    for i in range(1, NUM_POINTS):
        fractions[i] = max(fractions[i], fractions[i - 1] + 0.06)
    fractions[-1] = 1.0
    return fractions


def _resample_by_arc_length(
    x_dense: np.ndarray,
    y_dense: np.ndarray,
    parameter_dense: np.ndarray,
    fractions: Sequence[float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    points = np.column_stack((x_dense, y_dense))
    cumulative = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))))
    if cumulative[-1] <= 1e-12:
        raise ValueError("Degenerate curve has zero arc length.")
    normalized = cumulative / cumulative[-1]
    fractions = np.asarray(fractions, dtype=float)
    return (
        np.interp(fractions, normalized, x_dense),
        np.interp(fractions, normalized, y_dense),
        np.interp(fractions, normalized, parameter_dense),
    )


def _analytic_curvature(
    function_type: str,
    strength: float,
    parameter: float,
    reversed_curve: bool,
    normalization_scale: float,
) -> float:
    """Signed curvature after the final similarity transform."""
    if function_type == "circle":
        raw = 1.0 if reversed_curve else -1.0
        return float(raw / normalization_scale)
    signed_strength = -strength if reversed_curve else strength
    u = float(parameter)
    if function_type == "line":
        raw = 0.0
    elif function_type == "parabola":
        first = 2.0 * signed_strength * u
        second = 2.0 * signed_strength
        raw = second / (1.0 + first * first) ** 1.5
    elif function_type == "cubic":
        first = 3.0 * signed_strength * u**2
        second = 6.0 * signed_strength * u
        raw = second / (1.0 + first * first) ** 1.5
    elif function_type == "quartic":
        first = 4.0 * signed_strength * u**3
        second = 12.0 * signed_strength * u**2
        raw = second / (1.0 + first * first) ** 1.5
    elif function_type == "quintic":
        first = 5.0 * signed_strength * u**4
        second = 20.0 * signed_strength * u**3
        raw = second / (1.0 + first * first) ** 1.5
    else:
        raise ValueError(f"Unsupported function_type: {function_type}")
    return float(raw / normalization_scale)


def generate_function_points(
    function_type: str = "parabola",
    x_range=None,
    force_reversed: bool | None = None,
    movable_index: int | None = None,
    target_index: int | None = None,
    curve_strength: float | None = None,
    strength_level: str = "standard",
    spacing_profile: str = "fixed_irregular",
    stimulus_seed: int | None = None,
    practice_flattening: float = 1.0,
):
    """Generate a repeatable baseline contour and its geometry metadata.

    ``x_range`` remains accepted for compatibility but is intentionally ignored;
    every curve is now normalized using common geometric rules.
    """
    del x_range
    function_type = str(function_type).lower().strip()
    if function_type not in SUPPORTED_FUNCTIONS:
        raise ValueError(f"Unsupported function_type: {function_type}")

    if target_index is not None and movable_index is not None and int(target_index) != int(movable_index):
        raise ValueError("target_index and movable_index disagree.")
    if target_index is None:
        target_index = NUM_POINTS // 2 if movable_index is None else int(movable_index)
    target_index = int(target_index)
    if not 1 <= target_index <= NUM_POINTS - 2:
        raise ValueError("The adjustable target must be an interior point.")

    local_rng = random.Random(stimulus_seed)
    reversed_curve = local_rng.choice([False, True]) if force_reversed is None else bool(force_reversed)

    strength_level = str(strength_level).lower().strip()
    if strength_level not in STRENGTH_MULTIPLIERS:
        raise ValueError(f"Unknown strength_level: {strength_level}")
    if curve_strength is None:
        curve_strength = DEFAULT_CURVE_STRENGTH[function_type] * (1.0 if function_type in ("line", "circle") else STRENGTH_MULTIPLIERS[strength_level])
    curve_strength = float(curve_strength)

    fractions = _sample_fractions(spacing_profile, seed=stimulus_seed)
    x_dense, y_dense, parameter_dense = _dense_curve(function_type, curve_strength, reversed_curve)
    if not 0 < practice_flattening <= 1:
        raise ValueError("practice_flattening must lie in (0, 1].")
    if practice_flattening < 1:
        x_dense, y_dense, _ = _normalize_endpoints_similarity(x_dense, y_dense)
        y_dense *= practice_flattening
    x_vals, y_vals, sampled_parameter = _resample_by_arc_length(
        x_dense, y_dense, parameter_dense, fractions
    )
    x_vals, y_vals, normalization_scale = _normalize_endpoints_similarity(x_vals, y_vals)
    points = np.column_stack((x_vals, y_vals))
    features = geometry_features(points, target_index)
    target_analytic_curvature = _analytic_curvature(
        function_type,
        curve_strength,
        sampled_parameter[target_index],
        reversed_curve,
        normalization_scale,
    )
    if practice_flattening < 1:
        # Practice polynomial contours are flattened AFTER chord alignment.
        # Derive their curvature from the actual deformed dense curve.
        dx = np.gradient(x_dense, parameter_dense)
        dy = np.gradient(y_dense, parameter_dense)
        ddx = np.gradient(dx, parameter_dense)
        ddy = np.gradient(dy, parameter_dense)
        kappa = (dx * ddy - dy * ddx) / (dx * dx + dy * dy) ** 1.5
        target_analytic_curvature = float(np.interp(
            sampled_parameter[target_index], parameter_dense, kappa
        ) / normalization_scale)


    meta = {
        "practice_flattening": float(practice_flattening),
        "movable_index": target_index,
        "target_index": target_index,
        "initial_w": 0.5,
        "correct_w": 0.5,
        "function_type": function_type,
        "curve_family": function_type,
        "reversed": reversed_curve,
        "curve_strength": curve_strength,
        "strength_level": strength_level,
        "spacing_profile": spacing_profile,
        "sample_fractions": [float(value) for value in fractions],
        "sample_parameters": [float(value) for value in sampled_parameter],
        "stimulus_seed": stimulus_seed,
        "endpoint_halfspan": float(END_HALFSPAN),
        "normalization_scale": float(normalization_scale),
        "x_range": "normalized",
        "x_vals": [float(value) for value in x_vals],
        "y_vals": [float(value) for value in y_vals],
        "baseline_x_vals": [float(value) for value in x_vals],
        "baseline_y_vals": [float(value) for value in y_vals],
        "target_tangent_x": float(features["tangents"][target_index, 0]),
        "target_tangent_y": float(features["tangents"][target_index, 1]),
        "target_normal_x": float(features["normals"][target_index, 0]),
        "target_normal_y": float(features["normals"][target_index, 1]),
        "target_curvature": float(features["target_curvature"]),
        "target_dimensionless_curvature": float(features["target_dimensionless_curvature"]),
        "target_analytic_curvature": float(target_analytic_curvature),
        "target_analytic_dimensionless_curvature": float(
            target_analytic_curvature * features["spacing"][target_index]
        ),
        "baseline_local_curvature_mean": float(features["local_curvature_mean"]),
        "baseline_local_abs_curvature_mean": float(features["local_abs_curvature_mean"]),
        "baseline_local_curvature_variance": float(features["local_curvature_variance"]),
        "baseline_local_curvature_inconsistency": float(features["local_curvature_inconsistency"]),
        "baseline_local_turning_variance": float(features["local_turning_variance"]),
        "baseline_local_spacing_mean": float(features["local_spacing_mean"]),
        "baseline_local_spacing_cv": float(features["local_spacing_cv"]),
    }

    # Compatibility fields used by older replay/recording code.
    if function_type in ("parabola", "cubic", "quartic", "quintic"):
        meta["A"] = -curve_strength if reversed_curve else curve_strength
    elif function_type == "line":
        meta["slope"] = 0.0
    else:
        meta["k"] = 1.0

    rows = [{"index": i, "x": float(x), "y": float(y)} for i, (x, y) in enumerate(points)]
    return pd.DataFrame(rows), meta
