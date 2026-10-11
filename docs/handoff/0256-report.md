# 0256 — report: his two reports on iteration 11's shed dormer — the End-On dialog refused it ("never meets the host roof") and OK did nothing, and its ridge grip shrank it on every move; a shed's ridge is its high edge, on the host; both fixed, folded into `window-sill-endon`'s one commit; AMBER

**Code, 2026‑10‑11.** No merge has happened since
[`0255`](0255-report.md). His report, with the stacked branch waiting:

> *"when I edit the shed dormer between the 2 center dormers I get this
> dialog box which prevents me from making any changes and the OK button
> doesnt work. This is iter-11.json. Whats going on?"*

The dialog in his picture reads *"This ridge height never meets the host
roof -- the dormer cannot stand. Lower the ridge (or the pitch) to
continue."*, and OK stays open.

## 0. WHAT WAS GOING ON

The End-On dialog's dormer rule is R5b's
([`0191`](0191-ruling.md) §1): a dormer's ridge runs from its face into
the host roof, and its back end is DERIVED as the point where the host's
plane rises to the ridge height (`meet_along`). Typed above anything the
host reaches, the ridge never meets it, the dormer cannot stand, and the
dialog refuses — `accept` stays open, `apply` returns False. Written for
a GABLE dormer, whose ridge climbs the host's slope.

A SHED dormer (0248 plan A) is built the other way round: its "ridge" is
its HIGH EDGE, lying on the host plane and running parallel to the
host's ridge; its face is at the low edge; both ridge ends are faces.
Along that edge the host's surface is constant and already AT the ridge
height — `meet_along`'s first test (the host at or above the height at
the origin) answers None at once, so the dialog refused every shed
dormer that was correctly placed, and would have accepted only one
floating above the roof. The house's `rf_shed` has its top edge exactly
on the main roof's surface (iteration 9's derivation), so it hit this
the moment the dialog opened.

## 1. THE FIX

* **The standing rule for a shed dormer:** it stands while the host's
  surface at BOTH ridge ends is at or above the typed ridge height,
  within half an inch — the edge on the roof, or buried under it, where
  the clip hides what is buried and the dormer's plane emerges lower
  down. It is refused when the edge would float above the host.
  `dormer_meet_in` returns the clearance (0 on the roof); the note says
  *"High edge on the host roof; both ends are faces."*, or how far under,
  or the refusal *"stands above the host roof along the high edge — the
  dormer would float"*. A gable dormer's rule is untouched.
* **Nothing derived:** `RoofItem._derive_back_end` returns at once for a
  shed — the sketched second end IS the second face, not a point to find.
  (Before, `meet_along`'s None left `p2` alone by accident, so loading
  worked and only the dialog broke.)
* **The ends:** on a shed dormer both end choices are locked at Gable
  with the tooltip "A shed dormer's ends are both faces"; switching the
  form in the dialog re-evaluates the note and the ends.
* **Test:** `tests/test_roof_shed_form.py` gains the house's host and
  shed dormer as items — the dialog stands it, applies, accepts, leaves
  `p2` where it was; two inches above the host it refuses with the float
  note; ten inches under it stands with the clearance said. Opened on the
  house's own `rf_shed` through the app's load path in a probe: stands,
  edits, applies, accepts, writes.

## 1b. HIS SECOND REPORT — the ridge grip shrank the dormer on every move

> *"when I edit the second floor and click and drag the mouse on the top
> control handle, every mouse move shrinks the vertical limits of the
> dormer"*

The ridge grip (R4c) slides a gable's ridge sideways between fixed
eaves: `d` from the cursor, the two spans rebalanced `[span_l - d,
span_r + d]`, clamped so neither drops under an inch — `d >= 1 - span_r`.
A shed's right span is 0, so the clamp forced `d >= 1` on EVERY move,
whichever way the cursor went: the ridge walked an inch toward the eave
and the span lost an inch per mouse move. Fixed: a shed's ridge is its
HIGH EDGE — the drag moves that edge to the cursor, the eave line stays,
the one span follows (never under an inch), the same cursor twice moves
nothing; on a shed DORMER the edge keeps to the host's surface where it
lands (the dialog's standing rule), refused where the host there is not
above the face. The same gesture's end grip on a shed dormer's second
end was dead (the derived-back-end branch, with nothing to rise along);
it now drags like any roof end, since that end is the second face.
`tests/test_roof_shed_form.py`: a plain shed and the house's dormer,
dragged, dragged again with the same cursor (no creep), dragged
up-slope (the height follows the host), its end lengthened.

## 2. WHERE IT IS

Folded into `window-sill-endon`'s ONE commit (amended to `95e34ed`, force-pushed),
still stacked on `roof-gable-climb-level` (PR #84), no PR. The checkout
is on it. His word on the stack stands as [`0255`](0255-report.md) §6
put it: land in turn, or fold.

## 3. THE RECEIPT

`--quick` passed; ruff clean; the full gate GREEN on the amended commit.

## 4. WHAT HAPPENS NEXT

His check of 0255's four and these two; his word on #84 and the stack. Then
0248's E and the hip run on his word. Behind them: the compose cost
([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0255`](0255-report.md).
