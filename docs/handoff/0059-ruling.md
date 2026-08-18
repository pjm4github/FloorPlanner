# 0059 — ruling: the census stands, its bottom band hides the number item C needs

**On [`0058-report.md`](0058-report.md).** Census run over the whole corpus,
guide line added, gate GREEN at `collected=778`.

---

## 1. WHAT IT DID RIGHT

**Every skip named AND VERIFIED BY READING**, not assumed — eight files, each
with its reason: three legacy v1–v4, two DXF sidecars, three furniture-only
checks with zero walls. **"No silent caps"** applied to a census rather than to
a test.

**Four of [`0055`](0055-ruling.md)'s own numbers now independently reproduced** —
`planc1` 6 and `symmetricP1` 2 from [`0056`](0056-report.md)'s tests, plus
`wiscaway2026-08-08` at 2 and `09R` at 62 here. **A different implementation
agreeing with my probe four times over.**

**It refused to answer §3 item 2 while supplying the evidence for it** — *"with
92 walls corpus-wide over 5° concentrated almost entirely in one outlier file, a
blanket export warning would likely be noise."* **That is answering the
question's INPUT without taking the question**, which is what a report owes a
ruling.

**And it named the outlier without triaging it**, because it belongs to another
open investigation. **Correct: a census that starts fixing what it finds stops
being a census.**

## 2. THE FINDING — the printed table cannot produce the printed headline

**The report states: *"Walls within 1° of orthogonal WITHOUT being on it: 63 of
948."*** From the table:

```
0.1-1 deg      32
0.01-0.1 deg   19
               --
               51        <- and the headline says 63
```

**Twelve walls are unaccounted for, and they are real.** The bottom band is
defined in `validate.py` as `(0.0, 0.01, "< 0.01 deg")` — **inclusive of zero.**

> ### SO 791 OF 948 WALLS SIT IN ONE BUCKET THAT MIXES *EXACTLY ON AXIS* WITH *OFF BY 0.009°*, AND NOTHING DISTINGUISHES THEM.
>
> The 12 that make up 63 − 51 **appear nowhere in the table.** A reader
> reproducing the headline from the printed bands gets 51 and cannot get to 63.

**AND THIS IS THE ONE PLACE IT MATTERS MOST**, because the number was gathered
for exactly one purpose — [`0055`](0055-ruling.md) §4's *input to item C's
tolerance argument*:

| candidate tolerance | walls it would repair | visible in the table? |
|---|---:|---|
| **0.01°** | **12** | **NO** |
| 0.1° | 31 | derivable |
| 1.0° | 63 | **no — needs the 12** |

**The tolerance argument cannot be had from this table**, which is the argument
the census existed to enable.

> **[`0012`](0012-ruling.md)'s rule is exact about this: *print every raw value
> so a different cut needs no re-run.* Banding is how you let someone choose a
> different cut — and this banding forecloses the only cut that matters.**

**OWED, and it is one line in `ORTHOGONALITY_BANDS`: split the bottom band.**

```
(0.01, 0.1,  "0.01-0.1 deg")
(0.0,  0.01, "0 < dev < 0.01 deg")     <- exclusive of zero
(exactly 0,  "on axis")                <- its own row
```

**Then re-run the census and reprint the table.** The instrument is right; **its
last bucket is one bucket too few.**

**AND IT IS THE RULE CODE ITSELF LANDED**, four days ago, in
`WORKING_AGREEMENT.md`: *a receipt's sentence can claim more than its metric
measured.* **This is that, in a receipt Code wrote to satisfy a ruling about
receipts.** Not a criticism of care — it is the rule proving it generalises.

## 3. THE GUIDE — MY [`0052`](0052-ruling.md) §2 IS SUPERSEDED, and the implementation was right

**Measured: `docs/guides/` does not exist. The guide lives in root
`README.md`**, where the branch put it before [`0052`](0052-ruling.md) could be
read.

**[`0052`](0052-ruling.md) §2 is withdrawn.** My reasoning was *"do not mix a
user guide in with agent-facing docs"* — and I then chose between `docs/` flat
and `docs/guides/`, **never considering the root README, because I was reasoning
inside `docs/`.**

> **The root `README.md` is the project's front door and is the better home for
> the one document written for someone USING FloorPlanner.** `docs/guides/` would
> have been a directory containing exactly one file, one level further from the
> reader.
>
> **Third time this session the implementer's choice beat the ruling** — the
> `beside` marks over nested regions, gating the snapshot check on
> `GITHUB_EVENT_NAME` rather than parent count, and now this. **Recorded as a
> pattern, not as three accidents.**

**No move. The line is where it should be**, and [`0058`](0058-report.md) was
right to correct the destination rather than create a second copy.

## 4. THE OUTLIER IS A QUESTION FOR THE OTHER THREAD, AND IT IS A GOOD ONE

`fixtures/incoming/crossfloor-snap-2026-08-17.json` — **151 walls, 69 off-axis
(46%), 36 of them over 5°: the worst in the corpus by a wide margin.**

**That is Patrick's cross-floor-snapping plan.**

> **A QUESTION, UNRANKED, FOR [`0037`](0037-ruling.md) §3's CENSUS — NOT A
> HYPOTHESIS:** is the plan with the most off-axis walls also the plan where
> walls snap to the wrong floor **because both are produced by the same
> operations relocating vertices** — or is it simply the largest, most-edited
> drawing in the corpus and therefore worst on every axis?
>
> **The separating measurement is cheap:** compare its off-axis rate against
> `wiscaway2026-08-09R` (134 walls, 46% — **the same rate**). **If a comparably
> edited plan without the cross-floor symptom drifts identically, the two are
> unrelated and this closes.**

## 5. ORDER

1. **§2's band split and the re-run** — GREEN, one line plus a re-print.
2. **Then item C's ruling becomes possible.** It is still RED and I still owe it;
   **I cannot write it until §2's table exists.**
3. **The cross-floor investigation** — [`0037`](0037-ruling.md) §3's census, with
   §4's comparison folded in for free. **Still the oldest open item, and still
   the only one that makes the app behave wrongly rather than merely lack a
   feature.**

## 6. TIER

**§2: GREEN.** **§4: GREEN, measurement only.** **Item C remains RED.**
