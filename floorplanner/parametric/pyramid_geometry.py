"""Pyramid-roof geometry -- pure Python, the ONE calculator (0367 stage 1).

NO Qt AND NO `floorplanner` IMPORT, on purpose: like `dormer_geometry.py` and
`stair_geometry.py` this file is loaded BY PATH by the 3D viewer, so the plan
symbol, the properties dialog, the 3D faces and (stage 3) the weld all read the
same numbers -- condition C1 of the ruling: one geometry, no second formula.

WHAT A PYRAMID ROOF IS HERE (docs/handoff/0367-ruling.md). A furnishing, kind
`pyramid_roof`, dropped on a ceiling: a pyramid over a REGULAR POLYGON that
covers a bump-out (a bay / gazebo / turret). It owns no wall -- the walls under
it are whatever the user draws, and they rise to it. The apex is the only point
over the centre; every face is one flat plane at the same pitch.

ARC (a half / partial gazebo). `arc_deg` is the angular sweep and `sides` the
number of facets in it, so each facet spans `arc_deg / sides` degrees. At 360
(the default) the facets close into the regular polygon above, unchanged. Below
360 the facets fan SYMMETRICALLY about the up-screen direction (face 0's normal
at rotation 0): a pie wedge is left out, open to the peak -- no vertical cut
face, no gable wall. Everything downstream (plan symbol, 3D faces, walls, weld)
reads the present facets only, so a `sides`-facet arc builds `sides` faces.

LOCAL FRAME (inches). The origin is the CENTRE -- the furnishing's `pos`, which
is the apex in plan. +X is screen-east, +Y screen-south at rotation 0, so the
frame is the plan frame turned by `rotation` CLOCKWISE on screen (as every
furnishing turns). At rotation 0 ONE FACE's outward normal points UP the screen
(local `(0, -1)`, i.e. plan -y), matching `dormer_geometry.ridge_direction(0)`.

HEIGHTS are above the pyramid's OWN level -- the floor the user stands on to
size it, as the dormer's are. The apex height is DERIVED:
`eaves_h_in + inradius_in * pitch_12 / 12` (the pitch climbs the inradius run
from the wall line in to the centre).
"""
import math

MIN_SIDES = 3
MAX_SIDES = 12
MIN_INRADIUS_IN = 6.0
MIN_ARC_DEG = 15.0
FULL_ARC_DEG = 360.0

EAVES_BINDS = ("room_top", "manual")   # eaves follow the room ceiling, or set by hand
WELDS = ("auto", "off")                # weld into the surrounding roof, or stand whole

STATE_DEFAULTS = {
    "sides": 6,                 # the number of FACETS (sections); 3..12
    "arc_deg": 360.0,           # the angular SWEEP; 360 = a whole gazebo
    "inradius_in": 72.0,        # centre to the WALL line (the eaves-start line)
    "eaves_h_in": 96.0,         # the eaves-start line, above this level
    "eaves_bind": "room_top",   # room_top: eaves follow the room's ceiling
    "pitch_12": 10.0,           # rise per 12 of run, EVERY face
    "overhang_in": 12.0,        # eave past the wall line, in plan
    "weld": "auto",             # auto: weld into surrounding roof where higher
}
_NUMBERS = ("inradius_in", "eaves_h_in", "pitch_12", "overhang_in")
_EPS = 1e-9
_TAU = 2.0 * math.pi


def is_pyramid_roof_state(state):
    """A stored state that is a pyramid roof's (has `sides` and an inradius)."""
    return (isinstance(state, dict) and "sides" in state
            and "inradius_in" in state)


def normalize_state(state):
    """A complete, type-clean copy. Missing keys take their defaults; a value
    that will not parse takes its default. NOTHING IS CLAMPED except what would
    stop the arithmetic: `sides` into [3, 12], the inradius to a floor, the
    overhang and pitch to >= 0. Keys this version does not know are carried
    through, so a newer file survives a round trip."""
    src = dict(state or {})
    out = dict(src)
    try:
        sides = int(round(float(src.get("sides", STATE_DEFAULTS["sides"]))))
    except (TypeError, ValueError):
        sides = STATE_DEFAULTS["sides"]
    out["sides"] = max(MIN_SIDES, min(MAX_SIDES, sides))
    out["eaves_bind"] = (src.get("eaves_bind")
                         if src.get("eaves_bind") in EAVES_BINDS else "room_top")
    out["weld"] = src.get("weld") if src.get("weld") in WELDS else "auto"
    for key in _NUMBERS:
        try:
            v = float(src.get(key, STATE_DEFAULTS[key]))
        except (TypeError, ValueError):
            v = STATE_DEFAULTS[key]
        out[key] = v if math.isfinite(v) else STATE_DEFAULTS[key]
    out["inradius_in"] = max(out["inradius_in"], MIN_INRADIUS_IN)
    out["overhang_in"] = max(out["overhang_in"], 0.0)
    out["pitch_12"] = max(out["pitch_12"], 0.0)
    try:
        arc = float(src.get("arc_deg", FULL_ARC_DEG))
    except (TypeError, ValueError):
        arc = FULL_ARC_DEG
    if not math.isfinite(arc):
        arc = FULL_ARC_DEG
    out["arc_deg"] = max(MIN_ARC_DEG, min(FULL_ARC_DEG, arc))
    return out


def default_state(ceiling_in=None):
    """A newly dropped pyramid: eaves at the room's ceiling when there is one
    (the `room_top` bind), its own numbers otherwise."""
    st = dict(STATE_DEFAULTS)
    if ceiling_in is not None:
        st["eaves_h_in"] = max(float(ceiling_in), MIN_INRADIUS_IN)
    return st


# --------------------------------------------------------------------------
# heights
# --------------------------------------------------------------------------
def _rise(st):
    """Rise per inch of run (pitch-12 as a ratio)."""
    return st["pitch_12"] / 12.0


def apex_height(st):
    """The apex above this level -- derived: eaves + inradius x pitch / 12."""
    return st["eaves_h_in"] + st["inradius_in"] * _rise(st)


def eave_height(st):
    """The eave edge above this level -- below the wall line by the overhang's
    fall (the same plane continues out past the wall)."""
    return st["eaves_h_in"] - st["overhang_in"] * _rise(st)


# --------------------------------------------------------------------------
# the regular polygon (whole) or the fan of facets (an arc)
# --------------------------------------------------------------------------
def is_full(st):
    """True when the sweep is the whole 360 -- a closed regular polygon."""
    return st.get("arc_deg", FULL_ARC_DEG) >= FULL_ARC_DEG - _EPS


def _facet_angle(st):
    """The azimuth each facet spans (radians): `tau / sides` when whole, else
    `arc / sides`."""
    arc = _TAU if is_full(st) else math.radians(st["arc_deg"])
    return arc / st["sides"]


def _normal_azimuths(st):
    """Each facet's outward-normal azimuth (radians, CLOCKWISE from up-screen).
    Whole: `k * tau / n`, so face 0 points up. Arc: the facets fan symmetrically
    about up, so the middle of the sweep points up."""
    n = st["sides"]
    if is_full(st):
        return [k * _TAU / n for k in range(n)]
    d = _facet_angle(st)
    return [(k - (n - 1) / 2.0) * d for k in range(n)]


def _corner_azimuths(st):
    """The eave/wall CORNER azimuths (radians, clockwise from up). Whole: n
    corners `pi/n + j*tau/n` (so a corner sits half a facet off up). Arc: n+1
    corners from `-arc/2` to `+arc/2`, the two ends being the open cut edges."""
    n = st["sides"]
    if is_full(st):
        return [math.pi / n + j * _TAU / n for j in range(n)]
    d = _facet_angle(st)
    half = math.radians(st["arc_deg"]) / 2.0
    return [-half + j * d for j in range(n + 1)]


def face_normals(st):
    """The outward unit normals, local -- one per facet. Face 0's is `(0, -1)`
    (up the screen) when whole; for an arc the fan is centred on up."""
    return [(math.sin(a), -math.cos(a)) for a in _normal_azimuths(st)]


def _ring(apothem, st):
    """The corners at `apothem` in along each facet normal (circumradius out),
    local -- a closed n-gon when whole, an open polyline of n+1 corners for an
    arc. Corner j lies on the boundary between two adjacent facets."""
    r = apothem / math.cos(_facet_angle(st) / 2.0)        # circumradius
    return [(r * math.sin(a), -r * math.cos(a)) for a in _corner_azimuths(st)]


def wall_polygon(st):
    """The WALL line (eaves-start) corners, local -- inradius out."""
    return _ring(st["inradius_in"], st)


def eaves_polygon(st):
    """The EAVE corners, local -- the wall line plus the overhang."""
    return _ring(st["inradius_in"] + st["overhang_in"], st)


def circumradius(st):
    """Centre to a WALL-line corner."""
    return st["inradius_in"] / math.cos(_facet_angle(st) / 2.0)


def convex_cells(st):
    """The pyramid's plan footprint as CONVEX cells (eave extent), local -- the
    pieces the wall-climb and the weld split on. Whole: one cell, the eave
    n-gon. Arc: one triangle per facet `[apex, corner_k, corner_k+1]`, so a
    fan of any sweep (even a reflex one past 180) is handled as convex pieces."""
    eave = eaves_polygon(st)
    if is_full(st):
        return [list(eave)]
    return [[(0.0, 0.0), eave[k], eave[k + 1]] for k in range(st["sides"])]


# --------------------------------------------------------------------------
# the faces
# --------------------------------------------------------------------------
def face_at(st, p):
    """The index of the face whose plane governs local point `p` -- the one
    whose outward normal `p` reaches farthest along."""
    best, bi = -math.inf, 0
    for i, (nx, ny) in enumerate(face_normals(st)):
        m = p[0] * nx + p[1] * ny
        if m > best:
            best, bi = m, i
    return bi


def _max_proj(st, p):
    """The FARTHEST local point `p` reaches along any PRESENT face's outward
    normal -- the one quantity the pyramid's height is a function of. For an arc
    only the present facets count."""
    return max(p[0] * math.sin(a) + p[1] * -math.cos(a)
               for a in _normal_azimuths(st))


def _in_sweep(st, p):
    """Whether local point `p` lies within the arc's angular sweep (always true
    when whole). The apex itself is in every sweep. Outside it there is no roof
    -- the pie wedge was left open."""
    if is_full(st):
        return True
    if abs(p[0]) < _EPS and abs(p[1]) < _EPS:
        return True
    az = math.atan2(p[0], -p[1])                 # clockwise from up-screen
    half = math.radians(st["arc_deg"]) / 2.0
    return -half - 1e-9 <= az <= half + 1e-9


def plane_height(st, p):
    """The height of the pyramid's planes CONTINUED to local point `p` -- `apex_h`
    minus the pitch times `_max_proj`. Unlike `surface_height` it NEVER returns
    None: past the eave the planes simply continue, as a ridge roof's side
    planes do. The wall-climb and the weld read here, so there is ONE height
    formula (condition C1)."""
    return apex_height(st) - _rise(st) * _max_proj(st, p)


def surface_height(st, p):
    """The roof's height at local point `p`, or None past the eave. Every face
    is the plane `apex_h - (pitch/12) * (p . normal)`; the pyramid surface at
    `p` is the governing face's, so it is `apex_h` minus the pitch times the
    FARTHEST the point reaches along any face normal (`plane_height`). Returns
    None once `p` is past the eave edge -- there is no roof there -- and (for an
    arc) once `p` falls in the open pie wedge, outside the sweep."""
    if not _in_sweep(st, p):
        return None
    m = _max_proj(st, p)
    reach = st["inradius_in"] + st["overhang_in"]
    if m > reach + 1e-6:
        return None
    return apex_height(st) - _rise(st) * m


def hips(st):
    """The hips in plan: the apex-to-corner lines, one per eave corner. Local
    segments `[((0, 0), (cx, cy)), ...]` -- the diagonal ridges of the roof."""
    return [((0.0, 0.0), v) for v in eaves_polygon(st)]


def face_planes(st):
    """Each face as a 3D triangle `[apex, corner_a, corner_b]` (local x, y,
    height above this level) plus its outward `normal` and the `wall_edge`
    (the two wall-line corners it springs from). Face k springs from eave
    corners k-1 and k; its apex is the centre at `apex_height`."""
    n = st["sides"]
    apex = (0.0, 0.0, apex_height(st))
    eave = eaves_polygon(st)
    wall = wall_polygon(st)
    ez = eave_height(st)
    normals = face_normals(st)
    full = is_full(st)
    out = []
    for k in range(n):
        # whole: corner k-1 and k (the n corners wrap). arc: corner k and k+1
        # (n+1 corners, the ends being the open cut edges).
        a, b = ((k - 1) % n, k) if full else (k, k + 1)
        out.append({
            "normal": normals[k],
            "tri": [apex, (eave[a][0], eave[a][1], ez), (eave[b][0], eave[b][1], ez)],
            "wall_edge": (wall[a], wall[b]),
        })
    return out


# --------------------------------------------------------------------------
# the plan
# --------------------------------------------------------------------------
def footprint(st):
    """The plan outline, local (overhang included). Whole: the eave polygon.
    Arc: the fan -- the apex (centre) and the eave corners -- so the outline is
    the pie sector that is actually roofed."""
    eave = eaves_polygon(st)
    return eave if is_full(st) else [(0.0, 0.0), *eave]


def bbox(st):
    """(width, depth) of a bounding box CENTRED on the apex (the item's pos),
    local. Sized symmetrically about the centre so the furnishing's position
    stays the apex even for an arc, whose footprint is not centred on it. Whole
    (symmetric footprint) this is exactly the footprint's extent."""
    pts = footprint(st)
    w = 2.0 * max(abs(x) for x, _ in pts)
    d = 2.0 * max(abs(y) for _, y in pts)
    return (w, d)


def plan(st):
    """Everything the plan symbol draws, local coordinates:

        wall    [(x, y), ...]    the wall-line polygon (eaves-start)
        eaves   [(x, y), ...]    the eave polygon (overhang included)
        hips    [((x, y), (x, y)), ...]   apex to each eave corner
        apex    (x, y)           the centre
    """
    return {
        "wall": wall_polygon(st),
        "eaves": eaves_polygon(st),
        "hips": hips(st),
        "apex": (0.0, 0.0),
    }


# --------------------------------------------------------------------------
# local <-> plan
# --------------------------------------------------------------------------
def to_plan(pos, rotation_deg, pt):
    """A local point as a plan point -- the plan frame turned `rotation_deg`
    CLOCKWISE on screen (y down), about `pos`."""
    r = math.radians(rotation_deg)
    c, s = math.cos(r), math.sin(r)
    x, y = pt
    return (pos[0] + x * c - y * s, pos[1] + x * s + y * c)


def to_local(pos, rotation_deg, pt):
    r = math.radians(rotation_deg)
    c, s = math.cos(r), math.sin(r)
    dx, dy = pt[0] - pos[0], pt[1] - pos[1]
    return (dx * c + dy * s, -dx * s + dy * c)


def face_normal_plan(rotation_deg, normal):
    """A local face normal as a plan direction."""
    r = math.radians(rotation_deg)
    c, s = math.cos(r), math.sin(r)
    nx, ny = normal
    return (nx * c - ny * s, nx * s + ny * c)
