# Session snapshot — read this first

**Re-cut 2026‑08‑03 at the P4.3 merge (`main` @ `4050e44`).** This file exists so a fresh session can start from disk instead of from a chat summary. It is an **index and a state marker, not a second copy of the record** — where it points at another document, that document is authoritative and this one must not be trusted over it.

---

## 1. Where the work stands

| | |
|---|---|
| **Branch** | `main` @ `4050e44` — the **PR #5 merge commit** (merge, not squash). `p4.3-shuffle` carried 6 sub-commits (`a6ded30` … `545b79a`), each at a full green gate. |
| **PR** | **#5 MERGED 2026‑08‑03 on Patrick's acceptance** (green CI + acceptance — the P4.3/P4.4 rule; no mini-gate). CI green at every push and on the merge. |
| **Census** | **569 collected, local == CI** (559 passed, 7 deselected, 3 xfailed, every sum reconciling). The 3 xfails are all P4.5's (group round-trip, clipped band, group wall-copying). |
| **Phases done** | 0–3, P4.1, P4.1b, P4.2, **P4.3 — ticked 2026‑08‑03 and merged.** Next: **post-merge dispositions (one commit), then the P4.4 read-back.** |

**What P4.3 landed** (detail in the Progress log's P4.3 blocks, 1–6):
1. **Census + both rulings** (1): four `settings.editing` flags measured (one live, three dead); ruling 1 (STAY + two-test amendment) and ruling 2 (tiered doorway weld) recorded verbatim before work began.
2. **Plumbing** (2): `editing_enabled()` — shuffle implies the `auto_*` passes off without rewriting them; document emit from live SETTINGS; the document-synced Shuffle toolbar toggle.
3. **Gesture gating + tiered weld** (3): jamb-snap within `JOIN_TOL` at both release paths, else the P4.1b message; never split, never refuse; `auto_weld`'s decision; shuffle suppresses the message and the label-drag drop-join (moved → stays floating, click → still placed); explicit join reports deferred information. Five fail-first receipts.
4. **Acceptance** (4): shuffle drag across the plan through the real handlers, both unchanged, `check()` deep-clean at every step.
5. **Ruling 1 executed** (5): the P2.3 Known-regressions row closed as superseded-by-ruling (STAY); the xfail replaced by two hard passes (stay contract + the `auto_coalesce` heal).
6. **The fuse straggler** (6, register row 36): extract used two definitions of "the room's walls" (outline to copy-trim, binding list to float) — a bound-but-unnamed five-room wall rode out and was stranded; fixed by step 1b (extract releases bound walls no outline edge names); Patrick's macro pinned verbatim.

**The next actions, in order:**
1. **Post-merge dispositions, one commit** (ruled by Patrick 2026‑08‑03): (a) `auto_bind` leaves the UI — stays modelled/emitted/plumbed, control returns when a gateable site exists (register disposition with the census reasoning); (b) row 36's merge-rebind producer carried to P4.5 **conditionally on a CI watch test** (red if the producer or the extract guard changes); (c) the shuffle toggle's missing macro token/shortcut filed as its own register row.
2. **P4.4 read-back** (concept rooms, `nominal_size`, duplicate-as-template): census first; inherits the `_perimeter_span`/`_copy_spec` question (register's carried census note **authoritative**); must also state explicitly what P4.4 does to the **binding-list/outline duality in the clipboard path** — P4.5's rulings assume that consumer is resolved.
3. **P4.5** (group semantics + z-order) is the second designated **mini-gate** task; P4.4 merges on green CI + acceptance.

---

## 2. What to read, in order

1. **`CLAUDE.md`** — architecture and house rules.
2. **`docs/V5_MIGRATION_PLAN.md`** — Working agreement (census doctrine included), Status table (P4.2 and P4.3 ticked with acceptance lines), the Phase‑4 branch-strategy ruling, P4.4/P4.5 task text, and the **Progress log** (P4.2 blocks 1–26; P4.3 blocks 1–6 + dispositions).
3. **`docs/CODE_REVIEW_v2.md`** — the register: rows 13/17/25/30/34/35/36 closed with receipts; the **carried census note** (authoritative: `_perimeter_span` → P4.4, contingent on `_copy_spec`); the auto_bind standing disposition; the shuffle-token row.
4. **The schema** — `design-schema.v5.json` `$defs.editing_modes` (shuffle's contract) and the room `nominal_size` / `category: concept` fields (P4.4's ground; I13: a concept room must be floating).

**One-direction rule.** Where a fact is restated in two places, the text says which copy is authoritative. Never resolve a disagreement by editing the copy that is easier to reach.

---

## 3. The rules that bind the work (unchanged; each was paid for)

- **Gate with `tools/gate.py`** (full mode; paste the trailer verbatim — capture it programmatically).
- **The pre-work census is a phase of the task**; read-backs quote disk; task-line figures are estimates until measured.
- **Sub-commit per piece at a full green gate. A changed test is a red flag, named and justified. Receipts are fail-first against the unfixed tree, with preconditions asserted before verdicts.**
- **Destructive experiments in a worktree. Chat is not the record. The reviewer ticks the boxes.**
- **Phase‑4 branch strategy:** per-task branches, PR into `main` as a merge commit; **P4.5 needs the Patrick mini-gate before merge**; P4.4 merges on green CI + acceptance.
- **Findings are fixed only against measured reproductions** — reproduce → introspect → fix → pin, fail-first.

---

## 4. What P4.2 + P4.3 established, in one paragraph

**Rooms are durable movable units, and joining is explicit.** Extract lifts a room out of the shared wall network (`placed → floating`, I12 by construction) and join welds it back; the label-drag of a placed room *is* extract→move→join. The outline is the one definition of which walls are a room's — extract releases bound walls no outline edge names (row 36). Shuffle mode turns off every automatic joining pass through one accessor (`editing_enabled`): a moved room stays floating, nothing merges/welds/binds in passing, and information a mode defers is delivered at the explicit join. The doorway policy is tiered by ruling: snap-to-jamb within the gesture tolerance, else land-unwelded-and-report; never split, never refuse.

---

## 5. Open items

The **three dispositions** (next commit — see §1) · `_perimeter_span`/`_copy_spec` (→ **P4.4**'s read-back, as a question; register note authoritative) · the **clipboard path's binding/outline duality** (P4.4 must state its disposition) · defect **23** (→ P4.5) · defect **3** (groups serialize, P4.5) · defect **11** (z-order collapse, P4.5) · the **P3.1 split-on-write shim** (→ P4.5) · **two identity-churn sites** (→ P4.5) · the **`kind == "rigid"` carve-out** (retire or re-justify at P4.5) · **row 36's merge-rebind producer** (carried to P4.5, watched) · the **windows-latest CI leg** (row 27, open, not merge-blocking) · per-floor **visibility** (follow-up, not built).

---

## 6. Things that will waste your time if you don't know them

- **A running app keeps the code it imported** — the status-bar version label shows the launch identity; restart after any push before re-testing.
- **The timing lane is not in the gate**; `tools/gate.py --perf` runs it deliberately.
- **`gh` is not on `PATH`**: `& "C:\Program Files\GitHub CLI\gh.exe"` (PowerShell) or `"/c/Program Files/GitHub CLI/gh.exe"` (bash).
- **Files on disk are CRLF**; multi-line `\n` patterns silently match nothing.
- **Headless drags:** build `QMouseEvent`s with `buttons=LeftButton` to the viewport; `centerOn` first. **Headless keys:** construct `QKeyEvent`s with modifiers directly — never QTest Ctrl synthesis; the recorder's capture is pinned against the real delivery order.
- **Macro replay geometry matters:** a `.fpm` replays correctly only at the window geometry it was recorded at — the fiveRoomDragSplit pins run at 1400×1000+fit, the fuse-straggler pin at the default window; each test states which.
- **Patrick's macro loop** is the fastest reproduction channel: record in-app, commit the `.fpm` to `examples/`, replay headless via `win.run_macro`, pin verbatim.
- **The suite's console is cp1252** — no non-ASCII in test output.
