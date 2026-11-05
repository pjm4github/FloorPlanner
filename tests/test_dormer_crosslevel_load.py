"""A cross-level dormer -- its host roof a floor BELOW it (PR #101) -- must
survive a LOAD. The bridge used to drop any dormer whose host was not on its
own floor (`host.floor != item.floor`), silently deleting a re-levelled dormer
on reload (0292 sec2). The load now accepts a host on the dormer's floor OR the
floor directly below, matching `roofs.host_roof_at`. The floor-below is read
from the doc's own level elevations, so it does not depend on load order.
"""
import pytest

from floorplanner.design.bridge import apply_design_to_scene
from floorplanner.roofs import RoofItem

pytestmark = pytest.mark.io


def _doc(dormer_level, host_level):
    host = {"id": "h", "level": host_level, "ridge": [[-40.0, 100.0], [440.0, 100.0]],
            "eaves_h_in": 96.0, "ridge_h_in": 300.0, "overhang_in": [0.0, 0.0],
            "span_in": [170.0, 170.0], "gable": [True, True], "marker_end": 1}
    dormer = {"id": "d", "level": dormer_level, "ridge": [[200.0, 240.0], [200.0, 160.0]],
              "eaves_h_in": 180.0, "ridge_h_in": 240.0, "overhang_in": [0.0, 0.0],
              "span_in": [40.0, 40.0], "wall_span_in": [40.0, 40.0],
              "gable": [True, True], "marker_end": 0, "host": "h"}
    return {"format": "floorplanner-design", "version": 6, "units": "inches",
            "settings": {},
            "levels": [{"id": "L1", "name": "default", "elevation_in": 0.0,
                        "height_in": 96.0, "kind": "storey", "reference": False},
                       {"id": "L2", "name": "upper", "elevation_in": 100.0,
                        "height_in": 96.0, "kind": "storey", "reference": False}],
            "vertices": [], "walls": [], "rooms": [], "furnishings": [],
            "groups": [], "roofs": [host, dormer]}


def _dormers(scene):
    return [it for it in scene.items()
            if isinstance(it, RoofItem) and it.is_dormer()]


def test_a_dormer_hosted_a_floor_below_survives_the_load(scene):
    apply_design_to_scene(scene, _doc(dormer_level="L2", host_level="L1"))
    ds = _dormers(scene)
    assert len(ds) == 1, "the cross-level dormer was dropped on load"
    assert ds[0].floor == "upper"
    assert ds[0].host is not None and ds[0].host.floor == "default"


def test_a_same_floor_dormer_still_loads(scene):
    apply_design_to_scene(scene, _doc(dormer_level="L1", host_level="L1"))
    ds = _dormers(scene)
    assert len(ds) == 1
    assert ds[0].host is not None and ds[0].host.floor == "default"


def test_a_dormer_whose_host_is_above_it_is_still_skipped(scene):
    # host on L2, dormer on L1: the host is a floor UP, not down -- not a valid
    # host, so the dormer is still dropped (never a silent floating roof).
    apply_design_to_scene(scene, _doc(dormer_level="L1", host_level="L2"))
    assert _dormers(scene) == []
