"""Polynomial curvature maxima and a true semicircle at matched curvature.

Imported by run_exp.py. Run this file directly for a numeric design audit.
No endpoint normalization or shape-dependent display fitting is permitted.
"""
from functools import lru_cache
import math
import random
import numpy as np
import pandas as pd
from geometry import geometry_features, local_spacings
from function import generate_function_points

DESIGN_VERSION = '2026-10-06_all_chords_v9'
DISPLAY_SCALE = 5.0
FAMILIES = {'parabola': 2, 'circle': None, 'cubic': 3, 'quartic': 4, 'quintic': 5}

# Derive the reference from the actual original generator, not a second copy
# of its coefficients or spacing profile.
_reference_points, _reference_meta = generate_function_points(
    'parabola', target_index=4, force_reversed=False,
    strength_level='standard', spacing_profile='fixed_irregular')
REFERENCE_CURVATURE = abs(_reference_meta['target_analytic_curvature'])
CURVATURE_LEVELS = {'parabola_reference': REFERENCE_CURVATURE}
_b = 2 * _reference_meta['curve_strength']
_u = np.asarray(_reference_meta['sample_parameters'])
_primitive = .5 * (_u * np.sqrt(1 + (_b*_u)**2) + np.arcsinh(_b*_u)/_b)
_original_arc_offsets = (_primitive - _primitive[4]) * _reference_meta['normalization_scale']
# A radius 1/k semicircle spans +/- pi/(2*k) around its midpoint.
# These offsets now define the reference semicircle only. Polynomial arc
# positions are allowed to differ to match visible straight-line distances.
ARC_HALF_WINDOW = math.pi / (2 * REFERENCE_CURVATURE)
ARC_OFFSETS = _original_arc_offsets / _original_arc_offsets[-1] * ARC_HALF_WINDOW
ARC_OFFSETS[0], ARC_OFFSETS[-1] = -ARC_HALF_WINDOW, ARC_HALF_WINDOW
ARC_OFFSETS[4] = 0.
# Preserve the original per-index perturbation amplitudes across all families.
REFERENCE_SPACINGS = local_spacings(_reference_points[['x','y']].to_numpy())
VISIBLE_INDICES = np.array([0, 1, 2, 3, 5, 6, 7, 8])
_reference_angles = ARC_OFFSETS * REFERENCE_CURVATURE
_circle_reference = np.column_stack((np.sin(_reference_angles),
                                     1-np.cos(_reference_angles))) / REFERENCE_CURVATURE
VISIBLE_CHORDS = np.linalg.norm(np.diff(_circle_reference[VISIBLE_INDICES], axis=0), axis=1)
TARGET_NEIGHBOR_DISTANCE = float(np.linalg.norm(_circle_reference[3]))
SPACING_TOLERANCE_PX = 1e-6
NEIGHBOR_TOLERANCE_PX = 0.51  # Geometric acceptance bound, not a perceptual threshold.



def analytic_curvature(u, degree):
    first = degree * np.asarray(u) ** (degree - 1)
    second = degree * (degree - 1) * np.asarray(u) ** (degree - 2)
    return second / (1 + first * first) ** 1.5


def _bisect(function, low, high):
    """Deterministic bracketed scalar root; no optimizer/runtime dependency."""
    if not function(low) <= 0 <= function(high):
        raise ValueError('Spacing solver could not bracket the requested distance.')
    for _ in range(65):
        middle = (low + high) / 2
        if function(middle) > 0:
            high = middle
        else:
            low = middle
    return (low + high) / 2


def _walk_chord(point_at, start, direction, distance):
    """Move outward along the original polynomial by a prescribed chord."""
    origin = point_at(start)
    def residual(step):
        return np.linalg.norm(point_at(start + direction*step) - origin) - distance
    upper = .01
    for _ in range(40):
        if residual(upper) >= 0:
            return start + direction * _bisect(residual, 0., upper)
        upper *= 1.5
    raise ValueError('Polynomial does not reach the requested sample distance.')


def polynomial_arc_offsets(parameters, degree, coefficient, scale):
    nodes, weights = np.polynomial.legendre.leggauss(64)
    a, b = parameters[:-1], parameters[1:]
    q = (a[:, None]+b[:, None])/2 + (b-a)[:, None]/2*nodes
    lengths = np.sum(weights*np.sqrt(1+(coefficient*degree*q**(degree-1))**2), axis=1)*(b-a)/2*scale
    cumulative = np.r_[0., np.cumsum(lengths)]
    return cumulative-cumulative[4]


def _actual_arc_offsets(family, parameters, scale):
    if family == 'circle':
        return parameters * scale
    return polynomial_arc_offsets(parameters, FAMILIES[family], 1., scale)


def sample_visible_chords(point_at, target):
    """Match visible intervals and balance the nearest pair about a target."""
    def nearest_pair(radius):
        return (_walk_chord(point_at, target, -1, radius),
                _walk_chord(point_at, target, 1, radius))
    def gap_error(radius):
        left, right = nearest_pair(radius)
        return np.linalg.norm(point_at(right)-point_at(left)) - VISIBLE_CHORDS[3]
    # Start below half the gap so even a straight line has a strict bracket.
    radius = _bisect(gap_error, .49*VISIBLE_CHORDS[3], 2*VISIBLE_CHORDS[3])
    parameters = np.empty(9)
    parameters[4] = target
    parameters[3], parameters[5] = nearest_pair(radius)
    for i in (2, 1, 0):
        parameters[i] = _walk_chord(point_at, parameters[i+1], -1, VISIBLE_CHORDS[i])
    for i in (6, 7, 8):
        parameters[i] = _walk_chord(point_at, parameters[i-1], 1, VISIBLE_CHORDS[i-2])
    return parameters


@lru_cache(maxsize=2)
def shared_window_center(level='parabola_reference'):
    """Keep all targets at the matched set's established common location."""
    windows = np.concatenate([_window(f, level)[0] for f in FAMILIES])
    return (windows.min(axis=0) + windows.max(axis=0)) / 2


@lru_cache(maxsize=12)
def _window(family, level):
    if family == 'circle':
        radius = 1 / CURVATURE_LEVELS[level]
        angles = ARC_OFFSETS / radius
        if not np.isclose(angles[-1]-angles[0], math.pi):
            raise ValueError('The matched circle window must span exactly a semicircle.')
        points = radius * np.column_stack((np.sin(angles), 1-np.cos(angles)))
        tangents = np.column_stack((np.cos(angles),np.sin(angles)))
        return points, tangents, angles, 0.0, radius
    n = FAMILIES[family]
    # Differentiate |n(n-1)u^(n-2)/(1+n^2 u^(2n-2))^(3/2)|.
    peak = 0.0 if n == 2 else ((n-2)/(n*n*(2*n-1))) ** (1/(2*n-2))
    peak_curvature = float(analytic_curvature(peak, n))
    scale = peak_curvature / CURVATURE_LEVELS[level]
    angle = math.atan(n*peak**(n-1))
    c, s = math.cos(angle), math.sin(angle)
    rotation = np.array([[c, s], [-s, c]])
    def point_at(u):
        return np.array([u-peak, u**n-peak**n]) @ rotation.T * scale
    # Match the central visible gap exactly while balancing the two neighbors'
    # distances from the hidden target. That common radius can differ slightly
    # between families; it is measured and bounded, not claimed to be identical.
    sampled_u = sample_visible_chords(point_at, peak)
    points = np.column_stack((sampled_u-peak, sampled_u**n-peak**n)) @ rotation.T * scale
    tangents = np.column_stack((np.ones(9), n*sampled_u**(n-1))) @ rotation.T
    tangents /= np.linalg.norm(tangents, axis=1)[:, None]
    return points, tangents, sampled_u, peak, scale


def generate_curvature_maximum_points(spec):
    family, level = spec['curve_family'], spec['curvature_level']
    points, tangents, parameters, peak, scale = _window(family, level)
    points, tangents = points.copy(), tangents.copy()
    # One translation for the whole matched set, selected from its joint bounds.
    # Shared translation leaves target location matched across all families.
    common_center = shared_window_center(level)
    points -= common_center
    sign = -1 if spec['force_reversed'] else 1
    points[:, 1] *= sign
    tangents[:, 1] *= sign
    # Shift the whole contour; target need not coincide with aperture center.
    points += [spec['target_shift_x_units'], spec['target_shift_y_units']]
    normals = np.column_stack((-tangents[:, 1], tangents[:, 0]))
    features = geometry_features(points, 4)
    curvature = sign * CURVATURE_LEVELS[level]
    arc_offsets = _actual_arc_offsets(family, parameters, scale)
    visible = points[VISIBLE_INDICES]
    chords_px = np.linalg.norm(np.diff(visible, axis=0), axis=1)*DISPLAY_SCALE
    neighbors_px = np.linalg.norm(points[[3,5]]-points[4], axis=1)*DISPLAY_SCALE
    chord_error = float(np.max(np.abs(chords_px - VISIBLE_CHORDS*DISPLAY_SCALE)))
    neighbor_error = float(np.max(np.abs(neighbors_px-TARGET_NEIGHBOR_DISTANCE*DISPLAY_SCALE)))
    if chord_error > SPACING_TOLERANCE_PX or neighbor_error > NEIGHBOR_TOLERANCE_PX:
        raise ValueError('Matched stimulus exceeds the specified spacing tolerances.')
    if not np.all(np.diff(parameters) > 0):
        raise ValueError('Matched sample positions must remain ordered on the curve.')
    meta = dict(spec)
    meta.update(
        movable_index=4, target_index=4, reversed=bool(spec['force_reversed']),
        curve_strength=1.0,
        sample_fractions=(arc_offsets/np.where(arc_offsets < 0, -arc_offsets[0], arc_offsets[-1])).tolist(),
        sample_parameters=parameters.tolist(), sample_arc_offsets=arc_offsets.tolist(),
        curvature_peak_parameter=float(peak), normalization_scale=float(scale),
        baseline_x_vals=points[:, 0].tolist(), baseline_y_vals=points[:, 1].tolist(),
        x_vals=points[:, 0].tolist(), y_vals=points[:, 1].tolist(),
        target_tangent_x=1., target_tangent_y=0., target_normal_x=0., target_normal_y=1.,
        analytic_normals=normals.tolist(), target_analytic_curvature=curvature,
        target_analytic_dimensionless_curvature=curvature*features['spacing'][4],
        target_analytic_curvature_px=curvature/DISPLAY_SCALE,
        target_arc_curvature_derivative=0.0,
        sample_analytic_curvatures=(np.full(9,curvature) if family=='circle' else
                                   sign*analytic_curvature(parameters, FAMILIES[family])/scale).tolist(),
        requested_display_scale=DISPLAY_SCALE,
        perturbation_reference_spacing_units=spec['reference_spacing_units'],
        perturbation_magnitude_basis='original_parabola_chord_spacing',
        perturbation_direction_basis='analytic_local_normal',
        target_location_rule=('constant_curvature_arc_midpoint' if family=='circle'
                              else 'absolute_curvature_maximum'),
        sample_parameter_kind=('circle_angle_radians' if family=='circle' else 'polynomial_parameter'),
        circle_radius_units=(scale if family=='circle' else ''),
        circle_radius_px=(scale*DISPLAY_SCALE if family=='circle' else ''),
        circle_arc_span_rad=(float(parameters[-1]-parameters[0]) if family=='circle' else ''),
        sampling_rule='matched_visible_chords_balanced_target_neighbors',
        reference_arc_half_window_px=ARC_HALF_WINDOW*DISPLAY_SCALE,
        reference_visible_chords_px=(VISIBLE_CHORDS*DISPLAY_SCALE).tolist(),
        baseline_visible_chords_px=chords_px.tolist(),
        visible_chord_max_error_px=chord_error,
        target_neighbor_distances_px=neighbors_px.tolist(),
        target_neighbor_reference_px=TARGET_NEIGHBOR_DISTANCE*DISPLAY_SCALE,
        target_neighbor_max_error_px=neighbor_error,
        baseline_spread_px=float(np.linalg.norm(visible[:,None,:]-visible[None,:,:], axis=2).max()*DISPLAY_SCALE),
        reference_stimulus='original_parabola_target4_standard',
        reference_curvature_px=REFERENCE_CURVATURE/DISPLAY_SCALE,
        shared_window_center_x=float(common_center[0]), shared_window_center_y=float(common_center[1]),
    )
    return pd.DataFrame({'index': range(9), 'x': points[:, 0], 'y': points[:, 1]}), meta


def build_curvature_maxima_trials(seed=63, small_fraction=8/60, counterbalance_group=0):
    if not 0 < small_fraction <= .5:
        raise ValueError('New curvature-maxima block requires 0 < small-fraction <= 0.5.')
    if counterbalance_group not in range(4):
        raise ValueError('counterbalance_group must be 0, 1, 2 or 3.')
    trials = []
    # Nuisance assignments match across ALL families and curvature levels.
    # Each +/- pair shares pose, start and target displacement.
    visible = [i for i in range(9) if i != 4]
    for family in FAMILIES:
        for repetition in (1, 2):
            level = 'parabola_reference'
            for condition in range(24):
                # One matched baseline and both signs per dot, at each start side.
                point_slot, treatment = divmod(condition, 3)
                baseline = treatment == 0
                point = visible[point_slot]
                pair_id = point_slot+1
                rng = random.Random(seed + 9100 + pair_id)
                pose = (point_slot + counterbalance_group) % 4
                rotation = (-15., 15.)[pose % 2]
                reflected = bool(pose // 2)
                start = 1 if point_slot % 2 == 0 else -1
                start *= 1 if repetition == 1 else -1
                start_size = rng.uniform(45., 85.)
                patterns = [] if baseline else [(point, -1 if treatment == 1 else 1)]
                stimulus = f'maxima_{family}_{level}'
                trials.append(dict(
                    design_version=DESIGN_VERSION, stimulus_set='curvature_maxima',
                    stimulus_id=stimulus, trial_uid=f'{stimulus}_r{repetition}_c{condition}',
                    experiment_block='identification', experiment='identification',
                    curve_family=family, function_type=family, target_index=4, movable_index=4,
                    curvature_level=level, matched_curvature_units=CURVATURE_LEVELS[level],
                    strength_level='standard', spacing_profile='semicircle_matched_visible_chords',
                    stimulus_seed=seed+9100+pair_id, rotation_deg=rotation,
                    force_reversed=reflected, repetition=repetition, rep=repetition,
                    condition_number=condition, baseline_repeat=((repetition-1)*8+point_slot+1 if baseline else 0),
                    condition_type='baseline' if baseline else 'single',
                    perturbation_regime='baseline' if baseline else 'small',
                    perturbations=patterns, perturb_fraction=0. if baseline else small_fraction,
                    perturb_magnitude_units=float(REFERENCE_SPACINGS[point])*small_fraction,
                    reference_spacing_units=float(REFERENCE_SPACINGS[point]),
                    initial_side=start, initial_offset_px=start*start_size,
                    target_shift_x_units=rng.uniform(-2., 2.),
                    target_shift_y_units=rng.uniform(-2., 2.),
                    matched_pose_id=pair_id, counterbalance_group=counterbalance_group,
                    pose_combination=pose,
                ))
    return trials


if __name__ == '__main__':
    trials = build_curvature_maxima_trials()
    print(f'{len(trials)} trials: 5 families x (32 single + 16 matched baseline)')
    print(f'Reference peak curvature: {REFERENCE_CURVATURE/DISPLAY_SCALE:.6f} /px')
    print('Matched consecutive visible chords (px):', VISIBLE_CHORDS * DISPLAY_SCALE)
    for family in FAMILIES:
        _, meta = generate_curvature_maximum_points(next(t for t in trials if t['curve_family']==family))
        print(f"{family}: neighbor distances={meta['target_neighbor_distances_px']}, "
              f"max chord error={meta['visible_chord_max_error_px']:.3g}px, "
              f"spread={meta['baseline_spread_px']:.3f}px")
