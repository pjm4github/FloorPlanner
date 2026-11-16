# 0348 — report: the four report-PNG defects fixed, the text test added, the watcher restarted (PID 27380)

**Code (Claude Opus 4.8), 2026-11-16.** Answers [`0347`](0347-ruling.md). Tier:
**GREEN**, tooling only — `tools/plan_validate.py` (the render) and
`tools/plan_watch.py` (the failure card); no change to the result JSON, the
handshake, or the folder contract (`0347` §3).

## 1. The four fixes (`0347` §2)

1. **Text was hollow boxes — now the repo font.** The offscreen platform ships
   no font, so every glyph was `.notdef`. `plan_validate` now points
   `QT_QPA_FONTDIR` at `assets/fonts` **before** `QApplication`, calls
   `FP.load_fonts()` after, and draws every string in **`DejaVu Sans`**
   (`FP.FONT_FAMILY`) — the make_gallery recipe. Header distinct colours went
   2 → 18 on the same plan; the header, verdict, findings, panel titles and
   labels now read.
2. **Plan not fitted — now fitted to content.** Each level is fitted to the
   bounding rect of its own visible items plus a 4 % margin.
3. **Widget grab with scrollbars + forced-on callouts — now the SCENE.** The
   panel was `view.grab()`, which carried scrollbars and the callouts that
   `planio._finish_open` forces on at every open (0264). It now renders the
   **scene** (`scene.render`) with the **document's own Show settings** pushed
   back over the globals (`show_*` from the plan's `settings`), one level per
   panel (`show_other_floors` off), re-synced via `_sync_floor_state`.
4. **3D cropped — now framed.** `--fov 28` was telephoto; the house ran off the
   edges. Now `--fov 55 --zoom 1.45 --pitch -28`: the whole model is framed (the
   top and bottom rows of the 3D band are 100 % background on the test plan).

Verified on `wiscaway2026-11-14R1` (sent to Patrick): readable text, both
level plans fitted, callouts off, 3D whole-house. Render (step 6, incl. the 3D
process) is ~5 s as before.

## 2. The text test (`0347` §3)

`tests/test_plan_watch.py::test_report_text_uses_the_repo_font_and_renders_real_glyphs`:
asserts `QFontInfo(QFont(FONT)).family()` resolves to the repo font (not a
fallback), and that two different same-length strings (`PASS` / `FAIL`) render
to **different** pixels — a no-font render makes every glyph the same box, so
they would be identical. 7 tests in the file now, all `slow`, all GREEN in the
full gate. The app default font is set only inside `run_pass` (the subprocess),
NOT at module import, so importing `plan_validate` in-process for this test
cannot leak a changed default font into other tests' widget geometry.

## 3. Restart (`0347` §3)

- Stopped the old watcher (PID 17484).
- Restarted with the fixed code: `python tools/plan_watch.py` from the repo
  root. Its **live PID and heartbeat are in `fixtures/incoming/build/watcher.alive`**
  (the PID changes on each restart, so it is not pinned here). The counter
  continues across the restart.
- Note: the reviewer began the design loop as soon as the PNG read
  (`wiscaway-c01`, a PASS at `0006`), which is how `0349` was raised.

## 4. Housekeeping (`0347` §3)

The two smoke runs (`smoke-seed`, `smoke-two-rooms`) stay in `build/` as records;
their inputs are already tucked into their subfolders as `input.json` and the
top level is clean. Their stored PNGs are the old (boxed) renders — records of
what was run; new passes render with the fix. **Also gitignored `artifacts/`** —
the reviewer's design-run output (candidate plans, reports, throwaway generator
scripts) is transient scratch like `build/`, was untracked, and one of its
scripts (`candidate_01.py`, E741) was reddening the gate's ruff; `.gitignore`
now excludes it (ruff honours `.gitignore`), so reviewer scratch no longer gates
my commits.

## 5. Owed

- **Reviewer:** the seed inventory for Patrick's spec (WISC-FP-2026-11-16); the
  design loop can run now that the PNG is readable.
- **Code:** none outstanding for `0347`.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XVitzXNKQWS64xhKKpacra
