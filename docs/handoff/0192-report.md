# 0192 — report: R5b dormers — built as ruled; AMBER, stopped for his check

**Code, 2026‑09‑13, on [`0191-ruling.md`](0191-ruling.md).** Patrick's word
was *"proceed with ruling 0191"*. The ruling adopted
[`0190`](0190-report.md)'s read-back with one correction (a separate
Dormer tool) and ordered the build in §3's order, one AMBER tranche, gated
once at the end. Branch `roofs-r5b-dormers` off `main` at `0d49c3a`, PR
#63 open, gate GREEN, **stopped for his check** — §3's own sentence:
*sketch a dormer on the loft from the Dormer tool — the trace and the
room's dashes open under it, the valleys draw solid, the back end lands
on the host plane by itself — then the same in 3D: cheeks, face, gable,
nothing poking through.* His wiscaway loft is the check plan if he drops
it in `incoming/`; `fixtures/dormer-gable-check.json` is on the branch
either way. **One correction to 0190 §0, owned in §5 below.**

---

## 1. WHAT'S BUILT — §3's order

**(a) `host`, end to end, and the derived back end.**
`design-schema.v5.json`'s `roof` gains an optional `host` (`$ref id`,
additive, no version bump — a document with roofs is already version 6);
`Roof` in `design/model.py` gains the field; `bridge.py`'s writer sets it
to the id the same walk minted for the host (a second pass, since the
host may sort after the dormer); the loader resolves it **after every
roof exists** and, on a dangling or off-level host, reports the record in
`report["roofs_skipped"]` and removes it — never a silent floating roof;
`canonicalize()` remaps the reference through its roof renumbering (the
one roof field that is a reference, not a literal). On the item,
`RoofItem.host` is the host `RoofItem`; `rebuild()` first derives `p2` —
`roofclip.meet_along`, the point along the ridge from the face where the
host's surface rises to `ridge_h_in` (bracketed in half-inch steps, then
bisection to 1e-9; None when the host is already above the face or never
reaches the height) — and a host's own `rebuild()` re-derives every
dormer standing on it. The back end is written (§0 of 0190's `eaves_bind`
discipline) and re-derived on any edit, never on load.

**Cheeks and face, in plan.** `RoofItem.cheek_lines()`: the face across
the front at the eaves-start width and each cheek along its eaves-start
line from the face back to where the dormer's eaves meet the host plane
(`meet_along` at `eaves_h_in`). Drawn dashed with the other plan lines,
cut to the region while clipped, and in the hit shape.

**Grips and deletion.** A selected dormer shows no grip at its derived end;
the other four keep their meaning. "Delete roof" on a host removes its
dormers with it (`remove_with_dormers`) — one gesture. **Roof deletion
has no undo today, and did not before R5b**; the ruling's "undoable" is
therefore not met by this tranche and is named, not hidden.

**(b) The territory fix.** `roof_clip_spans` now passes each roof's spans
through `_within_territory`: the region's own exact segment clip
(Cyrus–Beck per cell) cuts the wall's span to the part inside that roof's
drawn territory, read back to inches along the wall. A roof with no
partner has no region and is unchanged byte for byte (asserted against
`test_roof_clip.py`'s own numbers).

**(c) 3D cheeks and face.** `fp3d._dormer_walls`: three prisms standing
on the host — the face just behind the front plane at the eaves-start
width, each cheek along its eaves-start line back to the meet — bottom
ring on the host's surface (sunk `DORMER_WALL_CLEAR_IN` = ½″ into its
slab), top at the dormer's eaves less ½″, every wall set ½″ in from its
line, thickness the interior wall's; `_standing_prism` is the builder
(per-vertex bottom, flat top). The gable triangle above the face is the
roof machinery's own (an open gable end, as 0190 §0 measured). The roof
meshes are unchanged by the `host` field (array-equal).

**(d) The Dormer tool** — as corrected in §2 of the ruling: `Roof ▸
Sketch dormer [M]`, its own toolbar button (`assets/icons/dormer.svg`,
from `_gen_assets.py`, regenerated), `TOOL_ROOF_DORMER`, macro letter
`M` in both maps and the `roofdormer` name. Press on a roof plane: the
roof whose drawn territory holds the point is the host (`host_roof_at`;
a dormer cannot host, v1); the press snaps onto the host's clip trace
within the tool tolerance (`snap_to_trace`), **and along the trace onto
the 6″ grid** (the same "on the grid, never by it" rule every roof drag
uses); the ridge runs up-slope by default (`upslope_direction`; a press
on the ridge line itself is refused with a status line). Drag along the
trace sets the width, both sides equal about the face, on the grid;
Shift frees the direction (perpendicular to the drag, still up-slope).
Release: no drag → "too narrow", dropped; else the End-On dialog as its
fourth door (`finish_roof_dormer`), seeded with `dormer_defaults` — eaves
= the governing ceiling at the face (R3b's rule) + 24″, ridge = eaves +
span × the host's own pitch. The dialog in dormer mode disables the
room-top binding and the derived end's gable/hip combo, shows the derived
meet distance live, and **refuses** a ridge the host never meets — the
note says why, `accept()` stays open, `apply()` returns False and the
tool drops the dormer. Esc during the drag discards it; hiding roofs
reverts the tool, as the ridge tool does.

**(e) The fixture.** `fixtures/dormer-gable-check.json`: 0190 §0's
geometry written by the app's own writer (a detected, wall-bound 96″
loft, the host, the dormer with its `host`), schema and invariants PASS,
load-bearing through `test_the_promoted_fixture_loads_with_its_dormer`;
its README row names it.

## 2. THE CHECK — receipts

Three new files, **28 tests**: `tests/test_roof_dormer.py` (17,
`walls`) — `meet_along` at the closed form and its two refusals; the back
end derived from a short sketch, and re-derived on a host edit and a
dormer edit; **0190 §0's table asserted as written** (host region 86 867
in², dormer 2 733, the seam vertices (170, 162.963), (200, 125.926),
(230, 162.963), the back end joined, no warning), and the same through
`RoofGeom` records; cheeks from the face to the eaves meet, drawn dashed;
no grip at the derived end; host deletion takes the dormer; **the
territory fix, fail-first** (the host-only control dashes the wall end to
end; with the dormer over it, nothing; a wall straddling the dormer's
edge dashes only outside it) and a lone roof byte-identical; `host`
through the document, canonical renumbering and back with the derived
end written; a dangling host reported and skipped; the fixture loads; the
tool helpers (territory read, dormers not hosts, defaults from the trace
ceiling and host pitch, up-slope both sides and none on the ridge, the
trace snap within tolerance and not beyond). `tests/test_roof_dormer_tool.py`
(8, `gui`) — the gesture through the view: a press 3″ off the trace lands
on it and on the grid, a 36″ drag gives 18″ each side, defaults and the
derived back end; a press off every roof makes nothing; a click without
a drag is dropped; Esc mid-drag discards; a cancelled dialog drops it;
Shift's free direction; the dialog's refusal end to end; the menu item
and both macro maps; hiding roofs reverts the tool. `tests/test_viewer_dormer.py`
(3, `viewer`, Qt-free) — three standing prisms with every bottom vertex on
the host surface less the sink, the cheeks reaching the eaves meet, all
inset inside the dormer's lines; the roof meshes array-equal with and
without `host`; a missing host noted, no walls built.

Full suite **1336 passed**, 7 deselected (`perf` lane), `ruff` clean,
gate GREEN — the branch's own run. The gallery regenerated for the new
toolbar button.

## 3. NAMED LIMITS

* **A dormer cannot host a dormer** (v1; `host_roof_at` skips dormers).
* **A hip dormer** is `gable[0] == false` and unchecked, as ruled.
* **Roof deletion is not undoable** (pre-existing); deleting a host takes
  its dormers in one gesture, but the gesture cannot be undone.
* **The cheek top is flat at the eaves height** (less ½″); the dormer's
  own plane rises inward over it, so the cheek's inner edge sits a little
  under the slab. Invisible; named.
* **`meet_along` brackets in half-inch steps** before bisecting; a
  piecewise-affine surface cannot re-cross inside a step, so the answer
  is exact to 1e-9, but the bracket is the one sampled step in the roof
  code — stated so no one takes "exact" to mean "closed-form".

## 4. `fixtures/incoming/`, with ages

Unchanged on the branch: the two promoted `w7` duplicates (2026‑08‑21).
[`0191`](0191-ruling.md) §4 rules exit 2 unless he says keep — **deleted
on `main` in the commit that lands this report**, both files, their cover
being `fixtures/w7offgrid.fpm` / `fixtures/w7offsetFloorplan.json`
(byte-identical, 0187 §4).

## 5. A CORRECTION TO 0190 §0, OWNED

0190's second measurement said the R3b wall dash *"dashes the whole wall
under the dormer"*. **The wall in that scene was not under the dormer.**
Its dormer stood on the trace with its ridge running up-slope, so its
footprint lay above the trace (y ≤ 177), and the wall at y = 185 sat
between the face and the eave — ground the host rightly dashes. Found
while writing the fail-first test: the "fix" changed nothing on that
scene. The territory fix is still real and still ruled correctly — a
dormer whose face is placed **beyond** the trace (the 0190 §0 table's own
first scene, face at y = 190) does put a wall under a dormer over a host
plane below the ceiling, and there the old union dashed it and the fix
does not — the test uses that scene. The consequence for the check: with
a dormer sketched **on** the trace, as the tool does by default, the
room's dashes under it were already clear; his check will see the trace
stop at the dormer's valleys and no dash under it either way.

## 6. WHAT HAPPENS NEXT

His check. On his word PR #63 merges, branch deleted in the merge
step. Then R6 multifloor — waiting on his fixture and his one-line
display answer ([`0186`](0186-ruling.md) §4).

**Carried:** unchanged from [`0191`](0191-ruling.md).
