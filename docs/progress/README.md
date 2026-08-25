# Progress log — index

*Append one entry per task. Newest at the bottom.*

> The line above is the log's own rule, carried here verbatim from the heading
> block it lived in (`V5_MIGRATION_PLAN.md:582`) when the log was split out on
> 2026-08-06. It still governs: **append, never revise.** A later correction is
> a later entry, and several entries here exist only to correct an earlier one.

**4,351 lines across seven files, moved verbatim.** Nothing was reworded,
reordered, tidied or reformatted. The whole log was reassembled from these files
and compared byte-for-byte against the plan's blob before the move — identical,
289,297 bytes either way. That receipt is in the commit that made the split.

---

## The files

| file | source lines | lines | dates in the entries | tasks |
|---|---|---|---|---|
| [`phase-0.md`](phase-0.md) | 585–828 | 244 | 2026-07-26 | P0.0 · P0.1 · P0.2 · P0.3 · P0.3b · P0.3b-step3 · P0.4 · P0.5 · P0.6 · P0.7 |
| [`phase-1.md`](phase-1.md) | 829–1246 | 418 | *none stated* | P1.1 · P1.2 · P1.3 · P1.3-followup · P1.3b · P1.4 · P1.4-followup · P1.5 · P1.6 |
| [`phase-2.md`](phase-2.md) | 1247–1657 | 411 | *none stated* | P2.1 · P2.2 · P2.3 · P2.4 · P2.4-followup · P2.5 |
| [`phase-3-part-1.md`](phase-3-part-1.md) | 1658–2649 | 992 | 2026-07-29 → 07-31 | P3.1 · P3.2 · P3.3 · P3.5 · P3.8 (and its numbered riders) |
| [`phase-3-part-2.md`](phase-3-part-2.md) | 2650–3518 | 869 | 2026-07-29 → 07-30 | P3.7 · P3.6-followup · P3.6 · P3.5-followup (×3) · P3.4 · exit check 3 |
| [`phase-4-part-1.md`](phase-4-part-1.md) | 3519–4360 | 842 | 2026-08-01 → 08-04 | P4.1 · P4.1b · P4.2 (+6 mini-gate findings) · P4.3 · P4.4 |
| [`phase-4-part-2.md`](phase-4-part-2.md) | 4361–4935 | 575 | 2026-08-04 → 08-06 | P4.5, entries (0) through (40) and the merge |
| [`side-tasks.md`](side-tasks.md) | — | — | 2026-08-06 → | work belonging to no phase |
| [`phase-5.md`](phase-5.md) | — | — | 2026-08-11 → | P5.2 · P5.2-followup · P5.2-complete |
| [`furnishings.md`](furnishings.md) | — | — | 2026-08-13 → | prism |
| [`tasks/`](tasks/) | — | — | 2026-08-24 → | new entries, one file per task — see below |

**`phase-5.md` was opened on 2026‑08‑12, a day after its first entry's work
merged**, and its header says so. P5.2 shipped at PR #26 with a defect record and
a handoff but no progress entry, so the entry is a reconstruction from the
commit, the handoff and the diff. It is marked as one. The same rule as the two
undated files above: a reconstruction that looks contemporaneous is worse than
one that admits its provenance.

Source line numbers are into `V5_MIGRATION_PLAN.md` **as of commit `2f232bd`**,
the last commit before the split.

**Two files state no dates.** P1 and P2's entries record commits, counts and
gate lines but never a calendar date. That is left as it is rather than filled
in from `git log`: a date derived afterwards would date the *commit*, not the
work, and would look authoritative while being a reconstruction.

---

## Why Phase 3 and Phase 4 are split into parts, and why the parts are not ranges

Both exceeded the 1,200-line limit (1,861 and 1,417). Every cut is at a
**column-0 task-entry start**, never inside an entry.

The parts are numbered rather than named for the tasks they hold, and that is
deliberate: **the log's append order is not the phase's task order.** Phase 3
was written down as P3.1, P3.2, P3.3, P3.5, P3.8, P3.7, P3.6, P3.5-followup,
P3.4 — because entries were appended as work finished and as earlier tasks were
returned to. Naming a file `P3.1-P3.5.md` would imply a numeric range the file
does not contain. The `tasks` column above says what is actually in each.

## The one out-of-sequence entry stays where it is

`phase-4-part-1.md` contains a non-phase entry — **the 3D view popup, branch
`viewer-popup`, 2026-08-04** — sitting between the P4.4 entry and P4.5. It was
not lifted into `side-tasks.md`, because the entry's own text is an argument
against moving it:

> NOT migration work, and recorded here precisely BECAUSE it is not: it landed
> between P4.4 and P4.5 rather than as a phase task, and it TOUCHES THE APP
> STARTUP PATH — floorplanner/app.py, which no Phase-4 task has needed to open.
> A change to the first ten lines the process runs deserves a row in the
> sequence it stepped outside of, or the next person reading this log will find
> app.py changed by nobody.

Its value *is* its position. `side-tasks.md` is therefore the destination for
non-phase work recorded from 2026-08-06 onward, not a re-filing of what came
before.

---


## An append-only shared file serialises parallel branches — measured 2026-08-07

**Every conflict in the GREEN batch was in this one file, and there were no
others.** Four independent tasks — a test-suite census, a CI job, a bridge
function, a walls-side report — touched four disjoint sets of source files and
never collided. They collided here, because each appended one entry to
`side-tasks.md`:

| branch | merge of `main` | conflict |
|---|---|---|
| G1 | — (merged first) | none |
| G2 | — (branched after G1 landed) | none |
| G3 | needed | **`side-tasks.md`** |
| G4 | needed | **`side-tasks.md`** |
| G4 | again, after G3 landed | none |

Two hand resolutions, both the same shape: two sides each appending different
entries to the same tail. Nothing was lost and nothing was hard — the entries are
independent paragraphs — but **git cannot know that**, because "append-only" is a
convention about the file, not a property git can see. Every parallel branch pays
it, and the cost grows with the square of how many run at once.

**Resolved by BATCH order, not merge order.** The entries label themselves item
1 through 4, so a reader following them should not have to know which pull
request landed first. Merge order is a fact about pull requests; the log records
the work.

### The consequence, for whenever agents run concurrently

**Progress entries go in per-task files, for the same reason defect records
became per-file.** That refactor's argument was that a table with unbounded prose
in its cells "diffs badly, guarantees merge conflicts between agents, and cannot
migrate to a tracker without transcription" — the first two clauses are exactly
this finding, one directory over, and they were written before anything had
measured it. Now something has.

**DONE — [`0104-ruling.md`](../handoff/0104-ruling.md) SS5 tier 1, named as the
blocker on running agents in parallel.** [`tasks/`](tasks/) is the new
destination: one file per task, `YYYY-MM-DD-<slug>.md`, and
[`tasks/INDEX.md`](tasks/INDEX.md) is *generated* from them by
`tools/progress_index.py` (mirroring `defects/INDEX.md`; wired into
`tools/gate.py --docs` as `Docs-Progress`) — one writer per file, no shared
tail, the index derived rather than maintained. **Write new entries there,
not here.**

**The files above are NOT migrated, and that is deliberate, not partial
work.** They are frozen narrative — nothing has appended to any of them since
2026-08-17 — so re-splitting settled history into per-task files would carry
all the risk of a large mechanical move (matching the split's own
byte-for-byte discipline) for a conflict that history, being finished, can no
longer have. The day-two-agents problem this section measured is about WHERE
THE NEXT ENTRY LANDS, and that is solved by `tasks/` existing at all.

## Conventions

**Cite, do not restate.** An entry names its evidence file and the command that
reproduces it (`docs/evidence/…`), rather than inlining the measurement.

**An entry cites its handoff when one exists** — one line, `handoff: 0042`,
pointing into [`../handoff/`](../handoff/). The log is curated: what happened,
why, and what proved it. The mailbox is raw: the exchange itself. Different
genres and different readers, so they are linked rather than merged.

**The log lives inside a code fence**, as it always has, so its column-aligned
`ruff:` / `pytest:` / `files:` / `notes:` fields render as written. Each file
reopens the fence and closes it at the end; a fence cannot be split across
files, and that is the only formatting a split file adds. **This still applies
inside the body of a [`tasks/`](tasks/) entry** — only the file's first two
lines (title, then the `**date**, branch \`…\`.` meta line
`tools/progress_index.py` parses) are new; the prose and fenced fields below
them follow the same conventions as always.
