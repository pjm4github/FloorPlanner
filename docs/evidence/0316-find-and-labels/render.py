"""0316 receipt: persistent annotation labels + the Find item tool.

Opens a plan, gives one wall a session label its geometric id CANNOT recover
(W777 on a wall whose canonical id is something else), saves the way the app
saves (`design_document`), reopens it, and shows the label came back -- the
drift a save used to cause (the id is renumbered by geometry) is gone. Then it
opens the Find dialog, filters to a label, and grabs the dialog + the plan view
with the found wall selected and zoomed.

    python docs/evidence/0316-find-and-labels/render.py
"""
import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))   # repo root, for the shim

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv[:1])                               # before FloorPlanner

import FloorPlanner as fp  # noqa: F401,E402
from floorplanner.find import FindDialog, find_targets  # noqa: E402
from floorplanner.mainwindow import MainWindow  # noqa: E402

OUT = Path(__file__).resolve().parent
EXAMPLES = Path(__file__).resolve().parents[2].parent / "examples"


def _wall_labels(win):
    return {w.uid for w in win.scene.items() if isinstance(w, fp.WallItem)}


def main():
    win = MainWindow()
    doc = __import__("json").loads((EXAMPLES / "symmetricP1.json").read_text("utf-8"))

    # give one wall a label its geometric id cannot give back
    doc["walls"][0]["uid"] = "W777"
    win.open_document(doc, interactive=False)
    before = "W777" in _wall_labels(win)
    print("after open, the plan shows W777:", before)

    # SAVE the way the app saves, then reopen -- the number comes back
    saved = win.design_document()
    stored = next((w["uid"] for w in saved["walls"] if w.get("uid") == "W777"), None)
    print("the saved file carries the label:", stored)
    win.open_document(saved, interactive=False)
    print("after save -> reopen, the plan STILL shows W777:", "W777" in _wall_labels(win))

    rows = find_targets(win.scene)
    print("find sees %d labelled items (%s ...)"
          % (len(rows), ", ".join(r[0] for r in rows[:6])))

    # the Find dialog, filtered to a wall, the match selected -> zoom + select
    dlg = FindDialog(win)
    dlg.resize(340, 440)
    some = next(r for r in rows if r[1] == "wall" and r[5] is not None)
    dlg.box.setText(some[0])
    picked = next(dlg.list.item(i) for i in range(dlg.list.count())
                  if dlg.list.item(i).data(Qt.ItemDataRole.UserRole)[0] == some[0])
    dlg._go(picked)
    app.processEvents()
    dlg.grab().save(str(OUT / "find_dialog.png"))
    print("wrote find_dialog.png (filtered to %s)" % some[0])

    win.view.resize(640, 420)
    win.view.grab().save(str(OUT / "find_zoomed.png"))
    print("wrote find_zoomed.png (the found wall selected and zoomed)")
    print("RENDER OK")


if __name__ == "__main__":
    main()
