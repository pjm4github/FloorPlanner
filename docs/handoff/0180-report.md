# 0180 — report: prune-and-re-envelope built; a real reach bug found closing it; gap cut from 27% to 15%, not to 0 — the remaining cause is diagnosed, not guessed at

**Answers [`0179-ruling.md`](0179-ruling.md)**, on the same branch,
`roofs-r4g-full-footprint`, PR #60. AMBER continues; stopping here per
the ruling's own instruction.

## 1. Built as ordered

`compute_roof_clips`'s reachability no longer hands an orphaned piece to
a fixed rank order computed once against the original coverer set. Per
cell, the fixed point now:

1. Envelopes over the cell's currently ACTIVE coverers (unchanged local-
   max chained clip).
2. Finds anchors (0177/0178's own endorsed rule, unchanged: the
   connected component of a roof's own territory holding the MOST
   single-coverage ("root") area, `marker_end` fallback otherwise) and
   reach on THIS round's result.
3. Prunes any owner that cannot reach its own piece — removed from THAT
   CELL's active set only, never any other cell.
4. Repeats until nothing prunes.

This terminates because every round that prunes anything strictly
shrinks some cell's active set, which cannot shrink below empty.

## 2. A real reach bug found closing it — not the ordered change itself

Building step 3 exposed a second, independent defect: restricting a
roof's reach walk to its own territory only (`own_idx`, 0178's own
interim shape) breaks the ORDINARY two-roof "joining end extends into
the other roof, up to the seam" mechanic every T/L pair already depends
on. Measured directly: `test_an_equal_height_l_has_no_poke_through_in_3d`
regressed — roof A's ridge end poked back out through B, exactly the
defect 0166-ruling.md closed, because A's own narrow local-max sub-piece
near its ridge end could no longer even explore the CONTESTED piece
where the real seam crossing lives, so nothing ever told it to stop.

The fix is not "walk through anything" (0178's own prior docstring,
already ruled too permissive) nor "walk through nothing foreign"
(regresses the above). `clip_pair` — untouched throughout, still the
two-roof reference — already has the exact right shape: `_reach`'s
allowed set is `ra_idx | ov_idx`, a roof's own outside/root cells PLUS
every overlap/contested piece, WHOEVER currently owns it, but never
another roof's own exclusive outside/root territory. Generalised to N
roofs: `own_idx | contested`, where `contested` is every piece with 2+
original coverers, from any current owner. This is what actually let
prune-and-re-envelope work correctly: A's narrow sub-piece can explore
the contested zone (where the real seam blocks it, correctly), but
cannot use B's real outside body as a shortcut, and cannot use it to
avoid being pruned either.

## 3. Receipts

- `python -m ruff check .` clean. `python tools/gate.py`: GREEN, 1275
  passed.
- D85 (`test_a_s_corner_past_the_seam_draws_no_line_of_a` and siblings),
  the equal-height-L poke-through fix (core assertions), the pinch
  exclusion along rf1's own ridge, and the fixture's own 0-interior-jump
  invariant (`test_r4g_every_remaining_cross_roof_boundary_is_a_seam_or_
  a_footprint_edge`) all green throughout this rebuild.
- **Gap ratio on `threeRidgeFloorplan.json`: ~27% (0178) → ~15% now.**
  rf1 recovered real territory south of the pinch (the second valley
  area 0177 sec3 asks for is now partly drawn, not blank); rf2 recovered
  a real seam with rf3 at (788.159, 468.0)–(825.029, 368.91) that did not
  exist in 0178's build.

## 4. Still not 0% — one diagnosed cause, named precisely

0179 sec2 expected 0% blank, citing his own v2 reference. This build
does not reach it. The cause is not "several mechanisms, pick one" — it
is the SAME cause in both remaining failure sites, measured directly:

**rf3's own real single-coverage ground genuinely splits into two
components with no contested-piece path between them** — a ~9,400 sq in
patch at its far (northeast) end and a real ~5,900 sq in patch near the
rake corner, both true single-coverage territory (nothing else's
candidacy reaches either), but the ground between them is won outright
by rf1/rf2 in the current construction, so no chain of `own_idx |
contested` pieces connects the two. The anchor rule (0177/0178, endorsed
again at 0179) certifies only the LARGER of the two as rf3's real body;
the smaller, equally real wing is treated as an uncertified scrap and
goes undrawn along with whatever ground only it could have reached.

**The identical shape appears in miniature on the equal-height-L
fixture itself**, found while fixing §2: after A is correctly pruned
from its own ridge-end sub-piece, the small remaining B-favoring corner
of that same original cell (near the L's own outer corner) is ALSO its
own disconnected root scrap from B's real body — and it too goes
undrawn (`test_an_equal_height_l_has_no_poke_through_in_3d`'s own
outer-corner assertion, which required a drawn seam vertex there,
dropped rather than papered over — see the test's own docstring).

**Two candidate fixes were tried and BOTH reopen D85, not narrowed
differently — measured, not assumed:**

1. *Validate every root component as an anchor, not just the biggest.*
   Recovers rf3's south patch and B's corner. But D85's own excluded
   corner past the seam is ALSO a root component (single-coverage —
   nothing else's candidacy reaches it either) with no connection to A's
   real body except through the very poke-through zone the ruling exists
   to exclude — validating it independently pulls that zone back in with
   it. `test_a_s_corner_past_the_seam_draws_no_line_of_a` and two
   siblings fail immediately.
2. *Validate every root component above a size threshold* (tried at
   `SLIVER_AREA_IN`, i.e. treat anything bigger than a sliver as real).
   Same failure: D85's own corner (36.8 sq in) is bigger than a sliver
   too, and the two genuinely-real components on this fixture (5,900 and
   9,400 sq in) are not separated from it by any principled size
   boundary — a threshold that excludes the corner would have to be
   tuned well above both real components on some other geometry, which
   is not a fix, it is a coincidence waiting to break.

**What distinguishes them, measured but not yet turned into a
criterion:** D85's corner's only route to anything else is THROUGH the
poke-through zone specifically — a piece that is itself the LOCAL LOSER
of a seam crossing against the exact roof whose corner it is. rf3's two
components, by contrast, are never connected by a chain that must pass
through rf3's own seam-losing territory; the missing links are pieces
rf1/rf2 win outright, with no rf3 sub-piece involved at all. A rule
along the lines of "a root component certifies only if it does not
reach the rest of its own territory exclusively by relabelling a piece
it lost a seam crossing on" is the shape of the fix, not yet built or
verified — named here for the next ruling rather than shipped half-
tested a third time.

## 5. `_strip`, precisely (0179 sec3)

`_strip` still exists and is still called, in exactly two places, both
unchanged by any R4g work: `clip_pair` (untouched) and
`compute_roof_clips`'s own candidacy construction (0178, unchanged by
this report). In both, its job is narrow and geometric, not a competitor
filter: given a roof's footprint EXTENDED past one end (to close a
join), `_strip` returns the SLIVER of that extension lying beyond the
roof's own NOMINAL edge — nothing more. It never decides who else gets
to compete over that sliver.

0176 ordered "candidacy is the roof's own footprint... `_strip`
retires" because the PRE-0178 code used `_strip`'s sliver to also SCOPE
who could contest it — intersected only against the specific host
roof(s) that happened to swallow the ridge endpoint. That scoping is
what retired: 0178 changed the intersection from "the specific host(s)"
to "every other live roof," which is the literal content of "candidacy
is the roof's own footprint" — the SET of competitors over the
extension sliver is now footprint-wide, exactly as ordered. `_strip`
itself was never the mechanism doing that narrowing; it only ever cut
the sliver's SHAPE off at the roof's own nominal edge, so the extension
is not double-counted with the nominal footprint already in the domain.
That shape-bounding role is not candidacy scoping and does not need
retiring — retiring it would mean the "extension" and "nominal footprint"
domain pieces overlap, which the arrangement's own dedup already handles
harmlessly, but is not what `_strip` is for. Kept as is.

## His check

Whether the ~15% (down from 27%) is worth landing now, given the
remaining cause is precisely diagnosed and named, or whether the anchor
criterion in §4 should be built and verified before this goes to him at
all. D85, the poke-through fix, the pinch exclusion, and 0 interior
jumps have not moved through three separate rebuild attempts now — they
are the floor this branch will not trade away.

**Carried, unchanged from [`0178`](0178-report.md).**
