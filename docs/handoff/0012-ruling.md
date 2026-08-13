# 0012 — ruling: prism order, and two rules the read-back earned

**Patrick's, 2026‑08‑12**, on
[`0012-readback-prism-outlines.md`](0012-readback-prism-outlines.md). Quoted
rather than summarised, per this directory's own convention.

---

## 1. PRISM ORDER — build, re-measure, then decide

> **PRISM ORDER, ruled from your numbers: BUILD PRISM, THEN RE-MEASURE, THEN
> DECIDE. Do not build the four furniture generators first. If prism covers 16
> of 18 on those forms, most of them may never need writing, and building them
> first guarantees work that prism would have made redundant. Vehicle-first
> survives as you say — 3 of 10 means prism does not reach it, which is a better
> reason than item count ever was.**

**This amends ruling 0010's item TWO.** That said *"the remaining generators in
descending item count"*, which put `vehicle` first for a reason that has now been
replaced by a better one, and put `enclosure` (7), `seat` (6), `bed` (4) and
`basin` (1) behind it as work to be done. **They are no longer scheduled work.**
They are a question to be re-asked after prism ships, against a re-measurement
rather than against the count.

**The sequence, stated as steps so it cannot be collapsed:**

1. **Build `prism`.** Make it the fallback in place of `box`.
2. **RE-MEASURE.** Not "look at it and feel good about it" — the read-back's
   tiers exist and can be re-run against the built generator.
3. **THEN decide** whether `seat`, `bed`, `basin` and `enclosure` still want
   generators of their own. **`vehicle` does not wait on that decision** — 3 of
   10 is already the answer for it.

**The stopping rule this replaces is worth naming.** 0010's *"stop when the
remainder is not worth a function"* asked for a judgement to be made **in
advance**, on counts. This one defers the same judgement until there is a
measurement to make it against.

## 2. The three NONE items are AUTHORING work, and stay separate

> **The three NONE items are an authoring fix and belong with the furnishings
> authoring work, not with the generators. Keep them separate so a code task
> does not acquire an artwork dependency.**

`glass_shower`, `bicycle`, `boat_trailer`. Each needs a filled body added to its
symbol in `_gen_assets.py` — **two edits and a command**, the cost the 0010
census measured. **They are not prism's blockers and prism does not wait on
them**: prism ships against 25 items that have something to extrude, and these
three keep falling back to a box until their artwork changes, which is exactly
what a fallback is for.

## 3. Two rules the read-back earned, both now in the working agreement

### IDENTITY NEEDS A CATEGORICAL CHANNEL, NOT A SCALAR ONE

> **My ruling named decoration as the channel but said nothing about decoration
> having AXES, and your first cut showed why that mattered: fence and railing as
> the same ladder differing only in FINENESS. Fineness is a scalar, and a scalar
> cannot carry identity between two similar things — which is exactly the reason
> thickness failed one level up. Fill versus stroke is CATEGORICAL, and
> categorical distinctions survive at working zoom while scalar ones dissolve
> into it.**
>
> **So the general form, and it now has two instances: IDENTITY NEEDS A
> CATEGORICAL CHANNEL, NOT A SCALAR ONE.**

**And with it: KEEP THE FILLED POST. It is not beyond the ruling, it completes
it.** Recorded in [D74](../defects/0074-thickness-cannot-carry-wall-identity-and-the.md)
and in [`../WORKING_AGREEMENT.md`](../WORKING_AGREEMENT.md) with both instances —
thickness (two types share a real thickness) and fineness (two ladders at
different pitches are one ladder at any working zoom).

### A CRITERION THAT SPLITS TWO STRUCTURALLY IDENTICAL CASES IS MEASURING THE WRONG THING

> **RECORD THE THRESHOLD FINDING TOO, and it may be the more portable one: a
> criterion that splits two structurally identical cases is measuring the wrong
> thing, and THE AGGREGATE NEVER SHOWS IT. Lawnmower usable and snowblower not,
> from one 25% line, and 21-of-28 looks perfectly respectable from above. The
> practice that catches it: inspect the items either side of the line, not the
> count. Add it beside the positive-control rule — same family, different
> failure.**

Filed beside the positive control, as instructed. **The pairing is the content:**
the positive control catches an instrument reporting **nothing**; this catches
one reporting a **plausible something**, which is the harder case because the
output looks like an answer.

## 4. The snapshot's staleness is now a gate condition

> **MAKE THE SNAPSHOT STALENESS A GATE CHECK. You are right that generation and
> a failing gate are the only things that have ever fixed this class here, and
> the re-cut you just did is the third time it has gone stale. `gate.py --docs`
> already exists: add one assertion that the snapshot's recorded HEAD equals the
> actual HEAD. Cheap, deterministic, and it converts a convention nobody keeps
> into a condition nobody can commit past. That closes it permanently rather
> than for one more cycle.**

**Implemented — and it went into FULL MODE as well as `--docs`, which the
instruction did not ask for and the purpose required.** Reported here because
the gap between the two is a real finding about the tool:

> **`--docs` is not part of the full gate and never has been.** `main()` returns
> from `_docs()` before the test lanes run, so `--docs` prints its own verdict
> and **writes no `.gate-result.json`** — and the commit hook reads only that
> file. A check placed solely in the docs lane would have been **one more thing
> nobody runs**, which is precisely the failure it was commissioned to close.

So `_snapshot_head()` is called by both, and the full-mode census line now
carries `snapshot=current|stale`.

**Two assertions, not one:** the marker must match the tip, **and** the §1
`main` row must carry the same hash — otherwise the marker becomes a number
bumped mechanically while the prose beside it goes on lying.

**What it cannot do, stated because an unstated boundary reads as coverage:** it
cannot check that anyone re-read the content. **It makes the file impossible to
ignore, not impossible to update carelessly.** And it puts every commit that
changes the recorded state on a one-line treadmill — **which caps drift at one
commit, where it reached eight.**

**Five outcomes are driven by `tests/test_gate.py`**, and the live wiring was
checked by pointing the marker at the old head: `Gate-Census: … snapshot=stale`,
`Gate-Verdict: RED`. **A check nobody can demonstrate failing is the same
species as the convention it replaces.**
