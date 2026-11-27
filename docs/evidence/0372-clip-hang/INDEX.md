# 0372 item C — `compute_roof_clips` hang: measurement

Evidence for [D91](../../defects/0091-compute-roof-clips-does-not-return-on-a-cluster-of-roofs.md)
and [`handoff/0385-report.md`](../../handoff/0385-report.md). 0372 §4 C ordered
the hang measured: *"loop or blow‑up (piece count, visits per piece)."*

## What is here

- **`measure_clip_hang.py`** — the harness. Monkeypatches the path‑loaded
  `ROOFCLIP` module's hot functions (`_adjacent`, `_neighbours`, `_reach`) with
  counters and a wall‑clock deadline, then runs the real `fp3d.build_model` on a
  plan and reports rounds, per‑round piece count, `_adjacent` calls, `_reach`
  calls and total frontier visits. No module is edited. Run from the repo root:

  ```
  python docs/evidence/0372-clip-hang/measure_clip_hang.py <plan.json> [--deadline S] [--keep rf1,rf2]
  ```

- **`measurement.log`** — a captured run on the opposed‑dormers repro (a user
  plan, not committed): all six roofs, and the minimal hanging subset `rf1+rf2`.

## Finding (verbatim numbers in the log)

A **combinatorial blow‑up from a non‑convergent fixed point**, not an infinite
loop and not a one‑shot huge arrangement. The envelope arrangement regrows every
round and never converges:

| input | rounds in window | pieces first → last | growth | `_adjacent` |
|---|---|---|---|---|
| opposed dormers, 6 roofs | 76 in 30 s | 113 → 565 | +6 / round, monotone | 1.66 M |
| three gables (`0007`), 7 roofs | 59 in 20 s | 170 → 705 | +9 / round, monotone | 1.20 M |
| opposed `rf1+rf2`, 2 roofs | 84 in 12 s | 44 → 376 | +4 / round, monotone | — |

Each pair of the `0007` three‑gable file, by contrast, converges in ≤ 2 rounds
(0350 §1's "any two finish in 0.2 s"). The opposed‑dormers file reduces to a
single hanging pair: `rf1` (horizontal ridge y = 540) and `rf2` (vertical ridge
whose end `(498, 540)` lies on `rf1`'s ridge) — a ridge‑end‑on‑ridge T.

Mechanism: the fixed‑point prune block splits cells and **appends** new cells and
active sets every round (`roofclip.py` ≈ 1699–1713); the re‑split sub‑pieces
don't coincide with the prior round's cells, so the arrangement grows ~constant
per round and outruns the active‑set shrinkage that is meant to make the loop
terminate. See D91 for the full write‑up and proposal.
