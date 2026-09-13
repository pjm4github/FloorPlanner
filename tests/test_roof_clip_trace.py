"""R5a -- the clip trace ON THE ROOF (0186-ruling.md sec2): "dashed lines on
the roof where the full height of the walls are clipped by the roof". Each
roof draws a dashed trace along the locus where its surface crosses the
covered rooms' wall-top plane -- the same `roof_clip_spans` geometry R3b
dashes along a wall, read from the roof's side. `roofs.roof_clip_trace`
computes it, `RoofItem._drawn_trace` cuts it to R4d's visible region, and
`RoofItem.paint` draws it in the wall dash's own ink.

The receipt the ruling names is the hug: the trace must meet every R3b wall
dash where that wall crosses it. So the tests here call the PRODUCTION
`roof_clip_spans` on the walls of the same scene and compare -- not a
restatement of the closed form (WORKING_AGREEMENT.md: call the predicate,
do not restate it). The closed form itself is checked once, on the same
300x200 fixture `tests/test_roof_clip.py` uses, so the two files' numbers
can be read against each other.
"""
import math

import pytest
from PyQt6 import sip
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QImage, QPainter, QPainterPath

from floorplanner.config import DEFAULT_FLOOR, DEFAULT_ROOM_PROPS
from floorplanner.roofs import RoofItem, roof_clip_spans, roof_clip_trace
from floorplanner.rooms import RoomItem
from floorplanner.walls import WallItem

pytestmark = pytest.mark.walls

# tests/test_roof_clip.py's own fixture: a 300x200 shell, ridge along x at
# y=100, 100in of span either side, eaves 80 / ridge 132 over a 96in ceiling
EAVES_H, RIDGE_H, SPAN = 80.0, 132.0, 100.0
CEILING_IN = 96.0
SLOPE = (RIDGE_H - EAVES_H) / SPAN
PERP_THRESH = (RIDGE_H - CEILING_IN) / SLOPE     # 69.230769...
DEFAULT_CEILING = float(DEFAULT_ROOM_PROPS["ceiling_height_in"])


def _room(scene, x0=0.0, x1=300.0, ceiling_in=CEILING_IN, floor=None,
          name="Room"):
    path = QPainterPath()
    path.addRect(x0, 0, x1 - x0, 200)
    room = RoomItem(name, QPointF((x0 + x1) / 2.0, 100), path, 100.0)
    room.floor = floor if floor is not None else DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = ceiling_in
    scene.addItem(room)
    return room


def _roof(scene, eaves_h=EAVES_H, ridge_h=RIDGE_H, overhang=0.0, gable=None):
    rf = RoofItem(QPointF(50, 100), QPointF(250, 100), eaves_h_in=eaves_h,
                  ridge_h_in=ridge_h, overhang_in=overhang, span_in=SPAN,
                  gable=gable)
    rf.floor = DEFAULT_FLOOR
    scene.addItem(rf)
    return rf


def _wall(scene, p1, p2, kind="exterior"):
    w = WallItem(p1, p2, kind)
    w.floor = DEFAULT_FLOOR
    scene.addItem(w)
    return w


def _rounded(segs, nd=3):
    return sorted(((round(p.x(), nd), round(p.y(), nd)),
                   (round(q.x(), nd), round(q.y(), nd))) for p, q in segs)


def _length(segs) -> float:
    return sum(math.hypot(q.x() - p.x(), q.y() - p.y()) for p, q in segs)


def _ys_crossed_at(segs, x, tol=1e-6):
    """The y of every trace segment that crosses the vertical line `x`."""
    out = set()
    for p, q in segs:
        lo, hi = min(p.x(), q.x()), max(p.x(), q.x())
        if lo - tol <= x <= hi + tol and abs(p.y() - q.y()) < tol:
            out.add(round(p.y(), 6))
    return out


# --------------------------------------------------------------------------
# the analytic core, once
# --------------------------------------------------------------------------
def test_gable_roof_trace_is_two_lines_at_the_closed_form_threshold(scene):
    _room(scene)
    rf = _roof(scene)
    trace = roof_clip_trace(scene, rf)
    assert _rounded(trace) == _rounded([
        (QPointF(50, 100 - PERP_THRESH), QPointF(250, 100 - PERP_THRESH)),
        (QPointF(50, 100 + PERP_THRESH), QPointF(250, 100 + PERP_THRESH))])


# --------------------------------------------------------------------------
# THE RECEIPT: the trace meets the R3b wall dashes -- production predicate
# --------------------------------------------------------------------------
def test_the_trace_meets_the_wall_dashes_where_each_wall_crosses_it(scene):
    """Every wall crossing the roof: its own `roof_clip_spans` boundaries
    (the ends of its dashes, in inches from p1 == its y here) are exactly
    the y's at which the trace crosses that wall. Two gable-parallel
    walls, one at the ridge end and one mid-roof."""
    _room(scene)
    rf = _roof(scene)
    trace = roof_clip_trace(scene, rf)
    for x in (50.0, 150.0):
        wall = _wall(scene, QPointF(x, 0), QPointF(x, 200))
        spans = roof_clip_spans(scene, wall)
        assert spans, "precondition: this wall must actually clip"
        dash_ends = {round(s, 6) for s0, s1 in spans for s in (s0, s1)
                     if 0.0 < s < wall.length()}       # interior boundaries only
        assert dash_ends == _ys_crossed_at(trace, x)


def test_an_eaves_wall_dashed_end_to_end_lies_outside_the_trace(scene):
    """The other half of the hug: a wall whose dash runs its whole length
    (the eaves wall, uniformly under the clip) never meets the trace --
    the trace crosses no such wall, by the same closed form."""
    _room(scene)
    rf = _roof(scene)
    eaves_wall = _wall(scene, QPointF(50, 0), QPointF(250, 0))
    spans = roof_clip_spans(scene, eaves_wall)
    assert spans == [(0.0, pytest.approx(200.0))], "precondition: fully dashed"
    trace = roof_clip_trace(scene, rf)
    assert trace, "positive control: the roof does have a trace"
    for p, q in trace:
        assert min(p.y(), q.y()) > 0.0 + 1.0


# --------------------------------------------------------------------------
# nothing clips / everything clips
# --------------------------------------------------------------------------
def test_no_trace_when_the_eaves_clear_the_ceiling(scene):
    """Positive control first: the same scene with lower eaves has one."""
    _room(scene)
    rf = _roof(scene)
    assert roof_clip_trace(scene, rf), "control: the low roof traces"
    rf.eaves_h_in = 100.0
    rf.rebuild()
    wall = _wall(scene, QPointF(50, 0), QPointF(50, 200))
    assert roof_clip_spans(scene, wall) == [], "precondition: no wall dash"
    assert roof_clip_trace(scene, rf) == []


def test_a_ridge_below_the_ceiling_clips_everywhere_and_has_no_locus(scene):
    """A named limit, not a bug: with the ridge itself under the ceiling
    the surface never reaches ceiling height, so there is no line to
    draw -- while R3b dashes every wall end to end (asserted, so the two
    readings are on record together)."""
    _room(scene)
    rf = _roof(scene, eaves_h=60.0, ridge_h=90.0)
    wall = _wall(scene, QPointF(50, 0), QPointF(50, 200))
    assert roof_clip_spans(scene, wall) == [(0.0, pytest.approx(200.0))]
    assert roof_clip_trace(scene, rf) == []


# --------------------------------------------------------------------------
# a hip end
# --------------------------------------------------------------------------
def test_a_hip_end_closes_the_loop_with_a_cross_segment(scene):
    """Past a hip end the hip plane governs, dropping along the axis at the
    same pitch (equal spans -> hip run == span), so the level set turns
    the corner: a cross segment PERP_THRESH beyond the ridge end, between
    the two side lines, which themselves start there."""
    _room(scene)
    rf = _roof(scene, gable=[False, True])
    hip_x = 50.0 - PERP_THRESH
    assert _rounded(roof_clip_trace(scene, rf)) == _rounded([
        (QPointF(hip_x, 100 - PERP_THRESH), QPointF(250, 100 - PERP_THRESH)),
        (QPointF(hip_x, 100 + PERP_THRESH), QPointF(250, 100 + PERP_THRESH)),
        (QPointF(hip_x, 100 - PERP_THRESH), QPointF(hip_x, 100 + PERP_THRESH))])


def test_the_hip_cross_segment_meets_the_end_wall_dash(scene):
    """The hug at a hip end: a wall running along the ridge axis under
    the hip has its dash end where the hip cross segment crosses it."""
    _room(scene)
    rf = _roof(scene, gable=[False, True])
    wall = _wall(scene, QPointF(-40, 100), QPointF(150, 100))   # on the ridge line
    spans = roof_clip_spans(scene, wall)
    assert spans, "precondition: the hip clips this wall near its start"
    dash_end_x = -40.0 + spans[0][1]
    cross = [(p, q) for p, q in roof_clip_trace(scene, rf)
             if abs(p.x() - q.x()) < 1e-6]
    assert len(cross) == 1
    assert cross[0][0].x() == pytest.approx(dash_end_x)


# --------------------------------------------------------------------------
# which ceiling governs where
# --------------------------------------------------------------------------
def test_rooms_of_different_heights_each_get_their_own_line(scene):
    """Two rooms under one roof, 96in and 108in: each room's half of the
    roof carries the trace at ITS ceiling's own threshold, split at the
    shared boundary. With no walls on the floor the margin is the bare
    pad, so the lower room's line runs that far past x=150 and the
    higher room's starts there (the lower governs where both hold)."""
    _room(scene, 0, 150, 96.0, name="A")
    _room(scene, 150, 300, 108.0, name="B")
    rf = _roof(scene)
    thresh_108 = (RIDGE_H - 108.0) / SLOPE               # 46.153846...
    pad = 0.5
    assert _rounded(roof_clip_trace(scene, rf)) == _rounded([
        (QPointF(50, 100 - PERP_THRESH), QPointF(150 + pad, 100 - PERP_THRESH)),
        (QPointF(50, 100 + PERP_THRESH), QPointF(150 + pad, 100 + PERP_THRESH)),
        (QPointF(150 + pad, 100 - thresh_108), QPointF(250, 100 - thresh_108)),
        (QPointF(150 + pad, 100 + thresh_108), QPointF(250, 100 + thresh_108))])


def test_the_lower_room_governs_over_the_shared_wall_as_the_wall_dash_does(scene):
    """R3b reads a wall against the LOWER of the rooms it borders. The
    trace must agree ON that wall: an interior wall between a 96in and a
    108in room dashes at the 96in threshold, and the 96in trace lines are
    the ones that reach its centreline (the margin is half the floor's
    thickest wall, so the lower room's line runs across the wall)."""
    _room(scene, 0, 150, 96.0, name="A")
    _room(scene, 150, 300, 108.0, name="B")
    rf = _roof(scene)
    wall = _wall(scene, QPointF(150, 0), QPointF(150, 200), "interior")
    spans = roof_clip_spans(scene, wall)
    dash_ends = {round(s, 6) for s0, s1 in spans for s in (s0, s1)
                 if 0.0 < s < wall.length()}
    assert dash_ends == {round(100 - PERP_THRESH, 6), round(100 + PERP_THRESH, 6)}
    assert _ys_crossed_at(roof_clip_trace(scene, rf), 150.0) == dash_ends


def test_no_room_at_all_uses_the_default_ceiling_like_the_wall_dash(scene):
    rf = _roof(scene)
    wall = _wall(scene, QPointF(50, 0), QPointF(50, 200))
    spans = roof_clip_spans(scene, wall)
    assert spans, "precondition: R3b's own no-room fallback dashes this wall"
    dash_ends = {round(s, 6) for s0, s1 in spans for s in (s0, s1)
                 if 0.0 < s < wall.length()}
    assert _ys_crossed_at(roof_clip_trace(scene, rf), 50.0) == dash_ends
    thresh_default = (RIDGE_H - DEFAULT_CEILING) / SLOPE
    assert dash_ends == {round(100 - thresh_default, 6), round(100 + thresh_default, 6)}


def test_a_room_on_another_floor_does_not_govern(scene):
    _room(scene, ceiling_in=120.0, floor="L2")
    rf = _roof(scene)
    with_other = _rounded(roof_clip_trace(scene, rf))
    for it in list(scene.items()):
        if isinstance(it, RoomItem):
            scene.removeItem(it)
    assert with_other == _rounded(roof_clip_trace(scene, rf))
    assert with_other, "control: the default-ceiling trace exists"


# --------------------------------------------------------------------------
# under R4d's clip
# --------------------------------------------------------------------------
def _l_scene(scene, wing_ridge_h=130.0):
    """tests/test_roof_intersection.py's L, eaves lowered to 80 so the
    trace sits inside the footprints rather than on the eave lines."""
    main = RoofItem(QPointF(0, 200), QPointF(400, 200), span_in=100.0,
                    overhang_in=0.0, ridge_h_in=150.0, eaves_h_in=80.0)
    main.floor = DEFAULT_FLOOR
    scene.addItem(main)
    wing = RoofItem(QPointF(200, 250), QPointF(200, 500), span_in=60.0,
                    overhang_in=0.0, ridge_h_in=wing_ridge_h, eaves_h_in=80.0)
    wing.floor = DEFAULT_FLOOR
    scene.addItem(wing)
    return main, wing


def test_the_drawn_trace_is_cut_to_the_visible_region_while_clipped(scene):
    main, wing = _l_scene(scene)
    for rf in (main, wing):
        assert rf.is_clipped(), "precondition: the L clips both roofs"
        full, drawn = roof_clip_trace(scene, rf), rf._drawn_trace()
        assert 0.0 < _length(drawn) < _length(full)
        for p, q in drawn:
            mid = QPointF((p.x() + q.x()) / 2.0, (p.y() + q.y()) / 2.0)
            assert rf._clip_region.contains(mid)


def test_the_two_traces_meet_on_the_seam(scene):
    """Where both surfaces are at ceiling height the seam (their equal-
    height locus) passes through the crossing of the two traces -- so
    the main's drawn trace ends exactly at the wing's trace lines,
    x = 200 +- (130 - 96) / (50 / 60)."""
    main, wing = _l_scene(scene)
    wing_thresh = (130.0 - DEFAULT_CEILING) / (50.0 / 60.0)      # 40.8
    ends = {round(p.x(), 3) for p, q in main._drawn_trace() for p in (p, q)}
    assert round(200 - wing_thresh, 3) in ends
    assert round(200 + wing_thresh, 3) in ends


def test_selected_is_unclipped_for_the_trace_too(scene):
    _, wing = _l_scene(scene)
    full = _rounded(roof_clip_trace(scene, wing))
    assert _rounded(wing._drawn_trace()) != full
    wing.setSelected(True)
    assert _rounded(wing._drawn_trace()) == full
    wing.setSelected(False)
    assert _rounded(wing._drawn_trace()) != full


def test_a_joined_end_carries_the_trace_into_its_extension(scene):
    """A wing whose ridge end sits UNDER the main is joined (R4d): its
    planes continue past its own end edge, so the locus runs on past
    y=250 into the extension -- and what is DRAWN of it stops on the
    seam, which crosses the wing's trace exactly where the main's own
    trace does (both surfaces at ceiling height there): y = 200 +
    (150 - 96) / 0.7. Selected (unclipped) the extension is gone and
    the locus ends at the wing's own end edge."""
    _, wing = _l_scene(scene, wing_ridge_h=110.0)
    assert wing._clip_ext[0] > 0.0, "precondition: the end is joined"
    full = roof_clip_trace(scene, wing)
    assert min(min(p.y(), q.y()) for p, q in full) < 250.0 - 1.0
    drawn = wing._drawn_trace()
    main_trace_y = 200.0 + (150.0 - DEFAULT_CEILING) / 0.7
    assert min(min(p.y(), q.y()) for p, q in drawn) == pytest.approx(main_trace_y)
    wing.setSelected(True)
    assert min(min(p.y(), q.y()) for p, q in roof_clip_trace(scene, wing))         == pytest.approx(250.0)


# --------------------------------------------------------------------------
# the paint
# --------------------------------------------------------------------------
def _render(scene, size=300):
    img = QImage(size, size, QImage.Format.Format_RGB32)
    img.fill(0xFFFFFFFF)
    pr = QPainter(img)
    pr.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    scene.render(pr, QRectF(0, 0, size, size), QRectF(-20, -30, 340, 260),
                 Qt.AspectRatioMode.IgnoreAspectRatio)
    pr.end()
    return img


def _is_clip_ink(color) -> bool:
    """tests/test_roof_clip.py's own predicate for the wall dash ink --
    the trace uses the same colour (ROOF_CLIP_INK), which is the point."""
    return color.red() > 180 and 60 < color.green() < 140 and color.blue() < 60


def _px(scene_x):
    return round((scene_x - (-20.0)) / 340.0 * 300.0)


def _py(scene_y):
    return round((scene_y - (-30.0)) / 260.0 * 300.0)


def test_the_trace_paints_where_computed_and_nowhere_else(scene):
    """No walls in this scene, so any clip ink is the roof's own trace.
    Scan a band of rows around each trace line across the roof's middle
    (a dash pattern has gaps, so "any ink somewhere along it"), and the
    clear band between them, away from the brown ridge."""
    _room(scene)
    _roof(scene)
    img = _render(scene)
    xs = range(_px(80.0), _px(220.0))
    for y in (100 - PERP_THRESH, 100 + PERP_THRESH):
        rows = range(_py(y) - 2, _py(y) + 3)
        assert any(_is_clip_ink(img.pixelColor(x, r))
                   for x in xs for r in rows), f"no trace ink at y={y:.2f}"
    clear_rows = list(range(_py(45.0), _py(90.0))) + list(range(_py(110.0), _py(155.0)))
    assert not any(_is_clip_ink(img.pixelColor(x, r)) for x in xs for r in clear_rows)


def test_no_trace_ink_when_nothing_clips(scene):
    _room(scene)
    _roof(scene, eaves_h=100.0, ridge_h=140.0)
    img = _render(scene)
    assert not any(_is_clip_ink(img.pixelColor(x, r))
                   for x in range(_px(80.0), _px(220.0))
                   for r in range(0, 300, 2))


# --------------------------------------------------------------------------
# teardown safety, as roof_clip_spans has
# --------------------------------------------------------------------------
def test_a_stale_roof_reference_gets_an_empty_answer_not_wrong_data(scene):
    _room(scene)
    rf = _roof(scene)
    assert roof_clip_trace(scene, rf), "precondition: traces while live"
    scene.removeItem(rf)
    sip.delete(rf)
    assert sip.isdeleted(rf)
    assert roof_clip_trace(scene, rf) == []
