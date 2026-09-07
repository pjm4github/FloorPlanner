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
    for it in scene.items():
        if not isinstance(it, RoofItem):
            continue
        mode = floor_display_mode(it.floor)
        it.setVisible(mode != "hidden" and show)
        it.setEnabled(mode == "active" and show and edit)
        if not edit:
            it.setSelected(False)


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
    roofs = [it for it in scene.items()
             if isinstance(it, RoofItem) and not sip.isdeleted(it)
             and it.floor == wall.floor]
    if not roofs:
        return []                          # cheap exit before the room scan
    ceiling_in = _wall_ceiling_in(scene, wall)
    spans = []
    for rf in roofs:
        spans.extend(_clip_spans_against_one_roof(wall, rf, ceiling_in))
    return _merge_spans(spans, wall.length())


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
                marker_end=1, eaves_bind="manual"):
        super().__init__()
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
        self._overhang_in = self._normalized_pair(overhang_in)
        self.gable = list(gable) if gable is not None else [True, True]
        self._span_in = self._normalized_pair(span_in)
        self.marker_end = 1 if marker_end else 0   # R2b: which ridge end
        self.eaves_bind = eaves_bind if eaves_bind in ("manual", "room_top") \
            else "manual"                            # R4a: schema slot only
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(WALL_Z + 1)        # reads above walls, like a callout
        self._bounds = QRectF()
        self._path = QPainterPath()
        self.marker = RoofEndMarkerItem(self)
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
    def span_in(self):
        return list(self._span_in)

    @span_in.setter
    def span_in(self, value):
        self._span_in = self._normalized_pair(value)

    @property
    def overhang_in(self):
        return list(self._overhang_in)

    @overhang_in.setter
    def overhang_in(self, value):
        self._overhang_in = self._normalized_pair(value)

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

    def hip_extension(self, end: int, gable=None, span=None):
        """`(run, overhang)` along the ridge axis, beyond ridge end `end`
        (0 = `p1`, 1 = `p2`), that a HIP end adds to the footprint:
        `(0, 0)` for a gable end. The run is the mean of the two side spans,
        the overhang the mean of the two side overhangs (class docstring).
        `gable`/`span` override the stored values -- the parameters dialog
        previews an edit before it is applied."""
        flags = self.gable if gable is None else gable
        spans = self._span_in if span is None else span
        if flags[end]:
            return 0.0, 0.0
        return ((spans[0] + spans[1]) / 2.0,
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
        e1, e2 = r1 + o1, r2 + o2
        return (QPointF(self.p1.x() - ux * e1, self.p1.y() - uy * e1),
                QPointF(self.p2.x() + ux * e2, self.p2.y() + uy * e2))

    def _eave_ends(self):
        """(eave1_a, eave1_b, eave2_a, eave2_b): the two eave-line endpoints
        on each side, offset perpendicular to the ridge by that SIDE's own
        span + overhang (R4a: per-side, no longer a single shared reach),
        and pushed past a hip end along the axis (R4b: `hip_extension`)."""
        _, _, nx, ny = self._axis()
        a1, a2 = self._extended_ridge()
        reach_l = self._span_in[0] + self._overhang_in[0]
        reach_r = self._span_in[1] + self._overhang_in[1]
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

    def boundingRect(self) -> QRectF:
        return self._bounds

    def shape(self) -> QPainterPath:
        if not _roofs_editable():
            # "shown, not editable": empty, not just disabled -- a manual
            # scan (RoomItem._outranked_at, the ridge tool's own marker
            # pre-check) must miss this ridge exactly as setEnabled(False)
            # already makes Qt's own automatic dispatch miss it. boundingRect
            # is untouched, so paint() keeps drawing at full extent.
            return QPainterPath()
        stroker = QPainterPathStroker()
        stroker.setWidth(8.0)
        return stroker.createStroke(self._path)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        ghost = floor_display_mode(self.floor) != "active"
        ink = FLOOR_GHOST if ghost else QColor(133, 77, 14)  # roof-brown
        e1a, e1b, e2a, e2b = self._eave_ends()
        painter.setPen(QPen(ink, 1.4, Qt.PenStyle.DashLine))
        painter.drawLine(e1a, e1b)
        painter.drawLine(e2a, e2b)
        # each end's own line: a gable line across the ridge end, or -- for
        # a hip end (R4b) -- the END EAVE beyond it plus the two hip lines
        # running from the ridge end down to that eave's corners
        painter.drawLine(e1a, e2a)
        painter.drawLine(e1b, e2b)
        if not self.gable[0]:
            painter.drawLine(self.p1, e1a)
            painter.drawLine(self.p1, e2a)
        if not self.gable[1]:
            painter.drawLine(self.p2, e1b)
            painter.drawLine(self.p2, e2b)
        heavy = QPen(ink, 3.0, Qt.PenStyle.SolidLine)
        heavy.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(heavy)
        painter.drawLine(self.p1, self.p2)
        if self.isSelected():
            painter.setPen(QPen(QColor(0, 120, 215), 1.0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self._bounds)

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
        a_heights = menu.addAction("Roof parameters…")
        a_del = menu.addAction("Delete roof")
        chosen = menu.exec(e.screenPos())
        if chosen is a_heights:
            self.open_end_on_dialog()
        elif chosen is a_del:
            if self.scene() is not None:
                self.scene().removeItem(self)
        e.accept()


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
                        "right-click (or double-click) for heights")
        self._dragging = False
        self.sync_position()

    def sync_position(self):
        self.prepareGeometryChange()
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
        if not _roofs_editable():
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
        self.roof.open_end_on_dialog()
        e.accept()

    def mouseDoubleClickEvent(self, e):
        # Qt's own default (unless overridden) re-delivers a double-click
        # as a second mousePressEvent -- defined here as "open the
        # dialog" instead, so it is never ambiguous with a drag.
        self._dragging = False
        if e.button() == Qt.MouseButton.LeftButton:
            self.roof.open_end_on_dialog()
        e.accept()
