# 0312 — report: the L1 door under a front dormer no longer fills in 3D — swept to `main`

**Code, 2026‑11‑10.** The record ([`0197-ruling.md`](0197-ruling.md) §7). On his
word 2026‑11‑10, checking `little-dormer-test.json`: *"when I look at the 3D view
on the front of the house I see that the door on L1 is being filled in by some
surface. Find the issue there."* Found, fixed, and swept to `main` **directly**
on his word *"land the door fix direct to main first"* — a localized 3D-build
correction with a regression test. GREEN. (No **Landed:** line — not a PR merge.)

## 1. WHAT HE SAW

On his two-dormer test plan, the L1 front **door** (the exterior wall `w15`,
`(288,780)–(420,780)`, code `3280`) rendered as a solid light panel in 3D,
while every window on the same wall read as a clean recessed void. A front-facing
dormer stands directly over that door.

## 2. THE CAUSE

The front wall is an **eaves** wall of the main roof, but it runs **perpendicular
to the front dormer's ridge**, so it is a GABLE wall of that dormer and climbs
into it (`_wall_under_roofs`). The dormer's **face window** (`sill_in` 132″)
projects onto this wall as a climb-band: the gable wall *below* the dormer window.
That under-sill was built **solid from the floor (`z0`) up to the window sill** —
and because the door sits directly beneath the dormer window, the solid closed it.
Proof (on the fixture): the door's opening volume held **124** solid
`walls:exterior` triangles; deleting the dormers dropped that to **0**; the
dormers' face windows carry exactly `sill_in = 132`, the fill height.

The host wall is ALREADY built with its own openings (piers, the door void, its
header) by the ordinary-opening loop, so the climb-band under-sill was both
**redundant below the wall top and wrong over the door** — it re-filled a hole
the host wall had correctly cut.

## 3. THE FIX

`floorplanner/viewer/fp3d.py`, the climb-band under-sill (`build_model`'s wall
loop): the under-sill is now **split by the host wall's own openings**. Over a
host door or window it starts **above the host wall top** (`z1`) — leaving that
opening its void and its header, which the ordinary loop already drew — and
climbs on up to the dormer sill. Everywhere else it fills from `z0` **exactly as
before**. So:

- **no host opening below** (a plain gable wall under a dormer window): a single
  full piece from `z0`, byte-identical to before — the set-back "fills up to the
  sill" case and the closed-gable case are untouched;
- **a host door/window below**: the opening keeps its hole and header; the gable
  wall above the opening (`z1` → sill) still climbs and closes the dormer gable.

## 4. VERIFICATION

The door-hole fill on the fixture went **124 → 0** triangles; the gable directly
above the door head stays solid (it climbs to the dormer). New regression test
`tests/test_p5_dormer_face_windows.py::test_a_host_door_under_a_dormer_window_is_not_filled`
(a centred host door under the dormer face window: a ray through the door at
mid-height meets nothing; a ray above the door head meets the climbing gable).
The existing P5 suite — including `test_the_face_window_undersill_fills_up_to_the_sill`
and `test_the_gable_stays_closed_below_and_above_the_face_window` — is unchanged
and green. `python -m ruff check` clean; the viewer / dormer / ceiling / roof-clip
suites pass. Full gate GREEN.

## 5. NEXT

His to check in the real app (open `little-dormer-test.json`, read the 3D front —
the door is a clean opening now). Still waiting on his side: the gable-end
Elevation **both-floors** work is held on branch `gable-end-openings` (PR #108,
AMBER) — report [`0311`](0311-report.md) landed its first round; the second round
(the storey above read and lifted) is staged for that branch's single commit,
pending his go-ahead to amend and force-push. 0248's items 8–9 named, not ordered.
