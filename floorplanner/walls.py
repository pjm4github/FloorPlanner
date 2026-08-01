"""Wall graphics items (WallItem/OpeningItem) and the wall-network
algorithms: spatial indices, coalescing, welding, fracturing, junction
clipping, and the full-scene rebuild.

rebuild_all_walls() refreshes rooms and a couple of WallItem actions touch
room binding; those are LATE imports from floorplanner.rooms so this module
stays importable before rooms (which imports this one)."""
import math

from PyQt6 import sip
from PyQt6.QtCore import *  # noqa: F401
from PyQt6.QtGui import *  # noqa: F401
from PyQt6.QtWidgets import *  # noqa: F401

from floorplanner.config import *  # noqa: F401
from floorplanner.design.topology import (
    ON_SEG_TOL, GraphView, OpeningView, WallView, bucket_reach, line_bucket,
    plan_merge_collinear, plan_split_edge,
)
from floorplanner.geometry import *  # noqa: F401
from floorplanner.vertex import Vertex


SHARE_TOL = 0.6        # two ends this close ARE one corner (== vertex_weld_in)


class _DragVertex:
    """One corner being moved by a drag (P3.3): the vertex, where it started,
    and every wall end that references it.

    `ends` is resolved ONCE, at drag start, so the per-event cost is the size of
    the corner and not the size of the plan -- the view repaints everything on
    every change, so anything per-event that scales with the scene is the thing
    that stalls a big plan."""

    __slots__ = ("v", "orig", "ends", "edges")

    def __init__(self, vertex):
        self.v = vertex
        self.orig = QPointF(vertex.point())
        self.ends = []
        self.edges = []       # room OutlineEdges holding this same corner (P3.5)

    def apply(self, dx, dy):
        """Move the corner. Every end follows because it IS the corner."""
        self.v = self.v.relocated_to(QPointF(self.orig.x() + dx,
                                             self.orig.y() + dy))
        for w, attr in self.ends:
            w.set_end_vertex(attr, self.v)
        for e in self.edges:
            e.v = self.v


def nearest_wall_endpoint(scene, p: QPointF, tol: float, exclude=None):
    """Closest endpoint of any wall (other than `exclude`) within `tol`."""
    best, best_d = None, tol
    if scene is None:
        return None
    active = active_floor()
    for it in scene.items():
        if (isinstance(it, WallItem) and it is not exclude
                and it.floor == active):         # weld only to active-floor walls
            for q in (it.p1, it.p2):
                d = QLineF(p, q).length()
                if d < best_d:
                    best_d, best = d, QPointF(q)
    return best


def nearest_wall_body(scene, p: QPointF, tol: float, exclude=None):
    """Closest (wall, centreline point) within reach of `p`, or None.

    This is the fuse target for T-junctions: a wall end that stops at (or
    inside) the body of another wall snaps onto that wall's centreline so
    the two paint as one solid joint."""
    best, best_d = None, float("inf")
    if scene is None:
        return None
    active = active_floor()
    for it in scene.items():
        if (isinstance(it, WallItem) and it is not exclude
                and it.floor == active):         # weld only to active-floor walls
            length = it.length()
            if length < 1e-6:
                continue
            u = it.unit()
            s = (p.x() - it.p1.x()) * u.x() + (p.y() - it.p1.y()) * u.y()
            s = max(0.0, min(length, s))
            q = it.point_at(s)
            d = QLineF(p, q).length()
            if d <= max(tol, it.t * 0.5 + 1.0) and d < best_d:
                best_d, best = d, (it, QPointF(q))
    return best


def nearest_wall_body_point(scene, p: QPointF, tol: float, exclude=None):
    hit = nearest_wall_body(scene, p, tol, exclude)
    return hit[1] if hit is not None else None


class _WallIndex:
    """Per-rebuild spatial cache so each wall's rebuild() is O(local) instead
    of O(all walls): the corner fold (joined ends) + per-line buckets
    (coincident party walls).  Built once by rebuild_all_walls and passed to
    every wall; the exact predicates are unchanged, the index just narrows the
    candidate set to a guaranteed superset.

    P3.4 (iii) took the endpoint hash out: `joined_at` reads a `_CornerIndex`,
    so "is this end joined" is a DEGREE lookup rather than a 3x3 cell search,
    and it answers from the same fold that decides what one corner is
    everywhere else in this module. The LINE buckets stay, and stay here --
    they are a spatial index, not detection machinery -- but the bucketing
    POLICY does not: `topology.line_bucket` owns it, so this and the planner
    narrow candidates by one definition rather than two transcriptions."""

    def __init__(self, scene):
        items = [w for w in (scene.items() if scene is not None else [])
                 if isinstance(w, WallItem)]
        self.corners = _CornerIndex(items)   # every wall, open and grouped too
        self.lines = {}          # ("h"|"v", n) -> [walls on that line offset]
        self.diag = []           # non-axis-aligned real walls (rare)
        for w in items:
            if w.length() < 1e-6:
                continue
            b = line_bucket((w.p1.x(), w.p1.y()), (w.p2.x(), w.p2.y()))
            if b is None:
                self.diag.append(w)
            else:
                self.lines.setdefault(b, []).append(w)

    def joined_at(self, wall, attr) -> bool:
        return self.corners.joined(wall, attr)

    def coincident_candidates(self, wall, reach=1):
        b = line_bucket((wall.p1.x(), wall.p1.y()), (wall.p2.x(), wall.p2.y()))
        if b is None:                                  # diagonal query: rare
            return [w for ws in self.lines.values() for w in ws] + self.diag
        axis, n = b
        return [w for d in range(-reach, reach + 1)
                for w in self.lines.get((axis, n + d), ())] + self.diag


def coincident_walls(scene, wall, index=None, perp_tol=1.5):
    """Real walls that lie on (within `perp_tol` of) the same line as `wall` and
    overlap its span.  At the default 1.5" this finds the duplicate party walls
    on a shared boundary (so a plain wall opens for a coincident wall's door);
    coalescing passes the wider wall-snap grid so near-parallel walls merge.
    With perp_tol > the index buckets, pass index=None for a full scan."""
    if scene is None or wall.length() < 1e-6:
        return []
    u = wall.unit()
    length = wall.length()
    out = []
    if index is not None:
        reach = bucket_reach(perp_tol)
        cands = index.coincident_candidates(wall, reach)
    else:
        cands = scene.items()
    for w in cands:
        if not isinstance(w, WallItem) or w is wall \
                or w.length() < 1e-6 or w.scene() is None \
                or w.floor != wall.floor:        # coalesce stays on one floor
            continue
        wu = w.unit()
        if abs(wu.x() * u.y() - wu.y() * u.x()) > 0.02:        # not parallel
            continue
        d1 = abs((w.p1.x() - wall.p1.x()) * u.y()              # off the line?
                 - (w.p1.y() - wall.p1.y()) * u.x())
        d2 = abs((w.p2.x() - wall.p1.x()) * u.y()
                 - (w.p2.y() - wall.p1.y()) * u.x())
        if d1 > perp_tol or d2 > perp_tol:
            continue
        s1 = (w.p1.x() - wall.p1.x()) * u.x() + (w.p1.y() - wall.p1.y()) * u.y()
        s2 = (w.p2.x() - wall.p1.x()) * u.x() + (w.p2.y() - wall.p1.y()) * u.y()
        if max(s1, s2) > 0.5 and min(s1, s2) < length - 0.5:   # spans overlap
            out.append(w)
    return out


# ------------------------------------------------------ topology ops (P3.4)
# The SCENE half of the planner/applier split. The decision logic lives once,
# pure, in `design.topology`; everything here either feeds it a view of the live
# scene or executes the delta it returns. See that module's header for why this
# is neither "lift the scene to a Design" nor a scene-side reimplementation.

def _corner_at(pos, cells, cell, x, y, floor):
    """The existing corner key within SHARE_TOL of (x, y) on `floor`, or None."""
    ci, cj = round(x / cell), round(y / cell)
    best, best_d = None, SHARE_TOL
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for k in cells.get((floor, ci + di, cj + dj), ()):
                d = math.hypot(pos[k][0] - x, pos[k][1] - y)
                if d <= best_d:
                    best, best_d = k, d
    return best


class _CornerIndex:
    """Wall ends folded into CORNERS -- the vertex adjacency the task line asks
    for, and the single definition of "these ends are the same corner".

    Two ends are one corner when they hold the same `Vertex` OR sit within
    SHARE_TOL of each other. Both halves are needed and neither is redundant:
    identity is the real answer, but P3.1 is split-on-write and load
    deliberately does not weld, so most coincident ends in a loaded plan are
    still distinct objects and only position can see the corner. That second
    half is also, exactly, the 0.6" endpoint hash `_WallIndex` used to keep --
    which is why `joined_at` can move onto this without changing a pixel."""

    def __init__(self, walls):
        self.pos, self.anchor, self.of, self.walls_at = {}, {}, {}, {}
        self._cells, self._seen = {}, {}
        cell = max(SHARE_TOL, 1e-6)
        for w in walls:
            for attr in ("p1", "p2"):
                v = w.end_vertex(attr)
                key = self._seen.get(id(v))
                if key is None:
                    p = v.point()
                    key = _corner_at(self.pos, self._cells, cell,
                                     p.x(), p.y(), w.floor)
                    if key is None:
                        key = len(self.pos)
                        self.pos[key] = (p.x(), p.y())
                        self.anchor[key] = v
                        self._cells.setdefault(
                            (w.floor, round(p.x() / cell),
                             round(p.y() / cell)), []).append(key)
                    self._seen[id(v)] = key
                self.of[(id(w), attr)] = key
                self.walls_at.setdefault(key, []).append(w)

    def joined(self, wall, attr) -> bool:
        """True when another wall meets `wall` at this end -- a degree query,
        where `_WallIndex` ran a 3x3 cell search per call."""
        return len(self.walls_at.get(self.of.get((id(wall), attr)), ())) > 1

    def vertex_at(self, p, floor):
        """The corner `Vertex` at scene point `p` on `floor`, or None -- the
        point-keyed lookup a room outline needs to adopt the corner its walls
        already meet at (P3.5)."""
        key = _corner_at(self.pos, self._cells, max(SHARE_TOL, 1e-6),
                         p.x(), p.y(), floor)
        return self.anchor.get(key) if key is not None else None


def graph_from_scene(scene, floor=None):
    """A `GraphView` of the live wall network for `design.topology`'s planners.

    THE CORNERS ARE THE VERTEX ADJACENCY the task line calls for: two ends
    holding the same `Vertex` object are one corner, and ends within SHARE_TOL
    of one another are folded into one corner for planning. The fold is not a
    concession -- P3.1 is split-on-write and P3.3 shares only the corners a drag
    touches, so most coincident ends in a loaded plan are still distinct
    objects. Folding by position is what lets the planner see the corner that is
    physically there; the applier then makes it real, by adopting one `Vertex`.

    `floor=None` views every floor at once. Level is part of the planner's
    grouping key, so floors stay apart there rather than by one pass per floor.
    Open (dashed) and grouped walls are excluded, exactly as coalesce excluded
    them."""
    if scene is None:
        return GraphView([], {}, {})
    walls = sorted((w for w in scene.items()
                    if isinstance(w, WallItem)
                    and w.group() is None and w.length() > 1e-6
                    and (floor is None or w.floor == floor)),
                   key=lambda w: (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y(),
                                  w.wall_type))
    corners = _CornerIndex(walls)
    views = [WallView(w, w.floor, corners.of[(id(w), "p1")],
                      corners.of[(id(w), "p2")], w.wall_type,
                      tuple(OpeningView(i, op.s, op.width, (op.kind, op.code),
                                        op.anchor_from())
                            for i, op in enumerate(w.openings)))
             for w in walls]
    return GraphView(views, corners.pos, corners.anchor)


def _adopt_end(wall, attr, vertex, xy):
    """Put a merged end on the corner the plan named -- REAL SHARING, which is
    what coalesce never created -- or, when the plan named none, move it to the
    planned coordinate. The second case splits on write, correctly: that end is
    landing where no corner was."""
    if vertex is not None:
        if wall.end_vertex(attr) is not vertex:
            wall.set_end_vertex(attr, vertex)
        return
    setattr(wall, attr, QPointF(xy[0], xy[1]))


def apply_merge_plan_to_scene(scene, plan, rebuild=True):
    """Execute a merge delta on the live items, touching ONLY what it names.

    No full-plan rebuild, so selection, in-flight drag state, group membership
    and the P3.1 uids all survive -- the property that disqualified
    lift-to-Design-and-apply-back. Returns the surviving walls."""
    survivors = []
    for m in plan:
        surv = m.survivor
        if sip.isdeleted(surv) or surv.scene() is not scene:
            continue
        # openings are read off the PRE-merge geometry, before anything moves
        specs = []
        for po in m.openings:
            src = po.wall
            if sip.isdeleted(src) or po.index >= len(src.openings):
                continue
            op = src.openings[po.index]
            specs.append((op if src is surv else None, op.kind, op.code,
                          po.s, op.door_type, op.swing))
        rooms = list(surv.rooms)               # the survivor borders them all
        for w in m.absorbed:
            if sip.isdeleted(w):
                continue
            for r in w.rooms:
                if r not in rooms:
                    rooms.append(r)
            for r in list(w.rooms):
                r.unbind_wall(w)
            if w.scene() is not None:
                scene.removeItem(w)
        _adopt_end(surv, "p1", m.v1, m.p1)
        _adopt_end(surv, "p2", m.v2, m.p2)
        keep = []
        for op, kind, code, s, door_type, swing in specs:
            if op is not None:                 # the survivor's own: it rides on
                op.s = s
                keep.append(op)
                continue
            try:
                new = OpeningItem(surv, kind, code, s)
            except ValueError as exc:          # wider than the merged wall
                report_opening_failure(surv.scene(), surv, kind, code, s,
                                       f"{exc} (merging collinear walls)")
                continue
            new.door_type, new.swing = door_type, swing
            keep.append(new)
        for op in surv.openings:               # deduped away (defect 9)
            if op not in keep and not sip.isdeleted(op):
                op.setParentItem(None)
                if op.scene() is not None:
                    scene.removeItem(op)
        surv.openings = keep
        for r in rooms:
            r.bind_wall(surv)
        survivors.append(surv)
        if rebuild:
            surv.rebuild()
    return survivors


def merge_collinear_scene(scene, floor=None, perp_tol=None, max_passes=6):
    """Merge every collinear run in the scene -- P3.4's replacement for
    coalesce, and the same planner `design.topology.merge_collinear` runs, so a
    scene and its document merge identically by construction.

    `perp_tol` defaults to the wall-snap grid, which is the tolerance coalesce
    used and therefore exactly the set of duplicates the editor has always
    cleaned up. Returns the number of walls absorbed."""
    if scene is None:
        return 0
    if perp_tol is None:
        perp_tol = SETTINGS.get("wall_snap_in", WALL_SNAP_DEFAULT)
    absorbed = 0
    for _ in range(max_passes):                # runs are maximal; a fuse only
        plan = plan_merge_collinear(graph_from_scene(scene, floor),
                                    perp_tol=perp_tol)
        if not plan:
            break
        apply_merge_plan_to_scene(scene, plan)
        absorbed += sum(len(m.absorbed) for m in plan)
    return absorbed


def share_coincident_ends(scene, floor=None):
    """Fold wall ends that already sit at the same point onto ONE `Vertex`.

    THE HALF `weld_all` NEVER HAD. A welded corner used to be two coordinates
    that happened to agree -- which is exactly what P3.3's drag then had to
    rediscover by scanning, at every press. "What counts as one corner" is
    decided by `graph_from_scene`'s fold, so this module has one definition of
    it and not two.

    Adopting a corner can move an end by up to SHARE_TOL (0.6"). That is the
    schema's own `vertex_weld_in`: at or below it two points ARE one vertex, so
    by the document's own definition nothing moved (P2.1's noise-floor rule).
    Returns the number of ends rebound."""
    view = graph_from_scene(scene, floor)
    rebound = 0
    for wv in view.walls:
        for attr, key in (("p1", wv.v1), ("p2", wv.v2)):
            anchor = view.anchor.get(key)
            if anchor is not None and wv.key.end_vertex(attr) is not anchor:
                wv.key.set_end_vertex(attr, anchor)
                rebound += 1
    return rebound


def split_body_landings(scene, floor=None, max_passes=6):
    """Split every wall on which another wall's END lands -- the split rule's
    second half, applied plan-wide rather than at one drag's press.

    A pass splits each wall at most once, so it iterates. A landing inside a
    doorway is declined by `split_wall_at` (P3.6's case) and stays unsplit.
    Returns the number of splits made."""
    made = 0
    for _ in range(max_passes):
        view = graph_from_scene(scene, floor)
        plans, done = [], set()
        for wv in view.walls:
            if id(wv.key) in done:
                continue
            for key, p in view.pos.items():
                if key in (wv.v1, wv.v2):
                    continue
                sp = plan_split_edge(view, wv.key, p[0], p[1])
                if sp is not None and not sp.straddled:
                    plans.append(sp)
                    done.add(id(wv.key))
                    break
        if not plans:
            break
        for sp in plans:
            if apply_split_plan_to_scene(scene, sp) is not None:
                made += 1
    return made


def _snap_wall_ends(scene, wall):
    """Move each free end of `wall` onto a nearby wall's end, or onto the body
    of a wall it stops on (T-junction), within JOIN_TOL. Never grows a wall
    toward a far one -- if it doesn't reach, the gap is left for the user.

    Lifted from `WallItem.join_endpoints` (P3.4 (iii)) so that method can be
    retired. It stays a COORDINATE snap on purpose: closing a 9" gap is a
    geometry repair, not topology, and it is the only way a drawn or
    pixel-extracted plan closes its junctions at all. The topology follows in
    `share_coincident_ends`, once the ends actually coincide."""
    moved = 0
    for attr, other in (("p1", "p2"), ("p2", "p1")):
        p = getattr(wall, attr)
        q = nearest_wall_endpoint(scene, p, JOIN_TOL, exclude=wall)
        if q is None:
            hit = nearest_wall_body(scene, p, JOIN_TOL, exclude=wall)
            if hit is not None:
                target, q = hit
                ip = axis_wall_intersection(target, getattr(wall, other), p)
                if ip is not None and QLineF(ip, p).length() <= JOIN_TOL * 2:
                    q = ip
        if q is not None:
            if QLineF(q, p).length() > 1e-9:
                moved += 1
            setattr(wall, attr, q)
    return moved


def weld_wall_ends(scene, wall, rebuild=True):
    """Weld ONE wall's ends -- P3.4 (iii)'s replacement for
    `WallItem.join_endpoints`, called on draw release.

    Snap, then SHARE: once the geometry lands, the ends that are now coincident
    are folded onto one `Vertex`, so a drawn corner is topology from the moment
    it is drawn rather than two coordinates a later drag must rediscover.

    Deliberately does NOT split a wall whose body this end landed on, though
    the machinery is right here. That is a real edit to a wall the user did not
    touch, and making it silently on every draw is a wider blast radius than a
    call-site migration should have. It belongs to the EXPLICIT pass
    (`normalize_walls`) -- and a drag makes it at press anyway (P3.4 (ii))."""
    if scene is None or wall is None or wall.scene() is None:
        return
    _snap_wall_ends(scene, wall)
    share_coincident_ends(scene, wall.floor)
    if rebuild:
        wall.rebuild()


def weld_scene(scene, max_passes=6):
    """Weld the whole plan -- P3.4 (iii)'s replacement for `weld_all`.

    Two stages, deliberately different kinds of thing: the GEOMETRY snap that
    closes gaps (iterated to a fixed point, as `weld_all` was, so a welded plan
    doesn't move on a further pass), then the TOPOLOGY `weld_all` had no way to
    do -- folding the now-coincident ends onto one vertex.

    IT DOES NOT SPLIT BODY LANDINGS, and that is the same rule `weld_wall_ends`
    follows: splitting is an edit to a wall the user did not touch, so it
    belongs to the EXPLICIT pass (`normalize_walls`) and nowhere else. Applied
    here it would silently turn a 5-wall extracted plan into a 7-wall one --
    correct topology, but a behaviour change smuggled in under a call-site
    migration. P3.5 will want plan-wide planarity for `enclosing_face`; that is
    P3.5's to ask for, through the pass that exists for it.

    Returns `(moved, shared)`."""
    if scene is None:
        return (0, 0)
    moved = 0
    for _ in range(max_passes):
        walls = sorted((w for w in scene.items()
                        if isinstance(w, WallItem)
                        and w.group() is None),
                       key=lambda w: (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y()))
        step = sum(_snap_wall_ends(scene, w) for w in walls)
        moved += step
        if not step:
            break
    return moved, share_coincident_ends(scene)


def normalize_walls(scene):
    """THE EXPLICIT PLAN-WIDE NORMALIZATION -- Edit ▸ Coalesce all walls now.

    The menu item outlives the implementation it was named after. Same command,
    same user intent ("tidy my walls"), new machinery: merge every collinear
    run, then weld -- close the gaps, fold coincident ends onto one vertex, and
    split a wall wherever another's end lands on its body. Ungated by
    `auto_coalesce`, because the user asked for it explicitly.

    Returns `(merged, moved, shared, split)`."""
    if scene is None:
        return (0, 0, 0, 0)
    merged = merge_collinear_scene(scene)
    moved, shared = weld_scene(scene)
    return merged, moved, shared, split_body_landings(scene)


def merge_wall(scene, wall, perp_tol=None):
    """Merge just the run `wall` sits in -- P3.4 (iii)'s replacement for
    `coalesce_wall`, and gated by the same `auto_coalesce` setting.

    `wall` is forced to be the run's SURVIVOR, which is not a detail: the
    caller has just drawn or dragged that item and holds a reference to it,
    and it carries the selection. The planner takes the run's first wall in the
    caller's own order, so putting `wall` first is all it takes to say so."""
    if not SETTINGS.get("auto_coalesce", True):
        return wall
    if (scene is None or wall is None or wall.scene() is None
            or wall.group() is not None or wall.length() < 1e-6):
        return wall
    if perp_tol is None:
        perp_tol = SETTINGS.get("wall_snap_in", WALL_SNAP_DEFAULT)
    view = graph_from_scene(scene, wall.floor)
    view = view._replace(walls=sorted(view.walls, key=lambda v: v.key is not wall))
    plan = [m for m in plan_merge_collinear(view, perp_tol=perp_tol)
            if m.survivor is wall]
    if plan:
        apply_merge_plan_to_scene(scene, plan)
    return wall


def merge_all(scene):
    """Plan-wide auto-merge (load, import, ungroup) -- P3.4 (iii)'s replacement
    for `coalesce_all`, gated by `auto_coalesce` exactly as that was. Returns
    the number of walls absorbed."""
    if not SETTINGS.get("auto_coalesce", True):
        return 0
    return merge_collinear_scene(scene)


def apply_split_plan_to_scene(scene, split, rebuild=True):
    """Execute a split delta on the live items. The source wall keeps its
    identity and becomes the FIRST segment; a new `WallItem` takes the second.

    Vertex-native throughout: the split corner and the far corner are both
    handed over with `set_end_vertex`, so a split costs ZERO split-on-writes and
    whatever sharing the far end already had survives it."""
    src = split.wall
    if sip.isdeleted(src) or src.scene() is not scene:
        return None
    at = QPointF(split.at[0], split.at[1])
    vsplit = split.v if split.v is not None else Vertex.at(at)
    far = src.end_vertex("p2")
    moved = [(src.openings[po.index], po.s) for po in split.move_openings
             if po.index < len(src.openings)]
    kept = [src.openings[po.index] for po in split.keep_openings
            if po.index < len(src.openings)]

    seg = WallItem(at, QPointF(far.point()), src.wall_type)
    seg.floor = src.floor
    seg.set_end_vertex("p1", vsplit)
    seg.set_end_vertex("p2", far)
    scene.addItem(seg)
    src.set_end_vertex("p2", vsplit)

    for op, s in moved:
        try:
            new = OpeningItem(seg, op.kind, op.code, s)
        except ValueError as exc:              # wider than the second segment
            report_opening_failure(seg.scene(), seg, op.kind, op.code, s,
                                   f"{exc} (splitting a wall)")
            continue
        new.door_type, new.swing = op.door_type, op.swing
        seg.openings.append(new)
        op.setParentItem(None)
        if op.scene() is not None:
            scene.removeItem(op)
    src.openings = kept
    for r in list(src.rooms):                  # both halves run the same edges
        r.bind_wall(seg)
    if rebuild:
        src.rebuild()
        seg.rebuild()
    return seg


def split_wall_at(scene, wall, p, on_seg_tol=ON_SEG_TOL, report=None):
    """Split `wall` at the scene point `p` -- THE SPLIT RULE'S SECOND HALF:
    a vertex landing on another wall's body splits that wall. Returns the new
    segment, or None when there is nothing to split.

    **THE DECLINE IS GONE (R2c).** A split whose point falls inside an opening
    used to return None here while `topology.split_edge` raised -- one planner,
    two policies. Both are retired for the same reason, and it is defect 17's:
    a gesture that silently does nothing is the worst of the three options, and
    keeping a second case of it on purpose is how folklore starts. The split now
    happens; the opening lands on the segment holding its anchor (R2b) and is
    appended to `report` if the caller passes one.

    The remaining asymmetry is not one: `topology.split_edge` and this take the
    same delta from the same planner and now do the same thing with it. What
    differs is only where each one's report is surfaced -- the conversion report
    for a load, a status line for an edit (R5)."""
    if scene is None or wall is None:
        return None
    split = plan_split_edge(graph_from_scene(scene, wall.floor), wall,
                            p.x(), p.y(), on_seg_tol=on_seg_tol)
    if split is None:
        return None
    if split.straddled and report is not None:
        for po in split.straddled:
            op = wall.openings[po.index] if po.index < len(wall.openings) else None
            report.append(
                f"{op.kind if op else 'opening'} "
                f"{op.code if op else po.index} on a wall at "
                f"({wall.p1.x():.0f}, {wall.p1.y():.0f}): a junction lands "
                f"inside it, so it no longer fits the segment it sits on")
    return apply_split_plan_to_scene(scene, split)


def delete_wall(scene, wall, settle=True):
    """Delete `wall` outright (P4.1).  A bordering room SURVIVES by
    construction: its stored outline holds the corners (P3.2/P3.5), so the
    vacated edge simply becomes an open edge (`wall: null`, drawn dashed by
    the room itself).  Nothing is fractured, trimmed or rebound -- deletion
    is deletion."""
    if scene is None or wall.scene() is None:
        return
    for r in list(wall.rooms):
        r.unbind_wall(wall)
    scene.removeItem(wall)
    if settle:
        rebuild_all_walls(scene)


def wall_endpoint_open(scene, p: QPointF, ignore=()) -> bool:
    """True when `p` is a free, dangling wall end: no other (non-open) wall has
    an endpoint within JOIN_TOL of it.  Walls in `ignore` are skipped (the
    endpoint's own wall, and the wall being drawn).

    THIS IS RIGHTLY SPATIAL, AND IT STAYS THAT WAY -- it is not a survivor of
    the pre-vertex world awaiting migration to vertex degree, so please do not
    "finish the job" by converting it.

    The tolerance is JOIN_TOL, the GESTURE tolerance, and gesture questions are
    inherently spatial. Degree answers the MODELLING question ("are these ends
    one corner?"); this answers the AIMING question ("is there something near
    enough to snap to?"), and those are different questions with different
    right answers. Degree cannot serve here even in principle, because the ends
    worth offering the user are precisely the ones NOT yet welded -- a degree
    query would report every one of them as free and the snap would have
    nothing to aim at.

    (`WallItem._joined_at` is the one that did migrate, at P3.4 (iii): its
    tolerance was SHARE_TOL, it asked the modelling question, and vertex
    adjacency answers it exactly.)"""
    if scene is None:
        return False
    for w in scene.items():
        if not isinstance(w, WallItem) or w in ignore:
            continue
        if (QLineF(w.p1, p).length() < JOIN_TOL
                or QLineF(w.p2, p).length() < JOIN_TOL):
            return False
    return True


def wall_bbox(w) -> QRectF:
    """A wall's scene bbox padded by its thickness."""
    t = w.t
    return QRectF(QPointF(min(w.p1.x(), w.p2.x()), min(w.p1.y(), w.p2.y())),
                  QPointF(max(w.p1.x(), w.p2.x()), max(w.p1.y(), w.p2.y()))
                  ).adjusted(-t, -t, t, t)


class _WallBBoxIndex:
    """Walls hashed by bbox cells so 'which walls are near this box' is
    O(local) instead of a scan.

    RIGHTLY SPATIAL, PERMANENTLY -- the third of three, and the reason it is
    worth naming as a category. P3.4 (iii) reframed `wall_endpoint_open` this
    way (its tolerance is JOIN_TOL, the GESTURE tolerance, and "is there
    something near enough to snap to?" is inherently a question about distance,
    which degree cannot answer even in principle). P3.4 (iv) then REFUSED the
    adjacency swap in `_compute_wall_junctions` for the same kind of reason: two
    walls can cross mid-span sharing no corner at all, so adjacency finds
    nothing where the bodies genuinely overlap.

    This index is what that refusal runs on. P3.4 (iv) forecast it as P3.5's on
    the grounds that the memoized room dirty-check was its last caller; P3.5
    deleted that check and the index stayed, because the same sub-commit's
    junction ruling had already created the caller that outlives it. A line dies
    when its LAST caller dies -- and here one correct decision invalidated
    another's forecast, which is what per-task ledgers are for.

    None of the three is a survivor of the old world. They are the queries whose
    question is about SPACE rather than about topology, and vertex adjacency was
    never the right instrument for any of them."""

    CELL = 60.0          # 5 ft cells

    def __init__(self, scene, floor=None):
        # floor=None indexes every wall; pass a floor to index only that floor's
        # walls (the junction pass scopes neighbours to the wall's own floor).
        self.cells = {}
        for w in (scene.items() if scene is not None else []):
            if not isinstance(w, WallItem):
                continue
            if floor is not None and w.floor != floor:
                continue
            wb = wall_bbox(w)
            for i in range(int(wb.left() / self.CELL),
                           int(wb.right() / self.CELL) + 1):
                for j in range(int(wb.top() / self.CELL),
                               int(wb.bottom() / self.CELL) + 1):
                    self.cells.setdefault((i, j), []).append((w, wb))

    def near(self, box):
        seen, out = set(), []
        for i in range(int(box.left() / self.CELL),
                       int(box.right() / self.CELL) + 1):
            for j in range(int(box.top() / self.CELL),
                           int(box.bottom() / self.CELL) + 1):
                for w, wb in self.cells.get((i, j), ()):
                    if id(w) not in seen and wb.intersects(box):
                        seen.add(id(w))
                        out.append(w)
        return out


# --------------------------------------------------- R5: one vocabulary
def describe_opening(wall, kind, code, s, why) -> str:
    """One entry in the `openings_failed` vocabulary (P3.6 / R5): what the
    opening was, which wall it was going on, where it was aimed, and why it
    could not be placed. The same sentence shape the walk files, so a load
    report and an edit report read alike."""
    where = (f"({wall.p1.x():.0f}, {wall.p1.y():.0f})"
             if wall is not None else "an unknown wall")
    at = f" at {s:.0f}\"" if s is not None else ""
    return f"{kind} {code} on the wall at {where}{at}: {why}"


def report_opening_failure(scene, wall, kind, code, s, why):
    """File an opening that could not be placed, on the SCENE.

    P3.6 replaces eight `except ValueError: continue` sites that dropped an
    opening in silence -- including on load, which is defect 6's "incl. on
    load". Scene-scoped rather than global for the same reason the weld
    baseline is: two windows must not share a report. `MainWindow` drains it at
    the debounce point and says it once."""
    if scene is None:
        return
    if not hasattr(scene, "_fp_opening_failures"):
        scene._fp_opening_failures = []
    scene._fp_opening_failures.append(
        describe_opening(wall, kind, code, s, why))


def drain_opening_failures(scene) -> list:
    """Take and clear whatever has been filed since the last drain."""
    out = list(getattr(scene, "_fp_opening_failures", ()) or ())
    if out:
        scene._fp_opening_failures = []
    return out


def rebuild_all_walls(scene):
    """Rebuild every wall's geometry and the junction clips.

    IT NO LONGER TOUCHES ROOMS (P3.5). This used to end in `refresh_rooms`,
    which re-detected every room whose nearby walls had changed -- the editor's
    hot path, and the reason a wall edit cost a raster flood-fill plus a planar
    face walk. A room's region now DERIVES from its outline, and the outline
    holds the very vertices the walls hold, so a wall edit updates the rooms it
    borders before this function is even called."""
    if scene is None:
        return
    index = _WallIndex(scene)                # shared: rebuild is O(local), not
    walls = [it for it in scene.items() if isinstance(it, WallItem)]
    for it in walls:                         # O(all walls) per wall
        it.rebuild(cascade=False, index=index)
    _compute_wall_junctions(scene, walls)


def _compute_wall_junctions(scene, walls=None):
    """For each wall, cache an outline clip = its bounds minus the bodies of the
    walls it overlaps, so the dark outline is drawn only on the OUTER boundary
    of the wall network -- T/cross/L joints read as one solid piece, not a seam.
    Runs once after every wall's footprint (`_solid`) is up to date."""
    if walls is None:
        walls = [it for it in scene.items() if isinstance(it, WallItem)]
    bbi = _WallBBoxIndex(scene)
    for w in walls:
        wb = w._solid.boundingRect()
        union = QPainterPath()
        found = False
        for other in bbi.near(wb):
            if (other is w or not isinstance(other, WallItem)
                    or other._solid.isEmpty()
                    or other.floor != w.floor):   # junctions don't cross floors
                continue
            if (other._solid.boundingRect().intersects(wb)
                    and other._solid.intersects(w._solid)):
                union = union.united(other._solid)
                found = True
        if found:
            clip = QPainterPath()
            clip.addRect(wb.adjusted(-2, -2, 2, 2))
            w._outline_clip = clip.subtracted(union)
        else:
            w._outline_clip = None
        w.update()


class WallItem(QGraphicsItem):
    """A straight wall segment.  Local coords == scene coords (pos stays 0,0).

    Geometry is defined by endpoints p1, p2 plus a standard thickness.
    Door/window OpeningItems are child items; each remembers its distance
    `s` along the wall from p1, so they ride along when the wall moves.
    """

    def __init__(self, p1: QPointF, p2: QPointF, wall_type: str = "exterior"):
        super().__init__()
        self.wall_type = wall_type
        # P3.1: the geometry lives in VERTICES now. p1/p2 are read-through
        # properties over them, so every existing caller keeps working; two
        # wall ends referencing the SAME Vertex object are the same corner.
        self._v1 = Vertex.at(p1)
        self._v2 = Vertex.at(p2)
        self.floor = active_floor()   # tagged with the active floor (load overrides)
        self.openings = []            # OpeningItem children
        self.rooms = []               # RoomItems this wall borders ([] = free)
        self._corners_unlocked = False  # endpoints draggable while in a room
        self._drawing = False         # True while being rubber-banded
        self._mode = None             # None | 'p1' | 'p2' | 'move'
        self._vmoves = []             # P3.3: the corners a body-drag moves
        self._path = QPainterPath()
        self._solid = QPainterPath()     # body footprint, no opening holes
        self._outline_clip = None        # outline-clip so junctions read solid
        self._hit = QPainterPath()
        self._bounds = QRectF()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(WALL_Z)           # above the translucent room fill (3)
        self.rebuild()

    # -- vertices (P3.1) -----------------------------------------------------
    # p1/p2 read through to the vertex table; ASSIGNMENT IS SPLIT-ON-WRITE --
    # it mints a fresh vertex for this end and leaves any sharer where it was,
    # preserving today's independent-ends semantics exactly. Shared movement is
    # P3.3's wall-move operation, never a side effect of assignment.
    @property
    def v1(self) -> str:
        """Stable uid of the start vertex (persistent across edits)."""
        return self._v1.uid

    @property
    def v2(self) -> str:
        return self._v2.uid

    @property
    def p1(self) -> QPointF:
        return self._v1.point()

    @p1.setter
    def p1(self, value):
        v = getattr(self, "_v1", None)
        self._v1 = v.moved_to(value) if v is not None else Vertex.at(value)
        self._carry_anchors(v, self._v1)

    @property
    def p2(self) -> QPointF:
        return self._v2.point()

    @p2.setter
    def p2(self, value):
        v = getattr(self, "_v2", None)
        self._v2 = v.moved_to(value) if v is not None else Vertex.at(value)
        self._carry_anchors(v, self._v2)

    def _carry_anchors(self, old, new):
        """Keep every opening dimensioned off `old` dimensioned off `new`.

        THE END DID NOT CHANGE -- its coordinate did. Assigning `p1`/`p2` is
        split-on-write, so the same corner comes away on a fresh `Vertex` with a
        fresh uid, and an anchor still naming the old object is orphaned. An
        orphaned anchor re-seats on `p1`, which for an opening dimensioned off
        `p2` MIRRORS it down the wall. Measured on `planc1` before this existed:
        12 of 41 openings changed position on load.

        Deliberately NOT what `set_end_vertex` does for a vertex somewhere else
        -- that is a swap or an explicit share, where the anchor must go on
        naming the corner it names. See `_fuse_anchors`."""
        if old is None or old is new:
            return
        for op in getattr(self, "openings", ()):
            if op.anchor_v is old:
                op.anchor_v = new

    def _fuse_anchors(self, old, new):
        """The WELD case: two ends at one corner fuse onto a single `Vertex`.
        Same physical corner, so an anchor on the absorbed vertex follows it --
        but only when the replacement really is in the same place. A
        `set_end_vertex` to a vertex ELSEWHERE is a swap or a deliberate share,
        and there the anchor must stay put or reversing a wall would move its
        openings (R1(b)). A RELOCATION lands here too and is left alone on
        purpose: it carries its uid, so `_anchor_attr` re-seats it for free."""
        if old is None or old is new:
            return
        a, b = old.point(), new.point()
        if abs(a.x() - b.x()) > SHARE_TOL or abs(a.y() - b.y()) > SHARE_TOL:
            return
        for op in getattr(self, "openings", ()):
            if op.anchor_v is old:
                op.anchor_v = new

    def end_vertex(self, attr: str) -> Vertex:
        """The Vertex object behind `p1` or `p2` -- the corner's IDENTITY, not
        its position. Two ends are the same corner iff this returns the same
        object for both (`is`, never `==`)."""
        return self._v1 if attr == "p1" else self._v2

    def set_end_vertex(self, attr: str, vertex: Vertex):
        """Point this end AT `vertex`, sharing it.

        The deliberate counterpart to assigning `p1`/`p2`, which splits on write
        and therefore cannot express sharing at all. P3.3's wall move is the
        first caller: it shares the corners it is about to move, then moves the
        vertex once for every end on it."""
        old = self._v1 if attr == "p1" else self._v2
        if attr == "p1":
            self._v1 = vertex
        else:
            self._v2 = vertex
        self._fuse_anchors(old, vertex)

    @property
    def primary_room(self):
        """A representative owning room (the first), or None when free."""
        return self.rooms[0] if self.rooms else None

    def itemChange(self, change, value):
        # when removed from the scene, release every room that borders this wall
        # so no RoomItem.walls keeps a reference to a deleted item
        if (change == QGraphicsItem.GraphicsItemChange.ItemSceneChange
                and value is None and self.rooms):
            for r in list(self.rooms):
                if not sip.isdeleted(r):
                    r.unbind_wall(self)
        return super().itemChange(change, value)

    # -- basic geometry ------------------------------------------------------
    @property
    def t(self) -> float:
        return EXTERIOR_T if self.wall_type == "exterior" else INTERIOR_T

    def length(self) -> float:
        return math.hypot(self.p2.x() - self.p1.x(), self.p2.y() - self.p1.y())

    def angle_rad(self) -> float:
        return math.atan2(self.p2.y() - self.p1.y(), self.p2.x() - self.p1.x())

    def unit(self) -> QPointF:
        length = self.length()
        if length < 1e-9:
            return QPointF(1.0, 0.0)
        return QPointF((self.p2.x() - self.p1.x()) / length,
                       (self.p2.y() - self.p1.y()) / length)

    def point_at(self, s: float) -> QPointF:
        u = self.unit()
        return QPointF(self.p1.x() + u.x() * s, self.p1.y() + u.y() * s)

    def s_of(self, p: QPointF) -> float:
        """Project a scene point onto the wall axis -> distance from p1."""
        u = self.unit()
        s = (p.x() - self.p1.x()) * u.x() + (p.y() - self.p1.y()) * u.y()
        return max(0.0, min(self.length(), s))

    # -- geometry cache ------------------------------------------------------
    def _joined_at(self, attr: str, index=None) -> bool:
        """True when another wall meets this wall at `attr` ("p1" / "p2").

        A VERTEX-DEGREE question (P3.4 (iii)), where it used to be a 0.6"
        coordinate search. The corner fold behind it treats same-`Vertex` and
        within-0.6" ends alike, so the answer is unchanged on a plan that was
        never welded -- and on one that was, it is now the real question rather
        than a proximity proxy for it."""
        if index is not None:
            return index.joined_at(self, attr)
        sc = self.scene()
        if sc is None:
            return False
        p = getattr(self, attr)
        for it in sc.items():
            if isinstance(it, WallItem) and it is not self:
                if (QLineF(p, it.p1).length() < 0.6
                        or QLineF(p, it.p2).length() < 0.6):
                    return True
        return False

    def rebuild(self, cascade=True, index=None):
        """Recompute the painted path (with openings cut out) and hit shape.

        When `cascade`, also rebuild any coincident party walls so they reopen
        for this wall's openings (and re-solidify when an opening leaves).
        rebuild_all_walls passes cascade=False since it rebuilds every wall."""
        self.prepareGeometryChange()
        length, t, ang = self.length(), self.t, self.angle_rad()

        # extend joined ends by half a thickness so corners fill in solid
        ext1 = t * 0.5 if self._joined_at("p1", index) else 0.0
        ext2 = t * 0.5 if self._joined_at("p2", index) else 0.0

        body = QPainterPath()
        body.addRect(QRectF(-ext1, -t / 2, length + ext1 + ext2, t))
        solid_local = QPainterPath(body)   # footprint before openings are cut
        holes = QPainterPath()
        for op in self.openings:
            # NO CLAMP (P3.6). This used to read
            #     op.s = min(max(op.s, half), max(half, length - half))
            # which silently SLID a door back onto a wall that had shrunk under
            # it -- repairing stored data on the render path, where nobody could
            # see it happen. An opening that no longer fits is a fact about the
            # plan (`op.fits()`), reported, not corrected in passing.
            half = op.width / 2
            holes.addRect(QRectF(op.s - half, -t / 2 - 0.5, op.width, t + 1.0))
        # open the body where a coincident wall carries a door/window, so a
        # plain party wall doesn't cover the opening on the wall next to it
        u = self.unit()
        for w in coincident_walls(self.scene(), self, index):
            for op in w.openings:
                p = w.point_at(op.s)
                sl = ((p.x() - self.p1.x()) * u.x()
                      + (p.y() - self.p1.y()) * u.y())
                half = op.width / 2
                if -half < sl < length + half:
                    holes.addRect(QRectF(sl - half, -t / 2 - 0.5,
                                         op.width, t + 1.0))
        if not holes.isEmpty():
            body = body.subtracted(holes)

        tr = QTransform()
        tr.translate(self.p1.x(), self.p1.y())
        tr.rotateRadians(ang)
        self._path = tr.map(body)
        self._solid = tr.map(solid_local)
        # cleared here; rebuild_all_walls' junction pass recomputes the clip so
        # neighbouring wall bodies hide this wall's inner seams (T/cross joints)
        self._outline_clip = None

        # hit shape: stroked centreline (no holes -> easy to click)
        line = QPainterPath()
        line.moveTo(self.p1)
        line.lineTo(self.p2)
        stroker = QPainterPathStroker()
        stroker.setWidth(max(t, 1.0))
        stroker.setCapStyle(Qt.PenCapStyle.FlatCap)
        self._hit = stroker.createStroke(line)
        if length < 0.01:
            self._hit.addEllipse(self.p1, t, t)

        b = self._path.boundingRect().united(self._hit.boundingRect())
        self._bounds = b.adjusted(-24, -24, 24, 24)   # room for handles/label

        for op in self.openings:
            op.sync()
        self.update()
        if cascade:
            for w in coincident_walls(self.scene(), self):
                w.rebuild(cascade=False)

    # -- QGraphicsItem interface ---------------------------------------------
    def boundingRect(self) -> QRectF:
        return self._bounds

    def shape(self) -> QPainterPath:
        return self._hit

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        ghost = floor_display_mode(self.floor) != "active"
        if ghost:                            # non-active floor: flat gray, no UI
            fill, outline = FLOOR_GHOST, FLOOR_GHOST
        elif self.wall_type == "exterior":
            fill, outline = QColor(60, 62, 68), QColor(25, 25, 25)
        else:
            fill, outline = QColor(150, 152, 158), QColor(25, 25, 25)
        # fill the body with NO outline so overlapping walls read as one solid
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(fill))
        painter.drawPath(self._path)
        # dark outline, clipped to the wall-network's outer boundary so the
        # seams INSIDE a T/cross/L junction don't show (one solid wall)
        painter.save()
        if self._outline_clip is not None:
            painter.setClipPath(self._outline_clip)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(outline, 0))
        painter.drawPath(self._path)
        painter.restore()
        if ghost:                            # skip selection knobs + length label
            return

        lod = option.levelOfDetailFromTransform(painter.worldTransform())
        lod = max(lod, 1e-6)

        if self.isSelected():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(0, 122, 255), 0))
            painter.drawPath(self._path)
            if self._ends_editable():       # endpoint knobs only when active
                hs = 13.0 / lod             # bigger knob -> easier to aim at
                painter.setPen(QPen(QColor(40, 40, 40), 0))
                painter.setBrush(QBrush(QColor(255, 200, 0)))
                for q in (self.p1, self.p2):
                    painter.drawRect(QRectF(q.x() - hs / 2, q.y() - hs / 2,
                                            hs, hs))

        if self.isSelected() or self._drawing:
            u = self.unit()
            n = QPointF(-u.y(), u.x())
            mid = QPointF((self.p1.x() + self.p2.x()) / 2,
                          (self.p1.y() + self.p2.y()) / 2)
            off = self.t / 2 + 12.0 / lod
            tp = QPointF(mid.x() + n.x() * off, mid.y() + n.y() * off)
            f = QFont()
            f.setPixelSize(max(2, int(13.0 / lod)))
            painter.setFont(f)
            painter.setPen(QPen(QColor(0, 90, 200), 0))
            painter.drawText(tp, fmt_ftin(self.length()))

    # -- interaction ----------------------------------------------------------
    def _view_scale(self) -> float:
        sc = self.scene()
        if sc and sc.views():
            return max(sc.views()[0].transform().m11(), 1e-6)
        return 1.0

    def _ends_editable(self) -> bool:
        """Every wall's endpoints are draggable.  In the shared-wall model a
        wall IS the room boundary (not a hidden copy), so the user edits it
        directly: a free wall re-angles/projects, a room wall moves its end
        along the wall axis (pulling a corner away opens that side)."""
        return True

    def mousePressEvent(self, e):
        if self.group() is not None:
            # grouped: let the group own the drag.  Running the wall-slide
            # / join logic on a group child mutates p1/p2 in the wrong
            # coordinate space and join_endpoints/grow_walls can collapse
            # walls -- ignore so the press falls through to the group.
            self._mode = None
            e.ignore()
            return
        if e.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(e)
            return
        sp = e.scenePos()
        # generous endpoint catch radius (~20 px on screen, larger when zoomed
        # in) so the little end-knob is easy to grab without missing -- but
        # never more than a third of the wall, so a SHORT wall keeps a grabbable
        # middle to body-slide perpendicular (else the end zones cover it all)
        tol = max(12.0, 20.0 / self._view_scale())
        ep_tol = min(tol, self.length() / 3.0)
        ends = self._ends_editable()       # endpoints locked while in a room
        near_p1 = ends and QLineF(sp, self.p1).length() <= ep_tol
        near_p2 = ends and QLineF(sp, self.p2).length() <= ep_tol
        ctrl = bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier)
        if ctrl and not (near_p1 or near_p2):
            # Ctrl+click on the body toggles selection-set membership; Ctrl on
            # an endpoint instead starts an angle-snapped drag (handled below)
            self.setSelected(not self.isSelected())
            self._mode = None
            e.accept()
            return
        if not self.isSelected() and not ctrl:
            self.scene().clearSelection()
        self.setSelected(True)
        if self.rooms:                     # bring an owning room to the front
            self.primary_room.raise_to_front()
        # ...then lift THIS wall above its siblings so clicking the wall you
        # want never buries it behind a coincident/crossing room wall
        bring_to_front(self)

        if near_p1:
            self._mode = "p1"
            self._anchor = QPointF(self.p2)
        elif near_p2:
            self._mode = "p2"
            self._anchor = QPointF(self.p1)
        else:
            self._mode = "move"
            self._press = QPointF(sp)
            self._o1 = QPointF(self.p1)
            self._o2 = QPointF(self.p2)
            # the whole collinear side slides as one (so an open-wall gap rides
            # along); perpendicular walls attached to the SIDE's endpoints then
            # stretch -- corner joints fully, T-joints sideways only
            self._slide_u = self.unit()
            self._run = self._collinear_run()
            run_ids = {id(w) for w in self._run}
            run_ends = [(w, a) for w in self._run for a in ("p1", "p2")]
            run_pts = [getattr(w, a) for w, a in run_ends]
            self._attached = []
            self._continuations = []      # collinear -- split, never dragged
            sc, length = self.scene(), self.length()
            ux, uy = self._slide_u.x(), self._slide_u.y()
            if sc is not None:
                for w in sc.items():
                    # SAME LEVEL ONLY (defect 12a). This scan was one of defect
                    # 12's unfiltered paths, and the promotion below raises the
                    # stakes: a cross-floor coincident end used to be a
                    # TRANSIENT mis-drag that ended with the mouse-up, but a
                    # shared vertex carries exactly one level, so sharing across
                    # floors would violate I2 outright or silently rewrite a
                    # wall's level, permanently. Filtered at the loop head, so
                    # cross-level sharing is impossible by construction rather
                    # than avoided by luck.
                    if (not isinstance(w, WallItem) or id(w) in run_ids
                            or w.floor != self.floor):
                        continue
                    for attr in ("p1", "p2"):
                        q = getattr(w, attr)
                        if any(QLineF(q, rp).length() < SHARE_TOL
                               for rp in run_pts):
                            if self._is_continuation(w):
                                self._continuations.append((w, attr))
                            else:
                                # a GROUPED neighbour still follows, but on the
                                # old coordinate path -- grouping duplicates a
                                # room's walls onto the originals, so promoting
                                # one would wire a group member to an outside
                                # wall permanently, and what a group even IS
                                # topologically is P4.5's question. Same
                                # instinct as the `group() is None` gate that
                                # keeps grouped walls out of coalesce.
                                kind = "corner" if w.group() is None else "rigid"
                                self._attached.append((w, attr, QPointF(q), kind))
                        else:
                            vx, vy = q.x() - self.p1.x(), q.y() - self.p1.y()
                            s = vx * ux + vy * uy
                            if (0.0 < s < length
                                    and abs(vy * ux - vx * uy) <= 0.75):
                                self._attached.append((w, attr, QPointF(q), "tee"))
            run_ends = self._split_body_landings(run_ends)
            self._plan_vertex_moves(run_ends)

        if self._mode in ("p1", "p2"):
            moving = self.p1 if self._mode == "p1" else self.p2
            d = QLineF(self._anchor, moving)
            if d.length() > 1e-6:
                self._axis = QPointF(d.dx() / d.length(), d.dy() / d.length())
            else:
                self._axis = QPointF(1.0, 0.0)
        e.accept()

    def _endpoint_target(self, sp: QPointF, mods) -> QPointF:
        """Lengthen / shorten this wall.  The end rides the wall's own axis,
        grid-snapped, and STICKS to the projected line of a close orthogonal
        wall when it lines up (so you can pull an end into a corner) -- it
        never fuses to another wall's endpoint or body.  Shift = free re-angle;
        Ctrl = re-angle in fixed increments (45 deg etc.)."""
        if mods & Qt.KeyboardModifier.ShiftModifier:
            return wall_snap(QPointF(sp))          # free re-angle, grid only
        if mods & Qt.KeyboardModifier.ControlModifier:
            return self._angle_snapped_target(sp)
        return self._axis_target(sp)

    def _angle_snapped_target(self, sp: QPointF) -> QPointF:
        """Ctrl-drag: swing the dragged end around the anchored end in fixed
        angular increments (SETTINGS['rotate_snap_deg'], default 15 deg), with a
        grid-snapped length -- so the user can build 45 deg and other off-axis
        walls, not just lengthen along the existing axis."""
        o = self._anchor
        dx, dy = sp.x() - o.x(), sp.y() - o.y()
        if math.hypot(dx, dy) < 1e-6:
            dx, dy = self._axis.x(), self._axis.y()
        step = math.radians(max(1.0, SETTINGS.get("rotate_snap_deg", 15.0)))
        ang = round(math.atan2(dy, dx) / step) * step
        length = max(MIN_WALL_LEN, wall_snap_len(math.hypot(dx, dy)))
        return QPointF(o.x() + math.cos(ang) * length,
                       o.y() + math.sin(ang) * length)

    def _axis_target(self, sp: QPointF) -> QPointF:
        o, u = self._anchor, self._axis
        s = (sp.x() - o.x()) * u.x() + (sp.y() - o.y()) * u.y()
        proj = self._project_to_orthogonal(o, u, s)
        s = proj if proj is not None else wall_snap_len(s)
        if s < MIN_WALL_LEN:                        # never collapse the wall
            s = MIN_WALL_LEN
        return QPointF(o.x() + u.x() * s, o.y() + u.y() * s)

    def _project_to_orthogonal(self, o: QPointF, u: QPointF, s: float):
        """The exact axis distance at which this wall's axis crosses the
        projected line of a NEARBY ORTHOGONAL wall, when the drag is within the
        stick tolerance of it -- else None (so it falls back to the grid).
        Snaps only to such lines, never to endpoints or bodies."""
        sc = self.scene()
        if sc is None:
            return None
        stick = max(WALL_PROJECT_STICK, 16.0 / max(self._view_scale(), 1e-6))
        best_s, best_d = None, stick
        for w in sc.items():
            if (not isinstance(w, WallItem) or w is self
                    or w.length() < 1e-6):
                continue
            v = w.unit()
            if abs(u.x() * v.x() + u.y() * v.y()) > 0.12:      # not orthogonal
                continue
            p = line_intersection(o, u, w.p1, v)
            if p is None:
                continue
            sp_ = (p.x() - o.x()) * u.x() + (p.y() - o.y()) * u.y()
            if sp_ <= MIN_WALL_LEN:                 # behind / at the anchor
                continue
            d = abs(sp_ - s)                         # drag distance to the line
            if d <= best_d and \
                    dist_point_segment(p, w.p1, w.p2) <= WALL_PROJECT_NEAR:
                best_s, best_d = sp_, d
        return best_s

    def _corner_target(self, sp: QPointF, mods) -> QPointF:
        """Endpoint target for a room wall: move the end along the wall
        (Shift = any direction, Ctrl = fixed 15 deg increments), grid-snapped
        and sticking to an orthogonal wall's projected line, WITHOUT fusing to
        neighbours -- so the corner can be pulled away to open a side."""
        if mods & Qt.KeyboardModifier.ShiftModifier:
            return wall_snap(QPointF(sp))
        if mods & Qt.KeyboardModifier.ControlModifier:
            return self._angle_snapped_target(sp)
        return self._axis_target(sp)

    def _collinear_run(self):
        """The full room 'side' this wall lies on: every wall of the same room
        (real and dashed open walls) that is collinear with it.  Body-sliding
        the wall moves the whole side -- including the open-wall gap -- as one,
        so the dashed segment travels with the wall."""
        if not self.rooms or self.length() < 1e-6:
            return [self]
        u = self.unit()
        run = []
        side = {self}
        for r in self.rooms:
            side.update(r.walls)
        for w in side:
            if w is self:
                run.append(w)
                continue
            if w.length() < 1e-6:
                continue
            wu = w.unit()
            if abs(wu.x() * u.y() - wu.y() * u.x()) > 0.02:   # not parallel
                continue
            d = abs((w.p1.x() - self.p1.x()) * u.y()           # off this line?
                    - (w.p1.y() - self.p1.y()) * u.x())
            if d <= 1.5:
                run.append(w)
        return run

    def _is_continuation(self, w) -> bool:
        """True when `w` runs along the SAME LINE as the slide -- a collinear
        continuation past one of the run's endpoints.

        Same parallel tolerance as `_collinear_run`, because it is the same
        question asked of a wall that answered no to being in the run (it
        belongs to another room, or to none)."""
        if w.length() < 1e-6:
            return False
        wu, u = w.unit(), self._slide_u
        return abs(wu.x() * u.y() - wu.y() * u.x()) <= 0.02

    def _run_wall_under(self, p: QPointF, tol=0.75):
        """The run wall whose BODY (not its ends) the point `p` lands on."""
        for w in self._run:
            if w.length() < MIN_WALL_LEN:
                continue
            u = w.unit()
            vx, vy = p.x() - w.p1.x(), p.y() - w.p1.y()
            s = vx * u.x() + vy * u.y()
            if (SHARE_TOL < s < w.length() - SHARE_TOL
                    and abs(vy * u.x() - vx * u.y()) <= tol):
                return w
        return None

    def _split_body_landings(self, run_ends):
        """THE SPLIT RULE'S SECOND HALF (P3.4 (ii)). A neighbour's end resting
        on the run's BODY has, until now, had no vertex to be: P3.3 could only
        stretch it sideways from coordinates, which is a split-on-write per
        mouse event. Cutting the run wall at the landing point MAKES the vertex,
        and the landing is then promoted exactly as a corner is -- a T-junction
        stops being a coincidence the drag has to remember and becomes topology.

        Declines quietly wherever it cannot cut: a landing inside a doorway
        (P3.6's case, which `split_wall_at` refuses), or a wall too short to
        halve. Those stay `tee` on P3.3's coordinate path, so the worst case is
        the previous behaviour rather than a broken drag.

        Returns the run_ends, extended with each new segment's two ends."""
        if not any(kind == "tee" for *_rest, kind in self._attached):
            return run_ends
        sc = self.scene()
        for i, (w, attr, orig, kind) in enumerate(self._attached):
            if kind != "tee":
                continue
            host = self._run_wall_under(orig)
            if host is None:
                continue
            seg = split_wall_at(sc, host, orig, on_seg_tol=0.75)
            if seg is None:
                continue
            self._run.append(seg)
            run_ends = run_ends + [(seg, "p1"), (seg, "p2")]
            self._attached[i] = (w, attr, orig, "corner")
        return run_ends

    def _plan_vertex_moves(self, run_ends):
        """Turn the 0.6" coincidence discovery into REAL VERTEX SHARING, once,
        at drag start -- P3.3's whole content.

        Until now the drag *scanned* for coincident ends and moved each one by
        hand, which is split-on-write: the corner came apart and was rebuilt
        from coordinates on every mouse event. After this pass the ends that ARE
        one corner reference ONE `Vertex`, and the drag moves the vertex -- so a
        neighbour follows because it is the same corner, not because a loop
        remembered to drag it. That is the difference between geometry that
        happens to agree and topology.

        THE SPLIT RULE COMES FIRST, and it is a rule about what must NOT be
        shared. A wall collinear with the slide that continues past an endpoint
        cannot ride the corner: the slide is perpendicular, so moving the shared
        end would swing the continuation's far end and SHEAR it. So the corner
        is split -- the continuation gets its own vertex and stays exactly where
        it is -- before any sharing is created. Split first, shear never.

        Tee attachments are deliberately NOT promoted: they land on the dragged
        wall's BODY, not on a corner, so there is no vertex to share. They keep
        the sideways-only stretch, and become real topology at P3.4, where
        `split_edge` gives a body-landing a vertex to be."""
        # 1. split off the collinear continuations, before anything is shared
        for w, attr in self._continuations:
            v = w.end_vertex(attr)
            if any(rw.end_vertex(ra) is v for rw, ra in run_ends):
                w.set_end_vertex(attr, Vertex.at(v.point()))

        # 2. the run's own ends are the corners this drag moves
        moves, by_id = [], {}
        for w, attr in run_ends:
            v = w.end_vertex(attr)
            dv = by_id.get(id(v))
            if dv is None:
                dv = by_id[id(v)] = _DragVertex(v)
                moves.append(dv)
            dv.ends.append((w, attr))

        # 3. promote each coincident neighbour end onto the corner it sits on
        self._promoted = 0
        for w, attr, orig, kind in self._attached:
            if kind != "corner":
                continue
            host = min(((rw, ra) for rw, ra in run_ends),
                       key=lambda t: QLineF(orig, getattr(t[0], t[1])).length())
            v = host[0].end_vertex(host[1])
            if w.end_vertex(attr) is not v:
                w.set_end_vertex(attr, v)
                self._promoted += 1
            by_id[id(v)].ends.append((w, attr))

        # 4. the room outlines holding these corners ride along (P3.5). A room
        # region is DERIVED from its outline, so this is the whole of "the rooms
        # either side resize when a party wall slides" -- there is no detection
        # pass left to do it, and there does not need to be.
        for room in {id(r): r for w in self._run for r in w.rooms}.values():
            for e in getattr(room, "outline", ()):
                dv = by_id.get(id(e.v))
                if dv is not None:
                    dv.edges.append(e)
        self._vmoves = moves

    def mouseMoveEvent(self, e):
        if self._mode is None:
            return
        sp = e.scenePos()
        target = (self._corner_target if self.rooms
                  else self._endpoint_target)
        if self._mode == "p1":
            self.p1 = target(sp, e.modifiers())
        elif self._mode == "p2":
            self.p2 = target(sp, e.modifiers())
        elif self._mode == "move":
            delta = QPointF(sp.x() - self._press.x(), sp.y() - self._press.y())
            if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Ctrl: move freely in any direction
                np1 = wall_snap(QPointF(self._o1.x() + delta.x(),
                                        self._o1.y() + delta.y()))
                dx, dy = np1.x() - self._o1.x(), np1.y() - self._o1.y()
            else:
                # slide only orthogonally to the wall: each end rides the
                # line projected perpendicular from its starting point, so
                # attached rooms stay rectangular instead of shearing
                ux, uy = self._slide_u.x(), self._slide_u.y()
                nx_, ny_ = -uy, ux
                s = wall_snap_len(delta.x() * nx_ + delta.y() * ny_)
                dx, dy = nx_ * s, ny_ * s
            # P3.3: MOVE THE VERTICES. One move per corner carries the whole
            # collinear side (self + the open-wall gap + any collinear
            # neighbour) AND every promoted corner joint, because they are all
            # ends of the same vertices now -- there is nothing left to keep in
            # step by hand.
            for dv in self._vmoves:
                dv.apply(dx, dy)
            for w in self._run:
                if w is not self:
                    w.rebuild()
            # what could not be promoted still moves by coordinate. T-joints
            # follow only the sideways part of the slide so they stretch
            # instead of tilting -- a body-landing has no vertex to share until
            # P3.4 makes one; a `rigid` corner is a grouped wall, held back
            # from sharing by the group guard, not by geometry.
            ux, uy = self._slide_u.x(), self._slide_u.y()
            along = dx * ux + dy * uy
            px, py = dx - along * ux, dy - along * uy
            for w, attr, orig, kind in self._attached:
                if kind == "rigid":
                    setattr(w, attr, QPointF(orig.x() + dx, orig.y() + dy))
                elif kind == "tee":
                    setattr(w, attr, QPointF(orig.x() + px, orig.y() + py))
                w.rebuild()
        self.rebuild()
        e.accept()

    def mouseReleaseEvent(self, e):
        if self._mode is not None:
            # A wall is left exactly where the drag put it -- never snapped to
            # another wall on release, so a body-slide can't yank an end over
            # and tilt the wall.  Stretching an end (p1/p2) only sticks to an
            # orthogonal projected line while dragging (and a free wall fuses
            # if it now overlaps a same-type one); the angle changes only with
            # Shift.
            endpoint_edit = self._mode in ("p1", "p2")
            corner_drag = endpoint_edit and bool(self.rooms)
            merge_wall(self.scene(), self)          # fuse if it now overlaps
            rebuild_all_walls(self.scene())
            # dragging a corner back so the room is fully walled again fuses
            # the wall back in: re-lock its corners (right-click to detach
            # again)
            # P3.5: "fully walled again" is a question about the room's OUTLINE
            # -- does a wall span every edge? -- which is what `open_edges()`
            # answers. It used to be asked of a dashed placeholder item, and
            # asking THAT would have re-locked the wall on the very drag that
            # opened the side. The placeholder went at P3.7.
            if (corner_drag and self._corners_unlocked
                    and not any(r.open_edges() for r in self.rooms)):
                self._corners_unlocked = False
                self.primary_room.raise_to_front()   # normalise z to siblings
        self._mode = None
        e.accept()

    def contextMenuEvent(self, e):
        from floorplanner.rooms import detach_wall_from_room  # late (cycle)
        menu = QMenu()
        a_ext = menu.addAction("Exterior wall (6\")")
        a_ext.setCheckable(True)
        a_ext.setChecked(self.wall_type == "exterior")
        a_int = menu.addAction("Interior wall (4 1/2\")")
        a_int.setCheckable(True)
        a_int.setChecked(self.wall_type == "interior")
        a_detach = None
        if self.rooms:
            menu.addSeparator()
            a_detach = menu.addAction("Detach wall from room")
        menu.addSeparator()
        a_del = menu.addAction("Delete wall")
        a_front, a_back = add_front_back_actions(menu)
        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        sc = self.scene()
        if chosen is a_ext:
            self.wall_type = "exterior"
            self.rebuild()
        elif chosen is a_int:
            self.wall_type = "interior"
            self.rebuild()
        elif a_detach is not None and chosen is a_detach and sc is not None:
            self.setSelected(True)
            detach_wall_from_room(sc, self)   # opens the vacated edge
        elif chosen is a_del and sc is not None:
            delete_wall(sc, self)   # room survives via its outline; edge opens
        e.accept()


class OpeningItem(QGraphicsItem):
    """A door or window.  Child of its wall; local x runs along the wall,
    local y across the thickness.

    **ANCHORED TO A NAMED END (P3.6), not measured from `p1`.** The opening
    holds the `Vertex` it is dimensioned off and `offset_in`, the distance from
    that corner to its NEAR EDGE -- which is how a drawing dimensions a door,
    and what the v5 schema stores. `s` (the centre's distance from `p1`) stays
    as a read-through property so every existing caller keeps working: the
    compat-shim discipline P3.1 used for `p1`/`p2` and P3.2 for `corners`.

    The anchor is a VERTEX and not the string "v1"/"v2", which is what makes
    the schema's three claims true rather than approximately true:
      * STRETCHED at the far end -- the offset is from the corner that did not
        move, so nothing slides;
      * REVERSED -- swapping which end is `p1` renames the ends and moves no
        geometry, and an opening anchored to a corner does not care what that
        corner is currently called;
      * SPLIT -- the opening goes with the segment its anchor corner is on,
        which is R2's rule stated literally rather than reconstructed from
        coordinates.
    Absolute `s` survives none of the three, which is the whole of defect 7."""

    def __init__(self, wall: WallItem, kind: str, code: str, s: float):
        super().__init__(wall)
        self.wall = wall
        self.kind = kind                  # 'door' | 'window'
        self.code = "3280"
        self.width, self.height = 32.0, 80.0
        self.door_type = "LH"
        self.swing = -1                   # -1 / +1 : which face it swings to
        self.anchor_v = None              # the Vertex this is dimensioned off
        self.offset_in = 0.0              # ...to the opening's NEAR EDGE
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(OPENING_Z)
        self.set_code(code, rebuild=False)      # sets width, which s needs
        # NEARER END, ties toward v1 (R4) -- the same rule `bridge._walls_of`
        # already emits with, so the scene and the document agree on which end
        # a given opening is dimensioned off and canonical form round-trips.
        length = wall.length()
        self.anchor_v = wall.end_vertex("p1" if s <= length / 2.0 else "p2")
        self.s = s
        self.sync()

    # -- the anchor -----------------------------------------------------------
    def _anchor_attr(self) -> str:
        """"p1" / "p2" -- which end this opening is dimensioned off, resolved by
        IDENTITY and SELF-HEALING.

        Object identity first, because it holds in the common case and costs
        nothing. When it fails the corner has been RELOCATED (P3.3 mints a new
        `Vertex` carrying the same uid), so the uid still matches and the anchor
        is re-pointed at the new object -- once per move, not once per read.
        That matters: `s` is read on every rebuild and every paint, and forcing
        a uid mint per read is exactly the allocation P3.1 had to remove."""
        w = self.wall
        # A DELETED WALL IS A HARD CRASH, not an exception (P3.6). `s` became a
        # property here, so it now touches `self.wall` on every read -- and an
        # `OpeningItem` outlives its wall's C++ object often enough to matter
        # (teardown, undo restore, a fractured wall's discarded segments). The
        # old stored float never dereferenced anything. Same `sip.isdeleted`
        # guard `WallItem.itemChange` and `RoomItem.itemChange` already carry.
        if w is None or sip.isdeleted(w):
            return "p1"
        v1, v2 = w.end_vertex("p1"), w.end_vertex("p2")
        if self.anchor_v is v1:
            return "p1"
        if self.anchor_v is v2:
            return "p2"
        if self.anchor_v is not None:
            uid = self.anchor_v._uid          # no mint: None means never named
            if uid is not None:
                if v1._uid == uid:
                    self.anchor_v = v1
                    return "p1"
                if v2._uid == uid:
                    self.anchor_v = v2
                    return "p2"
        self.anchor_v = v1                    # orphaned -> re-seat on v1
        return "p1"

    def anchor_from(self, wall=None) -> str:
        """"v1" / "v2" -- the anchor as the DOCUMENT names it."""
        return "v1" if self._anchor_attr() == "p1" else "v2"

    @property
    def s(self) -> float:
        """Distance of the opening's CENTRE from `wall.p1` -- derived from the
        anchor, so it moves when the anchored corner does and not otherwise."""
        if self.wall is None or sip.isdeleted(self.wall):
            return self.offset_in + self.width / 2.0
        if self._anchor_attr() == "p2":
            return self.wall.length() - self.offset_in - self.width / 2.0
        return self.offset_in + self.width / 2.0

    @s.setter
    def s(self, value: float):
        """Place the centre at `value` from `p1`, re-expressed against the end
        this opening is dimensioned off. The drag writes through here."""
        if self._anchor_attr() == "p2":
            self.offset_in = (self.wall.length() - float(value)
                              - self.width / 2.0)
        else:
            self.offset_in = float(value) - self.width / 2.0

    def fits(self) -> bool:
        """False when the opening no longer lies within its wall -- the
        condition `rebuild`'s clamp used to hide by sliding the door (P3.6)."""
        half = self.width / 2.0
        return -1e-6 <= self.s - half and self.s + half <= self.wall.length() + 1e-6

    # -- data -----------------------------------------------------------------
    def set_code(self, code: str, rebuild: bool = True):
        w, h = parse_wwhh(code)
        if w > self.wall.length():
            raise ValueError("Opening is wider than the wall.")
        # A RESIZE IS ABOUT THE CENTRE, not about the anchored edge (P3.6).
        # `offset_in` runs to the NEAR EDGE, so leaving it alone while the width
        # changes grows the opening away from its anchor -- which pushed an
        # auto-sized garage door clean off the end of its wall and was caught by
        # shadow mode as I7. Widening a door in place is what a user means, so
        # the centre is held and the offset re-derived.
        centre = self.s if self.anchor_v is not None else None
        self.code = code.strip()
        self.prepareGeometryChange()
        self.width, self.height = w, h
        if centre is not None:
            self.s = centre
        if rebuild:
            self.wall.rebuild()           # re-cuts the gap, re-syncs children

    def set_door_type(self, name: str):
        """Change the door type; garage doors auto-size an undersized
        opening to their standard size (if the wall is long enough)."""
        self.prepareGeometryChange()
        self.door_type = name
        if name in GARAGE_DEFAULTS:
            code, min_w = GARAGE_DEFAULTS[name]
            if self.width < min_w:
                try:
                    self.set_code(code)
                except ValueError:
                    pass                  # wall too short: keep the size
        self.update()

    def sync(self):
        """Reposition/orient on the wall after any wall geometry change."""
        self.prepareGeometryChange()
        self.setPos(self.wall.point_at(self.s))
        self.setRotation(math.degrees(self.wall.angle_rad()))
        self.update()

    # -- QGraphicsItem ---------------------------------------------------------
    def boundingRect(self) -> QRectF:
        # Tightly bound only what paint() actually draws (local coords: x
        # along the wall, y across it).  A swing arc / overhead outline
        # reaches out on its swing side; everything else stays in the
        # opening footprint.  (A symmetric width+16 margin made the rect
        # huge for wide openings, ballooning any enclosing group's box.)
        w, t = self.width, self.wall.t
        x0, x1, y0, y1 = -w / 2, w / 2, -t / 2, t / 2
        if self.kind == "door":
            dt = self.door_type
            reach = {"LH": w, "RH": w, "FRENCH": w / 2,
                     "BIFOLD": 0.4 * w}.get(dt, 0.0)
            if dt in GARAGE_DEFAULTS:
                reach = min(self.height, 96.0)
            if self.swing < 0:
                y0 -= reach
            else:
                y1 += reach
            if dt == "POCKET":
                x0 -= w               # the panel slides into the wall
        pad = 18.0                    # line widths + the WWHH label
        return QRectF(x0 - pad, y0 - pad,
                      (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad)

    def shape(self) -> QPainterPath:
        w, t = self.width, self.wall.t
        p = QPainterPath()
        p.addRect(QRectF(-w / 2, -t / 2 - 1, w, t + 2))
        return p

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, t = self.width, self.wall.t
        ghost = floor_display_mode(self.wall.floor) != "active"
        ink = QPen(FLOOR_GHOST if ghost else QColor(20, 20, 20), 0)
        painter.setPen(ink)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # jambs (the cut ends of the wall)
        painter.drawLine(QPointF(-w / 2, -t / 2), QPointF(-w / 2, t / 2))
        painter.drawLine(QPointF(w / 2, -t / 2), QPointF(w / 2, t / 2))
        if ghost:                            # gray jambs only on non-active floors
            return

        if self.kind == "window":
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawRect(QRectF(-w / 2, -t / 2, w, t))
            painter.drawLine(QPointF(-w / 2, 0), QPointF(w / 2, 0))   # glazing
        else:
            self._paint_door(painter, w, t)

        # WWHH label, kept clear of the swing side
        f = QFont()
        f.setPixelSize(6)
        painter.setFont(f)
        painter.setPen(QPen(QColor(70, 70, 90) if not self.isSelected()
                            else QColor(0, 122, 255), 0))
        label = self.code if self.kind == "window" else f"{self.code} {self.door_type}"
        if self.kind == "door" and self.swing < 0:
            ty = t / 2 + 9
        else:
            ty = -t / 2 - 3
        painter.drawText(QPointF(-w / 2, ty), label)

        if self.isSelected():
            painter.setPen(QPen(QColor(0, 122, 255), 0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(-w / 2, -t / 2 - 1, w, t + 2))

    def _swing_arc(self, painter, hx, hy, sy, radius, hinge_left):
        """Door panel + quarter-circle swing arc from a hinge point."""
        painter.drawLine(QPointF(hx, hy), QPointF(hx, hy + sy * radius))
        rect = QRectF(hx - radius, hy - radius, 2 * radius, 2 * radius)
        if sy < 0:
            start = 0 if hinge_left else 90      # ends at N (visually up)
        else:
            start = 270 if hinge_left else 180   # ends at S (visually down)
        painter.drawArc(rect, start * 16, 90 * 16)

    def _paint_door(self, painter, w, t):
        sy = self.swing
        face = sy * t / 2
        dt = self.door_type
        white = QBrush(QColor(255, 255, 255))

        if dt == "LH":
            self._swing_arc(painter, -w / 2, face, sy, w, hinge_left=True)
        elif dt == "RH":
            self._swing_arc(painter, w / 2, face, sy, w, hinge_left=False)
        elif dt == "FRENCH":
            self._swing_arc(painter, -w / 2, face, sy, w / 2, hinge_left=True)
            self._swing_arc(painter, w / 2, face, sy, w / 2, hinge_left=False)
        elif dt == "BIFOLD":
            rise = sy * 0.35 * w
            painter.drawPolyline(QPolygonF([
                QPointF(-w / 2, face), QPointF(-w / 4, face + rise),
                QPointF(0, face)]))
            painter.drawPolyline(QPolygonF([
                QPointF(0, face), QPointF(w / 4, face + rise),
                QPointF(w / 2, face)]))
        elif dt == "POCKET":
            dash = QPen(QColor(20, 20, 20), 0, Qt.PenStyle.DashLine)
            painter.setPen(dash)
            painter.setBrush(white)
            painter.drawRect(QRectF(-w / 2 - w, -t / 2 + 0.75, w, t - 1.5))
            painter.setPen(QPen(QColor(20, 20, 20), 0))
            painter.drawRect(QRectF(-w / 2, -t / 6, w / 2, t / 3))
        elif dt == "SLIDER":
            painter.setBrush(white)
            pw = 0.55 * w
            painter.drawRect(QRectF(-w / 2, -t * 0.35, pw, t * 0.30))
            painter.drawRect(QRectF(w / 2 - pw, t * 0.05, pw, t * 0.30))
        elif dt == "DOORWAY":
            dash = QPen(QColor(20, 20, 20), 0, Qt.PenStyle.DashLine)
            painter.setPen(dash)
            painter.drawLine(QPointF(-w / 2, -t / 2), QPointF(w / 2, -t / 2))
            painter.drawLine(QPointF(-w / 2, t / 2), QPointF(w / 2, t / 2))
        elif dt in GARAGE_DEFAULTS:
            # closed panel in the opening + dashed OVERHEAD outline of the
            # open door projecting inward (the swing side), as deep as the
            # door is tall
            painter.setBrush(white)
            painter.drawRect(QRectF(-w / 2, -t * 0.25, w, t * 0.5))
            depth = sy * min(self.height, 96.0)
            y0 = sy * t / 2
            dash = QPen(QColor(20, 20, 20), 0, Qt.PenStyle.DashLine)
            painter.setPen(dash)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(-w / 2, min(y0, y0 + depth),
                                    w, abs(depth)))
            if dt == "GARAGE-2":          # double-wide: two-car divider
                painter.drawLine(QPointF(0, y0), QPointF(0, y0 + depth))

    # -- interaction -------------------------------------------------------------
    def mousePressEvent(self, e):
        if self.wall is not None and self.wall.group() is not None:
            # the opening's wall is grouped: let the group own the drag
            # instead of sliding the opening along its wall
            e.ignore()
            return
        if e.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(e)
            return
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.setSelected(not self.isSelected())    # toggle membership
            e.accept()
            return
        if not self.isSelected():
            self.scene().clearSelection()
        self.setSelected(True)
        if self.wall is not None and self.wall.rooms:
            self.wall.primary_room.raise_to_front()
        e.accept()

    def mouseMoveEvent(self, e):
        if self.wall is not None and self.wall.group() is not None:
            e.ignore()
            return
        # slide along the wall, snapping to the nearest inch.
        # THIS CLAMP LIVES, DELIBERATELY (P3.6 / R3), and it is not the one that
        # died in `rebuild`. That one silently repaired STORED DATA on the
        # render path; this one BOUNDS A GESTURE -- it stops the user dragging a
        # door off the end of its wall, which is the drag's job. Same
        # distinction that keeps `wall_endpoint_open` and `_WallBBoxIndex`:
        # rightly spatial, permanently. Do not remove it as a leftover of P3.6.
        s = round(self.wall.s_of(e.scenePos()))
        half = self.width / 2
        self.s = min(max(s, half), max(half, self.wall.length() - half))
        self.wall.rebuild()             # cascades to the coincident party wall
        e.accept()

    def mouseDoubleClickEvent(self, e):
        self._prompt_size()
        e.accept()

    def _view(self):
        sc = self.scene()
        return sc.views()[0] if sc and sc.views() else None

    def _prompt_size(self):
        v = self._view()
        code, ok = QInputDialog.getText(
            v, f"{self.kind.title()} size",
            'Size WWHH (width inches, height inches):', text=self.code)
        if not ok:
            return
        try:
            self.set_code(code)
        except ValueError as ex:
            QMessageBox.warning(v, "Invalid size", str(ex))

    def contextMenuEvent(self, e):
        menu = QMenu()
        type_actions = {}
        if self.kind == "door":
            tmenu = menu.addMenu("Type")
            for name in DOOR_TYPES:
                a = tmenu.addAction(name)
                a.setCheckable(True)
                a.setChecked(name == self.door_type)
                type_actions[a] = name
            a_flip = menu.addAction("Flip swing side")
        else:
            a_flip = None
        a_size = menu.addAction("Set size (WWHH)\u2026")
        menu.addSeparator()
        a_del = menu.addAction(f"Delete {self.kind}")
        a_front, a_back = add_front_back_actions(menu)

        chosen = menu.exec(e.screenPos())
        if handle_front_back(self, chosen, a_front, a_back):
            e.accept()
            return
        if chosen in type_actions:
            self.set_door_type(type_actions[chosen])
        elif chosen is a_flip and a_flip is not None:
            self.swing = -self.swing
            self.update()
        elif chosen is a_size:
            self._prompt_size()
        elif chosen is a_del:
            wall, sc = self.wall, self.scene()
            if self in wall.openings:
                wall.openings.remove(self)
            sc.removeItem(self)
            wall.rebuild()
        e.accept()
