# 0243 — report: his second 3D look — the dormer's cheek spill and the step under the overhang; no riser on any edge of the higher roof, and the hidden strip is its roof's territory for the wall cap; PR #81 updated, one commit

**Code, 2026‑10‑11.** No merge has happened since
[`0238`](0238-report.md). His word on [`0242`](0242-report.md), with a
second picture, two places circled:

> *"the gable ends look right on the roof but the gable edges that
> overlap the roof are still not correct. The should not have any spill
> over on the edge of the roof. See the problem area circles on this
> photo. Also notice that the lower roof has a strange 'step' where the
> overhang sits. This shouldnt be there, instead the lower roof should
> just cleanly merge into the gable edge of the upper roof. Fix those
> issues."*

## 0. THE TWO CIRCLES — measured

**The dormer.** The upper circle is the dormer's cheek: a cross-roof
riser on the dormer's EAVES line (x=186, y 300–360), from `rf4`'s
surface up to the dormer's eaves at 216″ — the two 0242 §1 left
standing as "not gable ends". A sheet of roof material hanging from the
dormer's edge to the roof below: the spill.

**The step.** The lower circle is not roof at all. It is the first
floor's north eaves wall `w1` (plan y=120) where it runs under `rf4`'s
gable overhang, x 108–120. `_wall_under_roofs` caps a wall piece by the
roof whose TERRITORY holds it; the territory there was `rf4`'s (156″ up
at that line, clear of the 96″ wall top), so the piece kept its full
box — while west of x=108 the same wall is capped under `rf1`'s eave
(its inner half at 95.5″, its outer half under the eave line lower
still, 88.5–94.5″, the surface continued past the edge). The wall top
jumped at x=108 by up to 7½″: his step. 0241 put `rf1`'s roof back
under the overhang, but not into the territory the walls read.

## 1. THE TWO RULES

**No riser on any footprint edge of the higher roof.** 0242's test —
the higher roof's gable-end line — becomes `_on_footprint_edge`: a rake,
an eaves line, or a hip end's eave line, both points within the edge's
own extent. Nothing of roof material hangs from a roof's edge: under a
gable end the wall climbs; under an overhang the lower roof runs in;
under an eave there is soffit, or the wall. What the riser is still for
is the residual it was built for ([`0174`](0174-report.md)): a
mismatched boundary INSIDE both footprints, where the candidacy strip's
width limit seats one roof's height beside another's — the three-ridge
fixture's sub-inch residue at (756, 553) is the only such left on any
fixture. **This retires two things on the record, and says so in both
tests:** [`0177-ruling`](0177-ruling.md) §3's one legitimate jump, "a
real vertical face on a real footprint edge" (the two-parallel-roofs
positive control: A's eave over B, now open — soffit), and
[`0195-ruling`](0195-ruling.md) §3's dormer closure (its cheeks and face
were three such risers; nothing of roof closes a dormer below its eaves
now — what closes it is what closes a gable, the walls beneath, which
climb into it).

**The hidden strip is its roof's territory, and the lowest roof over a
piece owns it.** `_hidden_overhang_pieces` is now computed with the
clips, before the walls, and each roof's strip is appended to its
territory for `_wall_under_roofs`. Territories then overlap exactly
there (the strip lies under its coverer), so `owner_of` takes, of the
territories holding a piece, the one with the LOWEST surface — the roof
the wall meets first. The roof section meshes the same pieces it did.

## 2. MEASURED

* Risers: base case 0 (was 0 after 0242); R2 **2 → 0**; dormer-gable-check
  2 → 0; the jump control 1 → 0; three-ridge: the four sub-inch residue
  segments only, unchanged.
* `w1` at x=108, both files: the distinct heights on that line are the
  base and the three cap heights under `rf1`'s eave — one profile, no
  96″ — and the piece under the overhang ends at the gable wall x=120
  with the same profile. Before: a fifth height, 96, the box.
* Everything 0241/0242 pinned still holds: `rf1` to x=120, `rf2` to 354,
  nothing below the rakes, the four unchanged fixtures still identical
  with the overhang rule off and on.
* `--quick` 1540 passed; the full gate GREEN on the branch commit.

Pictures re-rendered from the branch:
[`short-angle-roofR2-3d-southwest-built.png`](../evidence/short-angle-roofR2-3d-southwest-built.png),
[`…-northwest-built.png`](../evidence/short-angle-roofR2-3d-northwest-built.png),
and the base case's three.

## 3. TESTS

* `tests/test_roof_overhang_3d.py`, 20: the footprint-edge test (a rake,
  an eave, the inside, a skew segment, past a corner, under a hip and on
  its eave line); no riser on either file, with the edge rule switched
  off as the positive control (13 and 15 found, every one on an edge of
  the higher roof); rays through the dormer's cheek planes hit nothing
  while its own slab does; **the wall profile at x=108** on both files.
* `tests/test_viewer_dormer.py`: the closure test inverted — nothing of
  roof closes the dormer below its eaves, with the control through its
  slab.
* `tests/test_viewer_model.py`: the jump control inverted — no riser,
  the detector with the edge rule off finds the one it used to, and the
  slot under A's eave is open in the mesh while A's surface inside its
  eave is there.

## 4. WHERE IT STANDS

[PR #81](https://github.com/pjm4github/FloorPlanner/pull/81), still ONE
commit on `roof-overhang-build` rebased onto this landing: 0241's
build, 0242's gable ends, this. **AMBER** — his check on R2: no brown
below any roof edge, dormer included; the eaves wall runs under `rf4`'s
overhang at one height to the gable wall. His criterion stands: no end
wrap, then #81 closes.

## 5. `fixtures/incoming/`, with ages

* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 6. WHAT HAPPENS NEXT

His check. Open from [`0241`](0241-report.md) §2: the rule's reach on
the three-ridge slivers and the two-level stacked fixture. Behind it:
the compose cost ([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0242`](0242-report.md).
