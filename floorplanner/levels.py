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
    # z-band between floors (P4.2): the ACTIVE floor's band is 0, so every
    # newly created item (walls z=5, rooms 4, ...) lands in it with nothing
    # to re-apply; ghosted floors sit on NEGATIVE bands in the user's display
    # order. Wide enough that within-floor z machinery (raise_to_front's
    # running max) can never bleed across bands. VIEW STATE, like
    # active_floor: not serialized, not undoable. (Defect 11's P4.5 z-order
    # collapse should fold this band in as the one BETWEEN-floor term.)
    FLOOR_Z_BAND = 100_000.0

    def _sync_floor_state(self):
        """Mirror the authoritative roster (self.floors / active_floor /
        show_other_floors) into config's runtime cache, then re-apply
        visibility, floor stacking and repaint.  Cheap; called on init,
        load, and floor ops."""
        set_floor_state(
            active=self.active_floor,
            reference={f.name for f in self.floors if f.reference},
            show_others=self.show_other_floors,
        )
        apply_floor_visibility(self.scene)
        self._apply_floor_stacking()
        self.scene.update()
        if hasattr(self, "floor_label"):
            self.floor_label.setText(f"Floor: {self.active_floor}")
        if hasattr(self, "m_floors"):
            self._rebuild_floor_menu()

    def _floor(self, name):
        return next((f for f in self.floors if f.name == name), None)

    def _repair_floor_stack(self):
        """The display stack (bottom → top), kept in step with the roster:
        deleted floors drop out, new floors join at the TOP of the ghost
        pile."""
        names = [f.name for f in self.floors]
        stack = [n for n in getattr(self, "floor_stack", []) if n in names]
        stack += [n for n in names if n not in stack]
        self.floor_stack = stack
        return stack

    def _display_order(self):
        """Bottom → top for PAINTING: the user's stack with the ACTIVE floor
        forced topmost — you are editing it, and a grayed ghost must never
        occlude it. The stack order governs the ghosts beneath."""
        stack = [n for n in self._repair_floor_stack()
                 if n != self.active_floor]
        return stack + [self.active_floor]

    def _apply_floor_stacking(self):
        """Band every top-level item's z by its floor's display position
        (active = band 0, ghosts negative), preserving within-floor z by
        applying the band as a DELTA — raise_to_front etc. are untouched.

        ATMOSPHERIC DEPTH (P4.2, Patrick's refinement): each floor also
        gets an opacity from its depth in the display order — the active
        floor full-contrast, each ghost beneath it grayer as it drops back
        (the flat ghost paint fading toward the background reads as
        distance). Item opacity is view state, applied here alongside the
        band, restored to 1.0 the moment a floor becomes active."""
        order = self._display_order()
        n = len(order)
        band_of, fade_of = {}, {}
        for i, name in enumerate(order):
            depth = n - 1 - i                 # 0 = active (topmost)
            band_of[name] = -depth * self.FLOOR_Z_BAND
            fade_of[name] = (1.0 if depth == 0
                             else max(0.18, 0.60 * (0.65 ** (depth - 1))))
        for it in self.scene.items():
            if it.parentItem() is not None:
                continue
            floor = getattr(it, "floor", None)
            if floor is None or floor not in band_of:
                continue
            new = band_of[floor]
            old = getattr(it, "_floor_band", 0.0)
            if new != old:
                it.setZValue(it.zValue() - old + new)
                it._floor_band = new
            if it.opacity() != fade_of[floor]:
                it.setOpacity(fade_of[floor])

    def floor_display_front(self, name):
        """Floors ▸ <floor> ▸ Move to front (display): topmost of the
        GHOSTS — the active floor always paints above."""
        stack = self._repair_floor_stack()
        if name in stack:
            stack.remove(name)
            stack.append(name)
            self._sync_floor_state()

    def floor_display_back(self, name):
        """Floors ▸ <floor> ▸ Move to back (display)."""
        stack = self._repair_floor_stack()
        if name in stack:
            stack.remove(name)
            stack.insert(0, name)
            self._sync_floor_state()

    def default_floor_name(self) -> str:
        """The DEFAULT floor is the roster's FIRST — whatever it has been
        renamed to. Bare `^F` (and ENTER straight into the floor popup)
        targets it by position, not by the word 'default'."""
        return self.floors[0].name if self.floors else self.active_floor

    def _rebuild_floor_menu(self):
        """Repopulate &Floors per the P4.2 spec: Select… (^F), New… (^+F),
        separator, the floors (default first, marked), separator, the
        Show-other-floors toggle."""
        m = self.m_floors
        m.clear()
        if not hasattr(self, "a_select_floor"):
            # created ONCE (the menu is rebuilt often; the shortcuts must
            # not be re-registered each time). Ctrl+F pops the floor
            # selector; Ctrl+Shift+F is New floor. Every switch, from any
            # route, records as `^F "name"` via the switch_floor hook.
            self.a_select_floor = QAction("&Select…", self)
            self.a_select_floor.setShortcut(QKeySequence("Ctrl+F"))
            self.a_select_floor.triggered.connect(
                lambda: self.select_floor_popup())
            self.a_new_floor = QAction("&New…", self)
            self.a_new_floor.setShortcut(QKeySequence("Ctrl+Shift+F"))
            self.a_new_floor.triggered.connect(self.new_floor)
            # quick flip (Patrick's refinement): cycle without the popup.
            # Recording stays deterministic for free -- the switch_floor
            # hook emits the RESULTING `^F "name"` token, never the cycle.
            self.a_floor_up = QAction("Next floor", self)
            self.a_floor_up.setShortcut(QKeySequence("Ctrl+PgDown"))
            self.a_floor_up.triggered.connect(lambda: self.cycle_floor(+1))
            self.a_floor_down = QAction("Previous floor", self)
            self.a_floor_down.setShortcut(QKeySequence("Ctrl+PgUp"))
            self.a_floor_down.triggered.connect(lambda: self.cycle_floor(-1))
        m.addAction(self.a_select_floor)
        m.addAction(self.a_new_floor)
        m.addAction(self.a_floor_up)
        m.addAction(self.a_floor_down)
        m.addSeparator()
        grp = QActionGroup(self)
        grp.setExclusive(True)
        default = self.default_floor_name()
        for f in self.floors:
            tag = f"{f.name}{'  (Default)' if f.name == default else ''}" \
                  f"{'  (R)' if f.reference else ''}" \
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
            sub.addSeparator()
            # display stacking (P4.2): the active floor always paints on
            # top; these arrange the GHOSTS beneath it
            a_fr = sub.addAction("Move to front (display)")
            a_fr.triggered.connect(
                lambda _=False, n=f.name: self.floor_display_front(n))
            a_bk = sub.addAction("Move to back (display)")
            a_bk.triggered.connect(
                lambda _=False, n=f.name: self.floor_display_back(n))
        m.addSeparator()
        a_show = m.addAction("Show other floors (ghosted)")
        a_show.setCheckable(True)
        a_show.setChecked(self.show_other_floors)
        a_show.triggered.connect(self.toggle_show_others)

    def _build_floor_popup(self) -> QMenu:
        """The ONE floor-selection surface (P4.2 spec): default floor first
        and PRE-HIGHLIGHTED, so ENTER with no arrows selects the default,
        DOWN walks the other floors, ESC cancels. Built separately from
        showing so tests can assert its shape headless."""
        menu = QMenu(self)
        default = self.default_floor_name()
        for f in self.floors:
            tag = f"{f.name}{'  (Default)' if f.name == default else ''}" \
                  f"{'  ●' if f.name == self.active_floor else ''}"
            a = menu.addAction(tag)
            a.triggered.connect(lambda _=False, n=f.name: self.switch_floor(n))
        if menu.actions():
            menu.setActiveAction(menu.actions()[0])
        return menu

    def select_floor_popup(self, global_pos=None):
        """Select… (^F) and the blank-canvas right-click both land here."""
        menu = self._build_floor_popup()
        if global_pos is None:
            global_pos = self.view.mapToGlobal(
                self.view.viewport().rect().center())
        menu.exec(global_pos)

    def _popup_floor_menu(self):
        """Quick floor switch from the status-bar label."""
        self.select_floor_popup(
            self.floor_label.mapToGlobal(self.floor_label.rect().topLeft()))

    def cycle_floor(self, step):
        """Ctrl+PgDown / Ctrl+PgUp: flip to the next / previous floor in
        roster order, wrapping — the fast path between floors; ^F pops the
        selector when you want to aim."""
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
        rec = getattr(self, "_recorder", None)
        if rec is not None:              # macro recorder: New floor with its
            rec.on_new_floor(name)       # typed name, as one ^+F token

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
        self.floor_stack = [new if n == name else n
                            for n in getattr(self, "floor_stack", [])]
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
