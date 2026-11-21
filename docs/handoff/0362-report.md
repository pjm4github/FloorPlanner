# 0362 — report: dormer edge-ordering cases, stage 1 COMPLETE (all 26 + INDEX)

**Code (Claude Opus 4.8), 2026-11-21.** Answers [`0360`](0360-ruling.md) §6.4
(the other 22, the full `INDEX.md`, a second report), on Patrick's word "build
the other 22". Follows [`0361`](0361-report.md) (the first four + the base
design). Tier: **evidence only** — designs, PNGs and `INDEX.md` under
`docs/evidence/0360-dormer-orderings/`; no `floorplanner/` change.

## 1. What was built

**All 26 buildable rows are built** — the four from 0361 (W01/W05/W09/W75) and
the other 22 — each on the same **LV2 base design** (0361 §2: the dormer a
furnishing on LV2 with its face + cheek walls, the host roof + house on LV1 a
storey below). Every case:

- **reproduces its table row exactly** — all 26 `reproduces=True`, the four
  read-back distances giving the row's six pairwise relations to the inch;
- **renders** — all 26 3D shots succeeded at the one camera (yaw 25 / pitch −14);
- carries its **plan + 3D + caption** PNG and a **loadable JSON** with the
  W-number and ordering as text annotations on LV2.

The **49 unbuildable rows are NOT built** (0360 §2) — `INDEX.md` lists each with
the table's reason and no image. Nothing was tuned; no case was skipped.

## 2. `INDEX.md` — all 75 rows

`docs/evidence/0360-dormer-orderings/INDEX.md`: one row per ID (W01–W75). A
buildable row carries the four read-back distances, the app's face
classification (`dg.classify_face`), the findings, and a link to its PNG; an
unbuildable row carries the table's reason and no link. The last column,
`Patrick's check`, is **empty** for you.

## 3. Face classification at scale — the §4 reading holds

0361 §4 found the app keys cantilever/setback/standard off **D (the wall line)**,
not the fascia eave A. Across all 26 it is exactly `C` vs `D`:

- **cantilever** (`C > D`, face past the wall), 10: W01 W07 W09 W25 W31 W37 W40
  W53 W61 W68.
- **setback** (`C < D`, face inside the wall), 10: W02 W05 W08 W26 W29 W38 W41
  W51 W62 W67.
- **standard** (`C = D`, face at the wall, within 6 in), 6: W49 W52 W65 W71 W72
  W75.

No exceptions — the boundary is the wall `D` in every case. Whether that is the
right rule (vs. the fascia `A`) remains your stage-2 call; recorded as fact.

## 4. Findings — both ADVISORY, recorded as facts

- **`dormer.cantilever`** (advisory) on exactly the 10 cantilever rows above —
  the face projects past the host eave edge.
- **`dormer.no_full_height`** (advisory) on **every** one of the 26. It fires
  because the test dormer's ridge sits at or below the LV2 ceiling, so it "adds
  no full-height floor". This is a property of the **base dimensions** — the
  dormer is deliberately small (span 60, pitch 7) so its eaves stay above the
  LV2 floor even for a case that puts it low on the roof — not of the edge
  ordering, and it is uniform. If you want the test dormers sized to clear the
  ceiling (no advisory), that is a one-line base-design change for stage 3; it
  does not affect the four distances. No ERROR or WARNING finding on any
  buildable row.

## 5. Against 0361 §6's expectations

- "All 22 should build and reproduce" — **held**: 26/26 build, 26/26 reproduce.
- "Face classification follows C-vs-D" — **held** exactly (§3); the ties read
  `standard`, as predicted.
- "One fixed 3D angle may not suit all 26" — in fact **yaw 25 suited all 26**:
  a setback tucks the dormer into the roof and a cantilever throws it forward,
  but the face reads in every shot (e.g. W51, a `B=C` setback; W53, a cantilever
  on a tie). No per-row camera was needed.

## 6. State — stage 1 COMPLETE; AMBER for your check

Stage 1 (0360) is done: the generator, all 26 designs + review images, and
`INDEX.md`. **Next is yours — stage 2:** add the rules column to
`DORMER_EDGE_ORDERINGS.md` (what the face / balcony / cantilever / roof skirt /
floor-under-balcony do per row). **Stage 3** (a later ruling) then checks the
dormer code against those rules, reusing these same cases and `make_cases.py`.

Landed by path (evidence only): the 22 new `Wnn.json` + `Wnn.png`, `INDEX.md`,
`make_cases.py` (now writes the index + records findings), and this report. Gate
GREEN. No `floorplanner/` change.
