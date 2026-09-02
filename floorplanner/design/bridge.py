"""The scene -> v5 `Design` walk (P1.4).

`design_from_scene(win)` reads the live `QGraphicsScene` into a P1.1 `Design`.
The reverse direction (`apply_design_to_scene`) is P1.5; P1.6 runs both under
`--verify-design` to check the document against the scene after every edit.

This is the one module in `floorplanner/design/` that imports Qt -- it is the
seam between the scene layer and the Qt-free document, so it has to. It is
deliberately NOT re-exported from `floorplanner/design/__init__.py`, which keeps
`model`/`topology`/`legacy`/`validate` importable without dragging the scene
layer in behind them.

Three rules govern the walk; they are the task's, not local taste.

**Level-scoped by construction.** Levels are the OUTER loop and items the inner
one, so a level's walk is handed only its own items and physically cannot see
another level's. This is what closes defect 12 (ten query paths that ignore the
floor filter): there is no global query here to forget to filter. Vertex tables,
wall graphs and room polygons are all per level, so cross-level contamination is
not merely prevented -- it is unrepresentable.

**Outlines come from the scene, not from the geometry.** Room outlines are built
from each `RoomItem.corners`, never from `topology.trace_faces`. The bridge
reports what the scene BELIEVES, not what the wall graph implies it should
believe. Repairing on the way past would make P1.6's shadow comparison diverge
from the very scene it is shadowing; repair happens once, at P2.1's import.

**The 9" weld is a CHECK here, never an edit.** The scene is `p1`/`p2`-based
until P3.1, so reaching a vertex table needs `legacy.py`'s pre-vertex pass. Only
the weld-on-insert half of that runs for real: `VertexTable` fuses coordinates
within `WELD_TOL` (0.6"), which is modelling precision -- two points that close
ARE one vertex -- and `split_params` cuts walls at junctions and room corners so
one wall spans one outline edge. Both are representation. `weld_endpoints`, the
9" gesture-tolerance repair, runs only on a COPY, to count what it WOULD move;
the emitted geometry is always the scene's own. A non-zero count means the scene
disagrees with itself and is surfaced (`report["unwelded_ends"]`, a warning, and
`strict=True` raises -- the hook P1.6's `--verify-design` pulls), because that is
a finding about the scene, not something to silently fix here.

Expect a non-zero count on any plan loaded from a legacy file: welds happen at
draw release only, never on load (corrected F5 in `docs/CODE_REVIEW_v2.md`).

`unwelded_ends` counts ends whose COORDINATE MOVES, which is deliberately not
what `weld_endpoints` returns. That return value counts weld OPERATIONS, and
most of them are no-ops on junctions that are already exact: on `planc1.json` it
reports 31 operations, of which 5 move anything -- four real 1.5" divider gaps
and one 0.001" float nudge. 31 is the right number for "welds attempted" and the
wrong number for "geometry that disagrees with itself"; this key is the latter.
"""
import copy
import math
import warnings
from collections import defaultdict

from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QGraphicsScene

from floorplanner.config import (
    DEFAULT_FLOOR, DEFAULT_SETTINGS, JOIN_TOL, SETTINGS, active_floor,
    coerce_setting, set_floor_state,
)
from floorplanner.design.canonical import canonicalize
from floorplanner.design.legacy import (
    MIN_SPAN, ON_SEG_TOL, WELD_TOL, VertexTable, split_params, weld_endpoints,
)
from floorplanner.design.model import Design
from floorplanner.geometry import parse_wwhh
from floorplanner.items import (
    FurnishingItem, GroupItem, ReferenceImageItem, furnishing_spec,
    make_furnishing,
)
from floorplanner.model import Floor
from floorplanner.vertex import Vertex
from floorplanner.roofs import RoofItem, nearest_eaves_wall
from floorplanner.rooms import (
    OutlineEdge, RoomItem, poly_area_sqft, room_path_from_corners,
)
from floorplanner.walls import (
    OpeningItem, WallItem, rebuild_all_walls,
)

# names that make a room exterior rather than interior.  Kept identical to
# tools/migrate_to_design_v5.py so a plan walked from the scene and the same
# plan imported at P2.1 classify alike.  Deliberately NOT extended to
# area_accounting: the scene already states that, per room, in
# properties["include_sqft"].
EXTERIOR_NAMES = ("porch", "deck", "patio", "terrace", "lanai")

# what the SCENE actually models. Everything else in a v5 wall/room is stashed
# on the item at apply and re-emitted by the walk, so a load->save round trip
# cannot quietly drop a field the editor has no widget for yet.
#
# LIFETIME, accepted rather than engineered around: the stash lives ON THE ITEM,
# so it survives ordinary edits but DIES WITH THE ITEM. A wall carrying
# thickness_in that gets coalesced away, or a room deleted and re-detected,
# silently loses its stash. That is acceptable only because these fields have no
# editor yet -- P4/P5 model them properly (nominal_size at P4.4,
# area_accounting and the finishes at P5.1-P5.3) and the stash retires then.
# `placement` retired at P4.2 exactly this way: modelled on RoomItem, emitted
# by the walk, applied on load, and no longer stashed.
# Written down here so it is a known limit, not a mystery discovered later.
_WALL_MODELLED = frozenset(("id", "level", "v1", "v2", "type", "left", "right",
                            "openings"))
_ROOM_MODELLED = frozenset(("id", "level", "name", "outline", "label",
                            "properties", "placement",
                            # P4.4: modelled on the item, like `placement`
                            "category", "nominal_size"))
# settings keys the walk re-emits itself; anything else in a document's
# settings (e.g. `name`) is likewise retained rather than lost
WALK_SETTINGS = frozenset(DEFAULT_SETTINGS) | {"vertex_weld_in", "join_tol_in",
                                               "area_basis", "editing"}


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


# ------------------------------------------------------------------ the source
def _resolve(source, floors):
    """(scene, floor roster) from a MainWindow or a bare QGraphicsScene.

    The roster must come from `MainWindow.floors` where there is one: an empty
    floor owns no items, so it cannot be derived from the scene. A bare scene
    (tests, headless walks) has no roster, so the floors are discovered from the
    items and ordered deterministically -- default floor first, then by name."""
    if isinstance(source, QGraphicsScene):
        scene, roster = source, floors
    else:
        scene = source.scene
        roster = floors if floors is not None else list(source.floors)
    if roster is None:
        names = {getattr(it, "floor", DEFAULT_FLOOR) for it in scene.items()}
        ordered = ([DEFAULT_FLOOR] if DEFAULT_FLOOR in names else []) + \
                  sorted(n for n in names if n != DEFAULT_FLOOR)
        roster = [Floor(n) for n in (ordered or [DEFAULT_FLOOR])]
    return scene, list(roster)


def _by_floor(scene):
    """Every scene item bucketed by its floor tag, in one pass.

    The buckets are the ONLY thing the per-level walk ever sees, which is what
    makes the level scoping structural rather than a filter it could forget."""
    out = defaultdict(list)
    for it in scene.items():
        out[getattr(it, "floor", DEFAULT_FLOOR)].append(it)
    return out


def _partitions(items):
    """One level's items split into VERTEX NAMESPACES: the plan, then each
    floating room with its own walls.

    Extracted from `design_from_scene` at G2 so the walk and
    `scene_identity_report` share ONE definition of "these ends may be compared
    with each other". They must agree: a floating room has EXPLICITLY broken its
    sharing with the plan (I12, P4.2), so two coincident ends across that
    boundary are correct rather than a fault, and a checker that did not know it
    would report every parked float as broken. A second copy of this rule would
    drift, and this project has measured what that costs.
    """
    floating = [r for r in items if isinstance(r, RoomItem)
                and getattr(r, "placement_state", "placed") == "floating"]
    fids = {id(r) for r in floating}
    fids |= {id(w) for r in floating for w in r.walls}
    parts = [[it for it in items if id(it) not in fids]]
    parts += [[r] + [w for w in r.walls if w.scene() is not None]
              for r in floating]
    return parts


def scene_identity_report(source, floors=None, tol=WELD_TOL):
    """D48: does geometric coincidence imply IDENTITY in the live scene?

    REPORT-ONLY. It gates nothing, raises nothing, and no operation calls it.

    THE HOLE IT MEASURES. `design_from_scene` WELDS on the way out, so a scene
    whose corners are not shared at all emits a document every one of the
    fifteen invariants accepts. Measured on the `fragment` product: 20 distinct
    `Vertex` objects on 10 geometric points, collapsing to 20 -> 10 vertices and
    16 -> 12 walls in the walk, with `check(doc, deep=True)` CLEAN throughout.
    So a green `check()` never meant "the scene is sound" -- only "the WELDED
    PROJECTION of the scene is sound", and nothing had ever looked at the
    difference. This looks at the difference.

    THE PROPERTY, in `WallItem.end_vertex`'s own words: *two ends are the same
    corner iff this returns the same object for both (`is`, never `==`)*. So for
    every pair of wall ends within `tol`, the check asks whether they are the
    same object -- identity, never coordinates.

    SCOPED THE WAY THE WALK IS SCOPED, and this is what keeps it quiet on
    correct scenes: per floor, then per vertex namespace via `_partitions`. A
    floating room has deliberately broken its sharing with the plan, so its
    coincidences are not faults; comparing across that boundary would report
    every parked float.

    Returns a dict. `split` is the finding list -- one entry per geometric point
    that more than one `Vertex` object claims:

        {"ends": N, "points": N, "split": [{"floor", "x", "y",
                                            "vertices", "ends", "walls"}],
         "extra_vertices": N}

    `extra_vertices` is the honest headline: how many `Vertex` objects exist
    beyond one per point. Zero on a scene whose corners are shared.
    """
    scene, roster = _resolve(source, floors)
    buckets = _by_floor(scene)
    split, n_ends, n_points = [], 0, 0

    for f in roster:
        for part in _partitions(buckets.get(f.name, [])):
            ends = []
            for w in part:
                if isinstance(w, WallItem):
                    ends.append((w.end_vertex("p1"), w))
                    ends.append((w.end_vertex("p2"), w))
            n_ends += len(ends)

            # Cluster by proximity. A grid of cell `tol` plus its eight
            # neighbours keeps this local instead of O(n^2) over the plan; the
            # union-find then makes the clustering order-independent, which a
            # naive sweep is not.
            cells = defaultdict(list)
            for i, (v, _w) in enumerate(ends):
                cells[(int(v.x // tol), int(v.y // tol))].append(i)
            parent = list(range(len(ends)))

            def find(i, parent=parent):
                while parent[i] != i:
                    parent[i] = parent[parent[i]]
                    i = parent[i]
                return i

            def union(a, b, parent=parent):
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[rb] = ra

            for (cx, cy), idxs in cells.items():
                near = []
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        near += cells.get((cx + dx, cy + dy), [])
                for i in idxs:
                    vi = ends[i][0]
                    for j in near:
                        if j <= i:
                            continue
                        vj = ends[j][0]
                        if math.hypot(vi.x - vj.x, vi.y - vj.y) <= tol:
                            union(i, j)

            groups = defaultdict(list)
            for i in range(len(ends)):
                groups[find(i)].append(i)
            n_points += len(groups)

            for members in groups.values():
                objs = {id(ends[i][0]) for i in members}
                if len(objs) > 1:
                    v0 = ends[members[0]][0]
                    split.append({
                        "floor": f.name,
                        "x": round(v0.x, 3), "y": round(v0.y, 3),
                        "vertices": len(objs), "ends": len(members),
                        "walls": len({id(ends[i][1]) for i in members}),
                    })

    split.sort(key=lambda d: (-d["vertices"], d["floor"], d["x"], d["y"]))
    return {"ends": n_ends, "points": n_points, "split": split,
            "extra_vertices": sum(d["vertices"] - 1 for d in split)}


def _ordered(items, kind, key):
    """This level's items of one type, in a GEOMETRIC order.

    `scene.items()` returns items in stacking order, so without this the ids the
    walk mints would depend on z -- and "Bring to front" would rewrite the whole
    document. Sorting by geometry instead is the same z-independence
    `Project.to_dict` already gives the v4 snapshot (`model.py:221-224`), and
    P1.5's round-trip identity rests on it: rebuilding a scene from a `Design`
    reverses insertion order, so unsorted ids would not survive one apply."""
    return sorted((it for it in items if isinstance(it, kind)), key=key)


def _wall_key(w):
    return (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y(), w.wall_type)


def _room_key(r):
    return (r.name, r.anchor.x(), r.anchor.y())


def _furn_key(f):
    return (f.pos().x(), f.pos().y(), f.kind, f.rotation())


def _roof_key(rf):
    return (rf.p1.x(), rf.p1.y(), rf.p2.x(), rf.p2.y())


# ------------------------------------------------------------------ weld check
def _weld_delta(raw):
    """How many wall ends `weld_endpoints` WOULD move on this level's geometry,
    run against a copy so nothing here is mutated.  0 on a scene that agrees
    with itself; non-zero is a finding, reported by the caller.

    Movement is counted above `WELD_TOL` (0.6"), the SAME floor the importer's
    `ends_moved` uses -- two coordinates that close ARE one vertex by the
    schema's own definition, so a smaller displacement is not a gap. One
    question deserves one floor: before this, telemetry counted planc1 at 5 and
    the conversion report at 4, which is the 31-vs-4 trap in miniature. The two
    NAMES stay distinct (`unwelded_ends` is telemetry, `ends_moved` is a user
    report) because they serve different masters."""
    probe = copy.deepcopy(raw)
    weld_endpoints(probe)
    moved = 0
    for before, after in zip(raw, probe, strict=False):
        for k in ("p1", "p2"):
            if math.dist(tuple(before[k]), tuple(after[k])) > WELD_TOL:
                moved += 1
    return moved


# ------------------------------------------------------------------ chain walk
def _walk(va, vb, edge, adj, vt, max_hops=10):
    """The wall chain from `va` to `vb` as directed (u, v) hops, or None when no
    run of walls covers it.  A room edge whose span was split at a T-junction is
    several walls, not one; each hop becomes its own outline edge so that every
    outline edge maps to exactly one wall (invariant I5)."""
    if (va, vb) in edge:
        return [(va, vb)]
    A, B = vt.xy(va), vt.xy(vb)
    L = math.dist(A, B)
    if L < 1e-6:
        return None
    u = _unit(A, B)
    chain, cur, guard = [], va, 0
    while cur != vb and guard < max_hops:
        guard += 1
        cs, _ = _proj(vt.xy(cur), A, u)
        best, bs = None, -1.0
        for nxt in adj[cur]:
            s, perp = _proj(vt.xy(nxt), A, u)
            if perp <= ON_SEG_TOL and cs + 1e-6 < s <= L + ON_SEG_TOL and s > bs:
                best, bs = nxt, s
        if best is None:
            return None
        chain.append((cur, best))
        cur = best
    return chain if cur == vb else None


# ------------------------------------------------- the unwelded-ends warning
_BASELINE_ATTR = "_fp_unwelded_baseline"
_WARNED_ATTR = "_fp_unwelded_warned"


def rebase_weld_baseline(scene):
    """Forget what the scene's weld state was, so the next walk re-reads it.

    Called by both load paths. A load REPLACES the document, so whatever it
    arrives with is its baseline -- not a tear some edit made."""
    for a in (_BASELINE_ATTR, _WARNED_ATTR):
        if hasattr(scene, a):
            delattr(scene, a)


def _warn_unwelded(scene, n):
    """Report unwelded ends BY CAUSE, and at most once per distinct state.

    The old message said one thing for every case: "expected on a plan loaded
    from a legacy file". That is true of the ends a legacy file arrives with and
    false of the ends an EDIT tears open, and it fired on every debounced
    snapshot -- so a user watching a plan that opened clean got a stream of
    warnings, with a count that moved as they worked, all blaming the file. A
    correct warning that misattributes is worse than none: it teaches people to
    ignore the channel that will one day be right.

    So: the first walk after a load sets the BASELINE, and only a walk that
    finds MORE than the baseline warns -- naming the split between what the plan
    arrived with and what has appeared since. Equal or better is silent.

    GATE 3 SILENCED THE OPENED-WITH BRANCH FOR A V5 PLAN, because measurement
    showed it had nothing to tell the user. On `planc1TestV5.json` (5 ends at
    open):

        Edit > Coalesce all walls now : scene count 5 -> 0
        the document's own gaps       : 4 -> 4, UNCHANGED
        saved file                    : byte-identical, 62 vertices either way

    The command silences the count without closing anything. It can, because
    this count is computed on the SCENE's decomposition of the walls, and
    merging collinear runs removes the ends that would weld without moving a
    coordinate. Meanwhile the same measurement found `planc1.json` and
    `symmetricP1.json` each carrying TWO 6.003" document gaps and warning about
    neither -- so the channel both cried wolf and missed the wolf.

    A 6" gap is very likely deliberate: the schema calls `join_tol_in` a GESTURE
    tolerance and says in as many words that "a wall deliberately stopping 6"
    short of another is a legitimate design (a reveal, a pilaster gap), and
    nothing may silently close it". So the document-side gaps are not
    automatically faults either, and nothing here can tell a reveal from a
    mistake.

    WHAT IS LEFT IS THE ONE CASE THAT IS ACTIONABLE: an EDIT that tears the wall
    network, where the count rises above what the plan opened with. That branch
    stays. On open, a v5 plan says nothing (there is nothing the user could do
    that would change the file) and a LEGACY plan still warns, because there the
    ends really are the file's own unwelded coordinates and the command really
    does repair them.

    The real repair gap -- a document that carries a 1.53" gap no command
    closes -- is defect 34, and is not this function's to fix."""
    base = getattr(scene, _BASELINE_ATTR, None)
    if base is None:
        setattr(scene, _BASELINE_ATTR, n)
        base = n
        if n and getattr(scene, "_v5_source", False):
            return                   # nothing to repair -- see the docstring
        if n:
            msg = (f"design_from_scene: this legacy (v1-v4) plan OPENED with {n} "
                   f"wall "
                   f"end(s) sitting within the {JOIN_TOL}\" join tolerance of "
                   f"a neighbour without sharing a corner with it -- the "
                   f"file's own coordinates, which load never welds (F5 in "
                   f"docs/CODE_REVIEW_v2.md). Edit > Coalesce all walls now "
                   f"closes them, and saving afterwards writes them closed.")
        else:
            return
    elif n > base:
        msg = (f"design_from_scene: {n} wall end(s) now sit within the "
               f"{JOIN_TOL}\" join tolerance of a neighbour without being "
               f"welded to it -- {base} were there when the plan opened and "
               f"{n - base} are NEW. An edit has torn the wall network; this is "
               f"not the legacy-load case.")
    else:
        return                       # unchanged, or repaired -- nothing to say
    if getattr(scene, _WARNED_ATTR, None) == n:
        return                       # same state, already reported
    setattr(scene, _WARNED_ATTR, n)
    warnings.warn(msg, stacklevel=3)


# ------------------------------------------------------------------ level walk
def _new_walk_report() -> dict:
    """THE shape of the walk's report. One definition, because there were two.

    `_walls_of` does not merely count into this: it `append`s to
    `openings_failed` and `add`s to `openings_failed_ids`, so the VALUE TYPES
    are part of the contract and a bare counter will not do. `design_from_scene`
    built the right shape; `face_at` passed `defaultdict(int)`, which made
    `rep["openings_failed"]` the integer 0 -- and the first plan to reach the
    `if straddles:` branch died there with `'int' object has no attribute
    'append'`, taking the process with it (D57).

    Writing the shape out a second time is what caused that, so it is written
    out ONCE. A `try/except` at the append would have silenced the crash and
    left both spellings free to drift again.
    """
    return {"levels": 0, "segments": 0, "merged": 0,
            "open_edges": 0, "openings_dropped": 0, "openings_deduped": 0,
            "rooms_without_outline": 0, "unwelded_ends": 0,
            # R5's one vocabulary. Strings for a human; ids for `verify`,
            # which exempts an I7 only for openings that were actually
            # filed -- an unreported I7 stays a full regression.
            "openings_failed": [], "openings_failed_ids": set()}


def _walls_of(items, lid, nid, vt, rep, src=None, weld_check=True):
    """This level's walls, split at every junction and room corner, as v5 wall
    dicts.  Openings are re-anchored from absolute `s` to {from, offset_in} on
    the segment that carries them.

    Pass `src` (a dict) to receive `{(v1, v2) sorted: WallItem}` -- which scene
    wall each emitted segment came from.  `face_at` needs it and nothing else
    does, so it is an out-param rather than a field on the wall dicts: the
    Design is a document and a `QGraphicsItem` has no business in one.
    `weld_check=False` skips the O(n^2) disagreement count, which only exists to
    warn a human and has no reader on the detection path."""
    w_items = _ordered(items, WallItem, _wall_key)
    r_items = _ordered(items, RoomItem, _room_key)
    raw = [{"p1": [w.p1.x(), w.p1.y()], "p2": [w.p2.x(), w.p2.y()],
            "type": w.wall_type,
            "openings": sorted(
                [{"kind": o.kind, "code": o.code, "s": float(o.s),
                  "width": float(o.width), "door_type": o.door_type,
                  "swing": float(o.swing),
                  # R4b: the end this opening is ACTUALLY dimensioned off, and
                  # its stored offset -- carried so the emit can honour them
                  # rather than recompute a nearer-end anchor over the top
                  "from": o.anchor_from(), "offset_in": float(o.offset_in)}
                 for o in w.openings],
                key=lambda o: o["s"]),
            "extra": getattr(w, "_v5_extra", None) or {}}
           for w in w_items]
    if weld_check:
        rep["unwelded_ends"] += _weld_delta(raw)

    loops = [[(c.x(), c.y()) for c in r.corners] for r in r_items if r.corners]
    prep, cuts = split_params(raw, loops)

    walls, by_pair = [], {}
    for i, w in enumerate(raw):
        a, _b, u, L = prep[i]
        stops = sorted({0.0, L} |
                       {c for c in cuts[i] if MIN_SPAN < c < L - MIN_SPAN})
        # WHICH SEGMENT OWNS EACH OPENING, decided ONCE per opening rather than
        # re-derived per segment (R2b). Extent decides: an opening wholly inside
        # one segment lands there. A STRADDLER -- one the cuts run through --
        # goes to the segment on the same side as its anchor: the lowest it
        # overlaps for a `v1` anchor, the highest for a `v2` one. Deciding this
        # per segment, as a centre-containment test used to, put a door whose
        # centre sat exactly ON a cut into BOTH segments.
        owner = {}
        for oi, o in enumerate(w["openings"]):
            lo = o["s"] - o["width"] / 2.0
            hi = o["s"] + o["width"] / 2.0
            over = [k for k in range(len(stops) - 1)
                    if stops[k] - 1e-6 < hi and lo < stops[k + 1] + 1e-6]
            if not over:
                continue
            whole = [k for k in over
                     if stops[k] - 1e-6 <= lo and hi <= stops[k + 1] + 1e-6]
            if whole:
                owner[oi] = whole[0]
            else:
                owner[oi] = over[-1] if o.get("from") == "v2" else over[0]
        for k in range(len(stops) - 1):
            s0, s1 = stops[k], stops[k + 1]
            if s1 - s0 < MIN_SPAN:
                continue
            v1 = vt.get((a[0] + u[0] * s0, a[1] + u[1] * s0), lid)
            v2 = vt.get((a[0] + u[0] * s1, a[1] + u[1] * s1), lid)
            if v1 == v2:
                continue
            rep["segments"] += 1
            seg_ops, seg_len = [], s1 - s0
            for oi, o in enumerate(w["openings"]):
                s = o["s"]
                if owner.get(oi) != k:
                    continue
                ow = o["width"]
                if ow > seg_len + 1e-6:
                    rep["openings_dropped"] += 1
                    continue
                loc = s - s0
                # R4b -- FIDELITY WHERE THE ANCHORED END SURVIVES, re-seat where
                # it does not, and mint nowhere here.
                #
                # A wall is emitted as one or more SEGMENTS. If the end this
                # opening is dimensioned off is still an end of the segment it
                # lands on -- `p1` and the segment starts at 0, or `p2` and the
                # segment ends at the wall's far end -- the stored anchor is
                # carried VERBATIM, offset and all. Recomputing a nearer-end
                # anchor over the top is what R4b overrules: the anchor end
                # decides which way the opening moves when the wall is
                # stretched, so rewriting it on save is a silent loss of intent.
                #
                # When a split has cut the anchored end off this segment, the
                # anchor RE-SEATS to the same-side end of the segment (R2b) --
                # low end for a `v1` anchor, high end for a `v2` one -- which
                # preserves the opening's position exactly and changes only its
                # description. Never the NEARER end: that would flip the anchor
                # for openings that happen to sit past the midpoint.
                held = o.get("from")
                at_v1 = held != "v2" and s0 <= 1e-6
                at_v2 = held == "v2" and s1 >= L - 1e-6
                # R2c -- THE WALK IS TOTAL: it reports and emits, it never
                # slides. `max(0.0, off)` used to pull a straddling opening back
                # onto the segment, which is the same silent repair the charter
                # deletes from `rebuild`, hiding in a different room. A door the
                # document must cut in half is a real fault; it is emitted where
                # R2b puts it and FILED, and `verify` learns to expect an I7
                # for exactly the openings that were filed.
                straddles = not (s0 - 1e-6 <= s - ow / 2.0
                                 and s + ow / 2.0 <= s1 + 1e-6)
                if at_v1 or at_v2:
                    frm = held
                    off = float(o.get("offset_in", 0.0))
                else:
                    # SAME SIDE (R2b), for a re-seat and for a straddler alike:
                    # low end for a v1 anchor, high end for a v2 one. Position
                    # is preserved exactly; only the description changes.
                    frm = "v2" if held == "v2" else "v1"
                    off = ((loc if frm == "v1" else seg_len - loc) - ow / 2.0)
                oid = nid("o")
                rec = {"id": oid, "kind": o["kind"], "code": o["code"],
                       "anchor": {"from": frm, "offset_in": round(off, 3)}}
                if straddles:
                    rep["openings_failed"].append(
                        f"{oid}: {o['kind']} {o['code']} on the wall at "
                        f"{tuple(round(v, 1) for v in a)} is cut by a junction "
                        f"-- anchored {round(off, 1)}\" from {frm}, and no "
                        f"segment can hold it")
                    rep["openings_failed_ids"].add(oid)
                near1 = frm != "v2"
                if o["kind"] == "door":
                    dt = o["door_type"]
                    rec["door_type"] = dt
                    m = ({"LH": "v1", "RH": "v2"} if near1
                         else {"LH": "v2", "RH": "v1"})
                    rec["hinge"] = m.get(dt, "none")
                    rec["swings_toward"] = "left" if o["swing"] < 0 else "right"
                if _sig(rec) in {_sig(x) for x in seg_ops}:
                    rep["openings_deduped"] += 1   # stacked identical opening
                    continue
                seg_ops.append(rec)

            key = (*sorted((v1, v2)),)
            if src is not None:
                src.setdefault(key, w_items[i])    # which scene wall covers it
            if key in by_pair:                     # invariant I4 enforced here
                ex = by_pair[key]
                rep["merged"] += 1
                if w["type"] == "exterior":
                    ex["type"] = "exterior"
                have = {_sig(x) for x in ex["openings"]}
                for o in seg_ops:
                    if _sig(o) not in have:
                        have.add(_sig(o))
                        ex["openings"].append(o)
                continue
            rec = {"id": nid("w"), "level": lid, "v1": v1, "v2": v2,
                   "type": w["type"], "left": None, "right": None,
                   "openings": seg_ops}
            rec.update(w["extra"])         # thickness_in / finish_*: unmodelled
            walls.append(rec)
            by_pair[key] = rec
    return walls


def _sig(op):
    return (op["kind"], op["code"], op["anchor"]["from"],
            round(op["anchor"]["offset_in"], 1))


def _rooms_of(items, lid, nid, vt, walls, rep, src=None):
    """This level's rooms, outlined from each `RoomItem.corners` -- the scene's
    own belief about its shape.  An edge no run of walls covers is emitted OPEN
    (`wall: null`) rather than invented; the room keeps its exact shape."""
    edge, adj = {}, defaultdict(list)
    for wr in walls:
        edge[(wr["v1"], wr["v2"])] = wr
        edge[(wr["v2"], wr["v1"])] = wr
        adj[wr["v1"]].append(wr["v2"])
        adj[wr["v2"]].append(wr["v1"])

    rooms = []
    for r in _ordered(items, RoomItem, _room_key):
        if not r.corners or len(r.corners) < 3:
            rep["rooms_without_outline"] += 1     # flood-fill only, no perimeter
            continue
        cv = [vt.get((c.x(), c.y()), lid) for c in r.corners]
        cv = [v for i, v in enumerate(cv) if v != cv[i - 1]]
        if len(cv) < 3:
            rep["rooms_without_outline"] += 1
            continue
        loop = []
        for i in range(len(cv)):
            va, vb = cv[i], cv[(i + 1) % len(cv)]
            chain = _walk(va, vb, edge, adj, vt)
            if chain is None:
                loop.append({"v": va, "wall": None})
                rep["open_edges"] += 1
            else:
                for a_, b_ in chain:
                    loop.append({"v": a_, "wall": edge[(a_, b_)]["id"]})
        if len(loop) < 3:
            rep["rooms_without_outline"] += 1
            continue

        pts = [vt.xy(e["v"]) for e in loop]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        props = dict(r.properties)
        # the outline IS the perimeter now; keeping the v4 mirror would store
        # the same geometry twice and let the two disagree (P3.2 drops it from
        # the scene side too)
        props.pop("perimeter_corners", None)
        low = r.name.lower()
        rec = {
            "id": nid("r"), "level": lid, "name": r.name,
            # P4.4: the item's own category wins; the name heuristic is the
            # FALLBACK for a room that was never told one (which is every
            # room drawn before concept rooms existed)
            "category": (getattr(r, "category", None)
                         or ("exterior" if any(k in low for k in EXTERIOR_NAMES)
                             else "interior")),
            "outline": loop,
            # P4.2: placement is MODELLED on the item now -- the walk reads it
            # rather than stamping "placed", so a floating room round-trips
            # through save, undo and verify without the stash
            "placement": {
                "state": getattr(r, "placement_state", None) or "placed",
                "rotation": float(getattr(r, "placement_rotation", 0.0) or 0.0),
                "extracted_from": getattr(r, "extracted_from", None)},
            "label": {"offset": [round(r.anchor.x() + r.label_offset.x() - cx, 3),
                                 round(r.anchor.y() + r.label_offset.y() - cy, 3)],
                      "show_dimensions": bool(r.show_dims),
                      "show_area": True},
            "properties": props,
        }
        if getattr(r, "nominal_size", None):     # P4.4, modelled on the item
            rec["nominal_size"] = dict(r.nominal_size)
        # v5 fields the SCENE has no home for (area_accounting, holes) ride
        # back out verbatim, or a save would quietly drop them -- measured: symmetricP1's Garage lost area_accounting:
        # "unconditioned". The derived defaults above stand for a scene that
        # was never loaded from a v5 document. (`placement` left the stash at
        # P4.2 -- it is modelled above.)
        rec.update(getattr(r, "_v5_extra", None) or {})
        if src is not None:               # which scene room (P4.5)
            src[rec["id"]] = r
        rooms.append(rec)
    return rooms


def _bind_sides(rooms, walls, vt):
    """Fill each wall's `left`/`right` from the outlines that name it.

    Direction is derived, never stored: probe just off the midpoint of the
    outline edge on the wall's `(dy, -dx)` side and ask whether that lands
    inside the room.  Invariant I6 checks the result against the outlines."""
    poly = {rm["id"]: [vt.xy(e["v"]) for e in rm["outline"]] for rm in rooms}
    wmap = {w["id"]: w for w in walls}
    for rm in rooms:
        pts = poly[rm["id"]]
        n = len(rm["outline"])
        for i, e in enumerate(rm["outline"]):
            if not e["wall"]:
                continue
            a = vt.xy(e["v"])
            b = vt.xy(rm["outline"][(i + 1) % n]["v"])
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1.0
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            probe = (m[0] + dy / ln * 2.0, m[1] - dx / ln * 2.0)  # (dy,-dx)=left
            side = "left" if _pip(probe, pts) else "right"
            if wmap[e["wall"]]["v1"] != e["v"]:      # outline runs v2 -> v1
                side = "right" if side == "left" else "left"
            wmap[e["wall"]][side] = rm["id"]
    return poly


def _furnishings_of(items, lid, nid, rooms, poly, src=None):
    """This level's furnishings, each owned by the SMALLEST room containing it
    (a closet inside a bedroom belongs to the closet)."""
    out = []
    for it in _ordered(items, FurnishingItem, _furn_key):
        p = (it.pos().x(), it.pos().y())
        owner, best = None, None
        for rm in rooms:
            pts = poly[rm["id"]]
            if _pip(p, pts):
                a = abs(_area2(pts))
                if best is None or a < best:
                    best, owner = a, rm["id"]
        rec = {"id": nid("f"), "level": lid, "kind": it.kind, "room": owner,
               "pos": [p[0], p[1]], "rotation": float(it.rotation())}
        state = dict(it.extra_state())
        if state:
            rec["state"] = state
        if src is not None:               # which scene item (P4.5)
            src[rec["id"]] = it
        out.append(rec)
    return out


def _roofs_of(items, lid, nid, src=None):
    """This level's roofs (0139-ruling.md P1.1, R2's first writer). Only
    the modelled fields are emitted -- `span_in` is a live-scene render
    affordance, not a document field (`RoofItem`'s own docstring), so a
    round trip re-derives it on load rather than persisting it here."""
    out = []
    for it in _ordered(items, RoofItem, _roof_key):
        rec = {"id": nid("rf"), "level": lid,
               "ridge": [[it.p1.x(), it.p1.y()], [it.p2.x(), it.p2.y()]],
               "eaves_h_in": float(it.eaves_h_in),
               "ridge_h_in": float(it.ridge_h_in),
               "overhang_in": float(it.overhang_in),
               "gable": [bool(it.gable[0]), bool(it.gable[1])],
               "marker_end": 1 if it.marker_end else 0}
        if src is not None:
            src[rec["id"]] = it
        out.append(rec)
    return out


# ------------------------------------------------------------------ public API
def design_from_scene(source, floors=None, report=None, strict=False) -> Design:
    """Walk the live scene into a v5 `Design`.

    `source` is a `MainWindow` (preferred -- it owns the authoritative floor
    roster) or a bare `QGraphicsScene`.  Pass a dict as `report` to receive the
    walk's counts AND `report["wall_items"]` (0101-ruling.md): `{final
    (canonical) wall id: WallItem}` -- the composition of the `src` out-param
    `_walls_of` already builds (live item -> pre-canonical id) with
    `canonicalize()`'s own renumbering (pre-canonical id -> final id), which
    were computed separately and both discarded on every prior call. Correlated
    by Python object identity on the wall dict itself (`canonicalize` mutates
    the SAME dicts in place, never copies), not by re-deriving a geometric
    match -- so it survives a merge or a split exactly as `of_item` (the
    group-membership map two lines below) already does for the reverse
    direction. A snapshot of this one walk: stale the instant the scene
    changes again, same as everything else this function returns.
    `strict=True` raises instead of warning when the weld check finds the
    scene disagreeing with itself (P1.6's `--verify-design` hook)."""
    scene, roster = _resolve(source, floors)
    seq = defaultdict(int)

    def nid(prefix):
        seq[prefix] += 1
        return f"{prefix}{seq[prefix]}"

    rep = report if report is not None else {}
    rep.update(_new_walk_report())
    rep["levels"] = len(roster)

    buckets = _by_floor(scene)
    levels, vertices, walls, rooms, furnishings, roofs = [], [], [], [], [], []
    groups = []                            # P4.5, defect 3
    # id(wall dict object) -> live WallItem (0101-ruling.md), ACROSS ALL
    # LEVELS -- unlike `of_item` a few lines below (per-level on purpose,
    # consumed within the same iteration for that level's own groups),
    # this one is read only once, after the whole roster loop, against the
    # FULLY ACCUMULATED `walls` list -- so it must accumulate too, not
    # reset per floor.
    wall_of_item = {}
    for f in roster:                       # LEVELS OUTER -- see the module note
        lid = nid("L")
        levels.append({"id": lid, "name": f.name, "elevation_in": 0.0,
                       "height_in": 96.0, "kind": "storey",
                       "reference": bool(f.reference)})
        items = buckets.get(f.name, [])    # ...ITEMS INNER, and only these
        # P4.2: a FLOATING room folds among its own items only. The lift's
        # "coincident coordinates are one corner" rule is exactly the sharing
        # a floating room has explicitly broken (I12), so each floating room
        # walks with its OWN vertex table -- a room parked over its old berth
        # emits private vertices instead of being silently re-welded to the
        # plan, and a floating room a gesture-width from a wall is not an
        # "unwelded end" (the weld check runs per partition too).
        parts = _partitions(items)
        lw_all, lr_all, poly_all = [], [], {}
        # P4.5 (defect 3): which live item produced which document id, so a
        # GROUP can be emitted as the member ids it actually holds. The wall
        # map is the `src` out-param that already exists for `face_at` -- one
        # mechanism, not a second geometric match -- and a live wall may map
        # to SEVERAL document walls, because the walk splits it at junctions.
        # That is why membership is a set of document objects rather than a
        # 1:1 id: the group holds whatever its member became.
        of_item = {}                       # id(live) -> [document ids]

        def _note(doc_id, live, of_item=of_item):   # bound: B023
            of_item.setdefault(id(live), []).append(doc_id)

        for part in parts:
            vt = VertexTable(lambda: nid("v"))
            wsrc, rsrc = {}, {}
            lw = _walls_of(part, lid, nid, vt, rep, src=wsrc)
            lr = _rooms_of(part, lid, nid, vt, lw, rep, src=rsrc)
            for rec in lw:
                live = wsrc.get((*sorted((rec["v1"], rec["v2"])),))
                if live is not None:
                    _note(rec["id"], live)
                    # keyed by the DICT OBJECT, not its (about to be
                    # renumbered) "id" string -- canonicalize() mutates this
                    # same object in place, so the correlation survives its
                    # own renumbering without re-deriving anything.
                    wall_of_item[id(rec)] = live
            for rid_, live in rsrc.items():
                _note(rid_, live)
            poly_all.update(_bind_sides(lr, lw, vt))
            # I10: emit only the vertices some wall or outline actually uses
            used = {v for w in lw for v in (w["v1"], w["v2"])}
            used |= {e["v"] for rm in lr for e in rm["outline"]}
            vertices += [row for row in vt.rows if row["id"] in used]
            lw_all += lw
            lr_all += lr
        fsrc = {}
        lf = _furnishings_of(items, lid, nid, lr_all, poly_all, src=fsrc)
        for fid_, live in fsrc.items():
            _note(fid_, live)
        rfsrc = {}
        lroofs = _roofs_of(items, lid, nid, src=rfsrc)
        for rfid_, live in rfsrc.items():
            _note(rfid_, live)
        # ...and the groups themselves: a membership list over what the walk
        # emitted, per the schema's "a group NEVER copies anything".
        for g in _ordered(items, GroupItem, lambda g: (id(g),)):
            members = sorted({d for ch in g.childItems()
                              for d in of_item.get(id(ch), ())})
            if not members:                # schema: minItems 1
                continue
            rec = {"id": nid("g"), "level": lid, "members": members}
            rot = float(g.rotation() or 0.0)
            if rot:
                rec["rotation"] = rot
            groups.append(rec)
        walls += lw_all
        rooms += lr_all
        furnishings += lf
        roofs += lroofs

    n = rep["unwelded_ends"]
    if n and strict:
        raise ValueError(
            f"design_from_scene: {n} wall end(s) sit within the {JOIN_TOL}\" "
            f"join tolerance of a neighbour without being welded to it. The "
            f"scene disagrees with itself; the Design reports the scene's own "
            f"coordinates unchanged.")
    _warn_unwelded(scene, n)

    settings = dict(SETTINGS)
    # the editing block is emitted from the LIVE flags (P4.3 -- the hardcoded
    # block predates the runtime half existing); the flat copies are popped so
    # each flag exists once, inside `editing`, where the schema puts it
    editing = {"shuffle": bool(settings.pop("shuffle", False)),
               "auto_coalesce": bool(settings.pop("auto_coalesce", True)),
               "auto_weld": bool(settings.pop("auto_weld", True)),
               "auto_bind": bool(settings.pop("auto_bind", True))}
    settings["vertex_weld_in"] = WELD_TOL
    settings["join_tol_in"] = JOIN_TOL
    # centerline, NOT the migrator's inside_face: the scene's areas ARE
    # centreline areas, and declaring the better basis would be a repair
    settings["area_basis"] = "centerline"
    settings["editing"] = editing

    design_doc = canonicalize({
        "format": "floorplanner-design",
        # R1's own migration discipline (0139-ruling.md sec1): a document
        # with no roofs at all stays version 5, no key emitted; roofs bump
        # it to 6, the only condition that does (design-schema.v5.json's
        # own `version` description).
        "version": 6 if roofs else 5,
        "units": "inches",
        "settings": settings, "levels": levels, "vertices": vertices,
        "walls": walls, "rooms": rooms, "furnishings": furnishings,
        **({"roofs": roofs} if roofs else {}),
        # DEFECT 3 CLOSES AT P4.5. The old note here said a grouped wall
        # "has no single id -- it splits into segments", and that is still
        # true: the answer is that membership is a SET of document objects,
        # so a wall that split contributes every segment it became. The
        # `src` out-param that `face_at` already uses is what maps live item
        # to emitted id, so no second (geometric) matcher was invented.
        "groups": groups,
    })
    # 0101-ruling.md: canonicalize() mutated `walls`' dicts IN PLACE (sorted
    # the list, renumbered each "id"), so the same objects `wall_of_item`
    # keyed by identity are still these ones -- read the id it wrote.
    rep["wall_items"] = {w["id"]: wall_of_item[id(w)] for w in walls
                         if id(w) in wall_of_item}
    return Design.from_dict(design_doc)


# -------------------------------------------------- "detect room here" (P3.5)
def _prune_spurs(ids):
    """Drop out-and-back excursions from a traced face loop.

    A wall that dangles into (or off) a room -- a stub with a degree-1 end --
    is part of the wall graph and therefore part of the face walk, which enters
    it and comes straight back out. That is correct for a FACE (the excursion
    encloses no area, so it costs nothing) and wrong for a room OUTLINE: the
    room would carry a corner at the stub's free end, miles off its boundary,
    and every consumer that asks "is this room inside the rubber band" or "how
    long is its perimeter" would answer from it.

    A tip is a vertex whose predecessor and successor in the loop are the same
    vertex. Removing it and one of the two visits to that neighbour leaves a
    loop whose consecutive pairs are still graph edges, so the edge -> wall
    mapping survives. Repeated, because a stub can hang off a stub."""
    out = list(ids)
    guard = 0
    while len(out) > 3 and guard < 4 * len(ids) + 8:
        guard += 1
        n = len(out)
        tip = next((i for i in range(n)
                    if out[(i - 1) % n] == out[(i + 1) % n]), None)
        if tip is None:
            break
        for k in sorted((tip, (tip + 1) % n), reverse=True):
            del out[k]
    return out


def face_at(scene, point, floor=None):
    """The wall-graph face enclosing `point`, as `[(QPointF corner, WallItem
    covering the edge that STARTS there), ...]`, or None.

    THE ONE-SHOT LIFT. This is P3.5's replacement for the flood-fill room
    detector: the scene's walls are lifted to a `Design` and
    `topology.enclosing_face` answers on it -- the room a click falls in is the
    face around it, which is a question about the wall graph and was never a
    question about pixels.

    Lifting a whole level per call is exactly what P3.4's point 1 rejected for
    edit ops, and the distinction is the reason this is allowed: an edit happens
    per mouse event and must touch only what it names, but "detect room here" is
    a ONE-SHOT gesture -- six call sites, each once per user action. Paying a
    plan walk there costs no more than the `_RoomGrid` + `_WallGraph` pair it
    replaces (both were rebuilt per call too, and the graph's split-finding was
    O(walls^2)), and it single-sources the topology instead of keeping a second
    implementation of it in the editor.

    THREE THINGS COME FOR FREE, and they are the reason the swap is worth making
    rather than merely equivalent:
      * the walk is unbounded, so DEFECT 16 closes structurally -- the raster
        grid was clipped to `canvas_rect()` and silently lost the edge rooms of
        any plan larger than the canvas;
      * every returned edge names the wall covering it, so a room binds its
        outline at creation instead of searching for its own walls afterwards;
      * a wall split at a T-junction yields one edge per SEGMENT, which is
        invariant I5 ("every outline edge maps to exactly one wall") holding by
        construction. The old tracer dropped those pass-through corners, so a
        room could carry an edge no single wall covered.
    """
    from floorplanner.design import topology as T

    lid = "L1"
    items = _by_floor(scene).get(floor or active_floor(), [])
    seq = defaultdict(int)

    def nid(prefix):
        seq[prefix] += 1
        return f"{prefix}{seq[prefix]}"

    vt = VertexTable(lambda: nid("v"))
    src = {}
    # D57: the report SHAPE is a contract, not a counter -- `_walls_of` appends
    # to it. This used to pass `defaultdict(int)` and died on the first plan
    # whose opening no segment could hold. `face_at` still discards the report;
    # that a straddler is recorded here and thrown away is filed separately.
    walls = _walls_of(items, lid, nid, vt, _new_walk_report(), src,
                      weld_check=False)
    if not walls:
        return None
    used = {v for w in walls for v in (w["v1"], w["v2"])}
    design = Design.from_dict({
        "levels": [{"id": lid, "name": "detect", "elevation_in": 0.0,
                    "height_in": 96.0, "kind": "storey"}],
        "vertices": [r for r in vt.rows if r["id"] in used],
        "walls": walls, "rooms": [], "furnishings": [],
    })
    face = T.enclosing_face(design, (point.x(), point.y()), lid)
    if face is None:
        return None
    ids = _prune_spurs(face.vertices)
    if len(ids) < 3:
        return None
    # CANONICAL WINDING, and it is not cosmetic. `_inner_faces` picks the inner
    # sign by MAJORITY, which is decisive from two rooms on but a tie at one:
    # a lone wall loop traces two faces of equal area and opposite winding, so
    # which one comes back depends on the rest of the plan. The vertex set is
    # the same either way, but the outline's ORDER is not -- and that order is
    # serialized, so the same room round-tripped through save/load came back
    # wound the other way. Fixed here at the one-shot entry, to the sign the
    # document already uses for inner faces (positive shoelace, interior on the
    # `left` side of each edge -- verified against every face of symmetricP1).
    if _area2([vt.xy(v) for v in ids]) < 0:
        ids = ids[:1] + ids[:0:-1]             # reverse, keeping the start
    out = []
    for i, vid in enumerate(ids):
        x, y = vt.xy(vid)
        nxt = ids[(i + 1) % len(ids)]
        out.append((QPointF(x, y), src.get((*sorted((vid, nxt)),))))
    return out


# ------------------------------------------------------- Design -> scene (P1.5)
def _opening_s(frm, off, ow, L):
    """Distance of an opening's CENTRE from the wall's v1 -- the exact inverse
    of the s -> anchor conversion in `_walls_of`.

    v4's absolute `s` is not stored; `{from, offset_in}` is an offset from a
    NAMED end to the opening's near edge, so recovering `s` means adding back
    half the width on the correct side. Getting this wrong by half a width is
    the failure that would look like a door sliding on every save/load cycle."""
    if frm == "v1":
        return off + ow / 2.0
    if frm == "v2":
        return L - off - ow / 2.0
    return L / 2.0 + off                       # "center": offset of the centre


def apply_design_to_scene(target, design, report=None, strict=False,
                          keep_backdrop=False):
    """Build the scene from a v5 `Design`.  The mirror of `design_from_scene`,
    and held to `scene -> Design -> scene -> Design` identity at the second
    `Design`.

    `target` is a `MainWindow` or a bare `QGraphicsScene`.  Four rules, all of
    them in service of that identity:

    **No coalesce, no weld, no detection.**  `apply_project_to_scene` runs
    `coalesce_all`; this must not.  Coalesce MOVES geometry -- it re-snaps the
    surviving wall's endpoints onto the 6" grid (`walls.py:200-201`, the
    corrected F5 mechanism) -- so a single pass would make the second `Design`
    differ from the first through no fault of the bridge.  Walls are built, then
    `rebuild_all_walls` runs once for rendering only.

    **Rooms are read, never re-detected.**  Each `RoomItem` takes its corners
    straight from the stored outline, and its region derives from those.  This
    used to need two defences -- rebuilding before any room existed, so
    `refresh_rooms` hit its empty-list guard, and then priming each room's
    detection memo so a later rebuild left it alone.  P3.5 deleted the pass both
    were guarding against, so the rule now holds because there is nothing that
    could break it.

    **Openings invert exactly.**  See `_opening_s`.

    **Every item's `floor` is assigned from its level explicitly**, never left
    to the `active_floor()` global that constructors read -- that global lies
    during a load, which is why `mainwindow.py:1348` needs its band-aid.

    `keep_backdrop` detaches the tracing image across the rebuild instead of
    letting `scene.clear()` delete it -- undo must not throw away the backdrop
    the user is tracing over (wired at P2.3, which is what made undo go through
    this function)."""
    scene, win = ((target, None) if isinstance(target, QGraphicsScene)
                  else (target.scene, target))
    doc = design.to_dict() if isinstance(design, Design) else design
    rep = report if report is not None else {}
    rep.update({"walls": 0, "rooms": 0, "furnishings": 0, "roofs": 0,
                "openings_failed": [], "unknown_furnishings": []})

    settings = doc.get("settings") or {}
    editing = settings.get("editing") or {}
    for key, default in DEFAULT_SETTINGS.items():
        val = editing.get(key, settings.get(key, default))
        SETTINGS[key] = coerce_setting(key, val, default)
    if win is not None:
        # settings the walk does not re-emit (a document `name`, anything a
        # later phase adds) would otherwise evaporate on the first save
        win._doc_settings = {k: v for k, v in settings.items()
                             if k not in WALK_SETTINGS and k != "active_floor"}
        # the v5 open path never reaches _apply_canvas, so the editing-mode
        # UI (the shuffle toggle) re-syncs here (P4.3)
        sync = getattr(win, "_sync_editing_ui", None)
        if sync is not None:
            sync()
        # same reasoning, R2c (0145-ruling.md sec2): the Roof menu's own
        # Show/Edit checkboxes and the ridge-sketch tool's enabled state
        sync = getattr(win, "_sync_roof_ui", None)
        if sync is not None:
            sync()

    backdrops = []
    if keep_backdrop:
        backdrops = [it for it in scene.items()
                     if isinstance(it, ReferenceImageItem)]
        for b in backdrops:
            scene.removeItem(b)
    scene.clear()
    for b in backdrops:
        scene.addItem(b)
    levels = doc.get("levels") or [{"id": "L1", "name": DEFAULT_FLOOR}]
    lname = {lv["id"]: lv.get("name", DEFAULT_FLOOR) for lv in levels}
    if win is not None:
        win.floors = [Floor(lv.get("name", DEFAULT_FLOOR),
                            bool(lv.get("reference", False))) for lv in levels]
        # active_floor is view state and is not carried by the document; keep
        # the current one when the new roster still has it
        # active_floor is VIEW state. The v5 root is a closed schema, so a saved
        # document carries it inside `settings` (the designated open bag) -- the
        # same in-on-load / out-on-save arrangement v4 has via `_write_plan`.
        # It is stripped here and NEVER re-emitted by the walk, so switching
        # floors still cannot dirty the document.
        names = [f.name for f in win.floors]
        want = settings.get("active_floor")
        if want not in names:
            want = win.active_floor if win.active_floor in names else names[0]
        win.active_floor = want
        set_floor_state(active=win.active_floor)

    pos = {v["id"]: QPointF(v["x"], v["y"]) for v in doc.get("vertices", [])}
    # THE DOCUMENT'S VERTEX IDENTITY, CARRIED INTO THE SCENE (P3.5). One live
    # `Vertex` per document vertex, handed to every wall end and every outline
    # edge that names it -- so a corner two walls share in the file is one
    # corner in the scene, and a room's outline is holding the very object its
    # walls hold. Reconstructing that by WELDING here would be a repair, and
    # apply must not repair: a file whose corner has drifted 0.3" is malformed
    # and is reported as such, not quietly closed up
    # (`test_malformed_v5_is_reported_not_rewelded`).
    # fresh uids, NOT the document's ids: those are canonical (renumbered by
    # geometry at every save), and a live uid is persistent. P3.1 settled that
    # the two id spaces stay separate and `canonicalize` bridges them.
    vmap = {vid: Vertex(p.x(), p.y()) for vid, p in pos.items()}

    wmap = {}
    for wd in doc.get("walls", []):
        wall = WallItem(pos[wd["v1"]], pos[wd["v2"]], wd.get("type", "interior"))
        wall.set_end_vertex("p1", vmap[wd["v1"]])
        wall.set_end_vertex("p2", vmap[wd["v2"]])
        wall.floor = lname.get(wd["level"], DEFAULT_FLOOR)   # never the global
        wall._v5_extra = {k: v for k, v in wd.items() if k not in _WALL_MODELLED}
        scene.addItem(wall)
        wmap[wd["id"]] = wall
        rep["walls"] += 1
        L = wall.length()
        for od in wd.get("openings") or []:
            a = od["anchor"]
            ow = parse_wwhh(od["code"])[0]
            s = _opening_s(a["from"], float(a["offset_in"]), ow, L)
            try:
                op = OpeningItem(wall, od["kind"], od["code"], s)
            except ValueError as exc:
                # NOT the silent `except ValueError: continue` of the v4 path
                # (13 sites, replaced by a reported list at P3.6) -- collected,
                # surfaced, and escalated under strict
                rep["openings_failed"].append(f"{od['id']}: {exc}")
                continue
            # R4b -- FIDELITY: the document's anchor is adopted VERBATIM, not
            # re-derived. `OpeningItem.__init__` mints against the nearer end,
            # which is right for an opening that has never had an anchor and
            # wrong for one that arrived with a deliberate far-end dimension.
            # Re-basing it here would lose that intent on every load, silently
            # -- the same category as the clamp this task deletes.
            op.anchor_v = wall.end_vertex("p1" if a["from"] != "v2" else "p2")
            op.offset_in = float(a["offset_in"])
            # v5 carries door_type for DOORS only ("meaningful only when
            # kind == door"), so absent means "not applicable", not "empty" --
            # clobbering it would rewrite a window's harmless default and make
            # a round trip look like an edit.
            op.door_type = od.get("door_type", op.door_type)
            op.swing = -1 if od.get("swings_toward", "left") == "left" else 1
            wall.openings.append(op)

    # rendering only, and deliberately BEFORE any RoomItem exists: refresh_rooms
    # returns at `if not rooms` so no flood-fill can overwrite a stored outline
    rebuild_all_walls(scene)

    rmap, fmap = {}, {}            # P4.5: document id -> live item, for groups
    for rd in doc.get("rooms", []):
        corners = [pos[e["v"]] for e in rd["outline"]]
        cx = sum(c.x() for c in corners) / len(corners)
        cy = sum(c.y() for c in corners) / len(corners)
        off = (rd.get("label") or {}).get("offset") or [0.0, 0.0]
        # v5 stores ONE label offset, relative to the centroid; the scene splits
        # the same information across anchor + label_offset. Folding it all into
        # the anchor round-trips exactly (the walk re-derives centroid + offset).
        room = RoomItem(rd["name"], QPointF(cx + off[0], cy + off[1]),
                        room_path_from_corners(corners),
                        poly_area_sqft(corners),
                        rd.get("properties") or {},
                        [OutlineEdge(vmap[e["v"]], wmap.get(e.get("wall")))
                         for e in rd["outline"]])
        room.floor = lname.get(rd["level"], DEFAULT_FLOOR)   # never the global
        room._v5_extra = {k: v for k, v in rd.items() if k not in _ROOM_MODELLED}
        pl = rd.get("placement") or {}
        room.placement_state = pl.get("state") or "placed"
        room.extracted_from = pl.get("extracted_from")
        room.placement_rotation = float(pl.get("rotation") or 0.0)
        room.category = rd.get("category")           # P4.4, modelled
        room.nominal_size = rd.get("nominal_size")
        room.show_dims = bool((rd.get("label") or {}).get("show_dimensions",
                                                          False))
        room.label_offset = QPointF(0.0, 0.0)
        scene.addItem(room)
        rmap[rd["id"]] = room
        for e in room.outline:                  # the outline IS the binding --
            if e.wall is not None:                       # read, not detected
                room.bind_wall(e.wall)
            # An edge with `wall: null` -- an archway or a detached side --
            # stays null. Until P3.5 this branch built a dashed placeholder
            # item so undo would not silently drop an archway; the outline
            # carries that fact itself (`RoomItem.open_edges`), so the
            # placeholder was a second representation of it and went with the
            # rest of them. Since P3.7 a null edge renders dashed directly,
            # drawn by the room from its own outline.
        rep["rooms"] += 1

    for fd in doc.get("furnishings", []):
        if furnishing_spec(fd["kind"]) is None:
            rep["unknown_furnishings"].append(fd["kind"] or "?")
            continue
        item = make_furnishing(fd["kind"], QPointF(*fd["pos"]),
                               float(fd.get("rotation", 0.0)),
                               fd.get("state") or {})
        item.floor = lname.get(fd["level"], DEFAULT_FLOOR)   # never the global
        scene.addItem(item)
        fmap[fd["id"]] = item
        rep["furnishings"] += 1

    # ROOFS (0139-ruling.md R1's block, R2's first reader). `span_in` is not
    # a document field -- `nearest_eaves_wall` re-derives the 2D overlay's
    # plan reach from whatever wall is nearest and roughly parallel to the
    # ridge NOW, on THIS level, rather than trusting a value that could have
    # gone stale against the plan (see `RoofItem`'s own docstring).
    for rfd in doc.get("roofs", []) or []:
        p1 = QPointF(*rfd["ridge"][0])
        p2 = QPointF(*rfd["ridge"][1])
        floor = lname.get(rfd["level"], DEFAULT_FLOOR)
        _, span_in = nearest_eaves_wall(scene, p1, p2, floor)
        item = RoofItem(p1, p2, eaves_h_in=float(rfd["eaves_h_in"]),
                        ridge_h_in=float(rfd["ridge_h_in"]),
                        overhang_in=float(rfd.get("overhang_in", 0.0)),
                        gable=list(rfd.get("gable", [True, True])),
                        span_in=span_in,
                        marker_end=int(rfd.get("marker_end", 1)))
        item.floor = floor   # never the global
        scene.addItem(item)
        rep["roofs"] += 1

    # GROUPS (P4.5, defect 3). Rebuilt last, once every member exists, and
    # only from ids the document actually resolved -- a group whose members
    # all vanished is dropped rather than restored empty. `adopt` keeps each
    # child's scene position, which is what lets the group sit at (0,0) and
    # the members keep the absolute coordinates the document gave them.
    for gd in doc.get("groups", []) or []:
        members = [m for m in (gd.get("members") or [])
                   if m in wmap or m in rmap or m in fmap]
        live = [wmap.get(m) or rmap.get(m) or fmap.get(m) for m in members]
        live = [x for x in live if x is not None and not isinstance(x, RoomItem)]
        if len(live) < 2:
            continue                    # a group of one is not a group
        grp = GroupItem()
        grp.floor = lname.get(gd["level"], DEFAULT_FLOOR)
        scene.addItem(grp)
        for x in live:
            grp.adopt(x)
        if gd.get("rotation"):
            grp.setRotation(float(gd["rotation"]))

    if win is not None:
        win._sync_floor_state()
    # P1.6: apply is a LOAD -- it replaces the whole document, so its faults are
    # the new document's, not ones an operation introduced. Rebase, exactly as
    # apply_project_to_scene does. (Also stops the wall-decomposition change
    # from reading as a regression: Design walls are edge-granular, so a plan
    # rebuilt from an identical Design has more, shorter walls than it started
    # with.)
    from floorplanner.design.verify import rebase   # late: verify imports this
    rebase(target)
    rebase_weld_baseline(scene)        # ...and the weld counter, for the same reason

    if rep["openings_failed"]:
        msg = ("apply_design_to_scene: %d opening(s) could not be placed: %s"
               % (len(rep["openings_failed"]), "; ".join(rep["openings_failed"])))
        if strict:
            raise ValueError(msg)
        warnings.warn(msg, stacklevel=2)
    return scene
