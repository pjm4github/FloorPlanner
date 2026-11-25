# 0370 — ruling: a wall does not climb THROUGH a roof to reach a dormer above it. AMBER.

2026-11-25, reviewer session. Number 0370 is the next free one (0369 is the
highest, on `main`); if a file of yours took it first, this ruling keeps its
name and your report takes the next. Written into the working tree while it
stood on `pyramid-roof-stage3-0367` at `6fc2fe3`; it is untracked.

## 1. Patrick's words

2026-11-25, on the gable dormer over BR3 in his Wiscaway plan, after the
settings were corrected and a skirt roof was put under it: *"The dormer face
and the corners on the face and cheek walls should not be there. See if you
can adjust the settings on the dormer to remove them and if not then make a
note of it so that Code can build a feature to fix that."*

## 2. What was measured (headless, `fp3d.build_model`, tree at `6fc2fe3`)

Plan: `C:\Users\pmora\OneDrive\Documents\FloorPlanner\wiscaway2026-11-25-BR3-dormer.json`
(his file plus two changes: dormer `f129` re-set, roof `rf5` added). It is a
user plan file: read it, do not commit it.

The geometry there, in plan inches (y grows toward the front):

| Thing | Where |
|---|---|
| L1 exterior side walls of BR3 (`w90`, `w103`) | x = 797 and x = 947.5, running to y = 840 |
| L2 dormer `f129` on host `rf2` | face at y = 804, cheeks on x = 797 / 947.5, eave past the face 12 |
| L1 lean-to `rf5` under the dormer | high edge y = 804 at 144, falling to 120 at y = 840 |

Result: two posts of `walls:exterior` material, **x 793.9–799.9 and
944.6–950.6, y 804–816, z 0 → 202.2**. They are the two L1 side walls, risen
through `rf5` (whose surface there is 144 → 136) up to the dormer's underside,
for exactly the depth of the dormer's rake overhang.

Settings sweep on `f129`, everything else held:

| Setting | Posts |
|---|---|
| eave past the face 12 (as delivered) | y 804–816 |
| eave past the face 6 | y 804–810 |
| eave past the face 3 or 0 | none (and no rake overhang) |
| face type balcony; roof skirt on / off; box 60 | unchanged |
| eave overhang 0 | half as thick, still there |
| side guide 60 | none, because the dormer roof no longer covers its own walls |

So no setting removes them while the dormer keeps a rake overhang. This is the
answer given to Patrick; the plan keeps 12.

Cause, as read (`_wall_under_roofs`, about lines 1905–2030): a `to_top` piece
inside a dormer's territory takes `dormer_over(pc)`, the covering dormer whose
surface is highest, and `above_bounds` stops the climb only where the storey
above has a room or a wall over the piece. Nothing stops it at a roof that is
drawn between the wall and the dormer. That is my reading; measure it before
you rely on it.

## 3. The rule

**A climbing wall piece stops under the first roof that is DRAWN over it.**
Dormer climb and gable climb alike. "Drawn" means the model emits roof there,
including the part of a lower roof kept under a higher roof's overhang (`rf5`
under the dormer's rake is drawn; the probe finds it at 138–142 at y = 807).
A host plane that is cut away inside its own dormer is not drawn there and
stops nothing: the wall under a dormer face still climbs into the dormer, as
it does today.

## 4. Orders

- **O1. Fixture, then a failing test.** Build a minimal plan of your own (an
  L1 box with a gable host, a bump-out past its eave, an L2 gable dormer whose
  face overhang covers the bump-out's side walls, an L1 shed under that
  overhang). Assert no wall-material vertex stands above the shed's surface
  inside the overhang strip. Show it RED on `6fc2fe3` first.
- **O2. The control.** In the same fixture with the shed removed, the walls
  DO climb to the dormer. Assert that too; it must pass before and after.
- **O3. Fix** to the rule in §3. Mechanism is yours; say what "drawn" is
  computed from.
- **O4. What must not move.** Hash every mesh of all 26 `0360-dormer-orderings`
  cases and the `0367-pyramid-roof` cases before and after. Report the count
  identical. Each case that differs gets its name, the vertex delta and a
  picture; none is waved through as "expected".
- **O5. Readback on his plan.** Re-run the probe of §2 on the plan file as
  delivered: posts absent at eave-past-the-face 12, wall tops in the strip at
  or under `rf5`.
- **O6. Report** as the next number. Not a mechanical phase.

## 5. Recorded, not ordered

Patrick asked for the skirt to run around BR3. Hipped ends on `rf5` were tried
and dropped: the §8.4 cantilever floor is laid at the L2 floor (134) across the
dormer's whole overhang even where a lower roof lies under it, so it stands
proud of the hips at the corners, and the L2 face wall's base (134) shows above
them. He accepted the lean-to. Whether this is ruled comes after his other four
dormers have been through the same pass; do not start it.

D89 (the 0360 skirt not showing in the live app) is not touched by this.

## 6. Tier and Patrick's check

AMBER: it changes what the 3D view shows. Stop before merge. One check, to be
batched with whatever else is waiting for him:

1. Open `wiscaway2026-11-25-BR3-dormer.json`, 3D view from the front: no posts
   under the rake at the two front corners of the BR3 dormer; the skirt and
   the gable face unchanged.
2. Any 0360 case O4 reports as changed, side by side.
