#!/usr/bin/env python3
"""D62: DOES A DIVORCED CORNER SURVIVE A SAVE AND RELOAD?

    python docs/evidence/d61_divorce_persistence.py <plan.json> [more.json ...]

The obvious account of D62 is that the state is RUNTIME-ONLY: `design_from_scene`
welds on the way out, so the emitted document has one vertex per point whatever
the scene holds, and a reload rebuilds shared corners. If that account holds,
the harm window is bounded by the session.

**TESTED, NOT ADOPTED.** Apply the command, save, reload, count.

  count == 0   the state cannot outlive the session; D62 drops in severity
  count  > 0   it persists; D62 rises above 2b

AND THE PAIRING WORTH STATING: the very mechanism that would make the state
harmless -- the weld in `design_from_scene` -- is also the mechanism that makes
it invisible to `check(deep=True)`. One mechanism, two effects, opposite signs.

CONTROLS
  1. the counter must read NON-ZERO in the scene straight after the command,
     or the reload's zero is a zero about nothing.
  2. the round trip must PRESERVE the plan -- same room count and same areas.
     A reload that lost the geometry would also read 0 divorced, for the wrong
     reason entirely.
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from d61_normalize_outline_arrow import (                        # noqa: E402
    app, corner_map, open_plan, _rooms_of, _walls_of,
)

import floorplanner.rooms as R                                   # noqa: E402
import floorplanner.walls as W                                   # noqa: E402


def divorce(win):
    m = corner_map(win)
    return {"FULL": sum(1 for c in m.values() if c["DIVORCED"]),
            "PARTIAL": sum(1 for c in m.values() if c["PARTLY_DIVORCED"]),
            "corners": len(m)}


def shape(win):
    return {"rooms": len(_rooms_of(win)), "walls": len(_walls_of(win)),
            "outline_slots": sum(len(r.outline) for r in _rooms_of(win)),
            "areas": {r.name: round(r.area_sqft, 2) for r in _rooms_of(win)}}


def doc_facts(path):
    """What the FILE says: does any room outline name a vertex no wall names?

    The scene-level question asked of the document. If the weld on the way out
    collapses the divorce, every outline vertex is also a wall vertex here.

    THE v5 DOCUMENT IS FLAT: `vertices`, `walls` and `rooms` are TOP-LEVEL and
    `levels` is only the storey roster. The first version of this reader walked
    `levels[*].walls`, found nothing, and reported a confident
    `outline_vertices_no_wall_names: 0` off zero walls and zero rooms. The
    counts below are carried precisely so that zero can never be read again
    without the denominators beside it."""
    d = json.loads(open(path, encoding="utf-8").read())
    wall_vs = set()
    for w in d.get("walls", ()):
        wall_vs.add(w["v1"])
        wall_vs.add(w["v2"])
    slots = orphan = 0
    for r in d.get("rooms", ()):
        for e in r.get("outline", ()):
            if e.get("v") is None:
                continue
            slots += 1
            if e["v"] not in wall_vs:
                orphan += 1
    return {"levels": len(d.get("levels", ())),
            "vertices": len(d.get("vertices", ())),
            "walls": len(d.get("walls", ())),
            "rooms": len(d.get("rooms", ())),
            "outline_slots": slots,
            "outline_vertices_no_wall_names": orphan,
            "READABLE": bool(d.get("walls") and d.get("rooms"))}


def run(path, outline_too=False):
    """`outline_too=False` runs the WALL half only; True runs what Edit >
    Coalesce all walls now actually does -- wall pass AND outline pass. The
    second is the one that asks whether 2a's fix reaches Patrick's next
    session."""
    name = os.path.basename(path)
    tag = "full" if outline_too else "wallonly"
    tmp = os.path.join(tempfile.gettempdir(), f"d62-{tag}-{name}")

    win = open_plan(path)
    as_loaded = divorce(win)
    loaded_shape = shape(win)
    W.normalize_walls(win.scene)
    app.processEvents()
    if outline_too:
        R.coalesce_outline_corners(win.scene, dry_run=False)
        app.processEvents()
    after_cmd = divorce(win)
    before_shape = shape(win)
    win.save_path(tmp)
    win.close()

    saved = doc_facts(tmp)

    win2 = open_plan(tmp)
    after_reload = divorce(win2)
    after_shape = shape(win2)
    win2.close()

    control_1 = after_cmd["FULL"] > 0
    control_2 = (before_shape["rooms"] == after_shape["rooms"]
                 and before_shape["areas"] == after_shape["areas"])
    return {
        "plan": name,
        "ran": "normalize_walls + coalesce_outline_corners" if outline_too
               else "normalize_walls only",
        "CONTROL_3_saved_file_was_READABLE": {
            "walls": saved["walls"], "rooms": saved["rooms"],
            "verdict": "PASS" if saved["READABLE"] else
                       "FAIL -- the reader found no walls/rooms, so its "
                       "orphan count is a zero about nothing",
        },
        "OUTLINE_SLOTS_the_number_Patrick_sees": {
            "as_loaded": loaded_shape["outline_slots"],
            "after_the_command": before_shape["outline_slots"],
            "in_the_saved_file": saved["outline_slots"],
            "after_reload": after_shape["outline_slots"],
            "SURVIVES_THE_ROUND_TRIP":
                before_shape["outline_slots"] == after_shape["outline_slots"],
        },
        "CONTROL_1_scene_divorced_before_save": {
            "value": after_cmd["FULL"],
            "verdict": "PASS" if control_1 else
                       "FAIL -- nothing to persist, so the reload says nothing",
        },
        "CONTROL_2_round_trip_preserved_the_plan": {
            "rooms": [before_shape["rooms"], after_shape["rooms"]],
            "areas_identical": before_shape["areas"] == after_shape["areas"],
            "verdict": "PASS" if control_2 else
                       "FAIL -- a lossy reload reads 0 for the wrong reason",
        },
        "divorced_as_loaded": as_loaded,
        "divorced_after_the_command": after_cmd,
        "divorced_after_save_and_reload": after_reload,
        "the_saved_FILE": saved,
        "walls_before_save": before_shape["walls"],
        "walls_after_reload": after_shape["walls"],
        "VERDICT": (
            "not reportable -- a control failed"
            if not (control_1 and control_2) else
            "RUNTIME ONLY -- the divorce does not survive a save/reload"
            if after_reload["FULL"] == 0 else
            "IT PERSISTS -- the divorce survives a save/reload"),
    }


if __name__ == "__main__":
    json.dump({
        "question": ("does a divorced outline corner survive a save and "
                     "reload -- and does 2a's outline fix survive one?"),
        "wall_pass_only": [run(os.path.abspath(p)) for p in sys.argv[1:]],
        "the_whole_menu_command": [run(os.path.abspath(p), outline_too=True)
                                   for p in sys.argv[1:]],
    }, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
