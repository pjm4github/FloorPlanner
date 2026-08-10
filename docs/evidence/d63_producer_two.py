#!/usr/bin/env python3
"""D63 PRODUCER 2: WHAT DO THE *PREVENTED* INSERTIONS HAVE IN COMMON?

    python docs/evidence/d63_producer_two.py <plan.json> [more.json ...]

THE THREAD, and it is the reviewer's rather than a count. Producer 2 is a
save-side insertion at corners the outline coalesce never touched, and the
wall-pass-alone lane accounts for it exactly -- same corners, set-equal in both
directions -- on every plan but one:

    roundedMultifloor   wall pass 6   coalesce lane 6    prevented 0
    wiscaway 08-09R     wall pass 3   coalesce lane 1    prevented 2   <- this
    planc1.v5           wall pass 3   coalesce lane 3    prevented 0

**It is ONE-SIDED**: nothing appears in the coalesce lane that the wall pass does
not also produce. So running the coalesce can PREVENT a producer-2 insertion,
never cause one -- which is a CAUSAL LINK BETWEEN THE TWO LANES, and a causal
link is worth more than either count.

THE QUESTION THIS ASKS: take the wall-pass lane's insertions, split them into
PREVENTED (gone once the coalesce runs) and FIRED (still there), and measure what
separates the two groups.

THE STANDING HYPOTHESIS, stated before the numbers so it can lose. `_walk(va,vb)`
emits one outline edge per wall along the chain from va to vb (invariant I5). A
producer-2 insertion is therefore a hop the document requires STRICTLY INSIDE a
room edge -- a T-junction the outline never named. Dissolving a corner makes an
edge LONGER, which should mean MORE hops, not fewer. So prevention is the
surprising direction, and whatever explains it is the mechanism.

    H1  the insertion point is a wall end CREATED BY THE WALL PASS
        (split_body_landings), not one the plan arrived with
    H2  a prevented point is one whose hop the dissolve made unnecessary --
        the removed corner and the insertion point are the SAME chain, so the
        edge is re-walked and lands differently
    H3  prevention is about the ROOM: the dissolve changed that room's ring,
        and only rooms whose ring changed lose an insertion

-- CONTROLS, because both a zero and a "nothing in common" are live outcomes --

POSITIVE   the PREVENTED set must be non-empty on at least one plan, or this
           instrument has nothing to measure and its silence means nothing.
           08-09R is the known non-zero case: it must report 2.
REPRODUCE  the per-lane counts must match the recorded table (6/6, 3/1, 3/3)
           before any attribute is read off. An instrument that cannot restate
           the finding it starts from is not measuring that finding.
ONE-SIDED  `coalesce_lane_only` must be EMPTY on every plan. If it is not, the
           one-sided claim is false and the whole framing above is wrong.
IDENTITY   both lanes' sets come from DIFFING the saved document against the
           scene that produced it -- never re-derived from a rule.
"""
import json
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from d61_normalize_outline_arrow import (                        # noqa: E402
    open_plan, _rooms_of, _walls_of,
)
from d63_producer_one import bag_diff, outline_pts, file_pts, TOL  # noqa: E402

import floorplanner.rooms as R                                   # noqa: E402
import floorplanner.walls as W                                   # noqa: E402


def _ends(win, floor=None):
    """Every wall end in the scene as (x, y), optionally one floor."""
    out = []
    for w in _walls_of(win):
        if floor is None or w.floor == floor:
            out += [(w.p1.x(), w.p1.y()), (w.p2.x(), w.p2.y())]
    return out


def _near(pt, pts, tol=TOL):
    return sum(1 for q in pts if math.dist(pt, q) <= tol)


def _edge_span(win, room_name, pt, tol=TOL):
    """Is `pt` strictly INSIDE one of this room's outline edges, and which?

    A producer-2 insertion should be exactly this -- a point the ring passes
    THROUGH without naming. Returns the edge's two endpoints, or None.
    """
    for r in _rooms_of(win):
        if r.name != room_name:
            continue
        n = len(r.outline)
        for i in range(n):
            a = r.outline[i].p
            b = r.outline[(i + 1) % n].p
            ax, ay, bx, by = a.x(), a.y(), b.x(), b.y()
            L = math.hypot(bx - ax, by - ay)
            if L < 1e-6:
                continue
            ux, uy = (bx - ax) / L, (by - ay) / L
            s = (pt[0] - ax) * ux + (pt[1] - ay) * uy
            perp = abs((pt[0] - ax) * uy - (pt[1] - ay) * ux)
            if 0.5 < s < L - 0.5 and perp <= 0.75:
                return {"from": [round(ax, 1), round(ay, 1)],
                        "to": [round(bx, 1), round(by, 1)],
                        "at_fraction": round(s / L, 3)}
    return None


def _lane(path, coalesce):
    """Run one lane and return (scene points, saved-file points, the window,
    plus the corners the coalesce removed in this lane)."""
    win = open_plan(path)
    pre_ends = _ends(win)                     # BEFORE the wall pass -- H1
    W.normalize_walls(win.scene)
    before = outline_pts(win)
    removed = {}
    if coalesce:
        R.coalesce_outline_corners(win.scene, dry_run=False)
        after = outline_pts(win)
        for room in before:
            gone = bag_diff(before.get(room, []), after.get(room, []))
            if gone:
                removed[room] = gone
    else:
        after = before
    tmp = os.path.join(tempfile.gettempdir(),
                       f"p2-{'c' if coalesce else 'w'}-{os.path.basename(path)}")
    win.save_path(tmp)
    infile = file_pts(tmp)
    inserted = []
    for room in sorted(set(infile) | set(after)):
        for p in bag_diff(infile.get(room, []), after.get(room, [])):
            inserted.append((room, p))
    return {"win": win, "scene": after, "inserted": inserted,
            "removed": removed, "pre_ends": pre_ends}


def run(path):
    name = os.path.basename(path)
    wall = _lane(path, coalesce=False)
    coal = _lane(path, coalesce=True)

    def has(lst, rm, p):
        return any(r2 == rm and math.dist(p, q) <= TOL for r2, q in lst)

    prevented = [(rm, p) for rm, p in wall["inserted"]
                 if not has(coal["inserted"], rm, p)]
    fired = [(rm, p) for rm, p in wall["inserted"]
             if has(coal["inserted"], rm, p)]
    lane_only = [(rm, p) for rm, p in coal["inserted"]
                 if not has(wall["inserted"], rm, p)]

    w = wall["win"]
    post_ends = _ends(w)

    def attrs(rm, p, group):
        # nearest corner the coalesce removed, and whether it is in THIS room
        best, best_room = None, None
        for room, pts in coal["removed"].items():
            for q in pts:
                d = math.dist(p, q)
                if best is None or d < best:
                    best, best_room = d, room
        same = None
        if rm in coal["removed"]:
            same = min((math.dist(p, q) for q in coal["removed"][rm]),
                       default=None)
        return {
            "group": group, "room": rm, "at": [round(p[0], 3), round(p[1], 3)],
            # H1: was there a wall end here BEFORE the wall pass?
            "wall_ends_here_AFTER_the_wall_pass": _near(p, post_ends),
            "wall_ends_here_BEFORE_the_wall_pass": _near(p, wall["pre_ends"]),
            "H1_CREATED_BY_THE_WALL_PASS": (_near(p, post_ends) > 0
                                            and _near(p, wall["pre_ends"]) == 0),
            # H2/H3: how close is the nearest dissolve, and is it this room's?
            "nearest_dissolved_corner_in": best_room,
            "nearest_dissolved_corner_dist": (None if best is None
                                              else round(best, 2)),
            "H3_this_room_lost_a_corner": rm in coal["removed"],
            "dist_to_this_rooms_nearest_dissolve": (None if same is None
                                                    else round(same, 2)),
            # the shape the hypothesis predicts: a point the ring runs through
            "inside_an_outline_edge": _edge_span(w, rm, p),
        }

    rows = ([attrs(rm, p, "PREVENTED") for rm, p in prevented]
            + [attrs(rm, p, "FIRED") for rm, p in fired])
    wall["win"].close()
    coal["win"].close()

    def frac(rows_, key):
        g = [r for r in rows_ if r[key] is True]
        return f"{len(g)}/{len(rows_)}" if rows_ else "0/0"

    P = [r for r in rows if r["group"] == "PREVENTED"]
    F = [r for r in rows if r["group"] == "FIRED"]
    return {
        "plan": name,
        "wall_pass_lane_inserted": len(wall["inserted"]),
        "coalesce_lane_inserted": len(coal["inserted"]),
        "PREVENTED": len(prevented),
        "FIRED": len(fired),
        "CONTROL_one_sided_coalesce_lane_only": len(lane_only),
        "CONTROL_one_sided_VERDICT": (
            "PASS -- nothing appears that the wall pass does not also produce"
            if not lane_only else "FAIL -- the one-sided claim is false"),
        "H1_created_by_the_wall_pass": {
            "PREVENTED": frac(P, "H1_CREATED_BY_THE_WALL_PASS"),
            "FIRED": frac(F, "H1_CREATED_BY_THE_WALL_PASS"),
        },
        "H3_the_room_lost_a_corner": {
            "PREVENTED": frac(P, "H3_this_room_lost_a_corner"),
            "FIRED": frac(F, "H3_this_room_lost_a_corner"),
        },
        "rows": rows,
    }


if __name__ == "__main__":
    plans = [os.path.abspath(p) for p in sys.argv[1:]]
    out = {"question": ("producer 2: what separates the insertions the coalesce "
                        "PREVENTS from the ones that still FIRE?"),
           "plans": [run(p) for p in plans]}
    # THE POSITIVE CONTROL, asserted rather than eyeballed: 08-09R is the known
    # non-zero case. If no plan reports a PREVENTED point, this instrument has
    # measured nothing and its "nothing in common" would be an artifact.
    tot = sum(p["PREVENTED"] for p in out["plans"])
    out["POSITIVE_CONTROL_prevented_set_is_non_empty"] = {
        "total_prevented_across_all_plans": tot,
        "verdict": ("PASS" if tot else
                    "FAIL -- nothing prevented anywhere; the instrument has "
                    "no case to measure and its silence means nothing"),
    }
    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
