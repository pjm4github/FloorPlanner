"""Macro language v2: the player (MACRO_SPEC.md sec8).

    text -> check (parse + validate) -> expand -> [InputEvent] -> QtEventSink

NOTHING runs unless the whole macro is valid (sec8.3): every syntax and
validation error is returned, positioned, and no event is delivered.

DELIVERY IS A TIMER-DRIVEN PUMP inside a local event loop, not a plain
`for` loop. A delivered event can open a modal dialog -- a door's size
prompt, a roof's End-On dialog, a context menu -- and `sendEvent` then does
not return until that dialog closes. The pump schedules the NEXT step
before it delivers the current one, so the following `TYPE` / `KEY {Enter}`
events are delivered from inside the dialog's own event loop and reach it.
It is the mechanism `MacroRunner._modal_step` has always used for `PUP`.

The result is the dict `MainWindow.run_macro` already returns --
`{ok, steps, log, errors, counts}` -- plus `warnings`.
"""
from __future__ import annotations

from collections import deque

from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWidgets import QApplication

from floorplanner.macro import MacroRunner
from floorplanner.macro2 import keys
from floorplanner.macro2.expand import InputEvent, expand, release_all
from floorplanner.macro2.sink import QtEventSink
from floorplanner.macro2.validate import check

#: the application's tool letters -- ONE table, `MacroRunner`'s (sec4)
TOOLS = MacroRunner._TOOL_CODES


class Player:
    def __init__(self, win, step_px: float = 8.0, delay_ms: int = 0):
        self.win = win
        self.step_px = step_px
        self.delay_ms = max(0, int(delay_ms))     # optional per-event pacing
        self.log = []
        self.errors = []
        self.warnings = []

    def _result(self, steps):
        return {"ok": not self.errors, "steps": steps, "log": self.log,
                "errors": self.errors, "warnings": self.warnings,
                "counts": self.win.scene_summary()["counts"]}

    def run(self, text: str) -> dict:
        res = check(text, TOOLS)
        if res.errors:
            self.errors = [str(e) for e in res.errors]
            self.log = [f"ERR {e}" for e in self.errors]
            return self._result(0)
        events, warnings = expand(res.macro)
        self.warnings = list(warnings)
        self._deliver(events)
        self.log = [f"ok  line {ln.line}" for ln in res.macro.lines] \
            + [f"WARN {w}" for w in self.warnings] \
            + [f"ERR {e}" for e in self.errors]
        return self._result(len(res.macro.lines))

    # -- the pump -----------------------------------------------------------
    def _deliver(self, events):
        sink = QtEventSink(self.win, TOOLS, self.step_px)
        queue = deque(events)
        loop = QEventLoop()
        state = {"mods": frozenset(), "held": set(), "done": False}

        def finish():
            if state["done"]:
                return
            state["done"] = True
            # a macro that ends with a menu or a dialog still open would hang
            # the caller in that dialog's loop: cancel it, and say so
            for _ in range(8):
                w = QApplication.activePopupWidget() or QApplication.activeModalWidget()
                if w is None:
                    break
                self.warnings.append(
                    f"{type(w).__name__} was still open at the end of the macro; closed")
                w.close()
                QApplication.processEvents()
            sink.reset()                 # the guard: no modifier left down
            loop.quit()

        def abort(exc, ev):
            self.errors.append(f"line {ev.line}: {type(exc).__name__}: {exc}")
            queue.clear()
            # the guard: whatever the failure, no key or modifier stays down
            for rel in release_all(state["mods"], state["held"]):
                try:
                    sink.deliver(rel)
                except Exception:                      # noqa: BLE001
                    pass
            finish()

        def track(ev: InputEvent):
            if ev.kind == "key_down":
                state["held"].add(ev.key)
            elif ev.kind == "key_up":
                state["held"].discard(ev.key)
            state["mods"] = frozenset(
                keys.MODIFIER_KEYS[k] for k in state["held"] if k in keys.MODIFIER_KEYS)

        def step():
            if state["done"]:
                return
            if not queue:
                finish()
                return
            ev = queue.popleft()
            if ev.kind == "move":
                # one drag segment -> its interpolated moves, each a step of
                # its own, so nothing else can be delivered between them
                pts = sink.drag_points(ev)
                queue.extendleft(reversed([
                    InputEvent("px", mods=ev.mods, x=p.x(), y=p.y(), line=ev.line)
                    for p in pts]))
                ev = queue.popleft()
            # schedule the NEXT step first: delivering this one may block in
            # a modal loop, and the rest of the macro must run inside it
            QTimer.singleShot(int(ev.ms) if ev.kind == "wait" else self.delay_ms, step)
            try:
                if ev.kind != "wait":
                    track(ev)
                    sink.deliver(ev)
            except Exception as exc:                   # noqa: BLE001
                abort(exc, ev)

        QTimer.singleShot(0, step)
        loop.exec()
        QApplication.processEvents()


def run_v2(win, text: str) -> dict:
    return Player(win).run(text)
