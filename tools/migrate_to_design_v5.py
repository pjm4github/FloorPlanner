#!/usr/bin/env python3
"""Migrate a FloorPlanner v1-v4 plan (`floorplanner-json`) to the v5 design
schema (`floorplanner-design`).

The derivation the editor currently repeats on every edit -- welding endpoints
into corners, splitting walls at junctions, tracing room perimeters -- runs ONCE
here and becomes the stored topology.

Two modes:

  (default)  FAITHFUL. Room outlines come from the stored
             properties.perimeter_corners, warts and all. Use this to prove the
             migration preserves the input, including any corruption.

  --clean    REPAIR. Room outlines are re-derived by tracing the enclosing face
             of the planarised wall graph around each room's label anchor, which
             is the same operation the app performs for "detect room here"
             (workflow C). Faces of a planar graph cannot overlap, so this
             structurally repairs overlapping rooms. Rooms with no enclosing
             face (an open porch, say) fall back to their stored corners, and
             any edge with no wall behind it becomes an OPEN edge -- the room
             keeps its shape either way.

Usage:
  python migrate_to_design_v5.py in.json out.json [--clean] [--name NAME]
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict

WELD_TOL = 0.6      # endpoints closer than this become ONE vertex
ON_SEG_TOL = 1.0    # perpendicular distance to count a point as on a centreline
MIN_SPAN = 1.0

EXTERIOR_NAMES = ("porch", "deck", "patio", "terrace", "lanai")
UNCONDITIONED_NAMES = ("garage", "carport", "shed", "barn")

JOIN_TOL = 9.0      # config.JOIN_TOL -- the app welds endpoints this close at
                    # runtime but never persists the result
END_TOL = 2.0       # endpoint-to-endpoint snap


def weld_endpoints(walls, join_tol=JOIN_TOL, end_tol=END_TOL):
    """Reproduce WallItem.join_endpoints (walls.py:948) as a one-time pass.

    A wall end within `end_tol` of another wall's END snaps onto it; a wall end
    within `join_tol` of another wall's BODY is extended ALONG ITS OWN AXIS to
    meet that wall, forming a real T-junction.  The editor does this on every
    draw/move release and on load, but the welded coordinates are never written
    to the file -- so a divider that stops 1.5" short is saved short, the
    centreline graph stays open, and room detection leaks between two spaces.
    Welding once here closes those gaps permanently.  Returns the weld count."""
    n = 0
    for i, w in enumerate(walls):
        for k, other_k in (("p1", "p2"), ("p2", "p1")):   # noqa: B007 (other_k read below)
            p = tuple(w[k])
            q = tuple(w[other_k])
            best = None
            for j, o in enumerate(walls):
                if i == j or w.get("floor") != o.get("floor"):
                    continue
                for ok in ("p1", "p2"):                       # end -> end
                    d = _d(p, tuple(o[ok]))
                    if 1e-9 < d <= end_tol and (best is None or d < best[0]):
                        best = (d, tuple(o[ok]))
            if best is not None:
                w[k] = list(best[1])
                n += 1
                continue
            for j, o in enumerate(walls):                     # end -> body (T)
                if i == j or w.get("floor") != o.get("floor"):
                    continue
                a, b = tuple(o["p1"]), tuple(o["p2"])
                L = _d(a, b)
                if L < MIN_SPAN:
                    continue
                u = _unit(a, b)
                s, perp = _proj(p, a, u)
                if perp > join_tol or not (MIN_SPAN < s < L - MIN_SPAN):
                    continue
                ip = _line_isect(q, p, a, b)                  # extend along own axis
                if ip is None or _d(ip, p) > join_tol * 2:
                    continue
                sc, _ = _proj(ip, a, u)
                if not (0.0 <= sc <= L):
                    continue
                w[k] = [ip[0], ip[1]]
                n += 1
                break
    return n


def _line_isect(a, b, c, d):
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-9:
        return None
    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den
    return (a[0] + r[0] * t, a[1] + r[1] * t)


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
    code = str(code).strip()
    if not code.isdigit() or len(code) not in (4, 5, 6):
        return (32.0, 80.0)
    k = 2 if len(code) == 4 else 3
    return (float(code[:k]), float(code[k:]))


class Ids:
    def __init__(self):
        self.n = defaultdict(int)

    def next(self, p):
        self.n[p] += 1
        return f"{p}{self.n[p]}"


class VertexTable:
    """Weld-on-insert: a coordinate within tol of an existing vertex on the same
    level RETURNS that vertex.  This is where the 'a corner is one point, not two
    coincident points' invariant is established."""

    def __init__(self, ids, tol=WELD_TOL):
        self.ids, self.tol = ids, tol
        self.pts, self.rows, self.by_id = [], [], {}
        self._bucket = defaultdict(list)

    def _keys(self, p):
        bx, by = int(p[0] // 12), int(p[1] // 12)
        return [(bx + dx, by + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]

    def get(self, p, level):
        for k in self._keys(p):
            for i in self._bucket[k]:
                if self.rows[i]["level"] == level and _d(self.pts[i], p) <= self.tol:
                    return self.rows[i]["id"]
        vid = self.ids.next("v")
        self.pts.append((p[0], p[1]))
        row = {"id": vid, "level": level, "x": round(p[0], 4), "y": round(p[1], 4)}
        self.rows.append(row)
        self.by_id[vid] = (p[0], p[1])
        self._bucket[(int(p[0] // 12), int(p[1] // 12))].append(len(self.pts) - 1)
        return vid

    def xy(self, vid):
        return self.by_id[vid]


# ------------------------------------------------------------------ planarise
def _split_params(walls, rooms):
    prep = [(tuple(w["p1"]), tuple(w["p2"]), _unit(tuple(w["p1"]), tuple(w["p2"])),
             _d(tuple(w["p1"]), tuple(w["p2"]))) for w in walls]
    cuts = [set() for _ in walls]
    for i, (a, _b, u, L) in enumerate(prep):
        if L < MIN_SPAN:
            continue
        for j, (c, d, v, M) in enumerate(prep):
            if i == j or M < MIN_SPAN or walls[i].get("floor") != walls[j].get("floor"):
                continue
            for q in (c, d):                       # T-junction
                s, perp = _proj(q, a, u)
                if perp <= ON_SEG_TOL and MIN_SPAN < s < L - MIN_SPAN:
                    cuts[i].add(s)
            den = u[0] * v[1] - u[1] * v[0]        # proper crossing
            if abs(den) > 1e-6:
                wx, wy = c[0] - a[0], c[1] - a[1]
                t = (wx * v[1] - wy * v[0]) / den
                s2 = (wx * u[1] - wy * u[0]) / den
                if MIN_SPAN < t < L - MIN_SPAN and MIN_SPAN < s2 < M - MIN_SPAN:
                    cuts[i].add(t)
    for r in rooms:                                # every room corner is a vertex
        for c in (r.get("properties", {}) or {}).get("perimeter_corners") or []:
            q = (float(c[0]), float(c[1]))
            for i, (a, _b, u, L) in enumerate(prep):
                if L < MIN_SPAN or walls[i].get("floor") != r.get("floor"):
                    continue
                s, perp = _proj(q, a, u)
                if perp <= ON_SEG_TOL and MIN_SPAN < s < L - MIN_SPAN:
                    cuts[i].add(s)
    return prep, cuts


# ------------------------------------------------------------------ face trace
def trace_faces(adj, pos):
    """Every face of the planar graph, as a list of directed (u, v) edges.
    Faces of a planar subdivision are disjoint by construction -- which is why
    --clean cannot produce overlapping rooms."""
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


def inner_faces(faces, pos):
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
    sign = 1 if sum(1 for a, _, _, s in out if s > 0) * 2 > len(out) else -1
    inner = [(a, f, pts) for a, f, pts, s in out if (s > 0) == (sign > 0)]
    if inner:
        inner.sort(key=lambda t: -t[0])
        inner = inner[1:]                     # drop the outer boundary face
    return inner


# ------------------------------------------------------------------ migration
def migrate(src, clean=False, design_name=None):
    if src.get("format") != "floorplanner-json":
        raise ValueError("not a floorplanner-json document")

    ids = Ids()
    lv_in = src.get("floors") or [{"name": "default", "reference": False}]
    lvl_id, levels = {}, []
    for f in lv_in:
        lid = ids.next("L")
        lvl_id[f.get("name", "default")] = lid
        levels.append({"id": lid, "name": f.get("name", "default"),
                       "elevation_in": 0.0, "height_in": 96.0,
                       "kind": "storey", "reference": bool(f.get("reference", False))})
    L0 = levels[0]["id"]

    def lvl(o):
        return lvl_id.get(o.get("floor", lv_in[0].get("name", "default")), L0)

    src_walls = [dict(w, p1=list(w["p1"]), p2=list(w["p2"]))
                 for w in src.get("walls", [])]
    src_rooms = list(src.get("rooms", []))
    n_weld = weld_endpoints(src_walls) if clean else 0
    prep, cuts = _split_params(src_walls, src_rooms)

    vt = VertexTable(ids)
    walls, by_pair = [], {}
    rep = {"src_walls": len(src_walls), "segments": 0, "merged": 0,
           "openings_src": 0, "openings_dropped": 0,
           "rooms_traced": 0, "rooms_from_stored_corners": 0,
           "open_edges": 0, "endpoints_welded": n_weld, "repaired": []}

    for i, w in enumerate(src_walls):
        a, _b, u, L = prep[i]
        level = lvl(w)
        stops = sorted({0.0, L} | {c for c in cuts[i] if MIN_SPAN < c < L - MIN_SPAN})
        ops = sorted(w.get("openings", []), key=lambda o: float(o.get("s", 0.0)))
        rep["openings_src"] += len(ops)
        for k in range(len(stops) - 1):
            s0, s1 = stops[k], stops[k + 1]
            if s1 - s0 < MIN_SPAN:
                continue
            v1 = vt.get((a[0] + u[0] * s0, a[1] + u[1] * s0), level)
            v2 = vt.get((a[0] + u[0] * s1, a[1] + u[1] * s1), level)
            if v1 == v2:
                continue
            rep["segments"] += 1
            seg_ops, seg_len = [], s1 - s0
            for o in ops:
                s = float(o.get("s", 0.0))
                if not (s0 - 1e-6 <= s <= s1 + 1e-6):
                    continue
                ow, _ = parse_wwhh(o.get("code", "3280"))
                if ow > seg_len + 1e-6:
                    rep["openings_dropped"] += 1
                    continue
                loc = s - s0
                near1 = loc <= seg_len / 2.0
                kind = o.get("kind", "door")
                dt = o.get("door_type", "")
                rec = {"id": ids.next("o"), "kind": kind,
                       "code": str(o.get("code", "3280")),
                       "anchor": {"from": "v1" if near1 else "v2",
                                  "offset_in": round(max(0.0, (loc if near1 else seg_len - loc) - ow / 2.0), 3)}}
                if kind == "door":
                    rec["door_type"] = dt
                    m = {"LH": "v1", "RH": "v2"} if near1 else {"LH": "v2", "RH": "v1"}
                    rec["hinge"] = m.get(dt, "none")
                    rec["swings_toward"] = "left" if float(o.get("swing", -1)) < 0 else "right"
                sig = (rec["kind"], rec["code"], rec["anchor"]["from"],
                       round(rec["anchor"]["offset_in"], 1))
                if sig in {(o["kind"], o["code"], o["anchor"]["from"],
                            round(o["anchor"]["offset_in"], 1)) for o in seg_ops}:
                    rep["openings_deduped"] = rep.get("openings_deduped", 0) + 1
                    continue          # stacked identical opening (coalesce bug #8)
                seg_ops.append(rec)

            key = (level, *sorted((v1, v2)))
            if key in by_pair:                       # invariant I4 enforced here
                ex = by_pair[key]
                rep["merged"] += 1
                if w.get("type") == "exterior":
                    ex["type"] = "exterior"
                have = {(o["kind"], o["code"], o["anchor"]["from"],
                         round(o["anchor"]["offset_in"], 1)) for o in ex["openings"]}
                for o in seg_ops:
                    sig = (o["kind"], o["code"], o["anchor"]["from"],
                           round(o["anchor"]["offset_in"], 1))
                    if sig not in have:
                        have.add(sig)
                        ex["openings"].append(o)
                continue
            rec = {"id": ids.next("w"), "level": level, "v1": v1, "v2": v2,
                   "type": w.get("type", "interior"),
                   "left": None, "right": None, "openings": seg_ops}
            walls.append(rec)
            by_pair[key] = rec

    # ---- graph
    edge = {}
    adj = defaultdict(list)
    for wr in walls:
        edge[(wr["level"], wr["v1"], wr["v2"])] = wr
        edge[(wr["level"], wr["v2"], wr["v1"])] = wr
        adj[(wr["level"], wr["v1"])].append(wr["v2"])
        adj[(wr["level"], wr["v2"])].append(wr["v1"])

    faces_by_level = {}
    if clean:
        for lid in {w["level"] for w in walls}:
            a = {v: nb for (lv, v), nb in adj.items() if lv == lid}
            faces_by_level[lid] = inner_faces(trace_faces(a, vt.by_id), vt.by_id)

    # ---- rooms
    #
    # --clean resolves each room to the enclosing FACE of the planarised wall
    # graph around its label anchor.  Faces are disjoint, so placed rooms cannot
    # overlap.  Two situations need a policy:
    #
    #   * no face at all (an open porch or, here, an unenclosed garage)
    #       -> keep the stored outline; every edge with no wall behind it becomes
    #          an OPEN edge.  The room keeps its exact shape, area and contents.
    #
    #   * two rooms resolve to the SAME face (the wall between them is missing
    #     from the file -- v4 never serialised open/archway edges)
    #       -> the room whose stored area matches the face keeps it; the other is
    #          emitted as a CONCEPT room, floating, sized from the furnishings it
    #          still owns, so nothing is invented and nothing is lost.  The user
    #          re-places it (or draws the missing wall) and rejoins it.
    rooms = []
    face_claim = {}
    if clean:
        for r in src_rooms:
            level = lvl(r)
            stored = (r.get("properties") or {}).get("perimeter_corners")
            sf = abs(_area2([(c[0], c[1]) for c in stored])) / 2 / 144 if stored else 0.0
            anchor = tuple(r.get("anchor", [0.0, 0.0]))
            for k, (area, _f, pts) in enumerate(faces_by_level.get(level, [])):
                if not _pip(anchor, pts):
                    continue
                score = abs(area / 144 - sf)
                cur = face_claim.get((level, k))
                if cur is None or score < cur[0]:
                    if cur is not None:
                        rep.setdefault("face_conflicts", []).append(
                            {"face_sf": round(area / 144, 1),
                             "kept": r.get("name"), "displaced": cur[1]})
                    face_claim[(level, k)] = (score, r.get("name"))
                else:
                    rep.setdefault("face_conflicts", []).append(
                        {"face_sf": round(area / 144, 1),
                         "kept": cur[1], "displaced": r.get("name")})

    deferred = []
    for r in src_rooms:
        level = lvl(r)
        props = dict(r.get("properties") or {})
        stored = props.pop("perimeter_corners", None)
        rid = ids.next("r")
        name = r.get("name", "Room")
        anchor = tuple(r.get("anchor", [0.0, 0.0]))

        loop = None
        if clean:
            best = None
            for k, (area, f, pts) in enumerate(faces_by_level.get(level, [])):
                if _pip(anchor, pts) and face_claim.get((level, k), (0, name))[1] == name:
                    if best is None or area < best[0]:
                        best = (area, f)
            if best is not None:
                area, f = best
                loop = [{"v": u, "wall": edge[(level, u, v)]["id"]} for u, v in f]
                rep["rooms_traced"] += 1
                traced_sf = abs(_area2([vt.xy(e["v"]) for e in loop])) / 2 / 144
                stored_sf = abs(_area2([(c[0], c[1]) for c in stored])) / 2 / 144 if stored else 0.0
                if stored and abs(traced_sf - stored_sf) > 5.0:
                    rep["repaired"].append({"room": name,
                                            "stored_sf": round(stored_sf, 1),
                                            "traced_sf": round(traced_sf, 1)})
            elif any(_pip(anchor, pts) for _a, _f, pts in faces_by_level.get(level, [])):
                deferred.append((rid, r, level, props, name, anchor))   # displaced
                continue

        if loop is None:                                # stored corners fallback
            if not stored or len(stored) < 3:
                continue
            cv = [vt.get((float(c[0]), float(c[1])), level) for c in stored]
            cv = [v for i, v in enumerate(cv) if v != cv[i - 1]]
            loop = []
            for i in range(len(cv)):
                va, vb = cv[i], cv[(i + 1) % len(cv)]
                chain = _walk(va, vb, level, edge, adj, vt)
                if chain is None:
                    loop.append({"v": va, "wall": None})   # OPEN edge, room intact
                    rep["open_edges"] += 1
                else:
                    for a_, b_ in chain:
                        loop.append({"v": a_, "wall": edge[(level, a_, b_)]["id"]})
            rep["rooms_from_stored_corners"] += 1

        if len(loop) < 3:
            continue
        pts = [vt.xy(e["v"]) for e in loop]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        lo = r.get("label_offset", [0.0, 0.0])
        low = name.lower()
        cat = "exterior" if any(k in low for k in EXTERIOR_NAMES) else "interior"
        acc = ("unconditioned"
               if any(k in low for k in UNCONDITIONED_NAMES) else None)

        rooms.append({
            "id": rid, "level": level, "name": name, "category": cat,
            "outline": loop,
            "placement": {"state": "placed", "rotation": 0.0, "extracted_from": None},
            "label": {"offset": [round(anchor[0] + lo[0] - cx, 3),
                                 round(anchor[1] + lo[1] - cy, 3)],
                      "show_dimensions": bool(r.get("show_dimensions", False)),
                      "show_area": True},
            "properties": props,
        })
        if acc:
            rooms[-1]["area_accounting"] = acc
            rep.setdefault("area_accounting_set", []).append({"room": name,
                                                              "as": acc})

    # ---- sides: derived from the outlines, then stored as the maintained index
    poly = {}
    for rm in rooms:
        poly[rm["id"]] = [vt.xy(e["v"]) for e in rm["outline"]]
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
            probe = (m[0] + dy / ln * 2.0, m[1] - dx / ln * 2.0)   # (dy,-dx) = left
            wr = wmap[e["wall"]]
            fwd = (wr["v1"] == e["v"])
            side = ("left" if _pip(probe, pts) else "right")
            if not fwd:
                side = "right" if side == "left" else "left"
            wr[side] = rm["id"]

    # ---- furnishings
    furnishings = []
    for f in src.get("furnishings", []):
        level = lvl(f)
        p = (float(f["pos"][0]), float(f["pos"][1]))
        owner = None
        best = None
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
        rec = {"id": ids.next("f"), "level": level, "kind": f.get("kind", ""),
               "room": owner, "pos": [p[0], p[1]],
               "rotation": float(f.get("rotation", 0.0))}
        if state:
            rec["state"] = state
        furnishings.append(rec)

    # ---- displaced rooms -> floating CONCEPT rooms, sized from what they own
    for rid, _r, level, props, name, anchor in deferred:
        # carry the furnishings whose NEAREST source room label is this room --
        # source anchors are where the author put the names, so this is the most
        # faithful available statement of "which room did this belong to".
        anchors = [(tuple(o.get("anchor", [0.0, 0.0])), o.get("name"))
                   for o in src_rooms if lvl(o) == level]
        claimed = []
        for fr in furnishings:
            if fr["level"] != level:
                continue
            near = min(anchors, key=lambda t: math.dist(tuple(fr["pos"]), t[0]))
            if near[1] == name:
                claimed.append(fr)
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
        for fr in claimed:
            fr["room"] = rid
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rooms.append({
            "id": rid, "level": level, "name": name, "category": "concept",
            "outline": loop,
            "placement": {"state": "floating", "rotation": 0.0,
                          "extracted_from": level},
            "nominal_size": {"width_in": x1 - x0, "depth_in": y1 - y0},
            "label": {"offset": [round(anchor[0] - cx, 3), round(anchor[1] - cy, 3)],
                      "show_dimensions": True, "show_area": True},
            "properties": props,
        })
        rep["open_edges"] += 4
        rep.setdefault("concept_rooms", []).append(
            {"room": name, "size_in": [x1 - x0, y1 - y0],
             "furnishings_carried": len(claimed),
             "why": "no enclosure of its own in the wall network "
                    "(the dividing wall is absent from the source file)"})

    # ---- drop vertices no wall and no outline uses
    used = {v for w in walls for v in (w["v1"], w["v2"])}
    used |= {e["v"] for rm in rooms for e in rm["outline"]}
    vertices = [v for v in vt.rows if v["id"] in used]

    settings = dict(src.get("settings", {}))
    auto = bool(settings.pop("auto_coalesce", True))
    settings.setdefault("vertex_weld_in", WELD_TOL)
    settings.setdefault("join_tol_in", JOIN_TOL)
    settings.setdefault("area_basis", "inside_face")
    settings["editing"] = {"shuffle": False, "auto_coalesce": auto,
                           "auto_weld": True, "auto_bind": True}
    if design_name:
        settings["name"] = design_name

    notes = [f"{x['room']}: stored {x['stored_sf']} sf -> traced {x['traced_sf']} sf"
             for x in rep.get("repaired", [])]
    notes += [f"{x['room']}: emitted as a floating concept room ({x['why']})"
              for x in rep.get("concept_rooms", [])]
    if rep.get("openings_deduped"):
        notes.append(f"{rep['openings_deduped']} stacked duplicate opening(s) removed")

    out = {"format": "floorplanner-design", "version": 5, "units": "inches",
           "settings": settings, "levels": levels, "vertices": vertices,
           "walls": walls, "rooms": rooms, "furnishings": furnishings,
           "groups": [],
           "provenance": {
               "migrated_from": {"format": src.get("format"),
                                 "version": int(src.get("version", 0))},
               "tool": "migrate_to_design_v5.py",
               "mode": "clean" if clean else "faithful",
               "endpoints_welded": n_weld,
               "openings_deduped": rep.get("openings_deduped", 0),
               "notes": notes}}
    return out, rep


def _walk(va, vb, level, edge, adj, vt, max_hops=10):
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


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--clean", action="store_true",
                    help="re-trace room outlines from the wall graph (repairs overlaps)")
    ap.add_argument("--name", default=None)
    a = ap.parse_args()
    doc, rep = migrate(json.load(open(a.src)), clean=a.clean, design_name=a.name)
    json.dump(doc, open(a.dst, "w"), indent=1)
    print(json.dumps(rep, indent=1))
