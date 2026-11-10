# 0307 — report: #1 the L2 attic knee line — the host roof's knee survives beside a dormer, built on a branch

**Code, 2026‑11‑09.** The record ([`0197-ruling.md`](0197-ruling.md) §7). His
standing item **#1** (the L2 knee line), unblocked when P4 closed the attic room
against the dormer walls ([`0305`](0305-report.md) §2, [`0306`](0306-report.md)
§1). Built on branch `l2-knee-under-dormer`, cut from `main` (c218b6e, the P4
merge, [`0306`](0306-report.md)); AMBER, **not merged** — awaiting his check in
the app.

## 1. HIS WORD, AND THE FAULT

2026‑11‑09, correcting a mis-framed question of mine (I had read a wide test
dormer as filling its room): **"the dormer is a smaller section than the
attic."** A dormer sits WITHIN the host roof, so the host's own knee — where the
main slope drops to the attic knee wall — runs BESIDE the dormer across the rest
of the room, while the dormer's own knee shows only across the narrower pop-up.

`room_ceiling_break_lines` (P2, [`0301`](0301-report.md)) draws a room's knee
where any roof's surface crosses the room's ceiling plane in absolute height,
gated per roof by that roof's clip region (`_clip_region`, R4d's drawn
territory). A dormer standing in the host SUBTRACTS its territory from the
host's region. The old gate tested ONE midpoint of each room-cut knee segment
against the region and kept or dropped the WHOLE segment — so a host knee that
ran clear across an attic was dropped entirely whenever its midpoint happened to
land in the dormer. The host knee then vanished across the whole attic (his
wiscaway L2: 14″ of a 123″ line survived).

## 2. THE FIX

One gate in `room_ceiling_break_lines`: CLIP each knee segment to the roof's
region (`ClipRegion.clip_segment`, Cyrus‑Beck — already the drawing and
hit-testing primitive) instead of the all-or-nothing midpoint test. The host
knee is kept where the host is the drawn roof and removed only where the dormer
actually stands; the dormer's own knee is unchanged; a roof with no region (a
lone roof, every unit fixture) is byte-identical. Painted as before by
`RoomItem.paint`; the memo still keys on each roof's `_clip_region`, so a drag or
recompose invalidates it.

## 3. RECEIPTS (instrument `docs/evidence/0307-l2-knee/receipts.py`)

His `wiscawayL2-fix.json` (L2 base 120, ceiling 216″ abs), host-knee length per
room, OLD → NEW (dormer-knee length alongside):

```
L2 attic (× 2):    host  14 → 109   dormer 245 → 216    the recovered host knee
L2 (dormer nook):  host 133 → 116   dormer 269 → 204    over-kept parts trimmed
L2 (no dormer):    host 187 → 187, 151 → 151, 229 → 229 unchanged
L1 (under dormers):host 790 → 691, 132 → 124,  73 →  88 same rule, any floor
```

The change is GENERAL — the knee function is floor-agnostic, so every room with
a dormer in its host roof is corrected the same way: the host knee is recovered
beside a dormer (14 → 109, 73 → 88) and trimmed to the host's region where it was
over-kept over another roof's territory (790 → 691). The L2 attic is the
motivating case he named.

`little-dormer-test.json` r3 is UNCHANGED (host 0, dormer 252): there the test
dormer `rf2`'s eaves sit on the room's own side walls (span 84 → eaves at
x 270/438 = the room edges), so it is as wide as that little room and leaves no
host slope — the degenerate case I first misread, not a counter-example.

## 4. TESTS

New `tests/test_roof_clip.py::test_the_host_knee_survives_beside_a_dormer` — a
room under a roof whose region is the room minus a central dormer strip; the host
knee reaches both sides of the strip and no segment crosses it. Proven to FAIL on
the old gate (empty — the whole segment dropped). The three existing knee tests
and the dormer-level knee test pass unchanged (their roofs carry no region).
Gate: full mode, GREEN.

## 5. NEXT

Awaiting his check — the host knee beside a dormer in the L2 attic, in the app;
on his word, merge. His other standing item **#3** (a dimensioned gable-end
window elevation) is separate; 0248's items 8–9 named, not ordered.
