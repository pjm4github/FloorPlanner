"""The "Malformed design file" report as a window that takes you there.

Patrick, 2026-10-07: *"I need a feature that lets me zoom into an area of a
design that has been opened when I get an error ... I want to be able to
click on the error items and have the tool take me to the point on the
design and zoom in."* The report used to be a modal `QMessageBox` with the
first three violations run together in one sentence; this is a non-modal
list of every violation. Selecting one switches to its level and fits the
view to the place it names (`design.locate`), with a margin so the
surroundings show; the status line says what was found and, when a message
names something the document does not hold, what was not.

`MainWindow.zoom_to_spot` is the navigation itself, on the window so a macro
or a test can call it without the dialog.
"""
from __future__ import annotations

import re

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout,
)

from floorplanner.annotations import set_report_open   # 0265
from floorplanner.design.locate import locate

#: the least the view shows around a problem, in inches, so a single vertex
#: or a 3ft door is not fitted to the whole window
MIN_VIEW_IN = 10 * 12.0
#: breathing room around the problem's own rectangle
MARGIN_IN = 3 * 12.0


class DesignProblemsDialog(QDialog):
    def __init__(self, win, title: str, head: str, messages, doc):
        super().__init__(win)
        self.win = win
        self.doc = doc
        self.setWindowTitle(title)
        self.setModal(False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.resize(640, 360)

        lay = QVBoxLayout(self)
        lbl = QLabel(head)
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        self.list = QListWidget()
        # 0265: the rows say the SESSION LABELS (W7, O15) the screen shows,
        # translated from the document ids the validator names; the original
        # message rides as data for the zoom, which resolves document ids
        self._label_of = _session_labels_of(getattr(win, "scene", None))
        for m in messages:
            it = QListWidgetItem(_with_session_labels(m, self._label_of), self.list)
            it.setData(Qt.ItemDataRole.UserRole, m)
        self.list.setToolTip("Select a problem to go to it; double-click or "
                             "Zoom to fits the view to the place it names.")
        lay.addWidget(self.list, 1)
        self.where = QLabel("")
        self.where.setWordWrap(True)
        lay.addWidget(self.where)

        row = QHBoxLayout()
        self.b_zoom = QPushButton("Zoom to")
        self.b_zoom.setEnabled(False)
        row.addWidget(self.b_zoom)
        row.addStretch(1)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(self.close)
        row.addWidget(bb)
        lay.addLayout(row)

        self.list.currentRowChanged.connect(self._on_row)
        self.list.itemActivated.connect(lambda _it: self.zoom_to_current())
        self.b_zoom.clicked.connect(self.zoom_to_current)

    @property
    def messages(self):
        """The validator's own messages (document ids), as given."""
        return [self.list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.list.count())]

    @property
    def shown_messages(self):
        """The rows as displayed: the session labels."""
        return [self.list.item(i).text() for i in range(self.list.count())]

    def showEvent(self, e):
        # 0265: while this report is open a callout whose label differs from
        # the file's id shows both, so the zoom lands on what the screen says
        set_report_open(True)
        sc = getattr(self.win, "scene", None)
        if sc is not None:
            sc.update()
        super().showEvent(e)

    def closeEvent(self, e):
        set_report_open(False)
        sc = getattr(self.win, "scene", None)
        if sc is not None:
            sc.update()
        super().closeEvent(e)

    def _on_row(self, row: int):
        self.b_zoom.setEnabled(row >= 0)
        if row >= 0:
            self.zoom_to_current()

    def zoom_to_current(self):
        item = self.list.currentItem()
        if item is None:
            return None
        spot = locate(self.doc, item.data(Qt.ItemDataRole.UserRole) or item.text())
        if spot is None:
            self.where.setText("Nothing in this message can be placed on the design.")
            return None
        self.win.zoom_to_spot(spot)
        text = f"At {', '.join(spot.found)}"
        if spot.level:
            text += f" on level '{spot.level}'"
        if spot.missing:
            text += f"; not in the document: {', '.join(spot.missing)}"
        self.where.setText(text + ".")
        return spot


def _session_labels_of(scene) -> dict:
    """`{document id: session label}` for everything on the scene that was
    stamped with a document id (a load, or the settle's walk)."""
    out = {}
    if scene is None:
        return out
    from floorplanner.rooms import RoomItem
    from floorplanner.walls import WallItem

    def note(obj):
        did = getattr(obj, "doc_id", None)
        if not did:
            return
        uid = getattr(obj, "uid", None)
        if not uid:
            return
        for d in (did if isinstance(did, list) else [did]):
            out.setdefault(d, uid)
    for it in scene.items():
        note(it)
        if isinstance(it, WallItem):
            for op in it.openings:
                note(op)
            for a in ("p1", "p2"):
                v = it.end_vertex(a)
                if v is not None:
                    note(v)
        elif isinstance(it, RoomItem):
            for e in it.outline:
                if e.v is not None:
                    note(e.v)
    return out


def _with_session_labels(message: str, label_of: dict) -> str:
    """The message with each document id it names replaced by the session
    label of the thing it is (0265); an id with no label stays as it is."""
    from floorplanner.design.locate import subjects
    out = message
    for s in subjects(message):
        lab = label_of.get(s)
        if lab and lab != s:
            out = re.sub(rf"\b{re.escape(s)}\b", lab, out)
    return out


def zoom_to_spot(win, spot) -> QRectF:
    """`MainWindow.zoom_to_spot`: switch to the spot's level when the plan
    has it, then fit the view to its rectangle, grown to at least
    `MIN_VIEW_IN` square and by `MARGIN_IN` all round. Returns the scene
    rectangle fitted."""
    if spot.level and win._floor(spot.level) is not None \
            and spot.level != win.active_floor:
        win.switch_floor(spot.level)
    x0, y0, x1, y1 = spot.rect
    w, h = max(x1 - x0, MIN_VIEW_IN), max(y1 - y0, MIN_VIEW_IN)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    rect = QRectF(cx - w / 2.0, cy - h / 2.0, w, h).adjusted(
        -MARGIN_IN, -MARGIN_IN, MARGIN_IN, MARGIN_IN)
    win.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
    win.view.centerOn(cx, cy)
    return rect
