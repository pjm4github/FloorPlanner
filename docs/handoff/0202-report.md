# 0202 — report: R6.c — the roof tool across levels; measured on his fixture, three faults found and fixed; AMBER, stopped for his check

**Code, 2026‑09‑27, on [`0197-ruling.md`](0197-ruling.md) §5.** The record
first: [`0201-report.md`](0201-report.md) landed on `main` at `8034a34`
and is pushed; no merge has happened since it. His next word: *"proceed
with R6.c."* Branch `roofs-r6c-tool-levels` off `main` at `8034a34`,
PR #69 open, gate GREEN, **stopped for his check** (§5).

**What this tranche was built FROM, said plainly.** No ruling describes
R6.c beyond its name — 0197 §5: *"R6.c (the roof tool across levels)"* —
and none answered 0201 §5's two questions before his word came. So the
scope was set by two things and nothing else: **a measurement** of what
the roof tool does today on his fixture with the upper level being
edited, and **D67's own rule**, which is already the project's: *"An
inactive floor may be drawn; it may not be hit-tested, selected, banded,
or dragged."* What the measurement found broken is fixed; what needs a
decision is named in §6 and not built.

## 1. MEASURED FIRST — his fixture, the upper level being edited

Probe [`docs/evidence/r6c_roof_tool_levels_probe.py`](../evidence/r6c_roof_tool_levels_probe.py),
driven by real mouse events on the view, run on `main`'s code
([`…before.txt`](../evidence/r6c-roof-tool-levels-probe.before.txt)) and
on the branch ([`…after.txt`](../evidence/r6c-roof-tool-levels-probe.after.txt)).
"Show other floors" off and on; the results differ between the two only
where a ghosted wall must be visible to be clicked (rows 4 and 8).

| # | the gesture | before | after |
|---|---|---|---|
| 1 | a lower roof drawn over the upper plan — does it answer a hit query | **yes** (roof and end marker) | no |
| 2 | ridge tool, press on the lower roof's ghosted line at (991,708), drag 96″ | **no ridge started** | a ridge started |
| | control: the same drag on blank canvas | a ridge started | a ridge started |
| 3 | start snap asked 2″ from each of 136 wall ends only the lower level has | 0 snapped | 0 snapped |
| 4 | eaves click on a ghosted lower-only wall at (554,840) | **the pick was taken**, spans 714″ / 714″ | refused |
| 5 | dormer press where only the lower roof owns the ground | refused, the general hint | refused, **names the level** |
| 6 | a roof selected, then the level switched | deselected, 0 grips | the same |
| 7 | a ridge awaiting its eaves, then the level switched | **still awaiting**; a click on a wall of the level switched to was taken as its eaves, 714″ / 714″ | settled before the switch, 282″ / 282″ from its own level's wall |

Rows 3 and 6 were already right and are recorded because 0197 §5 named
the hazard as *"a ridge sketched on L2 picking up L1's vertices"*: **it
does not.** The start snap (`nearest_wall_endpoint`, `nearest_wall_body`)
has been scoped to the level being edited all along, and a roof holds
plain points, not shared vertices. The faults were elsewhere — rows 2,
4 and 7.

## 2. WHAT'S BUILT

* **A roof of a level not being edited answers no hit query.**
  `roofs._roof_hittable(roof)`: roofs editable **and** the roof's level
  is the active one. `RoofItem.shape()`, its grips' and its end marker's
  return an empty path otherwise — the mechanism R2c already uses for
  "shown, not editable", extended from one switch to the level. Its
  bounding rectangle is untouched, so it paints exactly as before. This
  is what fixes row 2: the ridge tool's own check for "a press on an
  existing roof" no longer meets a roof it cannot edit.
* **The eaves pick takes a wall of the roof's own level only**
  (`view.py`). A click on another level's ghosted wall is refused with
  the tool's existing prompt and the ridge goes on waiting.
* **A level switch settles the gesture first.**
  `levels._settle_gesture()` runs before `switch_floor`,
  `new_floor_named` and `delete_floor` change the level: a drag in
  progress is dropped; a ridge released and awaiting its eaves is
  completed against **its own** level's walls — `cancel_temp`, the same
  settling a tool switch has given since the disappearing-roof fix.
* **The Dormer tool's refusal names the level.** Pressed where a roof of
  another level is drawn: *"Dormer: the roof here is on level 'default'
  -- switch to that level to put a dormer on it."* A dormer's host stays
  a roof of the level being edited (§6).
* **The End-On dialog says where the roof stands.** On a level whose
  base is not 0 it adds one live line — on his fixture's rf3, *"Level
  'upper' has its base at 100": in the building the eaves stand at 125"
  and the ridge at 335"."* — and its note no longer calls the level's
  base *"the ground line"* ([`0201`](0201-report.md) §3). The three fields stay
  level-relative; what is typed is what is stored. On a level at 0 the
  dialog is unchanged but for that one word. **This is the one thing
  here built from a finding rather than a fault** — his to reverse.

No schema change, no document change, no macro change: the `DORMER`
token and the recorder were already scoped to the level being edited.

## 3. THE CHECK — receipts

`tests/test_r6c_roof_tool_levels.py`, **9 tests** (`gui`), mouse-driven.
**Eight fail on `main`'s code and pass on the branch** — run both ways,
not assumed: a roof of another level drawn and answering no hit query,
and back when its level returns; a ridge pressed on another level's
ghosted roof line starts, on a synthetic pair and **on his fixture**;
the eaves pick refuses the lower wall and then takes the upper one
(span 100″, not 300″); a level switch settles a ridge awaiting its eaves
on its own level's wall though a lower wall is nearer, and a later click
on that lower wall changes nothing; a level switch drops a ridge still
being dragged; the Dormer tool names the level; the dialog's line, live
as the ridge is typed, and the stored height equal to the typed one.
**The ninth passes on both and is a receipt, not a fix:** a ridge
sketched with the tool on the upper level composes at that level's
elevation — R6.b already did this; nothing had driven it through the
tool.

Every pre-existing test passes unmodified. Full suite **1392
passed**, 7 deselected (`perf` lane), `ruff` clean, gate GREEN — the
branch's own run.

## 4. FOUND BESIDE IT — measured, NOT built

**The Door tool places an opening on another level's ghosted wall**
(row 8 of the probe): from the upper level, with other floors shown, a
click on a lower-only wall at (554,840) took the lower level's openings
from **56 to 57**. It is the same lookup the eaves pick had
(`_place_opening` takes the first wall under the cursor) and the same
class as [D67](../defects/0067-selection-is-not-scoped-to-the-active-floor.md).
It is not the roof tool, so it is not in this tranche. With
`interior_walls()` ([`0201`](0201-report.md) §1) that makes **two
measured D67 sites, one predicate each**, waiting on a word.

## 5. HIS CHECK

Open `fixtures/wiscaway-2level-stacked-floor.json`, Floors ▸ `upper`.

1. **Roof ▸ Sketch ridge**, and start the drag **on one of the grey
   lines of the lower level's roof**: the ridge starts. (Before, nothing
   happened there.)
2. With Floors ▸ "Show other floors" **on**, sketch a ridge and click a
   grey lower-level wall for the eaves: refused, the prompt stays. Click
   an upper wall: taken.
3. Sketch a ridge, and before picking the eaves switch to `default`:
   the roof is finished on `upper`, with its eaves from an upper wall.
4. Right-click an upper roof's end marker: the dialog carries the blue
   line saying where the roof stands in the building.
5. **Roof ▸ Sketch dormer**, press on ground only the lower roof
   covers: the status bar names the level.

## 6. NAMED — what R6.c does NOT do, each his to order

* **A dormer cannot stand on a roof of another level.** His drawing has
  L1's main roof rising through the upper storey; a dormer lighting an
  upper room there is drawn by switching to `default`, and its heights
  are then measured from L1's base. Hosting across levels needs the
  host's plane and the dormer's heights on one datum — R6.b's `Lifted`
  is the means — and a decision about which level owns the record.
* **The R3b wall dash and the R5a trace are still same-level**
  ([`0200`](0200-report.md) §6, unchanged): an upper wall under L1's
  roof is capped in 3D and not dashed in plan, and L1's roof carries no
  trace for the upper rooms under it. The Dormer tool snaps to the
  trace, so the item above and this one are one decision.
* **A ghosted roof does nothing when clicked.** Editing a roof means
  being on its level. If he wants a click on a ghosted roof to offer the
  switch, that is one status line or one menu entry.
* **The gallery was not regenerated**: no picture in it shows the End-On
  dialog on an upper level, and nothing else visible changed.

## 7. `fixtures/incoming/`, with ages

`README.md` only.

## 8. WHAT HAPPENS NEXT

His check (§5). On his word PR #69 merges, branch deleted in the
merge step, and the merge is recorded in the report that follows
(0197 §7). Then whatever he orders of §4 and §6.

**Carried:** unchanged from [`0201`](0201-report.md).
