#!/usr/bin/env python3
"""DOES 2b's LEAVE PATH REACH weld_scene -- AND DOES A ROOM MOVE DIVORCE?

    python docs/evidence/d61_leave_path_weld.py <plan.json> [room]

D62 gates D61's stage 2b only if 2b touches it. The deciding question, ruled:
does the path 2b wires into reach the welding that D62 attributes the divorce
to? If not, D62 is independent and 2b proceeds. If so, 2b would spray divorced
corners on every room move.

TWO QUESTIONS, AND THE SECOND IS THE ONE THAT DECIDES
-----------------------------------------------------
  Q1  IS A WELD CALLED during a real label-drag, and in which phase --
      extract (the leave) or join (the return)?
  Q2  DOES THE GESTURE ACTUALLY DIVORCE ANY CORNER? A call is not an effect.
      `share_coincident_ends` running on a two-wall neighbourhood need not
      strand anything; the menu command's 49 came from a plan-wide sweep.

Q2 is measured on the gesture Patrick performs, TODAY, with no 2b in the tree.

WRAPPING, AND WHY IT IS DONE THE HARD WAY
-----------------------------------------
`extract.py:31` does `from floorplanner.walls import ... share_coincident_ends`,
so patching `walls.share_coincident_ends` alone leaves extract's own name bound
to the original -- the exact failure that made stage one's first probe report
"no split at all" during a gesture that provably splits. So every module that
BINDS the name is patched, not just the module that defines it.

THE POSITIVE CONTROL: `normalize_walls` provably welds. With the wrappers
installed it MUST record a weld. A run that records none is a broken wrapper,
not a quiet code path, and its zero on the gesture would mean nothing.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# the arrow probe owns `corner_map` -- the ONE definition of the divorce
# predicate, with its floor scoping and floating exemption. Imported, not
# restated: a second copy is a second definition nobody will maintain.
from d61_normalize_outline_arrow import (                        # noqa: E402
    app, corner_map, fp, open_plan, _rooms_of, _walls_of,
)

from PyQt6.QtCore import QEvent, QPointF, Qt                     # noqa: E402
from PyQt6.QtGui import QMouseEvent                              # noqa: E402
from PyQt6.QtWidgets import QApplication                         # noqa: E402

import floorplanner.extract as X                                 # noqa: E402
import floorplanner.rooms as R                                   # noqa: E402
import floorplanner.walls as W                                   # noqa: E402

PLAN = os.path.abspath(sys.argv[1])
ROOM = sys.argv[2] if len(sys.argv) > 2 else None

WELDS = []          # (name, caller, phase)
PHASE = ["(none)"]


def caller_of(depth=2):
    f = sys._getframe(depth)
    return f"{os.path.basename(f.f_code.co_filename)}:{f.f_lineno} {f.f_code.co_name}"


def wrap(name):
    """Patch every module that BINDS `name`, not just the definer."""
    for mod in (W, X, R):
        orig = getattr(mod, name, None)
        if orig is None or getattr(orig, "_wrapped", False):
            continue

        def make(orig=orig, name=name, mod=mod):
            def w(*a, **k):
                WELDS.append({"fn": name, "via": mod.__name__.split(".")[-1],
                              "caller": caller_of(), "phase": PHASE[0]})
                return orig(*a, **k)
            w._wrapped = True
            return w
        setattr(mod, name, make())


for nm in ("share_coincident_ends", "weld_scene", "weld_wall_ends"):
    wrap(nm)


def divorce(win):
    m = corner_map(win)
    return {"FULL": sum(1 for c in m.values() if c["DIVORCED"]),
            "PARTIAL": sum(1 for c in m.values() if c["PARTLY_DIVORCED"]),
            "outline_corner_objects": len(m)}


def label_drag(win, room, dx, dy):
    """The real gesture: press the room's label, move, release.

    A placed room's label-drag IS extract -> move -> join (P4.2), which is
    exactly the path 2b hooks into."""
    vp = win.view.viewport()
    start = win.view.mapFromScene(room.mapToScene(room._label_rect().center()))

    def send(t, pt, btn, btns):
        QApplication.sendEvent(vp, QMouseEvent(
            t, QPointF(pt), vp.mapToGlobal(QPointF(pt)), btn, btns,
            Qt.KeyboardModifier.NoModifier))
        app.processEvents()

    send(QEvent.Type.MouseButtonPress, start, Qt.MouseButton.LeftButton,
         Qt.MouseButton.LeftButton)
    for k in (1, 2, 3):
        send(QEvent.Type.MouseMove,
             start + type(start)(int(dx * k / 3), int(dy * k / 3)),
             Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton)
    send(QEvent.Type.MouseButtonRelease, start + type(start)(int(dx), int(dy)),
         Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton)


# -- THE POSITIVE CONTROL ----------------------------------------------------
win = open_plan(PLAN)
PHASE[0] = "control: normalize_walls"
before_ctl = len(WELDS)
W.normalize_walls(win.scene)
control = {
    "statement": ("normalize_walls provably welds; with the wrappers installed "
                  "it MUST record one. A zero here means the wrapper is bound "
                  "to the wrong reference, not that the code is quiet"),
    "welds_recorded": len(WELDS) - before_ctl,
    "verdict": "PASS" if len(WELDS) - before_ctl > 0 else "FAIL",
    "calls": WELDS[before_ctl:],
}
win.close()

# -- THE GESTURE -------------------------------------------------------------
# TWO ARMS, AND THE FIRST DRAFT HAD ONLY THE WRONG ONE.
# `fixtures/wiscaway2026-08-08.json` carries `settings.editing.shuffle: true`,
# so on Patrick's own file a label-drag leaves the room FLOATING and join_room
# never runs (P4.3: "leaving shuffle joins nothing automatically"). Measured
# against that state alone, the gesture welds nothing -- which is true of the
# SHUFFLE path and says nothing about the ordinary drag that 2b targets.
# Caught by the ops-ran control, not by the result.
def gesture_arm(shuffle):
    WELDS.clear()
    RAN["extract_room"] = RAN["join_room"] = 0
    win = open_plan(PLAN)
    win.show()
    win.zoom_fit()
    win.set_tool(fp.TOOL_SELECT)
    fp.SETTINGS["shuffle"] = shuffle
    app.processEvents()

    rooms = sorted(_rooms_of(win), key=lambda r: -r.area_sqft)
    target = next((r for r in rooms if r.name == ROOM), None) or next(
        (r for r in rooms
         if getattr(r, "placement_state", "placed") == "placed"), rooms[0])

    loaded = divorce(win)
    walls_before = len(_walls_of(win))
    areas_before = {r.name: round(r.area_sqft, 2) for r in _rooms_of(win)}
    return win, target, loaded, walls_before, areas_before


# the phases are separated so a call can be attributed to the LEAVE or the
# RETURN. `extract_room` / `join_room` are wrapped for the boundary only.
_ex, _jn = X.extract_room, X.join_room


RAN = {"extract_room": 0, "join_room": 0}


def ex(scene, room):
    RAN["extract_room"] += 1
    PHASE[0] = "extract (THE LEAVE)"
    try:
        return _ex(scene, room)
    finally:
        PHASE[0] = "between"


def jn(scene, room):
    RAN["join_room"] += 1
    PHASE[0] = "join (the return)"
    try:
        return _jn(scene, room)
    finally:
        PHASE[0] = "after"


X.extract_room, X.join_room = ex, jn
for mod in (R, W):
    for nm, fn in (("extract_room", ex), ("join_room", jn)):
        if hasattr(mod, nm):
            setattr(mod, nm, fn)

ARMS = {}
for _shuffle in (False, True):
    win, target, loaded, walls_before, areas_before = gesture_arm(_shuffle)
    PHASE[0] = "gesture (outside extract/join)"
    label_drag(win, target, 60, 45)
    app.processEvents()
    after = divorce(win)

    ran_ok = bool(RAN["extract_room"] and RAN["join_room"])
    arm = {
        "shuffle": _shuffle,
        "room_moved": target.name,
        "room_state_after": getattr(target, "placement_state", "?"),
        # SECOND CONTROL: a zero weld count means nothing unless the gesture
        # actually ran the ops. The first draft reported "does not weld at
        # all" without checking that extract AND join had been entered -- and
        # under shuffle, join never is.
        "CONTROL_2_ops_actually_ran": dict(RAN),
        "CONTROL_2_verdict": ("PASS" if ran_ok else
                              "N/A -- join_room does not run under shuffle, "
                              "which is P4.3's design, not a probe fault"),
        "welds": list(WELDS),
        "weld_count_by_phase": {
            p: sum(1 for w in WELDS if w["phase"] == p)
            for p in sorted({w["phase"] for w in WELDS})} or {"(none)": 0},
        "LEAVE_PATH_WELDS": any(w["phase"] == "extract (THE LEAVE)"
                                for w in WELDS),
        "GESTURE_WELDS_AT_ALL": bool(WELDS),
        "divorced_before": loaded,
        "divorced_after": after,
        "DELTA_full": after["FULL"] - loaded["FULL"],
        "DELTA_partial": after["PARTIAL"] - loaded["PARTIAL"],
        "walls_before": walls_before,
        "walls_after": len(_walls_of(win)),
        "areas_changed": sorted(
            n for n, a in areas_before.items()
            if abs(a - round(next((x.area_sqft for x in _rooms_of(win)
                                   if x.name == n), a), 2)) > 0.01),
    }
    arm["verdict"] = (
        "nothing below is evidence -- the weld wrapper is not bound"
        if control["verdict"] == "FAIL" else
        "A ROOM MOVE DIVORCES CORNERS -- D62 is on 2b's path"
        if arm["DELTA_full"] > 0 else
        "the gesture WELDS but divorces nothing"
        if WELDS else
        "the gesture does not weld at all")
    ARMS["shuffle_ON (as the fixture loads)" if _shuffle
         else "shuffle_OFF (the ordinary drag 2b targets)"] = arm
    win.close()

# -- A WALK, because one sample is thin evidence for a ZERO -------------------
# Six moves to new spots, shuffle off: 2b's own acceptance scenario. If a room
# move divorces at all, six of them should show it.
WELDS.clear()
RAN["extract_room"] = RAN["join_room"] = 0
win = open_plan(PLAN)
win.show()
win.zoom_fit()
win.set_tool(fp.TOOL_SELECT)
fp.SETTINGS["shuffle"] = False
app.processEvents()
rooms = sorted(_rooms_of(win), key=lambda r: -r.area_sqft)
walker = next((r for r in rooms if r.name == ROOM), None) or next(
    (r for r in rooms
     if getattr(r, "placement_state", "placed") == "placed"), rooms[0])
walk = [{"step": 0, **divorce(win), "walls": len(_walls_of(win))}]
for i, (dx, dy) in enumerate([(40, 30), (35, -25), (-30, 40),
                              (45, 20), (-40, -30), (25, 35)], start=1):
    PHASE[0] = f"walk step {i}"
    label_drag(win, walker, dx, dy)
    app.processEvents()
    walk.append({"step": i, **divorce(win), "walls": len(_walls_of(win)),
                 "state": getattr(walker, "placement_state", "?")})
walk_result = {
    "room": walker.name,
    "joins_run": RAN["join_room"],
    "welds_in_the_LEAVE_phase": sum(
        1 for w in WELDS if w["phase"] == "extract (THE LEAVE)"),
    "welds_total": len(WELDS),
    "per_step": walk,
    "FULL_divorce_ever_above_zero": any(s["FULL"] for s in walk),
}
win.close()

json.dump({
    "plan": os.path.basename(PLAN),
    "question": ("does 2b's leave path reach the welding D62 attributes the "
                 "divorce to, and does a room move divorce anything?"),
    "WALK_six_moves_shuffle_off": walk_result,
    "CONTROL_1_wrapper_bound": control,
    "NOTE_on_the_fixture": ("fixtures/wiscaway2026-08-08.json carries "
                            "settings.editing.shuffle: true, so as it loads a "
                            "label-drag leaves the room FLOATING and join_room "
                            "never runs. Both states are measured; the "
                            "shuffle_OFF arm is the one that answers the "
                            "question"),
    "arms": ARMS,
}, sys.stdout, indent=1)
sys.stdout.write(chr(10))
