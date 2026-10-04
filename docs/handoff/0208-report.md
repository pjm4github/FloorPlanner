# 0208 — report: grid snap by default (A6) built on his four answers; three things the build had to decide beyond them; AMBER, stopped for his check

**Code, 2026‑10‑03.** His word on [`0207`](0207-report.md) §4's four
decisions: *"yes to all four, proceed with the build."* Branch
`grid-snap-default` off `main` at `fe9bb96`,
[PR #70](https://github.com/pjm4github/FloorPlanner/pull/70) open, gate
GREEN, **stopped for his check** (§5). No merge has happened since
[`0206`](0206-report.md). Angled walls are out, by his word of the same
day ([`0205`](0205-report.md) §1).

## 1. WHAT'S BUILT — the four decisions, as answered

Probe [`a6_grid_snap_readback_probe.py`](../evidence/a6_grid_snap_readback_probe.py),
run on `main` ([`…probe.txt`](../evidence/a6-grid-snap-readback-probe.txt))
and on the branch (`…probe.after.txt`, on the branch).

| | before | now |
|---|---|---|
| **1. Land on the grid.** Draw from an off-grid corner (123,203) | end x = 249 | end x = **252** |
| drag an end of an off-grid wall | 243 → 279 | 243 → **276** |
| slide an off-grid wall sideways | y 203 → 221 | y 203 → **222** |
| **2. Shift** | free angle, on the grid | the cursor itself — no grid, any angle |
| **3. Released 6″ short** of another wall's end | pulled on and welded | **left 6″ short**; released on it, still welds to one corner |
| **Same landing at every zoom** — a drawn end beside a wall at x=402 | 402 at 0.25×, 426 at 2× | **426 at both** |
| a press 32″ from a wall end | starts on the end at 0.25×, on the grid at 2× | **on the grid at both** |
| **4. Readout**, mid-draw | raw cursor in the status bar, no angle | `Wall 10'-6" at 0.0° -- end x 20'-6", y 10'-0"` |

* `geometry.wall_snap_landing(origin, s)` rounds the **coordinate**, not
  the distance — [`0070`](0070-ruling.md) §3's rule, which every roof drag
  already followed. Used by the draw, the end drag and the body slide,
  for axis-aligned walls only. A wall drawn from an off-grid corner gets
  an on-grid far end; the corner it started from is not moved.
* `config.GESTURE_WELD_IN = 3.0` — the weld radius of a gesture, half a
  step. `weld_wall_ends` takes it from the draw release; Normalize, Close
  gap and extraction keep `JOIN_TOL` (9″), pinned by a test.
* The readout is `MainWindow.show_wall_readout`, called while drawing and
  while dragging an end; the coordinate label follows the wall's end for
  the length of the gesture.
* The ridge tool shares the wall's end rule and follows it.
* The unreachable *"Ctrl: move freely"* branch of the body slide is gone.
* Tool hints and three `README.md` lines now say what Shift does.

## 2. THREE THINGS THE BUILD HAD TO DECIDE — beyond the four, and his to overrule

Each was forced by an acceptance line or by a measurement at the build;
none was in 0207 §4, so each is said here rather than left inside the
diff.

**(a) A pull acts only toward a target that is OFF the grid.** 0207 said
the two zoom-scaled tolerances would become 9″ scene-space constants.
That alone does not pass *"a 6″ reveal untouched"*: a 9″ pull toward
another wall's line takes an end released 6″ short and puts it on the
line before the weld is even asked. So the start catch, the draw's
align-to-an-open-end and the end drag's stick now **skip a target that
is itself on the grid** — the end lands on it when aimed at it (within
half a step) and a step short when meant short — and keep their 9″ reach
for a line or a corner the grid cannot express. **What he will feel:**
drawing toward an on-grid wall, a cursor 9″ short used to be pulled onto
it; now it must be within 3″. Four existing tests pinned the old pull
(cursor at 291 reaching a wall at 300) and are rewritten to both halves:
298 reaches it, 291 lands at 288.

**(b) A sideways slide of under an inch is not a slide.** Found by an
existing test, not foreseen: with landing in place, **any** drag on an
off-grid wall — a click that wobbled, a drag *along* the wall — jumped
it to its grid line. `dragWallFuseStraggler.fpm`, his own macro, drags
down the interior column on its fifth line, and that shifted the column
1.44″ sideways. Now a slide with less than 1″ of sideways travel moves
nothing; a deliberate small slide still reaches the nearest grid line
(203 → 204 for a 1.5″ drag, tested). With this the macro test passes
**unmodified**.

**(c) An off-grid corner is still caught at the start of a wall**, within
9″ scene-space, because the grid cannot put a new wall on it otherwise.
An on-grid corner needs no catch.

## 3. THE CHECK — receipts

`tests/test_grid_snap_default.py`, **17 tests** (`gui`), mouse-driven,
several at both 0.25× and 2×. **Eleven fail on `main`'s code — run
there, not assumed — and six are controls** that pass on both: an
on-grid wall behaves exactly as before; an angled wall still moves by
whole steps of length along its own axis; Ctrl still gives 15° steps; a
shared corner still carries both walls; and the 2× halves of the two
zoom tests.

Rewritten, not deleted: four draw tests and
`test_shift_still_free_angles` in `tests/test_walls.py`, with one added
for the pull toward an off-grid wall; the Shift ridge test in
`tests/test_roof_ridge_tool.py`, which asserted an exact on-grid end
and now asserts the cursor to within a pixel. Every other pre-existing
test passes unmodified.

Full suite **1411 passed**, 7 deselected (`perf` lane), `ruff` clean,
gate GREEN — the branch's own run.

## 4. FOUND AT THE BUILD — one pre-existing fault, named, not fixed

**Which wall is split at a four-way crossing depends on the run.**
Replaying `dragWallFuseStraggler.fpm` fourteen times in one process, on
`main`'s code: after its sixth line, three runs have the horizontal wall
whole and the vertical one split at (340.56, 270.03), and the others the
reverse. The macro's last line brings them back to the same sixteen
walls, which is why no test has seen it. Something on the join path
iterates in an order that is not fixed. It became visible only because
(b)'s fault briefly turned the transient difference into a final one —
15 walls instead of 16 in three runs of fourteen. With (b) fixed the
final state is stable (fourteen of fourteen). **The mid-macro
nondeterminism is still there on `main` and on the branch.** It wants
its own defect record; I have not filed one, since a number is his or
the reviewer's to give.

## 5. HIS CHECK

On a plan of his, with the snap at 6″:

1. Draw a wall starting on a corner that is off the grid — the far end
   lands on a grid line.
2. Drag the end of an off-grid wall, and slide an off-grid wall
   sideways — both land on the grid. Click an off-grid wall without
   dragging — it does not move.
3. Draw a wall to **6″ short** of another wall's end — it stays 6″
   short. Draw one onto the end — they join as one corner.
4. Hold **Shift** while drawing — the end follows the cursor exactly.
5. Watch the status bar while drawing — length, heading and the snapped
   end.
6. Repeat 1 zoomed far out — the same landing.
7. **(a) is the one to judge:** draw toward an on-grid wall and see
   whether needing to be within 3″ of it, rather than 9″, is right.

## 6. NOT IN THIS TRANCHE

* **Angled walls** — unchanged, by his word. An angled wall's end still
  rounds its length along the ray.
* **What an operation produces.** A weld, a join or a coalesce still
  puts geometry wherever its own rule says. This closes the cursor
  gestures only ([`0207`](0207-report.md) §3).
* **A Shift end-drag still makes an off-axis wall** — more freely than
  before, since the end no longer lands on the grid. That is what
  "unconstrained" means; the orthogonality report is where it shows.
* **Recorded macros that hold Shift** replay to the raw point now, not
  the grid point they were recorded landing on.
* **The gallery was not regenerated** — no picture in it shows a gesture
  in progress.

## 7. `fixtures/incoming/`, with ages

`single-floor-90-roof-gable-end-check.json` — his own, 2026‑10‑03, exit
not yet named ([`0205`](0205-report.md) §3). `README.md`.

## 8. WHAT HAPPENS NEXT

His check (§5). On his word PR #70 merges, branch deleted in the merge
step, the merge recorded in the report that follows. Then the queue as
[`0205`](0205-report.md) §4 left it: the file in `incoming/`, the D67
pair, the status board — and §4's fault, if he wants it filed.

**Carried:** unchanged from [`0207`](0207-report.md).
