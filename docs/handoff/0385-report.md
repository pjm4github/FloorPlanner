# 0385 — report on 0372 item C: `compute_roof_clips` does not return. The defect record opened (D91), the hang measured, a fix proposed. No fix made — the fix is RED until this report is ruled.

2026-11-27, Code (Opus). Answers [`0372-ruling.md`](0372-ruling.md) §4 C (and the
original order, [`0350-ruling.md`](0350-ruling.md) §1). Item C of the dormer-fix
workstream. No `fp3d.py`/`roofclip.py` change — the ruling's tier is *record
GREEN; fix RED*, and §1 says *"No fix until that report is ruled."*

## 1. The record, opened

[`docs/defects/0091-compute-roof-clips-does-not-return-on-a-cluster-of-roofs.md`](../defects/0091-compute-roof-clips-does-not-return-on-a-cluster-of-roofs.md)
(**D91**, `area:geometry`), with both reproductions 0372 §4 C named. 0350 §1 had
ordered the record and it was never opened; 0369 reported it filed against
`C2-weld-readback.md`, but that file only records that the pyramid *weld* is a
pairwise pass that never enters this walk — it does not hold the reproduction.
D91 is the real record. `defects/INDEX.md` regenerated (91 records, `--check`
clean).

## 2. The two reproductions

Both drive the real `fp3d.build_model` (`fp3d.py:3920` calls
`ROOFCLIP.compute_roof_clips`); the harness and a captured log are in
[`docs/evidence/0372-clip-hang/`](../evidence/0372-clip-hang/).

1. **Three gables** — `0007.plan.json` (0350 §1's watcher input, in the repo at
   `fixtures/incoming/build/wiscaway-c02/`): `rf1` main gable + `rf2`/`rf3` cross
   gables. All three hang; **every pair of the three converges in ≤ 2 rounds**
   (0350 §1's "any two finish in 0.2 s", confirmed). The hang needs ≥ 3.
2. **Opposed dormers** — Patrick's `...\wiscaway-roof-build\repro-opposed-dormers-hang.json`
   (a user plan; read, not committed): six L1 roofs. Here the hang reduces to
   **two roofs** — `rf1` (ridge y = 540) and `rf2` whose end `(498, 540)` sits
   exactly on `rf1`'s ridge, a ridge-end-on-ridge T. `rf1+rf2` alone hangs;
   `rf2+rf3` (far apart) returns in 0.1 s.

Two distinct minimal shapes (three roofs; two roofs) for one bug.

## 3. Measured: a combinatorial blow-up from a non-convergent fixed point

Not an infinite loop (the loop is `for _round in range(10_000)`, a backstop) and
not a one-shot huge arrangement. The envelope **regrows every round** and never
converges. Instrumenting `roofclip`'s hot functions (`_adjacent`, `_neighbours`,
`_reach`) with counters + a wall-clock deadline, and running `build_model`:

| input | rounds in window | pieces first → last | growth | `_adjacent` | `_reach` visits |
|---|---|---|---|---|---|
| opposed dormers, 6 roofs | 76 in 30 s | 113 → 565 | **+6 / round, monotone** | 1.66 M | 176 k |
| three gables, 7 roofs | 59 in 20 s | 170 → 705 | **+9 / round, monotone** | 1.20 M | 99 k |
| opposed `rf1+rf2`, 2 roofs | 84 in 12 s | 44 → 376 | **+4 / round, monotone** | — | — |

**Piece count rises by a near-constant amount every round, with no plateau and
no converging round.** Per-round cost is ≈ O(pieces²) in `_adjacent`
(neighbour-graph build + reach walk), and pieces grow linearly, so the loop runs
toward the 10 000-round backstop with the arrangement at tens of thousands of
pieces — it does not return in human time. "Visits per piece": ~2.3 k reach
visits per round against a few hundred pieces, i.e. the walk itself is healthy;
the cost is the round count × growing arrangement, not a runaway single walk.

## 4. Where it grows (mechanism)

The fixed-point loop re-envelopes each round (`_envelope_round`). Its prune block
(`roofclip.py` ≈ 1699–1713) splits a cell that holds a to-prune piece and
**appends** the extra parts as new cells — `cells.append(...)`,
`orig_coverers.append(...)`, `active.append(...)`. The loop's termination
argument (docstring ≈ 1491 and ≈ 1078) relies on a **finite, fixed** arrangement
— *"cells only ever split along equal-height lines of finitely many coverer
subsets"* — whose active-coverer sets only shrink, so each non-converging round
strictly shrinks some set. But the re-split sub-pieces are recomputed from
scratch each round and do not coincide with the previous round's cells, so
`cells`/`active` grow ~constant per round. The monotone growth of the cell list
outruns the active-set shrinkage that is supposed to be the decreasing measure;
the loop never reaches a fixed point.

## 5. Proposed (no fix made — RED until ruled)

For the reviewer to rule (D91 §"Not yet diagnosed to a fix"):

1. **Restore the finite-arrangement premise.** When a cell splits for pruning,
   dedupe the appended sub-cells against existing cells by vertex set (as the
   initial arrangement already dedupes). A round that only re-partitions the same
   ground and prunes an owner then does not grow `cells`, and the active-set
   measure actually bounds the loop. *(My recommendation — it fixes the cause.)*
2. **Convergence by active-set change, not piece identity.** A round that prunes
   nothing new is converged even when re-enveloping drew cosmetically different
   sub-pieces; detect and stop.
3. **A safety net, able to stand alone** before the cause is ruled: detect
   non-convergence (pieces rising with no active-set shrink over K rounds, or a
   far lower backstop) and return the cluster **unclipped** with a warning — the
   same fallback the coplanar-pair case already takes. This stops the app
   hanging on a plain farmhouse (front + rear cross gable) even if the root fix
   waits.

## 6. Scope held

No code changed. Item D (D89 skirt-not-live) and E (two dialog advisories) are
next in the workstream, B2 (the hipped front-corner floor tabs) riding with
them; none started here. The opposed-dormers and `0007` plans were read, never
committed (the second is under `fixtures/incoming/`, gitignored).
