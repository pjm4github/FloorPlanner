"""R2c -- the Roof menu's Show roof / Edit roof switches (0145-ruling.md
sec2, authorized 0146-ruling.md): three states (hidden / shown-inert /
shown-editable) gating both paint and hit-testing, invariant Edit=>Show,
persisted per document.
"""
import warnings

import pytest
from PyQt6.QtCore import QPointF

from floorplanner.design.bridge import apply_design_to_scene, design_from_scene
from floorplanner.roofs import RoofItem
from floorplanner.walls import WallItem

pytestmark = pytest.mark.gui


def _walk(win):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return design_from_scene(win).to_dict()


def _apply(win, doc):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        apply_design_to_scene(win, doc)


# --------------------------------------------------------------------------
# defaults and the menu checkboxes
# --------------------------------------------------------------------------
def test_defaults_are_shown_and_editable(fp, win):
    assert win.a_show_roofs.isChecked()
    assert win.a_edit_roofs.isChecked()
    assert win.a_ridge.isEnabled()


def test_a_roof_written_before_r2c_defaults_to_shown_and_editable(fp, win):
    """A saved document with no show_roofs/edit_roofs keys at all (every
    R1/R2/R2b-era file) must still show and allow editing every roof --
    the schema default (true/true), not a migration."""
    win.prepare_headless()
    win.scene.addItem(RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0))
    doc = _walk(win)
    doc["settings"].pop("show_roofs", None)
    doc["settings"].pop("edit_roofs", None)

    win2 = fp.MainWindow()
    win2.prepare_headless()
    _apply(win2, doc)
    roof2 = next(it for it in win2.scene.items() if isinstance(it, RoofItem))
    assert roof2.isVisible() and roof2.isEnabled()
    assert win2.a_show_roofs.isChecked() and win2.a_edit_roofs.isChecked()


# --------------------------------------------------------------------------
# the invariant: Edit => Show
# --------------------------------------------------------------------------
def test_unchecking_show_also_unchecks_edit(fp, win):
    win.a_edit_roofs.setChecked(True)
    win.a_show_roofs.setChecked(False)
    assert not win.a_show_roofs.isChecked()
    assert not win.a_edit_roofs.isChecked()


def test_checking_edit_also_checks_show(fp, win):
    win.a_show_roofs.setChecked(False)         # takes edit down with it
    assert not win.a_edit_roofs.isChecked()
    win.a_edit_roofs.setChecked(True)
    assert win.a_show_roofs.isChecked()
    assert win.a_edit_roofs.isChecked()


def test_a_same_value_toggle_is_a_no_op(fp, win, monkeypatch):
    """The guard both setters share: re-checking an already-checked box
    must not re-run side effects (a load calling setChecked to sync UI
    state must not itself dirty the document)."""
    calls = []
    monkeypatch.setattr(win, "_mark_dirty", lambda *a, **k: calls.append(1))
    win.a_show_roofs.setChecked(True)          # already true
    win.a_edit_roofs.setChecked(True)          # already true
    assert calls == []


# --------------------------------------------------------------------------
# the three states -- paint and hit-testing together
# --------------------------------------------------------------------------
def test_shown_and_editable_roof_wins_the_click_over_a_wall(fp, win):
    win.prepare_headless()
    win.scene.addItem(WallItem(QPointF(0, 0), QPointF(200, 0), "exterior"))
    win.scene.addItem(RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0))
    kinds = {type(it).__name__ for it in win.scene.items(QPointF(100, 0))}
    assert kinds == {"RoofItem", "WallItem"}


def test_shown_not_editable_roof_is_painted_but_absent_from_hit_census(fp, win):
    """The differential 0145-ruling.md sec2 names as the receipt: the same
    click on the ridge point sees only the wall once Edit is off, even
    though the roof is still visible."""
    win.prepare_headless()
    win.scene.addItem(WallItem(QPointF(0, 0), QPointF(200, 0), "exterior"))
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0)
    win.scene.addItem(roof)

    win.a_edit_roofs.setChecked(False)

    assert roof.isVisible()                    # still rendered
    assert not roof.isEnabled()
    kinds = {type(it).__name__ for it in win.scene.items(QPointF(100, 0))}
    assert kinds == {"WallItem"}                # the roof is not a candidate


def test_hidden_roof_is_absent_from_every_hit_census(fp, win):
    win.prepare_headless()
    win.scene.addItem(WallItem(QPointF(0, 0), QPointF(200, 0), "exterior"))
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0)
    win.scene.addItem(roof)

    win.a_show_roofs.setChecked(False)

    assert not roof.isVisible()
    kinds = {type(it).__name__ for it in win.scene.items(QPointF(100, 0))}
    assert kinds == {"WallItem"}


def test_hidden_roof_is_deselected(fp, win):
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0)
    win.scene.addItem(roof)
    roof.setSelected(True)
    win.a_edit_roofs.setChecked(False)
    assert not roof.isSelected()


def test_the_marker_inherits_visible_and_enabled_from_its_parent(fp, win):
    roof = RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0)
    win.scene.addItem(roof)
    win.a_show_roofs.setChecked(False)
    assert not roof.marker.isVisible()          # Qt ANDs the ancestor chain
    win.a_show_roofs.setChecked(True)
    win.a_edit_roofs.setChecked(False)
    assert roof.marker.isVisible() and not roof.marker.isEnabled()


# --------------------------------------------------------------------------
# the ridge-sketch tool: disabled with Edit off, force-on when reached anyway
# --------------------------------------------------------------------------
def test_the_ridge_tool_is_disabled_when_edit_is_off(fp, win):
    win.a_edit_roofs.setChecked(False)
    assert not win.a_ridge.isEnabled()
    assert not win._tool_actions[fp.TOOL_ROOF_RIDGE].isEnabled()


def test_switching_to_the_ridge_tool_while_editing_it_reverts_to_select(fp, win):
    win.set_tool(fp.TOOL_ROOF_RIDGE)
    win.a_edit_roofs.setChecked(False)
    assert win.tool == fp.TOOL_SELECT


def test_sketching_a_ridge_via_a_bare_macro_g_forces_both_switches_on(fp, win):
    """0145-ruling.md sec2: "sketching the first ridge via the menu turns
    both switches on." A macro's bare "G" token reaches TOOL_ROOF_RIDGE
    directly (bypassing QAction.isEnabled), so the force-on has to live at
    the gesture itself, not only at the action that usually starts it."""
    win.prepare_headless()
    win.a_edit_roofs.setChecked(False)
    win.a_show_roofs.setChecked(False)                  # both off now
    assert not win.a_edit_roofs.isChecked()

    win.run_macro("G")                # bare tool-switch token, no UI gate
    from PyQt6.QtCore import QEvent, Qt
    from PyQt6.QtGui import QMouseEvent
    from PyQt6.QtWidgets import QApplication
    vp = win.view.viewport()
    left = Qt.MouseButton.LeftButton

    def send(etype, sx, sy, buttons):
        pos = win.view.mapFromScene(QPointF(sx, sy))
        QApplication.sendEvent(vp, QMouseEvent(
            etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
            left, buttons, Qt.KeyboardModifier.NoModifier))

    send(QEvent.Type.MouseButtonPress, 0, 0, left)
    assert win.a_show_roofs.isChecked() and win.a_edit_roofs.isChecked()


# --------------------------------------------------------------------------
# round trip
# --------------------------------------------------------------------------
def test_show_edit_roofs_round_trip_through_save_and_load(fp, win):
    win.prepare_headless()
    win.scene.addItem(RoofItem(QPointF(0, 0), QPointF(200, 0), span_in=100.0))
    win.a_edit_roofs.setChecked(False)

    doc = _walk(win)
    assert doc["settings"]["show_roofs"] is True
    assert doc["settings"]["edit_roofs"] is False
    assert len(doc["roofs"]) == 1                # still walked, not deleted

    win2 = fp.MainWindow()
    win2.prepare_headless()
    _apply(win2, doc)
    assert win2.a_show_roofs.isChecked()
    assert not win2.a_edit_roofs.isChecked()
    roof2 = next(it for it in win2.scene.items() if isinstance(it, RoofItem))
    assert roof2.isVisible() and not roof2.isEnabled()
