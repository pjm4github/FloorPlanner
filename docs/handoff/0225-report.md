# 0225 — report: PR #76 merged on his word with the gable-end tranche folded in — the D67 pair and the open gable ends; D67 CLOSED

**Code, 2026‑10‑07.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0223`](0223-report.md) put the D67 pair to him on `d67-floor-scope`
(PR #76) and [`0224`](0224-report.md) the gable-end tranche on
`gable-end-walls` stacked on it. His word:

> *"gable ends look right, fold into #76 and land"*

Done as said. `d67-floor-scope` was fast-forwarded to `gable-end-walls`'s
tip (`0c8219a`), `main` (where 0224 had landed) merged into it, the
snapshot resolved as the merged state, the gate run GREEN, and the
branch landed on `main` at **`cdc54de`**, fast-forward. GitHub shows
[PR #76](https://github.com/pjm4github/FloorPlanner/pull/76) MERGED with
both commits. Both branches are deleted, local and remote, in the same
step.

## 1. WHAT HIS WORD RESTS ON — recorded as it is

He **checked the gable ends** on his own plan in the 3D view: *"gable
ends look right."* **The D67 pair he has not reported on**; it is merged
on his instruction and on its tests — the two probes' own gestures, red
before the predicates and green after, with two positive controls
([`0223`](0223-report.md) §1). If a group or the Door tool still crosses
floors in his hands, `tests/test_d67_floor_scope.py` is where to start.

## 2. D67 — CLOSED

`docs/defects/0067-…md`: `state: closed`, `closed: 2026‑10‑07`,
`closed_by: cdc54de`, a closing section saying what the leak actually
was — a fourth site, not the three the record named — and
`defects/INDEX.md` regenerated: **86 records, 31 open.** The Door-tool
twin ([`0202`](0202-report.md) §4) never had a record of its own; it is
fixed in the same commit and said in D67's closing section.

## 3. WHAT LANDED

On the merged tree: **1700 passed**, 7 deselected (`perf` lane), `ruff`
clean, gate GREEN.

| | report | what it is |
|---|---|---|
| the D67 pair | [`0223`](0223-report.md) §1 | `interior_walls()` returns the room's own floor's walls; the Door/Window tool takes a wall of the active level only |
| the gable ends | [`0224`](0224-report.md) | no roof-material triangle closes a gable end; the exterior wall perpendicular to the ridge climbs to the roof's underside, to the ridge; R3's *"gables closed"* and R4g's fascia clip reversed on the record |

**Owed from 0224 §4, his display needed:** `roofs-r3-planes-gables.png`
in `docs/evidence/` shows a closed gable the model no longer builds.

## 4. `fixtures/incoming/`, with ages

Empty.

## 5. WHAT HAPPENS NEXT

Nothing is open on a branch. On his word, from the queue as it stands:
the four-way crossing fault, parallel walls 6″ apart merging, the status
board, the evidence re-shot above.

**Carried:** unchanged from [`0224`](0224-report.md).
