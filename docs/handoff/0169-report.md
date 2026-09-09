# 0169 — report: R4e closed — PR #58 merged on Patrick's word; one item named for later

**Code, 2026‑09‑08.** His word, with the plan of the same corner attached:
*"3D view looks right, merge it. There is still an issue that we need to
come back to when there are multiple roof lines at various ridge peak
levels."*

---

## 1. DISPOSITION — R4E CLOSED, MERGED

[PR #58](https://github.com/pjm4github/FloorPlanner/pull/58) merged to
`main` at `e780b56`; branch `roofs-r4e-mesh-clip` deleted in the same merge
step, local and remote. CI green on the final push. Re-gated on the merged
tree: full suite passed, `ruff` clean, gate GREEN — numbers in the commit.

**The roofline plan as it now stands.** [`0139`](0139-ruling.md)'s tranches
R1 → R4c, [`0154`](0154-ruling.md)'s five requirements, [`0164`](0164-ruling.md)'s
R4d (the valley seam, plan) and his own R4e (the same clip in 3D) — **all
merged and checked by him.** Left of the plan: R5, dormers, RED behind its
own ruling; the roof-plan sheet in the exports; yard items.

## 2. THE ITEM HE NAMED — recorded, not started

*"Multiple roof lines at various ridge peak levels."* His picture is the
equal-height L, which is right; what he is pointing past it is the general
case — three or more roofs, ridges at different heights, meeting in one
place. What the built clip does there, so the gap is stated and not
guessed:

* **Every pair is clipped independently**, then a roof's visible region is
  the intersection of what each partner leaves it (`compute_roof_clips`).
  Two roofs are exact. With three, a seam between roofs A and B is kept
  even where roof C actually covers both of them, and a joining end's
  extension is per pair — so a corner where three roofs of different
  heights meet can show a seam that should be hidden, or an extension
  that another roof should have cut.
* **The seam of a lower roof running into a higher one** (the T) and of
  **equal roofs meeting** (the L) are both right, by his own checks.

This is **RED — his own ruling with a case**, not started here: which
configuration, and which of the two readings ("the higher roof wins the
three-way corner" or "the roof whose body is nearest wins") he wants.
Once a plan of his shows it, the receipts follow the pattern of
[`0166`](0166-report.md): the erased-lines picture is the spec.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items;
the stash entry (his call); the End-On marker's placement at a clipped
ridge end ([`0166`](0166-report.md) §3, his one line if wanted).
