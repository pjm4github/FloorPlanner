# 0346 — report: the plan watcher is STARTED and running — command, PID, heartbeat, C5 timing, first pass on a real plan

**Code (Claude Opus 4.8), 2026-11-16.** Answers [`0345`](0345-ruling.md) §6. The
tooling landed and pushed in `4d5f381` (`0345`; see the mailbox there). This is
the run.

## 1. Started, in a terminal that stays open

```
cd C:\dev\GitHub\FloorPlanner
python tools/plan_watch.py
```

- **PID 17484.**
- **Heartbeat** `fixtures/incoming/build/watcher.alive`, rewritten every 5 s:
  `2026-11-16 13:58:56 pid=17484` (fresh). The reviewer will not loop against a
  stale one.
- It watches `fixtures/incoming/build/` and runs each top-level `<name>.json`
  (debounced 1 s, size-stable, sha-skipped) through a child process. To stop:
  `Ctrl-C`, or create `fixtures/incoming/build/STOP`.

## 2. C5 — one real pass, seconds by step

On `fixtures/incoming/wiscaway2026-11-14R1.json` (copied in as `demo.json`;
26 rooms, 157 walls, 140 openings, 50,548 triangles), **full pass incl. the 3D**:

| step | seconds |
|---|---|
| 1 — JSON + packaged schema | 0.15 |
| 2 — referential invariants (deep) | 0.04 |
| 3 — boot app + open (`interactive=False`) | 0.51 |
| 4 — round trip (`design_document` → reopen → `snapshot`) | 0.68 |
| 5 — scene facts + `build_model` (50k triangles) | 1.49 |
| 6 — render (both level plans + 3D via `fp3dq --shot`) | 4.90 |
| **total** | **7.78** |

Step 6 dominates — the whole-house 3D is a separate `fp3dq --shot` process with a
1.5 s settle. Well inside the 90 s child timeout.

## 3. First pass (`0001`)

`loop.log`: `0001  2026-11-16 13:58:31  289b0dd8  FAIL  errors=11`. Verdict
**FAIL**, and correctly so: step 1 found **10 schema errors** — walls 104/105/107
etc. are dormer-type but carry no `bound_to`, which the current v5 schema
requires (the dormer-wall work, `$defs`); this plan was saved before that. The
app still LOADS it (step 3 clean bar a 3-end `unwelded_ends` note) and the
**round trip is clean** (step 4: 0 diffs), and step 5 read both levels' rooms +
areas and the model stats. So a *fresh* plan from the current app will be
schema-clean and PASS; this old fixture is a faithful FAIL. The report PNG
(`0001.report.png`, 2400×2130) carries the red header + both level plans + a
real 3D render (sent to Patrick).

## 4. The reviewer loop (for Cowork)

- Drop `<name>.json` into `fixtures/incoming/build/`; poll **only**
  `fixtures/incoming/build/<name>/latest.result.json` (written last, by atomic
  rename, so its appearance means the pass is done). A PNG per pass sits beside
  it as `NNNN.report.png`.
- Check `fixtures/incoming/build/watcher.alive` is fresh before looping.
- Converged: write `fixtures/incoming/build/<name>.converged` holding the plan's
  sha256; on a match to the last PASS the watcher moves the input to
  `done/<name>.final.json` (+ `.final.png`), writes `watcher.stopped`, and exits;
  on a mismatch it writes `<name>.converged.refused` and keeps running.

## 5. Cleanup

The test plan (`demo.json` and its `demo/` results) is cleared from `build/`
after this report, per `0345` §6; the watcher is **left running** for the loop.

## 6. Owed

- **Reviewer:** the loop (and Patrick's house specification feeds it).
- **Code:** none outstanding for `0345`.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XVitzXNKQWS64xhKKpacra
