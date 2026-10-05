"""Macro language v2, tranche T1 -- the language without Qt delivery.

`docs/macro-spec/MACRO_SPEC.md` sec12 lists the tests; items 1-8 are here
(item 9, the recorder, belongs to its own tranche). Everything below runs
against the AST and the ABSTRACT event list -- no window, no Qt events.

The grammar is Patrick's (`docs/macro-spec/grammar/*.g4`) and the parser is
generated from it and committed (0212-report.md sec3). The last test pins
that the committed parser was generated from the grammar on disk.
"""
import pathlib
import subprocess
import sys

import pytest

from floorplanner.macro2 import ast, check, expand, is_v2, parse, serialize, validate
from floorplanner.macro2.ast import Mod

pytestmark = pytest.mark.macro

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "docs" / "macro-spec" / "examples.macro"
TOOLS = frozenset("SEIDWRGM")          # the application's eight (macro.py:120)
S, C = Mod.SHIFT, Mod.CTRL


def _events(text, tools=TOOLS):
    res = check(text, tools)
    assert res.ok, [str(e) for e in res.errors]
    return expand(res.macro)


def _trace(text):
    """The sec5.4 notation: key and button events in order, the pre-press
    hover left out (the table does not list it), consecutive drag moves
    shown once each with their endpoint."""
    out = []
    for e in _events(text)[0]:
        if e.kind == "key_down":
            out.append(f"{e.key}↓")
        elif e.kind == "key_up":
            out.append(f"{e.key}↑")
        elif e.kind == "press":
            out.append(f"press({e.x:g},{e.y:g})")
        elif e.kind == "release":
            out.append(f"release({e.x:g},{e.y:g})")
        elif e.kind == "move":
            out.append(f"move({e.x:g},{e.y:g})")
    return out


# --------------------------------------------------------------------------
# 1. grammar acceptance
# --------------------------------------------------------------------------
def test_the_spec_example_parses_with_zero_errors():
    text = EXAMPLES.read_text(encoding="utf-8")
    res = parse(text)
    assert res.errors == ()
    assert len(res.macro.lines) == 26, "every non-comment line became a Line"
    assert is_v2(text)


def test_the_example_validates_except_for_its_tool_x():
    """Line 25 is `X MOVE 1.5 -2.25`. No tool has the letter X, so it
    PARSES (item 1) and fails VALIDATION (sec8.3) -- on that line only."""
    res = check(EXAMPLES.read_text(encoding="utf-8"), TOOLS)
    assert [(e.line, e.message) for e in res.errors] == [
        (25, "unknown tool letter 'X'")]


# --------------------------------------------------------------------------
# 2. grammar rejection
# --------------------------------------------------------------------------
@pytest.mark.parametrize("text", [
    "DRAG 10 10", "KEY +", "KEY }", "CLICK 10", "I S CLICK 1 1", "FOO 1 2",
    "KEYDOWN ^a", "KEYDOWN a b", "TYPEx", "CLICK 1 1 TYPE hi", "+"])
def test_each_listed_bad_line_is_rejected(text):
    res = parse(text)
    assert len(res.errors) >= 1
    assert all(e.line == 1 for e in res.errors), "and the error is positioned"
    assert res.macro.lines == (), "no AST is built from a repaired tree"


# --------------------------------------------------------------------------
# 3. TYPE literalness
# --------------------------------------------------------------------------
@pytest.mark.parametrize("line,expected", [
    ('TYPE "Hello World"', '"Hello World"'),
    ("TYPE +DRAG 10 10", "+DRAG 10 10"),
    ("TYPE   x ; y", "  x ; y"),
    ("TYPE", ""),
    ("TYPE ", ""),
])
def test_type_takes_the_rest_of_the_line_literally(line, expected):
    res = parse(line)
    assert res.ok
    (ln,) = res.macro.lines
    assert ln.command == ast.TypeText(expected)


def test_typed_text_becomes_one_key_pair_per_character():
    events, _ = _events("TYPE aB")
    assert [(e.kind, e.key, e.text) for e in events] == [
        ("key_down", "A", "a"), ("key_up", "A", ""),
        ("key_down", "B", "B"), ("key_up", "B", "")]


# --------------------------------------------------------------------------
# 4. expansion -- every row of sec5.4
# --------------------------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    ("CLICK 10 10",
     ["press(10,10)", "release(10,10)"]),
    ("CLICK 10 10 DRAG 200 10",
     ["press(10,10)", "move(200,10)", "release(200,10)"]),
    ("CLICK 10 10 +DRAG 200 80",
     ["press(10,10)", "Shift↓", "move(200,80)", "release(200,80)", "Shift↑"]),
    ("+CLICK 10 10 DRAG 200 80",
     ["Shift↓", "press(10,10)", "Shift↑", "move(200,80)", "release(200,80)"]),
    ("+CLICK 10 10 +DRAG 200 80",
     ["Shift↓", "press(10,10)", "move(200,80)", "release(200,80)", "Shift↑"]),
    ("CLICK 10 10 DRAG 100 10 +DRAG 100 90",
     ["press(10,10)", "move(100,10)", "Shift↓", "move(100,90)",
      "release(100,90)", "Shift↑"]),
    ("^CLICK 10 10 +DRAG 200 80",
     ["Ctrl↓", "press(10,10)", "Ctrl↑", "Shift↓", "move(200,80)",
      "release(200,80)", "Shift↑"]),
])
def test_a_chain_expands_to_exactly_the_listed_order(text, expected):
    assert _trace(text) == expected


def test_each_event_of_a_chain_carries_its_own_segments_modifiers():
    """sec5.3: the head's modifiers ride the press only; a segment's ride
    its moves; the last segment's ride the release (rule 3)."""
    events, _ = _events("^CLICK 10 10 +DRAG 200 80")
    by_kind = {e.kind: e.mods for e in events if e.kind in ("press", "move", "release")}
    assert by_kind == {"press": {C}, "move": {S}, "release": {S}}
    # sec7: a modifier key's own event carries the state AFTER the change
    mod_events = [(e.kind, e.key, e.mods) for e in events if e.key in ("Ctrl", "Shift")]
    assert mod_events == [("key_down", "Ctrl", {C}), ("key_up", "Ctrl", frozenset()),
                          ("key_down", "Shift", {S}), ("key_up", "Shift", frozenset())]


def test_the_pointer_reaches_the_head_before_the_press_with_no_button():
    events, _ = _events("CLICK 10 10")
    assert [e.kind for e in events] == ["hover", "press", "release"]
    assert (events[0].x, events[0].y, events[0].button) == (10.0, 10.0, None)


def test_modifiers_press_and_release_in_the_spec_order():
    """sec7: press Shift, Ctrl, Alt, Meta; release Meta, Alt, Ctrl, Shift --
    whatever order the prefixes were written in."""
    events, _ = _events("#!^+CLICK 1 1")
    keys_ = [(e.kind, e.key) for e in events if e.kind.startswith("key")]
    assert keys_ == [("key_down", "Shift"), ("key_down", "Ctrl"),
                     ("key_down", "Alt"), ("key_down", "Meta"),
                     ("key_up", "Meta"), ("key_up", "Alt"),
                     ("key_up", "Ctrl"), ("key_up", "Shift")]


def test_a_double_click_presses_releases_double_clicks_and_stays_held():
    events, _ = _events("DCLICK 5 5 DRAG 9 9")
    assert [e.kind for e in events] == [
        "hover", "press", "release", "dblclick", "move", "release"]
    events, _ = _events("DCLICK 5 5")
    assert [e.kind for e in events] == ["hover", "press", "release", "dblclick", "release"]


@pytest.mark.parametrize("verb,button", [
    ("CLICK", "left"), ("RCLICK", "right"), ("MCLICK", "middle"),
    ("DCLICK", "left"), ("XCLICK1", "back"), ("XCLICK2", "forward")])
def test_each_head_holds_its_own_button_for_the_whole_chain(verb, button):
    events, _ = _events(f"{verb} 1 1 DRAG 2 2")
    assert {e.button for e in events if e.kind in ("press", "move", "release")} == {button}


def test_the_tool_is_selected_before_the_command_on_its_line():
    events, _ = _events("I CLICK 1 1\nS")
    assert [(e.kind, e.tool) for e in events if e.kind == "tool"] == [
        ("tool", "I"), ("tool", "S")]
    assert events[0].kind == "tool" and events[-1].kind == "tool"


def test_move_wheel_and_wait():
    events, _ = _events("MOVE 50 60\n+WHEEL 0 -120\nWAIT 250")
    kinds = [e.kind for e in events]
    assert kinds == ["hover", "key_down", "wheel", "key_up", "wait"]
    wheel = events[2]
    assert (wheel.dx, wheel.dy, wheel.x, wheel.y, wheel.mods) == (0.0, -120.0, 50.0, 60.0, {S})
    assert events[-1].ms == 250.0


def test_key_strokes_press_modifiers_key_then_release_in_reverse():
    events, _ = _events("KEY ^c ^+z {Enter}")
    assert [(e.kind, e.key) for e in events] == [
        ("key_down", "Ctrl"), ("key_down", "C"), ("key_up", "C"), ("key_up", "Ctrl"),
        ("key_down", "Shift"), ("key_down", "Ctrl"), ("key_down", "Z"),
        ("key_up", "Z"), ("key_up", "Ctrl"), ("key_up", "Shift"),
        ("key_down", "Enter"), ("key_up", "Enter")]


def test_strokes_may_run_together():
    """sec6.2: `KEY ^cv` is Ctrl+C, then V."""
    a = parse("KEY ^cv").macro
    b = parse("KEY ^c v").macro
    assert a == b


# --------------------------------------------------------------------------
# 5. the KEYDOWN baseline
# --------------------------------------------------------------------------
def test_a_held_modifier_rides_every_event_with_no_extra_key_events():
    events, warnings = _events("KEYDOWN {Shift}\nCLICK 1 1\nKEYUP {Shift}")
    assert [(e.kind, e.key) for e in events if e.kind.startswith("key")] == [
        ("key_down", "Shift"), ("key_up", "Shift")], "one down, one up -- nothing between"
    press = next(e for e in events if e.kind == "press")
    release = next(e for e in events if e.kind == "release")
    assert press.mods == {S} and release.mods == {S}
    assert warnings == []


def test_a_key_left_held_is_released_at_the_end_with_a_warning():
    events, warnings = _events("KEYDOWN {Space}\nCLICK 1 1")
    assert (events[-1].kind, events[-1].key) == ("key_up", "Space")
    assert len(warnings) == 1 and "{Space}" in warnings[0] and "released" in warnings[0]


def test_a_doubled_keydown_and_a_stray_keyup_warn_and_do_nothing():
    events, warnings = _events("KEYDOWN a\nKEYDOWN A\nKEYUP a\nKEYUP a")
    assert [(e.kind, e.key) for e in events] == [("key_down", "A"), ("key_up", "A")], \
        "letters are case-insensitive: `a` and `A` are one key"
    assert len(warnings) == 2
    assert "already held" in warnings[0] and "not held" in warnings[1]


def test_a_held_modifier_is_not_released_by_a_chain_that_also_names_it():
    """K joins every segment's set (sec5.3), so `+CLICK` under a held Shift
    sends no Shift event of its own -- and does not release the held one."""
    events, _ = _events("KEYDOWN {Shift}\n+CLICK 1 1 DRAG 5 5\nKEYUP {Shift}")
    assert [(e.kind, e.key) for e in events if e.kind.startswith("key")] == [
        ("key_down", "Shift"), ("key_up", "Shift")]
    assert all(e.mods == {S} for e in events if e.kind in ("press", "move", "release"))


# --------------------------------------------------------------------------
# 6. validation -- positioned, and nothing runs
# --------------------------------------------------------------------------
@pytest.mark.parametrize("text,line,col,needle", [
    ("S\nQ CLICK 1 1", 2, 0, "unknown tool letter 'Q'"),
    ("KEY {Entr}", 1, 4, "unknown key name '{Entr}'"),
    ("KEYDOWN {Nope}", 1, 8, "unknown key name '{Nope}'"),
    ("++CLICK 1 1", 1, 1, "repeated modifier '+'"),
    ("CLICK 1 1 ^+^DRAG 2 2", 1, 12, "repeated modifier '^'"),
    ("KEY ^^c", 1, 5, "repeated modifier '^'"),
    ("WAIT -5", 1, 5, "WAIT cannot be negative"),
])
def test_each_validation_error_is_positioned(text, line, col, needle):
    res = check(text, TOOLS)
    assert [(e.line, e.col, e.message) for e in res.errors] == [(line, col, needle)]
    assert str(res.errors[0]) == f"line {line}:{col} {needle}"


def test_every_error_is_reported_not_only_the_first():
    res = check("Q CLICK 1 1\nKEY {Entr}\nWAIT -1\n++MOVE 1 1", TOOLS)
    assert [e.line for e in res.errors] == [1, 2, 3, 4]


def test_validate_alone_takes_the_applications_tool_letters():
    macro = parse("G CLICK 1 1").macro
    assert validate(macro, TOOLS) == []
    assert [e.message for e in validate(macro, frozenset("S"))] == [
        "unknown tool letter 'G'"]


def test_named_keys_match_without_regard_to_case_and_escapes_are_keys():
    res = check("KEY {enter} {ESC} {f12} {+} {^} {!} {#} {;} {{} {}} {x}", TOOLS)
    assert res.ok, [str(e) for e in res.errors]
    assert check("KEY {F25}", TOOLS).errors[0].message == "unknown key name '{F25}'"


# --------------------------------------------------------------------------
# 7. round trip, and the canonical form
# --------------------------------------------------------------------------
def _stable(text):
    """sec10's requirement: serialize(parse(serialize(ast))) == serialize(ast)."""
    once = serialize(parse(text).macro)
    again = parse(once)
    assert again.ok, [str(e) for e in again.errors]
    assert serialize(again.macro) == once
    return once


def test_the_example_round_trips():
    text = EXAMPLES.read_text(encoding="utf-8")
    out = _stable(text)
    assert out.startswith("; fpmacro 2\n") and out.endswith("\n")
    assert "\r" not in out
    # the example is already in canonical spelling, so nothing is lost:
    # the serialized text parses back to the very same macro
    assert parse(out).macro == parse(text).macro


@pytest.mark.parametrize("text,canonical", [
    ("ICLICK 1 2", "I CLICK 1 2"),                       # a tool letter gets one space
    ("+ CLICK 1 2", "+CLICK 1 2"),                       # modifiers attach
    ("^+CLICK 1 2 #!DRAG 3 4", "+^CLICK 1 2 !#DRAG 3 4"),  # in the order + ^ ! #
    ("CLICK   1.50    -0.0", "CLICK 1.5 0"),             # numbers trimmed; -0 is 0
    ("MOVE 1.005 2.999", "MOVE 1 3"),                    # two decimals at most
    ("KEY ^C +{f5} {ENTER} {x} {+}", "KEY ^c +{F5} {Enter} x {+}"),
    ("KEY ^cv", "KEY ^c v"),
    ("KEYDOWN {space}", "KEYDOWN {Space}"),
    ("TYPE   two leading spaces ; not a comment", "TYPE   two leading spaces ; not a comment"),
    ("TYPE", "TYPE"),
    ("WAIT 250.0", "WAIT 250"),
    ("S", "S"),
])
def test_the_canonical_form(text, canonical):
    out = _stable(text)
    assert out == f"; fpmacro 2\n{canonical}\n"


def test_comments_and_blank_lines_are_not_part_of_the_macro():
    out = _stable("; a comment\n\nCLICK 1 1   ; trailing\n\n")
    assert out == "; fpmacro 2\nCLICK 1 1\n"


# --------------------------------------------------------------------------
# 8. CRLF
# --------------------------------------------------------------------------
def test_a_crlf_copy_parses_to_the_same_ast_with_no_cr_in_any_text():
    lf = EXAMPLES.read_text(encoding="utf-8").replace("\r\n", "\n")
    crlf = lf.replace("\n", "\r\n")
    assert "\r\n" in crlf and "\r" not in lf
    a, b = parse(lf), parse(crlf)
    assert a.ok and b.ok
    assert a.macro == b.macro
    texts = [ln.command.text for ln in b.macro.lines
             if isinstance(ln.command, ast.TypeText)]
    assert texts and all("\r" not in t for t in texts)


# --------------------------------------------------------------------------
# format detection (sec11)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("text,v2", [
    ("; fpmacro 2\nCLICK 1 1", True),
    ("\n\n  ; fpmacro 2  \nCLICK 1 1", True),
    ("CLICK 1 1\n; fpmacro 2", False),
    ("# a legacy comment\nS CLICK 1 1", False),
    ("; fpmacro 3\n", False),
    ("", False),
])
def test_v2_is_detected_by_its_first_non_blank_line(text, v2):
    assert is_v2(text) is v2


# --------------------------------------------------------------------------
# the committed parser is the grammar's
# --------------------------------------------------------------------------
@pytest.mark.tooling
def test_the_committed_parser_was_generated_from_the_grammar_on_disk():
    """The generated code is committed so that nobody needs Java -- which
    leaves a grammar edit without regeneration as the one way to drift.
    `tools/gen_macro_parser.py` records the grammar's hash beside its
    output; this recomputes it."""
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "gen_macro_parser.py"),
                        "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    gen = ROOT / "floorplanner" / "macro2" / "_generated"
    assert "ANTLR 4.11.1" in (gen / "MacroParser.py").read_text(encoding="utf-8")[:80]
    import importlib.metadata
    assert importlib.metadata.version("antlr4-python3-runtime") == "4.11.1", \
        "the runtime is pinned to the tool version that generated the parser"
