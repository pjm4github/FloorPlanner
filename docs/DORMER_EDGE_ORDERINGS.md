# Dormer edge orderings

Every possible plan ordering, ties included, of the four edges that position a
dormer on its host roof. Each row is one case, identified by a stable ID
(W01–W75). Test cases, review images and rules reference a case by that ID.
Do not renumber or reorder the rows.

## Edges

| Symbol | Edge |
| ------ | ---- |
| A      | Host roof eave |
| B      | Dormer eave over the dormer face |
| C      | Dormer face wall |
| D      | Wall on the level below, which the host roof sits on |

## Notation

- Distances are measured in plan from the dormer anchor (apex).
- `X > Y` means X is farther from the anchor than Y. `X=Y` means the two are at
  the same distance.
- **Ordering** lists the edges from farthest to closest.
- **Pos 1 … Pos 4** are the distance groups, farthest (Pos 1) to closest. Tied
  edges share a cell.
- **Levels** is the number of distinct distances (4 = no ties, 1 = all equal).
- **Tie pattern** is the group sizes from farthest to closest, e.g. `1+2+1` is a
  single edge, then a tied pair, then a single edge.
- **X vs Y** is the pairwise relation of X to Y: `>`, `=` or `<`.

## Buildability

A row is unbuildable when either relation below holds. Ties (`=`) are buildable:
they are a zero overhang.

| Relation | Reason shown in the table | Why |
| -------- | ------------------------- | --- |
| D > A    | D > A: host eave inside LV1 wall | The host roof bears on the LV1 wall, so its eave cannot sit inside that wall line (negative host overhang). |
| C > B    | C > B: dormer eave inside face wall | The dormer roof must cover its face wall. The face travels only from the anchor out to the face eave (`DORMER_CONTROL_SPEC.md`, R3a). |

Unbuildable rows stay in the table as a record of the case. **Do not build a
roof/dormer example for a row marked `no`.**

| Status | Count |
| ------ | ----- |
| Buildable | 26 |
| Unbuildable, D > A only | 18 |
| Unbuildable, C > B only | 18 |
| Unbuildable, both | 13 |
| Total | 75 |

Buildable IDs: W01, W02, W05, W07, W08, W09, W25, W26, W29, W31, W37, W38, W40, W41, W49, W51, W52, W53, W61, W62, W65, W67, W68, W71, W72, W75

## Table 1:  Dormer Order IDs

| ID  | Ordering      | Buildable | Unbuildable reason                                                    | Pos 1 | Pos 2 | Pos 3 | Pos 4 | Levels | Tie pattern | A vs B | A vs C | A vs D | B vs C | B vs D | C vs D |
| --- | ------------- | --------- | --------------------------------------------------------------------- | ----- | ----- | ----- | ----- | ------ | ----------- | ------ | ------ | ------ | ------ | ------ | ------ |
| W01 | A > B > C > D | yes       |                                                                       | A     | B     | C     | D     | 4      | 1+1+1+1     | >      | >      | >      | >      | >      | >      |
| W02 | A > B > D > C | yes       |                                                                       | A     | B     | D     | C     | 4      | 1+1+1+1     | >      | >      | >      | >      | >      | <      |
| W03 | A > C > B > D | no        | C > B: dormer eave inside face wall                                   | A     | C     | B     | D     | 4      | 1+1+1+1     | >      | >      | >      | <      | >      | >      |
| W04 | A > C > D > B | no        | C > B: dormer eave inside face wall                                   | A     | C     | D     | B     | 4      | 1+1+1+1     | >      | >      | >      | <      | <      | >      |
| W05 | A > D > B > C | yes       |                                                                       | A     | D     | B     | C     | 4      | 1+1+1+1     | >      | >      | >      | >      | <      | <      |
| W06 | A > D > C > B | no        | C > B: dormer eave inside face wall                                   | A     | D     | C     | B     | 4      | 1+1+1+1     | >      | >      | >      | <      | <      | <      |
| W07 | B > A > C > D | yes       |                                                                       | B     | A     | C     | D     | 4      | 1+1+1+1     | <      | >      | >      | >      | >      | >      |
| W08 | B > A > D > C | yes       |                                                                       | B     | A     | D     | C     | 4      | 1+1+1+1     | <      | >      | >      | >      | >      | <      |
| W09 | B > C > A > D | yes       |                                                                       | B     | C     | A     | D     | 4      | 1+1+1+1     | <      | <      | >      | >      | >      | >      |
| W10 | B > C > D > A | no        | D > A: host eave inside LV1 wall                                      | B     | C     | D     | A     | 4      | 1+1+1+1     | <      | <      | <      | >      | >      | >      |
| W11 | B > D > A > C | no        | D > A: host eave inside LV1 wall                                      | B     | D     | A     | C     | 4      | 1+1+1+1     | <      | >      | <      | >      | >      | <      |
| W12 | B > D > C > A | no        | D > A: host eave inside LV1 wall                                      | B     | D     | C     | A     | 4      | 1+1+1+1     | <      | <      | <      | >      | >      | <      |
| W13 | C > A > B > D | no        | C > B: dormer eave inside face wall                                   | C     | A     | B     | D     | 4      | 1+1+1+1     | >      | <      | >      | <      | >      | >      |
| W14 | C > A > D > B | no        | C > B: dormer eave inside face wall                                   | C     | A     | D     | B     | 4      | 1+1+1+1     | >      | <      | >      | <      | <      | >      |
| W15 | C > B > A > D | no        | C > B: dormer eave inside face wall                                   | C     | B     | A     | D     | 4      | 1+1+1+1     | <      | <      | >      | <      | >      | >      |
| W16 | C > B > D > A | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | C     | B     | D     | A     | 4      | 1+1+1+1     | <      | <      | <      | <      | >      | >      |
| W17 | C > D > A > B | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | C     | D     | A     | B     | 4      | 1+1+1+1     | >      | <      | <      | <      | <      | >      |
| W18 | C > D > B > A | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | C     | D     | B     | A     | 4      | 1+1+1+1     | <      | <      | <      | <      | <      | >      |
| W19 | D > A > B > C | no        | D > A: host eave inside LV1 wall                                      | D     | A     | B     | C     | 4      | 1+1+1+1     | >      | >      | <      | >      | <      | <      |
| W20 | D > A > C > B | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | D     | A     | C     | B     | 4      | 1+1+1+1     | >      | >      | <      | <      | <      | <      |
| W21 | D > B > A > C | no        | D > A: host eave inside LV1 wall                                      | D     | B     | A     | C     | 4      | 1+1+1+1     | <      | >      | <      | >      | <      | <      |
| W22 | D > B > C > A | no        | D > A: host eave inside LV1 wall                                      | D     | B     | C     | A     | 4      | 1+1+1+1     | <      | <      | <      | >      | <      | <      |
| W23 | D > C > A > B | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | D     | C     | A     | B     | 4      | 1+1+1+1     | >      | <      | <      | <      | <      | <      |
| W24 | D > C > B > A | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | D     | C     | B     | A     | 4      | 1+1+1+1     | <      | <      | <      | <      | <      | <      |
| W25 | A=B > C > D   | yes       |                                                                       | AB    | C     | D     |       | 3      | 2+1+1       | =      | >      | >      | >      | >      | >      |
| W26 | A=B > D > C   | yes       |                                                                       | AB    | D     | C     |       | 3      | 2+1+1       | =      | >      | >      | >      | >      | <      |
| W27 | A=C > B > D   | no        | C > B: dormer eave inside face wall                                   | AC    | B     | D     |       | 3      | 2+1+1       | >      | =      | >      | <      | >      | >      |
| W28 | A=C > D > B   | no        | C > B: dormer eave inside face wall                                   | AC    | D     | B     |       | 3      | 2+1+1       | >      | =      | >      | <      | <      | >      |
| W29 | A=D > B > C   | yes       |                                                                       | AD    | B     | C     |       | 3      | 2+1+1       | >      | >      | =      | >      | <      | <      |
| W30 | A=D > C > B   | no        | C > B: dormer eave inside face wall                                   | AD    | C     | B     |       | 3      | 2+1+1       | >      | >      | =      | <      | <      | <      |
| W31 | B=C > A > D   | yes       |                                                                       | BC    | A     | D     |       | 3      | 2+1+1       | <      | <      | >      | =      | >      | >      |
| W32 | B=C > D > A   | no        | D > A: host eave inside LV1 wall                                      | BC    | D     | A     |       | 3      | 2+1+1       | <      | <      | <      | =      | >      | >      |
| W33 | B=D > A > C   | no        | D > A: host eave inside LV1 wall                                      | BD    | A     | C     |       | 3      | 2+1+1       | <      | >      | <      | >      | =      | <      |
| W34 | B=D > C > A   | no        | D > A: host eave inside LV1 wall                                      | BD    | C     | A     |       | 3      | 2+1+1       | <      | <      | <      | >      | =      | <      |
| W35 | C=D > A > B   | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | CD    | A     | B     |       | 3      | 2+1+1       | >      | <      | <      | <      | <      | =      |
| W36 | C=D > B > A   | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | CD    | B     | A     |       | 3      | 2+1+1       | <      | <      | <      | <      | <      | =      |
| W37 | A > B=C > D   | yes       |                                                                       | A     | BC    | D     |       | 3      | 1+2+1       | >      | >      | >      | =      | >      | >      |
| W38 | A > B=D > C   | yes       |                                                                       | A     | BD    | C     |       | 3      | 1+2+1       | >      | >      | >      | >      | =      | <      |
| W39 | A > C=D > B   | no        | C > B: dormer eave inside face wall                                   | A     | CD    | B     |       | 3      | 1+2+1       | >      | >      | >      | <      | <      | =      |
| W40 | B > A=C > D   | yes       |                                                                       | B     | AC    | D     |       | 3      | 1+2+1       | <      | =      | >      | >      | >      | >      |
| W41 | B > A=D > C   | yes       |                                                                       | B     | AD    | C     |       | 3      | 1+2+1       | <      | >      | =      | >      | >      | <      |
| W42 | B > C=D > A   | no        | D > A: host eave inside LV1 wall                                      | B     | CD    | A     |       | 3      | 1+2+1       | <      | <      | <      | >      | >      | =      |
| W43 | C > A=B > D   | no        | C > B: dormer eave inside face wall                                   | C     | AB    | D     |       | 3      | 1+2+1       | =      | <      | >      | <      | >      | >      |
| W44 | C > A=D > B   | no        | C > B: dormer eave inside face wall                                   | C     | AD    | B     |       | 3      | 1+2+1       | >      | <      | =      | <      | <      | >      |
| W45 | C > B=D > A   | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | C     | BD    | A     |       | 3      | 1+2+1       | <      | <      | <      | <      | =      | >      |
| W46 | D > A=B > C   | no        | D > A: host eave inside LV1 wall                                      | D     | AB    | C     |       | 3      | 1+2+1       | =      | >      | <      | >      | <      | <      |
| W47 | D > A=C > B   | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | D     | AC    | B     |       | 3      | 1+2+1       | >      | =      | <      | <      | <      | <      |
| W48 | D > B=C > A   | no        | D > A: host eave inside LV1 wall                                      | D     | BC    | A     |       | 3      | 1+2+1       | <      | <      | <      | =      | <      | <      |
| W49 | A > B > C=D   | yes       |                                                                       | A     | B     | CD    |       | 3      | 1+1+2       | >      | >      | >      | >      | >      | =      |
| W50 | A > C > B=D   | no        | C > B: dormer eave inside face wall                                   | A     | C     | BD    |       | 3      | 1+1+2       | >      | >      | >      | <      | =      | >      |
| W51 | A > D > B=C   | yes       |                                                                       | A     | D     | BC    |       | 3      | 1+1+2       | >      | >      | >      | =      | <      | <      |
| W52 | B > A > C=D   | yes       |                                                                       | B     | A     | CD    |       | 3      | 1+1+2       | <      | >      | >      | >      | >      | =      |
| W53 | B > C > A=D   | yes       |                                                                       | B     | C     | AD    |       | 3      | 1+1+2       | <      | <      | =      | >      | >      | >      |
| W54 | B > D > A=C   | no        | D > A: host eave inside LV1 wall                                      | B     | D     | AC    |       | 3      | 1+1+2       | <      | =      | <      | >      | >      | <      |
| W55 | C > A > B=D   | no        | C > B: dormer eave inside face wall                                   | C     | A     | BD    |       | 3      | 1+1+2       | >      | <      | >      | <      | =      | >      |
| W56 | C > B > A=D   | no        | C > B: dormer eave inside face wall                                   | C     | B     | AD    |       | 3      | 1+1+2       | <      | <      | =      | <      | >      | >      |
| W57 | C > D > A=B   | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | C     | D     | AB    |       | 3      | 1+1+2       | =      | <      | <      | <      | <      | >      |
| W58 | D > A > B=C   | no        | D > A: host eave inside LV1 wall                                      | D     | A     | BC    |       | 3      | 1+1+2       | >      | >      | <      | =      | <      | <      |
| W59 | D > B > A=C   | no        | D > A: host eave inside LV1 wall                                      | D     | B     | AC    |       | 3      | 1+1+2       | <      | =      | <      | >      | <      | <      |
| W60 | D > C > A=B   | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | D     | C     | AB    |       | 3      | 1+1+2       | =      | <      | <      | <      | <      | <      |
| W61 | A=B=C > D     | yes       |                                                                       | ABC   | D     |       |       | 2      | 3+1         | =      | =      | >      | =      | >      | >      |
| W62 | A=B=D > C     | yes       |                                                                       | ABD   | C     |       |       | 2      | 3+1         | =      | >      | =      | >      | =      | <      |
| W63 | A=C=D > B     | no        | C > B: dormer eave inside face wall                                   | ACD   | B     |       |       | 2      | 3+1         | >      | =      | =      | <      | <      | =      |
| W64 | B=C=D > A     | no        | D > A: host eave inside LV1 wall                                      | BCD   | A     |       |       | 2      | 3+1         | <      | <      | <      | =      | =      | =      |
| W65 | A=B > C=D     | yes       |                                                                       | AB    | CD    |       |       | 2      | 2+2         | =      | >      | >      | >      | >      | =      |
| W66 | A=C > B=D     | no        | C > B: dormer eave inside face wall                                   | AC    | BD    |       |       | 2      | 2+2         | >      | =      | >      | <      | =      | >      |
| W67 | A=D > B=C     | yes       |                                                                       | AD    | BC    |       |       | 2      | 2+2         | >      | >      | =      | =      | <      | <      |
| W68 | B=C > A=D     | yes       |                                                                       | BC    | AD    |       |       | 2      | 2+2         | <      | <      | =      | =      | >      | >      |
| W69 | B=D > A=C     | no        | D > A: host eave inside LV1 wall                                      | BD    | AC    |       |       | 2      | 2+2         | <      | =      | <      | >      | =      | <      |
| W70 | C=D > A=B     | no        | D > A: host eave inside LV1 wall; C > B: dormer eave inside face wall | CD    | AB    |       |       | 2      | 2+2         | =      | <      | <      | <      | <      | =      |
| W71 | A > B=C=D     | yes       |                                                                       | A     | BCD   |       |       | 2      | 1+3         | >      | >      | >      | =      | =      | =      |
| W72 | B > A=C=D     | yes       |                                                                       | B     | ACD   |       |       | 2      | 1+3         | <      | =      | =      | >      | >      | =      |
| W73 | C > A=B=D     | no        | C > B: dormer eave inside face wall                                   | C     | ABD   |       |       | 2      | 1+3         | =      | <      | =      | <      | =      | >      |
| W74 | D > A=B=C     | no        | D > A: host eave inside LV1 wall                                      | D     | ABC   |       |       | 2      | 1+3         | =      | =      | <      | =      | <      | <      |
| W75 | A=B=C=D       | yes       |                                                                       | ABCD  |       |       |       | 1      | 4           | =      | =      | =      | =      | =      | =      |


The following table describes the functionality of the dormer rendering in camera mode and in 3D mode. 
Here is the code for each aspect of the components of the dormer and the roof host. 

## Table 2: Dormer Render Rules

**Face type is set by `C vs D`.** In `auto` mode (the only mode the ordering
alone can decide), `dormer_geometry.classify_face` / `face_past_eave` read the
face (C) against the wall / host-eave reference (D): `C > D` → **cantilever**,
`C < D` → **setback**, `C = D` → **plain / standard**. The five render columns
below follow from that type. Codes marked with how they were derived; `—` =
not applicable to this ordering. See **Notes** under the table for the two
things the ordering CANNOT decide (balcony intent; wall-below on the face line).

***Legend***

**face** — how the dormer face wall is built (`fp3d._dormer_face`):
  - **R** = raise the face from the wall under the face wall that is on the same level as the balcony. make sure that the windows and openings on the wall under the dormer are used on the face.  *(code: a house wall on the face line climbs into the dormer, `_on_a_wall` → `face_cuts_out`; the wall-below's openings are cut into the climbing wall. Needs a wall on the face line.)*
  - **G** = generate a rake face standing ON the host roof surface — short wall pieces rise from the host up to the dormer's own surface. *(code: `_dormer_face` `in_host` branch. The default when no wall is drawn on the face line.)*
  - **H** = the face hangs past the host eave and drops to the attic floor, which is closed underneath. *(code: `_dormer_face` cantilever branch, `base = floor_z`.)*

**balcony** — built ONLY when the user sets `face_mode = "balcony"`; supported only on set-back geometry (`C < D`):
  - **F** = build the wall, if any around the balcony level, walls will riase to the dormer roof, fence will rise to the fence height. The floor of the balcony will extend out to the wall under the level of the floor below. The roof will be cut away so the balcony has a flat floor on the balcony. *(code: `_balcony_terraces` + `_cells_minus_terraces`; `WALL_H` caps railing 36", fence 72", exterior = full ceiling.)*
  - **F∗** = available on this ordering (it is set-back) but only if the user chooses balcony; in `auto` it renders as a plain setback.

**cantilever** — the overhang when the face projects past the host eave (`C > D`, `dormer_geometry.face_past_eave > 6"`):
  - **V** = cantilevered: the face overhangs the host roof edge (hangs over open air).
  - **—** = lands on the host (`C ≤ D`).

**roof-skirt** — a USER SWITCH (on/off) for a strip of roof in FRONT of the face that joins the dormer to the host eave (A). Its `A vs C` axis is PLAN only — whether host roof lies in front horizontally; a FULL answer also needs the VERTICAL relation (is the eave below the dormer), which the edge ordering does NOT carry — see note 7b. *(A control to ADD, stored like `face_mode` — the ENUM `skirt_mode` (`auto`/`on`/`off`), a dialog SELECTOR that greys out when no skirt is available; plus a schema key. See notes 4 and 8. Today a set-back strip renders only because the host is not cut there; there is no switch yet.)*
  - **S** = skirt available (`A > C`): host roof already lies in front, from the face out to the eave; the switch keeps/joins it (also for a balcony's front wall out to A).
  - **S°** = the face is PAST the eave in plan (`A < C`) but a skirt is STILL possible IF the host eave A sits BELOW the cantilever — a skirt roof bridges from the dormer down-and-in to the eave (Patrick, 2026-11-22). Needs elevations.
  - **—** = none: `A = C` (face at the eave, a degenerate zero-width strip).

**floor-under-balcony** — what closes the open air under the dormer:
  - **U** = a flat floor closes the attic underneath a cantilevered overhang (`fp3d._cantilever_floor`); laid for a cantilever that is NOT a balcony.
  - **U∥S°** = the §8.4 floor-vs-skirt DECISION: the overhang underside can be closed by the flat §8.4 floor (**U**, today's default) OR by a bridging roof-skirt (**S°**, note 7b) when the host eave is below the dormer — one or the other, not both. Applies to the true-overhang rows (`A < C`); stage 3 picks which the switch selects. See note 7c.
  - **U‡** = flat floor today, but if the `‡` face actually sits on the host (eave boundary, note 7) there is NO overhang to close and the floor is spurious.
  - **K∗** = the balcony's own deck floors the overhang out to the walls (`_balcony_overhang_deck`), so no separate cantilever floor is laid (only when balcony is chosen).
  - **—** = nothing to close (the dormer sits wholly on the host).

`∗` = depends on the user's `face_mode = "balcony"` choice, which the edge
ordering cannot determine; the `auto` cases (W##.json in `evidence/`) never set
it, so as-built they read `—` for the starred cells.

| ID  | Face type (C vs D) | face | balcony | cantilever | roof-skirt (A vs C) | floor-under-balcony |
| --- | ------------------ | ---- | ------- | ---------- | ------------------- | ------------------- |
| W01 | cantilever (C>D) | H‡   | —   | V | S  (A>C) | U‡ |
| W02 | setback (C<D)    | G    | F∗  | — | S  (A>C) | K∗ |
| W05 | setback (C<D)    | G    | F∗  | — | S  (A>C) | K∗ |
| W07 | cantilever (C>D) | H‡   | —   | V | S  (A>C) | U‡ |
| W08 | setback (C<D)    | G    | F∗  | — | S  (A>C) | K∗ |
| W09 | cantilever (C>D) | H    | —   | V | S° (A<C) | U∥S° |
| W25 | cantilever (C>D) | H‡   | —   | V | S  (A>C) | U‡ |
| W26 | setback (C<D)    | G    | F∗  | — | S  (A>C) | K∗ |
| W29 | setback (C<D)    | G    | F∗  | — | S  (A>C) | K∗ |
| W31 | cantilever (C>D) | H    | —   | V | S° (A<C) | U∥S° |
| W37 | cantilever (C>D) | H‡   | —   | V | S  (A>C) | U‡ |
| W38 | setback (C<D)    | G    | F∗  | — | S  (A>C) | K∗ |
| W40 | cantilever (C>D) | H    | —   | V | —  (A=C) | U  |
| W41 | setback (C<D)    | G    | F∗  | — | S  (A>C) | K∗ |
| W49 | plain/std (C=D)   | G†   | —   | — | S  (A>C) | —  |
| W51 | setback (C<D)    | G    | F∗  | — | S  (A>C) | K∗ |
| W52 | plain/std (C=D)   | G†   | —   | — | S  (A>C) | —  |
| W53 | cantilever (C>D) | H    | —   | V | S° (A<C) | U∥S° |
| W61 | cantilever (C>D) | H    | —   | V | —  (A=C) | U  |
| W62 | setback (C<D)    | G    | F∗  | — | S  (A>C) | K∗ |
| W65 | plain/std (C=D)   | G†   | —   | — | S  (A>C) | —  |
| W67 | setback (C<D)    | G    | F∗  | — | S  (A>C) | K∗ |
| W68 | cantilever (C>D) | H    | —   | V | S° (A<C) | U∥S° |
| W71 | plain/std (C=D)   | G†   | —   | — | S  (A>C) | —  |
| W72 | plain/std (C=D)   | G†   | —   | — | —  (A=C) | —  |
| W75 | plain/std (C=D)   | G†   | —   | — | —  (A=C) | —  |

`†` = **G** today (generated rake on the host), because the evidence cases draw
no wall on the storey BELOW the face. If a wall IS drawn on the face line on the
level below, `classify_face` returns **plain-wall** and the face becomes **R**
(that wall climbs into the dormer). Which it is cannot be read from the ordering.

`‡` = `C > D` (a cantilever by the WALL, so the face column reads **H**) yet
`A > C` (host roof still in front, so the skirt is available — **S**). The face
cannot both hang to the floor AND sit under a strip of host roof; which it is
turns on whether the boundary is the wall (D) or the eave (A). See note 7.

`°` = the face is past the eave in plan (`A < C`) but a skirt may STILL be built
if the host eave A sits BELOW the cantilever, bridging from the dormer down to
the eave (Patrick, 2026-11-22). Whether it does needs elevations the plan edge
ordering does not carry. See note 7b.

## Notes — what the code settles, and what it does not

1. **Type ← `C vs D`, confirmed in code and at scale.** `classify_face` splits
   on the face (C) vs the wall/host-eave reference (D) with a 6" tolerance
   (`FACE_ALIGN_TOL_IN`): past the eave → cantilever, roof in front → setback,
   at the eave → plain/standard. All 26 built cases classify exactly this way
   (`evidence/.../INDEX.md`), so the per-row **Face type** column above is
   extracted, not guessed.

2. **Balcony is intent, not ordering (the `∗` cells).** `face_mode` is a stored
   enum (`auto / plain_wall / setback / balcony`) and is the ONE dormer→house
   datum the builder cannot re-derive (DORMER_CONTROL_SPEC.md §7.3). Balcony is
   *supported* only where the face is set back (`C < D`), so only the setback
   rows can carry it — but no ordering forces it. The starred cells say "this is
   what balcony WOULD do on this ordering", not "this row is a balcony".

3. **face R vs G (the `†` cells) needs a wall below.** The generator draws the
   face + cheek walls on the dormer's OWN level (LV2); `_dormer_face` adopts a
   wall on the face line from ANY level (`all_plan_walls`), so whether these
   already render as **R** rather than **G** is a question for stage 3 to verify
   against the actual meshes — I did not want to assert it from the ordering.

4. **roof-skirt — a user SWITCH, available whenever `A > C`** (Patrick,
   2026-11-22). Confirmed: the roof-skirt IS the strip of host roof in front of
   the dormer face. It is its own control — an on/off switch, independent of the
   face type — that, when on, joins the host roof from the face out to the host
   eave (A), closing the gap in front of the face to the eave line. Its
   availability is the `A vs C` axis, DIFFERENT from the face type's `C vs D`:
     - **`A > C`** (host roof shows in front of the face) → skirt **available
       (S)**. This covers the plain case you named — `C = D` with `A > C` (W49,
       W52, W65, W71): the face sits at the wall and a skirt can join the eaves
       in front of it — plus every set-back row, plus the `C > D` rows whose face
       is past the WALL but short of the EAVE (W01, W07, W25, W37; note 7).
     - **`A < C`** (face past the eave in plan) → no host roof in front
       horizontally, but a skirt may STILL bridge if the host eave sits below the
       dormer (**S°**, notes 7b/7c): W09, W31, W53, W68.
     - **`A = C`** (face exactly at the eave) → a zero-width, purely vertical
       edge, skirt unavailable (**—**): W40, W61, W72, W75.
   **Balcony + skirt behind A.** A balcony set back from the eave can ALSO carry
   a skirt: the deck is cut from the face out to the balcony's front wall, and
   the host roof from that front wall out to the eave (A) can remain as a skirt.
   So balcony (cut deck) and roof-skirt (strip behind A) are not exclusive.
   **Other `A/B/C/D` combinations for the skirt are to be specified later**
   (Patrick). **Not yet coded** — today a set-back strip renders only because the
   host is not cut there; there is no on/off switch. This is a control to ADD.

5. **Unbuildable rows carry no render rule** — a `no` row (49 of them) builds no
   dormer at all (`C > B` or `D > A`), so Table 2 lists only the 26 buildable.

6. **Code references** (all in `floorplanner/viewer/fp3d.py` unless noted):
   `classify_face`, `face_past_eave`, `host_extent`
   (`floorplanner/parametric/dormer_geometry.py`); `_dormer_face`,
   `_dormer_cheeks`, `_cantilever_floor`, `_balcony_terraces`,
   `_cells_minus_terraces`, `_balcony_overhang_deck`, `WALL_H`.

7. **`A vs C` cuts across the `C vs D` face type (the `‡` cells).** Four rows —
   W01, W07, W25, W37 — are `C > D`, so `classify_face` calls them CANTILEVER and
   the face column reads **H** (hangs to the attic floor); yet `A > C`, so the
   face is past the WALL (D) but still short of the host EAVE (A), host roof
   remains in front, and the skirt is available (**S**). A face cannot both hang
   over open air AND sit under a strip of host roof — which it is turns on
   whether the cantilever boundary is the WALL (D, what `classify_face` uses
   today) or the FASCIA/eave (A, what `DORMER_CONTROL_SPEC.md` R3b describes).
   This is exactly the wall-vs-eave question `0361-report.md` §4 flagged for this
   stage; the roof-skirt switch brings it to a head. The true overhangs — face
   past the eave, `A < C` — are only W09, W31, W53, W68.

7b. **roof-skirt has a VERTICAL dimension the ordering cannot see** (Patrick,
   2026-11-22). `A vs C` is PLAN only — it says whether host roof lies in front
   of the face horizontally. But even when the face is past the eave in plan
   (`A < C`, the overhang rows W09/W31/W53/W68), a roof-skirt can STILL be built
   if the host eave A sits BELOW the cantilevered dormer: a skirt roof then
   bridges from the dormer down-and-in to the eave, closing the underside with
   roof instead of the flat cantilever floor (§8.4, `_cantilever_floor`).
   Whether the eave is below the dormer is an ELEVATION question (host eaves
   height vs. the dormer's face/eave height) that the edge ordering does not
   encode — so those rows read **S°**, not a flat —. In the generated base
   design the host eave and the cantilever base are coplanar at the LV2 floor
   (108″), so there the skirt is degenerate; a host eave drawn LOWER than the
   dormer level is the case you describe. Net switch spec: **a roof-skirt is
   available when host roof lies in front in plan (`A > C`), OR when the face is
   past the eave in plan (`A < C`) AND the host eave lies below the dormer
   face.** The one plan relation that still forbids it outright is `A = C` (the
   face exactly at the eave — a zero-width, purely vertical edge, not a skirt).

7c. **§8.4 floor vs skirt — the open decision (`U∥S°`).** A true-overhang row
   (`A < C`: W09, W31, W53, W68) has its underside closed in one of TWO ways,
   and they are alternatives, not both:
     - **U** — the flat cantilever floor/soffit at the attic level (§8.4,
       `_cantilever_floor`). This is what the builder lays TODAY.
     - **S°** — a bridging roof-skirt down to the host eave, possible only when
       the host eave sits below the dormer (note 7b).
   Which one the roof-skirt switch selects when both are possible is a stage-3
   decision — turning the skirt ON should REPLACE the §8.4 floor for that dormer,
   not stack on top of it. The `U‡` rows (`A > C`: W01, W07, W25, W37) hit the
   prior question first: if their face actually sits on the host (eave boundary,
   note 7), there is no overhang to close at all and the §8.4 floor is spurious.

8. **The skirt SWITCH — an ENUM with `auto`, a dialog selector** (Patrick,
   2026-11-22). The roof-skirt is a stored USER control, the sibling of
   `face_mode`: an ENUM **`skirt_mode`** with values **`auto` / `on` / `off`**,
   default `auto`:
     - **`auto`** — render the skirt where it is AVAILABLE (note 7b: host roof
       in front, `A > C`; or `A < C` with the host eave below the dormer), and
       not where it is not. The derive-from-geometry default.
     - **`on`** — force the skirt (choosable only where it is available).
     - **`off`** — never render a skirt.
   Wired the same three places as `face_mode`:
     - **State + default.** `skirt_mode` in `dormer_geometry.STATE_DEFAULTS`,
       normalised in `normalize_state` beside `face_mode` / `anchored`
       (`dormer_geometry.py` ~line 44/66), clamped to the enum the way
       `face_mode` is (line 66).
     - **Dialog.** A `ParamSpec(… ENUM …)` "Roof skirt" SELECTOR in `dormers.py`
       `specs()`, next to the `face_mode` one (line ~83), choices Auto / On /
       Off — where the R3e face-type selector already sits.
     - **Schema.** Declare `skirt_mode` (enum `auto`/`on`/`off`) in
       `$defs/dormer_state` in `floorplanner/design/design-schema.v6.json`
       (line ~505) — additive, "declared, not enforced" (the state object is
       `additionalProperties: true`), no version bump, like the other
       dormer-state keys. (Add `face_mode` there too — it is also undeclared.)
   **Disabled when no skirt is available** (Patrick): the selector GREYS OUT for
   a dormer whose geometry offers no skirt — `A = C`, or `A < C` with the host
   eave NOT below the dormer. Availability is a dialog/3D-time reading of the
   host-roof EXTENT + the eave ELEVATION (the plan `A vs C` alone cannot settle
   the `A < C` case — note 7b), best factored into a small
   `skirt_available(st, host…)` helper the dialog calls to enable/disable the
   field — exactly as `classify_face`'s `supported` flag drives the face-type
   field today (`dormers.py` ~line 185-207). A disabled selector reads back as
   `auto`, which resolves to OFF since nothing is available. The builder
   `fp3d._dormer_roof_records` reads `st.get("skirt_mode")` beside `face_mode`
   and feeds it to the dormer clip. **Not built this stage** — product code is
   stage 3; this records WHERE and HOW, matching the `face_mode` wiring that
   already works end-to-end.

