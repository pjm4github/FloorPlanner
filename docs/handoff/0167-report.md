# 0167 — report: R4d closed — PR #57 merged on Patrick's word; mesh clipping ordered as R4e

**Code, 2026‑09‑07.** His word after the re-check of [`0166`](0166-report.md):
*"The roof seams look good now. Lets merge it then lets enable mesh
clipping."* With his 3D view of the same corner attached — the poke-through
the plan now clips, still standing in 3D.

---

## 1. DISPOSITION — R4D CLOSED, MERGED

[PR #57](https://github.com/pjm4github/FloorPlanner/pull/57) merged to
`main` at `7a76283`; branch `roofs-r4d-clip` deleted in the same merge
step, local and remote. CI green on the final push. Re-gated on the merged
tree: full suite passed, `ruff` clean, gate GREEN — numbers in the commit.

What landed: [`0165`](0165-report.md) (the clip as a pure function of the
roofs, the exact equal-height seam, selected = unclipped) and
[`0166`](0166-report.md) (a joining roof stops at the seam whichever surface
is higher; a joining end extends inside the other roof; the lower surface
takes what neither body reaches). The seams are checked by him.

## 2. R4E — MESH CLIPPING, ORDERED BY HIS SENTENCE

[`0164`](0164-ruling.md) §2 left 3D interpenetrating and named mesh-level
clipping *"not ordered."* His sentence orders it. **R4e: the 3D roof meshes
are built from the same clip the plan draws** — `fp3d.build_model` takes
each roof's visible region (the convex cells `roofclip.py` already
computes), splits every cell by the roof's own plane boundaries so each
piece is planar, lifts it onto the roof surface, and builds the slab from
those pieces; an unclipped roof builds exactly as before (two planes, two
end faces — byte-identical, so R4a's receipt and every existing 3D test
stand); a joined end gets no end face; the seam in 3D falls out where the
cells of the two roofs meet at equal height.

**One structural move it needs, named before it is made:** `roofclip.py`
imports `PyQt6` for `QPointF`, and `fp3d.py` is deliberately Qt-free
(loaded by path, source-grep-guarded — CLAUDE.md). So `roofclip.py` goes
Qt-free — plain points — with `roofs.py` converting at its boundary, and
`fp3d.py` loads it by path exactly as it loads `validate.py`. No behaviour
change in the plan; the same 26 intersection tests must pass unchanged
across the move, which is the receipt for it.

**Tier: AMBER** — his check is the 3D view of the same corner: no
poke-through, a clean valley and hip, nothing past the seam. One branch,
one PR, then stop. R5 stays RED behind it.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items;
the stash entry (his call); the End-On marker's placement at a clipped
ridge end ([`0166`](0166-report.md) §3, his one line if wanted).
