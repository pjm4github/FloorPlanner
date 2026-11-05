"""Checkpoint 0 of the 1-1/2-storey arc (0297 sec0 item 4): measure the three
UNMEASURED items of 0293 sec1, headless on little-dormer-test.json.

  M1  RoofEndOnDialog.level_base_in() on a cross-level dormer
  M2  roof_clip_spans' same-floor filter on an L2 wall under the L1 roof
  M3  dormer_defaults' room source

Run:  PYTHONPATH=. .venv/Scripts/python.exe docs/evidence/1p5-storey-checkpoint0/measure.py
"""
import json
import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import QPointF  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])

import FloorPlanner as fp  # noqa: E402
import floorplanner.roofs as R  # noqa: E402
from floorplanner.config import floor_elevation  # noqa: E402
from floorplanner.design.bridge import apply_design_to_scene  # noqa: E402
from floorplanner.dialogs import RoofEndOnDialog  # noqa: E402

win = fp.MainWindow()
win.prepare_headless()
doc = json.load(open("fixtures/incoming/little-dormer-test.json"))
apply_design_to_scene(win, doc)
roofs = [it for it in win.scene.items() if isinstance(it, R.RoofItem)]
rf2 = next(r for r in roofs if r.host is not None)   # the dormer
rf1 = rf2.host                                        # its host
print("setup: host rf1.floor=%s  dormer rf2.floor=%s" % (rf1.floor, rf2.floor))

# M1 -- RoofEndOnDialog.level_base_in() on a cross-level dormer
base_same = RoofEndOnDialog(rf2).level_base_in()
host_base = floor_elevation(rf1.floor)
rf2.floor = "L2"                                      # promote (cross-level)
base_cross = RoofEndOnDialog(rf2).level_base_in()
rf2.floor = "L1"
print("M1 level_base_in: dormer-on-L1=%.1f  host_base=%.1f  dormer-on-L2=%.1f  OVERSTATED_BY=%.1f"
      % (base_same, host_base, base_cross, base_cross - host_base))

# M2 -- roof_clip_spans same-floor filter on an L2 wall under the L1 roof
l2walls = [it for it in win.scene.items() if isinstance(it, fp.WallItem) and it.floor == "L2"]
w = l2walls[0]
spans = R.roof_clip_spans(win.scene, w)
l1roofs = [r for r in roofs if r.floor == "L1"]
print("M2 roof_clip_spans(L2 wall %s): spans=%d   L1 roofs present=%d (excluded by it.floor==wall.floor)"
      % (getattr(w, "doc_id", "?"), len(spans), len(l1roofs)))

# M3 -- dormer_defaults room source (which floor's rooms it reads)
seen = {}
orig = R._floor_rooms


def spy(scene, floor):
    seen.setdefault("floors", []).append(floor)
    return orig(scene, floor)


R._floor_rooms = spy
R.dormer_defaults(win.scene, rf1, QPointF(rf2.p1.x(), rf2.p1.y()))
R._floor_rooms = orig
print("M3 dormer_defaults read rooms on floor(s): %s   (host.floor=%s; the dormer serves the floor ABOVE)"
      % (seen.get("floors"), rf1.floor))
