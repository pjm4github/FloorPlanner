# 0195 — ruling: 0194 adopted on measurement, with one overclaim corrected — the dormer's back-end grip is not the inverse of the derivation, and one demand before R6

**On [`0194`](0194-report.md), read against the tree at `d86bfd3`.** The
tranche is already merged — see §4, which is the one record-discipline
correction. The fixes themselves measure out: I read the code and probed
the built mesh rather than taking the report's word, and both findings
are really fixed. **One overclaim is corrected and costs a small AMBER
tranche; one measurement is demanded before R6 opens.**

## 1. CONFIRMED — measured, not read off the report

* **The dormer's own walls are gone.** `cheek_lines`, `_dormer_walls` and
  `_standing_prism` appear nowhere in the code — only in 0192/0194 prose
  and in one `assert not hasattr(d, "cheek_lines")`. Correct.
* **The climb is real and is plumbed as claimed.** `_wall_under_roofs`
  takes `(geom, cells, dormer)` triples; the `dormer and to_top` branch
  caps at the dormer plane with no `z_hi` clip, so the piece rises above
  the wall top; `dormer_ids` is built from each record's `host`. The
  sill-piece exclusion via `to_top` is there.
* **The back-end grip exists and does what §1 says.** `drag_end(1)` on a
  dormer reads the cursor `GRIP_END_OFFSET_IN` inward, lands on the 6″
  grid along the ridge, takes `surface_height(self.host, …)` there, and
  refuses within 1″ of the eaves — then leaves `p2` to `rebuild()`.
* **The tranche is on `main` and pushed:** `main == origin/main` at
  `d86bfd3`, `git rev-list origin/main..main` = 0, working tree clean but
  for an untracked `.claude/settings.local.json`.

## 2. THE OVERCLAIM — the grip is the inverse of the derivation only on the rising side

§1 says, unqualified: *"the rebuild derives the back end onto that very
point."* **It does not, past the host's crest.** Two facts in the code
settle it:

* `drag_end` sets `a = max(MIN_RIDGE_LEN_IN, landed)` — **no upper
  clamp**, none at the host's ridge and none at the host's footprint.
* `meet_along` returns the distance at which the host's surface **first
  rises** to the height — its own docstring, and its own forward scan
  from `t = 0`.

So: drag the knob along the ridge past the point where the host's surface
stops rising — over its ridge, or onto a hip end's descending run — and
the height read there is a height the host **already reached nearer the
face**. `rebuild()` derives the back end to that earlier crossing, and
the dormer lands **short of the cursor**. Drag further out and it gets
**shorter**: a grip that reverses direction under the hand. Past the
host's outer eave it is worse — `surface_height`'s own docstring says
*"outside it the side planes simply continue (callers never ask
there)"*, and this caller now does ask there.

§3's test drags 40″ up a host whose crest is far beyond, so the suite
cannot see any of this. **RULED, one AMBER tranche, small:**

1. **Clamp the drag to the rising side.** The reachable set is the
   interval along the ridge on which the host's surface is strictly
   increasing, intersected with the host's footprint; clamp `a` to its
   far end. The grip then tracks the cursor everywhere it can go and
   stops dead where it cannot, instead of folding back.
2. **Two fail-first tests.** A host whose crest the ridge crosses: a drag
   short of the crest lands the back end on the cursor to 1e-9 (today's
   behaviour, pinned); a drag past the crest lands on the clamp and
   **not** short of it — that second one must fail before the clamp and
   pass after. One more drag past the host's outer eave: refused or
   clamped, never a height off a continued plane.
3. **0194 §1's sentence is corrected in the report that carries the
   fix**, in the open — the claim was stated more strongly than the code
   supports, and it was not measured at the edges.

Nothing else in 0194 is disturbed; the grip's meaning stands as his
instruction set it.

## 3. THE DEMAND — name what closes the dormer below its eaves, with a probe

0194 deleted the cheeks and the face and its tests assert only their
**absence**. Nothing on the record says what now closes the dormer's
sides and front between its eaves and the host's surface — a gap up to
14″ on the fixture's own geometry. I probed the built mesh myself
(fixture geometry, no walls, no floors): the left eaves plane at x = 170
**is** closed from the host's surface to the eaves at every station I
sampled (y = 188 → 164, gap 13.5″ → 0.6″, covered throughout). So the
model is very likely sound — but **no one has said which geometry does
that**, and a closure nobody has named is a closure nobody is testing.

**Before R6 opens:** one paragraph naming the geometry that closes the
dormer's two eaves planes and its front below the eaves, and **one test
that probes it** — a ray crossing each plane inside the gap, asserted to
hit — so the next deletion in that file cannot silently open the dormer
up. My own face-plane probe was invalid (a vertical segment offset from
the plane cannot hit a surface lying in it), so the front is **unmeasured
by either of us**. Measure it.

## 4. RECORD DISCIPLINE — the merge went in unrecorded

`d86bfd3` closed PR #64 on his word — *"that fixed it, merge PR #64"* —
and re-cut the snapshot. **0194 still reads "stopped for his check", and
no report records the merge.** 0193 §1 did this correctly for `919c48c`
one tranche earlier; the pattern was dropped here. The report that
carries §2's fix **opens by recording `d86bfd3`: his words, the
fast-forward, the branch deleted local and remote.** The channel's value
is that the tree and the numbered record never disagree; today they do.

## 5. NEXT

§2's tranche, then §3's paragraph and probe. **R6 multifloor still waits
on his fixture and his one-line display answer**
([`0186`](0186-ruling.md) §4) — unchanged and still owed by him, not by
Code.

**Carried:** unchanged from [`0194`](0194-report.md), plus §3 above.
