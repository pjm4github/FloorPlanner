# 0314 — report: the plan CAMERA now elevations the whole ROOM wall it faces, labelled for reading — on branch `plan-cameras`

**Code, 2026‑11‑11.** The record ([`0197-ruling.md`](0197-ruling.md) §7). The
second increment of the plan-cameras feature ([`0313`](0313-report.md), PR #109),
on his check of the first. His order 2026‑11‑11, seeing the single-wall
elevation: *"I want the camera to render the entire elevation of [the] room from
the point of view of the camera … any doors or walls that [jog] within the
elevation are also shown … I need the annotations to show up … To see what the
left and right side of the camera is seeing … all walls on that room are shown in
elevation view and the wall[s] that adjoin the left and right are called out on
the left and right as short lines on either side with their W numbers shown."*
Then, on the result: *"The elevation looks good … 1) Just label the wall on top
with Wxxx, then callout the width on the bottom with a blue dimension. For the
walls that are too narrow to dimension then aggregate them into a group and
dimension the group. Make the wall seams on the common elevation a faint grey
line so it doesn't distract."* Built on branch `plan-cameras` (the open PR #109);
**his check 2026‑11‑11 PASSED — "Land it, that looks fantastic"** — awaiting the
merge. (No **Landed:** line — the code rides the branch; the report is on `main`.)

## 1. WHAT HE ORDERED

The camera elevation was of the single nearest wall its aim ray hit. He wants the
elevation the camera actually SEES: the whole wall PLANE it faces — every wall
along it, even where a doorway splits one wall into two — with the side walls that
turn toward the camera called out at the two ends, and the whole thing labelled so
it reads: a W-number on each wall, a width dimension under each, grouped where the
walls are too thin to dimension, and the wall-to-wall seams dropped back so they
do not fight the drawing.

## 2. WHAT IT DOES

- **The faced PLANE, not one wall** (`CameraItem.elevation()` rewritten). The
  camera finds the ROOM it sits in (`_room_at`, point-in-outline), then walks that
  room's boundary out from the wall its aim ray hits, collecting every contiguous
  wall that **runs across the view AND stands in front of the camera** (depth test
  along the aim). These are the `faces[]`, laid left→right as the camera sees them
  (ordered by projection onto the camera's right axis). A far wall broken by a
  doorway into two coplanar segments (his DINING: W47 + W57) comes back as two
  faces, one plane. The near wall behind the camera is excluded by the depth test.
- **The returns.** The two walls that bound the run — where the boundary turns
  away from the view (runs along the aim, not across it) — are the side walls
  returning toward the camera; they come back as `left_return`/`right_return`
  (labels), assigned to the ends by their position along the camera's right.
  His DINING: W48 left, W58 right.
- **Outside a room** it falls back to the single faced wall (one face, no
  returns), so a camera in the yard still reads an exterior wall.
- **The ceiling** is the room's `ceiling_height_in` (120″ for DINING), never
  clipping the tallest opening; the floor its storey datum.
- **Readability** (`_WallElevationCanvas` rewritten). Each wall carries **just its
  W-number on top**, drawn only where the panel is wide enough to hold it; its
  **width is a blue dimension along the bottom**, one per wall — and a RUN of walls
  too narrow to dimension on their own is **aggregated into a single group
  dimension** (a 6″+6″+11″ jamb run → one 23″ callout, the 77″ wall beside it
  keeping its own). The **seams between walls on one plane are faint grey**, so
  they read as joints, not competing wall outlines; only the run's outer boundary
  is bold. One **blue height dimension down the left** carries the storey height
  (off the top label). Openings keep their size and sill/head; the returns draw as
  short labelled ticks turning out from the two bottom corners.

## 3. RECEIPTS (instrument `docs/evidence/0313-plan-cameras/render.py`)

The receipt builds a room whose far wall is two coplanar segments split by a
doorway (as DINING's is), with a window on the right segment and the two side
walls, drops a camera in the room aimed at it, and renders. `camera_elevation.png`
draws BOTH segments across the view — the doorway segment left (a floor panel, its
head dimensioned), the window segment right (glass + muntin on its sill) — divided
by a faint grey seam, each wall's width a blue dimension below, the storey height
a blue dimension on the left, the side walls as labelled return ticks at the
corners. `camera_plan.png` shows the camera glyph aimed at the wall. (Offscreen
text renders as tofu; `fmt_in` is ASCII and draws on the real display.) Verified
against his own `wiscaway2026-08-30R2` DINING camera: `faces [W47 78″, W57 102″]`,
returns `W48`/`W58`, ceiling 120″ — a one-to-one match to his marked-up drawing.

## 4. TESTS

`tests/test_cameras.py` (13, up from 11): the two opening/centre-offset tests now
read the faced wall's `faces[0]`; a new test puts a camera in a walled room and
asserts it elevations the far wall and names BOTH returns, the near wall behind it
excluded, the room's ceiling setting the top; a new test builds a far wall of two
coplanar segments split by a doorway and asserts BOTH become faces, left→right,
the doorway located, with both returns. Gate: full, GREEN (2110 collected).

## 5. NEXT

**His check PASSED** ("Land it, that looks fantastic") — PR #109 ready to merge on
his word. Still named, not ordered: the elevation tops out at the flat room
ceiling (a wall under a gable does not yet show the roof triangle — cap at the
roofline via `roofclip.surface_height`); the camera draws the walls it faces, not
a full depth-sorted "everything in view"; more per-camera menu actions are his to
name (save a named view, open in 3D, a section, a label); 0248's items 8–9 (porch
steps/base; porch roof turning a corner) still stand.
