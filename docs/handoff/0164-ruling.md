# 0164 — ruling: roof intersection clipping — the valley item comes due as R4d

**Patrick, 2026‑09‑07, with R4 fully closed ([`0163`](0163-report.md) —
verified: PR #56 merged, branch gone, board clean):** intersecting roofs
clip at the intersection; the seam is a real drawn edge; a clipped roof
does not extend past the joining roof; **a selected roof shows its entire
unclipped outline, and re-clips on deselect.** The item named-not-ordered
since [`0139`](0139-ruling.md) is now ordered.

---

## 1. THE MODEL — derived, never stored. His own select rule proves it

**The schema does not change.** The roof's own rectangle
(`ridge`/`span_in`/`overhang_in`) stays the document's truth; the clip is a
**pure function of the `roofs` block**, recomputed whenever any roof
changes. That is exactly what his select/deselect behaviour requires — the
grips must edit the true rectangle, so the true rectangle must survive
underneath — and since [`0154`](0154-ruling.md) put the footprint fully in
the document, the whole computation is headless-testable with no scene.

## 2. THE GEOMETRY — three rules

* **The seam is the equal-height locus** of the two roof surfaces over the
  plan. Planar faces ⇒ straight segments (the valley), constructed exactly,
  not sampled. Drawn **solid** — a real edge, his words — distinct from the
  dashed eave/gable lines.
* **A roof draws only up to the seam.** The portion of its footprint beyond
  it — where it would pole out the far side of the joining roof — is
  dropped from the drawn path (and from the clickable `shape()`, so D85's
  lesson carries: what paints is what hits).
* **Selected = unclipped.** Selection shows the full rectangle, outline and
  grips on true geometry; deselect recomputes the clip and redraws. The
  re-clip also runs after any grip drag or dialog apply.

**Scope: roofs on the same level clip each other** — the wing/main case.
Cross-level clipping is one line from Patrick if ever wanted, not assumed.
**Degenerate configs (coplanar or parallel equal-height surfaces) draw
unclipped with a `Sheet`-style warning** — honest fallback, never a crash.
**3D stays interpenetrating for now** — correct from outside; mesh-level
clipping and seam lines in the exports stay named, not ordered.

## 3. TIER AND CHECK

**AMBER, one branch (R4d), then stop.** Receipts, on the wiscaway main +
45° wing: seam segments exist and every seam vertex satisfies z₁ = z₂
exactly; the wing's far portion is absent from both paint path and hit
shape; select → full rectangle → deselect → re-clipped, as a round trip.

> **His check:** run the wing's roof into the main roof. The valley seam
> draws as a real edge; nothing pokes out the far side; selecting the wing
> shows its whole rectangle; deselecting re-clips it.

R5 (dormers) stays RED behind this, its own ruling when wanted.

**Carried:** D83/D84 (held); room-label rounding ([`0131`](0131-ruling.md)
§2); delta-snap sites; D61-family; yard items; the stash entry (his call).
