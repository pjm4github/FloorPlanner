"""0368 — the four kitchen-casework kinds in the editor (Qt side; ruling O4).

Each of `tall_cab`, `kitchen_desk`, `corner_wall_cab`, `ceiling_cab` placed on
the canvas, its dialog opened, its state saved and loaded; `is_casework` true
for all four, and the new state keys (stands / wings / doors 3-4 / the ceiling
light) are wired. The Qt-free parts are `tests/test_kitchen_casework.py`.
A dialog is never `exec()`-ed headless; `try_accept()` is what OK calls.
"""
import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.furnishings

CASEWORK = ["tall_cab", "kitchen_desk", "corner_wall_cab", "ceiling_cab"]


@pytest.mark.parametrize("kind", CASEWORK)
def test_casework_places_opens_a_dialog_and_is_casework(fp, qapp, scene, kind):
    it = fp.make_furnishing(kind, QPointF(0, 0))
    scene.addItem(it)
    assert fp.is_casework(kind) and it.is_parametric()
    assert it.extra_state() == {}                     # untouched: its preset
    dlg = it.make_properties_dialog()
    assert dlg is not None and dlg._derived["parts"]
    assert dlg.try_accept()                           # advisories never block
    it.apply_params(dlg.result_state())
    assert it.extra_state() == {}
    dlg.deleteLater()


@pytest.mark.parametrize("kind", CASEWORK)
def test_casework_state_saves_and_loads(fp, qapp, kind):
    it = fp.make_furnishing(kind, QPointF(0, 0))
    it.apply_params({"finish": "walnut"})
    state = it.extra_state()
    assert state == {"finish": "walnut"}              # only what differs
    again = fp.make_furnishing(kind, QPointF(0, 0), 0.0, state)
    assert again.extra_state() == state
    assert (again.w, again.d) == (it.w, it.d)


@pytest.mark.io
def test_casework_state_reaches_the_document(fp, qapp, win):
    for kind in CASEWORK:
        it = fp.make_furnishing(kind, QPointF(60, 60))
        win.scene.addItem(it)
        it.apply_params({"finish": "oak"})
    recs = {f["kind"]: f for f in win.snapshot()["furnishings"]}
    for kind in CASEWORK:
        assert recs[kind]["state"] == {"finish": "oak"}


def test_tall_cabinet_can_stand_on_a_counter(fp, qapp):
    it = fp.make_furnishing("tall_cab", QPointF(0, 0))
    dlg = it.make_properties_dialog()
    stands = dlg._widgets["stands"]
    stands.setCurrentIndex(stands.findData("counter"))
    assert dlg.try_accept()
    it.apply_params(dlg.result_state())
    assert it.extra_state() == {"stands": "counter"}
    dlg.deleteLater()


def test_corner_wall_cabinet_has_wings(fp, qapp):
    it = fp.make_furnishing("corner_wall_cab", QPointF(0, 0))
    dlg = it.make_properties_dialog()
    assert "wing_in" in dlg._widgets
    dlg._widgets["wing_in"].setValue(30.0)
    assert dlg.try_accept()
    it.apply_params(dlg.result_state())
    assert it.extra_state().get("wing_in") == pytest.approx(30.0)
    dlg.deleteLater()


def test_ceiling_cabinet_offers_three_four_doors_and_a_light(fp, qapp, scene,
                                                             make_room):
    room = make_room(scene, 0, 0, 240, 240, "Kitchen")
    room.properties["ceiling_height_in"] = 96.0
    it = fp.make_furnishing("ceiling_cab", QPointF(120, 120))
    scene.addItem(it)
    dlg = it.make_properties_dialog()
    doors = dlg._widgets["doors"]
    assert doors.findData("3") >= 0 and doors.findData("4") >= 0
    light = dlg._widgets["under_light"]        # toggle off its preset default
    light.setChecked(not light.isChecked())
    assert dlg.try_accept()
    it.apply_params(dlg.result_state())
    assert it.extra_state().get("under_light") is False
    dlg.deleteLater()
