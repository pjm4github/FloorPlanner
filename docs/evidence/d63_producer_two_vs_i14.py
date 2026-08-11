#!/usr/bin/env python3
"""IS PRODUCER 2'S "ALREADY-THERE" HALF A PRODUCER AT ALL, OR AN I14 REPAIR?

    python docs/evidence/d63_producer_two_vs_i14.py

THE REVIEWER'S QUESTION, and it reframes the target if it comes out yes:

> If the stored outline genuinely violates I5 -- a room edge crossing a
> T-junction it never named -- then the save's insertion is a REPAIR, and
> counting it as a rebound was a category error on our side, not a fault in the
> code. `wiscaway2026-08-09R` fails I14 three times with exactly this shape:
> "w87 end v92 lies on w85, not a vertex of it, unwelded T". Are the points
> where producer 2's already-there insertions land THE SAME POINTS as the I14
> unwelded-T failures?

**Producer 2 splits by the ORIGIN of the wall end it lands on**
(`d63-producer-two.json`):

    the WALL PASS created the end          6   planc1 3/3, rounded 2/6, 08-09R 1/1
    the end was ALREADY THERE, unnamed     4   rounded 4/6

The already-there half is the one under test. If those four points are the I14
unwelded-T failures, the save is repairing a document that arrived broken, and
the target moves upstream to whatever wrote an outline across an unnamed T.

THE TEST IS A SET EQUALITY IN BOTH DIRECTIONS -- the same discipline that
separated `rounded`'s six from its supposed rebound. Reported as the two
one-sided differences, so a mismatch says WHICH way it missed.

-- CONTROLS --

PRECOND   the already-there set must be non-empty, and I14 must actually fire
          somewhere, or the comparison is vacuous by precondition and its
          "no coincidence" would mean nothing. Both are asserted.
SOURCE    the I14 failures come from PRODUCTION's own `check()` -- the message
          strings are parsed for the vertex ids, and the ids resolved through
          the document's own vertex table. Nothing here restates the invariant.
"""
import json
import math
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from d61_normalize_outline_arrow import open_plan                 # noqa: E402
from d63_producer_one import outline_pts, file_pts, bag_diff       # noqa: E402

import floorplanner.walls as W                                    # noqa: E402
from floorplanner.design.validate import check                    # noqa: E402

PLANS = ["examples/roundedMultifloor.json", "fixtures/wiscaway2026-08-09R.json",
         "examples/planc1.v5.json", "fixtures/wiscaway2026-08-08.json",
         "examples/symmetricP1.json"]


def i14_points(doc):
    """Every point an I14 message names, resolved through the document's own
    vertex table. Two shapes are emitted by `validate`:

        I14 wall <w> end <vid> lies on wall <w2> ...      -- the unwelded T
        I14 vertices <a> and <b> are within ...           -- the near pair
    """
    V = {}
    for lv in doc.get("levels", ()):
        for v in lv.get("vertices", ()):
            V[v["id"]] = (v["x"], v["y"])
    for v in doc.get("vertices", ()):
        V[v["id"]] = (v["x"], v["y"])
    out = []
    for msg in check(doc, deep=True):
        if not msg.startswith("I14"):
            continue
        kind = "unwelded_T" if " lies on wall " in msg else "near_pair"
        for vid in re.findall(r"\bv\d+\b|\b\d+\b", msg):
            if vid in V:
                out.append({"kind": kind, "vid": vid,
                            "at": [round(V[vid][0], 3), round(V[vid][1], 3)],
                            "msg": msg})
    return out


def run(path):
    name = os.path.basename(path)
    win = open_plan(os.path.abspath(path))
    W.normalize_walls(win.scene)
    scene = outline_pts(win)
    ends_before = [(w.p1.x(), w.p1.y()) for w in W_walls(win)] + \
                  [(w.p2.x(), w.p2.y()) for w in W_walls(win)]
    tmp = os.path.join(tempfile.gettempdir(), "i14-" + name)
    win.save_path(tmp)
    infile = file_pts(tmp)
    # I14 IS ASKED OF THE FILE AS IT ARRIVES, NOT OF THE RE-SAVED COPY, and the
    # first version of this file got that wrong. The save welds and re-splits,
    # so an I14 the fixture arrived with is already repaired in `tmp` -- asking
    # there reported 2 near-pairs and ZERO unwelded Ts on a fixture whose
    # README names three. Read the original bytes.
    doc = json.loads(open(os.path.abspath(path), encoding="utf-8").read())
    win.close()

    # producer 2 = in the saved file, not in the scene. Split by whether a wall
    # end was ALREADY at that point before the save (the already-there half).
    already, created = [], []
    for room in sorted(set(infile)):
        for p in bag_diff(infile.get(room, []), scene.get(room, [])):
            n = sum(1 for e in ends_before if math.dist(p, e) <= 0.05)
            (already if n else created).append((room, p))

    i14 = i14_points(doc)
    i14_pts = [tuple(r["at"]) for r in i14]
    tees = [tuple(r["at"]) for r in i14 if r["kind"] == "unwelded_T"]

    def missing(xs, ys):
        return [list(p) for p in xs
                if not any(math.dist(p, q) <= 0.75 for q in ys)]

    ap = [p for _, p in already]
    only_p2 = missing(ap, i14_pts)
    only_i14 = missing(i14_pts, ap)
    return {
        "plan": name,
        "producer2_ALREADY_THERE": len(already),
        "producer2_created_by_the_wall_pass": len(created),
        "I14_failures": len(i14),
        "I14_of_which_unwelded_T": len(tees),
        "already_there_points": [list(p) for _, p in already][:8],
        "I14_points": [r["at"] for r in i14][:8],
        "SET_EQUALITY": {
            "in_producer2_only": only_p2,
            "in_I14_only": only_i14,
            "EQUAL": not only_p2 and not only_i14,
        },
        "VERDICT": ("no already-there insertions on this plan"
                    if not already else
                    "COINCIDE -- the save is REPAIRING an I14 the file arrived "
                    "with; not a producer"
                    if not only_p2 and not only_i14 else
                    "DISJOINT -- producer 2's already-there half is NOT the "
                    "I14 failures" if len(only_p2) == len(ap) else
                    "PARTIAL -- some coincide and some do not"),
    }


def W_walls(win):
    from d61_normalize_outline_arrow import _walls_of
    return _walls_of(win)


if __name__ == "__main__":
    rows = [run(p) for p in PLANS]
    tot_already = sum(r["producer2_ALREADY_THERE"] for r in rows)
    tot_i14 = sum(r["I14_failures"] for r in rows)
    json.dump({
        "question": ("are producer 2's already-there insertions the same points "
                     "as the I14 unwelded-T failures?"),
        "PRECONDITION": {
            "already_there_insertions_total": tot_already,
            "I14_failures_total": tot_i14,
            "verdict": ("PASS" if tot_already and tot_i14 else
                        "VACUOUS -- one side is empty, so 'no coincidence' "
                        "would say nothing"),
        },
        "plans": rows,
    }, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
