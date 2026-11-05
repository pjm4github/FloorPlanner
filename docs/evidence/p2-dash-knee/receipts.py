"""P2 (0297 §2 / 0293 §5 P2) receipts on the wiscaway R-file (L2 height 96).

  * the R3b WALL DASH by level: L1 unchanged, L2 gains the cross-level dashes
    from the L1 roof it rises through (BEFORE/AFTER measured by stashing roofs.py);
  * the KNEE LINE in the L2 bedrooms: where rf1's surface crosses their ceiling
    plane (base + ceiling, absolute), with the y derived from rf1's record.

Run:  PYTHONPATH=. .venv/Scripts/python.exe docs/evidence/p2-dash-knee/receipts.py fixtures/incoming/wiscawayL2-fix.json
"""
import json
import os
import sys
from collections import Counter

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])

import FloorPlanner as fp  # noqa: E402
from floorplanner.design.bridge import apply_design_to_scene  # noqa: E402
from floorplanner.rooms import RoomItem  # noqa: E402
from floorplanner.roofs import roof_clip_spans, room_ceiling_break_lines  # noqa: E402

win = fp.MainWindow()
win.prepare_headless()
apply_design_to_scene(win, json.load(open(sys.argv[1])))

dashed, total = Counter(), Counter()
for it in win.scene.items():
    if isinstance(it, fp.WallItem):
        total[it.floor] += 1
        if roof_clip_spans(win.scene, it):
            dashed[it.floor] += 1
print("WALL DASH by level (dashed / total):")
for lvl in sorted(total):
    print("  %s: %d / %d" % (lvl, dashed[lvl], total[lvl]))

print("KNEE LINE, the L2 bedrooms (rf1: ridge 294 abs at y=678, 12/12; L2 ceiling"
      " 216 abs -> 78 from the ridge -> y = 600, 756):")
for it in win.scene.items():
    if isinstance(it, RoomItem) and getattr(it, "name", "") in ("BR2", "BR3", "BATH", "OPEN"):
        segs = room_ceiling_break_lines(win.scene, it)
        ys = sorted({round(p.y(), 1) for s in segs for p in s})
        print("  %-10s: %d segs; y in %s" % (it.name, len(segs), ys))
