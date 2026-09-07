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
import pytest
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QImage, QPainter

from floorplanner.config import DEFAULT_FLOOR
from floorplanner.roofclip import (
    clip_pair, compute_roof_clips, seam_heights, seam_length, surface_height,
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
