"""Regenerate the feature gallery under docs/gallery/ (and the hero
docs/screenshot.png).

Builds one demo plan and captures a framed window shot per feature, plus a
few dialog shots.  Run with:  python docs/make_gallery.py
"""
import html
import math
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QFont, QPixmap, QTextCursor
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QVBoxLayout,
                             QWidget)

import FloorPlanner as FP

os.environ.setdefault("QT_QPA_FONTDIR", str(FP.FONT_DIR))
app = QApplication([])
app.setApplicationName(FP.APP_NAME)      # so About shows the real config path
FP.load_fonts()
app.setFont(QFont(FP.FONT_FAMILY, 10))
GALLERY = os.path.join("docs", "gallery")
os.makedirs(GALLERY, exist_ok=True)
KEEP = Qt.AspectRatioMode.KeepAspectRatio


def frame(win, name, rect=None, palette=None, select=None, tool=None,
          size=(1500, 950)):
    """Save a full-window shot of `win`, with the canvas fit to `rect`
    (scene coords) or zoom-fit when None."""
    win.resize(*size)
    win.show()
    app.processEvents()
    if palette is not None:
        names = [g["name"] for g in FP.furnishing_groups()]
        if palette in names:
            win.furn_palette.setCurrentIndex(names.index(palette))
    if tool is not None:
        win.set_tool(tool)
    win.scene.clearSelection()
    for it in select or []:
        it.setSelected(True)
    app.processEvents()
    if rect is None:
        win.zoom_fit()
    else:
        win.view.fitInView(QRectF(*rect), KEEP)
    app.processEvents()
    path = os.path.join(GALLERY, f"{name}.png")
    win.grab().save(path)
    print("saved", path)
    return path


def shot_widget(w, name, size=None):
    if size:
        w.resize(*size)
    w.show()
    app.processEvents()
    path = os.path.join(GALLERY, f"{name}.png")
    w.grab().save(path)
    print("saved", path)
    w.close()


# ---------------------------------------------------------------------------
# Build the demo plan
# ---------------------------------------------------------------------------
def build():
    FP.SETTINGS["cost_per_sqft"] = 225.0
    win = FP.MainWindow()
    sc = win.scene
    W = [((0, 0), (480, 0), "exterior"), ((480, 0), (480, 336), "exterior"),
         ((480, 336), (0, 336), "exterior"), ((0, 336), (0, 0), "exterior"),
         ((192, 0), (192, 192), "interior"), ((0, 192), (192, 192), "interior"),
         ((96, 192), (96, 336), "interior"),
         ((480, 48), (744, 48), "exterior"), ((744, 48), (744, 336),
                                              "exterior"),
         ((480, 336), (744, 336), "exterior"),
         ((192, 336), (192, 576), "exterior"),
         ((192, 576), (480, 576), "exterior"),
         ((480, 576), (480, 336), "exterior")]
    walls = [FP.WallItem(QPointF(*p1), QPointF(*p2), t) for p1, p2, t in W]
    for w in walls:
        sc.addItem(w)
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

    opening(wall_at((192, 0), (192, 192)), "door", "3280", 156)
    opening(wall_at((0, 192), (192, 192)), "door", "2880", 48)
    opening(wall_at((96, 192), (96, 336)), "door", "2880", 72, "RH")
    opening(wall_at((480, 0), (480, 336)), "door", "3280", 180)
    opening(wall_at((480, 336), (0, 336)), "door", "3680", 144, "FRENCH")
    opening(wall_at((0, 0), (480, 0)), "window", "3648", 96)
    opening(wall_at((0, 0), (480, 0)), "window", "3648", 320)
    opening(wall_at((0, 336), (0, 0)), "window", "4848", 168)
    opening(wall_at((192, 576), (480, 576)), "window", "9648", 96)
    opening(wall_at((192, 576), (480, 576)), "window", "9648", 200)
    opening(wall_at((480, 336), (744, 336)), "door", "19284", 132,
            "GARAGE-2", swing=-1)

    rooms = {}

    def room(name, anchor, rtype="", dims=False):
        res = FP.detect_room(sc, QPointF(*anchor))
        r = FP.RoomItem(name, QPointF(*anchor), res[0], res[1], corners=res[2])
        if rtype:
            r.properties["room_type"] = rtype
        r.show_dims = dims
        sc.addItem(r)
        FP.bind_room_walls(sc, r)
        rooms[name] = r
        return r

    room("Bedroom", (96, 96), "Bedroom", dims=True)
    room("Bath", (48, 264), "Bathroom")
    room("Shop", (144, 264), "Shop")
    room("Living Room", (336, 168), "Living Room")
    room("Garage", (612, 192), "Garage")
    room("Sunroom", (336, 456), "Sunroom")

    F = [("bed_queen", (96, 78), 0), ("nightstand", (38, 26), 0),
         ("nightstand", (154, 26), 0), ("dresser", (120, 176), 180),
         ("bathtub", (20, 300), 0), ("toilet", (60, 212), 180),
         ("vanity", (62, 320), 180),
         ("table_saw", (144, 240), 0), ("toolchest", (150, 318), 0),
         ("sofa", (320, 44), 0), ("coffee_table", (320, 102), 0),
         ("armchair", (236, 90), 75), ("tv_stand", (320, 160), 180),
         ("large_tv", (320, 151), 0),            # flat screen above the console
         ("gas_fireplace", (264, 10), 0),        # fireplace on the north wall
         ("dining_table", (404, 250), 90),
         ("dining_chair", (366, 228), 270), ("dining_chair", (366, 272), 270),
         ("dining_chair", (442, 228), 90), ("dining_chair", (442, 272), 90),
         ("buffet", (404, 327), 180),            # sideboard on the south wall
         ("hutch", (468, 250), 90),              # china hutch on the east wall
         ("refrigerator", (456, 60), 90),
         ("suv", (560, 200), 0), ("bicycle", (706, 110), 0),
         ("garden_tractor", (650, 215), 0),      # tractor parked by the car
         ("workbench", (620, 70), 0), ("trashcan", (718, 310), 0),
         ("whirlpool", (428, 522), 0), ("lounge_chair", (222, 480), 0),
         ("lounge_chair", (258, 480), 0),
         ("gas_furnace", (506, 100), 0), ("gas_water_heater", (506, 146), 0),
         ("electric_panel", (500, 64), 90), ("well_pump", (520, 250), 0),
         ("car_charger", (700, 252), 0)]
    prices = {"sofa": 1200, "dining_table": 900, "refrigerator": 2400,
              "bed_queen": 1500, "suv": 38000, "gas_furnace": 3200}
    items = {}
    for kind, pos, rot in F:
        it = FP.FurnishingItem(kind, QPointF(*pos), rot)
        it.price = float(prices.get(kind, 0))
        sc.addItem(it)
        items.setdefault(kind, []).append(it)

    umb = FP.FurnishingItem("umbrella_table", QPointF(348, 460), 0)
    sc.addItem(umb)
    grp = FP.GroupItem()
    sc.addItem(grp)
    for it in [umb] + items["lounge_chair"]:
        grp.adopt(it)
    gc = grp.childrenBoundingRect().center()
    grp._begin_rotation(QPointF(gc.x() + 100, gc.y()))
    ang = math.radians(22)
    grp._apply_rotation(QPointF(gc.x() + 100 * math.cos(ang),
                                gc.y() + 100 * math.sin(ang)), False)
    grp._finish_rotation()

    stair = FP.make_furnishing("stairs", QPointF(250, 250), 0)
    sc.addItem(stair)
    sc.addItem(FP.make_furnishing("elevator", QPointF(650, 288), 0))
    win._update_totals()
    win._commit_if_changed()
    return win, dict(rooms=rooms, items=items, group=grp, stair=stair)


def build_open_wall():
    """A small separate plan with one room whose right-bottom side is open."""
    win = FP.MainWindow()
    sc = win.scene
    for a, b in [((0, 0), (216, 0)), ((216, 0), (216, 168)),
                 ((216, 168), (0, 168)), ((0, 168), (0, 0))]:
        sc.addItem(FP.WallItem(QPointF(*a), QPointF(*b), "interior"))
    FP.rebuild_all_walls(sc)
    res = FP.detect_room(sc, QPointF(108, 84))
    r = FP.RoomItem("Great Room", QPointF(108, 84), res[0], res[1],
                    corners=res[2])
    sc.addItem(r)
    FP.bind_room_walls(sc, r)
    bottom = next(w for w in r.walls if not w.is_open
                  and abs(w.p1.y() - 168) < 1 and abs(w.p2.y() - 168) < 1)
    FP.detach_wall_from_room(sc, bottom)
    if abs(bottom.p1.x() - 216) < 1:           # leave the right half open
        bottom.p1 = QPointF(108, 168)
    else:
        bottom.p2 = QPointF(108, 168)
    bottom.rebuild()
    FP.rebuild_all_walls(sc)
    win._update_totals()
    return win, bottom


def build_coincident_door():
    """Two adjacent rooms that each own their own wall on the shared boundary
    (coincident party walls) with one door between them -- the plain wall
    opens for it, so there's a single clean door, never two stacked."""
    win = FP.MainWindow()
    sc = win.scene
    for a, b in [((0, 0), (144, 0)), ((144, 0), (144, 120)),
                 ((144, 120), (0, 120)), ((0, 120), (0, 0))]:
        sc.addItem(FP.WallItem(QPointF(*a), QPointF(*b), "interior"))
    FP.rebuild_all_walls(sc)
    res = FP.detect_room(sc, QPointF(72, 60))
    kit = FP.RoomItem("Kitchen", QPointF(72, 60), res[0], res[1],
                      corners=res[2])
    kit.properties["room_type"] = "Kitchen"
    sc.addItem(kit)
    FP.bind_room_walls(sc, kit)
    shared = next(w for w in kit.walls if not w.is_open
                  and abs(w.p1.x() - 144) < 1 and abs(w.p2.x() - 144) < 1)
    door = FP.OpeningItem(shared, "door", "3280", 60)
    shared.openings.append(door)
    FP.rebuild_all_walls(sc)
    for a, b in [((144, 0), (288, 0)), ((288, 0), (288, 120)),
                 ((288, 120), (144, 120))]:       # reuse the shared wall
        sc.addItem(FP.WallItem(QPointF(*a), QPointF(*b), "interior"))
    FP.rebuild_all_walls(sc)
    res = FP.detect_room(sc, QPointF(216, 60))
    din = FP.RoomItem("Dining", QPointF(216, 60), res[0], res[1],
                      corners=res[2])
    din.properties["room_type"] = "Dining Room"
    sc.addItem(din)
    FP.bind_room_walls(sc, din)                    # synthesizes its own copy
    win._update_totals()
    return win


def build_bathroom():
    """A master bath laid out with the two luxury walk-in showers (glass and
    tiled) plus a toilet and vanity, all at true scale."""
    win = FP.MainWindow()
    sc = win.scene
    for a, b in [((0, 0), (168, 0)), ((168, 0), (168, 108)),
                 ((168, 108), (0, 108)), ((0, 108), (0, 0))]:
        sc.addItem(FP.WallItem(QPointF(*a), QPointF(*b), "interior"))
    FP.rebuild_all_walls(sc)
    res = FP.detect_room(sc, QPointF(84, 54))
    r = FP.RoomItem("Master Bath", QPointF(84, 54), res[0], res[1],
                    corners=res[2])
    r.properties["room_type"] = "Bathroom"
    r.label_offset = QPointF(0, 24)                # clear of the showers
    sc.addItem(r)
    FP.bind_room_walls(sc, r)
    for kind, pos, rot in [("glass_shower", (40, 30), 0),
                           ("walk_in_shower", (128, 31), 0),
                           ("toilet", (24, 92), 0),
                           ("vanity_48", (108, 95), 0)]:   # double-vanity base
        sc.addItem(FP.FurnishingItem(kind, QPointF(*pos), rot))
    win._update_totals()
    return win


def build_kitchen():
    """A kitchen with a run of standard base cabinets (door bases, sink base,
    drawer base, corner lazy-susan), dashed wall cabinets above, a centre
    island with cabinets, and tall pantry cabinets -- all at true scale."""
    win = FP.MainWindow()
    sc = win.scene
    for a, b in [((0, 0), (192, 0)), ((192, 0), (192, 156)),
                 ((192, 156), (0, 156)), ((0, 156), (0, 0))]:
        sc.addItem(FP.WallItem(QPointF(*a), QPointF(*b), "interior"))
    FP.rebuild_all_walls(sc)
    res = FP.detect_room(sc, QPointF(96, 78))
    r = FP.RoomItem("Kitchen", QPointF(96, 78), res[0], res[1],
                    corners=res[2])
    r.properties["room_type"] = "Kitchen"
    r.label_offset = QPointF(60, 56)
    sc.addItem(r)
    FP.bind_room_walls(sc, r)
    units = [("corner_base_36", (18, 18), 0),      # base run along the back
             ("base_cab_36", (54, 12), 0), ("sink_base_36", (90, 12), 0),
             ("drawer_base_18", (117, 12), 0), ("base_cab_24", (138, 12), 0),
             ("wall_cab_36", (54, 6), 0),          # dashed wall cabinets above
             ("wall_cab_30", (90, 6), 0), ("wall_cab_24", (138, 6), 0),
             ("kitchen_island", (96, 84), 0),      # centre island w/ cabinets
             ("pantry_18", (15, 132), 0),          # tall pantry row
             ("pantry_24", (48, 132), 0), ("pantry_36", (93, 132), 0)]
    for kind, pos, rot in units:
        sc.addItem(FP.FurnishingItem(kind, QPointF(*pos), rot))
    win._update_totals()
    return win


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------
win, h = build()
rooms, items, group, stair = h["rooms"], h["items"], h["group"], h["stair"]

# 1. overview (also the README hero)
frame(win, "01-overview", palette="All", tool=FP.TOOL_SELECT)
win.grab().save("docs/screenshot.png")
print("saved docs/screenshot.png")

# 2. furnishings library at true scale + palette
frame(win, "02-furnishings", rect=(186, -16, 320, 360), palette="All")

# 3. doors & windows (front wall windows + double garage door)
frame(win, "03-doors-windows", rect=(360, 280, 400, 130), palette="All")

# 4. rooms: areas + dimension arrows on the bedroom
frame(win, "04-rooms", rect=(-16, -16, 230, 230), palette="All")

# 5. stairs (Framing) close-up
stair.setSelected(True)
frame(win, "05-stairs",
      rect=tuple(stair.sceneBoundingRect().adjusted(-90, -50, 150, 50)
                 .getRect()),
      palette="Framing", select=[stair])

# 6. groups + rotation (sunroom umbrella set, tilted selection box)
frame(win, "06-groups-rotation", rect=(196, 412, 300, 176), palette="Sunroom",
      select=[group])

# 7. HVAC equipment in the garage
frame(win, "07-hvac", rect=(486, 44, 270, 300), palette="HVAC")

# 8. open walls (separate small plan)
ow_win, ow_wall = build_open_wall()
frame(ow_win, "08-open-walls", rect=(-40, -40, 296, 248), palette="All",
      select=[ow_wall], size=(1100, 850))
ow_win.close()

# 9. coincident party wall opens for one door (no stacking)
cd_win = build_coincident_door()
frame(cd_win, "09-coincident-door", rect=(-36, -36, 360, 192), palette="All",
      tool=FP.TOOL_SELECT, size=(1100, 800))
cd_win.close()

# 10. bathroom fixtures: the glass and tiled luxury walk-in showers
bath_win = build_bathroom()
frame(bath_win, "10-bathroom", rect=(-30, -30, 228, 168), palette="Bathroom",
      tool=FP.TOOL_SELECT, size=(1100, 850))
bath_win.close()

# 11. kitchen cabinets: base cabinet run + tall pantry cabinets
kit_win = build_kitchen()
frame(kit_win, "11-kitchen", rect=(-24, -24, 240, 204), palette="Kitchen",
      tool=FP.TOOL_SELECT, size=(1100, 850))
kit_win.close()

# --- dialogs ----------------------------------------------------------------
# 12. total inventory table (Excel-ready)
rows = FP.total_inventory_rows(win.scene)
shot_widget(FP.InventoryDialog("Inventory — Total", FP.TOTAL_INV_HEADERS,
                               rows), "12-inventory", size=(560, 360))

# 13. AI furnishing-price dialog
shot_widget(FP.AIPricingDialog(), "13-ai-pricing", size=(640, 560))

# 14. Help → About (where files are stored)
shot_widget(FP.AboutDialog(), "14-about", size=(520, 320))


# 15. headless macro driver: a macro in, a rendered canvas snapshot out
def build_macro_demo():
    """Run a small macro through the in-app hook and render the result, the
    same way the fp_macro.py driver does headlessly."""
    macro = (
        "WALL 0 0 252 0 ext   WALL 252 0 252 180 ext\n"
        "WALL 252 180 0 180 ext   WALL 0 180 0 0 ext\n"
        "ROOM Studio 126 90   DOOR 126 0 3280   WINDOW 252 90 4848\n"
        "PLACE bed_queen 66 66 90   PLACE dresser 210 22 0\n"
        "PLACE sofa 168 150 0   PLACE armchair 60 150 0"
    )
    mwin = FP.MainWindow()
    mwin.prepare_headless()
    result = mwin.run_macro(macro)
    tmp = os.path.join(GALLERY, "_macro_tmp.png")
    mwin.export_canvas(tmp, scale=2.5)
    pm = QPixmap(tmp)
    os.remove(tmp)
    mwin.close()
    return macro, result, pm


def macro_widget(macro, result, pm):
    """Compose a 'macro in -> visualization out' card for the gallery."""
    c = result["counts"]
    summary = (
        '{ "ok": %s, "steps": %d,\n'
        '  "counts": { "walls": %d, "rooms": %d,\n'
        '              "furnishings": %d } }' % (
            "true" if result["ok"] else "false", result["steps"],
            c["walls"], c["rooms"], c["furnishings"]))
    term_html = (
        "<pre style=\"font-family:'DejaVu Sans Mono'; font-size:12px; "
        "margin:0; color:#e6e6e6;\">"
        "<span style='color:#8ae234;'>$ python fp_macro.py --svg studio.svg "
        "--out studio.json \\<br>&nbsp;&nbsp;&nbsp;&nbsp;--macro \"</span>"
        f"{html.escape(macro)}"
        "<span style='color:#8ae234;'>\"</span><br><br>"
        f"<span style='color:#aab2c0;'>{html.escape(summary)}</span>"
        "</pre>"
    )
    w = QWidget()
    w.setStyleSheet("background:#ffffff;")
    outer = QVBoxLayout(w)
    title = QLabel("Headless macro driver  ·  fp_macro.py")
    title.setStyleSheet("font-size:18px; font-weight:bold; color:#1f2937;"
                        " padding:6px 2px;")
    outer.addWidget(title)
    row = QHBoxLayout()
    term = QLabel(term_html)
    term.setStyleSheet("background:#1e1e2e; border-radius:8px; padding:14px;")
    term.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
    term.setFixedWidth(548)
    row.addWidget(term)
    right = QVBoxLayout()
    img = QLabel()
    img.setPixmap(pm.scaledToWidth(
        512, Qt.TransformationMode.SmoothTransformation))
    img.setStyleSheet("background:#ffffff; border:1px solid #cbd2dc;"
                      " border-radius:8px; padding:8px;")
    img.setAlignment(Qt.AlignmentFlag.AlignCenter)
    cap = QLabel("Rendered canvas snapshot — studio.svg / .png")
    cap.setStyleSheet("color:#6b7280; font-size:12px; padding-top:6px;")
    cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
    right.addWidget(img)
    right.addWidget(cap)
    row.addLayout(right)
    outer.addLayout(row)
    return w


_m_macro, _m_result, _m_pm = build_macro_demo()
shot_widget(macro_widget(_m_macro, _m_result, _m_pm), "15-macro-driver",
            size=(1150, 560))

# 16. macro recorder / debugger window (Macro ▸ Record / Debug…)
rec = FP.MacroRecorderDialog(win)
rec.edit.setPlainText(
    "E DRAG 0 0 252 0\n"
    "E DRAG 252 0 252 180\n"
    "E DRAG 252 180 0 180\n"
    "E DRAG 0 180 0 0\n"
    "R ROOM Studio 126 90\n"
    "W WINDOW 252 90 4848\n"
    'PUP 252 90 DOWN ENTER BACKSPACE TYPE "4466" ENTER\n'
    "PLACE bed_queen 66 66 90\n"
    "PLACE sofa 168 150 0")
rec.status_lbl.setText("Stopped.  Select macro text and Replay, or Save As….")
# select the PUP line so the Replay button reads as enabled in the shot
rec.edit.moveCursor(QTextCursor.MoveOperation.Start)
rec.edit.find('PUP 252 90 DOWN ENTER BACKSPACE TYPE "4466" ENTER')
rec._sync_buttons()
shot_widget(rec, "16-macro-recorder", size=(600, 440))

print("gallery complete")
