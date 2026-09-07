# 0163 — report: R4c closed — PR #56 merged on Patrick's word

**Code, 2026‑09‑07.** Close-out of [`0162-report.md`](0162-report.md), the
AMBER tranche R4c. His word, after his own check: *"All five grips work,
merge it."*

---

## 1. DISPOSITION — R4C CLOSED, MERGED

[PR #56](https://github.com/pjm4github/FloorPlanner/pull/56) merged to
`main` at `8b33064`; branch `roofs-r4c-grips` deleted in the same merge
step, local and remote (confirmed by `git branch -a` after a prune). CI
green on the final push (`ruff`, `pytest (py3.13, full gate)`; the other
three jobs intentionally disabled per [`0105`](0105-ruling.md)).

Re-gated on the merged tree after the merge: full suite passed, `ruff`
clean, `python tools/gate.py` (full mode) GREEN — numbers in the commit.

**The decision [`0162`](0162-report.md) §1 named for his eye — the end grip
moves along the ridge axis only — stands as checked**: he dragged all five
and merged. Recorded here so it is a checked behaviour, not an unexamined
default.

## 2. WHERE THE ROOFLINE PLAN STANDS

[`0139`](0139-ruling.md)'s five tranches, re-planned at
[`0154`](0154-ruling.md): **R1 / R2 / R2b / R2c / R3 / R3b / R4a / R4b /
R4c — all DONE.** Patrick's five requirements from `0154` are each closed
by a merged tranche: overhang editing (R4b), full JSON persistence (R4a), a
solid schema (R4a), five-grip direct manipulation (R4c), the eaves-to-room-
top binding (R4b).

**What is left of the plan: R5, dormers — RED, its own ruling when he
wants it** ([`0139`](0139-ruling.md) §3). Named-not-ordered items unchanged:
valley/hip intersection lines in 2D, a roof-plan sheet in the PDF/DXF
exports, yard items.

**Nothing is open on this project's own work.** No branch, no PR, no owed
check.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items;
the pre-existing stash entry (`0162` §3's hygiene note, his call).
