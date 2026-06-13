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
    """Isolate tests that mutate global SETTINGS (snap / canvas size)."""
    _fp.SETTINGS.update(_fp.DEFAULT_SETTINGS)
    yield
    _fp.SETTINGS.update(_fp.DEFAULT_SETTINGS)


@pytest.fixture
def scene(qapp):
    """A bare QGraphicsScene -- enough for wall/room/furnishing geometry.

    Faster than a full MainWindow; use `win` only when you need the menus,
    the view, or import/export/group helpers."""
    s = QGraphicsScene()
    yield s
    s.clear()


@pytest.fixture
def win(qapp):
    """A fresh MainWindow (full UI) -- for io / group / gui tests."""
    w = _fp.MainWindow()
    w.resize(1200, 800)
    yield w
    w.close()


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
    def _drag(win, scene_pt, dx_px, dy_px, steps=2):
        vp = win.view.viewport()
        start = win.view.mapFromScene(QPointF(scene_pt))

        def send(etype, pt, button, buttons):
            ev = QMouseEvent(etype, QPointF(pt), vp.mapToGlobal(QPointF(pt)),
                             button, buttons, Qt.KeyboardModifier.NoModifier)
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
def counts(fp):
    """(#walls, #furnishings, #rooms) currently in a scene."""
    def _counts(scene):
        items = list(scene.items())
        return (sum(isinstance(i, fp.WallItem) for i in items),
                sum(isinstance(i, fp.FurnishingItem) for i in items),
                sum(isinstance(i, fp.RoomItem) for i in items))
    return _counts
