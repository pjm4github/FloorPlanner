# 0364 — report: 0360 stage 3 (dormer render rules) + knob grid-snap merged to main

**Code (Claude Opus 4.8), 2026-11-22.** Records [`0360`](0360-ruling.md) stage 3
(the render-rules check) landing on Patrick's word, together with an orthogonal
dormer UI change. Follows the stage-2 table fill (`ee683d2`) and the stage-1
evidence ([`0362`](0362-report.md)). Tier: **AMBER** — merged on his word while
one observation is still open ([`D89`](../defects/0089-the-0360-roof-skirt-does-not-render-in-the-app.md)
below); full gate GREEN (2611) at the branch tip `e62734b`.

**No board `**Landed:**` line:** Patrick merged **PR #110** himself on GitHub
(merge commit `501f5600`), and `main` carried no landing lines for the earlier
button-/ff-merged PRs #105–#109 either, so adding one only for #110 would break
the status board's contiguity invariant (`test_every_merged_pr…`). This report
is the record of the merge; boarding #105–#110 is a deferred cleanup.

## What landed

`dormer-render-rules` (five commits), merged into `main` via PR #110 (GitHub
merge commit `501f5600`):

1. **`3d9d125`** — the `skirt_mode` switch (state / normalize / dialog / schema),
   a `skirt_available` helper, and the cantilever boundary moved from the **wall
   (D)** to the **fascia (A)** in `classify_face`/`face_vs_host_eave` via a new
   `host_overhang_in` (Patrick's "Eave A — physically correct").
2. **`6b68879`** — the boundary goes live: `items.py` `_host_plane` threads the
   host eave-side overhang into `param_context`; `dormer.skirt_unavailable`
   finding; `skirt_mode` into the 3D roof record.
3. **`f175a93`** — the **S° roof-skirt mesh** in `fp3d`: a cantilever whose face
   stands past the host fascia (A < C) with the host eave below the dormer floor
   gets a sloped roof surface ramping from the fascia up to the attic floor
   (84 → 108 on W09), **replacing** the flat §8.4 cantilever floor; the dormer
   face/cheeks that hang into the overhang sit on that ramp (`skirt_z`). Fires on
   the A < C rows W09/W31 only; `skirt_mode` off keeps the flat floor. Regression
   `test_a_cantilever_roof_skirt_replaces_the_flat_floor`.
4. **`a80b37b`** — the 26 evidence cases re-rendered (`make_cases.py --all`, each
   reproducing to the inch); W09/W31 carry the skirt; every `.json` carries
   `skirt_mode`. Also fixed a latent evidence bug: `readback` now reads the face
   class from `DORMER.evaluate`'s derived `face_type` (threading
   `host_overhang_in` + `wall_below` like the app), so `INDEX.md`'s `Face (app)`
   matches the dialog — 11 rows corrected to the fascia reading (A > C → setback;
   A = C no wall → standard; A = C = D flush → wall); only the true A < C
   cantilevers W09/W31/W53/W68 keep `dormer.cantilever`.
5. **`e62734b`** — the dormer control knobs snap to the on-centre grid
   (`SETTINGS["wall_snap_in"]`, 6") unless **Shift** is held; each knob rounds
   its own axis dimension (anchor A snaps along the host fall line), regression
   `test_a_knob_snaps_its_dimension_to_the_grid_unless_shift`. Orthogonal to the
   render rules.

## Open: the roof-skirt does not render in the app (D89)

Patrick: *"The roof-skirt doesnt seem to work yet."* The skirt mesh builds
headless (W09/W31 return `roofs` × 2, no `dormer_floor`; ramp 84 → 108) but he
does not see it in the live app. Filed OPEN as
[`D89`](../defects/0089-the-0360-roof-skirt-does-not-render-in-the-app.md) so the
work merges without losing the observation; the break is between the built mesh
and the live viewer and is not yet diagnosed.

## Verification

Full gate GREEN (2611) at `e62734b`. Evidence PNGs under
`docs/evidence/0360-dormer-orderings/`.
