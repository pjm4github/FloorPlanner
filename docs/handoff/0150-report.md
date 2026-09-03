# 0150 — report: R3 — roof planes + gable ends in `fp3d.build_model`

**Code, 2026‑09‑03, answering [`0139`](0139-ruling.md) §3 (R3), the next
tranche after R2c ([`0148`](0148-report.md)/[`0149`](0149-report.md),
closed).**

---

## 1. WHAT'S BUILT

**A `Roof` document record now becomes geometry.** `fp3d.py`'s `build_model`
gains a `roofs` section (new `roofs=True` param, `--no-roofs` on the CLI,
mirroring `floors`/`furnishings`), reading `doc["roofs"]` and building, per
roof: two sloped planes off the ridge, plus a vertical gable-end triangle at
each end whose `gable[i]` flag is true. Both are Qt-free — `fp3d.py` imports
neither `PyQt6` nor `floorplanner` (VIEWER_NOTES §1), and this tranche is
the first to touch that boundary since R1.

**The eaves span is re-derived, not read.** `Roof.span_in` is a live-scene
render affordance, not a document field (`RoofItem`'s own docstring) — a
document round-trip must re-find it from the plan's own walls, the same
search the editor's own `nearest_eaves_wall` (`roofs.py`) does. That
function imports PyQt6 directly, so it cannot be imported here without
breaking the isolation `test_build_model_imports_neither_qt_nor_floorplanner`
already guards — `_heading_deg`/`_dist_point_segment` are Qt-free
duplicates of the two `geometry.py` functions it calls, named as
duplicates rather than silently rewritten, with the tolerance/default-span
constants matched to `roofs.py`'s own (`ROOF_EAVES_ANGLE_TOL_DEG` = 20°,
`ROOF_DEFAULT_HALF_SPAN_IN` = 144).

**Pitch is derived exactly where the editor derives it.** Both heights are
measured from the level's own base (0140-ruling.md §3's amendment), and the
slope is `(ridge_h - eaves_h) / span` — the run to the WALL (`span`), not to
the overhang tip. The overhang does not add a second, flatter strip: it
continues the SAME plane at the SAME slope past the eaves line, so a plane's
outer edge sits at `ridge_h - slope * (span + overhang)`, below the eaves
height by exactly `slope * overhang` — checked directly
(`test_roof_overhang_continues_the_same_slope_past_the_wall`).

**Gable ends close; a hip end is left open and named.** `roofs.py`'s own
`RoofItem` docstring says there is no UI yet to set an end to a hip — that
is R4. So today every roof in the app is `gable: [True, True]` by
construction, but the document FIELD already supports `False` per ridge
end, and a hand-edited or future document could set it. R3 honours the
flag rather than assuming: `gable[i] is False` skips that end's closing
triangle and adds an INFO note ("hip -- not modelled until R4, left open"),
the same "known gap, reported" discipline the furnishing fallbacks already
use — never a silent gable substituted for a hip that was actually asked
for.

**A new mesh primitive, not a new geometry style.** `_prism_slab` is `_box`
generalised to a top ring whose z varies per vertex (a roof plane is not
horizontal) and to any ring length >= 3 (a quad for a plane, a triangle for
a gable). The bottom ring is the top offset straight down in world z by
`ROOF_T` (4in) — the same "offset in z, not the plane's own normal"
simplification `_box` already uses for walls and `SLAB_T` already uses for
floors, not a new one — which is also why the winding-normalisation trick
(2D signed area on `x, y` alone decides CCW) still gives the outward
direction: the sweep is purely vertical, so a side face's outward-ness
depends only on the tangential winding, not on how the top ring's z
happens to vary. Giving the roof genuine thickness (rather than a
single-sided sheet) matters here specifically because this renderer's
lighting TRUSTS the winding (`_box`'s own comment: "a shader that trusts
the normal renders an inward-wound face black") — a one-sided plane would
read correctly from above and black from below or behind, which an orbit
check would find immediately.

**Colour**: `ROOF_C = (0.52, 0.30, 0.06, 1.0)` — the same roof-brown
`roofs.py`'s 2D ink uses (`QColor(133, 77, 14)`), so the plan overlay and
the 3D model read as the same roof rather than two unrelated colour
choices.

No schema or document change — R3 reads fields R1/R2/R2b already wrote;
`Roof`, `design_from_scene`, `apply_design_to_scene` are untouched.

## 2. THE CHECK, RUN HEADLESS

[`0139`](0139-ruling.md) §3's own words for R3: *"orbit wiscaway: both
roofs, right pitch, gables closed (headless receipts: plane slope = derived
pitch; `--shot` PNG as evidence)."* The orbit itself is Patrick's own
manual check (next section); this session supplies both named receipts:

* **Plane slope = derived pitch.** A synthetic 300in x 200in shell with a
  ridge centred between its two long walls (span = 100 by construction, so
  the search result is unambiguous). With heights 96/132 the built mesh's
  z-extremes land exactly on `132.0` and `96.0 - ROOF_T`, AND the specific
  ridge/eave vertex PAIR (not just any pair at those heights) sit exactly
  `span` apart in plan — ruling out a bug that reaches the right two z's
  over the wrong horizontal run. `atan2` on that measured pair reproduces
  the formula's own pitch to the float.
* **Gables closed.** Default `gable: [True, True]` yields exactly
  `2 * 12 + 2 * 8 = 40` triangles (two 12-triangle plane prisms, two
  8-triangle gable prisms) — a deterministic count, not a "some triangles
  exist" check.
* **A hip end is left open and named**, not silently drawn as a gable:
  `gable: [True, False]` drops to `2 * 12 + 1 * 8 = 32` triangles and the
  model's `info` (not `notes` — a named, expected gap) carries "end 1 is a
  hip -- not modelled until R4, left open."
* **The 45° wing carries its own ridge**, per 0139-ruling.md §1's own
  sentence — proven by rendering it, not merely asserted: see the `--shot`
  evidence below, a house with an orthogonal ridge and a separate wing
  rotated 45° with its own ridge, both closed at both gable ends.
* **Qt-free isolation, re-asserted for the new code path specifically**
  (not inherited from the furnishings-only probe): a subprocess builds a
  model from a document carrying a `roofs` key and asserts `PyQt6` /
  `floorplanner` never enter `sys.modules` — the eaves search is a
  hand-duplicated copy of Qt-importing code, and a copy-paste mistake could
  easily have pulled the wrong module in.
* **Backward compatibility**: a document with no `roofs` key at all (every
  v5 plan written before R1) still builds; `roofs=False` suppresses the
  mesh without suppressing the `stats["roofs"]` count, mirroring how
  `floors=False`/`furnishings=False` already behave.

**`--shot` PNG, as the ruling names it by name**: `fixtures/roofs-r3-orbit-check.json`
(synthetic — a 360x240 house, orthogonal ridge, heights 96/150, 12in
overhang; a 120x80 wing rotated 45°, its own ridge, heights 96/132, 8in
overhang; the two masses are deliberately disconnected, so this is not a
claim about mitred roof intersections, which `0139-ruling.md` §2 already
named as v1's own known limitation — "the planes interpenetrate") rendered
via `python floorplanner/viewer/fp3d.py fixtures/roofs-r3-orbit-check.json
--shot docs/evidence/roofs-r3-planes-gables.png --no-furnishings`, run with
a real display per D77/D78 (offscreen cannot create a GL context on this
machine) —
[`docs/evidence/roofs-r3-planes-gables.png`](../evidence/roofs-r3-planes-gables.png).
Both roofs show a correctly-pitched pair of planes, closed gable ends front
and back, and the wing's ridge visibly running at 45° to the house's own.

## 3. TESTS AND GATE

`tests/test_viewer_model.py` (+9, all under the module's existing `viewer`
marker): the slope/pitch receipt, gables-closed count, hip-left-open +
named, overhang continuing the same slope (with its own precondition that
the overhang edge sits BELOW the eaves height, or the assertion proves
nothing), `roofs=False` suppression, a roofless legacy document still
building, and the new Qt-free-isolation subprocess probe.

Full suite: **1133 passed**, 7 deselected (`perf` lane), 0 failures. `ruff`
clean. `python tools/gate.py` (full mode): **GREEN**.

## 4. DISPOSITION

**R3 is AMBER tier** ([`0139`](0139-ruling.md) §3) — built and gated
GREEN, going to its own branch and PR next (`roofs-r3-planes-gables`), and
Code stops there: no merge without Patrick's own check. §2 above answers
the check headless and supplies the named `--shot` evidence; the PR is for
him to run it by hand in the real app — orbit `wiscaway` with a ridge
sketched on it (from R2/R2b's own check), confirm the pitch reads right and
both gable ends are closed.

**R3b, R4, R5 do not start** until this merges, per
[`0139`](0139-ruling.md) §4's standing order and
[`0145-ruling.md`](0145-ruling.md) §3/§4's confirmation that R3b (the
roof-clip dotted line) waits on R3's own plane-z geometry specifically.

**Carried, unchanged:** room-label rounding ([`0131`](0131-ruling.md) §2);
delta-snap sites; D61-family; D83/D84 (held); yard items; ridge/eaves
horizontal repositioning ([`0140`](0140-ruling.md) §4).
