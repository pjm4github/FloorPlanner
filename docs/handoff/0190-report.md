# 0190 — report: R5b dormers — the design read-back ([`0186`](0186-ruling.md) §3), no code

**Code, 2026‑09‑13.** Patrick's second look at the 3D wall clip passed —
*"that fixed it, merge PR #62"* — and PR #62 landed on `main` at
`6812368`, fast-forward, the branch deleted in the merge step. His next
word: *"proceed with the R5b dormer read-back."* This is it: the four
questions [`0186`](0186-ruling.md) §3 asks, each answered as a proposal
against what the tree already has (EXISTS / PARTIAL / ABSENT, per clause),
**with two measurements** — what the current roof machinery does with a
dormer-shaped roof record, and what the R3b wall dash does under one.
**No production code was touched.** RED until he rules; nothing else is
open (the 3D wall clip was the only AMBER tranche, now merged).

---

## 0. THE MEASUREMENT FIRST — a dormer through today's machinery

The ruling's own premise, *"a dormer IS a small roof with two walls and a
face, so the roofs machinery should be reused, not paralleled"*, was
tested before anything was proposed. A host (ridge along x at plan
y=100, eaves 96″ / ridge 150″, span 100″, 12″ overhang) and a dormer-
shaped `roof` record on its south slope — ridge up-slope at x=200 from a
front point at y=190 (host 101.4″ there) to a back point, eaves 116″,
ridge 136″, span 30″ either side (a 60″-wide dormer), both ends gable —
through `compute_roof_clips` and `fp3d.build_model`, unmodified. Closed
form: the dormer ridge meets the host plane at y = 100 + (150 − 136)/0.54
= **125.93**, its eaves meet it at **162.96**.

| the dormer's back ridge end | host region | dormer region | seams | dormer `ext` |
|---|---|---|---|---|
| **short of the meet** (y=140, 7.6″ **in the air** over the host) | 87 027 of 89 600 in² | 2 573 of 3 000 | two valleys from (170, 163) / (230, 163) to (188.6, 140) / (211.4, 140) — they stop at the back gable line | (0, 0) — an **open** gable end, [`0184`](0184-report.md)'s rule |
| **at the meet** (y=125.93) | 86 867 | 2 733 of 3 844 | two valleys from (170, 163) / (230, 163) **to the apex (200, 125.9)** | (0, 916.9) — joined |
| **past the meet** (y=110, under the host) | 86 867 | 2 733 of 4 800 | identical to the row above | (0, 916.9) — joined |

`fp3d` builds every case with no note: the host's planes open exactly
where the dormer's territory is, the dormer's planes are lifted from its
own cells, the front gable triangle stands at y=190. 3–9 ms.

**What this says.** With the back end at or past the meet, **today's rules
produce the correct gable-dormer roof with no special case at all**: the
host's plane opens exactly where the dormer sits (its region loses
precisely the dormer's 2 733 in²), and the dormer's two side planes join
the host along two valleys that meet at the exact ridge/plane
intersection — the ruling's *"the dormer's own planes join by the SAME
envelope rules"* is already true. The one case that differs is a back
end **sketched short**, standing in the air over the host: 0184 ruled
such an end open (correct for a wing's ridge cut short, his own fixture),
and for a dormer that leaves a vertical back gable hanging above the
slope. **The fix belongs to the dormer's own geometry, not to
`roofclip.py`**: a dormer's back end is derived — where its ridge meets
the host plane — and stored (§1). Then no dormer ever presents the open
case, and the clip machinery stays as it is, byte for byte.

**The second measurement — the R3b wall dash under a dormer (host eaves
80″, a 96″ room, the dormer's face on the trace at y=177.1, a wall under
the dormer at y=185 where the host plane is 90.5″):** `roof_clip_spans`
dashes the whole wall, `[(0, 40)]`. It reads each roof independently and
**unions** the spans, so the host's plane clips the wall even though the
dormer above it is 110″+ there. The R5a trace is cut to the host's region
by construction (`_drawn_trace`), so it stops at the dormer's territory;
the wall dash does not know territories. Named in §2 as the one place the
2D side needs a change.

## 1. THE SCHEMA SHAPE — a `roof` record with a `host`, not a new object

**Proposal: a dormer is a `roof` record in the same `roofs` array,
carrying one additive optional field, `host` (the id of the roof it
stands on).** Presence of `host` is what makes it a dormer. Everything
else it needs it already has: `ridge` (front point, back point),
`eaves_h_in` / `ridge_h_in` (the cheek top and the dormer ridge, same
level-base datum), `span_in` (its half-width, per side), `overhang_in`,
`gable` (front: `true` = a gable dormer; `false` = a hip dormer, later),
`marker_end` (the front, index 0 — the End-On marker sits on the face).
Not a child list under the host: a child object would need its own
loader, writer, item class, grips, dialog, clip entry and 3D builder —
the paralleling the ruling forbids — whereas a `roof` with a `host` rides
every one of those as they stand (§0 proved the clip and the 3D planes).

| clause | status | in the tree |
|---|---|---|
| the record type, loader, writer, validator | **EXISTS** | `design/model.py` `Roof`; `planio.py` `_roofs_of` (writes; a document with roofs is version 6); `bridge.py` `apply_design_to_scene` (line 1326); `design-schema.v5.json` `roof` |
| the `host` field | **ABSENT** | one optional `$ref: id` on the schema's `roof`, one `Any` on `Roof`, one line each in loader/writer; [`ROADMAP`](../ROADMAP.md) R‑B: additive optional, **no version bump**. Load validates the reference the way a `level` id is validated: a dangling `host` is reported, the record skipped, never a silent floating roof |
| the back end derived | **ABSENT** | `ridge[1]` is **written** (the document stays self-contained, exactly `eaves_bind: "room_top"`'s discipline for `eaves_h_in`) but **re-derived** by the app whenever the dormer or its host changes: the point on the ridge line where `surface_height(host) == ridge_h_in`, closed form, never on load. A dormer whose ridge never meets the host (ridge above the host's ridge) is refused at the dialog, reported, not clamped |
| the two cheeks and the face | **ABSENT as geometry, derivable from the record** | the cheeks run along the eaves-START lines (`span_in`, not the overhang) from the face back to where the dormer's eaves meet the host plane (`eaves_h_in == surface_height(host)`, closed form); the face stands at `ridge[0]`, `span_in` wide. Thickness: one constant, `INTERIOR_T` (4½″), not a field — nothing in the record it does not already say. **Not `walls` records**: a dormer wall stands on a roof plane, not the level base, and drawing it as a plan wall (thick, grey, welded) would misrepresent it |
| deleting the host | **ABSENT** | proposal: deletes its dormers (`contextMenuEvent` "Delete roof" walks `scene.items()` for roofs whose `host` is this id), undoable as one gesture |

## 2. THE OPENING AND `compute_roof_clips` — no special case; one 2D fix beside it

| clause | status | measured / in the tree |
|---|---|---|
| the parent plane opens where the dormer sits | **EXISTS** | §0: the host's region loses exactly the dormer's territory; valleys are the seams |
| the dormer's planes join by the same envelope rules | **EXISTS** | §0, rows 2–3; `roofclip.py`'s own comment at `clip_pair` already names *"a dormer-like roof poking out of a bigger one"* as the case a roof with no body outside the other keeps where it is higher |
| the sketched-short back end | **handled in §1**, not here | 0184's open-end rule is right and stays; the dormer never presents that case once its back end is derived |
| the 2D wall dash under the dormer | **PARTIAL — the one change** | `roofs.roof_clip_spans` unions per-roof spans; under a dormer the host falsely dashes the wall. Fix: a roof's clip span counts only where the wall point lies in that roof's **territory** (`_clip_region.contains`, exactly what the 3D wall clip already does with `terr_by_level`). This is a correction R4d/R4g already implied for any two overlapping roofs, made necessary by the first roof that sits wholly inside another. `roof_clip_trace` needs nothing: it is cut to the region already |
| the 3D cheeks and face | **ABSENT** | `fp3d._wall_under_roofs` caps a wall's TOP at a roof; a dormer wall needs its BOTTOM lifted onto the host plane and its top capped by the dormer's own plane — the same function with a bottom surface, emitted as `_prism_slab` pieces with a varying bottom ring (its `bottom_z` grows a per-vertex form). The gable triangle above the face is already built by the roof machinery (§0: the front end is an open gable end) |
| a window in the face | **ABSENT, named for later** | an `openings` entry on the dormer record (a face is one wall); not v1 |
| a dormer on the R5a trace: the room below | **EXISTS by construction** | once the wall dash reads territories, a room under a dormer has full height there, and the trace (already region-cut) already shows the host's line stopping at the dormer's valleys |

## 3. THE SKETCH GESTURE — drop on a roof plane at the clip trace

**Proposal, in the ridge tool's own two-stage shape** (`view.py`
`TOOL_ROOF_RIDGE`: stage 1 drag, stage 2 pick, then the End-On dialog):

1. **Press on a roof plane** — inside some roof's visible region, not on
   its ridge/marker/grip (those keep their meaning). The press point
   snaps **onto the host's clip trace** (`roof_clip_trace`'s nearest
   segment, within the wall-snap tolerance) — the face stands on the line
   inside which the room loses full height, the ruling's *"dormer
   placement map"*. Off the trace it snaps to the grid as a ridge does.
2. **Drag along the trace to set the width** — the ridge is perpendicular
   to the eave (along the host's normal, up-slope) **by default**; the drag
   sets `span_in` (half the drag, both sides), landing ON the grid as the
   eave grips do ([`0070`](0070-ruling.md) §3's class). Shift while
   dragging frees the ridge direction (the rare off-square dormer) — the
   tool's own modifier convention, not a new one.
3. **Release → the End-On dialog** (the one dialog, a fourth door) with
   dormer defaults: `eaves_h_in` = the trace's ceiling + 24″, `ridge_h_in`
   = eaves + span × the host's own pitch (the same pitch as the host, the
   common case); the back end derived from the ridge height and shown
   on the drawing; **refused** if the ridge height would top the host's
   ridge. Cancel drops the dormer, as an under-length ridge is dropped.

| clause | status | in the tree |
|---|---|---|
| the two-stage gesture, the sticky tool, the snap-start, the dialog door | **EXISTS** | `view.py` 466–530, 728–745; `mainwindow.finish_roof_ridge`; `RoofEndOnDialog` |
| "press on a roof plane starts a dormer" | **ABSENT** | today a press on a roof body falls through to selection; the tool would need one branch: press inside a roof's region → dormer stage 1 with that roof as `host` |
| snap to the trace | **ABSENT** | `roof_clip_trace` gives the segments; a nearest-point snap is `dist_point_segment` |
| the eaves pick (stage 2) | **not needed for a dormer** | the width comes from the drag, the host from the press — no wall to pick |
| grips on a dormer | **PARTIAL** | the five `RoofGripItem`s exist; for a dormer the **back-end grip is disabled** (derived), the ridge grip slides the dormer along the eave, the eave grips set its width, the front-end grip moves the face up/down the slope |

## 4. THE V1 DORMER — gable; shed and hip named later

**v1 is the gable dormer**: `gable == [true, true]`, front face vertical,
back end derived into the host. **A hip dormer** is `gable[0] == false`
and costs nothing new — the hip machinery is per end already (§0's
machinery handles it; not checked in v1, named). **A shed dormer is a
different shape** — one plane sloping the host's own way at a flatter
pitch, no ridge — and does not fit a `roof` record's two-sided form; it
waits for its own ruling. Eyebrow and wall dormers are not named.

## 5. WHAT THE BUILD WOULD BE, IF RULED AS PROPOSED

One AMBER tranche, one branch, in this order, each step gated: (a) the
`host` field end to end, the derived back end, the cheek/face geometry
on the item (drawn dashed like every roof line, the valleys already
solid) — the plan view; (b) `roof_clip_spans` reads territories — the
wall dash under a dormer, with a fail-first test on §0's second scene;
(c) `fp3d`: cheeks and face as prisms between the host plane and the
dormer's plane; (d) the gesture; (e) a fixture: §0's geometry as
`fixtures/dormer-gable-check.json` unless he drops his own into
`fixtures/incoming/` — his wiscaway loft, the hip-ended roof in his own
R5a picture, is the natural one. His check: sketch a dormer on the loft,
see the room's dashes and trace open under it, and see it in 3D.

## 6. `fixtures/incoming/`, with ages

Unchanged from [`0187`](0187-report.md) §4: the two promoted `w7`
duplicates (2026‑08‑21, 23 days). Exit 2 on his word.

**Carried:** unchanged from [`0189`](0189-report.md) and
[`0186`](0186-ruling.md) §5 — R6 after this, on his fixture and his
display-rule answer.
