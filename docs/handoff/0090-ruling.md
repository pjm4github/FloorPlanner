# 0090 — ruling: PR #35 PASSED — all three merge, and the AMBER queue is empty

**Patrick, 2026‑08‑23, on `wall-label-fixes` at `c908cad`:** *"wall-label-fixes
is working too. I am back to the main branch."*

**Three checks, three passes, one session.** `HEAD` is on `main`, tree clean.

---

## 1. MERGE, IN THIS ORDER

| | branch | PR |
|---|---|---|
| 1 | `t-junction-grid-snap` | #36 |
| 2 | `cross-floor-align-fix` | #34 |
| 3 | `wall-label-fixes` | #35 |

**For each: bring the current `main` in, re-gate the combined tree, merge on
green CI, delete the branch local and remote.** Sequential, not parallel — each
one's re-gate must see the previous merge. [`0050`](0050-ruling.md) §3.

**`0088`/`0089`/this file land on `main` first**, doc-only, before any merge —
the mailbox gate from [`0084`](0084-ruling.md) §4 now enforces it anyway.

## 2. THE QUEUE THAT WAS THE BOTTLENECK IS EMPTY

[`0072`](0072-ruling.md) §7 said `ROADMAP.md`'s opening — *"the bottleneck has
never been review, it is unruled questions"* — had stopped being true, and that
what was queued was **Patrick's eyes, four deep, on one person.**

> **All three discharged today. Nothing is now waiting on a human check.** The
> line in `ROADMAP.md` is true again, and the snapshot should say so rather than
> leaving the old framing to be read next session.

## 3. TWO CARRIED ITEMS, ONE NOW CLOSED

**[`0081`](0081-report.md) §1 item 4 — *"is the status-bar label what you asked
for?"* — is ANSWERED.** Patrick has now selected walls in that label twice, on
two branches, and reported it working. **Recorded as passed on that basis; one
line from him retires it if I have read it too generously.**

**[`0068`](0068-ruling.md) §4 is STILL OPEN and is not a check** — it is a design
choice only he can make:

> **Off-axis walls: does the bar show the heading (`89.9990deg`), or how far off
> axis the wall is (`0.0010deg`)?** The second can never round to a lie; the
> first can, below `0.00005°`.

**Not blocking anything.** Named so it does not quietly become the oldest thing
on the board.

## 4. WHAT CODE DOES AFTER THE MERGES

**[`0084`](0084-ruling.md) §6, unchanged**, now unblocked at the top:

1. **§1 — restore `T = 1/16″` as the repair's candidacy filter** (AMBER)
2. **§2 — the orthogonality post-condition: no wall's deviation may increase**
   (AMBER, same commit)
3. **§3 — re-run the repair census under `T`**; per-wall rollback only if the
   whole-file rollback still fires (GREEN to measure)

**Then PR #37 becomes worth checking**, and it is the only AMBER item left.

**[`0085`](0085-ruling.md)'s `CLAUDE.md` trim is GREEN and unblocked** — good
work to interleave, and it directly reduces the context pressure that stopped a
session yesterday.

## 5. TIER

**GREEN** — three AMBER conditions discharged; merging is what the tier table
already authorises once the check passes.
