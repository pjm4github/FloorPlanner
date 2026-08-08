#!/usr/bin/env python3
"""D49's amendment demands the report name the OVERLAP AREA. This measures what
that number would be on the amendment's own driving case.

    python docs/evidence/d49_overlap_area_probe.py > docs/evidence/d49-farmplace-overlap-area.json

Why it exists: the amendment (2026-08-07) names
`examples/farmplaceBIGmultifloor.json` -- Lounge and Toi -- as the case that
moves D49 "from a reasoned hole to a hole that bit", and requires a report that
answers the author's question, *why?*. D52 has already measured that this pair
does not overlap: Toi is a WC fully ENCLOSED by Lounge, and I11 fires only
because its centroid is a VERTEX AVERAGE that lands in the zero-width slit the
drawing uses to carve the closet out.

So the number the amended report would print on its own driving case is worth
having as a measurement rather than as an inference. This computes it three
ways that do not depend on I11's predicate:

  * each ring's shoelace area -- Lounge's slit ring should already be
    net of the closet, which is the drawing saying what it means;
  * the true polygon INTERSECTION area (Qt's `QPolygonF.intersected`);
  * I11's three terms, so the misfiring one is visible beside the truth.

WHAT THIS DOES NOT ANSWER: whether D49's boundary check is worth building. It
is -- planc1's 591 sf master bath is a real overlap and is why I11 exists. This
probe is only about whether THIS FILE can serve as the acceptance case.
"""
import json
import os
import pathlib
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPointF                       # noqa: E402
from PyQt6.QtGui import QPolygonF                      # noqa: E402
from PyQt6.QtWidgets import QApplication               # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PLAN = ROOT / "examples" / "farmplaceBIGmultifloor.json"
PAIR = ("Lounge", "Toi")


def shoelace(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def main():
    QApplication([])                                   # QPolygonF needs no GUI,
    sys.path.insert(0, str(ROOT))                      # but the import does
    from floorplanner.design.validate import _pip, _seg_cross, check

    doc = json.loads(PLAN.read_text(encoding="utf-8"))
    verts = {v["id"]: (v["x"], v["y"]) for v in doc["vertices"]}
    rooms = {r["name"]: r for r in doc["rooms"]}
    a, b = (rooms[n] for n in PAIR)

    def ring(r):
        return [verts[e["v"]] for e in r["outline"]]

    pa, pb = ring(a), ring(b)
    ca = (sum(p[0] for p in pa) / len(pa), sum(p[1] for p in pa) / len(pa))
    cb = (sum(p[0] for p in pb) / len(pb), sum(p[1] for p in pb) / len(pb))

    inter = QPolygonF([QPointF(*p) for p in pa]).intersected(
            QPolygonF([QPointF(*p) for p in pb]))
    ipts = [(p.x(), p.y()) for p in inter]

    out = {
        "plan": PLAN.name,
        "pair": list(PAIR),
        "rings": {
            PAIR[0]: {"points": len(pa), "area_sqft": round(shoelace(pa) / 144, 1)},
            PAIR[1]: {"points": len(pb), "area_sqft": round(shoelace(pb) / 144, 1)},
        },
        "true_intersection": {
            "points": len(ipts),
            "area_sqft": round(shoelace(ipts) / 144, 3) if ipts else 0.0,
        },
        "i11_terms": {
            "pip_b_centre_in_a": _pip(cb, pa),
            "pip_a_centre_in_b": _pip(ca, pb),
            "edge_crossings": sum(
                1
                for i in range(len(pa))
                for j in range(len(pb))
                if _seg_cross(pa[i], pa[(i + 1) % len(pa)],
                              pb[j], pb[(j + 1) % len(pb)])
            ),
        },
        "i11_reports": [e for e in check(doc, deep=True) if e.startswith("I11")],
        "check_cheap": check(doc, deep=False),
    }
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
