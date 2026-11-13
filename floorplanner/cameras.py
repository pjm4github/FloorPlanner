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

MAX_EAVE_PITCH = 3.0                 # slope (rise/run) past which a roof side is
                                     # a near-vertical cut, not a soffited eave --
                                     # 36:12 is already steeper than any real roof,
                                     # so a half-gable's near-zero stub side (slope
                                     # in the hundreds) draws no eave overhang


def _tri_normal(a, b, c):
    """The (unnormalised) normal of the triangle a-b-c, as a 3-tuple."""
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    return (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)

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
_HOUSE_C = QColor(96, 125, 160)       # whole house side: slate blue
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
                 show_furnishings: bool = False, show_cabinetry: bool = False,
                 show_house_side: bool = False):
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
        # 0317: outside a room, elevation the WHOLE SIDE of the house -- every
        # exterior wall whose outside turns toward the camera, not just the one
        # wall the aim ray hits. A no-op while the camera sits inside a room.
        self.show_house_side = bool(show_house_side)
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
        if self.show_house_side:
            items.append(_HOUSE_C)
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
        elif ink == _HOUSE_C:                    # house: a gabled silhouette + door
            eave = r.top() + r.height() * 0.42
            body = QRectF(r.left(), eave, r.width(), r.bottom() - eave)
            painter.drawRect(body)
            roof = QPolygonF([QPointF(r.left() - 0.5, eave),
                              QPointF(r.center().x(), r.top()),
                              QPointF(r.right() + 0.5, eave)])
            painter.drawPolygon(roof)
            dw = r.width() * 0.26
            painter.setBrush(QBrush(ink))
            painter.drawRect(QRectF(r.center().x() - dw / 2.0,
                                    body.bottom() - body.height() * 0.55,
                                    dw, body.height() * 0.55))      # a door
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
        a_house = menu.addAction("View whole house side")
        a_house.setCheckable(True)
        a_house.setChecked(self.show_house_side)
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
        elif chosen is a_house:
            self.set_show_house_side(a_house.isChecked())
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

    def set_show_house_side(self, on: bool):
        """0317: turn the whole-house-side switch on/off -- the glyph grows a
        house badge and an outside-a-room elevation widens to the full side."""
        on = bool(on)
        if on != self.show_house_side:
            self.prepareGeometryChange()
            self.show_house_side = on
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

    def _room_at(self, p: QPointF, floor=None):
        """The RoomItem on `floor` (the camera's own by default) whose outline
        contains `p`, or None (the point sits outside every room -- e.g. aimed at
        an exterior wall from the yard)."""
        from floorplanner.rooms import RoomItem
        sc = self.scene()
        if sc is None:
            return None
        floor = self.floor if floor is None else floor
        for it in sc.items():
            if (isinstance(it, RoomItem) and not sip.isdeleted(it)
                    and getattr(it, "floor", None) == floor
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

    def _house_elevation(self, dx, dy, rx, ry, cx, cy):
        """0318 (compositional rework, his plan 2026-11-12): the whole-house-side
        elevation built by COMPOSITING 2-D pieces, not by projecting the 3-D model.

        Every piece is a flat shape on one shared plane: the horizontal axis U is
        the camera-right projection `u = (x-cx)*rx + (y-cy)*ry`; the vertical axis
        Z is the absolute world height in inches (`floor_elevation(floor)` + height
        above that floor). Exterior walls are vertical rectangles, so a whole wall
        is uniformly in front of or behind another along any shared column --
        hidden-surface removal is just PAINTER'S ORDER by wall depth (far first,
        near over it), no z-buffer.

        The pieces, each a flat polygon with a depth (painted FAR -> NEAR):
          * exterior walls at their true U-span, their tops clipped to the
            roofline above (rake where a wall sits under a gable, flat at the
            eave), or to the next storey where one stacks on them;
          * each gable/shed roof's camera-facing slopes and gable ends, from the
            roof's own geometry (`_axis`/`_extended_ridge`/`_eave_ends`);
          * dormers ride through the same roof projection, their face windows
            (`RoofItem.gable_elevation`) drawn frontmost.
        Windows and doors sit on the SAME camera-right axis as the linework, so
        they land on the walls. Replaces the first rework's 3-D `build_model`
        hidden-LINE projection (`house_3d`), which was slow and fragile.

        Returns the composite dict (`mode` "house_elev") -- `pieces`,
        `dormer_windows`, `faces` (for the caption) and `extent` -- or None when
        nothing faces the camera (the caller then falls back to a single wall)."""
        sc = self.scene()
        if sc is None:
            return None
        from floorplanner.model import DEFAULT_SILL_IN

        # his tweak 2026-11-12: a PURE FRONT-ON projection. Snap the horizontal
        # axis to the dominant exterior-wall direction (the facade) nearest the
        # camera's aim, so facade walls and roof eave/ridge lines come out exactly
        # horizontal -- a camera a couple of degrees off square otherwise skews
        # them (his "the main-roof gable end is a little sloped"). Depth stays
        # perpendicular to that axis (rx = -dy, ry = dx kept).
        fx, fy, best = rx, ry, -1.0
        for it in sc.items():
            if (not isinstance(it, WallItem) or sip.isdeleted(it)
                    or getattr(it, "wall_type", "") != "exterior"):
                continue
            a, b = it.p1, it.p2
            L = math.hypot(b.x() - a.x(), b.y() - a.y())
            if L < 1e-6:
                continue
            ux, uy = (b.x() - a.x()) / L, (b.y() - a.y()) / L
            wgt = abs(ux * rx + uy * ry) * L               # longest, most parallel
            if wgt > best:
                best, fx, fy = wgt, ux, uy
        if fx * rx + fy * ry < 0.0:                        # orient to camera-right
            fx, fy = -fx, -fy
        rx, ry, dx, dy = fx, fy, fy, -fx

        def pt_u(x, y):                                    # camera-right coordinate
            return (x - cx) * rx + (y - cy) * ry

        def pt_depth(x, y):                                # distance in FRONT (+ ahead)
            return (x - cx) * dx + (y - cy) * dy

        def is_face(a, b):                                 # runs across the view
            L = math.hypot(b.x() - a.x(), b.y() - a.y())
            if L < 1e-6:
                return False
            ux, uy = (b.x() - a.x()) / L, (b.y() - a.y()) / L
            return abs(ux * rx + uy * ry) >= abs(ux * dx + uy * dy)

        from floorplanner.roofs import RoofItem, _roof_datum_floor

        # the camera-facing exterior/dormer walls that SEPARATE the camera-side
        # outdoors from an interior room: the front side of the house. (Drops the
        # far side -- its camera-facing surface is indoors -- and the returns,
        # which run along the view.) Each keeps its WallItem (to resample for the
        # roof clip) and its `_face_record` (the caption's `faces`).
        front = []
        for it in sc.items():
            if (not isinstance(it, WallItem) or sip.isdeleted(it)
                    or getattr(it, "wall_type", "") not in ("exterior", "dormer")):
                continue
            a, b = it.p1, it.p2
            L = math.hypot(b.x() - a.x(), b.y() - a.y())
            if L < 1e-6 or not is_face(a, b):
                continue
            mx, my = 0.5 * (a.x() + b.x()), 0.5 * (a.y() + b.y())
            if pt_depth(mx, my) <= 1e-6:                   # behind the camera
                continue
            nx, ny = -(b.y() - a.y()) / L, (b.x() - a.x()) / L
            if nx * (cx - mx) + ny * (cy - my) < 0:
                nx, ny = -nx, -ny
            eps = 4.0
            op = QPointF(mx + nx * eps, my + ny * eps)
            ip = QPointF(mx - nx * eps, my - ny * eps)
            if not (self._room_at(op, it.floor) is None
                    and self._room_at(ip, it.floor) is not None):
                continue
            rec = self._face_record(it, dx, dy)
            if rec is not None:
                front.append((it, rec))
        if not front:
            return None

        roofs = [it for it in sc.items()
                 if isinstance(it, RoofItem) and not sip.isdeleted(it)]
        main_roofs = [r for r in roofs if not r.is_dormer()]  # these clip the walls
        ext_walls = [it for it in sc.items() if isinstance(it, WallItem)
                     and not sip.isdeleted(it)
                     and getattr(it, "wall_type", "") in ("exterior", "dormer")]

        def higher_base_over(mx, my, base):
            """The lowest base of an exterior wall on a HIGHER storey overlapping
            (within 20in of) this footprint -- the storey stacked on this wall,
            which caps it flat instead of the roofline. inf when none."""
            best = math.inf
            for v in ext_walls:
                vb = float(floor_elevation(v.floor))
                if vb <= base + 1.0:
                    continue
                va, vbp = v.p1, v.p2
                vl = math.hypot(vbp.x() - va.x(), vbp.y() - va.y())
                if vl < 1e-6:
                    continue
                t = (((mx - va.x()) * (vbp.x() - va.x())
                      + (my - va.y()) * (vbp.y() - va.y())) / (vl * vl))
                t = max(0.0, min(1.0, t))
                px, py = va.x() + t * (vbp.x() - va.x()), va.y() + t * (vbp.y() - va.y())
                if math.hypot(mx - px, my - py) <= 20.0:
                    best = min(best, vb)
            return best

        pieces = []                                        # {kind, depth, outline, ...}
        for w, _rec in front:
            a, b = w.p1, w.p2
            L = math.hypot(b.x() - a.x(), b.y() - a.y())
            ux, uy = (b.x() - a.x()) / L, (b.y() - a.y()) / L
            base = float(floor_elevation(w.floor))
            mx, my = 0.5 * (a.x() + b.x()), 0.5 * (a.y() + b.y())
            above = higher_base_over(mx, my, base)
            # the wall top: min roof surface above it (rake under a gable, flat at
            # the eave), capped at the next storey where one stacks on it.
            samples = 24
            top_pts = []
            for i in range(samples + 1):
                t = i / samples
                x, y = a.x() + t * (b.x() - a.x()), a.y() + t * (b.y() - a.y())
                cand = [z for r in main_roofs
                        if (z := self._roof_surface_z(r, x, y)) is not None
                        and z > base + 1.0]
                top = min([above] + cand)
                if top == math.inf:
                    top = base + DEFAULT_CAMERA_CEILING_IN
                top_pts.append((pt_u(x, y), max(top, base + 1.0)))
            ua, ub = pt_u(a.x(), a.y()), pt_u(b.x(), b.y())
            u_lo, u_hi = (ua, ub) if ua <= ub else (ub, ua)
            top_pts.sort(key=lambda q: q[0])
            outline = [(u_lo, base), (u_hi, base)] + [(u, z) for u, z in reversed(top_pts)]
            ops = []
            for o in getattr(w, "openings", []):
                if sip.isdeleted(o):
                    continue
                ww = float(getattr(o, "width", 0.0) or 0.0)
                hh = float(getattr(o, "height", 0.0) or 0.0)
                if ww <= 0.0 or hh <= 0.0:
                    continue
                uc = pt_u(a.x() + ux * float(o.s), a.y() + uy * float(o.s))
                kind = getattr(o, "kind", "window")
                if kind == "window":
                    s = getattr(o, "sill_in", None)
                    sill = base + (float(s) if s is not None else DEFAULT_SILL_IN)
                else:
                    sill = base
                ops.append({"x0": uc - ww / 2.0, "x1": uc + ww / 2.0,
                            "sill": sill, "head": sill + hh, "kind": kind})
            pieces.append({"kind": "wall",
                           "depth": min(pt_depth(a.x(), a.y()), pt_depth(b.x(), b.y())),
                           "outline": outline, "openings": ops,
                           "wall_type": getattr(w, "wall_type", "exterior")})

        # the roof faces (main roofs AND dormers): each gable/shed roof's 3-D
        # wireframe -- ridge + eave corners lifted to absolute Z -- split into two
        # slopes and two gable ends; the camera-facing faces (that aren't edge-on
        # slivers) are drawn. A dormer's own face windows ride frontmost.
        fwd = (dx, dy, 0.0)
        dormer_windows = []

        def face_outward_normal(poly, cen):
            n = _tri_normal(poly[0], poly[1], poly[2])
            fc = (sum(q[0] for q in poly) / len(poly),
                  sum(q[1] for q in poly) / len(poly),
                  sum(q[2] for q in poly) / len(poly))
            out = (fc[0] - cen[0], fc[1] - cen[1], fc[2] - cen[2])
            if n[0] * out[0] + n[1] * out[1] + n[2] * out[2] < 0:
                n = (-n[0], -n[1], -n[2])                  # orient OUTWARD
            return n

        for r in roofs:
            datum = float(floor_elevation(_roof_datum_floor(r)))
            ez, rz = datum + float(r.eaves_h_in), datum + float(r.ridge_h_in)
            a1, a2 = r._extended_ridge()
            e1a, e1b, e2a, e2b = r._eave_ends()
            gable = list(getattr(r, "gable", [True, True]))
            # The eave overhang is the roof's OWN geometry, not a drawn-in
            # constant: `overhang_in` is the soffit's plan-perpendicular reach
            # past the eaves line, per side, and `end_overhang_in` is the RAKE
            # past each GABLE end (both honour the roof-parameters dialog and
            # round-trip through the plan). The fascia drops below the eaves
            # height by the true slope * that soffit reach, so a roof with a
            # real overhang laps over the wall below; a roof that stores 0
            # sits flush, which is the faithful picture of its parameters.
            ux, uy, nx, ny = r._axis()
            span_l, span_r = r.span_in
            eo1, eo2 = r.end_overhang_in          # per-end rake reach (along)

            def side_eave(span, oh, rise=rz - ez):
                """(soffit reach, fascia drop) for one roof side. A side with
                no real plane -- a shed's dead side, or the near-zero stub of a
                half-gable, whose pitch would be all but vertical -- carries no
                soffited eave (a cut/abutment, not an eave), so an overhang set
                there projects nothing instead of dropping off the drawing."""
                if span <= 1e-6:
                    return 0.0, 0.0
                slope = rise / span
                if slope > MAX_EAVE_PITCH:        # a vertical cut, not an eave
                    return 0.0, 0.0
                return oh, slope * oh             # fascia drop = slope * overhang

            oh_l, drop_l = side_eave(span_l, r.overhang_in[0])
            oh_r, drop_r = side_eave(span_r, r.overhang_in[1])
            re1 = eo1 if gable[0] else 0.0         # rake only past a GABLE end
            re2 = eo2 if gable[1] else 0.0
            rr1 = (a1.x() - ux * re1, a1.y() - uy * re1, rz)
            rr2 = (a2.x() + ux * re2, a2.y() + uy * re2, rz)
            ll1 = (e1a.x() + nx * oh_l - ux * re1, e1a.y() + ny * oh_l - uy * re1, ez - drop_l)
            ll2 = (e1b.x() + nx * oh_l + ux * re2, e1b.y() + ny * oh_l + uy * re2, ez - drop_l)
            qq1 = (e2a.x() - nx * oh_r - ux * re1, e2a.y() - ny * oh_r - uy * re1, ez - drop_r)
            qq2 = (e2b.x() - nx * oh_r + ux * re2, e2b.y() - ny * oh_r + uy * re2, ez - drop_r)
            allp = [ll1, ll2, qq1, qq2, rr1, rr2]
            cen = (sum(q[0] for q in allp) / 6.0, sum(q[1] for q in allp) / 6.0,
                   sum(q[2] for q in allp) / 6.0)
            # his tweak: a REAR dormer (its FACE gable, end 0, turned away from the
            # camera) is on the back of the house -- drop it whole, windows and all,
            # so it never bleeds onto the front elevation.
            if r.is_dormer():
                nface = face_outward_normal([ll1, qq1, rr1], cen)
                if nface[0] * fwd[0] + nface[1] * fwd[1] + nface[2] * fwd[2] >= -1e-6:
                    continue                               # a rear dormer
                dormer_windows.extend(self._dormer_face_windows(r, pt_u))
            faces = [[ll1, ll2, rr2, rr1], [qq1, qq2, rr2, rr1]]
            if gable[0]:
                faces.append([ll1, qq1, rr1])
            if gable[1]:
                faces.append([ll2, qq2, rr2])
            for poly in faces:
                n = face_outward_normal(poly, cen)
                if n[0] * fwd[0] + n[1] * fwd[1] + n[2] * fwd[2] >= -1e-6:
                    continue                               # faces away from camera
                uz = [(pt_u(q[0], q[1]), q[2]) for q in poly]
                us = [p[0] for p in uz]
                if max(us) - min(us) < 24.0:               # an edge-on gable sliver
                    continue
                # sort by the NEAREST edge, so a roof that comes forward (a wing,
                # a garage) stacks IN FRONT of a roof set further back behind it.
                depth = min(pt_depth(q[0], q[1]) for q in poly)
                pieces.append({"kind": "roof", "depth": depth, "outline": uz})

        pieces.sort(key=lambda pc: pc["depth"], reverse=True)   # far -> near

        wall_ops = [o for pc in pieces if pc["kind"] == "wall" for o in pc["openings"]]
        all_u = ([u for pc in pieces for u, _z in pc["outline"]]
                 + [o["x0"] for o in wall_ops] + [o["x1"] for o in wall_ops]
                 + [dw[0] for dw in dormer_windows] + [dw[1] for dw in dormer_windows])
        all_z = ([z for pc in pieces for _u, z in pc["outline"]]
                 + [o["head"] for o in wall_ops] + [dw[3] for dw in dormer_windows])
        u_min, u_max = min(all_u), max(all_u)
        z_min, z_max = min(all_z), max(all_z)
        return {"mode": "house_elev", "room_name": "",
                "extent": (u_min, u_max, z_min, z_max),
                "floor_abs_in": float(z_min),
                "width_in": u_max - u_min, "height_in": z_max - z_min,
                "pieces": pieces, "dormer_windows": dormer_windows,
                "faces": [rec for _w, rec in front], "furnishings": [],
                "left_return": None, "right_return": None}

    @staticmethod
    def _roof_surface_z(r, x, y):
        """Absolute height (in) of gable/shed roof `r`'s surface over the plan
        point (x, y), or None if the point is outside the roof's body footprint.
        The surface is `ridge_h - slope*|perp|` per side (0140/R4a); the datum is
        the roof's own level, a dormer's HOST level (`_roof_datum_floor`)."""
        from floorplanner.roofs import _roof_datum_floor
        ux, uy, nx, ny = r._axis()
        r1 = r.p1
        ridge_len = math.hypot(r.p2.x() - r1.x(), r.p2.y() - r1.y())
        along = (x - r1.x()) * ux + (y - r1.y()) * uy
        perp = (x - r1.x()) * nx + (y - r1.y()) * ny
        if along < -2.0 or along > ridge_len + 2.0:
            return None
        span_l, span_r = r.span_in
        oh_l, oh_r = r.overhang_in
        span, reach = (span_l, span_l + oh_l) if perp >= 0 else (span_r, span_r + oh_r)
        if abs(perp) > reach + 2.0:
            return None
        ridge_h, eaves_h = float(r.ridge_h_in), float(r.eaves_h_in)
        slope = (ridge_h - eaves_h) / span if span > 1e-6 else 0.0
        return (float(floor_elevation(_roof_datum_floor(r)))
                + ridge_h - slope * min(abs(perp), span))

    @staticmethod
    def _dormer_face_windows(r, pt_u):
        """A dormer's own FACE windows (its `gable_elevation`), each as
        `(u0, u1, sill_abs, head_abs, kind)` on the camera-right axis -- drawn
        frontmost, over the dormer gable. `pt_u` projects a plan point onto U."""
        ge = r.gable_elevation()
        lines = r._dormer_wall_lines() if hasattr(r, "_dormer_wall_lines") else None
        if not ge or not lines:
            return []
        a, b = lines[0]
        L = math.hypot(b.x() - a.x(), b.y() - a.y()) or 1.0
        ux, uy = (b.x() - a.x()) / L, (b.y() - a.y()) / L
        mx, my = 0.5 * (a.x() + b.x()), 0.5 * (a.y() + b.y())
        fab = float(ge["floor_abs_in"])
        out = []
        for wn in ge.get("windows", []):
            px, py = mx + ux * wn["centre_in"], my + uy * wn["centre_in"]
            uc = pt_u(px, py)
            hw = float(wn["w_in"]) / 2.0
            out.append((uc - hw, uc + hw, fab + wn["sill_in"], fab + wn["head_in"],
                        wn.get("kind", "window")))
        return out

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
        Outside a room it reads the single faced wall (one face, no returns) --
        OR, with the WHOLE-HOUSE-SIDE switch on (0317), every exterior wall whose
        outside turns toward the camera, laid left->right: the full side of the
        house as an exterior elevation, jogs and wings included."""
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

        # 0317: outside a room with the WHOLE-HOUSE-SIDE switch on, the elevation
        # is EVERY exterior wall whose outside turns toward the camera (the full
        # side of the house, jogs and wings included), not just the one wall the
        # aim ray hits. A wall qualifies when it runs across the view, stands in
        # front, and SEPARATES the camera-side outdoors from an interior room --
        # which drops the far side of the house (its camera-facing side is
        # indoors) and the return walls (they run along the view, not across).
        if room is None and self.show_house_side:
            # 0318: the FULL exterior elevation -- every storey's exterior walls
            # stacked by floor elevation, the roof profile above, the dormers and
            # the gable ends. Returns the whole dict; None falls back to the
            # single faced wall below.
            full = self._house_elevation(dx, dy, rx, ry, cx, cy)
            if full is not None:
                return full

        if faces:                                # the whole-house-side run
            ref_wall = faces[0][2]
        else:
            wall = self.faced_wall()             # the single wall the aim ray hits
            if wall is None:
                return None
            ref_wall = wall
            outline = list(getattr(room, "outline", []) or []) if room is not None else []
            idx = next((i for i, e in enumerate(outline) if e.wall is wall), None)

            if idx is None:                      # outside a room, or wall off-outline
                rec = self._face_record(wall, dx, dy)
                if rec is None:
                    return None
                faces = [(edge_u(wall.p1, wall.p2), rec, wall)]
            else:
                n = len(outline)

                def pts(i):
                    return outline[i].v.point(), outline[(i + 1) % n].v.point()

                picked = {}                      # i -> (u, record)
                stops = []                        # the two bounding (return) edges
                for step in (+1, -1):            # walk both ways from the faced edge
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
                        if i == idx:             # full loop (degenerate) -- stop
                            break
                faces = list(picked.values())
                # the two bounding walls -> left/right by where each sits along
                # the view (midpoint projected onto the camera's right axis).
                rets = [w for w in stops if w is not None]
                scored = sorted(((self._wall_u(w, rx, ry, cx, cy), w) for w in rets),
                                key=lambda t: t[0])

                def _ret(w):
                    return {"label": getattr(w, "uid", "") or "Wall"}

                if len(scored) >= 2:
                    left_ret, right_ret = _ret(scored[0][1]), _ret(scored[-1][1])
                elif len(scored) == 1:           # one return: side by its u sign
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
                "floor_abs_in": float(floor_elevation(ref_wall.floor)),
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
        if self.show_house_side:
            rec["show_house_side"] = True
        if getattr(self, "_uid", None):  # 0316: the persisted session label (C<n>),
            rec["uid"] = self._uid       # read, never minted, during a walk
        return rec

    @classmethod
    def from_record(cls, rec: dict, floor: str):
        it = cls(QPointF(*rec["pos"]), float(rec.get("rotation", 0.0)),
                 floor=floor, name=rec.get("name", ""),
                 show_furnishings=bool(rec.get("show_furnishings", False)),
                 show_cabinetry=bool(rec.get("show_cabinetry", False)),
                 show_house_side=bool(rec.get("show_house_side", False)))
        it.doc_id = rec.get("id")
        return it
