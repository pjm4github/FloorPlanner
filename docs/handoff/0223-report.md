# 0223 — report: the D67 pair fixed on `d67-floor-scope`, one predicate each; his gable-end plan promoted as the check fixture; the gable-end tranche read back before it is built

**Code, 2026‑10‑06.** No merge has happened since
[`0222`](0222-report.md). His word, one message, three things:

> *"start on the D67 pair. Mark the incoming json file as a test cade for
> gable end. I want the roof and dormer constructor to build the roof's
> gable ends such that the 3d view shows an extension of the wall beneath
> the gable. The current 3D rendering creates a wrapped around roof on
> teh gables - thats not waht I want - instead I want the roof to extend
> out as speced, then the wall which is covered by teh roof to extend up
> to meet the roof."*

## 1. THE D67 PAIR — built, on branch `d67-floor-scope`, for his check

Two measured sites, one predicate each, exactly as
[`0201`](0201-report.md) §1 and [`0202`](0202-report.md) §4 named them:

| site | the predicate | what it stops |
|---|---|---|
| `RoomItem.interior_walls()` (`rooms.py`) | `it.floor == self.floor` | a group made on the upper floor taking the lower floor's partitions that stand under the room in plan — the drag then moved both floors |
| `PlanView._place_opening` (`view.py`) | the first wall under the cursor **of the active level** | the Door/Window tool cutting another level's ghosted wall |

**Fail-first:** `tests/test_d67_floor_scope.py`, six tests, five RED
before the predicates and GREEN after; the sixth is a positive control
and passes both ways. The two gestures are the probes' own: the band over
the whole of `roundedMultifloor.json`'s second floor, grouped and
dragged, with the lower floor compared wall by wall before and after
(0201's gesture; the group was `{'default': 2, 'second': 41}`, now
`{'second': …}` only); and the Door tool on a lower-only wall of
`wiscaway-2level-stacked-floor.json` from `upper` with other floors shown
(0202's row 8; 56 → 57, now 56 → 56 and the status line says *click on a
wall*). Two positive controls: the leaked partition rebuilt as a wall of
the room's own floor IS returned, and the Door tool on an upper wall
still cuts exactly one opening, on `upper`.

**D67's record is not closed by this commit.** It closes with
`closed_by` naming the landing commit, in the merge's own report, as D50
and D85 did.

## 2. THE FIXTURE — promoted, exit 2

`fixtures/incoming/single-floor-90-roof-gable-end-check.json` →
`fixtures/single-floor-90-roof-gable-end-check.json`, a `fixtures/README.md`
row carrying his sentence from this message as what it is for.
[`0205`](0205-report.md) §3 recommended exit 2 and said the row's
purpose sentence was his to give; he gave it. Content unchanged; git
normalises the line endings. `incoming/` is empty.

What the plan is, read for the tranche below: one level 96″ high, two
gable roofs at 90°. **The ridge ends are the rake tips.** `rf1`'s west
ridge end at x=168 stands 12″ past the gable walls `w2`/`w4` at x=180;
`rf2`'s ends at y=96 and 426 stand 24″ and 18″ past `w11` and `w19`.
`rf1`'s east end (x=498) is inside `rf2`'s territory, so it is a joined
end, not a gable. There is no separate gable-end overhang in the model;
*"extend out as speced"* can only mean the ridge as drawn.

## 3. THE GABLE-END TRANCHE — read back, not built

**What the 3D view does today** (`fp3d.py`, the roof builder): a gable
roof is two sloped planes off the ridge **plus a vertical triangle at
each gable end built of ROOF material** — R3's acceptance line, *"gables
closed"* ([`0139`](0139-ruling.md) §2), and on a clipped roof R4g's
`_gable_fascia_pieces`. That triangle stands at the rake tip (x=168), in
front of the gable wall, and is what he sees as *"a wrapped around
roof"*. The wall under it (`w2`/`w4`) is 96″ — the eaves height — and the
wall-cap code only ever LOWERS a wall to a roof surface (it raises one
only under a dormer: *"UNDER A DORMER THE WALL RISES"*, his own
instruction of 2026‑09‑24). So the gable above the wall is empty, and the
roof triangle hides that.

**What he asks for, as I read it:**

1. **No roof-material gable triangle.** A gable end is open under the
   rake; the roof planes end at the ridge end as drawn (the hip end's
   sloped face, R4b, stays — it is a roof surface).
2. **The gable wall climbs to the roof.** An EXTERIOR wall under a roof,
   running perpendicular to that roof's ridge, has its top follow the
   roof's underside — up to the ridge — the way a wall under a dormer
   already climbs into the dormer's plane. Interior walls do not climb
   (a partition under the ridge stops at ceiling height, as now).

**One question in it, which I will answer by his words unless he says
otherwise:** *which* exterior walls climb. His sentence is *"the wall
which is covered by the roof"*, so the rule is any exterior wall piece
whose owning roof is a gable roof and whose heading is perpendicular to
that ridge — not only the outermost. A cross wall mid-house under one
roof then climbs too; it is under the roof, so it is seen only through
an open gable, and the gable walls close those.

**What changes on the record:** R3's *"gables closed"* line is
reversed by his instruction; the two viewer tests that count the gable
triangles' faces (`test_roof_gable_ends_close_by_default` and its hip
control) are rewritten to pin the new rule, each saying why; R4g's
`_gable_fascia_pieces` becomes dead and is removed with its test. The
dormer's own gable (the dormer face) is a wall-climb already and does
not change.

**The receipt:** his fixture built by `build_model`: the walls mesh at
x=180 reaches `z0 + 165.75 − cap` at y=216 and 96 at the eaves; the roof
mesh has no face lying in the plane x=168 taller than a slab; and
`fixtures/roofs-r3-orbit-check.json` re-shot for the evidence folder,
which needs his display (D77).

Built next, on his word or on this read-back standing unanswered, as
branch `gable-end-walls` stacked on `d67-floor-scope`.

## 4. STATE

`main` is this commit: the report, the promoted fixture and its row, the
snapshot. The D67 code is the branch's commit; gate GREEN on the tree
with it — see this commit's own run and the PR's.

## 5. `fixtures/incoming/`, with ages

**Empty.** `README.md` only.

**Untracked, not mine, untouched:** `gen/`, `docs/macro-spec/grammar/gen/`,
my draft `docs/WORKING_AGREEMENT.proposed.md`, the old stash entry.

## 6. WHAT HAPPENS NEXT

His check of the D67 PR; the gable-end tranche (§3). Behind them,
unchanged: the four-way crossing fault, parallel walls 6″ apart merging,
the status board.

**Carried:** unchanged from [`0222`](0222-report.md).
