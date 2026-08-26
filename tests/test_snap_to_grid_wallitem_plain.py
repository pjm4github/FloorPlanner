"""`WallItem`'s plain "Snap to Grid" -- 0108-ruling.md, amended by
0109-ruling.md SS3: the scene-side wiring around `snap_wall_to_grid`
(`tests/test_snap_to_grid.py` covers the pure document math).

Unlike "Snap to Grid Orthogonal" (`tests/test_snap_to_grid_wallitem.py`),
this action needs no anchor -- always enabled, no endpoint hit test -- and
applies to EVERY selected wall in turn when more than one is selected
(0108-ruling.md SS4).
"""
import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QMenu

import FloorPlanner as fp

pytestmark = pytest.mark.walls


class _Ev:
    def __init__(self, scene_pt):
        self._pt = QPointF(*scene_pt)

    def scenePos(self):
        return self._pt

    def screenPos(self):
        return self._pt.toPoint()

    def accept(self):
        pass


def _wall(win, x1, y1, x2, y2):
    w = fp.WallItem(QPointF(x1, y1), QPointF(x2, y2), "interior")
    win.scene.addItem(w)
    return w


def _click_menu_item(monkeypatch, wall, scene_pt, label):
    """EXACT text match -- "Snap to Grid" is a strict prefix of "Snap to
    Grid Orthogonal", so `startswith` (the other test file's helper, where
    only one action starts with its label) would pick the wrong one here.

    Reads `.isEnabled()` INSIDE the callback, while the `QMenu` (and its
    `QAction` children) are still alive -- once `contextMenuEvent` returns,
    the menu is a dead local and PyQt has already deleted the C++ side."""
    found = {}

    def _fake_exec(self, *_a, **_k):
        act = next((a for a in self.actions() if a.text() == label), None)
        found["found"] = act is not None
        found["enabled"] = act is not None and act.isEnabled()
        return act if (act is not None and act.isEnabled()) else None

    monkeypatch.setattr(QMenu, "exec", _fake_exec)
    wall.contextMenuEvent(_Ev(scene_pt))
    return found.get("found", False), found.get("enabled", False)


# ---------------------------------------------------------------------------
# always enabled, no anchor needed
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_the_action_is_enabled_from_the_middle_of_the_wall(win, monkeypatch):
    w = _wall(win, 0, 0, 1200, 0)
    found, enabled = _click_menu_item(monkeypatch, w, (600, 0), "Snap to Grid")
    assert found and enabled


# ---------------------------------------------------------------------------
# the happy path
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_clicking_the_action_snaps_both_ends_independently(win, monkeypatch):
    w = _wall(win, 79.03, 50.0, 78.94, 100.0)
    _click_menu_item(monkeypatch, w, (600, 400), "Snap to Grid")
    assert w.p1.x() == 78.0 and w.p1.y() == 48.0
    assert w.p2.x() == 78.0 and w.p2.y() == 102.0
    assert "1 wall(s) snapped" in win.statusBar().currentMessage()


@pytest.mark.gui
def test_a_wall_already_on_grid_reports_nothing_to_snap(win, monkeypatch):
    w = _wall(win, 0.0, 0.0, 0.0, 120.0)
    _click_menu_item(monkeypatch, w, (0.0, 60.0), "Snap to Grid")
    assert w.p1 == QPointF(0.0, 0.0)
    assert w.p2 == QPointF(0.0, 120.0)
    assert "nothing to snap" in win.statusBar().currentMessage()


# ---------------------------------------------------------------------------
# refusal -- nothing changes, status explains why
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_a_degenerate_result_is_refused_and_the_scene_is_untouched(win, monkeypatch):
    w = _wall(win, 0.0, 0.0, 2.0, 1.0)
    before = (QPointF(w.p1), QPointF(w.p2))
    _click_menu_item(monkeypatch, w, (1.0, 0.5), "Snap to Grid")
    assert (w.p1, w.p2) == before
    assert "refused" in win.statusBar().currentMessage()


# ---------------------------------------------------------------------------
# multi-select -- every selected wall snaps, guards re-evaluated between
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_multi_select_snaps_every_selected_wall(win, monkeypatch):
    w1 = _wall(win, 79.03, 50.0, 78.94, 100.0)
    w2 = _wall(win, 500.0, 200.03, 500.0, 300.0)   # already grid-x, off-grid y
    w1.setSelected(True)
    w2.setSelected(True)
    _click_menu_item(monkeypatch, w1, (600, 400), "Snap to Grid")
    assert w1.p1.x() == 78.0 and w1.p1.y() == 48.0
    assert w2.p1.y() == 198.0
    assert "2 wall(s) snapped" in win.statusBar().currentMessage()


@pytest.mark.gui
def test_a_non_selected_wall_is_unaffected_by_another_walls_menu(win, monkeypatch):
    """Right-clicking w1 while it is NOT part of a multi-selection only
    snaps w1 -- w2 stays exactly where it started."""
    w1 = _wall(win, 79.03, 50.0, 78.94, 100.0)
    w2 = _wall(win, 500.0, 200.03, 500.0, 300.0)
    before_w2 = (QPointF(w2.p1), QPointF(w2.p2))
    _click_menu_item(monkeypatch, w1, (600, 400), "Snap to Grid")
    assert (w2.p1, w2.p2) == before_w2
    assert "1 wall(s) snapped" in win.statusBar().currentMessage()


@pytest.mark.gui
def test_multi_select_reports_a_mix_of_snapped_and_refused(win, monkeypatch):
    w1 = _wall(win, 79.03, 50.0, 78.94, 100.0)      # snaps cleanly
    w2 = _wall(win, 0.0, 0.0, 2.0, 1.0)             # degenerate -- refused
    w1.setSelected(True)
    w2.setSelected(True)
    _click_menu_item(monkeypatch, w1, (600, 400), "Snap to Grid")
    msg = win.statusBar().currentMessage()
    assert "1 wall(s) snapped" in msg
    assert "1 refused" in msg
    assert "degenerate" in msg
