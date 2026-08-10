"""The RoomItem graphics item plus room detection/binding algorithms and the
room-edge helpers.

Imports wall items + a few wall algorithms from floorplanner.walls at module
level (walls loads first).  FurnishingItem and the room dialogs are reached via
LATE imports to avoid an import cycle."""
import math

from PyQt6 import sip
from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import *  # noqa: F401

from floorplanner.config import *  # noqa: F401
from floorplanner.geometry import *  # noqa: F401
from floorplanner.vertex import Vertex
from floorplanner.walls import (
    WallItem, _CornerIndex, rebuild_all_walls, report_gesture_fault,
)
# `OpeningItem` and `report_opening_failure` left this module with
# `duplicate_wall` at P4.5: copying a wall's openings into a group was the only
# reason rooms.py ever built an opening or had one fail to fit.


def poly_area_sqft(corners) -> float:
    """Shoelace area of a closed polygon (inches) in square feet."""
    n = len(corners)
    a2 = 0.0
    for i in range(n):
        p, q = corners[i], corners[(i + 1) % n]
        a2 += p.x() * q.y() - q.x() * p.y()
    return abs(a2) / 2.0 / 144.0


def detect_room(scene, anchor: QPointF, floor=None):
    """The room at `anchor`: the enclosing FACE of the wall graph.

    Returns `(path, area_sqft, outline)` or None, where `outline` is a list of
    `OutlineEdge` -- so the caller's `RoomItem(..., corners=res[2])` gets an
    outline whose every edge already NAMES the wall covering it. Binding is
    then a fact the detection reports rather than a search that follows it,
    and `share_outline_vertices` (via `bind_room_walls`) turns those named
    walls into the shared corner identities of P3.5 (1).

    P3.5: this used to be a raster flood-fill (`_RoomGrid`) crossed with a
    hand-rolled planar face walk (`_WallGraph`), 220 lines of editor-side
    topology. It is now `topology.enclosing_face` over a one-shot lift of the
    scene (`design.bridge.face_at`) -- one definition of what a face is,
    shared with the document, instead of two that could disagree."""
    from floorplanner.design.bridge import face_at   # late: bridge imports rooms
    edges = face_at(scene, anchor, floor)
    if not edges:
        return None
    pts = [p for p, _w in edges]
    outline = [OutlineEdge(p, w) for p, w in edges]
    return room_path_from_corners(pts), poly_area_sqft(pts), outline


def unique_room_name(scene, base: str, exclude=None) -> str:
    """`base` if unused in the plan, else `base 2`, `base 3`, ..."""
    names = {it.name for it in scene.items()
             if isinstance(it, RoomItem) and it is not exclude}
    if base not in names:
        return base
    n = 2
    while f"{base} {n}" in names:
        n += 1
    return f"{base} {n}"


class OutlineEdge:
    """One edge of a room's perimeter: the corner it starts at, and the wall
    that covers it (`None` = an OPEN edge, the v5 `wall: null`).

    **The corner IS a vertex identity (P3.5).** It holds the very `Vertex`
    object the walls meeting there hold, so moving that corner moves the wall
    and the outline together -- not because anything recomputes, but because
    there is only one corner to move. This is the flip the whole phase is for.

    It was a bare COORDINATE from P3.2 until here, and deliberately so: P3.1's
    split-on-write world had no shared corner vertex to name, since at every
    corner each wall owned a distinct `Vertex`. Borrowing one wall's end would
    have picked arbitrarily between two; minting a room-owned one would have
    added a third object no wall referenced. Both encode an authority that did
    not exist yet, and a coordinate stated exactly what was known.
    `tests/test_outline.py` pinned that gap where it was, and its two guards
    flip here -- together, because they are two faces of one fact: an outline
    can only NAME a vertex once the corner IS one vertex.

    `p` stays a read-through property, so every existing caller keeps working
    -- the compat-shim discipline P3.1 used for `WallItem.p1`/`p2`. The
    representation moves; the callers do not.

    The `wall` reference came from P3.2: before it, a room had corners and an
    unordered `walls` list with no edge->wall mapping at all."""

    __slots__ = ("v", "wall")

    def __init__(self, p, wall=None):
        self.v = p if isinstance(p, Vertex) else Vertex.at(p)
        self.wall = wall

    @property
    def p(self) -> QPointF:
        """The corner's position -- read through to the vertex, shared not
        copied (see `vertex.Vertex.point`; a vertex is never mutated in
        place)."""
        return self.v.point()

    def __repr__(self):
        w = self.wall.wall_type if self.wall is not None else "open"
        return f"OutlineEdge(({self.p.x():.1f}, {self.p.y():.1f}), {w})"


def outline_self_intersects(room) -> bool:
    """Does this room's OWN outline cross itself? — I5b, asked of the scene.

    THE SAME PREDICATE the document check uses (`validate._seg_cross`), not a
    second one: one definition of "these two edges cross", per P3.4 point 1.
    Only the question's *timing* differs — I5b is a deep-only document check,
    and this asks it of a live room the instant a gesture deformed it."""
    from floorplanner.design.validate import _seg_cross  # late: design layer
    pts = [(c.x(), c.y()) for c in (room.corners or [])]
    n = len(pts)
    if n < 4:                       # a triangle cannot cross itself
        return False
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue            # adjacent edges share a corner, not a cross
            if _seg_cross(pts[i], pts[(i + 1) % n], pts[j], pts[(j + 1) % n]):
                return True
    return False


def report_self_intersections(scene, rooms):
    """Report any of `rooms` whose outline now crosses itself — P4.5's ruling
    on §2a, and the point is WHEN it is said.

    I5b already catches this exactly, but it is one of the three DEEP-ONLY
    checks: shadow mode never runs it while editing, while `save_path` does
    run it and REFUSES TO WRITE. So without this the user deforms a room,
    hears nothing, and finds out at the moment they try to keep their work —
    the same disease as defects 17 and 25, learning at the wrong moment. The
    save refusal stays exactly as it is (P4.1: do not write a corrupt plan);
    what changes is that the gesture speaks first.

    SCOPED to the rooms a move actually carried, so the cost is edges² over a
    handful of rooms rather than the plan. The message names the room AND the
    remedy, per the 06c2145 standard — a diagnostic the user cannot act on is
    only half a message.

    IT DOES NOT PROMISE THAT THE SAVE WILL REFUSE, and that omission is
    deliberate: measured, it sometimes will not. The document walk PLANARISES,
    so two crossing outline walls are split at their intersection and the room
    emits as a *pinched* loop that visits that point twice — which `_seg_cross`
    does not report, because it is a PROPER-crossing test by design (it must
    not fire on the collinear edges two rooms legitimately share). A message
    that told the user "you cannot save this" when they demonstrably can is
    exactly the 06c2145 failure: copy that reads as nonsense at a real value.
    The gap itself is register row 41, filed not fixed. Returns the rooms
    reported."""
    bad = [r for r in rooms if outline_self_intersects(r)]
    if not bad:
        return []
    names = [r.name for r in bad]
    if len(names) == 1:
        who = f"{names[0]}'s outline now crosses itself"
    elif len(names) == 2:
        who = f"{names[0]} and {names[1]} now have outlines that cross themselves"
    else:
        who = (f"{', '.join(names[:-1])} and {names[-1]} now have outlines "
               f"that cross themselves")
    report_gesture_fault(
        scene,
        f"{who} — undo, or extract the room before moving it.")
    return bad


def make_concept_room(scene, name, width_in, depth_in, at, floor=None):
    """A CONCEPT room (P4.4): a room typed in by dimension rather than drawn.

    Wall-less and floating by construction, which is what the schema means by
    the category: *"sketch units never intended to join the plan, and always
    floating"* — so I13 holds by construction and I11 exempts it, which is why
    a concept room can be parked anywhere, including over the plan, while you
    decide where it goes. Every outline edge is OPEN (`wall: null`) and draws
    dashed; `nominal_size` records the typed intent and is never authoritative
    — the outline is, exactly as the schema says.

    `at` is the CENTRE of the new room. Returns the `RoomItem`."""
    w, d = float(width_in), float(depth_in)
    if w <= 0 or d <= 0:
        raise ValueError("a concept room needs a positive width and depth")
    x0, y0 = at.x() - w / 2.0, at.y() - d / 2.0
    corners = [QPointF(x0, y0), QPointF(x0 + w, y0),
               QPointF(x0 + w, y0 + d), QPointF(x0, y0 + d)]
    room = RoomItem(unique_room_name(scene, name), QPointF(at),
                    room_path_from_corners(corners), poly_area_sqft(corners),
                    corners=[OutlineEdge(c) for c in corners])
    if floor is not None:
        room.floor = floor
    room.category = "concept"
    room.nominal_size = {"width_in": w, "depth_in": d}
    room.placement_state = "floating"
    room._floating_furnishings = []   # captured (empty), never re-scanned
    scene.addItem(room)
    room.update()
    return room


def rooms_holding(scene, vertex_ids):
    """Every room whose outline holds one of `vertex_ids` — the rooms a corner
    move will reshape, found by IDENTITY rather than by proximity.

    Defect 30's lesson, stated once: ask the corner who holds it. Three
    gestures now ask exactly this question — a group bake (`GroupItem`), Align
    to grid, and Distribute — and before P4.5 each answered it differently or
    not at all, which is how a room that was never selected ended up with its
    walls at x=150 and its outline at x=120. Scene-wide is not an oversight:
    identity makes a floor filter redundant, because a `Vertex` carries exactly
    one level (I2)."""
    if scene is None or not vertex_ids:
        return []
    return [it for it in scene.items()
            if isinstance(it, RoomItem)
            and any(id(e.v) in vertex_ids for e in it.outline)]


def relocate_corners(walls, rooms, target, scene=None):
    """Move each distinct corner of `walls` to `target(vertex)`; the walls AND
    every room outline holding those corners follow, because they hold the same
    `Vertex` objects. Returns the number of corners actually moved.

    THE ALTERNATIVE IS THE BUG, and it is measured. Assigning `p1`/`p2` splits
    on write, so each wall end comes away on a fresh vertex and the outline is
    left holding the old one — the walls move and the room does not. Measured
    at P4.5 on a row of three rooms: Align to grid took every selected room's
    walls onto the grid and left every outline off it (outline-to-wall corner
    sharing 4-of-4 → 1-of-4 and 0-of-4, two rooms gaining open edges), and
    Distribute destroyed all four corners' sharing on every room **while moving
    them by zero** — an assignment of the same coordinate still mints.

    `rooms` IS A STARTING SET, NOT THE GATHER. Every other room in the scene
    holding one of these corners is added via `rooms_holding`, and that
    widening is the whole point: the corner being moved is frequently a PARTY
    corner, so the neighbour that was never selected is holding it too. Passing
    only the selected rooms is what tore the neighbour — a room that never
    moved ending up with its wall at x=150 and its outline at x=120. That the
    neighbour DEFORMS rather than resisting is ruling 2a, not an accident: it
    follows because its corner moved.

    `target` returns the new point for a corner, or None to leave it."""
    if scene is None:
        scene = next((w.scene() for w in walls if w.scene() is not None), None)
    held = {id(w.end_vertex(a)) for w in walls for a in ("p1", "p2")}
    # AND THE GATHER WIDENS TO WALLS, NOT ONLY OUTLINES. An outside wall whose
    # end IS one of these corners must come along, or it is left behind on a
    # stale vertex and the network tears open at that corner -- measured on a
    # three-room row: aligning A and B moved the shared corner at (354, 118)
    # to (354, 120) while unselected C's own wall stayed short of it, giving C
    # a dashed open edge with genuinely no wall on it. A corner is one Vertex
    # (Phase 3); everything holding it moves, or it was never one corner.
    outside = [w for w in (scene.items() if scene is not None else ())
               if isinstance(w, WallItem) and w not in walls
               and any(id(w.end_vertex(a)) in held for a in ("p1", "p2"))]
    every_wall = list(walls) + outside
    holders = [(w, a) for w in every_wall for a in ("p1", "p2")]
    seen = {id(r) for r in rooms}
    every = list(rooms) + [r for r in rooms_holding(scene, held)
                           if id(r) not in seen]
    edges = [e for r in every for e in getattr(r, "outline", ()) or ()]
    # `old` keeps every vertex alive for the whole pass: the map is keyed by
    # id(), and an id freed mid-pass could be handed back to a new vertex.
    old = [w.end_vertex(a) for w, a in holders] + [e.v for e in edges]
    moved, n = {}, 0
    for v in old:
        if id(v) in moved:
            continue
        p = target(v)
        if p is None or (p.x() == v.x and p.y() == v.y):
            moved[id(v)] = v                 # unchanged: do NOT mint
        else:
            moved[id(v)] = v.relocated_to(p)
            n += 1
    for w, a in holders:
        w.set_end_vertex(a, moved[id(w.end_vertex(a))])
    for e in edges:
        e.v = moved[id(e.v)]
    for w in every_wall:
        w.rebuild()                          # repositions its openings too
    for r in every:
        # `path`/`area_sqft`/`corners` all DERIVE from the outline (P3.5), so
        # there is nothing to recompute -- only Qt to tell that the item's
        # geometry changed under it.
        r.prepareGeometryChange()
        r.update()
    return n


def share_outline_vertices(room):
    """Make `room`'s outline reference the SAME `Vertex` objects its walls do.

    THIS IS P3.5's FLIP, and the reason the phase exists. Afterwards a wall
    move updates the room outline BY CONSTRUCTION -- not because anything
    re-detects, but because there is only one corner to move and both the wall
    and the outline are holding it. `relocated_to` moves the corner; everything
    on it comes along.

    Two steps, and the first is why the outline could not do this before:
      1. WELD THE ROOM'S OWN CORNERS. At each corner two of the room's walls
         meet, and until now each owned a distinct `Vertex` -- so there was no
         single vertex for the outline to name (exactly what
         `test_a_corner_is_still_two_distinct_wall_vertices` pinned). Both ends
         are pointed at one anchor, using the same `_CornerIndex` fold that
         decides what one corner is everywhere else.
      2. POINT THE OUTLINE AT IT. Each edge adopts the corner vertex sitting
         at its coordinate.

    An edge whose coordinate matches no wall corner keeps the vertex it has --
    an OPEN edge (`wall is None`) spans a gap with no wall end to share, and
    inventing a share there would be the same false authority P3.2 refused."""
    walls = [w for w in room.walls if isinstance(w, WallItem)]
    if not walls or not room.outline:
        return 0
    idx = _CornerIndex(walls)
    for w in walls:                                   # 1. weld the corners
        for attr in ("p1", "p2"):
            anchor = idx.anchor.get(idx.of.get((id(w), attr)))
            if anchor is not None and w.end_vertex(attr) is not anchor:
                w.set_end_vertex(attr, anchor)
    shared = 0
    for e in room.outline:                            # 2. adopt them
        anchor = idx.vertex_at(e.p, room.floor)
        if anchor is not None and e.v is not anchor:
            e.v = anchor
            shared += 1
    return shared


class RoomItem(QGraphicsItem):
    """A named room: the wall-enclosed region around an anchor point.

    The translucent region, label and dimension arrows paint in scene
    coords (pos stays 0,0).  Only the label text is clickable, so wall
    editing and panning inside the room keep working.  Right-click the
    name for dimensions / properties / rename / delete."""

    def __init__(self, name: str, anchor: QPointF, path: QPainterPath,
                 area_sqft: float, properties=None, corners=None):
        super().__init__()
        self.name = name
        self.floor = active_floor()             # active floor (load overrides)
        self.anchor = QPointF(anchor)
        self.label_offset = QPointF(0.0, 0.0)   # label drag, relative to anchor
        self._dragging_label = False
        self._label_moved = False        # D53(b): distinguishes ctrl-click
        self._was_selected = False       #         from ctrl-drag at release
        self._toggled_on_press = False   # a modified click owns its release
        # geometry FALLBACKS, used only by a room with no outline (a legacy
        # import whose corners never traced).  A room that HAS an outline
        # derives both -- see the `path` / `area_sqft` properties.
        self._path = QPainterPath(path)
        self._area_sqft = float(area_sqft)
        self._derived = None             # (corner key, path, area) memo
        self.outline = []                # list[OutlineEdge]; corners derives
        self.corners = corners
        self.walls = []                  # WallItems this room owns (edge loop)
        # placement (P4.2): whether this room participates in the shared wall
        # network. A "placed" room is bound into the plan; a "floating" room is
        # genuinely independent -- no shared wall, no shared vertex (I12) --
        # which is what makes it safe to move as one unit. Modelled on the item
        # so the walk emits it and the stash (`_v5_extra`) retires for it.
        self.placement_state = "placed"
        self.extracted_from = None       # level it was extracted from, or None
        self.placement_rotation = 0.0
        # v5 `category` and `nominal_size`, MODELLED at P4.4 (the placement
        # pattern, one field family at a time -- they used to ride the
        # `_v5_extra` stash, which meant a room the app itself created could
        # not have either). `category = None` means "derive it" (the walk's
        # name heuristic); `nominal_size` is the typed design intent of a
        # concept room and is NEVER authoritative -- the outline is.
        self.category = None
        self.nominal_size = None
        # None = NEVER captured (the sentinel matters: a captured-but-EMPTY
        # list must not re-capture at the next drag, or a float parked over
        # another room absorbs its furnishings -- the P4.3+ steal). Captured
        # at extract / shuffle-ON; carried by _translate.
        self._floating_furnishings = None
        self._drag_autofloat = False     # this drag auto-extracted the room
        self._moving_room = False        # drag-the-name moves the whole room
        self._room_grab = QPointF(0.0, 0.0)
        self.show_dims = False
        self.properties = dict(DEFAULT_ROOM_PROPS)
        if properties:
            self.properties.update(properties)
        # geometry never lives in `properties` (P3.2): the schema calls that bag
        # "Schedule data only. NO geometry" and explicitly forbids the key. It is
        # re-derived from the outline for the legacy v4 export, and nowhere else.
        self.properties.pop("perimeter_corners", None)
        self._font = QFont(FONT_FAMILY)
        self._font.setPixelSize(14)       # 14" tall text reads well at plan scale
        self._sub_font = QFont(FONT_FAMILY)
        self._sub_font.setPixelSize(9)
        # cache per-paint helpers: fonts are fixed, so their metrics and the
        # fixed-width boundary stroker never need rebuilding each paint (P0.6)
        self._font_metrics = QFontMetricsF(self._font)
        self._sub_font_metrics = QFontMetricsF(self._sub_font)
        self._boundary_stroker = QPainterPathStroker()
        self._boundary_stroker.setWidth(3.0 * EXTERIOR_T)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        # above the walls: the fill only covers floor space (it stops at
        # the wall faces) and the perimeter dashes must paint OVER the walls
        self.setZValue(4)

    # -- data ------------------------------------------------------------------
    def set_region(self, path: QPainterPath, area_sqft: float, corners=None):
        """Replace the room's geometry.  `path`/`area_sqft` are kept only as
        the no-outline fallback: with an outline present both DERIVE from it."""
        self.prepareGeometryChange()
        self._path = QPainterPath(path)
        self._area_sqft = float(area_sqft)
        self.corners = corners
        self.update()

    # -- derived geometry (P3.5) -----------------------------------------------
    def _derive(self):
        """(path, area) off the outline, memoized on the corner COORDINATES.

        Keyed on coordinates and not on vertex identity: `relocated_to` returns
        a NEW `Vertex` for a moved corner, so an id-keyed memo would be stale in
        exactly the case that matters, and a vertex is never mutated in place so
        equal coordinates really do mean equal geometry."""
        pts = [e.v.point() for e in self.outline]
        key = tuple((p.x(), p.y()) for p in pts)
        memo = self._derived
        if memo is None or memo[0] != key:
            memo = self._derived = (key, room_path_from_corners(pts),
                                    poly_area_sqft(pts))
        return memo

    @property
    def path(self) -> QPainterPath:
        """The room's region, DERIVED from the outline (P3.5).

        A wall move relocates the corner vertices the outline holds, so the
        region follows with nothing to recompute it -- which is what let
        `refresh_rooms` go. `_path` survives as the fallback for an outline-less
        room (a legacy import whose corners never traced) and for nothing
        else."""
        return self._derive()[1] if self.outline else self._path

    @property
    def area_sqft(self) -> float:
        """Area inside the outline, on the same centreline basis the stored
        document uses (`settings.area_basis`).  Derived for the same reason
        `path` is: the number a wall move changes must not need a re-detection
        pass to notice."""
        return self._derive()[2] if self.outline else self._area_sqft

    # -- outline (P3.2) --------------------------------------------------------
    @property
    def corners(self):
        """The perimeter corners, DERIVED from the outline. `None` (not `[]`)
        when there is no outline, because the whole codebase tests `if
        room.corners:` and distinguishes the two."""
        return [e.p for e in self.outline] if self.outline else None

    @corners.setter
    def corners(self, pts):
        """Rebuild the outline from a corner loop. Wall references survive a
        same-length replacement -- a group move or a nudge translates every
        corner but keeps the same edges -- and are dropped when the loop
        changes shape, for `bind_room_walls` to repopulate.

        A list of `OutlineEdge`s is ADOPTED WHOLE (P3.5): `detect_room` now
        returns edges that already know their wall, and rebuilding points out
        of them only to look the same walls up again would throw away the one
        thing the face walk knows that a search has to guess."""
        if not pts:
            self.outline = []
            return
        if isinstance(pts[0], OutlineEdge):
            self.outline = list(pts)
            return
        old = self.outline
        keep = len(old) == len(pts)
        self.outline = [OutlineEdge(c, old[i].wall if keep else None)
                        for i, c in enumerate(pts)]

    def export_properties(self) -> dict:
        """`properties` as the LEGACY v4 export wants them: the schedule data
        plus `perimeter_corners` re-derived from the outline, at the same 2dp
        rounding the old live mirror used, so the export stays byte-compatible.

        The mirror is gone (P3.2) -- this is the one place the key is produced,
        at serialization time, rather than shadowed on every geometry change."""
        out = dict(self.properties)
        out.pop("perimeter_corners", None)
        if self.outline:
            out["perimeter_corners"] = [[round(e.p.x(), 2), round(e.p.y(), 2)]
                                        for e in self.outline]
        return out

    def interior_rect(self) -> QRectF:
        return self.path.boundingRect()

    def perimeter_in(self) -> float:
        if self.corners:
            n = len(self.corners)
            return sum(QLineF(self.corners[i], self.corners[(i + 1) % n]).length()
                       for i in range(n))
        poly = self.path.toFillPolygon()
        return sum(QLineF(poly[i], poly[i + 1]).length()
                   for i in range(poly.size() - 1))

    def _boundary_band(self) -> QPainterPath:
        # wide enough to safely contain the wall centrelines: the flood
        # region edge sits up to t/2 + one raster cell from a centreline,
        # and a point exactly on the stroke edge tests as outside
        return self._boundary_stroker.createStroke(self.path)

    def bounding_walls(self):
        """Walls whose body touches this room's boundary."""
        sc = self.scene()
        if sc is None:
            return []
        band = self._boundary_band()
        return [it for it in sc.items()
                if isinstance(it, WallItem) and it._hit.intersects(band)]

    def interior_walls(self):
        """Real walls that lie wholly inside this room (partitions etc.) -- not
        part of its perimeter band."""
        sc = self.scene()
        if sc is None or self.path.isEmpty():
            return []
        band = self._boundary_band()
        return [it for it in sc.items()
                if isinstance(it, WallItem)
                and not it._hit.intersects(band)
                and self.path.contains(it.p1) and self.path.contains(it.p2)]

    # -- owned walls (the room's edge loop) ----------------------------------
    def bind_wall(self, w):
        """Add this room to wall `w`'s set of bordering rooms.  A wall may be
        SHARED by several rooms (a coalesced party wall borders both), so this
        does not steal `w` from anyone -- it just adds the association."""
        if self not in w.rooms:
            w.rooms.append(self)
        if w not in self.walls:
            self.walls.append(w)

    def unbind_wall(self, w):
        """Detach this room from wall `w`.  Leaves `w` in the scene -- a shared
        wall survives for the other rooms that still border it."""
        if self in w.rooms:
            w.rooms.remove(self)
        if w in self.walls:
            self.walls.remove(w)

    def clear_walls(self):
        for w in list(self.walls):
            self.unbind_wall(w)

    def open_edges(self):
        """Outline edges no built wall actually covers.

        Two ways an edge is open, and P3.5 unified them: it names no wall at
        all (the v5 `wall: null`), or it names one that no longer SPANS it --
        a corner dragged away leaves the wall short of the edge it backs.
        Before P3.5 the second case was represented by interposing a dashed
        placeholder item, so "is this side open?" was answered by looking for
        an object; it is now answered from the outline, which is where the
        document has always answered it (`bridge._rooms_of` emits exactly
        these as open edges). The placeholder class went at P3.7, and the
        dashed cue is drawn from these edges by `_paint_open_edges`."""
        corners = self.corners or []
        n = len(corners)
        return [e for i, e in enumerate(self.outline)
                if e.wall is None or e.wall.scene() is None
                or not _wall_spans_segment(e.wall, corners[i],
                                           corners[(i + 1) % n])]

    def open_edge_segments(self):
        """`[(a, b)]` in item coordinates for every open edge -- the paint-side
        form of `open_edges()`.

        Edge `i` of the outline spans corner `i` to corner `i+1`, and the
        corners ARE the walls' own vertices, so these segments track a drag
        with nothing to recompute them."""
        corners = self.corners or []
        n = len(corners)
        if n < 2:
            return []
        opens = {id(e) for e in self.open_edges()}
        return [(corners[i], corners[(i + 1) % n])
                for i, e in enumerate(self.outline) if id(e) in opens]

    def _paint_open_edges(self, painter, option, ghost):
        """Draw a vacated side dashed (P3.7).

        The cue is drawn FROM THE OUTLINE, which is the whole point: an open
        side used to be an ITEM -- a dashed placeholder the binder interposed --
        so the scene carried a second representation of something the document
        already said (`wall: null`). The fact and the cue now come from one
        place, and the pen matches the item's exactly (same colour, same dash,
        same lod-scaled width) so this closes the P3.5 regression as the SAME
        cue rather than a different one.

        RENDER-ONLY, and deliberately: an open edge is the ABSENCE of a wall.
        Interacting with an absence means drawing a wall there (the draw tool
        owns that) or moving the room (the room owns that), so there is no
        selection or drag control to implement -- which is why the old
        `test_open_wall_is_editable` was deleted rather than rewritten. If a
        later task needs open edges to be hit-testable, P4.2 (extract / join)
        is the one that would, and it specs it."""
        segs = self.open_edge_segments()
        if not segs:
            return
        lod = max(option.levelOfDetailFromTransform(painter.worldTransform()),
                  1e-6)
        col = FLOOR_GHOST if ghost else QColor(90, 120, 170)
        painter.setPen(QPen(col, max(1.2, 1.6 / lod), Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for a, b in segs:
            painter.drawLine(a, b)

    def room_openings(self):
        return [op for w in self.walls for op in w.openings]

    def raise_to_front(self):
        """Bring this room and its owned walls/openings above every other
        room (uses a running max-z on the window; z is not serialized)."""
        win = None
        v = self._view()
        if v is not None:
            win = getattr(v, "win", None)
        if win is None or not hasattr(win, "_z_top"):
            return
        win._z_top += 1
        order = win._z_top * 10
        # THE BAND AND THE WITHIN-FLOOR ORDER ARE DIFFERENT QUANTITIES, and z
        # carries both: `levels._apply_floor_stacking` rides the floor band on
        # as a DELTA precisely so this running max keeps working. Assigning
        # `order` alone would drop the band -- and a room raised on a ghost
        # floor would paint OVER the floor being edited, leaving `_floor_band`
        # stale so the next re-band added the band again on top of the escaped
        # value. Re-base into this room's own band instead (defect 11).
        band = getattr(self, "_floor_band", 0.0)
        base = order + band
        # the translucent fill + label sit at `base` (above OTHER rooms); the
        # walls/openings sit ABOVE the fill so a wall is never hidden under its
        # own room tint and a 'Bring to front' is not undone on the next click
        self.setZValue(base)
        for w in self.walls:
            # an unlocked wall sits just above its siblings so corner clicks
            # at a shared corner grab IT (to edit) rather than a locked neighbour
            w.setZValue(base + 5 if w._corners_unlocked else base + 4)
        for op in self.room_openings():
            # an opening is a CHILD of its wall, so its z is relative to that
            # wall and the band must NOT be applied here -- a banded child
            # would sink behind the very wall it is cut into.
            op.setZValue(order + 6)

    def opening_stats(self):
        """(window count, window glazing sq ft, door count) on this
        room's bounding walls, counting only openings that sit on the
        stretch of wall actually facing the room."""
        band = self._boundary_band()
        wins, win_area, doors = 0, 0.0, 0
        for wall in self.bounding_walls():
            for op in wall.openings:
                if not band.contains(wall.point_at(op.s)):
                    continue
                if op.kind == "window":
                    wins += 1
                    win_area += op.width * op.height / 144.0
                else:
                    doors += 1
        return wins, win_area, doors

    # editable properties, in display order, for the inventory listing
    PROP_LABELS = [
        ("room_type", "Room type"),
        ("ceiling_height_in", "Ceiling height"),
        ("ceiling_type", "Ceiling type"),
        ("floor_finish", "Floor finish"),
        ("wall_finish", "Wall finish"),
        ("baseboard", "Baseboard / trim"),
        ("crown_molding", "Crown molding"),
        ("hvac", "Heating / cooling"),
        ("electrical", "Electrical"),
        ("notes", "Notes"),
    ]

    def inventory_rows(self) -> list:
        """Two-column (name, value/quantity) rows describing the room:
        its properties, then every item in it — furnishings whose centre
        sits inside the room plus the doors/windows on its walls."""
        from floorplanner.items import FurnishingItem  # late (cycle)

        def clean(v) -> str:
            return " ".join(str(v).split())     # no tabs/newlines in cells

        rows = [("Room", self.name), ("", ""), ("Property", "Value"),
                ("Area (sq ft)", f"{self.area_sqft:.1f}")]
        r = self.interior_rect()
        rows.append(("Interior width", fmt_ftin(r.width())))
        rows.append(("Interior length", fmt_ftin(r.height())))
        rows.append(("Perimeter", fmt_ftin(self.perimeter_in())))
        wins, win_area, doors = self.opening_stats()
        rows.append(("Window glazing (sq ft)", f"{win_area:.1f}"))
        for key, label in self.PROP_LABELS:
            v = self.properties.get(key, "")
            if key == "ceiling_height_in":
                v = fmt_ftin(float(v or 0))
            elif key == "crown_molding":
                v = "Yes" if v else "No"
            rows.append((label, clean(v)))

        counts = {}
        sc = self.scene()
        if sc is not None:
            for it in sc.items():
                if isinstance(it, FurnishingItem) and \
                        self.path.contains(it.pos()):
                    counts[it.name] = counts.get(it.name, 0) + 1
        band = self._boundary_band()
        for wall in self.bounding_walls():
            for op in wall.openings:
                if not band.contains(wall.point_at(op.s)):
                    continue
                if op.kind == "window":
                    name = f'Window {op.width:g}" × {op.height:g}"'
                else:
                    name = (f'Door {op.width:g}" × {op.height:g}" '
                            f'({op.door_type})')
                counts[name] = counts.get(name, 0) + 1

        rows += [("", ""), ("Item", "Quantity")]
        rows += [(n, str(q)) for n, q in sorted(counts.items())]
        return rows

    def inventory_text(self) -> str:
        """The inventory as tab-separated text, ready for Excel."""
        return "\n".join(f"{a}\t{b}" for a, b in self.inventory_rows())

    # -- QGraphicsItem -----------------------------------------------------------
    def itemChange(self, change, value):
        # when removed from the scene, release every wall this room borders so
        # no WallItem.rooms keeps a reference to a deleted room (mirrors
        # WallItem.itemChange, walls.py:496-504, with the same sip.isdeleted guard)
        if (change == QGraphicsItem.GraphicsItemChange.ItemSceneChange
                and value is None and self.walls):
            for w in list(self.walls):
                if not sip.isdeleted(w):
                    self.unbind_wall(w)
        return super().itemChange(change, value)

    def _outranked_at(self, scene_pos, item_pos):
        """The item that OUTRANKS this room at a point, or None.

        ONE RULE FOR BOTH VIRTUALS, and that is the whole point of its being a
        method rather than two inline blocks. `mousePressEvent` and
        `contextMenuEvent` are SEPARATE Qt deliveries, each routed to the
        topmost item BY Z. With the region in `shape()` a room that
        `raise_to_front` has lifted above `WALL_Z` swallows that wall's events
        -- and if the decline lived in one virtual and not the other,
        left-click and right-click would resolve DIFFERENTLY. That divergence
        presents as "right-click sometimes picks the wrong thing" long after
        anyone remembers this pass, so both routes ask here.

        THE LABEL IS EXEMPT: it is the room's own handle and routinely sits
        over its walls, so an event there belongs to the room whatever is
        underneath.

        ASKS THE WAY QT ASKS -- through the view, with a 1x1 PIXEL RECT. An
        exact scene point lands a fraction off a wall's edge and reports the
        wall absent; measured, that made this check silently never fire.
        """
        if self._label_rect().contains(item_pos):
            return None
        sc = self.scene()
        if sc is None:
            return None
        from floorplanner.items import best_by_priority   # late: higher layer
        v = self._view()
        cands = (v.items(v.mapFromScene(scene_pos)) if v is not None
                 else sc.items(scene_pos))
        best = best_by_priority(cands)
        return None if best is self or best is None else best

    def _paint_selection_handles(self, painter):
        """Square handles at the room's corners -- the second half of D53's
        solid selection channel, and the half that survives a zoom-out where a
        2 px stroke starts to look like any other line.

        Sized in DEVICE pixels off the painter's own transform, so they stay
        grabbable-looking at any zoom (same reasoning as `FurnishingItem`'s
        rotator handle, which reads the view scale for the same purpose).
        """
        pts = self.corners or [self.path.pointAtPercent(t / 8.0)
                               for t in range(8)]
        if not pts:
            return
        scale = max(abs(painter.transform().m11()), 1e-6)
        h = 3.0 / scale                  # half-side, ~3 device px
        painter.setPen(QPen(QColor(0, 110, 255), 0))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        for c in pts:
            painter.drawRect(QRectF(c.x() - h, c.y() - h, h * 2, h * 2))

    def _label_centre(self) -> QPointF:
        return QPointF(self.anchor.x() + self.label_offset.x(),
                       self.anchor.y() + self.label_offset.y())

    def _label_rect(self) -> QRectF:
        fm = self._font_metrics
        w = max(fm.horizontalAdvance(self.name), 48.0) + 10.0
        h = fm.height() + 13.0
        c = self._label_centre()
        return QRectF(c.x() - w / 2, c.y() - h / 2, w, h)

    def boundingRect(self) -> QRectF:
        r = self.path.boundingRect().united(self._label_rect())
        if self.corners:
            r = r.united(QPolygonF(self.corners).boundingRect())
        return r.adjusted(-24, -24, 24, 24)

    def shape(self) -> QPainterPath:
        """The REGION plus the label -- D53, widened 2026-08-08 at A1b.

        It returned only the label rect, which made the largest visible object
        in the plan a click-through hole: `PlanView` read `itemAt(...) is None`
        as "blank canvas", so pressing a room's fill panned and CLEARED the
        selection. The room was reachable only by its label.

        The label rect stays in the shape: it is the drag handle, and
        `label_offset` can carry it outside the outline.

        WINDING fill rule, deliberately. Two sub-paths under the default
        odd-even rule would turn their INTERSECTION into a hole -- so a label
        sitting over its own room would punch out exactly the middle of the
        region, which is where people click.

        THIS LINE IS ONLY SAFE BECAUSE HIT RESOLUTION NO LONGER READS Z.
        `items.hit_target` ranks a room LAST, so a furnishing (z 3, under the
        room's 4 on purpose) or a wall inside the room still wins its own
        clicks. Widen this while Qt's topmost-by-z answer still decides and
        every furnishing in the plan becomes unclickable.
        """
        p = QPainterPath()
        p.setFillRule(Qt.FillRule.WindingFill)
        p.addPath(self.path)
        p.addRect(self._label_rect())
        return p

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        ghost = floor_display_mode(self.floor) != "active"
        painter.setPen(Qt.PenStyle.NoPen)
        if ghost:                            # non-active floor: faint gray fill,
            painter.setBrush(QBrush(QColor(176, 176, 176, 18)))   # gray label
            painter.drawPath(self.path)
            r = self._label_rect()
            painter.setFont(self._font)
            painter.setPen(QPen(FLOOR_GHOST, 0))
            painter.drawText(r, Qt.AlignmentFlag.AlignHCenter
                             | Qt.AlignmentFlag.AlignTop, self.name)
            self._paint_open_edges(painter, option, ghost=True)
            return
        floating = self.placement_state == "floating"
        # a floating room reads distinctly -- warm fill + dashed boundary --
        # so "extracted, not yet joined" is visible at a glance (P4.2)
        painter.setBrush(QBrush(QColor(255, 170, 60, 34) if floating
                                else QColor(120, 170, 255, 26)))
        painter.drawPath(self.path)
        if floating:
            painter.setPen(QPen(QColor(216, 130, 26), 0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self.path)
            painter.setPen(Qt.PenStyle.NoPen)
        self._paint_open_edges(painter, option, ghost=False)
        if self.isSelected():
            # D53 CONSTRAINT 3: SELECTION AND FLOATING MUST NOT SHARE A VISUAL
            # CHANNEL. A floating room already paints a DASHED orange boundary
            # (just above), and dashed carries a third meaning already -- an
            # open edge, which over a real wall is the fault signature A1's
            # manual check looks for at item 5. Selection used to be a second
            # dash on the very same path, in blue, which on a floating room is
            # two dashes on one shape.
            #
            # So selection is SOLID and additive: a stronger fill tint, a
            # thicker solid stroke, and square corner handles. Floating-ness is
            # a property of the ROOM; selection is a property of the VIEW; they
            # now read as different things rather than as two colours of the
            # same thing.
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0, 122, 255, 30)))
            painter.drawPath(self.path)
            pen = QPen(QColor(0, 110, 255), 2.0, Qt.PenStyle.SolidLine)
            pen.setCosmetic(True)        # 2 device px, so it reads at any zoom
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self.path)
            self._paint_selection_handles(painter)

        r = self._label_rect()
        painter.setFont(self._font)
        painter.setPen(QPen(QColor(40, 40, 70), 0))
        painter.drawText(r, Qt.AlignmentFlag.AlignHCenter
                         | Qt.AlignmentFlag.AlignTop, self.name)
        painter.setFont(self._sub_font)
        painter.setPen(QPen(QColor(115, 115, 135), 0))
        painter.drawText(r, Qt.AlignmentFlag.AlignHCenter
                         | Qt.AlignmentFlag.AlignBottom,
                         f"{self.area_sqft:.0f} sq ft"
                         + (" (floating)" if floating else ""))
        if self.show_dims:
            self._paint_dims(painter)

    def _paint_dims(self, painter):
        """Double-headed arrows along every wall edge enclosing the room.
        Falls back to width/length arrows when no perimeter was traced."""
        col = QColor(178, 58, 40)
        painter.setPen(QPen(col, 0))
        painter.setBrush(QBrush(col))
        painter.setFont(self._sub_font)
        fm = self._sub_font_metrics

        if self.corners:
            n = len(self.corners)
            edges = []
            for i in range(n):
                a, b = self.corners[i], self.corners[(i + 1) % n]
                d = QLineF(a, b)
                length = d.length()
                if length < 18:
                    continue
                edges.append((a, b, length, d.dx() / length, d.dy() / length))
            shown = []
            for edge in edges:
                _, _, length, ux, uy = edge
                # opposite walls (anti-parallel) of equal length are
                # dimensioned only once
                if any(ux * vx + uy * vy < -0.999 and abs(length - vlen) < 1.0
                       for (_, _, vlen, vx, vy) in shown):
                    continue
                shown.append(edge)
            for a, b, length, ux, uy in shown:
                nx_, ny_ = -uy, ux        # room interior is left of the edge
                off = 14.0
                pa = QPointF(a.x() + ux * 4 + nx_ * off,
                             a.y() + uy * 4 + ny_ * off)
                pb = QPointF(b.x() - ux * 4 + nx_ * off,
                             b.y() - uy * 4 + ny_ * off)
                self._arrow(painter, pa, pb)
                text = fmt_ftin(length)
                ang = math.degrees(math.atan2(uy, ux))
                if ang > 90.0 or ang <= -90.0:
                    ang -= 180.0          # keep text upright
                painter.save()
                painter.translate(
                    QPointF((a.x() + b.x()) / 2 + nx_ * (off + 6),
                            (a.y() + b.y()) / 2 + ny_ * (off + 6)))
                painter.rotate(ang)
                painter.drawText(
                    QPointF(-fm.horizontalAdvance(text) / 2, 3), text)
                painter.restore()
            return

        r = self.interior_rect()
        if r.width() < 12 or r.height() < 12:
            return
        lc = self._label_centre()
        y = r.center().y()                # keep clear of the name label
        if abs(y - lc.y()) < 22:
            y = min(r.bottom() - 8, lc.y() + 26)
        self._arrow(painter, QPointF(r.left() + 1, y), QPointF(r.right() - 1, y))
        text = fmt_ftin(r.width())
        painter.drawText(QPointF(r.center().x() - fm.horizontalAdvance(text) / 2,
                                 y - 3), text)

        x = r.center().x()
        if abs(x - lc.x()) < 50:
            x = max(r.left() + 10, lc.x() - 60)
        self._arrow(painter, QPointF(x, r.top() + 1), QPointF(x, r.bottom() - 1))
        text = fmt_ftin(r.height())
        painter.save()
        painter.translate(x - 3, r.center().y() + fm.horizontalAdvance(text) / 2)
        painter.rotate(-90)
        painter.drawText(QPointF(0, 0), text)
        painter.restore()

    @staticmethod
    def _arrow(painter, a: QPointF, b: QPointF):
        painter.drawLine(a, b)
        d = QLineF(a, b)
        if d.length() < 1e-6:
            return
        ux, uy = d.dx() / d.length(), d.dy() / d.length()
        nx, ny = -uy, ux
        hl, hw = 7.0, 2.6                 # arrowhead length / half-width
        for tip, s in ((a, 1.0), (b, -1.0)):
            bx, by = tip.x() + ux * hl * s, tip.y() + uy * hl * s
            painter.drawPolygon(QPolygonF([
                tip,
                QPointF(bx + nx * hw, by + ny * hw),
                QPointF(bx - nx * hw, by - ny * hw)]))

    # -- interaction -------------------------------------------------------------
    def _view(self):
        sc = self.scene()
        return sc.views()[0] if sc and sc.views() else None

    def _rename(self):
        name, ok = QInputDialog.getText(self._view(), "Room name", "Name:",
                                        text=self.name)
        if ok and name.strip():
            self.prepareGeometryChange()
            self.name = unique_room_name(self.scene(), name.strip(),
                                         exclude=self)
            self.update()

    def _translate(self, dx: float, dy: float):
        """Rigidly shift the room's owned walls, openings and region.

        RELOCATES the corners rather than assigning coordinates (P3.5): each
        distinct `Vertex` moves once and every wall end and outline edge holding
        it comes along, so the region follows by construction instead of being
        translated alongside and hoping the two agree. A coordinate assignment
        here would split-on-write -- minting a fresh vertex per wall end and
        leaving the outline behind on the old ones."""
        if not dx and not dy:
            return
        self.prepareGeometryChange()
        holders = [(w, a) for w in self.walls for a in ("p1", "p2")]
        # `old` keeps every vertex alive for the whole pass: the map is keyed by
        # id(), and an id freed mid-pass could be handed back to a new vertex
        old = [w.end_vertex(a) for w, a in holders] + [e.v for e in self.outline]
        moved = {}                            # id(old vertex) -> new vertex
        for v in old:
            if id(v) not in moved:
                moved[id(v)] = v.relocated_to(QPointF(v.x + dx, v.y + dy))
        for w, a in holders:
            w.set_end_vertex(a, moved[id(w.end_vertex(a))])
        for e in self.outline:
            e.v = moved[id(e.v)]
        for w in self.walls:
            w.rebuild()                       # repositions its openings too
        for f in getattr(self, "_floating_furnishings", ()) or ():
            if f.scene() is not None:         # captured at extract (P4.2):
                f.moveBy(dx, dy)              # furnishings ride the float
        if not self.outline:                  # no outline -> the fallback moves
            self._path = QTransform.fromTranslate(dx, dy).map(self._path)
        self.anchor = QPointF(self.anchor.x() + dx, self.anchor.y() + dy)
        self.update()

    def mousePressEvent(self, e):
        # left-drag on the name moves the WHOLE room (walls, doors/windows and
        # region) when the room owns walls; Ctrl-drag keeps the legacy
        # label-only nudge (and unbound rooms always nudge the label).
        on_label = self._label_rect().contains(e.pos())
        mods = e.modifiers()
        shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
        ctrl_mod = bool(mods & Qt.KeyboardModifier.ControlModifier)
        # D53(b): SHIFT-CLICK AND CTRL-CLICK EACH TOGGLE MEMBERSHIP. Users try
        # both, and two modifiers doing one obvious thing is cheaper to learn
        # than one modifier and a wrong guess. Done here rather than left to
        # Qt, which toggles on Ctrl only -- and because the label branch below
        # would otherwise start a room DRAG on a modified click.
        #
        # CTRL ON THE LABEL IS CARVED OUT, because Ctrl+label-DRAG is the
        # legacy label-only nudge and is pinned by
        # `test_room_label_ctrl_drag_nudges_label`. A ctrl press there keeps
        # the nudge; a ctrl press that turns out NOT to have moved toggles at
        # RELEASE instead (see `mouseReleaseEvent`), so the gesture is honoured
        # either way and nothing is taken from the drag.
        # A ROOM DECLINES A PRESS ANOTHER ITEM OUTRANKS (D53). Measured on
        # Patrick's `dragWallFuseStraggler` macro: after two label-drags raise
        # R2 to `_z_top * 10 + band`, line 4's plain `CLICK 338 236` went from
        # selecting the interior column -- and FUSING it, the gesture that
        # macro exists to pin -- to selecting R2. `_outranked_at` is the same
        # rule `contextMenuEvent` uses; see it for why they share one.
        if self._outranked_at(e.scenePos(), e.pos()) is not None:
            e.ignore()                # fall through to the item that outranks
            return
        if e.button() == Qt.MouseButton.LeftButton and (
                shift or (ctrl_mod and not on_label)):
            self.setSelected(not self.isSelected())
            # AND THE RELEASE MUST BE SWALLOWED TOO. `QGraphicsItem`'s default
            # `mouseReleaseEvent` runs its OWN click-selection when the press
            # and release land on the same point: without Ctrl it calls
            # `clearSelection()` and selects this item (so a shift-click would
            # REPLACE the selection instead of adding to it), and with Ctrl it
            # toggles a second time (so a ctrl-click would cancel itself).
            # Measured both ways before this line existed.
            self._toggled_on_press = True
            e.accept()
            return
        if e.button() == Qt.MouseButton.LeftButton and on_label:
            self._was_selected = self.isSelected()
            self._label_moved = False
            self.setSelected(True)
            self.raise_to_front()
            ctrl = ctrl_mod
            self._dragging_label = True
            # `or self.corners`: a WALL-LESS room (a P4.4 concept room, or one
            # whose walls were all deleted) still moves as a unit -- it has an
            # outline to carry and nothing to tear. Before this it fell to the
            # label-only nudge and the region stayed behind.
            if (self.walls or self.corners) and not ctrl:
                self._moving_room = True
                self._room_moved = False      # displacement, not mode (P4.3)
                if self.placement_state != "floating":
                    # P4.2: the label-drag of a PLACED room is extract ->
                    # move -> join through the REAL ops -- the same
                    # observable result the privatize-then-merge_all path
                    # produced, minus the shadow implementation it was
                    from floorplanner.extract import extract_room  # late
                    extract_room(self.scene(), self)
                    if not SETTINGS.get("shuffle", False):
                        # the plain drag moves the room, not its
                        # furnishings -- P4.2's trait, preserved; under
                        # SHUFFLE every dragged room KEEPS its furnishings
                        # (ruled 2026-08-03), so the extract's capture
                        # stands there
                        self._floating_furnishings = []
                    self._drag_autofloat = True
                elif self._floating_furnishings is None:
                    # a room LOADED floating never ran extract: capture
                    # ONCE, at its first drag. `is None`, not falsy -- a
                    # captured-but-empty float parked over another room
                    # must never absorb that room's furnishings at the
                    # next press (the P4.3+ steal). The only re-baseline
                    # is the shuffle-ON toggle.
                    from floorplanner.extract import (  # late: higher layer
                        capture_floating_furnishings)
                    capture_floating_furnishings(self.scene(), self)
                self._room_grab = QPointF(e.scenePos())
            else:
                self._moving_room = False
                c = self._label_centre()
                self._label_grab = QPointF(e.scenePos().x() - c.x(),
                                           e.scenePos().y() - c.y())
            e.accept()
            return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._dragging_label and self._moving_room:
            sp = e.scenePos()
            dx = wall_snap_len(sp.x() - self._room_grab.x())
            dy = wall_snap_len(sp.y() - self._room_grab.y())
            if dx or dy:
                self._translate(dx, dy)
                self._room_moved = True
                self._room_grab = QPointF(self._room_grab.x() + dx,
                                          self._room_grab.y() + dy)
            e.accept()
            return
        if self._dragging_label:
            self._label_moved = True          # a real nudge, not a ctrl-click
            self.prepareGeometryChange()
            nx = e.scenePos().x() - self._label_grab.x()
            ny = e.scenePos().y() - self._label_grab.y()
            self.label_offset = QPointF(nx - self.anchor.x(),
                                        ny - self.anchor.y())
            self.update()
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if getattr(self, "_toggled_on_press", False):
            self._toggled_on_press = False      # see mousePressEvent
            e.accept()
            return
        if self._dragging_label:
            # D53(b), the carved-out half: a CTRL press on the label keeps the
            # legacy nudge, so the toggle it also owes the user is settled here
            # -- if the label never actually moved, this was a ctrl-CLICK and
            # it toggles, restoring whatever the press's unconditional
            # `setSelected(True)` overwrote.
            if (e.modifiers() & Qt.KeyboardModifier.ControlModifier
                    and not getattr(self, "_moving_room", False)
                    and not getattr(self, "_label_moved", True)):
                self._dragging_label = False
                self.setSelected(not getattr(self, "_was_selected", False))
                e.accept()
                return
            moved, self._dragging_label, self._moving_room = (
                self._moving_room, False, False)
            sc = self.scene()
            if getattr(self, "_drag_autofloat", False):
                # the drag owns this float (a placed room's label-drag is
                # extract -> move -> join, P4.2): it ends PLACED whether the
                # mouse moved or not -- a click must not leave a room afloat.
                # UNDER SHUFFLE (P4.3) a room that actually MOVED stays
                # floating -- "leaving shuffle joins nothing automatically",
                # and the floating paint cue is the signal; join is explicit
                # (right-click > Join room into plan). A click that never
                # moved still ends placed, exactly as P4.2 ruled.
                self._drag_autofloat = False
                if sc is not None:
                    if (SETTINGS.get("shuffle", False)
                            and getattr(self, "_room_moved", False)):
                        rebuild_all_walls(sc)
                    else:
                        from floorplanner.extract import join_room  # late
                        join_room(sc, self)
            elif moved and sc is not None:
                # an explicitly floating room: the move is CLOSED (P4.2,
                # section 4) -- nothing merges, welds or binds until an
                # explicit Join
                rebuild_all_walls(sc)
            if moved:
                self.raise_to_front()
            e.accept()
            return
        super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        self._rename()
        e.accept()

    def contextMenuEvent(self, e):
        # THE SAME DECLINE RULE AS `mousePressEvent`, through the same helper
        # (D53, ruled 2026-08-08). `contextMenuEvent` is a SEPARATE Qt virtual
        # with its own delivery, also routed by z -- so without this, a room
        # lifted by `raise_to_front` would answer a right-click meant for a
        # wall inside it, while the LEFT-click on that same point resolved
        # correctly. One rule, both routes, or they drift apart.
        if self._outranked_at(e.scenePos(), e.pos()) is not None:
            e.ignore()
            return
        from floorplanner.dialogs import (  # late: dialogs imports rooms at top
            RoomInventoryDialog, RoomPropertiesDialog)  # noqa: F401
        menu = QMenu()
        a_dims = menu.addAction("Show dimensions")
        a_dims.setCheckable(True)
        a_dims.setChecked(self.show_dims)
        a_props = menu.addAction("Properties…")
        a_inv = menu.addAction("Inventory…")
        a_ren = menu.addAction("Rename…")
        a_copy = menu.addAction("Copy room")
        a_extract = a_join = None
        if self.placement_state == "floating":
            a_join = menu.addAction("Join room into plan")
        elif self.walls:
            a_extract = menu.addAction("Extract room (float it)")
        menu.addSeparator()
        a_del = menu.addAction("Delete room")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        if chosen is a_dims:
            self.show_dims = not self.show_dims
            self.update()
        elif chosen is a_copy:
            v = self._view()
            if v is not None:
                # P4.4: the clipboard holds a one-room TEMPLATE DOCUMENT --
                # the same payload File > Save template room writes, so copy/
                # paste and save/load template are one mechanism with a
                # clipboard or a file in the middle
                v.win.room_clipboard = v.win.room_template(self)
                v.win.status(f"Copied room '{self.name}' — with the Room "
                             "Name tool active, right-click a blank spot "
                             "to paste.")
        elif a_extract is not None and chosen is a_extract:
            from floorplanner.extract import extract_room  # late: higher layer
            extract_room(self.scene(), self)
            v = self._view()
            if v is not None:
                v.win.status(f"Extracted '{self.name}' — drag it by its name, "
                             "then right-click it to join it back into the "
                             "plan.")
        elif a_join is not None and chosen is a_join:
            from floorplanner.extract import join_room  # late: higher layer
            join_room(self.scene(), self)
            v = self._view()
            if v is not None:
                v.win.status(f"Joined '{self.name}' into the plan.")
        elif chosen is a_props:
            dlg = RoomPropertiesDialog(self, self._view())
            if dlg.exec() == QDialog.DialogCode.Accepted:
                dlg.apply()
                self.prepareGeometryChange()
                self.update()
                v = self._view()
                if v is not None:
                    v.win._update_totals()    # include / name may have changed
        elif chosen is a_inv:
            RoomInventoryDialog(self, self._view()).exec()
        elif chosen is a_ren:
            self._rename()
        elif chosen is a_del and self.scene() is not None:
            self.clear_walls()           # release walls (they stay on canvas)
            self.scene().removeItem(self)
        e.accept()


def _wall_endpoints_match(w, a: QPointF, b: QPointF, tol: float = 1.0) -> bool:
    return ((QLineF(w.p1, a).length() <= tol and QLineF(w.p2, b).length() <= tol)
            or (QLineF(w.p1, b).length() <= tol
                and QLineF(w.p2, a).length() <= tol))


def _wall_spans_segment(w, a: QPointF, b: QPointF) -> bool:
    """True when wall `w`'s body runs along and contains the segment a->b
    (both ends project within the wall's length, ~collinear with it)."""
    u, length = w.unit(), w.length()
    if length < 1e-6:
        return False
    for p in (a, b):
        vx, vy = p.x() - w.p1.x(), p.y() - w.p1.y()
        s = vx * u.x() + vy * u.y()
        if not (-0.6 <= s <= length + 0.6
                and abs(vy * u.x() - vx * u.y()) <= 1.5):
            return False
    return True


def _edge_wall(scene, a: QPointF, b: QPointF, floor=None):
    """The wall covering the room edge a->b, or None.

    P3.5: the last survivor of `bind_room_walls`'s three-priority search, kept
    for the ONE case the face walk cannot answer -- an outline that came from a
    file rather than from detection, whose edges name no wall. Everything else
    is told which wall covers it by `detect_room`.

    A wall whose ENDS match the edge wins over a longer one that merely runs
    along it (the room's own edge before the party wall carrying it); after
    that the one covering MORE of the edge wins; and among equals the
    geometrically smallest is chosen so the pick is deterministic -- scene item
    order is not, and save/load round-trips depend on it.

    PARTIAL cover counts, which is what makes a reload agree with the live
    scene. A side whose corner was dragged away is backed by a wall that no
    longer spans its edge; the live outline goes on naming that wall (it is
    still that side's wall -- `open_edges` is what reports the shortfall), so a
    binder that demanded full cover would drop it on the way back in and a v4
    round-trip would stop being idempotent."""
    line = QLineF(a, b)
    L = line.length()
    if L < 1e-6:
        return None
    ux, uy = (b.x() - a.x()) / L, (b.y() - a.y()) / L
    best, best_key = None, None
    for w in scene.items():
        # GROUPED WALLS ARE CANDIDATES SINCE P4.5 -- the last of the four
        # exemptions. Its premise was the others': a grouped wall was a COPY
        # lying on the original, so admitting it risked binding a room's edge
        # to a transient duplicate that vanishes on ungroup. Nothing is copied
        # now -- grouping a room puts the room's OWN walls in the group -- so
        # the refusal inverted into "a room may not re-bind to its own wall
        # while that wall is grouped", and the edge read OPEN over a wall that
        # was right there. Measured before the change: 307 of 307 live-wall
        # edges across symmetricP1 / planc1TestV5 / fiveRoomTest could not be
        # recovered by this search once the plan was grouped.
        if (not isinstance(w, WallItem)
                or (floor is not None and w.floor != floor)):
            continue
        ss = []
        for p in (w.p1, w.p2):
            vx, vy = p.x() - a.x(), p.y() - a.y()
            if abs(vy * ux - vx * uy) > 1.5:      # not collinear with the edge
                break
            ss.append(vx * ux + vy * uy)
        if len(ss) != 2:
            continue
        lo, hi = max(0.0, min(ss)), min(L, max(ss))
        if hi - lo < min(MIN_WALL_LEN, L):        # touches, but backs nothing
            continue
        key = (not _wall_endpoints_match(w, a, b), -(hi - lo),
               w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y())
        if best_key is None or key < best_key:
            best, best_key = w, key
    return best


def room_walls(room) -> list:
    """The built walls this room's OUTLINE names, in edge order.

    The single answer to "which walls are this room's?" (P3.5). It used to be
    the parallel `room.walls` list, maintained alongside the outline by the
    binder; the outline's own `wall` references are the authority now, and
    `room.walls` is the association list walls read back (`WallItem.rooms`).
    Falls back to `room.walls` for a room with no outline at all -- a legacy
    import whose corners never traced.

    LIVE WALLS ONLY. An outline edge goes on NAMING a wall that has left the
    scene -- a merge absorbs the wall but does not clear the reference, so
    `e.wall` is a Python object outside the scene, "dead but not absent"
    (measured at P4.5). Handing one back made this predicate lie: a dead wall
    is not a wall this room has, and every consumer either wants a live one or
    re-checks liveness itself. It also had a live consequence once
    `group_selected` began consuming this list (P4.5(2)) -- grouping such a
    room ADOPTED the dead wall, and adoption re-parents it into the scene, so
    a wall the merge had deleted came back. Filtering here fixes it for every
    consumer at once rather than at each call site."""
    seen, out = set(), []
    for e in room.outline:
        w = e.wall
        if (w is not None and w.scene() is not None and id(w) not in seen):
            seen.add(id(w))
            out.append(w)
    if not out:
        out = [w for w in room.walls
               if isinstance(w, WallItem) and w.scene() is not None]
    return out


def room_owns_walls(walls, room) -> bool:
    """True when every built wall the room's outline names is in `walls`, so a
    rigid move of `walls` moves the room's own perimeter and its region/label
    must ride along.

    This is the criterion for MOVING/ROTATING a room with a group (bake/
    rotation): it is deliberately stricter than walls_cover_room() -- a group
    of coincident COPIES (as made when a room-only selection is grouped) does
    NOT own the room's walls, so it must not drag the original room off them.

    REWRITTEN AS AN OUTLINE PREDICATE AT P3.5 rather than deleted: its last
    caller is `GroupItem.bake`, so it lives on, but it now reads the outline
    (via `room_walls`) instead of the parallel bound-wall list the deleted
    binder maintained. Same criterion, one source."""
    own = room_walls(room)
    moving = set(walls)
    return bool(own) and all(w in moving for w in own)


def walls_cover_room(walls, room) -> bool:
    """True when `walls` correspond to `room` -- either they are the room's own
    perimeter (room_owns_walls) or they run along every outline edge (even if
    extra coincident walls also touch the boundary).

    This is the looser ASSOCIATION test (which room does this group enclose?),
    used by group_room() to pick up a grouped/extracted room by its walls even
    when the group holds copies rather than the room's bound walls.  For moving
    a room use room_owns_walls().

    REWRITTEN AS AN OUTLINE PREDICATE AT P3.5, same reasoning as above: the
    loop it walks is `room.outline`, which is the stored perimeter, not a
    freshly traced one that could disagree with it."""
    if room_owns_walls(walls, room):
        return True
    if not room.outline:
        return False
    moving = set(walls)
    corners = room.corners
    n = len(corners)
    for i in range(n):
        a, b = corners[i], corners[(i + 1) % n]
        if not any(_wall_spans_segment(w, a, b) for w in moving):
            return False
    return True


def repair_edge_bindings(scene, room):
    """Re-resolve outline edges whose named wall is WRONG in one of two
    narrow, safe-to-fix ways (P4.2, found by the fiveRoom macros):

    * DEAD -- the wall has left the scene (a merge absorbed it); the edge
      is looked up afresh, partial cover accepted, exactly as a load would.
    * OUTSPANNED -- the wall is alive but does not span the edge, while
      ANOTHER wall FULLY spans it (the fiveRoomDragSplit2 macro seeded
      this at its line 4: an edge bound to a collinear neighbour that
      covers none of it, with the exactly-matching wall right there --
      `_edge_wall`'s partial-cover acceptance had grabbed the wrong
      candidate during an earlier repair). UPGRADE ONLY: the rebind happens
      solely when the candidate fully spans -- a named wall that is
      legitimately short (a detached wall mid-open, a stretch awaiting the
      partial-cover splitter) is never swapped sideways or downgraded.

    Deliberately NARROWER than `bind_room_walls`: an edge whose wall is
    None stays None -- a deliberately opened side must never be silently
    re-closed. Returns the number of edges repaired."""
    if not room.outline or not room.corners:
        return 0
    corners = room.corners
    n = len(corners)
    fixed = 0
    for i, e in enumerate(room.outline):
        if e.wall is None:
            continue
        a, b = corners[i], corners[(i + 1) % n]
        dead = e.wall.scene() is None
        if not dead and _wall_spans_segment(e.wall, a, b):
            continue
        old = e.wall
        cand = (None if QLineF(a, b).length() < MIN_WALL_LEN
                else _edge_wall(scene, a, b, room.floor))
        if dead:
            e.wall = cand
        elif (cand is not None and cand is not old
                and _wall_spans_segment(cand, a, b)):
            e.wall = cand
        else:
            continue
        if old in room.walls and not any(k.wall is old for k in room.outline):
            room.unbind_wall(old)
        if e.wall is not None:
            room.bind_wall(e.wall)
            fixed += 1
    return fixed


# the original, narrower name -- kept callable; the repair grew a second
# case at the fiveRoomDragSplit2 finding and was renamed to say what it does
rebind_dead_edges = repair_edge_bindings


def _corner_path(a, p, b, step, tol_deg):
    """Is the outline STRAIGHT through `p`, and by which comparison?

    Returns `(straight, path)` with `path` in {"exact", "tolerance"}.

    EXACT WHEN EVERY COORDINATE IS ON THE LATTICE, which is Patrick's design
    argument for snap-by-default made operational: three lattice points are
    collinear exactly when an integer cross product is zero, so the test is a
    comparison rather than a tolerance question. The tolerance path is not
    removed -- it is what an ANGLED wall gets, by ruling -- and each dissolve
    reports which path decided it.
    """
    ux, uy = a.x() - p.x(), a.y() - p.y()
    wx, wy = b.x() - p.x(), b.y() - p.y()
    on_lattice = all(abs(c / step - round(c / step)) < 1e-9
                     for c in (a.x(), a.y(), p.x(), p.y(), b.x(), b.y()))
    if on_lattice:
        # integers after scaling: cross == 0 is exact, and dot < 0 keeps it a
        # STRAIGHT-THROUGH corner rather than a zero-width spur tip (dot > 0),
        # which is the distinction the pre-implementation check found the
        # wall-only predicate could not make.
        ia, ib = round(ux / step), round(uy / step)
        ic, idd = round(wx / step), round(wy / step)
        return (ia * idd - ib * ic == 0 and ia * ic + ib * idd < 0), "exact"
    nu = math.hypot(ux, uy) or 1e-9
    nw = math.hypot(wx, wy) or 1e-9
    dot = (ux * wx + uy * wy) / (nu * nw)
    return (dot < -math.cos(math.radians(tol_deg))), "tolerance"


AREA_BOUND_SQFT = 0.005
"""The most area a single dissolve may move, in square feet — ruled 2026‑08‑09,
at half the 2‑dp display resolution.

**"No room's area moves" was never a property of the operation; it was a
property of one plan.** It was validated on `wiscaway2026-08-08`, where the dry
run reports `28 exact / 0 by angle` — the angular path never fired. On
`wiscaway2026-08-09R` it is `24 exact / 60 by angle`, and **dissolving a
NEAR-collinear vertex must change area: that is arithmetic, not a bug.**

So the guarantee is a BOUND, enforced by REFUSAL rather than by avoidance: a
dissolve that would move any holding room by more than this is refused and
counted.

**THE DISPLAY CAVEAT, stated because the arithmetic cannot keep the other
promise.** No positive bound stops a *displayed* figure flipping its last digit:
a value sitting on a rounding boundary moves at any epsilon. `Garage` went
4868.36 → 4868.35 on a **2e‑5** change. **The MODEL is bounded; the display is
not**, and pretending otherwise would be a promise this cannot keep.

**A prediction on the record, to be checked rather than assumed:** the angular
path's share should collapse once grid-snap-by-default lands — Patrick's on-grid
argument predicts it. Re-measure the exact/angle split then."""


def _corner_area_sqft(a, b, c):
    """Area (sq ft) the ring loses by dropping corner `b` — the triangle
    `a,b,c`. Exact: removing one vertex of a polygon changes its area by
    exactly that triangle, so no re-derivation is needed to answer 'how much
    would this move?'."""
    return abs((b.x() - a.x()) * (c.y() - a.y())
               - (c.x() - a.x()) * (b.y() - a.y())) / 2.0 / 144.0


def coalesce_outline_corners(scene, rooms=None, dry_run=True, tol_deg=0.05,
                             area_bound_sqft=AREA_BOUND_SQFT):
    """Dissolve REDUNDANT OUTLINE CORNERS -- a corner the ring runs straight
    through, which no wall needs.

    THE SCOPED FORM IS THE PRIMITIVE. `rooms=None` means every room, so the
    plan-wide pass is this called with everything -- one implementation, two
    callers. A global sweep built first is one nobody dares run inside a
    gesture, and D61's stage 2b needs the scoped form for the leave path.

    WHY THIS EXISTS BESIDE `normalize_walls` RATHER THAN INSIDE IT. Measured on
    Patrick's plan: `normalize_walls` takes the WALL graph from 103 walls / 26
    collinear degree-2 vertices to 81 / 3, idempotently and with every room
    area unchanged -- and leaves the OUTLINES exactly as they were, 159 corners
    of which 69 are redundant, before and after. The wall pass dissolves a
    vertex and the outline goes on naming it: measured at (1062, 684), wall
    degree 2 -> 0 while Dining and KITCHEN still hold the corner. **69, not 26,
    is the size of the complaint**, and this is the half that addresses it.

    THE PREDICATE, as corrected by the pre-implementation check:

      * EVERY room outline holding the corner runs straight through it --
        opposite-directed, not merely collinear. A wall-graph test alone cannot
        see this: an outline's other edge there may be OPEN (`wall: null`), so
        a vertex can be degree-2 collinear among walls while a ring turns 90
        degrees at it. On Patrick's plan that was 3 of 26.
      * no wall NEEDS it -- degree 0, or degree 2 with its two walls
        opposite-directed collinear (which `normalize_walls` will merge).

    Returns a report and, with `dry_run=True`, CHANGES NOTHING. The report is
    the thing Patrick reads before anything is touched.
    """
    from floorplanner.walls import WallItem                   # late: cycle
    if scene is None:
        return {"rooms": {}, "removed": 0, "paths": {"exact": 0, "tolerance": 0},
                "areas": {}, "dry_run": dry_run, "max_area_delta_sqft": 0.0,
                "area_bound_sqft": area_bound_sqft,
                "refused": {"a_wall_needs_it": 0, "a_holder_turns": 0,
                            "triangle": 0, "area_would_move": 0}}
    all_rooms = [i for i in scene.items() if isinstance(i, RoomItem)]
    targets = all_rooms if rooms is None else [r for r in rooms
                                               if isinstance(r, RoomItem)]
    step = float(SETTINGS.get("wall_snap_in", WALL_SNAP_DEFAULT)) or 6.0

    deg, ends = {}, {}
    for w in scene.items():
        if isinstance(w, WallItem):
            for v, p in ((w._v1, w.p1), (w._v2, w.p2)):
                deg.setdefault(id(v), []).append(w)
                # SCOPED BY FLOOR, like every geometry path in this codebase --
                # unscoped, a wall end on the storey above would count as a
                # wall ending at this corner.
                # HONEST NOTE ON WHY IT IS HERE: it was written to explain
                # `roundedMultifloor`, the only two-level plan in the set and
                # the only one where every dissolved corner still comes back.
                # It did NOT explain it -- the result is byte-identical with
                # and without this scoping, on all four plans. It stays because
                # the floor rule is right, not because it fixed anything, and
                # rounded's rebound is still unexplained (D63).
                ends.setdefault(w.floor, []).append((p.x(), p.y()))

    def _ends_at(pt, floor, tol=0.05):
        return sum(1 for x, y in ends.get(floor, ())
                   if math.hypot(x - pt[0], y - pt[1]) <= tol)

    def wall_ok(vid, pt, floor):
        """Does any wall NEED this corner?

        TWO QUESTIONS, and the second was missing until D63. The first is
        whether the walls HOLDING this vertex need it: none, or exactly two
        that are collinear and about to merge. The second is whether any OTHER
        wall ENDS at this coordinate -- a T-junction whose stem is not on the
        run at all, so it holds a different vertex and is invisible to a
        degree count.

        THE DOCUMENT REQUIRES THE SECOND. `design/bridge._walk` emits one
        outline edge per wall (invariant I5), so a room edge crossing a
        T-junction is several edges however few corners the scene holds. Remove
        the corner and the next save puts it straight back.

        MEASURED, and this is what makes it a rule rather than a guess: of the
        corners the save re-inserted, 4/4 on `wiscaway`, 4/4 on the 08-09R
        plan and 16/16 on `roundedMultifloor` had a wall end at them -- while
        of those that stayed removed, 0/33, 0/94 and 1/7 did.
        """
        ws = deg.get(vid, [])
        if _ends_at(pt, floor) != len(ws):
            return False              # a wall ends here that does not hold it
        if not ws:
            return True
        if len(ws) != 2:
            return False
        a, b = ws
        # AND THEY MUST BE ABLE TO MERGE. Two COLLINEAR walls of different
        # type do not fuse -- `merge_wall` is same-type only -- so they stay
        # two walls and I5 still needs an outline edge each. Measured: every
        # corner that survived the wall-end test above and still came back on
        # save was exactly this, a 6" `exterior` meeting a 4.5" `interior`
        # head-on at 90.0 degrees ((1062, 774), (852, 762), (1476, 660) on
        # `wiscaway`). Without this the run merges in the WALL pass or not at
        # all, and "not at all" is a corner the document requires.
        if a.wall_type != b.wall_type:
            return False
        ua = math.atan2(a.p2.y() - a.p1.y(), a.p2.x() - a.p1.x())
        ub = math.atan2(b.p2.y() - b.p1.y(), b.p2.x() - b.p1.x())
        d = abs((ua - ub) % math.pi)
        return min(d, math.pi - d) < math.radians(tol_deg)

    # a corner may be held by SEVERAL rooms; it may only go if every one of
    # them runs straight through it, so the decision is per VERTEX not per room
    holders = {}
    for r in all_rooms:
        for i, e in enumerate(r.outline):
            if e.v is not None:
                holders.setdefault(id(e.v), []).append((r, i))

    doomed, paths = {}, {"exact": 0, "tolerance": 0}
    refused = {"a_wall_needs_it": 0, "a_holder_turns": 0, "triangle": 0,
               "area_would_move": 0}
    worst = 0.0
    for vid, hs in holders.items():
        if not any(r in targets for r, _ in hs):
            continue
        pt, fl = None, None
        for r, i in hs:
            q = r.outline[i].p
            pt, fl = (q.x(), q.y()), getattr(r, "floor", None)
            break
        if not wall_ok(vid, pt, fl):
            refused["a_wall_needs_it"] += 1
            continue
        ok, path, delta = True, "exact", 0.0
        for r, i in hs:
            n = len(r.outline)
            if n < 4:                       # never reduce a ring below a triangle
                ok = False
                refused["triangle"] += 1
                break
            straight, pth = _corner_path(r.outline[(i - 1) % n].p,
                                         r.outline[i].p,
                                         r.outline[(i + 1) % n].p, step, tol_deg)
            if pth == "tolerance":
                path = "tolerance"
            if not straight:
                ok = False
                refused["a_holder_turns"] += 1
                break
            # THE AREA THIS DISSOLVE WOULD MOVE, per holding room. Removing a
            # ring vertex changes the polygon's area by the triangle it cuts
            # off, so the answer is exact and cheap -- no re-derivation needed.
            delta = max(delta, _corner_area_sqft(r.outline[(i - 1) % n].p,
                                                 r.outline[i].p,
                                                 r.outline[(i + 1) % n].p))
        if ok and delta > area_bound_sqft:
            ok = False
            refused["area_would_move"] += 1
        if ok:
            worst = max(worst, delta)
            doomed[vid] = path
            paths[path] += 1

    per_room, areas = {}, {}
    for r in all_rooms:
        n = sum(1 for e in r.outline if e.v is not None and id(e.v) in doomed)
        if n or r in targets:
            per_room[r.name] = {"corners": len(r.outline), "removable": n}
        areas[r.name] = round(r.area_sqft, 2)

    report = {"rooms": per_room, "removed": len(doomed), "paths": paths,
              "areas_before": areas, "dry_run": dry_run,
              "refused": refused, "area_bound_sqft": area_bound_sqft,
              "max_area_delta_sqft": round(worst, 6)}
    if dry_run or not doomed:
        return report

    for r in all_rooms:
        keep = [e for e in r.outline
                if e.v is None or id(e.v) not in doomed]
        if len(keep) != len(r.outline):
            r.prepareGeometryChange()
            r.outline = keep
            r._derived = None               # path/area re-derive from the outline
    report["areas_after"] = {x.name: round(x.area_sqft, 2) for x in all_rooms}
    return report


def split_partially_covered_edges(scene, room, tol=0.75):
    """Split an outline edge at the END of a live wall that covers only PART
    of it (P4.2, mini-gate finding 5 -- Patrick's fiveRoomDragSplit macro).

    A drag that stretches or shrinks a perpendicular wall, or a join that
    lands a room slightly offset, leaves an edge NAMED by a wall that no
    longer spans it. That state is a LATENT TEAR: the next drag moves the
    wall's end vertex and the un-split edge follows at only one corner --
    the diagonal. The cure is structural: the coverage boundary becomes a
    real corner HOLDING THE WALL'S OWN END VERTEX, so later drags carry it
    by construction (and the mixed-corner step logic sees a plain corner
    instead of a hidden seam); the uncovered remainder re-binds to whatever
    actually covers it, or stays honestly open (None). Runs at drag release
    and after a join -- derived-state repair, never a coordinate move.
    Returns the number of splits made."""
    made = 0
    guard = len(room.outline) + 8
    while guard > 0:
        guard -= 1
        corners = room.corners or []
        n = len(corners)
        if n < 3:
            return made
        split = None
        for i, e in enumerate(room.outline):
            w = e.wall
            if w is None or w.scene() is None:
                continue
            a, b = corners[i], corners[(i + 1) % n]
            if _wall_spans_segment(w, a, b):
                continue
            ex, ey = b.x() - a.x(), b.y() - a.y()
            elen = math.hypot(ex, ey)
            if elen < 2.0:
                continue
            ex, ey = ex / elen, ey / elen
            for attr in ("p1", "p2"):
                p = getattr(w, attr)
                s = (p.x() - a.x()) * ex + (p.y() - a.y()) * ey
                perp = abs((p.y() - a.y()) * ex - (p.x() - a.x()) * ey)
                if not (perp <= tol and 1.0 < s < elen - 1.0):
                    continue
                # NEVER split under the deliberate-open workflow: a DETACHED
                # wall (`_corners_unlocked`, set only by
                # `detach_wall_from_room`, cleared at relock) retracted
                # mid-edge must keep its openness DERIVED, so dragging the
                # end back re-closes the gap -- splitting there froze it
                # open (test_closing_gap_refuses_and_relocks caught it).
                # Everything else mid-edge is a structural boundary. (A
                # junction-DEGREE guard was tried first and was wrong: a
                # slid wall can leave a genuinely dangling structural end
                # mid-edge, which the fiveRoomDragSplit2 macro seeded at
                # its line 4 and tore at line 12.)
                if getattr(w, "_corners_unlocked", False):
                    continue
                split = (i, e, w, attr, a, b, p)
                break
            if split is not None:
                break
        if split is None:
            return made
        i, e, w, attr, a, b, p = split
        vp = w.end_vertex(attr)
        uw, lw = w.unit(), w.length()
        sa = (a.x() - w.p1.x()) * uw.x() + (a.y() - w.p1.y()) * uw.y()
        pa = abs((a.y() - w.p1.y()) * uw.x() - (a.x() - w.p1.x()) * uw.y())
        a_covered = pa <= tol and -tol <= sa <= lw + tol
        room.prepareGeometryChange()
        if a_covered:
            # a..p stays with w; the p..b remainder re-binds
            other = _edge_wall(scene, QPointF(p), QPointF(b), room.floor)
            other = None if other is w else other
            room.outline.insert(i + 1, OutlineEdge(vp, other))
        else:
            # a..p re-binds; p..b keeps w
            other = _edge_wall(scene, QPointF(a), QPointF(p), room.floor)
            other = None if other is w else other
            e.wall = other
            room.outline.insert(i + 1, OutlineEdge(vp, w))
        if other is not None:
            room.bind_wall(other)
        made += 1
    return made


def bind_room_walls(scene, room, settle=True):
    """Bind `room` to the wall behind every edge of its STORED outline.

    P3.5 -- AND THE NAME NOW MEANS SOMETHING NARROWER THAN IT DID. This used to
    REBUILD the room's edge loop, and it did so by editing the plan: a
    three-priority search that could synthesize a private duplicate of a party
    wall (`synthesize_room_edge`) or interpose a dashed placeholder item for a
    gap. Asking
    which walls a room owned therefore changed the document, and it ran on
    every `rebuild_all_walls` via `refresh_rooms`.

    It now only ATTACHES. `detect_room` hands each outline edge the wall
    covering it, straight off the face walk, so there is nothing left to search
    for -- except on the one path that has an outline but no wall references: a
    plan loaded from a legacy file, whose corners come from the file and whose
    edges name nothing. `_edge_wall` answers for those, and for nothing else.

    Nothing is created, nothing is deleted, and no coordinate moves. An edge no
    wall covers keeps `wall = None` -- the v5 `wall: null`, which the room
    itself renders dashed (`_paint_open_edges`, P3.7)."""
    if not room.outline:
        return
    corners = room.corners
    n = len(corners)
    room.clear_walls()
    for i, e in enumerate(room.outline):
        if e.wall is None or e.wall.scene() is None:
            a, b = corners[i], corners[(i + 1) % n]
            e.wall = (None if QLineF(a, b).length() < MIN_WALL_LEN
                      else _edge_wall(scene, a, b, room.floor))
        if e.wall is not None:
            room.bind_wall(e.wall)
    # now that every edge knows its wall, make the corners ONE vertex and point
    # the outline at them -- the one place that knows which walls meet where
    share_outline_vertices(room)
    if settle:
        rebuild_all_walls(scene)


def detach_wall_from_room(scene, wall):
    """Unlock `wall`'s corners so the user can drag its endpoints.  The wall
    stays part of the room; pulling a corner away from the neighbouring wall
    opens that side, and the room draws the vacated stretch dashed."""
    if not wall.rooms:
        return
    wall._corners_unlocked = True
    wall.setZValue(wall.zValue() + 1)    # above locked neighbours at corners
    wall.update()


def room_path_from_corners(corners) -> QPainterPath:
    path = QPainterPath()
    path.addPolygon(QPolygonF([QPointF(c) for c in corners]))
    path.closeSubpath()
    return path


def path_area_sqft(path: QPainterPath) -> float:
    poly = path.toFillPolygon()
    pts = [poly[i] for i in range(poly.count())]
    return poly_area_sqft(pts) if len(pts) >= 3 else 0.0


def simplify_corners(poly) -> list:
    """Clean corner list from a boolean-result polygon: drop the closing
    duplicate, merge near-duplicates, and drop collinear points."""
    pts = [QPointF(poly[i]) for i in range(poly.count())]
    if len(pts) > 1 and QLineF(pts[0], pts[-1]).length() < 0.5:
        pts.pop()
    dedup = []
    for p in pts:
        if not dedup or QLineF(dedup[-1], p).length() > 0.5:
            dedup.append(p)
    n = len(dedup)
    if n < 3:
        return dedup
    corners = []
    for i in range(n):
        a, b, c = dedup[(i - 1) % n], dedup[i], dedup[(i + 1) % n]
        cross = ((b.x() - a.x()) * (c.y() - b.y())
                 - (b.y() - a.y()) * (c.x() - b.x()))
        if abs(cross) > 1.0:           # a real corner, not collinear filler
            corners.append(b)
    return corners if len(corners) >= 3 else dedup


def interior_point(poly) -> QPointF:
    """A point strictly inside a (possibly concave) polygon."""
    rule = Qt.FillRule.OddEvenFill
    c = poly.boundingRect().center()
    if poly.containsPoint(c, rule):
        return c
    br = poly.boundingRect()
    for iy in range(1, 12):
        for ix in range(1, 12):
            p = QPointF(br.left() + br.width() * ix / 12.0,
                        br.top() + br.height() * iy / 12.0)
            if poly.containsPoint(p, rule):
                return p
    return c


def room_walled(scene, room) -> bool:
    """True while the room's region is still enclosed by walls -- a flood
    fill from inside it doesn't escape to the canvas edge."""
    pts = []
    if room.corners:
        pts.append(interior_point(QPolygonF(room.corners)))
    pts.append(room.anchor)
    return any(detect_room(scene, p) is not None for p in pts)
