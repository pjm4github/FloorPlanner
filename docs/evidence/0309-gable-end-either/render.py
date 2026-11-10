"""0309 / his #3 follow-on (2026-11-10) -- EITHER gable end in the Elevation tab.
`RoofItem.gable_elevation(end=0|1)` draws the chosen gable end and ITS OWN
gable-end wall's windows; the dialog's end selector feeds it, the blue dot marks
the end. This instrument renders both ends so the per-end pick can be eyeballed
without the app. Run headless:

    PYTHONPATH=. QT_QPA_PLATFORM=offscreen python docs/evidence/0309-gable-end-either/render.py [out_dir]

Produces, for a built two-gable-end roof with DIFFERENT windows at each end,
`built_end0.png` / `built_end1.png`; and, from `wiscawayL2-fix.json`, both ends of
a plain gable roof that has two live gable ends (`fix_end0.png` / `fix_end1.png`),
or just `fix_end0.png` with a note if none has two. NOTE: headless text renders as
tofu -- the offscreen font has no glyphs; `fmt_in` is ASCII and draws on a real
display."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication, QGraphicsScene

_app = QApplication.instance() or QApplication([])

import FloorPlanner as fp
from floorplanner.config import DEFAULT_FLOOR
from floorplanner.dialogs import _ElevationCanvas
from floorplanner.roofs import RoofItem
from floorplanner.walls import WallItem

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


def _wins(data):
    """ASCII one-liner: the end drawn, the width/ridge, and the windows."""
    if not data:
        return "  (no gable end to draw)"
    ws = data.get("windows", [])
    sizes = ", ".join(f"{w['w_in']:g}x{w['h_in']:g}@{w['centre_in']:+.0f}" for w in ws)
    return (f"  end={data.get('end')} width={data['width_in']:g} "
            f"ridge={data['ridge_in']:g} windows={len(ws)} [{sizes}]")


def built():
    """A plain gable, BOTH ends gabled, a DIFFERENT window-wall at each end:
    p1 end (x=0) carries a 3648 at the wall centre; p2 end (x=400) a 3072
    off-centre. Each end must draw only its own wall's window(s)."""
    scene = QGraphicsScene()
    rf = RoofItem(QPointF(0, 100), QPointF(400, 100), eaves_h_in=96.0,
                  ridge_h_in=150.0, overhang_in=0.0, span_in=100.0)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    # p1-end wall (x=0): one centred window
    w1 = WallItem(QPointF(0, 0), QPointF(0, 200), "exterior")
    w1.floor = DEFAULT_FLOOR
    w1.openings.append(fp.OpeningItem(w1, "window", "3648", 100.0))
    scene.addItem(w1)
    # p2-end wall (x=400): a different, off-centre window
    w2 = WallItem(QPointF(400, 0), QPointF(400, 200), "exterior")
    w2.floor = DEFAULT_FLOOR
    w2.openings.append(fp.OpeningItem(w2, "window", "3072", 140.0))
    scene.addItem(w2)

    e0, e1 = rf.gable_elevation(end=0), rf.gable_elevation(end=1)
    _render(e0, os.path.join(OUT, "built_end0.png"))
    _render(e1, os.path.join(OUT, "built_end1.png"))
    print("built two-gable-end roof (p1 window 3648 centred, p2 window 3072 off):")
    print("  gable_elevation(end=0):")
    print(_wins(e0))
    print("  gable_elevation(end=1):")
    print(_wins(e1))
    assert e0 and e1 and e0["end"] == 0 and e1["end"] == 1
    # each end draws its OWN wall: end 0 the 36x48, end 1 the 30x72
    assert any(abs(w["w_in"] - 36) < 1 for w in e0["windows"]), "end 0 should show 3648"
    assert any(abs(w["w_in"] - 30) < 1 for w in e1["windows"]), "end 1 should show 3072"
    assert not any(abs(w["w_in"] - 30) < 1 for w in e0["windows"]), "end 0 must NOT show p2's window"
    print("  OK: each end drew only its own wall's window")


def from_fixture():
    win = fp.MainWindow()
    win.load_path("fixtures/incoming/wiscawayL2-fix.json")
    roofs = [it for it in win.scene.items() if isinstance(it, RoofItem)]
    plain = [r for r in roofs if not r.is_dormer()]
    two = [r for r in plain if all(bool(g) for g in list(getattr(r, "gable", [True, True]))[:2])]
    print(f"wiscawayL2-fix.json: {len(plain)} plain gable roof(s), "
          f"{len(two)} with two live gable ends")
    if two:
        # the one whose two ends carry the most windows between them
        def _score(r):
            return len((r.gable_elevation(end=0) or {}).get("windows", [])) + \
                   len((r.gable_elevation(end=1) or {}).get("windows", []))
        r = max(two, key=_score)
        e0, e1 = r.gable_elevation(end=0), r.gable_elevation(end=1)
        _render(e0, os.path.join(OUT, "fix_end0.png"))
        _render(e1, os.path.join(OUT, "fix_end1.png"))
        print("  end 0:")
        print(_wins(e0))
        print("  end 1:")
        print(_wins(e1))
    elif plain:
        r = max(plain, key=lambda r: len((r.gable_elevation() or {}).get("windows", [])))
        e0 = r.gable_elevation(end=0)
        _render(e0, os.path.join(OUT, "fix_end0.png"))
        print("  no plain roof has TWO gable ends; rendered end 0 of one gable roof:")
        print(_wins(e0))
    else:
        print("  no plain gable roof in the fixture")


def main():
    built()
    print()
    from_fixture()


if __name__ == "__main__":
    main()
