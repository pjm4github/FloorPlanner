"""Roof-family graphics items: RoofItem, plus the ridge-sketch tool's own
eaves-reference geometry.

0139-ruling.md's roofline plan, R1's `Roof` document record
(`floorplanner/design/model.py`); this module is R2's first UI writer.
Sits above walls (it finds an eaves wall to size its plan footprint), same
layer as rooms.py -- both load after walls, before items."""
import math
from typing import NamedTuple

from PyQt6 import sip
from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import QDialog, QGraphicsItem, QMenu

from floorplanner.config import *  # noqa: F401
from floorplanner.geometry import *  # noqa: F401
from floorplanner.roofclip import (
    Pt, _contains, compose_building, entry_along, footprint_polygon, meet_along,
    rising_reach, surface_height,
)
from floorplanner.walls import WallItem

# how parallel a wall must run to the ridge to count as its eaves reference
EAVES_SEARCH_ANGLE_TOL_DEG = 20.0
# used only when no qualifying wall exists nearby (an isolated ridge sketch)
DEFAULT_HALF_SPAN_IN = 144.0


def eaves_span_from_wall(p1: QPointF, p2: QPointF, wall: WallItem) -> float:
    """The perpendicular reach from ridge `p1`-`p2` to `wall`'s centerline --
    what an interactive eaves pick directly measures, no search needed."""
    mid = QPointF((wall.p1.x() + wall.p2.x()) / 2.0,
                  (wall.p1.y() + wall.p2.y()) / 2.0)
    return dist_point_segment(mid, p1, p2)


def eaves_span_to_ridge_line(p1: QPointF, p2: QPointF, wall: WallItem) -> float:
    """The PERPENDICULAR distance from `wall`'s centreline midpoint to the
    ridge's infinite LINE -- the span as the roof planes actually use it
    (`RoofItem._eave_ends` offsets the eave line perpendicular to the
    ridge). `eaves_span_from_wall` measures to the ridge SEGMENT instead:
    the same number while the wall's midpoint projects inside the ridge,
    but the hypotenuse to the nearer ridge END once it projects past one
    -- a ridge sketched shorter than its wall, or a 45deg wing's ridge
    running off the wing, both inflate the span and land the eave line
    further from the wall than the overhang says. Patrick's own check of
    R4b ("the overhang must be orthogonal to the walls ... 24 inches from
    that wall") is exactly this: measured here along the wall's normal,
    which for an eaves wall parallel to the ridge IS the ridge's normal.
    The segment form stays for `nearest_eaves_wall` (the pre-R4a
    migration's receipt is that it reproduces old loads exactly)."""
    mid = QPointF((wall.p1.x() + wall.p2.x()) / 2.0,
                  (wall.p1.y() + wall.p2.y()) / 2.0)
    dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
    ln = math.hypot(dx, dy)
    if ln < 1e-9:
        return QLineF(mid, p1).length()
    return abs((mid.x() - p1.x()) * dy - (mid.y() - p1.y()) * dx) / ln


def _roofs_editable() -> bool:
    return bool(SETTINGS.get("edit_roofs", True))


def _roof_hittable(roof) -> bool:
    """R6.c (0197-ruling.md sec5; D67's own rule: "an inactive floor may be
    drawn; it may not be hit-tested, selected, banded, or dragged"): a roof
    answers a geometric query only while roofs are editable AND its level
    is the one being edited. A roof of another level drawn over this plan
    (R6.a's covering roof, or any ghosted floor's) is "shown, not
    editable" exactly as `edit_roofs` off is, and for the same reason
    `setEnabled(False)` is not enough: a manual scan (`scene.items(pt)`)
    sees a disabled item. Measured before this (`docs/evidence/
    r6c-roof-tool-levels-probe.before.txt`): a ridge pressed on a lower
    level's ghosted roof line never started."""
    return _roofs_editable() and floor_display_mode(roof.floor) == "active"


def apply_roof_visibility(scene):
    """Show roof / Edit roof (0145-ruling.md sec2), layered on each roof's
    OWN floor display mode -- recomputed fresh here rather than read off
    the item's current visible/enabled state, so re-enabling the document
    switches always recovers correctly regardless of call order against
    `apply_floor_visibility` (config.py), which this always follows
    (`levels.py`'s `_sync_floor_state`).

    Three states. HIDDEN (`show_roofs` off): `setVisible(False)` is enough
    on its own -- Qt excludes an invisible item from `scene.items()`
    entirely, so it is absent from every hit census, automatic or manual.
    SHOWN, NOT EDITABLE (`edit_roofs` off): stays painted, but
    `setEnabled(False)` stops Qt's own automatic event dispatch, AND
    `RoofItem`/`RoofEndMarkerItem`'s own `shape()` empties out in that
    same state (see their docstrings) so manual scans
    (`RoomItem._outranked_at`, the ridge-sketch tool's own marker
    pre-check) never see it either -- "every mouse/key event reaches the
    floor tools exactly as if no roof existed" needs both, since only
    `shape()` governs a geometric query, not `setEnabled` alone. A roof
    that stops being editable is deselected, so no stray selection outline
    survives a switch it can no longer be clicked to clear."""
    if scene is None:
        return
    show = bool(SETTINGS.get("show_roofs", True))
    edit = _roofs_editable()
    active = active_floor()
    for it in scene.items():
        if not isinstance(it, RoofItem):
            continue
        mode = floor_display_mode(it.floor)
        # R6.a (0197-ruling.md sec4, Patrick's own display rule): this
        # level's roofs draw solid; a roof on ANY other level that covers
        # this level's rooms draws ghosted -- even with "show other floors"
        # off, since the roof over a room is a fact about that room's
        # plan. paint() already ghosts every non-active floor's roof; this
        # only decides whether it is shown at all. Never editable from
        # another level (R6.c owns the roof tool across levels).
        covering = (mode == "hidden" and it.floor != active
                    and roof_covers_floor(scene, it, active))
        it.setVisible((mode != "hidden" or covering) and show)
        it.setEnabled(mode == "active" and show and edit)
        if not edit:
            it.setSelected(False)


def roof_covers_floor(scene, roof, floor) -> bool:
    """R6.a (0197-ruling.md sec4): does `roof`'s footprint (eaves and
    overhang, the region it paints) cover a room on `floor`? The SAME
    overlap rule R4b's `bound_eaves_height` uses to say which rooms a roof
    sits on -- an intersection thicker than `_COVER_MIN_IN` on both axes,
    so a shared wall face's sliver is not coverage -- reused rather than
    a second predicate that could disagree with it (the ruling's own
    reason). Rooms on `floor` only; nothing about heights: whether the
    roof is above or below that level is R6.b's composition, not the
    plan's display rule."""
    from floorplanner.rooms import RoomItem  # late (peer layer)
    if scene is None or sip.isdeleted(roof):
        return False
    fp = QPainterPath()
    fp.addPolygon(QPolygonF([QPointF(p.x(), p.y())
                             for p in footprint_polygon(roof)]))
    fp.closeSubpath()
    for it in scene.items():
        if (not isinstance(it, RoomItem) or sip.isdeleted(it)
                or getattr(it, "floor", None) != floor):
            continue
        inter = it.path.intersected(fp)
        br = inter.boundingRect()
        if (not inter.isEmpty() and br.width() >= _COVER_MIN_IN
                and br.height() >= _COVER_MIN_IN):
            return True
    return False


def nearest_eaves_wall(scene, p1: QPointF, p2: QPointF, floor, exclude=None):
    """The wall on `floor` whose centerline runs closest to parallel with
    ridge `p1`-`p2` and sits nearest to it -- the ONE-NUMBER search
    `design/bridge.py`'s pre-R4a migration still reproduces exactly (a
    loaded old roof must come back with the geometry it always had). A
    fresh sketch no longer uses it: `eaves_spans_per_side` (R4b) measures
    each side to its own wall. Before R4a (0154-ruling.md) this was also
    how a LOADED roof found its span every time, since the field did not
    exist in the document at all; as of R4a a loaded roof's `span_in`
    comes from the document once it has one, and this search only runs
    again for a roof saved before R4a existed (`design/bridge.py`'s own
    migration) or a genuinely new sketch. Returns `(wall_or_None,
    span_in)`; `span_in` falls back to `DEFAULT_HALF_SPAN_IN` when nothing
    on the floor qualifies."""
    ang = heading_deg(p1, p2)
    if ang is None:
        return None, DEFAULT_HALF_SPAN_IN
    ang %= 180.0
    best, bestd = None, None
    for w in scene.items():
        if not isinstance(w, WallItem) or w is exclude or w.floor != floor:
            continue
        wang = heading_deg(w.p1, w.p2)
        if wang is None:
            continue
        wang %= 180.0
        d_ang = abs(wang - ang)
        d_ang = min(d_ang, 180.0 - d_ang)
        if d_ang > EAVES_SEARCH_ANGLE_TOL_DEG:
            continue
        d = eaves_span_from_wall(p1, p2, w)
        if bestd is None or d < bestd:
            best, bestd = w, d
    return best, (bestd if bestd is not None else DEFAULT_HALF_SPAN_IN)


def ridge_side(p1: QPointF, p2: QPointF, pt: QPointF) -> int:
    """Which side of ridge `p1`-`p2` the point `pt` lies on, as a
    `span_in`/`overhang_in` index: 0 = LEFT (the ridge direction's own
    +90deg-rotated normal, `RoofItem`'s convention), 1 = RIGHT."""
    dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
    nx, ny = -dy, dx
    perp = (pt.x() - p1.x()) * nx + (pt.y() - p1.y()) * ny
    return 0 if perp >= 0.0 else 1


def eaves_spans_per_side(scene, p1: QPointF, p2: QPointF, floor, picked=None):
    """`[left, right]`: the span to the eaves wall on EACH side of ridge
    `p1`-`p2` -- Patrick's own check of R4b found the one-number pick
    (mirrored to the far side) makes a ridge sketched a few inches
    off-centre come out with a lopsided footprint, the far side's eaves
    line landing inside its wall. So: the `picked` wall (the eaves click)
    sets its own side; the other side takes the nearest parallel wall
    that lies ACROSS the ridge from it (`nearest_eaves_wall`'s own
    parallel/nearest rule, restricted to that side); a side with no such
    wall mirrors the other side, which is exactly the pre-R4b result --
    every roof over a single wall, or over none, is unchanged by this.

    With this, "overhang 24in" reads as 24in past EACH wall's centreline
    in the plan (two 12in grid lines), on both sides -- `span_in` is the
    ridge-to-wall-centreline distance, so the drawn eave sits at
    `span + overhang` from the ridge, i.e. `overhang` past the wall."""
    spans = [None, None]
    picked_side = None
    if picked is not None:
        mid = QPointF((picked.p1.x() + picked.p2.x()) / 2.0,
                      (picked.p1.y() + picked.p2.y()) / 2.0)
        picked_side = ridge_side(p1, p2, mid)
        spans[picked_side] = eaves_span_to_ridge_line(p1, p2, picked)
    ang = heading_deg(p1, p2)
    if ang is not None and scene is not None:
        ang %= 180.0
        for w in scene.items():
            if not isinstance(w, WallItem) or w is picked or w.floor != floor:
                continue
            wang = heading_deg(w.p1, w.p2)
            if wang is None:
                continue
            wang %= 180.0
            d_ang = abs(wang - ang)
            d_ang = min(d_ang, 180.0 - d_ang)
            if d_ang > EAVES_SEARCH_ANGLE_TOL_DEG:
                continue
            mid = QPointF((w.p1.x() + w.p2.x()) / 2.0,
                          (w.p1.y() + w.p2.y()) / 2.0)
            side = ridge_side(p1, p2, mid)
            if side == picked_side:
                continue                  # the picked wall owns its side
            d = eaves_span_to_ridge_line(p1, p2, w)
            if d < 1e-6:
                continue                  # a wall under the ridge is no eaves
            if spans[side] is None or d < spans[side]:
                spans[side] = d
    if spans[0] is None and spans[1] is None:
        return [DEFAULT_HALF_SPAN_IN, DEFAULT_HALF_SPAN_IN]
    if spans[0] is None:
        spans[0] = spans[1]
    if spans[1] is None:
        spans[1] = spans[0]
    return [float(spans[0]), float(spans[1])]


# ---------------------------------------------------------------------------
# R3b (0145-ruling.md sec3): the roof-clip dotted line
# ---------------------------------------------------------------------------
# "affected walls should show a dotted line where any part of the roof is
# clipping the full height of the room underneath" -- this needs the same
# roof-plane-height-over-a-run math R3 built for fp3d.build_model, done here
# in plan space (no y-flip, no Qt boundary to keep clear of -- this module
# already imports PyQt6) rather than shared with it.

_CLIP_EPS_IN = 1e-6      # geometric tolerance, inches
_CLIP_SLOPE_EPS = 1e-6   # below this, treat a roof as flat (avoid /0)


def _room_ceiling_at(scene, pt: QPointF, floor):
    """The `ceiling_height_in` of whichever room on `floor` contains `pt`,
    or None if none does -- same room-lookup `items.py`'s
    `StairsItem._ceiling_height` already uses, reused rather than
    re-derived (late import: rooms.py is roofs.py's own same-layer peer,
    per this module's docstring, so importing it here rather than at
    module level keeps that peer relationship a fact about load order,
    not just about who happens to import whom first).

    `sip.isdeleted` guards every item `scene.items()` returns: `paint()`
    (this function's only caller, via `roof_clip_spans`) can run while a
    scene is mid-teardown (`clear_plan`'s `scene.clear()`), and a stale
    Python wrapper around an already-destroyed C++ `RoomItem` raises the
    moment anything touches it -- the same guard `walls.py`'s own
    `itemChange` already needs for the same reason."""
    from floorplanner.rooms import RoomItem  # late (peer layer)
    for it in scene.items():
        if (isinstance(it, RoomItem) and not sip.isdeleted(it)
                and getattr(it, "floor", None) == floor
                and it.path.contains(pt)):
            return float(it.properties.get(
                "ceiling_height_in", DEFAULT_ROOM_PROPS["ceiling_height_in"]))
    return None


def _wall_ceiling_in(scene, wall) -> float:
    """The ceiling height a clip line is measured against: the lower of
    whatever room(s) the wall borders (tested a little past each face, not
    on the centreline itself -- a room's own outline stops at the wall's
    INTERIOR face, so the centreline point is never actually inside one),
    falling back to `DEFAULT_ROOM_PROPS`'s own default when neither side
    resolves to a room (an exterior wall with nothing built against it,
    or an unenclosed sketch)."""
    mid = QPointF((wall.p1.x() + wall.p2.x()) / 2.0,
                  (wall.p1.y() + wall.p2.y()) / 2.0)
    u = wall.unit()
    n = QPointF(-u.y(), u.x())
    reach = wall.t / 2.0 + 6.0
    found = []
    for sign in (1.0, -1.0):
        pt = QPointF(mid.x() + n.x() * reach * sign,
                    mid.y() + n.y() * reach * sign)
        h = _room_ceiling_at(scene, pt, wall.floor)
        if h is not None:
            found.append(h)
    if not found:
        return float(DEFAULT_ROOM_PROPS["ceiling_height_in"])
    return min(found)


def _clip_spans_against_one_roof(wall, rf, ceiling_in: float):
    """(s0, s1) sub-spans, inches from `wall.p1`, where roof `rf` covers the
    wall AND its own height there is below `ceiling_in`.

    Every governing quantity -- how far along the ridge a point on the wall
    projects, how far off it, and (given those) the roof's own height there
    -- is AFFINE in the wall's own arc-length parameter `s`. So every place
    a condition can flip true/false is a single root of a linear equation,
    not a threshold to be discovered by stepping along the wall: collect
    every root that lands inside the wall, sort them into a partition of
    `[0, L]`, and read the (constant-within-each-piece) verdict once per
    piece, at its midpoint. Exact, not sampled -- the `cuts` list an
    opening's own span already builds along a wall is the same idiom."""
    L = wall.length()
    if L < _CLIP_EPS_IN:
        return []
    r1, r2 = rf.p1, rf.p2
    dx, dy = r2.x() - r1.x(), r2.y() - r1.y()
    ridge_len = math.hypot(dx, dy)
    if ridge_len < _CLIP_EPS_IN:
        return []
    ux, uy = dx / ridge_len, dy / ridge_len
    nx, ny = -uy, ux
    # R4a: per side, not a single shared reach/slope -- side L is perp >= 0
    # (the +normal direction, index 0), side R is perp < 0 (index 1).
    span_l, span_r = rf.span_in
    oh_l, oh_r = rf.overhang_in
    reach_l, reach_r = span_l + oh_l, span_r + oh_r
    ridge_h, eaves_h = rf.ridge_h_in, rf.eaves_h_in
    slope_l = ((ridge_h - eaves_h) / span_l) if span_l > _CLIP_EPS_IN else 0.0
    slope_r = ((ridge_h - eaves_h) / span_r) if span_r > _CLIP_EPS_IN else 0.0
    margin = ridge_h - ceiling_in         # > 0: ridge itself clears the ceiling
    # R4b: a HIP end extends the footprint past the ridge end by its run +
    # overhang, and adds a third plane there -- the roof surface in that
    # region is the LOWER of the side plane and the hip plane (they meet
    # along the hip line), so "clipped" is side-clipped OR hip-clipped.
    # The hip plane's own drop is affine in `along` exactly as a side's is
    # in `perp`, so it adds roots, never sampling.
    run_1, ohe_1 = rf.hip_extension(0)
    run_2, ohe_2 = rf.hip_extension(1)
    ext_1, ext_2 = run_1 + ohe_1, run_2 + ohe_2
    slope_h1 = ((ridge_h - eaves_h) / run_1) if run_1 > _CLIP_EPS_IN else 0.0
    slope_h2 = ((ridge_h - eaves_h) / run_2) if run_2 > _CLIP_EPS_IN else 0.0

    wu = wall.unit()
    ox, oy = wall.p1.x() - r1.x(), wall.p1.y() - r1.y()
    a0, a1 = ox * ux + oy * uy, wu.x() * ux + wu.y() * uy          # along(s)
    b0, b1 = ox * nx + oy * ny, wu.x() * nx + wu.y() * ny          # perp(s)

    roots = [0.0, L]

    def add_root(lhs_const, coeff):
        if abs(coeff) > _CLIP_EPS_IN:
            s = (lhs_const) / coeff
            if -_CLIP_EPS_IN <= s <= L + _CLIP_EPS_IN:
                roots.append(min(max(s, 0.0), L))

    add_root(0.0 - a0, a1)                 # along(s) == 0 -- hip 1 region starts
    add_root(ridge_len - a0, a1)           # along(s) == ridge_len -- hip 2 starts
    add_root(-ext_1 - a0, a1)              # along(s) == -ext_1 (footprint end)
    add_root(ridge_len + ext_2 - a0, a1)   # along(s) == ridge_len + ext_2
    add_root(0.0 - b0, b1)                 # perp(s) == 0 -- the side switches here
    add_root(reach_l - b0, b1)             # perp(s) == +reach_l
    add_root(-reach_r - b0, b1)            # perp(s) == -reach_r
    if slope_l > _CLIP_SLOPE_EPS:
        add_root(margin / slope_l - b0, b1)        # perp(s) == +perp_thresh_l
    if slope_r > _CLIP_SLOPE_EPS:
        add_root(-margin / slope_r - b0, b1)       # perp(s) == -perp_thresh_r
    if slope_h1 > _CLIP_SLOPE_EPS:
        add_root(-margin / slope_h1 - a0, a1)      # along(s) == -along_thresh_1
    if slope_h2 > _CLIP_SLOPE_EPS:
        add_root(ridge_len + margin / slope_h2 - a0, a1)   # == ridge_len + thresh_2

    roots = sorted(set(roots))
    spans = []
    for s_lo, s_hi in zip(roots, roots[1:], strict=False):
        if s_hi - s_lo < _CLIP_EPS_IN:
            continue
        s_mid = (s_lo + s_hi) / 2.0
        along_m, perp_m = a0 + a1 * s_mid, b0 + b1 * s_mid
        if perp_m >= 0:
            reach, slope = reach_l, slope_l
        else:
            reach, slope = reach_r, slope_r
        if not (-ext_1 - _CLIP_EPS_IN <= along_m <= ridge_len + ext_2 + _CLIP_EPS_IN
                and abs(perp_m) <= reach + _CLIP_EPS_IN):
            continue                       # not under this roof at all here
        if slope > _CLIP_SLOPE_EPS:
            clipped = (ridge_h - slope * abs(perp_m)) < ceiling_in - _CLIP_EPS_IN
        else:                              # degenerate/flat roof: uniform verdict
            clipped = margin < -_CLIP_EPS_IN
        if along_m < 0.0 and ext_1 > _CLIP_EPS_IN:            # under hip end 1
            beyond = -along_m
            if slope_h1 > _CLIP_SLOPE_EPS:
                clipped = clipped or (ridge_h - slope_h1 * beyond) < ceiling_in - _CLIP_EPS_IN
            else:
                clipped = clipped or margin < -_CLIP_EPS_IN
        elif along_m > ridge_len and ext_2 > _CLIP_EPS_IN:    # under hip end 2
            beyond = along_m - ridge_len
            if slope_h2 > _CLIP_SLOPE_EPS:
                clipped = clipped or (ridge_h - slope_h2 * beyond) < ceiling_in - _CLIP_EPS_IN
            else:
                clipped = clipped or margin < -_CLIP_EPS_IN
        if clipped:
            spans.append((s_lo, s_hi))
    return spans


def _merge_spans(spans, total):
    """Union overlapping/touching (s0, s1) pairs, clamped to `[0, total]`."""
    clean = sorted((max(0.0, s0), min(total, s1)) for s0, s1 in spans
                  if s1 - s0 > _CLIP_EPS_IN)
    merged = []
    for s0, s1 in clean:
        if merged and s0 <= merged[-1][1] + _CLIP_EPS_IN:
            merged[-1] = (merged[-1][0], max(merged[-1][1], s1))
        else:
            merged.append((s0, s1))
    return merged


def roof_clip_spans(scene, wall):
    """The dotted-line sub-span(s) along `wall` (0145-ruling.md sec3):
    where any roof on the same floor covers it below the room's own
    ceiling height. `[]` when nothing clips -- the common case, and the
    caller's own cue to draw nothing extra.

    Every item this touches -- `wall` itself, and every `RoofItem`
    `scene.items()` returns -- is checked with `sip.isdeleted` first:
    `WallItem.paint()` (the only caller) can fire while the scene is being
    torn down (`clear_plan`'s `scene.clear()`, `File > New`), and Qt does
    not guarantee every already-scheduled repaint is skipped before an
    item's C++ side is gone -- touching one raises, which a paint()
    override cannot recover from (it presents as a crash, not a
    traceback: PyQt6 aborts the process on an unhandled exception in a
    Qt virtual override)."""
    if scene is None or sip.isdeleted(wall):
        return []
    # P2 (0297 §2, 0293 §2b): EVERY live roof, in ABSOLUTE height -- a roof on
    # another level caps a wall it passes over (an L1 roof rising through an L2
    # wall, 0293 §1 M2's 0 dashes), not only a roof on the wall's own floor. The
    # affine clip (`_clip_spans_against_one_roof`) is unchanged: the per-roof
    # ceiling is shifted by the two levels' base difference, so its comparison
    # (roof height vs ceiling) is absolute (`Lifted`/`floor_elevation`, 0186 §4 --
    # ONE arithmetic). Same floor -> the shift is 0 -> byte-identical.
    roofs = [it for it in scene.items()
             if isinstance(it, RoofItem) and not sip.isdeleted(it)]
    if not roofs:
        return []                          # cheap exit before the room scan
    wall_base = float(floor_elevation(wall.floor))
    # 0276 (0275 sec5 step 2): computed once per change of what it reads --
    # the wall's line and thickness, every roof (its geometry, its visible
    # region and its level base) and the wall-floor's rooms -- not once per paint
    own = ((wall.p1.x(), wall.p1.y(), wall.p2.x(), wall.p2.y(), float(wall.t)),
           tuple((rf.geometry_key(), rf._clip_region, float(floor_elevation(rf.floor)))
                 for rf in roofs))
    memo = getattr(wall, "_roof_spans_memo", None)
    if memo is not None and rooms_held(scene) and memo[0][:2] == own:
        return list(memo[1])              # 0279: the rooms as at the press
    key = own + (floor_rooms_key(scene, wall.floor),)
    if memo is not None and memo[0] == key:
        return list(memo[1])
    ceiling_in = _wall_ceiling_in(scene, wall)
    spans = []
    for rf in roofs:
        adj = ceiling_in + wall_base - float(floor_elevation(rf.floor))
        spans.extend(_within_territory(
            wall, rf, _clip_spans_against_one_roof(wall, rf, adj)))
    out = _merge_spans(spans, wall.length())
    wall._roof_spans_memo = (key, list(out))
    return out


def _within_territory(wall, rf, spans):
    """R5b (0191-ruling.md sec1, the territory fix): a roof dashes a wall
    only where the wall point lies in that roof's own DRAWN territory --
    R4d/R4g's visible region -- not everywhere its plane passes overhead.
    Measured on the read-back's own scene (0190-report.md sec0): the host's
    plane under a dormer is 90in over a 96in room, and this function used
    to dash the wall there although the dormer above it is 110in+. A roof
    with no partner (`_clip_region` None) is unchanged, byte for byte; the
    region's own exact segment clip (Cyrus-Beck per cell) cuts each span,
    read back to inches along the wall."""
    region = rf._clip_region
    if region is None or not spans:
        return spans
    u = wall.unit()
    o = wall.p1
    out = []
    for s0, s1 in spans:
        a, b = wall.point_at(s0), wall.point_at(s1)
        for p, q in region.clip_segment(Pt(a.x(), a.y()), Pt(b.x(), b.y())):
            t0 = (p.x() - o.x()) * u.x() + (p.y() - o.y()) * u.y()
            t1 = (q.x() - o.x()) * u.x() + (q.y() - o.y()) * u.y()
            lo, hi = min(t0, t1), max(t0, t1)
            if hi - lo > _CLIP_EPS_IN:
                out.append((lo, hi))
    return out


# ---------------------------------------------------------------------------
# R5a (0186-ruling.md sec2): the clip trace, ON THE ROOF
# ---------------------------------------------------------------------------
# "dashed lines on the roof where the full height of the walls are clipped
# by the roof" -- the same fact R3b puts on the wall, read from the roof's
# side: the locus where the roof surface crosses the covered rooms'
# wall-top plane. Toward the ridge of it the roof clears the ceiling;
# toward the eaves rooms lose full height, and every R3b wall dash starts
# or ends exactly where its wall crosses this line. It is also the dormer
# placement map (the ruling's own reason for building it first).
#
# THE GEOMETRY. Within the roof's own footprint the surface is
# `ridge_h - slope * |perp|` on each side, and past a hip end the LOWER of
# that and the hip plane `ridge_h - slope_h * beyond` (the same surface
# `_clip_spans_against_one_roof` reads along a wall). Its level set at a
# ceiling height `h` is therefore straight lines in the roof's own
# (along, perp) frame: one per side at `perp = +-(ridge_h - h) / slope`,
# running the footprint's along-extent but stopping where a hip plane
# takes over, and per hip end a cross segment at `along = -(ridge_h - h)
# / slope_h` between the two side lines -- a closed loop for a hip roof,
# two open lines for a gable one. A side whose line would lie beyond its
# own eaves never clips, and draws nothing; a ridge below `h` clips
# everywhere and has no locus at all (R3b dashes the whole wall then; the
# roof has no line to draw -- `tests/test_roof_clip_trace.py` names that
# as a limit, not a bug).
#
# WHICH CEILING. A roof can cover rooms of different heights, and R3b
# reads each wall against the LOWER of the rooms it borders
# (`_wall_ceiling_in`), falling back to the default when no room is
# there. So the trace does the same at every point: for each distinct
# ceiling `h` among the floor's rooms (plus the default), the level set
# at `h` is cut wherever it crosses a room's outline -- dilated by half
# the floor's thickest wall, so a point ON a wall's centreline still
# counts as the room's (a room outline stops at the wall's interior
# face) -- and a piece is kept only where `h` is the governing ceiling
# at its midpoint: the LOWEST among the rooms holding the point, or the
# default where none does. Exact, not sampled: every place the verdict
# can flip is an intersection of the line with a dilated outline (an
# offset edge line or a vertex's circle), so those are the cuts, and the
# verdict is constant between them. Same idiom as the wall spans.
#
# A ROOF UNDER R4d's CLIP draws the trace only inside its visible region
# (`RoofItem._drawn_trace`), exactly as its eave lines are, and a JOINED
# end carries the trace on into its extension: the surface continues
# there, so the level set does too.

_TRACE_MARGIN_PAD_IN = 0.5   # past the half wall thickness, so a line landing
                             # exactly on a centreline is not a coin toss


def _trace_lines_local(rf, h: float, join_ext=(0.0, 0.0)):
    """The level set of `rf`'s surface at height `h`, as segments in the
    roof's own frame: `((a0, p0), (a1, p1))`, `a` along the ridge from
    `p1`, `p` perpendicular (+ is the LEFT side, `span_in[0]`). Pure
    geometry of one roof -- no scene, no rooms. `join_ext` is R4d's
    per-end extension of a joined end (the surface continues there)."""
    L = rf.length()
    if L < _CLIP_EPS_IN:
        return []
    span_l, span_r = rf.span_in
    oh_l, oh_r = rf.overhang_in
    reach_l, reach_r = span_l + oh_l, span_r + oh_r
    ridge_h, eaves_h = rf.ridge_h_in, rf.eaves_h_in
    drop = ridge_h - h                      # > 0: the ridge clears the ceiling
    if drop < -_CLIP_EPS_IN:
        return []                           # ridge below the ceiling: no locus
    slope_l = ((ridge_h - eaves_h) / span_l) if span_l > _CLIP_EPS_IN else 0.0
    slope_r = ((ridge_h - eaves_h) / span_r) if span_r > _CLIP_EPS_IN else 0.0
    run_1, ohe_1 = rf.hip_extension(0)
    run_2, ohe_2 = rf.hip_extension(1)
    ext_1 = run_1 + ohe_1 + max(0.0, join_ext[0])
    ext_2 = run_2 + ohe_2 + max(0.0, join_ext[1])
    slope_h1 = ((ridge_h - eaves_h) / run_1) if run_1 > _CLIP_EPS_IN else 0.0
    slope_h2 = ((ridge_h - eaves_h) / run_2) if run_2 > _CLIP_EPS_IN else 0.0
    a_lo, a_hi = -ext_1, L + ext_2          # the footprint's along-extent

    # where each hip plane takes over from the side planes, along the axis;
    # None when that end has no hip plane reaching `h` inside the footprint
    hip_a1 = hip_a2 = None
    if slope_h1 > _CLIP_SLOPE_EPS and drop / slope_h1 <= ext_1 + _CLIP_EPS_IN:
        hip_a1 = -drop / slope_h1
    if slope_h2 > _CLIP_SLOPE_EPS and drop / slope_h2 <= ext_2 + _CLIP_EPS_IN:
        hip_a2 = L + drop / slope_h2
    a_start = a_lo if hip_a1 is None else max(a_lo, hip_a1)
    a_end = a_hi if hip_a2 is None else min(a_hi, hip_a2)

    # each side's own line, where it lies inside that side's eaves reach
    def side_thresh(slope, reach):
        if slope <= _CLIP_SLOPE_EPS:        # flat side: at ridge height throughout
            return None
        thresh = drop / slope
        return thresh if thresh <= reach + _CLIP_EPS_IN else None

    thresh_l = side_thresh(slope_l, reach_l)
    thresh_r = side_thresh(slope_r, reach_r)
    lines = []
    if a_end - a_start > _CLIP_EPS_IN:
        if thresh_l is not None:
            lines.append(((a_start, thresh_l), (a_end, thresh_l)))
        if thresh_r is not None:
            lines.append(((a_start, -thresh_r), (a_end, -thresh_r)))
    # a hip end's cross segment: the hip plane at `h`, between the side
    # lines (or the eaves, where a side never reaches `h`)
    p_hi = reach_l if thresh_l is None else thresh_l
    p_lo = -(reach_r if thresh_r is None else thresh_r)
    for hip_a in (hip_a1, hip_a2):
        if hip_a is not None and p_hi - p_lo > _CLIP_EPS_IN:
            lines.append(((hip_a, p_lo), (hip_a, p_hi)))
    return lines


def _trace_to_scene(rf, lines):
    """Roof-frame `((a, p), (a, p))` pairs -> scene `(QPointF, QPointF)`."""
    ux, uy, nx, ny = rf._axis()
    o = rf.p1

    def pt(a, p):
        return QPointF(o.x() + ux * a + nx * p, o.y() + uy * a + ny * p)

    return [(pt(*s), pt(*e)) for s, e in lines]


class _TraceRoom(NamedTuple):
    """One room as the trace reads it: its ceiling, its outline path (for
    the inside test) and that outline's edge polygons (for the margin)."""
    ceiling: float
    path: object
    polys: list

    def holds(self, pt: QPointF, margin: float) -> bool:
        if self.path.contains(pt):
            return True
        for poly in self.polys:
            n = len(poly)
            for i in range(n):
                if dist_point_segment(pt, poly[i], poly[(i + 1) % n]) <= margin:
                    return True
        return False


def floor_rooms_key(scene, floor):
    """0275/0276: everything `roof_clip_trace` and `roof_clip_spans` read of
    `floor` other than the roofs -- as a key, cheap to build and EXACT.

    Each live room contributes ITSELF, the vertex OBJECTS of its outline
    (a moved corner is a NEW `Vertex` -- `Vertex.relocated_to` -- and a
    vertex is never moved in place, so identity is position; the key holds
    them, so no id can be reused while it lives), its no-outline fallback
    path object, and its ceiling height; the walls contribute the thickest
    thickness (the trace's margin). One pass over the scene, no geometry:
    tens of microseconds where the trace it guards costs tens of
    milliseconds."""
    from floorplanner.rooms import RoomItem  # late (peer layer)
    rooms = []
    t_max = 0.0
    for it in scene.items():
        if sip.isdeleted(it) or getattr(it, "floor", None) != floor:
            continue
        if isinstance(it, RoomItem):
            outline = it.outline
            rooms.append((it, tuple(e.v for e in outline) if outline else it._path,
                          it.properties.get("ceiling_height_in")))
        elif isinstance(it, WallItem):
            t_max = max(t_max, float(it.t))
    return (tuple(rooms), t_max)


def floor_rooms_value_key(scene, floor):
    """0281: `floor_rooms_key` by VALUE -- each room's outline coordinates
    (or its fallback path's polygons) and ceiling, sorted, and the floor's
    thickest wall. Dearer than the identity key (it reads every corner), so
    it is built only when the identity key has missed: after a reload,
    whose new objects carry the same geometry."""
    from floorplanner.rooms import RoomItem  # late (peer layer)
    rooms = []
    t_max = 0.0
    for it in scene.items():
        if sip.isdeleted(it) or getattr(it, "floor", None) != floor:
            continue
        if isinstance(it, RoomItem):
            if it.outline:
                shape = tuple((round(e.v.x, 6), round(e.v.y, 6)) for e in it.outline)
            else:
                shape = tuple(tuple((round(q.x(), 6), round(q.y(), 6)) for q in poly)
                              for poly in it._path.toSubpathPolygons())
            rooms.append((shape, it.properties.get("ceiling_height_in")))
        elif isinstance(it, WallItem):
            t_max = max(t_max, float(it.t))
    return (tuple(sorted(rooms, key=repr)), t_max)


_TRACE_BY_VALUE_MAX = 400


def _floor_rooms(scene, floor):
    """Every live room on `floor` as a `_TraceRoom` -- read once per
    trace, not once per point."""
    from floorplanner.rooms import RoomItem  # late (peer layer)
    out = []
    for it in scene.items():
        if (not isinstance(it, RoomItem) or sip.isdeleted(it)
                or getattr(it, "floor", None) != floor):
            continue
        ceiling = float(it.properties.get(
            "ceiling_height_in", DEFAULT_ROOM_PROPS["ceiling_height_in"]))
        polys = [[QPointF(q) for q in poly]
                 for poly in it.path.toSubpathPolygons() if len(poly) >= 2]
        out.append(_TraceRoom(ceiling, it.path, polys))
    return out


def _trace_margin_in(scene, floor) -> float:
    """Half the thickest wall on `floor`, plus a pad: how far outside a
    room's outline a point still counts as the room's (its walls' own
    centrelines, where the R3b dashes live)."""
    t_max = 0.0
    for it in scene.items():
        if isinstance(it, WallItem) and not sip.isdeleted(it) \
                and it.floor == floor:
            t_max = max(t_max, float(it.t))
    return t_max / 2.0 + _TRACE_MARGIN_PAD_IN


def _governing_ceiling(rooms, pt: QPointF, margin: float) -> float:
    """R3b's rule at a point: the LOWEST ceiling among the rooms holding
    `pt` (outline dilated by `margin`), else the default."""
    found = [room.ceiling for room in rooms if room.holds(pt, margin)]
    if not found:
        return float(DEFAULT_ROOM_PROPS["ceiling_height_in"])
    return min(found)


def _cut_params(p: QPointF, q: QPointF, rooms, margin: float):
    """Every parameter `t` in (0, 1) at which `p`-`q` can cross a room's
    dilated outline: its intersections with each edge's line offset by
    0 / +margin / -margin, and with each vertex's circle of radius
    `margin`. A superset of the true crossings -- an extra cut only
    splits a piece whose verdict is the same on both halves."""
    dx, dy = q.x() - p.x(), q.y() - p.y()
    qa = dx * dx + dy * dy
    ts = []

    def add(t):
        if _CLIP_EPS_IN < t < 1.0 - _CLIP_EPS_IN:
            ts.append(t)

    for room in rooms:
        for poly in room.polys:
            n = len(poly)
            for i in range(n):
                a, b = poly[i], poly[(i + 1) % n]
                ex, ey = b.x() - a.x(), b.y() - a.y()
                elen = math.hypot(ex, ey)
                if elen > _CLIP_EPS_IN:
                    onx, ony = -ey / elen, ex / elen
                    den = dx * ey - dy * ex
                    if abs(den) > _CLIP_EPS_IN:
                        for off in (0.0, margin, -margin):
                            ax, ay = a.x() + onx * off, a.y() + ony * off
                            add(((ax - p.x()) * ey - (ay - p.y()) * ex) / den)
                # the vertex circle: |p + t d - a|^2 == margin^2
                fx, fy = p.x() - a.x(), p.y() - a.y()
                qb = 2.0 * (fx * dx + fy * dy)
                qc = fx * fx + fy * fy - margin * margin
                disc = qb * qb - 4.0 * qa * qc
                if qa > _CLIP_EPS_IN and disc >= 0.0:
                    root = math.sqrt(disc)
                    add((-qb - root) / (2.0 * qa))
                    add((-qb + root) / (2.0 * qa))
    return sorted(set(ts))


def roof_clip_trace(scene, roof):
    """The clip trace of `roof` (0186-ruling.md sec2): `[(p, q)]` scene
    segments along the locus where its surface meets the ceiling plane of
    whichever room governs there -- the roof-side reading of the same fact
    `roof_clip_spans` dashes along a wall. `[]` when nothing clips, or
    when every governing ceiling is above the ridge. NOT clipped to R4d's
    visible region (`RoofItem._drawn_trace` does that): this is the
    roof's own locus. `sip.isdeleted` guards for the same paint-during-
    teardown reason `roof_clip_spans` carries."""
    if scene is None or sip.isdeleted(roof):
        return []
    rooms = _floor_rooms(scene, roof.floor)
    margin = _trace_margin_in(scene, roof.floor)
    heights = {float(DEFAULT_ROOM_PROPS["ceiling_height_in"])}
    heights.update(room.ceiling for room in rooms)
    join_ext = roof._clip_ext if roof.is_clipped() else (0.0, 0.0)
    out = []
    for h in sorted(heights):
        for p, q in _trace_to_scene(roof, _trace_lines_local(roof, h, join_ext)):
            dx, dy = q.x() - p.x(), q.y() - p.y()
            seg_len = math.hypot(dx, dy)
            ts = [0.0] + _cut_params(p, q, rooms, margin) + [1.0]
            # consecutive kept pieces merge back into one segment: the cuts
            # are a superset of the real crossings, and a dash pattern
            # restarting at every phantom cut would show them
            runs = []
            for t0, t1 in zip(ts, ts[1:], strict=False):
                if (t1 - t0) * seg_len < _CLIP_EPS_IN:
                    continue
                tm = (t0 + t1) / 2.0
                mid = QPointF(p.x() + dx * tm, p.y() + dy * tm)
                if abs(_governing_ceiling(rooms, mid, margin) - h) > _CLIP_EPS_IN:
                    continue
                if runs and abs(runs[-1][1] - t0) < 1e-12:
                    runs[-1][1] = t1
                else:
                    runs.append([t0, t1])
            out.extend((QPointF(p.x() + dx * t0, p.y() + dy * t0),
                        QPointF(p.x() + dx * t1, p.y() + dy * t1))
                       for t0, t1 in runs)
    return out


def _room_trace(room):
    """`room` as a `_TraceRoom` -- its ceiling and outline, for the knee line."""
    from floorplanner.rooms import RoomItem  # late (peer layer)
    if not isinstance(room, RoomItem) or sip.isdeleted(room):
        return None
    ceiling = float(room.properties.get(
        "ceiling_height_in", DEFAULT_ROOM_PROPS["ceiling_height_in"]))
    polys = [[QPointF(q) for q in poly]
             for poly in room.path.toSubpathPolygons() if len(poly) >= 2]
    return _TraceRoom(ceiling, room.path, polys)


def room_ceiling_break_lines(scene, room):
    """P2 (0297 §2, 0293 §2b): the KNEE LINE of `room` -- `[(p, q)]` scene
    segments where any roof's surface, in ABSOLUTE height, crosses this room's
    ceiling plane (`base + ceiling`), drawn INSIDE the room outline. His ask
    (2026-11-05): "walls that have a full height ceiling should get the dashed
    line that indicates where a flat ceiling starts." A DERIVED OVERLAY, never a
    wall and never stored -- the discipline of R3b's wall dash (`roof_clip_spans`)
    and R5a's roof trace (`roof_clip_trace`); it reads absolute height the one way
    3D does (`floor_elevation`), so a roof on a LOWER level draws the line in a
    room above. `[]` when no roof crosses the ceiling over the room. Memoised on
    the roofs (geometry, territory, level base) and the floor's rooms (0276), held
    during a drag (0279) -- paint must not recompose (0281)."""
    if scene is None or sip.isdeleted(room):
        return []
    roofs = [it for it in scene.items()
             if isinstance(it, RoofItem) and not sip.isdeleted(it)]
    if not roofs:
        return []
    roof_sig = tuple((rf.geometry_key(), rf._clip_region, float(floor_elevation(rf.floor)))
                     for rf in roofs)
    memo = getattr(room, "_knee_memo", None)
    if memo is not None and rooms_held(scene) and memo[0][0] == roof_sig:
        return list(memo[1])
    key = (roof_sig, floor_rooms_key(scene, room.floor))
    if memo is not None and memo[0] == key:
        return list(memo[1])
    tr = _room_trace(room)
    if tr is None:
        room._knee_memo = (key, [])
        return []
    ceiling_abs = float(floor_elevation(room.floor)) + tr.ceiling
    margin = _trace_margin_in(scene, room.floor)
    rooms = [tr]
    out = []
    for rf in roofs:
        h = ceiling_abs - float(floor_elevation(rf.floor))        # roof-relative height
        join_ext = rf._clip_ext if rf.is_clipped() else (0.0, 0.0)
        region = rf._clip_region
        for p, q in _trace_to_scene(rf, _trace_lines_local(rf, h, join_ext)):
            dx, dy = q.x() - p.x(), q.y() - p.y()
            seg_len = math.hypot(dx, dy)
            if seg_len < _CLIP_EPS_IN:
                continue
            ts = [0.0] + _cut_params(p, q, rooms, margin) + [1.0]
            for t0, t1 in zip(ts, ts[1:], strict=False):
                if (t1 - t0) * seg_len < _CLIP_EPS_IN:
                    continue
                tm = (t0 + t1) / 2.0
                mid = QPointF(p.x() + dx * tm, p.y() + dy * tm)
                if not tr.holds(mid, margin):
                    continue
                if region is not None and not region.contains(mid):
                    continue
                out.append((QPointF(p.x() + dx * t0, p.y() + dy * t0),
                            QPointF(p.x() + dx * t1, p.y() + dy * t1)))
    room._knee_memo = (key, list(out))
    return list(out)


# ---------------------------------------------------------------------------
# R5b (0191-ruling.md): dormers -- a roof with a host
# ---------------------------------------------------------------------------
# A dormer is a `RoofItem` whose `host` is another roof on its floor
# (0190-report.md sec1, adopted at 0191 sec1). Everything a roof has, it
# has; two facts are DERIVED on top: its back ridge end, where its ridge
# meets the host's plane (`meet_along`), and its cheeks and face, the
# walls that stand on the host plane under its own eaves. The clip
# machinery is untouched -- 0190 sec0 measured that a dormer whose back
# end sits on the host plane already partitions correctly by the same
# envelope rules (two valleys meeting at the ridge/plane intersection).

DORMER_EAVES_ABOVE_CEILING_IN = 24.0   # default cheek top over the trace's ceiling
DORMER_MIN_SPAN_IN = 6.0               # half-width below which a drag is a slip
_SHED_EDGE_TOL_IN = 0.5                # a shed dormer's high edge may sit this far under the host


def _host_roof_on(scene, p, floor):
    """The non-dormer roof on exactly `floor` whose drawn territory (R4d's
    visible region, or a lone roof's whole footprint) holds plan point `p`."""
    for it in scene.items():
        if (not isinstance(it, RoofItem) or sip.isdeleted(it)
                or it.floor != floor or it.is_dormer()):
            continue
        region = it._clip_region
        if region is not None:
            if region.contains(p):
                return it
        elif _contains(footprint_polygon(it), p):
            return it
    return None


def _floor_below(floor):
    """The floor one level down from `floor` -- the one whose elevation is the
    greatest strictly below it. None when `floor` is the lowest or unknown."""
    elevs = floor_elevations()
    here = elevs.get(floor)
    if here is None:
        return None
    lower = [(el, name) for name, el in elevs.items() if el < here - 1e-6]
    return max(lower)[1] if lower else None


def host_roof_at(scene, pt: QPointF, floor):
    """The roof a dormer pressed at `pt` on `floor` stands on. Tries `floor`
    first; when no roof is there, LOOKS DOWN a level (Patrick, 2026-11: a
    dormer drawn on the storey its gable occupies finds its host roof on the
    floor below -- its geometry is then anchored to the host's level, while
    its own `level` is where it is drawn and edited). A dormer cannot host
    another (v1: named, not built), so dormers are skipped. None when no roof
    is under `pt` on this floor or the one below."""
    if scene is None:
        return None
    p = Pt(pt.x(), pt.y())
    hit = _host_roof_on(scene, p, floor)
    if hit is not None:
        return hit
    below = _floor_below(floor)
    return _host_roof_on(scene, p, below) if below is not None else None


def dormer_defaults(scene, host, pt: QPointF):
    """`(eaves_h_in, slope)` for a dormer whose face stands at `pt` on
    `host` (0190-report.md sec3, adopted): the cheek top is the governing
    ceiling there (R3b's own rule, the trace's height) plus
    `DORMER_EAVES_ABOVE_CEILING_IN`; the slope is the host's own pitch on
    the side `pt` lies, so the dormer's ridge follows the host's pitch by
    default (`ridge_h = eaves_h + span * slope`)."""
    rooms = _floor_rooms(scene, host.floor) if scene is not None else []
    margin = _trace_margin_in(scene, host.floor) if scene is not None else 0.0
    ceiling = _governing_ceiling(rooms, pt, margin)
    _, _, nx, ny = host._axis()
    perp = (pt.x() - host.p1.x()) * nx + (pt.y() - host.p1.y()) * ny
    span = host.span_in[0] if perp >= 0 else host.span_in[1]
    slope = ((host.ridge_h_in - host.eaves_h_in) / span) if span > _CLIP_EPS_IN else 0.0
    return ceiling + DORMER_EAVES_ABOVE_CEILING_IN, slope


def upslope_direction(host, pt: QPointF):
    """Unit `(dx, dy)` from `pt` toward `host`'s ridge, perpendicular to
    its eave -- the default direction of a dormer's ridge. None on the
    ridge line itself (no side to climb from)."""
    _, _, nx, ny = host._axis()
    perp = (pt.x() - host.p1.x()) * nx + (pt.y() - host.p1.y()) * ny
    if abs(perp) < _CLIP_EPS_IN:
        return None
    sign = -1.0 if perp > 0 else 1.0
    return nx * sign, ny * sign


def snap_to_trace(scene, host, pt: QPointF, tol: float):
    """The nearest point on `host`'s clip trace (`roof_clip_trace`) within
    `tol` of `pt`, else None -- the dormer's face goes on the placement
    map (0186-ruling.md sec2). ALONG the trace the point lands on the
    grid (`wall_snap_len` of its coordinate along the trace's own
    direction, from the scene origin -- the same "on the grid, never by
    it" rule every roof drag uses, 0070-ruling.md sec3), clamped to the
    segment."""
    best, best_d = None, tol
    for p, q in host.clip_trace():
        d = dist_point_segment(pt, p, q)
        if d < best_d:
            dx, dy = q.x() - p.x(), q.y() - p.y()
            ln = math.hypot(dx, dy)
            if ln < 1e-9:
                best, best_d = QPointF(p), d
                continue
            tx, ty = dx / ln, dy / ln
            along = wall_snap_len(pt.x() * tx + pt.y() * ty)
            lo, hi = sorted((p.x() * tx + p.y() * ty, q.x() * tx + q.y() * ty))
            along = max(lo, min(hi, along))
            # back to the line: keep the perpendicular offset of the segment
            perp_off = p.x() * -ty + p.y() * tx
            best = QPointF(along * tx + perp_off * -ty, along * ty + perp_off * tx)
            best_d = d
    return best


# ---------------------------------------------------------------------------
# R4b (0154-ruling.md sec2, requirement 5): eaves bound to the room top
# ---------------------------------------------------------------------------
# "assign the roof's bottom -- where the eaves start -- to the top of the
# rooms it covers." Same datum as every roof height (0140-ruling.md sec3:
# the level's own base), so a room's top IS its `ceiling_height_in`.

# a room whose overlap with the footprint is thinner than this, on either
# axis, is a sliver from a shared wall face, not a room the roof covers
_COVER_MIN_IN = 1.0


class RoomTopBinding(NamedTuple):
    """What `bound_eaves_height` measured: the eaves height the binding
    produces, and the rooms it read, highest first, as `(name, ceiling)`.
    `fallback` is True when NO room sits under the footprint and the
    default ceiling stood in -- reported, never silent."""
    eaves_h_in: float
    rooms: list
    fallback: bool

    def differs(self) -> bool:
        return len({round(c, 6) for _, c in self.rooms}) > 1

    def note(self) -> str:
        """One line for the dialog and the status bar to share, so both say
        the same thing about the same measurement."""
        if self.fallback:
            return (f"No room under this roof -- eaves at the default "
                    f"ceiling, {fmt_in(self.eaves_h_in)}.")
        listed = ", ".join(f"{n} {fmt_in(c)}" for n, c in self.rooms)
        if self.differs():
            return (f"Room tops differ ({listed}) -- the highest governs, "
                    f"{fmt_in(self.eaves_h_in)}.")
        return f"Room top {fmt_in(self.eaves_h_in)} ({listed})."

    def status_line(self) -> str:
        return "Eaves bound to room top: " + self.note()


def bound_eaves_height(scene, roof, gable=None, span=None) -> RoomTopBinding:
    """The eaves height `eaves_bind == "room_top"` produces for `roof`: the
    HIGHEST `ceiling_height_in` among the rooms on the roof's own floor
    whose outline overlaps its eaves-start footprint (`eaves_start_polygon`
    -- the span, not the overhang: a room only under the overhang is not a
    room the roof sits on). Rooms of differing heights under one roof:
    the highest governs and the mismatch is reported in the returned
    record, not hidden (0154-ruling.md sec2, Patrick's default). No room
    at all: `DEFAULT_ROOM_PROPS`' own ceiling, flagged as a fallback.
    `scene` may be None (a roof not yet in a scene) -- that is the same
    "no room" case. `gable`/`span` preview an unapplied dialog edit."""
    from floorplanner.rooms import RoomItem  # late (peer layer)
    fp = QPainterPath()
    fp.addPolygon(roof.eaves_start_polygon(gable, span))
    fp.closeSubpath()
    found = []
    if scene is not None:
        for it in scene.items():
            if (not isinstance(it, RoomItem) or sip.isdeleted(it)
                    or getattr(it, "floor", None) != roof.floor):
                continue
            inter = it.path.intersected(fp)
            br = inter.boundingRect()
            if inter.isEmpty() or br.width() < _COVER_MIN_IN \
                    or br.height() < _COVER_MIN_IN:
                continue
            ceiling = float(it.properties.get(
                "ceiling_height_in", DEFAULT_ROOM_PROPS["ceiling_height_in"]))
            found.append((it.name, ceiling))
    if not found:
        return RoomTopBinding(float(DEFAULT_ROOM_PROPS["ceiling_height_in"]),
                              [], True)
    found.sort(key=lambda nc: (-nc[1], nc[0]))
    return RoomTopBinding(found[0][1], found, False)


def sync_bound_roofs(scene, floor=None):
    """Re-derive `eaves_h_in` for every roof whose `eaves_bind` is
    `"room_top"` (on `floor` only, when given) and rebuild it -- the hook
    a room-height edit calls so "change the room height, watch the roof
    follow" (0154-ruling.md sec3, R4b's own check) is one call, not a
    convention. Returns `[(roof, binding)]` for every bound roof it
    touched, changed or not, so the caller can report what happened."""
    out = []
    if scene is None:
        return out
    for it in scene.items():
        if (not isinstance(it, RoofItem) or sip.isdeleted(it)
                or it.eaves_bind != "room_top"
                or (floor is not None and it.floor != floor)):
            continue
        binding = bound_eaves_height(scene, it)
        it.eaves_h_in = binding.eaves_h_in
        it.rebuild()
        out.append((it, binding))
    return out


_CLIP_HOLD = "roof_clip_hold"


def hold_roof_clips(scene, on: bool):
    """R6.b, the cost (0200-report.md sec3): composing the whole building is
    about ten times one level's clip -- 1.66 s on his two-level wiscaway
    against 0.15 s -- so a gesture that rebuilds a roof at every step
    must not re-compose at every step. `hold_roof_clips(scene, True)`
    makes `sync_roof_clips` a no-op; `False` releases the hold AND
    composes once. Held while a plan loads (every roof added used to
    re-clip) and while a grip, a ridge or a dormer is being dragged (the
    dragged roof is selected or new, so it draws unclipped anyway; the
    others catch up at the release)."""
    if scene is None:
        return
    scene.setProperty(_CLIP_HOLD, bool(on))
    if not on:
        sync_roof_clips(scene)


_ROOMS_HOLD = "rooms_hold"


def hold_rooms(scene, on: bool):
    """0279 (0276 sec5, his word "go ahead with the wall and room drag
    hold"): while a canvas gesture is in progress -- a mouse button down
    on the plan -- the roof clip traces and the walls' roof-clip dashes
    take the floor's rooms AS THEY WERE AT THE PRESS. A wall or room drag
    changes the rooms every frame, and every roof over them recomputed its
    trace every frame (7 fps on his upper floor); now a roof recomputes
    only when ITS OWN geometry changes, and everything catches up once, at
    the release (`False` repaints the scene). The same discipline R6.b
    holds the compose by."""
    if scene is None:
        return
    was = bool(scene.property(_ROOMS_HOLD))
    scene.setProperty(_ROOMS_HOLD, bool(on))
    if was and not on:
        scene.update()


def rooms_held(scene) -> bool:
    return scene is not None and bool(scene.property(_ROOMS_HOLD))


def roof_clips_held(scene) -> bool:
    """True while a roof gesture holds the clips (`hold_roof_clips`): a grip,
    a ridge or a dormer being dragged, or a plan loading. 0276 (0275 sec5
    step 3): the settle walk waits for the hold to end, so a gesture is
    snapshotted once, at its end, however long its frames take."""
    return scene is not None and bool(scene.property(_CLIP_HOLD))


def sync_roof_clips(scene, floor=None, exclude=None):
    """R4d (0164-ruling.md): recompute every roof's intersection clip on
    `floor` (every floor when None) from the roofs as they are now, and
    hand each its region/seams/warnings. Called from `RoofItem.rebuild`
    (so a grip drag or a dialog apply re-clips live), on a roof entering
    or leaving a scene, and never from paint. `exclude` is a roof on its
    way out of the scene."""
    if scene is None or scene.property(_CLIP_HOLD):
        return
    # R6.b (0186-ruling.md sec4, ordered at 0197-ruling.md sec5): THE BUILDING
    # HAS ONE ROOFSCAPE. Every live roof composes against every other in
    # ABSOLUTE height -- its level's elevation plus its own heights -- so
    # `floor` no longer scopes anything (kept in the signature: every
    # caller names the floor it edited, and the answer is the same
    # building either way). A bare scene knows no elevations and composes
    # at one datum, exactly as one level always did.
    roofs = [it for it in scene.items()
             if isinstance(it, RoofItem) and not sip.isdeleted(it)
             and it is not exclude]
    if not roofs:
        return
    # 0281 (his Ctrl+Z, 3 s on wiscaway2026-10-13R1): THE COMPOSE BY VALUE.
    # The compose reads each roof's own geometry (`geometry_key`) and its
    # level's elevation, nothing else -- so the same roofs give the same
    # clips. An undo reloads the document as NEW objects with the SAME
    # roofs (a wall, room, opening or furnishing edit touches none) and
    # recomposed the building from scratch: ~950 ms of a ~1.7 s undo. Now
    # the last result is kept against the roofs' values and handed back.
    sig = [(rf.geometry_key(), float(floor_elevation(rf.floor))) for rf in roofs]
    key = tuple(sorted(sig, key=repr))
    memo = getattr(scene, "_compose_memo", None)
    if memo is not None and memo[0] == key and len(set(sig)) == len(sig):
        for rf, s in zip(roofs, sig, strict=True):
            rf.apply_clip(memo[1][s])
        return
    clips = compose_building([(rf, floor_elevation(rf.floor)) for rf in roofs])
    for rf in roofs:
        rf.apply_clip(clips[id(rf)])
    if len(set(sig)) == len(sig):             # two identical roofs: never cached
        scene._compose_memo = (key, {s: clips[id(rf)] for rf, s in zip(roofs, sig, strict=True)})


class RoofItem(QGraphicsItem):
    """A gable roof's ridge, drawn in plan: ridge heavy, eaves and gable
    ends dashed -- 0139-ruling.md R2's own 2D overlay convention.

    Local coords == scene coords (pos stays 0,0), same convention as
    `WallItem`; `p1`/`p2` are the ridge endpoints, plain `QPointF`s rather
    than shared `Vertex`s (0139-ruling.md sec2's model stores the ridge as
    two literal points, not a wall-network corner -- a roof does not need
    welding).

    `span_in`/`overhang_in` are `[left, right]`, PER SIDE as of R4a
    (0154-ruling.md) -- LEFT is the ridge direction's own +90deg-rotated
    normal, RIGHT the opposite side; a ridge-relative side, unrelated to
    the `ridge`-endpoint index `gable`/`marker_end` use. Both are
    PROPERTIES: assigning a bare number normalises to `[v, v]` (the
    ridge-sketch tool's own eaves pick, and every existing caller, still
    hands over one number), assigning a 2-item sequence is stored
    per-side as given -- so a caller cannot silently corrupt the pair back
    into a scalar the way a plain attribute would let it. `span_in` used
    to be a live-scene render affordance with no document field at all
    (`nearest_eaves_wall`'s own docstring); R4a gives it one, and
    `design/bridge.py`'s loader is what materialises a pre-R4a roof's
    single derived number into `[v, v]` on first load -- this class itself
    has no document-vs-live distinction to make.

    Unequal sides with one `ridge_h_in`/`eaves_h_in` pair now give unequal
    pitch on each slope (a saltbox) -- 0139-ruling.md's v1 symmetric-eaves
    assumption retires here, on schedule.

    A HIP end (`gable[i] == False`, settable from R4b's parameters dialog)
    extends the footprint PAST that ridge end by `hip_extension(i)`: the
    ridge stays where it was sketched, and a sloped end face runs from the
    ridge end down to an end eave line `hip run` beyond it (plus the end's
    own overhang). The hip run is the MEAN of the two side spans -- for
    the symmetric roof every sketch produces it equals the side span, so
    all four faces share one pitch (the regular hip); for a saltbox it is
    the one value that keeps the end face a single plane meeting both
    sides at their corners. Nothing new is stored for it: `gable` is the
    whole document fact, the run is derived, same discipline as pitch.

    `eaves_bind == "room_top"` (0154-ruling.md sec2, item 5): `eaves_h_in`
    is derived from the ceiling of the rooms this roof's eaves-start
    footprint covers (`bound_eaves_height`) and re-derived by
    `sync_bound_roofs` whenever a room's height is edited -- and the
    derived number is STILL written to `eaves_h_in` on save, so a
    document never has to re-derive it to be complete. Load never
    re-derives (the saved value is what the binding produced last time
    it ran); only an edit does."""

    def __init__(self, p1, p2, eaves_h_in=96.0, ridge_h_in=132.0,
                overhang_in=0.0, gable=None, span_in=DEFAULT_HALF_SPAN_IN,
                marker_end=1, eaves_bind="manual", host=None, form="gable",
                openings=None, hip_run_in=None, end_overhang_in=None,
                wall_span_in=None, box_half_in=None):
        super().__init__()
        self._trace_memo = None            # 0276: (key, segments) -- clip_trace()
        self._drawn_memo = None            # 0276: (key, segments) -- _drawn_trace()
        # 0258-report.md (0248 sec2 item 6): THE HIP RUN, per end, settable.
        # `[end0, end1]`, each a length along the ridge axis or None = the
        # derived run (the mean of the two spans, R4b's rule, which is all a
        # roof had before). A porch's one-plane roof wanted a short hip on a
        # long span and could not say so.
        self.hip_run_in = hip_run_in
        # 0248-report.md sec3 plan B: a DORMER's face openings -- the same
        # records a wall carries, held as plain dicts and round-tripped;
        # the 3D builder cuts them into the generated face. Nothing in the
        # plan draws them yet.
        self.openings = [dict(o) for o in (openings or [])]
        self._uid = None                  # 0265: the session label, RF<n>
        # R5b: a DORMER is a roof with a host (the RoofItem it stands on);
        # its back end (`p2`) is derived against the host at every rebuild
        self.host = host
        # 0248-report.md sec3 plan A: THE FORM. `"gable"` is the roof this
        # class always was; `"shed"` is ONE plane off the ridge, down the
        # LEFT side (`span_in[0]`) only -- the right side has no plane, so
        # its span and overhang are held at 0 by the two setters below,
        # whatever a grip or a dialog hands them. Every reader of the
        # geometry already treats a zero side as a zero-width strip (the
        # slopes guard it; the eave ends collapse onto the ridge), so a
        # shed needs no second code path in the clip, the item or the mesh.
        self.form = form if form in ("gable", "shed") else "gable"
        # READ-ONLY properties below, mutated only through `set_ridge` --
        # gate.py's own end-assignment census forbids `.p1 =`/`.p2 =`
        # project-wide (the retired wall split-on-write shim), and its
        # docstring says so explicitly: it polices the LITERAL text, not
        # which class it appears in. A roof has no vertex to weld, but the
        # spelling stays retired everywhere in floorplanner/, not just walls.
        self._p1 = QPointF(p1)
        self._p2 = QPointF(p2)
        self.floor = active_floor()      # active floor (load overrides)
        self.eaves_h_in = float(eaves_h_in)
        self.ridge_h_in = float(ridge_h_in)
        self.gable = list(gable) if gable is not None else [True, True]
        self.overhang_in = overhang_in           # the setters: a shed clamps
        self.span_in = span_in
        self.end_overhang_in = end_overhang_in   # per-end rake / face overhang
        self.wall_span_in = wall_span_in         # control C: the dormer walls
        self.box_half_in = box_half_in           # control B: the frame half-width
        self.marker_end = 1 if marker_end else 0   # R2b: which ridge end
        self.eaves_bind = eaves_bind if eaves_bind in ("manual", "room_top") \
            else "manual"                            # R4a: schema slot only
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(WALL_Z + 1)        # reads above walls, like a callout
        self._bounds = QRectF()
        self._path = QPainterPath()
        # R4d (0164-ruling.md): the intersection clip -- DERIVED, never
        # stored; None = unclipped. Set only by `sync_roof_clips`.
        self._clip_region = None
        self._seams = []
        self._clip_ext = (0.0, 0.0)
        self.clip_warnings = []
        self._syncing_clips = False
        # the marker menu's "Outline": a persistent, on-demand highlight of
        # this roof's footprint, so a blue dot in a crowded plan can be tied
        # to the region it governs. Off by default; toggled per roof, not saved.
        self._show_outline = False
        self.marker = RoofEndMarkerItem(self)
        # R4c (0154-ruling.md sec3): five grips, shown only while selected
        self.grips = [RoofGripItem(self, kind) for kind
                      in RoofGripItem.KINDS + RoofGripItem.DORMER_KINDS]
        self.rebuild()

    @staticmethod
    def _normalized_pair(value):
        """A bare number -> `[v, v]`; a 2-item sequence -> `[a, b]`, stored
        as floats either way. The one normalisation point for `span_in`/
        `overhang_in`'s setters, so "someone assigned a scalar" can never
        silently collapse an already-asymmetric pair one field at a time."""
        if isinstance(value, (list, tuple)):
            a, b = value
            return [float(a), float(b)]
        v = float(value)
        return [v, v]

    @property
    def hip_run_in(self):
        return list(self._hip_run_in)

    @hip_run_in.setter
    def hip_run_in(self, value):
        """`[a, b]` with None for a derived end; a bare number sets both."""
        if value is None:
            self._hip_run_in = [None, None]
        elif isinstance(value, (list, tuple)):
            a, b = value
            self._hip_run_in = [None if a is None else max(0.0, float(a)),
                                None if b is None else max(0.0, float(b))]
        else:
            v = max(0.0, float(value))
            self._hip_run_in = [v, v]

    @property
    def span_in(self):
        return list(self._span_in)

    @span_in.setter
    def span_in(self, value):
        pair = self._normalized_pair(value)
        if getattr(self, "form", "gable") == "shed":
            pair[1] = 0.0                       # a shed has no right plane
        self._span_in = pair

    @property
    def overhang_in(self):
        return list(self._overhang_in)

    @overhang_in.setter
    def overhang_in(self, value):
        pair = self._normalized_pair(value)
        if getattr(self, "form", "gable") == "shed":
            pair[1] = 0.0
        self._overhang_in = pair

    @property
    def end_overhang_in(self):
        return list(self._end_overhang_in)

    @end_overhang_in.setter
    def end_overhang_in(self, value):
        """Per-END overhang `[end0, end1]` along the ridge axis -- the rake
        (gable overhang) at each GABLE end, and a dormer's FACE eave at its
        own end (`end0`). The plane continues flat past a gable end, so the
        ridge holds to the rake (`surface_height`'s gable branch is unchanged)
        and only the painted eaves and the end line reach further out. A hip
        end ignores it (it has its own run/overhang). Non-negative; `None`
        and a bare number normalise like the other pairs. Default `[0, 0]`,
        so a roof written before this field round-trips unchanged."""
        if value is None:
            self._end_overhang_in = [0.0, 0.0]
            return
        pair = self._normalized_pair(value)
        self._end_overhang_in = [max(0.0, pair[0]), max(0.0, pair[1])]

    @property
    def wall_span_in(self):
        """DORMER_CONROLS.md control C: the dormer's two vertical WALL offsets
        `[left, right]` from the ridge -- the black cheek walls. Decoupled
        from `span_in` (the roof's eaves line, which sets the pitch): moving a
        wall slides it between the ridge and the roof line WITHOUT changing the
        pitch (the spec's central rule). `None` (the default and what a record
        without the field means) falls back to `span_in`, so a wall that was
        never moved sits on the eaves line exactly as before."""
        if getattr(self, "_wall_span_in", None) is None:
            return list(self._span_in)
        return list(self._wall_span_in)

    @wall_span_in.setter
    def wall_span_in(self, value):
        if value is None:
            self._wall_span_in = None
            return
        pair = self._normalized_pair(value)
        if getattr(self, "form", "gable") == "shed":
            pair[1] = 0.0                        # a shed has no right plane
        self._wall_span_in = pair

    @property
    def box_half_in(self):
        """DORMER_CONROLS.md control B (left/right): the blue frame's half-width
        per side `[left, right]`. It CLIPS the roof lines -- drawn only out to
        this width -- so stretching the frame in trims the diagonal roof lines.
        `None` (the default, and a record without the field) means no clip: the
        roof lines run to their full valley."""
        return None if getattr(self, "_box_half_in", None) is None else list(self._box_half_in)

    @box_half_in.setter
    def box_half_in(self, value):
        self._box_half_in = None if value is None else self._normalized_pair(value)

    def set_form(self, form: str):
        """Change the form; a shed drops its right span and overhang to 0,
        a gable given back a right side takes the left span's value."""
        form = form if form in ("gable", "shed") else "gable"
        if form == self.form:
            return
        self.form = form
        if form == "shed":
            self.span_in = self._span_in           # the setter clamps
            self.overhang_in = self._overhang_in
        elif self._span_in[1] < 1.0:
            self.span_in = [self._span_in[0], self._span_in[0]]
        self.rebuild()

    @property
    def p1(self) -> QPointF:
        return QPointF(self._p1)

    @property
    def p2(self) -> QPointF:
        return QPointF(self._p2)

    def set_ridge(self, p1: QPointF, p2: QPointF):
        self._p1, self._p2 = QPointF(p1), QPointF(p2)
        self.rebuild()

    def length(self) -> float:
        return math.hypot(self.p2.x() - self.p1.x(), self.p2.y() - self.p1.y())

    # -- R5b: dormers --------------------------------------------------------
    def is_dormer(self) -> bool:
        host = self.host
        return host is not None and not sip.isdeleted(host)

    def dormers(self):
        """The dormers standing on THIS roof, live in its scene."""
        sc = self.scene()
        if sc is None:
            return []
        return [it for it in sc.items()
                if isinstance(it, RoofItem) and not sip.isdeleted(it)
                and it.host is self]

    def _derive_back_end(self):
        """`p2` = where the ridge, run from the face `p1` in its own
        direction, meets the host's plane at `ridge_h_in` (0191-ruling.md
        sec1: derived, still written). Left where it is when the ridge
        cannot meet the host -- the dialog refuses that state before it is
        applied, so it is only ever transient (a drag in progress).

        A SHED dormer derives nothing (0256-report.md): its ridge is its
        high edge, lying ON the host plane parallel to the host's ridge,
        and both its ends are faces -- the sketched `p2` is the second face,
        not a point to find."""
        if getattr(self, "form", "gable") == "shed":
            return
        dx, dy = self._p2.x() - self._p1.x(), self._p2.y() - self._p1.y()
        ln = math.hypot(dx, dy)
        if ln < 1e-9:
            return
        ux, uy = dx / ln, dy / ln
        t = meet_along(self.host, self._p1, Pt(ux, uy), self.ridge_h_in)
        if t is not None:
            t = max(t, 1.0)
            self._p2 = QPointF(self._p1.x() + ux * t, self._p1.y() + uy * t)

    def dormer_stands(self) -> bool:
        """Whether this dormer meets its host and can stand (0191-ruling.md
        sec1). A GABLE dormer's ridge must rise along its own axis to meet
        the host's plane at `ridge_h_in`; a SHED dormer's high edge must lie
        on or just under (`_SHED_EDGE_TOL_IN`) the host at both ends. The
        End-On dialog refuses the same states before `apply` (`dormer_meet_in`);
        the Shift-build path (`view._build_dormer_auto`), which has no dialog
        to refuse in, asks this of the finished item instead. False for a roof
        with no live host."""
        from floorplanner.roofclip import Pt, meet_along, surface_height
        host = self.host
        if host is None or sip.isdeleted(host):
            return False
        if self.form == "shed":
            under = min(surface_height(host, Pt(p.x(), p.y())) - self.ridge_h_in
                        for p in (self.p1, self.p2))
            return under >= -_SHED_EDGE_TOL_IN
        ux, uy, _, _ = self._axis()
        return meet_along(host, Pt(self.p1.x(), self.p1.y()),
                          Pt(ux, uy), self.ridge_h_in) is not None

    def remove_with_dormers(self):
        """Delete this roof and every dormer standing on it (0191-ruling.md
        sec1) -- one gesture. Roof deletion has no undo today (none did
        before R5b either); named in 0192-report.md, not hidden."""
        sc = self.scene()
        if sc is None:
            return
        for d in self.dormers():
            sc.removeItem(d)
        sc.removeItem(self)

    def toggle_outline(self):
        """Show or hide this roof's footprint outline (the marker menu's
        'Outline') -- an on-demand highlight of the region the roof governs,
        independent of selection and not persisted."""
        self._show_outline = not getattr(self, "_show_outline", False)
        self.update()

    @property
    def uid(self) -> str:
        """The roof's session label (`RF1`), minted on first read; a load
        adopts the file's own id (labels.py)."""
        if getattr(self, "_uid", None) is None:
            from floorplanner import labels as _labels
            self._uid = _labels.mint("RF")
        return self._uid

    def hip_extension(self, end: int, gable=None, span=None, run=None):
        """`(run, overhang)` along the ridge axis, beyond ridge end `end`
        (0 = `p1`, 1 = `p2`), that a HIP end adds to the footprint:
        `(0, 0)` for a gable end. The run is the end's own `hip_run_in`
        when set (0258), else the mean of the two side spans; the overhang
        the mean of the two side overhangs (class docstring). `gable`/
        `span`/`run` override the stored values -- the parameters dialog
        previews an edit before it is applied."""
        flags = self.gable if gable is None else gable
        spans = self._span_in if span is None else span
        runs = self._hip_run_in if run is None else run
        if flags[end]:
            return 0.0, 0.0
        own = runs[end] if runs is not None and end < len(runs) else None
        return (((spans[0] + spans[1]) / 2.0) if own is None else float(own),
                (self._overhang_in[0] + self._overhang_in[1]) / 2.0)

    def _axis(self):
        """(ux, uy, nx, ny): the ridge's unit direction p1->p2 and its
        +90deg-rotated normal (the LEFT side, `span_in[0]`)."""
        dx, dy = self.p2.x() - self.p1.x(), self.p2.y() - self.p1.y()
        ln = math.hypot(dx, dy) or 1.0
        return dx / ln, dy / ln, -dy / ln, dx / ln

    def _extended_ridge(self, gable=None):
        """`(a1, a2)`: the ridge endpoints pushed outward along the axis by
        each end's hip extension (run + overhang), i.e. the ALONG-axis
        extent of the outer eave lines. Equal to `(p1, p2)` for two gable
        ends."""
        ux, uy, _, _ = self._axis()
        r1, o1 = self.hip_extension(0, gable)
        r2, o2 = self.hip_extension(1, gable)
        # a GABLE end's rake / face overhang pushes its eaves and end line
        # out along the axis (the plane continues flat, so the ridge holds
        # to the rake); a hip end has its own run + overhang and ignores it.
        flags = self.gable if gable is None else gable
        eo = self._end_overhang_in
        e1 = r1 + o1 + (eo[0] if flags[0] else 0.0)
        e2 = r2 + o2 + (eo[1] if flags[1] else 0.0)
        return (QPointF(self.p1.x() - ux * e1, self.p1.y() - uy * e1),
                QPointF(self.p2.x() + ux * e2, self.p2.y() + uy * e2))

    def _eave_ends(self):
        """(eave1_a, eave1_b, eave2_a, eave2_b): the two eave-line endpoints
        on each side, offset perpendicular to the ridge by that SIDE's own
        span + overhang (R4a: per-side, no longer a single shared reach),
        and pushed past a hip end along the axis (R4b: `hip_extension`)."""
        _, _, nx, ny = self._axis()
        a1, a2 = self._extended_ridge()
        # DORMER_CONROLS.md: the eave reaches wall + overhang (control C + E);
        # `wall_span_in` defaults to `span_in`, so a plain roof is unchanged
        # while a dormer with pulled-in walls truncates its roof at the eave.
        wall = self.wall_span_in
        reach_l = wall[0] + self._overhang_in[0]
        reach_r = wall[1] + self._overhang_in[1]
        return (QPointF(a1.x() + nx * reach_l, a1.y() + ny * reach_l),
               QPointF(a2.x() + nx * reach_l, a2.y() + ny * reach_l),
               QPointF(a1.x() - nx * reach_r, a1.y() - ny * reach_r),
               QPointF(a2.x() - nx * reach_r, a2.y() - ny * reach_r))

    def eaves_start_polygon(self, gable=None, span=None) -> QPolygonF:
        """The footprint at the EAVES-START line (`span_in`, no overhang) --
        the plane `eaves_h_in` applies at, and the rectangle whose covered
        rooms the `room_top` binding reads. A hip end extends it by that
        end's hip RUN (not its overhang). `gable`/`span` override the
        stored values, for a preview."""
        ux, uy, nx, ny = self._axis()
        r1, _ = self.hip_extension(0, gable, span)
        r2, _ = self.hip_extension(1, gable, span)
        a1 = QPointF(self.p1.x() - ux * r1, self.p1.y() - uy * r1)
        a2 = QPointF(self.p2.x() + ux * r2, self.p2.y() + uy * r2)
        sl, sr = self._span_in if span is None else span
        return QPolygonF([
            QPointF(a1.x() + nx * sl, a1.y() + ny * sl),
            QPointF(a2.x() + nx * sl, a2.y() + ny * sl),
            QPointF(a2.x() - nx * sr, a2.y() - ny * sr),
            QPointF(a1.x() - nx * sr, a1.y() - ny * sr)])

    def rebuild(self):
        self.prepareGeometryChange()
        if self.is_dormer():
            self._derive_back_end()
        e1a, e1b, e2a, e2b = self._eave_ends()
        pad = 4.0
        xs = [self.p1.x(), self.p2.x(), e1a.x(), e1b.x(), e2a.x(), e2b.x()]
        ys = [self.p1.y(), self.p2.y(), e1a.y(), e1b.y(), e2a.y(), e2b.y()]
        self._bounds = QRectF(min(xs) - pad, min(ys) - pad,
                              max(xs) - min(xs) + 2 * pad,
                              max(ys) - min(ys) + 2 * pad)
        # D85: the ridge alone used to be the only clickable part -- for a
        # ridge picked short (or barely picked at all, span/overhang doing
        # the rest of the visual reach), the DASHED eave/gable lines paint()
        # draws are most of what actually appears on screen, and none of it
        # was selectable. The shape now covers everything paint() draws
        # (ridge heavy, both eave lines, each end's own end line -- a gable
        # line or a hip end's end eave -- and a hip end's two hip lines) so
        # the reported bug -- a roof visible but not selectable -- cannot
        # recur regardless of how thin the ridge is.
        path = QPainterPath()
        path.moveTo(self.p1)
        path.lineTo(self.p2)
        path.moveTo(e1a)
        path.lineTo(e1b)
        path.moveTo(e2a)
        path.lineTo(e2b)
        path.moveTo(e1a)
        path.lineTo(e2a)
        path.moveTo(e1b)
        path.lineTo(e2b)
        if not self.gable[0]:
            path.moveTo(e1a)
            path.lineTo(self.p1)
            path.lineTo(e2a)
        if not self.gable[1]:
            path.moveTo(e1b)
            path.lineTo(self.p2)
            path.lineTo(e2b)
        self._path = path
        marker = getattr(self, "marker", None)   # absent mid-__init__
        if marker is not None:
            marker.sync_position()
        for g in getattr(self, "grips", ()):
            g.sync_position()
        # R4d: any change to this roof's true rectangle re-clips the floor
        if self.scene() is not None and hasattr(self, "grips"):
            sync_roof_clips(self.scene(), self.floor)
            # R5b: a host's edit re-derives every dormer standing on it
            # (their back ends and cheeks read the host's plane)
            if not self.is_dormer():
                for d in self.dormers():
                    d.rebuild()

    def apply_clip(self, clip):
        """Take a `RoofClip` from `sync_roof_clips`: what to paint and hit
        while NOT selected. Repaints; never touches the true geometry."""
        self._clip_region = clip.region
        # roofclip.py is Qt-free (R4e): its points come back as plain
        # `Pt`s -- QPointF from here on, since these get drawn
        self._seams = [(QPointF(p.x(), p.y()), QPointF(q.x(), q.y()))
                       for p, q in clip.seams]
        self._clip_ext = tuple(getattr(clip, "ext", (0.0, 0.0)))
        self.clip_warnings = list(clip.warnings)
        self.update()

    def is_clipped(self) -> bool:
        """True while the drawn/hit roof is less than its true rectangle:
        a clip exists and the roof is not selected (0164-ruling.md sec2:
        selected = unclipped)."""
        return self._clip_region is not None and not self.isSelected()

    def seams(self):
        """The seam segments (solid edges) this roof draws -- `[]` while
        selected, since the whole rectangle shows then."""
        return [] if self.isSelected() else list(self._seams)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            # the grips exist only for a selected roof. A DORMER shows its own
            # A-G controls (the dormer kinds plus the ridge, which is G) and
            # NOT the universal eave/end grips -- those duplicated the frame
            # and walls as extra blue knobs; a plain roof shows the universal
            # five and none of the dormer controls.
            dormer = self.is_dormer()
            for g in getattr(self, "grips", ()):
                if dormer:
                    vis = g.kind in RoofGripItem.DORMER_KINDS or g.kind == "ridge"
                else:
                    vis = g.kind in RoofGripItem.KINDS
                g.setVisible(bool(value) and vis)
            # R4d: selected = unclipped; deselect re-clips (the region is
            # still current -- nothing moved -- so a repaint is the re-clip)
            self.update()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged:
            # entering a scene: clip against what is there; leaving one:
            # the others must un-clip against this roof (see removal below)
            if value is not None and hasattr(self, "grips"):
                sync_roof_clips(value, self.floor)
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneChange:
            old = self.scene()
            if value is None and old is not None and hasattr(self, "grips"):
                sync_roof_clips(old, self.floor, exclude=self)
        return super().itemChange(change, value)

    # -- R4c: direct manipulation (0154-ruling.md sec3, the five grips) -----
    # Every drag lands ON the grid, never moves by it (0070-ruling.md sec3's
    # class): the quantity snapped is the ABSOLUTE coordinate of the line
    # being dragged, measured along the ridge's own axis or normal from the
    # scene origin -- for an axis-aligned ridge that is literally the line's
    # x or y landing on `wall_snap_in`; for a 45deg wing it is the same rule
    # in the roof's own frame (a rotated grid of the same pitch, anchored at
    # the origin), the only sense in which a diagonal line can be "on" a
    # square grid. A displacement snap would carry any existing offset
    # forever -- exactly the wall-drag fault 0070-ruling.md measured -- so nothing
    # here snaps a delta.

    def drag_eave(self, side: int, scene_pt: QPointF):
        """Eave-edge grip: move that side's OUTER eave line to (the snapped)
        `scene_pt`; the overhang rides along, so `span_in[side]` is what
        changes. The line cannot cross the ridge: the span stays >= 1in."""
        _, _, nx, ny = self._axis()
        origin_n = self.p1.x() * nx + self.p1.y() * ny
        cursor_n = scene_pt.x() * nx + scene_pt.y() * ny
        perp = wall_snap_len(cursor_n) - origin_n
        reach = perp if side == 0 else -perp
        if side == 1 and self.form == "shed":
            return                              # no right plane to drag
        spans = list(self._span_in)
        spans[side] = max(1.0, reach - self._overhang_in[side])
        self.span_in = spans
        self.rebuild()

    # -- the dormer controls (the six grips of the Build-Dormer picture) -----
    # `drag_eave` above moves a side's OUTER eave and lets the span change;
    # these move each of the dormer's own lines independently: the WALL (the
    # span line), the SOFFIT (the per-side eave = overhang), the SETBACK (the
    # face along the ridge) and the FACE eave (the per-end overhang, `end0`).
    def _perp_of(self, scene_pt: QPointF) -> float:
        """(Snapped) perpendicular distance of `scene_pt` from the ridge, in
        the +left normal's sense -- the quantity every side grip lands on."""
        _, _, nx, ny = self._axis()
        origin_n = self.p1.x() * nx + self.p1.y() * ny
        return wall_snap_len(scene_pt.x() * nx + scene_pt.y() * ny) - origin_n

    def drag_wall(self, side: int, scene_pt: QPointF):
        """Control C -- the side WALL grip: move this side's vertical wall to
        the cursor. The wall is `wall_span_in`, decoupled from `span_in` (the
        roof's eaves line and its pitch): the roof is untouched, so the PITCH
        does not change (DORMER_CONROLS.md: the only way to change the pitch is
        the dialog). Wall stays >= 1in off the ridge."""
        if side == 1 and self.form == "shed":
            return                               # a shed has no right plane
        reach = self._perp_of(scene_pt)
        reach = reach if side == 0 else -reach
        walls = self.wall_span_in
        walls[side] = max(1.0, reach)
        dv = self._face_valley_perp(side)        # the roof line is the limit
        if dv is not None:
            walls[side] = min(walls[side], dv)
        self.wall_span_in = walls
        self.rebuild()

    def _eave_reach(self, side):
        """Control E's result: the EAVE reach from the ridge on a side -- the
        wall (C) plus its overhang. The dormer roof reaches this far; its side
        eave (green) is drawn here."""
        return self.wall_span_in[side] + self._overhang_in[side]

    def drag_soffit(self, side: int, scene_pt: QPointF):
        """Control E -- the side EAVE grip: the eave OVERHANG beyond this side's
        WALL (C). The eave sits at wall + overhang; dragged in to the wall the
        overhang is 0, dragged out it extends to the roof line (the valley)."""
        if side == 1 and self.form == "shed":
            return
        reach = self._perp_of(scene_pt)
        reach = reach if side == 0 else -reach
        wall = self.wall_span_in[side]
        dv = self._face_valley_perp(side)        # the eave stops at the roof line
        hi = dv if dv is not None else max(reach, wall)
        ohs = list(self._overhang_in)
        ohs[side] = max(0.0, min(hi, reach) - wall)
        self.overhang_in = ohs
        self.rebuild()

    def drag_setback(self, scene_pt: QPointF):
        """Control D -- the gable FACE grip: slide the face (`p1`) along the
        ridge to the cursor; the back end re-derives (a dormer). The grip sits
        ON the face wall, so the cursor is read directly. The face stays at
        least `MIN_RIDGE_LEN_IN` off the back."""
        ux, uy, _, _ = self._axis()
        target = wall_snap_len(scene_pt.x() * ux + scene_pt.y() * uy)
        back_u = self.p2.x() * ux + self.p2.y() * uy
        target = min(target, back_u - MIN_RIDGE_LEN_IN)
        delta = target - (self.p1.x() * ux + self.p1.y() * uy)
        self.set_ridge(QPointF(self.p1.x() + ux * delta, self.p1.y() + uy * delta),
                       self.p2)

    def drag_face_eave(self, scene_pt: QPointF):
        """Face-EAVE grip: set the FACE overhang (`end_overhang_in[0]`) -- how
        far the eave projects down-slope past the face. The grip rides on the
        eave line; dragged up past the face it clamps to 0 (it cannot pass the
        face, the picture's rule)."""
        ux, uy, _, _ = self._axis()
        cursor_u = wall_snap_len(scene_pt.x() * ux + scene_pt.y() * uy)
        face_u = self.p1.x() * ux + self.p1.y() * uy
        eos = list(self._end_overhang_in)
        eos[0] = max(0.0, face_u - cursor_u)
        self.end_overhang_in = eos
        self.rebuild()

    def drag_end(self, end: int, scene_pt: QPointF):
        """Gable-end grip: move that ridge endpoint ALONG the ridge axis so
        the end line (gable line, or a hip end's outer eave) lands where the
        cursor projects; direction is preserved -- the roof stays the same
        rectangle, longer or shorter. A hip end's extension rides along.
        The ridge keeps at least `MIN_RIDGE_LEN_IN`. The grip itself sits
        `GRIP_END_OFFSET_IN` outside the line (`RoofGripItem`), so the
        cursor is read that much inward -- the LINE lands on the grid."""
        ux, uy, _, _ = self._axis()
        origin_u = self.p1.x() * ux + self.p1.y() * uy
        cursor_u = scene_pt.x() * ux + scene_pt.y() * uy
        cursor_u += GRIP_END_OFFSET_IN if end == 0 else -GRIP_END_OFFSET_IN
        landed = wall_snap_len(cursor_u) - origin_u        # along, from p1
        if end == 1 and self.is_dormer() and self.form != "shed":
            # (a SHED dormer's second end is its second face, not a derived
            # point -- 0256-report.md; it is dragged like any roof end below)
            # R5b, Patrick's look at the first dormer (2026-09-24: "a missing
            # control knob on the ridge of the dormer where it meets the
            # roof"): the back end is derived from the ridge height, so its
            # grip sets the RIDGE HEIGHT -- the dragged point (on the grid
            # along the ridge) is where the ridge is to meet the host, and
            # the ridge height becomes the host's surface there; the
            # rebuild then derives the back end onto that very point --
            # ON THE RISING SIDE ONLY (0195-ruling.md sec2): past the host's
            # crest, or its footprint, a height read there is one the host
            # already reached nearer the face, and the derivation would fold
            # the end back short of the cursor. So the drag is clamped to
            # `rising_reach`: the grip tracks the cursor everywhere it can
            # go and stops dead where it cannot.
            #
            # 0277 (his garage, wiscaway2026-10-13R1): MEASURED FROM WHERE
            # THE RIDGE ENTERS THE HOST, not from the face. A dormer whose
            # face stands past the host's eave line (a garage gable
            # projecting 48in beyond the main roof) had its reach read from
            # a point outside the host's footprint -- 0.0, every move
            # refused, the knob dead and silent -- while its ridge met the
            # host's slope perfectly well a few feet further in.
            u = Pt(ux, uy)
            t0 = entry_along(self.host, Pt(self.p1.x(), self.p1.y()), u)
            if t0 is None:
                self._refuse_drag("this roof's ridge never crosses its host roof")
                return
            if t0 > 0.0:
                t0 += 1e-3                     # just inside, where heights are the host's
            reach = t0 + rising_reach(
                self.host, Pt(self.p1.x() + ux * t0, self.p1.y() + uy * t0), u)
            if reach < max(MIN_RIDGE_LEN_IN, t0 + 1e-3):
                self._refuse_drag("the host roof does not rise along this ridge")
                return                          # nowhere to rise to: refused
            a = min(max(MIN_RIDGE_LEN_IN, t0, landed), reach)
            pt = QPointF(self.p1.x() + ux * a, self.p1.y() + uy * a)
            h = surface_height(self.host, Pt(pt.x(), pt.y()))
            if h > self.eaves_h_in + 1.0:
                self.ridge_h_in = float(h)
                self.rebuild()
            return
        L = self.length()
        run, oh = self.hip_extension(end)
        ext = run + oh
        if end == 0:
            a_end = min(landed + ext, L - MIN_RIDGE_LEN_IN)
            self.set_ridge(QPointF(self.p1.x() + ux * a_end,
                                   self.p1.y() + uy * a_end), self.p2)
        else:
            a_end = max(landed - ext, MIN_RIDGE_LEN_IN)
            self.set_ridge(self.p1, QPointF(self.p1.x() + ux * a_end,
                                            self.p1.y() + uy * a_end))

    def _refuse_drag(self, why: str):
        """0277: a grip that cannot follow the cursor says so, in the status
        bar, instead of doing nothing silently."""
        sc = self.scene()
        views = sc.views() if sc is not None else []
        win = getattr(views[0], "win", None) if views else None
        if win is not None:
            win.status(f"Roof grip: {why}.")

    def drag_ridge(self, scene_pt: QPointF):
        """Ridge grip: slide the ridge LATERALLY between fixed eave edges
        (0140-ruling.md sec4's deferral, due here) -- both eaves-start lines
        stay exactly where they are, the two spans rebalance, and the ridge
        lands on the grid. Clamped so neither span drops under 1in."""
        _, _, nx, ny = self._axis()
        origin_n = self.p1.x() * nx + self.p1.y() * ny
        cursor_n = scene_pt.x() * nx + scene_pt.y() * ny
        d = wall_snap_len(cursor_n) - origin_n
        span_l, span_r = self._span_in
        if self.form == "shed":
            # 0256-report.md (his report: "every mouse move shrinks the
            # vertical limits of the dormer"): a shed has no right plane, so
            # the gable clamp `1.0 - span_r` with span_r = 0 forced d >= 1
            # and every move walked the ridge an inch toward the eave. A
            # shed's ridge is its HIGH EDGE: the drag moves that edge, the
            # eave line stays, the one span follows (never under 1in).
            d = min(span_l - 1.0, d)
            if abs(d) < 1e-9:
                return
            p1 = QPointF(self.p1.x() + nx * d, self.p1.y() + ny * d)
            p2 = QPointF(self.p2.x() + nx * d, self.p2.y() + ny * d)
            if self.is_dormer():
                # a shed DORMER's high edge lies ON the host: the edge keeps
                # to the host's surface where it lands (the End-On dialog's
                # standing rule), refused where the host there is not above
                # the face
                h = min(surface_height(self.host, Pt(p.x(), p.y())) for p in (p1, p2))
                if h <= self.eaves_h_in + 1.0:
                    return
                self.ridge_h_in = float(h)
            self.span_in = [span_l - d, 0.0]
            self.set_ridge(p1, p2)
            return
        if self.is_dormer():
            # DORMER_CONROLS.md controls A/G: move the ridge laterally HOLDING
            # the pitch. span_in (the eaves line, and so the roof-line angle)
            # is unchanged -- the roof translates with the ridge; the walls (C)
            # stay where they are, so `wall_span_in` shifts the opposite way
            # and the walls run up to the new roof-line intersections. Clamped
            # so neither wall drops under 1in off the new ridge.
            walls = self.wall_span_in
            d = max(-(walls[1] - 1.0), min(walls[0] - 1.0, d))
            if abs(d) < 1e-9:
                return
            self.wall_span_in = [walls[0] - d, walls[1] + d]
            self.set_ridge(QPointF(self.p1.x() + nx * d, self.p1.y() + ny * d),
                           QPointF(self.p2.x() + nx * d, self.p2.y() + ny * d))
            return
        d = max(1.0 - span_r, min(span_l - 1.0, d))
        self.span_in = [span_l - d, span_r + d]
        self.set_ridge(QPointF(self.p1.x() + nx * d, self.p1.y() + ny * d),
                       QPointF(self.p2.x() + nx * d, self.p2.y() + ny * d))

    def drag_box_top(self, scene_pt: QPointF):
        """DORMER_CONROLS.md control B (top): move the APEX up or down the host
        slope, HOLDING the pitch -- the whole dormer roof grows or shrinks with
        the ridge, the roof lines keep their angle. Reuses the back-end meet
        logic to set the ridge height from the host, then raises the eaves with
        it so the pitch (and the roof-line angle) is unchanged."""
        if self._span_in[0] <= _CLIP_EPS_IN or self.ridge_h_in <= self.eaves_h_in:
            return
        pitch = (self.ridge_h_in - self.eaves_h_in) / self._span_in[0]
        self.drag_end(1, scene_pt)               # sets ridge_h from the host meet
        self.eaves_h_in = self.ridge_h_in - pitch * self._span_in[0]
        self.rebuild()

    def boundingRect(self) -> QRectF:
        # 0279: the ridge callout is painted beside the ridge's middle at a
        # fixed pixel size; on a short roof it reached past `_bounds`
        from floorplanner.annotations import callout_rect, callout_text, callouts_shown, view_lod
        if (callouts_shown() and floor_display_mode(self.floor) == "active"
                and callout_text(self)):
            lod = view_lod(self)
            m = QPointF((self.p1.x() + self.p2.x()) / 2.0, (self.p1.y() + self.p2.y()) / 2.0)
            return self._bounds.united(callout_rect(
                lod, QPointF(m.x() + 4.0 / lod, m.y() - 4.0 / lod), callout_text(self)))
        return self._bounds

    def selection_outline(self) -> QPolygonF:
        """The tight, ridge-oriented rectangle the selection is drawn as:
        the four outer eave corners (`_eave_ends`, so a hip end's
        extension is inside it too). Axis-aligned only when the ridge is."""
        e1a, e1b, e2a, e2b = self._eave_ends()
        return QPolygonF([e1a, e1b, e2b, e2a])

    def _dormer_wall_lines(self):
        """A DORMER's three standing walls in plan (`[(a, b), ...]`): the face
        wall across the span at the face, and the two cheek walls running up
        the slope from the face to where each meets the host (the host surface
        rising to the dormer's own eaves height, `meet_along`). Drawn solid
        black (the outside-wall format). `[]` for a roof with no host.
        Memoised on this roof's and its host's geometry (paint reads it)."""
        host = self.host
        if host is None or sip.isdeleted(host):
            return []
        key = (self.geometry_key(), host.geometry_key(), tuple(self.wall_span_in))
        memo = getattr(self, "_wall_memo", None)
        if memo is not None and memo[0] == key:
            return memo[1]
        from floorplanner.roofclip import Pt, meet_along
        ux, uy, nx, ny = self._axis()
        p1, p2 = self.p1, self.p2
        # control C: the black side walls stand at `wall_span_in`; each runs up
        # the slope from the face and is TRUNCATED where the roof line crosses
        # it (the valley at this wall's perp) -- past there the dormer roof has
        # met the host and there is no wall. The face wall closes the front.
        s0, s1 = self.wall_span_in
        left = QPointF(p1.x() + nx * s0, p1.y() + ny * s0) if s0 > _CLIP_EPS_IN else None
        right = QPointF(p1.x() - nx * s1, p1.y() - ny * s1) if s1 > _CLIP_EPS_IN else None
        out = []
        if left is not None and right is not None:
            out.append((left, right))              # the face wall, wall to wall
        elif left is not None:
            out.append((QPointF(p1), left))        # a shed: ridge to its one side
        for side, start in ((0, left), (1, right)):
            if start is None:
                continue
            sign = 1.0 if side == 0 else -1.0
            dv = self._face_valley_perp(side)
            if dv is not None and dv > _CLIP_EPS_IN and self.wall_span_in[side] < dv:
                # the valley at this wall's perp -- where the roof line crosses
                # the wall and the wall ends
                corner = QPointF(p1.x() + sign * nx * dv, p1.y() + sign * ny * dv)
                f = self.wall_span_in[side] / dv
                out.append((start, QPointF(p2.x() + (corner.x() - p2.x()) * f,
                                           p2.y() + (corner.y() - p2.y()) * f)))
            else:
                t = meet_along(host, Pt(start.x(), start.y()), Pt(ux, uy),
                               self.eaves_h_in)
                if t is None or t <= 0.0:
                    t = self.length()
                out.append((start, QPointF(start.x() + ux * t, start.y() + uy * t)))
        self._wall_memo = (key, out)
        return out

    def dormer_face_window_spans(self):
        """Phase C (0291): each of the dormer's own face windows as a
        `(start, end)` segment along its face wall in plan -- a READ-ONLY
        projection of `self.openings` (the single record the dormer owns and
        the End-On dialog edits; `fp3d._face_openings` reads the same list for
        3D). `[]` for a roof with no host, no face wall, or no openings.

        The face wall is `_dormer_wall_lines()[0]` and the anchor is resolved
        along its OWN plan length, from its left end -- the twin of
        `viewer.fp3d.opening_span`, kept local so the scene layer never imports
        the Qt-free viewer. A window whose code will not parse, or that lands
        wholly off the face, is skipped (the dialog validates on entry)."""
        host = self.host
        if host is None or sip.isdeleted(host):
            return []
        ops = getattr(self, "openings", None)
        if not ops:
            return []
        lines = self._dormer_wall_lines()
        if not lines:
            return []
        a, b = lines[0]                      # the face wall, left -> right
        dx, dy = b.x() - a.x(), b.y() - a.y()
        length = math.hypot(dx, dy)
        if length < _CLIP_EPS_IN:
            return []
        ux, uy = dx / length, dy / length

        def _span(anchor, width):
            frm = anchor.get("from", "v1")
            off = float(anchor.get("offset_in", 0.0))
            if frm == "v2":
                s0 = length - off - width
            elif frm == "center":
                s0 = length / 2.0 + off - width / 2.0
            else:
                s0 = off
            return s0, s0 + width

        out = []
        for o in ops:
            try:
                w, _h = parse_wwhh(o["code"])
            except (KeyError, ValueError, TypeError):
                continue
            u0, u1 = _span(o.get("anchor", {}), w)
            u0, u1 = max(0.0, u0), min(length, u1)
            if u1 - u0 <= 1e-6:
                continue
            out.append((QPointF(a.x() + ux * u0, a.y() + uy * u0),
                        QPointF(a.x() + ux * u1, a.y() + uy * u1)))
        return out

    def _valley_perp(self, host, sign, pitch):
        """The perpendicular distance from the ridge, at the FACE, where this
        side's cheek plane (sloping at `pitch` from the ridge) meets the host
        surface -- the roof line's outer reach. None when the face does not
        stand above the host, or the cheek never comes down to it."""
        from floorplanner.roofclip import Pt, surface_height
        _, _, nx, ny = self._axis()
        p1 = self.p1

        def f(d):
            pt = Pt(p1.x() + sign * nx * d, p1.y() + sign * ny * d)
            return (self.ridge_h_in - pitch * d) - surface_height(host, pt)

        if f(0.0) <= 0.0:                       # the face is not above the host
            return None
        hi = (self.ridge_h_in - self.eaves_h_in) / pitch + self.length() + 240.0
        if f(hi) > 0.0:                         # never comes down to the host
            return None
        lo = 0.0
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if f(mid) > 0.0:
                lo = mid
            else:
                hi = mid
        return hi

    def _face_valley_perp(self, side):
        """This side's roof-line reach at the face (`_valley_perp` with the
        current pitch) -- the outer limit for the wall (C) and the eave (E).
        None when there is no host or no valley."""
        host = self.host
        if host is None or sip.isdeleted(host) or self._span_in[side] <= _CLIP_EPS_IN:
            return None
        pitch = (self.ridge_h_in - self.eaves_h_in) / self._span_in[side]
        if pitch <= _CLIP_EPS_IN:
            return None
        return self._valley_perp(host, 1.0 if side == 0 else -1.0, pitch)

    def _host_edge_perp(self, side):
        """How far this side's frame can reach before it leaves the host's
        footprint -- the spec's limit ("the roof's lower edge it sits on").
        None with no host or a face off the host."""
        host = self.host
        if host is None or sip.isdeleted(host):
            return None
        from floorplanner.roofclip import Pt, _contains, footprint_polygon
        _, _, nx, ny = self._axis()
        sign = 1.0 if side == 0 else -1.0
        fp = footprint_polygon(host)
        p1 = self.p1
        if not _contains(fp, Pt(p1.x(), p1.y())):
            return None
        d, step = 0.0, 6.0
        while d < 4000.0 and _contains(fp, Pt(p1.x() + sign * nx * (d + step),
                                              p1.y() + sign * ny * (d + step))):
            d += step
        return d

    def drag_box_side(self, side: int, scene_pt: QPointF):
        """DORMER_CONROLS.md control B (left/right): stretch the frame's edge.
        It clips the roof line, so it stays between this side's WALL and the
        host's lower edge."""
        reach = self._perp_of(scene_pt)
        reach = reach if side == 0 else -reach
        box = self.box_half_in
        if box is None:
            dv = self._face_valley_perp(side)
            box = [dv or self._span_in[0], None]
            box[1] = self._face_valley_perp(1) or self._span_in[1]
        lo = self.wall_span_in[side]
        hi = self._host_edge_perp(side)
        box[side] = max(lo, reach if hi is None else min(hi, reach))
        self.box_half_in = box
        self.rebuild()

    def _dormer_roof_lines(self):
        """DORMER_CONROLS.md: the two brown ROOF LINES -- where the dormer roof
        meets the host (the valleys). Returns `(solid, dashed)` segment lists.
        The full valley runs from the apex to the face corner (set by the pitch
        and the host); the EAVE (E = span + overhang) sets how far the roof
        actually CONTACTS the host -- SOLID from the apex down to where the
        eave meets the valley, DASHED beyond (where the roof line would be if
        the eaves, the walls or the ridge were changed). `[]` with no host."""
        host = self.host
        if host is None or sip.isdeleted(host):
            return [], []
        box = self.box_half_in
        key = (self.geometry_key(), host.geometry_key(),
               None if box is None else tuple(box), tuple(self.wall_span_in))
        memo = getattr(self, "_roofline_memo", None)
        if memo is not None and memo[0] == key:
            return memo[1]
        _, _, nx, ny = self._axis()
        p1, p2 = self.p1, self.p2
        span = self._span_in
        wall = self.wall_span_in                        # control C: the walls
        solid, dashed = [], []
        for side in (0, 1):
            if span[side] <= _CLIP_EPS_IN:
                continue
            sign = 1.0 if side == 0 else -1.0
            pitch = (self.ridge_h_in - self.eaves_h_in) / span[side]
            if pitch <= _CLIP_EPS_IN:
                continue
            dv = self._valley_perp(host, sign, pitch)
            if dv is None or dv <= _CLIP_EPS_IN:
                continue
            # control B clips the line's OUTER end: it is drawn out to the frame
            # half-width, never past the valley
            qmax = dv if box is None else min(dv, box[side])
            # SOLID down to where the roof line crosses the wall (where the
            # cheek wall is truncated), DASHED below -- the projected valley
            qe = min(wall[side], qmax)
            # the valley runs from the apex (perp 0) to the corner (perp dv);
            # the point at perp q is that fraction of the way out
            cx = p1.x() + sign * nx * dv - p2.x()
            cy = p1.y() + sign * ny * dv - p2.y()
            if qe > _CLIP_EPS_IN:
                te = qe / dv
                solid.append((QPointF(p2),
                              QPointF(p2.x() + cx * te, p2.y() + cy * te)))
            if qmax > qe + _CLIP_EPS_IN:
                te, tm = qe / dv, qmax / dv
                dashed.append((QPointF(p2.x() + cx * te, p2.y() + cy * te),
                               QPointF(p2.x() + cx * tm, p2.y() + cy * tm)))
        out = (solid, dashed)
        self._roofline_memo = (key, out)
        return out

    def _dormer_eave_lines(self):
        """DORMER_CONROLS.md controls E and F: the dormer's eave outline as
        `(green_sides, orange_face)`. Each side eave (E) is the green line at
        `wall + overhang` from the face eave corner up to where it meets the
        host (the roof line). The face eave (F) is the orange line across the
        front, down-slope of the face by `end_overhang_in[0]`, joining the two
        green corners -- so the three meet at the corners."""
        host = self.host
        if host is None or sip.isdeleted(host):
            return [], []
        ux, uy, nx, ny = self._axis()
        p1, p2 = self.p1, self.p2
        eo = self.end_overhang_in[0]
        face = QPointF(p1.x() - ux * eo, p1.y() - uy * eo)   # the face eave line
        box = self.box_half_in
        green, corner = [], {}
        for side in (0, 1):
            sign = 1.0 if side == 0 else -1.0
            e = self._eave_reach(side)
            corner[side] = QPointF(face.x() + sign * nx * e, face.y() + sign * ny * e)
            dv = self._face_valley_perp(side)
            if dv is None or dv <= _CLIP_EPS_IN:
                green.append((corner[side],
                              QPointF(p1.x() + sign * nx * e, p1.y() + sign * ny * e)))
                continue
            qmax = dv if box is None else min(dv, box[side])
            qe = min(e, qmax)
            vx = p1.x() + sign * nx * dv - p2.x()
            vy = p1.y() + sign * ny * dv - p2.y()
            t = qe / dv
            green.append((corner[side], QPointF(p2.x() + vx * t, p2.y() + vy * t)))
        orange = [(corner[0], corner[1])] if 0 in corner and 1 in corner else []
        return green, orange

    def shape(self) -> QPainterPath:
        if not _roof_hittable(self):
            # "shown, not editable": empty, not just disabled -- a manual
            # scan (RoomItem._outranked_at, the ridge tool's own marker
            # pre-check) must miss this ridge exactly as setEnabled(False)
            # already makes Qt's own automatic dispatch miss it. boundingRect
            # is untouched, so paint() keeps drawing at full extent. R6.c:
            # the same for a roof of a level that is not being edited.
            return QPainterPath()
        stroker = QPainterPathStroker()
        stroker.setWidth(8.0)
        if self.is_clipped():
            # R4d: what paints is what hits (D85's lesson carried) -- the
            # part beyond the seam is neither drawn nor clickable, and the
            # seam itself is. Same clipped segments paint() draws.
            path = QPainterPath()
            for p, q in self._drawn_lines() + list(self._seams):
                path.moveTo(p)
                path.lineTo(q)
            return stroker.createStroke(path)
        return stroker.createStroke(self._path)

    def _plan_lines(self):
        """Every plan line paint() draws, as `(kind, p, q)`: the dashed
        eave/end/hip lines and the heavy ridge -- one list, so the clipped
        and unclipped paths and the hit shape all agree. While clipped, a
        JOINED end (R4d: `_clip_ext` > 0 there) draws its eaves on into
        the extension and no end line at all -- the end is inside the
        other roof, not open (roofclip.py's module docstring)."""
        e1a, e1b, e2a, e2b = self._eave_ends()
        ext0, ext1 = self._clip_ext if self.is_clipped() else (0.0, 0.0)
        joined0, joined1 = ext0 > 1e-6, ext1 > 1e-6
        if joined0 or joined1:
            ux, uy, _, _ = self._axis()
            e1a = QPointF(e1a.x() - ux * ext0, e1a.y() - uy * ext0)
            e2a = QPointF(e2a.x() - ux * ext0, e2a.y() - uy * ext0)
            e1b = QPointF(e1b.x() + ux * ext1, e1b.y() + uy * ext1)
            e2b = QPointF(e2b.x() + ux * ext1, e2b.y() + uy * ext1)
        # the end-0 line is a dormer's FACE eave, end-1 its back; kinds kept
        # specific so paint() can colour a dormer's eaves (green sides, orange
        # face) while every other roof draws them all as one brown dash.
        lines = [("eave", e1a, e1b), ("eave", e2a, e2b)]
        if not joined0:
            lines.append(("end0", e1a, e2a))
            if not self.gable[0]:
                lines += [("hip", self.p1, e1a), ("hip", self.p1, e2a)]
        if not joined1:
            lines.append(("end1", e1b, e2b))
            if not self.gable[1]:
                lines += [("hip", self.p2, e1b), ("hip", self.p2, e2b)]
        lines.append(("ridge", self.p1, self.p2))
        return lines

    def _drawn_lines(self):
        """The plan lines clipped to the visible region (R4d), as `(p, q)`
        segments; every line when not clipped."""
        out = []
        for _, p, q in self._plan_lines():
            if self.is_clipped():
                out.extend(self._clipped(p, q))
            else:
                out.append((p, q))
        return out

    def _painted_plan_lines(self, clipped: bool):
        """`[(kind, [(p, q), ...])]`: the plan lines as painted -- cut to the
        visible region while clipped. 0279: computed once per change of the
        roof's geometry, its region and its join extension, not on every
        paint (a clipped roof re-cut its lines on each one, ~4 ms a roof,
        the bulk of what a room drag's frames still spent on roofs)."""
        key = (self.geometry_key(), clipped, self._clip_region if clipped else None,
               tuple(self._clip_ext))
        memo = getattr(self, "_lines_memo", None)
        if memo is not None and memo[0][0] == key[0] and memo[0][1] == key[1]                 and memo[0][2] is key[2] and memo[0][3] == key[3]:
            return memo[1]
        out = [(kind, self._clipped(p, q) if clipped else [(p, q)])
               for kind, p, q in self._plan_lines()]
        self._lines_memo = (key, out)
        return out

    def _clipped(self, p, q):
        """`p`-`q` clipped to the visible region, as QPointF pairs."""
        return [(QPointF(a.x(), a.y()), QPointF(b.x(), b.y()))
                for a, b in self._clip_region.clip_segment(p, q)]

    def geometry_key(self):
        """Everything of this roof's own that its clip trace and a wall's
        roof-clip dashes read: the ridge, the spans and overhangs, the two
        heights, the form, the ends and their hip runs, the floor. Plain
        values, compared by value (0276)."""
        runs = self.hip_run_in or (None, None)
        return (self.p1.x(), self.p1.y(), self.p2.x(), self.p2.y(),
                tuple(self.span_in), tuple(self.overhang_in),
                tuple(self.end_overhang_in),
                float(self.eaves_h_in), float(self.ridge_h_in), self.form,
                tuple(self.gable), tuple(runs), self.floor)

    def clip_trace(self):
        """`roof_clip_trace(scene, self)`, computed ONCE per change of what
        it reads (0276; 0275-report.md measured it at 27 ms a roof, run
        from every paint of every roof, 214 of a repaint's 246 ms): this
        roof's geometry, whether it is clipped and its join extension, and
        its floor's rooms and walls (`floor_rooms_key`). R5a's own worry --
        "rooms change without the roof hearing about it" -- is answered by
        the key, not by recomputing: the roof need not hear, it compares."""
        sc = self.scene()
        if sc is None or sip.isdeleted(self):
            return []
        own = (self.geometry_key(), self.is_clipped(), tuple(self._clip_ext))
        memo = self._trace_memo
        if memo is not None and rooms_held(sc) and memo[0][:3] == own:
            return list(memo[1])          # 0279: the rooms as at the press
        key = own + (floor_rooms_key(sc, self.floor),)
        if memo is None or memo[0] != key:
            # 0281: before computing, the scene's by-VALUE cache -- a reload
            # (an undo) makes new rooms and a new roof with the same
            # geometry, which the identity key cannot recognise
            vkey = own + (floor_rooms_value_key(sc, self.floor),)
            by_value = getattr(sc, "_trace_by_value", None)
            if by_value is None:
                by_value = sc._trace_by_value = {}
            segs = by_value.get(vkey)
            if segs is None:
                segs = roof_clip_trace(sc, self)
                if len(by_value) >= _TRACE_BY_VALUE_MAX:
                    by_value.clear()
                by_value[vkey] = [(QPointF(p), QPointF(q)) for p, q in segs]
            memo = self._trace_memo = (key, [(QPointF(p), QPointF(q)) for p, q in segs])
        return list(memo[1])

    def _drawn_trace(self):
        """R5a (0186-ruling.md sec2): the clip trace as drawn -- the
        roof's own locus (`clip_trace`), cut to the visible region while
        clipped, exactly as the plan lines are. Asked for at paint time and
        answered from the cache (0276): the trace is computed when what it
        reads changes, the cut when the region does."""
        segs = self.clip_trace()
        if not self.is_clipped():
            return segs
        key = (segs, self._clip_region)
        memo = self._drawn_memo
        if memo is not None and memo[0][1] is key[1] and memo[0][0] == segs:
            return list(memo[1])
        out = []
        for p, q in segs:
            out.extend(self._clipped(p, q))
        self._drawn_memo = (key, out)
        return list(out)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        ghost = floor_display_mode(self.floor) != "active"
        ink = FLOOR_GHOST if ghost else QColor(133, 77, 14)  # roof-brown
        clipped = self.is_clipped()
        # 0264: the roof's document id at its ridge's middle, in the callout
        # ink, while Show > Item callouts is on
        from floorplanner.annotations import callout_text, callouts_shown, draw_callout
        if not ghost and callouts_shown() and callout_text(self):
            # 0267: the one callout font, beside the ridge's middle
            lod = max(option.levelOfDetailFromTransform(painter.worldTransform()), 1e-6)
            m = QPointF((self.p1.x() + self.p2.x()) / 2.0, (self.p1.y() + self.p2.y()) / 2.0)
            draw_callout(painter, lod, QPointF(m.x() + 4.0 / lod, m.y() - 4.0 / lod), callout_text(self))
        if getattr(self, "_show_outline", False) and not ghost:
            # the marker menu's "Outline": the roof's full footprint (eave
            # rectangle, hips and overhang included), a bold violet border on
            # a translucent fill, drawn UNDER the roof's own lines so they
            # still read. On regardless of selection, until toggled off.
            out_ink = QColor(150, 40, 200)
            painter.setPen(QPen(out_ink, 2.0, Qt.PenStyle.SolidLine))
            painter.setBrush(QBrush(QColor(150, 40, 200, 40)))
            painter.drawPolygon(self.selection_outline())
            painter.setBrush(Qt.BrushStyle.NoBrush)
        # the dashed lines: both eaves, each end's own line (a gable line
        # across the ridge end, or -- for a hip end, R4b -- the END EAVE
        # beyond it plus the two hip lines down to its corners), then the
        # heavy ridge. R4d: while clipped, every line is drawn only where
        # it lies inside the visible region (exact segment clipping,
        # `roofclip.ClipRegion`), and the seam is drawn after, solid -- a
        # real edge, distinct from the dashed lines.
        dash = QPen(ink, 1.4, Qt.PenStyle.DashLine)
        heavy = QPen(ink, 3.0, Qt.PenStyle.SolidLine)
        heavy.setCapStyle(Qt.PenCapStyle.RoundCap)
        # a dormer's own lines read like the picture: its two side eaves
        # GREEN, its face eave ORANGE, both dashed; the ridge and slopes stay
        # brown; its three standing walls are added solid black below. Every
        # other roof (and any ghosted one) draws every line brown as before.
        dormer = self.is_dormer() and not ghost
        green = QPen(QColor(0, 150, 0), 1.6, Qt.PenStyle.DashLine)
        orange = QPen(QColor(230, 120, 20), 1.6, Qt.PenStyle.DashLine)
        for kind, segs in self._painted_plan_lines(clipped):
            if dormer and kind in ("eave", "end0", "end1"):
                continue                # a dormer's eaves are drawn explicitly
            pen = heavy if kind == "ridge" else dash
            painter.setPen(pen)
            for a, b in segs:
                painter.drawLine(a, b)
        if dormer:
            # control E (green side eaves, at wall + overhang) and control F
            # (the orange face eave, joining their front corners)
            green_e, orange_e = self._dormer_eave_lines()
            painter.setPen(green)
            for a, b in green_e:
                painter.drawLine(a, b)
            painter.setPen(orange)
            for a, b in orange_e:
                painter.drawLine(a, b)
            # the ROOF LINES (the valleys where the dormer roof meets the host):
            # SOLID brown where the roof contacts the host (out to the eave),
            # DASHED brown beyond -- where the line would be if the eaves, the
            # walls or the ridge changed. These stand in for a dormer's clip
            # seam, so the generic seam draw below is skipped for a dormer.
            solid_rl, dashed_rl = self._dormer_roof_lines()
            rl_solid = QPen(ink, 2.0, Qt.PenStyle.SolidLine)
            rl_solid.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(rl_solid)
            for a, b in solid_rl:
                painter.drawLine(a, b)
            painter.setPen(QPen(ink, 1.4, Qt.PenStyle.DashLine))
            for a, b in dashed_rl:
                painter.drawLine(a, b)
            # control C: the dormer's three outside walls (face + two cheeks),
            # drawn as FULL-THICKNESS BANDS in the exterior-wall format, not
            # thin lines -- Patrick, 2026-11: "the same size as the actual
            # outside walls on the plan view." Each segment becomes a rectangle
            # EXTERIOR_T wide, centred on the wall line, filled and outlined
            # exactly as walls.py draws an exterior wall.
            half = EXTERIOR_T / 2.0
            band = QPainterPath()
            for a, b in self._dormer_wall_lines():
                dx, dy = b.x() - a.x(), b.y() - a.y()
                ln = math.hypot(dx, dy)
                if ln < 1e-6:
                    continue
                ox, oy = -dy / ln * half, dx / ln * half
                band.addPolygon(QPolygonF([
                    QPointF(a.x() + ox, a.y() + oy), QPointF(b.x() + ox, b.y() + oy),
                    QPointF(b.x() - ox, b.y() - oy), QPointF(a.x() - ox, a.y() - oy)]))
            band.setFillRule(Qt.FillRule.WindingFill)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(60, 62, 68)))     # exterior-wall fill
            painter.drawPath(band)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(25, 25, 25), 0))      # exterior-wall edge
            painter.drawPath(band)
            # Phase C (0291): the dormer's OWN face windows as a READ-ONLY
            # SHADOW on the face band -- a projection of `self.openings`,
            # editable only in the dormer's End-On dialog. A ghosted blue so it
            # reads as "a window here, not yours to drag"; the floor's own
            # storey windows (wall openings) are untouched and stay normal.
            spans = self.dormer_face_window_spans()
            if spans:
                glass = QColor(37, 99, 235)                  # read-only blue
                fill = QColor(glass)
                fill.setAlpha(55)
                for a, b in spans:
                    dx, dy = b.x() - a.x(), b.y() - a.y()
                    ln = math.hypot(dx, dy)
                    if ln < 1e-6:
                        continue
                    ox, oy = -dy / ln * half, dx / ln * half
                    poly = QPolygonF([
                        QPointF(a.x() + ox, a.y() + oy), QPointF(b.x() + ox, b.y() + oy),
                        QPointF(b.x() - ox, b.y() - oy), QPointF(a.x() - ox, a.y() - oy)])
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(fill))
                    painter.drawPolygon(poly)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.setPen(QPen(glass, 0, Qt.PenStyle.DashLine))
                    painter.drawPolygon(poly)
                    painter.drawLine(a, b)                   # the glazing line
        if clipped and not dormer:
            seam_pen = QPen(ink, 2.0, Qt.PenStyle.SolidLine)   # a real edge
            seam_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(seam_pen)
            for p, q in self._seams:
                painter.drawLine(p, q)
        # R5a (0186-ruling.md sec2): the clip trace -- where this roof's
        # surface crosses the covered rooms' ceiling plane. The SAME ink
        # as R3b's wall dashes (walls.py), because it is the same fact:
        # each wall dash ends where its wall crosses this line. Ghosted
        # with the rest of a non-active floor, like the wall dash.
        trace = self._drawn_trace()
        if trace:
            trace_ink = FLOOR_GHOST if ghost else ROOF_CLIP_INK
            painter.setPen(QPen(trace_ink, 1.6, Qt.PenStyle.DashLine))
            for p, q in trace:
                painter.drawLine(p, q)
        if self.isSelected():
            # Patrick's own check of R4b: the selection must hug the roof
            # -- the eave rectangle, oriented with the ridge -- not the
            # axis-aligned bounding box, which on a 45deg wing is a big
            # square with the roof drawn diagonally across it.
            painter.setPen(QPen(QColor(0, 120, 215), 1.0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolygon(self.selection_outline())

    def _view(self):
        sc = self.scene()
        return sc.views()[0] if sc and sc.views() else None

    def open_end_on_dialog(self):
        """The dialog's SECOND door (0140-ruling.md sec1: "selecting any
        ridge still reaches the same dialog ... one dialog, two doors") --
        the marker's own right-click is the first. R4b: the same dialog is
        now the parameters dialog (0154-ruling.md sec3), still one dialog."""
        from floorplanner.dialogs import RoofEndOnDialog  # late: cycle guard
        dlg = RoofEndOnDialog(self, self._view())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dlg.apply()
            v = self._view()
            if v is not None and dlg.binding is not None:
                v.win.status(dlg.binding.status_line())

    def contextMenuEvent(self, e):
        menu = QMenu()
        if self.is_dormer():
            a_heights = menu.addAction("Edit dormer…")
            a_del = menu.addAction("Delete dormer")
        else:
            a_heights = menu.addAction("Roof parameters…")
            a_del = menu.addAction("Delete roof")
        a_outline = menu.addAction(
            "Hide outline" if getattr(self, "_show_outline", False) else "Show outline")
        chosen = menu.exec(e.screenPos())
        if chosen is a_heights:
            self.open_end_on_dialog()
        elif chosen is a_del:
            self.remove_with_dormers()
        elif chosen is a_outline:
            self.toggle_outline()
        e.accept()


MIN_RIDGE_LEN_IN = 12.0     # a gable-end drag cannot shorten the ridge past this
GRIP_END_OFFSET_IN = 18.0   # an end grip sits this far OUTSIDE its end line (clear of the marker at 1:1)


class RoofGripItem(QGraphicsItem):
    """One of a selected roof's five grips (R4c, 0154-ruling.md sec3): the
    two eave edges, the two gable ends, the ridge. A Qt CHILD of its
    `RoofItem`, like the marker, sitting at the midpoint of the line it
    drags; hidden unless the roof is selected (`RoofItem.itemChange`).
    Dragging calls the roof's own `drag_eave` / `drag_end` / `drag_ridge`
    on every move, so the plan follows the cursor live and the undo step
    is the settled gesture (the app's own debounced snapshot), as for
    every other drag. Hit region view-scaled, same as the marker."""

    KINDS = ("eave_l", "eave_r", "end_0", "end_1", "ridge")
    # the six Build-Dormer controls -- shown only on a selected DORMER, beside
    # the five universal grips above (the two side walls, the two side eaves,
    # the gable-face setback, the face eave)
    DORMER_KINDS = ("wall_l", "wall_r", "soffit_l", "soffit_r",
                    "setback", "face_eave", "apex", "box_top",
                    "box_l", "box_r")
    SIZE = 5.0               # drawn half-size, scene inches
    HIT_PX = 12.0            # clickable half-size, view pixels
    _TIPS = {
        "eave_l": "Eave edge -- drag to change this side's span",
        "eave_r": "Eave edge -- drag to change this side's span",
        "end_0": "Roof end -- drag along the ridge to lengthen or shorten",
        "end_1": "Roof end -- drag along the ridge to lengthen or shorten",
        "ridge": "Ridge -- drag sideways between the eaves",
        "wall_l": "Side wall -- drag to set this side's span",
        "wall_r": "Side wall -- drag to set this side's span",
        "soffit_l": "Side eave -- drag to set this side's overhang",
        "soffit_r": "Side eave -- drag to set this side's overhang",
        "setback": "Gable face -- drag along the roof to set the setback",
        "face_eave": "Face eave -- drag down-slope to set the front overhang",
        "apex": "Apex -- drag to move the ridge left/right; double-click to edit",
        "box_top": "Grow the dormer up or down the roof (keeps the pitch)",
        "box_l": "Frame edge -- drag in to clip this side's roof line",
        "box_r": "Frame edge -- drag in to clip this side's roof line",
    }
    # the dormer controls carry the picture's colours; everything else blue
    # DORMER_CONROLS.md: A apex white, C walls yellow, E eaves green, D face
    # purple, F face eave orange, B frame blue
    _COLORS = {
        "wall_l": QColor(201, 149, 0), "wall_r": QColor(201, 149, 0),  # C walls
        "soffit_l": QColor(0, 150, 0), "soffit_r": QColor(0, 150, 0),  # E eaves
        "setback": QColor(147, 51, 234),                              # D face
        "face_eave": QColor(230, 120, 20),                            # F front eave
        "box_top": QColor(0, 120, 215),                               # B frame
        "box_l": QColor(0, 120, 215), "box_r": QColor(0, 120, 215),   # B frame
    }

    def __init__(self, roof, kind: str):
        super().__init__(roof)
        self.roof = roof
        self.kind = kind
        # above the roof, BELOW the marker: on a gable end the end line
        # runs through the ridge endpoint the marker may sit at, and the
        # marker (the End-On dialog's first door) keeps its click
        self.setZValue(WALL_Z + 1.5)
        self.setVisible(False)
        self._dragging = False
        self.setToolTip(self._TIPS[kind])
        self.sync_position()

    def sync_position(self):
        self.prepareGeometryChange()
        if self.kind in RoofGripItem.DORMER_KINDS:
            self.setPos(self._dormer_pos())
            return
        e1a, e1b, e2a, e2b = self.roof._eave_ends()
        a, b = {
            "eave_l": (e1a, e1b), "eave_r": (e2a, e2b),
            "end_0": (e1a, e2a), "end_1": (e1b, e2b),
            "ridge": (self.roof.p1, self.roof.p2),
        }[self.kind]
        mx, my = (a.x() + b.x()) / 2.0, (a.y() + b.y()) / 2.0
        if self.kind in ("end_0", "end_1"):
            # just outside the end line, along the axis, so a gable end's
            # grip does not sit on top of the ridge endpoint (and marker)
            ux, uy, _, _ = self.roof._axis()
            sign = -1.0 if self.kind == "end_0" else 1.0
            mx += ux * GRIP_END_OFFSET_IN * sign
            my += uy * GRIP_END_OFFSET_IN * sign
        self.setPos(QPointF(mx, my))

    def _dormer_pos(self) -> QPointF:
        """The six dormer controls' positions: the two side walls on the span
        line (0.45 along the ridge), the two side eaves on the soffit line
        (0.68 along, so they clear the walls), the setback handle inside the
        face, and the face eave on its own eave line down-slope of the face."""
        r = self.roof
        ux, uy, nx, ny = r._axis()
        p1, p2 = r.p1, r.p2
        span, eo = r.span_in, r.end_overhang_in
        wall = r.wall_span_in                          # control C: the walls

        def along(f):
            return (p1.x() + (p2.x() - p1.x()) * f, p1.y() + (p2.y() - p1.y()) * f)

        if self.kind in ("wall_l", "wall_r"):          # C: on the black cheek wall
            s = 0 if self.kind == "wall_l" else 1
            sign = 1.0 if s == 0 else -1.0
            base = QPointF(p1.x() + sign * nx * wall[s], p1.y() + sign * ny * wall[s])
            for a, b in r._dormer_wall_lines()[1:]:    # skip the face wall
                if abs(a.x() - base.x()) < 1e-6 and abs(a.y() - base.y()) < 1e-6:
                    return QPointF((a.x() + b.x()) / 2.0, (a.y() + b.y()) / 2.0)
            return base
        if self.kind == "soffit_l":                    # E: the eave, beyond the wall
            ax, ay = along(0.68)
            e0 = r._eave_reach(0)
            return QPointF(ax + nx * e0, ay + ny * e0)
        if self.kind == "soffit_r":
            ax, ay = along(0.68)
            e1 = r._eave_reach(1)
            return QPointF(ax - nx * e1, ay - ny * e1)
        if self.kind == "setback":                     # D: on the face wall, at p1
            return QPointF(p1)
        if self.kind == "apex":                        # A: the apex (back end)
            return QPointF(p2)
        if self.kind == "box_top":
            # B top: beyond the apex, at the same ALONG offset as the end-1
            # grip (so `drag_box_top` can reuse `drag_end(1)`'s math), shifted
            # to the side so it does not sit on that grip
            return QPointF(p2.x() + ux * GRIP_END_OFFSET_IN + nx * GRIP_END_OFFSET_IN,
                           p2.y() + uy * GRIP_END_OFFSET_IN + ny * GRIP_END_OFFSET_IN)
        if self.kind in ("box_l", "box_r"):
            # B left/right: on the frame edge, at the mid-ridge, out at the box
            # half-width (the valley when the frame is not clipped in)
            s = 0 if self.kind == "box_l" else 1
            box = r.box_half_in
            edge = (box[s] if box is not None else r._face_valley_perp(s)) or span[s]
            sign = 1.0 if s == 0 else -1.0
            ax, ay = along(0.5)
            return QPointF(ax + sign * nx * edge, ay + sign * ny * edge)
        # face_eave: on the face eave line, down-slope of the face by eo[0]
        return QPointF(p1.x() - ux * eo[0], p1.y() - uy * eo[0])

    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def _hit_half(self) -> float:
        return max(self.SIZE, self.HIT_PX / self._view_scale())

    def boundingRect(self) -> QRectF:
        # 0279: the ridge grip's diamond (1.4 x SIZE) plus its pen
        r = max(self._hit_half(), self.SIZE * 1.4) + 3.0
        return QRectF(-r, -r, 2.0 * r, 2.0 * r)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        if not _roof_hittable(self.roof) or not self.isVisible():
            return path            # same "shown, not editable" reasoning
        h = self._hit_half()
        path.addRect(QRectF(-h, -h, 2.0 * h, 2.0 * h))
        return path

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        s = self.SIZE
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(self._COLORS.get(self.kind, QColor(0, 120, 215)), 1.5))
        if self.kind == "apex":                    # A: a white filled circle
            r = s * 1.5
            painter.drawEllipse(QRectF(-r, -r, 2.0 * r, 2.0 * r))
        elif self.kind == "ridge":
            d = s * 1.4
            painter.drawPolygon(QPolygonF([QPointF(0, -d), QPointF(d, 0),
                                           QPointF(0, d), QPointF(-d, 0)]))
        else:
            painter.drawRect(QRectF(-s, -s, 2.0 * s, 2.0 * s))

    def apply_drag(self, scene_pt: QPointF):
        if self.kind == "eave_l":
            self.roof.drag_eave(0, scene_pt)
        elif self.kind == "eave_r":
            self.roof.drag_eave(1, scene_pt)
        elif self.kind == "end_0":
            self.roof.drag_end(0, scene_pt)
        elif self.kind == "end_1":
            self.roof.drag_end(1, scene_pt)
        elif self.kind == "wall_l":
            self.roof.drag_wall(0, scene_pt)
        elif self.kind == "wall_r":
            self.roof.drag_wall(1, scene_pt)
        elif self.kind == "soffit_l":
            self.roof.drag_soffit(0, scene_pt)
        elif self.kind == "soffit_r":
            self.roof.drag_soffit(1, scene_pt)
        elif self.kind == "setback":
            self.roof.drag_setback(scene_pt)
        elif self.kind == "face_eave":
            self.roof.drag_face_eave(scene_pt)
        elif self.kind == "box_top":
            self.roof.drag_box_top(scene_pt)
        elif self.kind == "box_l":
            self.roof.drag_box_side(0, scene_pt)
        elif self.kind == "box_r":
            self.roof.drag_box_side(1, scene_pt)
        elif self.kind in ("ridge", "apex"):       # A and G both move the ridge
            self.roof.drag_ridge(scene_pt)
        else:
            self.roof.drag_ridge(scene_pt)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            hold_roof_clips(self.scene(), True)      # R6.b: compose at release
            e.accept()
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._dragging:
            self.apply_drag(e.scenePos())
            e.accept()
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._dragging and e.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.apply_drag(e.scenePos())
            hold_roof_clips(self.scene(), False)     # ...once, here
            e.accept()
        else:
            super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        # DORMER_CONROLS.md control A: double-click the apex opens the dormer's
        # parameters dialog (where the pitch lives)
        if self.kind == "apex" and e.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            hold_roof_clips(self.scene(), False)     # a press started a hold
            self.roof.open_end_on_dialog()
            e.accept()
        else:
            super().mouseDoubleClickEvent(e)


class RoofEndMarkerItem(QGraphicsItem):
    """One marker per roof, snapping to either ridge end (0140-ruling.md
    sec1); a Qt CHILD of its `RoofItem` (parent sits at (0,0), so the
    marker's local position IS the scene position, same convention the
    parent itself uses).

    Plain click/drag moves it between the two ridge ends -- release snaps
    to whichever end is nearer, never a free position (§1: "which end
    persists in the roof object", a binary choice, not a coordinate).
    Right-click OR double-click opens the End-On dialog -- the first of
    its "two doors"; `RoofItem.contextMenuEvent` is the second. (A plain
    double-click with no override still reaches `mousePressEvent` twice,
    per Qt's own default -- giving it real behaviour instead of leaving
    that second press ambiguous is what closes off a wall underneath ever
    mistaking it for the start of a new ridge; see `_hit_radius`.)

    THE HIT REGION IS VIEW-SCALED, not a fixed scene-space radius -- same
    convention `FurnishingItem`'s rotator handle already uses
    (`_view_scale`/`HANDLE_PX`, items.py), for the same reason: a small
    handle sized in plan inches shrinks to a few PIXELS at any zoom out
    past a room or two, and a click or the second half of a double-click
    that misses by a couple of pixels used to fall through to the
    ridge-sketch tool's own press handler -- which, if it then landed on
    a wall, could misread as an eaves pick for an accidentally-started
    zero-length ridge, corrupting `span_in` toward zero and reading back
    as a near-90deg pitch. Caught from Patrick's own report, not a test."""

    RADIUS = 6.0             # the drawn glyph, in scene inches
    HIT_PX = 14.0             # the CLICKABLE radius, in view pixels

    def __init__(self, roof: RoofItem):
        super().__init__(roof)
        self.roof = roof
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(WALL_Z + 2)        # above the ridge it marks
        self.setToolTip("Roof end marker -- drag to the other ridge end, "
                        "double-click for heights, right-click to edit, "
                        "delete or outline")
        self._dragging = False
        self.sync_position()

    def sync_position(self):
        self.prepareGeometryChange()
        # a DORMER's marker sits at its APEX (p2 -- where the ridge meets the
        # host), the point that names the dormer; marker_end stays 0 (its face
        # is still p1 for the standing rule and openings)
        if self.roof.is_dormer():
            self.setPos(self.roof.p2)
        else:
            self.setPos(self.roof.p2 if self.roof.marker_end else self.roof.p1)

    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def _hit_radius(self) -> float:
        return max(self.RADIUS, self.HIT_PX / self._view_scale())

    def boundingRect(self) -> QRectF:
        r = self._hit_radius() + 2.0
        return QRectF(-r, -r, 2.0 * r, 2.0 * r)

    def shape(self) -> QPainterPath:
        if not _roof_hittable(self.roof):
            return QPainterPath()   # same "shown, not editable" reasoning
        path = QPainterPath()
        path.addEllipse(QPointF(0.0, 0.0), self._hit_radius(), self._hit_radius())
        return path

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        ghost = floor_display_mode(self.roof.floor) != "active"
        fill = FLOOR_GHOST if ghost else QColor(0, 120, 215)
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(QColor(255, 255, 255), 1.5))
        painter.drawEllipse(QPointF(0.0, 0.0), self.RADIUS, self.RADIUS)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            e.accept()
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._dragging:
            self.setPos(e.scenePos())
            e.accept()
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._dragging and e.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            d1 = QLineF(e.scenePos(), self.roof.p1).length()
            d2 = QLineF(e.scenePos(), self.roof.p2).length()
            self.roof.marker_end = 0 if d1 <= d2 else 1
            self.sync_position()
            e.accept()
        else:
            super().mouseReleaseEvent(e)

    def contextMenuEvent(self, e):
        # the blue dot's own menu (Patrick, 2026-11): edit, delete, and an
        # "outline" that highlights the footprint this roof governs -- so a
        # dot in a crowded plan can be read. The roof body carries the same
        # menu (`RoofItem.contextMenuEvent`); double-click still opens the
        # dialog straight.
        roof = self.roof
        menu = QMenu()
        if roof.is_dormer():
            a_edit = menu.addAction("Edit dormer…")
            a_del = menu.addAction("Delete dormer")
        else:
            a_edit = menu.addAction("Roof parameters…")
            a_del = menu.addAction("Delete roof")
        a_outline = menu.addAction(
            "Hide outline" if getattr(roof, "_show_outline", False) else "Show outline")
        chosen = menu.exec(e.screenPos())
        if chosen is a_edit:
            roof.open_end_on_dialog()
        elif chosen is a_del:
            roof.remove_with_dormers()
        elif chosen is a_outline:
            roof.toggle_outline()
        e.accept()

    def mouseDoubleClickEvent(self, e):
        # Qt's own default (unless overridden) re-delivers a double-click
        # as a second mousePressEvent -- defined here as "open the
        # dialog" instead, so it is never ambiguous with a drag.
        self._dragging = False
        if e.button() == Qt.MouseButton.LeftButton:
            self.roof.open_end_on_dialog()
        e.accept()
