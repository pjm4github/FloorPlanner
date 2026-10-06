"""Macro language v2, tranche T2 -- the player (MACRO_SPEC.md sec8).

T1 (`test_macro2_language.py`) stops at the abstract event list. These run
v2 macros through `MainWindow.run_macro` into a real (offscreen) window and
assert what the canvas holds afterwards.

The receipt this work was started for is the Shift-drag: report 0210 could
not reproduce Patrick's grid-snap fault from a recorded macro because the
existing language cannot hold Shift during a drag.

And the guard (0212-report.md sec3, his ruling: "follow the spec, guard the
leak"): after EVERY macro here -- clean, invalid or aborted --
`QApplication.keyboardModifiers()` is none. An autouse fixture asserts it.
"""
import pytest
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtWidgets import QApplication

from floorplanner.macro2 import sink as sink_mod
from floorplanner.macro2.parse import HEADER
from floorplanner.macro2.player import Player

pytestmark = [pytest.mark.macro, pytest.mark.gui]

NO_MODS = Qt.KeyboardModifier.NoModifier


@pytest.fixture(autouse=True)
def _modifiers_are_clean_afterwards():
    assert QApplication.keyboardModifiers() == NO_MODS, "a previous test leaked"
    yield
    assert QApplication.keyboardModifiers() == NO_MODS, \
        "the macro left a modifier down in Qt's global state"


def _run(win, body, prepare=True):
    if prepare:
        win.prepare_headless()
    return win.run_macro(HEADER + "\n" + body)


def _walls(fp, win):
    return sorted((round(w.p1.x(), 1), round(w.p1.y(), 1),
                   round(w.p2.x(), 1), round(w.p2.y(), 1))
                  for w in win.scene.items() if isinstance(w, fp.WallItem))


# --------------------------------------------------------------------------
# the engine is chosen by the first line
# --------------------------------------------------------------------------
def test_a_v2_macro_draws_walls_through_run_macro(fp, win):
    res = _run(win, "I CLICK 120 120 DRAG 360 120\nI CLICK 360 120 DRAG 360 300\nS")
    assert res["ok"], res
    assert res["steps"] == 3 and res["errors"] == []
    assert _walls(fp, win) == [(120.0, 120.0, 360.0, 120.0), (360.0, 120.0, 360.0, 300.0)]
    assert win.tool == fp.TOOL_SELECT, "the bare `S` line selected the tool"
    assert res["counts"]["walls"] == 2, "the same result dict run_macro always returned"


def test_a_macro_without_the_header_still_runs_on_the_existing_engine(fp, win):
    """Side by side (his ruling): the same words mean what they always did."""
    win.prepare_headless()
    res = win.run_macro("I CLICK 120 120 DRAG 360 120  S ^Z")   # two commands, one line
    assert res["ok"], res
    assert _walls(fp, win) == [], "legacy `^Z` undid the wall"
    res = win.run_macro("WALL 0 0 240 0 ext\nPLACE sofa 120 96 0   # a legacy comment")
    assert res["ok"] and res["counts"] == {"walls": 1, "rooms": 0, "furnishings": 1}


def test_the_legacy_words_are_errors_in_v2_and_the_lines_before_run(fp, win):
    """sec8.3 as amended (Patrick, 2026-10-06: "play as many lines as
    possible and stop on the error line"): the wall on line 2 is drawn; the
    bad line 3 and what follows are not."""
    res = _run(win, "I CLICK 120 120 DRAG 360 120\nWALL 0 0 240 0 ext\n@WALL 0 0 100 0")
    assert not res["ok"] and res["steps"] == 1            # line 2 alone
    assert all(e.startswith("line 3:") for e in res["errors"]), res["errors"]
    assert _walls(fp, win) == [(120.0, 120.0, 360.0, 120.0)]


def test_every_error_is_reported_and_nothing_from_the_first_bad_line_runs(fp, win):
    res = _run(win, "@WALL 0 0 240 0\nQ CLICK 1 1\n@WALL 0 60 240 60\nKEY {Nope}\n@WALL 0 120 240 120")
    assert [e.split()[1] for e in res["errors"]] == ["3:0", "5:4"]
    assert res["counts"]["walls"] == 1 and res["steps"] == 1


def test_an_error_on_the_first_command_line_runs_nothing(fp, win):
    res = _run(win, "Q CLICK 1 1\n@WALL 0 0 240 0")
    assert not res["ok"] and res["steps"] == 0 and res["counts"]["walls"] == 0
    assert res["errors"] == ["line 2:0 unknown tool letter 'Q'"]


# --------------------------------------------------------------------------
# the Shift-drag -- what the existing language could not say
# --------------------------------------------------------------------------
def test_a_shift_drag_lands_off_the_grid(fp, win):
    """`+DRAG`: Shift held for the segment, so the wall end follows the
    cursor -- unconstrained, off the 6in grid (A6, 0208). The same drag
    without Shift lands on the grid, square to its start."""
    res = _run(win, "I CLICK 120 120 +DRAG 355 133")
    assert res["ok"], res
    ((x1, y1, x2, y2),) = _walls(fp, win)
    px = 1.0 / win.view.transform().m11()            # one pixel, in inches
    assert (x1, y1) == (120.0, 120.0)
    assert x2 == pytest.approx(355.0, abs=px) and y2 == pytest.approx(133.0, abs=px)
    assert y2 != 120.0, "not pulled square"

    win2 = fp.MainWindow()
    try:
        res = _run(win2, "I CLICK 120 120 DRAG 355 133")
        assert _walls(fp, win2) == [(120.0, 120.0, 354.0, 120.0)]
    finally:
        from tests.conftest import dispose_window
        dispose_window(win2)


def test_the_modifier_changes_partway_through_a_chain(fp, win):
    """`CLICK a DRAG b +DRAG c`: one press, one release; the first segment
    is constrained and the second is not. The wall ends where the LAST
    segment ends, placed by the rule in force when the button came up."""
    res = _run(win, "I CLICK 120 120 DRAG 300 124 +DRAG 301 211")
    assert res["ok"], res
    ((x1, y1, x2, y2),) = _walls(fp, win)
    px = 1.0 / win.view.transform().m11()
    assert (x1, y1) == (120.0, 120.0)
    assert x2 == pytest.approx(301.0, abs=px) and y2 == pytest.approx(211.0, abs=px)


def test_a_held_shift_does_what_a_shift_prefix_does(fp, win):
    res = _run(win, "KEYDOWN {Shift}\nI CLICK 120 120 DRAG 355 133\nKEYUP {Shift}")
    assert res["ok"] and res["warnings"] == [], res
    ((_, _, x2, y2),) = _walls(fp, win)
    px = 1.0 / win.view.transform().m11()
    assert x2 == pytest.approx(355.0, abs=px) and y2 == pytest.approx(133.0, abs=px)


def test_a_drag_is_many_small_moves_not_one_jump(fp, win, monkeypatch):
    """sec8.5: at most `step_px` view pixels a move, and at least two."""
    seen = []
    real = sink_mod.QtEventSink.move_px

    def spy(self, p, mods):
        seen.append((p.x(), p.y()))
        return real(self, p, mods)

    monkeypatch.setattr(sink_mod.QtEventSink, "move_px", spy)
    res = _run(win, "I CLICK 120 120 DRAG 360 120\nI CLICK 400 400 DRAG 401 400")
    assert res["ok"]
    long_drag = [p for p in seen if p[1] == seen[0][1]]
    steps = [abs(b[0] - a[0]) for a, b in zip(long_drag, long_drag[1:], strict=False)]
    assert len(long_drag) > 10 and max(steps) <= 8
    assert len(seen) - len(long_drag) == 2, "a one-inch drag is still two moves"


# --------------------------------------------------------------------------
# keys: shortcuts, the canvas, dialogs
# --------------------------------------------------------------------------
def test_ctrl_z_undoes_straight_after_a_drag(fp, win):
    """A key press sent with sendEvent never reaches a QAction's shortcut;
    the sink resolves the stroke to the window's own Undo action -- and
    settles the gesture first, as the app's 180 ms timer would have."""
    res = _run(win, "I CLICK 120 120 DRAG 360 120\nKEY ^z")
    assert res["ok"], res
    assert _walls(fp, win) == []
    res = _run(win, "KEY ^y", prepare=False)
    assert _walls(fp, win) == [(120.0, 120.0, 360.0, 120.0)], "and Ctrl+Y redoes"


def test_a_key_the_window_has_no_shortcut_for_reaches_the_canvas(fp, win):
    """Arrows are the canvas's own (`PlanView.keyPressEvent`): a selected
    furnishing is nudged one snap step."""
    win.prepare_headless()
    win.run_macro("PLACE sofa 240 240 0\nSELECT 240 240")
    sofa = next(it for it in win.scene.items() if isinstance(it, fp.FurnishingItem))
    x0 = sofa.pos().x()
    res = _run(win, "KEY {Right} {Right}", prepare=False)
    assert res["ok"], res
    assert sofa.pos().x() == pytest.approx(x0 + 2 * fp.SETTINGS["wall_snap_in"])


def test_a_door_is_placed_by_driving_its_size_dialog(fp, win):
    """The click opens a modal size prompt and does not return until it
    closes. The pump delivers `TYPE` and `KEY {Enter}` inside that dialog's
    own event loop -- the reason delivery is timer-driven."""
    res = _run(win, "I CLICK 120 120 DRAG 360 120\nD CLICK 240 120\nTYPE 2868\nKEY {Enter}")
    assert res["ok"], res
    (wall,) = [w for w in win.scene.items() if isinstance(w, fp.WallItem)]
    (door,) = wall.openings
    assert (door.kind, door.code) == ("door", "2868")
    assert res["warnings"] == [], "the dialog was answered, not left open"


def test_a_dialog_left_open_is_closed_and_reported(fp, win):
    res = _run(win, "I CLICK 120 120 DRAG 360 120\nD CLICK 240 120")
    assert res["ok"]
    assert any("still open" in w for w in res["warnings"]), res["warnings"]
    assert QApplication.activeModalWidget() is None
    (wall,) = [w for w in win.scene.items() if isinstance(w, fp.WallItem)]
    assert wall.openings == [], "cancelled: no door"


def test_a_right_click_opens_the_context_menu_and_keys_drive_it(fp, win):
    """`RCLICK` is followed by the context-menu event the platform sends for
    a real right click; the menu then takes the keys."""
    win.prepare_headless()
    win.run_macro("PLACE sofa 240 240 0")
    sofa = next(it for it in win.scene.items() if isinstance(it, fp.FurnishingItem))
    r0 = sofa.rotation()
    res = _run(win, "RCLICK 240 240\nKEY {Down} {Enter}", prepare=False)
    assert res["ok"] and res["warnings"] == [], res
    assert sofa.rotation() != r0, "the first menu entry rotated it"


def test_the_wheel_zooms_at_the_pointer(fp, win):
    win.prepare_headless()
    s0 = win.view.transform().m11()
    res = _run(win, "MOVE 300 300\nWHEEL 0 120\nWAIT 80", prepare=False)
    assert res["ok"]
    assert win.view.transform().m11() > s0, "one notch in"


def test_the_specs_own_example_runs(fp, win):
    """MACRO_SPEC.md sec13, verbatim."""
    res = _run(win, "\n".join([
        "; Draw two walls, select one, label it",
        "I CLICK 100 100 DRAG 400 100",
        "I CLICK 400 100 +DRAG 400 300",
        "S +CLICK 250 100",
        "DCLICK 200 150",
        "TYPE Hello World",
        "KEY {Enter}",
        "KEYDOWN {Space}",
        "CLICK 300 300 DRAG 500 400",
        "KEYUP {Space}"]))
    assert res["ok"] and res["errors"] == [], res
    assert res["steps"] == 9


# --------------------------------------------------------------------------
# the guard
# --------------------------------------------------------------------------
def test_the_global_modifier_state_follows_the_macro_and_ends_clean(fp, win, monkeypatch):
    """sec7 wants widgets that read `keyboardModifiers()` to agree with the
    events. Seen from inside the app while the macro runs: Shift during a
    `+DRAG`, Ctrl during `KEY ^z`'s action."""
    seen = {}
    real_set_ridge = fp.WallItem.set_end_vertex

    def spy(self, *a, **kw):
        seen.setdefault("during_drag", QApplication.keyboardModifiers())
        return real_set_ridge(self, *a, **kw)

    monkeypatch.setattr(fp.WallItem, "set_end_vertex", spy)
    win.prepare_headless()
    win.a_undo.triggered.connect(
        lambda: seen.setdefault("during_undo", QApplication.keyboardModifiers()))
    res = _run(win, "I CLICK 120 120 +DRAG 355 133\nKEY ^z", prepare=False)
    assert res["ok"], res
    assert seen["during_drag"] == Qt.KeyboardModifier.ShiftModifier
    assert seen["during_undo"] == Qt.KeyboardModifier.ControlModifier
    assert QApplication.keyboardModifiers() == NO_MODS


def test_an_aborted_macro_releases_everything(fp, win, monkeypatch):
    """A failure mid-chain, Shift and a key held: the error is reported
    with its line, the rest does not run, and nothing is left down."""
    real = sink_mod.QtEventSink.move_px
    calls = {"n": 0}

    def boom(self, p, mods):
        calls["n"] += 1
        if calls["n"] == 3:
            raise RuntimeError("the canvas went away")
        return real(self, p, mods)

    monkeypatch.setattr(sink_mod.QtEventSink, "move_px", boom)
    res = _run(win, "KEYDOWN {Ctrl}\nI CLICK 120 120 +DRAG 360 200\nI CLICK 0 0 DRAG 60 0")
    assert not res["ok"]
    assert res["errors"] == ["line 3: RuntimeError: the canvas went away"]
    assert calls["n"] == 3, "nothing was delivered after the failure"
    assert QApplication.keyboardModifiers() == NO_MODS


def test_an_unreleased_key_is_released_and_reported(fp, win):
    res = _run(win, "KEYDOWN {Shift}\nI CLICK 120 120 DRAG 355 133")
    assert res["ok"]
    assert len(res["warnings"]) == 1 and "{Shift}" in res["warnings"][0]


def test_the_player_can_be_paced(fp, win):
    win.prepare_headless()
    p = Player(win, step_px=40.0, delay_ms=1)
    res = p.run(HEADER + "\nI CLICK 120 120 DRAG 360 120")
    assert res["ok"] and _walls(fp, win) == [(120.0, 120.0, 360.0, 120.0)]


# --------------------------------------------------------------------------
# the recorder dialog replays a v2 macro as ONE macro
# --------------------------------------------------------------------------
def test_the_dialog_replays_a_v2_selection_whole(fp, win):
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    dlg.edit.setPlainText(HEADER + "\nKEYDOWN {Shift}\nI CLICK 120 120 DRAG 355 133\nKEYUP {Shift}\n")
    dlg.edit.selectAll()
    dlg.replay()
    assert len(dlg._replay_lines) == 1, "one macro, not four independent lines"
    for _ in range(2):
        dlg._replay_step()
    ((_, _, x2, y2),) = _walls(fp, win)
    assert y2 != 120.0, "the KEYDOWN on one line held through the next"
    # a selection INSIDE a v2 macro is still v2: the header is put back
    cur = dlg.edit.textCursor()
    cur.setPosition(dlg.edit.toPlainText().index("I CLICK"))
    cur.movePosition(cur.MoveOperation.EndOfLine, cur.MoveMode.KeepAnchor)
    dlg.edit.setTextCursor(cur)
    dlg.replay()
    assert dlg._replay_lines[0].startswith(HEADER + "\nI CLICK")
    dlg._replay_timer.stop()


@pytest.mark.parametrize("anchor, pos, want", [
    ("CLICK 120 120", "+DRAG 355", "top down, mid-line to mid-line"),
    ("+DRAG 355", "CLICK 120 120", "bottom up: the same two lines"),
    ("DRAG 355 253", "I CLICK 120 120", "bottom up, to the start of the top line"),
])
def test_the_dialog_replays_whole_lines_top_down_however_they_were_selected(
        fp, win, anchor, pos, want):
    """Patrick, 2026-10-05: lines selected from the bottom up did not replay
    correctly. Every line the selection touches is replayed whole, in the
    order it is written, whichever end the drag began at."""
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    text = HEADER + "\nS\nI CLICK 120 120 DRAG 360 120\nCLICK 120 240 +DRAG 355 253\nS\n"
    dlg.edit.setPlainText(text)
    cur = dlg.edit.textCursor()
    cur.setPosition(text.index(anchor))
    cur.setPosition(text.index(pos), cur.MoveMode.KeepAnchor)
    dlg.edit.setTextCursor(cur)
    dlg.replay()
    dlg._replay_timer.stop()
    assert dlg._replay_lines == [
        HEADER + "\nI CLICK 120 120 DRAG 360 120\nCLICK 120 240 +DRAG 355 253"], want


def test_a_selection_ending_at_a_line_start_does_not_take_that_line(fp, win):
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    text = "CLICK 1 1\nCLICK 2 2\nCLICK 3 3\n"              # the existing format too
    dlg.edit.setPlainText(text)
    cur = dlg.edit.textCursor()
    cur.setPosition(text.index("CLICK 3"))                  # bottom up, from a line start
    cur.setPosition(text.index("LICK 2"), cur.MoveMode.KeepAnchor)
    dlg.edit.setTextCursor(cur)
    dlg.replay()
    dlg._replay_timer.stop()
    assert dlg._replay_lines == ["CLICK 2 2"]


def test_the_recorder_window_numbers_its_lines(fp, win):
    """Patrick, 2026-10-05: line numbers in the recorder window, so that an
    error can point at its line. One number per macro line, 1-based -- the
    way a v2 error counts -- in a gutter that widens with the count."""
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    dlg.resize(500, 400)
    dlg.show()
    edit = dlg.edit
    edit.setPlainText(HEADER + "\nCLICK 1 1\nCLICK 2 2")
    QApplication.processEvents()
    seen = edit.visible_line_numbers()
    assert [n for n, _ in seen] == [1, 2, 3]
    tops = [top for _, top in seen]
    assert tops == sorted(tops) and len(set(tops)) == 3
    narrow = edit.line_number_width()
    assert narrow > 0 and edit.viewportMargins().left() == narrow
    assert edit._gutter.width() == narrow and not edit._gutter.grab().isNull()
    edit.setPlainText("\n".join(["CLICK 1 1"] * 1200))
    QApplication.processEvents()
    assert edit.line_number_width() > narrow            # four digits now
    assert edit.viewportMargins().left() == edit.line_number_width()
    edit.verticalScrollBar().setValue(1000)
    QApplication.processEvents()
    assert edit.visible_line_numbers()[0][0] == 1001    # numbers follow the scroll
    res = win.run_macro(HEADER + "\nCLICK 1 1\nBOGUS 1")
    assert res["errors"][0].startswith("line 3:")       # the line the gutter shows as 3
    dlg.close()


def _dialog(fp, win, text):
    win.prepare_headless()
    dlg = fp.MacroRecorderDialog(win)
    dlg.resize(500, 400)
    dlg.show()
    dlg.edit.setPlainText(text)
    QApplication.processEvents()
    return dlg


def _replay_all(dlg):
    dlg.replay()
    dlg._replay_timer.stop()
    while dlg._replay_idx < len(dlg._replay_lines):
        dlg._replay_step()


def test_a_v2_error_marks_its_line_in_the_gutter(fp, win):
    """Patrick, 2026-10-06: "so an error can highlight the broken line
    number with an error indicator". The lines before the bad one run; it
    is marked, tinted, its tooltip is the error, and the error STAYS on the
    status line when the replay ends (his word: "keep the error message on
    the bottom of the macro window (instead of filling in replay complete)")."""
    dlg = _dialog(fp, win, HEADER + "\nCLICK 1 1\n\nBOGUS 1\nCLICK 2 2\n")
    dlg.edit.selectAll()
    _replay_all(dlg)
    errors = dlg.edit.error_lines()
    assert list(errors) == [4]
    assert errors[4].startswith("line 4:")
    assert dlg.status_lbl.text().startswith("Replay stopped: line 4:")
    assert len(dlg.edit.extraSelections()) == 1
    assert dlg.edit.extraSelections()[0].cursor.blockNumber() == 3
    rows = dict(dlg.edit.visible_line_numbers())
    assert dlg.edit.error_at(rows[4]) == errors[4]              # the tooltip
    assert dlg.edit.error_at(rows[3]) is None
    assert not dlg.edit._gutter.grab().isNull()
    dlg.close()


def test_a_v2_error_in_a_selection_without_the_header_still_lands_on_its_line(fp, win):
    """The header is put back on for the run, so the error's line is one
    more than the selection's; the marker is on the editor's line."""
    text = HEADER + "\nS\nCLICK 1 1\nKEY {Nope}\nCLICK 2 2\n"
    dlg = _dialog(fp, win, text)
    cur = dlg.edit.textCursor()
    cur.setPosition(text.index("CLICK 1 1"))
    cur.setPosition(text.index("CLICK 2 2"), cur.MoveMode.KeepAnchor)
    dlg.edit.setTextCursor(cur)
    _replay_all(dlg)
    assert list(dlg.edit.error_lines()) == [4]
    dlg.close()


def test_an_existing_format_error_marks_the_line_that_was_being_replayed(fp, win):
    """The existing language's errors name a token, not a line; it is
    replayed one line at a time, so the line is the one just run. Blank
    lines are skipped by the replay and counted by the gutter."""
    dlg = _dialog(fp, win, "CLICK 1 1\n\nFOO 1 2\nCLICK 2 2\nBAR\n")
    dlg.edit.selectAll()
    _replay_all(dlg)
    errors = dlg.edit.error_lines()
    assert list(errors) == [3, 5]
    assert errors[3].startswith("FOO:") and errors[5].startswith("BAR:")
    dlg.close()


def test_errors_are_cleared_by_the_next_replay_and_by_recording(fp, win):
    dlg = _dialog(fp, win, "FOO\nCLICK 2 2\n")
    dlg.edit.selectAll()
    _replay_all(dlg)
    assert dlg.edit.error_lines() == {1: "FOO: unknown command"}
    cur = dlg.edit.textCursor()                      # replay the good line only
    cur.setPosition(dlg.edit.toPlainText().index("CLICK"))
    cur.movePosition(cur.MoveOperation.EndOfLine, cur.MoveMode.KeepAnchor)
    dlg.edit.setTextCursor(cur)
    _replay_all(dlg)
    assert dlg.edit.error_lines() == {} and dlg.edit.extraSelections() == []
    dlg.edit.mark_error(1, "x")
    dlg.start()
    assert dlg.edit.error_lines() == {}
    dlg.stop()
    dlg.close()


def test_a_marker_stays_with_its_line_when_lines_are_inserted_above(fp, win):
    dlg = _dialog(fp, win, "CLICK 1 1\nFOO\n")
    dlg.edit.mark_error(2, "bad")
    cur = dlg.edit.textCursor()
    cur.setPosition(0)
    cur.insertText("; a comment\n; another\n")
    assert dlg.edit.error_lines() == {4: "bad"}
    dlg.edit.mark_error(99, "nowhere")               # out of range: ignored
    assert list(dlg.edit.error_lines()) == [4]
    dlg.close()


def test_his_macro_with_a_bad_line_11_draws_lines_7_to_10(fp, win):
    """Patrick's own case, 2026-10-06: the commands check macro with
    `@WALL 0 300 0` as line 11 -- "the mark should appear on that line but
    lines 7 through 10 should show on the canvas"."""
    import pathlib
    path = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "macro2-commands-check.fpm"
    lines = path.read_text(encoding="utf-8").splitlines()[:10]
    lines += ["@WALL 0 300 0", "; 2. the room is named; a quoted argument keeps its space",
              '@ROOM "Living Room" 120 90', "@DESELECT"]
    dlg = _dialog(fp, win, "\n".join(lines) + "\n")
    dlg.edit.selectAll()
    _replay_all(dlg)
    assert win.scene_summary()["counts"] == {"walls": 4, "rooms": 0, "furnishings": 0}
    assert list(dlg.edit.error_lines()) == [11]
    assert "line 11:" in dlg.status_lbl.text() and "complete" not in dlg.status_lbl.text()
    dlg.close()


def test_the_v2_point_is_scene_inches_whatever_the_zoom(fp, win):
    """sec5.1: scene coordinates, so the same macro draws the same wall
    zoomed out and zoomed in."""
    for zoom in (0.25, 2.0):
        win.prepare_headless()
        win.clear_plan() if hasattr(win, "clear_plan") else None
        win.view.resetTransform()
        win.view.scale(zoom, zoom)
        win.view.centerOn(QPointF(240.0, 150.0))
        res = win.run_macro(HEADER + "\nI CLICK 120 120 DRAG 360 120")
        assert res["ok"]
        assert _walls(fp, win) == [(120.0, 120.0, 360.0, 120.0)], zoom
        for w in [w for w in win.scene.items() if isinstance(w, fp.WallItem)]:
            win.scene.removeItem(w)


def test_the_check_macro_does_what_its_comments_say(fp, win):
    """`fixtures/macro2-player-check.fpm`, Patrick's manual check, replayed
    verbatim on an empty plan."""
    import pathlib
    path = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "macro2-player-check.fpm"
    win.prepare_headless()
    res = win.run_macro(path.read_text(encoding="utf-8"))
    assert res["ok"] and res["warnings"] == [], res
    px = 1.0 / win.view.transform().m11()
    by_y = {w[1]: w for w in _walls(fp, win)}
    assert by_y[120.0] == (120.0, 120.0, 360.0, 120.0)                    # 1
    _, _, x2, y2 = by_y[240.0]                                            # 2
    assert x2 == pytest.approx(355.0, abs=px) and y2 == pytest.approx(253.0, abs=px)
    _, _, x3, y3 = by_y[360.0]                                            # 3
    assert x3 == pytest.approx(301.0, abs=px) and y3 == pytest.approx(451.0, abs=px)
    wall1 = next(w for w in win.scene.items()
                 if isinstance(w, fp.WallItem) and w.p1.y() == 120.0 and w.p2.y() == 120.0)
    assert [(o.kind, o.code) for o in wall1.openings] == [("door", "2868")]   # 4
    assert win.tool == fp.TOOL_SELECT                                     # 5
