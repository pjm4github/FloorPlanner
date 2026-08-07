# Roadmap and autonomy charter

**Built 2026‑08‑07 from disk** — `docs/SESSION_SNAPSHOT.md` (re-cut at `ac93afc`) and
`docs/defects/INDEX.md`, read directly, not from conversation. State: `main` @ `763aa53`,
Phase 4 complete, 633 collected / 625 passed / 1 xfailed, 50 records — 11 open, 39 closed.

This document exists to answer one question: **what can proceed without Patrick, and what
cannot.** It tiers every remaining item, issues the rulings that unblock the most work, and
names what still needs a human.

Where this disagrees with the plan, the register or the snapshot, **those are authoritative**
and this document is wrong.

---

## 1. The autonomy policy

The bottleneck has never been review. It is **unruled questions**. So autonomy is granted per
item, by tier, and the tier is assigned **here** — Code does not self-classify.

| tier | criteria | what Code does |
|---|---|---|
| **GREEN** | a ruling exists on disk · no user-visible behaviour change · no format or schema change · acceptance is stated | run it, gate it, PR it, **merge on green CI**, report at the end of the batch |
| **AMBER** | a ruling exists, but the task changes what the user sees or what an operation produces | run it, gate it, PR it, **stop** — Patrick's manual check is the merge condition |
| **RED** | a ruling is missing | **do not start.** Read-back first |

**What revokes autonomy automatically** — the existing stop conditions, unchanged:

* a measurement changes the item's scope (this has fired six times in P4.5 alone)
* a finding contradicts something already decided
* a ruling is needed that this document does not contain
* the row‑36-style case: a watch trips, or a carried item's premise expires

A GREEN item that hits any of those becomes RED **mid-flight**. Stopping is not friction; it
is the mechanism working.

**What replaces per-task acceptance.** The gate (ruff + three verification modes + `--docs` +
`vacuous=0` + `end_assign=0`), the commit hook, CI's five jobs, and the standing receipt rules
— fail-first, differential, precondition-established. Those are machine-enforced now in a way
they were not three weeks ago. The reviewer's remaining job is rulings and the questions no
checklist encodes.

**What must never be autonomous, regardless of tier:** creating GitHub issues, force-pushing,
rewriting history, touching untracked files, changing the frozen corpus without a declared
justification, and merging anything with an AMBER tier.

---

## 2. Rulings issued now

These unblock the two largest RED items.

### R‑A — D41: a NEW invariant, not a widening of I5b

I5b tests **proper crossing**, and `_seg_cross`'s docstring says it must not fire on the
collinear edges two rooms legitimately share. That predicate is correct; widening it would
blur something that works.

A ring that visits a vertex twice — the pinched loop the walk planarises, and the zero-width
spur in WIC — is a **different fault**: not a crossing, a degeneracy. It gets its own
invariant: *a room outline is a simple ring; no vertex appears in it twice.*

**On the corpus, which is the harder half.** `symmetricP1.json` is the frozen clean reference
and it contains an instance. A clean reference containing a zero-area spur is a lie about what
clean means. So: **fix the spur, re-cut the freeze, and record the justification in the same
commit** — a declared fixture change, which this project has a rule for. `planc1.v5.json` is
the corruption fixture and keeps its instances; they are the point of it.

**Tier: AMBER.** Adding an invariant means files that validated now fail. A read-back is
required before starting, covering: which files in `examples/` fail the new check, whether the
new invariant is deep-only or joins the cheap twelve, and the corpus-freeze diff.

### R‑B — schema versioning policy, decided once for all three needs

Three separate features want a schema field: `level.kind` gaining `foundation` and `roof`
(Phase 7), the z stacking index (D11's serialization half), and possibly grid spacing.

**Ruling: an ADDITIVE OPTIONAL field or enum value does not bump the document version.** The
`version: 5` marker describes the *model* — rooms own outlines, vertices are identity, walls
are bindings. Adding an optional stacking index does not change the model, and a reader that
ignores it loses z-order, not correctness. What breaks is an **old validator**, not an old
reader — and the only validator ships with the app.

Mechanically: the schema file gains a revision marker (`$comment: "v5 rev N"` or an explicit
`schema_revision`), every addition is recorded with its date and reason, and
`additionalProperties: false` stays. **A breaking change — removing a field, changing a type,
changing what an existing value means — bumps to v6** and gets its own migration.

**This unblocks D11's serialization half.** It stays AMBER (z-order is user-visible and D11a
already bit once), but it is no longer waiting on a decision.

---

## 3. The work, tiered and ordered

### GREEN — run unattended, merge on green CI

| # | item | why green | acceptance |
|---|---|---|---|
| G1 | **D43** — sweep the suite for negative assertions, measure how many establish preconditions | the first step is *only the count*, deliberately. A measurement | the count, the hit rate, and a proposal sized by the number rather than by intuition |
| G2 | **D48** — scene-level identity check: geometric coincidence implies identity | additive, **report-only**. Must not gate, must not change any operation | it reports on the `fragment` product (10 points / 20 vertices) and is silent on a clean plan |
| G3 | **D27** — the Windows CI leg | additive infrastructure; the DEEP half already closed | a `windows-latest` job exists and runs. **If it goes red, that is a finding, not a failure of this task** — report and stop |
| G4 | **D42** — the party-wall drag's self-intersection exposure | applies §2a's existing ruling to a second site. Same report, new caller. No new semantics | the same actionable message fires on a drag as on a bake, scoped to the rooms the move carried |

Order: G1, G3, G2, G4. G1 and G3 are independent; G2 informs G4.

### AMBER — run, then stop for Patrick

| # | item | ruling status | the manual check |
|---|---|---|---|
| A1 | **D47** — `fragment` produces floating rooms via `extract` | direction ruled; it is the second duplication site `duplicate_wall`'s death never reached | fragment a room, move a piece, confirm it carries its region and no dashed edge lies over a real wall |
| A2 | **D11** — the runtime z collapse | rule fully specified (§2 of the snapshot). **Instrument the hang with a bounded event counter first — do not choose constants to avoid a symptom** | bring-to-front sticks; ghost floors stay behind the active floor; multi-floor banding unchanged |
| A3 | **D11** — the serialization half | unblocked by R‑B | bring-to-front survives save/reload and an unrelated undo |
| A4 | **D49** — deep checks at document boundaries | proposed fix stated | a corrupt plan now refuses to save **by default**; a clean plan saves unchanged. This is a real behaviour change and will be felt |
| A5 | **D41** — the new simple-ring invariant | ruled at R‑A; read-back required | the corpus still validates, `symmetricP1` re-cut with its justification |
| A6 | **Grid snap** | three sub-rulings still open — see §4 | the acceptance already written: shared vertex carries both walls; two coincident ends meet on the grid and weld; a 6″ reveal untouched; identical landing at every zoom |

### RED — do not start

| item | what it needs |
|---|---|
| **Grid snap's sub-rulings** | snap reference point per item class; spacing values; whether grid spacing is a document property (R‑B now permits it, but the *decision* is Patrick's) |
| **Phase 5 — Yard catalog** | artwork scope: which kinds, drawn by whom. D46 closes with it |
| **Phase 5 — settable wall types** | small, but it is the porch-railing feature and the 2D symbol is a design choice |
| **Phase 6 — command undo** | the largest remaining task; retires `snapshot()`. D42's applier consolidation and D45's `_edge_wall` fold in here |
| **Phase 7 — Build menu 7.1 / 7.2** | 7.2 needs `level.kind` additions, now permitted by R‑B but not yet specified |
| **Phase 7 — 7.3 roof** | needs its own design pass. Ridge, eave and pitch are over-determined; the UI must decide which two the user sets |
| **D44** | an accepted limit. Nothing to do — it exists so the boundary of `check()` is known |
| **D45, D46** | carried to Phase 6 and Phase 5 respectively |

---

## 4. Still needing Patrick

1. **Grid snap's three sub-rulings** (§3 RED) — these are the cheapest unlock left: answering
   them moves a whole feature from RED to AMBER.
2. **Every AMBER manual check** — six of them, each ten to fifteen minutes.
3. **Phase 5's artwork scope** — how many Yard kinds, and who draws the SVGs.
4. **The GitHub Issues migration**, when he wants it. Precondition already recorded: none of
   the 15 labels or 20 milestones exist; `--create-labels --yes` runs first.
5. **Who owns truth after that migration** — files mirrored, or issues authoritative and files
   frozen. Recorded as open in `defects/README.md`; needs deciding only when he migrates.

---

## 5. What Code does next

Run the GREEN batch — **G1, G3, G2, G4** — as one sequence. Sub-commit per piece, full gate
each, push each, one report at the end. Merge each on green CI without waiting.

Then stop, and take AMBER items **one at a time**, in order A1 → A6, each ending at a PR with
its manual check scripted Gate-3 style: stated expectations, not a rediscovery exercise.

Record this document's tiers in the plan so the classification is on disk rather than in a
conversation. If a tier looks wrong once measured, that is stop-condition (b) — say so rather
than proceeding on it.
