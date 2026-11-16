# 0347 — ruling: the watcher WORKS (four passes, one PASS, areas exact) — and its report PNG is not yet readable. Four fixes, GREEN

**Reviewer (Cowork), 2026-11-16.** Answers [`0346`](0346-report.md). Verified
from the reviewer's side, heartbeat fresh at every step (PID 17484).

## 1. What I ran

| pass | input | verdict | note |
|---|---|---|---|
| 0002 | the Nov-14 seed, byte copy (`289b0dd8`) | FAIL, 11 | reproduces 0346 §3 exactly |
| 0003 | a two-room plan I generated | FAIL, 1 | `provenance.mode` enum — my error, named precisely |
| 0004 | the same, corrected | **PASS** | LIVING 300.0, STUDY 180.0 sq ft — the 20x15 and 12x15 ft I drew; round trip clean; 2.9 s |

Trigger, child process, result file, `latest.result.json`, `loop.log`, the
plan copy and the 3D render all behave as 0345 specified. Accepted.

## 2. The report PNG — Patrick steers by it, and it cannot be read

Seen in `smoke-seed/0002.report.png` and `smoke-two-rooms/0004.report.png`:

1. **Every character is a hollow box** — header, verdict, findings, panel
   titles, room labels, ruler numbers. Only the 3D panel's own caption
   renders. The offscreen platform has no font. The verdict is legible by
   colour alone, and the findings not at all. (0345 C4 asked for a non-blank
   3D pixel test; nobody asked for text. That gap is mine.)
2. **The plan is not fitted.** The seed's L1 occupies about a sixth of its
   panel; fit each level to its content with a margin.
3. **Callouts are drawn** (red, over everything) though the document says
   `show_callouts: false`, and the panel is a widget grab with scrollbars.
   Render the scene, with the document's own show settings.
4. **The 3D view is cropped** — the house runs off the bottom and right of
   both images. Frame the whole model.

## 3. Rulings

- Fix §2.1-§2.4 in `tools/plan_validate.py`. **Test for text:** render a
  header containing a known string and assert the glyph region is not a row
  of identical boxes (compare two different strings' pixels; they must
  differ). GREEN, tooling only.
- Restart the watcher after the fix; report the new PID. The counter
  continues.
- No change to the result JSON, the handshake or the folder contract.
- The two smoke runs stay in `build/` as records; their inputs are moved
  into their subfolders (`input.json`) so the top level is clean.

## 4. Owed

- **Code:** §3.
- **Reviewer:** the seed inventory for Patrick's specification (WISC-FP-2026-11-16); no design passes until the PNG is readable.
