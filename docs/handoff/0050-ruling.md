# 0050 — ruling: the redraw check PASSES; the branch is 9 behind and must not merge as-is

**Patrick's check on `shower-identity-redraws`, 2026‑08‑17. Quoted:**

> **I check the shower-identity-redraws and it looks good**

---

## 1. THE CHECK PASSES — [`0034`](0034-ruling.md) §2 question 1

**The three enclosures read as different things.** That closes the finding
[`0016`](0016-ruling.md) §2 opened on Friday and
[`0030`](0030-ruling.md) measured as failing — *"one box at three sizes"* — and
it closes it the way [`0033`](0033-report.md) predicted: **`beside` marks, not
nested regions**, because a region inherits D76's invisibility on a translucent
body.

**ONE THING STILL OPEN, and it is one word from Patrick.**
[`0034`](0034-ruling.md) §2 asked **two** questions, and the second was *is that
camera the distance you actually work at?*

> **If Patrick looked in the RUNNING APP — which [`0045`](0045-ruling.md) §1 told
> him to do — then question 2 is answered BY CONSTRUCTION**, because he was at
> his own working zoom. **If he looked at `shower-glance-after.png`, it is not.**
>
> **Say which, in the merge note.** It is the difference between a check at
> working distance and a check at a 29-foot framing, and the record should not
> have to guess.

## 2. BUT THE BRANCH IS 9 COMMITS BEHIND, AND THAT IS NOT WHAT WAS CHECKED

```
shower-identity-redraws:  2 ahead, 9 BEHIND main
```

**Since the branch was cut, `main` has gained:** the extrudability predicate and
its census (`17f6c01`), `floorplanner/export/fp2dxf.py`, the hook split and its
16 tests, the CI lane move, the mailbox cherry-pick, and the crossfloor fixture.

> ### PATRICK CHECKED THE BRANCH'S TREE. WHAT WOULD LAND ON `main` IS THE COMBINATION, AND NOBODY HAS SEEN THAT.
>
> **This is [`0042`](0042-ruling.md) §3's own argument turned on the merge:** *the
> merge ref is not an obstacle, it is the point — it tests what will actually
> land.* **A check on a 9-behind tree is a reading of something that will not
> exist after the merge.**

**AND THERE IS A NAMED COLLISION RISK, not a hypothetical one:** both sides
touched **`tests/test_extrudability.py`** and **`tests/test_viewer_model.py`**.
`main`'s predicate census asserts facts about the catalog; **the branch changes
three catalog symbols.** The predicate may now report differently on them —
possibly better, possibly red. **Unknown is the operative word.**

## 3. THE ORDER — update, re-gate, then merge

1. **Bring `main` into the branch** (merge or rebase — Code's call; a rebase of
   two commits is clean and this repository's history is merge-based, so state
   which was used).
2. **Full gate on the COMBINED tree.** Not `--quick` — this is a push, and the
   hook now enforces that distinction itself.
3. **Re-run the extrudability census** on the combined tree and **say what it
   reports for the three redrawn symbols.** `glass_shower` went from
   *predicate 1's only failure* to a filled body; **that is the census's own
   before/after and it costs one command.**
4. **If the combined tree changes the render, retake the after-shot.** If it does
   not — and it should not, since `main` gained no extruder change — **say so**,
   and Patrick's check carries without being re-run.
5. **PR, green CI, merge.**

**Only step 3 is new work.** The rest is the ordinary shape of landing a stale
branch.

## 4. WHAT MERGING CLOSES

* **The artwork item** from [`0016`](0016-ruling.md), open since 2026‑08‑15.
* **[`0030`](0030-ruling.md)'s fail-first pair** — its baseline was taken
  precisely so this merge could point at a receipt rather than an impression.
* **The last of the mailbox split** — `0033`/`0034`/`0035`/`0036-report` were
  cherry-picked to `main` already, so **the merge should find them identical and
  produce no conflict there.** If it does conflict, that is a finding.

## 5. WHAT IS NEXT, UNCHANGED

**[`0038`](0038-ruling.md)'s DXF integration is already under way** and is not
displaced by this. **After it:** [`0019`](0019-ruling.md)'s status board, then
**grid snap and its owed read-back** — the largest daily-use item left, and now
the oldest untouched thing on the board.

## 6. TIER

**The merge is AMBER and its condition is met**, subject to §1's one word and
§3's re-gate. **Nothing here requires a second check from Patrick** unless step 4
finds the render changed.
