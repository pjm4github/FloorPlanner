"""P3 of the 1½-storey arc (0297 §2, 0293 §5 P3, 0295, 0296): a dormer's level
is its EDITING HOME; its datum is the host's. The two legal levels are the
host's and the one directly above; promote/demote is an edit of `level` alone,
leaving 3D untouched; the dormer shows on both legal levels (solid on its own,
ghosted on the other) and is editable only on its own.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

from floorplanner.design.bridge import apply_design_to_scene
from floorplanner.roofs import RoofItem, _roof_hittable, legal_dormer_levels

pytestmark = pytest.mark.gui

ROOT = Path(__file__).resolve().parents[1]


def _doc():
    host = {"id": "rf1", "level": "L1", "ridge": [[-40.0, 100.0], [440.0, 100.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 300.0, "overhang_in": [0.0, 0.0],
            "span_in": [170.0, 170.0], "gable": [True, True], "marker_end": 1}
    dormer = {"id": "rf2", "level": "L1", "ridge": [[200.0, 240.0], [200.0, 160.0]],
              "eaves_h_in": 180.0, "ridge_h_in": 240.0, "overhang_in": [0.0, 0.0],
              "span_in": [40.0, 40.0], "wall_span_in": [40.0, 40.0],
              "gable": [True, True], "marker_end": 0, "host": "rf1"}
    return {"format": "floorplanner-design", "version": 6, "units": "inches", "settings": {},
            "levels": [{"id": "L1", "name": "L1", "elevation_in": 0.0, "height_in": 96.0,
                        "kind": "storey", "reference": False},
                       {"id": "L2", "name": "L2", "elevation_in": 96.0, "height_in": 96.0,
                        "kind": "storey", "reference": False}],
            "vertices": [], "walls": [], "rooms": [], "furnishings": [], "groups": [],
            "roofs": [host, dormer]}


def _dormer(win):
    win.prepare_headless()
    apply_design_to_scene(win, _doc())
    return next(it for it in win.scene.items()
                if isinstance(it, RoofItem) and it.is_dormer())


def test_legal_dormer_levels_are_the_host_and_the_one_above(fp, win):
    d = _dormer(win)
    assert legal_dormer_levels(d) == ["L1", "L2"]       # host's and the one above


def test_promote_and_demote_a_dormer(fp, win):
    d = _dormer(win)
    assert d.floor == "L1"
    assert win.move_dormer_to_level(d, "L2") is True
    assert d.floor == "L2"
    assert win.move_dormer_to_level(d, "L1") is True    # demote back
    assert d.floor == "L1"
    assert win.move_dormer_to_level(d, "L1") is False   # same level: no-op
    assert win.move_dormer_to_level(d, "nowhere") is False   # not a legal level


def test_level_base_in_for_a_dormer_is_the_host_base(fp, win):
    from floorplanner.dialogs import RoofEndOnDialog
    d = _dormer(win)
    win.move_dormer_to_level(d, "L2")                   # drawn on L2, host on L1
    dlg = RoofEndOnDialog(d, win)
    assert dlg.level_base_in() == 0.0                   # the HOST's base, not L2's 96


def test_a_dormer_shows_on_both_legal_levels_editable_only_on_its_own(fp, win):
    d = _dormer(win)                                    # drawn on L1
    win.switch_floor("L1")
    assert d.isVisible() and _roof_hittable(d)          # solid, editable on its own
    win.switch_floor("L2")
    assert d.isVisible() and not _roof_hittable(d)      # ghosted, not editable


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_p3_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_promotion_leaves_build_model_byte_identical(fp3d):
    """0293 §3: promotion is an edit of `level` alone -- 3D never reads a
    dormer's level, so `build_model` is byte-identical before and after."""
    import copy

    import numpy as np

    def verts(doc):
        m = fp3d.build_model(doc, furnishings=False, floors=True)
        return np.concatenate([np.round(me.verts, 4) for me in sorted(m.meshes, key=lambda x: x.name)])
    a = verts(_doc())
    d2 = copy.deepcopy(_doc())
    next(r for r in d2["roofs"] if r.get("host"))["level"] = "L2"
    b = verts(d2)
    assert a.shape == b.shape and (a == b).all()


def test_a_cross_level_dormer_keeps_its_host_through_a_scene_round_trip(fp, win, fp3d):
    """Regression (Patrick, 2026-11-05): promoting a dormer to the storey above
    its host and serialising dropped the `host` -- `_roofs_of` names the host by
    the id its OWN level's walk minted, but the host is a floor below, in another
    bucket, so the per-level pass could not see it. With `host` gone, 3D re-datums
    the dormer to its own level and it POPS UP a storey. The cross-level resolve
    pass in `design_from_scene` keeps the link; 3D stays datumed to the host."""
    import numpy as np

    d = _dormer(win)                                    # drawn on L1, host rf1
    win.move_dormer_to_level(d, "L2")                   # a storey above its host
    out = win.design_document()
    dormer = next(r for r in out["roofs"] if r.get("level") == "L2")
    host = next(r for r in out["roofs"] if r.get("level") == "L1")
    assert dormer.get("host") == host["id"]             # the link survived

    def maxz(doc):
        m = fp3d.build_model(doc, furnishings=False, floors=True)
        return max(float(np.asarray(me.verts)[:, 2].max())
                   for me in m.meshes if me.verts is not None and len(me.verts))
    # datumed to the host (L1 base 0), not lifted to L2's base: identical extent
    assert maxz(out) == pytest.approx(maxz(_doc()))
