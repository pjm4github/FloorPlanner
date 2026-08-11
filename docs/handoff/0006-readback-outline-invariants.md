# 0006 — read-back: the two outline invariants

**Measurement only. Nothing is implemented in `validate.py`, no invariant is
numbered, and no corpus file is touched.** Every figure below was taken by
`docs/evidence/outline_invariants_readback.py` →
`outline-invariants-readback.json`, on `main`.

**The ruling this answers:** outline completeness *gets its own invariant, and
producer 2's second half is reclassified* — not alternatives, because without a
detector "the files were always non-compliant" is an excuse nobody can act on.

**The property, as ruled, stated on the stored document and never as a
difference between representations:**

> **No outline edge passes through a wall endpoint without naming it.** For every
> outline edge from one vertex to the next, no vertex that is a wall endpoint may
> lie strictly between them.

Checkable on a file nobody has loaded — it reads `rooms[*].outline`,
`walls[*].v1/v2` and `vertices[*]` out of the same bytes. No scene, no walk, no
emit.

---

## Q1 — which corpus files fail

| check | files failing | total violations |
|---|---|---:|
| **outline completeness** | **`wiscaway2026-08-09R.json` only** | **2** |
| **simple ring (D41)** | `farmplaceBIGmultifloor`, `planc1.v5`, `planc1TestV5`, **`symmetricP1`**, `wiscaway2026-08-09R` | **7** |

**`symmetricP1` — completeness 0, simple ring 1.** So the clean reference fails
**D41 only**. R-A's premise is confirmed on disk: `symmetricP1` carries a
simple-ring instance and a re-cut with a declared justification is required for
D41 — and **is not required for completeness.**

The two completeness violations, both on the fixture that is already retained
*because* it fails:

```
IOC room r15 edge v81->v79 passes through wall endpoint v80 without naming it
IOC room r19 edge v107->v98 passes through wall endpoint v100 without naming it
```

**Three files are skipped and named rather than dropped silently** —
`planc1.json`, `planc1TestV4.json`, `sample_plan.json` are legacy v4 and
`check()` cannot read them. A sweep that quietly covers fewer files than it
lists is the census-blindness problem in miniature.

---

## Q2 — cost, measured, and it changes the answer

Milliseconds, best-of-5, per plan. `cheap 12` and `deep 15` are the existing
lanes on the same document, so this is a comparison and not an adjective.

| plan | cheap 12 | deep 15 | completeness **naive** | completeness **indexed** |
|---|---:|---:|---:|---:|
| `wiscaway2026-08-09R` | 0.447 | 48.880 | **36.359** | **0.917** |
| `wiscaway2026-08-08` | 0.393 | 20.953 | 26.197 | 0.514 |
| `roundedMultifloor` | 0.387 | 24.149 | 20.270 | 0.629 |
| `planc1.v5` | 0.325 | 25.345 | 12.942 | 0.558 |
| `symmetricP1` | 0.288 | 19.978 | 10.073 | 0.425 |
| *(corpus total)* | — | — | **124.9** | **4.2** |

**Naive, it is deeper than deep** — 36 ms against the whole deep set's 49 ms on
the largest plan. That would have settled the cheap/deep question against a
property of the *loop* rather than of the *question*, so the question was
re-asked of an indexed form: endpoints bucketed into cells, each edge querying
only the cells its bounding box touches.

**Indexed, it is cheap-twelve class** — 0.917 ms against the cheap lane's 0.447
on the largest plan, roughly **2× the entire existing cheap lane and ~50× cheaper
than the deep set.**

> **RECOMMENDATION: the CHEAP TWELVE, on the indexed implementation only.** That
> is the answer D59 needs, since a boundary check can only enforce what is
> affordable at a boundary. **On the naive implementation the honest answer would
> be "deep", and the two must not be confused when this is built.**

**The index is asserted to agree with naive on every plan, and that assertion
earned its keep.** It disagreed on the first run — on the *only* plan with
failures. Cause: a vertex held by three walls appears three times in a plain
endpoint list, so the naive form reported **one violation three times** while the
grid form deduped. **The naive count was wrong, not the index.** The corrected
count is 2, not 3. An index that changes the answer is not an optimisation, and
this one was reporting a real over-count in its sibling.

---

## Q3 — tolerance, declared

**It is NOT `vertex_weld_in`.** 0.6″ is a *coincidence radius* — do two points
name one corner. This is a point-on-**segment** question and needs a
**perpendicular** distance. Sharing the number would merge two questions that
happen to be measured in inches.

**Exact on the lattice, declared tolerance off it** — the same shape as
`rooms._corner_path`, deliberately, so there is one rule for *"is this point on
this run"* rather than two. On-lattice triples are decided by an **integer cross
product**, so no tolerance is consulted at all.

Failures at each perpendicular tolerance, whole corpus:

| tol (in) | 0.0 | **0.001** | **0.01** | **0.05** | 0.25 | 0.6 |
|---|---:|---:|---:|---:|---:|---:|
| violations | 1 | **2** | **2** | **2** | 3 | 3 |

> **DECLARE 0.05″.** The answer is **flat across three decades** — 0.001 to 0.05
> all give 2 — so the number sits in the middle of a plateau rather than on a
> slope. **0.0 is unusable** (float exactness drops a genuine hit), and **0.25
> pulls in a third case** that is a different question. 0.05 is also one order
> below the 0.6″ coincidence radius, which keeps the two visibly distinct.

---

## Q4 — one pass or two? **TWO.**

| | ms, whole corpus |
|---|---:|
| completeness, indexed | **4.207** |
| simple ring, alone | **0.157** |
| run separately, summed | **4.364** |

**Simple ring costs 3.7% of the check it would share a traversal with.** Merging
can save at most that, and the saving is inside the noise.

**And the corpus argument, which was the real reason to consider it, does not
hold.** The proposal was that if `symmetricP1` failed both, it should fail them
in one commit with one justification. **It fails only D41.** Completeness touches
exactly one file — `wiscaway2026-08-09R`, already a characterised fixture
retained *because* it fails, so it needs no re-cut at all.

> **RECOMMENDATION: land them separately.** They have different costs, different
> corpus consequences, and different blockers. Combining them would couple an
> AMBER corpus change (`symmetricP1`'s re-cut, D41's) to a check that does not
> need one — and a joint commit would make the `symmetricP1` justification cover
> two things when it only argues for one.

**Caveat, stated because the number is in the evidence file:** the combined-pass
timing (296 ms) was written against the *unindexed* inner loop and is **not**
comparable to 4.2 ms. It is left labelled rather than quietly re-timed, because
Q4's answer does not rest on it.

---

## The instrument-boundary entry this earns

Recorded here for the table in `WORKING_AGREEMENT.md`, in the ruling's own terms:

| instrument | why it cannot see outline completeness |
|---|---|
| **I14** | compares **wall ends to WALLS**. A room outline is outside its subject entirely. **Wrong subject.** |
| **I5** | cannot fail on a saved document, because `bridge._walk` emits one outline edge per wall **by construction** — the violation is repaired in the act of asking. **A question that destroys its own evidence.** |

**An instrument that repairs what it measures reports health it manufactured.**
That is the sharper of the two and has no precedent in the existing table: every
other entry is *"this answers less than its name suggests"*. This one answers a
question it has already made true.

---

## What is still owed before implementation

1. **The invariant numbers.** I1–I14 plus I5b are taken. Proposed: **I15** simple
   ring (D41, ruled first at R-A) and **I16** outline completeness. Numbering is
   the reviewer's, not Code's.
2. **The tier.** Both are AMBER by the charter — a file that validated now fails.
3. **D41's corpus re-cut**, with its justification, per R-A. Completeness needs
   none.
4. **Whether completeness runs on the SAVE path at all**, given D59. It can only
   ever fire on a document the app is *reading*, since the app's own writer
   cannot produce a violation — which makes it a **load-time** check by nature,
   not a save-time one. That is a design question, not a measurement, and it is
   not answered here.
