"""0316: Find item -- locate an annotated item by its session label (W47, O3,
R2, V12, F4, RF1, C2) or its name, and zoom the view to it.

The number a user sees is the item's SESSION LABEL (`labels.py`), now persisted
across save/open (0316) so a find lands on the same item next session. The
dialog walks the open document for every labelled item, filters the list by
what the user types -- the LABEL or the optional NAME (Patrick's choice, not the
item type) -- and on a pick switches to the item's floor, selects it and fits
the view around it, reusing `MainWindow.zoom_to_spot` and the design `Spot`.

Edit ▸ Find item… (Ctrl+F). Non-modal, like the problems dialog, so the plan
stays visible while a selection zooms it.
"""
from __future__ import annotations

import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QVBoxLayout)

from floorplanner.design.locate import Spot

_LABEL_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


def _rect(item):
    r = item.sceneBoundingRect()
    return (r.left(), r.top(), r.right(), r.bottom())


def find_targets(scene):
    """Every labelled thing on `scene` as a list of rows
    `(label, kind, name, floor, rect, item)` -- `item` is the QGraphicsItem to
    select, or None for a corner (a `Vertex` is not a scene item). Sorted by
    label kind then number, so the list reads W1, W2, …, O1, …, deterministically."""
    from floorplanner.cameras import CameraItem
    from floorplanner.items import FurnishingItem
    from floorplanner.rooms import RoomItem
    from floorplanner.roofs import RoofItem
    from floorplanner.walls import OpeningItem, WallItem

    rows, seen_v = [], set()

    def floor_of(it):
        return (getattr(it, "floor", None)
                or getattr(getattr(it, "wall", None), "floor", None))

    def add_vertex(v, floor):
        if v is None or id(v) in seen_v or not getattr(v, "uid", None):
            return
        seen_v.add(id(v))
        rad = 6.0                               # a corner is a point; a small box
        rows.append((v.uid, "corner", getattr(v, "name", "") or "", floor,
                     (v.x - rad, v.y - rad, v.x + rad, v.y + rad), None))

    kinds = ((WallItem, "wall"), (OpeningItem, "opening"), (RoomItem, "room"),
             (FurnishingItem, "furnishing"), (RoofItem, "roof"),
             (CameraItem, "camera"))
    for it in scene.items():
        for cls, kind in kinds:
            if isinstance(it, cls):
                uid = getattr(it, "uid", None)
                if uid:
                    # NAME is a USER name only (Patrick's choice: not the item
                    # type). A room's name is a user name; a wall/corner's is the
                    # optional properties-dialog name; others have none.
                    name = getattr(it, "name", "") or ""
                    rows.append((uid, kind, name, floor_of(it), _rect(it), it))
                break
        if isinstance(it, WallItem):
            for a in ("p1", "p2"):
                add_vertex(it.end_vertex(a), it.floor)
        elif isinstance(it, RoomItem):
            for e in it.outline:
                add_vertex(e.v, it.floor)

    def key(row):
        m = _LABEL_RE.match(row[0] or "")
        return (m.group(1), int(m.group(2))) if m else (row[0] or "", 0)

    rows.sort(key=key)
    return rows


class FindDialog(QDialog):
    """A filter box over a list of every labelled item; a pick zooms + selects."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Find item")
        self.setModal(False)
        lay = QVBoxLayout(self)
        self.box = QLineEdit(self)
        self.box.setPlaceholderText("Type a label (W47, O3, R2…) or a name")
        self.box.setClearButtonEnabled(True)
        self.box.textChanged.connect(self._filter)
        self.box.returnPressed.connect(self._enter)
        lay.addWidget(self.box)
        self.list = QListWidget(self)
        self.list.currentItemChanged.connect(lambda cur, _prev: self._go(cur))
        self.list.itemActivated.connect(self._go)
        lay.addWidget(self.list)
        self.note = QLabel("", self)
        lay.addWidget(self.note)
        self.resize(340, 440)

        self._rows = find_targets(win.scene)
        self._filter("")
        self.box.setFocus()

    # -- the row's display text (shows the type; MATCH is label+name only) -----
    @staticmethod
    def _text(row):
        label, kind, name, floor = row[0], row[1], row[2], row[3]
        txt = f"{label}   {kind}"
        if name:
            txt += f"  ·  {name}"
        if floor:
            txt += f"   [{floor}]"
        return txt

    def _filter(self, text):
        q = (text or "").strip().lower()
        self.list.blockSignals(True)            # rebuilding is not a user pick
        self.list.clear()
        shown = 0
        for row in self._rows:
            hay = f"{row[0]} {row[2]}".lower()   # label + name, per the decision
            if q and q not in hay:
                continue
            item = QListWidgetItem(self._text(row))
            item.setData(Qt.ItemDataRole.UserRole, row)
            self.list.addItem(item)
            shown += 1
        self.list.blockSignals(False)
        self.note.setText(f"{shown} of {len(self._rows)} item(s)"
                          + ("" if shown else " — nothing matches"))

    def _enter(self):
        if self.list.count():
            self.list.setCurrentRow(0)          # fires currentItemChanged -> _go

    def _go(self, item):
        if item is None:
            return
        row = item.data(Qt.ItemDataRole.UserRole)
        if not row:
            return
        label, _kind, _name, floor, rect, obj = row
        self.win.zoom_to_spot(Spot(floor, rect, (label,), ()))
        sc = self.win.scene
        sc.clearSelection()
        if obj is not None:
            obj.setSelected(True)
        sc.update()
