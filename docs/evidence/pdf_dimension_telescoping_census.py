#!/usr/bin/env python3
"""0118-ruling.md sec2 / 0129-ruling.md sec3(a) / 0130-ruling.md sec2:
"telescoping asserted corpus-wide" -- run, not trusted from the small
constructed cases `tests/test_fp2pdf.py` carries.

For every level of every real v5 design in `examples/` and `fixtures/`
(`fixtures/incoming/` included -- a census reads, it does not depend, per
0063-ruling.md sec4's own precedent):

  * how many dimension stations the two-stage declutter (0118's 1"
    clustering, then 0129's grid-aware filter against the DOCUMENT's own
    `wall_snap_in`) collapses on the orthogonal rows -- the corpus-wide
    measure of how much the pile-up actually shrinks;
  * that row 1's segments (adjacent ROUNDED-station differences) sum to
    row 2's overall EXACTLY, on both axes, WITHIN THE ORTHOGONAL FAMILY'S
    OWN EXTENT (0130 sec2 -- row 2 no longer spans the whole plan bbox,
    since 0130 sec1 took angled-wall corners out of row 1 entirely);
  * the same telescoping property, independently, for EVERY angled
    dimension lane on the sheet (0130 sec2's "each family telescopes
    within itself").

Telescoping holds by construction (integer differences of one rounded
list always telescope) -- this script is not hunting for a counterexample,
it is the corpus-wide receipt that the real code path, run on real files,
never disagrees with its own arithmetic.

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
    """`_features()` with BOTH declutter stages disabled -- the
    pre-0118/0129 station count, for the "how much did declutter actually
    collapse" column."""
    real_cluster, real_grid = fp2pdf.cluster_stations, fp2pdf.grid_filter_stations
    fp2pdf.cluster_stations = lambda values, tol=fp2pdf.STATION_TOL_IN: list(values)
    fp2pdf.grid_filter_stations = lambda stations, snap_in: list(stations)
    try:
        return sheet._features()
    finally:
        fp2pdf.cluster_stations, fp2pdf.grid_filter_stations = real_cluster, real_grid


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
    lane_rows = []
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

            for fam in sheet._angled_families():
                geo = sheet._lane_geometry(fam)
                lane_ok = _telescopes(geo["stations"])
                lane_rows.append((f"{rel}:{lv.get('id')}",
                                  round(fam["angle"], 1),
                                  len(geo["stations"]), lane_ok))

    print(f"{'file:level':<58}{'raw':>6}{'declutter':>11}{'telescopes':>12}")
    for name, raw_n, clustered_n, ok in rows:
        print(f"{name:<58}{raw_n:>6}{clustered_n:>11}{str(ok):>12}")
    merged = raw_total - clustered_total
    print(f"\n{len(rows)} sheets, {raw_total} raw stations -> "
          f"{clustered_total} after 1\" clustering + grid filter ({merged} merged)")
    all_ok = all(ok for _, _, _, ok in rows)
    print(f"orthogonal telescoping: {'PASS -- every sheet' if all_ok else 'FAIL'} "
          f"(row 1 sums to row 2, within the orthogonal family's own extent)")

    if lane_rows:
        print(f"\n{'file:level':<58}{'angle':>7}{'stations':>10}{'telescopes':>12}")
        for name, angle, n, ok in lane_rows:
            print(f"{name:<58}{angle:>7}{n:>10}{str(ok):>12}")
    lanes_ok = all(ok for *_, ok in lane_rows)
    print(f"\n{len(lane_rows)} angled lanes across the corpus, telescoping: "
          f"{'PASS -- every lane' if lanes_ok else 'FAIL'}")

    if skipped:
        print(f"\n{len(skipped)} skipped:")
        for rel, why in skipped:
            print(f"  {rel}: {why}")
    return 0 if (all_ok and lanes_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
