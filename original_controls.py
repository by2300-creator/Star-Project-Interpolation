"""Spacing-controlled zero-curvature originals for combined mode only.

Legacy/practice generation remains in function.py. Preserve its polynomial
coefficient and similarity scale, then change samples without endpoint refitting.
"""
from functools import lru_cache
import numpy as np
import pandas as pd
from function import generate_function_points
from curvature_maxima import (
    DESIGN_VERSION, DISPLAY_SCALE, VISIBLE_INDICES, VISIBLE_CHORDS,
    TARGET_NEIGHBOR_DISTANCE, SPACING_TOLERANCE_PX, REFERENCE_CURVATURE,
    sample_visible_chords, polynomial_arc_offsets, shared_window_center,
)

ORIGINAL_FAMILIES = {'line': 1, 'cubic': 3, 'quartic': 4, 'quintic': 5}
GEOMETRY_PROTOCOL = 'spacing_controlled_original'


def control_original_trials(trials, matched_trials):
    """Reuse repetition-1 contexts; retain 16 singles and ONE baseline/family.

    The sole baseline uses context 1. It must not be treated as a matched
    baseline for contexts 2..8. Both signs of each point share their context.
    """
    references = {(t['matched_pose_id'], t['condition_type'],
                   t['perturbations'][0][1] if t['perturbations'] else 0): t
                  for t in matched_trials
                  if t['curve_family']=='parabola' and t['repetition']==1}
    fields = ('rotation_deg', 'force_reversed', 'initial_side', 'initial_offset_px',
              'target_shift_x_units', 'target_shift_y_units', 'matched_pose_id',
              'counterbalance_group', 'pose_combination', 'stimulus_seed',
              'reference_spacing_units', 'perturb_magnitude_units')
    controlled = []
    for old in trials:
        if old['curve_family'] not in ORIGINAL_FAMILIES or old['target_index'] != 4:
            raise ValueError('Controlled originals require the four retained midpoint families.')
        spec = dict(old)
        point, sign = old['perturbations'][0] if old['perturbations'] else (0, 0)
        context = list(VISIBLE_INDICES).index(point)+1
        reference = references[(context, old['condition_type'], sign)]
        spec.update({field: reference[field] for field in fields})
        previous_id = spec['stimulus_id']
        spec['stimulus_id'] = 'controlled_original_' + previous_id
        spec['trial_uid'] = spec['trial_uid'].replace(previous_id, spec['stimulus_id'], 1)
        spec.update(design_version=DESIGN_VERSION, geometry_protocol=GEOMETRY_PROTOCOL,
                    spacing_profile='semicircle_matched_visible_chords',
                    curvature_level='original_zero_curvature', matched_curvature_units=0.,
                    baseline_repeat=1 if not old['perturbations'] else 0,
                    baseline_context_scope='context_1_only', matched_reference_repetition=1)
        controlled.append(spec)
    return controlled


@lru_cache(maxsize=4)
def original_window(family):
    degree = ORIGINAL_FAMILIES[family]
    _, legacy = generate_function_points(family, target_index=4, force_reversed=False)
    coefficient, scale = legacy['curve_strength'], legacy['normalization_scale']
    def point_at(u):
        return scale*np.array([u, coefficient*u**degree])
    parameters = sample_visible_chords(point_at, 0.)
    points = np.array([point_at(u) for u in parameters])
    first = coefficient*degree*parameters**(degree-1)
    tangents = np.column_stack((np.ones(9), first))
    tangents /= np.linalg.norm(tangents, axis=1)[:,None]
    second = (np.zeros(9) if degree==1 else
              coefficient*degree*(degree-1)*parameters**(degree-2))
    curvatures = second/(1+first*first)**1.5/scale
    arc = polynomial_arc_offsets(parameters, degree, coefficient, scale)
    return points, tangents, parameters, coefficient, scale, curvatures, arc


def generate_controlled_original_points(spec):
    family = spec['curve_family']
    raw, tangents, parameters, coefficient, scale, curvatures, arc = original_window(family)
    points, tangents = raw.copy(), tangents.copy()
    center = shared_window_center()
    points -= center
    sign = -1 if spec['force_reversed'] else 1
    points[:,1] *= sign
    tangents[:,1] *= sign
    points += [spec['target_shift_x_units'], spec['target_shift_y_units']]
    normals = np.column_stack((-tangents[:,1], tangents[:,0]))
    visible = points[VISIBLE_INDICES]
    chords = np.linalg.norm(np.diff(visible,axis=0),axis=1)*DISPLAY_SCALE
    neighbors = np.linalg.norm(points[[3,5]]-points[4],axis=1)*DISPLAY_SCALE
    error = float(np.max(abs(chords-VISIBLE_CHORDS*DISPLAY_SCALE)))
    if error > SPACING_TOLERANCE_PX or abs(neighbors[0]-neighbors[1]) > SPACING_TOLERANCE_PX:
        raise ValueError('Original stimulus violates visible-spacing or neighbor-balance control.')
    if not np.all(np.diff(parameters)>0):
        raise ValueError('Original samples must remain ordered along the curve.')
    meta = dict(spec)
    meta.update(
        movable_index=4, target_index=4, reversed=bool(spec['force_reversed']),
        curve_strength=coefficient, normalization_scale=scale,
        sample_parameters=parameters.tolist(), sample_arc_offsets=arc.tolist(),
        sample_fractions=(arc/np.where(arc<0,-arc[0],arc[-1])).tolist(),
        sample_parameter_kind='polynomial_parameter', target_parameter=0.,
        baseline_x_vals=points[:,0].tolist(), baseline_y_vals=points[:,1].tolist(),
        x_vals=points[:,0].tolist(), y_vals=points[:,1].tolist(),
        target_tangent_x=1., target_tangent_y=0., target_normal_x=0., target_normal_y=1.,
        analytic_normals=normals.tolist(), target_analytic_curvature=0.,
        target_analytic_curvature_px=0., target_analytic_dimensionless_curvature=0.,
        # d(kappa)/ds at u=0 is nonzero for the cubic inflection.
        target_arc_curvature_derivative=sign*6*coefficient/scale**2 if family=='cubic' else 0.,
        sample_analytic_curvatures=(sign*curvatures).tolist(),
        requested_display_scale=DISPLAY_SCALE,
        perturbation_reference_spacing_units=spec['reference_spacing_units'],
        perturbation_magnitude_basis='original_parabola_chord_spacing',
        perturbation_direction_basis='analytic_local_normal',
        target_location_rule='original_zero_curvature_midpoint',
        sampling_rule='matched_visible_chords_balanced_target_neighbors',
        reference_visible_chords_px=(VISIBLE_CHORDS*DISPLAY_SCALE).tolist(),
        baseline_visible_chords_px=chords.tolist(), visible_chord_max_error_px=error,
        target_neighbor_distances_px=neighbors.tolist(),
        target_neighbor_reference_px=TARGET_NEIGHBOR_DISTANCE*DISPLAY_SCALE,
        target_neighbor_max_error_px=float(np.max(abs(neighbors-TARGET_NEIGHBOR_DISTANCE*DISPLAY_SCALE))),
        baseline_spread_px=float(np.linalg.norm(visible[:,None]-visible[None,:],axis=2).max()*DISPLAY_SCALE),
        reference_stimulus='original_parabola_target4_standard',
        reference_curvature_px=REFERENCE_CURVATURE/DISPLAY_SCALE,
        shared_window_center_x=float(center[0]), shared_window_center_y=float(center[1]),
    )
    return pd.DataFrame({'index':range(9), 'x':points[:,0], 'y':points[:,1]}), meta
