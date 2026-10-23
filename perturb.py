"""Contour-normal perturbations for Jacobian and segmentation trials."""

from __future__ import annotations

import json
import random
from typing import Iterable, Sequence

import numpy as np

from geometry import as_points, geometry_disruption, geometry_features


ENABLE_TYPE_0 = True
ENABLE_TYPE_1 = True
ENABLE_TYPE_2 = True
ENABLE_TYPE_3 = True

DEFAULT_PERTURB_MIN_PX = 4
DEFAULT_PERTURB_MAX_PX = 8
TYPE_DEFAULTS = {1: (4, 8), 2: (8, 12), 3: (12, 16)}


def define_rotation(meta, rotation_deg=None):
    """Attach a display rotation; a supplied value keeps matched trials identical."""
    meta["rotation_deg"] = (
        float(rotation_deg) if rotation_deg is not None else random.uniform(-22.5, 22.5)
    )
    return meta


def _normalize_pattern(perturbations: Iterable[Sequence[int]]) -> list[tuple[int, int]]:
    pattern: list[tuple[int, int]] = []
    seen: set[int] = set()
    for item in perturbations:
        if len(item) != 2:
            raise ValueError("Each perturbation must be an (index, sign) pair.")
        index, sign = int(item[0]), int(item[1])
        if sign not in (-1, 1):
            raise ValueError("Perturbation sign must be -1 or +1.")
        if index in seen:
            raise ValueError(f"Point {index} appears more than once in one perturbation pattern.")
        seen.add(index)
        pattern.append((index, sign))
    return pattern


def apply_normal_perturbations(
    pts_df,
    meta,
    perturbations: Iterable[Sequence[int]] = (),
    magnitude_fraction: float = 0.0,
    regime: str = "baseline",
    condition_type: str = "baseline",
    absolute_magnitude_units: float | None = None,
):
    """Move one or more visible samples along their baseline contour normals.

    Magnitude is expressed as a fraction of each point's local spacing.  Paired
    perturbations are computed from the same unperturbed baseline so their
    vector sum is well defined for the superposition test.
    """
    pattern = _normalize_pattern(perturbations)
    target_index = int(meta["movable_index"])
    if any(index == target_index for index, _ in pattern):
        raise ValueError("The adjustable/hidden point cannot also be perturbed.")
    if any(not 0 <= index < len(pts_df) for index, _ in pattern):
        raise ValueError("A perturbation index is outside the point sequence.")
    magnitude_fraction = float(magnitude_fraction)
    if magnitude_fraction < 0:
        raise ValueError("magnitude_fraction must be non-negative; use sign for direction.")

    result = pts_df.copy(deep=True)
    baseline_points = as_points(result["x"].to_numpy(), result["y"].to_numpy())
    baseline = geometry_features(baseline_points, target_index)
    normals = np.asarray(meta.get('analytic_normals', baseline['normals']), dtype=float)
    if absolute_magnitude_units is not None and (not np.isfinite(absolute_magnitude_units) or absolute_magnitude_units < 0):
        raise ValueError('Absolute perturbation magnitude must be finite and nonnegative.')
    displayed_points = baseline_points.copy()
    actual_units: list[float] = []

    for index, sign in pattern:
        delta_units = (magnitude_fraction * float(baseline["spacing"][index])
                       if absolute_magnitude_units is None else float(absolute_magnitude_units))
        displayed_points[index] += sign * delta_units * normals[index]
        actual_units.append(float(sign * delta_units))

    result["x"] = displayed_points[:, 0]
    result["y"] = displayed_points[:, 1]
    disruption = geometry_disruption(
        baseline_points,
        displayed_points,
        target_index,
        perturbed_indices=[index for index, _ in pattern],
    )
    displayed = geometry_features(displayed_points, target_index)

    pattern_string = ";".join(f"{index}:{sign:+d}" for index, sign in pattern)
    relation = "none"
    if len(pattern) == 1:
        index, sign = pattern[0]
        local_kappa = float(baseline["curvature"][index])
        if abs(local_kappa) <= 1e-12:
            relation = "flat"
        else:
            relation = "toward_center" if sign * local_kappa > 0 else "away_from_center"

    meta.update(
        {
            "baseline_x_vals": [float(value) for value in baseline_points[:, 0]],
            "baseline_y_vals": [float(value) for value in baseline_points[:, 1]],
            "perturbation_regime": str(regime),
            "condition_type": str(condition_type),
            "perturbation_pattern": pattern_string,
            "perturb_indices": json.dumps([index for index, _ in pattern]),
            "perturb_signs": json.dumps([sign for _, sign in pattern]),
            "perturb_actual_units": json.dumps(actual_units),
            "perturb_count": len(pattern),
            "perturb_fraction": magnitude_fraction,
            "perturb_direction_relation": relation,
            "perturb_type": 0 if not pattern else (1 if regime == "small" else 2),
            "perturb_index": pattern[0][0] if len(pattern) == 1 else "",
            "perturb_sign": pattern[0][1] if len(pattern) == 1 else "",
            "perturb_units": actual_units[0] if len(pattern) == 1 else "",
            "perturb_pixels": "",  # filled after display scale is known
            "displayed_local_curvature_variance": float(displayed["local_curvature_variance"]),
            "displayed_local_curvature_inconsistency": float(
                displayed["local_curvature_inconsistency"]
            ),
            **disruption,
        }
    )
    return result, meta


def apply_perturbation(
    pts_df,
    meta,
    perturb_min_px=None,
    perturb_max_px=None,
    px_per_unit=None,
    perturb_idx=None,
    perturb_type=1,
    perturb_sign=None,
    force_vertical_in_screen=False,
):
    """Compatibility wrapper for the earlier single-point API.

    New experimental code should call :func:`apply_normal_perturbations` with a
    dimensionless local-spacing fraction. ``force_vertical_in_screen`` is kept
    only so older scripts continue to call this function; perturbations are now
    deliberately contour-normal in every case.
    """
    del force_vertical_in_screen
    perturb_type = int(perturb_type)
    if perturb_type == 0:
        return apply_normal_perturbations(pts_df, meta, (), 0.0, "baseline", "baseline")
    if perturb_type not in TYPE_DEFAULTS:
        raise ValueError(f"Unsupported perturb_type: {perturb_type}")

    target_index = int(meta["movable_index"])
    eligible = [index for index in range(len(pts_df)) if index != target_index]
    chosen_index = random.choice(eligible) if perturb_idx is None else int(perturb_idx)
    if chosen_index not in eligible:
        raise ValueError(f"perturb_idx {chosen_index} must be one of {eligible}")
    sign = random.choice([-1, 1]) if perturb_sign is None else int(perturb_sign)
    if sign not in (-1, 1):
        raise ValueError("perturb_sign must be -1 or +1.")

    default_min, default_max = TYPE_DEFAULTS[perturb_type]
    low = default_min if perturb_min_px is None else int(perturb_min_px)
    high = default_max if perturb_max_px is None else int(perturb_max_px)
    if low > high:
        low, high = high, low
    magnitude_px = random.randint(low, high)
    px_per_unit = float(px_per_unit or meta.get("px_per_unit") or 5.0)

    points = as_points(pts_df["x"].to_numpy(), pts_df["y"].to_numpy())
    spacing = geometry_features(points, target_index)["spacing"][chosen_index]
    fraction = (magnitude_px / px_per_unit) / float(spacing)
    regime = "small" if perturb_type == 1 else "segmentation"
    result, meta = apply_normal_perturbations(
        pts_df,
        meta,
        [(chosen_index, sign)],
        magnitude_fraction=fraction,
        regime=regime,
        condition_type="single",
    )
    meta["perturb_pixels"] = int(sign * magnitude_px)
    return result, meta
