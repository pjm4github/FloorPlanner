"""P4 of the 1½-storey arc (0296): the `dormer` wall type. A dormer mints three
walls -- face, cheek_left, cheek_right -- as real `dormer`-type `WallItem`s on
the storey ABOVE the host, bound to it, so the attic room closes against them;
they are editable only from the dormer and round-trip with `bound_to`.
"""
import pytest

from floorplanner.design.bridge import apply_design_to_scene
from floorplanner.design.validate import schema_errors
from floorplanner.roofs import RoofItem
from floorplanner.walls import WallItem

pytestmark = pytest.mark.gui


def _doc(two_levels=True):
    # a dormer rf2 (host rf1) on L1, with an L2 above it, plus L1 walls forming a
    # room under it so there is a plan to close against
    V = [{"id": f"v{i}", "x": x, "y": y} for i, (x, y) in enumerate(
        [(0, 0), (400, 0), (400, 300), (0, 300)])]
    walls = [{"id": f"w{i}", "level": "L1", "v1": f"v{i}", "v2": f"v{(i + 1) % 4}",
              "type": "exterior"} for i in range(4)]
    host = {"id": "rf1", "level": "L1", "ridge": [[-40, 150], [440, 150]],
            "eaves_h_in": 96.0, "ridge_h_in": 300.0, "overhang_in": [0, 0],
            "span_in": [170, 170], "gable": [True, True], "marker_end": 1}
    dormer = {"id": "rf2", "level": "L1", "ridge": [[200, 300], [200, 220]],
              "eaves_h_in": 180.0, "ridge_h_in": 240.0, "overhang_in": [0, 0],
              "span_in": [40, 40], "wall_span_in": [40, 40], "gable": [True, True],
              "marker_end": 0, "host": "rf1"}
    levels = [{"id": "L1", "name": "L1", "elevation_in": 0.0, "height_in": 96.0,
               "kind": "storey", "reference": False}]
    if two_levels:
        levels.append({"id": "L2", "name": "L2", "elevation_in": 96.0,
                       "height_in": 96.0, "kind": "storey", "reference": False})
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {}, "levels": levels, "vertices": V, "walls": walls,
            "rooms": [], "furnishings": [], "groups": [], "roofs": [host, dormer]}


def _dormer(win, two_levels=True):
    win.prepare_headless()
    apply_design_to_scene(win, _doc(two_levels))
    return next(it for it in win.scene.items()
                if isinstance(it, RoofItem) and it.is_dormer())


def _dormer_walls(scene):
    return [w for w in scene.items()
            if isinstance(w, WallItem) and w.wall_type == "dormer"]


def test_a_dormer_mints_three_walls_on_the_storey_above(fp, win):
    d = _dormer(win)
    dw = _dormer_walls(win.scene)
    assert {w.bound_part for w in dw} == {"face", "cheek_left", "cheek_right"}
    assert all(w.floor == "L2" for w in dw)            # the storey above the host
    assert all(w.bound_to_roof is d for w in dw)


def test_no_walls_on_a_one_layer_plan(fp, win):
    _dormer(win, two_levels=False)                     # no storey above exists
    assert _dormer_walls(win.scene) == []


def test_the_dormer_walls_are_read_only(fp, win):
    _dormer(win)
    from PyQt6.QtWidgets import QGraphicsItem
    for w in _dormer_walls(win.scene):
        assert not (w.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)


def test_bound_to_round_trips_and_validates(fp, win):
    _dormer(win)
    out = win.design_document()
    dw = [w for w in out["walls"] if w.get("type") == "dormer"]
    assert len(dw) == 3
    assert all(w["bound_to"]["roof"] and w["bound_to"]["part"] for w in dw)
    assert not schema_errors(out)                      # bound_to required & present


def test_reload_adopts_the_walls_not_duplicates(fp, win2=None):
    # first window mints; a second loads the serialized doc and must not double
    import FloorPlanner as _fp
    w1 = _fp.MainWindow()
    _dormer(w1)
    out = w1.design_document()
    w2 = _fp.MainWindow()
    w2.load_data(out)
    dw = _dormer_walls(w2.scene)
    assert len(dw) == 3                                 # adopted, not 6
    assert all(getattr(w, "bound_to_roof", None) is not None for w in dw)


def test_deleting_the_dormer_removes_its_walls(fp, win):
    d = _dormer(win)
    assert len(_dormer_walls(win.scene)) == 3
    d.remove_with_dormers()
    assert _dormer_walls(win.scene) == []


def test_a_wall_can_be_opted_out_and_the_choice_round_trips(fp, win):
    """0296: the dialog's three checkboxes. A wall turned off is not minted, and
    the choice survives a save/reload (written as `dormer_walls`)."""
    import FloorPlanner as _fp
    d = _dormer(win)
    d.dormer_wall_parts = {"cheek_left", "cheek_right"}      # face off
    d.rebuild()
    assert {w.bound_part for w in _dormer_walls(win.scene)} == {"cheek_left", "cheek_right"}
    out = win.design_document()
    dormer_rec = next(r for r in out["roofs"] if r.get("host"))
    assert sorted(dormer_rec["dormer_walls"]) == ["cheek_left", "cheek_right"]
    w2 = _fp.MainWindow()
    w2.load_data(out)
    assert {w.bound_part for w in _dormer_walls(w2.scene)} == {"cheek_left", "cheek_right"}


def test_all_walls_on_writes_no_dormer_walls_key(fp, win):
    _dormer(win)                                            # default: all three on
    out = win.design_document()
    dormer_rec = next(r for r in out["roofs"] if r.get("host"))
    assert "dormer_walls" not in dormer_rec                 # clean record when all on


def test_undo_of_a_dormer_edit_does_not_duplicate_the_walls(fp):
    """0296's undo note: a dormer edit now writes to the walls on another floor,
    which are derived AND serialized. Undo must not leave a restored wall beside a
    re-minted one (the "resurrected wall"). A plan with dormer walls reloads in
    full on undo, which adopts them -- so the count stays 3."""
    import FloorPlanner as _fp
    win = _fp.MainWindow()
    d = _dormer(win)
    win._commit_if_changed()                                # baseline
    assert len(_dormer_walls(win.scene)) == 3
    d.ridge_h_in = 250.0
    d.rebuild()
    win._commit_if_changed()                                # the edit, an undo step
    win.undo()
    assert len(_dormer_walls(win.scene)) == 3               # not 6
