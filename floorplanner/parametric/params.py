"""Parameter definitions for parametric furnishings -- pure Python, no Qt.

A kind describes each editable value ONCE, as a `ParamSpec`; the generic
dialog builds its form from the list, and the same list fills defaults when a
stored state is read. Adding a parameter to a kind is one more `ParamSpec`.
"""
import math
from dataclasses import dataclass, field

FLOAT, INT, ENUM, BOOL = "float", "int", "enum", "bool"


# -- pitch, as degrees or rise-per-12 (Patrick, 2026-11-19) -------------------
# A pitch is stored canonically as RISE PER 12 in (the dormer's `pitch_12`).
# These convert that canonical value to and from a degree reading so a field
# can be shown and edited in either unit.
def pitch12_to_deg(rise_per_12: float) -> float:
    return math.degrees(math.atan2(float(rise_per_12), 12.0))


def deg_to_pitch12(deg: float) -> float:
    return 12.0 * math.tan(math.radians(float(deg)))


def _identity(v):
    return float(v)


@dataclass(frozen=True)
class UnitMode:
    """One selectable unit for a FLOAT field. `to_display`/`from_display`
    convert between the field's CANONICAL stored value and this unit's shown
    value; the rest size the spinbox while this unit is active."""
    key: str                         # remembered id, e.g. "in12" / "deg"
    label: str                       # the dropdown item, e.g. "in 12"
    suffix: str                      # the spinbox suffix, e.g. " in 12"
    minimum: float
    maximum: float
    step: float
    decimals: int
    to_display: object = _identity   # canonical -> this unit
    from_display: object = _identity  # this unit -> canonical


def pitch_unit_modes(lo_12=0.5, hi_12=24.0):
    """The two pitch units over a canonical `pitch_12` range [lo_12, hi_12]."""
    return (
        UnitMode("in12", "in 12", " in 12", lo_12, hi_12, 0.5, 2),
        UnitMode("deg", "degrees", " deg",
                 round(pitch12_to_deg(lo_12), 1), round(pitch12_to_deg(hi_12), 1),
                 0.5, 1, pitch12_to_deg, deg_to_pitch12),
    )


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
    # A FLOAT field may offer alternate display UNITS (e.g. pitch as rise/run
    # OR degrees). The value stays CANONICAL in `state`; the dialog shows a
    # dropdown and converts. `unit_setting` names the session preference that
    # remembers the choice across dialogs (config.pitch_units).
    unit_modes: tuple = field(default_factory=tuple)
    unit_setting: str = ""

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
