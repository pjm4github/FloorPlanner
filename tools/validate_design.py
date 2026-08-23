#!/usr/bin/env python3
"""Validate a v5 design document against the JSON Schema AND the referential
invariants JSON Schema cannot express.

The logic now lives in floorplanner.design.validate (vendored at P0.7); this is
a thin CLI over it.  The schema defaults to the packaged one, so:

    python tools/validate_design.py design.json          # packaged schema
    python tools/validate_design.py design.json other-schema.json
"""
import json
import sys
from pathlib import Path

# run from anywhere: put the repo root on the path so `floorplanner` imports
# (the package is not pip-installed; tests reach it via conftest, the CLI here)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from floorplanner.design.validate import (  # noqa: E402  (after sys.path setup)
    ORTHOGONALITY_BANDS, check, load_schema, orthogonality_bands, report,
    schema_errors, wall_orthogonality,
)


def main(argv):
    doc = json.load(open(argv[1]))
    schema = json.load(open(argv[2])) if len(argv) > 2 else load_schema()

    serr = schema_errors(doc, schema)
    print(f"JSON Schema : {'PASS' if not serr else str(len(serr)) + ' ERRORS'}")
    for e in serr[:8]:
        print("   ", e[:160])

    ierr = check(doc)
    print(f"Invariants  : {'PASS' if not ierr else str(len(ierr)) + ' ERRORS'}")
    for e in ierr[:20]:
        print("   ", e)

    print(f"\nlevels={len(doc['levels'])} vertices={len(doc['vertices'])} "
          f"walls={len(doc['walls'])} rooms={len(doc['rooms'])} "
          f"furnishings={len(doc.get('furnishings', []))} "
          f"openings={sum(len(w.get('openings', [])) for w in doc['walls'])}")
    print(f"\n  {'room':<16}{'area sf':>9}{'perim ft':>10}{'edges':>7}{'open':>6}"
          f"  {'state':<9}{'accounting'}")
    roll = {}
    for nm, ar, pe, ne, op, st, acc in sorted(report(doc)):
        print(f"  {nm:<16}{ar:>9.1f}{pe:>10.1f}{ne:>7}{op:>6}  {st:<9}{acc}")
        roll[acc] = roll.get(acc, 0.0) + ar
    for k in ("conditioned", "unconditioned", "site", "excluded"):
        if k in roll:
            print(f"  {'TOTAL ' + k:<16}{roll[k]:>9.1f}")
    sh = sum(1 for w in doc["walls"] if w.get("left") and w.get("right"))
    one = sum(1 for w in doc["walls"] if bool(w.get("left")) != bool(w.get("right")))
    print(f"\nwalls shared by two rooms {sh} | bounding one room {one} | "
          f"free {len(doc['walls']) - sh - one}")

    # 0055-ruling.md item B: a REPORT, not a repair -- names how many walls
    # sit off axis and by how much; fixes nothing, snaps nothing.
    orows = wall_orthogonality(doc)
    obands = orthogonality_bands(orows)
    print("\northogonality (deviation from the nearest axis-aligned angle):")
    label_w = max(len(lbl) for _lo, _hi, lbl in ORTHOGONALITY_BANDS) + 2
    for _lo, _hi, label in ORTHOGONALITY_BANDS:
        print(f"  {label:<{label_w}}{obands[label]}")
    worst = [r for r in orows if r[3] > 0.01][:8]
    if worst:
        print("  worst offenders (wall, level, type, deg, would-move-in):")
        for wid, lvl, typ, deg, disp in worst:
            print(f"    {wid:<6}{lvl:<6}{typ:<12}{deg:<10.4f}{disp:.4f}")

    return 1 if (serr or ierr) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
