# 0095 — report: `0084-ruling.md` §6 items 1–3 built — `T` restored, the post-condition added, the census re-run

**On [`0084-ruling.md`](0084-ruling.md) §6, unblocked by [`0090-ruling.md`](0090-ruling.md) §4.**

## 1. `T` RESTORED (§1)

`REPAIR_T_IN = 1/16"`. Candidates are near-axis walls with displacement
`< T`; at or above it, a wall lands in a new `over_t` list — reported,
never touched, regardless of conflict. `w24`/`w44` (`farmplaceBIGmultifloor`)
now sit in `over_t`, untouchable for the right reason.

## 2. THE POST-CONDITION (§2) — built, then a real bug it found in itself

Implemented as specified: after each successful move, re-check every
wall's degree against its pre-repair value; undo the move and refuse it
(`"would worsen <wall>"`) if anything got worse.

**First draft exempted still-pending candidates** (they get a later turn
to fix themselves). **Measured against `wiscaway2026-08-09R`'s real
`w57`: the exemption let it get tilted by an earlier move while pending,
then it reached its own turn already worse, was refused there for an
unrelated conflict, and nothing ever re-checked it.** The guarantee broke
on the file it was built to protect.

**Fixed: no exemption.** Every wall is checked after every move, including
pending candidates — costs some coverage (a move can be undone even when
the wall it disturbs would have self-corrected moments later) but is the
only form that is actually correct. Corpus-wide receipt, all four allowed
files plus `wiscaway`'s chain: **zero walls end up worse than before the
repair ran** (`test_the_post_condition_holds_corpus_wide_no_wall_ends_up_worse`).

## 3. THE CENSUS RE-RUN (§3) — the whole-file rollback is moot

`docs/evidence/orthogonality_repair_census.py`, re-run under both fixes:

```
file                                             near-axis   moved  refused  over_t      status
examples/farmplaceBIGmultifloor.json                     4       0        0       4     applied
examples/planc1.v5.json                                  6       5        0       1     applied
examples/planc1TestV5.json                                6       5        0       1     applied
examples/symmetricP1.json                                 2       1        0       1     applied
fixtures/crossfloor-snap-2026-08-17.json                 37       5       11      21     applied
fixtures/wiscaway2026-08-09R.json                          8       2        3       3     applied

TOTAL: 63 = 18 moved + 14 refused + 31 over_t. Rollbacks: 0, across 0 files.
```

**`0084` §3's own bet paid off.** `crossfloor-snap`'s two colliding walls
are both at/above `T` now (never moved), so the collision — and the
whole-file rollback that used to strand all 37 of its candidates — never
happens. **Item 3's "AMBER to change" half is not needed; nothing was
built for it.**

## 4. RECEIPT

24 tests in `tests/test_orthogonality_repair.py` (4 new: `over_t`
reporting, the worsen-and-undo mechanism, the corpus-wide post-condition
sweep ×4 parametrized). Dialog and `refused` tuple shape updated (now
5-tuple with a reason). Full suite 874 passed, `ruff` clean, gate GREEN.

## 5. TIER AND NEXT

**GREEN** on this build (matches an existing ruling's spec). PR #37
(`wall-orthogonality-repair`) is now worth checking — [`0066`](0066-ruling.md)
§7's own question, unchanged: run the repair on the `L2.dxf` source plan,
re-export, recount against Chief's 75, and does the drawing still look
like the drawing.

**Not built this pass:** `0092`/`0093`/`0094` (the status-bar angle
clause, AMBER, explicitly not blocking `0084` §6) — next.
