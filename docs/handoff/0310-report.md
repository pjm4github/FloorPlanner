# 0310 — report: the schema viewer swept to `main` — tidy graph, field-expand, cross-view highlight, and an edit-source/reload loop

**Code, 2026‑11‑10.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
`tools/schema_viewer.py` is his orthogonal, read-only JSON-Schema viewer (it
first reached `main` swept in beside the #3 merge, [`0308`](0308-report.md), §1).
He kept the next round HELD uncommitted in the working tree to run it first
([`0309`](0309-report.md) §5); on his word 2026‑11‑10 — *"sweep the schema_viewer
changes into main … create a means of opening the actual JSON schema document
and focus on the area of interest so that I can edit the source and reload the
schema to check again"* — it is swept to `main` **directly** with the new
edit/reload loop added. GREEN: a dev tool under `tools/`, no app behaviour and
no new app semantics; not a branch, not a PR. (No **Landed:** line — it is not
a PR merge, so the board does not track it as a landing.)

## 1. WHAT HE ORDERED

Two things, on top of the held round: **sweep** the schema-viewer work to
`main`, and **add a way to open the schema's source file at the area he is
looking at, edit it, and reload** — the look-at-it / edit-it / check-it-again
loop the viewer was missing (it could only *read* the schema).

## 2. WHAT WAS HELD, NOW SWEPT (built across 0309's session, his-checked)

- **A tidy containment tree** in place of the spaghetti — `_structure()` picks
  one primary parent per node (breadth-first from the root) so a node reached
  several ways is laid out once; `_compute_layout()` stacks by depth with a
  per-column de-overlap sweep; dragged positions and folds are remembered per
  schema in `~/.schema_viewer_layouts.json`.
- **`$ref` declutter** — dashed reference links show only for the selected node
  by default; an **All references** checkbox draws them all.
- **Double-click to expand fields** — a node with more than the six fields that
  fit shows `+N more (double-click)`; a double-click grows it to every field and
  the column reflows (session-only, not remembered).
- **Cross-view highlight** — clicking a node in the graph *or* a row in the tree
  shades the counterpart in the other view: **yellow**, or **light red** when it
  carries a finding. The echo survives a field-expand or a collapse.
- A latent **click-pins-node** bug fixed in passing: a plain click used to record
  the node's position as a manual override (freezing it against auto-layout); a
  drop is now remembered only when the node actually moved (> 2 px).

## 3. THE NEW EDIT-SOURCE / RELOAD LOOP (this session)

- **Edit source ↗** (Ctrl+E) opens the schema FILE in an external editor at the
  line that declares the **selected** node. `locate_pointer_offset()` walks the
  JSON pointer's keys, each search **scoped to the previous key's value span**, so
  `#/$defs/roof/properties/host` lands on the `"host"` line (220 in
  `design-schema.v6.json`), not a same-named key in a sibling. It copies
  `path:line` to the clipboard and names the line in the status bar, so even an
  editor that can't jump leaves him one paste away. Editor order:
  `$SCHEMA_VIEWER_EDITOR` → VS Code / VSCodium / Cursor (`-g file:line`) →
  Sublime → Notepad++ (`-n<line>`) → the OS default (no jump). (A `.cmd`
  launcher — VS Code's on Windows — is run through `COMSPEC`.)
- **Reload** (F5) re-reads the schema from disk, keeping the current folds,
  dragged positions, field-expansions and selection so the area under review
  stays put. A **broken edit** leaves the last good view up and reports it (the
  JSON parser's line/column is in the error) — fix it and Reload again.

## 4. VERIFICATION

`python -m ruff check tools/schema_viewer.py` clean. Headless smoke (offscreen):
the source-locate is accurate and scoped on `design-schema.v6.json` across a
spread of pointers (root, `$defs/*`, nested `properties/*`), the deepest key is
on its reported line, and two defs' same-named key resolve to different lines;
`load_file` returns success/failure; **Edit source** computes line 220 for
`roof.host` and copies `…:220`; **Reload** keeps the selection and the expanded
set and restores the highlight; a reload of a truncated file keeps all 34 nodes
up and reports the failure. On this machine the editor resolves to Notepad++
(VS Code is not on `PATH`; `$SCHEMA_VIEWER_EDITOR` overrides). Full gate GREEN.

## 5. NEXT

His to run — select a node, **Edit source ↗**, change the JSON, **Reload**. The
viewer stays under `tools/`, outside the app and the gallery. His either-gable-end
elevation follow-on is still AMBER on branch `gable-end-either`
([`0309`](0309-report.md), PR open), untouched by this sweep; the schema viewer
on `main` is a newer file than that branch carries until the branch merges, so a
checkout of the branch shows the previous viewer. 0248's items 8–9 named, not
ordered.
