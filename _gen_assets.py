# One-shot generator for assets/icons (toolbar) and assets/furnishings
# (top-view furniture symbol library, CC0).  Furnishing SVGs use a viewBox
# in INCHES so the app can render them at true scale (1 scene unit = 1").
import importlib.util
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "assets"
ICONS = ROOT / "icons"
FURN = ROOT / "furnishings"

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


# THE REGION HEIGHT ANNOTATION -- `data-h`, and it carries a HEIGHT AND NOTHING
# ELSE.  Ruled 2026-08-14:
#
#     The region's POSITION comes from the artwork; only its HEIGHT is
#     annotated. The moment the annotation could also say WHERE, there are two
#     sources of truth about where a pillow is, and they will disagree.
#
# Same discipline as the thickness table (D73): ONE NORMATIVE SOURCE PER FACT.
# The drawing already states where every region is, to the inch, because it has
# to draw it; what it cannot state is what the region IS -- and a height is the
# smallest thing that says so.  A parser cannot tell a pillow from a drain.
#
# The value is the piece's TOP, in inches above the item's base -- the same
# datum as the catalog's `height_in`, which stays the item's OVERALL height.
# So a value BELOW the body's height is a well (a tub's inside, a sink bowl)
# and one above it is a raised region (a pillow, a bench, a chair back).
def _h(h):
    return f' data-h="{h}"' if h is not None else ""


def R(x, y, w, h, rx=0.0, fill=FILL, sw=1.0, dash=None, top=None):
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{INK}" stroke-width="{sw}"'
            f'{extra}{_h(top)}/>')


def L(x1, y1, x2, y2, sw=0.7, dash=None):
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{INK}" stroke-width="{sw}"{extra}/>')


def Ci(cx, cy, r, fill="none", sw=0.7, top=None):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
            f'stroke="{INK}" stroke-width="{sw}"{_h(top)}/>')


def El(cx, cy, rx, ry, fill="#ffffff", sw=0.8, top=None):
    return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
            f'fill="{fill}" stroke="{INK}" stroke-width="{sw}"{_h(top)}/>')


def Pth(d, fill="none", sw=0.8):
    return (f'<path d="{d}" fill="{fill}" stroke="{INK}" '
            f'stroke-width="{sw}"/>')


# ---------------------------------------------------------------- furniture
def bed(w, d, pillows):
    parts = [R(0.75, 0.75, w - 1.5, d - 1.5, 2, sw=1.2)]
    if pillows == 1:
        parts.append(R(w * 0.18, 3, w * 0.64, 10, 2.5, "#ffffff", 0.8, top=30))
    else:
        pw = (w - 13) / 2
        parts.append(R(4.5, 3, pw, 10, 2.5, "#ffffff", 0.8, top=30))
        parts.append(R(w - 4.5 - pw, 3, pw, 10, 2.5, "#ffffff", 0.8, top=30))
    parts.append(L(0.75, 19, w - 0.75, 19, 0.8))      # blanket fold line
    return parts


def seat(w, d, cushions, arm=7.0, seat_h=17, arm_h=24, back_h=32):
    """Upholstered seat: body, BACK and ARMS as closed regions.

    THE BACK AND ARMS USED TO BE LINES -- `L(0.75, 7, w - 0.75, 7)` for the
    back band, one more per arm -- and a line has no inside. Two consequences,
    and the second is why this changed:

      * IN 3D there was no region to extrude, so the whole footprint rose to
        the catalog height (32", the BACK height) and a sofa rendered as a
        32-inch slab. `dining_chair` and `office_chair` drew their backs as
        closed rects and came out right, IN THE SAME FORM -- so the three
        upholstered seats were not a limit of the approach, they were three
        symbols drawn inconsistently with their own neighbours.
      * IN PLAN it was simply less true. A sofa back HAS thickness, and a line
        says it does not.

    That second point is the tell that this is the right fix rather than a
    workaround: it improves the drawing on its own terms, and the 3D follows.

    Heights are the item's real ones -- seat 17", arms 24", back 32" -- and the
    catalog's `height_in` stays 32, the overall height.
    """
    parts = [R(0.75, 0.75, w - 1.5, d - 1.5, 3, sw=1.2, top=seat_h),
             R(0.75, 0.75, w - 1.5, 6.25, 3, FILL, 0.7, top=back_h),
             R(0.75, 7, arm - 0.75, d - 7.75, 2, FILL, 0.7, top=arm_h),
             R(w - arm, 7, arm - 0.75, d - 7.75, 2, FILL, 0.7, top=arm_h)]
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
     [R(1, 0.75, 16, 2.8, 1.4, "#ffffff", 0.8, top=34),   # back
      R(1.4, 3.8, 15.2, 13.4, 2.5, top=18)]),             # seat
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
      R(3, 4, 12, 14, 2.5, "#ffffff", 0.8, top=2),     # bowls, 8" deep
      R(18, 4, 12, 14, 2.5, "#ffffff", 0.8, top=2),
      Ci(16.5, 2.2, 1, "none", 0.6)]),
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
      R(3.5, 3.5, 23, 53, 8, "#ffffff", 0.8, top=4),   # the well
      Ci(15, 10, 1.5, "none", 0.6)]),
    ("shower", "Shower 36\"", "Bathroom", 36, 36,
     [R(0.75, 0.75, 34.5, 34.5, 1, sw=1.2), R(3, 3, 30, 30, 1, "none", 0.6),
      L(3, 3, 33, 33, 0.4), L(33, 3, 3, 33, 0.4),
      Ci(18, 18, 1.8, "none", 0.7),
      # hinged door leaf, swung proud of the front opening -- a BESIDE part
      # (its centroid sits outside the body ring), not a nested region, so
      # it shares the body's own glass material and is never occluded by it
      # (0032-report.md SS4: a region enclosed by translucent glass does not
      # composite -- D76 -- but a beside part standing next to the body,
      # never inside it, is not that case)
      R(4, 34.6, 27, 2.6, 0.4, top=76)]),
    ("walk_in_shower", "Luxury Walk-in Shower", "Bathroom", 60, 42,
     [R(0.75, 0.75, 58.5, 40.5, 1.5, sw=1.2),               # tiled enclosure
      # faint tile grout grid
      L(15, 0.75, 15, 41.25, 0.3), L(30, 0.75, 30, 41.25, 0.3),
      L(45, 0.75, 45, 41.25, 0.3),
      L(0.75, 14, 59.25, 14, 0.3), L(0.75, 28, 59.25, 28, 0.3),
      # built-in bench seat at the left end
      R(2.5, 2.5, 11, 37, 1.2, "#ffffff", 0.8, top=18),
      L(13.5, 2.5, 13.5, 39.5, 0.5),
      # ceiling rainfall head (centre) plus a hand shower and valve trim
      Ci(37, 21, 7.5, "none", 0.7), Ci(37, 21, 2.2, "none", 0.5),
      Ci(24, 6.5, 1.6, "none", 0.6), Ci(30, 6.5, 1.1, "none", 0.6),
      # linear drain along the right end
      R(53, 4, 3.5, 34, 0.4, "none", 0.6), L(54.75, 4, 54.75, 38, 0.4),
      # frameless glass screen on the front with a walk-in opening
      L(31, 39.8, 58.5, 39.8, 1.6), L(31, 39.8, 31, 33, 1.2),
      # the fixed glass panel itself, standing at the opening -- a BESIDE
      # part, same reason as shower's door leaf: a walk-in's opening is a
      # single FIXED panel, not a hinged door (glass_shower's) or a full
      # stall door (shower's), which is its own categorical mark rather
      # than a copy of either. Near full height, not a low curb -- a curb
      # this shallow (originally 4in) read as barely a seam at the render's
      # own camera angle; the bench (a NESTED region) is correct and still
      # invisible through the glass body (D76), so identity cannot rest on
      # it alone
      R(31, 41.0, 27.5, 1.8, 0.3, top=74)]),
    ("glass_shower", "Luxury Glass Shower 5' x 4'", "Bathroom", 60, 48,
     [# floor-to-ceiling glass enclosure -- ONE FILLED BODY (was four
      # boundary lines with a gap for the door: no closed fill anywhere,
      # so nothing here could be extruded at all -- predicate 1,
      # 0032-report.md SS1). A conventional plan symbol (solid outline plus
      # a swing arc) reads at least as correctly as the line-art gap did.
      R(1, 1, 58, 46, 0, sw=1.1),
      # a faint inner line for the glass thickness
      R(2.6, 2.6, 54.8, 43.0, 0, "none", 0.35),
      # frameless glass door swinging in from the front opening
      L(34, 47, 34, 24, 1.3),
      Pth("M 11 47 A 23 23 0 0 1 34 24", "none", 0.6),
      # the door leaf itself -- a BESIDE part, same reason as shower's
      R(11, 46.4, 23, 2.6, 0.3, top=76),
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
    # 0333: over the range.  Both hang overhead, so both are drawn DASHED,
    # like a wall cabinet; the filled rectangle is what the 3D falls back to.
    ("range_hood", "Range Hood 30\"", "Kitchen", 30, 20,
     [R(0.6, 0.6, 28.8, 18.8, 1.5, "#ffffff", 0.9, "3,2"),
      R(4, 4, 22, 12, 1, "none", 0.5, "3,2"),
      Ci(9, 15.5, 1.3, "none", 0.5), Ci(21, 15.5, 1.3, "none", 0.5)]),
    ("microwave_otr", "Microwave, Over-Range 30\"", "Kitchen", 30, 16,
     [R(0.6, 0.6, 28.8, 14.8, 1, "#ffffff", 0.9, "3,2"),
      L(22.5, 0.6, 22.5, 15.4, 0.5, "3,2"),
      R(3, 3, 17, 9.5, 0.8, "none", 0.5, "3,2")]),
    # 0333: lights.  A plan symbol each; the fixture's shape, colour and output
    # are parameters, and ceiling fixtures hang from the room's own ceiling.
    ("light_recessed", "Recessed Light", "Lighting", 6, 6,
     [Ci(3, 3, 2.7, "#ffffff", 0.7), L(1, 3, 5, 3, 0.4), L(3, 1, 3, 5, 0.4)]),
    ("light_flush", "Ceiling Light", "Lighting", 14, 14,
     [Ci(7, 7, 6.5, "#ffffff", 0.8), Ci(7, 7, 4.2, "none", 0.5),
      L(2.4, 2.4, 11.6, 11.6, 0.4), L(11.6, 2.4, 2.4, 11.6, 0.4)]),
    ("light_pendant", "Pendant Light", "Lighting", 12, 12,
     [Ci(6, 6, 5.5, "#ffffff", 0.8), Ci(6, 6, 1.4, FILL, 0.6)]),
    ("light_linear", "Linear Light 4'", "Lighting", 48, 6,
     [R(0.5, 0.5, 47, 5, 1, "#ffffff", 0.8), L(2, 3, 46, 3, 0.4)]),
    ("light_sconce", "Wall Sconce", "Lighting", 6, 5,
     [R(0.4, 0.4, 5.2, 1.0, 0.3, FILL, 0.6),
      Pth("M0.8 1.4 L5.2 1.4 L4.4 4.6 L1.6 4.6 Z", "#ffffff", 0.7)]),
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
     [R(0.75, 0.75, 25.5, 76.5, 4, sw=1.2, top=16),    # the seat
      R(4, 3.5, 19, 9, 2.5, "#ffffff", 0.8, top=30),   # headrest
      L(2, 28, 25, 28, 0.8),                           # backrest hinge
      L(2, 56, 25, 56, 0.6)]),                         # leg hinge
    ("sauna", "Sauna 6'", "Sunroom", 72, 72,
     [R(0.75, 0.75, 70.5, 70.5, 1.5, sw=1.5),
      R(4, 4, 64, 14, 1, "none", 0.7),                 # bench (back)
      R(4, 18, 14, 50, 1, "none", 0.7),                # bench (side)
      R(52, 52, 14, 14, 1, FILL, 1, top=30),           # heater
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
      R(7, 7, 76, 166, 5, "#ffffff", 0.9, top=34),     # water line
      Ci(25, 16, 2.2, "none", 0.8), Ci(45, 16, 2.2, "none", 0.8),
      Ci(65, 16, 2.2, "none", 0.8),                    # swim jets
      L(45, 30, 45, 140, 0.6, "5,4"),                  # swim lane
      R(13, 148, 64, 20, 4, "none", 0.7)]),            # bench seat
    ("whirlpool", "Whirlpool", "Sunroom", 84, 84,
     [R(0.75, 0.75, 82.5, 82.5, 9, sw=1.5),
      Ci(42, 42, 32, "#ffffff", 1, top=30),            # water
      Ci(42, 14.5, 2, "none", 0.7), Ci(42, 69.5, 2, "none", 0.7),
      Ci(14.5, 42, 2, "none", 0.7), Ci(69.5, 42, 2, "none", 0.7),
      Ci(22.5, 22.5, 2, "none", 0.7), Ci(61.5, 61.5, 2, "none", 0.7),
      Ci(42, 42, 2.2, "none", 0.6)]),                  # drain

    ("desk", "Desk 5'", "Office / Storage", 60, 30,
     [R(0.75, 0.75, 58.5, 28.5, 1, sw=1.2), L(2, 4, 58, 4, 0.5)]),
    ("office_chair", "Office Chair", "Office / Storage", 24, 24,
     [R(4, 1, 16, 4, 2, "#ffffff", 0.8, top=40),          # back
      Ci(12, 13, 8.5, FILL, 1, top=19),                   # seat
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
    # 0258 (0248 sec3 plan E): a porch post -- a 6x6 column, drawn in plan as
    # the section every framing plan draws, a square with its diagonals
    ("post", "Post 6x6", "Framing", 6, 6,
     [R(0.5, 0.5, 5, 5, 0, sw=1.0),
      L(0.5, 0.5, 5.5, 5.5, 0.4), L(5.5, 0.5, 0.5, 5.5, 0.4)]),
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
#                 implemented directly; every other form falls back to prism
#                 -- the plan symbol, extruded (handoff 0012/0013) -- except
#                 vehicle and planting, still RESERVED.  vessel and enclosure
#                 (0018) are the two shapes prism's above/below rule can
#                 build: a vessel's internal region may RECESS (a tub's
#                 well); an enclosure's may only stand SOLID on the floor (a
#                 bench, a stove) -- the viewer reports any form it does not
#                 know rather than guessing.
#   material      the BODY's material, a NAME only.  Colour, roughness and
#                 metalness live once, in MATERIALS below, and are written to
#                 materials.json.  Putting three numbers on 95 entries would
#                 rebuild the duplication this table exists to remove.
#   region_material  OPTIONAL 5th element, the material of the item's
#                 internal REGION when it has one and it differs from the
#                 body's (0018 SS6: "materials attach to PARTS, not to
#                 ITEMS").  A vessel's region is its declared contents
#                 (`water`, translucent); an enclosure's is whatever solid
#                 sits inside it (a bench, a stove).  Absent for the 88 rows
#                 with no region, or where the region reasonably shares the
#                 body's material.
#
# LANDSCAPE KINDS ARE ABSENT ON PURPOSE.  tools/make_site_demo.py mints
# `bench`, `planter`, `shrub` and `tree`, which exist in no catalog -- the
# editor cannot place them and the viewer's old table was their only
# definition anywhere.  They are not added here: drawing four new symbols
# would pre-empt P5.2's landscape catalog.  They now render as unknown, which
# is what the editor already thinks of them.
def unpack_solid(row):
    """(height, elevation, form, material, region_material) for one SOLIDS
    row -- `region_material` is `None` when the row is the plain 4-tuple every
    other entry still is.  ONE DEFINITION, so the two consumers (the
    MATERIALS validation above `main()`'s guard, and the manifest writer)
    cannot drift on how they read the same table."""
    if len(row) == 4:
        return (*row, None)
    return row


SOLIDS = {
    # id                      height  elev  form         material  [region_material]
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
    "range_hood":             (18,     66, "box",       "metal"),
    "microwave_otr":          (17,     54, "box",       "metal"),
    # Lights.  The elevation is a NOMINAL 8 ft ceiling less the fixture: the
    # viewer hangs a ceiling light from the ceiling of the room it is in.
    "light_recessed":         (1,      95, "box",       "metal"),
    "light_flush":            (5,      91, "box",       "metal"),
    "light_pendant":          (38,     58, "box",       "metal"),
    "light_linear":           (3,      93, "box",       "metal"),
    "light_sconce":           (10,     66, "box",       "metal"),
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
    # -- Bathroom.  bathtub is a VESSEL (0018): its region is the water
    # surface, a RECESS below the rim -- exactly the shape the above/below
    # rule already gets right, which is why the form split leaves it alone
    # beyond the label.  walk_in_shower is an ENCLOSURE: its bench is a solid
    # standing on the floor, so it gains a region_material of its own (a
    # bench has no material in the OLD one-material-per-item schema, because
    # there was no second slot to put one in).
    "bathtub":                (20,      0, "vessel",    "porcelain", "water"),
    "shower":                 (78,      0, "enclosure", "glass"),
    "walk_in_shower":         (78,      0, "enclosure", "glass",     "stone"),
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
    # sauna is an ENCLOSURE (0018): the stove is a solid standing on the
    # floor, and it gains its own region_material (metal) -- the body stays
    # wood, which was already right.
    "sauna":                  (84,      0, "enclosure", "wood", "metal"),
    "umbrella_table":         (30,      0, "slab",      "wood"),
    # swim_spa and whirlpool are VESSELS (0018): each BODY MATERIAL changes
    # from "water" -- which made the whole tub translucent, surround
    # included, because one column was carrying both "what surrounds the
    # water" and "the water" -- to "porcelain", the surround; the water
    # itself moves to region_material, which is the only slot the geometry
    # actually gives it a shape to sit in.
    "swim_spa":               (40,      0, "vessel",    "porcelain", "water"),
    "whirlpool":              (36,      0, "vessel",    "porcelain", "water"),
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
    # 0258 (plan E): a post is a COLUMN, which the viewer builds from its
    # level to the underside of the roof standing over it; 96 is only what
    # it is drawn at when no roof stands over it.
    "post":                   (96,      0, "column",    "wood"),
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
    # Vehicle parts (0325). A side profile names a material PER PART, so a
    # car is paint, glass, rubber and trim rather than one grey block. The
    # glass is OPAQUE and dark on purpose: translucent glass around an empty
    # cabin would show the far side of the car through the near one (D76).
    "auto_paint":       {"colour": [0.16, 0.30, 0.50, 1.00],
                         "roughness": 0.30, "metalness": 0.55},
    "auto_paint_light": {"colour": [0.74, 0.76, 0.78, 1.00],
                         "roughness": 0.30, "metalness": 0.55},
    "auto_glass":       {"colour": [0.09, 0.12, 0.16, 1.00],
                         "roughness": 0.08, "metalness": 0.40},
    "auto_trim":        {"colour": [0.11, 0.11, 0.12, 1.00],
                         "roughness": 0.70, "metalness": 0.10},
    "rubber":           {"colour": [0.05, 0.05, 0.06, 1.00],
                         "roughness": 0.92, "metalness": 0.00},
    "lamp":             {"colour": [0.96, 0.95, 0.86, 1.00],
                         "roughness": 0.20, "metalness": 0.10},
    "tail_lamp":        {"colour": [0.66, 0.05, 0.05, 1.00],
                         "roughness": 0.25, "metalness": 0.10},
    # Yard machines and the boat (0328): painted sheet metal, and a hull.
    "machine_red":      {"colour": [0.60, 0.09, 0.07, 1.00],
                         "roughness": 0.40, "metalness": 0.30},
    "machine_green":    {"colour": [0.12, 0.34, 0.16, 1.00],
                         "roughness": 0.40, "metalness": 0.30},
    "machine_yellow":   {"colour": [0.86, 0.66, 0.08, 1.00],
                         "roughness": 0.40, "metalness": 0.30},
    "gelcoat":          {"colour": [0.92, 0.93, 0.94, 1.00],
                         "roughness": 0.22, "metalness": 0.05},
    # Loud on purpose, and the ONLY entry a viewer may fall back to: an item
    # whose kind, form or material the catalog does not define must LOOK wrong.
    "unknown":   {"colour": [0.85, 0.35, 0.55, 1.00],
                  "roughness": 0.60, "metalness": 0.00},
}

# ------------------------------------------------------ cabinets and appliances
# 0329.  A cabinet is built from PARTS -- doors, drawers, toe kick, countertop --
# by `floorplanner/parametric/cabinet_geometry.py`, which also owns the style
# vocabulary (finishes, countertops, hardware) and those materials.  It is plain
# Python with no imports of its own, so it is loaded here BY PATH, exactly as
# the viewer loads it: importing the package would drag Qt into an asset build
# that is deliberately Qt-free.  ONE definition; this file only writes it out.
def _load_cabinet_geometry():
    path = (Path(__file__).resolve().parent / "floorplanner" / "parametric"
            / "cabinet_geometry.py")
    name = "_gen_cabinet_geometry"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod            # @dataclass looks its module up
    spec.loader.exec_module(mod)
    return mod


CABINETS = _load_cabinet_geometry()
MATERIALS.update(CABINETS.MATERIALS)

# ------------------------------------------------------- vehicle side profiles
# 0325 (Patrick, 2026-11-14: "I want to change the way that the vehicles are
# rendered so they look like real cars").
#
# WHY A SECOND DRAWING.  The plan symbol is a TOP view, and a top view pushed
# straight up can only ever be a block: a hood, a raked windshield, a wheel
# arch and the gap under the sills exist in the SIDE view and nowhere else.
# So a vehicle may carry a second SVG, `<id>.side.svg` -- its side elevation --
# and the viewer lofts the solid from that instead of extruding the symbol.
#
# THE FORMAT, which is the whole contract with the viewer (`fp3d.py`):
#
#   viewBox        "0 0 LENGTH HEIGHT" in inches.  The NOSE is at x = 0, the
#                  ground is the BOTTOM edge (y = HEIGHT), so a point's height
#                  is HEIGHT - y.  LENGTH and HEIGHT must equal the catalog's
#                  depth_in and height_in -- checked below, refused if not.
#   on <svg>       data-belt / data-roof / data-tumble: above the beltline the
#                  body leans in ("tumblehome") by `tumble` inches a side at
#                  the roof, pro rata between the two heights.
#                  data-round-front / data-round-rear: the plan corner radius
#                  at the nose and the tail -- the top view's rounded ends.
#   each part      a FILLED closed <polygon> or a <circle>, carrying
#                    data-part      what it is -- a name, for a reader
#                    data-material  a MATERIALS name, per PART
#                    data-inset     inches in from the body side (default 0)
#                    data-width     OPTIONAL.  Absent: the part spans the
#                                   vehicle side to side.  Present: it is a
#                                   PAIR, one slab of that thickness at each
#                                   side -- a wheel, a pillar, a lamp.
#                    data-half      OPTIONAL.  The part's outer face as a
#                                   plain distance from the CENTRELINE,
#                                   instead of an inset from the body side:
#                                   a motorcycle's wheel is 2.5 in either
#                                   side of centre whatever the handlebars
#                                   make the footprint.  Not rounded, not
#                                   leaned; never wider than the footprint.
#   data-plan      OPTIONAL, on <svg>: the TOP view's half-width along the
#                  vehicle, as "distance:halfwidth" pairs joined by straight
#                  lines -- a boat's pointed bow, a trailer's A-frame.  A part
#                  placed by data-inset is inset from THIS instead of from
#                  the straight body side.
#
# TWO RULES A PART MUST OBEY.  (1) No `transform`, and polygons not paths: the
# reader takes points as written.  (2) At any distance along the vehicle a part
# is ONE span of height -- the viewer fills between its lowest and highest
# point there.  A shape that needs a hole or an overhang is two parts.
#
# These are generic shapes, authored here -- a mid-size sedan and a mid-size
# SUV -- not a tracing of any real model.
def _smooth(points, rounds=2):
    """Chaikin corner cutting on an OPEN polyline: each round replaces every
    interior corner with two points, so a few control points become a smooth
    line that still starts and ends exactly where it was told to."""
    pts = list(points)
    for _ in range(rounds):
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:], strict=True):
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        out.append(pts[-1])
        pts = out
    return pts


def _arch(cx, cz, r, floor_z, n=14):
    """A wheel arch as seen walking from the TAIL toward the NOSE: the arc of
    radius `r` about the wheel centre, from where it leaves the sill line
    `floor_z` behind the wheel to where it meets it again in front."""
    a = math.asin(max(-1.0, min(1.0, (floor_z - cz) / r)))
    return [(cx + r * math.cos(t), cz + r * math.sin(t))
            for t in (a + (math.pi - 2 * a) * i / n for i in range(n + 1))]


def _lateral(inset, width, half):
    out = f' data-inset="{inset}"' if half is None else f' data-half="{half}"'
    return out + (f' data-width="{width}"' if width is not None else "")


def _side_poly(height, pts, part, material, fill, inset=0.0, width=None,
               half=None):
    """One side-view part as a <polygon>; `pts` are (distance, HEIGHT) pairs,
    flipped here into the SVG's y-down frame."""
    coords = " ".join(f"{x:.2f},{height - z:.2f}" for x, z in pts)
    return (f'<polygon points="{coords}" fill="{fill}" stroke="{INK}" '
            f'stroke-width="0.4" data-part="{part}" data-material="{material}"'
            f'{_lateral(inset, width, half)}/>')


def _side_circle(height, cx, cz, r, part, material, fill, inset=0.0,
                 width=None, half=None):
    return (f'<circle cx="{cx}" cy="{height - cz}" r="{r}" fill="{fill}" '
            f'stroke="{INK}" stroke-width="0.4" data-part="{part}" '
            f'data-material="{material}"{_lateral(inset, width, half)}/>')


_SIDE_FILL = {"rubber": "#111827", "auto_trim": "#1f2937", "metal": "#9ca3af",
              "wood": "#d6b98c", "auto_glass": "#334155", "lamp": "#fef9c3",
              "tail_lamp": "#b91c1c", "machine_red": "#dc2626",
              "machine_green": "#15803d", "machine_yellow": "#eab308",
              "gelcoat": "#f1f5f9", "auto_paint": "#3b82f6",
              "auto_paint_light": "#cbd5e1"}


def _box4(s0, s1, z0, z1):
    """A rectangle in the side view, as the four corners `_machine` takes."""
    return [(s0, z0), (s0, z1), (s1, z1), (s1, z0)]


def _machine(height, rows, **attrs):
    """A side profile written out part by part, for the vehicles that are not
    car-shaped.  Each row is (name, material, shape, lateral): `shape` is a
    list of (distance, height) corners, or ("circle", cx, cz, r); `lateral`
    is a dict of inset / width / half.  The drawing fill is looked up from the
    material, so the side SVG reads as a picture of the thing."""
    parts = []
    for name, material, shape, lateral in rows:
        fill = _SIDE_FILL.get(material, FILL)
        if shape and shape[0] == "circle":
            _tag, cx, cz, r = shape
            parts.append(_side_circle(height, cx, cz, r, name, material, fill,
                                      **lateral))
        else:
            parts.append(_side_poly(height, shape, name, material, fill,
                                    **lateral))
    return {f"data-{k.replace('_', '-')}": v for k, v in attrs.items()}, parts


def _side_profile(*, length, height, paint, wheel_r, wheel_x, sill, arch_r,
                  top, belt, roof, tumble, round_front, round_rear,
                  glass, roof_panel, pillars, lamp_z, grille_z):
    """A car-shaped side profile from a handful of numbers and outlines.

    `top` is the body's upper line, nose to tail, BELOW the windows (hood,
    beltline, deck); `glass` and `roof_panel` are closed outlines; `pillars`
    are closed outlines drawn over the glass.  Heights in inches off the
    ground.  Returns (attrs, [elements]) for `svg_side()`."""
    H = height
    front, rear = wheel_x
    nose, tail = 0.4, length - 0.4         # the lamps stand 0.4 in proud of these
    upper = _smooth(top)
    under = ([(tail, upper[-1][1]), (tail, sill + 4.5), (tail - 7.0, sill)]
             + _arch(rear, wheel_r, arch_r, sill)
             + _arch(front, wheel_r, arch_r, sill)
             + [(nose + 7.0, sill), (nose, sill + 2.5)])
    body = upper + under[1:]
    parts = [
        # the dark core seen through the wheel arches, so they are not tunnels
        _side_poly(H, [(nose + 8, sill + 0.5), (nose + 8, belt - 12),
                       (tail - 8, belt - 12), (tail - 8, sill + 0.5)],
                   "chassis", "auto_trim", "#1f2937", inset=9.5),
        _side_poly(H, body, "body", paint, "#cbd5e1"),
        _side_poly(H, glass, "glass", "auto_glass", "#334155", inset=1.0),
        _side_poly(H, roof_panel, "roof", paint, "#cbd5e1", inset=0.6),
    ]
    for i, ring in enumerate(pillars):
        parts.append(_side_poly(H, ring, f"pillar-{i + 1}", paint, "#cbd5e1",
                                inset=0.7, width=2.6))
    lz0, lz1 = lamp_z
    gz0, gz1 = grille_z
    parts += [
        _side_poly(H, [(0.0, gz0), (0.0, gz1), (1.2, gz1), (1.2, gz0)],
                   "grille", "auto_trim", "#1f2937", inset=17.0),
        _side_poly(H, [(0.0, lz0), (0.0, lz1), (5.0, lz1 + 0.6), (5.0, lz0)],
                   "headlamp", "lamp", "#fef9c3", inset=-0.25, width=13.0),
        _side_poly(H, [(length - 5.0, lz0 + 1), (length - 5.0, lz1 + 2.6),
                       (length, lz1 + 2), (length, lz0 + 1)],
                   "tail-lamp", "tail_lamp", "#b91c1c", inset=-0.25, width=13.0),
        _side_poly(H, [(0.0, sill + 2.5), (0.0, sill + 6.5), (2.2, sill + 6.5),
                       (2.2, sill + 2.5)],
                   "bumper-front", "auto_trim", "#1f2937", inset=3.0),
        _side_poly(H, [(length - 2.2, sill + 4.5), (length - 2.2, sill + 8.5),
                       (length, sill + 8.5), (length, sill + 4.5)],
                   "bumper-rear", "auto_trim", "#1f2937", inset=3.0),
    ]
    for cx in (front, rear):
        parts.append(_side_circle(H, cx, wheel_r, wheel_r, "tyre", "rubber",
                                  "#111827", 0.5, 8.5))
        parts.append(_side_circle(H, cx, wheel_r, round(wheel_r * 0.62, 2), "wheel",
                                  "metal", "#9ca3af", 0.2, 3.0))
    attrs = {"data-belt": belt, "data-roof": roof, "data-tumble": tumble,
             "data-round-front": round_front, "data-round-rear": round_rear}
    return attrs, parts


def svg_side(length, height, attrs, body):
    extra = "".join(f' {k}="{v}"' for k, v in attrs.items())
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {length} {height}" width="{length}" '
            f'height="{height}"{extra}>\n' + "\n".join(body) + "\n</svg>\n")


SIDE_PROFILES = {
    # A three-box sedan: 180 long, 56 high, on a 108 wheelbase.
    "car": {"length": 180, "height": 56, "spec": _side_profile(
        length=180, height=56, paint="auto_paint",
        wheel_r=12.5, wheel_x=(34.0, 142.0), sill=7.5, arch_r=14.5,
        top=[(0.4, 10.0), (0.4, 23.0), (4.0, 27.0), (28.0, 30.5), (54.0, 34.0),
             (100.0, 35.2), (150.0, 36.0), (172.0, 35.2), (179.6, 32.0)],
        belt=35.0, roof=56.0, tumble=6.0, round_front=13.0, round_rear=11.0,
        glass=[(50.0, 33.6), (77.0, 54.4), (129.0, 54.6), (155.0, 35.8)],
        roof_panel=[(74.5, 52.9), (78.5, 56.0), (127.5, 56.0), (132.0, 53.0),
                    (128.5, 54.2), (78.0, 54.0)],
        pillars=[[(50.0, 33.6), (53.4, 33.6), (80.4, 54.4), (77.0, 54.4)],
                 [(100.0, 34.6), (104.0, 34.6), (104.0, 54.5), (100.0, 54.5)],
                 [(151.6, 35.8), (155.0, 35.8), (129.0, 54.6), (125.6, 54.6)]],
        lamp_z=(22.0, 26.5), grille_z=(13.5, 21.0))},
    # A two-box SUV: 192 long, 70 high, taller sills and wheels, an upright tail.
    "suv": {"length": 192, "height": 70, "spec": _side_profile(
        length=192, height=70, paint="auto_paint_light",
        wheel_r=15.0, wheel_x=(37.0, 151.0), sill=10.0, arch_r=17.5,
        top=[(0.4, 13.0), (0.4, 32.0), (4.0, 37.0), (28.0, 40.5), (50.0, 43.5),
             (100.0, 45.0), (176.0, 46.0), (191.6, 44.0)],
        belt=45.0, roof=70.0, tumble=5.0, round_front=11.0, round_rear=9.0,
        glass=[(47.0, 43.2), (70.0, 68.4), (176.0, 68.6), (189.0, 45.4)],
        roof_panel=[(67.5, 66.8), (71.5, 70.0), (175.0, 70.0), (180.0, 66.6),
                    (176.0, 68.2), (71.0, 68.0)],
        pillars=[[(47.0, 43.2), (50.4, 43.2), (73.4, 68.4), (70.0, 68.4)],
                 [(96.0, 44.6), (100.0, 44.6), (100.0, 68.5), (96.0, 68.5)],
                 [(140.0, 45.4), (144.0, 45.4), (144.0, 68.5), (140.0, 68.5)],
                 [(185.4, 45.4), (189.0, 45.4), (176.0, 68.6), (172.4, 68.6)]],
        lamp_z=(31.0, 36.0), grille_z=(18.0, 30.0))},
    # 0328.  The rest of the garage.  None of these is car-shaped, so each is
    # written out part by part; a part on the centreline uses data-half.
    "motorcycle": {"length": 84, "height": 48, "spec": _machine(48, [
        ("tyre-front", "rubber", ("circle", 13.0, 12.5, 12.5), {"half": 2.5}),
        ("tyre-rear", "rubber", ("circle", 70.0, 12.5, 12.5), {"half": 3.0}),
        ("wheel-front", "metal", ("circle", 13.0, 12.5, 8.0), {"half": 2.8}),
        ("wheel-rear", "metal", ("circle", 70.0, 12.5, 8.0), {"half": 3.3}),
        ("fork", "metal", [(11.5, 12.0), (14.5, 12.0), (26.5, 40.0), (23.5, 40.0)],
         {"half": 4.5, "width": 1.6}),
        ("engine", "metal", [(29.0, 7.0), (27.5, 23.0), (53.0, 23.0), (57.0, 8.0)],
         {"half": 6.0}),
        ("frame", "auto_trim", [(26.0, 22.0), (24.5, 31.0), (62.0, 26.0),
                                (70.0, 14.0), (64.0, 12.0), (56.0, 21.0)],
         {"half": 3.5}),
        ("tank", "auto_paint", [(27.0, 25.0), (30.0, 35.0), (45.0, 34.0),
                                (49.0, 27.0)], {"half": 6.5}),
        ("seat", "auto_trim", [(46.0, 27.0), (47.0, 32.0), (69.0, 31.0),
                               (74.0, 28.5), (70.0, 26.0)], {"half": 5.5}),
        ("fender-rear", "auto_paint", [(60.0, 25.5), (62.0, 28.0), (80.0, 27.0),
                                       (83.5, 23.0), (78.0, 24.0)], {"half": 3.4}),
        ("fender-front", "auto_paint", [(3.0, 21.0), (8.0, 26.0), (18.0, 26.0),
                                        (22.0, 22.0), (17.0, 24.0), (8.0, 24.0)],
         {"half": 3.0}),
        ("headlamp", "lamp", _box4(18.5, 23.0, 32.0, 38.0), {"half": 3.5}),
        ("handlebar", "metal", _box4(23.0, 26.5, 40.0, 42.0), {"half": 14.0}),
        ("grip", "rubber", _box4(22.6, 26.9, 39.6, 42.4),
         {"half": 16.0, "width": 4.5}),
        ("mirror", "auto_trim", _box4(21.5, 23.5, 44.0, 48.0),
         {"half": 14.5, "width": 4.0}),
        ("exhaust", "metal", [(46.0, 9.0), (46.0, 12.5), (80.0, 15.5),
                              (80.0, 12.0)], {"half": 9.0, "width": 3.0}),
        ("tail-lamp", "tail_lamp", _box4(81.5, 83.8, 23.5, 26.5), {"half": 2.5}),
    ])},
    "bicycle": {"length": 68, "height": 42, "spec": _machine(42, [
        ("tyre-front", "rubber", ("circle", 13.5, 13.0, 13.0), {"half": 0.9}),
        ("tyre-rear", "rubber", ("circle", 54.5, 13.0, 13.0), {"half": 0.9}),
        ("rim-front", "metal", ("circle", 13.5, 13.0, 11.3), {"half": 1.0}),
        ("rim-rear", "metal", ("circle", 54.5, 13.0, 11.3), {"half": 1.0}),
        ("fork", "auto_paint", [(12.6, 12.5), (14.4, 12.5), (20.2, 31.0),
                                (18.4, 31.0)], {"half": 2.4, "width": 0.9}),
        ("head-tube", "auto_paint", _box4(18.2, 20.2, 28.0, 41.0), {"half": 0.9}),
        ("top-tube", "auto_paint", _box4(19.5, 42.5, 30.2, 31.8), {"half": 0.8}),
        ("down-tube", "auto_paint", [(18.4, 28.0), (20.4, 29.0), (34.6, 11.6),
                                     (32.6, 10.6)], {"half": 0.8}),
        ("seat-tube", "auto_paint", [(41.0, 34.5), (43.0, 34.5), (35.0, 10.5),
                                     (33.0, 10.5)], {"half": 0.8}),
        ("chain-stay", "auto_paint", [(33.0, 10.0), (33.0, 11.8), (54.5, 14.0),
                                      (54.5, 12.2)], {"half": 2.6, "width": 0.8}),
        ("seat-stay", "auto_paint", [(41.6, 30.4), (43.2, 31.2), (55.2, 13.6),
                                     (53.6, 12.8)], {"half": 2.6, "width": 0.8}),
        ("crank", "metal", ("circle", 33.5, 11.0, 3.6), {"half": 1.6}),
        ("pedal", "auto_trim", _box4(31.5, 35.5, 5.5, 6.7),
         {"half": 7.0, "width": 3.6}),
        ("saddle", "auto_trim", [(37.5, 34.6), (37.5, 36.4), (47.0, 37.0),
                                 (48.5, 35.0)], {"half": 2.8}),
        ("handlebar", "metal", _box4(17.6, 20.4, 40.4, 42.0), {"half": 10.0}),
        ("grip", "rubber", _box4(17.3, 20.7, 40.1, 42.0),
         {"half": 11.0, "width": 3.6}),
    ])},
    "lawnmower": {"length": 62, "height": 40, "spec": _machine(40, [
        ("deck", "machine_red", [(1.0, 2.5), (1.0, 8.5), (7.0, 11.0),
                                 (22.0, 11.0), (27.0, 8.0), (27.0, 2.5)],
         {"inset": 1.0}),
        ("engine", "auto_trim", _box4(8.5, 20.5, 11.0, 19.0), {"half": 6.0}),
        ("engine-cap", "metal", _box4(11.0, 18.0, 19.0, 21.0), {"half": 3.5}),
        ("wheel-front", "rubber", ("circle", 7.75, 3.5, 3.5),
         {"inset": 0.4, "width": 3.0}),
        ("wheel-rear", "rubber", ("circle", 21.75, 3.5, 3.5),
         {"inset": 0.4, "width": 3.0}),
        ("handle", "metal", [(26.0, 8.0), (27.6, 8.0), (59.6, 38.2),
                             (58.0, 38.2)], {"half": 6.5, "width": 1.0}),
        ("handle-bar", "auto_trim", _box4(57.6, 60.2, 37.6, 40.0), {"half": 6.5}),
    ])},
    "snowblower": {"length": 58, "height": 42, "spec": _machine(42, [
        ("housing", "machine_red", [(1.0, 1.0), (1.0, 20.0), (8.0, 22.0),
                                    (14.0, 20.0), (14.0, 1.0)], {"inset": 1.0}),
        ("auger", "auto_trim", _box4(0.4, 2.0, 2.0, 17.0), {"inset": 2.5}),
        ("chute", "machine_red", [(6.5, 20.0), (6.5, 36.0), (4.0, 36.5),
                                  (4.0, 40.5), (12.0, 40.5), (11.5, 20.0)],
         {"half": 3.2}),
        ("body", "machine_red", _box4(14.0, 31.0, 5.0, 18.0), {"half": 6.5}),
        ("engine", "auto_trim", _box4(16.0, 29.0, 18.0, 27.0), {"half": 5.5}),
        ("wheel", "rubber", ("circle", 22.5, 6.5, 6.5),
         {"inset": 3.5, "width": 4.0}),
        ("handle", "metal", [(30.0, 18.0), (31.6, 18.0), (55.6, 38.0),
                             (54.0, 38.0)], {"half": 7.5, "width": 1.0}),
        ("panel", "auto_trim", _box4(52.5, 56.5, 36.5, 42.0), {"half": 7.5}),
    ])},
    "garden_tractor": {"length": 120, "height": 50, "spec": _machine(50, [
        ("bucket", "machine_yellow", [(1.0, 2.0), (1.0, 14.0), (9.5, 12.0),
                                      (9.5, 2.0)], {"inset": 2.5}),
        ("loader-arm", "machine_yellow", [(9.0, 6.0), (9.0, 10.5), (42.0, 31.0),
                                          (42.0, 26.5)],
         {"half": 18.0, "width": 4.5}),
        ("chassis", "auto_trim", _box4(38.0, 112.0, 8.0, 14.5), {"half": 11.0}),
        ("hood", "machine_green", [(38.0, 14.0), (38.0, 35.0), (66.0, 36.5),
                                   (68.0, 14.0)], {"half": 14.0}),
        ("grille", "auto_trim", _box4(37.4, 38.6, 17.0, 32.0), {"half": 11.0}),
        ("dash", "auto_trim", [(66.0, 30.0), (66.0, 37.0), (72.0, 36.0),
                               (72.0, 30.0)], {"half": 6.0}),
        ("platform", "machine_green", _box4(68.0, 104.0, 12.0, 22.0),
         {"half": 16.0}),
        ("fender", "machine_green", [(88.0, 22.0), (90.0, 27.5), (115.0, 27.5),
                                     (117.0, 22.0)], {"inset": 0.5, "width": 10.0}),
        ("seat", "auto_trim", [(76.0, 22.0), (76.0, 28.0), (88.0, 28.0),
                               (90.5, 40.0), (93.5, 40.0), (92.5, 22.0)],
         {"half": 8.0}),
        ("rops", "auto_trim", _box4(96.0, 98.5, 22.0, 50.0),
         {"half": 15.0, "width": 2.5}),
        ("rops-top", "auto_trim", _box4(96.0, 98.5, 47.5, 50.0), {"half": 15.0}),
        ("wheel-front", "rubber", ("circle", 50.5, 8.5, 8.5),
         {"inset": 1.0, "width": 7.0}),
        ("wheel-rear", "rubber", ("circle", 102.5, 12.5, 12.5),
         {"inset": 0.5, "width": 9.0}),
        ("hub-front", "machine_yellow", ("circle", 50.5, 8.5, 4.5),
         {"inset": 0.7, "width": 3.0}),
        ("hub-rear", "machine_yellow", ("circle", 102.5, 12.5, 7.0),
         {"inset": 0.2, "width": 3.0}),
        ("hitch", "metal", _box4(112.0, 119.0, 8.0, 13.0), {"half": 6.0}),
    ])},
    "riding_mower_snow": {"length": 96, "height": 46, "spec": _machine(46, [
        ("blower", "machine_red", [(1.0, 1.0), (1.0, 18.0), (13.0, 16.0),
                                   (13.0, 1.0)], {"inset": 2.0}),
        ("auger", "auto_trim", _box4(0.4, 2.0, 2.0, 15.0), {"inset": 3.5}),
        ("chute", "machine_red", [(4.5, 17.0), (4.5, 31.0), (2.5, 31.5),
                                  (2.5, 35.0), (10.5, 35.0), (10.0, 17.0)],
         {"half": 3.2}),
        ("linkage", "metal", _box4(13.0, 18.0, 6.0, 10.0), {"half": 5.0}),
        ("chassis", "auto_trim", _box4(18.0, 86.0, 7.0, 11.0), {"half": 9.0}),
        ("hood", "machine_green", [(18.0, 10.0), (18.0, 29.0), (42.0, 30.5),
                                   (44.0, 10.0)], {"half": 14.0}),
        ("grille", "auto_trim", _box4(17.4, 18.6, 13.0, 26.0), {"half": 10.0}),
        ("column", "auto_trim", [(46.0, 20.0), (46.0, 33.0), (52.0, 35.0),
                                 (52.0, 20.0)], {"half": 4.5}),
        ("body", "machine_green", _box4(44.0, 86.0, 9.0, 20.0), {"half": 12.0}),
        ("seat", "auto_trim", [(56.0, 20.0), (56.0, 25.0), (68.0, 25.0),
                               (70.5, 37.0), (73.5, 37.0), (72.5, 20.0)],
         {"half": 9.0}),
        ("wheel-front", "rubber", ("circle", 31.0, 7.0, 7.0),
         {"inset": 0.5, "width": 6.0}),
        ("wheel-rear", "rubber", ("circle", 75.0, 11.0, 11.0),
         {"inset": 0.0, "width": 8.0}),
        ("hub-front", "machine_yellow", ("circle", 31.0, 7.0, 3.6),
         {"inset": 0.2, "width": 3.0}),
        ("hub-rear", "machine_yellow", ("circle", 75.0, 11.0, 6.0),
         {"inset": -0.3, "width": 3.0}),
    ])},
    # The bow is at distance 0.  `plan` is the hull seen from above; the
    # gunwales are a PAIR following it, so the cockpit between them is open.
    "boat": {"length": 168, "height": 60, "spec": _machine(60, [
        ("hull", "gelcoat", [(2.0, 33.0), (8.0, 20.0), (22.0, 8.0), (48.0, 2.0),
                             (166.0, 1.0), (166.0, 16.0), (60.0, 15.0),
                             (30.0, 21.0)], {"inset": 0.0}),
        ("topsides", "gelcoat", [(2.0, 32.0), (2.0, 36.0), (166.0, 31.0),
                                 (166.0, 14.0), (60.0, 13.0), (30.0, 19.0)],
         {"inset": 0.0, "width": 3.0}),
        ("bow-deck", "gelcoat", [(2.0, 33.5), (2.0, 36.2), (46.0, 35.0),
                                 (46.0, 32.6)], {"inset": 0.4}),
        ("transom", "gelcoat", _box4(163.0, 166.0, 1.5, 31.0), {"inset": 0.4}),
        ("rub-rail", "auto_trim", [(2.0, 35.6), (2.0, 36.6), (166.0, 31.6),
                                   (166.0, 30.6)], {"inset": -0.4, "width": 1.2}),
        ("thwart-1", "wood", _box4(92.0, 100.0, 23.0, 25.0), {"inset": 2.5}),
        ("thwart-2", "wood", _box4(124.0, 132.0, 23.0, 25.0), {"inset": 2.5}),
        ("windshield", "auto_glass", [(58.0, 34.6), (64.0, 47.0), (66.0, 47.0),
                                      (62.0, 34.4)], {"inset": 5.0}),
        ("motor", "auto_trim", [(160.0, 22.0), (160.0, 44.0), (168.0, 43.0),
                                (168.0, 22.0)], {"half": 5.0}),
        ("motor-leg", "metal", _box4(164.5, 168.0, 0.5, 22.0), {"half": 1.8}),
    ], plan="2:0 12:9 28:17 50:24 80:28.5 122:30 150:30 160:27 166:14")},
    # The coupler is at distance 0.  `plan` is the frame from above: the
    # tongue, widening through the A-frame to the two side rails.
    "boat_trailer": {"length": 216, "height": 72, "spec": _machine(72, [
        ("coupler", "auto_trim", _box4(1.0, 8.0, 13.0, 19.5), {"half": 3.5}),
        ("tongue", "metal", _box4(4.0, 66.0, 14.0, 18.0), {"half": 2.0}),
        ("rail", "metal", _box4(8.0, 205.0, 14.0, 18.0),
         {"inset": 0.0, "width": 3.0}),
        ("cross-1", "metal", _box4(74.0, 76.5, 14.5, 17.5), {"inset": 0.0}),
        ("cross-2", "metal", _box4(124.0, 126.5, 14.5, 17.5), {"inset": 0.0}),
        ("cross-3", "metal", _box4(174.0, 176.5, 14.5, 17.5), {"inset": 0.0}),
        ("cross-4", "metal", _box4(203.0, 206.0, 14.0, 18.0), {"inset": 0.0}),
        ("bunk", "wood", _box4(70.0, 200.0, 18.0, 22.0),
         {"half": 16.5, "width": 3.5}),
        ("winch-post", "metal", _box4(28.0, 32.0, 18.0, 40.0), {"half": 2.0}),
        ("winch", "auto_trim", _box4(27.0, 34.0, 34.0, 39.0), {"half": 3.5}),
        ("bow-stop", "rubber", _box4(32.0, 36.0, 39.0, 42.0), {"half": 4.0}),
        ("axle", "metal", _box4(144.0, 148.0, 11.0, 14.5), {"half": 30.0}),
        ("tyre", "rubber", ("circle", 146.0, 13.0, 13.0),
         {"half": 37.0, "width": 8.0}),
        ("wheel", "metal", ("circle", 146.0, 13.0, 7.5),
         {"half": 37.3, "width": 3.0}),
        ("fender", "auto_trim", [(130.0, 23.5), (133.0, 28.5), (159.0, 28.5),
                                 (162.0, 23.5), (158.0, 26.6), (134.0, 26.6)],
         {"half": 38.0, "width": 9.5}),
        ("tail-lamp", "tail_lamp", _box4(206.0, 211.5, 14.5, 19.0),
         {"half": 31.0, "width": 6.5}),
        ("jack", "metal", _box4(40.0, 43.0, 2.0, 22.0), {"half": 6.0, "width": 2.5}),
    ], plan="0:2 8:2 62:27 216:27")},
}

# The generator refuses to write a half-authored catalog.  A missing height is
# the failure this file exists to make impossible: it is the one field with no
# safe default, so a new symbol added without one stops here rather than
# reaching a viewer as a guess.

def main():
    """Write the whole asset tree: furnishing SVGs + manifest/materials/groups,
    tool icons.  BEHIND THE MAIN GUARD (D72) -- everything above this line is
    now safely IMPORTABLE: constants, `svg`/`svg_error`/the drawing primitives,
    and the data tables (`FURNISHINGS`, `SOLIDS`, `MATERIALS`).  `import
    _gen_assets` no longer regenerates the tree as a side effect; only calling
    `main()` (or running the file as a script) does.

    THE RECEIPT IS BYTE-IDENTICAL OUTPUT: this function's body is the same
    statements that used to run at module level, moved and indented, not
    rewritten -- so what it writes is unchanged."""
    ICONS.mkdir(parents=True, exist_ok=True)
    FURN.mkdir(parents=True, exist_ok=True)

    _ids = {fid for fid, *_ in FURNISHINGS}
    _unauthored = sorted(_ids - set(SOLIDS))
    _orphans = sorted(set(SOLIDS) - _ids)
    _all_materials = {m for row in SOLIDS.values()
                      for m in unpack_solid(row)[3:] if m is not None}
    _bad_material = sorted(_all_materials - set(MATERIALS))
    # 0325: a side profile must belong to a furnishing, match its catalog
    # length and height exactly, and name only materials that exist
    _dims = {fid: (d, unpack_solid(SOLIDS[fid])[0])
             for fid, _n, _c, _w, d, _b in FURNISHINGS if fid in SOLIDS}
    _bad_side = []
    for _sid, _sp in SIDE_PROFILES.items():
        if _sid not in _dims:
            _bad_side.append(f"{_sid}: no such furnishing")
            continue
        if (_sp["length"], _sp["height"]) != _dims[_sid]:
            _bad_side.append(f"{_sid}: profile is {_sp['length']} x "
                             f"{_sp['height']}, catalog is {_dims[_sid][0]} x "
                             f"{_dims[_sid][1]}")
        _text = svg_side(_sp["length"], _sp["height"], *_sp["spec"])
        _err = svg_error(_text)
        if _err:
            _bad_side.append(f"{_sid}: malformed side SVG ({_err})")
            continue
        for _el in ET.fromstring(_text):
            _m = _el.get("data-material")
            if _m not in MATERIALS:
                _bad_side.append(f"{_sid}: part {_el.get('data-part')!r} names "
                                 f"material {_m!r}, not in MATERIALS")
            # nothing may be drawn outside the viewBox: the viewer scales the
            # drawing to the catalog size, so a part past the edge would stand
            # outside the footprint the plan shows
            if _el.get("points"):
                _xy = [float(v) for pt in _el.get("points").split()
                       for v in pt.split(",")]
                _xs, _ys = _xy[0::2], _xy[1::2]
            else:
                _r = float(_el.get("r"))
                _xs = [float(_el.get("cx")) - _r, float(_el.get("cx")) + _r]
                _ys = [float(_el.get("cy")) - _r, float(_el.get("cy")) + _r]
            if (min(_xs) < -1e-6 or max(_xs) > _sp["length"] + 1e-6
                    or min(_ys) < -1e-6 or max(_ys) > _sp["height"] + 1e-6):
                _bad_side.append(f"{_sid}: part {_el.get('data-part')!r} is "
                                 f"drawn outside the {_sp['length']} x "
                                 f"{_sp['height']} view")
    # 0329: a cabinet preset must belong to a furnishing and agree with the
    # catalog on width, depth and overall height -- the plan symbol, the box
    # fallback and the parts are three readers of one size
    _full = {fid: (w, d, unpack_solid(SOLIDS[fid])[0], unpack_solid(SOLIDS[fid])[1])
             for fid, _n, _c, w, d, _b in FURNISHINGS if fid in SOLIDS}
    _bad_cab = []
    for _cid, _preset in CABINETS.PRESETS.items():
        if _cid not in _full:
            _bad_cab.append(f"{_cid}: no such furnishing")
            continue
        _st = CABINETS.normalize_state({}, _preset)
        _w, _d, _h, _elev = _full[_cid]
        _top = _st["height_in"] + (_st["top_thickness_in"] if _st["top_on"] else 0.0)
        _at = _st["floor_to_bottom_in"] if CABINETS.is_mounted(_st) else 0.0
        if CABINETS.footprint(_st) != (float(_w), float(_d)):
            _bad_cab.append(f"{_cid}: preset footprint {CABINETS.footprint(_st)}, "
                            f"catalog {_w} x {_d}")
        if _st["type"] == "light":
            continue        # a light's height is its room's ceiling, not a constant
        if abs(_top - _h) > 1e-6 or abs(_at - _elev) > 1e-6:
            _bad_cab.append(f"{_cid}: preset stands {_at} + {_top}, catalog "
                            f"{_elev} + {_h}")
    if _bad_cab:
        raise SystemExit("assets not written -- cabinet preset(s) disagree with "
                         "the catalog:\n"
                         + "".join(f"  {line}\n" for line in _bad_cab))
    if _bad_side:
        raise SystemExit("assets not written -- bad vehicle side profile(s):\n"
                         + "".join(f"  {line}\n" for line in _bad_side))
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
        height, elevation, form, material, region_material = unpack_solid(SOLIDS[fid])
        manifest.append({"id": fid, "name": name, "category": cat,
                         "file": f"{fid}.svg", "width_in": w, "depth_in": d,
                         "height_in": height, "elevation_in": elevation,
                         "form": form, "material": material,
                         "region_material": region_material,
                         # 0325: the side elevation a vehicle is lofted from
                         "side_file": (f"{fid}.side.svg"
                                       if fid in SIDE_PROFILES else None),
                         # 0329: what a cabinet or appliance is born as; the
                         # viewer builds its parts from this plus the item's
                         # own `state` and its room's style
                         "cabinet": CABINETS.PRESETS.get(fid),
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
    for _sid, _sp in SIDE_PROFILES.items():
        (FURN / f"{_sid}.side.svg").write_text(
            svg_side(_sp["length"], _sp["height"], *_sp["spec"]), encoding="utf-8")

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
                     "pantry_18", "pantry_24", "pantry_36", "range_hood",
                     "microwave_otr", "dining_chair"]),
        ("Bedroom", ["bed_king", "bed_queen", "bed_full", "bed_twin",
                     "nightstand", "dresser", "wardrobe", "armchair",
                     "tv_stand", "desk", "office_chair", "bookshelf"]),
        ("Bathroom", ["bathtub", "shower", "walk_in_shower", "glass_shower",
                      "toilet", "vanity", "vanity_24", "vanity_36", "vanity_48"]),
        ("Laundry", ["washer", "dryer"]),
        ("Lighting", ["light_recessed", "light_flush", "light_pendant",
                      "light_linear", "light_sconce"]),
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
        ("Framing", ["stairs", "elevator", "post"]),
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
        "  * `cabinet` — for a cabinet or an appliance, the preset it is born\n"
        "    as (type, width, depth, front ...), or null.  The 3D viewer builds\n"
        "    its doors, drawers, toe kick and countertop from this, the item's\n"
        "    own parameters and its room's style; the vocabulary and the\n"
        "    arithmetic are `floorplanner/parametric/cabinet_geometry.py`.\n"
        "  * `side_file` — for a vehicle, its SIDE ELEVATION (`<id>.side.svg`),\n"
        "    or null.  viewBox `0 0 LENGTH HEIGHT` in inches, nose at x = 0,\n"
        "    ground at the bottom edge.  Each part is a filled `<polygon>` or\n"
        "    `<circle>` with `data-part`, `data-material`, `data-inset` and,\n"
        "    for a part that exists once at each side (a wheel, a pillar),\n"
        "    `data-width`.  The 3D viewer lofts the vehicle from it; the plan\n"
        "    still draws the top-view symbol.  Full contract: `_gen_assets.py`.\n"
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
        "roof": [
            # gable outline, ridge dashed down the middle -- 0139-ruling.md's
            # own 2D convention (ridge heavy, eaves/gable dashed), inverted
            # here since the icon reads better with the OUTLINE bold and the
            # ridge as the accent line
            '<path d="M2.5 15.5 L12 4 L21.5 15.5 Z" fill="none" '
            'stroke="#1f2937" stroke-width="1.8" stroke-linejoin="round"/>',
            '<line x1="12" y1="4" x2="12" y2="15.5" stroke="#1f2937" '
            'stroke-width="1.3" stroke-dasharray="2.3,2"/>'],
        "dormer": [
            # R5b: a small gable standing on a slope -- the host's slope as
            # a grey line, the dormer's gable outline and face above it
            '<line x1="2.5" y1="18.5" x2="21.5" y2="6.5" stroke="#9ca3af" '
            'stroke-width="1.8" stroke-linecap="round"/>',
            '<path d="M8 15.5 L8 10.5 L13 5.5 L18 10.5 L18 9.2" fill="none" '
            'stroke="#1f2937" stroke-width="1.8" stroke-linejoin="round" '
            'stroke-linecap="round"/>'],
        "text": [
            # 0263: the Annotation tool -- a capital T
            '<path d="M5 5 L19 5 L19 8.5 L13.6 8.5 L13.6 19.5 L10.4 19.5 L10.4 8.5 '
            'L5 8.5 Z" fill="#1f2937"/>'],
        "measure": [
            # 0263: the Measure tool -- one thin line with a slash at each end
            '<line x1="3" y1="13" x2="21" y2="13" stroke="#1f2937" stroke-width="1.4"/>',
            '<line x1="1.5" y1="16" x2="6" y2="10" stroke="#1f2937" stroke-width="1.6" '
            'stroke-linecap="round"/>',
            '<line x1="18" y1="16" x2="22.5" y2="10" stroke="#1f2937" stroke-width="1.6" '
            'stroke-linecap="round"/>',
            '<line x1="4" y1="7" x2="4" y2="19" stroke="#9ca3af" stroke-width="1"/>',
            '<line x1="20" y1="7" x2="20" y2="19" stroke="#9ca3af" stroke-width="1"/>'],
        "leader": [
            # 0270: the Leader tool -- an arrow from the lower left up to a
            # shoulder, the text as a grey bar above it
            '<line x1="4.5" y1="18.5" x2="13" y2="9.5" stroke="#1f2937" stroke-width="1.5"/>',
            '<line x1="13" y1="9.5" x2="21" y2="9.5" stroke="#1f2937" stroke-width="1.5"/>',
            '<path d="M2.5 20.5 L8.6 18.6 L4.4 14.4 Z" fill="#1f2937"/>',
            '<line x1="14" y1="6" x2="21" y2="6" stroke="#9ca3af" stroke-width="1.8"/>'],
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



if __name__ == "__main__":
    main()
