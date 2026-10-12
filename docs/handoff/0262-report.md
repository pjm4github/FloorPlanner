# 0262 — report: his `wiscaway2026-10-11R2.json` given the shed dormer between the front gables and the porch roof, as the house model's iteration 11 has them — a new file beside his, nothing of the tools changed

**Code, 2026‑10‑11.** No merge has happened since
[`0261`](0261-report.md). His word:

> *"The roofs are fine now. I added wiscaway2026-10-11R2.json to the
> incoming. I want you to add a shed dormer to the roof between the 2
> front gable ends on the second level, then add the roof over the front
> porch. The shed dormer and the front porch roof will look like the
> house_cutout rev 11."*

## 0. WHAT WAS DONE

His file is untouched (the intake's own contract). The result is
**`fixtures/incoming/wiscaway2026-10-11R2-dormer-porch.json`** — his
plan plus six roof records, written by
`fixtures/incoming/wiscaway_r2_work/add_dormer_porch.py`, every number
derived from his roofs and walls; the work folder's `README.md` says
each one. Nothing in the tools moved: the dormer and the porch are what
[`0255`](0255-report.md) §3 and [`0258`](0258-report.md) §3 built the
house with, on his plan.

* **The shed dormer** (`rf_shed`, L2, host `rf4`): between his two front
  gables (`rf5`, `rf6`), on the recessed centre wall at y 696 — L2's
  `w136`, which already carries three `2448` windows at sill 20, the
  knee wall — 144″ wide centred on the recess, 18″ clear of each bay's
  side wall. Its top edge on the main slope at the height of the line
  between the gable peaks (both 160″ over L2), y 581; its face on the
  wall line at 108″; 52″ over 115″, 5.4:12. The wall under the face
  climbs with its windows, as the house's does.
* **The porch roof** (five shed pieces, L1): one 1:12 plane off the
  stepped front wall — the bay pieces from y 720, the centre and the two
  end strips from y 696 — 12″ overhang at the porch edge (y 817), hipped
  48″ at the porch's ends (x 287, 822). Its high edge 115″ over the porch
  floor, five inches under the main roof's knee-wall eaves (100 + 20);
  the edge 104.9″.

Schema clean. The invariant checker's two notes (`I6` on `w60`; `I7`,
`o15` off `w24`, which the 3D builder clamps) are in his file as
dropped, not from the roofs. Shot with the app's view in the work
folder: `r2-before-front.png` (his file), `r2dp-front.png`,
`r2dp-front-left.png`.

## 1. `fixtures/incoming/`, with ages

* `wiscaway2026-10-11R2.json` — his own, 2026‑10‑11; exit his to name.
* `wiscaway2026-10-11R2-dormer-porch.json`, `wiscaway_r2_work/` — mine,
  2026‑10‑11; his to rename, keep or drop.
* `house_cutout_transparent.png`, `house_cutout_1stfloor.png` — his own,
  2026‑10‑11.
* `house_cutout.json` (iteration 12), `house_cutout_work/` — mine,
  2026‑10‑11.
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 2. WHAT HAPPENS NEXT

His look at the file in the app. Nothing is open on a branch and nothing
is ordered; 0248's items 8 and 9 and the compose's next term stay named.

**Carried:** unchanged from [`0261`](0261-report.md).
