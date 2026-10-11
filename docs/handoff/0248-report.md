# 0248 — report: his house picture built as a design — `fixtures/incoming/house_cutout.json`, four iterations with renders; where the roof and dormer tools fell short, and the plan proposed

**Code, 2026‑10‑11.** No merge has happened since
[`0246`](0246-report.md). His instruction, with
`house_cutout_transparent.png` dropped in `incoming/`:

> *"Create a house json model of that image that will have the proper
> roof lines in that projection. Do not bother with the interior rooms,
> just concentrate on the windows, doors, roof lines, shed dormers and
> gable end dormers. Also include the roof over the porch. If the roof
> and dormer tools fall short in their capabilities, make a note of that
> and we will make a plan to enhance the roof and dormer tools. … Give
> me a status of the iterations and an intermediate rendering as you
> iterate through the json model. You can save intermediate results in
> a directory so I can monitor your progress."*

## 0. THE DELIVERABLE

**`fixtures/incoming/house_cutout.json`** — schema and invariants clean.
Two levels (108″ + 96″), a 720 × 432 body, an 8:12 main roof with a 24″
knee wall, the big left cross gable (18:12, its ridge 4″ under the
main's), the smaller right gable at the same pitch, a one-plane shed
dormer with three windows, a hipped 3:12 porch roof the full width of
the front with a 12″ overhang, the double entry door, six first-floor
windows, a window per end wall per level. No rooms, no posts, no porch
floor — as asked.

**`fixtures/incoming/house_cutout_work/`** — the iteration log
(`STATUS.md`), the generator (`make_house.py`, every dimension a named
constant), `iter-01`…`iter-04` as documents with front, front-left and
dormer close-up renders (`docs/evidence/render3d.py`, headless), and the
two helpers (`check_and_render.py`, `probe_dormer_wall.py`). Left in
`incoming/`, uncommitted, for his look; it is not his drop, so it is not
promoted. If he wants the design on the record, the generator is the
thing to keep (it regenerates the document), with the final document as
a fixture.

## 1. THE ITERATIONS, in one line each

1. Massing — right, but the shed dormer and porch roof sloped backwards
   (`span_in[0]` is the ridge direction rotated +90° in plan: the FRONT
   for a ridge running +x), the schema refused a zero span, and the left
   gable's ridge at exactly the main ridge height degenerated in the clip
   (a fin on the back slope, no gable).
2. Orientation fixed, 1″ back strips for the one-plane roofs, the left
   gable's ridge dropped 4″ — the house reads: both gables, the shed
   dormer with its face, the hipped porch roof.
3. The shed dormer's front edge pulled 1″ inside the house wall, so the
   wall's windows are what shows rather than the generated cheek.
4. Dormer windows at the picture's proportions; the wall under the
   dormer measured as built (three windows cut, top at the dormer plane)
   with the generated cheek an inch behind it, seen through the glass.

## 2. WHERE THE TOOLS FELL SHORT — nine, measured

1. **No one-plane roof.** A shed roof or shed dormer is a gable with a
   1″ second span (`span_in` has an exclusive minimum of 0). It builds,
   but a shed dormer's generated face comes out at one end only (both
   ends sit on the host plane; `_dormer_face` takes the first), so one
   side is open.
2. **A dormer whose eaves line lies on a house wall** gets a generated
   cheek on top of that wall, burying the wall's openings.
3. **A generated cheek just behind a house wall shows through its
   windows** as a run of 3″ boxes (the headless painter; the GL view
   shades it flat).
4. **No openings in a dormer that has no house wall under its face.**
   A set-back dormer's generated face is blank; the dormer record has
   no openings of its own.
5. **A cross gable meeting the main ridge at equal height** degenerates
   in the clip. Worked around by dropping the gable's ridge 4″.
6. **Hipped ends on a one-plane roof**: the hip run is the mean of the
   two spans (48″ here), which happens to look right on the porch; it is
   an accident of the formula, not a setting.
7. **No porch posts** — no column object; the porch roof floats.
8. **No porch floor, steps or base**; not attempted.
9. **A porch roof cannot turn a house corner**: it would need an
   L-shaped one-plane roof or two joined ones.

## 3. THE PLAN, proposed — his to order

A. **A roof `form` field: `gable` (today) | `shed` | `hip`.** `shed`
   carries one span and one slope; the clip, the item and the builder
   already handle a one-sided footprint (the 1″ strip proves it), so this
   is the record, the dialog and the validator, with `_dormer_face` on
   both ends of a shed dormer. Closes 1 and 6.
B. **Dormer openings.** `openings` on a dormer record (face only), cut
   into the generated face the way wall openings are cut. Closes 4.
C. **The cheek yields to a wall.** Where a house wall stands on a
   dormer's eaves or face line, the generated piece is skipped and the
   wall climbs as it does today. Closes 2 and 3.
D. **Equal-height ridges.** The joined-end extension of a ridge ending
   exactly on a host's ridge is a known degenerate case of the clip;
   a test on it, then the fix in `compute_roof_clips`. Closes 5.
E. **Posts and the porch floor** — a `post` furnishing kind (a square
   prism from the level to the roof above) and a `slab` region; the
   yard-items work this belongs with is named, not ordered.

A then C are small and GREEN-adjacent; B is a format change (AMBER); D
is a clip change (AMBER, RED without a fixture); E is a feature.

## 4. ONE THING ABOUT THE SESSION, recorded so it is not repeated

Running the generator from inside its folder moved both tool shells'
working directory there for good, and the commit hook — invoked by a
relative path — then refused every command, in every shell and every
subagent, until he relaunched from the root. The iterations were run
through subagents in their own git worktrees meanwhile. A memory note
now says never to `cd` in a tool command.

## 5. `fixtures/incoming/`, with ages

* `house_cutout_transparent.png` — his own, 2026‑10‑11; the picture.
* `house_cutout.json`, `house_cutout_work/` — mine, 2026‑10‑11, §0.
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 6. WHAT HAPPENS NEXT

His look at the model and his word on §3. Behind it: the compose cost
([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0247`](0247-report.md).
