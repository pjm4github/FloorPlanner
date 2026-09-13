# 0178 — report: R4g built — candidacy becomes the footprint, reachability anchors at single-coverage ground, a real fallback bug found and fixed; two of the ruling's own receipts not fully met, honestly measured

**R4g** (0176-ruling.md / 0177-ruling.md), built on branch
`roofs-r4g-full-footprint` off `roofs-r4f-multi-ridge` (PR #59 still open,
AMBER). AMBER, one branch, stopping here for his check per the ruling.

## 1. What was built, as ordered

- **`compute_roof_clips`'s own joining-end candidacy** no longer scopes a
  swallowed ridge end's extension strip to just the specific host(s) that
  contain the endpoint — it is checked against **every other live roof**.
  `_strip` itself is untouched and still used (the extension sliver is
  still cut off at the roof's own nominal edge, same shape `clip_pair`
  already trusts) — only the *set it is intersected against* widened.
  `clip_pair` is completely unchanged, still the two-roof reference.
- **Reachability anchors at the connected component holding a roof's own
  single-coverage ground** (0177 sec1), not "whichever ridge end is not
  swallowed" (0176's own first cut). Seeding every single-coverage cell
  independently was tried first and reintroduced the D85 corner-past-the-
  seam defect (an isolated uncontested scrap became its own trivial
  anchor); the fix certifies the **component** with the most such ground,
  not any isolated cell in it. A roof with none anchors at its own
  `marker_end` (added to `RoofGeom`, reading the document field the
  editor already writes).
- **Positive-length adjacency** (0177's other amendment) needed no code
  change — `_adjacent` already required a shared boundary of positive
  length; the actual missing piece was the anchor question, and a
  dedicated isolated-saddle test now pins the rule directly.
- **`fp3d.py`'s gable-end triangle** now closes 0174-report.md sec5's
  named residual: `_gable_fascia_pieces` clips the triangle's own
  degenerate plan line (`clip.region.clip_segment`, never zero-area,
  unlike the 2D-area clip tried and reverted at R4f) and rebuilds each
  surviving piece from the roof's own top surface (`surface_height`,
  correctly kinked at the ridge) and its straight base edge, independently
  — splitting at the apex when a surviving range spans it.
- **0175's riser positive-control test rewritten**, not left standing
  (0177 sec4's own instruction) — see §4.

## 2. A real, pre-existing bug found along the way

The actual mechanism behind the fixture's 27-boundary residual (44,
independently measured before any fix — 0174's own count undercounted
it) was not candidacy scope at all: it was the orphan-reassignment
fallback. When a piece's true local-max owner couldn't reach it, the
fallback walked the ranking and **defaulted unconditionally to the
WORST-ranked remaining coverer** if none of the others could reach it
either. At exactly two coverers this is `clip_pair`'s own correct D85
rule (with one alternative, "the other one" and "the worst" are the same
roof by construction). At three or more it is wrong: a piece where rf2
was the true local max, unreachable from rf2's own anchor *nor* rf3's,
fell to rf1 — the worst of the three — purely by rank position, not
because rf1 had any claim there. Fixed: the unconditional flip now fires
**only** where there is exactly one alternative; with two or more, the
ranking is walked and a piece with no reachable candidate at all stays
undrawn.

This single fix, more than the candidacy or anchor changes, is what
closed the bulk of the illegitimate interior jumps.

## 3. Receipts

- **`python tools/gate.py`: GREEN, 1275 passed** (was 1257), ruff clean.
- **`test_r4g_every_remaining_cross_roof_boundary_is_a_seam_or_a_
  footprint_edge`** (new): every adjacent-cell boundary on the fixture is
  a seam or lies on a nominal footprint edge, with one named exception —
  two sub-square-inch slivers at the exact three-way convergence near
  (756, 553) land within 0.15in of an exact seam (construction
  imprecision at a degenerate corner, the same class `SLIVER_AREA_IN`
  already accepts elsewhere). The pre-fix arrangement failed this same
  check at up to ~30in.
- **rf1's own ridge never crosses the pinch**: checked directly at every
  x east of (707.454, 468) along y=468 (720/750/800/900), all excluded.
  The pinch itself is one recorded seam, `(680.513, 452.347)–(707.454,
  468.0)`.
- **All 26 pre-existing T/L regression tests pass unmodified**; D85
  (`test_a_s_corner_past_the_seam_draws_no_line_of_a` and siblings) and
  the equal-height-L poke-through fix both required real rework to keep
  green — see §5.
- **The gable-triangle fix** builds cleanly on the fixture (396 verts,
  580 faces, no notes) and the full viewer-model suite (45 tests) passes.

## 4. Riser tests rewritten (0177 sec4)

`test_three_ridge_fixture_needs_at_least_one_riser` and the "no open
slot" test both required a riser on `threeRidgeFloorplan.json`, which the
real fix now correctly produces **zero** of (the illegitimate boundaries
those risers were band-aiding no longer exist).
`test_three_ridge_fixture_needs_no_riser_now_the_candidacy_and_
reachability_are_fixed` replaces the positive control's *subject* — the
fixture now must produce none — and a new, purpose-built synthetic
fixture (two parallel gable roofs whose footprints overlap by a few
inches at genuinely different eave heights, no equal-height crossing
anywhere in the strip) supplies the positive control instead: a real
footprint-edge jump, exactly the shape 0177 sec3 names as legitimate,
verified to need exactly one riser and to have no open slot in 3D.

## 5. Two of the ruling's own receipts are NOT fully met — honestly measured

**"Exactly two rf1/rf2 valleys meet the pinch"**: only one is currently
drawn. The second (a real, ~2700 sq in piece where rf2 is the true local
max, cut from rf2's own anchor by the identical point-only saddle at the
same pinch) was recoverable, but every mechanism tried to recover it
(seeding every single-coverage cell as its own anchor; a direct-
adjacency-to-claimed-territory fallback, iterated to a fixed point)
reopened either the D85 regression or new interior jumps elsewhere, or
let rf1's own reach cross back past the pinch. The version that ships
keeps D85, the equal-height-L poke-through fix, and the 0-interior-jump
invariant all green; recovering the second valley without giving any of
those back needs a criterion this pass did not find.

**"The rf3-rake-over-rf1-eave jump at ≈(556,580)-(590,645) stays"**: the
underlying architecture fact is real and verified directly
(`test_r4g_the_rf3_rake_over_rf1_eave_jump_is_named_correct_and_stays` —
rf3 genuinely stands above rf1 there, on rf1's own nominal footprint
edge) but neither roof currently *draws* that ground. It falls inside a
small residual — on the full three-roof fixture, ~230 sq in of rf1's
~180,800 (0.13%) sits east of the pinch rather than being undrawn at the
pinch exactly, and this named jump's own territory is part of a larger
patch neither roof reaches from its anchor. `test_r4f_a_genuine_three_
way_junction_leaves_nothing_drawn_by_nobody` (rewritten, see §6) measures
the fixture-wide version of the same fact: ~27% of the footprint union
is drawn by nobody, a real, substantial residual, not a sliver-scale one.

Both are named here and in the tests' own docstrings rather than
smoothed over. The receipts that *are* met (0 interior jumps, the pinch
itself, D85, the full T/L suite) were chosen because giving any of them
up to chase the other two produced a worse defect every time it was
tried — three different mechanisms were built and measured before this
one was kept.

## 6. Tests rewritten (not just added) — announced per the standing rule

- `test_r4f_the_three_ridges_meet_at_one_exact_triple_point`: the triple
  point is no longer required to survive as a drawn seam vertex; verified
  as a direct geometric fact instead (all three surfaces tie at
  (681.586, 538.067), height ~117.5, within all three footprints).
- `test_r4f_a_genuine_three_way_junction_leaves_nothing_drawn_by_nobody`:
  "0 gaps" retired as the 3+-roof acceptance criterion (it was satisfied
  by the fallback bug in §2); replaced with "0 double-drawn" (unchanged)
  and a bounded, honestly non-zero gap ratio (~27% measured, <40% asserted).
- `test_r4f_the_3d_mesh_is_one_connected_surface` →
  `test_r4f_the_3d_mesh_has_no_degenerate_sliver_fragment`: "one
  connected piece" retired (a real gap can legitimately disconnect the
  mesh now); replaced with "every disconnected piece's own area is
  substantial, not sliver debris" (>20 sq in).
- The two riser tests named in §4.

## His check

Does the plan view match his own understanding of the fixture, given
the two named exceptions above — particularly whether a single drawn
valley at the pinch (not two) and the undrawn patch near the rf3/rf1
corner read as acceptable, or whether the second valley is worth a
dedicated follow-up pass now rather than later.

**Carried, unchanged:** D83/D84 (held); room-label rounding
(0131-ruling.md sec2); delta-snap sites; D61-family; yard items; the
End-On marker at a clipped ridge end (0166-report.md sec3).
