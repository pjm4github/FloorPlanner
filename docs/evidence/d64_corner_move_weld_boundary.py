#!/usr/bin/env python3
"""DOES A SAVE-SIDE CORNER MOVE CROSS A WELD BOUNDARY? -- the question that
decides whether this is a DATA-INTEGRITY fault or an accuracy defect.

    python docs/evidence/d64_corner_move_weld_boundary.py

THE SENTENCE THAT MAKES IT A DEFECT, and it is the reviewer's:

> 1.5290 inches is not a rounding artifact. `vertex_weld_in` is 0.6 inches. A
> save that moves a corner by more than the weld distance can land it inside
> welding range of a DIFFERENT neighbour, or out of range of the one it belongs
> to -- which turns a projection error into an IDENTITY change, and identity is
> the one thing this model cannot afford to get wrong.

Measured 2026-08-10: the save moves outline corners on two of five plans --
**0** on all three axis-aligned plans, **2 at <= 0.3802"** on the angled
`wiscaway2026-08-09R`, and **2 at up to 1.5290"** on `planc1.v5`
(`d63-tolerance-and-drift.json`). 1.5290 > 0.6, so the move is larger than the
weld radius and the question is no longer hypothetical.

THE TEST IS A SET EQUALITY ON THE WELDS THEMSELVES, not on the corner positions:
take the set of welded groups before the save and after a reload, and compare.

  same set        -> no identity changed hands. An ACCURACY defect; queues
                     normally.
  different set   -> a corner joined or left a weld group across a round trip.
                     DATA INTEGRITY; goes ahead of everything.

WHY THE WELD SET AND NOT THE DISTANCES. A distance-based prediction ("this move
is 1.5", the radius is 0.6, therefore it must cross") is an inference; whether a
weld actually changes depends on what else is within 0.6" of both the old and
the new position, which is a property of the plan, not of the move. So the
welds are ENUMERATED on both sides and compared -- the consequence is measured,
not derived from the magnitude.

-- CONTROLS --

POSITIVE   the instrument must be able to SEE a weld-set change. A corner is
           moved by hand, by more than the weld radius, onto a neighbour, and
           the comparison must report a difference. An instrument that reports
           "no change" without ever having reported one is not evidence.
PRECOND    the moved corners must actually exist on the plan under test -- if
           the save moves nothing, "no weld changed" is vacuous by
           precondition, so the move census is re-run here and asserted.
"""
import json
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from d61_normalize_outline_arrow import open_plan, _walls_of      # noqa: E402
from d63_producer_one import outline_pts, file_pts                # noqa: E402

import floorplanner.walls as W                                    # noqa: E402
from floorplanner.config import SETTINGS                          # noqa: E402

PLANS = ["examples/planc1.v5.json", "fixtures/wiscaway2026-08-09R.json",
         "examples/roundedMultifloor.json", "fixtures/wiscaway2026-08-08.json",
         "examples/symmetricP1.json"]


def weld_radius():
    """Production's own number, not a literal copied into this file."""
    return float(SETTINGS.get("vertex_weld_in", 0.6))


def weld_groups(win):
    """The identity partition, as the scene holds it: which wall ends share a
    `Vertex` OBJECT. That is what "welded" MEANS under the Phase 3 model -- a
    corner is one Vertex the walls and outlines both hold -- so the partition
    is read off identity rather than recomputed from distances.

    Keyed by a canonical description of the members (floor, rounded point,
    which end) so the set survives a save/reload, where object ids do not.
    """
    by_vertex = {}
    for w in _walls_of(win):
        for end, v in (("p1", w._v1), ("p2", w._v2)):
            if v is None:
                continue
            p = w.p1 if end == "p1" else w.p2
            by_vertex.setdefault(id(v), []).append(
                (getattr(w, "floor", None), round(p.x(), 1), round(p.y(), 1)))
    # a GROUP is the multiset of ends sharing one vertex; only groups of 2+
    # say anything about welding, but singletons are kept so that a corner
    # LEAVING a group is visible as a new singleton rather than as nothing
    return {frozenset(sorted(set(m))) for m in by_vertex.values()}


def moved_corners(win, path):
    """Outline corners the save writes at a different coordinate.

    A PROXIMITY THRESHOLD ALONE CANNOT DO THIS, and the first version of this
    file proved it. "Within 2 inches of an existing corner" catches two
    different things:

      A MOVED corner   -- the same corner, recomputed. NO wall end is at it
                          (0 before the wall pass and 0 after) and it lies
                          inside no outline edge.
      A NEW corner     -- a producer-2 insertion that merely happens to be near
                          an existing corner. 3-6 wall ends are at it, and it
                          sits strictly inside an outline edge.

    Measured: `planc1`'s "1.5290 inch move" is the SECOND kind. It is at
    (248.43, 654.0), which `d63-producer-two.json` independently identifies as
    that plan's producer-2 insertion -- 3 wall ends, inside an edge at fraction
    0.562, in Hall / M Bath / Master Suite. It is a corner the save ADDED, not
    one it moved, and the 1.5290 is its distance to an unrelated neighbour.

    So the wall-end count discriminates, and both classes are returned labelled
    rather than one being silently dropped.
    """
    scene = outline_pts(win)
    ends = [(w.p1.x(), w.p1.y()) for w in _walls_of(win)] + \
           [(w.p2.x(), w.p2.y()) for w in _walls_of(win)]
    tmp = os.path.join(tempfile.gettempdir(), "wb-" + os.path.basename(path))
    win.save_path(tmp)
    infile = file_pts(tmp)
    out = []
    for room, pts in infile.items():
        cand = scene.get(room, [])
        if not cand:
            continue
        for q in pts:
            d = min(math.dist(q, s) for s in cand)
            if 1e-9 < d < 2.0:
                n = sum(1 for e in ends if math.dist(q, e) <= 0.05)
                out.append({"room": room, "at": [round(q[0], 3), round(q[1], 3)],
                            "moved_in": round(d, 4), "wall_ends_at_it": n,
                            "KIND": "NEW (producer 2)" if n else "MOVED"})
    return out, tmp


def end_positions(win):
    """Every wall END as (floor, x, y) at full precision -- positions, not
    identities, because identity cannot be tracked across a reload and
    positions can."""
    out = []
    for w in _walls_of(win):
        for p in (w.p1, w.p2):
            out.append((getattr(w, "floor", None), p.x(), p.y()))
    return out


def _within(pos, pt, floor, r):
    return {(round(x, 2), round(y, 2)) for f, x, y in pos
            if f == floor and math.hypot(x - pt[0], y - pt[1]) <= r}


def run(path):
    """THE WHOLE-PARTITION COMPARISON IS CONFOUNDED, and this function records
    that rather than hiding it.

    The literal reading of the question -- "does the set of welds after
    save-and-reload differ from the set before" -- compares a pre-save scene
    against a reloaded one. **The save legitimately re-splits walls** at every
    junction and room corner (`_walls_of` in `design/bridge`), so the reloaded
    scene has MORE wall ends and therefore more vertex groups, whether or not
    any corner moved. Both counts are reported so the size of that confound is
    visible, and `WELD_SET_IDENTICAL` is kept only as the evidence FOR the
    confound -- it is not the verdict.

    THE VERDICT COMES FROM A LOCAL TEST INSTEAD, which is decomposition-
    independent and is the question actually being asked: for each corner the
    save moved, are the wall ends within the weld radius of its NEW position
    the same as those within the weld radius of its OLD one? If they are, no
    corner can have changed which neighbour it welds to.
    """
    name = os.path.basename(path)
    win = open_plan(os.path.abspath(path))
    W.normalize_walls(win.scene)
    before = weld_groups(win)
    pos_before = end_positions(win)
    scene_pts = outline_pts(win)
    moves, tmp = moved_corners(win, path)
    win.load_path(tmp)                      # the round trip, same window
    after = weld_groups(win)
    pos_after = end_positions(win)
    r = weld_radius()

    # for each moved corner: its OLD position is the nearest scene point in
    # that room; its NEW position is what the file holds
    crossings = []
    for m in moves:
        new = (m["at"][0], m["at"][1])
        cand = scene_pts.get(m["room"], [])
        old = min(cand, key=lambda q: math.dist(new, q)) if cand else None
        if old is None:
            continue
        fl = None
        for r_ in _rooms(win):
            if r_.name == m["room"]:
                fl = getattr(r_, "floor", None)
                break
        n_old = _within(pos_before, old, fl, r)
        n_new = _within(pos_after, new, fl, r)
        if n_old != n_new:
            crossings.append({**m, "old": [round(old[0], 3), round(old[1], 3)],
                              "neighbours_at_the_OLD_position": sorted(n_old),
                              "neighbours_at_the_NEW_position": sorted(n_new)})
    win.close()

    only_before = before - after
    only_after = after - before
    genuine = [m for m in moves if m["KIND"] == "MOVED"]
    newc = [m for m in moves if m["KIND"] != "MOVED"]
    big = [m for m in genuine if m["moved_in"] > r]
    return {
        "plan": name,
        "weld_radius_in": r,
        "PRECONDITION_corners_the_save_moved": len(genuine),
        "misclassified_NEW_corners_near_an_existing_one": len(newc),
        "of_which_MOVED_FURTHER_THAN_THE_WELD_RADIUS": len(big),
        "largest_GENUINE_move_in": max((m["moved_in"] for m in genuine),
                                       default=0.0),
        "largest_if_NEW_corners_were_counted_too":
            max((m["moved_in"] for m in moves), default=0.0),
        "moves": sorted(moves, key=lambda m: -m["moved_in"])[:6],
        "LOCAL_TEST_corners_whose_weld_neighbourhood_CHANGED": len(crossings),
        "crossings": crossings[:6],
        # kept as evidence of the confound, NOT as a verdict -- see the
        # docstring. A plan with ZERO moved corners changing here is proof that
        # this comparison measures the re-split, not the move.
        "CONFOUNDED_weld_groups_before": len(before),
        "CONFOUNDED_weld_groups_after": len(after),
        "CONFOUNDED_set_identical": not only_before and not only_after,
    }


def _rooms(win):
    from d61_normalize_outline_arrow import _rooms_of
    return _rooms_of(win)


def positive_control():
    """THE INSTRUMENT MUST BE ABLE TO SEE A WELD-SET CHANGE.

    Three walls; two of them already share a corner. The third's end is moved
    ONTO that corner and the scene re-welded, which must merge it into the
    group -- so `weld_groups` must differ across the change. If it does not,
    every "identical" this file reports is worthless.
    """
    from PyQt6.QtCore import QPointF
    import FloorPlanner as fp
    win = fp.MainWindow()
    win.resize(900, 700)
    sc = win.scene
    a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    b = fp.WallItem(QPointF(120, 0), QPointF(120, 96), "interior")
    c = fp.WallItem(QPointF(240, 240), QPointF(240, 300), "interior")
    for w in (a, b, c):
        sc.addItem(w)
    W.weld_scene(sc)
    W.rebuild_all_walls(sc)
    before = weld_groups(win)
    # move c's end onto the shared corner and re-weld -- production's own op:
    # `detach_end(attr, p)` lands the end at `p` on a new corner, which is
    # exactly "the wall moved here", and `weld_scene` is then what decides
    # whether it joins the group. Nothing here reimplements either step.
    c.detach_end("p1", QPointF(120, 0))
    W.weld_scene(sc)
    W.rebuild_all_walls(sc)
    after = weld_groups(win)
    win.close()
    changed = before != after
    return {
        "statement": ("moving a third wall's end onto an existing shared corner "
                      "and re-welding MUST change the weld partition"),
        "groups_before": len(before), "groups_after": len(after),
        "verdict": "PASS" if changed else
                   "FAIL -- the instrument cannot see a weld change at all",
    }


if __name__ == "__main__":
    ctrl = positive_control()
    rows = [run(p) for p in PLANS]
    any_moves = sum(r["PRECONDITION_corners_the_save_moved"] for r in rows)
    crossed = [r["plan"] for r in rows
               if r["LOCAL_TEST_corners_whose_weld_neighbourhood_CHANGED"]]
    # THE CONFOUND, MEASURED RATHER THAN ARGUED: plans where NO corner moved
    # but the whole-partition comparison still reports a difference. A move
    # cannot be the cause on those, so any difference there is the re-split.
    confound = [r["plan"] for r in rows
                if not r["PRECONDITION_corners_the_save_moved"]
                and not r["CONFOUNDED_set_identical"]]
    json.dump({
        "question": ("does a save-side corner move cross a weld boundary -- "
                     "does it change which neighbours it can weld to?"),
        "POSITIVE_CONTROL": ctrl,
        "PRECONDITION_total_moved_corners_across_all_plans": any_moves,
        "THE_WHOLE_PARTITION_COMPARISON_IS_CONFOUNDED": {
            "plans_with_ZERO_moved_corners_that_still_differ": confound,
            "why": ("the save re-splits walls at every junction and room "
                    "corner, so the reloaded scene has more wall ends and more "
                    "vertex groups whether or not anything moved. A plan that "
                    "moved NOTHING and still differs is proof the comparison "
                    "measures the re-split, not the move"),
            "so": ("the verdict below comes from the LOCAL test, which asks "
                   "only whether a moved corner's weld neighbourhood changed"),
        },
        "plans": rows,
        "VERDICT": (
            "INSTRUMENT NOT VALIDATED -- the control failed; nothing counts"
            if ctrl["verdict"] != "PASS" else
            "VACUOUS -- the save moved no corner anywhere, so nothing was at risk"
            if not any_moves else
            f"DATA INTEGRITY -- a moved corner changed its weld neighbourhood "
            f"on: {', '.join(crossed)}"
            if crossed else
            "ACCURACY ONLY -- corners move, but not one of them changes which "
            "wall ends lie within the weld radius, on any plan measured"),
    }, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
