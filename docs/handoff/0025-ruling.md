# 0025 — ruling: the check PASSES, the merge needs a PR, and what follows

**Patrick's check on [`0024-report.md`](0024-report.md), 2026‑08‑15. Quoted
rather than summarised:**

> **The check looks great. Its all set on those items.**

---

## 1. THE CHECK IS PASSED — all three rows, and row 3's open question with them

**Rows 1, 2 and 3 pass.** None fell back to *explicitly unchecked*, which was
[`0022`](0022-ruling.md) §3's fallback and is not needed.

**Row 3 carried a live question — *"is `porcelain` right?"* — and the pass
answers it.** `swim_spa` and `whirlpool` keep `porcelain` bodies with `water`
regions. **Recorded as answered rather than left implicit**, because a question
inside a checked row is easy to lose in a yes.

**ONE THING FOR THE PROGRESS ENTRY: name the plan the check was run on.** The
render Patrick judged shows **five bathroom items and 284 triangles**, not the
three-item [`../../fixtures/enclosure-form-check.json`](../../fixtures/enclosure-form-check.json)
(212). **That is broader coverage, not a problem** — the pass covers `shower`,
`walk_in_shower`, `glass_shower`, `sauna` and `whirlpool` rather than three of
them. But [`0016`](0016-ruling.md) §6's standing rule cuts both ways: **a check
RESULT names its plan too**, or the record cannot say later what was seen.

## 2. THE MERGE CONDITION IS MET — BUT THERE IS NO PR, AND NO CI HAS SEEN THIS

**Measured:** `git ls-remote --heads origin` returns **no
`d74-vessel-enclosure-split`**. The branch has never been pushed. Three commits
sit local-only.

The tier table reads **"PR, *then* stop"** — in that order — and both
[`0021`](0021-report.md) and [`0024`](0024-report.md) describe themselves as
stopped at the AMBER gate. **The stop happened; the PR did not.**

> **THE SUBSTANCE WAS NEVER AT RISK — nothing merged, and the check still
> governed. WHAT WAS LOST IS THE CI SIGNAL.** The local gate is green on one
> machine. **The Linux, py3.10/py3.13 and DEEP-invariant jobs have not run on
> this work at all** — and CI running the deep gate is the entire content of
> [D27](../defects/0027-ci-never-runs-the-deep-gate-and.md), which was filed and
> closed to obtain exactly that.

**So:** push the branch, open the PR, **merge on green CI plus this check.** If
CI disagrees with the local gate, that disagreement is a finding and comes back
as a report — it does not get resolved by re-running until green.

**And the general form, which is why this is in a ruling and not a note:**

> ### AN AMBER STOP WITHOUT A PR IS A STOP THAT SKIPPED ITS OWN EVIDENCE STEP.
> The PR is not ceremony around the check — it is what puts the work in front of
> the *other* gate, the one that runs on hardware this machine is not.

## 3. WHAT CLOSES WITH THE MERGE

* **The vessel/enclosure split** — `bathtub`, `swim_spa`, `whirlpool` are
  `vessel`; the three showers and `sauna` stay `enclosure`. Categorical, not a
  threshold.
* **Materials attach to PARTS, not items** — body and region, with the form
  deciding which is which.
* **[D75](../defects/0075-a-recessed-floor-feature-is-not-representable.md)**
  (recessed floor feature — accepted limit),
  **[D76](../defects/0076-an-opaque-mesh-inside-a-translucent-body-does.md)**
  (no compositing through a translucent body) and
  **[D77](../defects/0077-fp3d-py-shot-reports-success-on-a-failed.md)**
  (`--shot` reports success on a failed save) filed.

**D76 and D77 stay open and unscheduled.** Both are real, neither blocks the
queue, and **D77 in particular should be read by whoever next writes an evidence
render** — it silently produces a missing artifact where a check expects one.

## 4. WHAT COMES NEXT — three items, in this order

**ONE — THE THREE ARTWORK REDRAWS. AMBER, one check for all three.**
`glass_shower` (all strokes, still the only box fallback in 95), `shower` (a
bare filled rect), `walk_in_shower` (a bench, now that the extruder places one
correctly). **The brief is [`0016`](0016-ruling.md) §2–3:** these three are
indistinguishable because identity is carried by footprint, a scalar — the fix
is an internal region that differs in KIND. **Now unblocked**, because the
extruder they flow into is correct as of this merge, which is why they waited.

**TWO — [`0019`](0019-ruling.md)'s STATUS BOARD. GREEN, and its read-back comes
first.** Small, and it fixes a table that is currently lying about P5.2.

**THREE — GRID SNAP. Its read-back comes before any code**, unchanged since the
snapshot: clause-by-clause EXISTS/PARTIAL/ABSENT, thresholds with reasons, the
shift modifier audit, the angle convention already in the geometry code, and
Ctrl's disposition. **The largest daily-use improvement left on the board.**

## 5. `boat_trailer` COMES OFF THE ARTWORK LIST

**Ruled, having been deferred twice.** Its form is `vehicle` — the one generator
[`0015`](0015-ruling.md) deliberately did not retire — and its failure is **five
disconnected filled fragments**, which is what a plan symbol of an open frame
gives you. **No redraw turns an open frame into a closed body without drawing a
trailer that is not there.**

> **IT IS THE VEHICLE LOFT'S, AND THE LOFT NEEDS A READ-BACK BEFORE IT STARTS** —
> same bar as grid snap and parameterisation. Design at
> [`../../floorplanner/viewer/VIEWER_NOTES.md`](../../floorplanner/viewer/VIEWER_NOTES.md) §5.
> **Not scheduled here**, and not to be picked up as artwork by anyone tidying
> the list.

**Worth recording plainly: `boat_trailer` has now survived three checks without
once appearing in the scene being checked.** That is not a fault of any of them;
it is why [`0016`](0016-ruling.md) §6 made naming the plan a standing rule.

## 6. TIER

**The merge is AMBER and its condition is met** — this check plus green CI.
**Item ONE is AMBER**, items TWO and THREE are **GREEN work behind read-backs**.
