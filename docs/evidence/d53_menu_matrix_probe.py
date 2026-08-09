#!/usr/bin/env python3
"""D53 / A1b: WHICH MENU does a right-click open, for EVERY item type?

    python docs/evidence/d53_menu_matrix_probe.py <repo-root>

The room row is the one reported by hand. **The other seven are where an
unreported change would hide** -- which is the whole reason this is an
eight-row table and not a one-row fix receipt.

`OpeningItem` is the row to read first: it now outranks `WallItem` in the type
priority, so if a door has its own menu, a right-click on a door stops giving
the wall's menu. That is a behaviour change nobody asked for, and it is either
visible here or it is invisible everywhere.

`StairItem` is row eight and is MEASURED, not reasoned: it subclasses
`FurnishingItem`, so the resolver returns the instance and Python's MRO should
reach `StairItem.contextMenuEvent`. "Should" is why it is in the table.

AND THE RAISE_TO_FRONT ROW IS THE ONE MOST LIKELY TO BITE. A test that
right-clicks on a freshly loaded plan passes while the real gesture fails,
because `raise_to_front` only lifts a room ABOVE `WALL_Z` after the user has
dragged its label. That is the exact path that broke `dragWallFuseStraggler` on
the first cut of A1b, arriving here through the other virtual.

`QMenu.exec` is neutered (modal hangs headless); the ROUTE is real.
"""
import json
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"

ROOT = os.path.abspath(sys.argv[1])
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from PyQt6.QtCore import QPoint, QPointF                 # noqa: E402
from PyQt6.QtGui import QContextMenuEvent                # noqa: E402
from PyQt6.QtWidgets import QApplication, QMenu          # noqa: E402

app = QApplication([])
import FloorPlanner as fp                                # noqa: E402

QMenu.exec = lambda self, *a, **k: None
SEEN = []


def instrument():
    import floorplanner.items as I
    import floorplanner.rooms as R
    import floorplanner.view as V
    import floorplanner.walls as W
    for cls, name in [(R.RoomItem, "RoomItem"), (V.PlanView, "PlanView"),
                      (I.FurnishingItem, "FurnishingItem"),
                      (I.StairItem, "StairItem"), (I.GroupItem, "GroupItem"),
                      (I.ReferenceImageItem, "ReferenceImageItem"),
                      (W.WallItem, "WallItem"), (W.OpeningItem, "OpeningItem")]:
        if "contextMenuEvent" not in cls.__dict__:
            continue
        orig = cls.__dict__["contextMenuEvent"]

        def spy(self, e, _o=orig, _n=name):
            SEEN.append(_n)
            return _o(self, e)
        cls.contextMenuEvent = spy


def right_click(win, scene_pt):
    SEEN.clear()
    vp = win.view.viewport()
    p = win.view.mapFromScene(QPointF(scene_pt))
    QApplication.sendEvent(vp, QContextMenuEvent(
        QContextMenuEvent.Reason.Mouse, QPoint(p), vp.mapToGlobal(QPoint(p))))
    app.processEvents()
    return " -> ".join(SEEN) if SEEN else "(nothing)"


win = fp.MainWindow()
win.resize(1200, 900)
win.show()
sc = win.scene
win.set_tool(fp.TOOL_SELECT)


def walls_rect(x, y, w, h, t="interior"):
    cs = [QPointF(x, y), QPointF(x + w, y), QPointF(x + w, y + h), QPointF(x, y + h)]
    out = []
    for i in range(4):
        wl = fp.WallItem(cs[i], cs[(i + 1) % 4], t)
        sc.addItem(wl)
        out.append(wl)
    fp.rebuild_all_walls(sc)
    return out


# a room with a wall inside it, a door on that wall, a furnishing, a stair
rw = walls_rect(0, 0, 400, 300)
centre = QPointF(200, 150)
res = fp.detect_room(sc, centre)
room = fp.RoomItem(fp.unique_room_name(sc, "Den"), centre, res[0], res[1],
                   corners=res[2])
sc.addItem(room)
fp.bind_room_walls(sc, room)

inner = fp.WallItem(QPointF(100, 240), QPointF(300, 240), "interior")
sc.addItem(inner)
fp.rebuild_all_walls(sc)
door = fp.OpeningItem(inner, "door", "3280", 100.0)
sc.addItem(door)
fp.rebuild_all_walls(sc)

furn = fp.make_furnishing(fp.furnishing_catalog()[0]["id"], QPointF(70, 70))
sc.addItem(furn)
stair = fp.StairItem(QPointF(330, 70))
sc.addItem(stair)

# ReferenceImageItem is constructible headlessly after all -- a QImage needs no
# file. Worth measuring rather than declaring untestable: it is the one type
# ranked BELOW the room, so "does a right-click on the backdrop still reach it"
# is exactly the question its placement raises.
from PyQt6.QtGui import QImage                              # noqa: E402
img = QImage(64, 64, QImage.Format.Format_RGB32)
img.fill(0xFFFFFF)
ref = fp.ReferenceImageItem(img, 4.0)
ref.setPos(QPointF(-300, 40))
sc.addItem(ref)

grp = fp.GroupItem()
sc.addItem(grp)
gw = fp.WallItem(QPointF(60, 200), QPointF(140, 200), "interior")
sc.addItem(gw)
grp.adopt(gw)

win.zoom_fit()
app.processEvents()
instrument()

# The door sits at s=100 along a wall running (100,240)->(300,240), i.e. scene
# (200,240). The WALL row must therefore be sampled AWAY from it -- the first
# draft put both at (200,240) and the "wall" row silently measured the door.
DOOR_PT, WALL_PT = QPointF(200, 240), QPointF(280, 240)
rows = [
    ("RoomItem (label)", room.mapToScene(room._label_rect().center())),
    ("RoomItem (region)", QPointF(200, 60)),
    ("WallItem", WALL_PT),
    ("OpeningItem (door)", DOOR_PT),
    ("FurnishingItem", furn.pos()),
    ("StairItem", stair.pos()),
    ("GroupItem", QPointF(100, 200)),
    ("ReferenceImageItem", QPointF(-280, 60)),
    ("blank canvas", QPointF(-160, -160)),
]
out = {"head": os.popen("git rev-parse --short HEAD").read().strip(), "rows": {}}
for name, pt in rows:
    out["rows"][name] = right_click(win, pt)

# ROW NINE -- the one most likely to bite: raise_to_front, THEN right-click a
# wall inside the room. `raise_to_front` is what a label-drag runs.
room.raise_to_front()
app.processEvents()
out["room_z_after_raise"] = room.zValue()
out["wall_z"] = inner.zValue()
out["rows"]["WallItem AFTER raise_to_front"] = right_click(win, WALL_PT)
out["rows"]["OpeningItem AFTER raise_to_front"] = right_click(win, DOOR_PT)
out["rows"]["FurnishingItem AFTER raise_to_front"] = right_click(win, furn.pos())

json.dump(out, sys.stdout, indent=2)
sys.stdout.write("\n")
