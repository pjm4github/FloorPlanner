#!/usr/bin/env python3
"""
fp3d.py -- standalone 3D viewer for FloorPlanner v5 design documents.

    python fp3d.py examples/symmetricP1.json
    python fp3d.py plan.json --level L1 --no-furnishings
    python fp3d.py plan.json --edges --xray      # drawn look, see-through walls
    python fp3d.py plan.json --dump              # headless: mesh stats + report
    python fp3d.py plan.json --obj out.obj       # export, no window
    python fp3d.py plan.json --shot view.png     # render offscreen to PNG

Nothing here imports `floorplanner`; it reads the v5 JSON directly, so it can
be run against any saved design and cannot affect the app.  The geometry half
(`build_model` and below) is pure numpy and Qt-free, so it is testable headless
and reusable when this becomes a popup in the app.

Requires: numpy, PyQt6, pyqtgraph, PyOpenGL   (only the last two are new)
    pip install pyqtgraph PyOpenGL

Conventions
-----------
* Plan coordinates are inches, x right / y DOWN (Qt scene).  3D world flips y
  so the plan reads correctly from above: world = (x, -y, z), z up.
* An opening is dimensioned per the v5 schema as an offset from a NAMED end.
* Openings that do not fit their wall are REPORTED, not silently dropped.
* Lighting is baked per face in numpy (key / fill / sky, world-fixed so the sun
  does not swim as you orbit).  No GLSL is compiled, so no driver or pyqtgraph
  version can refuse it; --flat falls back to pyqtgraph's own shader.
* Wall and floor colour come from two tables here, WALL_C by wall type and
  FLOOR_C by room category, because both are typed by the DOCUMENT.
* Furnishings are not: their size, height, elevation, form and material come
  from assets/furnishings/manifest.json + materials.json, read as data.  This
  file states no furnishing dimension of its own.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass, field

import numpy as np

# --------------------------------------------------------------------------
# defaults -- overridden by anything the document actually states
# --------------------------------------------------------------------------

WALL_T = {                       # thickness by type, inches
    "exterior": 6.0, "interior": 4.5, "partition": 3.5,
    "railing": 2.0, "fence": 2.0, "hedge": 12.0, "retaining": 8.0,
}
WALL_H = {                       # height by type; None = full level height
    "exterior": None, "interior": None, "partition": None,
    "railing": 36.0, "fence": 72.0, "hedge": 48.0, "retaining": 24.0,
}
WALL_C = {                       # r, g, b, a
    "exterior": (0.82, 0.79, 0.74, 1.0), "interior": (0.90, 0.88, 0.85, 1.0),
    "partition": (0.93, 0.92, 0.90, 1.0), "railing": (0.62, 0.50, 0.38, 1.0),
    "fence": (0.58, 0.44, 0.30, 1.0), "hedge": (0.33, 0.53, 0.31, 1.0),
    "retaining": (0.58, 0.55, 0.50, 1.0),
}
FLOOR_C = {                      # by room category
    "interior": (0.74, 0.66, 0.56, 1.0), "exterior": (0.70, 0.72, 0.74, 1.0),
    "site": (0.52, 0.70, 0.42, 1.0), "concept": (0.55, 0.60, 0.85, 0.45),
}
FLOATING_C = (0.95, 0.72, 0.28, 1.0)     # a room that is not placed

DEFAULT_SILL = 36.0              # window sill when the document doesn't say
SLAB_T = 1.0                     # floor slab thickness, drawn below z0

# --------------------------------------------------------------------------
# the furnishing catalog -- READ, never restated
# --------------------------------------------------------------------------
# This file used to carry its own table of furnishing footprints, heights and
# material colours.  It was a second definition of data
# `assets/furnishings/manifest.json` already owned, and a measurably wrong one:
# 58 of the 95 catalog kinds were absent from it (drawn 24x24x30 in magenta),
# and of the 37 it shared, 22 disagreed on footprint -- three by transposing
# width and depth, so the item rendered rotated 90 degrees.  The tables are
# gone; the catalog is the source.
#
# THE ISOLATION IS PRESERVED BECAUSE THESE ARE DATA FILES.  Nothing here
# imports `floorplanner` -- the manifest is read as JSON, exactly as the design
# document is, so the viewer still cannot affect the editor and cannot be
# broken by an editor refactor.  The path is resolved by walking UP from this
# module to the directory that holds `assets/`, so it works whether the file is
# run as a script, imported, or executed from another working directory.

# Used only when the catalog cannot be read at all, and reported when it is.
CATALOG_DEFAULT = {"width_in": 24.0, "depth_in": 24.0, "height_in": 30.0,
                   "elevation_in": 0.0, "form": "box", "material": "unknown"}
# Last-resort material if materials.json is missing too.  Loud on purpose.
UNKNOWN_C = (0.85, 0.35, 0.55, 1.00)


def _assets_dir(start=None):
    """The repo's assets/furnishings, found by walking up from this module."""
    here = os.path.abspath(start or __file__)
    d = os.path.dirname(here)
    while True:
        cand = os.path.join(d, "assets", "furnishings")
        if os.path.isdir(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def load_catalog(assets_dir=None):
    """(specs, materials, problems) straight off the generated asset files.

    `specs` is {kind: entry-dict}, `materials` is {name: {colour, roughness,
    metalness}}, and `problems` is a list of strings for the model's report.
    A MISSING CATALOG IS REPORTED, NOT RAISED: the viewer still draws, at the
    default box, and says in its report that it did -- silently guessing every
    size is the failure mode this whole change exists to remove."""
    d = assets_dir or _assets_dir()
    specs, materials, problems = {}, {}, []
    if d is None:
        return specs, materials, [
            "furnishing catalog not found (no assets/furnishings above "
            f"{os.path.dirname(os.path.abspath(__file__))}); every furnishing "
            "drawn at the default box in magenta"]
    for name, sink in (("manifest.json", "specs"),
                       ("materials.json", "materials")):
        path = os.path.join(d, name)
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as e:
            problems.append(
                f"furnishing catalog: cannot read {name} ({e}); "
                + ("every furnishing drawn at the default box"
                   if sink == "specs" else "materials fall back to magenta"))
            continue
        if sink == "specs":
            specs = {e["id"]: e for e in data if "id" in e}
        else:
            materials = dict(data)
    return specs, materials, problems


def _colour(materials, name):
    """(r, g, b, a) for a material name, or None if the catalog lacks it."""
    m = materials.get(name)
    if not isinstance(m, dict):
        return None
    col = m.get("colour")
    if not (isinstance(col, (list, tuple)) and len(col) == 4):
        return None
    return tuple(float(c) for c in col)


# --------------------------------------------------------------------------
# mesh primitives
# --------------------------------------------------------------------------

@dataclass
class Mesh:
    name: str
    verts: np.ndarray                    # (N, 3) float
    faces: np.ndarray                    # (M, 3) int
    color: tuple
    translucent: bool = False


@dataclass
class Model:
    meshes: list = field(default_factory=list)
    notes: list = field(default_factory=list)      # things we could not place
    info: list = field(default_factory=list)       # routine tidying, --verbose
    bbox: tuple = None                             # (min xyz, max xyz)
    stats: dict = field(default_factory=dict)


def _box(corners_xy, z0, z1):
    """Prism over a 4-point plan quad, wound so every normal points OUTWARD.

    The callers build quads in whatever order suits them, so the winding is
    normalised here.  It only matters once the lighting is real: a shader that
    trusts the normal renders an inward-wound face black.
    """
    p = list(corners_xy)
    a2 = sum(p[i][0] * p[(i + 1) % 4][1] - p[(i + 1) % 4][0] * p[i][1]
             for i in range(4))
    if a2 < 0:                                   # make it counter-clockwise
        p = p[::-1]
    v = np.array([(x, y, z0) for x, y in p] + [(x, y, z1) for x, y in p],
                 dtype=float)
    f = [[0, 2, 1], [0, 3, 2],                   # bottom, normal -z
         [4, 5, 6], [4, 6, 7]]                   # top, normal +z
    for i in range(4):                           # sides, normals outward
        j = (i + 1) % 4
        f += [[i, j, j + 4], [i, j + 4, i + 4]]
    return v, np.array(f, dtype=int)


def _merge(parts):
    """Concatenate (verts, faces) pairs into one mesh."""
    vs, fs, off = [], [], 0
    for v, f in parts:
        vs.append(v)
        fs.append(f + off)
        off += len(v)
    if not vs:
        return np.zeros((0, 3)), np.zeros((0, 3), dtype=int)
    return np.vstack(vs), np.vstack(fs)


# --------------------------------------------------------------------------
# polygon triangulation (ear clipping -- keeps this file dependency-free)
# --------------------------------------------------------------------------

def _area2(poly):
    s = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s


def _in_tri(p, a, b, c):
    def sign(u, v, w):
        return (u[0] - w[0]) * (v[1] - w[1]) - (v[0] - w[0]) * (u[1] - w[1])
    d1, d2, d3 = sign(p, a, b), sign(p, b, c), sign(p, c, a)
    neg = (d1 < -1e-12) or (d2 < -1e-12) or (d3 < -1e-12)
    pos = (d1 > 1e-12) or (d2 > 1e-12) or (d3 > 1e-12)
    return not (neg and pos)


def clean_ring(poly, eps=1e-6):
    """Make a ring safe to ear-clip.  Returns (points, [what was removed]).

    Three degeneracies actually occur in saved plans, so all three are handled
    and each is NAMED rather than silently swallowed:
      * repeated points  -- a corner stored twice
      * spikes / slits   -- the outline runs out to a vertex and back along the
                            same line (ring[i-1] == ring[i+1]); zero area, but
                            it stalls ear clipping dead
      * collinear points -- a corner where a wall was split; carries no shape
    """
    pts = [tuple(map(float, p)) for p in poly]
    notes = []

    def dedupe(seq):
        out = []
        for p in seq:
            if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
                out.append(p)
        while (len(out) > 1 and abs(out[0][0] - out[-1][0]) <= eps
               and abs(out[0][1] - out[-1][1]) <= eps):
            out.pop()
        return out

    n0 = len(pts)
    pts = dedupe(pts)
    if len(pts) != n0:
        notes.append(f"{n0 - len(pts)} repeated corner(s)")

    spikes = 0
    changed = True
    while changed and len(pts) > 3:
        changed = False
        m = len(pts)
        for i in range(m):
            a, c = pts[(i - 1) % m], pts[(i + 1) % m]
            if abs(a[0] - c[0]) <= eps and abs(a[1] - c[1]) <= eps:
                j = (i + 1) % m
                for k in sorted((i, j), reverse=True):
                    del pts[k]
                pts = dedupe(pts)
                spikes += 1
                changed = True
                break
    if spikes:
        notes.append(f"{spikes} zero-width spur(s)")

    m = len(pts)
    keep = []
    for i in range(m):
        a, b, c = pts[(i - 1) % m], pts[i], pts[(i + 1) % m]
        cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(cr) > 1e-7:
            keep.append(b)
    if len(keep) >= 3 and len(keep) != m:
        notes.append(f"{m - len(keep)} collinear corner(s)")
        pts = keep

    return pts, notes


def triangulate(poly):
    """Ear-clip a simple polygon.  Returns index triples into `poly`.

    Assumes `poly` has already been through `clean_ring`.  Degenerate input
    yields a partial fan rather than an exception -- the caller checks the
    count and reports the shortfall.
    """
    n = len(poly)
    if n < 3:
        return []
    idx = list(range(n))
    if _area2(poly) < 0:
        idx.reverse()                       # work counter-clockwise
    tris, guard = [], 0
    while len(idx) > 3 and guard < 20000:
        guard += 1
        m, cut = len(idx), False
        best = None
        for k in range(m):
            i0, i1, i2 = idx[(k - 1) % m], idx[k], idx[(k + 1) % m]
            a, b, c = poly[i0], poly[i1], poly[i2]
            cross = ((b[0] - a[0]) * (c[1] - a[1])
                     - (b[1] - a[1]) * (c[0] - a[0]))
            if cross <= 1e-9:               # reflex or collinear -- not an ear
                continue
            if any(_in_tri(poly[j], a, b, c)
                   for j in idx if j not in (i0, i1, i2)):
                if best is None:
                    best = k                # remember a convex fallback
                continue
            tris.append((i0, i1, i2))
            del idx[k]
            cut = True
            break
        if not cut:
            if best is None:
                break                       # nothing convex left: give up
            k = best                        # forced cut, slightly wrong but
            m = len(idx)                    # better than a hole
            tris.append((idx[(k - 1) % m], idx[k], idx[(k + 1) % m]))
            del idx[k]
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


# --------------------------------------------------------------------------
# v5 document -> meshes
# --------------------------------------------------------------------------

def parse_wwhh(code):
    """'3680' -> (36.0, 80.0);  'WWWHH' / 'WWWHHH' for wide openings."""
    code = str(code).strip()
    if not code.isdigit() or len(code) not in (4, 5, 6):
        raise ValueError(f"bad size code {code!r}")
    split = 2 if len(code) == 4 else 3
    return float(code[:split]), float(code[split:])


def opening_span(anchor, width, length):
    """Resolve a v5 anchor to (start, end) along the wall from v1.

    from=v1 : offset is v1 -> the opening's near edge
    from=v2 : offset is v2 -> the opening's near edge
    center  : offset is the wall midpoint -> the opening's centre
    """
    frm = anchor.get("from", "v1")
    off = float(anchor.get("offset_in", 0.0))
    if frm == "v1":
        s0 = off
    elif frm == "v2":
        s0 = length - off - width
    else:                                    # center
        s0 = length / 2.0 + off - width / 2.0
    return s0, s0 + width


def build_model(doc, levels=None, furnishings=True, wall_height=None,
                floors=True, openings=True, catalog=None):
    """v5 design dict -> Model.  Pure numpy; no Qt, no floorplanner import.

    `catalog` is a (specs, materials, problems) triple as `load_catalog()`
    returns; it defaults to the repo's own.  It is a parameter so a test can
    hand in a catalog that is missing, or one naming a form nothing
    implements, without moving files around on disk."""
    model = Model()

    lv = {L["id"]: L for L in doc.get("levels", [])}
    if levels:
        lv = {k: v for k, v in lv.items() if k in levels}
    if not lv:
        model.notes.append("no matching levels in this document")
        return model

    vx = {v["id"]: v for v in doc.get("vertices", [])}
    rooms = doc.get("rooms", [])
    walls = doc.get("walls", [])

    def base(level_id):
        return float(lv[level_id].get("elevation_in", 0.0))

    def top(level_id):
        h = wall_height or lv[level_id].get("height_in", 96.0)
        return base(level_id) + float(h)

    def pt(vid):
        v = vx[vid]
        return (float(v["x"]), -float(v["y"]))      # y flips: plan y is down

    n_wall = n_open = n_floor = n_furn = 0

    # ---- floor slabs -----------------------------------------------------
    if floors:
        by_colour = {}
        for r in rooms:
            if r.get("level") not in lv:
                continue
            ring = [e["v"] for e in r.get("outline", [])]
            if len(ring) < 3:
                model.notes.append(
                    f"room {r.get('name') or r['id']}: outline has "
                    f"{len(ring)} corners -- no floor drawn")
                continue
            label = r.get("name") or r["id"]
            try:
                raw = [pt(v) for v in ring]
            except KeyError as e:
                model.notes.append(f"room {label}: unknown vertex {e}")
                continue
            poly, cleaned = clean_ring(raw)
            # A collinear corner is ROUTINE -- every split wall makes one -- so
            # it is information, not a fault.  A repeated point or a zero-width
            # spur is a real outline degeneracy and gets said out loud.
            routine = [c for c in cleaned if "collinear" in c]
            real = [c for c in cleaned if "collinear" not in c]
            if routine:
                model.info.append(f"room {label}: " + ", ".join(routine))
            if real:
                model.notes.append(
                    f"room {label}: degenerate outline -- " + ", ".join(real)
                    + " (drawn without them)")
            if len(poly) < 3:
                model.notes.append(
                    f"room {label}: outline collapses to {len(poly)} corner(s)"
                    f" -- no floor drawn")
                continue
            tris = triangulate(poly)
            if not tris:
                model.notes.append(
                    f"room {label}: could not triangulate outline "
                    f"({len(poly)} corners)")
                continue
            if len(tris) < len(poly) - 2:
                model.notes.append(
                    f"room {label}: floor is PARTIAL -- {len(tris)} of "
                    f"{len(poly) - 2} triangles; the outline may self-intersect")
            z = base(r["level"])
            placement = r.get("placement") or {}
            floating = placement.get("state") == "floating"
            cat = r.get("category", "interior")
            col = FLOATING_C if floating else FLOOR_C.get(cat, FLOOR_C["interior"])
            key = (col, cat == "concept" or floating)

            v_lo = np.array([(x, y, z - SLAB_T) for x, y in poly])
            v_hi = np.array([(x, y, z) for x, y in poly])
            n = len(poly)
            f = []
            for (i, j, k) in tris:
                f.append([i + n, j + n, k + n])          # top face
                f.append([i, k, j])                      # bottom face
            for i in range(n):                           # edge band
                j = (i + 1) % n
                f += [[i, j, j + n], [i, j + n, i + n]]
            by_colour.setdefault(key, []).append(
                (np.vstack([v_lo, v_hi]), np.array(f, dtype=int)))
            n_floor += 1

        for (col, translucent), parts in by_colour.items():
            v, f = _merge(parts)
            model.meshes.append(Mesh("floors", v, f, col, translucent))

    # ---- walls -----------------------------------------------------------
    by_type = {}
    for w in walls:
        if w.get("level") not in lv:
            continue
        try:
            p1, p2 = pt(w["v1"]), pt(w["v2"])
        except KeyError as e:
            model.notes.append(f"wall {w['id']}: unknown vertex {e}")
            continue
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            model.notes.append(f"wall {w['id']}: zero length -- skipped")
            continue
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux                                  # left normal

        wtype = w.get("type", "interior")
        t = float(w.get("thickness_in") or WALL_T.get(wtype, 4.5))
        z0 = base(w["level"])
        z1 = top(w["level"])
        cap = WALL_H.get(wtype)
        if cap is not None:
            z1 = min(z1, z0 + cap)

        # resolve openings to (start, end, sill, head) along the wall
        cuts = []
        if openings:
            for o in w.get("openings", []):
                try:
                    ow, oh = parse_wwhh(o["code"])
                except (KeyError, ValueError) as e:
                    model.notes.append(f"wall {w['id']} opening "
                                       f"{o.get('id')}: {e}")
                    continue
                s0, s1 = opening_span(o.get("anchor", {}), ow, L)
                if s1 <= 0.01 or s0 >= L - 0.01:
                    model.notes.append(
                        f"wall {w['id']} opening {o.get('id')} ({o.get('kind')}"
                        f" {o.get('code')}): does not fit -- spans "
                        f"{s0:.1f}..{s1:.1f} of a {L:.1f}\" wall; not cut")
                    continue
                if s0 < -0.01 or s1 > L + 0.01:
                    model.notes.append(
                        f"wall {w['id']} opening {o.get('id')}: overhangs the "
                        f"wall ({s0:.1f}..{s1:.1f} of {L:.1f}\"); clamped")
                s0, s1 = max(0.0, s0), min(L, s1)
                sill = float(o.get("sill_in", 0.0 if o.get("kind") != "window"
                                   else DEFAULT_SILL))
                head = float(o.get("head_in", sill + oh))
                cuts.append((s0, s1, sill, min(head, z1 - z0)))
                n_open += 1
        cuts.sort()

        # loop variables bound as defaults (the repo's idiom, cf.
        # extract._span): a closure over a loop variable is a footgun
        # the moment anyone defers the call (B023)
        def quad(a, b, p1=p1, ux=ux, uy=uy, nx=nx, ny=ny, t=t):
            return [(p1[0] + ux * a + nx * t / 2, p1[1] + uy * a + ny * t / 2),
                    (p1[0] + ux * b + nx * t / 2, p1[1] + uy * b + ny * t / 2),
                    (p1[0] + ux * b - nx * t / 2, p1[1] + uy * b - ny * t / 2),
                    (p1[0] + ux * a - nx * t / 2, p1[1] + uy * a - ny * t / 2)]

        parts, cursor = [], 0.0
        for (s0, s1, sill, head) in cuts:
            if s0 - cursor > 1e-6:
                parts.append(_box(quad(cursor, s0), z0, z1))       # solid pier
            if sill > 1e-6:
                parts.append(_box(quad(s0, s1), z0, z0 + sill))    # under sill
            if z0 + head < z1 - 1e-6:
                parts.append(_box(quad(s0, s1), z0 + head, z1))    # header
            cursor = max(cursor, s1)
        if L - cursor > 1e-6:
            parts.append(_box(quad(cursor, L), z0, z1))
        if parts:
            by_type.setdefault(wtype, []).extend(parts)
            n_wall += 1

    for wtype, parts in by_type.items():
        v, f = _merge(parts)
        model.meshes.append(
            Mesh(f"walls:{wtype}", v, f, WALL_C.get(wtype, WALL_C["interior"])))

    # ---- furnishings -----------------------------------------------------
    if furnishings:
        specs, materials, problems = (catalog if catalog is not None
                                      else load_catalog())
        model.notes.extend(problems)
        parts, unknown_kind, unknown_mat = {}, set(), set()
        for fu in doc.get("furnishings", []):
            if fu.get("level") not in lv:
                continue
            pos = fu.get("pos") or [0, 0]
            cx, cy = float(pos[0]), -float(pos[1])
            kind = fu.get("kind", "")
            spec = specs.get(kind)
            if spec is None:
                unknown_kind.add(kind or "?")
                spec = CATALOG_DEFAULT
            fw = float(spec.get("width_in", CATALOG_DEFAULT["width_in"]))
            fd = float(spec.get("depth_in", CATALOG_DEFAULT["depth_in"]))
            fh = float(spec.get("height_in", CATALOG_DEFAULT["height_in"]))
            elev = float(spec.get("elevation_in", 0.0) or 0.0)
            mat = spec.get("material") or "unknown"
            if _colour(materials, mat) is None:
                unknown_mat.add(mat)
                mat = "unknown"
            a = math.radians(-float(fu.get("rotation", 0.0)))
            ca, sa = math.cos(a), math.sin(a)
            corners = []
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                lx, ly = sx * fw / 2, sy * fd / 2
                corners.append((cx + lx * ca - ly * sa, cy + lx * sa + ly * ca))
            # elevation_in is the UNDERSIDE above the level's floor: 0 for
            # anything floor-bearing, non-zero for the wall-hung and
            # counter-mounted items, which used to sit on the floor.
            z = base(fu.get("level")) + elev
            parts.setdefault(mat, []).append(_box(corners, z, z + fh))
            n_furn += 1
        for mat, plist in parts.items():
            v, f = _merge(plist)
            col = _colour(materials, mat) or UNKNOWN_C
            model.meshes.append(Mesh(f"furnishings:{mat}", v, f, col,
                                     translucent=col[3] < 1.0))
        if unknown_kind:
            model.notes.append(
                "furnishing kind(s) in no catalog, drawn at the default box "
                "in magenta: " + ", ".join(sorted(unknown_kind)))
        if unknown_mat:
            model.notes.append(
                "furnishing material(s) not in materials.json, drawn in "
                "magenta: " + ", ".join(sorted(unknown_mat)))

    # ---- bounds ----------------------------------------------------------
    allv = [m.verts for m in model.meshes if len(m.verts)]
    if allv:
        a = np.vstack(allv)
        model.bbox = (a.min(axis=0), a.max(axis=0))
    model.stats = {"levels": list(lv), "walls": n_wall, "openings": n_open,
                   "rooms": n_floor, "furnishings": n_furn,
                   "triangles": int(sum(len(m.faces) for m in model.meshes))}
    return model


def export_obj(model, path):
    """Wavefront OBJ, one group per mesh -- opens in anything."""
    with open(path, "w") as fh:
        fh.write("# FloorPlanner v5 -> OBJ (fp3d.py)\n")
        off = 1
        for m in model.meshes:
            fh.write(f"g {m.name}\n")
            for x, y, z in m.verts:
                fh.write(f"v {x:.4f} {z:.4f} {y:.4f}\n")   # OBJ is y-up
            for a, b, c in m.faces:
                fh.write(f"f {a + off} {b + off} {c + off}\n")
            off += len(m.verts)


# --------------------------------------------------------------------------
# Qt viewer
# --------------------------------------------------------------------------

# Key / fill / sky rig, applied in numpy rather than GLSL.
#
# An earlier version of this file registered a custom shader.  It compiled
# against desktop GLSL and failed hard on stacks that build with "#version 100"
# (GLSL ES), where gl_Normal / gl_Color / ftransform do not exist.  Since the
# rig is deliberately WORLD-fixed -- the sun must not swim while you orbit --
# nothing is lost by baking it into per-face colours, and it now works on every
# driver and every pyqtgraph version, with no shader compilation at all.
_KEY = np.array([0.352, -0.554, 0.755])
_FILL = np.array([-0.701, 0.409, 0.584])


def shade_faces(verts, faces, color):
    """Per-face RGBA for a mesh, lit by the rig above.  (M, 4) float32.

    Relies on `_box` and the floor builder winding every face outward; a face
    wound inward would come out dark, which is why the winding is normalised
    at source rather than papered over with abs() here.
    """
    tri = verts[faces]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1.0
    n = n / ln
    key = np.maximum(n @ _KEY, 0.0)
    fill = np.maximum(n @ _FILL, 0.0)
    sky = 0.5 + 0.5 * n[:, 2]                    # up-facing reads lighter
    lit = np.minimum(0.24 + 0.58 * key + 0.16 * fill + 0.18 * sky, 1.30)
    rgb = np.clip(lit[:, None] * np.asarray(color[:3])[None, :], 0.0, 1.0)
    alpha = color[3] if len(color) > 3 else 1.0
    return np.hstack([rgb, np.full((len(rgb), 1), alpha)]).astype(np.float32)


def make_view(model, edges=False, xray=False, flat=False, parent=None):
    """A GLViewWidget showing `model`, recentred on the origin.

    Recentring (rather than moving the camera target) keeps this working
    across pyqtgraph versions, which disagree about the type of opts['center'].
    """
    import pyqtgraph.opengl as gl

    class _View(gl.GLViewWidget):
        """Adds architectural view presets: T top, F front, S side, I iso."""

        PRESETS = {"t": (90, -90), "f": (0, -90), "s": (0, 0), "i": (28, -60)}

        def keyPressEvent(self, ev):
            k = ev.text().lower()
            if k in self.PRESETS:
                el, az = self.PRESETS[k]
                self.setCameraPosition(elevation=el, azimuth=az)
                ev.accept()
                return
            if k == "r":
                self.setCameraPosition(distance=self._home, elevation=28,
                                       azimuth=-60)
                ev.accept()
                return
            super().keyPressEvent(ev)

    view = _View(parent)
    view.setBackgroundColor((26, 28, 32))

    if model.bbox is not None:
        lo, hi = model.bbox
        ctr = (lo + hi) / 2.0
        span = float(max(hi - lo)) or 100.0
        floor_z = float(lo[2]) - ctr[2] - SLAB_T
    else:
        ctr, span, floor_z = np.zeros(3), 100.0, 0.0

    grid = gl.GLGridItem()
    grid.setSize(span * 1.7, span * 1.7)
    grid.setSpacing(60.0, 60.0)                    # 5 ft
    grid.translate(0, 0, floor_z)
    view.addItem(grid)

    for m in model.meshes:
        if not len(m.faces):
            continue
        col, translucent = m.color, m.translucent
        if xray and m.name.startswith("walls:"):
            col = (col[0], col[1], col[2], 0.30)       # see the plan through it
            translucent = True
        opts = dict(smooth=False, drawEdges=edges, edgeColor=(0, 0, 0, 0.25),
                    glOptions="translucent" if translucent else "opaque")
        if flat:
            # Escape hatch: pyqtgraph's own shader, flat colour.  Floors go
            # dark -- it has one hard-coded light and no sky term -- but it is
            # the configuration that is known to work everywhere.
            view.addItem(gl.GLMeshItem(vertexes=m.verts - ctr, faces=m.faces,
                                       color=col, shader="shaded", **opts))
        else:
            md = gl.MeshData(vertexes=m.verts - ctr, faces=m.faces,
                             faceColors=shade_faces(m.verts, m.faces, col))
            view.addItem(gl.GLMeshItem(meshdata=md, shader=None, **opts))

    view._home = span * 1.4
    view.setCameraPosition(distance=view._home, elevation=28, azimuth=-60)
    return view


def Plan3DWidget(model, edges=False, xray=False, flat=False, parent=None):
    """The reusable piece: view + a one-line status strip, as a QWidget.

    This is what to drop into a QDialog when the app grows a 3D popup:

        from fp3d import build_model, Plan3DWidget
        dlg = QDialog(self); lay = QVBoxLayout(dlg)
        lay.addWidget(Plan3DWidget(build_model(self.snapshot())))
        dlg.resize(1100, 780); dlg.show()
    """
    from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

    w = QWidget(parent)
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(0)
    view = make_view(model, edges=edges, xray=xray, flat=flat)
    lay.addWidget(view, 1)

    s = model.stats
    msg = (f"  {s['rooms']} rooms · {s['walls']} walls · {s['openings']} "
           f"openings · {s['furnishings']} furnishings · "
           f"{s['triangles']:,} triangles")
    if model.notes:
        msg += f"  ·  ⚠ {len(model.notes)} needing attention"
    msg += ("      drag orbit · middle-drag pan · wheel zoom · "
            "T top  F front  S side  I iso  R reset")
    bar = QLabel(msg)
    bar.setStyleSheet("color:#98a0ac; background:#16181c; padding:5px 2px;")
    if model.notes:
        bar.setToolTip("\n".join(model.notes))
    lay.addWidget(bar)
    w.view = view
    return w


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("design", help="a v5 design JSON file")
    ap.add_argument("--level", action="append", default=None,
                    help="level id to show (repeatable); default all")
    ap.add_argument("--list-levels", action="store_true")
    ap.add_argument("--no-furnishings", action="store_true")
    ap.add_argument("--no-floors", action="store_true")
    ap.add_argument("--no-openings", action="store_true",
                    help="draw walls solid, ignoring doors and windows")
    ap.add_argument("--wall-height", type=float, default=None,
                    help='override level height, inches (default: the level\'s)')
    ap.add_argument("--edges", action="store_true",
                    help="draw mesh edges (reads more like a drawing)")
    ap.add_argument("--flat", action="store_true",
                    help="use pyqtgraph's own shader instead of baked lighting")
    ap.add_argument("--xray", action="store_true",
                    help="walls translucent, so the whole plan reads at once")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="also list routine outline tidy-ups")
    ap.add_argument("--dump", action="store_true",
                    help="print stats and the placement report, then exit")
    ap.add_argument("--obj", metavar="PATH", help="write OBJ and exit")
    ap.add_argument("--shot", metavar="PATH", help="render to PNG and exit")
    a = ap.parse_args(argv)

    with open(a.design) as fh:
        doc = json.load(fh)
    if doc.get("format") != "floorplanner-design" or doc.get("version") != 5:
        print(f"warning: {a.design} is not a v5 design document "
              f"(format={doc.get('format')!r} version={doc.get('version')!r})",
              file=sys.stderr)

    if a.list_levels:
        for L in doc.get("levels", []):
            print(f"{L['id']:<6} {L.get('name',''):<16} "
                  f"elev {L.get('elevation_in',0):>8.1f}\"  "
                  f"height {L.get('height_in',96):>6.1f}\"  {L.get('kind','')}")
        return 0

    model = build_model(doc, levels=a.level,
                        furnishings=not a.no_furnishings,
                        floors=not a.no_floors,
                        openings=not a.no_openings,
                        wall_height=a.wall_height)

    s = model.stats
    print(f"{a.design}: levels {','.join(s['levels'])} · {s['rooms']} rooms · "
          f"{s['walls']} walls · {s['openings']} openings · "
          f"{s['furnishings']} furnishings · {s['triangles']:,} triangles")
    if model.bbox is not None:
        lo, hi = model.bbox
        print(f"  extent  {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x "
              f"{hi[2]-lo[2]:.1f} inches")
    if model.notes:
        print(f"  {len(model.notes)} item(s) needed attention:")
        for n in model.notes:
            print(f"    - {n}")
    if model.info:
        if a.verbose:
            print(f"  {len(model.info)} routine outline tidy-up(s):")
            for n in model.info:
                print(f"    - {n}")
        else:
            print(f"  ({len(model.info)} routine outline tidy-ups; "
                  f"-v to list)")

    if a.obj:
        export_obj(model, a.obj)
        print(f"  wrote {a.obj}")
        return 0
    if a.dump:
        return 0

    from PyQt6.QtWidgets import QApplication, QMainWindow
    app = QApplication(sys.argv[:1])
    win = QMainWindow()
    win.setWindowTitle(f"FloorPlanner 3D \u2014 {a.design}")
    body = Plan3DWidget(model, edges=a.edges, xray=a.xray, flat=a.flat)
    win.setCentralWidget(body)
    win.resize(1200, 820)
    win.show()
    if a.shot:
        for _ in range(3):
            app.processEvents()
        body.view.grabFramebuffer().save(a.shot)
        print(f"  wrote {a.shot}")
        return 0
    body.view.setFocus()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
