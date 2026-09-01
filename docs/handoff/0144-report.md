# 0144 — report: R2b — the End-On marker, its dialog, the three-way recompute

**Code, 2026‑09‑01, answering [`0139`](0139-ruling.md) §3 (R2b) as sharpened
by [`0140`](0140-ruling.md) (the End-On dialog ruling).**

---

## 1. WHAT'S BUILT

**One marker per roof** (`RoofEndMarkerItem`, `roofs.py`), a Qt CHILD of its
`RoofItem` — created automatically whenever a `RoofItem` is (a fresh sketch
or a loaded document), so it is never something a caller has to remember to
add. **Plain click/drag moves it between the two ridge ends** — release
snaps to whichever end is nearer, never a free position, per
[`0140`](0140-ruling.md) §1's "which end persists in the roof object": a
binary choice, not a coordinate. Works identically on an orthogonal ridge
and a 45° one — the marker only ever compares distances to `p1`/`p2`,
never an axis, so **off-orthogonal ridges are free by construction**, per
[`0140`](0140-ruling.md) §1's own claim, confirmed rather than assumed
(§2 below).

**A real bug caught before it shipped**: the ridge-sketch tool stays the
active tool after a sketch (sticky, like Door/Window), and its press
handler was stealing *every* press unconditionally — so dragging the
marker right after sketching a ridge silently started a SECOND ridge
instead of grabbing the marker. Fixed by checking whether the press lands
on an existing marker or ridge first; if so, the ridge tool steps aside and
lets Qt's normal item dispatch reach the marker. Regression test:
`test_dragging_the_marker_while_the_ridge_tool_is_still_active_works`.

**"One dialog, two doors"** ([`0140`](0140-ruling.md) §1), now three:
right-click the marker; right-click the ridge itself and pick "Roof
heights…"; and the ridge-sketch tool's own initial-heights prompt now
opens the SAME dialog — `RoofEndOnDialog` **replaces**
[`0142`](0142-report.md)'s `RoofHeightsDialog` entirely, exactly as
[`0140`](0140-ruling.md) §1 named it would ("REPLACES 0138 R2's plainer
heights dialog"). `RoofHeightsDialog` is deleted, not deprecated — nothing
else called it.

**The three-way recompute**, RULED verbatim in
[`0139`](0139-ruling.md) §2 and sharpened by Patrick's own worked example in
[`0140`](0140-ruling.md) §2: the two most recently EDITED fields are the
inputs; the third is derived and recomputed live. Implemented as a small
recency list (`RoofEndOnDialog._recent`) — editing a field moves it to the
end; the derived field is always whichever sits at the front. Verified
against his own literal example (`R→H→P→R`) and the End-On marker ruling's
own check text (`R+P→H`, `H→P`) — both pass, see §2. **At first open pitch
is the derived field** (the stored heights are the primaries, per
[`0140`](0140-ruling.md) §2), and it resets fresh every time the dialog
opens — "history" is a per-session UI state, not a document field. The
derived field's row is visibly marked ("— derived").

**The datum, amended** ([`0140`](0140-ruling.md) §3): ridge and eaves
heights are measured from the level's own base (ground), not the wall top;
the wall top now appears only as a dashed reference line on the drawing.
The schema's own `eaves_h_in`/`ridge_h_in` descriptions are corrected to
say so (they previously read "above the level" from R1, before this
amendment existed).

**The end-on drawing** (`_EndOnCanvas`, `dialogs.py`) — the app's first
`paintEvent`-based widget: ground line, a dashed wall-top reference, the
roof's two slopes from ridge apex to each eave point (using `span_in`, the
same live-scene render affordance the eaves pick already computes — no new
geometry field), R/H/P labelled on the drawing itself, redrawn on every
edit.

**Model + schema**: `Roof.marker_end` (0 or 1, index-aligned with `ridge`)
— additive over R1, OPTIONAL with a schema default (1), so every roof
record R1/R2 already wrote (none of them carry it) stays valid without a
migration. `design_from_scene`/`apply_design_to_scene` walk/read it like
every other roof field.

## 2. THE CHECK, RUN HEADLESS

[`0140`](0140-ruling.md) §3's own words: *"drop the marker on the main
ridge and the 45° wing ridge; drag it end to end; set ridge+pitch and
watch eaves derive; set eaves and watch pitch derive."* Driven end to end
via synthesized mouse/dialog events against a two-wall plan (main ridge
orthogonal, wing ridge Shift-held at true 45°, dx=dy=180):

* Both ridges sketched and eaves-picked against real walls — 2 roofs
  committed.
* Marker dragged from its default end to the opposite end on **both** the
  main and the 45° wing ridge — `marker_end` flips 1→0 on each, landing
  exactly on the target coordinate both times.
* On the main ridge: set ridge=150, pitch=30° → **eaves derived to 63.4**
  (`150 − 150·tan(30°)`, span 150 from the eaves pick) — matches
  "watch eaves derive."
* Same roof, a fresh dialog session: set eaves=80 → **pitch derived**
  (ridge stays 150, untouched this session) — matches "watch pitch
  derive," and confirms sessions reset per [`0140`](0140-ruling.md) §2.
* `design_from_scene` afterward: **zero schema errors** on the resulting
  version-6 document with both roofs and their `marker_end` values.

## 3. TESTS AND GATE

`tests/test_roof_end_on.py` (new, 12 tests, `gui`-marked): marker default
position, drag-to-snap on an orthogonal and a 45° ridge, the sticky-tool
regression above, both dialog doors (marker right-click, ridge's own
menu), delete-removes-marker-too, the recency-driven recompute (both his
worked examples, literally), the derived-field label, and that `apply()`
never persists pitch. `tests/test_design_model.py` (+2),
`tests/test_schema.py` (+3), `tests/test_design_bridge.py` (+4) cover
`marker_end`'s round-trip, schema validity/rejection, and the bridge walk
in both directions, including a roof written before R2b (no `marker_end`
key at all) still applying with the schema default.

Full suite: **1093 passed**, 7 deselected (`perf` lane), 0 failures. `ruff`
clean. `python tools/gate.py` (full mode): **GREEN**.

## 4. DISPOSITION

**R2b is AMBER tier** ([`0139`](0139-ruling.md) §3) — built and gated
GREEN, going to its own branch and PR next, and Code stops there: no merge
without Patrick's own check. §2 above answers his named check headless;
the PR is for him to run it by hand — drop the marker on both ridges, drag
it end to end, work through the R+P→H and H→P sequences.

**R3, R4 do not start** until this merges, per [`0139`](0139-ruling.md)
§4's standing order.

**Carried, unchanged:** room-label rounding ([`0131`](0131-ruling.md) §2);
delta-snap sites; D61-family; yard items; ridge/eaves horizontal
repositioning ([`0140`](0140-ruling.md) §4 — "on record as deferred").
