"""Phase C (0291): the dormer owns its face windows as ONE record, viewed
many ways. The End-On dialog (`RoofEndOnDialog`) is the editor -- it seeds
from `roof.openings`, add/edit/remove work a working copy, and `apply()`
writes it back. The plan draws those windows as a READ-ONLY shadow via
`RoofItem.dormer_face_window_spans()`, which `paint()` reads; the floor's own
wall windows are untouched. `_DormerWindowDialog` validates the size code so
a bad one never reaches the record.
"""
import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QDialog

from floorplanner.dialogs import RoofEndOnDialog, _DormerWindowDialog
from floorplanner.roofs import RoofItem

pytestmark = pytest.mark.gui

WIN = {"kind": "window", "code": "4860",
       "anchor": {"from": "v1", "offset_in": 0.0}, "sill_in": 36.0}


def _host(scene):
    h = RoofItem(QPointF(-40, 100), QPointF(440, 100), eaves_h_in=96.0,
                 ridge_h_in=300.0, overhang_in=0.0, span_in=[170.0, 170.0],
                 gable=[True, True], marker_end=1)
    h.floor = "default"
    scene.addItem(h)
    return h


def _dormer(scene, openings=None):
    d = RoofItem(QPointF(200, 240), QPointF(200, 160), eaves_h_in=180.0,
                 ridge_h_in=240.0, overhang_in=0.0, span_in=[40.0, 40.0],
                 wall_span_in=[40.0, 40.0], gable=[True, True], marker_end=0,
                 host=_host(scene), openings=openings)
    d.floor = "default"
    scene.addItem(d)
    return d


# -- the editor -----------------------------------------------------------

def test_the_dialog_seeds_the_window_list_from_the_record(scene):
    d = _dormer(scene, openings=[dict(WIN)])
    dlg = RoofEndOnDialog(d)
    assert dlg._dormer
    assert len(dlg._face_openings) == 1
    assert dlg._face_openings[0]["code"] == "4860"
    assert dlg.lst_windows.count() == 1


def test_apply_writes_the_working_copy_back_to_the_roof(scene):
    d = _dormer(scene, openings=[])
    dlg = RoofEndOnDialog(d)
    dlg._face_openings.append(dict(WIN))
    assert dlg.apply() is True
    assert len(d.openings) == 1
    assert d.openings[0]["code"] == "4860"
    assert d.openings[0]["anchor"] == {"from": "v1", "offset_in": 0.0}
    # the write is a copy -- mutating the dialog's list no longer touches the roof
    dlg._face_openings.clear()
    assert len(d.openings) == 1


def test_add_edit_remove_drive_the_working_copy(scene, monkeypatch):
    d = _dormer(scene, openings=[])
    dlg = RoofEndOnDialog(d)

    def _accept_with(opening):
        monkeypatch.setattr(_DormerWindowDialog, "exec",
                            lambda self: QDialog.DialogCode.Accepted)
        monkeypatch.setattr(_DormerWindowDialog, "opening",
                            lambda self: dict(opening))

    _accept_with(WIN)
    dlg._add_window()
    assert [o["code"] for o in dlg._face_openings] == ["4860"]
    assert dlg.lst_windows.count() == 1

    _accept_with({**WIN, "code": "3040"})
    dlg.lst_windows.setCurrentRow(0)
    dlg._edit_window()
    assert dlg._face_openings[0]["code"] == "3040"

    dlg.lst_windows.setCurrentRow(0)
    dlg._remove_window()
    assert dlg._face_openings == []


def test_the_window_dialog_refuses_a_bad_size_code(scene):
    bad = _DormerWindowDialog({**WIN, "code": "nope"})
    bad.accept()
    assert bad.result() != int(QDialog.DialogCode.Accepted)
    assert bad.lab_err.text()                     # the error is shown, not silent
    good = _DormerWindowDialog(dict(WIN))
    assert good.opening()["code"] == "4860"
    assert good.opening()["kind"] == "window"


def test_the_window_dialog_mints_a_schema_valid_id_and_keeps_it_on_edit(scene):
    import re
    fresh = _DormerWindowDialog({"code": "4860", "anchor": {"from": "v1", "offset_in": 0.0}})
    oid = fresh.opening()["id"]                 # a new window: a fresh id is minted
    assert re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", oid)
    kept = _DormerWindowDialog({**WIN, "id": "o7"})
    assert kept.opening()["id"] == "o7"         # an existing window keeps its id


def test_a_plain_roof_has_no_window_editor_and_apply_adds_no_openings(scene):
    rf = RoofItem(QPointF(0, 0), QPointF(200, 0), eaves_h_in=96.0,
                  ridge_h_in=150.0, overhang_in=0.0, span_in=[100.0, 100.0])
    rf.floor = "default"
    scene.addItem(rf)
    dlg = RoofEndOnDialog(rf)
    assert not dlg._dormer
    assert not hasattr(dlg, "lst_windows")
    dlg.apply()
    assert rf.openings == []


# -- the plan shadow ------------------------------------------------------

def test_the_shadow_has_one_span_per_window_positioned_on_the_face(scene):
    d = _dormer(scene, openings=[dict(WIN)])
    spans = d.dormer_face_window_spans()
    assert len(spans) == 1
    a, b = spans[0]
    import math
    # a 4860 window is 48" wide, so its plan span is 48" long
    assert abs(math.hypot(b.x() - a.x(), b.y() - a.y()) - 48.0) < 0.5


def test_a_window_off_the_face_or_with_a_bad_code_is_skipped(scene):
    d = _dormer(scene, openings=[
        {**WIN, "code": "bad"},                                   # unparseable
        {**WIN, "anchor": {"from": "v1", "offset_in": 500.0}},    # wholly off the 80" face
        dict(WIN),                                                # the one good one
    ])
    assert len(d.dormer_face_window_spans()) == 1


def test_no_host_means_no_shadow(scene):
    d = _dormer(scene, openings=[dict(WIN)])
    d.host = None
    assert d.dormer_face_window_spans() == []
