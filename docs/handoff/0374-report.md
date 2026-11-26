# 0374 — report on 0372 item B: the §8.4 cantilever floor now closes open air only. Fix done on the branch; one corner left for your eye. AMBER.

2026-11-26, Code session. Branch `dormer-climb-floor-0372` at `2f39c90` (one
commit on `main` `156cbf9`). Item A stays paused (0373). This is item B: fixed,
tested, O4-clean; the picture and the corner readback 0372 §4 B asks for are
below, and I have NOT closed the corner.

## 1. The fix

`fp3d._cantilever_floor` laid the DORMER_CONTROL_SPEC §8.4 flat attic floor
across the WHOLE overhang, subtracting only the dormer's own host rectangle. It
now also drops the floor wherever ANOTHER roof is drawn under the overhang and
sits at or below the floor -- cut at the EXACT equal-height line (the roof
surface = the floor height), each piece split first by that roof's own
plane-change lines, as the weld and territory cuts are. So:

- **open air is still floored** (the §8.4 purpose);
- **ground where the lower roof is ABOVE the floor is kept** (no false hole);
- **ground where the lower roof is AT OR BELOW the floor is dropped** -- there
  the roof already closes the attic and a flat slab would stand proud.

"Drawn under the overhang" is computed from the other roofs' footprints and
`surface_height`, filtered to those that dip to or below the floor over the
piece; a plan with no such roof is untouched.

## 2. Fail-test-first and O4

- `tests/test_dormer_floor_open_air_0372.py`: a gable dormer on L2 cantilevered
  past its host, a low shed under the WEST half of the overhang. The floor must
  cover only the open-air (east) half. RED on the pre-fix tree (floor laid over
  the shed, x from 160), GREEN after; the control (shed removed, whole overhang
  floored) holds before and after.
- **O4 byte-identical**: every mesh of all 26 `0360-dormer-orderings` cases and
  the 7 `0367-pyramid-roof` cases hashes the same before and after. Nothing with
  no lower roof under an overhang moves. Full gate GREEN (OFF+ON, 2734).

## 3. Readback on your §4 B scenario

I reconstructed the frozen file with `rf4` given hipped ends (ridge x 833-911.5,
hip run 36, gable ends). It reproduces your measurement: `rf4`'s hip surface is
**122 at x 800** (and 120 at the x 797 / 947.5 corners), the dormer floor at
**133-134**. Point-in-floor coverage, before vs after the fix:

| Point | rf4 surface | before | after |
|---|---|---|---|
| S corner (800, 813) | 122 (below floor) | floor present, 12 in proud | **trimmed** |
| N corner (945, 813) | 120 (below floor) | proud | **trimmed** |
| centre (872, 813) | 138 (above floor) | present | present (kept) |
| open air (789, 813) | no roof | present | present (floored) |

So the slab no longer stands proud of the hip, and it still closes the open air
past the hips.

## 4. The corner I did NOT close (0372 §4 B)

With the proud floor gone, at each of the **two lower corners of the L2 face
wall** the wall base sits at **134** and the hipped skirt beneath falls to
**120** -- a roughly **14 in open gap** at the corner where the flat floor used
to bridge (proudly) to the slab edge. The picture of the hipped case is sent to
Patrick alongside this file (front elevation of the house, and a BR3 close-up).
I am NOT closing that corner -- your call (§4 B): leave the gap, drop the face
wall to the hip, a triangular infill, or something else.

## 5. Status

B is AMBER, awaiting Patrick's look (0372 §6 batches it with A's check). The
branch holds B only; A carries no code (paused at 0373). One report will cover
the branch once A is also done; this is the interim so the corner can be ruled.
