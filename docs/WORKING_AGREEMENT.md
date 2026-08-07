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