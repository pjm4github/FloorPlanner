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

## Table

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
