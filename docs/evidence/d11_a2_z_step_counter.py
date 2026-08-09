"""A2 / D11: a BOUNDED EVENT COUNTER over the z step's consumers.

    python a2_counter.py <worktree> <step> [bound]

The z work was reverted, so the hang is not reproducible from disk. This
reconstructs the one thing the report names -- the MAGNITUDE of the step
`bring_to_front` applies -- and counts who is called while the pinned macro
replays.

**BOUNDED**, which is the whole point: the symptom is a hang, and a hang yields
no evidence. The counter aborts the run the moment total events cross a limit
and prints the tallies, so the hang becomes a finite report naming its consumer
instead of a wedged process. Nothing here chooses a constant to make the symptom
go away; the step is an argument and both values are run.
"""
import json
import os
import sys
import traceback
from collections import Counter

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = os.path.abspath(sys.argv[1])
STEP = float(sys.argv[2])
BOUND = int(sys.argv[3]) if len(sys.argv) > 3 else 200_000
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from PyQt6.QtWidgets import QApplication                # noqa: E402

app = QApplication([])
import FloorPlanner as fp                               # noqa: E402
import floorplanner.geometry as G                       # noqa: E402
import floorplanner.levels as L                         # noqa: E402
import floorplanner.rooms as R                          # noqa: E402
import floorplanner.walls as W                          # noqa: E402

G._A2_STEP = STEP
R._A2_STACK_BAND = float(os.environ.get('A2_STACK', '10'))

N = Counter()
ZMAX = {"max_abs_z": 0.0, "max_set": None}


class Bound(RuntimeError):
    pass


def tick(name):
    N[name] += 1
    N["TOTAL"] += 1
    if N["TOTAL"] > BOUND:
        raise Bound(f"bound {BOUND} exceeded at {name}")


def wrap(obj, attr, label):
    orig = getattr(obj, attr)

    def w(*a, **k):
        tick(label)
        return orig(*a, **k)
    setattr(obj, attr, w)


def wrap_method(cls, attr, label):
    if attr not in cls.__dict__:
        return
    orig = cls.__dict__[attr]

    def w(self, *a, **k):
        tick(label)
        return orig(self, *a, **k)
    setattr(cls, attr, w)


# -- the z step's producers ---------------------------------------------------
wrap(G, "bring_to_front", "geometry.bring_to_front")
wrap(G, "send_to_back", "geometry.send_to_back")
wrap_method(R.RoomItem, "raise_to_front", "RoomItem.raise_to_front")
wrap_method(L.LevelsMixin, "_apply_floor_stacking", "_apply_floor_stacking")

# -- the plausible CONSUMERS: anything that could re-enter on a z change ------
wrap(fp, "rebuild_all_walls", "rebuild_all_walls")
wrap_method(R.RoomItem, "itemChange", "RoomItem.itemChange")
wrap_method(W.WallItem, "itemChange", "WallItem.itemChange")
wrap_method(W.WallItem, "mousePressEvent", "WallItem.mousePressEvent")
wrap_method(R.RoomItem, "mousePressEvent", "RoomItem.mousePressEvent")
wrap_method(R.RoomItem, "paint", "RoomItem.paint")
wrap_method(W.WallItem, "paint", "WallItem.paint")

# -- and the z WRITES themselves, with the extreme value kept -----------------
from PyQt6.QtWidgets import QGraphicsItem              # noqa: E402

_setz = QGraphicsItem.setZValue


def setz(self, v):
    tick("setZValue")
    if abs(v) > abs(ZMAX["max_abs_z"]):
        ZMAX["max_abs_z"] = v
        ZMAX["max_set"] = type(self).__name__
    return _setz(self, v)


QGraphicsItem.setZValue = setz

out = {"root": ROOT, "step": STEP, "stack": R._A2_STACK_BAND, "bound": BOUND,
       "head": os.popen("git rev-parse --short HEAD").read().strip()}
import pathlib                                          # noqa: E402
ex = pathlib.Path(ROOT) / "examples"
win = fp.MainWindow()
win.resize(1400, 1000)
win.show()
win.load_path(str(ex / "fiveRoomTest.json"))
win.zoom_fit()
N.clear()
ZMAX["max_abs_z"], ZMAX["max_set"] = 0.0, None

lines = [ln for ln in (ex / "fiveRoomDragSplit.fpm").read_text().splitlines()
         if ln.strip()]
out["lines"] = len(lines)
per_line = []
try:
    for i, line in enumerate(lines, 1):
        before = N["TOTAL"]
        res = win.run_macro(line)
        per_line.append({"n": i, "line": line[:34], "ok": bool(res.get("ok")),
                         "events": N["TOTAL"] - before})
    out["completed"] = True
except Bound as b:
    out["completed"] = False
    out["aborted"] = str(b)
    per_line.append({"n": len(per_line) + 1, "line": "<<ABORTED HERE>>",
                     "events": N["TOTAL"] - (per_line[-1]["events"]
                                             if per_line else 0)})
except Exception as e:                                   # noqa: BLE001
    out["completed"] = False
    out["error"] = f"{type(e).__name__}: {e}"
    out["traceback"] = traceback.format_exc()[-1200:]

out["per_line"] = per_line
out["counts"] = dict(N.most_common())
out["max_abs_z"] = ZMAX["max_abs_z"]
out["max_z_on"] = ZMAX["max_set"]
json.dump(out, sys.stdout, indent=1)
sys.stdout.write("\n")
