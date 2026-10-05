"""Macro language v2: the legacy converter (MACRO_SPEC.md sec11).

    existing-format text -> v2 AST -> canonical v2 text

`convert` reads a macro written in the EXISTING language
(`floorplanner/macro.py`, `docs/macro_language.md`) and maps each of its
tokens onto a v2 command. It follows `MacroRunner._dispatch` token by token
and in its order, so what is one step there is one line (or, for `PUP`, a
few) here. Nothing is run and no window is needed.

WHAT MAPS TO WHAT

  tool letters, the digits 1-6, `TOOL name`   a tool letter (sec4); it is
                                              the prefix of the next command
                                              when that sat on its own line
  CLICK / ^CLICK / RCLICK / MOVE              the same word (sec5); a Ctrl
                                              click-drag carries `^` on every
                                              segment, as the existing engine
                                              put Ctrl on every event
  DRAG x1 y1 x2 y2                            CLICK x1 y1 DRAG x2 y2
  PRESS .. [MOVE ..] RELEASE ..               one chain
  ^Z ^Y ^X ^C ^V ^G ^+G ^S, bare ^H           KEY (sec6.2) -- a real shortcut
  ^+Z                                         KEY ^y: redo, by the shortcut
                                              every platform has
  ^N, ^A                                      @NEW, @SELECTALL: Ctrl+N asks
                                              before discarding and the app
                                              has no Ctrl+A, where the engine
                                              cleared and selected directly
  the arrows, ^arrows, ESC, ENTER             KEY {Left} / ^{Left} / {Esc} ..
  DEL, DELETE and the high-level words        @DELETE, @PLACE, @WALL .. (sec14)
  ^O / ^+S / ^F / ^+F / ^H with their value   @OPEN / @SAVE / @FLOOR /
                                              @NEWFLOOR / @SHUFFLE
  PUP x y keys.. TYPE "text"                  RCLICK x y, then KEY and TYPE
  TYPE "text"                                 TYPE text (trailing spaces as
                                              KEY {Space}, sec6.1)
  WAIT                                        WAIT 0
  # comment                                   ; comment

WHAT HAS NO v2 FORM IS REPORTED, NEVER DROPPED (sec11): it becomes a
`Problem`, and a `; NOT CONVERTED` comment in the written text at the place
it stood. Those are a `PRESS` with no `RELEASE` after it (v2 never holds
the button between lines), a `RELEASE` alone, a bare `^F` (`@FLOOR` needs
the name), and anything the existing engine itself would have refused.

A `Note` marks a line that converted but may behave differently, each for a
stated reason: `^S` and `RCLICK` are real input in v2.

`PUP` drove a menu and then CLOSED whatever was still open. Whether
anything is cannot be known without running it, so the converter writes a
closing `KEY {Esc}` only where the key list did not end in ENTER or ESC.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from floorplanner.macro import CARET_SHORTCUTS, MacroRunner
from floorplanner.macro2 import appcmd, ast, keys
from floorplanner.macro2.ast import Mod
from floorplanner.macro2.parse import HEADER, parse
from floorplanner.macro2.serialize import line as write_line

_NONE = frozenset()
_CTRL = frozenset({Mod.CTRL})
_TOKEN = re.compile(r'"([^"]*)"|(\S+)')

#: tool constant -> letter, and the two older spellings of a tool
_LETTER = {tool: letter for letter, tool in MacroRunner._TOOL_CODES.items()}

#: the existing key words -> the v2 key name (sec6.2)
_KEY_NAME = {"UP": "Up", "DOWN": "Down", "LEFT": "Left", "RIGHT": "Right",
             "ENTER": "Enter", "ESC": "Esc", "HOME": "Home", "END": "End",
             "TAB": "Tab", "BACKSPACE": "Backspace", "DELETE": "Delete"}

#: high-level word -> (fixed argument count, how many optional ones follow)
_OPTIONAL = {
    "PLACE": lambda rest: 1 if rest and not rest[0].quoted
    and MacroRunner._is_num(rest[0].text) else 0,
    "WALL": lambda rest: 1 if rest and rest[0].text.lower() in (
        "ext", "exterior", "int", "interior") else 0,
    "DORMER": lambda rest: 2 if len(rest) >= 2 and all(
        MacroRunner._is_num(t.text) for t in rest[:2]) else 0,
}


@dataclass(frozen=True)
class Token:
    text: str
    line: int
    quoted: bool

    @property
    def source(self) -> str:
        return f'"{self.text}"' if self.quoted else self.text


@dataclass(frozen=True)
class Problem:
    """A construct with no v2 form: where it stood, as written, and why."""
    line: int
    text: str
    reason: str

    def __str__(self) -> str:
        return f"line {self.line}: {self.text} -- {self.reason}"


@dataclass(frozen=True)
class Note:
    """A line that converted, with a difference worth knowing."""
    line: int
    message: str

    def __str__(self) -> str:
        return f"line {self.line}: {self.message}"


@dataclass(frozen=True)
class Conversion:
    macro: ast.Macro
    text: str                # canonical v2, comments and problems included
    problems: tuple
    notes: tuple

    @property
    def ok(self) -> bool:
        return not self.problems


class _NoForm(Exception):
    pass


def _stroke(key: ast.Key, mods=_NONE) -> ast.Stroke:
    return ast.Stroke(frozenset(mods), key)


def _key_line(*strokes) -> ast.KeyPress:
    return ast.KeyPress(tuple(strokes))


def _type_commands(text: str) -> list:
    """sec6.1: trailing spaces cannot be written on a TYPE line; they are
    `KEY {Space}` strokes after it."""
    body = text.rstrip(" ")
    out = [ast.TypeText(body)] if body or not text else []
    n = len(text) - len(body)
    if n:
        out.append(_key_line(*[_stroke(keys.named("Space"))] * n))
    return out


class _Converter:
    def __init__(self, text: str):
        self.toks = []
        self.comments = {}               # line -> comment text
        for n, raw in enumerate(str(text).splitlines(), 1):
            code, hash_, comment = raw.partition("#")
            if hash_:
                self.comments[n] = comment.strip()
            for m in _TOKEN.finditer(code):     # `MacroRunner._tokenize`'s rule
                quoted = m.group(1) is not None
                self.toks.append(Token(m.group(1) if quoted else m.group(2),
                                       n, quoted))
        self.out = []                    # ast.Line | str (a comment line)
        self.problems = []
        self.notes = []
        self.pending = None              # (letter, line): a tool not yet written

    # -- output --------------------------------------------------------------
    def _flush_tool(self):
        if self.pending is not None:
            self.out.append(ast.Line(self.pending[0], None))
            self.pending = None

    def _emit(self, cmd, line: int):
        tool = None
        if self.pending is not None and self.pending[1] == line:
            tool, self.pending = self.pending[0], None
        self._flush_tool()
        ln = ast.Line(tool, cmd)
        # the guard: only what the grammar reads back as itself is written
        back = parse(HEADER + "\n" + write_line(ln) + "\n")
        if back.errors or back.macro.lines != (ln,):
            if tool is not None:
                self.out.append(ast.Line(tool, None))
            raise _NoForm("it cannot be written in v2")
        self.out.append(ln)

    def _comment(self, text: str):
        self._flush_tool()
        self.out.append(("; " + text).rstrip())

    # -- arguments -----------------------------------------------------------
    def _take(self, i: int, n: int):
        if i + n > len(self.toks):
            raise _NoForm(f"expected {n} more argument(s)")
        return self.toks[i:i + n], i + n

    def _nums(self, i: int, n: int):
        toks, i = self._take(i, n)
        try:
            # two decimals, as the serializer writes them (sec10)
            return [round(MacroRunner._num(t.text), 2) for t in toks], i
        except ValueError:
            raise _NoForm("not a number") from None

    def _word(self, i: int):
        return self.toks[i].text.upper() if i < len(self.toks) else None

    # -- the walk ------------------------------------------------------------
    def run(self) -> Conversion:
        i, shown = 0, 0
        while i < len(self.toks):
            tok = self.toks[i]
            shown = self._comments_through(shown, tok.line)
            try:
                i = self._dispatch(tok, i + 1)
            except _NoForm as ex:
                j = i + 1               # its numbers go with it
                while j < len(self.toks) and not self.toks[j].quoted \
                        and MacroRunner._is_num(self.toks[j].text):
                    j += 1
                src = " ".join(t.source for t in self.toks[i:j])
                self.problems.append(Problem(tok.line, src, str(ex)))
                self._comment(f"NOT CONVERTED (line {tok.line}): {src} -- {ex}")
                i = j
        self._comments_through(shown, max(self.comments, default=0))
        self._flush_tool()
        lines = tuple(x for x in self.out if isinstance(x, ast.Line))
        text = "\n".join([HEADER, *(x if isinstance(x, str) else write_line(x)
                                    for x in self.out)]) + "\n"
        return Conversion(ast.Macro(lines), text, tuple(self.problems),
                          tuple(self.notes))

    def _comments_through(self, shown: int, line: int) -> int:
        for n in sorted(k for k in self.comments if shown < k <= line):
            self._comment(self.comments[n])
        return max(shown, line)

    def _dispatch(self, tok: Token, i: int) -> int:
        """`MacroRunner._dispatch`, in its order."""
        raw, cmd, line = tok.text, tok.text.upper(), tok.line
        if cmd in ("CLICK", "^CLICK"):
            return self._click(i, line, _CTRL if cmd[0] == "^" else _NONE)
        if raw.startswith("^"):
            return self._caret(raw[1:].upper(), i, line)
        if len(cmd) == 1 and cmd in MacroRunner._TOOL_CODES:
            return self._tool(cmd, i, line)
        if len(raw) == 1 and raw in "123456":
            return self._tool(_LETTER[MacroRunner._DIGIT_TOOLS[int(raw) - 1]], i, line)
        if cmd in MacroRunner._ARROWS or cmd in ("ESC", "ENTER"):
            self._emit(_key_line(_stroke(keys.named(_KEY_NAME[cmd]))), line)
            return i
        if cmd in ("DEL", "DELETE"):
            self._emit(ast.AppCommand("DELETE", ()), line)
            return i
        if cmd in appcmd.COMMANDS and cmd not in appcmd.LEGACY_TOKEN:
            return self._app(cmd, i, line)
        handler = _WORDS.get(cmd)
        if handler is None:
            raise _NoForm("unknown command")
        return handler(self, i, line)

    def _tool(self, letter: str, i: int, line: int) -> int:
        self._flush_tool()
        self.pending = (letter, line)
        return i

    def _app(self, name: str, i: int, line: int) -> int:
        lo, _hi = appcmd.COMMANDS[name]
        args, i = self._take(i, lo)
        extra = _OPTIONAL.get(name, lambda rest: 0)(self.toks[i:])
        more, i = self._take(i, extra)
        self._emit(ast.AppCommand(name, tuple(t.text for t in [*args, *more])), line)
        return i

    def _caret(self, key: str, i: int, line: int) -> int:
        """`MacroRunner._caret`: the shortcuts, and the five that carry a value."""
        if key in MacroRunner._ARROWS:
            self._emit(_key_line(_stroke(keys.named(_KEY_NAME[key]), _CTRL)), line)
            return i
        if key in ("O", "+S", "+F"):
            (arg,), i = self._take(i, 1)
            name = {"O": "OPEN", "+S": "SAVE", "+F": "NEWFLOOR"}[key]
            self._emit(ast.AppCommand(name, (arg.text,)), line)
            return i
        nxt = self.toks[i] if i < len(self.toks) else None
        if key == "F":
            # the engine asks the plan whether the next token names a floor;
            # here a quoted token is a name, and so is a bare one that is
            # not itself a command
            if nxt is None or not (nxt.quoted or not _is_command(nxt.text)):
                raise _NoForm("a bare ^F (back to the default floor) has no "
                              "v2 form: @FLOOR needs the floor's name")
            self._emit(ast.AppCommand("FLOOR", (nxt.text,)), line)
            return i + 1
        if key == "H" and nxt is not None and nxt.text.lower() in ("on", "off"):
            self._emit(ast.AppCommand("SHUFFLE", (nxt.text.lower(),)), line)
            return i + 1
        if key in ("N", "A"):
            self._emit(ast.AppCommand({"N": "NEW", "A": "SELECTALL"}[key], ()), line)
            return i
        if key not in CARET_SHORTCUTS:
            raise _NoForm("unknown shortcut")
        if key == "+Z":             # redo; Ctrl+Shift+Z is not Redo on Windows
            key = "Y"
        mods = _CTRL | ({Mod.SHIFT} if key[0] == "+" else set())
        self._emit(_key_line(_stroke(keys.char(key[-1].lower()), mods)), line)
        if key == "S":
            self.notes.append(Note(line, "^S is now the real Ctrl+S: with no "
                                         "current file it opens Save As, where "
                                         "the existing engine skipped it"))
        return i

    # -- the mouse -----------------------------------------------------------
    def _chain(self, verb: str, pts, mods=_NONE) -> ast.Chain:
        return ast.Chain(verb, tuple(ast.Segment(mods, x, y) for x, y in pts))

    def _click(self, i: int, line: int, mods) -> int:
        (x, y), i = self._nums(i, 2)
        pts = [(x, y)]
        if self._word(i) == "DRAG":
            (ex, ey), i = self._nums(i + 1, 2)
            pts.append((ex, ey))
        self._emit(self._chain("CLICK", pts, mods), line)
        return i

    def _rclick(self, i: int, line: int) -> int:
        (x, y), i = self._nums(i, 2)
        self._emit(self._chain("RCLICK", [(x, y)]), line)
        self.notes.append(Note(line, "RCLICK is now a real right click: it "
                                     "opens the context menu, where the "
                                     "existing engine sent the button alone"))
        return i

    def _move(self, i: int, line: int) -> int:
        (x, y), i = self._nums(i, 2)
        self._emit(ast.Move(_NONE, x, y), line)
        return i

    def _drag(self, i: int, line: int) -> int:
        (x1, y1, x2, y2), i = self._nums(i, 4)
        self._emit(self._chain("CLICK", [(x1, y1), (x2, y2)]), line)
        return i

    def _press(self, i: int, line: int) -> int:
        (x, y), j = self._nums(i, 2)
        pts = [(x, y)]
        while self._word(j) == "MOVE":
            (mx, my), j = self._nums(j + 1, 2)
            pts.append((mx, my))
        if self._word(j) != "RELEASE":
            raise _NoForm("PRESS with no RELEASE after it: v2 never holds "
                          "the button between lines")
        (rx, ry), j = self._nums(j + 1, 2)
        if (rx, ry) != pts[-1]:
            pts.append((rx, ry))
        self._emit(self._chain("CLICK", pts), line)
        return j

    def _release(self, i: int, line: int) -> int:
        raise _NoForm("RELEASE with no PRESS before it")

    # -- keys and text -------------------------------------------------------
    def _pup(self, i: int, line: int) -> int:
        (x, y), i = self._nums(i, 2)
        cmds, strokes, last = [self._chain("RCLICK", [(x, y)])], [], None

        def flush():
            if strokes:
                cmds.append(_key_line(*strokes))
                strokes.clear()

        while i < len(self.toks):
            t = self.toks[i].text.upper()
            if t == "TYPE" and i + 1 < len(self.toks):
                flush()
                cmds.extend(_type_commands(self.toks[i + 1].text))
                i, last = i + 2, "TYPE"
            elif t in MacroRunner._MENU_KEYS:
                strokes.append(_stroke(keys.named(_KEY_NAME[t])))
                i, last = i + 1, t
            else:
                break
        if last not in ("ENTER", "ESC"):       # PUP closed what was left open
            strokes.append(_stroke(keys.named("Esc")))
        flush()
        for cmd in cmds:
            self._emit(cmd, line)
        return i

    def _type(self, i: int, line: int) -> int:
        (text,), i = self._take(i, 1)
        for cmd in _type_commands(text.text):
            self._emit(cmd, line)
        return i

    def _tool_word(self, i: int, line: int) -> int:
        (name,), i = self._take(i, 1)
        tool = MacroRunner._TOOL_NAMES.get(name.text.lower())
        if tool is None:
            raise _NoForm(f"unknown tool '{name.text}'")
        return self._tool(_LETTER[tool], i, line)

    def _wait(self, i: int, line: int) -> int:
        self._emit(ast.Wait(0.0), line)
        return i


#: the existing words that are not application commands -> their conversion.
#: With `appcmd.COMMANDS` this is EVERY `MacroRunner._cmd_*`; a test holds
#: the two together, so a word added there cannot go unconverted unnoticed.
_WORDS = {
    "RCLICK": _Converter._rclick, "MOVE": _Converter._move,
    "DRAG": _Converter._drag, "PRESS": _Converter._press,
    "RELEASE": _Converter._release, "PUP": _Converter._pup,
    "TYPE": _Converter._type, "TOOL": _Converter._tool_word,
    "WAIT": _Converter._wait,
}


def words() -> frozenset:
    """Every word of the existing language the converter has a rule for."""
    return frozenset(_WORDS) | (frozenset(appcmd.COMMANDS)
                                - frozenset(appcmd.LEGACY_TOKEN))


def _is_command(text: str) -> bool:
    cmd = text.upper()
    return (cmd in words() or cmd in ("CLICK", "ESC", "ENTER", "DEL")
            or cmd in MacroRunner._ARROWS or text.startswith("^")
            or (len(cmd) == 1 and (cmd in MacroRunner._TOOL_CODES or cmd in "123456")))


def convert(text: str) -> Conversion:
    """The existing-format macro `text` as v2. `Conversion.text` is what a
    rewritten file holds; `Conversion.problems` is everything that has no
    v2 form, each also a `; NOT CONVERTED` comment in that text."""
    return _Converter(text).run()
