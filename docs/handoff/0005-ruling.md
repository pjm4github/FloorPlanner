# 0005 — ruling: the plan-file placement conflict

**On the conflict raised in [`0005-report.md`](0005-report.md) §2.** Quoted, not
summarised:

> **RULING ON THE PLACEMENT CONFLICT: fixtures/ stands, as you had it.**

---

## What that settles

`fixtures/wiscaway2026-08-09R.json` stays in **`fixtures/`** — characterised,
with all seven violations named in [`../../fixtures/README.md`](../../fixtures/README.md)
and pinned by
`tests/test_design_bridge.py::test_the_2026_08_09R_fixture_is_still_dirty_in_all_seven_ways`.

**No change to the tree.** The branch already carries exactly this arrangement;
the ruling confirms it rather than directing anything new.

**`fixtures/incoming/` keeps its contract intact.** The two clauses that the
alternative would have broken stand unqualified: files there are
**uncharacterised**, and **no test may reference a file in `incoming/`**.

## Why it is worth having on disk

The report asked the question and offered to move the file. Left as it was, a
fresh session would read §2 as an open decision and might act on it. **A ruling
that exists only in a conversation cannot be quoted later, cannot be found by
the next session, and cannot be disagreed with on the record** — which is the
whole reason this directory exists.

## The precedent it sets, stated once

**A characterised failure does not pass back through the intake.** `incoming/` is
an entry point, not a holding pen: once a plan has been measured and its faults
named, it belongs in `fixtures/` with its entry and its guard test. The three
exits in [`../../fixtures/incoming/README.md`](../../fixtures/incoming/README.md)
are one-way by design, and this ruling is the first instance of that being
tested against a real file.
