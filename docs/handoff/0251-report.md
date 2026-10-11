# 0251 — report: PR #82 merged on his word — the `shed` roof form, a shed's ends never joined, a dormer's generated side or face yielding to a house wall; 0248's plans A and C closed

**Landed:** PR #82 · c93c392 · 2026-10-11 · AMBER · checked by Patrick on the house model's iterations 6–9: "The dormers and roofs look right"

**Code, 2026‑10‑11.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0249`](0249-report.md) and [`0250`](0250-report.md) put 0248 §3's
plans A and C to him on `roof-shed-form`, one commit, re-made as the
house model's iterations found more. His word:

> *"The dormers and roofs look right, land #82"*

Done as said: the branch landed on `main` at **`c93c392`**,
fast-forward; [PR #82](https://github.com/pjm4github/FloorPlanner/pull/82)
MERGED; the branch deleted, local and remote. **0248 §3's A and C are
closed.** No defect record was opened for either; the three reports
carry their history.

## 1. WHAT LANDED, in one place

* **Plan A — the `shed` roof form** ([`0249`](0249-report.md) §0): a
  roof record's `form` is `gable` (default, omitted) or `shed` — one
  plane down the left side, the right span and overhang 0, legal in the
  schema only on a shed; the item clamps, the End-On dialog has a Form
  row, the clip twin carries it, the 3D builder skips the empty plane,
  gives a shed dormer a side at both ends and puts a hipped shed's
  ridge-line corner on the hip plane.
* **A shed's ends are never joined** ([`0250`](0250-report.md) §1):
  found on the house model, a shed dormer's joined ends ran its plane
  sideways across the host and the fixed point pruned the phantom to
  blank ground, taking the host's front strip; one `continue` in the
  joining loop.
* **Plan C — the generated side or face yields to a house wall**
  ([`0249`](0249-report.md) §1): a piece inside a wall's body and along
  it is skipped; the wall climbs with its own openings.
* `tests/test_roof_shed_form.py`, 12.

## 2. THE HOUSE MODEL, where his check was made

`fixtures/incoming/house_cutout.json` is iteration 9 — from his
first-floor plan, three roof blocks at one 45° pitch, the wings lower
by their eaves, the shed dormer's top on the line between the two
gable peaks ([`0250`](0250-report.md) §0 and the log in
`house_cutout_work/STATUS.md`, iterations 7–9). Still in `incoming/`,
uncommitted; the generator regenerates it. His to keep or promote.

## 3. STILL OPEN FROM 0248 — his to order

B (openings on a dormer record), D (the equal-height ridge meeting in
the clip; two more ties met on the house model, each tucked an inch),
E (posts and the porch floor). And 0248 §2 item 6 met concretely: a
124″-wide wing cannot carry a hip whose run is the mean of the spans.

## 4. `fixtures/incoming/`, with ages

* `house_cutout_transparent.png`, `house_cutout_1stfloor.png` — his own,
  2026‑10‑11.
* `house_cutout.json` (iteration 9), `house_cutout_work/` — mine,
  2026‑10‑11.
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 5. WHAT HAPPENS NEXT

His word on §3, or the next design. Behind it: the compose cost
([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0250`](0250-report.md).
