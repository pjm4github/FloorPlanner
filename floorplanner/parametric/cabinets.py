"""The CABINET and APPLIANCE parametric kinds (0329).

One definition class serves every catalog kind `cabinet_geometry.PRESETS`
names: a `base_cab_36` and a `wall_cab_24` differ only in the preset they are
born from, and so in which parameters their dialog offers. The arithmetic and
the style vocabulary are `cabinet_geometry.py`, shared with the 3D viewer.
"""
from floorplanner.parametric import cabinet_geometry as cg
from floorplanner.parametric.findings import ADVISORY, ERROR, Finding
from floorplanner.parametric.params import BOOL, ENUM, FLOAT, INT, ParamSpec
from floorplanner.parametric.registry import ParametricKind, register

_FROM_ROOM = (cg.ROOM, "From the room's style")


def _choices(table, with_room=True):
    rows = tuple((row[0], row[1]) for row in table)
    return ((_FROM_ROOM,) + rows) if with_room else rows


def _fmt(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


def _is_custom(values):
    return values.get("finish_mode") == "custom"


def _has_top(values):
    return bool(values.get("top_on"))


def _never(_values):
    return False


def _is_lit(values):
    return values.get("light_style", "none") != "none"


def _has_storage(values):
    return bool(values.get("has_cabinet"))


def _is_pendant(values):
    return values.get("fixture") == "pendant"


def _is_sconce(values):
    return values.get("fixture") in ("sconce", "table")


def _has_drop(values):
    return values.get("fixture") in ("pendant", "table")


def _shown_width(_values, derived, _context):
    return None if derived is None else derived["footprint"][0]


class CabinetKind(ParametricKind):
    def __init__(self, kind):
        self.kind = kind
        self.preset = cg.preset_for(kind)
        self.type = self.preset.get("type", "base")
        self.title = {"appliance": "Appliance Properties",
                      "island": "Island Properties",
                      "light": "Light Properties",
                      "fixture": "Fixture Properties",
                      "mirror": "Mirror / Wall Unit"}.get(self.type,
                                                       "Cabinet Properties")

    # -- parameters ----------------------------------------------------------
    def specs(self):
        d = cg.normalize_state({}, self.preset)
        t = self.type
        if t == "light":
            return [
                ParamSpec("fixture", "Shape", ENUM, d["fixture"],
                          choices=cg.FIXTURES),
                ParamSpec("size_in", "Size", FLOAT, d["size_in"], unit="in",
                          minimum=2.0, maximum=120.0, step=1.0,
                          tooltip="Diameter, or the length of a linear light."),
                ParamSpec("light_colour", "Light colour", ENUM, d["light_colour"],
                          choices=tuple((k, label) for k, label, _h
                                        in cg.LIGHT_COLOURS)),
                ParamSpec("lumens", "Output", FLOAT, d["lumens"], unit="lm",
                          minimum=0.0, maximum=20000.0, step=100.0, decimals=0,
                          tooltip="800 lm is about a 60 W bulb. 0 switches the "
                                  "source off and keeps the fixture."),
                ParamSpec("beam", "Beam", ENUM, d["beam"],
                          choices=(("wide", "Wide (all round)"),
                                   ("spot", "Spot (downward)")),
                          enabled_fn=lambda v: v.get("fixture") not in (
                              "sconce", "table")),
                ParamSpec("drop_in", "Drop / lamp height", FLOAT, d["drop_in"],
                          unit="in", minimum=4.0, maximum=120.0, step=1.0,
                          enabled_fn=_has_drop,
                          tooltip="A pendant: how far it hangs below the "
                                  "ceiling. A table lamp: how tall it is."),
                ParamSpec("floor_to_bottom_in", "Height from floor", FLOAT,
                          d["floor_to_bottom_in"], unit="in", minimum=0.0,
                          maximum=144.0, step=1.0, enabled_fn=_is_sconce),
            ]
        if t == "mirror":
            return self._mirror_specs(d)
        if t == "fixture":
            return self._fixture_specs(d)
        if t == "appliance" and d.get("appliance") in ("washer", "dryer"):
            labels = {k: label for k, label, _h in cg.COLOURS}
            return [ParamSpec("colour", "Gloss finish", ENUM, d["colour"],
                              choices=tuple((k, labels[k])
                                            for k in cg.LAUNDRY_COLOURS))]
        if t == "appliance":
            custom = _is_custom
            mounted = ([ParamSpec(
                "floor_to_bottom_in", "Height from floor", FLOAT,
                d["floor_to_bottom_in"], unit="in", minimum=0.0, maximum=120.0,
                step=1.0, tooltip="Floor to the underside. Over a 36 in range, "
                                  "54 in leaves 18 in; a hood usually sits "
                                  "24 to 30 in above the cooktop.")]
                       if d.get("wall_mounted") else [])
            return mounted + [
                ParamSpec("finish_mode", "Finish", ENUM, d["finish_mode"],
                          choices=(("standard", "Standard (stainless)"),
                                   ("match", "Match the room's cabinets"),
                                   ("custom", "Custom colour")),
                          tooltip="Match: the appliance takes the cabinet finish "
                                  "of the room it stands in."),
                ParamSpec("sheen", "Sheen", ENUM, d["sheen"],
                          choices=cg.SHEENS, enabled_fn=custom),
                ParamSpec("colour", "Colour", ENUM, d["colour"],
                          choices=tuple((k, label) for k, label, _h in cg.COLOURS),
                          enabled_fn=custom),
            ]
        if t == "island":
            slots = tuple((row[0], row[1]) for row in cg.ISLAND_SLOTS)
            out = [ParamSpec(key, f"Under the island, {i}", ENUM, d[key],
                             choices=slots,
                             tooltip="Left to right as seen from the door side. "
                                     "The island is as long as what stands "
                                     "under it.")
                   for i, key in enumerate(cg.ISLAND_SLOT_KEYS, start=1)]
            out += [
                ParamSpec("width_in", "Length", FLOAT, d["width_in"], unit="in",
                          minimum=6.0, maximum=400.0, enabled_fn=_never,
                          shown_fn=_shown_width),
                ParamSpec("depth_in", "Depth", FLOAT, d["depth_in"], unit="in",
                          minimum=27.0, maximum=72.0, step=1.0,
                          tooltip="Cabinets are 24 in deep; the rest overhangs "
                                  "the seating side."),
                ParamSpec("seats", "Seats", INT, d["seats"], minimum=0, maximum=8,
                          step=1, tooltip="Short-backed stools along the side "
                                          "away from the doors."),
                ParamSpec("finish_mode", "Appliances under it", ENUM,
                          d["finish_mode"],
                          choices=(("standard", "Stainless"),
                                   ("match", "Match the cabinets"))),
                ParamSpec("door_style", "Door style", ENUM, d["door_style"],
                          choices=_choices(cg.DOOR_STYLES)),
                ParamSpec("overlay", "Overlay", ENUM, d["overlay"],
                          choices=(("full", "Full overlay"),
                                   ("partial", "Partial (frame shows)"))),
                ParamSpec("pulls", "Pulls", ENUM, d["pulls"],
                          choices=(("bar", "Bar"), ("knob", "Knob"),
                                   ("none", "None"))),
                ParamSpec("finish", "Cabinet finish", ENUM, d["finish"],
                          choices=_choices(cg.FINISHES)),
                ParamSpec("hardware", "Hardware", ENUM, d["hardware"],
                          choices=_choices(cg.HARDWARE)),
                ParamSpec("top_material", "Countertop material", ENUM,
                          d["top_material"], choices=_choices(cg.COUNTERTOPS)),
                ParamSpec("top_thickness_in", "Countertop thickness", FLOAT,
                          d["top_thickness_in"], unit="in", minimum=0.25,
                          maximum=4.0, step=0.25),
            ]
            return out
        out = [
            ParamSpec("width_in", "Width", FLOAT, d["width_in"], unit="in",
                      minimum=6.0, maximum=96.0, step=3.0,
                      tooltip="Stock cabinets come in 3 in steps."),
            ParamSpec("depth_in", "Depth", FLOAT, d["depth_in"], unit="in",
                      minimum=6.0, maximum=48.0, step=1.0,
                      enabled_fn=lambda v: not (v.get("type") == "corner_base"
                                                and v.get("corner_type") != "blind")),
            ParamSpec("height_in", "Box height", FLOAT, d["height_in"], unit="in",
                      minimum=6.0, maximum=120.0, step=0.5,
                      tooltip="The cabinet box, toe kick included, countertop "
                              "not."),
        ]
        if t == "wall":
            out.append(ParamSpec(
                "floor_to_bottom_in", "Height from floor", FLOAT,
                d["floor_to_bottom_in"], unit="in", minimum=0.0, maximum=120.0,
                step=1.0, tooltip="Floor to the cabinet's underside. 54 in is "
                                  "18 in above a 36 in counter."))
        else:
            out += [
                ParamSpec("toe_kick_h_in", "Toe kick height", FLOAT,
                          d["toe_kick_h_in"], unit="in", minimum=0.0, maximum=12.0,
                          step=0.5),
                ParamSpec("toe_kick_d_in", "Toe kick depth", FLOAT,
                          d["toe_kick_d_in"], unit="in", minimum=0.0, maximum=6.0,
                          step=0.5),
            ]
        if t == "corner_base":
            out += [
                ParamSpec("corner_type", "Corner type", ENUM, d["corner_type"],
                          choices=(("diagonal", "Diagonal front"),
                                   ("l_shape", "L-shape (lazy Susan)"),
                                   ("blind", "Blind corner"))),
                ParamSpec("hand", "Corner at", ENUM, d["hand"],
                          choices=(("left", "Back left"), ("right", "Back right"))),
            ]
        if t == "base":
            out += [
                ParamSpec("front", "Front", ENUM, d["front"],
                          choices=(("doors", "Doors"),
                                   ("drawer_over_doors", "Drawer over doors"),
                                   ("drawers", "All drawers"))),
                ParamSpec("drawers", "Drawers", INT, d["drawers"], minimum=2,
                          maximum=5, step=1,
                          enabled_fn=lambda v: v.get("front") == "drawers"),
            ]
        if t == "sink_base":
            out.append(ParamSpec("sink", "Sink", ENUM, d["sink"],
                                 choices=(("none", "None"), ("single", "Single bowl"),
                                          ("double", "Double bowl"))))
            out.append(ParamSpec(
                "sink_side", "Sink position", ENUM, d["sink_side"],
                choices=(("left", "Left"), ("center", "Centre"),
                         ("right", "Right")),
                enabled_fn=lambda v: v.get("sink") == "single",
                tooltip="Which side a single bowl sits on. A double bowl stays "
                        "centred."))
        out += [
            ParamSpec("doors", "Doors", ENUM, d["doors"],
                      choices=(("auto", "Auto (one up to 21 in)"), ("1", "One"),
                               ("2", "Two"))),
            ParamSpec("hinge", "Hinge side", ENUM, d["hinge"],
                      choices=(("left", "Left"), ("right", "Right")),
                      enabled_fn=lambda v: cg.door_count(
                          cg.normalize_state(v, self.preset)) == 1),
            ParamSpec("door_style", "Door style", ENUM, d["door_style"],
                      choices=_choices(cg.DOOR_STYLES)),
            ParamSpec("overlay", "Overlay", ENUM, d["overlay"],
                      choices=(("full", "Full overlay"),
                               ("partial", "Partial (frame shows)"))),
            ParamSpec("pulls", "Pulls", ENUM, d["pulls"],
                      choices=(("bar", "Bar"), ("knob", "Knob"), ("none", "None"))),
            ParamSpec("finish", "Cabinet finish", ENUM, d["finish"],
                      choices=_choices(cg.FINISHES)),
            ParamSpec("hardware", "Hardware", ENUM, d["hardware"],
                      choices=_choices(cg.HARDWARE)),
        ]
        if t in ("base", "sink_base", "corner_base"):
            on = _has_top
            out += [
                ParamSpec("top_on", "Countertop", BOOL, d["top_on"]),
                ParamSpec("top_material", "Countertop material", ENUM,
                          d["top_material"], choices=_choices(cg.COUNTERTOPS),
                          enabled_fn=on),
                ParamSpec("top_thickness_in", "Countertop thickness", FLOAT,
                          d["top_thickness_in"], unit="in", minimum=0.25,
                          maximum=4.0, step=0.25, enabled_fn=on),
                ParamSpec("top_overhang_in", "Front overhang", FLOAT,
                          d["top_overhang_in"], unit="in", minimum=0.0,
                          maximum=18.0, step=0.25, enabled_fn=on),
                ParamSpec("backsplash_in", "Backsplash height", FLOAT,
                          d["backsplash_in"], unit="in", minimum=0.0, maximum=24.0,
                          step=1.0, enabled_fn=on),
            ]
        return out

    def _mirror_specs(self, d):
        """0366: a bathroom mirror / medicine cabinet with lights."""
        return [
            ParamSpec("width_in", "Width", FLOAT, d["width_in"], unit="in",
                      minimum=12.0, maximum=72.0, step=3.0,
                      tooltip="Stock widths step by 3 in."),
            ParamSpec("height_in", "Height", FLOAT, d["height_in"], unit="in",
                      minimum=18.0, maximum=48.0, step=1.0),
            ParamSpec("has_cabinet", "Storage behind the mirror", BOOL,
                      d["has_cabinet"],
                      tooltip="On: a medicine cabinet -- a box with shelves "
                              "behind a mirrored door. Off: a plain wall mirror."),
            ParamSpec("light_style", "Lights", ENUM, d["light_style"],
                      choices=(("none", "None"), ("bar", "Bar above"),
                               ("sconces", "Sconces each side"),
                               ("backlit", "Backlit (LED edge)"))),
            ParamSpec("light_colour", "Light colour", ENUM, d["light_colour"],
                      choices=tuple((k, label) for k, label, _h in cg.LIGHT_COLOURS),
                      enabled_fn=_is_lit),
            ParamSpec("lumens", "Output", FLOAT, d["lumens"], unit="lm",
                      minimum=0.0, maximum=20000.0, step=100.0, decimals=0,
                      enabled_fn=_is_lit,
                      tooltip="800 lm is about a 60 W bulb. 0 switches the lights "
                              "off and keeps the fixture."),
            ParamSpec("floor_to_bottom_in", "Height from floor", FLOAT,
                      d["floor_to_bottom_in"], unit="in", minimum=24.0,
                      maximum=72.0, step=1.0,
                      tooltip="Floor to the bottom of the mirror."),
            ParamSpec("finish", "Frame / cabinet finish", ENUM, d["finish"],
                      choices=_choices(cg.FINISHES)),
            ParamSpec("pulls", "Pull", ENUM, d["pulls"],
                      choices=(("bar", "Bar"), ("knob", "Knob"), ("none", "None")),
                      enabled_fn=_has_storage),
            ParamSpec("hardware", "Hardware", ENUM, d["hardware"],
                      choices=_choices(cg.HARDWARE), enabled_fn=_has_storage),
        ]

    def _fixture_specs(self, d):
        """0338: what a toilet, tub, bookshelf, fireplace or grab bar offers."""
        model = d["model"]
        labels = {k: label for k, label, _h in cg.COLOURS}
        colour = ParamSpec("colour", "Colour", ENUM, d["colour"],
                           choices=tuple((k, labels[k])
                                         for k in cg.FIXTURE_COLOURS))

        def size(key, label, lo, hi, step=1.0, tip=""):
            return ParamSpec(key, label, FLOAT, d[key], unit="in", minimum=lo,
                             maximum=hi, step=step, tooltip=tip)

        if model == "toilet":
            return [colour]
        if model == "bathtub":
            return [size("depth_in", "Length", 48.0, 84.0, 6.0),
                    size("width_in", "Width", 26.0, 48.0),
                    size("height_in", "Rim height", 12.0, 28.0), colour]
        if model == "bookshelf":
            return [
                size("width_in", "Width", 12.0, 96.0, 3.0),
                size("depth_in", "Depth", 6.0, 24.0),
                size("height_in", "Height", 24.0, 120.0, 6.0),
                ParamSpec("shelves", "Shelves", INT, d["shelves"], minimum=0,
                          maximum=10, step=1,
                          tooltip="Shelves between the bottom and the top."),
                ParamSpec("books", "Books on it", BOOL, d["books"]),
                ParamSpec("finish", "Finish", ENUM, d["finish"],
                          choices=_choices(cg.FINISHES))]
        if model == "fireplace":
            return [
                size("width_in", "Width", 30.0, 96.0, 6.0),
                size("depth_in", "Depth", 12.0, 36.0),
                size("height_in", "Mantel height", 30.0, 72.0),
                ParamSpec("surround", "Surround", ENUM, d["surround"],
                          choices=tuple((k, label) for k, label, _m
                                        in cg.SURROUNDS)),
                ParamSpec("finish", "Mantel finish", ENUM, d["finish"],
                          choices=_choices(cg.FINISHES)),
                ParamSpec("lit", "Lit", BOOL, d["lit"],
                          tooltip="Flames show, and glow in the 3D view.")]
        if model == "pedal_bin":
            custom = _is_custom
            return [
                size("width_in", "Diameter", 8.0, 24.0),
                size("height_in", "Height", 10.0, 40.0),
                ParamSpec("finish_mode", "Finish", ENUM, d["finish_mode"],
                          choices=(("standard", "Stainless"),
                                   ("custom", "Colour"))),
                ParamSpec("sheen", "Sheen", ENUM, d["sheen"],
                          choices=cg.SHEENS, enabled_fn=custom),
                ParamSpec("colour", "Colour", ENUM, d["colour"],
                          choices=tuple((k, label) for k, label, _h in cg.COLOURS),
                          enabled_fn=custom)]
        if model == "dog_crate":
            return [
                size("width_in", "Length", 18.0, 60.0, 6.0,
                     "Stock crates: 24, 30, 36, 42 and 48 in."),
                size("depth_in", "Width", 12.0, 36.0),
                size("height_in", "Height", 14.0, 40.0),
                ParamSpec("bed", "Bed inside", BOOL, d["bed"]),
                ParamSpec("colour", "Bed colour", ENUM, d["colour"],
                          choices=tuple((k, label) for k, label, _h in cg.COLOURS),
                          enabled_fn=lambda v: bool(v.get("bed")))]
        if model == "sofa_table":
            return [
                size("width_in", "Length", 24.0, 96.0, 6.0),
                size("depth_in", "Depth", 8.0, 24.0),
                size("height_in", "Height", 20.0, 42.0, 0.5,
                     "About the height of the sofa's back."),
                ParamSpec("shelves", "Shelves", INT, d["shelves"], minimum=0,
                          maximum=3, step=1),
                ParamSpec("finish", "Finish", ENUM, d["finish"],
                          choices=_choices(cg.FINISHES))]
        if model in ("desk", "office_chair", "office_set"):
            chair = [
                ParamSpec("colour", "Chair colour", ENUM, d["colour"],
                          choices=tuple((k, label) for k, label, _h in cg.COLOURS)),
                ParamSpec("arms", "Chair arms", BOOL, d["arms"])]
            if model == "office_chair":
                return chair
            desk = [
                size("width_in", "Width", 36.0, 96.0, 6.0),
                size("height_in", "Desk height", 24.0, 48.0, 0.5,
                     "29 to 30 in seated; 38 to 46 in standing."),
                ParamSpec("pedestal", "Drawers", ENUM, d["pedestal"],
                          choices=cg.PEDESTALS),
                ParamSpec("computer", "On the desk", ENUM, d["computer"],
                          choices=cg.COMPUTERS),
                ParamSpec("finish", "Finish", ENUM, d["finish"],
                          choices=_choices(cg.FINISHES))]
            if model == "desk":
                desk.insert(1, size("depth_in", "Depth", 18.0, 42.0))
                return desk
            return desk + chair
        return [                                      # grab bar
            ParamSpec("bar", "Mounted", ENUM, d["bar"],
                      choices=(("horizontal", "Horizontal"),
                               ("vertical", "Vertical"))),
            size("length_in", "Length", 9.0, 60.0, 6.0,
                 "Stock bars: 12, 18, 24, 36 and 42 in."),
            size("floor_to_bottom_in", "Height from floor", 0.0, 96.0, 0.5,
                 "Floor to the underside of the mounting flange. A horizontal "
                 "bar's grip is about 2 in higher."),
            ParamSpec("hardware", "Finish", ENUM, d["hardware"],
                      choices=_choices(cg.HARDWARE))]

    def normalize(self, state):
        return cg.normalize_state(state, self.preset)

    def to_state(self, values):
        """Only what differs from the preset is written, so a cabinet nobody
        has edited keeps an empty state and follows its preset and its room."""
        st = cg.normalize_state(values, self.preset)
        base = cg.normalize_state({}, self.preset)
        keys = {s.key for s in self.specs()}
        if self.type == "island":
            keys.discard("width_in")       # derived from the slots, never stored
        return {k: st[k] for k in sorted(keys) if st[k] != base[k]}

    def footprint(self, state):
        return cg.footprint(cg.normalize_state(state, self.preset))

    def plan_symbol(self, state):
        """The plan icon DRAWN FROM THE PARAMETERS, so it matches the unit --
        an island's slots, a vanity's sink on its chosen side, a mirror's
        lights -- instead of the catalog symbol stretched to the footprint.
        None keeps the catalog symbol (a plain base, a wall cabinet)."""
        st = cg.normalize_state(state, self.preset)
        if self.type == "island":
            return cg.island_plan(st)
        if self.type == "sink_base":
            return {"prims": cg.sink_base_plan(st)}
        if self.type == "mirror":
            return {"prims": cg.mirror_plan(st)}
        return None

    # -- evaluation ----------------------------------------------------------
    def evaluate(self, values, context):
        st = cg.normalize_state(values, self.preset)
        style = (context or {}).get("room_style")
        findings = []
        if st["width_in"] <= 0 or st["depth_in"] <= 0 or st["height_in"] <= 0:
            findings.append(Finding("size.invalid", ERROR,
                                    "Width, depth and height must be greater "
                                    "than zero.", field="width_in"))
            return None, findings
        try:
            ceiling = float((context or {}).get("ceiling_in") or 96.0)
        except (TypeError, ValueError):
            ceiling = 96.0
        parts = cg.cabinet_parts(st, style, ceiling)
        derived = {"state": st, "parts": parts,
                   "light": cg.light_source(st, ceiling), "ceiling": ceiling,
                   "materials": cg.resolve_materials(st, style),
                   "style": cg.effective_style(style),
                   "footprint": cg.footprint(st),
                   "height": cg.overall_height(st), "code": cg.trade_code(st)}
        if st["type"] in ("appliance", "light"):
            return derived, findings
        if st["type"] == "mirror":
            w = st["width_in"]
            if abs(w / 3.0 - round(w / 3.0)) > 1e-6:
                findings.append(Finding(
                    "width.module", ADVISORY,
                    f"{_fmt(w)} in is not a stock width; mirror units step by "
                    f"3 in.", actual=w, field="width_in"))
            return derived, findings
        if st["type"] == "fixture":
            if st["model"] == "grab_bar" and st["bar"] == "horizontal":
                grip = st["floor_to_bottom_in"] + 1.5 + cg.BAR_DIAMETER / 2.0
                if not 33.0 - 1e-6 <= grip <= 36.0 + 1e-6:
                    findings.append(Finding(
                        "bar.height", ADVISORY,
                        f"The top of the grip is {_fmt(grip)} in above the "
                        f"floor; accessible grab bars are set at 33 to 36 in.",
                        actual=grip, limit=36.0, field="floor_to_bottom_in"))
            if st["model"] == "bathtub" and st["width_in"] > st["depth_in"]:
                findings.append(Finding(
                    "tub.proportion", ADVISORY,
                    "The tub is wider than it is long; the filler stands at "
                    "the end of its length.", field="width_in"))
            return derived, findings
        if st["type"] == "island":
            seats, w = int(st["seats"]), st["width_in"]
            overhang = (st["depth_in"] - cg.ISLAND_CABINET_D
                        - cg.ISLAND_FRONT_SETBACK - 0.75)
            if seats and w / seats < 24.0 - 1e-6:
                findings.append(Finding(
                    "island.seat_width", ADVISORY,
                    f"{seats} seats share {_fmt(w)} in: {_fmt(w / seats)} in "
                    f"each. Allow 24 in a seat.", actual=w / seats, limit=24.0,
                    field="seats"))
            if seats and overhang < 12.0 - 1e-6:
                findings.append(Finding(
                    "island.overhang", ADVISORY,
                    f"The seating overhang is {_fmt(overhang)} in; 12 in is the "
                    f"usual minimum for knees at a 36 in counter.",
                    actual=overhang, limit=12.0, field="depth_in"))
            if not cg.island_slots(st):
                findings.append(Finding(
                    "island.empty", ADVISORY,
                    "Nothing stands under this island; it is drawn 48 in long "
                    "on a plain base.", field="slot_1"))
            return derived, findings
        w = st["width_in"]
        if abs(w / 3.0 - round(w / 3.0)) > 1e-6:
            findings.append(Finding(
                "width.module", ADVISORY,
                f"{_fmt(w)} in is not a stock width; stock cabinets step by "
                f"3 in. A custom width or a filler makes up the difference.",
                actual=w, field="width_in"))
        n = cg.door_count(st)
        leaf = w / n
        if leaf > 24.0 + 1e-6 and st["front"] != "drawers":
            findings.append(Finding(
                "door.wide", ADVISORY,
                f"Each door is {_fmt(leaf)} in wide; doors over 24 in sag and "
                f"swing far into the room. Use two doors, or drawers.",
                actual=leaf, limit=24.0, field="doors"))
        if st["type"] == "wall" and 36.0 < st["floor_to_bottom_in"] < 51.0 - 1e-6:
            findings.append(Finding(
                "wall.clearance", ADVISORY,
                f"The underside is {_fmt(st['floor_to_bottom_in'] - 36.0)} in "
                f"above a 36 in counter; 15 in is the usual minimum, 18 in "
                f"standard.", actual=st["floor_to_bottom_in"], limit=51.0,
                field="floor_to_bottom_in"))
        if (st["type"] == "sink_base" and st["sink"] != "none"
                and not any(p.role == "sink" for p in parts)):
            findings.append(Finding(
                "sink.fit", ADVISORY,
                "This base is too small for the sink chosen; none is drawn.",
                field="sink"))
        return derived, findings

    def summary(self, values, derived, context):
        if derived is None:
            return [("Result", "cannot be built")]
        st, mats = derived["state"], derived["materials"]
        w, d = derived["footprint"]
        if st["type"] == "light":
            src = derived.get("light")
            label = dict((k, name) for k, name, _h in cg.LIGHT_COLOURS)
            return [("Fixture", dict(cg.FIXTURES)[st["fixture"]]),
                    ("Light", label[st["light_colour"]]),
                    ("Output", f"{_fmt(st['lumens'])} lm"
                               + ("" if src else " (off)")),
                    ("Source height", "\u2014" if not src
                     else f"{_fmt(src['pos'][2])} in above the floor"),
                    ("Ceiling here", f"{_fmt(derived['ceiling'])} in")]
        if st["type"] == "fixture":
            name = {"toilet": "Toilet", "bathtub": "Bathtub",
                    "bookshelf": "Bookshelf", "fireplace": "Gas fireplace",
                    "grab_bar": "Grab bar", "desk": "Desk",
                    "office_chair": "Office chair",
                    "office_set": "Desk and chair",
                    "pedal_bin": "Pedal bin", "dog_crate": "Dog crate",
                    "sofa_table": "Sofa table"}[st["model"]]
            rows = [("Fixture", name),
                    ("Size", f"{_fmt(w)} x {_fmt(d)} x {_fmt(st['height_in'])} in")]
            if st["model"] in ("toilet", "bathtub"):
                rows.append(("Colour", _material_label(mats["porcelain"])))
            elif st["model"] == "bookshelf":
                rows += [("Shelves", str(st["shelves"])),
                         ("Finish", _material_label(mats["cabinet"]))]
            elif st["model"] in ("desk", "office_chair", "office_set"):
                if st["model"] != "office_chair":
                    rows += [("On the desk",
                              dict(cg.COMPUTERS)[st["computer"]]),
                             ("Finish", _material_label(mats["cabinet"]))]
                if st["model"] != "desk":
                    rows.append(("Chair", _material_label(mats["upholstery"])))
            elif st["model"] == "pedal_bin":
                rows.append(("Finish", _material_label(mats["appliance"])))
            elif st["model"] == "sofa_table":
                rows += [("Shelves", str(st["shelves"])),
                         ("Finish", _material_label(mats["cabinet"]))]
            elif st["model"] == "dog_crate":
                rows.append(("Bed", "yes" if st["bed"] else "no"))
            elif st["model"] == "fireplace":
                rows += [("Surround", dict((k, label) for k, label, _m
                                           in cg.SURROUNDS)[st["surround"]]),
                         ("Mantel", _material_label(mats["cabinet"]))]
            else:
                rows += [("Finish", _material_label(mats["hardware"])),
                         ("Underside", f"{_fmt(st['floor_to_bottom_in'])} in "
                                       f"above the floor")]
            return rows
        if st["type"] == "mirror":
            lights = {"none": "None", "bar": "Bar above",
                      "sconces": "Sconces each side",
                      "backlit": "Backlit (LED edge)"}[st["light_style"]]
            light_label = dict((k, name) for k, name, _h in cg.LIGHT_COLOURS)
            rows = [("Unit", "Medicine cabinet" if st["has_cabinet"]
                     else "Wall mirror"),
                    ("Size", f"{_fmt(w)} x {_fmt(d)} in"),
                    ("Bottom", f"{_fmt(st['floor_to_bottom_in'])} in "
                               f"above the floor"),
                    ("Lights", lights)]
            if st["light_style"] != "none":
                rows.append(("Light", f"{light_label[st['light_colour']]}, "
                                      f"{_fmt(st['lumens'])} lm"
                                      + ("" if st["lumens"] > 0 else " (off)")))
            if st["has_cabinet"]:
                rows.append(("Frame", _material_label(mats["cabinet"])))
            return rows
        if st["type"] == "appliance":
            rows = [("Finish", _material_label(mats["appliance"])),
                    ("Size", f"{_fmt(w)} x {_fmt(d)} x {_fmt(st['height_in'])} in")]
            if st.get("wall_mounted"):
                rows.append(("Underside", f"{_fmt(st['floor_to_bottom_in'])} in "
                                          f"above the floor"))
            return rows
        if st["type"] == "island":
            names = {row[0]: row[1] for row in cg.ISLAND_SLOTS}
            under = [names[code] for code, _w, _k, _o in cg.island_slots(st)]
            return [("Under it", ", ".join(under) or "nothing"),
                    ("Footprint", f"{_fmt(w)} x {_fmt(d)} in"),
                    ("Seats", str(st["seats"])),
                    ("Cabinet finish", _material_label(mats["cabinet"])),
                    ("Countertop", _material_label(mats["countertop"]))]
        rows = [("Trade code", derived["code"] or "—"),
                ("Footprint", f"{_fmt(w)} x {_fmt(d)} in"),
                ("Overall height", f"{_fmt(derived['height'])} in"),
                ("Doors", str(cg.door_count(st)) if st["front"] != "drawers"
                 else f"{st['drawers']} drawers"),
                ("Door style", dict(cg.DOOR_STYLES)[cg.door_style_of(
                    st, (context or {}).get("room_style"))]),
                ("Cabinet finish", _material_label(mats["cabinet"])),
                ("Hardware", _material_label(mats["hardware"]))]
        if st["top_on"]:
            rows.append(("Countertop", _material_label(mats["countertop"])))
        if st["type"] == "sink_base" and st["sink"] != "none":
            label = {"single": "Single bowl", "double": "Double bowl"}[st["sink"]]
            pos = {"left": "left", "center": "centred", "right": "right"}[
                st["sink_side"]]
            rows.append(("Sink", label if st["sink"] == "double"
                         else f"{label}, {pos}"))
        if st["type"] == "wall":
            rows.append(("Top of cabinet",
                         f"{_fmt(st['floor_to_bottom_in'] + st['height_in'])} in"))
        return rows

    def make_preview(self, parent=None):
        from floorplanner.parametric.cabinet_view import CabinetPreview  # late: Qt
        return CabinetPreview(parent)


def _material_label(material):
    for table in (cg.FINISHES, cg.COUNTERTOPS, cg.HARDWARE):
        for _key, label, mat in table:
            if mat == material:
                return label
    if material.startswith("sheen_"):
        sheen, _sep, hexa = material[len("sheen_"):].partition("#")
        name = next((label for _k, label, h in cg.COLOURS if h == "#" + hexa), hexa)
        return f"{dict(cg.SHEENS).get(sheen, sheen)} {name.lower()}"
    return {"metal": "Stainless steel"}.get(material, material)


KINDS = {kind: register(CabinetKind(kind)) for kind in cg.PRESETS}
