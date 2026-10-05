"""Macro language v2: AST -> abstract input events (MACRO_SPEC.md sec8.1).

PURE: scene coordinates, no Qt objects, so the expansion is unit-tested
without a GUI. The Qt sink turns each `InputEvent` into a real event; drag
interpolation (sec8.5) is the sink's, because it is measured in view pixels.

Event kinds:

    tool      select a tool                      .tool
    key_down  a key goes down                    .key (KeySpec.ident), .text, .mods
    key_up    a key comes up                     .key, .mods
    hover     pointer moves, NO button held      .x .y .mods
    press     the chain's button goes down       .button .x .y .mods
    move      pointer moves, the button held     .button .x .y .mods
    release   the button comes up                .button .x .y .mods
    dblclick  the double-click event             .button .x .y .mods
    wheel     one wheel event at the pointer     .dx .dy .x .y .mods
    wait      process events for .ms milliseconds
    command   an application command (sec14)    .text (the name), .args

`.mods` is the modifier state the event CARRIES. For a modifier key's own
key_down / key_up it is the state AFTER the change (sec7), which is what Qt
delivers for real hardware.
"""
from __future__ import annotations

from dataclasses import dataclass

from floorplanner.macro2 import ast, keys
from floorplanner.macro2.ast import MOD_ORDER, Mod

_NONE = frozenset()


@dataclass(frozen=True)
class InputEvent:
    kind: str
    mods: frozenset = _NONE
    key: str | None = None
    text: str = ""
    button: str | None = None
    x: float | None = None
    y: float | None = None
    dx: float = 0.0
    dy: float = 0.0
    ms: float = 0.0
    tool: str | None = None
    args: tuple = ()
    line: int = 0


class _Expander:
    def __init__(self):
        self.events = []
        self.warnings = []
        self.active = _NONE        # modifiers currently down
        self.held = {}             # KeySpec.ident -> KeySpec, by KEYDOWN
        self.pos = (None, None)    # pointer; None = the canvas centre (sec5.1)
        self.line = 0

    # -- helpers ----------------------------------------------------------
    def emit(self, kind, **kw):
        self.events.append(InputEvent(kind, line=self.line, **kw))

    @property
    def baseline(self):
        """K (sec5.3): the modifiers held by KEYDOWN."""
        return frozenset(s.mod for s in self.held.values() if s.mod is not None)

    def to(self, target):
        """sec7: move the modifier state to `target` with real key events --
        release Meta, Alt, Ctrl, Shift; then press Shift, Ctrl, Alt, Meta.
        Each event carries the state AFTER its own key changed."""
        target = frozenset(target)
        for m in reversed(MOD_ORDER):
            if m in self.active and m not in target:
                self.active = self.active - {m}
                self.emit("key_up", key=keys.MOD_KEY_NAME[m], mods=self.active)
        for m in MOD_ORDER:
            if m in target and m not in self.active:
                self.active = self.active | {m}
                self.emit("key_down", key=keys.MOD_KEY_NAME[m], mods=self.active)

    def hover(self, x, y):
        self.pos = (x, y)
        self.emit("hover", x=x, y=y, mods=self.active)

    # -- commands ---------------------------------------------------------
    def chain(self, c: ast.Chain):
        button, double = ast.CLICK_VERBS[c.verb]
        k = self.baseline
        head = c.segments[0]
        self.to(head.mods | k)                               # 1
        self.hover(head.x, head.y)                           # 2
        self.emit("press", button=button, x=head.x, y=head.y, mods=self.active)  # 3
        if double:
            self.emit("release", button=button, x=head.x, y=head.y, mods=self.active)
            self.emit("dblclick", button=button, x=head.x, y=head.y, mods=self.active)
        for seg in c.segments[1:]:                           # 4
            self.to(seg.mods | k)
            self.pos = (seg.x, seg.y)
            self.emit("move", button=button, x=seg.x, y=seg.y, mods=self.active)
        x, y = self.pos
        self.emit("release", button=button, x=x, y=y, mods=self.active)  # 5
        self.to(k)                                           # 6

    def stroke(self, s: ast.Stroke):
        spec = keys.resolve(s.key)
        k = self.baseline
        self.to(s.mods | k)
        self.emit("key_down", key=spec.ident, text="", mods=self.active)
        self.emit("key_up", key=spec.ident, mods=self.active)
        self.to(k)

    def type_text(self, t: ast.TypeText):
        # each character is a press/release pair carrying it as text(),
        # as QTest.keyClicks does (sec6.1)
        for ch in t.text:
            self.emit("key_down", key=ch.upper(), text=ch, mods=self.active)
            self.emit("key_up", key=ch.upper(), mods=self.active)

    def key_down(self, key: ast.Key):
        spec = keys.resolve(key)
        if spec.ident in self.held:
            self.warnings.append(
                f"line {self.line}: KEYDOWN {keys.write(key)} -- already held; ignored")
            return
        self.held[spec.ident] = spec
        if spec.mod is not None:
            self.active = self.active | {spec.mod}
        self.emit("key_down", key=spec.ident, mods=self.active)

    def key_up(self, key: ast.Key, warn=True):
        spec = keys.resolve(key)
        if spec.ident not in self.held:
            if warn:
                self.warnings.append(
                    f"line {self.line}: KEYUP {keys.write(key)} -- not held; ignored")
            return
        del self.held[spec.ident]
        if spec.mod is not None:
            self.active = self.active - {spec.mod}
        self.emit("key_up", key=spec.ident, mods=self.active)

    def finish(self):
        """sec6.3: when the macro ends every held key is released, with a
        warning for each."""
        for ident, spec in list(self.held.items()):
            self.warnings.append(
                f"{'{' + spec.name + '}' if spec.name else spec.char} was still held "
                f"at the end of the macro; released")
            del self.held[ident]
            if spec.mod is not None:
                self.active = self.active - {spec.mod}
            self.emit("key_up", key=ident, mods=self.active)
        self.to(_NONE)

    def run(self, macro: ast.Macro):
        for ln in macro.lines:
            self.line = ln.line
            if ln.tool is not None:                      # the tool FIRST (sec4)
                self.emit("tool", tool=ln.tool)
            cmd = ln.command
            if isinstance(cmd, ast.Chain):
                self.chain(cmd)
            elif isinstance(cmd, ast.Move):
                k = self.baseline
                self.to(cmd.mods | k)
                self.hover(cmd.x, cmd.y)
                self.to(k)
            elif isinstance(cmd, ast.Wheel):
                k = self.baseline
                self.to(cmd.mods | k)
                self.emit("wheel", dx=cmd.dx, dy=cmd.dy, x=self.pos[0],
                          y=self.pos[1], mods=self.active)
                self.to(k)
            elif isinstance(cmd, ast.TypeText):
                self.type_text(cmd)
            elif isinstance(cmd, ast.KeyPress):
                for s in cmd.strokes:
                    self.stroke(s)
            elif isinstance(cmd, ast.KeyDown):
                self.key_down(cmd.key)
            elif isinstance(cmd, ast.KeyUp):
                self.key_up(cmd.key)
            elif isinstance(cmd, ast.Wait):
                self.emit("wait", ms=cmd.ms)
            elif isinstance(cmd, ast.AppCommand):
                # no input is simulated, so no modifier or pointer state is
                # touched: a held key stays held across it
                self.emit("command", text=cmd.name, args=cmd.args)
        self.finish()


def expand(macro: ast.Macro):
    """`(events, warnings)` for a VALIDATED macro."""
    ex = _Expander()
    ex.run(macro)
    return ex.events, ex.warnings


def release_all(active, held_idents=()):
    """The events that bring a player back to a clean state from wherever an
    abort left it: every non-modifier held key up, then every modifier up in
    sec7's release order. The player's `finally`."""
    out = []
    state = frozenset(active)
    for ident in held_idents:
        if ident not in keys.MODIFIER_KEYS:
            out.append(InputEvent("key_up", key=ident, mods=state))
    for m in reversed(MOD_ORDER):
        if m in state:
            state = state - {m}
            out.append(InputEvent("key_up", key=keys.MOD_KEY_NAME[m], mods=state))
    return out


__all__ = ["InputEvent", "Mod", "expand", "release_all"]
