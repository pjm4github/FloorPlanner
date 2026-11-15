# 0336 — ruling: status at `17548c8`. Lights and Phase 2 are on `main`; the stair delta (0335) is NOT committed and NOT gated; one report is owed

**Reviewer (Cowork), 2026-11-15, 19:34 UTC.** Read from the tree and the log,
not from a report: there is none after 0334. Supersedes 0335 §4 only.

## 1. What the record shows

| | state | evidence |
|---|---|---|
| Furnishing delta (0333) | on `main`, pushed | `0a73b94`, 0334 |
| `lights-3d` (0333 §3) | **merged, pushed** | `eed4c4a`, on Patrick's walk; gate 2318 GREEN |
| `camera-phase2` (0328) | **merged, pushed** | `17548c8`, on Patrick's walk; gate 2349 GREEN, OFF+ON |
| Stair delta (0335) | **working tree only** | 7 modified + `tests/test_stair_rails.py`, evidence, 0335 itself untracked |
| `.gate-result.json` | GREEN, written 18:28 UTC | **an hour BEFORE the stair edits (19:29)** — it says nothing about them |

`main` = `origin/main`. No unmerged branch, no stray lock.

## 2. Rulings

1. **The standing gate result does not cover the stair delta.** Re-gate with
   it in the tree before any commit. Expect about 2349 + 29.
2. **0335 §4 is amended:** "apart from lights-3d and Phase 2" is moot, both
   have landed. Branch off `17548c8`; commit by path — the 7 modified stair
   files, `tests/test_stair_rails.py`, `docs/evidence/0335-stair-rails/`,
   `docs/handoff/0335-ruling.md` and this file. **Not** `assets/icons/*`,
   `docs/gallery/*`, `docs/screenshot.png`, `fixtures/incoming/*`.
3. **Still AMBER.** Gate GREEN lets it commit on the branch; it merges on
   Patrick's check (0335 §5), not before.
4. **Phase 2 landed without a build report.** The merges are sound on what I
   can read — Patrick's word is quoted in both, the gates reconcile, and
   `test_camera_phase2.py` carries a test for the `setPos` round trip, the
   canvas clamp, view-local pitch, one-snapshot undo, Esc, and C4's four
   releases. But the channel has no record of it. **Owed in the next report,
   short:** (a) that it was built on **Option B**, not the Option A 0328
   ruled, and the C1 measurement or reason that sent it there — C1 permits
   the fallback, the record must say it was taken; (b) how C2 is met (the
   write-back leaves QML before it touches the scene) and what pins it;
   (c) the fp3dq.py conflict resolution, as the merge message has it.
5. `assets/icons/*` and `docs/gallery/*` have sat modified through three
   landings. Code: say whose they are, or that you do not know. Do not commit
   or revert them without Patrick.

## 3. Owed

- **Code:** gate + branch commit of the stair delta; the report in §2.4;
  failures verbatim.
- **Reviewer:** fixes from that report. No git.
- **Patrick:** the 0335 §5 check, one sitting.
