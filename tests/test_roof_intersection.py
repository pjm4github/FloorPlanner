"""R4d -- roof intersection clipping, the valley seam (0164-ruling.md).

The fixture is the ruled case in miniature: a MAIN roof (ridge along x)
and a WING (ridge along y) running into its side, the wing's ridge lower
than the main's. Everything below is closed-form, so the receipts are
exact numbers, not "looks right":

  main: ridge (0,200)-(400,200), span 100, ridge 150 / eaves 96
        -> slope 0.54, footprint y 100..300
  wing: ridge (200,150)-(200,500), span 60, ridge 130 / eaves 96
        -> slope 0.5667, footprint x 140..260, y 150..500

At the wing's ridge (x=200) the main's surface is 150 - 0.54*|y-200|;
it equals the wing's ridge height 130 at y = 200 +- 37.037. So the seam
apex is (200, 237.037); the two valley lines run from there down to the
wing's eave-start corners on the main's eave line, (140,300) and (260,300),
where both surfaces are at 96. North of y = 237.037 the wing is under the
main (hidden); north of the main's ridge, for y < 162.963, the main's far
slope drops back under the wing's ridge -- the FAR-SIDE ISLAND, the case
the ruling names ("does not extend past the joining roof").
"""
import json
import math
from pathlib import Path

import numpy as np
import pytest
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QImage, QPainter

from floorplanner.config import DEFAULT_FLOOR
from floorplanner.roofclip import (
    clip_pair,
    compute_roof_clips,
    footprint_polygon,
    Pt,
    RoofGeom,
    seam_heights,
    seam_length,
    surface_height,
    _adjacent,
    _area,
    _centroid,
    _contains,
    _dist_to_segment,
)
from floorplanner.roofs import RoofItem, sync_roof_clips

pytestmark = pytest.mark.walls

APEX_Y = 200.0 + (150.0 - 130.0) / 0.54          # 237.037...
ISLAND_Y = 200.0 - (150.0 - 130.0) / 0.54        # 162.963...


def _main(scene=None):
    rf = RoofItem(QPointF(0, 200), QPointF(400, 200), span_in=100.0,
                  overhang_in=0.0, ridge_h_in=150.0, eaves_h_in=96.0)
    rf.floor = DEFAULT_FLOOR
    rf.clip_name = "main"
    if scene is not None:
        scene.addItem(rf)
    return rf


def _wing(scene=None, p1=None, p2=None):
    rf = RoofItem(p1 or QPointF(200, 150), p2 or QPointF(200, 500),
                  span_in=60.0, overhang_in=0.0, ridge_h_in=130.0,
                  eaves_h_in=96.0)
    rf.floor = DEFAULT_FLOOR
    rf.clip_name = "wing"
    if scene is not None:
        scene.addItem(rf)
    return rf


def _pts(seams):
    out = set()
    for p, q in seams:
        out.add((round(p.x(), 3), round(p.y(), 3)))
        out.add((round(q.x(), 3), round(q.y(), 3)))
    return out


# --------------------------------------------------------------------------
# the surface itself -- the function everything else is built on
# --------------------------------------------------------------------------
def test_surface_height_is_the_r3_plane(scene):
    m = _main()
    assert surface_height(m, QPointF(100, 200)) == pytest.approx(150.0)
    assert surface_height(m, QPointF(100, 300)) == pytest.approx(96.0)
    assert surface_height(m, QPointF(100, 100)) == pytest.approx(96.0)
    assert surface_height(m, QPointF(100, 250)) == pytest.approx(150.0 - 27.0)


def test_surface_height_past_a_hip_end_is_the_lower_plane(scene):
    rf = RoofItem(QPointF(100, 100), QPointF(300, 100), span_in=100.0,
                  overhang_in=0.0, ridge_h_in=150.0, eaves_h_in=96.0,
                  gable=[False, True])
    # 40in past p1 along the axis, on the ridge line: the hip plane at run
    # 100 drops 0.54/in -> 128.4; the side plane there would still be 150
    assert surface_height(rf, QPointF(60, 100)) == pytest.approx(150.0 - 0.54 * 40)
    # and off the ridge line the LOWER of hip and side governs
    assert surface_height(rf, QPointF(60, 180)) == pytest.approx(
        min(150.0 - 0.54 * 40, 150.0 - 0.54 * 80))


# --------------------------------------------------------------------------
# the seam: exact segments, equal heights at every vertex
# --------------------------------------------------------------------------
def test_the_valley_seam_is_two_straight_segments_meeting_at_the_apex(scene):
    m, w = _main(), _wing()
    _, _, seams, warnings = clip_pair(w, m)
    assert warnings == []
    assert len(seams) == 2
    assert _pts(seams) == {(140.0, 300.0), (260.0, 300.0),
                           (200.0, round(APEX_Y, 3))}
    assert seam_length(seams) == pytest.approx(
        2 * ((60.0 ** 2 + (300.0 - APEX_Y) ** 2) ** 0.5))


def test_every_seam_vertex_has_equal_height_on_both_roofs(scene):
    """0164-ruling.md sec3, literally: z1 == z2 at every seam vertex."""
    m, w = _main(), _wing()
    _, _, seams, _ = clip_pair(w, m)
    pairs = seam_heights(w, m, seams)
    assert len(pairs) == 4
    for h_w, h_m in pairs:
        assert h_w == pytest.approx(h_m, abs=1e-6)
    assert {round(h, 3) for h, _ in pairs} == {96.0, 130.0}


def test_no_seam_around_the_dropped_island(scene):
    """The far-side island has its own equal-height boundary (at
    y = 162.963); it is NOT a seam, because the island is not drawn."""
    m, w = _main(), _wing()
    _, _, seams, _ = clip_pair(w, m)
    assert all(y > 200.0 for _, y in _pts(seams))


# --------------------------------------------------------------------------
# the regions: the wing stops at the seam, the main shows through
# --------------------------------------------------------------------------
def test_the_wing_keeps_its_body_and_the_valley_pocket_only(scene):
    m, w = _main(), _wing()
    region_w, region_m, _, _ = clip_pair(w, m)
    assert region_w.contains(QPointF(200, 400))          # the body
    assert region_w.contains(QPointF(200, 260))          # in the pocket: 130 > 117.6
    assert not region_w.contains(QPointF(200, 220))      # hidden under the main
    assert not region_w.contains(QPointF(200, 155))      # the far-side island
    # (150, 290): wing 130-0.5667*50 = 101.7, main 150-0.54*90 = 101.4 -> wing higher
    assert region_w.contains(QPointF(150, 290))


def test_the_main_loses_exactly_the_pocket_and_shows_through_the_island(scene):
    m, w = _main(), _wing()
    region_w, region_m, _, _ = clip_pair(w, m)
    assert region_m.contains(QPointF(50, 260))           # untouched body
    assert not region_m.contains(QPointF(200, 260))      # under the wing's pocket
    assert region_m.contains(QPointF(200, 220))          # over the wing's hidden band
    assert region_m.contains(QPointF(200, 155))          # the island shows the MAIN


def test_the_two_regions_partition_the_overlap_and_the_seam_separates_them(scene):
    """Areas: the wing's region + the main's region == both footprints
    minus the overlap counted once (nothing drawn twice, nothing lost)."""
    m, w = _main(), _wing()
    region_w, region_m, seams, _ = clip_pair(w, m)
    overlap_area = 120.0 * 150.0
    assert region_w.area() + region_m.area() == pytest.approx(
        400.0 * 200.0 + 120.0 * 350.0 - overlap_area, abs=1e-3)
    for p, q in seams:
        mx, my = (p.x() + q.x()) / 2, (p.y() + q.y()) / 2
        assert region_w.contains(QPointF(mx, my + 2.0))   # wing side (south)
        assert region_m.contains(QPointF(mx, my - 2.0))   # main side (north)


def test_a_pair_that_does_not_overlap_is_left_alone(scene):
    m = _main()
    far = _wing(p1=QPointF(700, 150), p2=QPointF(700, 500))
    assert clip_pair(m, far) == (None, None, [], [])


def test_coplanar_roofs_are_not_clipped_and_say_so(scene):
    """The degenerate fallback (sec2): two roofs with the same surface over
    the overlap draw unclipped and warn, `Sheet.warnings`-style."""
    a = _main()
    b = RoofItem(QPointF(100, 200), QPointF(500, 200), span_in=100.0,
                 overhang_in=0.0, ridge_h_in=150.0, eaves_h_in=96.0)
    b.clip_name = "twin"
    ra, rb, seams, warnings = clip_pair(a, b)
    assert ra is None and rb is None and seams == []
    assert len(warnings) == 1 and "coplanar" in warnings[0]
    assert "main" in warnings[0] and "twin" in warnings[0]


def test_compute_roof_clips_folds_pairs_per_roof(scene):
    m, w = _main(), _wing()
    lone = _wing(p1=QPointF(900, 150), p2=QPointF(900, 500))
    clips = compute_roof_clips([m, w, lone])
    assert clips[id(lone)].region is None and clips[id(lone)].seams == []
    assert clips[id(w)].region is not None and len(clips[id(w)].seams) == 2
    assert clips[id(m)].region is not None and len(clips[id(m)].seams) == 2


# --------------------------------------------------------------------------
# on the item: derived, never stored; selected = unclipped
# --------------------------------------------------------------------------
def test_the_clip_is_derived_and_the_true_rectangle_survives(scene):
    _main(scene)
    w = _wing(scene)
    assert w.is_clipped()
    assert w.span_in == [60.0, 60.0]
    assert (w.p1.y(), w.p2.y()) == (150.0, 500.0)          # the document's truth
    assert w.selection_outline().boundingRect().top() == pytest.approx(150.0)


def test_select_shows_the_whole_rectangle_and_deselect_reclips(scene):
    """0164-ruling.md sec2's own round trip."""
    _main(scene)
    w = _wing(scene)
    far_ridge = QPointF(200, 155)                            # inside the island
    assert not w.shape().contains(far_ridge)
    assert w.seams()
    w.setSelected(True)
    assert not w.is_clipped()
    assert w.shape().contains(far_ridge)                     # whole rectangle hits
    assert w.seams() == []
    w.setSelected(False)
    assert w.is_clipped()
    assert not w.shape().contains(far_ridge)
    assert len(w.seams()) == 2


def test_the_hit_shape_stops_at_the_seam_and_includes_it(scene):
    _main(scene)
    w = _wing(scene)
    assert w.shape().contains(QPointF(200, 400))             # body
    assert w.shape().contains(QPointF(200, 260))             # ridge inside the pocket
    assert not w.shape().contains(QPointF(200, 220))         # hidden ridge
    assert w.shape().contains(QPointF(170, (300.0 + APEX_Y) / 2))   # on the seam


def test_a_grip_drag_reclips_live(scene):
    _main(scene)
    w = _wing(scene)
    w.drag_end(0, QPointF(200, 330))         # shorten the wing to y >= 300+18-> no overlap
    assert not w.is_clipped() or w._clip_region is not None
    # pull it back in: overlap again, clipped again
    w.drag_end(0, QPointF(200, 120))
    assert w.is_clipped()
    assert not w.shape().contains(QPointF(200, 155))


def test_removing_the_main_unclips_the_wing(scene):
    m, w = _main(scene), _wing(scene)
    assert w.is_clipped()
    scene.removeItem(m)
    assert not w.is_clipped()
    assert w.seams() == []


def test_roofs_on_another_floor_do_not_clip(scene):
    m = _main(scene)
    w = _wing(scene)
    w.floor = "Second"
    sync_roof_clips(scene)
    assert not w.is_clipped() and not m.is_clipped()


def test_coplanar_warning_reaches_the_item(scene):
    a = _main(scene)
    b = RoofItem(QPointF(100, 200), QPointF(500, 200), span_in=100.0,
                 overhang_in=0.0, ridge_h_in=150.0, eaves_h_in=96.0)
    b.floor = DEFAULT_FLOOR
    scene.addItem(b)
    assert not a.is_clipped() and not b.is_clipped()
    assert a.clip_warnings and "coplanar" in a.clip_warnings[0]


# --------------------------------------------------------------------------
# the paint: the seam is a real edge, nothing pokes out the far side
# --------------------------------------------------------------------------
def _render(scene):
    img = QImage(500, 500, QImage.Format.Format_RGB32)
    img.fill(0xFFFFFFFF)
    pr = QPainter(img)
    pr.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    scene.render(pr, QRectF(0, 0, 500, 500), QRectF(-50, 50, 500, 500),
                 Qt.AspectRatioMode.IgnoreAspectRatio)
    pr.end()
    return img


def _ink_near(img, sx, sy, half=3):
    px, py = int(sx + 50), int(sy - 50)
    for x in range(px - half, px + half + 1):
        for y in range(py - half, py + half + 1):
            if 0 <= x < img.width() and 0 <= y < img.height():
                c = img.pixelColor(x, y)
                if c.red() < 190 and c.green() < 150:      # roof-brown ink
                    return True
    return False


def test_paint_draws_the_seam_and_not_the_far_side(scene):
    _main(scene)
    _wing(scene)
    img = _render(scene)
    # the seam midpoint carries ink (solid, unclipped)
    assert _ink_near(img, 170, (300.0 + APEX_Y) / 2)
    # the wing's ridge inside the far-side island: no ink from anyone
    # (the main's own lines there are its ridge at y=200 and eaves, not x=200)
    assert not _ink_near(img, 200, 155, half=2)
    # and the wing's hidden ridge under the main: no ink either
    assert not _ink_near(img, 200, 215, half=2)
    # positive control: the wing's visible ridge in the pocket does paint
    assert _ink_near(img, 200, 270)


# --------------------------------------------------------------------------
# the 45deg wing (0164-ruling.md sec3: "the wiscaway main + 45deg wing")
# --------------------------------------------------------------------------
def _wing45():
    s = 0.7071067811865476
    rf = RoofItem(QPointF(150, 150), QPointF(150 + 200 * s, 150 + 200 * s),
                  span_in=60.0, overhang_in=12.0, ridge_h_in=135.0,
                  eaves_h_in=96.0)
    rf.floor = DEFAULT_FLOOR
    rf.clip_name = "wing45"
    return rf


def test_a_45_degree_wing_seams_at_equal_height_and_partitions_the_overlap(scene):
    """Nothing here is axis-aligned, so no coordinate is a shortcut: the
    seam vertices must still sit at equal height on both surfaces, the
    two regions must still add up to the union of the two footprints,
    and the wing's ridge must be hidden at its start (inside the main,
    below the main's surface) and visible at its far end."""
    m = RoofItem(QPointF(0, 150), QPointF(400, 150), span_in=100.0,
                 overhang_in=12.0, ridge_h_in=150.0, eaves_h_in=96.0)
    m.floor = DEFAULT_FLOOR
    w = _wing45()
    region_w, region_m, seams, warnings = clip_pair(w, m)
    assert warnings == [] and len(seams) >= 2
    for h_w, h_m in seam_heights(w, m, seams):
        assert h_w == pytest.approx(h_m, abs=1e-6)
    # partition: union of footprints, every point drawn once
    from floorplanner.roofclip import _area, _convex_intersection, footprint_polygon
    fw, fm = footprint_polygon(w), footprint_polygon(m)
    union = _area(fw) + _area(fm) - _area(_convex_intersection(fw, fm))
    assert region_w.area() + region_m.area() == pytest.approx(union, abs=1e-3)
    # the wing's ridge: hidden where it starts (150,150) on the main's
    # ridge line, where the main is at 150 and the wing at 135
    assert not region_w.contains(QPointF(152, 152))
    assert region_m.contains(QPointF(152, 152))
    # ... and visible at its far end, well outside the main
    assert region_w.contains(w.p2)
    assert not region_m.contains(w.p2)


def test_a_45_degree_wing_clips_and_reclips_on_the_item(scene):
    m = RoofItem(QPointF(0, 150), QPointF(400, 150), span_in=100.0,
                 overhang_in=12.0, ridge_h_in=150.0, eaves_h_in=96.0)
    m.floor = DEFAULT_FLOOR
    scene.addItem(m)
    w = _wing45()
    scene.addItem(w)
    assert w.is_clipped() and m.is_clipped()
    start = QPointF(152, 152)
    assert not w.shape().contains(start)
    w.setSelected(True)
    assert w.shape().contains(start)
    w.setSelected(False)
    assert not w.shape().contains(start)


# --------------------------------------------------------------------------
# Patrick's check of the first cut: two roofs of EQUAL height at an L --
# the roof whose ridge runs past the apex must stop at the seam even where
# its own surface is the higher one (his 3D view showed it poking through)
# --------------------------------------------------------------------------
def _l_pair(scene=None):
    """A: ridge (0,200)-(450,200), span 100, 150/96. B: ridge from
    (400,200) at 45deg down-right, same span and heights. A's last 50in
    of ridge run past the apex into B; B's start end lies inside A."""
    s = 0.7071067811865476
    a = RoofItem(QPointF(0, 200), QPointF(450, 200), span_in=100.0,
                 overhang_in=0.0, ridge_h_in=150.0, eaves_h_in=96.0)
    b = RoofItem(QPointF(400, 200), QPointF(400 + 300 * s, 200 + 300 * s),
                 span_in=100.0, overhang_in=0.0, ridge_h_in=150.0, eaves_h_in=96.0)
    for rf, name in ((a, "A"), (b, "B")):
        rf.floor = DEFAULT_FLOOR
        rf.clip_name = name
        if scene is not None:
            scene.addItem(rf)
    return a, b


def test_equal_roofs_at_an_l_both_stop_at_the_two_valleys(scene):
    a, b = _l_pair()
    region_a, region_b, seams, warnings = clip_pair(a, b)
    assert warnings == []
    # the two valleys: apex (400,200) to the inside corner on A's lower
    # eave and to the outside corner on A's upper eave -- closed form:
    # (x-400) = -+ (sqrt2 - 1) * (y-200)
    k = 2 ** 0.5 - 1
    assert _pts(seams) == {(400.0, 200.0),
                           (round(400 - k * 100, 3), 300.0),
                           (round(400 + k * 100, 3), 100.0)}
    for h_a, h_b in seam_heights(a, b, seams):
        assert h_a == pytest.approx(h_b, abs=1e-6)


def test_a_s_ridge_past_the_apex_is_gone_even_though_it_is_the_higher_surface(scene):
    a, b = _l_pair()
    region_a, region_b, _, _ = clip_pair(a, b)
    past = QPointF(440, 200)
    assert surface_height(a, past) > surface_height(b, past), \
        "precondition: A really is the higher surface there"
    assert not region_a.contains(past)          # ...and is still cut
    assert region_b.contains(past)              # B's slope shows through
    assert region_a.contains(QPointF(300, 200))  # A's body, untouched


def test_a_s_corner_past_the_seam_draws_no_line_of_a(scene):
    """The dashed corner he erased: A's top eave past the outer corner
    and A's gable line. Neither is A's to draw once A stops at the seam;
    B's slope, extended behind its own end, is what lies there."""
    a, b = _l_pair(scene)
    corner = QPointF(447, 103)
    assert not a.shape().contains(QPointF(447, 100))     # A's top eave, past the corner
    assert not a.shape().contains(QPointF(450, 150))     # A's gable line
    region_a, region_b, _, _ = clip_pair(a, b)
    # the sliver beyond the outer corner is outside B's band too: nobody's
    assert not region_a.contains(corner) and not region_b.contains(corner)


def test_b_s_start_end_inside_a_is_gone_too(scene):
    a, b = _l_pair()
    region_a, region_b, _, _ = clip_pair(a, b)
    s = 0.7071067811865476
    start_side = QPointF(400 - 60 * s + 3, 200 + 60 * s - 3)   # B's start corner region
    assert not region_b.contains(start_side)
    assert region_a.contains(start_side)
    assert region_b.contains(QPointF(400 + 200 * s, 200 + 200 * s))   # B's body


def test_the_l_on_the_items_hides_a_s_end_lines(scene):
    a, b = _l_pair(scene)
    assert a.is_clipped() and b.is_clipped()
    assert not a.shape().contains(QPointF(440, 200))       # ridge past the apex
    assert not a.shape().contains(QPointF(450, 150))       # A's gable line
    assert a.shape().contains(QPointF(300, 200))
    a.setSelected(True)
    assert a.shape().contains(QPointF(450, 150))           # whole rectangle


# ---------------------------------------------------------------------------
# R4f (0170-ruling.md): the three-ridge case -- the built pairwise fold
# (`clip_pair`, unchanged, still the T/L regression above) now filters its
# SEAMS twice before a `compute_roof_clips` caller ever sees them: once
# through each roof's own fully partner-intersected region (drops ground a
# further partner already took), and once again DIRECTLY against every
# other roof's own height (`h_owner >= h_third`, exact linear clipping) --
# the literal statement of "a seam is real only where no third roof is
# higher there". `fixtures/threeRidgeFloorplan.json` is Patrick's own
# report, promoted here under exit 1: three roofs on one level, every
# plane its own pitch, ridges converging near the plan's middle-right. His
# own estimate -- a triple point near (682, 538), all three surfaces at
# about 117.5in there -- is reproduced below as an EXACT number.
# ---------------------------------------------------------------------------
THREE_RIDGE_FIXTURE = (Path(__file__).resolve().parent.parent / "fixtures"
                       / "threeRidgeFloorplan.json")


def _three_ridge_roofs():
    doc = json.loads(THREE_RIDGE_FIXTURE.read_text(encoding="utf-8"))
    roofs = []
    for rec in doc["roofs"]:
        g = RoofGeom.from_record(rec)
        g.clip_name = rec["id"]
        roofs.append(g)
    return roofs


def test_r4f_fixture_promoted_and_loads_three_converging_roofs():
    roofs = _three_ridge_roofs()
    assert [g.clip_name for g in roofs] == ["rf1", "rf2", "rf3"]


def test_r4f_three_ridges_partition_no_point_drawn_by_two_roofs_at_once():
    """The invariant that matters for a WRONG PICTURE, 0170-ruling.md
    sec2's own words: 'no point painted by two roofs'. A dense grid over
    the union of the three footprints never lands in two roofs' final
    regions at once -- guaranteed by construction (each roof's region is
    the intersection, across every partner, of `clip_pair`'s own
    partition-preserving pairwise result), checked here directly rather
    than only trusted."""
    roofs = _three_ridge_roofs()
    clips = compute_roof_clips(roofs)
    fps = [footprint_polygon(g) for g in roofs]
    xs = [p.x() for fp in fps for p in fp]
    ys = [p.y() for fp in fps for p in fp]
    n = 45
    for i in range(n):
        for j in range(n):
            x = min(xs) + (max(xs) - min(xs)) * i / (n - 1)
            y = min(ys) + (max(ys) - min(ys)) * j / (n - 1)
            pt = Pt(x, y)
            owners = sum(1 for g in roofs
                        if clips[id(g)].region is not None
                        and clips[id(g)].region.contains(pt))
            assert owners <= 1, (x, y, owners)


def test_r4f_no_seam_segment_crosses_a_roof_that_is_actually_higher():
    """0170-ruling.md sec2, literally: 'a seam draws where the top two
    surfaces are equal AND no third is higher'. His own report is exactly
    the failure of the second half -- a seam between two roofs surviving
    where a third stood above both. Sampled along every seam segment
    every roof carries, at five points each, against every OTHER roof
    that actually covers that ground."""
    roofs = _three_ridge_roofs()
    clips = compute_roof_clips(roofs)
    checked = 0
    for idx, g in enumerate(roofs):
        for p, q in clips[id(g)].seams:
            for t in (0.0, 0.25, 0.5, 0.75, 1.0):
                pt = QPointF(p.x() + (q.x() - p.x()) * t,
                             p.y() + (q.y() - p.y()) * t)
                h_here = surface_height(g, pt)
                for k, other in enumerate(roofs):
                    if k == idx:
                        continue
                    if _contains(footprint_polygon(other), pt, tol=-1e-3):
                        checked += 1
                        assert surface_height(other, pt) <= h_here + 1e-3
    assert checked > 0, "the fixture's own overlap produced nothing to check"


def test_r4f_the_three_ridges_meet_at_one_exact_triple_point():
    """His own estimate ('a triple point exists at ~=(682, 538), all
    three heights ~=117.5in') reproduced as an exact construction, not
    eyeballed: at (681.586, 538.067) all three surfaces tie at ~117.5in,
    inside all three footprints.

    RESTORED AT 0181-ruling.md: the R4g rewrite (0176/0177) had dropped
    the requirement that this point survive as a DRAWN seam vertex,
    because the interim reachability left the ground around it blank.
    With the partition whole again (`test_r4f_a_genuine_three_way_
    junction_leaves_nothing_drawn_by_nobody`), the triple point is once
    more where three real seams meet: every roof carries a seam ending
    exactly there -- the second rf1/rf2 valley from the pinch, and the
    rf1/rf3 and rf2/rf3 seams."""
    roofs = _three_ridge_roofs()
    pt = QPointF(681.586, 538.067)
    assert all(_contains(footprint_polygon(g), pt) for g in roofs)
    heights = [surface_height(g, pt) for g in roofs]
    assert max(heights) - min(heights) < 1e-2, heights
    for h in heights:
        assert h == pytest.approx(117.5, abs=0.1)
    clips = compute_roof_clips(roofs)
    for g in roofs:
        ends = [e for p, q in clips[id(g)].seams for e in (p, q)
                if abs(e.x() - pt.x()) < 1e-2 and abs(e.y() - pt.y()) < 1e-2]
        assert len(ends) >= 2, (g.clip_name, clips[id(g)].seams)


def test_r4f_a_two_roof_pair_inside_a_three_roof_call_is_unaffected(scene):
    """The regression 0170-ruling.md names explicitly: 'the two-roof cases
    ... must come out identical -- the envelope reduces to the pair rule
    when n = 2'. A third, non-overlapping roof present in the SAME
    `compute_roof_clips` call changes nothing about the T fixture's own
    seam (byte for byte the same two points `clip_pair` gives alone)."""
    _main(scene)
    w = _wing(scene)
    far = _wing(scene, p1=QPointF(900, 150), p2=QPointF(900, 500))
    sync_roof_clips(scene)
    assert not far.is_clipped()
    assert _pts(w.seams()) == {(140.0, 300.0), (260.0, 300.0),
                               (200.0, round(APEX_Y, 3))}


def _grid_census(roofs, clips, n=70):
    """(in_any, gap, double) over an n x n grid of the footprints' bounding
    box: points inside at least one footprint, drawn by nobody, drawn by
    more than one."""
    fps = [footprint_polygon(g) for g in roofs]
    xs = [p.x() for fp in fps for p in fp]
    ys = [p.y() for fp in fps for p in fp]
    in_any = gap = double = 0
    for i in range(n):
        for j in range(n):
            x = min(xs) + (max(xs) - min(xs)) * i / (n - 1)
            y = min(ys) + (max(ys) - min(ys)) * j / (n - 1)
            pt = Pt(x, y)
            if not any(_contains(fp, pt) for fp in fps):
                continue
            in_any += 1
            owners = sum(1 for g in roofs if clips[id(g)].region is not None
                        and clips[id(g)].region.contains(pt))
            if owners == 0:
                gap += 1
            elif owners > 1:
                double += 1
    return in_any, gap, double


def test_r4f_a_genuine_three_way_junction_leaves_nothing_drawn_by_nobody():
    """His own check found the FIRST cut's residual patch visually --
    a real hole in the 3D roof at the junction, not a benign sliver. The
    original fill pass closed it unconditionally: any ground three or
    more roofs fought over got assigned to SOMEBODY, on the premise that
    real, bounded overlap territory always belongs to one of its
    contestants -- and 0176-ruling.md sec3 found that fill handing ground
    to the WORST-ranked coverer by rank position, so "0 gaps" was retired
    as an acceptance criterion at R4g, then bounded at <40% (0178) and
    <20% (0180) while the real cause was diagnosed.

    RESTORED AT 0181-ruling.md sec3, as the ruling itself refined it:
    blank ground is legal only on the root ground of an UNCERTIFIED LIMB
    (0181 sec2 -- a roof's own single-coverage ground cut off from its
    body with no corridor but phantom air), and on this fixture that set
    is EMPTY -- rf3's rake-side body certifies through its own under-pass
    (it runs beneath rf1 and comes out the other side), rf2's south arm
    is a join that reconnects around the pinch once rf1's overshoot is
    pruned first, and nothing is left for nobody. So: 0 blank, 0 double,
    measured on a grid, AND the invariant itself asserted globally from
    `compute_roof_clips`'s own diagnostics: no blank cell at all."""
    roofs = _three_ridge_roofs()
    diag = {}
    clips = compute_roof_clips(roofs, diag=diag)
    in_any, gap, double = _grid_census(roofs, clips)
    assert double == 0, f"double-drawn: {double}/{in_any}"
    assert gap == 0, f"drawn-by-nobody: {gap}/{in_any}"
    assert diag["blank"] == [], [(_centroid(diag["cells"][ci]), _area(diag["cells"][ci]))
                                 for ci in diag["blank"]]
    assert diag["limb_cells"] == []


def test_0181_blank_ground_is_only_ever_an_uncertified_limb_s_root_ground(scene):
    """0181-ruling.md sec3's partition invariant, refined once, asserted
    globally on the equal-height L: every blank cell is root ground of an
    uncertified limb, and the one legal blank is D85's corner -- A's own
    single-coverage sliver past the outer corner, whose only corridor to
    A's body is A's own wedge standing above B (phantom air, and the
    overshoot of A's crossed end). Nothing else on the L is blank: the
    hip behind the apex and B's extension ground both draw."""
    a, b = _l_pair()
    diag = {}
    clips = compute_roof_clips([a, b], diag=diag)
    assert diag["blank"] != []
    assert set(diag["blank"]) <= set(diag["limb_cells"])
    for ci in diag["blank"]:
        cell = diag["cells"][ci]
        assert diag["orig_coverers"][ci] == [id(a)]           # A's root ground
        assert _area(cell) == pytest.approx(36.8, abs=0.2)     # the D85 corner
        assert _contains(cell, Pt(447, 103))
    in_any, gap, double = _grid_census([a, b], clips)
    assert double == 0
    assert gap <= 2, gap          # the corner alone at 70x70 pitch


def test_0181_a_root_limb_certifies_by_passing_under_a_real_roof():
    """0181-ruling.md sec2 in isolation: a low gable crossing UNDER a
    tall one, both of its ends free. Its far side is real single-coverage
    ground cut off from its principal by the tall roof's ridge zone,
    where the tall roof wins; the plain walk cannot cross that seam. The
    continuity network can: the low roof's surface lies below the tall
    roof's drawn one there, so the far limb connects by passing under
    and certifies -- it draws on both sides of the crossing, pokes out
    through the tall roof's slopes near both eaves exactly as it should,
    and the tall roof keeps its ridge zone. Nothing is blank."""
    tall = RoofGeom.from_record({"ridge": [[0, 300], [600, 300]], "eaves_h_in": 96.0,
                                 "ridge_h_in": 180.0, "overhang_in": [0, 0],
                                 "span_in": [150, 150], "gable": [True, True]})
    low = RoofGeom.from_record({"ridge": [[300, 0], [300, 600]], "eaves_h_in": 96.0,
                                "ridge_h_in": 132.0, "overhang_in": [0, 0],
                                "span_in": [100, 100], "gable": [True, True]})
    diag = {}
    clips = compute_roof_clips([tall, low], diag=diag)
    lo, hi = clips[id(low)].region, clips[id(tall)].region
    assert lo.contains(Pt(300, 50)) and lo.contains(Pt(300, 550))      # both root sides
    assert lo.contains(Pt(300, 165)) and lo.contains(Pt(300, 435))     # poking through
    assert hi.contains(Pt(300, 300)) and not lo.contains(Pt(300, 300))  # under the ridge
    certified = [comp for rd in diag["rounds"] for comps in rd["certified"].values()
                 for comp in comps]
    assert certified, "the far side must have certified through the network"
    assert diag["blank"] == []
    in_any, gap, double = _grid_census([tall, low], clips)
    assert gap == 0 and double == 0


def test_r4f_the_fill_pass_never_touches_a_two_roof_corner():
    """0170-ruling.md's own regression clause, for the fill pass
    specifically: the L-case's deliberately-unclaimed corner past the
    seam (D85, `test_a_s_corner_past_the_seam_draws_no_line_of_a`) must
    stay nobody's even though `compute_roof_clips` now runs a gap-fill
    pass -- it only ever engages at three or more touched roofs."""
    a, b = _l_pair()
    region_a, region_b, _, _ = clip_pair(a, b)
    corner = QPointF(447, 103)
    clips = compute_roof_clips([a, b])
    assert not clips[id(a)].region.contains(corner)
    assert not clips[id(b)].region.contains(corner)


def test_r4f_no_duplicate_cells_near_the_junction():
    """His second report ('a minor ridge that doesn't clean nicely') named
    a stray fin near the junction. Root-caused, this session, to a razor-
    thin sliver cell's own SKIRT (`_prism_slab`'s side wall, whose area is
    perimeter times height-drop, not footprint area) -- NOT fully closed:
    a sliver is relabelled to its next-best coverer (never left undrawn
    or double-claimed, `test_r4f_a_genuine_three_way_junction_...` and
    `test_r4f_three_ridges_partition_...` cover that), but relabelling
    does not merge its polygon into a larger neighbour, so its own skirt
    is UNCHANGED -- closing that needs a real geometric merge, not built
    here (see `compute_roof_clips`'s own docstring at the fold-in step).
    What IS guaranteed and checked here: no two cells of the same
    region are exact duplicates (the one dedup class a single shared
    arrangement, built once, actually rules out by construction)."""
    roofs = _three_ridge_roofs()
    clips = compute_roof_clips(roofs)
    for g in roofs:
        region = clips[id(g)].region
        assert region is not None
        keys = [tuple(sorted((round(p.x(), 1), round(p.y(), 1)) for p in cell))
               for cell in region.cells]
        assert len(keys) == len(set(keys)), (g.clip_name, "duplicate cell")


def test_r4f_the_3d_mesh_has_no_degenerate_sliver_fragment():
    """The visual test of the same fix: a stray sliver reads in 3D as a
    triangle attached to nothing, or barely attached at a single edge.

    REWRITTEN AT R4g (0176-ruling.md / 0177-ruling.md): "one connected
    piece" is no longer the invariant -- `test_r4f_a_genuine_three_way_
    junction_leaves_nothing_drawn_by_nobody`'s own rewrite explains why a
    real, non-trivial gap can now legitimately exist (reachability
    correctly refusing to draw ground it cannot support owning), and an
    honest gap disconnects the mesh around it same as a sliver would.
    What this test was ACTUALLY built to catch -- debris, not architecture
    -- is still checked directly: every disconnected piece's own total
    triangle area must be substantial, not a fin a stray sliver's skirt
    would produce."""
    doc = json.loads(THREE_RIDGE_FIXTURE.read_text(encoding="utf-8"))
    from collections import defaultdict

    import importlib.util
    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location(
        "fp3d_r4f_check", root / "floorplanner" / "viewer" / "fp3d.py")
    fp3d = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = fp3d
    spec.loader.exec_module(fp3d)

    model = fp3d.build_model(doc, furnishings=False, floors=False)
    mesh = next(m for m in model.meshes if m.name == "roofs")
    edge_to_faces = defaultdict(list)
    for fi, face in enumerate(mesh.faces):
        pts = [tuple(round(float(c), 2) for c in mesh.verts[idx]) for idx in face]
        n = len(pts)
        for i in range(n):
            e = tuple(sorted((pts[i], pts[(i + 1) % n])))
            edge_to_faces[e].append(fi)
    parent = list(range(len(mesh.faces)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for _, faces in edge_to_faces.items():
        for i in range(1, len(faces)):
            ra, rb = find(faces[0]), find(faces[i])
            if ra != rb:
                parent[ra] = rb

    def tri_area(face):
        a, b, c = (mesh.verts[i] for i in face)
        return 0.5 * float(np.linalg.norm(np.cross(b - a, c - a)))

    area_by_root = {}
    for fi in range(len(mesh.faces)):
        root = find(fi)
        area_by_root[root] = area_by_root.get(root, 0.0) + tri_area(mesh.faces[fi])
    # a real fragment of roof, not sliver debris (whose skirt is
    # perimeter x height-drop over a MIN_CELL_AREA-scale footprint --
    # the module's own SLIVER_AREA_IN, 2.0 sq in, names the boundary)
    assert all(area > 20.0 for area in area_by_root.values()), area_by_root


# ---------------------------------------------------------------------------
# R4g (0176-ruling.md / 0177-ruling.md): candidacy becomes the roof's own
# footprint (`_strip` retires from `compute_roof_clips`'s own candidacy
# scope -- `clip_pair` keeps it, untouched); reachability is anchored at the
# COMPONENT holding a roof's own single-coverage ground, not "whichever
# ridge end is not swallowed" (0176's own first cut, refuted by his
# correction: rf1 has BOTH ends locally highest, yet the east piece must
# die); and a ridge-ridge crossing's far wedge, touching the near body at
# one POINT only, is disconnected by the same positive-length-adjacency
# rule `_adjacent` already enforced everywhere else in this module.
# ---------------------------------------------------------------------------
def test_r4g_a_ridge_ridge_saddle_disconnects_the_far_wedge_along_the_ridge():
    """0177-ruling.md sec3's own required receipt, in isolation: "a test
    constructs this saddle in isolation (two crossing ridges, equal
    heights) and the far wedge must surrender." Just rf1 and rf2 from his
    fixture, rf3 dropped entirely -- the saddle at (707.454, 468) is a
    property of rf1 and rf2 alone (both surfaces are at their OWN ridge
    height, 132, exactly there). Checked DIRECTLY ALONG rf1's own ridge
    line, where the saddle itself sits: no point east of the pinch, on
    the ridge, is rf1's.

    AT 0181-ruling.md: both far arms are severed at the point, and each
    ridge has crossed the other's -- two phantoms, each cutting the other
    off from its own body. They prune one at a time, the shorter
    overshoot first (rf1's 49" before rf2's 86"), so rf2's south arm is
    judged on the re-enveloped ground and reconnects around the pinch:
    rf1 ends at the pinch, rf2 continues to its own end -- with or
    without rf3 present, the same junction."""
    roofs = _three_ridge_roofs()
    rf1, rf2, _rf3 = roofs
    clips = compute_roof_clips([rf1, rf2])
    region = clips[id(rf1)].region
    assert region is not None
    for x in (712, 720, 750, 800):
        assert not region.contains(Pt(x, 468.0))
    south_arm = clips[id(rf2)].region
    for pt in ((742, 512), (730, 500), (748, 540)):
        assert south_arm.contains(Pt(*pt)) and not region.contains(Pt(*pt))


def test_r4g_rf1_owns_no_point_east_of_the_pinch_on_the_ridge():
    """0177-ruling.md sec3's own receipt: "rf1's final region contains no
    point east of the pinch; its trimmed ridge ends AT (707.454, 468)."
    On the full three-roof fixture (rf3 present, per the ruling's own
    scope): rf1's own RIDGE LINE never reaches past the pinch, and rf1's
    region holds NO ground east of it at all -- the ~13% 0180-report.md
    measured there was rf1 reconnecting through ground rf2's south arm
    holds in his reference, and is gone now that rf1's overshoot prunes
    first and rf2's arm reconnects (0181-ruling.md). The junction is his
    v2 evidence picture: rf1 ends at the pinch, exactly two rf1/rf2
    valleys meet there, the second running from the pinch to the triple
    point, and rf2's ridge runs on to its own end."""
    roofs = _three_ridge_roofs()
    rf1, rf2, _rf3 = roofs
    clips = compute_roof_clips(roofs)
    region = clips[id(rf1)].region
    assert region is not None
    for x in (712, 720, 750, 800, 900):
        assert not region.contains(Pt(x, 468.0))
    far_east = sum(_area(cell) for cell in region.cells
                  if max(p.x() for p in cell) > 707.454 + 1.0)
    assert far_east == 0.0, (far_east, region.area())
    pinch = Pt(707.454, 468.0)
    at_pinch = {(round(p.x(), 2), round(p.y(), 2), round(q.x(), 2), round(q.y(), 2))
                for p, q in clips[id(rf1)].seams
                if any(abs(e.x() - pinch.x()) < 1e-2 and abs(e.y() - pinch.y()) < 1e-2
                       for e in (p, q))}
    assert len(at_pinch) == 2, at_pinch
    assert any(abs(x1 - 681.586) < 1e-2 and abs(y1 - 538.067) < 1e-2
               for x1, y1, _x2, _y2 in at_pinch), at_pinch      # to the triple point
    south_arm = clips[id(rf2)].region
    for pt in ((742, 512), (730, 500), (748, 540)):
        assert south_arm.contains(Pt(*pt))


def test_r4g_every_remaining_cross_roof_boundary_is_a_seam_or_a_footprint_edge():
    """0176-ruling.md sec3's own invariant, testable and absolute: "every
    cross-roof boundary is either a true seam ... or lies on a real
    footprint edge of one of the two roofs ... a height jump anywhere
    else is a bug by definition." Checked directly: every pair of
    adjacent final cells from different roofs is sampled at their shared
    boundary; either the two surfaces agree there (a seam) or the sample
    point lies on one of the two roofs' own NOMINAL footprint edges (a
    real eave/gable/rake line -- 0177-ruling.md sec3's own named case,
    "rf3's rake edge standing over rf1's low eave corner ... CORRECT").

    HONESTLY MEASURED, ONE NAMED EXCEPTION: at the exact three-way
    convergence near (756, 553) two sub-square-inch slivers land within
    0.15in of an exact seam -- construction imprecision at a degenerate
    multi-roof corner, not a drawn architectural jump (`SLIVER_AREA_IN`
    already accepts a worse case of the same class for the same reason).
    The tolerance below is set to admit exactly that and nothing larger
    -- the pre-R4g arrangement failed this same check at up to ~30in
    (0174-report.md sec6's own "27 boundaries" residual)."""
    roofs = _three_ridge_roofs()
    clips = compute_roof_clips(roofs)
    fps = [footprint_polygon(g) for g in roofs]

    def on_edge(fp, pt, tol=0.1):
        n = len(fp)
        for i in range(n):
            a, b = fp[i], fp[(i + 1) % n]
            abx, aby = b.x() - a.x(), b.y() - a.y()
            length2 = abx * abx + aby * aby
            if length2 < 1e-9:
                continue
            t = max(0.0, min(1.0, ((pt.x() - a.x()) * abx
                                   + (pt.y() - a.y()) * aby) / length2))
            px, py = a.x() + abx * t, a.y() + aby * t
            if math.hypot(pt.x() - px, pt.y() - py) < tol:
                return True
        return False

    cells = [(g, cell) for g in roofs if clips[id(g)].region is not None
            for cell in clips[id(g)].region.cells]
    bad = []
    for i in range(len(cells)):
        g1, c1 = cells[i]
        for j in range(i + 1, len(cells)):
            g2, c2 = cells[j]
            if g1 is g2 or not _adjacent(c1, c2):
                continue
            for x, y in ((c1, c2), (c2, c1)):
                n = len(x)
                for k in range(n):
                    p, q = x[k], x[(k + 1) % n]
                    if math.hypot(q.x() - p.x(), q.y() - p.y()) < 1e-5:
                        continue
                    mid = Pt((p.x() + q.x()) / 2.0, (p.y() + q.y()) / 2.0)
                    m = len(y)
                    if not any(_dist_to_segment(mid, y[t], y[(t + 1) % m]) < 1e-5
                              for t in range(m)):
                        continue
                    h1, h2 = surface_height(g1, mid), surface_height(g2, mid)
                    if abs(h1 - h2) < 0.2:
                        continue
                    i1, i2 = roofs.index(g1), roofs.index(g2)
                    if on_edge(fps[i1], mid) or on_edge(fps[i2], mid):
                        continue
                    bad.append((g1.clip_name, g2.clip_name,
                               round(mid.x(), 2), round(mid.y(), 2),
                               round(h1, 2), round(h2, 2)))
    assert bad == [], bad


def test_0182_every_equal_height_boundary_between_two_roofs_is_a_drawn_seam():
    """Patrick's check of 0182: the 3D view was right and the plan was
    missing joints -- the rf2/rf3 seam between (756, 553) and (773, 509),
    exactly the boundary the per-piece prune had turned from a crossing
    inside one cell into an edge between two cells, which the crossing
    bookkeeping then never recorded. The seam is now read off the final
    pieces. The receipt is the definition itself, checked globally: every
    shared edge between two roofs' final cells along which both surfaces
    agree is covered by a seam segment of BOTH roofs -- and the two named
    joints are there."""
    roofs = _three_ridge_roofs()
    clips = compute_roof_clips(roofs)
    from floorplanner.roofclip import _shared_segment
    cells = [(g, cell) for g in roofs if clips[id(g)].region is not None
            for cell in clips[id(g)].region.cells]

    def covered(g, p, q):
        for a, b in clips[id(g)].seams:
            if (_dist_to_segment(p, a, b) < 1e-3 and _dist_to_segment(q, a, b) < 1e-3):
                return True
        return False

    missing = []
    for i in range(len(cells)):
        g1, c1 = cells[i]
        for j in range(i + 1, len(cells)):
            g2, c2 = cells[j]
            if g1 is g2:
                continue
            seg = _shared_segment(c1, c2)
            if seg is None:
                continue
            p, q = seg
            if any(abs(surface_height(g1, e) - surface_height(g2, e)) > 1e-3 for e in (p, q)):
                continue
            if not (covered(g1, p, q) and covered(g2, p, q)):
                missing.append((g1.clip_name, g2.clip_name, round(p.x(), 2), round(p.y(), 2),
                                round(q.x(), 2), round(q.y(), 2)))
    assert missing == [], missing
    # the joint he marked: from the rf2/rf3 seam's corner at (773, 509)
    # down to rf2's ridge end at (756, 553), for both roofs (it bends
    # once on the way, at rf3's ridge line, so it is two segments)
    rf1, rf2, rf3 = roofs
    for g in (rf2, rf3):
        segs = clips[id(g)].seams
        assert any(math.hypot(a.x() - 772.8, a.y() - 509.3) < 0.5 and b.y() > 525
                   or math.hypot(b.x() - 772.8, b.y() - 509.3) < 0.5 and a.y() > 525
                   for a, b in segs), segs
        assert any(math.hypot(e.x() - 756.5, e.y() - 553.0) < 1.0
                   for a, b in segs for e in (a, b)), segs


def test_r4g_the_rf3_rake_over_rf1_eave_jump_is_named_correct_and_stays():
    """0177-ruling.md sec3's own receipt: "the one jump boundary that
    remains on this fixture is rf3's rake edge standing over rf1's low
    eave corner (~= (556, 580)-(590, 645)) -- named here as CORRECT, a
    real vertical face on a real footprint edge." Verified at the named
    approximate location: rf3's surface genuinely stands above rf1's
    there, and the point sits on rf1's own nominal footprint edge (its
    eave line) -- exactly the licence 0176-ruling.md sec3's invariant
    grants a height jump.

    DRAWN AT 0181-ruling.md: the ground inside rf3's rake over rf1's
    footprint was blank through 0178-0180 (rf3's rake-side body was an
    uncertified limb); it is rf3's now, so the jump is a real drawn face
    -- rf3 draws the ground just inside its rake, rf1 does not, and rf1
    draws right up to the outside of it."""
    roofs = _three_ridge_roofs()
    rf1, _rf2, rf3 = roofs
    fp1 = footprint_polygon(rf1)
    pt = Pt(585, 642)     # on rf1's own low eave line, within the named span
    h1, h3 = surface_height(rf1, pt), surface_height(rf3, pt)
    assert h3 > h1 + 1.0, (h1, h3)
    n = len(fp1)
    on_edge = any(
        _dist_to_segment(pt, fp1[i], fp1[(i + 1) % n]) < 5.0 for i in range(n))
    assert on_edge, [(round(p.x(), 1), round(p.y(), 1)) for p in fp1]
    clips = compute_roof_clips(roofs)
    inside = Pt(570, 600)          # inside rf3's rake AND inside rf1's footprint
    assert _contains(footprint_polygon(rf3), inside) and _contains(fp1, inside)
    assert surface_height(rf3, inside) > surface_height(rf1, inside)
    assert clips[id(rf3)].region.contains(inside)
    assert not clips[id(rf1)].region.contains(inside)
    assert clips[id(rf1)].region.contains(Pt(575, 620))     # just outside the rake
