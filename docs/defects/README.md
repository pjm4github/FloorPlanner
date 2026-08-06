# The defect register

**One record per file**, `NNNN-kebab-slug.md`, zero-padded so `ls` sorts and a
lettered id files beside its parent (`0012a-…` follows `0012-…`).
[`INDEX.md`](INDEX.md) is **generated** from these files' front matter by
`tools/defects_index.py` and must never be hand-edited.

Split out of `docs/CODE_REVIEW_v2.md` §3 on 2026-08-06. Every record's
`## Record`, `## Site` and `## Milestone` sections are the register's three
cells **moved byte-for-byte** — 150 cells across 50 records, all verified
identical against the pre-move blob.

---

## The id is a permanent key, written `D23`

Independent of any tracker. GitHub numbers issues and pull requests from one
sequence and this repo already has ten PRs, so defect 23 will **not** be issue
#23. `github_issue:` carries the mapping if issues are ever created, so the
mapping lives in the repo rather than in a memory.

`tools/ref_audit.py` resolves every `defect N`, `row N` and `DN` reference in
the repository against these files; `python tools/gate.py --docs` fails on one
that resolves to nothing.

**A lettered id resolves to its parent when it has no record of its own.** `11a`
is a *half* of D11, named in its prose and never given a row; the audit reports
such a reference as resolved **via parent** and says so, rather than dangling
forever or pretending the distinction does not exist. `12a` is the one lettered
id that does have its own record, because the register gave it its own row.

## The headline changed: **38 defects, not 49**

Nothing was removed and nothing was closed. The categories got honest.

| | | |
|---|---:|---|
| `type:defect` | **38** | the product does something wrong |
| `type:gap` | 6 | something true goes unreported or unchecked |
| `type:limit` | 1 | structurally unclosable; accepted and recorded |
| `type:task` | 5 | correct as written, but must change |
| | **50** | records (ids 1–49 consecutive, plus `12a`) |

"49 defects" overstated twice: there are **50 rows**, and twelve of them were
never faults. Classification was proposed by Claude and ruled by Patrick; the
calls that could reasonably go the other way are named here so a reader can
disagree without re-deriving them:

* **D14, D15** (`area:perf`) — kept as **defects**. They produce correct output,
  only slowly, which is an argument for calling them something else. Patrick's
  ruling: *an operation that wastes time is doing something wrong, not merely
  doing it slowly.*
* **D27** (CI never runs the deep gate) — **gap**, not defect. The product is
  fine; the safety net is not.
* **D33** (stranding on dirty-baseline files) — stays **defect** although its
  stated mechanism was refuted and it closed as a duplicate. It was filed as a
  defect; `state` carries the outcome, `type` carries what it was.
* **D45** (`_edge_wall` answers by geometry) — reclassified by Patrick from gap
  to **task**: it is recorded, justified and known, so nothing is unreported.
  It works, and it must eventually change. That is a task.

## The fields, and why several are `null`

| field | rule |
|---|---|
| `id` `title` `rank` | `title` is the row's **own headline**, lifted, ≤99 chars, no trailing period. |
| `state` `state_reason` | `open`/`closed`; a closed record must say `completed` or `not_planned`. |
| `labels` | exactly one `type:`, exactly one `area:`, plus optional `status:`. |
| `milestone` | a phase from the Status table, **or `null`**. |
| `opened` `closed` `closed_by` | `null` unless the register states one **verbatim**. |
| `related` | D-numbers, never GitHub numbers. |
| `state_source` | `row` or `status-table` — see below. |
| `github_issue` | written back by `tools/defects_to_github.py --execute`. |

**Dates and shas are `null` almost everywhere, and that is deliberate.** The
register had four columns — id, defect, site, phase — and no date or commit
field; exactly one row names a closing sha. The alternative was to derive dates
from `git log`, and that was **ruled against**: git dates the record's first
appearance, not the defect, and *a derived date is worse than null because it
looks authoritative*. Where a date is present, the row states it. Where it is
`null`, the prose in `## Record` is still there to read.

**`milestone` is `null` on 29 records, and the gate only checks non-null
values.** Many Phase cells name no single phase — `Gate 3 (fixed, pre-merge)`,
`P3.6-followup`, `whichever task builds the 3D menu action`, `accepted limit —
recorded, not scheduled`, `DEEP HALF CLOSED at 65c4c02 (P3.8); WINDOWS HALF
OPEN`. The cell is preserved verbatim under `## Milestone`. A lint that failed
on correctly-recorded history is a lint that gets disabled.

**`sites` are verbatim strings and the gate does not resolve them.** Site cells
legitimately name deleted code (`rooms.py:29 (_RoomGrid, deleted)`), whole
directories (`tests/ (whole suite)`) and things that do not exist yet (`not yet
built`). A check that failed on those would punish accuracy.

### `state_source`: where a record's state was read from

`row` — the record says so itself. `receipt` — the record's state was **changed
after migration** on evidence recorded in its own `## Receipt` section (D3, D40).
`status-table` — **the record says nothing**,
and its state was read from the tick against its phase in the plan's Status
table. Fifteen of the terse early rows are four words and a phase id; their
state was only ever recorded in that tick box, in another document, and reading
the row alone would report every one of them as open.

### `status:partial` — because half-done is open

Six records have two halves (D3, D11, D13, D19, D20, D27). `state` describes the
**whole** record: closed only when every half is. On four of them both halves
have since closed, so the label would be noise; it is carried only by **D11**
(the runtime z-order half) and **D27** (the Windows CI half), which still
straddle. GitHub has no half-closed state either — this is a property of the
domain, not a workaround for our format.

### `rank` — preserved, and not more than it is

`rank` is the record's ordinal in the register's own row order, kept because it
exists nowhere else and file names sort by id. The register introduced its table
with one line, carried here verbatim because it is the only statement of what
the order means:

> Ranked by blast radius; each mapped to the phase that closes it.

**It is not a ranking throughout.** The review ranked roughly the first
twenty-one by blast radius; everything after that was *appended*, which is why
the rows are not in id order (17 precedes 16, 46 sits between 34 and 29). [`INDEX.md`](INDEX.md) offers both orders
so neither is privileged.

## The taxonomy is fixed, and the gate enforces it

```
type:    defect | gap | limit | task
area:    geometry | groups | io | ui | tests | docs | perf | schema
         | tooling | viewer
status:  carried | partial
```

`area:tooling` (CI, packaging, `tools/`) and `area:viewer` were added on
2026-08-06 because four records — D27, D39, D46, D40 — fitted none of the
original eight. A label that lies is worse than a label that is missing.

## The body: `## Record`, `## Site`, `## Milestone`

New records, and any record when it is **next revised**, take this shape:

```
## Symptom
## Mechanism
## Evidence     - measurements, with commands to reproduce
## Ruling       - what was decided and why
## Receipt      - how the close was proved
```

The 50 migrated records do **not**, and the reason is on the record: the
register wrote each row as one continuous argument in which symptom, mechanism,
evidence, ruling and receipt are interleaved — D23's ruling sits between two
measurements and its receipt is the closing clause. Dividing that into five
sections would have meant interpreting and rewording it, which would have cost
the byte-for-byte receipt that makes this migration checkable. So the corpus
converges on the new shape as records are revised, rather than being converted
by fiat. **`--docs` validates front matter, not body sections.**

---

## OPEN DECISION — who owns truth after migration?

**Recorded here, on disk, because it needs deciding only when issues are
actually created — and because a decision kept in a chat thread is not a
decision.**

After migrating to GitHub Issues, which is authoritative: **files, with issues
mirrored from them**, or **issues, with these files frozen as history**?

> **They must not both drift.**

`tools/defects_to_github.py` writes `github_issue:` back into each record, so
the mapping survives either answer. Nothing else about the question is settled.

---

---

## A content correction is never folded into a structural move

**Ruled 2026-08-06, and it is general.** When a move discovers that a record is
factually wrong — not misfiled, *wrong* — the move migrates it **as it stands**
and the correction lands in the **next commit**, with its own receipt.

Two reasons, and the first is the one that makes it a rule rather than a
preference:

1. **It keeps the move's verbatim receipt intact.** Every step of this refactor
   claims its moved text is byte-identical to what it replaced, and that claim
   is what makes the whole thing checkable. A single "while I was in there"
   correction turns a diff anyone can verify into a diff someone has to read.
2. **It makes the correction visible.** A state change buried among fifty
   relocations is invisible; a commit whose whole subject is "this record was
   wrong, here is the proof" is not.

**Two records were migrated knowingly wrong under this rule and closed
immediately afterwards:**

| | found | corrected |
|---|---|---|
| **D40** | its condition was met on 2026-08-03 and the row was never ticked — the message it required is at `mainwindow.py:532` with a test on it | closed at step 10 with `closed_by: 0a37581` |
| **D3** | its Phase cell still read *"is still open"*, written before P4.5 closed it; the only one of 50 records whose derived state disagreed with `SESSION_SNAPSHOT.md` | closed at step 10 with `closed_by: 52a6aed` |

Neither `## Record`, `## Site` nor `## Milestone` was touched in either. They
were true when written; the `## Receipt` section is the annotation, which is the
same discipline the register itself has always used.

## Standing notes

These four belong to no single record. They sat below the register's table and
are moved here **verbatim**; the first states that it is the authoritative copy
and is pointed at from the migration plan, so it must not be paraphrased or
duplicated. Read them in order — the second and third are questions the fourth
answers.

**Carried census note — P4.1 read-back, 2026‑07‑31 (this is the AUTHORITATIVE copy; the plan's P4.2 task text points here).** `_perimeter_span` (`rooms.py:304‑327`, 24 lines) does **not** die at P4.1, despite the claim on disk twice (the P3.5 log line, now annotated, and its own docstring, now corrected). Fresh census: it has two callers that outlive `fracture_delete_wall` — `_copy_spec` (`rooms.py:335`, the clipboard payload, **owned by no phase**) and `_privatize_shared_walls` (`rooms.py:785`, dies at P4.2). Its death is therefore **P4.2's at the earliest, and contingent**: it falls only if P4.2's real `extract` also reshapes `_copy_spec`. Stated as a contingency so P4.2's read-back inherits a **question, not a claim** — P4.2 must answer what happens to `_copy_spec` before counting `_perimeter_span` in its census.

**Standing disposition — `auto_bind` (ruled 2026‑08‑03, at the P4.3 dispositions).** `auto_bind` is **modelled, emitted and plumbed with no gateable site as of P4.3; its user-facing control is removed until one exists.** The census reasoning, quoted from the P4.3(1) record: *"auto_bind (dead): NO gateable automatic site exists today — measured over all 9 `bind_room_walls`/repair callers: Room tool `view.py:280`, paste `mainwindow.py:1348`, room_boolean `:849`, undo restore `:658` (constitutive of explicit gestures); load paths `planio.py:235`, `csvio.py:148`, `macro.py:413`; the explicit join `extract.py:218`; and the release repair family `walls.py:1968‑1975`, which is tear-repair of derived state and is exempted DELIBERATELY (gating it would reintroduce the mini-gate's stranding class)."* A checkbox would promise behaviour nothing enforces. The flag stays in `DEFAULT_SETTINGS`, the document's `settings.editing` block, and `editing_enabled()` (so shuffle's implies-off contract and the round-trip stay exactly as the schema states); the UI returns the day a task builds a genuinely automatic bind pass.

**ANSWERED at the P4.2 read-back by measurement, ruled (f), executed at P4.2:** the extract/join ops do **not** touch `_copy_spec` — the workflow it serves ("Copy room" → paste) is §4's *Duplicate a room*, which the plan assigns to **P4.4** (duplicate-as-template, `state: floating`). `_privatize_shared_walls` died at P4.2 as ruled (the label-drag rewire), so `_copy_spec` is now `_perimeter_span`'s **sole** caller. **Re-argued: `_perimeter_span` dies at P4.4, contingent on P4.4 building duplicate on the extract machinery per §4** — stated again as a contingency so P4.4's read-back inherits the question, not a claim. Not counted in P4.2's deletion census.

**RESOLVED AT P4.4, 2026‑08‑03 — the contingency fired YES and the whole family is gone.** Patrick ruled duplicate onto the extract machinery, so `_copy_spec` (35 lines) and `_perimeter_span` (24 lines) are **deleted**, and with them the clipboard's own third definition of "the room's walls" — a `bounding_walls()` proximity query over the scene, trimmed against the corners. What replaced it is a document operation: a room becomes a one-room v5 document and a one-room document folds back in as a floating room (`design/template.py`), with Copy/Paste putting a clipboard between the halves, File ▸ Save/Load template room a **file**, and Duplicate calling them back to back. **The consequence P4.5 was promised:** the binding-list/outline duality now has its clipboard consumer **resolved** — the template is cut from the outline (the one definition, P3.5 and row 36), and a *placed* room is cut out through the real ops (extract → template → join back) whose zero-offset round trip is exactly the P4.2 label-click path, pinned by `win.snapshot()` byte-equality across a template of a placed room.
