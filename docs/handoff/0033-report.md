# 0033 — report: the three redraws, built — AMBER, and one honest limit

**Per [`0029-ruling.md`](0029-ruling.md) §4, brief from [`0016-ruling.md`](0016-ruling.md)
§2–3, informed by [`0032-report.md`](0032-report.md)'s D76 finding.** AMBER —
nothing merges without Patrick's check.

**Per [`0016-ruling.md`](0016-ruling.md) §6's standing rule, the plan and its
items:**

* **Plan:** [`../../fixtures/shower-glance-check.json`](../../fixtures/shower-glance-check.json)
  — `shower` / `walk_in_shower` / `glass_shower`, left to right (placed by
  [`0031-ruling.md`](0031-ruling.md), untouched since).
* **Renders:** [`../evidence/shower-glance-before.png`](../evidence/shower-glance-before.png)
  (before, re-rendered fresh from this fixture, same camera) and
  [`../evidence/shower-glance-after.png`](../evidence/shower-glance-after.png)
  (after, same fixture, same camera).

---

## 1. THE BRIEF, PER `0032`'S FINDING — `beside` shapes, not regions

A mark drawn as a NESTED, annotated region (`build_prism`'s `wells` /
`on_body` / `grounded`) inherits D76's invisibility whenever the body is
translucent glass — `walk_in_shower`'s bench already proved this before any
redraw touched it. A mark drawn as a **`beside`** shape (a second top-level
ring in the plan symbol, its centroid outside the body's own footprint)
shares the body's material and is never enclosed by anything, so it
composites the ordinary way two adjacent meshes do. **All three redraws use
`beside` shapes.**

## 2. `glass_shower` — a filled body, plus its door leaf

**Predicate 1's fault, fixed at the root.** The four boundary lines with a
gap (representing "you can see through the glass, and here is the door
opening" in line art) are now one filled rect,
`R(1, 1, 58, 46, 0, sw=1.1)` — the conventional plan-symbol shape (solid
outline, a swing arc for the door), and no less correct than lines with a
gap. The existing door-swing arc (`Pth("M 11 47 A 23 23 0 0 1 34 24", …)`)
is kept as decoration; a new filled `beside` rect,
`R(11, 46.4, 23, 2.6, 0.3, top=76)`, is the door leaf itself, standing proud
of the front opening.

`extrudability()`: `(2, 1, False)` — was `(0, 0, False)`. Two closed filled
shapes (body + door), one connected component (they touch), still no nested
region (the door is `beside`, by design).

## 3. `shower` — a door leaf added to the existing body

Predicate 1 already passed (the body was always filled); predicate 3 flagged
it as body-with-no-region. New filled `beside` rect,
`R(4, 34.6, 27, 2.6, 0.4, top=76)`, standing proud of the front edge.
`extrudability()`: `(2, 1, False)` — was `(1, 1, False)`.

## 4. `walk_in_shower` — a second mark, because the first one is invisible

The bench (`grounded`, nested, `top=18`) stays exactly as it is — correct
geometry, correct material bucket, and per `0032`'s reconciliation, fully
contained in the body on all three axes, which is why it still does not
render. **Its fix is not redrawing the bench; it is adding a mark that does
not have the bench's problem.**

Added: a fixed glass panel at the walk-in opening — categorically distinct
from `glass_shower`'s swinging door and `shower`'s stall door, which is its
own real-world difference, not an arbitrary third variant. First cut used a
low curb (`top=4`, matching a real threshold's height) and it was **too
subtle to read at this render's own camera angle** — measured by looking, not
assumed: a close solo render showed only a sliver at the very bottom edge of
frame. Revised to a near-full-height fixed panel, `R(31, 41.0, 27.5, 1.8,
0.3, top=74)`, clearly visible as a distinct protruding leaf in a close solo
render (see §6).

`extrudability()`: `(3, 1, True)` — was `(2, 1, True)`; `has_region` was
already `True` (the invisible bench) and stays `True`.

## 5. THE CHECK ITSELF — the after-shot exists, and it should be looked at honestly

**Patrick's check, per `0029`/`0030`: do the three read as different things,
without being put side by side, at a glance?**

**At close range (§6), all three marks are clearly visible geometry** — a
protruding leaf catching different light than the body around it. **At
[`shower-glance-check.json`](../../fixtures/shower-glance-check.json)'s own
camera — the room-scale, walled view the fixture was built at — they are
harder to make out.** The after render is offered as-is rather than a closer
crop of it, because the fixture's own camera **is** the check, per
`0031`'s "the after-shot is this plan, this camera." **This may not be
enough**, and if it is not, the D74 lesson applies here too: a render at the
zoom a person actually works at is what tells you, and this is that render.

## 6. CLOSE-RANGE RENDERS, FOR WHETHER THE GEOMETRY ITSELF IS RIGHT

Not part of the check (different camera, not the fixture `0031` placed) —
built to verify each mark actually extrudes as intended before trusting the
room-scale render's small silhouettes. Not committed (scratch, single-item
plans); reproducible with `python floorplanner/viewer/fp3d.py <a one-item
plan for the kind> --shot <path>`, standalone per the standing note on GL
rendering needing a real display.

All three showed a clearly distinct protruding panel, correctly positioned
and sized, catching different shading than the body from the same light —
confirming the geometry is right even where the room-scale render makes it
small.

## Gate

`ruff` clean. Three pinned tests updated for the artwork's own legitimate
change, not loosened: `test_a_line_art_symbol_FALLS_BACK_and_is_NAMED` and
`test_the_fallback_still_draws_the_item` (`tests/test_viewer_model.py`) no
longer pin `glass_shower` to the fallback path — it now has a real prism —
and instead exercise the fallback mechanism against a synthetic line-art-only
kind (a nonexistent SVG filename, which `svg_outlines` already returns empty
for), so the tests keep meaning something once no real catalog item is
line-art-only. `test_an_unannotated_nested_shape_is_still_DROPPED` updates
its expected triangle count (12 → 24) for `shower`'s new door leaf while
still asserting the unfilled decoration stays dropped. Full suite:
`collected=734`, OFF/ON/DEEP each 727 passed, 7 deselected, `Gate-Verdict:
GREEN`. `docs/evidence/enclosure_form_measurement.py` re-run unchanged
(`walk_in_shower` still RAISED, `whirlpool` still WELL) — the vessel/
enclosure classification is untouched by this task.
