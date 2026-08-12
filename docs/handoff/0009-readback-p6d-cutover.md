# 0009 — read-back: P6.d, the cutover

**Measurement only. Nothing is wired, `scene.changed` still drives the stack, and
no command is constructed anywhere in the app.**

Carries the three questions ruled onto it. **Q3's determinism measurement is
already on disk and is carried forward, not re-measured.**

---

## Q1 — operation or entities? **ENTITIES, and undo comes back COMPLETE**

**Pre-committed consequence: `COMPLETE` → D67 stays deferred and the cutover
proceeds.** That is the outcome.

**`GestureCommand` records the affected entities, not the operation** — it holds
the `snapshot()` document **before** and **after**, and `undo()` calls
`_restore_state(before)`. A document contains **every level**, so a restore is
whole-plan by construction; the `floor` a command carries scopes *what the
gesture was allowed to touch*, never *what undo restores*.

**Measured on `examples/roundedMultifloor.json`** (81 walls on `default`, 41 on
`second`):

| | |
|---|---|
| precondition — the change spans floors | `['default', 'second']` |
| after `DragGesture.undo()` | `default` **restored**, `second` **restored** |
| **verdict** | **COMPLETE — every floor came back** |

**A precondition failure is recorded because it nearly produced a false pass.**
The first run changed *"the first six walls in scene order"* and they were **all
on `default`** — the assertion caught it, and without it the measurement would
have reported a complete restore of a change that never spanned floors, which is
the answer being sought arrived at vacuously. The probe now picks three walls
**per floor**.

**BOUNDARY, stated because the pre-commitment was written against a gesture this
does not perform.** [D67](../defects/0067-selection-is-not-scoped-to-the-active-floor.md)
is **testimony and unreproduced**, so the cross-floor *drag* was not driven here.
What was measured is the property the pre-commitment turns on: **when a gesture
has touched two floors, does undo bring both back?** It does. If D67's drag is
later found to mutate the scene by some route that never reaches `snapshot()`,
this answer does not cover it.

---

## Q2 — can commands be the SOLE source of the dirty signal? **NO — and the list is the finding**

**`scene.changed` cannot simply be retired from that path**, because document
mutations exist that no gesture command would ever construct. Parsed from the
census (`phase6-readback-census.json`), the public mutators **outside the twelve
classes**:

| file | mutating entry points not covered |
|---|---|
| `imageio.py` | `import_from_image`, `start_image_import`, `extract_from_reference` |
| `levels.py` | `delete_floor` |
| `items.py` | `contextMenuEvent` ×3, `adopt`, `dissolve`, `bake`, `mouseMoveEvent`, `crop_to_scene_rect` |
| `view.py` | `mousePressEvent`, `mouseReleaseEvent`, `dropEvent`, `cancel_temp` |
| `dialogs.py` | `refresh` |

**AND THE RE-CUT LIST HAS A GAP OF ITS OWN, which this question found.** P6.1's
original nine named `EditOpening`, `EditRoomProps`, `ChangeSettings` and *level
ops*. **My re-cut dropped all four**, because I derived the list from
`MainWindow`'s public mutators and those four are **not `MainWindow` methods** —
they live in dialogs, in item context menus and in `levels.py`.

**That is the same failure as the drag omission, committed a second time by the
same method.** A menu-shaped census misses what is not on the menu; a
`MainWindow`-shaped census misses what is not on `MainWindow`. **The re-cut list
is a lower bound and must be widened before the cutover**, with at least:
`EditRoomProps`, `EditOpening`, `ChangeSettings`, `AddFloor`/`DeleteFloor`,
`ImportImage`/`ExtractFromReference`, `AdoptIntoGroup`/`DissolveGroup`, and
whatever `dropEvent` places.

**So P6.c is NOT absorbed by the cutover** on this evidence. It could only be if
every document mutation ran through a command, and the table above says it does
not — the honest position is that commands become the **primary** source and
something still has to answer for the rest.

> **The reviewer's argument stands even so, and is worth separating from the
> conclusion:** `scene.changed` means *"something in the scene graph moved"*, not
> *"the document changed"* — which is why opening the viewer trips it and why
> every pending-term heuristic is another guess stacked on a signal answering a
> different question. **A `GestureCommand` IS a document mutation by
> definition.** That reasoning is correct; what the measurement adds is that the
> command set does not yet *cover* the document.

**Meanwhile dirty tracking stays exactly as it is**, per the ruling: its false
positive — clean-after-an-inverse reported dirty — costs a click, and that is the
direction where being wrong is cheap.

---

## Q3 — serialisation determinism: carried forward, not re-measured

`docs/evidence/p6c-serialisation-determinism.json`, on disk: **identical JSON
text** on five plans, three ways — same window twice, across a reload, and two
windows on one file — with a positive control confirming the comparator sees an
edit. **Compared as text, not as dicts**, because dict equality hides the
key-order difference a non-deterministic serialiser produces.

**The authoritative serialise-and-compare at close, quit and open is therefore
meaningful.**

---

## What the cutover now needs, in order

1. **Widen the command list** to cover the mutations in Q2's table. Until that
   is done the cutover would leave document changes outside undo — a *worse*
   failure than the one it fixes.
2. **Then P6.c**, on commands as the primary dirty source, with something named
   for the remainder.
3. **P6.d itself is AMBER and unchanged**: Patrick's check is the merge
   condition.

**D67 does not block.** Undo restores every floor.
