# 0280 — report: PR #93 merged on his word; his slow Ctrl+Z measured and fixed — the roofs' compose and their traces kept by value across the reload an undo is

**Landed:** PR #93 · 9a51df6 · 2026-10-17 · AMBER · checked by Patrick in the app: "the drags look right ... land #93"

**Code, 2026‑10‑17.** Two of his words, one report.

## 1. PR #93 MERGED

> *"land #93, then go ahead with undo steps 1 and 2"*

[`0279`](0279-report.md)'s branch landed on `main` at **`9a51df6`**,
fast-forward; [PR #93](https://github.com/pjm4github/FloorPlanner/pull/93)
MERGED; the branch deleted, local and remote. On `main` now: the
wall-and-room drag hold and the minimal repaint.

## 2. HIS QUESTION, MEASURED

> *"there is a question about undo (control-Z). I notice it takes 3
> seconds to complete. I see this when I drag W130 on the upper floor.
> Find why there is such a long delay."*

Undo in this app is snapshot-based: Ctrl+Z puts the previous **whole
document** back on the canvas (`_restore_state` → `load_data`), so every
item is recreated. On his `wiscaway2026-10-13R1.json`, after an edit beside
W130 on the upper floor (`undo_probe.py`; the probe's press reaches an
opening in W130 — any one-step undo takes the same reload):

| Part of one Ctrl+Z (`main`) | Time |
|---|---|
| Recompose the clips of all 15 roofs | ~1.0–1.4 s |
| Recreate every item, two document walks | ~0.3 s + |
| First repaint: every roof recomputing its clip trace | ~0.4 s |
| **Unprofiled total** | **3.6 s** (redo 1.7 s) |

The edit touched no roof. The compose reads **only the roofs** — their own
geometry and their levels' elevations — and the roofs came back
identical; they were new objects, so nothing recognised them.

## 3. THE FIX — on `undo-fast`, ONE commit on `main`'s tip, AMBER

**Step 1, the compose by value** (`roofs.sync_roof_clips`): the last
result is kept against the roofs' **values** — each roof's
`geometry_key()` and its level's elevation, as a sorted set — and handed
back when the same roofs are asked for again, whatever objects carry
them. A changed roof or elevation recomposes. Two identical roofs (a value
key that could not tell them apart) are never cached.

**Step 2, the trace by value** (`RoofItem.clip_trace`): when the identity
key misses — new objects after a reload — a scene-level cache keyed on the
roof's geometry and `floor_rooms_value_key` (each room's outline
coordinates, or its fallback path's polygons, and ceiling, and the floor's
thickest wall) answers before anything is computed. A changed room still
recomputes.

| | `main` | This branch |
|---|---|---|
| Ctrl+Z (unprofiled) | 3.6 s | **0.34 s** |
| Redo | 1.7 s | 0.34 s |
| The compose during it | ~1.0–1.4 s | 0 |
| The first repaint after it | ~0.4 s | ~0.08 s |

What is left of the 0.34 s is the reload itself (recreating every item,
~0.1 s) and the two document walks around it (~0.08 s each). Undo by
command (P6.b) is what would take those away; not built.

## 4. A SLIP, RECORDED

Capturing the "before" timing, a chained shell command ran `git stash pop`
after its `git stash push` had been skipped (the lint before it failed),
and so applied an **old, unrelated stash** from before this run ("WIP on
main: 863204a"), which conflicted on `SESSION_SNAPSHOT.md` and was kept,
not dropped. The working tree was restored to the committed snapshot file;
the old stash is still in the list, unchanged; no work was lost. The
probe's stash is now guarded (pushed and named, popped only if it is the
top entry).

## 5. RECEIPT

`tests/test_undo_fast.py` (6): the same roofs as new objects reuse the
compose with the right clips; a changed roof and a changed elevation
recompose; identical twin roofs are never cached; a reloaded roof over the
same rooms reuses its trace; a changed room recomputes it; an undo of a
wall edit end to end does not recompose and its clips equal a fresh
compose. Three of the six fail on `main` (the reuse); the three
correctness checks pass on both. `test_roofclip_cost.py`'s "the clip is a
function of the roofs alone" now pins both halves: the cache answers when
only walls are added, and a recompose forced past it is handed roofs
alone. `--quick` passed (1657); gate GREEN. `undo_probe.py` and its output
before and after in [`docs/evidence/0275-drag-timing/`](../evidence/0275-drag-timing/).

## 6. WHAT HAPPENS NEXT

His check of Ctrl+Z in the app. Named: undo by command (P6.b); DXF export
of annotations; his backlog (0248's items 8 and 9).

**Carried:** unchanged from [`0279`](0279-report.md).
