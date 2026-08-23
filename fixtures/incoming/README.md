# `fixtures/incoming/` — the intake

**Patrick drops plans here that break, misbehave, or look wrong.** Nothing more
is asked of him: no triage, no naming of the fault, no check that it still
reproduces. A plan that is annoying is enough reason to put it here.

## The contract

**Files here are UNCHARACTERISED.**

* **No test may reference a file in `incoming/`.** Not by name, not by glob.
* **No parametrized test may sweep this directory.**
* Each file may be accompanied by a `.txt` note of the same stem saying what
  the user was doing when it went wrong. Free prose — a sentence is plenty.

That is the whole contract, and it exists so that dropping a file here can
never turn the gate red or block a commit. **The moment a broken plan costs
someone a working tree, people stop reporting broken plans.**

## Why this directory exists at all

`examples/` is the **frozen clean corpus**: `tests/test_schema.py` parametrizes
over a filesystem glob of `examples/*.json`, so a plan dropped there changes the
collected test count and, if it trips an invariant, turns the gate red and —
through the commit hook — **blocks every commit in the repository**. That is
[D51](../../docs/defects/0051-the-census-depends-on-the-working-tree.md), and it
has now happened twice: to `fragment2room.json` on 2026‑08‑08, and to
`wiscaway2026-08-09R.json` on 2026‑08‑09, which arrived carrying seven real
violations and stopped the gate dead.

`fixtures/` is the next step in: **characterised** failures, each with a README
entry naming exactly what it violates and why it is kept. But characterising a
plan takes a measurement, and requiring one at drop time puts the work on the
wrong person at the wrong moment.

**So there are three tiers, and the rule is one sentence each:**

| | |
|---|---|
| `examples/` | the frozen clean corpus. **Nothing imperfect enters it.** |
| `fixtures/` | **characterised** failures, each named in `../README.md` |
| `fixtures/incoming/` | **uncharacterised** intake. No test may reach it. |

## Triage moves a file OUT of here — four exits, and only four

Every file leaves by exactly one of these, and the exit is **named** when it is
taken:

1. **PROMOTED to `fixtures/`** as a characterised failure, with an entry in
   [`../README.md`](../README.md) naming exactly what it violates and why it is
   retained, **and a fail-first test that references it**. A promotion with no
   test is a file that has been moved, not triaged.
2. **PROMOTED to `fixtures/` as a measurement subject**, with an entry in
   [`../README.md`](../README.md) naming exactly what it is evidence FOR and
   which census, script, or record consumes it — **no test names it, and none
   is owed**. This is not exit 1 with the test skipped: the file's value is a
   number a census reads, not a fault a test reproduces, so nothing in the
   suite references it by design. [`0063-ruling.md`](../../docs/handoff/0063-ruling.md)
   §4 — the clause exit 1 assumed ("the only reason to keep an intake file is
   as a test input") does not hold for `crossfloor-snap-2026-08-17.json`,
   which `docs/evidence/orthogonality_census.py` had already been counting
   while it sat here.
3. **DELETED as a duplicate**, *naming the fixture that already covers it*. "We
   have one of these" is only a reason if you can say which one.
4. **DELETED as no-defect-found**, *naming what was checked*. The value is the
   negative result: without the list, the next identical report starts from
   nothing.

## A file here is NEVER edited or repaired

Not tidied, not re-saved, not opened-and-saved by the app, not "cleaned up
slightly" on the way to `fixtures/`. **If it is promoted, it is frozen in the
state it arrived in**, and its freeze test asserts it still fails the way its
README entry documents.

The reason is the whole value of this directory: these plans record what
*ordinary use* did, and nobody curated them. A repaired intake file is a
synthetic plan wearing a real one's name — and this project has already measured
that synthetic scenes do not reach the branches real damage reaches (three were
tried for D57 and none got there).

## The deadline, and it is a reporting rule rather than a timer

**`incoming/` is listed in every handoff, with the age of each file.**

**A file that has sat here across two handoffs without triage is itself a
finding**: it means evidence is arriving faster than it is being read. That gets
**said out loud in the handoff**, not left to accumulate quietly — the failure
mode this guards against is a directory that fills up while everyone assumes
someone else is reading it.

An untriaged file is not a problem in itself. An untriaged file **nobody has
mentioned in two handoffs** is.

## The contract is enforced, not asserted

**A contract nobody checked is a comment.** `tests/test_fixture_layout.py`
carries the positive control: it writes a deliberately invalid plan into this
directory, runs the corpus collectors over it, and fails if any of them picks it
up. Measured when the directory was created — a plan with seven violations sat
here through a full green gate.
