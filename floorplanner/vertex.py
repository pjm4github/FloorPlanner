"""The live vertex store (P3.1).

A `Vertex` is a shared, identity-bearing point. Two wall ends that reference the
SAME `Vertex` object are the same corner -- that is the whole model, and it is
why there is no registry here: the "table" is simply the set of vertices
reachable from the walls, exactly as `Design.vertices` is.

**Uids are persistent and minted once.** They are stable across edits and so
macro-addressable, which is what P4.5 needs when it serializes groups by member
id. That is deliberately NOT the same thing as the ids in a FILE: those stay
canonical, renumbered geometrically at serialization by `design/canonical.py`.
Persistence is an in-memory property, canonical form is the interchange
property, and P2.3's canonical comparison is the bridge between them -- so
nothing on disk changes because live items carry uids.

**Assignment is SPLIT-ON-WRITE, not shared-move.** Moving one wall's end mints a
fresh vertex for that end and leaves any sharer on the old one, which preserves
today's independent-ends semantics exactly -- a shared move would drag a
neighbour's end and break tests that have nothing to do with this task. Sharing
is created explicitly (assign one wall's vertex to another's end) and broken
explicitly (this split). SHARED MOVEMENT ARRIVES AT P3.3, as the wall-move
operation, never as a side effect of assignment: representation changes first,
behaviour second, each observable separately.

Every split is counted (`split_count`) and ATTRIBUTED TO ITS CALL SITE
(`split_sites`), so `--verify-design` can report not just how many implicit
splits an operation caused but WHERE. The bare count told us the drag path
splits; it could not say which line, and "which call sites should become real
vertex moves" is a question about lines. P3.3 promotes the first of them --
the wall-move drag -- and the attribution is how the rest are found.

**A MOVE IS NOT A SPLIT** (P3.3). `moved_to` mints a new identity for one
wall's end; `relocated_to` carries this vertex's identity to a new position, so
every end rebound to it is still the same corner. The wall-move operation uses
the latter, which is what lets a promoted neighbour follow a drag because it IS
the corner rather than because a scan remembered to drag it.

**A vertex is never mutated in place**, which is what makes the two performance
decisions below safe. `point()` returns the SAME `QPointF` rather than a copy,
and `uid` is minted lazily on first read. Both matter: `p1`/`p2` are read on
every rebuild, paint and hit-test, so allocating per read cost ~50% of
`rebuild` and nearly doubled `bake` when this was first written. Because a MOVE
produces a NEW vertex, a caller holding an old `p1` still sees the old position
-- identical to the previous behaviour, where assignment rebound the attribute
to a fresh QPointF. (Verified before relying on it: nothing in the codebase
mutates a `p1`/`p2` in place -- every access is `.x()` / `.y()` or a whole-object
read.)
"""
import itertools
import sys

from PyQt6.QtCore import QPointF

_UIDS = itertools.count(1)
_SPLITS = [0]
_SITES = {}                      # (file, function, line) -> splits caused there

_THIS_FILE = __file__


def split_count() -> int:
    """Total split-on-writes since start. Callers record a delta across an
    operation rather than reading it absolutely."""
    return _SPLITS[0]


def split_sites() -> dict:
    """`{(file, function, line): count}` -- cumulative, same convention as
    `split_count`: callers diff it across an operation.

    Returned as a copy so a caller can keep it as a mark without it moving
    underneath them."""
    return dict(_SITES)


def _blame() -> tuple:
    """The call site that caused a split: the first frame outside this module
    that is not a `p1`/`p2` property setter.

    Skipping the setters is the whole point -- every split arrives through them,
    so blaming `walls.py: p1` would attribute all of them to one line and answer
    nothing. Uses `sys._getframe` rather than `traceback`: this runs on genuine
    coordinate moves (never on a READ, which is the hot path P3.1 had to fix),
    but a drag still moves several vertices per mouse event."""
    try:
        f = sys._getframe(2)
    except ValueError:                                  # pragma: no cover
        return ("<unknown>", "<unknown>", 0)
    while f is not None and (f.f_code.co_filename == _THIS_FILE
                             or f.f_code.co_name in ("p1", "p2")):
        f = f.f_back
    if f is None:                                       # pragma: no cover
        return ("<unknown>", "<unknown>", 0)
    return (f.f_code.co_filename, f.f_code.co_name, f.f_lineno)


class Vertex:
    """One corner. Identity is the point; `uid` names it for the document."""

    __slots__ = ("_uid", "_pt")

    def __init__(self, x: float, y: float, uid: str = None):
        self._uid = uid
        self._pt = QPointF(x, y)

    @classmethod
    def at(cls, p) -> "Vertex":
        """A fresh vertex at `p` (a QPointF or an (x, y) pair)."""
        if isinstance(p, QPointF):
            return cls(p.x(), p.y())
        return cls(p[0], p[1])

    @property
    def uid(self) -> str:
        """Minted on FIRST READ, then fixed for this vertex's lifetime. Lazy
        because the hot paths move vertices without ever naming them; only the
        document walk asks."""
        if self._uid is None:
            self._uid = f"V{next(_UIDS)}"
        return self._uid

    @property
    def x(self) -> float:
        return self._pt.x()

    @property
    def y(self) -> float:
        return self._pt.y()

    def point(self) -> QPointF:
        """The vertex's position. Shared, not copied -- see the module note."""
        return self._pt

    def moved_to(self, p) -> "Vertex":
        """SPLIT-ON-WRITE. `self` when the position is unchanged -- so a no-op
        assignment (there are many: every rebuild, every re-set of the same
        coordinates) keeps identity and keeps any sharing. Otherwise a NEW
        vertex, leaving every other user of `self` exactly where they were."""
        mine = self._pt
        if isinstance(p, QPointF):
            x, y = p.x(), p.y()
        else:
            x, y = p[0], p[1]
        if x == mine.x() and y == mine.y():
            return self
        _SPLITS[0] += 1
        site = _blame()
        _SITES[site] = _SITES.get(site, 0) + 1
        return Vertex(x, y)

    def relocated_to(self, p) -> "Vertex":
        """MOVE THIS CORNER (P3.3). Returns a vertex at `p` carrying THIS one's
        identity, so every wall end rebound to it is the same corner in a new
        place -- not a new corner.

        The difference from `moved_to` is the whole of P3.1-vs-P3.3. A split
        answers "this wall's end moved, and anything sharing it did not"; a
        relocation answers "the corner moved, and everything on it came along".
        Only the explicit wall-move operation may relocate: `p1`/`p2` assignment
        still splits, because a bare assignment does not know whether the caller
        meant the end or the corner. Not counted as a split, because it is not
        one.

        `self` when the position is unchanged, for the same reason `moved_to`
        does it: the drag re-applies the same delta on every mouse event that
        does not actually move."""
        mine = self._pt
        if isinstance(p, QPointF):
            x, y = p.x(), p.y()
        else:
            x, y = p[0], p[1]
        if x == mine.x() and y == mine.y():
            return self
        return Vertex(x, y, uid=self._uid)

    def __repr__(self):
        return f"Vertex({self._uid or '<unnamed>'} @ {self.x:.3f}, {self.y:.3f})"
