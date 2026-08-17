# 0041 — ruling: the recovery, and what actually survived

**Code reached its context limit before a checkpoint could be taken
(2026‑08‑17).** [`0023`](0023-ruling.md) §4 predicted this exact case and called
it *"a recovery, not a checkpoint."* **This is the first time it has happened,
so what survived is recorded rather than described.**

---

## 1. THE STATE, MEASURED — not a wreck

| | |
|---|---|
| **HEAD** | `a416222` on `main`, 12:41 — unchanged; nothing was committed after it |
| **Gate** | **GREEN**, `collected=734`, written 13:12:53 |
| **Uncommitted, and it is real work** | `floorplanner/export/fp2dxf.py` (**554 lines**), `floorplanner/export/__init__.py`, plus edits to `SESSION_SNAPSHOT.md` (+26) and `handoff/README.md` (+2) |
| **Not yet done** | the zip is still packed; no `sample/`, no `docs/evidence/chief-export/` |

**The gate being GREEN is the whole difference between this and the bad case.**
[`0023`](0023-ruling.md) §4's warning was that a **red** tree cannot commit
anything, including the report explaining why. **That did not happen.**

## 2. WHAT CODE DECIDED, LEGIBLE FROM THE ARTIFACT ALONE

**[`0038`](0038-ruling.md) §5 left the placement open** — repo root beside
`fp_macro.py`, or a package, with the
[D39](../defects/0039-viewer-is-a-top-level-package-and.md) grain noted against
the root. **Code took the package**, and wrote its reasoning into
`floorplanner/export/__init__.py` rather than leaving it in a lost conversation:

> *Nothing in here imports `floorplanner` … a module here reads a saved v5
> document directly and must stay usable from a plain `python -m` invocation or
> a test, without dragging in the Qt-heavy editor package … Where a fact
> genuinely belongs to the rest of the app (wall thickness, the schema), the
> module loads the ONE file that owns it BY PATH (`importlib`), exactly as
> `floorplanner/viewer/fp3d.py` already does … never `import
> floorplanner.design…`*

**That is [`0038`](0038-ruling.md) §3's ruling, restated by the implementer in
the file that has to obey it.** The placement decision is accepted, and the
by-path rule is where it will actually be read.

**And 470 → 554 lines says the integration was under way, not merely unpacked.**
**The dead `stem` variable I flagged as a possible gate blocker is gone.**

> ### THE ARTIFACT CARRIED THE REASONING, SO THE LOST CONTEXT COST ALMOST NOTHING.
>
> **That is not luck — it is what writing the "why" into the file instead of the
> conversation buys**, and it is the same property that makes the reviewer
> disposable. **Worth naming, because the next recovery will be judged against
> it.**

## 3. WHAT THE RECOVERY OWES — and it is one commit, not an investigation

1. **Re-run the gate.** `SESSION_SNAPSHOT.md` and `handoff/README.md` are tracked
   and modified; if either is newer than 13:12:53 the result is stale and the
   commit hook refuses. **Re-run, do not assume.**
2. **Commit what is there, named as a RECOVERY** — not as a checkpoint, because
   no checkpoint was taken and the record should not imply one was.
3. **A short report saying what is done and what is NOT**, from `git status` and
   the diff rather than from memory: the package placed, the by-path decision
   taken, the zip still packed, the sample and screenshots not yet placed, and
   whether the thickness rewiring, the three hygiene fixes and the golden test
   are begun.

**No re-derivation of intent is needed** — [`0038`](0038-ruling.md) is on disk
and unchanged, and §2 above shows the artifact agrees with it.

## 4. THE LESSON IS THE ONE [`0023`](0023-ruling.md) ALREADY STATED, NOW WITH A RECEIPT

> *`checkpoint` is said EARLY, at a green gate, never at the limit.*

**94% was already too late to act on**, and the only reason this is a one-commit
recovery rather than a lost session is that **the gate happened to be green when
the limit arrived.** That is not a plan.

**[`0023`](0023-ruling.md) §5's standing obligation is restated because it was
not met:** Code watches `/context`, Patrick cannot. **Code says so itself at
roughly 75% and checkpoints at the next green gate, unprompted** — rather than
waiting to be asked at 94%.

## 5. TIER

**GREEN** — a recovery commit and a state report. **Nothing merges, nothing
changes behaviour.**

**Then [`0040`](0040-ruling.md)**, whose §4 remedial cherry-pick is still owed
and still gates the next number.
