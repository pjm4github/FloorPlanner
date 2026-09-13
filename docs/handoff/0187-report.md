# 0187 — report: R5a — the clip trace on the roof, built; AMBER, stopped for his check

**Code, 2026‑09‑13, answering [`0186-ruling.md`](0186-ruling.md) §2.** The
ruling's order is R5a → R5b read-back → R5b build → R6 (§5), never two
open AMBER tranches at once; R5a is the one built here. Branch
`roofs-r5a-clip-trace` off `main` at `9b39c07`, PR #61 open, gate
GREEN, **stopped for Patrick's check** — his own sentence from §2:
*"wiscaway with roofs on, the dashed trace hugging where the R3b wall
dashes already are."* Nothing of §3 (the dormer read-back) or §4 (R6)
has been started.

## 1. WHAT'S BUILT

**The trace is the level set of the roof surface at ceiling height**
(`floorplanner/roofs.py`, `roof_clip_trace`). Within a roof's footprint
the surface is `ridge_h - slope * |perp|` on each side, and past a hip
end the LOWER of that and the hip plane — the same surface R3b's
`_clip_spans_against_one_roof` reads along a wall. Its level set at a
ceiling height `h` is straight lines in the roof's own (along, perp)
frame: one per side at `perp = ±(ridge_h - h) / slope`, running the
footprint's along-extent but stopping where a hip plane takes over, and
per hip end a cross segment at `along = -(ridge_h - h) / slope_h`
between the two side lines — a closed loop for a hip roof, two open
lines for a gable one. Exact, never sampled. A side whose line would lie
beyond its own eaves never clips and draws nothing.

**Which ceiling: R3b's rule, at every point.** A roof can cover rooms of
different heights, and `roof_clip_spans` reads each wall against the
LOWER of the rooms it borders, the default where no room is there. The
trace does the same: for each distinct ceiling among the floor's rooms
(plus the default), the level set at that height is cut wherever it
crosses a room's outline — dilated by half the floor's thickest wall, so
a point ON a wall's centreline still counts as the room's, since a room
outline stops at the wall's interior face — and a piece is kept only
where that height is the governing ceiling at its midpoint (the LOWEST
among the rooms holding the point, or the default). The cuts are exact:
every place the verdict can flip is the line's intersection with a
dilated outline (an offset edge line or a vertex's circle), and the
verdict is constant between cuts. Same idiom as the wall spans' own
roots-and-midpoints.

**Drawn like the roof's other plan lines.** `RoofItem._drawn_trace`
cuts the locus to R4d's visible region while the roof is clipped
(selected = unclipped, as everything else), and a joined end carries
the locus on into its extension, since the surface continues there.
`RoofItem.paint` draws it dashed in **the wall dash's own ink** — that
colour is now one constant, `ROOF_CLIP_INK` in `config.py`, read by
`walls.py` and `roofs.py` both, because it is one fact drawn from two
sides and the trace has to visibly meet the dashes it ends. Ghosted on a
non-active floor like the wall dash. Computed at paint time, like the
wall dash (rooms change without the roof hearing about it); it is a
handful of segments against a handful of outlines, not the junction-clip
work CLAUDE.md keeps out of `paint()`.

**Nothing stored, no schema change, no new gesture or setting.** The
roof layer's own visibility governs it (a hidden roof draws nothing).

## 2. THE CHECK — receipts

`tests/test_roof_clip_trace.py`, **18 tests**, on the same 300×200
fixture `test_roof_clip.py` uses (eaves 80″, ridge 132″, span 100″, a
96″ room), so the two files' numbers read against each other. **The hug
is asserted against the production `roof_clip_spans`, not restated**: a
wall crossing the roof has its dash ends (its own spans' interior
boundaries) exactly at the y's where the trace crosses it — at the ridge
end and mid-roof; an eaves wall dashed end to end is never crossed; a
hip end's cross segment lands on the end of the dash along a wall under
the hip; over an interior wall between a 96″ and a 108″ room the wall
dashes at the 96″ threshold and it is the 96″ trace lines that reach its
centreline, the 108″ lines starting past it; no room at all and the
default ceiling governs both readings alike; a room on another floor
changes nothing. The closed form once (two lines at
`(132 − 96) / 0.52 = 69.23″` off the ridge); the hip loop's exact three
segments; no trace when the eaves clear the ceiling (positive control
first); under R4d the drawn trace is strictly inside the visible region
and shorter than the locus, **the main's drawn trace ends exactly at the
wing's trace lines** — where both surfaces are at ceiling height the seam
passes through the crossing of the two traces, a structural fact the
build did not aim at and the test now pins — select → whole locus →
deselect → cut again; a joined end's locus runs past its own end edge and
what is drawn stops on the seam; the paint (ink on both lines, none in
the clear band, none when nothing clips); a stale roof reference gets an
honest empty answer.

Full suite **1298 passed**, 7 deselected (`perf` lane), `ruff` clean,
gate GREEN — the branch's own gate run.

**The picture:** `docs/evidence/roof-clip-trace-r5a.png`, from
`docs/evidence/roof_clip_trace_receipt.py` (offscreen 2D, reproducible).
No wiscaway-with-roofs file exists in the repo (the R4a receipt said the
same), so it is a synthetic house with wiscaway's two ceiling values, 96″
and 120″, side by side under one gable roof with a hip west end, eaves
80″ / ridge 150″: the orange dashes on every wall end where the orange
trace crosses that wall; the trace steps outward where the 120″ room
begins (a taller ceiling is hit lower down the slope); the hip cross
segment closes the loop 111″ past the ridge end. Room labels render as
boxes offscreen (no font); the geometry is the point.

## 3. NAMED LIMITS — none of them blocks the check

* **A ridge below the ceiling has no locus.** The whole roof clips (R3b
  dashes every wall end to end — asserted in the same test); the surface
  never reaches ceiling height, so there is no line. A roof that low is a
  modelling error the wall dashes already shout about.
* **The default ceiling stands in over ground with no room**, exactly as
  R3b's fallback does for a wall with no room beside it — so a roof over
  an unenclosed porch traces at 96″. The two readings agree; whether
  either should is his call, not a defect.
* **The margin is one number per floor** (half the thickest wall, plus
  ½″), not per wall. On a floor mixing 6″ exterior and 4½″ interior walls
  the lower room's line reaches ¾″ past an interior wall's centreline.
  Invisible at any working zoom; named so nobody measures it and wonders.
* **A clipped roof's unclipped locus is not for drawing.** The joined-end
  extension is R4d's raw candidacy reach (hundreds of inches); only the
  region-cut `_drawn_trace` is ever painted. Recorded in the snapshot's
  roof traps.

## 4. `fixtures/incoming/`, with ages

`README.md` (2026‑08‑23), `w7offgrid.fpm` and `w7offsetFloorplan.json`
(both 2026‑08‑21 by git, 23 days). **Both are byte-identical duplicates of
the promoted `fixtures/w7offgrid.fpm` / `fixtures/w7offsetFloorplan.json`**
(exit 1 under [`0070`](0070-ruling.md), D80 — `fixtures/README.md` names
them load-bearing). They have sat across every handoff since, unlisted
by `0182`–`0185`, which is the README's own finding: evidence the record
stopped mentioning. Exit 2 (delete as a duplicate, naming its cover) is
one commit if he says so; not touched here, since nothing in this
tranche asked for it.

## 5. WHAT HAPPENS NEXT

His check. On his word, PR #61 merges (branch deleted in the merge
step). Then [`0186`](0186-ruling.md) §3: the R5b dormer read-back — a
report, no code — covering the schema shape, the opening's interaction
with `compute_roof_clips`, the sketch gesture and the v1 dormer; RED
until he rules on it. R6's two waits (his multifloor fixture, the
plan-view display rule) are his.

**Carried:** unchanged from [`0185`](0185-report.md) §2–3 and
[`0186`](0186-ruling.md) §5.
