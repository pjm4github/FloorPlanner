"""0313 receipt: a plan CAMERA and the ROOM ELEVATION it produces.

Builds a small room whose FAR wall is two coplanar segments split by a doorway
(as the DINING room is: W47 + W57), with a window on the right segment and the
two side walls that turn toward the camera. Drops a camera in the room aimed at
that far wall, renders the `_WallElevationCanvas` to a PNG (both segments laid
left->right, the side walls as labelled return ticks), and renders the plan (the
camera glyph with its field-of-view wedge and aim arrow). Prints the elevation
dict (ASCII, legible where offscreen text renders as tofu).

    python docs/evidence/0313-plan-cameras/render.py
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


def _wall(scene, a, b):
    w = fp.WallItem(QPointF(*a), QPointF(*b), "interior")
    scene.addItem(w)
    return w


def main():
    app = QApplication(sys.argv[:1])   # noqa: F841
    scene = QGraphicsScene()
    # a 180" x 100" room; the far (top) wall is two coplanar segments
    wA = _wall(scene, (0, 0), (78, 0))         # far wall, left segment (a door)
    wB = _wall(scene, (78, 0), (180, 0))       # far wall, right segment (a window)
    _wall(scene, (180, 0), (180, 100))         # right side -> right return
    _wall(scene, (180, 100), (0, 100))         # near wall, behind the camera
    _wall(scene, (0, 100), (0, 0))             # left side -> left return
    wA.openings.append(fp.OpeningItem(wA, "door", "3280", 40.0))     # 32x80 on the floor
    wB.openings.append(fp.OpeningItem(wB, "window", "3648", 60.0))   # 36x48 on its sill
    fp.rebuild_all_walls(scene)
    centre = QPointF(90, 50)
    res = fp.detect_room(scene, centre)
    room = fp.RoomItem(fp.unique_room_name(scene, "DINING"), centre,
                       res[0], res[1], corners=res[2])
    room.properties["ceiling_height_in"] = 120.0
    scene.addItem(room)
    fp.bind_room_walls(scene, room)
    cam = CameraItem(QPointF(90, 60), rotation=270.0)   # in the room, aims up (-y)
    scene.addItem(cam)

    e = cam.elevation()
    print("room %s  ceiling %.0f  (floor %.0f)"
          % (e["room_name"], e["height_in"], e["floor_abs_in"]))
    for fc in e["faces"]:
        print("   face %-4s %.0f wide  windows=%d doors=%d"
              % (fc["label"], fc["width_in"], len(fc["windows"]), len(fc["doors"])))
    print("   returns: left=%s right=%s"
          % (e["left_return"] and e["left_return"]["label"],
             e["right_return"] and e["right_return"]["label"]))

    # the elevation canvas
    c = _WallElevationCanvas()
    c.resize(620, 360)
    c.set_data(e)
    img = QImage(620, 360, QImage.Format.Format_ARGB32)
    img.fill(0xFFFFFFFF)
    p = QPainter(img)
    c.render(p)
    p.end()
    img.save(str(OUT / "camera_elevation.png"))
    print("wrote camera_elevation.png")

    # the plan glyph (render the scene region around the room + camera)
    pw, ph = 520, 320
    plan = QImage(pw, ph, QImage.Format.Format_ARGB32)
    plan.fill(0xFFFFFFFF)
    pp = QPainter(plan)
    scene.render(pp, QRectF(0, 0, pw, ph), QRectF(-30, -30, 240, 160))
    pp.end()
    plan.save(str(OUT / "camera_plan.png"))
    print("wrote camera_plan.png")
    print("RENDER OK")


if __name__ == "__main__":
    main()
