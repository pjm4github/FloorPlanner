---
# permanent key, independent of GitHub
id: 49
title: "I11 - overlapping placed rooms, the corruption this migration was STARTED to fix - is reported"

# maps directly onto GitHub Issues fields
state: open
state_reason: null
labels:
  - type:gap
  - area:schema
milestone: null

# ours; becomes body prose after migration
opened: 2026-08-05
closed: null
closed_by: null
rank: 49
related: []
state_source: row
github_issue: null
---

# D49 — I11 - overlapping placed rooms, the corruption this migration was STARTED to fix - is reported

## Record

> **Moved verbatim** from the register (`docs/CODE_REVIEW_v2.md`, the row at its
> line 114) on 2026-08-06 — not reworded, not split, not
> reformatted. The register wrote each row as one continuous argument in which
> symptom, mechanism, evidence, ruling and receipt are interleaved, so dividing
> it into sections would have meant interpreting it. See
> [`README.md`](README.md) for the section shape new records take.

**I11 — overlapping placed rooms, the corruption this migration was STARTED to fix — is reported nowhere in the shipped app.** Filed 2026‑08‑05 at the fragment ruling. Two facts compose into a hole neither has on its own: I11 is **deep-only** (`validate.py:248`, with I5b `:156` and I14 `:302`), so shadow mode's always-on twelve never runs it while editing; and shadow mode is **off by default** — `verify()` returns `None` unless `verify_enabled()` (`design/verify.py:210`) and `app.py:47` sets the env var only for `--verify-design`. So the save refusal that the deep set was supposed to backstop **does not happen on a default launch**. Measured on one corrupt scene, three ways: `FP_VERIFY_DESIGN` unset → **the save WROTE the file** carrying I5b ×1 and I11 ×3; `=1` → refused; `=deep` → refused. This is the invariant that caught the real `planc1.json` corruption (the 591 sf master bath overlapping two other rooms, §2 F5), and in the shipped product nothing would have caught it. **Proposed fix, to be scoped separately: run the DEEP set at document BOUNDARIES — load and save — regardless of shadow mode, and keep the cheap twelve for editing.** The cost argument that produced the split (P1.2: an O(n²) sweep per edit makes the app unusable) does not apply at a boundary crossed once per file; the plan's own words for the deep three are already "run on save, load and import — paid once, where the stakes are highest", which is a description of a design that was never wired to the default path. **It also repairs ruling 2a's premise**, which assumed a save refusal that does not happen.

## Site

`design/verify.py` (`verify_enabled` gating), `planio.py:549,606` (the save path), `app.py:47`

## Milestone

**unassigned — scope separately, before Phase 5**
