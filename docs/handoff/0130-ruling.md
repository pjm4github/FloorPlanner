# 0130 — ruling: family exclusivity — each lane dimensions only its own walls

**Patrick, 2026‑08‑31, amending [`0129`](0129-ruling.md) §3:**

> *"Do not project any callouts from 45/135 walls to the orthogonal lanes and
> do not project any callouts of the orthogonal walls to the 45/135 lanes."*

**Adopted, and it supersedes one bullet of mine:**
[`0119`](0119-ruling.md) §2 explicitly kept angled endpoints in the X/Y rows as
*"corner stations"* — **withdrawn.** That bullet is where the clutter he is
seeing comes from: every 45° corner mints an X and a Y station the orthogonal
rows have no business measuring.

---

## 1. THE RULE

**A wall contributes stations only to the row family matching its own angle.**
Orthogonal walls → the X/Y rows only. Each angled family → its own lane only.
Classification by the wall's angle against the same 1° near-axis boundary
already in use; a shared corner between an orthogonal and a 45° wall appears
in **both** families — once from each wall, at the same point — which is
correct, not a duplicate: the corner genuinely bounds both.

## 2. THE CONSEQUENCE THAT MUST BE RULED WITH IT — or the telescoping test gets quietly weakened

**With angled endpoints out of row 1, row 1 can no longer sum to a row-2
overall spanning the whole plan bbox** — the bbox includes the 45° wing that
row 1 no longer measures.

> **RULED: each family telescopes within itself.** The X/Y rows' overall (row 2)
> spans the **orthogonal family's own extent**; each angled lane's overall spans
> **its family's extent**. The corpus receipt is re-pointed at that invariant —
> **deliberately, here — rather than discovered failing and patched around.**

If a whole-plan overall is ever wanted back, it is a separate single
dimension, not row 2's job. Not ordered.

## 3. DISPOSITION

**Folds into [`0129`](0129-ruling.md) §3's cleanup branch as item (e)** — same
branch, same check, one more glance:

> **No 45° corner appears in the bottom or left rows; no orthogonal corner
> appears in a lane; each row's segments sum to its own family's overall.**

**Receipts on `wiscaway2026-08-30R1.json`:** an angled-wing vertex absent from
the X/Y station lists (RED today, by [`0119`](0119-ruling.md) §2's own bullet);
an orthogonal vertex absent from every lane; the per-family telescoping
assertion corpus-wide.

**Everything else in [`0129`](0129-ruling.md) stands — including the merge of
PR #45 and the three ghost-branch deletions, which do not wait on this.**
