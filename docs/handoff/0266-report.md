# 0266 — report: PR #87 merged on his word — annotations, measurements with their four knobs and a datum, the session-label callouts, the Show menu; the knobs made small and black on his screen before the merge; his annotation-display clean-up next

**Landed:** PR #87 · aacccc2 · 2026-10-12 · AMBER · checked by Patrick in the app: "The measurements look correct ... the knobs look right, land #87"

**Code, 2026‑10‑12.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0263`](0263-report.md) built his four features on
`annotations-measure` (PR #87); [`0264`](0264-report.md) and
[`0265`](0265-report.md) folded his review and his word on the callouts
into its one commit. His check, in two steps:

> *"The measurements look correct, with the exception of the control
> knobs, they obscure the contents. When I zoom in, the red boxes are
> too big. They need to maintain a certain pixel size, sit on the point
> of control, and be solid black controls."*

Measured on his screen: the knobs were 4″ half-squares in scene inches,
a 24-pixel red box over the window they sat on at three pixels an inch.
`DimensionKnob` now draws a solid black square three pixels half-size at
every zoom, centred on its control point, an eight-pixel hit zone;
folded into the commit, pushed. Then:

> *"the knobs look right, land #87, after that lands I want to clean up
> the annotation display a little bit."*

Done as said: the branch landed on `main` at **`aacccc2`**,
fast-forward; [PR #87](https://github.com/pjm4github/FloorPlanner/pull/87)
MERGED; the branch deleted, local and remote.

## 1. WHAT LANDED, in one place

* **Annotations** ([`0263`](0263-report.md) §0.1): the T tool, a text on
  its level, movable, double-click edits.
* **Measurements** ([`0263`](0263-report.md) §0.2, [`0264`](0264-report.md)
  §1): the L tool, each end snapped to an item, one thin line with a
  slash at each callout point, feet-and-inches or inches, the datum;
  four knobs — move a point, Ctrl rotates about the other on the snap,
  Shift frees, the end slides, the label slides — small, black, fixed in
  pixels.
* **Item callouts** ([`0265`](0265-report.md)): the SESSION LABELS,
  always, adopted from the file's ids on open; the Malformed-design
  report translated to them; on when a plan opens.
* **The Show menu** ([`0263`](0263-report.md) §0.4): three switches, the
  units, the colour, the datum; plan settings.
* **The document**: the `annotations` block's first writer and reader,
  five settings keys, `SETTINGS_VERSION` 3.

## 2. WHAT HAPPENS NEXT

His clean-up of the annotation display, on his words to come. Named:
DXF/PDF export of annotations; a leader annotation; his backlog (0248's
items 8 and 9).

**Carried:** unchanged from [`0265`](0265-report.md).
