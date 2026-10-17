# 0284 — report: PR #96 merged on his word — undo by difference; nothing open on a branch

**Landed:** PR #96 · bc68e43 · 2026-10-17 · AMBER · checked by Patrick in the app: "land #96, the cntrl+Z looks good!"

**Code, 2026‑10‑17.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0283`](0283-report.md) built his option A on `undo-diff` (PR #96). His
check:

> *"land #96, the cntrl+Z looks good!"*

Done as said: the branch landed on `main` at **`bc68e43`**, fast-forward
(one commit on `main`'s tip); [PR #96](https://github.com/pjm4github/FloorPlanner/pull/96)
MERGED; the branch deleted, local and remote.

## 1. WHAT LANDED

* An undo or redo rebuilds only what differs between the plan on screen
  and the state restored (`bridge.apply_design_difference`), per level for
  the walls/rooms web, the furnishings and the annotations, the roofs as
  one roofscape; anything it cannot apply with certainty reloads in full,
  as before. On his R1 plan: Ctrl+Z 0.27 s → 0.17 s, redo 0.18 s (3.6 s
  before [`0280`](0280-report.md)).

## 2. THE UNDO RUN, IN ONE PLACE

[`0280`](0280-report.md) kept the roofs' traces by value across the
reload (3.6 s → 0.34 s); [`0282`](0282-report.md) dropped the walk after a
restore (→ 0.27 s) and corrected the P6.b claim; [`0283`](0283-report.md)
restores by difference (→ 0.17 s). The walk before an undo (~80 ms) stays,
for the reason in 0282. All on `main` (PRs #94–#96). **Nothing is open on
a branch.**

## 3. A TEST THAT FAILED AT RANDOM, FIXED

The gate on this record went RED twice on
`tests/test_undo_fast.py::test_undo_of_a_wall_edit_reuses_the_roofs`
(0280's), about one run in six, alone as well as in the suite. The
compared clips had the same area and the same segments; only **which end
of a seam a compose lists first** varied from run to run. Every consumer
of a seam treats it as an undirected line (`drawLine`, the hit stroke), so
the code is right and the test's signature was too strict: it now compares
each seam with its ends in order. 25 runs of the file in a row passed;
gate GREEN.

Named, not ordered: DXF export of annotations; his backlog (0248's items
8 and 9).

**Carried:** unchanged from [`0283`](0283-report.md).
