# 0320 — report: looking in a dormer window no longer shows an EXTRUSION OF THE ROOF — the host roof is cut at the dormer's eave plane within its footprint; plus the elevation's dormer faces tier in front — on branch `dormer-render-fixes`

**Code, 2026-11-14.** Two dormer render fixes he asked for, both in the tree
when 0319/0321 were written, carried on now per his word ("carry on with the
dormer work"). Built on branch `dormer-render-fixes`; **AMBER — his look at the
3D view (and the elevation) is the merge condition.** None of it touches the
furnishings lane (0319/0321): the one shared file, `fp3d.py`, is edited only in
`_hidden_overhang_pieces` (~l.1300-1470), far from the fenced furnishing regions
(~160-520, ~1827-2250, ~3018-3160).

## 1. ISSUE B — the roof extrusion in the dormer window (`fp3d.py`)

**His report, 2026-11-14**, looking up through a front dormer window in the 3D
view: *"Instead of seeing the interior room formed by the dormer, I see what
appears to be an extrusion of the roof."* A second shot showed the dark attic
void correct at the top of the window and a **brown roof wedge rising into the
bottom of it**.

**Root cause.** The envelope clip is correct — a dormer owns its footprint
cells, so the host roof's VISIBLE region is properly carved under it (verified:
`rf7` owns its footprint, `rf1`'s region does not). The stray roof came from
`_hidden_overhang_pieces`, the "lower roof runs under the overhang" add-back
(0240 §1): where a dormer covered the host, the seam was taken against the
dormer's own SURFACE. Extrapolated past the open gable FACE that surface climbs
well above the host, so the clip read the dormer as "higher" there and KEPT the
host roof — which then stood **above the dormer's eaves, inside the dormer
room**, and showed straight through the face window. The cheek-wall-box skip
only covered `±wall_span`; the intruding pieces sat on the face/eave-overhang
strip and the cheek edges, outside that box, at the host surface (~z129 on his
plan, 33" above the dormer's 96" eave).

**The fix.** Cut the host at the dormer's EAVE PLANE within the dormer's
footprint:

- Split the hidden pieces on each covering dormer's full roof FOOTPRINT (not
  just its cheek-wall box), so every piece lies wholly inside or outside a
  dormer and a centroid test places it.
- `_below_dormer_eaves(pc)`: clip every host piece to AT OR BELOW the eaves of
  each dormer standing over it. Below the eaves the host is untouched — so it
  still projects to the cheek walls (his 2026-11 request, 0318-era, preserved);
  above the eaves it is the dormer's room, removed.
- The cut rides on the dormer's FOOTPRINT, not on the dormer being the chosen
  `coverer`. That is what catches `rf4`, where a neighbouring wing roof (`rf6`)
  is the higher coverer at the cheek edge — the eave-surface seam alone missed
  it, the footprint cut does not.

**Why the eave plane is the right boundary.** His own earlier fix wanted the
host to "project all the way to the cheek walls … the cheek wall eaves are
truncating the host roof under the eaves" — host BELOW the eave, kept. The bug
is host ABOVE the eave, inside the room, shown. The eave plane separates the two
exactly; a dormer that sits properly (eave above the local host) keeps its cheek
projection unchanged.

## 2. ISSUE A — the elevation's dormer faces tier in front (`cameras.py`)

Already in the tree from the prior session, carried in this commit. In the
whole-house-side elevation (`CameraItem._house_elevation`), a dormer's own faces
now paint AFTER the main roofs: a dormer PROJECTS from the slope it sits on, so
its gable end must read in FRONT of that slope, not be hidden by the far->near
depth sort. Dormer pieces are tagged and tiered last
(`pieces.sort(key=lambda pc: (pc.get("dormer", False), -pc["depth"]))`). His
report that prompted it: the dormer gable ends "should be pulled forward to the
front of the building."

## 3. RECEIPTS (his plan `wiscaway2026-11-11R1`, measured through `build_model`)

Host-roof faces standing ABOVE the dormer eave inside a dormer window (the
wedge), front dormers:

| dormer | before | after |
|---|---:|---:|
| `rf7` (right front) | present (z~129, the wedge) | **0** |
| `rf4` (left front) | present | **0** host (6 faces left are the dormer's OWN roof at its cheeks, correct) |
| `rf5` | — | **0** |

A headless before/after render (front-on, `render3d.py`) shows the brown host
roof removed from the dormer region (2736 -> 1604 tris in the dormer window).
The front-on orthographic understates the through-window effect; his app is the
authoritative check. Mesh integrity: 0 degenerate faces; 573 roof/dormer/clip
tests green, `test_cameras` + `test_viewer_model` green, ruff clean.

## 4. TESTS

Gate GREEN, full (2135). No new regression test added for Issue B: the fix is a
geometry cut in flagged roof-clip code whose effect is a mesh-face count inside
a dormer footprint, which the existing viewer-model coverage exercises; a
focused face-count assertion is the natural follow-up if he wants it pinned.

## 5. NEXT — NAMED, NOT ORDERED

The 3D CAMERA feature (a first-person 3D view bound to a plan camera, his
2026-11-14 request) is in progress on a separate branch; its viewer side
(`fp3dq.py`, `scene.qml`) is built. A dormer-FACE window still shows nothing in
3D for his cross-gable dormers (0292 §2, a separate limitation). 0248 items 8-9
still stand.
