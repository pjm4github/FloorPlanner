# v5 migration plan — staged, gated, executable

**Target:** `floorplanner/design/design-schema.v5.json` (vendored at P0.7; pointer at `docs/design-schema.v5.md`) · **Review:** `docs/CODE_REVIEW_v2.md` · **Model rationale:** `docs/DESIGN_MODEL_v5.md`

Seven phases. Every task is small enough to finish and verify in one sitting, and **every task ends on a green gate**: `python -m ruff check .` then `python -m pytest -ra`, both clean, before the next task starts. `main` stays shippable throughout except during Phase 3, which runs on a branch.

---

## Working agreement

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

### The gate is `ruff check .` over the whole tree — settled 2026‑07‑26

P0.1 found the gate red at baseline: 23 findings, all in `tools/` and `docs/_superseded/` scaffolding committed during the design sessions, **0 in `floorplanner/` or `tests/`**. Four responses were on the table; the deciding fact is that **`.github/workflows/ci.yml:26` runs `python -m ruff check .` over the whole tree**. Narrowing the local gate to `floorplanner tests`, or excluding `tools/`, would make the local gate disagree with CI and leave CI red on the next push — a local gate that is greener than CI is worse than no gate.

So: the gate stands as written, and the 23 findings were **fixed at source** (mechanical: `l` → `lv`, unused loop vars prefixed `_`, `zip(..., strict=False)`, semicolons split, the `math` import hoisted). All three tools re-verified afterwards to produce byte-identical output. `docs/_superseded/` was moved to `_to_delete/` — dead drafts kept alive behind a lint exclusion is exactly how scaffolding rots.

**Standing rule for the rest of the migration:** scaffolding in `tools/` is held to the same lint bar as shipped code, because CI does not distinguish them.

**Corollary found at P0.2** — the divergence cuts both ways. `_to_delete/` was untracked, so the *local* gate went red while CI would have been green. Same principle: the two must agree. `_to_delete/` is now gitignored, which (because ruff respects `.gitignore` for discovery) removes it from both. That directory exists only because the Cowork device bridge cannot delete files on your machine; it is a transfer buffer that should always be empty, and Claude Code should empty it when it appears.

### Three more conventions, settled at P0.2

**Commit at every green gate.** One commit per task, message `P0.x — <task title>`. A 40-task migration with no commits has no rollback points; with one per task, every gate is a place to return to. Nothing is pushed unless asked.

**In a multi-part task, run the FULL gate before each commit, not just at the end.** Found at P0.5: fix 4 was committed after running only `test_selection.py` and turned out to break a test in a different file. Five sub-fixes means five full-suite runs. A targeted run tells you the fix works; only the full suite tells you what else it touched.

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

---

## Status

| | Task | Gate |
|---|---|---|
| ☑ | **P0.0** Point `CLAUDE.md` at this plan | ruff |
| ☑ | **P0.1** Record the green baseline | ruff + pytest |
| ☑ | **P0.2** Decouple tests from private names | ruff + pytest |
| ☑ | **P0.3** Scaling harness | + `pytest -m slow` |
| ☑ | **P0.3b** Add selection-building to the harness | + `pytest -m slow` |
| ☑ | **P0.4** Characterization tests (xfail where broken) | ruff + pytest |
| ☑ | **P0.5** Five free bug fixes | ruff + pytest |
| ☑ | **P0.6** Cheap render wins | + P0.3 ratios |
| ☑ | **P0.7** Vendor schema + validator; CI validates `examples/` | ruff + pytest |
| ☑ | **P1.1** `design/model.py` — dataclasses | ruff + pytest |
| ☑ | **P1.2** `design/validate.py` — I1–I14 | ruff + pytest |
| ☑ | **P1.3** `design/topology.py` — weld/planarize/trace | ruff + pytest |
| ☑ | **P1.3b** Fix defect 18 (`_inner_faces` winding) + corpus diff | ruff + pytest |
| ☑ | **P1.4** `design_from_scene()` | ruff + pytest |
| ☑ | **P1.5** `apply_design_to_scene()` | ruff + pytest |
| ☑ | **P1.6** `--verify-design` shadow mode; suite runs with it on | ruff + pytest ×2 |
| ☑ | **P2.1** Load path: v1–v4 migrate + dirty + report; v5 direct | ruff + pytest |
| ☑ | **P2.2** Save writes v5; legacy export | ruff + pytest |
| ☑ | **P2.3** Undo snapshots the v5 dict | ruff + pytest |
| ☑ | **P2.4** Convert the corpus and the tooling | ruff + pytest |
| ☑ | **P2.5** Split `MainWindow` IO/CSV/image/floors out | ruff + pytest |
| ☑ | **P3.1** Vertex table live; `WallItem` holds `v1`/`v2` | branch, ruff + pytest |
| ☑ | **P3.2** `RoomItem.outline`; drop `perimeter_corners` | ruff + pytest |
| ☑ | **P3.3** Wall move = move vertices + split rule | ruff + pytest |
| ☑ | **P3.4** Topology ops replace coalesce/weld/fracture | ruff + pytest |
| ☑ | **P3.5** Delete the detection engine | ruff + pytest |
| ☑ | **P3.6** Opening anchors — *ticked 2026-07-30 on the re-certification: **10/10 GREEN** under full-mode `tools/gate.py` trailers (ruff + OFF + ON + DEEP, every sum reconciling). Defects 26, 28 and 29 all closed.* | ruff + pytest |
| ☑ | **P3.7** Delete `OpenWall` — *ticked 2026-07-30 against the amended acceptance: the cue is drawn from the outline and pinned by a pixel test with measured polarity, the class and its `is_open` flag are gone (zero `git grep` hits in `*.py`), and the P3.5 Known-regression row closes on that test.* | ruff + pytest |
| ☑ | **P3.8** Perf verification vs P0.3 · **+ split-on-write exit survey** — *ticked 2026-07-30; **Phase 3 merged to `main` at `03f3868` on 2026‑07‑31**, all eight P3 rows complete.*  *(P3.8 detail: `bake` 10.6× faster (279.0 → 26.4 ms at 64 rooms); all four survey rows answered or dispositioned; the flap class retired class-wide; defect 27's DEEP CI job green. Merge checklist items 1–4 done at the tick; Gate 3 passed 2026‑07‑31 and the merge followed.)* | ratios recorded |
| ☑ | **P4.1** Delete-wall keeps the room — *ticked 2026‑07‑31, accepted at **PR #2** (merge commit; sub-commits `0df3aa5` census + rulings, `a0e1b95` delete_wall + 2b flip, `cce2eb6` corpse + tests). Acceptance met: P0.4 test 2b flipped xfail→pass on exactly the call-site switch (513/6 → 514/5); census 526 unchanged; defect 17 closed with the visible-lie coda.* | ruff + pytest |
| ☑ | **P4.1b** Defect 25's gesture-time message — *ticked 2026‑08‑01, accepted at **PR #3** (merge commit `ec5f207`; sub-commits `1d3eaa6` mechanism + tests, `e0519ae` record). Acceptance met: both gestures produce the specific message naming the doorway at release, pinned by two gui tests with a fail-first receipt against `main@708dc2e`; defect 25 closed; census 526 → 528.* | ruff + pytest |
| ☑ | **P4.2** Extract / join — *ticked 2026‑08‑02, accepted at **PR #4** (merge commit; 26 sub-commits, `dfd30af` … `ed9286c` + the record commit: core 1–7, mini-gate findings 8–15, tooling & floors 16–23, hand-off 24, census hygiene 25, record 26) — the first task under the Phase‑4 ruling's **Patrick mini-gate: PASSED, all 8 items**, on a fresh launch with the version label verified. Acceptance met: extract → move 500″ → join with `check()` clean at every step, I12 while floating, furnishings and openings intact; the party-wall regression flipped xfail → hard pass via the real `extract` (the P0.5 Known-regressions row closes). Defects 30, 34 and 13 (drag half) closed; defect 35 closed on the reporter's confirmation; six mini-gate findings fixed against measured reproductions, pinned by his macros verbatim. Census 528 → 552, local == CI.* | ruff + pytest |
| ☑ | **P4.3** Shuffle mode — *ticked 2026‑08‑03 on Patrick's acceptance, merged at **PR #5** (merge commit `4050e44`; 6 sub-commits `a6ded30` … `545b79a`: census + rulings, plumbing, gesture gating + the tiered doorway weld, acceptance, ruling 1's execution, the fuse-straggler finding). Acceptance met: shuffle on, a floating room dragged across the plan through the real handlers leaves both unchanged, `check()` deep-clean at every step. The P2.3 Known-regressions row closed as superseded-by-ruling (STAY, two replacement hard passes); defect row 36 fixed with the macro pinned verbatim; census 552 → 569, local == CI, xfails 4 → 3.* | ruff + pytest |
| ☑ | **P4.4** Concept rooms, `nominal_size`, duplicate-as-template — *ticked 2026‑08‑04 on Patrick's acceptance ("it works perfectly"), merged at **PR #6** (merge commit `ae9f0ad`; 5 sub-commits `868e315` … `da38c46`: census + the four rulings, the `^H` chord + token, duplicate-as-template, concept rooms, the record). Acceptance met: a one-room file validates against the schema and all fifteen invariants and loads into an existing design as a floating room (pinned against a **second** `MainWindow`, so "an existing design" is genuinely another document). The **carried census note resolves** — `_copy_spec` + `_perimeter_span` deleted, so P4.5 inherits the binding/outline duality with its clipboard consumer resolved; register row 37 closed with `^H`. Census 576 → 598.* | ruff + pytest |
| ☐ | **P4.5** Group semantics + z-order collapse | ruff + pytest |
| ☐ | **P5.1** Site levels, categories, area accounting | ruff + pytest |
| ☐ | **P5.2** Landscape wall types + gates | ruff + pytest |
| ☐ | **P5.3** Site schedule fields + reports | ruff + pytest |
| ☐ | **P6.1** `QUndoStack` + commands | ruff + pytest |
| ☐ | **P6.2** Retire snapshot undo | ruff + pytest |
| ☐ | **P6.3** Scene index + viewport update final pass | ratios recorded |

---

# Phase 0 — Baseline, safety net, free wins

*No file-format change. No user-visible behaviour change except the bug fixes.*

### P0.0 — Point `CLAUDE.md` at this plan
**Do.** Add to `CLAUDE.md` after the Architecture section:

```markdown
## v5 migration (in progress)
The file format and domain model are moving to `floorplanner/design/design-schema.v5.json` (vendored at P0.7; pointer at `docs/design-schema.v5.md`).
Read `docs/V5_MIGRATION_PLAN.md` before changing walls/rooms/items/mainwindow —
it says which code is being deleted and in which phase. Do not add new callers of
`detect_room`, `refresh_rooms`, `bind_room_walls`, `coalesce_*`, `weld_all` or
`OpenWall`; they are all scheduled for removal in Phase 3.
```
**Acceptance.** `CLAUDE.md` mentions the plan; no code change.

### P0.1 — Record the green baseline
**Do.** Run `python -m ruff check .`, then `python -m pytest -ra --durations=15`, then `python -m pytest --quick`. Record in the Progress log: pass/fail/xfail/skip counts, wall-clock for the full run and the quick run, and the 15 slowest tests.
**Why.** Every later "still green" claim is meaningless without this number. The slowest-15 list also tells us which tests Phase 3 will speed up.
**Acceptance.** Numbers in the log. If anything is already failing, **stop and report** — do not fix it as part of this task.

### P0.2 — Decouple tests from private names
**Touches.** `FloorPlanner.py:155‑160`, `tests/test_coalesce.py`, `tests/test_view.py`, `tests/test_groups.py`, `tests/test_rooms.py`, `tests/test_io.py`, `tests/test_selection.py`.
**Do.** Remove the four private re-exports (`_money`, `_WallBBoxIndex`, `_coalesce_all_impl`, `_coalesce_wall_impl`) from the shim. Tests that need them import from the submodule directly (`from floorplanner.walls import _coalesce_all_impl`). Where a test asserts on a private attribute that Phase 3 deletes (`view._zoom_accum`, `g._angle`, `room._detect_sig`, `dup._path`, `win._sel_order`), add a comment naming the phase that will retire it — do **not** rewrite the assertion yet.
**Acceptance.** Suite green; `grep -n "^from floorplanner" FloorPlanner.py` shows no underscore names.
**Why now.** Phase 3 deletes `_coalesce_*` and `_WallBBoxIndex` outright. If the shim still advertises them, the deletion breaks the public API instead of an internal one.

### P0.3 — Scaling harness
**Touches.** `tests/test_scaling.py` (new).
**Do.** Build an *n*×*n* grid of walled, named rooms with a door and a window per room and two furnishings, at *n* and 2*n* (start n=4 → 8, i.e. 16 → 64 rooms). Time four operations: `group_selected`, group drag + `bake`, `ungroup_selected`, `rebuild_all_walls`. Mark `@pytest.mark.slow`. Assert each ratio `t(2n)/t(n) < 8` (sub-quadratic in room count; quadratic would be ~16). Print the raw milliseconds so the numbers are visible in `-ra` output.
**Acceptance.** Test runs and prints. **Record the current ratios in the log even if they fail the assertion** — if grouping is already quadratic, mark that test `xfail(strict=False)` with a comment pointing at P3.8 rather than weakening the threshold.
**Why.** This is the only number that will prove Phase 3 worked.

> **How to read the ratios.** The grid is *n*×*n*, so `n → 2n` multiplies the **room count by 4**, not 2. Therefore: **4 ≈ linear in rooms, 16 ≈ quadratic, and the threshold of 8 sits at rooms^1.5.** Anything under 4 is sub-linear.

**Result (2026‑07‑26, n=4 → n=8, i.e. 16 → 64 rooms):**

| op | n=4 | n=8 | ratio | reading |
|---|---|---|---|---|
| `rebuild_all_walls` | 1.2 ms | 3.2 ms | **2.7** | **sub-linear** — the memoized `refresh_rooms` genuinely works |
| `group_selected` | 22.5 ms | 262.6 ms | **11.7–13.7** | near-quadratic → xfail, P3.8 |
| `bake` | 29.8 ms | 143.0 ms | 4.4–4.8 | ~linear, passes |
| `ungroup_selected` | 53.1 ms | 436.2 ms | **8.2–8.5** | rooms^1.5 → xfail, P3.8 |

**`rebuild` at 2.7 is the surprise, and it is a constraint on Phase 3, not just good news.** The `_RoomGrid`/`_WallGraph`/`room_signature` machinery that P3.5 deletes is currently performing *better than linear*. Stored outlines should beat it outright — there is no detection left to do — but P3.8 must confirm that rather than assume it. If P3.8 shows `rebuild` regressing, that is a real finding, not noise.

### P0.3b — Add selection-building to the harness
**Why.** P0.3 measures `group_selected` *after* the selection exists. It does not measure **building** the selection, which is where the user's reported stall most likely lives: `scene.selectionChanged` → `_update_edit_actions` (`mainwindow.py:323`) → `_selected_room_shapes()` (`:598‑629`) calls `bounding_walls()` **per already-selected room**, so ctrl-clicking room *k* re-runs O(k·W) `QPainterPath` booleans. Selecting R rooms is therefore O(R²·W) path booleans *before Ctrl+G is ever pressed*. Nothing measures this.
**Touches.** `tests/test_scaling.py`.
**Do.** Add a fifth timed operation: select the rooms **one at a time** (`setSelected(True)` per room, which is what a ctrl-click does), measuring cumulative wall-clock. Same `n` / `2n` grid, same ratio assertion, same `xfail(strict=False)` → P3.8 if it fails.
**Acceptance.** Ratio recorded. Also record the **absolute** time to select all 64 rooms — that number is the one to compare against the felt symptom.
**Note.** The harness runs headless offscreen, so it measures none of the repaint cost (`FullViewportUpdate`, no `setCacheMode`). Real-world stalls will be worse than these numbers, not better.

**Amendment (P0.6) — split `select` into two ops.** The debounce landed in P0.6 item 1 makes the single `select` op measure the wrong thing, and the fix is not simply to pump events: **the two user paths have genuinely different costs and should be measured separately.**

- **`select_burst`** — no event pumping. Models Ctrl+A, rubber-band, and the macro runner, where selections arrive faster than the debounce interval. Here the **debounce** does the work.
- **`select_interactive`** — `processEvents()` after *each* `setSelected`. Models a human ctrl-clicking, whose clicks are far slower than the timer, so `_apply_edit_actions` fires **once per click** and the debounce buys nothing. Here the **cheap-count fix** does the work.

Both get ratio assertions. Measure `select_interactive` first, then promote to a hard pass if it clears the threshold; if it doesn't, keep it `xfail` naming the specific task that will.

**This is not a goalpost move, and the tell is the direction the number moves.** Pumping makes the measurement *worse* (1.0 ms → 1.7 ms for the coalesced case, and higher again once it fires per click) because it models the user more faithfully. A goalpost move makes the number look better; this one makes it look honest.

**Step 3 — give the timing tests their own marker, before the first push.**
Register a `perf` marker in `pytest.ini` and tag every test in `tests/test_scaling.py` with it (keep `slow` too, so `--quick` behaviour is unchanged). Then change the CI test step to `python -m pytest -ra -m "not perf"`.

Deliberately `perf` and **not** `slow`: excluding `slow` from CI would also drop `test_fp_extract_cli_end_to_end` and the macro CLI subprocess test, which are slow but *deterministic* and worth running there. Only the timing-ratio assertions are unsafe on shared runners.

The harness stays a **local gate**, invoked explicitly at P0.6 and P3.8 — the two moments its numbers decide something. A timing gate that flaps in CI gets muted within a week and then protects nothing.

### P0.4 — Characterization tests
**Touches.** `tests/test_characterization.py` (new).
**Do.** Write these against *current* behaviour, marking `xfail` the ones that fail today:
1. Group a named room with a door, a window and two furnishings; move it; assert every opening's `s` relative to its wall is unchanged. Repeat for a 90° group rotation.
2. Delete one wall of a 4-wall named room. **Split into two tests — the single test cannot distinguish today's behaviour from P4.1's.**
   - **2a `test_delete_wall_keeps_room`** — the room still exists with its name, area and furnishings. **Passes today** (verified at P0.4), and must never regress. Assert hard.
   - **2b `test_delete_wall_actually_removes_the_wall`** — after the delete, the room has **3 built walls and 1 open edge**, not 4 built walls. *(xfail — P4.1)*
   
   Why the split: the room survives today **because the wall is not actually deleted**. `fracture_delete_wall` (`walls.py:300‑354`) keeps every stretch that runs along a room perimeter and rebinds it, so deleting a room's own perimeter wall is silently a **no-op** — 4 walls in, 4 walls out, 0 open edges (measured at P0.4). Under P4.1 the wall genuinely goes and the edge becomes `wall: null`. A test that only asserts "the room survived" passes in both worlds and therefore proves nothing about the change. 2b is the assertion that actually holds P4.1 to its promise.
3. Group two rooms, `serialize()`, `load_data()`, assert the group survives. *(expected xfail — P4.5)*
4. Group, move, `undo()`; assert the plan returns to its pre-group state. *(expected xfail — P4.5)*
5. Assert grouped walls are exempt from `coalesce_all` (guards the `group() is None` gate that nothing currently covers).
6. Group a room, ungroup, repeat 4×; assert wall and opening counts reach a fixed point. *(This is the deleted `test_zzleak.py`, promoted.)*
**Acceptance.** Each test either passes or is `xfail` with a comment naming the phase that flips it. **No existing test modified.**

> **An xfail prediction that turns out wrong is a finding, not an error.** Record what actually happens and *why*, then decide whether the test needs splitting (as test 2 did) — an unexpected pass usually means the test is measuring something coarser than the behaviour under change.

### P0.5 — Five free bug fixes
**Do.** One commit each, each with a regression test.

> **Expected test breakage — authorised in advance.** Fix 4 (making `select_in_rect` read-only) removes the wall synthesis that `tests/test_selection.py:53, 83, 106` currently assert.
>
> **Blast radius was wider than that — resolved at P0.5.** It also breaks `test_groups.py::test_extracted_room_region_follows_move`, which is not a defect-asserting test. Root cause: the old `select_in_rect` synthesised a *private copy* of a longer party-wall edge, and the following `rebuild_all_walls` rebound the room to that copy — so the room **owned** the edge and `bake()`'s strict `room_owns_walls` check would carry the region. Read-only selection removes that accidental privatisation, the room stays bound to the shared wall, and `bake()` correctly declines to move it.
>
> **Decision: mark it `xfail` → P4.2**, and record it in Known regressions below. Rationale: selection silently mutating the document is the worse defect, the workflow it protected is exactly what P4.2 rebuilds as a real `extract` operation, and dragging a room by its label still works today (`_privatize_shared_walls`, `rooms.py:838‑865`), so no workflow is lost outright — only the rubber-band-then-group route to it. Those three tests assert the *defect*: that a rubber-band selection duplicates a party-wall edge. Rewrite them to assert the corrected behaviour — selection creates nothing — and say so explicitly in the log. This and P3.4 / P4.5 are the only places in Phase 0–4 where changing an existing assertion is expected rather than suspicious.
1. `RoomItem.itemChange` on `ItemSceneChange` unbinds its walls, mirroring `walls.py:496‑504` including the `sip.isdeleted` guard. *(defect 5)*
2. `mainwindow.py:1074` → `properties=dict(it.properties)`. *(defect 4)*
3. `refresh_rooms_cmd` (`mainwindow.py:589‑593`) iterates only active-floor rooms. *(defect 2)*
4. `view.py:445` — `select_in_rect` must not call `synthesize_room_edge`; selection is read-only. *(defect 10)*
5. `catalog.apply_furnishing_prices` writes to the user config dir, not `assets/furnishings/manifest.json`. *(review §1)*
**Acceptance.** Five tests added; suite green; #3's test creates two floors and asserts the inactive floor's rooms survive.

### Known regressions carried during the migration

Behaviour that is deliberately worse between the task that broke it and the task that restores it. Kept visible rather than buried in a log, because "main stays shippable" has to mean something.

| Broken at | Behaviour | Workaround today | Restored at |
|---|---|---|---|
| **P0.5** (fix 4) | Rubber-band-select a room whose edge is a longer party wall, then group + move it — the region no longer follows. The walls captured by the band move; the room does not. | Drag the room by its **label** instead: `_privatize_shared_walls` handles the party wall correctly on that path. | **P4.2** (`extract` replaces the accidental privatisation with a real operation) |
| **pre-dates the branch** (surfaced at P3.5, defect 23) | **A rubber band that clips a room's wall set strands that room.** The band takes only items fully inside it, so a wall poking out is left behind, that room's remaining walls are duplicated into the group, and the group moves those while the room's region stays where it was — it reads as a detached dashed outline at the original position. 3 of 20 rooms on a band covering 92% of `symmetricP1`. | **Band whole rooms** — include every wall of any room you mean to take — **or move the room individually** by dragging its label, which carries its walls and openings correctly. | **P4.5**, where "what a group is" is decided. Listed here rather than as a Phase-3 regression because the branch measurably IMPROVES it (148.3" of drift before P3.5, 46.65" now) — the Phase-3 gate is no-worse, not all-better. |
| ~~**P3.5**~~ **CLOSED at P3.7 (2)** | ~~**An open side of a room is not drawn.**~~ **The cue is back, drawn from the outline: `RoomItem._paint_open_edges` strokes every `open_edge_segments()` with the same colour, dash and lod-scaled width the `OpenWall` item used — so this closes as *the same cue from one representation*, which is what the "Restored at" column asked for, and not as a different cue. RECEIPT, and it is a pixel test rather than a structural one because every structural assertion in `test_open_walls.py` stayed green throughout the regression: `test_an_open_side_is_drawn_dashed`. Polarity measured first (wall body 150, dash ~124, gaps and bare background 255), and it FAILS against a tree without the paint addition with the row's own words — `[255, 255, … 255]`, the open side rendering as nothing.** Original text: **An open side of a room is not drawn.** Detach a wall from its room and pull a corner away and the side opens — the room keeps its shape and area, and the document says `wall: null` exactly as before — but the vacated stretch renders as nothing rather than as a dashed line. The producer of the dashed `OpenWall` placeholder was `refresh_rooms` → `reloop_open_room` → `bind_room_walls`, all deleted here; the fact itself moved onto the outline (`RoomItem.open_edges()`), which is where the document had always kept it. | None needed for correctness — nothing is lost but the on-screen cue. The room's area, outline and saved file are unaffected. | **P3.7** (`OpenWall` is deleted and a `wall: null` edge renders dashed from the outline, which is the same cue drawn from the one representation instead of a second one) |
| **P2.3** | **After the first undo, a wall that crosses a junction comes back split** — and if it borders NO room, body-dragging it moves only that segment. Measured at P3.3: one 480″ wall with a mid-span T returns as two 240″ walls. **Narrower than first recorded**: `_collinear_run()` (`walls.py:888`) gathers the whole room *side*, so for a wall on a room perimeter — the common case, and the one a user would notice — both halves still move as one. Verified with a room: `_collinear_run()` gathers 2 of 2. The row applies only to room-less walls, where `self.rooms` is empty and the run short-circuits to `[self]`. | Bind the wall to a room, or drag the halves together. Nothing is lost either way: the **document is unchanged**, since `design_from_scene` planarises to the same canonical form. | ~~P3.4~~ → **retargeted at P3.4 (iv), and the predicted fix was wrong on its own terms.** Re-checked by hand: the 480″ wall still returns as two 240″ segments, `merge_all` does **not** re-merge them, and the body-drag still moves one segment. It must not — the mid-span T is a **degree-3 vertex**, load-bearing for the planar subdivision, and merging through it would destroy planarity. `merge_collinear` refuses for exactly the right reason, so this row was never merge's to close. The fix belongs in the **drag's run-gathering**: `_collinear_run()` (`walls.py`) short-circuits to `[self]` when the wall borders no room, which is precisely the case the row describes. Gathering the run over **vertex adjacency** instead would carry both segments. Unassigned rather than invented — it is one small change, and the honest place is whichever task next touches the drag (**P4.2** extract/join is the nearest). **SECOND PREDICTED FIX REFUTED AT P4.2** — the vertex-adjacency gather was implemented (per ruling e) and turned P3.3's anti-shear pins red: `_tee_scene` (a wall, its collinear continuation, a stem at the shared corner) is topologically **identical** to the undo-split segments, and P3.3's settled "split first, shear never" rule — the continuation keeps its vertex and stays exactly where it is — occupies that topology with three pinned tests. The representation cannot distinguish "one wall stored as two segments" from "two walls drawn end-to-end", so one rule must own the topology, and the settled one does. Reverted; the row's wanted behaviour is pinned by the xfail `test_wall_move.py::test_a_roomless_split_wall_body_drags_as_one_run`. **The row now needs a RULING (carry vs stay), not a third predicted fix** — both of its predictions have now failed on their own terms, each caught by a settled rule doing its job. **RULED at P4.3 (2026‑08‑03): STAY — the row CLOSES as superseded-by-ruling.** The settled rule keeps the topology; the drag moves the grabbed segment only, permanently. The xfail pin is **replaced by two hard passes** per the ruling's amendment: `test_a_roomless_body_drag_moves_the_grabbed_segment_only` (the stay contract, promoted from implied to asserted — the topology's one owner) and `test_the_roomless_seam_heals_and_then_drags_as_one` (with `auto_coalesce` on, the room-less degree-2 collinear seam an undo leaves dissolves at the next merge pass and the merged wall body-drags as one — **the restoration this row actually wanted, arriving through the document instead of the gesture**). The workaround column survives only for the shuffle / `auto_coalesce`-off world, where staying split is honest. |

### P0.6 — Cheap render wins
**Touches.** `items.py`, `rooms.py`, `mainwindow.py`, `view.py`.
**Do.**
1. Cache `GroupItem._oriented_box()` per geometry change instead of recomputing 3× per paint (`items.py:509‑528`).
2. Debounce `_update_totals` behind the existing 180 ms dirty timer instead of firing on every `scene.changed` (`mainwindow.py:98`).
3. Cache the `QFontMetricsF` in `RoomItem._label_rect` (`rooms.py:678`) and the stroker in `_boundary_band` (`rooms.py:514`).
4. `setCacheMode(DeviceCoordinateCache)` on `FurnishingItem`.
5. **Measure** `NoIndex` vs `BspTreeIndex` (`mainwindow.py:78`) with the P0.3 harness. Report both numbers; change the default only if BSP wins.
**Acceptance.** P0.3 ratios and absolute times recorded before and after. No behaviour change.

### P0.7 — Vendor the schema and validator
**Touches.** `floorplanner/design/` (new package), `tools/`, `tests/test_schema.py` (new), `.github/workflows/ci.yml`.
**Do.** Move `docs/design-schema.v5.json` to `floorplanner/design/design-schema.v5.json` (packaged data, with `docs/` keeping a symlink or a pointer). Port `tools/validate_design.py` to `floorplanner/design/validate.py` as an importable `check(doc) -> list[str]`. Add `tests/test_schema.py` validating every `examples/*.json` that declares `floorplanner-design`, plus asserting `planc1.v5.json` still fails I6 (it is the "does not launder its input" fixture). Add `jsonschema` to `requirements-dev.txt`.
**Acceptance.** `pytest -m io` validates the corpus; CI green.

---

# Phase 1 — The v5 document, shadow mode

*Nothing user-visible. The `Design` exists alongside the scene and is continuously checked against it.*

### P1.1 — `design/model.py`
Qt-free dataclasses for `Level`, `Vertex`, `Wall`, `Opening`, `Room`, `OutlineEdge`, `Furnishing`, `Group`, `Provenance`, `Design`, with `to_dict`/`from_dict` and stable emit order. No behaviour, no callers yet.
**Acceptance.** `Design.from_dict(load("symmetricP1.json")).to_dict() == load("symmetricP1.json")` byte-identical. Zero Qt imports (assert it in the test).

### P1.2 — `design/validate.py` (deep flag + negative tests)
**Most of this landed early at P0.7.** `check(doc) -> list[str]` already ports all **15** named checks (I1–I14 plus I5b; pure Python, in `floorplanner/design/validate.py`), and the corpus acceptance below already holds (`test_schema.py`). What actually **remains** of P1.2:
- Split the three O(n²) invariants behind a `deep` flag: **deep-only (3)** `I5b` (outline self-intersection, O(edges²)/room), `I11` (room-vs-room overlap, O(rooms²)), `I14` (weld closure, O(walls²) — ~6,700 pairs on 82 walls); **always-on (12)** I1 I2 I3 I4 I5 I6 I7 I8 I9 I10 I12 I13. The docstring must state the call sites, since they are the reason for the split: the cheap twelve run **per mutation** under P1.6's `--verify-design` (an O(n²) sweep per edit would make the app unusable); the deep three run on **save, load and import** (paid once, stakes highest — I11 and I14 are the two that caught the real corruption in `planc1.json`).
- Two negative unit tests, each of which must **fail the check** (not merely not-crash): nudge a shared vertex 0.3″ → `I14` fires (and does *not* fire under `deep=False`); point a wall's `left` at a room that doesn't name it → `I6` fires.
**Acceptance.** `check(doc, deep=True)` (the default) runs all 15; `deep=False` runs only the 12 always-on and skips I5b/I11/I14; both negative tests pass. **`deep=True` is the default deliberately**: forgetting `deep=False` on the hot path is a loud slowdown, but forgetting `deep=True` on load/import is *silent* corruption — the failure mode should be loud. (The corpus acceptance — `[]` for `symmetricP1.json` and `site_demo.json`, non-empty for `planc1.v5.json` — already holds from P0.7.)

### P1.3 — `design/topology.py`
Port from `tools/migrate_to_design_v5.py`: `weld_endpoints`, `planarize`, `split_edge`, `merge_collinear`, `trace_faces`, `enclosing_face`. Pure functions over the `Design`; no Qt.
**Acceptance.** `trace_faces` on `symmetricP1` recovers every stored room area (**20**, after the P1.3b `_inner_faces` fix; it was 19 while defect 18 dropped the Garage), plus one extra face for a genuinely unclaimed region. `weld_endpoints` on the legacy `planc1.json` geometry welds exactly 31 ends.

### P1.4 — `design_from_scene()`
Walk the live scene into a `Design`. **This is where the ten unfiltered floor queries get fixed** — the walk is level-scoped **by construction** (iterate levels outer, items inner, so cross-level contamination is impossible, not merely filtered out). Build room outlines from the scene's own `RoomItem.corners`, **not** from `trace_faces`: `design_from_scene` must report what the scene *believes*, not what the geometry *should* be. Repairing while reading would make P1.6's shadow comparison diverge from the live scene; repair belongs at P2.1's import, once, and nowhere else. The scene is still `p1`/`p2`-based (pre-P3.1), so the walk uses `legacy.py`'s weld/planarise to reach a vertex table.
**Acceptance.** Corpus is **legacy files only** — `examples/planc1.json`, `examples/sample_plan.json`, and scenes built by the test fixtures — because `symmetricP1.json`/`site_demo.json` are v5 and have no loader until P2.1. For each: load into a scene the old way, `design_from_scene()`, then room areas match `project_from_scene()`'s to 0.1 sf. `check(deep=True)` returns `[]` on the clean scenes (planc1 may carry the same referential faults as its v5 fixture — assert what it actually reports, don't force `[]`).

### P1.5 — `apply_design_to_scene()`
Build the scene from a `Design`.
**Acceptance.** `scene → Design → scene → Design` is identical at the second `Design`. Existing IO and undo tests still green.

### P1.6 — `--verify-design` shadow mode
A debug flag (env var or `--verify-design`) that rebuilds the `Design` and runs the cheap invariants after every mutating operation, raising on failure.
**Acceptance.** **The entire suite passes twice: once normally, once with the flag on.** This is the gate that says the bridge is trustworthy. CI runs both. Any invariant that fires here is a real bug in the current code — log it, don't paper over it.

---

# Phase 2 — IO cutover

*The file format changes. This is the first user-visible phase.*

### P2.1 — Load path
v1–v4 `floorplanner-json`: parse → weld at `join_tol_in` → planarize → trace outlines → convert openings → assign furnishing owners → write `provenance` → **mark dirty** → show the conversion report (§7a of `DESIGN_MODEL_v5.md`). v5 `floorplanner-design`: load, validate, **never dirty**; a file failing I14 is reported as malformed, not silently re-welded.

**Two weld counters, with a 0.6″ noise floor** *(added after P1.4 measured them)*. Track both: `weld_ops`, operations performed (31 on `planc1.json`), and `ends_moved`, operations that displaced a coordinate by **more than `settings.vertex_weld_in` (0.6″)** — **4**. Only `ends_moved` reaches the user or `provenance.endpoints_welded`, whose schema description already says "wall ends *moved*"; `weld_ops` is for cross-checks. Anything at or below 0.6″ is not a geometry change by the document's own definition, so it must not be counted as one. **Regenerate `examples/symmetricP1.json`'s `provenance.endpoints_welded` (31 → the measured `ends_moved`) as part of this task**, once the real importer exists — not before, since P1.1/P1.4/P1.5/P1.6 all pin that fixture and a mid-phase regeneration is churn for a semantics fix this task implements properly anyway.

**Also close defect 19's in-app arm here.** Weld-on-load fixes the PNG extractor's *file* route for free (write a plan, open it, it welds). It does **not** fix `extract_from_reference` (`mainwindow.py:1644`), which injects detected walls straight into the live scene and never passes through a load — that arm needs its own explicit weld pass after the walls are written. Closing only the file arm would tick the defect while leaving the reported reproduction alive.

**Outlines come from the welded FILE geometry, never from the scene's re-detection.** P1.4 measured why: loading `planc1.json` collapses Hall and M Bath into **one identical 21-vertex region** (both 243.5 sf, same vertex set), where the file at least keeps them distinct (Hall 243.5 sf/18 corners, M Bath 591.6 sf/24 corners). The scene's belief about a corrupt file is **strictly worse than the file itself**, so importing through the scene would bake in damage the file does not contain. `tests/test_design_bridge.py::test_planc1_reports_its_real_faults` pins the shared vertex set and is the guard for this.
**Acceptance.** Opening `examples/planc1.json` yields M Bath 182.0 sf, Hall 61.5 sf, **`provenance.endpoints_welded` = 4** (`ends_moved`, the ends displaced by more than 0.6″ — *not* the 31 weld operations attempted; see the two-counter rule above), and a dirty document. Opening `examples/symmetricP1.json` is clean and not dirty. The legacy file on disk is never modified. **Opening a v5 file must not dirty it** — this depends on P1.1 round-trip fidelity (`Design.from_dict(x).to_dict() == x`); if a v5 file opens dirty, suspect a model normalisation that broke byte-identity, not the load path.

### P2.2 — Save writes v5
Plus **File ▸ Export legacy v4…** for one release, so nobody is stranded.
**Acceptance.** Save → reopen → `check()` clean, not dirty. Legacy export round-trips through the old loader.

### P2.3 — Undo snapshots the v5 dict
Still whole-document; only the payload changes.

> **Correction (2026‑07‑27): groups do NOT close here.** This task originally read "Groups now serialize, so defect 3 partially closes here", with an acceptance test "group, undo, redo — the group survives". That was written before P1.4 decided — correctly — that the bridge emits `groups: []` until **P4.5**: mapping a grouped wall onto its split segments is undefined while grouping still *copies* walls. So group survival stays at P4.5, held by characterization test 3 exactly as it is now, and **the group-survives test must not be written here** — it would pass for the wrong reason or fail for a reason P2.3 cannot fix. The behaviour P2.3 *must* preserve is narrower and already works: **undo after grouping restores the plan correctly** (via the P0.5 aliasing fix) even though the group itself dissolves.
**Compare canonical form, not raw bytes.** The dirty check and the undo comparison must both run `design.canonical.canonicalize` over each side before comparing. With the importer canonicalized (P2.2) this is belt-and-braces — but defining equality on canonical form is what survives any future producer that forgets to canonicalize, **including whichever way P3.1's uid decision goes**. Two documents describing the same plan must compare equal even when they were built by different code paths.
**Also here: backdrop / reference-image retention.** `apply_project_to_scene`'s `keep_backdrop` flag exists because undo must not delete the tracing image; `apply_design_to_scene` (P1.5) deliberately does **not** implement it, since it belongs with the undo-restore path rather than the bridge. Wire it here, or undo silently drops the backdrop.
**Acceptance.** `test_undo.py` green. Undo after grouping restores the plan (the group dissolving is expected until P4.5). Undo with a reference image loaded keeps the image. **Record undo latency on the P0.3 64-room grid** — the canonical walk now runs per settled edit, so P6.1's "undo cost is independent of plan size" needs a baseline to be measured against.

### P2.4 — Convert the corpus and the tooling
`examples/*.json`, `docs/make_gallery.py`, `examples/make_examples.py`, `tests/bench_rooms.py`, `fp_extract.py`'s writer, and the macro `open`/`save` tokens.
**Includes flipping `fp_extract.py` from `export_legacy_v4_path` back to `save_path` (v5)** — deferred here from P2.2, where `save_path` going v5 would have converted that one writer early and out of step with the rest of the tooling.
**Acceptance.** `python docs/make_gallery.py` and `python examples/make_examples.py` both run; gallery images regenerate.

### P2.5 — Split `MainWindow`
Extract `io.py` (open/save/export), `csvio.py` (`_import_rooms`/`_export_rooms`, 137 lines), `imageio.py` (PNG import/calibration), `levels.py` (floor roster). `MainWindow` keeps UI wiring.
**Acceptance.** `MainWindow` under ~55 methods. Suite green with no test changes.
**Why here.** After the IO seam is clean and before Phase 3 churns the same files.

---

# Phase 3 — Vertices own the geometry

> **Branch.** `git switch -c v5-topology`. This is the only phase where `main` should not track HEAD.
>
> ## ✅ **MERGED — `03f3868`, 2026‑07‑31.** PR #1, as a **merge commit, not a squash**, so the sub-commit history keeps this phase's rollback points and the receipts in its commit messages. CI green on `main` at the merge commit: ruff, py3.10, py3.13, and the deep-invariant job. All six merge conditions met; the checklist below is closed. **`main` tracks HEAD again — Phase 4 opens against `main`.**

### What Phase 3 carries into Phase 4 — the open list, in one place

Written at the merge so Phase 4 starts from a list rather than a search. Each is registered in `docs/CODE_REVIEW_v2.md`; nothing here blocked the merge.

| | open item | argued phase |
|---|---|---|
| **23** | A group move strands a room it does not fully own. Confirmed by a real user at Gate 3 and reproduced exactly: a rubber band takes only items **wholly inside**, so a band that clips a room's wall set strands it — **100% coverage strands zero; every band short of it strands what it clipped**. The decision is semantic (deform-to-follow, or stay put?), which is what "what a group IS" means. | **P4.5** |
| **25** | A gesture can create a door-straddles-junction state the document can only report. **First real-user confirmation at Gate 3** (a wall drawn onto a doorway; the join correctly declines and the user gets the generic torn-network message). The mechanism works; the gesture-time message is missing. | **P4.1** *(my P4.3 dissent is on the record and Gate 3 weakened it)* |
| **30** | A body drag strands every room that holds the moved corner but owns no wall in the dragged run — its walls partly follow, its region does not. Measured with a real drag at a 4-way corner. | **P4.2** |
| **34** | A document gap in the (0.6″, 9.0″) band is reported by nothing and closed by nothing, and the command that looks like a repair only silences the report. **Must be a review, not an auto-repair** — a deliberate 6″ reveal is legitimate and nothing may silently close it. | **P4.2** *(alt P4.3)* |
| **13** (drag half) | Whether a gesture tolerance may set a geometric **result** — the endpoint catch radius and orthogonal stick are zoom-relative. Measured at P3.5; needs a ruling, not another number. | **P4.2** |
| — | **The P3.1 split-on-write shim**: `GroupItem.bake`'s residue is P4.5's by ruling, and the shim stays until that counter is owned entirely by P4.5's rebuild. | **P4.5** |
| — | **Two identity-churn assignment sites** (`_translate_shape`'s pair): they translate a whole selection by one delta, so the geometry stays self-consistent while identity is minted fresh. Lower stakes than the four defect-30 faces. | **P4.5** |

**They share one thesis, and P4.2 inherits it: every one is an operation that knows about ROOMS where it should know about CORNERS.** Phase 3 moved the geometry onto vertices; these are the call sites that still ask a room what they should be asking a corner.

### The Phase-3 merge checklist — ruled 2026‑07‑30

~~*Merge when P3.8 records its numbers.*~~ That one line was the whole condition, and it is not enough: it would have merged a branch whose gate can go red for reasons unrelated to the code, onto a `main` whose CI runs neither of the invariants that caught the only real corruption this project has seen. **PR #1 merges when ALL of the following hold.**

1. **P3.8's numbers are recorded** — a full P0.3 re-run against **both** the P0.3 baseline and the P3.5-exit numbers, ratios in the Progress log; and **grouping 20 rooms creates 0 new walls, asserted** (not observed).
2. **All four exit-survey rows are answered** — by measurement, or explicitly dispositioned to a named task. **No blank rows**, the corpse-table standard applied to the survey: the split-on-write assignment-site census, the stranding question, defect 13's drag half, and the P2.3 collinear-run row.
3. **The flap-class decision is made and applied to the CLASS** (all four members). **Constraint from member four, not negotiable: no wall-clock ratio may remain a gate-reddening hard pass on a shared machine.** Wider thresholds, best-of-N, or a non-gating recorded-benchmark lane with one very loose catastrophic guard — P3.8 decides from its own fresh numbers, but it decides for the class. *Why this is a merge condition and not housekeeping: as of today a red gate has two indistinguishable causes — a regression, or machine load — separable only by reading which test failed, which is the manual step the gate exists to replace.*
4. **Defect 27, first half: a DEEP CI job** (`FP_VERIFY_DESIGN=deep`, ubuntu) **is added and green before merge.** Defect 26's fix removed the crash that made this impossible. I11 and I14 caught `planc1`'s real corruption, and they do not land on `main` guarded by nothing but a human running a local gate. **The windows-latest half stays filed in defect 27 as its own task — desirable, not merge-blocking.**
5. ~~**Gate 3 passed by Patrick, findings dispositioned**~~ — **DONE, 2026‑07‑31.** Sections A and B re-run clean against the branch head. **Five findings, all dispositioned:** **31** the group-box stretch (fixed pre-merge, two mechanisms at defect 14's site) · **32** the warning's false advice (fixed pre-merge; a v5 plan is now silent on open) · **33** rooms left behind by a clipped band (**closed as a duplicate of 23** — measured: 100% band coverage strands zero, every band short of it strands what it clipped) · **34** a document gap in the (0.6″, 9.0″) band that nothing reports and nothing closes (**registered, carried to P4.2**; it wants a review, not an auto-repair) · and a **first real-user confirmation of defect 25's gesture arm** — a wall drawn onto a doorway leaves the end unwelded and the user sees only the generic torn-network message. Record in `docs/SANITY_CHECK.md`.
6. **CI green on the branch head**, and **merge commit, not squash.** The sub-commit history carries the rollback points and the receipts live in the commit messages; flattening it would delete the audit trail this phase spent so much effort making true.

### P3.1 — Vertex table live
`Design.vertices` becomes the live store. `WallItem` gains `v1`/`v2` ids; `p1`/`p2` become read-through properties resolving against the table, so **every existing caller keeps working**. Assignment to `p1`/`p2` moves the vertex and is logged under `--verify-design`.
**Assignment is SPLIT-ON-WRITE, not shared-move** *(ruled 2026‑07‑27)*. Assigning a new position to `p1`/`p2` **mints a fresh vertex for that wall's end** and leaves any sharer on the old one — today's independent-ends semantics, preserved exactly. That is what makes "suite green with no test changes" achievable at all: a shared move would drag a neighbour's end and break tests that have nothing to do with this task. Sharing is created **explicitly** (weld/join making two ends reference one vertex) and broken **explicitly** (split-on-write); shared movement arrives at **P3.3** as the wall-move *operation*, never as a side effect of assignment. Representation changes first, behaviour second, each observable separately. **Log every split-on-write under `--verify-design`** — the count of implicit splits per operation is exactly the data P3.3 needs to decide which call sites should become real vertex moves.

**Gate additions** *(the Gate 2 lesson, applied verbatim)*: the task's gate includes a round-trip through **both** apply paths — `load_data` (faithful) and `open_document` (converting) — plus the `--verify-design` run. Compositions, not just paths.

**Decide id policy here.** **Live items carry persistent uids, minted once; FILES stay canonical.** Persistence is an **in-memory** property; canonical form is the **interchange** property; P2.3's canonical comparison is the bridge that makes a persistent-uid document compare equal to its canonical form. Save canonicalizes at serialization exactly as P2.2 already built it, so **nothing on disk changes because of this decision** — fixtures, diffs and the equality definition are all untouched. Items should carry **persistent uids, minted once** — stable across edits, and therefore macro-addressable — with `canonicalize` (`design/canonical.py`) applied only at **snapshot/serialization time**, for equality. Content-derived ids recomputed per walk are almost certainly the wrong thing to *persist*: P1.5's canonical ids sort by geometry, so moving one wall renumbers its neighbours. That is harmless for round-trip and undo comparison, which is all it was built for, but P3.1 makes scene items id-carrying and **P4.5 serializes groups by member id** — a group whose members are renumbered by an unrelated wall move is a live bug. Settle it at this task rather than discovering it at P4.5.
**Acceptance.** Suite green with no test changes. The `--verify-design` run stays green.

### P3.2 — `RoomItem.outline`
`RoomItem` gains `outline: list[OutlineEdge]`. `corners` becomes a derived property. `properties["perimeter_corners"]` is dropped on save and ignored on load (the schema already forbids it).
**Acceptance.** Room areas unchanged across the corpus. `_sync_corner_props` and its six call sites deleted.

### P3.3 — Wall move = move vertices, plus the split rule
Dragging a wall moves its two vertices. Implement the split rule: a collinear continuation past an endpoint splits first; a vertex landing on another wall's body splits that wall.
**Acceptance.** Port `tools/demo_move_wall.py` to `tests/test_wall_move.py`: moving `w24` by +12 y changes exactly Lounge and Front Porch by ±17.5 sf, total unchanged, `check()` clean. Add a split-rule test with a T-junction continuation.

### P3.4 — Topology ops replace coalesce/weld/fracture
`coalesce_wall`, `coalesce_all`, `_coalesce_*_impl`, `weld_all`, `join_endpoints`, `fracture_delete_wall`, `_WallIndex`, `_WallBBoxIndex`, `_compute_wall_junctions` → `merge_collinear`, `split_edge`, vertex adjacency. **Defect 9 closes here** (merge dedups openings).
**Inherits the split rule's second half from P3.3: a vertex landing on another wall's body splits that wall.** P3.3 built only the first half (a collinear continuation past an endpoint splits first, so it can never be sheared); the body-landing half is `split_edge` applied scene-side, which is exactly this task, and building it twice would have meant building it wrong once. Until it lands, a body-landing has no vertex to be: P3.3 leaves those attachments on the old coordinate path (`kind == "tee"` in `WallItem.mousePressEvent`) with a comment naming this task. **Also remove `split_edge`'s `NotImplementedError` guard on walls carrying openings** (`design/topology.py`, added at P1.3-followup and pinned by `pytest.raises(match="P3.3")`) as the redistribution it names is built — the guard's message points at P3.3, so retarget or retire it rather than leaving it lying about which task owns the work.
**Settled before implementation** *(2026‑07‑27 — seven points; committed to this file first, per the handoff-spec rule above, so the implementing session reads them from disk rather than from a summary).*

**1. The crux — one pure planner, two thin appliers.** The ops in `design/topology.py` are pure `Design → Design`; this task needs them acting on a live scene of `WallItem`s carrying `OpeningItem` children, room bindings, groups, z-order and floors. Two obvious routes were considered and **both are rejected**:

- **(a) Lift the scene to a `Design`, run the pure op, apply back.** Disqualified *on measurement*, not on taste: it makes every wall edit a **full-plan rebuild**, which destroys item identity — selection, in-flight drag state, group membership, and the whole point of P3.1's persistent uids — and would regress precisely the numbers **P3.8** exists to improve.
- **(b) Scene-side siblings that share only the algorithm.** This is **F2's disease**: one concept, two implementations, drifting apart from the day they are written.

**The third way: the decision logic runs ONCE, pure; only the mutation is dual.** `plan_merge_collinear(...)` / `plan_split_edge(...)` compute a **delta** — which vertices merge, which walls die, which openings land where and with what anchors — and two **thin** appliers execute it: the `Design` applier (essentially what `topology.py` already is) and a new **scene** applier that touches **only the items named in the delta**. No full rebuild; the algorithm single-sourced.

**The drift risk that makes dual appliers frightening is already policed.** `--verify-design` re-derives the `Design` from the scene at every quiescent point, so **if the two appliers ever disagree, the shadow gate fires**. P1.6 was built for exactly this moment; this is the task that collects on it.

*Bonus, and it is not incidental:* **a delta plus an applier is a command in all but name.** **P6.1** (`QUndoStack` + `MoveVertices`/`EditOpening`/…) inherits this shape for free rather than inventing it later.

**2. The three unlisted helpers — let the call-site census decide, not the list.** The rule is: **a line dies when its last caller dies. Anything deleted must be uncalled; anything still called migrates.**

- `_merge_intervals` is `fracture_delete_wall`'s alone → **falls with it**.
- `coincident_walls` and `wall_endpoint_open` have callers in the **drawing / snap paths that survive Phase 3** → **they do not fall.** They are **reimplemented as thin queries over vertex adjacency** — a vertex's degree and its incident walls — which is precisely what the task line's "vertex adjacency" clause means. Census taken at P3.3, and it is **wider than "view.py"**: `wall_endpoint_open` at `view.py:248` (draw-release snapping); `coincident_walls` at `view.py:597` **and at `walls.py:656` and `walls.py:695`, inside `WallItem.rebuild` and `paint`** — those two are the party-wall opening cascade and the render path, neither of which Phase 3 removes. Only the `walls.py:201` caller (inside `_coalesce_wall_impl`) dies. Migrate on the census, not on the module a helper happens to live in.

**3. Junction rendering — the inputs change, the output must not.** `_compute_wall_junctions` found neighbours by **bbox search**; adjacency hands them over **by lookup** (the walls sharing a vertex). The `_outline_clip` cache is recomputed from adjacency. **Seam-free is an OUTPUT contract: if the junction test needs touching, the replacement is wrong.**

> **Correction, made at the read-back rather than discovered mid-task: the existing guard is NOT a pixel test.** `tests/test_walls.py:360` `test_junction_outline_is_clipped_so_walls_read_solid` asserts `w._outline_clip is not None` for crossing walls and `is None` for a lone one — **structural, not rendered**. It would pass against a replacement that populates the cache with the *wrong* clip, which is exactly the failure a bbox→adjacency swap can produce. So point 3 has two halves: keep that test green **unchanged** (it pins the cache's shape), **and add the pixel assertion it never had** — render a cross junction and assert no light seam pixel at the crossing. Per `CLAUDE.md`, antialiased 1-px assertions need a lenient threshold (`< 190`, not `< 100`). This is an **addition**, not a rewrite, so it does not count against the changed-test budget point 4 governs.

**4. Rewritten tests get one line each: old op → new op → why the assertion moved.** For **defect 9**, the closing test is **live-editing shaped**: merge two collinear walls carrying identical openings → one survivor, openings deduped. (`planc1`'s three stacked doors were cleaned at import; this guards **the path that created them**, which is the one still open.)

**5. Telemetry expectations, stated in advance so the numbers are predictions and not rationalisations.** The tee branch's **2** split-on-writes → **0** when the split rule's second half lands. `GroupItem.bake`'s **80 remain**: they are **P4.5's**, and the counter staying nonzero until then is **correct, not unfinished**. The split-on-write shim stays until its counter is owned entirely by P4.5's rebuild.

**6. Sub-commits, each at a FULL green gate** (the P0.5 per-fix precedent — and this task is the size that earns it: one task, several rollback points):

  1. planner/applier factoring + the scene applier for `merge_collinear`;
  2. `split_edge` scene-side + the split rule's second half + the guard retarget (with its **pre-authorized** `match=` change, named in the log rather than slipped through);
  3. call-site migration, **family by family**;
  4. deletion of the dead ~375 and the junction swap.

**7. On exit.** Re-check the **P2.3 Known-regressions row by hand** — the 480″ body-drag moving as one run again — and **flip it only if it genuinely closes**. Report the **measured** deletion count against the estimated 375.

**Acceptance.** `test_coalesce.py` and the coalesce half of `test_walls.py` rewritten against the new ops — **and this is the biggest "changed test" risk in the plan, so every rewritten assertion must be justified in the log.** ~330 lines deleted from `walls.py` — **measured at P3.3 as 375 across 13 functions (25% of the file), including the three helpers point 2 adjudicates**; report the real figure on exit.

### P3.5 — Delete the detection engine
`_RoomGrid`, `_WallGraph`, `detect_room`, `_detect_room`, `room_signature`, `refresh_rooms` memoization, `bind_room_walls`, `_wall_along_segment`, `_perimeter_span`, `room_owns_walls`, `walls_cover_room`, `duplicate_wall`, `_privatize_shared_walls`, `synthesize_room_edge`, `reloop_open_room`. "Detect room here" becomes `topology.enclosing_face`. **Defects 8 and 13 close here.**
**Acceptance.** ~550 lines deleted from `rooms.py`. `test_rooms.py` and `test_room_walls.py` pass against stored outlines. `room_boolean` rewritten as a polygon op on outlines that touches only its own walls.

**Settled before implementation** *(2026‑07‑27 — four riders on the read-back; committed to this file first, per the handoff-spec rule, so the implementing session reads them from disk).*

**1. The headline check — the acceptance's essence in one assertion.** After the flip a wall move must update room outlines **by construction, with zero recomputation**: the outline references the same `Vertex` the wall does, so `relocated_to` moves both, or the model is wrong. **The proof is the existing P3.3 demo test** — the Lounge / Front Porch party wall, +12 y, ±17.5 sf, total unchanged — **passing with `refresh_rooms` deleted.** That one test surviving the deletion of the machinery that used to make it pass is the whole phase in a single assertion.

**2. The tripwire disambiguation, made mechanical.** `test_a_corner_is_still_two_distinct_wall_vertices` can go red two ways: the designed outline flip, or a weld reaching the room-creation path (P3.4 built `share_coincident_ends`; `make_room` never calls it). **Sequence the sub-commits so the flip is unambiguous: retarget the docstrings → flip outlines to vertex identity (the guards flip HERE, for the designed reason) → then any path changes.** Red at any other point is a finding, not the flip.

**3. Defect 13 — do not tick it on the disappearance of its measuring instrument.** The read-back established that `detach_wall_from_room` contains no detection today, and the only zoom-dependent quantities on that path are the drag's (`mousePressEvent`'s `20.0 / _view_scale()` endpoint catch radius, `_project_to_orthogonal`'s `16.0 / view_scale` stick). *Archaeological note:* the original `test_zzprobe` evidence counted **OpenWalls after `detach_wall_from_room` at pinned zooms** — and `reloop_open_room` plus the bind machinery die here while `OpenWall` itself dies at **P3.7**, so the repro's substrate is being demolished across two tasks. If it cannot be reproduced at the P3.5 exit, write **"repro substrate removed, defect retargeted to the drag tolerances"** rather than ticking it. *A defect closed by the disappearance of its measuring instrument is not closed.*

**4. Census divergences, approved as tabled.** Realistic deletion **~470 from `rooms.py` + 34 from `walls.py`** against the ~550 estimate, with four names owned elsewhere: `_perimeter_span` (24) falls with `fracture_delete_wall` at **P4.1**; `duplicate_wall` (15) at **P4.5**; `room_owns_walls` (14) and `walls_cover_room` (20) are **rewritten as outline predicates, not deleted** (last caller is `GroupItem.bake`). `_privatize_shared_walls` (28) is assessed **in-task**, with the outlines already flipped, rather than guessed now. `synthesize_room_edge` (13) is already callerless — a free deletion. **`test_rooms.py` / `test_room_walls.py` rewrites are this task's authorized zone**, same discipline as P3.4: one line per rewritten assertion, old mechanism → stored outline → why.

### P3.6 — Opening anchors
`s` → `{from, offset_in}`. Delete the silent clamp in `WallItem.rebuild` (**`walls.py:1004`**, not `:568` — the line moved through P3.3–P3.5) — an out-of-range opening is an error surfaced to the user, not a slid door. Replace the **8 verified** `except ValueError: continue` sites that silently drop an opening with a collected, reported error list. **Defects 6 and 7 close here.**

**Read-back corrections, settled 2026‑07‑28** *(the numbers in the line above were quoted from the review and did not survive being checked; recorded here rather than carried).*

- **"13" was never the count of opening drops.** Measured at the migration baseline `841264e`: **13 is the count of *every* `except ValueError` in `floorplanner/`**, of which **7** wrapped an `OpeningItem(…)`. Today: 17 total, 9 wrapping `OpeningItem`, of which **8 are still silent** (`bridge.py` was converted to a reported list at P1.5 and its comment forecast this task). The other four at baseline are catalog price parsing ×2, `macro._is_num`, and dialog handlers that already report — feeding those into an opening-error list would be wrong. **The 8:** `planio.py:169` (the v4 load — defect 6's "incl. on load"), `mainwindow.py:1082` and `:1177` (paste), `rooms.py:749` (privatize), `rooms.py:1046` (`duplicate_wall`), `walls.py:333` (merge), `:587` (split), `:675` (fracture).
- **"P0.4 test 1 passes without xfail" pinned nothing** — it was never xfail. P0.4's own log says *"Passes: opening-s under group move AND rotate"*, and both still pass. Replaced by R1 below.
- **Defect 7's four cited sites are stale.** The *condition* is verified intact — nothing anywhere re-bases `op.s` — and that condition, not the site list, is what the anchor closes.

**Rulings, settled 2026‑07‑28 (R1–R5).**

**R1 — Acceptance.** The schema's own rationale, as three tests plus the report:
  (a) an opening anchored `from: "v2"` keeps its `offset_in` exactly when the wall is stretched **at v2** — *the discriminating case*, since absolute `s` holds position relative to v1 instead;
  (b) reversing a wall leaves the opening's physical position unchanged;
  (c) the split of R2;
  (d) loading a plan whose door no longer fits **reports** it.
  **Receipt standard:** (a) and (b) must be shown failing against `s`-based code in a worktree before the anchor lands.

**R2 — Straddle: the primitive becomes TOTAL, and both pins flip.** P3.4(ii)'s decline was a placeholder pending representability, and `match="P3.6"` was that test naming its own executioner. **Load-time planarize cannot decline** — a crossing that exists in the data has to split, and refusing there aborts or corrupts a load. Semantics: the opening anchors to the segment containing its **anchored end**; if its extent no longer fits that segment, it joins the collected report. **The scene op's decline dies with it** — a gesture that silently does nothing is defect 17's disease and we do not keep a second case on purpose. Both flipped assertions carry a one-line justification citing this ruling.

**R3 — The drag clamp LIVES,** and is annotated so a later census does not kill it as a survivor of this task. `rebuild`'s clamp silently repairs *stored data* (dies); `OpeningItem.mouseMoveEvent`'s (**`walls.py:1821`**) bounds a *gesture* (lives) — the same distinction that keeps `wall_endpoint_open` and `_WallBBoxIndex` in the "rightly spatial, permanently" category.

**R4 — `center`: consume, never produce.** Emitting `center` requires knowing the user *meant* centred, and inferring that from coordinates that happen to be the midpoint is detection-from-geometry — the disease v5 exists to kill. P3.6 emits `v1`/`v2` only, **nearer end, ties broken toward `v1`**, so canonicalization round-trips deterministically. **Production of `center` is deferred until a UI expresses the intent.**

**R5 — One vocabulary, two surfaces.** All 8 sites feed the `rep["openings_failed"]` structure, entries naming wall, opening type and anchor. Surfaced by context: **load-path** entries (`planio.py:169` included — that is defect 6's "incl. on load" closing, and it ends the v4-silent / v5-reported asymmetry) join the open/conversion report per P2.1; **edit-path** entries (paste ×2, merge, split, fracture, privatize, `duplicate_wall`) surface as a status-bar line naming the edit, **said once** — the `06c2145` wording standard applies.

**R4b — anchors: FIDELITY on round-trip, canonical at MINT only** *(settled 2026‑07‑28; overrules the canonicalize-on-emit shipped at P3.6(1))*. An anchor that already exists — loaded from a v5 file, or held by the live item — round-trips **verbatim**. The nearer-end / tie-to-`v1` rule of R4 applies **only when minting**: a legacy import, or an opening that has never had an anchor. *Why:* the anchor end changes behaviour under stretch, so re-basing it on save is **silent loss of intent — the same category as the clamp P3.6 deletes.** `_walls_of` reads the stored anchor when present and mints only when absent. Pinned by a round-trip test: a hand-authored FAR-end anchor survives load → save unchanged.

**R2b — the straddle rule, confirmed as read.** **Extent decides:** an opening wholly inside one segment lands there regardless of which end it is anchored to. The anchored-end rule is the tiebreak for the **true straddle only** — where the opening necessarily overhangs and is necessarily reported. When an opening lands on the segment that does *not* contain its anchor vertex, it **re-seats to the same-side end of its new segment** (the split vertex), exact position preserved, offset recomputed — **same-side, not nearer-end**, consistent with R4b.

**Also in scope, found during the read-back: defect 24.** `topology.graph_from_design` and `_reanchor` read and write `offset_in` as a **centre** distance where the schema, `bridge._walls_of` and `bridge._opening_s` all define it as a **near-edge** distance. This is the anchor arithmetic, so it is this task's; and R2's straddle test (`ov.s - half < s < ov.s + half`) rests on the value being right.

### P3.7 — Delete `OpenWall`
An outline edge with `wall: null` renders dashed.
~~**Acceptance.** `test_open_walls.py` rewritten against null edges; the class is gone.~~

**AMENDED ACCEPTANCE, settled 2026‑07‑30 before any code** *(the P3.6 lesson applied to a three-line task: a spec whose acceptance can pass vacuously is the same class of problem as a task line whose three numbers were all wrong — fix the spec first, then the code).*

**Two rulings from the read-back, and they are what the amendment implements.**

**R1 — RENDER-ONLY. No item, no interaction.** An open edge is *the absence of a wall*; interacting with an absence means either drawing a wall there (the draw tool already owns that) or moving the room (the room owns that). Selection of a nothing has no meaning to implement. `test_open_wall_is_editable`, deleted at P3.5 because "it asserted drag controls on a placeholder nothing constructs", **stays a precedent rather than a casualty**: no drag controls on something nothing constructs. The cue is drawn in `RoomItem.paint` from `RoomItem.open_edges()` — the fact and the cue from **one** representation, which is what the P3.5 Known-regression row promised. **Match the old `OpenWall` dash visually** so the row closes as *"same cue, one representation"* and not as *"different cue"*. If a later phase needs open-edge hit-testing, **that phase specs it** (P4.2 extract/join is the plausible candidate); a fence comment at the paint site naming P4.2 is welcome, not mandatory.

**R2 — THE PIXEL ASSERTION IS REQUIRED, on P3.4's junction-contract template:** render, **measure the polarity first**, then assert with a measured threshold. A dashed line is the canonical structurally-green / visually-absent cue, and the old acceptance would have passed with nothing drawn at all.

**The four acceptance items:**

**(a) `test_open_walls.py` against null edges — VERIFY, DO NOT RE-DO.** Already landed at P3.5 and logged there as `[DIVERGENCE — the whole file]`: `_open_count` sums `r.open_edges()` and the file's docstring states the old→new mechanism. What remains of it here is only its four `not w.is_open` helper filters, which fall with the flag in (c).

**(b) Pixel assertion, polarity measured**, on a room with an open edge: the dashed cue is drawn along the vacated stretch, and the closed sides are unaffected. Both halves in one test — positive and negative — so the positive assertion cannot go vacuous, exactly as P3.4's junction test does.

**(c) The class is gone**, by the standing rule (*a line dies when its last caller dies*). **Census taken on disk 2026‑07‑30, and it diverges from the estimate in two ways — reported rather than forced:**

- **THERE IS NO LIVE PRODUCER, and there has not been since P3.5.** `grep "OpenWall("` over the tree returns **zero** constructor calls. The **P2.3 producer branch in `apply`** named in the estimate is already deleted — `bridge.py:959` is now a *comment* recording that it went at P3.5. **The Progress-log line at P2.3 ("apply now builds an `OpenWall` per `wall: null` outline edge; P3.7 retires the branch") is stale history and is annotated as such**, not acted on. So the class is dead code today: deleting it removes a definition, not a behaviour.
- **`is_open` IS THE REAL SWEEP, and it is ~7× the estimate.** The estimate said "comments/docstrings ×7". Measured: the flag is read at **23 sites in `floorplanner/`, 19 in `tests/`, and 2 in `docs/make_gallery.py` — 44 readers across 17 files** — plus the definition (`walls.py:902`) and the override (`:1685`). **Every one of them is permanently `False`** once nothing constructs an `OpenWall`, and `walls.py:1631` already says so in a comment. The flag dies with its producer and the readers go with it: *a permanently-false flag is worse than no flag, because it tells every future reader that open walls exist as items.* Sub-committed separately from the rendering, so the mechanical sweep is its own rollback point.

**(d) The P3.5 Known-regression row closes**, citing the pixel test (b) as its receipt — not the deletion, and not "the code now draws something". The row's own wording is the bar: *the same cue drawn from the one representation instead of a second one.*

**Sub-commits:** (1) this amended acceptance; (2) rendering + pixel test; (3) the deletion sweep. **Full-mode `tools/gate.py` trailers throughout.**

### P3.8 — Perf verification
Re-run P0.3 and compare against the P0.6 numbers.
**Acceptance.** Ratios recorded in the log. Grouping 20 rooms creates **0** new walls — assert it.

**Also: the SPLIT-ON-WRITE EXIT SURVEY** *(added 2026‑07‑28)*. Assigning `p1`/`p2` mints a fresh vertex for that end, and three separate defects have now come from something downstream being left on the old one: the P3.1 shim's own telemetry, **defect 22** (bake orphaning room outlines) and **the anchor orphaning** found at P3.6(1) (12 of 41 openings mirrored on loading `planc1`). Three members is a pattern, not a coincidence. **Census at P3.6: 9 direct coordinate-assignment sites remain** — `mainwindow.py:568,569` (align to grid), `:578,579` (`_translate_shape`), `view.py:402` (the rubber-band wall being drawn), `walls.py:1511,1513` (the endpoint drag), `walls.py:1549,1551` (the `rigid` and `tee` branches, both P4.5's / P3.3's by ruling). P3.8 re-runs this grep, records the count, and for each survivor states what carries the things attached to that end — or names the task that will.

**And: the OPEN DRAG QUESTIONS.** *(table added 2026‑07‑30.)* Two questions about what a mouse gesture does have now been left explicitly unanswered rather than guessed, each because the measurement that would settle it was out of its task's scope. They are surveyed together here because they are the same organ — the endpoint drag — and because an unassigned question with no home is one nobody re-reads. **Neither is scoped to P3.8 by this table; P3.8 records the answer or names the task that will.** *(Structural note: this table is new. The split-on-write survey above is prose, and defect 13's drag half lives in the defect register's row 13 as "unassigned (drag)" — it is restated here so the two sit beside each other, not moved.)*

| question | why it is open | how to answer it |
|---|---|---|
| **Defect 13's drag half — does a drag's RESULT depend on view zoom?** *(**Status authoritative in register row 13; this row is the exit checkpoint.** One direction only — the register keeps the history, the survey blocks the exit. This row is a restatement, so it is the one that can drift.)* | Measured at P3.5 **before** anything was deleted: the same scene-space gesture gave **0 open sides at 0.25× and 1 at 0.5×–4×**, leaving the wall's far end at y=120 versus y=60. The detection half closed structurally; the zoom terms that remain are the drag's own — `mousePressEvent`'s `20.0 / _view_scale()` endpoint catch radius and `_project_to_orthogonal`'s `16.0 / view_scale` stick. Retargeted and left **unassigned** rather than invented a home for. | Drive the same gesture at pinned zooms and compare the resulting geometry, as P3.5 did — then decide whether a gesture tolerance *should* be zoom-relative (it probably should) and whether the RESULT may be. **P4.2** is the nearest task that touches the drag. |
| ~~**Does a real endpoint drag re-point every outline holder, or strand a third room?**~~ **ANSWERED at P3.8 (3): IT STRANDS — registered as defect 30.** A real viewport-driven body drag at `symmetricP1`'s 4-way corner (582, 714) moved it **(0, −24)**; Dining and Kitchen followed; **Foyer and Great Room were left behind**, each with one wall end at the new corner and one at the old while its outline stayed at the old. Step 4 gathers from the **run's rooms**, not the corner's **holders**. The ENDPOINT drag is a separate answer: it assigns `p1`/`p2`, which is split-on-write by P3.1's ruling and deliberately leaves the outline behind — that is the open-side feature, not a defect. Pinned `xfail` by `test_a_dragged_corner_carries_every_room_that_holds_it`. | The 38 synthetic drags at the defect-28 resolution **moved the corner in none of them**, so the app is neither cleared nor accused — that run's "0 stranded" is vacuous and was discarded rather than quoted as an acquittal. The question matters because the *test* that stranded a third room was hand-rolling what the drag does, and `mousePressEvent` step 4 gathers outline edges from the **run's rooms**, which is not obviously the same set as **every room holding the corner**. | **Answer with a real drag** — driven far enough to actually move the corner, asserted as having moved — **on a corner held by 3+ rooms**, then check every holder followed. |

---

# Phase 4 — Rooms as durable movable units

### Phase‑4 branch strategy — ruled 2026‑07‑31 at the P4.1 read-back

**Per-task branches**, each PR'd into `main` as a **merge commit** (never
squash), full-mode `tools/gate.py` trailers on every sub-commit. The facts that
changed since Phase 3's single-branch ruling: `main` now runs the DEEP
invariant job in CI itself (defect 27's closure), and Phase 4's tasks are
separable, releasable deliverables — each leaves `main` shippable, so there is
no intermediate state a long branch needs to hide.

**Two designated mini-gates:** P4.2 and P4.5 additionally require a Patrick
manual check before their PRs merge — they are the two tasks that change what
gestures MEAN (extract/join, and the group-semantics ruling). P4.1, P4.1b,
P4.3 and P4.4 merge on green CI plus reviewer acceptance.

### P4.1 — Delete-wall keeps the room
*(branch `p4.1-delete-wall`; scope verified and amended at the read-back, 2026‑07‑31)*

Deleting a wall genuinely deletes it; the room survives because its stored
outline (P3.2/P3.5) holds the corners — the vacated edge becomes open
(`wall: null`), drawn dashed by the room. No fracture, no trim-and-rebind.
**Defect 17 closes here**, with a coda measured at the read-back: post-P3.7 the
fracture "no-op" is not even silent any more — fracture deletes the original
wall and mints a replacement segment, the outline still names the dead wall,
and `open_edges()` therefore counts the edge open, so the room paints a dashed
open cue over an edge a wall actually covers (measured: 4 bound walls + 1 open
edge, against P0.4-era 4 + 0). Defect 17's silence aged into misinformation —
the final argument for deletion over repair.

**Census (fresh at the read-back, 2026‑07‑31):** `fracture_delete_wall`
(walls.py:653–709, 57 lines; live callers `delete_selected` at
mainwindow.py:490 and the wall context menu at walls.py:1666) and
`_merge_intervals` (walls.py:642–650, 9 lines; sole caller inside fracture)
die — **66 lines, two call sites**. `_perimeter_span` does **not** die here —
see the register's carried census note (authoritative copy).

**Tests that change, declared in advance and approved:** characterization 2b's
xfail marker comes off (the acceptance itself; its comment's "0 open edges"
figure is era-stale — today the no-op measures 4 built + 1 open);
`test_walls.py::test_fracture_delete_free_wall_removes_whole` preserves its
behaviour through the new delete entry point; `test_walls.py::
test_fracture_delete_keeps_room_edge_drops_overhang` and `test_room_walls.py::
test_fracture_delete_shared_wall_keeps_both_rooms` are **intentionally
replaced** to encode the measured new truth: the whole wall goes and each
bordering room keeps its area with one open edge (party-wall case measured at
the read-back: both rooms 100.0 sf, 3 bound + 1 open each).

**Acceptance.** P0.4 test 2 flips to pass.

### P4.1b — Defect 25's gesture-time message
*(ruled 2026‑07‑31: standalone and immediate — branches the moment P4.1's PR merges)*

The register's move trigger fired on both arms at once (P4.1 opened; Gate 3
delivered the first user report), and folding into P4.1 was rejected on the
fold-proposer's own honesty: the fold rested on next-to-touch plus the fired
trigger, not on mechanism. Scope, **message only**: draw-release and end-drag
say at gesture time what R2c's walk already detects and files — a message
naming *this* edit and *the doorway*, through the defect-6 edit-path
vocabulary, replacing the generic torn-network breadcrumb. Explicitly NOT in
scope: any change to what the gesture *does* — decline/split/weld policy stays
P4.3's with the `auto_*` flags (the dissent's surviving kernel).
**Acceptance.** Drawing a wall whose end lands inside a doorway produces the
specific message at release (and the same for an end-drag); the document
walk's report path stays unchanged as the load-path safety net.

### P4.2 — Extract / join
Per §4 of `DESIGN_MODEL_v5.md`. Extract privatizes walls and vertices, sets `state: floating`, `extracted_from`. Join welds, merges coincident walls, splits, rebinds, sets `state: placed`, and coalesces only the touched degree-2 vertices.
**Inherits a QUESTION from P4.1's census, not a claim** *(authoritative copy: the register's carried census note, 2026‑07‑31)*: whether `_perimeter_span` dies here — it does only if `_copy_spec` (its other surviving caller, owned by no phase) is also reshaped here. P4.2's read-back must answer it. *(ANSWERED at the P4.2 read-back: no — `_copy_spec` is §4's "Duplicate a room", which is P4.4's; re-argued to P4.4 as a contingency. See the register's note, which stays authoritative.)*
**Acceptance.** Extract → move 500″ → join at a new location → `check()` clean at every step; furnishings and openings intact; I12 holds while floating.
**Also required:** flip `test_groups.py::test_extracted_room_region_follows_move` back from `xfail` to a hard pass — via a real `extract`, not via selection-time synthesis. That test is the receipt for the P0.5 regression in Known regressions above.

### P4.3 — Shuffle mode
`settings.editing.{shuffle,auto_coalesce,auto_weld,auto_bind}` + a toolbar toggle. Leaving shuffle joins nothing automatically.
**Acceptance.** With shuffle on, dragging a floating room across the plan leaves both unchanged; `check()` clean throughout (I11 exempts floating rooms).

### P4.4 — Concept rooms, `nominal_size`, duplicate-as-template
Create a room by typed dimension; duplicate a room as a floating unit; save/load a one-room design as a template.
**Acceptance.** A one-room file validates against the schema and loads into an existing design as a floating room.

### P4.5 — Group semantics + z-order
Groups move the real items — no `duplicate_wall`, no `coalesce_all` on ungroup. Groups serialize (`Design.groups`). Collapse the four z schemes into one that is serialized. **Defects 3 and 11 close here.**
**Retire or re-justify P3.3's `kind == "rigid"` carve-out here, explicitly.** A wall drag promotes coincident ends into shared vertices, but *excludes grouped neighbours* — they keep the old coordinate path, following the drag without becoming topology. The reason is this task's premise: grouping **duplicates** a room's walls onto the originals, so a grouped coincident end is the common case and not an exotic one, and sharing one would wire a group member to an outside wall permanently while what a group *is* topologically is still undefined. Exactly the reasoning behind the `group() is None` gate that keeps grouped walls out of coalesce — deliberately not topology. **When groups stop copying walls, that reason evaporates**, and a carve-out whose justification has gone is how a workaround becomes folklore. Decide it here: delete it, or write down the new reason.
**Acceptance — CORRECTED 2026‑08‑04 against the merged tree, and the correction is the point.** The original line read *"P0.4 tests 3, 4 and 6 flip to pass"* and named three `test_groups.py` tests by LINE. Measured at `adaa519`: **only ONE flip is available** — test 3 (`test_characterization.py::test_group_survives_roundtrip`) is the sole surviving xfail of the three. Test 4 (`test_group_move_undo_restores`) was promoted to a hard pass at **P0.5** (its own comment says so) and test 6 (`test_group_ungroup_reaches_fixed_point`) passes today. The line numbers had also drifted — **the fourth instance of that class**, so every test below is named, never numbered.

**Acceptance, as it now stands:**
1. `test_characterization.py::test_group_survives_roundtrip` flips xfail → pass (defect 3).
2. `test_groups.py::test_a_clipped_band_leaves_every_room_coherent` passes — and the log must say it passed **as a consequence of the mechanism, not as a fix** (§2a's ruling).
3. `test_groups.py::test_grouping_rooms_without_their_walls_still_copies_them` is **rewritten into its opposite** (grouping a room alone creates nothing and moves the originals) — a declared assertion change.
4. The three tests encoding duplicate-on-group semantics are *intentionally* replaced, named not numbered: `test_grouping_a_room_duplicates_its_walls`, `test_grouping_room_with_its_walls_makes_no_coincident_copies`, `test_group_move_room_only_does_not_orphan_walls`.
5. `test_grouping_twenty_rooms_with_their_walls_creates_no_walls` is renamed and widened to **creates no OBJECTS at all** (walls *and* openings).

---

# Phase 5 — Landscape

### P5.1 — Site levels, categories, area accounting
`level.kind`, `room.category`, `area_accounting` with the class-scoped I11.
**Acceptance.** `examples/site_demo.json` opens, edits and re-saves clean. Area totals report conditioned / unconditioned / site separately.

### P5.2 — Landscape wall types + gates
`fence`, `hedge`, `retaining`, `railing`; `kind: "gate"`; no finishes on landscape walls.
**Acceptance.** Drawing a fence and placing a gate round-trips; placing a *door* in a fence is refused.

### P5.3 — Site schedule fields + reports
`surface`, `plant_palette[]`, `irrigation`, `sun_exposure`, `slope_pct`, `drainage`, `edging` in the room properties dialog; inventory/schedule split by accounting class.
**Acceptance.** Site rooms schedule correctly; interior reports unchanged.

---

# Phase 6 — Command undo and final perf

### P6.1 — `QUndoStack` + commands
`AddItems`, `DeleteItems`, `MoveVertices`, `EditOpening`, `EditRoomProps`, `Group`/`Ungroup`, `Extract`/`Join`, `ChangeSettings`, level ops. Each references items by id and re-runs a scoped rebuild.
### P6.2 — Retire snapshot undo
### P6.3 — Scene index + viewport update final pass
Revisit `FullViewportUpdate` now that bounding rects are trustworthy.
**Acceptance.** P0.3 numbers improve again; undo cost is independent of plan size (assert: undo time on a 20-room plan ≈ undo time on an 80-room plan).

---

## Risk register

| Risk | Mitigation |
|---|---|
| **P3 is the whole refactor in one phase** | Branch; P3.1/P3.2 are compat shims that keep every caller working, so the suite stays green while the store changes underneath |
| **Tests quietly relaxed to match new behaviour** | Every changed assertion must be named and justified in the Progress log; P0.4 characterization tests are written *before* the behaviour changes |
| **P3.4 and P4.5 legitimately invalidate existing tests** | Called out in advance — those are the only two tasks where rewriting tests is expected rather than suspicious |
| **The perf win doesn't materialise** | P0.3 exists before any of it; P0.6 and P3.8 both record numbers, so a regression is visible at the task that caused it |
| **Legacy files silently change on open** | Never modified in place; conversion is reported and requires an explicit Save (P2.1) |
| **Macro/gallery/extract tooling drifts** | P2.4 converts them at the format cutover, not later |

## Sequencing rationale

Phase 0 before anything: without the scaling harness and the characterization tests, no later phase can be shown to have worked. Phase 1 before Phase 2 so the document is proven against the live scene before it owns the file. Phase 2 before Phase 3 so the format cutover is separately revertible from the geometry rewrite. Phase 3 before Phase 4 because extract/join/shuffle need vertices. Phase 5 is additive and could move earlier if landscape work becomes urgent. Phase 6 last because commands want stable ids and settled operations.

---

## Progress log

*Append one entry per task. Newest at the bottom.*

```
P0.0  done
ruff:    n/a (doc only)
pytest:  n/a
files:   CLAUDE.md
notes:   "## v5 migration (in progress)" block added verbatim after Architecture,
         before "## Generated assets". No code change.

P0.1  blocked -> resolved
ruff:    23 findings at first run — ALL in tools/ and docs/_superseded/,
         0 in floorplanner/ or tests/. Correctly reported rather than papered over.
         RESOLUTION: fixed at source (17 after dedup across the two copies),
         docs/_superseded moved to _to_delete/. ruff check . now clean.
pytest:  287 passed, 0 failed, 0 xfailed, 0 skipped in 7.59s
quick:   276 passed, 11 skipped in 6.18s
files:   tools/{validate_design,migrate_to_design_v5,make_site_demo}.py (lint only)
notes:   No test changed. Tools re-verified after the lint fixes: welds=31,
         rooms_traced=19, openings_deduped=2; symmetricP1 + site_demo PASS/PASS;
         planc1.v5 still 23 invariant errors (intended fixture).

BASELINE OF RECORD
  full   287 passed / 0 failed  in 7.59s
  quick  276 passed / 11 skipped in 6.18s
  ruff   clean over the whole tree
  15 slowest: test_extract::test_detect_walls_on_clean_plan 0.75s;
              test_extract::test_fp_extract_cli_end_to_end 0.30s;
              test_macro::test_fp_macro_cli_pup_resize 0.29s; rest <= 0.12s.
  Note: the suite is fast because nothing in it is large. No test exceeds ~5
  group members and none exceeds 36 rooms — which is precisely why P0.3 exists.

P0.2  done
ruff:    clean
pytest:  287 passed, 0 failed, 0 xfailed, 0 skipped in 6.67s
files:   FloorPlanner.py (4 private re-exports removed);
         test_inventory.py, test_coalesce.py, test_walls.py, test_rooms.py
         (direct submodule imports);
         test_rooms/test_view/test_groups/test_selection (phase comments only)
notes:   NO assertion changed — import source + comments only.
         Touches list was wrong in three ways and the code was followed instead:
         test_io.py listed but references none of the names (left alone);
         test_inventory.py (_money) and test_walls.py (_coalesce_wall_impl)
         not listed but did need the switch. Correct call.
         Phase annotations corrected after review:
           room._detect_sig  -> P3.5   (refresh_rooms memoization)   confirmed
           win._sel_order    -> P3.5   (room_boolean rewrite)        confirmed
           dup._path         -> P0.5   (NOT Phase 3 — see below)     corrected
           g._angle          -> P4.5   (group semantics)             confirmed
           view._zoom_accum  -> none   (NOT scheduled for removal)   corrected
         dup._path: test_selection's duplicate comes from select_in_rect ->
         synthesize_room_edge, which P0.5 fix 4 removes. Retired at P0.5, not
         Phase 3.
         view._zoom_accum: wheel coalescing is a deliberate, documented perf
         feature (CLAUDE.md, view.py:159-179) that the migration KEEPS and
         copies to drags. Nothing deletes it. The assertion is brittle (an exact
         accumulator value of 400) but that is a test-quality nit, not a
         migration hazard.

P0.3  done   (commit 12024f1; b00af84..12024f1 = four rollback points, unpushed)
ruff:    clean
pytest:  289 passed, 2 xfailed, 0 failed in 8.72s
         --quick: 276 passed, 15 skipped in 5.46s (harness behind `slow`, as intended)
files:   tests/test_scaling.py (new)
notes:   No existing test touched. Ratios recorded WITHOUT weakening the
         threshold, per acceptance — group and ungroup are xfail(strict=False)
         -> P3.8; rebuild and bake assert hard.
         Numbers surfaced via warnings.warn (visible under plain -ra) rather
         than print (captured and hidden unless -s). Adopted as the convention.
         FINDING: room detection is clipped to canvas_rect() (rooms.py:29), so
         the n=8 grid (960") overflowed the default 840" canvas and edge rooms
         went undetected until the canvas was enlarged. Logged as defect 16.

P0.3b  done   (commit 43e838b; step 3 landed separately, see below)
ruff:    clean
pytest:  289 passed, 3 xfailed in 9.19s
         --quick: 276 passed, 16 skipped (all 5 scaling tests skipped)
files:   tests/test_scaling.py (fifth timed op; no other test touched)
notes:   Selection-building is the worst-scaling op measured, and the one
         nothing was timing before Ctrl+G.
           select   2.7 ms (16 rooms) -> 71.8 ms (64 rooms)   ratio 27.07  XFAIL
         27 is ABOVE the quadratic reference of 16 -> confirmed O(R^2 * W): each
         setSelected fires _update_edit_actions -> _selected_room_shapes(), which
         reruns bounding_walls() (QPainterPath booleans) for every already-
         selected room. ACCEPTANCE FIGURE: selecting all 64 rooms one at a time =
         71.8 ms HEADLESS -- excludes ALL repaint cost (FullViewportUpdate, no
         setCacheMode), so the felt stall is this PLUS a full-scene repaint per
         click, i.e. strictly worse. xfail(strict=False) -> P3.8. Nuance: P3.5's
         stored outlines cut the per-room W constant, but the O(R^2) recompute
         STRUCTURE lives in _selected_room_shapes and may not clear until P4.5.

P0.3b-step3  done
ruff:    clean
files:   pytest.ini (register `perf` marker); tests/test_scaling.py (tag every
         test perf + slow); .github/workflows/ci.yml (test step -> -m "not perf")
notes:   Precondition for the first push. `perf` and NOT `slow`, deliberately:
         excluding `slow` from CI would also drop the deterministic slow tests
         (fp_extract CLI, macro CLI subprocess) worth running there. Only the
         timing-ratio assertions are unsafe on shared runners. --quick behaviour
         unchanged (scaling tests keep `slow`).

P0.4  done
ruff:    clean
pytest:  294 passed, 6 xfailed in 10.42s
files:   tests/test_characterization.py (new)
notes:   6 behaviours pinned; no existing test modified. Passes: opening-s under
         group move AND rotate; delete-wall keeps the room (2a); grouped walls
         exempt from coalesce_all; group/ungroup 4x fixed point. xfail: 2b
         delete-actually-removes-the-wall (P4.1), group survives roundtrip
         (P4.5), group+move+undo restores (P4.5).
         FINDING that reshaped the task: test 2 was predicted xfail->P4.1 but
         PASSED. Diagnosed: the room survives because the wall is never deleted
         -- fracture_delete_wall keeps the perimeter stretch and rebinds it
         (measured 4 walls in, 4 out, 0 open edges). A single "room survived"
         test passes in both today's and P4.1's world, so it proves nothing about
         the change. Split per the amended plan into 2a (invariant, asserts hard,
         must never regress) and 2b (wall actually gone: 3 built + 1 open edge,
         xfail->P4.1). Refused deletion with no message = defect 17.

P0.5  done   (5 fix commits 947ae4f..76c32ee + 1 gate-resolution commit)
ruff:    clean
pytest:  298 passed, 6 xfailed, 0 failed, 0 xpassed in 9.14s
files (source): rooms.py (fix1 RoomItem.itemChange + sip import),
         mainwindow.py (fix2 dict(it.properties); fix3 refresh_rooms_cmd active-
         floor scope), view.py (fix4 select_in_rect read-only),
         catalog.py (fix5 price overrides -> config_dir, merged on load).
TESTS ADDED (one per fix): test_rooms::test_removing_room_unbinds_its_walls;
         test_io::test_project_from_scene_copies_room_properties;
         test_floors::test_refresh_rooms_cmd_spares_inactive_floor_rooms (two
         floors, inactive-floor room survives -- per acceptance);
         test_ai_pricing::test_apply_prices_writes_config_not_manifest +
         test_price_override_reloads_from_config.
TESTS CHANGED (each a red flag, named per the working agreement):
       * fix 4 (authorised): test_selection.py's two defect-asserting tests
         rewritten to assert selection creates nothing --
         test_room_edge_on_party_wall_is_not_duplicated,
         test_party_wall_edge_selection_leaves_the_door_intact; module docstring
         updated; the P0.2 dup._path assertion retired here as scheduled.
       * fix 5 (necessary consequence): test_apply_prices_updates_manifest_and_
         catalog asserted the defect (a manifest write) -> replaced with
         test_apply_prices_writes_config_not_manifest; manifest_guard fixture
         (existed only to restore the mutated asset) -> price_sandbox (redirects
         override path to tmp); test_placed_item_picks_up_price and
         test_dialog_fetch_applies_without_network switched to it.
       * gate fallout from fix 4 (NOT anticipated in the 3 named tests):
         test_groups::test_extracted_room_region_follows_move failed -- its
         "extract via rubber-band" workflow stood on the synthesis fix 4 removed.
         Root cause: old select_in_rect synthesised the party edge AND the
         following rebuild rebound the room to that private copy, so bake's strict
         room_owns_walls could carry it. Decision (a): xfail -> P4.2, logged in
         Known regressions; label-drag (_privatize_shared_walls) is the workaround.
       * XPASS resolved: test_characterization::test_group_move_undo_restores
         (was xfail->P4.5) PROMOTED to a hard pass -- fix 2 closed it (snapshot no
         longer aliases live properties). Verified first that test 3
         (group_survives_roundtrip) is STILL xfail, so P4.5's remaining half is
         still held; comment points at test 3 as the holder.
notes:   PROCESS: after this, run the FULL gate before each commit in a multi-part
         task, not just at the end -- fix 4 committed green on test_selection.py
         alone but red on the full suite (the extracted-room test). A targeted run
         proves the fix; only the full suite shows what else it touched.

P0.6  done   (item 1 commit c9451a5 + items 2-6/harness-split commit)
ruff:    clean
pytest:  300 passed, 4 xfailed, 1 xpassed in 8.44s
files:   mainwindow.py (item 1 debounce+cheap-count selection actions; item 3
         _update_totals off scene.changed onto the 180ms dirty timer),
         items.py (item 2 GroupItem._oriented_box cache; item 5 FurnishingItem
         DeviceCoordinateCache), rooms.py (item 4 cache QFontMetricsF x2 +
         boundary stroker), tests/test_scaling.py (split select op).
BEFORE -> AFTER ratios (t(2n)/t(n), n=4->8; before = P0.6 start):
                       before        after
           rebuild     2.48          2.84         (paint items don't touch it)
           select      25.90/75.5ms  -> SPLIT:
             select_burst              5.56 / 1.1ms   HARD PASS (debounce)
             select_interactive        3.63 / 6.6ms   HARD PASS (cheap-count)
           group       12.37         10.92        (still xfail -> P3.8)
           bake         4.53          4.69
           ungroup      8.56          5.62         (item 2's _oriented_box cache
                                                    cut its boundingRect cost.
                                                    Kept xfail(strict=False)->P3.8
                                                    -- see below: the sub-8 is
                                                    incidental, not a real fix.)
ITEM 1 (the headline): selecting all 64 rooms 75.5ms -> select_interactive 6.6ms
         (~11x on the honest per-click model; ~44x on the coalesced single pass).
         Split per the amendment: select_burst (no pump; debounce does the work)
         and select_interactive (processEvents per click; cheap-count does it).
         Both clear the threshold, so both are HARD PASSES (was one xfail).
ITEM 6: measured NoIndex vs BspTreeIndex on the 64-room grid -- NoIndex wins
         every op (rebuild 3.4 vs 3.6, group 138.6 vs 148.1, bake 136.9 vs 162.6,
         ungroup 197.5 vs 229.6 ms). Default UNCHANGED, per "only if BSP wins".
notes:   Items 2-5 are paint-time wins the headless harness barely reflects
         (no repaint), so rebuild/bake/group ratios move within noise; they are
         behaviour-preserving (full suite green, no test changed except the
         harness split).
       * select_burst: CONVERTED to an absolute assertion (large < 5 ms), ratio
         assertion dropped for that op only. 0.2 ms -> 1.1 ms is timer-floor
         noise; a ratio on it is noise wearing a threshold's clothing. Fixed now
         rather than waiting for it to flap.
       * ungroup: kept xfail(strict=False) -> P3.8 deliberately, NOT promoted.
         ungroup_selected calls coalesce_all on release, which is O(walls^2) by
         construction, so ungroup is genuinely super-linear. The sub-8 at n=8 is
         incidental (item 2 cut the boundingRect constant) and reasserts at
         larger n. Promoting would encode "ungroup is fine" -- false; only "less
         bad at n=8". P3.8's topology ops replace coalesce_all.

P0.7  done
ruff:    clean
pytest:  304 passed, 4 xfailed, 1 xpassed; pytest -m io = 38 passed (corpus)
files:   floorplanner/design/ (new pkg: __init__.py, validate.py, and the
         schema moved in via git mv from docs/); tools/validate_design.py (now a
         thin CLI over the package); tests/test_schema.py (new); requirements-
         dev.txt (+jsonschema); .github/workflows/ci.yml (+corpus-validate step);
         pyproject.toml (packages += floorplanner.design; package-data += the
         schema); docs/design-schema.v5.md (pointer); path refs updated in
         CLAUDE.md, DESIGN_MODEL_v5.md, SANITY_CHECK.md, and this plan's header
         + P0.0 block.
notes:   check(doc)->list[str] ported VERBATIM (pure Python, no third-party
         import) so it is safe to call from the app; JSON-Schema validation is a
         separate schema_errors() that LAZY-imports jsonschema -- a dev/test dep
         (requirements-dev.txt), never shipped, so importing floorplanner.design
         never requires it. Corpus results: symmetricP1 + site_demo schema PASS /
         invariants PASS; planc1.v5 schema PASS but 23 invariant errors incl I6
         -- test_corrupt_fixture_passes_schema_but_fails_I6 pins that (the "does
         not launder its input" guard). test_corpus_discovered guards against a
         rename silently emptying the parametrized corpus.
         The schema MOVED (git mv, not copied) into the package as packaged data;
         docs/ keeps design-schema.v5.md as the pointer. The CLI now defaults its
         schema to the packaged one and inserts the repo root on sys.path so it
         runs from any cwd (the package is not pip-installed; tests reach it via
         conftest). Ran only P0.7 as specified -- the actions/checkout@v5 +
         setup-python@v6 bump is deliberately held for a standalone commit at the
         top of Phase 1 (changing the CI environment is a different risk class
         from adding a step, and CI runs once per push).

GATE 1  manual sanity check — PASSED (user-run, 2026-07-26)
scope:   Phase 0 complete, format unchanged, CI green py3.10 + py3.13
result:  regression sweep clean; five P0.5 fixes verified; known regression
         (party-wall room via rubber-band) confirmed as expected; selection
         responsiveness confirmed improved.
meaning: the Phase 0 safety net is validated three ways — 304-test suite, CI on
         two Python versions, and a human using the application. Phase 1 may
         proceed. Next manual gate is Gate 2, after P2.2.

CI-bump  done   (commit 58590a2, pushed alone)
         actions/checkout@v5 + setup-python@v6. Shipped alone at the top of
         Phase 1; CI green on py3.10 + py3.13, Node-20 deprecation warning gone.

P1.1  done
ruff:    clean
pytest:  308 passed, 4 xfailed, 1 xpassed (+4 from test_design_model.py)
files:   floorplanner/design/model.py (new); floorplanner/design/__init__.py
         (+model exports); tests/test_design_model.py (new).
notes:   Qt-free dataclasses (Level, Vertex, Wall, Opening, Room, OutlineEdge,
         Furnishing, Group, Provenance, Design) over the v5 schema. from_dict/
         to_dict driven by a per-class FIELDS table; sub-structures the schema
         gives no object type (settings, anchor, placement, label, properties,
         pos, provenance fields) ride as RAW values.
         BYTE-IDENTICAL round-trip verified for symmetricP1.json AND site_demo.json
         -- both dict== and json.dumps== (not just the required symmetricP1). The
         crux is a _MISSING sentinel via d.get(k, _MISSING): a present-with-null
         field (free wall left: null) is kept null; an absent field (a room with
         no area_accounting) stays absent, never emitted as null. A dedicated test
         pins that distinction.
         WHY _MISSING IS LOAD-BEARING BEYOND P1.1: P2.1's "a v5 file never opens
         dirty" promise rests ENTIRELY on Design.from_dict(x).to_dict() == x. Had
         the model normalised absent -> null, every v5 file would round-trip
         structurally different from what was written and open dirty on every
         load -- and that bug would surface in Phase 2, months after the real
         cause. So this fidelity is a P2.1 dependency, not a P1.1 nicety.
         ZERO Qt: model.py imports only the stdlib. test_model_imports_zero_qt
         execs the file in ISOLATION (bypassing floorplanner/__init__, which star-
         imports the Qt scene layer) and asserts no PyQt6 module was pulled in --
         so it catches a stray Qt or floorplanner import, not just a direct one.
         No behaviour, no callers yet (the scene<->design bridge is P1.4/P1.5).
         Not pushed -- Phase 1 pushes at its end (or on the v5-topology branch for
         Phase 3), per the push policy.

P1.2  done
ruff:    clean
pytest:  312 passed, 4 xfailed, 1 xpassed
files:   floorplanner/design/validate.py (deep split + docstring); tests/
         test_schema.py (deep-gating + two negative tests); tests/
         test_design_model.py (planc1.v5.json added to the round-trip set).
notes:   COUNT CORRECTED (my error, was propagating): 15 named checks, not 14 --
         I1-I14 plus I5b. Split: deep-only 3 = I5b, I11, I14 (the O(n^2) ones);
         always-on 12 = I1 I2 I3 I4 I5 I6 I7 I8 I9 I10 I12 I13. Verified on the
         corpus: planc1.v5 trips I11 (deep) + I6 (always-on); deep=False drops
         I11 but still reports I6.
         DEFAULT = deep=True, and this FLIPS the "cheap by default" wording in my
         earlier P1.2 amendment (a894221) -- called out here because a changed
         decision is a red flag too. Rationale: forgetting deep=False on the hot
         path is a loud slowdown; forgetting deep=True on load/import is SILENT
         corruption (exactly where I11/I14 matter most). Loud failure wins. The
         per-command path (P1.6 --verify-design) opts out with deep=False; the
         CLI and corpus tests keep the default and validate fully -- no caller
         change needed.
         Negative tests each FAIL the check (not just not-crash): I14 fires on a
         welded corner split into two vertices 0.3" apart AND does not fire under
         deep=False (proves the gate); I6 fires on a wall side that disagrees with
         the room outlines.
         Also (riding with P1.2): planc1.v5.json added to the P1.1 round-trip --
         byte-identical, exercising wall: null open edges + a provenance block
         (three fixtures now). And recorded that _MISSING is a P2.1 dependency
         (see the P1.1 entry above) with a matching line added to P2.1's
         acceptance -- "opening a v5 file must not dirty it".

P1.3  done
ruff:    clean
pytest:  323 passed, 4 xfailed, 1 xpassed (+11 from test_topology.py)
files:   floorplanner/design/topology.py (new), floorplanner/design/legacy.py
         (new), floorplanner/design/__init__.py (+exports), tests/
         test_topology.py (new).
notes:   BOTH concrete acceptances hit exactly: trace_faces on symmetricP1
         recovers 19 room areas; weld_endpoints on legacy planc1.json welds 31.
         Per the three structural notes:
         (1) Ported to Design, not dicts: topology functions take and return
         P1.1 dataclasses; adjacency/pos are built from design.walls/vertices.
         (2) The one-shot legacy path is SEPARATE: weld_endpoints lives in
         design/legacy.py, on raw p1/p2 wall dicts (it runs at v1-v4 import,
         before a Design exists). Its lifetime ends when files are converted;
         split_edge/merge_collinear/trace_faces are forever. Not peers, so not
         in the same module.
         (3) Winding pinned by its own test: left = the (dy,-dx) side, verified
         79/79 walls-with-left on symmetricP1 (you said 61/61 -- the convention
         holds 100%, the count is 79). A second test ties trace_faces' winding
         to the stored `left`: the (dy,-dx) probe of a shared wall lands in a
         face whose area is the left room's. Without this, a flipped winding
         swaps every left/right and I6 still passes.
         The 19-vs-20: trace_faces returns 20 inner faces; exactly 19 match a
         stored room area. The sole unmatched room is the Garage (largest,
         boundary-touching) -- its face IS the outer boundary that _inner_faces
         drops. A test asserts unmatched == {Garage}, not just the count.
         Forward-looking ops (split_edge, merge_collinear, planarize) are pure
         Design->Design and tested for the invariant that matters -- they
         preserve trace_faces (rooms unchanged); planarize is idempotent on the
         already-planar corpus. DEFERRED with a note in the code: opening
         redistribution across a split, and crossing-point insertion, land at
         P3.3/P3.4 where the wall-move split rule is built -- split_edge leaves
         openings on the first segment for now.
         Zero Qt: model.py proven by isolated exec (P1.1); topology.py and
         legacy.py asserted Qt-free at the source level (no PyQt import; their
         only floorplanner imports are floorplanner.design.*), since importing
         them via the package would pull Qt through floorplanner/__init__.
         Not pushed -- Phase 1 pushes at its end.

P1.3-followup  done   (responding to the two P1.3 flags)
ruff:    clean
pytest:  324 passed, 4 xfailed, 1 xpassed (+1: split_edge raises-on-openings)
files:   design/topology.py (split_edge guard), design/legacy.py (docstring),
         tests/test_topology.py (raises test), docs/CODE_REVIEW_v2.md (defect 18),
         docs/V5_MIGRATION_PLAN.md (P1.4 acceptance amended).
notes:   FLAG 1 (landmine) fixed: split_edge no longer leaves openings on the
         first segment -- it RAISES NotImplementedError naming P3.3 on any wall
         carrying openings. P3.3 removes the guard as it builds redistribution.
         pytest.raises(match="P3.3") pins it. Same principle as deep=True: the
         failure mode is loud, at the call site, not a rendering oddity three
         tasks later.
         FLAG 2 (probe the unmatched face): I checked, and it is TWO findings,
         not the benign "no" branch.
         - The unmatched 60.6 sf face's centroid is inside NO room (Garage
           included) -- a genuinely unclaimed wall-bounded region in symmetricP1.
           Not an M-Bath-class outline/wall disagreement; a corpus observation.
         - Digging further: the Garage (868.5 sf) IS a valid raw traced face
           (9 edges) -- it is not unenclosed. _inner_faces DROPS it because its
           "drop the largest inner face as the outer boundary" heuristic is
           unsound: the true outer boundary (4535 sf) is opposite-wound and
           already excluded by the majority-sign filter, so inner[1:] discards
           the biggest ROOM. The migrator masks this (per-room enclosing_face
           recovers the room); standalone trace_faces loses it. Logged as
           DEFECT 18 -> P3.5 (identify the boundary by winding, not area).
         So the P1.3 "19 not 20" is really: Garage wrongly dropped by the
         heuristic + a separate 60.6 unclaimed region. The unmatched=={Garage}
         test still holds and still cannot pass for the wrong reason.
         Also corrected legacy.py's docstring: it is PRE-VERTEX geometry (raw
         p1/p2), used by BOTH the v4 importer (P2.1) AND design_from_scene (P1.4,
         scene still p1/p2 until P3.1) -- not purely import-only. Retired at P3.1.

P1.3b  done   (defect 18 fix + corpus diff, before P1.4)
ruff:    clean
pytest:  324 passed, 4 xfailed, 1 xpassed
files:   design/topology.py + tools/migrate_to_design_v5.py (_inner_faces /
         inner_faces fix), tests/test_topology.py (test updated to the fixed
         behaviour), docs/CODE_REVIEW_v2.md (defect 18 -> fixed), this plan
         (P1.3 acceptance 19->20).
notes:   FIX: _inner_faces now keeps the majority winding and drops ALL
         opposite-wound faces (one outer boundary per connected component --
         a detached garage or a Phase-4 floating room each has its own), never
         by size. Retargeted defect 18 P3.5 -> P1.3b and fixed NOW: P2.1's
         import traces outlines, so the old heuristic would have silently fallen
         back to stored corners for the largest room of every imported plan --
         user-facing, four tasks out. Fixed in BOTH topology.py and the migrator.
         Result: trace_faces on symmetricP1 now recovers all 20 rooms (Garage
         included), plus one extra face for the 60.6 sf unclaimed region.
         CORPUS DIFF (the required check): regenerated symmetricP1 with the fixed
         migrator (migrate(planc1.json, --clean --name "Symmetric P1"), the
         command that produced the committed file) and diffed. Result: GEOMETRY
         IDENTICAL -- Garage 868.5 sf both ways, same 9 edges, same cycle; the
         only file change is the Garage outline's start vertex rotating (the
         migrator now TRACES the Garage, rooms_traced 19->20, instead of the
         stored-corners fallback). So the Garage's stored outline AGREES with
         its traced face -- NOT an M-Bath-class disagreement. Per the decision
         tree that is the "identical" branch: the fixture STANDS, not
         regenerated (a cosmetic loop-rotation is not worth churning a fixture
         that P1.1/P1.4/P1.5/P1.6 pin). Had they disagreed, that would have been
         a corruption baked in by luck (the buggy fallback) -- they don't.

F5-correction  done   (doc-only commit e613b5d, taken BEFORE the P1.4 code)
ruff:    n/a (doc only)
pytest:  n/a
files:   docs/CODE_REVIEW_v2.md (F5 rewritten + a correction note),
         docs/DESIGN_MODEL_v5.md (section 6 sentence; a note at the head of 7a)
notes:   F5 and section 6 both said the editor welds "on every draw release and
         on load". The "on load" half is FALSE: apply_project_to_scene
         (mainwindow.py:1298) runs coalesce_all + rebuild_all_walls and no
         weld_all. Welds happen only at draw release (view.py:489) and via
         Edit > Coalesce all walls now (mainwindow.py:821).
         Corrected mechanism, verified in the source: coalesce is itself a gap
         SOURCE -- _coalesce_wall_impl (walls.py:200-201) re-snaps the survivor's
         p1/p2 onto the 6" on-centre grid independently of whatever neighbour an
         end was welded to, so it can pull a previously-welded end off its
         partner. Gaps are created and accumulated by the app's own pipeline and
         survive every round-trip, rather than merely failing to persist a weld
         the app already performed.
         CONSEQUENCE FOR P2.1, recorded in 7a: weld-on-load is NEW, deliberate
         repair behaviour the app has never applied to a user's file -- not
         persistence of something it already did. That strengthens the
         conversion report and the dirty flag rather than weakening them.

P1.4  done   (commit c78cb5e)
ruff:    clean
pytest:  337 passed, 4 xfailed, 1 xpassed in 10.16s (+13 from
         test_design_bridge.py; 324 -> 337, no other count moved)
files:   floorplanner/design/bridge.py (new), floorplanner/design/legacy.py
         (+VertexTable, +split_params -- PURELY ADDITIVE, weld_endpoints is
         byte-identical), floorplanner/design/__init__.py (docstring only),
         tests/test_design_bridge.py (new, 13 tests)
notes:   NO EXISTING TEST TOUCHED -- `git status` showed two modified source
         files and two new files, nothing else.
         The three notes, as built:
         (a) LEVEL-SCOPED BY CONSTRUCTION, not by filter. _by_floor() buckets the
         scene once; each level's walk receives ONLY its bucket, and the vertex
         table, wall graph and room polygons are per level. There is no global
         query left to forget to filter -- defect 12 closes structurally.
         test_walk_is_level_scoped builds two GEOMETRICALLY IDENTICAL rooms on
         two floors (coincident coordinates are precisely what a leaking walk
         would fuse) and asserts the levels share no vertex.
         (b) Outlines from RoomItem.corners, never trace_faces.
         (c) legacy.py grew the two pre-vertex helpers the walk needs:
         VertexTable (weld-on-insert at WELD_TOL 0.6") and split_params (cut at
         junctions + every room corner, so one wall spans one outline edge).
         THE WELD DECISION, resolved explicitly before any code: weld_endpoints
         is a CHECK, never an edit. It runs on a deepcopy to count what it WOULD
         move; the emitted geometry is always the scene's own. Non-zero ->
         report["unwelded_ends"] + a warning, and strict=True raises (the P1.6
         --verify-design hook). Rationale: silently welding would have made
         P2.2's Save move a user's walls up to 9", and would have made P1.6's
         shadow comparison diverge from the scene it shadows. Only the 0.6"
         weld-on-insert runs for real, and at that tolerance two points ARE one
         vertex -- representation, not repair.
         ACCEPTANCE: room areas match project_from_scene() EXACTLY (not merely
         within 0.1 sf) on planc1.json, sample_plan.json and fixture scenes.
         sample_plan walks fully clean: check(deep=True) == [], 0 unwelded ends,
         0 open edges, and schema_errors() == [] too. planc1 reports 17x I6 +
         1x I11 -- asserted as measured, per the acceptance, not forced to [].
         Same fault classes as its v5 fixture (I6 + I11), as predicted.
         FINDING 1 -- the 31 is a count of ATTEMPTS, not of damage. My checker
         reports 5 unwelded ends on planc1, not 31. Cross-checked: weld_endpoints
         returns 31 on the FILE geometry and 31 on the SCENE geometry -- identical,
         so the scene->raw-walls extraction is faithful and load's coalesce
         changed nothing here (46 walls in, 46 out). The 31/5 gap is the counting
         method: 31 counts weld OPERATIONS, and 26 of them are no-ops on
         junctions that are already exact. Measured displacements: 4 ends move
         1.529" (the documented divider gaps, y 655.529 -> 654.0) and 1 moves
         0.001" (float noise). So "31 wall ends were welded" in section 6 and in
         7a's user-facing conversion message overstates the geometry actually
         changed by ~6x. The P1.3 acceptance pinning 31 is still correct (it
         pins the function's return) and its test is untouched -- but 7a's
         message to the user should probably say "4 wall ends moved", not "31
         welded". FLAGGING, not editing: that is user-facing copy.
         FINDING 2 -- the SCENE's planc1 corruption is worse than the FILE's.
         On disk Hall and M Bath differ (243.5 sf / 18 corners vs 591.6 sf /
         24 corners). Load re-detects rooms, the 1.5" gap leaks the flood-fill,
         and BOTH label anchors resolve to the same merged region: they come out
         as the SAME 21-vertex loop at 243.5 sf each. I11 is firing on an exact
         coincidence, not a partial overlap. The test asserts the shared vertex
         set, so it cannot pass for the wrong reason. P2.1's repair has to fix
         a worse input than the file suggests.
         THREE CALLS the task text did not specify (all endorsed before coding):
         bridge.py is the home, and is deliberately NOT re-exported from
         design/__init__.py so model/topology/legacy/validate stay importable
         without the Qt scene layer; groups emit [] (defect 3 -- a grouped wall
         has no single id here, it splits into segments; emitting a guess would
         make characterization test 3 pass for the wrong reason, and both close
         at P4.5); settings.area_basis is "centerline", NOT the migrator's
         "inside_face", because the scene's areas ARE centreline areas and
         declaring the better basis would itself be a repair.
         Not pushed -- Phase 1 pushes at its end, per the push policy.

P1.4-followup  done   (doc-only; responding to the two P1.4 findings)
ruff:    n/a (doc only)
pytest:  n/a
files:   docs/DESIGN_MODEL_v5.md (7a message + the two-counter rule),
         docs/V5_MIGRATION_PLAN.md (P2.1 task text; this entry)
notes:   FINDING 1 SETTLED -- two counters, with the threshold taken from the
         document's own semantics rather than picked: the schema defines
         vertex_weld_in = 0.6" as the distance at which two coordinates ARE one
         vertex, so a displacement at or below it is not a geometry change BY
         DEFINITION. weld_ops = operations performed (31); ends_moved =
         displacement > 0.6" (4). Only ends_moved is ever shown to a user or
         written to provenance.endpoints_welded -- whose schema description
         already reads "Wall ends MOVED onto a neighbour", so the corrected
         reading is what the schema always meant and the fixture's stored 31
         contradicts its own field. 7a's example message now reads "4 wall ends
         moved to close gaps (31 junctions checked)".
         symmetricP1.json's provenance is NOT regenerated now -- deliberately.
         P1.1/P1.4/P1.5/P1.6 all pin that fixture; regenerating mid-phase is
         churn for a semantics fix P2.1 implements properly. Folded into P2.1's
         task text instead.
         FINDING 2 MADE BINDING -- P2.1's task text now REQUIRES the importer to
         derive outlines from the welded FILE geometry, never from the scene's
         re-detection, and cites the measurement: loading planc1 collapses Hall
         and M Bath into one identical 21-vertex region (both 243.5 sf, same
         vertex set), where the file keeps them distinct (243.5/18 corners vs
         591.6/24 corners). The scene's belief about a corrupt file is STRICTLY
         WORSE than the file. test_planc1_reports_its_real_faults pins the shared
         vertex set and is named in the plan as the guard.

P1.5  done   (commit 2678ff5)
ruff:    clean
pytest:  347 passed, 4 xfailed, 1 xpassed in 12.27s (+10; 337 -> 347)
files:   floorplanner/design/bridge.py (+apply_design_to_scene, +_canonicalize,
         +geometric ordering in the walk), tests/test_design_bridge.py (+10)
notes:   NO EXISTING TEST TOUCHED -- git status showed exactly two modified
         files, both mine. Existing IO and undo tests green unchanged.
         ACCEPTANCE MET on sample_plan.json AND planc1.json: scene -> Design ->
         scene -> Design is dict-identical at the second Design. planc1 is in
         the round-trip set deliberately -- a corrupt plan must round-trip as
         faithfully as a clean one; had apply quietly repaired the Hall/M Bath
         collision the second Design would be "better" and the bridge would be
         lying about what it holds.
         THE FINDING THAT SHAPED THE TASK -- ids were not canonical. The first
         round trip came back ISOMORPHIC BUT UNEQUAL: identical counts
         (8/8 vertices, 10/10 walls, 3/3 rooms on sample_plan; 61/80/20 on
         planc1) with different ids. Cause: P1.4 minted ids in EMISSION order,
         which is source-wall order, but apply turns each split segment into its
         own WallItem, so the second walk visits the same geometry in a
         different order. Fixed with _canonicalize: vertices sorted by
         (level, x, y), walls by (level, v1 pos, v2 pos, type), rooms by
         (level, name, centroid), furnishings by (level, pos, kind, rotation),
         openings renumbered along the wall -- then ids assigned and every
         reference rewritten. The walk's per-level item lists are sorted
         geometrically too, so the vertex-table weld order is deterministic.
         This is the same z-independence Project.to_dict already gives the v4
         snapshot (model.py:211-224) and for the same stated reason; P2.3's undo
         comparison needs it as well. A test pins it directly: bring a wall to
         the front, re-walk, document unchanged.
         The four mirror notes, as built:
         (1) NO coalesce/weld/detection in apply. Pinned by an OFF-GRID plan
         (205x101 at (7,3), no corner on the 6" wall-snap grid): a coalesce pass
         would re-snap the endpoints and the test asserts the exact
         coordinates survive.
         (2) Rooms READ, never re-detected. Ordering does the work --
         rebuild_all_walls runs BEFORE any RoomItem exists, so refresh_rooms
         returns at `if not rooms: return` and no flood-fill can overwrite a
         stored outline. Each room's _detect_sig is then primed via the public
         room_signature(scene, room) so a LATER rebuild also leaves it alone;
         the test asserts d1 == d2 across an explicit rebuild_all_walls.
         (3) Openings invert exactly. _opening_s is the algebraic inverse of the
         s -> anchor conversion, and the test compares openings wall-by-wall
         across planc1's 20+ openings (with a guard that the corpus has not
         silently got weaker), not just a count.
         (4) floor assigned from the level explicitly on every wall, room and
         furnishing. The test sets active_floor to the WRONG floor before
         applying, so anything trusting the active_floor() global lands
         visibly wrong.
         TWO SMALL CALLS: apply collapses the scene's anchor + label_offset into
         the anchor (v5 stores ONE label offset, relative to the centroid --
         the schema's stated intent), which round-trips exactly; and
         keep_backdrop / reference-image retention is deliberately NOT handled
         here, it belongs with the undo-restore path at P2.3.
         Opening failures are COLLECTED and surfaced (report["openings_failed"]
         + warning, strict=True raises), not dropped by the v4 path's silent
         `except ValueError: continue` -- pre-figures P3.6.
         Not pushed -- Phase 1 pushes at its end, after P1.6.

P1.6  done
ruff:    clean
pytest:  OFF  364 passed, 4 xfailed, 1 xpassed in 11.84s
         ON   364 passed, 4 xfailed, 1 xpassed in 12.50s   <- THE ACCEPTANCE
         DEEP 360 passed, 3 xfailed, 6 deselected in 11.23s  (-m "not perf")
files:   floorplanner/design/verify.py (new), floorplanner/mainwindow.py (3
         hooks + import), floorplanner/app.py (--verify-design -> env var),
         floorplanner/design/bridge.py (rebase at the end of apply),
         tests/conftest.py (fixture rebase + teardown verify),
         tests/test_verify_design.py (new, 17), .github/workflows/ci.yml
         (second suite run with the flag on), docs/CODE_REVIEW_v2.md (defect 19)
TEST CHANGED (declaring it, per the working agreement): tests/test_rooms.py
         `_overlapping_rooms` gained a `rebase(win)` call. NO assertion changed
         -- it declares that the helper's overlapping rooms are the deliberate
         INPUT to room_boolean, the same "this state is accepted" mechanism a
         corrupt legacy file uses at load. See finding 2.
notes:   Hooks at quiescent points only, never scene.changed (mid-operation the
         scene is legitimately inconsistent): _commit_if_changed before the
         snapshot (cheap twelve), save (deep), load (deep + REBASE), and the
         conftest fixture teardown -- that last one because the 180 ms dirty
         timer NEVER FIRES HEADLESS, so without it the suite would verify
         almost nothing.
         FINDING 1 -- unwelded_ends must NOT raise, and this contradicts the
         spec I was given ("same treatment as an invariant class"). Two
         independent reasons, both measured:
         (a) THE SCHEMA FORBIDS IT. join_tol_in is documented as "GESTURE
         TOLERANCE ... Never an invariant: a wall deliberately stopping 6"
         short of another is a legitimate design (a reveal, a pilaster gap),
         and nothing may silently close it." Raising would fail a user for
         drawing a reveal.
         (b) IT IS NOT A DOCUMENT PROPERTY. apply_design_to_scene rebuilds
         planc1 from a BYTE-IDENTICAL Design and the count goes 5 -> 15,
         because Design walls are edge-granular and a wall split at its
         junctions has more ends to be near things with. A metric that moves
         while the document is provably unchanged cannot be a document
         invariant. Resolution: REPORT_ONLY -- carried in the profile, warned
         once when it rises, never raised on. The real weld invariant is I14 at
         the 0.6" modelling tolerance, and that stays in the raising set.
         A test pins REPORT_ONLY's contents so adding to it can't silently
         disarm an invariant.
         FINDING 2 -- one I11 fired, and it is NOT a defect. Under the deep
         sweep, test_rooms::test_room_op_needs_two_rooms tripped "I11 two placed
         rooms overlap". Diagnosed rather than suppressed: the overlap is built
         by the `_overlapping_rooms` helper as the deliberate input to
         room_boolean, and the operation under test is a no-op by design, so
         nothing INTRODUCED it. Declared with a rebase in the helper.
         FINDING 3 -- defect 19, a real one. extract_from_reference writes
         detected walls into the scene and commits with no weld pass; per the
         corrected F5 nothing welds them later either. Every extracted plan is
         born with open junctions -- the exact condition that leaks room
         detection between spaces. Measured: 2 unwelded ends on the test_extract
         fixture. Logged -> P2.1. Note it is NOT caught by the gate (it is an
         unwelded_ends rise, which is report-only per finding 1), so it needs
         fixing on purpose.
         ON THE INVARIANT SCORE, honestly: ZERO invariant classes fired from
         app operations. Given this migration's hit rate I did not expect that,
         so I checked rather than celebrated -- which is what FP_VERIFY_DESIGN=
         deep is for. It promotes every quiescent point to all fifteen, so the
         sweep covers I5b/I11/I14 (the two that caught the real planc1
         corruption) across the whole suite, not just at save/load. Result after
         findings 2 and 3: still zero. Two honest caveats on that number -- the
         suite's scenes are small and mostly clean, and deep mode cannot run
         over the 64-room perf grid (O(rooms^2) + O(walls^2) per quiescent point
         is exactly what P1.2 split the invariants to avoid), so `-m "not perf"`.
         The acceptance run is the cheap twelve, as specced; deep is a
         diagnostic.
         CI now runs the suite TWICE per Python version, the second with
         FP_VERIFY_DESIGN=1. --verify-design on the CLI just sets the env var,
         so there is one switch however it is thrown.
         PHASE 1 COMPLETE. Ready to push (P1.1..P1.6 + the doc commits).

PHASE 1 PUSHED  (58590a2..52bd72e, 14 commits) -- CI GREEN on py3.10 + py3.13.
         Doubled suite: "Run tests" 14s / 15s, "Run tests with --verify-design"
         14s / 15s -- a clean doubling of the pytest step and nothing else
         (job total ~45s -> ~60s; the ~30s apt/pip setup is now amortised over
         two runs). NO cross-Python divergence with the flag on, which was a
         real risk worth measuring: P1.5's canonical sort keys are raw floats
         off QPointF, so a tie-break difference would have renumbered the
         document and broken the round-trip on one Python only. It did not.

P2.1  done   (commit ad62e66)
ruff:    clean
pytest:  OFF  377 passed, 4 xfailed, 1 xpassed in 12.51s
         ON   377 passed, 4 xfailed, 1 xpassed in 13.61s
         DEEP 373 passed, 3 xfailed, 6 deselected in 12.51s  (-m "not perf")
files:   floorplanner/design/importer.py (new), design/legacy.py
         (+weld_endpoints_counted), floorplanner/mainwindow.py (open_document,
         load_data split, _finish_open, defect 19), tools/migrate_to_design_v5.py
         (now a thin CLI), tests/test_load_path.py (new, 13),
         examples/symmetricP1.json + planc1.v5.json (surgical, see below)
notes:   NO EXISTING TEST TOUCHED.
         ACCEPTANCE HIT EXACTLY: planc1 opens at M Bath 182.0 sf / Hall 61.5 sf,
         provenance.endpoints_welded = 4, dirty; symmetricP1 opens clean and NOT
         dirty; the legacy file on disk is byte-identical afterwards (asserted).
         check(deep=True) on the converted document = 0 errors.
         FINDING 1 -- `load_data` was OVERLOADED, and migrating in it would have
         broken undo. It is the undo-restore path (mainwindow.py:896) AND a
         plain "apply this dict" helper used by a dozen round-trip tests. Had
         P2.1's migration gone there, EVERY UNDO would weld the geometry and
         re-trace every room -- a repair, not a restore, and silent. Split:
         `load_data` applies faithfully and never migrates (it now also accepts
         a v5 dict, routing to apply_design_to_scene); `open_document` is the
         file-open path that migrates, dirties and reports. load_path/open_plan
         call the latter. A test pins it with a divider stopping 1.5" short --
         geometry a weld WOULD move -- and asserts the gap survives an undo.
         The plan's task text says "Load path" as if it were one thing; it is
         two, and only one of them may repair.
         FINDING 2 -- a regression I introduced and caught: `active_floor` is
         VIEW state that the v4 FILE carries but the v5 Design deliberately does
         not (keeping it out is what stops a floor switch dirtying the
         document). Routing v4 opens through the importer silently forgot which
         floor the user was editing; test_floors::test_serialize_round_trip_two_
         floors caught it. Carried across by hand in open_document.
         FIXTURES: SURGICAL EDIT, NOT REGENERATION -- and the measurement is the
         reason. Regenerating symmetricP1.json produces TWENTY deltas: the two
         named (provenance.endpoints_welded 31->4, settings.area_basis
         inside_face->centerline) plus EIGHTEEN in rooms[5] -- the Garage
         outline's start vertex rotating, which is exactly the change P1.3b
         examined and deliberately declined to bake in ("the fixture STANDS,
         not regenerated"). A full regeneration would have silently reversed
         that decision. So the two fields were edited in place and the diff
         verified line-by-line: 3 changed lines across both fixtures, nothing
         else.
         THIRD FIXTURE DELTA, DECLARED: examples/planc1.v5.json also moves
         area_basis inside_face -> centerline. Not named in the brief, but it is
         the direct consequence of the approved importer decision, and leaving
         the corrupt fixture on inside_face would make the corpus disagree with
         the tool for no reason. Its corruption (I6 + I11) is untouched.
         FAITHFUL MODE PRESERVED. The importer keeps `clean=False`: it is what
         generates planc1.v5.json, the "does not launder its input" fixture from
         P0.7. Dropping it to serve only the load path would have orphaned that
         fixture. The CLI keeps naming ITSELF in provenance.tool, so
         symmetricP1's tool field did not move either.
         PROVENANCE IS RETAINED on the window (`_provenance`) rather than
         discarded after apply -- P2.2 needs it to write the audit trail into
         the saved file, and a v5 file that arrives with one keeps it.
         DEFECT 19 in-app arm closed: extract_from_reference now welds the walls
         it injects. Test asserts unwelded_ends == 0 after an extraction; it was
         2 before.
         CONCEPT-ROOM FIXTURE built as asked, because planc1 no longer exercises
         that path -- the weld closes its 1.5" gap, so M Bath and Hall now get a
         face each. The fixture is a single 20'x8' enclosure with TWO room
         labels and a chair in each half (the shape v4 produces because it never
         serialised open/archway edges). Pins: both rooms survive, the contest
         loser is category=concept + floating + extracted_from set, its outline
         edges are all wall:null, it is sized AROUND the furnishing it carried
         (asserted, not just counted), and check(deep=True) == [].
         FLAG for routing -- TWO THRESHOLDS FOR ONE IDEA. P1.6's bridge counts
         `unwelded_ends` at >1e-9 (reports 5 on planc1); this task's importer
         counts `ends_moved` at >0.6" (reports 4). Same underlying question,
         two numbers, which is the exact trap the 31-vs-4 episode was about. The
         0.6" floor is the principled one (it is the schema's own definition of
         "one vertex"). Aligning the bridge would change two P1.4/P1.6 test
         assertions, so I have NOT done it unasked -- flagging instead.

weld-floor  done   (commit e2a97b3; authorized follow-up to the P2.1 flag)
ruff:    clean
pytest:  377 passed, 4 xfailed, 1 xpassed (both flag OFF and ON)
files:   design/bridge.py (_weld_delta -> WELD_TOL), tests/test_design_bridge.py
notes:   One question, one floor. The bridge's telemetry counted movement above
         1e-9; the importer's ends_moved counts above 0.6". Now both use 0.6",
         the schema's own definition of "one vertex". The two NAMES stay
         distinct -- unwelded_ends is telemetry, ends_moved is a user report.
         ASSERTION CHANGED (authorized): test_weld_is_a_check_not_an_edit,
         planc1 unwelded_ends 5 -> 4. The dropped fifth is a 0.001" float nudge;
         the four real 1.5" divider gaps are unaffected, which is the point of a
         floor this small. The extract fixture stays at 0 (defect 19's weld at
         P2.1 already closed its 2 gaps, and they were far above 0.6" -- a floor
         this small does not launder a real gap). test_apply_design_rebases
         unaffected.
         ALSO CONFIRMED, in answer to the P2.1 report's omission: defect 19's
         in-app arm DID land at P2.1 (commit ad62e66) -- weld_all in
         extract_from_reference at mainwindow.py:1730 plus
         test_extracted_walls_are_welded. Only my summary dropped it; the
         register ticks correctly.

P2.2  done   (commit 6a7e5d4)
ruff:    clean
pytest:  OFF  386 passed, 4 xfailed, 1 xpassed in 13.35s
         ON   386 passed, 4 xfailed, 1 xpassed in 14.99s
         DEEP 382 passed, 3 xfailed, 6 deselected in 14.02s  (-m "not perf")
files:   floorplanner/design/canonical.py (new), design/bridge.py, design/
         importer.py, floorplanner/mainwindow.py (design_document, v5 save,
         legacy export), fp_extract.py, tests/test_load_path.py (+9),
         tests/test_floors.py (the authorized assertion), examples/
         symmetricP1.json + planc1.v5.json (regenerated)
notes:   ACCEPTANCE: save -> reopen -> check(deep=True) == [] and NOT dirty;
         legacy export round-trips through the old loader (asserted by loading
         it into a second window via load_data, the v4 path, and comparing room
         areas). Also pinned: save -> reopen -> save is a FIXED POINT, and
         opening a file the project wrote reproduces it exactly.
         THE ROTATION QUESTION, ANSWERED WITH A TEST rather than an assumption.
         It does NOT bite on save-reopen: apply builds RoomItem.corners in
         document order and the walk reads them back in that order, so rotation
         is carried, not regenerated (measured: Garage starts at (900.0, 12.0)
         both ways). The rotation delta was an artefact of REGENERATING the
         fixture, not of the save cycle. Per the ruling it is now moot anyway --
         canonical form DEFINES rotation.
         CANONICAL FORM MADE TOTAL. canonicalize() moved to design/canonical.py
         (Qt-free, so the importer can call it; it lived in bridge.py, which
         imports Qt) and now normalises outline rotation as well as ids: each
         loop restarts at its lexicographically-least (x, y) corner, orientation
         UNTOUCHED -- winding carries meaning, so reversing a loop would swap
         every wall's sides. Two tests pin it: outlines start at their least
         corner and canonicalize is a fixed point; and rotating every outline in
         the input produces byte-identical canonical output.
         FIXTURES REGENERATED, every delta class measured and named:
           symmetricP1.json  52/62 vertex ids renumbered; 0/20 room ids and
                             0/50 furnishing ids moved; 7/20 loops rotated
           planc1.v5.json    56/65 vertex ids; 0/20 and 0/50; 20/20 rotated
           BOTH: walls-as-coordinate-pairs IDENTICAL, vertex coordinate set
           IDENTICAL, room polygons identical as sets -- NO GEOMETRY MOVED.
           provenance identical, settings identical (area_basis and name carry
           over). planc1.v5.json still fails 23 invariants (I6 + I11), so the
           "does not launder its input" guard holds.
         THREE DATA LOSSES FOUND BY MEASUREMENT, not by a test failing. The
         P2.2 probe compared open(symmetricP1) -> design_from_scene against the
         file: vertices/walls/furnishings identical, but
           * rooms differed on exactly ONE field -- the Garage's
             area_accounting: "unconditioned" -- because the scene has no home
             for it. Fixed generally: v5 room/wall fields the scene cannot model
             are stashed on the item at apply and re-emitted by the walk, so
             category/placement/holes/nominal_size/thickness_in/finish_* survive
             a load-save too, not just the one field that showed up.
           * settings.name ("Symmetric P1") evaporated -- only DEFAULT_SETTINGS
             keys reach the global SETTINGS. Retained on the window.
           * provenance was dropped entirely. Now re-attached on EVERY save.
         ASSERTION CHANGED (authorized in advance; the third of the migration,
         and all three were declared before the fact): test_floors::
         test_serialize_round_trip_two_floors -- the file's remembered active
         floor moved from the top level to settings.active_floor, because the
         v5 root is a closed schema and settings is the designated open bag.
         Still absent from serialize(), so a floor switch still cannot dirty.
         fp_extract.py now calls export_legacy_v4_path, not save_path.
         Converting that writer is P2.4's, with the gallery/examples/macro
         tokens; save_path going v5 would have converted it early and out of
         step. Its output is not stranded -- opening a v4 file converts and
         welds it, which is defect 19's file arm.
         THE STASH'S LIFETIME, accepted rather than engineered around (recorded
         at review, and now a comment in bridge.py): the stash lives ON THE ITEM,
         so it survives ordinary edits but DIES WITH THE ITEM. A wall carrying
         thickness_in that is coalesced away, or a room deleted and re-detected,
         silently loses its stash. Acceptable only because these fields have no
         editor yet; P4/P5 model them properly (placement/nominal_size at
         P4.2-P4.4, area_accounting and finishes at P5.1-P5.3) and the stash
         retires then. Written down so it is a known limit, not a mystery.
         Not pushed -- Phase 2 pushes at its end.

P2.3  done   (commit bbe592c)
ruff:    clean
pytest:  OFF  393 passed, 4 xfailed, 1 xpassed in 15.33s
         ON   393 passed, 4 xfailed, 1 xpassed in 17.30s
         DEEP 388 passed, 3 xfailed, 7 deselected in 15.19s  (-m "not perf")
files:   floorplanner/mainwindow.py (snapshot, restore, dirty, serialize
         demoted), design/bridge.py (keep_backdrop, OpenWall rebuild, door_type),
         design/verify.py (reuse a caller's walk), tests/test_undo.py (+6),
         tests/test_scaling.py (snapshot + undo timings), tests/
         test_characterization.py + tests/test_io.py (the two assertions below)
notes:   snapshot() = canonicalize(design_from_scene().to_dict()), and undo,
         redo and the dirty flag are all defined on it. _restore_state applies
         through apply_design_to_scene with keep_backdrop (the retention
         deferred from P1.5). _is_dirty canonicalizes BOTH sides.
         ONE WALK per settled edit: _commit_if_changed builds the snapshot and
         passes it to verify(doc=..., walk_report=...) rather than walking the
         scene twice at the same quiescent point -- which also makes the latency
         number below honest instead of inflated by my own duplication.
         serialize() DEMOTED to the legacy exporter, with a comment naming its
         sole remaining caller and the release it dies with.
         GROUPS DO NOT CLOSE HERE, per the corrected task text. The bridge emits
         groups: [] until P4.5, so undo keeps dissolving groups exactly as
         today; I did NOT write the group-survives test. What is asserted is the
         narrower promise: undo after grouping restores the plan.
         WHY EDGE-GRANULAR RESTORE IS SAFE -- the canonical Design is
         GRANULARITY-INVARIANT. Whether the scene holds one long wall or three
         segments split at junctions, design_from_scene planarises to the same
         canonical document, so scene wall-count is PRESENTATION state, not
         document state. Pinned directly by
         test_undo::test_snapshot_is_granularity_invariant, which builds the
         same plan two ways and asserts one document. Consequences: (a) a test
         asserting scene wall counts across an undo is asserting presentation;
         (b) if coalesce re-merges collinear segments after a later edit, the
         document, dirty flag and undo comparison correctly do not notice.
         TWO REAL BUGS, found only because the restore now goes through the v5
         bridge:
           * OPEN WALLS were dropped. The v4 loader regenerated them via
             bind_room_walls -- which is DETECTION, and apply must not run it --
             so nothing rebuilt them. Undo silently ate every archway edge. apply
             now builds an OpenWall per `wall: null` outline edge; P3.7 retires
             the branch when null edges render dashed directly.
           * a WINDOW's door_type was clobbered to "". v5 carries door_type for
             DOORS only ("meaningful only when kind == door"), so absent means
             "not applicable", not "empty"; applying now leaves the scene's
             default alone. Caught by test_group_move_undo_restores, which was
             comparing v4 dicts.
         ASSERTIONS CHANGED (2, both presentation-vs-document, authorized in
         advance): test_group_move_undo_restores now compares snapshot() rather
         than serialize() -- v4 reported perimeter_corners ROTATED after an undo
         (same polygon, different first element) because canonical form
         normalises rotation; the polygon itself is now asserted separately so a
         REAL geometry change still fails. And test_unchanged_scene_is_not_
         falsely_dirty sets its baseline with snapshot(), as a save does.
         LATENCY BASELINE for P6.1, P0.3 grid, 16 -> 64 rooms:
           snapshot  2.1 ms -> 10.8 ms   ratio 5.10
           undo     22.0 ms -> 155.8 ms  ratio 7.09
         Guarded with ABSOLUTE bounds (undo < 500 ms, snapshot < 100 ms), not
         ratios: undo sits close enough to the threshold of 8 that a ratio
         assertion would flap -- the same call P0.6 made for select_burst. P6.1
         must make this independent of plan size; today it is not.
         KNOWN REGRESSION recorded in the table: after the first undo, a wall
         crossing a junction comes back split (measured by hand: one 480" wall
         with a mid-span T returns as two 240" walls), so body-dragging it moves
         half and leaves the neighbour. Checked deliberately rather than left
         for a user to find. Restored at P3.3/P3.4.
         Not pushed -- Phase 2 pushes at its end.

P2.4  done   (commit c085b8a)
ruff:    clean
pytest:  OFF  400 passed, 4 xfailed, 1 xpassed in 16.20s
         ON   400 passed, 4 xfailed, 1 xpassed in 17.78s
         DEEP 395 passed, 3 xfailed, 7 deselected in 18.35s  (-m "not perf")
files:   fp_extract.py (save_path), examples/make_examples.py, examples/
         README.md, examples/sample_plan.v5.json (new), tests/
         test_corpus_freeze.py (new, 6), tests/test_extract.py + tests/
         test_schema.py (the two assertions), gallery + example PNGs
ACCEPTANCE: `python docs/make_gallery.py` and `python examples/make_examples.py`
         both run; gallery images regenerated. `python tests/bench_rooms.py`
         also re-run (6x6: rebuild 59.1 ms, memoized no-op 1.9 ms).
notes:   THE FREEZE IS THE TASK. examples/planc1.json (v3) and
         examples/sample_plan.json (v1) are NOT converted and never will be:
         planc1 is the corruption fixture AND the importer's acceptance input;
         sample_plan is the clean legacy input the bridge tests run against, and
         the ONLY v1 file in the repo, so it exercises a migration path nothing
         else does. Converting either leaves the importer with no real v1-v4
         document to prove itself against.
         Made MECHANICAL rather than remembered: tests/test_corpus_freeze.py
         pins both files' format AND version and asserts the legacy corpus never
         drops below two files. Its failure message says what to do instead --
         write the v5 rendering ALONGSIDE, the planc1.json / planc1.v5.json
         pairing that already existed here, which is now what make_examples does
         for sample_plan. examples/README.md documents the freeze in a table.
         Chose that pairing over moving the legacy corpus to tests/fixtures/:
         planc1.json is referenced by path throughout CODE_REVIEW_v2.md,
         DESIGN_MODEL_v5.md, this plan and the migrator's CLI docs, and it has
         to stay in examples/ regardless -- splitting the pair across two
         directories would be worse than keeping both.
         VERIFIED, NOT ASSUMED: make_gallery.py and bench_rooms.py needed no
         format work (both build their scenes programmatically, neither reads
         the corpus), and the macro open/save tokens were already v5 via
         load_path/save_path.
         MACRO MODAL PATH TESTED, not claimed. `open` on a legacy plan through
         the macro runner converts, COLLECTS the report on win._conversion,
         writes it to the status line and leaves the document dirty -- with no
         QMessageBox. A modal there hangs a macro or a test forever, so the
         coverage matters more than the assertion (the test HANGS rather than
         fails if one returns, which is itself the signal). The v5 half is
         pinned too: not converted, not reported, not dirty.
         ASSERTIONS CHANGED (2, both declared in advance):
           * test_fp_extract_cli_end_to_end -- output is floorplanner-design
             now. The wall COUNT is deliberately relaxed to >= 5: v5 walls are
             edge-granular, so 5 detected runs planarise to however many graph
             edges they span. result["counts"]["walls"] == 5 still pins what was
             DETECTED, which is what that test is actually about.
           * test_corpus_discovered -- the pinned set grew by sample_plan.v5.json.
             It joined the validated sweep automatically the moment it existed
             (discovery works), and validates clean: schema 0, invariants 0 deep.
         Not pushed -- Phase 2 pushes after P2.5.

P2.4-followup  done   (commit 33e457d)
ruff:    clean · pytest: 400 passed, 4 xfailed, 1 xpassed
notes:   The `>= 5` wall bound was the WRONG SHAPE of guard -- a lower bound
         passes if planarisation ever explodes, so a bug splitting 5 detected
         runs into 500 spurious segments would sail through. Measured and
         hard-coded: 5 detected runs -> 9 graph edges over 8 vertices for that
         fixture, both exact (the fixture is deterministic and edge-granular
         walls are document state in v5). EIGHTH declared assertion change.
         Took the optional hardening too: the macro-modal test's failure mode
         was a HANG (a modal exec() blocks forever headless), which in CI means
         the job runs to its timeout. _modal_failsafe schedules a single-shot
         timer that dismisses any modal and records it, so the test goes RED
         instead. Timers fire inside nested exec loops -- the same mechanism
         macro._modal_step uses to drive dialogs, opposite purpose.

P2.5  done   (commit d274d21)
ruff:    clean
pytest:  OFF  400 passed, 4 xfailed, 1 xpassed in 14.89s
         ON   400 passed, 4 xfailed, 1 xpassed in 16.98s
         DEEP 395 passed, 3 xfailed, 7 deselected in 14.79s
files:   floorplanner/planio.py, csvio.py, imageio.py, levels.py (all new),
         floorplanner/mainwindow.py, CLAUDE.md
ACCEPTANCE: suite green with ZERO TEST CHANGES -- `git status tests/` empty --
         all three ways. MainWindow 100 methods / 2179 lines -> 49 / 1173,
         under the review's ~55 target.
INVENTORY (methods / lines):
         mainwindow.py  MainWindow    49  1173   UI wiring + edit orchestration
         planio.py      PlanIOMixin   26   544   open/save/export + bridges
         levels.py      LevelsMixin   13   198   the floor roster
         csvio.py       CsvIOMixin     6   260   room CSV import/export
         imageio.py     ImageIOMixin   6   186   reference image + extraction
notes:   MIXINS, NOT DELEGATING WRAPPERS. The suite calls these directly --
         win.serialize(), win.snapshot(), win.load_data(), win._import_rooms(),
         win._is_dirty(), win.switch_floor() -- and a mixin resolves every one
         unchanged with zero delegation boilerplate. A delegate-per-method split
         would ALSO have left MainWindow at 100 methods, missing the point of
         the target. The split is internal structure, invisible at the API.
         MOVER'S DISCIPLINE VERIFIED MECHANICALLY, not asserted: a script
         ast.unparse()s every method before and after the split and diffs them.
         100 before, 100 after, 0 missing, 0 CHANGED. Nothing improved in
         flight.
         BOTH KNOWN HAZARDS CHECKED rather than assumed: SETTINGS is ONE shared
         object (id() compared across config/planio/csvio/imageio/levels/
         mainwindow -- all identical; no module re-binds it), and serialize()
         travelled with its guard comment intact.
         The 84 unused imports left by copying mainwindow's header into each
         module were removed by `ruff --fix`; star imports keep their noqa.
         CLAUDE.md's module layout updated -- it described a layout that no
         longer existed and would have misdirected the next reader.
         NOTED FOR LATER, NOT DONE (the itches, per mover's discipline):
           * `import_from_image` (55 lines) and `_import_rooms` (137 lines) are
             both long enough to want splitting; neither is in P2.5's scope.
           * `apply_project_to_scene` (109 lines) is the v4 loader and is on a
             deletion path once the legacy export retires -- do not invest.
           * `room_boolean` (97 lines) stayed in mainwindow.py deliberately: it
             is rewritten as a polygon op at P3.5, so moving it now would churn
             a file that task rewrites.
         PHASE 2 COMPLETE. Ready to push.

PHASE 2 PUSHED  (52bd72e..3c2fbcf, 13 commits) -- CI GREEN on py3.10 + py3.13.
         Doubled suite: 16s/18s on py3.13, 17s/20s on py3.10; job total 1m13s.
         Still a clean doubling, still no cross-Python divergence.

GATE 2  manual sanity check -- FINDING, fixed on main before branching
         (commit d665e06)
ruff:    clean
pytest:  OFF  403 passed, 4 xfailed, 1 xpassed in 15.78s
         ON   403 passed, 4 xfailed, 1 xpassed in 18.43s
         DEEP 398 passed, 3 xfailed, 7 deselected in 15.84s
files:   floorplanner/design/importer.py (weld_room_corners),
         tests/test_load_path.py (+3), examples/symmetricP1.json (regenerated)
THE FINDING: reopening the app's OWN legacy-v4 export of a converted plan
         reported "5 wall ends moved (5 junctions checked)". Expected 0 -- the
         app's own output must never need repair. NO EXISTING TEST TOUCHED.
DIAGNOSIS -- (a), but UPSTREAM of the export. The export was faithful and the
         report honest (weld_ops == ends_moved == 5, nothing conflated). The
         IMPORTER baked a pre-repair artefact into the repaired document:
           1. the weld pulls the four divider ends 655.529 -> 654.0 (the fix);
           2. split_params then cuts those same walls at the STORED room
              corners, which are PRE-WELD data and still say 655.529;
           3. that injects a degree-2 vertex 1.53" from the freshly welded end
              and a 1.53" SLIVER wall -- the exact ghost of the gap just closed.
         The tell was the DIRECTION: displacements ran from 654.0 OUT to 655.53,
         away from the repair, not toward it.
         WHY NOTHING CAUGHT IT: 1.53 clears MIN_SPAN (1.0) so the sliver
         survives, and clears vertex_weld_in (0.6) so I14 stays silent; all 20
         room areas were correct. It is invisible until the document is exported
         and reopened, where the 2" end-to-end gesture weld fuses the pair.
FIX:     weld_room_corners() snaps stored perimeter_corners onto the welded wall
         ends using the same END_TOL the wall weld uses -- they describe the
         same corners. 66 corners welded on planc1; reopen now reports 0/0.
         It also removes a SECOND, quieter error: stored corners are rounded to
         2dp by _sync_corner_props, so using them verbatim seeded the vertex
         table with up to 0.005" of drift. Six symmetricP1 vertices gain
         precision (104.42 -> 104.4228, 280.24 -> 280.2416, ...).
WHY IT ESCAPED, and the missing test: P2.2 round-tripped only via load_data --
         the FAITHFUL apply, which never welds -- so the export was never taken
         back through the CONVERTER. The two paths were each covered and their
         composition was not. test_legacy_export_reopens_without_repair now
         drives the full journey (open -> save v5 -> export v4 -> reopen
         converting) and asserts ends_moved == 0 with areas identical, plus a
         unit test for the corner weld and a guard that no sub-2" sliver
         survives a conversion.
FIXTURE: symmetricP1.json regenerated, every delta class measured:
           2 sliver vertices REMOVED (the bug) -> 82 walls to 80; Hall 9->7,
             Great Room 11->10, M Bath 11->10 outline edges
           6 vertices gain precision (2dp stored corner -> exact wall endpoint)
           47/62 vertex ids renumbered, 11/20 loops rotated (consequences)
           0 OF 20 ROOM AREAS CHANGED -- the geometry is preserved
           provenance and settings identical
         planc1.v5.json BYTE-IDENTICAL: faithful mode never welds, so it never
         had the artefact -- which is itself a check on the diagnosis.
         Acceptance unchanged: M Bath 182.0, Hall 61.5, 4 ends moved, check
         clean. Side effect worth noting: suite warnings dropped 17 -> 2,
         because converted scenes no longer carry unwelded ends.
LESSON, recorded in one line because it generalises: both paths were covered;
         their composition was not -- COVERED-PATHS != COVERED-COMPOSITIONS.
         Every future gate should ask which pairs of covered paths have never
         been run back-to-back.
result:  GATE 2 -- PASSED, one finding found and fixed (d665e06). Patrick's two
         trailing checks (original file untouched on disk, undo feel) ride as
         optional confirmations, not blockers.
meaning: Phase 2's acceptance is complete. P3.1 may proceed.

P3.1  done   (commit f0990d4, on branch v5-topology)
ruff:    clean
pytest:  OFF  415 passed, 4 xfailed, 1 xpassed in 16.69s
         ON   415 passed, 4 xfailed, 1 xpassed in 20.20s
         DEEP 410 passed, 3 xfailed, 7 deselected in 18.22s
files:   floorplanner/vertex.py (new), floorplanner/walls.py (read-through
         p1/p2 + v1/v2), floorplanner/design/verify.py (split logging),
         tests/test_vertices.py (new, 12)
ACCEPTANCE: suite green with NO TEST CHANGES -- `git status tests/` shows only
         the new file -- and the --verify-design run stays green.
notes:   A Vertex is a shared, identity-bearing point; two wall ends holding the
         SAME Vertex object are the same corner. No registry: the "table" is the
         set of vertices reachable from the walls, exactly as Design.vertices is.
         SPLIT-ON-WRITE, per the ruling. Assigning a moved position mints a
         fresh vertex and leaves any sharer put; a NO-OP assignment returns the
         same vertex, so identity and sharing survive the many places that
         re-set the same coordinates. Pinned by a test that shares a corner
         explicitly, moves one end, and asserts the other did not follow.
         SPLIT LOGGING: verify() records the per-operation delta in
         win._vertex_split_log. It LOGS rather than warns -- a drag legitimately
         splits, so a warning per drag would be noise, not signal.
         A PERFORMANCE REGRESSION I INTRODUCED AND FIXED, recorded because the
         HARNESS caught it and review would not have: the first version
         allocated a QPointF on every p1/p2 READ and a uid string on every
         write. p1/p2 are read on every rebuild, paint and hit-test, so rebuild
         slowed ~50% and bake nearly doubled -- test_bake flapped at 8.54
         against a threshold of 8. Fixed by storing the QPointF once and
         returning it SHARED, and minting uids lazily. Both are safe only
         because a vertex is never mutated in place: a move produces a NEW
         vertex, so a caller holding an old p1 still sees the old position --
         identical to the previous behaviour, where assignment rebound the
         attribute to a fresh QPointF. Verified before relying on it (nothing in
         the codebase mutates a p1/p2 in place; every access is .x()/.y()) and
         pinned by test_vertex_is_never_mutated_in_place. bake now 43.7 -> 297
         ms ratio 6.83 vs P2.3's recorded 40.8 -> 278.7 ratio 6.83 -- restored,
         not merely under the threshold. This is the second time P0.3's harness
         has paid for itself on a change that looked free.
         FINDING -- WHY P3.1 STOPS AT THE REPRESENTATION. design_from_scene
         still builds its own vertex table by welding COORDINATES at 0.6"; it
         does not yet consume the live uids. It cannot: nothing creates sharing
         yet, so today every coincident wall end is a DISTINCT vertex, and
         emitting live uids would put two vertices 0" apart in the document and
         trip I14 across the whole corpus. Consuming the live table therefore
         has to wait until weld/join create shared vertices explicitly, at
         P3.3/P3.4. That ordering is not a shortcut -- it is the same
         representation-then-behaviour discipline the split-on-write ruling
         encodes.
         COMPOSITION GATE (the Gate 2 lesson): round trips asserted through BOTH
         apply paths -- load_data (faithful) and open_document (converting,
         composed all the way out to a legacy export and back).

CI-ON-BRANCH  done   (draft PR #1)
notes:   Pushing v5-topology ran NO CI -- ci.yml triggers on push-to-main and
         pull_request only, so the whole geometry rewrite would have gone
         unvalidated until the merge: exactly the situation P0.3 called out.
         Fixed with a DRAFT PR (v5-topology -> main) rather than editing
         ci.yml's push list: the pull_request trigger then covers every push,
         and it costs no config change on main that we would later revert. The
         PR also gives a running diff of the phase and is the merge vehicle at
         P3.8. First run green: ruff, py3.10 and py3.13, both suite runs.

P3.2  done   (commit 77bc91a, branch v5-topology)
ruff:    clean
pytest:  OFF  428 passed, 4 xfailed, 1 xpassed in 16.69s
         ON   428 passed, 4 xfailed, 1 xpassed in 18.64s
         DEEP 423 passed, 3 xfailed, 7 deselected in 16.80s
files:   floorplanner/rooms.py (OutlineEdge, derived corners, mirror deleted,
         edge->wall in bind_room_walls, clipboard fix), floorplanner/planio.py
         (export re-derives, load strips), floorplanner/items.py +
         mainwindow.py (mirror call sites), tests/test_outline.py (new, 13),
         tests/test_groups.py (one deleted-method call)
ACCEPTANCE: room areas unchanged across the corpus (asserted on sample_plan and
         planc1 through the faithful apply, with the document identical after);
         _sync_corner_props and its six call sites deleted.
notes:   INTERIM REPRESENTATION, stated not implied: an outline edge holds a
         COORDINATE, not a vertex identity. P3.1's split-on-write world has no
         shared corner vertex to name -- at every corner each wall owns a
         distinct Vertex. Borrowing one wall's end picks arbitrarily between
         two (and two rooms meeting there could pick differently); minting a
         room-owned vertex adds a third object no wall references. Both encode
         an authority that does not exist yet; a coordinate states exactly what
         is known. THE TEST FOR CHOOSING AN INTERIM REPRESENTATION IS WHICH ONE
         DOES NOT LIE.
         Two guards pin the gap: outline corner and wall end have equal
         coordinates but are distinct objects, and a corner is still two
         distinct wall vertices. Both say in their docstrings that FAILING is
         the signal P3.4 closed the gap, not that something broke.
         The edge->wall mapping is the real content of the task -- before it a
         room had corners and an unordered walls list with no correspondence.
         SHIPPED POPULATED (bind_room_walls already computed it to place
         OpenWall placeholders), so the fallback rider does not apply and P3.4
         inherits nothing.
         THREE FATES, all three exercised by tests: the live mirror DELETED;
         the legacy v4 export KEPT byte-compatibly via
         RoomItem.export_properties() re-deriving at serialization time at the
         same 2dp rounding (the v4 loader needs it for OPEN rooms, whose
         detection fails); the importer reading legacy FILES untouched forever.
         Plus "ignored on load" -- read for the fallback, then stripped.
         AUDIT FINDING -- THE MIRROR WAS MASKING A LATENT BUG, and only the
         grep-everything instruction found it. _copy_spec carried
         dict(self.properties) -- including the SOURCE room's perimeter_corners
         -- into the clipboard; paste_room passed it to the new RoomItem, where
         _sync_corner_props overwrote it. Deleting the mirror naively would have
         shipped the source room's geometry into every pasted room, in a corner
         the suite does not reach. Fixed by keeping geometry out of the
         clipboard, with a test. All 20 tree-wide hits reconcile: 6 importer
         (4 live + 2 docstrings), 2 mirror body, 1 legacy-load fallback, 1
         bridge pop, 1 tool docstring, 8 tests, 1 schema (which FORBIDS the key,
         confirming the plan's parenthetical).
         The room-properties dialog and the inventory paths were checked too:
         the dialog updates an explicit key list, inventory reads include_sqft
         only. Neither touches geometry.
         TEST CHANGED (1): tests/test_groups.py called room._sync_corner_props()
         directly -- a SEVENTH call site, in tests rather than production.
         Removed; a call to a deleted private method, not an assertion (the P0.2
         class). The change I PREDICTED to test_design_bridge's _project_areas
         did NOT materialise: because the export re-derives the key rather than
         dropping it, that helper reads it unchanged.

P3.3  done   (branch v5-topology)
ruff:    clean
pytest:  OFF  447 passed, 4 xfailed, 1 xpassed in 18.04s
         ON   447 passed, 4 xfailed, 1 xpassed in 19.61s
         DEEP 442 passed, 3 xfailed, 7 deselected in 17.69s
files:   floorplanner/vertex.py (relocated_to + call-site attribution),
         floorplanner/walls.py (_DragVertex, end_vertex/set_end_vertex,
         _is_continuation, _plan_vertex_moves, the drag rewritten),
         floorplanner/design/verify.py (SITE_LOG_ATTR),
         tests/test_wall_move.py (new, 19)
ACCEPTANCE: suite green with NO TEST CHANGES -- `git status tests/` shows only
         the new file, all three ways.
THE LOG ENTRY FOR THIS TASK WAS NOT ON DISK. The brief said the five settled
         points were in this Progress log; they were not, and 3d6d32e touched
         only two lines (defect 12a, and the P2.3 regression row). Reported
         rather than reconstructed, per the P0.6 rule. Two of the five WERE on
         disk and are quoted here: the same-level constraint (defect 12a,
         `_attached`) and `_collinear_run` at walls.py:888 gathering 2 of 2. The
         "72 splits" figure appears nowhere in the repo (a grep for it over
         docs/*.md is empty), so it is not quoted; the measured figure for this
         task's scenario is below. The 0.6" tolerance was verified in the CODE
         (walls.py, `QLineF(q, rp).length() < 0.6`), which matches
         vertex_weld_in / WELD_TOL -- the schema's own definition of one vertex,
         and now named SHARE_TOL rather than repeated as a literal.
THE HEADLINE NUMBER, measured both ways on the same 4x4 grid: 12 wall drags
         caused 148 SPLIT-ON-WRITES before this task and 2 after. The two that
         remain are the branches deliberately NOT promoted (see below), so the
         drag path is converted, not merely quieter.
(1) PROMOTION. The 0.6" scan used to discover coincident ends and then push each
         one by hand on every mouse event, which is split-on-write: the corner
         came apart and was rebuilt from coordinates 60 times a second. Now the
         scan runs ONCE at press and REBINDS those ends to one Vertex object
         (`set_end_vertex`), and the drag moves the vertex (`relocated_to`) --
         so a neighbour follows because it IS the corner. Asserted with `is`,
         never `==`: equal coordinates are exactly what the old code already
         produced and would not distinguish the two worlds.
         `relocated_to` CARRIES THE UID. A moved corner is the same corner, so
         renaming it would be wrong on its own terms and would also break P4.5,
         which serializes groups by member id. It is not counted as a split,
         because it is not one -- otherwise P3.3's own conversion would show up
         in the very telemetry that exists to find the call sites still needing
         it. A test pins that the count does not move across a drag.
         SAME LEVEL ONLY (defect 12a, now closed). Filtered at the LOOP HEAD, so
         cross-level sharing is impossible by construction. Note the filter
         covers the whole scan, not just the promotion: leaving the tee branch
         unfiltered would have left half of defect 12a alive for no benefit, and
         the transient cross-floor mis-drag is a real bug too. Declared because
         it is one line wider than "promotion is same-level".
(2) THE SPLIT RULE, and what it is really a rule about: what must NOT be shared.
         A wall collinear with the slide that continues past an endpoint cannot
         ride the corner -- the slide is perpendicular, so moving the shared end
         would swing its far end and SHEAR it. So the continuation is split off
         FIRST (its own vertex, and it stays put), before any sharing is made.
         Verified in both directions rather than asserted: with P3.3 reverted,
         test_a_collinear_continuation_is_never_sheared FAILS with the
         continuation's end at y=12 instead of y=0 -- it really was being
         dragged and sheared, so this is a behaviour FIX, not just a
         representation change.
         THE FIRST EARNED BEHAVIOUR CHANGE OF PHASE 3, and the label is the
         standard rather than a flourish. Phase 3's contract is that P3.1 and
         P3.2 are compat shims -- representation moves, behaviour does not, and
         "suite green with no test changes" is the receipt. A behaviour change
         inside that contract has to earn its place, which means all three of:
         DECLARED in advance (the split rule was in the task text), TESTED IN
         BOTH DIRECTIONS (it fails on reverted code, at a named coordinate, so
         the bug is exhibited and not merely described), and BRACKETED BY A
         MEASUREMENT (148 -> 2 splits over the same 12 drags, so the size of
         the change is known and not guessed). A behaviour change with fewer
         than three is a regression that has not been noticed yet.
         The rule also has to BREAK sharing that already exists, not merely
         decline to create it (a corner welded by an earlier operation is
         exactly what P3.4's weld produces). Own test.
(3) DETECTION STAYS AUTHORITATIVE. Nothing here reads outlines off vertices;
         room areas after a drag are what refresh_rooms arrives at, and the
         scene test asserts that. P3.5 flips it.
(4) CALL-SITE ATTRIBUTION, and the data it immediately produced. P3.1's counter
         said an operation splits; it could not say WHERE, and "which call sites
         should become real vertex moves" is a question about lines. `_blame()`
         walks past this module and past the p1/p2 setters -- blaming the
         setters would put every split on two lines and answer nothing.
         MEASURED, over coalesce + weld + group + bake + ungroup + 12 drags = 82
         splits:
             40  items.py:703 in bake()
             40  items.py:704 in bake()
              2  walls.py     in mouseMoveEvent()
         So 80 of 82 are GroupItem.bake, on two adjacent lines, and that is
         P4.5's ("groups move the real items -- no duplicate_wall"). The 2 are
         the tee and grouped branches this task deliberately left on the
         coordinate path. The drag's own corner moves contribute ZERO.
         TWO LOGS, not a wider tuple: SPLIT_LOG_ATTR keeps its (operation,
         splits) shape and SITE_LOG_ATTR carries the blame, so the P3.1 reader
         (and its test) is not broken to add data it did not ask for.
         COST measured, per the P3.1 lesson: 622 ns per split for the
         sys._getframe walk. Never on a READ -- reads are the hot path P3.1 had
         to fix -- and at 82 splits per heavy session it is under noise. The
         harness confirms: bake ratio 6.57 / 6.90 / 7.78 over three runs
         (absolute 303-332 ms) against P3.1's recorded 6.83 / 297 ms. The 7.78
         sample is variance, not a regression -- checked by re-running rather
         than by assuming, because the first run alone looked like one.
A HAZARD FOUND WHILE REVIEWING MY OWN DIFF, and it is not a corner case:
         GROUPING DUPLICATES A ROOM'S WALLS ONTO THE ORIGINALS, so a grouped end
         coincident with a dragged wall is the COMMON case. Promoting it would
         wire a group member to an outside wall permanently, and what a group is
         topologically is P4.5's open question. Grouped neighbours therefore
         keep the OLD coordinate path (`kind == "rigid"`) -- they still follow
         the drag exactly as today, they just do not become topology. Same
         instinct as the `group() is None` gate that keeps grouped walls out of
         coalesce, applied one task before the semantics that need it.
COMPOSITION GATE (the standing additions): both apply paths after a real drag --
         load_data (faithful) and open_document (converting, composed out to a
         legacy v4 export and back, ends_moved == 0) -- plus a corpus test that
         presses EVERY wall of sample_plan and planc1 without dragging and
         asserts the whole document is unchanged and zero splits occurred. That
         last one is the new risk this task introduces and nothing else would
         catch: the press rewrites which vertex a neighbour points at, on every
         wall the user so much as clicks. Areas would survive a promotion that
         re-pointed an end at the WRONG corner; the document would not, so the
         document is what is asserted. Measured on planc1: 80 walls pressed,
         document byte-identical, 0 splits.
DEFERRED, DECLARED, NOT DONE -- and it needs a ruling. The plan's P3.3 task text
         has a second half of the split rule: "a vertex landing on another
         wall's body splits that wall." It is NOT among the five settled points
         (which specify the promotion, detection authority, attribution, the
         four tests, and the gate), and it is P3.4's shape of work: splitting a
         WallItem at a landing point is `split_edge` scene-side, in the same
         task that replaces coalesce/weld/fracture. Doing it here would
         duplicate that and would add an automatic wall-splitting side effect to
         every drag release -- a wide blast radius for something no acceptance
         test asks for. The tee branch is left on the coordinate path with a
         comment naming P3.4. Flagging rather than quietly widening or
         narrowing the task: say the word and it lands here instead.
DEMO PORT: `w24` no longer exists as that wall. The demo named it, but ids are
         canonical and the Gate 2 regeneration (82 walls -> 80, 47/62 vertex ids
         renumbered) moved every id in symmetricP1.json -- w24 is now a Master
         Suite / Rear Porch wall, and pre-Gate-2 it was Hall / Lounge. The
         BEHAVIOURAL pin holds exactly on today's fixture: the Lounge / Front
         Porch party wall (currently w18, 210" at y=864), +12 y, Lounge +17.5 sf
         and Front Porch -17.5 sf, TOTAL UNCHANGED to 0.0, check(deep=True) ==
         []. The test picks the wall by rooms and axis, never by id, so it fails
         for a regression rather than for a renumbering. A second test pins that
         the chosen wall really has no collinear continuation -- the demo's own
         precondition -- so the first cannot pass by luck.

P3.5  done   (branch v5-topology; five sub-commits)
ruff:    clean
pytest:  OFF  497 passed, 5 xfailed in 13.7s
         ON   497 passed, 5 xfailed in 16.0s
         DEEP 492 passed, 3 xfailed, 7 deselected in 15.4s
         (baseline in: P3.4's 491/4/1.)
THE XFAIL/XPASS DELTA -- ASKED TWICE, ANSWERED FROM DISK. Both ends were run
         in worktrees and the marker lists diffed, rather than reasoned about:

           c133205 (P3.5 in)   493 passed, 4 xfailed, 1 xpassed
           f738437 (P3.5 out)  497 passed, 5 xfailed

         THERE IS NO "+1 XFAIL". The marked set is BYTE-IDENTICAL at both ends
         -- the same five tests, same order, same reason strings:
           test_characterization::test_delete_wall_actually_removes_the_wall  P4.1
           test_characterization::test_group_survives_roundtrip               P4.5
           test_groups::test_extracted_room_region_follows_move               P4.2
           test_scaling::test_group_scales_subquadratically                   P3.8
           test_scaling::test_ungroup_scales_subquadratically                 P3.8
         P3.5 added no marker and retired none.

         THE VANISHED XPASS IS THE LAST OF THEM, `test_ungroup_scales_
         subquadratically` -- same test, same `xfail(strict=False)` marker,
         reporting XPASS at c133205 and XFAIL at f738437 because its ratio
         crossed the threshold of 8. MEASURED 7.85 / 8.29 / 8.54 / 8.82 on
         successive runs of one build: it straddles. Its ABSOLUTE improved
         sharply (300.7 ms -> ~106 ms at n=8, from the deleted re-detection),
         which is exactly why it now sits ON the threshold instead of well
         above it.
         >> WIDENED AT P3.6 FROM ONE TEST TO THE CLASS, by measurement. The
         P3.6 gate audit replayed OFF and ON at all 27 code-touching branch
         commits and found 8 red -- of which SEVEN are this, and not one of
         them is `test_ungroup` alone: `test_bake_scales_subquadratically` was
         caught red at 8.05 against a threshold of 8, and every one of the
         seven shows the tell -- exactly "1 failed", ALTERNATING between the
         OFF and ON runs of the same commit. Code that is broken fails both
         gates; a ratio that straddles fails whichever run the machine was
         busier during. So the row is not one flaky test, it is the P0.3b
         TIMING-RATIO CLASS, flapping at roughly 7 of 27 replays (~26%), and
         whatever P3.8 decides -- a wider threshold, best-of-N, or moving them
         out of the suite entirely -- applies to the class and not to one
         member. Members seen flapping so far: `test_ungroup_scales_
         subquadratically`, `test_bake_scales_subquadratically`,
         `test_rebuild_scales_subquadratically`.
         >> SIGHTING, P3.7 (2026-07-30): `test_ungroup_scales_subquadratically`
         XPASSED once in 8 ON runs -- that is what the P3.7 (2) gate trailer's
         "5 xfailed, 1 xpassed" was. Named by re-running with `-ra` rather than
         inferred, because the trailer reports counts and not names.
         >> FOURTH MEMBER, AND IT CHANGES THE STAKES (2026-07-30):
         `test_select_interactive_scales_subquadratically` FAILED **1 of 8 and
         2 of 8** across two ON sweeps. The first three members are
         `xfail(strict=False)` -- they flap in a column nobody reads. THIS ONE
         IS A HARD PASS, so it turns the GATE RED on a busy machine.
         CONSEQUENCE, and it is why the P3.8 decision stops being housekeeping:
         **as of today a red gate has two indistinguishable causes -- a
         regression or machine load -- separable only by READING WHICH TEST
         FAILED, which is precisely the manual step the gate exists to
         replace.** The decision is therefore a PRECONDITION for trusting any
         future gate, and the merge does not happen before it is made and
         applied class-wide.
         EXONERATION OF P3.7's PAINT ADDITION, measured not assumed: the same
         failure reproduces on the PRE-P3.7 tree in a worktree at `2c5fd8d`
         (ratio **9.71** against the threshold of 8), while the three runs after
         the paint addition read **4.10 / 2.22 / 4.00**. The flap is the class,
         not the change.
         >> RESOLVED AT P3.8 (2): the ratios are RECORDED, never asserted;
         every timing assertion is an ABSOLUTE bound at n=8; and the lane is
         out of the gate in all three modes (`tools/gate.py --perf` runs it
         explicitly). The wider-threshold option is RULED OUT by measurement,
         not preference -- the ratio's noise band reaches ~27 while the whole
         diagnostic range it exists to read is 4 (linear) to 16 (quadratic).
         Full reasoning in the P3.8 (2) entry.
         CONSTRAINT ON THE P3.8 DECISION, ruled 2026-07-30 and NOT negotiable:
         **no wall-clock ratio may remain a gate-reddening hard pass on a shared
         machine.** Wider thresholds, best-of-N, or a non-gating
         recorded-benchmark lane with one very loose catastrophic guard -- P3.8
         chooses from its own fresh numbers, but it chooses for the CLASS (all
         four members), not for one test.
commits: ac9ad45 (0) . 600fdef (1) . 02eff1e (2) . 733d7d6 (3) . f07dbdb (4)
         Logged sub-commit by sub-commit per the handoff-spec rule, so a
         successor reads the state from here plus the four riders at lines
         416-424 rather than from a chat summary.
(0) done   commit ac9ad45 -- doc-only, committed BEFORE any code per rider 2.
         THE RETARGET WAS ITSELF A FINDING: both P3.2 guards' docstrings named
         P3.4 as the task that would close the coordinates-vs-identity gap.
         P3.4 replaced the coalesce/weld/fracture ops and never touched
         outlines, so both stayed green straight through it -- they were
         addressed to the wrong task. Retargeted in tests/test_outline.py
         (module + both docstrings + both failure messages) and rooms.py's
         OutlineEdge note, and the second guard's message now names BOTH ways
         it can fire so a red says which.
(1) done   commit 600fdef -- the flip.
ruff:    clean
pytest:  OFF  493 passed, 4 xfailed, 1 xpassed in 18.4s
         ON   493 passed, 4 xfailed, 1 xpassed in 20.3s
         DEEP 488 passed, 3 xfailed, 7 deselected in 18.5s
files:   rooms.py (OutlineEdge holds a Vertex, `p` read-through;
         share_outline_vertices; the bind_room_walls hook), walls.py
         (_CornerIndex.vertex_at), vertex.py (defect 21),
         tests/test_outline.py (the two guards replaced + rider 1's test),
         tests/test_wall_move.py (+1, the defect-21 case)
THE GUARDS FLIPPED, AND ONLY THE GUARDS -- both P3.2 tests went red at this
         change and the whole rest of the suite stayed green through it. That
         is exactly what rider 2's sequencing was for: the red is the flip,
         not a weld that wandered in. Their two causes turned out to BE one
         cause: the weld is the flip's first step, because an outline can only
         NAME a vertex once the corner IS one vertex.
DEFECT 21 -- FOUND BY RIDER 1's OWN TEST, and it is the best kind of find.
         `relocated_to` copied `self._uid`, and uids mint LAZILY on first
         read, so a corner nobody had named carried None across a move and got
         a FRESH identity the moment anything asked. Invisible while only the
         document walk read uids -- which is how it survived P3.1, P3.3 and
         P3.4 -- and a live bug at P4.5, which serializes groups by member id.
         THE NEAR-MISS IS THE LESSON: P3.3's
         test_relocation_carries_the_vertex_identity has pinned this exact
         rule since P3.3 and PASSES FOR A REASON IT DOES NOT STATE -- it reads
         `v.uid` before relocating, which forces the mint. A test that
         establishes the precondition it means to test cannot see the bug.
         Fixed, and pinned by a test that constructs the unnamed case.
PERF, checked not assumed (the P3.1 lesson): test_bake flagged 8.83 against a
         threshold of 8 on the first full run. Re-ran three times -- 6.31 /
         6.89 / 7.17, absolutes 307-310 ms against P3.3's recorded 297-332 --
         so variance, not the new property read. Same call as P3.3's 7.78.
(2) done   commit 02eff1e -- the region derives from the outline.
ruff:    clean
pytest:  OFF  495 passed, 4 xfailed, 1 xpassed / ON same / DEEP 490, 3 xfailed
files:   rooms.py (path + area_sqft become properties; _translate relocates),
         walls.py (_DragVertex carries outline edges), items.py + mainwindow.py
         (three rigid-move sites go through set_region),
         tests/test_outline.py (+2)
THE STEP P3.2 AND (1) DID NOT TAKE, and without it the deletion is impossible
         rather than merely risky. `corners` derived from the outline at P3.2
         and the corners became real vertex identities at (1) -- but `path` and
         `area_sqft` were still a stored QPainterPath and a stored float that
         ONLY `refresh_rooms` refreshed. So an outline that moved by
         construction still reported a stale area until a detection pass caught
         up, and deleting that pass would have frozen every number a user reads.
         Both derive now, memoized on the corner COORDINATES -- not identity,
         because `relocated_to` returns a NEW vertex for a moved corner and an
         id-keyed memo would be stale in exactly the case that matters.
NO EXISTING TEST CHANGED.

(3) done   commit 733d7d6 -- the deletion, and the lift.
ruff:    clean
pytest:  OFF  495 passed, 5 xfailed / ON 495/4/1xpassed / DEEP 490, 3 xfailed
DELETED, 418 lines across 11 top-level definitions, all callerless:
         `_RoomGrid` (90) + `_WallGraph` (131) -- the two engines, a raster
         flood-fill and a hand-rolled planar face walk; `_detect_room` (12),
         `detect_room_region` (6), `trace_room_perimeter` (6); the memo,
         `room_signature` (23) + `refresh_rooms` (53) + `_room_probe_points`
         (19); `reloop_open_room` (48); `synthesize_room_edge` (15) and
         `_wall_along_segment` (15). Plus `bind_room_walls` 70 -> 38.
         rooms.py 1425 -> 1162 lines.
`detect_room` SURVIVES AS A NAME, and this is the census's one real divergence
         on the rooms.py side. The task line lists it among the dead; it has
         ~40 call sites across the app, the tooling, the fixtures and eleven
         test modules, and this task's authorized rewrite zone is two test
         files. Deleting the NAME would have been a rewrite of the suite
         wearing a deletion's clothes. What the line MEANS is delivered in
         full: the editor no longer has its own answer to "what is a face". It
         asks the document's, through `bridge.face_at` -> `enclosing_face`.
THE LIFT, and why it is allowed where P3.4 point 1 forbade it. That ruling
         rejected lift-to-Design for EDIT ops, on measurement: an edit runs per
         mouse event and a full-plan rebuild destroys item identity. "Detect
         room here" is a ONE-SHOT gesture -- the six call sites (csvio, macro,
         mainwindow x2, planio, view) each fire once per user action -- so the
         walk costs no more than the `_RoomGrid` + `_WallGraph` pair it
         replaces, both of which were also rebuilt per call and one of which
         was O(walls^2). Single-sourced instead of duplicated.
THREE THINGS CAME FREE, and they are why the swap is worth making rather than
         merely equivalent:
         * DEFECT 16 closes STRUCTURALLY. The grid was sized by `canvas_rect()`
           and any flood reaching its edge counted as unenclosed, so a plan
           larger than the canvas silently lost its edge rooms. A graph walk has
           no canvas in it. Closed by deletion, which is the only kind of fix
           that cannot regress. Pinned.
         * every returned edge NAMES the wall covering it, so `bind_room_walls`
           stopped SEARCHING for a room's own walls and now only attaches them.
           A room binds its outline as a fact the detection reports.
         * a wall split at a T yields one edge per SEGMENT -- invariant I5
           ("every outline edge maps to exactly one wall") holding by
           construction, where the old tracer dropped pass-through corners and
           could leave an edge no single wall covered.
DEFECT 13 -- REPRODUCED BEFORE THE SUBSTRATE WENT, which rider 3 asked for and
         which is the reason the verdict is worth anything. At zooms 0.25x-4x
         on the `detach_wall_from_room` path, measured on the code as it stood:
         * DETECTION was already IDENTICAL at every zoom -- same area, same
           corners, 5/5. It never read the view.
         * THE DRAG was not. The same scene-space gesture gave 0 open sides at
           0.25x and 1 at 0.5x-4x, leaving the wall's far end at y=120 vs y=60.
         So the defect is real and its mechanism is the drag's zoom terms
         (`20.0 / _view_scale()` catch radius, `16.0 / view_scale` stick),
         exactly as rider 3 predicted. Detection half CLOSED and now structural;
         drag half RETARGETED and left UNASSIGNED, the same disposition the P2.3
         row got, with P4.2 as the nearest task that touches the drag. NOT
         "repro substrate removed" -- the substrate was still there and the
         measurement was taken.
TWO CORRECTIONS THE LIFT NEEDED, both found by a failing test rather than by
         reasoning, and both are findings about `trace_faces` as much as about
         this task:
         * SPUR PRUNING. A dangling wall stub is IN the wall graph, so the face
           walk enters it and comes straight back out. Free for a FACE (the
           excursion encloses no area) and wrong for an OUTLINE: the room grows
           a corner at the stub's free end, and every consumer that asks "is
           this room inside the rubber band" answers from it. Caught by
           test_selection, which is not in the authorized zone and was right not
           to be changed. `bridge._prune_spurs`.
         * CANONICAL WINDING. `_inner_faces` picks the inner sign by MAJORITY,
           decisive from two rooms on but a TIE at exactly one -- a lone wall
           loop traces two faces of equal area and opposite winding. So a
           one-room plan came back wound whichever way the rest of the plan
           happened to vote, and the outline ORDER is serialized. Caught by
           test_room_walls' idempotent round-trip. Fixed at the one-shot entry
           to the sign the document already uses (positive shoelace, verified
           against every face of symmetricP1).
THE APPLY PATH NOW CARRIES THE DOCUMENT'S VERTEX IDENTITY, one live `Vertex`
         per document vertex, shared by every wall end and outline edge naming
         it. The first attempt reconstructed it by WELDING
         (`share_outline_vertices`) and `test_malformed_v5_is_reported_not_
         rewelded` caught it within the minute: apply must not repair, and a
         corner that has drifted 0.3" is a malformed file to be REPORTED, not
         quietly closed up. The document already knows the identities; reading
         them is exact where welding is a guess.

(4) done   commit f07dbdb -- defect 8, the predicates, the privatize ruling.
ruff:    clean
pytest:  OFF  497 passed, 5 xfailed / ON 497/5 / DEEP 492, 3 xfailed
DEFECT 8, and it was TWO faults with ONE cause -- `room_boolean` worked from a
         re-traced boundary rather than from what the rooms said they were made
         of. (a) It DELETED WALLS THAT WERE NOT ITS OWN: inputs came from
         `bounding_walls()`, a proximity query with no floor filter, and the op
         removes everything handed to it -- so a combine took the wall a third
         room shared with an input, breaking that room open, and any wall of any
         other FLOOR whose body touched the band. (b) It FORCED every result
         wall to "interior", downgrading 6" exterior walls to 4 1/2" ones.
         Both fixed at the source: inputs come from the room's OUTLINE
         (`room_walls`), a wall still bordering a non-input room is kept, and
         each result edge inherits type and floor from whichever input wall runs
         along it. TWO REGRESSION TESTS, both CONFIRMED FAILING against the old
         code before being kept -- and the first fixture was rebuilt on the
         shared-wall model, because two `make_room` calls leave a coincident
         PAIR at the boundary and a duplicate wall is a different problem.
THE TWO PREDICATES, rewritten and not deleted, exactly as rider 4 tabled.
         `room_owns_walls` and `walls_cover_room` keep their criteria and read
         the outline through a new `room_walls(room)` -- one answer to "which
         walls are this room's?" -- instead of the parallel bound-wall list the
         deleted binder maintained.
`_privatize_shared_walls` ASSESSED IN-TASK: KEEP. Its reason is untouched -- a
         party wall is one wall, so a room moving off it must stop owning it.
         It needed one repair to stay honest: it swapped the room's BOUND wall
         for a private copy and left the OUTLINE naming the shared one, and the
         outline is now the authority, so `room_walls` went on handing bake and
         room_boolean a wall the room had just given up.
         AND IT WORKS FOR A REASON WORTH WRITING DOWN: `_translate` RELOCATES
         corners, and a relocation mints a new `Vertex` that only the ends
         REBOUND to it follow -- so a wall the room no longer owns simply stays
         on the old corner, with nothing holding it back. P4.2's real `extract`
         still replaces the shape of it; `_perimeter_span` still falls with
         `fracture_delete_wall` at P4.1.
         [ANNOTATED at the P4.1 read-back, 2026-07-31 -- the last clause failed
         checking, the third task-line census figure to do so. `_perimeter_span`
         does NOT fall at P4.1: `_copy_spec` (rooms.py:335, unowned by any
         phase) and `_privatize_shared_walls` (rooms.py:785, P4.2's) both call
         it and both outlive `fracture_delete_wall`. Earliest death is P4.2,
         contingent on `_copy_spec` being reshaped there; the authoritative
         statement is the register's carried census note. The line above stands
         as written -- this corrects it in place without rewriting history.]

EXIT 1 -- MEASURED DELETION vs THE CENSUS. Rider 4 tabled ~470 from rooms.py
         + 34 from walls.py. MEASURED: 418 in whole definitions plus 32 from
         `bind_room_walls`' shrink = 450 of the ~470, and 0 from walls.py.
         Two divergences, both reported rather than forced:
         * `_wall_along_segment` (15) is REPLACED, not deleted, by `_edge_wall`
           (48) -- LARGER, because it absorbed the job the deleted three-priority
           search was doing: find the wall behind an outline edge that came from
           a FILE and names none. It also had to accept PARTIAL cover, or a v4
           reload stops agreeing with the live scene about a side whose corner
           was dragged away, and the round-trip stops being idempotent.
         * `_WallBBoxIndex` (34) CANNOT DIE, and P3.4 (iv) is why. That
           sub-commit reported it as P3.5's on the grounds that `refresh_rooms`
           was its last caller -- but the SAME sub-commit refused the adjacency
           swap in `_compute_wall_junctions` and said so at length: an unwelded
           crossing shares no corner, so bbox search is the only thing that can
           answer there. `_compute_wall_junctions` stays, so its index stays. A
           line dies when its LAST caller dies, and P3.4 (iv)'s own ruling
           created the caller that outlives this task.
EXIT 2 -- RIDER 1'S HEADLINE CHECK, PASSING, AND THE ASSERTIONS DID NOT MOVE.
         `test_a_dragged_wall_resizes_the_rooms_it_borders` -- the editor half
         of the Lounge / Front Porch demo -- still asserts equal and opposite
         resizing with the total unchanged, now with `refresh_rooms` DELETED.
         Written at P3.3 the numbers came from detection; they now arrive
         because the rooms' outlines hold the very vertices the divider holds.
         A `not hasattr(fp, "refresh_rooms")` guard makes the claim explicit
         rather than implied, so the test cannot quietly stop proving it.
EXIT 3 -- PERF, MEASURED NOT ASSUMED: the same harness on the same machine at
         c133205 (pre-P3.5) vs HEAD. P0.3 warned that `rebuild` at 2.7 was
         ALREADY sub-linear and that a regression there would be a real
         finding. It improved.
                        before (n=4 -> n=8)      after
           rebuild      1.2 -> 3.7   r 3.05     1.0 -> 2.4    r 2.31
           bake        44.8 -> 299.1 r 6.68     6.9 -> 28.0   r 4.03  <- 10.7x
           ungroup     45.9 -> 300.7 r 6.55    13.5 -> 106.1  r 7.85  <- 2.8x
           undo        21.3 -> 157.7 r 7.40    20.9 -> 123.5  r 5.92
           group       27.7 -> 360.1 r 12.99   33.3 -> 370.1  r 11.10 (P3.8's)
         `bake` is the headline and the mechanism is exactly the deletion: a
         group move ended in `rebuild_all_walls` -> `refresh_rooms`, which
         re-detected every room the move touched. Nothing re-detects now. The
         ungroup RATIO worsened while its absolute fell 2.8x -- it is
         xfail(strict=False) -> P3.8 either way, and P3.8 owns the reading.
EXIT 4 -- TOOLING. `python docs/make_gallery.py` and
         `python examples/make_examples.py` both run; images regenerated.
         `08-open-walls.png` legitimately changed and README's open-wall
         paragraph was corrected to match -- see the new Known-regressions row.

CHANGED-TEST LEDGER, one line each, since this is the second-biggest such risk
         in the plan after P3.4:
         * test_rooms.py [AUTHORIZED]: test_region_follows_wall_move rewritten
           -- coordinate assignment -> corner relocation, because a bare
           `w.p1 = ...` is SPLIT-ON-WRITE by P3.1's ruling, so the old test
           replaced wall ends and asked detection to notice. Three
           room_signature / refresh-memo tests DELETED with the memo they
           measured. +4: defect 13 (view-independence), defect 16 (no canvas
           clip), and the two defect-8 regressions.
         * test_room_walls.py [AUTHORIZED]: test_wall_stretch_keeps_binding
           rewritten, same one-line reason. +2 assertions in the privatize test.
         * test_open_walls.py [DIVERGENCE -- the whole file]: this is P3.7's
           rewrite arriving early, because P3.5 deletes the PRODUCER. An open
           side was an ITEM (a dashed `OpenWall`, regenerated by
           `reloop_open_room` + `bind_room_walls`); it is now a fact about the
           outline, reported by the new `RoomItem.open_edges()` -- which is
           where `bridge._rooms_of` has emitted it since P1.4. The scene was
           carrying a second, item-shaped representation of something the
           document already said. `test_open_wall_is_editable` DELETED: it
           asserted drag controls on a placeholder nothing constructs. The
           CLASS still dies at P3.7, as planned.
         * test_design_bridge.py + test_verify_design.py [OUTSIDE THE ZONE, and
           named as such]: planc1's I6 characterization 17 -> 13. planc1's four
           divider walls stop 1.5" short, so each is a dangling STUB; the old
           tracer carried those out-and-back excursions into the outline (which
           is how Hall and M Bath each held 21 corners, several at the free end
           of a wall nowhere near the room). Spur pruning drops them, so four
           walls only a spur ever touched stop being claimed. Same fault
           classes, same Hall/M Bath collapse, same areas -- all three verified.
         * test_wall_move.py: docstrings + the `refresh_rooms`-is-gone guard.
           The ASSERTIONS DID NOT MOVE; that is exit check 2.
         * test_outline.py: +3 (the region derives; the memo is keyed on
           coordinates; plus (1)'s pair).
PROCESS NOTE, since the working agreement is explicit about the mechanism: a
         `git checkout floorplanner/mainwindow.py`, used to undo a deliberate
         break-it-to-prove-the-test experiment, discarded that file's
         uncommitted work along with it. Reapplied and re-verified. The rule is
         written for handed-back DOC edits; it applies to uncommitted code just
         as literally, and the safe move is to make the experiment in a copy.
         RULED at the P3.5 close and now a working-agreement entry of its own
         ("Destructive experiments run in a worktree, or after a WIP commit"):
         the solution was already in use in this same task, since the perf
         comparison ran the old code in a `git worktree`. The followup below
         used exactly that to verify its new tests against pre-fix code.

DEFECT 28 -- RULINGS AT THE SESSION BOUNDARY (2026-07-29). Committed here
         before stopping, per the handoff-spec rule: a fresh session reads the
         state from this block and needs nothing from chat.

  1. TWO DEFECTS, NOT ONE. The leak has a test half and an app half and they
     are fixed separately.
       * THE FIXTURE LEAK -- `tests/conftest.py`'s `win` fixture ends with
         `w.close()`, which hides a window and neither destroys it nor stops
         its 180 ms dirty timer. Registered under DEFECT 28.
       * DEFECT 29 -- the APP half: `MainWindow.close()` leaves a timer running
         that walks the whole document. A user closing one plan window while
         another is open pays that cost invisibly, so this is a real behaviour
         defect and NOT to be slipped in under a test-isolation fix.

  2. LEAK GUARD AS ACCEPTANCE, WITH A FAIL-FIRST RECEIPT. The fix is accepted
     by a guard that asserts no stale `MainWindow` keeps an active dirty timer
     (equivalently: `live_mainwindows` stays bounded across the suite). The
     guard MUST be shown FAILING against the current tree before the fix
     lands -- the receipt standard, unchanged.

  3. THE CORPSE-TABLE STANDARD: NO BLANK ROWS. Every corpse is attributed to
     the test whose scene it actually holds, not the test that was running.
     A corpse with no owner is listed AS unowned rather than dropped.
     Currently unowned: **'Kitchen' / 'Pan' on symmetricP1** -- no test has yet
     been shown to leave that overlap, and until one is, defect 28 is NOT
     dissolved into "leaked windows misreport". `'A'`/`'B'` IS owned:
     `test_save_verifies_deep`'s own deliberate fixture, working as designed.

  4. RE-CERTIFICATION: DEEP GREEN 10/10 under the machine-written trailer
     (`tools/gate.py`). Not 1 clean run, not "it looks fixed" -- ten.

  5. THE HISTORICAL CLAIM IS BOUNDED. What is established: a leaked window CAN
     misreport an earlier test's state, and did, five times on two harvests.
     What is NOT established, and must not be asserted: that DEEP's green/red
     has been meaningless for its whole existence. The mechanism has existed as
     long as the timer has; the OBSERVED instances are all from P3.6, when the
     first tests loading a twenty-room plan into `win` arrived. Anything wider
     needs its own measurement.

  6. DEFECT 26's `E` SIGHTINGS, one line: they are the same mechanism -- a
     stale window's timer firing inside a later test -- so the four sightings
     and the "suppressing" interventions are all explained by it, and no
     separate cause is outstanding.

P3.8  done -- PERF VERIFICATION AND THE EXIT SURVEY. The last task of Phase 3.
ruff:    clean
pytest:  Gate-Census: collected=523 ruff=clean
         Gate-OFF: 510 passed, 7 deselected, 6 xfailed in 12.89s  -> sum 523  OK
         Gate-ON: 510 passed, 7 deselected, 6 xfailed in 15.55s   -> sum 523  OK
         Gate-DEEP: 510 passed, 7 deselected, 6 xfailed in 16.35s -> sum 523  OK
         Gate-Verdict: GREEN (every sum reconciles against --collect-only)
commits: 4997da2 (1 the numbers) . 7b6c342 (2 the flap decision) . 65c4c02 +
         90bad2d (defect 27's DEEP half) . 28e6a59 (3 the stranding row) .
         9bd52c3 (4-5 the survey completed) . plus this entry.

=== 1. THE NUMBERS, against BOTH baselines, same machine, medians of seven ===

                    PRE-PHASE-3 (b82256c)      HEAD              what it says
                    n=4 -> n=8    ratio        n=4 -> n=8  ratio
  rebuild           1.2 ->   3.3   2.82        1.0 ->  2.6  2.61   improved
  snapshot          2.1 ->  10.8   5.06        2.2 -> 10.8  4.80   flat
  undo             22.0 -> 154.0   6.99       19.1 ->126.2  6.64   -18%
  select_burst      0.2 ->   1.0   5.26        0.2 ->  1.0  5.48   flat
  select_interact   2.5 ->   7.6   3.19        2.4 ->  9.5  4.13   +25%, unattributed
  group            27.8 -> 349.7  12.77       29.3 ->356.4 12.43   untouched
  bake             41.0 -> 279.0   6.81        6.4 -> 26.4  4.09   **10.6x**
  ungroup          41.5 -> 292.5   6.89       11.5 -> 99.8  8.64   2.9x abs, ratio worse

  P0.3's reading rule: 4 is linear in rooms, 16 quadratic, 8 = rooms^1.5.
  `bake` is the headline and the mechanism is exactly P3.5's deletion: a group
  move used to end in `refresh_rooms` re-detecting every room it touched.
  `ungroup` is the honest half -- 2.9x faster absolutely while its ratio crosses
  the threshold; both true, and the row says both. `rebuild` answers P0.3's
  standing warning that a regression there would be a real finding: it improved.
  `group` is the one op Phase 3 never touched.

  0 NEW WALLS, ASSERTED (not observed): grouping the 20 rooms of symmetricP1
  together with their walls -- what Ctrl+A or a band actually selects -- leaves
  80 walls at 80 across group and bake. The rooms-ALONE reading of the same
  sentence is +868 walls and is P4.5's; it is pinned xfail, not reworded.

=== 2. THE FOUR SURVEY ROWS, and the theme they share ===

  * SPLIT-ON-WRITE: 9 -> 11 sites, because the P3.6 census grepped a shape that
    cannot see `setattr(wall, attr, ...)`. Five are correct as they are, two are
    lower-stakes identity churn (P4.5), FOUR are one defect with four faces.
  * STRANDING: ANSWERED BY A REAL DRAG -- it strands. Defect 30, filed not
    fixed. The endpoint drag is a separate and correct answer.
  * THE P2.3 COLLINEAR ROW: re-checked by hand, does not close, cause intact,
    unassigned -> P4.2.
  * DEFECT 13's DRAG HALF: dispositioned, not re-measured; it needs a ruling,
    not another number. Register row 13 stays authoritative.

  **THE THESIS P4.2 INHERITS, and it is one thesis rather than four errands:
  every one of these is an operation that knows about ROOMS where it should
  know about CORNERS.** Defect 30's gather, the four coordinate-assignment
  faces, and `_collinear_run()`'s short-circuit are the same mistake wearing
  four hats -- Phase 3 moved the geometry onto vertices, and these are the call
  sites that still ask a room what they should be asking a corner.

=== 3. THE FLAP DECISION, applied class-wide ===

  Ratios are RECORDED, never asserted; every timing assertion is an ABSOLUTE
  bound at n=8; the lane is out of the gate in all three modes and runs under
  `tools/gate.py --perf`. The wider-threshold option is ruled out BY
  MEASUREMENT: the ratio's noise band reaches ~27 while the whole diagnostic
  range it exists to read is 4 to 16. Receipt: 8 consecutive full-mode gate
  runs, 24 mode-runs, every one byte-identical, zero xpassed and zero failed --
  against 1-in-8 and 2-in-8 red before. It is this file's own precedent
  (`select_burst` P0.6, `undo` P2.3) finished rather than a new mechanism.

=== 4. CI NOW RUNS THE DEEP INVARIANTS ===

  https://github.com/pjm4github/FloorPlanner/actions/runs/30592873265
  Gate-DEEP: 510 passed, 7 deselected, 5 xfailed in 21.26s -> sum 522 OK
  The job calls `tools/gate.py --deep`, so CI and the local gate are ONE
  instrument. Its census was byte-identical to the local Windows run -- the
  branch's first cross-platform confirmation, and it landed on the two things
  most likely to differ: the deep invariant walk and the pixel assertions.

=== 5. THE MERGE CHECKLIST, hashes verified on disk ===

  | # | condition | state |
  |---|---|---|
  | 1 | P3.8's numbers recorded; 0 new walls asserted | DONE `4997da2` |
  | 2 | four survey rows answered or dispositioned | DONE `28e6a59`, `9bd52c3` |
  | 3 | flap decision made and applied class-wide | DONE `7b6c342` |
  | 4 | defect 27 DEEP CI job added and green | DONE `65c4c02`, `90bad2d` |
  | 5 | Gate 3 passed by Patrick, findings dispositioned | PENDING -- his |
  | 6 | CI green on branch head; MERGE COMMIT, not squash | CI green; merge waits on 5 |

P3.8 (5)  THE REMAINING TWO SURVEY ROWS, and the survey is complete.

THE P2.3 COLLINEAR-RUN ROW: RE-CHECKED BY HAND, DOES NOT CLOSE, cause intact.
         Built the row's own scenario -- a 480" wall with a mid-span T,
         bordering NO room -- and ran it:
           before undo   2 walls, spans [120, 480]
           after undo    3 walls, spans [120, 240, 240]
           the grabbed segment borders 0 rooms
           `_collinear_run()` gathers 1 of 2 collinear segments -- SHORT-CIRCUITED
           a 12" body drag moves 1 of 2 segments
         Every clause of the row is still literally true, and the fix it names
         still fits: gather the run over VERTEX ADJACENCY rather than
         short-circuiting to `[self]` when `self.rooms` is empty. Left
         UNASSIGNED with P4.2 as the nearest task that touches the drag --
         unchanged from P3.4 (iv), and now re-verified rather than assumed at
         the phase exit.
         NOTE THE COMPANY IT KEEPS: this is the same family as defect 30 and
         the four coordinate-assignment faces above -- an operation that knows
         about ROOMS where it should know about CORNERS. P4.2 inherits one
         theme, not four errands.

DEFECT 13's DRAG HALF: DISPOSITIONED, NOT RE-MEASURED, and that is deliberate.
         The merge condition is "answered by measurement OR explicitly
         dispositioned to a named task". This row was measured at P3.5 (0 open
         sides at 0.25x, 1 at 0.5x-4x; the wall's far end at y=120 vs y=60) and
         its cause named (the drag's `20.0 / _view_scale()` catch radius and
         `16.0 / view_scale` stick). Nothing since has touched those terms.
         Re-running it would re-derive a number the register already holds;
         what it needs is a RULING on whether a gesture tolerance may set a
         geometric RESULT, and that is P4.2's to make. Status stays
         authoritative in register row 13, per the pointer filed at P3.7.

P3.8 (4)  THE SPLIT-ON-WRITE EXIT SURVEY -- re-grepped, and the count went UP
         because the census method was wrong, not because the code got worse.

P3.6 RECORDED 9 SITES. THE TRUE FIGURE IS 11, and the two extra were never
         missing from the code -- they were invisible to the GREP. The census
         searched for `.p1 = ` / `.p2 = `, which cannot see an assignment made
         through `setattr(wall, attr, ...)`. P3.6's list did contain two setattr
         sites (the `rigid` and `tee` branches, found by reading rather than by
         the pattern), so the pattern had already failed once without being
         corrected. The survey now greps BOTH FORMS, and that is the finding to
         carry: a census is only as good as the shape it looks for.

THE ELEVEN, EACH WITH WHAT CARRIES THE THINGS ATTACHED TO THAT END:

  1-2  `mainwindow.py:571,572`  align-to-grid (`w.p1/p2 = grid_snap(...)`).
       CARRIES NOTHING -- it snaps each end independently, so a shared corner
       comes apart and any room outline on it is left behind. It is a
       user-invoked plan-wide normalisation, and the honest fix is the same one
       defect 30 names: move CORNERS, not coordinates. UNASSIGNED, argue P4.2.
  3-4  `mainwindow.py:581,582`  `_translate_shape`. Same shape, same answer,
       but lower stakes: it translates a whole selection by the same delta, so
       the geometry stays self-consistent even though identity is minted fresh.
       UNASSIGNED, argue P4.5 (it is the group/selection family).
  5    `view.py:402`  the rubber-band wall being DRAWN. Nothing is attached to
       an end that does not exist yet -- this is the one site where
       split-on-write is not merely safe but correct. KEEP, permanently.
  6-7  `walls.py:1563,1565`  the ENDPOINT drag. Split-on-write is the DESIGNED
       behaviour here (P3.1's ruling), and P3.7 made it visible: pulling a
       corner away opens that side and the room keeps its shape. KEEP.
  8    `walls.py:290`  `_adopt_end`, the merge applier's fallback. NEW TO THE
       CENSUS. Documented at P3.4 (i) and correct: it splits only when the plan
       named no corner, i.e. the end is landing where no corner was. KEEP.
  9    `walls.py:455`  `weld_scene`'s geometric snap. NEW TO THE CENSUS, and
       the interesting one: it closes a gap by MOVING a coordinate, then the
       topology half shares the ends. Assigning here is what the weld is for --
       but it means a room outline holding the old position is not carried.
       Not observed to bite (load does not weld, and the explicit command
       re-shares afterwards); RECORDED, argue P4.2 with defect 30, since it is
       the same "coordinate moved, holders not told" shape.
  10-11 `walls.py:1601,1603`  the `rigid` and `tee` branches of the body drag.
       Unchanged disposition: `rigid` is a grouped wall held back by the group
       guard -> P4.5; `tee` is a body-landing, which P3.4 (ii) gave a real
       vertex, so this branch is now reached only for landings the split
       declined (a straddling opening) -> P3.6's report path covers it.

SO THE SURVEY'S OWN QUESTION -- "what carries the things attached to that end"
         -- has three answers: FIVE sites are correct as they are (5, 6, 7, 8,
         and the tee half of 11), TWO are lower-stakes identity churn (3, 4),
         and FOUR are the same defect-30 shape at different call sites (1, 2, 9,
         and the rigid half of 11). That is the number worth carrying forward:
         **the coordinate-assignment family is no longer a list of survivors to
         chase, it is ONE defect with four faces.**

P3.8 (2)  THE FLAP-CLASS DECISION, made from the numbers and applied to the
         class. It is the merge checklist's item 3 and the precondition for
         trusting any later gate run.

THE DECISION IN ONE LINE: **the ratios are RECORDED, never asserted; every
         timing assertion is an ABSOLUTE bound at the large grid; and the
         timing lane is out of the gate in every mode.**

AND IT IS NOT A NEW MECHANISM -- IT IS THIS FILE'S OWN PRECEDENT, APPLIED TO
         THE CLASS. `tests/test_scaling.py` already converted two ops for
         exactly this reason and wrote the reason down at the time:
           * `select_burst`, P0.6 -- "the numbers here (0.2 ms -> 1.1 ms) sit
             at the perf_counter floor, so a ratio built on them is timer noise
             wearing a threshold's clothing. The absolute is the meaningful
             guard."
           * `undo`, P2.3 -- "An ABSOLUTE bound, not a ratio: a ratio assertion
             this close to the threshold would flap (the P0.6 precedent)."
         The flap class is precisely the ops that were never converted. So the
         ruling's "applied class-wide" is satisfied by finishing a job this file
         started twice and stopped halfway through.

WHY NOT A WIDER THRESHOLD -- the option the evidence RULES OUT rather than
         merely disfavours. Measured over 7 identical runs per tree:
           ratio spread, four big ops        1.06 .. 1.70x
           ratio spread, `select_interactive` at 2c5fd8d   **21.98x**
                                             (1.22 .. 26.82)
           ABSOLUTE spread at n=8, big ops   **1.03 .. 1.15x**
         The diagnosis: the n=4 leg is 0.2-4 ms, so a ratio divides one
         noise-dominated number by another and doubles its exposure. THE NOISE
         BAND (up to ~27) SWALLOWS THE ENTIRE DIAGNOSTIC RANGE THE RATIO EXISTS
         TO READ -- 4 is linear, 8 the threshold, 16 quadratic. A threshold
         cannot separate signal from noise when the noise is wider than the
         signal. Only a different measurement can, and the absolute is it.

WHY NOT BEST-OF-N: it would work -- a minimum is the right estimator when
         interference is one-sided -- but it costs N x the lane's runtime to
         buy back a number the absolute gives for free at 1.05x spread. It is
         recorded here as the option not taken, and it remains available if a
         later task needs the RATIO to be trustworthy rather than merely
         recorded.

WHAT CHANGED, five assertions and one tool:
         * `rebuild` / `select_interactive` / `group` / `bake` / `ungroup`:
           ratio assertion -> absolute bound at n=8, each with its measured
           median in the comment. `bake`'s bound (200 ms, median 26.4) is set
           so A RETURN TO THE PRE-PHASE-3 COST (279.0) TRIPS IT -- the one
           regression here that would matter most, and one the ratio would have
           called "still under 8".
         * THE TWO xfail MARKERS GO WITH THEM (`group`, `ungroup`). There is no
           ratio assertion left to expect-a-failure from, and a known-quadratic
           op's fact now lives in prose and the printed report instead of in a
           marker that flapped between xfail and xpass on machine load.
         * `tools/gate.py`: `-m "not perf"` in ALL THREE modes, not just DEEP.
           The lane could redden OFF and ON, and did. A side effect worth
           having: all three runs now reconcile against the SAME collected
           total, where DEEP alone used to report "7 deselected".
         * `tools/gate.py --perf` runs the lane explicitly and prints its
           numbers -- P0.3b's "invoked explicitly at the moments its numbers
           decide something", given a command instead of a memory.

WHAT THIS COSTS, said plainly: an absolute bound catches a BLOW-UP, not a
         DRIFT. A 20% regression will pass every bound here. That is the trade
         the evidence forces -- a ratio that cannot tell 4 from 27 was not
         catching drift either, it was reporting the machine's mood -- and
         drift is now caught where P0.3b always said it would be: by the
         numbers being read at the tasks whose decisions depend on them.

RECEIPT: 8 consecutive full-mode gate runs, all three modes each, after the
         change. See the sub-commit's trailer and the tally below.

P3.8 (1)  the numbers, measured SAME-MACHINE and as MEDIANS OF SEVEN.
ruff:    clean
pytest:  (trailer with the sub-commit)
THE METHOD IS THE FIRST FINDING. Every previous perf entry in this log is a
         SINGLE RUN, and the flap class says a single run of a ratio is not a
         measurement. So: 7 runs per tree, medians reported, spread reported
         beside them -- and the comparison tree is re-measured TODAY in a
         worktree rather than quoted from a table recorded weeks ago, because
         comparing today's HEAD against an old table conflates the code change
         with the machine.
         Anchor: `1a4d125^` = `b82256c`, the commit immediately before Phase 3
         opened.

                    PRE-PHASE-3 (b82256c)        HEAD (dedfc57)
                    n=4  -> n=8    ratio         n=4  -> n=8    ratio
  rebuild           1.2  ->   3.3   2.82         1.0  ->   2.6   2.61
  snapshot          2.1  ->  10.8   5.06         2.2  ->  10.8   4.80
  undo             22.0  -> 154.0   6.99        19.1  -> 126.2   6.64
  select_burst      0.2  ->   1.0   5.26         0.2  ->   1.0   5.48
  select_interact   2.5  ->   7.6   3.19         2.4  ->   9.5   4.13
  group            27.8  -> 349.7  12.77        29.3  -> 356.4  12.43
  bake             41.0  -> 279.0   6.81         6.4  ->  26.4   4.09
  ungroup          41.5  -> 292.5   6.89        11.5  ->  99.8   8.64

THE HEADLINE IS `bake`: 279.0 -> 26.4 ms at 64 rooms, **10.6x faster**, ratio
         6.81 -> 4.09. That is P3.5's deletion of the detection engine, paid
         out: a group move used to end in `refresh_rooms` re-detecting every
         room it touched, and nothing re-detects now.
`ungroup` IS THE HONEST HALF: 292.5 -> 99.8 ms, **2.9x faster absolutely**,
         while its RATIO WORSENS 6.89 -> 8.64 and crosses the threshold of 8.
         Both are true and the row must say both. It is `xfail(strict=False)`,
         so it xfails today where it used to pass -- exactly the reading P3.5
         predicted and left for this task.
`rebuild` ANSWERS P0.3's WARNING. P0.3 recorded 2.7 and warned that the
         memoized machinery was already sub-linear, so a regression here would
         be a real finding rather than noise. It improved: 2.82 -> 2.61, and
         3.3 -> 2.6 ms absolute.
`group` IS UNCHANGED (12.77 -> 12.43) and remains the one op Phase 3 did not
         touch. It is not wall duplication -- the harness groups walls AND
         rooms, which copies nothing (measured below).
`select_interactive` READS 25% SLOWER THAN PRE-PHASE-3 (7.6 -> 9.5 ms), AND
         THAT IS NOT P3.7's PAINT ADDITION -- measured against `2c5fd8d`, the
         commit immediately before it, with the same 7-run method: pre-paint
         10.3 ms / spread 21.98x, HEAD 9.5 ms / spread 1.49x. HEAD is faster
         and far steadier. The Phase-3-wide difference is real and unattributed;
         it is small, and the op is one of the flap class's four members.

AND THE SPREAD COLUMN IS THE FLAP CLASS'S EVIDENCE, gathered here because this
         is the task that has to decide about it. Same code, same machine,
         seven runs:
           rebuild            ratio spread 2.12x  (2.32 .. 4.91)
           select_interactive ratio spread 1.49x on HEAD -- but **21.98x** at
                              2c5fd8d (1.22 .. 26.82), where a `< 8` assertion
                              passes six times and fails once
           ungroup            1.12x on HEAD, 1.70x pre-paint
         THE DIAGNOSIS, and it points at the fix: the n=4 leg is 0.2-4 ms, so
         the RATIO is a quotient of two noise-dominated numbers. It is not that
         the code is unstable; it is that the instrument divides by a
         millisecond. Any decision that keeps ratio-of-small-durations as a
         gating assertion will keep flapping whatever threshold it picks.

THE 0-NEW-WALLS ACCEPTANCE IS AMBIGUOUS, AND MEASUREMENT SPLIT IT IN TWO --
         the P0.4 test-2 precedent, applied without being asked:
           * rooms AND their walls (Ctrl+A, or a band -- what a user's
             selection actually contains): 80 walls -> 80 after group -> 80
             after bake. **0 new walls, asserted** in
             `test_grouping_twenty_rooms_with_their_walls_creates_no_walls`.
           * the 20 ROOM items alone, which is what the sentence literally
             says: **+868 walls**. `duplicate_wall` copies a room's walls when
             the room is grouped without them, and P3.5's census assigned that
             to **P4.5**. Pinned as `xfail(strict=False)` naming P4.5 rather
             than asserted-and-failed or quietly reworded.
         AND THE DUPLICATION COMPOUNDS, which is new: grouping the 20 rooms one
         at a time sums to **258** new walls, all together **868** -- 3.4x more,
         because each room's copy sees the copies the earlier rooms just made.
         Per room it is roughly 2x that room's own wall count (Foyer: 4 own ->
         10 new). Recorded for P4.5, whose deliverable this is.
         COST, DECLARED: these two tests TRIPLED the suite -- 16s -> 46s --
         because one loads a 20-room plan and the other builds 868 walls.
         Both are marked `slow` (not `perf`: they are deterministic and
         belong in CI), so `--quick` is 13s again while the full gate pays
         ~50s. A 10-run re-certification now costs ~10 minutes, which is a
         real change to the gate's ergonomics and is said out loud rather
         than discovered by whoever runs it next.

P3.7  done -- TICKED 2026-07-30 by the reviewer. Three sub-commits, each at a
         full-mode green gate.
ruff:    clean
pytest:  Gate-Census: collected=520 ruff=clean
         Gate-OFF: 514 passed, 6 xfailed in 15.36s  -> sum 520  OK
         Gate-ON: 514 passed, 5 xfailed, 1 xpassed in 18.49s  -> sum 520  OK
         Gate-DEEP: 509 passed, 7 deselected, 4 xfailed in 17.82s -> sum 520 OK
         Gate-Verdict: GREEN (every sum reconciles against --collect-only)
         519 -> 520 collected, +1 (test_an_open_side_is_drawn_dashed); nothing
         removed.
commits: 2c5fd8d (1 amended acceptance) . b8fec07 (2 the cue) . 1260721 (3 the
         deletion sweep)

THE SPEC WAS AMENDED BEFORE THE CODE, and the census is why that mattered. Two
         divergences from the estimate, both found by grepping disk rather than
         reading the task line:
         * NO LIVE PRODUCER since P3.5 -- zero `OpenWall(` calls tree-wide. The
           "P2.3 producer branch in apply" the estimate named is already a
           COMMENT. The P2.3 log line promising P3.7 would retire it is stale
           history, ANNOTATED not rewritten (the log is history; wrong history
           gets an annotation).
         * `is_open` was the real sweep at ~7x the estimate: 44 readers across
           17 files, every one permanently False.

(a) VERIFIED, NOT RE-DONE: `test_open_walls.py` went to null edges at P3.5.
(b) THE PIXEL ASSERTION, polarity measured FIRST (P3.4's template): wall body
         150, vacated stretch with no cue 255 (pure background -- the
         regression), dash ~124 with gaps at ~255. So the cue is a DARK, GAPPED
         line and CLAUDE.md's `< 190` sits between dash and background. Both
         halves in one test. RECEIPT: fails in a worktree without the paint
         addition, in the regression row's own words -- `[255, ... 255]`.
(c) THE CLASS IS GONE: `git grep is_open -- '*.py'` and `git grep OpenWall --
         '*.py'` both return NOTHING. Prose keeps the history.
(d) THE KNOWN-REGRESSION ROW CLOSES on the pixel test, and it HAD to be pixels:
         every structural assertion in that file stayed green for the whole life
         of the regression, because they ask the outline what is open and the
         outline was always right.

SAME CUE, PROVEN NOT ASSERTED: drawing the new cue and a real `OpenWall` at once
         puts them on the same pixels (124 each alone, 97 stacked), so the row
         closes as "the same cue from one representation" rather than "a
         different cue". `docs/gallery/08-open-walls.png` regenerates with the
         dash visible and the README sentence P3.5 had to amend is reverted.

MY OWN SWEEP FAILED TWICE BEFORE IT WORKED, recorded because the mechanism is
         reusable and so are the traps: the tree is CRLF, so every MULTI-LINE
         pattern matched zero times while single-line ones applied (a half-swept
         tree), and two `if not w.is_open\n and abs(...)` sites left a dangling
         `and` -- syntax errors written into the tree. Recovered with `git
         checkout`, safe ONLY because every piece of real work was already
         committed and the sole uncommitted content WAS the broken sweep. That
         is the P3.5 rule read the right way round: the danger is uncommitted
         WORK, and there was none.

DEFECT 28 -- THE CORPSE TABLE, AND IT IS COMPLETE (2026-07-29). Ruling 3's
         standard met: no blank rows, every corpse attributed to the test whose
         scene it actually holds. Full table and method in
         `docs/evidence/defect28-ownership.json`; the register row carries the
         summary. Swept DIRECTLY, per the amendment, rather than waiting for a
         2-in-10 race.

  'Kitchen'/'Pan' IS OWNED, and the owner is `test_groups.py::test_a_group_move_
  leaves_the_outlines_still_holding_their_corners` -- defect 22's own receipt.
  So is 'M Bath'/'Toi', and so are two pairs the re-harvest added
  ('Garage'/'PWDR', 'Garage'/'Mud'). `'A'`/`'B'` stays owned-innocent, and its
  provenance stack shows the running test IS the owner -- it was never a
  misreport at all.

  ATTRIBUTION BY DOCUMENT SIGNATURE, which is what finally cracked it. Every
  20-room corpse's own document is symmetricP1 translated +48" in x with ONE
  corner displaced a further (+12,+12) -- that test's literal script (:545 and
  :557), run by no other test in the suite. The reduced evidence file had kept
  only a summary, so the ownership question was unanswerable until a 10-run
  re-harvest on the unfixed tree (4 red, 14 dumps) produced corpses carrying
  their FULL documents. Confirmed twice more: solo, with no other window in the
  session, the test errors at its own teardown 1 run in 12; and on a red DEEP
  run PYTEST ALREADY NAMES IT ("ERROR ... test_a_group_move_leaves_the_outlines_
  still_holding_their_corners", at "win fixture teardown").

  THAT LAST POINT IS A CORRECTION TO THIS DEFECT'S OWN FRAMING. The leak
  misattributes the corpse FILE (the stack shows `macro.py:98 processEvents()`
  above `_commit_if_changed`, a stale timer inside a later test) -- it does NOT
  misattribute the pytest error. The red DEEP runs were correctly blamed all
  along; only the evidence artifacts pointed at the wrong test.

  ROOT CAUSE, and "the race picks the victim" is WITHDRAWN -- there is no race
  in the choice. The test picks its party wall with `next(w for w in
  win.scene.items() if ...)`, and scene item order is not stable across
  processes, so the PICK varies per run. It then re-points the moved vertex for
  the party wall's TWO rooms only (`for r in (a, b)`), leaving any THIRD room
  whose outline holds that corner behind; where the geometry allows, that room
  overlaps a neighbour. MEASURED EXHAUSTIVELY over all 59 candidate picks:
  18 produce an I11 (31%, against the measured 4-in-10 red runs), and
  re-pointing EVERY holder of the corner produces 0. Which is what both app
  corner-movers already do -- `_DragVertex.ends`/`.edges` on the drag,
  `GroupItem._corner_records` on bake and rotation.

  TWO OF MY OWN CLAIMS WITHDRAWN BY THE SWEEP:
    * `window.visible=false` is NOT a staleness tell. No fixture window is ever
      shown, so a LIVE fixture window reads exactly the same. The original
      "recorded by a window that is NOT VISIBLE, while an unrelated test was
      running" over-read it.
    * A stale window's walk is SILENT on this tree. Forcing `_commit_if_changed`
      -- the identical call the leaked timer makes -- on every live window after
      every test, 518 times, produced ZERO reports, because every I11 a stale
      scene holds sits in that scene's own accepted baseline. The leak is real
      and still worth fixing; it is not what turns a run red.

  NOT ESTABLISHED, AND NOT ASSERTED: that an equivalent APP gesture can strand a
  holder. 38 synthetic endpoint drags over multi-room corners moved the corner
  in NONE of them -- the branch does not drive headlessly that way -- so that
  run's "0 stranded, 0 I11" is VACUOUS and is discarded rather than quoted as an
  acquittal. Checked because a "clean" result that was never in a position to be
  dirty is exactly defect 21's near-miss. The app is neither cleared nor accused
  here; if the question is wanted answered it needs a harness that drives the
  drag for real.

P3.6-followup  done -- DEFECTS 28 AND 29, AND P3.6 TICKS (branch v5-topology)
ruff:    clean
pytest:  the re-certification, ruling 4's condition, met in FULL mode:
         TEN consecutive `python tools/gate.py` runs, 10/10 GREEN, each
         trailer machine-written and each sum reconciled against
         --collect-only. The last of them:
           Gate-Census: collected=519 ruff=clean
           Gate-OFF: 513 passed, 6 xfailed, 3 warnings in 15.52s  -> sum 519  OK
           Gate-ON: 513 passed, 6 xfailed, 4 warnings in 17.44s  -> sum 519  OK
           Gate-DEEP: 508 passed, 7 deselected, 4 xfailed, 3 warnings in 16.77s
                      -> sum 519  OK
           Gate-Verdict: GREEN (every sum reconciles against --collect-only)
         These are the FIRST `Gate-DEEP` trailers on the branch -- every
         previous commit carried `--quick` (Census + OFF only), which is why
         the trailer requirement was made explicit: a 10/10 claimed against
         quick trailers would be the transcription class returning through the
         mode flag.
commits: b1679a4 (the corpse table) . c1496fe (28A, the owning test) .
         ee7e4e5 (28B, the fixture leak) . e8a7348 (29) . plus this doc commit.
census:  518 -> 519 collected, +1: test_undo::test_closing_a_window_stops_its_
         dirty_timer. Nothing removed.

WHAT THE DEEP FLAP ACTUALLY WAS, and it was not the leak. The corpse table's
         owner -- `test_a_group_move_leaves_the_outlines_still_holding_their_
         corners` -- picked its party wall with `next(w for w in
         win.scene.items() ...)`, and scene item order is not stable across
         processes. 18 of its 59 candidate picks leave two rooms overlapping
         (31%, against the measured 4-in-10 red DEEP runs), because the test
         re-pointed the moved corner for the party wall's TWO rooms and left
         any THIRD holder behind. Deterministic pick + every holder re-pointed:
         0 of 59, and 15 consecutive solo DEEP runs green where the same test
         on the same tree was 1-red-in-12 before.

THE LEAK IS REAL AND IS FIXED, AND IT IS NOT WHAT TURNED RUNS RED -- the two
         are separate and were being read as one. Measured across the suite:
         peak live MainWindows 16 -> 0, peak holding a LIVE dirty timer 9 -> 0,
         alive at session end 12 -> 0. What the leak did was misattribute the
         corpse FILES (a stale timer firing inside a macro test, the stack
         showing `macro.py:98 processEvents()` above `_commit_if_changed`); the
         pytest ERROR was correctly blamed on the owner all along.

THE GUARD IS AN INVARIANT, NOT A BUDGET: no window outlives its test holding a
         live dirty timer. A cap on the count would pass a suite that leaks
         quietly as long as it leaked few enough. FAIL-FIRST RECEIPT, in a
         detached worktree per the standing rule: the guard alone against
         pre-fix code produces 333 teardown errors.

TWO MISTAKES IN THE DISPOSAL, both found by running it rather than reading it,
         and both worth carrying forward:
         * stopping the timer BEFORE the close silences a timer the close then
           RESTARTS -- closing emits scene changes, they reach `_mark_dirty`.
           Close, let them settle, then stop.
         * `processEvents()` does not deliver `DeferredDelete`, so `deleteLater`
           left the window standing and still counting. `sendPostedEvents(None,
           DeferredDelete)` is what destroys it.

AND THE GUARD IMMEDIATELY EARNED ITS KEEP: `test_scaling._measure` leaks the
         same way, and its two windows come from a MODULE-scoped fixture, so
         they predate every per-test disposal and outlived the whole file.
         Fixed at source rather than by loosening the guard -- 67 errors in the
         OFF/ON runs (the perf tests DEEP deselects), which is the whole blast
         radius of (B).

DEFECT 29, SEPARATELY per ruling 1: `closeEvent` stops the timer, and only once
         the close is ACCEPTED -- a close the user cancels must leave the
         window as it was, debounce included, or the edit in flight when they
         hit the X never becomes an undo step. Its test asserts the
         PRECONDITION (that the edit started the debounce) before asserting the
         fix, so it cannot pass vacuously, and it fails pre-fix on exactly the
         line it names.

THREE CLAIMS OF MY OWN WITHDRAWN BY MEASUREMENT, recorded because the register
         carried them as fact:
         * "the race picks the victim" -- there is no race in the choice; the
           PICK varies because scene order does.
         * `window.visible=false` is a staleness tell -- it is not; no fixture
           window is ever shown, so a live one reads identically.
         * a stale window's walk reports -- forcing `_commit_if_changed` on
           every live window after every test, 518 times, gave ZERO reports:
           every I11 a stale scene holds sits in its own accepted baseline.

NOT ESTABLISHED, AND NOT ASSERTED: that an equivalent APP gesture can strand a
         room holding a dragged corner. 38 synthetic endpoint drags moved the
         corner in NONE of them, so that run's "0 stranded" is vacuous and is
         discarded rather than quoted as an acquittal -- the app is neither
         cleared nor accused. Answering it needs a harness that drives the drag
         for real, and that is not this task's.

P3.6  CODE COMPLETE, NOT TICKED -- blocked by defect 28 (branch v5-topology)
      [SUPERSEDED: ticked at the P3.6-followup above, 2026-07-30.]
         DEFECT 26 IS FIXED and the diagnosis is worth carrying forward as the
         standard for what "root cause" means here: a stack, then an
         explanation for every property the bug had, then a narrow fix. It was
         never memory corruption -- `verify()` raised inside a QTimer callback,
         and PyQt turns an exception escaping a C++ -> Python callback into
         `qFatal()` -> `abort()`. The guard is narrow (that exception type only,
         at the 7 callback paths reaching the 3 call sites) and the acceptance
         was 0/10 crashes against ~4/20 before.
         WHAT REMAINS IS DEFECT 28, which the crash was hiding: a group rotation
         genuinely produces overlapping placed rooms (I11), ~2/10 deep runs. The
         tick waits on it, because DEEP green-and-reliable is the condition.
         Every acceptance property is green and every ruling is implemented,
         and the tick is still withheld, because the gate ruled at this task
         is what found the reason. `tools/gate.py` runs the three gates with
         their output CAPTURED, and under `FP_VERIFY_DESIGN=deep` the suite
         then ABORTS about 40% of the time -- rc 0xC0000409, a hard process
         crash, not a failing test. Bisected to P3.6: 0 of 4 at `e3fabb6`,
         the commit immediately before this task's first. A phase whose gate
         cannot be relied on to run is not a phase that has passed its gate,
         whatever the counts say when it does complete.
ruff:    clean
pytest:  OFF  512 passed, 6 xfailed in 15.9s
         ON   512 passed, 6 xfailed in 19.8s
         DEEP 507 passed, 4 xfailed, 7 deselected in 20.0s
         516 collected; OFF 512+6 and DEEP 507+4+7 both reconcile against
         `--collect-only`.
commits: 94a4de6 (0 spec) . 2fb3c77 (1 the anchor) . f964394 (1a the phantom E)
         . 80435c1 (1b R4b/R2b rulings) . 7fe1aa2 (2 defect 24) . 3cdf046 (3
         R4b) . e4907c7 (3a the gate that was not gating) . 52111c3 (4 R2c) .
         41cc975 (5 R2b) . ea50dce (6 R5)

THE AMENDED ACCEPTANCE (R1), and each of its four properties green:
  (a) an opening anchored `from: "v2"` keeps its `offset_in` exactly when the
      wall is stretched AT v2 -- `test_an_opening_holds_its_offset_when_the_
      far_end_is_stretched`. RECEIPT: failed against s-based code before the
      anchor landed.
  (b) reversing a wall leaves the opening's physical position unchanged --
      `test_reversing_a_wall_leaves_its_openings_where_they_are`. RECEIPT:
      failed measurably, the door mirroring 200.0 -> 40.0.
  (c) the split of R2 -- `test_a_split_clear_of_a_door_leaves_it_exactly_where_
      it_was`. WRITTEN AT R2b, and it did not exist before: R1 listed it, but
      the split coverage was the two refusal pins, and refusal is not a
      property of the anchor -- it is the absence of one.
  (d) loading a plan whose door no longer fits REPORTS it --
      `test_an_opening_that_cannot_be_placed_is_reported_not_dropped`, on the
      v4 load path specifically.

THE THREE NUMBERS IN THE TASK LINE WERE ALL WRONG, and the read-back is what
         caught them: "13 `except ValueError` sites" was every such site in the
         package, not the opening drops (7 at baseline, 8 today); `walls.py:568`
         had moved to `:1004`; and "P0.4 test 1 passes without xfail" pinned
         nothing, having never been xfail. Corrected in place at 94a4de6.

TWO DEFECTS FOUND WHILE DOING IT, both measured before being claimed:
         * DEFECT 24 -- `offset_in` read and written as a CENTRE distance in
           `topology.py`, near-edge everywhere else. 18.00" on a 36" door.
           THREE sites, not the two first registered: the third was a fourth
           hand-written copy of the arithmetic inline in `apply_merge_plan`,
           found only when fixing the other two turned its test red. All now
           route through one conversion.
         * DEFECT 25 -- a gesture can create a door-straddles-junction scene
           state the document can only represent as a reported fault. Registered
           P4.1 per ruling, with my argument for P4.3 and a move trigger in the
           entry rather than swallowed.

THE GATE AUDIT, ruled at the process failure, and it is a measurement in three
         layers because the first two were not trustworthy:
         1. GREP of every commit message (44 branch + 172 main): ONE hit, and
            it is e4907c7 -- my own disclosure, not a gate committed over.
         2. WHY THAT IS NOT THE ANSWER: 3cdf046's gate line was transcribed
            WITHOUT its ", 2 errors". The message looked green. Grepping
            messages audits what I wrote, not what ran.
         3. EMPIRICAL REPLAY of OFF and ON at all 27 code-touching branch
            commits: 8 red. Re-replayed with the P0.3b ratio class excluded:
            SEVEN GO GREEN, ONE STAYS RED.
         VERDICT: exactly ONE commit was made over a genuinely red gate --
         3cdf046 (P3.6(3), R4b), red on ON and DEEP with 2 errors, green at
         e4907c7 the next commit. Everything else was the timing-ratio class.

AND THE SEVEN ARE THE FLAP ROW'S EVIDENCE. `test_bake_scales_subquadratically`
         was caught red at 8.05 against a threshold of 8, and all seven show
         the tell: exactly "1 failed", ALTERNATING between the OFF and ON runs
         of the same commit. Broken code fails both; a straddling ratio fails
         whichever run the machine was busier during. ~7 of 27 replays, so the
         P3.8 row is widened from one test to the CLASS, with three members
         named.

TESTS: +9 (tests/test_openings.py, new). CHANGED, each with its one line:
         * the two R2b PINS flipped -- `split_edge` raising, `split_wall_at`
           declining. Both were placeholders pending representability;
           `match="P3.6"` was one test naming its own executioner.
         * the drag-side twin of the decline in test_wall_move.
         * two in test_topology_ops / test_topology that had encoded defect
           24's arithmetic (offset 50.0 where the near edge is 18.0) or were
           passing only because of it (a midpoint split that always fell
           inside the door).
         * test_a_clipped_band_leaves_every_room_coherent gained `rebase(win)`
           -- see the phantom-E resolution above.

P3.5-followup  done   commit d0ab89d -- DEFECT 22: a group move is a vertex move.
ruff:    clean
pytest:  OFF  503 passed, 5 xfailed in 16.5s
         ON   503 passed, 5 xfailed in 19.4s
         DEEP 498 passed, 3 xfailed, 7 deselected in 19.1s
FOUND BY A SMOKE TEST, not by the suite, and the gap is the finding as much as
         the bug. Symptoms on a v5 plan: some rooms did not track a whole-design
         group move; later individual room moves worked; and `unwelded_ends`
         warnings fired repeatedly with a moving count on a file that opened at
         zero.
REPRODUCED HEADLESSLY BEFORE ANY FIX, per the standard:
         * 140 of 140 room outline corners held one of their own walls'
           vertices before the bake -- 0 of 140 after. A party-wall drag then
           resized NOTHING: M Bath -18.20 sf / WIC +9.50 sf before, +0.00 /
           +0.00 after.
         * `unwelded_ends` 0 -> 133 grouping every ROOM; 0 -> 1 on a rubber
           band; 0 -> 0 grouping every WALL.
         * split telemetry during the bake: 160, all at items.py:703/704 --
           the exact residue P3.4 (iv) attributed to `bake()` and assigned to
           P4.5.
THE HYPOTHESIS WAS CONFIRMED FOR THE LOAD-BEARING HALF AND REFUTED FOR THE
         VISIBLE ONE, which is worth separating. CONFIRMED: `bake` assigned new
         COORDINATES to every member wall end (split-on-write) and rebuilt each
         carried room's corner list beside it, so the two agreed numerically and
         shared nothing -- orphaning the outlines P3.5 made authoritative.
         `refresh_rooms` re-bound and re-shared after every bake, so deferring
         bake's conversion to P4.5 was safe exactly as long as detection
         existed; P3.5 changed the deferral's premise, which is why this is a
         P3.5-followup and not P4.5's. REFUTED as the cause of "some rooms don't
         track": that is duplicate-on-group (defect 3, P4.5). A rubber band
         needs an item FULLY inside, so a wall poking out is left behind, its
         room's walls are DUPLICATED into the group, and `room_owns_walls` is
         then correctly false -- 17 of 20 tracked, and the 3 that did not were
         right not to. P3.5 only removed the re-detection that used to hide it.
THE FIX IS THE PLAN'S OWN `move_vertices`, and it is smaller than what it
         replaces. `_corner_records` resolves every corner the group's geometry
         holds together with the wall ends and outline edges on it;
         `_apply_corner_records` relocates each once. Walls and outlines follow
         because they hold those corners -- a bake is now the same operation as
         a wall drag.
THE CARVE-OUT IS RESPECTED BY SPLITTING, not by an exclusion list. A corner a
         NON-member wall also holds is split off before anything moves, so the
         group goes and the outsider stays -- today's behaviour exactly.
         Relocating it wholesale would wire a member to an outside wall, which
         is what the `group() is None` guards exist to prevent. Own test.
ROTATION HAD THE IDENTICAL DEFECT (140/140 -> 0/140) and now moves through the
         same records, resolved once at `_begin_rotation` and re-applied from
         the START point each event -- drift-free AND identity-preserving, where
         before it was split-on-write per mouse move. THE FIRST ATTEMPT WAS
         WRONG AND SAID SO: re-welding at `_finish_rotation` CONVERGED rather
         than closed (0/140 -> 138/140, then 139/140 on a second pass), which is
         how a positional instrument fails where an identity one is needed.
THE WARNING'S ERGONOMICS, because a correct warning that misattributes teaches
         people to ignore the channel that will one day be right. It said
         "expected on a plan loaded from a legacy file" for EVERY case -- true
         of what a file arrives with, false of what an edit tears -- and fired
         on every debounced snapshot, so a plan that opened clean produced a
         stream of them with a moving count. Now the first walk after a load
         sets the BASELINE, only a walk finding MORE warns, the message names
         the split (opened-with vs NEW), and a repeat of the same state is
         silent. `strict=True` is untouched: two tests pin it.
PERF HELD, and the harness earned its keep twice. bake 6.5 -> 28.6 ms
         (n=4 -> n=8), ratio 4.39, against P3.5's 6.9 -> 28.0 / 4.03. The FIRST
         cut rebuilt each member wall inside the loop -- redundant with the
         `rebuild_all_walls` that follows, and cascading -- and cost 9x
         (25.9 -> 251.3 ms, ratio 9.70). Caught by `test_bake_scales_
         subquadratically` on the first full run.
TESTS ADDED (5), and one of them is NOT the receipt -- verified by running all
         five against pre-fix code in a worktree:
         * whole-plan group + move carries every room, unwelded_ends still 0.
           PASSES ON BOTH SIDES: the old bake translated each carried room's
           corner list explicitly, so the rooms tracked POSITIONALLY. It guards
           the property at a scale the rest of test_groups.py never reaches (20
           rooms / 80 walls vs ~5 members) and is the first group test to look
           at the debris counter at all. Annotated as such in its own docstring
           so it is not mistaken for the receipt later.
         * the outlines still hold their corners after a bake, and a corner move
           still resizes the rooms -- THE RECEIPT, fails pre-fix.
         * the rotation half -- fails pre-fix.
         * a group move never drags a wall outside it -- the carve-out guard;
           passes on both sides by design, since it pins what must NOT change.
         * the warning names its cause and says it once (plus its mirror, that a
           legacy plan is still blamed on the file) -- both fail pre-fix.
WHY 503 GREEN TESTS MISSED IT: every group test in the suite tops out at ~5
         members, and not one had ever asserted on `unwelded_ends`. The bug
         needed a plan big enough to have party walls and a check nobody was
         making. Both gaps are closed here.

P3.5-followup, PER-ROOM DIAGNOSIS -- asked for after the fix landed, to explain
         the TWO presentations in the reported screenshot (one room fully
         detached with its dashed outline at the original position, another
         offset but coherent). Measured per room on a rubber-band selection over
         92% of symmetricP1, reporting (a) outline vertices matching no endpoint
         of any wall the room names, (b) whether walls moved, outline moved,
         both or neither, and the identity count underneath both.
         THE TWO PRESENTATIONS ARE TWO DIFFERENT DEFECTS, and the prediction
         that they collapse to one cause is REFUTED. Recording that is the
         point of having predicted:
         * OFFSET BUT COHERENT -- 17 of 20 rooms. walls 13/13 moved, outline
           13/13 moved, (a) = 0. Nothing visible is wrong. IDENTITY 0/13: every
           corner is a different object from its wall's vertex, because the old
           bake computed the room's new corner list SEPARATELY from the walls'
           new coordinates and the two agreed only numerically. This is DEFECT
           22, it is invisible in any screenshot, and it is fixed -- the same
           run post-fix reads 13/13 identity with every other column unchanged.
         * FULLY DETACHED -- 3 of 20 (Garage, PKT Off, Util). walls 6/9 moved,
           outline 0/9, (a) = 5 stranded corners, identity 4/9 -- the four
           corners it shares with the walls that did NOT move. The room was not
           carried at all (`room_owns_walls` false), because the band clipped
           one of its walls and `group_selected` duplicated the rest.
           BYTE-IDENTICAL BEFORE AND AFTER THE DEFECT-22 FIX: 46.65" / 39.98" /
           23.32" of region-to-walls drift either way. The vertex translation
           cannot touch it, because the room is not in the set being moved.
         AND THE "P3.5 UNMASKED IT" CLAIM IS WITHDRAWN, having been asserted
         before it was measured. The same drift measurement on the pre-P3.5
         tree strands Garage by 148.3" against 46.65" now -- re-detection was
         not hiding the detachment, it was landing the room somewhere worse.
         The detached presentation predates P3.5 and is REGISTERED AS DEFECT 23
         against P4.5, because what to do about it is a semantics decision (does
         a room whose walls partly moved DEFORM to follow the corners that
         moved, as a party-wall drag already makes both its rooms do -- or stay
         put?) and that question is what a group IS.
         METHOD NOTE: metric (a) is NOT comparable across the P3.5 boundary.
         Before P3.5 an outline edge could be spanned by a LONGER wall, so a
         corner legitimately sat mid-wall; "corner matches no wall endpoint"
         only became a defect once one edge meant one wall end to end. The
         cross-boundary comparison is the drift number, which is basis-free.

P3.5-followup, ACCEPTANCE ITEMS -- four, answered in order.

COMMIT NAMING, and the rule was NOT honoured on the first pass. The fix, its
         telemetry and its tests went in as ONE commit, d0ab89d, not three. The
         full gate (ruff + OFF/ON/DEEP) was run immediately before it, so the
         green is real; what is missing is the ROLLBACK POINTS the sub-commit
         rule exists to create. Recorded rather than rewritten -- history
         surgery to make a log entry look tidier is the wrong trade. The
         remainder was split properly: 06c2145 (a) the warning wording,
         408adf7 (b) the tests, plus this doc commit, each at a full gate.

THE +6, named from a collect-only diff of f738437 against HEAD (502 -> 508
         collected; nothing removed):
           test_groups::test_whole_plan_group_move_carries_every_room
           test_groups::test_a_group_move_leaves_the_outlines_still_holding_
             their_corners
           test_groups::test_a_group_rotation_also_keeps_the_corners
           test_groups::test_a_group_move_never_drags_a_wall_outside_it
           test_design_bridge::test_the_warning_names_the_cause_and_says_it_once
           test_design_bridge::test_a_legacy_plan_is_blamed_on_the_file_not_on_
             an_edit
         Plus, at (b), a SEVENTH that is an xfail rather than a pass:
         test_groups::test_a_clipped_band_leaves_every_room_coherent -> P4.5.
         So the census is now 503 passed / 6 xfailed, and the sixth marker is
         that one -- named here so the next delta starts from a known set.

STEP 4 WAS HALF-DONE AND IS NOW WHOLE. The whole-plan test asserted only that
         each room's outline LANDED in the right place, which is why it passed
         against the pre-fix code. It now asserts all four per-room columns --
         walls-moved, outline-moved, identity, unwelded_ends -- on a 100%
         selection with no clipped rooms, and FAILS pre-fix (identity 0 where 4
         is required, verified in a worktree). The diagnosis's columns and the
         guard's columns are now the same columns.

STEP 5 WAS DONE AT d0ab89d, and the specific question is answered by
         measurement on the defect-23 repro POST-FIX: the duplicated walls left
         behind by a clipped band DO register as unwelded ends under a live
         gesture, so the rewording belongs to this task exactly as reasoned.
         Same 10-walk sequence (open, idle, group, bake, four debounced
         snapshots, a second move, one more snapshot):
           BEFORE  8 warnings, one per snapshot, every one of them saying
                   "expected on a plan loaded from a legacy file"
           AFTER   2 warnings, one per DISTINCT state (1 end, then 8), both
                   reading "... are NEW ... this is not the legacy-load case"
         The idle and post-open walks are silent in both, and the legacy case
         still says legacy (`test_a_legacy_plan_is_blamed_on_the_file_not_on_an_
         edit`). Reading the message the repro actually printed also caught the
         copy saying it backwards -- "0 of them since the plan was opened and 1
         NEW" -- fixed at 06c2145.

ONE UNEXPLAINED OBSERVATION, recorded rather than dismissed: a single `E`
         appeared in one DEEP run's truncated progress output. Not reproduced in
         five subsequent full DEEP runs (NOT "under different random seeds" --
         that phrase is withdrawn at defect 26 round 2: pytest-randomly is not
         installed, so every run in this project has always been in the same
         order), and an
         explicit ERROR grep over a full `-ra` run finds nothing. Most likely a
         cut-off pipe rather than a real error, but it is written down here so
         that if it recurs at P3.6 it is the second sighting, not the first.
         STANDING INSTRUCTION, carried into P3.6 by ruling: a recurrence during
         P3.6 is a SECOND SIGHTING and is investigated on the spot -- not
         re-filed as a first.
         >> RESOLVED AT P3.6, and the guess above was wrong in both halves: not
         a cut-off pipe, and not a timing flap. It is
         `test_a_clipped_band_leaves_every_room_coherent`, added at 408adf7 --
         the defect-23 characterization. It deliberately leaves the scene
         corrupt (stranded rooms are its subject) and never declared that state
         as a baseline, so under FP_VERIFY_DESIGN=deep the `win` fixture's
         teardown verify fires and pytest reports the test TWICE: an `E` in the
         progress line, a second XFAIL in the summary. Fixed with `rebase(win)`,
         the move `_overlapping_rooms` has always made for its deliberate
         overlap. THE SAME DOUBLE-REPORT WAS THE OFF-vs-DEEP CENSUS DISCREPANCY
         -- one cause, two symptoms. Recorded as a closed sighting; a THIRD
         would be a new bug, not this one.

P3.4  done   (branch v5-topology; four sub-commits + two riders)
ruff:    clean
pytest:  OFF  491 passed, 4 xfailed, 1 xpassed in 19.2s
         ON   491 passed, 4 xfailed, 1 xpassed in 24.6s
         DEEP 486 passed, 3 xfailed, 7 deselected in 22.2s
         (baseline in: P3.3's 447/4/1. +44 tests, one deleted -- see (iv).)
commits: ea54413 (i) · 340816c (ii) · a4a3336 457105e e49c07f (iii, three
         families) · 670fded (rider: the two divergence rulings) · 89f3d8b (iv)
         · cf7f850 (defect 20) · plus the per-sub-commit doc entries below.
         Logged sub-commit by sub-commit per the handoff-spec rule, so a
         successor session reads the state from here plus the seven settled
         points at lines 375-408 rather than from a chat summary.
(i) done   commit ea54413 -- planner/applier factoring + the scene applier for
         merge_collinear.
ruff:    clean
pytest:  OFF  468 passed, 4 xfailed, 1 xpassed in 18.4s
         ON   468 passed, 4 xfailed, 1 xpassed in 21.9s
         DEEP 463 passed, 3 xfailed, 7 deselected in 18.5s
files:   floorplanner/design/topology.py (GraphView/WallView/OpeningView,
         Merge/PlannedOpening, plan_merge_collinear, apply_merge_plan,
         graph_from_design; merge_collinear becomes their composition),
         floorplanner/walls.py (graph_from_scene, apply_merge_plan_to_scene,
         merge_collinear_scene), tests/test_topology_ops.py (new, 21)
NO EXISTING TEST CHANGED -- `git status tests/` shows only the new file, all
         three ways. The changed-test budget point 4 governs is still untouched
         going into (iii).
THE SHAPE, since it is the crux and the thing (ii)-(iv) all lean on: the
         decision runs ONCE, pure, over a neutral `GraphView` whose keys and
         anchors are the CALLER's own handles -- wall ids and vertex ids for a
         Design, `WallItem`s and `Vertex` objects for a scene. It returns a
         `Merge` delta (survivor, absorbed, the corner anchors the ends adopt,
         the planned opening offsets, the corners consumed). Two thin appliers
         execute it, touching only what it names. The delta deliberately does
         NOT name room binding: a Design records that as wall.left/right, the
         scene as WallItem.rooms, and each applier derives its own from
         `Merge.absorbed`. That is the one thing the two targets genuinely
         represent differently, and saying so is cheaper than pretending
         otherwise.
TWO BEHAVIOUR CHANGES IN THE PURE OP, both found BY single-sourcing rather
         than in spite of it, and both fixes:
         * merge no longer REFUSES a wall carrying openings. They are
           redistributed onto the merged span and deduped -- DEFECT 9, closed
           on the live-editing path the task text names. Guarded both ways: the
           new op yields one door, and `_coalesce_all_impl` on the identical
           input still yields two, so the closure is legible rather than
           asserted.
         * the survivor keeps its OWN DIRECTION. The old code wrote
           `w1.v1, w1.v2 = far1, far2`, which REVERSES the survivor whenever the
           run extends behind its v1 -- and did not swap left/right to match, so
           every side on that wall silently flipped. Latent, unpinned, and
           invisible until the same code had to serve a scene that renders
           sides. Own test.
TELEMETRY, ahead of point 5's ledger: an exact end-to-end merge causes ZERO
         split-on-writes -- the merged end is re-pointed AT the corner's vertex
         (`set_end_vertex`), not assigned a coordinate as coalesce did. A merge
         absorbing a wall from up to perp_tol off the line still splits, and
         that is correct: that end lands where no corner was, so it is a new
         corner and should say so.
A NARROWER CLAIM THAN IT LOOKS, stated so (iii) does not inherit a
         misconception: the merge shares the SURVIVOR's end with the corner
         anchor. It does not rebind OTHER walls sitting at that corner -- that
         is weld's job, and weld is still on this task's deletion list. What is
         true today is that both ops resolve the same corner to the same
         representative `Vertex`, so they converge rather than fight.
(ii) done  commit 340816c -- split_edge scene-side, the split rule's second
         half, the guard retarget.
ruff:    clean
pytest:  OFF  482 passed, 4 xfailed, 1 xpassed in 18.4s
         ON   482 passed, 4 xfailed, 1 xpassed in 21.8s
         DEEP 477 passed, 3 xfailed, 7 deselected in 20.7s
files:   design/topology.py (Split, plan_split_edge, apply_split_plan;
         split_edge becomes their composition), walls.py
         (apply_split_plan_to_scene, split_wall_at, WallItem.
         _split_body_landings + _run_wall_under), tests/test_wall_move.py
         (+7, ADDITIONS ONLY -- 0 deletions), tests/test_topology_ops.py (+7),
         tests/test_topology.py (the one rewrite, below)
THE SPLIT RULE IS NOW WHOLE. P3.3 built the first half and left the second
         declared-but-not-done, tee branch on the coordinate path with a
         comment naming this task. A body-landing now SPLITS the wall it lands
         on -- which MAKES the vertex it never had -- and is then promoted onto
         it exactly as a corner attachment is. The new segment joins the run,
         so the user still slides the whole wall they grabbed (own test; that
         is the way this could have silently gone wrong).
TEST CHANGED (1), the pre-authorized one, named per the working agreement:
         tests/test_topology.py::test_split_edge_raises_on_a_wall_with_openings
         asserted `pytest.raises(NotImplementedError, match="P3.3")`. OLD OP:
         split_edge refused any wall carrying an opening. NEW OP: it
         redistributes them. WHY THE ASSERTION MOVED: that message was a
         placeholder for unbuilt work and said so; the work is built here, so
         the assertion pinning its absence has nothing left to pin. Rewritten
         as TWO tests -- redistribution works, and the guard SURVIVES narrowed
         to the case redistribution genuinely cannot answer. Hence the
         pre-authorized string change, `match="P3.3"` -> `match="P3.6"`.
THE GUARD IS RETARGETED, NOT RETIRED, and the distinction is the content of the
         ruling. Redistribution answers "which segment owns the door". It
         cannot answer "which segment owns a door the cut runs THROUGH",
         because neither does -- that is an opening which no longer fits where
         it lands, and reporting one instead of silently sliding it is P3.6's
         line in this plan. So the guard keeps its P1.3-followup discipline
         (fail loud AT the call site) on a strictly smaller domain.
TWO POLICIES, ONE DECISION -- declared, because it is the closest this task
         comes to the applier drift point 1 forbids, and it is not that.
         `topology.split_edge` RAISES on a straddling split; the scene op
         DECLINES it. Same planner, same delta, same `straddled` flag. What
         differs is what each CALLER does with a flagged delta, because one is
         a document repair and the other is a mouse gesture that must not
         crash mid-drag. The decision is single-sourced; only the policy is
         local, and a declined split leaves P3.3's exact behaviour behind.
TELEMETRY -- point 5's prediction, measured BOTH ways rather than asserted:
         * dedicated tee scenario, 12 drags: 12 split-on-writes BEFORE
           (measured by disabling the new pass), 0 AFTER. The branch is silent,
           which is the claim point 5 makes.
         * composite (coalesce + weld + group + bake + ungroup + 12 drags):
           mouseMoveEvent splits 4 -> 1.
         * AND THE RESIDUE IS NOT THE TEE BRANCH FAILING. Two landings were
           DECLINED because the split point falls inside an opening -- and
           those openings turn out to be 15 IDENTICAL 96" windows stacked at
           one `s`, produced by the old `_coalesce_wall_impl` on the
           bake/ungroup path. That is DEFECT 9 in the wild, inside the code
           (iii)/(iv) delete. PREDICTION FOR (iii), recorded now so it is a
           prediction and not a rationalisation: retiring coalesce removes the
           stacks and those two landings then split.
         * a call site P3.3's scenario never triggered: 8 splits at
           walls.py:233 in `_coalesce_wall_impl`. Also (iii)/(iv)'s.
THE CORPUS GUARD HAS GONE VACUOUS, and saying so is the point. P3.3's
         press-every-wall test still passes -- but neither corpus plan has an
         unwelded body-landing, so pressing every wall of sample_plan and
         planc1 now makes exactly 0 splits (measured). It no longer exercises
         the risk it was written for. Added the case that DOES split, asserting
         the document is unchanged across it: the scene walk already cuts walls
         at junctions (`split_params`), so a press-time split only makes the
         scene agree with what the document always said. Verified rather than
         assumed -- 2 scene walls -> 3, document byte-identical, 3 document
         walls before and after.
(iii) done  commits a4a3336 (family 1), 457105e (family 2), e49c07f (family 3).
ruff:    clean
pytest:  OFF  491 passed, 4 xfailed, 1 xpassed in 16.7s
         ON   491 passed, 4 xfailed, 1 xpassed in 19.3s
         DEEP 486 passed, 3 xfailed, 7 deselected in 17.4s
NO EXISTING TEST CHANGED across all three families. The changed-test budget
         point 4 governs is still spent only on (ii)'s one pre-authorized
         rewrite, going into (iv).
FAMILY 1 -- COALESCE (5 sites): view.py:487 and walls.py:1385 (draw / drag
         release) -> `merge_wall`; planio.py:181 (load), rooms.py:1020 (room
         label drop), mainwindow.py:820 (ungroup) -> `merge_all`.
         `merge_wall` forces the passed wall to be the run's SURVIVOR -- the
         caller has just drawn or dragged that item, holds a reference to it,
         and it carries the selection; the planner takes the run's first wall
         in the caller's order, so the whole of "this one survives" is a sort
         key. UNGROUP IS WIRED, NOT MIGRATED, per the ruling, with the comment
         at the site: under P4.5 nothing is duplicated so nothing needs merging
         on ungroup, making that call P4.5's to DELETE rather than this task's
         to port.
         Behaviour change, small and a fix: the merged wall lands on the union
         span exactly, where `_coalesce_wall_impl` re-snapped both ends to the
         6" grid. bridge.py:550 already flags that snap in its own words
         ("Coalesce MOVES geometry"). No test depended on it.
         PERF: the planner gained `_candidate_groups`, `_WallIndex`'s line
         bucketing moved to where the merge decision now lives -- without it a
         per-wall merge scans every wall on every draw-release, trading
         coalesce's O(local) for O(plan), the direction P3.8 must not go.
FAMILY 2 -- WELD (3 sites): view.py:489 `join_endpoints` -> `weld_wall_ends`;
         imageio.py:180 `weld_all` -> `weld_scene`; mainwindow.py:827 ->
         `normalize_walls`. After this the whole coalesce+weld set is a
         CALLERLESS ISLAND.
         THE COMMAND OUTLIVES ITS IMPLEMENTATION, per the ruling. Edit ▸
         Coalesce all walls now is the explicit plan-wide normalization: merge
         every collinear run, then weld -- close the gaps, fold coincident ends
         onto one vertex, split a wall where another's end lands on its body.
         Same menu item, same intent, new machinery, still ungated.
         Welding now has a TOPOLOGY half. `weld_all` left a welded corner as
         two coordinates that happened to agree, which is exactly what P3.3's
         drag then had to rediscover by scanning at every press. The geometry
         snap is kept verbatim: closing a 9" gap is a repair, not topology, and
         it is the only way a drawn or extracted plan closes junctions at all.
         ONE RULE, FOUND BY A FAILING TEST. The first cut had `weld_scene`
         split body landings too, and test_extract_from_reference_adds_walls
         went 5 walls -> 7. The split is CORRECT topology -- but shipping it
         inside a call-site migration is a behaviour change smuggled under a
         rename, and it edits a wall the user never touched. So splitting
         belongs to the EXPLICIT pass and nowhere else: `weld_wall_ends`
         doesn't, `weld_scene` doesn't, `normalize_walls` does. Applying the
         rule uniformly made the test change unnecessary, which is the tell
         that the rule was right and not a dodge. P3.5 will want plan-wide
         planarity for `enclosing_face`; that is P3.5's to ask for, through the
         pass built for it.
FAMILY 3 -- THE QUERY HELPERS: one migrated, one policed, two divergences.
         `_joined_at` MIGRATED: a 0.6" coordinate search becomes a DEGREE
         lookup on a `_CornerIndex`, and `_WallIndex`'s endpoint hash is gone.
         Zero behaviour change, and the replacement carries its own oracle --
         `_joined_at`'s un-indexed fallback still runs the old search, so the
         test compares the two directly on every end rather than trusting the
         reasoning. `_CornerIndex` is now the SINGLE definition of "these ends
         are one corner"; both halves earn their place, since identity is the
         real question but load deliberately does not weld, so in a loaded plan
         only position can see the corner.
         `coincident_walls` POLICED, NOT MERGED, and that is a decision. It is
         on the hottest path in the app (`WallItem.rebuild`, once per wall per
         pass) and routing it through the planner would allocate a view per
         candidate to prove a predicate that is already a transcription. A
         drift gate pins the two equal across overlapping / off-grid /
         abutting / perpendicular / diagonal pairs instead -- the same move
         `--verify-design` makes for the two appliers.
TWO CENSUS DIVERGENCES, reported rather than forced (Touches lists are hints):
         * `_WallBBoxIndex` CANNOT die at P3.4. The task line lists it, but its
           last caller is rooms.py:340, the memoized room dirty-check -- and
           "refresh_rooms memoization" is on P3.5's list BY NAME. A line dies
           when its last caller dies, and this one's last caller is P3.5's.
         * `wall_endpoint_open` NOT migrated to degree, deliberately. Its
           tolerance is JOIN_TOL (9"), not SHARE_TOL: the 9" scan was a PROXY
           for a question the pre-vertex code could not ask. Degree is the
           truer question, but swapping them changes which ends the draw-snap
           offers to align with on unwelded geometry -- a behaviour change
           needing this task's own three-part earning, and it buys no deletion
           since the helper survives Phase 3 either way. Recommended as its own
           change or as P3.5's.
         Consequence: `_WallIndex` SHRINKS rather than dies. Its line buckets
         are a spatial index, not detection machinery, and the planner needed
         the identical bucketing badly enough that `_candidate_groups` is a
         copy of them. The honest end-state is one index, not zero.
RIDER (commit 670fded) -- the two (iii) divergences, ruled:
         * `wall_endpoint_open` REFRAMED PERMANENTLY, in its own docstring, so
           no future task "migrates" it out of a misplaced sense of
           completeness. It is not a survivor of the old world; it is a correct
           citizen of the new one. Its tolerance is JOIN_TOL, the GESTURE
           tolerance, and gesture questions are inherently spatial. Degree
           answers the MODELLING question ("are these ends one corner?"); this
           answers the AIMING question ("is there something near enough to snap
           to?"). Degree cannot serve here even in principle -- the ends worth
           offering the user are precisely the ones NOT yet welded, so a degree
           query calls every one of them free and the snap has nothing to aim
           at. The docstring names `_joined_at` as the one that DID migrate.
         * THE BUCKETING DUPLICATION UNIFIED, not pinned. `topology.line_bucket`
           + `bucket_reach` are the one definition; `_candidate_groups` and
           `_WallIndex` both call them and `_WallIndex.OFF` is gone.
           Unification beat a second drift gate because the policy is pure
           coordinates, so it belongs on the Qt-free side with the scene
           importing it -- the dependency flows the right way, which is not
           true of most things one might want to share across that fence.

(iv) done   commit 89f3d8b -- the deletion, the junction contract, the checks.
DELETED, 149 lines across 7 functions, all callerless after (iii):
         `_coalesce_wall_impl` (59), `coalesce_wall` (8), `_wall_count` (5),
         `_coalesce_all_impl` (26), `coalesce_all` (7), `weld_all` (23),
         `WallItem.join_endpoints` (21) -- plus `_WallIndex`'s endpoint hash,
         folded into `_CornerIndex` at (iii): 50 lines -> 40.
EXIT CHECK 1 -- MEASURED DELETION vs THE ESTIMATE. Estimated 375 across 13
         functions; MEASURED 149 across 7. The gap is three survivors with
         named reasons, not shortfall, and 169 lines of the census live on:
         * `fracture_delete_wall` (55) + `_merge_intervals` (9) -> P4.1. Two
           live callers, not migrated at (iii), and retiring them IS P4.1's
           deliverable -- its acceptance is literally "P0.4 test 2 flips to
           pass". AND THE MEASUREMENT IS THE FINDING: a plain delete now KEEPS
           the room (1 room, 100.0 sf, 3 built walls + 1 open edge -- exactly
           test 2b's assertion), because P3.2 gave RoomItem a stored outline.
           P4.1's blocker is already gone and P4.1 is now a small change;
           doing it here would be landing another task's deliverable under this
           one's name.
         * `_WallBBoxIndex` (34) -> P3.5, as reported at (iii).
         * `_compute_wall_junctions` (31) STAYS -- next paragraph.
         * `_WallIndex` (40) shrank rather than died.
EXIT CHECK 4 -- THE JUNCTION CONTRACT, AND THE SWAP IT REFUSED. Point 3 said
         "if the junction test needs touching, the replacement is wrong."
         IT NEEDS TOUCHING, so the replacement is not made. Measured on the
         structural guard's own scene -- a horizontal and a vertical wall
         crossing mid-span -- the two share ZERO corners (all four ends degree
         1) while their `_solid`s genuinely intersect and the bbox pass
         correctly clips both. Adjacency-only neighbours find nothing, set both
         clips to None, and fail the guard. An unwelded crossing is a legal
         scene state (crossing-point insertion is not built), so bbox search is
         not legacy machinery here -- it is the only thing that answers the
         question. The contract worked exactly as designed: it was written to
         catch a wrong replacement, and it caught one.
         THE PIXEL ASSERTION LANDED ANYWAY, an ADDITION, because it is what
         makes any future attempt safe. POLARITY MEASURED, NOT ASSUMED, and it
         is the INVERSE of the spec's wording: the wall body is grey (150) and
         a seam is a DARK line across the junction (56), so "no LIGHT seam
         pixel" names the wrong failure. Seam-free asserts the interior stays
         body-grey; the `< 190` threshold is used where it genuinely belongs --
         the negative half, clip cleared, where an antialiased 1-px dark line
         must read under 190 and nowhere near 100. Both halves in one test, so
         the positive assertion cannot go vacuous. The structural pin is green
         and UNCHANGED.
EXIT CHECK 2 -- THE P2.3 KNOWN-REGRESSIONS ROW DOES NOT CLOSE, and the row's
         predicted fix was wrong on its own terms. Checked by hand: the 480"
         wall still returns as two 240" segments after the undo restore,
         `merge_all` does NOT re-merge them, and the body-drag still moves one
         segment (p1.y 12 and 0). It MUST not -- the mid-span T is a degree-3
         vertex, load-bearing for the planar subdivision, and merging through
         it would destroy planarity. So this was never merge's row to close.
         NOT FLIPPED; retargeted in place with the real fix named: the drag's
         run-gathering, where `_collinear_run()` short-circuits to `[self]` for
         a room-less wall. Left unassigned rather than invented, with P4.2 as
         the nearest task that touches the drag.
EXIT CHECK 3 -- THE DEFECT-9 PREDICTION, GRADED HALF-RIGHT AND PRECISELY.
         FIRST HALF CONFIRMED: retiring coalesce removed the stacks -- 16
         openings on one wall became 1. SECOND HALF FALSIFIED: the two tee
         landings still decline. But the residual cause is now legitimate
         rather than debris -- the harness puts a 96" window at the centre of a
         240" wall and the neighbouring grid line lands at s=120, dead inside
         it (measured: openings [(120.0, 96.0)], straddled 1). A genuine
         straddle, correctly declined, P3.6's case. The count coinciding at 2
         is coincidence; the mechanism the prediction named was real and is
         gone. Recording the falsified half is the point of having predicted.
EXIT CHECK 5 -- TELEMETRY RESIDUE, 137 splits on the composite scenario:
         64 + 64  items.py:703/704 in bake()   -- P4.5's, correct that they stay
          8       walls.py in _adopt_end()     -- MOVED, not new
          1       walls.py in mouseMoveEvent() -- the grouped/rigid branch, P4.5
         The 8 were `_coalesce_wall_impl`'s at (ii); they are the merge
         applier splitting on write when an absorbed end lands where no corner
         was -- declared at (i) as correct for that case. Same count, honest
         new home.
TESTS REWRITTEN -- the plan's biggest changed-test risk, one line each:
         * test_coalesce.py (whole file): `_coalesce_*_impl` -> `merge_all` /
           `merge_wall`. THE ASSERTIONS DID NOT MOVE -- they are the behaviour
           contract, not the implementation, and every line still says exactly
           what it said. Only the call changed.
         * test_walls.py: `join_endpoints` -> `weld_wall_ends`, `weld_all` ->
           `weld_scene`, `_coalesce_wall_impl` -> `merge_wall`. Assertions
           unchanged: the geometry snap they pin was lifted verbatim into
           `_snap_wall_ends`. Plus the pixel test, an addition.
         * test_characterization.py 5 and test_floors.py: `coalesce_all` ->
           `merge_all`; the group-exemption and cross-floor assertions
           unchanged.
         * test_topology_ops.py: the defect-9 OLD-op comparison DELETED with
           the op it exercised. Once the defect's implementation is gone there
           is no old behaviour left to exhibit and the test would be asserting
           against a museum piece. It did its job at (i) and (ii); a claim
           about code that no longer exists belongs in this log, and a comment
           at the site says so.
         * test_scaling.py, test_design_bridge.py: stale `coalesce_all` wording
           only, no assertion touched.
(iv) EXIT CHECKS as fixed before the work (all five answered above):
         1. the measured deletion count against the estimated 375 across 13
            functions, with `_WallIndex`/`_WallBBoxIndex` surviving named;
         2. the P2.3 Known-regressions row re-checked BY HAND (the 480"
            body-drag moving as one run) and flipped ONLY if it genuinely
            closes;
         3. (ii)'s recorded prediction, promoted to an exit check by ruling:
            retiring coalesce removes the defect-9 stacks, so the two tee
            landings that DECLINED in the composite telemetry should then
            split. Falsifiable, cheap, and if it holds it is the cleanest
            demonstration yet that the old machinery was manufacturing the
            conditions that defeated the new one;
         4. the junction contract's two halves: `test_junction_outline_is_
            clipped_so_walls_read_solid` green UNCHANGED, plus the new pixel
            assertion at the `< 190` threshold;
         5. tests/test_scaling.py's ungroup xfail reason still says "calls
            O(walls^2) coalesce_all" -- stale from family 1, true again only as
            history. Fix it with the deletion, where the claim actually changes.
Census re-verified on disk before starting:
         `coincident_walls` at walls.py:656 and :695 and view.py:597,
         `wall_endpoint_open` at view.py:248, and the dying caller at
         walls.py:201 inside `_coalesce_wall_impl`. ONE CORRECTION to the
         census's wording, not its content: BOTH walls.py hits are inside
         `WallItem.rebuild` (:656 is the party-wall opening cascade, :695 the
         neighbour-rebuild tail), not "rebuild and paint" -- `paint` reads the
         already-built `_path`. The adjudication is unaffected; both survive
         Phase 3 and both migrate.

P4.1  done   (branch p4.1-delete-wall, 3 sub-commits: 0df3aa5 census
         corrections + the three rulings; a0e1b95 delete_wall + both call
         sites + 2b flip; this commit, corpse + tests + docs)
ruff:    clean
pytest:  514 passed, 7 deselected, 5 xfailed (OFF/ON/DEEP each, sum 526 OK)
files:   walls.py (delete_wall added; fracture_delete_wall + _merge_intervals
         DELETED, 66 lines; context-menu call site), mainwindow.py
         (delete_selected), rooms.py (docstring corrected),
         tests/test_characterization.py (2b marker off),
         tests/test_walls.py + tests/test_room_walls.py (fracture trio
         renamed/replaced), CLAUDE.md, docs/CODE_REVIEW_v2.md (defect 17
         closed with coda; defect 25 -> P4.1b ruled; carried census note),
         this file.
notes:   CENSUS DOCTRINE APPLIED at task open, and it earned its keep a third
         time: _perimeter_span does NOT die here -- _copy_spec (unowned) and
         _privatize_shared_walls (P4.2's) both outlive fracture -- so the
         deletion is 66 lines, not the ~90 the task-line record implied.
         Stated as a contingency in the register (authoritative copy) so
         P4.2's read-back inherits a question, not a claim.
         RECEIPT, fail-first: 2b re-measured xfailing against main@5a7711c
         this session, then flipped green on exactly the call-site switch --
         513 passed / 6 xfailed -> 514 / 5, nothing else moved. Census 526
         unchanged across all three sub-commits (tests replaced 1:1).
         VISIBLE-LIE CODA now in defect 17's closing entry: post-P3.7 the
         fracture no-op measured 4 bound walls + 1 OPEN edge (the outline
         still naming the dead wall fracture replaced), i.e. a dashed open
         cue painted over an edge a wall actually covers. The silence had
         aged into misinformation -- the final argument for deletion over
         repair.
         TESTS CHANGED -- all four declared at the read-back, approved before
         work began: characterization 2b (marker off; IS the acceptance);
         test_delete_free_wall_removes_whole (behaviour preserved through the
         new delete_wall entry point); test_delete_overhanging_wall_goes_
         whole_room_keeps_area and test_delete_shared_wall_keeps_both_rooms
         (INTENTIONALLY replace the fracture-era pair: the wall genuinely
         goes; each bordering room keeps its area with one open edge -- the
         party-wall numbers measured at the read-back: 100.0 sf, 3 bound +
         1 open each).
         Defect 25 deliberately NOT touched here: P4.1b branches the moment
         this task's PR merges, message-only scope per its task text.

P4.1b done   (branch p4.1b-doorway-message: 1d3eaa6 mechanism + tests;
         this commit, docs)
ruff:    clean
pytest:  516 passed, 7 deselected, 5 xfailed (OFF/ON/DEEP each, sum 528 OK)
files:   walls.py (report_gesture_fault / drain_gesture_faults /
         report_doorway_landings + the endpoint-drag release hook),
         view.py (draw-release hook), mainwindow.py (_commit_if_changed
         drains the new list beside the defect-6 report), tests/
         test_walls.py (two gui tests), docs/CODE_REVIEW_v2.md (defect 25
         closed), this file.
notes:   REPORT ONLY, per the ruling -- no change to what the gesture DOES;
         decline/split/weld policy stays P4.3's with the auto_* flags (the
         dissent's surviving kernel). The straddle question is asked of
         plan_split_edge -- one planner, no second definition of "a junction
         lands inside this opening" (P3.4 point 1). The body search runs at
         ON_SEG_TOL, not JOIN_TOL, so a deliberate reveal (a wall stopped
         short of another) never nags -- only an end ON the body, whose
         junction is genuinely owed a split, reports. The drag checks only
         the end it moved (ends=(mode,)), so an old landing on the far end
         is not re-announced by an unrelated drag.
         CHANNEL: the defect-6 discipline exactly (scene-filed, drained at
         the debounce, said once, the sentence naming the edit and the
         thing in the way) as its OWN list -- nothing failed to be PLACED,
         so draining through "Could not place ..." would misblame a door
         that is fine. Drained after the opening report so the gesture the
         user just made wins the status bar.
         RECEIPT, fail-first and mechanism-proving: both tests run UNCHANGED
         against pre-fix main@708dc2e in a worktree, reach their
         preconditions (the drawn/dragged end measurably rests on the
         host's centreline inside the door span -- the defect-28 vacuity
         lesson applied), and FAIL on the message assert, the status bar
         holding only the generic tool hint. Both pass on the branch.
         Census 526 -> 528 (the two gui tests), every sum reconciling.
         The walk's report path (R2c) is untouched and stays as the
         load-path safety net, exactly as the register entry planned.

P4.2  done   (branch p4.2-extract-join, 7 sub-commits: dfd30af core,
         4cf67e8 label-drag rewire, 9821571 defect 30, 5c8795e the P2.3
         refutation, 7dbd740 defect 13, 216e755 defect 34, + this docs
         commit. AWAITS THE PATRICK MINI-GATE before its PR merges.)
ruff:    clean
pytest:  525 passed, 7 deselected, 4 xfailed (OFF/ON/DEEP each, sum 536 OK)
files:   extract.py (NEW: extract_room/join_room/capture_floating_
         furnishings), rooms.py (placement modelled; label-drag =
         extract->move->join; _privatize_shared_walls DELETED, 51 lines;
         floating paint cue; context menu Extract/Join), design/bridge.py
         (placement emit/apply; stash retired for placement; per-floating-
         room vertex namespaces in the level walk), design/validate.py
         (I14 floating exemption; near_vertex_gaps), walls.py (defect-30
         gather; defect-13 stick; close_gap), dialogs.py (GapReviewDialog),
         mainwindow.py (Review wall gaps... action), CLAUDE.md, register,
         tests: test_extract_join.py (NEW), test_groups.py (party-wall
         flip), test_room_walls.py, test_wall_move.py, test_walls.py.
notes:   CORE FIRST, HARVEST AFTER, per the ordering constraint -- each
         piece its own sub-commit at a full green gate.
         ACCEPTANCE MET: extract -> move 500" -> join, check() clean at
         EVERY step, I12 while floating, furnishings and openings intact;
         the party-wall round trip fuses back to ONE shared wall; the
         party-wall regression test flipped xfail -> hard pass via the
         real extract (P0.5 Known-regressions row closes).
         TWO MODEL CONSEQUENCES, not workarounds: the level walk folds
         each floating room in its OWN vertex namespace (coincident-is-one-
         corner is exactly the sharing I12 breaks), and I14 exempts
         floating-vs-plan pairs (closure within a floating room still
         holds) -- same exemption class as I11.
         RULINGS EXECUTED: (a) label-drag rewired, behaviour-preserving by
         construction (the old path already WAS extract->move->join in old
         clothes); (b) defect 30 fixed as a BUG (holders of the corner via
         vertex identity; 23-vs-30 boundary stated for P4.5); (c) defect 34
         closed as the review op (list, never auto-close); (d) defect 13's
         drag half closed (stick -> scene-space WALL_PROJECT_STICK, 9",
         == join_tol_in; catch radius stays screen-space); (f)
         _perimeter_span re-argued to P4.4 in the register, contingent,
         not counted in this census.
         RULING (e) REFUTED BY THE TREE, reverted, recorded: the vertex-
         adjacency run gather turned P3.3's anti-shear pins red --
         _tee_scene is topologically IDENTICAL to the undo-split segments,
         and "split first, shear never" owns that topology with three
         tests. The P2.3 row's SECOND predicted fix to fail on its own
         terms; the row now needs a carry-vs-stay RULING, pinned by the
         xfail test_a_roomless_split_wall_body_drags_as_one_run.
         TESTS CHANGED, all declared: the party-wall flip (route only,
         assertions unchanged); test_moving_a_room_does_not_distort_its_
         neighbour drives extract_room (follows the mousePress it always
         mirrored). Census 528 -> 536 (3 acceptance + 1 conflict pin +
         1 zoom pin + 3 gap tests), xfails 5 -> 4 net (party-wall and
         defect-30 flips out, P2.3 conflict pin in).

         THE PATRICK MINI-GATE (P4.2 is the first task under the ruling --
         the PR does NOT merge until this passes; ~15 min, stated
         expectations, Gate-3 style):
         1. EXTRACT: open planc1TestV5.json, right-click a room with
            shared walls -> Extract room. Expect: room reads floating
            (warm fill, dashed boundary, "(floating)" under the name); the
            plan keeps every wall; neighbours unchanged; no warning.
         2. FLOAT-MOVE: drag it ~500" away by its name. Expect: walls +
            doors + furnishings + region move as one unit; nothing else
            moves; nothing welds in passing.
         3. JOIN: place it beside existing walls -> right-click -> Join
            room into plan. Expect: coincident walls merge, no doubled
            wall, no duplicated openings; room reads placed.
         4. THE OLD WORKFLOW UNCHANGED: plain label-drag a PLACED room one
            bay over. Expect: exactly the old behaviour -- party wall
            stays with the neighbour, room re-merges on drop, furnishings
            stay put.
         5. UNDO back through all of it. Expect: each step reverses
            cleanly.
         6. DEFECT 30: body-drag a party wall at a 4-way corner. Expect:
            every room touching that corner follows; no stranded dashed
            outline.
         7. DEFECT 34: Edit > Review wall gaps... on planc1TestV5.json.
            Expect: the known 1.53"/6.003" pairs listed with distances;
            closing one 1.53" pair welds it; the 6" pairs left alone stay;
            the saved file is otherwise unchanged.
         8. FLOATING ROUND-TRIP: save while a room is floating -> close ->
            reopen. Expect: still floating, everything intact, and
            tools/validate_design.py on the saved file -> PASS/PASS.

P4.2+ mini-gate finding: DEFECT 30's FIRST CUT CORRECTED (item 6 caught it)
ruff:    clean
pytest:  527 passed, 7 deselected, 4 xfailed (sum 538 local; CI sees 536 --
         the two extra are Patrick's untracked examples/symmetricP2/P3.json
         picked up by the corpus validation, both green, not committed)
files:   walls.py (_plan_vertex_moves steps 1+4), tests/test_wall_move.py
         (pin revised), docs/CODE_REVIEW_v2.md (row 30 corrected), this file.
notes:   Patrick ran item 6 on symmetricP3 and the blanket follow tore a
         DIAGONAL across Foyer and Great Room -- their boundary at the
         corner is the CONTINUATION, which the anti-shear split holds
         still, so dragging their corner off it was the first cut's own
         error, screenshot on file (Screenshot 2026-08-01 162708.png).
         CORRECTED: the split makes the old corner TWO corners, and each
         room's corner goes with ITS OWN BOUNDARY -- run-bordered rooms
         follow the moved vertex; continuation-bordered rooms re-point to
         the stationary twin the split mints (now recorded in step 1).
         The pin is revised to the corrected expectation and renamed
         (test_a_dragged_corner_splits_by_each_rooms_own_boundary), with a
         no-diagonal assertion so the tear cannot come back. Fail-first:
         red against the first cut in a worktree ("borders the continuation
         but was dragged off it"), green on the correction. Verified on
         pristine symmetricP1: Foyer/Great Room outlines unchanged through
         a 24" down-drag, Dining/Kitchen resize, zero new off-axis edges
         (the four flagged are a pre-existing 0.3" skew at (582.3, 483.6)
         in the shipped example itself, below the weld band, identical
         before and after).
         NOTE for the re-run: symmetricP3.json still CONTAINS the damage
         from the bad-drag session -- re-cut it from symmetricP1 before
         re-running item 6, or drag and undo on the fixed build.

P4.2+ mini-gate finding 2: CLOSE_GAP STRANDED OUTLINES (item 7 + a drag)
ruff:    clean
pytest:  528 passed, 7 deselected, 4 xfailed (sum 539 local; CI 537 -- the
         two extra remain Patrick's untracked example files)
files:   walls.py (close_gap), tests/test_walls.py (invariant pin),
         docs/CODE_REVIEW_v2.md (row 34 corrected), this file.
notes:   Patrick closed symmetricP1's reviewed gaps, then dragged the
         M Bath/Lounge wall down -- and M Bath, Hall and Lounge drew dashed
         DIAGONALS to corners their walls no longer held (Screenshot
         2026-08-01 170311.png). Not deferred recalculation -- there is no
         later recalculation since P3.5, by design; outlines follow walls
         only through shared vertex IDENTITY, and close_gap's first cut
         broke exactly that: it folded WALL ends onto one anchor
         (share_coincident_ends) but left the OUTLINES holding coincident-
         but-distinct twins, so the next drag moved the walls' corner and
         stranded the rooms'. FIX: after the fold, every room on the floor
         re-adopts its walls' corner vertices (share_outline_vertices, the
         load path's own discipline, late-imported per the cycle rule).
         RECEIPTS, fail-first: the invariant pin (every outline corner IS
         one of its room's wall-end vertices, by identity) red against the
         first cut in a worktree, green on the fix; end-to-end headless on
         symmetricP1: both 6.003" gaps close (1 weld each at (379.4, 456)
         and (379.4, 654)), stranded corners 0, and the M Bath/Lounge 24"
         down-drag adds ZERO diagonals (the four flagged are the file's
         own pre-existing 0.3" skew at (582.3, 483.6), below the weld
         band, identical at load and untouched throughout).

P4.2+ mini-gate finding 3: THE MIXED CORNER (partial-side run coverage)
ruff:    clean
pytest:  529 passed, 7 deselected, 4 xfailed (sum 540 local; CI 538 -- the
         two extra remain Patrick's untracked example files)
files:   walls.py (_plan_vertex_moves step 4: mixed-corner step surgery;
         collapse_degenerate_outline_edges + release/close_gap call sites),
         tests/test_wall_move.py (step pin), docs/CODE_REVIEW_v2.md (row
         30, third finding), this file.
notes:   Patrick: clean gaps, drag the Master Suite / M Bath wall down --
         diagonal across Hall (Screenshot 2026-08-01 172305.png). NOT the
         stranding class (the invariant held, 0 stranded); a genuinely
         deeper case: the dragged run is Master Suite's WHOLE south side
         (x 30..330) but Hall's top side extends past the run's end
         (330..396, backed by the Clst|Hall wall -- a continuation, which
         correctly stays). Hall's corner at x=330 is run-backed on one
         adjacent edge and continuation-backed on the other; one corner
         cannot serve two stretches that now sit on different lines --
         follow tears the continuation stretch (the diagonal seen), stay
         tears the run stretch. FIX, outline surgery at drag start (the
         same moment the anti-shear split runs): the mixed corner becomes
         TWO corners joined by an OPEN step edge (wall: null, drawn dashed
         -- at insert time there genuinely is no wall on the jog; the
         stretched perpendicular wall covers it after the drag, so the
         dash-over-wall is a known presentational wrinkle, noted not
         hidden). Hygiene: collapse_degenerate_outline_edges drops
         zero-length edges -- the welded corner pair a closed gap leaves
         in a room that held both corners (the Hall doubled-corner residue)
         and a step whose drag ended where it began -- unbinding a wall
         whose only naming edge was the zero one.
         RECEIPTS, fail-first: the step pin (4-room replica: run-bordered
         rooms follow, Clst byte-still, Hall gains the OPEN step at the
         run's end, everything axis-aligned) red against the pre-fix tree
         in a worktree, green on the fix. End-to-end on symmetricP1: clean
         gaps -> drag Master Suite/M Bath 24" down -> 0 diagonals, 0
         stranded, Hall = (248.4,678)(330,678)(330,654)(379.4,654)
         (396,654)(396,714)(248.4,714) exactly, Clst untouched, doubled
         corner gone.

P4.2+ mini-gate: DEFECT 35 FILED (residual drag report, shelved), and the
         version label added so the next report carries its code identity
notes:   Patrick reported residual drag diagonals after the mixed-corner
         fix and shelved them; filed as register row 35 rather than lost.
         The replay of the exact sequence on the fixed tree is clean twice
         over (outline edges AND painted cue segments), the reporting
         session's code identity is unverifiable (it predates the label),
         so the row records the report, the clean replay, both candidate
         explanations (stale process vs uncovered gesture), and the
         re-open protocol: reproduce with the status-bar version label
         visible (launch >= a1e6083) plus the gesture sequence. The P4.2
         mini-gate re-run decides: confirmed -> fixed before the PR
         merges; unreproduced with the label -> closed as stale-process.
         (a1e6083: status bar + About now show "v1.2 - <branch> @ <sha7>",
         captured at LAUNCH, with two pins -- names the checkout, and
         launch-stable.)

P4.2+ mini-gate finding 5 (via fiveRoomDragSplit.fpm): a three-bug cascade
ruff:    clean
pytest:  534 passed, 7 deselected, 4 xfailed (sum 545)
files:   extract.py (join merges at SHARE_TOL), rooms.py
         (split_partially_covered_edges, junction-degree guarded),
         walls.py (run-wide tee gather; release repair pass),
         tests/test_extract_join.py (macro pin),
         examples/fiveRoomDragSplit.fpm (Patrick's reproduction), this file.
notes:   Patrick's macro (drag R2 out/back 6" offset, slide the R3|R4 wall,
         slide the R1|R3 wall) tore R1 and R4 diagonal. THREE distinct
         bugs, each measured before being touched:
         (a) JOIN MERGED AT THE WRONG TOLERANCE: merge_wall's default
         perp_tol is the 6" auto-coalesce snap, so a room dropped a
         gesture-width off SNAPPED ITS NEIGHBOURS' WALLS onto its own line
         -- R4's north wall physically moved 6" to meet the offset R2,
         stranding R4's outline. The join now merges at SHARE_TOL (0.6",
         vertex_weld_in): at or below it two lines ARE one; beyond it
         nothing moves -- the join's own stated rule, now obeyed by its
         merge step.
         (b) PARTIAL COVER IS A LATENT TEAR: an outline edge NAMED by a
         live wall that covers only part of it follows at only one corner
         on the next drag -- the diagonal. split_partially_covered_edges
         (release + join): the coverage boundary becomes a real corner
         HOLDING THE WALL'S OWN END VERTEX, so later drags carry it by
         construction; the remainder re-binds or stays honestly open.
         GUARDED BY JUNCTION DEGREE: only a vertex held by 2+ wall ends
         splits -- a DANGLING end mid-edge is the deliberately-opened side,
         whose openness stays DERIVED so dragging the end back re-closes
         it (test_closing_gap_refuses_and_relocks caught the unguarded
         version freezing the gap open; it passes unchanged now).
         (c) THE TEE GATHER TESTED ONLY SELF'S BODY: an end resting
         mid-span of another RUN member was invisible, so the run slid out
         from under a mid-run corner, leaving it floating. Body landings
         now test against every run wall -- the run slides as one line.
         RECEIPT, fail-first: the macro pinned VERBATIM
         (test_drag_split_macro_keeps_every_room_rectilinear -- after
         EVERY line, nothing diagonal and no edge names a wall that does
         not span it), red against the pre-fix tree in a worktree, green
         on the fixes; the full replay is clean at every step, R1 ending
         as the correct stepped shape, R4 with the correct tee corner.
         Census 544 -> 545, sums reconciling.

P4.2+ mini-gate finding 6 (via fiveRoomDragSplit2.fpm): three more, fixed
ruff:    clean
pytest:  535 passed, 7 deselected, 4 xfailed (sum 546)
files:   rooms.py (repair_edge_bindings, grown from rebind_dead_edges:
         upgrade-only rebind of live-but-outspanned edges; the deliberate-
         open guard moved from junction degree to _corners_unlocked),
         walls.py (_split_outline_landings; spike collapse in
         collapse_degenerate_outline_edges; release repair re-adopts
         wall corner vertices), tests/test_extract_join.py (macro pin),
         examples/fiveRoomDragSplit2.fpm, this file.
notes:   Patrick's 13-gesture macro seeded and tore through THREE more
         mechanisms, each introspected to its exact site before touching:
         (a) MISBOUND EDGE: an edge named a collinear NEIGHBOUR wall that
         covered none of it while the exactly-matching wall sat right
         there (_edge_wall's partial-cover acceptance grabbed the wrong
         candidate during an earlier repair). repair_edge_bindings now
         also fixes live-but-outspanned names, UPGRADE ONLY (rebind solely
         when the candidate fully spans -- a legitimately short detached
         wall is never swapped). The junction-DEGREE guard from finding 5
         was WRONG and is replaced by the explicit workflow flag
         (_corners_unlocked): a slid wall can leave a genuinely dangling
         structural end mid-edge.
         (b) OUTLINE-CORNER TEE: a pure room corner resting mid-span on
         the run wall's BODY -- no wall end there at all, so the tee
         gather cannot see it -- and the run slid out from under it.
         _split_outline_landings (drag start, beside the wall-end tee
         pass): cut the run wall at the corner, point every coincident
         outline corner at the split vertex; identity is what rides.
         (c) COLLINEAR SPIKE: a zero-area overshoot (A->B then straight
         back) left where a stationary corner was passed by its sliding
         side; collapsed as a degenerate, iteratively, walls unbound when
         their last naming edge goes.
         Release repair also re-adopts wall corner vertices
         (share_outline_vertices) so coincident-but-distinct outline
         corners cannot accumulate.
         RECEIPT, fail-first: the macro pinned VERBATIM (after EVERY line:
         nothing diagonal, no edge names a wall that does not span it) --
         red against 6f3e2b9 in a worktree, green here. Both earlier
         macros replay with zero violations (no regression). Census
         545 -> 546, sums reconciling.

P4.2+ tooling & floors run, 2026-08-02 (sub-commits 16-23; consolidated
         here, details in the commit messages, each at a full green gate)
pytest:  543 passed, 7 deselected, 4 xfailed (sum 554 local; CI 552 --
         the two extra remain Patrick's untracked symmetricP2/P3 examples)
THE RECORDER, made whole (16-19) -- keyboard capture was broken THREE
         separate ways, each found by Patrick's restart-and-retest and
         each now pinned by a test replicating the REAL Qt delivery order:
         (16) shortcut-consumed chords never arrive as KeyPress ->
              capture ShortcutOverride too;
         (17) the `obj is viewport` mouse branch ran FIRST and ate every
              canvas keystroke (keyboard recording had never worked in
              the app); keys are dispatched by event TYPE now. ^O "path"
              records File>Open with its chosen file (hook pattern);
         (18) the QWindow-level delivery (which precedes widget delivery
              and never passes _belongs_to_main) SET the de-dupe guards
              before the eligibility check, poisoning the recordable
              delivery -- eligibility first, state second;
         (19) CARET_SHORTCUTS: ONE module-level table drives recorder AND
              runner -- adding a menu shortcut is one row, a design-guard
              test fails on a row naming a missing MainWindow method.
              ^+S "path" (Save As, hook), ^S soft-skips with no current
              file, unnamed chords record nothing.
FLOORS, per Patrick's spec (20-23; 20's cycle design was superseded by
         his fuller spec ONE SESSION LATER, stated not blended):
         (21) Floors menu = Select... (^F) / New... (^+F) / floors
              (default FIRST, "name (Default)" = the roster's first
              whatever its alias) / ghost toggle. ONE popup surface
              (^F, status-bar label, right-click on blank canvas except
              the Room tool) with the default PRE-HIGHLIGHTED so bare
              ENTER selects it. Macro: ^F "name" switches, BARE ^F ->
              default, ^+F "name" creates (IDEMPOTENT on replay); the
              popup route records PUP ... # ^F "name" (comment form).
         (22) floors paint in Z-BANDS: active floor = band 0 (always on
              top; new items land on top with no re-sync), ghosts on
              negative bands in a user-arranged display stack (per-floor
              Move to front/back (display); view state, not serialized).
              Applied as a DELTA so within-floor z is untouched -- NOT a
              fifth z scheme; defect 11's P4.5 collapse should absorb the
              band as the one between-floor term. Reference backdrop to
              the true bottom. Fail-first receipt: "assert 5.0 > 5.0" --
              all floors had shared one z.
         (23) ATMOSPHERIC DEPTH: active floor full contrast, each visible
              floor beneath fades by stack depth (0.60/0.39/0.25...,
              floor 0.18) via per-item opacity -- no paint() touched.
              Quick flip: Ctrl+PgDown/PgUp cycle; recording stays
              deterministic (the hook emits the resulting ^F token).
STANDING:  PR #4 remains on HOLD for the Patrick mini-gate (items 1-8, on
         a fresh launch; findings 1-6 all fixed and pinned). Defect 35
         stays OPEN until Patrick confirms the macro reproductions
         covered everything on his shelf. _perimeter_span's re-argument
         to P4.4 stands in the register. Noted follow-up, not built:
         per-floor visibility (show a chosen subset while editing).

P4.2  MINI-GATE PASSED 2026-08-02 -- defect 35 closed, census hygiene,
         P4.2 TICKED; PR #4 merges as a merge commit on this record
ruff:    clean
pytest:  541 passed, 7 deselected, 4 xfailed (sum 552 -- and LOCAL == CI
         for the first time since the mini-gate findings began: Patrick
         removed his two untracked symmetricP2/P3.json, so the 554/552
         delta the record has carried line-by-line is GONE)
files:   examples/multifloor.fpm (committed at P4.2(25)),
         docs/CODE_REVIEW_v2.md (row 35 closed), this file (the tick +
         this block).
notes:   Patrick ran the mini-gate on a FRESH LAUNCH with the status-bar
         version label verified at the launch sha -- ALL 8 ITEMS PASS.
         (The label discipline the stale-process round bought, doing its
         job on the very run it was built for.)
         DEFECT 35 CLOSED on the reporter's confirmation, per the row's
         own re-open protocol: the shelf is EMPTY -- nothing remains on
         the "still some problems with the drag" report beyond the
         harvested findings 4-6. The residuals were neither stale-process
         nor unreproducible: the macro loop converted them into findings
         5 and 6 (six mechanisms, fixed against measured reproductions,
         pinned verbatim); the reporter's confirmation retires the
         report, which the clean replay alone never could.
         MULTIFLOOR.FPM RULING, asked and recorded: CONVENIENCE FILE,
         not pinned as a regression test -- the floors/token machinery
         keeps its existing unit pins as its guard.
         P4.2 ticked in the Status table citing PR #4 and the sub-commit
         range dfd30af..ed9286c + this record commit (26 in all). The
         snapshot is re-cut AT THE MERGE, on main, as the next action.

P4.3(1) the pre-work census + both rulings recorded (branch p4.3-shuffle
         from main@778b4b9; read-back answered 2026-08-02, work begins)
ruff:    clean
pytest:  (census commit -- code untouched; trailer below is the branch-point
         gate)
files:   this file only.
notes:   RULING 1 (the P2.3 row) -- STAY, with the amendment: the settled
         anti-shear rule keeps the topology; the row closes as
         superseded-by-ruling, and the xfail pin is REPLACED BY TWO HARD
         PASSES, not deleted: (i) the stay contract promoted (a room-less
         body drag moves the grabbed segment only, continuation untouched
         -- the topology's one owner, asserted rather than implied);
         (ii) the HEAL (with auto_coalesce on, the room-less degree-2
         collinear seam an undo leaves dissolves at the next pass, and
         the merged wall body-drags as one) -- the restoration the row
         wanted, arriving through the document instead of the gesture.
         The workaround line survives only for the shuffle/
         auto_coalesce-off world, where staying split is honest.
         Executed at P4.3(5).
         RULING 2 (defect 25's deferred policy, all three questions) --
         TIERED: jamb within the gesture's join tolerance -> snap the end
         to the jamb and weld there (a legitimate gesture-tolerance move;
         gestures are where the 9" tolerance is allowed to act); no jamb
         in tolerance -> land-unwelded-and-report (P4.1b's message, the
         standing fallback). NEVER split (manufactures a homeless-door
         reported-fault document from a live gesture; R2c reserved that
         totality for loads, where no user is present), NEVER refuse (a
         gesture that undoes itself is defect 17's disease). It is
         AUTO_WELD'S decision -- no fifth flag (the doorway case is a
         sub-case of the weld pass's target-finding; the editing_modes
         family is complete at four). Under shuffle the landing never
         welds and the message is SUPPRESSED (an unwelded end is the
         mode's intended state, not a tear); the deferred information is
         delivered at the EXPLICIT JOIN, which reports anything it could
         not place or weld through the defect-6 vocabulary.
         THE CENSUS, measured against main@778b4b9 (the task line's four
         flags, one live and three dead):
         * auto_coalesce (LIVE): internal gates walls.py:537 (merge_wall)
           / :557 (merge_all); callers view.py:504 (draw release),
           walls.py:1952 (drag release), mainwindow.py:915 (ungroup),
           planio.py:200 (legacy load), extract.py:211 (EXPLICIT join).
           FINDING: the explicit join routes through the gated merge_wall,
           so auto_coalesce off (or shuffle) would leave a Join with
           doubled walls -- the join must merge regardless (the schema's
           own "rooms are joined explicitly"); fix = a force param for
           explicit callers. normalize_walls stays ungated by design.
         * auto_weld (dead): ONE gesture site -- view.py:506, the
           draw-release weld_wall_ends. Stated non-sites: the end-drag
           release never welds by design (walls.py:1940 "left exactly
           where the drag put it"); imageio.py:180 weld_scene is defect
           19's import repair; close_gap is defect 34's explicit review
           op; join/normalize are explicit. Ruling 2's jamb-snap tier
           lands on BOTH release paths (draw + end-drag), gated by
           effective auto_weld; the end-drag jamb-snap is a deliberate,
           narrow exception to "never snapped on release" and carries
           the fail-first receipt.
         * auto_bind (dead): NO gateable automatic site exists today --
           measured over all 9 bind_room_walls/repair callers: Room tool
           view.py:280, paste mainwindow.py:1348, room_boolean :849,
           undo restore :658 (constitutive of explicit gestures); load
           paths planio.py:235, csvio.py:148, macro.py:413; the explicit
           join extract.py:218; and the release repair family
           walls.py:1968-1975, which is tear-repair of derived state and
           is exempted DELIBERATELY (gating it would reintroduce the
           mini-gate's stranding class). auto_bind lands plumbed
           (SETTINGS, document, UI) with an empty enforcement surface,
           honored implicitly under shuffle because a floating room
           reaches no bind at all. Stated, not invented.
         * shuffle (dead): four touchpoints -- (a) implies the other
           three off (one effective-flag accessor, config.py, so every
           gate asks the same question); (b) the label-drag drop-join
           rooms.py:884-891: under shuffle a MOVED room stays floating
           (the task line's "joins nothing automatically"); a click that
           never moved still ends placed (P4.2's "a click must not leave
           a room afloat" -- needs a genuine moved flag, today's
           _moving_room is mode, not displacement); (c) suppresses the
           P4.1b doorway message per ruling 2; (d) the toolbar toggle
           (mainwindow.py:143 is the toolbar).
         * emit/apply: bridge.py:709 emit hardcodes the editing block ->
           reads live SETTINGS; bridge.py:891-901 apply already iterates
           DEFAULT_SETTINGS over editing.* -- adding the three keys makes
           load correct BY CONSTRUCTION; importer.py:333's conversion
           defaults are RIGHT for legacy docs (no shuffle concept to
           preserve) and stay; planio.py:144's legacy apply iterates
           DEFAULT_SETTINGS, so the new bool keys default correctly on
           v1-v4 loads.
         Order of work (per the go): plumbing -> gesture gating with the
         tiered weld -> acceptance -> ruling 1's tests + row closure.
         Merge on green CI + Patrick's acceptance; no mini-gate.

P4.3  implemented (branch p4.3-shuffle, sub-commits: a6ded30 census +
         rulings, e9abeb3 plumbing, 2e11a05 gesture gating + tiered
         weld, 0f5642f acceptance, + this record commit. PR opens on
         this commit; MERGE AWAITS PATRICK'S ACCEPTANCE -- the reviewer
         ticks the box, not the implementer.)
ruff:    clean
pytest:  558 passed, 7 deselected, 3 xfailed (sum 568, all three modes,
         every sum reconciling; trailer in this commit's message)
files:   config.py (three flags join DEFAULT_SETTINGS; editing_enabled,
         the ONE effective-flag accessor -- shuffle implies the auto_*
         passes off without rewriting them), walls.py (merge gates
         through editing_enabled; merge_wall force=True for explicit
         callers; snap_end_to_doorway_jamb; end-drag release wires
         snap + gated report), view.py (draw release: gated weld,
         tier-1 snap, gated report), rooms.py (label-drag drop under
         shuffle: moved -> stays floating, click -> still placed, via
         a real displacement flag), extract.py (join merges force=True;
         join-time doorway reporting, unconditional), bridge.py
         (editing block emitted from live SETTINGS; v5 apply re-syncs
         the editing UI), dialogs.py (auto_weld/auto_bind checkboxes),
         mainwindow.py (Shuffle toolbar toggle, text-only QToolButton;
         _sync_editing_ui on every load path; dirty on flip),
         tests: test_shuffle.py (NEW, 11), test_walls.py (4 doorway-
         policy gui tests), test_wall_move.py (xfail replaced by the
         two ruling-1 hard passes), register row (P2.3 closure), this
         file.
notes:   ACCEPTANCE MET, as the task line states it: with shuffle on, a
         floating room dragged ACROSS the plan -- one gesture through
         the real handlers, stepped straight through the anchor room's
         footprint -- leaves both unchanged, check() deep-clean at
         EVERY step (I11 exempts the floating room; I12/I14 exemptions
         hold), the door survives, the plan-side furnishing stays put.
         RULING 1 EXECUTED: the xfail deleted, the two hard passes in
         (stay contract asserted; the heal -- auto_coalesce dissolves
         the room-less degree-2 seam at the next merge pass and the
         merged wall drags as one); the P2.3 Known-regressions row
         CLOSED as superseded-by-ruling, its workaround column alive
         only for the shuffle/auto_coalesce-off world. Census: xfails
         4 -> 3 (the pin retired by ruling, stated).
         RULING 2 EXECUTED: the tiered doorway weld at both release
         paths (snap-to-jamb within JOIN_TOL, else the P4.1b message,
         never split, never refuse), auto_weld's decision with no fifth
         flag; shuffle suppresses the message (an unwelded end is the
         mode's intended state); the explicit join delivers deferred
         information through the defect-6 channel unconditionally. The
         P4.1b pins run UNCHANGED (their landing is 16" from either
         jamb, outside the tolerance -- tier 2 IS the old behaviour).
         RECEIPT, fail-first (worktree at e9abeb3, new tests copied in
         unchanged): all five behaviour flips RED on their verdict
         asserts with preconditions held (the drawn jamb case lands
         measurably at (108, 0) inside the door and fails on
         "108.0 == 104.0 +/- 0.1"; the shuffle label-drag fails on
         'placed' == 'floating'); the click-stays-placed pin passes
         BOTH eras (preservation, not a flip). All green here.
         TESTS CHANGED, declared: the xfail
         test_a_roomless_split_wall_body_drags_as_one_run DELETED by
         the ruling it existed to force (replaced, not relaxed).
         auto_bind lands PLUMBED with an empty enforcement surface
         (the census's measured conclusion, recorded not invented).
         NOTED follow-ups, not built: no macro token for the shuffle
         toggle (the recorder records nothing for it -- same class as
         the pre-P4.2 unnamed chords); a shuffle keyboard shortcut.
         Patrick wants ten minutes with the toggle after the merge.

P4.3(6) Patrick's finding: THE FUSE STRAGGLER (dragWallFuseStraggler.fpm)
ruff:    clean
pytest:  559 passed, 7 deselected, 3 xfailed (sum 569, every sum
         reconciling; trailer in the commit)
files:   extract.py (extract_room step 1b), examples/
         dragWallFuseStraggler.fpm (Patrick's reproduction, committed),
         tests/test_extract_join.py (the verbatim macro pin),
         docs/CODE_REVIEW_v2.md (row 36), this file.
notes:   Patrick: moving the fiveRoomTest design with his macro "leaves
         a wall behind that should not have been copied out."
         REPRODUCED HEADLESS VERBATIM, introspected to three measured
         links (register row 36 has the full chain): an offset join
         round-trip (6" off, by design) + a plain CLICK's release merge
         (6" perp_tol, across a seam that IS degree-2 by identity --
         the horizontals pass mid-body, so no planner rule broke) left
         R2 BOUND to a fused five-room column that no R2 outline edge
         names. extract_room then partitioned by the OUTLINE (step 1)
         but floated the BINDING list (_translate moves room.walls) --
         two definitions of "the room's walls" -- so the column rode
         out bodily with floating R2 and the return join stranded it.
         FIX at the operation whose contract broke: step 1b releases
         every bound wall no outline edge names (the outline is the one
         definition, P3.5); the wall stays with the plan.
         RECEIPT, fail-first: the macro pinned verbatim, red against
         b23d685 in a worktree on "wall count 15 != baseline 16: a wall
         was minted or stranded", green on the fix; fixed end state ==
         the fresh load (16 walls, areas identical, zero open edges,
         check() clean). The pin replays at the DEFAULT window geometry
         (the macro was recorded there; the two fiveRoomDragSplit pins
         replay at 1400x1000+fit for the same reason, stated in each).
         PRODUCER NOTED, not fixed: the release-merge's unconditional
         rebind of absorbed walls' rooms can still mint binding-without-
         naming; extract is immune now, rebind semantics are P4.5's.
         Census 568 -> 569.

P4.3+ the three ruled dispositions, one commit (post-merge, on main;
         ruled by Patrick 2026-08-03 with the acceptance)
ruff:    clean
pytest:  (trailer in the commit; census 569 -> 570, the watch test)
files:   dialogs.py (auto_bind checkbox removed),
         tests/test_extract_join.py (the row-36 watch),
         docs/CODE_REVIEW_v2.md (standing disposition + row 36 carry
         note + row 37), this file.
notes:   (a) AUTO_BIND LEAVES THE UI: modelled, emitted and plumbed
         with no gateable site as of P4.3; the control returns when one
         exists. Standing disposition in the register QUOTES the
         census reasoning verbatim. Nothing changes in SETTINGS, the
         document block, or editing_enabled -- a checkbox promising
         behaviour nothing enforces is what goes.
         (b) ROW 36's PRODUCER: carried to P4.5 CONDITIONALLY on the CI
         watch (test_the_merge_rebind_producer_is_watched): its
         preconditions pin that the producer still mints binding-
         without-naming (red -> re-argue the row before touching the
         test); its verdict pins that extract's step 1b releases the
         state (red -> the guard regressed, caught by CI not a field
         macro). If the watch goes, the carry ruling goes with it.
         (c) THE SHUFFLE TOGGLE'S MISSING TOKEN/SHORTCUT: filed as
         register row 37 -- a user-facing mode the recorder cannot see
         is a gap in the one-table CARET_SHORTCUTS design; a replayed
         session that toggled shuffle replays with the wrong mode,
         silently. ARGUED TO P4.4 (my call, invited): earliest next
         task, one table row + a chord choice, and P4.4's duplicate-as-
         template work is exactly where floating rooms and shuffle get
         exercised together in recorded macros.

P4.3+ Patrick's field report: THE PARKED-FLOAT FURNISHING STEAL (row 38)
ruff:    clean
pytest:  566 passed, 7 deselected, 3 xfailed (sum 576, every sum
         reconciling; trailer in the commit)
files:   rooms.py (sentinel + press guard), extract.py (prev-aware
         capture with claimed-exclusion; join resets to None),
         mainwindow.py (_set_shuffle re-baseline),
         tests/test_shuffle.py (6 pins + the acceptance's declared
         change), docs/CODE_REVIEW_v2.md (row 38), this file.
notes:   REPRODUCED before his clarification arrived, mechanism
         measured: init [] == captured-empty, falsy lazy-capture guard
         -> a parked float re-captured at EVERY press by whatever it
         hovered over. THE CONTRACT, ruled: (a) floating captures the
         furnishings inside, any mode; (b) under shuffle EVERY dragged
         room keeps its furnishings (plain non-shuffle drag still
         leaves them -- P4.2's trait, scoped); (c) no mid-shuffle
         pickup ever; the ONE re-baseline is the shuffle-ON toggle --
         carried stays its own, inside-and-unclaimed becomes assigned,
         claimed-by-a-placed-room is never taken.
         TESTS CHANGED, declared: the P4.3 acceptance's furnishing
         assert flips from stays-put to rides (ruling (b) reached the
         path it pinned); red pre-fix with the three new flips, three
         preservation pins pass both eras.
         Census 570 -> 576.

P4.4(1) the four rulings recorded + the pre-work census (branch
         p4.4-concept-duplicate from main@e4b2028; read-back answered
         2026-08-03, work begins)
ruff:    clean
pytest:  (census commit -- code untouched; branch-point gate trailer in
         the commit)
files:   this file only.
notes:   THE FOUR RULINGS, verbatim in substance:
         (1) CONTINGENCY CONFIRMED -- duplicate is built on the extract
         machinery per section 4. Consequence executed at P4.4(3):
         _copy_spec and _perimeter_span DIE (the carried census note's
         contingency resolves YES); Copy/Paste room rewire to the new
         op; the clipboard path's third definition of "the room's
         walls" (bounding_walls proximity + _perimeter_span trim) dies
         with them, so P4.5 inherits the binding/outline duality with
         the clipboard consumer RESOLVED.
         (2) CREATE-BY-TYPED-DIMENSION mints a FLOATING, WALL-LESS room
         carrying nominal_size -- a dialog off the Room tool AND from
         the menu. category: concept; I13 (concept must be floating)
         is the guard.
         (3) FILE MENU: "Load template room..." and "Save template
         room..."; Save enabled ONLY when a floating room is selected
         (highlighted).
         (4) THE SHUFFLE CHORD IS ^H (register row 37's fix, this
         task's first code piece).
         CENSUS (measured at the read-back + this commit):
         _perimeter_span rooms.py:314-337 (24 lines), sole caller
         _copy_spec rooms.py:339-373, sole caller the context-menu
         Copy (rooms.py:947 -> win.room_clipboard), sole consumer
         paste_room mainwindow.py:1348-1388 (rebuild + detect_room +
         bind_room_walls), surfaced at view.py:530. bounding_walls
         SURVIVES (report/inventory callers rooms.py:517,:575,
         mainwindow.py:918). Schema ground already present:
         room.nominal_size ("Never authoritative -- the outline is"),
         category concept, I13 in validate.py; model/bridge ride
         nominal_size verbatim (bridge.py:95 names P4.4). The macro
         table: CARET_SHORTCUTS one-row design, hook pattern on_floor/
         on_open; H unclaimed.
P4.4  implemented (branch p4.4-concept-duplicate, sub-commits 868e315
         census + rulings, ef74e11 the ^H chord + token, 8f3382b
         duplicate-as-template, d02d5ea concept rooms, + this record
         commit. PR opens on this commit; MERGE AWAITS PATRICK'S
         ACCEPTANCE -- the reviewer ticks the box.)
ruff:    clean over floorplanner/ + tests/ (the full-tree run is red only
         on viewer/fp3d.py, Patrick's parallel WIP, staged in the index
         and deliberately untouched by this branch -- stated, not
         counted green; its packaging is its own branch)
pytest:  588 passed, 7 deselected, 3 xfailed (sum 598, all three modes,
         every sum reconciling; trailer in the commit)
files:   design/template.py (NEW), rooms.py (make_concept_room;
         category/nominal_size modelled; the wall-less label drag;
         _copy_spec + _perimeter_span DELETED, 59 lines), planio.py
         (room_template / insert_room_template / duplicate_room /
         save+load_template_path / the interactive pair /
         selected_floating_room), mainwindow.py (File menu pair with
         the ruled enable rule, Rooms > New concept room...,
         new_concept_room, paste_room rewritten, _sync_template_action,
         toggle_shuffle / set_shuffle_mode), dialogs.py
         (ConceptRoomDialog), view.py (the Room-tool blank-canvas menu),
         macro.py (^H row + on_shuffle hook), design/bridge.py
         (category + nominal_size modelled in emit AND apply),
         tests: test_template.py (NEW, 11), test_concept_rooms.py
         (NEW, 8), test_shuffle.py (+3), test_outline.py (rewritten
         guard), register (row 37 + the carried census note), this file.
notes:   ACCEPTANCE MET, as the task line states it: a one-room file
         validates against the SCHEMA and all fifteen invariants and
         loads into an existing design as a FLOATING room, the host
         design untouched (test_save_and_load_template_room builds a
         SECOND MainWindow, so "an existing design" is genuinely
         another document rather than the same scene).
         THE INHERITED QUESTION ANSWERED YES, and the family is gone:
         _copy_spec + _perimeter_span deleted (59 lines), and with them
         the clipboard's THIRD definition of a room's walls. P4.5
         inherits the binding/outline duality with its clipboard
         consumer RESOLVED, which is what its rulings assumed.
         ONE MECHANISM, THREE WORKFLOWS: room -> one-room document ->
         floating room. A clipboard between the halves = Copy/Paste; a
         FILE between them = Save/Load template; back to back =
         Duplicate. The merged document goes through the ONE apply
         path, so an inserted room arrives by exactly the route a
         loaded file does.
         WHY FLOATING IS STRUCTURAL, not menu polish: the level walk
         gives a floating room its own vertex namespace and its own
         walls (I12), so the subset {room, the walls its OUTLINE names,
         their vertices, its furnishings} is CLOSED. A PLACED room is
         cut out through the REAL ops -- extract, template, join back
         -- whose zero-offset round trip IS the P4.2 label-click path;
         pinned by snapshot byte-equality across the operation.
         CONCEPT ROOMS: category + nominal_size MODELLED on the item
         (the P4.2 placement pattern, next field family) so a room the
         app itself creates can carry them; the name heuristic stays as
         the FALLBACK, pinned. I13 holds BY CONSTRUCTION (the factory
         cannot mint a placed concept room) and I11 exempts the class,
         so a sketch unit parks over the plan legally.
         FIXED IN PASSING, same class as the P4.3+ steal: the label
         drag required self.walls, so a WALL-LESS room's region stayed
         behind while its label wandered off.
         TESTS CHANGED, declared: test_copying_a_room_does_not_carry_
         its_geometry now asks its guard of the template DOCUMENT (the
         payload that also goes to disk -- the stronger place); paste
         lands a FLOATING room centred on the click rather than a
         placed one snapped to the grid.
         ROW 37 CLOSED with the ruled ^H chord (sub-commit 2).
         Census 576 -> 598.

OUT-OF-SEQUENCE, 2026-08-04: THE 3D VIEW POPUP (branch viewer-popup)
         NOT migration work, and recorded here precisely BECAUSE it is not:
         it landed between P4.4 and P4.5 rather than as a phase task, and
         it TOUCHES THE APP STARTUP PATH -- floorplanner/app.py, which no
         Phase-4 task has needed to open. A change to the first ten lines
         the process runs deserves a row in the sequence it stepped
         outside of, or the next person reading this log will find app.py
         changed by nobody.
ruff:    clean
pytest:  594 passed, 7 deselected, 3 xfailed (sum 604; trailer in the
         commits) -- census 598 -> 604, +6: five for the popup's own
         discipline and one more when the surface-format guard grew a
         BEHAVIOURAL test (simulate the missing import) beside the
         source assertion for the ordering.
files:   viewer/fp3dq.py (Plan3DQuickWidget extracted from main(), which
         becomes a caller), viewer/scene.qml (NEW -- the QML leaves the
         inline temp file), viewer/fp3d.py + viewer/system-checker.py
         (lint at source), viewer/VIEWER_NOTES.md (section 5), app.py
         (set_3d_surface_format), mainwindow.py (show_3d_view),
         view.py + levels.py (the two blank-canvas menus),
         pyproject.toml (scene.qml as package-data),
         tests/test_viewer_popup.py (NEW, 6).
notes:   THE STARTUP CHANGE, stated plainly because it is the part with
         blast radius: QSurfaceFormat.setDefaultFormat(QQuick3D.ideal
         SurfaceFormat(4)) MUST run before the QApplication exists (Qt
         reads the default format at GUI init), so it cannot live in the
         viewer with the rest of the Qt Quick 3D code -- main() is the
         one place guaranteed to be earlier. It is extracted as
         set_3d_surface_format() and GUARDED: the 3D stack is an optional
         extra, and an unguarded import at the entry point would make
         `pip install -r requirements-viewer.txt` mandatory just to
         launch the editor. Pinned by SIMULATING the missing import (the
         call returns False rather than raising) plus a source assertion
         for the ordering, which no runtime test can observe without
         building a second QApplication.
         READ-ONLY IS THE ACCEPTANCE: the popup reads design_document() --
         the SAME producer _write_plan writes, so no second definition of
         the plan was introduced -- and the walk's warning channel is
         suppressed for that one call, because an unwelded-end report
         belongs to the edit that tore the network and the 180 ms
         debounce walk owns it. Pinned against a genuinely SAVED plan:
         dirty flag, snapshot, and wall/room counts all unchanged, with
         any warning promoted to an error.
         ONE WIDGET, ONE QML: the CLI tool and the popup render through
         Plan3DQuickWidget and scene.qml, so neither can drift from the
         other. w._keep survives the extraction and is why -- QML holds
         no Python reference to the geometry.
         MENU PLACEMENT: appended to the blank-canvas right-click only on
         the RIGHT-CLICK route; ^F and the status-bar label stay a pure
         floor selector (P4.2's one-popup-surface spec is about floor
         SELECTION, and a chord named "select a floor" should not offer a
         renderer).
         CI's py3.10 leg earned its keep on the first change that gave it
         something to find: a tomllib import (3.11+) in the new test.
         MERGE HELD FOR PATRICK'S 8-ITEM SMOKE TEST and the reviewer's
         ruling; merge commit, not squash.

P4.5(0) THE RULINGS, recorded BEFORE any code (branch p4.5-groups-zorder
         from main@adaa519). Patrick ruled all of sections 2-4 of the
         read-back plus three amendments; the census that preceded them
         is in the read-back and its measured numbers are used below.

RULED (2a) DEFORM -- RATIFIED AS A CONSEQUENCE, NOT CHOSEN AS A POLICY.
         Under vertex identity a room holding a moved corner follows
         BECAUSE THE CORNER MOVED; stay-put is the option that would need
         machinery built to hold a room back from corners it holds. So:
         build no hold-back. And when test_a_clipped_band_leaves_every_
         room_coherent passes, the log says it passed AS A CONSEQUENCE OF
         THE MECHANISM rather than claiming a fix -- that distinction is
         the record's to keep, not the code's.
         ASKED WITH IT: which invariant catches a room whose OWN outline
         crosses itself after a large deforming move?
         ANSWERED, and it is NOT a gap: I5b -- "room-outline
         self-intersection", validate.py:155-168, O(edges^2) per room.
         It exists and it is exact.
         THE FINDING IS ITS REACH, not its absence, and it is sharper
         than "reports": I5b is one of the THREE DEEP-ONLY checks
         (validate.py:77), so shadow mode's always-on twelve never sees
         it while editing -- but save_path runs _verify_or_report("save",
         deep=True) and REFUSES TO WRITE when it fails. So a deform that
         self-intersects is SILENT AT THE GESTURE and then BLOCKS THE
         SAVE: the user learns at the moment they try to keep their work,
         which is the worst possible ordering. (The refusal itself is
         deliberate and correct -- P4.1's "do not write a corrupt plan"
         -- so the fix is NOT to relax it.)
         PROPOSED, for Patrick's ruling and NOT built here: run I5b
         SCOPED TO THE ROOMS A GROUP MOVE ACTUALLY CARRIED, at bake, and
         report through the status channel. Scoped, it is cheap (edges^2
         over a handful of rooms, not the plan), it fires at the gesture
         that caused it, and the deep sweep stays exactly where it is.
         The operation stays allowed either way -- this is about WHEN the
         document speaks, not whether the gesture is permitted.

         AMENDED 2026-08-05, AND THE AMENDMENT IS TO THIS RULING'S OWN
         PREMISE. The ordering stated above -- "SILENT AT THE GESTURE and
         then BLOCKS THE SAVE" -- is FALSE AS SHIPPED, and the error is in
         the second half. save_path does call _verify_or_report("save",
         deep=True), but verify() returns None immediately unless shadow
         mode is on (design/verify.py:210), and app.py:47 sets the env var
         ONLY for --verify-design. So the refusal is a diagnostic-mode
         behaviour, never the default launch.
         MEASURED on one corrupt scene, the fragment case, three ways:
           FP_VERIFY_DESIGN unset  -> the save WROTE the file, carrying
                                      I5b x1 and I11 x3
           FP_VERIFY_DESIGN=1      -> refused
           FP_VERIFY_DESIGN=deep   -> refused
         WHAT ACTUALLY SHIPS is therefore neither the ordering feared here
         nor the one proposed: report_self_intersections DOES fire by
         default (confirmed with the var unset), so the I5b half speaks at
         the gesture as ruled -- and the I11 half, room-vs-room overlap,
         speaks NOWHERE AT ALL. Not while editing (deep-only), not at the
         save (no refusal without the flag).
         The proposal above was therefore right for the wrong reason: it
         treated the save refusal as the backstop that made a gesture-time
         report merely better-timed. There is no backstop. Row 49 carries
         the repair; this ruling's own conclusion -- report at the gesture,
         do not block -- is UNCHANGED, and is now the only thing standing
         between the user and an unreported overlap.
         Evidence: docs/evidence/defect23-fragment.json, reproducible with
         docs/evidence/defect23_fragment_probe.py.

RULED (2b) DO NOT PROMOTE. The band takes exactly what it encloses.
         Option (c), a size threshold, is out for defect 13's reason: a
         tolerance may pick a TARGET, it may not set a semantic RESULT.
         THE DECIDING ARGUMENT IS PATRICK'S, recorded because the
         read-back did not make it: PROMOTION HAS NO NATURAL STOPPING
         POINT. If clipping a room's wall pulls in that whole room, does
         it also pull in the walls that room shares with rooms outside
         the band? And theirs? In a connected plan that cascades toward
         "select everything", and any rule that stops it is an arbitrary
         depth limit. Selection stays what it LOOKS like. Deformation is
         the honest, visible result, and extract is the tool for
         detaching a room first -- which is precisely why P4.2 built it.
         REQUIRED ALONGSIDE: the group action REPORTS WHAT IT DID at the
         moment it does it -- e.g. "Grouped 5 rooms; 3 partly enclosed --
         their shapes will follow." Not a warning, and not the edit-tear
         channel: the plain status line, said once, to the 06c2145
         wording standard (that commit fixed a message that read as
         nonsense at its boundary value -- "0 of them since the plan was
         opened" -- so the standard is: read the sentence the code will
         actually print, at its edge cases, before shipping it). The
         difference between a surprising result and an explained one is
         one sentence, and this is the gesture most likely to surprise.

RULED (3) RETIRE kind == "rigid", and record the expired justification
         VERBATIM beside its removal, so the record shows a carve-out
         that died when its stated reason expired rather than one that
         quietly vanished. The reason, from walls.py:1529-1537 as it
         stands today: "a GROUPED neighbour still follows, but on the
         old coordinate path -- grouping duplicates a room's walls onto
         the originals, so promoting one would wire a group member to an
         outside wall permanently, and what a group even IS
         topologically is P4.5's question. Same instinct as the
         `group() is None` gate that keeps grouped walls out of
         coalesce." BOTH clauses expire in this task.

AMENDED (3b) DO NOT RETIRE THE 12 group() is None GUARDS AS A CLASS.
         Patrick's split, and the census confirms it: they are not one
         guard. Enumerated, with what each protects and its disposition.
         KEEP -- 7, not one of them about duplication:
           1. extract.py:91 (capture_floating_furnishings) -- a GROUPED
              furnishing is not swept into a floating room's cargo.
              Ownership arbitration between a group and a float.
           2. items.py:94 (_handle_visible) -- the individual selection
              box/rotator hide inside a group; the group's outline
              governs. Pure presentation.
           3. macro.py:315 (^A select-all) -- top-level items only.
              Selecting a child AND its group double-moves it.
           4. mainwindow.py:728 (arrow nudge) -- the same double-move
              class: groups move as groups.
           5. walls.py:1448 (WallItem.mousePressEvent) -- a grouped
              wall's drag belongs to the GROUP, not to the wall.
              Interaction ownership.
           6. walls.py:2389 (OpeningItem.mousePressEvent) -- ditto.
           7. walls.py:2409 (OpeningItem.mouseMoveEvent) -- ditto.
         RETIRE -- 1:
           8. walls.py:1537 -- the rigid carve-out itself (ruling 3).
         CONSEQUENTIAL, RULING NEEDED BEFORE ANY IS TOUCHED -- 4. These
         are the "grouped walls are exempt from the topology passes"
         family, and letting grouped walls in is a far larger change
         than retiring a drag branch:
           9.  walls.py:544  (merge_wall) -- THE coalesce exemption
               Patrick named by hand.
           10. walls.py:503  (weld_scene) -- grouped ends never weld.
           11. walls.py:267  (graph_from_scene) -- grouped walls are
               invisible to the planner's graph view entirely, so
               merge / split / weld cannot see them at all.
           12. rooms.py:1030 -- a room outline edge will not bind to a
               grouped wall.
         WHY THESE CANNOT BE WAVED THROUGH: today they are load-bearing
         because a grouped wall is a COPY -- letting copies into the
         graph would double every edge. Under no-copy a grouped wall IS
         a plan wall, so the same guards become the opposite thing: a
         wall the planner is blind to. That is a change of KIND, not of
         degree. And 9-11 are exactly ROW 36's producer path (the
         release-merge rebind), so relaxing them is precisely what would
         trip the watch. Each returns to Patrick individually.

RULED (4) ASSENT to z = floor_term + stack_term + type_term, with both
         consequences accepted: the backdrop's -1e9 becomes a TYPE TERM
         rather than a magic number, and z ENTERS THE SNAPSHOT so "Bring
         to front" survives save/load and becomes undoable (F4's
         complaint closes). bring_to_front's full-scene max scan dies
         with it.
         ADDITION 1 -- STATE THE BAND ARITHMETIC AS CONSTANTS AND ASSERT
         IT. This is one scheme rather than three that happen not to
         collide only because max(type_term) < STACK_BAND and
         max(stack_term) < FLOOR_BAND. Those become NAMED CONSTANTS with
         the inequality written beside them, PINNED BY A TEST --
         otherwise it is three schemes again the first time someone
         raises a type constant.
         ADDITION 2 -- CHECK THE SCHEMA BEFORE ASSUMING. Done, and the
         answer SPLITS THIS TASK: design-schema.v5.json has NO field for
         a stacking index anywhere -- not on room, wall, furnishing or
         group -- and all four set additionalProperties: false, so there
         is nowhere to put one and no way to smuggle one in. The
         measured property lists are in the read-back.
         THEREFORE, and NOT folded in: the RUNTIME collapse (one scheme,
         one number, the constants and their test, the full-scene scan
         retired) proceeds in P4.5. The SERIALIZATION half is BLOCKED on
         a schema ruling with version implications, and returns to
         Patrick as its own decision. Until it is ruled, z stays OUT of
         the document and defect 11 closes only its runtime half --
         stated plainly rather than half-claimed.

RULED (5) Test dispositions agreed as read back, including the rewrite
         of test_grouping_rooms_without_their_walls_still_copies_them
         into its opposite, and the widening of the twenty-room test
         from "creates no walls" to "creates no objects at all".

RULED (6) ROW 36's WATCH IS A LIVE TRIPWIRE FOR THIS TASK. If
         test_the_merge_rebind_producer_is_watched goes red mid-task:
         STOP. The row is re-argued and Patrick rules BEFORE the test is
         touched. Confirmed green against the merged tree at adaa519.

RULED (7) MINI-GATE APPROVED, with a NEW ITEM 1 -- the headline number
         of the whole migration: group the WHOLE PLAN (20 rooms), move
         it, ungroup. Expect ZERO new objects. The original review
         measured >= 106 duplicate walls and >= 149 duplicate openings
         on exactly this gesture; closing that to zero is what Phases 3
         and 4 were for. Time it too -- it should feel instant. The
         eight items from the read-back follow as 2-9.
         CROSS-CUTTING, ADDED 2026-08-04 -- not a tenth item but a thing to
         watch at EVERY step: NO ROOM MAY SHOW A DASHED OPEN EDGE WHERE A
         WALL ACTUALLY EXISTS. That is the user-visible signature of the
         whole group-guard family (a room reading OPEN over a wall that is
         right there), it costs nothing extra to watch for while doing the
         nine items, and it catches the class ANYWHERE in the gate rather
         than only where we thought to look -- which is exactly how the
         P4.2 mini-gate's six findings were caught.
         DELIBERATELY STILL BROKEN -- DO NOT REPORT THESE (added 2026-08-05
         with the fragment ruling). A gate spends its credibility on the
         first known defect it is asked to rediscover, so what is knowingly
         unfixed is named up front:
           * ROOM BOOLEAN "FRAGMENT" (register row 47). Fragmenting two
             overlapping rooms and then dragging one piece clear leaves
             that piece's REGION behind and opens a dashed edge on each
             neighbour, over walls that are really there. Measured, filed,
             and argued as the FIRST task after P4.5 merges. The
             cross-cutting dashed-edge watch above therefore EXEMPTS the
             fragment gesture and nothing else.
           * The runtime z-order collapse (row 11's remaining half) is
             still open; it is not reachable from any gate item, but if
             the app hangs on a drag, that is it and not a new fault.

P4.5(1a) the three amendments to (1), before the mechanism work
ruff:    clean
pytest:  601 passed, 7 deselected, 4 xfailed (sum 612; trailer in the commit)
files:   docs/CODE_REVIEW_v2.md (rows 41 + 42 amended), this file.
notes:   ROW 41 NOW CARRIES MEASURED FIXTURES, verified here rather than
         inherited. A loop can be non-simple by TOUCHING as well as by
         crossing, and the shipped corpus has the touching kind:
           python -m floorplanner.viewer.fp3d examples/symmetricP1.json --dump
           python -m floorplanner.viewer.fp3d examples/planc1.v5.json --dump
         Measured: symmetricP1.json -- WIC, 1 zero-width spur;
         planc1.v5.json -- Hall 4, M Bath 6, WIC 1 (the last not named in
         the ruling, found by running it). Both files return ZERO I5b
         errors under check(deep=True) -- planc1.v5 reports 23 errors of
         other kinds, none of them I5b -- so they pass the invariant while
         being non-simple. Both halves of the claim verified before
         recording, per the standing rule.
         AND THE FIXTURES CARRY A CONSTRAINT WITH THEM: symmetricP1.json
         is the REFERENCE CLEAN FILE and is corpus-frozen, so "is a
         spurred loop an I5b violation?" cannot be answered without also
         deciding whether the frozen reference gets re-cut. That is a
         corpus decision as much as an invariant one, and it now has
         something concrete to be decided against.
         ROW 42 sharpened as ruled, plus the adjacent finding recorded and
         NOT acted on: the three structurally identical appliers
         (_DragVertex.apply, GroupItem._apply_corner_records,
         RoomItem._translate) are a consolidation candidate -- one concept,
         three implementations, F2's shape, and the reason row 42 exists
         at all is that there was no single seam to hang a check on.
         ARGUED PHASE 6, where the command layer's MoveVertices IS that
         seam. Not P4.5's.
         THE XFAIL IN test_self_intersection.py IS A MECHANISM RECEIPT,
         and is named as such here so a future reader does not tidy it
         away as a stale marker. It is a DISTINCT USE from the P0.4
         characterization xfails: those mark behaviour that is wrong today
         and will be fixed; this one marks a test that CANNOT pass under
         copy-based grouping for a structural reason (_corner_records
         deliberately splits any corner an outsider holds, so a clipped
         bake cannot deform a room and there is nothing to report). Its
         flip in the no-copy sub-commit is therefore not a bug fix but the
         PROOF THE MECHANISM ACTUALLY CHANGED -- if it still xfails after
         duplicate_wall dies, the death was cosmetic.

P4.5(2a) the ungroup-merge question, measured on the PRE-P4.5 tree, and a
         claim of my own withdrawn
ruff:    clean
pytest:  602 passed, 7 deselected, 3 xfailed (sum 612; trailer in the commit)
files:   mainwindow.py (the comment corrected), this file (the rule + this
         block).
notes:   THE QUESTION, asked before filing: was ungroup's plan-wide
         merge_all destroying geometry BEFORE P4.5, or only after the
         copies stopped hiding it? Two filings hung on it -- "a pass that
         was about to become harmful" (one line) versus "the shipped app
         has been silently deleting walls from real plans" (an F5-family
         defect, with a note that saved plans may have lost geometry).
         MEASURED in a worktree at main@adaa519. The isolation that makes
         it decisive: merge_all is PLAN-WIDE, so it does not care whether
         a wall was in the group -- running it alone on a freshly loaded
         file answers the question without any grouping at all.
           symmetricP1.json    scene walls 80 -> 78
           planc1TestV5.json   scene walls 82 -> 78
           planc1.v5.json      scene walls 83 -> 80
           fiveRoomTest.json   scene walls 16 -> 16
         End-to-end (group everything, bake a move, ungroup) gives the
         IDENTICAL numbers, confirming the loss came from the plan-wide
         pass and not from the group.
         AND THEN THE DECIDING MEASUREMENT, which is the one that changes
         the filing -- RE-TAKEN ON THE SAVED-FILE PRODUCER after the
         reviewer asked which instrument it used, because the claim is
         'nothing reached a saved plan differently' and snapshot() is
         NOT that producer (it is canonicalize(design_from_scene(...))
         minus provenance, unmodelled settings and active_floor):
           snapshot()          identical on all three
           design_document()   identical on all three  <- _write_plan's
           json.dump bytes     identical on all three  <- the user's file
         They agree because design_from_scene CANONICALISES internally
         (Design.from_dict(canonicalize(...))), so both producers rest
         on a canonical walk, and the three things design_document adds
         are window state merge_all cannot touch. Reasoning that out
         would have been enough to be right and not enough to be
         MEASURED, which is the difference the census doctrine exists
         for. The original wording said only win.snapshot() and is
         superseded by this. The absorbed walls are collinear same-type
         segments the walk planarises to the same document, and wall count
         is PRESENTATION state (P2.3's Known-regressions row says so in as
         many words). So NO GEOMETRY WAS EVER LOST, by ungroup or
         otherwise, and this files as (1): a pass removed before it became
         harmful. One line, no defect number, nothing for SANITY_CHECK.md.
         A CLAIM OF MINE IS WITHDRAWN. P4.5(2)'s message said the ungroup
         "absorbed 2 REAL walls that no gesture asked it to touch" and
         called it "purely destructive". The first half is true of wall
         ITEMS and the second half is false: nothing was destroyed. The
         code comment is corrected to the measured truth, and the
         correction is recorded here rather than amended away -- the same
         discipline as defect 32's withdrawal and defect 23's.
         WHAT WAS ACTUALLY WRONG, stated accurately: a LOCAL gesture
         silently reshaped the WHOLE plan's item structure, which breaks
         "the group moves and nothing else changes" and makes an undo step
         look bigger than the edit that caused it. That is reason enough
         to remove it, and it is the reason the task line already gave.
         THE RULE IS RECORDED IN THE WORKING AGREEMENT, not beside the
         function, because it is general: "a tidy-up pass that outlives
         the mess it tidied only touches things nobody asked it to."
         Phase 6 meets it again when snapshot() retires -- the debounced
         full-document walk exists to serve snapshot-undo, and once the
         command stack owns undo every remaining caller needs
         re-justifying rather than inheriting.

P4.5(17a) THE OVERCLAIM ANNOTATION -- history stays, the correction sits
         beside it (the gate-failure disclosure's treatment, and the CRLF
         normalisation's)
notes:   TWO COMMIT MESSAGES ON THIS BRANCH CONTAIN CLAIMS THAT WERE FALSE
         WHEN WRITTEN. Neither is rewritten; both are named here so the
         record shows the correction rather than concealing the error.
         * 7b99030 "P4.5(8) - row 36 re-argued by MEASUREMENT" -- its third
           bullet claims the census doctrine was extended to cover
           BEHAVIOURAL claims. That edit never applied: the script used
           `if anchor in s:` and skipped silently when the anchor did not
           match -- a MISSING CHECK. The commit's other claims (the
           grouped-merge measurement, the sibling watch, the
           visibility/permission procedure, the boundary-marker
           precondition rule) did land and stand.
         * 39a4ada "P4.5(16) - the divergence named as latent; justifications
           join the census" -- its second item claims the doctrine was
           extended to cover SURVIVAL JUSTIFICATIONS. That edit never
           applied either: the script RAISED and was committed through
           because the gate was green in the same output -- a CORRECT CHECK
           IGNORED, the worse of the two shapes. The commit's first item
           (row 45's latent-divergence amendment) did land and stands.
         Both entries were added for real at a6bbd80, in the census section,
         and grepped for afterwards. The instrument that should have caught
         them is tools/record.py, added at P4.5(18) -- which then refused
         its own second edit on an ambiguous anchor, which is the behaviour
         being bought.

P4.5(24) THE ENDPOINT DRAG JOINS THE VERTEX OPS -- three method notes kept
         because each is a rule being obeyed rather than a result
notes:   * A COUNT WAS NOT ACCEPTED AS A FINDING. The receipt showed "2
           distinct uids" across a drag, which reads as churn REDUCED. Traced
           event by event it is V1, V2, V2, V2, V2, V2, V2 -- the original
           shared corner sampled before the snapped target had left it, then
           ONE detached vertex for the whole gesture. Churn ELIMINATED, not
           reduced, and the two readings are different claims.
         * DEFECT 13's RULING WAS MEASURED, NOT ARGUED. The conversion does
           not touch `_endpoint_target`/`_corner_target`, so "where the end
           lands is unchanged" was deducible -- and was taken at 0.25x, 1.0x
           and 4.0x anyway, identical before and after. An identity change
           that also moved geometry would be two changes wearing one commit,
           and the difference between a correct inference and a taken reading
           is the whole of "being right from the source is not the same as
           having measured".
         * A RECEIPT WAS DOWNGRADED RATHER THAN QUOTED AT FACE VALUE. Of the
           two fail-first reds, one was a behavioural verdict ("the end
           changed identity 6 times in one drag") and one was an
           AttributeError -- the API not existing yet. The second shows the
           test is new, not that the behaviour was wrong, and it is reported
           as the weaker shape it is. A red is not evidence merely because it
           is red.

P4.5(27) THE FRAGMENT CASE MEASURED -- evidence committed before any reading
notes:   docs/evidence/defect23_fragment_probe.py + defect23-fragment.json.
         Replayed on both trees. The product is the same on each and is
         already broken: 20 distinct Vertex objects on 10 geometric points,
         room_owns_walls FALSE for all nine (group, room) pairs. The walk
         WELDS on the way out (20 -> 10 vertices, 16 -> 12 walls, merged=4),
         so check(deep) is CLEAN on it. Base: the gesture moves 4 of 4 walls
         and 0 of 16 outline corners, opens four dashed edges that each have a
         real wall on them, and the SAVE SUCCEEDS on a file recording that
         nothing moved. Deform: I11 1 -> 3, I5b 0 -> 1, all pairs between
         rooms fragment itself created.

P4.5(28) THE SEVEN RULINGS RECORDED, before any code. Masking accepted as a
         Working-agreement entry at its second instance; rows 47 (fragment ->
         extract, first task after P4.5, and mainwindow.py:982-996 named as a
         SECOND duplication site duplicate_wall never reached), 48 (the
         invariants have never checked the scene the user edits), 49 (I11
         speaks nowhere in the shipped app); 2a amended in place; the
         mini-gate gains a "deliberately still broken" list.

P4.5(29) THE FRAGMENT TEST OFF ITS VACUOUS BASIS. all(enclosed(r)) after the
         move read the NEIGHBOURS duplicate walls, never the piece that moved
         -- it passed on a tree that stranded the room completely. New
         verdict: no wall belongs to two fragments, via room_walls. Three
         preconditions, including that the pieces ABUT (4 coincident edges
         measured). --runxfail lands on the VERDICT, not a precondition.

P4.5(30) DEFORM-TO-FOLLOW LANDS. Clipped band: Garage 0 of 9 -> 7 of 9
         corners, PKT Off 0 -> 5, Util 0 -> 3, the other 17 unchanged.
         THE OLD ASSERTION COULD NOT HAVE FLIPPED: it compared walls-moved to
         corners-moved and A RUN OF k WALLS HAS k+1 CORNERS, so "neither xfail
         flipped" was never evidence against the mechanism. A second
         formulation was tried and REJECTED FOR VACUITY -- "corners moved ==
         corners held by a moved wall" passes on the pre-fix tree too, both
         sides empty -- caught by running it against d57a76f before keeping
         it.

P4.5(31) THE SECOND XFAIL FLIPS, and it was the TEST's geometry. Its body said
         "move ONE corner"; a group of the two walls meeting at a corner holds
         THREE. Its delta (-400,300) yields a NON-crossing quad, so the silence
         it failed on was correct. Swept: crossing at (0,150) (0,200) (0,300)
         (60,240) (-60,300). The deform is now a PRECONDITION before the
         message is demanded.

P4.5(32) ALIGN AND DISTRIBUTE ON THE FINISHED GATHER. rooms_holding moves to
         rooms.py as the single definition; GroupItem._rooms_holding aliases
         it. THE RECEIPT IS THE NEIGHBOUR: three rooms on party walls, A and B
         selected, C never selected -- sharing before -> after (old) -> new is
         A 4/4 -> 1/4 -> 4/4, B 4/4 -> 0/4 -> 4/4, C 4/4 -> 2/4 -> 4/4, open
         edges 2/3/2 -> 0/0/0. Distribute destroyed sharing on every room
         WHILE MOVING THEM BY ZERO. THE GATHER HAD TO WIDEN TO WALLS TOO,
         found by walking into it: with only the room half widened, C drew a
         dashed edge with 0 walls spanning it. Same hole in _corner_records
         (unwelded_ends 0 -> 1 after the clipped bake), fixed by INVERTING the
         scan that used to split the outsider off.

P4.5(33) view.py:402 -- THE LAST p1/p2 WRITER IN floorplanner/. 40 mouse-move
         events: 40 split-on-writes -> 0, the drawn wall byte-identical.
         grep now returns ZERO writers in floorplanner/.

P4.5(34) THE SETTER DELETION IS STOPPED ON A SCOPE-CHANGING MEASUREMENT, and
         this entry is the finding rather than the work.
notes:   The completeness proof itself is DELIVERED: `grep -rn "\.p1 = \|\.p2
         = " floorplanner/` returns nothing. What deleting the setters would
         additionally buy is that they cannot be re-used; what it COSTS was
         not visible until censused.
         MEASURED: `Vertex.moved_to` is the ONLY thing that increments the
         split counter (`_SPLITS[0] += 1`, vertex.py:145), and its ONLY
         callers are the two setters (walls.py:1224, 1234). Delete them and
         `split_count()` is frozen at 0 for the life of the process.
         CONSEQUENCE: SIX ASSERTIONS BECOME UNFALSIFIABLE -- test_topology_ops
         :269 and :320, test_wall_move:223, :331 and :620, test_view:90 --
         each of the form `assert split_count() == before`. They are watches
         that an operation caused no splits; with nothing able to split they
         become tautologies that still read as coverage. That is VACUOUS BY
         TAUTOLOGY, the one shape the gate greps for, in a form its four
         literal patterns will not match -- and it would be introduced BY a
         cleanup, which is how the instrument-boundary rule says these
         arrive.
         SO THE PIECE IS BIGGER THAN "delete two properties": it is retire the
         shim AND its telemetry AND convert six watches from "no splits" to
         "identity preserved" (comparing Vertex objects, which is strictly
         stronger), plus 22 writers across seven test files and
         docs/make_gallery.py, plus tests/test_vertices.py, which is the
         shim's OWN spec and pins split-on-write as a behaviour.
         NOT DONE, and not fudged: a deletion that silently vacates six
         assertions is exactly the trade this project stops for. Ruling
         wanted on whether the counter retires with the setters (converting
         the watches) or the setters stay until Phase 6's command layer owns
         the move.

P4.5(35) THE RULING ON (34): retire the setters AND split_count() together.
notes:   Recorded before the code. VACUITY GAINS A FIFTH SHAPE -- THE
         UNSATISFIABLE ASSERTION, the mirror of the first: shapes 1-3 cannot
         be FALSE, this one cannot be TRUE. A test that cannot fail gives
         false CONFIDENCE; one that cannot pass gives false DOUBT, and false
         doubt is worse in one respect because it sends you hunting bugs that
         are not there. Not machine-detectable. The tell: a red that survives
         every plausible fix -- at which point try to satisfy the assertion BY
         HAND, and if you cannot, the test is the bug.
         AND: MIGRATION TELEMETRY RETIRES WITH THE THING IT MEASURED. Keeping
         split_count() meaningful means keeping split-on-write reachable,
         which is KEEPING THE DEFECT TO PRESERVE ITS ALARM -- ungroup's
         merge_all again. The replacement goes in AT A DIFFERENT LAYER: the
         counter measured runtime churn, what is wanted is that the MECHANISM
         CANNOT RETURN, and that is a question about the source text.

P4.5(36) THE CENSUS MADE PERMANENT. Gate-Census gains `end_assign=N`; any
         `.p1 = ` / `.p2 = ` in floorplanner/ fails the gate. Added BEFORE the
         deletion, so it passes in both states and protects the deletion
         rather than following it. Receipt: 0 clean, 1 with a no-op writer
         reintroduced (named with file and line), 0 after reverting.

P4.5(37) NINE WRITERS SAY WHAT THEY MEAN. Every one turned out to mean DETACH
         THIS END, not MOVE THIS CORNER; the `if p2 else p1` branches collapse
         to one line because the choice was always about which end. TWO
         FIXTURES ARE ONLY CONSTRUCTIBLE VIA THE SPLIT (test_outline's south
         shorten, test_walls' overhang) -- relocating carries the outline
         corner and the edge never opens, which is the state they exist to
         build. Informative, not an obstacle: the split survives as an
         explicit operation, only the coordinate-assignment spelling dies.

P4.5(38) THE SIX WATCHES CONVERTED to identity assertions. The view one is
         genuinely RED against 431a761 ("the drawn end took 36 identities
         across 40 move events"); the other five were green before and after,
         so they were PROBED instead -- make set_end_vertex fabricate rather
         than adopt, and four fail, one on its precondition (reported as the
         weaker shape it is). THREE DRAFTS were wrong before the corpus one
         was right: "same object" forbids PROMOTION, "already existed" forbids
         the ANTI-SHEAR SPLIT (measured: 4 ends re-minted at (216,288) and
         (432,144), all AT THE SAME COORDINATES, 8 sharing classes before and
         after). THE OLD COUNTER NEVER SAW THOSE MINTS -- they go through
         Vertex.at, not moved_to -- so a watch cannot be converted
         mechanically: what it measured and what it appeared to measure are
         different sets.

P4.5(39) test_vertices.py REWRITTEN as the spec for the operations that
         replaced the shim, pinning `Vertex.at` against `relocated_to` on the
         SAME scene and the SAME movement, so the only difference is which was
         asked for.

P4.5(40) THE SHIM RETIRES. Setters, _carry_anchors, moved_to, _SPLITS,
         _SITES, _blame, split_count, split_sites, note_vertex_splits and its
         two logs. 178 lines out, 73 in.
notes:   THE CENSUS THAT OPENED THIS PIECE WAS WRONG, and that is the finding.
         It counted 22 writers by grepping `.p1 = `. It MISSED FIVE, all
         `setattr(wall, attr, <point>)` with attr a variable -- four in
         walls.py, one in a test -- which surfaced as AttributeErrors the
         moment the setters went. EXACTLY the boundary P4.5(36) had written
         into the new check's own comment, crossed within the hour by the
         person who wrote it. A CENSUS BY SPELLING FINDS ONLY THAT SPELLING;
         the deletion is what made the true count visible, and it is now its
         own enforcement for that shape (setattr raises, and no grep can be
         fooled by that).
         THE OPERATION SURVIVES AS `WallItem.detach_end`, because those five
         sites genuinely mean it -- and it could NOT be
         `set_end_vertex(attr, Vertex.at(p))`: that routes through
         _fuse_anchors, which deliberately does not move an opening's anchor
         to a vertex somewhere ELSE (R1(b)). Here the end really moved, so the
         anchor must follow, which is what _carry_anchors did. 12 of 41
         openings on planc1 mirrored down their wall before that carry
         existed, so it is folded into the operation rather than deleted.


```
