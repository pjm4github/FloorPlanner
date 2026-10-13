# 0271 — report: the documentation and the schema brought to this `main` as version 6, and a README of every command with an example

**Code, 2026‑10‑12.** His words, given while the leader was being built
([`0270`](0270-report.md)):

> *"Update the various documentation files and schemas (use V6 here) so it
> matches this version of main. Include a new readme that has a complete
> list of commands with examples."*

Built on `docs-v6`, ONE commit STACKED on `leader-annotation` (PR #89's
tip) so the documents describe the leader and the recorder's new tools
too; pushed; no PR of its own ([`0255`](0255-report.md)'s precedent: land
in turn, or fold into #89 on his word). The checkout on this branch runs
the app with all three tranches in it.

## 1. THE SCHEMA IS VERSION 6

* **The file** is `floorplanner/design/design-schema.v6.json` (renamed
  with `git mv`, its history kept); its title and `$id` say v6; its
  `version` description now names what 6 holds — the `roofs` block
  (0139 R1: gable, hip and shed forms, dormers with their openings, hip
  runs), the `annotations` block (0263, 0270: texts, measures, leaders,
  the datum), the openings' `sill_in`/`head_in` (0255), the `post`
  furnishing (0258), the Show settings (0263) — and that **5 is still
  accepted unchanged** (every later block is optional), so nothing about
  an existing file needs migrating to be read. The enum is `[5, 6]` as it
  was.
* **Every document the app writes is version 6**: `design_from_scene`
  (was 6 only with roofs — R1's discipline, now superseded by his word),
  the importer's converted document, a room template. The exporters
  (`fp2dxf`, `fp2pdf`) accept 5 and 6 as before. `validate.py`,
  `pyproject.toml`'s package data and the one test that reads the file
  by name point at v6.
* **ROADMAP.md's R‑B** (an additive field does not bump the version) gets
  a dated note under it: his word made the schema v6 for this `main` —
  nothing broke; the number now says what the document is. Not a breaking
  change; no migration.
* **The pins moved**: the writes that asserted 5 (`test_corpus_freeze`,
  `test_load_path`, `test_undo`, `test_extract`, `test_template`,
  `test_design_bridge`'s "stays v5") assert 6, renamed; the inputs that
  say 5 (the examples, `_rect_doc`, the fixtures) stay 5 and still
  validate — that is the point.

## 2. THE DOCUMENTS

* **`README.md`** rewritten from the head to the PNG-import section: what
  the app is, the v6 document and where its schema and model are, every
  feature that landed since the last rewrite (roofs with hip and shed
  forms and dormers, floors, the 3D view and the two viewers, the
  leaders, the sills, the posts, the PDF plan set's drawn dimensions, the
  Malformed-design report, the templates, the two macro languages), a
  short controls table pointing at the command reference, and a shorter
  headless section. The stale head — "Version 1.2 … `FILE_VERSION`,
  currently 4" — is gone. Everything from the PNG import to the licences
  is kept as it was: the Chief Architect workflow is a verified record.
* **`docs/COMMANDS.md`** (new): every command the app and its tools take,
  with an example each — run it; the eleven tools and the keys; the
  keyboard; every menu (File, Edit, View, Show, Rooms, Floors, Roof,
  Inventory, AI, Macro, Help); every context menu by what is under the
  pointer; the dialogs' fields; the original macro language's tokens; the
  v2 lines; the application commands; `fp_macro.py`, `fp_extract.py`,
  `fp2dxf`, `fp2pdf`, `fp3d`, `fp3dq`, `validate_design`,
  `migrate_to_design_v5`, `plan-snap`, the generators; the developer
  commands and the gate. Built from the code's own tables (the actions,
  the dialogs' rows, the parsers' arguments), not from memory.
* **`docs/design-schema.v6.md`** (new pointer, with a table of what v6
  holds and since when); `docs/design-schema.v5.md` annotated, kept.
* **`docs/README.md`** (the map): the schema row says v6 and the new
  pointer; `COMMANDS.md` gets its row; the macro row notes 0270.
* **`docs/ARCHITECTURE.md`**: the module roster gains a dated paragraph
  naming every module added since it was written — `vertex`, `labels`,
  `annotations`, `wallprops`, `problems`, `roofs`, `roofclip`,
  `commands`, `extract`, `design/`, `export/`, `macro2/`, `viewer/` — and
  the floors section says v5 and v6 are read, v6 written.
* **`docs/DESIGN_MODEL_v5.md`** §7, **`docs/SANITY_CHECK.md`**'s validate
  step, **`CLAUDE.md`**'s payload trap: the schema's name and version,
  each a one-line dated note; nothing rewritten.
* **`tests/README.md`**: the layout table rebuilt from `pytest.ini`'s
  markers and the files that carry each (the old table named seven
  files; there are ninety), the gate named, and three traps the suite
  has paid for (the silent Qt-handler death, the offscreen font engine's
  five-pixel floor, the headless modal).

Not touched, on purpose: the handoff mailbox, the progress log, the
evidence and the superseded documents (the record, annotated never
rewritten — [`docs/README.md`](../README.md)'s own rule); the examples'
generators (`make_site_demo.py` still writes a v5 example, which is a
valid document); the gallery (its shots predate the roofs and the
annotations — a `make_gallery.py` run with new frames is a tranche of its
own, named below).

## 3. RECEIPT

`--quick` passed; the docs lane GREEN (the reference audit resolves every
id; the renamed file's old name survives only in historical text, which
the audit reports and does not enforce, by its own rule); gate GREEN.

## 4. WHAT HAPPENS NEXT

His check of PR #89 and of this; land in turn or fold on his word. Named:
new gallery frames for the roofs, the annotations and the 3D view; DXF
export of annotations; his backlog (0248's items 8 and 9).

**Carried:** unchanged from [`0270`](0270-report.md).
