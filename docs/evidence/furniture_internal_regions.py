"""DO THE FURNITURE SYMBOLS CONTAIN INTERNAL CLOSED PATHS, OR ONLY STROKES?

    python docs/evidence/furniture_internal_regions.py

Patrick's question, 2026-08-13, and the one fact the reserved decision turns on:

  > A sofa's back panel drawn as a CLOSED RECTANGLE is a different world from
  > the same panel drawn as THREE LINES.
  >
  >   if CLOSED PATHS exist, the cheap answer is available: extrude each
  >   internal region to its own height, from artwork already on disk, with a
  >   per-region height rule that is DATA rather than one function per kind.
  >   if only STROKES, the cheap answer is shut and the bespoke-generator
  >   question returns for real.

MEASUREMENT ONLY. Nothing is built and nothing is decided.

SCOPE: the 18 items whose form is `seat`, `bed`, `basin` or `enclosure`. The
ruling says 17 -- that is the 17 which EXTRUDE; `glass_shower` has no closed
shape at all and falls back to a box. All 18 are reported, with `glass_shower`
visible as the one that differs, because dropping it would hide the only item
whose answer is already known.

CLOSEDNESS IS THE CRITERION, NOT FILL. A region can be extruded whether or not
it is painted: `<rect fill="none">` is still a rectangle with an inside. So each
closed shape is reported by fill as well, since a `fill="none"` internal region
is a drafting line that HAPPENS to close, and whether that counts as a region is
a judgement rather than a measurement.

WHAT COUNTS AS CLOSED
  rect, circle, ellipse, polygon   closed by definition
  path                             only a subpath ending in Z
  line, polyline                   never -- these are the strokes

A CLOSED SHAPE BEYOND THE OUTER OUTLINE IS COUNTED WHEREVER IT SITS, and is
then classified:

  NESTED    its centroid lies inside the outer outline -- a tub's well, a bed's
            pillow, a sink's bowl. Extruding it to its own height carves or
            raises a region OF the body.
  BESIDE    it does not -- a dining chair's back panel is a separate rectangle
            ADJACENT to its seat, not inside it. Still a closed region with its
            own height; it simply is not a hole in anything.

**THE FIRST CUT OF THIS CENSUS COUNTED ONLY NESTED SHAPES AND REPORTED
`dining_chair` AS HAVING NONE.** It has a back panel drawn as a closed
rectangle -- exactly the case the question is about -- sitting beside the seat
rather than within it. Caught by READING THE FOUR FILES rather than by trusting
the parse, which is the standing rule here and the third time on this feature
that looking has overturned counting.

THE PARSER IS THE VIEWER'S. Ring extraction comes from `fp3d._path_rings` and
the element walk mirrors `fp3d.svg_outlines`, so this cannot report a shape the
extruder would not see. The one deliberate difference is that `svg_outlines`
DROPS nested rings -- they would z-fight at a single height -- and this census
is precisely about what it drops.
"""
import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FURN = ROOT / "assets" / "furnishings"
FORMS = ("seat", "bed", "basin", "enclosure")
SVG_NS = "{http://www.w3.org/2000/svg}"
CLOSED_TAGS = ("rect", "circle", "ellipse", "polygon")
OPEN_TAGS = ("line", "polyline")


def load_fp3d():
    spec = importlib.util.spec_from_file_location(
        "fp3d_regions", ROOT / "floorplanner" / "viewer" / "fp3d.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def shapes(fp3d, path):
    """[(ring, filled, tag)] for every CLOSED shape, plus the stroke count."""
    root = ET.parse(path).getroot()
    out, strokes = [], 0
    for el in root.iter():
        tag = el.tag.replace(SVG_NS, "")
        if tag in ("svg", "g", "defs", "title", "desc"):
            continue
        filled = fp3d._is_filled(el)
        if tag in OPEN_TAGS:
            strokes += 1
        elif tag == "rect":
            x, y = float(el.get("x", 0)), float(el.get("y", 0))
            w, h = float(el.get("width", 0)), float(el.get("height", 0))
            if w > 0 and h > 0:
                out.append(([(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
                            filled, tag))
        elif tag in ("circle", "ellipse"):
            rx = float(el.get("rx", el.get("r", 0)))
            ry = float(el.get("ry", el.get("r", 0)))
            if rx > 0 and ry > 0:
                out.append((fp3d._ellipse_ring(float(el.get("cx", 0)),
                                               float(el.get("cy", 0)), rx, ry),
                            filled, tag))
        elif tag == "polygon":
            p = fp3d._nums(el.get("points", ""))
            if len(p) >= 6:
                out.append((list(zip(p[0::2], p[1::2], strict=False)),
                            filled, tag))
        elif tag == "path":
            rings = fp3d._path_rings(el.get("d", ""))
            for r in rings:
                out.append((r, filled, tag))
            if not rings:
                strokes += 1              # a path that never closes IS a stroke
    return out, strokes


def simplify(ring, tol=1e-6):
    """Drop repeated points and points collinear with their neighbours.

    A 4-VERTEX OUTLINE IS A BOX BY DEFINITION, and that is the number this
    exists to produce honestly: an unsimplified ring can carry duplicate or
    collinear points that flatter it."""
    pts = []
    for p in ring:
        if not pts or abs(p[0] - pts[-1][0]) > tol or abs(p[1] - pts[-1][1]) > tol:
            pts.append(p)
    if len(pts) > 1 and abs(pts[0][0] - pts[-1][0]) <= tol \
            and abs(pts[0][1] - pts[-1][1]) <= tol:
        pts.pop()
    keep, n = [], len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        cross = ((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        if abs(cross) > 1e-9:
            keep.append(b)
    return keep or pts


def main():
    fp3d = load_fp3d()
    manifest = json.loads((FURN / "manifest.json").read_text("utf-8"))
    items = [i for i in manifest if (i.get("form") or "box") in FORMS]
    items.sort(key=lambda i: (i["form"], i["id"]))

    print(f"{len(items)} items in forms {FORMS}\n")
    print(f"{'kind':18s} {'form':10s} {'outer v':>7s} {'nested':>6s} "
          f"{'beside':>6s} {'strokes':>7s}   closed shapes beyond the outline")
    print("-" * 96)
    rows = []
    for it in items:
        sh, strokes = shapes(fp3d, FURN / it["file"])
        if not sh:
            rows.append((it["id"], it["form"], 0, [], [], strokes))
            print(f"{it['id']:18s} {it['form']:10s} {'-':>7s} {'-':>6s} "
                  f"{'-':>6s} {strokes:7d}   NO CLOSED SHAPE AT ALL")
            continue
        sh.sort(key=lambda s: fp3d._ring_area(s[0]), reverse=True)
        outer = sh[0]
        nested, beside = [], []
        for ring, filled, tag in sh[1:]:
            c = (sum(p[0] for p in ring) / len(ring),
                 sum(p[1] for p in ring) / len(ring))
            (nested if fp3d._pip(c, outer[0]) else beside).append((tag, filled))
        v = len(simplify(outer[0]))
        rows.append((it["id"], it["form"], v, nested, beside, strokes))

        def desc(lst):
            return ", ".join(f"{t}{'' if f else '(unfilled)'}"
                             for t, f in lst) or "-"
        print(f"{it['id']:18s} {it['form']:10s} {v:7d} {len(nested):6d} "
              f"{len(beside):6d} {strokes:7d}   "
              f"nested: {desc(nested)} | beside: {desc(beside)}")

    print("\nCOLUMNS")
    print("  outer v   vertices of the OUTER OUTLINE after simplification.")
    print("            4 = a rectangle. A 4-VERTEX PRISM IS A BOX.")
    print("  nested    closed shapes whose centroid is inside the outline")
    print("  beside    closed shapes elsewhere (a chair back beside its seat)")
    print("  strokes   line / polyline / never-closed path -- NOT extrudable")

    print("\nTHE TWO ANSWERS\n")
    boxes = [r for r in rows if r[2] == 4]
    print(f"1. OUTER OUTLINE IS A PLAIN RECTANGLE for {len(boxes)} of "
          f"{len(rows)} items:")
    print("   " + ", ".join(r[0] for r in boxes))
    other = [r for r in rows if r[2] != 4]
    for r in other:
        print(f"   NOT a rectangle: {r[0]} ({r[2]} vertices)")

    have = [r for r in rows if r[3] or r[4]]
    none = [r for r in rows if not (r[3] or r[4])]
    print(f"\n2. CLOSED SHAPES BEYOND THE OUTLINE exist for {len(have)} of "
          f"{len(rows)}:")
    for kind, _f, _v, nested, beside, _s in have:
        print(f"   {kind:18s} {len(nested)} nested, {len(beside)} beside")
    print(f"\n   NONE AT ALL -- detail is strokes only -- for {len(none)}:")
    for kind, _f, _v, _n, _b, s in none:
        print(f"   {kind:18s} {s} stroke element(s)")

    # THE COST, counted rather than estimated: if each extrudable region needs
    # a height stated beside the artwork, how many statements is that?
    filled_regions = sum(sum(1 for _t, f in n + b if f)
                         for _k, _fm, _v, n, b, _s in rows)
    all_regions = sum(len(n) + len(b) for _k, _fm, _v, n, b, _s in rows)
    items_with_filled = sum(1 for _k, _fm, _v, n, b, _s in rows
                            if any(f for _t, f in n + b))
    print("\n3. THE ANNOTATION COST, counted")
    print(f"   closed shapes beyond the outline, all:     {all_regions}")
    print(f"   ...of which FILLED (a region, not a mark): {filled_regions}")
    print(f"   items carrying at least one filled region: {items_with_filled} "
          f"of {len(rows)}")
    print("   The unfilled remainder are drains, jets and door swings -- marks,")
    print("   not regions. Whether they earn a height is a judgement, and the")
    print("   two counts are given separately so it stays one.")


if __name__ == "__main__":
    main()
