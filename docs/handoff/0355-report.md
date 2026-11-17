# 0355 — ask: control D (the face guide) needs a `dg` state field

**Code (Claude Opus 4.8), 2026-11-17.** Raised against [`0352`](0352-ruling.md)
§3 (phase 2, the `DormerItem` and its knobs) and the controls in
[`0351`](0351-ruling.md) / `DORMER_FURNISHING_PLAN.md`. Tier: **no code** —
this is a request for a ruling, not a change. Phase 2 is built and GREEN on
branch `dormer-item`, AMBER for Patrick's check; six of the seven knobs land
on existing `dg` state. One does not, and I will not add a field to the
reviewer's pure-geometry module unilaterally.

## The gap

`dormer_geometry.STATE_DEFAULTS` stores an offset for each **side** guide —
`guide_left_in`, `guide_right_in` — so knob **C** moves each side wall's guide
line inward from the eaves line. There is **no field for the face guide**
(control **D**). `guides(st)` returns the face line's y hard-coded to `0.0`:

```python
def guides(st):
    """Controls C and D as GUIDES, not walls: the two side lines and the face
    line the user draws their own walls against. Local x of (left, right)
    and the face's y (always 0)."""
    left  = st["guide_left_in"]  if st["guide_left_in"]  > _EPS else st["span_left_in"]
    right = st["guide_right_in"] if st["guide_right_in"] > _EPS else st["span_right_in"]
    return min(left, st["span_left_in"]), min(right, st["span_right_in"]), 0.0
#                                                                         ^^^ control D, no state
```

So knob D has nothing to write to: the docstring names control D, but phase 1
stored only the two side guides. The face guide cannot move off the face.

## The ask

Add one state field so D is symmetric with C — the face wall's guide line
offset **into the dormer** from the face (local +Y), 0 = on the face. By the
pattern of the side guides I would expect:

- `STATE_DEFAULTS["guide_face_in"] = 0.0` (and `normalize_state` to clamp it
  to `[0, depth_in]`, the way C clamps to the span);
- `guides(st)` to return `min(guide_face_in, depth_in)` as the third value in
  place of the literal `0.0`;
- `knee_lines` / `plan` unaffected (D is a guide the user draws a wall against,
  not a plane — same standing as C today);
- the schema `$defs/dormer_state` to gain `guide_face_in` beside
  `guide_left_in`/`guide_right_in`.

**But the field name, its sign and datum, the clamp, and whether D is even in
scope for this feature are yours to rule** — D is the one control that reaches
into your geometry module, and I would rather you set its shape than have me
guess and have it reworked.

## What I did instead, pending your ruling

Phase 2 ships the other six knobs (B span, C side guides, E eave overhangs,
F face overhang, A apex/dialog) wired to existing `dg` state. Knob D is
**not** placed — `DormerItem._grip_kinds` omits it — so nothing in the item
references a field that does not exist yet. When your ruling lands I add the
field's knob and a test; no rework to the other six.

## One related nuance, flagged not asked

The old roof-dormer let the ridge **slide off-center within the blue box**
(the `box_left_in`/`box_right_in` pair, which phase 1 does carry). As a
furnishing the ridge is the item's own anchor, centered; knob **A** is wired
only as the dialog-opener. Whether A (or a G) should also slide the ridge
within the box is a smaller question than D — I raise it here so it is on the
record, but it needs no field, only a decision, and it does not block.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XVitzXNKQWS64xhKKpacra
