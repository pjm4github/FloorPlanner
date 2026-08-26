"""`WallItem`'s "Snap to Grid Orthogonal" -- 0110-ruling.md SS2/SS4/SS5:
the scene-side wiring around `snap_wall_to_grid_orthogonal`
(`tests/test_snap_to_grid_orthogonal.py` covers the pure document math).

The action lives on the WALL's own context menu, anchored at whichever end
the right-click landed near -- `WallItem._hit_endpoint`, the SAME hit test
`mousePressEvent` uses to pick its drag mode (0110-ruling.md SS2: "reuse it,
do not invent a second one"). A disabled 15-degree placeholder ships in the
same menu (0110-ruling.md SS4/SS5 tier 3).
"""
import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QMenu

import FloorPlanner as fp

pytestmark = pytest.mark.walls


class _Ev:
    """A context-menu event good enough for `WallItem.contextMenuEvent`."""

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
    """Right-click `wall` at `scene_pt`; pick the menu action whose text
    starts with `label`. Returns that action (so a test can read
    `.isEnabled()`), or `None` if no such action exists."""
    found = {}

    def _fake_exec(self, *_a, **_k):
        found["menu"] = self
        act = next((a for a in self.actions()
                   if a.text().startswith(label)), None)
        found["action"] = act
        return act if (act is not None and act.isEnabled()) else None

    monkeypatch.setattr(QMenu, "exec", _fake_exec)
    wall.contextMenuEvent(_Ev(scene_pt))
    return found.get("action")


# ---------------------------------------------------------------------------
# _hit_endpoint -- the shared hit test
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_hit_endpoint_finds_p1_near_the_start(win):
    w = _wall(win, 0, 0, 1200, 0)
    assert w._hit_endpoint(QPointF(2, 0)) == "p1"


@pytest.mark.gui
def test_hit_endpoint_finds_p2_near_the_end(win):
    w = _wall(win, 0, 0, 1200, 0)
    assert w._hit_endpoint(QPointF(1198, 0)) == "p2"


@pytest.mark.gui
def test_hit_endpoint_is_none_in_the_middle(win):
    w = _wall(win, 0, 0, 1200, 0)
    assert w._hit_endpoint(QPointF(600, 0)) is None


# ---------------------------------------------------------------------------
# the menu -- enabled state and the 15-degree placeholder
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_the_action_is_enabled_near_an_endpoint(win, monkeypatch):
    w = _wall(win, 0, 0, 1200, 0)
    act = _click_menu_item(monkeypatch, w, (2, 0), "Snap to Grid Orthogonal")
    assert act is not None and act.isEnabled()


@pytest.mark.gui
def test_the_action_is_disabled_away_from_either_endpoint(win, monkeypatch):
    w = _wall(win, 0, 0, 1200, 0)
    act = _click_menu_item(monkeypatch, w, (600, 0), "Snap to Grid Orthogonal")
    assert act is not None and not act.isEnabled()
    assert act.toolTip()


@pytest.mark.gui
def test_the_15_degree_placeholder_is_disabled_with_a_tooltip(win, monkeypatch):
    w = _wall(win, 0, 0, 1200, 0)
    act = _click_menu_item(monkeypatch, w, (2, 0), "Snap to 15")
    assert act is not None
    assert not act.isEnabled()
    assert "0110-ruling" in act.toolTip()


# ---------------------------------------------------------------------------
# the happy path -- clicking the action snaps and centres feedback in status
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_clicking_the_action_snaps_the_wall_and_reports_it(win, monkeypatch):
    w = _wall(win, 79.03, 50.0, 78.94, 100.0)
    _click_menu_item(monkeypatch, w, (79.03, 50.0), "Snap to Grid Orthogonal")
    walls = [it for it in win.scene.items() if isinstance(it, fp.WallItem)]
    assert len(walls) == 1
    ww = walls[0]
    assert ww.p1.x() == ww.p2.x() == 78.0     # exactly vertical, on grid
    assert ww.p1.y() == 48.0
    assert ww.p2.y() == 102.0
    assert "Snapped wall" in win.statusBar().currentMessage()


@pytest.mark.gui
def test_clicking_the_far_end_anchors_there_instead(win, monkeypatch):
    w = _wall(win, 79.03, 50.0, 78.94, 100.0)
    _click_menu_item(monkeypatch, w, (78.94, 100.0), "Snap to Grid Orthogonal")
    walls = [it for it in win.scene.items() if isinstance(it, fp.WallItem)]
    ww = walls[0]
    assert ww.p1.x() == ww.p2.x() == 78.0
    assert ww.p2.y() == 102.0                 # the clicked end, unchanged shape
    assert ww.p1.y() == 48.0


# ---------------------------------------------------------------------------
# refusal -- nothing changes, status explains why
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_a_degenerate_result_is_refused_and_the_scene_is_untouched(win, monkeypatch):
    w = _wall(win, 0.0, 0.0, 2.0, 1.0)
    before = (QPointF(w.p1), QPointF(w.p2))
    _click_menu_item(monkeypatch, w, (0.0, 0.0), "Snap to Grid Orthogonal")
    assert (w.p1, w.p2) == before
    assert "refused" in win.statusBar().currentMessage()


@pytest.mark.gui
def test_a_near_45_wall_is_refused_and_the_scene_is_untouched(win, monkeypatch):
    w = _wall(win, 0.0, 0.0, 100.0, 99.0)
    before = (QPointF(w.p1), QPointF(w.p2))
    _click_menu_item(monkeypatch, w, (0.0, 0.0), "Snap to Grid Orthogonal")
    assert (w.p1, w.p2) == before
    assert "refused" in win.statusBar().currentMessage()


# ---------------------------------------------------------------------------
# a shared corner moves every wall that holds it -- by construction
# ---------------------------------------------------------------------------

@pytest.mark.gui
def test_a_shared_corner_carries_its_neighbour_along(win, monkeypatch):
    """`wZ` and `w1` share the vertex at (79.03, 50.0) (welded on add, this
    app's own default). Snapping `w1` at that corner moves `wZ`'s far end
    too -- P3.1's identity-carrying relocation, not a copy."""
    wz = _wall(win, -100.0, 50.0, 79.03, 50.0)
    w1 = _wall(win, 79.03, 50.0, 78.94, 100.0)
    _click_menu_item(monkeypatch, w1, (79.03, 50.0), "Snap to Grid Orthogonal")
    assert w1.p1.x() == 78.0 and w1.p1.y() == 48.0
    assert wz.p2.x() == 78.0 and wz.p2.y() == 48.0
