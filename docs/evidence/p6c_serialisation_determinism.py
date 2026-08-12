#!/usr/bin/env python3
"""P6.c's GATING MEASUREMENT: is serialisation DETERMINISTIC?

    python docs/evidence/p6c_serialisation_determinism.py

THE RULING P6.c IMPLEMENTS:

  * the STACK INDEX drives the dirty marker
  * an AUTHORITATIVE serialise-and-compare runs only at CLOSE, QUIT and OPEN
  * the CLEAN direction is trusted without a check, because being wrong there is
    cheap

**AND THE COMPARISON IS ONLY WORTH ANYTHING IF THE SERIALISER IS
DETERMINISTIC.** If the same plan serialises to different bytes twice, then
`snapshot() != saved_state` is true of a plan nobody touched, and the
authoritative check is a TAUTOLOGY SITTING WHERE NOBODY LOOKS -- it would report
"dirty" at every close, the prompt would become noise, and the noise would be
indistinguishable from the check working.

So this is measured FIRST, before the marker is wired to anything.

WHAT IS MEASURED, three ways, because "the same plan" has three meanings here:

  A  SAME WINDOW, TWICE     snapshot() called twice with no edit between
  B  RELOAD                 save, load that file, save again -- the round trip
                            the close/quit/open check actually performs
  C  TWO WINDOWS            the same file opened into two MainWindows

**A is the one the dirty comparison rests on**; B and C are recorded because a
serialiser can be stable within one process and unstable across a reload, and
the check at OPEN spans exactly that boundary.

-- CONTROLS --

POSITIVE   the comparator must be able to see a difference at all: an edit is
           made and the same comparison must report NOT identical. Without it,
           "identical" is the report of an instrument that cannot tell.
BYTES      compared as the JSON TEXT the file would carry, not as dicts --
           dict equality would hide a key-ORDER difference, and key order is
           exactly what a non-deterministic serialiser gets wrong.
"""
import json
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath("."))

from PyQt6.QtCore import QPointF                          # noqa: E402
from PyQt6.QtWidgets import QApplication                  # noqa: E402

app = QApplication([])
import FloorPlanner as fp                                 # noqa: E402

PLANS = ["examples/roundedMultifloor.json", "fixtures/wiscaway2026-08-08.json",
         "examples/symmetricP1.json", "examples/planc1.v5.json",
         "examples/farmplaceBIGmultifloor.json"]


def text(doc):
    """The JSON TEXT, not the dict: dict equality would hide a key-order
    difference, and key order is what a non-deterministic serialiser gets
    wrong."""
    return json.dumps(doc, indent=1)


def open_win(path):
    win = fp.MainWindow()
    win.resize(1200, 900)
    win.load_path(os.path.abspath(path))
    return win


def run(path):
    name = os.path.basename(path)
    win = open_win(path)

    # A -- same window, twice, no edit between
    a1, a2 = text(win.design_document()), text(win.design_document())

    # B -- the round trip the close/quit/open check performs
    tmp = os.path.join(tempfile.gettempdir(), "det-" + name)
    win.save_path(tmp)
    b1 = open(tmp, encoding="utf-8").read()
    win2 = open_win(tmp)
    tmp2 = os.path.join(tempfile.gettempdir(), "det2-" + name)
    win2.save_path(tmp2)
    b2 = open(tmp2, encoding="utf-8").read()

    # C -- the same file in two windows
    win3 = open_win(path)
    c1, c2 = text(win.design_document()), text(win3.design_document())

    # POSITIVE CONTROL -- the comparator must be able to see a difference
    before = text(win3.design_document())
    win3.scene.addItem(fp.WallItem(QPointF(3000, 3000), QPointF(3120, 3000),
                                   "interior"))
    fp.rebuild_all_walls(win3.scene)
    moved = text(win3.design_document())

    for w in (win, win2, win3):
        w.close()
    return {
        "plan": name,
        "A_same_window_twice": a1 == a2,
        "B_across_a_reload": b1 == b2,
        "C_two_windows_same_file": c1 == c2,
        "CONTROL_an_edit_is_visible": before != moved,
        "bytes": len(a1),
    }


if __name__ == "__main__":
    rows = [run(p) for p in PLANS]
    ok_a = all(r["A_same_window_twice"] for r in rows)
    ok_b = all(r["B_across_a_reload"] for r in rows)
    ok_c = all(r["C_two_windows_same_file"] for r in rows)
    ctrl = all(r["CONTROL_an_edit_is_visible"] for r in rows)
    json.dump({
        "question": ("is serialisation deterministic enough for a "
                     "serialise-and-compare dirty check to mean anything?"),
        "plans": rows,
        "POSITIVE_CONTROL_the_comparator_sees_an_edit": ctrl,
        "VERDICT": (
            "INSTRUMENT NOT VALIDATED -- the comparator cannot see an edit, so "
            "every 'identical' below is worthless"
            if not ctrl else
            "DETERMINISTIC -- A, B and C all identical on every plan; a "
            "serialise-and-compare dirty check is meaningful"
            if ok_a and ok_b and ok_c else
            f"NON-DETERMINISTIC -- same-window={ok_a} reload={ok_b} "
            f"two-windows={ok_c}. A comparison-based dirty check would report "
            f"dirty on an untouched plan wherever a False appears"),
    }, sys.stdout, indent=1)
    sys.stdout.write(chr(10))
