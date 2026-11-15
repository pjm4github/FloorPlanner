"""0328 -- 3D-camera PHASE 2: the first-person view becomes a CONTROLLER.

Phase 1 was one-way (plan camera -> view). Phase 2 makes it two-way: the user
walks the 3D view (WASD + mouse-look + Q/E), each step is WRITTEN BACK to the
plan `CameraItem`, and Phase 1's existing pose feed redraws the view from that
one model. The plan camera stays the single source of truth; the view edits it.

What these cover headlessly (offscreen Qt Quick 3D renders blank -- D77 -- so the
QML key/mouse/capture layer itself needs a real walk-test):
  * the write-back MATH (`qml_pose_to_plan` inverts `plan_to_qml_pose`), exact as
    arithmetic and within the grid snap step THROUGH a `CameraItem`;
  * a simulated walk step moves the plan camera horizontally, turns it, clamps to
    the canvas, and leaves the level and the 65in eye height untouched (C1);
  * the undo HOLD: a whole walk is ONE snapshot (`_settle` waits while held);
  * C3 (Esc releases the walk, does NOT close the dialog) and C4 (the hold is
    dropped on release, focus-out, close, and close-all / reload).
"""
import numpy as np
import pytest
from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QDialog

from floorplanner.cameras import CAMERA_EYE_H_IN, CameraItem
from floorplanner.config import DEFAULT_FLOOR, SNAP_STEP, canvas_rect, floor_elevation
from floorplanner.mainwindow import _CameraWalkEventFilter
from floorplanner.roofs import camera_walk_held, hold_camera_walk
from floorplanner.viewer.fp3dq import WalkBridge, plan_to_qml_pose, qml_pose_to_plan

pytestmark = pytest.mark.walls


# -- the write-back math (the correctness proof for driving the plan from QML) --

@pytest.mark.geometry
@pytest.mark.parametrize("ctr", [np.zeros(3),
                                 np.array([50.0, -300.0, 40.0]),
                                 np.array([-120.5, 77.2, 12.0])])
@pytest.mark.parametrize("px,py,rot", [(0.0, 0.0, 0.0), (123.4, 88.6, 0.0),
                                       (10.2, 500.9, 90.0), (300.5, 12.1, 215.0),
                                       (-40.0, 60.0, -45.0), (72.0, 48.0, 359.0)])
def test_qml_pose_to_plan_inverts_plan_to_qml_pose(px, py, rot, ctr):
    """The inverse round-trips `plan -> qml -> plan` to the identity as pure
    arithmetic (eye height and pitch are not read back -- C1 / view-local)."""
    ex, ey, ez, yaw, _pitch = plan_to_qml_pose(px, py, 65.0, rot, ctr)
    bpx, bpy, brot = qml_pose_to_plan(ex, ez, yaw, ctr)
    assert bpx == pytest.approx(px)
    assert bpy == pytest.approx(py)
    assert brot == pytest.approx(rot % 360.0)


def test_round_trip_through_camera_setpos_is_within_the_grid_snap_step(scene):
    """THROUGH a `CameraItem` the round-trip is only within the 1-inch grid step:
    `itemChange` snaps `setPos`. The error must not exceed that step (the ruling:
    don't assert bit-exactness through the item). Rotation is not snapped."""
    ctr = np.array([50.0, -300.0, 40.0])
    cam = CameraItem(QPointF(0, 0), rotation=0.0, floor=DEFAULT_FLOOR)
    scene.addItem(cam)
    for px, py, rot in [(123.4, 88.6, 0.0), (10.2, 500.9, 90.0), (300.5, 12.1, 215.0)]:
        ex, ey, ez, yaw, _pitch = plan_to_qml_pose(px, py, 65.0, rot, ctr)
        bpx, bpy, brot = qml_pose_to_plan(ex, ez, yaw, ctr)
        cam.setPos(QPointF(bpx, bpy))            # itemChange grid-snaps this
        cam.setRotation(brot)
        assert abs(cam.pos().x() - px) <= SNAP_STEP
        assert abs(cam.pos().y() - py) <= SNAP_STEP
        assert cam.rotation() == pytest.approx(rot % 360.0)


# -- the walk step (what the write-back does to the plan camera) ---------------

def test_a_walk_step_moves_horizontally_turns_and_keeps_the_eye_height(scene):
    """A walk step moves the plan camera in its own horizontal frame and turns
    it; the level and the eye height (`pose_3d()[2]`) are untouched -- Option B
    moves only in plan XY, so the eye stays at 65in BY CONSTRUCTION (C1)."""
    cam = CameraItem(QPointF(600, 400), rotation=0.0, floor=DEFAULT_FLOOR)
    scene.addItem(cam)
    z0 = cam.pose_3d()[2]
    assert z0 == pytest.approx(floor_elevation(DEFAULT_FLOOR) + CAMERA_EYE_H_IN)
    cam.apply_walk_step(forward=24.0, strafe=0.0, dyaw=30.0)
    assert cam.pos().x() == pytest.approx(624.0)   # heading +x at rot 0, forward 24
    assert cam.pos().y() == pytest.approx(400.0)
    assert cam.rotation() == pytest.approx(30.0)   # the heading turned
    assert cam.floor == DEFAULT_FLOOR              # the level never changes
    assert cam.pose_3d()[2] == pytest.approx(z0)   # the eye stayed at 65in (C1)


def test_strafe_moves_perpendicular_to_the_heading(scene):
    """`strafe` runs to the right of the heading, not along it."""
    cam = CameraItem(QPointF(600, 400), rotation=0.0, floor=DEFAULT_FLOOR)
    scene.addItem(cam)
    cam.apply_walk_step(forward=0.0, strafe=30.0, dyaw=0.0)
    assert cam.pos().x() == pytest.approx(600.0)   # no forward component
    assert cam.pos().y() == pytest.approx(430.0)   # right of +x (y-down) is +y


def test_a_walk_step_clamps_to_the_canvas(scene):
    """The written position is clamped to `canvas_rect()` -- no wander to
    infinity (no wall collision this phase)."""
    rect = canvas_rect()
    cam = CameraItem(QPointF(rect.right() - 5, 400), rotation=0.0, floor=DEFAULT_FLOOR)
    scene.addItem(cam)
    cam.apply_walk_step(forward=1000.0, strafe=0.0, dyaw=0.0)
    assert cam.pos().x() == pytest.approx(rect.right())
    assert rect.left() <= cam.pos().x() <= rect.right()
    assert rect.top() <= cam.pos().y() <= rect.bottom()


# -- the WalkBridge: Option B input (coalesce + deferred flush + view pitch) ----

def test_the_bridge_defers_and_coalesces_the_walk_steps(qapp):
    """C2: `step` does not move anything synchronously -- it accumulates and arms
    one `singleShot(0)`. The callback fires once, with the SUMMED deltas, on the
    next event-loop turn (so the write-back leaves QML before it touches scene)."""
    bridge = WalkBridge()
    got = []
    bridge._walk_cb = lambda f, s, y: got.append((f, s, y))
    bridge.step(3.0, 0.0, 0.0, 0.0)
    bridge.step(3.0, 1.0, 2.0, 0.0)
    assert got == [], "the move is deferred, not synchronous inside step"
    QApplication.processEvents()
    assert got == [(6.0, 1.0, 2.0)], "the burst coalesced into one summed move"


def test_the_bridge_pitch_is_view_local(qapp):
    """Mouse-look pitch goes to the view (the pitch callback), NEVER to the walk
    callback -- the plan camera owns no pitch (view-local, no schema change)."""
    bridge = WalkBridge()
    moves, pitches = [], []
    bridge._walk_cb = lambda f, s, y: moves.append((f, s, y))
    bridge._pitch_cb = lambda p: pitches.append(p)
    bridge.step(0.0, 0.0, 0.0, -10.0)            # a pure look-down tick
    QApplication.processEvents()
    assert moves == [], "a pitch-only tick moves the plan camera not at all"
    assert pitches == [pytest.approx(-10.0)]     # applied to the view alone


# -- the undo hold: one walk is one snapshot ----------------------------------

def test_one_walk_is_exactly_one_undo_snapshot(win):
    """A walk of several deferred write-backs, with a settle in the middle,
    produces exactly ONE undo step: `_settle` re-arms and returns while the hold
    is up (it does NOT snapshot mid-walk), and takes the one snapshot on release
    (the ruling's HOLD in `_settle`, mirroring `roof_clips_held`)."""
    cam = CameraItem(QPointF(600, 400))
    win.scene.addItem(cam)
    win._settle()                                 # a clean committed baseline
    base = len(win._undo_stack)

    hold_camera_walk(win.scene, True)             # capture takes the hold
    assert camera_walk_held(win.scene)
    cam.apply_walk_step(20.0, 0.0, 5.0)
    QApplication.processEvents()
    win._settle()                                 # the >180ms pause mid-walk
    assert len(win._undo_stack) == base, "no undo step is taken while held"
    assert camera_walk_held(win.scene)
    assert win._dirty_timer.isActive(), "the held settle re-armed the timer"

    cam.apply_walk_step(20.0, 0.0, 5.0)
    QApplication.processEvents()
    hold_camera_walk(win.scene, False)            # release drops the hold
    win._settle()
    assert len(win._undo_stack) == base + 1, "the whole walk is one snapshot"


# -- C3 / C4: capture, Esc, and the hold is never left stuck -------------------

class _Body:
    """A stand-in for `Plan3DQuickWidget`, exposing just the `walk_bridge` the
    dialog's event filter reaches (the real widget needs the Qt Quick 3D stack
    and a display)."""

    def __init__(self, bridge):
        self.walk_bridge = bridge


def _wire(win):
    """A camera 3D dialog wired for a walk exactly as `show_camera_3d_view` does,
    minus the 3D widget: a real `WalkBridge`, the capture/release callbacks into
    `win`, and the real `_CameraWalkEventFilter`. Returns (dlg, bridge)."""
    dlg = QDialog(win)
    bridge = WalkBridge()
    body = _Body(bridge)

    def _capture(d=dlg):
        win._camera_walk_captured.add(id(d))
        hold_camera_walk(win.scene, True)

    bridge._capture_cb = _capture
    bridge._release_cb = lambda d=dlg: win._release_camera_walk(d)
    filt = _CameraWalkEventFilter(win, dlg, body)
    dlg.installEventFilter(filt)
    dlg._walk_filter = filt
    return dlg, bridge


def test_esc_while_captured_releases_the_walk_and_keeps_the_dialog(win):
    """C3: Esc while a walk is captured RELEASES the walk and is CONSUMED -- the
    QDialog does not reject, so the window stays visible."""
    dlg, bridge = _wire(win)
    dlg.show()
    bridge.capture()
    assert bridge.captured and camera_walk_held(win.scene) and dlg.isVisible()
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape,
                   Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(dlg, ev)
    assert dlg.isVisible(), "Esc must NOT close the dialog (C3)"
    assert not bridge.captured, "Esc released the walk"
    assert not camera_walk_held(win.scene), "the hold dropped on release"
    dlg.close()


def test_esc_when_not_captured_is_left_alone(win):
    """Esc with no walk captured is NOT consumed -- the dialog's normal Esc
    (reject) is untouched, so the walk filter only intervenes during a walk."""
    dlg, _bridge = _wire(win)
    dlg.show()
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape,
                   Qt.KeyboardModifier.NoModifier)
    # the filter returns False (does not consume) when no walk is captured
    handled = dlg._walk_filter.eventFilter(dlg, ev)
    assert handled is False
    dlg.close()


def test_c4_the_hold_drops_on_release(win):
    """C4: an explicit release drops the hold."""
    dlg, bridge = _wire(win)
    bridge.capture()
    assert camera_walk_held(win.scene)
    bridge.release()
    assert not camera_walk_held(win.scene)
    dlg.close()


def test_c4_the_hold_drops_on_focus_out(win):
    """C4: the window losing focus (WindowDeactivate) releases a captured walk,
    so a walk left captured can never hold the undo record open."""
    dlg, bridge = _wire(win)
    dlg.show()
    bridge.capture()
    assert camera_walk_held(win.scene)
    QApplication.sendEvent(dlg, QEvent(QEvent.Type.WindowDeactivate))
    assert not bridge.captured, "focus-out released the walk"
    assert not camera_walk_held(win.scene)
    dlg.close()


def test_c4_the_hold_drops_on_close(win):
    """C4: `close_camera_3d_view` drops the hold before closing the window."""
    cam = CameraItem(QPointF(100, 100))
    win.scene.addItem(cam)
    dlg = QDialog(win)
    win._camera_3d_views[id(cam)] = dlg
    win._camera_walk_captured.add(id(dlg))
    hold_camera_walk(win.scene, True)
    win.close_camera_3d_view(cam)
    assert not camera_walk_held(win.scene)


def test_c4_the_hold_drops_on_close_all_and_reload(win):
    """C4: `close_all_camera_3d_views` (called on a design reload) drops the hold
    and clears the captured set, whatever was captured when the reload began."""
    dlg = QDialog(win)
    win._camera_3d_views[id(object())] = dlg
    win._camera_walk_captured.add(id(dlg))
    hold_camera_walk(win.scene, True)
    win.close_all_camera_3d_views()
    assert not camera_walk_held(win.scene)
    assert win._camera_walk_captured == set()
