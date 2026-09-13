# 0176 — ruling: the notch is the `_strip` residual, not a mystery — candidacy becomes the footprint, and phantom boundaries become illegal

**Patrick, 2026‑09‑13, with the 3D notch and the plan's wrong seam graph on
screen, and his own red-line drawing of what should draw.** Read for this
ruling: [`0174`](0174-report.md)/[`0175`](0175-report.md), `roofclip.py`, the
fixture — **and a full reference implementation of the ruled model, run on
his fixture** (evidence: `docs/evidence/threeridge-reference-junction.png`).

---

## 1. THE DIAGNOSIS — the record already contains it

[`0174`](0174-report.md)'s arrangement rebuild is the right chassis and is
**endorsed** — one shared decomposition, exact envelope per cell, concurrent
triple point. But its §6 residual is not a residual; **it is the defect he
is photographing.** `_strip` limits a joining roof's candidacy to an
arbitrary width rectangle, so ownership boundaries exist **in the interior
of an overlap** that are neither a seam nor any real edge of either roof —
27 of them, height jumps to ~30″. In 3D those are phantom vertical faces:
the jagged notch. [`0175`](0175-report.md)'s risers paper them over —
honestly disclosed as such — and the plan view never trims ridge ink to
owned ground at all, which is his second image: full-length ridges sailing
through other roofs, no connected valley graph.

## 2. MEASURED CONFIRMATION — the ruled model produces his red drawing

I implemented the rule below independently and ran it on
`threeRidgeFloorplan.json` (raster reference, 2″ grid). The result — the
evidence PNG — **is his red-line drawing**: the valleys meet in a connected
junction around the triple point (681.59, 538.07, h=117.5), `rf1`'s ridge
ends ON the junction, `rf3`'s swallowed ridge end is trimmed, and **every
height-jump boundary that remains lies on a roof's own footprint edge**
(a gable end standing above a lower neighbour — real architecture, a real
vertical face), never in the interior. On this fixture the reachability
fixpoint surrenders nothing — pure envelope is already anchor-connected —
so the change is safe exactly where the current code is wrong.

## 3. THE RULE — three sentences replace the strip

* **Candidacy is the roof's own footprint. Exactly. Nothing narrower
  (`_strip` retires), nothing wider (no extended planes — the failed
  attempts' mistake).**
* **Reachability is a global fixpoint:** each roof keeps only the piece of
  its winning territory connected to its own anchor; a surrendered piece
  falls to the next-ranked candidate **and connectivity is re-measured
  after every surrender, until stable.** This — not a wider candidacy
  shape — is what protects the L-case's excluded corner: that corner piece
  is disconnected from the joining roof's anchor and falls to the host.
  [`0174`](0174-report.md) §6's two regressions widened candidacy without
  this fixpoint; that is why they failed.
* **THE INVARIANT, testable and absolute:** every cross-roof boundary is
  either a true seam (heights equal, drawn solid) **or lies on a real
  footprint edge of one of the two roofs** (gable end / eave line — built
  in 3D as a genuine vertical face, which is what `_cross_roof_risers`
  matures into). **A height jump anywhere else is a bug by definition.**

**Plan view:** ridge ink draws only over ground the roof finally owns;
seams draw solid; the junction graph must be CONNECTED — every trimmed
ridge endpoint lands on a seam vertex. That is his red drawing, verbatim.

## 4. TIER, RECEIPTS, AND ONE TEST THAT MUST FLIP

**AMBER, one branch (R4g), then stop.** Receipts on the fixture: interior
height-jump boundaries = **0** (was 27); every remaining jump lies on a
named footprint edge; the junction graph connected as §3; the T/L
regression suite green **unmodified**; and [`0175`](0175-report.md)'s
riser **positive-control test is REWRITTEN, not left standing** — it
currently *requires* the fixture to produce a riser, so it would fail the
fix or silently defeat it ([`0124`](0124-ruling.md) §1's
receipt-reversal discipline). Fold in the gable-end-triangle fix by
[`0174`](0174-report.md) §5's own named method (clip the plan line,
interpolate the 3D edges) — it is the other visible edge defect at this
junction — and re-check §6's "unresolved visual artifact" after: it is
most plausibly this same residual, and if it survives, it gets its own
narrow investigation, not a guess.

> **His check:** the plan view of the fixture matches his red drawing —
> connected valleys, trimmed ridges, nothing sailing through — and the 3D
> junction is clean at [`0175`](0175-report.md)'s own screenshot angle.

**Carried:** D83/D84 (held); room-label rounding ([`0131`](0131-ruling.md)
§2); delta-snap sites; D61-family; yard items; the End-On marker at a
clipped ridge end ([`0166`](0166-report.md) §3).
