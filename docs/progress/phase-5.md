# Progress log — Phase 5 (Landscape)

*Append one entry per task. Newest at the bottom. See [`README.md`](README.md)
for the log's rules; the short form is **append, never revise** — a later
correction is a later entry.*

**This file was opened late, on 2026‑08‑12, and that is itself the first thing
recorded here.** P5.2 shipped and merged on 2026‑08‑11 without a progress entry,
so for a day the work existed only in a defect record and a handoff. The entry
below is written from the commit, the handoff and the diff rather than
contemporaneously, **and it says so** — a reconstruction that looks
contemporaneous is worse than one that admits its provenance.

```
P5.2 -- SETTABLE WALL TYPES, RAILINGS AND GATES  2026-08-11  (AMBER, merged at
         PR #26 after Patrick's check; the check then REFUTED part of it --
         see the follow-up entry below)
         handoff: 0011
         commits: 3f8af45 (census), e8b0243 (the work)
         files:   floorplanner/design/validate.py  floorplanner/view.py
                  floorplanner/walls.py  floorplanner/viewer/fp3d.py
                  floorplanner/viewer/VIEWER_NOTES.md  tests/test_openings.py
                  docs/defects/0073-*.md  docs/defects/INDEX.md
         gate:    698 collected / 691 passed, OFF/ON/DEEP all reconciling
                  ruff=clean vacuous=0 end_assign=0  Gate-Verdict: GREEN

         THE CENSUS CAME FIRST AND CHANGED THE WORK. Reporting before
         implementing, per the standing rule -- and this one earned it:
         implementing first would have built a schema field that already
         exists. `railing` was already in the schema enum, in the viewer's
         thickness, HEIGHT (36") and colour tables, and in an INVARIANT.
         FOUR OF SIX PROVISIONAL RULINGS WERE CONTRADICTED, mostly by being
         done already. No schema change, so R-B was not invoked and no
         revision entry was owed. The gap was confined to the SCENE and
         the UI.

         ONE -- D73, ONE TABLE, DUPLICATES DELETED. validate.py's STD_T is
         normative; the viewer's WALL_T and the scene's two-branch
         conditional are GONE, replaced by readers. Deleted rather than
         synced, because three tables that are synced become three that
         disagree again.
         HEDGE IS 18.0 BECAUSE IT IS THE MODEL'S VALUE, not because 18 is a
         better number for a hedge. Checked for a dependency on 12.0 before
         applying the rule: the corpus holds ONE hedge wall, NO test asserts
         a hedge thickness, and the only consumer was the renderer. Visible
         effect: one wall in site_demo renders 50% thicker.
         AND A MEASURED CONSTRAINT THE FIX HAD TO ROUTE AROUND. "Put it in
         the model layer and import it" was not enough: importing
         floorplanner.design.validate DRAGS IN THE QT BINDINGS, because
         floorplanner/__init__.py star-imports the editor -- measured, not
         assumed. fp3d is deliberately Qt-free and runs headless in CI, so
         it loads the module BY PATH. validate.py imports only json, math
         and pathlib, which is what makes that safe. Recorded at both ends.

         TWO -- THE thickness_in ROUND TRIP, MEASURED BEFORE DESIGNING
         CHANGE 1, because the census raised it and did not answer it.
         IT SURVIVES: site_demo carries six overrides, a load/save round
         trip preserves all six, and they ride in _v5_extra. So there was
         NO data loss and change 1 did not have to absorb a fix.
         But the measurement found the real fault on that surface: the
         scene DREW a retaining wall whose document says 8.0 at 4.5,
         because `t` was "EXTERIOR_T if exterior else INTERIOR_T" -- two
         answers for seven types. A DISPLAY divergence, not a data one.
         After: fence 2.0, hedge 24.0 (its override), retaining 6.0 and 8.0
         (theirs). All were 4.5.

         THREE -- THE THREE CHANGES.
         t resolves override -> STD_T -> INTERIOR_T fallback. paint reads
         self.t, so the plan drawing followed with NO CHANGE TO paint.
         The context menu offers all seven types, thicknesses READ from
         STD_T rather than written as literals, so a menu entry cannot
         drift from what the wall will actually be. WALL_TYPE_LABELS orders
         and names them and never DEFINES them -- a type added to the
         schema and omitted here is unsettable rather than silently
         renamed, and a test asserts the menu is a subset of the enum.
         THE GATE IS DERIVED, NOT CHOSEN: placing a door in a landscape
         wall makes a gate, because of what it was placed in. No mode, no
         tool, nothing to learn, and I7 becomes true BY CONSTRUCTION rather
         than by a check the user can fail. I7 has required this since P0.7
         and nothing could produce a gate; the string appeared once in the
         package, in the check itself.

         FIVE TESTS, and two exist to stop the others being vacuous: a door
         in a railing MUST fail I7, or "the gate satisfies I7" proves
         nothing; and a bad override must fall back rather than zero the
         wall. The I7-violating test rebases its own baseline, because the
         violation is the point of it and shadow mode would otherwise raise
         at teardown -- caught by the ON/DEEP lanes going red while the
         plain suite passed.
         The Qt-free guard is a SOURCE-TEXT grep and a docstring tripped it
         by naming the bindings in prose. The prose was reworded rather
         than the guard weakened -- the same code-versus-prose boundary the
         gate's end_assign check already has.

P5.2-FOLLOWUP -- THE THICKNESS RULING IS REFUTED BY THE MANUAL CHECK
         2026-08-12  (AMBER, new item, NOT a reopening)
         The AMBER gate worked exactly as it is supposed to: the code was
         green, the census was right, the implementation matched the ruling
         -- and the ruling was wrong. Patrick cannot tell a FENCE from a
         RAILING at working zoom and never will. Both are physically about
         two inches.
         THE GENERAL FORM, which outlives this feature: A CHANNEL COMMITTED
         TO REPRESENTING A REAL QUANTITY CANNOT ALSO CARRY IDENTITY.
         Thickness is already spent representing real thickness. It appears
         to work for hedge and retaining only because those genuinely ARE
         fatter -- that is the quantity being read correctly, not identity
         being communicated, and the two coincide there by accident.
         Filed as its own record with the second channel and the gate
         symbol; see the entry that lands with the fix.
```
