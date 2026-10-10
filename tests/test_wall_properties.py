"""The wall-properties dialog (Patrick, 2026-10-10): double-click a wall, see
all its properties, edit its name, its type and its end points -- each end's
name and x/y, in inches or feet-and-inches -- with a checkbox, on by default,
that carries every wall and room outline joined at a moved corner along.
Cancel leaves the wall as it was. A profile view has its place but is not
built.
"""
import pytest
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QDialog

from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
from floorplanner.design.model import Design
from floorplanner.design.validate import schema_errors
from floorplanner.wallprops import (
    WallProfileView, WallPropertiesDialog, length_text, parse_length,
)

pytestmark = pytest.mark.walls


# --------------------------------------------------------------------------
# lengths
# --------------------------------------------------------------------------
@pytest.mark.parametrize("text, inches", [
    ("120", 120.0), ("10.5", 10.5), ("-6", -6.0),
    ("10'", 120.0), ("10'6\"", 126.0), ("10' 6\"", 126.0), ("10'-6\"", 126.0), ("30\"", 30.0),
])
def test_a_plain_number_is_inches_and_a_mark_means_feet_and_inches(text, inches):
    assert parse_length(text) == inches


@pytest.mark.parametrize("text", ["", "ten", "10'x", "1'2'3"])
def test_a_bad_length_is_refused(text):
    with pytest.raises(ValueError):
        parse_length(text)


def test_the_field_shows_inches_without_trailing_zeros():
    assert length_text(126.0) == "126" and length_text(10.5) == "10.5" and length_text(0.004) == "0"


# --------------------------------------------------------------------------
# the sheet
# --------------------------------------------------------------------------
def _square(fp, win, x0=0.0, y0=0.0, n=240.0):
    """Four exterior walls closing a square, sharing corners, with a room."""
    pts = [QPointF(x0, y0), QPointF(x0 + n, y0), QPointF(x0 + n, y0 + n), QPointF(x0, y0 + n)]
    walls = []
    for i in range(4):
        w = fp.WallItem(pts[i], pts[(i + 1) % 4], "exterior")
        win.scene.addItem(w)
        walls.append(w)
    for i in range(4):                       # one corner, one vertex
        walls[(i + 1) % 4].set_end_vertex("p1", walls[i].end_vertex("p2"))
    fp.rebuild_all_walls(win.scene)
    res = win.run_macro(f"ROOM Den {x0 + n / 2:.0f} {y0 + n / 2:.0f}")
    assert res["ok"], res
    room = next(r for r in win.scene.items() if isinstance(r, fp.RoomItem))
    return walls, room


def _ends(w):
    return (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y())


def test_the_sheet_shows_the_walls_properties_and_its_ends(fp, win):
    win.prepare_headless()
    walls, room = _square(fp, win)
    w = walls[0]
    res = win.run_macro("DOOR 120 0 3080")
    assert res["ok"], res
    dlg = WallPropertiesDialog(w, win)
    assert dlg.cb_type.currentData() == "exterior"
    assert dlg.ed_name.text() == "" and dlg.ed_name.placeholderText() == w.uid
    assert [r.ed_x.text() for r in dlg.ends] == ["0", "240"]
    assert [r.ed_y.text() for r in dlg.ends] == ["0", "0"]
    assert dlg.ends[1].echo.text() == "(20'-0\", 0'-0\")"
    assert dlg.ck_joined.isChecked(), "on by default"
    assert isinstance(dlg.profile, WallProfileView)
    assert dlg.profile.spans() == [("door", 105.0, 135.0)]
    assert not dlg.profile.grab().isNull()


def test_ok_with_the_box_on_moves_the_corner_for_every_holder(fp, win):
    """The default: the corner p2 of wall 0 is also p1 of wall 1 and a corner
    of the room's outline; all three follow."""
    win.prepare_headless()
    walls, room = _square(fp, win)
    w0, w1 = walls[0], walls[1]
    corner = w0.end_vertex("p2")
    assert w1.end_vertex("p1") is corner and any(e.v is corner for e in room.outline)
    dlg = WallPropertiesDialog(w0, win)
    dlg.ends[1].ed_x.setText("20'6\"")
    dlg.ends[1].ed_y.setText("-12")
    dlg.ends[1].ed_name.setText("NE corner")
    dlg.ed_name.setText("North wall")
    assert dlg.apply() == 1
    assert _ends(w0) == (0.0, 0.0, 246.0, -12.0)
    assert (w1.p1.x(), w1.p1.y()) == (246.0, -12.0), "the joined wall followed"
    assert w1.end_vertex("p1") is w0.end_vertex("p2"), "still one corner"
    assert any(e.v is w0.end_vertex("p2") for e in room.outline), "the outline followed"
    assert w0.name == "North wall" and w0.end_vertex("p2").name == "NE corner"
    assert w1.end_vertex("p1").name == "NE corner", "the corner's name is the corner's"
    assert room.open_edges() == []


def test_ok_with_the_box_off_moves_this_walls_end_alone(fp, win):
    win.prepare_headless()
    walls, room = _square(fp, win)
    w0, w1 = walls[0], walls[1]
    dlg = WallPropertiesDialog(w0, win)
    dlg.ck_joined.setChecked(False)
    dlg.ends[1].ed_y.setText("-12")
    assert dlg.apply() == 1
    assert _ends(w0) == (0.0, 0.0, 240.0, -12.0)
    assert (w1.p1.x(), w1.p1.y()) == (240.0, 0.0), "the other wall stayed"
    assert w1.end_vertex("p1") is not w0.end_vertex("p2"), "the corner split"


def test_cancel_changes_nothing(fp, win):
    """Nothing is written until OK: a dialog edited and then rejected leaves
    the wall, its corners and the document exactly as they were."""
    win.prepare_headless()
    walls, room = _square(fp, win)
    w0 = walls[0]
    before = win.snapshot()
    dlg = WallPropertiesDialog(w0, win)
    dlg.ed_name.setText("gone")
    dlg.ends[0].ed_x.setText("99")
    dlg.cb_type.setCurrentIndex(1)
    dlg.reject()
    assert dlg.result() == QDialog.DialogCode.Rejected
    assert win.snapshot() == before and w0.name == "" and _ends(w0) == (0.0, 0.0, 240.0, 0.0)


def test_ok_refuses_a_bad_length_and_a_vanishing_wall(fp, win, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox
    said = []
    monkeypatch.setattr(QMessageBox, "warning",
                        staticmethod(lambda *a, **k: said.append(a[2]) or QMessageBox.StandardButton.Ok))
    win.prepare_headless()
    walls, _ = _square(fp, win)
    dlg = WallPropertiesDialog(walls[0], win)
    dlg.ends[1].ed_x.setText("ten")
    dlg._ok()
    assert dlg.result() != QDialog.DialogCode.Accepted and "p2 x" in said[-1]
    dlg.ends[1].ed_x.setText("2")                # a 2in wall: shorter than MIN_WALL_LEN
    dlg._ok()
    assert dlg.result() != QDialog.DialogCode.Accepted and "shorter" in said[-1]
    dlg.ends[1].ed_x.setText("240")
    dlg._ok()
    assert dlg.result() == QDialog.DialogCode.Accepted


def test_the_type_change_takes_effect(fp, win):
    win.prepare_headless()
    walls, _ = _square(fp, win)
    dlg = WallPropertiesDialog(walls[2], win)
    dlg.cb_type.setCurrentIndex(dlg.cb_type.findData("interior"))
    dlg.apply()
    assert walls[2].wall_type == "interior" and walls[2].t == fp.STD_T["interior"]


# --------------------------------------------------------------------------
# the double-click, and one undo step
# --------------------------------------------------------------------------
def test_a_double_click_on_a_wall_opens_the_sheet_and_ok_is_one_undo_step(fp, win, monkeypatch):
    win.prepare_headless()
    walls, _ = _square(fp, win)
    w0 = walls[0]
    seen = {}

    def fake_exec(self):
        seen["dlg"] = self
        self.ends[1].ed_y.setText("-24")
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(WallPropertiesDialog, "exec", fake_exec)
    win._commit_if_changed()
    depth = len(win._undo_stack)
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(120.0, 0.0))
    for et in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease,
               QEvent.Type.MouseButtonDblClick, QEvent.Type.MouseButtonRelease):
        QApplication.sendEvent(vp, QMouseEvent(
            et, QPointF(pos), QPointF(vp.mapToGlobal(pos)), Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton if et != QEvent.Type.MouseButtonRelease else Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier))
    assert seen["dlg"].wall is w0
    assert _ends(w0) == (0.0, 0.0, 240.0, -24.0)
    assert w0._mode is None, "the press's drag was disarmed"
    assert len(win._undo_stack) == depth + 1
    win.undo()                                   # a snapshot undo rebuilds the scene
    ends = sorted(_ends(w) for w in win.scene.items() if isinstance(w, fp.WallItem))
    assert (0.0, 0.0, 240.0, 0.0) in ends and not any(e[3] == -24.0 for e in ends)


# --------------------------------------------------------------------------
# the names are document fields
# --------------------------------------------------------------------------
def test_wall_and_corner_names_round_trip_through_the_document(fp, win):
    win.prepare_headless()
    walls, room = _square(fp, win)
    walls[0].name = "North wall"
    walls[0].end_vertex("p2").name = "NE corner"
    doc = design_from_scene(win).to_dict()
    assert schema_errors(doc) == []
    named_w = [w for w in doc["walls"] if w.get("name")]
    named_v = [v for v in doc["vertices"] if v.get("name")]
    assert [w["name"] for w in named_w] == ["North wall"]
    assert [(v["name"], v["x"], v["y"]) for v in named_v] == [("NE corner", 240.0, 0.0)]
    assert all("name" not in v for v in doc["vertices"] if v is not named_v[0]), "unnamed = absent"
    win.clear_plan()
    apply_design_to_scene(win, Design.from_dict(doc))
    back = [w for w in win.scene.items() if isinstance(w, fp.WallItem)]
    nw = next(w for w in back if w.name == "North wall")
    corner = next(w.end_vertex(a) for w in back for a in ("p1", "p2") if w.end_vertex(a).name)
    assert corner.name == "NE corner" and (corner.x, corner.y) == (240.0, 0.0)
    holders = [(w, a) for w in back for a in ("p1", "p2") if w.end_vertex(a) is corner]
    assert len(holders) == 2 and nw in [w for w, _ in holders], "one named corner, two walls on it"
    again = design_from_scene(win).to_dict()
    assert again == doc, "the second document is the first"


def test_a_relocated_corner_keeps_its_name_and_a_detached_end_does_not(fp):
    v = fp.Vertex(1.0, 2.0, name="A")
    moved = v.relocated_to(QPointF(3.0, 4.0))
    assert moved.name == "A" and moved.uid == v.uid
    w = fp.WallItem(QPointF(0, 0), QPointF(100, 0))
    w.set_end_vertex("p1", v)
    w.detach_end("p1", QPointF(5.0, 5.0))
    assert w.end_vertex("p1").name is None and w.end_vertex("p1") is not v
