# 0255 — report: his four fixes — the End-On dialog no longer takes the app down on the porch's shed roof; the window's elevation is a property on its sheet with a plan default; the schema audited against everything the app writes; iteration 11 of the house — on `window-sill-endon`, stacked on `roof-gable-climb-level`; AMBER, for his check

**Code, 2026‑10‑11.** No merge has happened since
[`0254`](0254-report.md) put iteration 10's fix on `roof-gable-climb-level`
(PR #84, AMBER, still open). His word, with that PR waiting:

> *"A couple of fixes are needed: 1) a bug: when the roof end on view of
> the new roof used for the porch, it crashes the application. Fix that
> so that the dialog box opens without crashing, 2) There needs to be a
> way to specify a window elevation above the floor. This should be
> managed in the properties of the window and set to a default value so
> that the plans use a default if not specified. 3) The schema needs to
> be updated to handle all the new items formats. 4) Finally, look at
> the house_cutout_transparent.png iterate, starting on iteration 11 so
> that the window position in the plan matches the image when rendered.
> This will require modifying the window elevation and window height to
> match the png picture."*

All four built on `window-sill-endon`, ONE commit, **stacked on
`roof-gable-climb-level`** (iteration 11 needs 0254's fix to show its
gable windows at all), pushed as `41b1a15` **without a PR** — one AMBER PR open at a
time, the stacked-work rule. §6 says what his word can do with it.

## 0. THE CRASH — measured, then fixed

Opened headless on a roof like his porch's (`form: shed`, right span 0,
right overhang 0, a hip at one end) the End-On dialog constructed and
died on its first paint, silently: `_EndOnCanvas.paintEvent` divided the
rise by the right span (`slope_r = rise / self.span_r`), and a Python
error inside a Qt paint event is fatal under PyQt6 — no traceback, the
process gone. `set_values` had clamped both spans to at least 1 since
R4b, which is why a gable never hit it; plan A's
`_apply_form_to_widgets` assigns the canvas's spans straight from the
spin boxes (a shed's right one 0, legitimately), the constructor calls
it after the first `_recompute`, and the next paint divided by zero.
(The clamp would not have been the fix either: a 1″ right span draws a
plane the shed does not have.)

**The canvas now knows a shed.** `set_values` keeps a zero right span;
`shed` is the property (no right span); the paint draws the one slope
down the left and the HIGH WALL under the ridge, no right plane, no
right eave, nothing divided by the right span; the right side's pitch is
the wall's, 90°, never labelled. The labels move to the left so the
ridge at the drawing's right edge is not clipped.
`tests/test_roof_shed_form.py` gains one: the porch's numbers, the
dialog constructed, the canvas painted through a real `QPainter`,
painted again after a ridge, overhang and hip edit, applied, and
switched back to a gable to show the gable's drawing unchanged. Opened
on every one of the house's eleven roofs (five shed porch pieces, the
shed dormer, five gables) in a probe: all paint.

## 1. THE WINDOW'S ELEVATION — a sill, a property, a default

* **The item.** `OpeningItem.sill_in`, `None` until set — the plan's
  default. `set_sill`. `data()`/`adopt()` are what every site that
  re-makes an opening goes through now — the collinear merge, the split,
  the extract, copy/paste — so the sill (and a door's type and swing)
  are carried by being named once; an older clipboard without the key
  is fine.
* **The default.** `DEFAULT_SILL_IN = 36.0` in `floorplanner/model.py`,
  beside the other schema constants. The 3D builder's own `DEFAULT_SILL`
  (Qt-free and standalone, so it cannot import it) is its twin, pinned
  equal by a test. The DXF export reads the record and falls back the
  same way it did.
* **The sheet.** `OpeningPropertiesDialog` gets a **Sill height** row on
  a WINDOW (a door and a gate sit on the floor): seeded with the record's
  value, or with the default and the note *"this one has not been set"*;
  OK writes what is typed (`_prompt_size` → `set_sill`). The head is
  the sill plus the size code's height, as before.
* **The document.** The bridge reads `sill_in` (absent stays `None`,
  never materialised) and writes it only once set — a record that never
  said goes on not saying. `head_in`, which nothing in the app writes,
  rides through a round trip as `_v5_extra` on the item (the wall's and
  the room's discipline) and is dropped when the size or the sill is
  edited, since it was measured from the old one.
* **Tests.** `tests/test_opening_sill.py` (7): the one default; a new
  window writes nothing; a set sill round-trips; `head_in` rides through
  until an edit; the sheet offers the row to a window only and seeds the
  default; OK applies it; a copy carries it, and a gate's swing is
  written (§2).

## 2. THE SCHEMA, AUDITED

Rather than guess which "new item formats" he meant, every design under
`fixtures/` and `examples/` (28 of them) was put through: validate the
file; load it into a scene; write it back; validate that; diff the keys
per object kind. The findings, and what moved:

1. **A window's `sill_in` was lost on every save** — the item did not
   carry it (the house model's 25 sills, among others). Fixed by §1.
2. **A gate's `door_type`, `hinge` and `swings_toward` were dropped by
   the writer**, which wrote them for `kind == "door"` only; a gate is
   drawn as the door it is (`walls.py`: "constructed exactly as a door
   and paints exactly as a door"), so a reloaded gate swung the default
   way. Written for both now; the schema's `door_type` description says
   "door or gate".
3. **The schema's words:** `sill_in` now says what absent means (the
   plan's default, 36″, `DEFAULT_SILL_IN`) and carries `"default": 36`;
   `head_in` had no description and has one.
4. **Everything the app writes validates** — the roof `form`, a dormer's
   `openings`, `host`, the wall and vertex `name`, the settings block —
   all 23 app-written documents raw-clean and round-trip-clean. The
   `provenance` and `active_floor` keys the scene writer "loses" belong
   to `design_document()`, which adds them; not a loss.
5. **Five hand-made fixtures fail the raw schema** (`prism-check`,
   `seat-check`, `walk-in-shower-close`, `enclosure-form-check`: no
   `units`; `roofs-r3-orbit-check`: `units: "in"`, vertices without a
   `level`). They are the 3D builder's own test inputs, read leniently
   by it, not documents the app wrote; left as they are and named here.
6. `examples/site_demo.json`'s seven furnishings are kinds the catalog
   does not have (`shrub`, `tree`, `bench`, `planter`) — the Yard catalog,
   RED on artwork scope since Phase 5; unchanged.

If he meant something narrower by "new items formats", it is in this
list or it is not, and he can say which.

## 3. ITERATION 11 — the windows at the picture's elevations and heights

Read off the picture: the porch floor to the porch ceiling as the first
floor's scale, a gable's eave corners to its peak as the second's (the
picture's gables are steeper than the 45° he ruled, so a second-floor
window is placed by proportion within its gable, not by inches off the
picture). Every window carries its own `sill_in`.

* **First floor:** every head on ONE line, about 90″ up — the bays' big
  windows `7260` from a 30″ sill, every other window `2448` from a 42″
  sill, in PAIRS 6″ apart beside the bays as the picture shows; the entry
  a 72″ double door to the same head (`7290`).
* **The gables:** a near-square `5454`, about a third of the gable's
  width as the picture's are, its sill 2″ above the gable's eave corners
  (50″ over the second floor). Iteration 10's `4860` from the knee wall
  ran to the ceiling.
* **The shed dormer:** three `2844` side by side 6″ apart, two thirds of
  the face, from the knee wall (48″) to 92″ — a band of wall under the
  dormer's roof edge, as the picture has; iteration 10's three `2460`
  filled the face to the top.

Schema and invariants clean. Published as
`fixtures/incoming/house_cutout.json`; shot with the app's view at the
three viewpoints (`iter-11-q3d-front.png`, `-front-left`,
`-gables-close`). The log is `STATUS.md` in the work folder; the
generator's constants at its top say every number.

## 4. THE RECEIPT

* `--quick` 1574 passed (1566 + the 8 new); ruff clean; the full gate
  GREEN on the branch commit.

## 5. TIER

**AMBER** — two things he sees: the End-On dialog on the porch roof
(opens, draws one slope and the high wall), and the window sheet's new
row (double-click any window). And iteration 11 in the 3D view against
his picture. The bridge change (a gate's swing written) is a round-trip
fix with a test.

## 6. THE BRANCH — stacked, his word on what happens

`window-sill-endon` sits on `roof-gable-climb-level` (PR #84), one
commit, pushed, no PR. The checkout is on it, so the app he runs has
all four. His word:

* **"land in turn"** — #84 lands as it is, then this one on top; or
* **"fold"** — this one into #84 (fast-forward the PR branch to it),
  and #84 lands with both.

## 7. `fixtures/incoming/`, with ages

* `house_cutout_transparent.png`, `house_cutout_1stfloor.png` — his own,
  2026‑10‑11.
* `house_cutout.json` (iteration 11), `house_cutout_work/` — mine,
  2026‑10‑11.
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 8. WHAT HAPPENS NEXT

His check of the four, and his word on #84 and the stack. Then 0248's E
and the hip run on his word. Behind them: the compose cost
([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0254`](0254-report.md).
