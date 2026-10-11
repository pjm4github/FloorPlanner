"""0258-report.md: THE HIP RUN PER END (0248 sec2 item 6) and PLAN E's POST.

A hip end ran past the ridge end by the mean of the two spans and nothing
could say otherwise -- a one-plane porch roof on a 13 ft span wanted a
4 ft hip. `hip_run_in: [end0, end1]` on the record, null = derived, the
item, the clip twin, the 3D builder, the dialog and the bridge all
reading it. And a `post`: a furnishing of form `column`, built from its
level to the underside of the roof standing over it.
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PyQt6.QtCore import QPointF

from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
from floorplanner.design.validate import schema_errors
from floorplanner.roofs import RoofItem

pytestmark = pytest.mark.walls

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fp3d():
    path = ROOT / "floorplanner" / "viewer" / "fp3d.py"
    spec = importlib.util.spec_from_file_location("fp3d_hiprun_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def roofclip():
    from floorplanner import roofclip as rc
    return rc


def _porch(hip_run=None, posts=()):
    """A one-plane porch roof like the house's: ridge along x at the house
    wall y=0 (the high edge, 131), descending +y 157 to the eave (118),
    12 in overhang, a hip at the p1 end; `posts` are (x, y) plan points."""
    rf = {"id": "rf_porch", "level": "L1", "ridge": [[0.0, 0.0], [300.0, 0.0]],
          "eaves_h_in": 118.0, "ridge_h_in": 131.0, "overhang_in": [12.0, 0.0],
          "span_in": [157.0, 0.0], "eaves_bind": "manual", "gable": [False, True],
          "marker_end": 1, "form": "shed"}
    if hip_run is not None:
        rf["hip_run_in"] = hip_run
    return {"format": "floorplanner-design", "version": 6, "units": "inches", "settings": {},
            "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0, "height_in": 120.0,
                        "kind": "storey", "reference": False}],
            "vertices": [], "walls": [], "rooms": [], "groups": [],
            "furnishings": [{"id": f"f{i}", "level": "L1", "kind": "post", "room": None,
                             "pos": [float(x), float(y)], "rotation": 0.0}
                            for i, (x, y) in enumerate(posts)],
            "roofs": [rf]}


# ---------------------------------------------------------------------------
# the record, the item, the twin
# ---------------------------------------------------------------------------

def test_the_item_takes_a_run_per_end_and_derives_the_rest(scene):
    rf = RoofItem(QPointF(0, 0), QPointF(300, 0), span_in=[157.0, 0.0], overhang_in=[12.0, 0.0],
                  gable=[False, False], form="shed", hip_run_in=[48.0, None])
    scene.addItem(rf)
    assert rf.hip_run_in == [48.0, None]
    assert rf.hip_extension(0) == (pytest.approx(48.0), pytest.approx(6.0))
    assert rf.hip_extension(1) == (pytest.approx(78.5), pytest.approx(6.0)), "the mean of the spans"
    assert rf.hip_extension(0, run=[None, None])[0] == pytest.approx(78.5), "a preview overrides"
    rf.hip_run_in = 30.0                                  # a bare number sets both
    assert rf.hip_run_in == [30.0, 30.0]
    rf.hip_run_in = None
    assert rf.hip_run_in == [None, None]
    # the footprint follows: the p1 end's eave corners sit the run plus the
    # overhang past the ridge end
    rf.hip_run_in = [48.0, None]
    e1a, _, _, _ = rf._eave_ends()
    assert e1a.x() == pytest.approx(-54.0)


def test_the_clip_twin_reads_the_run_and_agrees_with_the_item(scene, roofclip):
    doc = _porch(hip_run=[48.0, None])
    geom = roofclip.RoofGeom.from_record(doc["roofs"][0])
    assert geom.hip_run_in == [48.0, None]
    item = RoofItem(QPointF(0, 0), QPointF(300, 0), span_in=[157.0, 0.0], overhang_in=[12.0, 0.0],
                    gable=[False, True], form="shed", hip_run_in=[48.0, None])
    scene.addItem(item)
    for end in (0, 1):
        assert geom.hip_extension(end) == pytest.approx(item.hip_extension(end))
    # the hip plane descends along the ridge line over the RUN, not the mean
    h = roofclip.surface_height(geom, roofclip.Pt(-24.0, 0.0))
    assert h == pytest.approx(131.0 - (131.0 - 118.0) / 48.0 * 24.0)


def test_the_run_round_trips_through_the_document_and_an_unset_roof_writes_none(scene):
    doc = _porch(hip_run=[48.0, None])
    assert schema_errors(doc) == []
    apply_design_to_scene(scene, doc)
    rf = next(it for it in scene.items() if isinstance(it, RoofItem))
    assert rf.hip_run_in == [48.0, None]
    out = design_from_scene(scene).to_dict()
    assert out["roofs"][0]["hip_run_in"] == [48.0, None]
    assert schema_errors(out) == []
    rf.hip_run_in = None
    assert "hip_run_in" not in design_from_scene(scene).to_dict()["roofs"][0]
    bad = _porch(hip_run=[-1.0, None])
    assert schema_errors(bad), "a negative run is refused"


def test_the_end_on_dialog_offers_the_run_to_a_hip_end_and_writes_only_a_changed_one(scene):
    from floorplanner.dialogs import RoofEndOnDialog
    rf = RoofItem(QPointF(0, 0), QPointF(300, 0), span_in=[157.0, 0.0], overhang_in=[12.0, 0.0],
                  gable=[False, True], form="shed")
    scene.addItem(rf)
    dlg = RoofEndOnDialog(rf)
    other = 1 - dlg._marker_end                      # p1, the hip end
    assert dlg.sp_run[other].isEnabled() and not dlg.sp_run[dlg._marker_end].isEnabled()
    assert dlg.sp_run[other].value() == pytest.approx(78.5), "seeded with the derived run"
    assert dlg.hip_runs() == [None, None], "untouched: derived"
    dlg.sp_run[other].setValue(48.0)
    assert dlg.hip_runs() == [48.0, None]
    assert dlg.apply() and rf.hip_run_in == [48.0, None]
    # reopened, the end's own run is what it shows; a gable end's field is off
    dlg2 = RoofEndOnDialog(rf)
    assert dlg2.sp_run[other].value() == pytest.approx(48.0)
    dlg2.cb_end_other.setCurrentIndex(0)             # the hip end to a gable
    assert not dlg2.sp_run[other].isEnabled()
    assert dlg2.apply() and rf.hip_run_in == [None, None]


# ---------------------------------------------------------------------------
# the 3D builder: the hip corner on the run; a post to the roof above
# ---------------------------------------------------------------------------

def _roof_verts(model):
    return np.vstack([m.verts for m in model.meshes if m.name.startswith("roof")])


def test_the_builder_puts_the_hip_corner_on_the_run(fp3d):
    base = fp3d.build_model(_porch(), furnishings=False, floors=False)
    short = fp3d.build_model(_porch(hip_run=[48.0, None]), furnishings=False, floors=False)
    assert not short.notes, short.notes
    # the eave corner past the p1 end: mean run 78.5 + 6 before, 48 + 6 now
    assert _roof_verts(base)[:, 0].min() == pytest.approx(-84.5)
    assert _roof_verts(short)[:, 0].min() == pytest.approx(-54.0)


def test_a_post_rises_to_the_underside_of_the_roof_over_it(fp3d):
    # under the porch roof at y=150 (the surface there 131 - 13/157*150) and
    # one beyond it at y=400, where nothing stands over it
    model = fp3d.build_model(_porch(posts=[(150.0, 150.0), (150.0, 400.0)]), floors=False)
    posts = [m for m in model.meshes if m.name.startswith("furnishings:")]
    assert posts, model.notes
    v = np.vstack([m.verts for m in posts])
    under = v[abs(v[:, 1] + 150.0) < 4.0]            # world y is -plan y
    clear = v[abs(v[:, 1] + 400.0) < 4.0]
    assert under[:, 2].max() == pytest.approx(131.0 - 13.0 / 157.0 * 150.0 - fp3d.ROOF_T)
    assert under[:, 2].min() == pytest.approx(0.0)
    assert clear[:, 2].max() == pytest.approx(96.0), "the catalog height when no roof stands over it"
    assert any("no roof over them" in s for s in model.info)
    assert "column" in fp3d.BUILT_FORMS


def test_the_catalog_ships_the_post():
    manifest = json.loads((ROOT / "assets" / "furnishings" / "manifest.json").read_text(encoding="utf-8"))
    post = next(e for e in manifest if e["id"] == "post")
    assert post["form"] == "column" and (post["width_in"], post["depth_in"]) == (6, 6)
    groups = json.loads((ROOT / "assets" / "furnishings" / "groups.json").read_text(encoding="utf-8"))
    framing = next(g for g in groups if g["name"] == "Framing")
    assert "post.svg" in framing["items"]
