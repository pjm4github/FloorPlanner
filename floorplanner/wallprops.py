"""The wall-properties dialog (Patrick, 2026-10-10):

> *"a dialog box when I double click on a wall. The dialog box should show
> all the properties of the wall. The wall end points should be editable.
> The wall name and x/y (in inches/ or feet and inches) should be editable
> on a Vertex by vertex basis. There should be a checkbox that is on by
> default that ... all other walls (and room definitions) that touch that
> vertex are updated when the dialog box is OKed (accepted). If the user
> cancels the dialog box then it will revert to the settings that the wall
> had before the edit box opens. I will eventually want to show the wall in
> profile including the windows when the box is open. You dont need to
> build a profile view at the moment, but make room for that."*

NOTHING IS APPLIED UNTIL OK. The dialog reads the wall once, edits its own
fields, and `apply()` writes them back; Cancel discards the fields, so the
wall is exactly as it was -- "revert" by never having changed. One undo
step follows the apply (`WallItem.open_properties`).

THE CHECKBOX IS THE DIFFERENCE BETWEEN THE TWO VERTEX OPERATIONS
(`vertex.py`): on, a moved end RELOCATES its corner, and every wall end and
room outline holding that corner moves with it (`rooms.relocate_corners`,
the same path Align to grid and a corner drag use); off, the end DETACHES
onto a new corner and every sharer stays where it was.

LENGTHS: a plain number is inches (the macro language's own rule, `_num`);
anything with a foot or inch mark is feet-and-inches (`parse_feet`:
`10'`, `10'6"`, `126"`). Each field shows the inch value and, beside it,
the same length written feet-and-inches, live.

THE PROFILE: `WallProfileView` is the room he asked for -- a widget that
knows the wall and its openings and paints a placeholder today. It gets
the wall's length and the openings' spans, so the elevation drawing can
be filled in without the dialog's layout changing.
"""
from __future__ import annotations

import re

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWidget,
)

from floorplanner.geometry import fmt_ftin, fmt_in, heading_deg, parse_feet
from floorplanner.walls import (
    MIN_WALL_LEN, STD_T, WALL_TYPE_LABELS, WallItem, rebuild_all_walls,
)

_FTIN = re.compile(r"""['"’”]""")


def parse_length(text: str) -> float:
    """Inches from a field: a plain number is inches, a foot or inch mark
    means feet-and-inches. Raises ValueError on anything else."""
    s = str(text).strip()
    if not s:
        raise ValueError("empty")
    if _FTIN.search(s):
        return parse_feet(s)
    return float(s)


def length_text(inches: float) -> str:
    """The inch value as a field shows it: up to 2 decimals, no trailing zeros."""
    s = f"{float(inches):.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


class WallProfileView(QWidget):
    """THE PLACEHOLDER FOR THE PROFILE (elevation) VIEW. Holds the wall and
    paints its length as a bar with each opening's span marked, so the real
    drawing has its data and its place; the words say it is not built."""

    def __init__(self, wall: WallItem, parent=None):
        super().__init__(parent)
        self.wall = wall
        self.setMinimumHeight(110)

    def spans(self):
        """(kind, start, end) along the wall from p1, for each opening."""
        return [(o.kind, float(o.s) - float(o.width) / 2.0, float(o.s) + float(o.width) / 2.0)
                for o in getattr(self.wall, "openings", ())]

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(8, 8, -8, -8)
        p.setPen(QPen(QColor(160, 160, 160), 1, Qt.PenStyle.DashLine))
        p.drawRect(r)
        length = max(self.wall.length(), 1e-6)
        bar = QRectF(r.left() + 10, r.center().y() - 10, r.width() - 20, 20)
        p.setPen(QPen(QColor(90, 90, 90), 1))
        p.setBrush(QColor(225, 225, 225))
        p.drawRect(bar)
        for kind, s0, s1 in self.spans():
            x0 = bar.left() + bar.width() * max(0.0, s0) / length
            x1 = bar.left() + bar.width() * min(length, s1) / length
            p.setBrush(QColor(140, 180, 230) if kind == "window" else QColor(200, 170, 120))
            p.drawRect(QRectF(x0, bar.top() + 3, max(1.0, x1 - x0), bar.height() - 6))
        p.setPen(QColor(120, 120, 120))
        p.drawText(r.adjusted(4, 2, -4, -2), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                   "Profile view -- not built yet (the openings' spans are marked)")
        p.end()


class _EndRow:
    """One endpoint's editors: name, x, y, and the feet-and-inches echo."""

    def __init__(self, attr: str, vertex, grid: QGridLayout, row: int):
        self.attr = attr
        self.vertex = vertex
        self.orig = QPointF(vertex.point())
        self.ed_name = QLineEdit(vertex.name or "")
        self.ed_name.setPlaceholderText(vertex.uid)        # 0265: the session label
        self.ed_x = QLineEdit(length_text(vertex.x))
        self.ed_y = QLineEdit(length_text(vertex.y))
        self.echo = QLabel("")
        grid.addWidget(QLabel("p1" if attr == "p1" else "p2"), row, 0)
        grid.addWidget(self.ed_name, row, 1)
        grid.addWidget(self.ed_x, row, 2)
        grid.addWidget(self.ed_y, row, 3)
        grid.addWidget(self.echo, row, 4)
        self.ed_x.textChanged.connect(self._echo)
        self.ed_y.textChanged.connect(self._echo)
        self._echo()

    def _echo(self, *_):
        try:
            x, y = parse_length(self.ed_x.text()), parse_length(self.ed_y.text())
        except ValueError:
            self.echo.setText("?")
            return
        self.echo.setText(f"({fmt_ftin(x)}, {fmt_ftin(y)})")

    def point(self) -> QPointF:
        """The edited point, in inches. Raises ValueError with the field named."""
        try:
            x = parse_length(self.ed_x.text())
        except ValueError:
            raise ValueError(f"{self.attr} x: {self.ed_x.text()!r} is not a length") from None
        try:
            y = parse_length(self.ed_y.text())
        except ValueError:
            raise ValueError(f"{self.attr} y: {self.ed_y.text()!r} is not a length") from None
        return QPointF(x, y)

    def name(self) -> str:
        return self.ed_name.text().strip()


class WallPropertiesDialog(QDialog):
    def __init__(self, wall: WallItem, parent=None):
        super().__init__(parent)
        self.wall = wall
        self.setWindowTitle(f"Wall properties — {wall.name or wall.uid}")
        lay = QVBoxLayout(self)

        form = QFormLayout()
        self.ed_name = QLineEdit(wall.name)
        self.ed_name.setPlaceholderText(wall.uid)
        form.addRow("Name", self.ed_name)
        self.cb_type = QComboBox()
        for key, label in WALL_TYPE_LABELS:
            self.cb_type.addItem(f"{label} ({fmt_in(STD_T[key])})", key)
        idx = self.cb_type.findData(wall.wall_type)
        self.cb_type.setCurrentIndex(max(0, idx))
        form.addRow("Type", self.cb_type)
        form.addRow("Thickness", QLabel(fmt_in(wall.t)))
        form.addRow("Length", QLabel(f"{fmt_ftin(wall.length())}  ({length_text(wall.length())} in)"))
        hd = heading_deg(wall.p1, wall.p2)
        form.addRow("Heading", QLabel("—" if hd is None else f"{hd:.2f}°"))
        form.addRow("Level", QLabel(str(wall.floor)))
        rooms = ", ".join(r.name for r in wall.rooms) or "— (free)"
        form.addRow("Rooms", QLabel(rooms))
        ops = [f"{o.kind} {o.code} at {fmt_ftin(float(o.s))}" for o in wall.openings]
        form.addRow("Openings", QLabel("; ".join(ops) if ops else "none"))
        extra = {k: v for k, v in (getattr(wall, "_v5_extra", None) or {}).items()
                 if k != "name"}
        if extra:
            form.addRow("Document fields", QLabel(", ".join(f"{k}={v}" for k, v in sorted(extra.items()))))
        # 0265: the session label (what the plan's callouts say and the report
        # is translated into); the file's id beside it only when they differ
        from floorplanner import labels as _labels
        from floorplanner.annotations import document_id
        did = document_id(wall)
        shown = wall.uid if (not did or _labels.matches(wall.uid, did)) else f"{wall.uid}  (file: {did})"
        form.addRow("Id", QLabel(shown))
        lay.addLayout(form)

        ends = QGroupBox("End points — a plain number is inches; 10'6\" is feet-and-inches")
        grid = QGridLayout(ends)
        for c, h in enumerate(("", "Name", "X", "Y", "")):
            grid.addWidget(QLabel(h), 0, c)
        self.ends = [_EndRow("p1", wall.end_vertex("p1"), grid, 1),
                     _EndRow("p2", wall.end_vertex("p2"), grid, 2)]
        lay.addWidget(ends)

        self.ck_joined = QCheckBox("Move everything joined at these corners "
                                   "(other walls and room outlines) with them")
        self.ck_joined.setChecked(True)
        lay.addWidget(self.ck_joined)

        prof = QGroupBox("Profile")
        pl = QHBoxLayout(prof)
        self.profile = WallProfileView(wall)
        pl.addWidget(self.profile)
        lay.addWidget(prof)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._ok)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    # -- validation before OK -------------------------------------------------
    def edited_points(self):
        """(p1, p2) as edited. Raises ValueError naming the bad field or a
        wall that would vanish."""
        p1, p2 = (row.point() for row in self.ends)
        if (p2 - p1).manhattanLength() < 1e-9 or \
                ((p2.x() - p1.x()) ** 2 + (p2.y() - p1.y()) ** 2) ** 0.5 < MIN_WALL_LEN:
            raise ValueError(f"the wall would be shorter than {fmt_in(MIN_WALL_LEN)}")
        return p1, p2

    def _ok(self):
        try:
            self.edited_points()
        except ValueError as ex:
            QMessageBox.warning(self, "Wall properties", str(ex))
            return
        self.accept()

    # -- apply, on OK only ----------------------------------------------------
    def apply(self):
        """Write the fields to the wall. Returns the number of corners moved."""
        from floorplanner.rooms import relocate_corners     # late: rooms <-> walls
        wall = self.wall
        wall.name = self.ed_name.text()
        wall.wall_type = self.cb_type.currentData()
        for row in self.ends:
            row.vertex.name = row.name() or None
        p1, p2 = self.edited_points()
        want = {"p1": p1, "p2": p2}
        moved = 0
        sc = wall.scene()
        if self.ck_joined.isChecked():
            targets = {}
            for row in self.ends:
                p = want[row.attr]
                if p != row.orig:
                    targets[id(wall.end_vertex(row.attr))] = p
            if targets:
                moved = relocate_corners([wall], [], lambda v: targets.get(id(v)), sc)
        else:
            for row in self.ends:
                p = want[row.attr]
                if p != row.orig:
                    name = wall.end_vertex(row.attr).name
                    wall.detach_end(row.attr, p)
                    wall.end_vertex(row.attr).name = name    # the name goes with the end
                    moved += 1
        if sc is not None:
            rebuild_all_walls(sc)
        else:
            wall.rebuild()
        return moved
