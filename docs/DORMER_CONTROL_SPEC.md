# Dormer control specification & gap assessment

Status: **draft for review** (2026-11-18). Captures Patrick's requirements for
the dormer control knobs, maps them onto what is built today, and lists the
gaps. Supersedes the control *model* in the older `DORMER_CONROLS.md` where the
two diverge (the anchor's role and the face-type taxonomy are new here).

Scene units are inches. "Up / down / left / right" are the **plan (screen)**
view. The dormer is a furnishing: it owns no wall; the walls under it are the
user's. All geometry is the one calculator, `dormer_geometry.py`.

---

## 1. Requirements (Patrick, 2026-11-18)

### R1 — The anchor (A, round apex knob) sits ON the host roof
- **R1a** The anchor is placed on the host roof; the user drags it with the
  mouse to anywhere there is host roof under it. It must **always be on the
  roof and can never sit above it**. It travels from the **eave of the host
  roof up to the host ridge**.
- **R1b** The **furnishing's position IS the anchor** (today it is the face —
  see §2). The **blue control circle** spins the furnishing **around the
  anchor** — so move (drag the anchor) and rotate (blue circle) are visually
  distinct.
- **R1c** The anchor can **never go higher than the host roof's ridge**
  (it is a drag limit, not only an after-the-fact error).
- **R1d** If the dormer **spans the host ridge**, it is an **error** (draws
  red, dialog refuses OK). *Already working.*

### R2 — Orange knob (F): the face eave extent
- **R2a** The orange knob sets the **extent of the eave on the face** of the
  dormer. It can move all the way from the **face (purple knob)** out to
  **beyond the edge of the host roof**.

### R3 — Purple knob (D): the dormer face, and the face TYPE
- **R3a** Once the orange knob is set, the purple knob (the dormer **face**)
  can move all the way **from the anchor (A) to the orange knob (F)**.
- **R3b** If the purple face extends **beyond the edge of the host roof**, the
  dormer is a **cantilevered (hanging) dormer**.
- **R3c** If the purple face sits **on the exterior wall below** the floor the
  dormer sits on, it is a **wall dormer**.
- **R3d** If there is a **small strip of host roof** under the face, between
  the wall below and the dormer, it is a **setback dormer**.
- **R3e** These face types get a **selector in the dialog box**.

### R4 — Green knobs (E): the dormer eaves
- The left and right green knobs set the **left and right eaves** (overhangs)
  of the dormer.

### R5 — Yellow knobs (C): the dormer walls
- The yellow knobs set the **walls that drop from the dormer roof down to the
  attic floor** the dormer sits on (the left/right side walls).

### R6 — Blue control: spin around the anchor
- The **blue control circle** rotates the furnishing around the anchor (R1b).
  (This re-colours / replaces today's white rotate handle; the old blue *span*
  squares must move to another colour — see §3.)

### R2/R3 timing — probe below only when it matters (2026-11-18)
- The plan view stays cheap and **does not care what the purple knob is doing**
  until it is time to differentiate the dormer **type**.
- The dormer **reaches down to the host roof and examines what is below it** —
  the host roof's **eave edge**, and whether there are **walls under the face**
  — only when the **dialog is opened** and when the **3D is rendered**.
- The **orange** knob sets the **eave of the face**; the **purple** knob sets
  the **face location (the setback)**. When a **wall is drawn on the setback
  (purple) line, that wall becomes the face**; on dialog open, if a wall exists
  on the purple line it is taken as the face.

### Dormer variations (for R3e) — Patrick, 2026-11-18
Four named types. A **plain wall dormer requires a wall below**; a dormer with
**no underlying wall can never be a plain wall dormer**.

| Type | Condition |
| --- | --- |
| **Plain wall** | a wall below is aligned with the face and **no roof shows in front** — the face just rises from the floor beneath (Image #19) |
| **Setback** | the face is aligned with the wall below, but **a small strip of host roof shows in front** of the dormer |
| **Cantilever** | the **orange and purple knobs sit out past the host eave** — the face overhangs the roof edge (Image #20) |
| **Balcony** | the dormer **sits back from the floor beneath and the roof in front is cut away** to make a balcony outside the dormer |

### Facing (R1b / rotation)
Rotation is **free spin**, but the dormer **turns red (error)** when it is
**not facing straight downhill**. "Downhill" is the **fall line** of the host
roof (its slope orientation) under the anchor.

---

## 2. What is built today

Knobs (`items.py` `DormerGripItem`, placed by `DormerItem._grip_local`), and
the state key each drives (`dormer_geometry.STATE_DEFAULTS`):

| Knob | Colour | State key | Today's behaviour |
| --- | --- | --- | --- |
| A `apex` | white | `depth_in` | at `(0, depth)`; **drag sets `depth_in`, which is used ONLY off a roof** — on a host, depth is computed, so the drag is inert; double-click opens the dialog |
| B `span_l/r` | blue | `span_left/right_in` | half-width, ridge to the eave line |
| C `guide_l/r` | yellow | `guide_left/right_in` | side **guide** line only (draws no wall); 0 = on the eave line |
| D `guide_face` | purple | `guide_face_in` | face **guide** set-back from the face; range `[0, depth]` |
| E `eave_l/r` | green | `eave_overhang_left/right_in` | eave overhang past the wall |
| F `face` | orange | `face_overhang_in` | the rake/eave past the face |

Anchoring: the furnishing's **`pos` is the face end of the ridge** — i.e. the
**face is the fixed anchor today**, and the ridge runs *from* it into the host.
The host is found by height each rebuild (`_host_plane`), never stored.

Ridge / eaves / pitch are a **3-way coupling** (`dormers.normalize`): the ridge
is the anchor value, and the last-edited of eaves/pitch is pinned while the
other floats. `ridge_h_in` is a dialog field.

Unbuildable rules (`dormer_geometry.unbuildable`): gable over the host ridge →
`OVER_RIDGE`; host not rising → `FACES_UPHILL`; shed not shallower than host →
`TOO_STEEP`. These already draw red and block OK (satisfies **R1d**).

Dialog (`dormers.specs`): Form, Symmetric, half-widths, ridge height, eaves
height, pitch, eave overhangs, face overhang, side guides, face-guide set-back,
length-off-a-roof. **No face-type selector.**

---

## 3. Gap assessment

| Req | State | Gap |
| --- | --- | --- |
| **R1a** anchor placeable anywhere on host roof | **Missing** | the apex drag sets `depth_in`, inert on a host. There is no control that slides the ridge/anchor along the host surface. The *concept* of the fixed anchor is also inverted: today **pos = face**, not the ridge-on-roof. |
| **R1b** dragging anchor up-roof raises the ridge | **Missing (shed-partial)** | a shed's back-ridge height already rises with depth (`shed_back`), but nothing lets the user *drag* it; a gable ridge is level and derived from eaves+span·pitch, so "up the roof" needs a defined meaning for a gable. |
| **R1c** anchor ≤ host ridge | **Partial** | enforced as an *error after the fact* (`OVER_RIDGE`/over-ridge), not as a *drag limit* on the anchor. |
| **R1d** span-the-ridge = error | **Done** | `unbuildable` + red draw + dialog refusal. |
| **R2a** orange from face out past host-roof edge | **Partial** | `face_overhang_in` drags freely and is dialog-capped at 60"; there is **no awareness of the host roof's eave edge** as the reference it should be able to pass. |
| **R3a** purple travels anchor→orange | **Different** | purple (`guide_face`) travels `[0, depth]` = face→back-ridge. Patrick's range is **orange(front)→anchor(back)**, and the purple **is the face**, not a set-back guide of a fixed face. |
| **R3b–d** cantilever / wall / setback detection | **Missing** | no notion of the host roof **eave edge** or the **exterior wall below / floor below**, so none of the three face conditions can be detected. |
| **R3e** face-type selector in dialog | **Missing** | dialog has no face-type field; and the type is meant to be *derived* from geometry (see note). |
| **R4** green = dormer eaves | **Done** | `eave_overhang_left/right_in`. |
| **R5** yellow = walls to attic floor | **Partial / semantic** | yellow is a **guide that draws no wall**; Patrick frames it as the actual side walls dropping to the floor. Needs a decision: keep guide-only, or make it drive real walls. |
| **R6** blue = ? | **Needs confirmation** | built as half-width/span. |

### Cross-cutting gaps
1. **No host-roof *edge / extent* model.** R2a, R3b and R3d all need the host
   roof's **eave edge** (and R3c/R3d need the **exterior wall + floor below**).
   Today the item samples only the host height + slope under the face
   (`_host_plane`); it has no outline of where the host roof *ends*.
2. **Anchor inversion.** Moving the fixed anchor from the **face** to the
   **ridge-on-roof** touches the local frame (`pos = face end of ridge`),
   `to_plan`/`to_local`, every knob position, and the schema. This is the
   largest structural change and deserves its own decision before coding.
3. **Derived vs. selected face type.** R3b–d describe the type as a
   *consequence* of where the purple sits; R3e asks for a *selector*. Likely
   the selector picks the **intent** and the geometry snaps the face to satisfy
   it (and warns when the host/wall below can't support that intent).

---

## 4. Decisions (2026-11-18)
- **Anchor = position.** The furnishing's `pos` becomes the **anchor** (the
  apex-on-roof), not the face. Drag = move along the roof; **blue circle** =
  rotate around it.
- **Two probes, two timings.** The **host roof's own extent** (eave edge,
  ridge) is read **live** in the plan view — it is what limits the anchor drag
  (R1a/c) and it is cheap (we already read host height/slope/ridge). The
  **walls below the face** are probed only on **dialog open / 3D render** and
  decide the **face type** (R3). The plan view does not probe walls-below.
- **Face identity.** A **wall drawn on the purple (setback) line is the face**;
  absent a wall there, the purple is the setback guide and the orange sets the
  eave.
- **Face type** = part geometry, part intent, four types (plain wall / setback
  / cantilever / balcony). **Cantilever** is geometric (orange+purple past the
  host eave). **Plain wall** needs a wall below aligned with the face and no
  roof in front; **setback** is the same alignment with a roof strip in front;
  **balcony** is set back with the front roof cut away. With **no wall below**,
  plain wall is unavailable.
- **Facing.** Free spin, but **red/error when not straight downhill** (the host
  roof's fall line).
- **Colours.** Blue **circle** = rotate around the anchor. The **span (B) knobs
  become green** (note: eave knobs E are green today — see §6(4)).

## 5. Plan (draft — not yet started)

Ordered so each step is independently gate-able and visible.

- **P1 — Host-roof extent, live.** Give the item the host roof's **eave edge
  and ridge** under the dormer (reuse `roofs.py` / `roofclip`). Pure geometry +
  a finding; enables the anchor limits and "beyond the host edge". No visual
  change yet.
- **P2 — Anchor becomes the position + the blue rotate circle (R1a–c, R1b,
  R6).** Flip the local frame so `pos` = the anchor; dragging the anchor moves
  the dormer along the roof, limited **eave→ridge**; the blue circle rotates
  around it; **not-straight-downhill draws red** (new finding). Includes a
  **migration** for saved dormers (old pos=face → new pos=anchor) and
  re-colouring the span knobs **green**. The largest structural step.
- **P3 — Face travel (R2a, R3a).** Orange reaches from the face out **past the
  host eave**; purple (the face/setback) travels **anchor→orange**.
- **P4 — Probe below + the four types (R2/R3b–e).** On dialog open / 3D, read
  the host eave + walls below; adopt a wall on the purple line as the face;
  derive **cantilever** (past the eave); enable **plain wall / setback /
  balcony** per the wall-below + roof-in-front rules; dialog **selector**;
  warn when a chosen type is unsupported.
- **P5 — Walls & cleanup (R5).** *Done (2026-11-19).* Yellow (C) stays a
  **guide only** (Patrick: "keep them as guides") — it draws no wall; the knob
  tooltip and `_grip_local` already say so, so no knob change was needed. Added
  a **prominent warning** (`dormer.nothing_below`, WARNING) when neither a room
  nor an exterior wall is defined on the floor below a non-cantilever dormer —
  the storey under its face is then undefined and the 3D builder cannot read the
  face type. Backed by a new `_room_below` probe (dialog/3D-time, like
  `_wall_below`). The dormer↔below *reference* Patrick asked for is designed in
  §7 (a phase-3 proposal, not yet built).

Phase 3 (the 3D builder) stays deferred per the standing ruling.

---

## 6. Resolved (2026-11-18)
1. **Gable "up the roof"** — confirmed: dragging the anchor moves where the
   **level** gable ridge dies into the host; its depth/height follow the host
   surface.
2. **Rotation** — **free spin**, but **red/error when not straight downhill**
   (the host roof's fall line). New finding in P2.
3. **Four types** — plain wall / setback / cantilever / balcony (see §1). Plain
   wall needs a wall below + no roof in front; setback = aligned + roof strip in
   front; cantilever = orange+purple past the host eave; **balcony** = set back
   with the front roof cut away for a terrace (Image #21). No wall below ⇒ never
   plain wall.
4. **Colours** — blue **circle** = rotate around the anchor; span (B) knobs
   → **green**. *One niggle:* the eave knobs (E) are green already, so B and E
   would share a colour — fine if you want them grouped, else E takes a new
   shade. (Non-blocking; default to shared green unless you say otherwise.)

## 6b. Resolved (2026-11-19)
5. **Yellow (C) = guide only.** The side knobs stay guide lines; they draw no
   wall. A dormer owns no walls of its own — the house walls under it climb into
   it in 3D (see §7). So the yellow knobs mark *where a side wall would stand*,
   for the user's eye and for the face/side-wall gather, and nothing more.
6. **Prominent "nothing below" warning.** When a non-cantilever dormer has no
   room and no exterior wall defined on the floor below, the dialog raises a
   WARNING (orange headline, needs the acknowledge box). See §7 for why the
   builder needs the storey below, and the reference that will carry it.

---

## 7. The dormer ↔ house reference, the schema, and the 3D build (proposal)

Status: **proposal (2026-11-19)** for the phase-3 3D work. Patrick's ask: *"some
kind of reference in the dormer so that when the 3D is being built — if the tool
is building from walls and levels it finds the dormer, and when it is building
from roofs and dormers it finds the walls and levels."* Below is the data
relationship, the schema options with a recommendation, how the current 3D
pipeline actually works, and an incremental build plan.

### 7.1 What already exists — the *up/across* reference
The dormer→host-roof link is **already built and already a stored reference**,
and it is the template for everything here:

- In the editor, `DormerItem.host` is a live pointer to the host `RoofItem`,
  resolved by geometry each rebuild (`roofs.host_roof_at`, which also looks one
  level **down** for a dormer whose gable pops up a storey).
- At save (`design/bridge.py` `_roofs_of` + the cross-level resolve pass), the
  dormer is written into `doc["roofs"]` **as a roof record** carrying
  `host = <host roof id>` (a second pass fixes up a host that sorts after it, or
  stands on another floor).
- At load (`_build_roofs`), `host` is re-resolved to a live roof and
  **validated** (`host.floor in (item.floor, one-floor-below)`); a dangling host
  is dropped with a report line, never a crash.
- In the viewer (`viewer/fp3d.py` `build_model`), `dormer_ids` and
  `host_of = {rid: rf["host"]}` drive the whole dormer-vs-host clip: the dormer
  lifts to its **host's** level base, cuts the host roof within its footprint,
  and projects cheeks/face up from the host surface (`_dormer_cheeks`,
  `_dormer_face`).

So "building from roofs and dormers, find the host" is **done**. What Patrick is
asking to add is the *downward* half: find the **storey, room and walls below**
the face — and the inverse, let a wall/room find the dormer above it.

### 7.2 The relationship (three edges)
```
            (exists: roof record `host` id)
   DORMER  ───────────────────────────────▶  HOST ROOF
     │  ▲
     │  │  (new: the storey the face lands on)
     ▼  │
   LEVEL BELOW  ──▶  ROOM BELOW  ──▶  EXTERIOR WALLS on the face line
```
- **Dormer → host roof** — across/one-down; **stored id**, built (§7.1).
- **Dormer → level/room/walls below** — the storey under the face; today
  **probed live** at dialog/3D time (`items.py` `_wall_below`, and the new
  `_room_below`). *Not yet persisted.*
- **Inverse: wall/room/level → dormers over it** — needed so a bottom-up pass
  ("build from walls and levels") can find the dormer that cuts a balcony into
  the roof in front of a wall, or opens a gable above it. Today this is the
  **geometric footprint test** the builder already runs; no stored back-pointer.

### 7.3 Two ways to carry the reference
**Option A — stored foreign keys in the dormer record.** Add
`below = {"level": <id>, "room": <id>, "walls": [<id>, …]}` to the dormer's roof
record, minted at save like `host`.
- *Pro:* O(1) both directions; explicit; survives to the raw JSON a standalone
  `fp3d` reads.
- *Con:* **referential integrity.** A dormer, its host, the room below and those
  walls all move, split, merge and delete **independently**. Every edit to the
  storey below would have to re-mint the dormer's `below` list or it goes stale;
  a deleted wall leaves a dangling id. The walls under a face also change with
  the *anchor drag* (move the dormer along the roof and a different part of the
  house is beneath it) — so the keys would need re-resolving on almost every
  interaction, which is exactly the work a stored key is supposed to save.

**Option B — derived at build, into a link table (recommended).** Keep the
document a flat list of independent items; at build time run **one association
pass** that resolves every dormer's host (as now) *and* its below-storey, and
hand the rest of `build_model` a small `DormerLink` structure keyed by dormer
id. This matches how the renderer already works and preserves its load-bearing
invariant: *"a wall on any floor climbs into the dormer by absolute height …
which floor it is drawn on must not change the 3D"* (`fp3d` P1/P3). The
association is spatial (anchor/face point-in-footprint, face line vs. the walls
of the level whose base is directly below the host), computed once, never
persisted, never stale.
- *Pro:* no integrity burden, no migration, no new schema field to keep fresh;
  the standalone viewer already has every item it needs in the JSON.
- *Con:* recomputed each build (cheap — it is a handful of point-in-polygon and
  segment projections per dormer, the same class of work the clip already does).

**What *is* worth storing is the user's *intent*, not the geometry.** The
`face_mode` enum (auto / plain_wall / setback / balcony), added in P4b, is
already persisted and is the one thing the builder cannot re-derive — it is a
choice. Recommendation: **Option B for the geometric links; keep `face_mode` as
the only stored dormer→house datum**, plus the existing `host` id.

### 7.4 How the 3D build would use it (per face type)
`build_model` composes **one roofscape**: all roofs+dormers clip together in
absolute height, then each level's walls are capped/climbed against the roofs
over them, then ceilings, then furnishings. The below-link plugs in at two
seams:

- **Bottom-up (walls & levels → dormer).** The wall-capping pass
  (`_wall_under_roofs` / `dormer_over`) already lets a wall **climb into** the
  dormer over it instead of stopping at the host. With the link it also learns
  *which* wall is the **face** (the one on the face line, one storey down),
  so a **plain-wall** dormer's face is that wall continued straight up, and a
  **setback** leaves the host strip in front intact.
- **Top-down (roofs & dormers → walls/levels).** `_dormer_face` already cuts the
  host and raises the face; the link tells it the storey below so it can:
  - **plain wall** — face flush over the wall below, no host strip in front;
  - **setback** — face set back, host strip in front kept (default today);
  - **cantilever** — face past the host eave, nothing below (the one case the
    §6b warning is silent for);
  - **balcony** — face set back **and the host roof in front cut away** down to
    the floor of the storey below, with that floor becoming the terrace deck.
    This is the one type that needs the level-below *elevation* (where to put
    the deck) and the room-below *outline* (how far the terrace runs) — exactly
    the `_room_below`/`_floor_below` data the probe already gathers.

### 7.5 Referential integrity & the standalone viewer
`fp3d.py` is deliberately Qt-free and reads the saved JSON directly, so whatever
the editor resolves live must also be recoverable from the document alone. Under
Option B the viewer re-runs the same association pass on the flat item lists it
already loads — no editor state required. The only durable fields are `host`
(exists) and `face_mode` (exists); nothing new must be kept in sync.

### 7.6 Proposed phase-3 increments
1. **Link pass.** Factor the host resolve + a new below resolve (level/room/face
   walls) into one `dormer_links(doc)` helper in `fp3d`, returning
   `{dormer_id: DormerLink}`; feed it where `host_of`/`dormer_ids` are built.
   Pure data; no visible change. Mirror it in the editor so the dialog and the
   plan read the same link (the probes `_wall_below`/`_room_below` become its
   editor-side half).
2. **Face type → geometry.** `_dormer_face` consumes `face_mode` + the link:
   plain-wall and setback first (they differ only in the host strip in front).
3. **Balcony.** Cut the host in front of a set-back face down to the level-below
   deck; rail/terrace is a later nicety.
4. **Cantilever.** Confirm the face past the eave renders with open underside
   (no phantom wall below) — mostly a matter of the link reporting "nothing
   below" rather than failing to find it.

Each increment is gate-able and viewable on a saved plan with `fp3d … --shot`.

## 8. The balcony model, in full (Patrick, 2026-11-19)

Phase-3 first laid a balcony deck as a *geometric default* — face forward to the
host eave, across the dormer's cheek width. Patrick's full model makes the
**user's own walls** define the balcony. When a dormer's `face_mode` is
**balcony**:

1. **The deck.** The floor of the room the dormer sits on (the attic, the
   dormer's own level) is projected OUT past the face — downhill, toward the
   eave — to the **wall on the eave side of the face wall**, or to the **eave
   itself** when there is no such wall. The host roof over that strip is cut
   away. (Today's build stops at the eave always; the refinement is to stop at
   the front wall when one is drawn.)
2. **The balcony walls.** The walls the user draws OUTSIDE the dormer face (in
   front of it, between the face and the eave) ARE the balcony's walls. They
   rise to the **ceiling height of the attic floor** (the level's `height_in`).
3. **Railings.** A wall of type **railing** instead rises only to **railing
   height** (36", `fp3d.WALL_H["railing"]`) — not the ceiling.
4. **Cantilever, no front wall.** When the dormer is cantilevered (face past the
   footprint below), the attic floor is **closed underneath the dormer** — a
   soffit/floor so the overhang is solid, not open.
5. **Cantilevered balcony (cantilever + front walls).** When walls stand outside
   the face AND the dormer is cantilevered, the floor **extends out to those
   walls**, and the walls rise to the **ceiling height of that floor**; railings
   render at railing height.

So points 2/3 largely reuse walls the user already draws at their existing type
heights; the build's new work is (a) bound the deck/host-cut to the front wall
rather than the eave, (b) close the attic floor under a cantilever, and (c)
extend the floor to the walls on a cantilevered balcony. The deck sits at the
dormer level's floor (`base(level)`), where the railing/walls stand.
