#!/usr/bin/env python3
"""0055-ruling.md sec4 / 0057-ruling.md sec2: the census 0056-report.md built
the instrument for and did not run. "Nobody knows how many plans have this...
the corpus has been quietly drifting and no instrument has ever looked."

Walks every v5-shaped JSON in `examples/` and `fixtures/` (recursively; a
sidecar or legacy v1-v4 file has no top-level `vertices`/`walls` and is
skipped rather than guessed at) and prints `wall_orthogonality()`'s band
table per plan, then the corpus-wide total this census exists to produce:
how many walls are within 1 degree of orthogonal without being on it --
0055-ruling.md sec4's own input to item C's tolerance argument, which
"cannot be ruled without it."

    python docs/evidence/orthogonality_census.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from floorplanner.design.validate import (  # noqa: E402
    ORTHOGONALITY_BANDS, orthogonality_bands, wall_orthogonality,
)


def _v5_files():
    for d in ("examples", "fixtures"):
        for p in sorted((ROOT / d).rglob("*.json")):
            yield p


def main():
    grand_rows = []
    skipped = []                              # no silent drops: log what and why
    print(f"{'file':<48}{'walls':>7}", "".join(f"{lbl:>12}" for _lo, _hi, lbl
                                                in ORTHOGONALITY_BANDS))
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
        rows = wall_orthogonality(doc)
        if not rows:
            skipped.append((rel, "v5 design with zero walls"))
            continue
        bands = orthogonality_bands(rows)
        print(f"{rel:<48}{len(rows):>7}",
              "".join(f"{bands[lbl]:>12}" for _lo, _hi, lbl in ORTHOGONALITY_BANDS))
        grand_rows.extend(rows)

    total_bands = orthogonality_bands(grand_rows)
    print(f"\n{'TOTAL':<48}{len(grand_rows):>7}",
          "".join(f"{total_bands[lbl]:>12}" for _lo, _hi, lbl in ORTHOGONALITY_BANDS))

    within_1_not_on = sum(1 for *_rest, deg in grand_rows if 0.0 < deg <= 1.0)
    print(f"\nWalls within 1 degree of orthogonal WITHOUT being on it: "
          f"{within_1_not_on} of {len(grand_rows)}")

    if skipped:
        print(f"\nSkipped ({len(skipped)}), and why -- not silently dropped:")
        for rel, why in skipped:
            print(f"  {rel:<48}{why}")


if __name__ == "__main__":
    main()
