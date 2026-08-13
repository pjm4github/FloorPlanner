"""PRISM READ-BACK (handoff 0010, item ONE): how many of the fallback items
have an outline `prism` could actually use?

    python docs/evidence/prism_outline_census.py

The ruling that asks for this:

  > MEASURE FIRST: how many of the 28 fallback items have an outline `prism`
  > could actually use? Not every symbol is a single closed path -- some are
  > line art, some are several disjoint shapes. THAT NUMBER SIZES THE WIN
  > BEFORE ANYTHING IS BUILT.

MEASUREMENT ONLY. Nothing is built here and nothing is decided; the output is a
count and a per-item table.

WHAT "USABLE" MEANS HERE, stated before the number so the number can be argued
with. `prism` extrudes a closed planar outline, so the question is whether the
item's BODY is drawn as a filled closed shape or as strokes. The measure is the
largest filled closed shape as a fraction of the viewBox.

  BODY      a filled shape carries the item's body. A prism extrudes something
            that is recognisably the thing.
  PARTIAL   a real filled body exists, but structure drawn in STROKES is lost
            (a mower's handle, a bicycle's frame). A prism gives the body and
            drops the line art -- still better than a box, and not the whole
            item.
  NONE      no filled shape is a body: only accents (a fender, a light) or
            pure line art. A prism would extrude fragments floating in space,
            which is WORSE than a box.

THE FIRST CUT OF THIS CENSUS USED ONE THRESHOLD AT 25% AND IT WAS WRONG --
recorded because the way it was caught is the reusable part. It reported
`lawnmower` USABLE at 36.7% and `snowblower` TOO SMALL at 20.8%, and those two
symbols are STRUCTURALLY IDENTICAL: a filled body rect, filled wheels, and a
handle drawn in lines. The only difference is how much of each viewBox the
handle takes. **A criterion that splits two symbols of the same kind is
measuring the wrong thing** -- coverage-of-viewBox is a proxy for "is the body
filled", and the proxy fails wherever an item's envelope is mostly empty air.
It was caught by INSPECTING THE ITEMS EITHER SIDE OF THE LINE rather than by
reading the totals, which is the only way a threshold's own error shows up.

**Both thresholds below are still judgement, and every item's number is
printed**, so a different cut can be applied to the same data without re-running
anything.

THE INSTRUMENT'S BOUNDARY, which the ruling depends on:
  * Paths are read for their ANCHOR POINTS. A curve's control points are not
    sampled, so a rounded shape's area is slightly understated -- it makes
    coverage a LOWER bound, which is the safe direction for a "can we use it"
    question.
  * `transform` attributes are not applied. Every generated symbol is authored
    in viewBox units (see `_gen_assets.py`), and the census REPORTS any
    transform it meets rather than silently mis-measuring it.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

SVG_NS = "{http://www.w3.org/2000/svg}"

# from floorplanner/viewer/fp3d.py -- imported rather than restated so this
# census cannot drift from the viewer's own idea of what is built
sys.path.insert(0, str(ROOT / "floorplanner" / "viewer"))

BODY_MIN = 0.50       # a filled shape this big IS the body
PARTIAL_MIN = 0.10    # below this, the filled shapes are accents, not a body


def _known_and_built():
    """(KNOWN_FORMS, BUILT_FORMS) read from the viewer's source.

    Read as TEXT rather than imported: fp3d is Qt-free by design and importing
    the package would drag in the bindings (D73). The tuples are literals, so a
    parse is exact."""
    src = (ROOT / "floorplanner" / "viewer" / "fp3d.py").read_text("utf-8")
    out = []
    for name in ("KNOWN_FORMS", "BUILT_FORMS"):
        m = re.search(rf"^{name} = \((.*?)\)", src, re.S | re.M)
        out.append(tuple(re.findall(r'"([a-z_]+)"', m.group(1))))
    return out


def _num(s):
    return [float(v) for v in re.findall(r"-?\d*\.?\d+(?:e-?\d+)?", s)]


def _poly_area(pts):
    if len(pts) < 3:
        return 0.0
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


def _path_shapes(d):
    """Closed subpaths of a path's `d`, as anchor-point polygons.

    Only a subpath ending in Z counts: an unclosed subpath is a stroke, and a
    prism cannot extrude a stroke."""
    tokens = re.findall(r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)",
                        d)
    shapes, cur, pos, start = [], [], (0.0, 0.0), (0.0, 0.0)
    for cmd, args in tokens:
        n = _num(args)
        rel = cmd.islower()
        up = cmd.upper()
        if up == "Z":
            if len(cur) >= 3:
                shapes.append(cur)
            cur, pos = [], start
            continue
        if up == "M":
            for i in range(0, len(n) - 1, 2):
                p = ((pos[0] + n[i], pos[1] + n[i + 1]) if rel
                     else (n[i], n[i + 1]))
                if i == 0:
                    if len(cur) >= 3:
                        shapes.append(cur)
                    cur, start = [p], p
                else:
                    cur.append(p)
                pos = p
        elif up in ("L", "T"):
            for i in range(0, len(n) - 1, 2):
                pos = ((pos[0] + n[i], pos[1] + n[i + 1]) if rel
                       else (n[i], n[i + 1]))
                cur.append(pos)
        elif up == "H":
            for v in n:
                pos = (pos[0] + v if rel else v, pos[1])
                cur.append(pos)
        elif up == "V":
            for v in n:
                pos = (pos[0], pos[1] + v if rel else v)
                cur.append(pos)
        elif up in ("C", "S", "Q", "A"):
            # ANCHOR ONLY -- the endpoint of each segment, control points
            # ignored. Understates a curved area, which is the safe direction.
            step = {"C": 6, "S": 4, "Q": 4, "A": 7}[up]
            for i in range(0, len(n) - step + 1, step):
                ex, ey = n[i + step - 2], n[i + step - 1]
                pos = (pos[0] + ex, pos[1] + ey) if rel else (ex, ey)
                cur.append(pos)
    if len(cur) >= 3:
        shapes.append(cur)
    return shapes


def _filled(el):
    """A shape counts only if it is FILLED. `fill="none"` is line art."""
    fill = (el.get("fill") or "").strip().lower()
    style = (el.get("style") or "").lower()
    if fill == "none" or "fill:none" in style.replace(" ", ""):
        return False
    return True


def measure(path):
    """(best_area, viewbox_area, kinds, transforms) for one SVG."""
    root = ET.parse(path).getroot()
    vb = _num(root.get("viewBox") or "0 0 1 1")
    vb_area = abs(vb[2] * vb[3]) if len(vb) >= 4 else 0.0
    best, kinds, xf = 0.0, set(), 0
    for el in root.iter():
        tag = el.tag.replace(SVG_NS, "")
        if tag in ("svg", "g", "title", "desc", "defs"):
            if el.get("transform"):
                xf += 1
            continue
        kinds.add(tag)
        if el.get("transform"):
            xf += 1
        if not _filled(el):
            continue
        area = 0.0
        if tag == "rect":
            area = abs(float(el.get("width", 0)) * float(el.get("height", 0)))
        elif tag == "circle":
            r = float(el.get("r", 0))
            area = 3.141592653589793 * r * r
        elif tag == "ellipse":
            area = (3.141592653589793 * float(el.get("rx", 0))
                    * float(el.get("ry", 0)))
        elif tag in ("polygon", "polyline"):
            pts = _num(el.get("points", ""))
            area = _poly_area(list(zip(pts[0::2], pts[1::2], strict=False)))
        elif tag == "path":
            shapes = _path_shapes(el.get("d", ""))
            area = max((_poly_area(s) for s in shapes), default=0.0)
        best = max(best, area)
    return best, vb_area, kinds, xf


def main():
    known, built = _known_and_built()
    pending = tuple(f for f in known if f not in built)
    manifest = json.loads(
        (ROOT / "assets" / "furnishings" / "manifest.json").read_text("utf-8"))
    items = manifest["items"] if isinstance(manifest, dict) else manifest

    print(f"KNOWN_FORMS  {known}")
    print(f"BUILT_FORMS  {built}")
    print(f"PENDING      {pending}")
    print(f"catalog      {len(items)} items")

    rows, per_form = [], {}
    for it in items:
        form = it.get("form") or "box"
        if form not in pending:
            continue
        svg = ROOT / "assets" / "furnishings" / it["file"]
        if not svg.exists():
            rows.append((it["id"], form, -1.0, "MISSING SVG", 0))
            continue
        try:
            best, vb, kinds, xf = measure(svg)
        except Exception as ex:                        # noqa: BLE001
            rows.append((it["id"], form, -1.0, f"UNPARSEABLE {ex}", 0))
            continue
        cov = (best / vb) if vb else 0.0
        if cov >= BODY_MIN:
            verdict = "BODY"
        elif cov >= PARTIAL_MIN:
            verdict = "PARTIAL"
        else:
            verdict = "NONE"
        rows.append((it["id"], form, cov, verdict, xf))
        per_form.setdefault(form, []).append(verdict)

    print(f"\nfallback items (form recognised, generator not built): {len(rows)}")
    print(f"BODY >= {BODY_MIN:.0%} of viewBox; PARTIAL >= {PARTIAL_MIN:.0%}; "
          f"below that NONE\n")
    print(f"{'kind':28s} {'form':10s} {'coverage':>9s}  verdict")
    print("-" * 68)
    for kind, form, cov, verdict, xf in sorted(rows, key=lambda r: (r[1], r[0])):
        c = "  n/a" if cov < 0 else f"{cov:8.1%}"
        note = "  (has transform)" if xf else ""
        print(f"{kind:28s} {form:10s} {c}  {verdict}{note}")

    print("\nBY FORM        body partial none")
    for form in sorted(per_form):
        vs = per_form[form]
        print(f"  {form:10s} {vs.count('BODY'):4d} {vs.count('PARTIAL'):7d} "
              f"{vs.count('NONE'):4d}")

    body = sum(1 for r in rows if r[3] == "BODY")
    partial = sum(1 for r in rows if r[3] == "PARTIAL")
    none = sum(1 for r in rows if r[3] == "NONE")
    print(f"\nTHE NUMBER: of {len(rows)} fallback items, {body} have a filled "
          f"BODY prism can extrude,\n{' ' * 12}{partial} give a PARTIAL solid "
          f"(body kept, line-drawn structure lost),\n{' ' * 12}and {none} have "
          f"NONE -- prism would be worse than the box.")


if __name__ == "__main__":
    main()
