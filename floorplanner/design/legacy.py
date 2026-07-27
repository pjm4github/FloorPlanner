"""Pre-vertex geometry helpers (P1.3; `VertexTable`/`split_params` at P1.4).

These operate on RAW wall dicts (`p1`/`p2`) -- geometry that has coordinates but
no vertex table yet. That makes them distinct from `topology.py`, whose ops
take/return a vertex-based `Design`; keep them separate, they are not peers.

NOT purely import-only. Two callers, both pre-vertex:
  * the v1-v4 importer (P2.1), where no `Design` exists yet; and
  * `design_from_scene` (P1.4), because the live scene is still `p1`/`p2`-based
    and needs the same weld-and-planarise pass before it can become a `Design`.
Its lifetime ends at **P3.1**, when the scene becomes vertex-native and the
weld/planarise happens on the vertex table directly. The `topology.py` ops
(`split_edge`, `merge_collinear`, `trace_faces`) are forever.

Three tolerances, three different jobs -- do not conflate them:
  * `JOIN_TOL` / `END_TOL` (9" / 2") are GESTURE tolerances, used only by
    `weld_endpoints`, which REPAIRS geometry by moving wall ends. Repair belongs
    at P2.1's import, once. `design_from_scene` runs it as a CHECK and keeps the
    scene's own coordinates either way -- see `bridge.py`.
  * `WELD_TOL` (0.6") is MODELLING PRECISION: two coordinates this close ARE one
    vertex (schema `settings.vertex_weld_in`, invariant I14). `VertexTable`
    enforces it on insert, which changes representation, not geometry.
  * `ON_SEG_TOL` (1") is how close to a centreline a point must lie to count as
    being on it, for `split_params`.

`VertexTable` and `split_params` are LEVEL-SCOPED BY CONSTRUCTION: neither takes
a level, because each is given one level's geometry and can therefore never see
another's. Callers must not pass mixed-level input. (`weld_endpoints` predates
that convention and still filters on a `floor` key, because P2.1 hands it a whole
legacy file at once.)

Ported verbatim from `tools/migrate_to_design_v5.py`. Stdlib only, no Qt.
"""
import math
from collections import defaultdict

JOIN_TOL = 9.0      # the app welds endpoints this close at runtime but never
END_TOL = 2.0       # persists it; endpoint-to-endpoint snap
MIN_SPAN = 1.0
WELD_TOL = 0.6      # coordinates closer than this ARE one vertex
ON_SEG_TOL = 1.0    # perpendicular distance to count a point as on a centreline


def _d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _unit(a, b):
    L = _d(a, b)
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L) if L > 1e-9 else (1.0, 0.0)


def _proj(p, a, u):
    vx, vy = p[0] - a[0], p[1] - a[1]
    return vx * u[0] + vy * u[1], abs(vy * u[0] - vx * u[1])


def _line_isect(a, b, c, d):
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-9:
        return None
    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den
    return (a[0] + r[0] * t, a[1] + r[1] * t)


def weld_endpoints(walls, join_tol=JOIN_TOL, end_tol=END_TOL):
    """Reproduce WallItem.join_endpoints as a one-time pass over RAW legacy walls
    (dicts with `p1`, `p2`, optional `floor`), mutating them in place.

    A wall end within `end_tol` of another wall's END snaps onto it; a wall end
    within `join_tol` of another wall's BODY is extended ALONG ITS OWN AXIS to
    meet that wall, forming a real T-junction. The editor does this on every
    draw/move release and on load, but the welded coordinates are never written
    to the legacy file -- so a divider that stops 1.5" short is saved short, the
    centreline graph stays open, and room detection leaks between two spaces.
    Welding once here closes those gaps permanently. Returns the weld count."""
    n = 0
    for i, w in enumerate(walls):
        for k, other_k in (("p1", "p2"), ("p2", "p1")):
            p = tuple(w[k])
            q = tuple(w[other_k])
            best = None
            for j, o in enumerate(walls):
                if i == j or w.get("floor") != o.get("floor"):
                    continue
                for ok in ("p1", "p2"):                       # end -> end
                    dist = _d(p, tuple(o[ok]))
                    if 1e-9 < dist <= end_tol and (best is None or dist < best[0]):
                        best = (dist, tuple(o[ok]))
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
                ip = _line_isect(q, p, a, b)                  # extend own axis
                if ip is None or _d(ip, p) > join_tol * 2:
                    continue
                sc, _ = _proj(ip, a, u)
                if not (0.0 <= sc <= L):
                    continue
                w[k] = [ip[0], ip[1]]
                n += 1
                break
    return n


class VertexTable(object):
    """Weld-on-insert coordinate -> vertex-id table for ONE level.

    A coordinate within `tol` (`WELD_TOL`, the modelling precision) of an
    existing entry RETURNS that entry rather than adding a second one. This is
    where the "a corner is one point, not two coincident points" invariant is
    established -- and it is the only welding `design_from_scene` performs,
    because at 0.6" it is a statement about representation, not a change to the
    user's geometry.

    `new_id` is a zero-argument callable returning the next vertex id, so the
    caller keeps one document-wide id sequence (invariant I1).
    """

    def __init__(self, new_id, tol=WELD_TOL):
        self.new_id, self.tol = new_id, tol
        self.pts, self.rows, self.by_id = [], [], {}
        self._bucket = defaultdict(list)

    def _keys(self, p):
        bx, by = int(p[0] // 12), int(p[1] // 12)
        return [(bx + dx, by + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]

    def get(self, p, level):
        """The id of the vertex at `p`, welding onto an existing one within
        `tol`. `level` is stamped onto new rows; it is NOT a filter -- one table
        holds one level, so there is nothing to filter against."""
        for k in self._keys(p):
            for i in self._bucket[k]:
                if _d(self.pts[i], p) <= self.tol:
                    return self.rows[i]["id"]
        vid = self.new_id()
        self.pts.append((p[0], p[1]))
        self.rows.append({"id": vid, "level": level,
                          "x": round(p[0], 4), "y": round(p[1], 4)})
        self.by_id[vid] = (p[0], p[1])
        self._bucket[(int(p[0] // 12), int(p[1] // 12))].append(len(self.pts) - 1)
        return vid

    def xy(self, vid):
        return self.by_id[vid]


def split_params(walls, corner_loops=()):
    """Planarise, pre-vertex: where each wall must be cut so that one emitted
    wall spans exactly one edge of the graph.

    `walls` are RAW dicts (`p1`/`p2`) ON ONE LEVEL; `corner_loops` are that
    level's room perimeters, as sequences of (x, y). Returns `(prep, cuts)`:
    `prep[i]` is `(a, b, u, L)` for wall i, and `cuts[i]` the set of distances
    along it at which to split -- T-junctions, proper crossings, and every room
    corner that lands on its span.

    Room corners are cut sites because P1.4 builds outlines from the scene's own
    corners (never from `trace_faces`): a corner that is not a vertex of the wall
    it sits on leaves an outline edge no wall can span, which invariant I5 then
    reports. This is representation, not repair -- no coordinate moves."""
    prep = [(tuple(w["p1"]), tuple(w["p2"]),
             _unit(tuple(w["p1"]), tuple(w["p2"])),
             _d(tuple(w["p1"]), tuple(w["p2"]))) for w in walls]
    cuts = [set() for _ in walls]
    for i, (a, _b, u, L) in enumerate(prep):
        if L < MIN_SPAN:
            continue
        for j, (c, d, v, M) in enumerate(prep):
            if i == j or M < MIN_SPAN:
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
    for loop in corner_loops:                      # every room corner is a vertex
        for c in loop:
            q = (float(c[0]), float(c[1]))
            for i, (a, _b, u, L) in enumerate(prep):
                if L < MIN_SPAN:
                    continue
                s, perp = _proj(q, a, u)
                if perp <= ON_SEG_TOL and MIN_SPAN < s < L - MIN_SPAN:
                    cuts[i].add(s)
    return prep, cuts
