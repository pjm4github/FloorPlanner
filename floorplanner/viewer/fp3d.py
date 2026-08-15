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
import re
import sys
import xml.etree.ElementTree as ET
from collections import namedtuple
from dataclasses import dataclass, field

import numpy as np

# --------------------------------------------------------------------------
# defaults -- overridden by anything the document actually states
# --------------------------------------------------------------------------

def _load_wall_thickness():
    """The MODEL's thickness table, read rather than copied (D73).

    This file used to carry its own `WALL_T`, and it had drifted: `hedge` was
    12.0 here against 18.0 in the model. Two tables that are synced become two
    tables that disagree, so this one is deleted and the model's is read.

    LOADED BY PATH, NOT IMPORTED, and the reason is measured: `import
    floorplanner.design.validate` pulls in PyQt6, because
    `floorplanner/__init__.py` star-imports the editor -- and this module is
    deliberately Qt-free (numpy only; `--dump`, `--obj` and `--list-levels` run
    headless in CI). `validate.py` itself imports only `json`, `math` and
    `pathlib`, which is what makes loading it standalone safe.

    Falls back to the building types if the model cannot be found, because a
    viewer that cannot draw is worse than one drawing a partition at 3.5.
    """
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.join(os.path.dirname(here), "design", "validate.py")
    try:
        spec = importlib.util.spec_from_file_location("_fp_wall_thickness", cand)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return dict(mod.STD_T)
    except (OSError, AttributeError, ImportError):
        return {"exterior": 6.0, "interior": 4.5, "partition": 3.5}


WALL_T = _load_wall_thickness()  # thickness by type, inches -- the MODEL's
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


# --------------------------------------------------------------------------
# the plan symbol's outline -- what `prism` extrudes
# --------------------------------------------------------------------------
# THE DATA ALREADY EXISTS FOR EVERY ITEM. Each furnishing has a generated SVG
# whose viewBox is in inches and equals its real footprint, so the plan symbol
# IS a measured outline of the thing. `prism` extrudes it instead of guessing a
# rectangle, and needs no new authoring.
#
# ONLY FILLED CLOSED SHAPES COUNT. A stroke has no area and nothing to extrude,
# and a symbol drawn entirely in lines yields nothing -- which is a real answer
# ("this symbol cannot say what shape the object is"), not a failure to parse.
# Measured before this was written: of the 28 items that fall back, 19 carry a
# filled body, 6 carry a body plus line-art structure, and 3 carry no body at
# all (handoff 0012).

SVG_NS = "{http://www.w3.org/2000/svg}"
_NUM_RE = re.compile(r"-?\d*\.?\d+(?:[eE]-?\d+)?")
_CMD_RE = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)")
_CURVE_STEP = {"C": 6, "S": 4, "Q": 4, "A": 7}


def _nums(s):
    return [float(v) for v in _NUM_RE.findall(s or "")]


def _ring_area(pts):
    """Twice-signed area / 2 -- magnitude only; winding is normalised later."""
    if len(pts) < 3:
        return 0.0
    a = 0.0
    for i, (x0, y0) in enumerate(pts):
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


def _pip(pt, poly):
    """Point in polygon, ray cast. Used only to drop shapes NESTED inside
    another -- a cushion line inside a sofa body, a deck circle inside a mower
    -- which would otherwise extrude to exactly the same height and z-fight
    with the face they sit on."""
    x, y = pt
    inside = False
    for i, (x0, y0) in enumerate(poly):
        x1, y1 = poly[(i + 1) % len(poly)]
        if (y0 > y) != (y1 > y):
            t = (y - y0) / (y1 - y0)
            if x < x0 + t * (x1 - x0):
                inside = not inside
    return inside


def _path_rings(d):
    """Closed subpaths of a path's `d`, as anchor-point rings.

    ANCHOR POINTS ONLY -- a curve contributes its endpoint, not its control
    points, so a rounded outline is extruded as its inscribed polygon. That is
    a deliberate under-approximation: the solid is never larger than the symbol
    drawn, which is the safe direction for something standing in a room.

    A subpath that never closes is a stroke and is dropped."""
    rings, cur, pos, start = [], [], (0.0, 0.0), (0.0, 0.0)
    for cmd, args in _CMD_RE.findall(d or ""):
        n, rel, up = _nums(args), cmd.islower(), cmd.upper()
        if up == "Z":
            if len(cur) >= 3:
                rings.append(cur)
            cur, pos = [], start
        elif up == "M":
            for i in range(0, len(n) - 1, 2):
                p = ((pos[0] + n[i], pos[1] + n[i + 1]) if rel
                     else (n[i], n[i + 1]))
                if i == 0:
                    if len(cur) >= 3:
                        rings.append(cur)
                    cur, start = [p], p
                else:
                    cur.append(p)
                pos = p
        elif up in ("L", "T"):
            for i in range(0, len(n) - 1, 2):
                pos = ((pos[0] + n[i], pos[1] + n[i + 1]) if rel
                       else (n[i], n[i + 1]))
                cur.append(pos)
        elif up == "H":
            for v in n:
                pos = (pos[0] + v if rel else v, pos[1])
                cur.append(pos)
        elif up == "V":
            for v in n:
                pos = (pos[0], pos[1] + v if rel else v)
                cur.append(pos)
        elif up in _CURVE_STEP:
            step = _CURVE_STEP[up]
            for i in range(0, len(n) - step + 1, step):
                ex, ey = n[i + step - 2], n[i + step - 1]
                pos = (pos[0] + ex, pos[1] + ey) if rel else (ex, ey)
                cur.append(pos)
    if len(cur) >= 3:
        rings.append(cur)
    return rings


def _is_filled(el):
    fill = (el.get("fill") or "").strip().lower()
    style = (el.get("style") or "").replace(" ", "").lower()
    return not (fill == "none" or "fill:none" in style)


def _ellipse_ring(cx, cy, rx, ry, n=24):
    return [(cx + rx * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


#: One extrudable piece of a symbol.
#:
#: `h` is the piece's TOP HEIGHT IN INCHES above the item's base, read from a
#: `data-h` attribute on the element, or `None` when it carries none.
#:
#: THE ANNOTATION CARRIES A HEIGHT AND NOTHING ELSE, and that boundary is the
#: ruling (2026-08-14): **the region's POSITION comes from the artwork; only its
#: HEIGHT is annotated.** The moment `data-h` could also say *where*, there are
#: two sources of truth about where a pillow is and they will disagree. Same
#: discipline as the thickness table (D73): one normative source per fact.
Part = namedtuple("Part", "ring h nested")


def svg_outlines(path):
    """(parts, (vw, vh)) for one furnishing symbol, in viewBox units.

    `parts` are the FILLED CLOSED shapes, largest first, each with the height
    its element annotates (or `None`). Empty when the symbol is line art -- the
    caller falls back to a box and says so.

    A ring NESTED inside a larger one is marked rather than dropped: with a
    height it is a region (a tub's well, a bed's pillow), and without one it is
    decoration that would z-fight the face it sits on, so the extruder skips
    it. Before regions existed this function dropped them here.

    A `transform` on any element makes the file UNUSABLE here rather than
    silently mis-placed: this reader does not apply transforms, and a shape
    extruded at the wrong place is worse than a box at the right one. No
    generated symbol carries one (measured, handoff 0012); if one ever does,
    the item falls back and the report names it.
    """
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return [], (0.0, 0.0)
    vb = _nums(root.get("viewBox") or "")
    if len(vb) < 4 or vb[2] <= 0 or vb[3] <= 0:
        return [], (0.0, 0.0)
    found = []                                   # (ring, annotated height)
    for el in root.iter():
        if el.get("transform"):
            return [], (vb[2], vb[3])
        tag = el.tag.replace(SVG_NS, "")
        if tag in ("svg", "g", "defs", "title", "desc") or not _is_filled(el):
            continue
        try:
            ah = float(el.get("data-h")) if el.get("data-h") else None
        except ValueError:
            ah = None                            # a bad height is no height
        if tag == "rect":
            x, y = float(el.get("x", 0)), float(el.get("y", 0))
            w, h = float(el.get("width", 0)), float(el.get("height", 0))
            if w > 0 and h > 0:
                found.append(([(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
                              ah))
        elif tag in ("circle", "ellipse"):
            rx = float(el.get("rx", el.get("r", 0)))
            ry = float(el.get("ry", el.get("r", 0)))
            if rx > 0 and ry > 0:
                found.append((_ellipse_ring(float(el.get("cx", 0)),
                                            float(el.get("cy", 0)), rx, ry), ah))
        elif tag in ("polygon", "polyline"):
            p = _nums(el.get("points", ""))
            if len(p) >= 6:
                found.append((list(zip(p[0::2], p[1::2], strict=False)), ah))
        elif tag == "path":
            for r in _path_rings(el.get("d", "")):
                found.append((r, ah))
    found = [(r, h) for r, h in found if _ring_area(r) > 1e-9]
    found.sort(key=lambda rh: _ring_area(rh[0]), reverse=True)
    parts, outer = [], []
    for ring, ah in found:
        c = (sum(p[0] for p in ring) / len(ring),
             sum(p[1] for p in ring) / len(ring))
        nested = any(_pip(c, o) for o in outer)
        if not nested:
            outer.append(ring)
        parts.append(Part(ring, ah, nested))
    return parts, (vb[2], vb[3])


def _ear_clip(ring):
    """Triangulate a simple polygon by ear clipping -> [(i, j, k), ...].

    Rings here are tens of points at most (a rect is 4, an ellipse 24), so the
    O(n^2) shape costs nothing and avoids a dependency. Returns [] rather than
    raising on a ring it cannot clip -- a furnishing that will not triangulate
    falls back to a box and is reported, which is this file's rule for
    everything it cannot draw."""
    n = len(ring)
    if n < 3:
        return []
    idx = list(range(n))
    if sum(ring[i][0] * ring[(i + 1) % n][1] - ring[(i + 1) % n][0] * ring[i][1]
           for i in range(n)) < 0:
        idx.reverse()                                # work counter-clockwise

    def cross(o, a, b):
        return ((ring[a][0] - ring[o][0]) * (ring[b][1] - ring[o][1])
                - (ring[a][1] - ring[o][1]) * (ring[b][0] - ring[o][0]))

    tris, guard = [], 0
    while len(idx) > 3 and guard < 4 * n:
        guard += 1
        for k in range(len(idx)):
            prev, cur, nxt = (idx[k - 1], idx[k], idx[(k + 1) % len(idx)])
            if cross(prev, cur, nxt) <= 0:           # reflex
                continue
            others = [i for i in idx if i not in (prev, cur, nxt)]
            if any(_pip(ring[i], [ring[prev], ring[cur], ring[nxt]])
                   for i in others):
                continue
            tris.append((prev, cur, nxt))
            idx.pop(k)
            guard = 0
            break
        else:
            return []                                # not a simple polygon
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


def _segments_cross(a, b, c, d):
    """Do open segments ab and cd properly cross? Shared endpoints do not."""
    def side(p, q, r):
        return ((q[0] - p[0]) * (r[1] - p[1])
                - (q[1] - p[1]) * (r[0] - p[0]))
    if (a == c or a == d or b == c or b == d):
        return False
    d1, d2 = side(a, b, c), side(a, b, d)
    d3, d4 = side(c, d, a), side(c, d, b)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def _bridge_holes(outer, holes):
    """Splice each hole into `outer` with a two-way bridge -> one ring.

    THE STANDARD TRICK, and the reason it is here: a cap with a hole in it
    cannot be ear-clipped, but a cap whose boundary walks IN along a bridge,
    round the hole and back OUT along the same bridge can be -- the two bridge
    edges are coincident and enclose no area, so they vanish visually while
    making the polygon simply-connected.

    Bridges are chosen as the shortest outer-vertex/hole-vertex pair whose
    segment crosses no edge already in play. Returns `None` if any hole cannot
    be bridged, and the CALLER FALLS BACK TO A SOLID BODY AND REPORTS -- a
    wrong hole is worse than a missing one, and a silent wrong hole is worst.
    """
    ring = list(outer)
    for hole in sorted(holes, key=_ring_area, reverse=True):
        edges = ([(ring[i], ring[(i + 1) % len(ring)])
                  for i in range(len(ring))]
                 + [(hole[i], hole[(i + 1) % len(hole)])
                    for i in range(len(hole))])
        best = None
        for i, o in enumerate(ring):
            for j, hpt in enumerate(hole):
                d2 = (o[0] - hpt[0]) ** 2 + (o[1] - hpt[1]) ** 2
                if best is not None and d2 >= best[0]:
                    continue
                if any(_segments_cross(o, hpt, e0, e1) for e0, e1 in edges):
                    continue
                best = (d2, i, j)
        if best is None:
            return None
        _, i, j = best
        # ...out along the bridge, round the hole the OTHER way, back in
        loop = hole[j:] + hole[:j + 1]
        loop.reverse()
        ring = ring[:i + 1] + loop + ring[i:]
    return ring


def _cap(ring, holes, z, up):
    """A horizontal face over `ring` minus `holes`, or None if it cannot be
    triangulated."""
    poly = ring if not holes else _bridge_holes(ring, holes)
    if poly is None:
        return None
    tris = _ear_clip(poly)
    if not tris:
        return None
    v = np.array([(x, y, z) for x, y in poly], dtype=float)
    f = [[a, b, c] if up else [a, c, b] for a, b, c in tris]
    return v, np.array(f, dtype=int)


def _wall(ring, z0, z1, outward):
    """The vertical band swept by a ring between two heights."""
    n = len(ring)
    ccw = sum(ring[i][0] * ring[(i + 1) % n][1]
              - ring[(i + 1) % n][0] * ring[i][1] for i in range(n)) > 0
    v = np.array([(x, y, z0) for x, y in ring] + [(x, y, z1) for x, y in ring],
                 dtype=float)
    f = []
    for i in range(n):
        j = (i + 1) % n
        if ccw == outward:
            f += [[i, j, j + n], [i, j + n, i + n]]
        else:
            f += [[i, j + n, j], [i, i + n, j + n]]
    return v, np.array(f, dtype=int)


def _extrude(ring_world, z0, z1):
    """One closed ring -> a solid prism between two heights."""
    tris = _ear_clip(ring_world)
    if not tris:
        return None
    n = len(ring_world)
    v = np.array([(x, y, z0) for x, y in ring_world]
                 + [(x, y, z1) for x, y in ring_world], dtype=float)
    f = [[a, c, b] for a, b, c in tris]              # bottom, normal -z
    f += [[a + n, b + n, c + n] for a, b, c in tris]  # top, normal +z
    ccw = sum(ring_world[i][0] * ring_world[(i + 1) % n][1]
              - ring_world[(i + 1) % n][0] * ring_world[i][1]
              for i in range(n)) > 0
    for i in range(n):
        j = (i + 1) % n
        f += ([[i, j, j + n], [i, j + n, i + n]] if ccw
              else [[i, j + n, j], [i, i + n, j + n]])
    return v, np.array(f, dtype=int)


def load_outline(kind, specs, assets_dir=None, _cache=None):
    """`svg_outlines()` for a catalog kind, memoised per run.

    A plan can hold forty of the same chair; parsing its symbol forty times
    would be forty identical XML parses on the model-build path."""
    if _cache is None:
        _cache = _OUTLINE_CACHE
    if kind in _cache:
        return _cache[kind]
    spec = specs.get(kind) or {}
    d = assets_dir or _assets_dir()
    out = ([], (0.0, 0.0))
    if d and spec.get("file"):
        out = svg_outlines(os.path.join(d, spec["file"]))
    _cache[kind] = out
    return out


_OUTLINE_CACHE = {}


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


# --------------------------------------------------------------------------
# furnishing solids -- one generator per `form` in the catalog
# --------------------------------------------------------------------------
# The catalog names a form per item; this is where a name becomes geometry.
# FIRST PASS: `box` and `slab` are built.  The rest are RECOGNISED but not yet
# implemented, and an item using one is built as a box and SAID SO in the
# report -- a known gap that announces itself is a different thing from a
# silent guess, which is what the deleted FURN table was.
#
# `prism` -- extruding the symbol's true SVG outline -- IS NOW BUILT, and it is
# also THE FALLBACK: a form whose own generator does not exist yet is drawn from
# its plan symbol rather than as a rectangle. See PRISM IS THE FALLBACK below.
KNOWN_FORMS = ("box", "slab", "seat", "bed", "basin", "enclosure", "vessel",
               "vehicle", "planting", "prism")
BUILT_FORMS = ("box", "slab", "prism")


def _plan_quad(place, x0, x1, y0, y1):
    """The four world corners of a local axis-aligned rectangle."""
    return [place(x0, y0), place(x1, y0), place(x1, y1), place(x0, y1)]


def build_prism(place, w, d, h, z0, outline, form="prism"):
    """The plan symbol, extruded. `outline` is `svg_outlines()`'s return.

    `form` is the item's CATALOG form (`"vessel"`, `"enclosure"`, ...), not the
    generic `"prism"` dispatch tag `build_model` reassigns once it decides to
    fall back here -- the caller must pass the real one through, or this
    cannot tell a tub from a shower stall. Defaults to `"prism"`, which is
    deliberately not `"enclosure"`: an item whose catalog form literally is
    `prism` was never a room, so it keeps the general (vessel-shaped) rule
    below rather than needing a special case of its own.

    THE MAPPING, and the y flip in it is not cosmetic. A symbol point `(sx, sy)`
    sits at `(px - W/2 + sx, py - H/2 + sy)` in the EDITOR's scene, where y
    grows downward; this viewer's world has y growing the other way (`cy` is
    `-pos[1]`). So local y is `H/2 - sy`, not `sy - H/2`. Get it wrong and every
    asymmetric item renders mirrored -- which is exactly the class of fault the
    deleted furniture table shipped for months (three kinds rotated 90 degrees
    because width and depth were transposed).

    Scaled by `w/W`, `d/H` rather than assumed equal, so an item whose document
    size differs from its symbol's viewBox still comes out the right size.

    RETURNS (body_parts, region_parts) -- TWO LISTS, NOT ONE (handoff 0018
    SS6: "materials attach to PARTS, not to ITEMS"). `region_parts` is the
    well or the raised region -- a vessel's water, an enclosure's bench or
    stove -- which the caller may colour differently from the body. A
    "beside" part (a chair back beside its seat, not covered by this
    ruling's table) stays grouped with the body, so every item this ruling
    does not touch keeps today's one-material behaviour unchanged. Both
    lists are `[]` when nothing could be extruded, which the caller reports.
    """
    shapes, (vw, vh) = outline
    if not shapes or vw <= 0 or vh <= 0:
        return [], []
    sx, sy = w / vw, d / vh

    def to_world(ring):
        return [place((x - vw / 2.0) * sx, (vh / 2.0 - y) * sy)
                for x, y in ring]

    # THE BODY may state its own height. A sofa's catalog `height_in` is 32 --
    # the BACK -- so a body that used it extruded the whole seat to back height
    # and read as a slab. `height_in` stays the item's OVERALL height, which is
    # what the box fallback needs; the body says how far IT rises.
    body = shapes[0]
    body_h = body.h if body.h is not None else h

    # A VESSEL'S INTERNAL REGION IS A RECESS; AN ENCLOSURE'S IS A SOLID
    # STANDING ON THE FLOOR (handoff 0018 SS4) -- and "ON THE FLOOR" IS THE
    # PART THAT CHANGES THE EXTRUSION, NOT JUST THE CLASSIFICATION.
    #
    # "on_body" (a pillow on a mattress, a back on a seat) sits ON TOP of the
    # body: it extrudes from body_h up to its own height, and that formula
    # ONLY makes sense when body_h is the item's own surface -- furniture,
    # where the region genuinely rests on something.
    #
    # An enclosure's body_h is the WALL height, not a surface anything rests
    # on, so a bench or a stove must extrude from THE FLOOR (z0) to its own
    # height -- THE SAME FORMULA "beside" already uses. The first cut of this
    # fix reused the on_body formula for enclosures too and built walk_in_
    # shower's bench spanning 18in TO 78in -- a column hanging near the
    # ceiling -- instead of 0 to 18in standing on the floor. Caught by
    # dumping the mesh's own bounding box, not by the roof-over signal, which
    # only ever asked about the CAP and had nothing to say about where the
    # bench itself ended up.
    #
    # NOT A HEIGHT THRESHOLD: the split is categorical, on the catalog's own
    # form, not on body_h -- a threshold here would repeat the
    # lawnmower/snowblower mistake (0012-ruling.md) one level up.
    is_enclosure = form == "enclosure"
    wells, on_body, grounded, beside = [], [], [], []
    for p in shapes[1:]:
        if not p.nested:
            beside.append(p)
        elif p.h is None:
            continue                 # decoration: it would z-fight the face
        elif is_enclosure:
            grounded.append(p)       # a bench, a stove -- stands on the floor
        elif p.h < body_h:
            wells.append(p)          # a tub's well, a sink's bowl
        else:
            on_body.append(p)        # a pillow, a headrest -- sits ON the body

    body_parts, region_parts = [], []
    well_rings = [to_world(p.ring) for p in wells]
    body_ring = to_world(body.ring)

    if well_rings:
        top = _cap(body_ring, well_rings, z0 + body_h, up=True)
        if top is None:
            # A hole that will not bridge falls back to a SOLID body rather
            # than to a wrong one, and the caller reports it.
            body_parts.append(_extrude(body_ring, z0, z0 + body_h))
            well_rings = []
        else:
            body_parts.append(top)
            body_parts.append(_cap(body_ring, [], z0, up=False))
            body_parts.append(_wall(body_ring, z0, z0 + body_h, outward=True))
            for p, wr in zip(wells, well_rings, strict=True):
                region_parts.append(_wall(wr, z0 + p.h, z0 + body_h,
                                          outward=False))
                region_parts.append(_cap(wr, [], z0 + p.h, up=True))
    else:
        body_parts.append(_extrude(body_ring, z0, z0 + body_h))

    for p in on_body:                 # sits ON the body -- a region
        region_parts.append(_extrude(to_world(p.ring), z0 + body_h, z0 + p.h))
    for p in grounded:                 # stands on the FLOOR -- also a region
        region_parts.append(_extrude(to_world(p.ring), z0, z0 + p.h))
    for p in beside:                 # its own column, from the floor -- BODY
        top = z0 + (p.h if p.h is not None else h)
        body_parts.append(_extrude(to_world(p.ring), z0, top))

    return ([o for o in body_parts if o is not None],
            [o for o in region_parts if o is not None])


def build_solid(form, place, w, d, h, z0, outline=None):
    """[(verts, faces), ...] for one furnishing, in its own local frame.

    `place(lx, ly) -> (x, y)` carries rotation and position, so a generator
    only has to think in the item's own axes.  `z0` is the UNDERSIDE (the
    level's floor plus the catalog's elevation_in), so a wall-hung item is
    built exactly like a floor-standing one, higher up.

    `outline` is the item's plan symbol when one could be read; `prism` needs
    it and every other generator ignores it.

    THIS FUNCTION'S CONTRACT STAYS A SINGLE FLAT LIST -- `build_prism`'s own
    body/region split (0018 SS6) is flattened back together here, because
    `build_solid` has no `region_material` parameter to route a second list
    to. Only `build_model`'s direct call to `build_prism` uses the split;
    every other caller of THIS function keeps one material per item, exactly
    as before."""
    z1 = z0 + h
    if form == "prism":
        body, region = build_prism(place, w, d, h, z0,
                                   outline or ([], (0.0, 0.0)))
        parts = body + region
        if parts:
            return parts
        # falls through to the box -- the CALLER reports it, because only the
        # caller knows which kind this was
    if form == "slab":
        # A top on legs: table, desk, workbench, machine table.  The top is a
        # real thickness rather than a plane, because a zero-thickness top
        # z-fights and casts no shadow under the Qt Quick 3D path.
        t = min(2.0, max(0.75, h * 0.08))
        leg = min(3.0, w / 8.0, d / 8.0)
        parts = [_box(_plan_quad(place, -w / 2, w / 2, -d / 2, d / 2),
                      z1 - t, z1)]
        if leg > 0.1 and z1 - t > z0 + 1e-6:
            for sx in (-1, 1):
                for sy in (-1, 1):
                    x0 = sx * (w / 2 - leg) if sx > 0 else sx * w / 2
                    x1 = sx * w / 2 if sx > 0 else sx * (w / 2 - leg)
                    y0 = sy * (d / 2 - leg) if sy > 0 else sy * d / 2
                    y1 = sy * d / 2 if sy > 0 else sy * (d / 2 - leg)
                    parts.append(_box(_plan_quad(place, x0, x1, y0, y1),
                                      z0, z1 - t))
        return parts
    # box, and every form whose own generator is still to come
    return [_box(_plan_quad(place, -w / 2, w / 2, -d / 2, d / 2), z0, z1)]


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
    by_prism, still_box = set(), set()      # which kinds got which solid

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
        parts = {}
        unknown_kind, unknown_mat, unknown_form, pending_form = (
            set(), set(), set(), set())
        outline_dir = _assets_dir()
        _OUTLINE_CACHE.clear()      # per build, so a test can swap the catalog
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
            form = spec.get("form") or "box"
            # PRESERVED BEFORE `form` GETS OVERWRITTEN TO THE GENERIC "prism"
            # DISPATCH TAG BELOW -- `build_prism` needs the real catalog form
            # ("vessel" vs "enclosure") to decide whether an internal region
            # may recess (handoff 0018 SS4), and by the time `form == "prism"`
            # is checked further down, this is the only place that still knows.
            catalog_form = form
            outline = None
            if form not in KNOWN_FORMS:
                # A form nothing recognises is a catalog the viewer cannot
                # read, so it is loud, exactly like an unknown kind.
                unknown_form.add(form)
                form, mat = "box", "unknown"
            elif form not in BUILT_FORMS:
                # PRISM IS THE FALLBACK, in place of the box (handoff 0012's
                # ruling). A form whose own generator is not written yet is
                # drawn from the item's PLAN SYMBOL -- data that already exists
                # for every item, at its true footprint -- rather than as a
                # rectangle that is merely the right size.
                #
                # The box is still there behind it, for a symbol drawn entirely
                # in strokes: those have no outline to extrude, and a prism
                # would have to invent one. Which items land where is REPORTED,
                # because "a third of the catalog renders as a box" is a claim
                # that has to stay checkable.
                pending_form.add(form)
                outline = load_outline(kind, specs, outline_dir)
                if outline[0]:
                    form = "prism"
                else:
                    still_box.add(kind)
            if _colour(materials, mat) is None:
                unknown_mat.add(mat)
                mat = "unknown"
            a = math.radians(-float(fu.get("rotation", 0.0)))
            ca, sa = math.cos(a), math.sin(a)

            def place(lx, ly, cx=cx, cy=cy, ca=ca, sa=sa):
                # loop variables bound as defaults (B023, the repo's idiom)
                return (cx + lx * ca - ly * sa, cy + lx * sa + ly * ca)

            # elevation_in is the UNDERSIDE above the level's floor: 0 for
            # anything floor-bearing, non-zero for the wall-hung and
            # counter-mounted items, which used to sit on the floor.
            z = base(fu.get("level")) + elev
            if form == "prism" and outline is None:      # an explicit `prism`
                outline = load_outline(kind, specs, outline_dir)
            # THE PRISM IS ATTEMPTED HERE RATHER THAN INSIDE `build_solid`, so
            # the bookkeeping can never claim a prism that is really a box.
            # `build_solid` falls back silently by design (it does not know the
            # kind, so it cannot name it), which means its return is non-empty
            # either way and tells the caller nothing.
            # BODY and REGION may carry DIFFERENT materials (0018 SS6): a
            # vessel's region is its declared contents (water, translucent);
            # an enclosure's is a solid standing on the floor (a bench, a
            # stove). Falls back to the body's own material when the catalog
            # states none, which is every item this ruling does not touch.
            region_mat = spec.get("region_material") or mat
            if _colour(materials, region_mat) is None:
                unknown_mat.add(region_mat)
                region_mat = "unknown"

            body_solid, region_solid = None, None
            if form == "prism":
                body_solid, region_solid = build_prism(
                    place, fw, fd, fh, z, outline or ([], (0.0, 0.0)),
                    form=catalog_form)
                if body_solid or region_solid:
                    by_prism.add(kind)
                else:                    # a ring that would not triangulate
                    form = "box"
                    by_prism.discard(kind)
                    still_box.add(kind)
            if not body_solid and not region_solid:
                body_solid = build_solid(form, place, fw, fd, fh, z, outline)
            parts.setdefault(mat, []).extend(body_solid or [])
            if region_solid:
                parts.setdefault(region_mat, []).extend(region_solid)
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
        if unknown_form:
            model.notes.append(
                "furnishing form(s) this viewer does not recognise, drawn as "
                "a box in magenta: " + ", ".join(sorted(unknown_form)))
        if pending_form:
            # INFO, not a note: a recognised form whose generator is a later
            # pass is a known gap, not a document that could not be drawn.
            model.info.append(
                "furnishing form(s) recognised but not yet built, drawn from "
                "the plan symbol where there is one: "
                + ", ".join(sorted(pending_form)))
        if by_prism:
            model.info.append(
                f"{len(by_prism)} kind(s) EXTRUDED FROM THEIR PLAN SYMBOL "
                f"(prism): " + ", ".join(sorted(by_prism)))
        if still_box:
            # NAMED, not counted. "A third of the catalog renders as a box" was
            # the sentence that sized this work, and the only way it stays
            # checkable is if the survivors are listed rather than totalled --
            # a count cannot be argued with and cannot be acted on.
            model.info.append(
                f"{len(still_box)} kind(s) STILL DRAWN AS A BOX -- the plan "
                f"symbol has no closed filled shape to extrude: "
                + ", ".join(sorted(still_box)))

    # ---- bounds ----------------------------------------------------------
    allv = [m.verts for m in model.meshes if len(m.verts)]
    if allv:
        a = np.vstack(allv)
        model.bbox = (a.min(axis=0), a.max(axis=0))
    model.stats = {"levels": list(lv), "walls": n_wall, "openings": n_open,
                   "rooms": n_floor, "furnishings": n_furn,
                   "triangles": int(sum(len(m.faces) for m in model.meshes)),
                   # WHICH kinds, not how many: the sentence this work is
                   # measured against ("a third of the catalog renders as a
                   # box") can only be falsified by a list
                   "prism_kinds": sorted(by_prism),
                   "box_fallback_kinds": sorted(still_box)}
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
                    help="also list the routine items (outline tidy-ups, "
                         "forms not yet built)")
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
            print(f"  {len(model.info)} routine item(s):")
            for n in model.info:
                print(f"    - {n}")
        else:
            print(f"  ({len(model.info)} routine items; -v to list)")

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
