# 0367 pyramid-roof — evidence INDEX

The pyramid-roof furnishing ordered in `docs/handoff/0367-ruling.md`. `Patrick's
check` is left empty for him.

## Stage 2 (the item, plan symbol, 3D faces, §3 walls/posts)

| ID | Case | sides | Plan | Image (3D) | Patrick's check |
| -- | ---- | ----- | ----- | ---------- | --------------- |
| E1 | free-standing hexagon gazebo — an exterior room 12 ft across the flats, a 6×6 post at each corner, a six-sided pyramid roof (eaves 96, apex 156) | 6 | [json](E1-free-standing-hexagon.json) | [png](E1-free-standing-hexagon.png) | |

## Stage 3 (the weld)

Where a pyramid and a roof overlap in plan, each is drawn only where it is the
**higher** surface; the boundary is the equal-height line, exact; the lower is
**cut**, in plan and 3D. `weld: off` draws both whole.

| ID | Case | sides | Plan | Image (3D) | Patrick's check |
| -- | ---- | ----- | ----- | ---------- | --------------- |
| E2 | an octagon bay on an eave, mid-wall, under a plain gable — the bay welds into the gable eave | 8 | [json](E2-octagon-bay-on-eave.json) | [png](E2-octagon-bay-on-eave.png) | |
| E4 | a square pyramid astride a ridge — it pokes up at the centre and dies into both slopes | 4 | [json](E4-square-astride-ridge.json) | [png](E4-square-astride-ridge.png) | |
| E5 | E4 with `weld: off` — both drawn whole (the contrast) | 4 | [json](E5-weld-off-both-whole.json) | [png](E5-weld-off-both-whole.png) | |
| E3 | the NOOK on a copy of `wiscaway-c03-roofA-garage.json` | 8 | — owed — | — owed — | |

**E3 is owed with the garage file**, which is not in the repository (it is one
of Patrick's gitignored `fixtures/incoming/` plans). The weld is proven on E2/E4
and timed on the three-roof junction (C2); E3 renders the moment the file is
dropped in. E5 here stands in for E3-with-`weld:off` as the whole-both contrast.

## Conditions

- **C1 — one geometry.** The plan symbol, the dialog, the 3D faces, the
  walls/posts and the weld all read `pyramid_geometry.py` (`plane_height` /
  `surface_height`); no second height formula in `items.py` or `fp3d.py`.
- **C2 — read-back.** `C2-weld-readback.md` (ruled on by Patrick): where the
  weld is computed and why, the cost, and the termination proof —
  `C2-weld-timing.json` from `c2_weld_probe.py` (the 0350 §1 three-roof junction
  + a pyramid welds in 0.94 ms; no `compute_roof_clips`).
- **C3 — differential receipt.** `C3-differential.json` (from
  `c3_differential.py`): every no-pyramid document builds **identically** before
  (branch base `24601ac`) and after — the weld is gated on a pyramid being
  present; `weld: off` draws the stage-2 whole.
- **C4 — fail-first.** `tests/test_pyramid_3d.py`: over the apex the weld leaves
  ONE surface (the roof is cut); with `weld: off` it leaves TWO. Remove the cut
  and the test goes red.
- **C5 — never abort.** A flat-pitch pyramid still loads, draws RED, is noted in
  `model.notes`, holds up no wall or post, and takes part in no weld.

## Reproduce

- `make_e1.py` — E1.  `make_weld_evidence.py` — E2 / E4 / E5.
- `c2_weld_probe.py` — the C2 timing.  `c3_differential.py` — the C3 receipt.
