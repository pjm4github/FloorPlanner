"""Dormer geometry -- pure Python, the ONE calculator (0352, phase 1).

NO Qt AND NO `floorplanner` IMPORT, on purpose: like `stair_geometry.py` this
file is loaded BY PATH by the 3D viewer, so the plan item, the properties
dialog, the knee lines and the 3D roof are all read from the same numbers.

WHAT A DORMER IS HERE (docs/furnishing-spec/DORMER_FURNISHING_PLAN.md). A
furnishing, kind `dormer`, dropped on the level whose rooms it lights. Its
parameters live in the record's `state`. IT OWNS NO WALL: the walls under it
are whatever the user draws on that level, and they rise into it. The only
plan lines it produces are its own outline and the KNEE LINES -- where its
planes cross a ceiling height.

LOCAL FRAME (inches). The origin is the FACE END OF THE RIDGE -- the
furnishing's `pos`. +Y runs along the ridge, from the face back into the host
roof. +X is the ridge's LEFT, by the roof code's own convention: for a ridge
direction (dx, dy) the left normal is (-dy, dx). A rotation of 0 points the
ridge up the screen (plan -y), so the face looks down the screen; the angle
turns clockwise on screen, as every furnishing's does.

HEIGHTS are above the dormer's OWN level -- the floor the user stands on to
size it. `to_roof_record` shifts them to whatever datum the clipper wants.
"""
import math

FORMS = ("gable", "shed")

STATE_DEFAULTS = {
    "form": "gable",
    "symmetric": True,
    "span_left_in": 60.0,          # ridge to the eaves-start line, left
    "span_right_in": 60.0,         # ... right (a shed has none)
    "eaves_h_in": 60.0,            # the eaves-start line, above this level
    "pitch_12": 10.0,              # rise per 12 of run, on the LEFT span
    "eave_overhang_left_in": 12.0,     # control E
    "eave_overhang_right_in": 12.0,
    "face_overhang_in": 12.0,      # control F: the rake past the face
    "guide_left_in": 0.0,          # control C: side guide, 0 = on the eaves line
    "guide_right_in": 0.0,
    "box_left_in": 0.0,            # control B: frame half-width, 0 = not set
    "box_right_in": 0.0,
    "depth_in": 96.0,              # ridge length (anchor to face); the run off a roof
    "anchored": False,             # P2: pos is the ANCHOR, not the face (migration flag)
}
_NUMBERS = tuple(k for k, v in STATE_DEFAULTS.items() if isinstance(v, float))
_EPS = 1e-9
MIN_SPAN_IN = 12.0


def is_dormer_state(state):
    return isinstance(state, dict) and state.get("form") in FORMS


def normalize_state(state):
    """A complete, type-clean copy. Missing keys take their defaults, a
    nonsense form falls back, a number that will not parse takes its default;
    NOTHING IS CLAMPED except what would stop the arithmetic (a span of zero).
    Keys this version does not know are carried through."""
    src = dict(state or {})
    out = dict(src)
    out["form"] = src.get("form") if src.get("form") in FORMS else "gable"
    out["symmetric"] = bool(src.get("symmetric", STATE_DEFAULTS["symmetric"]))
    out["anchored"] = bool(src.get("anchored", STATE_DEFAULTS["anchored"]))
    for key in _NUMBERS:
        try:
            v = float(src.get(key, STATE_DEFAULTS[key]))
        except (TypeError, ValueError):
            v = STATE_DEFAULTS[key]
        out[key] = v if math.isfinite(v) else STATE_DEFAULTS[key]
    # A shed and a gable SHARE their box: both have two side walls, symmetric
    # by default (Patrick, 2026-11-18 -- the shed's left/right controls work on
    # both sides). They differ only in the ROOF: a gable has two planes meeting
    # at a ridge that runs along the depth; a SHED has ONE plane, level across
    # the width, that rises from the FACE back along the depth to a high ridge
    # at the back -- the only line that touches the host roof.
    out["span_left_in"] = max(out["span_left_in"], MIN_SPAN_IN)
    out["span_right_in"] = max(out["span_right_in"], MIN_SPAN_IN)
    if out["symmetric"]:
        for a, b in (("span_left_in", "span_right_in"),
                     ("eave_overhang_left_in", "eave_overhang_right_in"),
                     ("guide_left_in", "guide_right_in"),
                     ("box_left_in", "box_right_in")):
            out[b] = out[a]
    for key in ("eave_overhang_left_in", "eave_overhang_right_in",
                "face_overhang_in", "guide_left_in", "guide_right_in",
                "box_left_in", "box_right_in", "pitch_12"):
        out[key] = max(out[key], 0.0)
    out["depth_in"] = max(out["depth_in"], 1.0)
    return out


def default_state(ceiling_in=None, host_slope=None, host_ridge_in=None):
    """A newly dropped dormer: its eaves a foot under the ceiling it lights,
    the host's own pitch when there is a host -- and, given the host's ridge
    height, fitted UNDER it (0359): a dormer is never born in error."""
    st = dict(STATE_DEFAULTS)
    if ceiling_in is not None:
        st["eaves_h_in"] = max(float(ceiling_in) - 12.0, 12.0)
    if host_slope is not None and host_slope > _EPS:
        st["pitch_12"] = round(host_slope * 12.0, 3)
    if host_ridge_in is not None:
        st = fit_under_ridge(st, float(host_ridge_in))
    return st


RIDGE_CLEAR_IN = 6.0     # a newly fitted dormer's ridge stops this far under


def fit_under_ridge(state, host_ridge_in, clear=RIDGE_CLEAR_IN):
    """`state` changed as little as it takes to bring the ridge to `clear`
    under `host_ridge_in`: first NARROWED (pitch kept, down to 2 ft a side),
    then, if that is not enough, its eaves LOWERED. Unchanged when it
    already fits."""
    st = normalize_state(state)
    limit = host_ridge_in - clear
    if ridge_height(st) <= limit + _EPS:
        return st
    rise_per_in = st["pitch_12"] / 12.0
    if rise_per_in > _EPS:
        span = max((limit - st["eaves_h_in"]) / rise_per_in, 24.0)
        if span < st["span_left_in"]:
            scale = span / st["span_left_in"]
            st["span_left_in"] = span
            if st["span_right_in"] > _EPS:
                st["span_right_in"] = max(st["span_right_in"] * scale, MIN_SPAN_IN)
            st["guide_left_in"] = min(st["guide_left_in"], st["span_left_in"])
            st["guide_right_in"] = min(st["guide_right_in"], st["span_right_in"])
    over = ridge_height(st) - limit
    if over > _EPS:
        st["eaves_h_in"] = max(st["eaves_h_in"] - over, 0.0)
    return normalize_state(st)


# what stops a dormer being BUILT, as opposed to merely being worth a note
OVER_RIDGE = "over_ridge"          # a GABLE's ridge is above the host's ridge
FACES_UPHILL = "faces_uphill"      # the host does not rise along its ridge
TOO_STEEP = "too_steep"            # a SHED's plane is not shallower than the host
NOT_DOWNHILL = "not_downhill"      # the ridge is off the host's fall line
FACING_TOL_DEG = 1.5               # how far off straight-downhill still counts


def unbuildable(st, host_z_face=None, host_slope=None, host_ridge_in=None,
                offaxis_deg=None):
    """Why this dormer must NOT be built on this host -- `OVER_RIDGE`,
    `FACES_UPHILL`, `TOO_STEEP`, `NOT_DOWNHILL` -- or None. ONE RULE FOR THE
    DIALOG AND THE 3D BUILDER (0359): what the dialog refuses, the builder
    skips.

    A GABLE's ridge AT the host's ridge height is allowed (ridge to ridge is an
    ordinary cross gable); above it is `OVER_RIDGE` (also the astride-the-ridge
    case). A SHED is different (Patrick, 2026-11-18): it touches the host only
    along its back ridge, so it MAY sit above the host ridge -- but its plane
    must be SHALLOWER than the host (`TOO_STEEP` otherwise) or it never dies
    into the host. A dormer must also face STRAIGHT DOWN the slope: more than
    `FACING_TOL_DEG` off the host's fall line is `NOT_DOWNHILL` (Patrick,
    2026-11-18, P2). `offaxis_deg` is the angle between the ridge and the fall
    line, which only the item knows. With no host there is nothing to be wrong
    about: None."""
    if host_z_face is None or host_slope is None:
        return None
    if host_slope <= _EPS:
        return FACES_UPHILL
    if offaxis_deg is not None and abs(offaxis_deg) > FACING_TOL_DEG:
        return NOT_DOWNHILL
    if st["form"] == "shed":
        return TOO_STEEP if _rise(st) >= host_slope - _EPS else None
    if host_ridge_in is not None and ridge_height(st) > float(host_ridge_in) + 1e-6:
        return OVER_RIDGE
    return None


# --------------------------------------------------------------------------
# heights
# --------------------------------------------------------------------------
def spans(st):
    return st["span_left_in"], st["span_right_in"]


def _rise(st):
    """Rise per inch of the dormer's own roof slope (pitch-12 as a ratio)."""
    return st["pitch_12"] / 12.0


def ridge_height(st):
    """Above the dormer's level. For a gable the pitch is the LEFT plane's,
    rising across the half-width; for a SHED the single plane rises along the
    DEPTH, so its back ridge is host-free the stored `depth_in` away."""
    if st["form"] == "shed":
        return st["eaves_h_in"] + _rise(st) * st["depth_in"]
    return st["eaves_h_in"] + st["span_left_in"] * st["pitch_12"] / 12.0


def _ridge_run(st):
    """The run the pitch climbs to reach the ridge: a gable's HALF-WIDTH (the
    left plane), a SHED's DEPTH (its one plane rises along the depth)."""
    return st["depth_in"] if st["form"] == "shed" else st["span_left_in"]


def couple_ridge(st, ridge, pinned):
    """Hold the ridge at `ridge` by floating whichever of eaves/pitch is NOT
    `pinned` (the 3-way anchor: the ridge is the anchor, the last-edited of
    eaves/pitch is pinned, the other gives way). Form-aware -- a gable climbs
    over the half-width, a shed over the depth. Returns a normalized state;
    `ridge` None leaves it unchanged."""
    out = normalize_state(st)
    if ridge is None:
        return out
    run = _ridge_run(out)
    if run <= _EPS:
        return out
    ridge = float(ridge)
    if pinned == "eaves_h_in":          # eaves held, pitch takes the slack
        out["pitch_12"] = max((ridge - out["eaves_h_in"]) * 12.0 / run, 0.5)
    else:                               # pitch held (default), eaves gives way
        out["eaves_h_in"] = max(ridge - run * out["pitch_12"] / 12.0, 0.0)
    return normalize_state(out)


def slopes(st):
    """(left, right) rise per inch of run. A SHED's single plane has the one
    slope both sides; a gable's two planes fall from one ridge to one eaves
    height, so unequal spans mean unequal slopes."""
    if st["form"] == "shed":
        return _rise(st), _rise(st)
    rise = ridge_height(st) - st["eaves_h_in"]
    left, right = spans(st)
    return (rise / left if left > _EPS else 0.0,
            rise / right if right > _EPS else 0.0)


def surface_height(st, x):
    """The dormer roof's height at local across-coordinate `x` (left +). A
    SHED's roof is level across the width -- at the FACE it is the eaves."""
    if st["form"] == "shed":
        return st["eaves_h_in"]
    sl, sr = slopes(st)
    return ridge_height(st) - (sl * x if x >= 0.0 else sr * -x)


def shed_back(st, host_z_face=None, host_slope=None):
    """A SHED's single plane rises from the FACE back along the depth; its high
    back edge -- the ridge -- meets the host as ONE line. Returns (depth,
    ridge_height, met): where it meets (or the stored `depth_in` with no host),
    the back height there, and whether it met a host. To meet, the dormer must
    be SHALLOWER than the host (Patrick, 2026-11-18)."""
    rise, eaves = _rise(st), st["eaves_h_in"]
    if (host_z_face is not None and host_slope is not None
            and host_slope - rise > _EPS and eaves - host_z_face > _EPS):
        y = (eaves - host_z_face) / (host_slope - rise)
        return y, eaves + rise * y, True
    return st["depth_in"], eaves + rise * st["depth_in"], False


def back_height(st, host_z_face=None, host_slope=None):
    """The dormer's high edge above its level: a gable's ridge (host-free), or
    a shed's back edge where it meets the host (or its stored depth)."""
    if st["form"] == "shed":
        return shed_back(st, host_z_face, host_slope)[1]
    return ridge_height(st)


# --------------------------------------------------------------------------
# meeting the host roof
# --------------------------------------------------------------------------
def host_plane(surface_height_at, pos, direction, step=12.0):
    """(height at the face, slope along the ridge) of whatever roof is under
    the dormer, from a callable `surface_height_at((x, y))` in plan
    coordinates and in the DORMER'S datum. `direction` is the ridge's unit
    vector. Sampled, so it suits any host; a caller with an analytic plane
    can skip this and pass its own two numbers."""
    z0 = float(surface_height_at(pos))
    z1 = float(surface_height_at((pos[0] + direction[0] * step,
                                  pos[1] + direction[1] * step)))
    return z0, (z1 - z0) / step


def host_extent(host_z_face=None, host_slope=None, host_ridge_in=None,
                host_eave_in=None):
    """Along the dormer's ridge direction (local +Y runs uphill into the host),
    where the host roof's EAVE and RIDGE fall, as signed distances from the
    face: `ridge_y` the host ridge (uphill, >= 0), `eave_y` the host eave
    (downhill, <= 0 when the face is above the eave, > 0 once the face hangs
    past it). The ANCHOR may travel between them -- past the ridge is
    OVER_RIDGE, past the eave the face hangs off the roof (P1 of the 2026-11-18
    control redesign). None with no host or one that does not rise along the
    ridge; a missing ridge/eave height leaves that entry None."""
    if host_z_face is None or host_slope is None or host_slope <= _EPS:
        return None
    ridge_y = (None if host_ridge_in is None
               else (float(host_ridge_in) - host_z_face) / host_slope)
    eave_y = (None if host_eave_in is None
              else -(host_z_face - float(host_eave_in)) / host_slope)
    return {"eave_y": eave_y, "ridge_y": ridge_y}


def ridge_depth(st, host_z_face=None, host_slope=None):
    """How far the ridge runs (gable) / how deep the plane reaches (shed)
    before it meets the host -- or the stored `depth_in` with no host. A
    shed's back edge meets the host where the shallower plane catches it.
    Returns (depth, met)."""
    if st["form"] == "shed":
        y, _rh, met = shed_back(st, host_z_face, host_slope)
        return y, met
    if host_z_face is None or host_slope is None or host_slope <= _EPS:
        return st["depth_in"], False
    gap = ridge_height(st) - host_z_face
    if gap <= _EPS:
        return 0.0, True                 # the host is already over the ridge
    return gap / host_slope, True


def _meet_y(height, host_z_face, host_slope):
    """Where the host plane reaches `height`, along the ridge from the face."""
    return (height - host_z_face) / host_slope


def valley_lines(st, host_z_face=None, host_slope=None):
    """The lines where the dormer's planes meet the host, local coordinates:
    `{"left": [(x, y), (x, y)], "right": [...]}`, each from its outer end to
    the ridge's end. A side whose eave stands ABOVE the host at the face has
    a CHEEK: the valley then starts back from the face, at the point the host
    climbs to the dormer's eaves height. `{}` with no host, or for a SHED --
    whose single plane touches the host only along its back ridge, not down
    the sides (Patrick, 2026-11-18)."""
    if st["form"] == "shed":
        return {}
    depth, met = ridge_depth(st, host_z_face, host_slope)
    if not met or depth <= _EPS:
        return {}
    out = {}
    for name, sign, span, slope in (("left", 1.0, st["span_left_in"], slopes(st)[0]),
                                    ("right", -1.0, st["span_right_in"], slopes(st)[1])):
        if span <= _EPS or slope <= _EPS:
            continue
        # across-distance at which this plane is down to the host AT THE FACE
        u_face = (ridge_height(st) - host_z_face) / slope
        u = min(span, u_face)
        y = max(_meet_y(ridge_height(st) - slope * u, host_z_face, host_slope), 0.0)
        out[name] = [(sign * u, y), (0.0, depth)]
    return out


def knee_lines(st, ceiling_in, host_z_face=None, host_slope=None):
    """THE ONE THING A DORMER COMPUTES FOR THE PLAN: where its planes cross
    the ceiling height `ceiling_in` (above the dormer's level). Local
    segments `[((x, y), (x, y)), ...]`, at most one per side, each parallel
    to the ridge, from the face back to the valley.

    None on a side whose eaves-start line is already at or above the ceiling
    -- the room is full height right out to that side -- and none at all
    when the ceiling is at or above the ridge."""
    rh = back_height(st, host_z_face, host_slope)
    if ceiling_in >= rh - _EPS:
        return []
    depth, met = ridge_depth(st, host_z_face, host_slope)
    if st["form"] == "shed":
        # the single plane rises along the depth; it crosses the ceiling on ONE
        # line ACROSS the width, at the depth where z(y) reaches the ceiling.
        rise = _rise(st)
        if rise <= _EPS:
            return []
        y = (ceiling_in - st["eaves_h_in"]) / rise
        if y <= _EPS or y >= depth - _EPS:
            return []
        return [((-st["span_right_in"], y), (st["span_left_in"], y))]
    out = []
    for sign, span, slope in ((1.0, st["span_left_in"], slopes(st)[0]),
                              (-1.0, st["span_right_in"], slopes(st)[1])):
        if span <= _EPS or slope <= _EPS:
            continue
        u = (rh - ceiling_in) / slope
        if u >= span - _EPS:
            continue
        end = depth
        if met:
            end = min(depth, max(_meet_y(ceiling_in, host_z_face, host_slope), 0.0))
        if end > _EPS:
            out.append(((sign * u, 0.0), (sign * u, end)))
    return out


def full_height_width(st, ceiling_in):
    """Width under the dormer where the roof is at or above `ceiling_in`. A
    SHED is full WIDTH behind its knee, so its full-height measure is the
    whole width once the back rises above the ceiling."""
    rh = ridge_height(st)
    if ceiling_in >= rh - _EPS:
        return 0.0
    if st["form"] == "shed":
        return st["span_left_in"] + st["span_right_in"]
    total = 0.0
    for span, slope in zip(spans(st), slopes(st), strict=False):
        if span > _EPS and slope > _EPS:
            total += min(span, (rh - ceiling_in) / slope)
    return total


# --------------------------------------------------------------------------
# the plan
# --------------------------------------------------------------------------
def footprint(st, depth):
    """The dormer roof's plan outline, local: eave overhangs and the face
    overhang included, back to the end of the ridge."""
    left = st["span_left_in"] + st["eave_overhang_left_in"]
    right = st["span_right_in"] + st["eave_overhang_right_in"]
    front = -st["face_overhang_in"]
    return [(-right, front), (left, front), (left, depth), (-right, depth)]


def guides(st):
    """Control C as GUIDES, not walls: the two side lines the user draws their
    own walls against. Local x of (left, right). The old face guide D is
    RETIRED (P3, 2026-11-18) -- the purple knob now sets the face DISTANCE
    (`depth_in`), so a face wall stands at the face itself."""
    left = st["guide_left_in"] if st["guide_left_in"] > _EPS else st["span_left_in"]
    right = st["guide_right_in"] if st["guide_right_in"] > _EPS else st["span_right_in"]
    return (min(left, st["span_left_in"]), min(right, st["span_right_in"]))


def plan(st, ceiling_in=None, host_z_face=None, host_slope=None):
    """Everything the plan item draws, local coordinates:

        ridge    ((x, y), (x, y))
        eaves    [((x, y), (x, y))]      the eave edges, overhang included
        rake     ((x, y), (x, y))        the face edge, overhang included
        guides   [((x, y), (x, y))]      side and face guides (controls C, D)
        valleys  [((x, y), (x, y))]
        knees    [((x, y), (x, y))]      [] when no ceiling height is given
    """
    depth, _met = ridge_depth(st, host_z_face, host_slope)
    fp = footprint(st, depth)
    gl, gr = guides(st)
    shed = st["form"] == "shed"
    # BOTH side eaves and BOTH side guides, for a gable and a shed alike
    # (Patrick, 2026-11-18): the shed is a full box with two symmetric
    # trapezoid sides, so it carries a left AND a right eave and side guide.
    # The side guides run from the FACE back to the host (the face guide D is
    # retired -- the purple knob now sets the face distance).
    eaves = [(fp[1], fp[2]), (fp[0], fp[3])]
    lines = [((gl, 0.0), (gl, depth)), ((-gr, 0.0), (-gr, depth))]
    # the RIDGE: a gable's runs down the middle, from the face into the host;
    # a shed's is its high BACK edge across the width -- its ONLY host contact.
    ridge = (fp[2], fp[3]) if shed else ((0.0, 0.0), (0.0, depth))
    return {
        "ridge": ridge,
        "eaves": eaves,
        "rake": (fp[0], fp[1]),
        "guides": lines,
        "valleys": [tuple(v) for v in valley_lines(st, host_z_face,
                                                   host_slope).values()],
        "knees": ([] if ceiling_in is None
                  else knee_lines(st, ceiling_in, host_z_face, host_slope)),
    }


# --------------------------------------------------------------------------
# the face: the gable end seen from outside, and the openings in it
# --------------------------------------------------------------------------
FACE_TOL_IN = 6.0        # how far off the face guide a wall may stand and count
OPENING_SHAPES = ("rect", "octagon", "round")


def roof_height_at(st, x):
    """The roof's underside line over the face at across-coordinate `x`, or
    None where there is no roof plane over it (a shed's high side, x < 0)."""
    if x < -_EPS and st["span_right_in"] <= _EPS:
        return None
    return surface_height(st, x)


def face_profile(st, host_z_face=None, host_slope=None):
    """The gable end (or the shed FRONT) in ELEVATION, seen from OUTSIDE:
    points `(x, z)`, x the across-coordinate (the ridge's left is the viewer's
    RIGHT), z above the dormer's level.

        roof      the roof line, eave to peak to eave, overhangs included
        wall      the outline a face wall fills between the side guides:
                  floor, up each guide, along the roof line through the peak
        peak      (x, z) of the ridge

    A SHED reads front-on as a RECTANGULAR face wall (to the eaves) with the
    single roof plane behind it drawn as a band up to the back ridge, level
    across the width (Patrick, 2026-11-18). The back ridge needs the host, so
    a shed face takes the host plane; a gable ignores it."""
    if st["form"] == "shed":
        eaves = st["eaves_h_in"]
        back = back_height(st, host_z_face, host_slope)
        gl, gr = guides(st)
        left = st["span_left_in"] + st["eave_overhang_left_in"]
        right = st["span_right_in"] + st["eave_overhang_right_in"]
        wall = [(gl, 0.0), (gl, eaves), (-gr, eaves), (-gr, 0.0)]
        roof = [(left, eaves), (left, back), (-right, back), (-right, eaves)]
        return {"roof": roof, "wall": wall, "peak": (0.0, back)}
    rh = ridge_height(st)
    sl, sr = slopes(st)
    gl, gr = guides(st)
    left = st["span_left_in"] + st["eave_overhang_left_in"]
    roof = [(0.0, rh), (left, rh - sl * left)]
    wall = [(gl, 0.0), (gl, rh - sl * gl), (0.0, rh)]
    if st["span_right_in"] > _EPS:
        right = st["span_right_in"] + st["eave_overhang_right_in"]
        roof.insert(0, (-right, rh - sr * right))
        wall += [(-gr, rh - sr * gr), (-gr, 0.0)]
    else:
        wall.append((0.0, 0.0))
    return {"roof": roof, "wall": wall, "peak": (0.0, rh)}


def project_wall(pos, rotation_deg, p1, p2, guide_face=0.0, tol=FACE_TOL_IN):
    """A wall's two ends as across-coordinates `(x1, x2)` on the dormer's
    face -- or None when the wall is not a FACE wall: not square to the ridge
    (within `tol` over its length) or not within `tol` of the face guide."""
    (x1, y1), (x2, y2) = to_local(pos, rotation_deg, p1), to_local(pos, rotation_deg, p2)
    if abs(y1 - y2) > tol or abs(x1 - x2) <= _EPS:
        return None
    if abs((y1 + y2) / 2.0 - guide_face) > tol:
        return None
    return x1, x2


def project_openings(x1, x2, wall_length, openings):
    """A face wall's openings in across-coordinates. `x1`, `x2` are the
    wall's ends from `project_wall`; each opening carries `s0`, `s1` (inches
    from the wall's FIRST end to its two edges) and `sill_in`, `head_in`
    above the dormer's level. Everything else on it (`id`, `kind`, `code`,
    `shape`) is carried through."""
    out = []
    if wall_length <= _EPS:
        return out
    for op in openings:
        a = x1 + (x2 - x1) * float(op["s0"]) / wall_length
        b = x1 + (x2 - x1) * float(op["s1"]) / wall_length
        rec = {k: v for k, v in op.items() if k not in ("s0", "s1")}
        rec["x0"], rec["x1"] = min(a, b), max(a, b)
        out.append(rec)
    return out


def _corners(op):
    """The points of an opening that must stay under the roof. An octagon's
    and a round window's top corners are cut back, so a small one fits
    higher in a gable than its bounding box would."""
    x0, x1, head = op["x0"], op["x1"], op["head_in"]
    shape = op.get("shape", "rect")
    if shape not in ("octagon", "round"):
        return [(x0, head), (x1, head)]
    w, h = x1 - x0, head - op["sill_in"]
    cut = 0.2929                      # 1 - 1/sqrt(2): a regular octagon's corner
    return [(x0 + w * cut, head), (x1 - w * cut, head),
            (x0, head - h * cut), (x1, head - h * cut)]


def _judge(openings, top_at, ceiling_in, wall_span):
    out = []
    for i, op in enumerate(openings):
        rec = dict(op)
        rec.setdefault("id", i)
        rec["shape"] = op.get("shape") if op.get("shape") in OPENING_SHAPES else "rect"
        through = False
        for x, z in _corners(rec):
            top = top_at(x)
            if top is None or z > top + 1e-6:
                through = True
        rec["through_roof"] = through
        rec["above_ceiling"] = (ceiling_in is not None
                                and rec["head_in"] > ceiling_in + 1e-6)
        rec["off_wall"] = (wall_span is not None
                           and (rec["x0"] < min(wall_span) - 1e-6
                                or rec["x1"] > max(wall_span) + 1e-6))
        rec["overlaps"] = []
        out.append(rec)
    for a in out:
        for b in out:
            if a is not b and (a["x0"] < b["x1"] - 1e-6 and b["x0"] < a["x1"] - 1e-6
                               and a["sill_in"] < b["head_in"] - 1e-6
                               and b["sill_in"] < a["head_in"] - 1e-6):
                a["overlaps"].append(b["id"])
    out.sort(key=lambda r: (r["sill_in"], r["x0"]))
    return out


def face_openings(st, openings, ceiling_in=None, wall_span=None):
    """Each opening in the face, judged against THIS dormer's gable. Input
    records are `project_openings`' (x0, x1, sill_in, head_in, ...); each
    comes back with:

        through_roof    a top corner is above the roof line, or beside it
        above_ceiling   its head is above `ceiling_in`. NOT a fault: the
                        gable rises above the ceiling line and a window may
                        sit up there -- reported so the drawing can say so
        off_wall        it is outside `wall_span` (the face wall's x extent)
        overlaps        ids (or indexes) of openings whose rectangles cross
                        this one's. Two openings STACKED one above the other
                        do not overlap

    Sorted bottom to top, then left to right."""
    return _judge(openings, lambda x: roof_height_at(st, x), ceiling_in, wall_span)


# -- the two sides (the cheeks) ----------------------------------------------
SIDES = ("left", "right")


def side_x(st, side):
    """The across-coordinate of a side guide. A shed's RIGHT side is its
    high wall, under the ridge."""
    gl, gr = guides(st)
    return gl if side == "left" else -gr


def side_top(st, side):
    """Where the roof meets a wall standing on that side guide."""
    if side == "right" and st["span_right_in"] <= _EPS:
        return ridge_height(st)
    return surface_height(st, side_x(st, side))


def side_profile(st, side, host_z_face=None, host_slope=None):
    """One side wall in ELEVATION, seen from outside: points `(y, z)`, y
    along the ridge from the face.

        wall    the rectangle a side wall fills: from the face guide back to
                where the host roof climbs to the wall's top
        roof    the dormer's eave line over it, face overhang included
        host    the host roof's line across it, or None with no host. BELOW
                this line the wall is inside the main roof, not outdoors
        ridge   the dormer's OWN roof in this projection, a HIDDEN line: the
                ridge at the top, the front rake hanging over the face by the
                overhang, the back dying into the host roof. A true left
                projection, not just the cheek wall (Patrick, 0361)
        span    (y0, y1) of the wall;  top  its height

    A SHED side is a TRAPEZOID -- low at the face, high at the back where the
    single plane meets the host; its roof is the VISIBLE sloping top (no hidden
    ridge line) and the host diagonal is the reference (Patrick, 2026-11-18)."""
    if st["form"] == "shed":
        eaves = st["eaves_h_in"]
        fo = st["face_overhang_in"]
        rise = _rise(st)
        depth, back, met = shed_back(st, host_z_face, host_slope)
        host = ([(0.0, host_z_face), (depth, host_z_face + host_slope * depth)]
                if met else None)
        return {
            "wall": [(0.0, 0.0), (0.0, eaves), (depth, back), (depth, 0.0)],
            "roof": [(-fo, eaves - rise * fo), (depth, back)],
            "host": host, "ridge": None, "span": (0.0, depth), "top": back}
    top = side_top(st, side)
    rh = ridge_height(st)
    fo = st["face_overhang_in"]
    depth, met = ridge_depth(st, host_z_face, host_slope)
    y0 = 0.0                             # the side wall runs from the FACE
    y1 = depth
    host = None
    if met and depth > _EPS:
        y1 = min(max(_meet_y(top, host_z_face, host_slope), y0), depth)
        host = [(y0, host_z_face + host_slope * y0), (y1, host_z_face + host_slope * y1)]
    # the roof silhouette seen from the side: front eave corner (over the
    # face) -> up the front rake to the ridge -> back along the ridge to where
    # it meets the host -> down the host roof to where the eave meets it. The
    # back two legs run ALONG the host roof; with no host the end squares off.
    ridge = [(-fo, top), (-fo, rh), (depth, rh), (y1, top)]
    return {"wall": [(y0, 0.0), (y0, top), (y1, top), (y1, 0.0)],
            "roof": [(-fo, top), (y1, top)],
            "host": host, "ridge": ridge, "span": (y0, y1), "top": top}


def project_side_wall(pos, rotation_deg, p1, p2, x_side, tol=FACE_TOL_IN):
    """A wall's two ends as along-ridge coordinates `(y1, y2)` -- or None
    when it is not a wall on that side guide: not parallel to the ridge
    (within `tol`) or not within `tol` of `x_side`."""
    (x1, y1), (x2, y2) = to_local(pos, rotation_deg, p1), to_local(pos, rotation_deg, p2)
    if abs(x1 - x2) > tol or abs(y1 - y2) <= _EPS:
        return None
    if abs((x1 + x2) / 2.0 - x_side) > tol:
        return None
    return y1, y2


def side_openings(st, side, openings, ceiling_in=None, wall_span=None,
                  host_z_face=None, host_slope=None):
    """`face_openings` for a side wall: records from `project_openings` fed
    `project_side_wall`'s ends, so `x0`/`x1` here run ALONG THE RIDGE. Adds

        behind_host    part of its sill is under the host roof's line: that
                       part looks into the main roof, not outdoors
    """
    top = side_top(st, side)
    out = _judge(openings, lambda _y: top, ceiling_in, wall_span)
    for rec in out:
        rec["behind_host"] = (
            host_z_face is not None and host_slope is not None
            and host_z_face + host_slope * rec["x1"] > rec["sill_in"] + 1e-6)
    return out


# --------------------------------------------------------------------------
# local <-> plan, and the record the roof code already reads
# --------------------------------------------------------------------------
def ridge_direction(rotation_deg):
    """The ridge's unit vector in plan coordinates (y down the screen)."""
    r = math.radians(rotation_deg)
    return math.sin(r), -math.cos(r)


def to_plan(pos, rotation_deg, pt):
    """A local point as a plan point."""
    ux, uy = ridge_direction(rotation_deg)
    nx, ny = -uy, ux                       # the ridge's LEFT
    return (pos[0] + ux * pt[1] + nx * pt[0], pos[1] + uy * pt[1] + ny * pt[0])


def to_local(pos, rotation_deg, pt):
    ux, uy = ridge_direction(rotation_deg)
    nx, ny = -uy, ux
    dx, dy = pt[0] - pos[0], pt[1] - pos[1]
    return dx * nx + dy * ny, dx * ux + dy * uy


def to_roof_record(st, pos, rotation_deg, depth, datum_shift=0.0, **extra):
    """The dormer as the `roof` record `roofclip.RoofGeom.from_record` and
    the 3D builder already take -- so the clipper, the host cut and the roof
    mesh need no new geometry code. `datum_shift` is added to both heights:
    this level's elevation minus the elevation of whatever datum the caller
    composes in. `ridge[0]` is the FACE, as the roof code expects of a
    dormer. `extra` (an `id`, a `level`, a `host`) is merged in."""
    gl, gr = guides(st)
    rec = {
        "ridge": [list(pos), list(to_plan(pos, rotation_deg, (0.0, depth)))],
        "eaves_h_in": st["eaves_h_in"] + datum_shift,
        "ridge_h_in": ridge_height(st) + datum_shift,
        "span_in": [st["span_left_in"], st["span_right_in"]],
        "overhang_in": [st["eave_overhang_left_in"], st["eave_overhang_right_in"]],
        "end_overhang_in": [st["face_overhang_in"], 0.0],
        "wall_span_in": [gl, gr],
        "eaves_bind": "manual", "gable": [True, True], "marker_end": 0,
        "form": st["form"],
        "dormer_walls": [],              # a furnishing dormer mints no wall
    }
    if st["box_left_in"] > _EPS or st["box_right_in"] > _EPS:
        rec["box_half_in"] = [st["box_left_in"] or st["span_left_in"],
                              st["box_right_in"] or st["span_right_in"]]
    rec.update(extra)
    return rec


def from_roof_record(rec, datum_shift=0.0):
    """(state, pos, rotation_deg, depth) from an OLD dormer record -- a
    `roofs[]` entry with a `host` -- for the conversion on load. The inverse
    of `to_roof_record`; `datum_shift` is subtracted from the heights."""
    (x0, y0), (x1, y1) = rec["ridge"]
    dx, dy = x1 - x0, y1 - y0
    depth = math.hypot(dx, dy)
    rotation = math.degrees(math.atan2(dx, -dy)) % 360.0 if depth > _EPS else 0.0

    def pair(value, default):
        if isinstance(value, (list, tuple)):
            return float(value[0]), float(value[1])
        if value is None:
            return default
        return float(value), float(value)

    form = rec.get("form", "gable") if rec.get("form") in FORMS else "gable"
    sl, sr = pair(rec.get("span_in"), (60.0, 60.0))
    ol, orr = pair(rec.get("overhang_in"), (0.0, 0.0))
    face, _back = pair(rec.get("end_overhang_in"), (0.0, 0.0))
    gl, gr = pair(rec.get("wall_span_in"), (0.0, 0.0))
    bl, br = pair(rec.get("box_half_in"), (0.0, 0.0))
    eaves = float(rec.get("eaves_h_in", 96.0)) - datum_shift
    ridge = float(rec.get("ridge_h_in", 132.0)) - datum_shift
    st = {"form": form, "span_left_in": sl, "span_right_in": sr,
          "symmetric": form != "shed" and abs(sl - sr) < 1e-6
          and abs(ol - orr) < 1e-6 and abs(gl - gr) < 1e-6,
          "eaves_h_in": eaves,
          "pitch_12": (ridge - eaves) / sl * 12.0 if sl > _EPS else 0.0,
          "eave_overhang_left_in": ol, "eave_overhang_right_in": orr,
          "face_overhang_in": face,
          "guide_left_in": 0.0 if abs(gl - sl) < 1e-6 else gl,
          "guide_right_in": 0.0 if abs(gr - sr) < 1e-6 else gr,
          "box_left_in": bl, "box_right_in": br, "depth_in": max(depth, 1.0)}
    return normalize_state(st), (float(x0), float(y0)), rotation, depth
