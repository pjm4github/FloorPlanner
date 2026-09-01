"""Roof-family graphics items: RoofItem, plus the ridge-sketch tool's own
eaves-reference geometry.

0139-ruling.md's roofline plan, R1's `Roof` document record
(`floorplanner/design/model.py`); this module is R2's first UI writer.
Sits above walls (it finds an eaves wall to size its plan footprint), same
layer as rooms.py -- both load after walls, before items."""
import math

from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import QGraphicsItem

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
                overhang_in=0.0, gable=None, span_in=DEFAULT_HALF_SPAN_IN):
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
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(WALL_Z + 1)        # reads above walls, like a callout
        self._bounds = QRectF()
        self._path = QPainterPath()
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
