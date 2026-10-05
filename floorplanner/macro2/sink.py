"""Macro language v2: abstract input events -> Qt (MACRO_SPEC.md sec8.1).

`QtEventSink` turns one `InputEvent` into real `QMouseEvent` / `QKeyEvent` /
`QWheelEvent` objects and delivers them with `QApplication.sendEvent`:
mouse and wheel events to the canvas VIEWPORT, key events to whatever holds
the keyboard. Coordinates are SCENE coordinates (the canvas is a
`QGraphicsView`), mapped with `view.mapFromScene`, so a macro survives zoom
and pan (sec5.1).

MODIFIERS -- the one place a project rule is deliberately crossed
(Patrick's ruling, docs/handoff/0212-report.md sec3: "follow the spec, guard
the leak"). `CLAUDE.md` forbids synthesizing Ctrl-modified key events
because they leave `QApplication.keyboardModifiers()` set. MEASURED for
this sink (0214-report.md sec2), with `sendEvent` to any widget:

  * a KeyPress of an ORDINARY key sets the global state to that event's
    modifiers -- and nothing afterwards clears it: not its KeyRelease, not
    the modifier's own KeyRelease, not a mouse event. That is the leak.
  * a KeyPress of a MODIFIER key itself, a KeyRelease, and a mouse event
    with modifier flags do not change the global state at all.
  * a later KeyPress carrying other modifiers replaces it.

So `_sync_global` is the guard: after every key event it compares the
global state with the modifiers this macro actually holds and, when they
differ, sends one KeyPress of `Key_unknown` carrying the right set to a
PRIVATE, never-shown widget -- no application widget sees it. The global
state therefore FOLLOWS the macro (a widget that reads
`keyboardModifiers()` during a `+DRAG` sees Shift, which sec7 asks for)
and is back to none when the macro ends or aborts. A test pins that after
every macro. Never use `QTest`'s key functions here.

SHORTCUTS. A key press delivered with `sendEvent` skips Qt's shortcut map,
so `KEY ^z` would reach the canvas and undo nothing. `_key_down` does what
Qt does for a real key press, in Qt's order: offer the widget a
`ShortcutOverride`; if it declines, look for an enabled `QAction` of the
window with that shortcut and trigger it; only otherwise deliver the
`KeyPress`. While a menu or a modal dialog is open the window's shortcuts
are not live, as in the real application.
"""
from __future__ import annotations

from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import (
    QAction, QContextMenuEvent, QKeyEvent, QKeySequence, QMouseEvent, QWheelEvent,
)
from PyQt6.QtWidgets import QApplication, QLineEdit, QWidget

from floorplanner.macro2 import keys
from floorplanner.macro2.ast import Mod

_MOD = {Mod.SHIFT: Qt.KeyboardModifier.ShiftModifier,
        Mod.CTRL: Qt.KeyboardModifier.ControlModifier,
        Mod.ALT: Qt.KeyboardModifier.AltModifier,
        Mod.META: Qt.KeyboardModifier.MetaModifier}
_BUTTON = {"left": Qt.MouseButton.LeftButton,
           "right": Qt.MouseButton.RightButton,
           "middle": Qt.MouseButton.MiddleButton,
           "back": Qt.MouseButton.BackButton,
           "forward": Qt.MouseButton.ForwardButton}
_TEXT = {"Enter": "\r", "Tab": "\t", "Space": " "}


def qt_mods(mods):
    out = Qt.KeyboardModifier.NoModifier
    for m in mods:
        out |= _MOD[m]
    return out


def qt_key(ident: str):
    """The `Qt.Key` for an expansion key identity: a canonical key name, or
    an upper-cased character (sec6.2: in the Latin-1 range Qt key codes are
    the code points)."""
    name = keys.qt_name(ident)
    if name is not None:
        return getattr(Qt.Key, name)
    if len(ident) == 1 and ord(ident) < 256:
        return Qt.Key(ord(ident))
    return Qt.Key.Key_unknown


class QtEventSink:
    def __init__(self, win, tools, step_px: float = 8.0, run_command=None):
        self.win = win
        self.run_command = run_command     # (name, args) -> None; sec14
        self.view = win.view
        self.tools = tools                 # letter -> the app's tool constant
        self.step_px = max(1.0, float(step_px))
        self.pos = None                    # pointer, viewport pixels
        self.buttons = Qt.MouseButton.NoButton
        self._swallowed = set()            # key idents a shortcut consumed
        self._null = QWidget()             # the guard's private target; never shown

    # -- geometry ----------------------------------------------------------
    def _vp(self):
        return self.view.viewport()

    def _to_view(self, x, y) -> QPoint:
        if x is None or y is None:         # "starts at the canvas centre"
            return self.pos if self.pos is not None else self._vp().rect().center()
        return self.view.mapFromScene(QPointF(float(x), float(y)))

    def _mouse(self, etype, pos: QPoint, button, buttons, mods):
        vp = self._vp()
        QApplication.sendEvent(vp, QMouseEvent(
            etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)), button, buttons,
            qt_mods(mods)))

    # -- keyboard ----------------------------------------------------------
    def _key_target(self):
        """sec6: keys go to the focus widget, else the canvas. A popup menu
        takes its own keys, and a modal dialog's go to its text field --
        focus may not be set the instant the dialog opens (the lesson
        `MacroRunner._modal_step` already carries)."""
        popup = QApplication.activePopupWidget()
        if popup is not None:
            return popup, True
        modal = QApplication.activeModalWidget()
        if modal is not None:
            return (modal.focusWidget() or modal.findChild(QLineEdit) or modal), True
        return (QApplication.focusWidget() or self.view), False

    def _shortcut_action(self, key, mods):
        seq = QKeySequence(int(qt_mods(mods).value) | int(key.value))
        for act in self.win.findChildren(QAction):
            if act.isEnabled() and any(
                    s.matches(seq) == QKeySequence.SequenceMatch.ExactMatch
                    for s in act.shortcuts()):
                return act
        return None

    def _sync_global(self, mods):
        """The guard (module docstring): make `QApplication.keyboardModifiers()`
        equal the modifiers this macro holds."""
        want = qt_mods(mods)
        if QApplication.keyboardModifiers() != want:
            QApplication.sendEvent(self._null, QKeyEvent(
                QEvent.Type.KeyPress, Qt.Key.Key_unknown, want, ""))

    def reset(self):
        """No modifier is down as far as Qt is concerned -- the end of every
        macro, however it ended."""
        self._sync_global(frozenset())

    def _key_down(self, ev):
        key = qt_key(ev.key)
        mods = qt_mods(ev.mods)
        target, captured = self._key_target()
        is_mod = ev.key in keys.MODIFIER_KEYS
        text = ev.text or ("" if is_mod else self._text_of(ev))
        if not is_mod and not captured:
            # what the app's 180 ms settle timer would have done by the time
            # a person pressed a key: commit the gesture just made, so that
            # Undo is live. Without it `KEY ^z` straight after a drag found
            # the action disabled and did nothing (measured).
            settle = getattr(self.win, "_commit_if_changed", None)
            if settle is not None:
                settle()
            over = QKeyEvent(QEvent.Type.ShortcutOverride, key, mods, text)
            over.ignore()
            QApplication.sendEvent(target, over)
            if not over.isAccepted():
                act = self._shortcut_action(key, ev.mods)
                if act is not None:
                    self._swallowed.add(ev.key)
                    act.trigger()
                    return
        QApplication.sendEvent(target, QKeyEvent(QEvent.Type.KeyPress, key, mods, text))

    def _text_of(self, ev):
        """What a real press of this key would carry as text(): nothing
        under Ctrl/Alt/Meta, else the character (upper-cased under Shift)."""
        if ev.mods & {Mod.CTRL, Mod.ALT, Mod.META}:
            return ""
        if ev.key in _TEXT:
            return _TEXT[ev.key]
        if keys.qt_name(ev.key) is None and len(ev.key) == 1:
            return ev.key if Mod.SHIFT in ev.mods else ev.key.lower()
        return ""

    def _key_up(self, ev):
        if ev.key in self._swallowed:      # its press became a shortcut
            self._swallowed.discard(ev.key)
            return
        target, _ = self._key_target()
        QApplication.sendEvent(target, QKeyEvent(
            QEvent.Type.KeyRelease, qt_key(ev.key), qt_mods(ev.mods), ""))

    # -- one event ---------------------------------------------------------
    def deliver(self, ev):
        k = ev.kind
        if k == "tool":
            # the handler the toolbar's QAction calls -- no key press (sec4)
            self.win.set_tool(self.tools[ev.tool])
        elif k == "key_down":
            self._key_down(ev)
            self._sync_global(ev.mods)
        elif k == "key_up":
            self._key_up(ev)
            self._sync_global(ev.mods)
        elif k == "hover":
            self.pos = self._to_view(ev.x, ev.y)
            self._mouse(QEvent.Type.MouseMove, self.pos, Qt.MouseButton.NoButton,
                        self.buttons, ev.mods)
        elif k == "press":
            button = _BUTTON[ev.button]
            self.pos = self._to_view(ev.x, ev.y)
            self.buttons |= button
            self._mouse(QEvent.Type.MouseButtonPress, self.pos, button,
                        self.buttons, ev.mods)
        elif k == "dblclick":
            button = _BUTTON[ev.button]
            self.buttons |= button
            self._mouse(QEvent.Type.MouseButtonDblClick, self.pos, button,
                        self.buttons, ev.mods)
        elif k == "release":
            button = _BUTTON[ev.button]
            self.pos = self._to_view(ev.x, ev.y)
            self.buttons &= ~button
            self._mouse(QEvent.Type.MouseButtonRelease, self.pos, button,
                        self.buttons, ev.mods)
            if ev.button == "right":
                # the platform follows a real right click with a context-menu
                # event; without it no context menu ever opens
                vp = self._vp()
                QApplication.sendEvent(vp, QContextMenuEvent(
                    QContextMenuEvent.Reason.Mouse, self.pos,
                    vp.mapToGlobal(self.pos), qt_mods(ev.mods)))
        elif k == "move":
            for p in self.drag_points(ev):
                self.move_px(p, ev.mods)
        elif k == "px":
            self.move_px(QPoint(int(ev.x), int(ev.y)), ev.mods)
        elif k == "wheel":
            pos = self._to_view(ev.x, ev.y)
            vp = self._vp()
            QApplication.sendEvent(vp, QWheelEvent(
                QPointF(pos), QPointF(vp.mapToGlobal(pos)), QPoint(),
                QPoint(int(ev.dx), int(ev.dy)), self.buttons, qt_mods(ev.mods),
                Qt.ScrollPhase.NoScrollPhase, False))
        elif k == "command":
            self.run_command(ev.text, ev.args)
        # "wait" is the player's: it is a pause between deliveries

    def drag_points(self, ev):
        """sec8.5: a drag segment is split into moves of at most `step_px`
        VIEW pixels, at least two, so `startDragDistance()` and rubber-band
        logic see what a real mouse would give them. Returns the viewport
        points to visit, the last being the segment's own endpoint.

        The player delivers each as its OWN pump step (`px`): interpolating
        in a loop here with `processEvents()` between moves let the pump's
        next timer fire mid-drag, and the release arrived after the first
        move -- measured, a 240in wall came out 18in long."""
        end = self._to_view(ev.x, ev.y)
        start = self.pos if self.pos is not None else end
        dx, dy = end.x() - start.x(), end.y() - start.y()
        dist = (dx * dx + dy * dy) ** 0.5
        n = max(2, int(-(-dist // self.step_px)))
        return [end if i == n else QPoint(round(start.x() + dx * i / n),
                                          round(start.y() + dy * i / n))
                for i in range(1, n + 1)]

    def move_px(self, p: QPoint, mods):
        self.pos = p
        self._mouse(QEvent.Type.MouseMove, p, Qt.MouseButton.NoButton,
                    self.buttons, mods)
