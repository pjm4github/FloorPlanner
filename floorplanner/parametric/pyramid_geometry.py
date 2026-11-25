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

EAVES_BINDS = ("room_top", "manual")   # eaves follow the room ceiling, or set by hand
WELDS = ("auto", "off")                # weld into the surrounding roof, or stand whole

STATE_DEFAULTS = {
    "sides": 6,                 # 3..12
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
# the regular polygon
# --------------------------------------------------------------------------
def _angle(k, n):
    """Face k's outward-normal angle parameter."""
    return k * _TAU / n


def face_normals(st):
    """The n outward unit normals, local. Face 0's is `(0, -1)` -- up the
    screen at rotation 0 -- and they run clockwise as the index rises."""
    n = st["sides"]
    return [(math.sin(_angle(k, n)), -math.cos(_angle(k, n))) for k in range(n)]


def _polygon(apothem, n):
    """The regular n-gon whose edge MIDPOINTS sit `apothem` out along each face
    normal: its vertices, local. Vertex j lies between face j-1 and face j."""
    r = apothem / math.cos(math.pi / n)          # circumradius
    out = []
    for j in range(n):
        a = _angle(j, n) + math.pi / n
        out.append((r * math.sin(a), -r * math.cos(a)))
    return out


def wall_polygon(st):
    """The WALL line (eaves-start) polygon, local -- inradius out."""
    return _polygon(st["inradius_in"], st["sides"])


def eaves_polygon(st):
    """The EAVE polygon, local -- the wall line plus the overhang."""
    return _polygon(st["inradius_in"] + st["overhang_in"], st["sides"])


def circumradius(st):
    """Centre to a WALL-line corner."""
    return st["inradius_in"] / math.cos(math.pi / st["sides"])


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
    """The FARTHEST local point `p` reaches along any face's outward normal --
    the one quantity the pyramid's height is a function of."""
    n = st["sides"]
    return max(p[0] * math.sin(_angle(k, n)) + p[1] * -math.cos(_angle(k, n))
               for k in range(n))


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
    None once `p` is past the eave edge -- there is no roof there."""
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
    out = []
    for k in range(n):
        a, b = (k - 1) % n, k
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
    """The eave polygon, local -- the plan outline (overhang included)."""
    return eaves_polygon(st)


def bbox(st):
    """(width, depth) of the eave polygon's bounding box, local."""
    pts = eaves_polygon(st)
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    return (max(xs) - min(xs), max(ys) - min(ys))


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
