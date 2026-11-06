# 0304 — report: P5 of the 1½-storey arc — windows on the dormer face (plan item + 3D cut)

**Code, 2026‑11‑06.** The record ([`0197-ruling.md`](0197-ruling.md) §7). P5 of
the arc ([`0294`](0294-ruling.md); [`0297`](0297-ruling.md) §2 order
P1→P2→P3→**P5**→P4). Built on branch `p5-dormer-face-windows`, cut from `main`
(the P1–P3 merge, [`0303`](0303-report.md)); AMBER, **not merged** — it waits on
his **check session B** (0294 §5), which checks P5 then P4. Two commits: §3 (the
3D cut) then §2 (the plan item).

## 1. §3 — THE 3D CUT INTO THE CLIMBING WALL

Before P5 a dormer's `openings` cut only the GENERATED face; where a house wall
stands on the face line the face yields (`_on_a_wall`) and generates nothing, so
a gable-end window over a wall was a no-op — 0292 measured a **0-triangle** change
and his gable-end windows never rendered (0292 §2).

`_dormer_face` now records the opening bands where it yields to a climbing wall
(plan segment + band, heights absolute). The wall loop projects each onto that
wall's own `u` and cuts it as a **climb-band void**: the head is NOT clamped to
the wall top, and the header climbs to the dormer surface. The header's nominal
top is carried far above any surface (`_CLIMB_TOP_IN`) so a cell OUTSIDE the climb
— the host's own territory, under a wall parallel to the host ridge — yields
EMPTY, not an inverted box over the void. The under-sill is unchanged
(`to_top=False` already caps at `min(surface, sill)`).

Receipts (`tests/test_p5_dormer_face_windows.py`, a constructed wall-on-face
fixture): the dormer face window is a VOID by ray test (0292's 0 is the fail-
first), the gable stays solid below the sill and above the head. A SET-BACK dormer
(generated face) and an ordinary wall window build **byte-identically** — the
record fires only on a wall yield.

## 2. §2 — THE PLAN-VIEW DORMER WINDOW ITEM (THE SECOND ROW)

Each dormer face window is now a hit-testable `DormerWindowItem` — a Qt child of
its `RoofItem` (like the grips/marker), reconciled with `openings` by
`RoofItem.sync_windows` (called from `rebuild`, so the End-On dialog's `apply`
refreshes them). It draws a band PARALLEL to the face, offset to the UP-SLOPE
side (into the dormer) by half the face wall's thickness plus a fixed screen
gutter, so it never lies on the house wall's own storey window below; two short
ties say "this face"; its mark is CATEGORICAL — a dashed blue outline with a small
gable triangle at its centre. The stack reads as two rows: the storey window on
the wall, the dormer window just inside the face. The old read-only blue band in
`RoofItem.paint` is retired (the item replaces it).

Editing: drag ALONG the face → the anchor offset, snapped on the grid, never
across (`wall_snap_len`, the standing rule); double-click → the End-On dialog with
THAT window selected in its list (`open_end_on_dialog(select_opening=…)`); right-
click → edit / duplicate / delete; Delete removes the opening. Width, sill, head
and kind stay the dialog's. Drawn and hittable only while the dormer's level is
active and roofs are editable (`_roof_hittable`); ghosted with the dormer
otherwise. Tests: `tests/test_p5_dormer_window_item.py` (sync, the up-slope
offset, level-gated hittability, delete, duplicate).

## 3. GATE

Full mode, GREEN. The 7 deselected are the perf lane (standing P3.8 flap-class
ruling).

## 4. NEXT

His **check session B** (0294 §5), on `little-dormer-test.json` (now TWO dormers,
his edit): the two rows on the L1 plan, drag the dormer band along the face, open
the dialog from it, both windows in 3D. On his word, land P5; then **P4** — the
`dormer` wall type (0296). The elevation view's per-window parameters keep growing
(0294 §4), each his to order. Named, not ordered: his backlog (0248's items 8–9).
