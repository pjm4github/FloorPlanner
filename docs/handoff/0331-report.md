# 0331 — report: the ROOMS UNDER A DORMER render right from inside — the host roof no longer shows through the dormer's gable ceiling; and the 0328 §5 record-gap answered

**Code, 2026-11-14.** Patrick, looking into the left-front dormer from inside the
room with the 3D camera (0326): brown diagonal streaks and a ceiling sloping the
wrong way, where the dormer's gable ceiling, flat ceiling and knee wall should
read. He asked me to fix the mechanism. **He has since checked it: "The dormers
look very good now."** AMBER cleared.

## 1. THE MECHANISM

`fp3d._ceiling_pieces` clamped each room ceiling to the LESSER of the ceiling
line and the underside of EVERY roof over it — including the HOST roof. But a
dormer is a HOLE in the host roof: inside the dormer footprint the host is cut
away. Toward the gable the host slope drops well below the dormer roof, so the
`min()` dragged the ceiling DOWN to a roof that is not there (measured on the
left-front dormer's centreline: 247→135 in, following the host slope), and the
dormer's own roof underside (the brown `roofs` mesh, ~246) was left exposed above
the wrong ceiling. That is the brown streaks and the mis-sloped ceiling.

## 2. THE FIX

Inside a dormer's footprint the host roof no longer clamps the ceiling — only
the dormer roof does. `_ceiling_pieces` now takes the set of dormer roofs
(`dormer_lf_ids`, computed in `build_model` from each roof's `host`), splits
ceiling pieces along every dormer footprint, and skips any non-dormer (host)
roof at points inside a dormer. It is the INTERIOR DUAL of
`_hidden_overhang_pieces`' eave cut (0320, the exterior fix).

## 3. VERIFIED (geometry; the Qt Quick view needs a real GPU, D77 — offscreen is blank)

- Centreline: the dormer ceiling now holds at the dormer ridge (~242) instead of
  diving to 135.
- Across the gable: a clean gable — the ceiling rises from the cheeks (~167) to
  the ridge peak (~240) and back.
- Brown exposure: 0 of 513 sample columns in the left-front dormer; the other two
  dormers (back, right-front) also clean. The only roof-with-no-ceiling columns
  sit exactly on the cheek-wall line, hidden by the vertical cheek wall.
- Tests: the viewer/roof/dormer suites pass + a new regression,
  `tests/test_viewer_ceiling.py::test_a_dormer_ceiling_follows_the_dormer_not_the_host_it_replaces`
  (it compares the dormer-aware clamp against the old `min` and asserts the
  ceiling rides the dormer, not the host).

Files: `floorplanner/viewer/fp3d.py` (`_ceiling_pieces` + the `build_model`
ceiling call site only — NOT the furnishing regions), `tests/test_viewer_ceiling.py`.

## 4. THE 0328 §5 RECORD-GAP — ANSWERED

0328 §5 asked what "after the double-click fix" meant in the furnishings merge
message (`6d24a4f`), since no furnishing code changed between the gated branch
and the merge. It was NOT a code change. It refers to PATRICK'S OWN CHECK: a
stair saved before 0323 has a `state` with no `type` and renders as the legacy
box; a stair becomes parametric only when you DOUBLE-CLICK it and click OK (or
drag a fresh one from the palette), which writes a `type`. Patrick's plan had a
legacy stair; he double-clicked it to OK, and it then rendered as the parametric
stair (420-triangle L-stair, not a box). That is the "double-click fix" the merge
message names — a usage step he performed to confirm the stairs, not an edit to
the code.

## 5. OWED

- **Code:** this report; the fix is on `main` with the mailbox docs. The
  furnishings-lane gate is [`0332`](handoff/0332-report.md).
- **Reviewer:** nothing on this.
