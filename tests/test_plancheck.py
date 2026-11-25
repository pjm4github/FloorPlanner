"""Edit ▸ Check plan for problems -- the red-box overlay of design problems on
the active floor (2026-11, Patrick: "a means of showing this information on the
plan ... a red box ... a 'check plan' ... a 'clear' ... a 'show/hide'").

Detection reuses the validator (`check` + `near_vertex_gaps`), so these pin
the WIRING, not the finding logic (that is pinned in test_design_bridge /
test_validate): the scan finds the gaps a known plan carries; the boxes live
only on the scene and never enter a saved document or dirty the plan; they
follow the active floor; and the three menu actions enable, disable and toggle
as specified.
"""
import json
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsRectItem

from floorplanner.plancheck import PlanCheckOverlay, problem_spots

pytestmark = [pytest.mark.io, pytest.mark.walls]

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def _load(win, name):
    win.load_data(json.loads((EXAMPLES / name).read_text(encoding="utf-8")))
    return win


def _markers(scene):
    return [it for it in scene.items() if getattr(it, "_fp_plan_marker", False)]


# -- detection ---------------------------------------------------------------
def test_problem_spots_find_the_gaps_a_known_plan_carries(fp, win):
    """planc1 carries four 1.5" divider gaps (test_design_bridge pins the
    count). The scan lists them as gap spots on the floor being edited, each
    with a four-number plan rectangle."""
    _load(win, "planc1.json")
    spots, other, unplaceable = problem_spots(win)
    gaps = [s for s in spots if s.kind == "gap"]
    assert len(gaps) >= 4, "the plan's own divider gaps must be found"
    assert all(s.floor == win.active_floor for s in gaps)
    assert all(len(s.rect) == 4 for s in gaps)
    assert isinstance(other, int) and isinstance(unplaceable, int)


def test_a_fresh_plan_has_nothing_to_box(fp, win):
    """An empty, valid plan yields no spots and leaves the overlay empty."""
    spots, other, unplaceable = problem_spots(win)
    assert spots == []
    assert (other, unplaceable) == (0, 0)


# -- the overlay and the three actions ---------------------------------------
def test_check_plan_boxes_then_toggles_then_clears(fp, win):
    _load(win, "planc1.json")
    spots = win.check_plan()
    scene = win.scene
    assert spots, "the loaded plan has problems to box"

    boxes = _markers(scene)
    assert len(boxes) == len(spots)
    assert all(isinstance(b, QGraphicsRectItem) for b in boxes)
    # the actions now reflect a live scan
    assert win.a_plan_show.isChecked() and win.a_plan_show.isEnabled()
    assert win.a_plan_clear.isEnabled()
    # each box is click-through (does not steal clicks from the wall beneath)
    # and stamped with the floor it was computed on
    for b in boxes:
        assert b.acceptedMouseButtons() == Qt.MouseButton.NoButton
        assert b.floor == win.active_floor
        assert b.zValue() >= PlanCheckOverlay.ZVALUE

    # Show/hide toggles visibility without recomputing
    win.a_plan_show.setChecked(False)
    assert all(not b.isVisible() for b in boxes)
    assert _markers(scene) == boxes, "hiding must not remove the boxes"
    win.a_plan_show.setChecked(True)
    assert all(b.isVisible() for b in boxes)

    # Clear removes them and disables both items
    win.clear_plan_problems()
    assert _markers(scene) == []
    assert not win.a_plan_show.isEnabled() and not win.a_plan_show.isChecked()
    assert not win.a_plan_clear.isEnabled()


def test_a_rescan_replaces_the_previous_boxes(fp, win):
    """Running Check plan twice does not accumulate boxes."""
    _load(win, "planc1.json")
    first = win.check_plan()
    again = win.check_plan()
    assert len(_markers(win.scene)) == len(again) == len(first)


# -- the boxes are presentation, never document ------------------------------
def test_boxes_never_enter_the_document_or_dirty_the_plan(fp, win):
    """The markers are plain rect items: the canonical snapshot is byte-equal
    with them on the scene, so they cannot save, dirty or print."""
    _load(win, "planc1.json")
    before = win.snapshot()
    win.check_plan()
    assert _markers(win.scene), "the boxes really are on the scene"
    assert win.snapshot() == before, "the red boxes changed the document"


# -- the boxes belong to their floor -----------------------------------------
def test_boxes_follow_the_active_floor(fp, win):
    """A box carries its floor, so the floor-visibility machinery hides it the
    moment you leave that floor and shows it again on return -- no coupling to
    the floor-switch path."""
    _load(win, "planc1.json")
    home = win.active_floor
    win.check_plan()
    boxes = _markers(win.scene)
    assert boxes and all(b.isVisible() for b in boxes)

    win.new_floor_named("Upper")            # creates and switches to Upper
    assert win.active_floor == "Upper"
    assert all(not b.isVisible() for b in boxes), \
        "the ground-floor boxes hide while another floor is edited"

    win.switch_floor(home)
    assert all(b.isVisible() for b in boxes)
