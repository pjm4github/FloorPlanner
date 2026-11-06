# 0302 — report: P3 of the 1½-storey arc — the dormer's level, datum, dialog and the four views

**Code, 2026‑11‑05.** The record ([`0197-ruling.md`](0197-ruling.md) §7). P3 of
the arc ([`0297`](0297-ruling.md) §2; [`0293`](0293-ruling.md) §5 P3; [`0295`](0295-ruling.md);
[`0296`](0296-ruling.md) §1). Built on branch `p3-dormer-level`, stacked on
`p2-dash-knee` (P2); AMBER, **not merged** — the merge of P1–P3 waits on his
**check session A** (0297 §3/§4). Next: nothing opens past P3 without that check.

## 1. WHAT LANDED

* **Datum (M1 closed).** `RoofEndOnDialog.level_base_in()` for a dormer is the
  HOST's level base (0293 §2c): a cross-level dormer no longer overstates its
  absolute heights by the storey elevation (measured 96″ → **0″**). The level
  note names both floors ("drawn on L2; pinned to the host on L1, its datum").
* **3D never reads a dormer's level (0293 §2c, the gap P1 left).** Two sites
  still did: the roof SECTION lifted by `base(lid)` and the cheek/face yield used
  `plan_walls.get(lid)`. Both now use the HOST's base / ALL levels' walls. So a
  **promotion is a byte-identical `build_model`** (the receipt, below).
* **Pinned to + Edited on level (0293 §5 P3 ii).** The dialog gains a "Pinned to"
  line (host level, pitch) and an "Edited on level" selector over the two legal
  levels that EXIST — the host's and the one above (`legal_dormer_levels`); OK
  promotes/demotes. The marker menu gains "Move to level ▸" (same levels, current
  ticked). Both disabled with a note on a one-layer plan (0296 §1).
  `levels.move_dormer_to_level` applies it: an edit of `level` alone, undoable.
* **Four views (0295 §1).** A dormer is now SHOWN on both legal levels —
  solid+editable on its own, **ghosted+not-editable on the other** — regardless
  of "show other floors" or rooms (`apply_roof_visibility`, `_roof_hittable`).
* **`dormer_defaults` (M3).** Seeds the cheek top from the DRAWN level's rooms,
  converted into the host datum (`(base_drawn − base_host) + ceiling + …`); the
  Dormer tool passes `active_floor()`.
* **Schema text (0293 §0).** `roof.host` now says "the dormer's own level OR the
  one directly below" (not "same level"); `roof.openings` sill/head are "above
  the HOST roof's level base" (not the dormer's); the "plan view does not draw
  them yet" line corrected to the Phase C shadow.
* **Macro (0293 §5 P3 vi).** The `DORMER` token carries geometry, NOT a level —
  the dormer is built on its host's floor, and the active floor at replay is the
  drawn level. A promotion records a new **`MOVEDORMER x y level`** token (v1 and
  `@MOVEDORMER` v2): replay finds the dormer whose face is nearest (x, y) and
  moves it. So the gesture replays.

## 2. RECEIPTS (little-dormer-test; promote `rf2` L1 → L2)

* **`build_model` BYTE-IDENTICAL** before and after the promotion —
  `docs/evidence/p3-dormer-level/byte_identity.py` (fingerprint `83b2a32877f85f9f`
  both ways). The document differs in `rf2.level` ALONE.
* **M1** `level_base_in`: dormer-on-L2 = 0.0 = the host's base (was 96.0).
* **Four views**, measured per quadrant (a file with no rooms): dormer on L1 —
  active L1 `visible, hittable`; active L2 `visible, NOT hittable`. The dormer-on-L2
  row mirrors it by the one rule (`legal_dormer_levels` is symmetric).

## 3. TESTS, AND THE ONE CHANGED ASSERTION (0297 §6)

`tests/test_p3_dormer_level.py`: the legal levels, promote/demote (+ illegal
refused), the host-datum `level_base_in`, the four-view visible/hittable sets,
and the byte-identical promotion. **CHANGED ASSERTION, named:**
`test_roof_dormer.py::test_a_dormer_marker_menu_names_the_dormer` — the marker
menu gains the "Move to level" submenu.

Full gate GREEN on the final tree (OFF+ON; 2027 passed). Would `check(deep=True)`
have fired? **No — a limit, not a gap** (0293 §1).

## 4. NEXT

**Check session A** (0293 §6 item 3): P1's climb, P2's dash + knee line, and P3's
dormer views, together, on the wiscaway file and `little-dormer-test`. Then the
merge of P1–P3. After that, **P5** (windows on the dormer face) then **P4** (the
dormer wall type). His files under `incoming/` stay his.
