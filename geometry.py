"""Geometry utilities shared by stimulus generation, perturbation, and recording.

All calculations use the local, pre-display coordinate system.  Curvature is
reported both in inverse local units and in a dimensionless form obtained by
multiplying by local point spacing.  The latter is the primary analysis scale.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np


EPS = 1e-12


def as_points(xs: Sequence[float], ys: Sequence[float]) -> np.ndarray:
    points = np.column_stack((np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)))
    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError("Expected matching one-dimensional x and y coordinate arrays.")
    return points


def segment_lengths(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=float)
    if len(points) < 2:
        return np.zeros(0, dtype=float)
    return np.linalg.norm(np.diff(points, axis=0), axis=1)


def cumulative_arc_length(points: np.ndarray) -> np.ndarray:
    lengths = segment_lengths(points)
    return np.concatenate(([0.0], np.cumsum(lengths)))


def local_spacings(points: np.ndarray) -> np.ndarray:
    """Return a stable per-point spacing based on adjacent chord lengths."""
    points = np.asarray(points, dtype=float)
    n = len(points)
    if n == 0:
        return np.zeros(0, dtype=float)
    if n == 1:
        return np.ones(1, dtype=float)
    seg = segment_lengths(points)
    spacing = np.empty(n, dtype=float)
    spacing[0] = seg[0]
    spacing[-1] = seg[-1]
    if n > 2:
        spacing[1:-1] = 0.5 * (seg[:-1] + seg[1:])
    return np.maximum(spacing, EPS)


def signed_menger_curvature(p0: Sequence[float], p1: Sequence[float], p2: Sequence[float]) -> float:
    """Signed curvature of the circumcircle through three ordered points."""
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    a = float(np.linalg.norm(p1 - p0))
    b = float(np.linalg.norm(p2 - p1))
    c = float(np.linalg.norm(p2 - p0))
    denom = a * b * c
    if denom <= EPS:
        return 0.0
    first = p1 - p0
    second = p2 - p0
    cross = float(first[0] * second[1] - first[1] * second[0])
    return float(2.0 * cross / denom)


def pointwise_curvatures(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=float)
    n = len(points)
    if n < 3:
        return np.zeros(n, dtype=float)
    values = np.zeros(n, dtype=float)
    for i in range(1, n - 1):
        values[i] = signed_menger_curvature(points[i - 1], points[i], points[i + 1])
    values[0] = values[1]
    values[-1] = values[-2]
    return values


def pointwise_turning_angles(points: np.ndarray) -> np.ndarray:
    """Signed turning angle at each sample, with endpoint values copied inward."""
    points = np.asarray(points, dtype=float)
    n = len(points)
    if n < 3:
        return np.zeros(n, dtype=float)
    values = np.zeros(n, dtype=float)
    for i in range(1, n - 1):
        incoming = points[i] - points[i - 1]
        outgoing = points[i + 1] - points[i]
        denom = float(np.linalg.norm(incoming) * np.linalg.norm(outgoing))
        if denom <= EPS:
            values[i] = 0.0
            continue
        cross = float(incoming[0] * outgoing[1] - incoming[1] * outgoing[0])
        dot = float(np.dot(incoming, outgoing))
        values[i] = math.atan2(cross, dot)
    values[0] = values[1]
    values[-1] = values[-2]
    return values


def tangents_and_normals(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Estimate unit tangents and consistently oriented left normals."""
    points = np.asarray(points, dtype=float)
    n = len(points)
    if n < 2:
        raise ValueError("At least two points are required to estimate tangents.")
    tangents = np.zeros_like(points, dtype=float)
    tangents[0] = points[1] - points[0]
    tangents[-1] = points[-1] - points[-2]
    if n > 2:
        tangents[1:-1] = points[2:] - points[:-2]
    norms = np.linalg.norm(tangents, axis=1)
    if np.any(norms <= EPS):
        raise ValueError("Degenerate point sequence: a tangent has zero length.")
    tangents = tangents / norms[:, None]
    normals = np.column_stack((-tangents[:, 1], tangents[:, 0]))
    return tangents, normals


def curvature_inconsistency(dimensionless_curvature: np.ndarray, indices: Iterable[int] | None = None) -> float:
    values = np.asarray(dimensionless_curvature, dtype=float)
    if indices is not None:
        idx = sorted(set(int(i) for i in indices if 0 <= int(i) < len(values)))
        values = values[idx]
    if len(values) < 2:
        return 0.0
    return float(np.mean(np.abs(np.diff(values))))


def geometry_features(points: np.ndarray, target_index: int) -> dict:
    points = np.asarray(points, dtype=float)
    target_index = int(target_index)
    if not 0 <= target_index < len(points):
        raise ValueError("target_index is outside the point sequence.")

    spacing = local_spacings(points)
    curvature = pointwise_curvatures(points)
    dimensionless_curvature = curvature * spacing
    turning = pointwise_turning_angles(points)
    tangents, normals = tangents_and_normals(points)
    arc = cumulative_arc_length(points)
    median_spacing = float(np.median(segment_lengths(points))) if len(points) > 1 else 1.0
    median_spacing = max(median_spacing, EPS)
    signed_arc_distance = (arc - arc[target_index]) / median_spacing

    lo = max(0, target_index - 2)
    hi = min(len(points), target_index + 3)
    local = dimensionless_curvature[lo:hi]
    local_spacing = spacing[lo:hi]
    # Differentiate raw curvature, not kappa * variable spacing: a circle must
    # have zero curvature variation even when sample spacing is irregular.
    interior = np.arange(1, len(points) - 1)
    derivative = np.zeros(len(points))
    if len(interior) >= 2:
        derivative[interior] = np.gradient(curvature[interior], arc[interior])
        derivative[0], derivative[-1] = derivative[1], derivative[-2]

    return {
        "curvature_derivative": derivative,
        "target_curvature_derivative": float(derivative[target_index]),
        "local_curvature_derivative_rms": float(np.sqrt(np.mean(derivative[lo:hi] ** 2))),
        "spacing": spacing,
        "curvature": curvature,
        "dimensionless_curvature": dimensionless_curvature,
        "turning_angle": turning,
        "tangents": tangents,
        "normals": normals,
        "arc": arc,
        "signed_arc_distance": signed_arc_distance,
        "target_curvature": float(curvature[target_index]),
        "target_dimensionless_curvature": float(dimensionless_curvature[target_index]),
        "local_curvature_mean": float(np.mean(local)),
        "local_abs_curvature_mean": float(np.mean(np.abs(local))),
        "local_curvature_variance": float(np.var(local)),
        "local_curvature_inconsistency": curvature_inconsistency(local),
        "local_turning_variance": float(np.var(turning[lo:hi])),
        "local_spacing_mean": float(np.mean(local_spacing)),
        "local_spacing_cv": float(np.std(local_spacing) / max(np.mean(local_spacing), EPS)),
        "median_spacing": median_spacing,
    }


def geometry_disruption(
    baseline_points: np.ndarray,
    displayed_points: np.ndarray,
    target_index: int,
    perturbed_indices: Iterable[int] = (),
) -> dict[str, float]:
    """Summarize how a perturbation changes local, scale-normalized geometry."""
    baseline = geometry_features(baseline_points, target_index)
    displayed = geometry_features(displayed_points, target_index)
    delta_k = displayed["dimensionless_curvature"] - baseline["dimensionless_curvature"]
    delta_turn = displayed["turning_angle"] - baseline["turning_angle"]

    affected: set[int] = set()
    for raw_idx in perturbed_indices:
        idx = int(raw_idx)
        affected.update(range(max(0, idx - 1), min(len(delta_k), idx + 2)))
    if not affected:
        affected.add(int(target_index))
    affected_idx = np.asarray(sorted(affected), dtype=int)

    target_window = np.arange(
        max(0, int(target_index) - 2),
        min(len(delta_k), int(target_index) + 3),
        dtype=int,
    )

    return {
        "geometry_disruption_rms": float(np.sqrt(np.mean(delta_k[affected_idx] ** 2))),
        "geometry_disruption_max": float(np.max(np.abs(delta_k[affected_idx]))),
        "turning_disruption_rms": float(np.sqrt(np.mean(delta_turn[affected_idx] ** 2))),
        "target_window_disruption_rms": float(np.sqrt(np.mean(delta_k[target_window] ** 2))),
        "delta_local_curvature_variance": float(
            displayed["local_curvature_variance"] - baseline["local_curvature_variance"]
        ),
        "delta_local_curvature_inconsistency": float(
            displayed["local_curvature_inconsistency"] - baseline["local_curvature_inconsistency"]
        ),
    }
