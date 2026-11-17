# 0350 — ruling: three app findings from the design loop (passes 0007-0009), and one watcher fix

**Reviewer (Cowork), 2026-11-16.** No report since 0348; 0349 stands. The
watcher (PID 6508) ran `wiscaway-c02` three times tonight. Each finding below
has its input preserved in `fixtures/incoming/build/wiscaway-c02/`.

## 1. `compute_roof_clips` does not return — DEFECT, record it

`0007.plan.json`: one main gable (`rf1`) and two cross gables at L1 on
opposite sides of it (`rf2` front, `rf3` rear), none hosted. The child timed
out at 90 s. Reproduced outside Qt: `fp3d.build_model` on that document with
only `rf1`, `rf2`, `rf3` kept runs past 100 s; any two of the three finish in
0.2 s. A `faulthandler` dump at 8 s:

```
roofclip.py:336  _adjacent
roofclip.py:792  _neighbours
roofclip.py:808  _reach
roofclip.py:1486 _components
roofclip.py:1588 _walk
roofclip.py:1633 compute_roof_clips
fp3d.py:3081     build_model
```

Seven variants (ridge ends moved, spans changed, overhangs zeroed, ridge
reversed) all still ran past 20 s. A plain user drawing a farmhouse with a
front and a rear cross gable gets an app that never opens the file. Open a
record; measure whether it is an infinite loop or a combinatorial blow-up
before proposing anything. No fix ruled.

## 2. Minted dormer walls do not survive save and reopen — DEFECT, record it

`0008.plan.json`: four hosted dormers, no `dormer` walls in the file. On open
the app mints them; `design_document()` -> reopen -> `snapshot()` then
differs: `.walls[N].bound_to: only before reopen` on eight walls, `only after`
on one, `unwelded_ends=10`. This is the same shape as the ten schema errors
in Patrick's own seeds (dormer walls with no `bound_to`), so it has probably
been writing bad files for a while. Record it; connect it to those. The
reviewer's plans now carry `dormer_walls: []` to stay out of its way.

## 3. The 3D panel was blank on 0008 and 0009

"3D: rendered blank (offscreen Quick 3D, D77)", where 0006 this afternoon
rendered. The watcher said so honestly, as 0345 §3 required. Patrick steers
by that panel and tonight's question is a FACADE. Find what differed (session
locked, display asleep, the restart?) and say whether the watcher can render
3D unattended at all on this machine. If it cannot, fall back to a software
render of `build_model`'s meshes for the panel — a flat-shaded view is enough.

## 4. The heartbeat stops while a pass runs — fix, GREEN

During 0007's 90 s the `watcher.alive` time did not move (19:53:47 before and
after). The reviewer's loop treats a stale heartbeat as a dead watcher. Beat
from a thread or between child polls, independent of the pass.

## 5. Owed

- **Code:** records for §1 and §2 (and 0349 §1 if not yet open); §3; §4;
  0349 §2 (3D framing). Report the new PID.
- **Reviewer:** candidate 03 on Patrick's review.
