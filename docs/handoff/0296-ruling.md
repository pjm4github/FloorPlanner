# 0296 — ruling: the DORMER WALL — a wall type minted from the dormer, on the storey above the host, editable only from the dormer; promotion exists only once that storey does

**On his two answers, 2026‑11‑05, to 0295 §2:** *(1)* the one-layer state
is the **upper right** quadrant; *"if the second layer does not exist then
the dormer cannot be promoted … the promotion can only be available once
there is a layer."* *(2)* **both** readings, and more: *"I want the room in
L2 to 'close' by matching the cheek walls from the dormer even though the
dormer is on L1. This should be a 'special wall type' that is created from
the dormer, is available for L2 wall operations, and is only editable from
the dormer editor controls."*

## 1. PROMOTION — gated on the storey above existing

The "Edited on level" selector (0293 P3 ii) and the marker's "Move to
level ▸" (0295 §1) list only levels that EXIST among the two legal ones —
the host's and the one directly above by elevation. On a one-layer plan
both are disabled with the note *"add a level above level L1 to move the
dormer."* Adding a level later enables them; nothing moves by itself.
0293 §3's reading of modality 2 stands as he confirmed it.

## 2. THE DORMER WALL — 0293 P4 restated

**A new wall `type`: `dormer`.** The precedent is PR #98's `beam` and
`partition` (0288): an enum value added, `STD_T` extended, no version bump.
What it is:

* **Minted from the dormer, never drawn.** Three parts — `face`,
  `cheek_left`, `cheek_right` — each an ordinary `walls` record with
  `type: "dormer"` and `bound_to: {"roof": <dormer id>, "part": ...}`
  (required when the type is `dormer`, forbidden otherwise — a schema
  conditional). Thickness `STD_T["exterior"]`. Its two vertices are
  DERIVED from `_dormer_wall_lines()` at every dormer rebuild, through the
  vertex API (no `.p1 =`; the gate's census), and still written — the
  `eaves_bind` discipline.
* **Its level is the storey ABOVE the host — always**, whichever layer the
  dormer is edited on. A dormer on L1 with an L2 mints L2 walls; a dormer
  on a one-layer plan mints nothing (an attic has no plan to close). That
  is his sentence exactly: the L2 room closes against the cheeks *"even
  though the dormer is on L1."* A dormer's promotion does not move its
  walls; they were never on its layer.
* **Created and removed from the dormer dialog**, three checkboxes under
  *"Walls on level L2"* (face, left cheek, right cheek), on by default for a
  dormer whose storey above exists; the same controls on the marker menu.
  Not automatic at dormer creation: a hand-drawn L2 wall already on a line
  would be welded into by surprise. `remove_with_dormers` removes them with
  the dormer; deleting the level above removes them with the level.
* **Available to every L2 wall operation that READS:** room detection
  (`face_at`, as an exterior wall), welding (a hand-drawn L2 wall may share
  a dormer wall's vertex — the knee wall welded to a cheek's back end
  FOLLOWS the cheek when the dormer moves, deform-to-follow, P4.5's own
  mechanism), the R3b dash, the gap review, the exports.
* **Editable only from the dormer:** a drag on a dormer wall is refused with
  a status line naming the dormer and its layer; the wall dialog shows its
  geometry read-only; it carries NO openings of its own — the face's are the
  dormer's (0294), and a cheek window is named, not ordered. Split, delete,
  type change: refused the same way.
* **In 3D nothing new:** it is exterior material on L2; under P1 it climbs
  into the dormer by absolute height; the generated cheek and face yield to
  it (`_on_a_wall`, already); the dormer's face openings are cut into it
  (0294 §3). Receipt: with the three walls minted, that dormer's generated
  cheek/face triangles → **0**, and the L2 wall pieces under it climb.
* **Plan:** drawn as a wall (the `EXTERIOR_T` band 0288 already paints for
  the dormer's walls), with a CATEGORICAL mark for its kind — ruled at
  implementation, not here, but not colour or weight alone (WA 2026‑08‑12).
  On L2 active the dormer's walls are solid; on L1 active they are the
  ghost the lower quadrants of his diagram show stepping around the dormer
  — 0295 §2's reading (a) is therefore not separate paint: it is these
  walls, drawn by the ordinary floor display rules, with the L1 wall ghost
  left as it is. Nothing is clipped.

**Undo.** A dormer edit now writes to another floor's walls and, through
welds, to hand-drawn walls and room outlines. State plainly what the
command stack covers before P4 opens; a half-undo (the wall reverts, the
dormer does not) is row 44's resurrected-wall shape. If the stack cannot
hold the whole gesture, the gesture refuses undo and says so.

## 3. RECEIPTS, on `little-dormer-test.json` after P3 (both modalities)

Dormer on L1, L2 present: tick the three boxes → three `walls` records on
L2, `type: dormer`, each `bound_to` naming `rf2`; a room drawn on L2
against face + cheeks + one hand-drawn knee wall closes (`check(deep=True)`
clean, area the expected rectangle); drag control C left 12″ ON L1 → the
left cheek's two vertices on L2 move 12″, the welded knee wall's end
follows, the room outline follows, and nothing else in `design_document()`
changes (set equality, both directions); save → reload → the walls are
still bound and still derived (0293 P3's round-trip, extended); a drag on
the cheek wall itself: refused, document byte-identical. Then promote the
dormer to L2: the walls do not move, the document differs in `rf2.level`
only, the 3D is byte-identical (0293 P3's receipt).

## 4. ORDER

Unchanged: P1 → P2 → P3 → P5 → P4, P4 now as §2. Check session B (0294 §5)
gains: tick the walls on, draw the room, drag C from L1 and watch L2.

**Carried:** 0293 §0 and §6; 0294 §5; 0295 §1's table.
