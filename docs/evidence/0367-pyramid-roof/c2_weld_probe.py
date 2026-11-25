"""0367 — C2 read-back probe: the pyramid WELD, prototyped and timed.

The weld (ruling §4): where a pyramid and a roof overlap in plan, EACH is drawn
only where it is the higher surface; the boundary is the equal-height line, exact
(both surfaces are planar by pieces, so it is a line, interpolated not sampled).

This prototypes the core decomposition the full stage-3 build would use, and
TIMES it, to answer C2: where it is computed, its cost, and proof it RETURNS.

It is a PAIRWISE pass over (pyramid, roof) couples, each one:
  1. overlap   = convex∩convex           (pyramid eave polygon ∩ roof footprint)
  2. cells     = overlap split by the pyramid's hips and the roof's cut lines
                 -> on each cell BOTH surfaces are a single plane, so the height
                 difference is AFFINE
  3. boundary  = the zero set of that affine difference = ONE line per cell,
                 found by `_clip_by_values` (exact interpolation, no sampling)
It never calls `compute_roof_clips` (0350 §1's non-returning adjacency/component
walk on three roofs): there is no graph, no recursion, no iteration-to-converge.

Run:  python docs/evidence/0367-pyramid-roof/c2_weld_probe.py
Writes C2-weld-timing.json next to itself.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import floorplanner.roofclip as rc                       # noqa: E402
from floorplanner.parametric import pyramid_geometry as pg  # noqa: E402


def roof(rid, ridge, eaves, ridge_h, span, overhang=(12, 12)):
    rec = {"id": rid, "level": "L1", "ridge": ridge, "eaves_h_in": eaves,
           "ridge_h_in": ridge_h, "span_in": list(span),
           "overhang_in": list(overhang), "gable": [True, True]}
    return rid, rc.RoofGeom.from_record(rec, span_fallback=span[0])


# 0350 §1's three-roof case: a main gable (rf1) and two cross gables on opposite
# sides of it (rf2 front, rf3 rear), meeting at (200, 200) -- the junction whose
# ROOF-ROOF clip (`compute_roof_clips`) did not return. The weld does not use it.
THREE_ROOFS = [
    roof("rf1", [[0, 200], [400, 200]], 96, 150, (100, 100)),
    roof("rf2", [[200, 200], [200, 340]], 96, 150, (60, 60)),
    roof("rf3", [[200, 200], [200, 60]], 96, 150, (60, 60)),
]
ONE_ROOF = [THREE_ROOFS[0]]

# a pyramid at the junction, higher than the roofs around it (eaves above the
# main's eaves), so it welds against all three.
PYR = {"pos": (200.0, 200.0), "rot": 0.0,
       "st": pg.normalize_state({"sides": 8, "inradius_in": 72.0,
                                 "eaves_bind": "manual", "eaves_h_in": 128.0,
                                 "pitch_12": 12.0, "overhang_in": 12.0})}


def weld(pyr, roofs):
    """The welded plan pieces: for each (pyramid, roof) couple, the part of the
    overlap where the pyramid is higher, and the part where the roof is. Returns
    counts: couples that overlap, cells decomposed, boundary segments."""
    pos, rot, st = pyr["pos"], pyr["rot"], pyr["st"]
    p_fp = [rc.Pt(*pg.to_plan(pos, rot, v)) for v in pg.eaves_polygon(st)]
    p_cuts = []
    for v in pg.eaves_polygon(st):
        wx, wy = pg.to_plan(pos, rot, v)
        p_cuts.append((rc.Pt(pos[0], pos[1]), rc.Pt(wx - pos[0], wy - pos[1])))

    def hP(p):
        return pg.plane_height(st, pg.to_local(pos, rot, (p.x(), p.y())))

    overlaps = cells_total = boundaries = pyr_pieces = roof_pieces = 0
    for _name, g in roofs:
        ov = rc._convex_intersection(p_fp, rc.footprint_polygon(g))
        if len(ov) < 3:
            continue
        overlaps += 1
        cells = [ov]
        for a, d in p_cuts + rc._cut_lines(g):
            cells = [c for cell in cells for c in rc._split_by_line(cell, a, d)]
        for cell in cells:
            if len(cell) < 3:
                continue
            cells_total += 1
            vals = [hP(v) - rc.surface_height(g, v) for v in cell]
            hi, cr = rc._clip_by_values(cell, vals)          # pyramid higher
            lo, _ = rc._clip_by_values(cell, [-x for x in vals])  # roof higher
            if cr:
                boundaries += 1
            if len(hi) >= 3 and rc._area(hi) > rc.MIN_CELL_AREA:
                pyr_pieces += 1
            if len(lo) >= 3 and rc._area(lo) > rc.MIN_CELL_AREA:
                roof_pieces += 1
    return {"overlaps": overlaps, "cells": cells_total, "boundaries": boundaries,
            "pyramid_pieces": pyr_pieces, "roof_pieces": roof_pieces}


def timed(pyr, roofs, iters):
    t0 = time.perf_counter()
    for _ in range(iters):
        shape = weld(pyr, roofs)
    dt = time.perf_counter() - t0
    return shape, dt / iters * 1e3            # ms per weld


def main():
    cases = {
        "one roof + pyramid": (ONE_ROOF, 2000),
        "three-roof junction + pyramid (0350 §1)": (THREE_ROOFS, 2000),
    }
    out = {}
    for name, (roofs, iters) in cases.items():
        shape, ms = timed(PYR, roofs, iters)
        out[name] = {"ms_per_weld": round(ms, 4), "iters": iters, **shape,
                     "returned": True}
        print(f"{name}: {ms:.3f} ms/weld  {shape}")
    (Path(__file__).with_name("C2-weld-timing.json")).write_text(
        json.dumps({"note": "pairwise pyramid weld; no compute_roof_clips",
                    "cases": out}, indent=2) + "\n", encoding="utf-8")
    print("wrote C2-weld-timing.json")


if __name__ == "__main__":
    main()
