# 0070 — ruling: the code snaps the MOVE, not the DESTINATION — Patrick's off-grid walls

**On [`0069-report.md`](0069-report.md) (accepted, §1) and on Patrick's own
off-grid report, which is the rest of this file.**

**I could not run the macro** — the bridge this review runs over has no PyQt6,
so `fp_macro.py` will not start here. **Everything below is read from the intake
file and from source. There is no reproduction on my side, and §5 is written
accordingly.**

---

## 1. `0069` — ACCEPTED, AND THE DIFFERENTIAL IS REAL THIS TIME

All four GREEN items done. **§1 is the part that matters:** the format was
reverted to `.1f` locally, the new round-trip test confirmed RED, the format
restored, confirmed GREEN. **That is two runs of one predicate against two
states of the code** — [`0063`](0063-ruling.md) §1's standard, which
[`0067`](0067-report.md) §3 claimed and did not have. **And the test magnitude is
now derived in the test against `.4f`'s own floor rather than borrowed from a
ruling** — [`0068`](0068-ruling.md) §3's rule applied on its first use. Nothing
owed. PR #35 stays AMBER.

## 2. WHAT THE INTAKE FILE MEASURES — snap step 6″, and only `y` is wrong

`fixtures/incoming/w7offsetFloorplan.json`, `settings.wall_snap_in = 6.0`:

| | |
|---|---|
| vertices off the 6″ grid | **5 of 10** — `v2 v4 v5 v7 v8` |
| **every `x`** | 60, 108, 204, 300 — **all exactly on grid** |
| distinct off-grid `y` values | **exactly two**: `347.5515` (`v4`,`v7`), `389.0628` (`v2`,`v5`,`v8`) |
| displacement from the nearest grid line | **−0.4485″** and **−0.9372″** — both negative, neither a multiple of anything |
| **every one of the 12 walls** | **exactly axis-aligned** — each pair shares `x` or `y` to the last bit |

**W7 is `v5 → v8`, `y = 389.0628″ = 32.4219 ft` — Patrick's "x.4 feet", exactly.**

> **Two facts do most of the work.** **(a)** Two values, five vertices — this is
> **one bad number propagated by welding, twice**, not per-vertex jitter.
> **(b)** Every wall is perfectly orthogonal. **This is NOT
> [`0055`](0055-ruling.md)'s drift fault** — that one tilts walls and leaves
> them near the grid; this one keeps them perfectly straight and puts them
> between grid lines. **Separate faults. I am not merging the threads**, which
> is the error [`0059`](0059-ruling.md) §4 made and [`0061`](0061-ruling.md) §1
> had to withdraw.

**AND THE TARGETS WERE ALREADY ON THE GRID.** Reading `w7offgrid.fpm` against
[`macro_language.md`](../macro_language.md): the two operations that produced
the bad values aimed at `y = 348` (line 11's `CLICK 203 348`, and `348 / 6 = 58`)
and `y = 390` (line 10's `DRAG 144 390`, `390 / 6 = 65`). **Both are exact grid
lines. No rounding was required, and the result is off by a fraction of an inch
anyway.** Whatever this is, it is **not a failure to round**.

## 3. THE MECHANISM — READ FROM SOURCE, AND THE CORRECT FORM IS THREE LINES AWAY FROM THE WRONG ONE

`WallItem.mouseMoveEvent`, the body-slide — **both branches, side by side:**

```python
if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
    np1 = wall_snap(QPointF(self._o1.x() + delta.x(),      # <- DESTINATION
                            self._o1.y() + delta.y()))
    dx, dy = np1.x() - self._o1.x(), np1.y() - self._o1.y()
else:
    s = wall_snap_len(delta.x() * nx_ + delta.y() * ny_)   # <- DISPLACEMENT
    dx, dy = nx_ * s, ny_ * s
```

> ### THE DEFAULT PATH SNAPS HOW FAR THE WALL MOVES. THE Ctrl PATH SNAPS WHERE IT LANDS. ONLY THE SECOND ONE PUTS A WALL ON THE GRID.
>
> **A displacement-snap preserves any existing offset exactly, forever, and can
> never remove one.** Slide a wall sitting at `359.0628` by a snapped `+30` and
> it arrives at `389.0628` — the observed value, to the digit.

**And it is not one site. Measured, every snap on the wall-drawing path:**

| site | what it snaps | lands on grid? |
|---|---|---|
| `view.py:230` `_snap_start` | returns a neighbour's endpoint/body point **verbatim**; `wall_snap` is only the `else` | **only if nothing is within tolerance** |
| `view.py:267` `_wall_end_point` | `wall_snap_len` — the **length from `p1`** | **only if `p1` is on grid** |
| `view.py:255` `_align_to_wall` | overwrites the free coordinate with **a neighbour's coordinate** | **only if that neighbour is** |
| `walls.py:2288` move, **Ctrl** | `wall_snap(origin + delta)` | **always ✅** |
| `walls.py:2294` move, **default** | `wall_snap_len(perpendicular)` | **only if it started on grid** |

**`nearest_wall_endpoint` returns `QPointF(q)` — the other wall's corner, byte
for byte. Nothing on that path ever reaches `wall_snap`.**

> ### THE INVARIANT THE CODE IMPLEMENTS IS *"MOVE BY A MULTIPLE OF THE GRID."* THE INVARIANT PATRICK EXPECTS IS *"LAND ON THE GRID."*
>
> **They agree only while every vertex already sits on the grid.** One unsnapped
> seed — a start point taken from a neighbour, a free coordinate taken from
> [`0061`](0061-ruling.md)'s own `_align_to_wall`, a weld copying a corner — and
> **every later operation carries the offset perfectly and nothing in the
> application can ever remove it.** That is why two values, why five vertices,
> why perfectly orthogonal, and why "sometimes".

**AND THIS IS [`0055`](0055-ruling.md) §4'S UNANSWERED CLAUSE, ANSWERED BY A
REPRODUCTION.** It asked: *"does snapping cover an operation's OUTPUT, or only
cursor input?"* **Measured answer: neither. It covers the DELTA** — which is not
one of the two options the clause offered, and is worse than both. **This
belongs in A6's read-back as its central fact, not beside it.**

## 4. WHAT I HAVE NOT ESTABLISHED — said plainly, because §3 reads like a solve

**`347.5515` sits on `w9`, and this macro never body-moves it.** The
`mouseMoveEvent` finding therefore **cannot be the whole cause**, and I have no
reproduction with which to say which site seeded either value.

> **Two of the five sites are enough to explain the file, and I cannot tell you
> which two.** The first plausible mechanism is not the finding —
> [`0035`](0035-ruling.md) §2 and [`0061`](0061-ruling.md) §2 both turned on
> exactly that distinction. **Do not let §3 close the investigation.**

## 5. WHAT CODE DOES — the bisect first, and it costs one loop

**1 — NAME THE FIRST BAD STEP. GREEN, measurement only, and it goes first.**
Replay `w7offgrid.fpm` **one line at a time** (`fp_macro.py --repl`, or 14
cumulative prefixes), dumping every vertex after each step, and **report the
first line at which any coordinate leaves the 6″ grid, with the value before and
after.** Fourteen steps turns a five-site hypothesis into one operation.

**2 — THE A/B, same run, free.** Replay with `auto_weld` and `auto_coalesce`
off. **If the vertices land on grid, the seed is in the normalisation, not the
draw.** If they still drift, it is the draw path. Either answer halves the
remaining space.

**3 — THE FAIL-FIRST RECEIPT.** The macro **is** the reproduction, so the test
replays it and asserts **every vertex is congruent to zero mod
`wall_snap_in`** — RED today, GREEN after. **Scope it to geometry this plan
creates, not to loaded documents:** the corpus is full of legitimately off-grid
history and the invariant is about what the application *produces*.
**[`0061`](0061-ruling.md) §3's caveat carries:** if a reduced synthetic scene
does not reproduce, **that is a finding — say so and use the macro.**

**4 — FIX THE SITE THE BISECT NAMES. ONE SITE.** Not all five.
[`0062`](0062-report.md) §3 refused to change sites with no receipt behind them
and [`0063`](0063-ruling.md) §2 sustained it. **Same rule here, and it is not
negotiable just because I have now listed the other four.** They are named, not
ordered.

**5 — FILE THE RECORD.** **D80**, citing the fixture, the macro, and §3's table.
This is Patrick's second reproduced report in the thread and it must not live
only in a handoff.

**Not ordered, named once:** `grid_snap`'s default step is `SNAP_STEP = 1.0`,
and `items.py:71` / `items.py:478` call it **with the default**, not
`wall_snap_in`. **A second grid, 6× finer, on a path nobody has enumerated.**
Worth a look during the census; not part of this fix.

## 6. THE INTAKE EXIT

The two files are tracked (`cad8fdb`) and the clock started at
[`0069`](0069-report.md) §6. **Their exit is now decided in advance:
`w7offgrid.fpm` and `w7offsetFloorplan.json` are PROMOTED to `fixtures/` under
exit 1 — with the fail-first test of §5 item 3 naming them.** No second
handoff of drift, and no fourth-exit argument needed: this pair **is** a test
input.

## 7. TIER AND ORDER

| | | |
|---|---|---|
| 1 | **§5 items 1–2 — the bisect and the A/B** | **GREEN.** Measurement only. Report the step, do not fix in the same breath |
| 2 | **§5 item 3 — the fail-first test** | **GREEN.** Must be RED before anything is changed |
| 3 | **§5 item 4 — the one fix** | **AMBER** — it changes what a gesture produces. **Batch the check with #34/#35** |
| 4 | **§5 item 5 / §6 — D80 and the promotion** | **GREEN** |
| 5 | **PR #34, PR #35** | **AMBER, unchanged, still waiting on Patrick** |

**PATRICK'S CHECK, when the fix exists — one question, batched with the other
three and `0068` §4's:**

> **"With snap set to 6″, draw and then slide an interior wall inside an
> existing room. Does every corner land on a 6″ line?"**

## 8. ITEM C, AND I AM DONE PROMISING AN ORDER

**`0066` is still reserved and still unwritten.** Twice now I have named the next
ruling and been overtaken — first by Patrick saying *"0067 is up"*, now by a
live reproduced defect from him. **Both times his instruction outranked mine,
correctly, and `ca3c6b7` says so in the tree.**

> **The commitment is the wrong instrument.** A reviewer who cannot control the
> queue should not keep announcing it — that is three handoffs of a promise
> doing the work a schedule cannot. **So: no date, no "next".** Item C is
> **RED and owed**, it is on Patrick's side of nothing and mine alone, and the
> only thing that will close it is writing it. **Ask me for `0066` and it gets
> written before anything else in that turn.**
