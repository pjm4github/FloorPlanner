#!/usr/bin/env python3
"""
fp2pdf -- FloorPlanner v5 design JSON -> dimensioned floor-plan PDF,
formatted to a residential designer's transmittal spec:

  * one 11x17 (tabloid) landscape sheet per storey level
  * auto-selected standard architectural scale (1/4", 3/16", 1/8" ... = 1'-0")
  * walls drawn as face pairs with gray poche, broken at openings
  * door symbols (leaf + swing arc / slider panels), window glazing lines,
    every opening tagged with its WWHH size code
  * room labels: NAME / clear WxL size / ceiling height
  * dimension strings (arch ticks, feet-inches text):
      row 1: features -- every wall line + every opening centerline
      row 2: overall
    on the bottom (x) and left (y) of the plan
  * title block: project, level, scale, date, wall-assembly note,
    dimension-reference note, NOT FOR CONSTRUCTION

Dimension reference: OVERALL WALL FACES (stated in the title block).
The receiving designer converts to their own convention (e.g. stud-stud);
wall assemblies are called out so that conversion is deterministic.

Requires: reportlab  (pip install reportlab)

Usage:
    python fp2pdf.py design.json [-o out.pdf] [--title "Wiscaway Crest"]
        [--assembly-note "2x6 exterior / 2x4 interior, conventional framing"]
        [--level ID ...] [--set exterior=6.5 ...] [--include-concept]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path


def _load_stdt_module():
    """`_stdt.py`, loaded BY PATH -- the leaf `0077-ruling.md` sec5 built so
    this file and `fp2dxf.py` share one loader instead of one execing the
    other (execing the whole 23KB `fp2dxf.py` just to reach its seven-line
    loader needed a `sys.modules` registration to satisfy ITS OWN
    `ConvertResult` `@dataclass` -- a coupling this leaf removes; `_stdt.py`
    has no dataclasses to trip over).

    Not `from floorplanner.export._stdt import ...`: importing ANY
    `floorplanner` submodule first runs `floorplanner/__init__.py`, which
    star-imports the whole Qt editor (`export/__init__.py`'s own
    docstring)."""
    path = Path(__file__).resolve().parent / "_stdt.py"
    spec = importlib.util.spec_from_file_location("_fp2pdf_stdt", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_default_thickness_cache = None


def _default_thickness() -> dict[str, float]:
    """THE NORMATIVE thickness table, read live from
    `floorplanner.design.validate` via `_stdt.py` -- REUSED, not
    transcribed (0072-ruling.md sec2(1): this file once shipped a THIRD
    wall-thickness table, disagreeing with the normative one in 4 of 7
    rows).

    LAZY, NOT MODULE SCOPE (0077-ruling.md sec5, the same shape the
    deferred `reportlab` import already has): nothing runs merely by
    importing this file. Cached after the first call within one process."""
    global _default_thickness_cache
    if _default_thickness_cache is None:
        _default_thickness_cache = _load_stdt_module().load_std_thickness()
    return _default_thickness_cache


PAGE = (17 * 72, 11 * 72)                     # 17x11 landscape, in points
MARGIN = 0.5 * 72
DIM_LANE = 0.30 * 72                          # per dimension row
TITLE_H = 0.85 * 72
SCALES = [1 / 48, 1 / 64, 1 / 96, 1 / 128, 1 / 192]   # in/in: 1/4",3/16",1/8",3/32",1/16"
SCALE_NAMES = {1 / 48: '1/4" = 1\'-0"', 1 / 64: '3/16" = 1\'-0"',
               1 / 96: '1/8" = 1\'-0"', 1 / 128: '3/32" = 1\'-0"',
               1 / 192: '1/16" = 1\'-0"'}

GRAY_POCHE = 0.82
GRAY_LT = 0.55


def ftin(v_in: float, dash: bool = True) -> str:
    """246.5 -> 20'-6 1/2\" """
    neg = v_in < 0
    v = abs(v_in)
    whole = math.floor(v + 1e-9)
    frac = v - whole
    sixt = round(frac * 16)
    if sixt == 16:
        whole, sixt = whole + 1, 0
    ft, inch = divmod(whole, 12)
    fs = ""
    if sixt:
        num, den = sixt, 16
        while num % 2 == 0:
            num, den = num // 2, den // 2
        fs = f" {num}/{den}"
    sep = "-" if dash else " "
    s = f"{ft}'{sep}{inch}{fs}\"" if ft else f"{inch}{fs}\""
    return ("-" if neg else "") + s


def parse_code(code: str) -> tuple[float, float]:
    cut = 2 if len(code) == 4 else 3
    return float(code[:cut]), float(code[cut:])


STATION_TOL_IN = 1.0   # 0118-ruling.md sec2 step 1: the sheet's own resolution


def cluster_stations(values, tol: float = STATION_TOL_IN) -> list[float]:
    """Merge dimension stations closer than `tol` into their mean.

    0118-ruling.md sec2: a drifted wall's near-duplicate vertex used to mint
    its own station a fraction of an inch from a clean one, cramming a full
    dimension segment -- extension lines, ticks, a 45-rotated label -- into
    a sliver of the page (the "mess of dimensions on top of each other").
    After whole-inch labels, a segment under `tol` cannot be expressed on
    the sheet at all, so keeping it separate loses nothing the paper could
    say. Chains transitively: a run of stations each within `tol` of its
    predecessor collapses to one, even if the run's own span exceeds `tol`.
    """
    if not values:
        return []
    groups = [[values[0]]]
    for v in values[1:]:
        if v - groups[-1][-1] < tol:
            groups[-1].append(v)
        else:
            groups.append([v])
    return [sum(g) / len(g) for g in groups]


def _rounded_stations(coords):
    """Nearest whole inch, per 0118-ruling.md sec2 step 2 -- computed once
    and shared by row 1's adjacent-pair differences and row 2's overall
    difference, so they telescope BY CONSTRUCTION (integer arithmetic, no
    compounding). Rounding each label independently -- `ftin(b - a)` on the
    raw stations -- does not: it is the classic drafting bug where the
    parts stop summing to the whole."""
    return [round(c) for c in coords]


def _door_symbol(kind: str, door_type) -> str | None:
    """Which PDF symbol a door/gate opening gets -- the vocabulary is
    `floorplanner/config.py:DOOR_TYPES`, drawn in the editor by
    `walls.py:_paint_door`, transcribed here rather than invented.
    Returns None for a non-door/gate kind (window/cased/pass-through,
    handled by `draw_opening`'s own fallback) and `"unknown"` for a
    `door_type` string outside the catalog -- D81's own finding is that
    `door_type == "sliding"` can never match any of these, so that string
    (and any other stray value) now falls through here, drawn as a generic
    swing but named in a warning, not silently absorbed."""
    if kind == "gate":
        return "swing"
    if kind != "door":
        return None
    dt = (door_type or "").upper()
    if dt in ("LH", "RH", ""):
        return "swing"
    if dt == "FRENCH":
        return "french"
    if dt == "BIFOLD":
        return "bifold"
    if dt == "POCKET":
        return "pocket"
    if dt == "SLIDER":
        return "slider"
    if dt == "DOORWAY":
        return "doorway"
    if dt.startswith("GARAGE"):
        return "garage"
    return "unknown"


class Sheet:
    """One storey plan sheet. Plan coords in inches (y already flipped up);
    self.k = points per plan-inch."""

    def __init__(self, c, doc, level, thickness, include_concept, meta):
        self.c, self.doc, self.level = c, doc, level
        self.th, self.inc_concept, self.meta = thickness, include_concept, meta
        self.vx = {v["id"]: v for v in doc["vertices"]}
        self.rooms = {r["id"]: r for r in doc["rooms"]}
        self.walls = [w for w in doc["walls"] if w["level"] == level["id"]
                      and w["type"] not in ("fence", "hedge")]
        self.warnings = []
        self._frame()

    def warn(self, msg: str) -> None:
        # COLLECTED, NOT PRINTED -- `convert()` is a library call from a Qt
        # menu handler as well as the CLI, same shape as fp2dxf.py's
        # `Ctx.warn` (this file's own sibling).
        self.warnings.append(msg)

    # ---------- setup ----------
    def pt(self, vid):
        v = self.vx[vid]
        return float(v["x"]), -float(v["y"])

    def wall_t(self, w):
        return float(w.get("thickness_in") or self.th[w["type"]])

    def is_concept(self, w):
        sides = [s for s in (w.get("left"), w.get("right")) if s]
        return bool(sides) and all(
            self.rooms[s]["category"] == "concept" for s in sides
            if s in self.rooms)

    def _frame(self):
        xs, ys = [], []
        for w in self.walls:
            if self.is_concept(w) and not self.inc_concept:
                continue
            t2 = self.wall_t(w) / 2
            for vid in (w["v1"], w["v2"]):
                x, y = self.pt(vid)
                xs += [x - t2, x + t2]
                ys += [y - t2, y + t2]
        self.bx0, self.bx1 = min(xs), max(xs)
        self.by0, self.by1 = min(ys), max(ys)
        w_in, h_in = self.bx1 - self.bx0, self.by1 - self.by0
        avail_w = PAGE[0] - 2 * MARGIN - 3 * DIM_LANE
        avail_h = PAGE[1] - 2 * MARGIN - TITLE_H - 3 * DIM_LANE
        self.k = None
        for s in SCALES:
            if w_in * s * 72 <= avail_w and h_in * s * 72 <= avail_h:
                self.k = s * 72
                self.scale_name = SCALE_NAMES[s]
                break
        if self.k is None:                       # fit-to-page fallback
            self.k = min(avail_w / w_in, avail_h / h_in)
            self.scale_name = "NTS"
        # plan origin -> page: center in available area, left+bottom lanes
        px = MARGIN + 3 * DIM_LANE + (avail_w - w_in * self.k) / 2
        py = MARGIN + TITLE_H + 3 * DIM_LANE + (avail_h - h_in * self.k) / 2
        self.ox = px - self.bx0 * self.k
        self.oy = py - self.by0 * self.k

    def X(self, x):  return self.ox + x * self.k
    def Y(self, y):  return self.oy + y * self.k

    # ---------- drawing primitives ----------
    def line(self, x1, y1, x2, y2, w=0.7, gray=0.0, dash=None):
        c = self.c
        c.saveState()
        c.setLineWidth(w)
        c.setStrokeGray(gray)
        if dash:
            c.setDash(dash)
        c.line(self.X(x1), self.Y(y1), self.X(x2), self.Y(y2))
        c.restoreState()

    def text(self, x, y, s, size=7, rot=0.0, bold=False, gray=0.0,
             center=True):
        c = self.c
        c.saveState()
        c.translate(self.X(x), self.Y(y))
        c.rotate(rot)
        c.setFillGray(gray)
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        w = c.stringWidth(s, font, size)
        c.drawString(-w / 2 if center else 0, -size * 0.36 if center else 0, s)
        c.restoreState()
        return self.c.stringWidth(s, font, size)

    # ---------- walls & openings ----------
    def opening_span(self, w, op, L):
        wd, _ = parse_code(op["code"])
        off = float(op["anchor"]["offset_in"])
        frm = op["anchor"]["from"]
        if frm == "v1":
            s0 = off
        elif frm == "v2":
            s0 = L - off - wd
        else:
            s0 = L / 2 + off - wd / 2
        return max(0.0, s0), min(L, s0 + wd)

    def draw_walls(self):
        c = self.c
        for w in self.walls:
            concept = self.is_concept(w)
            if concept and not self.inc_concept:
                continue
            p1, p2 = self.pt(w["v1"]), self.pt(w["v2"])
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            L = math.hypot(dx, dy)
            if L < 1e-9:
                continue
            ux, uy = dx / L, dy / L
            nx, ny = -uy, ux
            t2 = self.wall_t(w) / 2
            spans = sorted(
                (self.opening_span(w, op, L), op)
                for op in (w.get("openings") or []))
            breaks = [0.0]
            for (s0, s1), _ in spans:
                breaks += [s0, s1]
            breaks.append(L)

            def P(s, side, p1=p1, ux=ux, uy=uy, nx=nx, ny=ny, t2=t2):
                return (p1[0] + ux * s + nx * t2 * side,
                        p1[1] + uy * s + ny * t2 * side)

            for i in range(0, len(breaks) - 1, 2):
                a, b = breaks[i], breaks[i + 1]
                if b - a < 1e-9:
                    continue
                poly = [P(a, 1), P(b, 1), P(b, -1), P(a, -1)]
                c.saveState()
                if concept:
                    c.setStrokeGray(GRAY_LT)
                    c.setDash([3, 2])
                else:
                    c.setFillGray(GRAY_POCHE)
                p = c.beginPath()
                p.moveTo(self.X(poly[0][0]), self.Y(poly[0][1]))
                for q in poly[1:]:
                    p.lineTo(self.X(q[0]), self.Y(q[1]))
                p.close()
                c.setLineWidth(0.9)
                c.drawPath(p, stroke=1, fill=0 if concept else 1)
                c.restoreState()
            for (s0, s1), op in spans:
                self._host_wall_left = bool(w.get("left"))
                self.draw_opening(op, p1, ux, uy, nx, ny, t2, s0, s1)

    def draw_opening(self, op, p1, ux, uy, nx, ny, t2, s0, s1):
        wd = s1 - s0
        mid = (s0 + s1) / 2
        kind = op["kind"]

        def A(s, d):   # point at station s, offset d from centerline
            return (p1[0] + ux * s + nx * d, p1[1] + uy * s + ny * d)

        def rect(sa, da, sb, db, w=0.7, dash=None):
            pts = [A(sa, da), A(sb, da), A(sb, db), A(sa, db)]
            for a, b in zip(pts, pts[1:] + pts[:1], strict=True):
                self.line(*a, *b, w=w, dash=dash)

        def leaf(hinge_s, radius, direction, sgn):
            """One swing leaf + quarter-circle arc, hinged at `hinge_s`.
            `direction` = +1 if the jamb it swings toward sits at a HIGHER
            station, -1 if lower. Reference: `walls.py:_paint_door`'s
            `_swing_arc` -- same shape (hinge -> perpendicular open-leaf
            tip, arc back to the jamb), this file's own coordinate frame."""
            hx, hy = A(hinge_s, 0)
            jx, jy = A(hinge_s + direction * radius, 0)
            lx, ly = hx + nx * radius * sgn, hy + ny * radius * sgn
            self.line(hx, hy, lx, ly, w=0.8)
            a_leaf = math.degrees(math.atan2(ly - hy, lx - hx))
            a_jamb = math.degrees(math.atan2(jy - hy, jx - hx))
            if (a_leaf - a_jamb) % 360.0 <= 180.0:
                start, ext = a_jamb, (a_leaf - a_jamb) % 360.0
            else:
                start, ext = a_leaf, (a_jamb - a_leaf) % 360.0
            c = self.c
            c.saveState()
            c.setLineWidth(0.5)
            c.arc(self.X(hx - radius), self.Y(hy - radius),
                  self.X(hx + radius), self.Y(hy + radius), start, ext)
            c.restoreState()

        # jamb lines closing the wall poche
        for s in (s0, s1):
            a, b = A(s, t2), A(s, -t2)
            self.line(*a, *b, w=0.9)

        symbol = _door_symbol(kind, op.get("door_type"))
        if symbol is None:                           # window / cased / pass
            for d in (t2 * 0.25, -t2 * 0.25):
                self.line(*A(s0, d), *A(s1, d), w=0.6)
            if kind == "window":
                self.line(*A(mid, t2 * 0.25), *A(mid, -t2 * 0.25), w=0.6)
        else:
            if symbol == "unknown":
                self.warn(f"opening {op.get('code')}: unrecognized "
                          f"door_type {op.get('door_type')!r}, drawn as a "
                          f"generic swing")
            hinge = op.get("hinge") if op.get("hinge") in ("v1", "v2") else "v1"
            swing = op.get("swings_toward")
            if swing not in ("left", "right"):
                # default: swing toward whichever side of the wall has a
                # room (Qt-left maps to geometric left under the y-flip)
                swing = "left" if self._host_wall_left else "right"
            sgn = 1.0 if swing == "left" else -1.0
            if symbol in ("swing", "unknown"):
                if hinge == "v1":
                    leaf(s0, wd, 1.0, sgn)
                else:
                    leaf(s1, wd, -1.0, sgn)
            elif symbol == "french":
                leaf(s0, wd / 2, 1.0, sgn)
                leaf(s1, wd / 2, -1.0, sgn)
            elif symbol == "bifold":
                face_d = sgn * t2
                rise = sgn * 0.35 * wd
                for a, m, b in ((s0, s0 + 0.25 * wd, mid),
                                (mid, s0 + 0.75 * wd, s1)):
                    self.line(*A(a, face_d), *A(m, face_d + rise), w=0.8)
                    self.line(*A(m, face_d + rise), *A(b, face_d), w=0.8)
            elif symbol == "pocket":
                # dashed panel slid INTO the wall run before s0, plus the
                # short solid stub still visible at the opening's near half
                rect(s0 - wd, -t2 + 0.75, s0, t2 - 0.75, w=0.7, dash=[3, 2])
                rect(s0, -t2 / 3, mid, t2 / 3, w=0.8)
            elif symbol == "slider":
                pw = 0.55 * wd
                rect(s0, -0.70 * t2, s0 + pw, -0.10 * t2, w=0.8)
                rect(s1 - pw, 0.10 * t2, s1, 0.70 * t2, w=0.8)
            elif symbol == "doorway":
                for d in (t2, -t2):
                    self.line(*A(s0, d), *A(s1, d), w=0.6, dash=[3, 2])
            elif symbol == "garage":
                _wd_code, h = parse_code(op["code"])
                rect(s0, -t2 * 0.25, s1, t2 * 0.25, w=0.8)
                depth = sgn * min(h, 96.0)
                y0 = sgn * t2
                rect(s0, y0, s1, y0 + depth, w=0.6, dash=[3, 2])
                if (op.get("door_type") or "").upper() == "GARAGE-2":
                    self.line(*A(mid, y0), *A(mid, y0 + depth), w=0.6,
                              dash=[3, 2])

        rot = math.degrees(math.atan2(uy, ux))
        if rot > 90 or rot <= -90:
            rot += 180
        tx, ty = A(mid, t2 + 8.0 / self.k)               # 8 pt off face
        self.text(tx, ty, op["code"], size=6, rot=rot)

    # ---------- rooms ----------
    def draw_rooms(self):
        for room in self.doc["rooms"]:
            if room["level"] != self.level["id"]:
                continue
            if room["category"] == "concept" and not self.inc_concept:
                continue
            pts = [self.pt(e["v"]) for e in room["outline"]]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
            # clear size for axis-aligned rectangles: centerline bbox
            # minus half-thickness of each bounding wall
            name = room["name"].upper()
            lines = [(name, 9, True)]
            if len(pts) == 4 and self._axis_aligned(pts):
                w_clear, h_clear = self._clear_dims(room, xs, ys)
                lines.append((f"{ftin(w_clear)} x {ftin(h_clear)}", 7, False))
            clg = (room.get("properties") or {}).get("ceiling_height_in") \
                or self.level.get("height_in")
            if clg:
                lines.append((f"CLG {ftin(float(clg))}", 6, False))
            if room.get("area_accounting") == "unconditioned":
                lines.append(("UNCONDITIONED", 5.5, False))
            lh = 12.0 / self.k                      # 12 pt in plan inches
            yy = cy + (len(lines) - 1) * lh / 2
            for i, (s, size, bold) in enumerate(lines):
                self.text(cx, yy - i * lh, s,
                          size=size, bold=bold,
                          gray=GRAY_LT if room["category"] == "concept"
                          else 0.0)

    @staticmethod
    def _axis_aligned(pts):
        for i in range(4):
            a, b = pts[i], pts[(i + 1) % 4]
            if abs(a[0] - b[0]) > 1e-6 and abs(a[1] - b[1]) > 1e-6:
                return False
        return True

    def _clear_dims(self, room, xs, ys):
        wmap = {}
        for w in self.walls:
            wmap[frozenset((w["v1"], w["v2"]))] = w
        # half-thickness per edge orientation
        sub_x, sub_y = [0.0, 0.0], [0.0, 0.0]   # [min-side, max-side]
        n = len(room["outline"])
        for i, e in enumerate(room["outline"]):
            if e.get("wall") is None:
                continue
            v1 = e["v"]
            v2 = room["outline"][(i + 1) % n]["v"]
            w = wmap.get(frozenset((v1, v2)))
            if not w:
                continue
            t2 = self.wall_t(w) / 2
            a, b = self.pt(v1), self.pt(v2)
            if abs(a[0] - b[0]) < 1e-6:          # vertical edge
                side = 0 if abs(a[0] - min(xs)) < 1e-6 else 1
                sub_x[side] = max(sub_x[side], t2)
            else:                                 # horizontal edge
                side = 0 if abs(a[1] - min(ys)) < 1e-6 else 1
                sub_y[side] = max(sub_y[side], t2)
        return (max(xs) - min(xs) - sub_x[0] - sub_x[1],
                max(ys) - min(ys) - sub_y[0] - sub_y[1])

    # ---------- dimensions ----------
    def _features(self):
        fx, fy = set(), set()
        for w in self.walls:
            if self.is_concept(w):
                continue
            p1, p2 = self.pt(w["v1"]), self.pt(w["v2"])
            for p in (p1, p2):
                fx.add(round(p[0], 3))
                fy.add(round(p[1], 3))
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            L = math.hypot(dx, dy)
            if L < 1e-9:
                continue
            ux, uy = dx / L, dy / L
            for op in (w.get("openings") or []):
                s0, s1 = self.opening_span(w, op, L)
                mid = (s0 + s1) / 2
                mx, my = p1[0] + ux * mid, p1[1] + uy * mid
                if abs(uy) < 1e-6:
                    fx.add(round(mx, 3))
                elif abs(ux) < 1e-6:
                    fy.add(round(my, 3))
        return cluster_stations(sorted(fx)), cluster_stations(sorted(fy))

    def dim_row_along(self, ext_pairs, station_pts, labels, rot_deg):
        """One dimension string -- extension lines, the row line + arch
        ticks, and labels -- shared by the two orthogonal rows and (a
        later, angled-lane tranche). 0119-ruling.md sec3: "the same
        routine with the axis baked in... one generalisation, not a
        third copy." Entirely in PAGE POINTS; a caller does its own
        plan-to-page projection (the near-drawing gaps and overshoot are
        the one part that genuinely differs per row, not the part named
        as triplicated).

        `ext_pairs`: [(start_pt, end_pt), ...], one per station, drawn
        as-is. `station_pts`: the row-line points themselves, ticked and
        connected. `labels`: len(station_pts) - 1 strings, one per
        adjacent pair. `rot_deg`: text rotation, already flipped upright
        by the caller -- the same one-line idiom `draw_opening` and
        `draw_extras` use for their own labels."""
        if len(station_pts) < 2:
            return
        c = self.c
        for start, end in ext_pairs:
            c.saveState()
            c.setLineWidth(0.4)
            c.setStrokeGray(0.25)
            c.line(start[0], start[1], end[0], end[1])
            c.restoreState()
        c.saveState()
        c.setLineWidth(0.5)
        (x0, y0), (x1, y1) = station_pts[0], station_pts[-1]
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        ux, uy = dx / length, dy / length
        c.line(x0 - 4 * ux, y0 - 4 * uy, x1 + 4 * ux, y1 + 4 * uy)
        for px, py in station_pts:                # arch ticks
            c.setLineWidth(0.9)
            c.line(px - 3, py - 3, px + 3, py + 3)
        c.restoreState()
        for (ax, ay), (bx, by), label in zip(
                station_pts, station_pts[1:], labels, strict=False):
            seg_len = math.hypot(bx - ax, by - ay)
            mx, my = (ax + bx) / 2, (ay + by) / 2
            c.setFont("Helvetica", 6.5)
            wpt = c.stringWidth(label, "Helvetica", 6.5)
            c.saveState()
            c.translate(mx, my)
            c.rotate(rot_deg)
            if wpt + 4 < seg_len:
                c.drawCentredString(0, 2.5, label)
            else:
                c.rotate(45)
                c.drawString(3, 1, label)
            c.restoreState()

    def dim_row_x(self, coords, y_pt):
        """horizontal dimension string at page-y y_pt (points)"""
        if len(coords) < 2:
            return
        rounded = _rounded_stations(coords)
        labels = [ftin(rb - ra) for ra, rb in
                  zip(rounded, rounded[1:], strict=False)]
        station_pts = [(self.X(x), y_pt) for x in coords]
        ext_base = self.oy + self.by0 * self.k - 4
        ext_pairs = [((self.X(x), ext_base), (self.X(x), y_pt - 5))
                     for x in coords]
        self.dim_row_along(ext_pairs, station_pts, labels, 0.0)

    def dim_row_y(self, coords, x_pt):
        if len(coords) < 2:
            return
        rounded = _rounded_stations(coords)
        labels = [ftin(rb - ra) for ra, rb in
                  zip(rounded, rounded[1:], strict=False)]
        station_pts = [(x_pt, self.Y(y)) for y in coords]
        ext_base = self.ox + self.bx0 * self.k - 4
        ext_pairs = [((ext_base, self.Y(y)), (x_pt + 5, self.Y(y)))
                     for y in coords]
        self.dim_row_along(ext_pairs, station_pts, labels, 90.0)

    def draw_dims(self):
        fx, fy = self._features()
        y1 = self.oy + self.by0 * self.k - DIM_LANE
        y2 = y1 - DIM_LANE
        self.dim_row_x(fx, y1)
        self.dim_row_x([fx[0], fx[-1]], y2)
        x1 = self.ox + self.bx0 * self.k - DIM_LANE
        x2 = x1 - DIM_LANE
        self.dim_row_y(fy, x1)
        self.dim_row_y([fy[0], fy[-1]], x2)

    # ---------- annotations, open edges ----------
    def draw_extras(self):
        for room in self.doc["rooms"]:
            if room["level"] != self.level["id"]:
                continue
            loops = [room["outline"]] + list(room.get("holes") or [])
            for loop in loops:
                n = len(loop)
                for i, e in enumerate(loop):
                    if e.get("wall") is None:
                        a = self.pt(e["v"])
                        b = self.pt(loop[(i + 1) % n]["v"])
                        self.line(*a, *b, w=0.6, gray=GRAY_LT, dash=[4, 3])
                        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                        rot = math.degrees(math.atan2(b[1] - a[1],
                                                      b[0] - a[0]))
                        if rot > 90 or rot <= -90:
                            rot += 180
                        self.text(mx, my, "OPEN", size=5.5, rot=rot,
                                  gray=GRAY_LT)
        for ann in self.doc.get("annotations") or []:
            if ann["level"] == self.level["id"] and ann["kind"] == "text" \
                    and ann.get("text"):
                x, y = float(ann["pos"][0]), -float(ann["pos"][1])
                self.text(x, y, ann["text"], size=6, gray=0.2,
                          rot=-float(ann.get("rotation", 0)), center=False)

    # ---------- title block ----------
    def title_block(self, sheet_no, total):
        c = self.c
        m = self.meta
        y0 = MARGIN
        c.saveState()
        c.setLineWidth(1.0)
        c.rect(MARGIN, y0, PAGE[0] - 2 * MARGIN, TITLE_H)
        cols = [MARGIN, MARGIN + 5.4 * 72, MARGIN + 10.2 * 72,
                MARGIN + 13.4 * 72, PAGE[0] - MARGIN]
        for x in cols[1:-1]:
            c.line(x, y0, x, y0 + TITLE_H)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(cols[0] + 8, y0 + TITLE_H - 18, m["title"])
        c.setFont("Helvetica", 7.5)
        c.drawString(cols[0] + 8, y0 + TITLE_H - 32, m["subtitle"])
        c.setFont("Helvetica", 7)
        c.drawString(cols[0] + 8, y0 + 8,
                     "DESIGN REFERENCE ONLY - NOT FOR CONSTRUCTION")
        c.setFont("Helvetica-Bold", 11)
        c.drawString(cols[1] + 8, y0 + TITLE_H - 18,
                     self.level.get("name", self.level["id"]).upper()
                     + " - FLOOR PLAN")
        c.setFont("Helvetica", 7.5)
        c.drawString(cols[1] + 8, y0 + TITLE_H - 32,
                     f"SCALE: {self.scale_name}   (11x17 SHEET)")
        c.drawString(cols[1] + 8, y0 + 8, m["dim_note"])
        c.setFont("Helvetica", 7.5)
        c.drawString(cols[2] + 8, y0 + TITLE_H - 16, "WALL ASSEMBLIES:")
        c.drawString(cols[2] + 8, y0 + TITLE_H - 28, m["assembly_note"])
        c.drawString(cols[2] + 8, y0 + 8,
                     "Openings tagged W/H in inches (e.g. 3080 = 3'-0\" x 6'-8\")")
        c.setFont("Helvetica", 7.5)
        c.drawString(cols[3] + 8, y0 + TITLE_H - 16,
                     time.strftime("DATE: %Y-%m-%d"))
        c.drawString(cols[3] + 8, y0 + TITLE_H - 28, f"BY: {m['author']}")
        c.setFont("Helvetica-Bold", 16)
        c.drawRightString(cols[4] - 10, y0 + 10, f"P{sheet_no}")
        c.setFont("Helvetica", 7)
        c.drawRightString(cols[4] - 10, y0 + TITLE_H - 16,
                          f"SHEET {sheet_no} OF {total}")
        c.restoreState()

    def render(self, sheet_no, total):
        self.draw_walls()
        self.draw_rooms()
        self.draw_extras()
        self.draw_dims()
        self.title_block(sheet_no, total)
        self.c.showPage()


@dataclass
class ConvertResult:
    """Everything a caller needs to show a completion summary -- a GUI menu
    handler as much as the CLI below, per 0072-ruling.md sec2(3), the same
    shape `fp2dxf.ConvertResult` already settled: the module has no
    business deciding where its progress and warnings are READ, only
    collecting them."""
    out: Path = None
    sheets: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def convert(doc, out: Path, meta, only_levels=None,
            thickness_overrides=None, include_concept=False) -> ConvertResult:
    if doc.get("format") != "floorplanner-design" or doc.get("version") != 5:
        # A NORMAL EXCEPTION, NOT `raise SystemExit` (0038-ruling.md sec4 /
        # 0072-ruling.md sec2(2)): this is a library call from a Qt menu
        # handler as well as the CLI, and `SystemExit` inside a Qt call
        # stack is not something a `try/except Exception` around the menu
        # action would even see coming.
        raise ValueError("not a floorplanner-design v5 document")
    try:
        # DEFERRED, NOT A MODULE-TOP IMPORT (0072-ruling.md sec2(4) / D40):
        # reportlab is optional (requirements-viewer.txt's own precedent --
        # "optional; the editor runs without it"), so importing it only
        # inside convert() means the module itself, and the app that wires
        # it in, still load without it -- only an actual export attempt
        # fails, with a reason.
        from reportlab.pdfgen import canvas as rl_canvas
    except ImportError as exc:
        raise ValueError(
            "reportlab is not installed; PDF export is unavailable "
            "(pip install reportlab)") from exc
    th = dict(_default_thickness())
    th.update(thickness_overrides or {})
    levels = [lv for lv in doc["levels"]
              if lv.get("kind", "storey") != "site"
              and (not only_levels or lv["id"] in only_levels)]
    result = ConvertResult(out=out)
    c = rl_canvas.Canvas(str(out), pagesize=PAGE)
    c.setTitle(f"{meta['title']} - floor plans")
    c.setAuthor(meta["author"])
    for i, lv in enumerate(levels):
        sheet = Sheet(c, doc, lv, th, include_concept, meta)
        sheet.render(i + 1, len(levels))
        result.sheets.append(f"sheet P{i + 1}: {lv.get('name', lv['id'])}")
        result.warnings.extend(sheet.warnings)
    c.save()
    return result


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("design", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("plans.pdf"))
    ap.add_argument("--title", default="RESIDENCE")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--author", default="Owner")
    ap.add_argument("--assembly-note",
                    default="2x6 exterior / 2x4 interior, conventional framing")
    ap.add_argument("--dim-note",
                    default="All dimensions to overall wall faces")
    ap.add_argument("--level", action="append", dest="levels")
    ap.add_argument("--set", action="append", default=[], metavar="TYPE=IN")
    ap.add_argument("--include-concept", action="store_true")
    a = ap.parse_args(argv)
    overrides = {}
    for kv in a.set:
        k, _, v = kv.partition("=")
        overrides[k] = float(v)
    meta = {"title": a.title, "subtitle": a.subtitle, "author": a.author,
            "assembly_note": a.assembly_note, "dim_note": a.dim_note}
    doc = json.loads(a.design.read_text(encoding="utf-8"))
    print(f"fp2pdf: {a.design}")
    result = convert(doc, a.out, meta, a.levels, overrides, a.include_concept)
    for line in result.sheets:
        print(f"  {line}")
    for msg in result.warnings:
        print(f"  WARNING: {msg}")
    print(f"  wrote {result.out}")


if __name__ == "__main__":
    main()
