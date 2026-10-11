# 0250 — report: the house regenerated from the first-floor plan (iteration 6); a shed's ends are never joined — found on it, fixed on `roof-shed-form`; PR #82 updated, one commit

**Code, 2026‑10‑11.** No merge has happened since
[`0246`](0246-report.md). His word, with `house_cutout_1stfloor.png`
dropped in `incoming/`:

> *"regenerate the plan starting from iteration 6 looking at the plan
> view in the house_cutout_1stfloor.png"*

## 0. ITERATION 6 — the plan's footprint, the picture's roof lines

The first-floor plan, read at ~1.42 in/px (the porch is labelled
8 × 59 ft): a body 846 × 312 with two bays projecting 61″ from the
front wall (left x 124–330, right x 514–699); a porch 8 ft deep in
front of the bays and 13 ft at the recessed centre and the ends,
x 74–784, 10′ ceiling, steps at the middle. `make_house_plan.py` in
`fixtures/incoming/house_cutout_work/` builds it: both storeys on the
outline (L1 120″, L2 108″), the entry centred between the bays, the
plan's windows at their walls; the main roof 8:12 with a 36″ knee wall;
the two gables on the bays at 12:12; the shed dormer over the recessed
centre with its face on the recessed wall (plan C lets the wall's three
windows show); the porch roof ONE plane at 2:12, tucked an inch under
the main eaves, in FIVE shed pieces so the bays are not under it — the
centre, the two ends hipped outward, the two bay strips — meeting at
equal height, no risers. Schema and invariants clean; renders beside it
(`iter-06-front.png`, `-front-left.png`, `-plan.png`). Published as
`fixtures/incoming/house_cutout.json` (iteration 4 replaced).

## 1. FOUND ON IT, FIXED ON THE BRANCH — a shed's ends are never joined

The main roof lost its whole front strip beside the shed dormer at the
right end — 147 × 72 in of ground, measured gone with the dormer in and
whole with it out. Cause: the shed dormer's two ridge ends stand inside
its host, so `compute_roof_clips` treated them as JOINED ends and
extended them — but a shed's ridge is its high edge and its plane is
constant along it, so the extension ran the same plane sideways across
the main roof, a phantom the fixed point pruned to BLANK ground, and the
main's own cells went with it (0181's class: blank ground under an
uncertified limb). **A shed's ends are never joined now** — one `continue`
at the top of the joining loop for `form == "shed"`: its ends are its
sides, faces in 3D; a shed against a main is a lean-to, not a join. A
gable dormer's back end is still joined (`test_roof_dormer.py` pins it;
every roof suite green). Pinned by
`test_a_sheds_ends_are_never_joined_so_the_host_keeps_its_ground_beside_a_shed_dormer`:
the main keeps every inch beside the dormer, the shed draws its own
footprint only, no warnings.

A second equal-height tie noted on the way: the porch roof's high edge
at exactly the main eaves height along the same line; tucked 1″ under
in the model (0248 §2 item 6's class; plan D's territory).

## 2. WHERE IT STANDS

[PR #82](https://github.com/pjm4github/FloorPlanner/pull/82), still ONE
commit on `roof-shed-form` rebased onto this landing: plans A and C
([`0249`](0249-report.md)) plus the shed-ends rule. **AMBER** — his
check: the End-On dialog's Form row, a shed saved and reloaded, and the
house model's iteration 6 in the 3D view.

## 3. `fixtures/incoming/`, with ages

* `house_cutout_transparent.png`, `house_cutout_1stfloor.png` — his own,
  2026‑10‑11.
* `house_cutout.json` (iteration 6), `house_cutout_work/` — mine,
  2026‑10‑11.
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 4. WHAT HAPPENS NEXT

His check of PR #82 and his look at iteration 6. Then 0248 §3's B, D
and E on his word. Behind them: the compose cost
([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0249`](0249-report.md).
