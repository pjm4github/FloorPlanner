#!/usr/bin/env python3
"""Build examples/site_demo.json -- a landscape design proving the v5 schema
carries garden work with no new object types: planting beds, a lawn zone and a
patio are ROOMS (areas, schedules, movable units); fences, hedges and retaining
walls are WALLS; a gate is an opening; a raised bed being trialled is a floating
concept room.  Boundaries with no built edge are simply open outline edges."""
import json
import math

V, W, R, F = [], [], [], []
LS = "LS"


def v(vid, x, y):
    V.append({"id": vid, "level": LS, "x": float(x), "y": float(y)})
    return vid


def w(wid, a, b, t, openings=None):
    W.append({"id": wid, "level": LS, "v1": a, "v2": b, "type": t,
              "left": None, "right": None, "openings": openings or []})
    return wid


#                     288                 720
#   (0,0) A ---------- P1 --------------- B (720,0)
#         |   PATIO    |    ROSE BED      |
#    192  P3 ...  J2 . J1 --retaining---- P2 (720,96)   <- y=96
#         |  VEG BED   |      LAWN        |
#   (0,480) D --gate-- P4 --------------- C (720,480)
for _vid, _x, _y in (("A", 0, 0), ("P1", 288, 0), ("B", 720, 0),
                     ("P2", 720, 96), ("J1", 288, 96), ("J2", 288, 192),
                     ("P3", 0, 192), ("C", 720, 480), ("P4", 288, 480),
                     ("D", 0, 480)):
    v(_vid, _x, _y)

w("wf1", "A", "P1", "fence")
w("wf2", "P1", "B", "fence")
w("wf3", "B", "P2", "fence")
w("wf4", "P2", "C", "fence")
w("wf5", "C", "P4", "fence")
w("wf6", "P4", "D", "fence",
  [{"id": "g1", "kind": "gate", "code": "4872",
    "anchor": {"from": "v2", "offset_in": 60.0}, "swings_toward": "left"}])
w("wf7", "D", "P3", "fence")
w("wf8", "P3", "A", "fence")
w("rw1", "J1", "P2", "retaining", None)
w("hg1", "J2", "P4", "hedge", None)
W[-2]["thickness_in"] = 8.0
W[-1]["thickness_in"] = 24.0


def room(rid, name, loop, props, cat="site", acc=None, state="placed"):
    r = {"id": rid, "level": LS, "name": name, "category": cat,
         "outline": [{"v": a, "wall": b} for a, b in loop],
         "placement": {"state": state, "rotation": 0.0, "extracted_from": None},
         "label": {"offset": [0, 0], "show_dimensions": True, "show_area": True},
         "properties": props}
    if acc:
        r["area_accounting"] = acc
    R.append(r)


room("rPatio", "Patio",
     [("A", "wf1"), ("P1", None), ("J1", None), ("J2", None), ("P3", "wf8")],
     {"surface": "Bluestone pavers", "edging": "Steel", "drainage": "Sheet to lawn",
      "sun_exposure": "part-shade", "notes": "Dining terrace off the great room"})
room("rRose", "Rose Bed",
     [("P1", "wf2"), ("B", "wf3"), ("P2", "rw1"), ("J1", None)],
     {"surface": "Planting soil", "irrigation": "Drip", "edging": "Steel",
      "sun_exposure": "full-sun", "slope_pct": 2.0,
      "plant_palette": ["Rosa 'New Dawn'", "Nepeta racemosa", "Salvia nemorosa"]})
room("rLawn", "Lawn",
     [("J1", "rw1"), ("P2", "wf4"), ("C", "wf5"), ("P4", "hg1"), ("J2", None)],
     {"surface": "Turf - tall fescue", "irrigation": "Rotor",
      "sun_exposure": "full-sun", "slope_pct": 1.5, "drainage": "Swale at east fence"})
room("rVeg", "Veg Beds",
     [("P3", None), ("J2", "hg1"), ("P4", "wf6"), ("D", "wf7")],
     {"surface": "Raised beds - cedar", "irrigation": "Drip",
      "sun_exposure": "full-sun",
      "plant_palette": ["Tomato", "Basil", "Rhubarb", "Espalier apple"]})

# ---- a raised bed being trialled: a floating CONCEPT room, private walls
for i, (x, y) in enumerate([(792, 0), (888, 0), (888, 48), (792, 48)]):
    v(f"c{i + 1}", x, y)
for i, (a, b) in enumerate([("c1", "c2"), ("c2", "c3"), ("c3", "c4"), ("c4", "c1")]):
    w(f"cw{i + 1}", a, b, "retaining")
    W[-1]["thickness_in"] = 6.0
room("rTrial", "Trial Bed",
     [("c1", "cw1"), ("c2", "cw2"), ("c3", "cw3"), ("c4", "cw4")],
     {"surface": "Planting soil", "sun_exposure": "full-sun",
      "notes": "8x4 raised bed - shuffling for the best spot"},
     cat="concept", state="floating")
R[-1]["nominal_size"] = {"width_in": 96, "depth_in": 48}

plants = [("shrub", 360, 48, "rRose"), ("shrub", 470, 48, "rRose"),
          ("tree", 600, 300, "rLawn"), ("bench", 140, 96, "rPatio"),
          ("planter", 240, 150, "rPatio"), ("shrub", 100, 300, "rVeg"),
          ("shrub", 840, 24, "rTrial")]
for i, (kind, x, y, owner) in enumerate(plants):
    F.append({"id": f"fu{i + 1}", "level": LS, "kind": kind, "room": owner,
              "pos": [float(x), float(y)], "rotation": 0.0,
              "state": {"species": "TBD", "spread_in": 48}})

doc = {"format": "floorplanner-design", "version": 5, "units": "inches",
       "settings": {"name": "Site demo", "canvas_w_in": 1000, "canvas_h_in": 560,
                    "vertex_weld_in": 0.6, "area_basis": "centerline",
                    "editing": {"shuffle": True, "auto_coalesce": False,
                                "auto_weld": False, "auto_bind": False}},
       "levels": [{"id": LS, "name": "Site", "elevation_in": 0.0,
                   "height_in": 96.0, "kind": "site", "reference": False}],
       "vertices": V, "walls": W, "rooms": R, "furnishings": F, "groups": []}

# left/right from outline winding, same rule the migrator uses
pos = {x["id"]: (x["x"], x["y"]) for x in V}
wmap = {x["id"]: x for x in W}


def pip(q, pts):
    x, y = q
    ins = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


for r in R:
    pts = [pos[e["v"]] for e in r["outline"]]
    n = len(pts)
    for i, e in enumerate(r["outline"]):
        if not e["wall"]:
            continue
        a, b = pos[e["v"]], pos[r["outline"][(i + 1) % n]["v"]]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        probe = ((a[0] + b[0]) / 2 + dy / L * 2, (a[1] + b[1]) / 2 - dx / L * 2)
        side = "left" if pip(probe, pts) else "right"
        if wmap[e["wall"]]["v1"] != e["v"]:
            side = "right" if side == "left" else "left"
        wmap[e["wall"]][side] = r["id"]

json.dump(doc, open("site_demo.json", "w"), indent=1)
print("wrote site_demo.json")
