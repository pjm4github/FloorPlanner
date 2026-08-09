---
# permanent key, independent of GitHub
id: 56
title: "A macro replay's final SELECTION is nondeterministic - two answers from one .fpm"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:tests
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-08
closed: null
closed_by: null
rank: 57
related: [53, 28]
state_source: report
github_issue: null
---

# D56 — A macro replay's final SELECTION is nondeterministic

## Symptom

Replaying `examples/dragWallFuseStraggler.fpm` over `examples/fiveRoomTest.json`
gives **two different selection outcomes** from the same file, on the same plan,
on an unchanged tree. The last three lines sometimes end with an extra
`WallItem` selected and sometimes do not.

Measured 2026‑08‑08, twelve consecutive runs per tree:

| tree | wall-count outcomes | selection outcomes | split |
|---|---:|---:|---|
| `main` `bcffa08` | **1** | **2** | 6 / 6 |
| A1b branch | **1** | **2** | 8 / 4 |

**The two outcomes are the same two on both trees**, and **`main` flaps at 6/6**
— so this is **pre-existing** and was not introduced by A1b. The per-line
**wall-count** sequence is a single outcome on both trees and identical:
`[18, 18, 16, 16, 18, 15, 17, 16]`.

## Mechanism

*(Not diagnosed — this record is the measurement, filed where it was found.)*
What is established: the replay drives real synthetic mouse events through the
view, and the divergence is in the **selection set**, not in the geometry — the
same walls exist either way. Candidates worth testing, in the order they seem
likely:

1. **`QGraphicsScene.items()` ordering among equal-z items.** Several walls sit
   at `WALL_Z` exactly; nothing in the app breaks that tie, so which one a
   press resolves to may depend on insertion or internal index order.
2. **A debounced pass landing inside or after the replay.**
   `_update_edit_actions` schedules `_apply_edit_actions` on a timer, and the
   180 ms dirty timer is in the same family — a run where the timer fires
   between lines is a different run.
3. **The probe's own snapshot point**, reading `selectedItems()` before a
   queued event has been delivered.

(1) and (2) would be app-side; (3) would be probe-side, and it should be
excluded first because it is cheapest.

## Evidence

`docs/evidence/d53-macro-differential.txt`, which carries the run counts and
the correction described below.

**HOW IT WAS FOUND MATTERS MORE THAN THE DEFECT, and it is why this is filed
rather than shrugged at.** A single run of the comparison was written up in
A1b's receipt as *"the macro replay is identical to `main` at every line"*. On
a field that flaps roughly half the time, one matching run is close to a coin
landing heads — the reading was true of that run and says almost nothing about
the tree.

It surfaced when the probe was re-run after a pure refactor and gave a
**different** answer on a tree whose behaviour could not have changed. The
bisect that followed pointed at `RoomItem.contextMenuEvent` — which is entered
**zero times** during the replay, an impossible culprit. That impossibility is
what prompted testing the instrument instead of believing the bisect.

## Ruling

*(Open. Measurement only — nothing diagnosed, nothing fixed.)*

**The corrected claim for A1b stands on the stable half**: the wall-count
sequence is deterministic, identical on both trees, and shows line 4's fuse
restored. The selection field is **not evidence either way** and A1b's receipt
now says so.

**This weakens every macro pin that asserts on selection**, and that is the part
worth scheduling. `docs/evidence/d53-macro-differential.txt` records which half
of this comparison can be trusted; the pinned macro tests in
`tests/test_extract_join.py` assert wall counts, room areas and binding
invariants — **the stable quantities** — which is why they have not flapped.
That is luck rather than design, and naming it is the point.

## Receipt

*(Open.)* Acceptance: twelve consecutive replays of the same `.fpm` on the same
plan produce **one** selection outcome, not two — measured the same way, on
whichever tree the fix lands.
