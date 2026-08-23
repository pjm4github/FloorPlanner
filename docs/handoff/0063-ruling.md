# 0063 — ruling: the fix is right, the receipt for it is not in the suite

**On [`0062-report.md`](0062-report.md).** Fail-first test built and confirmed
RED, fix applied, gate GREEN at `collected=779`, branch `cross-floor-align-fix`
at `d9c44de`, **AMBER and correctly stopped.**

**Read from the tree, not from the report:** the diff, the test, every caller of
the changed helper, both READMEs, and `.gate-result.json`.

---

## 1. ACCEPTED — and the differential is the strongest receipt this thread has produced

```
BEFORE   AssertionError: a new wall's endpoint snapped to an open end on a hidden floor
         Obtained: 500.0        <- the hidden floor's coordinate
         Expected: 505.0        <- where it was drawn
AFTER    same test, same assertion, passes
```

**That is not a test written after a fix and asserted to have failed. It is two
runs of one predicate against two states of the code, and the numbers are the
mechanism**: 505 → 500 is the free coordinate being taken by a wall on
`"Upper"` while `"Upper"` reports `floor_display_mode() == "hidden"`.

**And the test calls `win.view._align_to_wall(...)` directly rather than
restating its arithmetic** — the same one-definition discipline
[`0057`](0057-ruling.md) §1 credited in [`0056`](0056-report.md), applied again
without being asked.

**The fix is the shape [`0061`](0061-ruling.md) §4 ordered, verified line by
line:**

```python
active = active_floor()
for w in sc.items():
    if not isinstance(w, WallItem) or w is exclude or w.floor != active:
        continue                          # align only to the active floor
    for end in (w.p1, w.p2):
        if not wall_endpoint_open(sc, end, ignore=(w, exclude), floor=active):
```

**`wall_endpoint_open`'s new `floor=` is more than [`0061`](0061-ruling.md)
asked for and it is right.** A wall on another floor could previously mark an
active-floor end as *joined* by coincidental proximity — **the same fault
inverted**, suppressing a legitimate snap rather than causing an illegitimate
one. **Nobody reported that one. It was reasoned from the mechanism**, which is
how the second half of a bug gets found.

## 2. §3'S REFUSAL IS CORRECT, AND IT USED MY OWN DISTINCTION AGAINST ME PROPERLY

[`0061`](0061-ruling.md) §4 said the four other unfiltered sites *"should be
fixed in the same pass."* [`0062`](0062-report.md) §3 declines, quoting
[`0061`](0061-ruling.md) §2 back:

> *"`hit_candidates` (`items(pos)`) and the rubber-band select (`items(area,
> ...)`) are both position/area-scoped queries of the same kind `0061` itself
> found masked … Fixing them has no fail-first receipt behind it."*

**Sustained.** [`0061`](0061-ruling.md) §2 spent a section establishing that
`items(pos)` is masked and `items()` is not, then §4 asked for both classes in
one pass **as if the distinction had not just been drawn.** *A ruling that
argues a boundary and then orders work across it has contradicted itself in the
space of two sections*, and [`0062`](0062-report.md) caught it.

**Named, not dropped** — §5 carries them forward. **[`0061`](0061-ruling.md)
§4's "masked is not fixed" still stands as a reason to do them eventually; it is
not a reason to do them without a receipt.**

## 3. THE FINDING — THE FAIL-FIRST RECEIPT LIVES IN THE TRANSCRIPT, NOT IN THE SUITE

**Measured:** `test_align_to_wall_does_not_snap_to_a_hidden_floor` is the **only
test in the suite that calls `_align_to_wall`.** Its single assertion is

```python
assert aligned.x() == pytest.approx(pt.x())
```

**— an assertion that nothing happened.**

> ### THE RED RUN PROVED THE SCENE COULD SNAP. NOTHING IN THE COMMITTED SUITE PROVES IT STILL CAN.
>
> **Concrete failure:** let `active_floor()` later return a name no wall
> carries, or let `wall_endpoint_open(floor=…)` over-reject. Then `best is
> None` on every iteration, `_align_to_wall` returns `pt` unchanged, **wall
> alignment is silently dead across the whole application — and this test is
> green.** So is the gate.

**This is [D43](../defects/0043-sweep-the-suite-for-negative-assertions-and.md)
exactly, in the shape D43 itself enumerates (`== before`):** *"absence and
prevention are indistinguishable in the result … which makes negative
assertions the place vacuity concentrates."* **And D43 names why no tool
catches it: `tools/gate.py`'s vacuity check catches tautology only.** GREEN at
779 is not evidence against this.

**It is also [`0022`](0022-ruling.md) §2 — the positive control for zero —
which [`0056`](0056-report.md) applied unprompted to a brand-new instrument and
was credited for in [`0057`](0057-ruling.md) §1.** **The same author, the same
week, the same rule, not applied here.** Not a lapse of care: the RED run *felt*
like the control, and it was — **for one afternoon, in a terminal nobody kept.**

**OWED, AND IT IS TWO LINES IN THE TEST THAT ALREADY EXISTS:** on the same
scene, put an open end at the same coordinate on the **ACTIVE** floor and assert
the endpoint **DOES** take it.

```python
# the control: same geometry, active floor -- alignment must still fire
sc.addItem(near)                       # (500, 700)-(620, 700), DEFAULT_FLOOR
assert win.view._align_to_wall(None, QPointF(505, 300), horizontal=True) \
          .x() == pytest.approx(500.0)
```

**Then the test can only pass if the filter DISCRIMINATES**, rather than if
alignment has stopped working. **One test, two assertions, and the differential
that only existed in `0062`'s prose becomes a thing the gate re-proves on every
run.**

## 4. THE `incoming/` EXIT — the right outcome, one reason that cannot tell before from after, and a README that now has a counter-instance

**The outcome is accepted.** The file is real corpus evidence, the defect was
reproduced by a minimal scene, and **[`0062`](0062-report.md) §4 states the
split openly** rather than picking one of my two exits and hoping. **A report
that names a third answer and argues it beats a report that forces itself into
the ruling's menu.**

**But one of its two reasons is vacuous by tautology**, and it is the project's
own doctrine:

> *"`docs/evidence/orthogonality_census.py` sweeps `fixtures/` recursively
> regardless of subdirectory, so its own numbers are unaffected by the move."*

**`rglob("*.json")` — measured, `orthogonality_census.py:30`. The census was
ALREADY counting this file while it sat in `incoming/`**; that is where
[`0058`](0058-report.md)'s 948 came from and where
[`0059`](0059-ruling.md) §4's outlier paragraph came from. **A clause true
identically before and after the move cannot be a reason for the move.** The
move stands on its other leg — clearing the intake — **and that leg is
sufficient**, so nothing is lost by saying so.

**AND THE CONTRACT NOW HAS A COUNTER-INSTANCE IN THE TREE.**
`fixtures/incoming/README.md`, exit 1, verbatim:

> *"**PROMOTED to `fixtures/`** … **and a fail-first test that references it**.
> A promotion with no test is a file that has been moved, not triaged."*

**`fixtures/README.md`'s new entry says, in its own words, "No test names it."**

> ### THE ACTION IS RIGHT AND THE RULE IS WRONG — SO THE RULE IS WHAT CHANGES.
>
> The clause assumes the only reason to keep an intake file is as a test input.
> **This file is kept as a MEASUREMENT SUBJECT** — the corpus's orthogonality
> outlier, cited across four handoffs by a census, named by no test and needing
> none.
>
> **OWED, GREEN, and it is one row:** add the fourth exit — *promoted as corpus
> evidence, no test, with the census or record that consumes it named.* **A
> contract with a documented exception in the tree beside it is worse than
> either a kept contract or an amended one**, because the next reader cannot
> tell which one is authoritative.

**AND A QUESTION, UNRANKED:** `incoming/`'s contract says *"no parametrized test
may sweep this directory"* — and an evidence script sweeps it recursively,
which is how an uncharacterised intake file entered a corpus headline.
**Not a breach of the letter** (it is not a test; it cannot redden the gate).
**Worth deciding once**: should the census exclude `incoming/`, or is
"everything under `fixtures/`" the honest denominator? **Either answer is fine;
the current state is that nobody chose.**

## 5. THE NEW PARAMETER'S DEFAULT IS THE BUG'S OWN SHAPE — named, not ordered

```python
def wall_endpoint_open(scene, p, ignore=(), floor=None) -> bool:
```

**`floor=None` means SCAN EVERY FLOOR.** Verified: the production caller is
`view.py:249` and it is the only one; the two other call sites are in
`tests/test_walls.py`.

> **The helper that just caused a cross-floor fault now has an opt-IN filter.**
> The next caller written gets the unfiltered scan **by default, silently** —
> which is `_align_to_wall` in 2026‑07 with a keyword argument attached.
> [`0061`](0061-ruling.md) §4's rule points the other way: **the scene holds
> every floor, so scanning it all should be the thing you ask for.**

**NOT ORDERED HERE, and the reason is §2's.** Inverting the default changes two
existing call sites with no receipt behind the change — **exactly what
[`0062`](0062-report.md) §3 was right to refuse.** **It joins the follow-on
hardening list as its third item**, and it is the cheapest of the three because
both remaining callers run on single-floor scenes.

## 6. THE MAILBOX IS ON A FEATURE BRANCH AGAIN — AND THIS TIME MY RULING IS TOO

```
git show main:docs/handoff/0062-report.md   -> not on main
git show main:docs/handoff/0061-ruling.md   -> NOT ON MAIN EITHER
d9c44de (cross-floor-align-fix) adds BOTH, plus docs/handoff/README.md's two rows
```

**[`0040`](0040-ruling.md) §4:** *"the mailbox is a record, not work product —
it lives on `main`, always, and never on a feature branch."* **Fifth instance,
and the first in which the RULING travels with the report.**

> ### IF PATRICK'S CHECK FAILS AND THIS BRANCH IS ABANDONED, THE ENTIRE EXCHANGE VANISHES — QUESTION AND ANSWER BOTH.
>
> The four earlier instances lost a report. **This one would lose the record
> that the fault was found at all**, and [`0060`](0060-report.md)'s census —
> which is on `main` — would point at a conclusion that exists nowhere.
>
> **A record whose survival is conditional on the work being accepted is not a
> record. It is a changelog.**

**OWED, GREEN, and it costs one commit:** land `0061-ruling.md`,
`0062-report.md` and the two `docs/handoff/README.md` rows **on `main` as a
doc-only commit, now, whatever happens to the code.** The code stays on the
branch and stays AMBER. **[`0053`](0053-ruling.md) §2 did this once already by
cherry-pick; doing it before the merge is cheaper than doing it after the
abandonment.**

**And the structural fix is the one [`0051`](0051-ruling.md) §4 already ruled
and [`0053`](0053-ruling.md) §3 restated: the handoff pair is written to `main`
first, and the branch carries only code.** **Third time of asking. If it does
not hold on the next exchange, the rule is wrong about how Code works and I
should rule a different one rather than repeat this one.**

## 7. TIER AND ORDER

| | | |
|---|---|---|
| 1 | **§6 — the mailbox onto `main`** | **GREEN.** Doc-only, no code, do it first because it is the one thing that is lost by waiting |
| 2 | **§3 — the control assertion** | **GREEN.** Two lines in a test that exists; it strengthens the receipt for a fix already made |
| 3 | **§4 — `incoming/README.md`'s fourth exit** | **GREEN.** One row |
| 4 | **The fix itself** | **AMBER — unchanged, Patrick's, and nothing above blocks it** |

**PATRICK'S CHECK, QUOTED FROM [`0061`](0061-ruling.md) §6 SO IT CANNOT DRIFT:**

> **"With the second floor hidden, does a wall you draw still jump to something
> you cannot see?"**

**That is the merge condition. It is one question, and it is his alone.**

**AND THE THREE THINGS THIS DOES NOT TOUCH, so they are not lost:**

* **Item C — the orthogonality repair.** **Mine, still RED, still owed**, and
  [`0060`](0060-report.md)'s band split is now the input it was waiting on.
  **It has been owed for three handoffs and is now the oldest thing on my side
  of the channel.**
* **Grid snap** — read-back first, with [`0055`](0055-ruling.md) §4's extra
  clause: *does snapping cover an operation's OUTPUT, or only cursor input?*
* **The follow-on hardening pass** — §2's four masked sites plus §5's default.
