# 0055 — ruling: grid snap will NOT fix the off-axis walls, and the measurement says why

**Patrick, 2026‑08‑18:** *"When I exported the DXF and then used the CAD-WALL
tool in CAX17 many of the walls were not on axis … I assume a snap to grid will
fix that."*

**The assumption is reasonable and the measurement refutes it.** Grid snap is
still worth building; **it is not the instrument for this fault.**

---

## 1. THE EXPORTER IS CLEAN — ruled out first

**The committed sample export: 74 LINE entities, ZERO off-axis.**

```
fixtures/chief-export/L1.dxf   47 LINEs,  0 not axis-aligned
fixtures/chief-export/L2.dxf   27 LINEs,  0 not axis-aligned
```

**So `fp2dxf` introduces no angular error.** Whatever Chief is flagging came out
of the document, not out of the converter. **That eliminates the hypothesis
worth eliminating first**, and it cost one measurement.

## 2. PATRICK'S OWN EXPORT — and there are TWO populations, not one

```
L1.dxf   494 lines   288 OFF-AXIS (58%)   worst 45.0000 deg
L2.dxf   134 lines    75 OFF-AXIS (56%)   worst  1.5032 deg
```

**Deviation bands:**

| band | L1 | L2 |
|---|---:|---:|
| **> 5°** — a real angle | **162** | **0** |
| 1–5° | 13 | 8 |
| 0.1–1° | 71 | 44 |
| 0.01–0.1° | 33 | 8 |
| **< 0.01°** — invisible | 9 | 15 |

> ### `L2` IS THE SEPARATOR, AND IT IS DECISIVE: 75 OFF-AXIS LINES AND NOT ONE OF THEM ABOVE 1.51°.
>
> **An entire floor where every off-axis wall is sub-2° drift.** No deliberate
> diagonals to confuse the reading. **56% of that floor is almost-but-not-quite
> straight**, and that is exactly the class that makes a CAD tool complain about
> walls which look perfectly straight to the person who drew them.

**So: `L1`'s 162 large angles may be architecture — a 45° bay, a diagonal wing —
and Chief is right to flag them. `L2`'s 75 are not architecture. They are
drift.**

## 3. THE DRIFT IS PRODUCED BY OPERATIONS, NOT BY DRAWING — and that is why snap cannot fix it

**Measured across two saves of the SAME drawing, one day apart:**

```
fixtures/wiscaway2026-08-08.json    103 walls,  2 off-axis  (45.0000, 18.4349 -- both deliberate)
fixtures/wiscaway2026-08-09R.json   134 walls, 62 off-axis
```

**And the part that settles it — of the 53 large-angle walls in the later file:**

| | |
|---|---|
| **27** | **NEW** — did not exist the day before |
| **26** | kept the same wall id … **and 24 of those were EXACTLY axis-aligned in the earlier file** |

> ### TWENTY-FOUR WALLS KEPT THEIR IDENTITY AND ROTATED FROM 0.0000° TO OVER 5°.
>
> **Nobody redrew those walls.** A wall that keeps its id and changes its angle
> was moved by an **operation**, not by a cursor.
>
> **GRID SNAP CONSTRAINS INPUT. THIS IS COMPUTED GEOMETRY.** Snapping where the
> mouse lands does nothing to a vertex that a move, join, weld or coalesce
> relocated.

**This is the same file pair that is already the field evidence for
[D61](../defects/0061-a-room-move-permanently-adds-two-walls.md)** — *walls
103 → 134, vertices 101 → 201* — **and it sits beside
[D63](../defects/0063-a-coalesced-outline-partly-rebounds-on-save.md),
[D64](../defects/0064-the-save-writes-an-outline-corner-at-a.md)** (*"the save
writes an outline corner at a recomputed coordinate, **and only on angled
geometry**"*) **and [D65](../defects/0065-weld-scene-is-implicated-in-three-separate.md).**
**All four are open, all four are geometry moving under operations, and this is
what that family looks like from the user's side, three weeks later, measured in
a CAD tool.**

## 4. THE RULING — grid snap is ONE of three things, and it is not the one that fixes this

| | what it does | fixes Patrick's export? |
|---|---|---|
| **A — grid snap** *(already ruled, read-back owed)* | constrains **new** drawing | **No.** Prevents future input error only |
| **B — an orthogonality REPORT** | names every wall within N° of axis but not on it | **No, but it makes the fault visible** — and it is nearly free |
| **C — an orthogonality REPAIR** | snaps near-axis walls onto axis | **Yes** — and it changes the document, so it needs its own ruling |

**BUILD B FIRST, AND IT IS THE CHEAPEST THING ON THIS PAGE.** The measurement in
§2 took one pass over the vertex table. **As a `check()` report or a menu item it
turns *"Chief complains about my walls"* into *"41 walls are within 1° of
orthogonal and 9 are within 0.01°"*** — a number the user can act on, and the
receipt for whether C ever worked.

> **AND B IS THE HONEST ORDER FOR ANOTHER REASON: nobody knows how many plans
> have this.** `planc1.v5.json` carries 6 walls at 0.0666°; `symmetricP1.json`
> carries 2. **The corpus has been quietly drifting and no instrument has ever
> looked.**

**C IS NOT AUTHORISED HERE.** *"Snap near-axis walls onto axis"* silently
rewrites a document, and **the tolerance is the whole design** — too tight and
it fixes nothing; too loose and it destroys the 45° bay in §2's `L1`. **It needs
its own ruling with the tolerance argued, and B's census is the input to that
argument.**

**A STAYS AS RULED, AND ITS READ-BACK NOW OWES ONE MORE CLAUSE:**

> **Does snapping apply to the OUTPUT of an operation — a move, join, weld,
> coalesce — or only to cursor input?** §3 says the drift comes from the first,
> and a snap feature that only covers the second will be reported as not working.

## 5. WHAT I AM NOT CLAIMING

**I have not shown that the 24 rotated walls are a defect rather than deliberate
edits.** Patrick moved rooms that day; some of those diagonals may be exactly
what he drew.

**The separating measurement, if it is wanted:** take `w19`, `w83`, `w109`,
`w113` — the exact-45° walls — and ask whether their geometry is consistent with
a deliberate diagonal or with a join artifact. **[D61](../defects/0061-a-room-move-permanently-adds-two-walls.md)
is the record that would own it.**

**`L2` does not depend on that question.** Its 75 sub-2° deviations are drift
under any reading.

## 6. TIER

**B — the orthogonality report: GREEN.** A report that fires only where something
is already off, adding nothing the user must learn.

**C — the repair: RED. No ruling exists and one is owed before it starts.**

**A — grid snap: unchanged**, read-back first, now with §4's extra clause.
