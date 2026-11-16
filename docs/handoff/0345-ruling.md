# 0345 — ruling: build the PLAN WATCHER — a headless validator and report renderer the reviewer loops against. GREEN tooling; RED if it needs an app change

**Reviewer (Cowork), 2026-11-16.** 0344 accepted (PNGs in the repo, pushed).
Patrick's word today: he will give the reviewer a house specification; the
reviewer builds a plan JSON in a loop; **the app must validate every pass**;
he watches a PNG per pass and stops it if it goes wrong. The reviewer's shell
has no PyQt, so the app side runs on his machine, unattended. This is that.

## 1. What to build

`tools/plan_watch.py` (+ `tools/plan_validate.py` for one file, one pass —
the watcher calls it). Runs in the project venv. Watches ONE folder,
`fixtures/incoming/build/` (create it; add it to `.gitignore`).

**Trigger:** a `<name>.json` in that folder appears or changes. Ignore
anything in subfolders and any `*.tmp`. Debounce 1 s and require the size to
hold still; skip a file whose sha256 equals the last pass's.

**Each pass, in a CHILD PROCESS** (a crash or hang must not kill the watcher;
90 s timeout = a FAIL result, not a stall):

1. JSON parses; packaged schema (`floorplanner.design.validate.schema_errors`).
2. Invariants (`validate.check`, deep).
3. Boot the app, open the document with `interactive=False`; capture
   `_import_errors`, the status line, and anything `design/verify.py` raises.
4. Round trip: `design_document()` -> reopen -> `snapshot()` equal? Report
   what differs, not just that it does.
5. From the LOADED scene, not the file: per level, room names and areas;
   counts of walls, openings, rooms, furnishings, roofs; `build_model` notes
   and stats.
6. Render ONE PNG (§3).

## 2. What it writes — `fixtures/incoming/build/<name>/`

- `NNNN.plan.json` — a byte copy of the input this pass validated.
- `NNNN.result.json` — `pass`, `sha256`, `verdict` (`PASS` only if steps 1-4
  are all clean), each step's findings as lists of strings, step 5's data,
  `duration_s`, `git_head`, and a traceback string if anything raised.
- `NNNN.report.png` (§3).
- `latest.result.json` — written LAST, by rename, so its appearance means the
  pass is complete. The reviewer polls this file and nothing else.
- `loop.log` — one line per pass: number, time, sha (8), verdict, error count.
- `fixtures/incoming/build/watcher.alive` — rewritten every 5 s with the time
  and PID. The reviewer will not loop against a stale heartbeat.

`NNNN` is the watcher's own counter, zero-padded, continuing across restarts.

## 3. The report PNG

One image per pass, about 2400 px wide: a header band (plan name, pass
number, time, verdict in green or red, error count, first three findings);
the PLAN of each level, rendered by the app's own scene (room labels on); and
a 3D VIEW of the whole house. Use the path `docs/make_gallery.py` uses for
`20-3d-view.png` (`fp3dq --shot`, own process, windows platform) — D77 says
offscreen Quick 3D draws blank, so **prove the 3D panel is not blank with a
pixel test**, and if a pass cannot render it, the panel says "3D not
rendered: <reason>" rather than showing an empty frame. A plan that fails to
load still gets a PNG: the header and the findings.

## 4. Convergence and stopping

- **Converged** is the reviewer's call (app PASS and the spec met). The
  reviewer writes `fixtures/incoming/build/<name>.converged` containing the
  plan's sha256. The watcher then checks that its own last pass for that sha
  was `PASS`; if so it MOVES `<name>.json` to
  `fixtures/incoming/build/done/<name>.final.json`, copies the last report
  beside it as `<name>.final.png`, writes `watcher.stopped` with the reason,
  and exits. If the sha or the verdict does not match it writes
  `<name>.converged.refused` saying why, and keeps running.
- **Patrick stops it** with Ctrl-C, or by creating
  `fixtures/incoming/build/STOP`. Either way: `watcher.stopped`, clean exit.
- **Runaway cap:** 300 passes per plan name, then stop as above.

## 5. Conditions

- **C1 — it never writes outside `fixtures/incoming/build/`, never edits the
  input, never touches git.** The one move is §4's.
- **C2 — no modal can hang it.** Every app call takes its non-interactive
  path; the child's timeout is the backstop.
- **C3 — no app change.** If step 3, 4 or 5 cannot be done through what the
  app already offers, STOP and report: that is RED and needs its own ruling.
- **C4 — tests** (`tests/test_plan_watch.py`): a known-good plan gives PASS
  and a non-blank PNG; a plan with a dangling vertex reference gives FAIL
  with the finding named; a file that is not JSON gives FAIL, not a crash;
  the converged handshake moves the file on a match and refuses on a
  mismatch; `STOP` stops it. The watcher loop itself is tested with a
  temp folder, not the real one.
- **C5 — measure one pass** on a real plan (`wiscaway*` from
  `fixtures/incoming/`, copied in) and report the seconds, by step.

## 6. Then set the trigger

Gate, commit by path, push. Then START the watcher in a terminal that stays
open, from the repo root in the venv, and report in the next number: the
exact command, the PID, a fresh `watcher.alive`, the C5 timing, and the
first `0001.report.png` from the real plan (then clear that test plan out of
`build/`). GREEN — tooling, no behaviour change.

## 7. Owed

- **Code:** §1-§6.
- **Reviewer:** nothing until the heartbeat is reported; then the loop.
- **Patrick:** the specification.
