# 0261 — report: PR #86 merged on his word — the compose cost: the arrangement from one set of disjoint cells and the neighbour graph, 15 roofs 32 s → 8 s; the clip pinned a function of the roofs alone; the parked patch deleted

**Landed:** PR #86 · 95ebc65 · 2026-10-11 · AMBER · checked by Patrick in the roof editor on his plans: "the roofs look right"

**Code, 2026‑10‑11.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0260`](0260-report.md) put the compose cost on `roofclip-cost`, one
commit, AMBER. His word:

> *"the roofs look right, land #86"*

Done as said: the branch landed on `main` at **`95ebc65`**,
fast-forward; [PR #86](https://github.com/pjm4github/FloorPlanner/pull/86)
MERGED; the branch deleted, local and remote.
`docs/evidence/roofclip-adjacency-memo.patch`, the parked memo of
[`0237`](0237-report.md) §0, is deleted with this report: superseded by
the neighbour graph, and a patch that no longer applies is a trap.
**0237 §0's compose-cost tranche is closed.**

## 1. WHAT LANDED, in one place

* **The arrangement from one set of disjoint cells**
  ([`0260`](0260-report.md) §1): each roof's domain laid down in turn,
  cut by and cutting the cells it meets, covered pieces dropped; a
  roof's plane lines cut only the cells its domain can reach. The cells
  pinned pairwise disjoint; every promoted roof fixture's region area
  and seam lines pinned against the record taken before
  (`tests/data/roofclip_ground_0260.json`).
* **The neighbour graph** once per piece list; the reach walk follows
  it. 15 roofs 32 s → 8.3 s, 12 roofs 5.2 s → 1.7 s on the probe's shape.
* **The clip sees roofs alone**, pinned: walls, openings, rooms and
  furnishings never reach the composer (`tests/test_roofclip_cost.py`).

## 2. `fixtures/incoming/`, with ages

* `house_cutout_transparent.png`, `house_cutout_1stfloor.png` — his own,
  2026‑10‑11.
* `house_cutout.json` (iteration 12), `house_cutout_work/` — mine,
  2026‑10‑11.
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
  The probe's input; promoting it would let the scaling test run on it.
* `README.md`.

## 3. WHAT HAPPENS NEXT

Nothing is open on a branch and nothing is ordered. Named, not ordered:
0248's items 8 and 9 (steps and the stone base; a porch roof turning a
house corner); the compose's next term (the envelope rounds and the
per-cell local-maximum clips) if 8 s at 15 roofs is still too slow for
him.

**Carried:** unchanged from [`0260`](0260-report.md).
