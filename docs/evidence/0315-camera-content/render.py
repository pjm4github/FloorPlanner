"""0315 receipt: the camera's SHOW FURNISHINGS / SHOW CABINETRY switches.

Builds a kitchen-ish room, stands a base cabinet, a wall cabinet and a sofa
against the faced wall, turns both switches on, and renders the elevation (the
items as to-scale silhouettes at their mounting heights -- cabinetry wood,
furnishings teal). Also renders the plan GLYPH in its three states (plain /
furnishings / both), showing the badges that grow on the icon.

    python docs/evidence/0315-camera-content/render.py
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
from floorplanner.items import FurnishingItem

OUT = Path(__file__).resolve().parent


def _wall(scene, a, b):
    w = fp.WallItem(QPointF(*a), QPointF(*b), "interior")
    scene.addItem(w)
    return w


def main():
    app = QApplication(sys.argv[:1])   # noqa: F841
    scene = QGraphicsScene()
    wA = _wall(scene, (0, 0), (78, 0))         # far wall, left segment (a door)
    _wall(scene, (78, 0), (180, 0))            # far wall, right segment
    _wall(scene, (180, 0), (180, 100))
    _wall(scene, (180, 100), (0, 100))
    _wall(scene, (0, 100), (0, 0))
    wA.openings.append(fp.OpeningItem(wA, "door", "3080", 40.0))
    fp.rebuild_all_walls(scene)
    centre = QPointF(90, 50)
    res = fp.detect_room(scene, centre)
    room = fp.RoomItem(fp.unique_room_name(scene, "KITCHEN"), centre,
                       res[0], res[1], corners=res[2])
    room.properties["ceiling_height_in"] = 108.0
    scene.addItem(room)
    fp.bind_room_walls(scene, room)
    for kind, pos in [("base_cab_36", (120, 12)), ("wall_cab_36", (120, 6)),
                      ("sofa", (40, 14))]:
        it = FurnishingItem(kind, QPointF(*pos))
        scene.addItem(it)
    cam = CameraItem(QPointF(90, 60), rotation=270.0,
                     show_furnishings=True, show_cabinetry=True)
    scene.addItem(cam)

    e = cam.elevation()
    print("room %s  ceiling %.0f" % (e["room_name"], e["height_in"]))
    for it in e["furnishings"]:
        print("   %-18s casework=%s  x[%.0f..%.0f] y[%.0f..%.0f]"
              % (it["name"], it["casework"], it["x0_in"], it["x1_in"],
                 it["sill_in"], it["head_in"]))

    c = _WallElevationCanvas()
    c.resize(640, 360)
    c.set_data(e)
    img = QImage(640, 360, QImage.Format.Format_ARGB32)
    img.fill(0xFFFFFFFF)
    p = QPainter(img)
    c.render(p)
    p.end()
    img.save(str(OUT / "camera_content_elevation.png"))
    print("wrote camera_content_elevation.png")

    # the plan glyph in its three states, side by side
    strip = QImage(480, 180, QImage.Format.Format_ARGB32)
    strip.fill(0xFFFFFFFF)
    sp = QPainter(strip)
    states = [(False, False), (True, False), (True, True)]
    for i, (f, cb) in enumerate(states):
        g = CameraItem(QPointF(0, 0), rotation=270.0,
                       show_furnishings=f, show_cabinetry=cb)
        gs = QGraphicsScene()
        gs.addItem(g)
        gs.render(sp, QRectF(i * 160, 0, 160, 180), QRectF(-30, -45, 90, 100))
    sp.end()
    strip.save(str(OUT / "camera_glyphs.png"))
    print("wrote camera_glyphs.png (plain / furnishings / both)")
    print("RENDER OK")


if __name__ == "__main__":
    main()
