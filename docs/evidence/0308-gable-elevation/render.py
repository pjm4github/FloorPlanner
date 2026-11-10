"""0308 / his #3 -- the gable-end window ELEVATION. Renders the End-On dialog's
Elevation tab (`dialogs._ElevationCanvas` fed by `RoofItem.gable_elevation()`) to
PNGs so the drawing can be eyeballed without the app. Run headless:

    PYTHONPATH=. QT_QPA_PLATFORM=offscreen python docs/evidence/0308-gable-elevation/render.py [out_dir]

Needs `wiscawayL2-fix.json` and `little-dormer-test.json` in fixtures/incoming/.
Produces `elev_gable.png` (a plain gable with its located windows) and
`elev_dormer.png` (a dormer face with its window). NOTE: headless text renders as
tofu -- the offscreen font has no glyphs; `fmt_in` is ASCII and draws on a real
display."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication([])

import FloorPlanner as fp
from floorplanner.dialogs import _ElevationCanvas
from floorplanner.roofs import RoofItem

OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def _render(data, path, size=(560, 360)):
    c = _ElevationCanvas()
    c.resize(*size)
    c.set_data(data)
    img = QImage(size[0], size[1], QImage.Format.Format_ARGB32)
    img.fill(0xFFFFFFFF)
    p = QPainter(img)
    c.render(p)
    p.end()
    img.save(path)
    print("wrote", path)


def main():
    win = fp.MainWindow()
    win.load_path("fixtures/incoming/wiscawayL2-fix.json")
    roofs = [it for it in win.scene.items() if isinstance(it, RoofItem)]
    gable = max((r for r in roofs if not r.is_dormer()),
                key=lambda r: len((r.gable_elevation() or {}).get("windows", [])))
    _render(gable.gable_elevation(), os.path.join(OUT, "elev_gable.png"))

    win2 = fp.MainWindow()
    win2.load_path("fixtures/incoming/little-dormer-test.json")
    dormer = next(r for r in win2.scene.items()
                  if isinstance(r, RoofItem) and r.is_dormer())
    _render(dormer.gable_elevation(), os.path.join(OUT, "elev_dormer.png"))


if __name__ == "__main__":
    main()
