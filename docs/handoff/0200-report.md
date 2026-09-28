# 0200 — report: PR #67 merged on his word; R6.b — the building's one roofscape, composed in absolute height; its cost measured and fixed; AMBER, stopped for his check

**Code, 2026‑09‑27, on [`0197-ruling.md`](0197-ruling.md) §5 and
[`0186-ruling.md`](0186-ruling.md) §4.** First the record (0197 §7):
Patrick's check of PR #67 passed — his words, *"This is all correct. Go
ahead and merge this."* — and on that word `roofs-r6a-display` was landed
on `main` at `1262530`, fast-forward, the branch deleted local and
remote. R6.a is closed. His next word: *"proceed with R6.b."* Branch
`roofs-r6b-composition` off `main` at `1262530`, PR #68 open, gate
GREEN, **stopped for his check** (§5).

## 1. WHAT'S BUILT — the same rules, one more term in z

0186 §4: *"composition runs in absolute height — a roof's surface is its
level's `elevation_in` plus its own heights — and the envelope / prune /
under-pass machinery runs over all live roofs of the building, not per
level. The same rules, one more term in z; no new geometry class."*
Built exactly so: **`compute_roof_clips` is not changed by one rule.**

* **`roofclip.Lifted(roof, dz)`** — a view of any roof (a `RoofItem`, a
  `RoofGeom`) with its two heights raised by its level's elevation;
  everything else is the wrapped roof's own. Pitch is a difference of
  the two heights and every plan quantity is untouched, so only
  comparisons *between* roofs change. **`compose_building([(roof,
  elevation), …])`** lifts, clips, and returns the clips keyed by the
  roofs given.
* **The editor.** `roofs.sync_roof_clips` composes every live roof in
  the scene; its `floor` argument stays in the signature (every caller
  names the floor it edited) and no longer scopes anything. Elevations
  come from the floor state — `config.floor_elevation(name)`, mirrored
  from the roster by `_sync_floor_state`, which **re-composes when an
  elevation changes** and only then. The loader primes the elevations
  before the first roof arrives. A bare scene knows none and composes
  at one datum, exactly as one level always did.
* **3D.** `fp3d.build_model` composes every built level's roofs
  together. Each roof's mesh is still lifted from its own geometry by
  its own level base, so no mesh moves; what changes is which ground
  each roof owns, the risers between roofs of different levels
  (absolute heights in, absolute out), and **which roof caps a wall**:
  the territories are the building's, each with its absolute surface
  and its level, so a wall is capped by whichever roof is really over
  it whatever level that roof stands on. **The dormer climb stays on
  the dormer's own level** — a wall a storey below a dormer does not
  climb through the floor between.
* **0164 §2's "same floor only" is reversed**, as 0186 §4 rules; the one
  test that pinned it is rewritten, not deleted (§4).

## 2. HIS FIXTURE, MEASURED — per level against the building

`fixtures/wiscaway-2level-stacked-floor.json`, L1 at 0″, L2 at 100″:

| roof | per level (as `main` composed it) | the building (R6.b) |
|---|---|---|
| rf1 — L1 main, eaves 96 / ridge 296 | 372 556 in², **91.2 %** of its footprint | **96 292 in², 23.6 %** |
| rf2 — L1 45° wing | 177 732, 80.4 % | 177 732, 80.4 % — no upper roof stands over it |
| rf3 — L2, eaves 125 / ridge 335 abs | 233 861, 77.3 % | 233 861, 77.3 % |
| rf4, rf5, rf6 — L2 | 36 043 / 19 903 / 35 958 | unchanged |

**The partition holds across levels:** 0 blank cells of 162 (the `diag`
hook's own invariant), and on a 12″ grid over the union of the
footprints, 4 204 points under some roof — **0 owned twice, 0 owned by
nobody.** What changed is exactly what should: L1's main roof, which per
level believed it owned nine tenths of its footprint, keeps under a
quarter once the four upper roofs standing over it are in the same
composition. The upper roofs lose nothing to the lower ones.

## 3. THE COST — measured, and fixed before it shipped

Composing the building cost **1.66 s** on his fixture against 0.15 s for
its larger level alone, and because every roof added to a scene
re-clipped, **loading the fixture took 7.45 s**; a grip drag would have
stalled the same way at every mouse move. Profiled: **97 % of the time
was `roofclip._adjacent`** — piece-to-piece adjacency by point-to-segment
distances, asked of 56 000 pairs, nearly all nowhere near each other.

Two changes, neither a rule:

* **`_adjacent` rejects by bounding box first.** An edge midpoint of one
  cell within `tol` of an edge of the other puts the two boxes within
  `tol` of each other, so boxes further apart cannot be adjacent — a
  pure prefilter. **Every result is identical to the last printed digit**
  (rf1's region 96 292.103 829 643 63 in² before and after; the same
  seam counts; the same 2 836 mesh faces), and the whole roof suite
  passes unmodified.
* **`hold_roof_clips(scene, on)`** — re-clipping is held while a plan
  loads and while a grip, a ridge or a dormer is being dragged, and the
  building composes once at the release. The dragged roof is selected
  or new, so it draws unclipped through the drag anyway; the others
  catch up when the button comes up.

| | before | after |
|---|---|---|
| the building's composition, his fixture | 1.66 s | **0.20 s** |
| loading his fixture in the app | 7.45 s | **0.71 s** |
| `fp3d.build_model`, his fixture | 2.04 s | **0.50 s** |
| `threeRidgeFloorplan.json` (the 0.36 s named limit of [`0182`](0182-report.md) §5) | 0.36 s | **0.08 s** |

The 0.36 s limit carried since 0182 is discharged by the same prefilter.

## 4. THE CHECK — receipts

`tests/test_r6b_composition.py`, **13 tests** (`walls`). The receipts are
**invariances**, which cannot pass by accident: `Lifted` raises the two
heights and nothing else; **a common elevation changes nothing**;
**lifting a roof a storey while lowering its heights by that storey's
elevation changes nothing** (regions and seams identical to the
single-level L, 76 222.22 in² and the apex at (200, 237.037)); the
converse — the same heights a storey up — takes exactly the ground
stood over (the main loses the 120 × 200 overlap and no seam is left);
in the editor, roofs on different floors compose at their elevations
and the `floor` argument no longer scopes; **changing a floor's
elevation re-composes the building**; a held scene composes once at the
release; his fixture with 0 blank, 0 double- or un-owned grid points and
the six measured areas; the app loading it composed; in 3D, the
roofscape mesh **vertex-for-vertex identical** under lift-and-lower; an
upper-level wall capped at 143.75″ by a lower level's roof rising
through it (196″ without the roof); and a wall a storey below a dormer
staying at its own 96″ while the upper wall climbs into the dormer.
`tests/test_roof_intersection.py`: `test_roofs_on_another_floor_do_not_clip`
is rewritten as `…_compose_in_the_one_roofscape`. Every other
pre-existing test passes unmodified.

Full suite **1383 passed**, 7 deselected (`perf` lane), `ruff` clean,
gate GREEN — the branch's own run.

## 5. HIS CHECK

Open the fixture, 3D view: **one roofscape** — no roof passing through
another, L1's big roofs stopping where the upper roofs stand over them,
the upper walls capped where L1's roofs rise through the upper storey.
In plan, on `default`, L1's main roof now draws only the ground it
really owns.

**One thing in the drawing itself, his to decide:** L2's storey height is
**196″** in the file, and the 3D view reads the storey height as the
level's wall top, so the upper walls build 196″ tall (to 296″ absolute)
wherever no roof caps them. If the upper storey is 96″ tall, Floors ▸
upper ▸ "Elevation and height…" with the height at 96 will show it.

## 6. NAMED — for his ruling, none blocking the check

* **The crossed-arm rule reads the plan, not the height.** An upper roof
  whose ridge end has crossed a lower roof's ridge still takes its
  joined extension over it ([`0184`](0184-report.md): "a crossed end
  never opens") even when it floats a storey above. The synthetic L
  shows it (the lifted wing owns 48 000 in², 6 000 of it extension);
  **his fixture has no such arm** — its upper roofs' regions are
  unchanged. One rule if he wants a floating end to open: the end is
  open when the roof stands above the host's *ridge* there.
* **The R3b wall dash and the R5a trace are still same-level.** A wall on
  L2 is not dashed by an L1 roof rising through it, though 3D now caps
  it. Whether the 2D readings follow the building is his call — it
  changes what each plan shows — and 0197 §4's corollary (a dash never
  without a roof drawn above it) already holds for it, since a covering
  roof draws ghosted.
* **A lower roof hidden under an upper one no longer dashes the walls
  beneath it** (`_within_territory`): hidden ground is a phantom by
  R4d's principle. No wall in his fixture changes by it.
* **Undo on a plan with many roofs pays one composition** (0.2 s here) —
  the restore reloads the document.

## 7. `fixtures/incoming/`, with ages

`README.md` only.

## 8. WHAT HAPPENS NEXT

His check (§5). On his word PR #68 merges, branch deleted in the merge
step. Then, before R6.c is written (0197 §5): **D67 reproduced or
refuted** — one headless run on `roundedMultifloor.json`, drag across
floors, undo, compare floor 1 to pristine — **and the roof-elevation
measurement**: whether the dialog's seeded heights are still right when
the level base is not zero, measured on his fixture. Then R6.c.

**Carried:** unchanged from [`0199`](0199-report.md); 0182 §5's 0.36 s
timing limit discharged (§3).
