"""Macro language v2: the recorder's state machine (MACRO_SPEC.md sec9).

Qt-FREE on purpose. The dialog's event filter turns each Qt event into plain
values -- a button name, scene coordinates, a set of `Mod`, a `Key` -- and
calls a method here; what comes out is canonical v2 text, a line at a time,
through `emit`. So every rule of sec9 is unit-tested without a window.

What it records, and how:

* TOOL changes are held and written as the PREFIX of the next line; one
  still pending when recording stops is written on its own line.
* A MOUSE press opens a CHAIN. While the button is held the pointer is
  tracked, and when the modifiers change the current segment is closed at
  the pointer's position with the PREVIOUS modifiers and a new one begins.
  The release closes the last segment with the modifiers held at release.
  A press and release closer than the drag threshold, with no modifier
  change, is a plain click at the press point (hand jitter dropped).
* A DOUBLE CLICK replaces the `CLICK` just written at that point with
  `DCLICK`; a drag that follows becomes its segments.
* Printable KEYS typed into a text field gather into one `TYPE` line;
  trailing spaces come off it and follow as `KEY {Space}` strokes. Any
  other key is a `KEY` stroke, and consecutive strokes share a line.
* An APPLICATION COMMAND (sec14) is written when the app reports an action
  whose parameters came from a dialog -- a door's size, a room's name --
  so replay never has to drive that dialog.
"""
from __future__ import annotations

from floorplanner.macro2 import ast, keys
from floorplanner.macro2.serialize import line as write_line
from floorplanner.macro2.ast import Mod

_NONE = frozenset()
_VERB = {"left": "CLICK", "right": "RCLICK", "middle": "MCLICK",
         "back": "XCLICK1", "forward": "XCLICK2"}


def _digits(px: float) -> int:
    """Decimal places worth keeping for a scene coordinate when one view
    pixel is `px` scene units: none while a pixel is half an inch or more,
    so a recording made at an ordinary zoom reads `CLICK 120 96`."""
    if px >= 0.5:
        return 0
    return 1 if px >= 0.05 else 2


class Recorder:
    def __init__(self, emit, retract=None, drag_px: float = 4.0,
                 wait_ms: float | None = None, hover: bool = False):
        self.emit = emit                 # (line text) -> None
        self.retract = retract           # (line text) -> bool: remove the last line
        self.drag_px = float(drag_px)
        self.wait_ms = wait_ms           # emit WAIT for gaps longer than this
        self.hover = hover
        self._tool = None                # a tool letter awaiting its line
        self._chain = None               # the open mouse chain
        self._typed = ""                 # the TYPE buffer
        self._strokes = []               # the KEY line being gathered
        self._last_click = None          # (text, button, x, y) of the last plain click
        self._pointer = None             # last recorded pointer position
        self._last_t = None

    # -- output -------------------------------------------------------------
    def _write(self, command):
        text = write_line(ast.Line(self._tool, command))
        self._tool = None
        self.emit(text)
        return text

    def flush(self):
        """Write out the gathered `TYPE` text and `KEY` strokes."""
        self._flush_typed()
        if self._strokes:
            strokes, self._strokes = tuple(self._strokes), []
            self._write(ast.KeyPress(strokes))

    def _flush_typed(self):
        """The TYPE buffer, written. Trailing spaces cannot be said on a TYPE
        line (sec6.1), so they come off it and become `{Space}` strokes --
        left GATHERING, so that a stroke typed next shares their line."""
        if not self._typed:
            return
        body = self._typed.rstrip(" ")
        spaces = len(self._typed) - len(body)
        self._typed = ""
        if body:
            self._write(ast.TypeText(body))
        self._strokes.extend([ast.Stroke(_NONE, keys.named("Space"))] * spaces)

    def _gap(self, t):
        if t is None:
            return
        if self.wait_ms is not None and self._last_t is not None \
                and t - self._last_t > self.wait_ms:
            self.flush()
            self._write(ast.Wait(float(round(t - self._last_t))))
        self._last_t = t

    def stop(self):
        """Recording ended: nothing gathered is lost, and a tool change still
        waiting for a line gets one of its own (sec9)."""
        if self._chain is not None:
            c = self._chain
            self.release(c["last"][0], c["last"][1], c["mods"])
        self.flush()
        if self._tool is not None:
            self._write(None)

    # -- tools and application commands -------------------------------------
    def tool(self, letter: str):
        self.flush()
        self._tool = letter
        self._last_click = None

    def command(self, name: str, args):
        self.flush()
        self._last_click = None
        self._write(ast.AppCommand(name, tuple(str(a) for a in args)))

    # -- mouse --------------------------------------------------------------
    def _pt(self, x, y, px):
        d = _digits(px)
        return round(float(x), d) + 0.0, round(float(y), d) + 0.0

    def press(self, button, x, y, mods=_NONE, px: float = 1.0, t=None, double=False):
        self._gap(t)
        self.flush()
        x, y = self._pt(x, y, px)
        mods = frozenset(mods)
        self._chain = {"button": button, "double": double, "px": px,
                       "segs": [ast.Segment(mods, x, y)], "mods": mods,
                       "press": (x, y), "last": (x, y), "far": 0.0,
                       "changed": False}

    def move(self, x, y, mods=_NONE, px: float | None = None, t=None):
        c = self._chain
        if c is None:
            if self.hover:
                self._hover(x, y, mods, px or 1.0, t)
            return
        mods = frozenset(mods)
        self._turn(c, mods)
        x, y = self._pt(x, y, c["px"])
        c["last"] = (x, y)
        px_ = c["px"] or 1.0
        dist = ((x - c["press"][0]) ** 2 + (y - c["press"][1]) ** 2) ** 0.5 / px_
        c["far"] = max(c["far"], dist)

    @staticmethod
    def _turn(c, mods):
        """The modifiers changed: close the current segment where the
        pointer IS, with the modifiers it had, and start the next (sec9)."""
        if mods == c["mods"]:
            return
        last = c["segs"][-1]
        if c["last"] != (last.x, last.y):
            c["segs"].append(ast.Segment(c["mods"], c["last"][0], c["last"][1]))
        c["mods"] = mods
        c["changed"] = True

    def release(self, x, y, mods=_NONE, t=None):
        c = self._chain
        if c is None:
            return
        self._gap(t)
        self._chain = None
        mods = frozenset(mods)
        self.move_final(c, x, y)
        self._turn(c, mods)
        verb = "DCLICK" if c["double"] else _VERB[c["button"]]
        head = c["segs"][0]
        end = c["last"]
        self._pointer = end
        if not c["changed"] and c["far"] < self.drag_px:
            # hand jitter: a plain click at the PRESS point
            text = self._write(ast.Chain(verb, (head,)))
            self._pointer = (head.x, head.y)
            self._last_click = None if c["double"] else (text, c["button"], head.x, head.y)
            return
        segs = list(c["segs"])
        last = segs[-1]
        if len(segs) == 1 or end != (last.x, last.y) or c["mods"] != last.mods:
            # the last segment carries the modifiers held AT THE RELEASE
            # (sec5.2 rule 3) -- even when the pointer did not move after
            # the change, as a zero-length segment
            segs.append(ast.Segment(c["mods"], end[0], end[1]))
        self._write(ast.Chain(verb, tuple(segs)))
        self._last_click = None

    @staticmethod
    def move_final(c, x, y):
        d = _digits(c["px"])
        x, y = round(float(x), d) + 0.0, round(float(y), d) + 0.0
        px_ = c["px"] or 1.0
        c["last"] = (x, y)
        dist = ((x - c["press"][0]) ** 2 + (y - c["press"][1]) ** 2) ** 0.5 / px_
        c["far"] = max(c["far"], dist)

    def dblclick(self, button, x, y, mods=_NONE, px: float = 1.0, t=None):
        """Qt delivers Press, Release, DblClick, Release. The first pair has
        already been written as a `CLICK`; at the same point that line
        becomes a `DCLICK`, whose release (and any drag) is still to come."""
        if button != "left":
            self.press(button, x, y, mods, px, t)
            return
        xr, yr = self._pt(x, y, px)
        lc = self._last_click
        if lc is not None and lc[1] == button and (lc[2], lc[3]) == (xr, yr) \
                and self.retract is not None and self.retract(lc[0]):
            # the retracted CLICK may have carried a tool prefix: give it back
            prefix = lc[0].split(" ", 1)[0]
            if len(prefix) == 1 and prefix.isalpha():
                self._tool = prefix
        self._last_click = None
        self.press(button, x, y, mods, px, t, double=True)

    def click(self, verb_button, x, y, mods=_NONE, px: float = 1.0, t=None):
        """A click reported whole (the context-menu event of a right click)."""
        self._gap(t)
        self.flush()
        x, y = self._pt(x, y, px)
        self._pointer = (x, y)
        self._last_click = None
        self._write(ast.Chain(_VERB[verb_button], (ast.Segment(frozenset(mods), x, y),)))

    def _hover(self, x, y, mods, px, t):
        x, y = self._pt(x, y, px)
        if self._pointer is not None:
            d = ((x - self._pointer[0]) ** 2 + (y - self._pointer[1]) ** 2) ** 0.5 / (px or 1.0)
            if d < 4 * self.drag_px:
                return
        self._gap(t)
        self.flush()
        self._pointer = (x, y)
        self._write(ast.Move(frozenset(mods), x, y))

    def wheel(self, dx, dy, x, y, mods=_NONE, px: float = 1.0, t=None):
        """`WHEEL` acts at the current pointer (sec5.6), so a wheel event
        somewhere the pointer was not last recorded is preceded by a `MOVE`."""
        self._gap(t)
        self.flush()
        self._last_click = None
        x, y = self._pt(x, y, px)
        if self._pointer != (x, y):
            self._pointer = (x, y)
            self._write(ast.Move(_NONE, x, y))
        self._write(ast.Wheel(frozenset(mods), float(dx), float(dy)))

    # -- keyboard -----------------------------------------------------------
    def text(self, ch: str, t=None):
        """A printable character typed into a text field."""
        self._gap(t)
        if self._strokes:
            self.flush()
        self._last_click = None
        self._typed += ch

    def key(self, key: ast.Key, mods=_NONE, t=None):
        """Any other key press: one `KEY` stroke. A modifier key pressed on
        its own is not recorded -- it shows as a prefix on what it affects."""
        spec = keys.resolve(key)
        if spec is None or spec.mod is not None:
            return
        self._gap(t)
        self._flush_typed()
        self._last_click = None
        self._strokes.append(ast.Stroke(frozenset(mods), key))


__all__ = ["Mod", "Recorder"]
