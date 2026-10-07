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

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout,
)

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
        for m in messages:
            QListWidgetItem(m, self.list)
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
        return [self.list.item(i).text() for i in range(self.list.count())]

    def _on_row(self, row: int):
        self.b_zoom.setEnabled(row >= 0)
        if row >= 0:
            self.zoom_to_current()

    def zoom_to_current(self):
        item = self.list.currentItem()
        if item is None:
            return None
        spot = locate(self.doc, item.text())
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
