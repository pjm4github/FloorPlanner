# 0089 — ruling: PR #34's check PASSED — and the grid symptom beside it is expected, measured

**Patrick, 2026‑08‑23, on `cross-floor-align-fix` at `904bd93`:**

> *"didnt have the cross floor align problem (its fixed) but the snap to grid is
> still a problem, this branch must not include the t-junction-grid-snap fix."*

---

## 1. THE MERGE CONDITION IS MET

[`0061`](0061-ruling.md) §6's one question — *"with the second floor hidden,
does a wall you draw still jump to something you cannot see?"* — **answered no.**

**Merge authorised**, after `main` (now carrying #36) is brought in and the
combined tree is re-gated. **Order matters here:** merge **#36 first**, then
bring that `main` into this branch. Delete the branch after.

## 2. HIS DIAGNOSIS IS CORRECT — MEASURED, NOT ASSUMED

```
_grid_snap_t_junction   t-junction-grid-snap : present
                        main                 : absent
                        cross-floor-align-fix: absent
                        wall-label-fixes     : absent

3456186 (D80's fix) is NOT an ancestor of cross-floor-align-fix
```

**The three branches are siblings off `main`, and D80's fix has not reached
`main` yet.** So the grid symptom on this branch is **the absence of a fix that
lives elsewhere**, not a regression and not a second fault. **It disappears when
#36 merges and this branch takes `main` in — which §1 already orders.**

> **Worth recording rather than passing over: the symptom was read correctly
> from the branch alone.** A check that separates *"this branch's fault"* from
> *"a fix this branch does not have"* is the thing
> [`0045`](0045-ruling.md) was written about, and it happened here without a
> ruling having to say it.

## 3. WHAT REMAINS

**Check 3 — `wall-label-fixes` (#35) — is the last of this session.** It touches
`geometry.py`/`mainwindow.py` only: no wall drawing, no snapping, so §2's
absence cannot affect it.

**PR #37 stays out**, per [`0084`](0084-ruling.md) §1.

## 4. TIER

**Merge: GREEN** — the AMBER condition is discharged. **Merge order: #36, then
#34.** Code stays paused until Patrick reports check 3.
