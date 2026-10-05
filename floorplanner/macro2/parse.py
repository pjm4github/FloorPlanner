"""Macro language v2: text -> AST (MACRO_SPEC.md sec8.1).

The ANTLR parser generated from `docs/macro-spec/grammar/*.g4` is used as
written; this module is the only one that touches ANTLR types. Syntax
errors are COLLECTED, never printed (sec8.3), each with its line and column.
"""
from __future__ import annotations

from dataclasses import dataclass

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from floorplanner.macro2 import ast
from floorplanner.macro2._generated.MacroLexer import MacroLexer
from floorplanner.macro2._generated.MacroParser import MacroParser

HEADER = "; fpmacro 2"


def is_v2(text: str) -> bool:
    """sec11: a macro whose first non-blank line is `; fpmacro 2` is v2."""
    for line in str(text).splitlines():
        if line.strip():
            return line.strip() == HEADER
    return False


@dataclass(frozen=True)
class ParseResult:
    macro: ast.Macro
    errors: tuple            # of ast.MacroError, in source order

    @property
    def ok(self) -> bool:
        return not self.errors


class _Collector(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(ast.MacroError(line, column, f"syntax error: {msg}"))


def _mods(ctx, errors):
    """The modifier set of a `modifiers` context (None = no prefix). A
    repeated prefix (`++CLICK`) is a validation error (sec3.5, sec8.3),
    reported here because this is where the repeat is still visible."""
    out = set()
    if ctx is None:
        return frozenset()
    for tok in ctx.MOD():
        m = ast.MOD_BY_CHAR[tok.getText()]
        if m in out:
            errors.append(ast.MacroError(
                tok.symbol.line, tok.symbol.column,
                f"repeated modifier '{tok.getText()}'"))
        out.add(m)
    return frozenset(out)


def _kmods(tokens, errors):
    out = set()
    for tok in tokens:
        m = ast.MOD_BY_CHAR[tok.getText()]
        if m in out:
            errors.append(ast.MacroError(
                tok.symbol.line, tok.symbol.column,
                f"repeated modifier '{tok.getText()}'"))
        out.add(m)
    return frozenset(out)


def _key(ctx) -> ast.Key:
    tok = ctx.start
    if ctx.KNAMED() is not None:
        return ast.Key(True, tok.text[1:-1], tok.line, tok.column)
    return ast.Key(False, tok.text, tok.line, tok.column)


def _num(tok) -> float:
    return float(tok.text)


def _point(ctx):
    return _num(ctx.x), _num(ctx.y)


def _command(ctx, errors):
    if ctx.mouseChain() is not None:
        c = ctx.mouseChain()
        x, y = _point(c.point())
        segs = [ast.Segment(_mods(c.modifiers(), errors), x, y)]
        for d in c.dragSegment():
            x, y = _point(d.point())
            segs.append(ast.Segment(_mods(d.modifiers(), errors), x, y))
        return ast.Chain(c.clickVerb().getText(), tuple(segs))
    if ctx.move() is not None:
        c = ctx.move()
        x, y = _point(c.point())
        return ast.Move(_mods(c.modifiers(), errors), x, y)
    if ctx.wheel() is not None:
        c = ctx.wheel()
        return ast.Wheel(_mods(c.modifiers(), errors), _num(c.dx), _num(c.dy))
    if ctx.typeText() is not None:
        # sec8.2: TEXT is exactly the text; the separator space is already
        # consumed by the lexer, and no TEXT child means empty text
        t = ctx.typeText().TEXT()
        return ast.TypeText(t.getText() if t is not None else "")
    if ctx.keyPress() is not None:
        strokes = [ast.Stroke(_kmods(s.KMOD(), errors), _key(s.keyName()))
                   for s in ctx.keyPress().keyStroke()]
        return ast.KeyPress(tuple(strokes))
    if ctx.keyDown() is not None:
        return ast.KeyDown(_key(ctx.keyDown().keyName()))
    if ctx.keyUp() is not None:
        return ast.KeyUp(_key(ctx.keyUp().keyName()))
    if ctx.appCommand() is not None:
        c = ctx.appCommand()
        tok = c.APPCMD().symbol
        args = tuple(a.getText()[1:-1] if a.ASTRING() is not None else a.getText()
                     for a in c.appArg())
        return ast.AppCommand(tok.text[1:], args, tok.line, tok.column)
    c = ctx.wait()
    return ast.Wait(_num(c.ms), c.ms.line, c.ms.column)


def parse(text: str) -> ParseResult:
    """Parse a v2 macro. The AST is built only when there is no syntax
    error -- a tree ANTLR had to repair is not a macro anyone wrote."""
    collector = _Collector()
    lexer = MacroLexer(InputStream(str(text)))
    lexer.removeErrorListeners()
    lexer.addErrorListener(collector)
    parser = MacroParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(collector)
    tree = parser.macro()
    if collector.errors:
        return ParseResult(ast.Macro(()), tuple(collector.errors))
    errors = []
    lines = []
    for lc in tree.line():
        tool = lc.toolSelect().getText() if lc.toolSelect() is not None else None
        cmd = _command(lc.command(), errors) if lc.command() is not None else None
        lines.append(ast.Line(tool, cmd, lc.start.line, lc.start.column))
    return ParseResult(ast.Macro(tuple(lines)), tuple(errors))
