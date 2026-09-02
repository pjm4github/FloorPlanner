"""Roof-family graphics items: RoofItem, plus the ridge-sketch tool's own
eaves-reference geometry.

0139-ruling.md's roofline plan, R1's `Roof` document record
(`floorplanner/design/model.py`); this module is R2's first UI writer.
Sits above walls (it finds an eaves wall to size its plan footprint), same
layer as rooms.py -- both load after walls, before items."""
import math

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
