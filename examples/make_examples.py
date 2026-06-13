"""Generate the example plans and their rendered PNGs.

Run with:  python examples/make_examples.py
Produces, in this directory:
  simple_house.csv / .png   -- room import that fits the default canvas
  large_site.csv  / .png    -- room import that grows the canvas to fit
  sample_plan.json / .png   -- a native plan (walls + rooms + furnishings)

The PNGs are clean scene renders (no app chrome), so they double as a quick
visual reference for the file formats.
"""
import json
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QFont, QImage, QPainter
from PyQt6.QtWidgets import QApplication

import FloorPlanner as FP

os.environ.setdefault("QT_QPA_FONTDIR", str(FP.FONT_DIR))
app = QApplication([])
FP.load_fonts()
app.setFont(QFont(FP.FONT_FAMILY, 10))
F = FP.FOOT


def render(win, path):
    """Render the scene's content to a clean white PNG."""
    sc = win.scene
    sc.clearSelection()
    app.processEvents()
    rect = sc.itemsBoundingRect().adjusted(-F, -F, F, F)
    if rect.width() < 1 or rect.height() < 1:
        return
    scale = min(1600.0 / rect.width(), 1200.0 / rect.height(), 3.0)
    img = QImage(int(rect.width() * scale), int(rect.height() * scale),
                 QImage.Format.Format_ARGB32)
    img.fill(QColor("white"))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    sc.render(p, QRectF(0, 0, img.width(), img.height()), rect)
    p.end()
    img.save(path)
    print("wrote", os.path.relpath(path, ROOT), f"({img.width()}x{img.height()})")


def fresh():
    FP.SETTINGS.update(FP.DEFAULT_SETTINGS)
    win = FP.MainWindow()
    win.resize(1400, 900)
    return win


# ---------------------------------------------------------------------------
# 1. CSV import that fits the default 100' x 70' canvas
# ---------------------------------------------------------------------------
SIMPLE_CSV = """\
Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes
Living Room,Living Room,18,16,4,4,
Kitchen,Kitchen,12,12,24,8,
Bedroom,Bedroom,14,12,4,22,
Bath,Bathroom,8,8,20,24,
Garage,Garage,22,22,40,4,
"""
simple_csv = os.path.join(HERE, "simple_house.csv")
with open(simple_csv, "w", encoding="utf-8", newline="") as f:
    f.write(SIMPLE_CSV)
win = fresh()
win._import_rooms(simple_csv, interactive=False)
print("simple_house:", win._import_errors or "no errors")
render(win, os.path.join(HERE, "simple_house.png"))
win.close()


# ---------------------------------------------------------------------------
# 2. CSV import that needs a bigger canvas (a room sits past the default 100')
# ---------------------------------------------------------------------------
LARGE_CSV = """\
Name,Type,X_ft,Y_ft,X_loc_ft,Y_loc_ft,Notes
Main House,,40,30,5,5,
Workshop,Shop,30,24,60,5,
Barn,,40,30,110,5,Sits beyond the default 100' canvas - it grows to fit
"""
large_csv = os.path.join(HERE, "large_site.csv")
with open(large_csv, "w", encoding="utf-8", newline="") as f:
    f.write(LARGE_CSV)
win = fresh()
win._import_rooms(large_csv, interactive=False)
c = FP.canvas_rect()
print(f"large_site: {win._import_errors or 'no errors'} "
      f"| canvas now {c.width() / F:g}' x {c.height() / F:g}'")
render(win, os.path.join(HERE, "large_site.png"))
win.close()


# ---------------------------------------------------------------------------
# 3. A native JSON plan: walls + rooms + furnishings
# ---------------------------------------------------------------------------
win = fresh()
sc = win.scene
# 36' x 24' shell, split into living (left), kitchen (top-right),
# bedroom (bottom-right)
WALLS = [((0, 0), (432, 0), "exterior"), ((432, 0), (432, 288), "exterior"),
         ((432, 288), (0, 288), "exterior"), ((0, 288), (0, 0), "exterior"),
         ((216, 0), (216, 288), "interior"),
         ((216, 144), (432, 144), "interior")]
for p1, p2, t in WALLS:
    sc.addItem(FP.WallItem(QPointF(*p1), QPointF(*p2), t))
FP.rebuild_all_walls(sc)


def wall_at(p1, p2):
    for it in sc.items():
        if isinstance(it, FP.WallItem) and (
                (it.p1 - QPointF(*p1)).manhattanLength() < 1
                and (it.p2 - QPointF(*p2)).manhattanLength() < 1):
            return it
    raise LookupError((p1, p2))


# a front door and a couple of windows
front = FP.OpeningItem(wall_at((432, 288), (0, 288)), "door", "3680", 96,
                       )
front.door_type = "FRENCH"
wall_at((432, 288), (0, 288)).openings.append(front)
win_ = FP.OpeningItem(wall_at((0, 0), (432, 0)), "window", "4848", 108)
wall_at((0, 0), (432, 0)).openings.append(win_)
FP.rebuild_all_walls(sc)

for name, anchor, rtype in [("Living Room", (108, 200), "Living Room"),
                            ("Kitchen", (324, 72), "Kitchen"),
                            ("Bedroom", (324, 216), "Bedroom")]:
    res = FP.detect_room(sc, QPointF(*anchor))
    assert res is not None, name
    r = FP.RoomItem(name, QPointF(*anchor), res[0], res[1], corners=res[2])
    r.properties["room_type"] = rtype
    sc.addItem(r)

for kind, pos, rot in [("sofa", (108, 150), 0), ("coffee_table", (108, 196), 0),
                       ("tv_stand", (108, 60), 180),
                       ("refrigerator", (250, 40), 90),
                       ("dining_table", (340, 70), 0),
                       ("bed_queen", (330, 250), 0),
                       ("nightstand", (390, 250), 0)]:
    sc.addItem(FP.FurnishingItem(kind, QPointF(*pos), rot))

plan_json = os.path.join(HERE, "sample_plan.json")
with open(plan_json, "w", encoding="utf-8") as f:
    json.dump(win.serialize(), f, indent=2)
print("wrote", os.path.relpath(plan_json, ROOT))
render(win, os.path.join(HERE, "sample_plan.png"))
win.close()

print("done.")
