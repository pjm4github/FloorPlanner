"""0318 receipt: the whole-house-side elevation as a composited LINE drawing.

Builds a TWO-STOREY house (L1 at 0, L2 at 108) with a gable roof on top, puts a
camera outside facing a GABLE END and another facing an EAVE side, turns the
whole-house-side switch on, and renders each elevation. The elevation is built by
COMPOSITING 2-D pieces from the planner's own wall/roof/dormer geometry (no 3D
model, no depth buffer): each exterior wall is a vertical polygon clipped to the
roofline above it, each gable/shed roof contributes its camera-facing slopes and
gable ends, and the pieces are painted far -> near so a nearer form hides what
stands behind it.

    python docs/evidence/0318-full-elevation/render.py
"""
import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication, QGraphicsScene

app = QApplication(sys.argv[:1])   # noqa: F841

import FloorPlanner as fp  # noqa: E402
from floorplanner.cameras import CameraItem  # noqa: E402
from floorplanner.config import set_floor_state  # noqa: E402
from floorplanner.dialogs import _WallElevationCanvas  # noqa: E402
from floorplanner.roofs import RoofItem  # noqa: E402

OUT = Path(__file__).resolve().parent


def wall(scene, a, b, floor, kind="exterior"):
    w = fp.WallItem(QPointF(*a), QPointF(*b), kind)
    w.floor = floor
    scene.addItem(w)
    return w


def storey(scene, floor):
    w1 = wall(scene, (0, 0), (150, 0), floor)        # front, split in two
    w2 = wall(scene, (150, 0), (300, 0), floor)
    wall(scene, (300, 0), (300, 180), floor)
    wall(scene, (300, 180), (0, 180), floor)
    wall(scene, (0, 180), (0, 0), floor)
    return w1, w2


def detect(scene, floor, name):
    set_floor_state(active=floor)
    fp.rebuild_all_walls(scene)
    c = QPointF(150, 90)
    res = fp.detect_room(scene, c)
    if res is None:
        print("  (no room detected on %s)" % floor)
        return None
    r = fp.RoomItem(fp.unique_room_name(scene, name), c, res[0], res[1], corners=res[2])
    r.floor = floor
    scene.addItem(r)
    fp.bind_room_walls(scene, r)
    return r


def build():
    set_floor_state(active="L1", elevations={"L1": 0.0, "L2": 108.0})
    scene = QGraphicsScene()
    l1a, l1b = storey(scene, "L1")
    l1a.openings.append(fp.OpeningItem(l1a, "door", "3680", 75.0))
    l1b.openings.append(fp.OpeningItem(l1b, "window", "3648", 75.0))
    detect(scene, "L1", "L1ROOM")
    l2a, l2b = storey(scene, "L2")
    l2a.openings.append(fp.OpeningItem(l2a, "window", "3048", 75.0))
    l2b.openings.append(fp.OpeningItem(l2b, "window", "3048", 75.0))
    detect(scene, "L2", "L2ROOM")
    # a gable roof on L2: ridge runs in Y (0..180), eaves at x=0 and x=300
    set_floor_state(active="L2")
    rf = RoofItem(QPointF(150, 0), QPointF(150, 180),
                  eaves_h_in=108.0, ridge_h_in=168.0, span_in=[150.0, 150.0])
    rf.floor = "L2"
    scene.addItem(rf)
    set_floor_state(active="L1")
    return scene


def render(scene, cam, name):
    scene.addItem(cam)
    e = cam.elevation()
    if e is None:
        print("%s: elevation is None" % name)
        scene.removeItem(cam)
        return
    pcs = e.get("pieces", [])
    nop = sum(len(pc.get("openings", [])) for pc in pcs) + len(e.get("dormer_windows", []))
    print("%s: mode %s, %d piece(s), %d opening(s), height %.0f, width %.0f"
          % (name, e.get("mode"), len(pcs), nop, e["height_in"], e["width_in"]))
    c = _WallElevationCanvas()
    c.resize(820, 420)
    c.set_data(e)
    img = QImage(820, 420, QImage.Format.Format_ARGB32)
    img.fill(0xFFFFFFFF)
    p = QPainter(img)
    c.render(p)
    p.end()
    img.save(str(OUT / name))
    print("  wrote %s" % name)
    scene.removeItem(cam)


def main():
    scene = build()
    render(scene, CameraItem(QPointF(150, -90), rotation=90.0, floor="L1",
                             show_house_side=True), "gable_end.png")
    render(scene, CameraItem(QPointF(380, 90), rotation=180.0, floor="L1",
                             show_house_side=True), "eave_side.png")
    print("RENDER OK")


if __name__ == "__main__":
    main()
