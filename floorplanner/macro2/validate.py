"""Macro language v2: validation (MACRO_SPEC.md sec8.3).

The whole macro is validated BEFORE anything runs, and every error is
reported with its position. Syntax errors and repeated modifiers come from
`parse`; this adds the three that need the AST: an unknown tool letter, an
unknown `{Name}`, and a negative `WAIT`.
"""
from __future__ import annotations

from floorplanner.macro2 import ast, keys
from floorplanner.macro2.parse import ParseResult, parse


def _keys_of(cmd):
    if isinstance(cmd, ast.KeyPress):
        return [s.key for s in cmd.strokes]
    if isinstance(cmd, (ast.KeyDown, ast.KeyUp)):
        return [cmd.key]
    return []


def validate(macro: ast.Macro, tools) -> list:
    """Validation errors of a parsed macro. `tools` is the set of tool
    letters the application has."""
    errors = []
    for ln in macro.lines:
        if ln.tool is not None and ln.tool not in tools:
            errors.append(ast.MacroError(
                ln.line, ln.col, f"unknown tool letter '{ln.tool}'"))
        for key in _keys_of(ln.command):
            if keys.resolve(key) is None:
                errors.append(ast.MacroError(
                    key.line, key.col, f"unknown key name '{{{key.text}}}'"))
        if isinstance(ln.command, ast.Wait) and ln.command.ms < 0:
            errors.append(ast.MacroError(
                ln.command.line, ln.command.col, "WAIT cannot be negative"))
    return errors


def check(text: str, tools) -> ParseResult:
    """Parse AND validate: one result whose `errors` holds every syntax and
    validation error, in source order. Nothing may run unless it is empty."""
    res = parse(text)
    if any(e.message.startswith("syntax error") for e in res.errors):
        return res
    errors = sorted([*res.errors, *validate(res.macro, tools)],
                    key=lambda e: (e.line, e.col))
    return ParseResult(res.macro, tuple(errors))
