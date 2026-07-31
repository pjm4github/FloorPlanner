# Session snapshot — read this first

**Written 2026‑07‑31, at the Phase‑3 merge.** This file exists so a fresh session can start from disk instead of from a chat summary. It is an **index and a state marker, not a second copy of the record** — where it points at another document, that document is authoritative and this one must not be trusted over it.

---

## 1. Where the work stands

| | |
|---|---|
| **Branch** | `main` — Phase 3 is merged, so `main` tracks HEAD again |
| **Merge commit** | **`03f3868`** (PR #1, a merge commit, not a squash), 2026‑07‑31 |
| **Head at snapshot** | `5a7711c` *docs: Phase 3 merged — banner closed, carried list written, CLAUDE.md current* |
| **Working tree** | clean, except three untracked `Screenshot *.png` left deliberately for the owner |
| **CI** | green on `main` at both `03f3868` and `5a7711c` — ruff, py3.10, py3.13, **and the deep-invariant job** |
| **Census** | **526 collected**; OFF / ON / DEEP each **513 passed, 7 deselected, 6 xfailed**, every sum reconciling |
| **Phases done** | 0, 1, 2, 3 complete (all rows ticked). **Phase 4 has not started.** |

**The next action is a read-back for P4.1, run against `main`, and nothing else.** No P4.1 code until that read-back is confirmed. Its **first open question is the branch strategy for Phase 4** — Phase 3 ran on `v5-topology` under a rule that said so explicitly; Phase 4 has no such ruling yet.

---

## 2. What to read, in order

1. **`CLAUDE.md`** — architecture and the house rules. Brought current at the merge; its Phase‑3 sentences are accurate as of `5a7711c`.
2. **`docs/V5_MIGRATION_PLAN.md`** — the plan. Read, in this order: the **Working agreement** (top), the **Status** table, the **Phase‑3 merge banner**, **What Phase 3 carries into Phase 4**, then the **P4.x task text**. The **Progress log** at the bottom is history, newest work interleaved by phase — it is appended to, never rewritten.
3. **`docs/CODE_REVIEW_v2.md`** — the defect register. Authoritative for every defect's status.
4. **`docs/SANITY_CHECK.md`** — the three manual gates. Gates 1, 2 and 3 all **PASSED**; Gate 3's findings and their dispositions are recorded there.

**One-direction rule.** Several facts are deliberately restated in two places (a survey row and a register row, for instance). Where that happens the text says which copy is authoritative and which is the checkpoint. **Never resolve a disagreement by editing the copy that is easier to reach.**

---

## 3. The rules that bind the work

These are settled and are not up for re-litigation; each was paid for by a failure recorded in the plan.

- **Gate with `tools/gate.py`, never with hand-typed counts.** It runs the gates, computes the census, checks every run's outcomes sum to `--collect-only`, and prints a trailer meant to be pasted verbatim into the commit message. `python tools/gate.py` (ruff + OFF + ON + DEEP) · `--quick` (ruff + OFF) · `--deep` (what CI's deep job runs) · `--perf` (the timing lane, explicitly).
- **A pipeline's exit status is the last command's.** Never `... | tail -N && <next step>` — that gate enforces nothing, and it is how a commit landed over two errors once.
- **Sub-commit per piece, each at a full green gate.** One task, several rollback points.
- **Read-backs quote disk, not memory.** Quote what disk supports, name what it does not, proceed on the verified subset. A number that cannot be found on disk is not quoted back as though it were.
- **Destructive experiments run in a `git worktree`, or after a WIP commit.** `git checkout <file>` has no undo and has already eaten uncommitted work once.
- **Chat is not the record.** Before ending a session mid-task, commit the spec — then summarize. The summary describes what was committed; it is never the thing itself.
- **Commit handed-back doc edits immediately**, before running any git that could discard them.
- **A changed test is a red flag, not a detail.** Name every one, with the line that justifies it.
- **The reviewer ticks the boxes.** Claude Code implements, gates, logs, and reports; the checkbox in the status table is the reviewer's to set, unless they say otherwise.
- **Receipt standard:** a fix is accepted by a guard shown **failing first** against the unfixed tree — and the harness must prove it exercised the mechanism before its verdict counts. (Thirty-eight synthetic drags once reported a clean result having moved nothing.)

---

## 4. What Phase 3 established, in one paragraph

**A corner is one `Vertex`,** held by the walls *and* by the room outlines that meet there. A wall move updates the rooms it borders **by construction** — nothing recomputes, because there is only one corner to move. That is what let the room-detection engine, the coalesce/weld family and the `OpenWall` placeholder be **deleted outright** rather than ported, and it is why `bake` went from 279.0 ms to 26.4 ms at 64 rooms. The file format is **v5 `floorplanner-design`**; `FILE_VERSION = 4` survives only as the legacy export writer.

---

## 5. Open items carried into Phase 4

**Authoritative list: `docs/V5_MIGRATION_PLAN.md` → “What Phase 3 carries into Phase 4”.** Index only, so this file cannot drift into a rival copy:

defect **23** (group move strands a clipped room → P4.5) · **25** (gesture-time message for a door straddling a junction → P4.1, with a recorded dissent for P4.3 that Gate 3 weakened) · **30** (a body drag strands corner-holders outside the dragged run → P4.2) · **34** (a document gap in the (0.6″, 9.0″) band nothing reports or closes — must be a **review**, not an auto-repair → P4.2) · **defect 13's drag half** (may a gesture tolerance set a geometric result? → P4.2) · the **P3.1 split-on-write shim** (→ P4.5) · **two identity-churn assignment sites** (→ P4.5).

**They share one thesis, and it is the most useful sentence to carry forward: every one is an operation that knows about ROOMS where it should know about CORNERS.**

---

## 6. Things that will waste your time if you don't know them

- **The timing lane is not in the gate**, in any mode, by ruling — its ratios are **recorded, never asserted** (the noise band reached ~27 while the whole diagnostic range is 4→16). Run it deliberately with `tools/gate.py --perf`.
- **`gh` is not on `PATH`**: call it as `& "C:\Program Files\GitHub CLI\gh.exe"`.
- **Files on disk are CRLF.** A multi-line search/replace written with `\n` will silently match zero times and leave a half-applied edit. Normalize the pattern, or edit with a tool that handles it.
- **`design_from_scene` resolves its argument to the `QGraphicsScene`.** Per-scene flags and baselines live there, not on the `MainWindow`.
- **Headless drags:** `QTest.mouseMove` cannot synthesize a button-held drag; build `QMouseEvent`s with `buttons=LeftButton` and send to the viewport — and `centerOn` first, or the scene point maps outside the viewport and the press goes nowhere. A wall's midpoint is often an **opening**, whose child item takes the press.
- **The suite's console is cp1252** — no `≈`, `×` or other non-ASCII in test output.
