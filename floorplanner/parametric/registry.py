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


def register(definition):
    _KINDS[definition.kind] = definition
    return definition


def get(kind):
    return _KINDS.get(kind)


def is_parametric(kind):
    return kind in _KINDS


def kinds():
    return sorted(_KINDS)
