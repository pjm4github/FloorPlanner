"""Planar-topology operations over a v5 `Design` (P1.3).

Pure functions, dataclasses in and out (P1.1's `Design`), no Qt. These replace
the editor's per-edit detection engine in Phase 3: `trace_faces` recovers rooms
from the wall graph, `enclosing_face` is "which room is this point in", and
`split_edge` / `merge_collinear` / `planarize` maintain the planar subdivision.

Ported from `tools/migrate_to_design_v5.py` (`trace_faces`, `inner_faces`, the
`_split_params` planarise logic). The legacy import weld lives in `legacy.py`,
NOT here -- see that module's note; it has a different lifetime.

Winding convention: an inner face is wound so that walking an edge v1->v2 keeps
the interior on the `(dy, -dx)` side -- the wall's `left`. `trace_faces` and the
stored `left`/`right` MUST agree, or every side silently swaps and I6 still
passes; `tests/test_topology.py` pins it directly.
"""
import copy
import math
from collections import defaultdict, namedtuple

from floorplanner.design.model import Vertex, Wall

WELD_TOL = 0.6      # coords closer than this are one vertex
ON_SEG_TOL = 1.0    # perpendicular distance to count a point as on a centreline
MIN_SPAN = 1.0

# a traced face: `vertices` is the vertex-id loop; `area_in2` its area (sq in);
# `level` the level it belongs to
Face = namedtuple("Face", "vertices area_in2 level")


# ------------------------------------------------------------------ small math
def _area2(pts):
    n = len(pts)
    return sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
               for i in range(n))


def _pip(q, pts):
    x, y = q
    inside = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def _unit(a, b):
    L = math.dist(a, b)
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L) if L > 1e-9 else (1.0, 0.0)


def _proj(p, a, u):
    vx, vy = p[0] - a[0], p[1] - a[1]
    return vx * u[0] + vy * u[1], abs(vy * u[0] - vx * u[1])


# ------------------------------------------------------------------ graph build
def _levels(design):
    return [lv.id for lv in design.levels]


def _positions(design):
    return {v.id: (v.x, v.y) for v in design.vertices}


def _adjacency(design, level):
    """(adj, pos) for the wall graph on `level`: adj maps a vertex id to its
    neighbour ids; pos maps a vertex id to its (x, y)."""
    pos = _positions(design)
    adj = defaultdict(set)
    for w in design.walls:
        if w.level != level:
            continue
        adj[w.v1].add(w.v2)
        adj[w.v2].add(w.v1)
    return {k: list(v) for k, v in adj.items()}, pos


# ------------------------------------------------------------------ face trace
def _trace_faces_raw(adj, pos):
    """Every face of the planar graph as a list of directed (u, v) edges.
    Faces of a planar subdivision are disjoint by construction."""
    order, idx = {}, {}
    for v, nbrs in adj.items():
        s = sorted(set(nbrs), key=lambda w: math.atan2(pos[w][1] - pos[v][1],
                                                        pos[w][0] - pos[v][0]))
        order[v] = s
        for i, w in enumerate(s):
            idx[(v, w)] = i
    seen, faces = set(), []
    for u in order:
        for v in order[u]:
            if (u, v) in seen:
                continue
            face, cu, cv = [], u, v
            while (cu, cv) not in seen:
                seen.add((cu, cv))
                face.append((cu, cv))
                nb = order[cv]
                nxt = nb[(idx[(cv, cu)] - 1) % len(nb)]
                cu, cv = cv, nxt
            if face:
                faces.append(face)
    return faces


def _inner_faces(faces, pos):
    """From the raw faces, the room-candidate inner faces: drop sub-2 sf slivers,
    then keep the MAJORITY-winding faces and drop every opposite-wound one.

    Interior faces all share one winding; each connected component's outer
    (unbounded) boundary is wound the other way. Dropping ALL opposite-wound
    faces removes every boundary -- a plan with a detached garage, or Phase-4
    floating/concept rooms, has one boundary per component, not one total.
    Do NOT drop by size: the largest interior face can be a real room (defect 18
    -- symmetricP1's Garage). Returns [(area_in2, edge_loop, pts)].

    (A single-face-per-component plan -- e.g. one lone room -- ties the majority
    vote; that edge case is revisited with concept-room templates at P4.4.)"""
    out = []
    for f in faces:
        pts = [pos[u] for u, _ in f]
        if len(pts) < 3:
            continue
        a2 = _area2(pts)
        if abs(a2) < 2 * 144:                 # < 2 sf: a spur or a sliver
            continue
        out.append((abs(a2) / 2.0, f, pts, a2))
    if not out:
        return []
    positive = sum(1 for t in out if t[3] > 0)
    sign = 1 if positive * 2 > len(out) else -1
    return [(a, f, pts) for a, f, pts, s in out if (s > 0) == (sign > 0)]


def trace_faces(design, level=None):
    """The inner (room) faces of `design`'s wall graph, as `Face`s. `level`
    restricts to one level; None traces every level. Faces are wound so the
    interior sits on each edge's `(dy, -dx)` (`left`) side."""
    faces = []
    for lid in ([level] if level is not None else _levels(design)):
        adj, pos = _adjacency(design, lid)
        for area, floop, _pts in _inner_faces(_trace_faces_raw(adj, pos), pos):
            faces.append(Face(tuple(u for u, _ in floop), area, lid))
    return faces


def enclosing_face(design, point, level):
    """The inner face containing `point` on `level`, or None. Replaces the
    editor's detect_room: the room a click falls in is the face around it."""
    pos = _positions(design)
    for f in trace_faces(design, level):
        if _pip(point, [pos[v] for v in f.vertices]):
            return f
    return None


# ------------------------------------------------------------------ edit ops
def _vertex_at(design, x, y, level):
    """An existing vertex id within WELD_TOL of (x, y) on `level`, or None --
    the weld-on-insert rule that keeps a corner one point, not two."""
    for v in design.vertices:
        if v.level == level and math.dist((v.x, v.y), (x, y)) <= WELD_TOL:
            return v.id
    return None


def _next_id(design, prefix):
    used = {o.id for coll in (design.vertices, design.walls, design.rooms)
            for o in coll}
    i = 1
    while f"{prefix}{i}" in used:
        i += 1
    return f"{prefix}{i}"


def split_edge(design, wall_id, x, y):
    """Return a copy of `design` with wall `wall_id` split at the point (x, y)
    on its span into two collinear walls sharing a (welded) vertex. A no-op if
    the point is at either endpoint.

    RAISES on a wall that carries openings: redistributing a door/window across
    a split (which segment owns it, at what offset) is P3.3's split rule, not
    yet built. Failing loud here means the missing redistribution surfaces at
    the call site, not three tasks later as a misplaced opening. P3.3 removes
    this guard as part of implementing redistribution."""
    src = next((w for w in design.walls if w.id == wall_id), None)
    if src is not None and isinstance(src.openings, list) and src.openings:
        raise NotImplementedError(
            f"split_edge on wall {wall_id} carrying {len(src.openings)} "
            "opening(s): opening redistribution across a split is P3.3 (the "
            "wall-move split rule). Remove this guard when implementing it.")
    d = copy.deepcopy(design)
    pos = _positions(d)
    w = next((w for w in d.walls if w.id == wall_id), None)
    if w is None:
        return d
    a, b = pos[w.v1], pos[w.v2]
    if math.dist(a, (x, y)) <= WELD_TOL or math.dist(b, (x, y)) <= WELD_TOL:
        return d                              # at an endpoint -> nothing to split
    vid = _vertex_at(d, x, y, w.level) or _next_id(d, "v")
    if vid not in {v.id for v in d.vertices}:
        d.vertices.append(Vertex.from_dict(
            {"id": vid, "level": w.level, "x": round(x, 4), "y": round(y, 4)}))
    v2_old = w.v2
    w.v2 = vid                                # first half keeps w.id + openings
    d.walls.append(Wall.from_dict({
        "id": _next_id(d, "w"), "level": w.level, "v1": vid, "v2": v2_old,
        "type": w.type, "left": w.left, "right": w.right, "openings": []}))
    return d


def merge_collinear(design):
    """Return a copy of `design` with runs of collinear, same-type walls that
    meet at a degree-2 vertex (no other wall, no opening straddling the join)
    merged into one wall. The inverse of split_edge; closes the degree-2 spurs a
    split leaves behind."""
    d = copy.deepcopy(design)
    changed = True
    while changed:
        changed = False
        pos = _positions(d)
        incident = defaultdict(list)
        for w in d.walls:
            incident[(w.level, w.v1)].append(w)
            incident[(w.level, w.v2)].append(w)
        for (level, vid), ws in incident.items():
            if len(ws) != 2:
                continue
            w1, w2 = ws
            if w1 is w2 or w1.type != w2.type:
                continue
            if (w1.openings or w2.openings):
                continue
            # the two far endpoints and the shared vertex must be collinear
            far1 = w1.v1 if w1.v2 == vid else w1.v2
            far2 = w2.v1 if w2.v2 == vid else w2.v2
            if far1 == far2:
                continue
            u1 = _unit(pos[far1], pos[vid])
            u2 = _unit(pos[vid], pos[far2])
            if abs(u1[0] * u2[1] - u1[1] * u2[0]) > 1e-3:   # not collinear
                continue
            w1.v1, w1.v2 = far1, far2          # w1 absorbs the run
            d.walls.remove(w2)
            d.vertices = [v for v in d.vertices
                          if not (v.id == vid and v.level == level)]
            changed = True
            break
    return d


def planarize(design):
    """Return a copy of `design` in which every wall is split at each existing
    vertex that lies on its interior span (an unsplit T-junction). Idempotent on
    an already-planar design. Crossing-point insertion and opening
    redistribution are P3.3/P3.4 -- this covers the T-junction case the migrator
    needs on import."""
    d = copy.deepcopy(design)
    changed = True
    while changed:
        changed = False
        pos = _positions(d)
        by_level = defaultdict(list)
        for v in d.vertices:
            by_level[v.level].append(v.id)
        for w in list(d.walls):
            a, b = pos[w.v1], pos[w.v2]
            L = math.dist(a, b)
            if L < MIN_SPAN:
                continue
            u = _unit(a, b)
            cut = None
            for vid in by_level[w.level]:
                if vid in (w.v1, w.v2):
                    continue
                s, perp = _proj(pos[vid], a, u)
                if perp <= ON_SEG_TOL and MIN_SPAN < s < L - MIN_SPAN:
                    cut = pos[vid]
                    break
            if cut is not None:
                d = split_edge(d, w.id, cut[0], cut[1])
                changed = True
                break
    return d
