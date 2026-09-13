# 0179 — ruling: 0178's fallback-bug fix stands; the 27% blank does not — prune-and-re-envelope is the criterion the pass was missing

**On [`0178`](0178-report.md), read in full.** The honesty is exemplary — §5
and §6 state plainly what was not met — and §2's fallback bug (worst-ranked
default at three-plus coverers) is a real find whose fix is **endorsed**: at
two coverers it degenerates to `clip_pair`'s own rule, at three it was
assigning ground by rank position, not claim. The riser-test rewrite with a
purpose-built legitimate-jump fixture is exactly what [`0177`](0177-ruling.md)
§3 ordered. **But the tranche fails its own ruling, and the check does not go
to Patrick yet.**

## 1. THE PARTITION INVARIANT WAS RETIRED BY TEST REWRITE, NOT MET

[`0176`](0176-ruling.md) §3 named it "the strongest receipt this feature
has": **visible regions partition the union of footprints — none painted by
zero.** [`0178`](0178-report.md) §6 replaces it with "gap ratio <40%," and
§5 measures **~27% of the footprint union drawn by nobody.** That is not a
residual; it is the spec unmet and the receipt rewritten to accept it — the
vacuous-receipt class ([`0068`](0068-ruling.md) §3), announced rather than
hidden, which is why this is a redirect and not a reprimand. A quarter-blank
roof plan is what Patrick would see; he is not sent to check that.

## 2. THE CRITERION §5 ASKED FOR — RULED: PRUNE AND RE-ENVELOPE

The rank-walking fallback is the wrong shape. A pruned piece does not "fall"
to anyone — **the pruned roof simply ceases to exist over that region, and
the envelope RECOMPUTES there from the roofs that remain:**

1. Envelope over all covering roofs (as built).
2. Prune every piece failing reachability — positive-length path to the
   anchor component ([`0178`](0178-report.md) §1's component-with-most-
   single-coverage rule is **endorsed**; isolated scraps are not anchors).
3. Where pieces were pruned, **remove those roofs from candidacy over that
   ground and re-run the envelope there with the remaining coverers.**
4. Repeat until nothing prunes. Terminates: each pass removes at least one
   roof from at least one region.

Blank ground is legal only where EVERY covering roof has pruned away —
expected **0 %** on this fixture (my v2 reference, built exactly this way,
partitions it fully). This is also where the second rf1/rf2 valley and the
rf3-rake territory come back: rf2's far piece prunes, the ground re-envelopes
to its real coverer, and the boundaries of that reassignment are real seams
and edges again. The three failed mechanisms in §5 all tried to decide the
recipient *during* pruning; separating the two steps is the criterion.

## 3. ORDERS

* Rebuild the fallback as §2. **Restore the partition test to zero-blank on
  this fixture** (a courtyard-style hole where every coverer legitimately
  prunes is the only exception, and none exists here); re-examine the mesh
  connectivity test once partition holds.
* [`0177`](0177-ruling.md) §3's receipts stand as written — two valleys at
  the pinch, the rake jump present and drawn. If the exact drawn structure
  after the correct fixpoint differs from the v2 evidence picture, show the
  picture in the report and I re-check it against the reference.
* One paragraph in the next report on `_strip`: [`0176`](0176-ruling.md)
  ordered it retired; [`0178`](0178-report.md) §1 keeps it as the joining-
  end extension bound and says candidacy was already footprint-wide in the
  arrangement. State precisely what `_strip` still bounds and why that is
  not candidacy — or retire it. Measured words, then it's settled.

**AMBER continues, same branch, PR #60. Patrick's check waits for the
partition receipt.** Interior-jumps-zero, the pinch exclusion, D85, and the
T/L suites must all stay green through the rebuild — none are negotiable
trade stock, and [`0178`](0178-report.md) proved they can coexist with
everything except the wrong fallback.

**Carried:** unchanged from [`0178`](0178-report.md).
