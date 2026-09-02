# 0149 — report: R2c closed — the disappearing-roof bug found and fixed, PR #51 merged

**Patrick, 2026‑09‑02, in chat:** reported *"When I draw the roof (with
the ridge tool) then select the another tool, the roof disappears!"*,
supplied a reproducing macro (`fixtures/incoming/disappearingroof.fpm`),
confirmed *"It does return when I use Control Z but the shape it wrong,"*
then, once fixed: *"merge it once CI's green."*

---

## 1. THE BUG, ROOT-CAUSED FROM HIS OWN MACRO

His macro, six lines: four walls closing a rectangle, `G CLICK ... DRAG
...` sketching a ridge across them, then `S ^Z` — switch to Select, then
Undo. **The eaves-pick click is never made.** That is the whole defect:
`RoofItem`'s Stage‑1 preview (eave lines, gable ends) renders in full the
moment the ridge is released — before the eaves wall is ever clicked — so
it reads as a finished roof on screen. But `PlanView` still considered it
mid‑gesture (`_roof_awaiting_eaves`), and `cancel_temp()` — fired by any
tool switch, or Esc — discarded it under the same rule an under‑length
wall drag uses. Correct for a ridge still being dragged; wrong for one
already released and shown as complete. His own diagnostic (`Ctrl+Z`
brings it back, with the wrong shape) confirmed the mechanism exactly:
the roof-less state got committed to the undo stack when `S` ran, and the
RESTORED roof (via `apply_design_to_scene`'s own span re-derivation) did
not match what had briefly been on screen.

## 2. THE FIX

`cancel_temp()` no longer discards an abandoned eaves‑pick — it
auto‑completes it, deriving `span_in` from the nearest qualifying wall,
the exact same search a **loaded** roof already uses to re‑derive
`span_in` (`nearest_eaves_wall`, unchanged, just called from one more
place). Heights stay at `RoofItem`'s own constructor defaults, adjustable
afterward from the marker's own dialog. A ridge still **mid-drag** (not
yet released) is unaffected — it still discards on cancel, matching the
wall tool's own precedent exactly; only a **released, awaiting-eaves**
ridge gets the new treatment.

His macro is now a permanent fixture and regression test:
`fixtures/disappearingroof.fpm` (promoted from `incoming/`, entry in
`fixtures/README.md`), replayed verbatim by
`tests/test_roof_ridge_tool.py::test_replaying_the_reported_macro_keeps_the_roof_after_switching_tools`
— confirmed RED against the unfixed `cancel_temp()`, GREEN after. Two
more targeted tests cover the same fix directly (Esc-equivalent and
tool-switch paths), and the pre-existing test that had asserted the OLD
(buggy) behavior — `test_escape_mid_draw_removes_the_ridge` — is rewritten
to `test_escape_before_the_ridge_is_released_discards_it` (the drag-not-
yet-released case, still correctly discarding) plus a new
`test_escape_while_awaiting_the_eaves_pick_keeps_the_ridge` (the fixed
case).

## 3. DISPOSITION — R2c CLOSED, MERGED

[PR #51](https://github.com/pjm4github/FloorPlanner/pull/51) merged to
`main` at `dab927a`, branch `roofs-r2c-show-edit` deleted (local and
remote), per his explicit *"merge it once CI's green"* — CI was already
green at that point. **R2c is done.**

**R3 is the next available tranche (AMBER)** — roof planes + gable ends in
`fp3d.build_model` ([`0139-ruling.md`](0139-ruling.md) §3), per
[`0145-ruling.md`](0145-ruling.md) §4's order: R2b → R2c → **R3** → R3b →
R4 → R5.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items;
ridge/eaves horizontal repositioning (R4).
