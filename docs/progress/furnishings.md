# Progress log — furnishings and their 3D forms

*Append one entry per task. Newest at the bottom. See [`README.md`](README.md)
for the log's rules; the short form is **append, never revise** — a later
correction is a later entry.*

**Opened 2026‑08‑13.** This is not a phase: it is the programme of work that
began when Patrick asked whether authoring furnishings *including their 3D
forms* belonged in the AI tool set, and the census that answered it found a
third of the catalog rendering as a box. Kept as its own file rather than in
`side-tasks.md` because it has a ruled order and several steps.

```
PRISM -- THE PLAN SYMBOL, EXTRUDED  2026-08-13  (the ruled first item)
         handoff: 0012 (read-back + ruling), 0013 (the receipt)
         files:   floorplanner/viewer/fp3d.py  tests/test_viewer_model.py
                  docs/evidence/prism_remeasure.py + prism-extrusion-look.png
                  docs/evidence/prism_outline_census.py (re-pointed)
         gate:    719 collected / 712 passed, OFF/ON/DEEP all reconciling
                  ruff=clean vacuous=0 end_assign=0 snapshot=current  GREEN

         THE RECEIPT, AND IT IS A RE-MEASUREMENT RATHER THAN A CLAIM --
         ruled that way before the work started, so it could not be
         replaced by an impression afterwards:
             falling back to a box   28  ->  1
             extruded from the plan symbol   0  ->  27
             the one left is glass_shower, the single symbol drawn
             entirely in strokes
         By form: vehicle 10 of 10, seat 6 of 6, bed 4 of 4, basin 1 of 1,
         enclosure 6 of 7. "A THIRD OF THE CATALOG RENDERS AS A BOX" IS
         FALSIFIED; it is now one item in ninety-five.

         MEASURED THROUGH build_model ITSELF. The model emits prism_kinds
         and box_fallback_kinds in its stats, so the receipt comes off the
         production path rather than from an instrument that predicts it.
         As LISTS, not totals: a count cannot be argued with or acted on,
         and the claim only stays checkable if the survivors are named. A
         test asserts the two lists PARTITION the fallback set, so an item
         cannot quietly vanish from both.

         PRISM IS THE FALLBACK, in place of the box. A form whose own
         generator is not written yet is now drawn from the item's plan
         symbol -- data that already exists for every item, at its true
         footprint -- rather than as a rectangle that is merely the right
         size. The box survives behind it for a symbol with nothing to
         extrude.

         THE Y FLIP IS THE PART THAT COULD HAVE SHIPPED WRONG. The editor's
         scene has y growing down and the viewer's world has it growing up,
         so local y is H/2 - sy, not sy - H/2. A sign error there renders
         every asymmetric item MIRRORED -- the same class of fault the
         deleted furniture table shipped for months, three kinds rotated 90
         degrees from transposed width and depth. Asserted on the mower,
         whose deck must land on the +y side, and the assertion reverses
         cleanly when the sign is flipped.

         UNDER-APPROXIMATION ON PURPOSE: a curve contributes its anchor
         points, so a rounded outline extrudes as its inscribed polygon and
         the solid is never LARGER than the symbol drawn. A test pins that
         across four kinds. A ring nested inside another is dropped, or it
         would extrude to the same height and z-fight the face it sits on.

         AND THE COUNT OVERSTATES THE WIN -- THE PICTURE SAYS WHERE.
         build_model extrudes whatever filled rings a symbol has; it does
         not judge body from accent. The read-back's NONE tier named three,
         and two of them now extrude:
             boat_trailer  PREDICTION BORNE OUT. Frame, rails and tongue
                           are all <line>; only the fenders, coupler and
                           lights are filled. Five disconnected slabs and
                           no trailer.
             bicycle       PREDICTION NOT BORNE OUT. Two wheels and a
                           saddle -- thin, but A BICYCLE IS THIN, and a
                           24x68 box says something much more wrong.
         NO THRESHOLD WAS ADDED TO CATCH boat_trailer, deliberately. It
         would have to be a coverage threshold, which is the exact
         instrument whose failure is already in the working agreement --
         one such line put lawnmower and snowblower on opposite sides while
         they are structurally identical. Reintroducing it to catch one
         item would rebuild a fault that has already cost a withdrawn
         number. Reported and left extruding; the decision is Patrick's.

         THE CENSUS NOW CALLS THE PRODUCTION PARSER. prism_outline_census
         had its own SVG reader while it was a prediction; it now calls
         fp3d.svg_outlines, so it cannot drift from what the viewer reads.
         It reproduces the same tiers (19 BODY / 6 PARTIAL / 3 NONE), which
         is the closest thing to a cross-check available.

         WHAT IS NOT CLAIMED: that a prism is the right SOLID (a bathtub is
         not a prism, whatever its outline -- prism is a better FALLBACK,
         not a model); that every extrusion has been seen (eight rendered
         and looked at, nineteen counted); that the meshes are watertight.

         NEXT, AND IT IS A DECISION RATHER THAN A TASK: the ruling was
         build prism, re-measure, THEN decide. This is the re-measurement,
         and it is the strongest case for not writing the four furniture
         generators -- seat, bed, basin and enclosure are 17 of 18 extruded
         from real outlines. What a dedicated generator would add is
         structure the plan symbol does not contain (a seat back, a tub's
         inner well), which is a different question from "is the footprint
         right" and is best answered by looking at the 3D view now that it
         shows real shapes. vehicle at 10 of 10 weakens its own case too --
         but "extruded" and "looks right" are different claims, and only
         two of those ten have been looked at.

         The authoring list is now TWO, not three: glass_shower (no fill at
         all) and boat_trailer (fills, but no body). bicycle comes off it.
         Still separate from the generators, per the ruling that a code
         task must not acquire an artwork dependency.

PRISM MERGED, AND THE FURNITURE HALF NARROWED  2026-08-14
         handoff: 0013 (receipt + ruling), 0014 (the furniture parse)
         merged:  PR #28 (33043ed), after Patrick's check:
             "I looked - prism ships, merge it"
         It went to main FIRST WITHOUT ITS CHECK (8724740), was backed
         out (72e49cb) and re-landed through the PR. Prism is AMBER --
         it changes the 3D view for 27 of 95 items -- and a strong
         receipt was allowed to stand in for a tier decision. A GREEN
         GATE AND A STRONG NUMBER ARE EVIDENCE ABOUT THE CODE; NEITHER
         IS EVIDENCE ABOUT THE TIER.

         THE VEHICLE HALF IS SETTLED BY EYE AND WAS NOT RE-MEASURED.
         Patrick, on prism-live code on a real plan: TRACTOR, LAWN MOWER
         AND SNOWBLOWER have visibly changed shape, while THE SOFA AND
         THE BED in the same view are still slabs. Vehicle gained real
         geometry; furniture gained nothing. Recorded as the receipt,
         naming the three items, on instruction.

         AND THE NUMBER THAT REPLACES 28 -> 1: THE OUTER OUTLINE IS A
         PLAIN RECTANGLE FOR 17 OF 18 furniture symbols, office_chair
         (a circle, 24 vertices) being the only exception. A 4-VERTEX
         PRISM IS A BOX. 28 -> 1 counted items that EXTRUDE; it could
         not tell "extrudes something" from "extrudes a rectangle", and
         that gap is exactly what Patrick saw.

         THE DECIDING QUESTION, ANSWERED PER ITEM: closed internal paths
         EXIST, but not where it matters most.
             beds        1-2 filled pillows each
             bathtub     the WELL, a filled rect inside the rim
             kitchen_sink two bowls
             13 of 18 items carry at least one filled region, 17 in all
             BUT sofa, armchair and loveseat draw the BACK AS ONE LINE,
             and the arms as lines. No region, nothing to give a height
             to -- and those are the three seats a room is fullest of.
             dining_chair and office_chair draw theirs as a real rect,
             which is why this is reported PER ITEM and not per form.

         COST OF THE CHEAP ANSWER, COUNTED NOT ESTIMATED: 17 filled
         regions to annotate in _gen_assets.py, where the artwork is
         already drawn, plus ONE LOOP in build_prism, which already
         returns a list of parts and already extrudes a ring between two
         heights. Not built -- the decision is Patrick's.

         ONE CORRECTION MADE BY READING RATHER THAN PARSING: the first
         cut reported dining_chair as having no internal closed paths.
         It has a back panel drawn as a closed rect, sitting BESIDE the
         seat rather than nested inside it, and the criterion only
         counted nested shapes. Caught by opening the four files. Third
         time on this feature that looking has overturned counting.
```
