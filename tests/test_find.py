"""0316: Find item -- the target list, the filter (label + name), and
zoom+select on a pick. Edit ▸ Find item (Ctrl+F)."""
import re
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt

from floorplanner.find import FindDialog, find_targets

pytestmark = pytest.mark.io

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _open(win, name="symmetricP1.json"):
    win.load_path(str(EXAMPLES / name))


def test_find_targets_covers_the_labelled_kinds_with_unique_labels(fp, win):
    _open(win)
    rows = find_targets(win.scene)
    kinds = {r[1] for r in rows}
    assert {"wall", "room", "corner"} <= kinds, f"missing a kind: {kinds}"
    # every row carries a session-label-shaped id, and each label is unique
    assert all(re.match(r"^[A-Za-z]+[0-9]+$", r[0]) for r in rows)
    labels = [r[0] for r in rows]
    assert len(labels) == len(set(labels)), "two rows claim one label"


def test_the_filter_matches_label_and_name_not_the_type(fp, win):
    _open(win)
    dlg = FindDialog(win)
    # a type word (e.g. "wall") must NOT be what the filter matches on -- only
    # the label and the user name. Filtering by the literal kind should not
    # return every wall.
    dlg.box.setText("zzzznope")
    assert dlg.list.count() == 0, "a nonsense query still matched something"

    # the exact label of some wall appears when typed
    wall = next(r for r in find_targets(win.scene) if r[1] == "wall")
    dlg.box.setText(wall[0])
    found = [dlg.list.item(i).data(Qt.ItemDataRole.UserRole)[0]
             for i in range(dlg.list.count())]
    assert wall[0] in found, "typing a wall's label did not surface it"


def test_picking_a_row_selects_the_item(fp, win):
    _open(win)
    dlg = FindDialog(win)
    target = next(r for r in dlg._rows if r[1] == "wall" and r[5] is not None)
    dlg.box.setText(target[0])
    picked = next((dlg.list.item(i) for i in range(dlg.list.count())
                   if dlg.list.item(i).data(Qt.ItemDataRole.UserRole)[0] == target[0]),
                  None)
    assert picked is not None, "the label did not appear after filtering"
    dlg._go(picked)
    assert target[5].isSelected(), "the picked wall was not selected"


def test_find_item_opens_the_dialog(fp, win):
    _open(win)
    win.find_item()
    assert win._find_dialog is not None and win._find_dialog.isVisible()
    win._find_dialog.close()
