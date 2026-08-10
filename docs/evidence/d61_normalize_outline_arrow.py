#!/usr/bin/env python3
"""D61 ITEM 2: DOES `normalize_walls` MANUFACTURE REDUNDANT OUTLINE CORNERS?

    python docs/evidence/d61_normalize_outline_arrow.py <plan.json> [more.json ...]

THE QUESTION IS THE DIRECTION OF THE ARROW. `a604d40` measured that a wall
coalesce leaves the outlines untouched (159 corners / 69 redundant, before and
after, on Patrick's plan). That is a statement about a plan that had ALREADY
been through one. It does not answer whether running `normalize_walls` on a
plan that has never had one RAISES the redundant-corner count -- and if it
does, D61 has a SECOND PRODUCER and stage 2b (the leave path) closes only one
of them.

Reported three ways -- before, after, delta -- on every plan given.

-- THE POSITIVE CONTROL, AND IT IS NAMED HERE RATHER THAN IN A COMMIT MESSAGE --

A zero from this instrument is the interesting answer, which is exactly when a
zero must not be believed on trust. The control is two vertices already known
to be non-zero, from `a604d40`'s own measurement of `fixtures/wiscaway...json`:

    (1062, 684)  wall-degree 2 -> 0 across normalize_walls, still named by
                 Dining and KITCHEN
    (750, 684)   wall-degree 2 -> 0 across normalize_walls, still named by
                 Foyer, GREAT RM and HALL

CONTROL A (the reviewer's wording, and the one a zero rests on): after
`normalize_walls`, this instrument MUST report both of those as outline corners
at wall-degree 0 whose holders are those rooms. An instrument that cannot see
the two orphaned corners it was built from cannot be believed when it reports
none anywhere else.

CONTROL B (strictly more than was asked): whether those two are also in the set
the PRODUCTION predicate would dissolve. B may legitimately fail while A passes
-- "no wall needs this corner" and "every holder runs straight through it" are
different questions, and the second is the one `coalesce_outline_corners` asks.
Both verdicts are printed. Only A gates belief in a zero.

-- WHAT IS MEASURED, AND BY WHAT --

The counts come from the PRODUCTION predicate, `rooms.coalesce_outline_corners`
with `dry_run=True`. Nothing here restates it.

The IDENTITY of the dissolvable set is not exposed by that report, so it is
obtained the only way that does not restate the predicate either: on a separate
load, the report is APPLIED and the outline corner map diffed before and after.
The set that disappears is the set production chose, by construction.

-- THE BOUNDARY OF "BEFORE" --

`planio.load_data` calls `merge_all(scene)` (`planio.py:204`), gated by
`auto_coalesce`, which defaults True. So a plan AS LOADED has already had a
plan-wide collinear MERGE run over it, and "before" in this report means
"as the user sees it on opening the file", not "as the bytes on disk describe".
The three sub-passes are therefore also run and measured SEPARATELY (pass B) so
that whatever moves can be attributed to merge, to weld or to split rather than
to "normalize_walls" as a lump.

WHAT IT DOES NOT ANSWER: whether any of this is reachable from a user gesture.
That is a run question and this is a plan-state measurement.
"""
import json
import math
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from PyQt6.QtWidgets import QApplication              # noqa: E402

app = QApplication([])
import FloorPlanner as fp                             # noqa: E402
import floorplanner.rooms as R                        # noqa: E402
import floorplanner.vertex as V                       # noqa: E402
import floorplanner.walls as W                        # noqa: E402

CONTROL_PLAN = "wiscaway2026-08-08.json"
CONTROL_POINTS = [
    {"at": [1062.0, 684.0], "holders": ["Dining", "KITCHEN"]},
    {"at": [750.0, 684.0], "holders": ["Foyer", "GREAT RM", "HALL"]},
]
CONTROL_TOL = 0.75          # inches; a weld may nudge a corner


# ---------------------------------------------------------------- measurement
def _rooms_of(win):
    return [i for i in win.scene.items() if isinstance(i, fp.RoomItem)]


def _walls_of(win):
    return [i for i in win.scene.items() if isinstance(i, fp.WallItem)]


POINT_TOL = 0.05        # inches; a wall END is AT an outline corner


def corner_map(win):
    """Every vertex an outline NAMES: its point, its holders, and its wall
    degree measured TWO WAYS.

    Keyed by id(), which is stable across the wall passes because those do not
    touch outlines -- the very claim under test, so the map also reports any
    outline corner that CHANGED identity.

    WHY TWO DEGREES, AND IT IS NOT PEDANTRY. `by_id` asks "does a wall hold
    THIS VERY Vertex OBJECT"; `by_point` asks "does any wall end LIE HERE".
    Under the Phase 3 model -- a corner is one `Vertex` that the walls and the
    outlines both hold -- those two must agree. Where they do not, the wall and
    the outline have been divorced: geometry at the same coordinate, identity
    no longer shared, so a later wall drag moves one and not the other. A
    single-degree instrument reports that state as "no wall needs this corner"
    and is wrong about which fault it is looking at."""
    deg_id, ends = {}, {}
    for w in _walls_of(win):
        for v, p in ((w._v1, w.p1), (w._v2, w.p2)):
            if isinstance(v, V.Vertex):
                deg_id[id(v)] = deg_id.get(id(v), 0) + 1
            # SCOPED BY FLOOR, like every geometry path in this codebase. An
            # unfiltered by-point test counts a wall end on the storey above
            # as though it were at this corner, which on a two-level plan is
            # not a small error -- and this probe made it before the
            # self-test's non-zero baseline drew attention to the question.
            ends.setdefault(w.floor, []).append((p.x(), p.y()))
    out = {}
    for r in _rooms_of(win):
        # a FLOATING room has deliberately broken its sharing with the plan
        # (P4.2), so its coincidences are not faults -- the same exemption
        # `scene_identity_report` makes, and for the same reason.
        floating = getattr(r, "placement_state", "placed") == "floating"
        for e in r.outline:
            v = getattr(e, "v", None)
            if not isinstance(v, V.Vertex):
                continue
            rec = out.setdefault(id(v), {"at": None, "holders": [],
                                         "floors": set(), "floating": False,
                                         "wall_degree": deg_id.get(id(v), 0)})
            rec["at"] = [round(v.x, 3), round(v.y, 3)]
            rec["holders"].append(r.name)
            rec["floors"].add(getattr(r, "floor", None))
            rec["floating"] = rec["floating"] or floating
    for rec in out.values():
        rec["holders"].sort()
        near = [p for f in rec.pop("floors") for p in ends.get(f, ())]
        rec["wall_degree_by_point"] = sum(
            1 for x, y in near if math.dist((x, y), rec["at"]) <= POINT_TOL)
        # FULL divorce: no wall holds this object at all, though wall ends are
        # here. PARTIAL: some do and some do not -- the corner is half carried.
        # The partial case was invisible to the first draft of this detector,
        # and its own self-test is what found that: detaching ONE of the two
        # walls on a corner left the count at 0, because the other still held
        # the object. A detector that only fires when EVERY wall has left is
        # not measuring "are the wall and the outline still one corner".
        rec["DIVORCED"] = (not rec["floating"] and rec["wall_degree"] == 0
                           and rec["wall_degree_by_point"] > 0)
        rec["PARTLY_DIVORCED"] = (not rec["floating"]
                                  and 0 < rec["wall_degree"]
                                  < rec["wall_degree_by_point"])
    return out


def complaint_count(win):
    """THE USER'S COMPLAINT, COUNTED: outline corner slots whose OWN ring runs
    straight through -- "a straight run carrying more than a dozen handles".

    Deliberately the LOOSE measure: no wall test, and no agreement between the
    rooms sharing a corner. It is what a person sees when they look at one room
    edge, and it is NOT what `coalesce_outline_corners` removes. Kept apart
    from that count on purpose -- `a604d40` quotes 69 for this and 28/40 for
    the strict one, and reconciling them is the whole point of measuring both
    with one instrument.

    Uses production's own corner test (`rooms._corner_path`), not a copy."""
    step = float(fp.SETTINGS.get("wall_snap_in", 6.0)) or 6.0
    per_room, total = {}, 0
    for r in _rooms_of(win):
        n, c = len(r.outline), 0
        for i in range(n):
            if n < 4:
                break
            straight, _ = R._corner_path(r.outline[(i - 1) % n].p,
                                         r.outline[i].p,
                                         r.outline[(i + 1) % n].p, step, 0.05)
            c += bool(straight)
        per_room[r.name] = c
        total += c
    return total, per_room


def census(win, label):
    """The counts, from the production predicate. Nothing here restates it."""
    rooms = _rooms_of(win)
    walls = _walls_of(win)
    rep = R.coalesce_outline_corners(win.scene, dry_run=True)
    slots = sum(pr["removable"] for pr in rep["rooms"].values())
    cmap = corner_map(win)
    complaint, complaint_rooms = complaint_count(win)

    inc = {}
    for w in walls:
        for v in (w._v1, w._v2):
            if isinstance(v, V.Vertex):
                inc.setdefault(id(v), []).append(w)
    deg2 = coll = 0
    for ws in inc.values():
        if len(ws) != 2:
            continue
        deg2 += 1
        a, b = ws
        ua = math.atan2(a.p2.y() - a.p1.y(), a.p2.x() - a.p1.x())
        ub = math.atan2(b.p2.y() - b.p1.y(), b.p2.x() - b.p1.x())
        d = abs((ua - ub) % math.pi)
        if min(d, math.pi - d) < math.radians(0.5):
            coll += 1

    return {
        "label": label,
        "walls": len(walls),
        "rooms": len(rooms),
        "outline_corner_slots": sum(len(r.outline) for r in rooms),
        "outline_corner_objects": len(cmap),
        "COMPLAINT_ring_runs_straight_slots": complaint,
        "REDUNDANT_vertices": rep["removed"],
        "REDUNDANT_slots": slots,
        "D48_scene_identity_extra_vertices": _d48(win),
        "orphaned_named_corners": sum(1 for c in cmap.values()
                                      if c["wall_degree"] == 0),
        "TRULY_orphaned_no_wall_end_here": sum(
            1 for c in cmap.values() if c["wall_degree_by_point"] == 0),
        "DIVORCED_wall_here_but_not_this_object": sum(
            1 for c in cmap.values() if c["DIVORCED"]),
        "PARTLY_DIVORCED_some_walls_left_the_object": sum(
            1 for c in cmap.values() if c["PARTLY_DIVORCED"]),
        "wall_degree2": deg2,
        "wall_degree2_collinear": coll,
        "total_area_sqft": round(sum(r.area_sqft for r in rooms), 2),
        "_map": cmap,
        "_per_room": {k: v["removable"] for k, v in rep["rooms"].items()},
        "_complaint_rooms": complaint_rooms,
    }


def _d48(win):
    """What the SHIPPED scene-identity report (D48/G2) says about this scene.

    Recorded beside the divorce count because the two do not measure the same
    thing: `scene_identity_report` compares WALL ENDS to WALL ENDS. An outline
    corner holding a `Vertex` no wall holds is outside its question entirely,
    so its zero is not evidence that the scene's corners are shared."""
    try:
        from floorplanner.design.bridge import scene_identity_report
        return scene_identity_report(win).get("extra_vertices")
    except Exception as exc:                              # noqa: BLE001
        return f"unavailable: {type(exc).__name__}"


def strip(c):
    return {k: v for k, v in c.items() if not k.startswith("_")}


def open_plan(path):
    win = fp.MainWindow()
    win.resize(1400, 1000)
    win.load_path(path)
    app.processEvents()
    return win


DELTA_KEYS = ["walls", "outline_corner_slots", "outline_corner_objects",
              "COMPLAINT_ring_runs_straight_slots",
              "REDUNDANT_vertices", "REDUNDANT_slots",
              "D48_scene_identity_extra_vertices",
              "orphaned_named_corners", "TRULY_orphaned_no_wall_end_here",
              "DIVORCED_wall_here_but_not_this_object",
              "PARTLY_DIVORCED_some_walls_left_the_object",
              "wall_degree2_collinear", "total_area_sqft"]


def delta(a, b):
    out = {}
    for k in DELTA_KEYS:
        x, y = a[k], b[k]
        out[k] = (round(y - x, 2) if isinstance(x, (int, float))
                  and isinstance(y, (int, float)) else f"{x} -> {y}")
    return out


# ------------------------------------------------------------------- the runs
def run_plan(path):
    name = os.path.basename(path)
    res = {"plan": name}

    # -- PASS A: the arrow, plus idempotence -------------------------------
    win = open_plan(path)
    before = census(win, "as loaded (merge_all has already run -- planio:204)")
    ret1 = W.normalize_walls(win.scene)
    after = census(win, "after normalize_walls")
    ret2 = W.normalize_walls(win.scene)
    again = census(win, "after a SECOND normalize_walls")

    # did any outline corner change IDENTITY across the wall passes?
    churn = sorted(set(after["_map"]) ^ set(before["_map"]))
    res["A_arrow"] = {
        "normalize_walls_returned": {"merged": ret1[0], "moved": ret1[1],
                                     "shared": ret1[2], "split": ret1[3]},
        "second_run_returned": {"merged": ret2[0], "moved": ret2[1],
                                "shared": ret2[2], "split": ret2[3]},
        "BEFORE": strip(before),
        "AFTER": strip(after),
        "DELTA": delta(before, after),
        "AFTER_A_SECOND_RUN": strip(again),
        "DELTA_of_second_run": delta(after, again),
        "outline_corner_objects_that_changed_identity": len(churn),
        "per_room_removable_BEFORE": before["_per_room"],
        "per_room_removable_AFTER": after["_per_room"],
        "per_room_COMPLAINT_BEFORE": before["_complaint_rooms"],
        "per_room_COMPLAINT_AFTER": after["_complaint_rooms"],
        "per_room_outline_corners": {r.name: len(r.outline)
                                     for r in _rooms_of(win)},
    }

    # WHICH corners became redundant that were not? Needs the identified set,
    # which pass C produces. Here, record only what the counts say.
    win.close()

    # -- PASS B: attribution to a sub-pass ---------------------------------
    win = open_plan(path)
    steps = [("as loaded", None)]
    b0 = census(win, "as loaded")
    merged = W.merge_collinear_scene(win.scene)
    b1 = census(win, "after merge_collinear_scene")
    moved, shared = W.weld_scene(win.scene)
    b2 = census(win, "after weld_scene")
    split = W.split_body_landings(win.scene)
    b3 = census(win, "after split_body_landings")
    steps = [
        {"pass": "merge_collinear_scene", "returned": {"merged": merged},
         "DELTA": delta(b0, b1)},
        {"pass": "weld_scene", "returned": {"moved": moved, "shared": shared},
         "DELTA": delta(b1, b2)},
        {"pass": "split_body_landings", "returned": {"split": split},
         "DELTA": delta(b2, b3)},
    ]
    res["B_attribution"] = {"start": strip(b0), "steps": steps,
                            "end": strip(b3)}
    win.close()

    # -- PASS C: identity of the dissolvable set, and the control ----------
    win = open_plan(path)
    pre_map = corner_map(win)
    W.normalize_walls(win.scene)
    post_map = corner_map(win)
    rep_dry = R.coalesce_outline_corners(win.scene, dry_run=True)
    slots_before = sum(len(r.outline) for r in _rooms_of(win))
    applied = R.coalesce_outline_corners(win.scene, dry_run=False)
    slots_after = sum(len(r.outline) for r in _rooms_of(win))
    left_map = corner_map(win)
    gone = [dict(post_map[k], vid=k) for k in post_map if k not in left_map]

    # ITEM 1: do the dissolved VERTICES account for the vacated SLOTS?
    hist = {}
    for g in gone:
        hist[len(g["holders"])] = hist.get(len(g["holders"]), 0) + 1
    # ITEM 1's other half: is the applied result a FIXPOINT, or does dissolving
    # one corner make its neighbour newly redundant?  If the second dry run is
    # non-zero the preview UNDER-REPORTS and must iterate before it is shown.
    second = R.coalesce_outline_corners(win.scene, dry_run=True)

    # the aux identification is validated against the production count, not
    # trusted: if these disagree the identification below is not evidence.
    res["C_identified"] = {
        "production_dry_run_removed": rep_dry["removed"],
        "identified_by_applying_and_diffing": len(gone),
        "AGREES": rep_dry["removed"] == len(gone),
        "slots_vacated": sum(len(g["holders"]) for g in gone),
        # `coalesce_outline_corners` returns EARLY when nothing is doomed, so
        # `areas_after` is absent rather than equal. Reading that as "areas
        # changed" is a false alarm this probe raised on planc1 before the
        # early return was checked.
        "areas_unchanged": (True if not gone else
                            applied.get("areas_before")
                            == applied.get("areas_after")),
        "nothing_to_dissolve": not gone,
        "ITEM_1_slots_before": slots_before,
        "ITEM_1_slots_after": slots_after,
        "ITEM_1_slots_vacated": slots_before - slots_after,
        "ITEM_1_holders_per_dissolved_vertex": dict(sorted(hist.items())),
        "ITEM_1_sum_of_holder_counts": sum(len(g["holders"]) for g in gone),
        "ITEM_1_RESIDUE": (slots_before - slots_after)
                          - sum(len(g["holders"]) for g in gone),
        "ITEM_1_second_dry_run_removed": second["removed"],
        "ITEM_1_IS_A_FIXPOINT": second["removed"] == 0,
        "dissolved": sorted(gone, key=lambda g: (g["at"][1], g["at"][0])),
    }

    # -- the control -------------------------------------------------------
    if name == CONTROL_PLAN:
        checks = []
        for cp in CONTROL_POINTS:
            def find(m, want=cp["at"]):        # bind, do not close over `cp`
                return [dict(v, vid=k) for k, v in m.items()
                        if math.dist(v["at"], want) <= CONTROL_TOL]
            pre = find(pre_map)
            post = find(post_map)
            a_ok = bool(post) and all(p["wall_degree"] == 0 for p in post) and \
                any(sorted(set(p["holders"])) == sorted(cp["holders"])
                    for p in post)
            b_ok = any(math.dist(g["at"], cp["at"]) <= CONTROL_TOL
                       for g in gone)
            checks.append({
                "at": cp["at"], "expected_holders": cp["holders"],
                "BEFORE_normalize": pre, "AFTER_normalize": post,
                "CONTROL_A_orphaned_and_still_named": "PASS" if a_ok else "FAIL",
                "CONTROL_B_in_the_dissolvable_set": "PASS" if b_ok else "FAIL",
            })
        res["CONTROL"] = {
            "statement": ("after normalize_walls, both known corners must be "
                          "reported at wall-degree 0 with their named holders; "
                          "CONTROL A gates belief in any zero this instrument "
                          "reports on any plan"),
            "A_verdict": ("PASS" if all(c["CONTROL_A_orphaned_and_still_named"]
                                        == "PASS" for c in checks) else "FAIL"),
            "B_verdict": ("PASS" if all(c["CONTROL_B_in_the_dissolvable_set"]
                                        == "PASS" for c in checks) else "FAIL"),
            "checks": checks,
        }
    win.close()
    return res


def divorce_selftest(path):
    """POSITIVE CONTROL FOR THE DIVORCE DETECTOR, which is a number this probe
    INVENTED and which therefore has no prior instance to lean on.

    The five plans all read 0 as loaded, which is a negative control and proves
    only that the detector is quiet. So one is constructed: rebind a wall's end
    to a FRESH `Vertex` at the same coordinate -- production's own detach, the
    documented meaning of `Vertex.at` -- while the room outline keeps the old
    object. That is a divorce by construction, and the detector must see it.

    Reported as 0 -> N. A detector that cannot make this transition is not to
    be believed when it reports 62."""
    def read(win, label):
        c = census(win, label)
        return {"FULL": c["DIVORCED_wall_here_but_not_this_object"],
                "PARTIAL": c["PARTLY_DIVORCED_some_walls_left_the_object"]}

    steps = {}

    # -- arm 1: detach ONE of the walls on a corner two walls hold -> PARTIAL
    win = open_plan(path)
    steps["as_loaded"] = read(win, "as loaded")
    one = None
    for r in _rooms_of(win):
        for e in r.outline:
            v = getattr(e, "v", None)
            if not isinstance(v, V.Vertex):
                continue
            held = [(w, a) for w in _walls_of(win) for a in ("p1", "p2")
                    if w.end_vertex(a) is v]
            if len(held) < 2:
                continue
            w, a = held[0]
            w.set_end_vertex(a, V.Vertex.at(v.point()))
            one = {"room": r.name, "at": [round(v.x, 3), round(v.y, 3)],
                   "walls_on_this_corner": len(held), "detached": 1,
                   "_rest": held[1:]}
            break
        if one:
            break
    steps["after_detaching_ONE_of_them"] = read(win, "one detached")

    # -- arm 2: detach the REST of them -> FULL
    for w, a in (one or {}).get("_rest", []):
        w.set_end_vertex(a, V.Vertex.at(w.end_vertex(a).point()))
    steps["after_detaching_ALL_of_them"] = read(win, "all detached")
    win.close()
    if one:
        one.pop("_rest", None)

    quiet = steps["as_loaded"]
    part = steps["after_detaching_ONE_of_them"]
    full = steps["after_detaching_ALL_of_them"]
    ok = (part["PARTIAL"] == quiet["PARTIAL"] + 1
          and full["FULL"] == quiet["FULL"] + 1)
    return {
        "statement": ("THE CONTROL IS THE TRANSITION, NOT THE BASELINE: "
                      "detaching ONE wall from a shared corner must raise "
                      "PARTIAL by exactly 1, and then detaching the rest must "
                      "raise FULL by exactly 1 -- using production's own "
                      "`Vertex.at` + `set_end_vertex`"),
        "why_not_a_zero_baseline": ("the first version demanded 0 on the "
                                    "loaded plan and FAILED at PARTIAL=2. "
                                    "That 2 is real and pre-existing, so the "
                                    "assertion was UNSATISFIABLE on this "
                                    "fixture -- a control must test that the "
                                    "instrument MOVES, not that the world is "
                                    "empty"),
        "why_two_arms": ("the first draft detached one of two walls and read "
                         "0 -- the detector only saw FULL divorce, so a "
                         "half-carried corner was invisible to it. The "
                         "self-test found that, not the result"),
        "detached": one, "steps": steps,
        "verdict": "PASS" if ok else "FAIL",
    }


# Importable: `corner_map` is the ONE definition of the divorce predicate, and
# `d61_leave_path_weld.py` reads it from here rather than restating it. The
# QApplication above is created at import, which is what any Qt probe needs
# anyway; only the measurement below is guarded.
if __name__ == "__main__":
    plans = [os.path.abspath(p) for p in sys.argv[1:]]
    out = {
        "question": ("does normalize_walls RAISE the redundant-outline-corner "
                     "count -- i.e. is it a SECOND PRODUCER for D61?"),
        "control_named_at": ("see CONTROL in the wiscaway entry, and the "
                             "docstring"),
        "DIVORCE_DETECTOR_SELFTEST": (divorce_selftest(plans[0]) if plans
                                      else None),
        "plans": [run_plan(p) for p in plans],
    }
    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
