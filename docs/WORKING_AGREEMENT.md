# Working agreement

> **The standing rules.** Extracted verbatim from `V5_MIGRATION_PLAN.md`
> (its lines 10-291) on 2026-08-06, because these rules outlive the migration
> that happened to be where they were first written down: they bind Phase 5,
> Phase 6 and whatever follows. Nothing below this line was reworded, tidied,
> reordered or reformatted. Where the text says "this plan", it means
> [`V5_MIGRATION_PLAN.md`](V5_MIGRATION_PLAN.md), which is where it was
> written and which still owns the Status table and the phase specifications.

---


This plan is written to be executed by Claude Code in the repo, one task at a time.

**The loop.** For each task: Claude Code reads the task below, implements it, runs the gate, and appends one line to the **Progress log** at the bottom of this file. Then paste the result back here — I verify it against the acceptance criteria, tick the box in the status table, and hand over the next task.

**What I need back from each run**, so I can mark it honestly rather than optimistically:

```
P0.3  <done|blocked>
ruff:    <clean | N findings>
pytest:  <N passed, M failed, K xfailed, S skipped in T.Ts>
files:   <added/changed>
notes:   <anything surprising — especially a test you had to change and why>
```

**Code reaches Claude Code as INSTRUCTIONS, not whole-file handoffs — added 2026‑08‑04, and it is Patrick's rule about Patrick's own habit.** A whole-file replacement sent to be "diffed in" silently overwrites work the repo's discipline already produced: the viewer's B023 closure fix was made at source under the P0.1 standing rule, then lost when a newer copy of `fp3d.py` arrived as a file rather than as a change, and had to be re-applied a second time. The lint bar, the fail-first receipts and the at-source fixes are only worth what they survive; a handoff that bypasses them spends the same effort twice and quietly re-opens closed findings. This applies to the viewer exactly as it does to everything else.

**A green `check()` is not an acceptance criterion on its own — a task that changes what an operation DOES owes a DIFFERENTIAL RECEIPT — added 2026‑08‑04.** `check(deep=True)` answers *is this document legal*. It has never answered *is this the document the gesture should have produced*, and it cannot: a fault that lives in the **transition** is invisible to any check of a single state (row 44 — a resurrected wall passes all fifteen because it is perfectly consistent, just not what the merge produced). So **acceptance = the delta, stated and measured before and after, PLUS the green gate** — never the gate alone. The suite has been doing this without naming it: defect 22's per-room shared-corner table, the 3D popup's byte-identical `design_document()`, the `merge_all` filing (which a green gate would have called a defect and a delta called a non-defect), and every fail-first receipt, which is a delta expressed as two runs. **Binding on the rest of P4.5 immediately** — defect 3's serialization, the z-order collapse, the P3.1 shim retirement and the identity-churn sites each state what they changed, measured, not only that the gate is green. **The Patrick mini-gate is the human instrument for the same class**, which is much of why it exists: a person looking at the plan before and after is a differential receipt with judgement attached.

**When a defect is found by anything OTHER than the invariants, ask whether the invariants could have caught it — and record the answer either way — added 2026‑08‑04.** Found by reasoning, by a test, by a review question: the follow-up is always *would `check(deep=True)` have fired?* **A "no" that goes unrecorded is a hole nobody knows the shape of**, and the answer is worth having in both directions — a fire means defence in depth held and the defect was merely found early; silence is either a gap to schedule or a limit to accept, and saying which is the whole value. It has paid three times already: **row 41** (non-simple outlines pass I5b — asked, answered no, and the `fp3d --dump` cross-check then found real instances in the shipped corpus), and **row 44** (a resurrected wall passes all fifteen — asked, answered no, and the reason is that the invariants check *consistency*, not *history*, so it is an accepted limit rather than a gap). Distinguishing those two outcomes — schedulable gap vs. structural limit — is the point of writing the answer down.

**NEGATIVE ASSERTIONS ARE WHERE VACUITY CONCENTRATES — added 2026‑08‑04, as a predictive rule.** *Absence and prevention are indistinguishable in the result*: a test asserting "X did not happen" passes identically whether X was prevented or was never attempted. So for that class the precondition is **mandatory, not advisory** — a negative assertion must first assert that the conditions for X were present. Evidence it is aimed correctly: two near-misses in two days, both in negative assertions (the P4.5(5) boundary marker that asserted `weld_scene == (0,0)` with nothing weldable in the scene; the row‑36 sibling whose first draft *branched* on the outcome instead of asserting it, and would have gone silent on exactly the change worth hearing). Both were written in the same sessions as the rules they nearly broke, which is not a coincidence — **rules get written precisely where the pull to skip them is strongest.**

**In a test, call the production predicate — do not restate it — added 2026‑08‑04.** The one-definition rule applies to the test layer too, and the test layer is where it is easiest to forget, because restating a condition inline looks like being explicit. Worked example: a P4.5 assertion checked `e.wall is None` to mean "this edge has no wall", when the production predicate is `open_edges()` — and the two differ exactly where it mattered, because an outline goes on NAMING a wall that has left the scene ("dead, not absent"). The restatement was wrong about the very case the test existed for. A test that restates a predicate is a second definition that nobody will maintain.

**Vacuity: an assertion that cannot fail is worse than no assertion, because it reads as coverage — added 2026‑08‑04, in three shapes.** This project has now produced all three, so they are named rather than described:
- **Vacuous by TAUTOLOGY** — the assert cannot be false whatever the code does (`assert … or True`, `assert True`). Written at P4.5(5) and caught before commit.
- **Vacuous by PRECONDITION** — the test never reaches the state it means to judge, so the verdict is about nothing. Defect 21's guard *established the very condition it existed to test* (it read `v.uid`, forcing the mint, then checked the mint); defect 28's "0 stranded" came from 38 synthetic drags that moved the corner in **none** of them, and was discarded rather than quoted.
- **Vacuous by BASIS** — the numbers are real but measured against something that cannot support the claim; P3.8's ratio tests flapped on machine load, so a green meant "the runner was quiet", not "the code is fast".

- **VACUOUS BY BASIS, AT A DIFFERENTIAL — added 2026‑08‑08, and it is the third shape one layer up.** The original instance was P3.8's ratio tests flapping on machine load, so a green meant *"the runner was quiet"*. The same disease reaches **differential receipts**: a differential is only as good as the STABILITY OF THE FIELD IT COMPARES, and a single run of a comparator that flaps is a coin landing heads. Worked example, and the claim was mine: A1b's receipt said *"the macro replay is identical to `main` at every line"* on one run — measured afterwards, that replay's **selection** field has two outcomes on an unchanged tree, 6/6 on `main` and 8/4 on the branch (D56). Its **wall-count** field is a single outcome on both, which is why the sound half of the claim survived and the other half did not. **So: before a differential is quoted, run the comparator twice on ONE tree.** If it disagrees with itself, either repeat until the distribution is the evidence, or compare a field that does not move — and say which you did.

- **UNSATISFIABLE — the MIRROR of vacuous, added 2026‑08‑05 as the fifth shape.** The assert cannot be TRUE whatever the code does. Worked example, and it cost a day: `test_a_clipped_band_leaves_every_room_coherent` compared **walls-moved** against **corners-moved**, and a run of *k* walls has *k+1* corners — so no correct implementation could ever satisfy it. **A test that cannot fail gives false CONFIDENCE; a test that cannot pass gives false DOUBT**, and false doubt is worse in one respect: it sends you hunting bugs that are not there. This one stood as evidence *against* a working mechanism until the arithmetic was checked. **Not machine-detectable**, for the same reason shapes 2 and 3 are not — the assertion is well-formed and its terms are real; only the domain makes it impossible. The tell is a red that survives every plausible fix: at that point stop debugging the code and go and satisfy the assertion **by hand, on paper**. If you cannot, the test is the bug.

**Only the first is machine-detectable**, and `tools/gate.py` now greps `tests/` for it and fails the gate on a hit (`Gate-Census: … vacuous=N`). The other two need a human asking *what did this test establish before it asserted?* — which is why preconditions are asserted before verdicts throughout this suite.

**The vacuity grep's own boundary is one of the five in the instrument-boundary table above** — it knows four literal shapes and not a tautology built from the code under test. Widening it is not obviously right: a pattern general enough to catch `f(x) == f(x)` starts flagging legitimate round-trip assertions, so the limit is stated rather than chased.

**Fail-first receipts: verify the probe actually mutated the tree before trusting its red — added 2026‑08‑04.** A receipt is only as good as the instrument that took it, and an instrument that silently did nothing produces a red (or a green) about the wrong tree — **vacuity one layer up**. Worked example, P4.5(5): the fail-first probe for the visibility guard was applied with a `python -c` replace whose pattern did not match because the file is CRLF on disk; it exited 0 and reported success while changing nothing. Caught by `grep`-ing the file for the restored line rather than trusting the exit code. So: after applying a probe, **confirm the edit is present** (grep the line, or `git diff --stat`) before running the test, and say in the receipt how the mutation was confirmed.

**A boundary-marker test passes in BOTH states, deliberately — added 2026‑08‑04.** When a change is deliberately split across sub-commits, the test asserting *what this sub-commit did **not** change* is doing real work: it marks the line the change stopped at. `test_seeing_a_grouped_wall_is_not_permission_to_merge_it` passes before and after the visibility retirement because it pins the permission guards, which that commit left alone. **A boundary marker asserting that something did NOT happen must first assert that the conditions for it were PRESENT** — otherwise it is vacuous by precondition *by construction*, which is exactly what the P4.5(5) marker was: it asserted `weld_scene == (0, 0)` on two overlapping collinear walls, which have no coincident endpoints, so there was nothing to weld and the zero said nothing about groups. This suite already holds that standard for positive verdicts (the defect‑28 lesson); a negative verdict needs it **more**, because "nothing happened" is also what an empty test reports. **Such a test must declare its own expiry** — this one's rewrite is pre-declared for the `merge_wall` sub-commit — or a future reader deletes it as a no-op that never fails. A boundary marker without a stated expiry is indistinguishable from dead weight.

**Being right from the source is not the same as having measured — added 2026‑08‑04, verbatim, as the one-sentence version of why the pre-work census exists.** It generalises past code to every claim this project makes. Its occasion: a byte-identity claim was taken on `snapshot()` when the claim being defended was *"nothing reached a saved plan differently"*, and the saved-file producer is `design_document()`. The two agree — provably, from the source, because `design_from_scene` canonicalises internally and the extras are window state — and reasoning that out would have been enough to be **right**. It would not have been enough to have **measured**, and the difference is the whole doctrine: a correct inference and a taken reading are different objects, and only one of them survives being wrong about a premise. Re-taken on `design_document()` and on the literal `json.dump` bytes; same answer, now known rather than deduced.

**Retiring a guard: VISIBILITY before PERMISSION — added 2026‑08‑04.** When a subsystem is fenced off from part of the model by several guards, retire the one controlling **what it can see** before the ones controlling **what it may touch**. The intermediate state is then coherent — the subsystem has complete information and still declines to act — and every step is independently revertible. The reverse order produces the incoherent state: a pass acting on geometry the graph it consults cannot see, which is **F1 and F2 rebuilt by hand**. **SEPARABLE ONLY WHEN EACH ACTION GUARD OWNS ITS OWN FILTER — a consumer that derives scope from the view inherits whatever the view admits. Therefore: before retiring a visibility guard, enumerate the view's consumers and identify which scope themselves by it. Those are permission grants in disguise.** Worked example, and it cost a false claim before it was caught: retiring `graph_from_scene`'s group filter (P4.5(5)) silently granted the SHARE half of welding, because `share_coincident_ends` scopes itself by that view rather than filtering groups itself. Measured across the two commits — `weld_scene` on a grouped weldable pair returns **(0,0) at `7a00fe1` and (0,1) at `ac86173`** — after the sub-commit had already claimed "complete information, no new action". Occasion: P4.5's four `group() is None` guards, retired `graph_from_scene` → `merge_wall` → `weld_scene`. **Corollary for reading a watch test across such a sequence:** while only the visibility guard has gone, the guarded action is still unreachable, so a green watch has *not* exercised the risky path. Report it as **"green, but the producer path is not yet reachable"** — a watch that could not have failed must not hand confidence to the sub-commit that follows it.

**A declared test rewrite is the expected outcome of retiring a carve-out — added 2026‑08‑04, at two instances.** `test_grouping_rooms_without_their_walls_still_copies_them` and `test_a_grouped_neighbour_follows_but_is_never_promoted` both had to be **inverted** rather than flipped, and for the same reason: each pinned a **rationale** rather than a behaviour — the first in its name, the second in a docstring that quoted the very premise that expired — so neither could pass unchanged once its reason was gone. **The count of such rewrites measures how load-bearing the retired guard was**, and is therefore evidence the retirement was real. The smell is the opposite case: **a rewrite when nothing was retired**, which is a test relaxed to match code rather than a contract deliberately changed. That distinction is what keeps "a changed test is a red flag" from degrading into "never change a test".

**MIGRATION TELEMETRY RETIRES WITH THE THING IT MEASURED — added 2026‑08‑05, at the `split_count()` ruling, and it is the counterpart to the tidy-up rule below.** An instrument built to find instances of a defect has a natural end: the moment there are none left. Keeping it alive then costs nothing *by itself* — the cost is that every assertion built on it silently becomes unfalsifiable, so a suite of watches reading "this operation caused no splits" turns into a suite of tautologies that still read as coverage. And the only way to keep such a counter *meaningful* is to keep the defect it counts reachable, **which is keeping the defect in order to preserve its alarm** — the same shape as `ungroup`'s plan-wide `merge_all`, a pass whose whole job was absorbing copies that no longer exist. So: **when the last producer of a measured event is retired, the counter retires in the same commit, and every assertion that depended on it is converted rather than left standing.** The six `assert split_count() == before` watches assert the ABSENCE of a mechanism; the property they were reaching for is that identity was preserved, and asserting that directly (the uid is stable, the neighbour is the same object) is strictly stronger — it holds whether or not any mechanism exists to violate it.

**AND THE REPLACEMENT GOES IN AT A DIFFERENT LAYER, which is the more general half.** The counter measured **runtime churn**; what is actually wanted permanently is that the **mechanism cannot return**. Those are different questions, and the second is answered at source, not at runtime: `tools/gate.py` now fails on any coordinate assignment to a wall end (`.p1 = ` / `.p2 = `) anywhere in `floorplanner/`. That is **the pre-work census made permanent** — cheaper than the counter (a grep, not per-move bookkeeping in a hot path), stricter (it catches a writer that no test happens to execute), and it cannot go vacuous, because its subject is the source text rather than a run. **Ask of any retiring instrument: was it measuring the symptom or the mechanism? If the symptom, the replacement usually belongs one layer down.**

**A tidy-up pass that outlives the mess it tidied only touches things nobody asked it to — added 2026‑08‑04, as a general rule.** Recorded here rather than beside the function that prompted it, because it is not an observation about that function. A cleanup exists to repair a specific mess; when the mess is designed out, the pass does not become harmless, it becomes an unexplained side effect of whatever gesture still calls it. Found at P4.5: `ungroup` ran a **plan-wide** `merge_all` whose only job was absorbing the copies grouping used to make. **Measured on the pre-P4.5 tree before filing** — the honest answer mattered, because "it deletes geometry" and "it re-decomposes items" are different defects: scene items fell 80→78 / 82→78 / 83→80 on three plans, but the emitted **document was byte-identical in every case**, so nothing was ever lost; wall count is presentation state (P2.3). The cost was that a local gesture silently reshaped the whole plan's item structure. **Phase 6 meets this rule again when `snapshot()` retires** — the debounced full-document snapshot exists to serve snapshot-undo, and once the command stack owns undo, every remaining caller of it needs re-justifying rather than inheriting.

**A BUG CAN MASK A BUG, SO THE CORRECT FIX PRESENTS AS A REGRESSION — added 2026‑08‑05, at two instances, and it is a rule about how to READ a red.** When a broken mechanism's breakage is what was holding a second fault harmless, repairing the first makes the second visible for the first time — and the repair gets the blame, because the red arrived with it. The diagnostic question is therefore never *"what did my change break?"* but **"was this state reachable before, by a path nobody was measuring?"** Both instances are P4.5's and both cost a parked branch:

* **align/distribute** (`p4.5-align-wip`). A and B share a party wall; B moves; A's wall goes to x=150 while A's outline stays at 120. Split-on-write had been *destroying identity*, and destroying identity is what kept the neighbour intact. Fixing align exposed the missing neighbour gather.
* **`fragment`** (`p4.5-defect23-wip`, ruled 2026‑08‑05). `_corner_records` split every corner an outsider held, which detached the group's walls from every outline, so a group move moved *nothing* and `check(deep=True)` stayed clean — while the gesture stranded the room whole, tore two bystanders open and saved a file recording that nothing had moved. Deform-to-follow did not create that; it made an already-broken product emit a document the invariants can finally see. **Measured both ways before the reading was taken** (`docs/evidence/defect23-fragment.json`), which is the only thing that distinguishes this from a genuine regression.

**The tell, in both cases, is that the pre-change state was WORSE and SILENT.** So a red that arrives with a fix earns a differential receipt on the *pre-change* behaviour before it is treated as a regression — and if the old behaviour turns out to be the worse one, the row that gets filed is against the masked fault, not against the fix.

**A changed test is a red flag, not a detail.** If a task required editing an existing assertion, say so explicitly. Half this migration's risk lives in tests being quietly relaxed to match new behaviour.

**Prompt shape for Claude Code:**

> Read `docs/V5_MIGRATION_PLAN.md`. Do task **P0.3** exactly as specified — no adjacent refactoring, no drive-by cleanups. When done, run `python -m ruff check .` then `python -m pytest -ra`, and append your result line to the Progress log.

**P0.0 first** (below) adds a pointer in `CLAUDE.md` so Claude Code finds this plan without being told each time.

### WHERE A PLAN FILE GOES — three tiers, settled 2026‑08‑09

**A plan dropped in the wrong directory blocks every commit in the repository.**
`tests/test_schema.py` parametrizes over a filesystem glob of `examples/*.json`,
so an imperfect plan there changes the collected count and, if it trips an
invariant, turns the gate red — and the commit hook then refuses everything.
That is [D51](defects/0051-the-census-depends-on-the-working-tree.md), and it
has now happened **twice**: `fragment2room.json` on 2026‑08‑08, and
`wiscaway2026-08-09R.json` on 2026‑08‑09, which arrived with seven real
violations and stopped the gate dead.

| | |
|---|---|
| **`examples/`** | the frozen **clean** corpus. **Nothing imperfect enters it.** Changing a file needs a declared justification and a re-cut freeze |
| **`fixtures/`** | **characterised** failures. Each one named in `fixtures/README.md` with exactly what it violates and why it is retained; a fixture a test depends on carries a guard test that fails when the dirt is cleaned |
| **`fixtures/incoming/`** | **uncharacterised** intake. Patrick drops plans here that break or look wrong. **No test may reference a file here and no parametrized test may sweep the directory** |

**The intake exists because requiring characterisation at drop time puts the
work on the wrong person at the moment they are least able to do it** — and
because the moment a broken plan costs someone a working tree, people stop
reporting broken plans. Triage moves a file **out**: to `fixtures/` with its
README entry, or deleted once its finding is closed.

**AND THE CONTRACT IS ENFORCED, NOT ASSERTED.** `tests/test_fixture_layout.py`
plants a deliberately invalid plan in `incoming/` and fails if any corpus
collector picks it up. Measured when the directory was created: the full gate
ran **GREEN** with a seven-violation plan sitting there, against `1 failed` for
the same file in `examples/`. A structural claim — "the glob is scoped to
`examples/`" — passes whether or not the directory exists or holds anything;
only a plant that MUST be reported if seen makes it a measurement.

### The gate is `ruff check .` over the whole tree — settled 2026‑07‑26

P0.1 found the gate red at baseline: 23 findings, all in `tools/` and `docs/_superseded/` scaffolding committed during the design sessions, **0 in `floorplanner/` or `tests/`**. Four responses were on the table; the deciding fact is that **`.github/workflows/ci.yml:26` runs `python -m ruff check .` over the whole tree**. Narrowing the local gate to `floorplanner tests`, or excluding `tools/`, would make the local gate disagree with CI and leave CI red on the next push — a local gate that is greener than CI is worse than no gate.

So: the gate stands as written, and the 23 findings were **fixed at source** (mechanical: `l` → `lv`, unused loop vars prefixed `_`, `zip(..., strict=False)`, semicolons split, the `math` import hoisted). All three tools re-verified afterwards to produce byte-identical output. `docs/_superseded/` was moved to `_to_delete/` — dead drafts kept alive behind a lint exclusion is exactly how scaffolding rots.

**Standing rule for the rest of the migration:** scaffolding in `tools/` is held to the same lint bar as shipped code, because CI does not distinguish them.

**Corollary found at P0.2** — the divergence cuts both ways. `_to_delete/` was untracked, so the *local* gate went red while CI would have been green. Same principle: the two must agree. `_to_delete/` is now gitignored, which (because ruff respects `.gitignore` for discovery) removes it from both. That directory exists only because the Cowork device bridge cannot delete files on your machine; it is a transfer buffer that should always be empty, and Claude Code should empty it when it appears.

### Three more conventions, settled at P0.2

**Commit at every green gate.** One commit per task, message `P0.x — <task title>`. A 40-task migration with no commits has no rollback points; with one per task, every gate is a place to return to. Nothing is pushed unless asked.

**In a multi-part task, run the FULL gate before each commit, not just at the end.** Found at P0.5: fix 4 was committed after running only `test_selection.py` and turned out to break a test in a different file. Five sub-fixes means five full-suite runs. A targeted run tells you the fix works; only the full suite tells you what else it touched.

**AMENDED 2026‑08‑10, and the amendment is the reviewer's, correcting the reviewer's own phrasing.** *"Gate each commit"* is right for the case it was written for — P0.5's five **independent sub-fixes**, each a tree that genuinely existed and could have been checked out and run. It is wrong for a **series split for legibility**, where several commits are one coherent change carved into readable pieces: those intermediate trees never existed. Gating them would mean stashing the not-yet-committed remainder, and `git stash` / `checkout` against uncommitted work is precisely what the *"destructive experiments run in a worktree"* rule below forbids — so the instruction, read literally, ordered the one manoeuvre most likely to destroy the work it was protecting.

**THE RULE, RESTATED SO IT COVERS BOTH:** **gate every tree that will exist in history as a state someone could check out and run** — which for independent sub-fixes is each commit, and for a split-for-legibility series is the final one. **And say plainly in the report which trees were gated.** The second half is not optional: a reader seeing four commits and one gate line must be told that is deliberate, or they will read it as a gate that was skipped.

Occasion: D63's producer-1 close landed as three sub-commits — instrument, guard, record — from one tree, with one full gate on the complete state. The implementer gated the whole tree, committed the slices, and *volunteered* the discrepancy unprompted. **The volunteering is what turned a defensible exception into a rule**; a silent version of the same thing would have been indistinguishable from carelessness, which is the whole reason the disclosure half is written down.

**`Touches` lists are hints, not contracts.** P0.2's list named `test_io.py` (which references none of the removed names) and missed `test_inventory.py` and `test_walls.py` (which do). Follow the code, do the task, and report the divergence in the log — that is what happened, and it is the correct behaviour. I write these lists from static analysis; the compiler is a better authority than I am.

**Annotating a doomed assertion means naming the *specific* task**, not "Phase 3". If no task actually retires it, say so rather than inventing one.

### Push policy — settled at P0.3

**Commit per task; push per phase.** With one exception: **push once now, at the end of Phase 0's safety net.**

The reason is that `.github/workflows/ci.yml` triggers on push and PR only, so **nothing in this migration has ever been validated by CI.** Local runs are py3.13 on Windows; CI is py3.10 *and* py3.13 on `ubuntu-latest`. Those differ in ways that matter — Qt offscreen font metrics, path handling, and py3.10 syntax support. Discovering a py3.10 break at P1.4 means bisecting a stack of commits instead of reading one failure.

Pushing per *task* is the wrong granularity: 40 pushes is noise, and a phase boundary is the natural "coherent, shippable state". Pushing per *phase* after this first one is the rule. Phase 3 runs on `v5-topology` and pushes there.

**Before the first push, the timing tests need a marker of their own** — see P0.3b step 3. Ratio assertions on shared CI runners flap; that is a well-known false-positive source and it would poison the signal we just built.

### Doc edits are Cowork's, committing is Claude Code's — settled at P0.6

The Cowork device bridge writes into the working tree but **cannot run git**. So every doc edit handed back (a re-ticked status table, a new rule, an amendment) sits **uncommitted** until Claude Code commits it — and any `git checkout` / `restore` / `stash` in between silently discards it. Root cause of the P0.3b/P0.4/P0.5 checkbox drift: the ticks were written to the working tree but never committed, then overwritten.

Two rules:

**Commit handed-back doc edits immediately, as a doc-only commit, before running any git that could discard them.** A doc edit you can see on disk but have not committed is one `checkout` away from gone.

**Verify the status table on disk, not from a summary — including your own.** `grep '☐\|☑' docs/V5_MIGRATION_PLAN.md` before claiming a task is ticked. A summary (yours or mine) is not the file. And if a Progress-log entry goes missing after a hand-back, that is a regeneration bug on my side — say so rather than committing the lossy version.

**Root cause of the three doc-loss incidents — identified at P0.6, and it is Cowork's.**
`device_stage_files` reports the device's true file size but can serve a *stale*
container-side copy from an earlier stage. Measured: the tool reported 46,942 bytes
while the copy it produced was 38,760 — a version several commits old. Editing that
stale copy and writing it back overwrites newer work with older content, which is
exactly the damage seen at P0.4, P0.5 and P0.6.

**Consequence: Cowork no longer edits ANY FILE IN THE REPO DIRECTLY.** Changes of
every kind — plan, review, notes, code — are handed to Claude Code as explicit edit
instructions; Claude Code applies them, commits, and grep-verifies on disk. One extra
round-trip, and the only channel that has destroyed work in this project is closed.

**WIDENED 2026‑08‑04, at a second instance the original wording did not cover — and
the new instance defeats the check that caught the first one.** As first written this
rule named two files, this one and `CODE_REVIEW_v2.md`, because those were the two
that had been damaged. The mechanism is not file-specific. On the viewer branch,
`device_stage_files` served a **stale** copy of `floorplanner/viewer/VIEWER_NOTES.md`
**while reporting the correct byte count** — so the size disagreement that exposed it
at P0.6 (46,942 reported against 38,760 delivered) was **absent**, and writing that
copy back would have destroyed committed work in a file the rule did not mention. A
near-miss, caught before the write, and only because the file was re-read from disk
rather than trusted. **A rule enumerated from its instances protects exactly its
instances**: the correct scope of a rule is its mechanism's scope. That is the same
correction defect 7 took when it closed by the CONDITION rather than by its four
cited sites, and the same reason a size check is not a freshness check.

### The gate must be checked, not printed — settled at P3.6

**`python -m pytest -q | tail -1 && git commit` does not gate anything.** A
pipeline's exit status is the LAST command's, so `&&` was testing `tail`, which
always succeeds. Every gate run in that shape reported its counts honestly and
enforced nothing — which is how P3.6(3) came to be committed with **two errors**
in the ON and DEEP runs, visible in the very output that was pasted into the
commit message.

The errors were real and were shadow mode doing its job (`I7: 0 -> 1`, an
opening pushed off its wall by a width change). They were found and fixed
minutes later, so nothing shipped broken — but they were found by *reading* the
output, which is exactly the manual step the gate exists to replace.

**Run the command, capture its status, then print.** A helper that stores the
output, keeps `$?`, echoes the tail and returns the status; or simply
`set -o pipefail`. Never `... | tail -N && <next step>`.

### Truncation invites fabrication — settled 2026-08-07

**`| tail` has now caused two different failures, and they are not the same
failure.** The first was mechanical: `pytest -q | tail -1 && git commit` tested
`tail`'s exit status, so the gate enforced nothing (above). The second was
human, and it is the one worth naming separately.

`tools/gate.py | tail -3` shows the DEEP line and the verdict. It hides the
OFF and ON lines. At `47f9675` the trailer pasted into the commit message
therefore had two lines that had **never been on screen**, and they were filled
in from an earlier run: `17.28s` / `20.55s` quoted, `17.14s` / `19.79s`
recorded.

**The mechanism is the point. A truncated output does not read as incomplete —
it reads as output.** Nothing prompts for the missing part, so the gap is closed
from memory, and memory supplies something plausible. That is the identical
disease as "515 collected" quoted after two more tests landed, arriving through
a different door: the transcription class is *a number carried between two
moments*, and this is *a number invented to fill a hole the tool never showed
you*.

It is also why the harm looks small and is not. The fabricated values were two
wall-clock durations — the least consequential figures in the block, which is
exactly why nobody would check them. Everything that decides anything was
correct and the gate had genuinely passed. **A trailer that is right about
everything that matters and wrong about two numbers is still not a verbatim
trailer**, and the whole value of that block is that it can be trusted without
re-deriving it.

**So: never truncate a gate, a census or any output you are about to quote.**
Read it whole, or have the tool hand you the text — `tools/gate.py --trailer`
reprints the stored block for redirection into a message file, which removes the
human from the copy entirely. `--quick` and `--deep` deliberately do not write
that block, so neither can be quoted as a full-mode run.

**AND STATE WHAT THE GUARDS DO NOT COVER.** The commit hook closes *did the gate
run, green, on this tree*. It does **not** close *does the message describe the
run* — it never reads the message. Two guards, two questions; the second one was
open until `--trailer` existed. An unstated boundary reads as coverage, which is
how a gap survives behind two working instruments.

### Destructive experiments run in a worktree, or after a WIP commit — settled at P3.5

**Never against uncommitted work.** `git checkout <file>` has no undo. At P3.5 it
was used to revert a deliberate break-it-to-prove-the-test experiment (making
the two defect-8 regressions fail on purpose, to confirm they catch what they
name — which is the right thing to do) and it took that file's *uncommitted*
work with it.

The solution was already in use in the same task: the P3.5 perf comparison ran
the old code in a `git worktree`, which cannot touch the working tree at all.
So: **`git worktree add --detach <path> <ref>` for anything that needs the code
in another state, or commit first and experiment on top.** The P3.5-followup
verified its five new tests against pre-fix code exactly that way, and found
that one of them passes on both sides — which is a finding the experiment only
surfaces if it is safe enough to run.

The doc-edit rule below is the same rule for a different asset. Stated once
here so it does not have to be re-learned per file type.

### A checkpoint is not complete until its handoff spec is committed — settled at P3.3

**Session-end summaries and hand-off prompts are chat, and chat is not the record.**
The P3.3 boundary proved it: the "five settled points" that fully specified the task
existed **only in conversation**. The commit that was supposed to carry them
(`3d6d32e`) changed exactly two lines — the defect 12a row and the P2.3 regression
row — and the Progress log still ended at P3.2. Only the read-back verification
caught it.

**So: before ending a session mid-task, commit the spec** — into the Progress log or
the task text — **then summarize.** The summary describes what was committed; it is
never the thing itself.

And the read-back is the check that makes the rule enforceable, so it stays: **quote
what disk supports, name what it doesn't, proceed on the verified subset.** A number
that cannot be found on disk is not quoted back as though it were — at P3.3 the
"72 splits" figure appeared nowhere in the repo, and saying so is what surfaced the
gap rather than papering over it.

### The pre-work census is a phase of the task, not a virtue — settled 2026‑07‑31 at the P4.1 read-back

Task-line deletion figures have now failed checking three times: P3.4's estimate
(375 across 13 functions; measured 149 across 7), P3.5's rider table (~470;
measured 450 with two named divergences), and P4.1's ("`_perimeter_span` falls
with `fracture_delete_wall`" — on disk twice and false; it has two callers that
outlive fracture, so P4.1 deletes 66 lines, not 90). Doctrine: **every task
opens with a fresh census of what it deletes and touches, run against the tree
at task open, and the read-back protocol is its enforcement.** A task-line
number is an estimate until the census confirms it; the census is quoted with
spans and callers so the reviewer can check it without re-running it.

**IT COVERS BEHAVIOURAL CLAIMS AS MUCH AS COUNTS, AND SURVIVAL JUSTIFICATIONS
MOST OF ALL — added 2026-08-04.** A count reads like a number and gets checked;
a sentence about what the code *does* reads like understanding and does not.
P4.5's guard census asserted *"grouped ends never weld"* — measured, the snap
half filtered and the share half never did. **And when a row explains why some
code SURVIVES a phase that killed its relatives, that explanation asserts what
the code does and who calls it — a behavioural claim wearing a rationale's
clothes. Measure the justification before filing the row.** Row 45 justified
`_edge_wall` with *"outlines arriving from a file"*; measured, no file path
calls it at all — the loader reads the stored binding. **Both unmeasured claims
in that stretch were justifications, and both were caught only because the
measurement was asked for**, which is why this is a rule rather than a
reminder: a justification is the most dangerous claim to leave unmeasured,
because it is written precisely to explain why nobody needs to look further.

**A CENSUS BY SPELLING FINDS ONLY THAT SPELLING — added 2026‑08‑06, at the SECOND instance, and this one is measured rather than noticed.** When the thing being counted is a *call shape* rather than a name, a grep counts the shape you thought of. The two instances are the same shape twice:

* **P3.6's split-on-write exit survey** counted *"9 direct coordinate-assignment sites"* and listed all nine by the `.p1 = ` / `.p2 = ` spelling.
* **P4.5(40)'s census** repeated it exactly — 22 writers, same grep — and missed **five** of the form `setattr(wall, attr, <point>)`, with `attr` a variable. They surfaced as `AttributeError` the instant the setters were deleted.

**Measured, and this is the part that makes it a rule rather than an anecdote:** those `setattr` writers were already there at **`03f3868`** (the Phase 3 merge — four of them) and at **`adaa519`** (the P4.4 merge — five). So P3.6's "9" was really 13, and **the same blind spot survived two censuses and the whole of Phase 4 undetected**, because both censuses reached for the same instrument. A second measurement that repeats the first one's method does not corroborate it — it inherits its blind spot and dresses it as confirmation.

**So: the next census of a CALL SHAPE reaches for an AST walk or a runtime probe, not a grep.** `ast` sees `Assign` to an `Attribute` and a `Call` to `setattr` as what they are, whatever the attribute name is spelled by; a probe (make the property raise, run the suite) finds every reachable caller regardless of spelling. A grep stays fine for a NAME — `git grep detach_end` is exact — and that distinction is the whole rule: **grep for identifiers, parse for shapes.**

**The corollary is the cheaper half:** the deletion found what the census could not. Removing the thing and reading the failures is a census, and often the only complete one — which is an argument for retiring a mechanism *before* believing you have enumerated its callers, not after.

**EVERY INSTRUMENT IS VALIDATED AGAINST A CASE KNOWN TO BE NON-ZERO BEFORE ITS ZERO IS BELIEVED — added 2026‑08‑09, as a REQUIRED PRACTICE rather than a caution.**

**A zero from an instrument earns the same suspicion as a green from a test that may not have run.** Both are the absence of a signal, and absence is what a broken instrument produces most readily. The mechanism is a **positive control**: before trusting that an instrument reports nothing, point it at a case that MUST report something and confirm it does.

**Two instruments failed this way within one measurement**, and both produced a confident zero:

* a vertex census reported **degree-2 = 0 on a 103-wall plan**. `WallItem.v1` returns the vertex's **UID string**, not the object; `_v1` holds the `Vertex`. An `isinstance` filter then silently dropped every wall corner. 206 ends over 97 objects averages 2.1, and *that* implausibility is what caught it — not the instrument.
* a call counter reported **no split at all** during a gesture that provably splits. `extract.py` does `from floorplanner.walls import split_wall_at`, so wrapping `walls.split_wall_at` left extract's own name bound to the original. **The wrapper was bound to the wrong reference.**

**Both are "grep for identifiers, parse for shapes" arriving INSIDE THE MEASURING APPARATUS**, which is the worst place for it: the apparatus is what the rest of the reasoning rests on, so its error propagates into every conclusion drawn with it rather than being one wrong number among many. A census with a blind spot yields a wrong count; an *instrument* with a blind spot yields a wrong **story**.

**A positive control would have killed both instantly** — a plan with a known junction must report degree-2 > 0; a gesture known to split must report a split. Neither needed insight, only a case with a known non-zero answer.

**So: name the control when the instrument is written, not after it disagrees with you.** And when an instrument reports zero, the question is never *"is the code clean?"* but **"would this instrument have reported the thing if it were there?"**

**AN ACCEPTANCE STATED AS A COUNT IS SATISFIED BY REPLACEMENT — added 2026‑08‑10, and the error being recorded is the REVIEWER'S OWN.**

**When the question is whether a specific thing PERSISTED, the measure must be an identity, not a total.** A count cannot distinguish *forty survivors* from *forty removals and forty fresh insertions at other points*. Both read as forty.

**The instance, and it is not a near-miss.** D63's durability acceptance was issued as *"40 of 40 survive a save"* and implemented as `assert slots() == in_session` — the total of every room's outline length. On `roundedMultifloor` that total goes **187 → 181 → 187**, returning exactly to where it started, so six corners removed and six inserted **elsewhere** read as *nothing survived*. The record then carried `6 removed / 0 durable / 6 rebound — UNRESOLVED` for that plan across two handoffs, and a floor-scoping hypothesis was written and refuted against a failure that had never happened. Re-measured per `(room, point)`: all six are durable, rebound is **0**, and the six in the file are producer 2 — which the wall-pass-alone lane inserts at exactly the same places.

**So the whole rebound investigation — two producers, an exact arithmetic identity, a refuted causal hypothesis — rested on a metric that could not answer the question it was asked.** The identity and the two producers survive re-measurement; what does not survive is the row that sent a session hunting a cause.

**THE PAIR IS MORE INSTRUCTIVE THAN EITHER HALF, which is why both are cited here.** This project has met this distinction twice, and caught it once:

* **CAUGHT — the 28-versus-40 case.** D61 stage 2a reported *69* corners a person can see, *40* slots the strict predicate vacated, and *28* vertices behind them. Those three numbers were deliberately kept apart and reconciled with **one instrument**, precisely because a slot and a vertex and a complaint are different objects and summing them would have hidden which was which. The reconciliation was the point.
* **NOT CAUGHT — this one.** The same instrument family, the same session, one measure taken as a total instead of a reconciliation — and the damage was a *reported failure that had not occurred*, which is the direction nobody audits. A false red is not the safe kind of error: it is the kind that gets investigated.

**The cheap form of the rule is a SET EQUALITY IN BOTH DIRECTIONS** — nothing in A that is not in B, and nothing in B that is not in A. That is what separated `rounded`'s producer 2 from its supposed rebound: two lanes each inserting six could otherwise have been two different sixes. **Ask of any surviving-count acceptance: would it read the same if every item were replaced?** If yes, it is not measuring persistence.

**AND ITS SIBLING: AN ACCEPTANCE MUST NAME THE MECHANISM IT IS MEASURED THROUGH — added 2026‑08‑11, and it is the same failure at the other end.** The count rule catches an acceptance **satisfied by REPLACEMENT**. This one catches an acceptance **satisfied by ABSENCE**: a test that drives the code through a path which never reaches the thing under test passes against an implementation that fixes nothing, and its green is about the driver, not the code.

**The instance, and it was caught BEFORE the test was written rather than after — the first time that has happened here.** D61 stage 2b's acceptance was ruled as *"a six-move walk ends with the counts it started with"*. Measured: a walk that moves the room with **`setPos`** reports **`0,0,0,0,0,0`** — because a floating room's walls are moved by **`_translate`**, not by the item's position, so `setPos` **never reaches the producer at all**. A 2b test written that way would have been **vacuous by precondition** and would have gone green against code that changed nothing. With `_translate` the producer fires — and **oscillating, not monotonic**, which is a second correction to the same acceptance.

**So an acceptance states its driver, not only its assertion.** *"A six-move walk"* names neither what moves the room nor what shape the counts take; *"a six-move walk driven by `_translate`, whose counts return to baseline whenever the room lands back on its berth"* can only be satisfied by reaching the code. **The two rules together:** ask whether the assertion could pass with every item replaced (the count rule), and whether it could pass without the mechanism ever running (this one).

**PARASITIC REACH: WHEN YOU REPAIR A CAPABILITY THAT NEVER WORKED, BUDGET FOR THE AFFORDANCES RESTING ON THE FAULT — added 2026‑08‑08 at the FIFTH instance, and it is named so it can be cited.**

A defect that has been in a product a long time stops being only a defect. Things come to depend on it — some of them code nobody exercises, and some of them **features the user learned as the way the application works**. Repair the fault and those go with it. **The second kind is reported as a regression, by the person who depended on it, and they are not wrong to call it one.**

The five, all downstream of one thing — `RoomItem.shape()` returning only the label rect, so a click inside a room reached no item and the view called it blank canvas:

| # | what was resting on it | record |
|---|---|---|
| 1 | **room selection** — a room could not be selected by its region at all | [D53](defects/0053-a-room-cannot-be-selected-by-clicking-its.md) |
| 2 | **the room context menu** — reachable only from the label; deleting the blank-canvas clause made it unreachable entirely for one commit | D53 |
| 3 | **room naming** — the Room tool's *"click the enclosed space"* route, which the reporter had learned as the way to name a region | D53, and the account in [D57](defects/0057-face-at-hands-walls-of-a-report-of.md) |
| 4 | **a crash that turned out not to be A1b's** — four hypotheses were built on the assumption that it was | [D57](defects/0057-face-at-hands-walls-of-a-report-of.md) |
| 5 | **the 3D viewer** — `show_3d_view` had two call sites, both blank-canvas right-clicks, no menu entry, no shortcut, no button | D53's affordance report, `evidence/d53-blank-canvas-routes.txt` |

**The first three are the ordinary shape: dead code and unreachable paths, found by fixing the thing.** The fourth is a warning about diagnosis — a defect *adjacent* to the repair attracts blame for it. **The fifth is the expensive one**, and it is the reason this has a name: a whole feature, reachable *only* through the fault, with no other route. On a plan that fills the canvas the renderer could not be opened at all, and nothing said so, because the fault was providing the reach.

**The consequences, in the order they bite:**

1. **Expect the census to be incomplete.** The blank-canvas affordance census found **four** features on that path where the question had been asked about one. Ask what is REACHED through a fault, not only what is BROKEN by it.
2. **A fix that removes reach must restore it in the same merge.** Not a follow-up. A user who loses a route does not care that the record says it was accidental.
3. **The replacement is a design question, not a mechanical one.** *Where* the 3D viewer belongs is not "wherever it used to appear" — it got onto blank canvas by being put where there was space, and repeating that is how the next instance is made. It got a View menu; **"there was room for it" is not a reason, and it was not accepted as one.**
4. **Expect the report to arrive as a regression**, and expect the reporter to be describing a real loss in the vocabulary they have.

**A REPORTED REPRO IS TESTIMONY, NOT MEASUREMENT — added 2026‑08‑08 at D57, and it cost four hypotheses.** A user's account of what they did is a **hypothesis about what happened**, and it earns exactly the scrutiny any other premise does. It arrives sounding like data because it comes from the person who was there — but they are reporting an intention and a memory, not an instrument reading.

**THE FIRST QUESTION TO ASK OF ANY REPORTED REPRO: can the application even reach the state described?** It is nearly always the cheapest check available, and it is the one that gets skipped.

Worked example, and the four hypotheses were the reviewer's own: the report was *"delete the name of the room, not the actual room"*, and four theories were built on an unnamed room — a destroyed label item, room identity across a re-derivation, a name-keyed lookup breaking on `""`, and a menu clause mis-firing on a live room. **Measured, no UI route can empty a name**: `RoomItem._rename` guards `if ok and name.strip():`, `RoomPropertiesDialog.apply` guards `if name:`, and the schema rejects `""` outright. The state the whole search was aimed at **does not exist**. What the user had actually done was **delete the room** — the room menu's *Delete room*, which leaves the walls standing, so the enclosed space becomes nameable again. One reading of one word, four dead branches, and a real crash sitting somewhere else entirely.

**The check is not "is the user wrong".** They were right that the app crashed, right about which gestures produced it, and right that it was worth reporting. They were describing an outcome in the vocabulary available to them. **Reproduce from the report, then verify the reproduction reaches the state the report names** — and when it cannot, that gap is itself the first real evidence, because it says the mechanism is elsewhere.

**AND IT EXTENDS PAST THE USER: AN IMPLEMENTER'S REPORT IS TESTIMONY TOO, AND SO IS A REVIEWER'S RESTATEMENT OF ONE — added 2026‑08‑10, ruled by the reviewer against the reviewer.**

The rule above was written about a *user's* repro. That scoping was too narrow, and the narrowing is the same shape the rule itself warns about: it enumerated its instance instead of its mechanism. **Every report is testimony, whoever writes it** — and a number restated by a reviewer is testimony that has been *promoted*.

**A CRITERION RESTATED FROM A REPORT INHERITS THE REPORT'S ERRORS.** The implementer's report said *"10 genuine rebounds on `wiscaway`"*. The reviewer quoted that back as the acceptance criterion for the control — *"if it reports the ten genuine rebounds on wiscaway, the zero is validated"* — and the restatement is what gave the figure authority it had not earned. Measured, the ten are **`roundedMultifloor`'s**; `wiscaway` has four. The reading came from a parametrised pytest failure block whose room names (`Master Suite`, `BR3`, `MBATH`) were read past, only `Rear Porch` existing in both plans.

**Nothing was harmed, and that is the point rather than a mitigation.** The control passed on its real numbers (17 pre-fix against 0 post-fix), so the criterion would have been met either way. Had it not been — had `wiscaway` alone been checked and found at 4 where 10 was demanded — a *passing* control would have read as a failure, and the instrument would have been rebuilt to satisfy a number that was never true of it.

**THE MECHANISM: WHEN A REVIEWER QUOTES A NUMBER BACK AS A GATE, THEY LAUNDER A MEASUREMENT INTO A REQUIREMENT.** On the way out it was an observation with a provenance and an error bar; on the way back it is a threshold, and thresholds do not get re-derived — they get met. The round trip strips exactly the property that made it checkable.

**So an acceptance criterion carries its provenance, or it is not a criterion:** name the artifact the number came from (which run, which plan, which file), and re-read it at the instrument before it gates anything. **The implementer's obligation is the mirror of it — when a reviewer restates your figure, check the restatement against your own output before working to it.** That is the step that was skipped here, on both sides.

**A CENSUS INHERITS THE BLINDNESS OF THE PREDICATE THAT SCOPES IT — added 2026‑08‑08, at a regression a manual check caught and 646 green tests did not.** The census rule already said *grep for identifiers, parse for shapes*. This is the next layer up and it is about the QUESTION, not the instrument: A1b's hit census was scoped to *"sites where `itemAt(...) is None` stands for blank canvas"*, answered that completely and correctly — and was therefore structurally incapable of reporting a menu reached by any other route. A ruling asserted that no room context menu existed; the census could not contradict it, because contradicting it was outside the question. `RoomItem.contextMenuEvent` is **68 lines** and offers *Extract room* and *Join room into plan*.

**AND THE SHARPER HALF, WHICH IS WORSE AND IS THE REASON THIS IS A RULE.** The fact was not actually absent from the output. The same census's *items* table listed `contextMenuEvent` among `RoomItem`'s handlers, one section above. **It was on the page, under a heading that answered a different question, and was read for the question that had been asked.** So the failure is not only "the scope excluded it" — it is that a scoped reading makes you blind to material already in front of you. Re-deriving the scope is not enough; the tell is a *claim of absence*.

**SO: A CENSUS MAY NEVER ESTABLISH THAT SOMETHING DOES NOT EXIST unless its question was "does this exist?"** Absence claims need their own census, scoped by the thing claimed absent and by every mechanism that could provide it — for a menu that means `contextMenuEvent` overrides, `QMenu` construction, `.exec` sites, `setContextMenuPolicy` / `customContextMenuRequested`, and shared builders. Run that way it found **eight** overrides where the predicate-scoped census had reported two sites, plus a ninth path (`StairItem`, its own 47-line menu) neither party had named, and one clean negative worth having: **this application uses the signal route nowhere at all.** `docs/evidence/d53_menu_census.py`.

**The counterpart, and it is cheap: a census cannot tell you a handler is REACHABLE.** It proved `RoomItem.contextMenuEvent` exists; only a runtime probe showed the view above it was accepting the event first. Existence is a parse question, reachability is a run question, and they are different files here on purpose.

**A GREEN SIGNAL IS ONLY EVIDENCE ABOUT WHAT IT MEASURES — added 2026-08-04, as
the rule above three instances.** `tools/gate.py` has never made a claim about
`docs/V5_MIGRATION_PLAN.md`: it runs ruff and pytest, and neither reads this
file. That is not a bug in the gate; it is **the boundary of what its green
means**, and the failure mode is borrowing confidence across that boundary.
Every artifact a task changes needs the check that covers *it*:

| artifact changed | the check that covers it |
|---|---|
| code | `tools/gate.py` (ruff + the three modes, sums reconciling) |
| the record (plan, register, notes) | `tools/record.py` — anchored edit, re-read from disk, non-zero if the text is not there afterwards |
| what an operation DOES | a **differential receipt** — measured before and after (row 44) |
| a document's legality | `check(doc, deep=True)` — and only legality; never "is this the document the gesture should have produced" |

**THE COROLLARY — AN INSTRUMENT'S NAME ALWAYS SUGGESTS A BROADER QUESTION THAN
IT ANSWERS, added 2026‑08‑05 at the fifth instance.** The boundary is invisible
from the name, which is exactly why it gets crossed: nothing about `vacuous=0`
says *"none of four literal patterns"*, and nothing about `split_count()` says
*"split-on-write only"*. So **state at the instrument the question it actually
answers, and state what it does not cover** — the second half is the one that
gets skipped, and it is the one that stops a green being borrowed. Five
instances, all found by walking into the boundary rather than by foreseeing it:

| instrument | the question it answers | what it does NOT cover |
|---|---|---|
| `check(doc, deep=True)` | is this document CONSISTENT? | its HISTORY — a resurrected wall passes all fifteen (row 44) |
| `tools/gate.py` | is the CODE green? | the record; it runs ruff and pytest, and neither reads a `.md` |
| the vacuity grep | does any test match one of FOUR literal unfailable shapes? | a tautology built from the code under test (`assert f(x) == f(x)`) — written once at P4.5(22) and caught by a re-read, not by the grep |
| ~~`vertex.split_count()`~~ **RETIRED P4.5(40)** | how many SPLIT-ON-WRITES happened? | identity change as such — P4.5(24)'s deliberate detach went through `Vertex.at` and reported **0** while changing identity. It retired *with the mechanism it measured*: with nothing able to split, six watches built on it would have become tautologies. |
| `tools/gate.py`'s `end_assign` | does the source TEXT contain a coordinate assignment to a wall end? | the same operation spelled any other way — `setattr(w, attr, p)` passes it, and **five real writers were in exactly that shape**, found by the deletion rather than by the check (P4.5(40)). It also cannot tell code from prose, so it is the one instrument here that errs toward FALSE POSITIVES. |
| `validate._seg_cross` | do two edges PROPERLY cross? | a loop that is non-simple by *touching* — deliberate, so it cannot fire on the collinear edges two rooms share (row 41) |
| the **room-operation suite** (`test_rooms.py`'s boolean tests) | given two rooms as input, does the operation produce the right geometry? | **HOW A ROOM COMES TO BE SELECTED.** `_overlapping_rooms` ends `win._sel_order = [r1, r2]` — the selection list is *assigned*, so no `setSelected`, no mouse event, and `_update_edit_actions` never runs. Measured at D53 (2026‑08‑08): cutting the only path from a Qt selection to `_sel_order` leaves **all 639 tests passing**. |

| `scene_identity_report` (D48/G2) | do two WALL ENDS at one point share a vertex? | **whether a ROOM OUTLINE shares the wall's vertex.** Measured 2026‑08‑09 at [D62](defects/0062-weld-scene-leaves-room-outlines-holding-a.md): after `normalize_walls` it reports `extra_vertices` **0** on four of five plans while **49–78 outline corners hold a `Vertex` no wall holds**. Not broken — the outline question is outside the one it asks, and the two look identical from outside |

| the **whole suite**, for one gesture family | everything it does cover | **THE Ctrl+DRAG SELECTION BAND, which it cannot reach at all.** `QRubberBand.show()` on an OFFSCREEN viewport takes the process down — measured 2026‑08‑08 and **pre-existing on `main`**, so no headless test has ever covered that gesture or could. |

**AN INSTRUMENT THAT REPAIRS WHAT IT MEASURES REPORTS HEALTH IT MANUFACTURED — added 2026‑08‑10, and it has no precedent in the table above.** Every other entry is *"this instrument answers less than its name suggests"*. This one **answers a question it has already made true**.

The occasion is D63's producer 2 — a stored room outline crossing a point where walls end without naming it. **Two instruments miss it, and they miss it in two DIFFERENT ways**, which is why the pair is recorded rather than either half:

| instrument | why it cannot see it |
|---|---|
| **I14** | compares **wall ends to WALLS** (`validate.py:283`). A room OUTLINE is outside its subject entirely. **WRONG SUBJECT** — the ordinary boundary, the same shape as `scene_identity_report` being blind to whether an outline shares a wall's vertex |
| **I5** | cannot fail on a **saved** document, because `bridge._walk` emits one outline edge per wall **BY CONSTRUCTION**. Asking repairs it. **A QUESTION THAT DESTROYS ITS OWN EVIDENCE** |

**The second is the dangerous one, because its silence is indistinguishable from correctness and no amount of running it more often helps.** A normalising step between the fault and the check launders the fault: the state is real, the file on disk carries it, and the check is answering about a *different document* — the one the walk just built. **Ask of any check that runs downstream of a canonicalisation: is it reading the artifact, or the canonical form of the artifact?** Where those differ, the check has an opinion only about the second.

**The corollary is the reason the ruling paired the detector with the reclassification.** A fault only visible in a stored-versus-emitted difference has no home in an invariant set that only sees emitted documents — so it must be restated as **a direct property of the bytes** before it can be checked at all (`handoff/0006-readback-outline-invariants.md`). *"The files were always non-compliant"* is a diagnosis when a detector exists and an excuse when one does not.

**THE MECHANISM THAT MAKES A FAULT HARMLESS CAN BE THE SAME MECHANISM THAT MAKES IT INVISIBLE — added 2026‑08‑09 at D62, and it is the sharpest entry in the table.** The boundaries above are all *"this instrument answers less than its name suggests"*. This one is a **coincidence of mechanism**, and it is the reason "legal under v5 and unreachable by two separate checks" must never be read as "harmless".

`weld_scene` leaves 49–78 room outline corners holding a `Vertex` no wall holds. **`check(deep=True)` cannot fire on it**, because `design_from_scene` welds on the way out and the emitted document has one vertex per point whatever the scene holds. **And the divorce does not survive a save** — 49 → 0, 56 → 0, 78 → 0, 57 → 0, measured — *for exactly the same reason*. **One mechanism, two effects, opposite signs:** the weld bounds the harm to the session and hides it from the only check that could have reported it.

**So the severity finding and the invisibility finding are not independent evidence** — they are one fact read twice, and treating the second as corroboration of the first would be counting a single mechanism as two. The honest statement is: *the fault is bounded BECAUSE it is invisible to the layer that would otherwise have to represent it.* Ask of any state that survives every check: **is it clean, or is it being normalised away by the same step that would have had to record it?**

**And the state was not harmless.** `close_gap` already repairs it (`walls.py:1101`), with a comment naming the symptom — diagonal tears in M Bath / Hall / Lounge, found by a **manual check** at the P4.2 mini-gate. Two automated checks were structurally silent; a person dragging a wall found it.

**THE SIXTH ENTRY IS A DIFFERENT SHAPE FROM THE OTHER FIVE, AND IT IS THE ONE THIS PROJECT HAD NOT MET — added 2026‑08‑08 at D53.** The five above are boundaries of *one instrument*: a function answers a narrower question than its name suggests. This one is a boundary **between two layers that are each correctly tested**. The room operations are covered from `_sel_order` inward; the click handlers are covered from the mouse inward as far as the label. Neither layer is under-tested. **The seam between them is covered by nothing, and it is invisible from either side** — which is why 639 tests and six green CI jobs coexisted with a room that could not be selected by clicking it.

**VACUITY BY PRECONDITION AT AN INTEGRATION SEAM.** It is the fourth shape's habitat, not a new shape: the precondition (`_sel_order` holds two rooms) is established *by the test itself* rather than by the mechanism under test — defect 21's guard, one layer up. What makes it harder to see is that the substitution is **legitimate at the unit altitude**: a polygon operation *should* be tested from a constructed input. The fault is not in that test; it is that no test exists at the other altitude, and nothing anywhere says so.

**THE SEVENTH ENTRY NAMES A GESTURE FAMILY THE SUITE CANNOT REACH, AND THAT IS WHY IT IS IN THE TABLE — added 2026‑08‑08 at D53, on the ruling that it be filed rather than left reported.** A boundary is usually *"this instrument answers less than its name suggests."* This one is *"this gesture cannot be executed here at all"*, and it is invisible from every direction: there is no red, no skip, and no gap in a coverage report — the tests that would cover it were never written, because writing one kills the runner. **An untestable gesture reads exactly like a well-tested one from the outside.** `QRubberBand.show()` on an offscreen viewport aborts the process; a ctrl-click on empty canvas reproduces it on `main` today. D53 works around it by creating the band on the first *move* rather than on the press — which made the ctrl-click half testable and is a better gesture anyway — but the boundary is the platform's and it stays named.

**AND THE FINDING BESIDE IT, WHICH IS THE SHARPER STATEMENT OF THE SAME HOLE.** The ruling put it as *"in 639 tests nothing had ever clicked — only dragged."* **Measured, that is not quite true, and the true version is worse.** Clicks existed: four same-point press/release pairs in `test_macro.py`, and every bare `CLICK x y` line in the replayed `.fpm` macros, which go through the real view. What did not exist is **any test that asserted what a click SELECTS**. `test_macro.py`'s clicks assert what the RECORDER emits (`"CLICK" in text`, `"DRAG" not in text`) — they are about transcription, and some run against an empty scene. The `.fpm` replays assert wall counts, room areas and binding invariants — never the selection. And `conftest` offered exactly one gesture helper, `drag`, which always moves; a test author reaching for a gesture got a drag.

**So the hole was not "nobody clicked". It was "nobody ever asked what a click selected", plus a fixture set that made the question awkward to pose** — which is a more specific and more actionable statement than any coverage figure, and it is the reason this defect survived 639 tests and six green CI jobs to be found by hand. The `click` fixture exists now so the question is one line to ask.

**The diagnostic, and it is cheap: CUT THE SEAM AND RUN THE SUITE.** Not the function — the *wiring between the layers*. If the suite stays green, nothing crosses it. The same run also showed the counterpart worth knowing: emptying `RoomItem.shape()` outright **did** fail three tests, all label gestures — so the suite pins the hit area that *exists* and is silent about the one that does not. **You cannot write a regression test for a capability that was never there**, so absent capabilities never show up as red; they show up as a user's report, and the only mechanical way to find them first is to sever a connection and see whether anything screams.

Three of the five are recorded where the defect lives (rows 41 and 44) or at
the call site (`split_count`); they are cited here rather than restated,
because five notes saying the same thing is the duplication disease arriving in
the record instead of in the code.

**TWO FAILURE SHAPES, and they are not the same — separate them.** *(a) A
MISSING CHECK*: P4.5(8)'s edit used `if anchor in s:` and skipped silently —
nothing was watching, and the fix is to add an instrument. *(b) A CORRECT CHECK
IGNORED*: P4.5(16)'s edit **raised**, and the red was overridden because an
unrelated green (the gate) was in the same output. **(b) is the more dangerous
shape** — the instrument worked and was disregarded — and it is the same
failure as reading a `pytest | tail` and committing on the summary line while
an error scrolled past above. Adding instruments does nothing for it; only
refusing to let one green stand in for another does.

**VERIFY THAT A RECORD EDIT LANDED, exactly as a code probe must — added
2026-08-04, the hard way.** The fail-first rule already says to confirm a probe
mutated the tree before trusting its result. The same applies to edits to THIS
FILE: two commit messages (P4.5(8), P4.5(16)) claimed record additions that
never landed, because one script skipped silently on a conditional and the
other raised and was committed through anyway. The gate was green both times —
**a green gate says nothing about whether a document edit applied.** Grep for
the added text before writing the commit message that claims it.