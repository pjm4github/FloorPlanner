# 0088 — ruling: PR #36's check PASSED — D80 closes, merge authorised

**Patrick, 2026‑08‑23, on `t-junction-grid-snap` at `881c908`:**

> *"The result of t-junction-grid-snap is perfect. The walls snap exactly
> correct."*

**Checked in the running app, on the branch, against the procedure
[`0086`](0086-ruling.md) §2 names:** new plan, 6″ wall snap, a rectangular room,
an interior wall started **on an existing wall's body** (the T-junction that is
D80's own mechanism), then slid with the Select tool.

---

## 1. THE MERGE CONDITION IS MET

[`0070`](0070-ruling.md) §7 set it as one question — *"with snap set to 6″, draw
and then slide an interior wall inside an existing room, does every corner land
on a 6″ line?"* **Answered yes, by the only person who could answer it.**

**Merge authorised.** Bring `main` in first (the branch is **1 commit behind** —
`0087`'s own landing, doc-only), **re-gate on the combined tree**, then merge on
green CI. [`0050`](0050-ruling.md) §3's rule stands even when the gap is one doc
commit: **what merges is what gets gated.**

Delete the branch, local and remote, after the merge.

## 2. D80 CLOSES

[`0071`](0071-report.md) §5 held it open on exactly this condition — *"closes
once Patrick's manual check passes **and a ruling says so**, not before."*

**This ruling says so.** `docs/defects/0080-*.md` moves to closed, citing this
number, the branch tip `881c908`, and the merge commit. The record carries the
**fix, the receipt, and the human check** — which is what a closed record in this
project is supposed to mean.

## 3. WHAT THIS DOES NOT CLOSE

**[`0070`](0070-ruling.md) §3's other four sites are untouched and stay named,
not ordered** — `_snap_start`'s unfiltered branch is fixed; `_wall_end_point`'s
length-snap, `_align_to_wall`'s inherited coordinate, and the body-slide's
displacement-snap are not. **The invariant is still *"move by a multiple of the
grid"*, not *"land on the grid"*, everywhere except the one path D80 named.**

**One passed check is not a claim about the class.** [`0062`](0062-report.md) §3
and [`0063`](0063-ruling.md) §2's rule holds: no receipt, no change.

## 4. TIER

**Merge: GREEN** — the AMBER condition is discharged. **D80's closure: GREEN.**

**Checks 2 and 3 continue as [`0086`](0086-ruling.md) §2 orders** —
`cross-floor-align-fix` (#34) next, then `wall-label-fixes` (#35). Code stays
paused until Patrick reports both.
