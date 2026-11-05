# 0298 — report: checkpoint 0 of the 1½-storey arc — the load fix recorded, the three unmeasured items measured, the ground cleared

**Landed:** PR #103 · 3761819 · 2026-11-05 · AMBER · the cross-level dormer LOAD fix (`bridge.py` accepts a host on the dormer's floor or the one directly below); 3 regression tests, full gate GREEN; recorded here per 0293 §0, his word for the arc ([`0297`](0297-ruling.md))

**Code, 2026‑11‑05.** The record ([`0197-ruling.md`](0197-ruling.md) §7). This closes
**checkpoint 0** of the 1½-storey arc ([`0297`](0297-ruling.md) §0); the rulings
`0293`–`0297` were committed first as one doc-only commit (`4b12fff`), then this.

## 1. THE LOAD FIX, RECORDED (0293 §0, 0297 §0 item 2)

`3761819` landed with no numbered report; this records it. **Commit** `3761819`
("Cross-level dormer load: accept a host a floor below…"), fast-forwarded onto
`main` from PR #103. **Test** `tests/test_dormer_crosslevel_load.py`: a dormer
hosted a floor below survives the load; a same-floor dormer still loads; a
host-ABOVE dormer is still skipped. **His word**: the arc's rulings order it
reported and built on (0293 §0). It fixes `design/bridge.py` `_build_roofs`,
which dropped any dormer whose host was not on its own floor — contradicting the
cross-level model PR #101 landed — so a re-levelled dormer vanished on reload
(0292 §2). The loader now accepts a host on the dormer's floor OR the one
directly below, from the doc's own level elevations.

## 2. THE THREE UNMEASURED ITEMS — MEASURED (0297 §0 item 4; 0293 §1)

A reviewer's reading is testimony until measured (WORKING_AGREEMENT). Instrument:
`docs/evidence/1p5-storey-checkpoint0/measure.py`, headless on
`fixtures/incoming/little-dormer-test.json` (the arc's fixture; `rf2` a dormer on
L1 hosted on `rf1`, L2 present at elevation 96). Verbatim:

```
setup: host rf1.floor=L1  dormer rf2.floor=L1
M1 level_base_in: dormer-on-L1=0.0  host_base=0.0  dormer-on-L2=96.0  OVERSTATED_BY=96.0
M2 roof_clip_spans(L2 wall w20): spans=0   L1 roofs present=2 (excluded by it.floor==wall.floor)
M3 dormer_defaults read rooms on floor(s): ['L1']   (host.floor=L1; the dormer serves the floor ABOVE)
```

* **M1 — `RoofEndOnDialog.level_base_in()`.** Reads `roof.floor`. For a dormer
  promoted to L2 over an L1 host it returns **96.0** (L2's base) while the host's
  base is **0.0** — the dialog's absolute heights are **overstated by 96″**, the
  L2 elevation, exactly where `fp3d` lifts the dormer by the host's base. Fixed
  in P3 (0293 §5 P3 i; 2c).
* **M2 — `roof_clip_spans`.** For an L2 wall (`w20`) it returns **0 spans** though
  **2** L1 roofs stand present, excluded by `it.floor == wall.floor`. An L2 wall
  under the L1 roof gets no R3b dash. Fixed in P2 (0293 §2b, §5 P2).
* **M3 — `dormer_defaults`.** Reads rooms on floor **`L1`** (the host's) via
  `_floor_rooms(scene, host.floor)` — the floor BELOW the rooms the dormer serves
  (its drawn level, L2). Fixed in P3 (0293 §5 P3 iii).

**Would `check(deep=True)` have fired on any of this? No — a limit, not a gap**
(0293 §1): the invariants know nothing of heights or of 3D. The instrument for
this class is the headless build with a receipt, which every phase is gated on.

## 3. THE GROUND CLEARED (0297 §0 items 3, 5)

* **`_to_delete/` emptied** — the one tarball removed.
* **Fixtures.** `fixtures/incoming/little-dormer-test.json` is present (modality 2:
  roof + dormer on L1, L2 present with four walls); **P3–P5 run on it.**
* **The wiscaway R-file is NOT yet usable for P1/P2.** He saved
  `fixtures/incoming/wiscawayL2-fix.json`, but **its L2 `height_in` is still 196″,
  not 96″** (verified: `levels` L2 elevation 100, height 196). A receipt on a 196″
  storey measures his workaround, not the rule (0293 §6 item 1). **P1 and P2 stay
  RED** until L2's height is 96″ — his gesture to make, his file to keep
  (uncommitted; no test references `incoming/`, D51).

## 4. NEXT

P1 — the stacked climb (3D), on the wiscaway R-file **once its L2 height is 96″**
(0293 §5 P1, 0297 §2). The next phase does not open until this report is on disk
(0297 §6); it now is. The two schema-text corrections (0293 §0 item 2) land in
P3, where the dialog and datum are touched, not here.
