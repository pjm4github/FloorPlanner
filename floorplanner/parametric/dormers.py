"""The DORMER parametric kind (0352): its parameters, what its dialog
reports, and its findings. The arithmetic is `dormer_geometry.py`.

REGISTERED (0352 phase 2) now that `DormerItem` draws one and the catalog
offers it in the Framing group: a drag from the palette places it, a
double-click opens the generic dialog. Phase 1 built the kind but withheld
`register()` so nothing offered a dormer before one could be drawn.

`context` (all optional) is what the item knows about where it stands:

    ceiling_in         the ceiling of the room it is over, above this level
    host_z_face_in     the host roof's height at the dormer's face, this
                       level's datum; absent = it is over no roof
    host_slope         the host's rise per inch along the dormer's ridge
    host_ridge_in      the host's ridge height, this level's datum
    face_wall          (x1, x2): the across-extent of the wall the user drew
                       under the face (`dg.project_wall`); None = looked, and
                       there is none; absent = nobody looked
    face_openings      that wall's openings (`dg.project_openings`)
    side_walls         {"left": (y1, y2) | None, "right": ...}: the same for
                       the walls on the two side guides (`dg.project_side_wall`)
    side_openings      {"left": [...], "right": [...]}
    wall_below         (x1, x2): the across-extent of an exterior wall on the
                       floor BELOW, under the face (`dg.project_wall`); None =
                       looked and found none / no lower floor; absent = nobody
                       looked. Drives the plain-wall / setback reading.
    room_below         True/False: a room is defined on the floor below under
                       the dormer; None = no lower floor. Drives the P5 warning.
"""
from floorplanner.parametric import dormer_geometry as dg
from floorplanner.parametric.findings import ADVISORY, ERROR, WARNING, Finding
from floorplanner.parametric.params import BOOL, ENUM, FLOAT, ParamSpec
from floorplanner.parametric.registry import ParametricKind, register


def _fmt(x, places=2):
    return f"{x:.{places}f}".rstrip("0").rstrip(".")


def _free_right(values):
    # a shed and a gable both have two sides; the right follows the left until
    # the dormer is made asymmetric (Patrick, 2026-11-18).
    return not values.get("symmetric")


def _host(context):
    c = context or {}
    try:
        return float(c["host_z_face_in"]), float(c["host_slope"])
    except (KeyError, TypeError, ValueError):
        return None, None


def _ceiling(context):
    try:
        return float((context or {}).get("ceiling_in"))
    except (TypeError, ValueError):
        return None


class DormerKind(ParametricKind):
    kind = "dormer"
    title = "Dormer Properties"

    def specs(self):
        d = dg.STATE_DEFAULTS

        def size(key, label, lo, hi, step=1.0, tip="", enabled=None):
            return ParamSpec(key, label, FLOAT, d[key], unit="in", minimum=lo,
                             maximum=hi, step=step, tooltip=tip,
                             enabled_fn=enabled)

        return [
            ParamSpec("form", "Form", ENUM, d["form"],
                      choices=(("gable", "Gable"), ("shed", "Shed")),
                      tooltip="A gable has two planes meeting at a ridge. A "
                              "SHED has one plane rising from the face back to "
                              "a high ridge at the back, where it meets the "
                              "host roof -- shallower than the host."),
            ParamSpec("symmetric", "Symmetric", BOOL, d["symmetric"],
                      tooltip="The right side takes the left side's numbers."),
            ParamSpec("face_mode", "Face type", ENUM, d["face_mode"],
                      choices=(("auto", "Auto (from geometry)"),
                               ("plain_wall", "Plain wall"),
                               ("setback", "Setback"),
                               ("balcony", "Balcony")),
                      tooltip="How the face meets the house below. AUTO reads it "
                              "from the geometry: CANTILEVER when the eave is past "
                              "the roof edge, SETBACK when host roof shows in "
                              "front, PLAIN WALL when flush with a wall below. "
                              "Pick one to force it; a note warns when the "
                              "geometry cannot support the pick."),
            size("span_left_in", "Half-width, left", dg.MIN_SPAN_IN, 480.0,
                 tip="Ridge to the eaves line (knob B / G)."),
            size("span_right_in", "Half-width, right", dg.MIN_SPAN_IN, 480.0,
                 enabled=_free_right),
            ParamSpec("ridge_h_in", "Ridge height", FLOAT, dg.ridge_height(d),
                      unit="in", minimum=0.0, maximum=600.0, step=0.5,
                      tooltip="The ridge above THIS level's floor -- the ANCHOR. "
                              "Edit it and whichever of the eaves / pitch you did "
                              "NOT set last gives way to hold the geometry."),
            size("eaves_h_in", "Eaves height", 0.0, 360.0, 0.5,
                 "The eaves line above THIS level's floor. Edit it and the PITCH "
                 "gives way, the ridge held."),
            ParamSpec("pitch_12", "Pitch", FLOAT, d["pitch_12"], unit="in 12",
                      minimum=0.5, maximum=24.0, step=0.5,
                      tooltip="Rise per 12 in of run, on the left plane. Edit it "
                              "and the EAVES give way, the ridge held."),
            size("eave_overhang_left_in", "Eave overhang, left", 0.0, 60.0,
                 tip="Knob E."),
            size("eave_overhang_right_in", "Eave overhang, right", 0.0, 60.0,
                 enabled=_free_right),
            size("face_overhang_in", "Eave past the face", 0.0, 240.0,
                 tip="The eave of the face, past the face wall — out to and "
                     "beyond the host roof edge (knob F, orange)."),
            size("guide_left_in", "Side guide, left", 0.0, 480.0,
                 tip="Knob C, as a guide line only: where a side wall would "
                     "stand. 0 = on the eaves line. It draws no wall."),
            size("guide_right_in", "Side guide, right", 0.0, 480.0,
                 enabled=_free_right),
            size("depth_in", "Face distance", 1.0, 600.0,
                 tip="How far the FACE WALL stands down the roof from the anchor "
                     "(knob D, purple). The anchor sits on the host; this is the "
                     "roof's run from the ridge to the face."),
        ]

    def normalize(self, state):
        # Ridge, eaves and pitch are all editable; the RIDGE is the ANCHOR.
        # Between eaves and pitch, whichever was edited LAST is pinned and the
        # other FLOATS to hold the ridge (Patrick, 2026-11-18):
        #   edit pitch -> eaves floats;  edit eaves -> pitch floats;
        #   edit ridge -> the one NOT pinned floats.
        # `ridge_h_in` is a dialog-only input `to_state` drops; `_pinned`
        # remembers the last of {eaves, pitch} the user set. `_edited` is the
        # dialog's hint of the field just changed.
        st = dict(state or {})
        edited = st.pop("_edited", None)
        ridge = st.pop("ridge_h_in", None)
        pinned = st.pop("_pinned", None)
        if edited in ("eaves_h_in", "pitch_12"):
            pinned = edited
        if pinned not in ("eaves_h_in", "pitch_12"):
            pinned = "pitch_12"             # default: pitch pinned, eaves floats
        norm = dg.normalize_state(st)
        if ridge is not None:
            try:
                norm = dg.couple_ridge(norm, float(ridge), pinned)
            except (TypeError, ValueError):
                pass
        norm = dict(norm)
        norm["ridge_h_in"] = dg.ridge_height(norm)
        norm["_pinned"] = pinned
        return norm

    def to_state(self, values):
        st = dg.normalize_state(values)
        return {k: st[k] for k in dg.STATE_DEFAULTS}

    def evaluate(self, values, context):
        st = dg.normalize_state(values)
        findings = []
        if st["pitch_12"] <= 0.0:
            findings.append(Finding("dormer.flat", ERROR,
                                    "A dormer needs a pitch above zero.",
                                    field="pitch_12"))
            return None, findings
        z_face, slope = _host(context)
        ceiling = _ceiling(context)
        rh = dg.back_height(st, z_face, slope)   # a shed's ridge needs the host
        depth, met = dg.ridge_depth(st, z_face, slope)
        derived = {
            "state": st, "ridge_h_in": rh, "slopes": dg.slopes(st),
            "depth_in": depth, "on_roof": met,
            "valleys": dg.valley_lines(st, z_face, slope),
            "knees": ([] if ceiling is None
                      else dg.knee_lines(st, ceiling, z_face, slope)),
            "full_height_in": (None if ceiling is None
                               else dg.full_height_width(st, ceiling)),
            "footprint": dg.footprint(st, depth), "ceiling_in": ceiling,
        }
        eave_h = (context or {}).get("host_eave_in")
        wall_below = bool((context or {}).get("wall_below"))
        choice = st.get("face_mode", "auto")
        ftype, supported = dg.classify_face(st, z_face, slope, eave_h, wall_below, choice)
        derived["face_type"] = ftype
        derived["wall_below"] = wall_below
        if ftype == dg.FACE_CANTILEVER:
            past = dg.face_past_eave(st, z_face, slope, eave_h)
            findings.append(Finding(
                "dormer.cantilever", ADVISORY,
                f"The face stands {_fmt(past)} in past the host roof edge: "
                "this is a cantilever (hanging) dormer.",
                field="depth_in"))
        if choice != "auto" and not supported:
            why = {"plain_wall": "needs an exterior wall below the face and the "
                                 "face at the roof edge",
                   "setback": "needs the face set back up the roof",
                   "balcony": "needs the face set back, with roof in front to cut"}
            findings.append(Finding(
                "dormer.face_unsupported", WARNING,
                f"A {choice.replace('_', ' ')} dormer {why.get(choice, '')} here; "
                f"the dormer reads as a {ftype.replace('_', ' ')} instead.",
                field="face_mode"))
        # P5 (Patrick, 2026-11-19): a prominent warning when the storey beneath
        # the face is undefined. The face-type reading and the 3D build both
        # need to know the house is there; a CANTILEVER is the one face that
        # SHOULD have nothing below, so it is exempt. `looked_below` is set once
        # the item's probe has run (absent = nobody looked, e.g. a bare state).
        room_below = (context or {}).get("room_below")
        looked_below = "wall_below" in (context or {})
        if (z_face is not None and looked_below and ftype != dg.FACE_CANTILEVER
                and not wall_below and not room_below):
            findings.append(Finding(
                "dormer.nothing_below", WARNING,
                "No room or exterior wall is defined on the floor below this "
                "dormer, so the storey under its face is undefined. The 3D model "
                "cannot tell how the face meets the house (plain wall, setback or "
                "balcony). Draw the room and its walls below, or set the face "
                "type.", field="face_mode"))
        if z_face is None:
            findings.append(Finding(
                "dormer.no_host", WARNING,
                "This dormer is not over a roof. It is drawn "
                f"{_fmt(st['depth_in'])} in long and cuts nothing.",
                field="depth_in"))
        elif depth <= 0.0 and slope > 0.0:
            findings.append(Finding(
                "dormer.buried", WARNING,
                f"The roof here is already {_fmt(z_face)} in up, at or above "
                f"this dormer's ridge ({_fmt(rh)} in). Nothing of it shows. "
                "Raise the eaves or the pitch, or move it down the slope.",
                actual=rh, limit=z_face, field="eaves_h_in"))
        host_ridge = (context or {}).get("host_ridge_in")
        offaxis = (context or {}).get("host_offaxis_deg")
        why = dg.unbuildable(st, z_face, slope, host_ridge, offaxis)
        derived["unbuildable"] = why
        if why == dg.FACES_UPHILL:
            findings.append(Finding(
                "dormer.level_host", ERROR,
                "The roof under this dormer does not rise along its ridge: it "
                "is facing up the slope, or sitting over the main ridge. Turn "
                "it to face down the slope, or move it down the roof."))
        elif why == dg.OVER_RIDGE:
            fitted = dg.fit_under_ridge(st, float(host_ridge))
            findings.append(Finding(
                "dormer.above_host_ridge", ERROR,
                f"The dormer's ridge ({_fmt(rh)} in) is above the main roof's "
                f"ridge ({_fmt(float(host_ridge))} in). Narrow it to "
                f"{_fmt(fitted['span_left_in'])} in a side, lower the pitch, "
                "or lower the eaves.", actual=rh, limit=float(host_ridge),
                field="span_left_in"))
        elif why == dg.TOO_STEEP:
            findings.append(Finding(
                "dormer.too_steep", ERROR,
                f"This shed dormer's slope ({_fmt(st['pitch_12'])} in 12) is "
                f"not shallower than the host roof ({_fmt(slope * 12.0)} in 12), "
                "so its back never dies into the host. Lower the pitch.",
                actual=st["pitch_12"], limit=slope * 12.0, field="pitch_12"))
        elif why == dg.NOT_DOWNHILL:
            findings.append(Finding(
                "dormer.not_downhill", ERROR,
                f"This dormer faces {_fmt(offaxis)} deg off straight down the "
                "slope. Turn it to face down the fall line of the roof it sits "
                "on."))
        if ceiling is not None and derived["full_height_in"] <= 0.0:
            findings.append(Finding(
                "dormer.no_full_height", ADVISORY,
                f"The ridge ({_fmt(rh)} in) is not above the {_fmt(ceiling)} in "
                "ceiling: this dormer adds no full-height floor.",
                actual=rh, limit=ceiling, field="eaves_h_in"))
        self._face(st, context or {}, ceiling, derived, findings)
        return derived, findings

    @staticmethod
    def _face(st, context, ceiling, derived, findings):
        """The gable end (or shed front) and what stands in it (0356)."""
        z_face, slope = _host(context)
        wall = context.get("face_wall")
        derived["face_profile"] = dg.face_profile(st, z_face, slope)
        derived["face_wall"] = tuple(wall) if wall else None
        derived["face_openings"] = dg.face_openings(
            st, context.get("face_openings") or [], ceiling,
            tuple(wall) if wall else None)
        if "face_wall" in context and not wall:
            findings.append(Finding(
                "dormer.face_open", ADVISORY,
                "No wall is drawn under this dormer's face. Draw one on the "
                "face guide and it will rise to the gable; its windows and "
                "doors will show here."))
        z_face, slope = _host(context)
        walls = context.get("side_walls") or {}
        given = context.get("side_openings") or {}
        derived["sides"] = {}
        for side in dg.SIDES:
            span = walls.get(side)
            derived["sides"][side] = {
                "profile": dg.side_profile(st, side, z_face, slope),
                "wall": tuple(span) if span else None,
                "openings": dg.side_openings(
                    st, side, given.get(side) or [], ceiling,
                    tuple(span) if span else None, z_face, slope)}
            if "side_walls" in context and not span:
                findings.append(Finding(
                    f"dormer.side_open.{side}", ADVISORY,
                    f"No wall is drawn under this dormer's {side} side."))
        groups = [("face", derived["face_openings"],
                   lambda op: min((dg.roof_height_at(st, x) or 0.0)
                                  for x in (op["x0"], op["x1"])))]
        groups += [(f"{side} side", derived["sides"][side]["openings"],
                    lambda _op, side=side: dg.side_top(st, side))
                   for side in dg.SIDES]
        for where, ops, top_of in groups:
            for op in ops:
                name = f"{op.get('kind', 'opening')} {op.get('code', op['id'])}"
                if op["through_roof"]:
                    top = top_of(op)
                    findings.append(Finding(
                        "dormer.opening_through_roof", WARNING,
                        f"The {name} in the {where} rises to "
                        f"{_fmt(op['head_in'])} in, but the roof over it is at "
                        f"{_fmt(top)} in. Lower it, narrow it, move it toward "
                        "the ridge, or raise the dormer.",
                        actual=op["head_in"], limit=top))
                if op["overlaps"] and str(op["id"]) < str(op["overlaps"][0]):
                    findings.append(Finding(
                        "dormer.openings_overlap", WARNING,
                        f"The {name} overlaps another opening in the {where}. "
                        "Stacked openings need the lower one's head under the "
                        "upper one's sill."))
                if op.get("behind_host"):
                    findings.append(Finding(
                        "dormer.opening_behind_roof", ADVISORY,
                        f"The {name} in the {where} is partly below the main "
                        "roof's line: that part looks into the roof, not "
                        "outdoors."))

    def summary(self, values, derived, context):
        if derived is None:
            return [("Result", "cannot be built")]
        st = derived["state"]
        sl, sr = derived["slopes"]
        rows = [("Ridge height", f"{_fmt(derived['ridge_h_in'])} in above this floor"),
                ("Pitch", f"{_fmt(sl * 12.0)} in 12"
                          + ("" if st["form"] == "shed" or abs(sl - sr) < 1e-9
                             else f" left, {_fmt(sr * 12.0)} in 12 right")),
                ("Ridge length", f"{_fmt(derived['depth_in'])} in"
                                 + (" (to the roof)" if derived["on_roof"]
                                    else " (not on a roof)"))]
        if derived["ceiling_in"] is not None:
            rows.append(("Full height under it",
                         f"{_fmt(derived['full_height_in'])} in wide at the "
                         f"{_fmt(derived['ceiling_in'])} in ceiling"))
            for (x, _y0), (_x, y1) in derived["knees"]:
                rows.append((f"Knee line, {'left' if x > 0 else 'right'}",
                             f"{_fmt(abs(x))} in from the ridge, "
                             f"{_fmt(y1)} in long"))
            if not derived["knees"] and derived["full_height_in"] > 0.0:
                rows.append(("Knee lines", "none: full height to both sides"))
        ops = derived.get("face_openings") or []
        if ops:
            high = sum(1 for o in ops if o["above_ceiling"])
            rows.append(("Openings in the face",
                         f"{len(ops)}" + (f", {high} above the ceiling line "
                                          "(in the gable)" if high else "")))
        elif derived.get("face_wall"):
            rows.append(("Openings in the face", "none"))
        for side in dg.SIDES:
            info = (derived.get("sides") or {}).get(side) or {}
            if info.get("openings"):
                rows.append((f"Openings in the {side} side",
                             str(len(info["openings"]))))
        return rows


    def make_preview(self, parent=None):
        from floorplanner.parametric.dormer_view import DormerFaceView  # late: Qt
        return DormerFaceView(parent)


DORMER = register(DormerKind())
