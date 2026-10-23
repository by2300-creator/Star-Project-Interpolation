# –––straight_line_practice.py–––
"""
Self-contained straight-line game that matches the 3-shape game's structure and behavior.
Now supports two interpolation orientations: "vertical" (original) and "horizontal".
Balanced reversing (half reversed / half not) is controlled by the RNG seed.
Perturbation is applied in PIXELS (converted to math units using computed px_per_unit).
Manual step keys: 1=small, 2=med, 3=big. Movement keys: 'z' (toward first anchor) and '/' (toward second anchor).
"""

import pygame
import sys
import numpy as np
import pandas as pd
import random
import math
import os

# ---------- Random seed configuration ----------
RANDOM_SEED = 63  # remember to keep this the same as the other
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
# ------------------------------------------------

# ---------- Game constants (matched to 3-shape game) ----------
SCREEN_SIZE = 1050  # Changed from 1100 to match 3-shape game
FPS = 60
NUM_TRIALS = 10  # should preferably be even so vertical/horizontal counts are equal
DOT_RADIUS = 2  # Changed from 4 to match 3-shape game
HIGHLIGHT_TIME = 200
RESET_HIGHLIGHT_TIME = 700
DESIRED_SCALE = 5

# Points sampling (matched to 3-shape game)
NUM_POINTS = 6  # Changed from 7 to match 3-shape game
X_RANGE = 30  # Changed from 10 to match 3-shape game

# Perturb defaults (pixels) - matched to 3-shape game
DEFAULT_PERTURB_MIN_PX = 4
DEFAULT_PERTURB_MAX_PX = 8

# Step sizes in pixels: index 0 = big, 1 = med, 2 = small (matched to 3-shape game)
GLOBAL_STEP_SIZES = [10, 5, 1]
MAX_PRESSES = 70

# ---------- New configuration ----------
# Show/hide in-game instructional text (upper-left and bottom). Title/tutorial/Next remain shown.
SHOW_IN_GAME_TEXT = False

# Triangle size for anchor markers (pixels)
ANCHOR_TRIANGLE_SIZE = 10

# Moveable dot color
MOVABLE_DOT_COLOR = (255, 255, 255) # (0, 150, 255)=blue
# -------------------------------------------------


def _read_env_int(name, default):
    val = os.environ.get(name, None)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except Exception:
        return default


def generate_straight_line_points(scale_factor=1.0, force_reversed=None):
    """
    Return pts_df (DataFrame) and meta dict.
    Accepts force_reversed: None (random), True, or False to explicitly control reversal.
    """
    x_vals = np.linspace(-X_RANGE, X_RANGE, NUM_POINTS)
    y_vals = scale_factor * x_vals  # For straight line y = k*x with k==scale_factor

    # Controlled reversed option: if force_reversed is None, choose randomly;
    # otherwise obey the forced flag (used so reversal balance is controlled by seed).
    if force_reversed is None:
        is_reversed = random.choice([False, True])
    else:
        is_reversed = bool(force_reversed)

    if is_reversed:
        y_vals = -y_vals  # Reverse the line

    pts = [{"index": i, "x": float(x), "y": float(y)} for i, (x, y) in enumerate(zip(x_vals, y_vals))]
    meta = {
        "movable_index": NUM_POINTS // 2,
        "initial_w": random.uniform(0, 1),
        "correct_w": 0.5,
        "x_vals": list(x_vals),
        "y_vals": list(y_vals),
        "function_type": "straight_line",
        "reversed": is_reversed,  # Added to match 3-shape game
        # rotation/px_per_unit will be attached later
    }
    return pd.DataFrame(pts), meta


def define_rotation(meta):
    """Small rotation consistent with main experiment (-22.5..22.5 deg)."""
    meta["rotation_deg"] = random.uniform(-22.5, 22.5)
    return meta


def adjust_spread_local(pts_df, meta, left_range=(2.0, 3.0), right_range=(2.0, 3.0)):
    """
    Shift non-movable points left/right in math-units.
    For straight line y = k*x, update both x and y to preserve the line slope.
    """
    new_pts = pts_df.copy().reset_index(drop=True)
    movable_idx = int(meta["movable_index"])

    for i, row in new_pts.iterrows():
        idx = int(row["index"])
        if idx == movable_idx:
            continue

        base_x = float(row["x"])
        if idx < movable_idx:
            mag = random.uniform(left_range[0], left_range[1])
            sign = np.sign(base_x) if np.sign(base_x) != 0 else 1.0
            new_x = base_x - sign * mag
        else:
            mag = random.uniform(right_range[0], right_range[1])
            sign = np.sign(base_x) if np.sign(base_x) != 0 else 1.0
            new_x = base_x + sign * mag

        # keep y consistent with straight line y = scale_factor * x
        if abs(row["x"]) > 1e-9:
            scale_factor = float(row["y"]) / float(row["x"])
            new_y = scale_factor * new_x
        else:
            # fallback slope:
            slope = 1.0
            if "x_vals" in meta:
                for xo, yo in zip(meta.get("x_vals", []), meta.get("y_vals", [])):
                    if abs(xo) > 1e-9:
                        slope = yo / xo
                        break
            new_y = slope * new_x

        new_pts.at[i, "x"] = float(new_x)
        new_pts.at[i, "y"] = float(new_y)

    # update meta
    if "x_vals" in meta:
        meta["x_vals"] = [float(new_pts.loc[i, "x"]) for i in range(len(new_pts))]
    if "y_vals" in meta:
        meta["y_vals"] = [float(new_pts.loc[i, "y"]) for i in range(len(new_pts))]

    return new_pts, meta


def apply_perturbation_local(pts_df, meta, perturb_min_px=None, perturb_max_px=None, px_per_unit=None,
                             perturb_idx=None, perturb_sign=None):
    """
    Perturb one static point vertically by a random PIXEL amount (converted to math units).
    perturb_sign can be -1 / +1 to force direction; otherwise chosen randomly.
    """
    if perturb_min_px is None:
        perturb_min_px = _read_env_int("PERTURB_MIN_PX", DEFAULT_PERTURB_MIN_PX)
    if perturb_max_px is None:
        perturb_max_px = _read_env_int("PERTURB_MAX_PX", DEFAULT_PERTURB_MAX_PX)

    if perturb_min_px > perturb_max_px:
        perturb_min_px, perturb_max_px = perturb_max_px, perturb_min_px

    movable_idx = int(meta["movable_index"])
    static_idxs = [i for i in range(len(pts_df)) if i != movable_idx]

    if perturb_idx is not None:
        if int(perturb_idx) not in static_idxs:
            raise ValueError(f"perturb_idx {perturb_idx} invalid; must be one of {static_idxs}")
        chosen_idx = int(perturb_idx)
    else:
        chosen_idx = random.choice(static_idxs)

    if px_per_unit is None:
        px_per_unit = meta.get("px_per_unit", None) or DESIRED_SCALE

    if perturb_sign is not None and int(perturb_sign) in (-1, 1):
        sign = int(perturb_sign)
    else:
        sign = random.choice([-1, 1])

    delta_px = sign * random.randint(int(perturb_min_px), int(perturb_max_px))
    delta_units = float(delta_px) / float(px_per_unit)

    pts_df.at[chosen_idx, "y"] = float(pts_df.at[chosen_idx, "y"]) + delta_units

    meta.update({
        "perturb_index": int(chosen_idx),
        "perturb_pixels": int(delta_px),
        "perturb_units": float(delta_units),
        "perturb_x": float(pts_df.at[chosen_idx, "x"]),
        "perturb_y": float(pts_df.at[chosen_idx, "y"]),
        "perturb_sign": int(sign),
        "px_per_unit": float(px_per_unit)
    })

    return pts_df, meta


# ----------------- helper to draw oriented triangle anchor -----------------
def draw_anchor_triangle(surface, center_xy, anchor_xy, size, color=(0, 200, 0)):
    """
    Draw a small triangle centered at anchor_xy with one vertex pointing toward the circle center (center_xy).
    This makes anchors "point inward".
    """
    ax, ay = float(anchor_xy[0]), float(anchor_xy[1])
    cx, cy = float(center_xy[0]), float(center_xy[1])
    # angle from anchor toward center
    ang = math.atan2(cy - ay, cx - ax)
    # produce three vertices: one pointing toward center, two others rotated +-120 deg
    r = float(size)
    v1 = (ax + math.cos(ang) * r, ay + math.sin(ang) * r)
    ang2 = ang + (2.0 * math.pi / 3.0)
    v2 = (ax + math.cos(ang2) * r, ay + math.sin(ang2) * r)
    ang3 = ang - (2.0 * math.pi / 3.0)
    v3 = (ax + math.cos(ang3) * r, ay + math.sin(ang3) * r)
    pygame.draw.polygon(surface, color, [v1, v2, v3])


# ---------------- Canvas class (matched to 3-shape game) ----------------
class StraightLineCanvas:
    def __init__(self, screen, screen_size):
        self.screen = screen
        self.screen_size = screen_size
        self.cx = self.cy = screen_size // 2
        self.font = pygame.font.SysFont(None, 24)
        self.dot_radius = DOT_RADIUS
        self.desired_scale = DESIRED_SCALE
        self.step_sizes = GLOBAL_STEP_SIZES[:]  # pixels
        self.highlight_time = HIGHLIGHT_TIME
        self.reset_highlight_time = RESET_HIGHLIGHT_TIME
        self.max_presses = MAX_PRESSES

    def rotate_point(self, x, y, cx, cy, cosA, sinA):
        dx, dy = x - cx, y - cy
        return cx + dx * cosA - dy * sinA, cy + dx * sinA + dy * cosA

    def move_towards(self, current, target, step):
        """Move current position towards target by maximum of 'step' pixels (matched to 3-shape game)"""
        dx = target[0] - current[0]
        dy = target[1] - current[1]
        distance = math.hypot(dx, dy)

        if distance <= step:
            return (target[0], target[1])  # Reached target

        ratio = step / distance
        return (
            current[0] + dx * ratio,
            current[1] + dy * ratio
        )

    def get_screen_position(self, local_x, local_y, scale, cosA, sinA):
        """Convert local coordinates to screen coordinates with scaling and rotation"""
        wx = self.cx + local_x * scale
        wy = self.cy + local_y * scale
        return self.rotate_point(wx, wy, self.cx, self.cy, cosA, sinA)

    # ---- Tutorial (updated to match 3-shape game) ----
    def run_tutorial(self, pts_df, meta, fps, orientation="vertical"):
        """
        orientation: 'vertical' or 'horizontal'
        tutorial defaults to 'vertical' but can be set.
        """
        clock = pygame.time.Clock()
        screen = self.screen
        cx, cy = self.cx, self.cy

        theta = math.radians(meta.get("rotation_deg", 0))
        cosA, sinA = math.cos(theta), math.sin(theta)
        mi = meta["movable_index"]
        move_x = float(pts_df.loc[mi, "x"])
        move_y = float(pts_df.loc[mi, "y"])

        # Static points and scale
        static_pts = [(r["x"], r["y"]) for _, r in pts_df.iterrows() if int(r["index"]) != mi]
        max_x = max(abs(x) for x, _ in static_pts) if static_pts else 0
        scale = min(self.desired_scale, (cx - self.dot_radius) / max_x) if max_x != 0 else self.desired_scale

        # store screen positions for recorder
        for i, row in pts_df.iterrows():
            sx, sy = self.get_screen_position(float(row["x"]), float(row["y"]), scale, cosA, sinA)
            pts_df.at[i, "screen_x"] = float(sx)
            pts_df.at[i, "screen_y"] = float(sy)

        # Reference anchor offset: place anchors at the circle edge (touching)
        label_px = cx - (self.dot_radius + 2)  # anchor distance from center in pixels (nearly touching edge)

        # Local anchor coords depend on orientation:
        if orientation == "vertical":
            # anchors are directly above/below at the movable x (same as original behavior)
            ref_up = (move_x, -label_px / scale)
            ref_down = (move_x, label_px / scale)
            # convert to screen positions
            ref_up_screen = self.get_screen_position(ref_up[0], ref_up[1], scale, cosA, sinA)
            ref_down_screen = self.get_screen_position(ref_down[0], ref_down[1], scale, cosA, sinA)
            # correct position is midpoint
            correct_screen_pos = ((ref_up_screen[0] + ref_down_screen[0]) / 2,
                                  (ref_up_screen[1] + ref_down_screen[1]) / 2)
            # initial local pos: x = move_x, y along anchors
            initial_w = meta.get("initial_w", 0.5)
            init_local_x = move_x
            init_local_y = ref_up[1] * initial_w + ref_down[1] * (1 - initial_w)
            dot_screen_pos = self.get_screen_position(init_local_x, init_local_y, scale, cosA, sinA)
        else:
            # horizontal: anchors are left and right, symmetric around center x=0, y = move_y
            ref_left = (-label_px / scale, move_y)
            ref_right = (label_px / scale, move_y)
            ref_left_screen = self.get_screen_position(ref_left[0], ref_left[1], scale, cosA, sinA)
            ref_right_screen = self.get_screen_position(ref_right[0], ref_right[1], scale, cosA, sinA)
            correct_screen_pos = ((ref_left_screen[0] + ref_right_screen[0]) / 2,
                                  (ref_left_screen[1] + ref_right_screen[1]) / 2)
            initial_w = meta.get("initial_w", 0.5)
            init_local_y = move_y
            init_local_x = ref_left[0] * initial_w + ref_right[0] * (1 - initial_w)
            dot_screen_pos = self.get_screen_position(init_local_x, init_local_y, scale, cosA, sinA)
            # assign to canonical names so drawing code below can reuse variable names
            ref_up_screen = ref_left_screen
            ref_down_screen = ref_right_screen

        # Tutorial state for manual step selection
        manual_step_idx = None  # None means no manual override; default base is 0 (big)

        def draw_frame(instruction_lines, show_refs=True, intermediate_msg=""):
            screen.fill((30, 30, 30))
            pygame.draw.circle(screen, (0, 0, 0), (cx, cy), cx)

            # Title
            title = self.font.render("Interactive Tutorial", True, (255, 255, 255))
            screen.blit(title, (20, 12))

            # Draw static dots
            for lx, ly in static_pts:
                sx, sy = self.get_screen_position(lx, ly, scale, cosA, sinA)
                pygame.draw.circle(screen, (255, 255, 255),
                                   (int(sx), int(sy)), self.dot_radius)

            # Draw movable dot
            pygame.draw.circle(screen, MOVABLE_DOT_COLOR,
                               (int(dot_screen_pos[0]), int(dot_screen_pos[1])), self.dot_radius)

            # Draw reference markers (triangles)
            if show_refs:
                for pos in [ref_up_screen, ref_down_screen]:
                    draw_anchor_triangle(screen, (cx, cy), pos, ANCHOR_TRIANGLE_SIZE)

            # Render instructions only if configured
            if SHOW_IN_GAME_TEXT:
                for i, line in enumerate(instruction_lines):
                    txt = self.font.render(line, True, (220, 220, 220))
                    screen.blit(txt, (20, 50 + i * 28))

                # Intermediate message
                if intermediate_msg:
                    im = self.font.render(intermediate_msg, True, (255, 255, 255))
                    screen.blit(im, ((self.screen_size - im.get_width()) // 2, self.screen_size - 60))

            pygame.display.flip()

        # 0) Initial overlay (keep tutorials visible)
        intro_lines = [
            "Welcome! We'll walk you through the controls interactively.",
            "You'll first move the blue dot, then practice reversals (the trick),",
            "and finally choose step sizes with 1 (small), 2 (med), 3 (big).",
            "",
            "Press any key to begin the interactive tutorial."
        ]
        overlay = pygame.Surface((self.screen_size, self.screen_size), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        for i, line in enumerate(intro_lines):
            txt = self.font.render(line, True, (255, 255, 255))
            x = (self.screen_size - txt.get_width()) // 2
            y = self.screen_size // 3 + i * 30
            screen.blit(txt, (x, y))
        pygame.display.flip()
        waiting = True
        while waiting:
            for ev in pygame.event.get():
                if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
                elif ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            clock.tick(30)

        # ------------ Step 1: Move the blue dot ------------
        moved = False
        instruction_lines = [
            "Step 1: Move the BLUE dot.",
            "Press 'z' (move toward first anchor) or '/' (move toward second anchor).",
            "Try pressing either key once to move the blue dot."
        ]
        draw_frame(instruction_lines, show_refs=True, intermediate_msg="Waiting for your first move...")
        while not moved:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_z:
                        dot_screen_pos = self.move_towards(dot_screen_pos, ref_up_screen, self.step_sizes[0])
                        moved = True
                        draw_frame(instruction_lines, show_refs=True, intermediate_msg="Good — you moved with 'z'!")
                        pygame.time.delay(self.highlight_time)
                    elif ev.key == pygame.K_SLASH:
                        dot_screen_pos = self.move_towards(dot_screen_pos, ref_down_screen, self.step_sizes[0])
                        moved = True
                        draw_frame(instruction_lines, show_refs=True, intermediate_msg="Good — you moved with '/'!")
                        pygame.time.delay(self.highlight_time)
            draw_frame(instruction_lines, show_refs=True)
            clock.tick(fps)

        # ------------ Step 2: Reversal practice ------------
        reversals = 0
        last_btn = None
        instruction_lines = [
            "Step 2: Reversal practice — make TWO reversals.",
            "A reversal is when you switch keys: e.g. z -> / -> z",
            "When you make two reversals the step size becomes very small for fine adjustments."
        ]
        intermediate = "Reversals: 0 / 2"
        draw_frame(instruction_lines, show_refs=True, intermediate_msg=intermediate)
        while reversals < 2:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif ev.type == pygame.KEYDOWN:
                    # numeric keys ignored here (but they now reset reversals and last_btn)
                    if ev.key == pygame.K_1:
                        manual_step_idx = 2
                        reversals = 0
                        last_btn = None
                        # show step-change message even if in-game text is hidden
                        pygame.draw.rect(screen, (50, 50, 50), (self.screen_size - 340, 50, 320, 40))
                        lbl = self.font.render("Step set to SMALL (1)", True, (255, 255, 255))
                        screen.blit(lbl, (self.screen_size - 340 + 10, 50 + 6))
                        pygame.display.flip()
                        pygame.time.delay(self.highlight_time)
                        continue
                    elif ev.key == pygame.K_2:
                        manual_step_idx = 1
                        reversals = 0
                        last_btn = None
                        pygame.draw.rect(screen, (50, 50, 50), (self.screen_size - 340, 50, 320, 40))
                        lbl = self.font.render("Step set to MEDIUM (2)", True, (255, 255, 255))
                        screen.blit(lbl, (self.screen_size - 340 + 10, 50 + 6))
                        pygame.display.flip()
                        pygame.time.delay(self.highlight_time)
                        continue
                    elif ev.key == pygame.K_3:
                        manual_step_idx = 0
                        reversals = 0
                        last_btn = None
                        pygame.draw.rect(screen, (50, 50, 50), (self.screen_size - 340, 50, 320, 40))
                        lbl = self.font.render("Step set to BIG (3)", True, (255, 255, 255))
                        screen.blit(lbl, (self.screen_size - 340 + 10, 50 + 6))
                        pygame.display.flip()
                        pygame.time.delay(self.highlight_time)
                        continue
                    else:
                        current_btn = None
                        target = None

                    if ev.key == pygame.K_z:
                        current_btn = "up"
                        target = ref_up_screen
                    elif ev.key == pygame.K_SLASH:
                        current_btn = "down"
                        target = ref_down_screen

                    if current_btn:
                        # Check for reversal
                        if last_btn is not None and current_btn != last_btn:
                            reversals += 1
                        # Compute effective step index using additive rule:
                        base_idx = manual_step_idx if manual_step_idx is not None else 0
                        rev_idx = min(reversals, len(self.step_sizes) - 1)
                        step_idx = min(len(self.step_sizes) - 1, base_idx + rev_idx)
                        # Move the dot
                        dot_screen_pos = self.move_towards(dot_screen_pos, target, self.step_sizes[step_idx])
                        last_btn = current_btn
                        intermediate = f"Reversals: {reversals} / 2"
                        draw_frame(instruction_lines, show_refs=True, intermediate_msg=intermediate)
            draw_frame(instruction_lines, show_refs=True, intermediate_msg=intermediate)
            clock.tick(fps)

        # Congrats message
        draw_frame(["Great — you made two reversals!",
                    "Notice the step size is now very small, allowing fine adjustments."],
                   show_refs=True, intermediate_msg="Press any key to continue to step-size practice.")
        pygame.display.flip()
        waiting = True
        while waiting:
            for ev in pygame.event.get():
                if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
                elif ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            clock.tick(30)

        # ------------ Step 3: Step-size practice (now with 1/2/3) ------------
        instruction_lines = [
            "Step 3: Step-size selection practice.",
            "Press '1' for SMALL steps, '2' for MEDIUM, '3' for BIG.",
            "You can still reduce step size further by making reversals."
        ]
        draw_frame(instruction_lines, show_refs=True, intermediate_msg="Press 1, 2, or 3 now.")
        step_practiced = False
        # reset reversals and manual idx for this practice
        reversals = 0
        last_btn = None
        manual_step_idx = None
        while not step_practiced:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_1:
                        manual_step_idx = 2
                        reversals = 0
                        last_btn = None
                        pygame.draw.rect(screen, (50, 50, 50), (self.screen_size - 340, 50, 320, 40))
                        lbl = self.font.render("Small selected (1).", True, (255, 255, 255))
                        screen.blit(lbl, (self.screen_size - 340 + 10, 50 + 6))
                        pygame.display.flip()
                        pygame.time.delay(self.highlight_time)
                        step_practiced = True
                    elif ev.key == pygame.K_2:
                        manual_step_idx = 1
                        reversals = 0
                        last_btn = None
                        pygame.draw.rect(screen, (50, 50, 50), (self.screen_size - 340, 50, 320, 40))
                        lbl = self.font.render("Medium selected (2).", True, (255, 255, 255))
                        screen.blit(lbl, (self.screen_size - 340 + 10, 50 + 6))
                        pygame.display.flip()
                        pygame.time.delay(self.highlight_time)
                        step_practiced = True
                    elif ev.key == pygame.K_3:
                        manual_step_idx = 0
                        reversals = 0
                        last_btn = None
                        pygame.draw.rect(screen, (50, 50, 50), (self.screen_size - 340, 50, 320, 40))
                        lbl = self.font.render("Big selected (3).", True, (255, 255, 255))
                        screen.blit(lbl, (self.screen_size - 340 + 10, 50 + 6))
                        pygame.display.flip()
                        pygame.time.delay(self.highlight_time)
                        step_practiced = True
                    elif ev.key == pygame.K_z:
                        dot_screen_pos = self.move_towards(dot_screen_pos, ref_up_screen, self.step_sizes[0])
                        draw_frame(instruction_lines, show_refs=True, intermediate_msg="You moved with 'z'.")
                        pygame.time.delay(self.highlight_time)
                    elif ev.key == pygame.K_SLASH:
                        dot_screen_pos = self.move_towards(dot_screen_pos, ref_down_screen, self.step_sizes[0])
                        draw_frame(instruction_lines, show_refs=True, intermediate_msg="You moved with '/'.")
                        pygame.time.delay(self.highlight_time)
            clock.tick(fps)

        # Confirmation screen
        draw_frame(["Good — you know how to move, make reversals, and choose step sizes."],
                   show_refs=True, intermediate_msg="When ready, press any key to run practice trials.")
        waiting = True
        while waiting:
            for ev in pygame.event.get():
                if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
                elif ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            clock.tick(30)

        # ------------- NEW: Run 3 randomized practice trials (unrecorded) -------------
        num_practice = 3

        for i in range(1, num_practice + 1):
            # 1) Generate fresh straight line points
            pts_practice, meta_practice = generate_straight_line_points(scale_factor=1.0)

            # 2) rotation & spread
            meta_practice = define_rotation(meta_practice)
            pts_practice, meta_practice = adjust_spread_local(pts_practice, meta_practice)

            # 3) compute px_per_unit to match Canvas scaling
            static_pts_trial = [(r["x"], r["y"]) for _, r in pts_practice.iterrows() if
                                int(r["index"]) != meta_practice["movable_index"]]
            max_x_trial = max(abs(x) for x, _ in static_pts_trial) if static_pts_trial else 0
            px_per_unit_trial = DESIRED_SCALE if max_x_trial == 0 else min(DESIRED_SCALE,
                                                               (self.cx - self.dot_radius) / max_x_trial)

            # 4) Apply perturbation (practice uses apply_perturbation_local)
            pts_practice, meta_practice = apply_perturbation_local(
                pts_practice,
                meta_practice,
                px_per_unit=px_per_unit_trial
            )

            # 5) Randomly pick orientation for practice (balanced not enforced)
            prac_orientation = random.choice(["vertical", "horizontal"])

            # 6) Run the practice trial (interactive, unrecorded)
            try:
                self.run_trial(f"Practice {i}", pts_practice, meta_practice, fps, orientation=prac_orientation)
            except SystemExit:
                raise
            except Exception as e:
                overlay = pygame.Surface((self.screen_size, self.screen_size), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                err_txt = self.font.render(f"Practice trial error: {e}", True, (255, 0, 0))
                screen.blit(err_txt, ((self.screen_size - err_txt.get_width()) // 2, self.screen_size // 2))
                pygame.display.flip()
                pygame.time.delay(700)

        # ------------- Tutorial completion -------------
        overlay = pygame.Surface((self.screen_size, self.screen_size), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        done_txt = self.font.render("Tutorial complete! Click Next to begin.", True, (255, 255, 255))
        btn = pygame.Rect(self.screen_size - 110, 10, 100, 32)
        pygame.draw.rect(self.screen, (50, 50, 50), btn)
        lbl = self.font.render("Next", True, (200, 200, 200))
        screen.blit(done_txt, ((self.screen_size - done_txt.get_width()) // 2, self.screen_size // 2 - 20))
        screen.blit(lbl, lbl.get_rect(center=btn.center))
        pygame.display.flip()
        waiting = True
        while waiting:
            for ev in pygame.event.get():
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if btn.collidepoint(ev.pos):
                        waiting = False
                elif ev.type in (pygame.KEYDOWN,) and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    # allow Enter/Space to act like clicking Next in the tutorial
                    waiting = False
                elif ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            clock.tick(30)

    # ---- run_trial (updated to accept orientation and draw triangles) ----
    def run_trial(self, trial, pts_df, meta, fps, orientation="vertical", record=True):
        clock = pygame.time.Clock()
        screen = self.screen
        cx, cy = self.cx, self.cy

        theta = math.radians(meta.get("rotation_deg", 0))
        cosA, sinA = math.cos(theta), math.sin(theta)
        mi = int(meta["movable_index"])

        # static points and scale
        static_pts = [(r["x"], r["y"]) for _, r in pts_df.iterrows() if int(r["index"]) != mi]
        max_x = max(abs(x) for x, _ in static_pts) if static_pts else 0
        scale = min(self.desired_scale, (cx - self.dot_radius) / max_x) if max_x != 0 else self.desired_scale

        # store screen positions of all points (recorder-friendly)
        for i, row in pts_df.iterrows():
            sx, sy = self.get_screen_position(float(row["x"]), float(row["y"]), scale, cosA, sinA)
            pts_df.at[i, "screen_x"] = float(sx)
            pts_df.at[i, "screen_y"] = float(sy)

        # compute reference anchors in local coords (vertical or horizontal)
        label_px = cx - (self.dot_radius + 2)  # anchors at edge of circular window

        if orientation == "vertical":
            ref_up_local = (float(pts_df.loc[mi, "x"]), -label_px / scale)
            ref_down_local = (float(pts_df.loc[mi, "x"]), label_px / scale)
            ref_up_screen = self.get_screen_position(ref_up_local[0], ref_up_local[1], scale, cosA, sinA)
            ref_down_screen = self.get_screen_position(ref_down_local[0], ref_down_local[1], scale, cosA, sinA)
            correct_screen_pos = ((ref_up_screen[0] + ref_down_screen[0]) / 2,
                                  (ref_up_screen[1] + ref_down_screen[1]) / 2)
            # initial dot pos along vertical anchors
            initial_w = float(meta.get("initial_w", 0.5))
            init_local_x = ref_up_local[0]
            init_local_y = ref_up_local[1] * initial_w + ref_down_local[1] * (1 - initial_w)
            dot_screen_pos = self.get_screen_position(init_local_x, init_local_y, scale, cosA, sinA)
        else:
            # horizontal anchors (left/right symmetric around x=0 at movable y)
            move_y = float(pts_df.loc[mi, "y"])
            ref_left_local = (-label_px / scale, move_y)
            ref_right_local = (label_px / scale, move_y)
            ref_left_screen = self.get_screen_position(ref_left_local[0], ref_left_local[1], scale, cosA, sinA)
            ref_right_screen = self.get_screen_position(ref_right_local[0], ref_right_local[1], scale, cosA, sinA)
            ref_up_screen = ref_left_screen  # reuse variable names for 'first/second anchor'
            ref_down_screen = ref_right_screen
            correct_screen_pos = ((ref_left_screen[0] + ref_right_screen[0]) / 2,
                                  (ref_left_screen[1] + ref_right_screen[1]) / 2)
            # initial dot pos along horizontal anchors
            initial_w = float(meta.get("initial_w", 0.5))
            init_local_y = move_y
            init_local_x = ref_left_local[0] * initial_w + ref_right_local[0] * (1 - initial_w)
            dot_screen_pos = self.get_screen_position(init_local_x, init_local_y, scale, cosA, sinA)

        # px_per_unit used for perturb; record into meta for logging
        px_per_unit = scale
        meta["px_per_unit"] = float(px_per_unit)
        # also record orientation in meta so recorder can write it
        meta["orientation"] = orientation

        move_count = 0
        # Separate reversal counters: one for game logic, one for recording
        game_reversals = 0  # Used for step size calculation (resets with 1-2-3)
        cumulative_reversals = 0  # Used for recording (persists through resets)
        last_btn = None
        manual_step_idx = None  # None => default base = 0 (big)
        presses = []
        btn_rect = pygame.Rect(self.screen_size - 110, 10, 100, 32)
        in_trial = True

        while in_trial:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif ev.type == pygame.KEYDOWN:
                    # manual step keys (reset GAME reversals only)
                    if ev.key == pygame.K_1:
                        manual_step_idx = 2
                        game_reversals = 0  # Reset game reversal counter
                        last_btn = None
                        # Record with cumulative reversals
                        presses.append(("step_small", cumulative_reversals))
                        pygame.draw.rect(screen, (50, 50, 50), (self.screen_size - 340, 50, 320, 40))
                        lbl = self.font.render("Step set to SMALL (1)", True, (255, 255, 255))
                        screen.blit(lbl, (self.screen_size - 340 + 10, 50 + 6))
                        pygame.display.flip()
                        pygame.time.delay(self.highlight_time)
                        continue
                    elif ev.key == pygame.K_2:
                        manual_step_idx = 1
                        game_reversals = 0  # Reset game reversal counter
                        last_btn = None
                        presses.append(("step_medium", cumulative_reversals))
                        pygame.draw.rect(screen, (50, 50, 50), (self.screen_size - 340, 50, 320, 40))
                        lbl = self.font.render("Step set to MEDIUM (2)", True, (255, 255, 255))
                        screen.blit(lbl, (self.screen_size - 340 + 10, 50 + 6))
                        pygame.display.flip()
                        pygame.time.delay(self.highlight_time)
                        continue
                    elif ev.key == pygame.K_3:
                        manual_step_idx = 0
                        game_reversals = 0  # Reset game reversal counter
                        last_btn = None
                        presses.append(("step_big", cumulative_reversals))
                        pygame.draw.rect(screen, (50, 50, 50), (self.screen_size - 340, 50, 320, 40))
                        lbl = self.font.render("Step set to BIG (3)", True, (255, 255, 255))
                        screen.blit(lbl, (self.screen_size - 340 + 10, 50 + 6))
                        pygame.display.flip()
                        pygame.time.delay(self.highlight_time)
                        continue

                    # movement keys - map to the first/second anchor for current orientation
                    current_btn = None
                    target = None
                    if ev.key == pygame.K_z or ev.key == pygame.K_UP:
                        current_btn = "up"
                        target = ref_up_screen
                    elif ev.key == pygame.K_SLASH or ev.key == pygame.K_DOWN:
                        current_btn = "down"
                        target = ref_down_screen

                    # Allow space/enter to act like clicking the Next button
                    if ev.key in (pygame.K_SPACE, pygame.K_RETURN):
                        # Simulate clicking the Next button
                        ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": btn_rect.center, "button": 1})
                        pygame.event.post(ev)
                        continue

                    if current_btn:
                        # Check reversal
                        reversal_occurred = last_btn is not None and current_btn != last_btn
                        if reversal_occurred:
                            game_reversals += 1  # Update game counter
                            cumulative_reversals += 1  # Update cumulative counter for recording

                        # Use game_reversals for step size calculation
                        base_idx = manual_step_idx if manual_step_idx is not None else 0
                        rev_idx = min(game_reversals, len(self.step_sizes) - 1)
                        step_idx = min(len(self.step_sizes) - 1, base_idx + rev_idx)
                        step_px = self.step_sizes[step_idx]
                        dot_screen_pos = self.move_towards(dot_screen_pos, target, step_px)
                        move_count += 1
                        # Record with cumulative reversals
                        presses.append((current_btn, cumulative_reversals))
                        last_btn = current_btn

                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if btn_rect.collidepoint(ev.pos):
                        # finalize
                        pygame.draw.rect(screen, (0, 200, 0), btn_rect)
                        lbl = self.font.render("Next", True, (255, 255, 255))
                        screen.blit(lbl, lbl.get_rect(center=btn_rect.center))
                        pygame.display.flip()
                        pygame.time.delay(self.highlight_time)

                        pixel_distance = math.hypot(dot_screen_pos[0] - correct_screen_pos[0],
                                                    dot_screen_pos[1] - correct_screen_pos[1])
                        final_record = {
                            "total_moves": move_count,
                            "final_x": float(dot_screen_pos[0]),
                            "final_y": float(dot_screen_pos[1]),
                            "pixel_distance": float(pixel_distance)
                        }
                        in_trial = False

            # Draw frame
            screen.fill((30, 30, 30))
            pygame.draw.circle(screen, (0, 0, 0), (cx, cy), cx)

            # Trial info (title only)
            title_txt = self.font.render(f"Trial {trial}", True, (255, 255, 255))
            screen.blit(title_txt, (20, 12))

            # In-game instructions (hidden if SHOW_IN_GAME_TEXT is False)
            if SHOW_IN_GAME_TEXT:
                inst1 = self.font.render("Press 'z' or '/' to move.", True, (200, 200, 200))
                inst2 = self.font.render("Press '1'=small '2'=med '3'=big to set step.", True, (200, 200, 200))
                screen.blit(inst1, (20, 50))
                screen.blit(inst2, (20, 80))

            # Static dots
            for lx, ly in static_pts:
                sx, sy = self.get_screen_position(lx, ly, scale, cosA, sinA)
                pygame.draw.circle(screen, (255, 255, 255), (int(sx), int(sy)), self.dot_radius)

            # Movable dot
            pygame.draw.circle(screen, MOVABLE_DOT_COLOR, (int(dot_screen_pos[0]), int(dot_screen_pos[1])), self.dot_radius)

            # Next button
            pygame.draw.rect(screen, (50, 50, 50), btn_rect)
            lbl = self.font.render("Next", True, (200, 200, 200))
            screen.blit(lbl, lbl.get_rect(center=btn_rect.center))

            # Reference markers (draw triangles at anchors)
            for pos in [ref_up_screen, ref_down_screen]:
                draw_anchor_triangle(screen, (cx, cy), pos, ANCHOR_TRIANGLE_SIZE)

            pygame.display.flip()
            clock.tick(fps)

        # return in same style as 3-shape game
        return (float(final_record["final_x"]), float(final_record["final_y"])), presses, final_record


# ------------------ Recorder (updated to match 3-shape game) ------------------
class PracticeRecorder:
    def __init__(self):
        self.records = []
        self.events = []

    def record(self, trial, final_px, press_sequence, meta, final_record, pts_df):
        # Count how many times reset was pressed
        r_positions = [i for i, (btn, rev) in enumerate(press_sequence, start=1) if btn == "reset"]
        r_count = len(r_positions)

        rec = {
            "trial": trial,
            "total_moves": final_record.get("total_moves", 0),
            "final_x_px": final_record.get("final_x", ""),
            "final_y_px": final_record.get("final_y", ""),
            "pixel_distance": final_record.get("pixel_distance", ""),
            "initial_w": meta.get("initial_w", ""),
            "rotation_deg": meta.get("rotation_deg", ""),
            "perturb_index": meta.get("perturb_index", ""),
            "perturb_amount": meta.get("perturb_pixels", ""),
            "function_type": meta.get("function_type", "straight_line"),
            "orientation": meta.get("orientation", ""),  # NEW: orientation saved
            "reversed": meta.get("reversed", False),
            "r_count": r_count,
            "random_seed": RANDOM_SEED
        }

        # Add all points' screen coordinates
        for _, row in pts_df.iterrows():
            idx = int(row["index"])
            rec[f"x{idx}_math"] = row["x"]
            rec[f"y{idx}_math"] = row["y"]

            # Safer extraction of screen coordinates
            sx = row.get("screen_x", "")
            sy = row.get("screen_y", "")
            if sx is None or (isinstance(sx, float) and pd.isna(sx)):
                rec[f"x{idx}_px"] = ""
            else:
                rec[f"x{idx}_px"] = float(sx)

            if sy is None or (isinstance(sy, float) and pd.isna(sy)):
                rec[f"y{idx}_px"] = ""
            else:
                rec[f"y{idx}_px"] = float(sy)

        self.records.append(rec)

        # Build button-press log
        press_row = {"trial": trial}
        for i, (btn, rev) in enumerate(press_sequence, start=1):
            press_row[f"press_{i}"] = f"{btn}_{rev}"

        # Track where resets occurred
        if r_positions:
            press_row["r_presses"] = ";".join(str(x) for x in r_positions)
        else:
            press_row["r_presses"] = ""

        self.events.append(press_row)

    def save(self):
        pd.DataFrame(self.records).to_csv("straight_line_practice_data.csv", index=False)
        pd.DataFrame(self.events).to_csv("straight_line_button_sequence.csv", index=False)


# -------------------- Main script (updated to match 3-shape game) --------------------
def show_screen(screen, text, subtext=None, wait_for_key=True):
    screen.fill((30, 30, 30))
    cx, cy = SCREEN_SIZE // 2, SCREEN_SIZE // 2
    main_text = pygame.font.SysFont(None, 36).render(text, True, (255, 255, 255))
    screen.blit(main_text, (cx - main_text.get_width() // 2, cy - 40))
    if subtext:
        sub_text = pygame.font.SysFont(None, 24).render(subtext, True, (200, 200, 200))
        screen.blit(sub_text, (cx - sub_text.get_width() // 2, cy + 40))
    pygame.display.flip()
    if wait_for_key:
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption("Straight Line Task")  # Updated title to match 3-shape game's style
    clock = pygame.time.Clock()

    show_screen(screen, "Straight Line Task", "Press any key to begin")

    canvas = StraightLineCanvas(screen, SCREEN_SIZE)
    recorder = PracticeRecorder()

    # Tutorial trial (generate, spread, rotate, perturb)
    tutorial_pts, tutorial_meta = generate_straight_line_points(scale_factor=1.0)
    tutorial_meta["random_seed"] = RANDOM_SEED
    tutorial_meta = define_rotation(tutorial_meta)

    tutorial_pts, tutorial_meta = adjust_spread_local(tutorial_pts, tutorial_meta)
    # compute px_per_unit for tutorial perturbation to match Canvas scaling
    static_pts_tut = [(r["x"], r["y"]) for _, r in tutorial_pts.iterrows() if
                      int(r["index"]) != tutorial_meta["movable_index"]]
    max_x_tut = max(abs(x) for x, _ in static_pts_tut) if static_pts_tut else 0
    px_per_unit_tut = DESIRED_SCALE if max_x_tut == 0 else min(DESIRED_SCALE,
                                                               (canvas.cx - canvas.dot_radius) / max_x_tut)
    tutorial_pts, tutorial_meta = apply_perturbation_local(tutorial_pts, tutorial_meta, px_per_unit=px_per_unit_tut)

    # Run tutorial; keep tutorial orientation vertical for clarity
    canvas.run_tutorial(tutorial_pts, tutorial_meta, FPS, orientation="vertical")
    show_screen(screen, "Let's begin the task!", wait_for_key=True)

    # Build trial list with proper randomization and balanced orientations & reversals
    movable_idx = NUM_POINTS // 2
    perturbable_idxs = [i for i in range(NUM_POINTS) if i != movable_idx]

    # Prepare a repeated list of perturb indices to reach NUM_TRIALS
    repeats = math.ceil(NUM_TRIALS / len(perturbable_idxs))
    base_indices = []
    for _ in range(repeats):
        base_indices.extend(perturbable_idxs)
    base_indices = base_indices[:NUM_TRIALS]
    random.shuffle(base_indices)

    # Balanced orientations: half vertical, half horizontal (if NUM_TRIALS odd last one will be horizontal)
    half = NUM_TRIALS // 2
    orientations = ["vertical"] * half + ["horizontal"] * (NUM_TRIALS - half)
    random.shuffle(orientations)

    # Balanced reversals: half True (reversed), half False (not reversed)
    half_rev = NUM_TRIALS // 2
    reversals = [True] * half_rev + [False] * (NUM_TRIALS - half_rev)
    random.shuffle(reversals)

    # merge to final trial list: (perturb_idx, orientation, reversed_flag)
    trial_list = list(zip(base_indices, orientations, reversals))

    # Run trials
    for trial_num, (perturb_idx, orientation, reversed_flag) in enumerate(trial_list, start=1):
        # pass the reversed_flag into generation so reversal is controlled by RNG
        pts_df, meta = generate_straight_line_points(scale_factor=1.0, force_reversed=reversed_flag)
        meta["random_seed"] = RANDOM_SEED
        meta = define_rotation(meta)
        # store orientation into meta so recorder picks it up
        meta["orientation"] = orientation

        pts_df, meta = adjust_spread_local(pts_df, meta)
        static_pts = [(r["x"], r["y"]) for _, r in pts_df.iterrows() if int(r["index"]) != meta["movable_index"]]
        max_x = max(abs(x) for x, _ in static_pts) if static_pts else 0
        px_per_unit = DESIRED_SCALE if max_x == 0 else min(DESIRED_SCALE, (canvas.cx - canvas.dot_radius) / max_x)
        pts_df, meta = apply_perturbation_local(pts_df, meta, px_per_unit=px_per_unit, perturb_idx=perturb_idx)
        # run trial with chosen orientation
        final_px, press_sequence, final_record = canvas.run_trial(trial_num, pts_df, meta, FPS, orientation=orientation)
        recorder.record(trial_num, final_px, press_sequence, meta, final_record, pts_df)
        recorder.save()  # Save after each trial to prevent data loss

    recorder.save()
    show_screen(screen, "Task Complete!", "Thank you for participating")
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
