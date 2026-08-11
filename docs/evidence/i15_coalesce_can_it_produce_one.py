#!/usr/bin/env python3
"""CAN `coalesce_outline_corners` PRODUCE AN I15 VIOLATION? -- the confirmation
the load-only ruling is conditional on.

    python docs/evidence/i15_coalesce_can_it_produce_one.py

THE RULING THIS TESTS, and it is conditional on exactly this measurement:

> I15 goes on the LOAD path. The app's own writer cannot produce a violation, so
> a save-side completeness check could never fire -- cannot-fail-by-precondition,
> straight out of this project's own vacuity taxonomy.
>
> One confirmation before that hardens: the walk is not the only writer any more.
> `coalesce_outline_corners` now REMOVES outline corners. Its predicate refuses
> when a wall needs the corner, so it SHOULD be incapable of producing an I15
> violation -- but that is reasoning, and the rule says measure.

TWO QUESTIONS, because "the coalesce produces one" and "one reaches a file" are
different claims and only the second decides where the check belongs:

  A  SCENE-LEVEL. Straight after the coalesce, does any room outline cross a
     wall endpoint it does not name? This is I15's question asked of the live
     scene, by IDENTITY -- outline vertices against wall end vertices.
  B  DOCUMENT-LEVEL. Save that scene and ask I15 of the bytes. This is the one
     that decides the ruling: a state the writer repairs on the way out cannot
     reach a file, so load-side checking would still be sufficient.

If B is non-zero on any plan, the load-only ruling is wrong and I15 belongs on
both sides.

-- CONTROLS --

POSITIVE  the predicate must be able to report a violation at all. It is run
          against `wiscaway2026-08-09R`, KNOWN to carry 2 (read-back 0006), and
          must report exactly those before any conclusion is drawn from a zero.
PRECOND   the coalesce must actually have removed something on each plan, or
          "it produced no violation" is true of a pass that did nothing.
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from d61_normalize_outline_arrow import (                        # noqa: E402
    open_plan, _rooms_of, _walls_of,
)
from outline_invariants_readback import (                        # noqa: E402
    outline_completeness_indexed, read, between,
)

import floorplanner.rooms as R                                   # noqa: E402
import floorplanner.walls as W                                   # noqa: E402
import floorplanner.vertex as V                                  # noqa: E402
from floorplanner.config import SETTINGS                         # noqa: E402

PLANS = ["examples/roundedMultifloor.json", "fixtures/wiscaway2026-08-08.json",
         "examples/symmetricP1.json", "fixtures/wiscaway2026-08-09R.json",
         "examples/planc1.v5.json"]
TOL_PERP = 0.05


def scene_violations(win):
    """I15 asked of the LIVE SCENE, by identity.

    Deliberately NOT via a document: building one would run the walk, which
    repairs the very thing under test. Outline corners hold `Vertex` objects and
    so do wall ends (the Phase 3 model), so the question is asked of those
    objects directly -- `p` is a wall end vertex that is not either endpoint of
    this outline edge, and lies strictly between them.
    """
    step = float(SETTINGS.get("wall_snap_in", 6.0)) or 6.0
    ends = {}
    for w in _walls_of(win):
        for v, p in ((w._v1, w.p1), (w._v2, w.p2)):
            if isinstance(v, V.Vertex):
                ends.setdefault(w.floor, {})[id(v)] = (p.x(), p.y())
    out = []
    for r in _rooms_of(win):
        if getattr(r, "placement_state", "placed") == "floating":
            continue
        ring = [e for e in r.outline if isinstance(getattr(e, "v", None), V.Vertex)]
        n = len(ring)
        if n < 3:
            continue
        near = ends.get(getattr(r, "floor", None), {})
        for i in range(n):
            ea, eb = ring[i], ring[(i + 1) % n]
            a = (ea.p.x(), ea.p.y())
            b = (eb.p.x(), eb.p.y())
            for vid, p in near.items():
                if vid in (id(ea.v), id(eb.v)):
                    continue
                if between(a, p, b, step, TOL_PERP)[0]:
                    out.append({"room": r.name, "at": [round(p[0], 3),
                                                       round(p[1], 3)]})
    return out


def run(path):
    name = os.path.basename(path)
    win = open_plan(os.path.abspath(path))
    W.normalize_walls(win.scene)
    before_scene = len(scene_violations(win))
    rep = R.coalesce_outline_corners(win.scene, dry_run=False)
    after_scene = scene_violations(win)
    tmp = os.path.join(tempfile.gettempdir(), "i15-" + name)
    win.save_path(tmp)
    win.close()
    doc_after = outline_completeness_indexed(read(tmp))
    return {
        "plan": name,
        "PRECONDITION_corners_the_coalesce_removed": rep["removed"],
        "A_scene_violations_BEFORE_the_coalesce": before_scene,
        "A_scene_violations_AFTER_the_coalesce": len(after_scene),
        "A_produced_by_the_coalesce": len(after_scene) - before_scene,
        "B_document_violations_after_saving_that_scene": len(doc_after),
        "sample_scene": after_scene[:4],
        "sample_document": doc_after[:4],
    }


if __name__ == "__main__":
    rows = [run(p) for p in PLANS]
    # POSITIVE CONTROL: the document predicate must report the two known
    # violations on the fixture that carries them, or its zeros mean nothing.
    known = outline_completeness_indexed(
        read(os.path.abspath("fixtures/wiscaway2026-08-09R.json")))
    dead = [r["plan"] for r in rows
            if not r["PRECONDITION_corners_the_coalesce_removed"]]
    prod_a = sum(max(0, r["A_produced_by_the_coalesce"]) for r in rows)
    prod_b = sum(r["B_document_violations_after_saving_that_scene"] for r in rows)
    json.dump({
        "question": ("can the outline coalesce produce an I15 violation -- in "
                     "the scene, and in a file?"),
        "POSITIVE_CONTROL_predicate_sees_the_known_case": {
            "plan": "fixtures/wiscaway2026-08-09R.json (as it arrives)",
            "violations": len(known),
            "expected_from_readback_0006": 2,
            "verdict": "PASS" if len(known) == 2 else "FAIL",
        },
        "PRECONDITION_plans_where_the_coalesce_removed_NOTHING": dead,
        "plans": rows,
        "VERDICT_A_scene": (f"the coalesce PRODUCES {prod_a} scene-level "
                            f"violation(s)" if prod_a else
                            "the coalesce produces NO scene-level violation"),
        "VERDICT_B_document": (
            f"LOAD-ONLY IS WRONG -- {prod_b} violation(s) reached a saved file"
            if prod_b else
            "LOAD-ONLY HOLDS -- no violation reaches a saved file on any plan"),
    }, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
