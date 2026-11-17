# 0351 — ruling: Patrick is changing the dormer's direction — a PLAN is written, nothing is ordered. RED until he decides

**Reviewer (Cowork), 2026-11-16.** Patrick's word tonight: the dormer becomes
a furnishing, like the stair; editing it computes no wall — only the knee
lines; the walls the user draws on the upper level rise to the roof or the
ceiling. "This separates the floorplan from the roof line."

The plan is [`docs/furnishing-spec/DORMER_FURNISHING_PLAN.md`](../furnishing-spec/DORMER_FURNISHING_PLAN.md).
Read it before answering anything about dormers.

## 1. What it says, in four lines

- Phases 1-3 of the 1½-storey arc (absolute-height governance, the knee line,
  the wall that climbs into a dormer) are KEPT — they are the new rule.
- Phases 4 and 5 (minted `dormer` walls with `bound_to`, the weld, windows on
  the dormer record, `DormerWindowItem`) and the generated face and cheeks in
  `fp3d` are RETIRED.
- Old plans are converted on load: minted walls become ordinary exterior
  walls, face windows become wall windows. 23 fixtures, 57 dormers.
- 0350 §2 and the seed plans' ten schema errors are both that machinery and
  go with it.

## 2. Rulings

1. **RED.** No phase starts until Patrick answers the plan's section 8.
2. **Do not fix 0350 §2** (minted walls lose `bound_to`). Record it; the plan
   deletes the code. If Patrick declines the plan, it comes back.
3. **0350 §1 (the clipper that does not return) is NOT covered** by this and
   stays owed as a record with a measurement. The plan's phase 3 leans on
   that clipper.
4. **Phase 0 measurements may be taken now** — they change no code: (a) the
   time to recompute one dormer's and its host's knee trace, per mouse move,
   on `wiscaway2026-11-15R1.json`; (b) the ~165 dormer tests sorted into
   "pins the rule that stays" and "pins minted walls or face windows".
5. On his yes: phase 1 is the reviewer's (pure geometry, furnishings lane);
   phases 2-5 are Code's, each AMBER on his check.

## 3. Owed

- **Patrick:** the six decisions in the plan's section 8.
- **Code:** §2.4, and everything still owed from 0349 and 0350.
