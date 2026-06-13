import math
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

# --- walls -------------------------------------------------------------------
# 40' x 28' shell; bedroom / bath / shop left; garage wing right;
# sunroom below the living room
W = [((0, 0), (480, 0), "exterior"), ((480, 0), (480, 336), "exterior"),
     ((480, 336), (0, 336), "exterior"), ((0, 336), (0, 0), "exterior"),
     ((192, 0), (192, 192), "interior"), ((0, 192), (192, 192), "interior"),
     ((96, 192), (96, 336), "interior"),
     # garage 22' x 24', sharing the shell's right wall
     ((480, 48), (744, 48), "exterior"), ((744, 48), (744, 336), "exterior"),
     ((480, 336), (744, 336), "exterior"),
     # sunroom 24' x 20' below the living room
     ((192, 336), (192, 576), "exterior"),
     ((192, 576), (480, 576), "exterior"),
     ((480, 576), (480, 336), "exterior")]
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


def opening(w, kind, code, s, door_type="LH", swing=None):
    op = FP.OpeningItem(w, kind, code, s)
    op.door_type = door_type
    if swing is not None:
        op.swing = swing
    w.openings.append(op)
    w.rebuild()


opening(wall_at((192, 0), (192, 192)), "door", "3280", 156)      # bedroom
opening(wall_at((0, 192), (192, 192)), "door", "2880", 48)       # bath
opening(wall_at((96, 192), (96, 336)), "door", "2880", 72, "RH")  # shop
opening(wall_at((480, 0), (480, 336)), "door", "3280", 180)      # garage
opening(wall_at((480, 336), (0, 336)), "door", "3680", 144, "FRENCH")
opening(wall_at((0, 0), (480, 0)), "window", "3648", 96)
opening(wall_at((0, 0), (480, 0)), "window", "3648", 320)
opening(wall_at((0, 336), (0, 0)), "window", "4848", 168)
opening(wall_at((192, 576), (480, 576)), "window", "9648", 96)
opening(wall_at((192, 576), (480, 576)), "window", "9648", 200)
# double-wide garage door with its dashed overhead outline
opening(wall_at((480, 336), (744, 336)), "door", "19284", 132,
        "GARAGE-2", swing=-1)


# --- rooms ------------------------------------------------------------------
def room(name, anchor, rtype="", dims=False, sel=False):
    res = FP.detect_room(sc, QPointF(*anchor))
    assert res is not None, name
    r = FP.RoomItem(name, QPointF(*anchor), res[0], res[1], corners=res[2])
    if rtype:
        r.properties["room_type"] = rtype
    r.show_dims = dims
    sc.addItem(r)
    if sel:
        r.setSelected(True)
    return r


room("Bedroom", (96, 96), "Bedroom", dims=True)
room("Bath", (48, 264), "Bathroom")
room("Shop", (144, 264), "Shop")
room("Living Room", (336, 168), "Living Room")
room("Garage", (612, 192), "Garage")
room("Sunroom", (336, 456), "Sunroom")


# --- room operation: three rooms placed at uneven gaps, then spaced with
# equal gaps by Rooms ▸ Distribute horizontally
def _walled_room(x, y, w, h, name):
    for a, b in [((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
                 ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))]:
        sc.addItem(FP.WallItem(QPointF(*a), QPointF(*b), "interior"))
    FP.rebuild_all_walls(sc)
    res = FP.detect_room(sc, QPointF(x + w / 2, y + h / 2))
    r = FP.RoomItem(name, QPointF(x + w / 2, y + h / 2), res[0], res[1],
                    corners=res[2])
    sc.addItem(r)
    r.setSelected(True)
    return r


_d1 = _walled_room(500, 396, 56, 108, "Den")
_d2 = _walled_room(584, 396, 56, 108, "Study")    # uneven gaps to start
_d3 = _walled_room(664, 396, 56, 108, "Nook")
win._sel_order = [_d1, _d2, _d3]
win.distribute_rooms(horizontal=True)

# --- furnishings -------------------------------------------------------------
F = [("bed_queen", (96, 78), 0), ("nightstand", (38, 26), 0),
     ("nightstand", (154, 26), 0), ("dresser", (120, 176), 180),
     ("bathtub", (20, 300), 0), ("toilet", (60, 212), 180),
     ("vanity", (62, 320), 180),
     ("table_saw", (144, 240), 0), ("toolchest", (150, 318), 0),
     ("sofa", (320, 44), 0), ("coffee_table", (320, 102), 0),
     ("armchair", (236, 90), 75), ("tv_stand", (320, 160), 180),
     ("dining_table", (404, 250), 90),
     ("dining_chair", (366, 228), 270), ("dining_chair", (366, 272), 270),
     ("dining_chair", (442, 228), 90), ("dining_chair", (442, 272), 90),
     ("refrigerator", (456, 60), 90),
     ("suv", (560, 200), 0), ("bicycle", (706, 110), 0),
     ("workbench", (620, 70), 0), ("trashcan", (718, 310), 0),
     ("whirlpool", (428, 522), 0), ("lounge_chair", (222, 480), 0),
     ("lounge_chair", (258, 480), 0),
     # HVAC equipment tucked along the garage's left wall
     ("gas_furnace", (506, 100), 0), ("gas_water_heater", (506, 146), 0),
     ("electric_panel", (500, 64), 90), ("well_pump", (520, 250), 0),
     ("car_charger", (700, 252), 0)]
items = {}
for kind, pos, rot in F:
    it = FP.FurnishingItem(kind, QPointF(*pos), rot)
    sc.addItem(it)
    items.setdefault(kind, []).append(it)

# umbrella table grouped with the lounge chairs, then rotated to show the
# group's rotation handle and oriented (tilted) selection box
umb = FP.FurnishingItem("umbrella_table", QPointF(348, 460), 0)
sc.addItem(umb)
g = FP.GroupItem()
sc.addItem(g)
for it in [umb] + items["lounge_chair"]:
    g.adopt(it)
gc = g.childrenBoundingRect().center()
g._begin_rotation(QPointF(gc.x() + 100, gc.y()))
_ang = math.radians(22)
g._apply_rotation(QPointF(gc.x() + 100 * math.cos(_ang),
                          gc.y() + 100 * math.sin(_ang)), False)
g._finish_rotation()
g.setSelected(True)

# show the new HVAC palette section
names = [grp["name"] for grp in FP.furnishing_groups()]
win.furn_palette.setCurrentIndex(names.index("HVAC"))

# activate the one-shot Room Name tool: the toolbar highlights it and the
# status bar explains it reverts to Select (Ctrl-pick to keep it)
win.set_tool(FP.TOOL_ROOM)

# --- grab --------------------------------------------------------------------
win.resize(1500, 950)
win.show()
app.processEvents()
win.zoom_fit()
app.processEvents()
os.makedirs("docs", exist_ok=True)
win.grab().save("docs/screenshot.png")
print("saved docs/screenshot.png")
