"""0317 receipt: the camera's WHOLE-HOUSE-SIDE switch.

Stands a camera OUTSIDE a house, aimed at its front, turns the whole-house-side
switch on, and renders the elevation -- every exterior wall whose outside turns
toward the camera, laid left->right as one exterior elevation (not just the
single wall the aim ray hits). Also renders the plan glyph in three states
(plain / house-side / all three switches), showing the house badge.

    python docs/evidence/0317-house-side/render.py
"""
import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))   # repo root, for the shim

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication, QGraphicsScene

import FloorPlanner as fp  # noqa: F401
from floorplanner.cameras import CameraItem
from floorplanner.dialogs import _WallElevationCanvas

OUT = Path(__file__).resolve().parent


def _wall(scene, a, b, kind="exterior"):
    w = fp.WallItem(QPointF(*a), QPointF(*b), kind)
    scene.addItem(w)
    return w


def main():
    app = QApplication(sys.argv[:1])   # noqa: F841
    scene = QGraphicsScene()
    # a house whose FRONT (y=0) is two exterior segments with openings; the
    # camera stands outside, above it, and looks down the front
    w1 = _wall(scene, (0, 0), (120, 0))       # front, left segment (a door)
    w2 = _wall(scene, (120, 0), (300, 0))     # front, right segment (two windows)
    _wall(scene, (300, 0), (300, 180))        # right side (a return)
    _wall(scene, (300, 180), (0, 180))        # back of the house (excluded)
    _wall(scene, (0, 180), (0, 0))            # left side (a return)
    w1.openings.append(fp.OpeningItem(w1, "door", "3680", 60.0))
    w2.openings.append(fp.OpeningItem(w2, "window", "3648", 60.0))
    w2.openings.append(fp.OpeningItem(w2, "window", "3648", 140.0))
    fp.rebuild_all_walls(scene)
    centre = QPointF(150, 90)
    res = fp.detect_room(scene, centre)
    room = fp.RoomItem(fp.unique_room_name(scene, "HOUSE"), centre,
                       res[0], res[1], corners=res[2])
    room.properties["ceiling_height_in"] = 108.0
    scene.addItem(room)
    fp.bind_room_walls(scene, room)
    cam = CameraItem(QPointF(150, -80), rotation=90.0, show_house_side=True)
    scene.addItem(cam)

    e = cam.elevation()
    print("room %s  ceiling %.0f" % (e["room_name"] or "(outside)", e["height_in"]))
    print("faces (the whole side, left->right):",
          [(f["label"], round(f["width_in"])) for f in e["faces"]])

    c = _WallElevationCanvas()
    c.resize(760, 320)
    c.set_data(e)
    img = QImage(760, 320, QImage.Format.Format_ARGB32)
    img.fill(0xFFFFFFFF)
    p = QPainter(img)
    c.render(p)
    p.end()
    img.save(str(OUT / "house_side_elevation.png"))
    print("wrote house_side_elevation.png")

    # the plan glyph: plain / house-side / all three switches
    strip = QImage(360, 180, QImage.Format.Format_ARGB32)
    strip.fill(0xFFFFFFFF)
    sp = QPainter(strip)
    states = [(False, False, False), (False, False, True), (True, True, True)]
    for i, (f, cb, hs) in enumerate(states):
        g = CameraItem(QPointF(0, 0), rotation=270.0,
                       show_furnishings=f, show_cabinetry=cb, show_house_side=hs)
        gs = QGraphicsScene()
        gs.addItem(g)
        gs.render(sp, QRectF(i * 120, 0, 120, 180), QRectF(-30, -45, 90, 100))
    sp.end()
    strip.save(str(OUT / "camera_glyphs.png"))
    print("wrote camera_glyphs.png (plain / house-side / all three)")
    print("RENDER OK")


if __name__ == "__main__":
    main()
