#!/usr/bin/env python3
"""Migrate a FloorPlanner v1-v4 plan (`floorplanner-json`) to the v5 design
schema (`floorplanner-design`).

The logic now lives in `floorplanner.design.importer` (ported at P2.1, where it
became the app's load path); this is a thin CLI over it -- the same move
`validate_design.py` made at P0.7. Keeping one implementation means the file the
tool writes and the document the app builds on Open cannot drift apart.

Two modes:

  (default)  FAITHFUL. Room outlines come from the stored
             properties.perimeter_corners, warts and all, and nothing is welded.
             Use this to prove the migration preserves the input, including any
             corruption -- it is what generates examples/planc1.v5.json.

  --clean    REPAIR. What the app now does on Open: weld at join_tol_in,
             planarise, and re-derive each room outline by tracing the enclosing
             face of the wall graph around its label anchor. Faces of a planar
             graph cannot overlap, so this structurally repairs overlapping
             rooms. Rooms with no enclosing face fall back to their stored
             corners, with wall-less edges left open; a room displaced from its
             face becomes a floating concept room.

Usage:
  python migrate_to_design_v5.py in.json out.json [--clean] [--name NAME]
"""
import argparse
import json
import sys
from pathlib import Path

# run from anywhere: put the repo root on the path so `floorplanner` imports
# (the package is not pip-installed; tests reach it via conftest, the CLI here)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from floorplanner.design.importer import import_legacy  # noqa: E402

# provenance records WHICH tool did the conversion, so the CLI keeps naming
# itself even though the code now lives in the package
TOOL = "migrate_to_design_v5.py"


def migrate(src, clean=False, design_name=None):
    """(doc, report) -- the dict form, kept for callers that predate P2.1."""
    design, rep = import_legacy(src, tool=TOOL, design_name=design_name,
                                clean=clean)
    return design.to_dict(), rep


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--clean", action="store_true",
                    help="re-trace room outlines from the wall graph "
                         "(repairs overlaps)")
    ap.add_argument("--name", default=None)
    a = ap.parse_args(argv)
    with open(a.src, encoding="utf-8") as f:
        src = json.load(f)
    doc, rep = migrate(src, clean=a.clean, design_name=a.name)
    with open(a.dst, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
