"""Session labels (0265-report.md, Patrick's word on the callouts: *"I always
want the SESSION LABELS shown ... I want W7/V12 specifically"*).

Every live item carries a session label -- `W7` a wall, `V12` a corner,
`O3` an opening, `R2` a room, `F4` a furnishing, `RF1` a roof -- minted
here, once per item, and fixed for the item's lifetime. It is what the
plan's callouts write, what the wall dialog's Id row says, and what the
*Malformed design file* report is translated into.

WHEN A PLAN IS OPENED the labels are taken FROM THE FILE'S OWN IDS
(`adopt`: `w7` is `W7`, `rf1` is `RF1`), so the file's ids and the
session's labels match, as he assumes they do, and a reported `w7` is
the `W7` on screen. The counters are kept past every adopted number so
nothing minted later collides. An id without that shape (another tool's
`wall_3`) gets a fresh label, and the report then says the label.

The labels are not the document's ids: `design_from_scene` renumbers by
geometry at every save (`vertex.py`'s module note), which is why a
session needs a name of its own for a thing a user is looking at.
"""
from __future__ import annotations

import re

__all__ = ["mint", "adopt", "reset", "PREFIXES"]

PREFIXES = {"wall": "W", "vertex": "V", "opening": "O", "room": "R",
            "furnishing": "F", "roof": "RF"}

_COUNTERS: dict[str, int] = {}
_ID_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


def mint(prefix: str) -> str:
    """The next fresh label with `prefix` (`W1`, `W2`, ...)."""
    n = _COUNTERS.get(prefix, 0) + 1
    _COUNTERS[prefix] = n
    return f"{prefix}{n}"


def adopt(prefix: str, file_id) -> str:
    """The session label for a loaded item: the file's own id in the
    session's spelling when it has the shape (`w7` -> `W7`), the counter
    kept past it; else a fresh label."""
    m = _ID_RE.match(str(file_id or ""))
    if m and m.group(1).upper() == prefix:
        n = int(m.group(2))
        _COUNTERS[prefix] = max(_COUNTERS.get(prefix, 0), n)
        return f"{prefix}{n}"
    return mint(prefix)


def matches(label: str, file_id) -> bool:
    """True when a session label and a file id name the same thing in the
    two spellings (`W7` and `w7`)."""
    return bool(label) and bool(file_id) and str(label).upper() == str(file_id).upper()


def reset():
    """Forget every counter (a test's own clean start)."""
    _COUNTERS.clear()
