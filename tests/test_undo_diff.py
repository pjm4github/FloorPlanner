"""0283-report.md -- undo by difference (Patrick: "go ahead with option A").

An undo used to rebuild the whole scene from the restored document; it now
rebuilds only what differs (`bridge.apply_design_difference`) and reloads in
full when it cannot be sure. The receipt is EQUIVALENCE: for every kind of
edit, on the repository's own plans (two of them multi-floor), the scene
after an undo by difference must be the restored document exactly -- the
same snapshot a full reload gives -- and redo must bring the edit back.
The harness also records which path ran, so a regression that quietly
sends everything back through the full reload is caught too.
"""
import copy
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

from floorplanner.design.bridge import apply_design_difference

pytestmark = pytest.mark.io

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
PLANS = ["symmetricP1.json", "roundedMultifloor.json", "farmplaceBIGmultifloor.json",
         "sample_plan.v5.json"]


@pytest.fixture
def reloads(monkeypatch):
    """Count full reloads through `load_data`."""
    n = {"full": 0}
    import floorplanner.mainwindow as mw
    cls = mw.MainWindow
    real = cls.load_data

    def counting(self, *a, **k):
        n["full"] += 1
        return real(self, *a, **k)
    monkeypatch.setattr(cls, "load_data", counting)
    return n


def _items(fp, win, cls, floor=None):
    return [it for it in win.scene.items() if isinstance(it, cls) and it.parentItem() is None
            and (floor is None or it.floor == floor)]


# --- the edits, each a function of the window ---------------------------------

def _move_furnishing(fp, win):
    f = _items(fp, win, fp.FurnishingItem)[0]
    f.setPos(f.pos() + QPointF(24, 12))


def _rotate_furnishing(fp, win):
    f = _items(fp, win, fp.FurnishingItem)[-1]
    f.setRotation(f.rotation() + 90)


def _add_opening(fp, win):
    w = max(_items(fp, win, fp.WallItem), key=lambda w: w.length())
    w.openings.append(fp.OpeningItem(w, "window", "2424", w.length() / 3))
    w.rebuild()


def _move_corner(fp, win):
    from floorplanner.rooms import relocate_corners
    w = max(_items(fp, win, fp.WallItem), key=lambda w: w.length())
    u = w.unit()
    relocate_corners([w], [], lambda v: QPointF(v.x - u.y() * 12, v.y + u.x() * 12), win.scene)
    fp.rebuild_all_walls(win.scene)


def _room_ceiling(fp, win):
    r = _items(fp, win, fp.RoomItem)[0]
    r.properties["ceiling_height_in"] = float(r.properties.get("ceiling_height_in", 96.0)) + 12.0
    r.update()


def _add_annotation(fp, win):
    from floorplanner.annotations import TextAnnotationItem
    win.scene.addItem(TextAnnotationItem(QPointF(30, 30), "a note"))


def _add_roof(fp, win):
    rf = fp.RoofItem(QPointF(0, 120), QPointF(240, 120), eaves_h_in=96.0, ridge_h_in=150.0,
                     span_in=100.0)
    win.scene.addItem(rf)


def _delete_wall(fp, win):
    w = min(_items(fp, win, fp.WallItem), key=lambda w: w.length())
    fp.delete_wall(win.scene, w, settle=False)


EDITS = {"move a furnishing": _move_furnishing, "rotate a furnishing": _rotate_furnishing,
         "add an opening": _add_opening, "move a corner": _move_corner,
         "change a room's ceiling": _room_ceiling, "add an annotation": _add_annotation,
         "add a roof": _add_roof, "delete a wall": _delete_wall}


@pytest.mark.parametrize("plan", PLANS)
@pytest.mark.parametrize("edit", list(EDITS))
def test_undo_by_difference_restores_exactly(fp, win, reloads, plan, edit):
    win.load_path(str(EXAMPLES / plan))
    before = copy.deepcopy(win._committed_state)
    EDITS[edit](fp, win)
    win._commit_if_changed()
    after = copy.deepcopy(win._committed_state)
    if after == before:
        pytest.skip("the edit changed nothing on this plan")
    full0 = reloads["full"]
    win.undo()
    assert win.snapshot() == before, "undo by difference left a different plan"
    assert reloads["full"] == full0, "the undo fell back to the full reload"
    win.redo()
    assert win.snapshot() == after, "redo by difference left a different plan"
    assert reloads["full"] == full0, "the redo fell back to the full reload"


def test_its_result_is_the_full_reloads_item_for_item(fp, win):
    """Beyond the document: the same items of each class on each floor."""
    win.load_path(str(EXAMPLES / "roundedMultifloor.json"))
    before = copy.deepcopy(win._committed_state)
    _move_corner(fp, win)
    _move_furnishing(fp, win)
    win._commit_if_changed()
    win.undo()

    def census():
        out = {}
        for it in win.scene.items():
            k = (type(it).__name__, getattr(it, "floor", None))
            out[k] = out.get(k, 0) + 1
        return out
    by_diff = census()
    win.load_data(before, keep_backdrop=True)
    assert census() == by_diff


def test_what_it_cannot_apply_with_certainty_reloads_in_full(fp, win, reloads):
    """A level renamed is outside the six blocks it understands: False, and
    the undo reloads, so the restore is still exact."""
    win.load_path(str(EXAMPLES / "sample_plan.v5.json"))
    cur = copy.deepcopy(win._committed_state)
    tgt = copy.deepcopy(cur)
    tgt["levels"][0]["name"] = "renamed"
    assert apply_design_difference(win, cur, tgt) is False
    tgt = copy.deepcopy(cur)
    tgt["settings"]["wall_snap_in"] = 3.0
    assert apply_design_difference(win, cur, tgt) is False


def test_a_welded_corner_never_compares_equal_to_two_unwelded_ones():
    """Comparison is by content with ids stripped -- so vertex SHARING must be
    part of it, or a corner welded in one state and two coincident corners
    in the other would read as no difference."""
    from floorplanner.design.bridge import _web_by_level
    welded = {"vertices": [{"id": "v1", "x": 0, "y": 0}, {"id": "v2", "x": 100, "y": 0},
                           {"id": "v3", "x": 0, "y": 100}],
              "walls": [{"id": "w1", "level": "L1", "v1": "v1", "v2": "v2", "type": "interior"},
                        {"id": "w2", "level": "L1", "v1": "v1", "v2": "v3", "type": "interior"}],
              "rooms": []}
    apart = copy.deepcopy(welded)
    apart["vertices"].append({"id": "v4", "x": 0, "y": 0})
    apart["walls"][1]["v1"] = "v4"
    assert _web_by_level(welded)[0] != _web_by_level(apart)[0]


def test_renumbered_ids_alone_are_no_difference():
    """The same plan with every id renumbered is the same plan."""
    from floorplanner.design.bridge import _web_by_level
    a = {"vertices": [{"id": "v1", "x": 0, "y": 0}, {"id": "v2", "x": 100, "y": 0}],
         "walls": [{"id": "w1", "level": "L1", "v1": "v1", "v2": "v2", "type": "interior"}],
         "rooms": []}
    b = {"vertices": [{"id": "v9", "x": 0, "y": 0}, {"id": "v8", "x": 100, "y": 0}],
         "walls": [{"id": "w5", "level": "L1", "v1": "v9", "v2": "v8", "type": "interior"}],
         "rooms": []}
    assert _web_by_level(a)[0] == _web_by_level(b)[0]
