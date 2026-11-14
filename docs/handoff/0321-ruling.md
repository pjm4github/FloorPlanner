# 0321 — ruling: the furnishings exception is CONFIRMED by Patrick, the step-1 read is done, and 0319's file list is corrected in two places

**Reviewer (Cowork), 2026-11-14.** Follows 0319. 0320 is left free for Code's
dormer report, as 0319 said. Nothing but this file and 0319 has been written.

## 1. THE EXCEPTION — HIS WORDS

Patrick, 2026-11-14: *"yes make an exception for furnishings modifications and
enhancements. You can edit them in place."* And on the AMBER check being his
look at the 3D view: *"Correct."* So 0319 §4 is now in force, on its stated
terms: in-place edits through the device shell, no git from this session, Code
commits by path on its own branch, AMBER, his 3D look is the merge condition.

## 2. WHAT THE READ FOUND (measured through `build_model`, one kind at a time)

One authoring source, three generated files, three readers:

- **Authored** in `_gen_assets.py`: `FURNISHINGS` (id, name, category, w, d, SVG
  body), `SOLIDS` (height, elevation, form, material, optional region material),
  `MATERIALS`, and `GROUPS` (inside `main()`). `main()` refuses to write if a
  furnishing has no `SOLIDS` row, or the reverse, or a material is undefined.
- **Generated** into `assets/furnishings/`: one SVG per kind (viewBox in
  inches), `manifest.json`, `materials.json`, `groups.json`.
- **Stored in a plan** as `{id, level, kind, room, pos, rotation}` only — no
  size, no shape. Everything else is looked up by `kind`.
- **Read** by the palette and the 2D item (`catalog.py`, SVG at true scale), by
  the camera elevation (a to-scale box from w/h/elevation), and by the 3D
  viewer (`fp3d.py`, as JSON, no `floorplanner` import).

**How the 96 kinds actually build in 3D today:**

| built as | kinds | what it is |
|---|---:|---|
| plain box | 56 | 12 triangles, one material |
| slab | 11 | a top on four corner legs |
| extruded plan symbol (prism) | 28 | seat 6, bed 4, vehicle 10, enclosure 4, vessel 3, basin 1 |
| column | 1 | the post |

The 3D shape of every non-box item is its PLAN SYMBOL extruded, using the
`data-h` height the generator writes on each filled region. Three limits follow
and they are where realism is lost: (a) every part is a vertical extrusion — no
taper, no rounding, no overhang, no open space under a seat or bed; (b) one
colour per material, merged across the whole model, so a wood cabinet has no
door, top or toe-kick distinct from its carcass; (c) `suv`, `car` and
`lawnmower` come out at 12 triangles — a prism in name, a block in fact.
All kitchen and bath casework, every appliance, the toilet, the stairs and the
fireplace are plain boxes.

## 3. CORRECTIONS TO 0319 §2

- **Add `tests/test_viewer_model.py:75`** — it pins `len(manifest) == 96`. Any
  new furnishing changes that number on purpose; it also pins named kinds in
  `prism_kinds` / `box_fallback_kinds`, which a new solid generator will move.
- **Add `floorplanner/catalog.py` `_CASEWORK_PREFIX` / `_CASEWORK_EXACT`** —
  cabinetry is recognised by id prefix, so a new cabinet kind must be named to
  match or be added there, or the camera's cabinetry toggle misfiles it.
- Not in the lane, noted for Code: `docs/progress/furnishings.md` (append-only,
  Code's), the gallery (`docs/make_gallery.py`) after the palette changes, and
  the generated `assets/furnishings/README.md`, whose form list omits `vessel`
  and `column` and still says 95 entries — a generator text fix, to ride along
  with the first lane change.

## 4. A LIMIT ON THIS SESSION'S OWN CHECKING — STATED, NOT HIDDEN

The device shell has Python 3.10 with numpy and matplotlib, and **no PyQt6, no
pytest, no ruff**. So this session can run the generator and `build_model` and
measure meshes, and cannot run the gate, the Qt tests or the real 3D view.
**Every lane change therefore reaches Code un-gated.** Code runs the full gate
before committing; a red gate comes back as a report, not a fix-up in place.

## 5. OWED

- **Code:** commit 0319 and 0321 as doc-only; honour 0319 §3 (commit by path,
  look before any checkout/stash/reset).
- **Reviewer:** nothing edited until Patrick names the first goals. Each batch
  gets one numbered file listing the kinds touched, the files changed, and the
  measurements, for Code to gate and commit.
