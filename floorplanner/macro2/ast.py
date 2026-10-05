"""The macro language v2 AST -- plain dataclasses, no ANTLR and no Qt types
(docs/macro-spec/MACRO_SPEC.md sec8.1: "keep the rest of the code independent
of ANTLR types"). `parse.py` builds these; `validate.py`, `expand.py` and
`serialize.py` read them.

Positions are 1-based lines and 0-based columns, as ANTLR reports them.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field


class Mod(enum.Enum):
    """A modifier prefix (sec3.5). The VALUE is the prefix character; the
    declaration order is the canonical writing order (sec10) and the press
    order (sec7)."""
    SHIFT = "+"
    CTRL = "^"
    ALT = "!"
    META = "#"


MOD_ORDER = (Mod.SHIFT, Mod.CTRL, Mod.ALT, Mod.META)
MOD_BY_CHAR = {m.value: m for m in Mod}


@dataclass(frozen=True)
class MacroError:
    """One positioned error -- syntax or validation (sec8.3)."""
    line: int
    col: int
    message: str

    def __str__(self) -> str:
        return f"line {self.line}:{self.col} {self.message}"


@dataclass(frozen=True)
class Key:
    """One key as written: a bare character (`a`) or a braced name
    (`{Enter}`, `{+}`). `text` is the character, or the name without its
    braces. Resolution to a real key is `keys.resolve`."""
    named: bool
    text: str
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass(frozen=True)
class Segment:
    """A point with the modifiers that apply while reaching it."""
    mods: frozenset
    x: float
    y: float


@dataclass(frozen=True)
class Chain:
    """`[mods] HEAD x y { [mods] DRAG x y }` (sec5.2). `segments[0]` is the
    head; `verb` is the head keyword, which fixes the button and `double`."""
    verb: str
    segments: tuple


@dataclass(frozen=True)
class Move:
    mods: frozenset
    x: float
    y: float


@dataclass(frozen=True)
class Wheel:
    mods: frozenset
    dx: float
    dy: float


@dataclass(frozen=True)
class TypeText:
    text: str


@dataclass(frozen=True)
class Stroke:
    mods: frozenset
    key: Key


@dataclass(frozen=True)
class KeyPress:
    strokes: tuple


@dataclass(frozen=True)
class KeyDown:
    key: Key


@dataclass(frozen=True)
class KeyUp:
    key: Key


@dataclass(frozen=True)
class Wait:
    ms: float
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass(frozen=True)
class AppCommand:
    """`@NAME arg ...` (sec14): the application acts directly. `args` are
    the argument texts with any double quotes removed."""
    name: str
    args: tuple
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass(frozen=True)
class Line:
    """`[TOOL] [command]` (sec4). At least one of the two is present."""
    tool: str | None
    command: object | None
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)


@dataclass(frozen=True)
class Macro:
    lines: tuple


#: head keyword -> (button, double click) (sec5.2)
CLICK_VERBS = {
    "CLICK": ("left", False),
    "RCLICK": ("right", False),
    "MCLICK": ("middle", False),
    "DCLICK": ("left", True),
    "XCLICK1": ("back", False),
    "XCLICK2": ("forward", False),
}
