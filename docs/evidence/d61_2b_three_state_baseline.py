"""THE CORRECT BASELINE: three states, not two.

  1 PRISTINE     the plan before the room ever landed at site B
  2 AFTER-JOIN   the room joined at B
  3 AFTER-LEAVE  the room extracted from B and taken far away -- B is empty again

DEBRIS = what AFTER-LEAVE has at site B that PRISTINE did not, with the room gone.
The earlier attempt compared before-move to after-move at the room's ORIGINAL
site, whose 'before' already contained every split a previous arrival caused --
so an unchanged count could not distinguish absence from presence in both terms.
"""
import math
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath("."))

from PyQt6.QtWidgets import QApplication                  # noqa: E402

app = QApplication([])
import FloorPlanner as fp                                 # noqa: E402
from floorplanner.extract import extract_room, join_room  # noqa: E402

def dist_to_poly(pt, poly):
    best = float("inf")
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        L = math.hypot(bx-ax, by-ay)
        if L < 1e-9:
            continue
        t = max(0.0, min(1.0, ((pt[0]-ax)*(bx-ax) + (pt[1]-ay)*(by-ay))/(L*L)))
        best = min(best, math.dist(pt, (ax+t*(bx-ax), ay+t*(by-ay))))
    return best

def near(win, poly, tol=1.0):
    out = []
    for w in win.scene.items():
        if not isinstance(w, fp.WallItem):
            continue
        mid = ((w.p1.x()+w.p2.x())/2.0, (w.p1.y()+w.p2.y())/2.0)
        if dist_to_poly(mid, poly) < tol:
            out.append((round(w.p1.x(),1), round(w.p1.y(),1),
                        round(w.p2.x(),1), round(w.p2.y(),1)))
    return sorted(out)

OFF = 24.0     # lands AMONG NEIGHBOURS -- open space cannot show debris
win = fp.MainWindow()
win.resize(1400, 1000)
win.load_path(os.path.abspath("fixtures/wiscaway2026-08-08.json"))
room = next(r for r in win.scene.items()
            if isinstance(r, fp.RoomItem) and r.name == "WIC")

# site B = where the room WILL land. Compute it from the current polygon + OFF.
home = [(c.x(), c.y()) for c in room.corners]
siteB = [(x + OFF, y) for x, y in home]

pristine = near(win, siteB)
print("1 PRISTINE   walls at site B: %d" % len(pristine))

extract_room(win.scene, room)
room._translate(OFF, 0.0)
join_room(win.scene, room)
joined = near(win, siteB)
print("2 AFTER-JOIN walls at site B: %d" % len(joined))

# state 3: the room LEAVES site B and is taken right out of the plan.
# join_room is NOT called -- 'after-leave' is the vacated state, and the
# room rejoining somewhere else would add that site's splits to the count.
extract_room(win.scene, room)
room._translate(2000.0, 0.0)
left = near(win, siteB)
print("3 AFTER-LEAVE walls at site B: %d" % len(left))

debris = [w for w in left if w not in pristine]
gone = [w for w in pristine if w not in left]
print()
print("DEBRIS (in after-leave, not in pristine): %d" % len(debris))
for d in debris[:8]:
    print("    ", d)
print("LOST  (in pristine, not in after-leave): %d" % len(gone))
for g in gone[:8]:
    print("    ", g)
win.close()
