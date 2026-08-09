#!/usr/bin/env python3
"""STAGE TWO's PRE-IMPLEMENTATION CHECK: can a dissolve break a ring, or make a weld pair?

    python docs/evidence/coalesce_safety_check.py <plan.json> [more.json ...]

Two questions were ordered before any code:

  1. can dissolving a degree-2 collinear vertex CREATE or DESTROY a ring
     degeneracy of the kind D41 proposes an invariant for?
  2. can any dissolve produce a vertex pair inside I14's 0.6" weld distance?

**The predicate under test is the one the ruling specifies** -- "a degree-2
vertex whose two incident walls are collinear" -- and this asks what that
predicate actually selects on real plans, rather than what it was meant to.

THE DISTINCTION IT IS LOOKING FOR. At a genuine mid-run vertex the two incident
walls leave it in OPPOSITE directions: the vertex lies between them. At the tip
of a ZERO-WIDTH SPUR -- the slit a room uses to carve out an enclosed closet,
D52 -- the two walls leave in the SAME direction, out and back along one line.
BOTH ARE COLLINEAR. A line test cannot tell them apart; only a direction test
can, and the ruling's wording does not include one.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

COLLINEAR_DEG = 0.5          # the tolerance the stage-one probe used
WELD_TOL = 0.6               # I14


def load(path):
    return json.loads(open(path, encoding="utf-8").read())


def analyse(doc, name):
    V = {v["id"]: (v["x"], v["y"]) for v in doc["vertices"]}
    inc = {}
    for w in doc["walls"]:
        for end, other in ((w["v1"], w["v2"]), (w["v2"], w["v1"])):
            inc.setdefault(end, []).append((w["id"], other))

    midpoints, spur_tips = [], []
    for vid, ends in inc.items():
        if len(ends) != 2:
            continue
        (w1, o1), (w2, o2) = ends
        p = V[vid]
        d1 = (V[o1][0] - p[0], V[o1][1] - p[1])
        d2 = (V[o2][0] - p[0], V[o2][1] - p[1])
        n1 = math.hypot(*d1) or 1e-9
        n2 = math.hypot(*d2) or 1e-9
        u1 = (d1[0] / n1, d1[1] / n1)
        u2 = (d2[0] / n2, d2[1] / n2)
        dot = u1[0] * u2[0] + u1[1] * u2[1]
        # collinear as a LINE: the two directions are parallel either way
        if abs(abs(dot) - 1.0) > math.radians(COLLINEAR_DEG):
            continue
        rec = {"vertex": vid, "walls": [w1, w2], "dot": round(dot, 4)}
        (midpoints if dot < 0 else spur_tips).append(rec)

    # THE QUESTION THE WALL GRAPH CANNOT ANSWER: does a ROOM OUTLINE turn at
    # this vertex?  An outline edge may have `wall: null` (an open side), so a
    # vertex can be degree-2 and collinear among WALLS while the room's ring
    # turns 90 degrees there through an open edge.  Dissolving it and dropping
    # it from the outline would change the outline's SHAPE -- exactly what the
    # room-area receipt is meant to catch.
    outline_turns, outline_spurs, on_open_edge = [], [], []
    coll_ids = {r["vertex"] for r in midpoints}
    for r in doc["rooms"]:
        vs = [e["v"] for e in r["outline"]]
        n = len(vs)
        for i, vid in enumerate(vs):
            if vid not in coll_ids:
                continue
            p_, a, b = V[vid], V[vs[(i - 1) % n]], V[vs[(i + 1) % n]]
            u = (a[0] - p_[0], a[1] - p_[1])
            w_ = (b[0] - p_[0], b[1] - p_[1])
            nu = math.hypot(*u) or 1e-9
            nw = math.hypot(*w_) or 1e-9
            dot = (u[0] * w_[0] + u[1] * w_[1]) / (nu * nw)
            rec = {"room": r["name"], "vertex": vid, "outline_dot": round(dot, 3)}
            if dot > 0.5:
                outline_spurs.append(rec)          # out and back: a spur tip
            elif not (abs(abs(dot) - 1.0) <= math.radians(COLLINEAR_DEG)):
                outline_turns.append(rec)          # the ring TURNS here
            if doc["rooms"] and r["outline"][i].get("wall") is None:
                on_open_edge.append(rec)

    # rooms whose outline repeats a vertex -- D41's degeneracy, as it stands
    repeats = []
    for r in doc["rooms"]:
        seen, dup = set(), set()
        for e in r["outline"]:
            if e["v"] in seen:
                dup.add(e["v"])
            seen.add(e["v"])
        if dup:
            repeats.append({"room": r["name"], "repeated": sorted(dup)})

    # would any dissolve bring two vertices within the weld distance?  A
    # dissolve MOVES NOTHING, so the only way is a merged wall whose two ends
    # are already that close -- i.e. the spur case collapsing to zero length.
    close = []
    for rec in midpoints + spur_tips:
        w1, w2 = rec["walls"]
        ends = set()
        for wid in (w1, w2):
            w = next(x for x in doc["walls"] if x["id"] == wid)
            ends |= {w["v1"], w["v2"]}
        ends.discard(rec["vertex"])
        if len(ends) == 2:
            a, b = (V[e] for e in ends)
            d = math.dist(a, b)
            if d < WELD_TOL:
                close.append({**rec, "merged_span": round(d, 4)})

    return {
        "plan": name,
        "walls": len(doc["walls"]), "vertices": len(doc["vertices"]),
        "degree2_collinear_total": len(midpoints) + len(spur_tips),
        "TRUE_MIDPOINTS (safe to dissolve)": len(midpoints),
        "SPUR_TIPS (same direction -- NOT safe)": len(spur_tips),
        "spur_tip_detail": spur_tips[:6],
        "OUTLINE_TURNS_AT_A_COLLINEAR_VERTEX (unsafe)": outline_turns,
        "OUTLINE_SPUR_AT_A_COLLINEAR_VERTEX (unsafe)": outline_spurs,
        "collinear_vertex_on_an_open_outline_edge": on_open_edge,
        "rooms_with_a_repeated_outline_vertex": repeats,
        "dissolves_that_would_make_a_weld_pair": close,
    }


out = [analyse(load(p), os.path.basename(p)) for p in sys.argv[1:]]
json.dump(out, sys.stdout, indent=1)
sys.stdout.write(chr(10))
