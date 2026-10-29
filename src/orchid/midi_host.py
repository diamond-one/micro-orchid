"""Host-side Orchid Mode.

This speaks MIDI. It is the playable reference for the musical spec. It is
not the native MicroFreak firmware patch.

Input notes are positions on a 25-key keyboard only after `input_base` is
subtracted. The default base, 48, is a test convention. It is not a measured
MicroFreak scan map.

Generated chords leave on `output_channel`. Live playing is read on
`input_channel`. Messages that arrive on any other channel are ignored,
which is what stops a chord sent back down the same cable from being
played as more keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from orchid.engine import Engine, Event
from orchid.layout import KEY_COUNT, MODIFIER_COUNT, Key, physical_key, root_note


@dataclass
class HostResult:
    events: list[Event]
    display: str | None = None
    enabled: bool = False
    stock_button: str | None = None


@dataclass
class Host:
    engine: Engine = field(default_factory=Engine)
    input_base: int = 48
    input_channel: int = 0
    output_channel: int = 1
    octave: int = 0
    enabled: bool = False
    shift: bool = False
    oct_mod: bool = False
    _combo_used: bool = False
    _thru: set[int] = field(default_factory=set)

    def power_on(self, *, shift: bool = False, oct_mod: bool = False) -> HostResult:
        """Startup. A shortcut already held does not activate Orchid Mode."""
        events = self._tag(self.engine.panic())
        self._thru.clear()
        self.enabled = False
        self.shift = shift
        self.oct_mod = oct_mod
        self._combo_used = bool(shift and oct_mod)
        self.octave = 0
        return HostResult(events, enabled=False)

    def button(self, name: str, down: bool) -> HostResult:
        if name in ("hold", "octave_down", "octave_up"):
            if not down:
                return HostResult([], enabled=self.enabled)
            if name == "hold":
                events = self._tag(self.engine.set_latch(not self.engine.latch))
                return HostResult(events, enabled=self.enabled)
            delta = -1 if name == "octave_down" else 1
            return self._set_octave(self.octave + delta)
        if name == "shift":
            self.shift = down
        elif name == "oct_mod":
            self.oct_mod = down
        else:
            raise ValueError(name)

        if self.shift and self.oct_mod and not self._combo_used:
            self._combo_used = True
            return self._toggle()
        if not (self.shift and self.oct_mod):
            self._combo_used = False
        stock = None
        if down and name == "oct_mod" and not self.shift:
            stock = "oct_mod"
        if down and name == "shift" and not self.oct_mod:
            stock = "shift"
        return HostResult([], enabled=self.enabled, stock_button=stock)

    def note(self, kind: str, note: int, velocity: int = 100, channel: int | None = None) -> HostResult:
        if kind not in ("on", "off"):
            raise ValueError(kind)
        channel = self.input_channel if channel is None else channel
        if channel != self.input_channel:
            return HostResult([], enabled=self.enabled)
        if kind == "on" and velocity <= 0:
            kind = "off"
        if not self.enabled:
            return self._thru_note(kind, note, velocity)
        index = note - self.input_base
        if not 0 <= index < KEY_COUNT:
            return HostResult([], enabled=self.enabled)
        kind_key, value = physical_key(index)
        if kind_key == "mod":
            assert isinstance(value, Key)
            events = self.engine.modifier_down(value) if kind == "on" else self.engine.modifier_up(value)
            return HostResult(self._tag(events), enabled=True)
        root_index = MODIFIER_COUNT + int(value)
        events = (
            self.engine.root_down(root_index, root_note(root_index, self.octave), velocity)
            if kind == "on"
            else self.engine.root_up(root_index)
        )
        return HostResult(self._tag(events), enabled=True)

    def advance(self, ms: int) -> HostResult:
        if not self.enabled:
            return HostResult([], enabled=False)
        return HostResult(self._tag(self.engine.advance(ms)), enabled=True)

    def _toggle(self) -> HostResult:
        if self.enabled:
            events = self._tag(self.engine.panic())
            self.enabled = False
            return HostResult(events, display="ORCHID OFF", enabled=False)
        events = [self._tag_one(Event("off", note)) for note in sorted(self._thru)]
        self._thru.clear()
        self.enabled = True
        return HostResult(events, display="ORCHID ON", enabled=True)

    def _set_octave(self, octave: int) -> HostResult:
        self.octave = max(-3, min(4, octave))
        if not self.enabled:
            return HostResult([], enabled=False)
        updates = {
            key: (root_note(key, self.octave), velocity)
            for key, (_note, velocity) in self.engine.roots.items()
        }
        return HostResult(self._tag(self.engine.set_root_notes(updates)), enabled=True)

    def _thru_note(self, kind: str, note: int, velocity: int) -> HostResult:
        if kind == "on":
            self._thru.add(note)
            event = Event("on", note, min(127, max(1, velocity)))
        else:
            self._thru.discard(note)
            event = Event("off", note)
        event = Event(event.kind, event.note, event.velocity)
        return HostResult([self._tag_one(event)], enabled=False)

    def _tag(self, events: list[Event]) -> list[Event]:
        return [self._tag_one(event) for event in events]

    def _tag_one(self, event: Event) -> Event:
        return Event(
            event.kind, event.note, event.velocity, event.delay_ms, self.output_channel
        )
