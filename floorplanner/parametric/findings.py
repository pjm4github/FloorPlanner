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
    # An ERROR the user may ACKNOWLEDGE and accept anyway, because resolving it
    # needs a change OUT ON THE PLAN, not in this dialog -- e.g. a dormer whose
    # host roof is too steep or faces the wrong way. The item draws red until
    # fixed; committing it keeps it on the plan to work on (Patrick, 2026-11-19).
    overridable: bool = False


def sort_findings(findings):
    """Worst first, in a stable order, for display."""
    return sorted(findings, key=lambda f: (_ORDER.get(f.severity, 99), f.rule_id))


def errors(findings):
    return [f for f in findings if f.severity == ERROR]


def hard_errors(findings):
    """Errors that genuinely block OK -- an overridable error does not."""
    return [f for f in findings if f.severity == ERROR and not f.overridable]


def overridable_errors(findings):
    return [f for f in findings if f.severity == ERROR and f.overridable]


def unresolved(findings):
    """What must be acknowledged before a commit: warnings, anything not
    evaluated, and errors the user may override to fix out on the plan."""
    return [f for f in findings
            if f.severity in (WARNING, NOT_EVALUATED)
            or (f.severity == ERROR and f.overridable)]


def blocks(findings):
    """True only when an error cannot be overridden -- a hard block on OK."""
    return bool(hard_errors(findings))


def needs_ack(findings):
    return bool(unresolved(findings))


def headline(findings):
    """One honest status line. It never says 'compliant': with any check
    unresolved the most it says is that the BASIC dimensions pass (spec sec
    6.1, the important rule)."""
    n_hard = len(hard_errors(findings))
    if n_hard:
        return f"{n_hard} error(s) -- cannot be accepted"
    n_over = len(overridable_errors(findings))
    if n_over:
        return (f"{n_over} issue(s) to fix on the plan; acknowledge to keep the "
                f"dormer on the plan and work on it there")
    n_open = len(unresolved(findings))
    if n_open:
        return (f"Basic dimensions pass; {n_open} additional check(s) pending "
                f"or unresolved")
    return "All evaluated checks pass"
