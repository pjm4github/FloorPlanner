"""R6.0 (0197-ruling.md sec2) -- closing D50: a level's `elevation_in` and
`height_in` survive a load/save round trip. Measured before the fix
(0198-report.md sec1): the LOADER dropped both fields on the way in --
`model.Floor` had only `name` and `reference` -- and every writer emitted
literals; so the fix is a field on the roster, then the loader and the
writers reading it.

The acceptance is D50's own Receipt, verbatim, extended across all five
multifloor plans 0197 sec1 tabled: set L2's elevation and height, open,
save, read back -- the values must be the ones that went in. Read back the
way `fp3d.py --list-levels` reads them: straight off the document.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF

pytestmark = pytest.mark.io

ROOT = Path(__file__).resolve().parents[1]
PLANS = [
    "examples/farmplaceBIGmultifloor.json",
    "examples/roundedMultifloor.json",
    "fixtures/crossfloor-snap-2026-08-17.json",
    "fixtures/wiscaway2026-08-30R1.json",
    "fixtures/wiscaway2026-08-30R2.json",
]
ELEV, HEIGHT = 120.0, 108.0


def _levels(path):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return [(L["id"], L.get("name"), float(L.get("elevation_in", 0.0)),
             float(L.get("height_in", 96.0))) for L in doc["levels"]]


# --------------------------------------------------------------------------
# D50's Receipt, across the five plans
# --------------------------------------------------------------------------
@pytest.mark.parametrize("rel", PLANS)
def test_a_levels_elevation_and_height_survive_open_and_save(fp, win, tmp_path, rel):
    doc = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    assert len(doc["levels"]) == 2, "precondition: a multifloor plan"
    assert all(float(L.get("elevation_in", 0.0)) == 0.0 for L in doc["levels"]), \
        "precondition: the corpus plan says 0.0 everywhere (0197 sec1)"
    doc["levels"][1]["elevation_in"] = ELEV
    doc["levels"][1]["height_in"] = HEIGHT
    src = tmp_path / "in.json"
    src.write_text(json.dumps(doc, indent=1), encoding="utf-8")

    win.prepare_headless()
    win.load_path(str(src))
    # the loader half: the roster carries what the document said
    roster = {f.name: (f.elevation_in, f.height_in) for f in win.floors}
    l1, l2 = doc["levels"][0]["name"], doc["levels"][1]["name"]
    assert roster[l1] == (0.0, 96.0)
    assert roster[l2] == (ELEV, HEIGHT)
    # the writer half: the file says it again
    out = tmp_path / "out.json"
    win.save_path(str(out))
    levels = _levels(out)
    assert levels[0][2:] == (0.0, 96.0)
    assert levels[1][2:] == (ELEV, HEIGHT), levels
    assert levels[1][1] == l2


def test_the_fail_first_control_a_document_with_zero_everywhere_still_round_trips(fp, win, tmp_path):
    """A round trip on a plan whose levels were 0.0 to begin with proves
    nothing about D50 (0197 sec2 item 2) -- pinned so the receipt above is
    read for what it is: the non-zero values are the instrument."""
    rel = PLANS[1]
    win.prepare_headless()
    win.load_path(str(ROOT / rel))
    out = tmp_path / "zero.json"
    win.save_path(str(out))
    assert [lv[2:] for lv in _levels(out)] == [(0.0, 96.0), (0.0, 96.0)]


# --------------------------------------------------------------------------
# stored, not derived: the new-floor default, and the edit
# --------------------------------------------------------------------------
def test_a_new_floor_defaults_to_the_floor_below_plus_its_height(fp, win):
    win.prepare_headless()
    assert [(f.elevation_in, f.height_in) for f in win.floors] == [(0.0, 96.0)]
    win.new_floor_named("Upper")
    win.new_floor_named("Attic")
    got = {f.name: (f.elevation_in, f.height_in) for f in win.floors}
    assert got["Upper"] == (96.0, 96.0)
    assert got["Attic"] == (192.0, 96.0)
    # and WRITTEN, not recomputed on read: the document carries the numbers
    doc = win.design_document()
    assert [(L["name"], L["elevation_in"], L["height_in"]) for L in doc["levels"]] == [
        (fp.DEFAULT_FLOOR, 0.0, 96.0), ("Upper", 96.0, 96.0), ("Attic", 192.0, 96.0)]


def test_editing_a_floors_levels_is_a_roster_edit_with_an_undo_step(fp, win):
    win.prepare_headless()
    win.new_floor_named("Upper")
    win._commit_if_changed()
    depth = len(win._undo_stack)
    assert win.set_floor_levels("Upper", 110.0, 120.0)
    f = win._floor("Upper")
    assert (f.elevation_in, f.height_in) == (110.0, 120.0)
    assert win._is_dirty()
    win._commit_if_changed()
    assert len(win._undo_stack) == depth + 1
    win.undo()
    f = win._floor("Upper")
    assert (f.elevation_in, f.height_in) == (96.0, 96.0), "undo restores the roster"
    assert win.set_floor_levels("Upper", 110.0, 0.0) is False, "a height must be positive"
    assert win.set_floor_levels("Nowhere", 1.0, 2.0) is False


def test_the_levels_dialog_seeds_from_the_floor_and_returns_what_was_typed(fp, win):
    from floorplanner.dialogs import FloorLevelsDialog
    win.prepare_headless()
    win.new_floor_named("Upper")
    dlg = FloorLevelsDialog(win._floor("Upper"), win)
    assert dlg.values() == (96.0, 96.0)
    dlg.sp_elev.setValue(-36.0)                    # a basement is legal
    dlg.sp_height.setValue(102.0)
    assert dlg.values() == (-36.0, 102.0)


# --------------------------------------------------------------------------
# the other two writers: the v4 project and the legacy importer
# --------------------------------------------------------------------------
def test_the_v4_project_and_the_legacy_importer_carry_the_storey_numbers(fp, win):
    win.prepare_headless()
    win.new_floor_named("Upper")
    win.set_floor_levels("Upper", 108.0, 100.0)
    win.scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior"))
    fp.rebuild_all_walls(win.scene)
    v4 = json.loads(json.dumps(win.serialize()))
    assert v4["version"] == 4
    assert {f["name"]: (f["elevation_in"], f["height_in"]) for f in v4["floors"]} == {
        fp.DEFAULT_FLOOR: (0.0, 96.0), "Upper": (108.0, 100.0)}
    win2 = fp.MainWindow()
    try:
        win2.load_data(v4)                          # the legacy import path
        assert {f.name: (f.elevation_in, f.height_in) for f in win2.floors} == {
            fp.DEFAULT_FLOOR: (0.0, 96.0), "Upper": (108.0, 100.0)}
        doc = win2.design_document()
        assert [(L["name"], L["elevation_in"], L["height_in"]) for L in doc["levels"]] == [
            (fp.DEFAULT_FLOOR, 0.0, 96.0), ("Upper", 108.0, 100.0)]
    finally:
        win2.close()


def test_the_detect_path_reads_the_roster_and_a_bare_scene_gets_the_defaults(fp, win, scene):
    from floorplanner.design.bridge import _floor_levels
    win.prepare_headless()
    win.set_floor_levels(fp.DEFAULT_FLOOR, 12.0, 100.0)
    assert _floor_levels(win.scene, fp.DEFAULT_FLOOR) == (12.0, 100.0)
    assert _floor_levels(scene, fp.DEFAULT_FLOOR) == (0.0, 96.0)


# --------------------------------------------------------------------------
# 0197 sec6: does closing D50 by itself put each storey at its own height in 3D?
# --------------------------------------------------------------------------
def _load_fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_levels_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_a_stored_elevation_stacks_the_storeys_in_3d(fp, win, tmp_path):
    """Measured, not reasoned: `fp3d.build_model` reads `elevation_in` as each
    level's base and `height_in` as its wall top (0197 sec2 item 4), so
    once the document carries a real elevation the upper storey's walls
    stand on it -- no z-order work (D11) is needed for that."""
    import numpy as np
    win.prepare_headless()
    win.scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(240, 0), "exterior"))
    win.new_floor_named("Upper")
    win.set_floor_levels("Upper", 108.0, 100.0)
    win.scene.addItem(fp.WallItem(QPointF(0, 0), QPointF(240, 0), "exterior"))
    fp.rebuild_all_walls(win.scene)
    doc = win.design_document()
    fp3d = _load_fp3d()
    model = fp3d.build_model(doc, furnishings=False, floors=False, roofs=False)
    z = np.vstack([m.verts for m in model.meshes if m.name.startswith("walls:")])[:, 2]
    assert z.min() == pytest.approx(0.0) and z.max() == pytest.approx(108.0 + 100.0)
    assert np.any(np.isclose(z, 108.0)), "the upper wall's base is its level's elevation"
    assert np.any(np.isclose(z, 96.0)), "the lower wall's top is its storey height"
