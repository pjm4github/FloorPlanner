"""Qt-free tests for the plain-Python domain model (model.py).

The whole point of the model layer is that the JSON schema + its load-time
migration are testable WITHOUT a QApplication, so these import only `model`.
"""
import copy

import pytest

from floorplanner import model
from floorplanner.model import (DEFAULT_FLOOR, FILE_FORMAT, FILE_VERSION, Floor,
                                Furnishing, Opening, Project, Wall)

pytestmark = pytest.mark.io


def _sample_dict() -> dict:
    """A representative plan dict in the canonical (serialize) shape — arrays
    already sorted exactly as Project.to_dict / the legacy serialize emit them
    (walls by p1,p2,type,rooms; rooms by name; furnishings by pos,kind,rot)."""
    return {
        "format": FILE_FORMAT,
        "version": FILE_VERSION,
        "units": "inches",
        "settings": {"wall_snap_in": 6.0, "auto_coalesce": True},
        "floors": [{"name": "default", "reference": False},
                   {"name": "Upper", "reference": True}],
        "walls": [
            {"type": "interior", "p1": [0.0, 0.0], "p2": [0.0, 96.0],
             "rooms": ["Bath", "Kitchen"], "openings": [], "floor": "default"},
            {"type": "exterior", "p1": [0.0, 0.0], "p2": [120.0, 0.0],
             "rooms": ["Kitchen"], "openings": [
                 {"kind": "door", "code": "3280", "s": 30.0,
                  "door_type": "LH", "swing": -1},
                 {"kind": "window", "code": "3040", "s": 90.0,
                  "door_type": "LH", "swing": 1}], "floor": "Upper"},
        ],
        "rooms": [
            {"name": "Bath", "anchor": [10.0, 20.0],
             "label_offset": [1.0, 2.0], "show_dimensions": True,
             "properties": {"floor_finish": "Tile"}, "floor": "default"},
            {"name": "Kitchen", "anchor": [60.0, 48.0],
             "label_offset": [0.0, 0.0], "show_dimensions": False,
             "properties": None, "floor": "Upper"},
        ],
        "furnishings": [
            {"kind": "sofa", "pos": [40.0, 40.0], "rotation": 0.0,
             "floor": "default"},
            {"kind": "stairs", "pos": [80.0, 10.0], "rotation": 90.0,
             "floor": "Upper", "flight": "half", "turn": "left",
             "direction": "up"},
        ],
    }


def test_round_trip_is_identity():
    d = _sample_dict()
    out = Project.from_dict(copy.deepcopy(d)).to_dict()
    assert out == d


def test_to_dict_sorts_z_independently():
    """Item order in the model must not affect the serialized output, so a
    z-reorder (which reorders scene.items()) never dirties the snapshot."""
    d = _sample_dict()
    proj = Project.from_dict(copy.deepcopy(d))
    proj.walls.reverse()
    proj.rooms.reverse()
    proj.furnishings.reverse()
    assert proj.to_dict() == d


def test_openings_emitted_sorted_along_wall():
    w = Wall(p1=(0.0, 0.0), p2=(120.0, 0.0), openings=[
        Opening("door", "3280", 90.0), Opening("door", "3280", 10.0)])
    assert [o["s"] for o in w.to_dict()["openings"]] == [10.0, 90.0]


def test_rooms_list_emitted_sorted():
    w = Wall(p1=(0.0, 0.0), p2=(10.0, 0.0), rooms=["Zed", "Alpha"])
    assert w.to_dict()["rooms"] == ["Alpha", "Zed"]


def test_furnishing_extra_round_trips():
    f = Furnishing.from_dict({"kind": "stairs", "pos": [1.0, 2.0],
                              "rotation": 0.0, "flight": "full",
                              "turn": "right", "direction": "down"})
    assert f.extra == {"flight": "full", "turn": "right", "direction": "down"}
    assert f.to_dict()["turn"] == "right"


def test_bad_format_raises():
    with pytest.raises(ValueError, match="Not a Floor Planner"):
        Project.from_dict({"format": "something-else"})


def test_v1_file_migrates_to_default_floor():
    """A legacy v1 dict (no floors/floor keys) loads as one default floor with
    every item tagged 'default' — the forward-compat path for the Floors feature."""
    d = {"format": FILE_FORMAT, "version": 1, "units": "inches",
         "settings": {}, "walls": [
             {"type": "interior", "p1": [0, 0], "p2": [10, 0]}],
         "rooms": [{"name": "R", "anchor": [5, 5]}],
         "furnishings": [{"kind": "sofa", "pos": [1, 1]}]}
    proj = Project.from_dict(d)
    assert proj.version == 1
    assert [f.name for f in proj.floors] == [DEFAULT_FLOOR]
    assert proj.active_floor == DEFAULT_FLOOR
    assert proj.walls[0].floor == DEFAULT_FLOOR
    assert proj.rooms[0].floor == DEFAULT_FLOOR
    assert proj.furnishings[0].floor == DEFAULT_FLOOR


def test_floors_emitted_but_active_floor_is_not():
    """v4 emits the floor roster + per-item floor, but NOT active_floor (view
    state) — so a floor switch can't change the snapshot."""
    proj = Project.from_dict(_sample_dict())
    proj.floors = [Floor("default"), Floor("Upper", reference=True)]
    proj.active_floor = "Upper"
    out = proj.to_dict()
    assert out["floors"] == [{"name": "default", "reference": False},
                             {"name": "Upper", "reference": True}]
    assert "active_floor" not in out
    assert all("floor" in w for w in out["walls"])
    assert all("floor" in r for r in out["rooms"])
    assert all("floor" in f for f in out["furnishings"])


def test_opening_default_s_is_half_wall():
    d = {"format": FILE_FORMAT, "version": FILE_VERSION, "units": "inches",
         "settings": {}, "walls": [
             {"type": "interior", "p1": [0, 0], "p2": [100, 0],
              "openings": [{"kind": "door", "code": "3280"}]}],
         "rooms": [], "furnishings": []}
    proj = Project.from_dict(d)
    assert proj.walls[0].openings[0].s == 50.0


def test_module_constants_match_app():
    assert model.FILE_FORMAT == "floorplanner-json"
    assert isinstance(model.FILE_VERSION, int)
