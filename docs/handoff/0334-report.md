# 0334 — report: the furnishing delta landed on `main` and pushed; the 3D LIGHT SOURCES are built on a branch (0333 §3), AMBER

**Code, 2026-11-15.** Answering [`0333`](0333-ruling.md) and Patrick's word
today: gate and commit the furnishing delta by path apart from Phase 2, push
(Cowork paused for it), then build §3's light sources on a branch and report.

## 0. WHAT LANDED, AND WHERE

- **The furnishing delta is on `main` and PUSHED** — `0a73b94`,
  `ce0c439..0a73b94`. Committed BY PATH (no `-a`/`-A`): the parametric
  CABINETS + room style and the VEHICLE fleet (the old `furnishings-lane`
  work) PLUS 0333's new ISLAND, RANGE HOOD, over-range MICROWAVE, gloss
  LAUNDRY and LIGHT FIXTURES (geometry). The catalog is now 103. The push also
  carried the already-committed-but-unpushed `432d82e` (the dormer-interior
  fix + mailbox 0328–0332). Reviewer built it un-gated; **I gated it GREEN
  here first** (full, OFF+ON, ruff clean — census below).
- **Phase 2 was LEFT OUT** of that commit, as ordered — the camera walk stays
  on `camera-phase2` (`c592018`). Its files (`cameras.py`, `mainwindow.py`,
  `roofs.py`, `viewer/scene.qml`, `viewer/fp3dq.py`, `test_camera_phase2.py`)
  are not in `0a73b94`.
- **The LIGHT SOURCES are built on branch `lights-3d`** (`26e832c`, on top of
  `0a73b94`), AMBER, NOT merged, NOT pushed. This is §3 — Code's piece.

Not committed on `main`, left in the working tree untouched: the stray
`assets/icons/*` modifications (not furnishing, not mine), the user's
`fixtures/incoming/*` plans, and Cowork's non-furnishing untracked docs.

## 1. THE BRIGHTNESS FACTOR — MEASURED, NOT GUESSED (§3.1)

The three existing lights are DirectionalLights (no distance falloff):
key **1.15** (casts the shadow), fill **0.35**, sky-bounce **0.18**. A
`PointLight`/`SpotLight` falls off with distance by Qt Quick 3D's quadratic
attenuation, `1 / (constantFade + linearFade·d·0.01 + quadraticFade·d²·0.0001)`
with the defaults `constantFade = 1`, `linearFade = 0`, `quadraticFade = 1`
(d in scene units = inches).

I set **`LUMENS_PER_BRIGHTNESS = 800`**, so an 800 lm fixture has brightness
**1.0 at the source**. At 8 ft (96 in) the attenuation is
`1 / (1 + 96²·0.0001) = 1 / 1.9216 = 0.52`, so an 800 lm point delivers ≈ **0.52**
to a surface 8 ft away — **above the fill (0.35), well below the key (1.15)**:
a soft pool, not a flood. A 1600 lm fixture doubles to ≈ 1.04 at 8 ft (≈ the
key); a 400 lm nightlight gives ≈ 0.26. This is the one knob, named in one
place in `fp3dq.py`. **Caveat:** the render itself cannot be measured here (an
offscreen Qt Quick 3D View3D draws blank without a GPU — D77), and Qt's exact
internal distance scaling is taken from its documented model; the perceptual
result is Patrick's to confirm by walking a lit plan, and the factor is a
one-line change if it reads too dim or too hot.

## 2. SHADOW COST — NONE CAST TO START (§3.2)

Every added light has `castsShadow: false`. A non-shadowing light is cheap:
N lights add N per-fragment light evaluations in the shader, linear and small
for the handful a plan carries. The expensive part is a shadow-casting POINT
light — it needs a six-face cube shadow map rendered every frame (a spot needs
one map); turning even a few on multiplies the per-frame render passes. Held
off until Patrick has walked a lit plan and judged it worth the cost. Frame
cost not measured in fps here — D77: the offscreen view renders blank, so fps
on this machine would not be the fps on his.

## 3. WHAT WAS BUILT (branch `lights-3d`)

- **`fp3dq.py`** — `_light_to_qml(light, ctr)` maps each `model.lights` entry
  through the SAME recentre (`- ctr`) and z-up→y-up remap (`(x, z, -y)`) the
  meshes take, so a light sits exactly where its fixture is (pinned against
  `_to_qt3d` in the test). Brightness from lumens by `LUMENS_PER_BRIGHTNESS`.
  Lights split into `planPointLights` / `planSpotLights` and set as context
  properties. A new `LightEntry` QObject carries position/colour/brightness/
  cone to QML; `MeshEntry` gains an `emissive` (QVector3D).
- **`scene.qml`** — a `Repeater3D` per list: a `PointLight` (omnidirectional)
  or a `SpotLight` aimed straight down (`eulerRotation.x: -90`) with its cone,
  none casting shadows. The lens material now sets
  `emissiveFactor: modelData.emissive`, so a `furnishings:light_emit#rrggbb`
  mesh reads as LIT whatever the scene lighting does (§3.4); every other mesh
  carries `(0,0,0)` and is unchanged.
- **`_pbr` sheen fix (§3.5 / 0329 §4.1)** — strips the `#rrggbb` a finish name
  may carry before the catalog lookup, so the gloss laundry (and every
  `sheen_*`/`light_emit` finish) gets its real roughness instead of the
  default sheen.
- **§3.3** — an empty `model.lights` leaves both lists empty; a plan with no
  fixtures renders exactly as before (the three directional lights). Pinned.

## 4. RUN, AND NOT RUN

- **Gate on the furnishing delta (`main`):** GREEN, full.
  `Gate-Census: collected=2339 ruff=clean vacuous=0 end_assign=0 snapshot=current`;
  `Gate-OFF: 2332 passed, 7 deselected`; `Gate-ON: 2332 passed, 7 deselected`.
  (The 2339 count includes `test_camera_phase2.py`, present uncommitted in the
  working tree; it is NOT in `0a73b94`.)
- **Gate on `lights-3d`:** GREEN, quick (not pushed, so quick unlocks the
  commit). `collected=2318 ruff=clean`, `Gate-OFF: 2311 passed, 7 deselected`.
  The lower count is the honest one for the branch — a clean checkout with no
  uncommitted Phase 2 test file.
- **New test** `tests/test_viewer_lights.py` (10 cases, all pass): the light
  rides the same transform as the meshes, brightness scales by the factor,
  kind/cone/colour pass through, the lens is emissive in its colour and every
  other mesh is not, `_pbr` strips the suffix (and still resolves a plain
  name), and an empty plan reports no lights.
- **QML load confirmed** offscreen with a point, a spot and an emissive mesh
  instantiated — `scene.qml` parses and loads with the new nodes, no QML
  errors. The RENDER is not asserted (D77).
- **Not run:** the lit render on a real GPU — that is Patrick's walk.

## 5. FOR PATRICK (§3 is AMBER on `lights-3d`)

1. Run the app from `lights-3d` (the branch is checked out at
   `.claude/worktrees/lights-3d`, or `git checkout lights-3d`). Place light
   fixtures (the Lighting palette group), put a camera in the room, 3D view,
   and walk. The fixtures should now LIGHT the room; the lens should glow its
   colour; the gloss laundry should read gloss, not matte.
2. Say if the brightness is too dim or too hot — `LUMENS_PER_BRIGHTNESS` is the
   one knob. Say if any light should cast a shadow (and accept the frame cost).
3. When it reads right, it merges to `main`. Its `_pbr` sheen fix reaches
   `main` with it; Phase 2's own `scene.qml`/`fp3dq.py` edits and this branch's
   will need one reconciliation at merge (both touch those two files) — a known,
   small overlap, deferred until both land.

## 6. OWED

- **Patrick:** the walk-test above; the brightness / shadow calls.
- **Reviewer (Cowork):** the furnishing fixes from 0333 §5–6 (the island's
  plan symbol, etc.); may resume on the pushed `0a73b94`.
- **Code:** merge `lights-3d` on his word; reconcile with Phase 2 at its
  landing.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XVitzXNKQWS64xhKKpacra
