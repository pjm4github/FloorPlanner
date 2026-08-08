"""Click-selection differential, WIDENED: which points of a room are clickable?

    python click_probe2.py <repo-root> <plan.json>

The first probe clicked the LABEL CENTRE and found selection retained. That
answered a narrower question than the report asks: "clicking a room" can mean
the label or the REGION, and those are different objects here because
`RoomItem.shape()` returns only the label rect.

So this samples several points per room and reports, for each:

  top_item     what Qt says is under that point (scene.itemAt, view transform)
  hit_room     did THIS RoomItem receive the press
  sel_release  is the room selected after a full press+release with no movement
  scene_sel    everything the scene reports selected afterwards

Run on `main` and on the A1 branch and diff the two. Points sampled:

  label        the label rect's centre -- the drag handle
  region       a point well inside the region and OUTSIDE the label rect,
               which is what "clicking a room" most naturally means
  region2      a second interior point, to guard against one unlucky sample

The label-overflow numbers are collected too, because the same `_label_rect`
is both the hit area and the text clip: `w` is sized from `self.name` in the
14px font and the SUBTITLE is drawn with the 9px font and never measured.
"""
import json
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"

ROOT = os.path.abspath(sys.argv[1])
PLAN = os.path.abspath(sys.argv[2])
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from PyQt6.QtCore import QPoint, QPointF, Qt            # noqa: E402
from PyQt6.QtGui import QMouseEvent                      # noqa: E402
from PyQt6.QtWidgets import QApplication, QGraphicsView  # noqa: E402

app = QApplication([])
import FloorPlanner as fp                                # noqa: E402


def the_view(win):
    if isinstance(getattr(win, "view", None), QGraphicsView):
        return win.view
    for n in dir(win):
        v = getattr(win, n, None)
        if isinstance(v, QGraphicsView):
            return v
    raise SystemExit("no view")


def send(view, kind, scene_pt, buttons):
    vp = view.viewport()
    local = QPointF(view.mapFromScene(scene_pt))
    gp = vp.mapToGlobal(QPoint(int(local.x()), int(local.y())))
    QApplication.sendEvent(vp, QMouseEvent(
        kind, local, QPointF(gp), Qt.MouseButton.LeftButton, buttons,
        Qt.KeyboardModifier.NoModifier))
    app.processEvents()


def label_pt(r):
    return r.mapToScene(r._label_rect().center())


def region_pts(r):
    """Two interior points that are NOT in the label rect."""
    p = r.path
    br = p.boundingRect()
    lab = r._label_rect()
    out = []
    for fx, fy in [(0.5, 0.78), (0.28, 0.30), (0.72, 0.30), (0.5, 0.5),
                   (0.28, 0.72), (0.72, 0.72)]:
        pt = QPointF(br.x() + br.width() * fx, br.y() + br.height() * fy)
        if p.contains(pt) and not lab.contains(pt):
            out.append(r.mapToScene(pt))
        if len(out) == 2:
            break
    return out


def click(win, room, scene_pt):
    view = the_view(win)
    ran = {"n": 0}
    orig = type(room).mousePressEvent

    def spy(self, e, _o=orig):
        if self is room:
            ran["n"] += 1
        return _o(self, e)

    top = win.scene.itemAt(scene_pt, view.transform())
    type(room).mousePressEvent = spy
    try:
        win.scene.clearSelection()
        app.processEvents()
        send(view, QMouseEvent.Type.MouseButtonPress, scene_pt,
             Qt.MouseButton.LeftButton)
        sp = room.isSelected()
        send(view, QMouseEvent.Type.MouseButtonRelease, scene_pt,
             Qt.MouseButton.NoButton)
    finally:
        type(room).mousePressEvent = orig
    return {
        "top_item": type(top).__name__ if top is not None else None,
        "top_is_this_room": top is room,
        "hit_room": ran["n"] > 0,
        "sel_press": sp,
        "sel_release": room.isSelected(),
        "scene_sel": sorted(getattr(i, "name", type(i).__name__)
                            for i in win.scene.selectedItems()),
    }


def label_metrics(r):
    lab = r._label_rect()
    sub = f"{r.area_sqft:.0f} sq ft" + (
        " (floating)" if r.placement_state == "floating" else "")
    return {
        "name": r.name,
        "state": r.placement_state,
        "rect_w": round(lab.width(), 1),
        "name_advance_14px": round(r._font_metrics.horizontalAdvance(r.name), 1),
        "subtitle": sub,
        "subtitle_advance_9px": round(
            r._sub_font_metrics.horizontalAdvance(sub), 1),
        "overflow_px": round(
            r._sub_font_metrics.horizontalAdvance(sub) - lab.width(), 1),
    }


def rooms(win):
    return [i for i in win.scene.items() if isinstance(i, fp.RoomItem)]


out = {"head": os.popen("git rev-parse --short HEAD").read().strip(), "cases": {}}
win = fp.MainWindow()
win.resize(1200, 800)
win.show()
win.load_path(PLAN)
app.processEvents()

r0 = sorted(rooms(win), key=lambda r: r.name)[0]
out["cases"]["placed/label"] = click(win, r0, label_pt(r0))
for i, pt in enumerate(region_pts(r0)):
    out["cases"][f"placed/region{i}"] = click(win, r0, pt)

win.scene.clearSelection()
for r in rooms(win):
    r.setSelected(True)
win.room_boolean("fragment")
app.processEvents()

pieces = sorted(rooms(win), key=lambda r: r.name)
out["pieces"] = [(r.name, r.placement_state) for r in pieces]
out["groups_after_fragment"] = sum(
    1 for i in win.scene.items() if type(i).__name__ == "GroupItem")
p = pieces[0]
out["cases"]["piece/label"] = click(win, p, label_pt(p))
for i, pt in enumerate(region_pts(p)):
    out["cases"][f"piece/region{i}"] = click(win, p, pt)
out["labels"] = [label_metrics(r) for r in pieces]

json.dump(out, sys.stdout, indent=2)
sys.stdout.write("\n")
