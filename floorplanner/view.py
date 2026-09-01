"""The plan canvas (PlanView) and the furnishing palette widgets."""
import math

from PyQt6 import sip  # noqa: F401
from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import *  # noqa: F401

from floorplanner.config import *  # noqa: F401
from floorplanner.geometry import *  # noqa: F401
from floorplanner.catalog import *  # noqa: F401
from floorplanner.walls import *  # noqa: F401
from floorplanner.rooms import *  # noqa: F401
from floorplanner.rooms import _wall_endpoints_match  # star skips underscores
from floorplanner.roofs import RoofEndMarkerItem, RoofItem
from floorplanner.items import *  # noqa: F401


class FurnishingList(QListWidget):
    """One palette section: an icon grid of furnishing symbols; drag a
    symbol onto the plan to place it at true scale."""

    def __init__(self, specs, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(QSize(52, 52))
        self.setGridSize(QSize(88, 92))
        self.setMovement(QListWidget.Movement.Static)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setDragEnabled(True)
        self.setWordWrap(True)
        self.setSpacing(2)
        for spec in specs:
            it = QListWidgetItem(self._icon(spec), spec["name"])
            it.setData(Qt.ItemDataRole.UserRole, spec["id"])
            it.setToolTip(self._tooltip(spec))
            self.addItem(it)

    @staticmethod
    def _tooltip(spec) -> str:
        t = (f'{spec["name"]} — {fmt_in(spec["width_in"])} × '
             f'{fmt_in(spec["depth_in"])}  ({spec["category"]})')
        price = float(spec.get("price", 0.0) or 0.0)
        if price > 0:
            t += f'  ·  ${price:,.0f}'
        return t

    def refresh_tooltips(self):
        """Re-read each item's price from the live catalog (after an AI
        price update) and rebuild its tooltip."""
        for row in range(self.count()):
            it = self.item(row)
            spec = furnishing_spec(it.data(Qt.ItemDataRole.UserRole))
            if spec is not None:
                it.setToolTip(self._tooltip(spec))

    @staticmethod
    def _icon(spec) -> QIcon:
        pm = QPixmap(64, 64)
        pm.fill(Qt.GlobalColor.transparent)
        r = furnishing_renderer(spec["id"])
        if r is not None:
            w, d = spec["width_in"], spec["depth_in"]
            s = 56.0 / max(w, d)
            p = QPainter(pm)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            r.render(p, QRectF((64 - w * s) / 2, (64 - d * s) / 2,
                               w * s, d * s))
            p.end()
        return QIcon(pm)

    def startDrag(self, actions):
        it = self.currentItem()
        kind = it.data(Qt.ItemDataRole.UserRole) if it else None
        if not kind:
            return
        mime = QMimeData()
        mime.setData(FURN_MIME, str(kind).encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        pm = it.icon().pixmap(48, 48)
        drag.setPixmap(pm)
        drag.setHotSpot(QPoint(pm.width() // 2, pm.height() // 2))
        drag.exec(Qt.DropAction.CopyAction)


class FurnishingPalette(QToolBox):
    """Right-hand palette: one expandable tab per room group from
    assets/furnishings/groups.json (a furnishing may appear in several
    groups).  Clicking a tab expands that section; "All" — the whole
    library — is the section open by default."""

    def __init__(self, parent=None):
        super().__init__(parent)
        all_index = 0
        for i, group in enumerate(furnishing_groups()):
            lst = FurnishingList(group["specs"], self)
            self.addItem(lst, f'{group["name"]}  ({len(group["specs"])})')
            if group["name"].lower() == "all":
                all_index = i
        self.setCurrentIndex(all_index)

    def refresh_prices(self):
        """Refresh every section's tooltips after an AI price update."""
        for i in range(self.count()):
            w = self.widget(i)
            if isinstance(w, FurnishingList):
                w.refresh_tooltips()


class PlanView(QGraphicsView):
    def __init__(self, scene, win):
        super().__init__(scene)
        self.win = win
        self.setAcceptDrops(True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setMouseTracking(True)
        self._panning = False
        self._pan_last = None
        self._temp_wall = None
        self._temp_roof = None            # ridge being dragged, or None
        self._roof_awaiting_eaves = None  # ridge fixed, awaiting the eaves pick
        self._last_scene = None           # last mouse position (paste target)
        self._rubber = None               # Ctrl+drag selection rubber band
        self._rubber_origin = None
        self._img_mode = None             # None | "calibrate" | "crop"
        self._img_ref = None              # the ReferenceImageItem being edited
        self._calib_pts = []              # collected calibration points
        self._crop_start = None           # crop rubber-band start (scene)
        # coalesce a wheel burst into one zoom/repaint -- high-res wheels and
        # trackpads emit dozens of wheelEvents per physical notch; with a full
        # viewport repaint per event a large plan stalls for seconds.
        self._zoom_accum = 0
        self._zoom_timer = QTimer(self)
        self._zoom_timer.setSingleShot(True)
        self._zoom_timer.setInterval(16)  # ~one 60 Hz frame
        self._zoom_timer.timeout.connect(self._apply_zoom)

    # -- reference-image (PNG import) modes ----------------------------------
    def start_image_calibrate(self, item):
        self._img_mode, self._img_ref, self._calib_pts = "calibrate", item, []
        self.win.status("Calibrate: click two points a known distance apart "
                        "on the image (Esc to cancel).")

    def start_image_crop(self, item):
        self._img_mode, self._img_ref = "crop", item
        self._crop_start = None
        self.win.status("Crop: drag a rectangle over the area to keep "
                        "(Esc to cancel).")

    def _end_image_mode(self):
        self._img_mode = self._img_ref = self._crop_start = None
        self._calib_pts = []
        if self._rubber is not None:
            self._rubber.hide()

    # -- zoom ------------------------------------------------------------------
    def wheelEvent(self, e):
        delta = e.angleDelta().y()
        if delta == 0:
            return
        # accumulate; apply once on the next frame so a burst of events is a
        # single scale() + repaint instead of one full repaint per event.
        self._zoom_accum += delta
        if not self._zoom_timer.isActive():
            self._zoom_timer.start()
        e.accept()

    def _apply_zoom(self):
        delta, self._zoom_accum = self._zoom_accum, 0
        if delta == 0:
            return
        factor = 1.0015 ** delta
        cur = self.transform().m11()
        target = max(0.03, min(40.0, cur * factor))
        if target == cur:
            return
        self.scale(target / cur, target / cur)

    # -- background grid --------------------------------------------------------
    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor(252, 252, 250))
        lod = max(self.transform().m11(), 1e-6)

        def vgrid(step, pen):
            painter.setPen(pen)
            x = math.floor(rect.left() / step) * step
            while x <= rect.right():
                painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
                x += step
            y = math.floor(rect.top() / step) * step
            while y <= rect.bottom():
                painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
                y += step

        if lod > 0.22:
            vgrid(GRID_MINOR, QPen(QColor(234, 237, 241), 0))
        if lod > 0.05:
            vgrid(GRID_MAJOR, QPen(QColor(206, 213, 221), 0))

        # canvas outline (size from File > Settings…; default 100' x 70')
        painter.setPen(QPen(QColor(150, 158, 170), 0, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(canvas_rect())

        # foot labels along the major grid
        if lod > 0.08:
            f = QFont()
            f.setPixelSize(max(2, int(11.0 / lod)))
            painter.setFont(f)
            painter.setPen(QPen(QColor(160, 166, 176), 0))
            x = math.floor(rect.left() / GRID_MAJOR) * GRID_MAJOR
            ytop = rect.top() + 14.0 / lod
            while x <= rect.right():
                painter.drawText(QPointF(x + 2.0 / lod, ytop), f"{int(x // 12)}'")
                x += GRID_MAJOR
            y = math.floor(rect.top() / GRID_MAJOR) * GRID_MAJOR
            xleft = rect.left() + 3.0 / lod
            while y <= rect.bottom():
                painter.drawText(QPointF(xleft, y - 2.0 / lod), f"{int(y // 12)}'")
                y += GRID_MAJOR

    # -- snapping helpers ---------------------------------------------------------
    def _snap_start(self, sp: QPointF) -> QPointF:
        tol = max(6.0, 10.0 / max(self.transform().m11(), 1e-6))
        q = nearest_wall_endpoint(self.scene(), sp, tol)
        if q is not None:
            return q
        hit = nearest_wall_body(self.scene(), sp, tol)
        if hit is not None:
            return self._grid_snap_t_junction(*hit)
        return wall_snap(sp)

    @staticmethod
    def _grid_snap_t_junction(wall, q: QPointF) -> QPointF:
        """0070-ruling.md sec3/sec5: `q` is the raw geometric projection of
        the click onto `wall`'s centreline -- exactly on the host's line,
        but never rounded to the grid, so a fresh wall started against an
        existing wall's body (a T-junction) silently inherited whatever
        fraction the click happened to land on and no later operation could
        remove it (this was the FIRST bad step the bisect named, identical
        with weld/coalesce on or off -- the seed is here, not in
        normalisation). Snap the position ALONG the host to the grid,
        leaving the coordinate ACROSS it untouched so the point stays
        exactly on the host's line. Only for an axis-aligned host: a
        diagonal wall has no single grid position to round the point onto,
        so it is returned unchanged, same as before this fix."""
        dx, dy = wall.p2.x() - wall.p1.x(), wall.p2.y() - wall.p1.y()
        if abs(dy) < 1e-6:                          # horizontal host
            return QPointF(wall_snap_len(q.x()), q.y())
        if abs(dx) < 1e-6:                          # vertical host
            return QPointF(q.x(), wall_snap_len(q.y()))
        return q

    def _align_to_wall(self, exclude, pt, horizontal) -> QPointF:
        """Snap the drawn endpoint's free coordinate (x when horizontal, y
        when vertical) to the projected line of a nearby OPEN-ENDED wall (a
        dangling end), so the new wall lines up with it while staying H/V.
        Fully-joined walls are ignored, and any gap is left as-is -- nothing
        auto-grows; the user extends to meet by hand."""
        sc = self.scene()
        if sc is None:
            return pt
        active = active_floor()
        tol = max(JOIN_TOL, 16.0 / max(self.transform().m11(), 1e-6))
        base = pt.x() if horizontal else pt.y()
        best, bestd = None, tol
        for w in sc.items():
            if not isinstance(w, WallItem) or w is exclude or w.floor != active:
                continue                          # align only to the active floor
            for end in (w.p1, w.p2):
                if not wall_endpoint_open(sc, end, ignore=(w, exclude), floor=active):
                    continue
                c = end.x() if horizontal else end.y()
                d = abs(base - c)
                if d < bestd:
                    bestd, best = d, c
        if best is None:
            return pt
        return QPointF(best, pt.y()) if horizontal else QPointF(pt.x(), best)

    def _wall_end_point(self, wall, sp, mods) -> QPointF:
        dx, dy = sp.x() - wall.p1.x(), sp.y() - wall.p1.y()
        if math.hypot(dx, dy) < 1e-6:
            return QPointF(wall.p1)
        if mods & Qt.KeyboardModifier.ShiftModifier:
            return wall_snap(QPointF(sp))     # free angle
        if mods & Qt.KeyboardModifier.ControlModifier:
            # fixed angular increments off the anchor (SETTINGS['rotate_snap_deg'],
            # default 15deg) -- same formula WallItem._angle_snapped_target uses
            # for a re-angle DRAG on an existing wall's end; this is the DRAW
            # gesture's own copy, anchored at wall.p1 instead of self._anchor.
            step = math.radians(max(1.0, SETTINGS.get("rotate_snap_deg", 15.0)))
            ang = round(math.atan2(dy, dx) / step) * step
            length = max(MIN_WALL_LEN, wall_snap_len(math.hypot(dx, dy)))
            return QPointF(wall.p1.x() + math.cos(ang) * length,
                           wall.p1.y() + math.sin(ang) * length)
        ang = math.atan2(dy, dx)              # orthogonal from the anchor
        a = round(ang / (math.pi / 2)) * (math.pi / 2)
        horizontal = abs(math.cos(a)) > 0.5
        proj = wall_snap_len(dx * math.cos(a) + dy * math.sin(a))
        pt = QPointF(wall.p1.x() + math.cos(a) * proj,
                     wall.p1.y() + math.sin(a) * proj)
        # align the endpoint with the nearest orthogonal wall, staying H/V
        return self._align_to_wall(wall, pt, horizontal)

    def _make_named_room(self, sp, name, res):
        """Create a named room at sp from a detection result; the Room tool
        is one-shot, so it reverts to Select unless it was Ctrl-set sticky."""
        path, area, corners = res
        name = unique_room_name(self.scene(), name)
        room = RoomItem(name, grid_snap(sp), path, area, corners=corners)
        self.scene().addItem(room)
        bind_room_walls(self.scene(), room)   # fuse the enclosing walls in
        room.raise_to_front()
        if self.win._recorder is not None:
            # record the name the user typed so replay needs no dialog
            self.win._recorder.on_room(name, room.anchor)
        if not self.win._room_sticky:
            self.win.set_tool(TOOL_SELECT)
        return room

    # -- mouse / tools ----------------------------------------------------------
    # -- hit resolution (D53) --------------------------------------------------
    # Two questions, written down rather than inferred from `itemAt(...) is
    # None`. That expression had been STANDING IN for both, and they are not
    # the same: "which item did the user mean" and "is there anything here at
    # all" diverge the moment a room's shape covers its region.
    def hit(self, pos):
        """The item the user MEANT at a VIEWPORT point, by type priority.

        Candidates come from `QGraphicsView.items(pos)`, which is how Qt's own
        `itemAt` asks: a 1x1 PIXEL RECT, not an exact point. That matters and
        was measured -- a viewport coordinate is an integer, so mapping it to
        the scene and testing an exact point lands a fraction off a wall's edge
        and reports blank canvas over a wall. Five wall-drag tests failed on
        exactly that before this used the view's own query.
        """
        return best_by_priority(self.items(pos))

    def blank(self, pos) -> bool:
        """True when NO item of any type is under a VIEWPORT point."""
        return not self.items(pos)

    def _band_may_start(self, pos) -> bool:
        """May a Ctrl+drag start a selection band here?

        A REFUTED PREMISE, not a compromise -- and it is recorded that way
        because the two read differently to whoever changes this next.

        The ruling was: "an explicit modifier gesture should never depend on
        what happens to sit under the press point." Sound in general. FALSE
        HERE, and the premise it rests on is what fails: **CTRL IS ALREADY AN
        ITEM-LEVEL MODIFIER IN THIS APPLICATION** -- it is the label-only nudge
        on a room's label, and it drives the wall corner-drags. An unconditional
        Ctrl band eats gestures older than this record, because the press never
        reaches those items at all. Six tests said so before any reasoning did:
        `test_room_label_ctrl_drag_nudges_label`,
        `test_a_dragged_end_near_a_jamb_snaps_to_it`,
        `test_dragging_an_end_into_a_doorway_names_the_doorway_at_release`,
        `test_closing_gap_refuses_and_relocks`, and two macro replays.

        WHAT THE RULING WAS FOR IS KEPT WHOLE: the band was blocked by
        `itemAt(pos) is None`, so once a room's shape covered its region you
        could never start one from inside a room. That is exactly what this
        allows. The band starts on blank canvas and over a room's REGION; it
        does not start on a room's LABEL (the room's own handle) or on any
        other item, whose ctrl gestures are older than this record.
        """
        target = self.hit(pos)
        if target is None:
            return True
        if isinstance(target, RoomItem):
            item_pt = target.mapFromScene(self.mapToScene(pos))
            return not target._label_rect().contains(item_pt)
        return False

    def mousePressEvent(self, e):
        pos = e.position().toPoint()
        sp = self.mapToScene(pos)
        tool = self.win.tool

        if self._img_mode is not None \
                and e.button() == Qt.MouseButton.LeftButton:
            if self._img_mode == "calibrate":
                self._calib_pts.append(QPointF(sp))
                if len(self._calib_pts) == 2:
                    self.win._finish_calibrate(
                        self._img_ref, self._calib_pts)
                    self._end_image_mode()
                e.accept()
                return
            if self._img_mode == "crop":
                self._crop_start = QPointF(sp)
                e.accept()
                return

        if e.button() == Qt.MouseButton.MiddleButton:
            self._panning, self._pan_last = True, pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            e.accept()
            return

        if e.button() == Qt.MouseButton.LeftButton:
            # Ctrl+drag: rubber-band that ADDS to the selection set.
            #
            # UNCONDITIONAL since D53 (ruled 2026-08-08). It used to require
            # `itemAt(pos) is None`, so an explicit modifier gesture depended
            # on what happened to sit under the press point -- incidental all
            # along, and untenable once a room's shape covers its region, since
            # the band could then never be started from inside a room.
            #
            # THE CTRL-CLICK HALF IS SETTLED AT RELEASE, not here, because this
            # ruling and D53(b) ("ctrl-click toggles membership") would
            # otherwise contradict: starting a band on every ctrl-press means
            # the press never reaches the item. A band that never grew past a
            # few pixels WAS a click, and `mouseReleaseEvent` treats it as one.
            if (tool == TOOL_SELECT
                    and e.modifiers() & Qt.KeyboardModifier.ControlModifier
                    and self._band_may_start(pos)):
                # ARM the band; do not SHOW one yet. The widget appears on
                # the first move (`mouseMoveEvent`), for two reasons:
                #   * a ctrl-CLICK must not flash a one-pixel rubber band, and
                #     under D53 every ctrl-press arms this gesture, so clicks
                #     now come through here constantly;
                #   * `QRubberBand.show()` on an OFFSCREEN viewport takes the
                #     process down -- measured 2026-08-08, and PRE-EXISTING:
                #     a ctrl-click on empty canvas crashes identically at
                #     `a1172be`, which is why no headless test has ever covered
                #     this gesture. Deferring the show is what makes the
                #     ctrl-click half testable at all.
                self._rubber_origin = pos
                e.accept()
                return
            if tool in (TOOL_WALL_EXT, TOOL_WALL_INT):
                p = self._snap_start(sp)
                wt = "exterior" if tool == TOOL_WALL_EXT else "interior"
                w = WallItem(p, p, wt)
                w._drawing = True
                self.scene().addItem(w)
                self._temp_wall = w
                e.accept()
                return
            if tool == TOOL_DOOR:
                self._place_opening(sp, "door")
                e.accept()
                return
            if tool == TOOL_WINDOW:
                self._place_opening(sp, "window")
                e.accept()
                return
            if tool == TOOL_ROOM:
                res = detect_room(self.scene(), sp)
                if res is None:
                    QMessageBox.information(
                        self, "Room",
                        "Click inside an area completely enclosed by walls.")
                else:
                    name, ok = QInputDialog.getText(self, "Room name", "Name:")
                    if ok and name.strip():
                        self._make_named_room(sp, name.strip(), res)
                e.accept()
                return
            if tool == TOOL_ROOF_RIDGE:
                if self._roof_awaiting_eaves is not None:
                    # STAGE 2: this press is the eaves pick, not a new ridge
                    # (0139-ruling.md sec1/sec3: "pick a ridge line, pick an
                    # eaves line"). Same wall lookup as _place_opening.
                    wall = None
                    for it in self.scene().items(sp):
                        if isinstance(it, WallItem):
                            wall = it
                            break
                    if wall is None:
                        self.win.status(
                            "Roof ridge: click the eaves wall this roof "
                            "spans over (Esc cancels).")
                        e.accept()
                        return
                    item = self._roof_awaiting_eaves
                    self._roof_awaiting_eaves = None
                    self.win.finish_roof_ridge(item, wall)
                    e.accept()
                    return
                # A press on an EXISTING roof's own marker or ridge is not
                # "start a new ridge here" -- it is the marker drag / the
                # ridge's own selection (R2b: the marker stays draggable
                # while the ridge tool is the sticky active tool, same as
                # a fresh sketch). Falls through to Qt's normal item
                # dispatch, which is what lets RoofEndMarkerItem's own
                # mousePressEvent -- and RoofItem's own selection -- run.
                for it in self.scene().items(sp):
                    if isinstance(it, (RoofEndMarkerItem, RoofItem)):
                        break
                else:
                    # STAGE 1: start the ridge, same anchor snap a wall gets
                    p = self._snap_start(sp)
                    item = RoofItem(p, p)
                    self.scene().addItem(item)
                    self._temp_roof = item
                    e.accept()
                    return
            # SELECT tool: pan when pressing empty space.
            #
            # D53: `on_blank_canvas`, not `itemAt(...) is None`. Now that a
            # room's shape covers its region, a left-drag pan started INSIDE a
            # room goes away -- ruled, and no reach is lost, because
            # MIDDLE-MOUSE DRAG PANS ANYWHERE UNCONDITIONALLY and is checked
            # first (see the MiddleButton branch above). Keep it that way: it
            # is the pan that does not depend on what is under the cursor, and
            # it is what makes this branch safe to narrow.
            if self.blank(pos):
                self._panning, self._pan_last = True, pos
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.scene().clearSelection()
                e.accept()
                return

        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        pos = e.position().toPoint()
        sp = self.mapToScene(pos)
        self._last_scene = QPointF(sp)
        self.win.show_coords(sp)

        # the selection band becomes a real widget only once the press has
        # actually MOVED -- see mousePressEvent for why it is not shown there
        if self._rubber_origin is not None:
            if self._rubber is None:
                self._rubber = QRubberBand(QRubberBand.Shape.Rectangle,
                                           self.viewport())
            self._rubber.setGeometry(
                QRect(self._rubber_origin, pos).normalized())
            self._rubber.show()

        if self._img_mode == "crop" and self._crop_start is not None:
            origin = self.mapFromScene(self._crop_start)
            if self._rubber is None:
                self._rubber = QRubberBand(QRubberBand.Shape.Rectangle,
                                           self.viewport())
            self._rubber.setGeometry(QRect(origin, pos).normalized())
            self._rubber.show()
            e.accept()
            return

        if self._rubber_origin is not None:
            self._rubber.setGeometry(
                QRect(self._rubber_origin, pos).normalized())
            e.accept()
            return

        if self._panning and self._pan_last is not None:
            d = pos - self._pan_last
            self._pan_last = pos
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - d.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - d.y())
            e.accept()
            return

        if self._temp_wall is not None:
            # RELOCATE, do not assign. This was the last `p1`/`p2` writer in
            # `floorplanner/` (the P3.1 split-on-write shim's final call site),
            # and it fired on EVERY mouse-move of the draw gesture -- a fresh
            # `Vertex` per event for an end nobody else was holding yet.
            # Nothing observable changes here, because the drawn end is not
            # shared until release welds it; what changes is that the shim now
            # has no production caller at all, which is what lets the setters
            # go. `relocated_to` carries the identity, so a moving end is the
            # same corner throughout the gesture rather than a new one 60
            # times a second.
            w = self._temp_wall
            w.set_end_vertex("p2", w.end_vertex("p2").relocated_to(
                self._wall_end_point(w, sp, e.modifiers())))
            w.rebuild()
            e.accept()
            return

        if self._temp_roof is not None:
            # SAME snap math as a wall drag (0139-ruling.md sec1: "the ridge
            # tool calls that machinery") -- `_wall_end_point` only reads
            # `wall.p1`, so a RoofItem duck-types as the `wall` it expects.
            item = self._temp_roof
            item.set_ridge(item.p1, self._wall_end_point(item, sp, e.modifiers()))
            e.accept()
            return

        super().mouseMoveEvent(e)

    def select_in_rect(self, area: QRectF):
        """Additively select everything the rubber band fully encloses.

        Only items wholly inside `area` are selected, so a room can be picked
        out by its walls while the longer party walls that run past it stay
        unselected.

        SELECTION CREATES NOTHING (defect 10, P0.5). This docstring used to
        promise the opposite -- that an edge carried by a longer party wall was
        SYNTHESIZED as a fresh copy "so the room comes through as a complete,
        movable loop" -- and that synthesis was removed three phases ago,
        because a selection gesture that mutates the document is the worse
        defect. The prose survived the code, which made it a promise the
        function had stopped keeping.

        IT MATTERS BECAUSE IT DESCRIBES THE MISSING MECHANISM BEHIND A REPORTED
        SYMPTOM. A band that clips any of a room's walls leaves that room
        without a complete selected loop, `group_selected` duplicates the rest,
        `room_owns_walls` is then correctly false, and the room is NOT carried
        by the move -- it stays put as a dashed outline while the walls walk
        away. That is defect 23, it is expected until P4.5 decides what a group
        IS, and the workaround is exact: band the WHOLE plan. Measured on
        `planc1TestV5.json` -- a band at 100% coverage strands zero rooms, and
        every band short of it strands the rooms it clipped."""
        scene = self.scene()
        if scene is None:
            return
        # walls / furnishings / groups that sit entirely within the band
        for it in scene.items(area, Qt.ItemSelectionMode.IntersectsItemShape):
            top = it.group() or it         # grouped items select the group
            if (isinstance(top, (WallItem, FurnishingItem, GroupItem))
                    and item_fully_inside(top, area)):
                top.setSelected(True)
        # rooms whose perimeter is enclosed: select the room, and select the
        # walls that back its edges -- WITHOUT creating any (see the docstring;
        # the old comment here said "duplicating shared/longer walls", which
        # has not been true since P0.5)
        rooms = [it for it in scene.items() if isinstance(it, RoomItem)]
        for room in rooms:
            if not room.corners or not item_fully_inside(room, area):
                continue
            room.setSelected(True)
            n = len(room.corners)
            for i in range(n):
                a, b = room.corners[i], room.corners[(i + 1) % n]
                w = next((x for x in scene.items()
                          if isinstance(x, WallItem)
                          and _wall_endpoints_match(x, a, b)), None)
                if w is not None:
                    w.setSelected(True)      # the room's own edge wall
                # selection is READ-ONLY (defect 10): an edge backed only by a
                # longer/party wall is left unselected, not duplicated. Nothing
                # is created, so no rebuild is needed.

    def mouseReleaseEvent(self, e):
        if (self._img_mode == "crop" and self._crop_start is not None
                and e.button() == Qt.MouseButton.LeftButton):
            rect = QRectF(self._crop_start,
                          self.mapToScene(e.position().toPoint())).normalized()
            ref = self._img_ref
            self._end_image_mode()
            if ref is not None and rect.width() > 1 and rect.height() > 1:
                ref.crop_to_scene_rect(rect)
                self.win.status("Cropped the image.")
            e.accept()
            return

        if (self._rubber_origin is not None
                and e.button() == Qt.MouseButton.LeftButton):
            rect = QRect(self._rubber_origin,
                         e.position().toPoint()).normalized()
            if self._rubber is not None:
                self._rubber.hide()
            origin, self._rubber_origin = self._rubber_origin, None
            # D53: the band is now started on EVERY ctrl-press, so a press that
            # never moved is a ctrl-CLICK and must toggle membership -- D53(b),
            # which the unconditional band would otherwise swallow. Threshold
            # rather than exact equality: a real click jitters by a pixel.
            if rect.width() <= CLICK_SLOP and rect.height() <= CLICK_SLOP:
                target = self.hit(origin)
                if target is not None and target.flags() &                         QGraphicsItem.GraphicsItemFlag.ItemIsSelectable:
                    target.setSelected(not target.isSelected())
                e.accept()
                return
            area = self.mapToScene(rect).boundingRect()
            self.select_in_rect(area)
            e.accept()
            return

        if self._panning and e.button() in (Qt.MouseButton.LeftButton,
                                            Qt.MouseButton.MiddleButton):
            self._panning, self._pan_last = False, None
            self.unsetCursor()
            e.accept()
            return

        if self._temp_wall is not None and e.button() == Qt.MouseButton.LeftButton:
            w, self._temp_wall = self._temp_wall, None
            w._drawing = False
            if w.length() < MIN_WALL_LEN:
                self.scene().removeItem(w)
            else:
                # an overlapping same-type wall coalesces into one; then the
                # drawn end welds onto whatever wall it lands on (T/L joint) so
                # it reads as one connected structure, not a loose segment.
                # The weld pass is auto_weld's (P4.3): with it off -- or under
                # shuffle -- the wall lands exactly where drawn, nothing snaps,
                # and the doorway report stays quiet (an unwelded end is the
                # chosen state, not a tear).
                merge_wall(self.scene(), w)
                if w.scene() is not None and editing_enabled("auto_weld"):
                    # ruling 2, tier 1: a jamb within the join tolerance is
                    # the junction the user meant -- snap to it; else the end
                    # lands as drawn and tier 2 reports (P4.1b's message)
                    snap_end_to_doorway_jamb(self.scene(), w)
                    weld_wall_ends(self.scene(), w, rebuild=False)
                    # defect 25 (P4.1b): a drawn end that came to rest inside
                    # a doorway reports at the gesture -- the walk would only
                    # say "torn network" later, blaming a tear, not this draw
                    report_doorway_landings(self.scene(), w, "drawing a wall")
                rebuild_all_walls(self.scene())
            e.accept()
            return

        if self._temp_roof is not None and e.button() == Qt.MouseButton.LeftButton:
            item, self._temp_roof = self._temp_roof, None
            if item.length() < MIN_WALL_LEN:
                self.scene().removeItem(item)
                self.win.status("Roof ridge too short; try again.")
            else:
                self._roof_awaiting_eaves = item
                self.win.status(
                    "Roof ridge set. Click the eaves wall this roof spans "
                    "over (Esc cancels).")
            e.accept()
            return

        super().mouseReleaseEvent(e)

    def contextMenuEvent(self, e):
        # Room Name tool + BLANK CANVAS -> paste the copied room, or type a
        # new CONCEPT room right here (P4.4: the dialog is on this menu and
        # on Rooms > New concept room…, per the ruling)
        #
        # A RIGHT-CLICK RESOLVES THROUGH THE SAME TYPE-PRIORITY RESOLVER AS A
        # LEFT-CLICK, and each type answers with its OWN menu; the blank-canvas
        # menus below fire only on `blank()`. Ruled 2026-08-08.
        #
        # The previous clause fired these on "no item OR a room", written when
        # a room menu was believed not to exist. It does: `RoomItem.
        # contextMenuEvent` is 68 lines and offers Extract room / Join room.
        # The clause SHADOWED it -- measured, and reported by hand rather than
        # by any test. It is deleted, not tuned.
        #
        # THE FLOOR POPUP LOSES ITS REGION ROUTE, and that is accepted: with
        # the region in a room's shape, a right-click there gives the ROOM
        # menu, so the popup is blank-canvas only. NO REACH IS LOST, and the
        # justification is measured rather than assumed (the same standard the
        # left-drag pan's retirement was held to, where middle-mouse drag was
        # the surviving route). The popup offers exactly ONE operation --
        # switch floor -- and `Floors > Select…` opens THE IDENTICAL POPUP via
        # `select_floor_popup()`, on Ctrl+F, with `Edit this floor` per floor
        # as a direct switch besides.
        if self.win.tool == TOOL_ROOM and self.blank(e.pos()):
            menu = QMenu(self)
            a_paste = menu.addAction("Paste room")
            a_paste.setEnabled(self.win.room_clipboard is not None)
            a_concept = menu.addAction("New concept room…")
            menu.addSeparator()
            a_3d = menu.addAction("3D view…")
            chosen = menu.exec(e.globalPos())
            at = self.mapToScene(e.pos())
            if chosen is a_paste:
                self.win.paste_room(grid_snap(at))
            elif chosen is a_concept:
                self.win.new_concept_room(at=grid_snap(at))
            elif chosen is a_3d:
                self.win.show_3d_view()
            e.accept()
            return
        if self.blank(e.pos()):
            # BLANK CANVAS ONLY (D53) -> the floor popup (P4.2 spec):
            # default pre-highlighted so ENTER selects it, DOWN walks the
            # floors, ESC cancels. Recorded as a PUP line; the resulting
            # switch appends its deterministic `# ^F "name"` comment.
            self.win.select_floor_popup(e.globalPos(), scene_menu=True)
            e.accept()
            return
        super().contextMenuEvent(e)

    # -- furnishing drag & drop ---------------------------------------------------
    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(FURN_MIME):
            e.acceptProposedAction()
            return
        super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasFormat(FURN_MIME):
            e.acceptProposedAction()
            return
        super().dragMoveEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasFormat(FURN_MIME):
            kind = bytes(e.mimeData().data(FURN_MIME)).decode("utf-8")
            sp = grid_snap(self.mapToScene(e.position().toPoint()))
            item = make_furnishing(kind, sp)
            self.scene().addItem(item)
            if self.win._recorder is not None:
                self.win._recorder.on_place(kind, sp)
            self.win.status(f"Placed {item.name} ({fmt_ftin(item.w)} × "
                            f"{fmt_ftin(item.d)}). Drag to move; select and "
                            f"drag the round handle to rotate (Ctrl = 15° "
                            f"steps).")
            e.acceptProposedAction()
            return
        super().dropEvent(e)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            if self._img_mode is not None:
                self._end_image_mode()
                self.win.status("Cancelled.")
                return
            self.cancel_temp()
            super().keyPressEvent(e)
            return
        nudges = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0),
                  Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}
        if e.key() in nudges:
            dx, dy = nudges[e.key()]
            fine = bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier)
            if self.win.nudge_selected(dx, dy, fine):
                e.accept()
                return
        super().keyPressEvent(e)

    def cancel_temp(self):
        if self._temp_wall is not None:
            self.scene().removeItem(self._temp_wall)
            self._temp_wall = None
        if self._temp_roof is not None:
            self.scene().removeItem(self._temp_roof)
            self._temp_roof = None
        if self._roof_awaiting_eaves is not None:
            self.scene().removeItem(self._roof_awaiting_eaves)
            self._roof_awaiting_eaves = None

    # -- door / window placement ---------------------------------------------------
    def _place_opening(self, sp: QPointF, kind: str):
        wall = None
        for it in self.scene().items(sp):
            if isinstance(it, WallItem):
                wall = it
                break
            if isinstance(it, OpeningItem):
                wall = it.wall
                break
        if wall is None:
            self.win.status(f"Click on a wall to place a {kind}.")
            return

        default = self.win.last_door if kind == "door" else self.win.last_window
        code, ok = QInputDialog.getText(
            self, f"{kind.title()} size",
            'Size WWHH (width inches, height inches):', text=default)
        if not ok:
            return
        try:
            w, _h = parse_wwhh(code)
        except ValueError as ex:
            QMessageBox.warning(self, "Invalid size", str(ex))
            return
        if w > wall.length():
            QMessageBox.warning(self, "Too wide",
                                f"A {fmt_ftin(w)} opening will not fit in a "
                                f"{fmt_ftin(wall.length())} wall.")
            return

        s = round(wall.s_of(sp))
        s = min(max(s, w / 2), wall.length() - w / 2)
        # never stack two openings on top of each other (on this wall or a
        # coincident party wall): refuse if one already overlaps this span
        ctr = wall.point_at(s)
        for ow in [wall, *coincident_walls(self.scene(), wall)]:
            for ex in ow.openings:
                if QLineF(ow.point_at(ex.s), ctr).length() < (w + ex.width) / 2:
                    QMessageBox.warning(
                        self, "Opening in the way",
                        "There is already a door or window here (on this wall "
                        "or the wall coincident with it). Move or resize that "
                        "one instead.")
                    return
        # A GATE IS A DOOR IN A LANDSCAPE WALL (Phase 5). Invariant I7 has
        # required this since P0.7 -- "only gates are allowed" in a railing,
        # fence, hedge or retaining wall -- and nothing could produce one, so
        # the rule guarded a state the editor could not reach.
        #
        # DERIVED, NOT CHOSEN: the user places a door and gets a gate because
        # of what they placed it IN. That adds no mode, no tool and nothing to
        # learn, and it makes I7 true by construction rather than by a check
        # the user can fail. A separate gate tool would let someone put a gate
        # in a bedroom wall and then be told off for it.
        if kind == "door" and wall.wall_type in LANDSCAPE_TYPES:
            kind = "gate"
        op = OpeningItem(wall, kind, code.strip(), s)
        wall.openings.append(op)
        rebuild_all_walls(self.scene())   # coincident walls open for the new one
        if kind in ("door", "gate"):
            self.win.last_door = code.strip()
        else:
            self.win.last_window = code.strip()
        if self.win._recorder is not None:
            # record the size the user typed so replay needs no dialog
            self.win._recorder.on_opening(kind, sp, code.strip())
