# 0273 — report: the gallery regenerated with four new frames — the roofs, the End-On dialog, the annotations, the 3D view

**Code, 2026‑10‑13.** His words after [`0272`](0272-report.md):

> *"regenerate the gallery with roofs, annotations and 3D frames"*

Built on `gallery-frames`, ONE commit on `main`'s tip, AMBER for his look
at the frames.

## 1. WHAT THE GENERATOR DOES NOW

`docs/make_gallery.py` builds its one demo plan as before and takes the
sixteen frames it took, then:

* **Roofs on the demo house** (`build_roofs`): a **gable** over the main
  block (eaves 96″, ridge 156″, 12″ overhang), a **hip** over the garage
  with a 60″ run per end, a **shed** over the sunroom (the ridge on the
  house wall as its high edge, the one plane falling south — 0262's own
  recipe), and a **dormer** on the main roof's south slope built by the
  `DORMER` macro command, which does what the Dormer tool does with no
  dialog. The roofs are added AFTER the classic frames, so the overview
  and the hero screenshot keep the plan they showed.
* **Frame 17, roofs**: the house with *Roof ▸ Edit roof* on, the main roof
  selected (its grips), the dormer, the hip, the shed, the clip traces.
* **Frame 18, the End-On dialog**: `RoofEndOnDialog` on the main roof —
  the section it draws and every field.
* **Frame 19, annotations**: a text, two measures (one selected, its four
  knobs), a leader, the datum, and the item callouts on — W, V, O, R, F
  labels in the one font and colour. The bedroom's own dimension arrows
  are off for this frame so they do not compete.
* **Frame 20, the 3D view**: the demo plan saved to a temporary file and
  rendered by `fp3dq --shot` in its own process on the **windows**
  platform (Qt Quick 3D needs a real GPU surface; the offscreen platform
  the rest of the script runs on cannot give one), a camera chosen so the
  three roofs and the dormer read. The script fails loudly if the shot is
  not written.
* **The item callouts** (on by default since 0264) are switched off for
  the classic frames, so they look as they did, and on for frame 19.

`docs/gallery/README.md` gains the four sections (and its furnishing count
says 96, the catalog's number, not the 70 it said). The classic PNGs are
re-rendered by the same run — the toolbar has three more buttons since
they were last taken.

## 2. A WRONG TURN, RECORDED

The first run's shed was given its ridge 12″ off the house wall with the
span on the wrong side (`span_in=[0, 240]`): the 3D builder drew nothing
for it. The porch roofs of [`0262`](0262-report.md) say how a shed is
written — the ridge IS the high edge, on the wall, the span to its left —
and the frame was retaken.

## 3. RECEIPT

The twenty frames and the hero screenshot regenerated; the four new ones
looked at. The gallery is generated, not tested: `--quick` and the gate
are GREEN as before (the generator is not under the suite).

## 4. WHAT HAPPENS NEXT

His look at the frames. Named: DXF export of annotations; his backlog
(0248's items 8 and 9).

**Carried:** unchanged from [`0272`](0272-report.md).
