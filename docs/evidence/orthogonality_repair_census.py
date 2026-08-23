#!/usr/bin/env python3
"""0082-ruling.md sec3: "'61 of 63' is provisional and must not be restated
as a property of the repair." This is that number, actually run, corpus-wide,
against the built `repair_wall_orthogonality` (0066-ruling.md item C, as
amended by 0082-ruling.md secs 2-4) -- rather than trusted from the two
per-file read-back examples (`farmplaceBIGmultifloor.json`,
`wiscaway2026-08-09R.json`) either ruling actually walked.

Walks the same file set `orthogonality_census.py` does (`examples/` +
`fixtures/`, recursively -- INCLUDING `fixtures/crossfloor-snap-2026-08-17.json`,
promoted out of `fixtures/incoming/` per [0061-ruling.md](../handoff/0061-ruling.md)
sec6 as a measurement subject, "no test names it, and none is owed" -- this
script is that measurement, not a test, and `orthogonality_census.py` already
reads this same file at this same tier).

    python docs/evidence/orthogonality_repair_census.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from floorplanner.design.validate import (  # noqa: E402
    repair_wall_orthogonality, wall_orthogonality,
)


def _v5_files():
    for d in ("examples", "fixtures"):
        for p in sorted((ROOT / d).rglob("*.json")):
            yield p


def main():
    total_moved = total_refused = total_over_t = total_candidates = 0
    rolled_back = []
    skipped = []
    print(f"{'file':<48}{'near-axis':>10}{'moved':>8}{'refused':>9}"
          f"{'over_t':>8}{'status':>12}")
    for p in _v5_files():
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            skipped.append((rel, f"unreadable JSON ({e})"))
            continue
        if not (isinstance(doc, dict) and "vertices" in doc and "walls" in doc):
            skipped.append((rel, "not a v5 design (sidecar or v1-v4)"))
            continue
        near_axis = [r for r in wall_orthogonality(doc) if 0 < r[3] <= 1.0]
        if not near_axis:
            continue
        try:
            res = repair_wall_orthogonality(doc)
        except (KeyError, StopIteration) as e:
            skipped.append((rel, f"repair raised ({e}) -- not a v5 design"
                                  " this repair can read"))
            continue
        total_candidates += len(near_axis)
        if res["rolled_back"]:
            rolled_back.append((rel, len(near_axis), sorted(res["newly_failing"])))
            print(f"{rel:<48}{len(near_axis):>10}{'--':>8}{'--':>9}"
                  f"{'--':>8}{'ROLLED BACK':>12}")
            continue
        total_moved += len(res["moved"])
        total_refused += len(res["refused"])
        total_over_t += len(res["over_t"])
        print(f"{rel:<48}{len(near_axis):>10}{len(res['moved']):>8}"
              f"{len(res['refused']):>9}{len(res['over_t']):>8}{'applied':>12}")

    print(f"\nTOTAL near-axis candidates: {total_candidates}")
    print(f"TOTAL moved (straightened): {total_moved}")
    print(f"TOTAL refused (conflict or would-worsen): {total_refused}")
    print(f"TOTAL over_t (at/above T, size-excluded): {total_over_t}")
    print(f"TOTAL stranded by a whole-file rollback: "
          f"{sum(n for _r, n, _k in rolled_back)}, across {len(rolled_back)} file(s)")
    if rolled_back:
        print("\nRolled back, and why -- the new invariant key(s) the repair "
              "would have introduced:")
        for rel, n, keys in rolled_back:
            print(f"  {rel} ({n} near-axis candidates, all withheld):")
            for code, ids in keys:
                print(f"    {code} {' '.join(ids)}")
    if skipped:
        print(f"\nSkipped ({len(skipped)}), and why -- not silently dropped:")
        for rel, why in skipped:
            print(f"  {rel:<48}{why}")


if __name__ == "__main__":
    main()
