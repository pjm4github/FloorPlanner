"""Patrick's repro: delete the Kitchen room, Room-tool click the enclosed space.

    python kitchen_repro.py <repo-root> <plan> <logfile>

THE FAULT IS CAPTURED, NOT INFERRED. PyQt6 aborts the process on an unhandled
Python exception inside a virtual override, and the abort can outrun stdout --
which is how this class of crash presents as a segfault with no traceback. So
faulthandler AND sys.excepthook both write to a FILE that is flushed and fsynced
on every write, and the file is read back after the process dies.
"""
import os
import sys
import traceback

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT, PLAN, LOG = (os.path.abspath(a) for a in sys.argv[1:4])
sys.path.insert(0, ROOT)
os.chdir(ROOT)

log = open(LOG, "w", encoding="utf-8", buffering=1)


def say(*a):
    log.write(" ".join(str(x) for x in a) + "\n")
    log.flush()
    os.fsync(log.fileno())


import faulthandler                                    # noqa: E402
faulthandler.enable(file=log)


def hook(t, v, tb):
    say("!!! UNHANDLED EXCEPTION IN A QT VIRTUAL -- PyQt6 will abort after this")
    traceback.print_exception(t, v, tb, file=log)
    log.flush()
    os.fsync(log.fileno())


sys.excepthook = hook

from PyQt6.QtCore import QEvent, QPointF, Qt           # noqa: E402
from PyQt6.QtGui import QMouseEvent                    # noqa: E402
from PyQt6.QtWidgets import QApplication, QInputDialog  # noqa: E402

app = QApplication([])
import FloorPlanner as fp                              # noqa: E402

say("step 0: load", PLAN)
win = fp.MainWindow()
win.resize(1400, 1000)
win.show()
win.load_path(PLAN)
app.processEvents()
win.zoom_fit()
app.processEvents()

rooms = [i for i in win.scene.items() if isinstance(i, fp.RoomItem)]
say("   rooms:", sorted(r.name for r in rooms))
kitchen = next((r for r in rooms if r.name.lower().startswith("kitchen")), None)
if kitchen is None:
    say("NO KITCHEN -- cannot run the repro")
    raise SystemExit(2)

inside = kitchen.path.boundingRect().center()
if not kitchen.path.contains(inside):
    inside = kitchen.anchor
say(f"   Kitchen at {inside.x():.1f},{inside.y():.1f}  state={kitchen.placement_state}"
    f"  walls={len(kitchen.walls)}  area={kitchen.area_sqft:.0f}")

say("step 1: DELETE THE ROOM exactly as the room menu does "
    "(clear_walls, then removeItem -- the walls stay)")
kitchen.clear_walls()
win.scene.removeItem(kitchen)
app.processEvents()
say("   rooms now:", sorted(r.name for r in win.scene.items()
                            if isinstance(r, fp.RoomItem)))

say("step 2: select the Room Name tool")
win.set_tool(fp.TOOL_ROOM)

say("step 3: the naming dialog will answer 'Kitchen'")
QInputDialog.getText = staticmethod(
    lambda *a, **k: (say("   ...naming dialog OPENED"), ("Kitchen", True))[1])

say("step 4: LEFT-CLICK the enclosed space that was the kitchen")
vp = win.view.viewport()
p = QPointF(win.view.mapFromScene(inside))
for et, btn, btns in ((QEvent.Type.MouseButtonPress, Qt.MouseButton.LeftButton,
                       Qt.MouseButton.LeftButton),
                      (QEvent.Type.MouseButtonRelease, Qt.MouseButton.LeftButton,
                       Qt.MouseButton.NoButton)):
    say(f"   sending {et.name}")
    QApplication.sendEvent(vp, QMouseEvent(et, p, vp.mapToGlobal(p), btn, btns,
                                           Qt.KeyboardModifier.NoModifier))
    app.processEvents()
    say("   ...survived")

say("step 5: SURVIVED THE WHOLE GESTURE -- no crash")
say("   rooms now:", sorted(r.name for r in win.scene.items()
                            if isinstance(r, fp.RoomItem)))
