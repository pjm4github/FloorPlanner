# 0361 — report: dormer edge-ordering cases, stage 1 (four read-back cases)

**Code (Claude Opus 4.8), 2026-11-21.** Answers [`0360`](0360-ruling.md) §6
(the four read-back cases, then stop). Tier: **evidence only** — one generator,
design files, PNGs under `docs/evidence/0360-dormer-orderings/`; no change to
`floorplanner/`. The table [`../DORMER_EDGE_ORDERINGS.md`](../DORMER_EDGE_ORDERINGS.md)
and the ruling are landed by path in the same commit.

> **Number note.** `dormer_geometry.py` (`side_profile`, commit `0d06a73`) cites
> "(Patrick, 0361)" for the dialog side projection, but no `0361` handoff was
> ever filed and nothing in STATUS/README claims it. 0360 §6.2 says "report at
> the next free number," which is 0361, so this report takes it. If you meant
> 0361 for the side-projection ruling, rename either — flagging it rather than
> leaving a gap.

## 1. What was built

The four cases 0360 §6 names, and nothing else:

| ID  | Ordering      | Face type (app) | A | B | C | D | host eave-overhang (A−D) | face overhang (B−C) |
| --- | ------------- | --------------- | -: | -: | -: | -: | -: | -: |
| W01 | A > B > C > D | cantilever | 120 | 96 | 72 | 48 | 72 | 24 |
| W05 | A > D > B > C | setback    | 120 | 72 | 48 | 96 | 24 | 24 |
| W09 | B > C > A > D | cantilever |  72 | 120 | 96 | 48 | 24 | 24 |
| W75 | A = B = C = D | standard   |  48 | 48 | 48 | 48 |  0 |  0 |

All four distances are in plan inches from the anchor. **Every number above is
READ BACK from the built design** (§3), not the number the script set — and in
each case the six pairwise relations reproduce the table row exactly
(`reproduces=True` for all four). The pictures are
`docs/evidence/0360-dormer-orderings/Wnn.png`; the loadable designs are
`Wnn.json` beside them.

The app's face classification (`dg.classify_face`) is recorded as a FACT, not
judged (that is stage 2): W01 cantilever, W05 setback, W09 cantilever, W75
standard. See §4 for what drives it — it matters for the mapping.

## 2. The base design — TWO levels (0360 §3 + Patrick's 2026-11-21 addition)

Same for every case; only the four distances change. **Patrick's 2026-11-21
addition:** the dormer is a furnishing on the UPPER level **LV2**, with the host
roof and house a storey below on **LV1**, and the dormer's own **face wall and
two cheek walls are drawn on LV2** to match its face and cheeks — the real
furnishing-dormer model, where the user's upper-level walls rise into the gable.

- **LV1** (elevation 0, storey height 108 in): a plain rectangle **360 × 288
  in**, four exterior walls, and the **12:12 gable host roof** — ridge down the
  middle along the 360-in axis, slope 1.0 (a plan inch along the fall line is an
  inch of height, so the distances read straight off the surface). **Half-span
  (ridge → eave wall) 144 in; eave-wall height 108 in** (= the LV2 floor, so the
  roof bears on the LV1 walls); ridge height 252 in. **D (the wall below)** is
  the faced LV1 wall.
- **LV2** (elevation 108 in): the **symmetric gable dormer**, square to the host
  eave (no rotation), span 60/60. Its host is the LV1 roof, found a storey down
  (`host_roof_at` looks one level below). Its pitch is **7:12** — shallower than
  the host so its eaves stay above the LV2 floor even when the case puts it low
  on the roof. The **face wall** (across the side guides at the face) and the
  **two cheek walls** (each from the face back along a guide to the anchor) are
  drawn on LV2.
- **The level does not change the distances.** The four edges are plan
  distances; the datum shift between LV1 and LV2 cancels in `host_extent`, so
  every read-back below is identical whether the dormer sits on LV1 or LV2
  (verified — `reproduces=True` unchanged).
- **Why it fits all 26** (not just the four): every `D` is ≤ 96 in, and
  `D < 144` (the half-span) keeps the anchor on the roof (its perp from the
  ridge is `144 − D ≥ 48`). The dormer ridge is pinned to the host surface at
  the anchor, so it is always below the host ridge — `OVER_RIDGE` cannot fire.
  No dialog cap is reached.

## 3. How the distances are set, and read back

**Anchor and face.** `pos` is the **anchor** (apex), a point ON the host roof;
the face is `depth_in` DOWNHILL of it along the ridge (`items.py`:
`pos_face = pos − ridge_direction·depth`). Distances are measured from the
anchor toward the face, all positive.

**The ladder (0360 §4).** From the ordering string: the closest group is 48 in,
each step farther out adds 24 in. Tied edges get the SAME number (exactly
equal); separated edges differ by ≥ 24 in (≥ the 12-in floor). So W01's four
levels are 48/72/96/120, W75's one level is 48 all round.

**Setting four numbers through three controls + the anchor.** The base host is
fixed; per case the script sets

- `depth_in = C`
- `face_overhang_in = B − C`
- host roof `overhang_in[faced] = A − D`
- anchor perp from the ridge `= 192 − D`

**Read-back (the numbers in §1).** Build the house + dormer in a headless
scene, then from `DormerItem.param_context()` take `host_z_face_in`,
`host_slope`, `host_eave_in`, `host_ridge_in`; `dg.host_extent(...)` gives
`eave_y`, and

- `D = depth_in − eave_y`
- `A = D + host overhang (faced side)`
- `C = depth_in`
- `B = depth_in + face_overhang_in`

The read-back reproduces the set numbers to the inch in all four cases, because
the surface is analytic and the ridge is pinned to the host at the anchor.

**In the plan file itself.** Each `Wnn.json` carries the case ID + table
ordering and the closest→farthest ordering as two **text annotations** (kind
`text`, the T tool) on LV2, and opens with LV2 active — so the labels show in
the app, not only on the review PNG (Patrick, 2026-11-21).

## 4. The edge mapping (0360 §4) — confirmed and CORRECTED

0360 §4 gave an unverified reading. Measuring the built designs:

- **CONFIRMED** `B − C = face_overhang_in` — exact in every case.
- **CONFIRMED** `A − D = the host roof's eave overhang past the wall below` —
  exact; it is the host roof's own `overhang_in`, nothing the dormer carries.
- **CORRECTED** "`A` is what `host_extent` / `host_eave_in` already carry." It
  is not. `host_eave_in` is `RoofItem.eaves_h_in`, and `roofclip.surface_height`
  puts that height at the **WALL line** (`perp = span`), not at the fascia. So
  `host_extent`'s `eave_y` locates **D (the wall below)**, NOT A. The physical
  host eave **A** (the fascia) is `overhang` farther downhill and is carried
  ONLY by the host roof's `overhang_in` — the script adds it (`A = D + overhang`).
  In short: **`host_extent` → D; A = D + host overhang.**
- **CONFIRMED** `D` is the wall below — but it is the wall the host bears on
  (`host_eave_in`'s own line), which the "wall below" probe also sits on.

**Consequence, recorded as fact (stage 2 is yours).** `classify_face` /
`face_vs_host_eave` key off `host_eave_in` — i.e. off **D, the wall line**, not
off A (the fascia). So the app's cantilever/setback boundary is at the WALL:

- C past the wall (`C > D`) → **cantilever** — W01 (C 72 > D 48), W09 (C 96 > D 48).
- C inside the wall (`C < D`) → **setback** — W05 (C 48 < D 96).
- C at the wall (`C ≈ D`, within 6 in) → **standard** — W75 (C = D = 48).

Whether "cantilever past the WALL" (rather than past the fascia A) is the right
rule is exactly a stage-2 question. It is flagged, not fixed.

## 5. How the picture is captured

Each `Wnn.png` stacks three bands, drawn with the repo font (`assets/fonts`):

1. **Plan** — the scene rendered by its own items, then an overlay: each of
   A/B/C/D a coloured line across the dormer at its edge, a bold letter, a
   legend giving the edge name and its distance, the anchor as a dot, and a
   dashed fall-line from the anchor through the marks. A top band carries the
   **case ID** and the **ordering closest → farthest** (e.g. W05 is
   `C < B < D < A`) above the legend. **LV2 is the active floor, so the dormer's
   own face and cheek walls draw solid; LV1 (the house and host roof) ghosts
   below.**
2. **3D** — the whole house via `fp3dq --shot` (its own process, real platform),
   **yaw 25 / pitch −14**, looking at the DORMER (faced) side so the face, its
   eave, the host eave and the LV1 wall read together (plan +y is world −y, so
   the camera sits in front of the face, not behind the ridge — Patrick's
   2026-11-21 correction).
3. **Caption** — ID, the ordering string exactly as the table writes it, and
   the four read-back numbers.

The A–D marks and caption are drawn by the generator on the captured image; the
app grows nothing to make them. `make_cases.py` READS the case list (ID,
ordering, Buildable) from `DORMER_EDGE_ORDERINGS.md` — it carries no copy — and
is deterministic and re-runnable (`python make_cases.py` builds the four;
`--all` the 26; `Wnn …` named ones).

## 6. What I expect for the remaining 22

- **All 22 should build and reproduce.** The same closed-form mapping covers
  every buildable row within the base limits (§2). No row needs a tuned case.
- **Face classification will follow C-vs-D** (§4), the wall line — not the
  fascia A. Watch the ties: a row with `C = D` and a wall below may read
  `standard` rather than `wall`; W75 read `standard` (the auto rule took the
  at-eave branch, no plain-wall choice set). These are facts for your stage-2
  column, not faults.
- **One fixed 3D angle may not suit all 26.** A deep setback tucks the face
  behind the host roof; a far cantilever throws it forward. If a row's 3D hides
  the face I will set a per-row yaw/pitch when I build the 22 — no geometry
  changes, only the camera.
- **Openings/shape features are out of scope** here (no windows in these cases).

## 7. State — AMBER, your check (0360 §6.3, §8)

Four pictures for four cases; format and mapping settled on four, not
discovered on twenty-six. On your word I build the other 22, write the full
`INDEX.md` (all 75, with the `no` rows' reasons and an empty `Patrick's check`
column), and file a second report. A picture that fails your check comes back
through the reviewer with its ID.

Landed by path (evidence only): `docs/evidence/0360-dormer-orderings/`
(`make_cases.py`, `W01/W05/W09/W75` `.json` + `.png`), the table, this report,
and the `0360` ruling. Gate GREEN. No `floorplanner/` change.
