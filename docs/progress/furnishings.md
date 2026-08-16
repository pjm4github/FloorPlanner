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

REGION EXTRUSION -- ONE GENERATOR, NOT FOUR  2026-08-14  (AMBER, at a PR)
         handoff: 0014 (report + ruling)
         branch:  region-extrusion
         files:   floorplanner/viewer/fp3d.py  _gen_assets.py
                  assets/furnishings/*.svg (13 regenerated)
                  tests/test_viewer_model.py
                  docs/evidence/seat-check.png, seat-plan-symbols.png,
                  prism-check-regions.png
         Patrick's check is ONE QUESTION: does a sofa read as a sofa.

         WHAT A REGION IS: a closed shape in the plan symbol carrying a
         data-h -- its TOP HEIGHT, in inches above the ITEM'S BASE, the
         same datum as the catalog's height_in. Three rules, and they are
         the whole generator:
             h > body   a raised region: extruded FROM the body's top
                        (a pillow, a bench, a chair back on its seat)
             h < body   a WELL: the body's top cap is opened for it and
                        the region gets walls and a floor (a tub's
                        inside, a sink bowl)
             not nested a column of its own from the floor
         An unannotated nested shape is still DROPPED -- it would z-fight
         the face it sits on, which is why prism dropped it before.

         THE BODY MAY STATE ITS OWN HEIGHT, and that is what fixed the
         seats. A sofa's catalog height_in is 32 -- the BACK -- so a body
         using it extruded the whole footprint to back height and read as
         a slab. height_in stays the item's OVERALL height, which the box
         fallback needs; the body now says how far IT rises (17").

         THE ANNOTATION CARRIES A HEIGHT AND NOTHING ELSE. The artwork
         says WHERE a region is and never WHAT it is; a parser cannot
         tell a pillow from a drain. An ordinal rule would break silently
         when artwork is re-ordered, and a geometric heuristic would
         INVENT A NUMBER THE DOCUMENT DOES NOT CONTAIN -- the same
         objection that already refused --stack for the viewer, quoted in
         the ruling so the repetition is visible. A test walks every SVG
         and fails on any data- attribute that is not data-h, or any
         value that is not one number.

         THE THREE SEATS WERE AN ARTWORK FIX, NOT A LIMIT. dining_chair
         and office_chair draw their backs as closed rects IN THE SAME
         FORM, so sofa, armchair and loveseat were three symbols drawn
         inconsistently with their neighbours. seat() now draws the back
         and arms as closed regions. THE TELL THAT IT IS THE RIGHT FIX:
         it improves the PLAN symbol on its own terms -- a sofa back has
         thickness and a line says it does not -- and the 3D follows.
         Checked before shipping: evidence/seat-plan-symbols.png.

         THE COSTING SAID "ONE LOOP" AND THE WELL NEEDED MORE, which is
         reported rather than absorbed. A region BELOW the body is only a
         well if the body is OPENED for it, and a cap with a hole cannot
         be ear-clipped -- so _bridge_holes splices each hole into the
         outer ring with a two-way bridge, and the two coincident bridge
         edges enclose no area. A hole that will not bridge falls back to
         a SOLID body and the item is reported: a wrong hole is worse
         than a missing one, and a silent wrong hole is worst.

         ONE TEST WAS VACUOUS AND IS RECORDED RATHER THAN REPLACED. The
         first tub test asserted that the well's height appears among the
         solid's z values and that there are more than twelve triangles.
         BOTH ARE TRUE OF A SOLID BODY WITH A BLOCK INSIDE IT, which is
         exactly what the broken version built -- it PASSED against code
         with the well branch disabled. The assertion is now the thing
         the eye checks: IS THERE A ROOF OVER THE WELL. A hollow tub has
         no horizontal face at rim height above its centre, and a block
         cannot satisfy that. Its precondition asserts the rim still
         exists, or "no roof" would be satisfied by building nothing.

         AND ONE CLARIFICATION A RED TEST PRODUCED: data-h is measured
         from the ITEM'S BASE, so kitchen_sink's data-h="2" is 2" above
         the counter (elevation 26), not above the floor. The test had
         assumed world z; the test was wrong and the extruder right. An
         annotation measured from the floor would have to know where the
         counter is -- which is a coordinate, which is the boundary.

         AUTHORING LIST NOW FIVE, THREE OF THEM DONE HERE: sofa, armchair
         and loveseat are redrawn. glass_shower (no fill at all) and
         boat_trailer (fills, but no body) remain, and stay separate from
         the generators.

         MERGED 2026-08-14, PR #29 (6fc9a29). Patrick's check, verbatim:
             "I looked - a sofa reads as a sofa, merge it - that looks
             fantastic."

WHERE THE FURNISHINGS WORK STANDS AFTER IT  2026-08-14
         The ruled order was: (1) prism, (2) the remaining generators by
         item count, (3) parameterisation after a read-back, (4) AI
         symbol drafting last and at authoring time only.

         (1) IS DONE and (2) HAS BEEN ANSWERED WITHOUT BEING BUILT, which
         is what the "build prism, re-measure, then decide" sequence was
         for. The four furniture generators -- seat, bed, basin,
         enclosure -- WERE NEVER WRITTEN. Region extrusion covers what
         they were wanted for, from artwork already on disk, with ONE
         generator that generalises to every form instead of four that
         each know one kind. THE FORMAL RULING ON RETIRING THEM IS
         PATRICK'S AND IS NOT RECORDED AS TAKEN.

         vehicle is the one form with a case left, and it is the LOFT
         design in VIEWER_NOTES section 5 -- a car-shaped slab against a
         car. That design predates all of this, still stands, and its
         urgency is what changed: vehicles now extrude at the right
         footprint with real outlines.

         STILL OPEN, and both are ARTWORK, deliberately kept apart from
         code so a code task cannot acquire an artwork dependency:
             glass_shower   drawn entirely in strokes; no closed shape at
                            all, so it still falls back to a box
             boat_trailer   frame, rails and tongue are all <line>; only
                            fenders, coupler and lights are filled, so it
                            extrudes five disconnected slabs and no
                            trailer
         The other three on that list -- sofa, armchair, loveseat -- were
         done with the region work.

THE FOUR GENERATORS ARE RETIRED -- Patrick's ruling  2026-08-14
         handoff: 0015 (ruling only, no report)
         seat, bed, basin and enclosure are NOT DEFERRED, NOT PENDING,
         RETIRED. They were never written; what closes is the
         EXPECTATION that they would be, live since 0010's item TWO.
         vehicle is NOT retired with them -- the loft design in
         VIEWER_NOTES section 5 stands, and only its urgency changed.

         "NOT NEEDED" IS A MEASUREMENT AND "RETIRED" IS A DECISION, and
         the register should not blur them. The ruling was left to be
         taken rather than inferred from the fact that the generators
         had turned out unnecessary -- an inferred ruling is
         indistinguishable from a taken one a month later.

         THE REUSABLE PART IS THE SEQUENCE, NOT THE OUTCOME:

             BUILD THE CHEAP GENERAL MECHANISM, RE-MEASURE, THEN DECIDE
             WHETHER THE SPECIFIC ONES ARE STILL WANTED.

         It replaced "build five generators in descending item count,
         stopping when the remainder is not worth a function" -- which
         asks for a judgement IN ADVANCE, on counts, about work nobody
         has seen the results of. Building the specific ones first
         GUARANTEES work the general mechanism would have made
         redundant, and how much is unknowable until the general one
         exists.

         FOUR FUNCTIONS UNWRITTEN IS THE RECEIPT. Not deleted, not
         deprecated: never written, with the plan that called for them
         closing without them.

         Two conditions, so it is not applied where it does not fit: the
         general mechanism must be GENUINELY CHEAP (prism needed no new
         authoring at all), and the re-measurement must be real with its
         receipt FIXED IN ADVANCE -- "build it and see" is not this.

         And one correction that is part of the pattern rather than a
         blemish on it: the first re-measurement said 28 -> 1 and
         overstated the win. The honest number was 17 of 18 outlines
         still a plain rectangle. THE RE-MEASUREMENT STEP IS ONLY AS
         GOOD AS WHAT IT MEASURES, and it took Patrick looking at a real
         plan to find the sofa was still a slab.

THE ENCLOSURE CHECK -- ONE BOX WEARING THREE NAMES  2026-08-15
         (AMBER, nothing merges; measurement only, no fix)
         handoff: 0016 (ruling, landed on disk 2026-08-15 after arriving
         uncommitted), 0017 (the owed measurement, report only)
         Patrick's check on a real render found what the receipts had
         been silent about: shower, walk_in_shower and glass_shower are
         near-identical footprints at the SAME 78" height, so nothing
         about the extruder's correctness tells them apart. IDENTITY
         NEEDS A CATEGORICAL CHANNEL, NOT A SCALAR ONE -- the third
         instance of the rule, the first in 3D. Recorded in
         WORKING_AGREEMENT.md alongside the first two (thickness,
         fineness).
         AND A SEPARATE FINDING, RECEIPT-SHAPED RATHER THAN CHANNEL-
         SHAPED: "enclosure 6 of 7", the number that helped retire the
         four furniture generators, counted items that EXTRUDED A BODY
         -- not items that read as their kind. shower and walk_in_shower
         both extrude successfully to a box with no internal feature, so
         the model's own report (which names only items with NOTHING to
         extrude) cannot see them. Third time this exact substitution has
         happened on prism's own receipts; recorded as its own entry in
         WORKING_AGREEMENT.md, a sibling of the surviving-count rule.
         A FIRST VERDICT WAS WITHDRAWN, NOT OVERRULED: "the boat trailer
         is chunky" was said about a render that did not contain
         boat_trailer at all (1 room / 4 walls / 28 furnishings vs the
         render's 23 rooms / 106 walls / 49 openings). VACUOUS BY
         PRECONDITION, arriving at a person instead of at code -- the
         same class the negative-assertion rule already names. Standing
         fix, recorded in WORKING_AGREEMENT.md: a check request names the
         plan and lists the items it contains, so the reviewer can verify
         the subject was in frame before reading the verdict.
         THE OWED MEASUREMENT (0016 SS5, Code's -- explicitly not a
         ruling): for walk_in_shower, sauna and whirlpool, does the
         internal region come out RAISED or as an OPENED CAP (a well)?
         Answered black-box -- calling only build_model, unmodified, and
         asking whether a face exists at the body's full height over the
         region's centre, rather than re-deriving build_prism's own
         classification lines in a second copy that could drift.
         Positive control run first (bathtub, a known-correct well, must
         still read as one -- it does).
             walk_in_shower  18in region, 78in body  ->  WELL
             sauna           30in region, 84in body  ->  WELL
             whirlpool       30in region, 36in body  ->  WELL
         whirlpool's well is the CORRECT outcome for a vessel. The other
         two confirm the inference by measurement: form="enclosure"
         conflates a VESSEL (recess-into-top, right) and a ROOM (a tall
         hollow volume where a low internal feature should stand on the
         floor, not recess into the ceiling) -- a defect only Patrick can
         rule on, per his own instruction not to infer past the picture.
         AUTHORING LIST, RECONCILED: glass_shower and boat_trailer carry
         forward. shower and walk_in_shower join it (0016 SS4) for the
         featureless-box reason above -- both artwork, not code. sauna
         and whirlpool are NOT on it: their question is the form split,
         not the artwork. boat_trailer's own verdict is SEPARATED OUT
         (0016 SS5c): its form is vehicle, the one generator 0015 did not
         retire, and its failure -- five disconnected filled fragments --
         is what an open-frame plan symbol gives you; the likely fix is
         the loft design already in VIEWER_NOTES SS5, not a redraw. It is
         not sent for a redraw until that is decided.
         ORDER, AS RULED: the SS5 measurement first (done, this entry),
         since redrawing an artwork item the extruder would still punch
         a hole in is work done twice. The redraws wait on Patrick's
         ruling on the form split.

THE VESSEL/ENCLOSURE SPLIT, BUILT  2026-08-15  (AMBER, at a PR)
         handoff: 0018 (ruling), 0021 (report, opens the PR)
         branch:  d74-vessel-enclosure-split
         files:   floorplanner/viewer/fp3d.py  _gen_assets.py
                  assets/furnishings/manifest.json
                  docs/evidence/enclosure_form_measurement.py (+3 renders)
                  docs/defects/0075-*.md (new)  0069 (noted)
         Patrick's check: sauna's roof unbroken, whirlpool solid-body +
         translucent water, on the after render. walk_in_shower's row is
         answered from mesh numbers instead -- see below.

         THE §2 CONTROL RAN FIRST, AS ORDERED, BOTH SIDES: bathtub -> WELL,
         sofa's back (already proven RAISED by PR #29) -> RAISED. Neither
         side assumed from the prior probe.

         THE SPLIT: KNOWN_FORMS gains vessel. build_prism now takes the
         real catalog form (threaded through build_model's loop via a
         catalog_form variable captured BEFORE form gets overwritten to
         the generic "prism" dispatch tag) and asks ONE categorical
         question -- does this form allow a recess. vessel (bathtub,
         swim_spa, whirlpool): unchanged, height decides well vs raised.
         enclosure (shower, walk_in_shower, glass_shower, sauna): a
         region is ALWAYS a solid, never a recess, regardless of height.
         NOT A THRESHOLD -- categorical, on form, exactly as ruled.

         A SECOND BUG, FOUND BY DUMPING THE MESH, NOT BY THE PROBE. The
         first cut reused the "sits ON the body" extrusion formula
         (body_h -> region_h) for enclosures too -- correct for a pillow
         rising above a mattress, wrong for a room, where body_h is the
         WALL height and a low internal feature must stand on the FLOOR.
         Built walk_in_shower's bench spanning 18in to 78in -- a column
         near the ceiling -- instead of 0 to 18in. THE ROOF-OVER PROBE
         COULD NOT HAVE CAUGHT THIS: it only asks whether the CAP is
         open, and this bug never touched the cap. Fixed with a third
         bucket (grounded, alongside wells and on_body) using the SAME
         floor-to-height formula beside already had. The instrument
         family this project keeps caught the classification bug and had
         nothing to say about the extrusion bug one layer down -- a
         control proves the question it was built to answer, no more.

         THE MATERIALS SPLIT, BUILT ALONGSIDE IT. build_prism now returns
         (body_parts, region_parts), not one flat list -- build_solid's
         own internal dispatch flattens them back together, since it has
         no region_material to route a second list to; only build_model's
         direct call uses the split. _gen_assets.py's SOLIDS table gains
         an OPTIONAL 5th element (region_material), read via one
         unpack_solid() helper so the two consumers (the MATERIALS
         validation, the manifest writer) cannot drift on how they read
         the same row -- 88 rows stay the 4-tuple they always were.
             bathtub         body porcelain (unchanged)  region water
             swim_spa        body porcelain (WAS water)  region water
             whirlpool       body porcelain (WAS water)  region water
             walk_in_shower  body glass (unchanged)       region stone
             sauna           body wood (unchanged)        region metal
         swim_spa and whirlpool's OLD body material ("water") made the
         WHOLE TUB translucent, surround included -- one column carrying
         two facts, the D73/D74 disease again, same remedy: one
         normative source per fact.

         ONE THING THE RENDER CANNOT SHOW, and it is not a geometry
         problem -- confirmed by dumping the built mesh directly:
             furnishings:glass   z[ 0.0, 78.0]   body, translucent
             furnishings:stone   z[ 0.0, 18.0]   bench, right position
         The bench is the right size, right material, right place. IT
         DOES NOT APPEAR IN THE RENDER AT ANY GLASS ALPHA TESTED (0.35
         shipped, 0.12 synthetic, both restored after). The fp3d.py CLI
         does not composite an opaque interior mesh through a translucent
         body, independent of transparency. NOTED AGAINST D69 rather than
         fixed here -- exactly the class the ruling's own SS7 anticipated
         for sauna, and this turns out to be the sharper instance, since
         walk_in_shower's body is translucent SPECIFICALLY so the
         interior would be visible, and it still is not.

         D75 FILED ALONGSIDE THE SPLIT, D44's precedent, per the ruling's
         own instruction to state a limit when it lands rather than
         discover it later: an enclosure's region can only stand ON the
         floor, never recess INTO it (a shower pan, a floor drain). No
         catalog item needs this today.

         Whole catalog re-built as a sanity check: 95 of 95 furnishings,
         0 notes, only glass_shower still falls back to a box (unchanged
         -- no closed shape at all).

         THE CRLF PHANTOM-DIFF, MET AGAIN: regenerating assets touched
         all 95 SVGs' line endings with no content change. Isolated by
         diffing CRLF-stripped content against HEAD per file and staging
         only the one file (manifest.json) with a real difference, rather
         than committing 95 files of noise.
```
