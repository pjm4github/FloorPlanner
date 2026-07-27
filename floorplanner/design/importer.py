"""Legacy v1-v4 `floorplanner-json` -> v5 `Design` (P2.1).

The derivation the editor otherwise repeats on every edit -- welding endpoints
into corners, splitting walls at junctions, tracing room perimeters -- runs ONCE
here and becomes the stored topology.

Ported from `tools/migrate_to_design_v5.py`, which is now a thin CLI over this
module (same move `validate.py` made at P0.7 and `topology.py` at P1.3). The
shared pieces come from their real homes rather than being copied: the weld and
the pre-vertex planarise from `legacy.py`, face tracing from `topology.py`. One
implementation each, so the app and the tool cannot drift.

**This is REPAIR, and it is the only place in the codebase allowed to be.**
`design_from_scene` (P1.4) reports what the scene believes and repairs nothing;
the repair happens here, once, at import, and is reported to the user and marked
dirty (S7a of `DESIGN_MODEL_v5.md`). Two consequences worth stating:

  * **Outlines are traced from the welded FILE geometry, never from the scene.**
    P1.4 measured why: loading `planc1.json` into a scene collapses Hall and
    M Bath into one identical 21-vertex region, where the file still holds them
    apart. The scene's belief about a corrupt file is strictly worse than the
    file, so importing through the scene would bake in damage the file does not
    contain.
  * **Two weld counters.** `weld_ops` (31 on planc1) is operations attempted and
    exists for cross-checks; `ends_moved` (4) counts only displacements above
    `vertex_weld_in`, and is the only number shown to a user or written to
    `provenance.endpoints_welded`.

`settings.area_basis` is written **`centerline`**, not the schema's `inside_face`
default. `inside_face` is the better number, but a conversion must not silently
restate every area in the same breath as moving four wall ends -- a user
reconciling the conversion report should not face two overlapping explanations
for why numbers moved. `inside_face` becomes an explicit opt-in at Phase 5, with
its own visible moment.
"""
import math
from collections import defaultdict

from floorplanner.design.canonical import canonicalize
from floorplanner.design.legacy import (
    JOIN_TOL, MIN_SPAN, ON_SEG_TOL, WELD_TOL, VertexTable, split_params,
    weld_endpoints_counted,
)
from floorplanner.design.model import Design
from floorplanner.design.topology import trace_faces

EXTERIOR_NAMES = ("porch", "deck", "patio", "terrace", "lanai")
UNCONDITIONED_NAMES = ("garage", "carport", "shed", "barn")


# ------------------------------------------------------------------ small math
def _d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _unit(a, b):
    L = _d(a, b)
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L) if L > 1e-9 else (1.0, 0.0)


def _proj(p, a, u):
    vx, vy = p[0] - a[0], p[1] - a[1]
    return vx * u[0] + vy * u[1], abs(vy * u[0] - vx * u[1])


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


def parse_wwhh(code):
    """Tolerant size-code parse: a legacy file may carry junk, and an import
    that raises on one bad door is worse than one that assumes a 32x80."""
    code = str(code).strip()
    if not code.isdigit() or len(code) not in (4, 5, 6):
        return (32.0, 80.0)
    k = 2 if len(code) == 4 else 3
    return (float(code[:k]), float(code[k:]))


def _walk(va, vb, level, edge, adj, vt, max_hops=10):
    """The wall chain from `va` to `vb`, or None. Used only by the stored-corner
    fallback, where a room edge may span several walls."""
    if (level, va, vb) in edge:
        return [(va, vb)]
    A, B = vt.xy(va), vt.xy(vb)
    L = _d(A, B)
    if L < 1e-6:
        return None
    u = _unit(A, B)
    chain, cur, guard = [], va, 0
    while cur != vb and guard < max_hops:
        guard += 1
        cs, _ = _proj(vt.xy(cur), A, u)
        best, bs = None, -1.0
        for nxt in adj[(level, cur)]:
            s, perp = _proj(vt.xy(nxt), A, u)
            if perp <= ON_SEG_TOL and cs + 1e-6 < s <= L + ON_SEG_TOL and s > bs:
                best, bs = nxt, s
        if best is None:
            return None
        chain.append((cur, best))
        cur = best
    return chain if cur == vb else None


# ------------------------------------------------------------------- the import
def import_legacy(src, tool="floorplanner.design.importer", design_name=None,
                  clean=True):
    """`(Design, report)` from a v1-v4 `floorplanner-json` dict.

    The source dict is never mutated -- the legacy file on disk must survive the
    conversion untouched, so the caller can decline it.

    `clean=True` (the load path, and the only mode P2.1 uses) welds, planarises
    and re-traces room outlines from the wall graph. `clean=False` is FAITHFUL:
    no weld, outlines straight from the stored `perimeter_corners`, warts and
    all. Faithful exists to prove the converter does not launder its input --
    it is what generates `examples/planc1.v5.json`, the deliberately-corrupt
    fixture that must keep failing I6 and I11."""
    if src.get("format") != "floorplanner-json":
        raise ValueError("not a floorplanner-json document")

    seq = defaultdict(int)

    def nid(prefix):
        seq[prefix] += 1
        return f"{prefix}{seq[prefix]}"

    lv_in = src.get("floors") or [{"name": "default", "reference": False}]
    lvl_id, levels = {}, []
    for f in lv_in:
        lid = nid("L")
        lvl_id[f.get("name", "default")] = lid
        levels.append({"id": lid, "name": f.get("name", "default"),
                       "elevation_in": 0.0, "height_in": 96.0,
                       "kind": "storey",
                       "reference": bool(f.get("reference", False))})
    L0 = levels[0]["id"]
    default_floor = lv_in[0].get("name", "default")

    def lvl(o):
        return lvl_id.get(o.get("floor", default_floor), L0)

    src_walls = [dict(w, p1=list(w["p1"]), p2=list(w["p2"]))
                 for w in src.get("walls", [])]
    src_rooms = list(src.get("rooms", []))
    weld_ops, ends_moved = (weld_endpoints_counted(src_walls) if clean
                            else (0, 0))

    rep = {"src_walls": len(src_walls), "segments": 0, "merged": 0,
           "openings_src": 0, "openings_dropped": 0, "openings_deduped": 0,
           "rooms_traced": 0, "rooms_from_stored_corners": 0, "open_edges": 0,
           "weld_ops": weld_ops, "ends_moved": ends_moved,
           "repaired": [], "concept_rooms": [], "face_conflicts": []}

    vertices, walls, rooms, furnishings = [], [], [], []
    vt_of, wall_recs_of = {}, {}
    # LEVEL-SCOPED BY CONSTRUCTION, as P1.4 established: levels outer, items
    # inner, so one level's geometry can never weld or trace into another's.
    for lv in levels:
        lid = lv["id"]
        lw = [w for w in src_walls if lvl(w) == lid]
        lr = [r for r in src_rooms if lvl(r) == lid]
        loops = [[(float(c[0]), float(c[1])) for c in
                  ((r.get("properties") or {}).get("perimeter_corners") or [])]
                 for r in lr]
        prep, cuts = split_params(lw, [x for x in loops if x])
        vt = VertexTable(lambda: nid("v"))
        vt_of[lid] = vt
        recs, by_pair = [], {}
        for i, w in enumerate(lw):
            a, _b, u, L = prep[i]
            stops = sorted({0.0, L} |
                           {c for c in cuts[i] if MIN_SPAN < c < L - MIN_SPAN})
            ops = sorted(w.get("openings", []),
                         key=lambda o: float(o.get("s", 0.0)))
            rep["openings_src"] += len(ops)
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
                for o in ops:
                    s = float(o.get("s", 0.0))
                    if not (s0 - 1e-6 <= s <= s1 + 1e-6):
                        continue
                    ow, _h = parse_wwhh(o.get("code", "3280"))
                    if ow > seg_len + 1e-6:
                        rep["openings_dropped"] += 1
                        continue
                    loc = s - s0
                    near1 = loc <= seg_len / 2.0
                    off = (loc if near1 else seg_len - loc) - ow / 2.0
                    kind = o.get("kind", "door")
                    rec = {"id": nid("o"), "kind": kind,
                           "code": str(o.get("code", "3280")),
                           "anchor": {"from": "v1" if near1 else "v2",
                                      "offset_in": round(max(0.0, off), 3)}}
                    if kind == "door":
                        dt = o.get("door_type", "")
                        rec["door_type"] = dt
                        m = ({"LH": "v1", "RH": "v2"} if near1
                             else {"LH": "v2", "RH": "v1"})
                        rec["hinge"] = m.get(dt, "none")
                        rec["swings_toward"] = ("left"
                                                if float(o.get("swing", -1)) < 0
                                                else "right")
                    if _sig(rec) in {_sig(x) for x in seg_ops}:
                        rep["openings_deduped"] += 1   # stacked duplicate (#8)
                        continue
                    seg_ops.append(rec)

                key = (*sorted((v1, v2)),)
                if key in by_pair:                     # invariant I4 enforced
                    ex = by_pair[key]
                    rep["merged"] += 1
                    if w.get("type") == "exterior":
                        ex["type"] = "exterior"
                    have = {_sig(x) for x in ex["openings"]}
                    for o in seg_ops:
                        if _sig(o) not in have:
                            have.add(_sig(o))
                            ex["openings"].append(o)
                    continue
                rec = {"id": nid("w"), "level": lid, "v1": v1, "v2": v2,
                       "type": w.get("type", "interior"),
                       "left": None, "right": None, "openings": seg_ops}
                recs.append(rec)
                by_pair[key] = rec
        wall_recs_of[lid] = recs
        walls += recs

    # a Design of just vertices+walls, so face tracing runs through P1.3's ONE
    # implementation (including the P1.3b winding fix) rather than a copy
    for vt in vt_of.values():
        vertices += vt.rows
    graph = Design.from_dict({"format": "floorplanner-design", "version": 5,
                              "units": "inches", "levels": levels,
                              "vertices": vertices, "walls": walls,
                              "rooms": []})

    edge, adj = {}, defaultdict(list)
    for wr in walls:
        edge[(wr["level"], wr["v1"], wr["v2"])] = wr
        edge[(wr["level"], wr["v2"], wr["v1"])] = wr
        adj[(wr["level"], wr["v1"])].append(wr["v2"])
        adj[(wr["level"], wr["v2"])].append(wr["v1"])

    faces_by_level = {}
    if clean:                       # faithful mode traces nothing: every room
        for lv in levels:           # falls through to its stored corners
            lid = lv["id"]
            pos = {v["id"]: (v["x"], v["y"]) for v in vt_of[lid].rows}
            faces_by_level[lid] = [
                (f.area_in2, list(f.vertices), [pos[v] for v in f.vertices])
                for f in trace_faces(graph, lid)]

    rooms += _rooms_from_faces(src_rooms, lvl, faces_by_level, edge,
                               adj, vt_of, nid, rep)
    poly = _bind_sides(rooms, walls, vt_of)
    furnishings += _furnishings(src, lvl, rooms, poly, nid)
    _deferred_concept_rooms(rep, rooms, furnishings, poly, vt_of, src_rooms,
                            lvl)

    used = {(w["level"], v) for w in walls for v in (w["v1"], w["v2"])}
    used |= {(r["level"], e["v"]) for r in rooms for e in r["outline"]}
    vertices = [v for lid, vt in vt_of.items() for v in vt.rows
                if (lid, v["id"]) in used]

    settings = dict(src.get("settings", {}))
    auto = bool(settings.pop("auto_coalesce", True))
    settings.setdefault("vertex_weld_in", WELD_TOL)
    settings.setdefault("join_tol_in", JOIN_TOL)
    settings["area_basis"] = "centerline"      # see the module note
    settings["editing"] = {"shuffle": False, "auto_coalesce": auto,
                           "auto_weld": True, "auto_bind": True}
    if design_name:
        settings["name"] = design_name

    notes = [f"{x['room']}: stored {x['stored_sf']} sf -> traced "
             f"{x['traced_sf']} sf" for x in rep["repaired"]]
    notes += [f"{x['room']}: emitted as a floating concept room ({x['why']})"
              for x in rep["concept_rooms"]]
    if rep["openings_deduped"]:
        notes.append(f"{rep['openings_deduped']} stacked duplicate opening(s) "
                     f"removed")

    doc = canonicalize({
           "format": "floorplanner-design", "version": 5, "units": "inches",
           "settings": settings, "levels": levels, "vertices": vertices,
           "walls": walls, "rooms": rooms, "furnishings": furnishings,
           "groups": [],
           "provenance": {
               "migrated_from": {"format": src.get("format"),
                                 "version": int(src.get("version", 0))},
               "tool": tool,
               "mode": "clean" if clean else "faithful",
               # ends_moved, NOT weld_ops -- the field is "wall ends MOVED"
               "endpoints_welded": ends_moved,
               "openings_deduped": rep["openings_deduped"],
               "notes": notes}})
    return Design.from_dict(doc), rep


def _sig(op):
    return (op["kind"], op["code"], op["anchor"]["from"],
            round(op["anchor"]["offset_in"], 1))


def _rooms_from_faces(src_rooms, lvl, faces_by_level, edge, adj, vt_of,
                      nid, rep):
    """Resolve each source room to the enclosing FACE around its label anchor.

    Faces of a planar subdivision are disjoint, so placed rooms cannot overlap
    -- this is what structurally repairs `planc1.json`'s Hall/M Bath collision.
    Two situations need a policy:

      * no face at all (an open porch) -> keep the stored outline; every edge
        with no wall behind it becomes an OPEN edge, so the room keeps its exact
        shape, area and contents.
      * two rooms resolve to the SAME face (the dividing wall is absent from the
        file -- v4 never serialised open/archway edges) -> the room whose stored
        area matches the face keeps it; the other is DEFERRED to a floating
        concept room. Nothing is invented and nothing is lost."""
    face_claim = {}
    for r in src_rooms:
        level = lvl(r)
        stored = (r.get("properties") or {}).get("perimeter_corners")
        sf = (abs(_area2([(c[0], c[1]) for c in stored])) / 2 / 144
              if stored else 0.0)
        anchor = tuple(r.get("anchor", [0.0, 0.0]))
        for k, (area, _loop, pts) in enumerate(faces_by_level.get(level, [])):
            if not _pip(anchor, pts):
                continue
            score = abs(area / 144 - sf)
            cur = face_claim.get((level, k))
            if cur is None or score < cur[0]:
                if cur is not None:
                    rep["face_conflicts"].append(
                        {"face_sf": round(area / 144, 1),
                         "kept": r.get("name"), "displaced": cur[1]})
                face_claim[(level, k)] = (score, r.get("name"))
            else:
                rep["face_conflicts"].append(
                    {"face_sf": round(area / 144, 1),
                     "kept": cur[1], "displaced": r.get("name")})

    out, deferred = [], []
    for r in src_rooms:
        level = lvl(r)
        vt = vt_of[level]
        props = dict(r.get("properties") or {})
        stored = props.pop("perimeter_corners", None)
        rid = nid("r")
        name = r.get("name", "Room")
        anchor = tuple(r.get("anchor", [0.0, 0.0]))

        loop, best = None, None
        for k, (area, vloop, pts) in enumerate(faces_by_level.get(level, [])):
            if (_pip(anchor, pts)
                    and face_claim.get((level, k), (0, name))[1] == name
                    and (best is None or area < best[0])):
                best = (area, vloop)
        if best is not None:
            area, vloop = best
            n = len(vloop)
            loop = [{"v": u, "wall": edge[(level, u, vloop[(i + 1) % n])]["id"]}
                    for i, u in enumerate(vloop)]
            rep["rooms_traced"] += 1
            traced_sf = abs(_area2([vt.xy(e["v"]) for e in loop])) / 2 / 144
            stored_sf = (abs(_area2([(c[0], c[1]) for c in stored])) / 2 / 144
                         if stored else 0.0)
            if stored and abs(traced_sf - stored_sf) > 5.0:
                rep["repaired"].append({"room": name,
                                        "stored_sf": round(stored_sf, 1),
                                        "traced_sf": round(traced_sf, 1)})
        elif any(_pip(anchor, pts)
                 for _a, _f, pts in faces_by_level.get(level, [])):
            deferred.append((rid, level, props, name, anchor))   # displaced
            continue

        if loop is None:                            # stored-corners fallback
            if not stored or len(stored) < 3:
                continue
            cv = [vt.get((float(c[0]), float(c[1])), level) for c in stored]
            cv = [v for i, v in enumerate(cv) if v != cv[i - 1]]
            loop = []
            for i in range(len(cv)):
                va, vb = cv[i], cv[(i + 1) % len(cv)]
                chain = _walk(va, vb, level, edge, adj, vt)
                if chain is None:
                    loop.append({"v": va, "wall": None})   # OPEN edge
                    rep["open_edges"] += 1
                else:
                    for a_, b_ in chain:
                        loop.append({"v": a_,
                                     "wall": edge[(level, a_, b_)]["id"]})
            rep["rooms_from_stored_corners"] += 1

        if len(loop) < 3:
            continue
        out.append(_room_record(rid, level, name, loop, r, anchor, props, vt))
    rep["deferred"] = deferred
    return out


def _room_record(rid, level, name, loop, src_room, anchor, props, vt):
    pts = [vt.xy(e["v"]) for e in loop]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    lo = src_room.get("label_offset", [0.0, 0.0])
    low = name.lower()
    rec = {
        "id": rid, "level": level, "name": name,
        "category": ("exterior" if any(k in low for k in EXTERIOR_NAMES)
                     else "interior"),
        "outline": loop,
        "placement": {"state": "placed", "rotation": 0.0,
                      "extracted_from": None},
        "label": {"offset": [round(anchor[0] + lo[0] - cx, 3),
                             round(anchor[1] + lo[1] - cy, 3)],
                  "show_dimensions": bool(src_room.get("show_dimensions",
                                                       False)),
                  "show_area": True},
        "properties": props,
    }
    if any(k in low for k in UNCONDITIONED_NAMES):
        rec["area_accounting"] = "unconditioned"
    return rec


def _bind_sides(rooms, walls, vt_of):
    """Derive each wall's left/right from the outlines that name it."""
    poly = {rm["id"]: [vt_of[rm["level"]].xy(e["v"]) for e in rm["outline"]]
            for rm in rooms}
    wmap = {w["id"]: w for w in walls}
    for rm in rooms:
        pts = poly[rm["id"]]
        vt = vt_of[rm["level"]]
        n = len(rm["outline"])
        for i, e in enumerate(rm["outline"]):
            if not e["wall"]:
                continue
            a = vt.xy(e["v"])
            b = vt.xy(rm["outline"][(i + 1) % n]["v"])
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1.0
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            probe = (m[0] + dy / ln * 2.0, m[1] - dx / ln * 2.0)  # (dy,-dx)
            wr = wmap[e["wall"]]
            side = "left" if _pip(probe, pts) else "right"
            if wr["v1"] != e["v"]:
                side = "right" if side == "left" else "left"
            wr[side] = rm["id"]
    return poly


def _furnishings(src, lvl, rooms, poly, nid):
    out = []
    for f in src.get("furnishings", []):
        level = lvl(f)
        p = (float(f["pos"][0]), float(f["pos"][1]))
        owner, best = None, None
        for rm in rooms:
            if rm["level"] != level:
                continue
            pts = poly[rm["id"]]
            if _pip(p, pts):
                a = abs(_area2(pts))
                if best is None or a < best:
                    best, owner = a, rm["id"]
        state = {k: v for k, v in f.items()
                 if k not in ("kind", "pos", "rotation", "floor")}
        rec = {"id": nid("f"), "level": level, "kind": f.get("kind", ""),
               "room": owner, "pos": [p[0], p[1]],
               "rotation": float(f.get("rotation", 0.0))}
        if state:
            rec["state"] = state
        out.append(rec)
    return out


def _deferred_concept_rooms(rep, rooms, furnishings, poly, vt_of, src_rooms,
                            lvl):
    """A room displaced from its face becomes a FLOATING CONCEPT room, sized
    from the furnishings it still owns.

    This is the only thing standing between a two-rooms-one-face file and
    silently losing a room. The furnishings carried are those whose nearest
    SOURCE room anchor was this room -- the author put the names where the
    spaces were, so that is the most faithful available statement of
    ownership."""
    for rid, level, props, name, anchor in rep.pop("deferred", []):
        vt = vt_of[level]
        anchors = [(tuple(o.get("anchor", [0.0, 0.0])), o.get("name"))
                   for o in src_rooms if lvl(o) == level]
        claimed = []
        for f in furnishings:
            if f["level"] != level or not anchors:
                continue
            near = min(anchors, key=lambda t: math.dist(tuple(f["pos"]), t[0]))
            if near[1] == name:
                claimed.append(f)
        if claimed:
            pad = 30.0
            x0 = math.floor((min(f["pos"][0] for f in claimed) - pad) / 6) * 6
            x1 = math.ceil((max(f["pos"][0] for f in claimed) + pad) / 6) * 6
            y0 = math.floor((min(f["pos"][1] for f in claimed) - pad) / 6) * 6
            y1 = math.ceil((max(f["pos"][1] for f in claimed) + pad) / 6) * 6
        else:
            x0, y0 = anchor[0] - 60, anchor[1] - 60
            x1, y1 = anchor[0] + 60, anchor[1] + 60
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        loop = [{"v": vt.get(c, level), "wall": None} for c in corners]
        for f in claimed:
            f["room"] = rid
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rooms.append({
            "id": rid, "level": level, "name": name, "category": "concept",
            "outline": loop,
            "placement": {"state": "floating", "rotation": 0.0,
                          "extracted_from": level},
            "nominal_size": {"width_in": x1 - x0, "depth_in": y1 - y0},
            "label": {"offset": [round(anchor[0] - cx, 3),
                                 round(anchor[1] - cy, 3)],
                      "show_dimensions": True, "show_area": True},
            "properties": props,
        })
        poly[rid] = [vt.xy(e["v"]) for e in loop]
        rep["open_edges"] += 4
        rep["concept_rooms"].append(
            {"room": name, "size_in": [x1 - x0, y1 - y0],
             "furnishings_carried": len(claimed),
             "why": "no enclosure of its own in the wall network "
                    "(the dividing wall is absent from the source file)"})


def conversion_report(rep, src_version=0) -> str:
    """The user-facing sentence of S7a -- not a silent repair.

    Reports `ends_moved`, with `weld_ops` in parentheses as context. Saying "31
    wall ends were welded" would overstate the geometry actually changed by ~6x
    on planc1."""
    bits = [f"Converted from the v{src_version} format."]
    if rep["ends_moved"]:
        bits.append(f"{rep['ends_moved']} wall end"
                    f"{'s' if rep['ends_moved'] != 1 else ''} moved to close "
                    f"gaps the old format could not store "
                    f"({rep['weld_ops']} junctions checked).")
    if rep["repaired"]:
        changed = ", ".join(f"{x['room']} {x['stored_sf']} -> {x['traced_sf']} sf"
                            for x in rep["repaired"])
        bits.append(f"{len(rep['repaired'])} room"
                    f"{'s' if len(rep['repaired']) != 1 else ''} changed size "
                    f"as a result: {changed}.")
    if rep["concept_rooms"]:
        names = ", ".join(x["room"] for x in rep["concept_rooms"])
        bits.append(f"{len(rep['concept_rooms'])} room"
                    f"{'s' if len(rep['concept_rooms']) != 1 else ''} had no "
                    f"enclosure of their own and are now floating: {names}.")
    if rep["openings_deduped"]:
        bits.append(f"{rep['openings_deduped']} duplicate door"
                    f"{'s' if rep['openings_deduped'] != 1 else ''} removed.")
    bits.append("Save to keep these corrections.")
    return " ".join(bits)
