# 0282 — report: "undo by command" — a correction first: P6.b as built would not make undo faster; the walk after a restore removed (0.34 → 0.26–0.28 s); the reload's remedy put to him

**Code, 2026‑10‑17.** His words after [`0281`](0281-report.md):

> *"go ahead with undo by command"*

## 0. A CORRECTION, MINE

In the conversation after [`0280`](0280-report.md) I wrote that undo by
command (P6.b) "is what would take" the reload and the walks away, and
would make Ctrl+Z "nearly instant". **That was wrong.** The P6.b classes
(`floorplanner/commands.py`, merged and dormant since 2026‑08) are a
**memento stack**: each `GestureCommand` holds the document before and
after a gesture and applies one by `_restore_state` — the very reload
today's undo does. The park record says so ([`ROADMAP.md`](../ROADMAP.md)
§ "PHASE 6 IS PARKED": "what P6.b built is a memento stack (documents
before/after)"). Wiring it (P6.c, P6.d) would give **named** undo steps
and a `QUndoStack`; Ctrl+Z would cost the same.

What removes the reload is an undo that applies **only what changed**,
and there are two ways to that (§3). Both are larger and riskier than
anything in this run; that is his to choose, so it is not built.

## 1. WHAT WAS BUILT — on `undo-restore-walk`, ONE commit, AMBER

What did not depend on that choice: the two document walks around a
restore (~80 ms each, measured at 0280).

* **The walk after a restore is gone.** `_restore_state` now takes the
  restored state as the committed state instead of walking the scene to
  re-derive it. That is exact because `load_data` is a faithful apply:
  `snapshot(load(state)) == state` holds on his R1 plan and on
  `symmetricP1`, `sample_plan.v5` and `site_demo` (pinned by a test). If a
  plan ever round-tripped inexactly, the next settle would file one extra
  step to an equivalent state — never lose one.
* **The walk before an undo stays — tried, and refuted by the suite.** It
  folds in a pending edit. Skipping it when the settle timer is quiet
  looked safe and is not: `scene.changed` arrives on a *later* turn of the
  event loop, so an edit and a Ctrl+Z in the same turn find the timer
  quiet with a change pending — three tests in `tests/test_undo.py` edit
  and undo exactly so, and failed. Reverted, with the reason in the code.

| On his R1 plan (unprofiled) | 0280 | Now |
|---|---|---|
| Ctrl+Z | 0.34 s | 0.26–0.28 s |
| Redo | 0.34 s | 0.26–0.29 s |

(3.6 s before 0280.) What remains: the walk before the undo (~80 ms), the
reload (~105 ms), the first repaint (~75 ms).

## 2. RECEIPT

`tests/test_undo_fast.py` (10): three plans round-trip exactly through a
restore; a restore neither alters the state it was given nor files a
spurious step at the next settle, and redo brings the edit back.
`tests/test_undo.py` unchanged and green. `--quick` passed (1661); gate
GREEN. `undo-after-0282-R1.txt` beside 0280's probe output.

## 3. FOR HIS WORD — THE RELOAD

The reload (~105 ms) and most of the first repaint (~75 ms) go only if an
undo stops recreating the whole plan. Two ways:

**A. Restore by difference** (recommended). Keep today's snapshot
undo — its states are already exact — but apply a restore as a
**difference**: compare the target document with the current one and
rebuild only the records that differ (a moved wall, its vertices, the
rooms that hold them; a furnishing; an opening), leaving every unchanged
item in place. One mechanism for every gesture, no inverses to write, the
same tested states; the risk is in the partial apply (shared vertices,
room bindings, groups), which a fallback to the full reload contains: any
difference it cannot apply cleanly reloads as today. Estimated: undo of a
small edit on his plan ~0.1 s. Medium size; AMBER.

**B. Operation-inverse commands** (P6's original idea). Each gesture
records how to reverse itself. Fastest in principle, but every gesture
needs a correct inverse, and this codebase has measured itself not having
them (D61, D62, D65, D66, named in `commands.py`'s own docstring). Large;
not recommended.

**C. Wire P6.b as built** (P6.c, P6.d): named undo steps ("Undo Delete",
"Undo Group") and a `QUndoStack`; no speed change. Small to medium.

**Carried:** unchanged from [`0281`](0281-report.md).
