# 0182 — report: the under-pass network built; the partition is whole — 0% blank on the three-ridge fixture, D85's corner the L's one legal blank; two facts the rule needed that the ruling did not name, each measured

**Answers [`0181-ruling.md`](0181-ruling.md)**, on the same branch,
`roofs-r4g-full-footprint`, PR #60 (`main` at `7714ae7` merged into the
branch first, so 0177–0181 and the v2 evidence picture are on it). AMBER
continues; **stopped for Patrick's check, which 0181 says follows the 0%
receipt — it is in.**

## 1. Built as ordered — the continuity network

`compute_roof_clips` now certifies a root limb (a connected patch of a
roof's own single-coverage ground the principal anchor's walk did not
reach) iff it connects to the principal through the roof's continuity
network: the pieces the roof is drawn on, plus every piece where its
surface lies below a real roof's drawn one (`_under_pieces`, cut at the
equal-height line where a piece is crossed), by positive-length adjacency
only (`_certify_limbs`). A certified limb anchors a walk of its own and
draws wherever it wins; hidden ground conducts connectivity and never
draws; an uncertified limb prunes with everything only it could reach.

Receipt in isolation, as a new test
(`test_0181_a_root_limb_certifies_by_passing_under_a_real_roof`): a low
gable crossing under a tall one with both ends free. Its far side is real
root ground the plain walk cannot reach (the tall roof's ridge zone wins
between, and that seam blocks). The network certifies it — one limb of
four pieces, measured through the new `diag` hook — and the low roof
draws on both sides, pokes out through the tall roof's slopes near both
eaves, keeps nothing under the tall ridge, and nothing is blank.

## 2. Measured first: the rule as written did not reach 0%, and why

Built literally — a root component certifies iff it connects through
drawn-plus-hidden ground — the three-ridge gap went 15% → 10% and the
L's own 6% blank did not move. Three causes, each measured on the round
trace, none of them in the ruling's own picture of the geometry:

* **D85's corner rode its own wedge.** In the round the network is
  evaluated on, A's wedge past the apex is A's own DRAWN piece; the
  corner sits in the same component; the wedge touches B's real body
  across the valleys, where A is under B — hidden — so the corner
  certified and the poke-through came back. Restricting limbs to root
  pieces alone fixes D85, but then rf3's rake limb touches nothing but
  rf3's own cut-off winning pieces — the ground between the limb and
  rf3's body is not "won outright by rf1/rf2 with no rf3 sub-piece
  involved" ([`0180`](0180-report.md) §4's words); measured, the limb's
  only neighbours are three rf3 sub-pieces standing over rf2's far end.
  So the network's exclusion had to be "above a REAL roof", and the
  corner and the rake limb had to be told apart by something else (§3).
* **Pruning by cell lost ground to nobody.** One cell of the L held both
  A's phantom strip east of the valley and B's extension lens west of it.
  Pruning A from the cell for the strip's sake, then B for the lens, left
  nobody to re-envelope the lens ground A's own body should carry. Fixed:
  a cell holding a piece about to prune first splits into that round's
  pieces (they partition it exactly, each a convex local-maximum region),
  and a roof prunes over its own lost piece only.
* **Simultaneous pruning.** rf3's whole rake-side body was severed from
  its NE body by nothing but rf2's far end — itself a phantom — and both
  pruned in one round. A "judge each roof with every other roof's
  unsupported pieces removed" step was built and measured: on this
  fixture all three roofs rescue one another through each other's
  vacated ground (rf1's east arm reconnects south of the pinch once
  rf3's pieces are gone, and so on), the step degenerates to "prune all",
  and the cascade is unchanged. Removed.

## 3. The two facts that close it — named, measured, not guessed

**A swallowed end that has CROSSED its host's ridge names the phantom.**
A cut-off component holding a ridge end that lies past the crossing of
its own ridge with a host's is a joining end's overshoot: it prunes and
never returns (A's end, 50" past the apex; rf1's east end, 49" past the
pinch — "the rf1 ridge completely intersects the rf2 ridge. So the rf1
ridge will end at rf2", his own reading in [`0177`](0177-ruling.md)). An
end that has not crossed is a JOIN, not an overshoot (B's start sits
exactly on A's ridge; rf2's south end stops 13" short of rf3's ridge) —
its arm is judged like any orphan. Phantoms prune first, one at a time,
the shorter overshoot first; orphans are judged only once no phantom
remains anywhere, when whatever still cuts them off is a real roof, and
root orphans are the limbs the network certifies. Why one at a time: at
the pinch both far arms are point-severed and each is blocked by nothing
but the other. Pruned together, rf1 takes ground south of the pinch and
rf1/rf3 meet in a false seam under rf2's own ridge — the junction 0180
had, with the seam-crossing test failing. Pruned rf1 first (49" before
rf2's 86" past rf1's ridge), rf2's south arm is judged on the
re-enveloped ground, reconnects around the pinch, and runs on to its
end: his v2 picture. The order was first tried as the end's height over
its host ("the end standing highest above the roof it runs into") and
that fails the saddle in isolation — without rf3, rf2's end stands
higher over rf1 than rf1's over rf2, and rf1 survives — so it was
rejected, measured; overshoot past the crossing holds in both settings.

**A joining end's extension never comes back up.** With A's wedge pruned
first, B's walk went body → hip ground under the wedge (B below A's
plane, legitimately drawn as the lower surface) → B's lens behind the
apex, where B's extended ridge is ABOVE A's north slope — and drew it: B's
extension floating over A's real roof. The strip past a swallowed end may
pass from above its hosts' original planes to below them, never from
below back to above (`_reach`'s `no_step` veto, measured against the
original coverers' planes whether or not their own phantom was pruned).
With it the L is exactly `clip_pair`'s answer: A's wedge, then B's lens,
then A's north slope under the lens and B's hip under the wedge meeting
at (441.4, 100).

## 4. Receipts ([`0181`](0181-ruling.md) §3)

* **Gap on `threeRidgeFloorplan.json`: 0%.** 70×70 grid: 2483 points
  inside a footprint, 0 drawn by nobody, 0 drawn twice. The partition
  invariant asserted globally through `compute_roof_clips(..., diag=)`:
  no blank cell at all, no limb cell. On the L: the blank set is exactly
  D85's corner (36.8 sq in, A's own root ground) and it is a subset of
  the uncertified-limb root ground —
  `test_0181_blank_ground_is_only_ever_an_uncertified_limb_s_root_ground`.
* **Both 0177 §3 valleys at the pinch, against the v2 picture:**
  `docs/evidence/threeridge-drawn-junction-0182.png`, drawn the same way
  (regions, seams red, ridges brown, the rake over rf1's eave blue). rf1
  ends at the pinch; exactly two rf1/rf2 valleys meet there, the second
  running from the pinch to the triple point (681.586, 538.067); rf2 runs
  on to its own end, wrapped by the rf2/rf3 seam; rf3 passes under rf1
  and comes out to its rake. rf1 east of the pinch: **0 sq in** (0180 had
  ~13%; the test now asserts exactly zero). The triple point is again a
  drawn seam vertex of all three roofs — that assertion restored.
* **The outer-corner seam vertex (441.4, 100) at 96" is RESTORED** in
  `test_an_equal_height_l_has_no_poke_through_in_3d`, as ordered, with
  the ground between (400, 130) drawn again.
* **The floor, untraded:** D85 (both `clip_pair` and the item), the
  poke-through fix, the pinch exclusion (now exact), 0 interior jumps
  (`test_r4g_every_remaining_cross_roof_boundary_is_a_seam_or_a_footprint_edge`
  unmodified), T/L suites unmodified, `clip_pair` untouched.
* **3D:** the rake jump 0177 §3 named correct is DRAWN now, so it is a
  real riser (a 30"+ step on rf3's own rake line); the riser test is
  refined to require it and to admit nothing else but sub-inch residue
  at the degenerate corner (756, 553) — where rf2's extended ridge, rf3's
  ridge and rf1's east edge meet — with steps under half an inch.
* `python -m ruff check .` clean; `python tools/gate.py` GREEN; the full
  suite 1284 passed (1275 at 0180: three tests added, six rewritten to
  the restored receipts).

## 5. Named limits, measured

* `compute_roof_clips` on the fixture: 0.11 s → 0.36 s (three phantom
  rounds and one orphan round, each a full envelope).
* Four sub-inch slivers at (756, 553) with steps of 0.15–0.3" — the same
  construction imprecision the 2D receipt already tolerates at 0.2"
  mid-edge, now visible to the riser detector as well; named, not fixed.
* A join end (inside a host, short of its ridge) whose cut-off arm holds
  root ground touching hidden ground would certify through the network —
  no fixture exercises it; D85 as built has the crossing. Named for the
  ruling rather than guessed at.
* `_strip` unchanged — [`0181`](0181-ruling.md) settled it.

## His check

The 0% receipt is in: the 3D view of `threeRidgeFloorplan.json` and of
the equal-height L, and the junction picture against his v2.

**Carried:** unchanged from [`0180`](0180-report.md).
