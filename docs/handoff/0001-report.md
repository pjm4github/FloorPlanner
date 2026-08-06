# 0001 — report: docs refactor, read-back

**From:** Claude Code · **To:** Patrick · **2026-08-06** · branch `docs-refactor`
**Ruling:** [`0001-ruling.md`](0001-ruling.md) · **Progress:**
[`../progress/side-tasks.md`](../progress/side-tasks.md)

> Transcribed to disk at step 9 of the task it governs, because the mailbox did
> not exist when the exchange happened — the protocol it demonstrates is the
> thing the exchange built. Later reports are written here first.

---

## Verification of the brief's own measurements

Every number in the brief was checked against disk and **every one was
correct**: plan 5,216 lines / 417,043 bytes with section boundaries at 1, 9,
295, 344, 843, 860; register 156 lines / 107,749 bytes; the four stale
candidates at 34,076 / 10,427 / 11,404 / 11,499 bytes; one screenshot at 0
bytes. The progress log measured 4,356 lines as the brief stated — that is the
log *body*; including its heading it is 4,357.

`docs/design-schema.v5.md` — flagged in the brief as unknown — is a **live
pointer, not a dead stub**. Its own last line: *"This pointer remains in `docs/`
so references to the old location resolve."* Six inbound references. It stays.

## Findings that changed the work

**A. The register holds 50 rows, not 49**, and `11a` is not one of them. Ids
1–49 are consecutive; `12a` is the one lettered row. `11a` is a *half* named
inside row 11's prose. Splitting it out would rewrite prose while moving it.

**B. Six rows have two halves, and one `state` cannot describe them.** D11
(`11a done · runtime half CARRIED OUT`), D27 (`DEEP HALF CLOSED · WINDOWS HALF
OPEN`), D13, D19, D20, D3.

**C. A milestone check against the Status table would fail on most rows.** Real
Phase cells include `Gate 3 (fixed, pre-merge)`, `P3.6-followup`, `whichever
task builds the 3D menu action`, `accepted limit — recorded, not scheduled`.

**D. `opened`, `closed` and `closed_by` do not exist on disk.** The register has
four columns — id, defect, site, phase. Exactly one row names a closing sha.

**E. `sites` cannot be a list of `path:line`.** Cells legitimately name deleted
code (`rooms.py:29 (_RoomGrid, deleted)`), whole directories, and things not yet
built. A check that resolved them would go red on correctly-recorded history.

**F. Row order encodes ranking and filenames destroy it.** The register's own
line: *"Ranked by blast radius; each mapped to the phase that closes it."* The
rows are not in id order — 17 precedes 16, 46 sits between 34 and 29.

**G. Four standing notes sit below the table and belong to no row.** The first
says it is the AUTHORITATIVE copy and is pointed at from the migration plan.

**H. The root clutter is untracked, and two thirds already ignored.** All eleven
files are untracked; `snip.png` and `trial-export-rooms.csv` are in
`.gitignore`. **Moving them to `docs/evidence/` would ADD them to the repo.**
*(Correction issued later: `_tot.png` is also already ignored, by `_*.png`.)*

**I. The four documents are superseded by two different mechanisms.**
`CODE_REVIEW.md` and `CANVAS_ITEM_REFACTOR_PLAN.md` by a document, each saying
so itself; `REFACTOR_PLAN.md` and `TODO.md` by *completion* — they name no
successor because the work shipped. `CANVAS_ITEM_REFACTOR_PLAN.md` has **zero
inbound references** yet its own header says its `test_zz*` forensics are
duplicated nowhere.

**J. Step 0 and step 9 only compare if the pattern set is frozen.** Ad-hoc
greps disagreed with each other (213 / 58 / 35 / 32 by one spelling). Requested
scope addition: `tools/ref_audit.py`.

**K. Two mechanical cautions.** The verbatim proof must compare against the
pre-move blob with endings normalised once. Adding `--docs` to the default gate
block would change the trailer's shape partway through the branch.

## Raised at step 5, after reading the rows

**Ruling 1 — the five body sections do not exist in the source.** The register
writes each row as one continuous argument in which symptom, mechanism,
evidence, ruling and receipt are interleaved. D23's ruling sits *between* two
measurements; its receipt is the closing clause. Splitting requires
interpretation and rewording.

**Ruling 2 — the area taxonomy has no bucket for four rows.** D27 (`ci.yml`),
D39 (packaging), D46 (`tools/`), D40 (viewer).

**Finding — D40's requirement is already implemented and the row does not say
so.** It required, verbatim, *"report '3D view needs `pip install -r
requirements-viewer.txt`' through the status channel"*. On disk:
`mainwindow.py:532` `VIEWER_HINT`, asserted at `tests/test_viewer_popup.py:139`.
Not closed here — changing a row's state is the edit-while-moving the principles
forbid.

## The type breakdown

50 records. **38 defect · 6 gap · 1 limit · 5 task** (after ruling addition 1
moved D45 to task). "49 defects" overstated twice: there are 50 rows, and twelve
were never faults. Debatable calls named for the record: D14/D15, D27, D33, D45.

## Reported later in the same task

**D3 disagrees with the snapshot.** Derived states agree with
`SESSION_SNAPSHOT.md` on 49 of 50 records. D3's Phase cell still says the
remaining half *"is still open"*, written before P4.5 closed it. Migrated open,
as the register has it.

**`--execute` was run by accident and reached the GitHub API.** It failed on the
missing-label ordering it documents. Verified immediately: no issue exists, no
record carries a `github_issue`, `git status` clean. The tool now requires
`--yes`.
