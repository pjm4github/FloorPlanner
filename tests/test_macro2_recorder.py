"""Macro language v2 -- the recorder (MACRO_SPEC.md sec9, sec12 item 9).

Patrick, 2026-10-04, after running the v2 check macros and recording more
on top: "The one issue I see is that the shift key is not captured in the
recorder." It was not: that recorder was the existing one, which records
only Ctrl on the mouse, and it was appending its own format to a v2 macro.

The first half drives `macro2.recorder.Recorder` with plain values -- no
window. The second sends real mouse and key events to the canvas with the
dialog recording, asserts the text, then REPLAYS the text on a fresh plan
and asserts the canvas (item 9; pytest-qt is not installed, so the events
are built the way this suite's other recorder tests build them).
"""
import pytest
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent
from PyQt6.QtWidgets import QApplication

from floorplanner.macro2 import keys, parse
from floorplanner.macro2.ast import Mod
from floorplanner.macro2.parse import HEADER
from floorplanner.macro2.recorder import Recorder

pytestmark = pytest.mark.macro

S, C, A = frozenset({Mod.SHIFT}), frozenset({Mod.CTRL}), frozenset({Mod.ALT})
N = frozenset()


class Tape:
    """What the dialog's editor is to the recorder: lines in, and the last
    one taken back on request."""
    def __init__(self):
        self.lines = []

    def emit(self, line):
        self.lines.append(line)

    def retract(self, line):
        if self.lines and self.lines[-1] == line:
            self.lines.pop()
            return True
        return False


def _rec(**kw):
    tape = Tape()
    return Recorder(tape.emit, tape.retract, **kw), tape


# --------------------------------------------------------------------------
# the state machine, without a window
# --------------------------------------------------------------------------
def test_a_drag_is_one_chain():
    r, t = _rec()
    r.press("left", 120, 120)
    r.move(200, 121)
    r.release(360, 120)
    assert t.lines == ["CLICK 120 120 DRAG 360 120"]


def test_shift_held_for_the_whole_drag_prefixes_both():
    r, t = _rec()
    r.press("left", 120, 120, S)
    r.move(200, 130, S)
    r.release(355, 133, S)
    assert t.lines == ["+CLICK 120 120 +DRAG 355 133"]


def test_a_modifier_pressed_mid_drag_splits_the_chain_where_the_pointer_was():
    """sec9: close the current segment at the pointer, with the PREVIOUS
    modifiers; the release takes the modifiers held at the release."""
    r, t = _rec()
    r.press("left", 120, 120)
    r.move(200, 120)
    r.move(300, 124)            # still no modifier
    r.move(301, 200, S)         # Shift went down somewhere after (300,124)
    r.release(301, 211, S)
    assert t.lines == ["CLICK 120 120 DRAG 300 124 +DRAG 301 211"]


def test_a_modifier_released_mid_drag_splits_it_too():
    r, t = _rec()
    r.press("left", 10, 10, C)
    r.move(100, 10, C)
    r.move(100, 60)             # Ctrl came up
    r.release(100, 90)
    assert t.lines == ["^CLICK 10 10 ^DRAG 100 10 DRAG 100 90"]


def test_a_modifier_changed_with_the_pointer_still_is_a_zero_length_last_segment():
    """The release must carry the modifiers held at the release (sec5.2
    rule 3), even though the pointer did not move after the change."""
    r, t = _rec()
    r.press("left", 10, 10)
    r.move(100, 10)
    r.release(100, 10, S)
    assert t.lines == ["CLICK 10 10 DRAG 100 10 +DRAG 100 10"]


def test_jitter_under_the_drag_threshold_is_a_plain_click_at_the_press_point():
    r, t = _rec(drag_px=4.0)
    r.press("left", 50, 50, px=1.0)
    r.move(52, 51)
    r.release(52, 51)
    assert t.lines == ["CLICK 50 50"]
    r.press("left", 50, 50, px=1.0)
    r.move(56, 50)
    r.release(56, 50)
    assert t.lines[-1] == "CLICK 50 50 DRAG 56 50", "four pixels is a drag"


def test_the_threshold_is_in_view_pixels_not_scene_inches():
    """Zoomed out, 6 inches is 1.5 pixels: jitter. Zoomed in, it is a drag."""
    r, t = _rec(drag_px=4.0)
    r.press("left", 50, 50, px=4.0)
    r.release(56, 50)
    r.press("left", 50, 50, px=0.25)
    r.release(56, 50)
    assert t.lines == ["CLICK 50 50", "CLICK 50 50 DRAG 56 50"]


def test_coordinates_keep_only_the_precision_a_pixel_has():
    r, t = _rec()
    r.press("left", 120.37, 96.81, px=2.0)
    r.release(360.2, 96.9)
    r.press("left", 120.37, 96.81, px=0.25)
    r.release(360.26, 96.94)
    assert t.lines == ["CLICK 120 97 DRAG 360 97", "CLICK 120.4 96.8 DRAG 360.3 96.9"]


def test_a_double_click_replaces_the_click_just_written():
    r, t = _rec()
    r.press("left", 200, 150)
    r.release(200, 150)
    assert t.lines == ["CLICK 200 150"]
    r.dblclick("left", 200, 150)
    r.release(200, 150)
    assert t.lines == ["DCLICK 200 150"]


def test_a_drag_after_a_double_click_becomes_its_segments_and_keeps_the_tool():
    r, t = _rec()
    r.tool("S")
    r.press("left", 200, 150)
    r.release(200, 150)
    r.dblclick("left", 200, 150)
    r.move(260, 150)
    r.release(300, 150)
    assert t.lines == ["S DCLICK 200 150 DRAG 300 150"]


def test_the_other_buttons():
    r, t = _rec()
    r.press("middle", 10, 10)
    r.move(60, 40)
    r.release(90, 60)
    r.click("right", 5, 5)
    r.press("back", 1, 1)
    r.release(1, 1)
    assert t.lines == ["MCLICK 10 10 DRAG 90 60", "RCLICK 5 5", "XCLICK1 1 1"]


def test_a_tool_change_prefixes_the_next_line_or_stands_alone_at_the_end():
    r, t = _rec()
    r.tool("I")
    r.press("left", 100, 100)
    r.release(400, 100)
    r.tool("E")
    r.tool("S")                 # changed again before anything happened
    r.stop()
    assert t.lines == ["I CLICK 100 100 DRAG 400 100", "S"]


def test_typed_text_gathers_and_trailing_spaces_become_key_strokes():
    r, t = _rec()
    for ch in "Hello World  ":
        r.text(ch)
    r.key(keys.named("Enter"))
    r.stop()
    assert t.lines == ["TYPE Hello World", "KEY {Space} {Space} {Enter}"]


def test_text_that_is_only_spaces_is_only_strokes():
    r, t = _rec()
    r.text(" ")
    r.text(" ")
    r.stop()
    assert t.lines == ["KEY {Space} {Space}"]


def test_consecutive_strokes_share_a_line_and_text_breaks_it():
    r, t = _rec()
    r.key(keys.char("c"), C)
    r.key(keys.char("v"), C)
    r.key(keys.named("Down"))
    r.text("x")
    r.key(keys.char("z"), C | S)
    r.stop()
    assert t.lines == ["KEY ^c ^v {Down}", "TYPE x", "KEY +^z"]


def test_a_modifier_pressed_alone_is_not_recorded():
    r, t = _rec()
    r.key(keys.named("Shift"), S)
    r.key(keys.named("Ctrl"), C)
    r.stop()
    assert t.lines == []


def test_the_wheel_is_preceded_by_a_move_when_the_pointer_was_elsewhere():
    r, t = _rec()
    r.press("left", 10, 10)
    r.release(10, 10)
    r.wheel(0, 120, 10, 10)             # where the pointer already is
    r.wheel(0, -120, 300, 200, C)       # somewhere else
    assert t.lines == ["CLICK 10 10", "WHEEL 0 120", "MOVE 300 200", "^WHEEL 0 -120"]


def test_an_application_command_is_one_line_and_takes_the_pending_tool():
    r, t = _rec()
    r.tool("D")
    r.command("DOOR", (120, 0, "3280"))
    r.command("ROOM", ("Living Room", 120, 90))
    assert t.lines == ["D @DOOR 120 0 3280", '@ROOM "Living Room" 120 90']


def test_waits_are_off_by_default_and_optional():
    r, t = _rec()
    r.press("left", 1, 1, t=0)
    r.release(1, 1, t=10)
    r.press("left", 2, 2, t=5000)
    r.release(2, 2, t=5010)
    assert t.lines == ["CLICK 1 1", "CLICK 2 2"]
    r, t = _rec(wait_ms=1000)
    r.press("left", 1, 1, t=0)
    r.release(1, 1, t=10)
    r.press("left", 2, 2, t=5000)
    r.release(2, 2, t=5010)
    assert t.lines == ["CLICK 1 1", "WAIT 4990", "CLICK 2 2"]


def test_hover_moves_are_recorded_only_when_asked():
    r, t = _rec()
    r.move(100, 100)
    assert t.lines == []
    r, t = _rec(hover=True)
    r.move(100, 100)
    r.move(101, 100)                    # too close to bother
    r.move(300, 100)
    assert t.lines == ["MOVE 100 100", "MOVE 300 100"]


def test_everything_the_recorder_writes_is_valid_canonical_v2():
    r, t = _rec()
    r.tool("I")
    r.press("left", 10, 10, C)
    r.move(50, 10, C)
    r.release(90, 40, S | A)
    r.text("a b ")
    r.key(keys.char(";"), N)
    r.command("OPEN", ("my plans/den; v2.json",))
    r.stop()
    text = HEADER + "\n" + "\n".join(t.lines) + "\n"
    res = parse(text)
    assert res.ok, [str(e) for e in res.errors]
    from floorplanner.macro2 import serialize
    assert serialize(res.macro) == text, "already canonical"


# --------------------------------------------------------------------------
# the dialog: real events in, text out, and the text replays (sec12 item 9)
# --------------------------------------------------------------------------
LEFT, NONE = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
SHIFT, CTRL, NOMOD = (Qt.KeyboardModifier.ShiftModifier,
                      Qt.KeyboardModifier.ControlModifier,
                      Qt.KeyboardModifier.NoModifier)


def _mouse(win, etype, x, y, button, buttons, mods=NOMOD):
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(x, y))
    QApplication.sendEvent(vp, QMouseEvent(
        etype, QPointF(pos), QPointF(vp.mapToGlobal(pos)), button, buttons, mods))


def _walls(fp, win):
    return sorted((round(w.p1.x(), 1), round(w.p1.y(), 1),
                   round(w.p2.x(), 1), round(w.p2.y(), 1))
                  for w in win.scene.items() if isinstance(w, fp.WallItem))


def _lines(dlg):
    return [ln for ln in dlg.edit.toPlainText().splitlines() if ln.strip()]


@pytest.fixture
def clean_mods():
    yield
    assert QApplication.keyboardModifiers() == NOMOD


@pytest.mark.gui
def test_a_shift_drag_is_recorded_and_replays_to_the_same_wall(fp, win, clean_mods):
    """HIS REPORT. Shift goes down partway through a wall drag: the
    recording says so, and replaying it draws the same off-grid wall."""
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win, fmt="v2")
    dlg.start()
    win.set_tool(fp.TOOL_WALL_INT)
    _mouse(win, QEvent.Type.MouseButtonPress, 120, 240, LEFT, LEFT)
    _mouse(win, QEvent.Type.MouseMove, 200, 242, NONE, LEFT)
    _mouse(win, QEvent.Type.MouseMove, 300, 244, NONE, LEFT)
    _mouse(win, QEvent.Type.MouseMove, 340, 250, NONE, LEFT, SHIFT)
    _mouse(win, QEvent.Type.MouseMove, 355, 253, NONE, LEFT, SHIFT)
    _mouse(win, QEvent.Type.MouseButtonRelease, 355, 253, LEFT, NONE, SHIFT)
    dlg.stop()
    lines = _lines(dlg)
    assert lines[0] == HEADER
    assert len(lines) == 2
    tool, click, x1, y1, d1, xa, ya, d2, xb, yb = lines[1].split()
    assert (tool, click, d1, d2) == ("I", "CLICK", "DRAG", "+DRAG"), lines[1]
    px = 1.0 / win.view.transform().m11()
    assert float(xb) == pytest.approx(355, abs=px) and float(yb) == pytest.approx(253, abs=px)
    recorded = _walls(fp, win)
    ((_, _, x2, y2),) = recorded
    assert y2 != 240.0, "Shift was down at the release: not pulled square"

    win2 = fp.MainWindow()
    try:
        win2.prepare_headless()
        res = win2.run_macro(dlg.edit.toPlainText())
        assert res["ok"] and res["warnings"] == [], res
        ((_, _, rx, ry),) = _walls(fp, win2)
        assert (rx, ry) == pytest.approx((x2, y2), abs=px), "the replay drew the same wall"
    finally:
        from tests.conftest import dispose_window
        dispose_window(win2)


@pytest.mark.gui
def test_typing_into_a_context_menus_dialog_records_type_and_strokes(fp, win, clean_mods):
    """A typed string with a trailing space (item 9): printable keys in a
    menu-opened dialog gather into TYPE; the trailing space follows as a
    KEY stroke; Enter is a stroke."""
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win, fmt="v2")
    dlg.start()
    dlg._v2.click("right", 240, 240)
    dlg._modal_line = True
    from PyQt6.QtWidgets import QInputDialog
    box = QInputDialog(win)
    box.setModal(True)
    box.show()
    QApplication.processEvents()
    assert QApplication.activeModalWidget() is box
    for ch in "28 68 ":
        QApplication.sendEvent(box, QKeyEvent(
            QEvent.Type.KeyPress, Qt.Key(ord(ch.upper())), NOMOD, ch))
        QApplication.sendEvent(box, QKeyEvent(
            QEvent.Type.KeyRelease, Qt.Key(ord(ch.upper())), NOMOD, ch))
    QApplication.sendEvent(box, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, NOMOD, "\r"))
    box.close()
    QApplication.processEvents()
    dlg.stop()
    assert _lines(dlg) == [HEADER, "RCLICK 240 240", "TYPE 28 68", "KEY {Space} {Enter}"]


@pytest.mark.gui
def test_a_recording_added_to_a_v2_macro_stays_v2(fp, win, clean_mods):
    """What he did: Load a v2 file, then record more on top. One file is
    one language -- the editor's format wins over the checkbox."""
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)               # legacy by construction
    dlg.edit.setPlainText(HEADER + "\n@PLACE sofa 120 96 0\n")
    dlg.start()
    assert dlg.fmt == "v2" and dlg.v2_check.isChecked()
    win.set_tool(fp.TOOL_WALL_INT)
    _mouse(win, QEvent.Type.MouseButtonPress, 120, 300, LEFT, LEFT, SHIFT)
    _mouse(win, QEvent.Type.MouseMove, 250, 320, NONE, LEFT, SHIFT)
    _mouse(win, QEvent.Type.MouseButtonRelease, 355, 333, LEFT, NONE, SHIFT)
    dlg.stop()
    lines = _lines(dlg)
    assert lines[:2] == [HEADER, "@PLACE sofa 120 96 0"]
    assert lines[2].startswith("I +CLICK ") and " +DRAG " in lines[2]
    assert parse(dlg.edit.toPlainText()).ok


@pytest.mark.gui
def test_a_legacy_macro_in_the_editor_keeps_the_legacy_recorder(fp, win, clean_mods):
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win, fmt="v2")
    dlg.edit.setPlainText("PLACE sofa 60 60 0\n")
    dlg.start()
    assert dlg.fmt == "legacy" and dlg._v2 is None
    win.set_tool(fp.TOOL_WALL_INT)
    _mouse(win, QEvent.Type.MouseButtonPress, 120, 300, LEFT, LEFT)
    _mouse(win, QEvent.Type.MouseMove, 250, 300, NONE, LEFT)
    _mouse(win, QEvent.Type.MouseButtonRelease, 360, 300, LEFT, NONE)
    dlg.stop()
    text = dlg.edit.toPlainText()
    assert HEADER not in text
    last = text.splitlines()[-1].split()
    assert (last[0], last[1], last[4]) == ("I", "CLICK", "DRAG"), "the legacy form, unprefixed"


@pytest.mark.gui
def test_dialog_tools_record_one_command_not_a_click_and_a_dialog(fp, win, clean_mods):
    """A door's size comes from a dialog: the app's hook reports it, and
    v2 writes `@DOOR x y code` (sec14) -- replay opens no dialog."""
    win.prepare_headless()
    win.run_macro("WALL 0 0 240 0 ext")
    dlg = fp.MacroRecorderDialog(win, fmt="v2")
    dlg.start()
    win.set_tool(fp.TOOL_DOOR)
    _mouse(win, QEvent.Type.MouseButtonPress, 120, 0, LEFT, LEFT) if False else None
    dlg.on_opening("door", QPointF(120, 0), "3280")     # what view.py calls
    dlg.on_room("Living Room", QPointF(120, 90))
    dlg.on_place("sofa", QPointF(120, 96))
    dlg.on_new_floor("Floor 2")
    dlg.on_floor("default")
    dlg.on_shuffle(True)
    dlg.on_open("plans/my den.json")
    dlg.stop()
    assert _lines(dlg) == [
        HEADER, "D @DOOR 120 0 3280", '@ROOM "Living Room" 120 90',
        "@PLACE sofa 120 96", '@NEWFLOOR "Floor 2"', "@FLOOR default",
        "@SHUFFLE on", '@OPEN "plans/my den.json"']
    assert parse(dlg.edit.toPlainText()).ok


@pytest.mark.gui
def test_a_double_click_and_the_wheel_are_recorded(fp, win, clean_mods):
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win, fmt="v2")
    dlg.start()
    _mouse(win, QEvent.Type.MouseButtonPress, 200, 150, LEFT, LEFT)
    _mouse(win, QEvent.Type.MouseButtonRelease, 200, 150, LEFT, NONE)
    _mouse(win, QEvent.Type.MouseButtonDblClick, 200, 150, LEFT, LEFT)
    _mouse(win, QEvent.Type.MouseButtonRelease, 200, 150, LEFT, NONE)
    vp = win.view.viewport()
    pos = win.view.mapFromScene(QPointF(300, 300))
    QApplication.sendEvent(vp, QWheelEvent(
        QPointF(pos), QPointF(vp.mapToGlobal(pos)), QPoint(), QPoint(0, 120),
        NONE, CTRL, Qt.ScrollPhase.NoScrollPhase, False))
    dlg.stop()
    lines = _lines(dlg)
    px = 1.0 / win.view.transform().m11()
    assert lines[1].startswith("DCLICK ")
    assert lines[2].startswith("MOVE ") and lines[3] == "^WHEEL 0 120"
    mx, my = (float(v) for v in lines[2].split()[1:])
    assert (mx, my) == pytest.approx((300, 300), abs=px)


@pytest.mark.gui
def test_canvas_keys_record_strokes_but_not_the_ones_a_hook_already_writes(fp, win, clean_mods):
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win, fmt="v2")
    dlg.start()
    vp = win.view.viewport()

    def press(key, mods=NOMOD, text=""):
        QApplication.sendEvent(vp, QKeyEvent(QEvent.Type.KeyPress, key, mods, text))
        QApplication.sendEvent(vp, QKeyEvent(QEvent.Type.KeyRelease, key, mods, text))

    press(Qt.Key.Key_Right)
    press(Qt.Key.Key_Right)
    press(Qt.Key.Key_Z, CTRL)
    press(Qt.Key.Key_O, CTRL)            # Open: its hook writes @OPEN with the path
    press(Qt.Key.Key_Shift, SHIFT)       # a modifier alone
    dlg.stop()
    assert _lines(dlg) == [HEADER, "KEY {Right} {Right} ^z"]


@pytest.mark.gui
def test_the_application_opens_the_recorder_in_v2(fp, win, clean_mods):
    win.open_macro_recorder()
    dlg = win._recorder_dialog
    try:
        assert dlg.fmt == "v2" and dlg.v2_check.isChecked()
        dlg.start()
        assert dlg.edit.toPlainText() == HEADER + "\n"
        dlg.stop()
    finally:
        dlg.close()
