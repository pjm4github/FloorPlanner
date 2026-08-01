# Session snapshot — read this first

**Written 2026‑07‑31, at the P4.1 merge.** This file exists so a fresh session can start from disk instead of from a chat summary. It is an **index and a state marker, not a second copy of the record** — where it points at another document, that document is authoritative and this one must not be trusted over it.

---

## 1. Where the work stands

| | |
|---|---|
| **Branch** | `main` — P4.1 is merged, so `main` tracks HEAD again |
| **Merge commit** | **`0d6db8e`** (PR #2, a merge commit, not a squash), 2026‑07‑31 |
| **CI** | green on `main` post-merge (run 30682374579) — ruff, py3.10, py3.13, and the deep-invariant job |
| **Census** | **526 collected**; OFF / ON / DEEP each **514 passed, 7 deselected, 5 xfailed**, every sum reconciling |
| **Phases done** | 0, 1, 2, 3 complete; **P4.1 complete and ticked** (sub-commits `0df3aa5`, `a0e1b95`, `cce2eb6`). |

**The next action is P4.1b** — defect 25's gesture-time message, ruled standalone at the P4.1 read-back, branching now that PR #2 is merged (branch `p4.1b-doorway-message`). Scope is **message only**: draw-release and end-drag say at gesture time what R2c's walk already detects and files — naming *the edit* and *the doorway*, through the defect-6 edit-path vocabulary; no change to what the gesture *does* (decline/split/weld policy stays P4.3's with the `auto_*` flags). Acceptance: Patrick's exact Gate-3 scenario — draw a wall ending on a doorway — produces the specific message instead of the generic torn-network line, pinned by a test asserting the message names the doorway, with a fail-first receipt against `main`.

**After P4.1b comes P4.2 (extract/join)**, which carries two things ruled at the P4.1 read-back: a **Patrick manual mini-gate before its PR merges** (it changes what gestures mean), and an inherited **open question, not a claim** — whether `_perimeter_span` dies there, contingent on `_copy_spec` (its other surviving caller, owned by no phase) being reshaped there too. Authoritative copy: the register's carried census note.

---

## 2. What to read, in order

1. **`CLAUDE.md`** — architecture and the house rules. Brought current at the P4.1 merge (delete is deletion; the fracture family is gone).
2. **`docs/V5_MIGRATION_PLAN.md`** — the plan. Read, in this order: the **Working agreement** (top — now including the census doctrine), the **Status table**, the **Phase‑4 branch strategy ruling** (head of Phase 4), the **P4.1b and P4.2 task text**, then the carried-list table under the Phase‑3 merge banner. The **Progress log** at the bottom is history, newest work appended — it is annotated, never rewritten.
3. **`docs/CODE_REVIEW_v2.md`** — the defect register. Authoritative for every defect's status, for the **carried census note** (the `_perimeter_span`/`_copy_spec` contingency), and for defect 25's P4.1b ruling.
4. **`docs/SANITY_CHECK.md`** — the three manual gates of Phase 3, all PASSED; Gate 3's findings and dispositions are recorded there. Phase 4 adds per-task mini-gates at P4.2 and P4.5 (see the branch-strategy ruling).

**One-direction rule.** Several facts are deliberately restated in two places (a survey row and a register row, for instance). Where that happens the text says which copy is authoritative and which is the checkpoint. **Never resolve a disagreement by editing the copy that is easier to reach.**

---

## 3. The rules that bind the work

These are settled and are not up for re-litigation; each was paid for by a failure recorded in the plan.

- **Gate with `tools/gate.py`, never with hand-typed counts.** It runs the gates, computes the census, checks every run's outcomes sum to `--collect-only`, and prints a trailer meant to be pasted verbatim into the commit message. `python tools/gate.py` (ruff + OFF + ON + DEEP) · `--quick` (ruff + OFF) · `--deep` (what CI's deep job runs) · `--perf` (the timing lane, explicitly).
- **The pre-work census is a phase of the task, not a virtue** *(settled at the P4.1 read-back, after task-line figures failed checking three times)*. Every task opens with a fresh census of what it deletes and touches, run against the tree, quoted with spans and callers; the read-back protocol is its enforcement.
- **A pipeline's exit status is the last command's.** Never `... | tail -N && <next step>` — that gate enforces nothing, and it is how a commit landed over two errors once.
- **Sub-commit per piece, each at a full green gate.** One task, several rollback points.
- **Read-backs quote disk, not memory.** Quote what disk supports, name what it does not, proceed on the verified subset.
- **Destructive experiments run in a `git worktree`, or after a WIP commit.** `git checkout <file>` has no undo and has already eaten uncommitted work once.
- **Chat is not the record.** Before ending a session mid-task, commit the spec — then summarize. Rulings from review conversations are committed to the plan/register the same day they are made (the three P4.1 read-back rulings are the model).
- **Commit handed-back doc edits immediately**, before running any git that could discard them.
- **A changed test is a red flag, not a detail.** Name every one, with the line that justifies it — and declare intentional replacements in the task text *before* the work (P4.1's four were declared at the read-back and approved).
- **The reviewer ticks the boxes.** Claude Code implements, gates, logs, and reports; the checkbox is the reviewer's to set, unless they say otherwise.
- **Receipt standard:** a fix is accepted by a guard shown **failing first** against the unfixed tree — and the harness must prove it exercised the mechanism before its verdict counts.
- **Phase‑4 branch strategy** *(ruled at the P4.1 read-back)*: per-task branches, PR into `main` as a **merge commit** (never squash), full-mode trailers on every sub-commit; **P4.2 and P4.5 require a Patrick manual check before their PRs merge**; P4.1b, P4.3, P4.4 merge on green CI plus reviewer acceptance.

---

## 4. What Phases 3 and 4-so-far established, in one paragraph

**A corner is one `Vertex`,** held by the walls *and* by the room outlines that meet there. A wall move updates the rooms it borders **by construction** — nothing recomputes, because there is only one corner to move. That deleted the room-detection engine, the coalesce/weld family and the `OpenWall` placeholder outright, and took `bake` from 279.0 ms to 26.4 ms at 64 rooms. **P4.1 extended it to deletion: `delete_wall` deletes outright** — the room survives through its stored outline and the vacated edge becomes an open edge — and the fracture family is gone (defect 17 closed, with a coda: its "no-op" had aged into painting a dashed open cue over an edge a wall actually covers). The file format is **v5 `floorplanner-design`**; `FILE_VERSION = 4` survives only as the legacy export writer.

---

## 5. Open items carried in Phase 4

**Authoritative list: `docs/V5_MIGRATION_PLAN.md` → "What Phase 3 carries into Phase 4" (as amended by the P4.1 rulings) and the register.** Index only:

defect **25** (gesture-time doorway message → **P4.1b, ruled, next up**) · **23** (group move strands a clipped room → P4.5) · **30** (a body drag strands corner-holders outside the dragged run → P4.2) · **34** (the (0.6″, 9.0″) document-gap band — must be a **review**, not an auto-repair → P4.2) · **defect 13's drag half** (may a gesture tolerance set a geometric result? → P4.2) · the **P3.1 split-on-write shim** (→ P4.5) · **two identity-churn assignment sites** (→ P4.5) · the **`_perimeter_span`/`_copy_spec` contingency** (→ P4.2's read-back, as a question).

**They share one thesis: every one is an operation that knows about ROOMS where it should know about CORNERS.** P4.1 was the first Phase-4 confirmation of it — deletion needed no fracture because the corners already carry the room.

---

## 6. Things that will waste your time if you don't know them

- **The timing lane is not in the gate**, in any mode, by ruling — its ratios are **recorded, never asserted**. Run it deliberately with `tools/gate.py --perf`.
- **`gh` is not on `PATH`**: call it as `& "C:\Program Files\GitHub CLI\gh.exe"`.
- **Files on disk are CRLF.** A multi-line search/replace written with `\n` will silently match zero times and leave a half-applied edit. Normalize the pattern, or edit with a tool that handles it.
- **`design_from_scene` resolves its argument to the `QGraphicsScene`.** Per-scene flags and baselines live there, not on the `MainWindow`.
- **Headless drags:** `QTest.mouseMove` cannot synthesize a button-held drag; build `QMouseEvent`s with `buttons=LeftButton` and send to the viewport — and `centerOn` first, or the scene point maps outside the viewport and the press goes nowhere. A wall's midpoint is often an **opening**, whose child item takes the press.
- **The suite's console is cp1252** — no `≈`, `×` or other non-ASCII in test output.
