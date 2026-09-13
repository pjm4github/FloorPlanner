# 0177 — ruling: Patrick's correction adopted — a point is not a connection, and the anchor is the roof's own ground

**Patrick, 2026‑09‑13, on [`0176`](0176-ruling.md)'s evidence picture:** *"The
light blue triangle to the right of rf2 … should not sit above the green
[roof], because the rf1 ridge completely intersects the rf2 ridge. So the rf1
ridge will end at rf2 and there will only be 2 red lines."* **Correct, and
adopted.** Measured: rf2's ridge crosses rf1's at **(707.454, 468)**, where
both surfaces sit at exactly 132″ — a single-point saddle. East of it rf1's
plane is again numerically higher (margin growing to 10″ at its gable end),
but that ground touches rf1's body **only at that one point.**

---

## 1. TWO AMENDMENTS TO [`0176`](0176-ruling.md) §3 — the rule's precise form

* **Connectivity is shared boundary of POSITIVE LENGTH.** In the exact
  arrangement, a ridge-ridge crossing makes a four-wedge saddle: the two
  equal-height lines cross at the point, and the far wedge touches the near
  body only at that vertex. **A vertex connects nothing.** Under
  edge-adjacency the far wedge is disconnected, surrenders, and rf1 ends at
  the pinch — his two red lines, exactly.
* **The anchor is the component holding the roof's own SINGLE-COVERAGE
  ground** — territory no other roof's footprint reaches. [`0174`](0174-report.md)'s
  "unswallowed ridge end" anchor fails this very fixture: **both** of rf1's
  ridge ends are locally the highest surface, yet the east piece must die.
  Ground only the roof itself covers is the unambiguous root; a piece that
  lives entirely inside other roofs' footprints is a poke-through by
  definition. (A roof wholly inside another's footprint — no single ground —
  anchors at its `marker_end`; none in this fixture.)

## 2. OWNED — my own evidence carried the defect he caught

[`0176`](0176-ruling.md)'s PNG kept the triangle because my raster reference
flood-filled through the pinch: the margin is 0.219″ one inch west of it,
zero AT it, 0.206″ one inch east — **a measure-zero pinch is invisible to
sampling at any grid pitch.** So the receipt for this rule is **analytic,
never sampled**: the far wedge's shared boundary with the body has length
zero, by construction of the two equality lines. The exact arrangement is
the only place this rule can be enforced — one more reason
[`0174`](0174-report.md)'s chassis was right. Evidence superseded:
`docs/evidence/threeridge-reference-junction-v2.png` (committed with this
ruling) shows the corrected junction; the v1 file stays as the record of the
error.

## 3. RECEIPTS ADDED TO R4g ([`0176`](0176-ruling.md) §4 otherwise unchanged)

* rf1's final region contains **no point east of the pinch**; its trimmed
  ridge ends AT (707.454, 468), and **exactly two** rf1/rf2 valleys meet it
  there.
* Adjacency in the reachability graph is asserted as positive-length shared
  edges — a test constructs this saddle in isolation (two crossing ridges,
  equal heights) and the far wedge must surrender.
* The one jump boundary that remains on this fixture is rf3's rake edge
  standing over rf1's low eave corner (≈ (556, 580)–(590, 645)) — **named
  here as CORRECT**, a real vertical face on a real footprint edge, so the
  check doesn't mistake it for a defect.
* T/L regression suites still green, unmodified.

**Carried:** unchanged from [`0176`](0176-ruling.md).
