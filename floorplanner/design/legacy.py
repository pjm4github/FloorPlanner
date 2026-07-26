"""Pre-vertex geometry helpers (P1.3).

`weld_endpoints` operates on RAW wall dicts (`p1`/`p2`/`floor`) -- geometry that
has coordinates but no vertex table yet. That makes it distinct from
`topology.py`, whose ops take/return a vertex-based `Design`; keep them separate,
they are not peers.

NOT purely import-only. Two callers, both pre-vertex:
  * the v1-v4 importer (P2.1), where no `Design` exists yet; and
  * `design_from_scene` (P1.4), because the live scene is still `p1`/`p2`-based
    and needs the same weld-and-planarise pass before it can become a `Design`.
Its lifetime ends at **P3.1**, when the scene becomes vertex-native and the
weld/planarise happens on the vertex table directly. The `topology.py` ops
(`split_edge`, `merge_collinear`, `trace_faces`) are forever.

Ported verbatim from `tools/migrate_to_design_v5.py`. Stdlib only, no Qt.
"""
import math

JOIN_TOL = 9.0      # the app welds endpoints this close at runtime but never
END_TOL = 2.0       # persists it; endpoint-to-endpoint snap
MIN_SPAN = 1.0


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
