"""The application main window: menus, toolbars, the scene<->model
serialization bridge, IO, and all edit orchestration."""
import importlib.util

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
from floorplanner.rooms import *  # noqa: F401
from floorplanner.roofs import RoofItem, eaves_span_from_wall
from floorplanner.items import *  # noqa: F401
from floorplanner.model import (  # serialization bridge (aliased)
    DEFAULT_FLOOR, Floor,
)
from floorplanner.design.validate import check   # defect 28 evidence
from floorplanner.design.verify import (  # P1.6 shadow mode
    BASELINE_ATTR as VERIFY_BASELINE_ATTR, DesignVerificationError, verify,
)
from floorplanner.dialogs import *  # noqa: F401
from floorplanner.view import *  # noqa: F401
from floorplanner.macro import *  # noqa: F401
from floorplanner.csvio import CsvIOMixin
from floorplanner.imageio import ImageIOMixin
from floorplanner.levels import LevelsMixin
from floorplanner.planio import PlanIOMixin


class MainWindow(QMainWindow, PlanIOMixin, CsvIOMixin,
                 ImageIOMixin, LevelsMixin):
    HINTS = {
        TOOL_SELECT: ("Select: drag wall BODY to slide it sideways (Ctrl = "
                      "free move) \u2022 drag wall ENDS to lengthen/shorten "
                      "(Shift = free angle) \u2022 drag furnishings from the "
                      "right palette onto the plan \u2022 Ctrl+click toggles "
                      "items in the selection set, Ctrl+drag rubber-bands "
                      "more in, Ctrl+G groups, Ctrl+X/C/V cut-copy-paste "
                      "\u2022 drag empty space to pan \u2022 wheel zoom"),
        TOOL_WALL_EXT: "Exterior wall (6\"): click-drag to draw. Orthogonal "
                       "from the anchor (Shift = free angle, Ctrl = 15° "
                       "steps). Esc cancels.",
        TOOL_WALL_INT: "Interior wall (4 1/2\"): click-drag to draw. "
                       "Orthogonal from the anchor (Shift = free angle, "
                       "Ctrl = 15° steps). Esc cancels.",
        TOOL_DOOR: "Door: click on a wall, then enter the WWHH size "
                   "(e.g. 3280 = 32\" x 80\").",
        TOOL_WINDOW: "Window: click on a wall, then enter the WWHH size "
                     "(e.g. 3648 = 36\" x 48\").",
        TOOL_ROOM: "Room name: click inside an enclosed area to name a room, "
                   "then the tool reverts to Select. Ctrl+click the tool to "
                   "keep it active for several rooms.",
        TOOL_ROOF_RIDGE: "Roof ridge: click-drag to sketch the ridge line "
                         "(Shift = free angle, Ctrl = 15° steps, same as a "
                         "wall). Release, then click the eaves wall this "
                         "roof spans over. Esc cancels.",
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
        # the selected wall's identity: id + its two vertices, cleared unless
        # exactly one wall is selected -- kept updated in _apply_edit_actions,
        # the existing debounced selectionChanged handler, rather than a
        # second listener
        self.wall_label = QLabel("")
        self.wall_label.setStyleSheet("QLabel { padding: 0 6px; }")
        self.statusBar().addPermanentWidget(self.wall_label)
        # active-floor indicator: click to pop a quick floor-switch menu
        self.floor_label = QLabel("Floor: default")
        self.floor_label.setToolTip("Active floor — click to switch")
        self.floor_label.setStyleSheet("QLabel { padding: 0 6px; }")
        self.floor_label.mousePressEvent = lambda e: self._popup_floor_menu()
        self.statusBar().addPermanentWidget(self.floor_label)
        # launch-time code identity (version · branch @ sha): the truthful
        # answer to "which code is this window running?" -- a process keeps
        # the code it imported, so restart after pulling to pick up changes
        ver_label = QLabel(code_version())
        ver_label.setToolTip("App version and the git branch/commit this "
                             "window was LAUNCHED from. If you pulled or "
                             "edited code since, restart to pick it up.")
        ver_label.setStyleSheet("QLabel { color: #888; padding: 0 6px; }")
        self.statusBar().addPermanentWidget(ver_label)
        self.status(self.HINTS[TOOL_SELECT])

        # keep the toolbar totals current -- debounced behind the 180 ms dirty
        # timer (set up below), not fired on every scene.changed (defect 15:
        # scene.changed emits per repaint region, so a drag ran _update_totals'
        # full room scan dozens of times a second)
        self._update_totals()

        self._z_top = 0                  # running max-z for bring-to-front
        self._sync_floor_state()         # populate the Floors menu + status label

        # undo / redo: full-document snapshots captured after each change
        # settles (debounced), so every canvas operation is reversible
        self._undo_stack = []
        self._redo_stack = []
        self._restoring = False
        self._committed_state = self.snapshot()
        self._saved_state = self._committed_state   # last on-disk/new baseline
        self._conversion = None      # P2.1 report, set when a legacy file was
        self._provenance = None      # converted; provenance rides to P2.2's save
        self._doc_settings = {}      # document settings the walk does not model
        self._dirty_timer = QTimer(self)
        self._dirty_timer.setSingleShot(True)
        self._dirty_timer.setInterval(180)
        self._dirty_timer.timeout.connect(self._commit_if_changed)
        self._dirty_timer.timeout.connect(self._update_totals)   # debounced
        self.scene.changed.connect(self._mark_dirty)
        self.scene.selectionChanged.connect(self._sync_template_action)
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
            (TOOL_ROOF_RIDGE, "Roof Ridge", "G", "roof"),
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
        # the shuffle-mode toggle (P4.3). Text-only on purpose: a mode reads
        # better as a word than as one more pictogram, and it saves an asset
        self.a_shuffle = QAction("Shuffle", self)
        self.a_shuffle.setCheckable(True)
        self.a_shuffle.setChecked(bool(SETTINGS.get("shuffle", False)))
        self.a_shuffle.setShortcut("Ctrl+H")     # row 37: the ruled chord
        self.a_shuffle.setToolTip(
            "Shuffle mode: drag rooms freely -- nothing merges, welds or "
            "binds until you join a room explicitly  [Ctrl+H]")
        self.a_shuffle.toggled.connect(self._set_shuffle)
        shuffle_btn = QToolButton()
        shuffle_btn.setDefaultAction(self.a_shuffle)
        shuffle_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        tb.addWidget(shuffle_btn)

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
        m_file.addSeparator()
        a_save = QAction("&Save", self)
        a_save.setShortcut(QKeySequence.StandardKey.Save)
        a_save.triggered.connect(self.save_plan)
        m_file.addAction(a_save)
        a_saveas = QAction("Save &As…", self)
        a_saveas.setShortcut(QKeySequence.StandardKey.SaveAs)
        a_saveas.triggered.connect(self.save_plan_as)
        m_file.addAction(a_saveas)
        m_file.addSeparator()
        # THE EXPORT SUBMENU (0072-ruling.md §4, unblocked by 0116-ruling.md):
        # a REAL `addMenu`, not a label containing "▸" -- the DXF action's own
        # label carried a literal "▸" as plain text (0050-report.md flagged it
        # against itself, never ruled, until Patrick asked for exactly this).
        # Four entries, every existing slot keeping its name (re-parent, not a
        # rewrite) -- the two Import actions above are untouched, he asked
        # about exports.
        m_export = m_file.addMenu("&Export")
        a_exp = QAction("&Rooms as CSV…", self)
        a_exp.triggered.connect(self.export_rooms_csv)
        m_export.addAction(a_exp)
        a_dxf = QAction("&Chief Architect (DXF)…", self)  # handoff 0038
        a_dxf.triggered.connect(self.export_dxf)
        m_export.addAction(a_dxf)
        # PDF PLAN SET (0072-ruling.md §5 / 0116-ruling.md §2). `reportlab`
        # missing -> DISABLED WITH A REASON, not a crash (D40) -- checked with
        # `find_spec`, which does not execute reportlab's own code, only the
        # cheap "is it on disk" question the menu needs.
        a_pdf = QAction("&PDF plan set…", self)
        a_pdf.triggered.connect(self.export_pdf)
        if importlib.util.find_spec("reportlab") is None:
            a_pdf.setEnabled(False)
            a_pdf.setToolTip("reportlab is not installed; PDF export is "
                             "unavailable (pip install reportlab)")
        m_export.addAction(a_pdf)
        a_v4 = QAction("&Legacy v4…", self)            # one release, so nobody
        a_v4.triggered.connect(self.export_legacy_v4)   # is stranded on v5
        m_export.addAction(a_v4)
        m_file.addSeparator()
        a_tload = QAction("&Load template room…", self)   # P4.4
        a_tload.triggered.connect(self.load_template_room)
        m_file.addAction(a_tload)
        self.a_save_template = QAction("Sa&ve template room…", self)
        self.a_save_template.triggered.connect(self.save_template_room)
        self.a_save_template.setEnabled(False)   # only with a floating room
        self.a_save_template.setToolTip(
            "Save the selected FLOATING room as a one-room template")
        m_file.addAction(self.a_save_template)
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
        # PASTE ROOM, beside Paste (D53). "Copy room" lives on the ROOM's own
        # context menu; its partner used to live ONLY on the blank-canvas menu,
        # so on a plan that fills the canvas there was nowhere to invoke it --
        # and A1b widening the room menu made copy easier to reach while paste
        # stayed put. It is here so both halves sit on surfaces a user already
        # associates with copy and paste.
        #
        # DELIBERATELY NOT MERGED WITH Ctrl+V. `item_clipboard` and
        # `room_clipboard` are separate stores and joining them is a design
        # question this pass does not own -- filed as its own record.
        self.a_paste_room = QAction("Paste &room", self)
        self.a_paste_room.setShortcut(QKeySequence("Ctrl+Shift+V"))
        self.a_paste_room.triggered.connect(self.paste_room_here)
        m_edit.addAction(self.a_paste_room)
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
        a_gaps = QAction("Review wall gaps…", self)
        a_gaps.triggered.connect(self.review_wall_gaps)
        m_edit.addAction(a_gaps)
        a_ortho = QAction("Wall orthogonality report…", self)  # 0055-ruling.md item B
        a_ortho.triggered.connect(self.review_wall_orthogonality)
        m_edit.addAction(a_ortho)
        a_ortho_repair = QAction("Repair wall orthogonality…", self)  # 0066/0082 item C
        a_ortho_repair.triggered.connect(self.repair_wall_orthogonality)
        m_edit.addAction(a_ortho_repair)

        # A VIEW MENU, and 3D view is its first item (D53). It had NO menu-bar
        # entry, no shortcut and no toolbar button: `show_3d_view`'s only two
        # call sites were blank-canvas right-clicks, so on a plan that fills
        # the canvas the renderer was unreachable. It is NOT hung under Floors
        # -- `select_floor_popup`'s docstring is right that "a chord named
        # 'select a floor' should not offer a renderer", and that reasoning
        # applies to a menu as much as to a chord. Putting a renderer wherever
        # there was space is how it came to live on blank canvas.
        m_view = self.menuBar().addMenu("&View")
        self.a_3d = QAction("&3D view…", self)
        self.a_3d.setShortcut(QKeySequence("Ctrl+3"))
        self.a_3d.triggered.connect(self.show_3d_view)
        m_view.addAction(self.a_3d)

        m_rooms = self.menuBar().addMenu("&Rooms")
        a_concept = QAction("&New concept room…", self)      # P4.4
        a_concept.triggered.connect(lambda: self.new_concept_room())
        m_rooms.addAction(a_concept)
        m_rooms.addSeparator()
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

        # 0139-ruling.md's roofline plan, R2 (menu + ridge sketch + eaves
        # pick + a minimal heights dialog -- 0140-ruling.md sec3)
        m_roof = self.menuBar().addMenu("R&oof")
        a_ridge = QAction("&Sketch ridge  [G]", self)   # "G": the toolbar's own shortcut
        a_ridge.triggered.connect(lambda: self.set_tool(TOOL_ROOF_RIDGE))
        m_roof.addAction(a_ridge)

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

        # coalesce action enable/disable: a burst of selection changes (rubber-
        # band, select-all before Ctrl+G) fires selectionChanged many times;
        # apply once on the next event loop, like wheelEvent -> _apply_zoom.
        self._edit_actions_timer = QTimer(self)
        self._edit_actions_timer.setSingleShot(True)
        self._edit_actions_timer.setInterval(0)
        self._edit_actions_timer.timeout.connect(self._apply_edit_actions)
        self.scene.selectionChanged.connect(self._update_edit_actions)
        self._apply_edit_actions()            # initial state, synchronously

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
        self._sync_editing_ui()

    def _sync_editing_ui(self):
        """Point the toolbar's shuffle toggle at the document's flag. Called
        from `_apply_canvas` (legacy open / import / New) and from the bridge's
        v5 apply, which never reaches `_apply_canvas`; `_set_shuffle`'s
        same-value guard keeps the setChecked from echoing back into
        SETTINGS."""
        a = getattr(self, "a_shuffle", None)
        if a is not None:
            a.setChecked(bool(SETTINGS.get("shuffle", False)))

    def _set_shuffle(self, on):
        """The toolbar toggle -> the document's `settings.editing.shuffle`.
        Same-value guard: sync from a loaded document must not re-trigger."""
        on = bool(on)
        if bool(SETTINGS.get("shuffle", False)) == on:
            return
        SETTINGS["shuffle"] = on
        if on:
            # THE ONE RE-BASELINE EVENT (ruled 2026-08-03): entering shuffle
            # re-captures what each floating room holds -- what is inside it
            # NOW and unclaimed by a placed room is assigned to it; what it
            # already carried stays its own. Mid-shuffle a float never picks
            # up anything; only turning shuffle off and on again re-runs
            # this.
            from floorplanner.extract import (  # late: higher layer
                capture_floating_furnishings)
            for it in self.scene.items():
                if (isinstance(it, RoomItem)
                        and getattr(it, "placement_state", "placed")
                        == "floating"):
                    capture_floating_furnishings(self.scene, it)
        self._mark_dirty()               # settings are document state (saved)
        rec = getattr(self, "_recorder", None)
        if rec is not None:              # macro recorder: any route to a
            rec.on_shuffle(on)           # flip, as one absolute ^H token
        self.status("Shuffle mode ON: nothing merges, welds or binds -- "
                    "join rooms explicitly (right-click > Join room into "
                    "plan)." if on else
                    "Shuffle mode off: automatic joining passes re-enabled.")

    VIEWER_HINT = ("3D view needs pip install -r requirements-viewer.txt")

    def show_3d_view(self):
        """The 3D popup: render the CURRENT plan, modal, without touching it.

        READ-ONLY BY CONSTRUCTION, and that is the whole discipline here:
        the document comes from `design_document()` -- the same producer the
        save path writes, so there is no second definition of "what this plan
        is" -- and nothing downstream of it holds a scene reference. No file
        is written, no item is touched, and the dirty flag cannot move because
        nothing changes.

        The walk's warning channel is silenced for this call ON PURPOSE: an
        unwelded-end report belongs to the edit that tore the network, and the
        180 ms debounce walk owns that channel and will say so within a frame.
        A viewer that opens is not an edit and must not speak in the edit
        channel -- the same reasoning that keeps `active_floor` out of undo.
        (In a live window the weld baseline is already set by the snapshot in
        `__init__`, so this call cannot establish one either.)
        """
        import warnings
        try:
            from floorplanner.viewer.fp3d import build_model
            from floorplanner.viewer.fp3dq import Plan3DQuickWidget
        except ImportError:
            self.status(self.VIEWER_HINT)
            return None
        with warnings.catch_warnings():
            # SCOPED TO THE ONE MESSAGE, not a blanket ignore. Silencing the
            # whole call would swallow any OTHER warning the walk raises --
            # `except ValueError: continue` wearing a different hat, and the
            # exact family defect 6 spent a phase removing. Only the
            # unwelded-ends line is suppressed, and only because it belongs
            # to the edit that tore the network: the debounce walk owns that
            # channel and will say so within a frame.
            warnings.filterwarnings("ignore", message="design_from_scene:")
            doc = self.design_document()
        # D68: THE ACTIVE FLOOR ONLY, and the floor is read from the WINDOW,
        # not from `doc`. `active_floor` is deliberately VIEW STATE -- kept out
        # of `serialize()` so switching floors is neither undoable nor dirtying
        # -- so the document does not carry it and looking there is the wrong
        # path a fixer would take.
        #
        # THIS REMOVES A REACHABLE CAPABILITY, and that is acceptable HERE and
        # only here, because the capability is BROKEN. D11's z collapse means
        # every floor currently renders at ONE HEIGHT, so "see the whole
        # building" has never actually worked -- it produced a pile, not a
        # building. **This removes a misleading view, not a working one**, which
        # is the distinction PARASITIC REACH exists to make: the rule says
        # budget for what rests on a fault, and what rested on this one was an
        # image that lied.
        #
        # THE ESCAPE EXISTS MEANWHILE: the `fp3d` and `fp3dq` CLIs keep
        # `--level` and can still render everything. D69's control panel is
        # what restores the choice in the UI, and it restores it as a
        # `build_model` parameter (VIEWER_NOTES.md section 1), never as a mesh
        # filter.
        #
        # AND THE ID IS NOT THE NAME. `build_model(levels=…)` filters by level
        # **id** (`L1`, `L2`); `active_floor` is the level **name**
        # (`default`, `second`). Passing the name straight through matches
        # nothing and `build_model` renders an EMPTY MODEL with a note nobody
        # reads -- a silent blank window, which is worse than the defect. The
        # mapping is done here, and a floor with no matching level falls back to
        # the whole document rather than to nothing.
        want = [lv["id"] for lv in doc.get("levels", [])
                if lv.get("name") == self.active_floor] or None
        model = build_model(doc, levels=want)
        dlg = QDialog(self)
        dlg.setWindowTitle("3D view")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(0, 0, 0, 0)
        try:
            body = Plan3DQuickWidget(model, parent=dlg)
        except ImportError:          # Qt Quick 3D itself is the optional half
            dlg.deleteLater()
            self.status(self.VIEWER_HINT)
            return None
        except RuntimeError as exc:  # QML loaded but failed -- say which
            dlg.deleteLater()
            self.status(f"3D view could not load its scene: {exc}")
            return None
        lay.addWidget(body)
        dlg.resize(1100, 780)
        dlg.exec()
        return dlg

    def new_concept_room(self, at=None):
        """Rooms ▸ New concept room… (and the Room tool's blank-canvas menu):
        type a size, get a wall-less FLOATING room there (P4.4)."""
        dlg = ConceptRoomDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None
        name, w, d = dlg.values()
        if at is None:
            at = self.view.mapToScene(self.view.viewport().rect().center())
        room = make_concept_room(self.scene, name, w, d, at,
                                 floor=self.active_floor)
        self.status(f"Concept room '{room.name}' "
                    f"({w / FOOT:g}' x {d / FOOT:g}') — floating and "
                    "wall-less; drag it by its name.")
        return room

    def finish_roof_ridge(self, item, eaves_wall):
        """Roof ▸ Sketch ridge…'s second half: the ridge is drawn, an eaves
        wall is picked (0139-ruling.md R2 / 0140-ruling.md). The picked wall
        sets `item.span_in` (the 2D overlay's plan reach -- not a document
        field, see `RoofItem`'s docstring); the End-On dialog
        (0140-ruling.md's own "one dialog, two doors" -- this is the third:
        the ridge-sketch tool's own initial prompt) sets the two persisted
        heights. Cancelling drops the ridge entirely, same as an
        under-length wall drag."""
        item.span_in = eaves_span_from_wall(item.p1, item.p2, eaves_wall)
        item.rebuild()
        dlg = RoofEndOnDialog(item, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            self.scene.removeItem(item)
            self.status("Roof ridge cancelled.")
            return None
        dlg.apply()
        self.status(f"Roof ridge added ({fmt_ftin(item.length())} long, "
                    f"ridge {fmt_in(item.ridge_h_in)}, "
                    f"eaves {fmt_in(item.eaves_h_in)}).")
        return item

    def _sync_template_action(self):
        """File ▸ Save template room… is live only while exactly one FLOATING
        room is selected (P4.4's ruled rule -- and a structural one: only a
        floating room owns its walls outright, so only it can be cut out
        whole)."""
        a = getattr(self, "a_save_template", None)
        if a is not None:
            a.setEnabled(self.selected_floating_room() is not None)

    def toggle_shuffle(self):
        """Flip shuffle mode through the action, so the toolbar stays in
        sync -- the macro runner's ^H (bare) target."""
        self.a_shuffle.toggle()

    def set_shuffle_mode(self, on):
        """Set shuffle mode absolutely through the action -- the macro
        runner's '^H \"on\"/\"off\"' target."""
        self.a_shuffle.setChecked(bool(on))

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
                # a bordering room survives via its stored outline; the
                # vacated edge becomes an open edge (P4.1)
                delete_wall(self.scene, it, settle=False)
            elif isinstance(it, (RoomItem, FurnishingItem, GroupItem, RoofItem)):
                self.scene.removeItem(it)
        rebuild_all_walls(self.scene)

    # -- group / ungroup / cut / copy / paste -------------------------------------
    def _update_edit_actions(self):
        """On every selection change: keep the click-order list for subtract
        (cheap, so it stays synchronous and accurate) and schedule the action
        enable/disable pass. A burst of N selection changes coalesces into one
        _apply_edit_actions instead of N (was the biggest measured cost in the
        group workflow -- P0.3b select ratio 27, O(R^2*W) path booleans)."""
        sel = self.scene.selectedItems()
        selset = set(sel)
        order = getattr(self, "_sel_order", [])
        order = [it for it in order if it in selset]
        for it in sel:
            if it not in order:
                order.append(it)
        self._sel_order = order
        if not self._edit_actions_timer.isActive():
            self._edit_actions_timer.start()

    def _apply_edit_actions(self):
        """Enable/disable Group / Ungroup / room-op / align / distribute from a
        cheap COUNT over the selection -- never by building shape specs. Group
        needs 2+ groupables; Ungroup a group; room ops exactly two shapes.

        A "shape" is a directly-selected room (with corners) or a selected group
        (which may enclose a room or be a wall-loop). Counting groups without
        resolving them can over-enable a room op when a selected group encloses
        nothing -- harmless, because every room op re-validates via
        _selected_room_shapes() when it actually fires and no-ops on a bad count.
        This replaces a per-change len(self._selected_room_shapes()) that ran
        bounding_walls() per room and group_room() per group just to take a length."""
        sel = self.scene.selectedItems()
        n = sum(1 for it in sel
                if isinstance(it, (WallItem, FurnishingItem, GroupItem)))
        self.a_group.setEnabled(n >= 2)
        self.a_ungroup.setEnabled(
            any(isinstance(it, GroupItem) for it in sel))
        n_shapes = sum(1 for it in sel
                       if (isinstance(it, RoomItem) and it.corners)
                       or isinstance(it, GroupItem))
        for a in getattr(self, "_room_op_actions", []):
            a.setEnabled(n_shapes == 2)
        if hasattr(self, "a_align"):
            self.a_align.setEnabled(n_shapes >= 1)
        for a in getattr(self, "_distribute_actions", []):
            a.setEnabled(n_shapes >= 3)
        walls = [it for it in sel if isinstance(it, WallItem)]
        if hasattr(self, "wall_label"):
            self.wall_label.setText(self._wall_label_text(walls))

    #: 0094-ruling.md sec3: below this, a deviation is float noise from the
    #: angle snap's own round trip (~4e-15deg, measured), not a real drift
    #: -- five orders of magnitude above the noise, five below the smallest
    #: real corpus drift on record (2.04e-4deg, 0066-ruling.md sec2). There
    #: is no value in that gap and nothing physical lands there.
    ANGLE_CLAUSE_TOL_DEG = 1e-9

    @staticmethod
    def _angle_snap_step_deg() -> float:
        """0093-ruling.md sec2: the wall label's intended-angle grid is
        `SETTINGS["rotate_snap_deg"]` -- the SAME increment `_angle_snapped_
        target` (walls.py) already snaps Ctrl-drags to, deliberately reused
        rather than a second setting meaning the same thing. Falls back to
        90 (cardinals only, today's behaviour) unless the configured step
        divides 90 exactly -- an arbitrary step (the spin box allows 1-90)
        would otherwise make every vertical wall in the plan report a false
        "6deg off axis" at, say, a 7deg step. Never fails, never warns: a
        furnishing-rotation setting must not make the wall label wrong."""
        step = SETTINGS.get("rotate_snap_deg", ROTATE_SNAP_DEFAULT)
        if step <= 0 or abs(round(90.0 / step) * step - 90.0) > 1e-9:
            return 90.0
        return step

    @staticmethod
    def _wall_label_text(walls) -> str:
        """The selected wall's id, its two vertices' id + (x, y) in decimal
        feet (fixed 2 decimals -- 0065-ruling.md sec4), its length, and its
        angle -- for the status bar. Empty unless exactly one wall is
        selected.

        THE ANGLE CLAUSE FIRES IFF THE WALL IS NOT ON AN INTENDED ANGLE
        (0093-ruling.md sec1) -- deviation from the nearest multiple of
        `_angle_snap_step_deg()`, not from the nearest cardinal, so a
        deliberate 45deg wall (itself a multiple of the default 15deg step)
        says nothing at all, heading included (0093 sec5). When it fires,
        BOTH numbers show (0092-ruling.md, closing 0068 sec4): the heading
        at fixed decimals (an absolute bearing, useful precision does not
        scale with size) and the deviation at significant figures (a small
        relative quantity) -- the pair is what makes it honest, since a
        fixed-decimal heading alone can still round to a false cardinal
        below `ANGLE_CLAUSE_TOL_DEG`, and the deviation beside it never
        reads as exactly zero for a real one."""
        if len(walls) != 1:
            return ""
        w = walls[0]
        p1, p2 = w.p1, w.p2
        text = (f"Wall {w.uid}: {w.v1}({fmt_ft2(p1.x())}, {fmt_ft2(p1.y())})ft"
                f" -> {w.v2}({fmt_ft2(p2.x())}, {fmt_ft2(p2.y())})ft"
                f"  len {fmt_ft2(w.length())}ft")
        heading = heading_deg(p1, p2)
        if heading is not None:
            step = MainWindow._angle_snap_step_deg()
            remainder = heading % step
            deviation = min(remainder, step - remainder)
            if deviation > MainWindow.ANGLE_CLAUSE_TOL_DEG:
                text += f"  angle {heading:.4f}deg ({deviation:.3g}deg off axis)"
        return text

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
        # RELOCATE the corners; do not assign coordinates. Assigning `p1`/`p2`
        # splits on write, so every wall end came away on a fresh vertex and
        # the outline was left holding the old ones -- measured at P4.5, all
        # four walls of a room snapped to the grid and its outline stayed
        # entirely off it. `relocate_corners` also widens the gather to every
        # room in the scene holding a corner being moved, which is what stops
        # the party-wall neighbour tearing (it deforms instead, ruling 2a).
        rooms = [s["room"] for s in shapes if s["room"] is not None]
        relocate_corners(walls, rooms,
                         lambda v: grid_snap(v.point(), step), self.scene)
        rebuild_all_walls(self.scene)
        self.status(f"Aligned {len(shapes)} room(s) to the "
                    f'{step:g}" grid.')

    def _translate_shape(self, shape, dx, dy):
        """Rigidly shift a room shape (its walls and, if any, its region).

        SAME CORRECTION AS `align_rooms_to_grid`, and it was the more damaging
        of the two: this used to assign `p1`/`p2` AND rebuild the room's corner
        list from fresh `QPointF`s, so the two agreed numerically and shared
        nothing. Measured at P4.5 on a row of three rooms, outline-to-wall
        corner sharing went 4-of-4 to 0-of-4 on EVERY room -- **while
        Distribute moved them by zero**, because assigning the same coordinate
        still mints a vertex. The room looked right and the next wall drag
        stranded it (defect 22's shape, arriving through a different door)."""
        r = shape["room"]
        relocate_corners(shape["walls"], [r] if r is not None else [],
                         lambda v: QPointF(v.x + dx, v.y + dy), self.scene)
        if r is not None:
            r.prepareGeometryChange()
            r.anchor = QPointF(r.anchor.x() + dx, r.anchor.y() + dy)
            if not r.outline:     # outline-less: the stored path IS the region
                r.set_region(QTransform.fromTranslate(dx, dy).map(r.path),
                             r.area_sqft, None)
            r.update()

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
        were moved away), then re-attach the survivors to their walls.

        P3.5: the second half used to be a re-detection sweep (`refresh_rooms`)
        that this command merely triggered on demand. Regions now derive from
        their outlines, so there is nothing to re-detect -- what a user still
        wants from this menu item is the ORPHAN SWEEP above plus a re-bind, and
        that is what it does."""
        sc = self.scene
        removed = 0
        # only the active floor: room_walled tests against active-floor walls, so
        # a room parked on another floor would look unwalled and be wrongly
        # deleted (defect 2).
        rooms = [it for it in sc.items()
                 if isinstance(it, RoomItem) and it.floor == self.active_floor]
        for it in rooms:
            if not room_walled(sc, it):
                sc.removeItem(it)
                removed += 1
        for it in rooms:
            if it.scene() is not None:
                bind_room_walls(sc, it, settle=False)
        rebuild_all_walls(sc)
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
                # the room's OWN walls, off its outline -- not every wall
                # whose body touches its boundary band. `bounding_walls()` is a
                # proximity query with no floor filter, so it picks up the
                # neighbour's walls and other floors' walls too, and
                # `room_boolean` DELETES what it is handed (defect 8).
                shape = {"corners": [QPointF(c) for c in it.corners],
                         "name": it.name, "props": dict(it.properties),
                         "walls": room_walls(it),
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

    @staticmethod
    def _source_edge(a, b, sources, default_floor):
        """(wall_type, floor) for a result edge a->b, from whichever input wall
        runs along it -- exterior wins a tie, so a combine cannot downgrade an
        exterior wall to an interior one. `("interior", default_floor)` for an
        edge no input covers, which for a boolean result is a genuinely new
        edge and not a lost one."""
        L = QLineF(a, b).length()
        if L < 1e-6:
            return "interior", default_floor
        ux, uy = (b.x() - a.x()) / L, (b.y() - a.y()) / L
        best = None
        for p1, p2, kind, fl in sources:
            ss = []
            for p in (p1, p2):
                vx, vy = p.x() - a.x(), p.y() - a.y()
                if abs(vy * ux - vx * uy) > 1.5:
                    break
                ss.append(vx * ux + vy * uy)
            if len(ss) != 2:
                continue
            lo, hi = max(0.0, min(ss)), min(L, max(ss))
            if hi - lo < 1.0:
                continue
            key = (kind != "exterior", -(hi - lo))
            if best is None or key < best[0]:
                best = (key, kind, fl)
        return (best[1], best[2]) if best else ("interior", default_floor)

    def room_boolean(self, op: str):
        """Boolean op on the two selected rooms' OUTLINE polygons.

        combine = union, intersect = overlap only, subtract = first room
        minus second (selection order), fragment = the three pieces
        (first-only, second-only, overlap).  The two rooms may be selected
        directly, via their groups, or as grouped wall-loops.  The inputs
        and their walls are replaced by freshly walled result rooms.

        DEFECT 8, closed at P3.5, and it was two faults in one operation:

          * IT DELETED WALLS THAT WERE NOT ITS OWN. The inputs' walls came from
            `bounding_walls()`, a proximity query over the whole scene with no
            floor filter -- so a neighbouring room's shared wall, and any wall
            of any other floor whose body happened to touch the band, was
            removed along with the inputs. They now come from each room's
            outline (`room_walls`), which is the definition of "this room's
            walls", and a wall still bordering another room is kept.
          * IT FORCED EVERY RESULT WALL TO `"interior"`. An exterior wall came
            back as a 4.5" interior one after a combine. Each result edge now
            inherits the type (and floor) of whichever input wall runs along it,
            falling back to interior only for an edge no input wall covers --
            which, for a boolean, is a genuinely new edge.

        Both were possible because the operation worked from a re-traced
        boundary rather than from what the rooms said they were made of."""
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

        # remember what the inputs were made of BEFORE removing them, so the
        # result walls can inherit type and floor per edge instead of being
        # forced to interior (defect 8, second half)
        sources = [(QPointF(w.p1), QPointF(w.p2), w.wall_type, w.floor)
                   for w in list(s1["walls"]) + list(s2["walls"])]
        src_room = s1["room"] or s2["room"]
        floor = src_room.floor if src_room is not None else self.active_floor

        # drop the input rooms and the walls that defined them
        old_walls = set(s1["walls"]) | set(s2["walls"])
        for s in (s1, s2):
            if s["room"] is not None and s["room"].scene() is not None:
                sc.removeItem(s["room"])
        for w in old_walls:
            # a wall still bordering a room that is NOT an input is that room's
            # too; deleting it would break a bystander open (defect 8)
            keep = [r for r in w.rooms
                    if r is not s1["room"] and r is not s2["room"]]
            if w.scene() is not None and not keep:
                sc.removeItem(w)

        # gather result sub-polygons
        regions = []
        for path, base, props in results:
            for poly in path.simplified().toSubpathPolygons():
                corners = simplify_corners(poly)
                if len(corners) >= 3 and poly_area_sqft(corners) >= 1.0:
                    regions.append((corners, base, props))
        # A COMPLETE WALL LOOP FOR EVERY REGION -- shared edges deliberately
        # get a wall per region, with no dedup. That was written to make each
        # fragment "own all its walls" and, on its own, it did not: ownership
        # is a binding question, and `bind_room_walls` binds by geometry, so a
        # room could end up bound to a neighbour's coincident copy (D47).
        #
        # It is KEPT, because it is exactly the shape `extract_room` wants. A
        # private loop per region means extraction finds nothing shared and
        # nothing over-long, so it keeps every wall whole and copies none --
        # the loops stop being duplicates the moment each one belongs to a
        # floating room that is the only thing referencing it.
        region_walls = []
        for corners, _, _ in regions:
            ws, n = [], len(corners)
            for j in range(n):
                a, b = corners[j], corners[(j + 1) % n]
                if QLineF(a, b).length() >= MIN_WALL_LEN:
                    kind, fl = self._source_edge(a, b, sources, floor)
                    w = WallItem(QPointF(a), QPointF(b), kind)
                    w.floor = fl
                    sc.addItem(w)
                    ws.append(w)
            region_walls.append(ws)
        rebuild_all_walls(sc)

        # detect + create the result rooms; for fragment, EXTRACT each piece
        # so it is a floating, self-contained unit (D47)
        from floorplanner.extract import extract_room   # late: higher layer
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
            if op == "fragment":
                self._claim_region_walls(room, ws)
            created += 1
            if op == "fragment":
                # D47: A FRAGMENT IS A FLOATING ROOM, NOT A GROUP OF WALLS.
                #
                # This used to build a `GroupItem` over the region's own walls
                # so the piece "moves as a self-contained, fully-enclosed
                # unit". That comment describes P4.2's floating room, and it
                # was written before `extract` existed -- so it named the right
                # property and reached for the only mechanism there was.
                #
                # The group could never deliver it. `bind_room_walls` binds by
                # GEOMETRY, and every shared edge here carries one wall per
                # region, so a room could be bound to a NEIGHBOUR's coincident
                # copy: `room_owns_walls` was false for all nine (group, room)
                # pairs, and dragging a piece moved 4 of 4 walls and 0 of 16
                # outline corners -- the room stranded whole, with dashed
                # "open" edges that each had a real wall lying on them.
                #
                # `extract_room` is the mechanism that was missing: it makes
                # every edge's wall the room's OWN (copy-trimming anything
                # shared), privatises the corners an outside wall still
                # touches, folds outline and walls onto one vertex per corner,
                # and flips the state. The result is I12 by construction -- a
                # unit that is self-contained because nothing else references
                # its geometry, rather than because a group says so.
                extract_room(sc, room)
            else:
                room.setSelected(True)
        self.status(f"{op.title()}: {name1} + {name2} -> {created} room(s).")

    @staticmethod
    def _claim_region_walls(room, ws):
        """Point every outline edge at the wall THIS region built for it.

        D47. `bind_room_walls` binds by GEOMETRY, and `fragment` deliberately
        builds one wall per region, so on a shared edge there are two or three
        coincident candidates and the room can be bound to a NEIGHBOUR's copy.
        That is the whole mechanism of the defect, and it survives extraction:
        `extract_room` then sees a wall it must copy-trim (another room is on
        it), mints a copy, and leaves the original bound to nobody -- measured,
        4 orphan walls on the two-room case.

        So the region's own loop is asserted here, before extraction, by
        matching each outline edge to the wall spanning it FROM THIS REGION'S
        LIST ONLY. Geometry still decides which wall covers which edge -- the
        candidate set is what narrows.
        """
        tol = 0.01
        for e, nxt in zip(room.outline, room.outline[1:] + room.outline[:1],
                          strict=True):
            a, b = e.p, nxt.p
            for w in ws:
                p1, p2 = w.p1, w.p2
                fwd = (QLineF(p1, a).length() < tol
                       and QLineF(p2, b).length() < tol)
                rev = (QLineF(p1, b).length() < tol
                       and QLineF(p2, a).length() < tol)
                if fwd or rev:
                    if e.wall is not w:
                        if e.wall is not None:
                            room.unbind_wall(e.wall)
                        e.wall = w
                        room.bind_wall(w)
                    break

    def group_selected(self):
        """Group the selected walls/furnishings (existing groups merge).  When a
        room is selected, its surrounding + interior walls are DUPLICATED into
        the group (the originals stay put) so the group is a movable/copyable
        copy of the room."""
        selected = list(self.scene.selectedItems())
        # walls the user selected directly ride into the group as themselves;
        # a room's walls are duplicated EXCEPT any already selected this way, so
        # selecting a room together with its walls doesn't make a coincident
        # copy of every edge (which bloated the wall count until ungroup).
        # P4.5: A GROUP NEVER COPIES ANYTHING. The schema says so in as many
        # words -- "moving it translates the vertices its members reference
        # plus its member furnishings; rooms are the durable unit" -- and
        # `duplicate_wall` is deleted. A selected room contributes its REAL
        # walls, so there is nothing to reconcile afterwards: no coincident
        # copies to merge on ungroup, no `room_owns_walls` reading false
        # against a group of clones, and no wall count that grows with every
        # group/move/ungroup cycle. `seen` now guards against adopting one
        # wall twice (two selected rooms share a party wall) rather than
        # against copying it twice.
        seen = {id(it) for it in selected if isinstance(it, WallItem)}
        members, old_groups = [], []
        for it in selected:
            if isinstance(it, GroupItem):
                old_groups.append(it)
            elif isinstance(it, (WallItem, FurnishingItem)):
                members.append(it)
            elif isinstance(it, RoomItem):
                for w in room_walls(it) + it.interior_walls():
                    if not isinstance(w, WallItem) or id(w) in seen:
                        continue
                    seen.add(id(w))
                    members.append(w)
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
        # REMOVED AT P4.5, exactly as the task line called for ("no
        # duplicate_wall, no coalesce_all on ungroup"). The merge existed to
        # clean up the COPIES grouping used to make; with nothing duplicated
        # there is nothing to clean.
        #
        # WHAT IT ACTUALLY COST, measured on the pre-P4.5 tree rather than
        # assumed: it is PLAN-WIDE, so it re-decomposed walls no gesture had
        # touched -- symmetricP1 80 -> 78 items, planc1TestV5 82 -> 78,
        # planc1.v5 83 -> 80. But the SAVED FILE is byte-identical across it
        # on all three -- measured on `design_document()`, the producer
        # `_write_plan` writes, and on the literal `json.dump` output, not
        # only on `snapshot()`: those are collinear same-type segments the
        # walk planarises to the same thing, and wall count is presentation
        # state (P2.3). So NO GEOMETRY WAS EVER LOST -- what was wrong is that a
        # local gesture silently reshaped the whole plan's item structure,
        # which breaks "the group moves and nothing else changes" and makes
        # undo steps that look bigger than the edit.
        rebuild_all_walls(self.scene)     # rooms re-derive region/outline
        self.status("Ungrouped — items left in place.")

    def coalesce_all_now(self, interactive=True):
        """Edit ▸ Coalesce all walls now: the explicit plan-wide normalization.

        The COMMAND outlives the implementation it was named after (P3.4 (iii)).
        Same menu item, same user intent -- tidy my walls -- new machinery:
        merge every collinear run, then weld the junctions into shared
        vertices. Still forced even when auto-coalesce is switched off."""
        merged, _moved, _shared, split = normalize_walls(self.scene)

        # THE OUTLINE HALF (D61 stage 2a). The wall pass above dissolves a
        # vertex and the ROOM OUTLINE goes on naming it -- measured on a real
        # plan, 103 walls / 26 collinear -> 81 / 3 while the outlines stayed at
        # 159 corners, 69 of them redundant, before and after. That is the half
        # the user sees as "a straight run carrying a dozen handles".
        #
        # DRY RUN FIRST, ALWAYS. The numbers are shown before anything is
        # touched; `interactive=False` takes the applied path without a modal,
        # for tests and macros.
        from floorplanner.rooms import coalesce_outline_corners   # late
        plan = coalesce_outline_corners(self.scene, dry_run=True)
        removed = 0
        if plan["removed"]:
            worst = sorted(((v["removable"], k) for k, v in plan["rooms"].items()
                            if v["removable"]), reverse=True)[:4]
            detail = ", ".join(f"{name} {n}" for n, name in worst)
            ok = True
            if interactive:
                ok = QMessageBox.question(
                    self, "Coalesce room outlines",
                    f"Remove {plan['removed']} redundant outline corner(s) "
                    f"from {len(worst)}+ room(s)?\n\n{detail}\n\n"
                    f"({plan['paths']['exact']} exact on the grid, "
                    f"{plan['paths']['tolerance']} by angle.)\n"
                    f"Largest area change: {plan['max_area_delta_sqft']:.4f} "
                    f"sq ft (bound {plan['area_bound_sqft']} — "
                    f"{plan['refused']['area_would_move']} refused for "
                    f"exceeding it).\nUndo restores the plan.",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                ) == QMessageBox.StandardButton.Yes
            if ok:
                removed = coalesce_outline_corners(
                    self.scene, dry_run=False)["removed"]

        rebuild_all_walls(self.scene)
        msg = (f"Coalesced {merged} overlapping wall(s) and welded junctions."
               if merged else "Welded wall junctions.")
        if split:
            msg += f" Split {split} wall(s) at junctions."
        if removed:
            msg += f" Dissolved {removed} redundant outline corner(s)."
        self.status(msg)

    def review_wall_gaps(self):
        """Edit ▸ Review wall gaps… -- defect 34's REVIEW, deliberately not a
        repair. Lists the document's near-vertex pairs in the (0.6", 9.0")
        band; the user closes chosen pairs one at a time. A deliberate 6"
        reveal left alone stays exactly as drawn."""
        GapReviewDialog(self).exec()

    def review_wall_orthogonality(self):
        """Edit ▸ Wall orthogonality report… -- 0055-ruling.md item B, a
        REPORT, not a repair. Names every wall off axis and by how much;
        does not decide which are deliberate diagonals and which are drift,
        and nothing in it changes a wall's angle (item C, unruled)."""
        OrthogonalityReportDialog(self).exec()

    def repair_wall_orthogonality(self):
        """Edit ▸ Repair wall orthogonality… -- 0066-ruling.md item C,
        unblocked by 0082-ruling.md. Previews, applies as one undoable
        operation on Apply, never runs automatically (0066 sec5)."""
        OrthogonalityRepairDialog(self).exec()

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

    def _verify_or_report(self, where, **kw):
        """Run shadow mode, and REPORT a violation instead of dying of it.

        DEFECT 26. `verify()` raises by design, and that is right -- a genuine
        invariant violation must not pass silently. What is wrong is WHERE the
        raise lands: every one of this app's three `verify()` call sites is
        reachable from a Qt callback (the dirty timer, menu actions for
        undo/redo, image import, floor ops and save), and since PyQt 5.5 an
        exception escaping a C++ -> Python callback goes to `sys.excepthook` and
        then `qFatal()`, which calls `abort()`. So a violation found at a
        quiescent point KILLED THE PROCESS -- on Windows, in a GUI session, the
        user loses their work.

        The catch is deliberately narrow: `DesignVerificationError` ONLY. A
        blanket `except Exception` here would be the `except ValueError:
        continue` disease at application scale, hiding real faults behind the
        thing that was meant to surface them. Anything else still propagates.

        Said once, per the R5 wording standard: shadow mode fires at every
        quiescent point, so an unchanged message would repeat on every timer
        tick.

        Returns True when clean. The caller decides what a violation MEANS --
        the edit path carries on (the edit already happened), the save path
        still refuses to write. Only the fatality was the bug; the refusal is a
        deliberate data-integrity decision that predates this fix."""
        try:
            verify(self, where, **kw)
            return True
        except DesignVerificationError as exc:
            self._persist_verify_corpse(where, exc, kw)
            msg = f"Shadow mode: {exc}"
            if msg != getattr(self, "_last_verify_report", None):
                self._last_verify_report = msg
                self.status(msg)
            return False

    def _persist_verify_corpse(self, where, exc, kw):
        """Write everything about a caught violation to disk, then carry on.

        THE GUARD MAKES THIS NEARLY FREE, and that is the point. Before defect
        26's fix a violation ended the process and took its own evidence with
        it; now every catch can pay a permanent artifact instead. At a rate of
        ~2 deep runs in 10, each run is a lottery ticket, and one win yields the
        exact document, the exact rooms and the exact call path -- examinable
        offline, forever, instead of a race to re-observe.

        Recorded: the failing `Design`, the accepted baseline, the full
        violation list, and the PROVENANCE -- a real Python stack, because
        `where` only says "operation" or "save" and there are seven callback
        paths into three call sites (defect 26's audit). The stack says which.

        Never raises. Evidence-gathering that can itself fail the operation
        would be a second defect 26."""
        import datetime
        import json
        import os
        import tempfile
        import traceback
        try:
            root = os.environ.get("FP_VERIFY_DUMP") or os.path.join(
                tempfile.gettempdir(), "floorplanner-verify")
            os.makedirs(root, exist_ok=True)
            doc = kw.get("doc")
            if doc is None:
                doc = self.snapshot()
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            payload = {
                "when": stamp,
                "where": where,
                "error": str(exc),
                "baseline": getattr(self, VERIFY_BASELINE_ATTR, None),
                "violations": check(doc, deep=True),
                "provenance": traceback.format_stack()[-14:],
                # defect 28: is this window still the LIVE one, or a corpse of
                # an earlier test whose dirty timer never stopped?
                "window": {
                    "id": id(self),
                    "visible": bool(self.isVisible()),
                    "timer_active": bool(self._dirty_timer.isActive()),
                    "live_mainwindows": sum(
                        1 for w in QApplication.topLevelWidgets()
                        if type(w).__name__ == "MainWindow"),
                    "title": self.windowTitle(),
                },
                "document": doc,
            }
            path = os.path.join(root, f"verify-{stamp}.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=1, default=str)
        except Exception:                     # evidence must never break the app
            pass

    def _commit_if_changed(self):
        """Snapshot the plan as one undo step if it differs from the last
        committed state."""
        if self._restoring:
            return
        # R5, EDIT SURFACE: an opening an edit could not place is reported at
        # the quiescent point, naming the edit that dropped it, and SAID ONCE --
        # the 06c2145 wording standard. Eight sites used to swallow these with
        # `except ValueError: continue` (defect 6); they now file into one
        # vocabulary and this is where the edit half of it reaches a human.
        failed = drain_opening_failures(self.scene)
        if failed and failed != getattr(self, "_last_opening_report", None):
            self._last_opening_report = failed
            head = failed[0]
            more = f" (+{len(failed) - 1} more)" if len(failed) > 1 else ""
            self.status(f"Could not place {head}{more}")
        # Defect 25's gesture arm (P4.1b): the same discipline, its own head
        # -- nothing failed to be placed, so "Could not place" would misblame
        # a door that is fine. The filed sentence is complete on its own.
        # Drained after the opening report so the gesture the user just made
        # wins the status bar when both fire at one quiescent point.
        faults = drain_gesture_faults(self.scene)
        if faults and faults != getattr(self, "_last_gesture_report", None):
            self._last_gesture_report = faults
            more = f" (+{len(faults) - 1} more)" if len(faults) > 1 else ""
            self.status(f"{faults[0]}{more}")
        # ONE walk, shared: the snapshot and the shadow-mode check happen at
        # the same quiescent point, and walking the scene twice here would
        # double the per-edit cost for nothing.
        rep = {}
        state = self.snapshot(report=rep)
        self.verify_settled(doc=state, walk_report=rep)
        if state == self._committed_state:
            return
        self._undo_stack.append(self._committed_state)
        if len(self._undo_stack) > self.UNDO_LIMIT:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._committed_state = state
        self._update_undo_actions()

    def verify_settled(self, doc=None, walk_report=None):
        """P6.a — THE PER-MUTATION INVARIANT HOOK, ON ITS OWN NAME.

        **P1.6 shadow mode: a settled operation is exactly where the document
        must be consistent, so this is the per-mutation hook.** Cheap twelve
        only — an O(n^2) sweep per edit would make the app unusable.

        WHY IT IS A METHOD RATHER THAN THREE LINES INSIDE `_commit_if_changed`,
        which is where it lived until 2026‑08‑11. Read-back 0008 measured what
        `snapshot()`'s eight callers actually protect, and found that
        `_commit_if_changed` **is not an undo function**: it is this
        application's ONLY per-mutation invariant trigger, wearing undo's
        clothes. Phase 6 retires snapshot undo — and retiring it naively would
        have taken `FP_VERIFY_DESIGN` down with it, silently, because nothing in
        the plan said the two were the same call site.

        **So the hook is separated FIRST and ALONE, before any command exists.**
        It is the thing that dies quietly, and doing it first means the cutover
        cannot take it with it. The debounce still calls it — that is the
        settled-operation boundary and P6.b keeps it — but the dependency now
        runs the other way: shadow mode does not need undo to exist.

        `doc` and `walk_report` are passed when the caller has already walked
        the scene, so the shared-walk saving that motivated the original
        inlining is kept. A caller with nothing to share may pass neither.
        """
        return self._verify_or_report("operation", doc=doc,
                                      walk_report=walk_report)

    def _restore_state(self, state):
        self._dirty_timer.stop()
        self._restoring = True
        try:
            self.load_data(state, keep_backdrop=True)   # undo keeps the backdrop
        finally:
            self._restoring = False
        self._committed_state = self.snapshot()
        self._update_undo_actions()

    def _reset_undo(self):
        """Drop the history (after New / Open): the current plan becomes the
        baseline state."""
        self._dirty_timer.stop()
        self._z_top = 0
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._committed_state = self.snapshot()
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
                except ValueError as exc:
                    report_opening_failure(self.scene, wall, od["kind"],
                                           od["code"], od["s"],
                                           f"{exc} (pasting)")
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


    def _headless(self) -> bool:
        """True under the offscreen Qt platform (tests): skip modal dialogs."""
        return QApplication.platformName() == "offscreen"


    def closeEvent(self, e):
        # no prompt when there is no interactive UI (headless/offscreen tests),
        # otherwise the modal save dialog would block on close
        headless = QApplication.platformName() == "offscreen"
        if headless or self._confirm_discard_changes("Quit Floor Planner"):
            # DEFECT 29. A closed window went on walking the WHOLE document
            # every 180 ms -- snapshotting it, verifying it, and (before defect
            # 26's guard) able to abort the process from it. Close one plan
            # window with another still open and you paid that cost forever,
            # invisibly, for a window you believe is gone.
            #
            # Stopped only once the close is ACCEPTED: a close the user cancels
            # must leave the window exactly as it was, debounce included, or
            # the edit in flight when they hit the X never becomes an undo step.
            self._dirty_timer.stop()
            e.accept()
        else:
            e.ignore()


    # -- save / load -------------------------------------------------------------






    # -- floor operations -----------------------------------------------------

















    def paste_room_here(self):
        """Edit ▸ Paste room (Ctrl+Shift+V) -- paste at the mouse, or the centre.

        `paste_room` wants a LOCATION, which is why it lived on the canvas menu:
        a right-click carries a point and a menu-bar action does not. This
        resolves one the same way `paste_clipboard` does -- the last scene
        position the view saw, falling back to the viewport centre -- so the
        keyboard route lands where the user is looking.
        """
        if not self.room_clipboard:
            self.status("No room copied -- right-click a room and Copy room "
                        "first.")
            return
        at = self.view._last_scene
        if at is None:
            at = self.view.mapToScene(self.view.viewport().rect().center())
        self.paste_room(grid_snap(at))

    def paste_room(self, sp: QPointF):
        """Paste the copied room, centred on `sp`, as a FLOATING room.

        P4.4: the clipboard holds a one-room TEMPLATE DOCUMENT, so paste is
        `insert_room_template` -- the same operation File > Load template room
        performs, with a clipboard instead of a file in the middle. It arrives
        floating because it has joined nothing yet; right-click > Join room
        into plan (or drop it outside shuffle mode) places it.
        """
        if not self.room_clipboard:
            return
        room = self.insert_room_template(self.room_clipboard, at=sp)
        if room is None:
            self.status("Could not paste the room.")
            return
        self.status(f"Pasted room '{room.name}' -- it is FLOATING: drag it "
                    "by its name, then right-click it to join it in.")

    # -- CSV room import ----------------------------------------------------------



    # -- import a plan from a PNG image (preview -> accept) -------------------



    # -- interactive image backdrop: place, calibrate, extract ---------------










    # -- headless / macro hooks ----------------------------------------------
    # These let an external driver (fp_macro.py) load, edit, snapshot and save
    # a plan with no dialogs.  See docs/macro_language.md for the macro syntax.






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
