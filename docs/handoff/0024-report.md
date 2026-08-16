# 0024 — report: 0022's four remedies, built

**Per [`0022-ruling.md`](0022-ruling.md), on [`0021-report.md`](0021-report.md).**
Same plan and items as 0021 — [`../../fixtures/enclosure-form-check.json`](../../fixtures/enclosure-form-check.json),
`walk_in_shower` / `sauna` / `whirlpool` — nothing new added to it.

---

## 1. §2 — THE FOURTH MEMBER LANDED

*"A control proves the question it was built to answer, and no more"* is now
in [`../WORKING_AGREEMENT.md`](../WORKING_AGREEMENT.md), beside the
positive-control family, quoted from 0022 verbatim as instructed. Cites
`0018-ruling.md` §2 by link for the third member rather than re-deriving its
text into this file — that record already states it, and a second copy is the
exact thing this project has ruled against repeatedly.

## 2. §3 — ROW 1 HAS ITS EVIDENCE RENDER

**[`../evidence/enclosure-bodies-omitted.png`](../evidence/enclosure-bodies-omitted.png)**,
from **[`../evidence/enclosure_bodies_omitted_render.py`](../evidence/enclosure_bodies_omitted_render.py)**
— a new evidence script, not a `fp3d.py` flag. It calls `build_model()`
unmodified on the same fixture, then drops exactly one mesh from the built
`Model` before handing it to `make_view`:

```
meshes before: ['furnishings:glass', 'furnishings:metal', 'furnishings:porcelain',
                'furnishings:stone', 'furnishings:water', 'furnishings:wood']
meshes after (omitted ['furnishings:glass']): ['furnishings:metal', 'furnishings:porcelain',
                'furnishings:stone', 'furnishings:water', 'furnishings:wood']
```

`furnishings:glass` is `walk_in_shower`'s body and, in this three-item
fixture, the *only* glass mesh — omitting it does not touch `sauna` or
`whirlpool`. What is left is exactly what `build_model` built for the other
five parts; nothing invented, per §3's distinction from the refused `--stack`
option.

**With the body gone, the bench (`furnishings:stone`) stands alone on the
grid**, correctly small and correctly floor-standing next to `sauna`'s full
wood body and `whirlpool`'s porcelain/water split. **This is now yours to
read, not mine to certify** — row 1 of the check below is answered by a
render, same as rows 2 and 3, and none of the three needed the fallback
(row 1 carried as explicitly unchecked).

## 3. A FIFTH THING, FOUND WHILE BUILDING THE RENDER — NOT ASKED FOR, FILED SEPARATELY

**[D77](../defects/0077-fp3d-py-shot-reports-success-on-a-failed.md).**
`fp3d.py --shot`'s `grabFramebuffer().save(a.shot)` does not check its own
return value. Under `QT_QPA_PLATFORM=offscreen`, this machine cannot create a
GL context at all (`QOpenGLWidget: Failed to create context`) — `--shot`
still printed `wrote <path>` and wrote nothing, reproducibly, exit 0. The real
(non-offscreen) platform succeeds. **This is the family §2 just landed, one
level down**: not this task's instrument, but the CLI every evidence render
in this project goes through, and it fooled the same "wrote" message the
existing `enclosure_form_measurement.py` docstring already warns about for a
different reason (subprocess nesting). Filed, not fixed — production code,
out of this task's scope. `enclosure_bodies_omitted_render.py` documents the
workaround it needed (do not force `offscreen`; render from a real desktop
session).

## 4. §4 — D76 FILED, CROSS-REFERENCED TO D69

**[D76](../defects/0076-an-opaque-mesh-inside-a-translucent-body-does.md)** —
*"an opaque mesh inside a translucent body does not composite, at any alpha
tested"* — its own record, not a line inside D69. D69 now points back at it
(`related` gained 76; a note against the existing "wanted it" section says a
components panel that hides the body is a workaround for D76, not a fix of
it).

## 5. §8 — HOUSEKEEPING

`channel-commands.svg` linked from [`README.md`](README.md)'s channel-contract
section (**`handoff/README.md`**, the one whose own text names the diagram —
`docs/README.md`, the top-level map, already points at `handoff/README.md`
for the protocol, so the link belongs one level in rather than duplicated at
the top). Committed alongside this report since it was sitting unstaged and a
diagram only on the working tree is not yet on the record.

## 6. §5 and §6 — nothing built, both already ruled

**§5 (materials, accepted)** and **§6 (D75, accepted)** asked for nothing
further — noted here only so this report accounts for every section of
0022, not because either needed action.

## 7. 0023 — ONE LINE, GREEN, TAKEN WHILE HERE

[`0023-ruling.md`](0023-ruling.md) landed on disk mid-task (Patrick's session-
continuity ruling), explicitly ordered behind 0022 and non-blocking. Its one
GREEN action — `CLAUDE.md`'s *"Starting a session"* naming `docs/handoff/` and
the highest-number-is-current rule — is included in this commit rather than
held for its own, since it is documentation-only and the standing autonomy
policy covers GREEN work without asking.

## THE CHECK, AS IT NOW STANDS — every row has a render

| | item | question | render |
|---|---|---|---|
| 1 | `walk_in_shower` | a solid bench, on the floor, that reads as a bench | [`enclosure-bodies-omitted.png`](../evidence/enclosure-bodies-omitted.png) |
| 2 | `sauna` | roof unbroken, the dark notch gone | [`enclosure-form-measurement-after.png`](../evidence/enclosure-form-measurement-after.png) |
| 3 | `whirlpool` | solid top/sides, translucent round pool — and is `porcelain` right? | [`enclosure-form-measurement-after.png`](../evidence/enclosure-form-measurement-after.png) |

**Tier unchanged: AMBER.** Nothing merges without your check.

## Gate

`ruff` clean; `python tools/defects_index.py --validate` — 78 records, front
matter valid (76 → 78: D76 and D77, `INDEX.md` regenerated). Full gate to
follow before commit.
