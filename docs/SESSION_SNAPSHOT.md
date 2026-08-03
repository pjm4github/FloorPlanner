# Session snapshot — read this first

**Re-cut 2026‑08‑02 at the P4.2 merge (`main` @ `6d24969`).** This file exists so a fresh session can start from disk instead of from a chat summary. It is an **index and a state marker, not a second copy of the record** — where it points at another document, that document is authoritative and this one must not be trusted over it.

---

## 1. Where the work stands

| | |
|---|---|
| **Branch** | `main` @ `6d24969` — the **PR #4 merge commit** (merge, not squash). `p4.2-extract-join` carried 26 sub-commits (`dfd30af` … `3b62142`), each at a full green gate. |
| **PR** | **#4 MERGED 2026‑08‑02** after the Patrick mini-gate **PASSED — all 8 items**, fresh launch, status-bar version label verified at the launch sha. CI green at every push and on the merge. |
| **Census** | **552 collected, local == CI** (541 passed, 7 deselected, 4 xfailed, every sum reconciling). The 554/552 delta is gone: Patrick removed his two untracked `examples/symmetricP2/P3.json`; `examples/multifloor.fpm` is committed as a **convenience file, not pinned** (his ruling, recorded). |
| **Phases done** | 0–3, P4.1, P4.1b, **P4.2 — ticked 2026‑08‑02 and merged.** Next: **P4.3 (shuffle mode), read-back sent, nothing started.** |

**What P4.2 landed** (detail in the Progress log's P4.2 blocks, 1–26):
1. **The task** (1–7): `extract.py` (extract/join per §4), placement modelled end-to-end, acceptance green, party-wall regression flipped (P0.5 Known-regressions row closed), label-drag rewired (`_privatize_shared_walls` deleted), defects 30/34/13-drag closed, the P2.3 row's second predicted fix refuted and recorded.
2. **Six mini-gate findings** (8–15), each fixed against a measured reproduction with a fail-first pin; Patrick's macro files pinned verbatim as regression tests.
3. **Tooling & floors** (16–23): the macro recorder made whole (three capture bugs; `CARET_SHORTCUTS`; `^O`/`^+S` tokens), and the Floors work per Patrick's spec (Select `^F` / New `^+F`, one popup surface, deterministic floor tokens, z-banded stacking, atmospheric depth fade, Ctrl+PgDown/PgUp).
4. **The close-out** (24–26): the hand-off record, census hygiene (`multifloor.fpm`), the mini-gate pass recorded, **defect 35 CLOSED** on the reporter's confirmation (shelf empty; residuals were harvested as findings 5–6), P4.2 ticked.

**The next actions, in order:**
1. **P4.3 (shuffle mode)** starts on Patrick's answers to the read-back (sent 2026‑08‑02): the **carry-vs-stay ruling** on the P2.3 row (both contracts quoted side by side; pinned by the xfail `test_a_roomless_split_wall_body_drags_as_one_run`), and **defect 25's deferred gesture-policy questions** (decline/split/weld — the `auto_*` flags are P4.3's).
2. Per the Phase‑4 branch strategy: per-task branch, PR into `main`, **merge on green CI + acceptance** (no mini-gate for P4.3; the next mini-gate task is P4.5).
3. P4.4's read-back inherits the `_perimeter_span`/`_copy_spec` contingency (register's carried census note, re-argued at P4.2 — authoritative there).

---

## 2. What to read, in order

1. **`CLAUDE.md`** — architecture and house rules; current through P4.2 (extract.py, rooms-as-movable-units, floors tooling).
2. **`docs/V5_MIGRATION_PLAN.md`** — Working agreement (census doctrine included), Status table (P4.2 ticked with its acceptance line), the Phase‑4 branch-strategy ruling, P4.3 task text (§ "P4.3 — Shuffle mode"), and the **Progress log**, whose P4.2 blocks (1–26) are the detailed record of the merged branch.
3. **`docs/CODE_REVIEW_v2.md`** — the register: rows 13/17/25/30/34 closed with receipts; **row 35 CLOSED 2026‑08‑02** (shelf confirmed empty by the reporter at the mini-gate pass); the **carried census note** (authoritative: `_perimeter_span` → P4.4, contingent).
4. **The schema** — `floorplanner/design/design-schema.v5.json` `$defs.editing_modes`: shuffle's contract in the document format (shuffle implies `auto_coalesce`/`auto_weld`/`auto_bind` all off; leaving shuffle joins nothing automatically — "rooms are joined explicitly, not silently").

**One-direction rule.** Where a fact is restated in two places, the text says which copy is authoritative. Never resolve a disagreement by editing the copy that is easier to reach.

---

## 3. The rules that bind the work (unchanged; each was paid for)

- **Gate with `tools/gate.py`** (full mode; paste the trailer verbatim — capture it programmatically, one transcription slip is on record in P4.2(12)'s reply).
- **The pre-work census is a phase of the task**; read-backs quote disk; task-line figures are estimates until measured (0-for-3 across phases).
- **Sub-commit per piece at a full green gate. A changed test is a red flag, named and justified. Receipts are fail-first against the unfixed tree, with preconditions asserted before verdicts.**
- **Destructive experiments in a worktree. Chat is not the record. The reviewer ticks the boxes.**
- **Phase‑4 branch strategy:** per-task branches, PR into `main` as a merge commit; **P4.5 needs the Patrick mini-gate before merge** (P4.2's is passed and done); P4.3/P4.4 merge on green CI + acceptance.
- **Findings are fixed only against measured reproductions** — the six mini-gate findings all followed reproduce → introspect → fix → pin; two proposed fixes (P2.3's vertex-adjacency gather, finding 5's junction-degree guard) were **refuted by the tree and reverted with the refutation recorded**, which is the system working.

---

## 4. What the merged branch established, in one paragraph

**Rooms are durable movable units.** Extract lifts a room out of the shared wall network (`placed → floating`, I12 by construction — the plan keeps every wall it had) and join welds it back; the label-drag of a placed room *is* extract→move→join through those ops. The document walk folds each floating room in its own vertex namespace; I14 exempts floating-vs-plan pairs. The drag machinery honors the corners-not-rooms thesis in every direction: a moved corner carries each room by that room's *own boundary* (run-bordered follows, continuation-bordered stays, mixed corners step, partial covers split at the wall's end vertex, outline-corner tees split the run). And the session toolchain — record/replay macros covering mouse, keyboard, shortcuts, files and floors — is what converted "the drag is wrong somewhere" into six named, pinned mechanisms, and what let the reporter confirm the shelf empty (defect 35 closed).

---

## 5. Open items

The **P2.3 carry-vs-stay ruling** (both predicted fixes refuted; pinned by an xfail; asked in the P4.3 read-back) · **defect 25's gesture-policy questions** (decline/split/weld → P4.3's `auto_*` flags; asked in the read-back) · defect **23** (→ P4.5, boundary stated in the register) · the **P3.1 split-on-write shim** (→ P4.5) · **two identity-churn sites** (→ P4.5) · `_perimeter_span`/`_copy_spec` (→ **P4.4**'s read-back, as a question) · per-floor **visibility** (noted follow-up, not built) · **dashed-cue-over-covered-stretch** presentational wrinkle (disclosed at finding 3; not flagged at the mini-gate) · the **windows-latest CI leg** (register row 27, open, explicitly not merge-blocking).

---

## 6. Things that will waste your time if you don't know them

- **A running app keeps the code it imported** — the status-bar version label shows the launch identity; restart after any push before re-testing. (This cost a full round once; the mini-gate pass ran under it.)
- **The timing lane is not in the gate**; `tools/gate.py --perf` runs it deliberately.
- **`gh` is not on `PATH`**: `& "C:\Program Files\GitHub CLI\gh.exe"` (PowerShell) or `"/c/Program Files/GitHub CLI/gh.exe"` (bash).
- **Files on disk are CRLF**; multi-line `\n` patterns silently match nothing.
- **Headless drags:** build `QMouseEvent`s with `buttons=LeftButton` to the viewport; `centerOn` first; a wall's midpoint is often an opening. **Headless keys:** construct `QKeyEvent`s with modifiers directly — never QTest Ctrl synthesis (global `keyboardModifiers` leak); the recorder's capture is pinned against the real delivery order (QWindow → widget, ShortcutOverride before KeyPress).
- **Patrick's macro loop** is the fastest reproduction channel: record in-app (Load…/Replay in the recorder), commit the `.fpm` to `examples/`, replay headless via `win.run_macro`, pin verbatim.
- **The suite's console is cp1252** — no non-ASCII in test output.
