"""P5 §2 (0294 §2): a dormer's face windows are hit-testable plan items -- the
SECOND ROW just inside the face, told apart from the storey wall's own window by
a categorical mark and an up-slope offset. One `DormerWindowItem` per face
window, reconciled with `openings` by `RoofItem.sync_windows`.
"""
import pytest

from floorplanner.design.bridge import apply_design_to_scene
from floorplanner.roofs import DormerWindowItem, RoofItem, _roof_hittable

pytestmark = pytest.mark.gui


def _doc(openings):
    host = {"id": "rf1", "level": "L1", "ridge": [[-40.0, 100.0], [440.0, 100.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 300.0, "overhang_in": [0.0, 0.0],
            "span_in": [170.0, 170.0], "gable": [True, True], "marker_end": 1}
    dormer = {"id": "rf2", "level": "L1", "ridge": [[200.0, 240.0], [200.0, 160.0]],
              "eaves_h_in": 180.0, "ridge_h_in": 240.0, "overhang_in": [0.0, 0.0],
              "span_in": [40.0, 40.0], "wall_span_in": [40.0, 40.0],
              "gable": [True, True], "marker_end": 0, "host": "rf1", "openings": openings}
    return {"format": "floorplanner-design", "version": 6, "units": "inches", "settings": {},
            "levels": [{"id": "L1", "name": "L1", "elevation_in": 0.0, "height_in": 96.0,
                        "kind": "storey", "reference": False},
                       {"id": "L2", "name": "L2", "elevation_in": 96.0, "height_in": 96.0,
                        "kind": "storey", "reference": False}],
            "vertices": [], "walls": [], "rooms": [], "furnishings": [], "groups": [],
            "roofs": [host, dormer]}


def _window(oid, offset=0.0):
    return {"id": oid, "kind": "window", "code": "3040",
            "anchor": {"from": "center", "offset_in": offset}, "sill_in": 150.0}


def _dormer(win, openings):
    win.prepare_headless()
    apply_design_to_scene(win, _doc(openings))
    return next(it for it in win.scene.items()
                if isinstance(it, RoofItem) and it.is_dormer())


def test_a_face_window_gets_one_plan_item(fp, win):
    d = _dormer(win, [_window("w1")])
    assert len(d.windows) == 1 and d.windows[0].opening_id == "w1"
    assert isinstance(d.windows[0], DormerWindowItem)


def test_items_reconcile_with_the_openings(fp, win):
    d = _dormer(win, [_window("w1"), _window("w2", offset=40.0)])
    assert {w.opening_id for w in d.windows} == {"w1", "w2"}
    d.openings = [_window("w2", offset=40.0)]          # drop w1
    d.rebuild()
    assert {w.opening_id for w in d.windows} == {"w2"}


def test_the_band_sits_up_slope_of_the_face_not_on_it(fp, win):
    d = _dormer(win, [_window("w1")])
    it = d.windows[0]
    # the band's centre is offset from the face line toward the dormer apex (p2)
    face_y = d._dormer_wall_lines()[0][0].y()          # the face is at y=240
    band_y = (it._a.y() + it._b.y()) / 2.0
    assert band_y < face_y                              # p2 (apex) is at y=160, up-slope
    assert abs(band_y - face_y) > 1.0                  # a real gap, not on the line


def test_the_item_is_hittable_only_on_its_active_level(fp, win):
    d = _dormer(win, [_window("w1")])
    win.switch_floor("L1")
    assert _roof_hittable(d) and not d.windows[0].shape().isEmpty()
    win.switch_floor("L2")                              # the dormer ghosts here
    assert d.windows[0].shape().isEmpty()              # shown, not hittable


def test_delete_removes_the_opening_and_its_item(fp, win):
    d = _dormer(win, [_window("w1"), _window("w2", offset=40.0)])
    win.switch_floor("L1")
    target = next(w for w in d.windows if w.opening_id == "w1")
    target._delete()
    assert [o["id"] for o in d.openings] == ["w2"]
    assert {w.opening_id for w in d.windows} == {"w2"}


def test_duplicate_adds_a_second_opening(fp, win):
    d = _dormer(win, [_window("w1")])
    win.switch_floor("L1")
    d.windows[0]._duplicate()
    assert len(d.openings) == 2
    assert len({o["id"] for o in d.openings}) == 2     # a fresh id, not a clash


def test_the_sill_is_referenced_from_the_dormer_floor(fp, win):
    """P5 (Patrick, 2026-11-06): a dormer window's sill reads from the DORMER's
    own floor -- the top of the ceiling of the storey it sits over (the host
    floor's height) -- not the ground. The record stores the host-datum number;
    the dialog edits above the dormer floor (0294 §1c, a display conversion)."""
    from floorplanner.dialogs import _DormerWindowDialog
    d = _dormer(win, [_window("w1")])
    win.switch_floor("L1")
    assert d.dormer_sill_floor_in() == 96.0            # L1's height, the attic floor
    # a window stored at sill_in 150 shows as 150-96 = 54 above the dormer floor
    o = dict(_window("w1"))
    o["sill_in"] = 150.0
    dlg = _DormerWindowDialog(o, None, sill_floor_in=d.dormer_sill_floor_in(),
                              ceiling_in=d.ridge_h_in)
    assert dlg.sp_sill.value() == pytest.approx(54.0)
    dlg.sp_sill.setValue(30.0)                          # 30 above the dormer floor
    assert dlg.opening()["sill_in"] == pytest.approx(126.0)   # stored above the datum


def test_a_window_past_the_ridge_is_refused(fp, win):
    from floorplanner.dialogs import _DormerWindowDialog
    d = _dormer(win, [_window("w1")])
    win.switch_floor("L1")
    dlg = _DormerWindowDialog(_window("w1"), None, sill_floor_in=96.0,
                              ceiling_in=float(d.ridge_h_in))
    dlg.ed_code.setText("3080")                        # 80" tall
    dlg.sp_sill.setValue(dlg.sp_sill.maximum())        # as high as allowed
    dlg.sp_sill.setValue(100.0)                        # head would pass the ridge
    before = dlg.lab_err.text()
    dlg.accept()                                       # refused: an error, not accept
    assert dlg.lab_err.text() and dlg.lab_err.text() != before
    assert "too tall" in dlg.lab_err.text().lower() or "ridge" in dlg.lab_err.text().lower()
