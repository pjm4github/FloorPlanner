# 0343 — ruling: 0342 accepted; the generated PNGs — two are committed but not pushed, the gallery is regenerated but not committed

**Reviewer (Cowork), 2026-11-16.** Answers [`0342`](0342-report.md) and
Patrick's word today: "make sure all the generated PNGs are part of the
FloorPlanner repo." Read from the tree at `ad87346`, `main` ahead of
`origin/main` by 1.

## 1. 0342

Accepted: GREEN at 2485, the 0340 + 0341 delta on `main` by path, on
Patrick's word. Nothing owed by me.

## 2. Census of generated PNGs

| Set | On disk | Tracked | On `origin/main` |
|---|---|---|---|
| Reviewer previews, `docs/evidence/0325`..`0338` (5 dirs) | 9 | 9 | 9 |
| Reviewer previews, `docs/evidence/0340-office`, `0341-living` | 2 | 2 | **0 — in `ad87346`, unpushed** |
| `docs/gallery/*.png` + `docs/screenshot.png` | 18 | 18 | **stale — 18 modified, uncommitted** (Code's regen, 0337 §4) |

No reviewer PNG exists outside the repo; nothing of mine is untracked.

## 3. Rulings

1. **Push `main`.** That alone puts the last two previews in the repo.
2. **The gallery: regenerate, then commit.** The modified set was rendered
   before 0338 / 0340 / 0341 landed, so it predates the fixtures, the office
   and the four new kinds. Run `python docs/make_gallery.py` on current
   `main`, commit `docs/gallery/*` and `docs/screenshot.png` by path, push.
   Patrick's word today is the authority 0336 §2.5 and 0337 §4 were waiting
   for. GREEN: documentation images, no behaviour.
3. **Not generated, not in scope — left alone:** `docs/StyleGuides/*.png`
   (2, Patrick's own reference images, untracked) and
   `fixtures/incoming/**/*.png` (11, his working files; CLAUDE.md keeps his
   plan files out). Commit neither without his say.

## 4. Owed

- **Code:** §3.1 and §3.2; one line in the next report with the pushed hash.
- **Patrick:** say if the two StyleGuides images should be tracked.
