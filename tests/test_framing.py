"""Framing category: the dynamic StairItem (step count from room ceiling
height, full/half flights, turn direction, up/down arrow) and the elevator.
Persistence of stair state through save/load and the make_furnishing
factory."""

import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.furnishings


def test_framing_catalog_and_group(fp):
    for fid in ("stairs", "elevator"):
        spec = fp.furnishing_spec(fid)
        assert spec is not None and spec["category"] == "Framing"
    groups = {g["name"]: [s["id"] for s in g["specs"]]
              for g in fp.furnishing_groups()}
    assert groups.get("Framing") == ["stairs", "elevator"]


def test_factory_returns_right_types(fp):
    st = fp.make_furnishing("stairs", QPointF(0, 0))
    assert isinstance(st, fp.StairItem)
    el = fp.make_furnishing("elevator", QPointF(0, 0))
    assert isinstance(el, fp.FurnishingItem) and not isinstance(el,
                                                                fp.StairItem)


def test_step_count_defaults_without_room(fp):
    st = fp.StairItem(QPointF(0, 0))
    # not in a scene/room -> default 96" ceiling -> round(96/7) = 14 risers
    assert st.n_risers == 14


def test_step_count_scales_with_ceiling(fp, scene, make_room):
    room = make_room(scene, 0, 0, 240, 240, "Foyer")
    room.properties["ceiling_height_in"] = 120.0
    st = fp.make_furnishing("stairs", QPointF(120, 120))
    scene.addItem(st)           # ItemSceneHasChanged triggers a recompute
    assert st.n_risers == round(120 / fp.STAIR_RISER)   # 17


def test_full_vs_half_footprint(fp):
    full = fp.StairItem(QPointF(0, 0), flight="full")
    half = fp.StairItem(QPointF(0, 0), flight="half", turn="right")
    # a right turn makes the half flight L-shaped: wider, shorter than full
    assert half.w > full.w
    assert half.d < full.d


def test_extra_state_round_trips(fp):
    st = fp.StairItem(QPointF(0, 0), flight="half", turn="right",
                      direction="down")
    state = st.extra_state()
    assert state == {"flight": "half", "turn": "right", "direction": "down"}
    rebuilt = fp.make_furnishing("stairs", QPointF(0, 0), 90.0, state)
    assert rebuilt.extra_state() == state
    assert rebuilt.rotation() == 90.0


def test_invalid_state_falls_back_to_defaults(fp):
    st = fp.StairItem(QPointF(0, 0), flight="bogus", turn="x", direction="z")
    assert st.flight == "full"
    assert st.turn == "left"
    assert st.direction == "up"


@pytest.mark.io
def test_stair_survives_save_load(fp, qapp, win):
    st = fp.make_furnishing("stairs", QPointF(60, 60))
    st.flight, st.turn, st.direction = "half", "right", "down"
    st._recompute()
    win.scene.addItem(st)
    win.load_data(win.serialize())
    stairs = [it for it in win.scene.items() if isinstance(it, fp.StairItem)]
    assert len(stairs) == 1
    assert stairs[0].extra_state() == {"flight": "half", "turn": "right",
                                       "direction": "down"}
