#!/usr/bin/env python3
"""D53 / A1b: WHICH handler receives a right-click over a room?

    python docs/evidence/d53_menu_route_probe.py <repo-root> <plan.json>

The census proves `RoomItem.contextMenuEvent` EXISTS. It cannot prove the menu
is REACHABLE -- a handler can exist and still be shadowed by a widget above it
accepting the event first. That is a runtime question, so it is measured here
and not inferred, and the two are deliberately separate files.

`QMenu.exec` is neutered to return None for the duration: it is modal, and a
modal dialog hangs a headless run. Everything else runs for real, so the ROUTE
is the real route -- only the blocking show is removed.

Two points per room, because they were never equivalent: the LABEL (which was
inside `RoomItem.shape()` before A1b as well as after) and the REGION (which was
not). Run against a `main` worktree and against the branch, and diff.
"""
import json
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"

ROOT = os.path.abspath(sys.argv[1])
PLAN = os.path.abspath(sys.argv[2])
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from PyQt6.QtCore import QPoint, QPointF                 # noqa: E402
from PyQt6.QtGui import QContextMenuEvent                # noqa: E402
from PyQt6.QtWidgets import QApplication, QMenu          # noqa: E402

app = QApplication([])
import FloorPlanner as fp                                # noqa: E402

QMenu.exec = lambda self, *a, **k: None                  # modal -> no-op

SEEN = []


def instrument():
    """Log every contextMenuEvent entry, then call the real one."""
    import floorplanner.items as I
    import floorplanner.rooms as R
    import floorplanner.view as V
    import floorplanner.walls as W
    targets = [(R.RoomItem, "RoomItem"), (V.PlanView, "PlanView"),
               (I.FurnishingItem, "FurnishingItem"), (I.GroupItem, "GroupItem"),
               (I.StairItem, "StairItem"),
               (I.ReferenceImageItem, "ReferenceImageItem"),
               (W.WallItem, "WallItem"), (W.OpeningItem, "OpeningItem")]
    for cls, name in targets:
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
    ev = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, QPoint(p),
                           vp.mapToGlobal(QPoint(p)))
    QApplication.sendEvent(vp, ev)
    app.processEvents()
    return list(SEEN)


win = fp.MainWindow()
win.resize(1200, 800)
win.show()
win.load_path(PLAN)
app.processEvents()
instrument()

rooms = sorted((i for i in win.scene.items() if isinstance(i, fp.RoomItem)),
               key=lambda r: r.name)
room = rooms[0]
br = room.path.boundingRect()
region = QPointF(br.x() + br.width() * 0.5, br.y() + br.height() * 0.8)
label = room.mapToScene(room._label_rect().center())

out = {
    "head": os.popen("git rev-parse --short HEAD").read().strip(),
    "room": room.name,
    "room_has_contextMenuEvent": "contextMenuEvent" in type(room).__dict__,
    "region_in_label_rect": room._label_rect().contains(
        room.mapFromScene(region)),
    "right_click_on_LABEL": right_click(win, label),
    "right_click_on_REGION": right_click(win, region),
}
json.dump(out, sys.stdout, indent=2)
sys.stdout.write("\n")
