# 0316 — report: annotation numbers (W/O/V/R/F/RF/C) now SURVIVE a save/open cycle, and a FIND tool jumps to any of them — on branch `find-and-labels`

**Code, 2026‑11‑11.** The record ([`0197-ruling.md`](0197-ruling.md) §7). His
order 2026‑11‑11, in the same message that landed the camera content switches:
*"inspect the way that the json floorplan is saved and the walls and openings are
numbered. Let's try and preserve the annotation values between save/open/refresh
cycles so that I can find a certain W or O in the design. I want to have a 'find'
tool that lets me find/zoom to an annotated item."* Then, settling the shortcut
clash: *"change the floor selection to L (for LEVEL) then we can use F for
find."* Built on branch `find-and-labels`; **his word: "land it and merge"** —
report on `main`, the one branch commit, then merged.

## 1. WHAT WAS WRONG (the inspection he asked for)

The number on a callout — `W47`, `O3` — is a SESSION LABEL (`labels.py`), minted
per live item and, on load, ADOPTED from the file's own `id` (`w47` → `W47`). But
the file's `id` is a CANONICAL id that `design_from_scene` **renumbers by geometry
on every save** (`canonical.py`, the dirty-flag/undo/round-trip invariant rests on
it). So a wall you had named `W47` was written out with whatever id its geometry
sorted to — `w12` — and reopened as `W12`. The number drifted across save→open.
A plain refresh/rebuild was already stable (same live objects); only the save/open
boundary moved the numbers.

## 2. WHAT IT DOES

### Labels persist (every labelled kind: W O V R F RF C)

- **A new optional `uid` field** on each item record (`$defs/uid`, v6 schema;
  `design/model.py`) carries the session label. `design_from_scene` writes it
  from the live item's label, and a load ADOPTS it in preference to the `id`
  (`_labels.adopt("W", wd.get("uid") or wd.get("id"))`) — so the number the user
  sees comes back, whatever geometry did to the id.
- **Stored only when the id cannot recover it.** After `canonicalize`,
  `_persist_labels` drops a `uid` whenever it matches the record's canonical id
  (the two spellings of one number, `labels.matches`), and drops a duplicate when
  an earlier record of the same kind already carried it (a scene wall split into
  segments stamps each; only the first keeps it). So an UNEDITED plan's records
  stay bare and **a file still reproduces byte‑for‑byte on open→save**
  (`test_load_path::…_reproduces_it_exactly` holds).
- **The label rides the FILE, not the undo/dirty snapshot.** `design_document()`
  (what is written) carries `uid`; `snapshot()` STRIPS it (`strip_labels`). The
  snapshot defines the dirty flag and undo, and must stay granularity‑invariant —
  one long wall and the same wall held as its split segments must planarise to ONE
  document — which a per‑item label would break. A walk READS the stored label
  (`_uid`), it never MINTS one, so an undisplayed or programmatic scene emits none.

### Find item (Edit ▸ Find item, **Ctrl+F**)

- A non‑modal dialog (`floorplanner/find.py`): a filter box over a list of every
  labelled item. Type a **label** (`W47`, `O3`, `R2`, `V12`, `F4`, `RF1`, `C2`)
  or a **name** — the match list narrows live; picking one **switches to the
  item's floor, selects it and fits the view around it** (reusing
  `MainWindow.zoom_to_spot` and the design `Spot`). Matches on label + name, as he
  chose — not the item type. Corners (not scene items) zoom to their point.

### The shortcut remap (his call)

- Floor **Select → Ctrl+L**, **New floor → Ctrl+Shift+L** (L for LEVEL), which
  freed **Ctrl+F for Find**. The macro token is UNCHANGED: a floor switch still
  records as `^F "name"` (the token names the ACTION, not the key).

## 3. RECEIPTS (instrument `docs/evidence/0316-find-and-labels/render.py`)

The receipt opens `symmetricP1`, gives one wall the label `W777` — a number its
geometric id cannot give back — saves the way the app saves (`design_document`)
and reopens: **the plan still shows `W777`** (the file carried it; the drift is
gone). It then opens the Find dialog, filters to a wall's label, and grabs the
dialog (`find_dialog.png`) and the plan view with that wall selected and zoomed
(`find_zoomed.png`). Find sees 247 labelled items on that plan.

## 4. TESTS

`tests/test_label_persistence.py` (7): a wall/opening/room label survives
save→open when its id differs; a clean canonical plan stores NO labels (byte‑for‑
byte preserved); a label is stored on at most one record; the undo/dirty snapshot
is label‑free. `tests/test_find.py` (4): the target list covers every labelled
kind with unique labels; the filter matches label + name (not the type); a pick
selects the item; Edit ▸ Find opens the dialog. The suite grew 2118 → 2128. Gate:
full, GREEN (2128 collected, 2121 passed OFF and ON, ruff clean).

## 5. NEXT

**His word was "land it and merge"** — this increment lands. Still named, not
ordered: a Find that also matches an opening's size code or a furnishing's kind
(he scoped this to label + name); a Find history / recent list; a right‑click
"Find similar"; a per‑item "copy label". 0248's items 8–9 (porch steps/base; a
porch roof turning a corner) still stand.
