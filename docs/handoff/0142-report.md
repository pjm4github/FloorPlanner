# 0142 — report: R2 — roof menu, ridge sketch, eaves pick, minimal heights dialog

**Code, 2026‑08‑31, answering [`0139`](0139-ruling.md) §3 (R2) as amended by
[`0140`](0140-ruling.md) §3 ("its dialog now minimal: initial heights only,
no pitch logic").**

---

## 1. WHAT'S BUILT

**A new `Roof` menu, one action: Sketch ridge [G].** Sets the tool, same
mechanism every other tool uses (`TOOL_ROOF_RIDGE`, `set_tool`,
`_tool_actions`); the toolbar carries the same action with a generated icon
(`_gen_assets.py`'s `TOOL_ICONS["roof"]`, re-run — nothing hand-edited under
`assets/`).

**Ridge sketch reuses the wall tool's own snap machinery, not a second
copy of it**, per [`0139`](0139-ruling.md) §1's own instruction ("the ridge
tool calls that machinery"): `PlanView._wall_end_point` only reads
`wall.p1` and calls `_align_to_wall(wall, ...)` by identity, so a `RoofItem`
duck-types as the `wall` argument with zero new snap math. **Default
orthogonal, Shift free-angle — identical to a wall**, verified both by a
headless drive (below) and by `tests/test_roof_ridge_tool.py`.

**Two-stage gesture, matching Patrick's own words** ("pick a ridge line,
pick an eaves line"): press-drag-release sketches the ridge (mirrors
`TOOL_WALL_EXT`'s temp-item pattern exactly — a real `RoofItem` is added to
the scene at press time, removed if the drag is too short or Esc cancels,
same as a wall); the *next* click must land on an existing wall, which
becomes the eaves reference. A click that misses re-prompts and keeps
waiting rather than silently canceling.

**A minimal heights dialog** (`RoofHeightsDialog`, `dialogs.py`) — ridge
height and eaves height only, no pitch field, exactly what
[`0140`](0140-ruling.md) §3 asked R2 to stay to now that R2b owns the
three-way dialog. Eaves defaults from `DEFAULT_ROOM_PROPS["ceiling_height_in"]`
(96"); ridge defaults to eaves + 48". Cancel drops the ridge entirely, same
disposition as an under-length wall drag.

**The 2D overlay**: ridge drawn heavy and solid; eave lines and gable ends
dashed. **`span_in` — how far the eave lines sit from the ridge — is
NOT a persisted field.** [`0139`](0139-ruling.md) §2's own model
(`{id, level, ridge, eaves_h_in, ridge_h_in, overhang_in, gable}`) names no
width, and R3's own row ("Roof planes … *+ overhang*") reads `overhang_in`
as the small roof overhang past a wall face, not a building half-width — so
inventing a stored span would have meant either misusing that field or
adding one the ruling doesn't call for. Instead `span_in` is a live-scene
render affordance: the interactive eaves pick measures it directly off the
clicked wall (`eaves_span_from_wall`), and a roof loaded from a document
re-derives it automatically (`nearest_eaves_wall`: closest wall on the same
level running within 20° of parallel to the ridge) rather than trusting a
number that could go stale against the plan's own walls. **v1 assumption,
named**: the eave reach is symmetric about the ridge, mirroring
[`0140`](0140-ruling.md) §2's own symmetric-eaves-height assumption; a
`gable` end draws as a straight line unconditionally (no hip geometry yet —
that is R4).

**The bridge writes and reads roofs.** `design_from_scene` walks `RoofItem`s
into the document's `roofs` block, minting `rf1`, `rf2`, … (no prefix
collision: rooms already own `r`); **version flips to 6 only when a scene
has at least one roof, and the `roofs` key is omitted entirely when it has
none** — a version-5 document with no roofs key is still valid under the
same schema, per [R1's](0141-report.md) own migration discipline, so this
is the schema's `version` description finally made TRUE (0141's report
flagged it as aspirational; it now matches what the walk actually does).
`apply_design_to_scene` is the mirror, re-deriving `span_in` on load.
`canonicalize` sorts roofs by (level, ridge start) and renumbers, same
shape as vertices/walls/rooms. **`design_from_scene()`'s hardcoded
`"version": 5` is gone** — R1's report named this as the thing R2 would have
to touch, and it did, exactly where predicted (walking roof scene items).

## 2. THE CHECK, RUN HEADLESS

[`0139`](0139-ruling.md) §3's own words: *"sketch the main ridge and the 45°
wing ridge on wiscaway; modifiers feel like the wall tool."* Driven via
synthesized `QMouseEvent`s (the project's own headless-drag pattern,
`test_macro.py`'s `_send_mouse`), against a two-wall plan:

* Main ridge, default modifiers, drag (0,0)→(300,4): landed at **(0,0)→(300,0)**
  — orthogonal-snapped, exactly a wall's own default.
* Wing ridge, **Shift held**, drag (300,198)→(420,318): landed at
  **exactly (300,198)→(420,318)** — dx=dy=120, a true 45°, not rounded to
  square — exactly a wall's own Shift behavior.
* Both eaves-picked against real walls; `design_from_scene` produced a
  version-6 document with both roofs, **zero schema errors**
  (`floorplanner.design.validate.schema_errors`).

## 3. TESTS AND GATE

`tests/test_roof_ridge_tool.py` (new, 8 tests, `gui`-marked): orthogonal
default, Shift free-angle, under-length discard, Esc mid-draw, a miss-click
during eaves pick keeps waiting (does not cancel), a hit sets `span_in`
correctly, dialog-cancel drops the roof, the Roof menu carries the action.
`tests/test_design_bridge.py` (+7): a roof round-trips through
`design_from_scene`/`apply_design_to_scene` byte-identically at the second
`Design` (P1.5's own identity, extended); version omits/includes the
`roofs` key correctly; floor is read from the level, never the global
(mirrors the existing wall/room/furnishing guard); a roof with no nearby
wall falls back to `DEFAULT_HALF_SPAN_IN` rather than crashing;
`canonicalize` sorts and renumbers; a roof-bearing document validates
against the packaged schema.

Full suite: **1069 passed**, 7 deselected (`perf` lane), 0 failures. `ruff`
clean. `python tools/gate.py` (full mode): **GREEN** — including a genuine
finding caught and fixed along the way: the end-assignment census
(`tools/gate.py`'s own retired-shim grep) flagged `RoofItem`'s original
`self.p1 = …` / `self.p2 = …` constructor lines, because that check is
deliberately textual and project-wide, not class-scoped (its own docstring
says so). Fixed by making `p1`/`p2` read-only properties over private
`_p1`/`_p2`, mutated only through `set_ridge()` — the same shape `WallItem`
already uses for an unrelated reason (vertex identity); here it is adopted
purely to keep the retired assignment spelling retired everywhere in
`floorplanner/`, as the gate requires.

## 4. DISPOSITION

**R2 is AMBER tier** ([`0139`](0139-ruling.md) §3) — built and gated GREEN,
going to its own branch and PR next, and Code stops there: no merge without
Patrick's check. His own words are the check (§2 above already answers it
headless); the PR is for him to run by hand in the app — sketch a ridge,
sketch the 45° wing, confirm the modifiers feel like the wall tool.

**R2b, R3, R4 do not start** until this merges, per
[`0139`](0139-ruling.md) §4's standing order.

**Carried, unchanged:** room-label rounding ([`0131`](0131-ruling.md) §2);
delta-snap sites; D61-family; yard items.
