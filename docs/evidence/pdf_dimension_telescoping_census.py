#!/usr/bin/env python3
"""0118-ruling.md sec2: "telescoping asserted corpus-wide" -- run, not
trusted from the small constructed cases `tests/test_fp2pdf.py` carries.

For every level of every real v5 design in `examples/` and `fixtures/`:
  * how many dimension stations `_features()` collapses via station
    clustering (0118 step 1) -- the corpus-wide measure of how much the
    "mess of dimensions on top of each other" pile-up actually shrinks;
  * that row 1's segments (adjacent ROUNDED-station differences) sum to
    row 2's overall (first-to-last ROUNDED-station difference) EXACTLY,
    on both axes -- the telescoping property 0118 sec2 step 2 exists for.

Telescoping holds by construction (integer differences of one rounded
list always telescope) -- this script is not hunting for a counterexample,
it is the corpus-wide receipt that the real code path, run on real files,
never disagrees with its own arithmetic, and it reports how often
clustering actually fires so the fix's effect on the pile-up is a number,
not an assertion.

    python docs/evidence/pdf_dimension_telescoping_census.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from floorplanner.export import fp2pdf  # noqa: E402


def _v5_files():
    for d in ("examples", "fixtures"):
        for p in sorted((ROOT / d).rglob("*.json")):
            yield p


def _raw_features(sheet):
    """`_features()` with clustering disabled -- the pre-0118 station
    count, for the "how much did clustering actually collapse" column."""
    real = fp2pdf.cluster_stations
    fp2pdf.cluster_stations = lambda values, tol=fp2pdf.STATION_TOL_IN: list(values)
    try:
        return sheet._features()
    finally:
        fp2pdf.cluster_stations = real


def _telescopes(coords):
    if len(coords) < 2:
        return True
    rounded = fp2pdf._rounded_stations(coords)
    segments = sum(b - a for a, b in zip(rounded, rounded[1:], strict=False))
    return segments == rounded[-1] - rounded[0]


def main():
    th = fp2pdf._default_thickness()
    meta = {"title": "t", "subtitle": "", "author": "a",
            "assembly_note": "n", "dim_note": "d"}
    skipped = []
    rows = []
    raw_total = clustered_total = 0
    for p in _v5_files():
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            skipped.append((rel, f"unreadable JSON ({e})"))
            continue
        if not (isinstance(doc, dict) and doc.get("format") ==
                "floorplanner-design" and doc.get("version") == 5):
            skipped.append((rel, "not a v5 design (sidecar or v1-v4)"))
            continue
        for lv in doc.get("levels", []):
            if lv.get("kind", "storey") == "site":
                continue
            try:
                sheet = fp2pdf.Sheet(None, doc, lv, th, False, meta)
            except (KeyError, ZeroDivisionError, ValueError) as e:
                skipped.append((f"{rel}:{lv.get('id')}", f"Sheet() raised ({e})"))
                continue
            raw_fx, raw_fy = _raw_features(sheet)
            fx, fy = sheet._features()
            ok = _telescopes(fx) and _telescopes(fy)
            raw_total += len(raw_fx) + len(raw_fy)
            clustered_total += len(fx) + len(fy)
            rows.append((f"{rel}:{lv.get('id')}", len(raw_fx) + len(raw_fy),
                         len(fx) + len(fy), ok))

    print(f"{'file:level':<58}{'raw':>6}{'clustered':>11}{'telescopes':>12}")
    for name, raw_n, clustered_n, ok in rows:
        print(f"{name:<58}{raw_n:>6}{clustered_n:>11}{str(ok):>12}")
    merged = raw_total - clustered_total
    print(f"\n{len(rows)} sheets, {raw_total} raw stations -> "
          f"{clustered_total} after clustering ({merged} merged)")
    all_ok = all(ok for _, _, _, ok in rows)
    print(f"telescoping: {'PASS -- every sheet' if all_ok else 'FAIL'} "
          f"(row 1 sums to row 2 on both axes)")
    if skipped:
        print(f"\n{len(skipped)} skipped:")
        for rel, why in skipped:
            print(f"  {rel}: {why}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
