"""Experimenter-only viewer. Run directly in PyCharm; no participant CSVs.

Same trial builder, stimuli and renderer as run_exp.py. Left/Right browse,
PgUp/PgDn skip ten, Home/End go to endpoints, G jumps to a numbered trial.
C places the movable dot at the red reference answer. No fine-step gate.
"""
import argparse
import json
from run_exp import parse_args, build_trials, materialize_trial, compute_screen_px, FPS
from experiment_design import summarize_trials


def navigate(index, action, value, count):
    requested = index + value if action == 'relative' else value
    return max(0, min(count - 1, requested))


def main(argv=None):
    viewer = argparse.ArgumentParser(description=__doc__, add_help=False)
    viewer.add_argument('--start-trial', type=int, default=1)
    options, remaining = viewer.parse_known_args(argv)
    args = parse_args(remaining)
    trials = build_trials(args)
    print('EXPERIMENTER VIEW — no participant data are saved.')
    print(json.dumps(summarize_trials(trials), indent=2))
    if args.dry_run:
        return 0
    import pygame
    from canvas import Canvas, ExperimenterNavigation
    pygame.init()
    try:
        size = compute_screen_px()
        screen = pygame.display.set_mode((size, size))
        pygame.display.set_caption('EXPERIMENTER — contour inspection — no recording')
        canvas = Canvas(screen, size)
        canvas.experimenter_mode = True
        canvas.require_fine_submission = False
        index = navigate(0, 'absolute', options.start_trial-1, len(trials))
        while True:
            points, meta = materialize_trial(trials[index], args.seed)
            try:
                canvas.run_trial(f'{index+1}/{len(trials)}', points, meta, FPS, record=False)
                index = navigate(index, 'relative', 1, len(trials))
            except ExperimenterNavigation as event:
                index = navigate(index, event.action, event.value, len(trials))
    except SystemExit:
        return 0
    finally:
        pygame.quit()


if __name__ == '__main__':
    raise SystemExit(main())
