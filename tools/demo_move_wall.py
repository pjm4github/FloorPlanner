#!/usr/bin/env python3
"""Demonstrate that moving a wall in a v5 design resizes the adjoining rooms
with NO other edit to the document.

Moving a wall = moving its two vertices.  Because vertices are the only place
coordinates live, every room outline and every other wall that references those
vertices follows automatically -- there is nothing to synchronise and nothing
that can drift.  The only rule that needs care is the SPLIT RULE: if a wall
collinear with the one being dragged continues past an endpoint, that vertex
must be split first (insert a new vertex, re-point the dragged wall at it) or
the continuation would be sheared.  This script picks a wall with no collinear
continuation so the pure vertex move is legal.

Usage: python demo_move_wall.py design.json schema.json [wall_id] [dx] [dy]
"""
import copy
import json
import math
import sys

import validate_design as VD


def area_sf(doc, r):
    P = {v["id"]: (v["x"], v["y"]) for v in doc["vertices"]}
    return abs(VD._area2([P[e["v"]] for e in r["outline"]])) / 2 / 144


def pick_wall(doc):
    P = {v["id"]: (v["x"], v["y"]) for v in doc["vertices"]}
    inc = {}
    for w in doc["walls"]:
        inc.setdefault(w["v1"], []).append(w)
        inc.setdefault(w["v2"], []).append(w)
    best = None
    for w in doc["walls"]:
        if not (w.get("left") and w.get("right")):
            continue                                  # want a SHARED wall
        a, b = P[w["v1"]], P[w["v2"]]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 60 or (abs(dx) > 1e-6 and abs(dy) > 1e-6):
            continue                                  # axis-aligned, decent length
        ok = True
        for vid in (w["v1"], w["v2"]):
            for o in inc[vid]:
                if o["id"] == w["id"]:
                    continue
                oa, ob = P[o["v1"]], P[o["v2"]]
                odx, ody = ob[0] - oa[0], ob[1] - oa[1]
                if abs(odx * dy - ody * dx) < 1e-6:    # collinear continuation
                    ok = False
        if ok and (best is None or L > best[1]):
            best = (w, L)
    return best[0] if best else None


def move_wall(doc, wid, dx, dy):
    """The entire operation.  Two vertices move.  That is all."""
    w = next(x for x in doc["walls"] if x["id"] == wid)
    for v in doc["vertices"]:
        if v["id"] in (w["v1"], w["v2"]):
            v["x"] += dx
            v["y"] += dy


if __name__ == "__main__":
    path, schema = sys.argv[1], sys.argv[2]
    doc = json.load(open(path))
    wid = sys.argv[3] if len(sys.argv) > 3 else None
    dx = float(sys.argv[4]) if len(sys.argv) > 4 else None
    dy = float(sys.argv[5]) if len(sys.argv) > 5 else None

    w = (next(x for x in doc["walls"] if x["id"] == wid) if wid else pick_wall(doc))
    P = {v["id"]: (v["x"], v["y"]) for v in doc["vertices"]}
    a, b = P[w["v1"]], P[w["v2"]]
    if dx is None:
        vertical = abs(b[0] - a[0]) < 1e-6
        dx, dy = (12.0, 0.0) if vertical else (0.0, 12.0)

    L = {x["id"]: x for x in doc["rooms"]}
    lname, rname = L[w["left"]]["name"], L[w["right"]]["name"]
    print(f"wall {w['id']}  {w['type']}  ({a[0]:.0f},{a[1]:.0f})-({b[0]:.0f},{b[1]:.0f})"
          f"   left={lname}  right={rname}")
    print(f"move by ({dx:+.0f}, {dy:+.0f}) -- editing exactly 2 vertices "
          f"({w['v1']}, {w['v2']}) and nothing else\n")

    before = {r["id"]: area_sf(doc, r) for r in doc["rooms"]}
    after_doc = copy.deepcopy(doc)
    move_wall(after_doc, w["id"], dx, dy)
    after = {r["id"]: area_sf(after_doc, r) for r in after_doc["rooms"]}

    print(f"  {'room':<16}{'before sf':>10}{'after sf':>10}{'delta':>9}")
    tb = ta = 0.0
    for r in sorted(doc["rooms"], key=lambda r: r["name"]):
        d = after[r["id"]] - before[r["id"]]
        tb += before[r["id"]]
        ta += after[r["id"]]
        flag = "  <-- resized" if abs(d) > 0.05 else ""
        if flag or True:
            print(f"  {r['name']:<16}{before[r['id']]:>10.1f}{after[r['id']]:>10.1f}"
                  f"{d:>+9.1f}{flag}")
    print(f"  {'TOTAL':<16}{tb:>10.1f}{ta:>10.1f}{ta - tb:>+9.1f}")

    errs = VD.check(after_doc)
    import jsonschema
    serr = list(jsonschema.Draft202012Validator(json.load(open(schema)))
                .iter_errors(after_doc))
    print(f"\nafter the move -- JSON Schema: {'PASS' if not serr else 'FAIL'}"
          f"   Invariants: {'PASS' if not errs else str(len(errs)) + ' ERRORS'}")
    for e in errs[:5]:
        print("   ", e)
