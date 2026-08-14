"""Build `fixtures/prism-check.json` -- the plan for prism's AMBER check.

    python fixtures/prism-check.json.py

ONE OF EVERY AFFECTED KIND, laid out in a room, grouped by form so a whole form
can be judged together rather than item by item. The 28 items prism changes are
the only furnishings in it, plus walls and a floor so the scene reads as a room
and not as objects in a void.

Kept as a builder rather than as hand-written JSON because the 28 come from the
catalog: if the catalog changes, the plan should change with it rather than
quietly test a stale set.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FURN = ROOT / "assets" / "furnishings"
OUT = ROOT / "fixtures" / "prism-check.json"

BUILT_BEFORE = ("box", "slab")          # what already had a generator
COL_PITCH, ROW_PITCH, MARGIN = 130.0, 150.0, 60.0
PER_ROW = 6


def main():
    manifest = json.loads((FURN / "manifest.json").read_text("utf-8"))
    affected = [it for it in manifest
                if (it.get("form") or "box") not in BUILT_BEFORE]
    affected.sort(key=lambda it: (it["form"], it["id"]))

    furn, x, y, col, form = [], MARGIN, MARGIN, 0, None
    for it in affected:
        if form is not None and it["form"] != form:   # new form -> new row
            col, y = 0, y + ROW_PITCH
        elif col >= PER_ROW:
            col, y = 0, y + ROW_PITCH
        form = it["form"]
        x = MARGIN + col * COL_PITCH
        furn.append({"id": f"f_{it['id']}", "level": "L0", "kind": it["id"],
                     "pos": [x, y], "rotation": 0.0})
        col += 1

    w = MARGIN * 2 + PER_ROW * COL_PITCH
    h = y + ROW_PITCH
    corners = [(0.0, 0.0), (w, 0.0), (w, h), (0.0, h)]
    verts = [{"id": f"v{i}", "x": p[0], "y": p[1]}
             for i, p in enumerate(corners)]
    walls = [{"id": f"w{i}", "level": "L0", "type": "exterior",
              "v1": f"v{i}", "v2": f"v{(i + 1) % 4}", "openings": []}
             for i in range(4)]

    doc = {
        "format": "floorplanner-design", "version": 5,
        "schema_revision": 1,
        "levels": [{"id": "L0", "name": "default", "elevation_in": 0.0,
                    "height_in": 96.0}],
        "vertices": verts,
        "walls": walls,
        "rooms": [{"id": "r0", "level": "L0", "name": "Prism check",
                   "category": "other",
                   "outline": [{"v": f"v{i}"} for i in range(4)]}],
        "furnishings": furn,
    }
    OUT.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"wrote {OUT}  ({len(furn)} furnishings, {len(affected)} affected "
          f"kinds, room {w:.0f}x{h:.0f}\")")
    per = {}
    for it in affected:
        per.setdefault(it["form"], []).append(it["id"])
    for f in sorted(per):
        print(f"  row(s) for {f:10s} {len(per[f]):2d}: {', '.join(per[f])}")


if __name__ == "__main__":
    main()
