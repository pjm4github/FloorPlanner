# 0322 — ruling: a PLAN for parametric furnishings is on disk for Patrick's review; nothing is built, and building it needs the lane widened

**Reviewer (Cowork), 2026-11-14.** Follows 0321. Patrick asked for a
"parametrized furnishing feature", stairs first, planned before anything is
written.

- **Added, docs only:** `docs/furnishing-spec/STAIRS_FURNISHING_SPECIFICATION.md`
  (his spec, byte-for-byte) and
  `docs/furnishing-spec/PARAMETRIC_FURNISHINGS_PLAN.md` (the plan).
- **No code, asset, schema or test changed.**
- **The plan needs two files outside 0319's lane:** `floorplanner/items.py`
  (`FurnishingItem`, `StairItem`, `make_furnishing` only) and
  `floorplanner/__init__.py` (exports only). **Not in force until Patrick says
  yes** — plan §6 D6. If he does, 0319 §3's rules cover those two files as well.
- **The plan does not touch** `cameras.py`, `roofs.py`, `roofclip.py`,
  `fp3dq.py`, `scene.qml`, `design/bridge.py` or the JSON schema, and in
  `fp3d.py` only the furnishing block.
- **Code:** commit the two docs and this file as doc-only. Nothing else is owed
  until a build phase is reported in a later number.
