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

Every split is counted (`split_count`) so `--verify-design` can report implicit
splits per operation -- that count is exactly the data P3.3 needs to decide
which call sites should become real vertex moves.

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

from PyQt6.QtCore import QPointF

_UIDS = itertools.count(1)
_SPLITS = [0]


def split_count() -> int:
    """Total split-on-writes since start. Callers record a delta across an
    operation rather than reading it absolutely."""
    return _SPLITS[0]


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
        return Vertex(x, y)

    def __repr__(self):
        return f"Vertex({self._uid or '<unnamed>'} @ {self.x:.3f}, {self.y:.3f})"
