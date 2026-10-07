"""Where in the design a `check()` message points -- so the "Malformed design
file" report can take the user THERE (Patrick, 2026-10-07: *"when I get this
error I want to be able to click on the error items and have the tool take me
to the point on the design and zoom in"*).

A violation message names its subjects by document id (`w89`, `o54`,
`r20`, `v12`) or, for I11, by room NAME in quotes. The scene cannot answer
for an id -- a live item's uid is not the document's id, which is canonical
and renumbered by geometry at every save (`bridge.apply_design_to_scene`) --
but the DOCUMENT can: a vertex has its coordinates, a wall names two
vertices, an opening names a wall and an anchor along it, a room names the
corners of its outline. So this resolves against the dict that was opened,
Qt-free, and returns plain numbers.

`subjects(message)` is `validate._invariant_key`'s own id rule, so the two
cannot drift: an id is lowercase letters + digits, a name is anything in
single quotes.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from floorplanner.design.validate import _invariant_key

_WIDTH = re.compile(r"^\s*(\d{2})(\d{2})\s*$")


def subjects(message: str):
    """The ids and quoted names a message points at, in a stable order."""
    return _invariant_key(message)[1]


@dataclass(frozen=True)
class Spot:
    """A place in the design: the level it is on (its NAME, which is what
    the application switches floors by) and a plan rectangle in inches,
    `(x0, y0, x1, y1)`, around everything the message named."""
    level: str | None
    rect: tuple
    found: tuple          # the subjects that resolved, in order
    missing: tuple        # the subjects that did not


def _index(doc):
    by = {"levels": {}, "vertices": {}, "walls": {}, "rooms": {}, "openings": {},
          "furnishings": {}, "names": {}}
    for lv in doc.get("levels", []) or []:
        by["levels"][lv.get("id")] = lv.get("name")
    for v in doc.get("vertices", []) or []:
        by["vertices"][v.get("id")] = v
    for w in doc.get("walls", []) or []:
        by["walls"][w.get("id")] = w
        for op in w.get("openings", []) or []:
            by["openings"][op.get("id")] = (op, w)
    for r in doc.get("rooms", []) or []:
        by["rooms"][r.get("id")] = r
        if r.get("name"):
            by["names"].setdefault(r["name"], r)
    for f in doc.get("furnishings", []) or []:
        by["furnishings"][f.get("id")] = f
    return by


def _opening_width(code):
    m = _WIDTH.match(str(code or ""))
    return float(m.group(1)) if m else 36.0


def _points_of(subject, by):
    """The plan points a subject covers, and its level id -- or (None, None)."""
    v = by["vertices"].get(subject)
    if v is not None:
        return [(float(v["x"]), float(v["y"]))], v.get("level")
    w = by["walls"].get(subject)
    if w is not None:
        pts = [p for vid in (w.get("v1"), w.get("v2"))
               for p in _points_of(vid, by)[0] or []]
        return pts, w.get("level")
    hit = by["openings"].get(subject)
    if hit is not None:
        op, w = hit
        a, b = _points_of(w.get("v1"), by)[0], _points_of(w.get("v2"), by)[0]
        if not a or not b:
            return None, None
        (ax, ay), (bx, by_) = a[0], b[0]
        length = math.hypot(bx - ax, by_ - ay)
        if length < 1e-9:
            return [(ax, ay)], w.get("level")
        ux, uy = (bx - ax) / length, (by_ - ay) / length
        width = _opening_width(op.get("code"))
        anchor = op.get("anchor") or {}
        frm, off = anchor.get("from", "v1"), float(anchor.get("offset_in", 0.0) or 0.0)
        if frm == "v1":
            s0 = off
        elif frm == "v2":
            s0 = length - off - width
        else:
            s0 = length / 2.0 + off - width / 2.0
        return ([(ax + ux * s0, ay + uy * s0), (ax + ux * (s0 + width), ay + uy * (s0 + width))],
                w.get("level"))
    r = by["rooms"].get(subject) or by["names"].get(subject)
    if r is not None:
        pts = [p for e in r.get("outline", []) or []
               for p in _points_of(e.get("v"), by)[0] or []]
        return pts, r.get("level")
    f = by["furnishings"].get(subject)
    if f is not None:
        pos = f.get("pos") or [0, 0]
        return [(float(pos[0]), float(pos[1]))], f.get("level")
    return None, None


def locate(doc, message: str):
    """The `Spot` a violation message points at in `doc`, or None when none
    of its subjects can be placed. The rectangle encloses every subject
    that resolved; the level is the first resolved subject's."""
    by = _index(doc)
    pts, level, found, missing = [], None, [], []
    for s in subjects(message):
        p, lid = _points_of(s, by)
        if not p:
            missing.append(s)
            continue
        found.append(s)
        pts.extend(p)
        if level is None and lid is not None:
            level = by["levels"].get(lid, lid)
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return Spot(level, (min(xs), min(ys), max(xs), max(ys)), tuple(found), tuple(missing))
