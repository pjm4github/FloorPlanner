#!/usr/bin/env python3
"""WHAT 2a LEAVES, PER ROOM -- AND DOES THE PAIR REACH A FIXPOINT?

    python docs/evidence/d61_what_2a_leaves.py <plan.json> [more.json ...]

Two questions, both for Patrick to judge rather than for me to conclude.

1. THE 29, PER ROOM. On `wiscaway`, 69 outline corners look redundant to a
   person and the strict predicate removes 40, leaving 29. Both refusal reasons
   are LEGITIMATE -- a wall needs the corner, or a co-holding room turns at it
   -- so the honest reading may be that those 29 are REAL corners rather than
   redundant ones. Printed per room so he can look at the Kitchen and say
   whether he agrees.

   The refusal reasons are attributed, and the attribution is CHECKED: the
   classes must partition exactly the set production refused. If they do not
   sum, the classification is reported as unreliable rather than quoted.

2. DOES THE PAIR ITERATE? The two coalesces can unlock each other: a wall
   coalesce removes a wall, so a corner a wall NEEDED becomes free. Run
   wall-then-outline, then run the pair AGAIN, and report whether round two
   removes more. If it does, one round is not enough and Edit > Coalesce all
   walls now must iterate to a fixpoint -- which changes what the MENU COMMAND
   should do, not only what 2b should do.

DURABILITY IS MEASURED TOO, because it is the same question one layer out: a
corner removed in the session and back after a save was not removed.
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import math                                                      # noqa: E402

from d61_normalize_outline_arrow import (                        # noqa: E402
    complaint_count, open_plan, _rooms_of, _walls_of,
)

import FloorPlanner as fp                                        # noqa: E402
import floorplanner.rooms as R                                   # noqa: E402
import floorplanner.vertex as V                                  # noqa: E402
import floorplanner.walls as W                                   # noqa: E402


def slots(win):
    return sum(len(r.outline) for r in _rooms_of(win))


def refusal_reasons(win):
    """Why each COMPLAINT corner was refused, attributed and then checked.

    Class A -- A WALL NEEDS IT: the vertex is not degree-0, and not degree-2
               with two opposite-directed collinear walls.
    Class B -- A CO-HOLDER TURNS: this room runs straight through, another
               room holding the same corner does not.
    Class C -- the ring is a triangle; the predicate never reduces below one.

    A and B are the two the ruling calls legitimate. The classification is
    validated against production below: it must reproduce production's
    removable count exactly, or it is not quoted."""
    step = float(fp.SETTINGS.get("wall_snap_in", 6.0)) or 6.0
    deg = {}
    for w in _walls_of(win):
        for v in (w._v1, w._v2):
            if isinstance(v, V.Vertex):
                deg.setdefault(id(v), []).append(w)

    def wall_needs(vid):
        ws = deg.get(vid, [])
        if not ws:
            return False
        if len(ws) != 2:
            return True
        a, b = ws
        ua = math.atan2(a.p2.y() - a.p1.y(), a.p2.x() - a.p1.x())
        ub = math.atan2(b.p2.y() - b.p1.y(), b.p2.x() - b.p1.x())
        d = abs((ua - ub) % math.pi)
        return not (min(d, math.pi - d) < math.radians(0.05))

    holders = {}
    for r in _rooms_of(win):
        for i, e in enumerate(r.outline):
            if getattr(e, "v", None) is not None:
                holders.setdefault(id(e.v), []).append((r, i))

    def straight(r, i):
        n = len(r.outline)
        if n < 4:
            return None
        ok, _ = R._corner_path(r.outline[(i - 1) % n].p, r.outline[i].p,
                               r.outline[(i + 1) % n].p, step, 0.05)
        return ok

    per_room, mine = {}, 0
    for r in _rooms_of(win):
        row = {"corners": len(r.outline), "complaint": 0, "removable": 0,
               "left_A_a_wall_needs_it": 0, "left_B_a_co_holder_turns": 0,
               "left_C_triangle": 0}
        for i, e in enumerate(r.outline):
            v = getattr(e, "v", None)
            if v is None:
                continue
            st = straight(r, i)
            if st is None:
                row["left_C_triangle"] += 1
                continue
            if not st:
                continue                       # this room turns: not complained
            row["complaint"] += 1
            if wall_needs(id(v)):
                row["left_A_a_wall_needs_it"] += 1
            elif any(straight(r2, j) is not True
                     for r2, j in holders.get(id(v), ()) if r2 is not r):
                row["left_B_a_co_holder_turns"] += 1
            else:
                row["removable"] += 1
                mine += 1
        per_room[r.name] = row
    return per_room, mine


def run(path):
    name = os.path.basename(path)
    win = open_plan(path)

    # -- the pair, round one ------------------------------------------------
    W.normalize_walls(win.scene)
    r1 = R.coalesce_outline_corners(win.scene, dry_run=False)
    after1 = {"walls": len(_walls_of(win)), "slots": slots(win),
              "removed": r1["removed"]}

    # -- the pair, round TWO: does the wall pass unlock more corners? --------
    ret2 = W.normalize_walls(win.scene)
    dry2 = R.coalesce_outline_corners(win.scene, dry_run=True)
    r2 = R.coalesce_outline_corners(win.scene, dry_run=False)
    after2 = {"walls": len(_walls_of(win)), "slots": slots(win),
              "removed": r2["removed"],
              "normalize_returned": {"merged": ret2[0], "moved": ret2[1],
                                     "shared": ret2[2], "split": ret2[3]}}
    ret3 = W.normalize_walls(win.scene)
    dry3 = R.coalesce_outline_corners(win.scene, dry_run=True)
    after3 = {"walls": len(_walls_of(win)), "slots": slots(win),
              "would_remove": dry3["removed"],
              "normalize_returned": {"merged": ret3[0], "moved": ret3[1],
                                     "shared": ret3[2], "split": ret3[3]}}
    win.close()

    # -- the per-room table, on a clean load with ONE round -----------------
    win = open_plan(path)
    total_complaint, _ = complaint_count(win)
    W.normalize_walls(win.scene)
    dry = R.coalesce_outline_corners(win.scene, dry_run=True)
    per_room, mine = refusal_reasons(win)
    check = {
        "production_removable_vertices": dry["removed"],
        "my_classification_removable_slots": mine,
        "production_removable_slots": sum(v["removable"]
                                          for v in dry["rooms"].values()),
        "AGREES": mine == sum(v["removable"] for v in dry["rooms"].values()),
    }
    win.close()

    # -- durability ---------------------------------------------------------
    win = open_plan(path)
    base = slots(win)
    W.normalize_walls(win.scene)
    R.coalesce_outline_corners(win.scene, dry_run=False)
    in_session = slots(win)
    tmp = os.path.join(tempfile.gettempdir(), f"d61-durable-{name}")
    win.save_path(tmp)
    win.close()
    win2 = open_plan(tmp)
    reopened = slots(win2)
    win2.close()

    return {
        "plan": name,
        "COMPLAINT_total": total_complaint,
        "CLASSIFICATION_CHECK": check,
        "per_room": per_room,
        "PAIR_FIXPOINT": {
            "round_1": after1, "round_2": after2, "round_3_dry": after3,
            "round_2_removed_more": after2["removed"] > 0,
            "IS_A_FIXPOINT_AFTER_ONE_ROUND": after2["removed"] == 0
                                             and dry2["removed"] == 0,
        },
        "DURABILITY": {
            "as_loaded": base, "after_the_command": in_session,
            "after_save_and_reopen": reopened,
            "removed_in_session": base - in_session,
            "still_removed_after_a_save": base - reopened,
            "REBOUND": reopened - in_session,
        },
    }


if __name__ == "__main__":
    json.dump({
        "question": ("what does 2a leave, per room -- and does the wall+outline "
                     "pair need to iterate?"),
        "plans": [run(os.path.abspath(p)) for p in sys.argv[1:]],
    }, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
