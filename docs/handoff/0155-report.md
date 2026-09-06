# 0155 — report: R4a — the roof footprint enters the schema

**Code, 2026‑09‑06, answering [`0154-ruling.md`](0154-ruling.md) (R4 re-planned
into R4a/R4b/R4c), the tranche after R3b ([`0153`](0153-report.md), closed).**

---

## 1. WHAT'S BUILT

**`span_in` is now a real document field, per side.** `design-schema.v5.json`'s
`roof` object gains `span_in: [left, right]` (each side `exclusiveMinimum: 0`)
and widens `overhang_in` to `oneOf` a bare number (the pre-R4a shape) or
`[left, right]` — a document written before this tranche stays valid under
the SAME schema, no version bump, matching the `marker_end` precedent R2b
already set. `eaves_bind: "manual" | "room_top"` (default `"manual"`) gets
its own field too — this tranche only gives it somewhere to round-trip;
the actual `room_top` recomputation is R4b's own dialog toggle, named
explicitly rather than half-built.

**`RoofItem.span_in`/`.overhang_in` are now properties, not plain
attributes**, normalising whatever is assigned: a bare number becomes
`[v, v]` (every existing caller — the ridge-sketch tool's own eaves pick,
every pre-R4a test — still works unchanged), a 2-item sequence is stored
per side as given. This is deliberate, not incidental: a plain attribute
would let a future caller (R4c's own drag grips) overwrite one side with a
scalar and silently erase the other side's asymmetry. `_eave_ends()` reads
each side's own span + overhang independently.

**`design/bridge.py` stops re-deriving a span on every load.** The reader
now checks the document for `span_in` first; when present, it's used
directly (no wall search at all). Only a document with no `span_in` — every
record R1 through R3b ever wrote — falls back to the old behaviour
(`nearest_eaves_wall`, symmetric), and MATERIALISES the result onto the live
`RoofItem` so the next save writes it. `overhang_in` migrates the same way,
a bare number becoming `[v, v]`. The writer (`_roofs_of`) always emits both
as arrays now, plus `eaves_bind` — every live roof, loaded or freshly
sketched, already carries real values, so the writer never needs to know
which case it is.

**`fp3d.py`'s 3D planes read the per-side fields too**, with one subtlety
worth stating plainly: this file's own y-flip (`world = (x, -y, z)`)
REVERSES HANDEDNESS, so its world-space `+normal` side is `span_in`'s index
1 (right in plan-space terms), not index 0. Documented at the exact line it
matters, and pinned by a test built specifically to catch the swap (an
asymmetric span with a ridge oriented so the flip actually matters — an
x-aligned ridge would not expose it).

**Consequence landed as specified, not deferred**: with one `ridge_h_in`/
`eaves_h_in` pair, unequal `span_in` sides now give unequal pitch per slope
(a saltbox) — 0139-ruling.md's v1 symmetric-eaves assumption retires here,
on schedule per 0154's own instruction, in the geometry itself even though
no dialog can SET an asymmetric span yet (that is R4c's own drag grips;
R4a only had to make the math correct once something eventually does).

**`roof_clip_spans` (R3b's own function) updated for per-side math** —
each side of a wall's clip zone now uses its own reach/slope, with an
explicit breakpoint at `perp == 0` where the governing formula switches
sides, plus each side's own `reach`/`perp_thresh` roots, all still exact
interval arithmetic, no sampling.

No `RoofEndOnDialog` feature work (that stays R4b's), but it can no longer
crash: it read `roof.span_in` as a bare float, which would now raise on
the list — reads index 0 (`"left"`) as its one reference until R4b gives
it a real per-side display.

## 2. THE CHECK — GREEN tier, CI

Per [`0154`](0154-ruling.md) §3's own table, R4a's check is CI, not
Patrick's manual review: full suite **1168 passed** (19 new: 3 schema-layer
`Design` round-trip tests, 8 JSON-schema validation tests, 3 bridge-layer
migration/materialisation tests including the receipt below, 3 clip-math
tests for per-side geometry and the property-normalisation seam itself, 2
fp3d tests including the handedness cross-check), 7 deselected (`perf`
lane), 0 failures. `ruff` clean. `python tools/gate.py` (full mode):
**GREEN**.

**The named receipt** — "a re-saved roof renders pixel/number-identical
before vs after" — run against the real `fixtures/roofs-r3-orbit-check.json`
(two pre-R4a roofs, one orthogonal, one at 45°) as the concrete stand-in
for "a re-saved wiscaway roof" (no wiscaway file in the repo actually
carries roofs yet): loaded, walked back out (materialising `span_in`/
`overhang_in`/`eaves_bind`), loaded again into a fresh window, and compared
— ridge endpoints, `span_in`, `overhang_in`, every `_eave_ends()` point,
and `fp3d.build_model`'s own "roofs" mesh vertices and faces, all
number-identical between the two loads.

**A second receipt, sharper than the ruling's own wording asked for**: a
roof's span now survives a reload with NO nearby wall at all (not just
"the same wall is still there to re-derive it from," which was the old
test's own precondition) — proof that persistence, not a lucky re-derivation,
is what carries it across.

## 3. DISPOSITION

**R4a is GREEN tier** — per ROADMAP.md's own row for it, that means run,
gate, PR, merge on green CI, not a direct push: on branch
`roofs-r4a-schema`, PR going up next. No manual check is owed and none
will be waited for — once CI reports green the merge follows under the
standing autonomy policy, same as every other GREEN-tier item. **R4b is
the next available tranche (AMBER)** — the parameters dialog: per-side
overhang, heights/pitch via the End-On machinery, gable↔hip per end, the
`room_top` binding toggle — per [`0154`](0154-ruling.md) §3's order:
R4a → **R4b** → R4c → R5.

**Carried, unchanged:** D83/D84 (held); room-label rounding
([`0131`](0131-ruling.md) §2); delta-snap sites; D61-family; yard items.
