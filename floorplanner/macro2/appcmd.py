"""Application commands of the macro language v2 -- `@NAME arg ...`
(MACRO_SPEC.md sec14; Patrick, 2026-10-04: "carry v1's high level commands
as a single command using the form @COMMAND").

An application command makes the application ACT -- place a furnishing, cut
a door, open a file -- where every other v2 line simulates input. The
commands are the existing macro language's own (`floorplanner/macro.py`),
and they are RUN BY ITS HANDLERS: `LEGACY_TOKEN` maps each v2 name to the
token `MacroRunner._dispatch` already understands, so nothing about `PLACE`
or `DORMER` is written a second time.

What is carried is what v2 has no other way to say. The existing words that
simulate input are NOT carried, because v2 says them itself: `CLICK`,
`RCLICK`, `DRAG`, `MOVE`, `PRESS`, `RELEASE` (a mouse chain), `TYPE`, `WAIT`,
`ENTER`, `ESC`, the arrows and the shortcut carets (`KEY`), `TOOL` and the
digits (a tool letter), `PUP` (`RCLICK` then `KEY`).

`COMMANDS` gives each name its argument count, `(fewest, most)`, so a wrong
count is a VALIDATION error, found before anything runs (sec8.3). What an
argument must BE -- a number, a catalog id, a path that exists -- is the
handler's to judge when it runs, and a failure there aborts the macro with
its line.
"""
from __future__ import annotations

#: v2 name -> (fewest arguments, most arguments)
COMMANDS = {
    "PLACE": (3, 4),        # kind x y [rot]
    "WALL": (4, 5),         # x1 y1 x2 y2 [ext|int]
    "DOOR": (3, 3),         # x y WWHH
    "WINDOW": (3, 3),       # x y WWHH
    "ROOM": (3, 3),         # name x y
    "DORMER": (5, 7),       # x y width eaves ridge [dx dy]
    "SELECT": (2, 2),       # x y
    "SELECTALL": (0, 0),
    "DESELECT": (0, 0),
    "ROTATE": (1, 1),       # deg
    "MOVETO": (2, 2),       # x y
    "DELETE": (0, 0),
    "ZOOMFIT": (0, 0),
    "OPEN": (1, 1),         # path
    "SAVE": (1, 1),         # path
    "NEW": (0, 0),
    "SHOT": (1, 1),         # path
    "FLOOR": (1, 1),        # name          (the existing `^F "name"`)
    "NEWFLOOR": (1, 1),     # name          (the existing `^+F "name"`)
    "SHUFFLE": (1, 1),      # on|off        (the existing `^H "on"`)
}

#: v2 name -> the existing language's token for it, where the two differ
LEGACY_TOKEN = {"FLOOR": "^F", "NEWFLOOR": "^+F", "SHUFFLE": "^H"}

#: DORMER takes 5 or 7 arguments, never 6: the direction is a pair
_FORBIDDEN_COUNTS = {"DORMER": {6}}


def legacy_token(name: str) -> str:
    return LEGACY_TOKEN.get(name, name)


def arity_error(name: str, n: int):
    """None when `n` arguments is acceptable for `name`, else the message."""
    lo, hi = COMMANDS[name]
    if lo <= n <= hi and n not in _FORBIDDEN_COUNTS.get(name, ()):
        return None
    if lo == hi:
        want = f"{lo} argument{'s' if lo != 1 else ''}"
    elif name in _FORBIDDEN_COUNTS:
        want = f"{lo} or {hi} arguments"
    else:
        want = f"{lo} to {hi} arguments"
    return f"@{name} takes {want}, not {n}"


def quote(arg: str) -> str:
    """An argument as the serializer writes it (sec10, sec14): bare when it
    can be, in double quotes when it is empty, starts with a quote, or holds
    a space, a tab or a semicolon."""
    if arg == "" or arg[0] == '"' or any(c in arg for c in ' \t;'):
        return '"' + arg + '"'
    return arg
