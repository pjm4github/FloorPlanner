---
# permanent key, independent of GitHub
id: 53
title: "A room cannot be selected by clicking its region - a MISSING CAPABILITY, not a regression"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:task
  - area:ui
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-08
closed: null
closed_by: null
rank: 54
related: [47, 11]
state_source: report
github_issue: null
---

# D53 — A room cannot be selected by clicking its region

## Symptom

Reported 2026‑08‑08 at the D47 manual check: *"Clicking a room paints a brief
pressed state and drops it on release; the region is never retained as selected.
Press-and-drag does move a region, so the item receives the press."*

A room is reachable **only by its label**. A press anywhere else inside it — the
fill, which is the whole visible extent of the room — selects nothing, and if
something was already selected it is **deselected**.

## THIS IS A MISSING CAPABILITY, NOT A REGRESSION — ruled 2026‑08‑08

**Filed as `type:task`** ("correct as written, but must change") rather than
`type:defect`, and the framing is the ruling's, not a reading arrived at here.

The eight-case differential below shows the room region selected the room in
**zero cases on either tree**. There is no commit that broke this, because it
never worked. Calling it a regression would send the next reader hunting for
that commit, and the hunt would not terminate.

**What changed at A1 is that the masking went away.** `fragment` used to leave a
`GroupItem` over each piece, and a group's shape *is* its box — so pressing a
piece's region selected **the group**, never the room. A1 deletes those groups,
which is exactly what item 2 of its manual check required and what that check
confirmed ("three pieces, each floating, **no group boxes**"). The selection
that disappeared belonged to an object the ruling deliberately removed. Removing
a mask does not create the thing it was hiding.

*(One half sits closer to `type:defect` and is noted rather than reclassified:
pressing a room's region does not merely fail to select it, it CLEARS an
existing selection. That is the product doing something wrong. It is kept in
this record because it has the same single cause and the same fix.)*

## Mechanism

Two sites compose, and neither is wrong on its own.

**`rooms.py:775‑778` — `RoomItem.shape()` returns ONLY the label rect:**

    def shape(self) -> QPainterPath:
        p = QPainterPath()
        p.addRect(self._label_rect())
        return p

`boundingRect()` (`:769`) covers the path, the label and the corners, but Qt
hit-tests against `shape()`. So the region is not part of the item as far as the
mouse is concerned — which is also why press-and-drag *does* move a region: the
drag handle is the label, and `mousePressEvent` (`:968`) is reached only
through it.

**`view.py:359‑365` — a press with no item under it is EMPTY CANVAS:**

    # SELECT tool: pan when pressing empty space
    if self.itemAt(pos) is None:
        self._panning, self._pan_last = True, pos
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        self.scene().clearSelection()
        e.accept()
        return

`itemAt` consults `shape()`. So a press on a room's fill returns `None`, the
view concludes the user pressed blank canvas, and it **pans and clears the
selection**.

Each half is locally defensible: a label-only `shape()` keeps a room from
stealing clicks meant for the walls and furnishings inside it, and clearing on
empty-space press is ordinary canvas behaviour. Composed, they make the largest
visible object in the plan a click-through hole that also cancels the current
selection.

## Evidence

### The differential — `main` @ `a1172be` versus the branch @ `5a22a7f`

Same gesture (press + release, zero movement, SELECT tool), same plan
(`fixtures/fragment2room.json`), same probe run against both trees:
`docs/evidence/d53-click-selection-differential.json`, reproduce with
`docs/evidence/d53_click_selection_probe.py <repo-root> <plan>` (point it at a
`git worktree` for the `main` side).

| case | main | branch | **room** selected after release |
|---|---|---|---|
| ordinary room, **label** | `RoomItem`, selected | `RoomItem`, selected | **True / True** |
| ordinary room, **region** ×2 | `itemAt` → `None`, nothing | `itemAt` → `None`, nothing | **False / False** |
| fragment piece, **label** | `RoomItem`, selected | `RoomItem`, selected | **True / True** |
| fragment piece, **region** ×2 | `itemAt` → **`GroupItem`**, *group* selected | `itemAt` → `None`, nothing | **False / False** |

**The room is selected by its region in none of the eight measurements, on
either tree.**

**What this evidence does NOT establish.** It measures selection state and
hit-testing. It does **not** reproduce the *painting* of the "brief pressed
state" — a headless probe has no frame to observe — so that half is taken from
the report as described. `clearSelection()` on press plus a cursor change to
`ClosedHandCursor` is a mechanism consistent with it, offered as that rather
than as a measured match.

### The instrument boundary — which test would have caught this?

**None**, and the shape of the hole is measured rather than asserted. Two
mutations, each in its own `git worktree`, each grep-verified on disk before the
run: `docs/evidence/d53-instrument-boundary.txt`.

| mutation | result |
|---|---|
| `RoomItem.shape()` → empty path (no click can hit a room *at all*) | **3 failed**, 636 passed |
| `_update_edit_actions` no longer feeds `_sel_order` (no UI selection can reach any room op) | **639 passed — the whole suite green** |

**The first result is the interesting one, because it is not zero.** The suite is
not blind to room hit-testing: it pins the hit area **that exists**. All three
failures (`test_room_plain_drag_moves_whole_room`,
`test_room_label_ctrl_drag_nudges_label`,
`test_fuse_straggler_macro_steals_no_wall`) are **label** gestures, because the
label rect is the whole of what `shape()` has ever returned — and none is a
selection assertion; they are drag assertions that happen to need a press to
land. You cannot write a regression test for a capability that was never there,
so the tests pin the reachable area exactly and are silent about the rest.

**The second result is the boundary.** `_update_edit_actions` is the only path
by which a Qt selection reaches a room operation — it runs on `selectionChanged`
and maintains `_sel_order`, and `_selected_room_shapes()`, the input to every
`room_boolean` op, iterates `_sel_order` and nothing else. Cut it, and no
selection made by any gesture can reach any room operation. **All 639 tests
still pass.**

**Why the fragment tests did not catch it.** `tests/test_rooms.py`'s
`_overlapping_rooms` helper ends:

    win._sel_order = [r1, r2]

It assigns the selection list **directly** — never `setSelected()`, never a
mouse event, never letting `_update_edit_actions` run. Every
combine / intersect / subtract / fragment test therefore starts **downstream of
the entire selection mechanism**. They establish that the operation is correct
given its input, and assert nothing about whether a user can produce that input.

**That is vacuity by precondition at the INTEGRATION SEAM** — the precondition
(`_sel_order` holds two rooms) is established by the test itself rather than by
the mechanism under test. Same shape as defect 21's guard, one layer up: at a
seam instead of inside a function. **This is recorded as an instrument boundary
regardless of how D53 is fixed**, and is added to the boundary table in
[`../WORKING_AGREEMENT.md`](../WORKING_AGREEMENT.md).

**And it is not a criticism of those tests.** A unit test of a polygon operation
*should* start from a constructed input. What is missing is any test at the
other altitude — one that selects by gesture and asserts the selection — and the
absence is invisible from either side, because each layer's tests are
individually correct.

## Ruling

**Scope, ruled 2026‑08‑08. Tier AMBER — user-visible, needs the manual check.
Position: AHEAD OF A2.** Room click-selection is the most common gesture in the
application; D11's z collapse can wait behind it.

**(a) A click on a room's region selects that room, and the selection persists
after release with a visible selected state.** *"The absence of a visual is half
this defect — a selection nobody can see is not a selection."*

**(b) Shift-click toggles a room's membership in the selection. Ctrl-click does
the same.** Users try both, and two modifiers doing one obvious thing is cheaper
to learn than one modifier and a wrong guess.

**(c) Rubber-band selection keeps its current behaviour. Do not change it while
fixing (a).**

### Two findings that bear on (a), measured while filing

**The selected-state painting already exists and is simply never reached.**
`paint()` draws a blue dashed outline over the room path when `isSelected()`
(`rooms.py:806‑809`), plus the corner polygon (`:811‑815`). So (a) is not
"build a visual" — it is "make the state happen", and the visual follows. That
makes (a) cheaper than the ruling's wording implies, and the wording is right
anyway: nothing is *shown* today, because nothing is *selected*.

**But the existing visual may not be legible on the very rooms that prompted
this.** A floating room already paints a **dashed** boundary in orange
(`:800‑803`); selection paints a **dashed** outline in blue (`:807`) over the
same path. Two dashed outlines on one shape is exactly where "a selection nobody
can see" would survive the fix. Worth deciding as part of (a) rather than
discovering at the manual check.

**Why not simply widen `shape()` to the region.** A room sits above the walls at
`z=4` (`rooms.py:411`), so a region-wide `shape()` trades one click-through
problem for another: clicks meant for the walls, openings and furnishings
*inside* the room would start landing on the room. "What is on top at this
point" is the same question **D11 / A2** is asking, which is the reason this
record is `related: [11]` and the reason (c) fences the rubber band off — one
selection change at a time.

## Receipt

*(Open.)* Acceptance:

* the probe's four **region** cases flip from `False` to `True` while the four
  **label** cases stay `True`;
* a press on a room's region no longer clears an existing selection;
* shift-click and ctrl-click each toggle membership;
* rubber-band behaviour is unchanged — pinned by a test, since (c) is a
  boundary marker and a boundary marker with no assertion is dead weight;
* **and a test exists at the gesture altitude**, so the seam measured above
  stops being green under mutation 2.
