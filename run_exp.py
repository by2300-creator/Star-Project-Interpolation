"""Run the geometry-conditioned interpolation experiment.

Use ``--dry-run`` to generate and validate a complete trial manifest without
opening the display.  Identification and segmentation are deliberately
separate blocks because they test different response regimes.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from experiment_design import (
    DEFAULT_SEGMENTATION_FRACTIONS,
    DEFAULT_SMALL_FRACTION,
    DEFAULT_TARGETS,
    build_identification_trials,
    build_practice_trials,
    build_segmentation_trials,
    summarize_trials,
)
from function import generate_function_points
from curvature_maxima import build_curvature_maxima_trials, generate_curvature_maximum_points
from original_controls import control_original_trials, generate_controlled_original_points, GEOMETRY_PROTOCOL
from perturb import apply_normal_perturbations, define_rotation
from practice_feedback import PRACTICE_PROTOCOL_VERSION, GOOD_FRACTION, MODERATE_FRACTION, FEEDBACK_DURATION_MS


FPS = 60
SCREEN_UNITS = "px"
SCREEN_VALUE = 1100
SCREEN_PPI = None
DEFAULT_PPI = 96
# PyCharm: True = 68 spacing-controlled original + 240 matched trials (308 recorded).
# False = original 108-condition design repeated twice.
ENABLE_CURVATURE_MAXIMA = True
PARTICIPANT_ID = "P010"  # Set a unique ID, e.g. P001, P002, ... for each participant.
SESSION_ID = "1"
COUNTERBALANCE_GROUP = None  # None: infer from numeric ID; otherwise choose 0..3.
FINE_ADJUSTMENT_DEFAULT = False  # Coarse start; fine adjustment is required to submit.


def _comma_ints(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected comma-separated integer indices.") from exc


def _comma_floats(value: str) -> tuple[float, ...]:
    try:
        return tuple(float(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected comma-separated numeric values.") from exc


def _comma_strings(value: str) -> tuple[str, ...]:
    values = tuple(item.strip() for item in value.split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("At least one value is required.")
    return values


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", choices=("identification", "segmentation"), default="identification")
    parser.add_argument("--seed", type=int, default=63)
    parser.add_argument("--order-seed", type=int, default=None, help="Override participant/session-specific ordering.")
    parser.add_argument("--counterbalance-group", type=int, choices=range(4), default=COUNTERBALANCE_GROUP)
    parser.add_argument("--curvature-maxima", action=argparse.BooleanOptionalAction,
                        default=ENABLE_CURVATURE_MAXIMA,
                        help="Add the matched maxima block instead of repetition; --no-curvature-maxima restores repeats.")
    parser.add_argument("--repetitions", type=int, default=None,
                        help="Legacy/segmentation repetitions (default: 2). Requires --no-curvature-maxima for identification.")
    parser.add_argument(
        "--targets",
        type=_comma_ints,
        default=None,
        help="Comma-separated hidden-point indices (default: 3,4 for identification; 4 for segmentation).",
    )
    parser.add_argument("--strength-levels", type=_comma_strings, default=("standard",))
    parser.add_argument(
        "--spacing-profile",
        choices=("fixed_irregular", "equal_arc", "jittered_arc"),
        default="fixed_irregular",
    )
    parser.add_argument("--small-fraction", type=float, default=DEFAULT_SMALL_FRACTION)
    parser.add_argument(
        "--segmentation-fractions",
        type=_comma_floats,
        default=DEFAULT_SEGMENTATION_FRACTIONS,
    )
    parser.add_argument("--participant-id", default=PARTICIPANT_ID)
    parser.add_argument("--session-id", default=SESSION_ID)
    parser.add_argument("--partition-count", type=int, default=1)
    parser.add_argument("--partition-index", type=int, default=1)
    parser.add_argument("--output-prefix", default=None)
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-tutorial", action="store_true")
    args = parser.parse_args(argv)
    digest = hashlib.sha256(f"{args.seed}|{args.participant_id}|{args.session_id}".encode()).digest()
    if args.order_seed is None:
        args.order_seed = int.from_bytes(digest[:4], 'big')
    if args.counterbalance_group is None:
        number = re.search(r'(\d+)$', args.participant_id)
        args.counterbalance_group = ((int(number.group()) - 1) % 4 if number
                                    else int.from_bytes(hashlib.sha256(args.participant_id.encode()).digest()[:4], 'big') % 4)
    return args


def cm_to_px(cm, ppi):
    return int(round((float(cm) / 2.54) * float(ppi)))


def compute_screen_px():
    if SCREEN_UNITS == "px":
        return int(round(SCREEN_VALUE))
    if SCREEN_UNITS == "cm":
        return cm_to_px(SCREEN_VALUE, SCREEN_PPI or DEFAULT_PPI)
    raise ValueError("SCREEN_UNITS must be 'px' or 'cm'.")


def build_trials(args):
    args.targets = args.targets or (DEFAULT_TARGETS if args.block == "identification" else (4,))
    maxima_enabled = args.block == 'identification' and args.curvature_maxima
    if maxima_enabled and (args.repetitions is not None or tuple(args.targets) != (3, 4)
                           or tuple(args.strength_levels) != ('standard',)
                           or args.spacing_profile != 'fixed_irregular'):
        raise ValueError('Combined design requires default targets/strength/spacing and no --repetitions. '
                         'Use --no-curvature-maxima for customized legacy designs.')
    common = {
        "seed": args.seed,
        "repetitions": 1 if maxima_enabled else (2 if args.repetitions is None else args.repetitions),
        "target_indices": args.targets,
        "strength_levels": args.strength_levels,
        "spacing_profile": args.spacing_profile,
    }
    if args.block == "identification":
        trials = build_identification_trials(
            **common,
            small_fraction=args.small_fraction,
        )
    else:
        trials = build_segmentation_trials(
            **common,
            magnitude_fractions=args.segmentation_fractions,
        )

    for trial in trials:
        trial['stimulus_set'] = 'original'
    if maxima_enabled:
        # Replace original parabola and circle midpoint conditions with full
        # matched protocols. Retain all other midpoint conditions and repeats.
        trials = [t for t in trials if t['target_index']==4 and t['curve_family'] not in ('parabola','circle')]
        matched = build_curvature_maxima_trials(args.seed, args.small_fraction, args.counterbalance_group)
        trials = control_original_trials(trials, matched) + matched

    if args.partition_count < 1:
        raise ValueError("partition-count must be at least one.")
    if not 1 <= args.partition_index <= args.partition_count:
        raise ValueError("partition-index must lie between 1 and partition-count.")
    if args.partition_count > 1:
        family_order = {name: index for index, name in enumerate(
            ("line", "parabola", "cubic", "quartic", "quintic", "circle")
        )}
        target_order = {value: index for index, value in enumerate(args.targets)}
        level_order = {value: index for index, value in enumerate(args.strength_levels)}
        def partition_key(trial):
            return (trial['stimulus_id'], trial['repetition'] if trial['stimulus_set']=='curvature_maxima' else 0)
        unique_bases = {partition_key(trial): trial for trial in trials}
        allowed = set()
        for stimulus_id, base in unique_bases.items():
            slot = (
                family_order[base["curve_family"]]
                + target_order[base["target_index"]]
                + level_order.get(base["strength_level"], 0)
                + (base['repetition']-1 if base['stimulus_set']=='curvature_maxima' else 0)
            ) % args.partition_count
            if slot == args.partition_index - 1:
                allowed.add(stimulus_id)
        trials = [trial for trial in trials if partition_key(trial) in allowed]

    random.Random(args.order_seed + 404 + args.partition_index).shuffle(trials)
    for order, trial in enumerate(trials, start=1):
        trial["display_margin_fraction"] = (args.small_fraction if args.block == "identification"
                                              else max(args.segmentation_fractions))
        trial["planned_order"] = order
        trial["order_seed"] = args.order_seed
        trial["counterbalance_group"] = args.counterbalance_group
        trial["participant_id"] = args.participant_id
        trial["session_id"] = args.session_id
        trial["partition_count"] = args.partition_count
        trial["partition_index"] = args.partition_index
    if not trials:
        raise ValueError("This partition contains no trials. Reduce partition-count.")
    return trials


def materialize_trial(trial_spec: dict, global_seed: int):
    if trial_spec.get('stimulus_set') == 'curvature_maxima':
        points, meta = generate_curvature_maximum_points(trial_spec)
    elif trial_spec.get('geometry_protocol') == GEOMETRY_PROTOCOL:
        points, meta = generate_controlled_original_points(trial_spec)
    else:
        points, meta = generate_function_points(
            function_type=trial_spec["curve_family"],
            force_reversed=trial_spec["force_reversed"],
            target_index=trial_spec["target_index"],
            strength_level=trial_spec["strength_level"],
            spacing_profile=trial_spec["spacing_profile"],
            stimulus_seed=trial_spec["stimulus_seed"],
            curve_strength=trial_spec.get("curve_strength"),
            practice_flattening=trial_spec.get("practice_flattening", 1.0),
        )
    meta.update({key: value for key, value in trial_spec.items() if key != "perturbations"})
    meta["random_seed"] = int(global_seed)
    define_rotation(meta, trial_spec["rotation_deg"])
    points, meta = apply_normal_perturbations(
        points,
        meta,
        perturbations=trial_spec["perturbations"],
        magnitude_fraction=trial_spec["perturb_fraction"],
        regime=trial_spec["perturbation_regime"],
        condition_type=trial_spec["condition_type"],
        absolute_magnitude_units=trial_spec.get('perturb_magnitude_units'),
    )
    return points, meta


def manifest_rows(trials, seed):
    rows = []
    for trial in trials:
        points, meta = materialize_trial(trial, seed)
        row = {
            key: value
            for key, value in meta.items()
            if not isinstance(value, (list, tuple, dict, np.ndarray))
        }
        row["perturbations"] = json.dumps(trial["perturbations"])
        row["sample_fractions"] = json.dumps(meta.get("sample_fractions", []))
        for field in ('sample_arc_offsets', 'sample_parameters', 'reference_visible_chords_px',
                      'baseline_visible_chords_px', 'target_neighbor_distances_px'):
            row[field] = json.dumps(meta.get(field, []))
        row['screen_size_px'] = compute_screen_px()
        for _, point in points.iterrows():
            index = int(point["index"])
            row[f"x{index}_displayed"] = float(point["x"])
            row[f"y{index}_displayed"] = float(point["y"])
            row[f"x{index}_baseline"] = float(meta["baseline_x_vals"][index])
            row[f"y{index}_baseline"] = float(meta["baseline_y_vals"][index])
        rows.append(row)
    return rows


def save_manifest(trials, seed, path):
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame(manifest_rows(trials, seed)).to_csv(path, index=False)
    return path


def show_screen(pygame, screen, text, subtext=None, wait_for_key=True):
    screen.fill((30, 30, 30))
    width, height = screen.get_size()
    main_text = pygame.font.SysFont(None, 36).render(text, True, (255, 255, 255))
    screen.blit(main_text, (width // 2 - main_text.get_width() // 2, height // 2 - 40))
    if subtext:
        secondary = pygame.font.SysFont(None, 24).render(subtext, True, (200, 200, 200))
        screen.blit(secondary, (width // 2 - secondary.get_width() // 2, height // 2 + 40))
    pygame.display.flip()
    clock = pygame.time.Clock()
    while wait_for_key:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                continue
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return
        clock.tick(60)


def main(argv=None):
    args = parse_args(argv)
    random.seed(args.seed)
    np.random.seed(args.seed)
    trials = build_trials(args)
    summary = summarize_trials(trials)
    print(json.dumps(summary, indent=2, sort_keys=True))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in args.participant_id)
    safe_session = "".join(c if c.isalnum() or c in "-_" else "_" for c in args.session_id)
    default_prefix = Path(__file__).resolve().parent / "data" / f"{safe_id}_{args.block}_s{safe_session}_{stamp}"
    output_prefix = str(Path(args.output_prefix or default_prefix).resolve())
    if args.dry_run or args.manifest:
        manifest_path = args.manifest or f"{output_prefix}_manifest.csv"
        if os.path.exists(manifest_path):
            raise FileExistsError(f"Manifest already exists: {manifest_path}")
        print(f"Trial manifest: {save_manifest(trials, args.seed, manifest_path)}")
    if args.dry_run:
        return 0

    try:
        import pygame
    except ImportError as exc:
        raise RuntimeError(
            "pygame is required for the interactive task. The design itself can be checked with --dry-run."
        ) from exc

    from canvas import Canvas
    from recorder import DataRecorder

    recorder = DataRecorder(
        records_path=f"{output_prefix}_trials.csv",
        presses_path=f"{output_prefix}_presses.csv",
    )
    print(f"Trial responses: {recorder.records_path}", flush=True)
    print(f"Button presses: {recorder.presses_path}", flush=True)
    try:
        screen_size = compute_screen_px()
        pygame.init()
        screen = pygame.display.set_mode((screen_size, screen_size))
        pygame.display.set_caption("Contour Interpolation Experiment")
        canvas = Canvas(screen, screen_size)
        canvas.default_step_idx = 2 if FINE_ADJUSTMENT_DEFAULT else 0
        show_screen(pygame, screen, "Contour Interpolation Task", "Press any key to begin")

        if not args.skip_tutorial:
            practice = [materialize_trial(spec, args.seed) for spec in build_practice_trials(
                seed=args.seed, small_fraction=args.small_fraction,
                spacing_profile=args.spacing_profile,
                include_off_center=not (args.block == 'identification' and args.curvature_maxima),
            )]
            canvas.run_tutorial(practice, FPS)
            show_screen(pygame, screen, "Practice complete", "Press any key to start the block")

        for trial_number, trial_spec in enumerate(trials, start=1):
            trial_spec['practice_protocol_version'] = PRACTICE_PROTOCOL_VERSION
            trial_spec['practice_feedback_received'] = not args.skip_tutorial
            trial_spec['practice_good_fraction'] = GOOD_FRACTION
            trial_spec['practice_moderate_fraction'] = MODERATE_FRACTION
            trial_spec['practice_feedback_duration_ms'] = FEEDBACK_DURATION_MS
            points, meta = materialize_trial(trial_spec, args.seed)
            final_position, press_sequence, final_record = canvas.run_trial(
                trial_number, points, meta, FPS
            )
            recorder.record(
                trial_number,
                final_position,
                press_sequence,
                meta,
                final_record,
                points,
            )
            print(f"Trial {trial_number}: both CSV files saved.", flush=True)

        show_screen(pygame, screen, "Block complete", "Thank you for participating")
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
