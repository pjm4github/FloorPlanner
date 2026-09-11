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
from pathlib import Path

import pytest
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QImage, QPainter

from floorplanner.config import DEFAULT_FLOOR
from floorplanner.roofclip import (
    Pt, RoofGeom, _area, _contains, clip_pair, compute_roof_clips,
    footprint_polygon, seam_heights, seam_length, surface_height,
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
    eyeballed: among every seam vertex the three roofs carry, EXACTLY ONE
    lands inside all three footprints with all three surfaces tied."""
    roofs = _three_ridge_roofs()
    clips = compute_roof_clips(roofs)
    verts = set()
    for g in roofs:
        for p, q in clips[id(g)].seams:
            verts.add((round(p.x(), 3), round(p.y(), 3)))
            verts.add((round(q.x(), 3), round(q.y(), 3)))
    triples = []
    for vx, vy in verts:
        pt = QPointF(vx, vy)
        if not all(_contains(footprint_polygon(g), pt) for g in roofs):
            continue
        heights = [surface_height(g, pt) for g in roofs]
        if max(heights) - min(heights) < 1e-2:
            triples.append((pt, heights))
    assert len(triples) == 1, triples
    pt, heights = triples[0]
    assert pt.x() == pytest.approx(682, abs=2)
    assert pt.y() == pytest.approx(538, abs=2)
    for h in heights:
        assert h == pytest.approx(117.5, abs=0.1)


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


def test_r4f_a_genuine_three_way_junction_leaves_nothing_drawn_by_nobody():
    """His own check found the FIRST cut's residual patch visually --
    a real hole in the 3D roof at the junction, not a benign sliver.
    `_fill_unclaimed_ground` closes it: any ground three or more roofs
    fought over that the pairwise fold could not assign to either
    partner goes to whichever covering roof is highest there, once every
    already-decided region and seam is subtracted out first. Scoped to
    3+ roofs on purpose -- the TWO-roof "corner past the seam ... drawn
    by nobody" behaviour (D85, tested below) is untouched, matching
    0170-ruling.md's own regression clause."""
    roofs = _three_ridge_roofs()
    clips = compute_roof_clips(roofs)
    fps = [footprint_polygon(g) for g in roofs]
    xs = [p.x() for fp in fps for p in fp]
    ys = [p.y() for fp in fps for p in fp]
    n = 70
    in_any = gap = 0
    for i in range(n):
        for j in range(n):
            x = min(xs) + (max(xs) - min(xs)) * i / (n - 1)
            y = min(ys) + (max(ys) - min(ys)) * j / (n - 1)
            pt = Pt(x, y)
            if not any(_contains(fp, pt) for fp in fps):
                continue
            in_any += 1
            if not any(clips[id(g)].region is not None
                      and clips[id(g)].region.contains(pt) for g in roofs):
                gap += 1
    assert gap == 0, f"drawn-by-nobody: {gap}/{in_any}"


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


def test_r4f_no_stray_slivers_or_duplicate_cells_near_the_junction():
    """His own second report ('a minor ridge that doesn't clean nicely'):
    the pairwise fold's two independently-built decompositions can
    intersect into a razor-thin sliver cell near a complex junction --
    exact, not a math bug, but `_prism_slab` still extrudes it as its own
    tiny prism, reading as a stray fin. And a fill candidate reduced by
    `_subtract_claimed` from two different starting cells can converge on
    the SAME leftover geometry, added twice. Both are now filtered:
    slivers below `MIN_FILL_AREA` are dropped from a live (3+-touched)
    roof's region before the fill pass runs, and the fill pass itself
    dedups what it manufactures before merging it in."""
    roofs = _three_ridge_roofs()
    clips = compute_roof_clips(roofs)
    for g in roofs:
        region = clips[id(g)].region
        assert region is not None
        areas = [_area(cell) for cell in region.cells]
        assert min(areas) > 1.0, (g.clip_name, min(areas))
        keys = [tuple(sorted((round(p.x(), 1), round(p.y(), 1)) for p in cell))
               for cell in region.cells]
        assert len(keys) == len(set(keys)), (g.clip_name, "duplicate cell")


def test_r4f_the_3d_mesh_is_one_connected_surface():
    """The visual test of the same fix: a stray sliver reads in 3D as a
    triangle attached to nothing, or barely attached at a single edge --
    the whole roofs mesh should be ONE connected piece (every triangle
    reachable from any other by walking shared edges), not several."""
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
    n_components = len({find(fi) for fi in range(len(mesh.faces))})
    assert n_components == 1, f"roof mesh has {n_components} disconnected pieces"
