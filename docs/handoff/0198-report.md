# 0198 — report: PR #65 merged on his word (the record 0197 §7 owed); R6.0 — D50 measured, closed, and its receipt across all five multifloor plans; AMBER, stopped for his check

**Code, 2026‑09‑25, on [`0197-ruling.md`](0197-ruling.md).** First the record
[`0197`](0197-ruling.md) §7 names: Patrick's check of PR #65 passed — his
words, *"that fixed it, merge PR #65"* — and on that word
`roofs-r5e-grip-clamp` was landed on `main` at `299576a`, fast-forward,
the branch deleted local and remote; only `main` remains. That merge is
now in the numbered record, as every merge will be from here. Then R6.0:
branch `roofs-r6-0-d50` off `main` at `299576a`, PR #66 open, gate
GREEN, **stopped for his check** — 0197 §2 item 6's own acceptance, run
by hand: open a multifloor plan, set L2's elevation and height, save,
reopen, read them back unchanged.

## 1. THE LOADER, MEASURED FIRST — as 0197 §2 item 2 ordered

Before a line was written: each of the five plans of 0197 §1 was copied,
its L2 given `elevation_in 120` / `height_in 108`, opened with
`MainWindow.load_path`, and the live roster and the in-memory document
read. On all five:

| | loader → `Floor` roster | writer → `levels` |
|---|---|---|
| before the fix | `(name, <none>, <none>)` — `Floor` has attributes `name`, `reference` only | `(L2, 0.0, 96.0)` |

**Both halves were lossy, at one site each.** The loader
(`bridge.py`'s `apply_design_to_scene`, the `win.floors = [Floor(...)]`
line) built each `Floor` from the level's name and reference flag and
had nowhere to put the other two numbers; the writer (`bridge.py`'s scene
walk) emitted `0.0` / `96.0` literally. So D50's own round-trip receipt
could not have told the two apart, and a writer fixed alone would still
have round-tripped to zero — exactly the trap the ruling named.

## 2. THE FIX — fields first, then every reader

* **`model.Floor` gains `elevation_in` (0.0) and `height_in` (96.0)**,
  carried by `from_dict`/`to_dict` too, so the v4 project record (the
  legacy export) carries them as well — additive.
* **The loader puts the document's values onto the roster**
  (`apply_design_to_scene`), and **the three writers read them**: the
  scene walk (`_walk`'s level record), the **detect** path — its
  throwaway design now reads the live roster through the scene's window
  (`_floor_levels`) instead of a literal, the defaults only for a bare
  scene — and the **legacy importer** (`importer.py`), which reads a
  v4 floor's own two numbers when present. The v4 project ↔ roster
  conversions in `planio.py` carry them both ways.
* **Stored, not derived (0197 §2 item 3).** `new_floor_named` sets a new
  floor's elevation to **the floor below's elevation plus its height**,
  and its height to the floor below's; both are written, never
  recomputed on read. **Editable:** Floors ▸ *floor* ▸ "Elevation and
  height… (elev / height)" opens `FloorLevelsDialog` (two spin boxes; a
  basement may be negative); `set_floor_levels` is the non-interactive
  core — a roster edit, so an undo step and dirty, like rename.
* **No schema change** (0197 §2 item 5): `level` has carried both since
  v5 was vendored.

**Which height the existing code reads (0197 §2 item 4), measured, not
changed:** `viewer/fp3d.py` reads `height_in` as the level's **wall top**
(`top(level) = base + height_in`, capped per wall type by `WALL_H`) and
`elevation_in` as the level base every wall, floor slab, furnishing and
roof height sits on. The 2D editor reads neither: R3b reads each *room's*
`ceiling_height_in`, and every roof height is measured from the level
base (0140 §3) as a number — the base itself is only ever added in 3D.
So today the storey height IS the wall height in 3D, and nothing in this
tranche changes that; the dialog's note says so.

## 3. THE RECEIPT — D50's, verbatim, across all five plans

`tests/test_levels_elevation.py`, **12 tests** (`io`): for each of the
five plans (`farmplaceBIGmultifloor`, `roundedMultifloor`,
`crossfloor-snap-2026-08-17`, `wiscaway2026-08-30R1`, `R2`) — the
precondition that the corpus file says 0.0 everywhere, L2 set to
120 / 108, opened, the roster carrying both, saved, the file saying them
again, read the way `--list-levels` reads them; the zero-everywhere
control pinned as proving nothing; the new-floor default (96 then 192,
written into the document); the edit as an undo step, restored by undo,
a non-positive height and an unknown floor refused; the dialog seeding
and returning what was typed; the v4 project and the legacy importer
carrying the numbers; the detect path reading the roster and a bare
scene getting the defaults; and 0197 §6's question, measured: **a stored
elevation stacks the storeys in 3D by itself** — the upper wall's base
at its level's 108″, the lower wall's top at its 96″ storey height, the
upper's top at 108 + 100 — so **no z-order work (D11) is needed for
that; D11 stays its own record.** Three `test_model.py` expectations
that pinned the v4 floor record's exact shape moved with the additive
fields.

**D50 closes on this branch**, `closed: 2026‑09‑25`, `closed_by` the fix
commit, the defects index regenerated. [D67](../defects/0067-selection-is-not-scoped-to-the-active-floor.md)'s
out-of-date line (0197 §1) is left for when D67 is next touched, as ruled.

Full suite **1363 passed**, 7 deselected (`perf` lane), `ruff` clean,
gate GREEN — the branch's own run.

## 4. NAMED

* The macro records a new floor (`^+F "name"`, which now takes the
  default elevation deterministically) but has no token for the levels
  edit; a `LEVELS "name" elev height` token is one small addition if a
  recorded session needs it.
* The Floors menu entry shows the two numbers inline; no gallery
  screenshot shows a menu open, so the gallery is not regenerated.

## 5. `fixtures/incoming/`, with ages

`README.md` only.

## 6. WHAT HAPPENS NEXT

His check (§0 of the snapshot): a multifloor plan, L2's elevation and
height set, saved, reopened, unchanged. On his word PR #66 merges,
branch deleted in the merge step. **Then his one gesture (0197 §3):**
open `fixtures/wiscaway2026-08-30R2.json`, set L2's elevation to the
real storey height, draw a roof on L2 over the upper walls, save — that
file is the R6 fixture. Then R6.a (0197 §4's two answers), R6.b, the D67
reproduction, R6.c.

**Carried:** unchanged from [`0197`](0197-ruling.md).
