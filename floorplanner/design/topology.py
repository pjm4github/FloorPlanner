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


def split_edge(design, wall_id, x, y, report=None):
    """Return a copy of `design` with wall `wall_id` split at the point (x, y)
    on its span into two collinear walls sharing a (welded) vertex. A no-op if
    the point is at either endpoint or off the centreline.

    Openings are REDISTRIBUTED by EXTENT (R2b): one wholly inside a segment
    lands there whichever end it is dimensioned off.

    **THE GUARD IS GONE AND THE PRIMITIVE IS TOTAL (R2c).** It was added at
    P1.3-followup naming P3.3, retargeted to P3.6 at P3.4(ii), and it was a
    placeholder pending representability the whole time -- `match="P3.6"` was
    that test naming its own executioner. The reason it cannot survive is not
    taste: **load-time planarize cannot decline.** A crossing that exists in the
    data has to split, and refusing there aborts or corrupts a load.

    So a TRUE STRADDLE -- the cut running through an opening, where neither
    segment can hold it -- is no longer refused. The opening lands on the
    segment holding its ANCHOR (R2b's tiebreak) and is appended to `report` if
    one is passed. Nothing is dropped, nothing is slid, and the fault is
    carried in the one vocabulary R5 defines rather than thrown.

    The scene op no longer declines either, for defect 17's reason: a gesture
    that silently does nothing is the worst of the three options, and we do not
    keep a second case of it on purpose."""
    plan = plan_split_edge(graph_from_design(design), wall_id, x, y)
    if plan is None:
        return copy.deepcopy(design)
    if plan.straddled and report is not None:
        for po in plan.straddled:
            report.append(
                f"opening {po.index} on wall {wall_id}: the split at "
                f"({x:.3f}, {y:.3f}) runs through it, so it lands on the "
                f"segment holding its anchor and no longer fits there")
    return apply_split_plan(design, plan)


# --------------------------------------------------------- planner / applier
# THE PLANNER / APPLIER SPLIT (P3.4, settled point 1).
#
# Everything above is pure `Design -> Design`. P3.4 needs the SAME operations on
# a live scene of `WallItem`s carrying `OpeningItem` children, room bindings,
# groups, z-order and floors. Two obvious routes were rejected: lifting the
# scene to a `Design` and applying back makes every wall edit a full-plan
# rebuild (it destroys item identity -- selection, in-flight drag state, group
# membership, P3.1's persistent uids -- and regresses exactly the numbers P3.8
# exists to improve); scene-side siblings sharing only the algorithm are one
# concept with two implementations, drifting from the day they are written.
#
# So the DECISION LOGIC RUNS ONCE, PURE, over a neutral `GraphView`, and returns
# a DELTA. Two THIN appliers execute it, touching only the objects the delta
# names: `apply_merge_plan` here, and `apply_merge_plan_to_scene` in
# `floorplanner.walls`. `--verify-design` re-derives the `Design` from the scene
# at every quiescent point, so if the two appliers ever disagree the shadow gate
# fires -- P1.6 was built for this moment.
#
# A delta plus an applier is a command in all but name, so P6.1's `QUndoStack`
# inherits the shape rather than inventing it.
#
# The delta names TOPOLOGY -- which corners merge, which walls die, where the
# openings land. It deliberately does NOT name room binding: a `Design` records
# that as `wall.left`/`right`, the scene as `WallItem.rooms`, and each applier
# maintains its own from `Merge.absorbed`. That is not applier drift; it is the
# one thing the two targets genuinely represent differently.

# The planner's neutral input. `key` and `anchor` values are the CALLER's own
# handles (a wall id / vertex id for a `Design`; a `WallItem` / `Vertex` object
# for a scene) -- the planner only ever compares and passes them back.
GraphView = namedtuple("GraphView", "walls pos anchor")
WallView = namedtuple("WallView", "key level v1 v2 type openings")
# `frm` is the END the opening is dimensioned off ("v1"/"v2"), which R2b
# needs as the tiebreak when a cut runs through it.
OpeningView = namedtuple("OpeningView", "index s width ident frm")

# The deltas. On a `Merge`, `v1`/`v2` are the corner anchors the survivor
# adopts, or None when the merge lands somewhere no existing corner sits (then
# `p1`/`p2` are used). On a `Split`, `v` is the corner anchor already sitting at
# the split point, or None when one must be made; `straddled` names the openings
# the split point falls inside, which neither segment can hold.
Merge = namedtuple("Merge", "survivor absorbed v1 v2 p1 p2 dropped_vertices "
                            "openings dropped_openings")
Split = namedtuple("Split", "wall v at keep_openings move_openings straddled")
PlannedOpening = namedtuple("PlannedOpening", "wall index s")

ANGLE_TOL = 0.02        # |sin| between units to still call two walls parallel
DEDUP_TOL = 1.0         # two same-code openings this close are ONE (defect 9)
LINE_BUCKET = 3.0       # line-offset bucket for the candidate index (>> tols)


def _find(parent, i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def _union(parent, a, b):
    ra, rb = _find(parent, a), _find(parent, b)
    if ra != rb:
        parent[max(ra, rb)] = min(ra, rb)


def _same_line(a, b, pos, perp_tol, angle_tol):
    """`b` lies on `a`'s line: parallel, and both its ends within `perp_tol`.
    Deliberately the predicate `walls.coincident_walls` already uses, so the
    scene keeps the merge candidates it has always had."""
    a1 = pos[a.v1]
    u = _unit(a1, pos[a.v2])
    ub = _unit(pos[b.v1], pos[b.v2])
    if abs(ub[0] * u[1] - ub[1] * u[0]) > angle_tol:
        return False
    return all(abs((p[0] - a1[0]) * u[1] - (p[1] - a1[1]) * u[0]) <= perp_tol
               for p in (pos[b.v1], pos[b.v2]))


def _spans_overlap(a, b, pos):
    """`b`'s span overlaps `a`'s along `a`'s axis -- the duplicate party wall
    case the editor's coalesce exists to clean up."""
    a1 = pos[a.v1]
    u = _unit(a1, pos[a.v2])
    length = math.dist(a1, pos[a.v2])
    s = [(p[0] - a1[0]) * u[0] + (p[1] - a1[1]) * u[1]
         for p in (pos[b.v1], pos[b.v2])]
    return max(s) > 0.5 and min(s) < length - 0.5


def _abut_at_degree_2(a, b, degree):
    """`a` and `b` meet end to end at a corner NOTHING ELSE attaches to. The
    degree test is what keeps a real T-junction a vertex: a third wall there
    makes the corner load-bearing for the planar subdivision."""
    for ka in (a.v1, a.v2):
        for kb in (b.v1, b.v2):
            if ka != kb or degree[(a.level, ka)] != 2:
                continue
            far_a = a.v2 if ka == a.v1 else a.v1
            far_b = b.v2 if kb == b.v1 else b.v1
            if far_a != far_b:                 # not a degenerate two-wall loop
                return True
    return False


def _plan_one_merge(run, pos, anchor, degree):
    """One run of mergeable walls -> one `Merge`. `run[0]` survives, and the
    merged wall keeps the SURVIVOR'S DIRECTION -- every other end projects onto
    its axis, so `left`/`right` stay on the sides they were on."""
    surv = run[0]
    a = pos[surv.v1]
    u = _unit(a, pos[surv.v2])
    ends = [((p[0] - a[0]) * u[0] + (p[1] - a[1]) * u[1], k)
            for w in run for k, p in ((w.v1, pos[w.v1]), (w.v2, pos[w.v2]))]
    smin, kmin = min(ends, key=lambda t: t[0])
    smax, kmax = max(ends, key=lambda t: t[0])
    p1 = (a[0] + u[0] * smin, a[1] + u[1] * smin)
    p2 = (a[0] + u[0] * smax, a[1] + u[1] * smax)
    # adopt the real corner when the merged end lands ON it; a wall absorbed
    # from up to perp_tol off the line lands on the PROJECTION instead, which is
    # a new position and so honestly a new corner
    v1 = anchor.get(kmin) if math.dist(pos[kmin], p1) <= WELD_TOL else None
    v2 = anchor.get(kmax) if math.dist(pos[kmax], p2) <= WELD_TOL else None

    kept, planned, dropped_ops = [], [], []
    for w in run:                              # run order: the survivor first
        wa = pos[w.v1]
        wu = _unit(wa, pos[w.v2])
        for ov in w.openings:
            px = (wa[0] + wu[0] * ov.s, wa[1] + wu[1] * ov.s)
            s = (px[0] - p1[0]) * u[0] + (px[1] - p1[1]) * u[1]
            dup = next((k for k in kept if k[0] == ov.ident and abs(k[1] - s)
                        <= max(DEDUP_TOL, min(k[2], ov.width) / 2)), None)
            if dup is not None:                # defect 9: no stacked doors
                dropped_ops.append(PlannedOpening(w.key, ov.index, s))
                continue
            kept.append((ov.ident, s, ov.width))
            planned.append(PlannedOpening(w.key, ov.index, s))
    planned.sort(key=lambda po: po.s)

    used = defaultdict(int)                    # corners this run consumes whole
    for w in run:
        used[w.v1] += 1
        used[w.v2] += 1
    gone = tuple(anchor[k] for k in sorted(used, key=str)
                 if k not in (kmin, kmax) and k in anchor
                 and degree[(surv.level, k)] == used[k])
    return Merge(surv.key, tuple(w.key for w in run[1:]), v1, v2, p1, p2,
                 gone, tuple(planned), tuple(dropped_ops))


def line_bucket(a, b):
    """The line-offset bucket for a wall running `a` -> `b`: `("h"|"v", n)` for
    an axis-aligned wall, None for a diagonal (which no offset bucket narrows).

    THE ONE DEFINITION, imported by both users -- this module's
    `_candidate_groups` and `walls._WallIndex`. It was briefly two
    transcriptions of one policy, which is precisely the F2 disease this task
    exists to remove; and since the policy is pure coordinates it belongs on
    this side of the Qt fence, with the scene importing it rather than the
    reverse. The bucket is the lever that made coalesce survivable on a
    1492-wall plan, so wherever a merge or coincidence query is decided, it has
    to be the same lever."""
    u = _unit(a, b)
    if abs(u[1]) < 1e-4:
        return ("h", round(a[1] / LINE_BUCKET))
    if abs(u[0]) < 1e-4:
        return ("v", round(a[0] / LINE_BUCKET))
    return None


def bucket_reach(perp_tol):
    """How many neighbouring buckets a query at `perp_tol` must sweep."""
    return int(perp_tol / LINE_BUCKET) + 1


def _candidate_groups(walls, pos, perp_tol):
    """Yield `(primary, near)` index lists: walls that could possibly merge --
    same level, same type, and on a nearby parallel line."""
    reach = bucket_reach(perp_tol)
    buckets, diag = defaultdict(list), defaultdict(list)
    for i, w in enumerate(walls):
        grp = (w.level, w.type)
        b = line_bucket(pos[w.v1], pos[w.v2])
        if b is None:
            diag[grp].append(i)                # non-axis-aligned: rare
        else:
            buckets[(grp, *b)].append(i)
    for (grp, axis, b), idxs in buckets.items():
        near = list(idxs) + diag.get(grp, [])
        for d in range(1, reach + 1):
            near += buckets.get((grp, axis, b + d), [])
            near += buckets.get((grp, axis, b - d), [])
        yield idxs, near
    for idxs in diag.values():
        yield idxs, idxs


def plan_merge_collinear(view, perp_tol=WELD_TOL, angle_tol=ANGLE_TOL):
    """Plan every collinear merge in `view` -- the ONE place the decision is
    made, for a `Design` and for a live scene alike.

    Two walls join a run when they are on the same line (same level, same type)
    and either their spans OVERLAP or they ABUT at a degree-2 corner. Runs are
    maximal, so one pass replaces the old merge-one-and-restart loop; the
    survivor is the run's first wall in the caller's own order, which is what
    makes the plan deterministic."""
    pos = view.pos
    walls = [w for w in view.walls if math.dist(pos[w.v1], pos[w.v2]) > 1e-6]
    degree = defaultdict(int)
    for w in walls:
        degree[(w.level, w.v1)] += 1
        degree[(w.level, w.v2)] += 1

    parent = list(range(len(walls)))
    for primary, near in _candidate_groups(walls, pos, perp_tol):
        for ia in primary:
            for ib in near:
                if ia == ib or _find(parent, ia) == _find(parent, ib):
                    continue
                a, b = walls[ia], walls[ib]
                if _same_line(a, b, pos, perp_tol, angle_tol) and (
                        _spans_overlap(a, b, pos)
                        or _abut_at_degree_2(a, b, degree)):
                    _union(parent, ia, ib)

    runs = defaultdict(list)
    for i in range(len(walls)):
        runs[_find(parent, i)].append(i)
    return [_plan_one_merge([walls[i] for i in sorted(idxs)], pos, view.anchor,
                            degree)
            for _root, idxs in sorted(runs.items()) if len(idxs) > 1]


def _code_width(code):
    """Nominal opening width from a WWHH / WWWHH size code ("3280" -> 32").

    Parsed locally rather than shared with `geometry.parse_wwhh`, which lives on
    the Qt side of the fence this module may not cross. Deliberately lenient:
    the width is used only to decide whether a split falls INSIDE an opening,
    and a code this cannot read should not make a split raise."""
    code = str(code).strip()
    if not code.isdigit() or len(code) not in (4, 5, 6):
        return 0.0
    return float(int(code[:2 if len(code) == 4 else 3]))


def graph_from_design(design, level=None):
    """A `GraphView` of `design` -- wall ids and vertex ids as the handles."""
    pos = _positions(design)
    walls = []
    for w in design.walls:
        if level is not None and w.level != level:
            continue
        if w.v1 not in pos or w.v2 not in pos:
            continue
        length = math.dist(pos[w.v1], pos[w.v2])
        ops = []
        for i, o in enumerate(w.openings if isinstance(w.openings, list)
                              else ()):
            anc = o.anchor if isinstance(o.anchor, dict) else {}
            off = anc.get("offset_in", 0.0)
            ow = _code_width(o.code)
            # DEFECT 24: `offset_in` is the distance from the named end to the
            # opening's NEAR EDGE -- the schema says so and `bridge._walls_of` /
            # `_opening_s` both emit and invert it that way. This read used to
            # omit the half-width, putting the planner's idea of the opening
            # half a door away from everyone else's (measured 18.00" on a 36"
            # door). It self-cancelled against `_reanchor`'s matching omission
            # for a v1 anchor on the kept segment, which is why it survived.
            frm = anc.get("from")
            if frm == "v2":
                s = length - off - ow / 2.0
            elif frm == "center":
                s = length / 2.0 + off        # consume only (R4); never emitted
            else:
                s = off + ow / 2.0
            ops.append(OpeningView(i, s, ow, (o.kind, o.code),
                                   "v2" if frm == "v2" else "v1"))
        walls.append(WallView(w.id, w.level, w.v1, w.v2, w.type, tuple(ops)))
    return GraphView(walls, pos, {vid: vid for vid in pos})


def _adopt_vertex(d, anchor, xy, level):
    """The vertex id the merged end should carry: the adopted corner when the
    plan named one, else the welded-or-fresh vertex at the planned point."""
    if anchor is not None and any(v.id == anchor for v in d.vertices):
        return anchor
    vid = _vertex_at(d, xy[0], xy[1], level)
    if vid is None:
        vid = _next_id(d, "v")
        d.vertices.append(Vertex.from_dict(
            {"id": vid, "level": level,
             "x": round(xy[0], 4), "y": round(xy[1], 4)}))
    return vid


def apply_merge_plan(design, plan):
    """The `Design` applier: execute a merge delta, touching only what it names.

    Openings are re-anchored to the NEAREST end of the merged wall -- the same
    convention `importer`/`bridge` already emit -- because the merge moved both
    ends and an offset from the old `v1` would name nothing."""
    d = copy.deepcopy(design)
    by_id = {w.id: w for w in d.walls}
    dead = set()
    for m in plan:
        surv = by_id.get(m.survivor)
        if surv is None:
            continue
        ops = []                               # read off the PRE-merge geometry
        for po in m.openings:
            src = by_id.get(po.wall)
            src_ops = src.openings if src is not None and isinstance(
                src.openings, list) else []
            if po.index < len(src_ops):
                ops.append((src_ops[po.index], po.s))
        surv.v1 = _adopt_vertex(d, m.v1, m.p1, surv.level)
        surv.v2 = _adopt_vertex(d, m.v2, m.p2, surv.level)
        length = math.dist(m.p1, m.p2)
        # THE THIRD SITE OF DEFECT 24, and the reason it is a defect and not a
        # typo: this was a fourth hand-written copy of the s <-> anchor
        # arithmetic, inline, with the same missing half-width. Routed through
        # `_reanchor` so the conversion exists once.
        merged = [_reanchor(o, s, length) for o, s in ops]
        surv.openings = merged
        dead.update(m.absorbed)
    if dead:
        d.walls = [w for w in d.walls if w.id not in dead]
        live = {w.v1 for w in d.walls} | {w.v2 for w in d.walls}
        d.vertices = [v for v in d.vertices if v.id in live]
    return d


def plan_split_edge(view, wall_key, x, y, on_seg_tol=ON_SEG_TOL):
    """Plan the split of `wall_key` at (x, y) -- the OTHER half of the split
    rule, and the one op both a document repair and a live drag need.

    Returns a `Split`, or None when there is nothing to split: unknown wall,
    degenerate span, a point off the centreline, or a point already at an
    endpoint (which is a corner, not a split). Openings are assigned to
    whichever segment holds them; one the split point falls INSIDE is reported
    in `straddled` and left on the first segment, for the caller to refuse or
    raise on -- the planner itself never raises, because one of its two callers
    is a mouse drag."""
    w = next((ww for ww in view.walls if ww.key == wall_key), None)
    if w is None:
        return None
    pos = view.pos
    a, b = pos[w.v1], pos[w.v2]
    length = math.dist(a, b)
    if length < MIN_SPAN:
        return None
    u = _unit(a, b)
    s = (x - a[0]) * u[0] + (y - a[1]) * u[1]
    if abs((y - a[1]) * u[0] - (x - a[0]) * u[1]) > on_seg_tol:
        return None                            # not on this wall's centreline
    at = (a[0] + u[0] * s, a[1] + u[1] * s)
    if not (0.0 < s < length) or min(s, length - s) <= WELD_TOL:
        return None                            # at an end -> nothing to split
    on_level = {k for ww in view.walls if ww.level == w.level
                for k in (ww.v1, ww.v2)}
    near = [k for k in on_level if math.dist(pos[k], at) <= WELD_TOL]
    vkey = min(near, key=lambda k: math.dist(pos[k], at)) if near else None
    keep, move, straddled = [], [], []
    for ov in w.openings:
        half = ov.width / 2
        if ov.s - half < s < ov.s + half:
            straddled.append(PlannedOpening(w.key, ov.index, ov.s))
        if ov.s <= s:
            keep.append(PlannedOpening(w.key, ov.index, ov.s))
        else:
            move.append(PlannedOpening(w.key, ov.index, ov.s - s))
    return Split(w.key, view.anchor.get(vkey), at, tuple(keep), tuple(move),
                 tuple(straddled))


def _opening_centre(opening, length):
    """The opening's CENTRE along a wall of `length`, from its stored anchor --
    the one place that conversion is written for a `Design` opening (defect
    24). `bridge._opening_s` is the identical arithmetic for a raw dict."""
    anc = opening.anchor if isinstance(opening.anchor, dict) else {}
    off, ow = anc.get("offset_in", 0.0), _code_width(opening.code)
    frm = anc.get("from")
    if frm == "v2":
        return length - off - ow / 2.0
    if frm == "center":
        return length / 2.0 + off
    return off + ow / 2.0


def _reanchor(opening, s, length, width=None, frm=None):
    """Re-dimension an opening whose wall changed, `s` being its CENTRE on the
    new wall.

    `offset_in` is to the NEAR EDGE, so the half-width comes off -- omitting it
    was defect 24, and it is the same half-width `bridge._opening_s` adds back.

    `frm` forces the end to dimension from, which R2b requires: an opening that
    lands on the segment NOT holding its anchor re-seats to the SAME-SIDE end of
    its new segment -- the split vertex -- rather than to the nearer one, so its
    position is preserved exactly and only the description changes. Left None it
    mints against the nearer end, ties to v1 (R4)."""
    ow = _code_width(opening.code) if width is None else width
    if frm is None:
        frm = "v1" if s <= length / 2 else "v2"
    off = (s - ow / 2.0) if frm == "v1" else (length - s - ow / 2.0)
    opening.anchor = {"from": frm, "offset_in": round(off, 4)}
    return opening


def apply_split_plan(design, split):
    """The `Design` applier for a split delta. The first segment keeps the
    wall's id (and so its identity in the document); the second is minted."""
    d = copy.deepcopy(design)
    if split is None:
        return d
    w = next((ww for ww in d.walls if ww.id == split.wall), None)
    if w is None:
        return d
    src_ops = w.openings if isinstance(w.openings, list) else []
    keep = [(src_ops[po.index], po.s) for po in split.keep_openings
            if po.index < len(src_ops)]
    move = [(src_ops[po.index], po.s) for po in split.move_openings
            if po.index < len(src_ops)]
    pos = _positions(d)
    a, b = pos[w.v1], pos[w.v2]
    vid = _adopt_vertex(d, split.v, split.at, w.level)
    v2_old = w.v2
    w.v2 = vid                                 # first half keeps w.id
    first_len = math.dist(a, split.at)
    second_len = math.dist(split.at, b)
    w.openings = [_reanchor(o, s, first_len) for o, s in keep]
    d.walls.append(Wall.from_dict({
        "id": _next_id(d, "w"), "level": w.level, "v1": vid, "v2": v2_old,
        "type": w.type, "left": w.left, "right": w.right,
        "openings": []}))
    d.walls[-1].openings = [_reanchor(o, s, second_len) for o, s in move]
    return d


def merge_collinear(design):
    """Return a copy of `design` with runs of collinear, same-type walls merged
    into one wall -- the inverse of `split_edge`, closing the degree-2 spurs a
    split leaves behind.

    P3.4 rebuilt this as `plan_merge_collinear` + `apply_merge_plan` so the
    scene shares the decision logic; the composition here is what every existing
    caller still sees. Two behaviours changed with the rebuild and both are
    fixes: a wall carrying openings is no longer refused (they are redistributed
    onto the merged span and deduplicated), and the survivor keeps its own
    direction, so `left`/`right` can no longer silently swap when the run
    extends behind its `v1`."""
    d = design
    for _ in range(8):                         # runs are maximal; 8 is a fuse
        plan = plan_merge_collinear(graph_from_design(d))
        if not plan:
            break
        d = apply_merge_plan(d, plan)
    return d if d is not design else copy.deepcopy(design)


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
