"""Shadow mode -- check the live scene against the v5 invariants (P1.6).

Off by default. Set **`FP_VERIFY_DESIGN=1`** (or pass `--verify-design`, which
sets it) and the app rebuilds the `Design` at each quiescent point and raises if
an operation made the document worse. The suite runs unmodified either way,
which is the point: the acceptance is the WHOLE suite green twice, once with the
flag on. That is the gate that says the P1.4/P1.5 bridge is trustworthy.

**Quiescent points, not `scene.changed`.** Mid-operation the scene is legitimately
inconsistent -- walls added but the room not yet bound, a wall moved but the
rebuild not yet run. Checking there would report the editor's own intermediate
states as corruption. So the hooks are the three places the app itself considers
settled, plus one for the tests:

  * `MainWindow._commit_if_changed`, before the undo snapshot -- the app's own
    definition of "an operation finished" (cheap twelve);
  * save and load (all fifteen, `deep=True`, and load also REBASES -- see below);
  * `tests/conftest.py` teardown, because the 180 ms dirty timer never fires
    headless, so without it a test could mutate the scene and never verify.

**Baseline semantics: no operation may make the document worse.** A scene loaded
from a corrupt legacy file legitimately reports faults at rest -- `planc1.json`
sits at 17x I6 + 1x I11 + 5 unwelded ends the moment it opens. Verify mode must
not fire on that; it must fire on corruption this session INTRODUCED. So load
records a per-invariant-class fault profile as the baseline, and a later check
raises only when some class's count goes UP.

Deliberately coarse -- counts per class, never the message strings. Fault
messages embed ids, and P1.5's ids are canonical: they sort by geometry, so
moving one wall renumbers its neighbours and a string diff would light up on
every edit. Counting per class is stable under renumbering; a diff would not be.

**`unwelded_ends` is REPORTED, never raised on** -- see `REPORT_ONLY`. It was
specced to get the same baseline treatment as an invariant class; measuring it
showed that would be wrong on both counts. First, the schema forbids it outright:
`join_tol_in` is documented as "GESTURE TOLERANCE... **Never an invariant**: a
wall deliberately stopping 6" short of another is a legitimate design (a reveal,
a pilaster gap), and nothing may silently close it." Raising here would fail a
user for drawing a deliberate reveal. Second, it is a property of how the scene
DECOMPOSES walls, not of the document: `apply_design_to_scene` rebuilds planc1
from a byte-identical `Design` and the count goes 5 -> 15, because a wall split
at its junctions has more ends to be near things with. A metric that moves while
the document is provably unchanged cannot be a document invariant. The real weld
invariant is **I14**, at the 0.6" modelling tolerance, and it stays in the
raising set (deep).
"""
import os
import warnings

from floorplanner.design.bridge import design_from_scene
from floorplanner.design.validate import check
from floorplanner.vertex import split_count

ENV_VAR = "FP_VERIFY_DESIGN"
BASELINE_ATTR = "_design_baseline"
SPLIT_LOG_ATTR = "_vertex_split_log"      # [(operation, splits), ...]
_SPLIT_MARK = "_vertex_splits_at"

# keys carried in the profile for visibility but never raised on
REPORT_ONLY = ("unwelded_ends",)


class DesignVerificationError(AssertionError):
    """An operation introduced a v5 invariant violation.

    `AssertionError` rather than a bare exception because that is what this is:
    a failed internal consistency assertion about the editor's own state, and
    every occurrence is a live bug in current code (P1.6 says log it, do not
    paper over it)."""


def _flag() -> str:
    return os.environ.get(ENV_VAR, "").strip().lower()


def verify_enabled() -> bool:
    """True when shadow mode is on. Read per call, not cached at import, so a
    test can switch it with monkeypatch.setenv."""
    return _flag() not in ("", "0", "false", "no", "off")


def verify_deep() -> bool:
    """True for `FP_VERIFY_DESIGN=deep`: run all fifteen at EVERY quiescent
    point, not just save and load.

    Too slow to be the default -- that is the whole reason P1.2 split the
    invariants -- but it turns "the suite found nothing" from an absence into a
    measurement, since the cheap twelve exclude I5b, I11 and I14, and I11/I14
    are the two that caught the real corruption in `planc1.json`."""
    return _flag() in ("deep", "2", "all")


def fault_profile(target, deep=False, doc=None, walk_report=None) -> dict:
    """`{invariant class: count}` for the scene behind `target`, plus the
    report-only `unwelded_ends`. `{}` means a clean document.

    Pass `doc` (and its `walk_report`) to reuse a walk the caller has ALREADY
    done -- P2.3's `_commit_if_changed` builds the undo snapshot and verifies it
    at the same quiescent point, and walking the scene twice there would double
    the per-edit cost for nothing. Canonicalisation does not affect any
    invariant, so a canonical doc checks the same as a raw one.

    The walk's own weld warning is swallowed here: at a quiescent point it would
    fire on every check and drown the signal. `verify` re-raises it once, when
    the count actually moves."""
    rep = walk_report if walk_report is not None else {}
    if doc is None:
        rep = {}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            doc = design_from_scene(target, report=rep).to_dict()
    prof = {}
    for err in check(doc, deep=deep):
        cls = err.split()[0]                  # "I6", "I5b", "I14", ...
        prof[cls] = prof.get(cls, 0) + 1
    if rep.get("unwelded_ends"):
        prof["unwelded_ends"] = rep["unwelded_ends"]
    return prof


def rebase(target, deep=True) -> dict:
    """Record `target`'s current faults as the accepted baseline. Called at load
    (including undo's restore, which reinstates an already-verified state) and
    after a save. Deep by default: the baseline is set at exactly the moments
    P1.2 designated for the O(n^2) three."""
    prof = fault_profile(target, deep=deep) if verify_enabled() else {}
    setattr(target, BASELINE_ATTR, prof)
    return prof


def note_vertex_splits(target, where) -> int:
    """Record how many SPLIT-ON-WRITES happened during the operation just
    finished, and return the count (P3.1).

    Assigning `wall.p1` mints a fresh vertex and leaves any sharer behind, so
    every implicit split is a place where the code moved a coordinate when it
    may have meant to move a CORNER. The per-operation counts are exactly what
    P3.3 needs to decide which call sites become real vertex moves -- so this
    logs rather than warns: a drag legitimately splits, and a warning per drag
    would be noise, not signal."""
    now = split_count()
    prev = getattr(target, _SPLIT_MARK, None)
    setattr(target, _SPLIT_MARK, now)
    if prev is None or now <= prev:
        return 0
    log = getattr(target, SPLIT_LOG_ATTR, None)
    if log is None:
        log = []
        setattr(target, SPLIT_LOG_ATTR, log)
    log.append((where, now - prev))
    del log[:-200]                         # a ring: P3.3 wants the shape, not
    return now - prev                      # every drag since launch


def verify(target, where, deep=False, doc=None, walk_report=None):
    """Raise `DesignVerificationError` if `target` has MORE faults of any class
    than its baseline. A no-op unless shadow mode is on.

    With no baseline recorded (a scene built directly, never loaded), the first
    call establishes one instead of raising -- otherwise every fixture that
    legitimately builds an odd scene would fail on first sight. Test fixtures
    prime an empty baseline at setup, so within the suite this branch means
    "brand-new empty scene", and any fault a test then introduces is a
    regression against `{}`."""
    if not verify_enabled():
        return None
    note_vertex_splits(target, where)
    base = getattr(target, BASELINE_ATTR, None)
    prof = fault_profile(target, deep=deep or verify_deep(), doc=doc,
                         walk_report=walk_report)
    if base is None:
        setattr(target, BASELINE_ATTR, prof)
        return prof
    worse = {k: (base.get(k, 0), v) for k, v in prof.items()
             if v > base.get(k, 0)}
    noted = {k: worse.pop(k) for k in REPORT_ONLY if k in worse}
    for k, (b, n) in noted.items():
        base[k] = n                          # report once, not on every check
        warnings.warn(f"{where}: {k} rose {b} -> {n}. Not an invariant "
                      f"(the 9\" join tolerance is a gesture, not a rule) but "
                      f"worth knowing: some wall end now sits near a neighbour "
                      f"unwelded.", stacklevel=2)
    if worse:
        detail = ", ".join(f"{k}: {b} -> {n}" for k, (b, n) in
                           sorted(worse.items()))
        raise DesignVerificationError(
            f"{where}: the operation introduced v5 invariant violations "
            f"({detail}). Baseline {base or '{}'} was recorded at load. "
            f"This is a real bug in the current code, not a bridge artefact -- "
            f"see P1.6 in docs/V5_MIGRATION_PLAN.md.")
    return prof
