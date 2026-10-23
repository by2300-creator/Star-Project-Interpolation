"""Trial-level recording with analysis-ready baseline and geometry fields."""

from __future__ import annotations

import json
import math
import os
import tempfile

import numpy as np
import pandas as pd

from geometry import as_points, geometry_features, pointwise_curvatures, signed_menger_curvature


def curvature_from_3pts(x1, y1, x2, y2, x3, y3, eps=1e-12):
    """Compatibility wrapper around the shared signed Menger curvature."""
    value = signed_menger_curvature((x1, y1), (x2, y2), (x3, y3))
    return 0.0 if abs(value) < eps else float(value)


def compute_pointwise_curvatures(xs, ys):
    return list(pointwise_curvatures(as_points(xs, ys)))


def _json_list(value):
    if value in (None, ""):
        return []
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return list(value)


def _to_local(final_x, final_y, correct_x, correct_y, correct_local, scale, rotation_deg):
    """Invert the display rotation using the known correct point as the origin."""
    theta = math.radians(float(rotation_deg))
    cosine, sine = math.cos(theta), math.sin(theta)
    dx = float(final_x) - float(correct_x)
    dy = float(final_y) - float(correct_y)
    local_dx = (dx * cosine + dy * sine) / float(scale)
    local_dy = (-dx * sine + dy * cosine) / float(scale)
    return float(correct_local[0] + local_dx), float(correct_local[1] + local_dy)


class DataRecorder:
    def __init__(
        self,
        records_path="pixel_based_adjustment_data.csv",
        presses_path="button_press_sequence.csv",
    ):
        self.records = []
        self.events = []
        self.records_path = records_path
        self.presses_path = presses_path
        if os.path.abspath(records_path) == os.path.abspath(presses_path):
            raise ValueError("Trial and press CSV paths must differ.")
        for path in (records_path, presses_path):
            if os.path.exists(path):
                raise FileExistsError(f"Refusing to overwrite existing participant data: {path}")
        self.save()

    def record(self, trial, final_pos, press_sequence, meta, final_record, pts_df):
        """Record a completed trial and synchronously persist BOTH CSVs.

        Returns only after both files have been flushed and replaced on disk.
        The caller must finish this call before starting the next trial.
        """
        target = int(meta["movable_index"])
        displayed_points = as_points(pts_df["x"].to_numpy(), pts_df["y"].to_numpy())
        baseline_points = as_points(
            meta.get("baseline_x_vals", pts_df["x"].tolist()),
            meta.get("baseline_y_vals", pts_df["y"].tolist()),
        )
        baseline_geometry = geometry_features(baseline_points, target)
        displayed_geometry = geometry_features(displayed_points, target)

        reset_positions = [
            index for index, (button, _) in enumerate(press_sequence, start=1) if button == "reset"
        ]
        scale = float(meta.get("display_scale_px_per_unit", meta.get("px_per_unit", 1.0)))
        perturb_actual_units = [float(value) for value in _json_list(meta.get("perturb_actual_units"))]
        perturb_actual_px = [float(value * scale) for value in perturb_actual_units]

        final_x = float(final_record.get("final_x", final_pos[0]))
        final_y = float(final_record.get("final_y", final_pos[1]))
        correct_x_px = float(final_record.get("correct_x_px", meta.get("correct_x_px")))
        correct_y_px = float(final_record.get("correct_y_px", meta.get("correct_y_px")))
        correct_local = baseline_points[target]
        player_local_x, player_local_y = _to_local(
            final_x,
            final_y,
            correct_x_px,
            correct_y_px,
            correct_local,
            scale,
            meta.get("rotation_deg", 0.0),
        )

        player_curvature = ""
        if 0 < target < len(baseline_points) - 1:
            player_curvature = signed_menger_curvature(
                baseline_points[target - 1],
                (player_local_x, player_local_y),
                baseline_points[target + 1],
            )

        response_normal_px = float(
            final_record.get("response_normal_px", final_record.get("pixel_distance_signed", 0.0))
        )
        response_normal_units = float(
            final_record.get("response_normal_units", response_normal_px / scale)
        )

        rec = {
            "design_version": meta.get("design_version", "legacy"),
            "trial": int(trial),
            "planned_order": meta.get("planned_order", trial),
            "trial_uid": meta.get("trial_uid", ""),
            "stimulus_id": meta.get("stimulus_id", ""),
            "participant_id": meta.get("participant_id", ""),
            "session_id": meta.get("session_id", ""),
            "experiment": meta.get("experiment", meta.get("experiment_block", "")),
            "experiment_block": meta.get("experiment_block", ""),
            "repetition": meta.get("repetition", meta.get("rep", "")),
            "condition_number": meta.get("condition_number", ""),
            "condition_type": meta.get("condition_type", ""),
            "perturbation_regime": meta.get("perturbation_regime", ""),
            "function_type": meta.get("function_type", ""),
            "curve_family": meta.get("curve_family", meta.get("function_type", "")),
            "curve_strength": meta.get("curve_strength", ""),
            "strength_level": meta.get("strength_level", ""),
            "spacing_profile": meta.get("spacing_profile", ""),
            "sample_fractions": json.dumps(meta.get("sample_fractions", [])),
            "target_index": target,
            "movable_index": target,
            "random_seed": meta.get("random_seed", ""),
            "stimulus_seed": meta.get("stimulus_seed", ""),
            "rotation_deg": meta.get("rotation_deg", ""),
            "reversed": meta.get("reversed", False),
            "initial_side": meta.get("initial_side", ""),
            "initial_offset_px": meta.get("initial_offset_px", ""),
            "actual_initial_offset_px": meta.get("actual_initial_offset_px", ""),
            "initial_movable_x_math": meta.get("initial_movable_x_math", ""),
            "initial_movable_y_math": meta.get("initial_movable_y_math", ""),
            "initial_movable_x_px": meta.get("initial_movable_x_px", ""),
            "initial_movable_y_px": meta.get("initial_movable_y_px", ""),
            "total_moves": final_record.get("total_moves", ""),
            "reaction_time_ms": final_record.get("reaction_time_ms", ""),
            "r_count": len(reset_positions),
            "final_x_px": final_x,
            "final_y_px": final_y,
            "correct_x_px": correct_x_px,
            "correct_y_px": correct_y_px,
            "ref_up_x_px": final_record.get("ref_up_x_px", ""),
            "ref_up_y_px": final_record.get("ref_up_y_px", ""),
            "ref_down_x_px": final_record.get("ref_down_x_px", ""),
            "ref_down_y_px": final_record.get("ref_down_y_px", ""),
            "player_final_local_x": player_local_x,
            "player_final_local_y": player_local_y,
            "response_normal_px": response_normal_px,
            "response_normal_units": response_normal_units,
            "response_abs_px": abs(response_normal_px),
            "pixel_distance": response_normal_px,
            "pixel_distance_signed": response_normal_px,
            "pixel_distance_abs": abs(response_normal_px),
            "display_scale_px_per_unit": scale,
            "px_per_unit": scale,
            "perturb_type": meta.get("perturb_type", ""),
            "perturbation_pattern": meta.get("perturbation_pattern", ""),
            "perturb_indices": meta.get("perturb_indices", "[]"),
            "perturb_signs": meta.get("perturb_signs", "[]"),
            "perturb_count": meta.get("perturb_count", 0),
            "perturb_fraction": meta.get("perturb_fraction", 0.0),
            "perturb_actual_units": json.dumps(perturb_actual_units),
            "perturb_actual_px": json.dumps(perturb_actual_px),
            "perturb_index": meta.get("perturb_index", ""),
            "perturb_sign": meta.get("perturb_sign", ""),
            "perturb_units": meta.get("perturb_units", ""),
            "perturb_pixels": meta.get("perturb_pixels", ""),
            "perturb_direction_relation": meta.get("perturb_direction_relation", ""),
            "geometry_disruption_rms": meta.get("geometry_disruption_rms", 0.0),
            "geometry_disruption_max": meta.get("geometry_disruption_max", 0.0),
            "turning_disruption_rms": meta.get("turning_disruption_rms", 0.0),
            "target_window_disruption_rms": meta.get("target_window_disruption_rms", 0.0),
            "delta_local_curvature_variance": meta.get("delta_local_curvature_variance", 0.0),
            "delta_local_curvature_inconsistency": meta.get(
                "delta_local_curvature_inconsistency", 0.0
            ),
            "target_normal_x": meta.get("target_normal_x", ""),
            "target_normal_y": meta.get("target_normal_y", ""),
            "target_dkappa_ds_baseline": baseline_geometry["target_curvature_derivative"],
            "local_dkappa_ds_rms_baseline": baseline_geometry["local_curvature_derivative_rms"],
            "geometry_estimator": "three_point_curvature_chord_arc_gradient",
            "num_points": len(pts_df),
            "target_curvature_baseline": baseline_geometry["target_curvature"],
            "target_dimensionless_curvature_baseline": baseline_geometry[
                "target_dimensionless_curvature"
            ],
            "target_analytic_curvature_baseline": meta.get("target_analytic_curvature", ""),
            "target_analytic_dimensionless_curvature_baseline": meta.get(
                "target_analytic_dimensionless_curvature", ""
            ),
            "baseline_local_curvature_mean": baseline_geometry["local_curvature_mean"],
            "baseline_local_abs_curvature_mean": baseline_geometry["local_abs_curvature_mean"],
            "baseline_local_curvature_variance": baseline_geometry["local_curvature_variance"],
            "baseline_local_curvature_inconsistency": baseline_geometry[
                "local_curvature_inconsistency"
            ],
            "baseline_local_turning_variance": baseline_geometry["local_turning_variance"],
            "baseline_local_spacing_mean": baseline_geometry["local_spacing_mean"],
            "baseline_local_spacing_cv": baseline_geometry["local_spacing_cv"],
            "displayed_local_curvature_variance": displayed_geometry[
                "local_curvature_variance"
            ],
            "displayed_local_curvature_inconsistency": displayed_geometry[
                "local_curvature_inconsistency"
            ],
            "movable_kappa_correct_math": baseline_geometry["target_curvature"],
            "movable_kappa_correct_px": baseline_geometry["target_curvature"] / scale,
            "movable_kappa_player_final_math": player_curvature,
            "movable_kappa_player_final_px": (
                "" if player_curvature == "" else float(player_curvature) / scale
            ),
            "A": meta.get("A", ""),
            "slope": meta.get("slope", ""),
            "k": meta.get("k", ""),
        }

        for index, row in pts_df.iterrows():
            point_index = int(row["index"])
            rec[f"x{point_index}_baseline_math"] = float(baseline_points[point_index, 0])
            rec[f"y{point_index}_baseline_math"] = float(baseline_points[point_index, 1])
            rec[f"x{point_index}_math"] = float(displayed_points[point_index, 0])
            rec[f"y{point_index}_math"] = float(displayed_points[point_index, 1])
            screen_x = row.get("screen_x", "")
            screen_y = row.get("screen_y", "")
            rec[f"x{point_index}_px"] = (
                "" if screen_x in (None, "") or pd.isna(screen_x) else float(screen_x)
            )
            rec[f"y{point_index}_px"] = (
                "" if screen_y in (None, "") or pd.isna(screen_y) else float(screen_y)
            )
            rec[f"spacing{point_index}_baseline"] = float(baseline_geometry["spacing"][point_index])
            rec[f"spacing{point_index}_displayed"] = float(displayed_geometry["spacing"][point_index])
            rec[f"kappa{point_index}_baseline_math"] = float(
                baseline_geometry["curvature"][point_index]
            )
            rec[f"kappa{point_index}_math"] = float(displayed_geometry["curvature"][point_index])
            rec[f"K{point_index}_baseline"] = float(
                baseline_geometry["dimensionless_curvature"][point_index]
            )
            rec[f"K{point_index}_displayed"] = float(
                displayed_geometry["dimensionless_curvature"][point_index]
            )
            rec[f"turn{point_index}_baseline"] = float(
                baseline_geometry["turning_angle"][point_index]
            )
            rec[f"turn{point_index}_displayed"] = float(
                displayed_geometry["turning_angle"][point_index]
            )
            rec[f"distance{point_index}_from_target"] = float(
                baseline_geometry["signed_arc_distance"][point_index]
            )
            rec[f"kappa{point_index}_px"] = float(
                displayed_geometry["curvature"][point_index] / scale
            )

        # Explicit design fields keep new maxima trials separable from legacy pilots.
        for field in ('stimulus_set', 'curvature_level', 'matched_curvature_units',
                      'target_location_rule', 'curvature_peak_parameter', 'normalization_scale',
                      'target_analytic_curvature_px', 'target_arc_curvature_derivative',
                      'requested_display_scale', 'perturbation_reference_spacing_units',
                      'perturbation_magnitude_basis', 'perturbation_direction_basis',
                      'target_shift_x_units', 'target_shift_y_units', 'matched_pose_id',
                      'baseline_repeat', 'initial_step_px', 'input_version',
                      'control_up_normal_sign', 'response_sign_convention',
                      'practice_protocol_version', 'practice_feedback_received',
                      'practice_good_fraction', 'practice_moderate_fraction', 'practice_feedback_duration_ms',
                      'order_seed', 'counterbalance_group', 'pose_combination',
                      'reference_stimulus', 'reference_curvature_px',
                      'sample_parameter_kind', 'circle_radius_units', 'circle_radius_px',
                      'circle_arc_span_rad', 'matched_arc_half_window_px',
                      'sampling_rule', 'reference_arc_half_window_px', 'screen_size_px',
                      'visible_chord_max_error_px', 'target_neighbor_reference_px',
                      'target_neighbor_max_error_px', 'baseline_spread_px',
                      'geometry_protocol', 'baseline_context_scope', 'matched_reference_repetition', 'target_parameter',
                      'shared_window_center_x', 'shared_window_center_y'):
            rec[field] = meta.get(field, '')
        for field in ('fine_moves', 'submission_step_px', 'blocked_submissions', 'response_screen_up_px'):
            rec[field] = final_record.get(field, '')
        for field in ('sample_arc_offsets', 'sample_parameters', 'sample_analytic_curvatures', 'step_sizes_px',
                      'reference_visible_chords_px', 'baseline_visible_chords_px', 'target_neighbor_distances_px'):
            rec[field] = json.dumps(meta.get(field, []))
        self.records.append(rec)

        press_row = {
            "stimulus_set": meta.get('stimulus_set', 'original'),
            "curvature_level": meta.get('curvature_level', ''),
            "repetition": meta.get('repetition', ''),
            "design_version": meta.get("design_version", "legacy"),
            "trial": int(trial),
            "trial_uid": meta.get("trial_uid", ""),
            "stimulus_id": meta.get("stimulus_id", ""),
        }
        for index, (button, reversal_count) in enumerate(press_sequence, start=1):
            press_row[f"press_{index}"] = f"{button}_{reversal_count}"
        press_row["r_presses"] = ";".join(str(value) for value in reset_positions)
        self.events.append(press_row)
        self.save()

    def save(self):
        for path in (self.records_path, self.presses_path):
            directory = os.path.dirname(os.path.abspath(path))
            os.makedirs(directory, exist_ok=True)
        for rows, path, columns in (
            (self.records, self.records_path, ["trial", "trial_uid", "participant_id", "response_normal_px"]),
            (self.events, self.presses_path, ["trial", "trial_uid", "stimulus_id", "r_presses"]),
        ):
            # Replace each file atomically: interruption cannot truncate an existing CSV.
            frame = pd.DataFrame(rows) if rows else pd.DataFrame(columns=columns)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                        dir=os.path.dirname(os.path.abspath(path)), delete=False) as handle:
                    temporary = handle.name
                    frame.to_csv(handle, index=False)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, path)
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)
