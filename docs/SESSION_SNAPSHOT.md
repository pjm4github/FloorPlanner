# Session snapshot — read this first

**Written 2026‑08‑02, mid‑P4.2, on branch `p4.2-extract-join`.** This file exists so a fresh session can start from disk instead of from a chat summary. It is an **index and a state marker, not a second copy of the record** — where it points at another document, that document is authoritative and this one must not be trusted over it.

---

## 1. Where the work stands

| | |
|---|---|
| **Branch** | `p4.2-extract-join` — **23 sub-commits**, each at a full green gate; `main` last merged P4.1b (`ec5f207`) |
| **PR** | **#4, open and ON HOLD** for the Patrick mini-gate (the first task under that ruling). CI green at every push. |
| **Census** | **554 local / 552 on CI** (the two extra are Patrick's untracked `examples/symmetricP2/P3.json`, picked up by corpus validation, both green); 543 passed, 4 xfailed, sums reconciling |
| **Phases done** | 0–3, P4.1, P4.1b complete and ticked. **P4.2 implemented (core + all harvest pieces + six mini-gate findings fixed) — NOT ticked, PR not merged.** |

**P4.2 on the branch, in three layers:**
1. **The task itself** (sub-commits 1–7): `extract.py` (extract/join per §4), placement modelled end-to-end (stash retired), the acceptance suite green, party-wall regression flipped, label-drag rewired (`_privatize_shared_walls` deleted), defect 30 fixed (corner splits by each room's own boundary), defect 34's gap review op, defect 13's drag half closed per ruling, the P2.3 row's second predicted fix **refuted and recorded** (needs a carry-vs-stay ruling).
2. **Six mini-gate findings** (8–15), every one caught by Patrick and fixed against a measured reproduction with a fail-first pin: the 4-way corner split correction, `close_gap` stranding outlines, the mixed-corner step, the drag-split cascade (join merge tolerance → `SHARE_TOL`; partial-cover edge splitting; run-wide tee gather), the misbound-edge upgrade rebind + outline-corner tee + spike collapse. His two macro files (`fiveRoomTest.json` + three `.fpm`s, committed to `examples/`) are pinned verbatim as regression tests.
3. **Tooling & floors** (16–23, consolidated Progress-log block): the macro recorder made whole (three capture bugs; `CARET_SHORTCUTS` one-table design; `^O`/`^+S` file tokens; Load… button), and the Floors work per Patrick's spec (Select `^F` / New `^+F`, one popup surface with default pre-highlighted, `^F "name"` / bare-`^F` / `^+F "name"` tokens with the PUP comment form, **z-banded floor stacking** with per-floor Move to front/back (display), **atmospheric depth fade**, Ctrl+PgDown/PgUp quick flip).

**The next actions, in order:**
1. **Patrick runs the mini-gate** (items 1–8, scripted in the Progress log's P4.2(7) block) on a fresh launch — the version label (status bar, `v1.2 · branch @ sha`) must show the launch sha; that label exists because a stale process cost one round.
2. **Defect 35's disposition**: it stays open until Patrick confirms the macro-driven findings (4–6) covered everything on his shelved "still some problems with the drag" list.
3. On mini-gate pass: **reviewer ticks P4.2, PR #4 merges as a merge commit**, snapshot re-cut at the merge.
4. Then the **P4.3 read-back** (shuffle mode; the `auto_*` flags — decline/split/weld gesture policy deferred there from defect 25). P4.4's read-back inherits the `_perimeter_span`/`_copy_spec` contingency (register's carried census note, re-argued at P4.2).

---

## 2. What to read, in order

1. **`CLAUDE.md`** — architecture and house rules; current through the P4.2 core (extract.py, rooms-as-movable-units).
2. **`docs/V5_MIGRATION_PLAN.md`** — Working agreement (census doctrine included), Status table, the Phase‑4 branch-strategy ruling, P4.2/P4.3 task text, and the **Progress log**, whose P4.2 blocks (1–23) are the detailed record of this branch, including the mini-gate script (in the (7) block) and the six findings.
3. **`docs/CODE_REVIEW_v2.md`** — the register: rows 13/17/25/30/34 closed with receipts; **row 35 OPEN** (the shelved drag report + re-open protocol); the **carried census note** (authoritative: `_perimeter_span` → P4.4, contingent).
4. **PR #4's description + commit messages** — each sub-commit carries its own receipts and verbatim gate trailer.

**One-direction rule.** Where a fact is restated in two places, the text says which copy is authoritative. Never resolve a disagreement by editing the copy that is easier to reach.

---

## 3. The rules that bind the work (unchanged; each was paid for)

- **Gate with `tools/gate.py`** (full mode; paste the trailer verbatim — capture it programmatically, one transcription slip is on record in P4.2(12)'s reply).
- **The pre-work census is a phase of the task**; read-backs quote disk; task-line figures are estimates until measured (0-for-3 across phases).
- **Sub-commit per piece at a full green gate. A changed test is a red flag, named and justified. Receipts are fail-first against the unfixed tree, with preconditions asserted before verdicts.**
- **Destructive experiments in a worktree. Chat is not the record. The reviewer ticks the boxes.**
- **Phase‑4 branch strategy:** per-task branches, PR into `main` as a merge commit; **P4.2 and P4.5 need the Patrick mini-gate before merge**; P4.3/P4.4 merge on green CI + acceptance.
- **Findings are fixed only against measured reproductions** — the six mini-gate findings all followed reproduce → introspect → fix → pin; two proposed fixes (P2.3's vertex-adjacency gather, finding 5's junction-degree guard) were **refuted by the tree and reverted with the refutation recorded**, which is the system working.

---

## 4. What this branch established, in one paragraph

**Rooms are durable movable units.** Extract lifts a room out of the shared wall network (`placed → floating`, I12 by construction — the plan keeps every wall it had) and join welds it back; the label-drag of a placed room *is* extract→move→join through those ops. The document walk folds each floating room in its own vertex namespace; I14 exempts floating-vs-plan pairs. The drag machinery now honors the corners-not-rooms thesis in every direction: a moved corner carries each room by that room's *own boundary* (run-bordered follows, continuation-bordered stays, mixed corners step, partial covers split at the wall's end vertex, outline-corner tees split the run). And the session toolchain — record/replay macros covering mouse, keyboard, shortcuts, files and floors — is what converted "the drag is wrong somewhere" into six named, pinned mechanisms.

---

## 5. Open items

defect **35** (shelved drag report — open pending Patrick's confirmation the macros covered it) · the **P2.3 carry-vs-stay ruling** (both predicted fixes refuted; pinned by an xfail) · defect **23** (→ P4.5, boundary stated in the register) · the **P3.1 split-on-write shim** (→ P4.5) · **two identity-churn sites** (→ P4.5) · `_perimeter_span`/`_copy_spec` (→ **P4.4**'s read-back, as a question) · per-floor **visibility** (noted follow-up, not built) · **dashed-cue-over-covered-stretch** presentational wrinkle (disclosed at finding 3; flag if it bothers in the mini-gate).

---

## 6. Things that will waste your time if you don't know them

- **A running app keeps the code it imported** — the status-bar version label shows the launch identity; restart after any push before re-testing. (This cost a full round once.)
- **The timing lane is not in the gate**; `tools/gate.py --perf` runs it deliberately.
- **`gh` is not on `PATH`**: `& "C:\Program Files\GitHub CLI\gh.exe"`.
- **Files on disk are CRLF**; multi-line `\n` patterns silently match nothing.
- **Headless drags:** build `QMouseEvent`s with `buttons=LeftButton` to the viewport; `centerOn` first; a wall's midpoint is often an opening. **Headless keys:** construct `QKeyEvent`s with modifiers directly — never QTest Ctrl synthesis (global `keyboardModifiers` leak); the recorder's capture is pinned against the real delivery order (QWindow → widget, ShortcutOverride before KeyPress).
- **Patrick's macro loop** is the fastest reproduction channel: record in-app (Load…/Replay in the recorder), commit the `.fpm` to `examples/`, replay headless via `win.run_macro`, pin verbatim.
- **The suite's console is cp1252** — no non-ASCII in test output.
