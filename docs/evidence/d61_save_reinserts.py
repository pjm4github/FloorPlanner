#!/usr/bin/env python3
"""DOES design_from_scene's WELD RE-INSERT THE CORNERS 2a JUST REMOVED?

    python docs/evidence/d61_save_reinserts.py <plan.json> [more.json ...]

THE HYPOTHESIS UNDER TEST, ruled before implementation: the save-side weld is
already implicated twice -- it bounds D62's harm to the session and it hides
D62 from `check(deep=True)`. The rebound has the same signature (a pure round
trip is stable at 159; a round trip AFTER a coalesce comes back at 126, once,
then settles). If the corners the save puts back are the corners 2a took out,
the rebound is not a separate defect -- it is D62's mechanism seen from a third
side.

**A ZERO OVERLAP REFUTES IT OUTRIGHT**, and that is a live outcome: the save
could equally be inserting corners somewhere else entirely (a body landing, a
canonical split), in which case the rebound has its own producer.

WHAT IS COMPARED
  REMOVED   the corner slots `coalesce_outline_corners` took out of each room
  INSERTED  the corner slots present in the SAVED FILE that were not in the
            scene when it was saved
  OVERLAP   |INSERTED and REMOVED| per room, by coordinate

Both sets are obtained by DIFFING STATES, not by re-implementing a predicate:
removed = scene before the pass minus scene after it; inserted = the file minus
the scene that produced it.

THE CONTROLS, and a zero here is expected in one arm and fatal in the other:
  NEGATIVE  a PURE round trip -- no command at all -- must report 0 inserted.
            If saving alone inserts corners, the comparison below is measuring
            the save's ordinary behaviour and not the coalesce's rebound.
  POSITIVE  on a plan whose rebound is known non-zero (wiscaway 7, rounded 19)
            the instrument must identify exactly that many inserted corners.
            Identification that disagrees with the count is not identification.
"""
import json
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from d61_normalize_outline_arrow import (                        # noqa: E402
    open_plan, _rooms_of,
)

import floorplanner.rooms as R                                   # noqa: E402
import floorplanner.walls as W                                   # noqa: E402

TOL = 0.05


def scene_outlines(win):
    """{room name: [(x, y), ...]} -- the corner slots, in ring order."""
    out = {}
    for r in _rooms_of(win):
        out.setdefault(r.name, []).extend(
            (round(e.p.x(), 3), round(e.p.y(), 3)) for e in r.outline)
    return out


def file_outlines(path):
    """The same, read from the saved v5 document (which is FLAT)."""
    d = json.loads(open(path, encoding="utf-8").read())
    V = {v["id"]: (round(v["x"], 3), round(v["y"], 3))
         for v in d.get("vertices", ())}
    out = {}
    for r in d.get("rooms", ()):
        pts = [V[e["v"]] for e in r.get("outline", ()) if e.get("v") in V]
        out.setdefault(r["name"], []).extend(pts)
    return out


def bag_diff(a, b):
    """Multiset a - b, by coordinate within TOL. Multiset because one ring can
    legitimately visit two corners at the same point (D41's spur)."""
    rest, gone = list(b), []
    for p in a:
        hit = next((q for q in rest if math.dist(p, q) <= TOL), None)
        if hit is None:
            gone.append(p)
        else:
            rest.remove(hit)
    return gone


def overlap(a, b):
    rest, both = list(b), []
    for p in a:
        hit = next((q for q in rest if math.dist(p, q) <= TOL), None)
        if hit is not None:
            rest.remove(hit)
            both.append(p)
    return both


def run(path):
    name = os.path.basename(path)

    # -- NEGATIVE CONTROL: a pure round trip, no command --------------------
    win = open_plan(path)
    plain = scene_outlines(win)
    t0 = os.path.join(tempfile.gettempdir(), f"ri-plain-{name}")
    win.save_path(t0)
    win.close()
    plain_file = file_outlines(t0)
    plain_inserted = sum(len(bag_diff(plain_file.get(k, []), v))
                         for k, v in plain.items())

    # -- LANE B: the WALL pass only, then save ------------------------------
    # This is what separates the two producers. If the save inserts corners
    # after `normalize_walls` alone -- with no outline pass to have removed
    # anything -- then some of the rebound is NOT the coalesce coming undone
    # and the hypothesis does not cover it.
    win = open_plan(path)
    W.normalize_walls(win.scene)
    wall_only = scene_outlines(win)
    tB = os.path.join(tempfile.gettempdir(), f"ri-wall-{name}")
    win.save_path(tB)
    win.close()
    wall_only_inserted = sum(
        len(bag_diff(file_outlines(tB).get(k, []), v))
        for k, v in wall_only.items())

    # -- the measurement ----------------------------------------------------
    win = open_plan(path)
    W.normalize_walls(win.scene)
    before_pass = scene_outlines(win)
    R.coalesce_outline_corners(win.scene, dry_run=False)
    after_pass = scene_outlines(win)
    t1 = os.path.join(tempfile.gettempdir(), f"ri-cmd-{name}")
    win.save_path(t1)
    win.close()
    in_file = file_outlines(t1)

    per_room, tot_rm, tot_ins, tot_ov = {}, 0, 0, 0
    for room in sorted(set(before_pass) | set(in_file)):
        removed = bag_diff(before_pass.get(room, []), after_pass.get(room, []))
        inserted = bag_diff(in_file.get(room, []), after_pass.get(room, []))
        both = overlap(inserted, removed)
        tot_rm += len(removed)
        tot_ins += len(inserted)
        tot_ov += len(both)
        if removed or inserted:
            per_room[room] = {"removed": len(removed),
                              "inserted_by_the_save": len(inserted),
                              "inserted_that_2a_had_REMOVED": len(both),
                              "points": [list(p) for p in both]}

    return {
        "plan": name,
        "NEGATIVE_CONTROL_pure_round_trip": {
            "slots": sum(len(v) for v in plain.values()),
            "inserted_by_the_save": plain_inserted,
            "verdict": "PASS" if plain_inserted == 0 else
                       "FAIL -- the save inserts corners with no command at "
                       "all, so the rebound below is not the coalesce's",
        },
        "slots_after_the_wall_pass": sum(len(v) for v in before_pass.values()),
        "slots_after_the_outline_pass": sum(len(v) for v in after_pass.values()),
        "slots_in_the_saved_file": sum(len(v) for v in in_file.values()),
        "POSITIVE_CONTROL_identification_matches_the_count": {
            "count_delta": (sum(len(v) for v in in_file.values())
                            - sum(len(v) for v in after_pass.values())),
            "identified": tot_ins,
            "verdict": "PASS" if tot_ins == (
                sum(len(v) for v in in_file.values())
                - sum(len(v) for v in after_pass.values())) else
                "FAIL -- identification disagrees with the count",
        },
        "PRODUCER_B_inserted_after_the_WALL_pass_alone": wall_only_inserted,
        "DECOMPOSITION": {
            "claim": ("inserted-after-the-pair minus inserted-after-the-wall-"
                      "pass should equal the overlap: what is left over is "
                      "exactly the coalesce coming undone"),
            "inserted_after_the_pair": tot_ins,
            "inserted_after_the_wall_pass": wall_only_inserted,
            "difference": tot_ins - wall_only_inserted,
            "overlap": tot_ov,
            "HOLDS": tot_ins - wall_only_inserted == tot_ov,
        },
        "REMOVED_by_2a": tot_rm,
        "INSERTED_by_the_save": tot_ins,
        "OVERLAP_inserted_that_2a_had_removed": tot_ov,
        "OVERLAP_share_of_inserted": (round(tot_ov / tot_ins, 3)
                                      if tot_ins else None),
        "per_room": per_room,
        "VERDICT": (
            "no rebound on this plan -- says nothing either way"
            if tot_ins == 0 else
            "CONFIRMED -- every corner the save puts back is one 2a removed"
            if tot_ov == tot_ins else
            "PARTLY CONFIRMED -- some inserted corners are 2a's, some are not"
            if tot_ov else
            "REFUTED -- the save inserts corners 2a never touched"),
    }


if __name__ == "__main__":
    json.dump({
        "question": ("does the save-side weld re-insert the very corners the "
                     "outline coalesce removed?"),
        "plans": [run(os.path.abspath(p)) for p in sys.argv[1:]],
    }, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
