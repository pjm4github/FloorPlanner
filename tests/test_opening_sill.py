"""0255-report.md: THE WINDOW'S ELEVATION -- a sill height, a property of the
window, carried by the opening item, offered on its property sheet, written
to and read from the document, and ONE default everywhere a record does not
say (`DEFAULT_SILL_IN`, model.py; the Qt-free 3D builder keeps a twin).
"""
import importlib.util
import sys
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
from floorplanner.design.validate import schema_errors
from floorplanner.model import DEFAULT_SILL_IN

pytestmark = pytest.mark.walls

ROOT = Path(__file__).resolve().parents[1]


def _fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_sill_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _wall_with(fp, scene, kind, code, y=0.0):
    w = fp.WallItem(QPointF(0, y), QPointF(240, y), "exterior")
    scene.addItem(w)
    op = fp.OpeningItem(w, kind, code, 120.0)
    w.openings.append(op)
    fp.rebuild_all_walls(scene)
    return w, op


def _openings(fp, scene):
    return [o for it in scene.items() if isinstance(it, fp.WallItem) for o in it.openings]


def test_the_default_sill_is_one_number_everywhere():
    assert DEFAULT_SILL_IN == 36.0
    assert _fp3d().DEFAULT_SILL == DEFAULT_SILL_IN


def test_a_new_window_has_no_sill_and_writes_none(fp, scene):
    _w, op = _wall_with(fp, scene, "window", "3660")
    assert op.sill_in is None
    out = design_from_scene(scene).to_dict()
    assert "sill_in" not in out["walls"][0]["openings"][0], "a record that never said goes on not saying"
    assert schema_errors(out) == []


def test_a_set_sill_round_trips_through_the_document(fp, scene):
    _w, op = _wall_with(fp, scene, "window", "3660")
    op.set_sill(30.0)
    out = design_from_scene(scene).to_dict()
    assert out["walls"][0]["openings"][0]["sill_in"] == 30.0
    assert schema_errors(out) == []
    scene.clear()
    apply_design_to_scene(scene, out)
    ops = _openings(fp, scene)
    assert len(ops) == 1 and ops[0].sill_in == 30.0


def test_a_documents_head_rides_through_until_the_size_or_sill_changes(fp, scene):
    _w, op = _wall_with(fp, scene, "window", "3660")
    doc = design_from_scene(scene).to_dict()
    doc["walls"][0]["openings"][0]["head_in"] = 90.0
    doc["walls"][0]["openings"][0]["sill_in"] = 30.0
    scene.clear()
    apply_design_to_scene(scene, doc)
    op = _openings(fp, scene)[0]
    assert op.sill_in == 30.0 and op._v5_extra == {"head_in": 90.0}
    assert design_from_scene(scene).to_dict()["walls"][0]["openings"][0]["head_in"] == 90.0
    op.set_sill(40.0)                     # the head was measured from the old sill
    assert "head_in" not in design_from_scene(scene).to_dict()["walls"][0]["openings"][0]
    scene.clear()
    apply_design_to_scene(scene, doc)
    op = _openings(fp, scene)[0]
    op.set_code("3648")                   # a new height: the head no longer fits
    assert "head_in" not in op._v5_extra


def test_the_sheet_offers_the_sill_to_a_window_only_and_seeds_the_default(fp, scene):
    from PyQt6.QtWidgets import QLabel

    from floorplanner.dialogs import OpeningPropertiesDialog
    _w, win = _wall_with(fp, scene, "window", "3660")
    dlg = OpeningPropertiesDialog(win)
    assert dlg.sp_sill is not None and dlg.sill_in() == DEFAULT_SILL_IN
    text = " ".join(lb.text() for lb in dlg.findChildren(QLabel))
    assert "Sill height" in text and "has not been set" in text, "the sheet says the default is in use"
    dlg.sp_sill.setValue(48.0)
    assert dlg.sill_in() == 48.0
    win.set_sill(48.0)
    dlg2 = OpeningPropertiesDialog(win)
    text2 = " ".join(lb.text() for lb in dlg2.findChildren(QLabel))
    assert dlg2.sill_in() == 48.0 and "has not been set" not in text2
    _w2, door = _wall_with(fp, scene, "door", "3280", y=240.0)
    dlg3 = OpeningPropertiesDialog(door)
    assert dlg3.sp_sill is None and dlg3.sill_in() is None


def test_the_sheet_applies_the_sill_on_ok(fp, scene, monkeypatch):
    from PyQt6.QtWidgets import QDialog

    from floorplanner import dialogs
    _w, win = _wall_with(fp, scene, "window", "3660")

    class Sheet(dialogs.OpeningPropertiesDialog):
        def exec(self):
            self.sp_sill.setValue(42.0)
            return QDialog.DialogCode.Accepted
    monkeypatch.setattr(dialogs, "OpeningPropertiesDialog", Sheet)
    win._prompt_size()
    assert win.sill_in == 42.0


def test_a_copy_carries_the_sill_and_a_gates_swing_is_written(fp, scene):
    """`data`/`adopt` is what a merge, a split, an extract and a paste go
    through; and a gate's type and swing are written like a door's (they
    were dropped on every save)."""
    _w, win = _wall_with(fp, scene, "window", "3660")
    win.set_sill(24.0)
    w2 = fp.WallItem(QPointF(0, 240), QPointF(240, 240), "exterior")
    scene.addItem(w2)
    twin = fp.OpeningItem(w2, win.kind, win.code, 120.0)
    twin.adopt(win.data())
    assert twin.sill_in == 24.0 and twin.swing == win.swing
    twin.adopt({"door_type": "RH", "swing": 1})     # an older clipboard: no sill key
    assert twin.sill_in is None and twin.door_type == "RH"
    rail = fp.WallItem(QPointF(0, 480), QPointF(240, 480), "railing")
    scene.addItem(rail)
    gate = fp.OpeningItem(rail, "gate", "3648", 120.0)
    gate.door_type, gate.swing = "RH", 1
    rail.openings.append(gate)
    fp.rebuild_all_walls(scene)
    out = design_from_scene(scene).to_dict()
    rec = next(o for w in out["walls"] for o in w["openings"] if o["kind"] == "gate")
    assert rec["door_type"] == "RH" and rec["swings_toward"] == "right" and rec["hinge"] == "v2"
    assert schema_errors(out) == []
