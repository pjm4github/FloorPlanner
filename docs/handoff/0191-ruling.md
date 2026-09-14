# 0191 — ruling: the dormer read-back is adopted nearly whole — one gesture correction, and the build is ordered

**On [`0190`](0190-report.md).** The method is the standard the channel
exists for: the machinery was **measured with a dormer-shaped record before
anything was proposed**, and the measurement carried the design — today's
rules already build a correct gable dormer when the back end sits at or
past the meet, so the clip stays byte-for-byte. RED lifts; **R5b builds.**

## 1. ADOPTED AS PROPOSED

* **A dormer is a `roof` record with an optional `host` field** — presence
  makes it a dormer; additive, no version bump; a dangling `host` reported
  and skipped, never a silent floating roof.
* **The back end is derived where the ridge meets the host plane, and
  still written** — the `eaves_bind` discipline exactly; re-derived on any
  edit of dormer or host; a ridge that cannot meet the host (above its
  ridge) **refused at the dialog**, not clamped.
* **`compute_roof_clips` untouched.** §0's table is the receipt and
  becomes tests as written.
* **The `roof_clip_spans` territory fix** — a roof dashes a wall only
  where the wall point lies in that roof's own drawn territory. This is a
  real correction R4g already implied for any overlapping pair; fail-first
  test on §0's second scene, and one glance that non-overlapping cases are
  byte-identical.
* **Cheeks and face are derived geometry, not `walls` records**; thickness
  one constant; the face's window an `openings` entry, named, not v1.
* **Deleting a host deletes its dormers, one undoable gesture.**
* **v1 = gable dormer; hip named unchecked; shed waits for its own ruling**
  (a one-plane shape that does not fit the record — correctly refused
  rather than shoehorned).
* Grips: back-end grip disabled (derived), ridge grip slides along the
  eave, eave grips set width, front grip walks the face up the slope.

## 2. THE ONE CORRECTION — a Dormer TOOL, not an overloaded press

§3 hangs the gesture on "press inside a roof's region while the ridge tool
is active." **That press is not free**: ordinary crossing ridges — the
R4f/R4g bread and butter — legitimately START inside another roof's
region, and the branch would steal them (or force a modifier nobody will
remember). **RULED: a separate "Dormer" item in the Roof menu — its own
tool, its own macro letter — sharing the two-stage machinery** exactly as
proposed: press snaps to the host's clip trace (the placement map), drag
sets the width on the grid, Shift frees the direction, release opens the
End-On dialog as its fourth door with §3's defaults. The ridge tool stays
untouched, and the two tools cannot be confused in a macro recording.

## 3. THE BUILD — one AMBER tranche, §5's order, gated once at the end

(a) `host` end-to-end + derived back end + plan-view cheeks/face → (b) the
territory fix → (c) 3D cheeks and face → (d) the Dormer tool → (e) the
fixture: **§0's geometry promoted as `dormer-gable-check.json`, and
Patrick's wiscaway loft as the check plan if he drops it in `incoming/`**
— his hip-roofed loft from the R5a picture is the natural real case.

> **His check:** sketch a dormer on the loft from the Dormer tool — the
> trace and the room's dashes open under it, the valleys draw solid, the
> back end lands on the host plane by itself — then the same in 3D:
> cheeks, face, gable, nothing poking through.

## 4. HOUSEKEEPING, one line each

The two `w7` files in `fixtures/incoming/` are 23 days promoted — exit 2
(delete) unless Patrick says keep. R6 (multifloor) still waits on his
fixture and his one-line display answer ([`0186`](0186-ruling.md) §4).

**Carried:** unchanged from [`0190`](0190-report.md).
