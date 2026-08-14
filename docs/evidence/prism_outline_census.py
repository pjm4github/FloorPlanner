"""PRISM READ-BACK (handoff 0010, item ONE): how many of the fallback items
have an outline `prism` could actually use?

    python docs/evidence/prism_outline_census.py

The ruling that asks for this:

  > MEASURE FIRST: how many of the 28 fallback items have an outline `prism`
  > could actually use? Not every symbol is a single closed path -- some are
  > line art, some are several disjoint shapes. THAT NUMBER SIZES THE WIN
  > BEFORE ANYTHING IS BUILT.

**SUPERSEDED AS A PREDICTION, 2026-08-13 — prism is built, and the receipt is
now `prism_remeasure.py`, which reads the answer off `build_model` itself.**
This file is kept because the pre-build measurement is what the ruling was made
on, and because its own error is recorded in the working agreement. Its parser
has been REPLACED by a call to the viewer's `svg_outlines`, so it can no longer
disagree with what the viewer actually reads.

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
  * `transform` attributes are not applied -- and `svg_outlines` REFUSES a
    file carrying one rather than mis-placing it, so such an item reads as
    NONE and falls back to a box. No generated symbol carries one.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

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


def _fp3d():
    """The VIEWER's module, loaded by path.

    THE PARSER IS NO LONGER THIS FILE'S. `svg_outlines` is production code in
    fp3d.py, so this census measures what the viewer will actually read rather
    than a second implementation that agrees with it today. Loaded by path
    because fp3d is deliberately Qt-free and importing the package would drag
    in the bindings (D73).
    """
    spec = importlib.util.spec_from_file_location(
        "fp3d_census", ROOT / "floorplanner" / "viewer" / "fp3d.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def measure(fp3d, path):
    """(best_ring_area, viewbox_area) for one SVG, via the viewer's reader."""
    parts, (vw, vh) = fp3d.svg_outlines(str(path))
    best = max((fp3d._ring_area(p.ring) for p in parts
                if not p.nested), default=0.0)
    return best, (vw * vh)


def main():
    fp3d = _fp3d()
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
            best, vb = measure(fp3d, svg)
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
        rows.append((it["id"], form, cov, verdict, 0))
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
