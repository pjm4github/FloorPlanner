"""Alt+click click-cycling through items stacked under one point (his report,
2026-11-07: a hand-drawn L2 wall, and a dormer's own minted walls raised with
their room, sit above the roof's grips, so a buried dormer can never be selected
and opened). Alt+click selects the top; Alt+click again at the same spot cycles
to the next one down and lifts it. A roof also opens on a plain double-click of
its ridge -- the door a cycled-to dormer uses.
"""
import pytest
from PyQt6.QtCore import QPoint, QPointF

from floorplanner.config import active_floor
from floorplanner.roofs import RoofItem
from floorplanner.walls import WallItem

pytestmark = pytest.mark.gui


def _vp_at(view, sp):
    """A viewport point that maps to scene point `sp`, with `sp` scrolled into
    view first so `items()` can find what sits there."""
    view.resetTransform()
    view.centerOn(sp)
    return view.mapFromScene(sp)


def test_alt_click_cycles_through_stacked_items(fp, win):
    win.prepare_headless()
    sc = win.scene
    fl = active_floor()
    c = sc.sceneRect().center()                   # mid-scene: never clamped off
    cx, cy = c.x(), c.y()
    # two walls crossing at the centre -- both shapes cover that point
    w1 = WallItem(QPointF(cx - 100, cy), QPointF(cx + 100, cy), "exterior")
    w2 = WallItem(QPointF(cx, cy - 100), QPointF(cx, cy + 100), "interior")
    for w in (w1, w2):
        w.floor = fl
        sc.addItem(w)
    view = win.view
    vp = _vp_at(view, QPointF(cx, cy))

    targets = view._stacked_targets(vp)
    assert set(targets) == {w1, w2}, "both stacked walls must be candidates"

    assert view._cycle_select(vp)                 # first: the top candidate
    first = next(it for it in (w1, w2) if it.isSelected())
    assert view._cycle_select(vp)                 # repeat at the same spot: cycle
    second = next(it for it in (w1, w2) if it.isSelected())
    assert second is not first                    # advanced to the other one
    assert not first.isSelected()                 # and only one is selected
    assert view._cycle_select(vp)                 # wraps back round
    assert next(it for it in (w1, w2) if it.isSelected()) is first


def test_alt_click_cycle_tolerates_cursor_jitter(fp, win):
    """A person clicking "the same spot" twice moves several pixels between
    clicks (his report 2026-11-07: a 4px window made every Alt+click restart at
    the top, so the dormer under the wall never arrived). Clicks a few pixels
    apart over the same stack still advance the cycle."""
    win.prepare_headless()
    sc = win.scene
    fl = active_floor()
    c = sc.sceneRect().center()
    cx, cy = c.x(), c.y()
    # two walls on the SAME line, so a point and a nearby point share the stack
    w1 = WallItem(QPointF(cx - 120, cy), QPointF(cx + 120, cy), "exterior")
    w2 = WallItem(QPointF(cx - 120, cy), QPointF(cx + 120, cy), "interior")
    for w in (w1, w2):
        w.floor = fl
        sc.addItem(w)
    view = win.view
    vp = _vp_at(view, QPointF(cx, cy))
    view._cycle_select(vp)
    first = next(it for it in (w1, w2) if it.isSelected())
    # a second click a few pixels along the wall (past the old 4px window, still
    # over the same stack) must still advance -- not restart at the top
    view._cycle_select(QPoint(vp.x() + 7, vp.y()))
    second = next(it for it in (w1, w2) if it.isSelected())
    assert second is not first                            # still advanced


def test_alt_click_reaches_a_roof_buried_under_a_lifted_wall(fp, win):
    """The real case: a selectable wall lifted above a roof at the same point.
    A first Alt+click takes the wall (higher priority); a second reaches the
    roof underneath and selects it, which is what makes its grips appear."""
    win.prepare_headless()
    win._set_show_roofs(True)
    win._set_edit_roofs(True)
    sc = win.scene
    fl = active_floor()
    c = sc.sceneRect().center()
    cx, cy = c.x(), c.y()
    rf = RoofItem(QPointF(cx - 100, cy), QPointF(cx + 100, cy),
                  eaves_h_in=80.0, ridge_h_in=132.0, span_in=100.0)
    rf.floor = fl
    sc.addItem(rf)
    wall = WallItem(QPointF(cx - 100, cy), QPointF(cx + 100, cy), "exterior")
    wall.floor = fl
    sc.addItem(wall)
    wall.setZValue(10_000)                         # as a raised room's wall sits
    view = win.view
    vp = _vp_at(view, QPointF(cx, cy))

    assert rf in view._stacked_targets(vp), "the roof ridge must be a candidate"
    view._cycle_select(vp)                         # the wall (outranks the roof)
    assert wall.isSelected() and not rf.isSelected()
    view._cycle_select(vp)                         # ...cycles down to the roof
    assert rf.isSelected() and not wall.isSelected()


def test_double_click_a_roof_ridge_opens_its_dialog(fp, win, monkeypatch):
    """A roof opens on a plain double-click of its ridge -- the door a cycled-to
    dormer uses once selected (no need to find its small apex grip)."""
    from PyQt6.QtCore import QEvent, Qt
    from PyQt6.QtGui import QMouseEvent
    win.prepare_headless()
    win._set_show_roofs(True)
    win._set_edit_roofs(True)
    rf = RoofItem(QPointF(0, 100), QPointF(200, 100),
                  eaves_h_in=80.0, ridge_h_in=132.0, span_in=100.0)
    rf.floor = active_floor()
    win.scene.addItem(rf)
    opened = []
    monkeypatch.setattr(rf, "open_end_on_dialog", lambda *a, **k: opened.append(1))
    ev = QMouseEvent(QEvent.Type.MouseButtonDblClick, QPointF(100, 100),
                     Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier)
    rf.mouseDoubleClickEvent(ev)
    assert opened == [1]
