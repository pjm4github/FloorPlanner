# 0154 — ruling: R4 re-planned around Patrick's five requirements — the footprint enters the schema

**Patrick, 2026‑09‑06:** (1) modify the eaves overhang; (2) roofs and ALL
their properties saved in the JSON; (3) a solid roof schema; (4) drag all 4
edges and the ridge by clicking the roof; (5) assign the roof's bottom —
where the eaves start — to the top of the rooms it covers. *"These must all
be properly captured in the schema."*

---

## 1. THE MEASURED GAP HIS INSTINCT FOUND

**A roof's footprint is not in the document.** `roofs.py:75`, its own
comment: *"`RoofItem.span_in` is NOT part of the persisted `Roof`"* — the
lateral extent is recomputed on every load from the nearest parallel wall.
So a saved roof can silently change shape when walls move, and a document
alone (fp3d, exports) does not fully determine the roof. Requirements (2)
and (3) land exactly here; (4) is impossible until the dragged geometry has
somewhere to live. **The schema, not the scene, becomes the footprint's
source of truth.**

## 2. THE SCHEMA — additive over v6, one materializing migration

* **`span_in: [left, right]`** — perpendicular distance, ridge → the
  eaves-START line on each side (the plane where `eaves_h_in` applies).
  Per-side, so the ridge need not be centered. Migration: on first load of
  an existing roof, materialize both sides from today's live computation —
  identical geometry, now owned by the document.
* **`overhang_in: [left, right]`** — beyond the eaves-start line, per side
  (migrates from the existing scalar, same value both sides).
* **`eaves_bind: "manual" | "room_top"`** (default `"manual"`) — (5). With
  `room_top`, `eaves_h_in` is recomputed from the wall-top (level
  `elevation_in + height_in` / the rooms' own ceiling) of the rooms the
  footprint covers, **and the recomputed value is still written to
  `eaves_h_in` on save** — documents stay self-contained; exports and fp3d
  never re-derive. Rooms of differing heights under one roof: **the highest
  governs, and the mismatch is warned, not hidden** (one line from Patrick
  overrides this default).
* Consequence, named: per-side spans with one ridge height ⇒ **per-side
  pitch is now legal** (saltbox) — the End-On drawing shows both slopes
  when they differ. [`0139`](0139-ruling.md)'s symmetric-gable v1
  assumption retires here, on schedule.
* `roof_clip_spans` and the 3D builder re-point at the stored fields —
  after R4a nothing reads a live-recomputed span.

## 3. THE TRANCHES — R4 splits in three, gated one at a time

| # | tranche | tier | check |
|---|---|---|---|
| R4a | schema + migration + round-trip; **receipt: a re-saved wiscaway roof renders pixel/number-identical before vs after** (materialization changes ownership, not geometry) | **GREEN** | CI |
| R4b | parameters dialog: per-side overhang (1), heights/pitch via the End-On machinery, gable↔hip per end, the `room_top` binding toggle (5) | AMBER | set an overhang, bind eaves to room top, change the room height, watch the roof follow |
| R4c | direct manipulation (4): selected roof grows **five grips — two eave edges, two gable ends, the ridge**. Eave-edge drag edits that side's `span_in` (overhang rides along); gable-end drag moves that ridge endpoint; **ridge drag slides it laterally between fixed eave edges**, rebalancing the two spans — the [`0140`](0140-ruling.md) §4 deferral comes due. All undoable; **drags land ON the grid, never move by it** ([`0070`](0070-ruling.md) §3's class, named so it is tested, not remembered) | AMBER | drag all five on the main roof and the 45° wing |

Order: R4a → R4b → R4c → R5 (dormers, own ruling). Requirement (2) is
discharged by R4a's receipts; nothing else about persistence is owed after
it.

**Carried:** D83/D84 (held); room-label rounding ([`0131`](0131-ruling.md)
§2); delta-snap sites; D61-family; yard items.
