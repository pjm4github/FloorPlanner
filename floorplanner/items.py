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
from floorplanner.parametric import registry as _param_registry
from floorplanner.parametric import stair_geometry as _sg
from floorplanner.parametric import dormer_geometry as _dg
from floorplanner.walls import OpeningItem, WallItem, rebuild_all_walls
from floorplanner.rooms import (
    RoomItem, report_self_intersections, room_owns_walls, walls_cover_room,
    rooms_holding,
)
from floorplanner.roofs import RoofEndMarkerItem, RoofGripItem, RoofItem

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
        # 0323: the item's PARAMETERS (the record's `state`), or None for a
        # furnishing that has none. A subclass may set it before this runs.
        if not hasattr(self, "params"):
            self.params = None
        self._uid = None                  # 0265: the session label, F<n>
        self.floor = active_floor()      # active floor (load overrides)
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
        # cache the rendered SVG symbol at device resolution: it only re-rasters
        # on zoom/selection, not on every full-viewport repaint of the plan (P0.6)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

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
        # 0279: the callout under the footprint is painted, so it is bounded
        # (the view repaints only what changed; outside the box it trails)
        from floorplanner.annotations import (callout_font, callout_rect, callout_text,
                                              callouts_shown, view_lod)
        if callouts_shown() and callout_text(self):
            lod = view_lod(self)
            h = QFontMetricsF(callout_font(lod)).height()
            rect = rect.united(callout_rect(lod, QPointF(0.0, self.d / 2 + h),
                                            callout_text(self), "center"))
        return rect

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(QRectF(-self.w / 2, -self.d / 2, self.w, self.d))
        if self.isSelected():
            c, r = self._handle()
            path.addEllipse(c, r * 1.8, r * 1.8)
        return path

    @property
    def uid(self) -> str:
        """The furnishing's session label (`F4`), minted on first read; a
        load adopts the file's own id (labels.py)."""
        if getattr(self, "_uid", None) is None:
            from floorplanner import labels as _labels
            self._uid = _labels.mint("F")
        return self._uid

    def paint(self, painter, option, widget=None):
        rect = QRectF(-self.w / 2, -self.d / 2, self.w, self.d)
        if floor_display_mode(self.floor) != "active":
            # non-active floor: a flat gray footprint (the SVG keeps its own
            # colors, so show the outline/extent instead) and no handle.
            painter.setPen(QPen(FLOOR_GHOST, 0))
            painter.setBrush(QBrush(QColor(176, 176, 176, 40)))
            painter.drawRect(rect)
            return
        # 0264: the furnishing's document id under its footprint, in the
        # callout ink, while Show > Item callouts is on
        from floorplanner.annotations import callout_font, callout_text, callouts_shown, draw_callout
        if callouts_shown() and callout_text(self):
            # 0267: the one callout font, under the footprint
            lod = max(option.levelOfDetailFromTransform(painter.worldTransform()), 1e-6)
            h = QFontMetricsF(callout_font(lod)).height()
            draw_callout(painter, lod, QPointF(0.0, self.d / 2 + h), callout_text(self), "center")
        r = furnishing_renderer(self.kind)
        definition = _param_registry.get(self.kind)
        symbol = (definition.plan_symbol(self.params or {})
                  if definition is not None else None)
        if symbol is not None:
            self._paint_plan_symbol(painter, symbol)
        elif r is not None:
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
        """Per-kind state to persist alongside kind/pos/rotation: the item's
        parameters, when it has any.  Subclasses (e.g. StairItem) override."""
        return dict(self.params) if self.params else {}

    # -- parametric furnishings (0323) ---------------------------------------
    def is_parametric(self) -> bool:
        """True when this kind has a registered parameter definition."""
        return _param_registry.is_parametric(self.kind)

    def _room_style(self):
        """0329: the STYLE of the room this item stands in (its
        `properties["style"]`), or None -- what a cabinet's finish, countertop
        and hardware fall back to. The smallest room holding the item's
        centre, the same owner the plan file records."""
        room = self._owning_room()
        if room is None:
            return None
        style = room.properties.get("style")
        return dict(style) if isinstance(style, dict) else None

    def _owning_room(self):
        """The smallest room on this item's floor that holds its centre."""
        sc = self.scene()
        if sc is None:
            return None
        pt = self.scenePos()
        best = None
        for it in sc.items():
            if (isinstance(it, RoomItem) and it.floor == self.floor
                    and it.path.contains(pt)):
                area = abs(it.path.boundingRect().width()
                           * it.path.boundingRect().height())
                if best is None or area < best[0]:
                    best = (area, it)
        return None if best is None else best[1]

    def _room_ceiling(self) -> float:
        """0333: the ceiling a ceiling light hangs from -- its room's."""
        room = self._owning_room()
        try:
            return float(room.properties.get("ceiling_height_in")) if room else 96.0
        except (TypeError, ValueError):
            return 96.0

    def param_context(self) -> dict:
        """What a parameter definition may read about where the item stands:
        its floor, every floor's elevation, and its room's style."""
        return {"this_floor": self.floor,
                "this_elev": floor_elevation(self.floor),
                "elevations": floor_elevations(),
                "room_style": self._room_style(),
                "ceiling_in": self._room_ceiling()}

    def _paint_plan_symbol(self, painter, symbol):
        """0338: a plan symbol drawn from the item's PARAMETERS -- an island
        with its own slots, sink, cooktop and one stool per seat. `symbol`
        is in the cabinet frame (x across, f down from the top edge)."""
        top = -self.d / 2.0
        ink = QColor(55, 65, 81)

        def box(x0, f0, x1, f1):
            return QRectF(QPointF(x0, top + f0), QPointF(x1, top + f1))

        x0, _f0, x1, _f1 = symbol["top"]
        back = symbol["back"]
        painter.setPen(QPen(ink, 1.2))
        painter.setBrush(QBrush(QColor(248, 250, 252)))
        painter.drawRoundedRect(
            box(*symbol["top"]).adjusted(0.6, 0.6, -0.6, -0.6), 1.0, 1.0)
        # where the cabinets end, and where one slot meets the next
        painter.setPen(QPen(ink, 0.5, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(x0 + 0.6, top + back),
                         QPointF(x1 - 0.6, top + back))
        for _a, b, _code in symbol.get("slots", ())[1:]:
            painter.drawLine(QPointF(b, top + 0.6), QPointF(b, top + back))
        painter.setPen(QPen(ink, 0.7))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        for bx0, bf0, bx1, bf1 in symbol.get("bowls", ()):
            painter.drawRoundedRect(box(bx0, bf0, bx1, bf1), 1.5, 1.5)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for hx0, hf0, hx1, hf1 in symbol.get("hobs", ()):
            painter.drawRect(box(hx0, hf0, hx1, hf1))
            for u, v in ((0.27, 0.30), (0.73, 0.30), (0.27, 0.72), (0.73, 0.72)):
                painter.drawEllipse(QPointF(hx0 + (hx1 - hx0) * u,
                                            top + hf0 + (hf1 - hf0) * v), 2.6, 2.6)
        # one stool per seat, under the overhang: seat, and its short back
        painter.setBrush(QBrush(QColor(226, 232, 240)))
        for sx0, sf0, sx1, sf1 in symbol.get("stools", ()):
            painter.drawRoundedRect(box(sx0, sf0, sx1, sf1), 2.5, 2.5)
            painter.drawLine(QPointF(sx0 + 1.5, top + sf1 - 1.6),
                             QPointF(sx1 - 1.5, top + sf1 - 1.6))

    def draft_state(self) -> dict:
        """The state a properties dialog starts editing -- a COPY."""
        return dict(self.params or {})

    def _apply_footprint(self):
        """0329: a kind whose FOOTPRINT follows its parameters (a cabinet's
        width and depth) resizes here; the plan symbol is drawn into the new
        rectangle. The item's position is its centre, so it grows both ways."""
        definition = _param_registry.get(self.kind)
        if definition is None:
            return
        size = definition.footprint(self.params or {})
        if not size:
            return
        w, d = float(size[0]), float(size[1])
        if abs(w - self.w) > 1e-9 or abs(d - self.d) > 1e-9:
            self.prepareGeometryChange()
            self.w, self.d = w, d
            tip = f"{self.name} \u2014 {fmt_in(self.w)} \u00d7 {fmt_in(self.d)}"
            if self.price > 0:
                tip += f"  \u00b7  ${self.price:,.0f}"
            self.setToolTip(tip + "  \u00b7  double-click to edit")

    def apply_params(self, state: dict):
        """Take an accepted parameter set. The kind decides what is worth
        WRITING (a cabinet stores only what differs from its preset), and
        the footprint follows. A kind whose whole shape is its parameters --
        the stair -- overrides this."""
        definition = _param_registry.get(self.kind)
        if definition is not None:
            state = definition.to_state(state or {})
        self.params = dict(state or {}) or None
        self._apply_footprint()
        self.update()

    def make_properties_dialog(self, parent=None):
        """The properties dialog for this item, NOT shown -- or None for a
        kind that has no parameters."""
        definition = _param_registry.get(self.kind)
        if definition is None:
            return None
        from floorplanner.parametric.dialog import ParametricDialog  # late: Qt widgets
        return ParametricDialog(definition, self.draft_state(),
                                self.param_context(), parent)

    def open_properties(self, parent=None) -> bool:
        """Open the modal properties dialog; apply on OK. True when applied.
        The dialog edits a draft, so Cancel leaves the item untouched."""
        if parent is None:
            sc = self.scene()
            if sc is not None and sc.views():
                parent = sc.views()[0].window()
        dlg = self.make_properties_dialog(parent)
        if dlg is None:
            return False
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return False
        state = dlg.result_state()
        if state is None:
            return False
        self.apply_params(state)
        return True

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.is_parametric():
            self.open_properties()
            e.accept()
            return
        super().mouseDoubleClickEvent(e)


class StairItem(FurnishingItem):
    """A stair flight whose number of steps is computed from the ceiling
    height of the room it is placed in.  `flight` is 'full' or 'half';
    a half flight rises to a landing that either ends ('none') or turns
    'left'/'right' for the remaining rise.  `direction` ('up'/'down')
    flips the travel arrow.

    THAT IS THE LEGACY STAIR, and a stair keeps drawing that way for as long
    as `params` is None -- every stair saved before 0323 (Patrick,
    2026-11-14: "keep existing stairs frozen until I edit").  A stair WITH
    `params` is PARAMETRIC: straight, L or U, its rise taken from the floor
    levels or typed in, its tread depth, width, riser count and landing
    height editable from the properties dialog (double-click).  Its whole
    shape then comes from `floorplanner.parametric.stair_geometry`, the same
    calculator the 3D viewer loads."""

    def __init__(self, pos: QPointF, rotation: float = 0.0, *,
                 flight: str = "full", turn: str = "left",
                 direction: str = "up", params: dict = None):
        self.flight = flight if flight in ("full", "half") else "full"
        self.turn = turn if turn in ("none", "left", "right") else "left"
        self.direction = direction if direction in ("up", "down") else "up"
        self.params = None
        self._rise_used = None
        self._recompute_pending = False
        if params is not None:
            self.params = _sg.normalize_state(params)
            self._sync_legacy_attrs()
        self.n_risers = 14
        self._off = QPointF(0.0, 0.0)
        self._geo = {"rects": [], "steps": [], "arrow": [], "label": ""}
        super().__init__("stairs", pos, rotation)
        self._recompute()

    def extra_state(self) -> dict:
        legacy = {"flight": self.flight, "turn": self.turn,
                  "direction": self.direction}
        if self.params is None:
            return legacy
        # flight / turn / direction are still written, so a build from before
        # 0323 opens the file and draws a stair on the same side
        state = dict(self.params)
        state.update(legacy)
        return state

    # -- parameters (0323) ---------------------------------------------------
    def _sync_legacy_attrs(self):
        """Keep flight / turn / direction telling the truth about a
        parametric stair, for the code and the older builds that read them."""
        st = self.params
        self.flight = "full" if st["type"] == "straight" else "half"
        if st["type"] != "straight":
            self.turn = "right" if st["turn_deg"] > 0 else "left"
        self.direction = st["direction"]

    def _param_geometry(self):
        """(geometry or None, rise) for a parametric stair, where it stands."""
        ctx = self.param_context()
        elevs = list(ctx["elevations"].values())
        try:
            geom, rise, _ok = _sg.geometry_from_state(
                self.params, ctx["this_elev"], elevs)
        except _sg.StairError:
            rise, _ok = _sg.effective_rise(self.params, ctx["this_elev"], elevs)
            return None, rise
        return geom, rise

    def draft_state(self) -> dict:
        if self.params is not None:
            return dict(self.params)
        # A LEGACY stair opens on its own numbers, so the dialog's picture is
        # the stair on the plan; nothing changes unless the user accepts.
        rise = self._ceiling_height()
        n = self.n_risers
        st = dict(_sg.STATE_DEFAULTS)
        st.update(rise_mode="detached", total_rise_in=rise,
                  tread_depth_in=STAIR_TREAD, stair_width_in=STAIR_WIDTH,
                  riser_count_mode="manual", riser_count=n,
                  direction=self.direction)
        if self.flight == "half":
            first = max(1, (n - 1) // 2)             # treads below the landing
            if self.turn in ("left", "right"):
                st.update(type="L", turn_deg=90 if self.turn == "right" else -90,
                          landing_mode="custom",
                          landing_height_in=(first + 1) * rise / n)
            else:                                    # ended at its landing
                st.update(total_rise_in=(first + 1) * rise / n,
                          riser_count=first + 1)
        return _sg.normalize_state(st)

    def apply_params(self, state: dict):
        """Take an accepted parameter set and redraw. THE FOOT STAYS WHERE IT
        IS: the item's position is the centre of its footprint, which moves
        when the footprint changes, so the position is shifted to keep the
        first riser on the spot the user put it."""
        foot = self.mapToScene(self._off)
        self.params = _sg.normalize_state(state)
        self._sync_legacy_attrs()
        self._recompute()
        moved = self.mapToScene(self._off)
        self.setPos(self.pos() + (foot - moved))
        self.update()

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

    def _build_parametric(self):
        """(geo, tooltip) for a parametric stair, in the same shape `_build`
        returns so one `paint` serves both."""
        geom, rise = self._param_geometry()
        self._rise_used = rise
        if geom is None or geom.tread_count < 1:
            # nothing drawable: keep a one-tread placeholder so the item can
            # still be selected and its properties reopened to fix it
            w = self.params["stair_width_in"] if self.params["stair_width_in"] > 0 else STAIR_WIDTH
            t = STAIR_TREAD
            self.n_risers = 0 if geom is None else geom.riser_count
            return ({"rects": [QRectF(0, 0, w, t)], "steps": [],
                     "line": [QPointF(w / 2, t * 0.25), QPointF(w / 2, t * 0.75)],
                     "label_pt": QPointF(w / 2 + 1, t * 0.25)},
                    "Stairs \u2014 these parameters do not make a stair; "
                    "double-click to edit")
        self.n_risers = geom.riser_count
        plan = _sg.plan(geom)
        geo = {"rects": [QRectF(x, y, w, h) for x, y, w, h in plan["rects"]],
               "steps": list(plan["steps"]),
               "line": [QPointF(x, y) for x, y in plan["line"]],
               "label_pt": QPointF(*plan["label"])}
        shape = {"straight": "straight", "L": "L", "U": "U"}[geom.stair_type]
        tip = (f"Stairs \u2014 {shape}, {geom.riser_count} risers @ "
               f"{geom.riser_height:.3f}\", {geom.tread_count} treads @ "
               f"{geom.tread_depth:g}\"; rise {geom.total_rise:g}\" "
               f"({self.params['rise_mode']}). Double-click to edit.")
        return geo, tip

    def _recompute(self):
        self._recompute_pending = False
        self.prepareGeometryChange()
        if self.params is not None:
            self.params["direction"] = self.direction
            geo, tip = self._build_parametric()
            bbox = QRectF(geo["rects"][0])
            for r in geo["rects"][1:]:
                bbox = bbox.united(r)
            self._geo = geo
            self._bbox = bbox
            self.w = bbox.width()
            self.d = bbox.height()
            self._off = QPointF(-bbox.center().x(), -bbox.center().y())
            self.setToolTip(tip)
            self.update()
            return
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
    def _rise_is_stale(self) -> bool:
        """A LINKED stair follows the floor levels. Nothing tells the item
        when a level moves, so it asks as it paints -- one subtraction."""
        if self.params is None or self.params["rise_mode"] != "linked":
            return False
        rise, _ok = _sg.effective_rise(self.params, floor_elevation(self.floor),
                                       list(floor_elevations().values()))
        return self._rise_used is None or abs(rise - self._rise_used) > 1e-6

    def _deferred_recompute(self):
        # The footprint is rebuilt about the item's POSITION, which is its
        # centre and is what the plan file stores -- so a stair read back
        # from a file lands exactly where it was saved even when the floor
        # levels reach the cache after the item is built.
        if sip.isdeleted(self):
            return
        self._recompute()

    def paint(self, painter, option, widget=None):
        if not self._recompute_pending and self._rise_is_stale():
            # never change geometry inside paint: do it on the next turn
            self._recompute_pending = True
            QTimer.singleShot(0, self._deferred_recompute)
        ghost = floor_display_mode(self.floor) != "active"
        painter.save()
        painter.translate(self._off)
        ink = FLOOR_GHOST if ghost else QColor(55, 65, 81)
        fill = QColor(176, 176, 176, 40) if ghost else QColor(248, 250, 252)
        painter.setPen(QPen(ink, 1.2))
        painter.setBrush(QBrush(fill))
        for r in self._geo["rects"]:
            painter.drawRect(r)
        painter.setPen(QPen(ink, 0.7))
        for x1, y1, x2, y2 in self._geo["steps"]:
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        self._paint_arrow(painter, ink)
        painter.restore()
        if not ghost and self._handle_visible():
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
        a_props = menu.addAction("Stair properties\u2026")
        menu.addSeparator()
        m_flight = menu.addMenu("Flight")
        # a parametric stair's type and turn are set in its properties, where
        # they are validated; the two menus stay for a legacy stair only
        m_flight.menuAction().setVisible(self.params is None)
        for label, val in [("Full flight", "full"),
                           ("Half flight (landing)", "half")]:
            a = m_flight.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.flight == val)
            a.setData(("flight", val))
        m_turn = menu.addMenu("Half-flight direction")
        m_turn.setEnabled(self.flight == "half")
        m_turn.menuAction().setVisible(self.params is None)
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
        if chosen is a_props:
            self.open_properties()
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


class DormerItem(FurnishingItem):
    """A DORMER furnishing (0352, phase 2).

    Dropped on the level whose rooms it lights, like any furnishing -- but it
    OWNS NO WALL. Editing it computes no wall; the only plan lines it draws are
    its own outline (ridge, eaves, rake, valleys), the control GUIDES (C/D),
    and the KNEE LINES where its planes cross the room's ceiling plane. The
    walls under it are whatever the user draws on that level.

    THE ITEM'S POSITION IS THE ANCHOR (P2, 2026-11-18) -- the point on the host
    roof where the ridge dies into it, the ridge's HIGH end. `rotation` turns
    the ridge. `dormer_geometry` keeps its FACE frame (origin = face, +y up the
    ridge), so the item draws a dg point `(x, y)` at ITEM-local `(x, depth - y)`
    (`_q`): the anchor (dg y = depth) lands at the item origin and the face (dg
    y = 0) sits `depth` DOWNHILL of it. The anchor's height on the roof IS the
    ridge height, so the ridge rises as the anchor is moved up the slope; eaves
    or pitch floats to hold it (`dg.couple_ridge`, `_recompute`). An OLD record
    (pos = face) migrates once (`_migrate_to_anchor`).

    THE HOST IS FOUND BY HEIGHT each rebuild and nothing about it is stored
    (`host_roof_at` + `roofclip.surface_height`, shifted to this level's
    datum): a dormer over no roof is drawn, reported and cuts nothing. The 3D
    roof and the host cut are phase 3; this item is the plan side."""

    _GUIDE_INK = QColor(120, 120, 120)

    def __init__(self, pos: QPointF, rotation: float = 0.0, *,
                 params: dict = None, new: bool = False):
        self.params = _dg.normalize_state(params or _dg.STATE_DEFAULTS)
        self._seed_defaults = new and not params   # host pitch on first rebuild
        self._pinned = "pitch_12"                   # under the anchor, eaves floats
        # P2: pos is the ANCHOR (ridge-on-roof), not the face. A fresh drop is
        # already anchored (the user clicks the anchor); an OLD record (pos =
        # face, no `anchored`) migrates once on the first rebuild in a scene.
        if new:
            self.params["anchored"] = True
        self._migrate_anchor = not self.params.get("anchored")
        self._geo = _dg.plan(self.params)
        self._knees = []                            # orange knee lines, settled
        self._unbuildable = None                    # dg.unbuildable reason, or None
        self._depth = self.params["depth_in"]       # ridge length, anchor to face
        self._bbox = QRectF(-1, -1, 2, 2)
        self._sig = None
        self._recompute_pending = False
        self._frozen = False
        self._grips = []                            # DormerGripItem children
        super().__init__("dormer", pos, rotation)
        self._recompute()

    # -- state ---------------------------------------------------------------
    def extra_state(self) -> dict:
        return {k: self.params[k] for k in _dg.STATE_DEFAULTS}

    def draft_state(self) -> dict:
        return dict(self.params)

    def apply_params(self, state: dict):
        """Take an accepted parameter set and redraw. The FACE stays put (it is
        the item's position / anchor), so unlike a stair nothing is shifted."""
        self.params = _dg.normalize_state(state)
        self._seed_defaults = False
        self._recompute()
        self._place_grips()
        self.update()

    # -- the host, found by height -------------------------------------------
    def _host_plane(self):
        """(height at the face, slope along the ridge, host ridge height, host
        EAVE height, OFF-AXIS degrees) of the roof under the dormer, in THIS
        level's datum -- or (None,)*5 when no roof is under it. Nothing is
        stored. The ridge and eave heights bound the anchor's travel up the roof
        (`dg.host_extent`); `offaxis_deg` is how far the ridge runs off the
        host's fall line (straight downhill, `None` on the ridge line itself) --
        past `dg.FACING_TOL_DEG` is `NOT_DOWNHILL` (Patrick, 2026-11-18, P1/P2
        of the control redesign)."""
        sc = self.scene()
        if sc is None:
            return None, None, None, None, None
        from floorplanner.roofs import host_roof_at, upslope_direction
        from floorplanner.roofclip import surface_height
        face = self.pos()
        host = host_roof_at(sc, face, self.floor)
        if host is None:
            return None, None, None, None, None
        shift = float(floor_elevation(host.floor)) - float(floor_elevation(self.floor))
        direction = _dg.ridge_direction(self.rotation())
        z_face, slope = _dg.host_plane(
            lambda p: surface_height(host, QPointF(p[0], p[1])) + shift,
            (face.x(), face.y()), direction)
        up = upslope_direction(host, face)       # unit toward the ridge, or None
        offaxis = None
        if up is not None:
            dot = max(-1.0, min(1.0, direction[0] * up[0] + direction[1] * up[1]))
            offaxis = math.degrees(math.acos(dot))
        return (z_face, slope, float(host.ridge_h_in) + shift,
                float(host.eaves_h_in) + shift, offaxis)

    def param_context(self) -> dict:
        ctx = super().param_context()
        z_anchor, slope, ridge, eave, offaxis = self._host_plane()  # at pos=anchor
        if z_anchor is not None:
            # dg works in the FACE frame: the face is `depth` DOWNHILL of the
            # anchor, so its host height is z_anchor - slope*depth. With the
            # ridge held at the anchor (couple below), this makes dg.ridge_depth
            # return `depth` and the whole face-frame geometry stays correct.
            depth = max(self.params["depth_in"], 1.0)
            z_face = _dg.ridge_height(self.params) - slope * depth
            ctx.update(host_z_face_in=z_face, host_slope=slope,
                       host_ridge_in=ridge, host_eave_in=eave,
                       host_anchor_in=z_anchor)
            if offaxis is not None:
                ctx["host_offaxis_deg"] = offaxis
        if not self._frozen:                 # not per-frame while a knob drags
            self._face_and_sides(ctx)
            self._wall_below(ctx)            # P4b: the wall below, for the face type
            self._room_below(ctx)            # P5: the room below, for the warning
        return ctx

    def _face_and_sides(self, ctx):
        """F1 (0356): the user's walls on THIS level that stand under the
        dormer's face and its two sides, with their openings handed to `dg`.
        No geometry lives here -- `dg.project_wall` / `project_side_wall` /
        `project_openings` do it; this only gathers and dispatches. `face_wall`
        / `side_walls` are the joined extents (or None when it LOOKED and found
        none); absent means it never looked (no scene)."""
        sc = self.scene()
        if sc is None:
            return
        from floorplanner.walls import WallItem
        from floorplanner.model import DEFAULT_SILL_IN
        rot = self.rotation()
        depth = max(self.params["depth_in"], 1.0)
        ux, uy = _dg.ridge_direction(rot)                 # pos is the ANCHOR; the
        pos = (self.pos().x() - ux * depth,               # FACE is `depth` downhill
               self.pos().y() - uy * depth)

        def op_records(wall):
            out = []
            for op in wall.openings:
                if sip.isdeleted(op):
                    continue
                sill = (op.sill_in if op.sill_in is not None
                        else (DEFAULT_SILL_IN if op.kind == "window" else 0.0))
                head = float(op._v5_extra.get("head_in", float(sill) + op.height))
                out.append({"s0": op.s - op.width / 2.0,
                            "s1": op.s + op.width / 2.0,
                            "sill_in": float(sill), "head_in": head,
                            "id": op._uid or op.code, "kind": op.kind,
                            "code": op.code})
            return out

        walls = [w for w in sc.items()
                 if isinstance(w, WallItem) and not sip.isdeleted(w)
                 and getattr(w, "floor", None) == self.floor]

        def gather(project, *pargs):
            ext, ops = [], []
            for w in walls:
                e = project(pos, rot, (w.p1.x(), w.p1.y()),
                            (w.p2.x(), w.p2.y()), *pargs)
                if e is None:
                    continue
                a, b = e
                ext += [a, b]
                ops += _dg.project_openings(a, b, w.length(), op_records(w))
            return ((min(ext), max(ext)) if ext else None), ops

        ctx["face_wall"], ctx["face_openings"] = gather(_dg.project_wall)
        side_walls, side_openings = {}, {}
        for side in _dg.SIDES:
            span, ops = gather(_dg.project_side_wall, _dg.side_x(self.params, side))
            side_walls[side], side_openings[side] = span, ops
        ctx["side_walls"], ctx["side_openings"] = side_walls, side_openings

    def _wall_below(self, ctx):
        """P4b (0352): is there an exterior wall on the floor BELOW, aligned
        under the dormer FACE? The plain-wall / setback reading needs it. Like
        F1 but on the level below, projected onto the face line. `wall_below` is
        the across-extent (or None when there is no lower floor / no wall)."""
        sc = self.scene()
        if sc is None:
            return
        from floorplanner.walls import WallItem
        from floorplanner.roofs import _floor_below
        below = _floor_below(self.floor)
        if below is None:
            ctx["wall_below"] = None
            return
        rot = self.rotation()
        depth = max(self.params["depth_in"], 1.0)
        ux, uy = _dg.ridge_direction(rot)
        face = (self.pos().x() - ux * depth, self.pos().y() - uy * depth)
        ext = []
        for w in sc.items():
            if (not isinstance(w, WallItem) or sip.isdeleted(w)
                    or getattr(w, "floor", None) != below):
                continue
            e = _dg.project_wall(face, rot, (w.p1.x(), w.p1.y()),
                                 (w.p2.x(), w.p2.y()))
            if e is not None:
                ext += list(e)
        ctx["wall_below"] = (min(ext), max(ext)) if ext else None

    def _room_below(self, ctx):
        """P5 (0360): is a ROOM defined on the floor BELOW, under the dormer?
        Patrick wants a prominent warning when the storey beneath the face is
        undefined -- the 3D builder cannot otherwise tell how the face meets the
        house. `room_below` is True when a room on the lower floor covers the
        anchor or the face point, False when the lower floor has none there, and
        None when there is no lower floor at all. Scene-coord `path.contains`,
        the same frame `_wall_below` uses (rooms paint at pos 0,0)."""
        sc = self.scene()
        if sc is None:
            return
        from floorplanner.rooms import RoomItem
        from floorplanner.roofs import _floor_below
        below = _floor_below(self.floor)
        if below is None:
            ctx["room_below"] = None
            return
        rot = self.rotation()
        depth = max(self.params["depth_in"], 1.0)
        ux, uy = _dg.ridge_direction(rot)
        anchor = self.pos()
        face = QPointF(anchor.x() - ux * depth, anchor.y() - uy * depth)
        found = False
        for it in sc.items():
            if (not isinstance(it, RoomItem) or sip.isdeleted(it)
                    or getattr(it, "floor", None) != below):
                continue
            if it.path.contains(anchor) or it.path.contains(face):
                found = True
                break
        ctx["room_below"] = found

    def as_camera_roof(self):
        """P3.3 (0352, 2026-11-19): a TRANSIENT RoofItem for the 2D elevation
        camera, so a dormer FURNISHING draws in an elevation like a roof-dormer.
        The host is resolved by the anchor; the heights are shifted to the host's
        datum (which the camera reads via `_roof_datum_floor`) -- the same record
        `fp3d` builds the 3D from (`dg.to_roof_record`). None when over no roof.
        The item is not added to any scene; the camera only reads its geometry."""
        sc = self.scene()
        if sc is None:
            return None
        from floorplanner.roofs import RoofItem, host_roof_at
        host = host_roof_at(sc, self.pos(), self.floor)
        if host is None or sip.isdeleted(host):
            return None
        rot = self.rotation()
        depth = max(self.params["depth_in"], 1.0)
        ux, uy = _dg.ridge_direction(rot)
        face = (self.pos().x() - ux * depth, self.pos().y() - uy * depth)
        shift = floor_elevation(self.floor) - floor_elevation(host.floor)
        rec = _dg.to_roof_record(_dg.normalize_state(self.params), face, rot,
                                 depth, datum_shift=shift)
        (x0, y0), (x1, y1) = rec["ridge"]
        rr = RoofItem(QPointF(x0, y0), QPointF(x1, y1),
                      eaves_h_in=rec["eaves_h_in"], ridge_h_in=rec["ridge_h_in"],
                      overhang_in=rec["overhang_in"], gable=rec["gable"],
                      span_in=rec["span_in"], marker_end=rec["marker_end"],
                      host=host, form=rec["form"],
                      end_overhang_in=rec["end_overhang_in"],
                      wall_span_in=rec["wall_span_in"],
                      openings=rec.get("openings"))
        rr.floor = self.floor
        return rr

    # -- geometry ------------------------------------------------------------
    def _current_sig(self, ctx):
        return (round(self.pos().x(), 3), round(self.pos().y(), 3),
                round(self.rotation(), 3), id(self.params),
                None if ctx.get("host_z_face_in") is None
                else round(ctx["host_z_face_in"], 3),
                None if ctx.get("host_slope") is None
                else round(ctx["host_slope"], 6),
                None if ctx.get("ceiling_in") is None
                else round(ctx["ceiling_in"], 3))

    def _recompute_outline(self, ctx=None):
        """The dormer's own lines (ridge, eaves, rake, valleys, guides) and
        its extent -- the CHEAP part, recomputed LIVE while a knob drags. The
        orange KNEE LINES are NOT touched here (0354 §2); they settle once on
        release via `_recompute_knees`."""
        if ctx is None:
            ctx = self.param_context()
        z = ctx.get("host_z_face_in")
        slope = ctx.get("host_slope")
        depth, _met = _dg.ridge_depth(self.params, z, slope)
        self._depth = depth
        plan = _dg.plan(self.params, None, z, slope)   # None -> no knee work
        plan["knees"] = self._knees                    # keep the settled ones
        self._geo = plan
        # why this dormer cannot be BUILT on its host (0359), live on a knob
        # drag: paint draws it error-red and drops its host cut + knee lines.
        self._unbuildable = _dg.unbuildable(
            self.params, z, slope, ctx.get("host_ridge_in"),
            ctx.get("host_offaxis_deg"))
        pts = [self._q(p) for p in _dg.footprint(self.params, depth)]
        xs = [p.x() for p in pts]
        ys = [p.y() for p in pts]
        bbox = QRectF(QPointF(min(xs), min(ys)),
                      QPointF(max(xs), max(ys))).adjusted(-2, -2, 2, 2)
        c, r = self._handle()
        bbox = bbox.united(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r))
        self.prepareGeometryChange()
        self._bbox = bbox

    def _recompute_knees(self, ctx=None):
        """The orange knee lines -- where the dormer's planes cross the room
        ceiling. Settled once, on release of a drag (and on a static change)."""
        if ctx is None:
            ctx = self.param_context()
        ceil = ctx.get("ceiling_in")
        self._knees = ([] if ceil is None else
                       _dg.knee_lines(self.params, ceil,
                                      ctx.get("host_z_face_in"),
                                      ctx.get("host_slope")))
        self._geo["knees"] = self._knees

    def _migrate_to_anchor(self):
        """OLD frame -> NEW (P2, 2026-11-18): the record's `pos` was the FACE.
        Sample the host there, find how far the ridge ran to MEET it, and move
        `pos` up the ridge to that meeting point -- the ANCHOR -- keeping
        `depth_in` as the run so the shape does not move. Runs once; marks the
        state `anchored`. With no host, pos is left where it is."""
        self._migrate_anchor = False
        self.params["anchored"] = True
        z_at, slope, _hr, _he, _off = self._host_plane()    # at pos = old face
        if z_at is not None and slope is not None and slope > 0.0:
            depth = _dg.ridge_depth(self.params, z_at, slope)[0]
        else:                                 # no host: keep the stored run, so
            depth = self.params["depth_in"]   # the face stays where it was drawn
        depth = max(depth, 1.0)
        ux, uy = _dg.ridge_direction(self.rotation())
        self.params["depth_in"] = depth
        self.setPos(QPointF(self.pos().x() + ux * depth,
                            self.pos().y() + uy * depth))

    def _recompute(self):
        if self._migrate_anchor and self.scene() is not None:
            self._migrate_to_anchor()
        ctx = self.param_context()
        if self._seed_defaults and ctx.get("host_slope"):
            self.params = _dg.default_state(ctx.get("ceiling_in"),
                                            ctx.get("host_slope"),
                                            ctx.get("host_ridge_in"))
            self.params["anchored"] = True
            self._seed_defaults = False
            ctx = self.param_context()
        # on a roof the ANCHOR sets the ridge: hold ridge = host-at-anchor by
        # floating whichever of eaves/pitch is not pinned (P2, 2026-11-18).
        za, slope = ctx.get("host_anchor_in"), ctx.get("host_slope")
        if za is not None and slope is not None and self.params.get("anchored"):
            coupled = _dg.couple_ridge(self.params, za, self._pinned)
            if coupled != self.params:
                self.params = coupled
                ctx = self.param_context()
        self._recompute_knees(ctx)
        self._recompute_outline(ctx)
        self._sig = self._current_sig(ctx)
        self._recompute_pending = False

    def _deferred_recompute(self):
        if not sip.isdeleted(self):
            self._recompute()
            self._place_grips()
            self.update()

    def _q(self, pt) -> QPointF:
        """A dg-local point (dg's FACE frame) as an item-local point. With the
        ANCHOR as the item's `pos` (P2, 2026-11-18), the face sits `depth`
        DOWNHILL of it: dg y (uphill from the face) maps to item y = depth - y,
        so the anchor (dg y = depth) lands at the item origin and the face
        (dg y = 0) at item +depth."""
        return QPointF(pt[0], self._depth - pt[1])

    def boundingRect(self) -> QRectF:
        return QRectF(self._bbox)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self._bbox)
        return path

    def _handle(self) -> tuple:
        """The rotator handle, in ITEM coordinates: a BLUE RING just UPHILL of
        the ANCHOR (local -y, toward the host), so 'move the anchor' (the apex
        dot) and 'spin around it' (this ring) read as two distinct controls
        (P2, 2026-11-18)."""
        s = self._view_scale()
        stem, r = 16.0 / s, 6.0 / s
        return QPointF(0.0, -(stem + r)), r     # beyond the face

    # -- painting ------------------------------------------------------------
    def paint(self, painter, option, widget=None):
        if not self._frozen and not self._recompute_pending \
                and self._sig != self._current_sig(self.param_context()):
            self._recompute_pending = True          # never change geo in paint
            QTimer.singleShot(0, self._deferred_recompute)
        ghost = floor_display_mode(self.floor) != "active"
        geo = self._geo

        def seg(a, b):
            painter.drawLine(self._q(a), self._q(b))

        if ghost:
            painter.setPen(QPen(FLOOR_GHOST, 0))
            seg(*geo["ridge"])
            for a, b in geo["eaves"]:
                seg(a, b)
            seg(*geo["rake"])
            return
        # an UNBUILDABLE dormer (ridge above the host's, or a non-rising host)
        # still draws, but in error-red and WITHOUT its host cut or knee lines
        # (0359): the dialog says why and refuses OK; the item is not deleted.
        bad = self._unbuildable is not None
        ink = QColor(185, 28, 28) if bad else QColor(55, 65, 81)
        painter.setPen(QPen(ink, 1.3))                  # ridge
        seg(*geo["ridge"])
        painter.setPen(QPen(ink, 0.9))                  # eaves + rake
        for a, b in geo["eaves"]:
            seg(a, b)
        seg(*geo["rake"])
        if not bad:                                     # valleys = the host cut
            painter.setPen(QPen(ink, 1.0))
            for v in geo["valleys"]:
                seg(v[0], v[1])
        painter.setPen(QPen(self._GUIDE_INK, 0.8, Qt.PenStyle.DashLine))
        for a, b in geo["guides"]:                      # controls C / D
            seg(a, b)
        if geo["knees"] and not bad:                    # the knee lines
            painter.setPen(QPen(ROOF_CLIP_INK, 1.6, Qt.PenStyle.DashLine))
            for a, b in geo["knees"]:
                seg(a, b)
        if self._handle_visible():
            self._paint_selection(painter)

    def _paint_selection(self, painter):
        blue = QColor(0, 110, 255)
        painter.setPen(QPen(blue, 0, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self._bbox.adjusted(1, 1, -1, -1))
        c, hr = self._handle()
        painter.setPen(QPen(blue, 0))
        painter.drawLine(QPointF(0.0, 0.0), QPointF(c.x(), c.y() + hr))  # stem from anchor
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(blue, max(1.4, hr * 0.5)))                   # a BLUE RING = spin
        painter.drawEllipse(c, hr, hr)

    # -- the drag hold (0354 §2, Patrick's decision) -------------------------
    def _hold(self, on: bool):
        """Hold the knee recompute for a whole drag and settle once at the
        end: the orange knee lines are NOT redrawn while dragging (0354 §2).
        Holds the HOST's knee (the rooms' `room_ceiling_break_lines`) too."""
        sc = self.scene()
        if sc is None:
            return
        from floorplanner.roofs import hold_roof_clips, hold_rooms
        hold_roof_clips(sc, on)
        hold_rooms(sc, on)
        self._frozen = on

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._hold(True)
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        was = self._frozen
        super().mouseReleaseEvent(e)
        if was:
            self._hold(False)
            self._recompute()       # settle once, now the drag is over
            self._place_grips()
            self.update()

    # -- the knobs A-G (grips) -----------------------------------------------
    # dg-local positions of each grip, from the current parameters + depth.
    _GRIP_KINDS = ("span_l", "span_r", "guide_l", "guide_r",
                   "eave_l", "eave_r", "guide_face", "face", "apex")

    def _grip_local(self, kind):
        """A grip's position in ITEM-local coordinates (dg-local, y-flipped)."""
        st = self.params
        depth = max(self._depth, 1.0)
        sl, sr = st["span_left_in"], st["span_right_in"]
        gl = st["guide_left_in"] or sl
        gr = st["guide_right_in"] or sr
        pt = {
            "span_l":  (sl, 0.50 * depth),
            "span_r":  (-sr, 0.50 * depth),
            "guide_l": (min(gl, sl), 0.30 * depth),
            "guide_r": (-min(gr, sr), 0.30 * depth),
            "eave_l":  (sl + st["eave_overhang_left_in"], 0.68 * depth),
            "eave_r":  (-(sr + st["eave_overhang_right_in"]), 0.68 * depth),
            "guide_face": (0.0, 0.0),            # D (purple): the FACE wall
            "face":    (0.0, -st["face_overhang_in"]),   # F (orange): the EAVE
            "apex":    (0.0, depth),             # A (white): the ANCHOR on the roof
        }[kind]
        return self._q(pt)

    def _grip_kinds(self):
        # Both sides for a gable AND a shed (Patrick, 2026-11-18): the shed's
        # two trapezoid sides each take a B/C/E knob, mirrored when symmetric.
        return list(self._GRIP_KINDS)

    def _sync_grips(self):
        """Create the grips when the dormer is selected, remove them when it is
        not. They are Qt children, so they ride the item's move and rotation."""
        want = self.isSelected() and self.group() is None
        if want and not self._grips:
            self._grips = [DormerGripItem(self, k) for k in self._grip_kinds()]
            self._place_grips()
        elif not want and self._grips:
            sc = self.scene()
            for g in self._grips:
                if sc is not None and not sip.isdeleted(g):
                    sc.removeItem(g)
            self._grips = []

    def _place_grips(self):
        active = floor_display_mode(self.floor) == "active"
        for g in self._grips:
            if sip.isdeleted(g):
                continue
            g.setVisible(active)
            g.setPos(self._grip_local(g.kind))

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self._sync_grips()
        return super().itemChange(change, value)

    # -- a knob drag ---------------------------------------------------------
    def _to_dg_local(self, scene_pt):
        p = self.mapFromScene(scene_pt)
        return p.x(), self._depth - p.y()    # item-local -> dg-local (anchor frame)

    def begin_knob(self):
        self._hold(True)                     # freeze the knee lines (0354 §2)

    def drag_knob(self, kind, scene_pt):
        """Live while a knob is down: reshape the dormer, reposition the grips,
        but DO NOT recompute the orange knee lines (they are held)."""
        if kind == "apex":                   # A is the ANCHOR: it MOVES, not reshapes
            self._drag_anchor(scene_pt)
            return
        x, y = self._to_dg_local(scene_pt)
        st = dict(self.params)
        sym = st["symmetric"]            # a symmetric shed mirrors too (2026-11-18)

        def both(lkey, rkey, v):
            st[lkey] = v
            st[rkey] = v

        if kind in ("span_l", "span_r"):
            v = max(_dg.MIN_SPAN_IN, abs(x))
            both("span_left_in", "span_right_in", v) if sym else st.__setitem__(
                "span_left_in" if kind == "span_l" else "span_right_in", v)
        elif kind in ("guide_l", "guide_r"):
            side = st["span_left_in"] if kind == "guide_l" else st["span_right_in"]
            v = min(max(abs(x), 0.0), side)
            both("guide_left_in", "guide_right_in", v) if sym else st.__setitem__(
                "guide_left_in" if kind == "guide_l" else "guide_right_in", v)
        elif kind in ("eave_l", "eave_r"):
            side = st["span_left_in"] if kind == "eave_l" else st["span_right_in"]
            v = max(abs(x) - side, 0.0)
            both("eave_overhang_left_in", "eave_overhang_right_in", v) if sym \
                else st.__setitem__("eave_overhang_left_in" if kind == "eave_l"
                                    else "eave_overhang_right_in", v)
        elif kind == "guide_face":
            # D (purple) is the FACE WALL: slide it from the anchor out to the
            # orange EAVE, the eave held fixed (P3, 2026-11-18). depth = how far
            # the face is from the anchor; the overhang takes up the rest.
            item_y = self.mapFromScene(scene_pt).y()
            eave = self._depth + st["face_overhang_in"]
            depth = max(min(item_y, eave), 1.0)
            st["depth_in"] = depth
            st["face_overhang_in"] = max(eave - depth, 0.0)
        elif kind == "face":
            # F (orange) is the EAVE: it reaches from the face (purple) out past
            # the host roof edge (a cantilever). overhang = eave beyond the face.
            item_y = self.mapFromScene(scene_pt).y()
            st["face_overhang_in"] = max(item_y - self._depth, 0.0)
        self.params = _dg.normalize_state(st)
        self._recompute_outline()
        self._place_grips()
        self.update()

    def _drag_anchor(self, scene_pt):
        """Knob A, on a roof: slide the ANCHOR along the host's fall line,
        keeping it ON the roof and NO HIGHER than the host ridge (P2 R1a,
        2026-11-18). `pos` moves and the ridge follows (host-at-anchor, via
        `dg.couple_ridge`). Off a roof there is no fall line, so A sets the
        stored run (`depth_in`) as before."""
        sc = self.scene()
        if sc is None:
            return
        from floorplanner.roofs import host_roof_at, upslope_direction
        host = host_roof_at(sc, self.pos(), self.floor)
        up = upslope_direction(host, self.pos()) if host is not None else None
        if host is None or up is None:
            _x, y = self._to_dg_local(scene_pt)     # no roof: old behaviour
            st = dict(self.params)
            st["depth_in"] = max(y, 1.0)
            self.params = _dg.normalize_state(st)
            self._recompute_outline()
            self._place_grips()
            self.update()
            return
        # project the mouse onto the fall line through the anchor, then clamp to
        # a point that is still over THIS host and not above its ridge
        d = scene_pt - self.pos()
        t = d.x() * up[0] + d.y() * up[1]
        cand = QPointF(self.pos().x() + up[0] * t, self.pos().y() + up[1] * t)
        cand = self._anchor_on_roof(host, cand)
        if cand is None:
            return                                  # at the eave or the ridge
        self.setPos(cand)
        za, _slope, _hr, _he, _off = self._host_plane()
        if za is not None:
            self.params = _dg.couple_ridge(self.params, za, self._pinned)
        self._recompute_outline()
        self._place_grips()
        self.update()

    def _anchor_on_roof(self, host, cand):
        """`cand` if the anchor may sit there -- still over `host` and on the
        SAME side of its ridge as now -- else None, so the drag stops at the
        eave (off the roof) and at the ridge (it may not cross to the far side,
        where the dormer would face up the far slope)."""
        sc = self.scene()
        from floorplanner.roofs import host_roof_at
        if host_roof_at(sc, cand, self.floor) is not host:
            return None                             # off this roof (past the eave)
        _ux, _uy, nx, ny = host._axis()

        def perp(p):                                # signed distance from the ridge
            return (p.x() - host.p1.x()) * nx + (p.y() - host.p1.y()) * ny

        if perp(cand) * perp(self.pos()) < -1e-9:
            return None                             # would cross the host ridge
        return cand

    def end_knob(self, kind, scene_pt):
        self.drag_knob(kind, scene_pt)
        self._hold(False)
        self._recompute_knees()              # settle the knee lines, once
        self._geo["knees"] = self._knees
        self.update()

    def contextMenuEvent(self, e):
        menu = QMenu()
        a_props = menu.addAction("Dormer properties…")
        menu.addSeparator()
        a_cw = menu.addAction("Rotate 90° CW")
        a_ccw = menu.addAction("Rotate 90° CCW")
        menu.addSeparator()
        a_del = menu.addAction("Delete dormer")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if chosen is None:
            e.accept()
            return
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        if chosen is a_props:
            self.open_properties()
        elif chosen is a_cw:
            self.setRotation((self.rotation() + 90.0) % 360.0)
            self._recompute()
        elif chosen is a_ccw:
            self.setRotation((self.rotation() - 90.0) % 360.0)
            self._recompute()
        elif chosen is a_del and self.scene() is not None:
            self.scene().removeItem(self)
        e.accept()


class DormerGripItem(QGraphicsItem):
    """One control knob on a selected `DormerItem` (0352 phase 2 -- the knobs
    A-G of `docs/DORMER_CONROLS.md`, moved off `RoofGripItem` onto the
    furnishing). A Qt CHILD of the dormer, so it rides its move and rotation;
    its position is set by `DormerItem._place_grips`. Dragging it reshapes the
    dormer LIVE and HOLDS the knee lines until release (0354 §2):

        span_l / span_r   (B, teal)    the half-width to the eaves line
        guide_l / guide_r (C, yellow)  the KNEE WALL guide: where the side wall
                                       drops to the attic floor (draws no wall)
        eave_l / eave_r   (E, green)   the dormer eave overhang beyond the wall
        guide_face        (D, purple)  the FACE WALL: sets the face distance,
                                       sliding from the anchor out to the eave
        face              (F, orange)  the EAVE, past the host roof edge
        apex              (A, white)   the ANCHOR: drag along the roof; double-
                                       click opens the dialog

    Sized in VIEW PIXELS (like `FurnishingItem`'s rotator and `RoofGripItem`),
    so it stays grabbable at any zoom."""

    SIZE = 3.2            # the drawn glyph half-size, scene inches at 1:1
    HIT_PX = 11.0         # the clickable half-size, view pixels
    _COLORS = {
        "span_l": QColor(0, 160, 170), "span_r": QColor(0, 160, 170),  # teal (B off blue)
        "guide_l": QColor(214, 170, 0), "guide_r": QColor(214, 170, 0),
        "eave_l": QColor(40, 160, 70), "eave_r": QColor(40, 160, 70),
        "guide_face": QColor(150, 60, 200),         # D, purple
        "face": QColor(230, 90, 20), "apex": QColor(90, 90, 90),
    }
    _TIPS = {
        "span_l": "Half-width (knob B) — ridge to the eaves line on this side",
        "span_r": "Half-width (knob B) — ridge to the eaves line on this side",
        "guide_l": "Knee wall (knob C) — where the side wall drops from the "
                   "dormer roof to the attic floor. A guide; draws no wall.",
        "guide_r": "Knee wall (knob C) — where the side wall drops from the "
                   "dormer roof to the attic floor. A guide; draws no wall.",
        "eave_l": "Dormer eave (knob E) — the roof's overhang past the dormer "
                  "wall on this side",
        "eave_r": "Dormer eave (knob E) — the roof's overhang past the dormer "
                  "wall on this side",
        "guide_face": "Face wall (knob D) — the dormer's front wall; slide it "
                      "from the anchor out toward the eave",
        "face": "Eave of the face (knob F) — reaches past the host roof edge",
        "apex": "Anchor (knob A) — drag along the roof; double-click for properties",
    }

    def __init__(self, dormer, kind: str):
        super().__init__(dormer)
        self.dormer = dormer
        self.kind = kind
        self._dragging = False
        self.setZValue(6)
        self.setAcceptHoverEvents(True)
        self.setToolTip(self._TIPS[kind])

    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def _half(self) -> float:
        return max(self.SIZE, self.HIT_PX / self._view_scale())

    def boundingRect(self) -> QRectF:
        r = self._half() + 2.0
        return QRectF(-r, -r, 2.0 * r, 2.0 * r)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        h = self._half()
        path.addRect(QRectF(-h, -h, 2.0 * h, 2.0 * h))
        return path

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        s = self.SIZE
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(self._COLORS.get(self.kind, QColor(0, 120, 215)), 1.4))
        if self.kind == "apex":
            r = s * 1.5
            painter.drawEllipse(QRectF(-r, -r, 2.0 * r, 2.0 * r))
        else:
            painter.drawRect(QRectF(-s, -s, 2.0 * s, 2.0 * s))

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self.dormer.begin_knob()
            e.accept()
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._dragging:
            self.dormer.drag_knob(self.kind, e.scenePos())
            e.accept()
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._dragging and e.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.dormer.end_knob(self.kind, e.scenePos())
            e.accept()
        else:
            super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        if self.kind == "apex" and e.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.dormer._hold(False)            # a press started a hold
            self.dormer.open_properties()
            e.accept()
        else:
            super().mouseDoubleClickEvent(e)


def make_furnishing(kind: str, pos: QPointF, rotation: float = 0.0,
                    state: dict = None, *, new: bool = False):
    """Create the right item for a catalog `kind`: a dynamic StairItem for
    'stairs', otherwise a plain FurnishingItem.  `state` carries per-kind
    extras (e.g. stair flight/turn/direction) from the plan/clipboard.

    0323 -- THREE STAIRS, told apart by what they were saved with:
      * a state carrying PARAMETERS (`type`) -> a parametric stair;
      * `new=True` and no state -- the user has just dropped one from the
        palette -> a parametric stair on the defaults, linked to the level
        above when there is one;
      * anything else -> the legacy stair, exactly as before, so a plan saved
        before parameters existed does not move.
    Any other PARAMETRIC kind keeps the state it was saved with; a plain
    furnishing has none, as before."""
    state = state or {}
    if kind == "stairs":
        if _sg.is_parametric_state(state):
            return StairItem(pos, rotation, params=state)
        if new and not state:
            return StairItem(pos, rotation, params=_sg.default_state(
                floor_elevation(active_floor()),
                list(floor_elevations().values())))
        return StairItem(pos, rotation,
                         flight=state.get("flight", "full"),
                         turn=state.get("turn", "left"),
                         direction=state.get("direction", "up"))
    if kind == "dormer":                              # 0352 phase 2
        return DormerItem(pos, rotation, params=state or None, new=new)
    item = FurnishingItem(kind, pos, rotation)
    if state and _param_registry.is_parametric(kind):
        item.params = dict(state)
        item._apply_footprint()            # 0329: a cabinet's own width / depth
    return item


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
        self.floor = active_floor()       # active floor (set on grouping)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
                     True)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        self._rotating = False
        self._angle = 0.0                 # current orientation of the box
        self._obox = None                 # cached _oriented_box(); see there
        self._snap_walls = self._snap_furn = self._snap_rooms = []
        self._snap_corners = []           # corners a rotation moves (defect 22)

    def _invalidate_box(self):
        """Drop the cached oriented box after any geometry change."""
        self._obox = None

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # No longer dropped on a MOVE: since `_content_points` answers in
            # this group's own frame, the box does not depend on where the group
            # sits, so a move cannot stale it. Dropping it here was also one
            # step WRONG -- `ItemPositionChange` fires BEFORE the move commits,
            # so anything that rebuilt the cache during it (a repaint, a
            # boundingRect query) stored the box for the position the group was
            # LEAVING. Measured at Gate 3: the reported box lagged the group by
            # exactly one drag step.
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
        """Extreme points of the members -- wall endpoints and furnishing
        footprint corners -- ALL IN THIS GROUP'S OWN FRAME.

        THE FRAME MATTERS AND USED TO BE MIXED (Gate 3). A wall child
        contributes `ch.p1`/`ch.p2`, which are the wall's own geometry and so
        already in the group's frame; a furnishing used to contribute
        `ch.mapToScene(...)`, which is SCENE. The two agree only while the group
        sits at the origin. Move the group and the furnishing's points shift by
        the group's translation while the wall's do not -- and since
        `boundingRect()` is read in the item's own frame, that translation is
        then applied a SECOND time, so the box's leading edge ran at ~2x the
        mouse while its trailing edge stood still. `mapToParent` is the same
        query asked in the frame the answer is used in."""
        pts = []
        for ch in self.childItems():
            if isinstance(ch, WallItem):
                pts += [ch.p1, ch.p2]
            elif isinstance(ch, FurnishingItem):
                r = QRectF(-ch.w / 2, -ch.d / 2, ch.w, ch.d)
                pts += [ch.mapToParent(r.topLeft()),
                        ch.mapToParent(r.topRight()),
                        ch.mapToParent(r.bottomRight()),
                        ch.mapToParent(r.bottomLeft())]
        return pts

    def _oriented_box(self) -> tuple:
        """(localRect, centre): an axis-aligned rectangle in the frame
        rotated by -self._angle that tightly contains the content.  Drawn
        back through +self._angle it becomes an oriented box hugging the
        members at the group's current orientation.

        Cached per geometry change (defect 14): boundingRect(), _handle() and
        paint() each call this, so it ran ~3x per repaint. The cache is dropped
        by _invalidate_box() on move/rotate/adopt/dissolve/bake."""
        if self._obox is not None:
            return self._obox
        pts = self._content_points()
        if not pts:
            b = self.childrenBoundingRect()
            self._obox = (b, b.center())
            return self._obox
        cx = sum(p.x() for p in pts) / len(pts)
        cy = sum(p.y() for p in pts) / len(pts)
        center = QPointF(cx, cy)
        local = [self._rot_transform(center, -self._angle).map(p) for p in pts]
        xs = [p.x() for p in local]
        ys = [p.y() for p in local]
        m = EXTERIOR_T                    # margin for wall half-thickness
        rect = QRectF(min(xs) - m, min(ys) - m,
                      max(xs) - min(xs) + 2 * m, max(ys) - min(ys) + 2 * m)
        self._obox = (rect, center)
        return self._obox

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
                if isinstance(it, RoomItem) and room_owns_walls(group_walls, it):
                    self._snap_rooms.append(
                        (it, [QPointF(c) for c in (it.corners or [])],
                         QPointF(it.anchor), QPainterPath(it.path)))
        # the corners this gesture will move, resolved ONCE (defect 22): the
        # rotation then relocates each of them per event instead of assigning
        # coordinates to wall ends and rebuilding room corner lists beside them
        self._snap_corners = self._corner_records(
            group_walls, [r for r, *_ in self._snap_rooms])

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
        self._obox = None                     # angle + children changed
        # the whole geometric move: relocate the corners, and every wall end and
        # room outline edge holding them comes along (defect 22)
        self._apply_corner_records(self._snap_corners, tr)
        for w, _p1_0, _p2_0 in self._snap_walls:
            w.rebuild()                       # re-syncs its openings too
        for f, pos_0, rot_0 in self._snap_furn:
            f.setPos(tr.map(pos_0))
            f.setRotation((rot_0 + theta) % 360.0)
        for room, corners_0, anchor_0, path_0 in self._snap_rooms:
            room.prepareGeometryChange()
            room.anchor = tr.map(anchor_0)
            if not corners_0:                 # outline-less: the path IS the region
                room.set_region(tr.map(path_0), room.area_sqft, None)
            room.update()
        self.update()

    def _finish_rotation(self):
        self._snap_walls = self._snap_furn = self._snap_rooms = []
        self._snap_corners = []
        self.prepareGeometryChange()
        self._obox = None
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
        self._obox = None                 # membership changed

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

    def _corner_records(self, group_walls, carry_rooms):
        """Every CORNER the group's geometry holds, as
        `[start_point, vertex, [(wall, attr)...], [outline_edge...]]`.

        DEFECT 22, P3.5-followup, and the one mechanism both a bake and a
        rotation now move through. Both used to assign new COORDINATES to every
        member wall end -- split-on-write, by P3.1's ruling, so each end came
        away on a fresh `Vertex` -- and then rebuild each carried room's corner
        LIST separately, which minted a third set. The two agreed numerically
        and shared nothing, so afterwards a room's outline no longer held its
        walls' corners and a later wall drag left the room behind (measured:
        140/140 shared corners -> 0/140). `refresh_rooms` used to re-bind and
        re-share after every group move, which is why deferring the conversion
        to P4.5 was safe until P3.5 deleted it.

        DEFORM-TO-FOLLOW (P4.5, ruled): A CORNER AN OUTSIDE WALL ALSO HOLDS IS
        NO LONGER SPLIT. It used to be, before anything moved, so that "the
        group moves, whatever is outside it does not" -- and the justification
        given was that relocating it wholesale would drag a non-member's end,
        "the very wiring the `group() is None` guards exist to prevent". **That
        justification expired**: P4.5 retired all four of those guards, and
        `duplicate_wall` died with them, so a group now holds the REAL walls
        rather than copies. A corner the group and a room both hold is the
        NORMAL case, not an outsider to protect from.

        So the corner relocates whole, and everything on it comes along: an
        outside wall end because it IS that corner, and every room whose
        outline holds it -- gathered SCENE-WIDE BY IDENTITY, the same question
        `_rooms_holding` and `_DragVertex.ends` ask. Gathering only the rooms
        the group fully owns is what stranded the clipped room (defect 23): its
        walls walked out from under a region that had no record telling it to
        follow.

        A carried room whose outline corner is on NO member wall (sharing was
        already broken -- a legacy import, or a group move from before this fix)
        gets a record of its own, so it is carried rather than left behind."""
        sc = self.scene()
        held, ends = {}, []
        for w in group_walls:
            for a in ("p1", "p2"):
                v = w.end_vertex(a)
                held.setdefault(id(v), v)
                ends.append((w, a, v))
        # AN OUTSIDE WALL'S END ON ONE OF THESE CORNERS COMES ALONG, and this
        # is the same scan that used to SPLIT it off -- inverted rather than
        # deleted, which is the shape of the whole ruling. Without it the
        # outsider keeps the old vertex while everything else moves, so the
        # network tears open at that corner: measured on the clipped band as
        # `unwelded_ends` rising 0 -> 1 after a bake that was otherwise clean.
        # The room half of this gather widened at P4.5; the wall half is the
        # same question and had been left behind (found by Align to grid
        # hitting it first, on a three-room row).
        for it in (sc.items() if sc is not None else ()):
            if isinstance(it, WallItem) and it not in group_walls:
                for a in ("p1", "p2"):
                    v = it.end_vertex(a)
                    if id(v) in held:
                        ends.append((it, a, v))
        recs = {}
        for k, v in held.items():
            recs[k] = [QPointF(v.point()), v, [], []]
        for w, a, v in ends:
            recs[id(v)][2].append((w, a))
        # A FULLY-OWNED room moves RIGIDLY, so a corner of its outline that no
        # member wall holds still gets a record -- that is the legacy-sharing
        # repair, and it is what makes the room travel whole.
        for r in carry_rooms:
            for e in r.outline:
                rec = recs.get(id(e.v))
                if rec is None:
                    rec = recs[id(e.v)] = [QPointF(e.v.point()), e.v, [], []]
                rec[3].append(e)
        # A room the group only PARTLY holds must DEFORM, not travel: it follows
        # exactly the corners that moved and keeps the ones that did not. So it
        # attaches to EXISTING records only -- minting one for an unheld corner
        # is what would drag the whole room, which is the rigid case above and
        # the opposite error to the stranding this fixes.
        owned = {id(r) for r in carry_rooms}
        for r in self._rooms_holding(sc, set(held)):
            if id(r) in owned:
                continue
            for e in r.outline:
                rec = recs.get(id(e.v))
                if rec is not None:
                    rec[3].append(e)
        return list(recs.values())

    # THE GATHER LIVES IN `rooms.py` NOW (P4.5). It was defined here first,
    # then wanted by Align to grid and Distribute, and one concept with three
    # implementations is F2's disease -- so `rooms_holding` is the single
    # definition and this stays only as the name `bake` and the rotation
    # already call.
    _rooms_holding = staticmethod(rooms_holding)

    @staticmethod
    def _apply_corner_records(recs, tr):
        """Relocate every corner to `tr` of where it STARTED, and rebind every
        wall end and outline edge on it.  Mapping from the start point rather
        than from the current one is what lets a rotation re-apply this on each
        mouse event without accumulating drift."""
        for rec in recs:
            v = rec[1].relocated_to(tr.map(rec[0]))
            rec[1] = v
            for w, a in rec[2]:
                w.set_end_vertex(a, v)
            for e in rec[3]:
                e.v = v

    def bake(self):
        """Fold the group's current translation into its members and
        reset the group to (0, 0).  A room whose perimeter is fully walled
        by the group rides along -- its anchor (label) and region shift too
        -- even when an extra coincident wall (e.g. a shared party wall the
        room edge was copied from) also touches its boundary.

        The move is a VERTEX move (defect 22): the members' corners relocate,
        and their walls and the carried rooms' outlines follow because they are
        holding those corners -- the same thing a wall drag does, and the only
        shape that keeps P3.5's by-construction property across a bake."""
        d = self.pos()
        if abs(d.x()) < 1e-9 and abs(d.y()) < 1e-9:
            return
        sc = self.scene()
        moved_rooms = []
        group_walls = {ch for ch in self.childItems()
                       if isinstance(ch, WallItem)}
        if sc is not None and group_walls:
            for it in sc.items():
                if isinstance(it, RoomItem) and room_owns_walls(group_walls, it):
                    moved_rooms.append(it)
        self.prepareGeometryChange()
        self._obox = None                 # child coords change below
        tr = QTransform.fromTranslate(d.x(), d.y())
        recs = self._corner_records(group_walls, moved_rooms)
        # WHICH ROOMS CAN THIS DEFORM (P4.5 §2a). Not `moved_rooms`: a room the
        # group fully owns moves RIGIDLY and cannot cross itself. The exposure
        # is the CLIPPED room -- it holds some corners this bake moves and some
        # it does not, so its shape changes. Gathered by vertex identity (the
        # defect-30 gather), and gathered BEFORE the move, because
        # `relocated_to` hands back a new object.
        watched = self._rooms_holding(sc, {id(rec[1]) for rec in recs})
        self._apply_corner_records(recs, tr)
        for ch in self.childItems():
            # a member WALL needs nothing here: its ends moved with the corner,
            # and the `rebuild_all_walls` below rebuilds it. Rebuilding it here
            # too costs a cascading neighbour query per member -- measured at
            # 9x on the 64-room harness, which is how it was caught.
            if not isinstance(ch, WallItem):
                ch.setPos(ch.pos().x() + d.x(), ch.pos().y() + d.y())
        for r in moved_rooms:
            r.prepareGeometryChange()
            r.anchor = QPointF(r.anchor.x() + d.x(), r.anchor.y() + d.y())
            if not r.outline:             # outline-less: the stored path IS it
                r.set_region(tr.map(r.path), r.area_sqft, None)
            r.update()
        self.setPos(0.0, 0.0)
        rebuild_all_walls(sc)
        # ...and say so AT THE GESTURE if the deform crossed an outline. The
        # document check (I5b) is deep-only and would not speak until the save
        # refused to write -- learning at the wrong moment, defect 17's disease.
        report_self_intersections(sc, watched)

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

    # far below every floor's z-band (P4.2: ghost floors sit on negative
    # bands of 100k) -- a BACKDROP is beneath everything, always
    Z = -1_000_000_000.0
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


# -- HIT RESOLUTION ------------------------------------------------------------
#
# RULED 2026-08-08 at A1b (D53): TYPE PRIORITY, NOT Z-ORDER.
#
# Qt resolves hits by z, so z-order has been carrying TWO jobs at once: painting
# (walls crisp above the room fill -- a real requirement, WALL_Z's comment says
# so) and hit resolution (which item did I mean). Those two agree only while a
# room's `shape()` is small. Widen it to the region and they diverge
# permanently, and NO z assignment satisfies both -- which is exactly what the
# furnishing exposure was telling us: `FurnishingItem` sits at z 3 under a
# room's 4, deliberately (`items.py:58`, "under the room fill/label and walls"),
# because the fill is translucent and furnishings are MEANT to show through it.
# Raising rooms to win hits would either bury furnishings or un-tint them.
#
# `raise_to_front` settles it. It sets a touched room to `_z_top * 10 + band`
# while furnishings stay at 3, so any scheme whose hit outcomes depend on z is
# ONE ROOM INTERACTION away from breaking. Painting and hitting are separated
# here instead: **z stays a painting concern and does not change.**
#
# THE RULE IS NOT NEW. `macro.py`'s `_cmd_select` has preferred "an editable
# item (furnishing / wall / group) over a room, whose label can sit on top of
# what you meant to grab" since long before this record -- written for this
# exact reason and quietly correct all along. This GENERALISES that rule rather
# than building a second answer beside it, and `_cmd_select` calls this now.
# Two priority rules in one codebase would drift, and the drift presents as
# "sometimes clicking picks the wrong thing", which is close to undebuggable.

#: PRIORITY RUNS FROM MOST SPECIFIC TO LEAST SPECIFIC. That is the whole rule,
#: stated as the principle rather than as a list with exceptions -- ruled
#: 2026-08-08, after a first draft said "a room is always last" and two entries
#: promptly needed explaining away. They do not: both follow from specificity.
#:
#:  * `OpeningItem` outranks `WallItem` because THE CONTAINING THING MUST NEVER
#:    OUTRANK THE CONTAINED THING. A door is a Qt CHILD of its wall and both are
#:    returned for the same point, so the door is the more specific answer. Not
#:    a deviation -- the same rule, one level deeper. (It wins by OPENING_Z 6.0 >
#:    WALL_Z 5.0 today; ranking it keeps that outcome once z stops deciding.)
#:  * `ReferenceImageItem` ranks below `RoomItem` for the same reason and not as
#:    a carve-out: a full-canvas TRACING BACKDROP is LESS specific than a room,
#:    not more. The proof is what the opposite would do -- above rooms, no room
#:    would be selectable while an image was loaded, inverting the very defect
#:    D53 closes.
#:
#: A room still comes last among the things a user ordinarily selects, which is
#: the property D53 needed; it just is not the axiom.
#:
#: `RoofEndMarkerItem` outranks EVERYTHING for the same contained-thing reason
#: `OpeningItem` outranks `WallItem` above -- it is a Qt CHILD of its `RoofItem`
#: (roofs.py), so the two are routinely returned for the same point and the
#: marker is the more specific answer. `RoofItem` itself ranks with `WallItem`
#: (both are the plan's own structural lines, above the room fill they sit
#: over) -- added here, not left to fall through to the "unknown" tail rank,
#: because that tail rank is BELOW `RoomItem`: a named room's own fill was
#: silently winning every right-click meant for a ridge drawn over it, since
#: an unlisted type's rank (`len(HIT_PRIORITY)`) is worse than `RoomItem`'s.
#: Caught from Patrick's own report, not a test.
HIT_PRIORITY = (RoofEndMarkerItem, RoofGripItem, OpeningItem, FurnishingItem,
                WallItem,
                RoofItem, GroupItem, RoomItem, ReferenceImageItem)


def _hit_rank(item) -> int:
    for i, cls in enumerate(HIT_PRIORITY):
        if isinstance(item, cls):
            return i
    return len(HIT_PRIORITY)          # unknown types sort last, ahead of nothing


def hit_candidates(scene, scene_pos, transform=None):
    """Every item under `scene_pos`, in the scene's own stacking order.

    Built on `items(pos)`, NOT `itemAt(pos)`: `itemAt` returns only the topmost,
    which is the z-decides-everything answer this module exists to stop using.
    """
    if scene is None:
        return []
    if transform is None:
        return list(scene.items(scene_pos))
    return list(scene.items(scene_pos, Qt.ItemSelectionMode.IntersectsItemShape,
                            Qt.SortOrder.DescendingOrder, transform))


def best_by_priority(candidates):
    """THE resolver. Choose by TYPE PRIORITY, breaking ties by the order given.

    Callers supply their own candidate list because the right way to ASK
    differs -- and getting that wrong cost a debugging session here. A view
    must ask the way Qt does, with a 1x1 pixel RECT (`QGraphicsView.items`),
    because a viewport coordinate is an integer and round-tripping it through
    `mapToScene` lands a fraction off a wall's edge; a macro asks with an exact
    scene point, which is what its coordinates mean. The PRIORITY RULE is the
    part that must not be duplicated, so it lives here alone and both call it.

    Ties keep the first candidate, so two walls under one point still resolve
    by stacking order: only the CROSS-TYPE question is taken away from z.
    """
    best, best_rank = None, len(HIT_PRIORITY) + 1
    for it in candidates:
        r = _hit_rank(it)
        if r < best_rank:
            best, best_rank = it, r
    return best


def hit_target(scene, scene_pos, transform=None):
    """The item meant at an exact SCENE point (the macro's question).

    This makes `raise_to_front` irrelevant to selection BY CONSTRUCTION rather
    than by careful ordering, which is the property being bought.
    """
    return best_by_priority(hit_candidates(scene, scene_pos, transform))


def on_blank_canvas(scene, scene_pos, transform=None) -> bool:
    """True when there is NO item of any type under `scene_pos` -- rooms included.

    A separate predicate on purpose. The four `itemAt(...) is None` sites were
    not testing the wrong thing; `itemAt(...) is None` had been STANDING IN for
    a question nobody ever wrote down. This writes it down, so widening a room's
    shape changes what those sites see only where that is intended.
    """
    return not hit_candidates(scene, scene_pos, transform)
