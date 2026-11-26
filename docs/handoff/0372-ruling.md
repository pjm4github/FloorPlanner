# 0372 — ruling: the dormer fixes, realigned to `main` at `ab8aad8`. One workstream, five items, in this order.

2026-11-25 (21:30 local), reviewer session. The RULES of 0370 §3 and 0371 §3
stand. Their ORDER lists and readbacks are replaced by this file, because the
plan they pointed at has moved. Untracked until you file it.

## 1. Patrick's words

*"Look at where Code is and then realign the ruling to get Code to fix the
known errors with the dormers."*

## 2. Where Code is, as read from disk

`main` at `ab8aad8`: 0367 stages 1–3 and the arc, and 0368, landed on Patrick's
word. 0370 and 0371 are filed (`26c9a32`) and not started. Owed from before:
0367 stage 4 (docs) and the E3 evidence. The dormer items below go first;
stage 4 is not blocked by them and does not block them.

## 3. What moved under 0370 / 0371

- Patrick re-saved the plan at 17:58 local. The BR3 dormer is now `f135`
  (was `f129`), the skirt roof is `rf4` (was `rf5`), and he set eave-past-the-
  face to 3. Do not read back against his live file again.
- **Frozen readback file:**
  `C:\Users\pmora\OneDrive\Documents\FloorPlanner\wiscaway-roof-build\readback-BR3-dormer-rake12.json`
  (his 17:58 save with `f135`'s eave-past-the-face put back to 12; eave
  overhang 12). A user plan: read it, do not commit it.
- Re-measured on `ab8aad8` with that file; the fault is unchanged:

| Piece | Plan box (in) | z |
|---|---|---|
| front post, south | x 794.0–800.1, y 804–816 | 0 → 202.4 |
| front post, north | x 944.5–950.5, y 804–816 | 0 → 202.0 |
| cheek fin, south (`w88`) | x 784.8–796.8, y 777–783 | 0 → 200.2 |
| cheek fin, north (`w114`) | x 948–959.2, about y 795–804 | 0 → 199.7 |

- 0371 §5's question (which tree his app runs from) is closed on his word:
  after a restart the four cabinets appear.

## 4. The items

| | Item | Tier |
|---|---|---|
| A | A climbing wall stops under the first roof drawn over it | AMBER |
| B | The §8.4 floor is not laid where a roof is drawn beneath | AMBER |
| C | `compute_roof_clips` does not return: record and measure | record GREEN; fix RED |
| D | D89, the 0360 skirt not showing in the live app: diagnose | diagnosis GREEN; fix AMBER |
| E | Two dormer-dialog findings | AMBER |

**A.** Rule: 0370 §3 with 0371 §3. Do 0370 O1–O4 and 0371 O1 as written.
Readback: in the frozen file, none of the four boxes of §3 holds wall material
above the roof drawn beneath it, and the walls of 0370 O2's control still climb.

**B.** Measured on the frozen file with `rf4` given hipped ends (ridge
x 833–911.5, hip run 36): the `dormer_floor` slab is laid at z 133–134 over
x 784.8–959.2, y 810–816. The hip surface under it is 122 at x 800 and there is
no roof at all outside x 791, so the slab stands 12 in proud at each corner and
hangs in air past the hips. Rule: the §8.4 floor closes OPEN AIR; where a roof
is drawn under the dormer's overhang it is not laid. Failing test first. Then
send a picture of the hipped case and say what shows at the two lower corners
of the L2 face wall (its base is 134, the hip falls to 120). I rule on that
corner after I see it; do not close it on your own.

**C.** 0350 §1 ordered a defect record; `defects/INDEX.md` has none. 0369 says
the opposed-dormer reproduction was filed in `C2-weld-readback.md`; that file
does not mention it. Open the record now with both reproductions: 0350's three
gables, and
`...\wiscaway-roof-build\repro-opposed-dormers-hang.json` (one main roof, two
dormers directly opposite; `build_model` did not return in 75 s on `ab8aad8`,
and returns when the east dormer is moved 72 in). Measure loop or blow-up
(piece count, visits per piece) and propose. No fix until that report is ruled.

**D.** Take the first step D89 itself names. For W09 through the live path
(`fp3dq`), report whether the skirt mesh reaches the scene (entry count, its
box) and a capture from under the eave. Then say absent or hidden.

**E.** Last. Two ADVISORY findings, each giving the number and the value that
cures it; no auto-fix:
1. The eaves line stands N in outside a side wall drawn under the dormer, so a
   second cheek is built there (his BR3 dormer as he had it: 20.75 in).
2. An anchored dormer's ridge is not at the host's surface at its anchor (his
   13:30 plan: the entry gable +5.7 in, the west shed +6.9 in).

## 5. How to run it

A and B on one branch, C and D each their own, E after A–D. Not mechanical:
no Sonnet on A–C. One report per branch. Stop and report on double failure.
Out of scope: dormer meeting dormer on the west side. It has not been measured.

## 6. Patrick's checks, batched

1. After A and B: the frozen file from the front and from each side. No posts
   at the front corners, plain cheeks, skirt and gable face unchanged.
2. After E: open the BR3 dormer's dialog on his 13:30-style settings and read
   the two findings.
