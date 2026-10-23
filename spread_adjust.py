# spread_adjust.py
import random

def adjust_spread(pts_df, meta, x_offset_min=2.0, x_offset_max=3.0, function_type=None):
    """
    Apply a small random horizontal offset to ALL points (including the movable point),
    intended to vary the *screen placement* without changing the underlying function type.

    Supports: parabola, cubic, line, quartic, circle,quintic
    """

    if function_type is None:
        function_type = meta.get("function_type", None)
    if function_type is None:
        raise ValueError("adjust_spread requires function_type either as arg or in meta['function_type'].")

    function_type = str(function_type).lower().strip()

    # ------------------ Circle handling (keep your existing circle logic) ------------------
    # If your previous spread_adjust.py already had special circle behavior, keep it.
    # Here we implement a safe default: circle -> no x-offset jitter, because it can
    # distort the arc if you treat points independently.
    if function_type == "circle":
        meta["x_offset_applied"] = 0.0
        return pts_df, meta

    # ------------------ Generic curve handling ------------------
    # For parabola/cubic/line/quartic, apply the same x-offset shift to all points.
    if function_type in ("parabola", "cubic", "line", "quartic", "quintic"):
        # choose one shared offset per trial so the whole curve shifts together
        if x_offset_min is None or x_offset_max is None:
            x_off = 0.0
        else:
            lo = float(min(x_offset_min, x_offset_max))
            hi = float(max(x_offset_min, x_offset_max))
            x_off = random.uniform(lo, hi) * random.choice([-1.0, 1.0])

        # apply to all x positions
        if "x" in pts_df.columns:
            pts_df["x"] = pts_df["x"].astype(float) + float(x_off)

        # store for debugging / recording
        meta["x_offset_applied"] = float(x_off)
        return pts_df, meta

    # ------------------ Anything else is unsupported ------------------
    raise ValueError(f"Unsupported function_type: {function_type}")
