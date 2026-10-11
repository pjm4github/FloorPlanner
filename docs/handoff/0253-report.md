# 0253 — report: PR #83 merged on his word — openings on a dormer record, the equal-height ridge meeting, the app's 3D view taking a shot; 0248's plans B and D closed; iteration 10 of the house ordered

**Landed:** PR #83 · 32fd37d · 2026-10-11 · AMBER · checked by Patrick on the house model's shots: "The dormers and roofs look right"

**Code, 2026‑10‑11.** The record ([`0197-ruling.md`](0197-ruling.md) §7).
[`0252`](0252-report.md) put 0248 §3's plans B and D to him on
`roof-openings-ridge-meet`, one commit, with the app's own 3D view
given a shot. His word:

> *"The dormers and roofs look right, land #83 - We need to do another
> iteration starting at 10 to make sure that windows in the dormers are
> properly rendered and match the house_cutout_transparent.png."*

Done as said: the branch landed on `main` at **`32fd37d`**,
fast-forward; [PR #83](https://github.com/pjm4github/FloorPlanner/pull/83)
MERGED; the branch deleted, local and remote. **0248 §3's B and D are
closed.** Of 0248's plan, E (posts, the porch floor) and the hip run
(§2 item 6) remain, his to order.

## 1. WHAT LANDED, in one place

* **Plan D** ([`0252`](0252-report.md) §0): an end that touches its
  host's ridge at the host's height is a meeting, not a join; a touch at
  the far end is no crossing for the near end; a swallowed host end is
  the equal-height L, the join unchanged. `tests/test_roof_ridge_meeting.py`.
* **Plan B** ([`0252`](0252-report.md) §1): `openings` on a dormer
  record, cut into its generated face and a shed dormer's front edge.
  `tests/test_roof_dormer_openings.py`.
* **The app's 3D view takes a shot** ([`0252`](0252-report.md) §2):
  `fp3dq.py --shot --yaw --pitch --zoom --fov`; on his word after the
  first shots, pitch 32 for eye level and `--fov 28` with the camera
  farther back for an undistorted picture; his white background landed.

## 2. ITERATION 10 — ordered, in `fixtures/incoming/house_cutout_work/`

The windows in the dormers, rendered and matched to the picture. First
measured on iteration 9 before anything moved: the gable dormers' (the
bays' gables') second-floor windows are in the record, on the bay front
walls, and the shot shows the gable faces SOLID while the shed dormer's
three read as openings — a ray through the left gable's window at its
centre meets wall. The iteration starts from that measurement; what it
finds goes in the work folder's `STATUS.md` and the next report.

## 3. `fixtures/incoming/`, with ages

* `house_cutout_transparent.png`, `house_cutout_1stfloor.png` — his own,
  2026‑10‑11.
* `house_cutout.json` (iteration 9), `house_cutout_work/` — mine,
  2026‑10‑11.
* `wiscaway2026-10-07R1.json` — his own, 2026‑10‑07; exit his to name.
* `README.md`.

## 4. WHAT HAPPENS NEXT

Iteration 10. Then E and the hip run on his word. Behind them: the
compose cost ([`0237`](0237-report.md) §0).

**Carried:** unchanged from [`0252`](0252-report.md).
