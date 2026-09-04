# 0152 — report: R3b — the roof-clip dotted line

**Code, 2026‑09‑03, answering [`0145-ruling.md`](0145-ruling.md) §3 (R3b),
the next tranche after R3 ([`0150`](0150-report.md)/[`0151-report.md`](0151-report.md),
closed).**

---

## 1. WHAT'S BUILT

**The dotted line itself, in his own words** ([`0145`](0145-ruling.md) §3):
*"affected walls should show a dotted line where any part of the roof is
clipping the full height of the room underneath."* `roofs.py` gains
`roof_clip_spans(scene, wall)` — the sub-span(s), in inches from a wall's
own `p1`, where a roof on the wall's floor covers it below the room's own
ceiling height — and `WallItem.paint()` (`walls.py`) draws them, a dashed
orange line alongside the wall's own body, right after the existing
type-decoration block.

**The geometry is exact, not sampled.** Every governing quantity — how far
along the ridge a point on the wall projects, how far off it, and (given
those) the roof's own height there — is AFFINE in the wall's own arc-length
parameter. So every place a condition can flip true/false is a single root
of a linear equation: collect every root that lands on the wall, sort them
into a partition of `[0, length]`, and read the (constant-within-each-piece)
verdict once per piece, at its midpoint. This is the same idiom an
opening's own span already uses to cut a wall run into pieces — reused,
not invented for this.

**The ceiling reference is per-wall, from whichever room borders it.**
`_wall_ceiling_in` probes a little past each face of the wall (offset by
`t/2 + 6in`, since a room's own outline stops at the wall's INTERIOR face —
the bare centreline is never actually inside one) and reads
`RoomItem.properties["ceiling_height_in"]`, the SAME room-lookup
`items.py`'s `StairsItem._ceiling_height` already uses for an unrelated
purpose, reused rather than re-derived. **The lower of the two sides
governs** when a wall borders two rooms with different ceilings. **No
bordering room at all** (an exterior wall with nothing built against it, or
an unenclosed sketch) falls back to `DEFAULT_ROOM_PROPS`'s own default
(96in) — the same fallback value `_ceiling_height`'s own default names,
though read through a different constant, since roofs.py may not import
`items.py` (layering: `roofs.py`'s own docstring already states it sits at
the SAME layer as `rooms.py`, both loading after `walls.py` and before
`items.py` — importing `items.py`'s `DEFAULT_CEILING_IN` from here would
invert that order).

**Overhang continues the same slope**, exactly as R3's 3D planes do: the
covered footprint is `along in [0, ridge_len], |perp| <= span + overhang`,
and height is `ridge_h - slope * |perp|` throughout, so a wall standing at
the outer overhang edge is still covered and its height keeps dropping past
`eaves_h` at the same rate, never a separate flat strip.

**A late import closes a real cycle**, the same treatment this codebase
already gives the walls↔rooms cycle: `roofs.py` imports `walls.py` at
module level (it always has, for `WallItem` in `nearest_eaves_wall`), so
`walls.py` cannot import `roofs.py` back at module level without a real
circular import — `WallItem.paint()` imports it late, inside the method,
exactly where `rooms.py` names are already imported late elsewhere in this
file. `roofs.py` importing `RoomItem` from `rooms.py` is a NEW,
one-directional edge (`rooms.py` imports neither `roofs.py` nor
`items.py`), so it needed no late-import treatment of its own.

**No schema or document change** — R3b reads fields R1/R2/R2b/R2c/R3
already wrote or already had (`Roof`'s ridge/heights/span/overhang,
`Room.properties["ceiling_height_in"]`); nothing new is persisted.

## 2. THE CHECK, RUN HEADLESS

His own words for R3b's check: *"his check on the 45° wing, where the clip
is real."* `docs/evidence/roof_clip_wing_receipt.py` builds a synthetic
120x80in wing rotated 45° (the same shape shape R3's own `--shot` evidence
used), ridge along its long axis reaching exactly to both gable walls,
`eaves_h=60in`/`ridge_h=140in` against the app's own default 96in ceiling —
chosen so the clip is real on every wall, not a boundary-case zero-width
sliver: the two long (eaves) walls clip UNIFORMLY along their whole run
(the roof's height there is the constant 60in, below the 96in ceiling
everywhere it covers them), and the two short (gable) walls clip in TWO
sub-spans each, `(0, 18in)` and `(62, 80in)` of their own 80in run — clear
in the middle, near the ridge crossing (height there reaches 140in, well
clear), clipped toward both outer corners (height ramps down toward
`eaves_h`). Runs under `QT_QPA_PLATFORM=offscreen` (2D `QGraphicsScene`
painting, not `fp3d.py`'s GL path — D77/D78's finding is GL-specific).
Rendered: [`docs/evidence/roof-clip-wing.png`](../evidence/roof-clip-wing.png) —
the wing's own dashed orange clip line visible on all four walls, alongside
the roof's existing dashed eave/gable overlay and its heavy ridge line.

## 3. TESTS AND GATE

`tests/test_roof_clip.py` (new, 11 tests, `walls`-marked): the core
gable-end case with exact boundary values against the closed form; the
no-roof / eaves-already-clear-the-ceiling negatives; an eaves-parallel wall
clipping its ENTIRE run (the other shape the spec's "any part" language
implies but does not spell out); a different-floor roof not clipping; the
lower of two bordering rooms governing (with rooms built to actually
straddle the wall, not merely contain it — a room rect that just contains
the wall's centreline on both sides would not exercise the two-sided
lookup at all); the default-ceiling fallback with no room present; overhang
continuing the same slope past the wall; two roofs' clip spans unioning
correctly on one long wall; and a pixel-level integration test (the same
polarity discipline `test_walls.py`'s own junction-seam pixel test uses)
confirming the dashed ink actually paints where the analytic spans say it
should, and nowhere else — including a genuine `QGraphicsScene.render()`
pitfall caught while writing it: `aspectRatioMode` defaults to
`KeepAspectRatio`, which silently letterboxes a non-square source into a
square target and breaks a naive linear scene→pixel formula; fixed by
passing `IgnoreAspectRatio` explicitly, named in the helper's own docstring
so the next pixel test in this codebase does not rediscover it the hard
way.

Full suite: **1144 passed**, 7 deselected (`perf` lane), 0 failures. `ruff`
clean. `python tools/gate.py` (full mode): **GREEN**.

## 4. DISPOSITION

**R3b is AMBER tier** ([`0139-ruling.md`](0139-ruling.md) §3 /
[`0145`](0145-ruling.md) §3) — built and gated GREEN, going to its own
branch and PR next (`roofs-r3b-clip-line`), and Code stops there: no merge
without Patrick's own check. §2 above supplies the named evidence; the PR
is for him to run it by hand — sketch a roof low enough to clip a real
room in the running app (the 45° wing is the shape he asked for) and
confirm the dotted line appears where it should.

**R4, R5 do not start** until this merges, per [`0139`](0139-ruling.md)
§4's standing order.

**Carried, unchanged:** room-label rounding ([`0131`](0131-ruling.md) §2);
delta-snap sites; D61-family; D83/D84 (held); yard items; ridge/eaves
horizontal repositioning (R4).
