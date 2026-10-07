"""Macro language v2 -- the legacy converter (MACRO_SPEC.md sec11).

`floorplanner/macro2/convert.py` rewrites a macro of the EXISTING language
as v2; `fp_macro.py --convert` does it to files, keeping a `.bak`. A
construct with no v2 form is REPORTED and never dropped.

The first half needs no window. The second replays every committed
existing-format `.fpm` on both engines and compares the plans.
"""
import json
import pathlib
import warnings

import pytest
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QDialog

import fp_macro
from floorplanner.macro import CARET_SHORTCUTS, MacroRunner
from floorplanner.macro2 import check, is_v2
from floorplanner.macro2.convert import convert, words
from floorplanner.macro2.parse import HEADER

pytestmark = pytest.mark.macro

TOOLS = frozenset(MacroRunner._TOOL_CODES)
ROOT = pathlib.Path(__file__).resolve().parent.parent


def _body(text):
    """The converted lines, without the header; nothing unconverted."""
    conv = convert(text)
    assert conv.ok, [str(p) for p in conv.problems]
    assert check(conv.text, TOOLS).errors == ()
    head, *lines = conv.text.splitlines()
    assert head == HEADER
    return lines


# --------------------------------------------------------------------------
# token by token
# --------------------------------------------------------------------------
@pytest.mark.parametrize("legacy, v2", [
    # tools: a letter, a digit, a name; the prefix of what shared its line
    ("S", ["S"]),
    ("i click 1 2", ["I CLICK 1 2"]),
    ("3", ["I"]),
    ("TOOL roofridge CLICK 1 2", ["G CLICK 1 2"]),
    ("S\nCLICK 1 2", ["S", "CLICK 1 2"]),
    ("S E", ["S", "E"]),
    # the mouse
    ("CLICK 10 20", ["CLICK 10 20"]),
    ("CLICK 10 20 DRAG 30 40", ["CLICK 10 20 DRAG 30 40"]),
    ("^CLICK 10 20", ["^CLICK 10 20"]),
    ("^CLICK 10 20 DRAG 30 40", ["^CLICK 10 20 ^DRAG 30 40"]),
    ("DRAG 1 2 3 4", ["CLICK 1 2 DRAG 3 4"]),
    ("PRESS 1 1 RELEASE 9 9", ["CLICK 1 1 DRAG 9 9"]),
    ("PRESS 1 1 MOVE 5 5 RELEASE 9 9", ["CLICK 1 1 DRAG 5 5 DRAG 9 9"]),
    ("PRESS 1 1 MOVE 9 9 RELEASE 9 9", ["CLICK 1 1 DRAG 9 9"]),
    ("PRESS 1 1 RELEASE 1 1", ["CLICK 1 1"]),
    ("RCLICK 4 5", ["RCLICK 4 5"]),
    ("MOVE 4 5", ["MOVE 4 5"]),
    # numbers: feet-and-inches become inches, two decimals at most
    ("""CLICK 10' 12'6" """, ["CLICK 120 150"]),
    ("CLICK 1.239 -0.001", ["CLICK 1.24 0"]),
    # shortcuts and keys
    ("^Z ^y ^+Z", ["KEY ^z", "KEY ^y", "KEY ^y"]),      # redo, either way
    ("^X ^C ^V", ["KEY ^x", "KEY ^c", "KEY ^v"]),
    ("^G ^+G", ["KEY ^g", "KEY +^g"]),
    ("^H", ["KEY ^h"]),
    ("^N ^A", ["@NEW", "@SELECTALL"]),
    ("LEFT RIGHT UP DOWN", ["KEY {Left}", "KEY {Right}", "KEY {Up}", "KEY {Down}"]),
    ("^LEFT ^down", ["KEY ^{Left}", "KEY ^{Down}"]),
    ("ESC ENTER", ["KEY {Esc}", "KEY {Enter}"]),
    ("S ^Z", ["S KEY ^z"]),
    # what carried a value is an application command
    ('^O "my plans/a.json"', ['@OPEN "my plans/a.json"']),
    ("^+S out.json", ["@SAVE out.json"]),
    ('^F "Floor 2"', ['@FLOOR "Floor 2"']),
    ("^F Loft", ["@FLOOR Loft"]),
    ('^+F "Floor 2"', ['@NEWFLOOR "Floor 2"']),
    ('^H "on" ^H OFF', ["@SHUFFLE on", "@SHUFFLE off"]),
    # the high-level words
    ("DEL DELETE", ["@DELETE", "@DELETE"]),
    ("PLACE sofa 120 96", ["@PLACE sofa 120 96"]),
    ("PLACE sofa 120 96 90 PLACE bed 1 2", ["@PLACE sofa 120 96 90", "@PLACE bed 1 2"]),
    ("""PLACE sofa 10' 12'6" """, ["""@PLACE sofa 10' 12'6\""""]),
    ("WALL 0 0 240 0", ["@WALL 0 0 240 0"]),
    ("WALL 0 0 240 0 int WALL 1 1 2 2", ["@WALL 0 0 240 0 int", "@WALL 1 1 2 2"]),
    ("DOOR 120 0 3680 WINDOW 60 0 3040", ["@DOOR 120 0 3680", "@WINDOW 60 0 3040"]),
    ('ROOM "Living Room" 120 90', ['@ROOM "Living Room" 120 90']),
    ("DORMER 1 2 3 4 5", ["@DORMER 1 2 3 4 5"]),
    ("DORMER 1 2 3 4 5 0 -1 S", ["@DORMER 1 2 3 4 5 0 -1", "S"]),
    ("SELECT 1 2 ROTATE 90 MOVETO 3 4", ["@SELECT 1 2", "@ROTATE 90", "@MOVETO 3 4"]),
    ("SELECTALL DESELECT ZOOMFIT NEW", ["@SELECTALL", "@DESELECT", "@ZOOMFIT", "@NEW"]),
    ("OPEN a.json SAVE b.json SHOT c.svg", ["@OPEN a.json", "@SAVE b.json", "@SHOT c.svg"]),
    ("WAIT", ["WAIT 0"]),
    # text
    ('TYPE "Hello World"', ["TYPE Hello World"]),
    ('TYPE "2868  "', ["TYPE 2868", "KEY {Space} {Space}"]),
    ('TYPE " "', ["KEY {Space}"]),
    ('TYPE ""', ["TYPE"]),
    ('TYPE "a;b +c"', ["TYPE a;b +c"]),
    # the context menu: a right click, then its keys and text
    ('PUP 120 0 DOWN DOWN DOWN ENTER TYPE "2868" ENTER',
     ["RCLICK 120 0", "KEY {Down} {Down} {Down} {Enter}", "TYPE 2868", "KEY {Enter}"]),
    ("PUP 120 96 DOWN ESC", ["RCLICK 120 96", "KEY {Down} {Esc}"]),
    ("PUP 5 5", ["RCLICK 5 5", "KEY {Esc}"]),
    ('PUP 5 5 DOWN ENTER TYPE "x" CLICK 1 1',
     ["RCLICK 5 5", "KEY {Down} {Enter}", "TYPE x", "KEY {Esc}", "CLICK 1 1"]),
    # comments
    ("# a note\nS  # select\n# end", ["; a note", "; select", "S", "; end"]),
])
def test_each_existing_token_has_its_v2_form(legacy, v2):
    assert _body(legacy) == v2


@pytest.mark.parametrize("legacy, source, kept", [
    ("PRESS 1 1 CLICK 2 2", "PRESS 1 1", ["CLICK 2 2"]),
    ("RELEASE 1 1 S", "RELEASE 1 1", ["S"]),
    ("^F", "^F", []),
    ("^F CLICK 1 1", "^F", ["CLICK 1 1"]),
    ("FOO 1 2 S", "FOO 1 2", ["S"]),
    ("^Q", "^Q", []),
    ("^+CLICK 1 2", "^+CLICK 1 2", []),
    ("TOOL hammer", "TOOL", ["; NOT CONVERTED (line 1): hammer -- unknown command"]),
    ("CLICK 1", "CLICK 1", []),
    ("CLICK a b", "CLICK", None),
    ("WALL 1 2 3", "WALL 1 2 3", []),
    ('OPEN "abc', "OPEN", None),             # an argument v2 cannot quote
])
def test_what_has_no_v2_form_is_reported_and_stays_in_the_text(legacy, source, kept):
    """sec11: "report it and do not drop it silently". Each is a `Problem`
    AND a comment where it stood; what follows it still converts; and the
    text is a valid v2 macro all the same."""
    conv = convert(legacy)
    assert not conv.ok
    first = conv.problems[0]
    if source is not None:
        assert (first.line, first.text) == (1, source)
    lines = conv.text.splitlines()
    assert lines[1] == f"; NOT CONVERTED (line 1): {first.text} -- {first.reason}"
    if kept is not None:
        assert lines[2:] == kept
    assert sum(ln.startswith("; NOT CONVERTED") for ln in lines) == len(conv.problems)
    assert check(conv.text, TOOLS).errors == ()


def test_a_problem_keeps_its_own_line_number_and_its_tool():
    conv = convert("S\n\nI PRESS 5 5\nCLICK 1 1")
    (p,) = conv.problems
    assert (p.line, p.text) == (3, "PRESS 5 5")
    assert conv.text.splitlines()[1:] == [
        "S", "I", f"; NOT CONVERTED (line 3): PRESS 5 5 -- {p.reason}", "CLICK 1 1"]


def test_the_two_lines_that_convert_but_differ_are_noted():
    conv = convert("CLICK 1 1\n^S\nRCLICK 2 2")
    assert conv.ok
    assert [n.line for n in conv.notes] == [2, 3]
    assert "Save As" in conv.notes[0].message
    assert "context menu" in conv.notes[1].message
    assert convert("CLICK 1 1 ^Z").notes == ()


def test_the_macro_and_the_text_are_the_same_lines():
    from floorplanner.macro2 import parse
    conv = convert("# c\nI CLICK 1 2 DRAG 3 4\nBOGUS\nPLACE sofa 1 2")
    assert parse(conv.text).macro == conv.macro
    assert is_v2(conv.text) and conv.text.endswith("\n") and "\r" not in conv.text


# --------------------------------------------------------------------------
# the census: nothing of the existing language is left without a rule
# --------------------------------------------------------------------------
def test_every_command_word_of_the_existing_engine_has_a_rule():
    engine = {n[5:].upper() for n in dir(MacroRunner) if n.startswith("_cmd_")}
    assert len(engine) >= 25                    # the enumeration is not empty
    assert words() == engine | {"DELETE"}       # DELETE is `_dispatch`'s own


def test_every_shortcut_of_the_table_converts():
    for key in CARET_SHORTCUTS:
        conv = convert(f'^{key} "x"')
        if key == "F":
            assert conv.text.splitlines()[1] == "@FLOOR x"
        assert conv.problems == () or \
            [p.text for p in conv.problems] == ['"x"'], key    # the spare argument


def test_every_shortcut_written_as_a_key_is_a_shortcut_the_app_has(win):
    """`KEY ^g` only groups if an action answers Ctrl+G. The two the app
    does not have that way -- ^A, and ^N whose action asks first -- are
    application commands instead."""
    seqs = [s for act in win.findChildren(QAction) for s in act.shortcuts()]
    found = 0
    for key in CARET_SHORTCUTS:
        line = convert(f"^{key}").text.splitlines()[1]
        if not line.startswith("KEY "):
            continue
        want = QKeySequence("Ctrl+" + ("Shift+" if "+" in line else "") + line[-1])
        assert any(s.matches(want) == QKeySequence.SequenceMatch.ExactMatch
                   for s in seqs), key
        found += 1
    assert found == 10


# --------------------------------------------------------------------------
# the committed macros: every one converts whole, and replays the same
# --------------------------------------------------------------------------
#: file -> (plan loaded first, walls afterwards)
COMMITTED = {
    "examples/fiveRoomTestMacro.fpm": ("examples/fiveRoomTest.json", 16),
    "examples/fiveRoomDragSplit.fpm": ("examples/fiveRoomTest.json", 19),
    "examples/fiveRoomDragSplit2.fpm": ("examples/fiveRoomTest.json", 16),
    # 19 since 0228: at this replay geometry (not the macro's own 1200x800, see
    # test_extract_join.py) one slide used to merge into a parallel wall 6in
    # away; a gesture now merges at 3in, so it stays a wall. Both engines agree.
    "examples/dragWallFuseStraggler.fpm": ("examples/fiveRoomTest.json", 19),
    "examples/multifloor.fpm": (None, 12),
    "fixtures/w7offgrid.fpm": (None, 9),
    "fixtures/grid-snap-3in-check.fpm": ("fixtures/grid-snap-3in-check.json", 6),
    # ends `S ^Z`, and with no pause between its steps the undo takes all of it
    "fixtures/disappearingroof.fpm": (None, 0),
}


def _legacy_files():
    return sorted(str(p.relative_to(ROOT)).replace("\\", "/")
                  for d in ("examples", "fixtures") for p in (ROOT / d).glob("*.fpm")
                  if not is_v2(p.read_text(encoding="utf-8")))


def test_the_table_is_every_committed_existing_format_macro():
    assert _legacy_files() == sorted(COMMITTED)
    assert len(COMMITTED) == 8


def _source(name):
    """The macro as the tests replay it: `dragWallFuseStraggler` opens its
    plan by a path of Patrick's machine, so its first line is the setup."""
    text = (ROOT / name).read_text(encoding="utf-8")
    return "\n".join(ln for ln in text.splitlines() if not ln.startswith("^O "))


@pytest.mark.parametrize("name", sorted(COMMITTED))
def test_a_committed_macro_converts_with_nothing_left_over(name):
    conv = convert((ROOT / name).read_text(encoding="utf-8"))
    assert conv.problems == () and conv.notes == ()
    assert check(conv.text, TOOLS).errors == ()
    assert len(conv.macro.lines) >= 2


@pytest.mark.gui
@pytest.mark.parametrize("name", sorted(COMMITTED))
def test_a_committed_macro_replays_to_the_same_plan_converted(fp, name, monkeypatch):
    """The receipt: the existing engine on the file as committed, the v2
    player on its conversion, each on a window of its own -- one plan."""
    from conftest import dispose_window
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    plan, walls = COMMITTED[name]
    legacy = _source(name)
    plans = []
    for text in (legacy, convert(legacy).text):
        win = fp.MainWindow()
        try:
            win.resize(1400, 1000)
            win.show()
            if plan is not None:
                win.load_path(str(ROOT / plan))
                win.zoom_fit()
            if is_v2(text):
                res = win.run_macro(text)
                assert res["ok"] and res["warnings"] == [], res
            else:
                for line in text.splitlines():
                    if line.strip():
                        res = win.run_macro(line)
                        assert res["ok"], res
            assert win.scene_summary()["counts"]["walls"] == walls
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")     # the torn-network report
                plans.append(json.dumps(win.snapshot(), sort_keys=True, default=str))
        finally:
            dispose_window(win)
    assert plans[0] == plans[1]


# --------------------------------------------------------------------------
# fp_macro.py --convert
# --------------------------------------------------------------------------
def _run(capsys, *paths):
    code = fp_macro.main(["--convert", *map(str, paths)])
    return code, json.loads(capsys.readouterr().out)


def test_convert_rewrites_the_file_and_keeps_the_original_as_bak(tmp_path, capsys):
    src = tmp_path / "edits.fpm"
    original = b"# mine\r\nI CLICK 1 2 DRAG 3 4\r\nS ^Z\r\n"
    src.write_bytes(original)
    code, out = _run(capsys, src)
    assert code == 0 and out["ok"]
    (entry,) = out["files"]
    assert entry["status"] == "converted" and entry["lines"] == 2
    assert entry["not_converted"] == [] and entry["notes"] == []
    assert (tmp_path / "edits.fpm.bak").read_bytes() == original
    assert src.read_bytes() == b"; fpmacro 2\n; mine\nI CLICK 1 2 DRAG 3 4\nS KEY ^z\n"


def test_convert_leaves_a_v2_file_alone_so_running_it_twice_is_safe(tmp_path, capsys):
    src = tmp_path / "m.fpm"
    src.write_bytes(b"CLICK 1 2\n")
    assert _run(capsys, src)[0] == 0
    once = src.read_bytes()
    code, out = _run(capsys, src)
    assert code == 0 and out["files"][0]["status"] == "already v2"
    assert src.read_bytes() == once
    assert (tmp_path / "m.fpm.bak").read_bytes() == b"CLICK 1 2\n"


def test_convert_never_overwrites_a_bak(tmp_path, capsys):
    src = tmp_path / "m.fpm"
    src.write_text("CLICK 1 2\n", encoding="utf-8")
    (tmp_path / "m.fpm.bak").write_text("the only original\n", encoding="utf-8")
    code, out = _run(capsys, src)
    assert code == 1 and out["files"][0]["status"] == "error"
    assert src.read_text(encoding="utf-8") == "CLICK 1 2\n"
    assert (tmp_path / "m.fpm.bak").read_text(encoding="utf-8") == "the only original\n"


def test_convert_reports_what_it_could_not_carry_and_exits_1(tmp_path, capsys):
    good, bad, gone = tmp_path / "a.fpm", tmp_path / "b.fpm", tmp_path / "c.fpm"
    good.write_text("S\n", encoding="utf-8")
    bad.write_text("CLICK 1 1\nPRESS 5 5\n^S\n", encoding="utf-8")
    code, out = _run(capsys, good, bad, gone)
    assert code == 1 and not out["ok"]
    a, b, c = out["files"]
    assert a["status"] == "converted" and a["not_converted"] == []
    assert b["status"] == "converted" and len(b["not_converted"]) == 1
    assert b["not_converted"][0].startswith("line 2: PRESS 5 5 -- ")
    assert len(b["notes"]) == 1 and b["notes"][0].startswith("line 3: ")
    assert "; NOT CONVERTED (line 2): PRESS 5 5" in bad.read_text(encoding="utf-8")
    assert c["status"] == "error" and not (tmp_path / "c.fpm.bak").exists()
