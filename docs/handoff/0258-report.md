# 0258 — report: 0248's plan E and its item 6 built on his word — the hip run settable per end; a `post` furnishing that rises to the roof over it; the porch floor as an exterior room; iteration 12 of the house — on `porch-posts-hip-run`, AMBER, for his check

**Code, 2026‑10‑11.** No merge has happened since
[`0257`](0257-report.md), which recorded PR #84 and left E and the hip
run his to order. His word: *"Go ahead."*

Built on `porch-posts-hip-run`, ONE commit on `main`'s tip, pushed, PR
open. The checkout is on it.

## 0. THE HIP RUN, PER END (0248 §2 item 6)

A hip end ran the roof past the ridge end by the mean of the two spans,
and nothing could say otherwise — R4b's "the same discipline as pitch".
The house's porch showed the limit: a one-plane roof 157″ deep whose end
hips wanted the 48″ that iteration 1's 96″/0″ spans had given by
accident. Now:

* **The record:** `hip_run_in: [end0, end1]`, index-aligned with `ridge`
  and `gable`, a length or `null` (= derived, the mean of the spans —
  what every record without the key means). Omitted while both ends are
  derived. Additive optional, no version bump. A negative run is refused.
* **The item and its twin:** `RoofItem.hip_run_in` (a setter normalises
  a bare number, a pair, None); `hip_extension(end, gable, span, run)`
  returns the end's own run when set, else the mean; `RoofGeom` reads
  the same key, so the clip's hip plane descends over the run.
* **The 3D builder:** the unclipped path's hip corner and hip plane use
  the end's run; the clipped path follows the twin.
* **The dialog:** two fields, *Hip run, end with the marker* and *Hip
  run, other end*, enabled while that end is a hip, seeded with the end's
  own run or the derived one; OK writes an end's run only where it
  differs from the derived value, so an untouched end stays derived and
  follows the spans.
* **The bridge** writes the key once an end is set and reads it back.
* **Tests** (`tests/test_hip_run_and_posts.py`): the item derives and
  overrides per end and its footprint follows; the twin agrees with the
  item and its hip plane descends over the run; the document round-trips
  and an unset roof writes nothing; the dialog's fields; the builder's
  hip corner moves from the mean to the run.

## 1. THE POST (plan E, first half)

* **The catalog:** `post` — a 6×6 square with its diagonals, "Post 6x6",
  in the Framing group; `_gen_assets.py` regenerated (96 symbols now).
  Its solid is a new form, **`column`**, height 96 as the fallback.
* **The builder:** `column` is a built form. A column rises from its
  level to the UNDERSIDE of the lowest roof whose footprint (hip ends
  and overhangs included) holds its point — the surface there less the
  roof slab's thickness — found among the roofs the build already lifted
  to absolute height (`_roof_underside_at`). No roof over it: the
  catalog's height, said in the report's info.
* **Tests:** a post under the porch roof tops out at the underside
  there; one beyond the roof stands at 96 and is reported; the manifest
  and the Framing group carry it. `test_viewer_model.py`'s catalog count
  moves 95 → 96 and its partition test knows a column is built directly.

## 2. THE PORCH FLOOR (plan E, second half)

No new object: a room of category `exterior` on the porch's outline,
every edge open (`wall: null`), is what the builder already draws as a
slab in the exterior colour. The schema allowed it all along
(`exterior` "covers roofed-but-unconditioned space -- porches, decks");
the house had simply not used it. Said here so plan E's "slab region"
is closed by the room, not by a new kind.

## 3. ITERATION 12 OF THE HOUSE

The porch floor as `r_porch`; eight posts at the porch edge (the porch
corners, the bay corners, a pair either side of the steps), each
reaching the porch roof over it; the end pieces' hips on a 48″ run.
Schema and invariants clean. `fixtures/incoming/house_cutout.json` is
iteration 12; shot with the furnishings on (`iter-12-q3d-*.png`). Not
attempted: the steps and the stone base (0248 item 8), a porch roof
turning the house corner (item 9).

## 4. THE RECEIPT

`--quick` passed; ruff clean; the full gate GREEN on the branch commit.

## 5. TIER

**AMBER** — a format change (`hip_run_in`) and a feature (the post, the
column form). For his check: the porch in the 3D view (the posts meeting
the roof, the floor, the short end hips) and the End-On dialog's hip-run
fields on a porch end piece.

## 6. `fixtures/incoming/`, with ages

* `house_cutout_transparent.png`, `house_cutout_1stfloor.png` — his own,
  2026‑10‑11.
* `house_cutout.json` (iteration 12), `house_cutout_work/` — mine,
  2026‑10‑11.
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 7. WHAT HAPPENS NEXT

His check of the PR. 0248's plan is then built out but for items 8 and
9, named above and not ordered. Behind it: the compose cost
([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0257`](0257-report.md).
