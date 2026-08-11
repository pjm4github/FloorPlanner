"""Does the recorded growth law reproduce when each move goes to a NEW SPOT?
The record says 'walk x6 (each to a NEW spot) -> 0,2,4,6,8,10'. My earlier walk
OSCILLATED (+6/-6), returning to the berth every second move."""
import math
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath("."))

from PyQt6.QtWidgets import QApplication                  # noqa: E402

app = QApplication([])
import FloorPlanner as fp                                 # noqa: E402
from floorplanner.extract import extract_room, join_room  # noqa: E402

def counts(win):
    ws = [w for w in win.scene.items() if isinstance(w, fp.WallItem)]
    vs = set()
    inc = {}
    for w in ws:
        for v in (w._v1, w._v2):
            vs.add(id(v))
            inc.setdefault(id(v), []).append(w)
    coll = 0
    for group in inc.values():
        if len(group) != 2:
            continue
        a, b = group
        ua = math.atan2(a.p2.y()-a.p1.y(), a.p2.x()-a.p1.x())
        ub = math.atan2(b.p2.y()-b.p1.y(), b.p2.x()-b.p1.x())
        d = abs((ua-ub) % math.pi)
        if min(d, math.pi - d) < math.radians(0.5):
            coll += 1
    return len(ws), len(vs), coll

for label, step in (("NEW SPOT each move (+24 each time)", +24.0),
                    ("OSCILLATING (+6/-6)", None)):
    win = fp.MainWindow()
    win.resize(1400, 1000)
    win.load_path(os.path.abspath("fixtures/wiscaway2026-08-08.json"))
    room = next(r for r in win.scene.items()
                if isinstance(r, fp.RoomItem) and r.name == "WIC")
    base = counts(win)
    seq = []
    for i in range(1, 7):
        extract_room(win.scene, room)
        room._translate(step if step else (6.0 if i % 2 else -6.0), 0.0)
        join_room(win.scene, room)
        c = counts(win)
        seq.append(tuple(x - y for x, y in zip(c, base, strict=True)))
    print("%-36s base=%s" % (label, base))
    print("    walls delta    :", [s[0] for s in seq])
    print("    vertices delta :", [s[1] for s in seq])
    print("    collinear delta:", [s[2] for s in seq])
    win.close()
