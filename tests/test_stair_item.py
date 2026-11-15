"""The parametric stair on the plan and its properties dialog (0323).

Three things are pinned here: a stair saved before parameters existed is
UNTOUCHED until it is edited; a parametric stair's footprint, save, load and
undo all follow its parameters; and the dialog's acceptance checkpoint --
errors block, unresolved checks need the acknowledgement, Cancel changes
nothing (STAIRS_FURNISHING_SPECIFICATION.md sec 6.3, sec 9.2).

The dialog is never `exec()`-ed: a modal loop hangs headless. Its checkpoint
is `try_accept()`, which is exactly what OK calls.
"""
import pytest
from PyQt6.QtCore import QPointF

from floorplanner.parametric import findings as F
from floorplanner.parametric import stair_geometry as sg

pytestmark = pytest.mark.furnishings

LEGACY = {"flight": "full", "turn": "left", "direction": "up"}


def _state(**over):
    st = dict(sg.STATE_DEFAULTS)
    st.update(over)
    return st


def _stairs(win, fp):
    return [it for it in win.scene.items() if isinstance(it, fp.StairItem)]


# -- legacy stairs are frozen ------------------------------------------------
def test_a_stair_with_no_parameters_is_the_legacy_stair(fp):
    st = fp.make_furnishing("stairs", QPointF(0, 0))
    assert st.params is None
    assert st.extra_state() == LEGACY
    assert st.n_risers == 14 and st.d == pytest.approx(13 * fp.STAIR_TREAD)
    old = fp.make_furnishing("stairs", QPointF(0, 0), 0.0,
                             {"flight": "half", "turn": "right",
                              "direction": "down"})
    assert old.params is None
    assert old.extra_state() == {"flight": "half", "turn": "right",
                                 "direction": "down"}


def test_looking_at_a_legacy_stair_does_not_convert_it(fp):
    st = fp.StairItem(QPointF(0, 0))
    draft = st.draft_state()
    assert st.params is None, "the draft is a copy; the item is untouched"
    assert draft["rise_mode"] == "detached"
    assert draft["total_rise_in"] == pytest.approx(96.0)
    assert draft["tread_depth_in"] == fp.STAIR_TREAD
    assert (draft["riser_count_mode"], draft["riser_count"]) == ("manual", 14)


def test_accepting_a_legacy_stairs_own_numbers_keeps_its_footprint(fp):
    st = fp.StairItem(QPointF(0, 0))
    before = (st.w, st.d)
    st.apply_params(st.draft_state())
    assert st.params is not None and st.params["type"] == "straight"
    assert (st.w, st.d) == pytest.approx(before)


# -- parametric stairs ---------------------------------------------------------
def test_a_fresh_drop_is_parametric(fp):
    st = fp.make_furnishing("stairs", QPointF(0, 0), new=True)
    assert isinstance(st, fp.StairItem)
    assert st.params is not None and st.params["type"] == "straight"
    assert st.params["tread_depth_in"] == sg.DEFAULT_TREAD_IN
    assert st.extra_state()["type"] == "straight"


def test_footprint_follows_the_parameters(fp):
    st = fp.StairItem(QPointF(0, 0), params=_state())
    assert st.n_risers == 14
    assert (st.w, st.d) == pytest.approx((36.0, 143.0))
    wide = fp.StairItem(QPointF(0, 0), params=_state(type="L", turn_deg=90))
    assert (wide.w, wide.d) == pytest.approx((102.0, 102.0))
    low = fp.StairItem(QPointF(0, 0), params=_state(
        type="U", turn_deg=180, landing_mode="custom", landing_height_in=30.0))
    even = fp.StairItem(QPointF(0, 0), params=_state(type="U", turn_deg=180))
    assert low.d > even.d, "a low landing makes the upper flight overhang"


def test_state_round_trips_and_older_builds_still_get_their_three_keys(fp):
    a = fp.StairItem(QPointF(5, 6), 90.0, params=_state(
        type="U", turn_deg=-180, landing_mode="custom", landing_height_in=30.0))
    state = a.extra_state()
    assert (state["flight"], state["turn"], state["direction"]) == (
        "half", "left", "up")
    b = fp.make_furnishing("stairs", QPointF(5, 6), 90.0, state)
    assert b.params is not None
    assert b.extra_state() == state
    assert (b.w, b.d) == pytest.approx((a.w, a.d))
    assert b.rotation() == 90.0


def test_applying_parameters_keeps_the_foot_where_it_was(fp, scene):
    st = fp.StairItem(QPointF(200, 300), 90.0, params=_state())
    scene.addItem(st)
    foot = st.mapToScene(st._off)
    st.apply_params(_state(tread_depth_in=12.0))
    assert st.d == pytest.approx(13 * 12.0)
    after = st.mapToScene(st._off)
    # the position snaps to the 1 in grid, so the foot holds to within it
    assert after.x() == pytest.approx(foot.x(), abs=1.0)
    assert after.y() == pytest.approx(foot.y(), abs=1.0)


def test_unusable_parameters_leave_a_selectable_placeholder(fp):
    st = fp.StairItem(QPointF(0, 0), params=_state(total_rise_in=7.0))
    assert st.w > 0 and st.d > 0
    assert "double-click" in st.toolTip()


# -- the dialog ----------------------------------------------------------------
def test_only_parametric_kinds_offer_a_dialog(fp, qapp):
    assert fp.make_furnishing("sofa", QPointF(0, 0)).make_properties_dialog() is None
    assert not fp.make_furnishing("sofa", QPointF(0, 0)).is_parametric()
    st = fp.StairItem(QPointF(0, 0), params=_state())
    dlg = st.make_properties_dialog()
    assert dlg is not None and dlg.isModal()
    assert dlg.preview is not None
    dlg.deleteLater()


def test_ok_needs_the_acknowledgement_and_errors_cannot_be_ticked_away(fp, qapp):
    st = fp.StairItem(QPointF(0, 0), params=_state())
    dlg = st.make_properties_dialog()
    assert F.needs_ack(dlg.findings()) and not F.blocks(dlg.findings())
    assert not dlg.try_accept(), "unresolved checks, box not ticked"
    assert dlg.result_state() is None

    dlg.set_value("tread_depth_in", 9.5)
    dlg.ack.setChecked(True)
    assert F.blocks(dlg.findings())
    assert not dlg.try_accept(), "an error is not something to acknowledge"
    assert dlg.result_state() is None

    dlg.set_value("tread_depth_in", 11.0)
    dlg.ack.setChecked(True)
    assert dlg.try_accept()
    result = dlg.result_state()
    assert result["tread_depth_in"] == 11.0
    assert "headroom.min" in result["acknowledged"]
    assert st.params["tread_depth_in"] == 11.0 and "acknowledged" not in st.params, \
        "the dialog edits a draft; only apply_params changes the item"
    dlg.deleteLater()


def test_edits_update_the_calculation_live(fp, qapp):
    st = fp.StairItem(QPointF(0, 0), params=_state())
    dlg = st.make_properties_dialog()
    tread = dlg._widgets["tread_depth_in"]
    tread.setValue(12.0)                     # as typed: the widget's own signal
    assert dlg._derived.total_run == pytest.approx(13 * 12.0)
    assert dlg._derived.total_rise == pytest.approx(108.0), "run changed, rise did not"

    mode = dlg._widgets["riser_count_mode"]
    count = dlg._widgets["riser_count"]
    assert not count.isEnabled() and count.value() == 14     # showing the auto count
    mode.setCurrentIndex(mode.findData("manual"))
    assert count.isEnabled() and dlg.values["riser_count"] == 14
    count.setValue(13)
    assert dlg._derived.riser_count == 13 and F.blocks(dlg.findings())
    mode.setCurrentIndex(mode.findData("auto"))
    assert dlg._derived.riser_count == 14 and not F.blocks(dlg.findings())
    dlg.deleteLater()


def test_type_drives_the_turn_and_landing_fields(fp, qapp):
    st = fp.StairItem(QPointF(0, 0), params=_state())
    dlg = st.make_properties_dialog()
    turn = dlg._widgets["turn_deg"]
    landing = dlg._widgets["landing_height_in"]
    assert not turn.isEnabled() and not landing.isEnabled()
    kind = dlg._widgets["type"]
    kind.setCurrentIndex(kind.findData("U"))
    assert turn.isEnabled()
    assert sorted(turn.itemData(i) for i in range(turn.count())) == [-180, 180]
    assert dlg._derived.landing_height == pytest.approx(54.0)
    assert landing.value() == pytest.approx(54.0) and not landing.isEnabled()
    lmode = dlg._widgets["landing_mode"]
    lmode.setCurrentIndex(lmode.findData("custom"))
    assert landing.isEnabled()
    landing.setValue(30.0)
    assert dlg._derived.landing_risers == 4
    dlg.deleteLater()


def test_reset_and_cancel_leave_the_item_alone(fp, qapp):
    st = fp.StairItem(QPointF(0, 0), params=_state())
    before = st.extra_state()
    dlg = st.make_properties_dialog()
    dlg.set_value("stair_width_in", 48.0)
    dlg.reset()
    assert dlg.values["stair_width_in"] == 36.0
    dlg.set_value("stair_width_in", 48.0)
    dlg.reject()
    assert dlg.result_state() is None
    assert st.extra_state() == before
    dlg.deleteLater()


# -- the document --------------------------------------------------------------
@pytest.mark.io
def test_parameters_are_written_in_the_furnishing_state(fp, qapp, win):
    st = fp.StairItem(QPointF(60, 60), params=_state(type="L", turn_deg=90))
    win.scene.addItem(st)
    recs = [f for f in win.snapshot()["furnishings"] if f["kind"] == "stairs"]
    assert len(recs) == 1
    state = recs[0]["state"]
    assert state["type"] == "L" and state["turn_deg"] == 90
    assert state["tread_depth_in"] == 11.0
    for derived in ("riser_height", "tread_count", "total_run", "pitch_degrees"):
        assert derived not in state, "only controlling values are stored"


@pytest.mark.io
def test_parametric_stair_survives_save_load(fp, qapp, win):
    st = fp.StairItem(QPointF(60, 60), 90.0, params=_state(
        type="U", turn_deg=180, landing_mode="custom", landing_height_in=40.0))
    win.scene.addItem(st)
    want, size = st.extra_state(), (st.w, st.d)
    win.load_data(win.serialize())
    stairs = _stairs(win, fp)
    assert len(stairs) == 1
    assert stairs[0].extra_state() == want
    assert (stairs[0].w, stairs[0].d) == pytest.approx(size)


def test_accepted_parameters_are_one_undo_step(fp, qapp, win):
    st = fp.StairItem(QPointF(60, 60), params=_state())
    win.scene.addItem(st)
    win._commit_if_changed()
    st.apply_params(_state(tread_depth_in=12.0))
    win._commit_if_changed()
    assert _stairs(win, fp)[0].d == pytest.approx(156.0)
    win.undo()
    back = _stairs(win, fp)
    assert len(back) == 1
    assert back[0].params["tread_depth_in"] == 11.0
    assert back[0].d == pytest.approx(143.0)
