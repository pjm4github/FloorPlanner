# 0166 — report: R4d's check — a joining roof stops at the seam, whichever surface is higher

**Code, 2026‑09‑07, answering Patrick's own check of [`0165`](0165-report.md)
(PR #57), run the same day with two pictures: his plan with the lines he
wanted gone erased by hand, and the 3D view of the same corner. Fixed on
the same branch; still AMBER, his re-check owed.**

---

## 1. WHAT HE FOUND, AND WHAT IT WAS

*"The seam looks OK but the roof should clip at the seam."* Two roofs of
equal height meeting at an L, roof A's ridge running past the apex into
roof B. The seam drew correctly; A's ridge, its gable line and its top
corner beyond the seam were still there, and his 3D view showed A's end
poking out through B's slope.

**That was the rule, not a bug in it.** The first cut kept, in the
overlap, the part where a roof's surface is the *higher* one. Past the
apex, A's ridge IS above B's slope, so A's whole end survived — a gable
poking through, physically real, and not what anyone building that
corner intends. [`0164`](0164-ruling.md) §2's own sentence is the rule,
and it is not a height rule: *"a clipped roof does not extend past the
joining roof."*

## 2. WHAT'S BUILT

The assignment in `roofclip.py` is rewritten around that sentence; the
module docstring carries the full statement.

* **A roof stops at the seam, on the side its own body is on.** Each
  roof's footprint is one set of convex pieces (its cells outside the
  overlap, plus the overlap cells split by the seam). A piece is
  reachable from another across a shared boundary *unless* that boundary
  is a seam segment. A roof keeps what it can reach from its **anchor**:
  the outside cell holding the ridge endpoint that is NOT inside the
  other roof — its far end; every outside cell for a roof the other
  merely runs into, or with neither end inside.
* **What a roof cannot reach it gives up.** An overlap piece neither body
  reaches goes to the roof whose surface is **lower** there: the higher
  one is precisely the cut-off phantom — the far-side island under a main
  shows the main; A's end past the apex shows B's slope. Cut-off pieces
  *outside* the overlap (A's top corner past the outer seam) are drawn by
  nobody: exactly the dashed lines he erased. (A roof with no body
  outside the other at all keeps where it is higher — a dormer-like roof
  poking out of a bigger one; the only sensible reading, named.)
* **A joining end extends.** His picture also showed the outer corner:
  the hip runs from the apex to where the two *outer* eaves meet, which
  lies *behind* B's own end edge. So a roof whose ridge endpoint is
  inside the other does not end at its own end edge there — its planes
  continue, inside the other roof, up to the seam. The footprint is
  extended per joining end for the pair (only inside the other's
  footprint), `RoofClip.ext` carries it, and the item draws its eaves on
  into the extension and **no end line at a joined end** — the end is
  joined, not open. The phantom equal-height branches an extension
  creates over the other roof's body end up with one owner on both sides
  and vanish by themselves.

**The T case is unchanged by all of this**: every prior test in the
module (the lower wing into a main's side, the pocket, the hidden band,
the island, the 45° wing) passes as it did — the receipt that the new
rule contains the old one where the old one was right.

## 3. THE CHECK — receipts

Five new tests (`tests/test_roof_intersection.py`, now 26), the L in closed
form: A's ridge (0,200)–(450,200), B's from the apex (400,200) at 45°,
equal spans and heights. Both valleys from the apex to the inside corner
on A's lower eave and the outer corner on A's upper eave — `(x−400) =
∓(√2−1)(y−200)` — with z₁ = z₂ at every vertex; **A's ridge past the apex
gone while its surface is measured to be the higher one there** (the
precondition that makes the test discriminating), B's slope showing
through; A's corner past the outer seam drawing no line of A and belonging
to nobody; B's start end inside A gone; on the items, A's ridge past the
apex and its gable line neither drawn nor hit, and the whole rectangle
back on select.

Full suite **1252 passed**, 7 deselected (`perf` lane), collected 1259.
`ruff` clean. Gate GREEN. His configuration rendered offscreen and looked
at, clipped and with A selected: A's ridge ends at the apex, its gable line
is gone, both seams draw solid to the two corners, B's start edge is gone,
B's eaves run on to the corners; selected, A shows its whole rectangle and
grips while B stays clipped.

**One thing for his eye that the picture does not settle:** A's End-On
marker still sits at A's *true* ridge end, now inside B's roof area. It
marks the document's geometry, and dragging the end grip is how the
overrun is corrected; if he would rather it hid with the clipped part, that
is one line.

## 4. DISPOSITION

**Still AMBER**, PR #57 updated, his re-check owed: the same corner, plan
and 3D — the plan should now match his erased picture line for line. (3D
still interpenetrates, as [`0164`](0164-ruling.md) §2 ruled; the poke-
through he saw there is the same geometry the plan now clips, and mesh-
level clipping stays named, not ordered.) R5 stays RED behind this.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items;
the stash entry (his call).
