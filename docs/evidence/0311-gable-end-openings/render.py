"""0311 receipt: the End-On dialog's Elevation tab reads the WALL(S) under the
gable end and draws every DOOR and WINDOW to scale, with measurements.

Builds a plain gable roof with a gable-end wall carrying a door and two windows,
and a second case where the gable end is two collinear wall segments. Renders
the `_ElevationCanvas` for each to a PNG, and prints the `gable_elevation()`
dicts (ASCII, so legible where offscreen text renders as tofu).

    python docs/evidence/0311-gable-end-openings/render.py
"""
import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root, for the shim

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication

import FloorPlanner as fp  # noqa: F401  (loads the package API: OpeningItem etc.)
from floorplanner.config import DEFAULT_FLOOR
from floorplanner.dialogs import _ElevationCanvas
from floorplanner.roofs import RoofItem
from floorplanner.walls import WallItem

OUT = Path(__file__).resolve().parent


def render(canvas_data, name, w=560, h=340):
    c = _ElevationCanvas()
    c.resize(w, h)
    c.set_data(canvas_data)
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    img.fill(0xFFFFFFFF)
    p = QPainter(img)
    c.render(p)
    p.end()
    img.save(str(OUT / name))
    print("wrote", name)


def show(tag, e):
    print(f"\n[{tag}] kind={e['kind']} width={e['width_in']:.0f} "
          f"ridge={e['ridge_in']:.0f} apex={e['apex_in']:.0f} end={e['end']}")
    print(f"   windows={len(e['windows'])} doors={len(e['doors'])} (separate lists)")
    for o in e["windows"] + e["doors"]:
        print(f"   {o['kind']:6s} {o['w_in']:.0f}x{o['h_in']:.0f}  "
              f"sill={o['sill_in']:.0f} head={o['head_in']:.0f} "
              f"centre={o['centre_in']:+.0f}")


def main():
    app = QApplication(sys.argv[:1])  # noqa: F841
    scene = fp.PlanScene() if hasattr(fp, "PlanScene") else _bare_scene()

    # Case 1: one gable-end wall, a door between two windows.
    rf = RoofItem(QPointF(0, 100), QPointF(400, 100), eaves_h_in=96.0,
                  ridge_h_in=156.0, overhang_in=0.0, span_in=[120.0, 80.0])
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    w = WallItem(QPointF(0, 0), QPointF(0, 200), "exterior")
    w.floor = DEFAULT_FLOOR
    w.openings.append(fp.OpeningItem(w, "window", "3048", 40.0))
    w.openings.append(fp.OpeningItem(w, "door", "3680", 100.0))
    w.openings.append(fp.OpeningItem(w, "window", "2436", 160.0))
    scene.addItem(w)
    e1 = rf.gable_elevation(end=0)
    show("one wall: door + two windows", e1)
    render(e1, "gable_openings.png")

    # Case 2: the gable end built from two collinear segments.
    scene2 = _bare_scene()
    rf2 = RoofItem(QPointF(0, 100), QPointF(400, 100), eaves_h_in=96.0,
                   ridge_h_in=150.0, overhang_in=0.0, span_in=100.0)
    rf2.floor = DEFAULT_FLOOR
    scene2.addItem(rf2)
    lo = WallItem(QPointF(0, 0), QPointF(0, 82), "exterior")
    lo.floor = DEFAULT_FLOOR
    lo.openings.append(fp.OpeningItem(lo, "window", "2430", 40.0))
    scene2.addItem(lo)
    hi = WallItem(QPointF(0, 118), QPointF(0, 200), "exterior")
    hi.floor = DEFAULT_FLOOR
    hi.openings.append(fp.OpeningItem(hi, "door", "3080", 40.0))   # within the 82" segment
    scene2.addItem(hi)
    e2 = rf2.gable_elevation(end=0)
    show("two collinear segments", e2)
    render(e2, "gable_segments.png")

    # Case 3: a TWO-STOREY gable -- the roof's floor and the floor above both
    # stand under the gable, so the upper window lifts to its true height.
    from floorplanner.config import set_floor_state
    set_floor_state(elevations={DEFAULT_FLOOR: 0.0, "upper": 96.0})
    scene3 = _bare_scene()
    rf3 = RoofItem(QPointF(0, 100), QPointF(400, 100), eaves_h_in=96.0,
                   ridge_h_in=240.0, overhang_in=0.0, span_in=[144.0, 144.0])
    rf3.floor = DEFAULT_FLOOR
    scene3.addItem(rf3)
    g = WallItem(QPointF(0, -44), QPointF(0, 244), "exterior")      # ground gable wall
    g.floor = DEFAULT_FLOOR
    g.openings.append(fp.OpeningItem(g, "window", "3648", 84.0))
    g.openings.append(fp.OpeningItem(g, "window", "3648", 204.0))
    scene3.addItem(g)
    up = WallItem(QPointF(0, -44), QPointF(0, 244), "exterior")     # storey above
    up.floor = "upper"
    up.openings.append(fp.OpeningItem(up, "window", "6048", 144.0))
    scene3.addItem(up)
    e3 = rf3.gable_elevation(end=0)
    show("two storeys: ground + upper gable window", e3)
    render(e3, "gable_two_storeys.png", w=640, h=380)
    set_floor_state(elevations={})
    print("\nRENDER OK")


def _bare_scene():
    from PyQt6.QtWidgets import QGraphicsScene
    return QGraphicsScene()


if __name__ == "__main__":
    main()
