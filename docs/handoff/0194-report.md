# 0194 — report: his look at the merged dormer — the back-end grip returns, the dormer's own walls go; fixed on PR #64's branch, stopped for his check

**Code, 2026‑09‑24.** Patrick's look at the dormer as merged (R5b, PR #63),
his words in full: *"something is wrong with the dormer control knobs.
There is a missing control know on the the ridge of the dormer where it
meets the roof. In addition that walls of the dormer are being drawn down
from teh dormer. Ir should show only the roof line and intersect withe
the walls under it."* Two findings, both his own direct instruction as
authority ([`0065`](0065-ruling.md) §2), both **fixed on
`roofs-r5c-undo-macro` — PR #64's branch, the one open AMBER tranche —
as its second commit**, so his check of PR #64 covers the undo, the
macro and these together. Gate GREEN.

## 1. THE MISSING KNOB — the back-end grip returns, and sets the ridge height

R5b hid the dormer's back-end grip because that end is derived
([`0191`](0191-ruling.md) §1: "back-end grip disabled (derived)"). His
look says the knob belongs there, and it has a natural meaning: **the
dragged point is where the ridge is to meet the host**, so the grip sets
the **ridge height** — the host's surface height at that point — and
the rebuild derives the back end onto that very point. `RoofItem.drag_end(1)`
on a dormer: the cursor read `GRIP_END_OFFSET_IN` inward as for every
end grip, landing on the 6″ grid along the ridge; the height taken from
`surface_height(host)` there; refused (unchanged) when that would put
the ridge within 1″ of the eaves. The grip is visible again; the other
four keep their meaning (face up the slope, width, ridge sideways). The
ruling's line is superseded by his instruction, on the record here.

## 2. THE DORMER'S OWN WALLS GO — the house walls climb into its roof

R5b gave the dormer derived cheeks and a face, drawn dashed in plan and
built in 3D as prisms hanging from its eaves down to the host plane
(0192 §1). His look: *"drawn down from the dormer … it should show only
the roof line and intersect with the walls under it."* So:

* **Plan:** a dormer draws only its roof lines — two eaves, the front
  gable line, the ridge; the back end is joined and the valleys are the
  seams. `cheek_lines` and its plan lines are deleted.
* **3D:** `_dormer_walls` and `_standing_prism` are deleted. Instead, in
  `_wall_under_roofs`, a wall piece whose territory owner is a **dormer**
  is capped at the dormer's plane (less the same 4½″ drop every wall
  gets) **whether that is below or above the wall's own top** — the wall
  climbs into the dormer roof, the way a gable wall climbs into a gable.
  Only pieces that run to the wall's top climb (piers and headers); the
  wall under a window sill keeps its own flat top. Territory entries
  carry a dormer flag (`rid in dormer_ids`, from the record's `host`).
  Under an ordinary roof nothing changes: walls are only ever lowered.

What the check will show: a wall the dormer sits over rises through the
old ceiling line into the dormer's roof, capped by the dormer plane; a
wall beside the dormer stays at its height or is capped by the host as
before.

## 3. THE CHECK — receipts

`tests/test_roof_dormer.py` (3 rewritten): the dormer's plan lines are
exactly three dashes and the ridge, and there is no `cheek_lines`; a
selected dormer shows all five grips; the back-end grip dragged to the
point 40″ up the ridge sets the ridge height to the host's 123″ there
and the derived back end lands on that point, and a drag that would put
the ridge under the eaves is refused. `tests/test_viewer_dormer.py`
(rewritten, 4): a dormer builds no walls of its own; a wall crossing
under the dormer climbs to the dormer plane less the drop (131½″ at the
ridge line, above the level's 96″), keeps 96″ outside it, and the same
wall with no dormer never rises above 96″ (the control); the wall under
a sill does not climb; the roof meshes are unchanged by `host`. All
pre-existing wall-clip, grip, tool and macro tests pass unmodified.

Full suite **1347 passed**, 7 deselected (`perf` lane), `ruff` clean,
gate GREEN — the branch's own run.

## 4. NAMED

* The macro's `DORMER` token and the recorder are untouched by this;
  0193 stands.
* A wall under the dormer's *back* territory (behind the valleys' apex,
  where the dormer plane is barely above the host's) climbs to the
  dormer plane there too — a few inches. Consistent, and invisible from
  outside; named.

## 5. `fixtures/incoming/`, with ages

`README.md` only.

## 6. WHAT HAPPENS NEXT

His check of PR #64, now three things: record a dormer and replay it;
delete a host and undo it; drag the dormer's back knob and see the
walls under the dormer climb into its roof in 3D. On his word PR #64
merges, branch deleted in the merge step. Then R6.

**Carried:** unchanged from [`0193`](0193-report.md).
