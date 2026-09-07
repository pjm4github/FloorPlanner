# 0161 — report: R4b closed — PR #55 merged on Patrick's word

**Code, 2026‑09‑07.** Close-out per [`0160-ruling.md`](0160-ruling.md) §2:
*"On his word: merge PR #55, delete the branch in the merge step, and R4c
starts."* His word: *"Outline looks right, merge it."*

---

## 1. DISPOSITION — R4B CLOSED, MERGED

[PR #55](https://github.com/pjm4github/FloorPlanner/pull/55) merged to
`main` at `9d91705`; branch `roofs-r4b-parameters` deleted in the same
merge step (local and remote, confirmed by `git branch -a` after a prune).
CI green on the final push (`ruff`, `pytest (py3.13, full gate)`; the other
three jobs intentionally disabled per [`0105`](0105-ruling.md)).

What landed, in one line each — the receipts are the four reports behind it:

* [`0157`](0157-report.md): the parameters dialog — per-side overhang,
  gable↔hip per end (with real hip geometry in 2D, 3D and the clip line),
  the `room_top` eaves binding re-synced at every room-height edit.
* [`0158`](0158-report.md): his first check's three findings — the eaves
  pick measures each side to its own wall; editable "Eaves span, left /
  right"; the span is the perpendicular distance to the ridge LINE, so 24″
  is two 12″ grid lines past each wall, on a 45° wing too.
* [`0159`](0159-report.md): the selection outline is the eave rectangle,
  oriented with the ridge.
* [`0160`](0160-ruling.md): verified, two decisions endorsed as precedent,
  the hygiene line.

Re-gated on the merged tree after the merge: full suite passed, `ruff`
clean, `python tools/gate.py` (full mode) GREEN — numbers in the commit.

## 2. THE HYGIENE LINE, AS ASKED

`git fetch --prune` removed **two** stale local remote-tracking refs,
`origin/roofs-r3b-clip-line` and `origin/roofs-r4a-schema`. Both were
unpruned tracking refs: the remote branches themselves were already
deleted, exactly as [`0153`](0153-report.md) and [`0156`](0156-report.md)
reported. Nothing on the remote changed.

## 3. NEXT — R4C

**R4c is the next available tranche (AMBER)** per [`0154`](0154-ruling.md)
§3: five grips on a selected roof — two eave edges, two gable ends, the
ridge. [`0160`](0160-ruling.md) §2's named receipt binds it: **the
eave-edge grips must drag exactly the two `span_in` values the dialog now
edits** — no second span convention. Also from `0154`'s row: overhang rides
along with an eave-edge drag; a gable-end drag moves that ridge endpoint;
the ridge drag slides it laterally between fixed eave edges, rebalancing
the two spans; all undoable; drags land ON the grid, never move by it
([`0070`](0070-ruling.md) §3's class, to be tested, not remembered).
Then R5 (dormers, RED, own ruling).

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items.
