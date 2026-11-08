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


def test_a_welded_knee_wall_follows_the_cheek_when_the_dormer_moves(fp, win):
    """0296 §2 -- WELD / deform-to-follow: a hand-drawn L2 wall whose end sits on a
    dormer cheek's back end SHARES that cheek's `Vertex`, and FOLLOWS the cheek
    when the dormer moves. The sync re-derives the cheek's vertices; it must
    RELOCATE a shared corner (carrying every holder) rather than detach it onto a
    fresh one (which would strand the knee wall at the old spot)."""
    from PyQt6.QtCore import QPointF
    from floorplanner.walls import share_coincident_ends
    d = _dormer(win)
    cheek = next(w for w in _dormer_walls(win.scene) if w.bound_part == "cheek_left")
    back = cheek.p2                                    # the up-slope back end
    knee = WallItem(QPointF(back), QPointF(back.x() + 40, back.y() + 40), "interior")
    knee.floor = cheek.floor                           # the storey above (L2)
    win.scene.addItem(knee)
    share_coincident_ends(win.scene, cheek.floor)      # weld: fold onto one Vertex
    assert knee.end_vertex("p1") is cheek.end_vertex("p2"), "not welded"

    d.set_ridge(QPointF(d.p1.x() + 20, d.p1.y()), QPointF(d.p2.x() + 20, d.p2.y()))
    d.rebuild()                                         # moves the cheek + its sync
    new_back = cheek.p2
    assert (new_back.x(), new_back.y()) != (back.x(), back.y())    # the cheek moved
    # the knee's welded end tracked the cheek, and still shares its corner
    assert knee.p1.x() == pytest.approx(new_back.x())
    assert knee.p1.y() == pytest.approx(new_back.y())
    assert knee.end_vertex("p1") is cheek.end_vertex("p2")


def test_a_welded_knee_wall_survives_a_save_and_reload(fp, win):
    """0296 §2 receipt: save -> reload -> the walls are still bound AND the welded
    knee wall still shares the cheek's back-end corner, so it follows again. The
    shared `Vertex` serializes to ONE document vertex, re-shared on load."""
    from PyQt6.QtCore import QPointF
    from floorplanner.walls import share_coincident_ends
    import FloorPlanner as _fp
    _dormer(win)
    cheek = next(w for w in _dormer_walls(win.scene) if w.bound_part == "cheek_left")
    back = cheek.p2
    knee = WallItem(QPointF(back), QPointF(back.x() + 40, back.y() + 40), "interior")
    knee.floor = cheek.floor
    win.scene.addItem(knee)
    share_coincident_ends(win.scene, cheek.floor)
    out = win.design_document()

    w2 = _fp.MainWindow()
    w2.load_data(out)
    cheek2 = next(w for w in w2.scene.items()
                  if isinstance(w, WallItem) and w.wall_type == "dormer"
                  and w.bound_part == "cheek_left")
    knee2 = next(w for w in w2.scene.items()
                 if isinstance(w, WallItem) and w.wall_type != "dormer"
                 and w.floor == cheek2.floor)
    assert knee2.end_vertex("p1") is cheek2.end_vertex("p2"), "weld lost on reload"
    # and it still follows a move in the reloaded plan
    d2 = next(it for it in w2.scene.items()
              if isinstance(it, RoofItem) and it.is_dormer())
    d2.set_ridge(QPointF(d2.p1.x() + 20, d2.p1.y()), QPointF(d2.p2.x() + 20, d2.p2.y()))
    d2.rebuild()
    assert knee2.p1.x() == pytest.approx(cheek2.p2.x())
    assert knee2.p1.y() == pytest.approx(cheek2.p2.y())


def test_a_free_dormer_wall_end_detaches_to_a_fresh_corner(fp, win):
    """The non-welded default is unchanged: a cheek end with no wall on it is
    DETACHED to a derived corner (a fresh `Vertex`), so a dormer with no welded
    knee wall syncs exactly as before the weld path existed."""
    from PyQt6.QtCore import QPointF
    d = _dormer(win)
    cheek = next(w for w in _dormer_walls(win.scene) if w.bound_part == "cheek_left")
    v_before = cheek.end_vertex("p2")
    d.set_ridge(QPointF(d.p1.x() + 15, d.p1.y()), QPointF(d.p2.x() + 15, d.p2.y()))
    d.rebuild()
    assert cheek.end_vertex("p2") is not v_before      # a fresh, detached corner


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
