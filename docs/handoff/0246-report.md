# 0246 — report: PR #81 merged on his word — the lower roof under the overhang, nothing of roof hanging from a roof's edge, the dormer's sides and face projected up from the roof; the roof-wrap bug closed

**Landed:** PR #81 · 37b58d6 · 2026-10-11 · AMBER · checked by Patrick on his own designs: "the dormers look right"

**Code, 2026‑10‑11.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0241`](0241-report.md)–[`0245`](0245-report.md) put the build to him on
`roof-overhang-build`, one commit, re-made after each of his four 3D
looks. His word:

> *"the dormers look right, land #81"*

Done as said: the branch landed on `main` at **`37b58d6`**,
fast-forward; [PR #81](https://github.com/pjm4github/FloorPlanner/pull/81)
MERGED; the branch deleted, local and remote. His criterion of
[`0242`](0242-report.md) — *"When we have no end wrap then we can close
PR #81 and consider the roof wrap bug closed"* — is met by his own
check: **the roof-wrap bug is closed.** No defect record was opened for
it; the five reports carry its whole history.

## 1. WHAT LANDED, in one place

* **The lower roof runs under the overhang** ([`0241`](0241-report.md)):
  a clipped roof meshes the cells of its own footprint the clip hid,
  wherever their centroid lies outside every wall loop of the covering
  roof's level, cut at the seam.
* **Nothing of roof material hangs from a roof's edge**
  ([`0242`](0242-report.md), [`0243`](0243-report.md)): no cross-roof
  riser on any footprint edge of the higher roof.
* **The wall under the overhang keeps its profile** ([`0243`](0243-report.md)):
  the hidden strip is its roof's territory, the lowest roof over a wall
  piece owns it.
* **A dormer's sides and face are projected up from the roof**
  ([`0244`](0244-report.md), [`0245`](0245-report.md)): wall standing on
  the host, to the eaves and the rake, where the dormer stands on the
  host; a face past the host's eave is left to the house wall, which
  climbs.
* His three designs promoted: `short-angle-roof.json` (0237),
  `short-angle-roofR2.json` (a dormer), `short-angle-roofR3.json` (the
  dormer set back).

## 2. STILL OPEN FROM THE TRANCHE — his to rule

[`0241`](0241-report.md) §2: the overhang rule as ordered also reaches
the three-ridge fixtures (slivers under `rf3`'s soffit at the notch
outside the walls) and the two-level stacked fixture (the first-floor
roof under the second-floor roof where the second floor has no walls).
Kept as the rule says; one line narrows it to a covering roof of a
higher level only.

## 3. `fixtures/incoming/`, with ages

* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 4. WHAT HAPPENS NEXT

His word on §2, or the next design. Behind it: the compose cost
([`0237`](0237-report.md) §0, the patch at
`docs/evidence/roofclip-adjacency-memo.patch`), as its own tranche.

**Carried:** unchanged from [`0245`](0245-report.md).
