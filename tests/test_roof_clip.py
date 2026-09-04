"""R3b -- the roof-clip dotted line (0145-ruling.md sec3): "affected walls
should show a dotted line where any part of the roof is clipping the full
height of the room underneath." `roofs.roof_clip_spans` computes the
sub-span(s), in inches from a wall's own `p1`, where a roof on the wall's
floor covers it below the room's own ceiling height; `WallItem.paint`
draws them.

Every governing quantity (how far along the ridge a point on the wall
projects, how far off it, the roof's own height there) is affine in the
wall's own arc-length parameter, so the whole computation is exact interval
arithmetic, not a fixed-resolution sample -- the tests check exact
boundaries against the closed form, the same discipline the R3 (3D) tests
already applied to the same slope formula.
"""
import pytest
from PyQt6 import sip
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QImage, QPainter, QPainterPath

from floorplanner.config import DEFAULT_FLOOR, DEFAULT_ROOM_PROPS
from floorplanner.roofs import RoofItem, roof_clip_spans
from floorplanner.rooms import RoomItem
from floorplanner.walls import WallItem

pytestmark = pytest.mark.walls

# A 300x200 shell, ridge along x at y=100 -- centred between the y=0/y=200
# long walls, so the eaves span is unambiguous (100in either side), matching
# tests/test_viewer_model.py's own R3 fixture.
EAVES_H, RIDGE_H, SPAN = 80.0, 132.0, 100.0
CEILING_IN = 96.0                       # DEFAULT_ROOM_PROPS's own default
SLOPE = (RIDGE_H - EAVES_H) / SPAN
PERP_THRESH = (RIDGE_H - CEILING_IN) / SLOPE    # 69.230769...


def _room(scene, ceiling_in=CEILING_IN):
    path = QPainterPath()
    path.addRect(0, 0, 300, 200)
    room = RoomItem("Room", QPointF(150, 100), path, 100.0)
    room.floor = DEFAULT_FLOOR
    room.properties["ceiling_height_in"] = ceiling_in
    scene.addItem(room)
    return room


def _roof(scene, eaves_h=EAVES_H, ridge_h=RIDGE_H, overhang=0.0, floor=None,
          gable=None):
    rf = RoofItem(QPointF(50, 100), QPointF(250, 100), eaves_h_in=eaves_h,
                 ridge_h_in=ridge_h, overhang_in=overhang, span_in=SPAN,
                 gable=gable)
    rf.floor = floor if floor is not None else DEFAULT_FLOOR
    scene.addItem(rf)
    return rf


def _gable_wall(scene):
    """The wall at the ridge's own left end (x=50), running its full width
    (y 0..200) -- crosses directly under the ridge endpoint, so the roof's
    covering height varies continuously from RIDGE_H (at the crossing) down
    to EAVES_H (at either end), exactly the "gable end" case named in the
    ruling."""
    w = WallItem(QPointF(50, 0), QPointF(50, 200), "exterior")
    w.floor = DEFAULT_FLOOR
    scene.addItem(w)
    return w


# --------------------------------------------------------------------------
# the analytic core
# --------------------------------------------------------------------------
def test_no_roof_at_all_means_no_clip(scene):
    wall = _gable_wall(scene)
    _room(scene)
    assert roof_clip_spans(scene, wall) == []


def test_gable_end_wall_clips_at_both_low_ends(scene):
    """The headline case: PERP_THRESH < SPAN, so the middle of the wall (near
    the ridge crossing, tall) reads clear and both ends (near the eaves,
    short) read clipped -- exact boundaries against the closed form."""
    wall = _gable_wall(scene)
    _roof(scene)
    _room(scene)
    spans = roof_clip_spans(scene, wall)
    assert len(spans) == 2, spans
    lo, hi = SPAN - PERP_THRESH, SPAN + PERP_THRESH
    assert spans[0] == pytest.approx((0.0, lo))
    assert spans[1] == pytest.approx((hi, 200.0))


def test_no_clip_when_the_eaves_already_clear_the_ceiling(scene):
    """PRECONDITION-shaped: eaves_h > ceiling means the roof is never lower
    than the ceiling anywhere it covers -- proves the function does not
    clip unconditionally just because a roof exists."""
    wall = _gable_wall(scene)
    _roof(scene, eaves_h=100.0, ridge_h=140.0)   # both above CEILING_IN
    _room(scene)
    assert roof_clip_spans(scene, wall) == []


def test_an_eaves_wall_clips_uniformly_along_its_whole_run(scene):
    """A wall running PARALLEL to the ridge, sitting exactly at the eaves
    line (perp constant = SPAN along its whole length): the roof's covering
    height is constant EAVES_H everywhere on it, so a low eaves clips the
    ENTIRE wall, not a sub-span -- the other shape R3b's own spec implies
    ("any part... clipping") but does not spell out."""
    wall = WallItem(QPointF(60, 200), QPointF(240, 200), "exterior")
    wall.floor = DEFAULT_FLOOR
    scene.addItem(wall)
    _roof(scene)                          # EAVES_H=80 < CEILING_IN=96
    _room(scene)
    spans = roof_clip_spans(scene, wall)
    assert spans == [pytest.approx((0.0, 180.0))]


def test_a_roof_on_a_different_floor_does_not_clip(scene):
    wall = _gable_wall(scene)
    _roof(scene, floor="upstairs")
    _room(scene)
    assert roof_clip_spans(scene, wall) == []


def test_the_lower_of_two_bordering_rooms_governs(scene):
    """A wall between two rooms of different ceiling heights: clipped by the
    MORE restrictive one, not whichever happens to be found first -- the
    threshold with a lower ceiling (84) must reach further than with the
    default (96), and the function must pick the lower automatically when
    both sides resolve to a room. The two rooms straddle the wall (x=50)
    exactly -- x in [50,300] on one side, [-250,50] on the other -- so each
    of `_wall_ceiling_in`'s two offset probes lands in a DIFFERENT room,
    which a room rect merely CONTAINING the wall (as `_room`'s own default
    does) would not test."""
    wall = _gable_wall(scene)
    _roof(scene)
    high = QPainterPath()
    high.addRect(50, 0, 250, 200)
    high_room = RoomItem("High", QPointF(150, 100), high, 100.0)
    high_room.floor = DEFAULT_FLOOR
    high_room.properties["ceiling_height_in"] = CEILING_IN
    scene.addItem(high_room)
    low = QPainterPath()
    low.addRect(-250, 0, 300, 200)
    low_room = RoomItem("Low", QPointF(-150, 100), low, 100.0)
    low_room.floor = DEFAULT_FLOOR
    low_room.properties["ceiling_height_in"] = 84.0
    scene.addItem(low_room)

    spans = roof_clip_spans(scene, wall)
    thresh = (RIDGE_H - 84.0) / SLOPE
    lo, hi = SPAN - thresh, SPAN + thresh
    assert spans[0] == pytest.approx((0.0, lo))
    assert spans[1] == pytest.approx((hi, 200.0))
    # precondition: the two ceilings really do produce different thresholds
    assert thresh != pytest.approx(PERP_THRESH)


def test_no_bordering_room_falls_back_to_the_default_ceiling(scene):
    """No room anywhere near the wall (an unenclosed sketch): the same
    fallback `DEFAULT_ROOM_PROPS["ceiling_height_in"]` items.py's own
    `StairsItem._ceiling_height` uses, not a silently different constant."""
    wall = _gable_wall(scene)
    _roof(scene)
    # no _room(scene) call at all
    spans = roof_clip_spans(scene, wall)
    default_ceiling = DEFAULT_ROOM_PROPS["ceiling_height_in"]
    thresh = (RIDGE_H - default_ceiling) / SLOPE
    lo, hi = SPAN - thresh, SPAN + thresh
    assert spans[0] == pytest.approx((0.0, lo))
    assert spans[1] == pytest.approx((hi, 200.0))


def test_overhang_extends_the_covered_zone_at_the_same_slope(scene):
    """A wall standing exactly at the OUTER overhang edge (perp = SPAN +
    overhang, beyond the wall the roof is nominally built over) is still
    COVERED (matches R3's own "overhang continues the same plane" model),
    and its height there continues the same downward slope past EAVES_H --
    so it clips whenever that continued height is below the ceiling, which
    a positive overhang only makes MORE likely, never less."""
    overhang = 24.0
    wall = WallItem(QPointF(60, 100 + SPAN + overhang),
                    QPointF(240, 100 + SPAN + overhang), "exterior")
    wall.floor = DEFAULT_FLOOR
    scene.addItem(wall)
    _roof(scene, overhang=overhang)
    _room(scene)
    spans = roof_clip_spans(scene, wall)
    edge_h = RIDGE_H - SLOPE * (SPAN + overhang)
    assert edge_h < EAVES_H < CEILING_IN, "precondition: the overhang droops lower still"
    assert spans == [pytest.approx((0.0, 180.0))]


def test_two_roofs_union_their_clip_spans(scene):
    """Two independent roofs on the same floor, each clipping a different
    part of one long wall -- the result is their UNION, not just the last
    roof considered."""
    wall = WallItem(QPointF(0, 0), QPointF(400, 0), "exterior")
    wall.floor = DEFAULT_FLOOR
    scene.addItem(wall)
    left = RoofItem(QPointF(0, -100), QPointF(0, 100), eaves_h_in=EAVES_H,
                    ridge_h_in=RIDGE_H, overhang_in=0.0, span_in=SPAN)
    left.floor = DEFAULT_FLOOR
    scene.addItem(left)
    right = RoofItem(QPointF(400, -100), QPointF(400, 100), eaves_h_in=EAVES_H,
                     ridge_h_in=RIDGE_H, overhang_in=0.0, span_in=SPAN)
    right.floor = DEFAULT_FLOOR
    scene.addItem(right)
    _room(scene)

    spans = roof_clip_spans(scene, wall)
    # each ridge crosses the wall at its own x -- covered only within
    # SPAN either side (x in [0,100] of the left roof, [300,400] of the
    # right), clipped past PERP_THRESH inside that, exactly the gable-end
    # math already validated above, applied at two independent locations
    assert spans == [pytest.approx((PERP_THRESH, SPAN)),
                     pytest.approx((300.0, 400.0 - PERP_THRESH))]
    # the two clipped zones must NOT touch -- otherwise this is only testing
    # one roof twice
    assert spans[0][1] < spans[1][0]


# --------------------------------------------------------------------------
# the paint()-level integration -- the pixels, not just the numbers
# --------------------------------------------------------------------------
def _render(scene, size=300):
    """`aspectRatioMode` defaults to `KeepAspectRatio`, which letterboxes a
    non-square source (340x260) into a square target and silently breaks
    any linear scene->pixel formula that assumes a plain stretch --
    `IgnoreAspectRatio` here makes the mapping the simple one the pixel
    math below actually relies on."""
    img = QImage(size, size, QImage.Format.Format_RGB32)
    img.fill(0xFFFFFFFF)
    pr = QPainter(img)
    pr.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    scene.render(pr, QRectF(0, 0, size, size), QRectF(-20, -30, 340, 260),
                Qt.AspectRatioMode.IgnoreAspectRatio)
    pr.end()
    return img


def _is_clip_ink(color) -> bool:
    return color.red() > 180 and 60 < color.green() < 140 and color.blue() < 60


def test_the_clip_line_actually_paints_where_computed(scene):
    """The output, not the internals: sample the wall's own on-screen line at
    a point analytically inside a clipped sub-span (must find the ink) and
    one squarely in the middle, clear zone (must not) -- the same polarity
    discipline `test_walls.py`'s own junction-seam pixel test uses.

    `gable=[False, False]`: this wall sits exactly where the ROOF's OWN
    gable line would also draw (same x, the wall's whole run) -- with it on,
    the roof's dashed gable outline and the wall's dashed clip line share a
    column, and their dash phases can coincide well enough to hide one under
    the other. Turning it off isolates what this test actually checks, the
    WALL's own paint(), from a real but separate rendering-order question
    (two dashed decorations sharing a column) this test is not about."""
    wall = _gable_wall(scene)
    _roof(scene, gable=[False, False])
    _room(scene)
    spans = roof_clip_spans(scene, wall)
    assert spans, "precondition: this scene must actually clip"

    img = _render(scene)
    # scene x=50 -> pixel x = (50 - (-20)) / 340 * 300 = ~61.8
    px = round((50.0 - (-20.0)) / 340.0 * 300.0)

    def py_of(scene_y):
        return round((scene_y - (-30.0)) / 260.0 * 300.0)

    # a RANGE of rows, not one: DashLine has on/off phases along the line, so
    # a single row can land in a gap even where the span itself is clipped --
    # scan the whole clipped sub-span (spans[0] == (0, ~30.77)) for "any ink
    # somewhere in it", and the whole clear zone around the ridge crossing
    # (spans[0][1] to spans[1][0] == ~30.77 to ~169.23) for "none anywhere"
    clipped_rows = range(py_of(0.0), py_of(spans[0][1]) + 1)
    clear_rows = range(py_of(spans[0][1]) + 5, py_of(spans[1][0]) - 5)

    found_clipped = any(_is_clip_ink(img.pixelColor(x, y))
                        for x in range(px - 2, px + 3) for y in clipped_rows)
    found_clear = any(_is_clip_ink(img.pixelColor(x, y))
                      for x in range(px - 2, px + 3) for y in clear_rows)
    assert found_clipped, "expected the clip ink somewhere inside a clipped sub-span"
    assert not found_clear, "the clip ink appeared where nothing should clip"


def test_no_clip_ink_when_nothing_clips(scene):
    wall = _gable_wall(scene)
    _roof(scene, eaves_h=100.0, ridge_h=140.0)     # never clips (see above)
    _room(scene)
    assert roof_clip_spans(scene, wall) == []

    img = _render(scene)
    px = round((50.0 - (-20.0)) / 340.0 * 300.0)
    any_ink = any(_is_clip_ink(img.pixelColor(x, y))
                 for x in range(px - 2, px + 3) for y in range(0, 300, 5))
    assert not any_ink, "clip ink painted with nothing analytically clipped"


# --------------------------------------------------------------------------
# a stale reference handed in directly
# --------------------------------------------------------------------------
# Investigating a crash Patrick's own check hit (roughly: several roofs
# incl. one at 45deg, then File > New): `scene.items()` was checked
# directly and, at least under this Qt build, a `sip.delete()`d item is
# gone from it in the SAME call that deletes it -- `QGraphicsScene`
# appears to detach an item from its own list synchronously as part of
# deleting it, so a roof or room reached THROUGH `scene.items()` was never
# actually reproducible as stale here. What IS real: `roof_clip_spans` is a
# public function, not just `WallItem.paint()`'s private detail, and a
# CALLER holding a wall reference from before it was deleted gets silently
# WRONG spans (computed off whatever plain-Python attributes happen to
# survive C++ deletion) rather than an empty, honest answer. `sip.delete()`
# forces that state directly rather than needing to win a real Qt
# scheduling race. The roof/room guards inside the function are kept as
# the same cheap, established precaution `walls.py`'s own `sip.isdeleted`
# checks already are elsewhere in this codebase, but this file does not
# claim a test proves them load-bearing -- `scene.items()` did not hand
# back a stale one in anything tried here, so nothing here reproduces
# Patrick's own crash; it narrows what this session could rule out, not
# what caused it.
def test_a_stale_wall_reference_gets_an_empty_answer_not_wrong_data(scene):
    wall = _gable_wall(scene)
    _roof(scene)
    _room(scene)
    live = roof_clip_spans(scene, wall)
    assert live, "precondition: this roof does clip while the wall is live"

    scene.removeItem(wall)
    sip.delete(wall)
    assert sip.isdeleted(wall)
    assert roof_clip_spans(scene, wall) == [], (
        "a wall reference that outlived its own deletion returned data "
        "instead of the honest empty answer")
