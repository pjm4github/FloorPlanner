# 0357 — report: control D and F1 built; F2–F4 measured (0356)

**Code (Claude Opus 4.8), 2026-11-17.** Answers [`0356`](0356-ruling.md) —
knob D, F1, and the three measurements F2–F4 — with [`0352`](0352-ruling.md)
governing. The code is on branch `dormer-item` (phase-2 increment C), gated
GREEN, AMBER, folded into Patrick's phase-2 check. This report and the
`0356` ruling land on `main`; the evidence PNG is under
`docs/evidence/0356-dormer-face/`.

## 1. Knob D and F1 — built (`0356` §1, F1)

- **Control D (`guide_face`).** A PURPLE knob (per `DORMER_CONROLS.md` §D)
  on the ridge centreline that slides the face guide along the ridge into
  the dormer, writing `guide_face_in` (Cowork's new `dg` field). It is not a
  `_r` knob, so a shed keeps it. `tests/test_dormer_item.py` covers the drag
  and the shed case.
- **F1 — the context.** `DormerItem.param_context` now gathers the user's
  walls on the dormer's own level: `dg.project_wall` picks the FACE walls
  (square to the ridge, within 6 in of the face guide) and `dg.project_side_wall`
  the two SIDE walls, their openings handed to `dg.project_openings` as
  `s0`/`s1` from each wall's first end with `sill_in`/`head_in` (the window
  default sill, or the opening's own; head = sill + height). `face_wall` /
  `side_walls` are the joined extents, or `None` when it LOOKED and found
  none (absent = no scene, nobody looked) — the distinction `DormerKind`'s
  advisories key on. **No geometry in `items.py`** — it gathers and calls `dg`.
- **Cost.** The gather is SKIPPED while a knob (or the item) is held
  (`self._frozen`), so it never runs per mouse-move during a drag — the
  `0354` §2 discipline. It runs when the dialog opens and on each settle.

## 2. F2 — the preview, seen

Rendered the dialog's preview headless on a dormer with a face wall holding
two windows (one low, one high in the gable) and a left-side wall holding
one, over the 96-in ceiling. `docs/evidence/0356-dormer-face/preview-after.png`
(and `-before.png`). **It draws right:** the gable end with its roof line,
the two windows each at its own sill/head — the high one correctly ABOVE the
orange ceiling line, up in the gable, not flagged — and the two side panels
(one with a wall, one dashed "no wall drawn"), the host line drawn when there
is a host.

- **One plain paint bug, FIXED:** the "ceiling 96" label was clipped to a
  52-px box and lost its last digit (rendered "9€"). Widened the label rect
  to the panel's right edge (`dormer_view.py`). The after-PNG reads cleanly.
- **Not a widget bug:** in a headless render the widget's default `QFont`
  has no glyphs (tofu); the app's own font renders it. The evidence PNG is
  rendered with the repo font (`DejaVu Sans`), as the watcher's PNG is.
- **For Patrick (judgment, not bugs):** the sides are laid "seen from
  outside, face toward the middle" (right drawn left, left drawn right); a
  "no wall drawn" side shows a dashed rectangle plus the eave-overhang gap,
  which is subtle. Both are as `0356` describes; flag if you want them
  changed.

## 3. F3 — can the app stack openings today? YES, end to end

Placed two windows at the SAME position along a wall (`s = 60`), one sill 24,
one sill 80. Measured all three paths `0356` named:

- **Plan:** both coexist on the wall, both `fits()` — no refusal, no merge.
- **Save / reopen:** `design_document()` → reopen carries BOTH, each with its
  own sill (24 and 80).
- **3D (`build_model`):** the wall is cut TWICE — 60 triangles with both
  windows vs 48 with one and 12 with none; `openings` stat = 2.

**No change to walls is needed for stacking** — it already works, so the
stacked decorative-plus-lower-window case `0356` §2 describes is supported by
the existing opening model. No new ruling required here.

## 4. F4 — an opening whose head is above the room ceiling

Two parts, both measured:

- **The opening sheet ACCEPTS it.** The window property sheet's sill spins
  `[0, 600]` with no clamp to the room ceiling; the head is `sill + height`,
  derived. So a window whose head sits above the ceiling is accepted and
  stored.
- **`build_model` does NOT cut it in the climbing band.** An ordinary
  opening's head is clamped to the wall's modelled top,
  `min(head, z1 − z0)` with `z1 = top(level)` — the storey ceiling
  (`fp3d.py:3277, 3329`). Measured straddle: a window sill 60 / head 100 over
  a 96-in ceiling is cut only to 96; the 4 in above fills SOLID. Only a
  recorded dormer-FACE cut (`wall_face_cuts`, `fp3d.py:3331+`) gets the
  unclamped climb-band void — that is the OLD roof-dormer's path, not a
  user-drawn wall under a furnishing dormer.

**So: the sheet is fine; the 3D cut is the gap.** Phase 3 owns it (`0356`
F4): the furnishing dormer's wall rule must route the user's high window into
the climb band the way the dormer-face cut does. I did not change walls — it
needs the phase-3 ruling you already named.

## 5. Where it stands

- `dormer-item`, AMBER, gate GREEN — phase-2 increments A, B and now C.
  Patrick's phase-2 check batch is now five (`0356` §4): drop a dormer on a
  roof; move B C D E F A; release and see the knee lines settle; open the
  dialog and see the gable end and both sides; draw a wall on the face guide
  with a window and see it appear. The checkout stays on `dormer-item`.
- Still Cowork's / Patrick's: the A/G ridge-slide behaviour (`0356` §1 —
  built as "A across trades span, symmetric off"; his to confirm).
- Phase 3 next, on his word: the 3D (`to_roof_record` + the wall rule, which
  F4 shows must cut the high window in the climb band) and `0350` §1 (the
  clipper that does not return) measured first (`0352` C4).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XVitzXNKQWS64xhKKpacra
