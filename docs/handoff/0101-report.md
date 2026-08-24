# 0101 — report: the read-back for `0100-ruling.md` §5 — no code built

**On [`0100-ruling.md`](0100-ruling.md) §5.** Answered in order. Nothing below
is built; `0100` §6 owes the read-back before any code, full stop.

## 1. The `WallItem` ↔ document-id map

**Already half-built, as an out-param.** `bridge._walls_of(..., src=wsrc)`
populates `wsrc: {(v1_docid, v2_docid) sorted: WallItem}` as it emits each
wall record. Zipping that against the returned records
(`doc_id → wsrc[(*sorted((rec["v1"], rec["v2"])),)]`) gives the map directly
— no new machinery, one dict built alongside the existing
`design_from_scene()` call every wall-listing dialog already makes.

**How long it stays valid: exactly as long as the walk that built it, and
no longer.** It is a snapshot, not a view — the next scene edit (add, delete,
split, merge, move) can silently invalidate an entry: the id might now name
a different `WallItem`, or one that is no longer in the scene at all.
Nothing refreshes it automatically.

**What happens when the scene changes under it: the existing guard is
`sip.isdeleted(item)`**, used exactly for this shape at four sites already
(`walls.py`, `rooms.py`) — a stored `WallItem` reference outliving its Qt
C++ object. A row's click handler checks it before `setSelected`/`centerOn`;
a merged-but-not-deleted wall (same object, different shape) is not caught
by this guard and is a real gap, named in §3 below.

## 2. Centre-on-click, or selection alone

**Genuinely his call, not mine — but the evidence leans one way.** No
existing pattern centres the view on a selection anywhere in this app (the
one `centerOn` call is the startup default). Plain `setSelected(True)`
highlights a wall wherever it already is, on-screen or off. **His own
words were "so I can find them"** — the friction in `0098`/`0099` was
specifically a wall he could not locate, not one he could not identify
once looked at. Selection alone does not solve "find" for a wall outside
the current view. **Recommend centring** (`view.centerOn(wall_item)` — the
Qt API takes an item directly); asking rather than assuming.

## 3. Dead-reference behaviour

**Matches the `sip.isdeleted` guard named in §1**, with one gap named, not
closed: a wall that was MERGED (survives as a Qt object, different shape or
absorbed into another) is not "deleted" and the guard will not catch it. A
row whose wall merged away still resolves to a live `WallItem` — possibly
the wrong one, silently. **Two things need deciding, not one**: what a
dead row shows (recommend: the row stays, greyed, with "no longer present"
in place of the click action) and whether a MERGED wall counts as dead too
(recommend: yes — a `doc_id` that no longer round-trips through a fresh
`design_from_scene()` walk should read the same as deleted, since the
symptom to the user is identical: the row's number does not point at
anything real any more).

## 4. Coalesce's preview — this item or its own

**Measured, not assumed:** `coalesce_all_now` (`mainwindow.py:1290`) runs
`normalize_walls(self.scene)` on its **very first line**, unconditionally —
merge and weld both already applied before any text is shown. Only the
room-outline half (`coalesce_outline_corners`) has a dry-run-then-confirm
step today. Giving Coalesce a preview means the WALL half gains the same
shape the outline half already has — a real, separate feature, not a
dialog skin. **Recommend its own item**, matching `0100` §2's own framing
("worth doing, and it is its own item") — flagged for confirmation, not
assumed granted.

## 5. What `Review wall gaps…` does, and the one thing that does not carry over

**Already interactive today**: `near_vertex_gaps(doc)` lists gaps, "Close
selected gap" acts on the current selection, the dialog refreshes after.
Modal (`.exec()`), no click-to-select, no highlight.

**It cannot take the row widget unmodified.** Every other surface names
**walls**; a gap is a pair of **vertices** — `near_vertex_gaps` returns
`(level, (ax,ay), (bx,by), dist)`, no wall id at all, since a vertex can
belong to several walls or none directly at the corner. "The same
treatment" needs its own small design: click a row, highlight/centre on
the **pair of points**, not a single `WallItem` — a variant of the shared
widget, not a literal reuse of it. Named here so it is not discovered
mid-build.

## A confirmation while investigating, not itself an answer to §5

`0099` §3 withdrew the 104/103 discrepancy pending the repo's own copy.
**Checked independently, no app needed:** `fixtures/wiscaway2026-08-08.json`
has 103 walls; `wall_orthogonality()` returns 103 rows; the two off-axis
entries are `w19` (45.0000°) and `w25` (18.4349°) — exact match to `0098`'s
own numbers. The repo's copy has no discrepancy; withdrawal stands, no
further action.

## Tier

**RED throughout** — a read-back, not a build. Waiting on a ruling before
`0100` §1 (the label) or anything after it starts.
