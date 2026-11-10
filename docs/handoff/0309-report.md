# 0309 — report: either gable end in the Elevation tab — the End-On dialog, on a branch

**Code, 2026‑11‑10.** The record ([`0197-ruling.md`](0197-ruling.md) §7). A
follow-on to his standing item **#3** (the dimensioned gable-end window
elevation — [`0294`](0294-ruling.md) §4, built and merged at
[`0308`](0308-report.md)), on his word 2026‑11‑10: *"the one thing that is still
missing … is the elevation for the ordinary gable ends of the roof … show either
end of the roof if there are 2 gable ends (or only one end if the roof doesn't
have 2 gable ends) … use the blue dot to indicate which end is being shown."*
Built on branch `gable-end-either`, cut from `main` (`8fcfc6d`, the #3 merge);
AMBER, **awaiting his check**. (No **Landed:** line — AMBER, and a two-parent
merge's landing commit is not on `main`'s first-parent chain anyway.)

## 1. HIS ORDER (2026‑11‑10)

#3 as merged drew ONE gable end — the one whose wall carries windows, else the
marker end — picked automatically. He asked for **either** end on demand: both
when the roof has two live gable ends, the one when it has one; and for the
**blue dot** (the roof's end marker) to indicate which end the tab is showing.
He chose (2026‑11‑10): a **toggle in the Elevation tab, and the dot follows**.

## 2. WHAT IT DOES

`RoofItem.gable_elevation(end=None)` now takes an **end index** (0 = `p1`,
1 = `p2`) and its returned dict carries `"end"`. An explicit `end` draws that
gable end when it is a live gable (`roof.gable[end]`); a hip or non-gabled `end`
falls back to a drawable one; `end=None` keeps the prior auto-pick (so #3's
tests and callers are unchanged). The drawing stays in the roof's **ridge frame**
— the apex leans toward `span_in[1]` for both ends, not mirrored per side — so
the established `apex_in` contract (and its test) holds; `end` selects only
*which gable-end wall's* windows are located.

`RoofItem._gable_end_wall(gable, axis, end=None)` now returns `(wall, end)`: with
`end` given and gabled it searches **only** that end; otherwise it keeps the
window-carrying-then-marker preference and reports whichever end it resolved to
(so the triangle still draws when no wall is found).

`RoofEndOnDialog`'s Elevation tab grows a **"Gable end"** selector listing the
roof's LIVE gable ends only — "Marker end (blue dot)" and "Other end"; disabled
when there is one, absent for a dormer (one face). Picking an end redraws it and
moves the roof's blue end-marker to that ridge end as a **live indicator**. The
move is transient: the dialog is modal, and on close the dot is restored to the
roof's real `marker_end` (`_restore_marker_dot`), so merely *looking* at the far
end never rewrites which end the roof calls its marker. The tab opens on the
marker end (or, if that end is a hip, on a drawable gable end, moving the dot to
it).

## 3. RECEIPTS (instrument `docs/evidence/0309-gable-end-either/render.py`)

A built two-gable-end roof with a DIFFERENT window wall at each end renders
`gable_elevation(end=0)` and `(end=1)` to separate PNGs: end 0 draws its p1-end
window (36×48) and NOT p2's, end 1 draws its p2-end window (30×72) — each end
locates only its own wall. On `wiscawayL2-fix.json` a plain gable roof (6 found,
5 with two live gable ends) renders genuinely different window sets per end
(two 30×48 at one end; a 36×80 and two 36×48 at the other), confirming the
gable-end wall is found per end. Width and ridge are shared (same roof, ridge
frame). Headless text renders as tofu offscreen (no font glyphs); `fmt_in` is
ASCII and draws on the real display.

## 4. TESTS

`tests/test_gable_elevation_ends.py` (7): each end draws its own wall's windows
(the other end bare but a valid triangle); each end finds the wall at that end; a
hip `end` falls back to a drawable gable; `_gable_end_wall(..., end=)` returns the
requested end index; the Elevation tab's selector switches ends and the blue dot
follows (and is restored, `marker_end` unchanged); one live gable end disables the
selector; a dormer has none. The #3 suite (`test_gable_elevation.py`, 7) is
untouched and green. Gate: full mode, GREEN.

## 5. NEXT

AMBER — his to check (run the app, open the End-On dialog on a two-gable-end
roof, flip the "Gable end" selector, watch the blue dot). More elevation
parameters remain his to order ([`0294`](0294-ruling.md) §4): live spinbox
tracking, head-below-ridge, corner offsets, pitch. His `tools/schema_viewer.py`
graph cleanup (tidy tree, collapse, remembered layout) is built and held
uncommitted in the working tree on his word, for him to run first. 0248's items
8–9 named, not ordered.
