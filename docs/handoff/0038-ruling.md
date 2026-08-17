# 0038 — ruling: the DXF export is ACCEPTED, and its thickness table is D73 arriving again

**Patrick, 2026‑08‑17**, handing over `fp2dxf` — a FloorPlanner v5 → Chief
Architect X17 DXF converter built outside this repository, with a README and a
verified 16-step import workflow.

**Accepted in principle. Four things must be settled before it lands, and the
first one is a ruling this project already made.**

---

## 1. WHAT IS GOOD, MEASURED — because most of it is

**Pure stdlib, confirmed by reading the imports:** `argparse`, `json`, `math`,
`sys`, `dataclasses`, `pathlib`. **No third-party dependency**, which matters —
[D40](../defects/0040-a-missing-optional-dependency-must-degrade-not.md) exists
because an optional dependency crashed rather than degraded.

**470 lines, a clean `convert(doc, outdir, only_levels, thickness_overrides)`
API, and a CLI on top of it** rather than a CLI with a library bolted on.

**The door-symbol finding is a real discovery and it was found the right way:**
both doors arrived as `2640DH` **windows** — correct width, correct station,
wrong class — because Chief classifies by conventional drawing symbol and a bare
gap reads as a window. **That is a differential receipt with judgement attached,
taken against real software.**

**The `FP-` layer prefix is reasoned, not decorative** — it exists because
imported layers case-insensitively merged with Chief's native `Doors`/`Windows`,
which was measured, not feared.

**And the concept quarantine respects FloorPlanner's own semantics**: walls
serving only `category:"concept"` rooms never convert. **That is the export
agreeing with the model rather than reinterpreting it.**

## 2. THE THICKNESS TABLE IS A FOURTH TABLE, AND IT ALREADY DISAGREES

`STD_T` in `floorplanner/design/validate.py` is **the normative table**, settled
at [D73](../defects/0073-two-wall-thickness-tables-disagree-and-one.md). Against
`fp2dxf.DEFAULT_THICKNESS`:

| type | `STD_T` **(normative)** | `fp2dxf` | |
|---|---:|---:|---|
| exterior | **6.0** | **6.5** | ✗ |
| interior | 4.5 | 4.5 | ✓ |
| partition | 3.5 | 3.5 | ✓ |
| railing | **2.0** | **3.0** | ✗ |
| fence | **2.0** | **1.5** | ✗ |
| hedge | **18.0** | **24.0** | ✗ |
| retaining | 8.0 | 8.0 | ✓ |

**Four of seven disagree, before it has landed.**

**D73's ruling was not "sync them":**

> *Deleted rather than synced, **because three tables that are synced become
> three tables that disagree again.***

**This is that sentence coming true on the next table**, and the README predicted
it — *"this table must agree with FloorPlanner's own per-type standards"* — which
is an instruction, and instructions do not hold.

## 3. BUT THE FIX IS NOT "COPY THE RIGHT NUMBERS" — the table is carrying TWO facts

**Read the README's reasoning and the disagreements stop looking like errors:**
6.5 *"pairs with Chief stock Siding-6"*; railing *"widened from 1.5 so Chief's
rail types match"*. **Those are not thicknesses. They are a MAPPING to Chief wall
types.**

> ### ONE COLUMN IS CARRYING "HOW THICK IS THIS WALL" AND "WHICH CHIEF TYPE SHOULD IT BECOME", AND THOSE ARE DIFFERENT FACTS.
>
> **This is the D74 rule exactly** — *a channel committed to representing a real
> quantity cannot also carry identity.* Thickness is already spent representing
> thickness; using it to select a Chief wall type is a second job on one number,
> and the disagreement is the symptom.

**THE RULING, and it dissolves the conflict rather than patching it:**

1. **Thickness comes from `STD_T`, READ AND NOT COPIED.** `fp2dxf` carries no
   thickness values of its own.
2. **The Chief mapping becomes its own table** — `type → Chief wall type name`
   (`exterior → Siding-6`, `interior → Interior-4`, …) — **which is what it
   actually is**, and it can say `Siding-6` without pretending to be 6.5 inches.
3. **`thickness_overrides` stays** as the per-run escape hatch.

**AND THE MECHANISM IS ALREADY SOLVED IN THIS REPO.** `import
floorplanner.design.validate` **drags in the Qt bindings** — measured at P5.2,
recorded in D73's own text — which is why `viewer/fp3d.py` is Qt-free and **loads
that module BY PATH**. **`fp2dxf` does the same thing.** A source-text grep
already guards `fp3d.py` against naming the bindings; the same guard should cover
`fp2dxf`.

> **±1 inch is Chief's matching tolerance** (README §1), and `STD_T`'s exterior
> 6.0 against Siding-6's 6 7/16″ is **0.44″** — inside it. **The normative
> numbers work.** Where one genuinely does not, that is a finding about `STD_T`
> and it goes to the register — **not a second opinion held privately by an
> exporter.**

## 4. THREE LIBRARY-HYGIENE FAULTS — it is a CLI wearing a library's clothes

**Each is small; each is a class this project has already been bitten by.**

**ONE — `raise SystemExit(...)` inside `convert()`.** A library called from a Qt
menu handler must **return or raise a normal exception**, never exit.
[D26](../defects/0026-shadow-mode-kills-the-process-instead-of.md) is *"shadow
mode kills the process instead of reporting"*, and `SESSION_SNAPSHOT` §6 records
that an exception inside a Qt override **presents as a segfault with no
traceback.** **A bad document must be a message in a dialog.**

**TWO — `print()` is the progress channel.** Skipped site levels and the
per-level summary go to **stdout**, which does not exist for a GUI. **The README
asks the menu item to "show a completion summary listing files written and any
warnings" — so that summary must be RETURNED**, not printed. `convert()` already
returns `list[Path]`; it needs to return the warnings and the skips with it.

**THREE — `out.write_text(...)` with no encoding.** On Windows that is **cp1252**,
and **room names are written into the DXF** on `FP-ROOM-LABELS`. A room named
with any non-ASCII character raises `UnicodeEncodeError` **at export time, on
Patrick's machine.** The sample's names are all ASCII, so **the sample cannot
catch this.** Specify the encoding explicitly.

**And one lint note:** `stem = f"{Path(outdir).stem or 'plan'}"` in `convert()` is
assigned and never used. **The gate is `ruff check .` over the whole tree** — the
module clears that bar before anything else is discussed.

## 5. WHERE THINGS GO

| what | where | why |
|---|---|---|
| `fp2dxf.py` | repo root, beside `fp_macro.py` / `fp_extract.py` | matches the existing standalone-tool convention. **Flagged, not ruled:** [D39](../defects/0039-viewer-is-a-top-level-package-and.md) moved `viewer/` *into* the package, so a new top-level module runs against that grain — **Code may argue for `floorplanner/export/`** |
| `sample_design.json`, `L1/L2.dxf`, sidecars | **`fixtures/`** | a characterised known-good input **and its expected output** — never `examples/`, per D51 |
| the 16 screenshots | **`docs/evidence/chief-export/`** | they are the receipt for a workflow validated against software this repo cannot run |
| the README | **split** — see §6 | |

## 6. THE README IS TWO DOCUMENTS AND SHOULD BE SPLIT

**§1 (integration task) is a HANDOFF SPEC — it is spent once the menu item
exists** and should not survive as documentation telling a reader to build
something already built.

**§§2–5 (rationale, the verified Chief workflow, limitations) are USER
DOCUMENTATION** and are the part Patrick asked to keep. **That is the half that
goes to the help docs**, because it tells a person how to get a FloorPlanner plan
into Chief — which no other document does.

**The workflow section is the valuable one and it must not be summarised.** *Show
Import Assistant ON · Create CAD Blocks **OFF** · Polylines **OFF*** are settings
whose wrongness is invisible until CAD-to-Walls silently does nothing. **Those
are traps, and §6 of the snapshot is where this project keeps traps.**

## 7. THE RECEIPT — a golden-file test, and it is nearly free

**The package ships `sample_design.json` AND the `L1.dxf` / `L2.dxf` it
produced.** That is a fail-first pair already sitting in the box:

> **`convert(sample_design.json)` must reproduce the committed DXF and sidecars
> byte for byte.** One test, no new fixtures, and it pins **every** decision in
> §3 — a thickness change, a layer rename, a coordinate flip all turn it red.

**And it makes §3's rewiring safe**: moving to `STD_T` will change the sample
output, **and the regenerated golden files ARE the differential receipt** for
that change. **Regenerate them in the same commit, and state the diff.**

## 8. TIER

**AMBER.** A new menu item, a new output format, and a user-visible completion
dialog. **Patrick's check: export the two-storey plan, import one level into
Chief following §3 of the README, and confirm walls, doors and windows arrive as
their own kinds.**

**Order: behind [`0033`](0033-report.md)'s redraw check and the floor-visibility
work in [`0037`](0037-ruling.md).** It is new capability; the floor bug is
something Patrick hits while working.
