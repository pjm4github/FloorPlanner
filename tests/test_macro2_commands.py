"""Macro language v2 -- application commands, `@NAME arg ...`
(MACRO_SPEC.md sec14).

Patrick, 2026-10-04: "carry v1's high level commands as a single command
using the form @COMMAND". An application command makes the application act
directly where every other v2 line simulates input, and it is RUN BY THE
EXISTING LANGUAGE'S OWN HANDLER, so `@PLACE` and `PLACE` cannot drift apart.

The first half needs no window (grammar, validation, serializer); the
second runs the commands through `MainWindow.run_macro`.
"""
import pytest
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtWidgets import QApplication

from floorplanner.macro import MacroRunner
from floorplanner.macro2 import appcmd, ast, check, expand, parse, serialize
from floorplanner.macro2.parse import HEADER
from floorplanner.roofs import RoofItem

pytestmark = pytest.mark.macro

TOOLS = frozenset("SEIDWRGM")


def _cmd(text):
    res = parse(text)
    assert res.ok, [str(e) for e in res.errors]
    (ln,) = res.macro.lines
    return ln


# --------------------------------------------------------------------------
# the grammar
# --------------------------------------------------------------------------
def test_a_name_and_its_arguments():
    ln = _cmd("@PLACE sofa 120 96 0")
    assert ln.tool is None
    assert ln.command == ast.AppCommand("PLACE", ("sofa", "120", "96", "0"))


def test_a_quoted_argument_keeps_its_spaces_and_loses_its_quotes():
    assert _cmd('@ROOM "Living Room" 120 90').command.args == ("Living Room", "120", "90")
    assert _cmd('@OPEN "plans/my den; v2.json"').command.args == ("plans/my den; v2.json",)
    assert _cmd('@ROOM "" 1 2').command.args == ("", "1", "2")


def test_a_bare_word_may_contain_a_quote_so_feet_and_inches_is_one_argument():
    assert _cmd("""@PLACE sofa 10' 12'6" 0""").command.args == ("sofa", "10'", "12'6\"", "0")


def test_a_comment_ends_the_arguments_and_a_tool_letter_may_lead():
    ln = _cmd("S @SELECT 120 96   ; pick the sofa")
    assert (ln.tool, ln.command) == ("S", ast.AppCommand("SELECT", ("120", "96")))
    assert _cmd("@NEW").command == ast.AppCommand("NEW", ())


def test_the_at_sign_is_what_makes_it_a_command():
    """Without it the letters are tool letters, and two on a line is an
    error -- which is why the form needs a marker at all."""
    assert not parse("PLACE sofa 120 96 0").ok
    assert not parse("DOOR 120 0 3280").ok
    assert parse("@DOOR 120 0 3280").ok


@pytest.mark.parametrize("text", [
    "@place sofa 1 2",          # the name is uppercase, like every keyword
    "@ sofa 1 2",               # a name is required
    "@1PLACE sofa 1 2",         # and starts with a letter
    '@ROOM "unclosed 1 2',      # a quoted string closes on its line
    "CLICK 1 1 @NEW",           # one command to a line
])
def test_malformed_commands_are_syntax_errors(text):
    res = parse(text)
    assert res.errors and all(e.line == 1 for e in res.errors)


def test_crlf_and_a_command_as_the_last_line_without_a_newline():
    a = parse("@NEW\n@PLACE sofa 1 2").macro
    b = parse("@NEW\r\n@PLACE sofa 1 2").macro
    assert a == b and len(a.lines) == 2
    assert all("\r" not in arg for ln in b.lines for arg in ln.command.args)


# --------------------------------------------------------------------------
# validation: found before anything runs
# --------------------------------------------------------------------------
@pytest.mark.parametrize("text,col,needle", [
    ("@FLOOGLE 1 2", 0, "unknown application command '@FLOOGLE'"),
    ("@CLICK 1 2", 0, "unknown application command '@CLICK'"),
    ("@PLACE sofa 120", 0, "@PLACE takes 3 to 4 arguments, not 2"),
    ("@DOOR 120 0", 0, "@DOOR takes 3 arguments, not 2"),
    ("@NEW now", 0, "@NEW takes 0 arguments, not 1"),
    ("@OPEN", 0, "@OPEN takes 1 argument, not 0"),
    ("@DORMER 1 2 3 4 5 6", 0, "@DORMER takes 5 or 7 arguments, not 6"),
    ("S @WALL 0 0 240", 2, "@WALL takes 4 to 5 arguments, not 3"),
])
def test_an_unknown_name_or_a_wrong_count_is_a_positioned_error(text, col, needle):
    res = check(text, TOOLS)
    assert [(e.line, e.col, e.message) for e in res.errors] == [(1, col, needle)]


def test_the_input_words_of_the_existing_language_are_deliberately_not_commands():
    """sec14.2: v2 says these itself -- a chain, KEY, a tool letter."""
    for name in ("CLICK", "RCLICK", "DRAG", "MOVE", "PRESS", "RELEASE", "TYPE",
                 "WAIT", "TOOL", "PUP", "ENTER", "ESC"):
        assert name not in appcmd.COMMANDS


def test_every_command_resolves_to_a_handler_the_existing_language_has():
    """One vocabulary, not two: each name maps to a token `MacroRunner`
    dispatches -- a `_cmd_*` handler, `DELETE`, or a caret command."""
    for name in appcmd.COMMANDS:
        tok = appcmd.legacy_token(name)
        if tok.startswith("^"):
            assert tok in ("^F", "^+F", "^H")
        elif tok == "DELETE":
            continue
        else:
            assert hasattr(MacroRunner, f"_cmd_{tok.lower()}"), name


# --------------------------------------------------------------------------
# expansion and the serializer
# --------------------------------------------------------------------------
def test_a_command_simulates_no_input_and_leaves_a_held_key_held():
    res = check('KEYDOWN {Shift}\n@PLACE sofa 1 2\nKEYUP {Shift}', TOOLS)
    events, warnings = expand(res.macro)
    assert [(e.kind, e.key or e.text) for e in events] == [
        ("key_down", "Shift"), ("command", "PLACE"), ("key_up", "Shift")]
    assert events[1].args == ("sofa", "1", "2") and warnings == []


@pytest.mark.parametrize("text,canonical", [
    ("@PLACE   sofa\t120   96", "@PLACE sofa 120 96"),
    ('@ROOM "Living Room" 120 90', '@ROOM "Living Room" 120 90'),
    ('@ROOM "Den" 120 90', "@ROOM Den 120 90"),            # quotes only when needed
    ('@OPEN "a;b.json"', '@OPEN "a;b.json"'),
    ('@ROOM "" 1 2', '@ROOM "" 1 2'),
    ("""@PLACE sofa 10' 12'6\"""", """@PLACE sofa 10' 12'6\""""),
    ("S@SELECTALL", "S @SELECTALL"),
    ("@NEW ; start over", "@NEW"),
])
def test_the_canonical_form_and_the_round_trip(text, canonical):
    once = serialize(parse(text).macro)
    assert once == f"; fpmacro 2\n{canonical}\n"
    again = parse(once)
    assert again.ok and serialize(again.macro) == once
    assert again.macro == parse(text).macro, "the same command either way"


# --------------------------------------------------------------------------
# running them
# --------------------------------------------------------------------------
@pytest.fixture
def clean_mods():
    yield
    assert QApplication.keyboardModifiers() == Qt.KeyboardModifier.NoModifier


def _run(win, body):
    win.prepare_headless()
    return win.run_macro(HEADER + "\n" + body)


@pytest.mark.gui
def test_the_specs_own_example_builds_a_furnished_room(fp, win, tmp_path, clean_mods):
    """MACRO_SPEC.md sec14.4, with the snapshot sent to a temp path: four
    walls, a named room, a door, a sofa by command -- and one free-angle
    wall by INPUT, in the same macro."""
    shot = tmp_path / "den.svg"
    res = _run(win, "\n".join([
        "@WALL 0 0 240 0 ext", "@WALL 240 0 240 180 ext",
        "@WALL 240 180 0 180 ext", "@WALL 0 180 0 0 ext",
        '@ROOM "Living Room" 120 90', "@DOOR 120 0 3680", "@PLACE sofa 120 140 0",
        "I CLICK 60 90 +DRAG 177 133     ; and a free-angle wall, by input",
        f'@SHOT "{shot.as_posix()}"']))
    assert res["ok"] and res["warnings"] == [], res
    assert res["counts"] == {"walls": 5, "rooms": 1, "furnishings": 1}
    room = next(it for it in win.scene.items() if isinstance(it, fp.RoomItem))
    assert room.name == "Living Room"
    assert sum(len(w.openings) for w in win.scene.items() if isinstance(w, fp.WallItem)) == 1
    free = next(w for w in win.scene.items() if isinstance(w, fp.WallItem)
                and w.wall_type == "interior")
    assert free.p2.y() != free.p1.y() and free.p2.x() != free.p1.x(), "the Shift-drag"
    assert shot.exists() and shot.stat().st_size > 0


@pytest.mark.gui
def test_a_command_does_exactly_what_the_existing_word_does(fp, win, clean_mods):
    """The same handler, so the same scene -- compared item for item."""
    win.prepare_headless()
    win.run_macro("WALL 0 0 240 0 ext\nDOOR 120 0 3280\nPLACE sofa 10' 8' 90\n"
                  "SELECT 120 96\nROTATE 45")
    legacy = win.snapshot()
    win.clear_plan()
    res = win.run_macro(HEADER + "\n@WALL 0 0 240 0 ext\n@DOOR 120 0 3280\n"
                        "@PLACE sofa 10' 8' 90\n@SELECT 120 96\n@ROTATE 45")
    assert res["ok"], res
    v2 = win.snapshot()
    for key in ("vertices", "walls", "openings", "furnishings"):
        assert v2.get(key) == legacy.get(key), key


@pytest.mark.gui
def test_selection_editing_and_files(fp, win, tmp_path, clean_mods):
    plan = tmp_path / "out.json"
    res = _run(win, "\n".join([
        "@PLACE sofa 120 96 0", "@PLACE armchair 240 96 0",
        "@SELECT 120 96", "@MOVETO 300 300", "@DESELECT",
        "@SELECTALL", "@DELETE",
        "@PLACE bed_queen 60 60 90", "@ZOOMFIT",
        f'@SAVE "{plan.as_posix()}"', "@NEW"]))
    assert res["ok"], res
    assert res["counts"]["furnishings"] == 0, "@NEW cleared the plan"
    res = win.run_macro(HEADER + f'\n@OPEN "{plan.as_posix()}"')
    assert res["ok"] and res["counts"]["furnishings"] == 1, "one bed, saved and reopened"


@pytest.mark.gui
def test_floors_and_shuffle(fp, win, clean_mods):
    res = _run(win, '@NEWFLOOR "Floor 2"\n@WALL 0 0 120 0\n@FLOOR default\n@SHUFFLE on')
    assert res["ok"], res
    assert win.active_floor == fp.DEFAULT_FLOOR
    assert [f.name for f in win.floors] == [fp.DEFAULT_FLOOR, "Floor 2"]
    (wall,) = [w for w in win.scene.items() if isinstance(w, fp.WallItem)]
    assert wall.floor == "Floor 2"
    assert win.a_shuffle.isChecked()
    assert _run(win, "@SHUFFLE off")["ok"] and not win.a_shuffle.isChecked()


@pytest.mark.gui
def test_a_dormer_by_command(fp, win, clean_mods):
    win.prepare_headless()
    host = RoofItem(QPointF(0, 100), QPointF(400, 100), eaves_h_in=96.0,
                    ridge_h_in=150.0, overhang_in=0.0, span_in=100.0)
    win.scene.addItem(host)
    res = win.run_macro(HEADER + "\n@DORMER 200 190 60 116 136")
    assert res["ok"], res
    dormers = [it for it in win.scene.items() if isinstance(it, RoofItem) and it.is_dormer()]
    assert len(dormers) == 1 and dormers[0].host is host


@pytest.mark.gui
def test_a_command_that_fails_when_it_runs_aborts_with_its_line(fp, win, clean_mods):
    """The count was right, so it validated; the catalog has no such kind,
    which only the handler can know. Nothing after it runs."""
    res = _run(win, "@PLACE sofa 120 96\n@PLACE no_such_thing 240 96\n@PLACE armchair 300 96")
    assert not res["ok"]
    assert res["errors"] == ["line 3: ValueError: unknown furnishing 'no_such_thing'"]
    assert res["counts"]["furnishings"] == 1, "the first ran, the third did not"


@pytest.mark.gui
def test_a_wrong_count_is_found_first_and_stops_the_macro_at_its_line(fp, win, clean_mods):
    """sec8.3 as amended (Patrick, 2026-10-06): the error is found before
    anything runs and reported with its line; the lines before it run."""
    res = _run(win, "@PLACE sofa 120 96\n@DOOR 120 0\n@PLACE sofa 240 96")
    assert not res["ok"] and res["steps"] == 1
    assert res["errors"] == ["line 3:0 @DOOR takes 3 arguments, not 2"]
    assert res["counts"]["furnishings"] == 1, "the line before ran; the rest did not"


@pytest.mark.gui
def test_a_number_the_handler_cannot_read_is_reported_not_swallowed(fp, win, clean_mods):
    res = _run(win, "@WALL 0 0 two-forty 0")
    assert not res["ok"] and res["errors"][0].startswith("line 2: ValueError")


@pytest.mark.gui
def test_the_check_macro_does_what_its_comments_say(fp, win, clean_mods):
    """`fixtures/macro2-commands-check.fpm`, Patrick's manual check,
    replayed verbatim on an empty plan."""
    import pathlib
    path = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "macro2-commands-check.fpm"
    win.prepare_headless()
    res = win.run_macro(path.read_text(encoding="utf-8"))
    assert res["ok"] and res["warnings"] == [], res
    assert res["counts"] == {"walls": 5, "rooms": 1, "furnishings": 2}
    room = next(it for it in win.scene.items() if isinstance(it, fp.RoomItem))
    assert room.name == "Living Room"
    doors = [o for w in win.scene.items() if isinstance(w, fp.WallItem) for o in w.openings]
    assert [(o.kind, o.code) for o in doors] == [("door", "3680")]
    furn = {it.kind: it for it in win.scene.items() if isinstance(it, fp.FurnishingItem)}
    chair = furn["armchair"].pos()                  # pos is the centre
    assert (chair.x(), chair.y()) == pytest.approx((48.0, 72.0)), "4ft, 6ft"
    assert furn["sofa"].rotation() == pytest.approx(90.0)
    assert win.scene.selectedItems() == []
    free = next(w for w in win.scene.items() if isinstance(w, fp.WallItem)
                and w.wall_type == "interior")
    assert free.p1.y() != free.p2.y(), "the Shift-drag, off square"
