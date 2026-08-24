# docs/ — the map

**What each document is, which ones are authoritative, and which are history.**

> **This map was written first, deliberately.** It describes the structure the
> docs refactor is building, so the remaining steps have something to follow.
> For a few sub-commits it therefore names directories that do not exist yet —
> `defects/`, `progress/`, `handoff/`, `superseded/`. Each arrives with its own
> commit and its own receipt. If one is missing while you are reading this, it
> is still in flight, not lost.

---

## Start here

1. **[`SESSION_SNAPSHOT.md`](SESSION_SNAPSHOT.md)** — where the work stands,
   what to read in what order, and the traps that waste time. It is an **index
   and a state marker, not a second copy of the record**: where it points at
   another document, that document wins.
2. **[`../CLAUDE.md`](../CLAUDE.md)** — architecture and house rules.
3. Then whichever of the below the task needs.

---

## Authoritative — these decide things

| document | what it is |
|---|---|
| [`WORKING_AGREEMENT.md`](WORKING_AGREEMENT.md) | The standing rules: census doctrine, gate discipline, what a receipt is, how vacuity is detected, what a green signal is evidence of. **Extracted from the migration plan because it outlives the migration** — these rules bind Phase 5, Phase 6 and whatever follows. |
| [`ROADMAP.md`](ROADMAP.md) | **What may proceed without Patrick, and what may not.** Tiers every remaining item GREEN / AMBER / RED, and carries the rulings issued with them. Code does not self-classify; the tiers are also recorded in the plan. |
| [`V5_MIGRATION_PLAN.md`](V5_MIGRATION_PLAN.md) | The Status table (every task and its tick), the phase specifications, the risk register and the sequencing rationale. **What is planned and what is done.** |
| [`DESIGN_MODEL_v5.md`](DESIGN_MODEL_v5.md) | Why the room is the durable unit and walls are an optional binding onto its outline. The rationale behind the schema. |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | The module layout roster, phase-history pointers, extract/join and floors mechanics, and the performance measurements moved out of `CLAUDE.md` at [`handoff/0085-ruling.md`](handoff/0085-ruling.md) — `CLAUDE.md` itself is traps only now. |
| [`design-schema.v5.md`](design-schema.v5.md) | A **pointer**, not a stub. The schema itself was vendored into the package at P0.7 and lives at `floorplanner/design/design-schema.v5.json`; this file remains so references to the old location still resolve. |
| [`defects/`](defects/) | The defect register — **one file per record**. See below. |
| [`SANITY_CHECK.md`](SANITY_CHECK.md) | The three manual gates and their outcomes. The only checks a human has to perform by hand. |
| [`macro_language.md`](macro_language.md) | The headless macro grammar and driver — the interface a script or an AI system drives the editor through. |
| [`../floorplanner/viewer/VIEWER_NOTES.md`](../floorplanner/viewer/VIEWER_NOTES.md) | The 3D viewer track: architecture, the renderer decision, and the hard-won specifics. Lives beside its code on purpose. |

## The record — what happened, and what proved it

| document | what it is |
|---|---|
| [`progress/`](progress/) | The progress log, split by phase. **Contemporaneous and verbatim** — its value is that it was written at the time, not that it is tidy. Nothing in it is edited after the fact; a later correction is a later entry. |
| [`evidence/`](evidence/) | Measurements and the probes that produced them. **Cited, never inlined**: a record names its artifact and the command that reproduces it. |
| [`handoff/`](handoff/) | The agent mailbox — reports and rulings, each authoritative only from its file. See [`handoff/README.md`](handoff/README.md) for the protocol. |

## History — kept, not current

| directory | what it is |
|---|---|
| [`superseded/`](superseded/) | Documents that no longer direct the work. **They are kept because they hold material that exists nowhere else** — see the warning below. Each carries a one-line header saying what replaced it, or that its work simply shipped. |

## Generated — never hand-edit

| | |
|---|---|
| [`gallery/`](gallery/) + `screenshot.png` | Built by `python docs/make_gallery.py` from one demo plan. When a feature changes the UI, regenerate; do not edit the PNGs. |
| [`defects/INDEX.md`](defects/INDEX.md) | Generated from the defect records' front matter. The gate fails if it differs from a regeneration. |

---

## `superseded/` holds UNIQUE material, not ignorable material

**This is the part of the map most likely to be misread, so it is stated
plainly.** "Superseded" means *no longer the plan*. It does not mean *safe to
skip*, and in at least one case it is the opposite:

* **`CANVAS_ITEM_REFACTOR_PLAN.md`** records the **group/drag trace** and the
  recovered **`test_zz*` forensics**. Its own header says these are *"not
  duplicated elsewhere"*, and that is still true — nothing in the v5 plan
  reproduces them. It is superseded as a plan and live as a source.
* **`CODE_REVIEW.md`** and **`REFACTOR_PLAN.md`** are the only record that the
  repository-root clutter was ever a finding — a finding this refactor closes.

**Two things follow, and the second is a lesson this repo has already paid for.**
First, a document moving here loses its authority, never its content: nothing is
deleted and nothing is rewritten, only headed. Second, **`superseded/` is not
excluded from any lint, gate or search.** There was once a `docs/_superseded/`,
hidden behind a leading underscore and a ruff exclusion; P0.1 found 23 lint
findings rotting inside it and the whole directory was moved to `_to_delete/`
and dropped. The plan's own log put it exactly: *dead drafts kept alive behind a
lint exclusion is exactly how scaffolding rots.* The underscore and the
exclusion were what made that possible. This directory has neither.

---

## The defect register: `defects/`

**One record per file**, `NNNN-kebab-slug.md`, zero-padded so `ls` sorts and a
lettered id files beside its parent.

**The id is a PERMANENT KEY and is written `D23`.** It is independent of any
tracker. GitHub numbers issues and pull requests from one sequence and this repo
already has ten PRs, so defect 23 will *not* be issue #23 — which is exactly why
the reference form never becomes a `#`. `github_issue:` in the front matter
carries the mapping if and when issues are created, so the mapping lives in the
repo rather than in someone's memory.

Each record carries YAML front matter (`id`, `title`, `state`, `state_reason`,
`labels`, `milestone`, and provenance) and a fixed body: **Symptom ·
Mechanism · Evidence · Ruling · Receipt**. The rules that govern the fields —
including why several are `null` rather than derived, what a *partial* record
is, and what `rank:` does and does not mean — are in
[`defects/README.md`](defects/README.md), beside the records they bind.

`tools/ref_audit.py` resolves every `defect N` / `row N` / `DN` reference in the
repository against these files. `python tools/gate.py --docs` fails on one that
resolves to nothing.

---

## Two rules that apply to every document here

**Annotate, do not rewrite.** A document that was true when written stays as it
was; what changed goes in a dated note, a later log entry, or a new file. The
progress log is worth reading precisely because nobody went back and tidied it.

**Cite the artifact, do not inline it.** A record names its evidence file and
the command that reproduces it. A progress entry cites its handoff file when one
exists (`handoff: 0042`) rather than restating the exchange — the log is
curated, the mailbox is raw, and collapsing the two would make the log inherit
the exchange's verbosity.
