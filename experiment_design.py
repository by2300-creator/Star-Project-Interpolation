"""Counterbalanced trial construction for the revised experiment."""

from __future__ import annotations

from collections import Counter
import math
import random
from typing import Iterable, Sequence

from function import NUM_POINTS, SUPPORTED_FUNCTIONS, DEFAULT_CURVE_STRENGTH
from practice_feedback import PRACTICE_PROTOCOL_VERSION


# Hon et al. (1997), Experiment I, p. 413: 8 arcmin shift / ~60 arcmin spacing.
# Relative-size adaptation; monitor/viewing-distance calibration is not assumed.
DEFAULT_SMALL_FRACTION = 8.0 / 60.0
DESIGN_VERSION = "2026-09-25_midpoint_single_v2"
DEFAULT_SEGMENTATION_FRACTIONS = (0.08, 0.16, 0.32, 0.64)
DEFAULT_TARGETS = (3, 4)
DEFAULT_START_OFFSET_PX = 70.0


def build_practice_trials(seed=63, small_fraction=DEFAULT_SMALL_FRACTION,
                          spacing_profile="fixed_irregular", include_off_center=True) -> list[dict]:
    """Twenty ordered practice trials; depth rises from 10% to 90% strength.

    The line stays straight. Circle strength controls circular-arc depth,
    while polynomials are flattened perpendicular to their endpoint chord.
    Practice uses the same materializer, perturbations and renderer as trials.
    """
    families = ["line", "circle", "parabola", "cubic", "quartic", "quintic"] * 3
    families += ["circle", "parabola"]
    bases = _base_stimuli(seed, DEFAULT_TARGETS, ("standard",), spacing_profile)
    lookup = {(b["curve_family"], b["target_index"]): b for b in bases}
    trials = []
    for index, family in enumerate(families):
        target = 3 if include_off_center and index in (0, 6, 12, 18) else 4
        fraction = 0.10 + 0.80 * index / 19
        # Grade only unperturbed contours: perturbations have no unique answer.
        baseline = True
        visible = [i for i in range(NUM_POINTS) if i != target]
        pattern = () if baseline else ((visible[index % len(visible)], -1 if index % 2 else 1),)
        spec = _condition(
            lookup[(family, target)], block="practice", repetition=1,
            condition_type="baseline" if baseline else "single",
            regime="baseline" if baseline else "small", perturbations=pattern,
            magnitude_fraction=0.0 if baseline else small_fraction,
            condition_number=index,
        )
        spec.update(
            practice_protocol_version=PRACTICE_PROTOCOL_VERSION,
            practice_trial=index + 1, practice_strength_fraction=fraction,
            curve_strength=(fraction if family == "circle" else DEFAULT_CURVE_STRENGTH[family]),
            practice_flattening=(1.0 if family == "circle" else fraction),
            display_margin_fraction=small_fraction, planned_order=index + 1,
        )
        trials.append(spec)
    return trials


def _parse_targets(target_indices: Iterable[int]) -> tuple[int, ...]:
    targets = tuple(int(value) for value in target_indices)
    if not targets:
        raise ValueError("At least one target location is required.")
    if any(not 1 <= value <= NUM_POINTS - 2 for value in targets):
        raise ValueError(f"Target locations must be interior indices 1..{NUM_POINTS - 2}.")
    if len(set(targets)) != len(targets):
        raise ValueError("Target locations must be unique.")
    return targets


def _base_stimuli(
    seed: int,
    target_indices: Sequence[int],
    strength_levels: Sequence[str],
    spacing_profile: str,
):
    rng = random.Random(int(seed))
    bases = []
    for family_index, curve_family in enumerate(SUPPORTED_FUNCTIONS):
        for target_index in target_indices:
            family_levels = ("standard",) if curve_family in ("line", "circle") else strength_levels
            for level_index, strength_level in enumerate(family_levels):
                base_number = len(bases)
                bases.append(
                    {
                        "stimulus_id": f"{curve_family}_target{target_index}_{strength_level}",
                        "curve_family": curve_family,
                        "function_type": curve_family,
                        "target_index": int(target_index),
                        "movable_index": int(target_index),
                        "strength_level": str(strength_level),
                        "spacing_profile": str(spacing_profile),
                        "stimulus_seed": rng.randrange(1, 2**31 - 1),
                        "rotation_deg": rng.uniform(-22.5, 22.5),
                        "force_reversed": bool((family_index + target_index + level_index) % 2),
                        "baseline_number": base_number,
                        "family_number": family_index,
                        "strength_number": level_index,
                    }
                )
    return bases


def _condition(
    base: dict,
    *,
    block: str,
    repetition: int,
    condition_type: str,
    regime: str,
    perturbations: Sequence[tuple[int, int]],
    magnitude_fraction: float,
    condition_number: int,
) -> dict:
    # Ignore perturbation sign when assigning the starting side, so each +/-
    # symmetric-difference pair begins from the same motor state. Repetition
    # flips the side for repeated identical conditions.
    start_token = 0
    if condition_type == "single" and perturbations:
        visible = [index for index in range(NUM_POINTS) if index != int(base["target_index"])]
        start_token = visible.index(int(perturbations[0][0]))
    if condition_type == "paired":
        # The four +/- pair patterns are split evenly across starting sides.
        start_token = sum(
            (position + 1) * int(sign > 0)
            for position, (_, sign) in enumerate(perturbations)
        )
    start_side = 1 if (
        start_token
        + repetition
        + int(base["family_number"])
        + int(base["strength_number"])
    ) % 2 else -1
    pattern_label = "none" if not perturbations else "_".join(
        f"p{index}{'plus' if sign > 0 else 'minus'}" for index, sign in perturbations
    )
    trial = dict(base)
    trial.update(
        {
            "design_version": DESIGN_VERSION,
            "experiment_block": block,
            "experiment": block,
            "repetition": int(repetition),
            "rep": int(repetition),
            "condition_type": condition_type,
            "perturbation_regime": regime,
            "perturbations": [(int(index), int(sign)) for index, sign in perturbations],
            "perturb_fraction": float(magnitude_fraction),
            "initial_offset_px": float(start_side * DEFAULT_START_OFFSET_PX),
            "initial_side": int(start_side),
            "condition_number": int(condition_number),
            "trial_uid": (
                f"{base['stimulus_id']}_{block}_r{repetition}_c{condition_number}_{pattern_label}"
                f"_m{magnitude_fraction:.3f}"
            ),
        }
    )
    return trial


def build_identification_trials(
    seed: int = 63,
    repetitions: int = 1,
    target_indices: Sequence[int] = DEFAULT_TARGETS,
    strength_levels: Sequence[str] = ("standard",),
    spacing_profile: str = "fixed_irregular",
    small_fraction: float = DEFAULT_SMALL_FRACTION,
) -> list[dict]:
    """Midpoint single-dot perturbations; off-center targets are baseline only."""
    targets = _parse_targets(target_indices)
    if repetitions < 1:
        raise ValueError("repetitions must be at least one.")
    if not math.isfinite(small_fraction) or small_fraction <= 0:
        raise ValueError("small_fraction must be finite and positive.")
    bases = _base_stimuli(seed, targets, strength_levels, spacing_profile)
    trials: list[dict] = []

    for base in bases:
        target = int(base["target_index"])
        visible_indices = [index for index in range(NUM_POINTS) if index != target]
        for repetition in range(1, int(repetitions) + 1):
            condition_number = 0
            trials.append(
                _condition(
                    base,
                    block="identification",
                    repetition=repetition,
                    condition_type="baseline",
                    regime="baseline",
                    perturbations=(),
                    magnitude_fraction=0.0,
                    condition_number=condition_number,
                )
            )
            condition_number += 1

            if target != NUM_POINTS // 2:
                continue

            for point_index in visible_indices:
                for sign in (-1, 1):
                    trials.append(
                        _condition(
                            base,
                            block="identification",
                            repetition=repetition,
                            condition_type="single",
                            regime="small",
                            perturbations=((point_index, sign),),
                            magnitude_fraction=small_fraction,
                            condition_number=condition_number,
                        )
                    )
                    condition_number += 1

    rng = random.Random(int(seed) + 101)
    rng.shuffle(trials)
    for order, trial in enumerate(trials, start=1):
        trial["planned_order"] = order
    validate_trials(trials)
    return trials


def _diagnostic_segmentation_indices(target: int) -> tuple[int, ...]:
    nearest = [target - 1, target + 1]
    far_candidates = [index for index in range(NUM_POINTS) if index != target]
    farthest = max(far_candidates, key=lambda index: abs(index - target))
    return tuple(nearest + [farthest])


def build_segmentation_trials(
    seed: int = 63,
    repetitions: int = 1,
    target_indices: Sequence[int] = DEFAULT_TARGETS,
    strength_levels: Sequence[str] = ("standard",),
    spacing_profile: str = "fixed_irregular",
    magnitude_fractions: Sequence[float] = DEFAULT_SEGMENTATION_FRACTIONS,
) -> list[dict]:
    """Build a separate large-perturbation block for the membership transition."""
    targets = _parse_targets(target_indices)
    if repetitions < 1:
        raise ValueError("repetitions must be at least one.")
    if not magnitude_fractions or any(not math.isfinite(float(value)) or float(value) <= 0 for value in magnitude_fractions):
        raise ValueError("Segmentation magnitudes must be positive.")
    bases = _base_stimuli(seed, targets, strength_levels, spacing_profile)
    trials: list[dict] = []

    for base in bases:
        target = int(base["target_index"])
        diagnostic_indices = _diagnostic_segmentation_indices(target)
        for repetition in range(1, int(repetitions) + 1):
            condition_number = 0
            trials.append(
                _condition(
                    base,
                    block="segmentation",
                    repetition=repetition,
                    condition_type="baseline",
                    regime="baseline",
                    perturbations=(),
                    magnitude_fraction=0.0,
                    condition_number=condition_number,
                )
            )
            condition_number += 1
            if target != NUM_POINTS // 2:
                continue

            for point_index in diagnostic_indices:
                for magnitude_fraction in magnitude_fractions:
                    for sign in (-1, 1):
                        trials.append(
                            _condition(
                                base,
                                block="segmentation",
                                repetition=repetition,
                                condition_type="single",
                                regime="segmentation",
                                perturbations=((point_index, sign),),
                                magnitude_fraction=float(magnitude_fraction),
                                condition_number=condition_number,
                            )
                        )
                        condition_number += 1

    rng = random.Random(int(seed) + 202)
    rng.shuffle(trials)
    for order, trial in enumerate(trials, start=1):
        trial["planned_order"] = order
    validate_trials(trials)
    return trials


def validate_trials(trials: Sequence[dict]) -> None:
    """Fail early if target/perturbation rules or symmetric signs are broken."""
    for trial in trials:
        target = int(trial["target_index"])
        indices = [int(index) for index, _ in trial["perturbations"]]
        if target in indices:
            raise AssertionError("A trial perturbs its adjustable target.")
        if len(indices) != len(set(indices)):
            raise AssertionError("A trial perturbs the same point twice.")

    singles = Counter()
    for trial in trials:
        if trial["condition_type"] != "single":
            continue
        index, sign = trial["perturbations"][0]
        key = (
            trial["stimulus_id"],
            trial["repetition"],
            index,
            trial["perturb_fraction"],
        )
        singles[(key, sign)] += 1
    for (key, sign), count in singles.items():
        if singles[(key, -sign)] != count:
            raise AssertionError(f"Unbalanced perturbation signs for {key}.")


def summarize_trials(trials: Sequence[dict]) -> dict:
    return {
        "total_trials": len(trials),
        "curve_families": dict(Counter(trial["curve_family"] for trial in trials)),
        "target_locations": dict(Counter(trial["target_index"] for trial in trials)),
        "condition_types": dict(Counter(trial["condition_type"] for trial in trials)),
        "regimes": dict(Counter(trial["perturbation_regime"] for trial in trials)),
        "start_sides": dict(Counter(trial["initial_side"] for trial in trials)),
        "stimulus_sets": dict(Counter(trial.get('stimulus_set', 'original') for trial in trials)),
    }
