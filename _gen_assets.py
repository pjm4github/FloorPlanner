# One-shot generator for assets/icons (toolbar) and assets/furnishings
# (top-view furniture symbol library, CC0).  Furnishing SVGs use a viewBox
# in INCHES so the app can render them at true scale (1 scene unit = 1").
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "assets"
ICONS = ROOT / "icons"
FURN = ROOT / "furnishings"
ICONS.mkdir(parents=True, exist_ok=True)
FURN.mkdir(parents=True, exist_ok=True)

INK = "#374151"
FILL = "#f8fafc"


def svg(w, d, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {d}" '
            f'width="{w}" height="{d}">\n' + "\n".join(body) + "\n</svg>\n")


def svg_error(text):
    """D70: is this SVG WELL-FORMED?  Returns a message, or None if it parses.

    THE FAILURE THIS CATCHES, and it is the one that produced the record.
    `svg()` does a join over `body`, so `body` must be a SEQUENCE OF ELEMENT
    STRINGS.  Pass a single string and it is joined CHARACTER BY CHARACTER --
    the generator reports success and writes a file with one character per
    line.  The item still reaches the catalog, still draws a correct footprint
    and still builds a 3D mesh, because all three read the MANIFEST; only the
    plan SYMBOL is silently blank, because only it reads the SVG.

    WHY AN XML PARSE AND NOT A RENDERER.  `QSvgRenderer` would be stronger --
    it would also reject an SVG that parses but draws nothing -- and it would
    drag Qt into an asset build that is deliberately Qt-free.  Ruled: parse,
    and refuse.  **The limit is stated rather than hidden: this proves the file
    is well-formed XML, not that it renders.**

    The string case is named in the caller's message because it is the known
    cause and the fix is one character -- brackets round the body.
    """
    try:
        ET.fromstring(text)
    except ET.ParseError as exc:
        return str(exc)
    return None


def R(x, y, w, h, rx=0.0, fill=FILL, sw=1.0, dash=None):
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{INK}" stroke-width="{sw}"{extra}/>')


def L(x1, y1, x2, y2, sw=0.7, dash=None):
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{INK}" stroke-width="{sw}"{extra}/>')


def Ci(cx, cy, r, fill="none", sw=0.7):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
            f'stroke="{INK}" stroke-width="{sw}"/>')


def El(cx, cy, rx, ry, fill="#ffffff", sw=0.8):
    return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
            f'fill="{fill}" stroke="{INK}" stroke-width="{sw}"/>')


def Pth(d, fill="none", sw=0.8):
    return (f'<path d="{d}" fill="{fill}" stroke="{INK}" '
            f'stroke-width="{sw}"/>')


# ---------------------------------------------------------------- furniture
def bed(w, d, pillows):
    parts = [R(0.75, 0.75, w - 1.5, d - 1.5, 2, sw=1.2)]
    if pillows == 1:
        parts.append(R(w * 0.18, 3, w * 0.64, 10, 2.5, "#ffffff", 0.8))
    else:
        pw = (w - 13) / 2
        parts.append(R(4.5, 3, pw, 10, 2.5, "#ffffff", 0.8))
        parts.append(R(w - 4.5 - pw, 3, pw, 10, 2.5, "#ffffff", 0.8))
    parts.append(L(0.75, 19, w - 0.75, 19, 0.8))      # blanket fold line
    return parts


def seat(w, d, cushions, arm=7.0):
    parts = [R(0.75, 0.75, w - 1.5, d - 1.5, 3, sw=1.2),
             L(0.75, 7, w - 0.75, 7, 0.7),            # back band
             L(arm, 7, arm, d - 0.75, 0.7),           # arms
             L(w - arm, 7, w - arm, d - 0.75, 0.7)]
    for i in range(1, cushions):
        x = arm + (w - 2 * arm) * i / cushions
        parts.append(L(x, 7, x, d - 0.75, 0.55))
    return parts


def base_unit(w, d, doors=2):
    """Top view of a base cabinet: box, a counter-nosing line near the front
    (bottom), vertical door dividers and a knob on each door."""
    parts = [R(0.75, 0.75, w - 1.5, d - 1.5, 0.8, sw=1.1),
             L(1.5, d - 3, w - 1.5, d - 3, 0.4)]            # counter nosing
    fw = (w - 1.5) / doors
    for i in range(1, doors):
        parts.append(L(0.75 + fw * i, 0.75, 0.75 + fw * i, d - 0.75, 0.45))
    for i in range(doors):
        parts.append(Ci(0.75 + fw * (i + 0.5), d - 4.5, 0.8, "none", 0.55))
    return parts


def drawer_unit(w, d, n):
    """Top view of a drawer base: box with n stacked drawer fronts + pulls."""
    parts = [R(0.75, 0.75, w - 1.5, d - 1.5, 0.8, sw=1.1)]
    for j in range(1, n):
        y = 0.75 + (d - 1.5) * j / n
        parts.append(L(0.75, y, w - 0.75, y, 0.45))
    for j in range(n):
        cy = 0.75 + (d - 1.5) * (j + 0.5) / n
        parts.append(L(w / 2 - 4, cy, w / 2 + 4, cy, 0.8))    # drawer pull
    return parts


def sink_base(w, d):
    """Kitchen sink base: box, a double-bowl basin near the back, faucet, and
    two doors with knobs along the front."""
    bw, bh = w - 11, d - 9
    parts = [R(0.75, 0.75, w - 1.5, d - 1.5, 0.8, sw=1.1),
             R(5.5, 2.5, bw, bh, 1.5, "#ffffff", 0.7),
             L(w / 2, 2.5, w / 2, 2.5 + bh, 0.4),             # bowl divider
             Ci(w / 2, 2.0, 1.1, "none", 0.6),                # faucet
             L(w / 2, 2.5 + bh, w / 2, d - 0.75, 0.45),       # door divider
             Ci(w / 4 + 1, d - 4, 0.8, "none", 0.55),
             Ci(3 * w / 4 - 1, d - 4, 0.8, "none", 0.55)]
    return parts


def vanity_unit(w, d, sinks):
    """Top view of a bathroom vanity base: box, oval basin(s) + faucet(s)
    toward the back, and door dividers / knobs along the front."""
    parts = [R(0.75, 0.75, w - 1.5, d - 1.5, 0.8, sw=1.1)]
    for k in range(sinks):
        cx = w * (k + 0.5) / sinks
        parts.append(El(cx, d * 0.46, min(8.5, w / sinks * 0.34), 5.5,
                        "#ffffff", 0.7))
        parts.append(Ci(cx, 3.2, 1.1, "none", 0.6))           # faucet
    doors = max(2, sinks * 2)
    fw = (w - 1.5) / doors
    for i in range(1, doors):
        parts.append(L(0.75 + fw * i, d - 8, 0.75 + fw * i, d - 0.75, 0.4))
    for i in range(doors):
        parts.append(Ci(0.75 + fw * (i + 0.5), d - 3, 0.7, "none", 0.5))
    return parts


def island(w, d, doors, cab=24, sink=False):
    """Top view of a kitchen island: a countertop, a base-cabinet block along
    the back (door fronts + knobs, optional sink) and a seating overhang at
    the front with bar stools."""
    parts = [R(0.75, 0.75, w - 1.5, d - 1.5, 1.5, sw=1.2),     # countertop
             L(1.5, cab, w - 1.5, cab, 0.5)]                   # cabinet face
    fw = (w - 1.5) / doors
    for i in range(1, doors):
        parts.append(L(0.75 + fw * i, 0.75, 0.75 + fw * i, cab, 0.45))
    for i in range(doors):
        parts.append(Ci(0.75 + fw * (i + 0.5), cab - 2.5, 0.7, "none", 0.5))
    if sink:
        bw, bh = w * 0.34, cab - 9
        parts.append(R(w / 2 - bw / 2, 3, bw, bh, 1.5, "#ffffff", 0.7))
        parts.append(Ci(w / 2, 2.2, 1.1, "none", 0.6))
    for k in range(max(2, round(w / 28))):                     # bar stools
        sx = w * (k + 0.5) / max(2, round(w / 28))
        parts.append(Ci(sx, d - 6.5, 6, "none", 0.6))
    return parts


def wall_unit(w, d, doors=2):
    """Top view of a wall (upper) cabinet: a DASHED box -- it sits overhead,
    above the plan cut -- with door dividers and knobs."""
    parts = [R(0.75, 0.75, w - 1.5, d - 1.5, 0.6, sw=1.0, dash="3,2")]
    fw = (w - 1.5) / doors
    for i in range(1, doors):
        parts.append(L(0.75 + fw * i, 0.75, 0.75 + fw * i, d - 0.75, 0.4,
                       "3,2"))
    for i in range(doors):
        parts.append(Ci(0.75 + fw * (i + 0.5), d - 3, 0.7, "none", 0.5))
    return parts


def pantry_unit(w, d, doors=2):
    """Top view of a tall pantry / utility cabinet: box, dashed interior
    shelves, full-height door dividers and a knob on each door."""
    parts = [R(0.75, 0.75, w - 1.5, d - 1.5, 0.8, sw=1.1)]
    for j in range(1, 4):                                 # dashed shelves
        y = 0.75 + (d - 1.5) * j / 4
        parts.append(L(2.5, y, w - 2.5, y, 0.4, "2,2"))
    fw = (w - 1.5) / doors
    for i in range(1, doors):
        parts.append(L(0.75 + fw * i, 0.75, 0.75 + fw * i, d - 0.75, 0.5))
    for i in range(doors):
        parts.append(Ci(0.75 + fw * (i + 0.5), d - 3.5, 0.8, "none", 0.55))
    return parts


FURNISHINGS = [
    # (id, name, category, width", depth", body parts)
    ("sofa", "Sofa", "Living", 84, 36, seat(84, 36, 3)),
    ("loveseat", "Loveseat", "Living", 58, 36, seat(58, 36, 2)),
    ("armchair", "Armchair", "Living", 33, 33, seat(33, 33, 1, arm=6)),
    ("coffee_table", "Coffee Table", "Living", 48, 24,
     [R(0.6, 0.6, 46.8, 22.8, 3)]),
    ("side_table", "Side Table", "Living", 20, 20,
     [R(0.6, 0.6, 18.8, 18.8, 1.5)]),
    ("tv_stand", "TV Stand", "Living", 60, 16,
     [R(0.6, 0.6, 58.8, 14.8, 1), L(20, 0.6, 20, 15.4, 0.5),
      L(40, 0.6, 40, 15.4, 0.5)]),
    ("large_tv", "Large Screen TV 75\"", "Living", 66, 4,
     [R(0.5, 0.5, 65, 3, 0.4, sw=1.3),                          # flat panel
      L(2, 3, 64, 3, 0.3),                                      # screen face
      R(29, 0.5, 8, 1.2, 0.3, FILL, 0.7)]),                     # wall bracket
    ("gas_fireplace", "Gas Fireplace 4'", "Living", 48, 20,
     [R(0.75, 0.75, 46.5, 18.5, 1, sw=1.2),                     # surround
      R(8, 3.5, 32, 13.5, 0.8, "none", 0.7),                    # glass firebox
      R(13, 12.5, 22, 3, 1.5, FILL, 0.6),                       # gas logs
      Pth("M19 7.5 c-2 2 -2 4 0 4.8 c2 -0.6 2 -2.8 0 -4.8 z",
          "#ffffff", 0.6),
      Pth("M24 6.3 c-2.2 2.2 -2.2 4.5 0 5.4 c2.2 -0.7 2.2 -3.2 0 -5.4 z",
          "#ffffff", 0.7),
      Pth("M29 7.5 c-2 2 -2 4 0 4.8 c2 -0.6 2 -2.8 0 -4.8 z",
          "#ffffff", 0.6)]),

    ("dining_table", "Dining Table 6'", "Dining", 72, 36,
     [R(0.75, 0.75, 70.5, 34.5, 1.5, sw=1.2),
      R(3, 3, 66, 30, 1, "none", 0.5)]),
    ("dining_table_round", "Round Table 4'", "Dining", 48, 48,
     [Ci(24, 24, 23.25, FILL, 1.2), Ci(24, 24, 20.5, "none", 0.5)]),
    ("dining_chair", "Dining Chair", "Dining", 18, 18,
     [R(1, 0.75, 16, 2.8, 1.4, "#ffffff", 0.8),
      R(1.4, 3.8, 15.2, 13.4, 2.5)]),
    ("buffet", "Buffet 5'", "Dining", 60, 18,
     [R(0.75, 0.75, 58.5, 16.5, 1, sw=1.2),
      L(2, 5, 58, 5, 0.45),                                 # top drawer band
      L(13.5, 2.7, 16.5, 2.7, 0.6), L(28.5, 2.7, 31.5, 2.7, 0.6),
      L(43.5, 2.7, 46.5, 2.7, 0.6),                         # drawer pulls
      L(20, 5, 20, 17.25, 0.5), L(40, 5, 40, 17.25, 0.5),   # door dividers
      Ci(10, 12, 0.8, "none", 0.5), Ci(30, 12, 0.8, "none", 0.5),
      Ci(50, 12, 0.8, "none", 0.5)]),                       # door knobs
    ("hutch", "China Hutch 5'", "Dining", 60, 20,
     [R(0.75, 0.75, 58.5, 18.5, 1, sw=1.2),                 # buffet base
      L(20, 0.75, 20, 19.25, 0.5), L(40, 0.75, 40, 19.25, 0.5),
      Ci(10, 16, 0.8, "none", 0.5), Ci(30, 16, 0.8, "none", 0.5),
      Ci(50, 16, 0.8, "none", 0.5),                         # base door knobs
      R(2.5, 1.5, 55, 11, 0.5, "none", 0.7, dash="3,2"),    # upper display cabinet
      L(2.5, 5, 57.5, 5, 0.4, "3,2"),
      L(2.5, 9, 57.5, 9, 0.4, "3,2")]),                     # glass shelves

    ("refrigerator", "Refrigerator", "Kitchen", 36, 30,
     [R(0.75, 0.75, 34.5, 28.5, 1, sw=1.2), L(18, 1.5, 18, 28.5, 0.7)]),
    ("range", "Range / Stove", "Kitchen", 30, 26,
     [R(0.75, 0.75, 28.5, 24.5, 1, sw=1.2),
      Ci(8, 8, 4), Ci(22, 8, 4), Ci(8, 18, 4), Ci(22, 18, 4),
      L(1, 22.5, 29, 22.5, 0.5)]),
    ("dishwasher", "Dishwasher", "Kitchen", 24, 24,
     [R(0.75, 0.75, 22.5, 22.5, 1, sw=1.2),
      R(2.5, 2.5, 19, 19, 1, "none", 0.5), L(2.5, 2.5, 21.5, 21.5, 0.5)]),
    ("kitchen_sink", "Kitchen Sink", "Kitchen", 33, 22,
     [R(0.75, 0.75, 31.5, 20.5, 1, sw=1.2),
      R(3, 4, 12, 14, 2.5, "#ffffff", 0.8),
      R(18, 4, 12, 14, 2.5, "#ffffff", 0.8), Ci(16.5, 2.2, 1, "none", 0.6)]),
    # kitchen base cabinets (standard 24" deep)
    ("base_cab_24", "Base Cabinet 24\"", "Kitchen", 24, 24,
     base_unit(24, 24, 2)),
    ("base_cab_36", "Base Cabinet 36\"", "Kitchen", 36, 24,
     base_unit(36, 24, 2)),
    ("drawer_base_18", "Drawer Base 18\"", "Kitchen", 18, 24,
     drawer_unit(18, 24, 3)),
    ("sink_base_36", "Sink Base 36\"", "Kitchen", 36, 24, sink_base(36, 24)),
    ("corner_base_36", "Corner Base 36\"", "Kitchen", 36, 36,
     [R(0.75, 0.75, 34.5, 34.5, 1, sw=1.1),
      Ci(18, 18, 15, "none", 0.4), Ci(18, 18, 1.4, "none", 0.5),  # lazy susan
      L(7.5, 28.5, 28.5, 7.5, 0.7)]),                             # diagonal door
    # tall pantry / utility cabinets (24" deep)
    ("pantry_18", "Pantry 18\"", "Kitchen", 18, 24, pantry_unit(18, 24, 1)),
    ("pantry_24", "Pantry 24\"", "Kitchen", 24, 24, pantry_unit(24, 24, 2)),
    ("pantry_36", "Pantry 36\"", "Kitchen", 36, 24, pantry_unit(36, 24, 2)),
    # wall (upper) cabinets, drawn dashed; standard 12" deep
    ("wall_cab_24", "Wall Cabinet 24\"", "Kitchen", 24, 12, wall_unit(24, 12)),
    ("wall_cab_30", "Wall Cabinet 30\"", "Kitchen", 30, 12, wall_unit(30, 12)),
    ("wall_cab_36", "Wall Cabinet 36\"", "Kitchen", 36, 12, wall_unit(36, 12)),
    # kitchen islands: base cabinets + a seating overhang with stools
    ("kitchen_island", "Kitchen Island 6'", "Kitchen", 72, 39,
     island(72, 39, doors=3)),
    ("island_sink", "Island w/ Sink 7'", "Kitchen", 84, 42,
     island(84, 42, doors=4, sink=True)),

    ("bed_king", "King Bed", "Bedroom", 76, 80, bed(76, 80, 2)),
    ("bed_queen", "Queen Bed", "Bedroom", 60, 80, bed(60, 80, 2)),
    ("bed_full", "Full Bed", "Bedroom", 54, 75, bed(54, 75, 2)),
    ("bed_twin", "Twin Bed", "Bedroom", 39, 75, bed(39, 75, 1)),
    ("nightstand", "Nightstand", "Bedroom", 20, 16,
     [R(0.6, 0.6, 18.8, 14.8, 1)]),
    ("dresser", "Dresser", "Bedroom", 60, 18,
     [R(0.75, 0.75, 58.5, 16.5, 1, sw=1.2),
      L(20, 0.75, 20, 17.25, 0.6), L(40, 0.75, 40, 17.25, 0.6),
      Ci(10, 9, 0.9), Ci(30, 9, 0.9), Ci(50, 9, 0.9)]),

    ("bathtub", "Bathtub 5'", "Bathroom", 30, 60,
     [R(0.75, 0.75, 28.5, 58.5, 2.5, sw=1.2),
      R(3.5, 3.5, 23, 53, 8, "#ffffff", 0.8), Ci(15, 10, 1.5, "none", 0.6)]),
    ("shower", "Shower 36\"", "Bathroom", 36, 36,
     [R(0.75, 0.75, 34.5, 34.5, 1, sw=1.2), R(3, 3, 30, 30, 1, "none", 0.6),
      L(3, 3, 33, 33, 0.4), L(33, 3, 3, 33, 0.4),
      Ci(18, 18, 1.8, "none", 0.7)]),
    ("walk_in_shower", "Luxury Walk-in Shower", "Bathroom", 60, 42,
     [R(0.75, 0.75, 58.5, 40.5, 1.5, sw=1.2),               # tiled enclosure
      # faint tile grout grid
      L(15, 0.75, 15, 41.25, 0.3), L(30, 0.75, 30, 41.25, 0.3),
      L(45, 0.75, 45, 41.25, 0.3),
      L(0.75, 14, 59.25, 14, 0.3), L(0.75, 28, 59.25, 28, 0.3),
      # built-in bench seat at the left end
      R(2.5, 2.5, 11, 37, 1.2, "#ffffff", 0.8), L(13.5, 2.5, 13.5, 39.5, 0.5),
      # ceiling rainfall head (centre) plus a hand shower and valve trim
      Ci(37, 21, 7.5, "none", 0.7), Ci(37, 21, 2.2, "none", 0.5),
      Ci(24, 6.5, 1.6, "none", 0.6), Ci(30, 6.5, 1.1, "none", 0.6),
      # linear drain along the right end
      R(53, 4, 3.5, 34, 0.4, "none", 0.6), L(54.75, 4, 54.75, 38, 0.4),
      # frameless glass screen on the front with a walk-in opening
      L(31, 39.8, 58.5, 39.8, 1.6), L(31, 39.8, 31, 33, 1.2)]),
    ("glass_shower", "Luxury Glass Shower 5' x 4'", "Bathroom", 60, 48,
     [# floor-to-ceiling glass enclosure: outer panels with a door gap, plus
      # a faint inner line for the glass thickness
      L(1, 1, 59, 1, 1.1), L(1, 1, 1, 47, 1.1), L(59, 1, 59, 47, 1.1),
      L(1, 47, 11, 47, 1.1), L(34, 47, 59, 47, 1.1),
      R(2.6, 2.6, 54.8, 43.0, 0, "none", 0.35),
      # frameless glass door swinging in from the front opening
      L(34, 47, 34, 24, 1.3),
      Pth("M 11 47 A 23 23 0 0 1 34 24", "none", 0.6),
      # ceiling rainfall head over the centre, with a tile grid in the head
      R(28, 13, 18, 18, 1, "none", 0.7),
      L(33, 13, 33, 31, 0.3), L(37, 13, 37, 31, 0.3), L(41, 13, 41, 31, 0.3),
      L(28, 17.5, 46, 17.5, 0.3), L(28, 22, 46, 22, 0.3),
      L(28, 26.5, 46, 26.5, 0.3),
      # hand shower + valve trim on the back wall
      Ci(12, 7, 1.7, "none", 0.6), Ci(17, 7, 1.1, "none", 0.6),
      # linear drain along the back wall
      R(28, 4, 24, 2.4, 0.3, "none", 0.5), L(40, 4, 40, 6.4, 0.3)]),
    ("toilet", "Toilet", "Bathroom", 20, 28,
     [R(2, 0.75, 16, 7, 1.5, FILL, 1),
      El(10, 17.5, 7.5, 9.5, "#ffffff", 1), El(10, 18, 5.5, 7, "none", 0.5)]),
    ("vanity", "Bath Vanity 30\"", "Bathroom", 30, 21,
     [R(0.75, 0.75, 28.5, 19.5, 1, sw=1.2), El(15, 11, 9, 6.5),
      Ci(15, 3.5, 1.2, "none", 0.6)]),
    # bathroom vanity base cabinets (standard 21" deep)
    ("vanity_24", "Vanity Base 24\"", "Bathroom", 24, 21, vanity_unit(24, 21, 1)),
    ("vanity_36", "Vanity Base 36\"", "Bathroom", 36, 21, vanity_unit(36, 21, 1)),
    ("vanity_48", "Double Vanity 48\"", "Bathroom", 48, 21,
     vanity_unit(48, 21, 2)),

    ("washer", "Washer", "Laundry", 27, 30,
     [R(0.75, 0.75, 25.5, 28.5, 1, sw=1.2),
      Ci(13.5, 16, 9, "#ffffff", 0.9), Ci(13.5, 16, 5.5, "none", 0.6)]),
    ("dryer", "Dryer", "Laundry", 27, 30,
     [R(0.75, 0.75, 25.5, 28.5, 1, sw=1.2),
      Ci(13.5, 16, 9, "#ffffff", 0.9), L(5, 4, 22, 4, 0.7)]),

    ("suv", "SUV", "Garage", 78, 192,
     [R(1, 1, 76, 190, 14, FILL, 1.5),
      R(9, 52, 60, 104, 9, "#ffffff", 0.9),       # cabin glasshouse
      L(9, 74, 69, 74, 0.7), L(9, 134, 69, 134, 0.7),
      R(0.5, 58, 7, 4, 1.5, FILL, 0.8), R(70.5, 58, 7, 4, 1.5, FILL, 0.8),
      L(14, 14, 64, 14, 0.6), L(14, 180, 64, 180, 0.6)]),
    ("car", "Car", "Garage", 72, 180,
     [R(1, 1, 70, 178, 16, FILL, 1.5),
      R(8, 50, 56, 92, 9, "#ffffff", 0.9),
      L(8, 70, 64, 70, 0.7), L(8, 122, 64, 122, 0.7),
      R(0.5, 55, 7, 4, 1.5, FILL, 0.8), R(64.5, 55, 7, 4, 1.5, FILL, 0.8),
      L(14, 12, 58, 12, 0.6), L(14, 170, 58, 170, 0.6)]),
    ("motorcycle", "Motorcycle", "Garage", 32, 84,
     [El(16, 12, 3, 10, FILL, 1.1), El(16, 71, 3.5, 10, FILL, 1.1),
      L(16, 22, 16, 61, 1.4),
      R(10.5, 32, 11, 30, 5.5, FILL, 1),           # tank + seat
      L(4, 22, 28, 22, 1.4),                       # handlebars
      Ci(4, 22, 1.2), Ci(28, 22, 1.2)]),
    ("bicycle", "Bicycle", "Garage", 24, 68,
     [El(12, 13, 2.2, 11, FILL, 1), El(12, 55, 2.2, 11, FILL, 1),
      L(12, 13, 12, 55, 1.2),
      L(2, 23, 22, 23, 1.2),                       # handlebars
      El(12, 42, 3.2, 5, FILL, 0.9),               # saddle
      L(5, 33, 19, 33, 0.9)]),                     # pedals
    ("boat", "Boat 14'", "Garage", 68, 168,
     ['<path d="M34 2 C 12 28 4 72 4 122 L4 148 Q4 166 22 166 L46 166 '
      'Q64 166 64 148 L64 122 C64 72 56 28 34 2 Z" '
      f'fill="{FILL}" stroke="{INK}" stroke-width="1.5"/>',
      '<path d="M34 12 C 17 34 10 74 10 120 L10 146 Q10 160 24 160 L44 160 '
      'Q58 160 58 146 L58 120 C58 74 51 34 34 12 Z" '
      f'fill="none" stroke="{INK}" stroke-width="0.6"/>',
      L(10, 96, 58, 96, 0.8), L(10, 128, 58, 128, 0.8)]),   # thwart seats
    ("workbench", "Workbench 6'", "Garage", 72, 24,
     [R(0.75, 0.75, 70.5, 22.5, 1, sw=1.2),
      R(3, 3, 66, 18, 0.5, "none", 0.5), Ci(64, 7, 3, "none", 0.8)]),
    ("storage_shelves", "Storage Shelves", "Garage", 48, 18,
     [R(0.6, 0.6, 46.8, 16.8, 0.5, sw=1),
      L(12, 0.6, 12, 17.4, 0.5), L(24, 0.6, 24, 17.4, 0.5),
      L(36, 0.6, 36, 17.4, 0.5), L(0.6, 9, 47.4, 9, 0.4, "2,2")]),
    ("lawnmower", "Lawn Mower", "Garage", 22, 62,
     [R(1, 2, 20, 25, 8, FILL, 1.1),               # deck
      Ci(11, 14.5, 6, "none", 0.6),
      R(0.4, 4.5, 3, 6.5, 1.2, FILL, 0.8),         # four wheels
      R(18.6, 4.5, 3, 6.5, 1.2, FILL, 0.8),
      R(0.4, 18.5, 3, 6.5, 1.2, FILL, 0.8),
      R(18.6, 18.5, 3, 6.5, 1.2, FILL, 0.8),
      L(6, 27, 8.5, 59, 1.1), L(16, 27, 13.5, 59, 1.1),
      L(8.5, 59, 13.5, 59, 1.4)]),                 # handle
    ("garden_tractor", "Garden Tractor + Loader", "Garage", 54, 120,
     [R(2.5, 1, 49, 8.5, 1.5, FILL, 1.3),                  # front loader bucket
      L(2.5, 5.5, 51.5, 5.5, 0.5),                         # bucket lip
      R(9, 9, 4.5, 32, 1, FILL, 1), R(40.5, 9, 4.5, 32, 1, FILL, 1),  # arms
      R(13, 38, 28, 30, 3, FILL, 1.3),                     # hood / engine
      L(13, 48, 41, 48, 0.5), L(13, 56, 41, 56, 0.5),      # hood louvers
      R(11, 70, 32, 32, 2.5, FILL, 1.2),                   # operator platform
      R(19, 76, 16, 15, 3, "#ffffff", 0.9),                # seat
      L(13, 84, 41, 84, 1.4),                              # ROPS roll bar
      R(21, 114, 12, 5, 1, FILL, 1),                       # rear 3-point hitch
      R(1, 42, 7, 17, 2, FILL, 1), R(46, 42, 7, 17, 2, FILL, 1),  # front wheels
      R(0.5, 90, 9, 25, 2.5, FILL, 1.1),                   # rear wheels (large)
      R(44.5, 90, 9, 25, 2.5, FILL, 1.1)]),
    ("riding_mower_snow", "Riding Mower + Snowblower", "Garage", 46, 96,
     [R(2, 1, 42, 12, 1.5, FILL, 1.3),                     # front snowblower
      L(12, 2, 12, 12, 0.5), L(23, 2, 23, 12, 0.5),
      L(34, 2, 34, 12, 0.5),                               # auger flights
      Ci(23, 7, 3.2, "#ffffff", 0.8),                      # discharge chute
      R(18, 13, 10, 5, 1, FILL, 1),                        # mount linkage
      R(9, 18, 28, 26, 3, FILL, 1.3),                      # hood / engine
      L(9, 28, 37, 28, 0.5),                               # hood line
      Ci(23, 50, 4.5, "none", 1),                          # steering wheel
      R(14, 56, 18, 18, 3, "#ffffff", 0.9),                # operator seat
      R(11, 74, 24, 12, 2, FILL, 1.1),                     # rear fender / body
      R(0.5, 24, 6, 14, 2, FILL, 1), R(39.5, 24, 6, 14, 2, FILL, 1),  # front
      R(0, 64, 8, 22, 2.5, FILL, 1.1),                     # rear wheels (large)
      R(38, 64, 8, 22, 2.5, FILL, 1.1)]),
    ("boat_trailer", "Boat Trailer", "Garage", 78, 216,
     [L(39, 6, 39, 62, 1.4),                       # tongue
      R(35.5, 1, 7, 7, 1.5, FILL, 1),              # coupler
      L(12, 62, 39, 8, 1.2), L(66, 62, 39, 8, 1.2),  # A-frame
      L(12, 62, 12, 205, 1.4), L(66, 62, 66, 205, 1.4),  # side rails
      L(12, 75, 66, 75, 0.8), L(12, 125, 66, 125, 0.8),  # cross members
      L(12, 175, 66, 175, 0.8), L(12, 205, 66, 205, 1.2),
      L(24, 70, 24, 200, 0.8, "4,3"),              # hull bunks
      L(54, 70, 54, 200, 0.8, "4,3"),
      Ci(39, 30, 3.2, "#ffffff", 0.9),             # winch post
      R(2, 130, 8, 32, 3, FILL, 1),                # fenders / wheels
      R(68, 130, 8, 32, 3, FILL, 1),
      R(7.5, 206.5, 6.5, 5, 1, "#ffffff", 0.8),    # tail lights
      R(64, 206.5, 6.5, 5, 1, "#ffffff", 0.8)]),
    ("snowblower", "Snow Blower", "Garage", 28, 58,
     [R(1, 1, 26, 13, 2, FILL, 1.2),              # auger housing
      L(8, 2, 8, 13.5, 0.5), L(14, 2, 14, 13.5, 0.5),
      L(20, 2, 20, 13.5, 0.5),
      Ci(9, 7.5, 2.8, "#ffffff", 0.8),            # discharge chute
      R(7.5, 14, 13, 17, 3, FILL, 1),             # engine body
      R(4, 18, 3.5, 9, 1.5, FILL, 0.8), R(20.5, 18, 3.5, 9, 1.5, FILL, 0.8),
      L(9, 31, 6.5, 55, 1.1), L(19, 31, 21.5, 55, 1.1),
      L(6.5, 55, 21.5, 55, 1.4)]),                # handlebar
    ("wheelbarrow", "Wheelbarrow", "Garage", 27, 58,
     [El(13.5, 5.5, 2.5, 4.5, FILL, 1),           # front wheel
      '<path d="M9.5 10 L17.5 10 L23 36 L4 36 Z" '
      f'fill="{FILL}" stroke="{INK}" stroke-width="1.2" '
      'stroke-linejoin="round"/>',                # tub (narrow at wheel)
      '<path d="M11 14 L16 14 L19.5 32.5 L7.5 32.5 Z" '
      f'fill="none" stroke="{INK}" stroke-width="0.5" '
      'stroke-linejoin="round"/>',
      L(6, 36, 8.5, 57, 1.1), L(21, 36, 18.5, 57, 1.1)]),
    ("trashcan", "Trash Can", "Garage", 24, 24,
     [Ci(12, 12, 11, FILL, 1.2), Ci(12, 12, 8.5, "none", 0.6),
      L(1.5, 12, 4.5, 12, 1.2), L(19.5, 12, 22.5, 12, 1.2)]),

    ("toolchest", "Tool Chest", "Shop", 41, 18,
     [R(0.75, 0.75, 39.5, 16.5, 1, sw=1.2),
      L(14, 0.75, 14, 17.25, 0.6), L(27, 0.75, 27, 17.25, 0.6),
      L(3, 3, 11, 3, 0.8), L(30, 3, 38, 3, 0.8)]),     # side handles
    ("table_saw", "Table Saw", "Shop", 40, 27,
     [R(0.75, 0.75, 38.5, 25.5, 1, sw=1.2),
      R(19, 7, 2, 13, 0.5, "#ffffff", 0.8),            # blade slot
      L(20, 9, 20, 18, 1.2),                           # blade
      L(13, 2, 13, 25, 0.5, "2,2"), L(27, 2, 27, 25, 0.5, "2,2"),
      L(2, 5, 38, 5, 0.8)]),                           # rip fence
    ("lathe", "Lathe 5'", "Shop", 60, 18,
     [R(0.75, 5, 58.5, 8, 1, sw=1.2),                  # bed
      R(2, 2, 11, 14, 1, FILL, 1),                     # headstock
      R(46, 4, 8, 10, 1, FILL, 1),                     # tailstock
      L(13, 9, 46, 9, 0.6, "3,2")]),                   # spindle axis
    ("jointer", "Jointer 5'", "Shop", 60, 20,
     [R(0.75, 5, 26.5, 11, 0.5, sw=1.2),               # infeed table
      R(32.75, 5, 26.5, 11, 0.5, sw=1.2),              # outfeed table
      R(27.8, 3.5, 4.4, 14, 0.5, "#d8dde3", 0.9),      # cutterhead
      L(2, 6.5, 58, 6.5, 0.8)]),                       # fence
    ("drill_press", "Drill Press", "Shop", 20, 28,
     [R(2.5, 20.5, 15, 6.75, 1, sw=1),                 # base
      R(4, 0.75, 12, 17, 3, FILL, 1.2),                # head
      Ci(10, 6, 2.6, "#ffffff", 0.8),                  # chuck
      Ci(10, 18.5, 7, "none", 0.8)]),                  # table below
    ("cutoff_saw", "Cutoff Saw", "Shop", 40, 24,
     [R(0.6, 9, 38.8, 6.5, 1, sw=1),                   # stand rails
      Ci(20, 15, 7.5, FILL, 0.9),                      # turntable
      R(13.5, 2, 13, 14, 2, FILL, 1.1),                # saw body
      L(20, 3.5, 20, 14.5, 1.2)]),                     # blade
    ("bandsaw", "Bandsaw", "Shop", 24, 30,
     [Ci(12, 8, 8.5, FILL, 1.1),                       # wheel housing
      R(2, 13, 20, 14.5, 1, FILL, 1.2),                # table
      L(12, 13, 12, 20.5, 0.8, "2,1.5"),               # blade slot
      Ci(12, 20.5, 1, "#1f2937", 0.5)]),               # blade
    ("planer", "Planer", "Shop", 24, 24,
     [R(0.6, 8, 22.8, 8, 0.5, sw=0.9),                 # in/outfeed tables
      R(3, 3.5, 18, 17, 2, FILL, 1.2),                 # body
      L(3, 9, 21, 9, 0.7), L(3, 15, 21, 15, 0.7),      # rollers
      Ci(12, 2, 1.4, "none", 0.7)]),                   # height crank

    ("lounge_chair", "Lounge Chair", "Sunroom", 27, 78,
     [R(0.75, 0.75, 25.5, 76.5, 4, sw=1.2),
      R(4, 3.5, 19, 9, 2.5, "#ffffff", 0.8),           # headrest
      L(2, 28, 25, 28, 0.8),                           # backrest hinge
      L(2, 56, 25, 56, 0.6)]),                         # leg hinge
    ("sauna", "Sauna 6'", "Sunroom", 72, 72,
     [R(0.75, 0.75, 70.5, 70.5, 1.5, sw=1.5),
      R(4, 4, 64, 14, 1, "none", 0.7),                 # bench (back)
      R(4, 18, 14, 50, 1, "none", 0.7),                # bench (side)
      R(52, 52, 14, 14, 1, FILL, 1),                   # heater
      Ci(59, 59, 3.5, "none", 0.6),                    # rocks
      L(30, 71.25, 46, 71.25, 1.8)]),                  # door
    ("umbrella_table", "Umbrella Table", "Sunroom", 96, 96,
     ['<circle cx="48" cy="48" r="46.5" fill="none" stroke="#374151" '
      'stroke-width="0.9" stroke-dasharray="5,4"/>',   # canopy overhead
      L(48, 1.5, 48, 17, 0.5, "5,4"), L(48, 79, 48, 94.5, 0.5, "5,4"),
      L(1.5, 48, 17, 48, 0.5, "5,4"), L(79, 48, 94.5, 48, 0.5, "5,4"),
      Ci(48, 48, 21, FILL, 1.2),                       # table
      Ci(48, 48, 1.8, "#374151", 0.5),                 # pole
      R(39, 17, 18, 14, 3, FILL, 0.9), R(39, 65, 18, 14, 3, FILL, 0.9),
      R(17, 41, 14, 18, 3, FILL, 0.9), R(65, 41, 14, 18, 3, FILL, 0.9)]),
    ("swim_spa", "Swim Spa", "Sunroom", 90, 180,
     [R(0.75, 0.75, 88.5, 178.5, 6, sw=1.5),
      R(7, 7, 76, 166, 5, "#ffffff", 0.9),             # water line
      Ci(25, 16, 2.2, "none", 0.8), Ci(45, 16, 2.2, "none", 0.8),
      Ci(65, 16, 2.2, "none", 0.8),                    # swim jets
      L(45, 30, 45, 140, 0.6, "5,4"),                  # swim lane
      R(13, 148, 64, 20, 4, "none", 0.7)]),            # bench seat
    ("whirlpool", "Whirlpool", "Sunroom", 84, 84,
     [R(0.75, 0.75, 82.5, 82.5, 9, sw=1.5),
      Ci(42, 42, 32, "#ffffff", 1),                    # water
      Ci(42, 14.5, 2, "none", 0.7), Ci(42, 69.5, 2, "none", 0.7),
      Ci(14.5, 42, 2, "none", 0.7), Ci(69.5, 42, 2, "none", 0.7),
      Ci(22.5, 22.5, 2, "none", 0.7), Ci(61.5, 61.5, 2, "none", 0.7),
      Ci(42, 42, 2.2, "none", 0.6)]),                  # drain

    ("desk", "Desk 5'", "Office / Storage", 60, 30,
     [R(0.75, 0.75, 58.5, 28.5, 1, sw=1.2), L(2, 4, 58, 4, 0.5)]),
    ("office_chair", "Office Chair", "Office / Storage", 24, 24,
     [R(4, 1, 16, 4, 2, "#ffffff", 0.8), Ci(12, 13, 8.5, FILL, 1),
      Ci(12, 13, 3, "none", 0.5)]),
    ("office_set", "Office Desk & Chair", "Office / Storage", 54, 36,
     [R(0.75, 0.75, 52.5, 23.5, 1, sw=1.2),                 # desk top
      L(2, 4.5, 52, 4.5, 0.5),                              # back edge line
      R(38, 5, 13, 17, 0.6, "none", 0.5),                   # drawer pedestal
      L(38, 11, 51, 11, 0.4), L(38, 17, 51, 17, 0.4),       # drawers
      R(19, 24.5, 16, 3.5, 2, "#ffffff", 0.8),              # chair back
      Ci(27, 30, 5.5, FILL, 1), Ci(27, 30, 2.2, "none", 0.5)]),  # seat + post
    ("corner_desk", "Corner Desk 5'", "Office / Storage", 60, 60,
     [Pth("M0.75 0.75 H59.25 V23.25 H23.25 V59.25 H0.75 Z", FILL, 1.2),  # L top
      L(44, 3, 44, 20.5, 0.5), L(3, 44, 20.5, 44, 0.5),     # drawer lines
      Ci(36, 36, 6.5, FILL, 1), Ci(36, 36, 2.2, "none", 0.5),  # task chair
      Pth("M41.5 30.5 a8 8 0 0 1 0 11", "none", 0.8)]),     # chair back arc
    ("bookshelf", "Bookshelf 3'", "Office / Storage", 36, 12,
     [R(0.6, 0.6, 34.8, 10.8, 0.5, sw=1),
      L(12, 0.6, 12, 11.4, 0.5), L(24, 0.6, 24, 11.4, 0.5)]),
    ("wardrobe", "Wardrobe 4'", "Office / Storage", 48, 24,
     [R(0.75, 0.75, 46.5, 22.5, 1, sw=1.2), L(24, 0.75, 24, 23.25, 0.7),
      L(2, 7, 46, 7, 0.5, "2,2")]),

    # --- HVAC / mechanicals --------------------------------------------------
    ("gas_furnace", "Gas Furnace", "HVAC", 24, 30,
     [R(0.75, 0.75, 22.5, 28.5, 1.5, sw=1.2),
      Ci(12, 9, 6, FILL, 0.9), Ci(12, 9, 1.6, "none", 0.5),     # blower
      L(2, 18, 22, 18, 0.6),                                    # burner deck
      Pth("M12 20 c-3 3 -3 6 0 7 c3 -1 3 -4 0 -7 z", "#ffffff", 0.7)]),
    ("electric_furnace", "Electric Furnace", "HVAC", 21, 30,
     [R(0.75, 0.75, 19.5, 28.5, 1.5, sw=1.2),
      Ci(10.5, 9, 5.5, FILL, 0.9), Ci(10.5, 9, 1.5, "none", 0.5),
      L(2, 18, 19, 18, 0.6),
      Pth("M4 24 l3 -4 l3 4 l3 -4 l3 4 l3 -4", "none", 0.8)]),   # heat coil
    ("oil_furnace", "Oil Furnace", "HVAC", 26, 34,
     [R(0.75, 0.75, 24.5, 32.5, 1.5, sw=1.2),
      Ci(13, 11, 6.5, FILL, 0.9), Ci(13, 11, 1.7, "none", 0.5),
      Ci(13, 25, 3.5, "none", 0.8),                             # burner
      L(13, 28.5, 13, 33.5, 0.8)]),                             # fuel line
    ("gas_water_heater", "Gas Water Heater", "HVAC", 22, 22,
     [Ci(11, 11, 10.25, FILL, 1.3),
      Ci(11, 11, 2.2, "none", 0.8),                             # flue
      Pth("M11 13.5 c-2 2 -2 4 0 4.6 c2 -0.6 2 -2.6 0 -4.6 z",
          "#ffffff", 0.6)]),                                    # pilot flame
    ("electric_water_heater", "Electric Water Heater", "HVAC", 22, 22,
     [Ci(11, 11, 10.25, FILL, 1.3),
      R(7.5, 13.5, 7, 4, 0.6, "#ffffff", 0.7),                  # element panel
      L(9, 15.5, 13, 15.5, 0.5)]),
    ("water_softener", "Water Softener", "HVAC", 24, 15,
     [Ci(7.5, 7.5, 6.75, FILL, 1.1), Ci(7.5, 7.5, 2, "none", 0.5),  # resin
      R(15.5, 1.5, 8, 12, 1.5, FILL, 1),                        # brine tank
      L(14.25, 7.5, 15.5, 7.5, 0.7)]),
    ("gas_tank", "Gas Tank", "HVAC", 120, 36,
     [R(0.75, 0.75, 118.5, 34.5, 17.25, sw=1.5),                # propane cyl.
      Ci(60, 18, 4.5, "none", 0.9),                             # dome valve
      L(18, 18, 42, 18, 0.5), L(78, 18, 102, 18, 0.5)]),
    ("oil_tank", "Oil Tank", "HVAC", 60, 27,
     [R(0.75, 0.75, 58.5, 25.5, 12.75, sw=1.5),
      Ci(16, 13.5, 2.6, "none", 0.8), Ci(44, 13.5, 2.6, "none", 0.8),
      L(30, 4, 30, 23, 0.4, "3,3")]),                           # fittings
    ("electric_panel", "Electric Panel", "HVAC", 16, 4,
     [R(0.5, 0.5, 15, 3, 0.4, sw=1.1), L(8, 0.5, 8, 3.5, 0.5),
      L(3, 1.3, 7, 1.3, 0.4), L(3, 2.7, 7, 2.7, 0.4),
      L(9, 1.3, 13, 1.3, 0.4), L(9, 2.7, 13, 2.7, 0.4)]),       # breakers
    ("car_charger", "Car Charger", "HVAC", 8, 6,
     [R(0.6, 0.6, 6.8, 3.8, 0.8, sw=1.1),
      Ci(4, 2.5, 1.5, "none", 0.7), Ci(4, 2.5, 0.5, "none", 0.5),
      L(4, 4.4, 4, 6, 0.8)]),                                   # plug + cable
    ("battery_wall", "Battery Wall", "HVAC", 45, 6,
     [R(0.75, 0.75, 43.5, 4.5, 2, sw=1.2),
      L(15, 0.75, 15, 5.25, 0.4), L(30, 0.75, 30, 5.25, 0.4),
      Pth("M23 1.8 l-2.2 2.2 l1.6 0 l-1.6 1.4 l3.6 -2.4 l-1.6 0 "
          "l1.6 -1.2 z", "#ffffff", 0.6)]),                     # bolt
    ("well_pump", "Well Pump", "HVAC", 24, 24,
     [Ci(12, 13.5, 9.8, FILL, 1.3), Ci(12, 13.5, 2.2, "none", 0.6),
      R(10, 1.5, 4, 3, 0.5, "none", 0.7)]),                     # pressure tank
    ("heat_exchanger", "Heat Exchanger", "HVAC", 30, 30,
     [R(0.75, 0.75, 28.5, 28.5, 2, sw=1.2),
      Ci(15, 15, 12.5, "none", 0.9), Ci(15, 15, 2.5, FILL, 0.7),
      L(15, 15, 15, 3.5, 0.7), L(15, 15, 25, 21, 0.7),
      L(15, 15, 5, 21, 0.7)]),                                  # fan

    # -- Framing: structural elements.  The placed stair is drawn live by the
    # app (step count from the room's ceiling height); this is the palette
    # icon for a representative full flight.
    ("stairs", "Stairs (flight)", "Framing", 36, 120,
     [R(0.75, 0.75, 34.5, 118.5, 0, sw=1.2)]
     + [L(0.75, i * 10.8 + 6.0, 35.25, i * 10.8 + 6.0, 0.6)
        for i in range(10)]
     + [L(18, 104, 18, 26, 1.1), Pth("M 12 36 L 18 24 L 24 36", sw=1.1)]),
    ("elevator", "Residential Elevator", "Framing", 48, 60,
     [R(0.75, 0.75, 46.5, 58.5, 0, sw=1.2),
      R(4, 4, 40, 48, 0, "none", 0.6),
      L(4, 4, 44, 52, 0.4), L(44, 4, 4, 52, 0.4),               # cab X
      L(6, 56.5, 22, 56.5, 1.3), L(26, 56.5, 42, 56.5, 1.3),    # sliding doors
      Ci(40, 30, 1.3, "none", 0.6)]),                           # call panel
]

# --------------------------------------------------------------- 3D solids
# The catalog's THIRD DIMENSION, authored here because the manifest is a
# generated asset and this is the one place a new symbol can be added.
#
# WHY IT LIVES IN THE CATALOG AND NOT IN A VIEWER.  fp3d.py carried its own
# table of widths, depths, heights and material families -- a second definition
# of data this file already owns, and measurably a WRONG one: 58 of the 95
# catalog kinds were missing from it entirely (drawn as a 24x24x30 magenta
# default), and of the 37 it shared, 22 disagreed on footprint, three of those
# by transposing width and depth so the item rendered rotated 90 degrees. One
# definition, here, is the fix.
#
#   height_in     REQUIRED, and deliberately has no default.  A wrong height
#                 that a default supplied is indistinguishable from a right
#                 one; a missing entry that stops the generator is not.
#                 AUTHORED, not measured -- these are architect's nominals.
#   elevation_in  height of the item's UNDERSIDE above the level's floor.
#                 0 for anything floor-bearing.  Non-zero for the wall-hung
#                 items and for the one counter-mounted one, kitchen_sink,
#                 whose rim then lands at the standard 36".
#   form          which generator builds the solid.  box and slab are
#                 implemented; seat / bed / basin / enclosure / vehicle build
#                 as boxes for now, and the viewer reports any form it does
#                 not know rather than guessing.  planting and prism are
#                 RESERVED and unused: nothing in the catalog is a plant (see
#                 the landscape-kinds note below), and prism -- extruding the
#                 symbol's true SVG outline -- is a second pass.
#   material      a NAME only.  Colour, roughness and metalness live once, in
#                 MATERIALS below, and are written to materials.json.  Putting
#                 three numbers on 95 entries would rebuild the duplication
#                 this table exists to remove.
#
# LANDSCAPE KINDS ARE ABSENT ON PURPOSE.  tools/make_site_demo.py mints
# `bench`, `planter`, `shrub` and `tree`, which exist in no catalog -- the
# editor cannot place them and the viewer's old table was their only
# definition anywhere.  They are not added here: drawing four new symbols
# would pre-empt P5.2's landscape catalog.  They now render as unknown, which
# is what the editor already thinks of them.
SOLIDS = {
    # id                      height  elev  form         material
    # -- Living
    "sofa":                   (32,      0, "seat",      "soft"),
    "loveseat":               (32,      0, "seat",      "soft"),
    "armchair":               (32,      0, "seat",      "soft"),
    "coffee_table":           (18,      0, "slab",      "wood"),
    "side_table":             (24,      0, "slab",      "wood"),
    "tv_stand":               (24,      0, "box",       "wood"),
    # A wall-hung panel is a box, not a top on legs.  It was authored `slab`
    # before the slab generator existed; writing the generator is what showed
    # the name was wrong, which is the argument for naming forms at all.
    "large_tv":               (38,     42, "box",       "screen"),
    "gas_fireplace":          (40,      0, "box",       "stone"),
    # -- Dining
    "dining_table":           (30,      0, "slab",      "wood"),
    "dining_table_round":     (30,      0, "slab",      "wood"),
    "dining_chair":           (34,      0, "seat",      "wood"),
    "buffet":                 (36,      0, "box",       "wood"),
    "hutch":                  (78,      0, "box",       "wood"),
    # -- Kitchen.  Base cabinets and counters 36"; wall cabinets 30" tall with
    # their underside 54" up, the standard 18" backsplash above a counter.
    "refrigerator":           (70,      0, "box",       "metal"),
    "range":                  (36,      0, "box",       "metal"),
    "dishwasher":             (34,      0, "box",       "metal"),
    "kitchen_sink":           (10,     26, "basin",     "metal"),
    "base_cab_24":            (36,      0, "box",       "wood"),
    "base_cab_36":            (36,      0, "box",       "wood"),
    "drawer_base_18":         (36,      0, "box",       "wood"),
    "sink_base_36":           (36,      0, "box",       "wood"),
    "corner_base_36":         (36,      0, "box",       "wood"),
    "pantry_18":              (84,      0, "box",       "wood"),
    "pantry_24":              (84,      0, "box",       "wood"),
    "pantry_36":              (84,      0, "box",       "wood"),
    "wall_cab_24":            (30,     54, "box",       "wood"),
    "wall_cab_30":            (30,     54, "box",       "wood"),
    "wall_cab_36":            (30,     54, "box",       "wood"),
    "kitchen_island":         (36,      0, "box",       "wood"),
    "island_sink":            (36,      0, "box",       "wood"),
    # -- Bedroom
    "bed_king":               (26,      0, "bed",       "soft"),
    "bed_queen":              (26,      0, "bed",       "soft"),
    "bed_full":               (26,      0, "bed",       "soft"),
    "bed_twin":               (26,      0, "bed",       "soft"),
    "nightstand":             (26,      0, "box",       "wood"),
    "dresser":                (34,      0, "box",       "wood"),
    # -- Bathroom
    "bathtub":                (20,      0, "enclosure", "porcelain"),
    "shower":                 (78,      0, "enclosure", "glass"),
    "walk_in_shower":         (78,      0, "enclosure", "glass"),
    "glass_shower":           (78,      0, "enclosure", "glass"),
    "toilet":                 (30,      0, "box",       "porcelain"),
    "vanity":                 (34,      0, "box",       "wood"),
    "vanity_24":              (34,      0, "box",       "wood"),
    "vanity_36":              (34,      0, "box",       "wood"),
    "vanity_48":              (34,      0, "box",       "wood"),
    # -- Laundry
    "washer":                 (38,      0, "box",       "metal"),
    "dryer":                  (38,      0, "box",       "metal"),
    # -- Garage
    "suv":                    (70,      0, "vehicle",   "vehicle"),
    "car":                    (56,      0, "vehicle",   "vehicle"),
    "motorcycle":             (48,      0, "vehicle",   "vehicle"),
    "bicycle":                (42,      0, "vehicle",   "vehicle"),
    "boat":                   (60,      0, "vehicle",   "vehicle"),
    "workbench":              (36,      0, "slab",      "wood"),
    "storage_shelves":        (72,      0, "box",       "metal"),
    "lawnmower":              (40,      0, "vehicle",   "vehicle"),
    "garden_tractor":         (50,      0, "vehicle",   "vehicle"),
    "riding_mower_snow":      (46,      0, "vehicle",   "vehicle"),
    "boat_trailer":           (72,      0, "vehicle",   "vehicle"),
    "snowblower":             (42,      0, "vehicle",   "vehicle"),
    "wheelbarrow":            (30,      0, "box",       "metal"),
    "trashcan":               (40,      0, "box",       "metal"),
    # -- Shop
    "toolchest":              (40,      0, "box",       "metal"),
    "table_saw":              (36,      0, "slab",      "metal"),
    "lathe":                  (48,      0, "box",       "metal"),
    "jointer":                (36,      0, "slab",      "metal"),
    "drill_press":            (68,      0, "box",       "metal"),
    "cutoff_saw":             (40,      0, "box",       "metal"),
    "bandsaw":                (72,      0, "box",       "metal"),
    "planer":                 (42,      0, "box",       "metal"),
    # -- Sunroom.  umbrella_table is the TABLE's height; the umbrella above it
    # is not modelled, and a 96" box would be a lie about a shade.
    "lounge_chair":           (30,      0, "seat",      "soft"),
    "sauna":                  (84,      0, "enclosure", "wood"),
    "umbrella_table":         (30,      0, "slab",      "wood"),
    "swim_spa":               (40,      0, "enclosure", "water"),
    "whirlpool":              (36,      0, "enclosure", "water"),
    # -- Office / Storage
    "desk":                   (30,      0, "slab",      "wood"),
    "office_chair":           (40,      0, "seat",      "soft"),
    "office_set":             (30,      0, "slab",      "wood"),
    "corner_desk":            (30,      0, "slab",      "wood"),
    "bookshelf":              (72,      0, "box",       "wood"),
    "wardrobe":               (72,      0, "box",       "wood"),
    # -- HVAC.  The four wall-hung ones carry an elevation; everything else
    # here stands on the floor.
    "gas_furnace":            (60,      0, "box",       "metal"),
    "electric_furnace":       (60,      0, "box",       "metal"),
    "oil_furnace":            (60,      0, "box",       "metal"),
    "gas_water_heater":       (60,      0, "box",       "metal"),
    "electric_water_heater":  (60,      0, "box",       "metal"),
    "water_softener":         (48,      0, "box",       "metal"),
    "gas_tank":               (40,      0, "box",       "metal"),
    "oil_tank":               (44,      0, "box",       "metal"),
    "electric_panel":         (30,     48, "box",       "metal"),
    "car_charger":            (14,     42, "box",       "metal"),
    "battery_wall":           (30,     24, "box",       "metal"),
    "well_pump":              (36,      0, "box",       "metal"),
    "heat_exchanger":         (30,      0, "box",       "metal"),
    # -- Framing.  stairs is a full STOREY RISE, which is what the object's
    # height is; that a box generator renders it as a 108" block is the
    # renderer's gap and is reported as one, not hidden by authoring a wrong
    # number here.
    "stairs":                (108,      0, "box",       "wood"),
    "elevator":               (96,      0, "box",       "metal"),
}

# Material properties, ONCE.  Colour is (r, g, b, a) in 0..1.  These values are
# carried over unchanged from the viewer's FAMILY_C so that moving them here
# changes no pixel; the known caveat that they were tuned for baked flat
# shading and read dark under PBR is recorded in VIEWER_NOTES.md section 5 and
# is a separate decision from this move.
MATERIALS = {
    "soft":      {"colour": [0.44, 0.49, 0.57, 1.00],
                  "roughness": 0.85, "metalness": 0.00},
    "wood":      {"colour": [0.52, 0.37, 0.23, 1.00],
                  "roughness": 0.85, "metalness": 0.00},
    "porcelain": {"colour": [0.93, 0.94, 0.95, 1.00],
                  "roughness": 0.25, "metalness": 0.00},
    "glass":     {"colour": [0.62, 0.76, 0.80, 0.35],
                  "roughness": 0.12, "metalness": 0.00},
    "water":     {"colour": [0.28, 0.54, 0.70, 0.55],
                  "roughness": 0.12, "metalness": 0.00},
    "metal":     {"colour": [0.66, 0.68, 0.71, 1.00],
                  "roughness": 0.35, "metalness": 0.85},
    "stone":     {"colour": [0.55, 0.53, 0.50, 1.00],
                  "roughness": 0.85, "metalness": 0.00},
    "vehicle":   {"colour": [0.26, 0.28, 0.32, 1.00],
                  "roughness": 0.45, "metalness": 0.30},
    "screen":    {"colour": [0.10, 0.11, 0.13, 1.00],
                  "roughness": 0.15, "metalness": 0.20},
    # Loud on purpose, and the ONLY entry a viewer may fall back to: an item
    # whose kind, form or material the catalog does not define must LOOK wrong.
    "unknown":   {"colour": [0.85, 0.35, 0.55, 1.00],
                  "roughness": 0.60, "metalness": 0.00},
}

# The generator refuses to write a half-authored catalog.  A missing height is
# the failure this file exists to make impossible: it is the one field with no
# safe default, so a new symbol added without one stops here rather than
# reaching a viewer as a guess.
_ids = {fid for fid, *_ in FURNISHINGS}
_unauthored = sorted(_ids - set(SOLIDS))
_orphans = sorted(set(SOLIDS) - _ids)
_bad_material = sorted({m for _h, _e, _f, m in SOLIDS.values()
                        if m not in MATERIALS})
if _unauthored or _orphans or _bad_material:
    raise SystemExit(
        "assets not written -- the 3D data model is incomplete:\n"
        + (f"  {len(_unauthored)} furnishing(s) with no SOLIDS row: "
           f"{', '.join(_unauthored)}\n" if _unauthored else "")
        + (f"  {len(_orphans)} SOLIDS row(s) naming no furnishing: "
           f"{', '.join(_orphans)}\n" if _orphans else "")
        + (f"  {len(_bad_material)} material(s) not in MATERIALS: "
           f"{', '.join(_bad_material)}\n" if _bad_material else ""))

# Purchase prices are filled in at runtime by the app's AI ▸ Update
# furnishing prices… tool, so carry any existing prices across regeneration
# rather than resetting them to 0.
try:
    _prev_price = {e["id"]: float(e.get("price", 0.0))
                   for e in json.loads((FURN / "manifest.json")
                                       .read_text(encoding="utf-8"))}
except (OSError, ValueError, KeyError, TypeError):
    _prev_price = {}

manifest = []
_pending, _malformed = [], []
for fid, name, cat, w, d, body in FURNISHINGS:
    _text = svg(w, d, body)
    _err = svg_error(_text)
    if _err:
        _malformed.append((f"{fid}.svg", _err,
                           "body is a str, not a list of elements"
                           if isinstance(body, str) else "malformed element"))
    _pending.append((FURN / f"{fid}.svg", _text))
    height, elevation, form, material = SOLIDS[fid]
    manifest.append({"id": fid, "name": name, "category": cat,
                     "file": f"{fid}.svg", "width_in": w, "depth_in": d,
                     "height_in": height, "elevation_in": elevation,
                     "form": form, "material": material,
                     "price": _prev_price.get(fid, 0.0)})
# D70: REFUSE BEFORE WRITING ANYTHING, the same shape as the data-model gate
# above -- a half-written asset tree is worse than none, and this generator is
# the only thing between a bad symbol and a silently blank item.
if _malformed:
    raise SystemExit(
        f"assets not written -- {len(_malformed)} malformed SVG(s):\n"
        + "".join(f"  {n}: {why} ({err})\n" for n, err, why in _malformed))
for _path, _text in _pending:
    _path.write_text(_text, encoding="utf-8")

(FURN / "manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
(FURN / "materials.json").write_text(
    json.dumps(MATERIALS, indent=2) + "\n", encoding="utf-8")

# Palette sections: furnishings grouped by room type; items are the SVG
# file names and may appear in several groups.  "All" lists everything
# and is the section the app opens by default.
GROUPS = [
    ("Living Room", ["sofa", "loveseat", "armchair", "coffee_table",
                     "side_table", "tv_stand", "large_tv", "gas_fireplace",
                     "bookshelf"]),
    ("Dining Room", ["dining_table", "dining_table_round", "dining_chair",
                     "buffet", "hutch"]),
    ("Kitchen", ["refrigerator", "range", "dishwasher", "kitchen_sink",
                 "base_cab_24", "base_cab_36", "drawer_base_18",
                 "sink_base_36", "corner_base_36", "wall_cab_24",
                 "wall_cab_30", "wall_cab_36", "kitchen_island", "island_sink",
                 "pantry_18", "pantry_24", "pantry_36", "dining_chair"]),
    ("Bedroom", ["bed_king", "bed_queen", "bed_full", "bed_twin",
                 "nightstand", "dresser", "wardrobe", "armchair",
                 "tv_stand", "desk", "office_chair", "bookshelf"]),
    ("Bathroom", ["bathtub", "shower", "walk_in_shower", "glass_shower",
                  "toilet", "vanity", "vanity_24", "vanity_36", "vanity_48"]),
    ("Laundry", ["washer", "dryer"]),
    ("Garage", ["suv", "car", "motorcycle", "bicycle", "boat",
                "boat_trailer", "garden_tractor", "riding_mower_snow",
                "workbench", "storage_shelves", "lawnmower", "snowblower",
                "wheelbarrow", "trashcan"]),
    ("Shop", ["toolchest", "table_saw", "lathe", "jointer", "drill_press",
              "cutoff_saw", "bandsaw", "planer", "workbench",
              "storage_shelves"]),
    ("Sunroom", ["lounge_chair", "sauna", "umbrella_table", "swim_spa",
                 "whirlpool", "armchair", "side_table"]),
    ("Office", ["desk", "office_chair", "office_set", "corner_desk",
                "bookshelf", "armchair", "side_table"]),
    ("HVAC", ["gas_furnace", "electric_furnace", "oil_furnace",
              "gas_water_heater", "electric_water_heater", "water_softener",
              "gas_tank", "oil_tank", "electric_panel", "car_charger",
              "battery_wall", "well_pump", "heat_exchanger"]),
    ("Framing", ["stairs", "elevator"]),
]
groups_out = [{"name": "All",
               "items": [f"{fid}.svg" for fid, *_ in FURNISHINGS]}]
groups_out += [{"name": name, "items": [f"{i}.svg" for i in ids]}
               for name, ids in GROUPS]
(FURN / "groups.json").write_text(
    json.dumps(groups_out, indent=2) + "\n", encoding="utf-8")

(FURN / "LICENSE").write_text(
    "Floor Planner furnishing symbol library\n"
    "----------------------------------------\n"
    "These top-view furniture/fixture symbols were drawn for this project\n"
    "and are released under CC0 1.0 Universal (public domain dedication).\n"
    "https://creativecommons.org/publicdomain/zero/1.0/\n",
    encoding="utf-8")
(FURN / "README.md").write_text(
    "# Furnishing symbol library (CC0)\n\n"
    "Top-view architectural symbols used by the Furnishings palette.\n\n"
    "* Every SVG `viewBox` is in **inches** (`0 0 WIDTH DEPTH`), so the app\n"
    "  renders each symbol at true scale (1 scene unit = 1\").\n"
    "* `manifest.json` lists the catalog: `id`, `name`, `category`, `file`,\n"
    "  `width_in`, `depth_in`, `price` (USD purchase cost; the app's\n"
    "  AI ‣ Update furnishing prices… tool fills these in), plus the four\n"
    "  fields the 3D viewers read:\n"
    "  * `height_in` — the item's height in inches.  **Required, and it has\n"
    "    no default**: a wrong height supplied by a default cannot be told\n"
    "    apart from a right one, so a symbol added without one stops the\n"
    "    generator instead.  These are authored architect's nominals.\n"
    "  * `elevation_in` — the height of the item's underside above the\n"
    "    level's floor.  `0` for anything floor-bearing; non-zero for the\n"
    "    wall-hung items (upper cabinets, the large TV, the electric panel,\n"
    "    the car charger, the battery wall) and for the counter-mounted\n"
    "    `kitchen_sink`, whose rim then lands at the standard 36\".\n"
    "  * `form` — which solid generator builds it: `box`, `slab` (a top on\n"
    "    legs), `seat`, `bed`, `basin`, `enclosure`, `vehicle`, and the\n"
    "    reserved `planting` and `prism`.  A viewer that does not implement\n"
    "    a form falls back to `box` and **says so in its report**; an\n"
    "    unrecognised one renders in the loud magenta.\n"
    "  * `material` — a name only, resolved in `materials.json`.\n"
    "* `materials.json` holds each material's `colour` (r, g, b, a in 0..1),\n"
    "  `roughness` and `metalness` — **once**, so the properties are not\n"
    "  repeated across 95 catalog entries.  `unknown` is the deliberate\n"
    "  fallback and is loud on purpose: an item the catalog does not define\n"
    "  must look wrong rather than plausible.\n"
    "* `groups.json` defines the palette's expandable sections: a list of\n"
    "  `{name, items}` where each item is an SVG file name from this\n"
    "  directory.  A furnishing may appear in several groups.  The `All`\n"
    "  group always shows the whole library and is open by default.\n\n"
    "To add your own symbol: drop an SVG here whose viewBox matches the\n"
    "real-world footprint in inches, add a manifest entry, and list it in\n"
    "the groups it belongs to.\n\n"
    "**Everything in this directory is generated by `_gen_assets.py`** —\n"
    "including this README, the manifest and `materials.json`.  Edit that\n"
    "script and re-run it; a hand edit here is overwritten on the next run.\n",
    encoding="utf-8")

# ---------------------------------------------------------------- tool icons
TOOL_ICONS = {
    "select": [
        '<path d="M7 3 L7 18 L11 14.5 L13.5 20 L16 18.9 L13.5 13.5 '
        'L18.5 13.5 Z" fill="#1f2937"/>'],
    "wall_ext": [
        '<rect x="2.5" y="9" width="19" height="6" fill="#1f2937"/>',
        '<line x1="2.5" y1="12" x2="21.5" y2="12" stroke="#f8fafc" '
        'stroke-width="1" stroke-dasharray="3,2"/>'],
    "wall_int": [
        '<rect x="2.5" y="10" width="19" height="4" fill="#9ca3af"/>',
        '<line x1="2.5" y1="12" x2="21.5" y2="12" stroke="#f8fafc" '
        'stroke-width="1" stroke-dasharray="3,2"/>'],
    "door": [
        '<line x1="2" y1="20" x2="6" y2="20" stroke="#1f2937" '
        'stroke-width="2.4"/>',
        '<line x1="18" y1="20" x2="22" y2="20" stroke="#1f2937" '
        'stroke-width="2.4"/>',
        '<line x1="6.5" y1="19.5" x2="6.5" y2="7.5" stroke="#1f2937" '
        'stroke-width="1.6"/>',
        '<path d="M6.5 7.5 A12 12 0 0 1 18.5 19.5" fill="none" '
        'stroke="#1f2937" stroke-width="1.2" stroke-dasharray="2.5,2"/>'],
    "window": [
        '<rect x="2.5" y="9" width="19" height="6" fill="#f8fafc" '
        'stroke="#1f2937" stroke-width="1.4"/>',
        '<line x1="2.5" y1="12" x2="21.5" y2="12" stroke="#1f2937" '
        'stroke-width="1"/>'],
    "room": [
        # speech-bubble callout with a tail at the lower left
        '<path d="M6 3.5 H18 Q21 3.5 21 6.5 V12 Q21 15 18 15 H12.5 '
        'L6.5 20.5 L8.5 15 H6 Q3 15 3 12 V6.5 Q3 3.5 6 3.5 Z" '
        'fill="#f8fafc" stroke="#1f2937" stroke-width="1.5" '
        'stroke-linejoin="round"/>',
        '<line x1="7" y1="8" x2="17" y2="8" stroke="#1f2937" '
        'stroke-width="1.3"/>',
        '<line x1="7" y1="11" x2="13.5" y2="11" stroke="#1f2937" '
        'stroke-width="1.3"/>'],
    "delete": [
        '<line x1="4.5" y1="6.5" x2="19.5" y2="6.5" stroke="#1f2937" '
        'stroke-width="1.6"/>',
        '<line x1="9.5" y1="4" x2="14.5" y2="4" stroke="#1f2937" '
        'stroke-width="1.6"/>',
        '<path d="M6.5 6.5 L7.5 20.5 L16.5 20.5 L17.5 6.5" fill="none" '
        'stroke="#1f2937" stroke-width="1.6"/>',
        '<line x1="10" y1="9.5" x2="10.3" y2="17.5" stroke="#1f2937" '
        'stroke-width="1.2"/>',
        '<line x1="14" y1="9.5" x2="13.7" y2="17.5" stroke="#1f2937" '
        'stroke-width="1.2"/>'],
    "zoomfit": [
        '<circle cx="10.5" cy="10.5" r="6" fill="none" stroke="#1f2937" '
        'stroke-width="1.7"/>',
        '<line x1="15" y1="15" x2="20.5" y2="20.5" stroke="#1f2937" '
        'stroke-width="2.2"/>'],
    "undo": [
        '<path d="M6 8 H14.5 A5.5 5.5 0 1 1 9 18.5" fill="none" '
        'stroke="#1f2937" stroke-width="1.8" stroke-linecap="round"/>',
        '<polyline points="9.5,4.5 6,8 9.5,11.5" fill="none" '
        'stroke="#1f2937" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round"/>'],
    "redo": [
        '<path d="M18 8 H9.5 A5.5 5.5 0 1 0 15 18.5" fill="none" '
        'stroke="#1f2937" stroke-width="1.8" stroke-linecap="round"/>',
        '<polyline points="14.5,4.5 18,8 14.5,11.5" fill="none" '
        'stroke="#1f2937" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round"/>'],
    "record": [
        # the universal red "record" dot
        '<circle cx="12" cy="12" r="7" fill="#dc2626" stroke="#991b1b" '
        'stroke-width="1.4"/>'],
}
# the icons build their SVG inline rather than through `svg()`, so the D70
# check is applied here too -- one writer skipped is the whole gap.
_icons, _bad_icons = [], []
for name, body in TOOL_ICONS.items():
    _text = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
             'width="24" height="24">\n' + "\n".join(body) + "\n</svg>\n")
    _err = svg_error(_text)
    if _err:
        _bad_icons.append((f"{name}.svg", _err,
                           "body is a str, not a list of elements"
                           if isinstance(body, str) else "malformed element"))
    _icons.append((ICONS / f"{name}.svg", _text))
if _bad_icons:
    raise SystemExit(
        f"icons not written -- {len(_bad_icons)} malformed SVG(s):\n"
        + "".join(f"  {n}: {why} ({err})\n" for n, err, why in _bad_icons))
for _path, _text in _icons:
    _path.write_text(_text, encoding="utf-8")
(ICONS / "README.md").write_text(
    "# Toolbar icons\n\nSVG icons for the Floor Planner toolbar, drawn for "
    "this project (CC0).\n", encoding="utf-8")

print(f"wrote {len(FURNISHINGS)} furnishing symbols + manifest, "
      f"{len(TOOL_ICONS)} tool icons")
