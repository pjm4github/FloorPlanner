"""Q4 (REAL DISPLACEMENT: +6/-6 alternating, so the room genuinely relocates
and returns -- a zero-offset move never reaches the producer at all).

Would a command that KNOWS WHAT IT DID remove the need for 2b's
leave-path coalesce?

Attribution per HALF-STEP. The six-move walk is extract, move, join, repeated.
If the growth is produced by JOIN and an inverse-Extract could restore the
pre-join state, a command layer would cancel it. If the growth is already there
after EXTRACT, no inverse can help -- there is nothing to invert yet.

Measured on the PLAIN tree (2b is stashed), so this is the state as it ships.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath("."))

from PyQt6.QtWidgets import QApplication          # noqa: E402

app = QApplication([])
import FloorPlanner as fp                         # noqa: E402
from floorplanner.extract import extract_room, join_room   # noqa: E402

def counts(win):
    walls = [w for w in win.scene.items() if isinstance(w, fp.WallItem)]
    vs = set()
    for w in walls:
        vs.add(id(w._v1))
        vs.add(id(w._v2))
    return len(walls), len(vs)

win = fp.MainWindow()
win.resize(1400, 1000)
win.load_path(os.path.abspath("fixtures/wiscaway2026-08-08.json"))
target = next(r for r in win.scene.items()
              if isinstance(r, fp.RoomItem) and r.name == "WIC")
base = counts(win)
print("start                    walls=%d vertices=%d" % base)
for i in range(1, 7):
    extract_room(win.scene, target)
    a = counts(win)
    target._translate(6.0 if i % 2 else -6.0, 0.0)   # production's own float mover
    join_room(win.scene, target)
    b = counts(win)
    print("move %d  after EXTRACT %s   after JOIN %s   cumulative delta %s"
          % (i, a, b, tuple(x - y for x, y in zip(b, base, strict=True))))
win.close()
