# canvas.py
import pygame
import math
import sys

from geometry import local_spacings
import numpy as np
from practice_feedback import evaluate_feedback, FEEDBACK_DURATION_MS

# ------------------ CONFIG ------------------
# Toggle the in-game movement instruction (upper-left).
# Trial title and submission readiness remain shown.
SHOW_IN_GAME_TEXT = False

# Anchor triangle size (pixels)
ANCHOR_TRIANGLE_SIZE = 10

# Moveable dot color
MOVABLE_DOT_COLOR = (255, 255, 255)  # (0, 150, 255)=blue
# --------------------------------------------


class ExperimenterNavigation(Exception):
    def __init__(self, action, value=0):
        self.action, self.value = action, value


def _anchor_vertices(toward_xy, anchor_xy, size):
    """Triangle points along the adjustment line toward the opposite marker."""
    ax, ay = map(float, anchor_xy)
    tx, ty = map(float, toward_xy)
    angle = math.atan2(ty - ay, tx - ax)
    return [(ax + math.cos(angle + offset) * size,
             ay + math.sin(angle + offset) * size)
            for offset in (0.0, 2 * math.pi / 3, -2 * math.pi / 3)]


def _draw_anchor_triangle(surface, toward_xy, anchor_xy, size, color=(0, 200, 0)):
    pygame.draw.polygon(surface, color, _anchor_vertices(toward_xy, anchor_xy, size))


def screen_ordered_endpoints(positive, negative):
    """Z goes toward smaller screen y; exactly horizontal axes use left for Z."""
    if abs(positive[1] - negative[1]) < 1e-8:
        positive_first = positive[0] < negative[0]
    else:
        positive_first = positive[1] < negative[1]
    return (positive, negative, 1) if positive_first else (negative, positive, -1)


class Canvas:
    def __init__(self, screen, screen_size):
        self.screen = screen
        self.screen_size = screen_size
        self.cx = self.cy = screen_size // 2
        self.font = pygame.font.SysFont(None, 24)
        self.dot_radius = 2
        self.desired_scale = 5

        # –– PIXEL-BASED STEP SIZES ––
        # index 0 = big, 1 = medium, 2 = small
        self.step_sizes = [30, 10, 1]  # Larger to smaller pixel steps
        self.default_step_idx = 0
        self._trial_token = 0
        self.require_fine_submission = True
        self.experimenter_mode = False
        self.practice_feedback_history = []

        self.max_presses = 50
        self.highlight_time = 200
        self.reset_highlight_time = 700

    def rotate_point(self, x, y, cx, cy, cosA, sinA):
        dx, dy = x - cx, y - cy
        return cx + dx * cosA - dy * sinA, cy + dx * sinA + dy * cosA

    def move_towards(self, current, target, step):
        """Move current position towards target by maximum of 'step' pixels"""
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

    def draw_response_guides(self, ref_up, ref_down, dot_position):
        for pos, opposite, key_label in ((ref_up, ref_down, "Z"), (ref_down, ref_up, "/")):
            # Point in the direction of movement toward this endpoint.
            outward = (2*pos[0]-opposite[0], 2*pos[1]-opposite[1])
            _draw_anchor_triangle(self.screen, outward, pos, ANCHOR_TRIANGLE_SIZE)
            dx, dy = opposite[0] - pos[0], opposite[1] - pos[1]
            length = math.hypot(dx, dy)
            ux, uy = (dx / length, dy / length) if length else (0.0, 1.0)
            label = self.font.render(key_label, True, (0, 200, 0))
            label_pos = (pos[0] + 25 * ux - 16 * uy, pos[1] + 25 * uy + 16 * ux)
            self.screen.blit(label, label.get_rect(center=label_pos))
        center = (int(dot_position[0]), int(dot_position[1]))
        if any(math.dist(dot_position, ref) <= ANCHOR_TRIANGLE_SIZE + self.dot_radius + 2
               for ref in (ref_up, ref_down)):
            pygame.draw.circle(self.screen, (0, 0, 0), center, self.dot_radius + 2)
        pygame.draw.circle(self.screen, MOVABLE_DOT_COLOR, center, self.dot_radius)

    def run_tutorial(self, practice_trials, fps):
        """Practice with exactly the experimental renderer and movement rules."""
        lines = [
            "Place the movable dot on the smooth contour suggested by the dots.",
            "Z / Up: move upward along the adjustment line.",
            "/ / Down: move downward along the adjustment line.",
            f"1: fine ({self.step_sizes[2]} px), 2: medium ({self.step_sizes[1]} px), 3: coarse ({self.step_sizes[0]} px).",
            "Changing direction automatically reduces the step size.",
            "Before submitting: use 1-pixel moves and finish in fine mode.",
            "Enter, Space, or Next submits. Close the window to exit.",
            "20 practice trials: shapes gradually become more curved.",
            "After each practice trial, a short message rates your placement.",
            "Practice is not recorded. Press Enter to practice.",
        ]
        self.screen.fill((30, 30, 30))
        for i, line in enumerate(lines):
            label = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(label, (24, 180 + 38 * i))
        pygame.display.flip()
        clock = pygame.time.Clock()
        while True:
            events = pygame.event.get()
            if any(e.type == pygame.QUIT for e in events):
                raise SystemExit
            if any(e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN for e in events):
                break
            clock.tick(fps)
        self.practice_feedback_history = []
        for number, (points, meta) in enumerate(practice_trials, start=1):
            _, _, result = self.run_trial(f"Practice {number}/{len(practice_trials)}", points, meta, fps, record=False)
            index = int(meta['movable_index'])
            baseline = np.column_stack((meta['baseline_x_vals'],meta['baseline_y_vals']))
            spacing_px = float(local_spacings(baseline)[index])*meta['display_scale_px_per_unit']
            feedback = evaluate_feedback(result['response_normal_px'],spacing_px)
            self.practice_feedback_history.append(dict(practice_trial=number, **feedback))
            self.show_practice_feedback(feedback, fps)

    def show_practice_feedback(self, feedback, fps):
        """Fixed-duration feedback; keys cannot skip it or submit the next trial."""
        self.screen.fill((30,30,30))
        colors = {'good':(120,220,140),'moderate':(255,210,110),'needs_adjustment':(255,170,140)}
        label = self.font.render(feedback['sentence'],True,colors[feedback['level']])
        self.screen.blit(label,label.get_rect(center=(self.cx,self.cy)))
        pygame.display.flip()
        start = pygame.time.get_ticks()
        clock = pygame.time.Clock()
        while pygame.time.get_ticks()-start < FEEDBACK_DURATION_MS:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit
            clock.tick(fps)

    def run_trial(self, trial, pts_df, meta, fps, record=True):
        clock = pygame.time.Clock()
        screen = self.screen
        cx, cy = self.cx, self.cy

        theta = math.radians(meta.get("rotation_deg", 0))
        cosA, sinA = math.cos(theta), math.sin(theta)
        mi = int(meta["movable_index"])

        # Displayed static points may be perturbed, but matched +/- trials must
        # use one common display scale.  Derive scale from the unperturbed
        # baseline rather than allowing the perturbation to resize the contour.
        static_pts = [(float(r["x"]), float(r["y"])) for _, r in pts_df.iterrows() if int(r["index"]) != mi]
        baseline_x = [float(value) for value in meta.get("baseline_x_vals", pts_df["x"].tolist())]
        baseline_y = [float(value) for value in meta.get("baseline_y_vals", pts_df["y"].tolist())]
        # Reserve the largest planned displacement at every anchor, identically
        # across all conditions of a baseline, so no perturbed anchor is clipped.
        spacing = local_spacings(np.column_stack((baseline_x, baseline_y)))
        margin = float(meta.get("display_margin_fraction", meta.get("perturb_fraction", 0.0)))
        max_r = max((math.hypot(x, y) + margin * spacing[i]
                     for i, (x, y) in enumerate(zip(baseline_x, baseline_y))), default=0.0)

        safe_radius_px = cx - (self.dot_radius + 20)
        scale = self.desired_scale if max_r <= 1e-9 else min(self.desired_scale, safe_radius_px / max_r)
        if 'requested_display_scale' in meta:
            scale = float(meta['requested_display_scale'])
            # Never silently resize one member of a curvature-matched set.
            bound = max(
                max(math.hypot(x, y) for x,y in zip(baseline_x, baseline_y)),
                max(math.hypot(x, y) for x,y in zip(pts_df['x'], pts_df['y'])),
            )
            if bound * scale > safe_radius_px:
                raise ValueError('Matched-curvature stimulus does not fit this display. '
                                 'Increase the display area or adjust the entire matched set.')

        # store screen positions of all points (recorder-friendly)
        for i, row in pts_df.iterrows():
            sx, sy = self.get_screen_position(float(row["x"]), float(row["y"]), scale, cosA, sinA)
            pts_df.at[i, "screen_x"] = float(sx)
            pts_df.at[i, "screen_y"] = float(sy)

        # Constrain adjustment to the baseline contour normal at the hidden
        # point.  The two green markers are the intersections of that normal
        # with the circular aperture.
        correct_local = (baseline_x[mi], baseline_y[mi])
        normal_x = float(meta.get("target_normal_x", 0.0))
        normal_y = float(meta.get("target_normal_y", 1.0))
        normal_length = math.hypot(normal_x, normal_y)
        if normal_length <= 1e-12:
            normal_x, normal_y = 0.0, 1.0
        else:
            normal_x /= normal_length
            normal_y /= normal_length

        aperture_radius_units = safe_radius_px / scale
        projection = correct_local[0] * normal_x + correct_local[1] * normal_y
        discriminant = max(
            0.0,
            projection * projection
            + aperture_radius_units * aperture_radius_units
            - correct_local[0] * correct_local[0]
            - correct_local[1] * correct_local[1],
        )
        root = math.sqrt(discriminant)
        positive_extent = -projection + root
        negative_extent = -projection - root
        ref_up_local = (
            correct_local[0] + positive_extent * normal_x,
            correct_local[1] + positive_extent * normal_y,
        )
        ref_down_local = (
            correct_local[0] + negative_extent * normal_x,
            correct_local[1] + negative_extent * normal_y,
        )

        ref_up_screen = self.get_screen_position(ref_up_local[0], ref_up_local[1], scale, cosA, sinA)
        ref_down_screen = self.get_screen_position(ref_down_local[0], ref_down_local[1], scale, cosA, sinA)
        # Preserve the analytic response sign even when keyboard endpoints swap.
        baseline_positive_screen, baseline_negative_screen = ref_up_screen, ref_down_screen
        ref_up_screen, ref_down_screen, control_sign = screen_ordered_endpoints(ref_up_screen,ref_down_screen)
        meta['control_up_normal_sign'] = control_sign
        meta['step_sizes_px'] = list(self.step_sizes)
        meta['response_sign_convention'] = 'baseline_normal_positive'

        # A balanced signed starting offset prevents starting-position bias from
        # masquerading as perturbation influence.
        initial_w = float(meta.get("initial_w", 0.5))
        requested_offset_px = meta.get("initial_offset_px", None)
        if requested_offset_px is None:
            requested_offset_units = (0.5 - initial_w) * min(positive_extent, -negative_extent)
        else:
            requested_offset_units = float(requested_offset_px) / scale
        initial_offset_units = max(
            negative_extent + self.dot_radius / scale,
            min(positive_extent - self.dot_radius / scale, requested_offset_units),
        )
        init_local_x = correct_local[0] + initial_offset_units * normal_x
        init_local_y = correct_local[1] + initial_offset_units * normal_y

        dot_screen_pos = self.get_screen_position(init_local_x, init_local_y, scale, cosA, sinA)

        # px_per_unit used for perturb; record into meta for logging
        px_per_unit = scale
        meta["px_per_unit"] = float(px_per_unit)
        meta["display_scale_px_per_unit"] = float(px_per_unit)
        meta["screen_size_px"] = int(self.screen_size)
        if meta.get("perturb_units", "") not in ("", None):
            meta["perturb_pixels"] = float(meta["perturb_units"]) * float(px_per_unit)

        # --- RECORD initial local (math) and pixel positions into meta so recorder can save them ---
        meta["initial_w"] = float(initial_w)
        meta["initial_math_x"] = float(init_local_x)
        meta["initial_math_y"] = float(init_local_y)
        meta["initial_x_px"] = float(dot_screen_pos[0])
        meta["initial_y_px"] = float(dot_screen_pos[1])
        meta["initial_movable_x_math"] = float(init_local_x)
        meta["initial_movable_y_math"] = float(init_local_y)
        meta["initial_movable_x_px"] = float(dot_screen_pos[0])
        meta["initial_movable_y_px"] = float(dot_screen_pos[1])

        meta["actual_initial_offset_px"] = float(initial_offset_units * scale)

        # also record the movable (true) math coordinates (useful for replay/analysis)
        meta["movable_x_math"] = float(pts_df.loc[mi, "x"])
        meta["movable_y_math"] = float(pts_df.loc[mi, "y"])

        # The hidden point's unperturbed curve coordinate is the correct answer
        # for every family.  The previous center-of-screen shortcut was wrong
        # for all curved non-circle trials.
        correct_screen_pos = self.get_screen_position(
            correct_local[0], correct_local[1], scale, cosA, sinA
        )

        # save correct position (screen px) and math coords (where meaningful) into meta
        meta["correct_x_px"] = float(correct_screen_pos[0])
        meta["correct_y_px"] = float(correct_screen_pos[1])
        try:
            meta["correct_x_math"] = float(correct_local[0])
            meta["correct_y_math"] = float(correct_local[1])
        except Exception:
            meta["correct_x_math"] = ""
            meta["correct_y_math"] = ""

        move_count = 0
        # Separate reversal counters: one for game logic, one for recording
        game_reversals = 0  # Used for step size calculation (resets with 1-2-3)
        cumulative_reversals = 0  # Used for recording (persists through resets)
        last_btn = None
        manual_step_idx = self.default_step_idx
        meta['initial_step_px'] = self.step_sizes[self.default_step_idx]
        meta['input_version'] = '2026-10-04_screen_up_down_v2'
        self._trial_token += 1
        trial_token = self._trial_token
        held = pygame.key.get_pressed()
        blocked_confirm_keys = {key for key in (pygame.K_SPACE, pygame.K_RETURN) if held[key]}
        presses = []
        btn_rect = pygame.Rect(self.screen_size - 110, 10, 100, 32)
        in_trial = True
        trial_start_ms = pygame.time.get_ticks()
        fine_moves = blocked_submissions = 0
        jump_text = None

        while in_trial:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif ev.type == pygame.KEYUP:
                    blocked_confirm_keys.discard(ev.key)

                elif ev.type == pygame.KEYDOWN:
                    if self.experimenter_mode:
                        if jump_text is not None:
                            if ev.key == pygame.K_ESCAPE:
                                jump_text = None
                            elif ev.key == pygame.K_BACKSPACE:
                                jump_text = jump_text[:-1]
                            elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                                if jump_text:
                                    raise ExperimenterNavigation('absolute', int(jump_text)-1)
                                jump_text = None
                            elif getattr(ev, 'unicode', '').isdigit() and len(jump_text)<6:
                                jump_text += ev.unicode
                            continue
                        if ev.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                            raise ExperimenterNavigation('relative', {
                                pygame.K_LEFT:-1, pygame.K_RIGHT:1,
                                pygame.K_PAGEUP:-10, pygame.K_PAGEDOWN:10}[ev.key])
                        if ev.key in (pygame.K_HOME, pygame.K_END):
                            raise ExperimenterNavigation('absolute', 0 if ev.key==pygame.K_HOME else 10**9)
                        if ev.key == pygame.K_g:
                            jump_text = ''
                            continue
                        if ev.key == pygame.K_c:
                            dot_screen_pos = correct_screen_pos
                            continue
                    if ev.key == pygame.K_ESCAPE:
                        continue  # Ignore accidental Esc; window close still exits.
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
                        # Record with cumulative reversals
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
                        # Record with cumulative reversals
                        presses.append(("step_big", cumulative_reversals))
                        pygame.draw.rect(screen, (50, 50, 50), (self.screen_size - 340, 50, 320, 40))
                        lbl = self.font.render("Step set to BIG (3)", True, (255, 255, 255))
                        screen.blit(lbl, (self.screen_size - 340 + 10, 50 + 6))
                        pygame.display.flip()
                        pygame.time.delay(self.highlight_time)
                        continue

                    # movement keys - added up/down arrows to match 3-shape game
                    current_btn = None
                    target = None
                    if ev.key == pygame.K_z or ev.key == pygame.K_UP:
                        current_btn = "up"
                        target = ref_up_screen
                    elif ev.key == pygame.K_SLASH or ev.key == pygame.K_DOWN:
                        current_btn = "down"
                        target = ref_down_screen

                    # Allow space/enter to act like clicking "Next"
                    if ev.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if ev.key in blocked_confirm_keys:
                            continue
                        blocked_confirm_keys.add(ev.key)
                        # Simulate clicking the Next button
                        ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
                            "pos": btn_rect.center, "button": 1, "trial_token": trial_token})
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
                        previous_pos = dot_screen_pos
                        dot_screen_pos = self.move_towards(dot_screen_pos, target, step_px)
                        if step_px == 1 and math.dist(previous_pos, dot_screen_pos) > 1e-8:
                            fine_moves += 1
                        move_count += 1
                        # Record with cumulative reversals
                        presses.append((current_btn, cumulative_reversals))
                        last_btn = current_btn

                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if getattr(ev, 'trial_token', trial_token) != trial_token:
                        continue
                    if btn_rect.collidepoint(ev.pos):
                        current_step = self.step_sizes[min(2, manual_step_idx + min(game_reversals, 2))]
                        if self.require_fine_submission and not self.experimenter_mode and (current_step != 1 or fine_moves == 0):
                            blocked_submissions += 1
                            continue
                        # Timestamp the response before visual confirmation delay.
                        response_time_ms = pygame.time.get_ticks() - trial_start_ms
                        # finalize
                        pygame.draw.rect(screen, (0, 200, 0), btn_rect)
                        lbl = self.font.render("Next", True, (255, 255, 255))
                        screen.blit(lbl, lbl.get_rect(center=btn_rect.center))
                        pygame.display.flip()
                        pygame.time.delay(self.highlight_time)

                        # ------------------- NEW: rotation-aware signed vertical distance -------------------
                        # screen-space vector from correct -> dot (pixels)
                        dot_x, dot_y = float(dot_screen_pos[0]), float(dot_screen_pos[1])
                        corr_x, corr_y = float(correct_screen_pos[0]), float(correct_screen_pos[1])
                        diff_x, diff_y = dot_x - corr_x, dot_y - corr_y

                        # Baseline-normal sign stays compatible with old data;
                        # keyboard-up sign is separately recorded below.
                        up_x = float(baseline_positive_screen[0]) - float(baseline_negative_screen[0])
                        up_y = float(baseline_positive_screen[1]) - float(baseline_negative_screen[1])
                        up_len = math.hypot(up_x, up_y)

                        if up_len == 0:
                            # fallback (extremely unlikely): use screen vertical signed px
                            signed_vertical_px = float(corr_y - dot_y)
                        else:
                            unit_up_x = up_x / up_len
                            unit_up_y = up_y / up_len
                            # projection of (dot - correct) onto unit_up:
                            # positive => along the original baseline normal
                            signed_vertical_px = float(diff_x * unit_up_x + diff_y * unit_up_y)

                        # Store canonical and screen-up response signs separately.
                        final_record = {
                            'fine_moves': fine_moves,
                            'submission_step_px': current_step,
                            'blocked_submissions': blocked_submissions,
                            "total_moves": move_count,
                            "final_x": float(dot_x),
                            "final_y": float(dot_y),
                            "pixel_distance": float(signed_vertical_px),  # keep name for backward compatibility
                            "pixel_distance_signed": float(signed_vertical_px),
                            "pixel_distance_abs": float(abs(signed_vertical_px)),
                            "response_normal_px": float(signed_vertical_px),
                            "response_normal_units": float(signed_vertical_px / scale),
                            "response_screen_up_px": float(signed_vertical_px * control_sign),
                            "reaction_time_ms": int(response_time_ms),
                            "correct_x_px": float(corr_x),
                            "correct_y_px": float(corr_y),
                            "ref_up_x_px": float(ref_up_screen[0]),
                            "ref_up_y_px": float(ref_up_screen[1]),
                            "ref_down_x_px": float(ref_down_screen[0]),
                            "ref_down_y_px": float(ref_down_screen[1]),
                        }
                        in_trial = False
                        break

            # Draw frame (unchanged)
            screen.fill((30, 30, 30))
            pygame.draw.circle(screen, (0, 0, 0), (cx, cy), cx)

            # Trial info
            trial_info = self.font.render(f"Trial {trial}", True, (255, 255, 255))
            screen.blit(trial_info, (20, 20))

            # Instructions - matched to 3-shape game (shown only if config True)
            if SHOW_IN_GAME_TEXT:
                inst1 = self.font.render("Press 'z' or '/' to move.", True, (200, 200, 200))
                screen.blit(inst1, (20, 50))

            # Static dots
            for lx, ly in static_pts:
                sx, sy = self.get_screen_position(lx, ly, scale, cosA, sinA)
                pygame.draw.circle(screen, (255, 255, 255), (int(sx), int(sy)), self.dot_radius)

            # Next button
            pygame.draw.rect(screen, (50, 50, 50), btn_rect)
            lbl = self.font.render("Next", True, (200, 200, 200))
            screen.blit(lbl, lbl.get_rect(center=btn_rect.center))

            # Draw response dot last so even an endpoint start stays visible.
            self.draw_response_guides(ref_up_screen, ref_down_screen, dot_screen_pos)

            current_step = self.step_sizes[min(2, manual_step_idx + min(game_reversals, 2))]
            if self.experimenter_mode:
                answer = tuple(int(v) for v in correct_screen_pos)
                pygame.draw.circle(screen, (255, 100, 100), answer, 7, 2)
                pygame.draw.line(screen, (255,100,100), (answer[0]-9,answer[1]), (answer[0]+9,answer[1]), 1)
                details = [
                    f"EXPERIMENTER: {meta['curve_family']} | {meta.get('stimulus_set','original')} | rep {meta.get('repetition',1)}",
                    f"{meta.get('curvature_level','')} | {meta.get('condition_type','')} | {meta.get('perturbation_pattern','')} | target {mi}",
                    'Red circle: reference answer. C: place dot there. No data saved.',
                    'Left/Right: previous/next | PgUp/PgDn: skip 10 | Home/End: first/last',
                    'G: jump to trial | Enter/Space/Next: advance | Close window: exit',
                ]
                for i, line in enumerate(details):
                    screen.blit(self.font.render(line, True, (255,210,130)), (12, 50+i*25))
                if jump_text is not None:
                    screen.blit(self.font.render(f'Go to trial: {jump_text}_  (Enter confirms)',True,(255,255,0)),(15,self.screen_size-80))
            else:
                can_proceed = not self.require_fine_submission or (current_step == 1 and fine_moves > 0)
                text = 'Ready to proceed' if can_proceed else 'Cannot proceed yet'
                color = (120, 220, 140) if can_proceed else (255, 190, 80)
                screen.blit(self.font.render(text, True, color), (20, self.screen_size-40))

            pygame.display.flip()
            clock.tick(fps)

        # return in same style as 3-shape game
        return (float(final_record["final_x"]), float(final_record["final_y"])), presses, final_record
