# replay.py
"""
Replay visualizer for the Function Adjustment Experiment.

Controls:
 - SPACE: play / pause
 - RIGHT: next trial
 - LEFT: previous trial
 - UP: increase playback speed
 - DOWN: decrease playback speed
 - G: open/close jump-to-trial input box (or click the box)
 - ESC / window close: exit

Usage:
    python replay.py --screen-size 1050
"""
import argparse
import json
import math
import time
import sys
import pandas as pd
import pygame
from collections import OrderedDict

# --- Configuration (tweak if needed) ---
DEFAULT_SCREEN_SIZE = 800
STEP_SIZES = [10, 5, 1]   # same indexing as game's canvas: 0=big,1=med,2=small
PLAY_DELAY = 0.12         # base seconds per press (will be multiplied by speed factor)
FONT_SIZE = 18
# ---------------------------------------

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--screen-size", type=int, default=DEFAULT_SCREEN_SIZE,
                   help="Square screen size in pixels (should match experiment run)")
    p.add_argument("--records", default="pixel_based_adjustment_data.csv")
    p.add_argument("--presses", default="button_press_sequence.csv")
    return p.parse_args()

def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

def move_towards(current, target, step):
    dx = target[0] - current[0]
    dy = target[1] - current[1]
    dist = math.hypot(dx, dy)
    if dist <= step or dist == 0:
        return (target[0], target[1])
    r = step / dist
    return (current[0] + dx * r, current[1] + dy * r)

def get_screen_position_from_local(cx, cy, local_x, local_y, scale, cosA, sinA):
    wx = cx + local_x * scale
    wy = cy + local_y * scale
    dx, dy = wx - cx, wy - cy
    sx = cx + dx * cosA - dy * sinA
    sy = cy + dx * sinA + dy * cosA
    return (sx, sy)

def parse_press_row(row):
    presses = []
    for col in sorted([c for c in row.index if c.startswith("press_")],
                      key=lambda s: int(s.split("_", 1)[1])):
        v = row[col]
        if pd.isna(v) or v == "":
            break
        presses.append(str(v))
    return presses

def parse_press_token(tok):
    if not isinstance(tok, str) or tok == "":
        return None, None
    parts = tok.split("_")
    if len(parts) == 1:
        return parts[0], 0
    btn = "_".join(parts[:-1])
    try:
        rev = int(parts[-1])
    except Exception:
        rev = 0
    return btn, rev

def estimate_px_per_unit(math_xs, screen_xs, screen_ys):
    scales = []
    n = len(math_xs)
    for i in range(n - 1):
        dx_math = math_xs[i+1] - math_xs[i]
        if abs(dx_math) < 1e-9:
            continue
        sx1, sy1 = screen_xs[i], screen_ys[i]
        sx2, sy2 = screen_xs[i+1], screen_ys[i+1]
        screen_dist = math.hypot(sx2 - sx1, sy2 - sy1)
        scales.append(screen_dist / abs(dx_math))
    if not scales:
        return None
    scales.sort()
    return scales[len(scales)//2]

def build_trial_records(records_df, presses_df):
    press_map = {}
    for _, r in presses_df.iterrows():
        trial = r.get("trial", None)
        if pd.isna(trial):
            continue
        trial = int(trial)
        press_map[trial] = r

    trials = OrderedDict()
    for _, r in records_df.iterrows():
        trial = r.get("trial", None)
        if pd.isna(trial):
            continue
        trial = int(trial)
        press_row = press_map.get(trial, None)
        if press_row is None:
            presses = []
        else:
            presses = parse_press_row(press_row)
        trials[trial] = {"rec": r, "presses": presses}
    return trials

def collect_points_from_rec(rec, num_points_guess=6):
    math_xs = []
    math_ys = []
    screen_xs = []
    screen_ys = []
    i = 0
    while True:
        math_x_key = f"x{i}_math"
        math_y_key = f"y{i}_math"
        if math_x_key in rec.index and not pd.isna(rec[math_x_key]):
            math_xs.append(safe_float(rec[math_x_key]))
            math_ys.append(safe_float(rec[math_y_key]))
            sx_key = f"x{i}_px"
            sy_key = f"y{i}_px"
            if sx_key in rec.index and not pd.isna(rec[sx_key]):
                screen_xs.append(safe_float(rec[sx_key]))
                screen_ys.append(safe_float(rec[sy_key]))
            else:
                screen_xs.append(None)
                screen_ys.append(None)
            i += 1
        else:
            break
    if not math_xs:
        for i in range(num_points_guess):
            math_xs.append(safe_float(rec.get(f"x{i}_math", 0.0)))
            math_ys.append(safe_float(rec.get(f"y{i}_math", 0.0)))
            sx = rec.get(f"x{i}_px", None)
            sy = rec.get(f"y{i}_px", None)
            screen_xs.append(None if pd.isna(sx) else safe_float(sx))
            screen_ys.append(None if pd.isna(sy) else safe_float(sy))
    return math_xs, math_ys, screen_xs, screen_ys

def draw_text(screen, text, x, y, font, color=(255,255,255)):
    surf = font.render(text, True, color)
    screen.blit(surf, (x, y))

def replay_trial(screen, cx, cy, screen_size, trial_num, trial_data, font, speed=1.0):
    rec = trial_data["rec"]
    presses = trial_data["presses"]

    math_xs, math_ys, screen_xs, screen_ys = collect_points_from_rec(rec)
    num_points = len(math_xs)
    movable_idx = int(safe_float(rec.get("target_index", rec.get("movable_index", num_points // 2))))

    # estimate scale from recorded screen coords if available
    has_screen_coords = all(v is not None for v in screen_xs)
    scale_est = safe_float(
        rec.get("display_scale_px_per_unit", rec.get("px_per_unit", 0.0)), 0.0
    )
    if has_screen_coords:
        scale_est = scale_est or estimate_px_per_unit(math_xs, screen_xs, screen_ys)
    if scale_est is None or scale_est <= 0:
        scale_est = 5.0

    # rotation
    rot_deg = safe_float(rec.get("rotation_deg", 0.0), 0.0)
    theta = math.radians(rot_deg)
    cosA = math.cos(theta)
    sinA = math.sin(theta)

    # New files store the contour-normal endpoints directly. Older files fall
    # back to their historical vertical markers.
    stored_ref_up_x = rec.get("ref_up_x_px", None)
    if stored_ref_up_x is not None and not pd.isna(stored_ref_up_x) and stored_ref_up_x != "":
        ref_up_screen = (safe_float(stored_ref_up_x), safe_float(rec.get("ref_up_y_px")))
        ref_down_screen = (
            safe_float(rec.get("ref_down_x_px")),
            safe_float(rec.get("ref_down_y_px")),
        )
    else:
        label_px = int((screen_size // 2) * 0.8)
        ref_up_local = (float(math_xs[movable_idx]), -label_px / scale_est)
        ref_down_local = (float(math_xs[movable_idx]), label_px / scale_est)
        ref_up_screen = get_screen_position_from_local(
            cx, cy, ref_up_local[0], ref_up_local[1], scale_est, cosA, sinA
        )
        ref_down_screen = get_screen_position_from_local(
            cx, cy, ref_down_local[0], ref_down_local[1], scale_est, cosA, sinA
        )

    function_type = rec.get("function_type", "")
    stored_correct_x = rec.get("correct_x_px", None)
    if stored_correct_x is not None and not pd.isna(stored_correct_x) and stored_correct_x != "":
        correct_screen_pos = (safe_float(stored_correct_x), safe_float(rec.get("correct_y_px")))
    else:
        correct_screen_pos = get_screen_position_from_local(
            cx,
            cy,
            float(math_xs[movable_idx]),
            float(math_ys[movable_idx]),
            scale_est,
            cosA,
            sinA,
        )

    # initial dot position (uses 'initial_w' if present)
    initial_w = rec.get("initial_w", None)
    try:
        initial_w = float(initial_w) if initial_w is not None and not pd.isna(initial_w) else 0.5
    except Exception:
        initial_w = 0.5

    stored_initial_x = rec.get("initial_movable_x_px", None)
    if stored_initial_x is not None and not pd.isna(stored_initial_x) and stored_initial_x != "":
        dot_pos = [safe_float(stored_initial_x), safe_float(rec.get("initial_movable_y_px"))]
    else:
        dot_pos = [
            ref_up_screen[0] * initial_w + ref_down_screen[0] * (1 - initial_w),
            ref_up_screen[1] * initial_w + ref_down_screen[1] * (1 - initial_w),
        ]

    # static points (prefer recorded screen coords when available)
    static_screen_points = []
    for i in range(num_points):
        sx = screen_xs[i]
        sy = screen_ys[i]
        if sx is None or sy is None:
            sx, sy = get_screen_position_from_local(cx, cy, math_xs[i], math_ys[i], scale_est, cosA, sinA)
        static_screen_points.append((sx, sy))

    final_x_px = safe_float(rec.get("final_x_px", rec.get("final_x", rec.get("final_x_px", 0.0))))
    final_y_px = safe_float(rec.get("final_y_px", rec.get("final_y", rec.get("final_y_px", 0.0))))

    # New records contain exact baseline coordinates and support paired
    # perturbations.  Old files fall back to the legacy single index.
    perturb_indices = []
    raw_indices = rec.get("perturb_indices", "")
    if isinstance(raw_indices, str) and raw_indices.strip():
        try:
            perturb_indices = [int(value) for value in json.loads(raw_indices)]
        except Exception:
            perturb_indices = []
    if not perturb_indices:
        legacy_index = rec.get("perturb_index", None)
        if legacy_index is not None and legacy_index != "" and not pd.isna(legacy_index):
            perturb_indices = [int(legacy_index)]

    perturbed_screens = {}
    unperturbed_screens = {}
    for pidx in perturb_indices:
        if not 0 <= pidx < num_points:
            continue
        perturbed_screens[pidx] = static_screen_points[pidx]
        baseline_x = rec.get(f"x{pidx}_baseline_math", None)
        baseline_y = rec.get(f"y{pidx}_baseline_math", None)
        if (
            baseline_x is not None
            and baseline_y is not None
            and baseline_x != ""
            and baseline_y != ""
            and not pd.isna(baseline_x)
            and not pd.isna(baseline_y)
        ):
            unperturbed_screens[pidx] = get_screen_position_from_local(
                cx,
                cy,
                float(baseline_x),
                float(baseline_y),
                scale_est,
                cosA,
                sinA,
            )

    perturb_idx = rec.get("perturb_index", None)
    perturb_type = rec.get("perturb_type", "")
    perturb_amount = rec.get("perturb_amount", rec.get("perturb_pixels", ""))

    parsed_presses = [parse_press_token(p) for p in presses]

    recorded_initial_step = rec.get('initial_step_px', 10)
    if pd.isna(recorded_initial_step) or recorded_initial_step == '':
        recorded_initial_step = 10
    manual_step_idx = STEP_SIZES.index(int(recorded_initial_step))
    game_reversals = 0
    last_btn = None
    up_target = ref_up_screen
    down_target = ref_down_screen

    # Input-box state for jump-to-trial
    input_active = False
    input_str = ""

    # draw legend & static overlay
    def draw_static_overlay(msg=""):
        # Draw anchors / static points / highlights
        screen.fill((30, 30, 30))
        pygame.draw.circle(screen, (0, 0, 0), (cx, cy), cx)

        # Draw only visible anchors; the target sample was hidden in the task.
        for i, (sx, sy) in enumerate(static_screen_points):
            if i == movable_idx:
                continue
            pygame.draw.circle(screen, (255, 255, 255), (int(sx), int(sy)), 3)

        # draw perturbed static points (red) if known
        for psx, psy in perturbed_screens.values():
            pygame.draw.circle(screen, (255, 0, 0), (int(psx), int(psy)), 6)

        # draw exact baseline locations (cyan)
        for ux, uy in unperturbed_screens.values():
            pygame.draw.circle(screen, (0, 200, 200), (int(ux), int(uy)), 5)

        # draw correct position (green small cross)
        try:
            cxp, cyp = correct_screen_pos
            pygame.draw.line(screen, (0, 255, 0), (int(cxp) - 5, int(cyp)), (int(cxp) + 5, int(cyp)), 2)
            pygame.draw.line(screen, (0, 255, 0), (int(cxp), int(cyp) - 5), (int(cxp), int(cyp) + 5), 2)
        except Exception:
            pass

        # draw final player response (magenta filled circle) and also yellow cross for precise final px coords
        pygame.draw.circle(screen, (255, 0, 255), (int(final_x_px), int(final_y_px)), 5)  # player answer
        pygame.draw.line(screen, (255, 255, 0), (int(final_x_px) - 6, int(final_y_px)),
                         (int(final_x_px) + 6, int(final_y_px)), 2)
        pygame.draw.line(screen, (255, 255, 0), (int(final_x_px), int(final_y_px) - 6),
                         (int(final_x_px), int(final_y_px) + 6), 2)

        # anchor markers
        ref_color = (0, 200, 0)
        pygame.draw.circle(screen, ref_color, (int(ref_up_screen[0]), int(ref_up_screen[1])), 4)
        pygame.draw.circle(screen, ref_color, (int(ref_down_screen[0]), int(ref_down_screen[1])), 4)

        # legend
        legend_y = screen_size - 120
        draw_text(screen, "Legend:", 12, legend_y, font)
        draw_text(screen, "red = perturbed static dot", 12, legend_y + 18, font)
        draw_text(screen, "cyan = reconstructed unperturbed location", 12, legend_y + 36, font)
        draw_text(screen, "magenta = player's final answer", 12, legend_y + 54, font)
        draw_text(screen, "green cross = correct position", 12, legend_y + 72, font)

        # metadata text
        draw_text(screen, f"Trial {trial_num}    Func={function_type}    Exp={rec.get('experiment','')}", 12, 8, font)
        draw_text(screen, f"Rotation: {rot_deg:.1f} deg   Scale≈{scale_est:.2f}px/unit", 12, 30, font)
        if msg:
            draw_text(screen, msg, 12, 52, font)

        # input box (top-right)
        box_w = 160
        box_h = 28
        box_x = screen_size - box_w - 12
        box_y = 8
        pygame.draw.rect(screen, (50, 50, 50), (box_x, box_y, box_w, box_h))
        pygame.draw.rect(screen, (120, 120, 120), (box_x, box_y, box_w, box_h), 1)
        hint = "press 'g' to jump"
        draw_text(screen, f"Jump to trial: {input_str if input_active else ''}", box_x + 8, box_y + 4, font, color=(220,220,220))
        draw_text(screen, hint, box_x + 8, box_x + box_h + 4 if False else box_y + box_h + 4, font, color=(150,150,150))

    # initial static draw
    draw_static_overlay()
    pygame.display.flip()

    playing = True
    press_index = 0
    last_time = time.time()
    delay = PLAY_DELAY / max(0.05, speed)
    local_clock = pygame.time.Clock()
    msg = ""

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "quit"
            elif ev.type == pygame.KEYDOWN:
                if input_active:
                    if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        try:
                            target = int(input_str)
                            input_active = False
                            input_str = ""
                            return f"jump:{target}"
                        except Exception:
                            input_str = ""
                            input_active = False
                            msg = "Invalid number"
                        continue
                    elif ev.key == pygame.K_BACKSPACE:
                        input_str = input_str[:-1]
                        continue
                    elif ev.unicode.isdigit() or (ev.key == pygame.K_MINUS and input_str == ""):
                        input_str += ev.unicode
                        continue
                    elif ev.key == pygame.K_g:
                        input_active = False
                        input_str = ""
                        continue
                    else:
                        continue

                # normal controls
                if ev.key == pygame.K_ESCAPE:
                    return "quit"
                elif ev.key == pygame.K_SPACE:
                    playing = not playing
                elif ev.key == pygame.K_RIGHT:
                    return "next"
                elif ev.key == pygame.K_LEFT:
                    return "prev"
                elif ev.key == pygame.K_UP:
                    speed *= 1.5
                    delay = PLAY_DELAY / max(0.05, speed)
                elif ev.key == pygame.K_DOWN:
                    speed = max(0.1, speed / 1.5)
                    delay = PLAY_DELAY / max(0.05, speed)
                elif ev.key == pygame.K_g:
                    input_active = not input_active
                    input_str = ""
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                box_w = 160; box_h = 28; box_x = screen_size - box_w - 12; box_y = 8
                mx, my = ev.pos
                if box_x <= mx <= box_x + box_w and box_y <= my <= box_y + box_h:
                    input_active = True
                    input_str = ""
                else:
                    input_active = False

        draw_static_overlay(msg)
        msg = ""

        if not playing:
            # draw movable dot (current pos)
            pygame.draw.circle(screen, (0, 150, 255), (int(dot_pos[0]), int(dot_pos[1])), 5)
            # final recorded pos as green cross
            pygame.draw.line(screen, (0,255,0), (int(final_x_px)-6, int(final_y_px)), (int(final_x_px)+6, int(final_y_px)), 2)
            pygame.draw.line(screen, (0,255,0), (int(final_x_px), int(final_y_px)-6), (int(final_x_px), int(final_y_px)+6), 2)
            pygame.display.flip()
            local_clock.tick(30)
            continue

        now = time.time()
        if press_index < len(parsed_presses) and (now - last_time) >= delay:
            btn, rev = parsed_presses[press_index]
            if btn and btn.startswith("step_"):
                if btn.endswith("small"):
                    manual_step_idx = 2
                elif btn.endswith("medium"):
                    manual_step_idx = 1
                else:
                    manual_step_idx = 0
                game_reversals = 0
                last_btn = None
                msg = f"Manual step set: {btn.split('_',1)[1]}"
            elif btn in ("up", "down"):
                current_btn = "up" if btn == "up" else "down"
                target = up_target if current_btn == "up" else down_target
                reversal_occurred = (last_btn is not None and current_btn != last_btn)
                if reversal_occurred:
                    game_reversals += 1
                base_idx = manual_step_idx if manual_step_idx is not None else 0
                rev_idx = min(game_reversals, len(STEP_SIZES) - 1)
                step_idx = min(len(STEP_SIZES) - 1, base_idx + rev_idx)
                step_px = STEP_SIZES[step_idx]
                dot_pos = move_towards(dot_pos, target, step_px)
                last_btn = current_btn
                msg = f"Press {press_index+1}/{len(parsed_presses)}: {btn} (step {step_px}px)"
            else:
                msg = f"Press {press_index+1}/{len(parsed_presses)}: {btn}"

            draw_static_overlay(msg)
            pygame.draw.circle(screen, (0, 150, 255), (int(dot_pos[0]), int(dot_pos[1])), 5)
            # final recorded pos as green cross
            pygame.draw.line(screen, (0,255,0), (int(final_x_px)-6, int(final_y_px)), (int(final_x_px)+6, int(final_y_px)), 2)
            pygame.draw.line(screen, (0,255,0), (int(final_x_px), int(final_y_px)-6), (int(final_x_px), int(final_y_px)+6), 2)
            # magenta correct target re-draw
            try:
                pygame.draw.circle(screen, (230, 100, 230), (int(correct_screen_pos[0]), int(correct_screen_pos[1])), 6)
            except Exception:
                pass
            pygame.display.flip()

            press_index += 1
            last_time = now

            if press_index >= len(parsed_presses):
                steps = int(max(1, 12 / max(0.2, speed)))
                fx, fy = final_x_px, final_y_px
                for k in range(steps):
                    t = (k + 1) / steps
                    dot_pos[0] = dot_pos[0] + (fx - dot_pos[0]) * t
                    dot_pos[1] = dot_pos[1] + (fy - dot_pos[1]) * t
                    draw_static_overlay(msg)
                    pygame.draw.circle(screen, (0, 150, 255), (int(dot_pos[0]), int(dot_pos[1])), 5)
                    pygame.draw.line(screen, (0,255,0), (int(final_x_px)-6, int(final_y_px)), (int(final_x_px)+6, int(final_y_px)), 2)
                    pygame.draw.line(screen, (0,255,0), (int(final_x_px), int(final_y_px)-6), (int(final_x_px), int(final_y_px)+6), 2)
                    pygame.display.flip()
                    time.sleep(0.03)
                time.sleep(0.6)
                return "done"

        local_clock.tick(60)


def main():
    args = parse_args()

    try:
        rec_df = pd.read_csv(args.records)
    except Exception as e:
        print("Error reading records CSV:", e)
        sys.exit(1)
    try:
        press_df = pd.read_csv(args.presses)
    except Exception as e:
        print("Error reading presses CSV:", e)
        sys.exit(1)

    trials = build_trial_records(rec_df, press_df)
    if not trials:
        print("No trials found in CSVs.")
        sys.exit(1)

    pygame.init()
    screen = pygame.display.set_mode((args.screen_size, args.screen_size))
    pygame.display.set_caption("Experiment Replay")
    font = pygame.font.SysFont(None, FONT_SIZE)
    cx = cy = args.screen_size // 2

    trial_keys = list(trials.keys())
    idx = 0
    speed = 1.0

    while True:
        trial_num = trial_keys[idx]
        status = replay_trial(screen, cx, cy, args.screen_size, trial_num, trials[trial_num], font, speed=speed)
        if status == "quit":
            break
        elif status == "next":
            idx = min(len(trial_keys) - 1, idx + 1)
        elif status == "prev":
            idx = max(0, idx - 1)
        elif isinstance(status, str) and status.startswith("jump:"):
            try:
                t = int(status.split(":",1)[1])
                if t in trial_keys:
                    idx = trial_keys.index(t)
                else:
                    nearest = min(range(len(trial_keys)), key=lambda i: abs(trial_keys[i] - t))
                    idx = nearest
            except Exception:
                pass
        elif status in ("done", None):
            screen.fill((30, 30, 30))
            pygame.draw.circle(screen, (0, 0, 0), (cx, cy), cx)
            draw_text(screen, f"Trial {trial_num} completed. LEFT/RIGHT to navigate. Press 'g' to jump. ESC to quit.", 12, 8, font)
            pygame.display.flip()
            waiting = True
            while waiting:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        waiting = False
                        sys.exit(0)
                    elif ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_RIGHT:
                            idx = min(len(trial_keys) - 1, idx + 1)
                            waiting = False
                        elif ev.key == pygame.K_LEFT:
                            idx = max(0, idx - 1)
                            waiting = False
                        elif ev.key == pygame.K_ESCAPE:
                            sys.exit(0)
                        elif ev.key == pygame.K_g:
                            waiting = False
                time.sleep(0.05)

    pygame.quit()

if __name__ == "__main__":
    main()
