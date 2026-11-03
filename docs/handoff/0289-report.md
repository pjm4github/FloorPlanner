# 0289 — report: PR #99 merged — a wall is not a gap, and each gap names its walls and vertices

**Landed:** PR #99 · 0438669 · 2026-11-02 · AMBER · checked by Patrick in the app ("The gaps look right"); landed on his word "merge #99"

**Code, 2026‑11‑02.** The record ([`0197-ruling.md`](0197-ruling.md) §7).

## 1. WHAT LANDED

`main` merged **`0438669`**, two commits on `3d1f9df`.

### A WALL IS NOT A GAP (the Review-wall-gaps bug)

He reported that fixing a gap and rescanning did not remove it from the list.
`validate.near_vertex_gaps` listed ANY two vertices in the
(`vertex_weld_in`, `join_tol_in`) band — including the two ENDS of one wall
segment. So a run of short 6″ walls listed every consecutive pair, and
"closing" one welded that wall to zero length and surfaced the next segment as
an identical gap: a real fix read as doing nothing. The scan now EXCLUDES a
pair joined by a wall (`connected = {frozenset((w.v1, w.v2)) ...}`). On his
`wiscaway2026-11-01R1.json` the list drops from **7 to the 1** genuine 0.82″
near-weld, and closing it clears on rescan.

### THE WALL AND VERTEX IDS IN THE DIALOG

`near_vertex_gaps` now returns each corner's vertex id —
`(level, (ax, ay), (bx, by), dist, a_id, b_id)`. The Review-wall-gaps dialog
names, per corner, the vertex and the wall(s) it holds, in the plan's session
labels (from `problems._session_labels_of` and the walk's `wall_items`), beside
the coordinates:

    default: V19 [free] (36'-11 1/2", 41'-5 1/2") and V20 [W22, W23, W36] (37'-0", 41'-6") are 0.82" apart

`[free]` is an open room corner no wall covers.

Tests: `test_a_wall_is_not_a_gap` (a short wall and an L are not gaps; a real
near-miss between separate walls still lists); the band test asserts the vertex
ids ride along; the existing gap tests updated to the new tuple shape.

## 2. RIDING ALONG — THE SNAPSHOT RE-CUT

`5bef843` re-cut `SESSION_SNAPSHOT.md` §0/§1 current through PR #98 (the prior
landing left only the marker advanced, its narrative sections stale). It is in
this PR because the branch was cut after it, not because it is part of the gap
change; it lands here.

## 3. FOR THE RECORD

His own plan files under `fixtures/incoming/` stay uncommitted, his to keep.
