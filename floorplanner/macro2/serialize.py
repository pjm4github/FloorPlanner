"""Macro language v2: AST -> canonical text (MACRO_SPEC.md sec10).

Writers ALWAYS produce this form: `; fpmacro 2` first, one space after a
tool letter, modifiers attached to their keyword in the order `+ ^ ! #`,
single spaces, numbers to two decimals with trailing zeros removed, named
keys in the table's spelling, bare key characters in lowercase, LF endings
and a final newline. Comments are not part of the AST and are not written.

Round trip: `serialize(parse(serialize(ast))) == serialize(ast)`.
"""
from __future__ import annotations

from floorplanner.macro2 import ast, keys
from floorplanner.macro2.ast import MOD_ORDER
from floorplanner.macro2.parse import HEADER


def number(v: float) -> str:
    """Up to 2 decimal places, trailing zeros and a trailing `.` removed;
    `-0` is written `0`."""
    s = f"{float(v):.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def mods(ms) -> str:
    return "".join(m.value for m in MOD_ORDER if m in ms)


def command(cmd) -> str:
    if isinstance(cmd, ast.Chain):
        parts = []
        for i, seg in enumerate(cmd.segments):
            word = cmd.verb if i == 0 else "DRAG"
            parts.append(f"{mods(seg.mods)}{word} {number(seg.x)} {number(seg.y)}")
        return " ".join(parts)
    if isinstance(cmd, ast.Move):
        return f"{mods(cmd.mods)}MOVE {number(cmd.x)} {number(cmd.y)}"
    if isinstance(cmd, ast.Wheel):
        return f"{mods(cmd.mods)}WHEEL {number(cmd.dx)} {number(cmd.dy)}"
    if isinstance(cmd, ast.TypeText):
        return f"TYPE {cmd.text}" if cmd.text else "TYPE"
    if isinstance(cmd, ast.KeyPress):
        return "KEY " + " ".join(mods(s.mods) + keys.write(s.key)
                                 for s in cmd.strokes)
    if isinstance(cmd, ast.KeyDown):
        return "KEYDOWN " + keys.write(cmd.key)
    if isinstance(cmd, ast.KeyUp):
        return "KEYUP " + keys.write(cmd.key)
    if isinstance(cmd, ast.Wait):
        return "WAIT " + number(cmd.ms)
    raise TypeError(f"not a v2 command: {cmd!r}")


def line(ln: ast.Line) -> str:
    parts = []
    if ln.tool is not None:
        parts.append(ln.tool)
    if ln.command is not None:
        parts.append(command(ln.command))
    return " ".join(parts)


def serialize(macro: ast.Macro) -> str:
    return "\n".join([HEADER, *(line(ln) for ln in macro.lines)]) + "\n"
