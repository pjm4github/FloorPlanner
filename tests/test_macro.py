"""Headless macro language (MainWindow.run_macro / MacroRunner) plus the
SVG/PNG canvas-export hooks that the fp_macro.py driver relies on, and the
non-modal MacroRecorderDialog (record / replay / save)."""
import json

import pytest
from PyQt6.QtCore import QEvent, QPointF, Qt, QTimer
from PyQt6.QtGui import QContextMenuEvent, QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import QApplication

pytestmark = pytest.mark.macro


def _counts(win):
    s = win.scene_summary()["counts"]
    return s["walls"], s["rooms"], s["furnishings"]


def test_place_adds_furnishing_at_scene_inches(fp, win):
    res = win.run_macro("PLACE sofa 120 96 0")
    assert res["ok"], res["errors"]
    furn = [it for it in win.scene.items() if isinstance(it, fp.FurnishingItem)]
    assert len(furn) == 1
    assert furn[0].kind == "sofa"
    # pos is the centre, in scene inches
    assert (furn[0].pos().x(), furn[0].pos().y()) == pytest.approx((120, 96))


def test_place_rejects_unknown_kind(fp, win):
    res = win.run_macro("PLACE not_a_real_thing 10 10")
    assert not res["ok"]
    assert res["errors"] and "unknown furnishing" in res["errors"][0]
    assert _counts(win)[2] == 0


def test_wall_and_room_build_and_bind(fp, win):
    macro = ("WALL 0 0 240 0 ext  WALL 240 0 240 180 ext "
             "WALL 240 180 0 180 ext  WALL 0 180 0 0 ext  ROOM Den 120 90")
    res = win.run_macro(macro)
    assert res["ok"], res["errors"]
    w, r, _ = _counts(win)
    assert (w, r) == (4, 1)
    room = next(it for it in win.scene.items() if isinstance(it, fp.RoomItem))
    assert room.name == "Den"
    assert len(room.walls) == 4            # the room owns its enclosing walls


def test_door_cuts_the_wall(fp, win):
    win.run_macro("WALL 0 0 240 0 ext")
    res = win.run_macro("DOOR 120 0 3680")
    assert res["ok"], res["errors"]
    wall = next(it for it in win.scene.items() if isinstance(it, fp.WallItem))
    assert len(wall.openings) == 1
    assert wall.openings[0].kind == "door"


def test_quoted_room_name_with_space(fp, win):
    macro = ('WALL 0 0 120 0 int WALL 120 0 120 120 int '
             'WALL 120 120 0 120 int WALL 0 120 0 0 int '
             'ROOM "Living Room" 60 60')
    res = win.run_macro(macro)
    assert res["ok"], res["errors"]
    room = next(it for it in win.scene.items() if isinstance(it, fp.RoomItem))
    assert room.name == "Living Room"


def test_select_copy_paste_adds_a_copy(fp, win):
    win.run_macro("PLACE sofa 120 96 0")
    res = win.run_macro("SELECT 120 96  MOVE 240 96  ^C  ^V")
    assert res["ok"], res["errors"]
    assert _counts(win)[2] == 2            # original + pasted copy


def test_select_prefers_furnishing_over_room(fp, win):
    # a room label sits at the anchor; SELECT there must grab the furnishing
    macro = ("WALL 0 0 240 0 ext WALL 240 0 240 180 ext "
             "WALL 240 180 0 180 ext WALL 0 180 0 0 ext "
             "ROOM Den 120 90 PLACE sofa 120 90 0")
    win.run_macro(macro)
    win.run_macro("SELECT 120 90")
    sel = win.scene.selectedItems()
    assert len(sel) == 1
    assert isinstance(sel[0], fp.FurnishingItem)


def test_arrow_nudge_moves_selection(fp, win):
    win.run_macro("PLACE sofa 120 96 0  SELECT 120 96")
    step = fp.SETTINGS["wall_snap_in"]
    win.run_macro("RIGHT")
    furn = next(it for it in win.scene.items()
                if isinstance(it, fp.FurnishingItem))
    assert furn.pos().x() == pytest.approx(120 + step)
    # fine nudge with the caret prefix uses the 1" step
    win.run_macro("^DOWN")
    assert furn.pos().y() == pytest.approx(96 + fp.SNAP_STEP)


def test_rotate_and_delete(fp, win):
    win.run_macro("PLACE sofa 120 96 0  SELECT 120 96  ROTATE 90")
    furn = next(it for it in win.scene.items()
                if isinstance(it, fp.FurnishingItem))
    assert furn.rotation() == pytest.approx(90)
    win.run_macro("SELECT 120 96  DEL")
    assert _counts(win)[2] == 0


def test_tool_code_switches_tool(fp, win):
    win.run_macro("E")                        # Exterior-wall
    assert win.tool == fp.TOOL_WALL_EXT
    win.run_macro("S")                        # Select
    assert win.tool == fp.TOOL_SELECT
    win.run_macro("R")                        # Room
    assert win.tool == fp.TOOL_ROOM


def test_legacy_digit_tool_still_works(fp, win):
    win.run_macro("2")                        # legacy exterior-wall code
    assert win.tool == fp.TOOL_WALL_EXT


def test_drag_draws_a_wall_via_synthesized_mouse(fp, win):
    win.prepare_headless()
    before = _counts(win)[0]
    win.run_macro("E  DRAG 24 24 240 24")     # exterior-wall tool, then drag
    assert _counts(win)[0] == before + 1


def test_combined_click_drag_draws_a_wall(fp, win):
    # CLICK x1 y1 DRAG x2 y2 == one press-drag-release (the DRAG carries only
    # the end point; the CLICK supplies the start)
    win.prepare_headless()
    before = _counts(win)[0]
    win.run_macro("E  CLICK 24 24 DRAG 240 24")
    assert _counts(win)[0] == before + 1


def test_ctrl_click_toggles_selection(fp, win):
    # ^CLICK rides the Ctrl modifier on the synthesized event, so the app
    # treats it as an additive (toggle) click
    win.prepare_headless()
    win.run_macro("PLACE sofa 120 96 0  PLACE armchair 300 96 0")
    win.run_macro("CLICK 120 96  ^CLICK 300 96")
    kinds = sorted(it.kind for it in win.scene.selectedItems()
                   if isinstance(it, fp.FurnishingItem))
    assert kinds == ["armchair", "sofa"]


def test_pup_drives_a_context_menu_action(fp, win):
    # PUP pops the right-click menu and the following nav keys drive it; the
    # furnishing menu's first item is "Rotate 90 CW", so DOWN ENTER rotates
    win.prepare_headless()
    win.run_macro("PLACE armchair 120 96 0")
    furn = next(it for it in win.scene.items()
                if isinstance(it, fp.FurnishingItem))
    res = win.run_macro("PUP 120 96 DOWN ENTER")
    assert res["ok"], res["errors"]
    assert furn.rotation() == pytest.approx(90)


def test_pup_esc_cancels_without_action(fp, win):
    win.prepare_headless()
    win.run_macro("PLACE armchair 120 96 0")
    furn = next(it for it in win.scene.items()
                if isinstance(it, fp.FurnishingItem))
    win.run_macro("PUP 120 96 ESC")               # open then cancel
    assert furn.rotation() == pytest.approx(0)


def _drive_modal(seq):
    """Feed a sequence of Qt keys / text strings to the active menu/dialog,
    one per timer tick so it threads through nested exec() loops."""
    digit = {c: getattr(Qt.Key, f"Key_{c}") for c in "0123456789"}
    q = list(seq)

    def step():
        if not q:
            w = (QApplication.activePopupWidget()
                 or QApplication.activeModalWidget())
            if w is not None:
                w.close()
            return
        item = q.pop(0)
        QTimer.singleShot(12, step)
        t = (QApplication.focusWidget() or QApplication.activePopupWidget()
             or QApplication.activeModalWidget())
        if t is None:
            return
        chars = item if isinstance(item, str) else [item]
        for c in chars:
            key = digit[c] if isinstance(item, str) else item
            txt = c if isinstance(item, str) else ""
            for et in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
                QApplication.sendEvent(t, QKeyEvent(
                    et, key, Qt.KeyboardModifier.NoModifier, txt))
        QApplication.processEvents()

    QTimer.singleShot(0, step)


def _send_context_menu(win, sx, sy):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(sx, sy))
    QApplication.sendEvent(vp, QContextMenuEvent(
        QContextMenuEvent.Reason.Mouse, pos, vp.mapToGlobal(pos)))


def test_pup_type_resizes_a_door(fp, win):
    # navigate the door menu to "Set size", type a new WWHH, accept — no
    # dialog interaction needed beyond the macro tokens
    win.prepare_headless()
    win.run_macro("WALL 0 0 240 0 ext  DOOR 120 0 3680")
    op = next(it for it in win.scene.items()
              if isinstance(it, fp.WallItem)).openings[0]
    res = win.run_macro('PUP 120 0 DOWN DOWN DOWN ENTER TYPE "2868" ENTER')
    assert res["ok"], res["errors"]
    assert op.code == "2868"


def test_recorder_captures_modal_text_on_one_line(fp, win):
    win.prepare_headless()
    win.run_macro("WALL 0 0 240 0 ext  DOOR 120 0 3680")
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    _drive_modal([Qt.Key.Key_Down] * 3
                 + [Qt.Key.Key_Return, "2868", Qt.Key.Key_Return])
    _send_context_menu(win, 120, 0)
    dlg.stop()
    text = dlg.edit.toPlainText().strip()
    assert text.startswith("PUP")
    assert 'TYPE "2868"' in text
    assert "\n" not in text               # the whole interaction on one line


def test_recorder_dedupes_doubled_key_delivery(fp, win):
    # one physical key press can reach the event filter twice (propagation up
    # the parent chain, or a re-dispatched popup/dialog key) with the SAME
    # event object — it must be recorded only once
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Left,
                   Qt.KeyboardModifier.NoModifier)
    dlg.eventFilter(win.view, ev)              # first delivery
    dlg.eventFilter(win, ev)                   # duplicate (same object)
    rel = QKeyEvent(QEvent.Type.KeyRelease, Qt.Key.Key_Left,
                    Qt.KeyboardModifier.NoModifier)
    dlg.eventFilter(win, rel)
    ev2 = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Left,
                    Qt.KeyboardModifier.NoModifier)
    dlg.eventFilter(win.view, ev2)             # a genuine second press
    dlg.stop()
    assert dlg.edit.toPlainText().split() == ["LEFT", "LEFT"]


def test_recorder_tool_dialog_not_double_captured(fp, win):
    # the door-tool click opens a size dialog; that typing must NOT be
    # recorded as modal keys — on_opening already records DOOR x y code
    win.prepare_headless()
    win.run_macro("WALL 0 0 240 0 ext")
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    win.set_tool(fp.TOOL_DOOR)
    _drive_modal(["3680", Qt.Key.Key_Return])
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 120, 0, left, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 120, 0, left,
                Qt.MouseButton.NoButton)
    dlg.stop()
    text = dlg.edit.toPlainText()
    assert "TYPE" not in text             # dialog text not double-captured
    assert "DOOR" in text                 # the on_opening hook recorded it


def test_recorder_captures_popup_and_nav(fp, win):
    win.prepare_headless()
    win.run_macro("PLACE sofa 120 96 0")
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()

    def drive():                                  # navigate the open menu
        for k in (Qt.Key.Key_Down, Qt.Key.Key_Return):
            w = QApplication.activePopupWidget()
            if w is None:
                break
            for et in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
                QApplication.sendEvent(w, QKeyEvent(
                    et, k, Qt.KeyboardModifier.NoModifier))
            QApplication.processEvents()
        w = QApplication.activePopupWidget()
        if w is not None:
            w.close()

    QTimer.singleShot(0, drive)
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(120, 96))
    QApplication.sendEvent(vp, QContextMenuEvent(
        QContextMenuEvent.Reason.Mouse, pos, vp.mapToGlobal(pos)))
    dlg.stop()
    text = dlg.edit.toPlainText()
    assert "PUP" in text
    assert "DOWN" in text and "ENTER" in text


def test_unknown_token_is_recorded_not_fatal(fp, win):
    res = win.run_macro("PLACE sofa 10 10  FLOOGLE  PLACE armchair 50 50")
    assert not res["ok"]
    assert any("FLOOGLE" in e for e in res["errors"])
    assert _counts(win)[2] == 2               # both PLACEs still ran


def test_open_save_roundtrip(fp, win, tmp_path):
    p = tmp_path / "plan.json"
    win.run_macro(f'PLACE sofa 120 96 0  SAVE "{p}"')
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["furnishings"][0]["kind"] == "sofa"
    win.run_macro("NEW")
    assert _counts(win) == (0, 0, 0)
    win.run_macro(f'OPEN "{p}"')
    assert _counts(win)[2] == 1


def test_shot_writes_png_and_svg(fp, win, tmp_path):
    win.run_macro("PLACE sofa 120 96 0")
    png, svg = tmp_path / "s.png", tmp_path / "s.svg"
    res = win.run_macro(f'SHOT "{png}"  SHOT "{svg}"')
    assert res["ok"], res["errors"]
    assert png.exists() and png.stat().st_size > 0
    assert svg.exists() and svg.read_text(encoding="utf-8").startswith("<?xml")


def test_export_canvas_png_dimensions(fp, win, tmp_path):
    from PyQt6.QtGui import QImage
    win.run_macro("WALL 0 0 240 0 ext WALL 240 0 240 120 ext")
    out = tmp_path / "c.png"
    assert win.export_canvas(str(out), scale=2.0)
    img = QImage(str(out))
    assert not img.isNull()
    assert img.width() > 0 and img.height() > 0


def test_scene_summary_has_counts_and_model(fp, win):
    win.run_macro("PLACE sofa 0 0 0  PLACE armchair 60 60 0")
    summ = win.scene_summary()
    assert summ["counts"]["furnishings"] == 2
    assert summ["format"] == "floorplanner-json"
    assert len(summ["furnishings"]) == 2


def test_feet_inches_coordinates(fp, win):
    win.run_macro("PLACE sofa 10' 8' 0")      # 120in x 96in
    furn = next(it for it in win.scene.items()
                if isinstance(it, fp.FurnishingItem))
    assert (furn.pos().x(), furn.pos().y()) == pytest.approx((120, 96))


# --------------------------------------------------------------------------
# Macro recorder dialog
# --------------------------------------------------------------------------
def _send_mouse(win, etype, sx, sy, button, buttons, ctrl=False):
    from PyQt6.QtWidgets import QApplication
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(sx, sy))
    mods = (Qt.KeyboardModifier.ControlModifier if ctrl
            else Qt.KeyboardModifier.NoModifier)
    ev = QMouseEvent(etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)),
                     button, buttons, mods)
    QApplication.sendEvent(vp, ev)


def test_recorder_tool_and_place_hooks(fp, win):
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    win.set_tool(fp.TOOL_WALL_EXT)                 # -> "E"
    dlg.on_place("sofa", QPointF(120, 96))         # -> PLACE sofa 120 96
    dlg.stop()
    text = dlg.edit.toPlainText()
    assert "E" in text.split()
    assert "PLACE sofa 120 96" in text
    assert win._recorder is None                   # stop unhooks the recorder


def test_recorder_ignores_when_not_started_or_paused(fp, win):
    dlg = fp.MacroRecorderDialog(win)
    win.set_tool(fp.TOOL_DOOR)                      # not recording -> nothing
    assert dlg.edit.toPlainText() == ""
    dlg.start()
    dlg.toggle_pause()                             # paused -> still nothing
    win.set_tool(fp.TOOL_WINDOW)
    assert dlg.edit.toPlainText() == ""
    dlg.toggle_pause()                            # resume
    win.set_tool(fp.TOOL_ROOM)                     # -> "R"
    dlg.stop()
    assert dlg.edit.toPlainText().split() == ["R"]


def test_recorder_captures_live_drag(fp, win):
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    win.set_tool(fp.TOOL_WALL_EXT)
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 24, 24, left, left)
    _send_mouse(win, QEvent.Type.MouseMove, 130, 24,
                Qt.MouseButton.NoButton, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 240, 24, left,
                Qt.MouseButton.NoButton)
    dlg.stop()
    text = dlg.edit.toPlainText()
    assert "CLICK" in text and "DRAG" in text       # combined click-drag form


def test_recorder_ctrl_drag_emits_caret_click_drag(fp, win):
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    left, none = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 60, 60, left, left,
                ctrl=True)
    _send_mouse(win, QEvent.Type.MouseMove, 150, 60, none, left, ctrl=True)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 180, 60, left, none,
                ctrl=True)
    dlg.stop()
    text = dlg.edit.toPlainText()
    assert text.startswith("^CLICK")                # Ctrl captured
    assert "DRAG" in text


def test_recorder_ctrl_click_emits_caret_click(fp, win):
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    left, none = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 90, 90, left, left,
                ctrl=True)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 90, 90, left, none,
                ctrl=True)
    dlg.stop()
    text = dlg.edit.toPlainText().strip()
    assert text.startswith("^CLICK")
    assert "DRAG" not in text                        # no movement -> plain click


def test_recorder_short_click_is_click_not_drag(fp, win):
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 60, 60, left, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 60, 60, left,
                Qt.MouseButton.NoButton)
    dlg.stop()
    assert "CLICK" in dlg.edit.toPlainText()
    assert "DRAG" not in dlg.edit.toPlainText()


def test_recorder_replay_rebuilds_scene(fp, win):
    dlg = fp.MacroRecorderDialog(win)
    dlg.edit.setPlainText("PLACE sofa 60 60 0\nPLACE armchair 120 60 0")
    dlg.edit.selectAll()
    dlg.replay()
    for _ in range(len(dlg._replay_lines) + 1):    # drive the step timer
        dlg._replay_step()
    furn = [it for it in win.scene.items()
            if isinstance(it, fp.FurnishingItem)]
    assert len(furn) == 2


def test_recorder_replay_enabled_only_with_selection(fp, win):
    dlg = fp.MacroRecorderDialog(win)
    dlg.edit.setPlainText("PLACE sofa 60 60 0")
    dlg._sync_buttons()
    assert not dlg.b_replay.isEnabled()            # no selection yet
    dlg.edit.selectAll()
    dlg._sync_buttons()
    assert dlg.b_replay.isEnabled()
    assert dlg.b_saveas.isEnabled()                # text present


def test_recorder_save_writes_file(fp, win, tmp_path):
    dlg = fp.MacroRecorderDialog(win)
    dlg.edit.setPlainText("PLACE sofa 60 60 0\nE DRAG 0 0 120 0")
    out = tmp_path / "m.fpm"
    dlg._write_macro(str(out))
    assert out.read_text(encoding="utf-8") == dlg.edit.toPlainText()


def test_recorder_opening_hook_captures_dialog_value(fp, win):
    # door/window sizes come from a dialog, not keystrokes: they must be
    # baked into a self-contained DOOR/WINDOW token so replay needs no dialog
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    dlg.on_opening("door", QPointF(120, 0), "3680")
    dlg.on_opening("window", QPointF(240, 90), "4848")
    dlg.stop()
    text = dlg.edit.toPlainText()
    assert "DOOR 120 0 3680" in text
    assert "WINDOW 240 90 4848" in text


def test_recorder_room_hook_quotes_name(fp, win):
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    dlg.on_room("Living Room", QPointF(120, 90))
    dlg.stop()
    assert 'ROOM "Living Room" 120 90' in dlg.edit.toPlainText()


def test_recorder_suppresses_raw_click_for_dialog_tools(fp, win):
    # with the Door tool active, the raw click is NOT recorded as CLICK —
    # the on_opening hook (with the dialog value) records it instead
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    dlg.start()
    win.set_tool(fp.TOOL_DOOR)
    left = Qt.MouseButton.LeftButton
    _send_mouse(win, QEvent.Type.MouseButtonPress, 120, 0, left, left)
    _send_mouse(win, QEvent.Type.MouseButtonRelease, 120, 0, left,
                Qt.MouseButton.NoButton)
    dlg.stop()
    assert "CLICK" not in dlg.edit.toPlainText()


def test_recorded_opening_replays_without_dialog(fp, win):
    # a captured DOOR token replays purely via run_macro (no dialog)
    win.run_macro("WALL 0 0 240 0 ext")
    dlg = fp.MacroRecorderDialog(win)
    dlg.edit.setPlainText("DOOR 120 0 3680")
    dlg.edit.selectAll()
    dlg.replay()
    for _ in range(len(dlg._replay_lines) + 1):
        dlg._replay_step()
    wall = next(it for it in win.scene.items() if isinstance(it, fp.WallItem))
    assert len(wall.openings) == 1
    assert wall.openings[0].kind == "door"
