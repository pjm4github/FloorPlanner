# 0113 — report: `0111`/`0112`'s close-out, then `0108`-`0110`'s three snap-to-grid features — all four PRs checked and merged

Answers `0111-ruling.md` (close out the three open PRs) and `0110-ruling.md`
§5 (build Snap to Grid Orthogonal, then plain Snap to Grid, then the
disabled 15° placeholder). Four PRs, four of Patrick's own checks, four
merges — full trail below.

---

## 1. `0111`/`0112`'s CLOSE-OUT — three branches, one check session, merged

Per `0111-ruling.md` §3's order: the in-flight `0107` work landed first
(`--docs` wired into the push hook, the CI matrix collapsed to one leg, DEEP
moved out of local full mode into CI-only — `0107-ruling.md`, built and
gated the same session), then `0112`'s `plans.pdf` gitignore, then all three
branches brought current with `main` and re-gated.

**The check session, in the order `0111` §4 specified, each returning to
`main` between:**

| PR | branch | check | result |
|---|---|---|---|
| #39 | `wall-report-id-fix` | `wiscaway2026-08-09R.json`, Wall orthogonality report — every row names a findable wall (`W7 · w19 …`), clicking a row selects + centres it | **passed** |
| #37 | `wall-orthogonality-repair` (item C) | same file, Repair wall orthogonality — 5 walls offered, largest correction 0.041″, applied, drawing still correct | **passed** |
| #38 | `wall-label-angle-clause` | a straight/Ctrl-snapped wall shows nothing; a Shift-dragged freehand angle shows `angle NNN.NNNNdeg (N.NNdeg off axis)` | **passed** |

**Merged sequentially, each re-gated on the previous merge, each branch
deleted (local + remote):** #39 → `8fa213b`, #37 → `e8ff209`, #38 →
`5737dcf`. `0072-ruling.md` §7's three-concurrent-AMBER-PR bottleneck —
measured as this project's real throughput limiter — is closed out.

## 2. `0108`-`0110` — THE THREE SNAP-TO-GRID FEATURES, BUILT IN ORDER

`0110-ruling.md` §5 ordered these first-Orthogonal (the safer variant,
found while answering Patrick's second request), then plain Snap to Grid,
then a disabled placeholder for the unsolved 15° case.

### (a) Snap to Grid Orthogonal — PR #40, merged

`floorplanner/design/validate.py`'s `snap_wall_to_grid_orthogonal`: the
clicked vertex (whichever end the right-click landed near — reusing
`WallItem.mousePressEvent`'s own endpoint hit test, factored out as
`_hit_endpoint`) snaps to the nearest grid point on both coordinates; the
other vertex takes the clicked vertex's shared-axis coordinate (chosen by
the wall's larger original delta) and its own free coordinate independently
snaps to grid. Exactly axis-aligned AND both ends on grid, anchored wherever
the user clicked — "which endpoint moves" answered by where they click, not
guessed (`0079-report.md` §2(c)'s old open question).

Refuses a degenerate result, a wall too near 45° (no shared axis to guess),
or a NEW `check()` violation (an opening running off its wall, I7, caught
by the same stable-key differential the batch repair uses — no special
case). REPORTS, does not refuse (`0109-ruling.md` §3's amendment to
`0108-ruling.md` §3's fourth refusal), any other wall whose angle deviation
or grid error gets worse.

A disabled "Snap to 15deg grid…" placeholder shipped in the same commit
(`0110-ruling.md` §4/§5 tier 3) — no arithmetic exists for it: `tan(15°)`
is irrational, so no wall at 15° can land both ends on any grid, at any
length.

**Patrick's check** (`wiscaway2026-08-09R.json`, right-click the lower end
of the wall near x≈79ft, Snap to Grid Orthogonal): *"Yes, both ends landed
on 79.00, exactly vertical. Perfect!"* — **passed**. Merged `4445fa4`,
branch deleted.

### (b) Snap to Grid, plain — PR #41, merged

Simpler than the orthogonal variant: no anchor, no shared axis, no near-45
refusal. Both endpoints round to the grid **independently**
(`floorplanner/design/validate.py`'s `snap_wall_to_grid`) — `0108-ruling.md`
§1's own words, "two ends that round to the same row make the wall
axis-aligned as a side effect, not as the goal." A wall whose ends straddle
a grid line can come out tilted — a **named limitation**, found while
building the safer variant first, not a surprise discovered later.

Same refusal/report shape as the orthogonal variant (degenerate, a new
`check()` violation, a worsened neighbour reported not refused).
**Multi-select applies to every selected wall in turn** (`0108-ruling.md`
§4): the document is walked fresh before each wall's turn, so the guards
see whatever the previous wall's snap already moved —
`0082-ruling.md` §3's stale-predicate lesson, reused rather than relearned.

**Patrick's check** (`wiscaway2026-08-09R.json`, select the wall at
x≈78.97ft, snap it): *"I checked the snap to grid and it works perfectly."*
— **passed**. Merged `d897df3`, branch deleted.

## 3. RECEIPTS

Both features verified against the real corpus before either check ran:

```
wiscaway2026-08-09R.json, w74, snap_wall_to_grid_orthogonal:
  refused: None
  relocations: [('L1', (1116.1155, 538.0612), (1116.0, 540.0)),
                ('L1', (1115.7089, 587.1283), (1116.0, 588.0))]
  worsened: ['w76', 'w92']
  baseline check() errors: 7 -- post-move: 7 (none new)

wiscaway2026-08-09R.json, w56 (the x=78.97ft chain 0108's own check names),
snap_wall_to_grid:
  refused: None
  relocations: [('L1', (947.9476, 660.0001), (948.0, 660.0)),
                ('L1', (947.9344, 654.0001), (948.0, 654.0))]
  worsened: ['w55', 'w57']
```

Fail-first throughout: every new test (16 + 11 for the orthogonal variant,
10 + 7 for the plain variant, plus `0107`'s own hook/gate tests) confirmed
RED against the pre-fix code before the fix landed, GREEN after. Full local
gate GREEN at every commit; CI green on every push and every merge to
`main` (single `pytest (py3.13, full gate)` job, per `0107-ruling.md`'s CI
simplification).

## 4. WHERE THINGS STAND

`main` at `69f03ca`. Working tree clean, no open branches, no open PRs.
`0072-ruling.md` §7's three-concurrent-AMBER-PR queue is empty. All of
`0107`-`0112` and `0108`-`0110`'s ordered work is DONE.

**Nothing is currently owed or blocked.** The one gap `0106-report.md` §3
flagged (the `--docs` lane running nowhere once CI's copy was cut) closed
with `0107-ruling.md` §3: the push hook now runs `--docs` live, every push.
