"""Cabinets and appliances as PARTS -- pure Python, the ONE calculator.

NO Qt AND NO `floorplanner` IMPORT, on purpose: the 3D viewer and the asset
generator both load this file BY PATH (as they do `stair_geometry.py`), so
the 3D solid, the properties dialog's preview and -- later -- the camera
elevation all draw the same doors, drawers, toe kick and countertop.

A cabinet is a list of `Part`s. Each is an upright prism over a plan
quadrilateral, with a ROLE ("cabinet", "countertop", "hardware", ...) rather
than a colour: `resolve_materials` turns roles into materials from the
cabinet's own choices, else its ROOM'S STYLE, else the defaults. That order
is the whole style feature -- restyle the room and every cabinet in it that
was not overridden follows.

LOCAL COORDINATES (inches). `x` runs across the cabinet, 0 at its centre.
`f` is distance out from the WALL: 0 at the back, the cabinet's depth at its
front. `z` is height above the FLOOR of its level (so a wall cabinet's parts
start at its mounting height). The plan symbol is drawn back-up, so a viewer
maps `f` to its own local y as `depth / 2 - f`.

Dimensions are the trade's, not invented here: a 34.5 in base box on a 4.5 in
toe kick set 3 in back, under a 1.5 in top; 12 in deep wall cabinets hung
18 in above the counter; 21 in deep vanities; 3 in width modules
(docs/furnishing-spec/CABINETS_AND_ROOM_STYLE_PLAN.md sec 2, with sources).
"""
import math
from dataclasses import dataclass

# --------------------------------------------------------------------------
# the style vocabulary -- one table per choice: (key, label, material)
# --------------------------------------------------------------------------
FINISHES = (
    ("modern_white", "Modern white", "cab_white"),
    ("maple", "Maple", "cab_maple"),
    ("cherry", "Cherry", "cab_cherry"),
    ("oak", "Oak", "cab_oak"),
    ("walnut", "Walnut", "cab_walnut"),
    ("espresso", "Espresso", "cab_espresso"),
    ("grey", "Painted grey", "cab_grey"),
    ("navy", "Painted navy", "cab_navy"),
    ("sage", "Painted sage", "cab_sage"),
)
COUNTERTOPS = (
    ("marble", "Marble", "ct_marble"),
    ("tile", "Tile", "ct_tile"),
    ("quartz", "Quartz", "ct_quartz"),
    ("granite", "Granite", "ct_granite"),
    ("soapstone", "Soapstone", "ct_soapstone"),
    ("laminate", "Laminate", "ct_laminate"),
    ("butcher_block", "Butcher block", "ct_butcher_block"),
    ("concrete", "Concrete", "ct_concrete"),
    ("stainless", "Stainless steel", "ct_stainless"),
)
HARDWARE = (
    ("brushed_nickel", "Brushed nickel", "hw_brushed_nickel"),
    ("chrome", "Chrome", "hw_chrome"),
    ("matte_black", "Matte black", "hw_matte_black"),
    ("brass", "Brass", "hw_brass"),
)
DOOR_STYLES = (("slab", "Slab"), ("shaker", "Shaker (recessed panel)"),
               ("raised", "Raised panel"), ("glass", "Glass front"))
SHEENS = (("matte", "Matte"), ("gloss", "Gloss"), ("gel_coat", "Gel coat"))
COLOURS = (
    ("white", "White", "#f2f2ee"), ("cream", "Cream", "#e9dfc6"),
    ("black", "Black", "#19191b"), ("slate", "Slate", "#4b5560"),
    ("red", "Red", "#a3211c"), ("navy", "Navy", "#1f2f52"),
    ("sage", "Sage", "#8a9a7b"), ("yellow", "Yellow", "#d9b53a"),
    ("copper", "Copper", "#a8623a"), ("sky", "Sky blue", "#7fa8c9"),
    ("silver", "Silver", "#c3c6ca"),
)
# A washer or a dryer comes in gloss white, silver or black (Patrick, 2026-11-15).
LAUNDRY_COLOURS = ("white", "silver", "black")
# What a light gives off: (key, label, colour).  The first four are white
# light by colour temperature; the rest are colours.
LIGHT_COLOURS = (
    ("warm_white", "Warm white (2700 K)", "#ffd9a8"),
    ("soft_white", "Soft white (3000 K)", "#ffe4bf"),
    ("neutral", "Neutral white (4000 K)", "#fff3e0"),
    ("daylight", "Daylight (5000 K)", "#f4f8ff"),
    ("amber", "Amber", "#ffb347"), ("red", "Red", "#ff4a3d"),
    ("green", "Green", "#5fe37a"), ("blue", "Blue", "#5a8cff"),
    ("purple", "Purple", "#b072ff"),
)
FIXTURES = (("recessed", "Recessed can"), ("flush", "Flush mount"),
            ("pendant", "Pendant"), ("linear", "Linear / strip"),
            ("sconce", "Wall sconce"), ("globe", "Globe"),
            ("table", "Table lamp"))
# What can stand under an island: (code, label, width, type, overrides).
ISLAND_SLOTS = (
    ("none", "\u2014 empty \u2014", 0.0, None, {}),
    ("B12", "Base 12 in", 12.0, "base", {"front": "doors"}),
    ("B15", "Base 15 in", 15.0, "base", {}),
    ("B18", "Base 18 in", 18.0, "base", {}),
    ("B24", "Base 24 in", 24.0, "base", {}),
    ("B30", "Base 30 in", 30.0, "base", {}),
    ("B36", "Base 36 in", 36.0, "base", {}),
    ("DB18", "Drawer base 18 in", 18.0, "base", {"front": "drawers"}),
    ("DB24", "Drawer base 24 in", 24.0, "base", {"front": "drawers"}),
    ("DB30", "Drawer base 30 in", 30.0, "base", {"front": "drawers"}),
    ("SB30", "Sink base 30 in", 30.0, "sink_base", {"sink": "single"}),
    ("SB36", "Sink base 36 in", 36.0, "sink_base", {"sink": "double"}),
    ("DW24", "Dishwasher 24 in", 24.0, "appliance", {"appliance": "dishwasher"}),
    # 0338
    ("BS18", "Bar sink base 18 in", 18.0, "sink_base", {"sink": "single"}),
    ("BS24", "Bar sink base 24 in", 24.0, "sink_base", {"sink": "single"}),
    ("CT30", "Cooktop over drawers 30 in", 30.0, "base",
     {"front": "drawers", "cooktop": True}),
    ("CT36", "Cooktop over drawers 36 in", 36.0, "base",
     {"front": "drawers", "cooktop": True}),
    ("RG30", "Range 30 in", 30.0, "appliance", {"appliance": "range"}),
    ("WC15", "Wine cooler 15 in", 15.0, "appliance", {"appliance": "wine_cooler"}),
    ("WC24", "Wine cooler 24 in", 24.0, "appliance", {"appliance": "wine_cooler"}),
    ("MW24", "Microwave drawer 24 in", 24.0, "appliance",
     {"appliance": "microwave_drawer"}),
)
# 0338: fixtures built from parts -- what each is, and what its dialog offers.
FIXTURE_MODELS = ("toilet", "bathtub", "bookshelf", "fireplace", "grab_bar",
                  "desk", "office_chair", "office_set",
                  "pedal_bin", "dog_crate", "sofa_table")
COMPUTERS = (("desktop", "Monitor, keyboard and mouse"),
             ("dual", "Two monitors, keyboard and mouse"),
             ("laptop", "Laptop"), ("none", "None"))
PEDESTALS = (("right", "Drawers on the right"), ("left", "Drawers on the left"),
             ("both", "Drawers both sides"), ("none", "No drawers"))
DESK_TOP_T = 1.5
SET_DESK_D = 24.0              # the desk of a desk-and-chair set
CHAIR = 24.0                   # an office chair's footprint, square
CHAIR_SEAT_Z = 19.0
FIXTURE_COLOURS = ("white", "cream", "black", "slate")
SURROUNDS = (("stone", "Stone", "stone"), ("brick", "Brick", "fp_brick"),
             ("marble", "Marble", "ct_marble"), ("tile", "Tile", "ct_tile"),
             ("white", "Painted white", "cab_white"))
BAR_DIAMETER = 1.25            # a grab bar, and its clear space off the wall
BAR_CLEAR = 1.5
ISLAND_SLOT_KEYS = tuple(f"slot_{i}" for i in range(1, 7))
ISLAND_CABINET_D = 24.0        # the cabinets under an island
ISLAND_FRONT_SETBACK = 1.6     # the top overhangs the door side by this much
STOOL = 13.0                   # a counter stool's seat, square
STOOL_SEAT_Z = 24.0            # for a 36 in counter
ROOM = "room"                 # the choice "take it from the room's style"

DEFAULT_STYLE = {"cabinet_finish": "maple", "door_style": "shaker",
                 "countertop": "quartz", "hardware": "brushed_nickel",
                 "backsplash": "countertop"}
STYLE_KEYS = tuple(DEFAULT_STYLE)

# Colour, roughness, metalness -- ONCE, here; `_gen_assets.py` writes these
# into materials.json beside the others.
MATERIALS = {
    "cab_white":    {"colour": [0.93, 0.93, 0.91, 1.0], "roughness": 0.45, "metalness": 0.0},
    "cab_maple":    {"colour": [0.80, 0.64, 0.42, 1.0], "roughness": 0.55, "metalness": 0.0},
    "cab_cherry":   {"colour": [0.48, 0.21, 0.13, 1.0], "roughness": 0.50, "metalness": 0.0},
    "cab_oak":      {"colour": [0.66, 0.49, 0.29, 1.0], "roughness": 0.60, "metalness": 0.0},
    "cab_walnut":   {"colour": [0.33, 0.22, 0.15, 1.0], "roughness": 0.55, "metalness": 0.0},
    "cab_espresso": {"colour": [0.17, 0.12, 0.10, 1.0], "roughness": 0.50, "metalness": 0.0},
    "cab_grey":     {"colour": [0.55, 0.57, 0.58, 1.0], "roughness": 0.50, "metalness": 0.0},
    "cab_navy":     {"colour": [0.13, 0.19, 0.32, 1.0], "roughness": 0.50, "metalness": 0.0},
    "cab_sage":     {"colour": [0.54, 0.60, 0.49, 1.0], "roughness": 0.50, "metalness": 0.0},
    "cabinet_kick": {"colour": [0.10, 0.10, 0.10, 1.0], "roughness": 0.80, "metalness": 0.0},
    "cabinet_glass": {"colour": [0.70, 0.80, 0.84, 1.0], "roughness": 0.08, "metalness": 0.2},
    "mirror_glass":  {"colour": [0.78, 0.82, 0.85, 1.0], "roughness": 0.04, "metalness": 0.95},
    "ct_marble":    {"colour": [0.91, 0.91, 0.89, 1.0], "roughness": 0.20, "metalness": 0.0},
    "ct_tile":      {"colour": [0.80, 0.77, 0.70, 1.0], "roughness": 0.35, "metalness": 0.0},
    "ct_quartz":    {"colour": [0.84, 0.84, 0.82, 1.0], "roughness": 0.25, "metalness": 0.0},
    "ct_granite":   {"colour": [0.33, 0.31, 0.30, 1.0], "roughness": 0.30, "metalness": 0.0},
    "ct_soapstone": {"colour": [0.22, 0.25, 0.25, 1.0], "roughness": 0.60, "metalness": 0.0},
    "ct_laminate":  {"colour": [0.72, 0.68, 0.60, 1.0], "roughness": 0.55, "metalness": 0.0},
    "ct_butcher_block": {"colour": [0.70, 0.50, 0.29, 1.0], "roughness": 0.60, "metalness": 0.0},
    "ct_concrete":  {"colour": [0.56, 0.56, 0.54, 1.0], "roughness": 0.80, "metalness": 0.0},
    "ct_stainless": {"colour": [0.70, 0.72, 0.74, 1.0], "roughness": 0.30, "metalness": 0.90},
    "hw_brushed_nickel": {"colour": [0.68, 0.67, 0.64, 1.0], "roughness": 0.40, "metalness": 0.9},
    "hw_chrome":    {"colour": [0.82, 0.83, 0.85, 1.0], "roughness": 0.12, "metalness": 1.0},
    "hw_matte_black": {"colour": [0.07, 0.07, 0.08, 1.0], "roughness": 0.75, "metalness": 0.3},
    "hw_brass":     {"colour": [0.76, 0.60, 0.26, 1.0], "roughness": 0.30, "metalness": 0.9},
    # An appliance's CUSTOM finish is a sheen plus a colour. The sheen is a
    # material here (its roughness and metalness); the colour rides on the
    # name as "#rrggbb" and replaces the white below.
    "sheen_matte":  {"colour": [1.0, 1.0, 1.0, 1.0], "roughness": 0.90, "metalness": 0.0},
    "sheen_gloss":  {"colour": [1.0, 1.0, 1.0, 1.0], "roughness": 0.12, "metalness": 0.1},
    "sheen_gel_coat": {"colour": [1.0, 1.0, 1.0, 1.0], "roughness": 0.22, "metalness": 0.05},
    # 0333: stools, and lights.  A light's LENS takes the light's own colour
    # the same way a custom appliance does: "light_emit#rrggbb".
    "stool_seat":    {"colour": [0.20, 0.15, 0.12, 1.0], "roughness": 0.70, "metalness": 0.0},
    "light_fixture": {"colour": [0.90, 0.90, 0.88, 1.0], "roughness": 0.45, "metalness": 0.2},
    "light_emit":    {"colour": [1.0, 1.0, 1.0, 1.0], "roughness": 0.30, "metalness": 0.0},
    "fp_brick":      {"colour": [0.58, 0.27, 0.20, 1.0], "roughness": 0.85, "metalness": 0.0},
    "fp_hearth":     {"colour": [0.22, 0.22, 0.23, 1.0], "roughness": 0.60, "metalness": 0.0},
    "fp_firebox":    {"colour": [0.07, 0.07, 0.07, 1.0], "roughness": 0.90, "metalness": 0.0},
    "fp_log":        {"colour": [0.30, 0.20, 0.13, 1.0], "roughness": 0.90, "metalness": 0.0},
    "screen_glass":  {"colour": [0.09, 0.13, 0.20, 1.0], "roughness": 0.10, "metalness": 0.1},
    "book_1":        {"colour": [0.55, 0.16, 0.14, 1.0], "roughness": 0.70, "metalness": 0.0},
    "book_2":        {"colour": [0.15, 0.27, 0.45, 1.0], "roughness": 0.70, "metalness": 0.0},
    "book_3":        {"colour": [0.20, 0.38, 0.26, 1.0], "roughness": 0.70, "metalness": 0.0},
    "book_4":        {"colour": [0.80, 0.72, 0.52, 1.0], "roughness": 0.70, "metalness": 0.0},
    "book_5":        {"colour": [0.28, 0.24, 0.24, 1.0], "roughness": 0.70, "metalness": 0.0},
}

# --------------------------------------------------------------------------
# the trade's dimensions
# --------------------------------------------------------------------------
BASE_BOX_H = 34.5
TOP_T = 1.5
KICK_H, KICK_D = 4.5, 3.0
DOOR_T = 0.75
STILE_W = 2.25                 # a five-piece door's stiles and rails
DRAWER_H = 6.0                 # the top drawer front, over doors
REVEAL = {"full": 0.125, "partial": 1.0}
WALL_UNDERSIDE = 54.0          # 36 in counter + 18 in backsplash
CORNER_LEG = 24.0
# 0368
COUNTER_H = BASE_BOX_H + TOP_T  # 36: where a unit standing on a base unit starts
DESK_BOX_H = 28.5              # a kitchen desk: 30 in to the top of its counter
DESK_DRAWER_H = 4.5            # the one shallow drawer under a desk's top
PANEL_T = 0.75                 # an end panel, a cap, a light rail

TYPES = ("base", "sink_base", "corner_base", "wall", "tall", "appliance",
         "island", "light", "fixture", "mirror",
         "kitchen_desk", "corner_wall", "suspended")

# Every catalog kind this file builds, with what it is born as. The generator
# writes each into the manifest (`cabinet`), refusing if a size here disagrees
# with the catalog's own.
PRESETS = {
    "base_cab_24": {"type": "base", "width_in": 24, "depth_in": 24},
    "base_cab_36": {"type": "base", "width_in": 36, "depth_in": 24},
    "drawer_base_18": {"type": "base", "width_in": 18, "depth_in": 24,
                       "front": "drawers", "drawers": 3},
    "sink_base_36": {"type": "sink_base", "width_in": 36, "depth_in": 24,
                     "sink": "double"},
    "corner_base_36": {"type": "corner_base", "width_in": 36, "depth_in": 36},
    "pantry_18": {"type": "tall", "width_in": 18, "depth_in": 24, "height_in": 84},
    "pantry_24": {"type": "tall", "width_in": 24, "depth_in": 24, "height_in": 84},
    "pantry_36": {"type": "tall", "width_in": 36, "depth_in": 24, "height_in": 84},
    "wall_cab_24": {"type": "wall", "width_in": 24, "depth_in": 12, "height_in": 30},
    "wall_cab_30": {"type": "wall", "width_in": 30, "depth_in": 12, "height_in": 30},
    "wall_cab_36": {"type": "wall", "width_in": 36, "depth_in": 12, "height_in": 30},
    # 0368. A tall unit of any width, one to four doors across: 84 in, the top
    # of a wall cabinet. `stands` puts it on the floor or on a base unit's
    # counter; either way it tops out with the wall cabinets.
    "tall_cab": {"type": "tall", "width_in": 24, "depth_in": 24, "height_in": 84},
    # the room's countertop at desk height, one shallow full-width drawer
    "kitchen_desk": {"type": "kitchen_desk", "width_in": 48, "depth_in": 24,
                     "height_in": DESK_BOX_H},
    # a corner WALL cabinet: two wings, `width_in` along the wall behind and
    # `wing_in` along the side wall, each `depth_in` deep
    "corner_wall_cab": {"type": "corner_wall", "width_in": 24, "wing_in": 24,
                        "depth_in": 12, "height_in": 30},
    # hung from the ceiling over an island: its height is its room's ceiling
    "ceiling_cab": {"type": "suspended", "width_in": 48, "depth_in": 15,
                    "height_in": 24},
    "vanity": {"type": "sink_base", "width_in": 30, "depth_in": 21,
               "height_in": 32.5, "sink": "single", "sink_material": "porcelain"},
    "vanity_24": {"type": "sink_base", "width_in": 24, "depth_in": 21,
                  "height_in": 32.5, "sink": "single", "sink_material": "porcelain"},
    "vanity_36": {"type": "sink_base", "width_in": 36, "depth_in": 21,
                  "height_in": 32.5, "sink": "single", "sink_material": "porcelain"},
    "vanity_48": {"type": "sink_base", "width_in": 48, "depth_in": 21,
                  "height_in": 32.5, "sink": "double", "sink_material": "porcelain"},
    "medicine_cabinet": {"type": "mirror", "width_in": 30, "has_cabinet": True,
                         "light_style": "bar"},
    "vanity_mirror": {"type": "mirror", "width_in": 36, "has_cabinet": False,
                      "light_style": "backlit"},
    "refrigerator": {"type": "appliance", "appliance": "refrigerator",
                     "width_in": 36, "depth_in": 30, "height_in": 70},
    "range": {"type": "appliance", "appliance": "range",
              "width_in": 30, "depth_in": 26, "height_in": 36},
    "dishwasher": {"type": "appliance", "appliance": "dishwasher",
                   "width_in": 24, "depth_in": 24, "height_in": 34},
    # gloss white by default; silver or black from the dialog
    "washer": {"type": "appliance", "appliance": "washer",
               "width_in": 27, "depth_in": 30, "height_in": 38,
               "finish_mode": "custom", "sheen": "gloss", "colour": "white"},
    "dryer": {"type": "appliance", "appliance": "dryer",
              "width_in": 27, "depth_in": 30, "height_in": 38,
              "finish_mode": "custom", "sheen": "gloss", "colour": "white"},
    # 0333: over the range.  Both hang on the wall: `floor_to_bottom_in`.
    "range_hood": {"type": "appliance", "appliance": "hood", "wall_mounted": True,
                   "width_in": 30, "depth_in": 20, "height_in": 18,
                   "floor_to_bottom_in": 66},
    "microwave_otr": {"type": "appliance", "appliance": "microwave",
                      "wall_mounted": True, "width_in": 30, "depth_in": 16,
                      "height_in": 17, "floor_to_bottom_in": 54},
    # An island: cabinets and appliances in SLOTS along one side, stools along
    # the other, one countertop over all of it.
    "kitchen_island": {"type": "island", "width_in": 72, "depth_in": 39,
                       "slot_1": "B36", "slot_2": "B36", "seats": 3},
    "island_sink": {"type": "island", "width_in": 84, "depth_in": 42,
                    "slot_1": "B24", "slot_2": "SB36", "slot_3": "DW24",
                    "seats": 3},
    # Lights.  A fixture's shape, colour and output are parameters; ceiling
    # fixtures hang from the ceiling of the room they are placed in.
    "light_recessed": {"type": "light", "fixture": "recessed", "width_in": 6,
                       "depth_in": 6, "size_in": 6, "beam": "spot"},
    "light_flush": {"type": "light", "fixture": "flush", "width_in": 14,
                    "depth_in": 14, "size_in": 14},
    "light_pendant": {"type": "light", "fixture": "pendant", "width_in": 12,
                      "depth_in": 12, "size_in": 12, "drop_in": 30},
    "light_linear": {"type": "light", "fixture": "linear", "width_in": 48,
                     "depth_in": 6, "size_in": 48},
    "light_sconce": {"type": "light", "fixture": "sconce", "width_in": 6,
                     "depth_in": 5, "size_in": 6, "floor_to_bottom_in": 66},
    # 0338: fixtures.  `model` says which; the kind decides it, never the file.
    "toilet": {"type": "fixture", "model": "toilet", "width_in": 20,
               "depth_in": 28, "height_in": 30},
    "bathtub": {"type": "fixture", "model": "bathtub", "width_in": 30,
                "depth_in": 60, "height_in": 20},
    "bookshelf": {"type": "fixture", "model": "bookshelf", "width_in": 36,
                  "depth_in": 12, "height_in": 72},
    "gas_fireplace": {"type": "fixture", "model": "fireplace", "width_in": 48,
                      "depth_in": 20, "height_in": 40},
    "grab_bar": {"type": "fixture", "model": "grab_bar", "wall_mounted": True,
                 "width_in": 24, "depth_in": 3.5, "height_in": 3,
                 "length_in": 24, "floor_to_bottom_in": 32},
    # 0340: the office.  `height_in` is the DESK top; a chair's is its back.
    "desk": {"type": "fixture", "model": "desk", "width_in": 60,
             "depth_in": 30, "height_in": 30},
    "office_chair": {"type": "fixture", "model": "office_chair",
                     "width_in": 24, "depth_in": 24, "height_in": 40,
                     "colour": "black"},
    "office_set": {"type": "fixture", "model": "office_set", "width_in": 54,
                   "depth_in": 36, "height_in": 30, "colour": "black"},
    # 0341
    "pedal_bin": {"type": "fixture", "model": "pedal_bin", "width_in": 13,
                  "depth_in": 16, "height_in": 24},
    "dog_crate": {"type": "fixture", "model": "dog_crate", "width_in": 36,
                  "depth_in": 24, "height_in": 26, "colour": "slate"},
    "sofa_table": {"type": "fixture", "model": "sofa_table", "width_in": 48,
                   "depth_in": 14, "height_in": 30, "shelves": 1},
    # a lamp STANDS ON something: `floor_to_bottom_in` is that surface
    "table_lamp": {"type": "light", "fixture": "table", "width_in": 12,
                   "depth_in": 12, "size_in": 12, "floor_to_bottom_in": 30,
                   "drop_in": 22},
}

_TYPE_DEFAULTS = {
    "base": {"height_in": BASE_BOX_H, "front": "drawer_over_doors", "top_on": True},
    "sink_base": {"height_in": BASE_BOX_H, "front": "false_front", "top_on": True,
                  "sink": "single"},
    "corner_base": {"height_in": BASE_BOX_H, "front": "doors", "top_on": True,
                    "corner_type": "diagonal"},
    "wall": {"height_in": 30.0, "front": "doors", "top_on": False,
             "floor_to_bottom_in": WALL_UNDERSIDE},
    "tall": {"height_in": 84.0, "front": "doors", "top_on": False},
    "appliance": {"height_in": 36.0, "front": "doors", "top_on": False},
    "island": {"height_in": BASE_BOX_H, "front": "drawer_over_doors",
               "top_on": True},
    "light": {"height_in": 6.0, "top_on": False},
    "fixture": {"height_in": 30.0, "top_on": False},
    # a bathroom mirror / medicine cabinet, hung over a vanity
    "mirror": {"height_in": 36.0, "depth_in": 4.5, "top_on": False,
               "floor_to_bottom_in": 40.0},
    # 0368
    "kitchen_desk": {"height_in": DESK_BOX_H, "front": "drawers", "top_on": True,
                     "toe_kick_h_in": 0.0, "toe_kick_d_in": 0.0},
    "corner_wall": {"height_in": 30.0, "depth_in": 12.0, "front": "doors",
                    "top_on": False, "floor_to_bottom_in": WALL_UNDERSIDE},
    "suspended": {"height_in": 24.0, "depth_in": 15.0, "front": "doors",
                  "top_on": False, "drop_in": 0.0},
}

STATE_DEFAULTS = {
    "width_in": 24.0, "depth_in": 24.0, "height_in": BASE_BOX_H,
    "toe_kick_h_in": KICK_H, "toe_kick_d_in": KICK_D,
    "front": "drawer_over_doors", "doors": "auto", "drawers": 3,
    "hinge": "left", "door_style": ROOM, "overlay": "full", "pulls": "bar",
    "finish": ROOM, "hardware": ROOM,
    "top_on": True, "top_thickness_in": TOP_T, "top_overhang_in": 1.0,
    "top_material": ROOM, "backsplash_in": 0.0,
    "floor_to_bottom_in": WALL_UNDERSIDE,
    "sink": "none", "sink_material": "metal", "sink_side": "center",
    "corner_type": "diagonal", "hand": "left",
    # 0368: a tall unit's footing; a corner wall cabinet's second wing; a
    # ceiling cabinet's door sides and the light under it
    "stands": "floor", "wing_in": CORNER_LEG, "door_sides": "both",
    "under_light": True,
    "appliance": "generic", "finish_mode": "standard", "sheen": "gloss",
    "colour": "white", "wall_mounted": False,
    # island
    "slot_1": "none", "slot_2": "none", "slot_3": "none", "slot_4": "none",
    "slot_5": "none", "slot_6": "none", "seats": 0,
    # light
    "fixture": "flush", "light_colour": "soft_white", "lumens": 800.0,
    "size_in": 12.0, "drop_in": 30.0, "beam": "wide",
    # fixture
    "model": "toilet", "shelves": 4, "books": True, "surround": "stone",
    "lit": True, "bar": "horizontal", "length_in": 24.0,
    "computer": "desktop", "pedestal": "right", "arms": True,
    "bed": True,
    # mirror / wall unit
    "has_cabinet": True, "light_style": "bar",
}
FRONTS = ("doors", "drawer_over_doors", "drawers", "false_front")
_ENUMS = {
    "front": FRONTS, "doors": ("auto", "1", "2", "3", "4"),
    "hinge": ("left", "right"),
    "stands": ("floor", "counter"), "door_sides": ("both", "one"),
    "door_style": (ROOM,) + tuple(k for k, _l in DOOR_STYLES),
    "overlay": ("full", "partial"), "pulls": ("bar", "knob", "none"),
    "finish": (ROOM,) + tuple(k for k, _l, _m in FINISHES),
    "hardware": (ROOM,) + tuple(k for k, _l, _m in HARDWARE),
    "top_material": (ROOM,) + tuple(k for k, _l, _m in COUNTERTOPS),
    "sink": ("none", "single", "double"),
    "sink_material": ("metal", "porcelain"),
    "sink_side": ("left", "center", "right"),
    "corner_type": ("diagonal", "l_shape", "blind"), "hand": ("left", "right"),
    "finish_mode": ("standard", "match", "custom"),
    "sheen": tuple(k for k, _l in SHEENS),
    "colour": tuple(k for k, _l, _h in COLOURS),
    "fixture": tuple(k for k, _l in FIXTURES),
    "light_colour": tuple(k for k, _l, _h in LIGHT_COLOURS),
    "beam": ("wide", "spot"),
    "model": FIXTURE_MODELS, "bar": ("horizontal", "vertical"),
    "computer": tuple(k for k, _l in COMPUTERS),
    "pedestal": tuple(k for k, _l in PEDESTALS),
    "surround": tuple(k for k, _l, _m in SURROUNDS),
    "light_style": ("none", "bar", "sconces", "backlit"),
}
_ENUMS.update({key: tuple(row[0] for row in ISLAND_SLOTS)
               for key in ISLAND_SLOT_KEYS})
_NUMBERS = ("width_in", "depth_in", "height_in", "toe_kick_h_in",
            "toe_kick_d_in", "top_thickness_in", "top_overhang_in",
            "backsplash_in", "floor_to_bottom_in", "lumens", "size_in",
            "drop_in", "length_in", "wing_in")


@dataclass(frozen=True)
class Part:
    name: str
    role: str
    quad: tuple          # four (x, f) plan corners
    z0: float
    z1: float


def is_cabinet_kind(kind):
    return kind in PRESETS


def preset_for(kind):
    return dict(PRESETS.get(kind) or {})


def normalize_state(state, preset=None):
    """A complete, type-clean parameter set: the stored `state` over the
    kind's `preset` over the type's defaults. A nonsense enum falls back and
    a number that will not parse takes its default; unknown keys are carried
    through, so a newer file's extra parameters survive an older build."""
    preset = dict(preset or {})
    src = dict(state or {})
    kind_type = preset.get("type", src.get("type", "base"))
    if kind_type not in TYPES:
        kind_type = "base"
    base = dict(STATE_DEFAULTS)
    base.update(_TYPE_DEFAULTS[kind_type])
    base.update(preset)
    out = dict(src)
    for key, default in base.items():
        value = src.get(key, default)
        if key in _NUMBERS:
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = float(default)
            if not math.isfinite(value):
                value = float(default)
        elif key in _ENUMS:
            value = str(value)
            if value not in _ENUMS[key]:
                value = str(default)
        elif key in ("top_on", "wall_mounted", "books", "lit", "arms", "bed",
                     "has_cabinet", "under_light"):
            value = bool(value)
        elif key == "shelves":
            try:
                value = min(max(int(value), 0), 10)
            except (TypeError, ValueError):
                value = int(default)
        elif key == "seats":
            try:
                value = min(max(int(value), 0), 8)
            except (TypeError, ValueError):
                value = int(default)
        elif key == "drawers":
            try:
                value = min(max(int(value), 2), 5)
            except (TypeError, ValueError):
                value = int(default)
        out[key] = value
    out["type"] = kind_type              # the kind decides, never the file
    for fixed in ("appliance", "wall_mounted", "model"):
        if fixed in preset:
            out[fixed] = preset[fixed]
    if kind_type == "fixture":
        model = out["model"]
        if model in ("toilet", "office_chair"):   # one size
            for key in ("width_in", "depth_in", "height_in"):
                out[key] = float(preset.get(key, out[key]))
        elif model == "pedal_bin":                # round, plus the pedal
            out["depth_in"] = out["width_in"] + 3.0
        elif model == "office_set":               # a desk, and room for the chair
            out["width_in"] = max(out["width_in"], CHAIR + 12.0)
            out["depth_in"] = SET_DESK_D + 12.0
        elif model == "grab_bar":
            length = min(max(out["length_in"], 9.0), 60.0)
            out["length_in"] = length
            out["depth_in"] = BAR_CLEAR + BAR_DIAMETER + 0.75
            if out["bar"] == "vertical":
                out["width_in"], out["height_in"] = 3.0, length
            else:
                out["width_in"], out["height_in"] = length, 3.0
        if out["colour"] not in FIXTURE_COLOURS and model in ("toilet", "bathtub"):
            out["colour"] = "white"
    if out.get("appliance") in ("washer", "dryer"):
        out["finish_mode"], out["sheen"] = "custom", "gloss"
        if out["colour"] not in LAUNDRY_COLOURS:
            out["colour"] = "white"
    if kind_type == "kitchen_desk":               # always a top, one drawer
        out["top_on"], out["front"] = True, "drawers"
        out["toe_kick_h_in"] = out["toe_kick_d_in"] = 0.0
    if kind_type == "corner_wall":
        if out["corner_type"] == "blind":         # a base cabinet's, not a wall's
            out["corner_type"] = "diagonal"
        out["depth_in"] = max(out["depth_in"], 6.0)
        reach = out["depth_in"] + 6.0             # room for a door past the corner
        out["width_in"] = max(out["width_in"], reach)
        out["wing_in"] = max(out["wing_in"], reach)
        out["top_on"] = False
    if kind_type == "suspended":
        out["depth_in"] = max(out["depth_in"], 9.0)
        out["drop_in"] = min(max(out["drop_in"], 0.0), 48.0)
        out["lumens"] = min(max(out["lumens"], 0.0), 20000.0)
        out["top_on"] = False
    if kind_type == "island":
        out["width_in"] = island_width(out)       # the slots ARE the length
        out["depth_in"] = max(out["depth_in"],
                              ISLAND_CABINET_D + ISLAND_FRONT_SETBACK + 1.0)
    if kind_type == "mirror":
        # a medicine cabinet stands proud of the wall; a plain mirror is thin.
        # the depth is the KIND's, never the file's, so the symbol and the 3D
        # agree with what `has_cabinet` says.
        out["depth_in"] = 4.5 if out["has_cabinet"] else 1.5
        out["top_on"] = False
        out["lumens"] = min(max(out["lumens"], 0.0), 20000.0)
    if kind_type == "light":
        out["size_in"] = min(max(out["size_in"], 2.0), 120.0)
        out["lumens"] = min(max(out["lumens"], 0.0), 20000.0)
        long_side = out["size_in"]
        if out["fixture"] == "linear":
            out["width_in"], out["depth_in"] = long_side, min(6.0, long_side)
        elif out["fixture"] == "sconce":
            out["width_in"], out["depth_in"] = long_side, 5.0
        else:
            out["width_in"] = out["depth_in"] = long_side
    return out


def island_slots(st):
    """[(code, width, type, overrides)] for the island's FILLED slots, in order."""
    table = {row[0]: row for row in ISLAND_SLOTS}
    out = []
    for key in ISLAND_SLOT_KEYS:
        code, _label, width, kind, over = table.get(st.get(key), table["none"])
        if kind is not None:
            out.append((code, width, kind, over))
    return out


def island_width(st):
    """An island is as long as what stands under it; an empty one is 48 in."""
    total = sum(width for _c, width, _k, _o in island_slots(st))
    return total if total > 0 else 48.0


def is_mounted(st):
    """True for anything hung on a wall at `floor_to_bottom_in` -- or, a
    `suspended` cabinet, from the ceiling: nothing of it stands on the floor."""
    return (st["type"] in ("wall", "mirror", "corner_wall", "suspended")
            or bool(st.get("wall_mounted")))


def footprint(st):
    """(width, depth) of the plan footprint these parameters occupy."""
    w = max(st["width_in"], 1.0)
    if st["type"] == "corner_base" and st["corner_type"] != "blind":
        return w, w
    if st["type"] == "corner_wall":               # one wing by the other
        return w, max(st["wing_in"], 1.0)
    return w, max(st["depth_in"], 1.0)


def overall_height(st, ceiling_in=96.0):
    """Floor to the highest point, countertop and backsplash included. A
    `suspended` cabinet's is its room's ceiling less its drop."""
    top = st["height_in"]
    if st["type"] == "suspended":
        return float(ceiling_in) - max(st["drop_in"], 0.0)
    if is_mounted(st):
        return st["floor_to_bottom_in"] + top
    if st["top_on"]:
        top += st["top_thickness_in"] + max(st["backsplash_in"], 0.0)
    return top


# --------------------------------------------------------------------------
# materials
# --------------------------------------------------------------------------
def _lookup(table, key, default_key):
    by = {k: m for k, _label, m in table}
    return by.get(key) or by[default_key]


def effective_style(room_style=None):
    """The room's style over the defaults; unknown values fall back."""
    out = dict(DEFAULT_STYLE)
    for key in STYLE_KEYS:
        value = (room_style or {}).get(key)
        if isinstance(value, str) and value:
            out[key] = value
    return out


def door_style_of(st, room_style=None):
    if st["door_style"] != ROOM:
        return st["door_style"]
    wanted = effective_style(room_style)["door_style"]
    return wanted if wanted in {k for k, _l in DOOR_STYLES} else "shaker"


def resolve_materials(st, room_style=None):
    """{role: material name}. Own choice, else the room's style, else the
    default -- for every role a part can carry."""
    style = effective_style(room_style)
    finish = st["finish"] if st["finish"] != ROOM else style["cabinet_finish"]
    top = st["top_material"] if st["top_material"] != ROOM else style["countertop"]
    hardware = st["hardware"] if st["hardware"] != ROOM else style["hardware"]
    cabinet = _lookup(FINISHES, finish, DEFAULT_STYLE["cabinet_finish"])
    counter = _lookup(COUNTERTOPS, top, DEFAULT_STYLE["countertop"])
    splash = style["backsplash"]
    backsplash = (counter if splash in ("countertop", "", None)
                  else _lookup(COUNTERTOPS, splash, top if top in
                               {k for k, _l, _m in COUNTERTOPS}
                               else DEFAULT_STYLE["countertop"]))
    if st["finish_mode"] == "match":
        appliance = cabinet
    elif st["finish_mode"] == "custom":
        hexes = {k: h for k, _l, h in COLOURS}
        appliance = f"sheen_{st['sheen']}{hexes.get(st['colour'], '#f2f2ee')}"
    else:
        appliance = "metal"
    glow = {k: h for k, _l, h in LIGHT_COLOURS}.get(st["light_colour"], "#ffe4bf")
    china = "sheen_gloss" + {k: h for k, _l, h in COLOURS}.get(
        st["colour"], "#f2f2ee")
    return {"porcelain": china, "upholstery": "sheen_matte" + china[len(
                "sheen_gloss"):],
            "screen": "screen_glass", "device": "metal",
            "surround": _lookup(SURROUNDS, st.get("surround"), "stone"),
            "hearth": "fp_hearth", "firebox": "fp_firebox", "log": "fp_log",
            "flame": "light_emit#ff7a1a", "burner": "metal",
            "book_1": "book_1", "book_2": "book_2", "book_3": "book_3",
            "book_4": "book_4", "book_5": "book_5",
            "cabinet": cabinet, "countertop": counter, "backsplash": backsplash,
            "hardware": _lookup(HARDWARE, hardware, DEFAULT_STYLE["hardware"]),
            "kick": "cabinet_kick", "glass": "cabinet_glass",
            "mirror": "mirror_glass",
            "sink": st["sink_material"], "appliance": appliance,
            "appliance_dark": "auto_trim", "stool": "stool_seat",
            "fixture": "light_fixture", "lens": f"light_emit{glow}"}


# --------------------------------------------------------------------------
# parts
# --------------------------------------------------------------------------
def _rect(x0, x1, f0, f1):
    return ((x0, f0), (x1, f0), (x1, f1), (x0, f1))


def _add(parts, name, role, x0, x1, f0, f1, z0, z1):
    if x1 - x0 > 1e-6 and f1 - f0 > 1e-6 and z1 - z0 > 1e-6:
        parts.append(Part(name, role, _rect(x0, x1, f0, f1), z0, z1))


def _ring(parts, name, role, ring, z0, z1):
    """A part over any CONVEX plan ring (the viewer builds 4 corners as a
    box and more as a prism)."""
    if len(ring) >= 3 and z1 - z0 > 1e-6:
        parts.append(Part(name, role, tuple(ring), z0, z1))


def _oval(parts, name, role, cx, cf, rx, rf, z0, z1, n=16):
    """An elliptical part, as an n-gon."""
    ring = [(cx + rx * math.cos(2.0 * math.pi * i / n),
             cf + rf * math.sin(2.0 * math.pi * i / n)) for i in range(n)]
    _ring(parts, name, role, ring, z0, z1)


def _leaf(parts, name, x0, x1, z0, z1, face, style, role="cabinet"):
    """One door or drawer front on a face at depth `face`, `DOOR_T` thick.
    A five-piece style is a recessed panel inside two stiles and two rails;
    too narrow or too short for that, it is a slab."""
    back = face - DOOR_T
    five = (style in ("shaker", "raised", "glass")
            and x1 - x0 > 2 * STILE_W + 1.5 and z1 - z0 > 2 * STILE_W + 1.5)
    if not five:
        _add(parts, name, role, x0, x1, back, face, z0, z1)
        return
    _add(parts, f"{name}-stile-l", role, x0, x0 + STILE_W, back, face, z0, z1)
    _add(parts, f"{name}-stile-r", role, x1 - STILE_W, x1, back, face, z0, z1)
    _add(parts, f"{name}-rail-b", role, x0 + STILE_W, x1 - STILE_W, back, face,
         z0, z0 + STILE_W)
    _add(parts, f"{name}-rail-t", role, x0 + STILE_W, x1 - STILE_W, back, face,
         z1 - STILE_W, z1)
    px0, px1 = x0 + STILE_W, x1 - STILE_W
    pz0, pz1 = z0 + STILE_W, z1 - STILE_W
    if style == "glass":
        _add(parts, f"{name}-pane", "glass", px0, px1, back + 0.2, face - 0.4,
             pz0, pz1)
    else:
        _add(parts, f"{name}-panel", role, px0, px1, back, face - 0.3, pz0, pz1)
        if style == "raised":
            _add(parts, f"{name}-field", role, px0 + 1.0, px1 - 1.0, back,
                 face - 0.08, pz0 + 1.0, pz1 - 1.0)


def _pull(parts, name, kind, cx, cz, face, vertical):
    if kind == "none":
        return
    if kind == "knob":
        _add(parts, name, "hardware", cx - 0.6, cx + 0.6, face, face + 1.1,
             cz - 0.6, cz + 0.6)
    elif vertical:
        _add(parts, name, "hardware", cx - 0.3, cx + 0.3, face, face + 1.2,
             cz - 2.5, cz + 2.5)
    else:
        _add(parts, name, "hardware", cx - 2.5, cx + 2.5, face, face + 1.2,
             cz - 0.3, cz + 0.3)


def door_count(st, width=None):
    width = st["width_in"] if width is None else width
    if st["doors"] in ("1", "2", "3", "4"):
        return int(st["doors"])
    return 1 if width <= 21.0 else 2


def _front(parts, st, style, x0, x1, z0, z1, face, pulls_low=False,
           tag="", front=None):
    """Doors and drawers over the face `x0..x1`, `z0..z1`, at depth `face`.
    Adjacent leaves and the edges are a reveal apart: an eighth for full
    overlay, an inch for partial -- where the box behind shows as a frame."""
    g = REVEAL[st["overlay"]]
    front = front or st["front"]
    n = door_count(st, x1 - x0)
    cols = [(x0 + g + i * (x1 - x0 - g) / n, x0 + (i + 1) * (x1 - x0 - g) / n)
            for i in range(n)]

    def doors(lo, hi):
        for i, (a, b) in enumerate(cols):
            _leaf(parts, f"{tag}door-{i + 1}", a, b, lo, hi, face, style)
            if n == 1:
                inner = b - 2.2 if st["hinge"] == "left" else a + 2.2
            else:                      # in pairs; an odd last door hinges left
                inner = b - 2.2 if i % 2 == 0 else a + 2.2
            cz = (lo + 5.0) if pulls_low else (hi - 5.0)
            cz = min(max(cz, lo + 3.0), hi - 3.0)
            _pull(parts, f"{tag}pull-{i + 1}", st["pulls"], inner, cz, face, True)

    lo, hi = z0 + g, z1 - g
    if hi - lo < 3.0:
        return
    if front == "drawers":
        rows = max(int(st["drawers"]), 2)
        top_h = min(DRAWER_H, (hi - lo) / rows)
        rest = (hi - lo - top_h) / (rows - 1)
        edges = [hi, hi - top_h] + [hi - top_h - rest * k for k in range(1, rows)]
        for r in range(rows):
            a, b = edges[r + 1] + (g if r < rows - 1 else 0.0), edges[r]
            _leaf(parts, f"{tag}drawer-{r + 1}", x0 + g, x1 - g, a, b, face, style)
            _pull(parts, f"{tag}drawer-pull-{r + 1}", st["pulls"],
                  (x0 + x1) / 2.0, (a + b) / 2.0, face, False)
    elif front in ("drawer_over_doors", "false_front") and hi - lo > DRAWER_H + 8.0:
        split = hi - DRAWER_H
        for i, (a, b) in enumerate(cols):
            name = "false-front" if front == "false_front" else "drawer"
            # a drawer front is a slab unless the door is: keep the style
            _leaf(parts, f"{tag}{name}-{i + 1}", a, b, split, hi, face,
                  "slab" if style == "glass" else style)
            if front == "drawer_over_doors":
                _pull(parts, f"{tag}drawer-pull-{i + 1}", st["pulls"],
                      (a + b) / 2.0, (split + hi) / 2.0, face, False)
        doors(lo, split - g)
    else:
        doors(lo, hi)


def _sink_layout(st, x0, x1, depth):
    """Where a sink's bowls sit, as `([(a, f0, b, f1), ...], faucet_cx)` in the
    cabinet frame -- the ONE placement the 3D parts (`_sink`) and the plan
    symbol (`sink_base_plan`) both read, so a sink drawn on the plan can never
    disagree with the one built in 3D on its side. `([], None)` for no sink."""
    bowls = {"none": 0, "single": 1, "double": 2}[st["sink"]]
    if not bowls:
        return [], None
    span = x1 - x0
    bw = min((span - 6.0 - (bowls - 1) * 1.5) / bowls, 30.0)
    bd = min(depth - 8.5, 18.0)
    if bw < 6.0 or bd < 6.0:
        return [], None
    f0 = min(4.5, depth - bd - 2.5)
    total = bowls * bw + (bowls - 1) * 1.5
    # A SINGLE bowl honours `sink_side`: it slides to the left or right of the
    # top, inset from the end, the faucet riding its new centre. A double bowl
    # stays centred -- "the side of the sink" only means something for one.
    side = st.get("sink_side", "center")
    if bowls == 1 and side in ("left", "right"):
        bw = min(bw, max(span - 14.0, 10.0))   # keep counter on the open side
        total = bw
        inset = 3.0
        left = x0 + inset if side == "left" else x1 - inset - total
        left = max(x0 + 1.0, min(left, x1 - total - 1.0))
    else:
        left = (x0 + x1) / 2.0 - total / 2.0
    rects = [(left + i * (bw + 1.5), f0, left + i * (bw + 1.5) + bw, f0 + bd)
             for i in range(bowls)]
    return rects, left + total / 2.0


def _sink(parts, st, x0, x1, depth, top):
    """Bowls let into the top (returned as the plan rectangles the top must
    leave open), each a floor and four walls, with a faucet behind."""
    rects, cx = _sink_layout(st, x0, x1, depth)
    if not rects:
        return []
    drop, wall = 7.0, 0.4
    f0 = rects[0][1]
    holes = []
    for i, (a, _f0, b, f1) in enumerate(rects):
        holes.append((a, b, f0, f1))
        _add(parts, f"bowl-{i + 1}-floor", "sink", a, b, f0, f1,
             top - drop, top - drop + wall)
        for tag, r in (("l", (a, a + wall, f0, f1)),
                       ("r", (b - wall, b, f0, f1)),
                       ("b", (a, b, f0, f0 + wall)),
                       ("f", (a, b, f1 - wall, f1))):
            _add(parts, f"bowl-{i + 1}-wall-{tag}", "sink", *r,
                 top - drop + wall, top - 0.05)
    _add(parts, "faucet-post", "hardware", cx - 0.7, cx + 0.7, f0 - 2.6, f0 - 1.2,
         top, top + 9.0)
    _add(parts, "faucet-spout", "hardware", cx - 0.5, cx + 0.5, f0 - 2.6, f0 + 5.0,
         top + 8.0, top + 9.0)
    return holes


def sink_base_plan(st):
    """The plan symbol for a sink base / vanity, from its parameters: the top
    outline, the bowl(s) WHERE THEY ACTUALLY SIT (so an offset single sink
    shows on its side), the faucet, and door dividers along the front. A list
    of drawing primitives in the cabinet frame (x across centred, f down from
    the back edge); `items._paint_plan_prims` renders them."""
    w, d = st["width_in"], st["depth_in"]
    x0, x1 = -w / 2.0, w / 2.0
    prims = [("outline", x0 + 0.75, 0.75, x1 - 0.75, d - 0.75)]
    rects, cx = _sink_layout(st, x0, x1, d)
    for a, f0, b, f1 in rects:
        prims.append(("bowl", a, f0, b, f1))
    if cx is not None:
        prims.append(("dot", cx, max(rects[0][1] - 2.0, 1.2), 1.1))
    doors = max(2, len(rects) * 2)
    fw = (w - 1.5) / doors
    for i in range(1, doors):
        xx = x0 + 0.75 + fw * i
        prims.append(("line", xx, d - 8.0, xx, d - 0.75))
    for i in range(doors):
        prims.append(("dot", x0 + 0.75 + fw * (i + 0.5), d - 3.0, 0.7))
    return prims


def mirror_plan(st):
    """The plan symbol for a mirror / medicine cabinet: a box (solid for a
    storage cabinet, dashed for a plain overhead mirror), the mirror diagonal,
    and the lights drawn per `light_style` -- a bar of bulbs, a sconce each
    side, or a backlit inner border. Primitives in the cabinet frame."""
    w, d = st["width_in"], st["depth_in"]
    x0, x1 = -w / 2.0, w / 2.0
    f1 = max(d - 0.3, 0.6)
    prims = [("outline" if st["has_cabinet"] else "dashed", x0 + 0.4, 0.3,
              x1 - 0.4, f1),
             ("line", x0 + 0.6, f1, x1 - 0.6, 0.4)]          # mirror diagonal
    style = st["light_style"]
    if style == "bar":
        prims.append(("line", x0 + 2.0, 0.5, x1 - 2.0, 0.5))
        n = max(2, round(w / 12))
        for k in range(n):
            prims.append(("bulb", x0 + w * (k + 0.5) / n, min(0.9, d * 0.5), 0.5))
    elif style == "sconces":
        for cx in (x0 + 0.5, x1 - 0.5):
            prims.append(("bulb", cx, d * 0.5, 0.7))
    elif style == "backlit":
        prims.append(("dashed", x0 + 1.0, 0.8, x1 - 1.0, max(d - 0.8, 1.0)))
    if st["has_cabinet"]:
        prims.append(("dot", x1 - 1.5, d * 0.5, 0.6))        # the door pull
    return prims


def _top(parts, st, x0, x1, depth, z, holes=(), front=None):
    """The countertop over `x0..x1`, front overhang included, left open over
    each bowl; and the backsplash against the wall."""
    t = st["top_thickness_in"]
    front = depth + st["top_overhang_in"] if front is None else front
    if not holes:
        _add(parts, "countertop", "countertop", x0, x1, 0.0, front, z, z + t)
    else:
        f0 = min(h[2] for h in holes)
        f1 = max(h[3] for h in holes)
        _add(parts, "countertop-back", "countertop", x0, x1, 0.0, f0, z, z + t)
        _add(parts, "countertop-front", "countertop", x0, x1, f1, front, z, z + t)
        edge = x0
        for i, (a, b, _f0, _f1) in enumerate(sorted(holes)):
            _add(parts, f"countertop-web-{i + 1}", "countertop", edge, a, f0, f1,
                 z, z + t)
            edge = b
        _add(parts, "countertop-web-end", "countertop", edge, x1, f0, f1, z, z + t)
    if st["backsplash_in"] > 0:
        _add(parts, "backsplash", "backsplash", x0, x1, 0.0, 0.75,
             z + t, z + t + st["backsplash_in"])


def _base_like(parts, st, style):
    w, d, h = st["width_in"], st["depth_in"], st["height_in"]
    x0, x1 = -w / 2.0, w / 2.0
    kick = min(max(st["toe_kick_h_in"], 0.0), h - 6.0)
    _add(parts, "toe-kick", "kick", x0, x1, 0.0, d - st["toe_kick_d_in"], 0.0, kick)
    _add(parts, "carcass", "cabinet", x0, x1, 0.0, d - DOOR_T, kick, h)
    _front(parts, st, style, x0, x1, kick, h, d)
    if st["top_on"]:
        holes = (_sink(parts, st, x0, x1, d, h + st["top_thickness_in"])
                 if st["type"] == "sink_base" else [])
        _top(parts, st, x0, x1, d, h, holes)


def _tall(parts, st, style):
    w, d, h = st["width_in"], st["depth_in"], st["height_in"]
    x0, x1 = -w / 2.0, w / 2.0
    if st["stands"] == "counter":
        # 0368: on a base unit's counter -- no toe kick, one run of doors from
        # the counter to the top, which is still `height_in` above the FLOOR
        z0 = min(COUNTER_H, h - 6.0)
        _add(parts, "carcass", "cabinet", x0, x1, 0.0, d - DOOR_T, z0, h)
        _front(parts, st, style, x0, x1, z0, h, d, pulls_low=True, front="doors")
        return
    kick = min(max(st["toe_kick_h_in"], 0.0), h - 6.0)
    _add(parts, "toe-kick", "kick", x0, x1, 0.0, d - st["toe_kick_d_in"], 0.0, kick)
    _add(parts, "carcass", "cabinet", x0, x1, 0.0, d - DOOR_T, kick, h)
    split = 54.0
    if h > split + 12.0:
        _front(parts, st, style, x0, x1, kick, split, d, tag="lower-", front="doors")
        _front(parts, st, style, x0, x1, split, h, d, pulls_low=True, tag="upper-",
               front="doors")
    else:
        _front(parts, st, style, x0, x1, kick, h, d, front="doors")


def _wall(parts, st, style):
    w, d, h = st["width_in"], st["depth_in"], st["height_in"]
    z0 = max(st["floor_to_bottom_in"], 0.0)
    x0, x1 = -w / 2.0, w / 2.0
    _add(parts, "carcass", "cabinet", x0, x1, 0.0, d - DOOR_T, z0, z0 + h)
    _front(parts, st, style, x0, x1, z0, z0 + h, d, pulls_low=True, front="doors")


def tall_plan(st):
    """0368: the plan symbol for a tall cabinet, from its parameters -- a box
    with its shelves, or DASHED when it stands on a counter (it is above the
    plan cut, like a wall cabinet), and one knob per door across."""
    w, d = st["width_in"], st["depth_in"]
    x0, x1 = -w / 2.0, w / 2.0
    over = st["stands"] == "counter"
    prims = [("dashed" if over else "outline", x0 + 0.75, 0.75, x1 - 0.75, d - 0.75)]
    if not over:
        for j in range(1, 4):
            f = 0.75 + (d - 1.5) * j / 4.0
            prims.append(("dline", x0 + 2.5, f, x1 - 2.5, f))
    n = door_count(st)
    fw = (w - 1.5) / n
    for i in range(1, n):
        xx = x0 + 0.75 + fw * i
        prims.append(("dline" if over else "line", xx, 0.75, xx, d - 0.75))
    for i in range(n):
        prims.append(("dot", x0 + 0.75 + fw * (i + 0.5), d - 3.5, 0.8))
    return prims


def _kitchen_desk(parts, st, style):
    """0368: a kitchen desk -- the room's countertop on two end panels, one
    shallow full-width drawer under it, knee space below. `height_in` is the
    underside of the top, as a base cabinet's is."""
    w, d, h = st["width_in"], st["depth_in"], st["height_in"]
    x0, x1 = -w / 2.0, w / 2.0
    t, g = PANEL_T, REVEAL[st["overlay"]]
    dh = min(DESK_DRAWER_H, max(h - 20.0, 2.0))
    apron = h - dh
    _add(parts, "end-panel-l", "cabinet", x0, x0 + t, 0.0, d - DOOR_T, 0.0, h)
    _add(parts, "end-panel-r", "cabinet", x1 - t, x1, 0.0, d - DOOR_T, 0.0, h)
    _add(parts, "back-rail", "cabinet", x0 + t, x1 - t, 0.0, t, apron, h)
    _add(parts, "drawer-box", "cabinet", x0 + t, x1 - t, t, d - DOOR_T, apron, h)
    _leaf(parts, "drawer-1", x0 + g, x1 - g, apron + g, h - g, d,
          "slab" if style == "glass" else style)
    _pull(parts, "drawer-pull-1", st["pulls"], 0.0, apron + dh / 2.0, d, False)
    _top(parts, st, x0, x1, d, h)


def kitchen_desk_plan(st):
    """0368: the plan symbol for a kitchen desk: its top, the drawer front
    along the open edge, and the drawer's pull."""
    w, d = st["width_in"], st["depth_in"]
    x0, x1 = -w / 2.0, w / 2.0
    return [("panel", x0 + 0.5, 0.5, x1 - 0.5, d - 0.5),
            ("line", x0 + 1.5, d - 3.0, x1 - 1.5, d - 3.0),
            ("line", -4.0, d - 1.6, 4.0, d - 1.6)]


def _corner_wall(parts, st, style):
    """0368: a corner WALL cabinet, hung at `floor_to_bottom_in`, its back
    corner at the plan symbol's top-left (top-right for a right hand). One
    wing runs `width_in` along the wall behind, the other `wing_in` along the
    side wall, each `depth_in` deep. `diagonal` has one door across the cut
    corner; `l_shape` has a door on each wing's inside face."""
    wa, wb, d, h = st["width_in"], st["wing_in"], st["depth_in"], st["height_in"]
    z0 = max(st["floor_to_bottom_in"], 0.0)
    z1 = z0 + h
    sign = 1.0 if st["hand"] == "left" else -1.0
    t, g = DOOR_T, REVEAL[st["overlay"]]

    def add_quad(name, role, pts, a=z0, b=z1):
        parts.append(Part(name, role,
                          tuple((sign * (u - wa / 2.0), f) for u, f in pts), a, b))

    def add_rect(name, role, u0, u1, f0, f1, a=z0, b=z1):
        if u1 - u0 > 1e-6 and f1 - f0 > 1e-6 and b - a > 1e-6:
            add_quad(name, role, [(u0, f0), (u1, f0), (u1, f1), (u0, f1)], a, b)

    pz = min(z0 + 5.0, z1 - 3.0)             # pulls low, as on a wall cabinet
    grip = 0.6 if st["pulls"] == "knob" else 2.5
    if st["corner_type"] == "l_shape":
        add_rect("carcass", "cabinet", 0.0, wa, 0.0, d - t)
        add_rect("carcass-leg", "cabinet", 0.0, d - t, d - t, wb)
        add_rect("door-1", "cabinet", d + g, wa - g, d - t, d, z0 + g, z1 - g)
        add_rect("door-2", "cabinet", d - t, d, d + g, wb - g, z0 + g, z1 - g)
        if st["pulls"] != "none":
            add_rect("pull-1", "hardware", d + 1.9, d + 2.5, d, d + 1.2,
                     pz - grip, pz + grip)
            add_rect("pull-2", "hardware", d, d + 1.2, d + 1.9, d + 2.5,
                     pz - grip, pz + grip)
        return
    a, b = wa - d, wb - d                    # the door runs (wa, d) -> (d, wb)
    run = math.hypot(a, b)
    k = min(t * run / b, d - 0.5)            # the door's thickness, along the wall
    add_rect("carcass", "cabinet", 0.0, wa, 0.0, d)
    add_quad("carcass-leg", "cabinet",
             [(0.0, d), (wa - k, d), (d - k, wb), (0.0, wb)])
    add_quad("door-1", "cabinet",
             [(wa - k, d), (wa, d), (d, wb), (d - k, wb)], z0 + g, z1 - g)
    if st["pulls"] != "none":
        mu = (wa + d) / 2.0 + 0.6 * b / run  # just proud of the door's middle
        mf = (d + wb) / 2.0 + 0.6 * a / run
        add_rect("pull-1", "hardware", mu - 0.45, mu + 0.45, mf - 0.45, mf + 0.45,
                 pz - grip, pz + grip)


def corner_wall_plan(st):
    """0368: the plan symbol for a corner wall cabinet: its outline DASHED (it
    is overhead), and a knob on each door."""
    wa, wb, d = st["width_in"], st["wing_in"], st["depth_in"]
    sign = 1.0 if st["hand"] == "left" else -1.0

    def at(u, f):
        return sign * (u - wa / 2.0), f

    if st["corner_type"] == "l_shape":
        ring = [(0.0, 0.0), (wa, 0.0), (wa, d), (d, d), (d, wb), (0.0, wb)]
        knobs = [((wa + d) / 2.0, d - 2.5), (d - 2.5, (wb + d) / 2.0)]
    else:
        ring = [(0.0, 0.0), (wa, 0.0), (wa, d), (d, wb), (0.0, wb)]
        a, b = wa - d, wb - d
        run = math.hypot(a, b)
        knobs = [((wa + d) / 2.0 - 2.5 * b / run, (d + wb) / 2.0 - 2.5 * a / run)]
    prims = [("poly", "dashed", [at(u, f) for u, f in ring])]
    for u, f in knobs:
        x, ff = at(u, f)
        prims.append(("dot", x, ff, 0.7))
    return prims


def _suspended(parts, st, style, ceiling_in):
    """0368: a cabinet hung from the ceiling over an island or a peninsula.
    Its top is `drop_in` below the ceiling -- 0 is tight to it, more hangs it
    on four rods -- so its underside follows the room. A cap and a light rail
    span the whole footprint; the doors sit back under them, on one long side
    or on both, and the rail hides an optional light strip. The strip carries
    the "lens" role, so it glows and `light_source` finds it."""
    w, d, h = st["width_in"], st["depth_in"], st["height_in"]
    x0, x1 = -w / 2.0, w / 2.0
    top = float(ceiling_in) - st["drop_in"]
    z0 = top - h
    t = PANEL_T
    both = st["door_sides"] == "both"
    face = d - ISLAND_FRONT_SETBACK
    back = (ISLAND_FRONT_SETBACK + DOOR_T) if both else 0.0
    _add(parts, "cap", "cabinet", x0, x1, 0.0, d, top - t, top)
    _add(parts, "light-rail", "cabinet", x0, x1, 0.0, d, z0, z0 + t)
    _add(parts, "carcass", "cabinet", x0, x1, back, face - DOOR_T, z0 + t, top - t)
    _front(parts, st, style, x0, x1, z0 + t, top - t, face, pulls_low=True,
           front="doors")
    if both:
        sub = []
        _front(sub, st, style, x0, x1, z0 + t, top - t, face, pulls_low=True,
               tag="back-", front="doors")
        for p in sub:                    # the same doors, turned to face away
            parts.append(Part(p.name, p.role,
                              tuple((-x, d - f) for x, f in p.quad), p.z0, p.z1))
    if st["drop_in"] > 0.5:
        for i, (rx, rf) in enumerate(((x0 + 2.0, 2.0), (x1 - 2.0, 2.0),
                                      (x1 - 2.0, d - 2.0), (x0 + 2.0, d - 2.0))):
            _add(parts, f"rod-{i + 1}", "hardware", rx - 0.3, rx + 0.3,
                 rf - 0.3, rf + 0.3, top, float(ceiling_in))
    if st["under_light"]:
        _add(parts, "light-strip", "lens", x0 + 1.5, x1 - 1.5, d / 2.0 - 1.0,
             d / 2.0 + 1.0, z0 - 0.3, z0)


def suspended_plan(st):
    """0368: the plan symbol for a ceiling cabinet: a DASHED box (overhead), a
    knob per door on each door side, and the light under it as bulbs."""
    w, d = st["width_in"], st["depth_in"]
    x0, x1 = -w / 2.0, w / 2.0
    prims = [("dashed", x0 + 0.5, 0.5, x1 - 0.5, d - 0.5)]
    n = door_count(st)
    fw = (w - 1.0) / n
    for i in range(1, n):
        xx = x0 + 0.5 + fw * i
        prims.append(("dline", xx, 0.5, xx, d - 0.5))
    rows = (d - 2.5, 2.5) if st["door_sides"] == "both" else (d - 2.5,)
    for f in rows:
        for i in range(n):
            prims.append(("dot", x0 + 0.5 + fw * (i + 0.5), f, 0.7))
    if st["under_light"] and st["lumens"] > 0:
        m = max(2, round(w / 16.0))
        for k in range(m):
            prims.append(("bulb", x0 + w * (k + 0.5) / m, d / 2.0, 0.6))
    return prims


def _mirror(parts, st, _style=None):
    """A bathroom mirror / medicine cabinet hung on the wall at
    `floor_to_bottom_in`. `has_cabinet` makes it a storage box behind a
    mirrored door; otherwise it is a plain mirror panel. `light_style` adds a
    fixture over it, a sconce each side, or a backlit edge -- the lit parts
    carry the "lens" role so they glow and `light_source` can find them."""
    w, h, d = st["width_in"], st["height_in"], st["depth_in"]
    z0 = max(st["floor_to_bottom_in"], 0.0)
    z1 = z0 + h
    x0, x1 = -w / 2.0, w / 2.0
    if st["has_cabinet"]:
        _add(parts, "carcass", "cabinet", x0, x1, 0.0, max(d - 0.5, 0.25), z0, z1)
        _add(parts, "mirror-door", "mirror", x0 + 0.5, x1 - 0.5,
             max(d - 0.5, 0.25), d, z0 + 0.5, z1 - 0.5)
        _pull(parts, "door-pull", st["pulls"], x1 - 1.5, (z0 + z1) / 2.0, d, True)
    else:
        _add(parts, "frame", "cabinet", x0, x1, 0.0, max(d - 0.4, 0.2), z0, z1)
        _add(parts, "mirror-panel", "mirror", x0 + 0.5, x1 - 0.5,
             max(d - 0.4, 0.2), d, z0 + 0.5, z1 - 0.5)
    style = st["light_style"]
    if style == "bar":
        bx0, bx1 = -w / 4.0, w / 4.0
        _add(parts, "light-bar", "fixture", bx0, bx1, 0.0, 3.0, z1 + 1.0, z1 + 3.0)
        _add(parts, "light-bar-lens", "lens", bx0 + 0.5, bx1 - 0.5, 0.5, 2.5,
             z1 + 1.1, z1 + 1.4)
    elif style == "sconces":
        zc = (z0 + z1) / 2.0
        for tag, a, b in (("l", x0 - 3.0, x0 - 0.5), ("r", x1 + 0.5, x1 + 3.0)):
            _add(parts, f"sconce-{tag}", "fixture", a, b, 0.0, 3.0,
                 zc - 6.0, zc + 6.0)
            _add(parts, f"sconce-{tag}-lens", "lens", a + 0.4, b - 0.4, 0.4, 2.6,
                 zc - 5.0, zc + 5.0)
    elif style == "backlit":
        f0, f1 = d, d + 0.2                 # a glowing ring just proud of the glass
        t = 1.0
        _add(parts, "backlit-top", "lens", x0, x1, f0, f1, z1 - t, z1)
        _add(parts, "backlit-bottom", "lens", x0, x1, f0, f1, z0, z0 + t)
        _add(parts, "backlit-left", "lens", x0, x0 + t, f0, f1, z0, z1)
        _add(parts, "backlit-right", "lens", x1 - t, x1, f0, f1, z0, z1)


def _corner(parts, st, style):
    """A corner base, its back corner at the plan symbol's top-left (or
    top-right for a right hand). `blind` is a straight cabinet whose far half
    is a blank panel; `l_shape` has two short doors in the inside corner;
    `diagonal` has one door across the cut corner."""
    w, h = st["width_in"], st["height_in"]
    kick = min(max(st["toe_kick_h_in"], 0.0), h - 6.0)
    sign = 1.0 if st["hand"] == "left" else -1.0

    def X(u):                         # u: distance from the back corner's wall
        return sign * (u - w / 2.0)

    def quad(pts):
        return tuple((X(u), f) for u, f in pts)

    def add_quad(name, role, pts, z0, z1):
        parts.append(Part(name, role, quad(pts), z0, z1))

    def add_rect(name, role, u0, u1, f0, f1, z0, z1):
        if u1 - u0 > 1e-6 and f1 - f0 > 1e-6 and z1 - z0 > 1e-6:
            add_quad(name, role, [(u0, f0), (u1, f0), (u1, f1), (u0, f1)], z0, z1)

    leg = min(CORNER_LEG, w - 6.0)
    t, g = DOOR_T, REVEAL[st["overlay"]]
    top_t = st["top_thickness_in"] if st["top_on"] else 0.0
    if st["corner_type"] == "blind":
        d = st["depth_in"]
        add_rect("toe-kick", "kick", 0.0, w, 0.0, d - st["toe_kick_d_in"], 0.0, kick)
        add_rect("carcass", "cabinet", 0.0, w, 0.0, d - t, kick, h)
        add_rect("blind-panel", "cabinet", g, w / 2.0, d - t, d, kick + g, h - g)
        sub = []
        _front(sub, st, style, 0.0, w / 2.0, kick, h, d, front="doors")
        for p in sub:                  # the door half, moved to the far side
            pts = [(x + w / 2.0, f) for x, f in p.quad]
            add_quad(p.name, p.role, pts, p.z0, p.z1)
        if st["top_on"]:
            add_rect("countertop", "countertop", 0.0, w, 0.0,
                     d + st["top_overhang_in"], h, h + top_t)
        return
    add_rect("toe-kick", "kick", 0.0, w - 3.0, 0.0, leg - 3.0, 0.0, kick)
    add_rect("toe-kick-leg", "kick", 0.0, leg - 3.0, leg - 3.0, w - 3.0, 0.0, kick)
    if st["corner_type"] == "l_shape":
        add_rect("carcass", "cabinet", 0.0, w, 0.0, leg - t, kick, h)
        add_rect("carcass-leg", "cabinet", 0.0, leg - t, leg - t, w, kick, h)
        add_rect("door-1", "cabinet", leg + g, w - g, leg - t, leg, kick + g, h - g)
        add_rect("door-2", "cabinet", leg - t, leg, leg + g, w - g, kick + g, h - g)
        if st["pulls"] != "none":
            add_rect("pull-1", "hardware", leg + 1.6, leg + 2.2, leg, leg + 1.2,
                     h - 8.0, h - 3.0)
        if st["top_on"]:
            o = st["top_overhang_in"]
            add_rect("countertop", "countertop", 0.0, w, 0.0, leg + o, h, h + top_t)
            add_rect("countertop-leg", "countertop", 0.0, leg + o, leg + o, w,
                     h, h + top_t)
    else:                               # diagonal
        k = t * math.sqrt(2.0)
        add_rect("carcass", "cabinet", 0.0, w, 0.0, leg, kick, h)
        add_quad("carcass-leg", "cabinet",
                 [(0.0, leg), (w - k, leg), (leg - k, w), (0.0, w)], kick, h)
        add_quad("door-1", "cabinet",
                 [(w - k, leg), (w, leg), (leg, w), (leg - k, w)], kick + g, h - g)
        if st["top_on"]:
            add_rect("countertop", "countertop", 0.0, w, 0.0, leg, h, h + top_t)
            add_quad("countertop-leg", "countertop",
                     [(0.0, leg), (w, leg), (leg, w), (0.0, w)], h, h + top_t)
    if st["top_on"] and st["backsplash_in"] > 0:
        add_rect("backsplash", "backsplash", 0.0, w, 0.0, 0.75,
                 h + top_t, h + top_t + st["backsplash_in"])
        add_rect("backsplash-leg", "backsplash", 0.0, 0.75, 0.75, w,
                 h + top_t, h + top_t + st["backsplash_in"])


def _appliance(parts, st):
    """An appliance as a body in its finish, with the few dark and bright
    details that make it read: a door, a handle, a control strip."""
    w, d, h = st["width_in"], st["depth_in"], st["height_in"]
    x0, x1 = -w / 2.0, w / 2.0
    kind = st.get("appliance", "generic")
    face = d
    if kind == "refrigerator":
        _add(parts, "body", "appliance", x0, x1, 0.0, d - 2.0, 0.0, h)
        _add(parts, "grille", "appliance_dark", x0 + 0.5, x1 - 0.5, d - 2.0, d - 1.0,
             0.0, 3.0)
        split = 28.0
        _add(parts, "freezer", "appliance", x0 + 0.2, x1 - 0.2, d - 2.0, face,
             3.3, split)
        _add(parts, "door-l", "appliance", x0 + 0.2, -0.15, d - 2.0, face,
             split + 0.4, h - 0.3)
        _add(parts, "door-r", "appliance", 0.15, x1 - 0.2, d - 2.0, face,
             split + 0.4, h - 0.3)
        for name, cx in (("handle-l", -1.6), ("handle-r", 1.6)):
            _add(parts, name, "hardware", cx - 0.4, cx + 0.4, face, face + 1.6,
                 split + 6.0, h - 12.0)
        _add(parts, "handle-freezer", "hardware", x0 + 6.0, x1 - 6.0, face,
             face + 1.6, split - 4.0, split - 3.2)
    elif kind == "range":
        _add(parts, "body", "appliance", x0, x1, 0.0, d - 1.0, 0.0, h - 1.0)
        _add(parts, "cooktop", "appliance_dark", x0, x1, 0.0, d, h - 1.0, h)
        _add(parts, "backguard", "appliance", x0, x1, 0.0, 2.0, h, h + 4.0)
        _add(parts, "controls", "appliance_dark", x0 + 0.3, x1 - 0.3, d - 1.0, face,
             h - 6.5, h - 1.2)
        _add(parts, "oven-door", "appliance", x0 + 0.3, x1 - 0.3, d - 1.0, face,
             7.0, h - 7.0)
        _add(parts, "oven-window", "appliance_dark", x0 + 5.0, x1 - 5.0, face,
             face + 0.15, 12.0, h - 12.0)
        _add(parts, "handle", "hardware", x0 + 3.0, x1 - 3.0, face, face + 1.8,
             h - 9.0, h - 8.2)
        _add(parts, "drawer", "appliance", x0 + 0.3, x1 - 0.3, d - 1.0, face, 0.8, 6.5)
    elif kind == "dishwasher":
        kick = 4.0
        _add(parts, "toe-kick", "kick", x0, x1, 0.0, d - 3.0, 0.0, kick)
        _add(parts, "body", "appliance", x0, x1, 0.0, d - 1.0, kick, h)
        _add(parts, "door", "appliance", x0 + 0.2, x1 - 0.2, d - 1.0, face,
             kick + 0.3, h - 4.8)
        _add(parts, "controls", "appliance_dark", x0 + 0.2, x1 - 0.2, d - 1.0, face,
             h - 4.5, h - 0.3)
        _add(parts, "handle", "hardware", x0 + 3.0, x1 - 3.0, face, face + 1.6,
             h - 7.2, h - 6.4)
    elif kind == "hood":
        # a canopy, a stepped shoulder and a chimney against the wall
        lip = min(6.0, h * 0.35)
        _add(parts, "canopy", "appliance", x0, x1, 0.0, d, 0.0, lip)
        _add(parts, "filters", "appliance_dark", x0 + 1.5, x1 - 1.5, 1.5, d - 1.5,
             -0.25, 0.0)
        _add(parts, "controls", "appliance_dark", x0 + 4.0, x1 - 4.0, d, d + 0.2,
             1.0, lip - 1.0)
        _add(parts, "shoulder", "appliance", x0 + w * 0.15, x1 - w * 0.15, 0.0,
             d * 0.8, lip, lip + 3.0)
        cw = min(12.0, w * 0.45) / 2.0
        _add(parts, "chimney", "appliance", -cw, cw, 0.0, min(11.0, d * 0.6),
             lip + 3.0, h)
    elif kind == "microwave":
        _add(parts, "body", "appliance", x0, x1, 0.0, d - 1.0, 0.0, h)
        split = x1 - w * 0.24
        _add(parts, "door", "appliance", x0 + 0.2, split - 0.1, d - 1.0, face,
             2.0, h - 0.3)
        _add(parts, "window", "appliance_dark", x0 + 2.2, split - 2.2, face,
             face + 0.15, 4.0, h - 2.5)
        _add(parts, "panel", "appliance_dark", split + 0.1, x1 - 0.2, d - 1.0, face,
             2.0, h - 0.3)
        _add(parts, "handle", "hardware", split - 1.6, split - 0.9, face, face + 1.4,
             4.0, h - 2.5)
        _add(parts, "vent", "appliance_dark", x0 + 0.2, x1 - 0.2, d - 1.0, face,
             0.2, 1.8)
    elif kind in ("washer", "dryer"):
        _add(parts, "body", "appliance", x0, x1, 0.0, d - 1.0, 0.0, h)
        _add(parts, "front", "appliance", x0 + 0.2, x1 - 0.2, d - 1.0, face,
             0.5, h - 6.0)
        _add(parts, "controls", "appliance_dark", x0 + 0.2, x1 - 0.2, d - 1.0, face,
             h - 5.7, h - 0.3)
        side = min(w, h - 12.0) * 0.52
        _add(parts, "window", "appliance_dark", -side / 2.0, side / 2.0, face,
             face + 0.2, (h - 6.0) / 2.0 - side / 2.0, (h - 6.0) / 2.0 + side / 2.0)
    elif kind == "wine_cooler":
        kick = 4.0
        _add(parts, "toe-kick", "kick", x0, x1, 0.0, d - 3.0, 0.0, kick)
        _add(parts, "body", "appliance_dark", x0, x1, 0.0, d - 1.0, kick, h)
        for name, a, b in (("frame-l", x0 + 0.2, x0 + 2.0),
                           ("frame-r", x1 - 2.0, x1 - 0.2)):
            _add(parts, name, "appliance", a, b, d - 1.0, face, kick + 0.3, h - 0.3)
        _add(parts, "frame-b", "appliance", x0 + 2.0, x1 - 2.0, d - 1.0, face,
             kick + 0.3, kick + 2.3)
        _add(parts, "frame-t", "appliance", x0 + 2.0, x1 - 2.0, d - 1.0, face,
             h - 2.3, h - 0.3)
        _add(parts, "window", "glass", x0 + 2.0, x1 - 2.0, d - 1.0, face - 0.3,
             kick + 2.3, h - 2.3)
        n_racks = 5
        for i in range(1, n_racks + 1):
            z = kick + 2.3 + (h - kick - 4.6) * i / (n_racks + 1)
            _add(parts, f"rack-{i}", "hardware", x0 + 2.2, x1 - 2.2, face - 0.3,
                 face - 0.2, z - 0.15, z + 0.15)
        _add(parts, "handle", "hardware", x1 - 1.4, x1 - 0.7, face, face + 1.6,
             kick + 8.0, h - 8.0)
    elif kind == "microwave_drawer":
        kick = 4.0
        _add(parts, "toe-kick", "kick", x0, x1, 0.0, d - 3.0, 0.0, kick)
        _add(parts, "body", "appliance", x0, x1, 0.0, d - 1.0, kick, h)
        _add(parts, "panel", "appliance", x0 + 0.2, x1 - 0.2, d - 1.0, face,
             kick + 0.3, h - 16.0)
        _add(parts, "drawer", "appliance", x0 + 0.2, x1 - 0.2, d - 1.0, face,
             h - 15.7, h - 0.3)
        _add(parts, "window", "appliance_dark", x0 + 2.0, x1 - 2.0, face,
             face + 0.15, h - 11.5, h - 4.5)
        _add(parts, "controls", "appliance_dark", x0 + 2.0, x1 - 2.0, face,
             face + 0.15, h - 3.5, h - 1.0)
        _add(parts, "handle", "hardware", x0 + 3.0, x1 - 3.0, face, face + 1.6,
             h - 14.2, h - 13.4)
    else:
        _add(parts, "body", "appliance", x0, x1, 0.0, d, 0.0, h)


def _moved(parts, dx=0.0, flip_depth=None, df=0.0, dz=0.0):
    """Copies of `parts` shifted by `dx` / `dz`, and -- for the cabinets under
    an island, whose doors face the other way -- turned back to front about
    a cabinet `flip_depth` deep, then set `df` out from the island's edge."""
    out = []
    for p in parts:
        quad = tuple((x + dx, (df + flip_depth - f) if flip_depth is not None
                      else f + df) for x, f in p.quad)
        out.append(Part(p.name, p.role, quad, p.z0 + dz, p.z1 + dz))
    return out


def _island(parts, st, style):
    """An island. Along the DOOR side (the plan symbol's top) stand whatever
    its slots name -- base cabinets, drawer bases, a sink base, a dishwasher --
    built by the same code that builds them against a wall, turned to face
    out. Along the other side the top overhangs a row of short-backed stools.
    One countertop covers all of it, open over a sink's bowls."""
    w, depth, h = st["width_in"], st["depth_in"], st["height_in"]
    x0 = -w / 2.0
    cab_d, setback = ISLAND_CABINET_D, ISLAND_FRONT_SETBACK
    slots = island_slots(st)
    holes = []
    # Slot 1 is at the LEFT as you stand facing the doors. The doors are on
    # the f = 0 side, where a viewer's left is +x, so the run is laid out
    # from +x toward -x.
    cursor = -x0
    for n, (code, width, kind, over) in enumerate(slots, start=1):
        sub = dict(st)
        sub.update(over)
        sub.update({"type": kind, "width_in": width, "depth_in": cab_d,
                    "top_on": False, "doors": "auto"})
        sub.setdefault("front", "drawer_over_doors")
        if kind == "sink_base":
            sub["front"] = "false_front"
        made = []
        cx = cursor - width / 2.0
        top_z = h + st["top_thickness_in"]
        if kind == "appliance" and over.get("appliance") == "range":
            # a range stands THROUGH the top: its cooktop is the counter
            # there, and an island range has no backguard
            sub["height_in"] = top_z
            _appliance(made, sub)
            made = [p for p in made if p.name != "backguard"]
            holes.append((cx - width / 2.0, cx + width / 2.0, 0.0,
                          setback + cab_d))
        elif kind == "appliance":
            sub["height_in"] = min(34.0, h)
            _appliance(made, sub)
        else:
            _base_like(made, sub, style)
        if over.get("cooktop"):
            # a glass cooktop let into the counter, four burners on it
            a, b = cx - width / 2.0 + 1.5, cx + width / 2.0 - 1.5
            f0, f1 = setback + 2.0, setback + cab_d - 2.0
            _add(parts, f"slot{n}-{code}-cooktop", "appliance_dark", a, b, f0, f1,
                 top_z, top_z + 0.25)
            for i, (bx, bf, r) in enumerate((
                    (a + (b - a) * 0.27, f0 + (f1 - f0) * 0.30, 3.6),
                    (a + (b - a) * 0.73, f0 + (f1 - f0) * 0.30, 2.8),
                    (a + (b - a) * 0.27, f0 + (f1 - f0) * 0.72, 2.8),
                    (a + (b - a) * 0.73, f0 + (f1 - f0) * 0.72, 3.6)), start=1):
                _oval(parts, f"slot{n}-{code}-burner-{i}", "burner", bx, bf, r, r,
                      top_z + 0.25, top_z + 0.32, n=12)
        tagged = [Part(f"slot{n}-{code}-{p.name}", p.role, p.quad, p.z0, p.z1)
                  for p in made]
        parts.extend(_moved(tagged, dx=cx, flip_depth=cab_d, df=setback))
        if kind == "sink_base":
            bowls = []
            for a, b, f0, f1 in _sink(bowls, sub, -width / 2.0, width / 2.0,
                                      cab_d, h + st["top_thickness_in"]):
                holes.append((a + cx, b + cx, setback + cab_d - f1,
                              setback + cab_d - f0))
            parts.extend(_moved([Part(f"slot{n}-{p.name}", p.role, p.quad,
                                      p.z0, p.z1) for p in bowls],
                                dx=cx, flip_depth=cab_d, df=setback))
        cursor -= width
    if not slots:                        # nothing under it: legs and a panel
        _add(parts, "base", "cabinet", x0 + 2.0, -x0 - 2.0, setback,
             setback + cab_d, st["toe_kick_h_in"], h)
    # the finished back the stools look at, and the two end panels
    back = setback + cab_d
    kick = min(max(st["toe_kick_h_in"], 0.0), h - 6.0)
    _add(parts, "back-panel", "cabinet", x0, -x0, back, back + 0.75, kick, h)
    if st["top_on"]:
        _top_grid(parts, st, x0, -x0, depth, h, holes)
    for i, (_cx, a, b, f0, f1) in enumerate(island_stools(st)):
        name = f"stool-{i + 1}"
        _add(parts, f"{name}-seat", "stool", a, b, f0, f1,
             STOOL_SEAT_Z - 2.0, STOOL_SEAT_Z)
        for j, (lx, lf) in enumerate(((a, f0), (b - 1.2, f0), (a, f1 - 1.2),
                                      (b - 1.2, f1 - 1.2)), start=1):
            _add(parts, f"{name}-leg-{j}", "hardware", lx, lx + 1.2, lf,
                 lf + 1.2, 0.0, STOOL_SEAT_Z - 2.0)
        _add(parts, f"{name}-rung", "hardware", a + 1.2, b - 1.2, f0 + 0.2,
             f0 + 1.0, 8.0, 8.8)
        # the SHORT BACK, on the side away from the island
        _add(parts, f"{name}-back", "stool", a, b, f1 - 1.2, f1,
             STOOL_SEAT_Z + 3.0, STOOL_SEAT_Z + 8.0)
        for j, lx in enumerate((a, b - 1.2), start=1):
            _add(parts, f"{name}-post-{j}", "hardware", lx, lx + 1.2, f1 - 1.2,
                 f1, STOOL_SEAT_Z, STOOL_SEAT_Z + 3.0)


def island_stools(st):
    """[(centre x, x0, x1, f0, f1)] -- one per seat, evenly along the side
    away from the doors, tucked under the overhang clear of the back panel.
    The 3D stools and the plan symbol both read this."""
    w, depth = st["width_in"], st["depth_in"]
    seats = int(st["seats"])
    back = ISLAND_FRONT_SETBACK + ISLAND_CABINET_D
    f1 = depth - 0.5
    f0 = max(f1 - STOOL, back + 0.9)
    if seats <= 0 or f1 - f0 < 6.0:
        return []
    pitch = w / seats
    size = max(min(STOOL, pitch - 1.0), 6.0)    # crowded seats get narrower stools
    out = []
    for i in range(seats):
        cx = -w / 2.0 + pitch * (i + 0.5)
        out.append((cx, cx - size / 2.0, cx + size / 2.0, f0, f1))
    return out


def _top_grid(parts, st, x0, x1, front, z, holes):
    """An island's countertop over `x0..x1`, `0..front`, left open over each
    hole `(a, b, f0, f1)` -- a sink's bowl, a range. Holes may differ in
    depth, so the top is laid in strips between their edges."""
    t = st["top_thickness_in"]
    xs = sorted({x0, x1} | {min(max(v, x0), x1) for a, b, _f0, _f1 in holes
                            for v in (a, b)})
    n = 0
    for a, b in zip(xs[:-1], xs[1:], strict=False):
        if b - a <= 1e-6:
            continue
        mid = (a + b) / 2.0
        hole = next((h for h in holes if h[0] - 1e-6 <= mid <= h[1] + 1e-6), None)
        spans = ([(0.0, front)] if hole is None
                 else [(0.0, hole[2]), (hole[3], front)])
        for f0, f1 in spans:
            n += 1
            _add(parts, "countertop" if n == 1 else f"countertop-{n}",
                 "countertop", a, b, f0, f1, z, z + t)


def island_plan(st):
    """The island's PLAN SYMBOL from its parameters (0338), in the cabinet
    frame -- x across, f down the symbol from the door side:

        top      (x0, f0, x1, f1)             the countertop's outline
        back     f                            the line where the cabinets end
        slots    [(x0, x1, code)]             what stands under it
        bowls    [(x0, f0, x1, f1)]           sink bowls
        hobs     [(x0, f0, x1, f1)]           cooktops and ranges
        stools   [(x0, f0, x1, f1)]           one per seat
    """
    w, depth = st["width_in"], st["depth_in"]
    setback, cab_d = ISLAND_FRONT_SETBACK, ISLAND_CABINET_D
    slots, bowls, hobs = [], [], []
    cursor = w / 2.0
    for code, width, kind, over in island_slots(st):
        a, b = cursor - width, cursor
        slots.append((a, b, code))
        if kind == "sink_base":
            sub = dict(st, **over)
            made = []
            for ha, hb, f0, f1 in _sink(made, sub, -width / 2.0, width / 2.0,
                                        cab_d, 0.0):
                cx = (a + b) / 2.0
                bowls.append((ha + cx, setback + cab_d - f1, hb + cx,
                              setback + cab_d - f0))
        if over.get("cooktop") or over.get("appliance") == "range":
            hobs.append((a + 1.5, setback + 2.0, b - 1.5, setback + cab_d - 2.0))
        cursor -= width
    return {"top": (-w / 2.0, 0.0, w / 2.0, depth), "back": setback + cab_d,
            "slots": slots, "bowls": bowls, "hobs": hobs,
            "stools": [(a, f0, b, f1) for _cx, a, b, f0, f1 in island_stools(st)]}


# --------------------------------------------------------------------------
# fixtures (0338)
# --------------------------------------------------------------------------
def _toilet(parts, st):
    """Tank against the wall, an oval bowl on a pedestal, seat and lid."""
    h = st["height_in"]
    cf = 17.5                                   # the bowl's centre, off the wall
    half = st["width_in"] / 2.0
    _add(parts, "tank", "porcelain", -half + 0.5, half - 0.5, 0.4, 8.0, 14.5,
         h - 1.5)
    _add(parts, "tank-lid", "porcelain", -half, half, 0.0, 8.4, h - 1.5, h)
    _add(parts, "lever", "hardware", -half + 1.0, -half + 3.5, 8.0, 8.6,
         h - 5.0, h - 4.2)
    _add(parts, "neck", "porcelain", -4.5, 4.5, 6.0, 11.0, 6.0, 14.5)
    _oval(parts, "pedestal", "porcelain", 0.0, cf - 1.0, 4.6, 7.2, 0.0, 6.0)
    _oval(parts, "bowl-lower", "porcelain", 0.0, cf - 0.5, 5.8, 8.4, 6.0, 10.5)
    _oval(parts, "bowl", "porcelain", 0.0, cf, 7.0, 9.5, 10.5, 14.5)
    _oval(parts, "seat", "porcelain", 0.0, cf, 7.3, 9.8, 14.5, 15.2)
    _oval(parts, "lid", "porcelain", 0.0, cf + 0.2, 6.9, 9.3, 15.2, 15.8)
    _add(parts, "hinge", "hardware", -3.5, 3.5, 8.0, 9.2, 14.5, 15.6)


def _bathtub(parts, st):
    """An alcove tub: a shell with a rim, an open well with eased corners, a
    drain, and a filler at the wall end (f = 0)."""
    w, length, h = st["width_in"], st["depth_in"], st["height_in"]
    x0, x1 = -w / 2.0, w / 2.0
    rim, floor = 3.0, min(4.0, h * 0.3)       # 4 in: the symbol's own well floor
    _add(parts, "floor", "porcelain", x0, x1, 0.0, length, 0.0, floor)
    _add(parts, "wall-l", "porcelain", x0, x0 + rim, 0.0, length, floor, h)
    _add(parts, "wall-r", "porcelain", x1 - rim, x1, 0.0, length, floor, h)
    _add(parts, "wall-head", "porcelain", x0 + rim, x1 - rim, 0.0, rim + 1.5,
         floor, h)
    _add(parts, "wall-foot", "porcelain", x0 + rim, x1 - rim, length - rim,
         length, floor, h)
    e = 4.0                                     # the well's eased corners
    a, b, f0, f1 = x0 + rim, x1 - rim, rim + 1.5, length - rim
    for name, ring in (
            ("ease-1", [(a, f0), (a + e, f0), (a, f0 + e)]),
            ("ease-2", [(b, f0), (b, f0 + e), (b - e, f0)]),
            ("ease-3", [(b, f1), (b - e, f1), (b, f1 - e)]),
            ("ease-4", [(a, f1), (a, f1 - e), (a + e, f1)])):
        _ring(parts, name, "porcelain", ring, floor, h)
    _oval(parts, "drain", "hardware", 0.0, f0 + 6.0, 1.1, 1.1, floor,
          floor + 0.12, n=10)
    _add(parts, "overflow", "hardware", -1.0, 1.0, f0, f0 + 0.15, h - 7.0, h - 5.0)
    _add(parts, "filler-post", "hardware", -0.7, 0.7, 1.2, 2.6, h, h + 5.0)
    _add(parts, "filler-spout", "hardware", -0.55, 0.55, 1.2, f0 + 3.0,
         h + 4.0, h + 5.0)
    for name, cx in (("tap-l", -4.5), ("tap-r", 4.5)):
        _add(parts, name, "hardware", cx - 0.9, cx + 0.9, 1.0, 2.8, h, h + 2.2)


def _bookshelf(parts, st):
    """Two sides, a top, a plinth and a back; shelves spaced evenly; and,
    when asked, a deterministic run of books on each."""
    w, d, h = st["width_in"], st["depth_in"], st["height_in"]
    x0, x1 = -w / 2.0, w / 2.0
    t, kick = 0.75, min(3.0, h * 0.1)
    _add(parts, "side-l", "cabinet", x0, x0 + t, 0.0, d, 0.0, h)
    _add(parts, "side-r", "cabinet", x1 - t, x1, 0.0, d, 0.0, h)
    _add(parts, "top", "cabinet", x0 + t, x1 - t, 0.0, d, h - t, h)
    _add(parts, "back", "cabinet", x0 + t, x1 - t, 0.0, 0.25, kick, h - t)
    _add(parts, "plinth", "cabinet", x0 + t, x1 - t, d - 1.5, d - 0.75, 0.0, kick)
    n = int(st["shelves"])
    lo, hi = kick, h - t
    levels = [lo + (hi - lo) * i / (n + 1) for i in range(n + 1)]
    for i, z in enumerate(levels):
        _add(parts, "bottom" if i == 0 else f"shelf-{i}", "cabinet",
             x0 + t, x1 - t, 0.25, d - 0.4, z, z + t)
    if not st["books"]:
        return
    seed = 12345
    for i, z in enumerate(levels):
        clear = (levels[i + 1] if i + 1 < len(levels) else hi) - z - t
        if clear < 5.0:
            continue
        x = x0 + t + 0.3
        seed = (seed * 1103515245 + 12345 + i) % 2147483648
        stop = x0 + t + (w - 2 * t) * (0.55 + (seed % 1000) / 1000.0 * 0.4)
        k = 0
        while True:
            seed = (seed * 1103515245 + 12345) % 2147483648
            bw = 0.9 + (seed % 100) / 100.0 * 1.4
            seed = (seed * 1103515245 + 12345) % 2147483648
            bh = min(clear - 0.6, 11.0) * (0.68 + (seed % 100) / 100.0 * 0.3)
            seed = (seed * 1103515245 + 12345) % 2147483648
            bd = min(max(d - 2.0, 2.0), 6.0 + (seed % 100) / 100.0 * 3.0)
            if x + bw > stop:
                break
            k += 1
            _add(parts, f"book-{i + 1}-{k}", f"book_{seed % 5 + 1}", x, x + bw - 0.06,
                 d - 0.8 - bd, d - 0.8, z + t, z + t + bh)
            x += bw


def _fireplace(parts, st):
    """A gas fireplace: hearth, a surround with an open firebox, logs, flames
    when lit, and a mantel shelf."""
    w, d, h = st["width_in"], st["depth_in"], st["height_in"]
    x0, x1 = -w / 2.0, w / 2.0
    body = max(d - 6.0, 6.0)                    # the surround's depth
    leg = max(w / 6.0, 4.0)
    top = h - 3.0                               # underside of the mantel
    mouth = 2.0 + (top - 2.0) * 0.64            # top of the firebox opening
    a, b = x0 + leg, x1 - leg
    _add(parts, "hearth", "hearth", x0, x1, 0.0, d, 0.0, 2.0)
    _add(parts, "leg-l", "surround", x0, a, 0.0, body, 2.0, top)
    _add(parts, "leg-r", "surround", b, x1, 0.0, body, 2.0, top)
    _add(parts, "header", "surround", a, b, 0.0, body, mouth, top)
    _add(parts, "mantel", "cabinet", x0, x1, 0.0, min(body + 2.5, d), top, h)
    _add(parts, "firebox-back", "firebox", a, b, 0.0, 1.5, 2.0, mouth)
    _add(parts, "firebox-l", "firebox", a, a + 0.4, 1.5, body - 0.6, 2.0, mouth)
    _add(parts, "firebox-r", "firebox", b - 0.4, b, 1.5, body - 0.6, 2.0, mouth)
    _add(parts, "firebox-floor", "firebox", a, b, 1.5, body, 2.0, 2.3)
    _add(parts, "firebox-roof", "firebox", a, b, 1.5, body - 0.6, mouth - 0.4, mouth)
    for name, r in (("trim-l", (a - 1.0, a, 2.0, mouth + 1.0)),
                    ("trim-r", (b, b + 1.0, 2.0, mouth + 1.0)),
                    ("trim-t", (a, b, mouth, mouth + 1.0))):
        _add(parts, name, "appliance_dark", r[0], r[1], body, body + 0.3, r[2], r[3])
    span = b - a
    mid_f = 1.5 + (body - 1.5) * 0.5
    _add(parts, "log-1", "log", a + span * 0.12, b - span * 0.12, mid_f - 3.2,
         mid_f - 0.8, 2.3, 4.7)
    _add(parts, "log-2", "log", a + span * 0.18, b - span * 0.18, mid_f + 0.4,
         mid_f + 2.8, 2.3, 4.7)
    _add(parts, "log-3", "log", a + span * 0.26, b - span * 0.26, mid_f - 1.4,
         mid_f + 1.0, 4.7, 6.9)
    if st["lit"]:
        room = mouth - 8.5
        for i, (u, tall) in enumerate(((0.22, 0.55), (0.36, 0.9), (0.5, 0.7),
                                       (0.64, 1.0), (0.78, 0.5)), start=1):
            cx = a + span * u
            _add(parts, f"flame-{i}", "flame", cx - span * 0.045,
                 cx + span * 0.045, mid_f - 0.3, mid_f + 0.3, 6.9,
                 6.9 + max(room * tall, 1.0))


def _grab_bar(parts, st):
    """A grab bar: a round-ish bar `BAR_CLEAR` off the wall on two standoffs
    with their flanges. Built from z = 0; the caller lifts it to its height."""
    length = st["length_in"]
    r = BAR_DIAMETER / 2.0
    f0, f1 = BAR_CLEAR, BAR_CLEAR + BAR_DIAMETER
    if st["bar"] == "vertical":
        _add(parts, "bar", "hardware", -r, r, f0, f1, 0.0, length)
        for name, z in (("lower", 0.0), ("upper", length - 3.0)):
            _add(parts, f"flange-{name}", "hardware", -1.5, 1.5, 0.0, 0.3, z, z + 3.0)
            _add(parts, f"standoff-{name}", "hardware", -r, r, 0.3, f0,
                 z + 1.5 - r, z + 1.5 + r)
        return
    _add(parts, "bar", "hardware", -length / 2.0, length / 2.0, f0, f1,
         1.5 - r, 1.5 + r)
    for name, cx in (("left", -length / 2.0 + 1.5), ("right", length / 2.0 - 1.5)):
        _add(parts, f"flange-{name}", "hardware", cx - 1.5, cx + 1.5, 0.0, 0.3,
             0.0, 3.0)
        _add(parts, f"standoff-{name}", "hardware", cx - r, cx + r, 0.3, f0,
             1.5 - r, 1.5 + r)


def _monitor(parts, name, cx, top, width=24.0):
    """A flat monitor on a stand, facing the sitter (+f)."""
    half = width / 2.0
    _add(parts, f"{name}-foot", "appliance_dark", cx - 4.5, cx + 4.5, 4.5, 10.5,
         top, top + 0.5)
    _add(parts, f"{name}-neck", "appliance_dark", cx - 1.0, cx + 1.0, 6.2, 7.2,
         top + 0.5, top + 9.0)
    _add(parts, f"{name}-case", "appliance_dark", cx - half, cx + half, 7.2, 8.2,
         top + 4.5, top + 4.5 + width * 0.6)
    _add(parts, f"{name}-screen", "screen", cx - half + 0.6, cx + half - 0.6,
         8.2, 8.3, top + 5.3, top + 3.9 + width * 0.6)


def _computer(parts, st, top, depth):
    """What stands on the desk: `computer` says which."""
    kind = st["computer"]
    if kind == "none":
        return
    if kind == "laptop":
        _add(parts, "laptop-base", "device", -6.5, 6.5, depth - 17.0, depth - 8.0,
             top, top + 0.6)
        _add(parts, "laptop-keys", "appliance_dark", -5.5, 5.5, depth - 15.5,
             depth - 11.5, top + 0.6, top + 0.65)
        _add(parts, "laptop-lid", "device", -6.5, 6.5, depth - 17.6, depth - 17.0,
             top, top + 9.0)
        _add(parts, "laptop-screen", "screen", -6.0, 6.0, depth - 17.0,
             depth - 16.92, top + 0.9, top + 8.5)
        return
    if kind == "dual":
        _monitor(parts, "monitor-1", -11.5, top, 22.0)
        _monitor(parts, "monitor-2", 11.5, top, 22.0)
    else:
        _monitor(parts, "monitor", 0.0, top)
    _add(parts, "keyboard", "appliance_dark", -8.5, 8.5, depth - 12.0,
         depth - 6.0, top, top + 0.7)
    _oval(parts, "mouse", "appliance_dark", 13.0, depth - 9.0, 1.3, 2.1, top,
          top + 1.2, n=10)


def _desk_parts(parts, st, w, depth):
    """A desk `w` x `depth`: a top on end panels, a modesty panel at the
    back (f = 0), drawer pedestals facing the sitter, and the computer."""
    h = st["height_in"]
    x0, x1 = -w / 2.0, w / 2.0
    top = h - DESK_TOP_T
    _add(parts, "top", "cabinet", x0, x1, 0.0, depth, top, h)
    side = st["pedestal"]
    ped = min(16.0, (w - CHAIR - 2.0) / 2.0) if side == "both" else min(16.0, w / 3.0)
    for tag, on, a, b in (("l", side in ("left", "both"), x0 + 1.0, x0 + 1.0 + ped),
                          ("r", side in ("right", "both"), x1 - 1.0 - ped, x1 - 1.0)):
        if on and ped >= 9.0:
            _add(parts, f"pedestal-{tag}", "cabinet", a, b, 2.0, depth - 2.25,
                 0.0, top)
            zs = [1.0, 12.0, 20.0, top - 0.4]
            for i in range(3):
                _add(parts, f"drawer-{tag}-{i + 1}", "cabinet", a + 0.3, b - 0.3,
                     depth - 2.25, depth - 1.5, zs[i] + 0.2, zs[i + 1] - 0.2)
                mid = (zs[i] + zs[i + 1]) / 2.0
                _add(parts, f"pull-{tag}-{i + 1}", "hardware", (a + b) / 2.0 - 2.5,
                     (a + b) / 2.0 + 2.5, depth - 1.5, depth - 0.5,
                     mid - 0.3, mid + 0.3)
        else:
            edge = x0 + 1.0 if tag == "l" else x1 - 2.5
            _add(parts, f"panel-{tag}", "cabinet", edge, edge + 1.5, 2.0,
                 depth - 2.0, 0.0, top)
    _add(parts, "modesty", "cabinet", x0 + 2.5, x1 - 2.5, 3.0, 3.75, 9.0, top)
    _computer(parts, st, h, depth)


def _desk(parts, st):
    _desk_parts(parts, st, st["width_in"], st["depth_in"])


def _office_chair(parts, st):
    """A task chair, its back at f = 0: a five-star base on casters, a gas
    column, an upholstered seat and back, and arms."""
    c = CHAIR / 2.0                             # the seat's centre, x and f
    seat = CHAIR_SEAT_Z
    for i in range(5):                          # the star, and a caster on each
        ang = math.radians(90.0 + 72.0 * i)
        ux, uf = math.cos(ang), math.sin(ang)
        px, pf = -uf, ux
        tip = (ux * 11.0, c + 0.3 + uf * 11.0)
        root = (ux * 1.0, c + 0.3 + uf * 1.0)
        _ring(parts, f"leg-{i + 1}", "appliance_dark",
              [(root[0] + px * 1.0, root[1] + pf * 1.0),
               (tip[0] + px * 0.7, tip[1] + pf * 0.7),
               (tip[0] - px * 0.7, tip[1] - pf * 0.7),
               (root[0] - px * 1.0, root[1] - pf * 1.0)], 2.2, 3.6)
        _oval(parts, f"caster-{i + 1}", "appliance_dark", ux * 10.3,
              c + 0.3 + uf * 10.3, 1.1, 1.1, 0.0, 2.2, n=8)
    _oval(parts, "hub", "appliance_dark", 0.0, c + 0.3, 1.8, 1.8, 2.2, 4.2, n=10)
    _oval(parts, "column", "hardware", 0.0, c + 0.3, 1.0, 1.0, 4.2, seat - 4.0, n=10)
    _add(parts, "mechanism", "appliance_dark", -4.0, 4.0, c - 3.0, c + 5.0,
         seat - 4.0, seat - 3.0)
    _oval(parts, "seat", "upholstery", 0.0, c + 1.5, 9.5, 9.0, seat - 3.0, seat,
          n=16)
    _add(parts, "back-post", "appliance_dark", -1.2, 1.2, 1.5, 4.5, seat - 4.0,
         seat + 6.0)
    for name, ring in (
            ("back-l", [(-9.0, 2.2), (-3.0, 0.0), (-3.0, 2.0), (-8.2, 4.0)]),
            ("back-c", [(-3.0, 0.0), (3.0, 0.0), (3.0, 2.0), (-3.0, 2.0)]),
            ("back-r", [(3.0, 0.0), (9.0, 2.2), (8.2, 4.0), (3.0, 2.0)])):
        _ring(parts, name, "upholstery", ring, seat + 4.0, st["height_in"])
    if st["arms"]:
        _add(parts, "arm-bar", "appliance_dark", -c + 0.4, c - 0.4, c - 0.8,
             c + 0.8, seat - 3.8, seat - 3.0)
        for tag, a, b in (("l", -c, -c + 2.0), ("r", c - 2.0, c)):
            _add(parts, f"arm-{tag}-post", "appliance_dark", a + 0.4, b - 0.4,
                 c - 1.0, c + 1.0, seat - 3.8, seat + 6.2)
            _add(parts, f"arm-{tag}-pad", "appliance_dark", a, b, c - 5.0, c + 5.0,
                 seat + 6.2, seat + 7.2)


def _office_set(parts, st):
    """A desk with its chair drawn up to it, facing the desk."""
    w, depth = st["width_in"], st["depth_in"]
    _desk_parts(parts, st, w, SET_DESK_D)
    chair = []
    _office_chair(chair, dict(st, height_in=40.0))
    # clear of a single drawer pedestal: slid just far enough the other way
    side = st["pedestal"]
    inner = w / 2.0 - 1.0 - min(16.0, w / 3.0)      # the pedestal's inside face
    slide = max(0.0, CHAIR / 2.0 + 1.0 - inner)
    dx = {"right": -slide, "left": slide}.get(side, 0.0)
    named = [Part(f"chair-{p.name}", p.role, p.quad, p.z0, p.z1) for p in chair]
    parts.extend(_moved(named, dx=dx, flip_depth=CHAIR, df=depth - CHAIR))


def _pedal_bin(parts, st):
    """A step bin: a round body on a dark base ring, a domed lid hinged at
    the back (f = 0), and the pedal out at the front."""
    w, d, h = st["width_in"], st["depth_in"], st["height_in"]
    r = w / 2.0
    cf = r                                      # the body stands at the back
    _oval(parts, "base", "appliance_dark", 0.0, cf, r, r, 0.0, 1.4)
    _oval(parts, "body", "appliance", 0.0, cf, r - 0.3, r - 0.3, 1.4, h - 2.4)
    _oval(parts, "rim", "appliance_dark", 0.0, cf, r, r, h - 2.4, h - 1.9)
    _oval(parts, "lid", "appliance", 0.0, cf, r - 0.1, r - 0.1, h - 1.9, h - 0.9)
    _oval(parts, "lid-crown", "appliance", 0.0, cf, r * 0.72, r * 0.72, h - 0.9, h)
    _add(parts, "hinge", "appliance_dark", -2.0, 2.0, 0.0, 0.9, h - 3.4, h - 1.2)
    _add(parts, "pedal-arm", "appliance_dark", -0.6, 0.6, cf + r - 1.0, d - 2.5,
         0.5, 1.1)
    _add(parts, "pedal", "appliance_dark", -2.3, 2.3, d - 3.2, d, 0.5, 1.3)


def _dog_crate(parts, st):
    """A wire crate: a tube frame, wires up the sides and across the top, a
    pan, a door in one end with its latch, and (when asked) a bed."""
    w, d, h = st["width_in"], st["depth_in"], st["height_in"]
    x0, x1 = -w / 2.0, w / 2.0
    t, wire, role = 0.4, 0.14, "appliance_dark"
    _add(parts, "pan", role, x0 + t, x1 - t, t, d - t, 0.0, 1.0)
    if st["bed"]:
        _add(parts, "bed", "upholstery", x0 + 2.0, x1 - 2.0, 2.0, d - 2.0, 1.0, 3.2)
        _add(parts, "bolster", "upholstery", x0 + 2.0, x1 - 2.0, 2.0, 5.0, 3.2, 5.6)
    for i, (px, pf) in enumerate(((x0, 0.0), (x1 - t, 0.0), (x0, d - t),
                                  (x1 - t, d - t)), start=1):
        _add(parts, f"post-{i}", role, px, px + t, pf, pf + t, 0.0, h)
    for tag, z in (("low", 0.0), ("high", h - t)):
        _add(parts, f"rail-back-{tag}", role, x0 + t, x1 - t, 0.0, t, z, z + t)
        _add(parts, f"rail-front-{tag}", role, x0 + t, x1 - t, d - t, d, z, z + t)
        _add(parts, f"rail-left-{tag}", role, x0, x0 + t, t, d - t, z, z + t)
        _add(parts, f"rail-right-{tag}", role, x1 - t, x1, t, d - t, z, z + t)
    pitch = 2.5
    nx = max(2, int(round((w - 2 * t) / pitch)))
    nf = max(2, int(round((d - 2 * t) / pitch)))
    off = (t - wire) / 2.0
    for i in range(1, nx):                      # the long sides and the top
        x = x0 + t + (w - 2 * t) * i / nx - wire / 2.0
        _add(parts, f"wire-back-{i}", role, x, x + wire, off, off + wire, t, h - t)
        _add(parts, f"wire-front-{i}", role, x, x + wire, d - off - wire, d - off,
             t, h - t)
        _add(parts, f"wire-top-x-{i}", role, x, x + wire, t, d - t,
             h - off - wire, h - off)
    for i in range(1, nf):                      # the ends
        f = t + (d - 2 * t) * i / nf - wire / 2.0
        _add(parts, f"wire-left-{i}", role, x0 + off, x0 + off + wire, f, f + wire,
             t, h - t)
        _add(parts, f"wire-right-{i}", role, x1 - off - wire, x1 - off, f,
             f + wire, t, h - t)
    for j in range(1, 4):                       # three hoops round the sides
        z = t + (h - 2 * t) * j / 4.0
        _add(parts, f"hoop-back-{j}", role, x0 + t, x1 - t, off, off + wire,
             z, z + wire)
        _add(parts, f"hoop-front-{j}", role, x0 + t, x1 - t, d - off - wire,
             d - off, z, z + wire)
        _add(parts, f"hoop-left-{j}", role, x0 + off, x0 + off + wire, t, d - t,
             z, z + wire)
        _add(parts, f"hoop-right-{j}", role, x1 - off - wire, x1 - off, t, d - t,
             z, z + wire)
    for i in range(1, 4):
        f = t + (d - 2 * t) * i / 4.0
        _add(parts, f"wire-top-f-{i}", role, x0 + t, x1 - t, f, f + wire,
             h - off - wire, h - off)
    # the door, in the +x end: a frame just inside the end, and its latch
    f0, f1 = d * 0.2, d * 0.8
    z0, z1 = 2.0, h - 3.0
    for name, r in (("door-jamb-1", (f0, f0 + 0.3, z0, z1)),
                    ("door-jamb-2", (f1 - 0.3, f1, z0, z1)),
                    ("door-sill", (f0, f1, z0, z0 + 0.3)),
                    ("door-head", (f0, f1, z1 - 0.3, z1))):
        _add(parts, name, role, x1 - t - 0.3, x1 - t, r[0], r[1], r[2], r[3])
    _add(parts, "latch", "hardware", x1 - t - 0.6, x1 - t - 0.3, f1 - 2.5,
         f1 + 1.0, (z0 + z1) / 2.0 - 0.3, (z0 + z1) / 2.0 + 0.3)
    _add(parts, "handle", role, x0 + w * 0.35, x1 - w * 0.35, d / 2.0 - 0.3,
         d / 2.0 + 0.3, h - t, h)


def _sofa_table(parts, st):
    """A console table: a top, an apron, four legs and low shelves."""
    w, d, h = st["width_in"], st["depth_in"], st["height_in"]
    x0, x1 = -w / 2.0, w / 2.0
    leg, top_t, inset = 2.0, 1.25, 1.0
    _add(parts, "top", "cabinet", x0, x1, 0.0, d, h - top_t, h)
    a, b, f0, f1 = x0 + inset, x1 - inset, inset, d - inset
    for i, (lx, lf) in enumerate(((a, f0), (b - leg, f0), (a, f1 - leg),
                                  (b - leg, f1 - leg)), start=1):
        _add(parts, f"leg-{i}", "cabinet", lx, lx + leg, lf, lf + leg, 0.0, h - top_t)
    apron = min(3.5, h * 0.15)
    z = h - top_t - apron
    _add(parts, "apron-back", "cabinet", a + leg, b - leg, f0 + 0.4, f0 + 1.2,
         z, h - top_t)
    _add(parts, "apron-front", "cabinet", a + leg, b - leg, f1 - 1.2, f1 - 0.4,
         z, h - top_t)
    _add(parts, "apron-left", "cabinet", a + 0.4, a + 1.2, f0 + leg, f1 - leg,
         z, h - top_t)
    _add(parts, "apron-right", "cabinet", b - 1.2, b - 0.4, f0 + leg, f1 - leg,
         z, h - top_t)
    n = min(int(st["shelves"]), 3)
    for i in range(1, n + 1):
        sz = 5.0 + (z - 5.0) * (i - 1) / max(n, 1)
        _add(parts, f"shelf-{i}", "cabinet", a + 0.3, b - 0.3, f0 + 0.3, f1 - 0.3,
             sz, sz + 0.75)


_FIXTURE_BUILDERS = {"toilet": _toilet, "bathtub": _bathtub,
                     "bookshelf": _bookshelf, "fireplace": _fireplace,
                     "grab_bar": _grab_bar, "desk": _desk,
                     "office_chair": _office_chair, "office_set": _office_set,
                     "pedal_bin": _pedal_bin, "dog_crate": _dog_crate,
                     "sofa_table": _sofa_table}


def _light(parts, st, ceiling_in):
    """A light as a simple fixture: a body, and a LENS that glows the light's
    colour. Ceiling fixtures hang from `ceiling_in`; a sconce sits on the
    wall (f = 0) at `floor_to_bottom_in`."""
    size = st["size_in"]
    r = size / 2.0
    top = float(ceiling_in)
    fx = st["fixture"]
    d = st["depth_in"]
    mid = d / 2.0
    if fx == "recessed":
        _add(parts, "trim", "fixture", -r, r, mid - r, mid + r, top - 0.4, top)
        _add(parts, "lens", "lens", -r + 0.8, r - 0.8, mid - r + 0.8, mid + r - 0.8,
             top - 0.6, top - 0.4)
    elif fx == "flush":
        _add(parts, "base", "fixture", -r, r, mid - r, mid + r, top - 1.2, top)
        _add(parts, "lens", "lens", -r + 1.0, r - 1.0, mid - r + 1.0, mid + r - 1.0,
             top - 4.5, top - 1.2)
    elif fx in ("pendant", "globe"):
        drop = max(st["drop_in"], 4.0) if fx == "pendant" else r + 2.0
        _add(parts, "canopy", "fixture", -2.5, 2.5, mid - 2.5, mid + 2.5,
             top - 1.0, top)
        _add(parts, "stem", "fixture", -0.3, 0.3, mid - 0.3, mid + 0.3,
             top - drop, top - 1.0)
        shade = size * (0.7 if fx == "pendant" else 1.0)
        if fx == "pendant":
            _add(parts, "shade", "fixture", -r, r, mid - r, mid + r,
                 top - drop - shade * 0.3, top - drop)
            _add(parts, "lens", "lens", -r + 1.0, r - 1.0, mid - r + 1.0,
                 mid + r - 1.0, top - drop - shade, top - drop - shade * 0.3)
        else:
            _add(parts, "lens", "lens", -r, r, mid - r, mid + r,
                 top - drop - size, top - drop)
    elif fx == "linear":
        w2 = d / 2.0
        _add(parts, "housing", "fixture", -r, r, mid - w2, mid + w2, top - 2.0, top)
        _add(parts, "lens", "lens", -r + 0.5, r - 0.5, mid - w2 + 0.8,
             mid + w2 - 0.8, top - 2.6, top - 2.0)
    elif fx == "table":
        # stands on a table top at `floor_to_bottom_in`; `drop_in` is the
        # lamp's own height, `size_in` its shade's width
        z0 = max(st["floor_to_bottom_in"], 0.0)
        tall = min(max(st["drop_in"], 10.0), 48.0)
        shade = tall * 0.38
        s0 = z0 + tall - shade
        _oval(parts, "lens", "lens", 0.0, mid, r, r, s0, s0 + shade * 0.4)
        _oval(parts, "lens-mid", "lens", 0.0, mid, r * 0.88, r * 0.88,
              s0 + shade * 0.4, s0 + shade * 0.75)
        _oval(parts, "lens-top", "lens", 0.0, mid, r * 0.76, r * 0.76,
              s0 + shade * 0.75, z0 + tall)
        _oval(parts, "foot", "fixture", 0.0, mid, min(r * 0.55, 3.2),
              min(r * 0.55, 3.2), z0, z0 + 0.8, n=12)
        _oval(parts, "body", "fixture", 0.0, mid, min(r * 0.38, 2.2),
              min(r * 0.38, 2.2), z0 + 0.8, z0 + (tall - shade) * 0.7, n=12)
        _oval(parts, "stem", "fixture", 0.0, mid, 0.4, 0.4,
              z0 + (tall - shade) * 0.7, s0 + shade * 0.3, n=8)
    else:                                   # sconce
        z0 = st["floor_to_bottom_in"]
        _add(parts, "backplate", "fixture", -r, r, 0.0, 0.8, z0, z0 + size * 1.6)
        _add(parts, "arm", "fixture", -0.5, 0.5, 0.8, 2.5, z0 + size * 0.7,
             z0 + size * 0.9)
        _add(parts, "lens", "lens", -r + 0.5, r - 0.5, 1.2, d, z0 + size * 0.3,
             z0 + size * 1.3)


def light_source(st, ceiling_in=96.0):
    """Where a light's light comes from, and what it is: a dict with `pos`
    (x, f, z in the cabinet frame), `colour` (r, g, b in 0..1), `lumens`,
    `kind` ("point" or "spot", a spot aims straight down) and `cone_deg`.
    None for anything that is not a light, or is switched to zero output."""
    if st["lumens"] <= 0:
        return None
    if st["type"] == "light":
        parts = []
        _light(parts, st, ceiling_in)
        lens = next((p for p in parts if p.role == "lens"), None)
        if lens is None:
            return None
        x = sum(q[0] for q in lens.quad) / 4.0
        f = sum(q[1] for q in lens.quad) / 4.0
        z = lens.z0 - 0.5
    elif st["type"] == "mirror" and st["light_style"] != "none":
        parts = []
        _mirror(parts, st)
        lenses = [p for p in parts if p.role == "lens"]
        if not lenses:
            return None
        pts = [q for p in lenses for q in p.quad]
        x = sum(q[0] for q in pts) / len(pts)
        f = sum(q[1] for q in pts) / len(pts) + 2.0        # cast into the room
        z = sum((p.z0 + p.z1) / 2.0 for p in lenses) / len(lenses)
    elif st["type"] == "suspended" and st["under_light"]:
        # 0368: the strip under a ceiling cabinet, aimed at the counter below
        x, f = 0.0, st["depth_in"] / 2.0
        z = float(ceiling_in) - st["drop_in"] - st["height_in"] - 0.8
    else:
        return None
    hexa = {k: h for k, _l, h in LIGHT_COLOURS}.get(st["light_colour"], "#ffe4bf")
    rgb = tuple(int(hexa[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    spot = (st["type"] == "light" and st["beam"] == "spot"
            and st["fixture"] not in ("sconce", "table"))
    cone = 60.0 if spot else 180.0
    if st["type"] == "suspended":            # a downlight, wider than a can's
        spot, cone = True, 110.0
    return {"pos": (x, f, z), "colour": rgb,
            "lumens": float(st["lumens"]), "kind": "spot" if spot else "point",
            "cone_deg": cone}


def cabinet_parts(st, room_style=None, ceiling_in=96.0):
    """The parts of one cabinet, appliance, island or light, from a
    NORMALIZED state. `ceiling_in` is the room's ceiling, for a ceiling
    light or a cabinet hung from it; everything else ignores it."""
    parts = []
    style = door_style_of(st, room_style)
    kind = st["type"]
    if kind == "light":
        _light(parts, st, ceiling_in)
    elif kind == "fixture":
        _FIXTURE_BUILDERS[st["model"]](parts, st)
        if st.get("wall_mounted"):
            parts = _moved(parts, dz=max(st["floor_to_bottom_in"], 0.0))
    elif kind == "island":
        _island(parts, st, style)
    elif kind == "appliance":
        _appliance(parts, st)
        if st.get("wall_mounted"):
            parts = _moved(parts, dz=max(st["floor_to_bottom_in"], 0.0))
    elif kind == "wall":
        _wall(parts, st, style)
    elif kind == "tall":
        _tall(parts, st, style)
    elif kind == "corner_base":
        _corner(parts, st, style)
    elif kind == "mirror":
        _mirror(parts, st, style)
    elif kind == "kitchen_desk":
        _kitchen_desk(parts, st, style)
    elif kind == "corner_wall":
        _corner_wall(parts, st, style)
    elif kind == "suspended":
        _suspended(parts, st, style, ceiling_in)
    else:
        _base_like(parts, st, style)
    return parts


def trade_code(st):
    """The catalog code a supplier would use: B33, SB36, W3030, U2484."""
    w = st["width_in"]
    width = str(int(w)) if abs(w - round(w)) < 1e-6 else f"{w:g}"
    h = int(round(st["height_in"]))
    kind = st["type"]
    if kind == "wall":
        return f"W{width}{h}"
    if kind == "tall":
        return f"U{width}{h}"
    if kind == "sink_base":
        return f"SB{width}"
    if kind == "corner_base":
        return {"blind": "BBC", "l_shape": "LS", "diagonal": "DCB"}[
            st["corner_type"]] + width
    if kind == "base":
        return ("DB" if st["front"] == "drawers" else "B") + width
    if kind == "island":
        return "+".join(code for code, _w, _k, _o in island_slots(st))
    if kind == "corner_wall":
        return {"l_shape": "WLS", "diagonal": "DCW"}[st["corner_type"]] + f"{width}{h}"
    if kind == "kitchen_desk":
        return f"KD{width}"
    return ""
