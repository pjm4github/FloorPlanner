# 0252 — report: 0248's plans B and D built on `roof-openings-ridge-meet` — openings on a dormer record, cut into its generated face; the equal-height ridge meeting in the clip; the viewer's `--shot` given a viewpoint; AMBER, for his check

**Code, 2026‑10‑11.** No merge has happened since
[`0251`](0251-report.md). His word:

> *"Implement plan B and D from 0248"*

and, while it was built: *"Look at using the QT 3D rendering feature
instead of the existing test rendering. The viewer we have does a very
nice job rendering the image, much better than the test one you are
currently using."*

One commit on `roof-openings-ridge-meet`, a PR for his check.

## 0. PLAN D — the equal-height ridge meeting

**What it was** (0248 §2 item 5, the house model's first iteration): a
cross gable whose ridge runs from the front wall back to EXACTLY the
main ridge at the main ridge's height — the ridges meet. The clip's
joining rule saw an end at its host's surface and extended it; the
extension ran on behind the main ridge, where the main's back slope
falls away, and was drawn there as a fin, while the gable's own front
body was pruned: the front showed the main's slope and no gable.

**The rule.** An end whose ridge TOUCHES its host's ridge at the host's
own height is a MEETING, not a join: nothing is extended; the gable's
planes meet the main's along the valleys from that point to the eave
corners, which the surfaces give. Two refinements the record's own
fixtures demanded: (a) a touch at the far end of a ridge is not a
crossing for the near end — the gable's front end stays open as before,
not "an arm that crossed the host"; (b) where the host's own ridge end
is swallowed by this roof's footprint it is the equal-height L
(`_l_pair`: A's last 50″ run into B), whose wing must run on over the
corner to the main's far eave — the join, as 0164 built it, unchanged.
Every roof suite green with both: the L's four tests, the three-ridge
fixtures, D88, the shed form.

**Pinned**, `tests/test_roof_ridge_meeting.py` (4): the meeting draws the
gable's front triangle and no fin, the main keeps everything else; the
4″-under workaround as the control; a lower gable ending on the main
slope is still a join; the porch-on-the-eaves tie draws both roofs
whole.

**A residual named, not this plan's:** a lower cross gable sketched
PAST where its height meets the main slope — buried under the main —
still draws a fin where its extension comes out the back slope
(measured: 1″ past, 40″ under: 14,976 sq in behind the ridge). A
sketching fault more than a clip one; the End-On dialog could refuse
it.

## 1. PLAN B — openings on a dormer record

**The record.** `openings` on a roof record that has a `host` — the
same `opening` records a wall carries (kind, code, anchor, sill, head);
the schema refuses them on a roof with no host. The face is dimensioned
like a wall: `v1` its LEFT end (the `span_in[0]` side of a gable
dormer; the `ridge[0]` end of a shed dormer's front edge), `v2` the
right, `center` the middle; sill and head above the dormer's level
base. Dataclass, writer, reader and `RoofItem.openings` round-trip it.

**The 3D builder.** `_face_openings` turns the records into bands along
the face (`opening_span` and `parse_wwhh`, the wall's own); the
generated run of boxes is split at every band edge (`_split_by_bands`);
inside a band a box becomes the piece under the sill and the piece over
the head (`_face_pieces`), nothing between. A gable dormer's face
(`_dormer_face`) carries them; a shed dormer's front edge — its side-0
cheek (`_dormer_cheeks`) — carries them; a shed's two end sides do not.
An unreadable record is skipped and the face stays whole.

**Not built:** the plan view draws nothing for them, and no dialog adds
them — the record is written by hand or by a generator (the house
model's dormer windows are on the house wall, not the dormer, so it
needs none).

**Pinned**, `tests/test_roof_dormer_openings.py` (6): the schema; the
round trip; a window cut into a gable dormer's face (rays inside hit
nothing, rays under the sill, over the head and beside it hit, the
control without the record hits throughout); a window in a shed
dormer's front edge with its sill and head pieces standing; an
unreadable record skipped; the three dormer fixtures carry none and
build as before.

## 2. THE APP'S OWN 3D VIEW CAN TAKE A SHOT

His viewer is the Qt Quick 3D one (`fp3dq.py` + `scene.qml`: ambient
occlusion, shadows, the view the app's *3D view…* opens; his
screenshots come from it), not the pyqtgraph `fp3d.py` one. It had no
shot. Now `python floorplanner/viewer/fp3dq.py <design> --shot <png>
--yaw Y --pitch P --zoom Z`: the orbit node's two angles and a distance
factor, 0 / 0 / 1 for the home view, exposed to the QML as `cfg.yaw`,
`cfg.pitch`, `cfg.zoom` (the OrbitCameraController goes on from there
by mouse, as before); `grab_quick_view` takes the image
(`grabFramebuffer` on the QQuickWidget, `grabWindow` on a container's
QQuickView) after `--shot-delay` ms (600) for AO and shadows to settle.
It needs a real display (D77), which this desktop has; a null image is
reported, not written. The pyqtgraph viewer's `--shot` got the same
three terms (`--azimuth`, `--elevation`, `--distance`) on the way.

The house model's iteration 9, shot with the app's view:
`fixtures/incoming/house_cutout_work/iter-09-q3d-front.png` (yaw 0,
pitch 8, zoom 0.6) and `…-front-left.png` (yaw 25, pitch 10, zoom 0.6).
`render3d.py` stays for headless tests and a session with no display.
(`scene.qml`'s background, white for green, is his own edit, landed
with this on his word: *"You can consider that a clean file and
incorporate those colors."*)

## 3. THE RECEIPT

* `--quick` 1564 passed; ruff clean; the full gate GREEN on the branch
  commit.

## 4. TIER

**AMBER** — a clip rule change (D) and a new record field with 3D
geometry (B). For his check: the house model's first-iteration case
(a gable to the main ridge) in the 3D view, if he wants to sketch it;
and a dormer with an `openings` record in the 3D view.

## 5. `fixtures/incoming/`, with ages

* `house_cutout_transparent.png`, `house_cutout_1stfloor.png` — his own,
  2026‑10‑11.
* `house_cutout.json` (iteration 9), `house_cutout_work/` — mine,
  2026‑10‑11.
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 6. WHAT HAPPENS NEXT

His check of the PR. Then 0248 §3's E (posts, the porch floor) and the
hip run (0248 §2 item 6) on his word. Behind them: the compose cost
([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0251`](0251-report.md).
