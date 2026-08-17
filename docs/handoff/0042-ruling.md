# 0042 — ruling: the CI is not overkill; ONE check in it is in the wrong lane

**Patrick, 2026‑08‑17:** *"Why does the CI have so many problems passing? The
code itself seems to run fine even as the CI is failing. Is the CI test overkill
in my case?"*

---

## 1. EVERY CI FAILURE THIS PROJECT HAS EVER RECORDED — the census

| record | what failed | was it the code? |
|---|---|---|
| [D27](../defects/0027-ci-never-runs-the-deep-gate-and.md) | CI **did not run** the deep gate, and ran Linux only | **No — CI was too WEAK.** Filed to make it stricter |
| [D78](../defects/0078-the-snapshot-staleness-gate-cannot-pass-on.md) | `Docs-Snapshot`, four commits to settle: filed → `HEAD^2` fix → blind under shallow fetch → the merge itself exposed a third case | **No — the check failed on itself** |

**That is the complete list.** `2630018` → `d0c29b1` → `a40c715` → `168190f` →
`db09acf`.

> ### THE CODE HAS NEVER FAILED CI. ONE CHECK HAS, REPEATEDLY, AND IT IS THE SAME ONE EVERY TIME.
>
> **Patrick's observation — "the code runs fine even as CI is failing" — is not a
> reason to distrust the CI. It is the diagnosis.** A red lane whose subject is
> not the code is telling you which lane to look at.

## 2. WHY THAT ONE CHECK AND NOTHING ELSE — it is the only one coupled to git topology

| check | what it reads | environment-sensitive? |
|---|---|---|
| `ruff check .` | source text | no |
| `pytest` ×3 (3.10, 3.13, Windows) | running code | no |
| deep invariants | running code | no |
| `defects_index --check` | a generated file vs its source | no |
| **`Docs-Snapshot`** | **`HEAD` and `HEAD~1`** | **YES** |

**`HEAD~1` means four different things in four places:** a real parent locally; a
**merge-ref's first parent — which is `main`** — on a `pull_request`; a merge
commit's parent on push-to-`main`; and **nothing at all under a shallow fetch**,
which was D78's second round.

**Every other check is a pure function of the tree.** `Docs-Snapshot` is a
function of **git history shape**, and CI reshapes history by design.

## 3. SO THE ANSWER IS: NOT OVERKILL — MISCATEGORISED

**Six jobs for a PyQt app with a JSON schema and fifteen invariants is
proportionate**, and the record proves it rather than assuming it:
**[D27](../defects/0027-ci-never-runs-the-deep-gate-and.md) was filed because CI
was too little** — the deep invariant set was unguarded and Windows was untested.
**Nothing here is testing the code twice.**

**But `Docs-Snapshot` is a LOCAL PRE-COMMIT CONCERN wearing a CI job's clothes.**

> **THE COMMIT HOOK ALREADY MAKES THE FAULT UNLANDABLE.** `verify_gate.py`
> refuses any commit unless `.gate-result.json` reads GREEN **and is newer than
> every tracked file** — and the full-mode gate that writes it includes the
> snapshot check. **A stale marker cannot be committed in the first place.**
>
> **So the CI copy prevents nothing the hook has not already prevented.** Its only
> residual value is catching a **bypassed** hook — `--no-verify`, or a commit made
> from a machine without it. **That is real but small, and it is not worth what
> four rounds of D78 cost.**

## 4. THE RULING — move it, do not delete it

**`Docs-Snapshot` runs on PUSH-TO-`main` and in the LOCAL FULL GATE. It comes out
of the `pull_request` lane.**

* **The local hook remains the primary enforcement** — it is where the fault is
  actually prevented, and it is unchanged.
* **Push-to-`main` keeps the bypass backstop**, on a real linear checkout where
  `HEAD~1` means what the check assumes.
* **The PR lane stops asking a question whose premise a merge-ref cannot
  satisfy.**

**THIS PARTLY REVERSES [`0027`](0027-ruling.md) §3, AND I SHOULD SAY SO PLAINLY.**
I refused option (c) — *scope it to push-to-main* — on the grounds that moving
detection after the merge leaves `main` red at rest. **That objection was sound
about DETECTION and I had the wrong model of where detection happens:** the hook
detects it **before the commit exists**, so nothing can reach `main` stale unless
the hook was bypassed. **`main` is not left unguarded; it is guarded a step
earlier than I was accounting for.**

**What survives from [`0027`](0027-ruling.md) unchanged:** the `HEAD^2` fix was
still correct for the push-to-`main` merge-commit case, and **the positive
control §4 demanded — a deliberately stale marker must still go RED — still
applies wherever the check runs.** Do not lose it in the move.

## 5. THE GENERAL FORM, because it is the part that outlives this

> ### A CHECK WHOSE SUBJECT IS THE ENVIRONMENT BELONGS WHERE THE ENVIRONMENT IS FIXED.
>
> Tests read the tree and are portable. **A check that reads git topology, a
> clock, a path or a machine is portable only where those are the same** — and CI
> exists precisely to vary them.
>
> **Ask of any check that fails in CI but not locally: is the code wrong, or is
> the check's PREMISE absent here?** D78 was four rounds of the second, each
> answered by repairing the check for one more environment. **Moving it costs
> one commit and closes the class.**

## 6. TIER

**GREEN** — a CI workflow change, no new semantics.

**And it is worth doing soon rather than eventually**: it is currently the only
thing making a green PR expensive, which is the tax that makes people stop
opening them.
