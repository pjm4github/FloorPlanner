"""D74: render the decoration channel, and build the manual-check plan.

    python docs/evidence/d74_decoration_render.py

Writes `fixtures/d74-wall-decoration.json` (the plan for the AMBER check) and
two PNGs beside this file: one at 6x and one at 2x, which is roughly working
zoom. **The 2x one is the whole point** -- the first cut of the channel passed
every test and still failed the check, because a fence and a railing rendered
as the same ladder at the zoom a person actually works at, differing only in
how fine it was. Nothing but a render was going to say so.

Four landscape runs side by side plus an ordinary wall for reference, and a
gate in the middle of the railing: that is exactly the check's two questions --
tell a fence from a railing without clicking, and find the gate in a run of
rail.
"""
import os
import sys
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import QPointF, QRectF          # noqa: E402
from PyQt6.QtWidgets import QApplication          # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

APP = QApplication([])                            # before importing the package

import FloorPlanner as fp                          # noqa: E402

RUNS = ["exterior", "railing", "fence", "hedge", "retaining"]


def main():
    win = fp.MainWindow()
    sc = win.scene
    for i, kind in enumerate(RUNS):
        w = fp.WallItem(QPointF(0, i * 60.0), QPointF(240, i * 60.0), kind)
        sc.addItem(w)
        if kind == "railing":                     # a gate, derived from the wall
            op = fp.OpeningItem(w, "gate", "3068", 120)
            w.openings.append(op)
    fp.rebuild_all_walls(sc)

    win.save_path(str(ROOT / "fixtures" / "d74-wall-decoration.json"))

    here = Path(__file__).resolve().parent
    rect = QRectF(-20, -30, 280, 300)
    for scale, name in ((6.0, "d74-decoration-zoomed.png"),
                        (2.0, "d74-decoration-working-zoom.png")):
        print(f"{name}: {win.export_canvas(str(here / name), rect, scale)}")

    for kind in RUNS:
        w = next(it for it in sc.items()
                 if isinstance(it, fp.WallItem) and it.wall_type == kind)
        marks = 0 if w._decor is None else w._decor.elementCount()
        print(f"{kind:10s} t={w.t:5.1f}  decor_elements={marks}")


if __name__ == "__main__":
    main()
