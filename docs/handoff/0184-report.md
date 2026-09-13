# 0184 — report: his second fixture — a ridge cut short over another roof needs a gable end, not an extension; built, the pinch unchanged

**Patrick, 2026‑09‑13, on [`0183`](0183-report.md):** *"The joints look
good"* — then a second fixture, `threeRidgeShortRidgeFloorplan.json`
(promoted from `incoming/` under exit 1), the three-ridge plan with rf2's
ridge deliberately cut short: *"there should be a gable end that shows up
at the end of the roof outline over the top of r#1 … The 3D view doesnt
render in this test case."* Same branch, `roofs-r4g-full-footprint`, PR
#60. AMBER continues.

## 1. What the fixture showed, measured

rf2's ridge now ends at (664, 393): 75" before rf1's ridge and 15" above
rf1's slope there. The clip did not fail and the 3D model built without
a note — but the plan carried rf2's planes on past its end, all the way
to rf1's ridge (both ridges are 132", so rf2's extended ridge meets rf1's
exactly there), and a real hole of 38 grid points (1.5%) sat east of
rf1's own end at (756, 468), where rf1's extension into rf3 and rf3's
ground had pruned each other. Both are the same rule: since R4d every
swallowed end has been a JOINED end — its planes extended into the host
"up to the seam", its end line dropped. That is right for an end at or
below its host (the L's B start flush on A's ridge; a lower wing run
into a main), where the extension closes the hip under the host. It is
wrong for an end standing in the air above the roof it sits on: nothing
is there to extend into, and the end is a gable face.

## 2. The rule, and the clause the pinch forced

**A swallowed end that stops short of every host's ridge, standing above
the host, is OPEN**: no extension (`ext` zero at that end), so the item
draws its end line, clipped to where the roof is drawn, and `fp3d`
builds its fascia — both already keyed on `ext`. An end at or below its
host is joined, as before.

**An end whose ridge has CROSSED a host's ridge is never open.** Built
without this clause, the pinch fixture changed: rf2's south end there
stands 4" above rf3, so it opened, its extension vanished — and that
extension was the very ground that kept rf1's east arm severed from
rf1's body. rf1 reconnected around rf2's end and ran past the pinch,
which [`0177`](0177-ruling.md) forbids and his v2 reference draws
otherwise. A crossed end is a cross-gable's arm: either the phantom the
fixed point prunes at the crossing (A's wedge, rf1 east of the pinch) or
the arm that survives and runs on joined (rf2's south arm, wrapped by the
rf2/rf3 seam exactly as his v2 reference has it). With the clause the
pinch fixture is byte-for-byte 0183's — same areas, same seams, same
rounds.

## 3. Receipts

* Short-ridge fixture: 0 blank, 0 double, one round, nothing pruned.
  rf2's and rf1's ends both open; rf2 drawn to its end edge and not one
  inch past; the rf1/rf2 valley from A's corner ends ON rf2's end edge;
  rf1 owns its whole ridge to 756 and shows its own gable end over rf3.
  Plan re-rendered headlessly: rf2's gable end line across its end, the
  valley meeting it. 3D: builds clean, the gable face standing over rf1
  (`fp3d.py --shot`, checked).
* Pinch fixture: unchanged from 0183 (0% blank, rf1 ends at the pinch,
  rf2 runs on to its end, `ext` still set at both crossed ends).
* Two new tests name the fixture (`fixtures/README.md` row added):
  `test_0184_a_ridge_end_in_the_air_over_its_host_is_an_open_gable_end`
  and `test_0184_the_open_end_draws_its_end_line_and_the_pinch_is_unchanged`.
  `ruff` clean; gate GREEN — the census is in the landing commit.

## 4. Named, not built

* rf2's end at the pinch is 4" above rf3 and stays joined by the crossed
  clause — a 4" fascia is not drawn there. If a crossed arm that survives
  should also end open, that is one line to change and the wrap-around
  seam at rf2's end goes; left as his v2 reference has it.
* The rule reads the ridge END point only. An end below its host at the
  ridge but above it at an eave corner (a wide, low joiner into a steep
  host) stays joined; no fixture exercises it.

## His check

The short-ridge plan and its 3D view — the gable end over rf1 — and the
pinch fixture once more, unchanged.

**Carried:** unchanged from [`0183`](0183-report.md).
