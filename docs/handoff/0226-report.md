# 0226 — report: the four-way crossing fault — NOT REPRODUCED in 96 runs across seven configurations and two commits, one of them the commit 0208 measured on; no defect filed; the instrument kept

**Code, 2026‑10‑07.** No merge has happened since
[`0225`](0225-report.md). His word: *"start on the four-way crossing
fault."* Nothing is changed by this commit but the record and
`docs/evidence/`.

## 0. THE CLAIM BEING TESTED

[`0208`](0208-report.md) §4, written during A6's build:

> *"Replaying `dragWallFuseStraggler.fpm` fourteen times in one process,
> on `main`'s code: after its sixth line, three runs have the horizontal
> wall whole and the vertical one split at (340.56, 270.03), and the
> others the reverse. … Something on the join path iterates in an order
> that is not fixed."*

Carried as open since ([`0209`](0209-report.md) §4, [`0211`](0211-report.md)
§4), with no defect record because *"a number is his or the reviewer's
to give."* Under the standing rule it is testimony — mine — and earns
the same scrutiny as any premise. **The first task was to reach the
state described. I could not.**

## 1. THE INSTRUMENT

[`docs/evidence/fourway_crossing_probe.py`](../evidence/fourway_crossing_probe.py),
output [`fourway-crossing-probe.txt`](../evidence/fourway-crossing-probe.txt).
It replays the macro's first six lines — the `^O` line included, so the
macro itself reloads the plan — N times, and tallies the **whole wall
set** (every end of every wall to 1/100″), so any difference at all is a
second state, not only the one 0208 described. Configuration by
environment: one window or a fresh one per run; shown or not; the window
geometry; a pause between lines for the 180 ms settle timer; the hash
seed.

**Positive control, built in and printed first:** the state after 0, 1,
… 6 lines — seven prefixes, six distinct wall sets (`6eebef53`,
`51662354`, `143c7ee5`, `cf230a4d`, `cf230a4d`, `937174de`). The
instrument tells wall sets apart.

**A trap that cost the first hour, recorded so it is not paid again:**
this macro was recorded at the **default 1200×800 window, no zoom-fit**
(`tests/test_extract_join.py`'s own pin says so); the other two
fiveRoom macros were recorded at 1400×1000 + fit. At the wrong geometry
the clicks land elsewhere and nothing is near the crossing at all.

## 2. THE MEASUREMENT

After six lines, in every configuration, **one state, `937174de`**: 18
walls, the horizontal wall at y=270.03 **split** at x=334.56 and the
vertical wall at x=340.56 **whole** from y=158 to 421.91 — 0208's
*"the reverse"*, the majority state it described.

| commit | configuration | runs | states |
|---|---|---|---|
| `main` (`687bdc0`) | one window, 1200×800, no pause | 14 | 1 |
| | fresh window per run | 14 | 1 |
| | shown, 250 ms pause between lines | 10 | 1 |
| | `PYTHONHASHSEED=7` | 10 | 1 |
| | `PYTHONHASHSEED=99`, fresh window per run | 10 | 1 |
| **`fe9bb96`** — 0207's commit, the pre-A6 `main` 0208 measured on | one window | 14 | 1 |
| | fresh window per run, shown | 14 | 1 |

96 runs, one state, the same state on both commits. Earlier, at the
wrong geometry (1400×1000, fit), another 90 runs across six prefixes and
six hash seeds: also one state each — not evidence about the crossing,
but evidence that the join path is deterministic for THAT click
sequence too.

## 3. WHAT THE CODE SAYS

The candidate the claim named — *"something on the join path iterates in
an order that is not fixed"* — read for its order sources:

* `graph_from_scene` (`walls.py`) **sorts the walls by geometry**
  (`p1.x, p1.y, p2.x, p2.y, type`) before anything plans on them.
* `split_body_landings` iterates that sorted order, then `view.pos`, a
  dict in insertion order from the same sort; its `done` set holds
  `id()`s for membership only, never iterated.
* `WallItem._split_body_landings` / `_run_wall_under` iterate
  `self._attached` and `self._run`, lists built in gesture order.
* `QGraphicsScene.items()` orders by z then insertion, which is fixed
  for a fixed sequence.

Nothing on that path iterates a set of items. **I found no order source
that is not fixed, and no run that varied.**

## 4. WHAT I CANNOT RULE OUT, said plainly

0208's harness is not on the record: not the window, its geometry,
whether it was shown, or whether all fourteen runs shared one process
state with the A6 branch's own (b) fault — which 0208 itself says is
what made the difference visible, and which was fixed in the same
tranche. The minority state it described (vertical split at
(340.56, 270.03), horizontal whole) is a state I have not seen the code
produce once. The likeliest reading is that the three odd runs were an
artefact of that build's own transient fault, or of a harness mixing
geometries; the record cannot say which.

## 5. RECOMMENDATION — his to take

**Close the queue item as NOT REPRODUCED; file no defect.** A record
needs either a reproduction or a report of his own; this has neither,
and D67's own history shows what an unreproduced record costs — it
named three sites, none of them the leak. The instrument stays in
`docs/evidence/` for the day it is seen again; one command, any
configuration.

If he would rather carry it, the honest shape is a record in the
`wontfix`-less state D67 had — *filed as reported, not reproduced* —
with this report as its measurement.

## 6. `fixtures/incoming/`, with ages

Empty.

## 7. WHAT HAPPENS NEXT

His word on §5. Behind it: parallel walls 6″ apart merging
([`0210`](0210-report.md) §6), the status board, the evidence re-shot
of `roofs-r3-planes-gables.png` (his display).

**Carried:** unchanged from [`0225`](0225-report.md).
