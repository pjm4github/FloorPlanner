# 0188 — report: R5a merged on his word; the 3D wall clip, built; AMBER, stopped for his look

**Code, 2026‑09‑13.** Patrick's check of R5a passed — his words, in full:
*"OK the dashed lines look good. The only minor change we need is to clip
the walls to the roof when viewing in 3D. At the moment the walls stick
up through the roof."* On the first sentence PR #61
(`roofs-r5a-clip-trace`) was landed on `main` at `7bee95c`, fast-forward,
the branch deleted local and remote. The second sentence is **his own
direct instruction as authority** ([`0065`](0065-ruling.md) §2, quoted
here as [`0068`](0068-ruling.md) §5 requires) for what this report builds
— a `viewer/fp3d.py` change, AMBER because it changes what he sees in the
3D view. Branch `roofs-3d-wall-clip` off `main` at `7bee95c`, PR #62
open, gate GREEN, **stopped for his 3D look**. [`0186`](0186-ruling.md)
§3's dormer read-back and §4's R6 are untouched; this sat between them
on his word, and it is the only AMBER tranche open.

## 1. WHAT'S BUILT

**The roof clips come first now.** `build_model` used to compute the
roofs' intersection clips (R4d/R4g's `compute_roof_clips`) in the roof
section, after the walls were already solid prisms. That block moves
ahead of the walls unchanged, and records each roof's **territory** on
its level: its visible region's cells when it has a partner, its whole
footprint when it has none. The roof section reuses the same result, so
the roof meshes are byte-for-byte what they were.

**Every solid piece of a wall is capped at the roof over it**
(`_wall_under_roofs`). The wall loop already builds each wall as pieces —
piers between openings, the wall under a sill, the header over a head —
each a plan quad between two heights. Each piece now goes through one
function that:

* splits the quad by the edge lines of every nearby territory cell, so
  each resulting piece lies wholly inside or outside every cell;
* gives each piece to the roof whose territory holds it — **that roof's
  surface, not the lowest plane passing overhead**: under a cross gable
  the main's plane continues beneath the wing as a phantom, and R4d's
  territory is exactly the record of which roof is really there;
* gives a piece that no territory holds, but that lies within the wall's
  own thickness of one, the nearest roof's plane **continued** past its
  edge — the outer half of an eaves wall with no overhang, where the eave
  line sits on the wall's centreline. Without this a thin fin of wall
  would stand up beside every zero-overhang eave;
* leaves a piece further than that from every roof at full height. The
  roof does not cover it; the model does not pretend it does;
* splits an owned piece by the roof's own plane-change lines (its ridge,
  a hip end's two equal-height lines) so the cap on each sub-piece is one
  plane, then cuts at the two level sets that matter — the piece's top
  (roof above it: the wall keeps its top there) and its base (roof below
  it: that part of the piece is gone, e.g. a window header wholly above
  the roof) — by exact interpolation on the vertex heights, never
  sampled;
* emits a capped piece as a solid with its top ring **on the roof's top
  surface** and a flat base (`_prism_slab` gains `bottom_z`), so a wall
  under a roof that sits exactly at its top is unchanged, and a lower
  roof hides the wall's end inside its own slab thickness.

**What does not change.** A plan with no roofs, a wall on a level with no
roof, a roof on another level, and a plan whose roofs all clear their
wall tops each build the walls **byte-identically** to before (the
function returns the original box whenever no roof intrudes on the
piece, asserted by array equality). Nothing is stored; no schema, dialog
or setting is touched; the plan view is untouched.

## 2. THE CHECK — receipts

`tests/test_viewer_wall_clip.py`, **10 tests**, Qt-free (fp3d loaded by
path, as every viewer test is). On the 300×200 shell with the ridge run
end to end (eaves 80″, ridge 132″, 96″ walls — the same closed form as
the R3b/R5a files, the roof crossing the wall top 69.23″ off the ridge):
no wall vertex above the surface, with the roofless build as the
positive control; the gable wall's top at the eaves height at both
corners, at the wall top at both crossings, and flat under the ridge; the
zero-overhang eaves wall capped by the continued plane (its top within
half a thickness of the eaves height, no fin); a roof clearing every wall
top → walls array-equal to the roofless build; a far wall one plain box
at full height; a window header wholly above the roof gone while its
under-sill piece survives at the opening's width; a roof on another level
capping nothing; the L (main over wing, eaves 80″) — a wall across the
wing's body capped by the **wing's** surface, 80″ at its eave, and
standing full height beyond it, a real step because nothing roofs it
there; every top face wound upward. **His own three-ridge fixture** at
the viewer's 120″ wall-height override (its own 96″ walls never top its
96″ eaves): the roofless control has wall vertices above the owning
roofs, the clipped build has **0**, and a ridge still clears a wall at
120″.

Full suite **1308 passed**, 7 deselected (`perf` lane), `ruff` clean,
gate GREEN — the branch's own run. Capping cost on the three-ridge
fixture: **0.07 s** (the roof clip itself is the 0.36 s
[`0182`](0182-report.md) named); wall vertices 136 → 438 there.

**No picture.** `fp3d.py`'s GL render needs a real display (D77; the
snapshot's own trap), so the receipt is the census above, not a shot.
His look is the check.

## 3. NAMED LIMITS

* **A wall no roof reaches keeps its full height** — including the run
  of a wall that leaves a roof's footprint sideways (the L test's step).
  Correct as a model; if a real plan shows a wall he expected covered,
  that is a roof whose footprint stops short, not this clip.
* **The cap is the roof's top surface**, not its underside. From outside
  nothing shows; in x-ray the wall's end sits inside the slab's 4″. The
  underside is one constant if he wants it.
* **Two unclipped roofs sharing ground** (a coplanar pair, which R4d
  leaves unclipped with a warning) both claim it; the first in document
  order caps. Same surface either way, by definition of coplanar.
* **Adjacent capped pieces share internal faces** (each piece is a closed
  solid). Invisible opaque; a faint doubling in x-ray. Named, not fixed.

## 4. `fixtures/incoming/`, with ages

Unchanged from [`0187`](0187-report.md) §4: `README.md` (2026‑08‑23),
`w7offgrid.fpm` and `w7offsetFloorplan.json` (2026‑08‑21, 23 days), both
byte-identical duplicates of the promoted fixtures. Exit 2 on his word.

## 5. WHAT HAPPENS NEXT

His 3D look at wiscaway with roofs on. On his word PR #62 merges,
branch deleted in the merge step. Then [`0186`](0186-ruling.md) §3's R5b
dormer read-back — a report, no code — RED until he rules on it.

**Carried:** unchanged from [`0187`](0187-report.md) and
[`0186`](0186-ruling.md) §5.
