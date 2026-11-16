# 0344 — report: the generated PNGs are in the repo — gallery regenerated on `main` and committed, the two reviewer previews and the gallery pushed (0343 §3)

**Code (Claude Opus 4.8), 2026-11-16.** Answers [`0343-ruling.md`](0343-ruling.md)
and Patrick's word ("push main" / "make sure all the generated PNGs are part of
the FloorPlanner repo"). Tier: **GREEN, docs-only** — no behaviour, documentation
images and records.

## 1. Done

- **§3.2 — gallery regenerated and committed.** Ran `python docs/make_gallery.py`
  on current `main` (`ad87346`, which now carries the `0338` fixtures, the `0340`
  office set and the `0341` furnishings), so the images reflect what the app
  actually renders. Committed `docs/gallery/*` (18 panels) and
  `docs/screenshot.png` **by path** — closing the long-open "gallery regenerated
  but uncommitted" item (`0336` §2.5, `0337` §4), now on Patrick's word.
- **§3.1 — pushed.** `main` pushed to `origin/main`. That carries into the repo
  both the `0340-office` / `0341-living` reviewer previews (committed in
  `ad87346`, previously unpushed) and this gallery/records commit.
- The `0343` ruling and this report ride the same commit; the status board lists
  both.

## 2. Left alone (§3.3)

`docs/StyleGuides/*.png` (2 — Patrick's own reference images, untracked) and
`fixtures/incoming/**/*.png` (his working files; CLAUDE.md keeps his plan files
out of the repo). Neither committed. **Patrick:** say if the two StyleGuides
images should be tracked (`0343` §4).

## 3. Note — the reviewer lane was live throughout

Across `0340`–`0343` the reviewer (Cowork) was producing rulings continuously
(the `0341` ruling and the `0343` ruling each appeared mid-operation). Each new
`docs/handoff/NNNN-*.md` invalidates the committed status board until it is
regenerated, which reddens the gate's `test_status_index` and blocks a push. It
was absorbed each time, but a clean push needs the lane to pause briefly.

## 4. Owed

- **Code:** none outstanding for `0343`.
- **Patrick:** the StyleGuides-images question (§2).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XVitzXNKQWS64xhKKpacra
