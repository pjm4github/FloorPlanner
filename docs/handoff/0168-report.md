# 0168 — report: R4e — mesh clipping: the 3D roofs are built from the plan's own clip

**Code, 2026‑09‑07, answering Patrick's sentence after R4d's merge
([`0167`](0167-report.md) §2): *"then lets enable mesh clipping."* Built as
named there, on branch `roofs-r4e-mesh-clip`.**

---

## 1. WHAT'S BUILT

**The structural move first, as [`0167`](0167-report.md) §2 named it.**
`roofclip.py` is now Qt-free: the toolkit point type is gone from the
module (a point is anything with `.x()`/`.y()`; everything the module
creates is its own `Pt`), the unused path helper is gone, and **`RoofGeom`**
— the Qt-free twin of `RoofItem`'s geometry, built from a document roof
record with the loader's own bare-number tolerance — lets a document be
clipped with no scene at all. `roofs.py` converts at its boundary. **The
receipt for the move:** the 26 intersection tests pass unchanged across
it, and a new test pins `RoofGeom`'s eave ends against `RoofItem`'s on the
same record, hip extension included.

**Then the meshes.** `viewer/fp3d.py` loads `roofclip.py` by path, exactly
as it loads `validate.py`, and computes the intersection clip per level on
the document's own roofs before any mesh is built:

* **A roof with no partner builds exactly as before R4e** — two planes, two
  end faces, byte-identical — so R4a's re-save receipt and every existing
  3D test stand (the lone-roof face count is asserted again).
* **A clipped roof is built from its visible region's cells.** Each cell is
  split by the roof's own plane boundaries (its ridge line, a hip end's
  equal-height lines) so every piece lies in one plane, lifted onto the
  surface with the same `surface_height` the plan's seam was found with,
  and emitted in fp3d's world frame. **The seam in 3D falls out** where
  the two roofs' cells meet at equal height — no second seam computation.
* **A joined end gets no end face** (it is inside the other roof); an
  unjoined gable end keeps its vertical triangle; a hip end's face is
  already among the cells.
* Clip warnings land in `model.info`; a missing `roofclip.py` is a note
  and unclipped roofs, never a crash.

**What the gate caught on the way:** the end-assignment census read
`RoofGeom`'s `self.p2 = …` as the retired wall-end spelling (it polices the
literal text project-wide, as `RoofItem`'s own docstring says); the twin
now has read-only `p1`/`p2` properties, like the item.

## 2. THE CHECK — receipts

Five new tests in `tests/test_viewer_model.py` (now 40): `roofclip.py`
loads by path; a lone roof builds with R3's own face count and no note;
**the T** — no vertex at the wing's height at its far ridge end, the main's
surface there instead (z = 123), the apex a shared vertex at the wing's
ridge height (z₁ = z₂), and nothing of the wing's ridge in the band strictly
between the island edge and the apex; **his own 3D picture, the
equal-height L** — A's ridge end carries only B's surface height, never A's
150, the outer corner is a seam vertex at the eaves height, the apex at
150; and `RoofGeom` against `RoofItem`.

Full suite **1257 passed**, 7 deselected (`perf` lane), collected 1264.
`ruff` clean. Gate GREEN.

**Not rendered here, said plainly:** `fp3d`'s GL view needs a real display
(CLAUDE.md, D77); the receipts above are the mesh's own vertices, which is
what the view draws. His check is the view.

## 3. DISPOSITION — AMBER, PR open, waiting

**R4e is AMBER.** PR up on `roofs-r4e-mesh-clip`, not merged until his
check: the 3D view of the same corner as his picture — no poke-through, a
clean valley and hip, nothing past the seam; and the T (a lower wing into a
main's side) for the other case. R5 stays RED behind it.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items;
the stash entry (his call); the End-On marker's placement at a clipped
ridge end ([`0166`](0166-report.md) §3, his one line if wanted).
