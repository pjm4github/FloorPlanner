# 0257 — report: PR #84 merged on his word, the stack folded in — the gable climb's level check, his four fixes, the shed dormer's dialog and grip; iteration 11 of the house stands

**Landed:** PR #84 · 7a0a4bf · 2026-10-11 · AMBER · checked by Patrick on the house model's shed dormer in the app: "the shed dormer looks right, fold and land #84"

**Code, 2026‑10‑11.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0254`](0254-report.md) put iteration 10's fix on `roof-gable-climb-level`
(PR #84); [`0255`](0255-report.md) and [`0256`](0256-report.md) stacked
his four fixes and the shed dormer's two on `window-sill-endon`. His word:

> *"the shed dormer looks right, fold and land #84"*

Done as said: `window-sill-endon` folded into `roof-gable-climb-level`
(fast-forward to `95e34ed`), `main` (`caab2c0`) merged into it with the
snapshot resolved as the merged state, and the branch pushed to `main`
at **`7a0a4bf`** — [PR #84](https://github.com/pjm4github/FloorPlanner/pull/84)
MERGED; both branches deleted, local and remote.

## 1. WHAT LANDED, in one place

* **The gable climb stays on the wall's own level**
  ([`0254`](0254-report.md) §1): a wall climbs into a roof of its own
  level only. `tests/test_gable_climb_level.py`.
* **The End-On dialog draws a shed** ([`0255`](0255-report.md) §0): no
  division by the shed's zero right span; the one slope and the high
  wall under the ridge.
* **The window's elevation** ([`0255`](0255-report.md) §1):
  `OpeningItem.sill_in`, the sheet's Sill height row, `DEFAULT_SILL_IN`
  36″ when a record does not say, carried by the bridge and every copy
  path. `tests/test_opening_sill.py`.
* **The schema audited** ([`0255`](0255-report.md) §2): a window's sill
  and a gate's swing no longer lost on save; `sill_in`/`head_in`
  described.
* **A shed dormer stands in the dialog** ([`0256`](0256-report.md) §1):
  its high edge on the host, nothing to meet, nothing derived, both ends
  faces; **and its ridge grip no longer creeps** ([`0256`](0256-report.md)
  §1b): a shed's ridge is its high edge, the eave stays, the span
  follows.
* **Iteration 11 of the house** ([`0255`](0255-report.md) §3): the
  windows at the picture's elevations and heights;
  `fixtures/incoming/house_cutout.json`, uncommitted, his to keep.

## 2. `fixtures/incoming/`, with ages

* `house_cutout_transparent.png`, `house_cutout_1stfloor.png` — his own,
  2026‑10‑11.
* `house_cutout.json` (iteration 11), `house_cutout_work/` — mine,
  2026‑10‑11.
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 3. WHAT HAPPENS NEXT

Nothing is open on a branch. 0248's E (posts, the porch floor) and the
hip run (§2 item 6) stay his to order. Behind them: the compose cost
([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0256`](0256-report.md).
