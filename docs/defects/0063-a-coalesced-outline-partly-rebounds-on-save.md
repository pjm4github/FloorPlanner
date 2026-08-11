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

## PRODUCER 2 — measured 2026‑08‑10, and MY LOOSE THREAD WAS AN ARTIFACT

**The thread was mine and it does not exist.** I reported that on `08‑09R` the
coalesce lane inserts **1** where the wall-pass lane inserts **3**, one-sided,
and concluded *"removing a corner can PREVENT a producer-2 insertion"* — a causal
link between the lanes. The reviewer, reasonably, made that the starting point.
**Measured, two of those three are not insertions at all.**

| | the 2 "prevented" | the 10 that FIRE |
|---|---|---|
| wall ends at the point | **0** before *and* after the wall pass | **3 – 6** |
| lies inside an outline edge | **no** | **yes**, every one, at a real fraction |
| nearest dissolved corner | **0.08″ / 0.38″, same room** | 6″ – 166″, or none |

**They are the SAME CORNER AT A RECOMPUTED COORDINATE.** The scene holds a point
**0.0778″** and **0.3802″** away; the save wrote it slightly moved, and the
pairing tolerance (0.05″) scored the move as a fresh insertion. Dissolve that
corner and the ghost has nothing to be a ghost of — which is the whole of the
"prevention". **So the 3-versus-1 asymmetry is an artifact of my instrument, not
a mechanism**, and the one-sidedness has no causal content.

### The safety check this forced, and it matters more than the thread

If the save can move a corner by 0.38″, then a corner that *rebounded* 0.08″ from
where it left would be scored **not the same corner** — counted as `durable` and
as a producer-2 `insertion`, understating rebound twice. **So producer 1's
closure was re-run across four pairing tolerances:**

| tolerance | 0.05″ | 0.25″ | 0.75″ | 2.0″ |
|---|---|---|---|---|
| **total rebound, five plans** | **0** | **0** | **0** | **0** |

Every column identical, every plan. **The closure is robust, not
tolerance-dependent.** (Both modules' `TOL` had to be set — `d63_rounded_rebound`
does `from d63_producer_one import TOL`, so it holds its own binding; setting one
is not setting the other, which is the *wrapper bound to the wrong reference*
trap, and the sweep asserts both moved.)

### Producer 2, with the ghosts removed — one shape, two origins

Every remaining insertion is the same thing: **a room edge crossing a point where
walls end, that the outline never named.** I5 requires a hop there. The two lanes
then agree exactly — `rounded` 6, `planc1` 3, `08‑09R` **1**.

They differ only in **where the wall end came from**:

| origin | count | plans |
|---|---:|---|
| the **wall pass created it** (a new end mid-edge) | 6 | `planc1` 3/3, `rounded` 2/6, `08‑09R` 1/1 |
| the end was **already there** and the outline never named it | 4 | `rounded` 4/6 |

The second is the more interesting half: **the plan arrives with a room edge
crossing an unnamed T-junction**, so the save is correcting the *stored* outline
rather than reacting to anything the session did.

### IS THE ALREADY-THERE HALF AN I14 REPAIR? — NO, and I14 could not see it anyway

The question ruled worth asking first: *if the stored outline genuinely violates
I5 — a room edge crossing a T-junction it never named — then the save's insertion
is a **repair**, and counting it as a producer was our category error rather than
a fault in the code.* `wiscaway2026-08-09R` fails I14 three times with exactly
that wording.

**Measured, and it is disjoint — decisively, without needing a distance:**

| plan | producer-2 insertions | I14 failures | of which unwelded-T |
|---|---:|---:|---:|
| `roundedMultifloor` | **6** | **0** | 0 |
| `planc1.v5` | **3** | **0** | 0 |
| `wiscaway2026-08-09R` | 1 | **3** | **3** |
| `wiscaway2026-08-08` | 0 | 0 | 0 |
| `symmetricP1` | 0 | 0 | 0 |

**Two of the three plans that produce insertions have no I14 at all**, so there is
nothing for the insertions to coincide *with*. On the plan that has both, the
single insertion at `(1269.728, 387.728)` is **122.6″ from `v92`** and **50.2″
from `v148`** — the two vertices the I14 messages name. Not the same points, in
either direction.

**AND THE STRUCTURAL REASON IS THE STRONGER ANSWER: I14 CANNOT SEE THIS SHAPE.**
`validate.py:283` — *"no wall end sits within `vertex_weld_in` of another wall's
body or end without being that same vertex"*. It compares **wall ends to walls**.
A **room outline** crossing a point where walls end is outside its question
entirely, exactly as `scene_identity_report` is blind to whether an outline
shares a wall's vertex ([D62](0062-weld-scene-leaves-room-outlines-holding-a.md)).
So the coincidence could not have held however the geometry fell, and a *"no"*
here is a boundary rather than a measurement.

**Which leaves the state genuinely unreported.** A stored outline crossing an
unnamed T is invisible to I14 (wrong subject) and cannot fail I5 on a *saved*
document (the walk emits one edge per wall **by construction**, so the emitted
form is always compliant). **The fault is only visible in the stored-versus-emitted
difference** — which is what producer 2 is. That is a gap in the invariant set,
not merely a defect, and it is the honest place the target moves to.

**One correction on the way, recorded because it changed an answer.** The first
run of this comparison asked I14 of the **re-saved** document and reported *2
failures, 0 unwelded-T* on a fixture whose README names three. The save welds and
re-splits, so it had already repaired what was being looked for. Asked of the
bytes on disk: **7 violations, 3 I14, all three the unwelded-T shape**, matching
the fixture's characterisation exactly.

### A separate finding, flagged not chased

**The save moves a corner on two of five plans**: zero on all three axis-aligned
plans, **2 corners at ≤0.3802″** on the angled `08‑09R`, and **2 corners at up to
1.5290″** on `planc1`. Rare and isolated rather than general drift — but 1.5″ is
too large to leave as a footnote here, and it belongs to whichever pass owns
`split_params`' projection, not to D63.

> **FILED AS [D64](0064-the-save-writes-an-outline-corner-at-a.md), and the
> 1.5290″ HALF OF THIS PARAGRAPH IS WRONG.** Re-measured: `planc1`'s pair are not
> moves at all but **producer-2 insertions** that happen to sit 1.5290″ from an
> unrelated neighbour — the 2.0″ threshold in this census could not tell a moved
> corner from a new one. **The largest genuine move is 0.3802″, below the 0.6″
> weld radius**, and neither moved corner has another wall end nearer than
> **5.998″**, so no identity is at risk. Accuracy, not data integrity. The
> paragraph is left standing with this annotation rather than rewritten, because
> the wrong figure is what the escalation was issued on.

**Evidence:** `d63_producer_two.py` → `d63-producer-two.json` ·
`d63_tolerance_sweep.py` → `d63-tolerance-and-drift.json`.

**Controls:** the recorded per-lane table is reproduced before any attribute is
read (`3/1`, `6/6`, `3/3`, `0/0`, `0/0`); one-sidedness is asserted per plan and
**PASSES everywhere** (nothing in the coalesce lane the wall pass does not also
produce); and the PREVENTED set is asserted non-empty, because an instrument
reporting "nothing in common" across an empty set has measured nothing.

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

## PARKED (2026‑08‑11)

**Register entry, no work.** Patrick's ruling: bug cleanup circles back after
features. **Not to be reopened without a new instruction.** Parked alongside
[D63](0063-a-coalesced-outline-partly-rebounds-on-save.md)'s remaining halves,
[D64](0064-the-save-writes-an-outline-corner-at-a.md),
[D65](0065-weld-scene-is-implicated-in-three-separate.md) and
[D66](0066-a-departing-room-carries-its-neighbours-walls.md).

**What is parked here is PRODUCER 2** — both origins, the wall-pass-created
and the already-there half. Producer 1 is closed and stays closed.
