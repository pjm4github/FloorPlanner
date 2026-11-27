---
# permanent key, independent of GitHub
id: 91
title: "compute_roof_clips does not return on a cluster of roofs that meet in plan"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:geometry
milestone: null

# ours; becomes body prose after migration
opened: 2026-11-27
closed: null
closed_by: null
rank: 91
related: []
state_source: ruling
github_issue: null
---

# D91 — `compute_roof_clips` does not return on a cluster of roofs that meet in plan

## The report

**Ordered open by [`handoff/0350-ruling.md`](../handoff/0350-ruling.md) §1
(2026‑11‑16) and re‑ordered by [`handoff/0372-ruling.md`](../handoff/0372-ruling.md)
§4 C (2026‑11‑25), item C of the dormer‑fix workstream.** 0350 §1 ruled *"Open a
record; measure whether it is an infinite loop or a combinatorial blow‑up before
proposing anything. No fix ruled."* 0350 §1 said the record was owed; it was
never opened — [`0369`](../handoff/0369-report.md) reported it filed against the
pyramid‑weld read‑back (`docs/evidence/0367-pyramid-roof/C2-weld-readback.md`),
but that file only records that the *weld* is a pairwise pass that never enters
this walk; it does not hold the reproduction. 0372 §4 C ordered the record
opened now with both reproductions and the hang measured. This is that record.
The measurement is [`0385-report.md`](../handoff/0385-report.md).

`floorplanner/roofclip.py` `compute_roof_clips` — the roof‑roof clip that
`fp3d.build_model` runs once per built level (`fp3d.py:3920`) — does not return
on certain clusters of roofs that overlap in plan. `build_model` ran past 75–100 s
on `ab8aad8` and never finished; the app never opens the file. A
`faulthandler` dump taken at 8 s (0350 §1) placed the hang in the reachability
walk of the fixed point:

```
roofclip.py  _adjacent
roofclip.py  _neighbours
roofclip.py  _reach
roofclip.py  _components
roofclip.py  _walk
roofclip.py  compute_roof_clips
fp3d.py      build_model
```

## The two reproductions

1. **Three gables, none hosted** — 0350 §1's `0007.plan.json`
   (`fixtures/incoming/build/wiscaway-c02/0007.plan.json`, a watcher input): one
   main gable `rf1` and two cross gables `rf2`/`rf3` at L1 on opposite sides of
   it. All three together hang; **any single pair of the three returns in ~0.1 s**
   (confirmed: `rf1+rf2`, `rf1+rf3`, `rf2+rf3` each converge in ≤ 2 rounds). The
   hang needs ≥ 3 of the cluster.

2. **Opposed dormers** — Patrick's
   `...\wiscaway-roof-build\repro-opposed-dormers-hang.json` (a user plan; read,
   never committed): six L1 roofs (`rf1` main gable, `rf2`/`rf3` in‑line/cross,
   `rf4` gable, `rf5`/`rf6` sheds). `build_model` did not return in 75 s on
   `ab8aad8`, and returns when the east dormer is moved 72 in. Here the hang
   reduces all the way to **two roofs**: `rf1` (ridge horizontal, y = 540,
   x 384–1020) and `rf2` (ridge vertical, x = 498, y 156–540), whose top end
   `(498, 540)` lands **exactly on `rf1`'s ridge line** — a ridge‑end‑on‑ridge
   T‑junction. `rf1+rf2` alone hangs; `rf2+rf3` (far apart, in‑line) returns in
   0.1 s.

The two files are distinct reproductions of one bug: the minimal hanging subset
is three roofs in the first, two in the second.

## Measured: a combinatorial blow‑up from a non‑convergent fixed point

Not an infinite loop (the loop is `for _round in range(10_000)`, a backstop) and
not a one‑shot huge arrangement. The **arrangement regrows every round** and the
fixed point is never reached. Instrumenting the module's hot functions and
running the real `build_model` (full numbers in
[`0385-report.md`](../handoff/0385-report.md) and
`docs/evidence/0372-clip-hang/`):

| Reproduction | rounds in window | pieces: first → last | growth | `_adjacent` calls |
|---|---|---|---|---|
| opposed dormers (6 roofs) | 77 in 30 s | 113 → 571 | **+6 / round, monotone** | 1.72 M |
| three gables (7 roofs) | 59 in 20 s | 170 → 705 | **+9 / round, monotone** | 1.20 M |
| opposed `rf1+rf2` (2 roofs) | 84 in 12 s | 44 → 376 | **+4 / round, monotone** | — |

Piece count climbs by a near‑constant amount **every** round and never plateaus;
there is no converging round. Per‑round cost is ≈ O(pieces²) in `_adjacent`, and
pieces grow linearly, so the loop would run toward the 10 000‑round backstop with
the arrangement at tens of thousands of pieces — effectively never returning.

### Mechanism (where the arrangement grows)

The fixed‑point loop re‑envelopes each round (`_envelope_round`). Where a cell
holds a piece about to prune and that cell split into more than one
local‑maximum part, the loop **splits the cell and appends new cells** to the
arrangement (roofclip.py, the prune block ≈ lines 1699–1713:
`cells.append(...)`, `orig_coverers.append(...)`, `active.append(...)`). The
loop's termination argument (docstring ≈ line 1491, and ≈ 1078) relies on a
**finite, fixed** arrangement — *"cells only ever split along equal‑height lines
of finitely many coverer subsets"* — whose active‑coverer sets only ever shrink,
so each non‑converging round strictly shrinks some set. But the re‑split
sub‑pieces are recomputed from scratch each round and do **not** coincide with
the previous round's cells, so the `cells`/`active` lists grow by a roughly
constant amount every round. The monotone growth of the cell list outruns the
active‑set shrinkage that is supposed to be the decreasing measure, and the loop
never reaches a fixed point.

## Not yet diagnosed to a fix / proposal (no fix ruled)

Per 0350 §1 and 0372 §4 C, **no fix is ruled** — measure and propose only. The
shape of a fix is likely one of (for the reviewer to rule):

1. **Restore the finite‑arrangement premise.** When a cell splits for pruning,
   deduplicate the appended sub‑cells against existing cells by vertex set (as
   the initial arrangement construction already dedupes), so a round that only
   re‑partitions the *same* ground and prunes an owner does not grow `cells`.
   The active‑set measure then actually bounds the loop.
2. **Make the convergence test the active‑set change, not piece identity.** A
   round that prunes nothing new is converged even when re‑enveloping produced
   cosmetically different sub‑pieces; detect that and stop.
3. **A safety net, independent of the root fix** (could stand alone if the hang
   must be stopped before the cause is ruled): detect non‑convergence (piece
   count rising with no active‑set shrink over K rounds, or a far lower
   backstop) and return the cluster **unclipped** with a warning, so the app
   opens the file rather than hanging — the same fallback the coplanar‑pair case
   already takes (*"drawn unclipped"*).

## Status

**OPEN.** Opened per 0372 §4 C while landing the dormer fixes; measured (above);
no fix ruled. Reproductions preserved: `0007.plan.json` in the repo; the
opposed‑dormers file is a user plan (read only).
