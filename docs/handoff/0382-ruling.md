# 0382 — ruling on 0381. The code is accepted. The census is not: it names 3 changed cases and there are 22. The evidence is still owed. Patrick's look can start now.

2026-11-26 (23:59 local), reviewer session. Read: `dormer-climb-floor-0372` at
`c2b4c33` against `2f39c90`, loaded from the repo by path. Mine, not the
record: reproduce it.

## 1. Accepted: A and B's corner, as committed

Every figure in 0381 §2 reads the same here:

| Read | `2f39c90` | `c2b4c33` |
|---|---|---|
| W01 cheek x = 120, y 98 … 134 | 149.5 … 116.5 | identical |
| frozen posts (797, 812), (947.5, 812) | 200.4, 200.0 | 134.2, 134.2 |
| frozen fins (790, 780), (955, 802.5) | 195.7, 195.0 | 120.0, 110.2 |
| frozen face (872, 805.5), cheeks (795, 740), (799, 640) | 250.4, 199.0, 211.2 | identical |
| lean-to face base at x 803, 810, 942 | 134.0 | 134.0 |
| hipped face base at x 803, 810, 820, 925, 942 | 134.0 all | 124.0, 128.7, 134.0, 134.0, 123.7 |

Over the 31 evidence cases with walls: no mesh but `walls:*` differs, no wall
top is raised, no wall top changes inside a grown box. The gate file reads
GREEN, 2739 collected, both modes.

## 2. Not accepted: 0381 §4's census

**Wall-top reductions.** You report them "only in the class-2 cases (W02, W08,
W26)". On a 2 in grid I find them in **22 cases**, the same 22 as 0375 §3:

| Class | Cases | Fall |
|---|---|---|
| 1: LV1 wall under the eave overhang beside a cheek | W01 W07 W09 W25 W31 W37 W40 W49 W52 W53 W61 W65 W68 W71 W72 W75 | 4–13 in |
| 2: LV1 wall in front of the face, under the rake | W02 W08 W26 W38 W41 W62 | 28–74 in |

Your census missed 19 of 22. Say what it sampled and why it could not see a
4–13 in fall, or a 70 in one in W38, W41 and W62.

**B's below-base material.** You report 8 cases. A cruder read here (lowest
wall z changed where the top did not) finds it in 15. Mine may over-count;
reconcile the two and say which instrument is right.

**The evidence.** 0375 §3 ordered each changed case's PNG regenerated.
`c2b4c33` touches four files and none is under `docs/evidence`. Owed: the 22
PNGs, and INDEX rows giving each case's class and fall.

## 3. The lean-to test that runs only on this machine

You asked for the word: yes. A test that is skipped wherever the user's file is
absent is not in CI. Cut a committed fixture from the frozen file: only the
walls, the two roofs and the dormer the case needs; no rooms, furnishings,
annotations or cameras; named for the case, not for the plan. Show it RED on
0379's `roof_beneath` and GREEN now. If the reduced file stops reproducing, say
which removed element it was; that is the answer to "why a small scene does
not".

## 4. Recorded, not ordered (call it B2)

On the hipped file two floor tabs still hang in the air at the front corners,
outside the hips: x 784.8–791 and 953.5–959.2, y 810–816, z 133–134. They are
the §8.4 floor under the dormer's OVERHANG, where there is no attic to close.
Not for this PR. It is ruled with C, D and E.

## 5. Patrick's look, and the merge

His look starts now; nothing in §2–3 changes code. If any of it does change
`fp3d.py`, the look is void and is done again. In the app, from this branch:

1. `...\wiscaway-roof-build\readback-BR3-dormer-rake12.json`: front and both
   sides. No posts at the front corners; plain cheeks.
2. `...\wiscaway-roof-build\readback-BR3-dormer-hipped.json` (new, the same
   plan with `rf4` hipped): both lower corners of the face wall closed.
3. `docs/evidence/0360-dormer-orderings/W02.json` beside its old `W02.png`: the
   wall in front of the dormer face is gone.

Merge needs all three of: his word, §2 and §3 done, the gate GREEN on the tip.
Then C, D, E as 0372 ordered.
