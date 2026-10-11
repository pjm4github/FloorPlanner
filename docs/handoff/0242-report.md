# 0242 — report: his 3D view of the gable ends — the brown wrap is the cross-roof riser on the higher roof's gable-end line; gone, on `roof-overhang-build` with 0241's build, PR #81; his `short-angle-roofR2.json` (a dormer added) promoted

**Code, 2026‑10‑11.** No merge has happened since
[`0238`](0238-report.md). His word on [`0241`](0241-report.md), with a
new file in `incoming/` and a picture of the base case's 3D view, four
places circled:

> *"I have added another file which is an augmented version of the test
> file called 'short-angle-roofR2.json' which includes a dormer as well.
> In addition I have dropped a 3D view that still shows the problem. You
> can see that the red circles 'brown roof' components wrap around the
> gable ends and come down to the roof below. The brown roof material
> should not cover the gable ends. For that. When we have no end wrap
> then we can close PR #81 and consider the roof wrap bug closed."*

## 0. WHAT THE CIRCLES ARE — measured

Every circled face is a **cross-roof riser** (`_cross_roof_risers`,
R4f/0175): the double-sided vertical quad the builder adds wherever two
roofs' territories meet at unequal height, to close the slot between
their separately extruded skirts. At `rf4`'s west rake, x=108, its
territory meets `rf1`'s; `rf4` is 60″ higher all along that line, so a
riser ran from `rf1`'s surface (96″ at the eaves, 216″ at the ridge) up
to `rf4`'s (156″ to 276″) — a sheet of roof material hanging from the
rake to the roof below, the gable end wrapped. The same at x=366 over
`rf2` and `rf3`, at `rf2`'s own rake x=426 over `rf3`, and on `rf3`'s
rake over the junction. **On the base case: 13 risers, every one on the
gable-end line of the roof standing higher there.** The dormer in R2
adds two more, on its eaves lines — its cheeks, not gable ends.

0241's build did not touch this: it put `rf1` back under the overhang,
and the riser still hung in front of it.

## 1. THE RULE — one test in the riser detector

**No riser on the higher roof's gable-end line.** `_on_gable_end_line`:
the line through a gable ridge end perpendicular to the ridge (a hip end
has none — its slope runs on to the eaves). For each mismatched boundary
segment the detector finds, the roof higher along it is taken, and if
the segment lies on that roof's gable-end line the riser is skipped. A
gable end is open ([`0223`](0223-report.md) §3): nothing of roof
material belongs below the rake; the wall beneath climbs, and under an
overhang the lower roof runs in to it (0241). The LOWER roof's own
gable-end line is not exempt — a riser rising from its rake to a higher
roof's eaves above it is not covering its gable.

Result: **base case 13 → 0 risers; R2 13 → 2**, the dormer's cheeks at
x=186 and 282, from `rf4`'s surface up to the dormer's eaves.

## 2. WHAT ELSE THE RULE REACHES — two tests rewritten, said so

* **The dormer's front.** [`0195-ruling`](0195-ruling.md) §3 demanded
  the geometry closing the dormer below its eaves be named and probed;
  the probe found the risers closing its two eaves planes AND its face.
  The face is a gable end: by his word it is now open, and the test says
  so (the cheek rays hit, the face rays hit nothing, risers or no
  risers). A wall drawn beneath the dormer's face climbs into it
  (`test_a_wall_under_a_dormer_climbs_into_its_roof`). In R2 the dormer's
  front stands 6″ past `rf4`'s eaves line, so nothing met it there
  anyway.
* **The three-ridge fixture.** [`0181-ruling`](0181-ruling.md) named
  one riser CORRECT — `rf3`'s rake over `rf1`'s low eave corner, a 30″+
  step on a footprint edge — and the test required it. That is exactly
  a riser on the higher roof's gable-end line, and it is gone; the test
  now asserts no footprint-edge riser with a real step remains, the
  residue clause unchanged. **One thing to know:** that fixture's walls
  are all typed `interior`, and interior walls do not climb, so under
  `rf3`'s rake there the gable is open to the attic. On exterior walls
  — his R2, every wall — the gable wall climbs.

The dormer-gable-check fixture keeps its two cheek risers (its face,
y=190, was the third; gone). The jump fixture (two parallel roofs
overlapping at their eaves) keeps its one riser: an eaves line, not a
rake.

## 3. ON HIS R2 FILE — promoted

`fixtures/short-angle-roofR2.json`, under exit 1, his sentence as its
row. The base case's four roofs (`rf3`'s ridge re-drawn slightly) plus
`rf5`, a gable dormer on `rf4`'s south slope (ridge x=234, y 366→252,
spans 48, eaves 120″/ridge 168″ over `L2`, `host: rf4`) and one more
`L2` wall. Measured on it: `rf1` reaches x=120 and `rf2` x=354 as on
the base case; rays through `rf4`'s rake planes inside the gap between
the lower roofs and its underside hit no roof triangle (before, each hit
the riser); the dormer's cheeks stay closed.

Pictures, all from the branch as it stands:
[`short-angle-roofR2-3d-southwest-built.png`](../evidence/short-angle-roofR2-3d-southwest-built.png)
(near his viewpoint),
[`…-northwest-built.png`](../evidence/short-angle-roofR2-3d-northwest-built.png);
the base case's three `-built.png` pictures re-rendered, since the x=108
riser stood in two of them.

## 4. THE RECEIPT

* `tests/test_roof_overhang_3d.py`, now 19: the R2 fixture is the base
  case plus the dormer; `_on_gable_end_line` knows a rake from an eave,
  from the inside, from a skew segment and from a hip end; on both files
  no riser stands on any roof's gable-end line (base: none at all; R2:
  x=186 and 282 only); rays through `rf4`'s rake planes hit nothing,
  with a control ray through `rf4`'s own slab that does; the short roofs
  still reach their gable walls on R2 and the cheeks stay.
* `tests/test_viewer_dormer.py` and `tests/test_viewer_model.py`
  rewritten as §2 says, each docstring carrying his word and the date.
* `--quick` 1538 passed; the full gate GREEN on the branch commit.

## 5. WHERE IT STANDS

[PR #81](https://github.com/pjm4github/FloorPlanner/pull/81) carries
0241's build and this fix as ONE commit on `roof-overhang-build`,
rebased onto this landing (the branch is force-updated; the push hook
reads the snapshot marker, which must be `main`'s tip). **AMBER** — his
check of the 3D view on R2: no brown below any rake; the short roofs run
in under `rf4`'s gable overhangs to the gable walls; the dormer's cheeks
closed, its front open. His criterion is his own: *"When we have no end
wrap then we can close PR #81."*

## 6. `fixtures/incoming/`, with ages

* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 7. WHAT HAPPENS NEXT

His check of PR #81 on R2. Open from 0241 §2: the rule's reach on the
three-ridge slivers and the two-level stacked fixture, his to keep or
narrow. Behind it: the compose cost ([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0241`](0241-report.md).
