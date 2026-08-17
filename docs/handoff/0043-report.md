# 0043 — report: recovery closed out, measured against 0041 §3 and 0038's owed list

**Numbered `0043`, not `0042`: [`0042-ruling.md`](0042-ruling.md) (Patrick's
CI-lane question, unrelated to this recovery) landed on disk mid-session and
took `0042` first. This file was still uncommitted, so it was renumbered
rather than the committed convention being tested — no citation existed yet
to break.**

**Answering [`0041-ruling.md`](0041-ruling.md) §3 (the three things the recovery
owed) and, incidentally, giving the first real answer to
[`0038-ruling.md`](0038-ruling.md) §5's owed-list, since the artifact turned out
to already address most of it.** Everything below is read off `git status`,
`git diff` and the gate's own output just now — not from memory of the lost
session.

---

## 1. THE THREE THINGS 0041 §3 OWED — all done

1. **Gate re-run, not assumed.** It was right to re-run: the first full-mode run
   came back **RED** — one new `ruff` finding, `B905` (`zip()` without an
   explicit `strict=`) in `fp2dxf.py`'s opening-overlap scan
   (`emit_wall`'s span check, iterating `spans` against `spans[1:]`). Fixed with
   `strict=False` — the two sequences are pairwise-offset by construction, not
   a bug. Re-run: `collected=734 ruff=clean vacuous=0 end_assign=0
   snapshot=current`; OFF/ON/DEEP all `727 passed, 7 deselected`; **GREEN**.
2. **Committed, named as a recovery.** `5d61f1f`, message states plainly it is
   a recovery and not a checkpoint, per [0041](0041-ruling.md) §3's own
   instruction not to imply one was taken. Contains: `floorplanner/export/`
   (both files, with the `strict=` fix folded in — there is no separate
   "recovery fixed a bug" commit, since the bug was found *by* the recovery's
   own gate re-run), `docs/SESSION_SNAPSHOT.md`, `docs/handoff/README.md`, and
   the four handoff files plus the zip that were sitting untracked
   (`0038-ruling.md`, `0039-report.md`, `0040-ruling.md`, `0041-ruling.md`,
   `0038-fp2dxf-handoff.zip`). **Left alone, deliberately:** the CRLF-only
   diffs across `assets/` — pre-existing at session start (SESSION_SNAPSHOT
   §5's own named class), unrelated to this work, not staged.
3. **This report.**

## 2. WHAT'S DONE ON THE OWED LIST — more than 0041 §2 credited

[`0041`](0041-ruling.md) §2 read the artifact as far as the package placement
and the by-path rule. Measuring the rest of [`0038`](0038-ruling.md) §4's three
hygiene faults against the actual file, **all three are already fixed**, not
merely "under way":

| 0038's fault | status | where |
|---|---|---|
| `raise SystemExit` inside `convert()` | **fixed** | `fp2dxf.py:468` raises `ValueError`, with a comment citing 0038 §4 by name and explaining why (Qt-override segfault risk, `SESSION_SNAPSHOT` §5) |
| `print()` as the only progress channel | **fixed** | `convert()` never calls `print()`; skips/summary/warnings all land on `ConvertResult` (`.skipped_levels`, `.summary`, `.warnings`, `.written`). `print()` survives only in `main()`, the CLI entry point, which is the correct place for it |
| `out.write_text(...)` with no encoding | **fixed** | both writes (`out.write_text`, the openings sidecar) pass `encoding="utf-8"` explicitly, with a comment naming the cp1252-on-Windows / non-ASCII-room-name failure mode |

**Also done:** thickness reads live from `floorplanner.design.validate.STD_T`
by path (`fp2dxf.py:73-93`, docstring names the D73/D74 precedent by name) —
the module-level `THICKNESS`/`WALL_TYPE_NAMES` split keeps a name-to-Chief-type
mapping separate from the real quantity, which was the actual defect shape.
The dead `stem` assignment 0038 flagged is gone (confirmed by grep, not just
by [0041](0041-ruling.md)'s say-so).

**One gap in the encoding fix, not in 0038's original list:** `main()`'s
`a.design.read_text()` (line 542) has no explicit encoding — only the *write*
side was named in the ruling, so this isn't a regression against what was
asked, but a non-ASCII design file opened on a non-UTF-8-default system would
still be at risk on the read path. Flagging, not fixing — out of this
recovery's scope.

## 3. WHAT'S NOT DONE — unchanged from 0041 §1, still true

- **The zip is still packed.** `docs/handoff/0038-fp2dxf-handoff.zip` is
  untouched (27 entries, same CRC as `0040`'s check). Unpacked into it:
  `sample/` (3 JSON + 2 DXF), `screenshots/` (16 PNGs), and `README.md` — none
  of the three are anywhere in the repo tree yet.
- **No `docs/evidence/chief-export/`** — doesn't exist. Downstream of the zip
  being unpacked.
- **No golden-file test.** [0038](0038-ruling.md) §4 named this as
  nearly-free once the sample lands; it can't start before the sample does.
- **No README split** (handoff spec vs. user docs) — the only README that
  exists is the one still inside the zip.

**None of this is a new blocker.** [0038-ruling.md](0038-ruling.md) §5 already
put the placement/unpack/delete-the-zip step in the landing commit, and that
commit hasn't happened — this recovery only needed the code on disk to be
real and green, which it now measurably is.

## 4. ORDER — unchanged, and one thing still owed ahead of new numbers

Per [0041](0041-ruling.md) §5: this closes the recovery tier (GREEN, nothing
merged, nothing behavioural). **[0040](0040-ruling.md) §4's remedial —
cherry-picking `0033`, `0034`, `0035` and `0036-report.md` from
`shower-identity-redraws` onto `main` as a doc-only commit — is still owed and
still gates further numbered work**, per that ruling's own words. This report
is the direct completion of `0041`'s own §3, not a new topic — but
[`0042-ruling.md`](0042-ruling.md) landing mid-session, on a question this
report never touches, is itself a fresh instance of `0040`'s §4 pattern (the
mailbox disagreeing with itself across two writers). The cherry-pick is next,
ahead of anything else, including `0042`'s own CI-lane change.
