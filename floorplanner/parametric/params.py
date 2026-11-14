"""Parameter definitions for parametric furnishings -- pure Python, no Qt.

A kind describes each editable value ONCE, as a `ParamSpec`; the generic
dialog builds its form from the list, and the same list fills defaults when a
stored state is read. Adding a parameter to a kind is one more `ParamSpec`.
"""
from dataclasses import dataclass

FLOAT, INT, ENUM, BOOL = "float", "int", "enum", "bool"


@dataclass(frozen=True)
class ParamSpec:
    key: str                        # the key in the furnishing's `state`
    label: str
    kind: str                       # FLOAT, INT, ENUM or BOOL
    default: object = None
    unit: str = ""
    minimum: float = 0.0
    maximum: float = 100000.0
    step: float = 1.0
    decimals: int = 3
    choices: tuple = ()             # ((value, label), ...) for an ENUM
    choices_fn: object = None       # values -> choices, when they depend on others
    enabled_fn: object = None       # values -> bool; None = always editable
    shown_fn: object = None         # (values, derived, context) -> what a
    #                                 DISABLED field displays (a linked rise,
    #                                 an automatic riser count)
    tooltip: str = ""

    def choices_for(self, values):
        if self.choices_fn is not None:
            return tuple(self.choices_fn(values))
        return tuple(self.choices)

    def enabled(self, values):
        return True if self.enabled_fn is None else bool(self.enabled_fn(values))


def coerce(spec, value):
    """`value` as the spec's type, or the spec's default when it cannot be."""
    try:
        if spec.kind == FLOAT:
            return float(value)
        if spec.kind == INT:
            return int(value)
        if spec.kind == BOOL:
            return bool(value)
    except (TypeError, ValueError):
        return spec.default
    return value


def resolve(specs, state):
    """Every spec's value: the stored one when present, else its default.
    Keys no spec names are carried through, so a newer file's extra
    parameters survive a round trip through an older definition."""
    out = dict(state or {})
    for spec in specs:
        if spec.key in out and out[spec.key] is not None:
            out[spec.key] = coerce(spec, out[spec.key])
        else:
            out[spec.key] = spec.default
    return out
