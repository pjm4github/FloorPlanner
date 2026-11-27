"""0376 / 0377 — the furnishing kinds in the editor (Qt side; 0376 O4, 0377 O3).

The GEOMETRY (footprint, plan symbol, the weave, the tub fittings) is pinned
Qt-free in `tests/test_furnishings_0376.py`. This file is the EDITOR wiring that
cannot be tested without Qt: each new or reworked parametric kind places as a
`FurnishingItem`, opens its properties dialog, round-trips its state through the
item and the saved document; a placed armchair / wicker chair / corner desk with
no state stays stateless; and the corner desk's and the arrangement's plan
symbols turn, and the umbrella table's footprint grows, when the ITEM's state is
edited. A dialog is never `exec()`-ed headless; `try_accept()` is what OK calls.
"""
import pytest
from PyQt6.QtCore import QPointF

from floorplanner.parametric import registry

pytestmark = pytest.mark.furnishings

# every kind 0376/0377 made a parametric fixture with its own dialog
KINDS = ["corner_desk", "armchair", "umbrella_table", "large_tv",
         "wicker_chair", "wicker_chair_small", "wicker_loveseat", "wicker_table",
         "bathtub", "wall_art", "table_picture", "plant_floor", "plant_small",
         "table_arrangement", "floor_vase", "picture_trio"]

# a primary widget each kind's dialog offers, used to drive a real edit
REP_KEY = {
    "corner_desk": "hand", "armchair": "width_in", "umbrella_table": "size_in",
    "large_tv": "size_in", "wicker_chair": "height_in",
    "wicker_chair_small": "height_in", "wicker_loveseat": "seats",
    "wicker_table": "width_in", "bathtub": "tub_style", "wall_art": "art",
    "table_picture": "art", "plant_floor": "height_in", "plant_small": "height_in",
    "table_arrangement": "height_in", "floor_vase": "vase_fill",
    "picture_trio": "trio_order",
}


def _bump(widget):
    """Move a dialog widget off its current value, staying in range."""
    if hasattr(widget, "currentIndex"):                  # a combo (ENUM)
        n = widget.count()
        assert n > 1, "enum has nothing else to pick"
        widget.setCurrentIndex((widget.currentIndex() + 1) % n)
    elif hasattr(widget, "value"):                       # a spin box (FLOAT/INT)
        step = widget.singleStep() or 1
        if widget.value() + step <= widget.maximum():
            widget.setValue(widget.value() + step)
        else:
            widget.setValue(widget.value() - step)
    else:
        raise AssertionError(f"unknown widget type: {widget!r}")


@pytest.mark.parametrize("kind", KINDS)
def test_kind_places_opens_a_dialog_and_round_trips(fp, qapp, scene, kind):
    it = fp.make_furnishing(kind, QPointF(0, 0))
    scene.addItem(it)
    assert it.is_parametric()
    assert it.extra_state() == {}                        # untouched: its preset
    dlg = it.make_properties_dialog()
    assert dlg is not None and dlg._derived["parts"]
    key = REP_KEY[kind]
    assert key in dlg._widgets, (kind, key)
    _bump(dlg._widgets[key])
    assert dlg.try_accept()                              # advisories never block
    it.apply_params(dlg.result_state())
    state = it.extra_state()
    assert state, f"{kind}: an edit must record state"
    again = fp.make_furnishing(kind, QPointF(0, 0), 0.0, state)
    assert again.extra_state() == state                  # saves and loads
    assert (again.w, again.d) == (it.w, it.d)            # footprint reproduces
    dlg.deleteLater()


@pytest.mark.io
def test_kind_state_reaches_the_document(fp, qapp, win):
    for kind in ("corner_desk", "bathtub", "picture_trio", "floor_vase"):
        it = fp.make_furnishing(kind, QPointF(60, 60))
        win.scene.addItem(it)
        dlg = it.make_properties_dialog()
        _bump(dlg._widgets[REP_KEY[kind]])
        dlg.try_accept()
        it.apply_params(dlg.result_state())
        dlg.deleteLater()
    recs = {f["kind"]: f for f in win.snapshot()["furnishings"]}
    for kind in ("corner_desk", "bathtub", "picture_trio", "floor_vase"):
        assert recs[kind]["state"], f"{kind}: state missing from the document"


@pytest.mark.parametrize("kind", ["armchair", "wicker_chair", "corner_desk"])
def test_no_state_loads_and_saves_with_no_state(fp, qapp, kind):
    it = fp.make_furnishing(kind, QPointF(0, 0))
    assert it.extra_state() == {}
    again = fp.make_furnishing(kind, QPointF(0, 0), 0.0, it.extra_state())
    assert again.extra_state() == {}
    assert (again.w, again.d) == (it.w, it.d)


def test_corner_desk_plan_symbol_turns_with_its_hand(fp, qapp):
    """0376 O4: the return swaps side when `hand` is edited on the item."""
    left = fp.make_furnishing("corner_desk", QPointF(0, 0), 0.0, {"hand": "left"})
    right = fp.make_furnishing("corner_desk", QPointF(0, 0), 0.0, {"hand": "right"})
    kind = registry.get("corner_desk")
    assert kind.plan_symbol(left.draft_state()) != kind.plan_symbol(right.draft_state())


def test_umbrella_table_footprint_follows_size_in(fp, qapp):
    """0376 O4: editing the table size through the item grows its footprint."""
    it = fp.make_furnishing("umbrella_table", QPointF(0, 0))
    it.apply_params({"size_in": 36.0})
    small = (it.w, it.d)
    it.apply_params({"size_in": 60.0})
    assert it.w > small[0] and it.d > small[1]


def test_picture_trio_plan_symbol_turns_with_its_order(fp, qapp):
    """0377 O3: the three frames reorder when `trio_order` is edited."""
    asc = fp.make_furnishing("picture_trio", QPointF(0, 0), 0.0,
                             {"trio_order": "ascending"})
    desc = fp.make_furnishing("picture_trio", QPointF(0, 0), 0.0,
                              {"trio_order": "descending"})
    kind = registry.get("picture_trio")
    assert kind.plan_symbol(asc.draft_state()) != kind.plan_symbol(desc.draft_state())
