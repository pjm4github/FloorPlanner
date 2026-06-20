"""The application main window: menus, toolbars, the scene<->model
serialization bridge, IO, and all edit orchestration."""
import csv
import json
import os

from PyQt6 import sip  # noqa: F401
from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import *  # noqa: F401

try:
    from PyQt6.QtSvg import QSvgGenerator
except ImportError:
    QSvgGenerator = None

from floorplanner.config import *  # noqa: F401
from floorplanner.geometry import *  # noqa: F401
from floorplanner.catalog import *  # noqa: F401
from floorplanner.walls import *  # noqa: F401
from floorplanner.walls import _coalesce_all_impl  # star skips underscores
from floorplanner.rooms import *  # noqa: F401
from floorplanner.items import *  # noqa: F401
from floorplanner.model import (  # serialization bridge (aliased)
    DEFAULT_FLOOR, FILE_VERSION, Floor, Furnishing, Opening as OpeningModel,
    Project, Room as RoomModel, Wall as WallModel,
)
from floorplanner.dialogs import *  # noqa: F401
from floorplanner.view import *  # noqa: F401
from floorplanner.macro import *  # noqa: F401


class MainWindow(QMainWindow):
    HINTS = {
        TOOL_SELECT: ("Select: drag wall BODY to slide it sideways (Ctrl = "
                      "free move) \u2022 drag wall ENDS to lengthen/shorten "
                      "(Shift = free angle) \u2022 drag furnishings from the "
                      "right palette onto the plan \u2022 Ctrl+click toggles "
                      "items in the selection set, Ctrl+drag rubber-bands "
                      "more in, Ctrl+G groups, Ctrl+X/C/V cut-copy-paste "
                      "\u2022 drag empty space to pan \u2022 wheel zoom"),
        TOOL_WALL_EXT: "Exterior wall (6\"): click-drag to draw. Orthogonal "
                       "from the anchor (hold Shift for free angle). Esc "
                       "cancels.",
        TOOL_WALL_INT: "Interior wall (4 1/2\"): click-drag to draw. "
                       "Orthogonal from the anchor (hold Shift for free "
                       "angle). Esc cancels.",
        TOOL_DOOR: "Door: click on a wall, then enter the WWHH size "
                   "(e.g. 3280 = 32\" x 80\").",
        TOOL_WINDOW: "Window: click on a wall, then enter the WWHH size "
                     "(e.g. 3648 = 36\" x 48\").",
        TOOL_ROOM: "Room name: click inside an enclosed area to name a room, "
                   "then the tool reverts to Select. Ctrl+click the tool to "
                   "keep it active for several rooms.",
    }

    def __init__(self):
        super().__init__()
        self.tool = TOOL_SELECT
        self._room_sticky = False        # one-shot Room tool unless Ctrl-set
        self.last_door = "3280"
        self.last_window = "3648"
        self.current_path = None
        self.room_clipboard = None
        self.item_clipboard = None        # cut/copied walls + furnishings
        self._recorder = None             # active MacroRecorderDialog (or None)
        self._recorder_dialog = None      # the (reused) recorder window
        # floors: the authoritative roster (model Floor dataclasses) lives here;
        # config's runtime cache mirrors it via _sync_floor_state.  active_floor
        # and show_other_floors are VIEW state (kept out of serialize/undo).
        # Set before _build_menus so the Floors menu can build from it.
        self.floors = [Floor(DEFAULT_FLOOR)]
        self.active_floor = DEFAULT_FLOOR
        self.show_other_floors = False
        self._update_title()

        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)
        self._apply_canvas()
        self.view = PlanView(self.scene, self)
        self.setCentralWidget(self.view)

        self._build_toolbar()
        self._build_menus()
        self._build_palette()

        self.coord_label = QLabel("")
        self.statusBar().addPermanentWidget(self.coord_label)
        # active-floor indicator: click to pop a quick floor-switch menu
        self.floor_label = QLabel("Floor: default")
        self.floor_label.setToolTip("Active floor — click to switch")
        self.floor_label.setStyleSheet("QLabel { padding: 0 6px; }")
        self.floor_label.mousePressEvent = lambda e: self._popup_floor_menu()
        self.statusBar().addPermanentWidget(self.floor_label)
        self.status(self.HINTS[TOOL_SELECT])

        # keep the toolbar totals current as rooms are added/resized/removed
        self.scene.changed.connect(self._update_totals)
        self._update_totals()

        self._z_top = 0                  # running max-z for bring-to-front
        self._sync_floor_state()         # populate the Floors menu + status label

        # undo / redo: full-document snapshots captured after each change
        # settles (debounced), so every canvas operation is reversible
        self._undo_stack = []
        self._redo_stack = []
        self._restoring = False
        self._committed_state = self.serialize()
        self._saved_state = self._committed_state   # last on-disk/new baseline
        self._dirty_timer = QTimer(self)
        self._dirty_timer.setSingleShot(True)
        self._dirty_timer.setInterval(180)
        self._dirty_timer.timeout.connect(self._commit_if_changed)
        self.scene.changed.connect(self._mark_dirty)
        self._update_undo_actions()

        self.resize(1280, 860)
        self.view.scale(1.1, 1.1)
        self.view.centerOn(QPointF(24 * FOOT, 16 * FOOT))

    # -- UI ------------------------------------------------------------------
    def _build_toolbar(self):
        tb = self.addToolBar("Tools")
        tb.setMovable(False)
        tb.setIconSize(QSize(26, 26))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        group = QActionGroup(self)
        group.setExclusive(True)
        self._tool_actions = {}

        defs = [
            (TOOL_SELECT, "Select", "S", "select"),
            (TOOL_WALL_EXT, "Exterior Wall", "E", "wall_ext"),
            (TOOL_WALL_INT, "Interior Wall", "I", "wall_int"),
            (TOOL_DOOR, "Door", "D", "door"),
            (TOOL_WINDOW, "Window", "W", "window"),
            (TOOL_ROOM, "Room Name", "R", "room"),
        ]
        for tool, label, key, icon in defs:
            a = QAction(tool_icon(icon), label, self)
            a.setCheckable(True)
            a.setShortcut(key)
            a.setToolTip(f"{label}  [{key}]")
            a.triggered.connect(lambda _=False, t=tool: self.set_tool(t))
            group.addAction(a)
            tb.addAction(a)
            self._tool_actions[tool] = a
        self._tool_actions[TOOL_SELECT].setChecked(True)

        tb.addSeparator()
        a_del = QAction(tool_icon("delete"), "Delete", self)
        a_del.setShortcuts([QKeySequence(Qt.Key.Key_Delete),
                            QKeySequence(Qt.Key.Key_Backspace)])
        a_del.setToolTip("Delete selection  [Del]")
        a_del.triggered.connect(self.delete_selected)
        tb.addAction(a_del)

        a_fit = QAction(tool_icon("zoomfit"), "Zoom Fit", self)
        a_fit.setShortcut("F")
        a_fit.setToolTip("Zoom to fit the plan  [F]")
        a_fit.triggered.connect(self.zoom_fit)
        tb.addAction(a_fit)

        tb.addSeparator()
        self.a_undo = QAction(tool_icon("undo"), "Undo", self)
        self.a_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.a_undo.setToolTip("Undo  [Ctrl+Z]")
        self.a_undo.triggered.connect(self.undo)
        self.a_undo.setEnabled(False)
        tb.addAction(self.a_undo)
        self.a_redo = QAction(tool_icon("redo"), "Redo", self)
        self.a_redo.setShortcuts([QKeySequence.StandardKey.Redo,
                                  QKeySequence("Ctrl+Y")])
        self.a_redo.setToolTip("Redo  [Ctrl+Y]")
        self.a_redo.triggered.connect(self.redo)
        self.a_redo.setEnabled(False)
        tb.addAction(self.a_redo)

        tb.addSeparator()
        a_rec = QAction(tool_icon("record"), "Record macro", self)
        a_rec.setToolTip("Record / debug a macro…")
        a_rec.triggered.connect(self.open_macro_recorder)
        tb.addAction(a_rec)

        spacer = QWidget()                       # push the totals to the right
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding,
                             QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)
        self.totals_label = QLabel("Totals:  Cost-$0K   Sq. Feet-0")
        self.totals_label.setStyleSheet("padding: 0 12px; font-weight: 600;")
        self.totals_label.setToolTip(
            "Building total: the floor area of every room with “Include "
            "in total square footage” ticked (right-click a room name "
            "→ Properties…), priced at the cost per square foot set "
            "in File ▸ Settings….  Cost is shown in thousands of "
            "dollars.")
        tb.addWidget(self.totals_label)

        a_esc = QAction("select-esc", self)
        a_esc.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        a_esc.triggered.connect(lambda: self.set_tool(TOOL_SELECT))
        self.addAction(a_esc)

    def _build_palette(self):
        dock = QDockWidget("Furnishings", self)
        dock.setObjectName("furnishings")
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.furn_palette = FurnishingPalette(self)
        dock.setWidget(self.furn_palette)
        dock.setMinimumWidth(200)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _build_menus(self):
        m_file = self.menuBar().addMenu("&File")
        a_new = QAction("&New plan", self)
        a_new.setShortcut(QKeySequence.StandardKey.New)
        a_new.triggered.connect(self.new_plan)
        m_file.addAction(a_new)
        a_open = QAction("&Open…", self)
        a_open.setShortcut(QKeySequence.StandardKey.Open)
        a_open.triggered.connect(self.open_plan)
        m_file.addAction(a_open)
        a_imp = QAction("&Import rooms from CSV…", self)
        a_imp.triggered.connect(self.import_rooms_csv)
        m_file.addAction(a_imp)
        a_img = QAction("Import from i&mage (PNG)…", self)
        a_img.triggered.connect(lambda: self.start_image_import())
        m_file.addAction(a_img)
        a_exp = QAction("&Export rooms to CSV…", self)
        a_exp.triggered.connect(self.export_rooms_csv)
        m_file.addAction(a_exp)
        m_file.addSeparator()
        a_save = QAction("&Save", self)
        a_save.setShortcut(QKeySequence.StandardKey.Save)
        a_save.triggered.connect(self.save_plan)
        m_file.addAction(a_save)
        a_saveas = QAction("Save &As…", self)
        a_saveas.setShortcut(QKeySequence.StandardKey.SaveAs)
        a_saveas.triggered.connect(self.save_plan_as)
        m_file.addAction(a_saveas)
        m_edit = self.menuBar().addMenu("&Edit")
        m_edit.addAction(self.a_undo)    # same actions as the toolbar buttons
        m_edit.addAction(self.a_redo)
        m_edit.addSeparator()
        for label, keys, slot in [
                ("Cu&t", QKeySequence.StandardKey.Cut, self.cut_selected),
                ("&Copy", QKeySequence.StandardKey.Copy, self.copy_selected),
                ("&Paste", QKeySequence.StandardKey.Paste,
                 self.paste_clipboard)]:
            a = QAction(label, self)
            a.setShortcut(QKeySequence(keys))
            a.triggered.connect(slot)
            m_edit.addAction(a)
        m_edit.addSeparator()
        self.a_group = QAction("&Group", self)
        self.a_group.setShortcut(QKeySequence("Ctrl+G"))
        self.a_group.triggered.connect(self.group_selected)
        m_edit.addAction(self.a_group)
        self.a_ungroup = QAction("&Ungroup", self)
        self.a_ungroup.setShortcut(QKeySequence("Ctrl+Shift+G"))
        self.a_ungroup.triggered.connect(self.ungroup_selected)
        m_edit.addAction(self.a_ungroup)
        m_edit.addSeparator()
        a_coalesce = QAction("Coalesce all walls now", self)
        a_coalesce.triggered.connect(self.coalesce_all_now)
        m_edit.addAction(a_coalesce)

        m_rooms = self.menuBar().addMenu("&Rooms")
        self._room_op_actions = []
        for label, op in [("&Combine (union)", "combine"),
                          ("&Fragment into pieces", "fragment"),
                          ("&Subtract (1st − 2nd)", "subtract"),
                          ("&Intersect (overlap only)", "intersect")]:
            a = QAction(label, self)
            a.triggered.connect(lambda _checked, o=op: self.room_boolean(o))
            m_rooms.addAction(a)
            self._room_op_actions.append(a)
        m_rooms.addSeparator()
        self.a_align = QAction("&Align to grid", self)
        self.a_align.triggered.connect(self.align_rooms_to_grid)
        m_rooms.addAction(self.a_align)
        self._distribute_actions = []
        for label, horiz in [("Distribute &horizontally", True),
                             ("Distribute &vertically", False)]:
            a = QAction(label, self)
            a.triggered.connect(lambda _c, h=horiz: self.distribute_rooms(h))
            m_rooms.addAction(a)
            self._distribute_actions.append(a)
        a_refresh = QAction("&Refresh rooms (drop unwalled)", self)
        a_refresh.triggered.connect(self.refresh_rooms_cmd)
        m_rooms.addAction(a_refresh)

        m_inv = self.menuBar().addMenu("In&ventory")
        for label, slot in [("&House (structure)…", self.inventory_house),
                            ("&Interior furnishings…",
                             self.inventory_interior),
                            ("&Yard items…", self.inventory_yard),
                            ("&Total…", self.inventory_total)]:
            a = QAction(label, self)
            a.triggered.connect(slot)
            m_inv.addAction(a)

        m_ai = self.menuBar().addMenu("&AI")
        a_prices = QAction("Update furnishing &prices…", self)
        a_prices.triggered.connect(self.update_furnishing_prices)
        m_ai.addAction(a_prices)

        m_macro = self.menuBar().addMenu("&Macro")
        a_record = QAction("&Record / Debug…", self)
        a_record.setToolTip("Open the non-modal macro recorder")
        a_record.triggered.connect(self.open_macro_recorder)
        m_macro.addAction(a_record)

        self.m_floors = self.menuBar().addMenu("&Floors")
        self._rebuild_floor_menu()

        m_help = self.menuBar().addMenu("&Help")
        a_about = QAction(f"&About {APP_NAME}…", self)
        a_about.triggered.connect(self.show_about)
        m_help.addAction(a_about)

        self.scene.selectionChanged.connect(self._update_edit_actions)
        self._update_edit_actions()

        m_file.addSeparator()
        a_set = QAction("Se&ttings…", self)
        a_set.triggered.connect(self.edit_settings)
        m_file.addAction(a_set)
        m_file.addSeparator()
        a_quit = QAction("&Quit", self)
        a_quit.setShortcut(QKeySequence.StandardKey.Quit)
        a_quit.triggered.connect(self.close)
        m_file.addAction(a_quit)

    # -- actions ----------------------------------------------------------------
    def _update_totals(self, *args):
        """Refresh the toolbar Totals label: floor area of the rooms flagged
        for inclusion, and that area priced at the cost per square foot."""
        if not hasattr(self, "totals_label"):
            return
        sqft = sum(it.area_sqft for it in self.scene.items()
                   if isinstance(it, RoomItem)
                   and it.properties.get("include_sqft", True))
        cost_k = sqft * float(SETTINGS.get("cost_per_sqft", 0.0)) / 1000.0
        self.totals_label.setText(
            f"Totals:  Cost-${cost_k:,.0f}K   Sq. Feet-{sqft:,.0f}")

    def edit_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        dlg.apply()
        self._apply_canvas()
        self._update_totals()            # cost per sq ft may have changed
        c = canvas_rect()
        self.status(f'Wall snap {SETTINGS["wall_snap_in"]:g}" · rotation '
                    f'snap {SETTINGS["rotate_snap_deg"]:g}° · canvas '
                    f"{fmt_ftin(c.width())} × {fmt_ftin(c.height())} · "
                    f'${SETTINGS["cost_per_sqft"]:g}/sq ft.')

    def update_furnishing_prices(self):
        """AI ▸ Update furnishing prices…: fetch current purchase prices for
        the whole catalog from the chosen AI system and store them in the
        manifest, refreshing palette tooltips and any placed items."""
        dlg = AIPricingDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.result_prices:
            return
        n = apply_furnishing_prices(dlg.result_prices)
        if hasattr(self, "furn_palette"):
            self.furn_palette.refresh_prices()
        for it in self.scene.items():
            if isinstance(it, FurnishingItem):
                spec = furnishing_spec(it.kind)
                if spec is not None:
                    it.price = float(spec.get("price", 0.0) or 0.0)
                    tip = (f"{it.name} — {fmt_ftin(it.w)} × {fmt_ftin(it.d)}")
                    if it.price > 0:
                        tip += f"  ·  ${it.price:,.0f}"
                    it.setToolTip(tip)
        self.status(f"Updated purchase prices for {n} furnishing(s) "
                    "from the AI.")

    def show_about(self):
        AboutDialog(self).exec()

    # -- inventories ----------------------------------------------------------
    def _show_inventory(self, title, headers, rows, note=None):
        InventoryDialog(title, headers, rows, parent=self, note=note).exec()

    def inventory_house(self):
        rows, sqft = house_inventory_rows(self.scene)
        self._show_inventory(
            "Inventory — House (structure)", HOUSE_INV_HEADERS, rows,
            note=f"Rooms, doors, windows and walls.  "
                 f"Total floor area {sqft:,.1f} sq ft.")

    def inventory_interior(self):
        interior, _ = classify_furnishings(self.scene)
        rows, qty, cost = furnishing_inventory_rows(interior)
        self._show_inventory(
            "Inventory — Interior furnishings", FURN_INV_HEADERS, rows,
            note=f"{qty} furnishing(s) inside rooms.  Prices come from the "
                 "AI ▸ Update furnishing prices… tool.")

    def inventory_yard(self):
        _, yard = classify_furnishings(self.scene)
        rows, qty, cost = furnishing_inventory_rows(yard)
        self._show_inventory(
            "Inventory — Yard items", FURN_INV_HEADERS, rows,
            note=f"{qty} item(s) outside any room (vehicles, yard "
                 "equipment, patio furniture…).")

    def inventory_total(self):
        rows = total_inventory_rows(self.scene)
        self._show_inventory(
            "Inventory — Total", TOTAL_INV_HEADERS, rows,
            note="Whole-plan summary.  Building cost uses File ▸ Settings ▸ "
                 "cost per sq ft; furnishing prices come from the AI menu.")

    def _apply_canvas(self):
        """Resize the scene around the configured canvas and refresh."""
        m = 30 * FOOT
        self.scene.setSceneRect(canvas_rect().adjusted(-m, -m, m, m))
        self.scene.update()
        self._update_title()

    def set_tool(self, tool):
        self.tool = tool
        self.view.cancel_temp()
        self._tool_actions[tool].setChecked(True)
        self.status(self.HINTS[tool])
        if tool == TOOL_ROOM:
            # Ctrl held while choosing the tool keeps it active (sticky);
            # otherwise it reverts to Select after one room is named
            self._room_sticky = bool(QApplication.keyboardModifiers()
                                     & Qt.KeyboardModifier.ControlModifier)
        if self._recorder is not None:
            self._recorder.on_tool(tool)

    def open_macro_recorder(self):
        """Open (or re-show) the non-modal macro recorder / debugger window."""
        if self._recorder_dialog is None:
            self._recorder_dialog = MacroRecorderDialog(self)
        self._recorder_dialog.show()
        self._recorder_dialog.raise_()
        self._recorder_dialog.activateWindow()

    def status(self, msg):
        self.statusBar().showMessage(msg)

    def show_coords(self, sp: QPointF):
        self.coord_label.setText(
            f"x {fmt_ftin(sp.x())}   y {fmt_ftin(sp.y())}")

    def delete_selected(self):
        for it in list(self.scene.selectedItems()):
            if it.scene() is None:
                continue
            if isinstance(it, OpeningItem):
                wall = it.wall
                if it in wall.openings:
                    wall.openings.remove(it)
                self.scene.removeItem(it)
                if wall.scene() is not None:
                    wall.rebuild()
            elif isinstance(it, WallItem):
                # fracture at room perimeters so deleting a shared/through wall
                # never breaks an adjacent room open
                fracture_delete_wall(self.scene, it, settle=False)
            elif isinstance(it, (RoomItem, FurnishingItem, GroupItem)):
                self.scene.removeItem(it)
        rebuild_all_walls(self.scene)

    # -- group / ungroup / cut / copy / paste -------------------------------------
    def _update_edit_actions(self):
        """Group is enabled once the selection set holds 2+ groupable
        items; Ungroup once it holds a group; room ops once exactly two
        rooms are selected.  Also tracks click order for subtract."""
        sel = self.scene.selectedItems()
        selset = set(sel)
        order = getattr(self, "_sel_order", [])
        order = [it for it in order if it in selset]
        for it in sel:
            if it not in order:
                order.append(it)
        self._sel_order = order
        n = sum(1 for it in sel
                if isinstance(it, (WallItem, FurnishingItem, GroupItem)))
        self.a_group.setEnabled(n >= 2)
        self.a_ungroup.setEnabled(
            any(isinstance(it, GroupItem) for it in sel))
        # room ops act on two rooms/wall-loops, selected directly or grouped;
        # align works on one or more
        nshapes = len(self._selected_room_shapes())
        for a in getattr(self, "_room_op_actions", []):
            a.setEnabled(nshapes == 2)
        if hasattr(self, "a_align"):
            self.a_align.setEnabled(nshapes >= 1)
        for a in getattr(self, "_distribute_actions", []):
            a.setEnabled(nshapes >= 3)

    def nudge_selected(self, dx: int, dy: int, fine: bool = False) -> bool:
        """Arrow-key nudge of selected groups / ungrouped furnishings by one
        wall-snap step (a fine 1" step with Ctrl).  Returns True if anything
        moved."""
        step = SNAP_STEP if fine else SETTINGS["wall_snap_in"]
        moved = 0
        for it in self.scene.selectedItems():
            if isinstance(it, GroupItem):
                it.setPos(it.pos().x() + dx * step, it.pos().y() + dy * step)
                it.bake()                 # fold the move into the members
                moved += 1
            elif isinstance(it, FurnishingItem) and it.group() is None:
                it.setPos(it.pos().x() + dx * step, it.pos().y() + dy * step)
                moved += 1
        return moved > 0

    def align_rooms_to_grid(self):
        """Snap the walls of every selected room (or grouped wall-loop) to
        the wall-snap grid, so off-grid rooms line up.  Axis-aligned walls
        stay orthogonal because both endpoints share a coordinate that
        snaps to the same grid line."""
        shapes = self._selected_room_shapes()
        if not shapes:
            self.status("Select rooms (or grouped rooms) to align to the grid.")
            return
        step = SETTINGS["wall_snap_in"]
        walls = set()
        for s in shapes:
            walls.update(s["walls"])
        for w in walls:
            w.p1 = grid_snap(w.p1, step)
            w.p2 = grid_snap(w.p2, step)
        rebuild_all_walls(self.scene)     # rooms re-detect on the new walls
        self.status(f"Aligned {len(shapes)} room(s) to the "
                    f'{step:g}" grid.')

    @staticmethod
    def _translate_shape(shape, dx, dy):
        """Rigidly shift a room shape (its walls and, if any, its region)."""
        for w in shape["walls"]:
            w.p1 = QPointF(w.p1.x() + dx, w.p1.y() + dy)
            w.p2 = QPointF(w.p2.x() + dx, w.p2.y() + dy)
        r = shape["room"]
        if r is not None:
            r.prepareGeometryChange()
            r.anchor = QPointF(r.anchor.x() + dx, r.anchor.y() + dy)
            r.path = QTransform.fromTranslate(dx, dy).map(r.path)
            if r.corners:
                r.corners = [QPointF(c.x() + dx, c.y() + dy) for c in r.corners]
            r._sync_corner_props()

    def distribute_rooms(self, horizontal: bool):
        """Space the selected rooms so the gaps between them are equal,
        keeping the two outermost rooms fixed (3+ rooms needed)."""
        shapes = self._selected_room_shapes()
        if len(shapes) < 3:
            self.status("Select at least three rooms to distribute evenly.")
            return
        items = [(s, QPolygonF(s["corners"]).boundingRect()) for s in shapes]
        if horizontal:
            items.sort(key=lambda t: t[1].left())
            free = ((items[-1][1].right() - items[0][1].left())
                    - sum(b.width() for _, b in items))
            gap = free / (len(items) - 1)
            cursor = items[0][1].left()
            for s, b in items:
                self._translate_shape(s, cursor - b.left(), 0.0)
                cursor += b.width() + gap
        else:
            items.sort(key=lambda t: t[1].top())
            free = ((items[-1][1].bottom() - items[0][1].top())
                    - sum(b.height() for _, b in items))
            gap = free / (len(items) - 1)
            cursor = items[0][1].top()
            for s, b in items:
                self._translate_shape(s, 0.0, cursor - b.top())
                cursor += b.height() + gap
        rebuild_all_walls(self.scene)
        self.status(f"Distributed {len(shapes)} rooms evenly "
                    f"{'horizontally' if horizontal else 'vertically'}.")

    def refresh_rooms_cmd(self):
        """Re-scan the canvas: delete any room whose region is no longer
        enclosed by walls (e.g. a gray area left behind after its walls
        were moved away), then re-detect the survivors."""
        sc = self.scene
        removed = 0
        for it in list(sc.items()):
            if isinstance(it, RoomItem) and not room_walled(sc, it):
                sc.removeItem(it)
                removed += 1
        refresh_rooms(sc)                 # re-detect the survivors' regions
        self.status(f"Rooms refreshed — removed {removed} orphaned room(s)."
                    if removed else "Rooms refreshed — all rooms are walled.")

    def _selected_room_shapes(self):
        """Ordered list of room shapes from the selection.  Each is a dict
        {corners, name, props, walls, room, group}.  A shape comes from a
        directly selected room, the room a selected group encloses, or --
        when a group is just a closed wall-loop with no RoomItem -- the
        traced loop itself."""
        shapes, seen = [], set()
        for it in getattr(self, "_sel_order", []):
            shape = None
            if isinstance(it, RoomItem) and it.corners:
                shape = {"corners": [QPointF(c) for c in it.corners],
                         "name": it.name, "props": dict(it.properties),
                         "walls": list(it.bounding_walls()),
                         "room": it, "group": None, "key": id(it)}
            elif isinstance(it, GroupItem):
                gw = [c for c in it.childItems() if isinstance(c, WallItem)]
                room = group_room(it)
                if room is not None and room.corners:
                    shape = {"corners": [QPointF(c) for c in room.corners],
                             "name": room.name, "props": dict(room.properties),
                             "walls": gw, "room": room, "group": it,
                             "key": id(room)}
                else:
                    loop = trace_wall_loop(gw)
                    if loop:
                        shape = {"corners": loop, "name": "Room", "props": {},
                                 "walls": gw, "room": None, "group": it,
                                 "key": id(it)}
            if shape is not None and shape["key"] not in seen:
                seen.add(shape["key"])
                shapes.append(shape)
        return shapes

    def room_boolean(self, op: str):
        """Boolean op on the two selected rooms' perimeter polygons.

        combine = union, intersect = overlap only, subtract = first room
        minus second (selection order), fragment = the three pieces
        (first-only, second-only, overlap).  The two rooms may be selected
        directly, via their groups, or as grouped wall-loops.  The inputs
        and their walls are replaced by freshly walled result rooms."""
        shapes = self._selected_room_shapes()
        if len(shapes) != 2:
            self.status("Select two rooms or grouped wall-loops first.")
            return
        s1, s2 = shapes
        sc = self.scene
        # free any grouped sources so their walls are normal scene walls
        for s in (s1, s2):
            g = s["group"]
            if g is not None and g.scene() is not None:
                g.bake()
                g.dissolve()
        p1, p2 = (room_path_from_corners(s1["corners"]),
                  room_path_from_corners(s2["corners"]))
        overlap = p1.intersected(p2)
        name1, name2 = s1["name"], s2["name"]
        if op in ("intersect", "subtract", "fragment") \
                and path_area_sqft(overlap) < 1.0:
            self.status(f"{name1} and {name2} do not overlap.")
            return

        if op == "combine":
            results = [(p1.united(p2), name1, s1["props"])]
        elif op == "subtract":
            results = [(p1.subtracted(p2), name1, s1["props"])]
        elif op == "intersect":
            results = [(overlap, "Overlap", {})]
        elif op == "fragment":
            results = [(p1.subtracted(p2), name1, s1["props"]),
                       (p2.subtracted(p1), name2, s2["props"]),
                       (overlap, "Overlap", {})]
        else:
            return

        # drop the input rooms and the walls that defined them
        old_walls = set(s1["walls"]) | set(s2["walls"])
        for s in (s1, s2):
            if s["room"] is not None and s["room"].scene() is not None:
                sc.removeItem(s["room"])
        for w in old_walls:
            if w.scene() is not None:
                sc.removeItem(w)

        # gather result sub-polygons
        regions = []
        for path, base, props in results:
            for poly in path.simplified().toSubpathPolygons():
                corners = simplify_corners(poly)
                if len(corners) >= 3 and poly_area_sqft(corners) >= 1.0:
                    regions.append((corners, base, props))
        # build a COMPLETE wall loop for every region -- shared edges get a
        # wall per region (no dedup), tracked per region, so each fragment
        # owns all its walls
        region_walls = []
        for corners, _, _ in regions:
            ws, n = [], len(corners)
            for j in range(n):
                a, b = corners[j], corners[(j + 1) % n]
                if QLineF(a, b).length() >= MIN_WALL_LEN:
                    w = WallItem(QPointF(a), QPointF(b), "interior")
                    sc.addItem(w)
                    ws.append(w)
            region_walls.append(ws)
        rebuild_all_walls(sc)

        # detect + create the result rooms; for fragment, group each
        # fragment with its own walls so it moves as a self-contained,
        # fully-enclosed unit (coincident neighbour walls stay put)
        sc.clearSelection()
        created = 0
        for (corners, base, props), ws in zip(regions, region_walls,
                                              strict=True):
            res = detect_room(sc, interior_point(QPolygonF(corners)))
            if res is None:
                continue
            room = RoomItem(unique_room_name(sc, base),
                            interior_point(QPolygonF(corners)),
                            res[0], res[1], corners=res[2], properties=props)
            sc.addItem(room)
            bind_room_walls(sc, room)
            created += 1
            if op == "fragment" and len(ws) >= 2:
                grp = GroupItem()
                sc.addItem(grp)
                for w in ws:
                    grp.adopt(w)
            else:
                room.setSelected(True)
        self.status(f"{op.title()}: {name1} + {name2} -> {created} room(s).")

    def group_selected(self):
        """Group the selected walls/furnishings (existing groups merge).  When a
        room is selected, its surrounding + interior walls are DUPLICATED into
        the group (the originals stay put) so the group is a movable/copyable
        copy of the room."""
        members, old_groups = [], []
        for it in list(self.scene.selectedItems()):
            if isinstance(it, GroupItem):
                old_groups.append(it)
            elif isinstance(it, (WallItem, FurnishingItem)):
                members.append(it)
            elif isinstance(it, RoomItem):
                seen = set()
                for w in it.bounding_walls() + it.interior_walls():
                    if not isinstance(w, WallItem) or w.is_open or id(w) in seen:
                        continue
                    seen.add(id(w))
                    members.append(duplicate_wall(self.scene, w))
        for g in old_groups:
            g.bake()
            members += g.dissolve()
        if len(members) < 2:
            self.status("Select at least two walls/furnishings to group "
                        "(Ctrl+click to multi-select).")
            return
        self.scene.clearSelection()
        group = GroupItem()
        self.scene.addItem(group)
        for it in members:
            group.adopt(it)
        group.setSelected(True)
        self.status(f"Grouped {len(members)} items — drag to move, "
                    "Ctrl+Shift+G to ungroup.")

    def ungroup_selected(self):
        groups = [it for it in self.scene.selectedItems()
                  if isinstance(it, GroupItem)]
        if not groups:
            self.status("Select a group to ungroup.")
            return
        for g in groups:
            g.bake()                      # members keep their moved spot
            for c in g.dissolve():
                c.setSelected(True)
        coalesce_all(self.scene)          # now-free walls may merge with the plan
        rebuild_all_walls(self.scene)     # rooms re-detect region/outline
        self.status("Ungrouped — items left in place.")

    def coalesce_all_now(self):
        """Edit ▸ Coalesce all walls now: force the full-plan merge + weld sweep
        even when auto-coalesce is switched off."""
        n = _coalesce_all_impl(self.scene)
        weld_all(self.scene)                 # close T/L joints across the plan
        rebuild_all_walls(self.scene)
        self.status(f"Coalesced {n} overlapping wall(s) and welded junctions."
                    if n else "Welded wall junctions.")

    def _selection_spec(self):
        """Selected walls/furnishings (groups expand to their members)
        as a clipboard dict, or None when nothing usable is selected."""
        items = []
        for it in self.scene.selectedItems():
            if isinstance(it, GroupItem):
                it.bake()
                items += it.childItems()
            elif isinstance(it, (WallItem, FurnishingItem)):
                items.append(it)
        if not items:
            return None
        walls, furns = [], []
        xs, ys = [], []
        for it in items:
            if isinstance(it, WallItem):
                walls.append({
                    "type": it.wall_type,
                    "p1": [it.p1.x(), it.p1.y()],
                    "p2": [it.p2.x(), it.p2.y()],
                    "openings": [{
                        "kind": op.kind, "code": op.code, "s": op.s,
                        "door_type": op.door_type, "swing": op.swing,
                    } for op in it.openings],
                })
                xs += [it.p1.x(), it.p2.x()]
                ys += [it.p1.y(), it.p2.y()]
            else:
                p = it.scenePos()
                furns.append({"kind": it.kind, "pos": [p.x(), p.y()],
                              "rotation": it.rotation(), **it.extra_state()})
                xs.append(p.x())
                ys.append(p.y())
        ref = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2]
        return {"ref": ref, "walls": walls, "furnishings": furns,
                "grouped": len(items) > 1}

    # -- undo / redo ---------------------------------------------------------
    UNDO_LIMIT = 100

    def _mark_dirty(self, *args):
        """A scene change happened: (re)start the debounce so a burst of
        changes (e.g. a drag) becomes one undo step once it settles."""
        if not self._restoring:
            self._dirty_timer.start()

    def _commit_if_changed(self):
        """Snapshot the plan as one undo step if it differs from the last
        committed state."""
        if self._restoring:
            return
        state = self.serialize()
        if state == self._committed_state:
            return
        self._undo_stack.append(self._committed_state)
        if len(self._undo_stack) > self.UNDO_LIMIT:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._committed_state = state
        self._update_undo_actions()

    def _restore_state(self, state):
        self._dirty_timer.stop()
        self._restoring = True
        try:
            self.load_data(state, keep_backdrop=True)   # undo keeps the backdrop
        finally:
            self._restoring = False
        self._committed_state = self.serialize()
        self._update_undo_actions()

    def _reset_undo(self):
        """Drop the history (after New / Open): the current plan becomes the
        baseline state."""
        self._dirty_timer.stop()
        self._z_top = 0
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._committed_state = self.serialize()
        self._saved_state = self._committed_state    # fresh New/Open is clean
        self._update_undo_actions()

    def undo(self):
        self._commit_if_changed()        # fold in any pending change first
        if not self._undo_stack:
            self.status("Nothing to undo.")
            return
        self._redo_stack.append(self._committed_state)
        self._restore_state(self._undo_stack.pop())
        self.status("Undo.")

    def redo(self):
        self._commit_if_changed()
        if not self._redo_stack:
            self.status("Nothing to redo.")
            return
        self._undo_stack.append(self._committed_state)
        self._restore_state(self._redo_stack.pop())
        self.status("Redo.")

    def _update_undo_actions(self):
        if hasattr(self, "a_undo"):
            self.a_undo.setEnabled(bool(self._undo_stack))
            self.a_redo.setEnabled(bool(self._redo_stack))

    def cut_selected(self):
        spec = self._selection_spec()
        if spec is None:
            self.status("Select walls/furnishings (or a group) to cut.")
            return
        self.item_clipboard = spec
        for it in list(self.scene.selectedItems()):
            if isinstance(it, (GroupItem, WallItem, FurnishingItem)) \
                    and it.scene() is not None:
                self.scene.removeItem(it)
        rebuild_all_walls(self.scene)
        n = len(spec["walls"]) + len(spec["furnishings"])
        self.status(f"Cut {n} item(s) — Ctrl+V to paste at the mouse "
                    "position.")

    def copy_selected(self):
        spec = self._selection_spec()
        if spec is None:
            self.status("Select walls/furnishings (or a group) to copy.")
            return
        self.item_clipboard = spec
        n = len(spec["walls"]) + len(spec["furnishings"])
        self.status(f"Copied {n} item(s) — Ctrl+V to paste at the mouse "
                    "position.")

    def paste_clipboard(self):
        """Paste the cut/copied items centred on the mouse position,
        re-grouped when more than one item was taken."""
        spec = self.item_clipboard
        if not spec:
            self.status("Nothing to paste — cut or copy items first.")
            return
        target = self.view._last_scene
        if target is None:
            target = self.view.mapToScene(
                self.view.viewport().rect().center())
        dx, dy = target.x() - spec["ref"][0], target.y() - spec["ref"][1]
        if spec["walls"]:                 # keep walls on the on-centre grid
            dx, dy = wall_snap_len(dx), wall_snap_len(dy)
        else:
            dx, dy = round(dx), round(dy)
        pasted = []
        for wd in spec["walls"]:
            wall = WallItem(QPointF(wd["p1"][0] + dx, wd["p1"][1] + dy),
                            QPointF(wd["p2"][0] + dx, wd["p2"][1] + dy),
                            wd["type"])
            self.scene.addItem(wall)
            for od in wd["openings"]:
                try:
                    op = OpeningItem(wall, od["kind"], od["code"], od["s"])
                except ValueError:
                    continue
                op.door_type = od["door_type"]
                op.swing = od["swing"]
                wall.openings.append(op)
            wall.rebuild()
            pasted.append(wall)
        for fd in spec["furnishings"]:
            f = make_furnishing(
                fd["kind"], QPointF(fd["pos"][0] + dx, fd["pos"][1] + dy),
                fd["rotation"], fd)
            self.scene.addItem(f)
            pasted.append(f)
        rebuild_all_walls(self.scene)
        self.scene.clearSelection()
        if spec.get("grouped") and len(pasted) > 1:
            group = GroupItem()
            self.scene.addItem(group)
            for it in pasted:
                group.adopt(it)
            group.setSelected(True)
        else:
            for it in pasted:
                it.setSelected(True)
        self.status(f"Pasted {len(pasted)} item(s).")

    def zoom_fit(self):
        items = [it for it in self.scene.items() if isinstance(it, WallItem)]
        if items:
            rect = QRectF()
            for it in items:
                rect = rect.united(it.boundingRect())
            rect = rect.adjusted(-5 * FOOT, -5 * FOOT, 5 * FOOT, 5 * FOOT)
        else:
            rect = QRectF(-2 * FOOT, -2 * FOOT, 60 * FOOT, 44 * FOOT)
        self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def _is_dirty(self) -> bool:
        """True when the plan has edits not yet written to its file."""
        return self.serialize() != self._saved_state

    def _headless(self) -> bool:
        """True under the offscreen Qt platform (tests): skip modal dialogs."""
        return QApplication.platformName() == "offscreen"

    def _confirm_discard_changes(self, title: str = "Unsaved changes") -> bool:
        """If there are unsaved edits, ask Save / Discard / Cancel.  Returns True
        when it's OK to proceed (saved or discarded), False to cancel."""
        if not self._is_dirty():
            return True
        btn = QMessageBox.warning(
            self, title,
            "This design has unsaved changes.\nSave them before continuing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save)
        if btn == QMessageBox.StandardButton.Save:
            self.save_plan()
            return not self._is_dirty()      # False if the Save dialog was cancelled
        return btn == QMessageBox.StandardButton.Discard

    def closeEvent(self, e):
        # no prompt when there is no interactive UI (headless/offscreen tests),
        # otherwise the modal save dialog would block on close
        headless = QApplication.platformName() == "offscreen"
        if headless or self._confirm_discard_changes("Quit Floor Planner"):
            e.accept()
        else:
            e.ignore()

    def new_plan(self):
        if not self._confirm_discard_changes("New plan"):
            return
        self.scene.clear()
        self.current_path = None
        SETTINGS.update(DEFAULT_SETTINGS)
        self._apply_canvas()
        self.floors = [Floor(DEFAULT_FLOOR)]    # back to a single default floor
        self.active_floor = DEFAULT_FLOOR
        self._sync_floor_state()
        self._reset_undo()

    # -- save / load -------------------------------------------------------------
    def _update_title(self):
        if self.current_path:
            self.setWindowTitle(f"Floor Planner — {self.current_path}")
        else:
            c = canvas_rect()
            self.setWindowTitle(f"Floor Planner — canvas "
                                f"{fmt_ftin(c.width())} × "
                                f"{fmt_ftin(c.height())}")

    def project_from_scene(self) -> Project:
        """Walk the scene into the Qt-free domain model (model.Project).

        Open walls are skipped — they're regenerated from a room's open
        edges on load, not stored."""
        walls, rooms, furnishings = [], [], []
        for it in self.scene.items():
            if isinstance(it, FurnishingItem):
                furnishings.append(Furnishing(
                    kind=it.kind,
                    pos=(it.pos().x(), it.pos().y()),
                    rotation=it.rotation(),
                    extra=dict(it.extra_state()),
                    floor=getattr(it, "floor", DEFAULT_FLOOR),
                ))
            elif isinstance(it, WallItem) and not it.is_open:
                walls.append(WallModel(
                    wall_type=it.wall_type,
                    p1=(it.p1.x(), it.p1.y()),
                    p2=(it.p2.x(), it.p2.y()),
                    rooms=[r.name for r in it.rooms],
                    openings=[OpeningModel(op.kind, op.code, op.s,
                                           op.door_type, op.swing)
                              for op in it.openings],
                    floor=getattr(it, "floor", DEFAULT_FLOOR),
                ))
            elif isinstance(it, RoomItem):
                rooms.append(RoomModel(
                    name=it.name,
                    anchor=(it.anchor.x(), it.anchor.y()),
                    label_offset=(it.label_offset.x(), it.label_offset.y()),
                    show_dimensions=it.show_dims,
                    properties=it.properties,
                    floor=getattr(it, "floor", DEFAULT_FLOOR),
                ))
        # the roster MUST come from self.floors (an empty floor has no items to
        # derive it from); active_floor rides along but is dropped by to_dict.
        return Project(version=FILE_VERSION, units="inches",
                       settings=dict(SETTINGS), walls=walls, rooms=rooms,
                       furnishings=furnishings,
                       floors=[Floor(f.name, f.reference) for f in self.floors],
                       active_floor=self.active_floor)

    def serialize(self) -> dict:
        """Plan -> plain dict matching the documented JSON format.

        Goes through the Qt-free model; Project.to_dict emits the arrays in a
        stable, z-independent order (sorted by geometry) so bring-to-front z
        changes never alter the snapshot — keeping undo/redo comparison
        correct."""
        return self.project_from_scene().to_dict()

    def _sync_floor_state(self):
        """Mirror the authoritative roster (self.floors / active_floor /
        show_other_floors) into config's runtime cache, then re-apply
        visibility and repaint.  Cheap; called on init, load, and floor ops."""
        set_floor_state(
            active=self.active_floor,
            reference={f.name for f in self.floors if f.reference},
            show_others=self.show_other_floors,
        )
        apply_floor_visibility(self.scene)
        self.scene.update()
        if hasattr(self, "floor_label"):
            self.floor_label.setText(f"Floor: {self.active_floor}")
        if hasattr(self, "m_floors"):
            self._rebuild_floor_menu()

    # -- floor operations -----------------------------------------------------
    def _floor(self, name):
        return next((f for f in self.floors if f.name == name), None)

    def _rebuild_floor_menu(self):
        """Repopulate &Floors: New floor, a submenu per floor (edit/rename/
        reference/delete), then the Show-other-floors toggle."""
        m = self.m_floors
        m.clear()
        a_new = m.addAction("&New floor…")
        a_new.triggered.connect(self.new_floor)
        m.addSeparator()
        grp = QActionGroup(self)
        grp.setExclusive(True)
        for f in self.floors:
            tag = f"{f.name}{'  (R)' if f.reference else ''}" \
                  f"{'  ●' if f.name == self.active_floor else ''}"
            sub = m.addMenu(tag)
            a_edit = sub.addAction("Edit this floor")
            a_edit.setCheckable(True)
            a_edit.setChecked(f.name == self.active_floor)
            grp.addAction(a_edit)
            a_edit.triggered.connect(lambda _=False, n=f.name: self.switch_floor(n))
            a_ren = sub.addAction("Rename…")
            a_ren.triggered.connect(lambda _=False, n=f.name: self.rename_floor(n))
            a_ref = sub.addAction("Reference floor")
            a_ref.setCheckable(True)
            a_ref.setChecked(f.reference)
            a_ref.triggered.connect(
                lambda _=False, n=f.name: self.toggle_reference_floor(n))
            a_del = sub.addAction("Delete floor")
            a_del.setEnabled(len(self.floors) > 1)
            a_del.triggered.connect(lambda _=False, n=f.name: self.delete_floor(n))
        m.addSeparator()
        a_show = m.addAction("Show other floors (ghosted)")
        a_show.setCheckable(True)
        a_show.setChecked(self.show_other_floors)
        a_show.triggered.connect(self.toggle_show_others)

    def _popup_floor_menu(self):
        """Quick floor switch from the status-bar label."""
        menu = QMenu(self)
        for f in self.floors:
            a = menu.addAction(f"{f.name}{'  ●' if f.name == self.active_floor else ''}")
            a.triggered.connect(lambda _=False, n=f.name: self.switch_floor(n))
        menu.exec(self.floor_label.mapToGlobal(self.floor_label.rect().topLeft()))

    def switch_floor(self, name):
        """Make `name` the active (editable) floor.  View state only — no undo
        step, no dirty (serialize() is unchanged across a switch)."""
        if self._floor(name) is None or name == self.active_floor:
            return
        self.active_floor = name
        self._sync_floor_state()
        self.status(f"Editing floor '{name}'.")

    def new_floor(self):
        name, ok = QInputDialog.getText(self, "New floor", "Floor name:")
        name = name.strip()
        if not ok or not name:
            return
        if self._floor(name) is not None:
            QMessageBox.warning(self, "New floor",
                                f"A floor named '{name}' already exists.")
            return
        self.new_floor_named(name)

    def new_floor_named(self, name):
        """Add an EMPTY floor (Phase 1) and switch to it.  Non-interactive core
        of new_floor (also used by tests)."""
        if self._floor(name) is not None:
            return
        self.floors.append(Floor(name))
        self.active_floor = name               # switch to it
        self._sync_floor_state()
        self._commit_floor_change()
        self.status(f"Added floor '{name}'.")

    def rename_floor(self, name):
        f = self._floor(name)
        if f is None:
            return
        new, ok = QInputDialog.getText(self, "Rename floor",
                                       "New name:", text=name)
        new = new.strip()
        if not ok or not new or new == name:
            return
        if self._floor(new) is not None:
            QMessageBox.warning(self, "Rename floor",
                                f"A floor named '{new}' already exists.")
            return
        for it in self.scene.items():          # retag this floor's items
            if getattr(it, "floor", None) == name:
                it.floor = new
        f.name = new
        if self.active_floor == name:
            self.active_floor = new
        self._sync_floor_state()
        self._commit_floor_change()

    def toggle_reference_floor(self, name):
        f = self._floor(name)
        if f is None:
            return
        f.reference = not f.reference
        self._sync_floor_state()
        self._commit_floor_change()

    def toggle_show_others(self, checked):
        self.show_other_floors = bool(checked)
        self._sync_floor_state()             # view state only — not undoable

    def delete_floor(self, name):
        if len(self.floors) <= 1:            # never delete the last floor
            return
        f = self._floor(name)
        if f is None:
            return
        n_items = sum(1 for it in self.scene.items()
                      if getattr(it, "floor", None) == name)
        if self._confirm_floor_delete(name, n_items) is False:
            return
        for it in list(self.scene.items()):  # remove this floor's items
            if getattr(it, "floor", None) == name and it.parentItem() is None:
                self.scene.removeItem(it)
        self.floors = [g for g in self.floors if g.name != name]
        if self.active_floor == name:        # land on a surviving floor
            self.active_floor = self.floors[0].name
        rebuild_all_walls(self.scene)
        self._sync_floor_state()
        self._commit_floor_change()
        self.status(f"Deleted floor '{name}'.")

    def _confirm_floor_delete(self, name, n_items) -> bool:
        if self._headless():
            return True
        msg = (f"Delete floor '{name}' and its {n_items} item(s)?"
               if n_items else f"Delete the empty floor '{name}'?")
        return QMessageBox.question(
            self, "Delete floor", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes

    def _commit_floor_change(self):
        """Roster edits (add/rename/delete/reference) DO change serialize(), so
        capture an undo step + mark dirty — unlike a plain active-floor switch."""
        self._rebuild_floor_menu()
        self._commit_if_changed()

    def load_data(self, data: dict, keep_backdrop: bool = False):
        """Rebuild the scene from a plan dict, via the Qt-free model.

        Parsing/migration (format check, defaults, version) live in
        Project.from_dict; this bridge turns the model into scene items."""
        self.apply_project_to_scene(Project.from_dict(data), keep_backdrop)

    def apply_project_to_scene(self, project: Project,
                               keep_backdrop: bool = False):
        for key, default in DEFAULT_SETTINGS.items():
            val = project.settings.get(key, default)
            if isinstance(default, bool):    # keep flags as bool (not 1.0/0.0)
                SETTINGS[key] = bool(val)
                continue
            try:
                SETTINGS[key] = float(val)
            except (TypeError, ValueError):
                SETTINGS[key] = default
        self._apply_canvas()
        # the reference image is a tracing backdrop, not plan data -- on undo
        # (keep_backdrop) detach it so scene.clear() doesn't delete it, then
        # re-add it afterwards.  New/Open clear it like everything else.
        backdrops = []
        if keep_backdrop:
            backdrops = [it for it in self.scene.items()
                         if isinstance(it, ReferenceImageItem)]
            for b in backdrops:
                self.scene.removeItem(b)
        self.scene.clear()
        for b in backdrops:
            self.scene.addItem(b)
        # restore the floor roster + active floor from the model, and prime the
        # runtime cache NOW so items created during this load default to the
        # right active floor (each item's floor is then overridden from the file).
        self.floors = [Floor(f.name, f.reference) for f in project.floors]
        self.active_floor = project.active_floor
        set_floor_state(active=self.active_floor)
        self._z_top = 0                  # bring-to-front counter resets per doc
        for wm in project.walls:
            wall = WallItem(QPointF(*wm.p1), QPointF(*wm.p2), wm.wall_type)
            wall.floor = wm.floor                 # load overrides the default tag
            self.scene.addItem(wall)
            for om in wm.openings:
                try:
                    op = OpeningItem(wall, om.kind, om.code, om.s)
                except ValueError:
                    continue              # e.g. opening wider than the wall
                op.door_type = om.door_type
                op.swing = om.swing
                wall.openings.append(op)
            # no per-wall rebuild here: rebuild_all_walls below rebuilds every
            # wall once with a shared index (a per-wall rebuild is O(n) with
            # cascade, so on a big/duplicated plan the loop alone took minutes)
        # merge overlapping/duplicate walls (e.g. legacy v1/v2 party-wall pairs)
        # into single shared walls FIRST, so the rebuild runs on the reduced set
        # (welding is NOT done here: load is also the undo-restore path and
        # welding does not fully converge at messy junctions -> geometry would
        # drift on every undo.  Junctions weld on draw and via the manual sweep.)
        coalesce_all(self.scene)
        rebuild_all_walls(self.scene)
        missing = []
        for rm in project.rooms:
            anchor = QPointF(*rm.anchor)
            res = detect_room(self.scene, anchor)
            if res is None:
                # an open room (a wall was detached/moved away) won't flood-fill
                # -> rebuild it from the saved perimeter corners
                saved = (rm.properties or {}).get("perimeter_corners")
                if saved and len(saved) >= 3:
                    corners = [QPointF(c[0], c[1]) for c in saved]
                    res = (room_path_from_corners(corners),
                           poly_area_sqft(corners), corners)
                else:
                    # keep the room (so it survives a re-save); placeholder
                    path = QPainterPath()
                    path.addRect(QRectF(anchor.x() - 12, anchor.y() - 12,
                                        24, 24))
                    res = (path, 0.0, None)
                    missing.append(rm.name)
            name = unique_room_name(self.scene, rm.name)
            room = RoomItem(name, anchor, res[0], res[1],
                            rm.properties, res[2])
            room.floor = rm.floor                 # load overrides the default tag
            room.show_dims = rm.show_dimensions
            room.label_offset = QPointF(*rm.label_offset)
            self.scene.addItem(room)
            # bind this room's walls by geometry (works for both v2 plans,
            # which store coincident party walls, and legacy v1 plans)
            bind_room_walls(self.scene, room, settle=False)
            for w in room.walls:                  # a room's walls share its floor
                w.floor = room.floor              # (fixes synthesized/open edges)
        unknown = []
        for fm in project.furnishings:
            if furnishing_spec(fm.kind) is None:
                unknown.append(fm.kind or "?")
                continue
            item = make_furnishing(fm.kind, QPointF(*fm.pos), fm.rotation,
                                   fm.extra)
            item.floor = fm.floor                 # load overrides the default tag
            self.scene.addItem(item)
        # roster + active floor are restored; sync the runtime cache + visibility
        self._sync_floor_state()
        notes = []
        if missing:
            notes.append("Could not re-detect room(s): " + ", ".join(missing)
                         + " — check the walls around them.")
        if unknown:
            notes.append("Skipped unknown furnishing kind(s): "
                         + ", ".join(unknown) + ".")
        if notes:
            self.status("  ".join(notes))

    def paste_room(self, sp: QPointF):
        """Recreate the copied room (walls, openings, properties) with its
        anchor at `sp`; the name gets a number appended if already used."""
        spec = self.room_clipboard
        if not spec:
            return
        src = QPointF(*spec["anchor"])
        dx = wall_snap_len(sp.x() - src.x())   # pasted walls stay on the
        dy = wall_snap_len(sp.y() - src.y())   # same on-centre grid
        for wd in spec["walls"]:
            wall = WallItem(QPointF(wd["p1"][0] + dx, wd["p1"][1] + dy),
                            QPointF(wd["p2"][0] + dx, wd["p2"][1] + dy),
                            wd["type"])
            self.scene.addItem(wall)
            for od in wd["openings"]:
                try:
                    op = OpeningItem(wall, od["kind"], od["code"], od["s"])
                except ValueError:
                    continue
                op.door_type = od["door_type"]
                op.swing = od["swing"]
                wall.openings.append(op)
            wall.rebuild()
        rebuild_all_walls(self.scene)
        anchor = QPointF(src.x() + dx, src.y() + dy)
        res = detect_room(self.scene, anchor)
        if res is None:
            self.status("Pasted the walls, but no enclosed room was "
                        "detected at the paste point.")
            return
        path, area, corners = res
        name = unique_room_name(self.scene, spec["name"])
        room = RoomItem(name, anchor, path, area,
                        dict(spec["properties"]), corners)
        room.show_dims = bool(spec["show_dimensions"])
        self.scene.addItem(room)
        bind_room_walls(self.scene, room)
        self.status(f"Pasted room '{name}'.")

    # -- CSV room import ----------------------------------------------------------
    def _wall_exists(self, p1: QPointF, p2: QPointF) -> bool:
        for it in self.scene.items():
            if isinstance(it, WallItem) and (
                    (QLineF(it.p1, p1).length() < 0.6
                     and QLineF(it.p2, p2).length() < 0.6)
                    or (QLineF(it.p1, p2).length() < 0.6
                        and QLineF(it.p2, p1).length() < 0.6)):
                return True
        return False

    def _free_spot(self, w_in: float, h_in: float):
        """Top-left corner (snapped) of a canvas spot where a w x h room
        won't touch existing walls or rooms (24" clearance)."""
        margin = 24.0
        canvas = canvas_rect()
        occupied = []
        for it in self.scene.items():
            if isinstance(it, WallItem):
                occupied.append(it.boundingRect())
            elif isinstance(it, RoomItem):
                occupied.append(it.path.boundingRect())
        step = max(SETTINGS["wall_snap_in"], 12.0)
        y = canvas.top() + margin
        while y + h_in + margin <= canvas.bottom():
            x = canvas.left() + margin
            while x + w_in + margin <= canvas.right():
                cand = QRectF(x - margin / 2, y - margin / 2,
                              w_in + margin, h_in + margin)
                if not any(cand.intersects(r) for r in occupied):
                    return x, y
                x += step
            y += step
        # canvas full: park it to the right of everything
        right = max([r.right() for r in occupied], default=canvas.left())
        return wall_snap_len(right + margin), canvas.top() + margin

    def import_rooms_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import rooms from CSV", "",
            "CSV files (*.csv);;All files (*)")
        if path:
            self._import_rooms(path)

    # -- import a plan from a PNG image (preview -> accept) -------------------
    def import_from_image(self, path=None, *, width_ft=40.0, merge=3,
                          threshold=128, wall_type="exterior",
                          interactive=True):
        """File > Import from image: detect walls in a raster floor plan, show
        them as a blue ghost overlay, and add them on accept.  Pass
        interactive=False (with explicit params) to run headlessly."""
        if interactive and path is None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Import plan from image", "",
                "Images (*.png *.jpg *.jpeg *.bmp);;All files (*)")
            if not path:
                return None
            dlg = ImageImportDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return None
            width_ft, merge, threshold = dlg.values()
        try:
            import fp_extract
            gray = fp_extract.load_gray(path)
            h, w = gray.shape
            walls_px = fp_extract.detect_walls(gray, threshold, 24, merge, 40)
            segs = fp_extract.scene_segments(walls_px, w, h, width_ft=width_ft)
        except Exception as ex:                       # noqa: BLE001
            if interactive:
                QMessageBox.critical(self, "Import failed", str(ex))
            return None
        if not segs:
            if interactive:
                QMessageBox.information(
                    self, "Import from image",
                    "No walls detected.  Try a cleaner image or adjust the "
                    "threshold / merge settings.")
            return None

        self._show_wall_ghost(segs)
        if interactive:
            ok = QMessageBox.question(
                self, "Import from image",
                f"Detected {len(segs)} wall(s), shown in blue on the canvas.\n"
                "Add them to the plan?") == QMessageBox.StandardButton.Yes
            self._clear_wall_ghost()
            if not ok:
                return None
        else:
            self._clear_wall_ghost()

        for x0, y0, x1, y1 in segs:
            self.scene.addItem(
                WallItem(QPointF(x0, y0), QPointF(x1, y1), wall_type))
        rebuild_all_walls(self.scene)
        self._update_totals()
        self._commit_if_changed()
        self.status(f"Imported {len(segs)} wall(s) from {os.path.basename(path)}"
                    " — click an enclosed area with the Room tool to name it.")
        return len(segs)

    def _show_wall_ghost(self, segs):
        """Draw the candidate walls as a translucent blue overlay and fit the
        view to them so the user can preview before accepting."""
        self._clear_wall_ghost()
        path = QPainterPath()
        for x0, y0, x1, y1 in segs:
            path.moveTo(QPointF(x0, y0))
            path.lineTo(QPointF(x1, y1))
        item = QGraphicsPathItem(path)
        pen = QPen(QColor(37, 99, 235, 170), 6.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        item.setPen(pen)
        item.setZValue(1_000_000)                     # above everything
        self.scene.addItem(item)
        self._wall_ghost = item
        self.view.fitInView(item.boundingRect().adjusted(-24, -24, 24, 24),
                            Qt.AspectRatioMode.KeepAspectRatio)

    def _clear_wall_ghost(self):
        item = getattr(self, "_wall_ghost", None)
        if item is not None:
            if item.scene() is not None:
                self.scene.removeItem(item)
            self._wall_ghost = None

    # -- interactive image backdrop: place, calibrate, extract ---------------
    def start_image_import(self, path=None):
        """File > Import from image: drop the PNG on the canvas as a backdrop
        to move / scale / crop / calibrate, then Extract walls."""
        if path is None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Import plan from image", "",
                "Images (*.png *.jpg *.jpeg *.bmp);;All files (*)")
            if not path:
                return None
        img = QImage(path)
        if img.isNull():
            QMessageBox.critical(self, "Import failed",
                                 f"Could not read image:\n{path}")
            return None
        ipp = canvas_rect().width() * 0.7 / max(img.width(), 1)
        item = ReferenceImageItem(img, ipp)
        item.setPos(QPointF(canvas_rect().width() * 0.1,
                            canvas_rect().height() * 0.1))
        self.scene.addItem(item)
        self.scene.clearSelection()
        item.setSelected(True)
        self.view.fitInView(item.sceneBoundingRect().adjusted(-48, -48, 48, 48),
                            Qt.AspectRatioMode.KeepAspectRatio)
        self.status("Image placed — drag to move, drag a corner to scale, "
                    "right-click for Calibrate / Crop / Extract walls / "
                    "Remove.")
        return item

    def _finish_calibrate(self, item, pts):
        val, ok = QInputDialog.getDouble(
            self, "Calibrate scale",
            "Real distance between the two clicked points (feet):",
            10.0, 0.01, 100000.0, 2)
        if not ok or item is None:
            return
        item.calibrate(pts[0], pts[1], val * FOOT)
        self.status(f"Calibrated — that span is now {fmt_ftin(val * FOOT)}.")

    def extract_from_reference(self, item, interactive=True):
        """Detect walls in the (scaled/cropped) backdrop and add them, with a
        blue ghost preview when interactive."""
        segs = item.wall_segments()
        if not segs:
            if interactive:
                QMessageBox.information(
                    self, "Extract walls",
                    "No walls detected.  Calibrate/crop closer or adjust the "
                    "image, then try again.")
            return None
        self._show_wall_ghost(segs)
        if interactive:
            ok = QMessageBox.question(
                self, "Extract walls",
                f"Detected {len(segs)} wall(s), shown in blue.  Add them to "
                "the plan?") == QMessageBox.StandardButton.Yes
            self._clear_wall_ghost()
            if not ok:
                return None
        else:
            self._clear_wall_ghost()
        for x0, y0, x1, y1 in segs:
            self.scene.addItem(
                WallItem(QPointF(x0, y0), QPointF(x1, y1), "exterior"))
        rebuild_all_walls(self.scene)
        self._update_totals()
        self._commit_if_changed()
        self.status(f"Added {len(segs)} wall(s) — right-click the image to "
                    "remove it, then name rooms with the Room tool.")
        return len(segs)

    def _import_rooms(self, path: str, interactive: bool = True):
        """Create walled rooms from a CSV with the columns
        Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes (Type, locations and
        Notes optional).  X_ft/Y_ft are the room's perimeter width and
        length; X_loc/Y_loc place its BOTTOM-LEFT corner, measured in
        feet from the canvas's bottom-left corner.  Rooms without a
        location go to the first clear spot on the canvas.

        The canvas grows (never shrinks) so every room fits, up to
        MAX_CANVAS_IN; a room whose size/location needs more than that is
        rejected as a likely typo."""
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    raise ValueError("Empty CSV file.")
                rows = [{(k or "").strip().lower(): (v or "").strip()
                         for k, v in row.items()} for row in reader]
        except (OSError, csv.Error, ValueError) as ex:
            if interactive:
                QMessageBox.critical(self, "Import failed", str(ex))
            self.status(f"Import failed: {ex}")
            return
        margin = 2.0 * FOOT
        max_in = MAX_CANVAS_IN

        # -- pass 1: parse + validate every row (no placement yet) --------
        specs, errors = [], []
        for i, row in enumerate(rows, start=2):     # 1 = header line
            name = row.get("name", "")
            try:
                if not name:
                    raise ValueError("missing Name")
                w_in = parse_feet(row["x_ft"])
                h_in = parse_feet(row["y_ft"])
                if w_in < 36.0 or h_in < 36.0:
                    raise ValueError("rooms must be at least 3' x 3'")
                xl, yl = row.get("x_loc_ft", ""), row.get("y_loc_ft", "")
                if xl and yl:
                    xl_in, yl_in, located = parse_feet(xl), parse_feet(yl), True
                elif xl or yl:
                    raise ValueError("give both X_loc_ft and Y_loc_ft, "
                                     "or neither")
                else:
                    xl_in = yl_in = None
                    located = False
                far_w = (xl_in + w_in) if located else w_in
                far_h = (yl_in + h_in) if located else h_in
                if far_w > max_in or far_h > max_in:
                    raise ValueError(
                        f"exceeds the {max_in / FOOT:g}' canvas limit "
                        "(check for a typo)")
            except (KeyError, ValueError) as ex:
                errors.append(f"line {i} ({name or '?'}): {ex}")
                continue
            specs.append({"name": name, "w": w_in, "h": h_in,
                          "located": located, "xl": xl_in, "yl": yl_in,
                          "type": row.get("type", ""),
                          "notes": row.get("notes", "")})

        # -- grow the canvas so every room fits (grow only, capped) -------
        # located rooms drive both dimensions; auto-placed rooms only need
        # the height to be tall enough to hold them (width grows afterwards)
        req_w = max([s["xl"] + s["w"] + margin
                     for s in specs if s["located"]], default=0.0)
        req_h = max([s["yl"] + s["h"] + margin
                     for s in specs if s["located"]]
                    + [s["h"] + 2 * margin
                       for s in specs if not s["located"]], default=0.0)
        new_w = min(max(SETTINGS["canvas_w_in"], req_w), max_in)
        new_h = min(max(SETTINGS["canvas_h_in"], req_h), max_in)
        resized = (new_w > SETTINGS["canvas_w_in"]
                   or new_h > SETTINGS["canvas_h_in"])
        if resized:
            SETTINGS["canvas_w_in"], SETTINGS["canvas_h_in"] = new_w, new_h
            self._apply_canvas()

        # -- pass 2: build the rooms (canvas height is now final) ---------
        canvas = canvas_rect()
        imported = 0
        for s in specs:
            w_in, h_in = s["w"], s["h"]
            if s["located"]:
                left = wall_snap_len(s["xl"])
                top = wall_snap_len(canvas.bottom() - s["yl"] - h_in)
            else:
                left, top = self._free_spot(w_in, h_in)
            corners = [QPointF(left, top), QPointF(left + w_in, top),
                       QPointF(left + w_in, top + h_in),
                       QPointF(left, top + h_in)]
            for j in range(4):
                p1, p2 = corners[j], corners[(j + 1) % 4]
                if not self._wall_exists(p1, p2):
                    self.scene.addItem(WallItem(QPointF(p1), QPointF(p2),
                                                "interior"))
            rebuild_all_walls(self.scene)
            centre = QPointF(left + w_in / 2, top + h_in / 2)
            res = detect_room(self.scene, centre)
            if res is None:
                errors.append(f"{s['name']}: no enclosed area detected "
                              "(overlapping another room?)")
                continue
            room = RoomItem(unique_room_name(self.scene, s["name"]), centre,
                            res[0], res[1], corners=res[2])
            if s["type"]:
                room.properties["room_type"] = next(
                    (t for t in ROOM_TYPES if t.lower() == s["type"].lower()),
                    s["type"])
            if s["notes"]:
                room.properties["notes"] = s["notes"]
            self.scene.addItem(room)
            bind_room_walls(self.scene, room)
            imported += 1

        # -- grow width for any auto-placed room parked past the edge -----
        walls = [it for it in self.scene.items() if isinstance(it, WallItem)]
        right = max([p.x() for it in walls for p in (it.p1, it.p2)],
                    default=0.0)
        if right + margin > canvas.right():
            grow_w = min(right + margin, max_in)
            if grow_w > SETTINGS["canvas_w_in"]:
                SETTINGS["canvas_w_in"] = grow_w
                self._apply_canvas()
                resized = True

        note = ""
        if resized:
            c = canvas_rect()
            note = (f" Canvas resized to {c.width() / FOOT:g}' × "
                    f"{c.height() / FOOT:g}'.")
        self.status(f"Imported {imported} room(s) from {path}"
                    + (f" — {len(errors)} row(s) skipped." if errors else ".")
                    + note)
        self._import_errors = errors      # inspectable (and testable)
        if errors and interactive:
            QMessageBox.warning(self, "Import finished with problems",
                                "\n".join(errors[:20]))

    def export_rooms_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export rooms to CSV", "rooms.csv",
            "CSV files (*.csv);;All files (*)")
        if path:
            self._export_rooms(path)

    def _export_rooms(self, path: str, interactive: bool = True):
        """Write every room as a CSV row in the same format the importer
        reads (Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes), so a plan's
        rooms round-trip.  Sizes/locations come from the room perimeter
        (wall centrelines); locations are the bottom-left corner in feet
        from the canvas's bottom-left corner, lengths in decimal feet."""

        def ft(v: float) -> str:
            return f"{v / 12.0:g}"

        canvas = canvas_rect()
        rooms = sorted((it for it in self.scene.items()
                        if isinstance(it, RoomItem)),
                       key=lambda r: r.name.lower())
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                wr = csv.writer(f)
                wr.writerow(["Name", "Type", "X_ft", "Y_ft",
                             "X_loc_ft", "Y_loc_ft", "Notes"])
                for r in rooms:
                    if r.corners:
                        xs = [c.x() for c in r.corners]
                        ys = [c.y() for c in r.corners]
                    else:                   # no traced perimeter: use the
                        rect = r.interior_rect()      # flood region box
                        xs = [rect.left(), rect.right()]
                        ys = [rect.top(), rect.bottom()]
                    wr.writerow([
                        r.name,
                        r.properties.get("room_type", ""),
                        ft(max(xs) - min(xs)),
                        ft(max(ys) - min(ys)),
                        ft(min(xs)),
                        ft(canvas.bottom() - max(ys)),
                        " ".join(str(r.properties.get("notes", ""))
                                 .split()),
                    ])
        except OSError as ex:
            if interactive:
                QMessageBox.critical(self, "Export failed", str(ex))
            self.status(f"Export failed: {ex}")
            return
        self.status(f"Exported {len(rooms)} room(s) to {path}")

    def open_plan(self):
        if not self._confirm_discard_changes("Open plan"):
            return
        start = self.current_path or str(designs_dir())
        path, _ = QFileDialog.getOpenFileName(
            self, "Open plan", start,
            "Floor plan JSON (*.json);;All files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.load_data(data)
        except (OSError, ValueError, KeyError, TypeError) as ex:
            QMessageBox.critical(self, "Open failed", str(ex))
            return
        self.current_path = path
        self._update_title()
        self._reset_undo()               # opened document is the new baseline
        self.status(f"Opened {path}")

    def save_plan(self):
        if not self.current_path:
            self.save_plan_as()
            return
        self._write_plan(self.current_path)

    def save_plan_as(self):
        start = self.current_path or str(designs_dir() / "floorplan.json")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save plan", start,
            "Floor plan JSON (*.json);;All files (*)")
        if not path:
            return
        self._write_plan(path)

    def _write_plan(self, path: str):
        state = self.serialize()
        # the file remembers the active floor, but _saved_state must NOT (it's
        # view state) or the dirty check would flag a clean plan after a switch.
        on_disk = {**state, "active_floor": self.active_floor}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(on_disk, f, indent=2)
        except OSError as ex:
            QMessageBox.critical(self, "Save failed", str(ex))
            return
        self.current_path = path
        self._saved_state = state            # plan now matches what's on disk
        self._update_title()
        self.status(f"Saved {path}")

    # -- headless / macro hooks ----------------------------------------------
    # These let an external driver (fp_macro.py) load, edit, snapshot and save
    # a plan with no dialogs.  See docs/macro_language.md for the macro syntax.

    def load_path(self, path: str):
        """Non-interactive open (no dialogs).  Raises on failure."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.load_data(data)
        self.current_path = path
        self._update_title()
        self._reset_undo()

    def save_path(self, path: str):
        """Non-interactive save (no dialogs).  Raises on failure."""
        state = self.serialize()
        on_disk = {**state, "active_floor": self.active_floor}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(on_disk, f, indent=2)
        self.current_path = path
        self._saved_state = state
        self._update_title()

    def clear_plan(self):
        """Non-interactive New (no confirm dialog)."""
        self.scene.clear()
        self.current_path = None
        SETTINGS.update(DEFAULT_SETTINGS)
        self._apply_canvas()
        self.floors = [Floor(DEFAULT_FLOOR)]    # back to a single default floor
        self.active_floor = DEFAULT_FLOOR
        self._sync_floor_state()
        self._reset_undo()

    def prepare_headless(self, w: int = 1280, h: int = 860):
        """Size the window/view and fit the canvas so scene<->viewport
        mapping is valid for synthesized mouse events when running
        offscreen.  Call once before driving a macro that uses CLICK/DRAG."""
        self.resize(w, h)
        self.view.resize(w, max(200, h - 120))
        margin = 5 * FOOT
        self.view.setSceneRect(canvas_rect().adjusted(
            -margin, -margin, margin, margin))
        self.view.fitInView(self.view.sceneRect(),
                            Qt.AspectRatioMode.KeepAspectRatio)
        QApplication.processEvents()

    def _content_rect(self) -> QRectF:
        """Bounding box of all walls/rooms/furnishings (or the canvas when
        empty), with a 1' margin — the region a snapshot should frame."""
        box = QRectF()
        for it in self.scene.items():
            if isinstance(it, (WallItem, RoomItem, FurnishingItem)):
                box = box.united(it.sceneBoundingRect())
        if box.isNull():
            box = canvas_rect()
        return box.adjusted(-FOOT, -FOOT, FOOT, FOOT)

    def export_canvas(self, path: str, rect: QRectF = None,
                      scale: float = 2.0) -> bool:
        """Render the scene (items only, no editor grid) to a PNG or SVG file,
        chosen by the path's extension.  `rect` defaults to the content box."""
        rect = QRectF(rect) if rect is not None else self._content_rect()
        if str(path).lower().endswith(".svg"):
            return self._export_svg(path, rect)
        return self._export_png(path, rect, scale)

    def _export_png(self, path, rect, scale) -> bool:
        img = QImage(max(1, int(rect.width() * scale)),
                     max(1, int(rect.height() * scale)),
                     QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.white)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.scene.render(p, QRectF(0, 0, img.width(), img.height()), rect)
        p.end()
        return bool(img.save(str(path)))

    def _export_svg(self, path, rect) -> bool:
        if QSvgGenerator is None:
            raise RuntimeError("QtSvg is unavailable -- cannot write SVG.")
        gen = QSvgGenerator()
        gen.setFileName(str(path))
        gen.setSize(QSize(max(1, int(rect.width())),
                          max(1, int(rect.height()))))
        gen.setViewBox(QRectF(0, 0, rect.width(), rect.height()))
        gen.setTitle("FloorPlanner canvas")
        gen.setDescription("Scene units are inches (1 unit = 1 inch). "
                           "Origin at the framed region's top-left.")
        p = QPainter(gen)
        self.scene.render(p, QRectF(0, 0, rect.width(), rect.height()), rect)
        p.end()
        return True

    def scene_summary(self) -> dict:
        """A machine-readable description of the layout for an AI driver:
        the full serialized model plus item counts."""
        data = self.serialize()
        data["counts"] = {
            "walls": len(data["walls"]),
            "rooms": len(data["rooms"]),
            "furnishings": len(data["furnishings"]),
        }
        return data

    def run_macro(self, text: str) -> dict:
        """Execute a macro string against this window; returns a result dict
        {ok, steps, log, errors}.  See MacroRunner for the token grammar."""
        return MacroRunner(self).run(text)
