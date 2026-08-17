# 0045 — ruling: the check was run against the wrong tree, and a check request must name its BRANCH

**Patrick, 2026‑08‑17:** *"I think when I check the shower components I do NOT
see any change. Are these changes on a different branch?"*

**Yes. Measured:**

```
                 main    branch    YOUR WORKING TREE
shower             1        2            1
walk_in_shower     2        3            2
glass_shower       0        2            0      <- 0 = the original all-strokes symbol
```

*(counts of closed filled shapes per symbol)*

**`HEAD` is `main`. The redraws are on `shower-identity-redraws` and have never
been on `main`.** `glass_shower` on your disk still has **zero** filled shapes —
it is the un-redrawn file, exactly as [`0030`](0030-ruling.md) measured it.

**And the after-render is not on `main` either:**

```
shower-glance-before.png    main: yes    branch: yes
shower-glance-after.png     main: NO     branch: yes
```

> **THE CHECK WAS NOT FAILED. IT WAS NEVER RUN** — the instrument had the before
> state loaded, and the "after" it was supposed to be compared against does not
> exist on the tree Patrick was looking at.

---

## 1. TO RUN IT

```
git checkout shower-identity-redraws
```

**Then RESTART the app.** `SESSION_SNAPSHOT` §6: *"a running app keeps the code
it imported — restart before re-testing."* **The artwork is read at runtime, so a
live session holds the old symbols even after the checkout.**

**Then [`0034`](0034-ruling.md) §2's two questions, unchanged.**

## 2. THIS IS THE THIRD SYMPTOM OF ONE ROOT CAUSE

| what was on a branch while `main` was checked out | found at |
|---|---|
| `0033`, `0034`, `0035`, `0036-report` — the mailbox | [`0040`](0040-ruling.md) §4 |
| the three redrawn symbols | here |
| `shower-glance-after.png` — the check's own evidence | here |

**[`0040`](0040-ruling.md) §4 fixed the mailbox half by ruling that records live
on `main`. It did not go far enough.**

> ### EVERYTHING A CHECK NEEDS CAN LIVE ON A BRANCH THE CHECKER IS NOT STANDING ON, AND NOTHING SAYS SO.
>
> The work **should** be on a branch — that is what AMBER is for. **The failure
> is that the check request never named it**, so the only unstated variable was
> the one that mattered.

## 3. THE RULE — a check request names its BRANCH, and this is the third clause

**The standing check-request rule has now been learned three times, each from a
check that could not be run:**

| clause | earned at | the check that failed |
|---|---|---|
| **name the PLAN, and list its items** | [`0016`](0016-ruling.md) §6 | *"the boat trailer is chunky"* — on a scene containing no boat trailer |
| **name the CAMERA, and it must be working distance** | [`0034`](0034-ruling.md) §2 | the marks judged at a 29-foot framing |
| **name the BRANCH** | **here** | the before state judged as if it were the after |

> **THE THREE TOGETHER ARE THE INSTRUMENT'S SETUP**, and each was discovered the
> same way: **a verdict that turned out to be about something other than the
> thing under test.** A check request that omits any of them is asking for a
> reading without saying where the instrument is pointed.

**And the reciprocal, from [`0020`](0020-ruling.md) §4: a check RESULT names them
too** — *"no change"* against an unnamed branch is what sent this one round the
loop.

## 4. WHAT DOES NOT CHANGE

**[`0030`](0030-ruling.md)'s baseline still stands** and is still the fail-first
half of the pair: it was taken on `main`'s artwork, which is the same artwork the
branch changes. **The comparison is still valid, and `shower-glance-before.png`
exists on both.**

**[`0044`](0044-ruling.md) §3's order is unchanged.** The cherry-pick of the four
mailbox files is still owed and still does not require this branch to merge.

## 5. TIER

**None — this is a correction to how the check is run, not a change to anything.**
The redraws remain **AMBER** and unmerged, and the merge condition is still
[`0034`](0034-ruling.md) §2's two questions, now asked on the tree that has the
work on it.
