"""The floor roster: create / rename / switch / delete levels (P2.5).

Lifted VERBATIM out of `MainWindow` -- a mixin, not a delegating wrapper, so
every existing call site and test still resolves `win.switch_floor(...)` exactly
as before. The split is internal structure and invisible at the API.

`self.floors` + `self.active_floor` stay the authoritative roster;
`_sync_floor_state` mirrors them into config's runtime cache.
"""

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
from floorplanner.items import *  # noqa: F401
from floorplanner.model import (  # serialization bridge (aliased)
    Floor,
)
from floorplanner.dialogs import *  # noqa: F401
from floorplanner.view import *  # noqa: F401
from floorplanner.macro import *  # noqa: F401


class LevelsMixin:
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

    def _floor(self, name):
        return next((f for f in self.floors if f.name == name), None)

    def _rebuild_floor_menu(self):
        """Repopulate &Floors: cycle shortcuts, New floor, a submenu per floor
        (edit/rename/reference/delete), then the Show-other-floors toggle."""
        m = self.m_floors
        m.clear()
        if not hasattr(self, "a_next_floor"):
            # created ONCE (the menu is rebuilt often; the shortcuts must
            # not be re-registered each time). Ctrl+F / Ctrl+Shift+F cycle
            # the active floor -- the keyboard route to floor manipulation,
            # and therefore the macro-recordable one: every switch, from
            # any route, records as `^F "name"` via the switch_floor hook.
            self.a_next_floor = QAction("Next floor", self)
            self.a_next_floor.setShortcut(QKeySequence("Ctrl+F"))
            self.a_next_floor.triggered.connect(lambda: self.cycle_floor(+1))
            self.a_prev_floor = QAction("Previous floor", self)
            self.a_prev_floor.setShortcut(QKeySequence("Ctrl+Shift+F"))
            self.a_prev_floor.triggered.connect(lambda: self.cycle_floor(-1))
        m.addAction(self.a_next_floor)
        m.addAction(self.a_prev_floor)
        m.addSeparator()
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

    def cycle_floor(self, step):
        """Ctrl+F / Ctrl+Shift+F: switch to the next / previous floor in the
        roster, wrapping."""
        names = [f.name for f in self.floors]
        if len(names) < 2:
            self.status("Only one floor.")
            return
        i = names.index(self.active_floor) if self.active_floor in names else 0
        self.switch_floor(names[(i + step) % len(names)])

    def switch_floor(self, name):
        """Make `name` the active (editable) floor.  View state only — no undo
        step, no dirty (serialize() is unchanged across a switch)."""
        if self._floor(name) is None or name == self.active_floor:
            return
        self.active_floor = name
        self._sync_floor_state()
        self.status(f"Editing floor '{name}'.")
        rec = getattr(self, "_recorder", None)
        if rec is not None:              # macro recorder: any route to a
            rec.on_floor(name)           # floor switch, as one ^F token

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
