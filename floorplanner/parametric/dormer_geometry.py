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
    "depth_in": 96.0,              # ridge length, used only when no roof is under it
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
    for key in _NUMBERS:
        try:
            v = float(src.get(key, STATE_DEFAULTS[key]))
        except (TypeError, ValueError):
            v = STATE_DEFAULTS[key]
        out[key] = v if math.isfinite(v) else STATE_DEFAULTS[key]
    out["span_left_in"] = max(out["span_left_in"], MIN_SPAN_IN)
    if out["form"] == "shed":
        # one plane: the ridge is the high edge, the roof falls to the LEFT
        out["span_right_in"] = 0.0
        out["eave_overhang_right_in"] = 0.0
        out["guide_right_in"] = 0.0
        out["box_right_in"] = 0.0
        out["symmetric"] = False
    else:
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


def default_state(ceiling_in=None, host_slope=None):
    """A newly dropped dormer: its eaves a foot under the ceiling it lights,
    and the host's own pitch when there is a host."""
    st = dict(STATE_DEFAULTS)
    if ceiling_in is not None:
        st["eaves_h_in"] = max(float(ceiling_in) - 12.0, 12.0)
    if host_slope is not None and host_slope > _EPS:
        st["pitch_12"] = round(host_slope * 12.0, 3)
    return st


# --------------------------------------------------------------------------
# heights
# --------------------------------------------------------------------------
def spans(st):
    return st["span_left_in"], st["span_right_in"]


def ridge_height(st):
    """Above the dormer's level. The pitch is the LEFT plane's."""
    return st["eaves_h_in"] + st["span_left_in"] * st["pitch_12"] / 12.0


def slopes(st):
    """(left, right) rise per inch of run. Both planes fall from one ridge
    to one eaves height, so unequal spans mean unequal slopes."""
    rise = ridge_height(st) - st["eaves_h_in"]
    left, right = spans(st)
    return (rise / left if left > _EPS else 0.0,
            rise / right if right > _EPS else 0.0)


def surface_height(st, x):
    """The dormer roof's height at local across-coordinate `x` (left +)."""
    sl, sr = slopes(st)
    return ridge_height(st) - (sl * x if x >= 0.0 else sr * -x)


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


def ridge_depth(st, host_z_face=None, host_slope=None):
    """How far the ridge runs before it meets the host -- or the stored
    `depth_in` when there is no host, or the host never rises to the ridge.
    Returns (depth, met)."""
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
    climbs to the dormer's eaves height. `{}` with no host."""
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
    rh = ridge_height(st)
    if ceiling_in >= rh - _EPS:
        return []
    depth, met = ridge_depth(st, host_z_face, host_slope)
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
    """Width under the dormer where the roof is at or above `ceiling_in`."""
    rh = ridge_height(st)
    if ceiling_in >= rh - _EPS:
        return 0.0
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
    """Controls C and D as GUIDES, not walls: the two side lines and the face
    line the user draws their own walls against. Local x of (left, right)
    and the face's y (always 0)."""
    left = st["guide_left_in"] if st["guide_left_in"] > _EPS else st["span_left_in"]
    right = st["guide_right_in"] if st["guide_right_in"] > _EPS else st["span_right_in"]
    return min(left, st["span_left_in"]), min(right, st["span_right_in"]), 0.0


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
    gl, gr, gf = guides(st)
    eaves = [(fp[1], fp[2])]
    lines = [((gl, gf), (gl, depth))]
    if st["form"] != "shed":
        eaves.append((fp[0], fp[3]))
        lines.append(((-gr, gf), (-gr, depth)))
    lines.append(((-gr, gf), (gl, gf)))
    return {
        "ridge": ((0.0, 0.0), (0.0, depth)),
        "eaves": eaves,
        "rake": (fp[0], fp[1]),
        "guides": lines,
        "valleys": [tuple(v) for v in valley_lines(st, host_z_face,
                                                   host_slope).values()],
        "knees": ([] if ceiling_in is None
                  else knee_lines(st, ceiling_in, host_z_face, host_slope)),
    }


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
    gl, gr, _gf = guides(st)
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
