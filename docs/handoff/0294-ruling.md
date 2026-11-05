# 0294 — ruling: windows are authored on the DORMER FACE — 0293 §4's window item withdrawn; the plan-view stack; the cut into the climbing wall

**On his word, 2026‑11‑05, twenty minutes after 0293:** *"authoring the
windows should occur on the dormer face. There needs to be a clever way to
show the dormer windows in plan view so that [when] the user has the dormer
on the layer as the roof and there [are] windows below the gable end, both
windows in the stack can be edited in plan view. Propose a solution. We
will also continue to enhance the elevation view in the dormer dialog box
where various window parameters can be modified."* And: `little-dormer-
test.json` is his check-and-test plan (0293 already names it; it is the
fixture for §3 below too).

## 1. WHAT CHANGES IN 0293, AND WHAT STANDS

* **Withdrawn:** 0293 §4's window item (*"a window lives on a wall"*) and
  the `openings`-list gating by `_on_a_wall`. **Replaced:** the dormer's
  `openings` record is THE home of every dormer-face window, whatever
  stands under the face — a generated face, a hand-drawn wall, or a bound
  face wall. The Phase C model stands as built: one record, many views.
* **P4 (bound walls):** the bound FACE wall carries no wall openings — the
  wall dialog refuses one there, naming the dormer; cheek walls are ordinary
  walls. "Create walls" no longer moves anything.
* **P5** is no longer a receipt phase; it has mechanism (§3) and a plan view
  (§2), and it moves BEFORE P4 (§5).
* **Everything else in 0293 stands**, including (c) ONE datum, the host's:
  the dialog's elevation view SHOWS and EDITS a sill in the editing level's
  terms (*"36″ above level L2's floor"*) and writes the host-datum number,
  the conversion printed beside the field. A display conversion is not a
  second record.

## 2. THE PLAN-VIEW STACK — proposed, and ruled unless he objects

**The case.** Modality 2: dormer on the roof's level. The house wall under
the face carries its STOREY window (his `9648`, 36–84″); the dormer face
above carries the GABLE window (his `8048`, 136–184″). One plan line, two
records, two heights — today the wall's window and Phase C's read-only blue
band paint on top of each other.

**The second row.** Each dormer-face window becomes its own hit-testable
item (`DormerWindowItem`, a child of the `RoofItem` the way `RoofGripItem`
is), drawn as a band PARALLEL to the face, offset to the UP-SLOPE side
(into the dormer) by half the wall's thickness plus a fixed screen gutter
(pixels, zoom-invariant, as the grips are), so it never lies on the wall's
own window. Two short ties from the band's ends down to the face line say
*"this face"*. Its mark is CATEGORICAL (WORKING_AGREEMENT, 2026‑08‑12 — a
scalar channel cannot carry identity): a dashed outline with a small gable
glyph (a triangle) at its centre, in the dormer blue; the wall window keeps
its own mark untouched. The stack then reads as two rows — the storey row
on the wall, the dormer row just inside the face — and a glance tells them
apart at any zoom. A face standing on NO wall (set-back) draws the band on
the face line itself, offset 0: same item, no row to clear.

**Editing in plan.** Drag ALONG the face → the anchor offset, snapped on the
grid (`wall_snap_len`, the standing rule), never across. Double-click → the
dormer dialog with THAT window selected in its elevation view — the one
door between plan and elevation, which is where his per-window parameters
grow. Right-click → edit / duplicate / delete; Delete on a selected band
deletes the opening. Width, sill, head and kind are the dialog's only: a
plan-view width drag is refused, since it would be a second scalar control
on a number the elevation view owns. Drawn and hittable only while the
dormer's editing level is active and roofs are editable (`_roof_hittable`);
ghosted with the dormer otherwise. The callout (0279's family) names code,
sill and head in the editing level's terms.

**Refused alternatives, so they are not re-proposed:** both windows on the
face line told apart by colour or weight — same position, scalar channel,
and a hit-test lottery (D11's shape); an elevation inset drawn on the plan —
it moves editing off the plan, which is what the dialog is for; a `dormer`
flag on a wall opening — two homes again.

## 3. 3D — THE CUT INTO THE CLIMBING WALL

**Today**, measured (0293 §1 item 4): the dormer's openings cut only the
GENERATED face; where a house wall stands on the face line the face yields
(`_on_a_wall`) and the wall's own openings are the only voids — `rf4` and
`rf8` have 0 face triangles, which is why a face window never rendered on
his houses (0292 §2).

**RULED:** where a wall stands on the face line and climbs into the dormer,
the dormer's face openings are cut into THAT wall's climbing pieces: the
face spans projected onto the wall's own `u` (ONE projection — the twin of
`RoofItem.dormer_face_window_spans`; share the arithmetic, do not restate
it), their heights absolute (host datum, lifted). **Two things in
`build_model` must change, and the census names every caller first:** a
wall's cut `head` is clamped to `z1 − z0` (the wall's own top), and an
under-sill piece is `to_top=False` — both are wrong for a band ABOVE the
storey top. `_wall_under_roofs` gains a `z_cap`: an under-sill piece in the
climb band climbs to `min(surface, sill)`, the header above the band climbs
to the surface. A band that STRADDLES the wall's `z1` (sill below, head
above) is one void, not two — name that as its own test; it is where the
storey mechanism and the climb meet.

**Receipts, on `little-dormer-test.json`** (`rf2` on L1 hosted on `rf1`;
the L1 wall on its face): add a `3040` to `rf2.openings` through the
dialog → the band is a VOID by the ray test `test_dormer_gable_3d.py`
uses; the triangle delta is non-zero (0292 measured **0** — that zero is the
fail-first precondition, quote it); the wall's own storey window stays a
void (the 0248 invariant). Then on the promoted file (P3; modality 1): the
same cut, now from the L2 wall that P1 lets climb. `dormer-test.json` (no
wall under the face): the generated face still carries the cut,
**byte-identical** to before.

## 4. THE ELEVATION VIEW — named, not ordered

His word: it keeps growing, parameter by parameter. §2's double-click is
its door from the plan. Nothing more is specified here; each parameter is
his to order, and each lands in the record's one home.

## 5. THE ORDER, AMENDED

**P1 → P2 → P3 → P5 → P4.** P5 (§2 + §3) depends on P1 only (the wall on
the face may be hand-drawn; the predicate is `_on_a_wall`), is what he
asked for today, and must not wait behind bound walls. Check session A
(0293 §6 item 3) is unchanged; session B checks P5 then P4: on
`little-dormer-test`, the two rows on the L1 plan, drag the dormer band
along the face, open the dialog from it, both windows in 3D.

**Carried:** 0293's §0 and §6 unchanged.
