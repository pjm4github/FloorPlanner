# 0084 — ruling: `T` was dropped, and the interlock guards the wrong quantity

**On [`0083-report.md`](0083-report.md).** Item C is built, gated GREEN at
`collected=852`, PR #37 open and correctly stopped. **§2's chain receipt is
exactly what [`0082`](0082-ruling.md) §3 asked for, on the real plan it named,
with a real RED and a real GREEN.** §4 and §5 are two findings produced by
running the thing, reported rather than smoothed — **both are right, and §5 is
worse than the report treats it as.**

**Three things must change before Patrick's check, and one of them is the
safety bound this whole item turned on.**

---

## 1. `T = 1/16″` WAS DROPPED, AND THE READ-BACK I RULED SAYS IT SHOULD NOT HAVE BEEN

[`0083`](0083-report.md) §1: *"`T = 1/16″` is not spent in this delivery; the
near-axis census IS the candidate set."*

**[`0066`](0066-ruling.md) §3, in a boxed heading:** *"**T = 1/16″.** Below it,
moving a vertex cannot change any dimension a residential plan expresses. Above
it, **the correction is a real edit and the user must see it before it
happens**"* — with a table reading **auto-repairable 32, reported-not-touched
31.**

**And [`0079`](0079-report.md) §2(c), the read-back [`0082`](0082-ruling.md)
ruled, says it in its own words:**

> *"`T` bounds which walls are CANDIDATES in the first place, not whether a
> candidate is skipped."*

> ### THE INFERENCE WAS THAT MEASURING CONFLICTS ACROSS ALL 63 MEANT REPAIRING ALL 63. IT DOES NOT. A SUPERSET MEASUREMENT IS NOT A CANDIDACY DECISION.
>
> [`0082`](0082-ruling.md) §1 accepted the **conflict counts**. It did not
> re-open candidacy, and it could not have — [`0079`](0079-report.md) had just
> restated the bound correctly.

**Measured, my own implementation, the same corpus:**

| | under `T` | over `T` |
|---|---:|---:|
| `farmplaceBIGmultifloor` | 0 | 4 |
| `planc1.v5` / `planc1TestV5` | 5 / 5 | 1 / 1 |
| `symmetricP1` | 1 | 1 |
| `wiscaway2026-08-09R` | 5 | 3 |
| `crossfloor-snap` | 16 | 21 |
| **TOTAL** | **32** | **31** |

**32 and 31 — [`0066`](0066-ruling.md) §3's own table, to the wall.**

**AND THIS IS WHY IT MATTERS, NOT A TECHNICALITY:**

> **Without `T`, the largest correction this repair applies is 3.000″. With
> `T`, it is 0.0409″.** Patrick's check is *"does the drawing still look like
> your drawing?"* **Three inches on a floor plan is visible. A twenty-fourth of
> an inch is not.** The bound is the thing that makes the check answerable.

**RESTORE IT.** Candidates are the near-axis walls whose displacement is
`< 1/16″`. The other 31 are **reported with their values and not moved** — which
is also what makes `w24` (3.000″) untouchable for the right reason: **size, not
conflict.**

## 2. THE INTERLOCK GUARDS INVARIANTS AND NOT ORTHOGONALITY — AND THAT GAP IS MINE

[`0083`](0083-report.md) §5, measured: `w54` is **refused**, and moves anyway —
its shared vertex `v54` is relocated by `w53`'s repair — **from 0.0131″ off axis
to 4.679° off axis.**

> ### A REPAIR WHOSE PURPOSE IS ORTHOGONALITY LEFT A WALL 4.679° CROOKED, AND EVERY GUARD PASSED.
>
> `check()` saw no new invariant. The conflict predicate protects walls that are
> **exactly** on axis; `w54` was near-axis and refused, so it is protected by
> neither. **The differential I specified at [`0082`](0082-ruling.md) §2 —
> *"this operation made nothing worse"* — was applied to invariants and never to
> the quantity the operation exists to improve.** That omission is mine.

**RULED, and it is the same differential pointed at the right metric:**

> **After the repair, no wall's deviation from its nearest axis may be greater
> than before it ran.** A wall that would be worsened undoes the repair that
> worsened it. **Post-condition on the working copy, exactly like the invariant
> key comparison, and checked the same way.**

**§1 does most of the work here and it is worth seeing why.** `w53` moves
**0.1371″** and `w55` **0.3409″** — **both over `T`, so under §1 neither is a
candidate and neither ever touches `v54`.** The 4.679° does not happen. **But
the mechanism survives at a bounded size:** a `T`-sized move on a neighbour of
length `L` tilts it by `asin(T/L)` — on `wiscaway`'s 6.00″ walls that is still
**0.6°**. **So §1 caps the damage and §2 catches it. Both, not either.**

## 3. WHOLE-FILE ROLLBACK COSTS 37 OF 63 TO AVOID TWO COLLISIONS

[`0083`](0083-report.md) §4's census reconciles — **63 = 22 + 4 + 37** — and the
table producing its own headline is the discipline
[`0060`](0060-report.md) established. **"61 of 63" is correctly withdrawn.**

**But one clause of §4's reasoning is wrong and the record should not carry
it:** *"`crossfloor-snap` … was never among the 20 plans `0066`'s corpus census
walked."* **It was.** [`0066`](0066-ruling.md) §2's 63-value list includes its
walls; that is why the totals reconcile at 63 and why §1's table above shows its
37. **"61 of 63" did not fail from missing coverage — [`0079`](0079-report.md)
§2(b) ran the predicate over all 63. It failed because neither ruling modelled
the ROLLBACK, which is a whole-file effect no per-wall count can see.** Right
finding, wrong cause.

**RULED: a collision costs the colliding wall, not the file.** Undo the repair
that introduced the new invariant key; keep the rest. Whole-document rollback
was my wording at [`0082`](0082-ruling.md) §2 and **59% of the corpus's
candidates is too much to pay for two `I14`s.**

**Re-measure under §1 first — it may be moot.** Of `crossfloor`'s 37, only **16**
survive `T`, and `w21` — named in both collisions — is **over `T` at 0.998″**,
so it is no longer moved at all. **Run the census again with `T` restored before
building anything here; if the rollback no longer fires, this item closes
itself.**

**The algorithm is Code's** — per-wall check, or apply-all-then-bisect if
`check()` per wall is too slow. **The guarantee is what is ruled.**

## 4. THE MAILBOX IS ON A FEATURE BRANCH FOR THE SIXTH TIME — AND I SAID I WOULD STOP REPEATING THE RULE

```
git cat-file -e main:docs/handoff/0082-ruling.md   ->  NOT ON MAIN
git cat-file -e main:docs/handoff/0083-report.md   ->  NOT ON MAIN
both exist only on wall-orthogonality-repair
```

**[`0063`](0063-ruling.md) §6, my own words:** *"Third time of asking. **If it
does not hold on the next exchange, the rule is wrong about how Code works and I
should rule a different one rather than repeat this one.**"*

**It did not hold. So I am not repeating it.**

> ### THE RULE BECOMES A GATE, BECAUSE THIS PROJECT HAS WRITTEN DOWN WHAT ACTUALLY FIXES THIS CLASS: *"the only two things that have ever fixed this class here are generation and a gate that fails."*
>
> **The pre-commit hook refuses any commit that ADDS a `docs/handoff/NNNN-*.md`
> on a branch other than `main`.** Not a rule anyone has to remember at the
> moment they are thinking about code. **The natural order becomes forced:
> write the report, commit it on `main`, then branch.**

**GREEN**, one check in machinery that already exists and already has 18 tests.
**Exempt merge commits** (a branch that takes `main` in acquires mailbox files
legitimately), and **test both cells** — refused on a branch, allowed on `main`.

**And land `0082`/`0083` on `main` now, doc-only, as
[`0063`](0063-ruling.md) §6 ordered for the pair before them.** The branch keeps
the code.

## 5. WHAT IS ACCEPTED, AND IT IS MOST OF IT

**§2's chain receipt is the best receipt in this thread.** A real plan, a real
as-loaded RED (`w56` at **3.25°**, worse than it started, nothing refused), a
real re-evaluated GREEN (`w54`/`w57` refused, every other chain wall exactly 0).
**That is what [`0082`](0082-ruling.md) §3 asked for and it was built without
argument.**

`_invariant_key`, the withdrawn refuse-to-start, the rollback returning the
original document rather than a matching copy, `close_gap` reused as the
relocation primitive, the menu item reachable from nowhere else, 19 tests
including the stable-key differential in both directions — **all accepted.**

**And §5 was found by running and reported against a clause
[`0082`](0082-ruling.md) had just reaffirmed.** Reporting a measurement that
contradicts the reviewer's own fresh ruling, instead of testing around it, is
the behaviour this channel exists to produce.

## 6. TIER AND ORDER

| | | |
|---|---|---|
| 1 | **§4 — land `0082`/`0083` on `main`, doc-only** | **GREEN.** First; it is the only thing lost by waiting |
| 2 | **§4 — the hook check** | **GREEN.** Its own commit, revertible alone |
| 3 | **§1 — restore `T` as the candidacy filter** | **AMBER.** It changes what the repair produces — and it is the merge condition's own premise |
| 4 | **§2 — the orthogonality post-condition** | **AMBER**, same commit as 3 |
| 5 | **§3 — re-run the census under `T`; per-wall rollback only if it still fires** | **GREEN** to measure, **AMBER** to change |
| 6 | **PR #37** | **AMBER, stays open. Not merged, and not checked until 3–5 land** |

**PATRICK'S CHECK IS UNCHANGED AND IS NOW WORTH WAITING FOR:**

> Run the repair on the `L2.dxf` source plan, re-export, count what Chief flags
> against the 75 — **and does the drawing still look like your drawing?**

**Do not run it on PR #37 as it stands.** With `T` dropped, the answer to the
second half could be *no* for a reason the code is about to stop having —
**a 3″ wall move that §1 removes.** Checking it now would spend the one thing
this project is short of on a build that is one commit from being different.

**PRs #34, #35, #36 are still open on the same queue and unaffected by any of
this.**
