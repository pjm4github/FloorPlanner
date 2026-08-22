"""Pure geometry, formatting/parsing, and generic item-stacking helpers.

Nothing here knows about WallItem/RoomItem or the scene's contents beyond the
duck-typed attributes it is handed, so it sits at the bottom of the dependency
graph (only `config` for the snap settings).
"""
import math
import re

from PyQt6.QtCore import QLineF, QPointF

from floorplanner.config import SETTINGS, SNAP_STEP

__all__ = [
    "fmt_ftin", "fmt_in", "fmt_ft2", "parse_feet",
    "grid_snap", "wall_snap", "wall_snap_len", "parse_wwhh",
    "line_intersection", "dist_point_segment", "heading_deg",
    "bring_to_front", "send_to_back", "add_front_back_actions",
    "handle_front_back", "axis_wall_intersection",
]


def fmt_ftin(inches: float) -> str:
    """Format a length in inches as feet-and-inches, e.g. 30.5 -> 2'-6 1/2"."""
    sign = "-" if inches < 0 else ""
    v = abs(inches)
    ft = int(v // 12)
    rem = round((v - 12 * ft) * 2) / 2          # nearest half inch
    if rem >= 12:
        ft += 1
        rem = 0
    if rem == int(rem):
        rem_s = str(int(rem))
    else:
        rem_s = f"{int(rem)} 1/2"
    return f"{sign}{ft}'-{rem_s}\""


def fmt_in(inches: float) -> str:
    """Format a length as whole/half inches, e.g. 84 -> 84\"  (30.5 -> 30 1/2\")."""
    sign = "-" if inches < 0 else ""
    v = round(abs(inches) * 2) / 2          # nearest half inch
    whole = int(v)
    frac = v - whole
    s = str(whole) if frac == 0 else f"{whole} 1/2"
    return f'{sign}{s}"'


def fmt_ft2(inches: float) -> str:
    """Format a length/coordinate given in inches as DECIMAL feet, FIXED at
    2 decimal places, e.g. 148.14 -> "12.34" (feet). No unit suffix --
    callers that need one append it, since a coordinate pair usually wants
    it once, not per axis.

    Fixed, not significant-figure, on purpose (0065-ruling.md sec4): a
    coordinate's useful precision does not scale with its magnitude -- an
    inch is an inch at 8ft and at 140ft -- so resolution must not depend on
    where a wall happens to sit. The prior `.3g` gave only 1ft resolution
    (up to 6" of display error) on the 11.5% of this project's own corpus
    vertices at or above 100ft."""
    return f"{inches / 12.0:.2f}"


def heading_deg(p1: QPointF, p2: QPointF):
    """The wall's own compass heading in degrees, `[0, 360)`, `p1` -> `p2`.
    None for a degenerate (coincident) pair -- no direction is defined.

    Unlike `wall_angle_deviation_deg` (validate.py), this is the actual
    heading, not deviation from the nearest axis: 90 and 270 are both
    reported exactly, not folded together. That is deliberate -- it is for
    a human reading one wall's own direction, not a corpus-wide drift
    census, and folding a wall pointing east onto one pointing west would
    misinform exactly the reader it is for."""
    dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
    if math.hypot(dx, dy) < 1e-9:
        return None
    return math.degrees(math.atan2(dy, dx)) % 360.0


def parse_feet(text) -> float:
    """Parse a length given in feet into INCHES.

    Accepts:  12   12.5   12'   12.5'   12'6   12'6"   12' 6"   12'-6"
    (plain numbers are feet; 6" alone is inches).  Raises ValueError on
    anything else."""
    s = str(text).strip().replace("’", "'").replace("”", '"')
    if not s:
        raise ValueError("empty length")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*'\s*(?:-?\s*"
                     r"(\d+(?:\.\d+)?)\s*\"?)?", s)
    if m:
        return float(m.group(1)) * 12.0 + float(m.group(2) or 0.0)
    m = re.fullmatch(r'(\d+(?:\.\d+)?)\s*"', s)
    if m:
        return float(m.group(1))
    m = re.fullmatch(r"\d+(?:\.\d+)?", s)
    if m:
        return float(s) * 12.0
    raise ValueError(f"cannot parse length {text!r} "
                     "(use 12, 12.5, 12.5' or 12'6\")")


def grid_snap(p: QPointF, step: float = SNAP_STEP) -> QPointF:
    return QPointF(round(p.x() / step) * step, round(p.y() / step) * step)


def wall_snap(p: QPointF) -> QPointF:
    """Snap a wall centreline point to the configured on-centre grid."""
    return grid_snap(p, SETTINGS["wall_snap_in"])


def wall_snap_len(s: float) -> float:
    """Snap a distance along a wall axis to the configured grid."""
    step = SETTINGS["wall_snap_in"]
    return round(s / step) * step


def parse_wwhh(code: str):
    """Parse a size code -> (width_in, height_in). Raises ValueError.

    4 digits = WWHH (3280 = 32" x 80"); widths of 100" or more use
    5 digits WWWHH (10884 = 108" x 84") or 6 digits WWWHHH."""
    code = code.strip()
    if not code.isdigit() or len(code) not in (4, 5, 6):
        raise ValueError('Size must be digits "WWHH" (e.g. 3280 = 32" x '
                         '80"); wide openings use WWWHH (e.g. 10884 = '
                         '108" x 84").')
    split = 2 if len(code) == 4 else 3
    w, h = int(code[:split]), int(code[split:])
    if w < 8:
        raise ValueError("Width must be at least 8 inches.")
    if h < 8:
        raise ValueError("Height must be at least 8 inches.")
    return float(w), float(h)


def line_intersection(p: QPointF, u: QPointF, q: QPointF, v: QPointF):
    """Intersection of the line through `p` with direction `u` and the line
    through `q` with direction `v`; None when parallel."""
    den = u.x() * v.y() - u.y() * v.x()
    if abs(den) < 1e-9:
        return None
    wx, wy = q.x() - p.x(), q.y() - p.y()
    s = (wx * v.y() - wy * v.x()) / den
    return QPointF(p.x() + u.x() * s, p.y() + u.y() * s)


def dist_point_segment(p: QPointF, a: QPointF, b: QPointF) -> float:
    """Shortest distance from point `p` to segment `a`-`b`."""
    abx, aby = b.x() - a.x(), b.y() - a.y()
    L2 = abx * abx + aby * aby
    if L2 < 1e-9:
        return QLineF(p, a).length()
    t = ((p.x() - a.x()) * abx + (p.y() - a.y()) * aby) / L2
    t = max(0.0, min(1.0, t))
    return QLineF(p, QPointF(a.x() + abx * t, a.y() + aby * t)).length()


# ----------------------------------------------------------------------------
# Stacking order: "Bring to front" / "Send to back" for any item's menu
# ----------------------------------------------------------------------------
def bring_to_front(item):
    """Stack `item` above every other scene item (transient -- z is not saved)."""
    sc = item.scene()
    if sc is None:
        return
    top = max((it.zValue() for it in sc.items() if it is not item),
              default=0.0)
    item.setZValue(top + 1.0)


def send_to_back(item):
    """Stack `item` below every other scene item."""
    sc = item.scene()
    if sc is None:
        return
    bot = min((it.zValue() for it in sc.items() if it is not item),
              default=0.0)
    item.setZValue(bot - 1.0)


def add_front_back_actions(menu):
    """Append the stacking actions to a context menu; returns (front, back)."""
    menu.addSeparator()
    return (menu.addAction("Bring to front"), menu.addAction("Send to back"))


def handle_front_back(item, chosen, a_front, a_back) -> bool:
    """Apply a chosen stacking action; True if it was one of them."""
    if chosen is a_front:
        bring_to_front(item)
        return True
    if chosen is a_back:
        send_to_back(item)
        return True
    return False


def axis_wall_intersection(target, anchor: QPointF, through: QPointF):
    """Where the ray anchor->through crosses `target`'s centreline
    (clamped to the segment), or None when parallel or degenerate.

    Snapping a wall end to this point (instead of the perpendicular
    projection) keeps the snapped wall's own direction intact."""
    dx, dy = through.x() - anchor.x(), through.y() - anchor.y()
    if math.hypot(dx, dy) < 1e-9:
        return None
    wx, wy = target.p2.x() - target.p1.x(), target.p2.y() - target.p1.y()
    den = dx * wy - dy * wx
    if abs(den) < 1e-9:
        return None
    ex, ey = target.p1.x() - anchor.x(), target.p1.y() - anchor.y()
    t = (ex * wy - ey * wx) / den
    if t <= 1e-9:
        return None                       # crossing is behind the anchored end
    s = max(0.0, min(1.0, (ex * dy - ey * dx) / den))
    return QPointF(target.p1.x() + wx * s, target.p1.y() + wy * s)
