"""R3b's own named check (0145-ruling.md sec3): "his check on the 45° wing,
where the clip is real." A synthetic 80x120in wing, rotated 45 degrees (the
same shape the R3 --shot evidence used), with a ridge running its own long
axis and a room whose ceiling (96in, the app's own default) is taller than
the roof lets the two short gable-end walls clear -- eaves_h=60, ridge_h=140,
so each gable wall's covering height ramps from 60in (at its outer corners)
up to 140in (at the ridge crossing in the middle), dropping below the
96in ceiling everywhere outside +-22in of that crossing.

Writes `roof-clip-wing.png` beside this file: the wing alone, walls, roof
overlay and the two gable walls' own dotted orange clip line where it is
real. `QT_QPA_PLATFORM=offscreen` is fine here -- this is plain
`QGraphicsScene` painting (2D), not `fp3d.py`'s GL path, which is the one
that needs a real display (D77/D78).

    python docs/evidence/roof_clip_wing_receipt.py
"""
import math
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from PyQt6.QtCore import QPointF, QRectF, Qt          # noqa: E402
from PyQt6.QtGui import QImage, QPainter, QPainterPath  # noqa: E402
from PyQt6.QtWidgets import QApplication, QGraphicsScene  # noqa: E402

_app = QApplication.instance() or QApplication([])

from floorplanner.config import DEFAULT_FLOOR      # noqa: E402
from floorplanner.roofs import RoofItem, roof_clip_spans  # noqa: E402
from floorplanner.rooms import RoomItem            # noqa: E402
from floorplanner.walls import WallItem            # noqa: E402

HALF_L, HALF_W = 60.0, 40.0     # 120 x 80, matching the R3 --shot wing
CENTRE = (620.0, 120.0)
ANGLE_DEG = 45.0


def _rot(x, y, cx, cy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return (cx + x * ca - y * sa, cy + x * sa + y * ca)


def build_scene():
    scene = QGraphicsScene()
    corners_local = [(-HALF_L, -HALF_W), (HALF_L, -HALF_W),
                     (HALF_L, HALF_W), (-HALF_L, HALF_W)]
    corners = [_rot(x, y, *CENTRE, ANGLE_DEG) for x, y in corners_local]

    room_path = QPainterPath()
    room_path.moveTo(*corners[0])
    for x, y in corners[1:]:
        room_path.lineTo(x, y)
    room_path.closeSubpath()
    room = RoomItem("Wing", QPointF(*CENTRE), room_path, HALF_L * HALF_W * 4 / 144.0)
    room.floor = DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = 96.0
    scene.addItem(room)

    walls = []
    for i in range(4):
        p1, p2 = corners[i], corners[(i + 1) % 4]
        w = WallItem(QPointF(*p1), QPointF(*p2), "exterior")
        w.floor = DEFAULT_FLOOR
        scene.addItem(w)
        walls.append(w)

    ridge_half = HALF_L    # reaches exactly to the gable walls, like a real hip-free gable roof
    ca, sa = math.cos(math.radians(ANGLE_DEG)), math.sin(math.radians(ANGLE_DEG))
    r1 = (CENTRE[0] - ridge_half * ca, CENTRE[1] - ridge_half * sa)
    r2 = (CENTRE[0] + ridge_half * ca, CENTRE[1] + ridge_half * sa)
    roof = RoofItem(QPointF(*r1), QPointF(*r2), eaves_h_in=60.0,
                    ridge_h_in=140.0, overhang_in=6.0, span_in=HALF_W)
    roof.floor = DEFAULT_FLOOR
    scene.addItem(roof)
    return scene, walls, roof


def main():
    scene, walls, roof = build_scene()
    for w in walls:
        spans = roof_clip_spans(scene, w)
        if spans:
            print(f"wall ({w.p1.x():.1f},{w.p1.y():.1f}) -> "
                 f"({w.p2.x():.1f},{w.p2.y():.1f}): clipped {spans}")

    img = QImage(500, 400, QImage.Format.Format_ARGB32)
    img.fill(0xFFFFFFFF)
    pr = QPainter(img)
    pr.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    scene.render(pr, QRectF(0, 0, 500, 400), QRectF(500, -10, 250, 200),
                Qt.AspectRatioMode.IgnoreAspectRatio)
    pr.end()
    out = os.path.join(os.path.dirname(__file__), "roof-clip-wing.png")
    img.save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
