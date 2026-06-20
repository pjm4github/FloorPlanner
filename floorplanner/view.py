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
        if q is None:
            q = nearest_wall_body_point(self.scene(), sp, tol)
        return q if q is not None else wall_snap(sp)

    def _align_to_wall(self, exclude, pt, horizontal) -> QPointF:
        """Snap the drawn endpoint's free coordinate (x when horizontal, y
        when vertical) to the projected line of a nearby OPEN-ENDED wall (a
        dangling end), so the new wall lines up with it while staying H/V.
        Fully-joined walls are ignored, and any gap is left as-is -- nothing
        auto-grows; the user extends to meet by hand."""
        sc = self.scene()
        if sc is None:
            return pt
        tol = max(JOIN_TOL, 16.0 / max(self.transform().m11(), 1e-6))
        base = pt.x() if horizontal else pt.y()
        best, bestd = None, tol
        for w in sc.items():
            if not isinstance(w, WallItem) or w is exclude or w.is_open:
                continue
            for end in (w.p1, w.p2):
                if not wall_endpoint_open(sc, end, ignore=(w, exclude)):
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
            # Ctrl+drag on empty space: rubber-band that ADDS to the
            # selection set (Ctrl+click on items toggles membership)
            if (tool == TOOL_SELECT
                    and e.modifiers() & Qt.KeyboardModifier.ControlModifier
                    and self.itemAt(pos) is None):
                self._rubber_origin = pos
                if self._rubber is None:
                    self._rubber = QRubberBand(
                        QRubberBand.Shape.Rectangle, self.viewport())
                self._rubber.setGeometry(QRect(pos, QSize(1, 1)))
                self._rubber.show()
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
            # SELECT tool: pan when pressing empty space
            if self.itemAt(pos) is None:
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
            self._temp_wall.p2 = self._wall_end_point(self._temp_wall, sp,
                                                      e.modifiers())
            self._temp_wall.rebuild()
            e.accept()
            return

        super().mouseMoveEvent(e)

    def select_in_rect(self, area: QRectF):
        """Additively select everything the rubber band fully encloses.

        Only items wholly inside `area` are selected, so a room can be
        picked out by its walls while the longer party walls that run past
        it stay unselected.  When a room's interior is enclosed but an edge
        is carried by such a longer wall, a fresh copy of that edge is
        synthesized (and selected) so the room comes through as a complete,
        movable loop -- the original long wall is left untouched."""
        scene = self.scene()
        if scene is None:
            return
        # walls / furnishings / groups that sit entirely within the band
        for it in scene.items(area, Qt.ItemSelectionMode.IntersectsItemShape):
            top = it.group() or it         # grouped items select the group
            if (isinstance(top, (WallItem, FurnishingItem, GroupItem))
                    and item_fully_inside(top, area)):
                top.setSelected(True)
        # rooms whose perimeter is enclosed: select the room and make sure
        # every edge is a selected wall (duplicating shared/longer walls)
        rooms = [it for it in scene.items() if isinstance(it, RoomItem)]
        made_edges = False
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
                else:
                    synthesize_room_edge(scene, a, b).setSelected(True)
                    made_edges = True
        if made_edges:
            rebuild_all_walls(scene)

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
            self._rubber.hide()
            self._rubber_origin = None
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
                # it reads as one connected structure, not a loose segment
                coalesce_wall(self.scene(), w)
                if w.scene() is not None:
                    w.join_endpoints(rebuild=False)
                rebuild_all_walls(self.scene())
            e.accept()
            return

        super().mouseReleaseEvent(e)

    def contextMenuEvent(self, e):
        # Room Name tool + blank canvas -> offer to paste the copied room
        if self.win.tool == TOOL_ROOM and self.itemAt(e.pos()) is None:
            menu = QMenu(self)
            a_paste = menu.addAction("Paste room")
            a_paste.setEnabled(self.win.room_clipboard is not None)
            if menu.exec(e.globalPos()) is a_paste:
                self.win.paste_room(grid_snap(self.mapToScene(e.pos())))
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
        op = OpeningItem(wall, kind, code.strip(), s)
        wall.openings.append(op)
        rebuild_all_walls(self.scene())   # coincident walls open for the new one
        if kind == "door":
            self.win.last_door = code.strip()
        else:
            self.win.last_window = code.strip()
        if self.win._recorder is not None:
            # record the size the user typed so replay needs no dialog
            self.win._recorder.on_opening(kind, sp, code.strip())
