"""Shared pytest fixtures and helpers for the FloorPlanner test suite.

The app is a headless-friendly PyQt6 GUI, so we run Qt with the offscreen
platform and own the QApplication ourselves (no pytest-qt needed). The
QApplication MUST exist before any widget is built, so it is created at
import time here -- conftest is imported before any test module.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QGraphicsScene

_app = QApplication.instance() or QApplication([])

import FloorPlanner as _fp


# --------------------------------------------------------------------------
# Selective running: `--quick` skips the slow + gui tests for fast feedback
# during feature work.  (Equivalent to `-m "not slow and not gui"`.)
# --------------------------------------------------------------------------
def pytest_addoption(parser):
    parser.addoption("--quick", action="store_true", default=False,
                     help="skip slow and gui tests for fast feedback")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--quick"):
        return
    skip = pytest.mark.skip(reason="--quick: slow/gui tests skipped")
    for item in items:
        if "slow" in item.keywords or "gui" in item.keywords:
            item.add_marker(skip)


# --------------------------------------------------------------------------
# Core fixtures
# --------------------------------------------------------------------------
@pytest.fixture(scope="session")
def qapp():
    """The single QApplication for the whole test session."""
    return _app


@pytest.fixture
def fp():
    """The FloorPlanner module under test."""
    return _fp


@pytest.fixture(autouse=True)
def _reset_settings():
    """Isolate tests that mutate global SETTINGS (snap / canvas size) or the
    runtime floor cache (active/reference/show-others)."""
    def _reset():
        _fp.SETTINGS.update(_fp.DEFAULT_SETTINGS)
        _fp.set_floor_state(active=_fp.DEFAULT_FLOOR, reference=set(),
                            show_others=False)
    _reset()
    yield
    _reset()


@pytest.fixture
def scene(qapp):
    """A bare QGraphicsScene -- enough for wall/room/furnishing geometry.

    Faster than a full MainWindow; use `win` only when you need the menus,
    the view, or import/export/group helpers."""
    s = QGraphicsScene()
    _verify_rebase(s)
    yield s
    _verify_teardown(s, "scene fixture teardown")
    s.clear()


@pytest.fixture
def win(qapp):
    """A fresh MainWindow (full UI) -- for io / group / gui tests."""
    w = _fp.MainWindow()
    w.resize(1200, 800)
    _verify_rebase(w)
    yield w
    _verify_teardown(w, "win fixture teardown")
    dispose_window(w)


# --------------------------------------------------------------------------
# DEFECT 28 -- a closed window is not a destroyed one.
#
# This fixture used to end with `w.close()`, which HIDES a window and neither
# destroys it nor stops its 180 ms dirty timer.  MainWindows therefore
# accumulated for the whole session (measured: peak 16 live, 9 of them holding
# an active timer, 12 still alive at session end), and any later test that
# pumps the event loop -- the macro runner calls `processEvents()` after every
# token -- let a stale timer fire, walk its own dead scene and write a report
# under the running test's name.  That is how a macro test building ONE room
# produced a corpse containing symmetricP1's twenty.
#
# The guard below is the acceptance, and it is stated as the invariant rather
# than as a count: after a test, no MainWindow is left holding a live dirty
# timer.  A budget on the number alone would pass a suite that leaks windows
# quietly as long as it leaked few enough.
#
# The app half -- `MainWindow.close()` itself leaving the timer running, which
# costs a USER a full document walk every 180 ms for a window they believe is
# gone -- is defect 29, fixed separately: a behaviour change in the app has no
# business riding in under a test-isolation fix.
# --------------------------------------------------------------------------
def _mainwindows():
    out = []
    for w in QApplication.topLevelWidgets():
        try:
            if isinstance(w, _fp.MainWindow):
                out.append(w)
        except RuntimeError:                 # destroyed C++ side mid-iteration
            pass
    return out


def _timer_is_live(w):
    t = getattr(w, "_dirty_timer", None)
    try:
        return bool(t is not None and t.isActive())
    except RuntimeError:                     # already destroyed C++ side
        return False


def dispose_window(w):
    """Destroy a MainWindow, rather than merely hiding it.

    ORDER MATTERS, and getting it wrong is how the first cut of this failed:
    closing emits scene changes, which reach `_mark_dirty` and RESTART the
    timer -- so stopping it before the close silences a timer that is then
    started again. Close, let those signals settle, and only then stop it.

    `processEvents()` alone does not deliver `DeferredDelete`, so the window
    would survive `deleteLater()` and keep counting against the guard;
    `sendPostedEvents(None, DeferredDelete)` is what actually destroys it."""
    w.close()
    _app.processEvents()                     # close-time signals settle first
    t = getattr(w, "_dirty_timer", None)
    if t is not None:
        t.stop()
    w.deleteLater()
    _app.sendPostedEvents(None, QEvent.Type.DeferredDelete)


@pytest.fixture(autouse=True)
def _no_window_outlives_its_test(qapp):
    """Dispose every MainWindow a test created, then assert none is left with a
    live dirty timer.

    Autouse fixtures tear down LAST, so this runs after `win`'s own finalizer
    and catches the windows tests build for themselves too (test_io,
    test_floors, test_load_path and test_rooms all do)."""
    before = {id(w) for w in _mainwindows()}
    yield
    for w in _mainwindows():
        if id(w) not in before:
            dispose_window(w)
    stale = [w for w in _mainwindows() if _timer_is_live(w)]
    assert not stale, (
        f"{len(stale)} MainWindow(s) outlived the test still holding a live "
        f"180 ms dirty timer -- each will walk its own dead scene inside a "
        f"later test that pumps the event loop (defect 28).")


# --------------------------------------------------------------------------
# P1.6 shadow mode (FP_VERIFY_DESIGN=1): verify every test's final scene.
#
# The app's own per-operation hook hangs off the 180 ms dirty timer, which
# NEVER FIRES headless -- so without this the suite could mutate scenes all day
# and verify nothing.  Each fixture starts with an empty baseline, so any fault
# a test introduces is a regression against `{}`; tests that load a corrupt
# legacy file rebase at load, via MainWindow.apply_project_to_scene.
#
# Both helpers are no-ops with the flag off, so the suite runs unmodified.
# --------------------------------------------------------------------------
def _verify_rebase(target):
    from floorplanner.design.verify import rebase, verify_enabled
    if verify_enabled():
        rebase(target)


def _verify_teardown(target, where):
    from floorplanner.design.verify import verify, verify_enabled
    if not verify_enabled():
        return
    verify(target, where)                    # cheap twelve, per the P1.2 split


# --------------------------------------------------------------------------
# Builders
# --------------------------------------------------------------------------
@pytest.fixture
def add_walls(fp):
    """Add a rectangle of 4 walls to a scene; returns the wall list."""
    def _add(scene, x, y, w, h, wall_type="interior"):
        corners = [QPointF(x, y), QPointF(x + w, y),
                   QPointF(x + w, y + h), QPointF(x, y + h)]
        walls = []
        for i in range(4):
            wall = fp.WallItem(corners[i], corners[(i + 1) % 4], wall_type)
            scene.addItem(wall)
            walls.append(wall)
        fp.rebuild_all_walls(scene)
        return walls
    return _add


@pytest.fixture
def make_room(fp, add_walls):
    """Build a walled rectangular room and add a RoomItem; returns it."""
    def _make(scene, x, y, w, h, name="Room"):
        add_walls(scene, x, y, w, h)
        centre = QPointF(x + w / 2, y + h / 2)
        res = fp.detect_room(scene, centre)
        assert res is not None, "room not detected -- check wall geometry"
        room = fp.RoomItem(fp.unique_room_name(scene, name), centre,
                           res[0], res[1], corners=res[2])
        scene.addItem(room)
        fp.bind_room_walls(scene, room)      # rooms own their enclosing walls
        return room
    return _make


@pytest.fixture
def first_furnishing(fp):
    """Id of the first catalog furnishing (stable across asset changes)."""
    cat = fp.furnishing_catalog()
    assert cat, "furnishing catalog is empty -- run python _gen_assets.py"
    return cat[0]["id"]


@pytest.fixture
def drag(qapp):
    """Perform a synthetic left-button drag through the view's viewport.

    QTest.mouseMove can't synthesize button-held moves, so we build real
    QMouseEvents with buttons=LeftButton and post them to the viewport."""
    def _drag(win, scene_pt, dx_px, dy_px, steps=2,
              mods=Qt.KeyboardModifier.NoModifier):
        vp = win.view.viewport()
        start = win.view.mapFromScene(QPointF(scene_pt))

        def send(etype, pt, button, buttons):
            ev = QMouseEvent(etype, QPointF(pt), vp.mapToGlobal(QPointF(pt)),
                             button, buttons, mods)
            QApplication.sendEvent(vp, ev)
            qapp.processEvents()

        send(QEvent.Type.MouseButtonPress, start, Qt.MouseButton.LeftButton,
             Qt.MouseButton.LeftButton)
        for k in range(1, steps + 1):
            pt = start + QPoint(int(dx_px * k / steps), int(dy_px * k / steps))
            send(QEvent.Type.MouseMove, pt, Qt.MouseButton.NoButton,
                 Qt.MouseButton.LeftButton)
        end = start + QPoint(dx_px, dy_px)
        send(QEvent.Type.MouseButtonRelease, end, Qt.MouseButton.LeftButton,
             Qt.MouseButton.NoButton)
    return _drag


@pytest.fixture
def click(qapp):
    """A press+release at ONE scene point, with no movement between.

    The gesture `drag` cannot express, and the one D53 is about: a CLICK.
    `drag` always moves, so every gesture-level test in this suite until now
    exercised the drag path and none exercised the press-and-let-go path --
    which is part of why a room that could not be clicked went unnoticed.

    Modifiers pass through, so shift/ctrl toggling is testable.
    """
    def _click(win, scene_pt, mods=Qt.KeyboardModifier.NoModifier):
        vp = win.view.viewport()
        pt = QPointF(win.view.mapFromScene(QPointF(scene_pt)))

        def send(etype, button, buttons):
            ev = QMouseEvent(etype, pt, vp.mapToGlobal(pt), button, buttons,
                             mods)
            QApplication.sendEvent(vp, ev)
            qapp.processEvents()

        send(QEvent.Type.MouseButtonPress, Qt.MouseButton.LeftButton,
             Qt.MouseButton.LeftButton)
        send(QEvent.Type.MouseButtonRelease, Qt.MouseButton.LeftButton,
             Qt.MouseButton.NoButton)
    return _click


@pytest.fixture
def counts(fp):
    """(#walls, #furnishings, #rooms) currently in a scene."""
    def _counts(scene):
        items = list(scene.items())
        return (sum(isinstance(i, fp.WallItem) for i in items),
                sum(isinstance(i, fp.FurnishingItem) for i in items),
                sum(isinstance(i, fp.RoomItem) for i in items))
    return _counts
