---
# permanent key, independent of GitHub
id: 63
title: "A coalesced outline partly rebounds on save, and the two producers are separable"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:defect
  - area:io
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-09
closed: null
closed_by: null
rank: 64
related: [61, 62]
state_source: measurement
github_issue: null
---

# D63 — A coalesced outline partly rebounds on save

## Symptom

Run `Edit ▸ Coalesce all walls now`, save, reopen: **some of the removed outline
corners are back.** Once, not repeatedly — the count then settles.

| plan | as loaded | after the command | after save + reopen | **durable** | rebound |
|---|---:|---:|---:|---:|---:|
| **`wiscaway2026-08-08`** | 159 | 119 | **126** | **33 of 40** | 7 |
| `roundedMultifloor` | 187 | 167 | **186** | **1 of 20** | 19 |
| `symmetricP1` | 140 | 136 | 136 | 4 of 4 | 0 |

`119 → 126 → 126 → 126`. **A pure round trip with no command is stable** — 159,
159, 159, 159 — so saving is not a producer on its own; it is the *coalesced*
state that does not survive one.

**This is the number that decides whether 2a helped.** On Patrick's plan the
durable benefit is **33 of the 69** corners he can see, not the 40 the command
reports. On `roundedMultifloor` it is **1 of 20** — near-total loss.

## Mechanism: TWO producers, separated by an exact identity

Measured on five plans, with the coalesce lane and a **wall-pass-only** lane run
separately:

| plan | 2a removed | inserted by the save | of which 2a's | inserted after the **wall pass alone** |
|---|---:|---:|---:|---:|
| `wiscaway` | 40 | 7 | **7** | 0 |
| `roundedMultifloor` | 20 | 19 | **13** | 6 |
| `farmplace` | 2 | 2 | **2** | 0 |
| `symmetricP1` | 4 | 0 | 0 | 0 |
| `planc1.v5` | 0 | 3 | 0 | 3 |

> **`inserted_after_the_pair − inserted_after_the_wall_pass == overlap`, exactly,
> on all five plans.**

So:

* **Producer 1 — THE COALESCE COMING UNDONE.** The save puts back corners the
  outline pass removed. 7 on `wiscaway`, 13 on `rounded`, 2 on `farmplace`.
* **Producer 2 — A WALL-PASS-SIDE INSERTION.** Corners 2a never touched, added
  after `normalize_walls` alone. 6 on `rounded`, 3 on `planc1` — where the
  outline pass removed **nothing at all**, so producer 1 cannot account for it.

**These are two investigations, not one**, and the identity above is what says
so rather than an impression.

Both need the wall pass to have run: the negative control — a pure round trip
with no command — inserts **0** on every plan.

## What has been RULED OUT

**It is not D62 seen from another side, and that hypothesis is recorded as
REFUTED rather than partially confirmed.** The proposal was that the save-side
weld in `design_from_scene` — already implicated in bounding D62's harm and in
hiding it from `check(deep=True)` — was also re-inserting these corners.

**The identity half came out that way; the causal half did not, and only the
second mattered.** With [D62](0062-weld-scene-leaves-room-outlines-holding-a.md)'s
repair applied (`weld_scene` now restores the P3.5 invariant, divorce 49 → 0),
durability is **unchanged**: `wiscaway` 33 of 40 becomes 33 of **37**, `rounded`
1 of 20 becomes 1 of **17**. Fixing D62 does not fix the rebound.

## Evidence

`docs/evidence/d63_rounded_rebound.py` · `docs/evidence/d63-rounded-rebound.json` ·
`docs/evidence/d63_producer_one.py` · `docs/evidence/d63-producer-one.json` ·
`docs/evidence/d61-save-reinserts.json` · `docs/evidence/d61_save_reinserts.py` ·
`docs/evidence/d61-divorce-persistence.json` ·
`docs/evidence/d61-what-2a-leaves.json` ·
`docs/evidence/d61-leave-path-and-persistence.txt`

**Controls, because a zero was a live outcome throughout:** a pure round trip
must insert 0 (PASS, five plans); the identification must match the count delta
(PASS, five plans); and the document reader must be READABLE — the first version
walked `levels[*].walls` on a **flat** v5 document, found nothing, and reported a
confident `0 orphan refs` off zero walls and zero rooms.

## PRODUCER 1 — FOUND, AND IT IS NOT THE SAVE

**The save was right and the coalesce was wrong.** `design/bridge._walk` emits
**one outline edge per wall** (invariant I5), so a room edge crossing a
T-junction is several edges however few corners the scene holds. The coalesce
was removing corners the *document model requires*, and the save put them back
correctly.

**Measured, and the predicate discriminates cleanly** — of the corners the save
re-inserted, **4/4** on `wiscaway`, **4/4** on `wiscaway…09R` and **16/16** on
`roundedMultifloor` had a **wall end** at them; of those that stayed removed,
**0/33**, **0/94** and **1/7** did.

Two terms were missing from `wall_ok`, both now measured into it:

1. **A wall ENDS here that does not hold this vertex** — a T-junction whose stem
   is off the run, invisible to a degree count.
2. **The two collinear walls CANNOT MERGE.** `merge_wall` is same-type only, so
   a 6″ `exterior` meeting a 4.5″ `interior` head-on stays two walls and needs
   an outline edge each. Found at `(1062, 774)`, `(852, 762)`, `(1476, 660)` on
   `wiscaway` — collinear at 90.0°, different types.

**Result, measured across a save:**

| plan | removed | durable | rebound |
|---|---:|---:|---:|
| `wiscaway2026-08-08` | 33 | **33** | **0** *(was 40 / 33 / 7)* |
| `wiscaway2026-08-09R` | 94 | **93** | 1 |
| `symmetricP1` | 4 | **4** | 0 |
| **`roundedMultifloor`** | 6 | **0** | **6 — UNRESOLVED** |

Pinned by `tests/test_rooms.py::test_a_coalesced_corner_stays_gone_across_a_save`.

**`roundedMultifloor` is still open and its cause is not known.** A floor-scoping
hypothesis was written and **refuted** — the result is byte-identical with and
without it, so the scoping stays on its own merits and explains nothing here.

### THE `roundedMultifloor` ROW WAS AN ARTIFACT OF THE MEASURE — resolved 2026‑08‑10

**There was no rebound. All six removed corners are durable, and the six in the
saved file are six DIFFERENT corners.** The table above counts SLOTS; the
durability figure behind it came from
`test_a_coalesced_corner_stays_gone_across_a_save`, which asserted
`slots() == in_session` — **a total, not an identity.** On this plan the total
returns to exactly where it started (187 → 181 → **187**), so six removed and six
inserted elsewhere read as *nothing survived*.

Re-measured per `(room, point)` on five plans
(`docs/evidence/d63_rounded_rebound.py` → `d63-rounded-rebound.json`):

| plan | removed slots | **durable** | **rebound (p1)** | inserted (p2) | wall pass alone |
|---|---:|---:|---:|---:|---:|
| `roundedMultifloor` | 6 | **6** | **0** | 6 | **6** |
| `wiscaway2026-08-08` | 33 | **33** | **0** | 0 | 0 |
| `symmetricP1` | 4 | **4** | **0** | 0 | 0 |
| `wiscaway2026-08-09R` | 94 | **94** | **0** | 1 | 3 |
| `planc1.v5` | 0 | 0 | **0** | 3 | 3 |

**PRODUCER 1 IS CLOSED ON ALL FIVE PLANS.** The `08‑09R` row also improves — its
single re-inserted corner is producer 2, not the 1 rebound previously recorded,
so that plan is 94 of 94.

**`rounded`'s six are producer 2, and it is the same six, not merely six.** The
wall-pass-only lane — `normalize_walls`, save, **no coalesce** — inserts corners
at exactly the same `(room, point)` pairs: `EQUAL` on `rounded`, on `planc1` and
on the three silent plans. That set equality is the check, because two lanes
producing six each could otherwise be two different sixes.

**AND THAT IS THE DISCIPLINE THE ORIGINAL DURABILITY MEASURE NEEDED AND DID NOT
HAVE.** Checking both one-sided differences — nothing in lane A that is not in
lane B, and nothing in B that is not in A — is precisely what a slot total
cannot do, and applying it here is what exposed the artifact. The same question
asked of the original measure ("are these 33 survivors the same 33, or 33 of
something?") would have caught it at the time. **A set equality is the cheap form
of the general rule; a count is the expensive way to be wrong.**

**What was ruled out, and it is a clean negative.** `wall_ok` is floor-scoped but
takes its floor from the *first* holder of a shared vertex, which on the only
two-level plan in the set could have compared two differently-scoped numbers.
Measured: **0/4 of the re-inserted corners have cross-floor holders, and 0/3 of
those that stayed removed do** — there is no cross-floor vertex sharing on this
plan at all, so the hypothesis explains nothing. Recorded as refuted, alongside
the floor-scoping one above.

**The remaining discrepancy, named rather than smoothed over:** on `08‑09R` the
coalesce lane inserts **1** where the wall-pass lane inserts **3**. The
difference is one-sided — nothing appears in the coalesce lane that the wall pass
does not also produce — so the coalesce removing a corner can *prevent* a
producer-2 insertion. That belongs to producer 2 and is not chased here.

**The guard now asserts the identity.** The test is parametrised over
`wiscaway2026-08-08` and `roundedMultifloor` and pairs corners per room. Against
the pre-D63 predicate (`282333d`) **both cases fail** — so the fix did help
`rounded`, and only the count measure hid it. Producer 2's residue is
deliberately **not** pinned in producer 1's guard.

### THE INSTRUMENT'S OWN CONTROL — required, and it was owed

The measurement above is a **zero on five plans**, so it does not get believed
until the instrument has been shown to report non-zero where non-zero exists.
**The test's red does not supply that.** The test and the probe are two
implementations of one pairing rule, and two implementations agreeing is the same
claim made twice, not a control.

So the probe BINARY was run against pre-fix production code, in a `git worktree`
at `282333d` — **the instrument files copied in from the current tree, so only
`floorplanner/` varied**:

| plan | removed | durable | **rebound** | inserted (p2) |
|---|---:|---:|---:|---:|
| `roundedMultifloor` | 17 | 7 | **10** | 6 |
| `wiscaway2026-08-08` | 37 | 33 | **4** | 0 |
| `wiscaway2026-08-09R` | 97 | 94 | **3** | 1 |
| `symmetricP1` | 4 | 4 | 0 | 0 |
| `planc1.v5` | 0 | 0 | 0 | 3 |

**17 pre-fix against 0 post-fix, same binary. The zero is supported.**

**Two boundaries on that control, both stated because neither is visible from the
table.** `symmetricP1` and `planc1` read 0 on *both* sides — they carry no
producer-1 instance, so they contribute nothing to the validation, which rests on
the other three. And the ten are **`roundedMultifloor`'s, not `wiscaway`'s**: the
first reading of the fail-first output attributed them to `wiscaway`, because the
rooms named in it (`Master Suite`, `BR3`, `MBATH`) were read past — only
`Rear Porch` exists in both plans. Corrected here because the number was quoted
as a validation criterion before it was attributed.

**Preconditions, since a control is only as good as its own setup:** the worktree
holds neither D63 term (`grep -c` → 0 and 0) while the current tree holds both
(→ 2), and the probe reported at runtime which module it had loaded, with both
terms confirmed absent from the loaded source.

## Ruling

*(Open — **producer 1 is CLOSED**, producer 2 remains.)*
**Producer 1 first** — the coalesce coming undone — as ruled at handoff
0004's response. Producer 2 is separable and waits.

**Producer 1 closed 2026‑08‑10**, on five plans measured by identity: rebound 0
everywhere. `roundedMultifloor` was never an exception to it — the row that said
so was reading a slot total. **The record stays OPEN for producer 2**, which now
owns every insertion in the table above: 6 on `rounded`, 3 on `planc1`, 1 on
`08‑09R`.

**The lesson is about the instrument, not the geometry, and it generalises.** A
count answered a question about identity, and it answered it wrongly in the one
direction nobody checks — it reported a *failure* that had not happened, which
then survived two handoffs as an open unknown. The working agreement's *"grep
for identifiers, parse for shapes"* has a sibling here: **count only what you
cannot name.**

It bears directly on **D61 stage 2b**, whose acceptance is now *taken across a
save*: a six-move walk must end with the counts it started with **after save and
reload**, not in session. In-session-only would measure the wrong thing, and this
record is why.
