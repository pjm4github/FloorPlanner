# 0170 — ruling: the three-ridge case arrives — the clip becomes the upper envelope, computed globally

**Patrick, 2026‑09‑11:** *"3 roof lines coming together. The tool doesnt draw
the roof intersections correctly… find a way to correctly compute the
intersection of the 3 ridges."* This is the case [`0169`](0169-report.md) §2
held RED waiting for — **his fixture answers it, and this ruling orders it.**

---

## 1. THE FIXTURE, MEASURED — `fixtures/incoming/threeRidgeFloorplan.json`

Three roofs on `L1`, all ridges at 132″ over 96″ eaves, **spans differing per
side (174/144, 142.6/151.4, 125.2/131.4 — so every plane has its own
pitch)**, ridges converging near the plan's middle-right. **The three
surfaces genuinely meet: a triple point exists at ≈ (682, 538), all three
heights ≈ 117.5″** (my grid estimate; Code constructs it exactly). The three
pairwise valleys must run INTO that point and stop. The built clip composes
pairs ([`0169`](0169-report.md) §2's own admission): a seam between A and B
survives where C is above both, and the joining-end extension is per-pair —
which is exactly the wrong drawing he is seeing.

## 2. THE RULE — the higher roof wins. [`0169`](0169-report.md)'s question is answered

**RULED: visibility is the upper envelope of all roof surfaces on the
level.** A point of roof A's footprint draws iff no other roof covering it
is strictly higher. **A seam draws where the top two surfaces are equal AND
no third is higher** — equal-and-maximal, both conditions. The alternative
reading, "the roof whose body is nearest wins," is **rejected**: it is not
how intersecting roofs build, and it has no exact locus to construct.

**Computed globally, not pairwise-composed:** one cell decomposition of the
footprints' union, cut by every roof's own plane-change lines (each ridge,
each hip end's lines) — inside a cell every surface is linear, so maxima,
equalities, and the triple point itself are exact constructions,
[`0165`](0165-report.md)'s own idiom widened from two surfaces to n. The
connected-component drop ("a roof does not extend past the join") runs
against the **composite** visible region, never per pair. **New invariant,
and the strongest receipt this feature has: the visible regions PARTITION
the union of footprints — no point painted by two roofs, none by zero.**
The two-roof cases (his checked T and L) must come out **identical** —
the envelope reduces to the pair rule when n = 2; that is the regression.

## 3. TIER AND CHECK — R4f, one branch, then stop

**AMBER.** Receipts: the fixture promoted under exit 1 with the tests naming
it; the three seams terminate at the exactly-constructed triple point, with
no seam segment beyond it; every seam vertex equal-and-maximal; the
partition invariant on the fixture AND the existing pair fixtures
(byte-identical clip results there); R4e's mesh rebuilt from the corrected
plan clip on this fixture — 3D follows for free, by its own design.

> **His check:** open `threeRidgeFloorplan.json`. The three valleys meet at
> one point and stop; no seam runs past another roof; nothing pokes
> through; select any of the three → whole rectangle, deselect → re-clipped.

**Scope note:** this fixture's ridges are equal-height; his named "various
ridge peak levels" case is **the same rule with no special case** — a
second fixture with unequal ridges is welcome for the receipts, the rule
does not change.

**Carried:** D83/D84 (held); room-label rounding ([`0131`](0131-ruling.md)
§2); delta-snap sites; D61-family; yard items; the End-On marker at a
clipped ridge end ([`0166`](0166-report.md) §3, his one line if wanted).
