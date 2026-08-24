# 0099 — ruling: the session id is not reproducible, and the check was aimed at a plan with nothing to repair

**Two screenshots of the same file, minutes apart, both labelled `Wall W19`:**

```
run 1   Wall W19: V28(97.50, 43.50)ft -> V30(97.50, 50.50)ft  len 7.00ft   (vertical)
run 2   Wall W19: V31(127.00, 55.00)ft -> V26(123.00, 55.00)ft len 4.00ft  (horizontal)
```

---

## 1. `WallItem.uid` IS NOT STABLE ACROSS SESSIONS — this is worse than [`0098`](0098-ruling.md) said

[`0098`](0098-ruling.md) §1 called it a second namespace. **It is also a
non-reproducible one.** `_WALL_UIDS = itertools.count(1)` mints on **first
read**, so the numbering follows whichever walls the user happens to select
first. **`W19` names a different wall in every session.**

> ### AN IDENTIFIER THAT CHANGES BETWEEN TWO RUNS OF THE SAME FILE CANNOT BE USED TO REPORT, DISCUSS, OR RE-FIND A WALL — WHICH IS EVERY REASON A USER READS ONE.
>
> [`0064`](0064-report.md) called it *"stable for the item's lifetime,
> session-local"*, and both halves are true. **The consequence was never
> stated: outside that one session it means nothing**, and it is printed in the
> same shape as the id that means something everywhere.

**[`0098`](0098-ruling.md) §2's fix — endpoints in feet on every named wall —
now covers the status bar too:** the bar already prints them, so **the
coordinates, not the id, are the thing that matches across surfaces.** Whether
the bar should print the document id instead is a real question and needs
[`0064`](0064-report.md)'s own reason answered (lifting the scene to a `Design`
to name one wall is the per-event rebuild P3.4 forbids). **Named, not ordered.**

## 2. THE CHECK WAS AIMED AT THE WRONG PLAN — measured

`wiscaway2026-08-08.json` has **zero walls the repair can touch.** Its two
off-axis walls are 45.00° and 18.43° — deliberate diagonals, three orders of
magnitude past `T`. **The repair would correctly offer to straighten nothing.**

**Every plan in the repo with repairable walls, measured:**

| plan | near-axis | repairable (`< 1/16″`) |
|---|---:|---:|
| `fixtures/crossfloor-snap-2026-08-17.json` | 37 | **16** |
| `fixtures/wiscaway2026-08-09R.json` | 8 | **5** |
| `examples/planc1.v5.json` / `planc1TestV5.json` | 6 | 5 |
| `examples/symmetricP1.json` | 2 | 1 |
| `examples/farmplaceBIGmultifloor.json` | 4 | 0 |
| **`fixtures/wiscaway2026-08-08.json`** | **0** | **0** |

**`wiscaway2026-08-09R` is the plan to check** — his own drawing one day later,
and [`0055`](0055-ruling.md) §3's own drift evidence. **`crossfloor-snap` second**,
because it is the file whose whole-document rollback
[`0083`](0083-report.md) §4 measured and [`0097`](0097-report.md) claims no
longer fires.

> **A check aimed at a plan with no candidates cannot fail, and cannot pass
> either.** [`0086`](0086-ruling.md) §2 named the branch and the question and
> **did not name the file.** Mine to fix: **every AMBER check request from here
> names the file it is run against.**

## 3. THE 104/103 DISCREPANCY — withdrawn pending confirmation

[`0098`](0098-ruling.md) §3 flagged the report's 104 against the fixture's 103.
**The title bar shows he opened
`C:/Users/pmora/OneDrive/Documents/FloorPlanner/wiscaway2026-08-08.json` — not
the repo copy.** Same name, different file, and I cannot read outside the
connected folder.

**Not a defect until the same file is counted twice.** [`0098`](0098-ruling.md)
§3 is withdrawn; if the counts still disagree on `fixtures/`'s own copy, it
returns.

## 4. TIER

**[`0098`](0098-ruling.md) §2 stays GREEN and stays ahead of the check.**
§1 adds nothing to build — it sharpens why. **§2's table is the check's missing
half and costs nothing.**
