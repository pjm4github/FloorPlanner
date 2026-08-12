"""P6.d Q1: does a GestureCommand's undo restore BOTH floors, or only the
scoped one?

D67 is TESTIMONY and unreproduced, so the cross-floor drag itself cannot be
driven here. What CAN be measured is the property the pre-commitment turns on:
when a gesture has touched two floors, does undo bring BOTH back?

That is answerable without reproducing D67 -- construct a change on both floors,
wrap it in a GestureCommand exactly as the cutover would, undo, and compare each
floor to pristine.
"""
import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath("."))

from PyQt6.QtCore import QPointF                       # noqa: E402
from PyQt6.QtWidgets import QApplication               # noqa: E402

app = QApplication([])
import FloorPlanner as fp                              # noqa: E402
from floorplanner.commands import DragGesture          # noqa: E402

def per_floor(win):
    """Each floor's wall geometry, keyed by floor -- so a partial restore is
    visible as one floor differing while the other matches."""
    out = {}
    for w in win.scene.items():
        if isinstance(w, fp.WallItem):
            out.setdefault(w.floor, []).append(
                (round(w.p1.x(), 3), round(w.p1.y(), 3),
                 round(w.p2.x(), 3), round(w.p2.y(), 3)))
    return {k: sorted(v) for k, v in out.items()}

win = fp.MainWindow()
win.resize(1200, 900)
win.load_path(os.path.abspath("examples/roundedMultifloor.json"))
pristine = per_floor(win)
floors = sorted(pristine)
print("floors:", floors, {k: len(v) for k, v in pristine.items()})
assert len(floors) > 1, "precondition: multi-floor"

before = win.snapshot()

# a change touching BOTH floors -- the state a cross-floor drag would leave
# THREE WALLS PER FLOOR, chosen per floor rather than by scene order -- the
# first attempt took the first six items and they were all on `default`, which
# the precondition caught.
per = {}
for w in win.scene.items():
    if isinstance(w, fp.WallItem):
        per.setdefault(w.floor, []).append(w)
for f in floors:
    for w in per.get(f, [])[:3]:
        w.detach_end("p1", QPointF(w.p1.x() + 12.0, w.p1.y()))
fp.rebuild_all_walls(win.scene)
dirty = per_floor(win)
touched = [f for f in floors if dirty.get(f) != pristine.get(f)]
print("floors actually changed:", touched)
assert len(touched) > 1, f"precondition: the change must span floors, got {touched}"

after = win.snapshot()
cmd = DragGesture(win, before, after, win.active_floor, "cross-floor")
cmd.undo()

restored = per_floor(win)
result = {f: ("restored" if restored.get(f) == pristine.get(f) else "STILL DIRTY")
          for f in floors}
print("after undo:", json.dumps(result))
print()
print("VERDICT:", "COMPLETE -- every floor came back"
      if all(v == "restored" for v in result.values())
      else "PARTIAL -- undo left a floor displaced")
win.close()
