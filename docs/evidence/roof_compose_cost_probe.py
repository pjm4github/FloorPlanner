"""Compose time against the number of roofs on a level (0237-report.md sec0):
add ridges one at a time where a user editing would drop them, across the
existing ones, and time one building compose after each. On his
`wiscaway2026-10-07R1.json`: 9 roofs 0.75 s, 12: 5.2 s, 15: 32 s.

    python docs/evidence/roof_compose_cost_probe.py fixtures/incoming/wiscaway2026-10-07R1.json
"""
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from PyQt6.QtCore import QPointF  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

_app = QApplication.instance() or QApplication([])

import FloorPlanner as fp  # noqa: E402
from floorplanner.roofs import RoofItem, sync_roof_clips  # noqa: E402

EXTRA = [((300, 540), (900, 540)), ((500, 330), (500, 740)), ((200, 600), (1100, 600)),
         ((600, 360), (600, 700)), ((350, 450), (1000, 450)), ((800, 330), (800, 740)),
         ((250, 680), (1150, 680)), ((950, 340), (950, 720))]


def main():
    win = fp.MainWindow()
    win.prepare_headless()
    win.load_path(sys.argv[1])
    win.switch_floor("upper")
    win.set_tool(fp.TOOL_SELECT)
    win._set_show_roofs(True)
    win._set_edit_roofs(True)

    def n_roofs():
        return sum(1 for r in win.scene.items() if isinstance(r, RoofItem))

    def timed_sync():
        t = time.perf_counter()
        sync_roof_clips(win.scene)
        return time.perf_counter() - t

    print(f"{n_roofs()} roofs: compose {timed_sync():.2f}s", flush=True)
    for a, b in EXTRA:
        rf = fp.RoofItem(QPointF(*a), QPointF(*b))
        rf.floor = "upper"
        win.scene.addItem(rf)
        dt = timed_sync()
        print(f"{n_roofs()} roofs: compose {dt:.2f}s", flush=True)
        if dt > 60:
            break
    print("done", flush=True)


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    os._exit(0)
