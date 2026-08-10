#!/usr/bin/env python3
"""D63: WHY DOES `roundedMultifloor` REBOUND 6 OF 6, WHEN THE OTHER THREE PLANS
DO NOT?

    python docs/evidence/d63_rounded_rebound.py <plan.json> [more.json ...]

THE STATE THIS STARTS FROM, and it is a table in the record, not an impression:

    plan                    removed  durable  rebound
    wiscaway2026-08-08      33       33       0
    wiscaway2026-08-09R      94       93       1
    symmetricP1              4        4       0
    roundedMultifloor        6        0       6   <- this

`d63_producer_one.py` says all 6 have a wall END at them, and 0 of the 6 that
stayed removed do -- the same predicate that closed the other three plans.  So
the corrected `wall_ok` should have REFUSED all six and did not.  **The question
is not "what re-inserts them" -- producer 1 answers that.  It is why the
production predicate says yes to a corner it says no to elsewhere.**

THE CANDIDATE, and it is the one thing this plan has that the others do not:
`wall_ok` is FLOOR-SCOPED, and the floor it scopes to comes from the FIRST
holder of the vertex:

    for r, i in hs:
        pt, fl = (q.x(), q.y()), getattr(r, "floor", None)
        break                                   # <- rooms.py, the arbitrary one

If one `Vertex` object is held by rooms on TWO levels, `fl` is whichever room
the dict happened to yield first, and `_ends_at(pt, fl)` then counts the ends on
one storey while `deg[vid]` counts the walls holding the object on BOTH.  The
two sides of `_ends_at(pt, floor) != len(ws)` would be measuring different
scenes.  On a single-level plan that is unobservable, which is exactly why three
plans passed.

WHAT IS MEASURED, per rebounding corner: its holders WITH THEIR FLOORS, the
walls holding the vertex object with their floors, the wall ends at the point
BROKEN DOWN BY FLOOR, and the two numbers `wall_ok` actually compared.

-- CONTROLS, because a zero and a "no cross-floor sharing" are both live --

POSITIVE   the same dump for the corners that STAYED removed on this plan.  If
           they look identical, cross-floor sharing is true of every corner here
           and discriminates nothing.
NEGATIVE   the same question asked of `wiscaway2026-08-08`, which rebounds 0.
           A single-level plan must show no cross-floor holder anywhere; if it
           does, the probe is reading `floor` wrong rather than finding a fault.
IDENTITY   the rebounding set is obtained by DIFFING the saved document against
           the scene, as in `d63_producer_one.py` -- not re-derived from a rule.
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
import floorplanner.vertex as V                                  # noqa: E402


def _ends_by_floor(win, pt, tol=0.05):
    """Wall ends AT this point, broken down by the floor of the wall."""
    out = {}
    for w in _walls_of(win):
        for q in (w.p1, w.p2):
            if math.dist((q.x(), q.y()), pt) <= tol:
                out[w.floor] = out.get(w.floor, 0) + 1
    return out


def _holders_at(win, pt, tol=0.05):
    """Every outline slot naming a point here: room, floor, and the id() of the
    Vertex it holds -- so cross-floor SHARING (one object) is distinguishable
    from mere coincidence (two objects at one coordinate)."""
    out = []
    for r in _rooms_of(win):
        for i, e in enumerate(r.outline):
            v = getattr(e, "v", None)
            if not isinstance(v, V.Vertex):
                continue
            if math.dist((e.p.x(), e.p.y()), pt) <= tol:
                out.append({"room": r.name, "floor": getattr(r, "floor", None),
                            "slot": i, "vid": id(v)})
    return out


def _walls_holding(win, vid):
    out = []
    for w in _walls_of(win):
        for a, v in (("p1", w._v1), ("p2", w._v2)):
            if isinstance(v, V.Vertex) and id(v) == vid:
                out.append({"floor": w.floor, "end": a, "type": w.wall_type,
                            "deg_from": [round(w.p1.x(), 1), round(w.p1.y(), 1)],
                            "to": [round(w.p2.x(), 1), round(w.p2.y(), 1)]})
    return out


def dump(win, pt):
    """Everything `wall_ok` had to work with at this point, plus what it
    compared. The two comparands are reported separately BECAUSE the hypothesis
    is that they are scoped differently."""
    hs = _holders_at(win, pt)
    vids = sorted({h["vid"] for h in hs})
    floors = sorted({h["floor"] for h in hs}, key=str)
    ends = _ends_by_floor(win, pt)
    # the floor `wall_ok` would have used: the FIRST holder in the dict order
    # production sees. Reproduced here rather than assumed -- production
    # iterates its own `holders` map, so this is the honest approximation and
    # is labelled as such.
    fl_first = hs[0]["floor"] if hs else None
    holding = {v: _walls_holding(win, v) for v in vids}
    return {
        "at": list(pt),
        "holder_slots": hs,
        "distinct_vertex_objects_here": len(vids),
        "holder_floors": floors,
        "CROSS_FLOOR_HOLDERS": len(floors) > 1,
        "SHARED_ACROSS_FLOORS_one_object_two_storeys": (
            len(floors) > 1 and len(vids) == 1),
        "wall_ends_at_this_point_BY_FLOOR": ends,
        "wall_ends_TOTAL": sum(ends.values()),
        "walls_HOLDING_each_object": holding,
        "what_wall_ok_compared": {
            "floor_it_scoped_to (first holder)": fl_first,
            "_ends_at(pt, floor)": ends.get(fl_first, 0),
            "len(deg[vid])  walls holding the object": {
                v: len(holding[v]) for v in vids},
        },
    }


def _classify(path):
    """THE THREE-WAY SPLIT, PER (ROOM, POINT) -- which is the whole point.

    The shipped durability measure is a COUNT: `slots()` before the save against
    `slots()` after it (`test_a_coalesced_corner_stays_gone_across_a_save`).  A
    count cannot tell "the corner I removed came back" from "a different corner
    was added somewhere else", and those are producer 1 and producer 2 -- the
    two the record already says are separate investigations.  So classify by
    IDENTITY:

      DURABLE    removed by the coalesce, absent from the saved document
      REBOUND    removed by the coalesce, back in the saved document  (prod 1)
      INSERTED   never removed, present in the saved document anyway   (prod 2)

    Pairing is per ROOM as well as per point: a corner vacated in one room and
    added in another is not the same corner coming back, and a whole-plan point
    bag would score it as one.
    """
    name = os.path.basename(path)
    win = open_plan(path)
    W.normalize_walls(win.scene)
    before = outline_pts(win)
    rep = R.coalesce_outline_corners(win.scene, dry_run=False)
    after = outline_pts(win)
    tmp = os.path.join(tempfile.gettempdir(), f"reb-{name}")
    win.save_path(tmp)
    infile = file_pts(tmp)
    win.close()

    # THE CONTROL LANE: the same plan taken to a save with the WALL pass only,
    # no coalesce. Whatever the document gains here is producer 2 by
    # construction -- the coalesce removed nothing for it to put back.
    w2 = open_plan(path)
    W.normalize_walls(w2.scene)
    base = outline_pts(w2)
    tmp2 = os.path.join(tempfile.gettempdir(), f"reb-wallonly-{name}")
    w2.save_path(tmp2)
    wallonly = file_pts(tmp2)
    w2.close()

    removed, rebound, inserted, wall_pass_inserted = [], [], [], []
    for room in sorted(set(before) | set(infile) | set(wallonly)):
        gone = bag_diff(before.get(room, []), after.get(room, []))
        extra = bag_diff(infile.get(room, []), after.get(room, []))
        removed += [(room, p) for p in gone]
        rest = list(gone)
        for p in extra:
            hit = next((q for q in rest if math.dist(p, q) <= TOL), None)
            if hit is None:
                inserted.append((room, p))       # producer 2: never removed
            else:
                rest.remove(hit)
                rebound.append((room, p))        # producer 1: came back
        wall_pass_inserted += [
            (room, p) for p in bag_diff(wallonly.get(room, []),
                                        base.get(room, []))]
    durable = [(rm, p) for rm, p in removed
               if not any(rm == r2 and math.dist(p, q) <= TOL
                          for r2, q in rebound)]
    return {"plan": name, "win_removed": rep["removed"], "removed": removed,
            "durable": durable, "rebound": rebound, "inserted": inserted,
            "wall_pass_inserted": wall_pass_inserted}


def _same_set(a, b):
    """Do two (room, point) lists name the same corners? Reported as the two
    one-sided differences, so a mismatch says WHICH way it missed rather than
    just `False`."""
    def missing(x, y):
        return [{"room": rm, "at": list(p)} for rm, p in x
                if not any(rm == r2 and math.dist(p, q) <= TOL
                           for r2, q in y)]
    only_a, only_b = missing(a, b), missing(b, a)
    return {"EQUAL": not only_a and not only_b,
            "in_the_coalesce_lane_only": only_a,
            "in_the_wall_pass_lane_only": only_b}


def run(path):
    name = os.path.basename(path)
    cl = _classify(path)
    rein = [p for _, p in cl["rebound"]]
    stayed = [p for _, p in cl["durable"]]

    # THE DUMP IS TAKEN ON A FRESH LOAD, at the state `wall_ok` actually saw:
    # after normalize_walls and BEFORE the coalesce applied. Asking it of the
    # classified window would question a scene the corners have already been
    # removed from -- there would be no holders left to report.
    win = open_plan(path)
    W.normalize_walls(win.scene)
    rein_d = [dump(win, p) for p in rein]
    stay_d = [dump(win, p) for p in stayed]
    win.close()

    n_cross_rein = sum(1 for d in rein_d if d["CROSS_FLOOR_HOLDERS"])
    n_cross_stay = sum(1 for d in stay_d if d["CROSS_FLOOR_HOLDERS"])
    n_shared_rein = sum(1 for d in rein_d
                        if d["SHARED_ACROSS_FLOORS_one_object_two_storeys"])
    return {
        "plan": name,
        "coalesce_removed_vertices": cl["win_removed"],
        "coalesce_removed_SLOTS": len(cl["removed"]),
        "DURABLE_slots": len(stayed),
        "REBOUND_slots_producer_1": len(rein),
        "INSERTED_slots_producer_2_never_removed": len(cl["inserted"]),
        "CONTROL_inserted_by_the_WALL_PASS_ALONE": len(cl["wall_pass_inserted"]),
        # SAME COUNT IS NOT SAME CORNERS. If producer 2 is the wall pass, the
        # two lanes must insert the SAME (room, point) pairs -- six and six
        # could otherwise be two different sixes.
        "PRODUCER_2_IS_THE_WALL_PASS_same_corners_not_just_same_count":
            _same_set(cl["inserted"], cl["wall_pass_inserted"]),
        "THE_COUNT_MEASURE_the_shipped_test_uses": {
            "note": ("slots after the coalesce vs slots in the saved file -- "
                     "what `test_a_coalesced_corner_stays_gone_across_a_save` "
                     "asserts. It cannot separate the two producers."),
            "net_slot_change_across_the_save": (len(rein)
                                                + len(cl["inserted"])),
            "would_read_durable_as": (len(cl["removed"]) - len(rein)
                                      - len(cl["inserted"])),
        },
        "inserted_detail_producer_2": [
            {"room": rm, "at": list(p)} for rm, p in cl["inserted"]],
        "POSITIVE_CONTROL_cross_floor_discriminates": {
            "claim": ("if cross-floor holders explain the rebound, the corners "
                      "that STAYED removed must mostly NOT have them"),
            "rebound_with_cross_floor_holders": f"{n_cross_rein}/{len(rein_d)}",
            "stayed_with_cross_floor_holders": f"{n_cross_stay}/{len(stay_d)}",
            "rebound_sharing_ONE_object_across_storeys": (
                f"{n_shared_rein}/{len(rein_d)}"),
            "verdict": ("no rebound on this plan" if not rein_d else
                        "PASS" if n_cross_rein == len(rein_d) and not n_cross_stay
                        else "FAIL -- does not discriminate"
                        if n_cross_rein <= n_cross_stay else "PARTIAL"),
        },
        "REBOUND_detail": rein_d,
        "STAYED_detail": stay_d[:6],
    }


if __name__ == "__main__":
    json.dump({
        "question": ("why does the corrected wall_ok say YES to six corners on "
                     "roundedMultifloor that the save then puts straight back?"),
        "plans": [run(os.path.abspath(p)) for p in sys.argv[1:]],
    }, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
