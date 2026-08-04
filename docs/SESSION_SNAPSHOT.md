# Session snapshot — read this first

**Re-cut 2026‑08‑04 at the P4.4 merge (`main` @ `ae9f0ad`).** This file exists so a fresh session can start from disk instead of from a chat summary. It is an **index and a state marker, not a second copy of the record** — where it points at another document, that document is authoritative and this one must not be trusted over it.

---

## 1. Where the work stands

| | |
|---|---|
| **Branch** | `main` @ `ae9f0ad` — the **PR #6 merge commit**. `p4.4-concept-duplicate` carried 5 sub-commits (`868e315` … `da38c46`), each at a full green gate. |
| **PR** | **#6 MERGED 2026‑08‑04** on Patrick's acceptance ("it works perfectly"), tested on the branch build with the version label verified. CI green on the merge. |
| **Census** | **598 collected** (588 passed, 7 deselected, 3 xfailed, every sum reconciling). The 3 xfails are all P4.5's (group round-trip, clipped band, group wall-copying). |
| **Phases done** | 0–3, P4.1, P4.1b, P4.2, P4.3, **P4.4 — ticked 2026‑08‑04 and merged.** Next: **P4.5 (group semantics + z-order) — the second designated MINI-GATE task.** |
| **Side branch** | `viewer-packaging` — the 3D viewer's build wiring, independent of the migration. Register rows 39 (move under `floorplanner/`) and 40 (degrade on a missing optional dep). |

**What P4.4 landed** (detail in the Progress log's P4.4 blocks, 1–5):
1. **Census + the four rulings** (1), recorded verbatim before any code.
2. **Register row 37 closed** (2): the shuffle mode gets `Ctrl+H` and an **absolute** macro token (`^H "on"` / `^H "off"`) emitted for a flip from any route, so a replayed session lands in the mode the recording ended in.
3. **Duplicate-as-template** (3): `design/template.py` — a room becomes a one-room v5 document and a one-room document folds back in as a floating room. **One mechanism, three workflows**: a clipboard between the halves is Copy/Paste, a **file** is Save/Load template, back-to-back is Duplicate. `_copy_spec` + `_perimeter_span` **deleted**.
4. **Concept rooms** (4): a typed-by-dimension, wall-less, floating room; `category` and `nominal_size` **modelled on the item** (the placement pattern); I13 holds by construction.
5. **The record** (5).

**The next actions, in order:**
1. ~~The viewer move + merge~~ — **done 2026‑08‑04** (row 39): the viewer lives at `floorplanner/viewer/`, one top-level name per project. Row **40** stays open: the 3D menu action, when built, must report a missing optional dependency rather than raise.
2. **P4.5 read-back** (group semantics + z-order collapse): census first; it is the **second designated mini-gate task**, so its PR does not merge until Patrick runs the gate.
3. Then Phase 5 (site/landscape) and Phase 6 (command undo, final perf).

---

## 2. What to read, in order

1. **`CLAUDE.md`** — architecture and house rules.
2. **`docs/V5_MIGRATION_PLAN.md`** — Working agreement (census doctrine), Status table (P4.1–P4.4 ticked with acceptance lines), the Phase‑4 branch-strategy ruling, **P4.5 task text**, and the **Progress log** (P4.2 blocks 1–26; P4.3 1–6 + dispositions; P4.4 1–5).
3. **`docs/CODE_REVIEW_v2.md`** — the register: rows 13/17/25/30/34/35/36/37 closed with receipts; the **carried census note RESOLVED** at P4.4; open: 3, 11, 23 (all P4.5), 27's Windows leg, 39 + 40 (viewer).
4. **The schema** — `design-schema.v5.json`; for P4.5 the `groups` collection and the z-order question are the ground.

**One-direction rule.** Where a fact is restated in two places, the text says which copy is authoritative. Never resolve a disagreement by editing the copy that is easier to reach.

---

## 3. The rules that bind the work (unchanged; each was paid for)

- **Gate with `tools/gate.py`** (full mode; paste the trailer verbatim — capture it programmatically).
- **The pre-work census is a phase of the task**; read-backs quote disk; task-line figures are estimates until measured.
- **Sub-commit per piece at a full green gate. A changed test is a red flag, named and justified. Receipts are fail-first against the unfixed tree, with preconditions asserted before verdicts.**
- **Destructive experiments in a worktree. Chat is not the record. The reviewer ticks the boxes.**
- **Phase‑4 branch strategy:** per-task branches, PR into `main` as a merge commit; **P4.5 needs the Patrick mini-gate before merge** (P4.2's passed; P4.3 and P4.4 merged on green CI + acceptance).
- **Findings are fixed only against measured reproductions** — reproduce → introspect → fix → pin, fail-first.
- **`git commit` after `git add` commits the WHOLE index.** Use `git commit <paths>` when anything else is staged — a parallel WIP was swept into a sub-commit once and had to be unpicked.

---

## 4. What Phase 4 has established so far, in one paragraph

**Rooms are durable movable units, joining is explicit, and a room is a document.** Extract lifts a room out of the shared network (I12) and join welds it back; the outline is the one definition of which walls are a room's (row 36). Shuffle mode turns every automatic joining pass off through one accessor, so a dragged room stays floating and information a mode defers is delivered at the explicit join. And a room now round-trips through a **one-room v5 document**, which is simultaneously the clipboard payload, the template file, and the duplicate operation — so Copy/Paste, Save/Load template and Duplicate are one mechanism with a clipboard, a file, or nothing in the middle.

---

## 5. Open items

**P4.5 owns:** defect **3** (groups serialize), **11** (z-order collapse), **23** (clipped-band stranding — the deform-vs-stay ruling), the **P3.1 split-on-write shim**, **two identity-churn sites**, the **`kind == "rigid"` carve-out** (retire or re-justify), and **row 36's merge-rebind producer** (carried, **watched** by a CI test whose preconditions re-open the row if merge semantics change). · **Row 39** viewer move (doing next) · **row 40** viewer degrade-on-missing-dep · the **windows-latest CI leg** (row 27, not merge-blocking) · per-floor **visibility** (follow-up, not built).

---

## 6. Things that will waste your time if you don't know them

- **A running app keeps the code it imported** — the status-bar version label shows the launch identity. This has now caught a wrong-build test session once (`a4eaf74` had no P4.4), which is exactly what it is for.
- **The timing lane is not in the gate**; `tools/gate.py --perf` runs it deliberately.
- **`gh` is not on `PATH`**: `& "C:\Program Files\GitHub CLI\gh.exe"` (PowerShell) or `"/c/Program Files/GitHub CLI/gh.exe"` (bash).
- **Files on disk are CRLF**; multi-line `\n` patterns silently match nothing — this bit an Edit anchor in the Progress log, which is also inside a code fence.
- **Headless drags:** build `QMouseEvent`s with `buttons=LeftButton` to the viewport; `centerOn` first. **Headless keys:** construct `QKeyEvent`s with modifiers directly — never QTest Ctrl synthesis.
- **Macro replay geometry matters:** a `.fpm` replays correctly only at the window geometry it was recorded at — the fiveRoomDragSplit pins run at 1400×1000 + fit, the fuse-straggler pin at the default window; each test states which.
- **Patrick's macro loop** is the fastest reproduction channel: record in-app, commit the `.fpm` to `examples/`, replay headless via `win.run_macro`, pin verbatim.
- **The suite's console is cp1252** — no non-ASCII in test output.
