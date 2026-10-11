"""A joined end's extension gets ground in its HOSTS' footprints and nowhere
else (Patrick's `short-angle-roof.json`, 2026-10-11; 0237-report.md).

Two short first-floor roofs (rf1 west, rf2 east), a 45-degree first-floor
roof (rf3) off the east end of the house, and a low second-floor roof
(rf4) whose eaves sit below the short roofs' ridges. Each short roof's
inner end is under rf4 -- a joined end -- and nowhere near rf3 (rf1) or
standing in the air above rf3 (rf2). Before the fix the extension that
closes each join under rf4 was given ground in EVERY other roof's
footprint, ran on under rf4, came out its far side and was drawn across
rf3 and across the other short roof: his report, *"the right short
section on the first floor is being projected through the joining 45
degree roof. Since the right short roof ends before intersecting the 45
degree roof it shouldn't project out to that roof."*
"""
import json
import pathlib

import pytest

from floorplanner.roofclip import (
    Lifted, RoofGeom, compute_roof_clips, footprint_polygon, surface_height,
)

pytestmark = pytest.mark.walls

FIXTURE = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "short-angle-roof.json"


def _roofs():
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    elev = {lv["id"]: float(lv["elevation_in"]) for lv in doc["levels"]}
    out = {}
    for rec in doc["roofs"]:
        g = RoofGeom.from_record(rec)
        g.clip_name = rec["id"]
        out[rec["id"]] = Lifted(g, elev[rec["level"]])
    return out


def _xs(clip):
    return [pt.x() for cell in clip.region.cells for pt in cell]


def test_the_fixture_is_the_plan_he_described():
    rf = _roofs()
    assert sorted(rf) == ["rf1", "rf2", "rf3", "rf4"]
    # the short roofs: ridges 216in, side by side on the first floor
    assert (rf["rf1"].ridge_h_in, rf["rf2"].ridge_h_in) == (216.0, 216.0)
    assert rf["rf1"].p2.x() == 120.0 and rf["rf2"].p2.x() == 354.0
    # rf4 on the second floor (96in up): eaves 156, ridge 276 absolute --
    # over both inner ends, above both ridges
    assert (rf["rf4"].eaves_h_in, rf["rf4"].ridge_h_in) == (156.0, 276.0)
    for name in ("rf1", "rf2"):
        end = rf[name].p2
        assert surface_height(rf["rf4"], end) > rf[name].ridge_h_in, name
    # rf2's end stands inside rf3's footprint, in the air above it; rf1's
    # end is nowhere near rf3
    from floorplanner.roofclip import _contains
    assert _contains(footprint_polygon(rf["rf3"]), rf["rf2"].p2)
    assert surface_height(rf["rf3"], rf["rf2"].p2) < rf["rf2"].ridge_h_in - 50
    assert not _contains(footprint_polygon(rf["rf3"]), rf["rf1"].p2)


def test_a_short_roof_joined_under_the_second_floor_roof_is_drawn_in_its_own_footprint_only():
    rf = _roofs()
    clips = compute_roof_clips(list(rf.values()))
    c1, c2 = clips[id(rf["rf1"])], clips[id(rf["rf2"])]
    # both inner ends ARE joined (under rf4): the extension exists...
    assert c1.ext[1] > 0 and c2.ext[1] > 0
    # ...and all the ground either roof draws lies within its own footprint
    assert min(_xs(c1)) >= 30.0 - 1e-6 and max(_xs(c1)) <= 120.0 + 1e-6, "rf1 came out from under rf4"
    assert min(_xs(c2)) >= 354.0 - 1e-6 and max(_xs(c2)) <= 426.0 + 1e-6, "rf2 came out from under rf4"
    # the 45-degree roof is whole and unjoined
    assert clips[id(rf["rf3"])].ext == (0.0, 0.0)
    assert all(not c.warnings for c in clips.values())


def test_the_three_way_junction_keeps_its_ground_in_a_host_the_end_stands_over():
    """The counter-case the rule must not break (0176/0177, R4g): in the
    three-ridge fixture rf2's end stands inside rf3 above its surface AND
    crosses rf1; its planes run on over rf3 to their valley because rf3
    holds the end. `test_roof_intersection.py`'s boundary invariant pins
    the geometry; this pins the reason -- rf3 is a host of that end."""
    from floorplanner.roofclip import _contains
    doc = json.loads((FIXTURE.parent / "threeRidgeFloorplan.json").read_text(encoding="utf-8"))
    rf = {}
    for rec in doc["roofs"]:
        g = RoofGeom.from_record(rec)
        g.clip_name = rec["id"]
        rf[rec["id"]] = g
    end = rf["rf2"].p2
    assert _contains(footprint_polygon(rf["rf3"]), end) and _contains(footprint_polygon(rf["rf1"]), end)
    clips = compute_roof_clips(list(rf.values()))
    # rf2 still draws ground inside rf3's footprint beyond rf1's: the valley
    inside_rf3_only = [cell for cell in clips[id(rf["rf2"])].region.cells
                       if _contains(footprint_polygon(rf["rf3"]), cell[0], tol=1e-3)]
    assert inside_rf3_only, "rf2 lost its ground over rf3 at the junction"
