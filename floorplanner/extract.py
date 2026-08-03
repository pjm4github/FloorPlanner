"""Extract / join — rooms as durable movable units (P4.2).

The scene-side implementation of `DESIGN_MODEL_v5.md` §4's operation
semantics. `extract_room` lifts a placed room out of the shared wall network
(`placed → floating`) so it can be moved as one closed unit; `join_room` is
the inverse, welding it back into the plan wherever it now sits. Both are
built ON the existing machinery — the vertex fold, `merge_wall`'s planner,
`split_wall_at`, `bind_room_walls` — rather than beside it, per P3.4 point 1
(one planner, no second definition of merge/split/weld).

This module sits ABOVE `items.py` (it needs `FurnishingItem` — a floating
room carries its furnishings), so `rooms.py`'s context menu reaches it by
late import, the same pattern it already uses for `dialogs`.

I12 — a floating room shares no wall and no vertex with the plan — holds by
construction after `extract_room`: party walls are copied (the original stays
with the neighbour, exactly as §4 requires: the plan keeps every wall it
had), and every vertex an outside wall still touches is replaced with a
private copy before the state flips.
"""
from PyQt6.QtCore import QPointF

from floorplanner.items import FurnishingItem
from floorplanner.rooms import (
    RoomItem, bind_room_walls, rebind_dead_edges, share_outline_vertices,
    split_partially_covered_edges,
)
from floorplanner.vertex import Vertex
from floorplanner.walls import (
    SHARE_TOL, OpeningItem, WallItem, merge_wall, rebuild_all_walls,
    report_doorway_landings, report_opening_failure, share_coincident_ends,
    split_wall_at,
)


def _copy_edge_stretch(scene, room, edge, a: QPointF, b: QPointF):
    """Copy the stretch of `edge.wall` that spans this outline edge (corner
    `a` to corner `b`) into a new private wall for `room`, openings included.
    The original wall keeps its full geometry and stays with its other
    room(s). Returns the copy."""
    w = edge.wall
    u, L = w.unit(), w.length()
    sa = (a.x() - w.p1.x()) * u.x() + (a.y() - w.p1.y()) * u.y()
    sb = (b.x() - w.p1.x()) * u.x() + (b.y() - w.p1.y()) * u.y()
    s0, s1 = max(0.0, min(sa, sb)), min(L, max(sa, sb))
    c = WallItem(w.point_at(s0), w.point_at(s1), w.wall_type)
    c.floor = w.floor
    scene.addItem(c)
    for op in w.openings:
        if not (s0 - 1e-6 <= op.s <= s1 + 1e-6):
            continue
        try:
            nop = OpeningItem(c, op.kind, op.code, op.s - s0)
        except ValueError as exc:
            report_opening_failure(scene, c, op.kind, op.code, op.s - s0,
                                   f"{exc} (extracting a room)")
            continue
        nop.door_type, nop.swing = op.door_type, op.swing
        c.openings.append(nop)
    return c


def capture_floating_furnishings(scene, room):
    """(Re)capture the furnishings that live inside `room` so they ride its
    floating moves. Run at extract, and lazily at drag start for a room that
    was LOADED floating (the capture is scene state, not document state)."""
    room._floating_furnishings = [
        f for f in scene.items()
        if isinstance(f, FurnishingItem) and f.floor == room.floor
        and f.group() is None
        and room.path.contains(f.sceneBoundingRect().center())]
    return room._floating_furnishings


def extract_room(scene, room):
    """EXTRACT (`placed → floating`), per §4 of `DESIGN_MODEL_v5.md`:

    1. a bound edge whose wall serves another room too → COPY the stretch
       spanning this edge (openings included), leave the original with the
       neighbour, point the edge and the binding at the copy;
    2. a wall serving only this room keeps its geometry whole;
    3. any vertex of the room's outline or walls that an OUTSIDE wall still
       touches → replaced with a private copy, then the room's own corners
       are re-folded so walls and outline share one private vertex each;
    4. `state = floating`, `extracted_from = <level>`; the furnishings whose
       centre lies in the room ride along while it floats.

    Returns `room`. A room that is already floating is returned unchanged."""
    if scene is None or room is None or room.scene() is not scene:
        return room
    if getattr(room, "placement_state", "placed") == "floating":
        return room
    corners = room.corners or []
    n = len(corners)
    # -- 1. walls the room does not wholly own: copy the stretch spanning each
    # of this room's edges, rebind edge + room to the copy, leave the original
    # where it is. "Not wholly owned" is either kind of sharing: another ROOM
    # is bound to it (a party wall), or the wall EXTENDS beyond this room's
    # edges (a through-wall) -- taking a longer wall whole would drag plan
    # geometry that was never this room's.
    by_wall = {}
    if n:
        for i, e in enumerate(room.outline):
            w = e.wall
            if w is not None and w.scene() is not None:
                by_wall.setdefault(id(w), (w, []))[1].append(i)
    for w, idxs in by_wall.values():
        shared = any(r is not room for r in w.rooms)
        u, L = w.unit(), w.length()

        def _span(i, u=u, L=L, w=w):
            a, b = corners[i], corners[(i + 1) % n]
            sa = (a.x() - w.p1.x()) * u.x() + (a.y() - w.p1.y()) * u.y()
            sb = (b.x() - w.p1.x()) * u.x() + (b.y() - w.p1.y()) * u.y()
            return max(0.0, min(sa, sb)), min(L, max(sa, sb))

        covered = sum(s1 - s0 for s0, s1 in map(_span, idxs))
        if not shared and L - covered < 1.0:
            continue          # sole-use and fully this room's: keep it whole
        room.unbind_wall(w)
        for i in idxs:
            c = _copy_edge_stretch(scene, room, room.outline[i],
                                   corners[i], corners[(i + 1) % n])
            room.bind_wall(c)
            room.outline[i].wall = c
            c.rebuild()
    # -- 2 + 3. privatize every vertex an outside wall still touches
    room_walls = set(room.walls)
    outside = set()
    for it in scene.items():
        if (isinstance(it, WallItem) and it not in room_walls
                and it.floor == room.floor):
            outside.add(id(it.end_vertex("p1")))
            outside.add(id(it.end_vertex("p2")))
    replace = {}

    def _private(v):
        if id(v) not in replace:
            replace[id(v)] = Vertex.at(QPointF(v.point()))
        return replace[id(v)]

    for e in room.outline:
        if id(e.v) in outside:
            e.v = _private(e.v)
    for w in room.walls:
        for attr in ("p1", "p2"):
            if id(w.end_vertex(attr)) in outside:
                w.set_end_vertex(attr, _private(w.end_vertex(attr)))
    # the copies minted their own constructor vertices; fold the room's
    # corners so its walls AND outline hold one (private) vertex per corner
    share_outline_vertices(room)
    # -- 4. capture the furnishings that live here, and flip the state
    capture_floating_furnishings(scene, room)
    room.extracted_from = room.floor
    room.placement_state = "floating"
    rebuild_all_walls(scene)
    room.update()
    return room


def join_room(scene, room):
    """JOIN (`floating → placed`), per §4: weld outline vertices onto plan
    vertices within `vertex_weld_in`, merge private walls that have become
    coincident with plan walls (openings dedup — the defect-9 machinery),
    split any plan wall a room corner lands on, rebind, `state = placed`.
    Coalescing touches only the runs the room's own walls sit in
    (`merge_wall` is per-run and refuses through degree-3 vertices), never
    the whole plan.

    A join is deliberately NOT a gap-closer: adoption tolerance is the
    document's own `vertex_weld_in` (0.6″) — at or below it two points ARE
    one vertex, so nothing "moves". A room dropped a gesture-tolerance away
    stays floating until the user places it properly.

    Returns `room`. A room that is not floating is returned unchanged."""
    if scene is None or room is None or room.scene() is not scene:
        return room
    if getattr(room, "placement_state", "placed") != "floating":
        return room
    floor = room.floor
    room_walls = set(room.walls)
    # -- split: a room corner resting on a plan wall's BODY makes a junction
    # (the split rule's second half); a landing inside a doorway splits per
    # R2c and files its report
    plan_walls = [it for it in scene.items()
                  if isinstance(it, WallItem) and it not in room_walls
                  and it.floor == floor]
    for e in room.outline:
        p = QPointF(e.v.point())
        for w in list(plan_walls):
            if w.scene() is None:
                continue
            seg = split_wall_at(scene, w, p)
            if seg is not None:
                plan_walls.append(seg)
                break
    # -- weld: fold coincident ends (room ↔ plan) onto one vertex, then let
    # the outline adopt its walls' corners, which are now the shared ones
    share_coincident_ends(scene, floor)
    share_outline_vertices(room)
    # -- merge: private walls now coincident/collinear with plan walls fuse;
    # only the runs this room touches. AT THE WELD TOLERANCE, not the 6"
    # auto-coalesce one (P4.2, mini-gate finding 5, Patrick's
    # fiveRoomDragSplit macro): a room dropped a gesture-width off had its
    # neighbours' walls SNAPPED onto its own line by the default perp_tol --
    # measured: R4's north wall physically moved 6" to meet the offset R2,
    # stranding R4's outline. The join's own rule (docstring above) is that
    # at or below vertex_weld_in two lines ARE one and beyond it nothing
    # moves; the merge must obey the same line.
    # force=True: the join is EXPLICIT -- it must merge coincident walls even
    # under shuffle / auto_coalesce off, or a Join would leave doubled walls
    # (P4.3 census finding)
    for w in list(room.walls):
        if w.scene() is not None:
            merge_wall(scene, w, perp_tol=SHARE_TOL, force=True)
    # -- rebind: edges whose wall was absorbed re-resolve to the survivor --
    # for THIS room via the full bind, and for every NEIGHBOUR via the narrow
    # dead-reference repair (found by the fiveRoomTest macro: the merge
    # forces the returning room's copy as survivor, absorbing the original
    # party wall the neighbour's outline still named, so R2/R3 painted their
    # shared edge as open over a wall that was right there)
    bind_room_walls(scene, room, settle=False)
    share_outline_vertices(room)
    for r in scene.items():
        if isinstance(r, RoomItem) and r is not room and r.floor == floor:
            if rebind_dead_edges(scene, r):
                share_outline_vertices(r)
    # an offset landing can leave an edge only partly covered by its named
    # wall -- a latent tear (finding 5); make the coverage boundary a corner
    for r in scene.items():
        if isinstance(r, RoomItem) and r.floor == floor:
            split_partially_covered_edges(scene, r)
    room.placement_state = "placed"
    room.extracted_from = None
    room._floating_furnishings = []
    rebuild_all_walls(scene)
    # ruling 2's addition (P4.3): the explicit join is where information a
    # mode deferred is DELIVERED -- anything this join could not weld says so
    # now through the defect-6 channel (a room-wall end resting inside a plan
    # doorway stays unwelded and names the door), not at the next document
    # walk. Unconditional: joining is the user's stated intent, whatever the
    # automatic flags say.
    for w in room.walls:
        if w.scene() is not None:
            report_doorway_landings(scene, w, "joining the room")
    room.update()
    return room
