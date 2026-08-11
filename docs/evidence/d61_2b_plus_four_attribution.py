#!/usr/bin/env python3
"""D61 2b's SPECIFICATION: split the +4 between the two sites.

    python docs/evidence/d61_2b_plus_four_attribution.py

THE QUESTION, and it is not archaeology. A displacing label-drag leaves the plan
**+4 walls / +3 vertices** (`phase6_q4_command_vs_2b.py`). Two very different
things are inside that number:

  DESTINATION   splits the landing legitimately NEEDS -- a room corner resting
                on a plan wall's body makes a junction, and the wall must be cut
                there. Dissolving these would be a bug.
  VACATED       un-fused stubs the departure left -- the run the room used to
                divide is now one straight run that nobody re-merged. THIS is
                what 2b removes.

**Without this split, 2b may dissolve a split a landing corner legitimately
needs**, which is the exact failure mode `wall_ok`'s predicate exists to avoid.

HOW EACH NEW WALL IS ASSIGNED, and the tolerance is the point: the room is moved
by a KNOWN offset, so the vacated boundary and the destination boundary are that
far apart. Each new wall's midpoint is measured to BOTH polygons and assigned to
the nearer. A wall that is not clearly nearer one than the other is reported as
AMBIGUOUS rather than forced into a bucket -- a forced assignment would
manufacture the very number this exists to measure.

THE MOVER IS `_translate`, NAMED. A floating room's walls move by `_translate`,
not by the item's position: `setPos` gives 0,0,0,0,0,0 because it NEVER REACHES
THE PRODUCER. An acceptance must name the mechanism it is measured through.

-- CONTROLS --

PRECOND   the gesture must actually produce the +4, or the split is of nothing.
          Asserted before any assignment is read.
SEPARABLE the offset must exceed the assignment tolerance, or "nearer" is noise.
          Reported as the measured gap between the two polygons.
"""
import json
import math
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath("."))

from PyQt6.QtWidgets import QApplication                  # noqa: E402

app = QApplication([])
import FloorPlanner as fp                                 # noqa: E402
from floorplanner.extract import extract_room, join_room  # noqa: E402

PLAN = "fixtures/wiscaway2026-08-08.json"
ROOM = "WIC"
OFFSET = 240.0           # inches -- see the SEPARABLE control.
#
# 24.0 WAS TRIED FIRST AND ITS CONTROL FAILED: WIC is wider than 24", so the
# vacated and destination polygons still OVERLAP and the measured separation was
# 0.00 in. Two of the six new walls then sat at distance 0.00 from BOTH and were
# correctly reported AMBIGUOUS rather than forced into a bucket. The fix is not a
# looser rule, it is a displacement that actually separates the two sites.


def poly_of(room):
    return [(c.x(), c.y()) for c in (room.corners or [])]


def dist_to_poly(pt, poly):
    """Distance from a point to a polygon's BOUNDARY (not its interior)."""
    best = float("inf")
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        L = math.hypot(bx - ax, by - ay)
        if L < 1e-9:
            continue
        t = max(0.0, min(1.0, ((pt[0] - ax) * (bx - ax)
                               + (pt[1] - ay) * (by - ay)) / (L * L)))
        best = min(best, math.dist(pt, (ax + t * (bx - ax), ay + t * (by - ay))))
    return best


def walls_of(win):
    return [w for w in win.scene.items() if isinstance(w, fp.WallItem)]


def run():
    win = fp.MainWindow()
    win.resize(1400, 1000)
    win.load_path(os.path.abspath(PLAN))
    room = next(r for r in win.scene.items()
                if isinstance(r, fp.RoomItem) and r.name == ROOM)

    before_walls = {id(w) for w in walls_of(win)}
    n_before = len(before_walls)
    vacated = poly_of(room)                      # site A: where it starts
    n_on_vacated_before = sum(
        1 for w in walls_of(win)
        if dist_to_poly(((w.p1.x() + w.p2.x()) / 2.0,
                         (w.p1.y() + w.p2.y()) / 2.0), vacated) < 1.0)

    extract_room(win.scene, room)
    room._translate(OFFSET, 0.0)                 # production's own float mover
    destination = poly_of(room)                  # site B: where it lands
    join_room(win.scene, room)

    after = walls_of(win)
    new = [w for w in after if id(w) not in before_walls]
    gap = min(dist_to_poly(p, destination) for p in vacated) if vacated else 0.0

    # walls sitting ON the vacated boundary, before and after: the direct
    # measure of whether the run the room used to divide re-fused
    def near_vacated(ws):
        return sum(1 for w in ws
                   if dist_to_poly(((w.p1.x() + w.p2.x()) / 2.0,
                                    (w.p1.y() + w.p2.y()) / 2.0), vacated) < 1.0)

    rows, buckets = [], {"VACATED": 0, "DESTINATION": 0, "AMBIGUOUS": 0}
    for w in new:
        mid = ((w.p1.x() + w.p2.x()) / 2.0, (w.p1.y() + w.p2.y()) / 2.0)
        dv = dist_to_poly(mid, vacated)
        dd = dist_to_poly(mid, destination)
        if abs(dv - dd) < OFFSET / 4.0:
            where = "AMBIGUOUS"
        else:
            where = "VACATED" if dv < dd else "DESTINATION"
        buckets[where] += 1
        rows.append({"where": where, "mid": [round(mid[0], 1), round(mid[1], 1)],
                     "to_vacated": round(dv, 2), "to_destination": round(dd, 2),
                     "type": w.wall_type,
                     "length": round(w.length(), 1)})
    n_after = len(after)
    win.close()
    return {
        "plan": PLAN, "room": ROOM, "offset_in": OFFSET, "mover": "_translate",
        "walls_before": n_before, "walls_after": n_after,
        "net_delta": n_after - n_before,
        "PRECONDITION_new_walls": len(new),
        "SEPARABLE_gap_between_the_two_polygons_in": round(gap, 2),
        "attribution": buckets,
        "walls_ON_the_vacated_boundary_after": near_vacated(after),
        "walls_ON_the_vacated_boundary_before": n_on_vacated_before,
        "rows": sorted(rows, key=lambda r: r["where"]),
    }


if __name__ == "__main__":
    res = run()
    b = res["attribution"]
    res["VERDICT"] = (
        "NOTHING TO SPLIT -- the gesture produced no new wall; the "
        "precondition fails and any attribution below would be of nothing"
        if not res["PRECONDITION_new_walls"] else
        f"{b['VACATED']} at the VACATED site (2b's target), "
        f"{b['DESTINATION']} at the DESTINATION (legitimate landing splits), "
        f"{b['AMBIGUOUS']} ambiguous")
    json.dump(res, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
