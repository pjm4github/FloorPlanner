"""A6 -- grid snap by default (ROADMAP.md A6; read back at 0207-report.md;
built on Patrick's word, 2026-10-03: "yes to all four, proceed with the
build"; angled walls excepted by his word of the same day).

The read-back measured that the default snapped the DISTANCE moved, not the
place landed: an off-grid wall stayed off the grid through every gesture.
These pin the four decisions and the four acceptance lines, each case taken
from the read-back's own probe (`docs/evidence/a6_grid_snap_readback_probe.py`)
and each failing on the code before the build:

  1. the end LANDS on the grid -- draw, end drag, body slide;
  2. Shift is unconstrained;
  3. a gesture's weld radius is 3in: a 6in reveal survives, coincident
     ends still weld;
  4. the readout is the snapped end, the length and the heading;
  and the same landing at every zoom.
"""
import pytest
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication

pytestmark = pytest.mark.gui

LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
NOMOD = Qt.KeyboardModifier.NoModifier
SHIFT = Qt.KeyboardModifier.ShiftModifier
CTRL = Qt.KeyboardModifier.ControlModifier


def _zoom(win, z):
    win.resize(1400, 1000)
    win.prepare_headless()
    win.view.resetTransform()
    win.view.scale(z, z)
    win.view.centerOn(QPointF(300.0, 230.0))


def _send(win, etype, p, button, buttons, mods):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(*p))
    assert vp.rect().contains(pos), f"{p} is outside the viewport"
    QApplication.sendEvent(vp, QMouseEvent(
        etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)), button, buttons, mods))


def _drag(win, a, b, mods=NOMOD, release=True):
    _send(win, QEvent.Type.MouseButtonPress, a, LEFT, LEFT, mods)
    _send(win, QEvent.Type.MouseMove, b, NONE, LEFT, mods)
    if release:
        _send(win, QEvent.Type.MouseButtonRelease, b, LEFT, NONE, mods)


def _wall(fp, win, a, b):
    w = fp.WallItem(QPointF(*a), QPointF(*b), "interior")
    win.scene.addItem(w)
    fp.rebuild_all_walls(win.scene)
    return w


def _walls(fp, win):
    return [it for it in win.scene.items() if isinstance(it, fp.WallItem)]


def _draw(fp, win, a, b, mods=NOMOD):
    before = set(map(id, _walls(fp, win)))
    win.set_tool(fp.TOOL_WALL_INT)
    _drag(win, a, b, mods)
    win.set_tool(fp.TOOL_SELECT)
    return next(w for w in _walls(fp, win) if id(w) not in before)


def _on_grid(v, step=6.0):
    return abs(v / step - round(v / step)) < 1e-6


# --------------------------------------------------------------------------
# 1. the end LANDS on the grid
# --------------------------------------------------------------------------
def test_a_wall_drawn_from_an_off_grid_corner_ends_on_the_grid(fp, win):
    """Before: (123,203) -> end (249,203), 126in of length and x off the
    grid. Now the end's own x is rounded; the corner it started from is not
    moved, so y stays 203."""
    _zoom(win, 2.0)
    _wall(fp, win, (123, 303), (123, 203))
    w = _draw(fp, win, (124, 204), (250, 206))
    assert (w.p1.x(), w.p1.y()) == pytest.approx((123.0, 203.0)), "started on the corner"
    assert w.p2.x() == pytest.approx(252.0) and _on_grid(w.p2.x())
    assert w.p2.y() == pytest.approx(203.0), "square to the corner it began at"


def test_an_end_dragged_on_an_off_grid_wall_lands_on_the_grid(fp, win):
    """Before: p2 went 243 -> 279 (36in, a whole number of steps, still off
    the grid). Now 276."""
    _zoom(win, 2.0)
    w = _wall(fp, win, (123, 203), (243, 203))
    _drag(win, (243, 203), (278, 210))
    assert w.p2.x() == pytest.approx(276.0) and _on_grid(w.p2.x())
    assert w.p2.y() == pytest.approx(203.0), "along its own axis"
    assert (w.p1.x(), w.p1.y()) == pytest.approx((123.0, 203.0)), "the far end did not move"


def test_an_off_grid_wall_slid_sideways_comes_onto_the_grid(fp, win):
    """Before: y went 203 -> 221 (18in). Now 222."""
    _zoom(win, 2.0)
    w = _wall(fp, win, (123, 203), (243, 203))
    _drag(win, (183, 203), (192, 223))
    assert w.p1.y() == pytest.approx(222.0) and w.p2.y() == pytest.approx(222.0)
    assert _on_grid(w.p1.y())
    assert (w.p1.x(), w.p2.x()) == pytest.approx((123.0, 243.0)), "slid, not shifted along"


def test_a_drag_that_is_not_a_slide_leaves_an_off_grid_wall_alone(fp, win):
    """Landing on the grid is for a wall that is MOVED. A drag along the
    wall, or a click that wobbled under an inch sideways, moves nothing --
    found at the build: without this an off-grid wall jumped to its grid
    line on any touch (`dragWallFuseStraggler.fpm` line 5 shifted the
    interior column 1.44in)."""
    _zoom(win, 2.0)
    w = _wall(fp, win, (123, 203), (243, 203))
    _drag(win, (183, 203), (223, 203))              # 40in ALONG the wall
    assert (w.p1.y(), w.p2.y()) == pytest.approx((203.0, 203.0))
    _drag(win, (183, 203), (183, 203.5))            # a half-inch wobble
    assert (w.p1.y(), w.p2.y()) == pytest.approx((203.0, 203.0))
    _drag(win, (183, 203), (183, 204.5))            # a real, small slide
    assert (w.p1.y(), w.p2.y()) == pytest.approx((204.0, 204.0)),         "the nearest grid line is reachable by a small deliberate drag"


def test_an_on_grid_wall_behaves_exactly_as_before(fp, win):
    _zoom(win, 2.0)
    w = _draw(fp, win, (120, 120), (247, 133))
    assert (w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y()) == pytest.approx((120, 120, 246, 120))
    _drag(win, (246, 120), (281, 127))
    assert (w.p2.x(), w.p2.y()) == pytest.approx((282.0, 120.0))
    _drag(win, (200, 120), (209, 140))
    assert (w.p1.y(), w.p2.y()) == pytest.approx((138.0, 138.0))


def test_an_angled_wall_is_left_out_of_it(fp, win):
    """His word: "except for off angle walls". An angled wall's end still
    moves by whole steps of LENGTH along its own axis, as before."""
    _zoom(win, 2.0)
    w = _wall(fp, win, (120, 120), (204, 204))            # 45 degrees
    length0 = w.length()
    _drag(win, (204, 204), (230, 230))
    grown = w.length() - length0
    assert grown > 1.0
    assert _on_grid(w.length()), "length in whole steps along the ray"
    assert abs((w.p2.x() - w.p1.x()) - (w.p2.y() - w.p1.y())) < 1e-6, "still 45 degrees"


# --------------------------------------------------------------------------
# 2. Shift is unconstrained
# --------------------------------------------------------------------------
def test_shift_draws_to_the_cursor_itself_off_the_grid(fp, win):
    _zoom(win, 2.0)
    w = _draw(fp, win, (120, 120), (247, 133), SHIFT)
    assert (w.p2.x(), w.p2.y()) == pytest.approx((247.0, 133.0), abs=0.6), \
        "the cursor, to within a pixel -- before A6 this was (246, 132)"
    assert not (_on_grid(w.p2.x()) and _on_grid(w.p2.y()))


def test_ctrl_still_gives_fifteen_degree_steps(fp, win):
    _zoom(win, 2.0)
    w = _draw(fp, win, (120, 120), (220, 204), CTRL)       # ~40 degrees -> 45
    assert (w.p2.x() - 120) == pytest.approx(w.p2.y() - 120, abs=1e-6)


# --------------------------------------------------------------------------
# 3. a gesture's weld radius is under one step
# --------------------------------------------------------------------------
def test_a_six_inch_reveal_survives_and_coincident_ends_still_weld(fp, win):
    _zoom(win, 2.0)
    other = _wall(fp, win, (360, 300), (360, 400))
    short = _draw(fp, win, (240, 300), (354, 300))
    assert short.p2.x() == pytest.approx(354.0), "left 6in short -- before A6 it was pulled to 360"
    assert not any(v is ov for v in (short._v1, short._v2)
                   for ov in (other._v1, other._v2))

    other2 = _wall(fp, win, (360, 60), (360, 160))
    onit = _draw(fp, win, (240, 160), (360, 160))
    assert (onit.p2.x(), onit.p2.y()) == pytest.approx((360.0, 160.0))
    assert any(v is ov for v in (onit._v1, onit._v2)
               for ov in (other2._v1, other2._v2)), "one shared corner"


def test_the_explicit_weld_pass_keeps_its_nine_inches(fp, scene):
    """Normalize, Close gap and a pixel-extracted plan depend on JOIN_TOL;
    only the gesture's radius changed."""
    from floorplanner.walls import weld_wall_ends
    a = fp.WallItem(QPointF(0, 0), QPointF(120, 0), "interior")
    b = fp.WallItem(QPointF(126, 0), QPointF(126, 100), "interior")
    scene.addItem(a)
    scene.addItem(b)
    fp.rebuild_all_walls(scene)
    weld_wall_ends(scene, a)                               # default radius
    assert a.p2.x() == pytest.approx(126.0)
    assert fp.GESTURE_WELD_IN < fp.SETTINGS["wall_snap_in"] < fp.JOIN_TOL


def test_a_shared_corner_still_carries_both_walls(fp, win):
    _zoom(win, 2.0)
    a = _wall(fp, win, (120, 120), (240, 120))
    b = _wall(fp, win, (240, 120), (240, 240))
    fp.share_coincident_ends(win.scene, a.floor)
    _drag(win, (180, 120), (180, 144))
    assert (a.p2.x(), a.p2.y()) == pytest.approx((240.0, 144.0))
    assert (b.p1.x(), b.p1.y()) == pytest.approx((240.0, 144.0))


# --------------------------------------------------------------------------
# the same landing at every zoom
# --------------------------------------------------------------------------
@pytest.mark.parametrize("zoom", [0.25, 2.0])
def test_a_drawn_end_lands_the_same_at_every_zoom(fp, win, zoom):
    """Before: beside an open-ended wall at x=402 the end landed at 402 at
    0.25x and at 426 at 2x -- the pull was 16 pixels wide, not 9 inches."""
    _zoom(win, zoom)
    _wall(fp, win, (402, 60), (402, 150))
    w = _draw(fp, win, (120, 240), (425, 243))
    assert (w.p2.x(), w.p2.y()) == pytest.approx((426.0, 240.0))


@pytest.mark.parametrize("zoom", [0.25, 2.0])
def test_a_wall_starts_in_the_same_place_at_every_zoom(fp, win, zoom):
    """Before: a press 32in from a wall end started ON that end at 0.25x and
    on the grid at 2x."""
    _zoom(win, zoom)
    _wall(fp, win, (123, 303), (123, 203))
    w = _draw(fp, win, (152, 220), (300, 220))
    assert (w.p1.x(), w.p1.y()) == pytest.approx((150.0, 222.0))


def test_an_off_grid_corner_is_caught_at_the_start_within_three_inches(fp, win):
    """The grid cannot express an off-grid corner, so a press within the
    gesture's 3in reach starts on it -- in scene inches, at any zoom -- and
    a press further off starts on the grid (0210-report.md: it was 9in)."""
    _wall(fp, win, (123, 303), (123, 203))
    for zoom in (0.25, 2.0):
        _zoom(win, zoom)
        got = win.view._snap_start(QPointF(125.0, 205.0))          # 2.8in off
        assert (got.x(), got.y()) == pytest.approx((123.0, 203.0))
        got = win.view._snap_start(QPointF(128.0, 208.0))          # 7.1in off
        assert (got.x(), got.y()) == pytest.approx((126.0, 210.0)), \
            "not caught -- it was, when the reach was 9in"


# --------------------------------------------------------------------------
# 0210: one reach for every pull -- Patrick's own report
# --------------------------------------------------------------------------
@pytest.mark.parametrize("zoom", [0.25, 2.0])
def test_an_end_released_more_than_three_inches_from_an_off_grid_wall_is_not_pulled(
        fp, win, zoom):
    """His report, 2026-10-04: a wall drawn toward a vertical wall and
    released at 6ft landed at 5.27ft -- on the vertical wall, 8.75in away
    -- "I expect that wall to NOT SNAP to the veritcal wall because it is
    more than 3 inches away". The vertical wall is off the grid (63.25in),
    and a pull toward an off-grid target had a 9in reach."""
    _zoom(win, zoom)
    v = _wall(fp, win, (63.25, 60), (63.25, 96))
    w = _draw(fp, win, (96, 72), (72, 72))
    assert min(w.p1.x(), w.p2.x()) == pytest.approx(72.0), "6ft, where it was released"
    assert not any(a is b for a in (w._v1, w._v2) for b in (v._v1, v._v2))


def test_an_end_aimed_at_an_off_grid_wall_still_reaches_it(fp, win):
    """The other half: within 3in the end goes to the wall, so an off-grid
    wall can still be met. The grid point nearest any line is never more
    than 3in from it, so an end aimed at the wall is always in reach."""
    _zoom(win, 2.0)
    _wall(fp, win, (63.25, 60), (63.25, 96))
    w = _draw(fp, win, (96, 72), (66, 72))          # the grid says 66: 2.75in off
    assert min(w.p1.x(), w.p2.x()) == pytest.approx(63.25)


def test_a_dragged_end_more_than_three_inches_from_an_off_grid_wall_is_not_pulled(fp, win):
    _zoom(win, 2.0)
    _wall(fp, win, (63.25, 60), (63.25, 96))
    w = _wall(fp, win, (120, 72), (84, 72))
    _drag(win, (84, 72), (71, 72))                  # 7.75in from the wall
    assert w.p2.x() == pytest.approx(72.0), "the grid, not the wall 8.75in away"
    _drag(win, (72, 72), (65, 72))                  # 1.75in from it
    assert w.p2.x() == pytest.approx(63.25), "within reach: onto the wall's line"


# --------------------------------------------------------------------------
# 4. the readout
# --------------------------------------------------------------------------
def test_the_readout_shows_the_snapped_wall_not_the_cursor(fp, win):
    _zoom(win, 2.0)
    win.set_tool(fp.TOOL_WALL_INT)
    _drag(win, (120, 120), (247, 133), release=False)
    msg = win.statusBar().currentMessage()
    assert fp.fmt_ftin(126.0) in msg, "the snapped length"
    assert "0.0" in msg, "the heading"
    assert fp.fmt_ftin(246.0) in msg and fp.fmt_ftin(120.0) in msg, "the snapped end"
    assert win.coord_label.text() == f"x {fp.fmt_ftin(246.0)}   y {fp.fmt_ftin(120.0)}", \
        "the coordinate label follows the end, not the pointer at (247, 133)"
    win.view.cancel_temp()


def test_the_check_macro_lands_all_four_ends_where_the_instructions_say(fp, win):
    """`fixtures/grid-snap-3in-check.json` + `.fpm` + `.md`: Patrick's own
    manual check, replayed verbatim. Two vertical walls, one on the grid
    (x=60) and one off it (x=63.25, the value in his report); four walls
    drawn toward them. The third is his case: released at 6ft, 8.75in from
    the off-grid wall, and left there."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent / "fixtures"
    win.prepare_headless()
    win.load_path(str(root / "grid-snap-3in-check.json"))
    assert sorted(round(w.p1.x(), 2) for w in _walls(fp, win)) == [60.0, 63.25]
    for line in (root / "grid-snap-3in-check.fpm").read_text().splitlines():
        if line.strip():
            res = win.run_macro(line)
            assert res["ok"], res
    drawn = {round(w.p1.y()): min(w.p1.x(), w.p2.x()) for w in _walls(fp, win)
             if abs(w.p1.y() - w.p2.y()) < 1e-6}
    assert drawn == pytest.approx({72: 72.0, 96: 66.0, 192: 72.0, 216: 63.25})


# --------------------------------------------------------------------------
# 6. two parallel walls one grid step apart stay two walls
#    (Patrick's report, 0210-report.md sec6: "two parallel same-type walls
#    6in apart merge into one ... a 6in gap between parallel walls cannot be
#    drawn today"; built on his word, "start on the parallel walls 6in
#    apart merging"). A GESTURE merges at GESTURE_WELD_IN, the same 3in
#    rule a gesture's weld already follows; the load-time and explicit
#    passes keep the grid-step tolerance.
# --------------------------------------------------------------------------
def _spans(fp, win):
    return sorted((round(w.p1.y(), 2), round(min(w.p1.x(), w.p2.x()), 2),
                   round(max(w.p1.x(), w.p2.x()), 2)) for w in _walls(fp, win))


def test_two_parallel_walls_drawn_one_grid_step_apart_are_two_walls(fp, win):
    win.prepare_headless()
    _draw(fp, win, (120, 120), (360, 120))
    _draw(fp, win, (120, 126), (360, 126))
    assert _spans(fp, win) == [(120.0, 120.0, 360.0), (126.0, 120.0, 360.0)]


def test_a_wall_drawn_within_three_inches_of_a_parallel_one_still_merges(fp, win):
    """The positive control: the merge is still there, at the gesture
    tolerance. An off-grid wall 2in away (placed, not drawn, so the grid
    does not move it) absorbs the one drawn beside it into a single wall."""
    win.prepare_headless()
    _wall(fp, win, (120, 122), (360, 122))
    _draw(fp, win, (120, 120), (360, 120))
    spans = _spans(fp, win)
    assert len(spans) == 1, spans


def test_a_wall_slid_to_one_grid_step_from_a_parallel_one_stays_a_wall(fp, win):
    """The drag release (`WallItem.mouseReleaseEvent`) merges at the same
    tolerance as the draw release."""
    win.prepare_headless()
    _wall(fp, win, (120, 120), (360, 120))
    w = _wall(fp, win, (120, 144), (360, 144))
    win.set_tool(fp.TOOL_SELECT)
    _drag(win, (240, 144), (240, 126))               # slide it to y=126
    assert w.scene() is not None
    assert _spans(fp, win) == [(120.0, 120.0, 360.0), (126.0, 120.0, 360.0)]


def test_the_explicit_pass_keeps_the_grid_step_tolerance(fp, win):
    """What does NOT change: Edit > Coalesce all walls (`normalize_walls`,
    and the legacy loader's `merge_all`) still fuses parallel same-type
    walls within the grid step, as it always has -- the explicit passes
    keep their tolerance, as JOIN_TOL keeps 9in. (A v5 document is applied
    faithfully on load and is not merged there at all.)"""
    from floorplanner.walls import normalize_walls
    win.prepare_headless()
    _wall(fp, win, (120, 120), (360, 120))
    _wall(fp, win, (120, 125), (360, 125))           # 5in: under the step, over 3in
    assert len(_walls(fp, win)) == 2, "the control: placed, not merged"
    merged, *_rest = normalize_walls(win.scene)
    assert merged == 1 and len(_walls(fp, win)) == 1
