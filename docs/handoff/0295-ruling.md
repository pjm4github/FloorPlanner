# 0295 — ruling: the four views of a 1½-storey — one display rule, the "move dormer to layer" arrows, and two readings for him to confirm

**On his diagram, 2026‑11‑05** (four quadrants: active layer × the
dormer's layer; roof on L1 throughout; arrows *"move dormer to layer"*
between the quadrants of each row): *"the 4 ways we can edit this 1½
story floorplan … the dormer can be moved between layers and then the
representation of the dormer is shown differently … make sure that the plan
reflects these modalities."* It does, under one rule, and this file makes
that rule the display acceptance of 0293's P3.

## 1. THE ONE RULE — every quadrant follows from it

**An item draws SOLID, with its controls, only on its own layer while that
layer is active; on any other active layer it draws GHOSTED, with no
controls** — D67's rule, which `_roof_hittable` and the floor display modes
already enforce. The dormer's layer is its `level` (0293 §2c: its EDITING
HOME); the roof's is L1. So:

| active | dormer on | L1 walls | roof (L1) | dormer | dormer controls A–G, window bands |
|---|---|---|---|---|---|
| L1 | L1 (upper right) | solid | solid | **solid** | **live** |
| L1 | L2 (upper left) | solid | solid | ghost | none |
| L2 | L2 (lower left) | ghost | ghost | **solid** | **live** |
| L2 | L1 (lower right) | ghost | ghost | ghost | none |

Three consequences, ruled:

* **A dormer is SHOWN on both layers it can live on** — its host's and the
  one directly above (`host_roof_at`'s look-down, mirrored) — solid on its
  own, ghosted on the other, **regardless of "show other floors" and
  regardless of rooms.** Today `apply_roof_visibility` shows a foreign
  roof only when it covers a ROOM of the active floor (R6.a); his
  `little-dormer-test` has no rooms, and the upper-left quadrant would
  then be empty. A dormer is a fact about the roof it stands on, by the
  same reasoning R6.a used for a roof over a room.
* **The "move dormer to layer" arrows are 0293 P3's promote/demote**, both
  directions, with no geometry change (the byte-identical `build_model`
  receipt). They get a second door beside the dialog's selector: the End-On
  marker's right-click menu gains **"Move to level ▸"** listing exactly the
  two legal levels, the current one ticked. The gesture is recorded by the
  macro (0293 P3 vi).
* **0294 §2's window bands follow the dormer**: live on its layer, ghosted
  with it elsewhere. Nothing of the dormer is ever editable from the
  other layer — one home, one place to edit.

## 2. TWO READINGS — his word needed, one line each, with the next check

1. **"The upper left is the way the floorplan looks before a new layer is
   added."** The upper-left quadrant is LABELLED *dormer on L2*, and a
   dormer cannot be on L2 before L2 exists. Before a second layer exists the
   only reachable quadrant is the **upper right** (L1 active, dormer on L1,
   controls live), which is 0293 §3's modality 2. I take the quadrant
   LABELS as authoritative and read the sentence as naming the upper right.
   **Say "labels" or "sentence."**
2. **The jog in the ghosted L1 wall under the dormer (both lower
   quadrants).** The lower storey's wall is drawn continuous when L1 is
   active, but on L2 its ghost steps around the dormer, the cheeks running
   out to a face BEYOND the wall line — his *"bump the roof out to make the
   room wider."* Two readings: **(a) display** — the L1 ghost is clipped
   under the dormer's footprint and the dormer's face and cheeks are drawn
   in its place, so L2's plan reads as the storey's real boundary; **(b)
   model** — the dormer's face and cheeks ARE part of L2's boundary: walls
   a room can close against, which is 0293 P4's bound walls. The two are
   not exclusive: (a) is paint and lands with P3; (b) is P4. **Say (a),
   (b), or both** — I expect both, and have ordered nothing on (b) beyond
   what 0293 already does.

## 3. WHERE IT LANDS

Into **P3** (0293 §5): the table in §1 is its plan-view acceptance, taken
on `little-dormer-test.json` headless — per quadrant, which items are
visible, which are hittable (`_roof_hittable`, the grips' `shape()`), and
that the dormer's ghost appears on L1 with no rooms on the file. The
marker menu's "Move to level" and the always-shown ghost are two small
additions to P3's list; reading 2(a), if confirmed, is a third. P4 is
unchanged. Check session A (0293 §6) gains one line: switch layers and
move the dormer both ways; the four pictures should match his diagram.

**Carried:** 0293 §0 and §6; 0294 §5's order.
