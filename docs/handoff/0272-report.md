# 0272 — report: PR #89 merged on his word, the docs tranche folded in — the leader annotation and the recorder's new tools; the schema at version 6 and the documents brought to this `main`, the command README

**Landed:** PR #89 · 9be6e0b · 2026-10-12 · AMBER · checked by Patrick in the app from the stacked checkout: "the leader and docs look right, fold and land #89"

**Code, 2026‑10‑12.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0270`](0270-report.md) built the leader annotation and the annotation
tools in the macro recorder on `leader-annotation` (PR #89);
[`0271`](0271-report.md) built the documents and the schema at version 6
on `docs-v6`, one commit stacked on it, no PR of its own. His check of
both, from the stacked checkout:

> *"the leader and docs look right, fold and land #89"*

Done as said, the fold of [`0269`](0269-report.md)'s precedent:
`leader-annotation` fast-forwarded to `docs-v6`'s tip (`f8ff5e9`), `main`
(`fe50d56`, 0271 landed) merged in with the snapshot resolved as the
branch's and re-cut, the gate GREEN on the merged tree, pushed; then the
branch landed on `main` at **`9be6e0b`**, fast-forward;
[PR #89](https://github.com/pjm4github/FloorPlanner/pull/89) MERGED; both
branches deleted, local and remote.

## 1. WHAT LANDED, in one place

* **The leader annotation** ([`0270`](0270-report.md)): the N tool, a text
  with an arrow to the thing it names, two knobs, the schema's reserved
  `leader` kind given its item, on the PDF sheet by the Show switch.
* **The macro recorder** ([`0270`](0270-report.md) §2): the letters T, L
  and N in both recorders and the player; `@TEXT`, `@LEADER` and `@DATUM`
  carrying the dialogs' values; the spec, the language doc and the
  example file.
* **The schema at version 6** ([`0271`](0271-report.md) §1):
  `design-schema.v6.json`, every document the app writes version 6, a v5
  file still accepted; six pins moved.
* **The documents** ([`0271`](0271-report.md) §2): `README.md` rewritten
  to this `main`; **`docs/COMMANDS.md`**, every command with an example;
  the docs map, the architecture roster, the model, the sanity check,
  `CLAUDE.md`, `tests/README.md`.

## 2. WHAT HAPPENS NEXT

Nothing open on a branch. Named, not ordered: new gallery frames for the
roofs, the annotations and the 3D view; DXF export of annotations; his
backlog (0248's items 8 and 9).

**Carried:** unchanged from [`0271`](0271-report.md).
