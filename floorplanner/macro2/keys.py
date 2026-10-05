"""Key names of the macro language v2 (MACRO_SPEC.md sec6.2) -- ONE table,
read by validation, expansion, the serializer and the recorder.

No Qt here: a key resolves to the NAME of a `Qt.Key` member (`"Key_Return"`)
or, for a character in the Latin-1 range, to that character; the Qt sink
turns either into the real `Qt.Key`.
"""
from __future__ import annotations

from dataclasses import dataclass

from floorplanner.macro2.ast import Key, Mod

#: canonical spelling -> Qt.Key member name. The writer emits these spellings.
_NAMED = {
    "Enter": "Key_Return", "Tab": "Key_Tab", "Esc": "Key_Escape",
    "Space": "Key_Space", "Backspace": "Key_Backspace", "Delete": "Key_Delete",
    "Insert": "Key_Insert", "Up": "Key_Up", "Down": "Key_Down",
    "Left": "Key_Left", "Right": "Key_Right", "Home": "Key_Home",
    "End": "Key_End", "PgUp": "Key_PageUp", "PgDn": "Key_PageDown",
    "Shift": "Key_Shift", "Ctrl": "Key_Control", "Alt": "Key_Alt",
    "Meta": "Key_Meta",
}
_NAMED.update({f"F{n}": f"Key_F{n}" for n in range(1, 25)})
_BY_LOWER = {name.lower(): name for name in _NAMED}

#: the modifier keys, by canonical name
MODIFIER_KEYS = {"Shift": Mod.SHIFT, "Ctrl": Mod.CTRL, "Alt": Mod.ALT,
                 "Meta": Mod.META}
MOD_KEY_NAME = {m: name for name, m in MODIFIER_KEYS.items()}

#: characters that are syntax on a KEY line and so are written in braces
ESCAPED = "+^!#;{}"


@dataclass(frozen=True)
class KeySpec:
    """A resolved key. `name` is the canonical spelling for a named key and
    None for a character key; `char` is the character for a character key;
    `qt_name` is the `Qt.Key` member name for a named key; `mod` is set for
    the four modifier keys."""
    name: str | None
    char: str | None
    qt_name: str | None
    mod: Mod | None = None

    @property
    def ident(self):
        """A hashable identity for the held-key set."""
        return self.name if self.name is not None else self.char.upper()


def resolve(key: Key):
    """The `KeySpec` for `key`, or None when a braced name is unknown.

    A bare character names a physical key and letters are case-insensitive.
    A braced single character (`{x}`, `{+}`, `{;}`, `{{}`, `{}}`) is the
    same as the bare character. Any other braced text must be in the table,
    matched case-insensitively."""
    if not key.named:
        return KeySpec(None, key.text, None)
    canon = _BY_LOWER.get(key.text.lower())
    if canon is not None:
        return KeySpec(canon, None, _NAMED[canon], MODIFIER_KEYS.get(canon))
    if key.text == " ":                 # `{ }`: the space key, by its name
        return KeySpec("Space", None, _NAMED["Space"])
    if len(key.text) == 1:
        return KeySpec(None, key.text, None)
    return None


def write(key: Key) -> str:
    """The canonical spelling of `key` on a KEY line (sec10). An unknown
    name is written back as it came, so an invalid macro still round-trips."""
    spec = resolve(key)
    if spec is None:
        return "{" + key.text + "}"
    if spec.name is not None:
        return "{" + spec.name + "}"
    if spec.char in ESCAPED:
        return "{" + spec.char + "}"
    return spec.char.lower()


def qt_name(ident: str):
    """The `Qt.Key` member name for an expansion key identity
    (`KeySpec.ident`), or None when the identity is a character."""
    return _NAMED.get(ident)


def named_keys():
    """Every canonical key name."""
    return list(_NAMED)


def named(name: str) -> Key:
    """A `Key` for a canonical name -- the recorder's and converter's door."""
    return Key(True, name)


def char(ch: str) -> Key:
    return Key(False, ch)
