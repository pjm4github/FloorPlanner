# 0265 — report: his word on the callouts — the SESSION LABELS, always (W7, V12), adopted from the file's ids when a plan opens so the two match; the Malformed-design report translated to them; folded into PR #87's one commit; AMBER

**Code, 2026‑10‑12.** No merge has happened since
[`0264`](0264-report.md). His word, on 0264's "document ids" reading of
his review:

> *"I want a reference that follows whats on the screen. When the file
> opens I assume the FILE IDs and the SESSION LABELs match. I want to
> have them shown on screen so that when the user clicks on the "zoom"
> button the user can see them. Once the initial dialog box is closed
> then just show the session label. So I want W7/V12 specifically. If
> they dont match then just reference the SESSION LABELS in teh opening
> dialog box. I always want the SESSION LABELS shown."*

Built and folded into `annotations-measure`'s one commit (amended,
force-pushed); PR #87 stands, AMBER. The checkout is on it.

## 0. WHAT CHANGED FROM 0264

0264 read "the Item Names (IDs) ... in the dialog box" as the document's
ids and drew those. His word is the SESSION LABELS — `W7`, `V12`, what
the wall dialog showed all along — so:

* **The callouts write the session label, always** (`callout_text`:
  `session_label(item)`, plus the name where set). Every live item has
  one now: walls and corners had theirs (`W7`, `V12`); openings (`O3`),
  rooms (`R2`), furnishings (`F4`) and roofs (`RF1`) gain a `uid`, minted
  on first read from one mint, `floorplanner/labels.py`.
* **A plan opens with the file's ids AS the labels** (`labels.adopt`:
  `w7` is `W7`, `rf1` is `RF1`), so the file's ids and the session's
  labels match, as he assumes; the counters are kept past every adopted
  number, so an item added later never collides. An id without that
  shape (another tool's `wall_3`) gets a fresh label.
* **The Malformed-design report says the labels.** Its rows are
  translated from the validator's document ids to the session labels
  of the things they name (`_session_labels_of` the scene, `doc_id` →
  `uid`); the validator's own text rides as the row's data, so the zoom
  still resolves the file's ids. Where an id has no label (not on the
  scene) the row keeps it.
* **While that report is open,** a callout whose label differs from the
  file's id shows both, `W77 (w7)`, so the zoom lands on something the
  screen also says; once the report closes, the label alone. (On a
  freshly opened plan the two match and nothing extra is shown.)
* **The wall dialog's Id row** says the label, the file's id beside it
  only when they differ; a corner's placeholder is its label.

The document ids are still stamped (a load, the settle's walk) — that is
what the translation and the dialog's "when they differ" read — but
nothing draws them on their own any more.

## 1. TESTS

`tests/test_annotations.py` (18): the callout is the session label in
the ink, the file's id beside it only while the report is open and the
two differ; a load adopts the file's ids as the labels for walls,
corners and openings, a fresh wall does not collide, another tool's id
gets a fresh label; the report's rows say the labels while its data
keeps the validator's text and the zoom resolves; the layer is on when a
plan opens. `--quick` passed; the full gate GREEN on the amended commit.

## 2. WHAT HAPPENS NEXT

His check of PR #87.

**Carried:** unchanged from [`0264`](0264-report.md).
