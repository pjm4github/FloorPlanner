"""Modal dialogs (inventory, room properties, settings, image import, AI
pricing, about) and the inventory row/TSV helpers that feed them."""
import math
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
from floorplanner.roofs import RoofItem
from floorplanner.items import *  # noqa: F401

class GapReviewDialog(QDialog):
    """DEFECT 34's review (P4.2): LIST the document's near-vertex gaps in the
    (vertex_weld_in, join_tol_in) band with their distances, and let the user
    close the ones they did not intend -- one pair at a time, explicitly.
    Nothing auto-closes: a deliberate reveal is legitimate design (the schema
    says so in as many words), and nothing here can tell a reveal from a
    mistake. Same discipline as P2.1's conversion report: report to a human,
    repair only on their say-so."""

    #: red highlight box padding around a gap, in inches, and the least the
    #: view shows around one so a 1" gap is not fitted to the whole window
    MARKER_PAD_IN = 18.0
    MIN_VIEW_IN = 8 * 12.0

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Review wall gaps")
        self.resize(560, 360)
        # NON-MODAL (Patrick, 2026-11): the user edits the plan to fix a gap by
        # hand while this stays open, then rescans -- same pattern as the
        # design-problems report. WA_DeleteOnClose, so the red marker is torn
        # down with the window.
        self.setModal(False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._marker = None
        lay = QVBoxLayout(self)
        self.info = QLabel()
        self.info.setWordWrap(True)
        lay.addWidget(self.info)
        self.listw = QListWidget()
        self.listw.currentRowChanged.connect(self._on_row)
        lay.addWidget(self.listw)
        row = QHBoxLayout()
        self.b_zoom = QPushButton("Zoom to problem")
        self.b_zoom.clicked.connect(self._zoom_to_selected)
        row.addWidget(self.b_zoom)
        self.b_close = QPushButton("Close selected gap")
        self.b_close.clicked.connect(self._close_selected)
        row.addWidget(self.b_close)
        self.b_rescan = QPushButton("Rescan")
        self.b_rescan.clicked.connect(self.refresh)
        row.addWidget(self.b_rescan)
        row.addStretch(1)
        b_done = QPushButton("Done")
        b_done.clicked.connect(self.close)
        row.addWidget(b_done)
        lay.addLayout(row)
        self.refresh()

    def refresh(self):
        import warnings
        from floorplanner.design.bridge import design_from_scene
        from floorplanner.design.validate import near_vertex_gaps
        self._clear_marker()                    # a rescan drops the stale box
        rep = {}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            doc = design_from_scene(self.win, report=rep).to_dict()
        self._levels = {lv["id"]: lv["name"] for lv in doc.get("levels", [])}
        # 2026-11: each gap names its two VERTICES and the WALL(s) each holds,
        # in the session labels the plan shows (W7, V12). `wall_items` comes
        # from THIS walk, so the doc ids line up with the live items.
        from floorplanner.problems import _session_labels_of  # late (UI)
        label_of = _session_labels_of(self.win.scene)   # doc id -> W7 / V12
        wall_items = rep.get("wall_items", {})
        held = {}
        for w in doc["walls"]:
            held.setdefault(w["v1"], []).append(w["id"])
            held.setdefault(w["v2"], []).append(w["id"])

        def _ids(vid):
            # the vertex label covers an open room corner (no wall) too; the
            # wall labels come from the live items of this same walk
            vlabel = label_of.get(vid, vid)
            wls = []
            for wid in held.get(vid, []):
                wi = wall_items.get(wid)
                if wi is not None and not sip.isdeleted(wi):
                    wls.append(getattr(wi, "uid", None) or label_of.get(wid, wid))
                else:
                    wls.append(label_of.get(wid, wid))
            return vlabel, (", ".join(wls) or "free")

        self.gaps = near_vertex_gaps(doc)
        self.listw.clear()
        for lvl, a, b, dist, aid, bid in self.gaps:
            va, wa = _ids(aid)
            vb, wb = _ids(bid)
            self.listw.addItem(
                f"{self._levels.get(lvl, lvl)}: "
                f"{va} [{wa}] ({fmt_ftin(a[0])}, {fmt_ftin(a[1])}) and "
                f"{vb} [{wb}] ({fmt_ftin(b[0])}, {fmt_ftin(b[1])}) "
                f"are {dist:.2f}\" apart")
        if self.gaps:
            self.info.setText(
                f"{len(self.gaps)} pair(s) of corners sit close together "
                f"without sharing a corner. Some may be deliberate (a "
                f"reveal, a pilaster gap) -- those need no action. 'Zoom to "
                f"problem' boxes the pair in red; 'Close selected gap' welds "
                f"them; or edit the walls by hand and press 'Rescan'.")
            self.listw.setCurrentRow(0)
        else:
            self.info.setText("No near-vertex gaps -- every pair of corners "
                              "is either welded or genuinely apart.")
        has = bool(self.gaps)
        self.b_close.setEnabled(has)
        self.b_zoom.setEnabled(has)

    def _gap_rect(self, a, b):
        """The scene rectangle around a gap pair, padded so both corners and
        their surroundings show."""
        r = QRectF(QPointF(*a), QPointF(*b)).normalized().adjusted(
            -self.MARKER_PAD_IN, -self.MARKER_PAD_IN,
            self.MARKER_PAD_IN, self.MARKER_PAD_IN)
        if r.width() < self.MIN_VIEW_IN:
            r.adjust(-(self.MIN_VIEW_IN - r.width()) / 2.0, 0,
                     (self.MIN_VIEW_IN - r.width()) / 2.0, 0)
        if r.height() < self.MIN_VIEW_IN:
            r.adjust(0, -(self.MIN_VIEW_IN - r.height()) / 2.0,
                     0, (self.MIN_VIEW_IN - r.height()) / 2.0)
        return r

    def _clear_marker(self):
        if self._marker is not None:
            try:
                self.win.scene.removeItem(self._marker)
            except RuntimeError:
                pass
            self._marker = None

    def _show_marker(self, a, b):
        """Draw a red box around the gap pair itself (tight, not the padded
        view rect), on top of everything, on whatever floor is shown."""
        self._clear_marker()
        box = QRectF(QPointF(*a), QPointF(*b)).normalized().adjusted(
            -self.MARKER_PAD_IN / 2.0, -self.MARKER_PAD_IN / 2.0,
            self.MARKER_PAD_IN / 2.0, self.MARKER_PAD_IN / 2.0)
        pen = QPen(QColor(220, 30, 30), 2.0)
        pen.setCosmetic(True)                   # 2px at any zoom
        self._marker = self.win.scene.addRect(box, pen)
        self._marker.setZValue(10_000)          # above walls, rooms, roofs

    def _zoom_to_selected(self):
        i = self.listw.currentRow()
        if i < 0 or i >= len(self.gaps):
            return
        lvl, a, b, _dist, _aid, _bid = self.gaps[i]
        name = self._levels.get(lvl, lvl)
        if (self.win._floor(name) is not None
                and name != self.win.active_floor):
            self.win.switch_floor(name)
        rect = self._gap_rect(a, b)
        self.win.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self.win.view.centerOn(rect.center())
        self._show_marker(a, b)

    def _on_row(self, _row):
        # a stale red box must not linger on a different pair; it reappears
        # only when the user zooms to the newly selected one
        self._clear_marker()

    def closeEvent(self, e):
        self._clear_marker()
        super().closeEvent(e)

    def _close_selected(self):
        i = self.listw.currentRow()
        if i < 0 or i >= len(self.gaps):
            return
        lvl, a, b, dist, _aid, _bid = self.gaps[i]
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

        # -- 0255: the window's elevation. The sill over this level's floor,
        # a property of the window; a record that never said sits at the
        # plan's default, which seeds the field, and OK writes the value.
        self.sp_sill = None
        if kind == "window":
            from floorplanner.model import DEFAULT_SILL_IN
            said = getattr(opening, "sill_in", None)
            self.sp_sill = QDoubleSpinBox()
            self.sp_sill.setRange(0.0, 600.0)
            self.sp_sill.setDecimals(1)
            self.sp_sill.setSuffix(" in")
            self.sp_sill.setValue(float(DEFAULT_SILL_IN if said is None else said))
            form.addRow("Sill height", self.sp_sill)
            sill_hint = QLabel(
                f"The sill above this level's floor; the head is the sill plus "
                f"the height. A window that was never set sits at the plan's "
                f"default, {DEFAULT_SILL_IN:g}″"
                + (" — this one has not been set." if said is None else "."))
            sill_hint.setStyleSheet("color: #666;")
            sill_hint.setWordWrap(True)
            form.addRow("", sill_hint)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def code(self) -> str:
        return self.ed_code.text().strip()

    def sill_in(self):
        """The sill as typed, inches over the level; None on a sheet with no
        sill row (a door, a gate)."""
        return None if self.sp_sill is None else float(self.sp_sill.value())


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


class _EndOnCanvas(QWidget):
    """The end-on drawing itself (0140-ruling.md, the End-On dialog ruling,
    sec1): the roof triangle over the level's wall stack, projected along
    the ridge axis -- ridge apex, both eave lines, the wall top as a
    reference, R/H/P labelled on the drawing. Redrawn on every edit via
    `set_values`; the geometry math lives in the dialog, this widget only
    paints whatever it is handed.

    R4b: draws BOTH sides from their own span and overhang (0154-ruling.md
    sec2: "the End-On drawing shows both slopes when they differ") -- the
    overhang continues each slope past its wall line to the eave tip, and
    the right side gets its own pitch label whenever it differs from the
    left. Left is drawn on the left: `span_in[0]`'s side.

    0255-report.md: a SHED (0248 plan A) has no right side -- its right
    span is 0 and stays 0 here (the gable clamp to 1 would draw a plane
    that does not exist). It is drawn as the one slope down the left and
    the high wall under the ridge; nothing divides by the right span. The
    porch roof of his house opened this dialog on a zero and the division
    in `paintEvent` took the application down."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 240)
        self.span_l = self.span_r = 144.0
        self.oh_l = self.oh_r = 0.0
        self.ridge_h = 132.0
        self.eaves_h = 96.0
        self.wall_top_in = float(DEFAULT_ROOM_PROPS["ceiling_height_in"])

    @property
    def span_in(self) -> float:
        """The LEFT span -- the recompute's reference side (dialog docstring)."""
        return self.span_l

    def set_values(self, span_l, span_r, oh_l, oh_r, ridge_h, eaves_h,
                   wall_top_in=None):
        self.span_l, self.span_r = max(1.0, span_l), max(0.0, span_r)
        self.oh_l, self.oh_r = max(0.0, oh_l), max(0.0, oh_r)
        self.ridge_h, self.eaves_h = ridge_h, eaves_h
        if wall_top_in is not None:
            self.wall_top_in = float(wall_top_in)
        self.update()

    @property
    def shed(self) -> bool:
        """One plane: no right span (the shed form)."""
        return self.span_r < 1e-9

    def pitch_deg(self, side: int) -> float:
        span = self.span_l if side == 0 else self.span_r
        if span < 1e-9:
            return 90.0                  # a shed's right side is its high wall
        return math.degrees(math.atan2(max(0.0, self.ridge_h - self.eaves_h),
                                       span))

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        margin = 32.0
        reach_l, reach_r = self.span_l + self.oh_l, self.span_r + self.oh_r
        top_in = max(self.ridge_h, self.wall_top_in) + 24.0
        sx = (w - 2 * margin) / (reach_l + reach_r)
        sy = (h - 2 * margin) / max(top_in, 1.0)
        scale = min(sx, sy)
        cx = margin + reach_l * scale       # the ridge's own x
        base_y = h - margin

        def pt(x_in, y_in):
            return QPointF(cx + x_in * scale, base_y - y_in * scale)

        rise = self.ridge_h - self.eaves_h
        shed = self.shed
        slope_l = rise / self.span_l
        slope_r = 0.0 if shed else rise / self.span_r
        ridge_pt = pt(0.0, self.ridge_h)
        eave_l = pt(-self.span_l, self.eaves_h)
        eave_r = pt(self.span_r, self.eaves_h)
        tip_l = pt(-reach_l, self.eaves_h - slope_l * self.oh_l)
        tip_r = pt(reach_r, self.eaves_h - slope_r * self.oh_r)

        # the level's base line (the ground only on a level at elevation 0)
        p.setPen(QPen(QColor(90, 90, 90), 1.5))
        p.drawLine(QPointF(margin * 0.4, base_y), QPointF(w - margin * 0.4, base_y))
        # wall-top reference, dashed (0140-ruling.md sec3: shown as reference,
        # not the datum -- R/H are measured from the base line above)
        p.setPen(QPen(QColor(150, 150, 150), 1.0, Qt.PenStyle.DashLine))
        wt_y = base_y - self.wall_top_in * scale
        p.drawLine(QPointF(margin * 0.4, wt_y), QPointF(w - margin * 0.4, wt_y))
        # the roof itself: ridge heavy-adjacent slopes, eaves at wall stack,
        # continued past each wall line to the overhang tip
        p.setPen(QPen(QColor(133, 77, 14), 2.4))
        p.drawLine(tip_l, ridge_pt)
        if not shed:
            p.drawLine(ridge_pt, tip_r)
        p.setPen(QPen(QColor(60, 60, 60), 1.2))
        p.drawLine(QPointF(eave_l.x(), base_y), eave_l)
        if shed:
            p.drawLine(QPointF(cx, base_y), ridge_pt)   # the high wall under the ridge
        else:
            p.drawLine(QPointF(eave_r.x(), base_y), eave_r)

        p.setPen(QPen(QColor(20, 20, 20)))
        if shed:
            p.drawText(ridge_pt + QPointF(-64, -6), f"R {fmt_in(self.ridge_h)}")
            p.drawText(eave_l + QPointF(-70, 4), f"H {fmt_in(self.eaves_h)}")
            p.drawText(eave_l + QPointF(-70, 20), f"P {self.pitch_deg(0):.1f}°")
            return
        p.drawText(ridge_pt + QPointF(6, -6), f"R {fmt_in(self.ridge_h)}")
        p.drawText(eave_r + QPointF(6, 4), f"H {fmt_in(self.eaves_h)}")
        p.drawText(eave_l + QPointF(-70, 20), f"P {self.pitch_deg(0):.1f}°")
        if abs(self.span_l - self.span_r) > 1e-6:
            p.drawText(eave_r + QPointF(6, 20), f"P' {self.pitch_deg(1):.1f}°")


class _ElevationCanvas(QWidget):
    """#3 (0294 §4): the End-On dialog's ELEVATION tab -- the roof's gable end
    seen straight-on, to scale, with every DOOR and WINDOW in the wall(s) under
    it LOCATED by dimensions. Reads `RoofItem.gable_elevation()` (a dormer face,
    or a plain gable end's wall(s)). Per opening: its size (W×H), its height
    above the floor (a window's sill; a door/gate sits on the floor, so its head
    height), and its centre's offset from the gable centreline. A window draws as
    glass with a muntin cross, a door/gate as a panel on the floor with a leaf
    stile. More parameters land here as he orders them (his order 2026-11-11:
    read the walls under the gable and show their doors and windows)."""

    _WALL = QColor(60, 60, 60)
    _ROOF = QColor(133, 77, 14)
    _GLASS = QColor(191, 219, 254)
    _DOOR = QColor(214, 211, 203)
    _DIM = QColor(37, 99, 235)
    _CENTRE = QColor(150, 150, 150)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.setMinimumHeight(260)

    def set_data(self, data):
        self.data = data
        self.update()

    def sizeHint(self):
        return QSize(460, 300)

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(255, 255, 255))
        e = self.data
        if not e or e.get("width_in", 0.0) <= 0.0 or e.get("ridge_in", 0.0) <= 0.0:
            p.setPen(QPen(QColor(120, 120, 120)))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "No gable end to draw for this roof.")
            return
        W = float(e["width_in"])
        ridge = float(e["ridge_in"])
        eaves = max(0.0, min(float(e["eaves_in"]), ridge))
        apex = float(e.get("apex_in", 0.0))
        ml, mr, mt, mb = 54.0, 20.0, 22.0, 34.0
        scale = min((w - ml - mr) / W, (h - mt - mb) / ridge)
        scale = max(scale, 0.01)
        cx = ml + (w - ml - mr) / 2.0
        base_y = h - mb

        def X(xin):
            return cx + xin * scale

        def Y(yin):
            return base_y - yin * scale

        # the floor baseline + its absolute datum label
        p.setPen(QPen(self._WALL, 1.4))
        p.drawLine(QPointF(ml * 0.5, base_y), QPointF(w - mr * 0.5, base_y))
        p.setPen(QPen(QColor(90, 90, 90)))
        f = p.font()
        f.setPointSize(8)
        p.setFont(f)
        p.drawText(QPointF(ml * 0.5, base_y + 18),
                   f"floor {fmt_in(float(e.get('floor_abs_in', 0.0)))}")
        # the gable centreline (dashed, through the ridge apex)
        p.setPen(QPen(self._CENTRE, 1.0, Qt.PenStyle.DashLine))
        p.drawLine(QPointF(X(apex), base_y), QPointF(X(apex), Y(ridge)))
        # the gable outline: a rectangle to the eaves, a triangle to the ridge
        half = W / 2.0
        p.setPen(QPen(self._WALL, 1.6))
        p.drawLine(QPointF(X(-half), base_y), QPointF(X(-half), Y(eaves)))
        p.drawLine(QPointF(X(half), base_y), QPointF(X(half), Y(eaves)))
        p.setPen(QPen(self._ROOF, 2.4))
        p.drawLine(QPointF(X(-half), Y(eaves)), QPointF(X(apex), Y(ridge)))
        p.drawLine(QPointF(X(apex), Y(ridge)), QPointF(X(half), Y(eaves)))
        p.setPen(QPen(QColor(20, 20, 20)))
        p.drawText(QPointF(X(apex) + 4, Y(ridge) - 2), f"R {fmt_in(ridge)}")

        for wd in list(e.get("windows", [])) + list(e.get("doors", [])):
            c = float(wd["centre_in"])
            ww, hh = float(wd["w_in"]), float(wd["h_in"])
            sill, head = float(wd["sill_in"]), float(wd["head_in"])
            kind = wd.get("kind", "window")
            if ww <= 0.0 or hh <= 0.0:
                continue
            x0, x1 = X(c - ww / 2.0), X(c + ww / 2.0)
            y0, y1 = Y(head), Y(sill)
            r = QRectF(QPointF(x0, y0), QPointF(x1, y1))
            if kind == "window":
                p.fillRect(r, self._GLASS)
                p.setPen(QPen(self._WALL, 1.2))
                p.drawRect(r)
                # a muntin cross, so a window reads as a window
                p.setPen(QPen(self._WALL, 0.5))
                p.drawLine(QPointF((x0 + x1) / 2.0, y0), QPointF((x0 + x1) / 2.0, y1))
                p.drawLine(QPointF(x0, (y0 + y1) / 2.0), QPointF(x1, (y0 + y1) / 2.0))
            else:                                      # a door / gate: a panel on the floor
                p.fillRect(r, self._DOOR)
                p.setPen(QPen(self._WALL, 1.4))
                p.drawRect(r)
                # a leaf stile near the latch edge, so it reads as a door
                p.setPen(QPen(self._WALL, 0.6))
                kx = x0 + (x1 - x0) * 0.82
                p.drawLine(QPointF(kx, y0 + 3.0), QPointF(kx, y1 - 3.0))
            # size label, centred
            p.setPen(QPen(QColor(20, 20, 20)))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, f"{fmt_in(ww)}×{fmt_in(hh)}")
            # height dimension on the left: a window shows its sill above the
            # floor; a door/gate sits on the floor, so it shows its head height.
            p.setPen(QPen(self._DIM, 1.0))
            dx = x0 - 6.0
            if kind == "window":
                ytop, label = y1, f"sill {fmt_in(sill)}"
            else:
                ytop, label = y0, f"head {fmt_in(head)}"
            p.drawLine(QPointF(dx, base_y), QPointF(dx, ytop))
            p.drawLine(QPointF(dx - 3, base_y), QPointF(dx + 3, base_y))
            p.drawLine(QPointF(dx - 3, ytop), QPointF(dx + 3, ytop))
            p.save()
            p.translate(dx - 4, (base_y + ytop) / 2.0)
            p.rotate(-90)
            p.drawText(QPointF(0, 0), label)
            p.restore()
            # centre-offset dimension: a horizontal tick from centreline to centre
            oy = base_y - 14.0
            p.drawLine(QPointF(X(apex), oy), QPointF(X(c), oy))
            p.drawLine(QPointF(X(c), oy - 3), QPointF(X(c), oy + 3))
            p.drawText(QPointF((X(apex) + X(c)) / 2.0 - 10, oy - 4), fmt_in(abs(c - apex)))


class _WallElevationCanvas(QWidget):
    """0313: the elevation a plan CAMERA sees -- the whole wall PLANE it faces,
    floor to ceiling, with every DOOR and WINDOW located to scale. Reads
    `CameraItem.elevation()`: `faces[]` (each `label`, `width_in`, `windows[]`,
    `doors[]`), laid left->right as the camera sees them; `left_return`/
    `right_return` (the side walls that turn toward the camera) draw as short
    labelled return ticks at the two ends.

    For legibility each wall carries just its W-number on top; its width is a
    blue dimension along the bottom, and a RUN of walls too narrow to dimension
    on their own is aggregated into a single group dimension. The seams between
    walls on one plane are faint grey so they don't fight the elevation; one blue
    height dimension down the left gives the storey height. A window draws as
    glass with a muntin cross, a door/gate as a floor panel, each with its size
    and sill/head. The twin of `_ElevationCanvas`, flat-ceilinged (a roof-capped
    top is a follow-on)."""

    _WALL = QColor(60, 60, 60)
    _GLASS = QColor(191, 219, 254)
    _DOOR = QColor(214, 211, 203)
    _DIM = QColor(37, 99, 235)
    _CENTRE = QColor(150, 150, 150)
    _RET = QColor(120, 120, 120)
    _SEAM = QColor(205, 205, 205)          # faint seam between walls on one plane
    _MIN_DIM_PX = 36.0                      # narrower than this -> grouped dimension

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.setMinimumHeight(260)

    def set_data(self, data):
        self.data = data
        self.update()

    def sizeHint(self):
        return QSize(560, 320)

    @staticmethod
    def _run_width(e) -> float:
        return sum(float(fc.get("width_in", 0.0)) for fc in e.get("faces", []))

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(255, 255, 255))
        e = self.data
        W = self._run_width(e) if e else 0.0
        H = float(e.get("height_in", 0.0)) if e else 0.0
        if not e or W <= 0.0 or H <= 0.0:
            p.setPen(QPen(QColor(120, 120, 120)))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "The camera faces no wall — aim it at a wall.")
            return
        ml, mr, mt, mb = 52.0, 40.0, 30.0, 54.0
        scale = max(min((w - ml - mr) / W, (h - mt - mb) / H), 0.01)
        run_px = W * scale
        left_px = (w - run_px) / 2.0           # centre the run
        base_y = h - mb
        f = p.font()
        f.setPointSize(8)
        p.setFont(f)

        def X(xin):                            # inches from the run's LEFT end
            return left_px + xin * scale

        def Y(yin):
            return base_y - yin * scale

        faces = e.get("faces", [])
        edges = [0.0]                          # cumulative run inches at each seam
        for fc in faces:
            edges.append(edges[-1] + float(fc.get("width_in", 0.0)))

        # the floor baseline + its absolute datum label
        p.setPen(QPen(self._WALL, 1.4))
        p.drawLine(QPointF(X(0.0) - 26, base_y), QPointF(X(W) + 26, base_y))
        p.setPen(QPen(QColor(90, 90, 90)))
        p.drawText(QPointF(6, base_y + 15),
                   f"floor {fmt_in(float(e.get('floor_abs_in', 0.0)))}")

        # the openings on every faced wall (drawn first, under the wall outline)
        for i, fc in enumerate(faces):
            mid = 0.5 * (edges[i] + edges[i + 1])
            for wd in list(fc.get("windows", [])) + list(fc.get("doors", [])):
                self._draw_opening(p, X, Y, base_y, mid, wd)

        # the run outline (bold) + faint seams where one wall meets the next
        p.setPen(QPen(self._WALL, 1.6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(QPointF(X(0.0), Y(H)), QPointF(X(W), base_y)))
        p.setPen(QPen(self._SEAM, 1.0))
        for i in range(1, len(faces)):
            x = X(edges[i])
            p.drawLine(QPointF(x, Y(H)), QPointF(x, base_y))

        # the wall labels on top -- just W-number, where the panel is wide enough
        p.setPen(QPen(QColor(20, 20, 20)))
        fm = p.fontMetrics()
        for i, fc in enumerate(faces):
            lbl = fc.get("label", "")
            x0, x1 = X(edges[i]), X(edges[i + 1])
            if lbl and (x1 - x0) >= fm.horizontalAdvance(lbl) + 4:
                p.drawText(QRectF(x0, Y(H) - 17, x1 - x0, 15),
                           Qt.AlignmentFlag.AlignCenter, lbl)

        # the storey height (blue, far left) and the per-wall widths (blue, below,
        # narrow walls aggregated into one dimension)
        self._draw_height_dim(p, X, Y, base_y, H)
        self._draw_width_dims(p, X, base_y, edges, scale)

        # the return walls -- short ticks turning toward the camera, labelled
        self._draw_return(p, X(0.0), base_y, -1, e.get("left_return"))
        self._draw_return(p, X(W), base_y, +1, e.get("right_return"))

    def _draw_width_dims(self, p, X, base_y, edges, scale):
        """A blue dimension string under the run: one dimension per wall, but any
        RUN of walls too narrow to carry their own number is aggregated and the
        group dimensioned once."""
        n = len(edges) - 1
        groups, i = [], 0
        while i < n:                           # (a, b) inclusive face-index spans
            if (edges[i + 1] - edges[i]) * scale >= self._MIN_DIM_PX:
                groups.append((i, i))
                i += 1
            else:
                j = i
                while j < n and (edges[j + 1] - edges[j]) * scale < self._MIN_DIM_PX:
                    j += 1
                groups.append((i, j - 1))
                i = j
        dim_y = base_y + 22.0
        p.setPen(QPen(self._DIM, 1.0))
        for a, b in groups:
            xL, xR = X(edges[a]), X(edges[b + 1])
            p.drawLine(QPointF(xL, dim_y), QPointF(xR, dim_y))
            p.drawLine(QPointF(xL, dim_y - 4), QPointF(xL, dim_y + 4))
            p.drawLine(QPointF(xR, dim_y - 4), QPointF(xR, dim_y + 4))
            p.drawText(QRectF(xL, dim_y + 2, xR - xL, 14),
                       Qt.AlignmentFlag.AlignCenter,
                       fmt_in(edges[b + 1] - edges[a]))

    def _draw_height_dim(self, p, X, Y, base_y, H):
        """A single blue height dimension down the left of the run -- floor to the
        storey ceiling (the top label no longer carries the height)."""
        x = X(0.0) - 18.0
        top = Y(H)
        p.setPen(QPen(self._DIM, 1.0))
        p.drawLine(QPointF(x, base_y), QPointF(x, top))
        p.drawLine(QPointF(x - 4, base_y), QPointF(x + 4, base_y))
        p.drawLine(QPointF(x - 4, top), QPointF(x + 4, top))
        p.save()
        p.translate(x - 4, 0.5 * (base_y + top))
        p.rotate(-90)
        p.drawText(QRectF(-26, -14, 52, 13), Qt.AlignmentFlag.AlignCenter, fmt_in(H))
        p.restore()

    def _draw_opening(self, p, X, Y, base_y, mid_in, wd):
        c = mid_in + float(wd["centre_in"])    # the opening's centre, in run inches
        ww, hh = float(wd["w_in"]), float(wd["h_in"])
        sill, head = float(wd["sill_in"]), float(wd["head_in"])
        kind = wd.get("kind", "window")
        if ww <= 0.0 or hh <= 0.0:
            return
        x0, x1 = X(c - ww / 2.0), X(c + ww / 2.0)
        y0, y1 = Y(head), Y(sill)
        r = QRectF(QPointF(x0, y0), QPointF(x1, y1))
        if kind == "window":
            p.fillRect(r, self._GLASS)
            p.setPen(QPen(self._WALL, 1.2))
            p.drawRect(r)
            p.setPen(QPen(self._WALL, 0.5))
            p.drawLine(QPointF((x0 + x1) / 2.0, y0), QPointF((x0 + x1) / 2.0, y1))
            p.drawLine(QPointF(x0, (y0 + y1) / 2.0), QPointF(x1, (y0 + y1) / 2.0))
        else:
            p.fillRect(r, self._DOOR)
            p.setPen(QPen(self._WALL, 1.4))
            p.drawRect(r)
            p.setPen(QPen(self._WALL, 0.6))
            kx = x0 + (x1 - x0) * 0.82
            p.drawLine(QPointF(kx, y0 + 3.0), QPointF(kx, y1 - 3.0))
        p.setPen(QPen(QColor(20, 20, 20)))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, f"{fmt_in(ww)}×{fmt_in(hh)}")
        # height dimension on the left: a window its sill, a door its head
        p.setPen(QPen(self._DIM, 1.0))
        dx = x0 - 6.0
        if kind == "window":
            ytop, label = y1, f"sill {fmt_in(sill)}"
        else:
            ytop, label = y0, f"head {fmt_in(head)}"
        p.drawLine(QPointF(dx, base_y), QPointF(dx, ytop))
        p.drawLine(QPointF(dx - 3, base_y), QPointF(dx + 3, base_y))
        p.drawLine(QPointF(dx - 3, ytop), QPointF(dx + 3, ytop))
        p.save()
        p.translate(dx - 4, (base_y + ytop) / 2.0)
        p.rotate(-90)
        p.drawText(QPointF(0, 0), label)
        p.restore()

    def _draw_return(self, p, x, base_y, side, ret):
        """A side wall that turns the corner toward the camera: a short tick
        angling down-and-out from the run's end, with its W-number."""
        if not ret:
            return
        ex, ey = x + side * 26.0, base_y + 18.0
        p.setPen(QPen(self._RET, 1.4))
        p.drawLine(QPointF(x, base_y), QPointF(ex, ey))
        p.setPen(QPen(QColor(70, 70, 70)))
        lbl = ret.get("label", "")
        flags = (Qt.AlignmentFlag.AlignRight if side < 0 else Qt.AlignmentFlag.AlignLeft)
        box = (QRectF(ex - 48, ey + 1, 46, 14) if side < 0
               else QRectF(ex + 2, ey + 1, 46, 14))
        p.drawText(box, flags | Qt.AlignmentFlag.AlignVCenter, lbl)


class CameraElevationDialog(QDialog):
    """0313: the elevation of the wall a plan CAMERA faces, straight on and to
    scale. Non-modal; constructed `(camera, view)`. A "Refresh" re-reads the
    camera (aim or move it, then refresh) and the note names the wall or says the
    camera faces open space."""

    def __init__(self, camera, view=None, parent=None):
        super().__init__(parent or view)
        self.camera = camera
        self.setWindowTitle("Camera elevation")
        self.setModal(False)
        lay = QVBoxLayout(self)
        self.canvas = _WallElevationCanvas(self)
        lay.addWidget(self.canvas, 1)
        self.note = QLabel("")
        self.note.setWordWrap(True)
        self.note.setStyleSheet("color: #555;")
        lay.addWidget(self.note)
        row = QHBoxLayout()
        row.addStretch(1)
        b_refresh = QPushButton("Refresh")
        b_refresh.clicked.connect(self.refresh)
        row.addWidget(b_refresh)
        b_close = QPushButton("Close")
        b_close.clicked.connect(self.close)
        row.addWidget(b_close)
        lay.addLayout(row)
        self.resize(520, 360)
        self.refresh()

    def refresh(self):
        data = None
        try:
            data = self.camera.elevation()
        except Exception as exc:                         # never let a draw crash the app
            self.note.setText(f"Could not build the elevation: {exc}")
        self.canvas.set_data(data)
        if data is None:
            self.note.setText("The camera faces no wall. Aim it at a wall "
                              "(drag the handle), then Refresh.")
        else:
            faces = data.get("faces", [])
            nd = sum(len(fc.get("doors", [])) for fc in faces)
            nw = sum(len(fc.get("windows", [])) for fc in faces)
            width = sum(float(fc.get("width_in", 0.0)) for fc in faces)
            labels = ", ".join(fc.get("label", "") for fc in faces)
            room = data.get("room_name", "")
            where = f"{room}: " if room else ""
            rets = [r["label"] for r in (data.get("left_return"),
                                         data.get("right_return")) if r]
            ret_txt = (f" Returns: {', '.join(rets)}." if rets else "")
            self.note.setText(
                f"{where}wall {labels} — {fmt_in(width)} wide, "
                f"{nw} window(s), {nd} door(s).{ret_txt} Straight-on, to scale; "
                "heights from the floor. Move or aim the camera, then Refresh.")


class FloorLevelsDialog(QDialog):
    """Floors ▸ <floor> ▸ Elevation and height… (R6.0, 0197-ruling.md sec2,
    closing D50): the storey's two numbers, in inches from the building's
    datum -- the base and the storey height (its wall top in 3D).

    The BASE is DERIVED from the floor below by default (his word, 2026-11-05):
    a storey sits on the one beneath it, so its base IS that floor's top, shown
    read-only. Untick "Sits on the floor below" to set a custom base -- a
    basement (a negative base), a split level, a deliberate gap. The LOWEST
    floor has no floor below, so its base (the building's datum) is always
    editable. `below_top` is the floor-below's top (`levels.py` computes it);
    None for the lowest floor. A lower floor's height change re-derives the
    stack above it (`set_floor_levels`)."""

    def __init__(self, floor, parent=None, below_top=None):
        super().__init__(parent)
        self.setWindowTitle(f"Floor '{floor.name}': elevation and height")
        self._below_top = None if below_top is None else float(below_top)
        form = QFormLayout(self)

        self.ck_stack = QCheckBox("Sits on the floor below")
        stacks = (self._below_top is not None
                  and abs(float(floor.elevation_in) - self._below_top) < 0.5)
        self.ck_stack.setChecked(stacks)
        if self._below_top is None:
            self.ck_stack.setVisible(False)      # the lowest floor: nothing to sit on
        form.addRow("", self.ck_stack)

        self.sp_elev = QDoubleSpinBox()
        self.sp_elev.setRange(-1200.0, 2400.0)
        self.sp_elev.setDecimals(1)
        self.sp_elev.setSuffix(" in")
        self.sp_elev.setValue(self._below_top if stacks else float(floor.elevation_in))
        form.addRow("Elevation of the level's base", self.sp_elev)

        self.sp_height = QDoubleSpinBox()
        self.sp_height.setRange(12.0, 600.0)
        self.sp_height.setDecimals(1)
        self.sp_height.setSuffix(" in")
        self.sp_height.setValue(float(floor.height_in))
        form.addRow("Storey height", self.sp_height)

        self.note = QLabel("")
        self.note.setWordWrap(True)
        self.note.setStyleSheet("color: #666;")
        form.addRow(self.note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        self.ck_stack.toggled.connect(self._on_stack_toggled)
        self._refresh()

    def _derived(self) -> bool:
        return self._below_top is not None and self.ck_stack.isChecked()

    def _on_stack_toggled(self, on):
        if on and self._below_top is not None:
            self.sp_elev.setValue(self._below_top)
        self._refresh()

    def _refresh(self):
        derived = self._derived()
        self.sp_elev.setEnabled(not derived)     # derived -> greyed, read from the floor below
        if self._below_top is None:
            self.note.setText("The lowest floor: its base is the building's datum. The "
                              "3D view stacks levels by elevation and reads the storey "
                              "height as the level's wall top.")
        elif derived:
            self.note.setText(f"Base derived from the floor below (its top, "
                              f"{fmt_in(self._below_top)}). Untick to set a custom base "
                              f"-- a basement, a split level.")
        else:
            self.note.setText("Custom base. Tick 'Sits on the floor below' to keep it on "
                              "the floor beneath (its elevation plus its height).")

    def values(self):
        if self._derived():
            return self._below_top, float(self.sp_height.value())
        return float(self.sp_elev.value()), float(self.sp_height.value())


def _mint_opening_id():
    """A fresh, schema-valid opening id (`^[A-Za-z][A-Za-z0-9_-]*$`), unique
    enough for a dormer's own face windows -- the dialog is their only in-app
    author, so nothing else is minting into the same list."""
    import uuid
    return "dwin" + uuid.uuid4().hex[:10]


class _DormerWindowDialog(QDialog):
    """One window on a dormer's face (Phase C, 0291). The fields the dormer's
    single `opening` record carries -- a WWHH size code (as a wall opening),
    which end of the face the offset is measured from, the offset to the near
    edge (or, from the centre, of the window's centre), and the sill above the
    dormer's level base. Returns the same dict shape `fp3d._face_openings`
    consumes; the size code is validated here so a bad one never reaches the
    record (a dormer has no error channel the way a wall does)."""

    def __init__(self, opening=None, parent=None, sill_floor_in=0.0, ceiling_in=None):
        super().__init__(parent)
        from floorplanner.model import DEFAULT_SILL_IN
        self.setWindowTitle("Dormer window")
        o = dict(opening or {})
        self._id = o.get("id")              # preserved on edit, minted on create
        anchor = o.get("anchor", {}) or {}
        # P5 (Patrick, 2026-11-06): the sill is EDITED from the dormer's own
        # floor -- the top of the ceiling of the storey it sits over -- and
        # STORED as the host-datum number (`sill_floor_in` is that floor above
        # the datum; a display conversion, not a second record, 0294 §1c). The
        # window is clamped to `[floor, ridge]`: sill never below the floor it is
        # on, head never above the dormer roof line (`ceiling_in`, the ridge).
        self._floor_in = float(sill_floor_in)
        self._ceiling_in = float(ceiling_in) if ceiling_in is not None else None
        form = QFormLayout(self)
        self.ed_code = QLineEdit(str(o.get("code", "3040")))
        self.ed_code.setToolTip('Width then height in inches, e.g. 4860 = 48" '
                                'wide by 60" tall.')
        form.addRow("Size (WWHH)", self.ed_code)
        self.cb_from = QComboBox()
        self.cb_from.addItem("Left end of face", "v1")
        self.cb_from.addItem("Right end of face", "v2")
        self.cb_from.addItem("Centre of face", "center")
        self.cb_from.setCurrentIndex(
            {"v1": 0, "v2": 1, "center": 2}.get(anchor.get("from", "v1"), 0))
        form.addRow("Position from", self.cb_from)
        self.sp_off = QDoubleSpinBox()
        self.sp_off.setRange(-1200.0, 1200.0)
        self.sp_off.setDecimals(1)
        self.sp_off.setSuffix(" in")
        self.sp_off.setValue(float(anchor.get("offset_in", 0.0)))
        self.sp_off.setToolTip("To the window's near edge from the chosen end; "
                               "from the centre, the offset of its centre.")
        form.addRow("Offset", self.sp_off)
        self.sp_sill = QDoubleSpinBox()
        hi = (self._ceiling_in - self._floor_in) if self._ceiling_in is not None else 400.0
        self.sp_sill.setRange(0.0, max(0.0, hi))
        self.sp_sill.setDecimals(1)
        self.sp_sill.setSuffix(" in")
        # the stored sill is above the host datum; show it above the dormer floor
        stored = float(o.get("sill_in", self._floor_in + DEFAULT_SILL_IN))
        self.sp_sill.setValue(max(0.0, stored - self._floor_in))
        self.sp_sill.setToolTip("Height of the sill above the DORMER's own floor "
                                "(the top of the ceiling of the storey below). The "
                                "window must fit under the dormer's roof line.")
        form.addRow("Sill above dormer floor", self.sp_sill)
        if self._ceiling_in is not None:
            note = QLabel(f"The dormer floor is {fmt_in(self._floor_in)} above the "
                          f"datum and the ridge is at {fmt_in(self._ceiling_in)}; the "
                          f"window fits between -- sill 0 sits on the dormer floor.")
            note.setWordWrap(True)
            note.setStyleSheet("color: #666;")
            form.addRow("", note)
        self.lab_err = QLabel("")
        self.lab_err.setStyleSheet("color: #b45309;")
        self.lab_err.setWordWrap(True)
        form.addRow("", self.lab_err)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def accept(self):
        try:
            _w, h = parse_wwhh(self.ed_code.text())
        except (ValueError, TypeError):
            self.lab_err.setText("Size must be 4 to 6 digits, width then "
                                 "height (e.g. 3040 or 4860).")
            return
        # P5: the head may not rise above the dormer roof line (the ridge)
        if self._ceiling_in is not None:
            head = self._floor_in + float(self.sp_sill.value()) + h
            if head > self._ceiling_in + 0.01:
                room = self._ceiling_in - self._floor_in
                self.lab_err.setText(
                    f"The window is too tall for the dormer: its head would reach "
                    f"{fmt_in(head - self._floor_in)} above the dormer floor, past "
                    f"the ridge at {fmt_in(room)}. Lower the sill or the height.")
                return
        super().accept()

    def opening(self):
        # STORE the sill above the host datum (the dormer floor plus the edited
        # height above it) -- the one record the 3D and the dialog share.
        return {"id": self._id or _mint_opening_id(),
                "kind": "window",
                "code": self.ed_code.text().strip(),
                "anchor": {"from": self.cb_from.currentData(),
                           "offset_in": float(self.sp_off.value())},
                "sill_in": self._floor_in + float(self.sp_sill.value())}


class RoofEndOnDialog(QDialog):
    """The End-On marker's dialog (0140-ruling.md, R2b): a live end-on
    drawing with three editable values -- ridge height, eaves height,
    pitch -- one relation, two degrees of freedom. RULED (0139-ruling.md
    sec2, sharpened by Patrick's own worked example in 0140-ruling.md
    sec2): the two most recently EDITED fields are the inputs; the third
    is derived and recomputed live. At first open the heights are the
    primaries and pitch is derived, matching how the roof was created.

    REPLACES 0139-ruling.md R2's plainer `RoofHeightsDialog` entirely
    (0140-ruling.md sec1: "one dialog, two doors") -- reached from the
    marker's right-click, from selecting any ridge, AND from the
    ridge-sketch tool's own initial heights prompt.

    R4b (0154-ruling.md sec3) makes this same dialog the PARAMETERS
    dialog -- still one dialog, the same doors -- adding:

    * per-side overhang, with a "same both sides" link that is on
      whenever the two currently agree (every sketched roof) and mirrors
      an edit to the other side while it stays on;
    * gable/hip per end, the ends named by the marker ("end with the
      marker" / "other end") since that is the one physical way a user
      tells the two ridge ends apart on screen -- the mapping to
      `gable[0]`/`gable[1]` goes through `marker_end` at open time;
    * the `room_top` binding (requirement 5): while bound the eaves
      field is derived from the covered rooms' ceilings (`roofs.
      bound_eaves_height`) and locked, so the three-way rule runs
      between ridge and pitch alone -- the binding is an INPUT that
      cannot be the derived field. The measurement's own note (which
      rooms, whether they differ, whether nothing was found) is shown
      live under the toggle and repeated in the status bar on apply.

    The pitch field is the LEFT side's (`span_in[0]`) -- one editable
    pitch, because with one ridge/eaves pair the two sides' pitches are
    not independent; the right side's is shown on the drawing as `P'`
    whenever the spans differ (nothing before R4c can make them)."""

    _FIELDS = ("pitch", "ridge_h", "eaves_h")   # order = initial recency

    def __init__(self, roof: RoofItem, parent=None, select_opening=None):
        super().__init__(parent)
        self.roof = roof
        self._dormer = getattr(roof, "host", None) is not None
        self._level_combo = None          # P3: the dormer's "Edited on level" selector
        self._wall_checks = {}            # P4: the "Walls on <level>" checkboxes
        self._select_opening = select_opening   # P5 §2: a window to pre-select
        # Phase C (0291): a working copy of the dormer's own face windows,
        # edited through the list below and written back in `apply()`.
        self._face_openings = [dict(o) for o in (getattr(roof, "openings", None) or [])]
        self.setWindowTitle("Dormer parameters (end-on)" if self._dormer
                            else "Roof parameters (end-on)")
        self._recent = list(self._FIELDS)   # last element = most recent edit
        self._programmatic = False
        self.binding = None                 # RoomTopBinding while bound

        # #3 (0294 §4): the dialog is now tabbed -- "Parameters" (everything that
        # was here) and "Elevation" (the gable end to scale). The buttons sit
        # below the tabs, on the outer layout.
        outer = QVBoxLayout(self)
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs)
        _params = QWidget()
        lay = QVBoxLayout(_params)
        self.tabs.addTab(_params, "Parameters")
        self.canvas = _EndOnCanvas(self)
        self.canvas.setMaximumHeight(200)       # a reference sketch, not the bulk
        lay.addWidget(self.canvas)

        # Two columns (Patrick, 2026-11-05: "the dialog window opens across my
        # entire screen"): heights/form/spans/overhang on the LEFT, ends/hips and
        # the dormer's level on the RIGHT, so the box is about half as tall.
        form = QFormLayout()              # left column
        form_r = QFormLayout()            # right column (ends, hips, dormer level)
        self.sp_ridge = QDoubleSpinBox()
        self.sp_ridge.setRange(0.0, 600.0)
        self.sp_ridge.setSuffix(" in")
        self.lab_ridge = QLabel("Ridge height (R)")
        form.addRow(self.lab_ridge, self.sp_ridge)

        self.sp_eaves = QDoubleSpinBox()
        self.sp_eaves.setRange(0.0, 600.0)
        self.sp_eaves.setSuffix(" in")
        self.lab_eaves = QLabel("Eaves height (H)")
        form.addRow(self.lab_eaves, self.sp_eaves)

        self.sp_pitch = QDoubleSpinBox()
        self.sp_pitch.setRange(0.0, 80.0)
        self.sp_pitch.setDecimals(1)
        self.sp_pitch.setSuffix(" deg")
        self.lab_pitch = QLabel("Pitch (P)")
        form.addRow(self.lab_pitch, self.sp_pitch)

        # -- R4b: the room-top binding (0154-ruling.md sec2, item 5) --
        self.ck_bind = QCheckBox("Bind eaves to the room top")
        self.ck_bind.setChecked(getattr(roof, "eaves_bind", "manual") == "room_top")
        form.addRow("", self.ck_bind)
        self.lab_bind = QLabel("")
        self.lab_bind.setWordWrap(True)
        self.lab_bind.setStyleSheet("color: #666;")
        form.addRow("", self.lab_bind)

        # -- R4b: per-side eaves span (ridge to each eaves wall's centreline)
        # -- Patrick's own check: the sketch's one-number pick mirrored to
        # the far side left an off-centre ridge with a lopsided footprint,
        # and nothing before R4c could correct it. Editable here so an
        # existing roof can be fixed without redrawing; R4c's eave-edge
        # grips will drag the same two values.
        # -- 0248-report.md sec3 plan A: the form. A shed is one plane down
        # the LEFT side; its right span and overhang are 0 and not editable.
        self.cb_form = QComboBox()
        self.cb_form.addItems(["Gable (two planes)", "Shed (one plane, left side)"])
        self.cb_form.setCurrentIndex(1 if getattr(roof, "form", "gable") == "shed" else 0)
        form.addRow("Form", self.cb_form)

        span_l, span_r = (float(v) for v in getattr(roof, "span_in", [144.0, 144.0]))
        self.sp_span_l = QDoubleSpinBox()
        self.sp_span_l.setRange(1.0, 1200.0)
        self.sp_span_l.setDecimals(1)
        self.sp_span_l.setSuffix(" in")
        self.sp_span_l.setValue(span_l)
        form.addRow("Eaves span, left side", self.sp_span_l)
        self.sp_span_r = QDoubleSpinBox()
        self.sp_span_r.setRange(0.0, 1200.0)      # 0 only ever holds on a shed
        self.sp_span_r.setDecimals(1)
        self.sp_span_r.setSuffix(" in")
        self.sp_span_r.setValue(span_r)
        form.addRow("Eaves span, right side", self.sp_span_r)

        # -- R4b: per-side overhang (requirement 1) --
        oh_l, oh_r = (float(v) for v in getattr(roof, "overhang_in", [0.0, 0.0]))
        self.sp_oh_l = QDoubleSpinBox()
        self.sp_oh_l.setRange(0.0, 120.0)
        self.sp_oh_l.setDecimals(1)
        self.sp_oh_l.setSuffix(" in")
        self.sp_oh_l.setValue(oh_l)
        form.addRow("Overhang, left side", self.sp_oh_l)
        self.sp_oh_r = QDoubleSpinBox()
        self.sp_oh_r.setRange(0.0, 120.0)
        self.sp_oh_r.setDecimals(1)
        self.sp_oh_r.setSuffix(" in")
        self.sp_oh_r.setValue(oh_r)
        form.addRow("Overhang, right side", self.sp_oh_r)
        self.ck_oh_same = QCheckBox("Same overhang both sides")
        self.ck_oh_same.setChecked(abs(oh_l - oh_r) < 1e-6)
        form.addRow("", self.ck_oh_same)

        # -- R4b: gable <-> hip per end, named by the marker --
        self._marker_end = 1 if getattr(roof, "marker_end", 1) else 0
        gable = list(getattr(roof, "gable", [True, True]))
        self.cb_end_marker = QComboBox()
        self.cb_end_marker.addItems(["Gable", "Hip"])
        self.cb_end_marker.setCurrentIndex(0 if gable[self._marker_end] else 1)
        form_r.addRow("End with the marker", self.cb_end_marker)
        self.cb_end_other = QComboBox()
        self.cb_end_other.addItems(["Gable", "Hip"])
        self.cb_end_other.setCurrentIndex(0 if gable[1 - self._marker_end] else 1)
        form_r.addRow("Other end", self.cb_end_other)
        # -- 0258 (0248 sec2 item 6): the hip run per end. Enabled while that
        # end is a hip; seeded with the end's own run when the record says,
        # else the derived one (the mean of the spans); OK writes an end's
        # run only where it differs from the derived value, so an untouched
        # end stays derived and follows the spans.
        self.sp_run = {}
        for end, label in ((self._marker_end, "Hip run, marker end"),
                           (1 - self._marker_end, "Hip run, other end")):
            sp = QDoubleSpinBox()
            sp.setRange(0.0, 1200.0)
            sp.setDecimals(1)
            sp.setSuffix(" in")
            stored = list(getattr(roof, "hip_run_in", None) or [None, None])
            sp.setValue(float(stored[end]) if stored[end] is not None
                        else (span_l + span_r) / 2.0)
            sp.setToolTip("How far the hip runs past this ridge end; the mean "
                          "of the two spans unless set here")
            form_r.addRow(label, sp)
            self.sp_run[end] = sp
        self._refresh_run_fields()
        if self._dormer:
            # R5b: a dormer's eaves are its cheek top, not a room's ceiling,
            # and its back end is DERIVED into the host -- neither is a
            # choice here. The refusal (a ridge that cannot meet the host)
            # is shown inline, never as a modal (headless-safe).
            self.ck_bind.setChecked(False)
            self.ck_bind.setEnabled(False)
            other = self.cb_end_other if self._marker_end == 0 else self.cb_end_marker
            other.setCurrentIndex(0)
            other.setEnabled(False)
            other.setToolTip("A dormer's back end is derived: it meets the host roof")
            self.lab_dormer = QLabel("")
            self.lab_dormer.setWordWrap(True)
            self.lab_dormer.setStyleSheet("color: #b45309;")
            form_r.addRow("", self.lab_dormer)
            # P3 (0293 §5 P3 ii): "Pinned to" and "Edited on level". The host's
            # level and pitch; a selector over the two legal levels that EXIST
            # (the host's and the one above), current ticked -- OK promotes or
            # demotes (apply()). Disabled with a note on a one-layer plan.
            from floorplanner.roofs import legal_dormer_levels  # late: cycle guard
            host = roof.host
            hp = max(0.0, host.ridge_h_in - host.eaves_h_in)
            hspan = host.span_in[0] if host.span_in[0] > 1e-6 else 1.0
            host_pitch = math.degrees(math.atan2(hp, hspan))
            lab_pin = QLabel(f"Host roof on level '{host.floor}' (pitch "
                             f"{host_pitch:.1f}°); the dormer's heights are "
                             f"measured from its base.")
            lab_pin.setWordWrap(True)
            lab_pin.setMaximumWidth(240)
            lab_pin.setStyleSheet("color: #1d4ed8;")
            form_r.addRow("Pinned to", lab_pin)
            self._level_combo = QComboBox()
            legal = legal_dormer_levels(roof)
            for lv in legal:
                self._level_combo.addItem(lv, lv)
            if roof.floor in legal:
                self._level_combo.setCurrentIndex(legal.index(roof.floor))
            if len(legal) <= 1:
                self._level_combo.setEnabled(False)
                self._level_combo.setToolTip(
                    f"Add a level above '{roof.floor}' to move the dormer")
            form_r.addRow("Edited on level", self._level_combo)
            # 0296: the dormer's own walls on the storey above -- three
            # checkboxes, on by default, so a wall can be opted out (a hand-drawn
            # wall already on a line is not welded into by surprise). Enabled only
            # while a storey above exists (its room is the one they close).
            self._wall_checks = {}
            above_exists = len(legal) > 1
            above_name = legal[-1] if above_exists else "the storey above"
            on = getattr(roof, "dormer_wall_parts",
                         {"face", "cheek_left", "cheek_right"})
            for part, plabel in (("face", "Face"), ("cheek_left", "Left cheek"),
                                 ("cheek_right", "Right cheek")):
                cb = QCheckBox(plabel)
                cb.setChecked(part in on and above_exists)
                cb.setEnabled(above_exists)
                if not above_exists:
                    cb.setToolTip("Add a level above the host to close its attic room")
                self._wall_checks[part] = cb
                form_r.addRow(f"Walls on {above_name}" if part == "face" else "", cb)
        # keep the fields narrow so two columns do not widen the box: a spin
        # box with a 3-digit value and a suffix needs ~110px, not the ~400 it
        # claims by default, and the wrapped notes wrap rather than stretch.
        for sb in (self.sp_ridge, self.sp_eaves, self.sp_pitch, self.sp_span_l,
                   self.sp_span_r, self.sp_oh_l, self.sp_oh_r,
                   *self.sp_run.values()):
            sb.setFixedWidth(110)
        for cb in (self.cb_form, self.cb_end_marker, self.cb_end_other):
            cb.setFixedWidth(190)
        if self._level_combo is not None:
            self._level_combo.setFixedWidth(190)
        for lb in (getattr(self, "lab_dormer", None),
                   getattr(self, "lab_bind", None)):
            if lb is not None:
                lb.setMaximumWidth(240)
        # the two columns side by side; the trailing stretch keeps them at
        # their natural width (left-packed) instead of spreading across the box
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_r.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        cols = QHBoxLayout()
        cols.addLayout(form)
        cols.addSpacing(24)
        cols.addLayout(form_r)
        cols.addStretch(1)
        lay.addLayout(cols)

        # Phase C (0291): the dormer's own face windows -- a list editor,
        # only for a dormer. Its records are the single source the plan shadow
        # and the 3D face both read.
        if self._dormer:
            self._build_windows_ui(lay)

        # -- R6.c: where this level stands in the building. Every height
        # in this dialog is measured from the level's own base
        # (0140-ruling.md sec3), which is the ground only on a level whose
        # elevation is 0 -- so on any other level the absolute heights are
        # said, live, beside the level-relative ones that are typed.
        self.lab_level = QLabel("")
        self.lab_level.setWordWrap(True)
        self.lab_level.setMaximumWidth(640)
        self.lab_level.setStyleSheet("color: #1d4ed8;")
        lay.addWidget(self.lab_level)

        note = QLabel("Both heights measured from the level's own base "
                      "(the base line); the wall top is shown for "
                      "reference. Editing any two derives the third -- "
                      "the derived field is marked — derived. A span is "
                      "the ridge-to-wall-centreline distance; the overhang "
                      "extends that far past the wall (24 in = two 12 in "
                      "grid lines). A hip end runs the roof past that "
                      "ridge end by the side span.")
        note.setWordWrap(True)
        note.setMaximumWidth(640)
        note.setStyleSheet("color: #666;")
        lay.addWidget(note)

        # #3 (0294 §4): the ELEVATION tab -- this roof's gable end, to scale,
        # with its window(s) located. A dormer draws its own face + openings; a
        # plain gable roof draws the gable end and the gable-end wall's windows.
        self.elev_canvas = _ElevationCanvas(self)
        _elev_page = QWidget()
        _elev_lay = QVBoxLayout(_elev_page)
        # #3 (2026-11-10): EITHER gable end may be drawn, and the blue dot marks
        # which. The selector lists the roof's LIVE gable ends (a dormer has one
        # face -> no selector; one gable end -> a single, disabled entry; none ->
        # the canvas says so). Picking an end moves the blue end-marker to that
        # ridge end as a live indicator -- restored to the roof's real marker end
        # when the dialog closes (`_restore_marker_dot`), so merely LOOKING at the
        # far end never rewrites which end the roof calls its marker.
        self.cb_elev_end = None
        self._marker_dot_home = True
        _gf = list(getattr(roof, "gable", [True, True]))
        self._elev_end = (self._marker_end if _gf[self._marker_end]
                          else (0 if _gf[0] else 1))
        if not self._dormer:
            _end_row = QHBoxLayout()
            _end_row.addWidget(QLabel("Gable end"))
            self.cb_elev_end = QComboBox()
            for _e in (self._marker_end, 1 - self._marker_end):
                if _gf[_e]:
                    self.cb_elev_end.addItem(
                        "Marker end (blue dot)" if _e == self._marker_end
                        else "Other end", _e)
            self.cb_elev_end.setEnabled(self.cb_elev_end.count() > 1)
            _idx = self.cb_elev_end.findData(self._elev_end)
            if _idx >= 0:
                self.cb_elev_end.setCurrentIndex(_idx)
            _end_row.addWidget(self.cb_elev_end)
            _end_row.addStretch(1)
            _elev_lay.addLayout(_end_row)
            self.cb_elev_end.currentIndexChanged.connect(lambda _i: self._on_elev_end())
            if self._elev_end != self._marker_end:
                self._place_marker_dot(self._elev_end)   # marker end is a hip
        _elev_lay.addWidget(self.elev_canvas)
        _elev_note = QLabel("The gable end, straight on and to scale. Every door "
                            "and window in the wall(s) under the gable is drawn and "
                            "located by its size, its height above the floor (a "
                            "window's sill, a door's head), and its offset from the "
                            "gable centreline. The blue dot in the plan marks the "
                            "end shown here.")
        _elev_note.setWordWrap(True)
        _elev_note.setStyleSheet("color: #666;")
        _elev_lay.addWidget(_elev_note)
        self.tabs.addTab(_elev_page, "Elevation")
        self.tabs.currentChanged.connect(lambda _i: self._refresh_elevation())
        self.finished.connect(self._restore_marker_dot)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        spans = [float(v) for v in getattr(roof, "span_in", [144.0, 144.0])]
        self.canvas.span_l, self.canvas.span_r = spans
        self.canvas.oh_l, self.canvas.oh_r = oh_l, oh_r
        self._set_field("ridge_h", float(roof.ridge_h_in), redraw=False)
        self._set_field("eaves_h", float(roof.eaves_h_in), redraw=False)
        self._refresh_binding(seed=True)
        self._recompute()   # seed pitch from the stored heights
        self._refresh_labels()

        if self._dormer:
            self._refresh_dormer_note()
        self.sp_ridge.valueChanged.connect(lambda v: self._on_edit("ridge_h", v))
        self.sp_eaves.valueChanged.connect(lambda v: self._on_edit("eaves_h", v))
        self.sp_pitch.valueChanged.connect(lambda v: self._on_edit("pitch", v))
        self.ck_bind.toggled.connect(self._on_bind_toggled)
        self._apply_form_to_widgets()
        self.cb_form.currentIndexChanged.connect(lambda _i: self._on_form())
        self.sp_span_l.valueChanged.connect(lambda _v: self._on_span())
        self.sp_span_r.valueChanged.connect(lambda _v: self._on_span())
        self.sp_oh_l.valueChanged.connect(lambda v: self._on_overhang(0, v))
        self.sp_oh_r.valueChanged.connect(lambda v: self._on_overhang(1, v))
        self.ck_oh_same.toggled.connect(self._on_oh_same_toggled)
        self.cb_end_marker.currentIndexChanged.connect(lambda _i: self._on_ends())
        self.cb_end_other.currentIndexChanged.connect(lambda _i: self._on_ends())
        self._refresh_elevation()

    def _refresh_elevation(self):
        """#3: feed the Elevation tab this roof's gable-end drawing, for the end
        the selector names. Reads the roof's stored geometry (the tab reflects
        the saved state; live spinbox tracking is a later parameter, his to
        order)."""
        canvas = getattr(self, "elev_canvas", None)
        if canvas is not None:
            canvas.set_data(self.roof.gable_elevation(end=getattr(self, "_elev_end", None)))

    def _on_elev_end(self):
        """#3 (2026-11-10): the Elevation tab's end selector changed -- redraw
        that end and move the blue dot to it, so the plan shows which end."""
        if self.cb_elev_end is None:
            return
        data = self.cb_elev_end.currentData()
        if data is None:
            return
        self._elev_end = int(data)
        self._place_marker_dot(self._elev_end)
        self._refresh_elevation()

    def _place_marker_dot(self, end):
        """Move the roof's blue end-marker to `end` (p1/p2) as a live indicator
        of the drawn end. Transient (the dialog is modal): `_restore_marker_dot`
        puts it back at the roof's real marker end when the dialog closes."""
        self._marker_dot_home = (end == self._marker_end)
        marker = getattr(self.roof, "marker", None)
        if marker is None:
            return
        try:
            marker.setPos(self.roof.p1 if end == 0 else self.roof.p2)
        except RuntimeError:
            pass                        # the C++ marker went away -- nothing to move

    def _restore_marker_dot(self, *_):
        """On close, snap the blue dot back to the roof's real marker end --
        viewing the far end never changed `marker_end`, only the dot's position."""
        if getattr(self, "_marker_dot_home", True):
            return
        marker = getattr(self.roof, "marker", None)
        if marker is None:
            return
        try:
            marker.sync_position()
        except RuntimeError:
            pass

    # -- the three-way recompute (0139-ruling.md sec2 / 0140-ruling.md sec2) --
    def _spin(self, field):
        return {"ridge_h": self.sp_ridge, "eaves_h": self.sp_eaves,
                "pitch": self.sp_pitch}[field]

    def _set_field(self, field, value, redraw=True):
        self._programmatic = True
        self._spin(field).setValue(value)
        self._programmatic = False
        if redraw:
            self._redraw()

    def _on_edit(self, field, _value):
        if self._programmatic:
            return
        self._recent.remove(field)
        self._recent.append(field)          # most recent = last
        self._recompute()
        self._refresh_labels()
        if self._dormer:
            self._refresh_dormer_note()

    # -- R5b: the dormer's derived back end and its refusal ---------------
    #: a shed dormer's high edge may sit this far under the host surface
    #: and still count as ON it (the drawing's own half-inch)
    SHED_EDGE_TOL_IN = 0.5

    def dormer_meet_in(self):
        """A GABLE dormer: inches from the face along the ridge to where the
        host's plane rises to the ridge height as currently typed; None = it
        never does (the dormer cannot stand: refused, 0191-ruling.md sec1).

        A SHED dormer (0256-report.md, his report on iteration 11's dormer):
        its ridge is its HIGH EDGE, lying on the host plane parallel to the
        host's ridge -- there is nothing to meet along it, and `meet_along`
        answered None at its first step (the host is already at that
        height), so this dialog refused every shed dormer and OK did
        nothing. A shed dormer stands while the host surface at BOTH ridge
        ends is at or above the typed ridge height (the edge on the roof,
        or buried under it, where the clip hides what is buried); the value
        is that clearance, 0 when the edge lies on the roof, None when it
        would float above the host."""
        from floorplanner.roofclip import Pt, meet_along, surface_height  # late: cycle guard
        host = getattr(self.roof, "host", None)
        if host is None:
            return None
        if self.form_value() == "shed":
            under = min(surface_height(host, Pt(p.x(), p.y())) - float(self.sp_ridge.value())
                        for p in (self.roof.p1, self.roof.p2))
            return max(0.0, under) if under >= -self.SHED_EDGE_TOL_IN else None
        ux, uy, _, _ = self.roof._axis()
        return meet_along(host, self.roof.p1, QPointF(ux, uy),
                          float(self.sp_ridge.value()))

    def _refresh_dormer_note(self):
        t = self.dormer_meet_in()
        shed = self.form_value() == "shed"
        if t is None and shed:
            self.lab_dormer.setText(
                "This ridge height stands above the host roof along the high "
                "edge -- the dormer would float. Lower the ridge (or raise the "
                "eaves) to continue.")
        elif t is None:
            self.lab_dormer.setText(
                "This ridge height never meets the host roof -- the dormer "
                "cannot stand. Lower the ridge (or the pitch) to continue.")
        elif shed:
            self.lab_dormer.setText(
                "High edge on the host roof; both ends are faces."
                if t < self.SHED_EDGE_TOL_IN else
                f"High edge {fmt_ftin(t)} under the host roof's surface: the "
                f"dormer's plane emerges from the roof lower down; both ends "
                f"are faces.")
        else:
            self.lab_dormer.setText(
                f"Back end derived: the ridge meets the host roof "
                f"{fmt_ftin(t)} behind the face.")

    # -- Phase C (0291): the dormer's own face windows --------------------
    def _build_windows_ui(self, lay):
        box = QGroupBox("Dormer face windows")
        v = QVBoxLayout(box)
        self.lst_windows = QListWidget()
        self.lst_windows.setMaximumHeight(96)   # a few rows, not a tall panel
        self.lst_windows.setToolTip(
            "The dormer's OWN windows, cut into its face. They show on the "
            "plan as a read-only shadow and in 3D; the storey's wall windows "
            "below are separate and edited on the wall.")
        self.lst_windows.itemDoubleClicked.connect(lambda _i: self._edit_window())
        v.addWidget(self.lst_windows)
        row = QHBoxLayout()
        b_add = QPushButton("Add window…")
        b_edit = QPushButton("Edit…")
        b_rem = QPushButton("Remove")
        b_add.clicked.connect(self._add_window)
        b_edit.clicked.connect(self._edit_window)
        b_rem.clicked.connect(self._remove_window)
        for b in (b_add, b_edit, b_rem):
            row.addWidget(b)
        row.addStretch(1)
        v.addLayout(row)
        lay.addWidget(box)
        self._refill_windows()

    def _window_label(self, o):
        anchor = o.get("anchor", {}) or {}
        end = {"v1": "left", "v2": "right", "center": "centre"}.get(
            anchor.get("from", "v1"), "left")
        off = float(anchor.get("offset_in", 0.0))
        sill = o.get("sill_in", None)
        # P5: the list shows the sill above the DORMER floor, as the editor does
        floor_in = self.roof.dormer_sill_floor_in()
        tail = (f", sill {fmt_in(float(sill) - floor_in)} over the dormer floor"
                if sill is not None else "")
        return f"{o.get('code', '????')}  ({end} {fmt_in(off)}{tail})"

    def _refill_windows(self):
        self.lst_windows.clear()
        for o in self._face_openings:
            self.lst_windows.addItem(self._window_label(o))
        # P5 §2: a double-click on a plan `DormerWindowItem` opens the dialog with
        # that window selected in the list (its elevation view's door from plan).
        sel = getattr(self, "_select_opening", None)
        if sel is not None:
            for i, o in enumerate(self._face_openings):
                if o.get("id") == sel:
                    self.lst_windows.setCurrentRow(i)
                    break

    def _window_bounds(self):
        """P5: `(dormer floor above the datum, the ridge)` -- the band the sill is
        edited within. The ridge is the value being edited now, so the window
        tracks a dormer the user is reshaping; the floor is the storey below's
        ceiling top (`dormer_sill_floor_in`)."""
        return (self.roof.dormer_sill_floor_in(), float(self.sp_ridge.value()))

    def _add_window(self):
        floor_in, ceiling_in = self._window_bounds()
        dlg = _DormerWindowDialog(None, self, sill_floor_in=floor_in, ceiling_in=ceiling_in)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._face_openings.append(dlg.opening())
            self._refill_windows()
            self.lst_windows.setCurrentRow(len(self._face_openings) - 1)

    def _edit_window(self):
        r = self.lst_windows.currentRow()
        if not (0 <= r < len(self._face_openings)):
            return
        floor_in, ceiling_in = self._window_bounds()
        dlg = _DormerWindowDialog(self._face_openings[r], self,
                                  sill_floor_in=floor_in, ceiling_in=ceiling_in)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._face_openings[r] = dlg.opening()
            self._refill_windows()
            self.lst_windows.setCurrentRow(r)

    def _remove_window(self):
        r = self.lst_windows.currentRow()
        if 0 <= r < len(self._face_openings):
            del self._face_openings[r]
            self._refill_windows()

    def accept(self):
        if self._dormer and self.dormer_meet_in() is None:
            self._refresh_dormer_note()
            return                           # stay open; nothing applied
        super().accept()

    def _derived(self) -> str:
        """The least recently edited field -- except that, while the eaves
        are bound to the room top, the eaves field is an input by
        definition and can never be the derived one."""
        for field in self._recent:
            if field == "eaves_h" and self.binding is not None:
                continue
            return field
        return self._recent[0]

    def _recompute(self):
        derived = self._derived()
        span = self.canvas.span_in
        ridge_h = self.sp_ridge.value()
        eaves_h = self.sp_eaves.value()
        pitch_rad = math.radians(self.sp_pitch.value())
        if derived == "pitch":
            pitch_rad = math.atan2(max(0.0, ridge_h - eaves_h), span)
            self._set_field("pitch", math.degrees(pitch_rad), redraw=False)
        elif derived == "ridge_h":
            ridge_h = eaves_h + span * math.tan(pitch_rad)
            self._set_field("ridge_h", ridge_h, redraw=False)
        else:                                # derived == "eaves_h"
            eaves_h = ridge_h - span * math.tan(pitch_rad)
            self._set_field("eaves_h", eaves_h, redraw=False)
        self._redraw()

    def _redraw(self):
        self.canvas.set_values(self.canvas.span_l, self.canvas.span_r,
                               self.sp_oh_l.value(), self.sp_oh_r.value(),
                               self.sp_ridge.value(), self.sp_eaves.value())
        self._refresh_level_note()

    # -- R6.c: the level's base, and the heights in the building ----------
    def level_base_in(self) -> float:
        """The elevation of the base the roof's heights are measured from. For a
        DORMER that is the HOST's level (P3, 0293 §2c): `fp3d` lifts a dormer by
        the host's base, so the dialog's absolute heights must read the host's
        datum too -- M1 (0298 §2) measured the dialog overstating a cross-level
        dormer's heights by the storey elevation. Any other roof: its own level."""
        host = getattr(self.roof, "host", None)
        floor = (host.floor if host is not None and not sip.isdeleted(host)
                 else getattr(self.roof, "floor", None))
        return float(floor_elevation(floor))

    def absolute_heights(self):
        """`(eaves, ridge)` in the building: the level's base plus the two
        heights as currently typed -- what R6.b composes with."""
        base = self.level_base_in()
        return base + self.sp_eaves.value(), base + self.sp_ridge.value()

    def _refresh_level_note(self):
        host = getattr(self.roof, "host", None)
        base = self.level_base_in()
        if self._dormer and host is not None and not sip.isdeleted(host):
            eaves, ridge = self.absolute_heights()
            drawn = getattr(self.roof, "floor", None)
            self.lab_level.setVisible(True)
            self.lab_level.setText(
                f"Drawn and edited on level '{drawn}'; pinned to the host roof on "
                f"level '{host.floor}', whose base at {fmt_in(base)} is this "
                f"dormer's datum. In the building the eaves stand at "
                f"{fmt_in(eaves)} and the ridge at {fmt_in(ridge)}.")
            return
        if abs(base) < 1e-9:
            self.lab_level.setText("")
            self.lab_level.setVisible(False)
            return
        eaves, ridge = self.absolute_heights()
        self.lab_level.setVisible(True)
        self.lab_level.setText(
            f"Level '{self.roof.floor}' has its base at {fmt_in(base)}: in the "
            f"building the eaves stand at {fmt_in(eaves)} and the ridge at "
            f"{fmt_in(ridge)}.")

    def _refresh_labels(self):
        derived = self._derived()
        labels = {"ridge_h": ("Ridge height (R)", self.lab_ridge),
                  "eaves_h": ("Eaves height (H)", self.lab_eaves),
                  "pitch": ("Pitch (P)", self.lab_pitch)}
        for field, (base, lab) in labels.items():
            if field == "eaves_h" and self.binding is not None:
                lab.setText(base + "  — bound to room top")
                continue
            lab.setText(base + ("  — derived" if field == derived else ""))

    # -- R4b: the room-top binding --------------------------------------------
    def gable_flags(self):
        """`[end 0, end 1]` as the two combos currently say, mapped back
        through the marker end the labels were named by."""
        flags = [True, True]
        flags[self._marker_end] = self.cb_end_marker.currentIndex() == 0
        flags[1 - self._marker_end] = self.cb_end_other.currentIndex() == 0
        return flags

    def _refresh_binding(self, seed=False):
        """Re-measure the covered rooms (the footprint may just have
        changed -- a hip toggle extends it) and, while bound, push the
        measured height into the locked eaves field. `seed` is the
        constructor's own call: no recompute yet, the fields are still
        being filled in."""
        from floorplanner.roofs import bound_eaves_height  # late: cycle guard
        if self.ck_bind.isChecked():
            self.binding = bound_eaves_height(self.roof.scene(), self.roof,
                                              self.gable_flags(),
                                              self.span_values())
            self.lab_bind.setText(self.binding.note())
            self.sp_eaves.setEnabled(False)
            self._set_field("eaves_h", self.binding.eaves_h_in, redraw=False)
            self.canvas.wall_top_in = self.binding.eaves_h_in
        else:
            self.binding = None
            self.lab_bind.setText("")
            self.sp_eaves.setEnabled(True)
        if not seed:
            self._recompute()
            self._refresh_labels()

    def _on_bind_toggled(self, _on):
        self._refresh_binding()

    def _on_ends(self):
        self._refresh_run_fields()
        if self.binding is not None:
            self._refresh_binding()

    # -- 0258: the hip run per end ----------------------------------------------
    def _derived_run(self) -> float:
        return (self.sp_span_l.value() + self.sp_span_r.value()) / 2.0

    def _refresh_run_fields(self):
        flags = self.gable_flags()
        for end, sp in self.sp_run.items():
            sp.setEnabled(not flags[end])

    def hip_runs(self):
        """`[end0, end1]`: the run typed for a HIP end that differs from the
        derived mean, else None (derived)."""
        out = [None, None]
        for end, sp in self.sp_run.items():
            if not sp.isEnabled():
                continue
            v = float(sp.value())
            if abs(v - self._derived_run()) > 0.05:
                out[end] = v
        return out

    # -- R4b: per-side eaves span -------------------------------------------
    def span_values(self):
        return [float(self.sp_span_l.value()), float(self.sp_span_r.value())]

    # -- 0248 plan A: the form -------------------------------------------------
    def form_value(self) -> str:
        return "shed" if self.cb_form.currentIndex() == 1 else "gable"

    def _apply_form_to_widgets(self):
        """A shed's right side is 0 and locked; a gable's right side is
        editable, and takes the left span when it was 0."""
        shed = self.form_value() == "shed"
        self._programmatic = True
        was_empty = self.sp_span_r.value() < 1.0          # read before the minimum clamps it
        self.sp_span_r.setMinimum(0.0 if shed else 1.0)   # before the value: 0 must be legal
        if shed:
            self.sp_span_r.setValue(0.0)
            self.sp_oh_r.setValue(0.0)
            self.ck_oh_same.setChecked(False)
        elif was_empty:
            self.sp_span_r.setValue(self.sp_span_l.value())
        self._programmatic = False
        for w in (self.sp_span_r, self.sp_oh_r, self.ck_oh_same):
            w.setEnabled(not shed)
        if self._dormer:
            # a shed dormer's ends are BOTH faces (0248 plan A): the marker
            # end is no more a choice than the derived one; a gable dormer's
            # marker end (its face) keeps the gable/hip choice it had
            marker = self.cb_end_marker if self._marker_end == 0 else self.cb_end_other
            if shed:
                marker.setCurrentIndex(0)
            marker.setEnabled(not shed)
            marker.setToolTip("A shed dormer's ends are both faces" if shed else "")
        self.canvas.span_l, self.canvas.span_r = self.span_values()

    def _on_form(self):
        self._apply_form_to_widgets()
        if self.binding is not None:
            self._refresh_binding()
        self._redraw()
        if self._dormer:
            self._refresh_dormer_note()      # a shed's standing rule is its own

    def _on_span(self):
        """A span edit moves the wall line on the drawing, changes the
        derived value (pitch is rise over the LEFT span), and -- while
        bound -- changes which rooms the footprint covers."""
        if self._programmatic:
            return
        self.canvas.span_l, self.canvas.span_r = self.span_values()
        if self.binding is not None:
            self._refresh_binding()          # recomputes and relabels itself
        else:
            self._recompute()
            self._refresh_labels()

    # -- R4b: per-side overhang -----------------------------------------------
    def _on_overhang(self, side, value):
        if self._programmatic:
            return
        if self.ck_oh_same.isChecked():
            other = self.sp_oh_r if side == 0 else self.sp_oh_l
            self._programmatic = True
            other.setValue(value)
            self._programmatic = False
        self._redraw()

    def _on_oh_same_toggled(self, on):
        if on:
            self._programmatic = True
            self.sp_oh_r.setValue(self.sp_oh_l.value())
            self._programmatic = False
            self._redraw()

    def apply(self):
        """Write the (always-consistent) current heights back to the roof,
        plus R4b's own fields -- per-side overhang, gable/hip per end, the
        binding. Pitch itself is never stored (0139-ruling.md sec2:
        derived, always). Under `room_top` the derived eaves height IS
        written to `eaves_h_in` (0154-ruling.md sec2: the document stays
        self-contained; nothing downstream re-derives it)."""
        self.roof.ridge_h_in = float(self.sp_ridge.value())
        self.roof.eaves_h_in = float(self.sp_eaves.value())
        self.roof.form = self.form_value()        # before the spans: the setters clamp
        self.roof.span_in = self.span_values()
        self.roof.overhang_in = [float(self.sp_oh_l.value()),
                                 float(self.sp_oh_r.value())]
        self.roof.gable = self.gable_flags()
        self.roof.hip_run_in = self.hip_runs()        # 0258: after the spans
        self.roof.eaves_bind = "room_top" if self.ck_bind.isChecked() else "manual"
        if self._dormer:
            if self.dormer_meet_in() is None:
                return False             # refused: the caller drops the dormer
            self.roof.eaves_bind = "manual"
            # Phase C (0291): the dormer's own face windows, the single record
            # the plan shadow and the 3D face both read.
            self.roof.openings = [dict(o) for o in self._face_openings]
            # 0296: which of the dormer's walls are minted on the storey above
            if self._wall_checks:
                self.roof.dormer_wall_parts = {
                    part for part, cb in self._wall_checks.items() if cb.isChecked()}
        self.roof.rebuild()                 # re-mints the walls to match
        # P3 (0293 §5 P3 ii): the "Edited on level" selector -- a promote/demote
        # applied through the win, so it syncs visibility and is an undo step.
        if self._dormer and self._level_combo is not None:
            target = self._level_combo.currentData()
            if target and target != self.roof.floor:
                v = self.roof._view()
                if v is not None:
                    v.win.move_dormer_to_level(self.roof, target)
        return True


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

        # -- 0263: the item callouts' ink and the measurements' units (the
        # Show menu switches the same two; this is where they are typed)
        from floorplanner.annotations import callout_colour
        self._callout = callout_colour()
        self.bt_colour = QPushButton()
        self.bt_colour.clicked.connect(self._pick_colour)
        self._show_colour()
        form.addRow("Item callout colour", self.bt_colour)
        self.cb_units = QComboBox()
        self.cb_units.addItem("Feet and inches", "ftin")
        self.cb_units.addItem("Inches", "in")
        self.cb_units.setCurrentIndex(1 if SETTINGS.get("dimension_units", "ftin") == "in" else 0)
        form.addRow("Measurement units", self.cb_units)

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

    def _show_colour(self):
        self.bt_colour.setText(self._callout.name())
        self.bt_colour.setStyleSheet(f"background: {self._callout.name()}; color: white;")

    def _pick_colour(self):
        c = QColorDialog.getColor(self._callout, self, "Item callout colour")
        if c.isValid():
            self._callout = c
            self._show_colour()

    def callout_colour_name(self) -> str:
        return self._callout.name()

    def apply(self):
        SETTINGS["callout_color"] = self._callout.name()          # 0263
        SETTINGS["dimension_units"] = str(self.cb_units.currentData())
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
        self.ed_dim = QLineEdit("All dimensions to wall centerlines")
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
