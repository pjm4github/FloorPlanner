# 0153 — report: R3b closed — the crash investigated, D85 found and fixed, PR #53 merged

**Patrick, 2026‑09‑03 through 2026‑09‑05, in chat, across three rounds.**

---

## 1. ROUND ONE — his check found a real crash

*"I dont see the dotted line. and it crashed :("* Investigated at length
(a synthetic multi-roof scene incl. one at 45°, a real ridge-tool sketch
through actual `QMouseEvent`s against a real bound room, the full
`wiscaway` corpus plan with a roof added, `scene.clear()`/`new_plan()`
called directly and through a live event loop, both offscreen and on a
real shown window, a wide sweep of degenerate roof/wall geometry) —
**the crash itself did not reproduce anywhere tried.** One real, narrower
gap found along the way: `roof_clip_spans` handed a `WallItem` reference
that outlived `scene.clear()`'s deletion returned silently WRONG spans
(plain-Python-backed attributes survive C++ deletion and do not raise)
instead of an honest empty answer. Fixed with a `sip.isdeleted()` guard,
the same established precaution `walls.py` already uses elsewhere for
this exact class of problem — named as insurance for the roof/room side
of the guard, since a direct test showed `scene.items()` already excludes
a `sip.delete()`d item synchronously in everything tried here.

Also asked about, in passing: a "little tiny roof" he couldn't delete —
too early to diagnose from a chat description alone, so filed as
[D85](../defects/0085-a-very-short-roof-ridge-is-hard-to-select.md), held.

## 2. ROUND TWO — a screenshot turned D85 into a real, fixed bug

Second report, with a screenshot of a thin vertical dashed roof and his
own diagnosis: *"I cant deleted it or select it. I think the dotted roof
edges need to be selectable so that I can select the roof."* His read was
exactly right. `RoofItem.rebuild()` built `self._path` (what `shape()`
strokes for hit-testing) from the ridge segment alone — `paint()` also
draws two dashed EAVE lines and, per gable end, a dashed GABLE line, and
none of that was ever part of the clickable region. A roof picked thin on
either axis (a short ridge alongside normal eave lines, or a small span
alongside a normal ridge) had most of what actually reads on screen
sitting outside the hit region entirely.

**Fix**: `self._path` now includes every segment `paint()` draws. 4 new
tests (`tests/test_roof_hit_testing.py`) — a thin-span roof selectable on
its eave line, a short-ridge roof selectable on its own eave line
(confirmed RED against the unfixed `rebuild()`, GREEN after), a gable-end
line selectable, and the full select-then-delete round trip.

## 3. ROUND THREE — his check passed, PR #53 merged

*"OK that works fine lets merge and commit that change to main."* Merged
[PR #53](https://github.com/pjm4github/FloorPlanner/pull/53) to `main` at
`d6ca9d6`, branch `roofs-r3b-clip-line` deleted (local and remote).
**R3b is done. D85 is CLOSED** on his own word.

Re-gated on the combined tree after the merge: full suite **1149 passed**,
7 deselected (`perf` lane), `ruff` clean, `python tools/gate.py` (full
mode) GREEN.

## 4. WHAT'S ACTUALLY IN R3B, FOR THE RECORD

`roofs.py` gains `roof_clip_spans(scene, wall)` — the sub-span(s) along a
wall where a roof on its own floor covers it below the room's own ceiling
height, exact interval arithmetic (every governing quantity is affine in
the wall's arc-length, so every true/false flip is a root, not a sampled
threshold) mirroring how an opening's own span already cuts a wall run.
`WallItem.paint()` draws the result as a dashed orange line. The ceiling
reference is per-wall, from whichever room borders it, the lower side
governing when two differ, `DEFAULT_ROOM_PROPS`'s own default when
neither side resolves to a room. Plus, from this session's two rounds of
his own check: the `sip.isdeleted` hardening and D85's hit-testing fix
above.

**R4 is the next available tranche (AMBER)** — the roof parameters
dialog (heights/pitch, overhang, gable↔hip per end; owns held items 3/4:
draggable eaves/gable ends), per [`0139-ruling.md`](0139-ruling.md) §3 /
[`0145-ruling.md`](0145-ruling.md) §4's order: R2b → R2c → R3 → R3b →
**R4** → R5.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items;
ridge/eaves horizontal repositioning (owned by R4).
