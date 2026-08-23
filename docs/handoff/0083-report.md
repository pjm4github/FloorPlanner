# 0083 — report: item C (the orthogonality repair) built, gated GREEN, and two findings neither ruling anticipated

**On [`0082-ruling.md`](0082-ruling.md).** §6's tier table unblocked
[`0066-ruling.md`](0066-ruling.md) item C, folding its own three amendments
(secs 2-4) into the build. Built exactly as specified — and running it
against real corpus files (not just the two `0079`/`0082` hand-walked)
surfaced two things neither ruling could have anticipated, because the
repair did not exist yet when either was written. Both are reported here,
not smoothed over.

---

## 1. WHAT IS BUILT

`floorplanner/design/validate.py` gains:

- `wall_repair_conflict(d, wall_id, endpoint_attr)` / `choose_repair_endpoint(d, wall_id)`
  — `0079-report.md` sec2(b)/(c), unchanged. Both already read `d` fresh on
  every call, which is what makes `0082` sec3's amendment correct by
  construction once the caller re-invokes them per wall rather than
  precomputing a batch.
- `_invariant_key(message)` — `0082` sec4: invariant code + subject ids,
  parsed from `check()`'s own message text (ids are a lowercase letter run
  + digits; invariant codes are `I` + digits; the two alphabets never
  collide). I11's quoted room names are pulled in too, so two different
  overlapping pairs do not collapse onto one key.
- `repair_wall_orthogonality(d, deep=True)` — the repair itself. Population
  is `wall_orthogonality()`'s own near-axis rows (`0 < deg <= 1.0`, the same
  cut item 1's census already uses) — **not** a displacement-bounded set.
  This is the resolution to an ambiguity neither `0066` nor `0079` states in
  as many words: `0066` sec3's "auto-repairable (< 1/16″) / reported, not
  touched (>= 1/16″)" table reads as a candidacy filter, but `0079` sec2(b)
  measures conflict "over all 63 near-axis walls" and explicitly names
  `farmplaceBIGmultifloor` `w24` — `0066`'s own 3.000″ headline outlier, four
  orders of magnitude past any `T` — as a candidate refused for CONFLICT,
  not excluded for size, and `0082` sec1 re-derives and accepts that finding
  without objection. Read together, that settles it: `T = 1/16″` is not
  spent in this delivery; the near-axis census IS the candidate set, exactly
  as measured.

  The interlock: `check()` runs before and after on a deep-copied working
  document, compared on `_invariant_key`. `0066` sec5's refuse-to-start
  clause is gone (withdrawn at `0082` sec2); the whole repair rolls back —
  returning the ORIGINAL `d`, untouched, not a copy that merely matches —
  if and only if it introduces a key that was not already failing.

  Returns `moved`, `refused`, `relocations` (the vertex-level `(level, old,
  new)` triples the scene applier needs — `walls.close_gap`'s own shape, so
  the same relocate-and-reweld path serves both), `rolled_back`,
  `newly_failing`.

`floorplanner/dialogs.py` gains `OrthogonalityRepairDialog` — preview (`0079`
sec2(d)'s exact wording), Apply relocates the scene via `close_gap` per
`relocations` entry, then `rebuild_all_walls`; the existing dirty-timer
settle path captures it as one undo step, matching every other command.
`floorplanner/mainwindow.py` gains **Edit ▸ "Repair wall orthogonality…"**,
beside the existing report item, reachable from no other path — never on
open, save, or export.

**Receipt:** `tests/test_orthogonality_repair.py`, 19 tests (17 headless + 2
`gui`) — the conflict predicate and `choose_repair_endpoint` in isolation;
`_invariant_key`'s three properties (ignores rendered numbers, still
separates different subject ids, captures I11's quoted names); a moved wall
lands at exactly 0, not within a tolerance; a refused wall is named with its
displacement unchanged and the repair never claims zero remain; the
withdrawn refuse-to-start (runs on a document that already fails `check()`);
the stable-key differential (a pre-existing violation that re-renders with
different numbers after a neighbour's length changes does NOT roll back);
a genuinely new violation DOES roll back the whole operation, byte-identical
`doc` returned; the chain receipt (below); the two corpus receipts (below);
the dialog applies to the live scene, not just the preview. Full suite: 852
passed. `ruff` clean. Gate: **GREEN**
(`Gate-Census: collected=852 ruff=clean vacuous=0 end_assign=0
snapshot=current`).

## 2. THE CHAIN RECEIPT — `0082` sec3, run on the real plan it named

`0082` sec3 asked for exactly this: *"apply the batch, assert every
non-refused wall ends at displacement 0. RED under the as-loaded predicate,
GREEN under the re-evaluated one."* Built as
`test_the_as_loaded_predicate_mistilts_the_chain_RED` /
`test_the_re_evaluated_predicate_leaves_every_non_refused_chain_wall_on_axis_GREEN`,
against `fixtures/wiscaway2026-08-09R.json`'s real `w53..w59` chain (`v54..v58`,
six walls, each consecutive pair sharing an endpoint — `0082`'s own count).

**RED, measured:** deciding every endpoint once, against the document as
loaded, and applying in that order — `w56` ends at **3.25°** off axis, worse
than it started, and neither `w56` nor `w55`/`w59` (0.055°/0.084°) was ever
refused, because the as-loaded predicate found zero conflicts anywhere in
the chain before any wall moved.

**GREEN, measured:** the built repair (which re-evaluates
`choose_repair_endpoint` fresh, against the document as mutated so far,
before each wall) refuses `w54` and `w57` — both of which the as-loaded pass
missed entirely — and every wall it does NOT refuse (`w53`, `w55`, `w56`,
`w59`) lands at exactly 0°.

## 3. THE FIRST CORPUS RECEIPT — matches `0079`/`0082` to the digit

`farmplaceBIGmultifloor.json`: `check()` returns exactly 1 failure (`0082`
sec2's own table), and the repair runs anyway (refuse-to-start withdrawn),
without rolling back. The two named refusals match exactly:

| wall | deg | displacement | why |
|---|---:|---:|---|
| `w24` | 0.9290° | **3.000″** | `0066` sec1's own headline outlier — both ends conflict |
| `w44` | 0.0288° | 0.1145″ | both ends conflict |

Every moved wall lands at exactly 0°.

## 4. THE SECOND CORPUS RECEIPT — a finding neither ruling ran: "61 of 63" does not hold corpus-wide

`docs/evidence/orthogonality_repair_census.py` (new — the same shape as
`orthogonality_census.py`, reading the same file set including
`fixtures/incoming/`, where it is a MEASUREMENT SUBJECT per
[`0063-ruling.md`](0063-ruling.md) sec4, "no test names it, and none is
owed" — this script is that measurement, not a test):

```
file                                                 near-axis   moved  refused      status
examples/farmplaceBIGmultifloor.json                         4       2        2     applied
examples/planc1.v5.json                                      6       6        0     applied
examples/planc1TestV5.json                                   6       6        0     applied
examples/symmetricP1.json                                    2       2        0     applied
fixtures/incoming/crossfloor-snap-2026-08-17.json           37      --       -- ROLLED BACK
fixtures/wiscaway2026-08-09R.json                            8       6        2     applied

TOTAL near-axis candidates: 63
TOTAL moved (straightened): 22
TOTAL refused (conflict):   4
TOTAL stranded by a whole-file rollback: 37, across 1 file(s)
```

**63 = 22 + 4 + 37, exactly** — the table produces its own headline, the same
discipline `0060-report.md` demanded of the orthogonality census itself.

> ### "61 OF 63" NEVER HELD. IT WAS COMPUTED ONLY AGAINST THE TWO FILES `0079` HAND-WALKED, AND THE THIRD FILE THIS REPAIR EXISTS FOR CARRIES MORE THAN HALF THE CORPUS'S OWN NEAR-AXIS POPULATION.

`crossfloor-snap-2026-08-17.json` — one of the four plans `0082` sec2's own
interlock table names — was never among the 20 plans `0066`'s corpus census
walked (it arrived later, as intake evidence for the cross-floor thread).
Straightening its walls introduces two genuine new `I14` violations
(`v17`/`w20`/`w21` and `v17`/`w21`/`w22` — an endpoint moved by one repair
lands on an unrelated wall's body without being its vertex). `0082` sec2's
whole-document rollback — specified correctly, per its own wording, and not
something this report proposes changing — discards **every one** of this
file's 37 candidates, not just the two that collide. `0082` sec3 called "61
of 63" provisional without running it against this file; this is that run,
and the honest number is **22 moved, 4 refused, 37 withheld by one file's
rollback** — not 61-and-2.

**No design change proposed here.** A per-wall (rather than whole-document)
rollback is a real alternative and a real design question — whether the
walls that DID succeed on a rolled-back file should be kept — but it is a
new decision, not a bug in what was ruled, and it is named rather than
built.

## 5. A SECOND FINDING — a refused wall's OWN displacement can still change

`0079` sec2(f), reaffirmed at `0082` sec5: *"For every wall the repair DID
refuse: its displacement is unchanged from before the repair ran."*
Measured on `wiscaway2026-08-09R`'s own chain: `w54` is refused (both
candidate endpoints conflict, per the re-evaluated predicate) — but `w54`
shares vertex `v54` with `w53`, which the repair DOES straighten. Because a
`Vertex` is one shared corner (`CLAUDE.md`'s own architecture note — "moving
it moves everything on it"), straightening `w53` relocates `v54`, and `w54`
— refused, untouched by the repair's own choice — moves anyway, as a side
effect: from 0.0131″ off axis before, to **4.679°** off axis after (measured
directly; not asserted in the test suite, because the acceptance clause it
would contradict was itself just reaffirmed by `0082`, so this is reported
rather than silently tested around).

**This is a real gap in clause (f)'s second paragraph**, not a defect in
what was built: nothing in `0066`/`0079`/`0082` specifies that a refused
wall's shared vertex should be exempted from a NEIGHBOUR's repair, and
exempting it is a new rule (freeze every vertex touched by a refusal against
any other wall's move) with its own consequences for coverage — narrower in
scope than, but in the same family as, item 3's graph-solve. Named here,
not built.

## 6. TIER AND ORDER

| | | |
|---|---|---|
| 1-3 | `0082` secs 2-4's amendments | **GREEN, folded into the build below — no separate diff exists for them** |
| 4 | `0066` item C / `0082` §6 item 4 — the repair | **BUILT, GATED GREEN.** Branch/PR below, stopped for Patrick's check |
| — | §4 above — "61 of 63" corrected corpus-wide | **a finding, not a task** — no ruling owed unless Patrick wants the whole-file-rollback question answered differently |
| — | §5 above — refused-wall side-effect displacement | **a finding, not a task** — named for a future ruling if it matters to Patrick's own plans |
| 5 | `0066` §7 item 3 — user-settable `T`, the graph solve | **RED, unchanged** |
| 6 | `0066` §6's own Patrick check (run the repair on the `L2.dxf` source plan, re-export, recount) | **still owed — cannot be produced until Patrick runs it** |

**PATRICK'S CHECK — `0066` §7's own, unchanged, now runnable:**

> Open the plan that produced `L2.dxf`. Run Edit ▸ Repair wall orthogonality.
> Export DXF, open in Chief. How many walls does it flag now, against the 75
> before? And: does the drawing still look like your drawing? Nothing moved
> that you meant to be where it was.

Branch: `wall-orthogonality-repair`.
[PR #37](https://github.com/pjm4github/FloorPlanner/pull/37) opened against
`main`, AMBER, stopped for the check above — matching `0081-report.md` §1's
own pattern for PRs #34/#35/#36.
