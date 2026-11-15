"""Which furnishing kinds are parametric, and how each one behaves.

A kind registers ONE `ParametricKind`. Everything generic -- the dialog, the
double-click, the save and the load -- goes through this table, so a new
parametric furnishing is a new definition and nothing else. Pure Python: a
kind's Qt preview is imported only when a dialog actually asks for it.
"""

_KINDS = {}


class ParametricKind:
    """The contract. Subclass it, set `kind` and `title`, implement the rest."""

    kind = ""
    title = "Properties"

    def specs(self):
        """The editable parameters, in form order: a list of `ParamSpec`."""
        raise NotImplementedError

    def normalize(self, state):
        """A complete, type-clean copy of a stored state."""
        raise NotImplementedError

    def evaluate(self, values, context):
        """(derived, findings). `derived` is the kind's calculated result, or
        None when the values cannot be calculated at all."""
        raise NotImplementedError

    def summary(self, values, derived, context):
        """[(label, text)] -- the read-only CALCULATED block."""
        return []

    def make_preview(self, parent=None):
        """A QWidget with `set_data(values, derived, context)`, or None."""
        return None

    def to_state(self, values):
        """What is WRITTEN to the plan file for an accepted parameter set.
        The default writes everything; a kind whose parameters mostly sit at
        their defaults overrides this to write only what differs."""
        return dict(values)

    def footprint(self, state):
        """(width, depth) of the plan footprint for a stored state, or None
        when the kind keeps its catalog footprint."""
        return None

    def plan_symbol(self, state):
        """Plan-symbol primitives DRAWN FROM THE PARAMETERS, or None when the
        kind keeps its catalog symbol (0338: an island shows its own slots
        and seats)."""
        return None


def register(definition):
    _KINDS[definition.kind] = definition
    return definition


def get(kind):
    return _KINDS.get(kind)


def is_parametric(kind):
    return kind in _KINDS


def kinds():
    return sorted(_KINDS)
