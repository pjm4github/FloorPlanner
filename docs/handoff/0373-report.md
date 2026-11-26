# 0373 — report on 0372 item A: the hypothesized cause is disproven. The real cause, the fix direction, and why I paused before touching shared roof code. AMBER.

2026-11-26, Code session. Against `main` at `b6e649c` (the fp3d code is
`ab8aad8`'s; my 0372 filing was docs-only). Measured headless on the frozen
readback file `...\wiscaway-roof-build\readback-BR3-dormer-rake12.json` (read,
not committed), the four fin/post boxes of 0372 §3. **Item A is not fixed — it
is diagnosed.** I stopped before the fix because the cause is not the one 0370
§2 hypothesized and the real fix is in shared roof-territory code that the O4
invariance guards; per 0372 §5 ("not mechanical") I want your read on the
direction first.

## 1. The hypothesis, disproven

0370 §2 read the cause as `_wall_under_roofs`'s `dormer_over` override —
"a `to_top` piece inside a dormer's territory takes `dormer_over(pc)` ...
nothing stops it at a roof drawn between the wall and the dormer" — and flagged
it "that is my reading; measure it before you rely on it." I measured. Three
changes to exactly that machinery, each rebuilt and the four boxes re-measured:

| Change | `front post S / N`, `cheek fin S / N` (in) |
|---|---|
| baseline (`ab8aad8`) | 202.4 / 202.0 / 200.5 / 200.2 |
| gate the `dormer_over` override on `owner_of` returning a dormer | 202.4 / 202.0 / 200.5 / 200.2 — **no change** |
| + require the climb be PERPENDICULAR to the dormer ridge (`climb = to_top and _climbs(geom)`, dropping the unconditional `dormer or`) | **no change** |
| suppress the generated dormer cheeks/face (`_dormer_cheeks` / `_dormer_face`) entirely | **no change** |

None of the three moved the fins. The `dormer_over` climb is not what builds
them, and they are not generated cheek/face material either.

## 2. The real cause (measured)

The fins are ORDINARY house-wall pieces (the L1 exterior walls `w76`/`w77` at
x≈797 and `w92`/`w94` at x≈947.5, and the x-running front walls), capped at the
**dormer's own surface (~202)** through the NON-climb path of
`_wall_under_roofs`. Behind the dormer face, at the cheek line, the **dormer is
the only roof whose territory contains the piece**, so `owner_of` caps the wall
there. The host (`rf2`, ~176) and the skirt (`rf4`, ~122–144) that are
physically DRAWN beneath — 0371 §2's own vertical probe finds `rf2` at 174–178
under the eave overhang — are **not re-added into the wall-capping territory**
at that band. Just OUTSIDE it, where `_hidden_overhang_pieces` does re-add the
lower roof, the same walls correctly cap at ~113–135.

So "the first roof drawn over it" (0370 §3) and the territory the wall is capped
against have diverged: the roof is drawn (meshed) but is absent from the
territory `_wall_under_roofs` sees. The lever is `_hidden_overhang_pieces`
(0242/0240), not `dormer_over`.

Two incidental confirmations, both narrowing the scope in our favour:

- **The frozen file is a genuine code case, not the 0371 §5 settings cause.**
  `f135`'s half-span is 75.25 and at pos x=872 its cheeks fall at x≈796.75 /
  947.25 — essentially ON the walls (797.07 / 947.5), not 20.75 in outside them.
  The half-width=96 mismatch of 0371 §5 (advisory E) is not in play here.
- **Furnishing dormers build as roofs regardless of the `furnishings` flag**
  (the "5 dormer furnishing(s) built as roofs" note appears either way), so the
  fins are furnishing-independent — they are house walls, as you measured.

## 3. The fix direction, and the O4 risk

The fix is to make the wall-capping territory reflect what is actually drawn:
in `_hidden_overhang_pieces`, re-add the host (and any skirt) under a dormer's
eave/face overhang up to the dormer's ACTUAL cheek walls, so `owner_of` caps the
wall at that lower roof (~176) instead of the dormer (~202). "Drawn" would then
be computed as it is everywhere else — the piece centroid lies in some roof's
territory cells (visible region + hidden-overhang strips) — with the strips
extended to close this gap.

Why I paused: `_hidden_overhang_pieces` is the shared roof-territory code, and
0370 O4 requires every mesh of the 26 `0360-dormer-orderings` cases and the
`0367-pyramid-roof` cases to stay byte-identical. A change there is materially
riskier than the one-line `dormer_over` edit the O-orders assumed, and there is
a real behavioural question it exposes: a house wall straddling the cheek line
is partly over the drawn host (outside) and partly over the cut-away dormer
interior (inside). Where exactly it should terminate — at the host, or rising to
the dormer eave to close the side — is the kind of call 0372 §6 reserves for
your eye.

## 4. What I need

A short ruling on the direction before I do the territory surgery:

1. Confirm the target is "cap the cheek/eave wall at the lower roof drawn
   beneath (host/skirt), not the dormer surface," including for the wall piece
   that straddles the cheek line; or state where you want that straddling piece
   to stop.
2. Confirm `_hidden_overhang_pieces` is an acceptable place for the fix given
   O4 — or name a safer seam if you see one.

The 0370 O1/O2 and 0371 O1 fixtures still stand; I'll build them against the
corrected cause once the direction is set. Item B (the §8.4 floor over open air)
is untouched and not blocked by this. The branch `dormer-climb-floor-0372`
carries no code yet — the tree is clean.
