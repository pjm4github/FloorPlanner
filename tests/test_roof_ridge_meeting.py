"""0248-report.md sec3 plan D, on Patrick's word ("Implement plan B and D
from 0248"): THE EQUAL-HEIGHT RIDGE MEETING.

The house model's first iteration (0248 sec2 item 5): a cross gable whose
ridge runs from the front wall back to EXACTLY the main ridge, at the
main ridge's height -- the ridges meet. The clip's joining rule saw an
end at its host's surface and extended it; the extension ran on behind
the main ridge, where the main's back slope falls away, and was drawn
there as a fin -- while the gable's own front body was pruned, so the
front showed the main's slope and no gable at all. An end that lies ON
its host's ridge line at the host's height is a meeting of ridges: the
gable's planes meet the main's along the valleys from that point to the
eave corners, which the clip finds from the surfaces alone. Nothing is
extended.
"""
import pytest

from floorplanner.roofclip import (
    RoofGeom, _area, _contains, _convex_intersection, compute_roof_clips,
)

pytestmark = pytest.mark.walls

D, W = 432.0, 720.0            # the first house model's body
EAVES, RIDGE = 24.0, 168.0     # the main roof: 8:12 over a 216 in half-span


def _main():
    return RoofGeom.from_record({"id": "rf_main", "ridge": [[0.0, D / 2], [W, D / 2]],
                                 "span_in": [D / 2, D / 2], "overhang_in": [0.0, 0.0],
                                 "eaves_h_in": EAVES, "ridge_h_in": RIDGE, "gable": [True, True]})


def _gable(cx=275.0, hw=96.0, ridge_h=RIDGE, y_back=D / 2):
    return RoofGeom.from_record({"id": "rf_left", "ridge": [[cx, D], [cx, y_back]],
                                 "span_in": [hw, hw], "overhang_in": [0.0, 0.0],
                                 "eaves_h_in": EAVES, "ridge_h_in": ridge_h, "gable": [True, True]})


def _area_in(region, x0, x1, y0, y1):
    from floorplanner.roofclip import Pt
    box = [Pt(x0, y0), Pt(x1, y0), Pt(x1, y1), Pt(x0, y1)]
    total = 0.0
    for cell in region.cells:
        piece = _convex_intersection(cell, box)
        if piece:
            total += _area(piece)
    return total


def test_a_cross_gable_meeting_the_main_ridge_at_its_height_draws_its_front_and_no_fin():
    main, gable = _main(), _gable()
    per = compute_roof_clips([main, gable])
    g, m = per[id(gable)], per[id(main)]
    assert g.ext == (0.0, 0.0), "a meeting of ridges is not a join"
    assert g.region is not None and m.region is not None
    # nothing of the gable behind the main ridge (the fin)
    assert _area_in(g.region, 0.0, W, 0.0, D / 2) == pytest.approx(0.0, abs=1.0)
    # its front body: the triangle between the valleys, from the meeting point
    # (275, 216) to the eave corners (179, 432) and (371, 432) -- half of its
    # 192 x 216 footprint
    assert _area_in(g.region, 179.0, 371.0, D / 2, D) == pytest.approx(0.5 * 192.0 * 216.0, rel=0.02)
    # the main keeps everything else in front: its full strip minus that triangle
    front = _area_in(m.region, 0.0, W, D / 2, D)
    assert front == pytest.approx(W * D / 2 - 0.5 * 192.0 * 216.0, rel=0.02)
    # and all of its back
    assert _area_in(m.region, 0.0, W, 0.0, D / 2) == pytest.approx(W * D / 2, rel=0.01)
    assert not g.warnings and not m.warnings


def test_the_same_gable_four_inches_under_the_ridge_is_the_control():
    """The workaround the house model used: the gable's ridge 4in under the
    main's, ending where it meets the main slope -- a join, extended under
    the main, the same front triangle (to within the 4in)."""
    y_back = D / 2 + 4.0 / ((RIDGE - EAVES) / (D / 2))
    main, gable = _main(), _gable(ridge_h=RIDGE - 4.0, y_back=y_back)
    per = compute_roof_clips([main, gable])
    g = per[id(gable)]
    assert g.ext[1] > 0.0
    assert _area_in(g.region, 0.0, W, 0.0, D / 2) == pytest.approx(0.0, abs=1.0)
    assert _area_in(g.region, 179.0, 371.0, D / 2, D) == pytest.approx(0.5 * 192.0 * 216.0, rel=0.05)


def test_a_lower_cross_gable_ending_on_the_main_slope_is_still_a_join():
    """A lower cross gable whose ridge ends where it meets the main slope
    is a join as before: extended, its planes running under the main, no
    fin behind (the main is higher there). (An end sketched PAST that
    point, buried under the main, still draws a fin where its extension
    comes out the back slope -- a residual named in the report, not this
    plan's.)"""
    drop = 40.0
    main, gable = _main(), _gable(ridge_h=RIDGE - drop, y_back=D / 2 + drop / ((RIDGE - EAVES) / (D / 2)))
    per = compute_roof_clips([main, gable])
    g = per[id(gable)]
    assert g.ext == (0.0, pytest.approx(1679.3, abs=0.1))
    assert _area_in(g.region, 0.0, W, 0.0, D / 2) == pytest.approx(0.0, abs=1.0)
    assert not g.warnings


def test_a_shed_porch_whose_high_edge_lies_on_the_main_eaves_at_its_height_is_a_tie_that_draws_both():
    """The other tie the house model met (0250 sec1): a porch roof, on the
    floor below, whose high edge sits ON the main's front eaves line at
    exactly the eaves height. Both draw their own ground; the main keeps
    its whole front strip."""
    from floorplanner.roofclip import Lifted
    main = Lifted(_main(), 108.0)
    porch = RoofGeom.from_record({"id": "rf_porch", "ridge": [[0.0, D], [W, D]], "form": "shed",
                                  "span_in": [96.0, 0.0], "overhang_in": [12.0, 0.0],
                                  "eaves_h_in": 108.0 + EAVES - 24.0, "ridge_h_in": 108.0 + EAVES,
                                  "gable": [True, True]})
    porch = Lifted(porch, 0.0)
    per = compute_roof_clips([main, porch])
    m, p = per[id(main)], per[id(porch)]
    if m.region is not None:
        assert _area_in(m.region, 0.0, W, D / 2, D) == pytest.approx(W * D / 2, rel=0.01)
    if p.region is not None:
        assert _area_in(p.region, 0.0, W, D, D + 108.0) == pytest.approx(W * 108.0, rel=0.01)
    assert not m.warnings and not p.warnings
    assert all(not _contains(cell, type(cell[0])(360.0, D / 2 + 50.0)) for cell in (p.region.cells if p.region else []))
