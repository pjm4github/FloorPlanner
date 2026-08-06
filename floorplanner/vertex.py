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

**THE TWO OPERATIONS, and P4.5 left exactly these two.** `Vertex.at(p)` makes a
NEW corner -- a deliberate DETACH, leaving every sharer where it was.
`v.relocated_to(p)` carries THIS vertex's identity to a new position, so every
end rebound to it is still the same corner, which is what lets a promoted
neighbour follow a drag because it IS the corner rather than because a scan
remembered to drag it. Sharing is created by handing one wall's vertex to
another's end (`set_end_vertex`) and broken by detaching.

**SPLIT-ON-WRITE IS GONE (P4.5).** Until then, assigning a point to a wall's
`p1` was a third way in: it minted a fresh vertex for that end and left any
sharer behind. That was P3.1's compatibility shim, and it did its job -- it let
this store replace the old coordinate pairs underneath a green suite. But it was
ONE SPELLING FOR BOTH OPERATIONS ABOVE, so a reader could not tell which a call
site meant, and four separate defects came from something downstream being left
on the old vertex. Its last caller went at P4.5(33); the setters, the
split helper and the counter went with it. **The guarantee now lives in
`tools/gate.py`, which fails on any coordinate assignment to a wall end anywhere
in this package** -- at source, where it cannot go vacuous, rather than as a
runtime counter that nothing can increment.

(That check reads the source TEXT, so it cannot tell code from prose -- which is
why this paragraph spells the retired form out in words. A false positive in the
other direction from every boundary in the plan's instrument table, and cheaper
to write around than to teach a grep about docstrings.)

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

    def relocated_to(self, p) -> "Vertex":
        """MOVE THIS CORNER (P3.3). Returns a vertex at `p` carrying THIS one's
        identity, so every wall end rebound to it is the same corner in a new
        place -- not a new corner.

        The difference from `Vertex.at` is the whole of P3.1-vs-P3.3. A DETACH
        answers "this wall's end moved, and anything sharing it did not"; a
        RELOCATION answers "the corner moved, and everything on it came along".
        Until P4.5 there was a third way in -- assigning `p1`/`p2` -- which
        split, because a bare assignment cannot know whether the caller meant
        the end or the corner. That ambiguity is why it is gone.

        `self` when the position is unchanged: the drag re-applies the same
        delta on every mouse event that does not actually move.

        THE MINT HERE IS FORCED, and it has to be (defect 21, found by P3.5's
        by-construction test). Reading `self._uid` instead of `self.uid` looked
        like harmless laziness, but a vertex that had never been NAMED carried
        `None` across the move -- so the "same corner" got a fresh identity the
        first time anyone asked, silently. Nothing observably broke while only
        the document walk read uids, and it would have become a live bug at
        P4.5, which serializes groups by member id. This is not the per-READ
        allocation P3.1 removed: a relocation is a genuine move, orders of
        magnitude rarer than the reads on the paint path."""
        mine = self._pt
        if isinstance(p, QPointF):
            x, y = p.x(), p.y()
        else:
            x, y = p[0], p[1]
        if x == mine.x() and y == mine.y():
            return self
        return Vertex(x, y, uid=self.uid)

    def __repr__(self):
        return f"Vertex({self._uid or '<unnamed>'} @ {self.x:.3f}, {self.y:.3f})"
