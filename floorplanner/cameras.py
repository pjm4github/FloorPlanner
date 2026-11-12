"""Plan cameras (0313): a placeable VIEWPOINT the user drops on the plan, aims,
and opens an ELEVATION of the wall it faces.

A `CameraItem` is a small movable/selectable glyph with a field-of-view wedge and
an aim arrow; its `rotation()` IS the aim direction (degrees, 0 = +x, Qt scene
convention, y down). It carries a `.floor` like every other plan item, saves and
reloads with the design (`cameras` block, `design/bridge.py`), and offers its
actions on a right-click menu (the extensible home for future per-camera tools)
and a double-click (open the elevation).

`CameraItem.elevation()` is the one genuinely new piece: it ray-casts from the
camera along its aim to the nearest wall on its floor and projects that wall
straight-on, to scale, with its doors and windows located -- the data a
`_WallElevationCanvas` (dialogs.py) paints. This module is Qt-aware and sits a
layer above walls (it imports `WallItem`); nothing in walls/rooms imports it, so
there is no cycle. The elevation DIALOG is imported late (inside the handlers) to
dodge the UI import cycle, exactly as `RoofItem` does with `RoofEndOnDialog`."""
import math

from PyQt6 import sip
from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import *  # noqa: F401

from floorplanner.config import *  # noqa: F401
from floorplanner.geometry import *  # noqa: F401  (grid_snap lives here)
from floorplanner.walls import WallItem

DEFAULT_CAMERA_CEILING_IN = 96.0     # a standard storey ceiling, the elevation's
                                     # top when no room ceiling is found under it

# glyph sizes, in scene inches (they scale with zoom, like a furnishing)
_BODY_W = 22.0
_BODY_H = 15.0
_LENS_R = 5.0
_REACH = 60.0                         # the wedge / aim-arrow length
_FOV_DEG = 22.0                       # half-angle of the field-of-view wedge
_INK = QColor(37, 99, 235)            # camera blue
_FILL = QColor(37, 99, 235, 40)       # translucent wedge
# content badges (0315): drawn under the body when a switch is on, so the glyph
# shows what the elevation will carry. The same two inks mark the silhouettes in
# the elevation, so the badge and its content read as one.
_FURN_C = QColor(13, 118, 102)        # furnishings: teal
_CAB_C = QColor(166, 124, 64)         # cabinetry: wood tan
_BADGE_W = 13.0
_BADGE_H = 11.0
_BADGE_GAP = 3.0
_BADGE_TOP = _BODY_H / 2 + 3.0        # just below the camera body


def _ray_segment_t(ox, oy, dx, dy, ax, ay, bx, by):
    """Distance `t>0` along the ray (origin O, unit dir D) to where it crosses
    segment A->B, or None if it does not (parallel, behind, or off the segment).
    Standard 2D ray/segment solve (Gareth Rees): t along the ray, u along the
    segment; a hit needs t>0 and 0<=u<=1."""
    ex, ey = bx - ax, by - ay
    rxs = dx * ey - dy * ex
    if abs(rxs) < 1e-9:
        return None                   # parallel
    qx, qy = ax - ox, ay - oy
    t = (qx * ey - qy * ex) / rxs
    u = (qx * dy - qy * dx) / rxs
    if t > 1e-6 and -1e-9 <= u <= 1.0 + 1e-9:
        return t
    return None


class CameraItem(QGraphicsItem):
    """A viewpoint on the plan. Drag to move (snaps to 1"); when selected a round
    ROTATOR HANDLE floats above it -- drag to aim (Ctrl sticks to the snap step);
    right-click or the 90° steps also turn it. Double-click, or right-click ->
    "Open elevation…", opens the straight-on elevation of the wall it faces."""

    def __init__(self, pos: QPointF, rotation: float = 0.0, floor=None, name: str = "",
                 show_furnishings: bool = False, show_cabinetry: bool = False):
        super().__init__()
        self._uid = None                 # the session label, C<n>
        self.floor = floor if floor is not None else active_floor()
        self.name = name or ""
        self.doc_id = None
        # per-camera elevation content switches (0315): show the furnishings
        # and/or the cabinetry standing against the faced wall. The plan glyph
        # changes shape to show which are on.
        self.show_furnishings = bool(show_furnishings)
        self.show_cabinetry = bool(show_cabinetry)
        self._rotating = False
        self._rot_offset = 0.0
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(6)                # above walls/furnishings, a floating marker
        self.setPos(pos)
        self.setRotation(rotation)
        self.setToolTip("Camera — drag to move, the handle to aim; "
                        "double-click for its elevation")

    # -- identity -------------------------------------------------------------
    @property
    def uid(self) -> str:
        if getattr(self, "_uid", None) is None:
            from floorplanner import labels as _labels
            self._uid = _labels.mint("C")
        return self._uid

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            return grid_snap(value)
        return super().itemChange(change, value)

    # -- rotator handle (cloned from FurnishingItem) --------------------------
    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def _handle(self) -> tuple:
        s = self._view_scale()
        stem, r = 14.0 / s, 5.0 / s
        return QPointF(0.0, -_BODY_H / 2 - stem - r), r

    def _on_handle(self, item_pt: QPointF) -> bool:
        c, r = self._handle()
        return QLineF(item_pt, c).length() <= r * 1.8

    def _handle_visible(self) -> bool:
        return self.isSelected() and self.group() is None

    # -- content badges (glyph shape per active switch) -----------------------
    def _badges(self) -> list:
        """(rect, ink) for each active content switch, in a row below the body
        -- furnishings left, cabinetry right. Drives both paint and the bounds,
        so the glyph's silhouette grows as switches turn on."""
        items = []
        if self.show_furnishings:
            items.append(_FURN_C)
        if self.show_cabinetry:
            items.append(_CAB_C)
        if not items:
            return []
        total = len(items) * _BADGE_W + (len(items) - 1) * _BADGE_GAP
        x = -total / 2.0
        out = []
        for ink in items:
            out.append((QRectF(x, _BADGE_TOP, _BADGE_W, _BADGE_H), ink))
            x += _BADGE_W + _BADGE_GAP
        return out

    # -- geometry -------------------------------------------------------------
    def boundingRect(self) -> QRectF:
        half = _REACH * math.tan(math.radians(_FOV_DEG)) + 2.0
        rect = QRectF(-_BODY_W / 2 - 2.0, -max(half, _BODY_H / 2 + 2.0),
                      _REACH + _BODY_W, 2 * max(half, _BODY_H / 2 + 2.0))
        c, r = self._handle()
        rect.setTop(min(rect.top(), c.y() - r - 1.5))
        badges = self._badges()
        if badges:                               # badges are counter-rotated to
            total = len(badges) * _BADGE_W + (len(badges) - 1) * _BADGE_GAP
            rr = math.hypot(total / 2.0, _BADGE_TOP + _BADGE_H) + 2.0
            rect = rect.united(QRectF(-rr, -rr, 2 * rr, 2 * rr))  # upright at any aim
        return rect

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(QRectF(-_BODY_W / 2, -_BODY_H / 2, _BODY_W, _BODY_H))
        if self.isSelected():
            c, r = self._handle()
            path.addEllipse(c, r * 1.8, r * 1.8)
        return path

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        active = floor_display_mode(self.floor) == "active"
        ink = _INK if active else FLOOR_GHOST
        # the field-of-view wedge (+x is the aim)
        half = _REACH * math.tan(math.radians(_FOV_DEG))
        wedge = QPolygonF([QPointF(_BODY_W / 2 - 2, 0.0),
                           QPointF(_REACH, -half), QPointF(_REACH, half)])
        if active:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(_FILL))
            painter.drawPolygon(wedge)
        # the aim arrow along +x
        painter.setPen(QPen(ink, 0))
        painter.drawLine(QPointF(_BODY_W / 2, 0.0), QPointF(_REACH, 0.0))
        ah = 6.0
        painter.drawLine(QPointF(_REACH, 0.0), QPointF(_REACH - ah, -ah * 0.6))
        painter.drawLine(QPointF(_REACH, 0.0), QPointF(_REACH - ah, ah * 0.6))
        # the camera body + lens
        painter.setPen(QPen(ink, 0))
        painter.setBrush(QBrush(QColor(255, 255, 255) if active else QColor(240, 240, 240)))
        painter.drawRoundedRect(QRectF(-_BODY_W / 2, -_BODY_H / 2, _BODY_W, _BODY_H), 3, 3)
        painter.setBrush(QBrush(ink))
        painter.drawEllipse(QPointF(_BODY_W / 2 - _LENS_R, 0.0), _LENS_R, _LENS_R)
        # content badges -- the glyph grows a pictogram per active switch; drawn
        # counter-rotated so they sit upright just below the camera at ANY aim
        badges = self._badges()
        if badges:
            painter.save()
            painter.rotate(-self.rotation())
            for br, bink in badges:
                self._draw_badge(painter, br, bink if active else FLOOR_GHOST)
            painter.restore()
        # selection box + rotator handle
        if self._handle_visible():
            painter.setPen(QPen(_INK, 0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(-_BODY_W / 2 - 1, -_BODY_H / 2 - 1, _BODY_W + 2, _BODY_H + 2))
            c, hr = self._handle()
            painter.setPen(QPen(_INK, 0))
            painter.drawLine(QPointF(0.0, -_BODY_H / 2), QPointF(c.x(), c.y() + hr))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(c, hr, hr)
            painter.setBrush(QBrush(_INK))
            painter.drawEllipse(c, hr * 0.35, hr * 0.35)

    @staticmethod
    def _draw_badge(painter, r: QRectF, ink: QColor):
        """A tiny pictogram in `r`: an armchair for furnishings (teal), a base
        cabinet for cabinetry (wood). The fill is a wash of the ink so the badge
        reads as a filled shape at plan zoom."""
        wash = QColor(ink)
        wash.setAlpha(70)
        painter.setPen(QPen(ink, 0))
        painter.setBrush(QBrush(wash))
        if ink == _CAB_C:                        # base cabinet: box, counter, doors
            painter.drawRect(r)
            ctop = r.top() + r.height() * 0.22
            painter.drawLine(QPointF(r.left() - 0.5, ctop),
                             QPointF(r.right() + 0.5, ctop))   # overhanging counter
            midx = r.center().x()
            painter.drawLine(QPointF(midx, ctop), QPointF(midx, r.bottom()))  # door split
            hy = ctop + (r.bottom() - ctop) * 0.3
            painter.setBrush(QBrush(ink))
            for hx in (midx - r.width() * 0.16, midx + r.width() * 0.16):
                painter.drawEllipse(QPointF(hx, hy), 0.7, 0.7)  # handles
        else:                                    # armchair: body, back, two arms
            painter.drawRoundedRect(r, 2.0, 2.0)
            back = r.top() + r.height() * 0.42
            painter.drawLine(QPointF(r.left() + r.width() * 0.22, back),
                             QPointF(r.right() - r.width() * 0.22, back))   # seat line
            ax = r.width() * 0.2
            painter.drawLine(QPointF(r.left() + ax, back),
                             QPointF(r.left() + ax, r.bottom() - 1.0))      # left arm
            painter.drawLine(QPointF(r.right() - ax, back),
                             QPointF(r.right() - ax, r.bottom() - 1.0))     # right arm

    # -- rotation interaction (cloned from FurnishingItem) --------------------
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
                rot = round(rot / step) * step
            else:
                rot = round(rot)
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

    def mouseDoubleClickEvent(self, e):
        self.open_elevation()
        e.accept()

    def contextMenuEvent(self, e):
        menu = QMenu()
        a_elev = menu.addAction("Open elevation…")
        menu.addSeparator()
        # content switches -- checkable, each shows its set in the elevation and
        # changes the plan glyph so the camera shows what it will draw
        a_furn = menu.addAction("Show furnishings")
        a_furn.setCheckable(True)
        a_furn.setChecked(self.show_furnishings)
        a_cab = menu.addAction("Show cabinetry")
        a_cab.setCheckable(True)
        a_cab.setChecked(self.show_cabinetry)
        menu.addSeparator()
        a_cw = menu.addAction("Rotate 90° CW")
        a_ccw = menu.addAction("Rotate 90° CCW")
        menu.addSeparator()
        a_del = menu.addAction("Delete camera")
        chosen = menu.exec(e.screenPos())
        if chosen is a_elev:
            self.open_elevation()
        elif chosen is a_furn:
            self.set_show_furnishings(a_furn.isChecked())
        elif chosen is a_cab:
            self.set_show_cabinetry(a_cab.isChecked())
        elif chosen is a_cw:
            self.setRotation((self.rotation() + 90.0) % 360.0)
        elif chosen is a_ccw:
            self.setRotation((self.rotation() - 90.0) % 360.0)
        elif chosen is a_del:
            if self.scene() is not None:
                self.scene().removeItem(self)
        e.accept()

    def set_show_furnishings(self, on: bool):
        """Turn the furnishings content switch on/off -- redraws the glyph (whose
        shape shows the active modes) and marks the plan dirty (scene.changed)."""
        on = bool(on)
        if on != self.show_furnishings:
            self.prepareGeometryChange()
            self.show_furnishings = on
            self.update()

    def set_show_cabinetry(self, on: bool):
        on = bool(on)
        if on != self.show_cabinetry:
            self.prepareGeometryChange()
            self.show_cabinetry = on
            self.update()

    def open_elevation(self):
        """Open (or report) the elevation of the wall this camera faces. Late
        import of the dialog closes the UI cycle (the dialogs layer imports the
        scene layer, not the reverse)."""
        from floorplanner.dialogs import CameraElevationDialog
        view = self.scene().views()[0] if (self.scene() and self.scene().views()) else None
        dlg = CameraElevationDialog(self, view)
        dlg.show()
        dlg.raise_()
        return dlg

    # -- the elevation (the one new algorithm) --------------------------------
    def faced_wall(self):
        """The nearest WallItem on this camera's floor that its aim ray crosses,
        or None when it points at open space."""
        sc = self.scene()
        if sc is None:
            return None
        ang = math.radians(self.rotation())
        dx, dy = math.cos(ang), math.sin(ang)
        ox, oy = self.pos().x(), self.pos().y()
        best = None
        for it in sc.items():
            if not isinstance(it, WallItem) or sip.isdeleted(it):
                continue
            if it.floor != self.floor:
                continue
            a, b = it.p1, it.p2
            t = _ray_segment_t(ox, oy, dx, dy, a.x(), a.y(), b.x(), b.y())
            if t is not None and (best is None or t < best[0]):
                best = (t, it)
        return best[1] if best is not None else None

    def _room_at(self, p: QPointF):
        """The RoomItem on this camera's floor whose outline contains `p`, or
        None (the camera sits outside every room -- e.g. aimed at an exterior
        wall from the yard)."""
        from floorplanner.rooms import RoomItem
        sc = self.scene()
        if sc is None:
            return None
        for it in sc.items():
            if (isinstance(it, RoomItem) and not sip.isdeleted(it)
                    and getattr(it, "floor", None) == self.floor
                    and it.contains(it.mapFromScene(p))):
                return it
        return None

    @staticmethod
    def _ceiling_of(room) -> float:
        """A room's ceiling height, or the standard ceiling when it names none."""
        if room is not None:
            try:
                h = float(room.properties.get("ceiling_height_in", 0) or 0)
            except (TypeError, ValueError):
                h = 0.0
            if h > 0:
                return h
        return DEFAULT_CAMERA_CEILING_IN

    def _face_record(self, wall, dx, dy):
        """One wall drawn straight-on in the elevation: its label, type, width,
        and its openings located by `centre_in` (offset from the wall's middle,
        + toward the camera's RIGHT), each with `sill_in`/`head_in`/`w_in`/`h_in`.
        Doors and windows come back in SEPARATE lists."""
        from floorplanner.model import DEFAULT_SILL_IN
        a, b = wall.p1, wall.p2
        L = math.hypot(b.x() - a.x(), b.y() - a.y())
        if L < 1e-6:
            return None
        ux, uy = (b.x() - a.x()) / L, (b.y() - a.y()) / L
        rx, ry = -dy, dx                       # the camera's RIGHT (y-down scene)
        sign = 1.0 if (ux * rx + uy * ry) >= 0 else -1.0
        windows, doors = [], []
        for op in getattr(wall, "openings", []):
            if sip.isdeleted(op):
                continue
            kind = getattr(op, "kind", "window")
            h = float(getattr(op, "height", 0.0) or 0.0)
            w = float(getattr(op, "width", 0.0) or 0.0)
            if kind == "window":
                s = getattr(op, "sill_in", None)
                sill = float(s) if s is not None else DEFAULT_SILL_IN
            else:
                sill = 0.0
            centre_in = sign * (float(op.s) - L / 2.0)
            rec = {"centre_in": centre_in, "w_in": w, "h_in": h,
                   "sill_in": sill, "head_in": sill + h, "kind": kind}
            (windows if kind == "window" else doors).append(rec)
        windows.sort(key=lambda r: r["centre_in"])
        doors.sort(key=lambda r: r["centre_in"])
        return {"label": getattr(wall, "uid", "") or "Wall",
                "wall_type": getattr(wall, "wall_type", "interior"),
                "width_in": L, "windows": windows, "doors": doors}

    def elevation(self):
        """The elevation the camera sees, as a data dict for
        `_WallElevationCanvas`, or None when it faces no wall.

        When the camera sits in a ROOM, this is the whole wall PLANE it faces:
        every contiguous room-boundary wall that runs across the view and stands
        in front of the camera (e.g. the two coplanar segments of a far wall
        broken by a doorway), laid left->right as the camera sees them in
        `faces`, each with its own label and openings. The side walls that turn
        the corner toward the camera at the run's two ends come back as
        `left_return`/`right_return` (their labels), drawn as short return ticks.
        Outside any room it falls back to the single faced wall (one face, no
        returns), so a camera in the yard still reads an exterior wall."""
        wall = self.faced_wall()
        if wall is None:
            return None
        ang = math.radians(self.rotation())
        dx, dy = math.cos(ang), math.sin(ang)
        rx, ry = -dy, dx
        cx, cy = self.pos().x(), self.pos().y()

        def mid(a, b):
            return (0.5 * (a.x() + b.x()), 0.5 * (a.y() + b.y()))

        def edge_u(a, b):                       # projection of the midpoint onto R
            mx, my = mid(a, b)
            return (mx - cx) * rx + (my - cy) * ry

        def edge_depth(a, b):                   # how far in FRONT of the camera (+ = ahead)
            mx, my = mid(a, b)
            return (mx - cx) * dx + (my - cy) * dy

        def is_face(a, b):                      # runs across the view (a wall we look AT)
            L = math.hypot(b.x() - a.x(), b.y() - a.y())
            if L < 1e-6:
                return False
            ux, uy = (b.x() - a.x()) / L, (b.y() - a.y()) / L
            return abs(ux * rx + uy * ry) >= abs(ux * dx + uy * dy)

        room = self._room_at(self.pos())
        faces, left_ret, right_ret = [], None, None
        outline = list(getattr(room, "outline", []) or []) if room is not None else []
        idx = next((i for i, e in enumerate(outline) if e.wall is wall), None)

        if idx is None:                          # outside a room, or wall off-outline
            rec = self._face_record(wall, dx, dy)
            if rec is None:
                return None
            faces = [(edge_u(wall.p1, wall.p2), rec, wall)]
        else:
            n = len(outline)

            def pts(i):
                return outline[i].v.point(), outline[(i + 1) % n].v.point()

            picked = {}                          # i -> (u, record)
            stops = []                           # the two bounding (return) edges
            for step in (+1, -1):                # walk both ways from the faced edge
                i = idx
                while True:
                    a, b = pts(i)
                    if not is_face(a, b) or edge_depth(a, b) <= 1e-6:
                        stops.append(outline[i].wall)   # the turn / the near wall
                        break
                    if i not in picked and outline[i].wall is not None:
                        rec = self._face_record(outline[i].wall, dx, dy)
                        if rec is not None:
                            picked[i] = (edge_u(a, b), rec, outline[i].wall)
                    i = (i + step) % n
                    if i == idx:                 # full loop (degenerate) -- stop
                        break
            faces = list(picked.values())
            # the two bounding walls -> left/right by where each sits along the
            # view (its midpoint projected onto the camera's right axis).
            rets = [w for w in stops if w is not None]
            scored = sorted(((self._wall_u(w, rx, ry, cx, cy), w) for w in rets),
                            key=lambda t: t[0])

            def _ret(w):
                return {"label": getattr(w, "uid", "") or "Wall"}

            if len(scored) >= 2:
                left_ret, right_ret = _ret(scored[0][1]), _ret(scored[-1][1])
            elif len(scored) == 1:               # one return: side by its u sign
                if scored[0][0] <= 0:
                    left_ret = _ret(scored[0][1])
                else:
                    right_ret = _ret(scored[0][1])

        if not faces:
            return None
        faces.sort(key=lambda t: t[0])           # left -> right as the camera sees
        face_recs = [rec for _u, rec, _w in faces]
        # per-face run metadata (run origin + along-wall axis), to place the
        # furnishings / cabinetry that stand against each wall
        face_meta, x0 = [], 0.0
        for _u, rec, fw in faces:
            m = self._face_meta(fw, rx, ry, cx, cy, x0)
            if m is not None:
                face_meta.append(m)
            x0 += rec["width_in"]
        ceiling = self._ceiling_of(room)
        heads = [o["head_in"] for rec in face_recs for o in rec["windows"] + rec["doors"]]
        if heads:
            ceiling = max(ceiling, max(heads) + 6.0)     # never clip an opening
        furnishings = (self._items_against(face_meta)
                       if (self.show_furnishings or self.show_cabinetry) else [])
        return {"room_name": getattr(room, "name", "") or "",
                "height_in": ceiling,
                "floor_abs_in": float(floor_elevation(wall.floor)),
                "faces": face_recs, "furnishings": furnishings,
                "left_return": left_ret, "right_return": right_ret}

    def _wall_u(self, wall, rx, ry, cx, cy) -> float:
        """A wall's midpoint projected onto the camera's RIGHT axis -- used to
        decide which return is on the left and which on the right."""
        a, b = wall.p1, wall.p2
        mx, my = 0.5 * (a.x() + b.x()), 0.5 * (a.y() + b.y())
        return (mx - cx) * rx + (my - cy) * ry

    @staticmethod
    def _face_meta(wall, rx, ry, cx, cy, x0):
        """A faced wall's run mapping: the endpoint that sits at the LEFT of the
        drawing (smaller camera-right projection), the along-wall axis pointing
        toward the right, the wall normal, the wall length, and `x0` (the face's
        left edge in run inches). A scene point projected onto this wall maps to
        `x0 + (p - left)·axis`."""
        a, b = wall.p1, wall.p2
        ua = (a.x() - cx) * rx + (a.y() - cy) * ry
        ub = (b.x() - cx) * rx + (b.y() - cy) * ry
        left, right = (a, b) if ua <= ub else (b, a)
        L = math.hypot(right.x() - left.x(), right.y() - left.y())
        if L < 1e-6:
            return None
        ux, uy = (right.x() - left.x()) / L, (right.y() - left.y()) / L
        return {"lx": left.x(), "ly": left.y(), "ux": ux, "uy": uy,
                "nx": -uy, "ny": ux, "L": L, "x0": x0}

    def _items_against(self, face_meta, tol=12.0):
        """The furnishings / cabinetry standing against the faced walls, as
        elevation records. An item is placed on the face whose wall it is most
        flush against (its back within `tol` of the wall, on the camera's side),
        its footprint PROJECTED onto that wall for the run span and its
        `elevation_in`/`height_in` for the vertical. Each toggle admits its own
        set (casework = cabinetry; the rest = furnishings)."""
        from floorplanner.catalog import furnishing_spec
        from floorplanner.items import FurnishingItem
        sc = self.scene()
        if sc is None or not face_meta:
            return []
        px, py = self.pos().x(), self.pos().y()
        out = []
        for it in sc.items():
            if not isinstance(it, FurnishingItem) or sip.isdeleted(it):
                continue
            if getattr(it, "floor", None) != self.floor:
                continue
            spec = furnishing_spec(it.kind)
            if spec is None:
                continue
            casework = bool(spec.get("casework"))
            if (casework and not self.show_cabinetry) or \
               (not casework and not self.show_furnishings):
                continue
            h = float(spec.get("height_in", 0.0) or 0.0)
            if h <= 0.0:
                continue
            elev = float(spec.get("elevation_in", 0.0) or 0.0)
            icx, icy = it.pos().x(), it.pos().y()
            th = math.radians(it.rotation())
            ex, ey = math.cos(th), math.sin(th)      # item local x axis
            fx, fy = -math.sin(th), math.cos(th)     # item local y axis
            hw, hd = it.w / 2.0, it.d / 2.0
            best = None                              # (gap, run_x0, run_x1)
            for m in face_meta:
                relx, rely = icx - m["lx"], icy - m["ly"]
                t = relx * m["ux"] + rely * m["uy"]              # centre along wall
                dperp = relx * m["nx"] + rely * m["ny"]          # signed clearance
                half_al = abs(hw * (ex * m["ux"] + ey * m["uy"])) + \
                    abs(hd * (fx * m["ux"] + fy * m["uy"]))
                half_pp = abs(hw * (ex * m["nx"] + ey * m["ny"])) + \
                    abs(hd * (fx * m["nx"] + fy * m["ny"]))
                a0, a1 = t - half_al, t + half_al
                if a1 <= 0.0 or a0 >= m["L"]:                    # off the wall span
                    continue
                gap = abs(dperp) - half_pp
                if gap > tol:                                    # too far off the wall
                    continue
                cam_side = (px - m["lx"]) * m["nx"] + (py - m["ly"]) * m["ny"]
                if dperp * cam_side < 0 and abs(dperp) > half_pp:
                    continue                                     # behind the wall
                if best is None or gap < best[0]:
                    best = (gap, m["x0"] + max(0.0, a0), m["x0"] + min(m["L"], a1))
            if best is not None:
                out.append({"label": getattr(it, "uid", "") or it.name,
                            "name": it.name, "casework": casework,
                            "x0_in": best[1], "x1_in": best[2],
                            "sill_in": elev, "head_in": elev + h})
        out.sort(key=lambda r: r["x0_in"])
        return out

    # -- serialization --------------------------------------------------------
    def to_record(self, cid: str, level: str) -> dict:
        rec = {"id": cid, "level": level,
               "pos": [self.pos().x(), self.pos().y()],
               "rotation": float(self.rotation())}
        if self.name:
            rec["name"] = self.name
        if self.show_furnishings:
            rec["show_furnishings"] = True
        if self.show_cabinetry:
            rec["show_cabinetry"] = True
        return rec

    @classmethod
    def from_record(cls, rec: dict, floor: str):
        it = cls(QPointF(*rec["pos"]), float(rec.get("rotation", 0.0)),
                 floor=floor, name=rec.get("name", ""),
                 show_furnishings=bool(rec.get("show_furnishings", False)),
                 show_cabinetry=bool(rec.get("show_cabinetry", False)))
        it.doc_id = rec.get("id")
        return it
