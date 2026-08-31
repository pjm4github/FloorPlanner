# 0129 — ruling: PR #45 passes and merges; the four branches are one live and three ghosts; the cleanup tranche specified

**Patrick, 2026‑08‑31:** *"The dimensions look OK on the '#45 on angled
dimension lanes' version … make PR #45 green - I checked the functionality and
we're ready to move on to the pure cleanup. I see there are 4 different
branches … Lets pull these all into mainline."*

*(Numbering note: my `0124`/`0125` rulings landed as `0127`/`0128` after a
number race with Code's own reports — flagged in the files themselves, per
[`0044`](0044-ruling.md). The hook worked; nothing to fix.)*

---

## 1. PR #45 — CHECK PASSED, MERGE AUTHORISED

The AMBER condition is discharged in his words above. **Merge
`angled-dimension-lanes`** (0 behind, 1 own commit): bring `main` in if
anything lands first, gate, merge on green CI, **delete the branch.**

## 2. THE FOUR BRANCHES — measured, three are already in mainline

| branch | own commits | state |
|---|---:|---|
| `angled-dimension-lanes` | 1 | **live — §1 merges it** |
| `dim-row-along-refactor` | 0 | ghost — fully merged, ref never deleted |
| `export-menu-pdf` | 0 | ghost |
| `pdf-dimension-and-door-fix` | 0 | ghost |

**Nothing needs pulling — three refs hold no commits `main` lacks. Delete all
three, local and remote.** The delete-after-merge rule lapsed three times
running; **Code adds the branch deletion to the merge step it already
performs**, so this stops recurring by procedure rather than memory.

## 3. THE CLEANUP TRANCHE — four items, his words, one branch

**(a) Grid-aware station filtering** — *"drop the ones that are fractions of an
inch or not close to the grid"* when callouts crowd:

* A station is **on-grid** if within tolerance of a multiple of the document's
  own `wall_snap_in`. **Measured: `fp2pdf` never reads the document's
  `settings` block — it must start**, defaulting 6.0 when absent. No hardcoded 6.
* When two stations sit **closer than the grid step**, the **off-grid one is
  dropped; a grid station is never dropped.** All-off-grid crowds keep their
  existing cluster mean. Applies to all three row kinds.
* **Telescoping still holds on the retained set** (differences of retained
  stations) — the census re-runs green, corpus-wide.

**(b) Lane labels in feet-and-inches** — the 45°/135° lanes label with the same
`ftin` form the orthogonal rows use. One format on the sheet.

**(c) Centerline, stated and true** — dimensions call out to **wall
centerlines**. Stations already come from vertex (centerline) coordinates, so
the geometry is mostly right and the **title block is wrong**: the default
`dim_note` still says *"All dimensions to overall wall faces."* It becomes
**"All dimensions to wall centerlines"** — matching the document's own
`area_basis: centerline` — and any station derived from a face offset is
corrected to centerline. **The old faces doctrine is superseded by its author.**

**(d) Openings** — doors, frames, windows: **already out everywhere**
([`0126`](0126-report.md) §2, built and receipted). Reaffirmed for the record;
no new work. The architect picks up openings — [`0128`](0128-ruling.md) §2's
intent line already governs.

## 4. TIER

§1–2: **GREEN** (merge is authorised; ghost deletion is hygiene).
§3: **AMBER, one branch, one check:**

> **Export Wiscaway once more. Every orthogonal callout lands on the 6″ grid or
> is gone; the 45° lanes read in feet-and-inches; the title block says
> centerlines; and rows still sum to their overalls.**

**Carried:** the `L2.dxf` Chief recount — **still the oldest open line on the
board**, and the same export session could close it.
