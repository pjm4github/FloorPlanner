# 0001 — ruling: docs refactor

**From:** Patrick · **To:** Claude Code · **2026-08-06**
**Report:** [`0001-report.md`](0001-report.md)

> Patrick's words, quoted rather than summarised. A summary of a decision is a
> second version of it.

---

## A — row 11 stays one file

> ROW 11 STAYS ONE FILE. One row, one file; the halves live in the body. My
> spec's "11a" example was wrong — 11a is not a row, it is prose inside row 11's
> cell, and splitting it would rewrite prose while moving it. Principle 1 holds.
> 12a IS a row and gets `0012a-<slug>.md`; the lettered-id support exists, it
> simply has one user.

## B — two-half rows

> `state` describes the WHOLE row: closed only when every half is. The Phase
> cell is preserved verbatim in `milestone_note:`. The taxonomy gains
> `status:partial` — I declared it fixed, this is the amendment. **Reason to
> record: GitHub has no half-closed state either, so this is not us working
> around our own format, it is a real property of the domain that any tracker
> will meet. Half-done is open.**

## C — milestone

> `milestone: null` is legal; the gate validates only non-null values against
> the Status table; the raw cell goes verbatim into `milestone_note:`. Your
> reasoning is the deciding one: **a lint that fails on correctly-recorded
> history is a lint that gets disabled.**

## D — dates and shas

> `null` except where the cell states one verbatim, with `docs/defects/README.md`
> saying why. And do NOT derive from git: **git dates the record's first
> appearance, not the defect, and a derived date is worse than null because it
> looks authoritative.**

## E — sites

> Verbatim strings, gate does not resolve them. Same principle as C: **a
> register that records a deleted site is doing its job, and a check that failed
> on it would punish accuracy.**

## F — rank

> Add `rank: <ordinal as found>`, and have `INDEX.md` offer both orders. But the
> README must say what rank actually is: **the original review ranked roughly
> the first twenty-one by blast radius, and everything after was APPENDED, not
> ranked. Preserve the order; do not claim it means more than it does.**

## G — standing notes

> `docs/defects/README.md` under "Standing notes", verbatim. **REQUIRED: the
> plan's pointer is updated in the SAME sub-commit. A pointer and its target
> must never be split across commits.**

## H — root clutter

> Do NOT touch any untracked file. Add `_tot.png` and `Screenshot*.png` to
> `.gitignore`, so the class is closed going forward. That is the only part with
> git value. Leave every untracked file exactly where it is. Patrick deletes
> them himself if he wants to; they are his scratch files and there is no reason
> for an agent to be near them. Your catch that moving them to `docs/evidence/`
> would have ADDED them to the repo goes in the log — **"clean the root" would
> have made the repository larger.**

*(Executed with one correction: `_tot.png` needed no entry — `_*.png` already
covered it. Only `Screenshot*.png` was added.)*

## I — superseded headers

> Document-superseded: `CODE_REVIEW.md`, `CANVAS_ITEM_REFACTOR_PLAN.md`.
> Completed: `REFACTOR_PLAN.md`, `TODO.md` — *"Completed - the work described
> here shipped; the current plan is V5_MIGRATION_PLAN.md"*. REQUIRED in
> `docs/README.md`: **superseded/ holds UNIQUE material, not ignorable
> material** — name CANVAS_ITEM's group/drag trace and `test_zz*` forensics
> specifically. Also note in the two completed headers that they raised the root
> clutter finding that step 8 now closes.

*(Executed with one correction, reported: the clutter finding is raised at
`CODE_REVIEW.md:88` and carried at `REFACTOR_PLAN.md:202`. `TODO.md` raises
nothing. The note went on the two documents that actually raised it — one
completed, one document-superseded — rather than on the two the ruling named.)*

## J — `tools/ref_audit.py`

> APPROVED as a scope addition, and it was the right thing to ask rather than
> assume. Freeze the pattern set in code; step 9 re-runs the same module; step
> 7's resolver is the same code. **A retyped grep at step 9 would be the
> copied-number failure.**

## K — both approved

> The verbatim proof is a byte comparison against `git show HEAD:docs/...` with
> endings normalised once. `--docs` is its OWN LANE, invoked explicitly, its
> verdict quoted beside the full-mode trailer. **Changing the trailer's shape
> partway through a branch would make its own trailers incomparable, which is
> the census-discrepancy class again.**

---

## Ruling 1 — the record body

> Body is `## Record` (cell verbatim) plus `## Site` and `## Milestone`, also
> verbatim. The five sections are documented in `defects/README.md` as the shape
> NEW records take and the shape a record takes WHEN NEXT REVISED — **so the
> corpus converges naturally instead of being converted by fiat.**
>
> - Principle 1 is the integrity guarantee of this entire refactor. The
>   byte-identical receipt at every other step is what makes it checkable;
>   "content preserved, structure imposed" is weaker and you were right to name
>   it as weaker rather than offer it evenly.
> - The five sections were MY invention for records going forward. Back-fitting
>   them onto 50 rows of interleaved prose would be inventing structure that is
>   not in the evidence.
> - GitHub does not care about body headings.

## Ruling 2 — the taxonomy widens

> BOTH LABELS APPROVED. `area:tooling` (CI, packaging, `tools/`) and
> `area:viewer`. **A label that lies is worse than a label that is missing**,
> which is the same honesty that made `type:` worth introducing.

## Addition 1 — D45 reclassified

> By your own definitions: gap = "something true goes unreported or unchecked";
> task = "correct as written but must change". `_edge_wall` is not unreported —
> it is recorded, justified, and known. It works, and it must eventually change.
> That is task. New counts: **38 defect / 6 gap / 1 limit / 5 task.** Your other
> three debatable calls stand, including D14/D15 as defects — **an operation
> that wastes time is doing something wrong, not merely doing it slowly.**

## Addition 2 — a new step 10

> D40 migrates AS THE REGISTER HAS IT — open, "not yet built" — and you were
> right to refuse to change state during a move. Then close it in its own commit
> with the receipt. **Record the general rule beside it: a content correction
> discovered during a structural move is NEVER folded into the move; it is the
> next commit. That keeps the move's verbatim receipt intact and makes the
> correction visible instead of buried in a diff of relocations.**

*(D3 was found later under the same rule and joins step 10.)*

---

## Part 3 — the two questions held back

**Progress-log pointers — NO, keep them separate, but LINK.**

> The progress log is CURATED — what happened, why, what proved it. A handoff
> file is RAW — the exchange itself. Different genres, different readers.
> Collapsing them makes the log inherit the exchange's verbosity, and the log is
> already 4,356 lines. Instead: a progress entry CITES its handoff when one
> exists — one line, `handoff: 0042`. Same relationship the log already has with
> `docs/evidence/`: cite the artifact, do not inline it.

**Truth ownership — recorded, not decided.**

> Write it into `docs/defects/README.md` as an explicitly open decision, with the
> framing **"they must not both drift"**. On disk, not in the thread. That is
> the project's own rule and it applies here.
