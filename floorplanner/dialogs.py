"""Modal dialogs (inventory, room properties, settings, image import, AI
pricing, about) and the inventory row/TSV helpers that feed them."""
import os

from PyQt6 import sip  # noqa: F401
from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import *  # noqa: F401

from floorplanner.config import *  # noqa: F401
from floorplanner.geometry import *  # noqa: F401
from floorplanner.catalog import *  # noqa: F401
from floorplanner.walls import *  # noqa: F401
from floorplanner.rooms import *  # noqa: F401
from floorplanner.items import *  # noqa: F401

class GapReviewDialog(QDialog):
    """DEFECT 34's review (P4.2): LIST the document's near-vertex gaps in the
    (vertex_weld_in, join_tol_in) band with their distances, and let the user
    close the ones they did not intend -- one pair at a time, explicitly.
    Nothing auto-closes: a deliberate reveal is legitimate design (the schema
    says so in as many words), and nothing here can tell a reveal from a
    mistake. Same discipline as P2.1's conversion report: report to a human,
    repair only on their say-so."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Review wall gaps")
        self.resize(520, 340)
        lay = QVBoxLayout(self)
        self.info = QLabel()
        self.info.setWordWrap(True)
        lay.addWidget(self.info)
        self.listw = QListWidget()
        lay.addWidget(self.listw)
        row = QHBoxLayout()
        self.b_close = QPushButton("Close selected gap")
        self.b_close.clicked.connect(self._close_selected)
        row.addWidget(self.b_close)
        b_done = QPushButton("Done")
        b_done.clicked.connect(self.accept)
        row.addWidget(b_done)
        lay.addLayout(row)
        self.refresh()

    def refresh(self):
        import warnings
        from floorplanner.design.bridge import design_from_scene
        from floorplanner.design.validate import near_vertex_gaps
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            doc = design_from_scene(self.win).to_dict()
        self._levels = {lv["id"]: lv["name"] for lv in doc.get("levels", [])}
        self.gaps = near_vertex_gaps(doc)
        self.listw.clear()
        for lvl, a, b, dist in self.gaps:
            self.listw.addItem(
                f"{self._levels.get(lvl, lvl)}: "
                f"({fmt_ftin(a[0])}, {fmt_ftin(a[1])}) and "
                f"({fmt_ftin(b[0])}, {fmt_ftin(b[1])}) are {dist:.2f}\" apart")
        if self.gaps:
            self.info.setText(
                f"{len(self.gaps)} pair(s) of corners sit close together "
                f"without sharing a corner. Some may be deliberate (a "
                f"reveal, a pilaster gap) -- those need no action. Closing "
                f"a gap welds the two corners into one, at the first point.")
            self.listw.setCurrentRow(0)
        else:
            self.info.setText("No near-vertex gaps -- every pair of corners "
                              "is either welded or genuinely apart.")
        self.b_close.setEnabled(bool(self.gaps))

    def _close_selected(self):
        i = self.listw.currentRow()
        if i < 0 or i >= len(self.gaps):
            return
        lvl, a, b, dist = self.gaps[i]
        n = close_gap(self.win.scene, QPointF(*a), QPointF(*b),
                      floor=self._levels.get(lvl))
        self.win.status(f"Closed a {dist:.2f}\" gap ({n} corner(s) welded)."
                        if n else "Nothing to weld at that pair.")
        self.refresh()


class WallRowList(QListWidget):
    """Shared row widget for wall lists across the orthogonality report and
    repair preview (0100-ruling.md SS3(a)(b), answered by 0103-ruling.md SS3):
    clicking a row centres the view on that wall and selects it -- "so I can
    find them" needs more than selection alone, since a wall off-screen is
    invisible either way, and this app had exactly one prior `centerOn`
    (startup) to set precedent from neither direction.

    A dead row -- including a MERGED wall, where the Qt object survives but
    its id no longer names anything -- goes grey in place, reads "no longer
    present", and stops accepting clicks. THE TEST IS THE ROUND TRIP: a wall
    id that does not come back from a FRESH `design_from_scene()` walk is
    dead, whatever `sip.isdeleted` thinks of the pointer -- that guard alone
    misses exactly the merged case."""

    def __init__(self, win, parent=None):
        super().__init__(parent)
        self.win = win
        self.itemClicked.connect(self._on_click)

    def add_row(self, wall_id, text):
        """Append a row naming `wall_id` (the document/canonical id) with
        `text` as its label; returns the QListWidgetItem."""
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, wall_id)
        self.addItem(item)
        return item

    def _on_click(self, item):
        wall_id = item.data(Qt.ItemDataRole.UserRole)
        if wall_id is None:                # already marked dead
            return
        import warnings
        from floorplanner.design.bridge import design_from_scene
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rep = {}
            design_from_scene(self.win, report=rep)
        wall_item = rep.get("wall_items", {}).get(wall_id)
        if wall_item is None or sip.isdeleted(wall_item):
            self._mark_dead(item)
            return
        self.win.scene.clearSelection()
        wall_item.setSelected(True)
        self.win.view.centerOn(wall_item)

    def _mark_dead(self, item):
        item.setData(Qt.ItemDataRole.UserRole, None)
        item.setText(f"{item.text()}  — no longer present")
        item.setForeground(QColor("#999"))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)


class OrthogonalityReportDialog(QDialog):
    """0055-ruling.md item B: a REPORT, not a repair. Names every wall
    within a few degrees of axis-aligned but not on it, so "Chief complains
    about my walls" becomes a number Patrick can act on -- WITHOUT deciding
    for him which walls are deliberate diagonals and which are join-artifact
    drift (SS5: that question is explicitly not settled here). There is no
    button that changes a wall's angle; item C (a repair) is unruled and out
    of this dialog's scope on purpose."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Wall orthogonality report")
        self.resize(560, 380)
        lay = QVBoxLayout(self)
        self.info = QLabel()
        self.info.setWordWrap(True)
        lay.addWidget(self.info)
        self.listw = WallRowList(win)
        lay.addWidget(self.listw)
        b_done = QPushButton("Close")
        b_done.clicked.connect(self.accept)
        lay.addWidget(b_done)
        self.refresh()

    def refresh(self):
        import warnings
        from floorplanner.design.bridge import design_from_scene
        from floorplanner.design.validate import (
            ORTHOGONALITY_BANDS, orthogonality_bands, wall_orthogonality,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rep = {}
            doc = design_from_scene(self.win, report=rep).to_dict()
        wall_items = rep.get("wall_items", {})       # 0101-ruling.md
        levels = {lv["id"]: lv["name"] for lv in doc.get("levels", [])}
        W = {w["id"]: w for w in doc.get("walls", [])}
        V = {v["id"]: (v["x"], v["y"]) for v in doc.get("vertices", [])}
        rows = wall_orthogonality(doc)
        bands = orthogonality_bands(rows)
        summary = ", ".join(f"{bands[label]} {label}"
                            for _lo, _hi, label in ORTHOGONALITY_BANDS
                            if bands[label])
        offaxis = [r for r in rows if r[3] > 0.01]
        self.listw.clear()
        for wid, lvl, typ, deg, disp in offaxis:
            item = wall_items.get(wid)
            tag = f"{item.uid} · " if item is not None else ""
            w = W.get(wid)
            coords = ""
            if w is not None and w["v1"] in V and w["v2"] in V:
                x1, y1 = V[w["v1"]]
                x2, y2 = V[w["v2"]]
                coords = (f" at ({fmt_ft2(x1)}, {fmt_ft2(y1)}) -> "
                         f"({fmt_ft2(x2)}, {fmt_ft2(y2)})ft")
            self.listw.add_row(
                wid,
                f"{levels.get(lvl, lvl)}: {tag}{wid} ({typ}){coords} — "
                f"{deg:.2f}deg off axis (would move {disp:.3f}\" if straightened)")
        if offaxis:
            self.info.setText(
                f"{len(offaxis)} of {len(rows)} wall(s) are off axis: "
                f"{summary}. A small deviation (well under 1 degree) is "
                "often not a deliberate diagonal -- it can be left over "
                "from a move, join, weld or coalesce. The inches figure is "
                "how far a straightening repair would move that wall's free "
                "end (0066-ruling.md) -- this report only lists them; "
                "nothing here changes a wall's angle.")
        else:
            self.info.setText(
                f"All {len(rows)} wall(s) are axis-aligned (or a deliberate "
                "diagonal within 0.01 degrees of one).")


class OrthogonalityRepairDialog(QDialog):
    """Edit ▸ "Repair wall orthogonality…" -- 0066-ruling.md item C, as
    amended by 0082-ruling.md secs 2-4 (the wording below follows
    0079-report.md sec2(d)'s own read-back). Computes the WHOLE repair on a
    document walked from the scene -- nothing here touches the scene until
    Apply. Never automatic (0066 sec5): this dialog is the one and only
    place this app straightens a wall's angle.

    Each row names both wall ids and the CURRENT (pre-repair) endpoints in
    feet (0098/0100-ruling.md): Patrick selected a wall the report didn't
    mean, because the status-bar id and the document id are two different
    namespaces both printed as "W<n>". `0101-ruling.md`'s map --
    `design_from_scene`'s `report["wall_items"]` -- is what makes the
    status-bar id available here at all."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Repair wall orthogonality")
        self.resize(560, 400)
        lay = QVBoxLayout(self)
        self.info = QLabel()
        self.info.setWordWrap(True)
        lay.addWidget(self.info)
        self.listw = WallRowList(win)
        lay.addWidget(self.listw)
        row = QHBoxLayout()
        self.b_apply = QPushButton("Apply")
        self.b_apply.clicked.connect(self._apply)
        row.addWidget(self.b_apply)
        b_cancel = QPushButton("Cancel")
        b_cancel.clicked.connect(self.reject)
        row.addWidget(b_cancel)
        lay.addLayout(row)
        self.refresh()

    def refresh(self):
        import warnings
        from floorplanner.design.bridge import design_from_scene
        from floorplanner.design.validate import repair_wall_orthogonality
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rep = {}
            self._doc = design_from_scene(self.win, report=rep).to_dict()
        self._wall_items = rep.get("wall_items", {})    # 0101-ruling.md
        self._levels = {lv["id"]: lv["name"] for lv in self._doc.get("levels", [])}
        self._V = {v["id"]: (v["x"], v["y"])
                  for v in self._doc.get("vertices", [])}
        self._W = {w["id"]: w for w in self._doc.get("walls", [])}
        self._result = repair_wall_orthogonality(self._doc)
        self.listw.clear()

        if self._result["rolled_back"]:
            n = len(self._result["newly_failing"])
            self.info.setText(
                f"The repair would have introduced {n} new invariant "
                "violation(s) -- nothing was changed.")
            self.b_apply.setEnabled(False)
            return

        moved = self._result["moved"]
        refused = self._result["refused"]
        over_t = self._result["over_t"]
        if not moved and not refused and not over_t:
            self.info.setText("No near-axis walls found -- nothing to repair.")
            self.b_apply.setEnabled(False)
            return

        largest = max((m[3] for m in moved), default=0.0)
        parts = []
        if moved:
            parts.append(f"{len(moved)} wall(s) will be straightened "
                        f"(largest correction: {largest:.3f}\").")
        if refused:
            parts.append(f"{len(refused)} wall(s) are refused and are "
                        "listed below, unchanged.")
        if over_t:
            from floorplanner.design.validate import REPAIR_T_IN
            parts.append(f"{len(over_t)} wall(s) are off axis by "
                        f"{REPAIR_T_IN:.4f}\" or more -- too large to "
                        "straighten automatically; see Edit ▸ Wall "
                        "orthogonality report… for the full list.")
        parts.append("Nothing is applied until you choose Apply.")
        self.info.setText(" ".join(parts))

        for wid, lvl, typ, disp in moved:
            self.listw.add_row(wid, f"{self._levels.get(lvl, lvl)}: {self._tag(wid)}"
                              f"{wid} ({typ}){self._coords(wid)} — will move "
                              f"{disp:.3f}\"")
        for wid, lvl, typ, _disp, reason in refused:
            self.listw.add_row(wid, f"{self._levels.get(lvl, lvl)}: {self._tag(wid)}"
                              f"{wid} ({typ}){self._coords(wid)} — refused "
                              f"({reason})")
        self.b_apply.setEnabled(bool(moved))

    def _tag(self, wid):
        """0098/0100-ruling.md: the status-bar id beside the document id,
        so a wall this dialog names can be found in the running app."""
        item = self._wall_items.get(wid)
        return f"{item.uid} · " if item is not None else ""

    def _coords(self, wid):
        """The wall's CURRENT endpoints (before this repair applies) in
        feet, matching 0100 sec1's own ruled row shape."""
        w = self._W.get(wid)
        if w is None or w["v1"] not in self._V or w["v2"] not in self._V:
            return ""
        x1, y1 = self._V[w["v1"]]
        x2, y2 = self._V[w["v2"]]
        return (f" at ({fmt_ft2(x1)}, {fmt_ft2(y1)}) -> "
               f"({fmt_ft2(x2)}, {fmt_ft2(y2)})ft")

    def _apply(self):
        from floorplanner.walls import close_gap
        n_moved = len(self._result["moved"])
        n_refused = len(self._result["refused"])
        for lvl, old, new in self._result["relocations"]:
            close_gap(self.win.scene, QPointF(*new), QPointF(*old),
                      floor=self._levels.get(lvl, lvl), tol=1e-4)
        self.win.status(f"Wall orthogonality repaired — {n_moved} wall(s) "
                        f"straightened, {n_refused} refused.")
        self.accept()


# Inventory table headers (itemised plan tables, exportable to CSV).
FURN_INV_HEADERS = ["Item", "Quantity", "Unit price", "Line total"]
HOUSE_INV_HEADERS = ["Item", "Detail", "Quantity", "Size"]
TOTAL_INV_HEADERS = ["Category", "Item", "Quantity", "Value"]


def _money(v: float) -> str:
    return f"${v:,.0f}" if v > 0 else "-"


def classify_furnishings(scene):
    """Split the scene's furnishings into (interior, yard).  An item is
    interior only when its centre sits inside a non-garage room and it is
    not itself a garage-category item; cars, yard equipment and anything in
    the garage count as yard, as does anything outside the walls."""
    rooms = [it for it in scene.items() if isinstance(it, RoomItem)]
    interior, yard = [], []
    for it in scene.items():
        if not isinstance(it, FurnishingItem):
            continue
        pt = it.scenePos()
        room = next((r for r in rooms if r.path.contains(pt)), None)
        spec = furnishing_spec(it.kind) or {}
        is_garage_room = (room is not None
                          and room.properties.get("room_type", "") == "Garage")
        is_garage_item = spec.get("category", "") == "Garage"
        if room is not None and not is_garage_room and not is_garage_item:
            interior.append(it)
        else:
            yard.append(it)
    return interior, yard


def furnishing_inventory_rows(items):
    """Rows for FURN_INV_HEADERS aggregated by name, with a TOTAL row.
    Returns (rows, total_qty, total_cost)."""
    agg = {}
    for it in items:
        rec = agg.setdefault(it.name, {"qty": 0,
                                       "price": float(getattr(it, "price",
                                                              0.0) or 0.0)})
        rec["qty"] += 1
    rows, total_qty, total_cost = [], 0, 0.0
    for name in sorted(agg, key=str.lower):
        qty, price = agg[name]["qty"], agg[name]["price"]
        line = qty * price
        total_qty += qty
        total_cost += line
        rows.append([name, str(qty), _money(price), _money(line)])
    rows.append(["TOTAL", str(total_qty), "", _money(total_cost)])
    return rows, total_qty, total_cost


def _opening_counts(scene):
    """{label: qty} of doors/windows across every wall (each opening once)."""
    counts = {}
    for w in scene.items():
        if not isinstance(w, WallItem):
            continue
        for op in w.openings:
            if op.kind == "window":
                name = f'Window {op.width:g}" x {op.height:g}"'
            else:
                name = f'Door {op.width:g}" x {op.height:g}" ({op.door_type})'
            counts[name] = counts.get(name, 0) + 1
    return counts


def house_inventory_rows(scene):
    """Rows for HOUSE_INV_HEADERS: rooms, openings and walls. Returns
    (rows, total_sqft)."""
    rooms = [it for it in scene.items() if isinstance(it, RoomItem)]
    rows, total_sqft = [], 0.0
    for r in sorted(rooms, key=lambda x: x.name.lower()):
        total_sqft += r.area_sqft
        rows.append([r.name, r.properties.get("room_type", "") or "Room",
                     "1", f"{r.area_sqft:,.1f} sq ft"])
    for name, qty in sorted(_opening_counts(scene).items()):
        kind, _, detail = name.partition(" ")
        rows.append([kind, detail.strip(), str(qty), ""])
    for wt in ("exterior", "interior"):
        walls = [w for w in scene.items()
                 if isinstance(w, WallItem) and w.wall_type == wt]
        if walls:
            ft = sum(w.length() for w in walls) / FOOT
            rows.append([f"{wt.title()} wall", "", str(len(walls)),
                         f"{ft:,.1f} ft total"])
    return rows, total_sqft


def total_inventory_rows(scene):
    """Rows for TOTAL_INV_HEADERS: an executive summary of structure and
    furnishings with a grand total cost."""
    rooms = [it for it in scene.items() if isinstance(it, RoomItem)]
    total_sqft = sum(r.area_sqft for r in rooms)
    building_cost = total_sqft * float(SETTINGS.get("cost_per_sqft", 0.0))
    opens = _opening_counts(scene)
    doors = sum(q for n, q in opens.items() if n.startswith("Door"))
    windows = sum(q for n, q in opens.items() if n.startswith("Window"))
    interior, yard = classify_furnishings(scene)
    _, iq, ic = furnishing_inventory_rows(interior)
    _, yq, yc = furnishing_inventory_rows(yard)
    grand = building_cost + ic + yc
    return [
        ["Structure", "Rooms", str(len(rooms)), f"{total_sqft:,.1f} sq ft"],
        ["Structure", "Doors", str(doors), ""],
        ["Structure", "Windows", str(windows), ""],
        ["Structure", "Est. building cost", "", _money(building_cost)],
        ["Furnishings", "Interior items", str(iq), _money(ic)],
        ["Furnishings", "Yard items", str(yq), _money(yc)],
        ["Grand total", "Building + furnishings", str(iq + yq),
         _money(grand)],
    ]


def inventory_tsv(headers, rows) -> str:
    """Headers + rows as tab-separated text — Excel splits it into columns on
    paste.  Any tab/newline inside a cell is collapsed to single spaces."""
    def cell(v) -> str:
        return " ".join(str(v).split())

    lines = ["\t".join(cell(h) for h in headers)]
    for row in rows:
        cells = [cell(c) for c in row]
        cells += [""] * (len(headers) - len(cells))
        lines.append("\t".join(cells))
    return "\n".join(lines) + "\n"


class InventoryDialog(QDialog):
    """A read-only inventory shown as an aligned table.  'Copy to clipboard
    (TSV)' puts tab-separated values on the clipboard, which Excel splits
    straight into columns when pasted."""

    def __init__(self, title, headers, rows, parent=None, note=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.headers = list(headers)
        self.rows = [list(r) for r in rows]
        lay = QVBoxLayout(self)
        if note:
            lab = QLabel(note)
            lab.setWordWrap(True)
            lab.setStyleSheet("color: #555;")
            lay.addWidget(lab)
        self.table = QTableWidget(len(self.rows), len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        right = [self._align_right(h) for h in self.headers]
        for ri, row in enumerate(self.rows):
            bold = bool(row) and str(row[0]).strip().upper() in (
                "TOTAL", "GRAND TOTAL")
            for ci in range(len(self.headers)):
                val = row[ci] if ci < len(row) else ""
                cell = QTableWidgetItem(str(val))
                if right[ci]:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                          | Qt.AlignmentFlag.AlignVCenter)
                if bold:
                    f = cell.font()
                    f.setBold(True)
                    cell.setFont(f)
                self.table.setItem(ri, ci, cell)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        if self.headers:
            self.table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumSize(560, 440)
        lay.addWidget(self.table)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.btn_copy = buttons.addButton(
            "Copy to clipboard (TSV)", QDialogButtonBox.ButtonRole.ActionRole)
        self.btn_copy.clicked.connect(self._copy)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    @staticmethod
    def _align_right(header) -> bool:
        h = str(header).lower()
        return any(k in h for k in ("price", "total", "quantity", "qty",
                                    "value", "cost", "size", "$"))

    def tsv_text(self) -> str:
        return inventory_tsv(self.headers, self.rows)

    def _copy(self):
        QApplication.clipboard().setText(self.tsv_text())
        self.btn_copy.setText("Copied ✓")


class RoomInventoryDialog(InventoryDialog):
    """Per-room inventory (right-click a room name) as an aligned table:
    its properties followed by the furnishings and openings it contains."""

    def __init__(self, room: RoomItem, parent=None):
        super().__init__(f"Inventory — {room.name}", ["Field", "Value"],
                         room.inventory_rows(), parent=parent,
                         note="Copy to clipboard (TSV) to paste straight "
                              "into Excel.")


class AboutDialog(QDialog):
    """Help ▸ About: app identity plus where FloorPlanner keeps designs and
    its settings file, using the operating system's standard locations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        v = QVBoxLayout(self)
        head = QLabel(
            f'<h2 style="margin-bottom:2px;">{APP_NAME}</h2>'
            f'<p style="color:#555;margin-top:0;">{code_version()} '
            "— a 2D architectural floor-plan editor built with PyQt6.<br>"
            f'<a href="{APP_URL}">{APP_URL}</a></p>')
        head.setTextFormat(Qt.TextFormat.RichText)
        head.setOpenExternalLinks(True)
        v.addWidget(head)

        info = QLabel(
            "<b>Where your files are kept</b>"
            "<ul style='margin-left:-20px;'>"
            "<li><b>Designs</b> (your plans) open and save by default in:"
            f"<br><code>{designs_dir()}</code></li>"
            "<li>The <b>settings file</b> (app preferences, including a "
            "remembered AI key) is:"
            f"<br><code>{settings_file()}</code></li>"
            "<li><b>Per-plan settings</b> — wall snap, rotation snap, canvas "
            "size and cost per square foot — are saved inside each plan's "
            "<code>.json</code> file.</li>"
            "</ul>"
            "These all use your operating system's standard locations. The "
            "AI key can also be supplied via the "
            "<code>ANTHROPIC_API_KEY</code> environment variable.")
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        info.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction)
        v.addWidget(info)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.btn_designs = buttons.addButton(
            "Open designs folder", QDialogButtonBox.ButtonRole.ActionRole)
        self.btn_config = buttons.addButton(
            "Open settings folder", QDialogButtonBox.ButtonRole.ActionRole)
        self.btn_designs.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(designs_dir()))))
        self.btn_config.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(config_dir()))))
        buttons.rejected.connect(self.reject)
        v.addWidget(buttons)
        self.setMinimumWidth(480)


class RoomPropertiesDialog(QDialog):
    """Property sheet for a room.  Measured values (area, dimensions,
    perimeter, glazing, counts) are computed from the plan and shown
    read-only; the rest are editable and saved with the plan."""

    def __init__(self, room: RoomItem, parent=None):
        super().__init__(parent)
        self.room = room
        self.setWindowTitle(f"Room properties — {room.name}")
        form = QFormLayout(self)
        r = room.interior_rect()
        wins, win_area, doors = room.opening_stats()
        p = room.properties

        self.ed_name = QLineEdit(room.name)
        form.addRow("Name", self.ed_name)
        self.cb_type = self._combo(ROOM_TYPES, p.get("room_type", ""))
        form.addRow("Room type", self.cb_type)

        form.addRow("Area", QLabel(f"{room.area_sqft:.1f} sq ft"))
        self.ck_include = QCheckBox("Include in total square footage")
        self.ck_include.setChecked(bool(p.get("include_sqft", True)))
        form.addRow("", self.ck_include)
        form.addRow("Interior width", QLabel(fmt_ftin(r.width())))
        form.addRow("Interior length", QLabel(fmt_ftin(r.height())))
        form.addRow("Perimeter", QLabel(fmt_ftin(room.perimeter_in())))
        if room.corners:
            txt = "  ".join(f"({fmt_ftin(c.x())}, {fmt_ftin(c.y())})"
                            for c in room.corners)
        else:
            txt = "—  (no closed wall loop traced)"
        lab_c = QLabel(txt)
        lab_c.setWordWrap(True)
        form.addRow("Corners", lab_c)
        form.addRow("Windows", QLabel(f"{wins}  ({win_area:.1f} sq ft glazing)"))
        form.addRow("Doors", QLabel(str(doors)))

        self.sp_ceiling = QDoubleSpinBox()
        self.sp_ceiling.setRange(60.0, 300.0)
        self.sp_ceiling.setSuffix(" in")
        self.sp_ceiling.setValue(float(p.get("ceiling_height_in", 96.0)))
        form.addRow("Ceiling height", self.sp_ceiling)

        self.cb_ceiling = self._combo(CEILING_TYPES, p.get("ceiling_type", "Flat"))
        form.addRow("Ceiling type", self.cb_ceiling)
        self.cb_floor = self._combo(FLOOR_FINISHES, p.get("floor_finish", ""))
        form.addRow("Floor finish", self.cb_floor)
        self.cb_wall = self._combo(WALL_FINISHES, p.get("wall_finish", ""))
        form.addRow("Wall finish", self.cb_wall)
        self.ed_base = QLineEdit(str(p.get("baseboard", "")))
        form.addRow("Baseboard / trim", self.ed_base)
        self.ck_crown = QCheckBox()
        self.ck_crown.setChecked(bool(p.get("crown_molding", False)))
        form.addRow("Crown molding", self.ck_crown)
        self.cb_hvac = self._combo(HVAC_TYPES, p.get("hvac", ""))
        form.addRow("Heating / cooling", self.cb_hvac)
        self.ed_elec = QLineEdit(str(p.get("electrical", "")))
        form.addRow("Electrical", self.ed_elec)
        self.ed_notes = QPlainTextEdit(str(p.get("notes", "")))
        self.ed_notes.setFixedHeight(70)
        form.addRow("Notes", self.ed_notes)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    @staticmethod
    def _combo(items, value):
        cb = QComboBox()
        cb.setEditable(True)
        cb.addItems(items)
        cb.setCurrentText(str(value))
        return cb

    def apply(self):
        name = self.ed_name.text().strip()
        if name:
            sc = self.room.scene()
            if sc is not None:
                name = unique_room_name(sc, name, exclude=self.room)
            self.room.name = name
        self.room.properties.update({
            "room_type": self.cb_type.currentText().strip(),
            "include_sqft": self.ck_include.isChecked(),
            "ceiling_height_in": self.sp_ceiling.value(),
            "ceiling_type": self.cb_ceiling.currentText().strip(),
            "floor_finish": self.cb_floor.currentText().strip(),
            "wall_finish": self.cb_wall.currentText().strip(),
            "baseboard": self.ed_base.text().strip(),
            "crown_molding": self.ck_crown.isChecked(),
            "hvac": self.cb_hvac.currentText().strip(),
            "electrical": self.ed_elec.text().strip(),
            "notes": self.ed_notes.toPlainText(),
        })


class OpeningPropertiesDialog(QDialog):
    """Property sheet for a door, window or GATE.

    It exists because the size prompt it replaces **never said what the user had
    made** (D74). Placing a door in a railing produces a GATE — derived, not
    chosen, which is the right design: it adds no mode, no tool and nothing to
    learn, and it makes I7 true by construction rather than by a check the user
    can fail. But the derivation was invisible. The kind lived in a
    `QInputDialog`'s title bar, next to a field asking for a number.

    > **DERIVING A PROPERTY IS NOT A LICENCE TO HIDE IT.**

    A derived value the user cannot see is indistinguishable, from where they
    sit, from a value that was ignored.

    So the kind is shown as **read-only text with its reason** — read-only
    because it is derived and offering it as a choice would re-introduce exactly
    the mode the derivation removed (a gate placed in a bedroom wall, and then
    an invariant telling them off for it). The reason is stated only where there
    IS one: a door is a door because it was asked for, and inventing an
    explanation for that would be noise."""

    #: What made this kind what it is.  Keyed by kind; absent = chosen directly,
    #: and nothing is claimed.
    REASONS = {
        "gate": ("Derived: an opening in a {type} is a gate.\n"
                 "Only gates may open a landscape wall (invariant I7)."),
    }

    def __init__(self, opening, parent=None):
        super().__init__(parent)
        self.opening = opening
        kind = opening.kind
        self.setWindowTitle(f"{kind.title()} properties")
        form = QFormLayout(self)

        lab_kind = QLabel(kind.title())
        f = lab_kind.font()
        f.setBold(True)
        lab_kind.setFont(f)
        form.addRow("Kind", lab_kind)

        reason = self.REASONS.get(kind)
        if reason is not None:
            wall = getattr(opening, "wall", None)
            wtype = getattr(wall, "wall_type", "landscape wall")
            note = QLabel(reason.format(type=wtype))
            note.setStyleSheet("color: #666;")
            note.setWordWrap(True)
            form.addRow("", note)

        self.ed_code = QLineEdit(opening.code)
        self.ed_code.selectAll()
        form.addRow("Size WWHH", self.ed_code)
        hint = QLabel("Width inches, then height inches — e.g. 3280 is 32″ "
                      "wide by 80″ high.")
        hint.setStyleSheet("color: #666;")
        hint.setWordWrap(True)
        form.addRow("", hint)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def code(self) -> str:
        return self.ed_code.text().strip()


class ConceptRoomDialog(QDialog):
    """New concept room… (P4.4): a room typed in BY DIMENSION rather than
    drawn — the "12 x 14 bedroom" the schema's `nominal_size` describes.

    Feet, because that is how a room is spoken; the document stores inches.
    What it makes is wall-less and floating: a sketch unit you park where you
    like and turn into real walls later."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New concept room")
        form = QFormLayout(self)

        self.ed_name = QLineEdit("Room")
        self.ed_name.selectAll()
        form.addRow("Name", self.ed_name)

        self.sp_w = QDoubleSpinBox()
        self.sp_w.setRange(1.0, 200.0)
        self.sp_w.setDecimals(2)
        self.sp_w.setSuffix(" ft")
        self.sp_w.setValue(12.0)
        form.addRow("Width", self.sp_w)

        self.sp_d = QDoubleSpinBox()
        self.sp_d.setRange(1.0, 200.0)
        self.sp_d.setDecimals(2)
        self.sp_d.setSuffix(" ft")
        self.sp_d.setValue(14.0)
        form.addRow("Depth", self.sp_d)

        note = QLabel("Creates a FLOATING, wall-less room at the canvas "
                      "centre.\nDrag it by its name; the typed size is "
                      "recorded as design intent.")
        note.setStyleSheet("color: #666;")
        form.addRow(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        """(name, width_in, depth_in) — inches, the document's unit."""
        return (self.ed_name.text().strip() or "Room",
                float(self.sp_w.value()) * FOOT,
                float(self.sp_d.value()) * FOOT)


class SettingsDialog(QDialog):
    """File > Settings…: plan-wide preferences, saved in the plan file."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        form = QFormLayout(self)

        self.cb_snap = QComboBox()
        vals = list(WALL_SNAP_CHOICES)
        cur = SETTINGS["wall_snap_in"]
        if cur not in vals:
            vals = sorted(set(vals) | {cur})
        for v in vals:
            self.cb_snap.addItem(f'{v:g}"', v)
        self.cb_snap.setCurrentIndex(vals.index(cur))
        form.addRow("Wall snap (on centre)", self.cb_snap)

        self.sp_rot = QDoubleSpinBox()
        self.sp_rot.setRange(1.0, 90.0)
        self.sp_rot.setDecimals(1)
        self.sp_rot.setSuffix("°")
        self.sp_rot.setValue(float(SETTINGS["rotate_snap_deg"]))
        form.addRow("Rotation snap (Ctrl-drag)", self.sp_rot)

        self.sp_cw = QDoubleSpinBox()
        self.sp_cw.setRange(20.0, 500.0)
        self.sp_cw.setDecimals(1)
        self.sp_cw.setSuffix(" ft")
        self.sp_cw.setValue(SETTINGS["canvas_w_in"] / FOOT)
        form.addRow("Canvas width", self.sp_cw)

        self.sp_ch = QDoubleSpinBox()
        self.sp_ch.setRange(20.0, 500.0)
        self.sp_ch.setDecimals(1)
        self.sp_ch.setSuffix(" ft")
        self.sp_ch.setValue(SETTINGS["canvas_h_in"] / FOOT)
        form.addRow("Canvas height", self.sp_ch)

        self.sp_cost = QDoubleSpinBox()
        self.sp_cost.setRange(0.0, 100000.0)
        self.sp_cost.setDecimals(0)
        self.sp_cost.setPrefix("$ ")
        self.sp_cost.setSuffix(" / sq ft")
        self.sp_cost.setValue(float(SETTINGS.get("cost_per_sqft", 0.0)))
        form.addRow("Building cost", self.sp_cost)

        self.ck_coalesce = QCheckBox(
            "Merge overlapping walls automatically as you edit")
        self.ck_coalesce.setChecked(bool(SETTINGS.get("auto_coalesce", True)))
        form.addRow("Auto-coalesce walls", self.ck_coalesce)

        # the shuffle MODE itself lives on the toolbar (one surface); this is
        # its sibling editing flag (schema $defs.editing_modes, P4.3).
        # auto_bind is deliberately NOT here: it is modelled, emitted and
        # plumbed, but the P4.3 census measured NO gateable automatic site,
        # so a control would promise behaviour nothing enforces -- the UI
        # returns when a gateable site exists (ruled 2026-08-03; register).
        self.ck_weld = QCheckBox(
            "Weld a drawn wall end onto whatever it lands near")
        self.ck_weld.setChecked(bool(SETTINGS.get("auto_weld", True)))
        form.addRow("Auto-weld ends", self.ck_weld)

        note = QLabel("Defaults: 6\" wall snap, 15° rotation snap, "
                      "100' × 70' canvas, $150 / sq ft.\n"
                      "Settings are saved with the plan.")
        note.setStyleSheet("color: #666;")
        form.addRow(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def apply(self):
        SETTINGS["wall_snap_in"] = float(self.cb_snap.currentData())
        SETTINGS["rotate_snap_deg"] = float(self.sp_rot.value())
        SETTINGS["canvas_w_in"] = float(self.sp_cw.value()) * FOOT
        SETTINGS["canvas_h_in"] = float(self.sp_ch.value()) * FOOT
        SETTINGS["cost_per_sqft"] = float(self.sp_cost.value())
        SETTINGS["auto_coalesce"] = bool(self.ck_coalesce.isChecked())
        SETTINGS["auto_weld"] = bool(self.ck_weld.isChecked())


class PDFExportOptionsDialog(QDialog):
    """File ▸ Export ▸ PDF plan set… — 0072-ruling.md §5 / 0116-ruling.md §2:
    title, subtitle, author, wall-assembly note, dimension note, level
    selection, include-concept. Title defaults from the document's own name
    (`current_path`'s stem), not `"RESIDENCE"`.

    NO THICKNESS OVERRIDE CONTROL. `fp2pdf.py`'s own table is now the
    normative `STD_T` (0072-ruling.md §2(1), the third-table defect fixed) —
    a GUI control that let a user contradict it would reopen D73 through the
    front door, this time with a widget inviting it (0072-ruling.md §5)."""

    def __init__(self, doc, default_title, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PDF plan set options")
        form = QFormLayout(self)

        self.ed_title = QLineEdit(default_title)
        form.addRow("Title", self.ed_title)
        self.ed_subtitle = QLineEdit("")
        form.addRow("Subtitle", self.ed_subtitle)
        self.ed_author = QLineEdit("Owner")
        form.addRow("Author", self.ed_author)
        self.ed_assembly = QLineEdit(
            "2x6 exterior / 2x4 interior, conventional framing")
        form.addRow("Wall assembly note", self.ed_assembly)
        self.ed_dim = QLineEdit("All dimensions to overall wall faces")
        form.addRow("Dimension note", self.ed_dim)

        # ONE SHEET PER STOREY LEVEL, checkable -- a site-kind level is
        # never a sheet (fp2pdf.convert()'s own filter) so it is not
        # offered here either; nothing to uncheck that would never render.
        self.level_checks = []
        levels_box = QVBoxLayout()
        for lv in doc.get("levels", []):
            if lv.get("kind", "storey") == "site":
                continue
            cb = QCheckBox(lv.get("name", lv["id"]))
            cb.setChecked(True)
            cb.setProperty("level_id", lv["id"])
            levels_box.addWidget(cb)
            self.level_checks.append(cb)
        form.addRow("Levels", levels_box)

        self.ck_concept = QCheckBox("Include concept rooms")
        self.ck_concept.setChecked(False)
        form.addRow("", self.ck_concept)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        """(meta, only_levels, include_concept). `only_levels` is `None`
        for "every level" (every checkbox checked, or none exist to
        choose), else the checked level ids -- possibly `[]` if the user
        unchecked every one, which the caller refuses rather than exports
        an empty PDF."""
        meta = {"title": self.ed_title.text().strip() or "Untitled",
                "subtitle": self.ed_subtitle.text().strip(),
                "author": self.ed_author.text().strip() or "Owner",
                "assembly_note": self.ed_assembly.text().strip(),
                "dim_note": self.ed_dim.text().strip()}
        checked = [cb.property("level_id") for cb in self.level_checks
                  if cb.isChecked()]
        only_levels = None if len(checked) == len(self.level_checks) \
            else checked
        return meta, only_levels, self.ck_concept.isChecked()


class ImageImportDialog(QDialog):
    """File > Import from image…: scale + detection settings for turning a
    raster floor-plan PNG into walls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import plan from image")
        form = QFormLayout(self)

        self.sp_width = QDoubleSpinBox()
        self.sp_width.setRange(1.0, 2000.0)
        self.sp_width.setDecimals(1)
        self.sp_width.setSuffix(" ft")
        self.sp_width.setValue(40.0)
        form.addRow("Real width of the drawing", self.sp_width)

        self.sp_merge = QDoubleSpinBox()
        self.sp_merge.setRange(1.0, 200.0)
        self.sp_merge.setDecimals(0)
        self.sp_merge.setSuffix(" px")
        self.sp_merge.setValue(3.0)
        form.addRow("Merge double-line walls within", self.sp_merge)

        self.sp_thresh = QDoubleSpinBox()
        self.sp_thresh.setRange(1.0, 254.0)
        self.sp_thresh.setDecimals(0)
        self.sp_thresh.setValue(128.0)
        form.addRow("Wall darkness threshold (0–255)", self.sp_thresh)

        note = QLabel("Best on clean, axis-aligned plans (dark walls on a "
                      "light background).\nThe detected walls preview in blue "
                      "before you add them.")
        note.setStyleSheet("color: #666;")
        form.addRow(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        return (float(self.sp_width.value()), int(self.sp_merge.value()),
                int(self.sp_thresh.value()))


class AIPricingDialog(QDialog):
    """AI ▸ Update furnishing prices…: choose an AI system, edit the prompt,
    and fetch up-to-date purchase prices for the whole furnishing catalog.
    On success, `result_prices` holds the {id: price} mapping and the dialog
    accepts; the prompt and provider drop-down are fully editable."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI · Update furnishing prices")
        self.result_prices = None
        v = QVBoxLayout(self)

        form = QFormLayout()
        self.cb_provider = QComboBox()
        for prov in AI_PROVIDERS:
            self.cb_provider.addItem(prov["name"])
        form.addRow("AI system", self.cb_provider)

        self.cb_model = QComboBox()
        self.cb_model.setEditable(True)
        form.addRow("Model", self.cb_model)

        self.ed_key = QLineEdit()
        self.ed_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.ed_key.setPlaceholderText("sk-ant-…  (or set ANTHROPIC_API_KEY)")
        form.addRow("API key", self.ed_key)

        self.ck_remember = QCheckBox("Remember this key on this computer")
        form.addRow("", self.ck_remember)
        v.addLayout(form)

        v.addWidget(QLabel("Prompt (sent to the AI — edit freely):"))
        self.ed_prompt = QPlainTextEdit()
        self.ed_prompt.setPlainText(default_pricing_prompt())
        v.addWidget(self.ed_prompt, 1)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("color: #555;")
        v.addWidget(self.lbl_status)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel)
        self.btn_fetch = self.buttons.addButton(
            "Fetch prices", QDialogButtonBox.ButtonRole.AcceptRole)
        self.buttons.rejected.connect(self.reject)
        self.btn_fetch.clicked.connect(self._fetch)
        v.addWidget(self.buttons)

        self.cb_provider.currentIndexChanged.connect(self._sync_models)
        self._sync_models()
        self.ed_key.setText(load_saved_api_key()
                            or os.environ.get("ANTHROPIC_API_KEY", ""))
        self.resize(640, 580)

    def _sync_models(self):
        self.cb_model.clear()
        idx = max(self.cb_provider.currentIndex(), 0)
        self.cb_model.addItems(AI_PROVIDERS[idx]["models"])

    def _fetch(self):
        key = self.ed_key.text().strip()
        if not key:
            self.lbl_status.setText(
                "Enter an API key, or set the ANTHROPIC_API_KEY "
                "environment variable.")
            return
        model = self.cb_model.currentText().strip()
        prompt = self.ed_prompt.toPlainText()
        self.lbl_status.setText("Contacting the AI…  this may take a moment.")
        self.btn_fetch.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()
        try:
            prices = anthropic_fetch_prices(key, model, prompt)
        except Exception as ex:             # noqa: BLE001 - shown to the user
            QApplication.restoreOverrideCursor()
            self.btn_fetch.setEnabled(True)
            self.lbl_status.setText(str(ex))
            return
        QApplication.restoreOverrideCursor()
        if self.ck_remember.isChecked():
            save_api_key(key)
        self.result_prices = prices
        self.accept()
