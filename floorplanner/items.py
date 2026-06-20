"""Furnishing-family graphics items: FurnishingItem, StairItem, GroupItem,
ReferenceImageItem, plus make_furnishing and grouping helpers.

Sits above walls/rooms: imports the wall/room items and a few algorithms from
them at module level (both load first)."""
import math

from PyQt6 import sip
from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import *  # noqa: F401

from floorplanner.config import *  # noqa: F401
from floorplanner.geometry import *  # noqa: F401
from floorplanner.catalog import *  # noqa: F401
from floorplanner.walls import WallItem, rebuild_all_walls
from floorplanner.rooms import RoomItem, walls_cover_room

# Stairs — a dynamic "Framing" furnishing: step count from the room's ceiling
# height (standard ~7" risers); full or half flight to a landing.
STAIR_WIDTH = 36.0            # standard residential stair width
STAIR_TREAD = 10.5           # standard tread run
STAIR_RISER = 7.0            # target riser height (drives the step count)
DEFAULT_CEILING_IN = 96.0    # fallback when a stair is not inside a room


class FurnishingItem(QGraphicsItem):
    """A furniture / fixture symbol placed on the plan at true scale.

    The symbol comes from the bundled library (assets/furnishings); its
    SVG viewBox is in inches, so it is rendered 1:1 into a scene rect of
    the catalog's width_in x depth_in.  Drag to move (snaps to 1").
    When selected, a round ROTATOR HANDLE floats above the symbol: drag
    it to spin the item freely (Ctrl = stick to 15-degree increments).
    Right-clicking still offers 90-degree steps and delete.
    """

    def __init__(self, kind: str, pos: QPointF, rotation: float = 0.0):
        super().__init__()
        spec = furnishing_spec(kind) or {
            "name": kind, "width_in": 24.0, "depth_in": 24.0}
        self.kind = kind
        self.name = spec["name"]
        self.w = float(spec["width_in"])
        self.d = float(spec["depth_in"])
        self.price = float(spec.get("price", 0.0) or 0.0)
        self._rotating = False
        self._rot_offset = 0.0
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
                     True)
        self.setAcceptHoverEvents(True)
        self.setZValue(3)                 # under the room fill/label and walls
        self.setPos(pos)                  # pos = symbol centre
        self.setRotation(rotation)        # rotates about the centre
        tip = f"{self.name} — {fmt_in(self.w)} × {fmt_in(self.d)}"
        if self.price > 0:
            tip += f"  ·  ${self.price:,.0f}"
        self.setToolTip(tip)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            return grid_snap(value)
        return super().itemChange(change, value)

    # -- rotator handle -------------------------------------------------------
    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def _handle(self) -> tuple:
        """(centre, radius) of the rotator handle in ITEM coordinates;
        sized in view pixels so it stays grabbable at any zoom."""
        s = self._view_scale()
        stem, r = 14.0 / s, 5.0 / s
        return QPointF(0.0, -self.d / 2 - stem - r), r

    def _on_handle(self, item_pt: QPointF) -> bool:
        c, r = self._handle()
        return QLineF(item_pt, c).length() <= r * 1.8

    def _handle_visible(self) -> bool:
        """The individual selection box + rotator only show when the item
        is selected on its own; inside a group the group's outline and
        handle govern the whole set."""
        return self.isSelected() and self.group() is None

    def boundingRect(self) -> QRectF:
        rect = QRectF(-self.w / 2 - 1.5, -self.d / 2 - 1.5,
                      self.w + 3, self.d + 3)
        c, r = self._handle()
        rect.setTop(c.y() - r - 1.5)
        return rect

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(QRectF(-self.w / 2, -self.d / 2, self.w, self.d))
        if self.isSelected():
            c, r = self._handle()
            path.addEllipse(c, r * 1.8, r * 1.8)
        return path

    def paint(self, painter, option, widget=None):
        rect = QRectF(-self.w / 2, -self.d / 2, self.w, self.d)
        r = furnishing_renderer(self.kind)
        if r is not None:
            r.render(painter, rect)
        else:
            painter.setPen(QPen(QColor(55, 65, 81), 1.0))
            painter.setBrush(QBrush(QColor(248, 250, 252)))
            painter.drawRect(rect)
        if self._handle_visible():
            blue = QColor(0, 110, 255)
            painter.setPen(QPen(blue, 0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect.adjusted(-1, -1, 1, 1))
            # rotator handle: stem + circle + centre dot
            c, hr = self._handle()
            painter.setPen(QPen(blue, 0))
            painter.drawLine(QPointF(0.0, -self.d / 2),
                             QPointF(c.x(), c.y() + hr))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(c, hr, hr)
            painter.setBrush(QBrush(blue))
            painter.drawEllipse(c, hr * 0.35, hr * 0.35)

    def hoverMoveEvent(self, e):
        if self._handle_visible() and self._on_handle(e.pos()):
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.unsetCursor()
        super().hoverMoveEvent(e)

    def hoverLeaveEvent(self, e):
        self.unsetCursor()
        super().hoverLeaveEvent(e)

    def _mouse_angle(self, scene_pt: QPointF) -> float:
        """Angle (degrees) of the mouse around the symbol centre."""
        return math.degrees(math.atan2(scene_pt.y() - self.pos().y(),
                                       scene_pt.x() - self.pos().x()))

    def mousePressEvent(self, e):
        if (e.button() == Qt.MouseButton.LeftButton and self._handle_visible()
                and self._on_handle(e.pos())):
            self._rotating = True
            self._rot_offset = self.rotation() - self._mouse_angle(e.scenePos())
            e.accept()
            return
        self._rotating = False
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._rotating:
            rot = self._mouse_angle(e.scenePos()) + self._rot_offset
            if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
                step = max(SETTINGS["rotate_snap_deg"], 1.0)
                rot = round(rot / step) * step    # stick to snap steps
            else:
                rot = round(rot)                  # whole degrees
            self.setRotation(rot % 360.0)
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._rotating:
            self._rotating = False
            e.accept()
            return
        super().mouseReleaseEvent(e)

    def contextMenuEvent(self, e):
        menu = QMenu()
        a_cw = menu.addAction("Rotate 90° CW")
        a_ccw = menu.addAction("Rotate 90° CCW")
        menu.addSeparator()
        a_del = menu.addAction(f"Delete {self.name}")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        if chosen is a_cw:
            self.setRotation((self.rotation() + 90.0) % 360.0)
        elif chosen is a_ccw:
            self.setRotation((self.rotation() - 90.0) % 360.0)
        elif chosen is a_del:
            self.scene().removeItem(self)
        e.accept()

    def extra_state(self) -> dict:
        """Per-kind state to persist alongside kind/pos/rotation.  Plain
        furnishings have none; subclasses (e.g. StairItem) override this."""
        return {}


class StairItem(FurnishingItem):
    """A stair flight whose number of steps is computed from the ceiling
    height of the room it is placed in.  `flight` is 'full' or 'half';
    a half flight rises to a landing that either ends ('none') or turns
    'left'/'right' for the remaining rise.  `direction` ('up'/'down')
    flips the travel arrow."""

    def __init__(self, pos: QPointF, rotation: float = 0.0, *,
                 flight: str = "full", turn: str = "left",
                 direction: str = "up"):
        self.flight = flight if flight in ("full", "half") else "full"
        self.turn = turn if turn in ("none", "left", "right") else "left"
        self.direction = direction if direction in ("up", "down") else "up"
        self.n_risers = 14
        self._off = QPointF(0.0, 0.0)
        self._geo = {"rects": [], "steps": [], "arrow": [], "label": ""}
        super().__init__("stairs", pos, rotation)
        self._recompute()

    def extra_state(self) -> dict:
        return {"flight": self.flight, "turn": self.turn,
                "direction": self.direction}

    # -- geometry ------------------------------------------------------------
    def _ceiling_height(self) -> float:
        sc = self.scene()
        if sc is not None:
            pt = self.scenePos()
            for it in sc.items():
                if isinstance(it, RoomItem) and it.path.contains(pt):
                    return float(it.properties.get("ceiling_height_in",
                                                   DEFAULT_CEILING_IN))
        return DEFAULT_CEILING_IN

    def _build(self) -> dict:
        """Stair geometry in natural coords (first flight rising along +Y
        from the origin): rectangles, interior step lines, the travel-arrow
        polyline, and the floor-level label point."""
        w, t = STAIR_WIDTH, STAIR_TREAD
        treads = max(1, self.n_risers - 1)
        rects, steps = [], []
        if self.flight == "full":
            run = treads * t
            rects.append(QRectF(0, 0, w, run))
            for i in range(1, treads):
                steps.append((0, i * t, w, i * t))
            line = [QPointF(w / 2, t * 0.5), QPointF(w / 2, run - t * 0.5)]
            label_pt = QPointF(w / 2 + 1, t * 0.5)
        else:
            first = max(1, treads // 2)
            second = treads - first
            run1 = first * t
            land = w
            rects.append(QRectF(0, 0, w, run1))          # first flight
            for i in range(1, first):
                steps.append((0, i * t, w, i * t))
            rects.append(QRectF(0, run1, w, land))       # landing
            line = [QPointF(w / 2, t * 0.5),
                    QPointF(w / 2, run1 + land / 2)]
            label_pt = QPointF(w / 2 + 1, t * 0.5)
            if self.turn in ("left", "right") and second > 0:
                run2 = second * t
                if self.turn == "left":
                    rects.append(QRectF(-run2, run1, run2, w))
                    for j in range(1, second):
                        steps.append((-j * t, run1, -j * t, run1 + w))
                    line.append(QPointF(-run2 + t * 0.5, run1 + w / 2))
                else:
                    rects.append(QRectF(w, run1, run2, w))
                    for j in range(1, second):
                        steps.append((w + j * t, run1, w + j * t, run1 + w))
                    line.append(QPointF(w + run2 - t * 0.5, run1 + w / 2))
            else:
                line[-1] = QPointF(w / 2, run1 + land - t * 0.5)
        return {"rects": rects, "steps": steps, "line": line,
                "label_pt": label_pt}

    def _recompute(self):
        self.prepareGeometryChange()
        self.n_risers = max(2, round(self._ceiling_height() / STAIR_RISER))
        geo = self._build()
        bbox = QRectF(geo["rects"][0])
        for r in geo["rects"][1:]:
            bbox = bbox.united(r)
        self._geo = geo
        self._bbox = bbox
        self.w = bbox.width()
        self.d = bbox.height()
        self._off = QPointF(-bbox.center().x(), -bbox.center().y())
        rise_ft = self.n_risers * STAIR_RISER / FOOT
        kind = "full flight" if self.flight == "full" else \
            ("half flight, ends at landing" if self.turn == "none"
             else f"half flight, turns {self.turn}")
        self.setToolTip(f"Stairs — {self.n_risers} risers ({kind}), "
                        f"{self.direction.upper()}; rise ~{rise_ft:.1f} ft")
        self.update()

    def itemChange(self, change, value):
        res = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged:
            self._recompute()
        return res

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._recompute()             # the room under the stair may differ

    # -- painting ------------------------------------------------------------
    def paint(self, painter, option, widget=None):
        painter.save()
        painter.translate(self._off)
        ink = QColor(55, 65, 81)
        painter.setPen(QPen(ink, 1.2))
        painter.setBrush(QBrush(QColor(248, 250, 252)))
        for r in self._geo["rects"]:
            painter.drawRect(r)
        painter.setPen(QPen(ink, 0.7))
        for x1, y1, x2, y2 in self._geo["steps"]:
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        self._paint_arrow(painter, ink)
        painter.restore()
        if self._handle_visible():
            self._paint_selection(painter)

    def _paint_arrow(self, painter, ink):
        line = list(self._geo["line"])
        if self.direction == "down":
            line.reverse()
        painter.setPen(QPen(ink, 1.4))
        for a, b in zip(line[:-1], line[1:], strict=False):
            painter.drawLine(a, b)
        head, prev = line[-1], line[-2]
        ang = math.atan2(head.y() - prev.y(), head.x() - prev.x())
        for da in (math.radians(150), math.radians(-150)):
            painter.drawLine(head, QPointF(head.x() + 7 * math.cos(ang + da),
                                           head.y() + 7 * math.sin(ang + da)))
        font = painter.font()
        font.setPointSizeF(7.0)
        font.setBold(True)
        painter.setFont(font)
        lp = self._geo["label_pt"]
        painter.drawText(QRectF(lp.x(), lp.y() - 1, 24, 11),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                         "UP" if self.direction == "up" else "DN")

    def _paint_selection(self, painter):
        rect = QRectF(-self.w / 2, -self.d / 2, self.w, self.d)
        blue = QColor(0, 110, 255)
        painter.setPen(QPen(blue, 0, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(-1, -1, 1, 1))
        c, hr = self._handle()
        painter.setPen(QPen(blue, 0))
        painter.drawLine(QPointF(0.0, -self.d / 2), QPointF(c.x(), c.y() + hr))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(c, hr, hr)
        painter.setBrush(QBrush(blue))
        painter.drawEllipse(c, hr * 0.35, hr * 0.35)

    def contextMenuEvent(self, e):
        menu = QMenu()
        m_flight = menu.addMenu("Flight")
        for label, val in [("Full flight", "full"),
                           ("Half flight (landing)", "half")]:
            a = m_flight.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.flight == val)
            a.setData(("flight", val))
        m_turn = menu.addMenu("Half-flight direction")
        m_turn.setEnabled(self.flight == "half")
        for label, val in [("Turn left", "left"), ("Turn right", "right"),
                           ("End at landing", "none")]:
            a = m_turn.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.turn == val)
            a.setData(("turn", val))
        m_dir = menu.addMenu("Travel")
        for label, val in [("Going up", "up"), ("Going down", "down")]:
            a = m_dir.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.direction == val)
            a.setData(("direction", val))
        menu.addSeparator()
        a_cw = menu.addAction("Rotate 90° CW")
        a_ccw = menu.addAction("Rotate 90° CCW")
        menu.addSeparator()
        a_del = menu.addAction("Delete stairs")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if chosen is None:
            e.accept()
            return
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        data = chosen.data()
        if isinstance(data, tuple):
            setattr(self, data[0], data[1])
            self._recompute()
        elif chosen is a_cw:
            self.setRotation((self.rotation() + 90.0) % 360.0)
        elif chosen is a_ccw:
            self.setRotation((self.rotation() - 90.0) % 360.0)
        elif chosen is a_del and self.scene() is not None:
            self.scene().removeItem(self)
        e.accept()


def make_furnishing(kind: str, pos: QPointF, rotation: float = 0.0,
                    state: dict = None):
    """Create the right item for a catalog `kind`: a dynamic StairItem for
    'stairs', otherwise a plain FurnishingItem.  `state` carries per-kind
    extras (e.g. stair flight/turn/direction) from the plan/clipboard."""
    state = state or {}
    if kind == "stairs":
        return StairItem(pos, rotation,
                         flight=state.get("flight", "full"),
                         turn=state.get("turn", "left"),
                         direction=state.get("direction", "up"))
    return FurnishingItem(kind, pos, rotation)


class GroupItem(QGraphicsItemGroup):
    """A group of walls / furnishings that selects and moves as one
    (Ctrl+G to group, Ctrl+Shift+G to ungroup).

    After every drag the group's translation is BAKED back into its
    members — wall p1/p2 are scene coordinates, so they must be shifted
    for hit-testing, joining and room detection to keep working — and
    the group itself returns to (0, 0).
    """

    def __init__(self):
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
                     True)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        self._rotating = False
        self._angle = 0.0                 # current orientation of the box

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            return grid_snap(value)
        return super().itemChange(change, value)

    # -- rotator handle -------------------------------------------------------
    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    @staticmethod
    def _rot_transform(center: QPointF, angle: float) -> QTransform:
        tr = QTransform()
        tr.translate(center.x(), center.y())
        tr.rotate(angle)
        tr.translate(-center.x(), -center.y())
        return tr

    def _content_points(self) -> list:
        """Scene-coord extreme points of the members (wall endpoints and
        furnishing footprint corners) -- the box hugs these."""
        pts = []
        for ch in self.childItems():
            if isinstance(ch, WallItem):
                pts += [ch.p1, ch.p2]
            elif isinstance(ch, FurnishingItem):
                r = QRectF(-ch.w / 2, -ch.d / 2, ch.w, ch.d)
                pts += [ch.mapToScene(r.topLeft()), ch.mapToScene(r.topRight()),
                        ch.mapToScene(r.bottomRight()),
                        ch.mapToScene(r.bottomLeft())]
        return pts

    def _oriented_box(self) -> tuple:
        """(localRect, centre): an axis-aligned rectangle in the frame
        rotated by -self._angle that tightly contains the content.  Drawn
        back through +self._angle it becomes an oriented box hugging the
        members at the group's current orientation."""
        pts = self._content_points()
        if not pts:
            b = self.childrenBoundingRect()
            return b, b.center()
        cx = sum(p.x() for p in pts) / len(pts)
        cy = sum(p.y() for p in pts) / len(pts)
        center = QPointF(cx, cy)
        local = [self._rot_transform(center, -self._angle).map(p) for p in pts]
        xs = [p.x() for p in local]
        ys = [p.y() for p in local]
        m = EXTERIOR_T                    # margin for wall half-thickness
        rect = QRectF(min(xs) - m, min(ys) - m,
                      max(xs) - min(xs) + 2 * m, max(ys) - min(ys) + 2 * m)
        return rect, center

    def _handle(self) -> tuple:
        """(centre, radius) of the rotator handle in scene coords; floats
        above the oriented box and turns with it."""
        rect, center = self._oriented_box()
        s = self._view_scale()
        stem, r = 18.0 / s, 6.0 / s
        local_c = QPointF(rect.center().x(), rect.top() - stem - r)
        return self._rot_transform(center, self._angle).map(local_c), r

    def _on_handle(self, item_pt: QPointF) -> bool:
        c, r = self._handle()
        return QLineF(item_pt, c).length() <= r * 1.8

    def boundingRect(self) -> QRectF:
        rect, center = self._oriented_box()
        poly = self._rot_transform(center, self._angle).map(QPolygonF(rect))
        br = poly.boundingRect()
        c, r = self._handle()
        return br.united(
            QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r)).adjusted(-4, -4, 4, 4)

    def paint(self, painter, option, widget=None):
        sel = self.isSelected()
        rect, center = self._oriented_box()
        pen = QPen(QColor(0, 110, 255) if sel else QColor(165, 173, 185), 0,
                   Qt.PenStyle.DashLine)
        painter.save()
        painter.translate(center.x(), center.y())   # draw in the box's frame
        painter.rotate(self._angle)
        painter.translate(-center.x(), -center.y())
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(-2, -2, 2, 2))
        if sel:
            s = self._view_scale()
            stem, hr = 18.0 / s, 6.0 / s
            c = QPointF(rect.center().x(), rect.top() - stem - hr)
            blue = QColor(0, 110, 255)
            painter.setPen(QPen(blue, 0))
            painter.drawLine(QPointF(rect.center().x(), rect.top()),
                             QPointF(c.x(), c.y() + hr))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(c, hr, hr)
            painter.setBrush(QBrush(blue))
            painter.drawEllipse(c, hr * 0.35, hr * 0.35)
        painter.restore()

    def hoverMoveEvent(self, e):
        if self.isSelected() and self._on_handle(e.pos()):
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.unsetCursor()
        super().hoverMoveEvent(e)

    def hoverLeaveEvent(self, e):
        self.unsetCursor()
        super().hoverLeaveEvent(e)

    # -- rotation (baked live into the members about a fixed centre) ----------
    def _angle_to(self, scene_pt: QPointF) -> float:
        c = self._rot_center
        return math.degrees(math.atan2(scene_pt.y() - c.y(),
                                       scene_pt.x() - c.x()))

    def _begin_rotation(self, scene_pt: QPointF):
        self._rotating = True
        self._rot_center = self.childrenBoundingRect().center()
        self._rot_start = self._angle_to(scene_pt)
        self._rot_angle0 = self._angle
        self._snap_walls = [(w, QPointF(w.p1), QPointF(w.p2))
                            for w in self.childItems()
                            if isinstance(w, WallItem)]
        self._snap_furn = [(f, QPointF(f.pos()), f.rotation())
                           for f in self.childItems()
                           if isinstance(f, FurnishingItem)]
        group_walls = {w for w, _, _ in self._snap_walls}
        self._snap_rooms = []
        sc = self.scene()
        if sc is not None and group_walls:
            for it in sc.items():
                if isinstance(it, RoomItem) and walls_cover_room(group_walls, it):
                    self._snap_rooms.append(
                        (it, [QPointF(c) for c in (it.corners or [])],
                         QPointF(it.anchor), QPainterPath(it.path)))

    def _apply_rotation(self, scene_pt: QPointF, snap: bool):
        theta = self._angle_to(scene_pt) - self._rot_start
        if snap:
            step = max(SETTINGS["rotate_snap_deg"], 1.0)
            theta = round(theta / step) * step
        self._angle = (self._rot_angle0 + theta) % 360.0
        c = self._rot_center
        tr = QTransform()
        tr.translate(c.x(), c.y())
        tr.rotate(theta)
        tr.translate(-c.x(), -c.y())
        self.prepareGeometryChange()
        for w, p1_0, p2_0 in self._snap_walls:
            w.p1, w.p2 = tr.map(p1_0), tr.map(p2_0)
            w.rebuild()                       # re-syncs its openings too
        for f, pos_0, rot_0 in self._snap_furn:
            f.setPos(tr.map(pos_0))
            f.setRotation((rot_0 + theta) % 360.0)
        for room, corners_0, anchor_0, path_0 in self._snap_rooms:
            room.prepareGeometryChange()
            if corners_0:
                room.corners = [tr.map(p) for p in corners_0]
            room.anchor = tr.map(anchor_0)
            room.path = tr.map(path_0)
            room._sync_corner_props()
            room.update()
        self.update()

    def _finish_rotation(self):
        self._snap_walls = self._snap_furn = self._snap_rooms = []
        self.prepareGeometryChange()
        self.update()

    def adopt(self, item):
        """addToGroup without Qt's transform juggling.  The group always
        sits at (0,0) untransformed, so children can simply keep their
        own scene position and rotation.  (Qt's addToGroup bakes a
        rotated child's rotation into its transform(), which then
        combines with the still-set rotation() and double-rotates.)"""
        sp, rot = item.scenePos(), item.rotation()
        self.addToGroup(item)
        item.setTransform(QTransform())
        if isinstance(item, WallItem):
            item.setPos(0.0, 0.0)         # walls live in their p1/p2
        else:
            item.setPos(sp)
        item.setRotation(rot)

    def dissolve(self) -> list:
        """Remove the group, leaving its members in the scene exactly
        where they are now; returns the members."""
        children = list(self.childItems())
        sc = self.scene()
        for c in children:
            sp, rot = c.scenePos(), c.rotation()
            self.removeFromGroup(c)
            c.setTransform(QTransform())
            c.setPos(QPointF(0.0, 0.0) if isinstance(c, WallItem) else sp)
            c.setRotation(rot)
            # removeFromGroup() hands ownership back to Python; with no
            # external reference the wrapper (and its C++ item) would be
            # garbage-collected straight out of the scene.  Tie its
            # lifetime to the scene so it survives.
            if sc is not None:
                sip.transferto(c, sc)
        if sc is not None:
            sc.removeItem(self)
        return children

    def bake(self):
        """Fold the group's current translation into its members and
        reset the group to (0, 0).  A room whose perimeter is fully walled
        by the group rides along -- its anchor (label) and region shift too
        -- even when an extra coincident wall (e.g. a shared party wall the
        room edge was copied from) also touches its boundary."""
        d = self.pos()
        if abs(d.x()) < 1e-9 and abs(d.y()) < 1e-9:
            return
        sc = self.scene()
        moved_rooms = []
        group_walls = {ch for ch in self.childItems()
                       if isinstance(ch, WallItem)}
        if sc is not None and group_walls:
            for it in sc.items():
                if isinstance(it, RoomItem) and walls_cover_room(group_walls, it):
                    moved_rooms.append(it)
        self.prepareGeometryChange()
        for ch in self.childItems():
            if isinstance(ch, WallItem):
                ch.p1 = QPointF(ch.p1.x() + d.x(), ch.p1.y() + d.y())
                ch.p2 = QPointF(ch.p2.x() + d.x(), ch.p2.y() + d.y())
            else:
                ch.setPos(ch.pos().x() + d.x(), ch.pos().y() + d.y())
        tr = QTransform.fromTranslate(d.x(), d.y())
        for r in moved_rooms:
            r.prepareGeometryChange()
            r.anchor = QPointF(r.anchor.x() + d.x(), r.anchor.y() + d.y())
            # carry the region itself: a rigid translation of the walls
            # translates the room rigidly, so the fill/outline stay put
            # even before (and in case) re-detection runs
            r.path = tr.map(r.path)
            if r.corners:
                r.corners = [QPointF(c.x() + d.x(), c.y() + d.y())
                             for c in r.corners]
            r._sync_corner_props()
        self.setPos(0.0, 0.0)
        rebuild_all_walls(sc)             # re-detects rooms at new anchors

    def mousePressEvent(self, e):
        if (e.button() == Qt.MouseButton.LeftButton and self.isSelected()
                and self._on_handle(e.pos())):
            self._begin_rotation(e.scenePos())
            e.accept()
            return
        self._rotating = False
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._rotating:
            self._apply_rotation(
                e.scenePos(),
                bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier))
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._rotating:
            self._rotating = False
            self._finish_rotation()
            e.accept()
            return
        super().mouseReleaseEvent(e)
        self.bake()

    def contextMenuEvent(self, e):
        win = None
        sc = self.scene()
        if sc and sc.views():
            win = sc.views()[0].win
        menu = QMenu()
        a_un = menu.addAction("Ungroup")
        a_cut = menu.addAction("Cut group")
        a_copy = menu.addAction("Copy group")
        menu.addSeparator()
        a_del = menu.addAction("Delete group")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        if win is not None and chosen in (a_un, a_cut, a_del):
            sc.clearSelection()
            self.setSelected(True)
            # defer: these destroy this item, which must not happen
            # while Qt is still delivering its context-menu event
            slot = {a_un: win.ungroup_selected, a_cut: win.cut_selected,
                    a_del: win.delete_selected}[chosen]
            QTimer.singleShot(0, slot)
        elif chosen is a_copy and win is not None:
            sc.clearSelection()
            self.setSelected(True)
            win.copy_selected()
        e.accept()


def item_fully_inside(item, area: QRectF) -> bool:
    """True when `item` lies entirely within the scene rectangle `area`."""
    if isinstance(item, WallItem):
        return area.contains(item.p1) and area.contains(item.p2)
    if isinstance(item, RoomItem):
        if item.corners:
            return all(area.contains(c) for c in item.corners)
        return area.contains(item.path.boundingRect())
    if isinstance(item, FurnishingItem):
        foot = item.mapToScene(
            QRectF(-item.w / 2, -item.d / 2, item.w, item.d)).boundingRect()
        return area.contains(foot)
    if isinstance(item, GroupItem):
        return area.contains(item.sceneBoundingRect())
    return False


def group_room(group):
    """The room whose perimeter the group's walls fully enclose, or None --
    so a grouped (extracted) room can be picked up from its group."""
    sc = group.scene()
    gw = {c for c in group.childItems() if isinstance(c, WallItem)}
    if sc is None or not gw:
        return None
    for it in sc.items():
        if isinstance(it, RoomItem) and walls_cover_room(gw, it):
            return it
    return None


def trace_wall_loop(walls):
    """Ordered corner points of the single closed loop formed by `walls`
    (e.g. a grouped wall-loop with no RoomItem), or None if they don't form
    one simple loop."""
    if len(walls) < 3:
        return None

    def key(p):
        return (round(p.x() * 2) / 2.0, round(p.y() * 2) / 2.0)

    pts, adj = {}, {}
    for w in walls:
        a, b = key(w.p1), key(w.p2)
        if a == b:
            continue
        pts[a], pts[b] = w.p1, w.p2
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    if not adj or any(len(v) != 2 for v in adj.values()):
        return None
    start = next(iter(adj))
    loop, prev, cur = [start], None, start
    while True:
        nxt = next((n for n in adj[cur] if n != prev), None)
        if nxt is None or nxt == start:
            break
        loop.append(nxt)
        prev, cur = cur, nxt
        if len(loop) > len(adj):
            return None
    if len(loop) != len(adj):
        return None                # not one loop covering every node
    return [QPointF(pts[k]) for k in loop]


class ReferenceImageItem(QGraphicsItem):
    """A raster floor-plan image dropped on the canvas as a movable, scalable,
    croppable, translucent backdrop for tracing / wall extraction.  `ipp` is
    inches-per-image-pixel (the scale): drag the body to move, drag a corner
    to rescale, right-click to calibrate / crop / extract / remove."""

    Z = -100.0
    HANDLE_PX = 9.0           # corner handle half-size, in view pixels
    MIN_IPP = 0.05

    def __init__(self, image, ipp: float, threshold: int = 128, merge: int = 3):
        super().__init__()
        self._img = image                       # QImage (RGB/whatever)
        self._ipp = float(ipp)
        self.threshold = int(threshold)
        self.merge = int(merge)
        self.locked = False                     # lock: no move/scale/crop/remove
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
                     True)
        self.setZValue(self.Z)
        self._scaling = None                    # corner index while scaling

    def set_locked(self, locked: bool):
        """Lock/unlock the backdrop: locked images can't be moved, rescaled,
        cropped or removed (a small padlock badge shows the state)."""
        self.locked = bool(locked)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
                     not self.locked)
        self.update()

    # -- scale / geometry ----------------------------------------------------
    def inches_per_pixel(self) -> float:
        return self._ipp

    def set_inches_per_pixel(self, ipp: float):
        self.prepareGeometryChange()
        self._ipp = max(float(ipp), self.MIN_IPP)
        self.update()

    def _size_in(self):
        return (self._img.width() * self._ipp, self._img.height() * self._ipp)

    def _corner_local(self, i: int) -> QPointF:
        w, h = self._size_in()
        return [QPointF(0, 0), QPointF(w, 0), QPointF(w, h),
                QPointF(0, h)][i]

    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def _handle_in(self) -> float:
        return self.HANDLE_PX / self._view_scale()

    def boundingRect(self) -> QRectF:
        w, h = self._size_in()
        m = self._handle_in() + 1
        return QRectF(-m, -m, w + 2 * m, h + 2 * m)

    def paint(self, painter, option, widget=None):
        w, h = self._size_in()
        rect = QRectF(0, 0, w, h)
        painter.setOpacity(0.7)
        painter.drawImage(rect, self._img)
        painter.setOpacity(1.0)
        if self.locked:
            pen = QPen(QColor(202, 138, 4), 0)         # amber solid = locked
            pen.setStyle(Qt.PenStyle.SolidLine)
        else:
            pen = QPen(QColor(37, 99, 235), 0)
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)
        if self.isSelected() and not self.locked:      # no resize knobs when locked
            hs = self._handle_in()
            painter.setBrush(QColor(37, 99, 235))
            painter.setPen(Qt.PenStyle.NoPen)
            for i in range(4):
                c = self._corner_local(i)
                painter.drawRect(QRectF(c.x() - hs, c.y() - hs, 2 * hs, 2 * hs))
        if self.locked:
            self._paint_lock_badge(painter)

    def _paint_lock_badge(self, painter):
        """A small padlock at the top-left so the locked state is obvious."""
        s = 16.0 / self._view_scale()              # ~constant 16 px badge
        x, y = s * 0.4, s * 0.4
        painter.setPen(QPen(QColor(120, 80, 4), 0))
        painter.setBrush(QColor(250, 204, 21))      # body
        painter.drawRoundedRect(QRectF(x, y + s * 0.55, s, s * 0.75),
                                s * 0.16, s * 0.16)
        painter.setBrush(Qt.BrushStyle.NoBrush)     # shackle
        painter.setPen(QPen(QColor(120, 80, 4), max(0.8, s * 0.16)))
        painter.drawArc(QRectF(x + s * 0.2, y, s * 0.6, s * 0.9), 0, 180 * 16)

    # -- corner-drag scaling -------------------------------------------------
    def _corner_at(self, local_pt: QPointF):
        hs = self._handle_in() * 1.6
        for i in range(4):
            if (self._corner_local(i) - local_pt).manhattanLength() <= 2 * hs:
                return i
        return None

    def mousePressEvent(self, e):
        if not self.locked and e.button() == Qt.MouseButton.LeftButton:
            self._scaling = self._corner_at(e.pos())
            if self._scaling is not None:
                e.accept()
                return
        super().mousePressEvent(e)          # locked: select only (no move/scale)

    def mouseMoveEvent(self, e):
        if self._scaling is not None:
            opp = (self._scaling + 2) % 4
            anchor = self.mapToScene(self._corner_local(opp))   # stays fixed
            new_w = abs(e.scenePos().x() - anchor.x())
            self.set_inches_per_pixel(new_w / max(self._img.width(), 1))
            self.setPos(anchor - self._corner_local(opp))       # re-anchor
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._scaling is not None:
            self._scaling = None
            e.accept()
            return
        super().mouseReleaseEvent(e)

    # -- calibrate / crop / extract (testable model methods) -----------------
    def calibrate(self, scene_p1: QPointF, scene_p2: QPointF, real_in: float):
        """Set the scale so the two scene points are `real_in` inches apart."""
        a, b = self.mapFromScene(scene_p1), self.mapFromScene(scene_p2)
        d_px = QLineF(a, b).length() / max(self._ipp, 1e-9)     # image pixels
        if d_px > 1e-6 and real_in > 0:
            self.set_inches_per_pixel(real_in / d_px)

    def crop_to_scene_rect(self, scene_rect: QRectF) -> bool:
        w, h = self._size_in()
        local = self.mapRectFromScene(scene_rect).intersected(
            QRectF(0, 0, w, h))
        if local.width() < self._ipp or local.height() < self._ipp:
            return False
        px = QRect(round(local.x() / self._ipp), round(local.y() / self._ipp),
                   round(local.width() / self._ipp),
                   round(local.height() / self._ipp)).intersected(
                       self._img.rect())
        if px.width() < 1 or px.height() < 1:
            return False
        shift = QPointF(px.x() * self._ipp, px.y() * self._ipp)
        self.prepareGeometryChange()
        self._img = self._img.copy(px)
        self.setPos(self.pos() + shift)
        self.update()
        return True

    def wall_segments(self, min_wall_in: float = 12.0):
        """Detected walls as (x0, y0, x1, y1) scene-inch tuples at the current
        scale/position."""
        import fp_extract
        gray = fp_extract.gray_from_qimage(self._img)
        out = []
        for x0, y0, x1, y1 in fp_extract.detect_walls(
                gray, self.threshold, 24, self.merge, 40):
            a = self.mapToScene(QPointF(x0 * self._ipp, y0 * self._ipp))
            b = self.mapToScene(QPointF(x1 * self._ipp, y1 * self._ipp))
            a = grid_snap(a, SETTINGS["wall_snap_in"])
            b = grid_snap(b, SETTINGS["wall_snap_in"])
            if (a - b).manhattanLength() >= min_wall_in:
                out.append((a.x(), a.y(), b.x(), b.y()))
        return out

    def _view(self):
        sc = self.scene()
        return sc.views()[0] if sc and sc.views() else None

    def contextMenuEvent(self, e):
        menu = QMenu()
        a_lock = menu.addAction("Unlock image" if self.locked else "Lock image")
        menu.addSeparator()
        a_cal = menu.addAction("Calibrate scale (2 points)…")
        a_crop = menu.addAction("Crop to region")
        a_ext = menu.addAction("Extract walls")
        menu.addSeparator()
        a_rem = menu.addAction("Remove image")
        for a in (a_cal, a_crop, a_rem):     # locked: no scale/crop/delete
            a.setEnabled(not self.locked)
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        view = self._view()
        if chosen is a_lock:
            self.set_locked(not self.locked)
        elif chosen is a_cal and view is not None:
            view.start_image_calibrate(self)
        elif chosen is a_crop and view is not None:
            view.start_image_crop(self)
        elif chosen is a_ext and view is not None:
            view.win.extract_from_reference(self)
        elif chosen is a_rem and self.scene() is not None:
            self.scene().removeItem(self)
        e.accept()
