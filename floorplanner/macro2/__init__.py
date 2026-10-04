"""Macro language v2 -- docs/macro-spec/MACRO_SPEC.md.

A second macro format beside `floorplanner/macro.py`'s (Patrick's ruling,
docs/handoff/0212-report.md sec3: "side by side"). A macro whose first
non-blank line is `; fpmacro 2` is v2; anything else is the existing
language and runs on `MacroRunner`, untouched.

    text -> parse -> AST -> validate -> expand -> [InputEvent] -> Qt sink

This tranche (T1) is the language: everything up to the abstract events,
and the serializer. No Qt delivery yet.
"""
from floorplanner.macro2.ast import Macro, MacroError, Mod
from floorplanner.macro2.expand import InputEvent, expand
from floorplanner.macro2.parse import HEADER, ParseResult, is_v2, parse
from floorplanner.macro2.serialize import serialize
from floorplanner.macro2.validate import check, validate

__all__ = ["HEADER", "InputEvent", "Macro", "MacroError", "Mod", "ParseResult",
           "check", "expand", "is_v2", "parse", "serialize", "validate"]
