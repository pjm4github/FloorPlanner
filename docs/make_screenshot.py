import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)                       # writes docs/screenshot.png

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

import FloorPlanner as FP

os.environ.setdefault("QT_QPA_FONTDIR", str(FP.FONT_DIR))
app = QApplication([])
FP.load_fonts()
app.setFont(QFont(FP.FONT_FAMILY, 10))

win = FP.MainWindow()
sc = win.scene

# --- walls: 40' x 28' shell, bedroom / bath / office on the left ----------
W = [((0, 0), (480, 0), "exterior"), ((480, 0), (480, 336), "exterior"),
     ((480, 336), (0, 336), "exterior"), ((0, 336), (0, 0), "exterior"),
     ((192, 0), (192, 192), "interior"), ((0, 192), (192, 192), "interior"),
     ((96, 192), (96, 336), "interior")]
walls = []
for p1, p2, t in W:
    w = FP.WallItem(QPointF(*p1), QPointF(*p2), t)
    sc.addItem(w)
    walls.append(w)
FP.rebuild_all_walls(sc)


def wall_at(p1, p2):
    for w in walls:
        if (w.p1 - QPointF(*p1)).manhattanLength() < 1 and \
           (w.p2 - QPointF(*p2)).manhattanLength() < 1:
            return w
    raise LookupError((p1, p2))


def opening(w, kind, code, s, door_type="LH"):
    op = FP.OpeningItem(w, kind, code, s)
    op.door_type = door_type
    w.openings.append(op)
    w.rebuild()


opening(wall_at((192, 0), (192, 192)), "door", "3280", 156)      # bedroom
opening(wall_at((0, 192), (192, 192)), "door", "2880", 48)       # bath
opening(wall_at((96, 192), (96, 336)), "door", "2880", 72, "RH")  # office
opening(wall_at((0, 0), (480, 0)), "window", "3648", 96)
opening(wall_at((0, 0), (480, 0)), "window", "3648", 320)
opening(wall_at((480, 0), (480, 336)), "window", "4848", 160)
opening(wall_at((480, 336), (0, 336)), "window", "3648", 180)
opening(wall_at((480, 336), (0, 336)), "door", "3680", 400, "RH")

# --- rooms ------------------------------------------------------------------
def room(name, anchor, dims=False, sel=False):
    res = FP.detect_room(sc, QPointF(*anchor))
    assert res is not None, name
    path, area, corners = res
    r = FP.RoomItem(name, QPointF(*anchor), path, area, corners=corners)
    r.show_dims = dims
    sc.addItem(r)
    if sel:
        r.setSelected(True)
    return r


room("Bedroom", (96, 96), dims=True)
room("Bath", (48, 264))
room("Office", (144, 264))
room("Living Room", (336, 168), sel=True)

# --- furnishings -------------------------------------------------------------
F = [("bed_queen", (96, 78), 0), ("nightstand", (38, 26), 0),
     ("nightstand", (154, 26), 0), ("dresser", (120, 176), 180),
     ("bathtub", (20, 300), 0), ("toilet", (60, 212), 180),
     ("vanity", (62, 320), 180),
     ("desk", (150, 224), 0), ("office_chair", (150, 262), 180),
     ("bookshelf", (180, 320), 180),
     ("sofa", (320, 44), 0), ("coffee_table", (320, 102), 0),
     ("armchair", (236, 90), 75), ("tv_stand", (320, 168), 180),
     ("dining_table", (390, 252), 90),
     ("dining_chair", (352, 230), 270), ("dining_chair", (352, 274), 270),
     ("dining_chair", (428, 230), 90), ("dining_chair", (428, 274), 90),
     ("refrigerator", (456, 60), 90)]
for kind, pos, rot in F:
    sc.addItem(FP.FurnishingItem(kind, QPointF(*pos), rot))

# --- grab --------------------------------------------------------------------
win.resize(1500, 950)
win.show()
app.processEvents()
win.zoom_fit()
app.processEvents()
os.makedirs("docs", exist_ok=True)
win.grab().save("docs/screenshot.png")
print("saved docs/screenshot.png")
