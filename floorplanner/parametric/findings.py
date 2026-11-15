"""Validation findings for parametric furnishings -- pure Python, no Qt.

A validator returns a list of `Finding`s; the dialog decides what they allow.
The five severities are the spec's (STAIRS_FURNISHING_SPECIFICATION.md sec
6.2), and the one rule that matters most is that NOT_EVALUATED is never shown
as a pass: a check nobody ran is not a check that succeeded.
"""
from dataclasses import dataclass

ERROR = "ERROR"                    # blocks OK
WARNING = "WARNING"                # needs explicit acknowledgement
NOT_EVALUATED = "NOT_EVALUATED"    # needs explicit acknowledgement
ADVISORY = "ADVISORY"              # shown, never blocks
PASS = "PASS"

SEVERITIES = (ERROR, WARNING, NOT_EVALUATED, ADVISORY, PASS)
_ORDER = {s: i for i, s in enumerate(SEVERITIES)}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    message: str
    actual: float | None = None
    limit: float | None = None
    field: str | None = None       # the parameter to focus, when there is one


def sort_findings(findings):
    """Worst first, in a stable order, for display."""
    return sorted(findings, key=lambda f: (_ORDER.get(f.severity, 99), f.rule_id))


def errors(findings):
    return [f for f in findings if f.severity == ERROR]


def unresolved(findings):
    """What must be acknowledged before a commit: warnings and anything not
    evaluated."""
    return [f for f in findings if f.severity in (WARNING, NOT_EVALUATED)]


def blocks(findings):
    return bool(errors(findings))


def needs_ack(findings):
    return bool(unresolved(findings))


def headline(findings):
    """One honest status line. It never says 'compliant': with any check
    unresolved the most it says is that the BASIC dimensions pass (spec sec
    6.1, the important rule)."""
    n_err = len(errors(findings))
    if n_err:
        return f"{n_err} error(s) -- cannot be accepted"
    n_open = len(unresolved(findings))
    if n_open:
        return (f"Basic dimensions pass; {n_open} additional check(s) pending "
                f"or unresolved")
    return "All evaluated checks pass"
