# 0290 — report: PR #100 merged — dormer gable ends & shed fronts close in 3D (a wall under a dormer climbs into it)

**Landed:** PR #100 · 617182b · 2026-11-04 · AMBER · checked by Patrick on the 3D render (the front dormers' gable ends now close); landed as the foundation for the cross-level window work, his word "Land #100 now"

**Code, 2026‑11‑04.** The record ([`0197-ruling.md`](0197-ruling.md) §7).

## 1. WHAT LANDED

`main` merged **`617182b`**, one commit `00ed1fd` on `8c1610f`. Phase A of the
dormer-windows plan (a single-record, many-views model worked out with Patrick).

The gable ends of his front dormers did not render in 3D.
`_wall_under_roofs` caps a wall at the LOWEST roof over it (`owner_of`), and for
a wall under a dormer that lowest roof is the HOST it stands on. So the wall
stopped at the host surface (~108" at the front dormer face) and the dormer gable
up to the ridge (~246") was left open, while `_dormer_face` yielded the gable to
`_on_a_wall` expecting a climb that never came. (A naive "build the dormer face
anyway" covers a windowed house wall's opening and broke the pinned 0248
invariant -- found, measured, reverted.)

`fp3d.py` `_wall_under_roofs`: a wall piece whose centroid lies inside a
SAME-LEVEL dormer's territory now climbs to THAT dormer's surface
(`dormer_over`), closing the gable, instead of capping at the lower host. A
window in the wall stays a void -- no dormer face is generated, so the 0248
invariant (a windowed house wall's opening shows through) holds. Pieces not under
a dormer are unchanged.

Verified on `wiscaway2026-11-01R1.json`: the front dormer walls now rise to
~241" (dormer ridge less the cap) vs ~108". `tests/test_dormer_gable_3d.py`: the
wall climbs to close the gable, and a window in the climbing wall stays a void
(ray test); the pinned `test_roof_shed_form.py` stays green.

## 2. WHAT THIS IS THE FOUNDATION FOR

On his check the gables close but with the FIRST-floor wall, which hides the
SECOND-floor window that belongs in the gable (his `w102`/`w142`, `8048`, at
absolute 136–184", inside the gable band 108–246"; the first-floor window
`w12`/`w51`, `9648`, is a storey window at 36–84", below the gable). The dormer
is modelled on the first floor but its gable occupies the second-floor storey.

RULED with Patrick (next phase, not in this PR): the dormer's **`level` is the
floor it is drawn and edited on** (the storey whose wall forms its gable, so this
same-level climb brings that wall and its window), while its **geometry is
anchored to its HOST's level** -- the dormer builder finds its host by looking
DOWN a level when there is none on its own floor, and the 3D lifts the dormer by
the host's base so re-levelling the drawn floor does not move it. The record
stays single-source on the dormer.

## 3. FOR THE RECORD

His own plan files under `fixtures/incoming/` stay uncommitted, his to keep.
