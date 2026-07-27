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

from PyQt6.QtWidgets import QGraphicsScene

from floorplanner.config import DEFAULT_FLOOR, JOIN_TOL, SETTINGS
from floorplanner.design.legacy import (
    MIN_SPAN, ON_SEG_TOL, WELD_TOL, VertexTable, split_params, weld_endpoints,
)
from floorplanner.design.model import Design
from floorplanner.items import FurnishingItem
from floorplanner.model import Floor
from floorplanner.rooms import RoomItem
from floorplanner.walls import WallItem

# names that make a room exterior rather than interior.  Kept identical to
# tools/migrate_to_design_v5.py so a plan walked from the scene and the same
# plan imported at P2.1 classify alike.  Deliberately NOT extended to
# area_accounting: the scene already states that, per room, in
# properties["include_sqft"].
EXTERIOR_NAMES = ("porch", "deck", "patio", "terrace", "lanai")


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


# ------------------------------------------------------------------ weld check
def _weld_delta(raw):
    """How many wall ends `weld_endpoints` WOULD move on this level's geometry,
    run against a copy so nothing here is mutated.  0 on a scene that agrees
    with itself; non-zero is a finding, reported by the caller."""
    probe = copy.deepcopy(raw)
    weld_endpoints(probe)
    moved = 0
    for before, after in zip(raw, probe, strict=False):
        for k in ("p1", "p2"):
            if math.dist(tuple(before[k]), tuple(after[k])) > 1e-9:
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


# ------------------------------------------------------------------ level walk
def _walls_of(items, lid, nid, vt, rep):
    """This level's walls, split at every junction and room corner, as v5 wall
    dicts.  Openings are re-anchored from absolute `s` to {from, offset_in} on
    the segment that carries them."""
    w_items = [it for it in items
               if isinstance(it, WallItem) and not it.is_open]
    r_items = [it for it in items if isinstance(it, RoomItem)]
    raw = [{"p1": [w.p1.x(), w.p1.y()], "p2": [w.p2.x(), w.p2.y()],
            "type": w.wall_type,
            "openings": sorted(
                [{"kind": o.kind, "code": o.code, "s": float(o.s),
                  "width": float(o.width), "door_type": o.door_type,
                  "swing": float(o.swing)} for o in w.openings],
                key=lambda o: o["s"])}
           for w in w_items]
    rep["unwelded_ends"] += _weld_delta(raw)

    loops = [[(c.x(), c.y()) for c in r.corners] for r in r_items if r.corners]
    prep, cuts = split_params(raw, loops)

    walls, by_pair = [], {}
    for i, w in enumerate(raw):
        a, _b, u, L = prep[i]
        stops = sorted({0.0, L} |
                       {c for c in cuts[i] if MIN_SPAN < c < L - MIN_SPAN})
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
            for o in w["openings"]:
                s = o["s"]
                if not (s0 - 1e-6 <= s <= s1 + 1e-6):
                    continue
                ow = o["width"]
                if ow > seg_len + 1e-6:
                    rep["openings_dropped"] += 1
                    continue
                loc = s - s0
                near1 = loc <= seg_len / 2.0
                off = (loc if near1 else seg_len - loc) - ow / 2.0
                rec = {"id": nid("o"), "kind": o["kind"], "code": o["code"],
                       "anchor": {"from": "v1" if near1 else "v2",
                                  "offset_in": round(max(0.0, off), 3)}}
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
            walls.append(rec)
            by_pair[key] = rec
    return walls


def _sig(op):
    return (op["kind"], op["code"], op["anchor"]["from"],
            round(op["anchor"]["offset_in"], 1))


def _rooms_of(items, lid, nid, vt, walls, rep):
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
    for r in [it for it in items if isinstance(it, RoomItem)]:
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
        rooms.append({
            "id": nid("r"), "level": lid, "name": r.name,
            "category": ("exterior" if any(k in low for k in EXTERIOR_NAMES)
                         else "interior"),
            "outline": loop,
            "placement": {"state": "placed", "rotation": 0.0,
                          "extracted_from": None},
            "label": {"offset": [round(r.anchor.x() + r.label_offset.x() - cx, 3),
                                 round(r.anchor.y() + r.label_offset.y() - cy, 3)],
                      "show_dimensions": bool(r.show_dims),
                      "show_area": True},
            "properties": props,
        })
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


def _furnishings_of(items, lid, nid, rooms, poly):
    """This level's furnishings, each owned by the SMALLEST room containing it
    (a closet inside a bedroom belongs to the closet)."""
    out = []
    for it in [x for x in items if isinstance(x, FurnishingItem)]:
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
        out.append(rec)
    return out


# ------------------------------------------------------------------ public API
def design_from_scene(source, floors=None, report=None, strict=False) -> Design:
    """Walk the live scene into a v5 `Design`.

    `source` is a `MainWindow` (preferred -- it owns the authoritative floor
    roster) or a bare `QGraphicsScene`.  Pass a dict as `report` to receive the
    walk's counts; `strict=True` raises instead of warning when the weld check
    finds the scene disagreeing with itself (P1.6's `--verify-design` hook)."""
    scene, roster = _resolve(source, floors)
    seq = defaultdict(int)

    def nid(prefix):
        seq[prefix] += 1
        return f"{prefix}{seq[prefix]}"

    rep = report if report is not None else {}
    rep.update({"levels": len(roster), "segments": 0, "merged": 0,
                "open_edges": 0, "openings_dropped": 0, "openings_deduped": 0,
                "rooms_without_outline": 0, "unwelded_ends": 0})

    buckets = _by_floor(scene)
    levels, vertices, walls, rooms, furnishings = [], [], [], [], []
    for f in roster:                       # LEVELS OUTER -- see the module note
        lid = nid("L")
        levels.append({"id": lid, "name": f.name, "elevation_in": 0.0,
                       "height_in": 96.0, "kind": "storey",
                       "reference": bool(f.reference)})
        items = buckets.get(f.name, [])    # ...ITEMS INNER, and only these
        vt = VertexTable(lambda: nid("v"))
        lw = _walls_of(items, lid, nid, vt, rep)
        lr = _rooms_of(items, lid, nid, vt, lw, rep)
        poly = _bind_sides(lr, lw, vt)
        lf = _furnishings_of(items, lid, nid, lr, poly)
        # I10: emit only the vertices some wall or outline actually uses
        used = {v for w in lw for v in (w["v1"], w["v2"])}
        used |= {e["v"] for rm in lr for e in rm["outline"]}
        vertices += [row for row in vt.rows if row["id"] in used]
        walls += lw
        rooms += lr
        furnishings += lf

    if rep["unwelded_ends"]:
        msg = (f"design_from_scene: {rep['unwelded_ends']} wall end(s) sit "
               f"within the {JOIN_TOL}\" join tolerance of a neighbour without "
               f"being welded to it. The scene disagrees with itself; the "
               f"Design reports the scene's own coordinates unchanged. "
               f"Expected on a plan loaded from a legacy file -- load never "
               f"welds (see F5 in docs/CODE_REVIEW_v2.md).")
        if strict:
            raise ValueError(msg)
        warnings.warn(msg, stacklevel=2)

    settings = dict(SETTINGS)
    auto = bool(settings.pop("auto_coalesce", True))
    settings["vertex_weld_in"] = WELD_TOL
    settings["join_tol_in"] = JOIN_TOL
    # centerline, NOT the migrator's inside_face: the scene's areas ARE
    # centreline areas, and declaring the better basis would be a repair
    settings["area_basis"] = "centerline"
    settings["editing"] = {"shuffle": False, "auto_coalesce": auto,
                           "auto_weld": True, "auto_bind": True}

    return Design.from_dict({
        "format": "floorplanner-design", "version": 5, "units": "inches",
        "settings": settings, "levels": levels, "vertices": vertices,
        "walls": walls, "rooms": rooms, "furnishings": furnishings,
        # groups do not survive serialization today (defect 3) and a grouped
        # wall has no single id here -- it splits into segments.  Both close
        # together at P4.5, which is also what holds characterization test 3
        # xfail; emitting a guess now would make that test pass for the wrong
        # reason.
        "groups": [],
    })
