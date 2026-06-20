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
            f'<p style="color:#555;margin-top:0;">Version {APP_VERSION} '
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
