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

### THREE CONSTRAINTS, ruled 2026‑08‑08, BEFORE ANY CODE

**Constraint 1 — `shape()` has a blast radius, and it is not the one-line fix it
appears to be.** Qt hit-tests `shape()`, so widening it changes what is under
the cursor for every gesture over a room's interior. **Walls and vertices must
stay above the region in hit priority; a fix that makes rooms selectable and
vertices unreachable trades one defect for a worse one.** The census is below.

**Constraint 2 — panning must survive.** `view.py:359‑365` pans when the press
finds nothing. Make the region hit-testable and you cannot pan by dragging
inside a room — on a plan that fills the canvas, that is most of it. **The fix
must state what replaces it. Middle-mouse drag pans anywhere, unconditionally,
including over rooms**; that is conventional, collides with nothing, and does
not depend on what is under the cursor. Panning from empty canvas may stay as
it is.

**Constraint 3 — selection and floating must not share a visual channel.** A
floating room already paints a **dashed** orange boundary and selection would
paint **dashed** blue over the same path. **Dashed already carries two meanings
in this application** — the manual check's item 5 exists because a dashed edge
over a real wall is a fault signature. **Do not add a third.** Floating-ness is
a property of the *room*; selection is a property of the *view*; they get
different channels. Selection may tint the fill, add corner handles, or thicken
to a solid stroke — anything but a second dash on the same path.

### The census constraint 1 asks for — parsed, not grepped

`docs/evidence/d53-hit-census.txt`, produced by `docs/evidence/d53_hit_census.py`
(an `ast` walk of all 33 files in `floorplanner/`: every `QGraphicsItem`
subclass with whether it overrides `shape()`, every `setZValue` argument as
written, every `setFlag` with its enum, and every hit query with its enclosing
function). Grep finds the word; the parse finds the `setZValue` in a helper that
never names the class.

**Qt picks the topmost item whose `shape()` contains the point, so z is the
deciding term.** There are six item classes and the whole answer is here:

| item | z | vs `RoomItem` (z **4**) |
|---|---:|---|
| `OpeningItem` | `OPENING_Z` = **6.0** | **above — safe** |
| `WallItem` | `WALL_Z` = **5.0** | **above — safe** |
| **`RoomItem`** | **4** | — |
| `FurnishingItem` | **3** | **BELOW — loses its hit target** |
| `GroupItem` | **1** | **BELOW — loses its hit target** |
| `ReferenceImageItem` | **−1e9** | below (the backdrop; D11/A2 turns this into a type term) |

**Finding 1 — the constraint's wall half is already satisfied, by construction
and on purpose.** `config.py:88` reads `WALL_Z = 5.0  # walls sit above the room
fill so they stay crisp`, and `RoomItem.raise_to_front` re-establishes it after
every raise: room at `base`, its walls at `base + 4` / `base + 5`, its openings
at `order + 6`, with the comment *"the walls/openings sit ABOVE the fill so a
wall is never hidden under its own room tint"*. Widening `shape()` does not
endanger walls or openings.

**Finding 2 — THERE IS NO VERTEX ITEM.** The parse finds six `QGraphicsItem`
subclasses and none of them is a vertex or a handle: `Vertex` (`vertex.py:59`)
is a plain object — the model corner — and `_DragVertex` (`walls.py:27`) is not
a graphics item either. **Corner grabs are handled inside `WallItem`'s own press
handler, within the wall's own shape.** So "walls and vertices must stay above
the region" is **one condition, not two**, and `WALL_Z > 4` already holds it.
`raise_to_front` even lifts an unlocked wall to `base + 5` over its siblings'
`base + 4` precisely *"so corner clicks at a shared corner grab IT"*.

**Finding 3 — and this is the one that matters: FURNISHINGS ARE BELOW ROOMS.**
`FurnishingItem` is z **3** against `RoomItem`'s **4**. Widening a room's
`shape()` to its outline makes every room contain every furnishing inside it,
**above** it, so **every furnishing in the plan becomes unclickable and
undraggable**. That is precisely the trade constraint 1 forbids. And it is worse
after any room interaction: `raise_to_front` sets the room to `_z_top * 10 + band`
while furnishings stay at 3, so the gap widens permanently the first time a user
touches the room.

**`GroupItem` at z 1 has the same exposure** — and it is the object that was
masking this defect in the first place, which is a neat trap: the naive fix
would break the very item whose disappearance exposed the bug.

**Finding 4 — the "empty canvas" idiom has FOUR consumers, not one.** Constraint
2 names the pan. The parse finds `itemAt(...) is None` standing for *"the user
pressed blank canvas"* at **four** sites, and all four change meaning if a room
becomes hit-testable over its interior:

| site | what it does today | what breaks |
|---|---|---|
| `view.py:321` | Ctrl+drag rubber-band requires empty space | no additive band started from inside a room |
| `view.py:360` | pan, **and `clearSelection()`** | constraint 2's case |
| `view.py:540` | Room tool right-click → Paste room / New concept room | menu no longer offered inside a room |
| `view.py:557` | any other tool right-click → floor popup | popup no longer offered inside a room |

**Middle-mouse pan already exists, unconditionally, and is already first.**
`view.py:310‑314` handles `MiddleButton` *before* any tool or `itemAt` test. So
constraint 2's stated replacement is **already implemented** — the work is to
keep it and to decide what happens to the other three sites, not to build it.

**Finding 5 — constraint 3's rubber-band clause is safe, and for two reasons
worth knowing rather than trusting.** `select_in_rect` (`view.py:449`) does use
`IntersectsItemShape`, but (i) its first loop type-filters to
`(WallItem, FurnishingItem, GroupItem)`, so a room appearing in the results is
discarded; and (ii) it gathers rooms from a **full scan** — `scene.items()` with
no arguments — and decides with `item_fully_inside`, which for a `RoomItem`
tests `item.corners` (`items.py:937‑940`) and never consults `shape()`.
**Rubber-band selection is therefore independent of `shape()` in both halves**,
so constraint 3's "keep its current behaviour" costs nothing — but it must be
*pinned*, because nothing currently asserts that independence.

**Finding 6 — the app already contains one hand-rolled answer to this problem.**
The macro layer's `_cmd_select` (`macro.py:433`) picks from `scene.items(pt)`
with an explicit comment: *"prefer an editable item (furnishing / wall / group)
over a room, whose label can sit on top of what you meant to grab."* A
type-priority rule, written because the room's **label** already steals hits.
Widening the region makes that same problem general — and this is the precedent
for solving it by priority rather than by z alone. `_place_opening`
(`view.py:623`) is immune for the same reason: it type-filters to
`WallItem` / `OpeningItem`.

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

**Why widening `shape()` is not by itself the fix.** The census settles the
walls half in its favour (`WALL_Z` 5.0 > 4, and there is no vertex item) and
against it for **furnishings** (z 3) and **groups** (z 1). "What is on top at
this point" is the same question **D11 / A2** is asking, which is why this record
is `related: [11]`. The one precedent already in the tree — `_cmd_select`'s
*"prefer an editable item over a room"* — answers it by **type priority** rather
than by z, and that is the shape worth costing first.

## Receipt

**IMPLEMENTED at A1b, `957792c` on `a1b-d53-readback`. AWAITING THE MANUAL
CHECK — the fourth acceptance item, which is the merge condition.** Census
639 → **646 collected**, seven new tests, gate GREEN in all three modes.

**THE MUTATION RECEIPT — the item that decides whether the boundary CLOSED or
merely MOVED.** `docs/evidence/d53-mutation-receipt.txt`. Severing
`_update_edit_actions` from `_sel_order`, in a throwaway worktree, mutation
grep-verified on disk before each run:

| tree | result |
|---|---|
| before A1b, `5a22a7f` | **639 passed, 0 failed — the whole suite green** |
| after A1b, `957792c` | **1 failed**, 645 passed — and it is exactly `test_selecting_two_rooms_BY_CLICKING_them_feeds_a_room_operation` |

**DIFFERENTIAL RECEIPT — Patrick's `dragWallFuseStraggler` macro, per line, on
three trees.** `docs/evidence/d53-macro-differential.txt`. The first cut of this
fix **broke it**: line 4's plain `CLICK 338 236` went from selecting the
interior column and fusing it (18 → 16 walls) to selecting R2 with the count
stuck at 18, because the two preceding label-drags had run `raise_to_front` and
lifted R2 above `WALL_Z`, and **Qt routes a press to the topmost item by z**.
The ruling foresaw it — *"any scheme where hit outcomes depend on z is one room
interaction away from breaking"* — and Qt's own delivery was that scheme, which
is why `RoomItem.mousePressEvent` now declines a press another item outranks.
**After that, the replay is identical to `main` at every line**, wall counts
`[18, 18, 16, 16, 18, 15, 17, 16]`.

**Two deviations from the ruling, both forced by measurement**, both argued at
the code: `OpeningItem` is ranked (above `WallItem`) because a door is a Qt
child of its wall and both answer one point; `ReferenceImageItem` ranks *below*
the room, the one place "room always last" is not literal — the backdrop is a
full-canvas tracing aid, and above rooms it would make no room selectable while
an image was loaded, inverting this very defect. **And the Ctrl band could not
be made unconditional**: Ctrl is already an item-level modifier here (the label
nudge, the wall corner-drags), and six tests failed before any reasoning did —
so `_band_may_start` allows it on blank canvas and over a room's *region*,
which is what the ruling was for, and not on a room's label or another item.

*(Open — the manual check.)* Original acceptance, for the record:

* the probe's four **region** cases flip from `False` to `True` while the four
  **label** cases stay `True`;
* a press on a room's region no longer clears an existing selection;
* shift-click and ctrl-click each toggle membership;
* **furnishings and groups inside a room remain clickable and draggable** —
  constraint 1's real exposure, measured by the census, and the one a naive
  `shape()` widening breaks;
* **panning still works over a room** by the stated replacement, and the other
  three "empty canvas" sites (Ctrl-band, both context menus) each have a decided
  outcome rather than an accidental one;
* **a selected floating room is distinguishable at a glance from an unselected
  floating room and from a selected ordinary room** — constraint 3's acceptance,
  as ruled;
* rubber-band behaviour is unchanged — **pinned by a test**, since (c) is a
  boundary marker and a boundary marker with no assertion is dead weight, and
  since the census shows the independence currently holds by accident of two
  type filters rather than by any assertion;

**AND THE MUTATION IS PART OF THE RECEIPT, NOT AN EXTRA.** *"The fix is not done
when clicking selects a room. It is done when severing `_update_edit_actions`
from `_sel_order` breaks the suite."* Re-run **that exact mutation** in a
throwaway worktree as part of the receipt. **If it still yields 639 green, the
seam remains untested and the fix has only MOVED the boundary rather than closed
it.** You cannot write a regression test for something that never worked — but
you can write the test that *would* have caught it, and the mutation is how you
prove you did.
