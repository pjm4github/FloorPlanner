"""Roof-family graphics items: RoofItem, plus the ridge-sketch tool's own
eaves-reference geometry.

0139-ruling.md's roofline plan, R1's `Roof` document record
(`floorplanner/design/model.py`); this module is R2's first UI writer.
Sits above walls (it finds an eaves wall to size its plan footprint), same
layer as rooms.py -- both load after walls, before items."""
import math

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
    ridge `p1`-`p2` and sits nearest to it -- the automatic half of the
    eaves pick. `RoofItem.span_in` is NOT part of the persisted `Roof`
    record (0139-ruling.md sec2 names no width field), so a roof loaded
    from a document re-derives its eaves reference this way instead of
    trusting a stored value that could go stale against the plan's own
    walls. Returns `(wall_or_None, span_in)`; `span_in` falls back to
    `DEFAULT_HALF_SPAN_IN` when nothing on the floor qualifies."""
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
    reach = rf.span_in + rf.overhang_in
    ridge_h, eaves_h = rf.ridge_h_in, rf.eaves_h_in
    slope = ((ridge_h - eaves_h) / rf.span_in) if rf.span_in > _CLIP_EPS_IN else 0.0
    margin = ridge_h - ceiling_in         # > 0: ridge itself clears the ceiling

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

    add_root(0.0 - a0, a1)                 # along(s) == 0
    add_root(ridge_len - a0, a1)           # along(s) == ridge_len
    add_root(reach - b0, b1)               # perp(s) == +reach
    add_root(-reach - b0, b1)              # perp(s) == -reach
    if slope > _CLIP_SLOPE_EPS:
        perp_thresh = margin / slope
        add_root(perp_thresh - b0, b1)     # perp(s) == +perp_thresh
        add_root(-perp_thresh - b0, b1)    # perp(s) == -perp_thresh

    roots = sorted(set(roots))
    spans = []
    for s_lo, s_hi in zip(roots, roots[1:], strict=False):
        if s_hi - s_lo < _CLIP_EPS_IN:
            continue
        s_mid = (s_lo + s_hi) / 2.0
        along_m, perp_m = a0 + a1 * s_mid, b0 + b1 * s_mid
        if not (-_CLIP_EPS_IN <= along_m <= ridge_len + _CLIP_EPS_IN
                and abs(perp_m) <= reach + _CLIP_EPS_IN):
            continue                       # not under this roof at all here
        if slope > _CLIP_SLOPE_EPS:
            clipped = (ridge_h - slope * abs(perp_m)) < ceiling_in - _CLIP_EPS_IN
        else:                              # degenerate/flat roof: uniform verdict
            clipped = margin < -_CLIP_EPS_IN
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


class RoofItem(QGraphicsItem):
    """A gable roof's ridge, drawn in plan: ridge heavy, eaves and gable
    ends dashed -- 0139-ruling.md R2's own 2D overlay convention.

    Local coords == scene coords (pos stays 0,0), same convention as
    `WallItem`; `p1`/`p2` are the ridge endpoints, plain `QPointF`s rather
    than shared `Vertex`s (0139-ruling.md sec2's model stores the ridge as
    two literal points, not a wall-network corner -- a roof does not need
    welding). `span_in` is a live-scene render affordance, not a document
    field: see `nearest_eaves_wall`'s docstring.

    v1 simplification, named rather than silently assumed: the eaves reach
    is symmetric about the ridge (mirrors 0140-ruling.md sec2's own
    symmetric-eaves-height assumption), and a `gable` end draws as a
    straight gable line unconditionally in R2 -- there is no UI yet to set
    it to a hip end (that is R4)."""

    def __init__(self, p1, p2, eaves_h_in=96.0, ridge_h_in=132.0,
                overhang_in=0.0, gable=None, span_in=DEFAULT_HALF_SPAN_IN,
                marker_end=1):
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
        self.overhang_in = float(overhang_in)
        self.gable = list(gable) if gable is not None else [True, True]
        self.span_in = float(span_in)
        self.marker_end = 1 if marker_end else 0   # R2b: which ridge end
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(WALL_Z + 1)        # reads above walls, like a callout
        self._bounds = QRectF()
        self._path = QPainterPath()
        self.marker = RoofEndMarkerItem(self)
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

    def _eave_ends(self):
        """(eave1_a, eave1_b, eave2_a, eave2_b): the two eave-line endpoints
        on each side, offset perpendicular to the ridge by span + overhang."""
        dx, dy = self.p2.x() - self.p1.x(), self.p2.y() - self.p1.y()
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        reach = self.span_in + self.overhang_in
        return (QPointF(self.p1.x() + nx * reach, self.p1.y() + ny * reach),
               QPointF(self.p2.x() + nx * reach, self.p2.y() + ny * reach),
               QPointF(self.p1.x() - nx * reach, self.p1.y() - ny * reach),
               QPointF(self.p2.x() - nx * reach, self.p2.y() - ny * reach))

    def rebuild(self):
        self.prepareGeometryChange()
        e1a, e1b, e2a, e2b = self._eave_ends()
        pad = 4.0
        xs = [self.p1.x(), self.p2.x(), e1a.x(), e1b.x(), e2a.x(), e2b.x()]
        ys = [self.p1.y(), self.p2.y(), e1a.y(), e1b.y(), e2a.y(), e2b.y()]
        self._bounds = QRectF(min(xs) - pad, min(ys) - pad,
                              max(xs) - min(xs) + 2 * pad,
                              max(ys) - min(ys) + 2 * pad)
        path = QPainterPath()
        path.moveTo(self.p1)
        path.lineTo(self.p2)
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
        if self.gable[0]:
            painter.drawLine(e1a, e2a)
        if self.gable[1]:
            painter.drawLine(e1b, e2b)
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
        the marker's own right-click is the first."""
        from floorplanner.dialogs import RoofEndOnDialog  # late: cycle guard
        dlg = RoofEndOnDialog(self, self._view())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dlg.apply()

    def contextMenuEvent(self, e):
        menu = QMenu()
        a_heights = menu.addAction("Roof heights…")
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
