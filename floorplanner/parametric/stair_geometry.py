"""Stair geometry -- pure Python, the ONE calculator.

NO Qt AND NO `floorplanner` IMPORT, on purpose: the 3D viewer loads this file
BY PATH (as it loads `roofclip.py`), so the plan symbol, the properties
dialog and the 3D solid are all drawn from the same `StairGeometry` and cannot
disagree about how many risers a stair has.

THE CONVENTION (docs/furnishing-spec/STAIRS_FURNISHING_SPECIFICATION.md sec 3,
sec 5): `N` risers climb a rise `H`; a flight that ends at a floor or a landing
has ONE FEWER tread than risers, because that floor or landing is its top
step. A straight stair therefore has `N - 1` treads and a run of
`(N - 1) * d`; an L or U stair, with one landing, has `N - 2`.

NATURAL COORDINATES (inches). The first flight starts at the origin and rises
along +Y; its width runs 0..W along +X. This is the editor's frame, y DOWN the
screen. `turn_deg` is the plan angle the stair turns through at its landing:
POSITIVE puts the second flight on the +X side (a walker's LEFT), NEGATIVE on
the -X side. Heights are measured up from the stair's own lower floor.
"""
import math
from dataclasses import dataclass

STAIR_TYPES = ("straight", "L", "U")
TURNS = {"straight": (0,), "L": (90, -90), "U": (180, -180)}

DEFAULT_TREAD_IN = 11.0
DEFAULT_WIDTH_IN = 36.0
DEFAULT_DETACHED_RISE_IN = 108.0
DEFAULT_PROFILE = "irc_residential_example"

# Construction details of the 3D solid -- appearance only, never dimensions
# the calculation reads.
TREAD_T_IN = 1.0            # tread board thickness
NOSING_IN = 1.0             # tread projection past the riser below it
RISER_T_IN = 0.75           # riser board thickness
STRINGER_T_IN = 1.5         # stringer thickness, across the stair
STRINGER_DROP_IN = 9.25     # stringer depth below the tread line (a 2x10)
LANDING_T_IN = 1.5          # landing deck thickness
POST_IN = 3.5               # landing post, square

_EPS = 1e-9
_LEVEL_EPS = 1e-6


class StairError(ValueError):
    """An input the calculation cannot use. `field` names the offending
    parameter so a dialog can put the cursor on it."""

    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field


@dataclass(frozen=True)
class StairCodeProfile:
    """Dimensional limits for preliminary checking. NOT a legal determination:
    these are common IRC-derived residential defaults, and the adopted local
    code, edition and amendments govern (spec sec 6.1)."""
    profile_id: str
    title: str
    max_riser_in: float
    min_tread_in: float
    min_width_in: float
    max_riser_variation_in: float
    min_headroom_in: float
    max_flight_rise_in: float
    comfort_lo_in: float
    comfort_hi_in: float


PROFILES = {
    DEFAULT_PROFILE: StairCodeProfile(
        profile_id=DEFAULT_PROFILE,
        title="IRC residential (example defaults -- confirm local code)",
        max_riser_in=7.75, min_tread_in=10.0, min_width_in=36.0,
        max_riser_variation_in=0.375, min_headroom_in=80.0,
        max_flight_rise_in=151.0, comfort_lo_in=24.0, comfort_hi_in=25.0),
}


def profile_for(state):
    """The state's code profile; the default one for an id nothing defines."""
    pid = (state or {}).get("code_profile") or DEFAULT_PROFILE
    return PROFILES.get(pid, PROFILES[DEFAULT_PROFILE])


@dataclass(frozen=True)
class StairInputs:
    total_rise: float
    tread_depth: float
    stair_width: float
    riser_count_override: int | None = None
    stair_type: str = "straight"
    turn_deg: int = 0
    landing_height: float | None = None     # None = half way up


@dataclass(frozen=True)
class Flight:
    """One straight run. `origin` is its foot corner, `u` the unit direction
    of travel and `v` the unit direction across the width, so tread `k`
    (1-based) covers `origin + u*[(k-1)d, kd] + v*[0, W]`."""
    risers: int
    treads: int
    run: float
    z0: float                   # height at the foot
    origin: tuple
    u: tuple
    v: tuple


@dataclass(frozen=True)
class StairGeometry:
    stair_type: str
    turn_deg: int
    total_rise: float
    tread_depth: float
    stair_width: float
    riser_count: int
    riser_height: float
    tread_count: int
    total_run: float            # the sum of the flights' runs
    pitch_degrees: float
    comfort_index: float        # 2h + d
    footprint_length: float     # along the first flight's travel (Y)
    footprint_width: float      # across it (X)
    bbox: tuple                 # (x0, y0, x1, y1), natural coordinates
    flights: tuple
    landing: tuple | None       # (x, y, w, h) plan rect, or None
    landing_height: float | None
    landing_risers: int         # risers below the landing; 0 when none


# --------------------------------------------------------------------------
# the calculation
# --------------------------------------------------------------------------
def _positive(value, name, field):
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise StairError(f"{name} is not a number", field) from None
    if not math.isfinite(v):
        raise StairError(f"{name} must be a finite number", field)
    if v <= 0.0:
        raise StairError(f"{name} must be greater than zero", field)
    return v


def auto_riser_count(total_rise, max_riser_height):
    """The FEWEST risers that keep each at or under the maximum (spec sec 5).
    The epsilon is for float noise at an exact boundary: 15.5 / 7.75 is 2
    risers, not 3."""
    return max(1, math.ceil(total_rise / max_riser_height - 1e-10))


def calculate_stair_geometry(inputs, max_riser_height):
    """`StairInputs` -> `StairGeometry`, or `StairError` for input that is
    not a stair at all. A result is not a verdict: whether the stair is
    ACCEPTABLE is `stairs.validate_stairway`'s business, not this
    function's -- a 9-inch riser calculates perfectly well."""
    H = _positive(inputs.total_rise, "Total rise", "total_rise_in")
    d = _positive(inputs.tread_depth, "Tread depth", "tread_depth_in")
    W = _positive(inputs.stair_width, "Stair width", "stair_width_in")
    h_max = _positive(max_riser_height, "Maximum riser height", None)
    kind = inputs.stair_type
    if kind not in STAIR_TYPES:
        raise StairError(f"unknown stair type {kind!r}", "type")
    turn = int(inputs.turn_deg or 0)
    if kind == "straight":
        turn = 0
    elif turn not in TURNS[kind]:
        raise StairError(f"a {kind} stair turns {TURNS[kind][0]} or "
                         f"{TURNS[kind][1]} degrees, not {turn}", "turn_deg")

    if inputs.riser_count_override is None:
        N = auto_riser_count(H, h_max)
        if kind != "straight":
            N = max(N, 2)
    else:
        try:
            N = int(inputs.riser_count_override)
        except (TypeError, ValueError):
            raise StairError("Riser count is not a whole number",
                             "riser_count") from None
        if N < 1:
            raise StairError("Riser count must be at least 1", "riser_count")
        if kind != "straight" and N < 2:
            raise StairError("A stair with a landing needs at least 2 risers",
                             "riser_count")
    h = H / N

    side = 1.0 if turn > 0 else -1.0
    flights, landing, landing_h, n1 = [], None, None, 0
    if kind == "straight":
        flights.append(Flight(N, N - 1, (N - 1) * d, 0.0,
                              (0.0, 0.0), (0.0, 1.0), (1.0, 0.0)))
    else:
        want = H / 2.0 if inputs.landing_height is None else inputs.landing_height
        try:
            want = float(want)
        except (TypeError, ValueError):
            raise StairError("Landing height is not a number",
                             "landing_height_in") from None
        if not math.isfinite(want):
            raise StairError("Landing height must be a finite number",
                             "landing_height_in")
        # A landing can only sit a WHOLE number of risers up -- the risers of
        # one stair are equal -- so the requested height snaps to the nearest.
        # Half-way ties go DOWN (floor(x + 0.5 - eps)), so 7 of 14 is 7.
        n1 = int(math.floor(want / h + 0.5 - _EPS))
        n1 = min(max(n1, 1), N - 1)
        landing_h = n1 * h
        t1 = n1 - 1
        run1 = t1 * d
        flights.append(Flight(n1, t1, run1, 0.0,
                              (0.0, 0.0), (0.0, 1.0), (1.0, 0.0)))
        n2 = N - n1
        t2 = n2 - 1
        run2 = t2 * d
        if kind == "L":
            landing = (0.0, run1, W, W)
            origin = (W, run1) if side > 0 else (0.0, run1)
            flights.append(Flight(n2, t2, run2, landing_h, origin,
                                  (side, 0.0), (0.0, 1.0)))
        else:                                   # U: back beside the first
            x0 = 0.0 if side > 0 else -W
            landing = (x0, run1, 2.0 * W, W)
            origin = (W, run1) if side > 0 else (-W, run1)
            flights.append(Flight(n2, t2, run2, landing_h, origin,
                                  (0.0, -1.0), (1.0, 0.0)))

    xs, ys = [], []
    for f in flights:
        for x, y in flight_rect(f, W):
            xs.append(x)
            ys.append(y)
    if landing is not None:
        xs += [landing[0], landing[0] + landing[2]]
        ys += [landing[1], landing[1] + landing[3]]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    treads = sum(f.treads for f in flights)
    return StairGeometry(
        stair_type=kind, turn_deg=turn, total_rise=H, tread_depth=d,
        stair_width=W, riser_count=N, riser_height=h, tread_count=treads,
        total_run=sum(f.run for f in flights),
        pitch_degrees=math.degrees(math.atan2(h, d)),
        comfort_index=2.0 * h + d,
        footprint_length=bbox[3] - bbox[1], footprint_width=bbox[2] - bbox[0],
        bbox=bbox, flights=tuple(flights), landing=landing,
        landing_height=landing_h, landing_risers=n1)


def _pt(f, s, a):
    """The plan point `s` along flight `f`'s travel and `a` across it."""
    return (f.origin[0] + f.u[0] * s + f.v[0] * a,
            f.origin[1] + f.u[1] * s + f.v[1] * a)


def flight_rect(f, width):
    """The four plan corners of a flight's footprint."""
    return [_pt(f, 0.0, 0.0), _pt(f, f.run, 0.0),
            _pt(f, f.run, width), _pt(f, 0.0, width)]


def _norm_rect(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


# --------------------------------------------------------------------------
# the plan symbol
# --------------------------------------------------------------------------
def plan(geom):
    """The plan symbol's primitives, natural coordinates:

        rects   [(x, y, w, h)]        each flight, then the landing
        steps   [(x1, y1, x2, y2)]    the lines BETWEEN treads
        line    [(x, y)]              the travel arrow's polyline, foot to top
        label   (x, y)                where UP / DN is written

    A flight of `t` treads draws `t - 1` interior lines; its two ends are the
    rectangle's own edges, so it shows exactly `t` tread spaces."""
    W, d = geom.stair_width, geom.tread_depth
    rects, steps, line = [], [], []
    for f in geom.flights:
        if f.run > _EPS:
            rects.append(_norm_rect(flight_rect(f, W)))
        for k in range(1, f.treads):
            a, b = _pt(f, k * d, 0.0), _pt(f, k * d, W)
            steps.append((a[0], a[1], b[0], b[1]))
    if geom.landing is not None:
        rects.append(tuple(geom.landing))

    first = geom.flights[0]
    start = _pt(first, min(d * 0.5, first.run * 0.5), W / 2.0)
    line.append(start)
    if geom.landing is None:
        line.append(_pt(first, max(first.run - d * 0.5, first.run * 0.5), W / 2.0))
    else:
        second = geom.flights[1]
        lx, ly, lw, lh = geom.landing
        mid_y = ly + lh / 2.0
        line.append((W / 2.0, mid_y))                       # onto the landing
        if geom.stair_type == "U":
            line.append((second.origin[0] + W / 2.0, mid_y))  # across it
        if second.run > _EPS:
            line.append(_pt(second, max(second.run - d * 0.5, second.run * 0.5),
                            W / 2.0))
        elif geom.stair_type == "L":
            line.append((lx + lw / 2.0 + second.u[0] * lw * 0.3, mid_y))
    if len(line) < 2 or line[-1] == line[-2]:
        line.append((line[-1][0], line[-1][1] + max(d * 0.25, 1.0)))
    return {"rects": rects, "steps": steps, "line": line,
            "label": (W / 2.0 + 1.0, min(d * 0.5, max(first.run, d) * 0.5))}


# --------------------------------------------------------------------------
# the 3D solid
# --------------------------------------------------------------------------
def solids(geom):
    """The stair as simple solids, natural plan coordinates, heights up from
    the stair's lower floor. Two shapes:

        ("box",   [(x, y)] * 4, z0, z1)                 an upright prism
        ("prism", [(x, y, z)] * 4, [(x, y, z)] * 4)     two matching quads,
                                                        joined -- a stringer

    Built from the SAME `StairGeometry` the plan symbol and the dialog use."""
    W, d, h = geom.stair_width, geom.tread_depth, geom.riser_height
    out = []
    for f in geom.flights:
        for k in range(1, f.treads + 1):                 # tread boards
            top = f.z0 + k * h
            s0 = (k - 1) * d - (NOSING_IN if k > 1 or f.z0 > 0.0 else 0.0)
            out.append(("box", [_pt(f, s0, 0.0), _pt(f, k * d, 0.0),
                                _pt(f, k * d, W), _pt(f, s0, W)],
                        top - TREAD_T_IN, top))
        for k in range(1, f.risers + 1):                 # riser boards
            lo = f.z0 + (k - 1) * h
            hi = f.z0 + k * h - TREAD_T_IN
            if hi - lo <= _EPS:
                continue
            s0 = (k - 1) * d
            if k > f.treads:                 # the last one, under the landing
                s0 = max(f.run - RISER_T_IN, 0.0)
            out.append(("box", [_pt(f, s0, 0.0), _pt(f, s0 + RISER_T_IN, 0.0),
                                _pt(f, s0 + RISER_T_IN, W), _pt(f, s0, W)],
                        lo, hi))
        if f.treads >= 1 and W > 2.0 * STRINGER_T_IN:    # two stringers
            zt = f.z0 + f.treads * h
            if f.z0 <= _EPS:
                # the foot stands on the floor: the lower edge is cut level
                s_cut = min(STRINGER_DROP_IN * d / h, f.run)
                prof = [(0.0, f.z0), (f.run, zt),
                        (f.run, max(zt - STRINGER_DROP_IN, f.z0)), (s_cut, f.z0)]
            else:
                prof = [(0.0, f.z0), (f.run, zt),
                        (f.run, zt - STRINGER_DROP_IN),
                        (0.0, f.z0 - STRINGER_DROP_IN)]
            for a0 in (0.0, W - STRINGER_T_IN):
                near = [(*_pt(f, s, a0), z) for s, z in prof]
                far = [(*_pt(f, s, a0 + STRINGER_T_IN), z) for s, z in prof]
                out.append(("prism", near, far))
    if geom.landing is not None and geom.landing_height is not None:
        x, y, w, hh = geom.landing
        zl = geom.landing_height
        out.append(("box", [(x, y), (x + w, y), (x + w, y + hh), (x, y + hh)],
                    max(zl - LANDING_T_IN, 0.0), zl))
        under = zl - LANDING_T_IN
        if under > POST_IN and w > 2 * POST_IN and hh > 2 * POST_IN:
            for px in (x, x + w - POST_IN):
                for py in (y, y + hh - POST_IN):
                    out.append(("box", [(px, py), (px + POST_IN, py),
                                        (px + POST_IN, py + POST_IN),
                                        (px, py + POST_IN)], 0.0, under))
    return out


def developed_profile(geom):
    """The stair UNFOLDED along its line of travel, for a side elevation:
    `[(kind, s0, s1, z0, z1, flight)]` with kind 'riser', 'tread' or
    'landing'. `s` is distance walked, `z` height. A straight stair's
    developed profile is its true elevation; an L or U stair's is the same
    drawing with the turn laid flat."""
    d, h = geom.tread_depth, geom.riser_height
    segs, s = [], 0.0
    for i, f in enumerate(geom.flights):
        z = f.z0
        for k in range(1, f.risers + 1):
            segs.append(("riser", s, s, z, z + h, i))
            z += h
            if k <= f.treads:
                segs.append(("tread", s, s + d, z, z, i))
                s += d
        if i == 0 and geom.landing is not None:
            segs.append(("landing", s, s + geom.stair_width, z, z, i))
            s += geom.stair_width
    return segs


# --------------------------------------------------------------------------
# the stored state
# --------------------------------------------------------------------------
STATE_DEFAULTS = {
    "type": "straight",
    "turn_deg": 0,
    "direction": "up",
    "rise_mode": "detached",
    "total_rise_in": DEFAULT_DETACHED_RISE_IN,
    "tread_depth_in": DEFAULT_TREAD_IN,
    "stair_width_in": DEFAULT_WIDTH_IN,
    "riser_count_mode": "auto",
    "riser_count": 14,
    "landing_mode": "half",
    "landing_height_in": DEFAULT_DETACHED_RISE_IN / 2.0,
    "code_profile": DEFAULT_PROFILE,
}


def is_parametric_state(state):
    """True for a furnishing `state` that carries stair PARAMETERS. A stair
    saved before parameters existed has only flight / turn / direction, and
    stays on the old rules until it is edited (Patrick, 2026-11-14)."""
    return isinstance(state, dict) and state.get("type") in STAIR_TYPES


def _num(value, default):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


def normalize_state(state):
    """A complete, type-clean copy of a stored state. Missing keys take their
    defaults and a nonsense enum falls back, so a hand-edited file cannot
    crash the item; numbers are NOT clamped here -- an out-of-range value is
    the validator's to report, not this function's to hide. Keys this
    version does not know are carried through untouched."""
    src = dict(state or {})
    out = dict(src)
    d = STATE_DEFAULTS
    kind = src.get("type") if src.get("type") in STAIR_TYPES else d["type"]
    out["type"] = kind
    try:
        turn = int(src.get("turn_deg", 0) or 0)
    except (TypeError, ValueError):
        turn = 0
    out["turn_deg"] = turn if turn in TURNS[kind] else TURNS[kind][0]
    out["direction"] = (src.get("direction")
                        if src.get("direction") in ("up", "down") else "up")
    out["rise_mode"] = (src.get("rise_mode")
                        if src.get("rise_mode") in ("linked", "detached")
                        else d["rise_mode"])
    for key in ("total_rise_in", "tread_depth_in", "stair_width_in",
                "landing_height_in"):
        out[key] = _num(src.get(key), d[key])
    out["riser_count_mode"] = (src.get("riser_count_mode")
                               if src.get("riser_count_mode") in ("auto", "manual")
                               else "auto")
    try:
        out["riser_count"] = int(src.get("riser_count", d["riser_count"]))
    except (TypeError, ValueError):
        out["riser_count"] = d["riser_count"]
    out["landing_mode"] = (src.get("landing_mode")
                           if src.get("landing_mode") in ("half", "custom")
                           else "half")
    out["code_profile"] = str(src.get("code_profile") or DEFAULT_PROFILE)
    return out


def next_level_rise(this_elev, elevations):
    """Floor-to-floor rise to the NEXT LEVEL ABOVE `this_elev`, or None when
    nothing stands above it. The editor and the viewer both ask this, so they
    cannot pick different upper floors."""
    best = None
    for e in elevations:
        try:
            gap = float(e) - float(this_elev)
        except (TypeError, ValueError):
            continue
        if gap > _LEVEL_EPS and (best is None or gap < best):
            best = gap
    return best


def effective_rise(state, this_elev=0.0, elevations=()):
    """(rise, linked_ok). A LINKED stair takes the rise to the next level
    above; with no level above it falls back to its stored rise and says so
    with `linked_ok = False`. A detached stair always reports True."""
    st = normalize_state(state)
    if st["rise_mode"] == "linked":
        rise = next_level_rise(this_elev, elevations)
        if rise is not None:
            return rise, True
        return st["total_rise_in"], False
    return st["total_rise_in"], True


def default_state(this_elev=0.0, elevations=()):
    """The state of a NEWLY PLACED stair: linked to the level above when
    there is one, detached at 108 in when there is not."""
    st = dict(STATE_DEFAULTS)
    rise = next_level_rise(this_elev, elevations)
    if rise is not None:
        st["rise_mode"] = "linked"
        st["total_rise_in"] = rise
        st["landing_height_in"] = rise / 2.0
    return st


def inputs_from_state(state, total_rise):
    st = normalize_state(state)
    return StairInputs(
        total_rise=total_rise,
        tread_depth=st["tread_depth_in"],
        stair_width=st["stair_width_in"],
        riser_count_override=(st["riser_count"]
                              if st["riser_count_mode"] == "manual" else None),
        stair_type=st["type"],
        turn_deg=st["turn_deg"],
        landing_height=(st["landing_height_in"]
                        if st["landing_mode"] == "custom" else None))


def geometry_from_state(state, this_elev=0.0, elevations=()):
    """(geometry, rise, linked_ok) straight from a stored state. Raises
    `StairError` exactly as `calculate_stair_geometry` does."""
    st = normalize_state(state)
    rise, linked_ok = effective_rise(st, this_elev, elevations)
    geom = calculate_stair_geometry(inputs_from_state(st, rise),
                                    profile_for(st).max_riser_in)
    return geom, rise, linked_ok
