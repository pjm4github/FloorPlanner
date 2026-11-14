# Parametric Stairs Furnishing — Functional, UI, Geometry, and Validation Specification

**Status:** Implementation specification  
**Target:** Python / PyQt6 residential floor-planning application  
**Primary consumer:** Claude Cowork / implementation agent  
**Date:** 2026-11-14  
**Units in examples:** US customary inches (internal model may use a canonical unit system)

## 1. Objective

Implement a **Stairs** furnishing that can be placed on a floor plan, selected, moved, rotated, serialized, and **double-clicked to open a modal parameter editor**. The editor exposes a minimal set of controlling parameters, calculates all dependent stair dimensions, previews the resulting side elevation and plan footprint, and validates constraints before changes can be accepted.

**Design principle:** Keep geometry, validation, persistence, and presentation separate. Do not store independently editable copies of values that are mathematically derived from the same inputs.

### 1.1 Required user experience

1. User inserts a Stairs furnishing onto a plan, or double-clicks an existing one.
2. The `StairPropertiesDialog` opens modally with a recognizable **architectural side-elevation staircase image** as the dominant visual element.
3. User changes floor association / floor-to-floor rise, tread depth, stair width, or optional riser-count override.
4. Riser height, tread count, total run, pitch, and footprint update immediately.
5. Image annotations update to reflect the current calculation; the graphic must not misrepresent the actual number of risers or geometry.
6. On **OK**, perform a complete validation checkpoint. Block acceptance of hard violations and show actionable diagnostics. For advisory warnings, require explicit acknowledgement before accepting.
7. On **Cancel**, close without changing the furnishing or document.
8. Successful acceptance commits one undoable model transaction and refreshes all relevant plan/elevation/3D views.

## 2. Visual reference and modal layout

### 2.1 Mandatory image reference

Use the **middle staircase image in the prior ChatGPT response** as the intended visual reference: a residential straight stair shown in architectural side elevation with individual risers/treads and an upper landing/floor. The image was shown in an image carousel and **is not embedded in this Markdown file**. The implementation agent must obtain the original image asset from the project/user if available; **do not claim to have imported it** merely from this text. If inaccessible, request the asset or use a clearly labeled generated/vector schematic placeholder pending replacement.

Prefer an original project-owned image or a licensed asset. Do not copy a third-party image into the application without appropriate rights. The final UI should place a dynamic SVG/QGraphics-based dimension overlay above the visual, or reproduce the elevation as a scalable vector drawing using the reference for appearance. **The diagram must remain geometrically correct**, rather than stretching a static photograph to represent new dimensions.

### 2.2 Suggested dialog layout

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Stairway Properties                                               [×]      │
├───────────────────────────────────────┬──────────────────────────────────────┤
│  SIDE ELEVATION / REFERENCE VIEW      │  CONTROLLING PARAMETERS             │
│                                       │  Type: [Straight ▾]                  │
│  [Reference-inspired stair elevation] │  From floor: [Level 1 ▾]            │
│     ↑ Total Rise                      │  To floor:   [Level 2 ▾]            │
│     │     ┌──┐                        │  Total rise: [108.000] in (linked)  │
│     │  ┌──┘  └── upper landing        │  Tread depth: [11.000] in           │
│     └────────────────→ Total Run      │  Stair width: [36.000] in           │
│                                       │  Riser count: [Auto ▾] / [14]       │
│  [Optional plan footprint inset]      │                                      │
│                                       │  CALCULATED                          │
│                                       │  Risers: 14  Treads: 13             │
│                                       │  Riser height: 7.714 in             │
│                                       │  Run: 143.000 in  Pitch: 35.0°      │
│                                       │  Footprint: 143 × 36 in             │
├───────────────────────────────────────┴──────────────────────────────────────┤
│ Validation: [status and detailed findings; expand for explanations]         │
│                                            [Reset] [Cancel] [Apply] [OK]     │
└──────────────────────────────────────────────────────────────────────────────┘
```

The image must remain visible while parameters are edited. Use `QDialog`, `QDoubleSpinBox`, `QSpinBox`, `QComboBox`, `QLabel`, and a custom `QGraphicsView` or SVG widget as appropriate. Set accessible labels, keyboard navigation, tooltips, and sensible tab order. The dialog should resize without clipping controls. Use a consistent unit formatter; display decimal inches and optionally feet/inches.

## 3. Vocabulary and geometric definitions

| Symbol / field | Meaning | Ownership |
|---|---|---|
| `total_rise` (`H`) | Vertical distance between **finished** floor walking surfaces | Derived from associated floor elevations by default; editable only in detached mode |
| `riser_count` (`N`) | Number of vertical increments from lower finished floor to upper finished floor | Automatically solved or user overridden |
| `riser_height` (`h`) | Equal height of each riser: `H/N` | Calculated |
| `tread_depth` (`d`) | Horizontal distance between successive nosing vertical planes, measured along the direction of travel | Input |
| `tread_count` (`T`) | Separate stair treads below the upper landing | Calculated; normally `N - 1` for a straight flight terminating at upper floor |
| `total_run` (`R`) | Horizontal distance between first and last step nosing planes, using the defined stair convention | Calculated: `T*d` for this initial model |
| `stair_width` (`W`) | Nominal width across the stair; distinguish nominal vs code-required clear width | Input |
| `pitch_degrees` (`θ`) | Angle from horizontal of the nosing-to-nosing slope | Calculated: `atan(h/d)` |
| `nosing_projection` | Tread projection beyond riser face; not added to going/tread-depth calculation | Optional future input; validated if implemented |
| `headroom` | Minimum vertical clearance measured above stair nosing line to overhead construction | Geometry-dependent calculated measurement, if surrounding building geometry available |
| `landing` | Horizontal walking surface at stair top/bottom or between flights | Separate geometry; upper finished floor acts as final landing when suitable |

**Important:** For this straight-flight convention, `N` risers correspond to `N - 1` separate treads. Do not accidentally generate `N` treads and extend the footprint by one tread. This convention assumes the upper floor itself provides the top landing. Real construction details may affect framing dimensions; preserve the stated mathematical convention consistently in plan and elevation.

## 4. Minimal controlling inputs

### 4.1 Required for initial straight-stair release

1. `from_floor_id`, `to_floor_id`: links to lower/upper finished-floor elevations; the default `total_rise` is `to.finished_elevation - from.finished_elevation`.
2. `tread_depth`: default **11.0 in**.
3. `stair_width`: default **36.0 in nominal**, subject to local code and actual clear-width calculation.
4. `riser_count_mode`: `auto` (default) or `manual`.
5. `riser_count_override`: positive integer when mode is `manual`.
6. `code_profile_id`: applicable jurisdiction/code-edition configuration, not a fixed assumption embedded in geometry.

When floor associations are unavailable, allow a clearly labeled **Detached rise** mode with editable `total_rise` (default example 108 in). Never silently unlink an existing stair from its floors.

### 4.2 Derived, read-only outputs

`total_rise` when floor-linked; `riser_count` in auto mode; `riser_height`; `tread_count`; `total_run`; `pitch_degrees`; `footprint_length`; `footprint_width`; approximate `2*riser_height + tread_depth` comfort index; validation status.

### 4.3 Advanced controls / future extensions

Stair type (`straight`, `L`, `U`, `switchback`), multiple flights, landings, direction of ascent, left/right turn, nosing projection, open risers, handrail arrangements, stringers, stairwell opening, overhead geometry, fit-to-space solver, and 3D construction details. **Do not claim these are implemented in the initial straight-flight release.**

## 5. Mathematical rules

For positive `H`, `d`, `W`, and selected code-profile maximum riser height `h_max`:

```python
minimum_riser_count = max(1, math.ceil(H / h_max - 1e-10))
N = minimum_riser_count if mode == "auto" else riser_count_override
h = H / N
T = N - 1
R = T * d
theta_degrees = math.degrees(math.atan2(h, d))
comfort_index = 2 * h + d
```

The epsilon above is for floating-point noise near exact boundaries; production code should use a consistent decimal/unit tolerance policy. Validate all inputs are finite and positive. A practical residential flight should have a meaningful number of steps; if `N == 1`, the mathematical result has zero separate treads, so the furnishing must flag this as an unsupported/degenerate stair configuration rather than rendering an ordinary flight.

**Example:** `H=108 in`, `h_max=7.75 in`, `d=11 in`, `W=36 in`: `N=14`, `h=7.7142857 in`, `T=13`, `R=143 in`, `θ≈35.05°`, nominal footprint `143 × 36 in`. The comfort index is approximately `26.43 in`, outside the suggested 24–25 in comfort target; treat this as **advisory**, not as a code failure.

### 5.1 Fit-to-space mode (future)

When user specifies available run `R_available`, enumerate valid integer riser counts and solve feasible tread depths (e.g., `d <= R_available/(N-1)` for `N > 1`), applying all code-profile constraints. Present alternatives and avoid silently reducing tread depth below the minimum. **Do not simultaneously treat total run, tread depth, and riser count as independent unconstrained inputs.**

### 5.2 Landing and floor-opening geometry

The `total_run` above is the **stair flight run**, not necessarily the total required room or stairwell length. Top/bottom landings, door swings, required clearance, floor openings, and headroom may increase space needs. Do not conflate flight footprint with the code-compliant overall stair enclosure.

## 6. Code limits and validation checkpoint

### 6.1 Code-profile concept

Provide an editable/versioned `StairCodeProfile` containing adopted jurisdiction, code edition, amendment metadata, and rules. **The following numbers are common IRC-derived residential defaults for preliminary checking, not a legal determination for every jurisdiction or project.** Verify adopted local code, applicable building type, exceptions, and edition before labeling a design compliant.

| Check | Example default | Severity / behavior |
|---|---:|---|
| Maximum individual riser height | **7.75 in** | HARD ERROR if exceeded |
| Minimum tread depth | **10.0 in** | HARD ERROR if below |
| Minimum nominal stair width | **36.0 in** | HARD ERROR under simplified nominal-width rule; actual clear-width compliance requires handrail/obstruction checks |
| Maximum variation between tallest and shortest riser in one flight | **0.375 in** | HARD ERROR; equal-rise model normally yields zero; construction deviations must be assessed separately |
| Minimum headroom | **80.0 in** | HARD ERROR **only if geometry is available and actual clearance is computed**; otherwise UNKNOWN / NEEDS REVIEW |
| Landing dimensions / presence | Code-profile dependent | HARD ERROR only if fully measurable; otherwise UNKNOWN / NEEDS REVIEW |
| Maximum riser count per flight | **Not a universal IRC numerical limit** | Do not invent one; assess landing, geometry, and applicable rules |
| Minimum riser height | **No universal IRC minimum riser height in this simplified profile** | Do not invent one; reject degenerate/nonphysical designs via separate application rules |
| Maximum tread depth | **No universal IRC maximum tread depth in this simplified profile** | Do not invent one |
| Riser/tread uniformity | Variation limit per adopted code | HARD ERROR where modeled variation exists |
| Nosing / open riser / handrails | Code-profile and configuration dependent | UNKNOWN until relevant options and geometry exist |
| Comfort heuristic `2h+d` | Suggested **24–25 in**, not mandatory | ADVISORY only |
| Stair pitch | Derived; no universal hard pitch bound here | Display only; any local limits belong to code profile |

**Important rule:** Never show a global green **“Code compliant”** status merely because rise, tread depth, and nominal width pass. Instead show **“Basic dimensions pass; additional checks pending”** when headroom, landings, handrails, or surrounding geometry have not been verified.

### 6.2 Severity model

- `ERROR`: invalid input, unsupported geometry, or known hard limit violation. **Blocks OK and Apply**.
- `WARNING`: known risk or unresolved critical context (e.g., missing headroom model, missing local code confirmation). **Can be accepted only after explicit acknowledgement**, with warnings persisted in the model or audit trail.
- `ADVISORY`: comfort, design quality, and informational recommendations. Show in UI; acknowledgement not mandatory unless configured.
- `PASS`: evaluated rule passes.
- `NOT_EVALUATED`: required information unavailable; never masquerades as PASS.

### 6.3 Exact OK / Apply behavior

1. On every edit, perform lightweight geometry calculation and validation; show live status and field-level messages.
2. On **OK** or **Apply**, run **full checkpoint validation** against the candidate draft and its floor/building context.
3. If any `ERROR`: show a detailed summary with rule, actual value, allowed value, and recommended fix. **Do not close or commit**. Focus first invalid control.
4. If `WARNING` or `NOT_EVALUATED` items remain: show a confirmation panel listing them. Require an explicit checkbox **“I understand these checks are unresolved / warnings remain”** before committing. Do not represent the result as code-approved.
5. If only `PASS`/`ADVISORY`: accept normally; keep advisories visible.
6. **Apply** commits one undoable transaction but keeps dialog open; refresh the baseline draft after success. **OK** commits and closes; **Cancel** discards changes since last successful Apply. Consider omitting Apply in v1 if undo/transaction semantics are not yet ready.
7. If a floor elevation changes while dialog is open, detect the stale model/version and re-evaluate rather than overwriting concurrent changes.

### 6.4 Validation examples

- `H=108`, `N=13` => `h≈8.308 in`: **ERROR**, exceeds 7.75 in.
- `d=9.5 in`: **ERROR**, below 10 in.
- `W=34 in`: **ERROR** under simplified 36 in nominal rule.
- `H=108`, `N=14`, `d=11`, `W=36`: basic geometry passes, but headroom and landing status **NOT_EVALUATED** without building context; comfort heuristic **ADVISORY**.
- Negative, zero, `NaN`, or infinite values: **ERROR**.
- A floor-linked stair with `to.finished_elevation <= from.finished_elevation`: **ERROR**.

## 7. Object and persistence schema

Keep the existing project's JSON schema authoritative. Extend it without breaking legacy furnishings. Suggested logical structure (adapt names/types to existing schema conventions):

```json
{
  "id": "stair-uuid",
  "type": "stairs",
  "schema_version": 1,
  "geometry_type": "straight",
  "placement": {
    "floor_id": "level-1",
    "x": 0.0,
    "y": 0.0,
    "rotation_degrees": 0.0,
    "ascending_direction": "local_positive_x"
  },
  "floor_link": {
    "from_floor_id": "level-1",
    "to_floor_id": "level-2",
    "rise_mode": "linked",
    "detached_total_rise": null
  },
  "parameters": {
    "tread_depth": 11.0,
    "stair_width": 36.0,
    "riser_count_mode": "auto",
    "riser_count_override": null
  },
  "code_profile_id": "residential_irc_example",
  "unit": "in"
}
```

**Do not persist calculated geometry as independently authoritative.** A cached calculated summary may be saved for speed only with an explicit invalidation/version policy. Recalculate on load and whenever controlling parameters, floor elevations, or code profile change. Preserve stable object identity and references. Store acknowledgement/validation provenance separately if required for review/audit.

## 8. Suggested Python modules and APIs

Use Python `snake_case`, type hints, dataclasses or the project's established domain conventions, and pure testable geometry functions.

```python
@dataclass(frozen=True)
class StairInputs:
    total_rise: float
    tread_depth: float
    stair_width: float
    riser_count_override: int | None = None

@dataclass(frozen=True)
class StairGeometry:
    riser_count: int
    riser_height: float
    tread_count: int
    total_run: float
    pitch_degrees: float
    footprint_length: float
    footprint_width: float

@dataclass(frozen=True)
class ValidationFinding:
    rule_id: str
    severity: str
    message: str
    actual: float | None = None
    limit: float | None = None


def calculate_stair_geometry(inputs: StairInputs, code_profile) -> StairGeometry:
    ...

def validate_stairway(inputs: StairInputs, geometry: StairGeometry,
                      code_profile, building_context) -> list[ValidationFinding]:
    ...
```

Recommended responsibilities:

- `stair_model.py`: persistent stair furnishing state and floor links.
- `stair_geometry.py`: pure deterministic calculations and optional plan/elevation geometry generation.
- `stair_validation.py`: code-profile-based rules and structured findings.
- `stair_properties_dialog.py`: PyQt6 modal UI with draft state and OK/Cancel/Apply behavior.
- `stair_elevation_view.py`: reference-inspired scalable elevation drawing, dimensions, and selection-safe rendering.
- `stair_graphics_item.py`: plan-view furnishing item, hit testing, placement, rotation, selection, and double-click handling.
- `tests/test_stair_geometry.py`, `tests/test_stair_validation.py`, `tests/test_stair_dialog.py`, `tests/test_stair_serialization.py`.

Adapt file layout to the actual repository; do not create parallel domain abstractions when suitable project classes already exist.

### 8.1 Double-click integration

Use the existing scene/view architecture. For a `QGraphicsItem`-based furnishing, handle `mouseDoubleClickEvent` or route the event through the project's item editor dispatcher. Open the dialog with a **deep-copy draft** of the current stair parameters. Never mutate the persistent item during preview. After successful validation, invoke the application's existing command/undo stack and emit the standard document-changed/geometry-changed signals. Preserve current selection, z-order, placement, and rotation.

### 8.2 Plan view rendering

Render a plan footprint with two side boundaries, visible tread lines, and an **up arrow** indicating ascent. `N-1` treads should be represented consistently with the geometry convention. Transform local geometry by furnishing placement/rotation. Recompute bounding rectangle and hit shape when parameters change; ensure proper scene invalidation. Show dimension labels optionally, respecting zoom. In 3D-capable environments, derive 3D mesh from the same `StairGeometry` result, never from a separate calculator.

## 9. Tests and acceptance criteria

### 9.1 Unit tests

1. `H=108`, `d=11`, `h_max=7.75` => `N=14`, `h≈7.714285714`, `T=13`, `R=143`, `θ≈35.05°`.
2. Exact boundary `H=15.5`, `h_max=7.75` => `N=2` (not 3 due to rounding).
3. Manual `N=13`, `H=108` => riser violation.
4. `d=10.0` passes minimum; `d=9.999` fails with correct precision/tolerance.
5. `W=36.0` passes nominal-width check; `W=35.999` fails with correct tolerance.
6. Invalid negative/zero/nonfinite dimensions reject safely.
7. `N=1` cannot produce an ordinary rendered staircase.
8. Floor elevation update changes linked rise and derived geometry.
9. Detached rise does not silently change floor elevations.
10. Serialization round-trip preserves controls, floor links, placement, rotation, and identity; calculated values are recomputed.
11. Warning acknowledgement is required when configured; errors cannot be bypassed by acknowledgement.
12. Unknown headroom remains `NOT_EVALUATED`, never `PASS`.

### 9.2 PyQt6 interaction tests

- Double-click opens one modal editor for the selected Stairs furnishing.
- Editing tread depth changes run immediately without changing rise.
- Editing rise or floor association changes auto riser count when needed.
- Switching Auto → Manual exposes integer control; switching back recalculates count.
- Live preview and numeric labels match geometry; no clipped widgets at normal DPI/scaling.
- Cancel leaves original furnishing and undo stack unchanged.
- OK with error stays open and identifies the violated rule.
- OK with unresolved warnings requires explicit acknowledgement.
- Valid OK updates model and all views in one undoable action.
- Undo/redo restores both parameters and geometry.
- Opening/closing without changes does not dirty the document.
- Keyboard Enter/Escape and close-box behavior respect validation/Cancel semantics.

### 9.3 Completion definition

The feature is complete when a user can place a straight Stairs furnishing, double-click it, edit a minimal parameter set in a modal dialog dominated by the specified reference-inspired side elevation, see accurate live calculations, receive clear code-profile-based errors and unresolved-check warnings at the acceptance checkpoint, accept valid edits atomically, cancel without side effects, and save/reopen the plan without geometry drift.

## 10. Implementation sequence for Claude Cowork

1. **Inspect the repository first**: find furnishing base class, scene event dispatch, dialogs, floor elevations, persistence/schema, units, undo/redo, and test framework. Record design choices before editing.
2. Implement pure stair calculations and unit tests.
3. Implement validation profiles, findings, and tests. Keep building-context-dependent checks explicitly unresolved until measurable.
4. Add the Stairs furnishing schema and backward-compatible serialization.
5. Implement 2D plan geometry and double-click editor routing.
6. Implement modal UI and reference-inspired elevation preview, including dynamic dimensions and live updates.
7. Implement the pre-acceptance validation checkpoint and transactional commit/undo.
8. Add integration/UI tests and verify persistence round-trip.
9. Document any deferred features and unknown code compliance areas; provide screenshots and a concise change report.

## 11. Agent delivery requirements

Deliver actual repository changes, not merely a mockup. Include updated schema documentation, test output, and a short usage guide. Clearly identify any unavailable reference image, code-jurisdiction assumptions, missing building-context data, and unimplemented advanced stair types. Do not state that a staircase is fully building-code compliant based solely on the three basic dimensional checks. Do not introduce external services or change the application's authoritative schema without documenting migration/compatibility implications.

---

**Key architectural decision:** Floor-level elevations determine rise; tread depth and stair width are direct controls; riser count is automatic by default with an explicit override; the geometry engine calculates riser height, tread count, total run, pitch, and footprint; a separate validator governs whether the user may commit the draft.
