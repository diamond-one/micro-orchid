"""Performance state for Orchid Mode.

Input is musical state (which modifier keys are down, which roots are held).
Output is note-on and note-off events. The same object feeds the virtual MIDI
host and, later, a firmware patch. It does not know about USART frames or
scan codes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from orchid.chords import Ext, Quality, key_mode_choice, resolve_quality, spell
from orchid.layout import EXTENSION_KEYS, QUALITY_KEYS, Key


@dataclass(frozen=True)
class Event:
    kind: str
    note: int
    velocity: int = 0
    delay_ms: int = 0
    channel: int = 0

    def __post_init__(self) -> None:
        if self.kind not in ("on", "off"):
            raise ValueError(self.kind)


@dataclass
class _Finger:
    stack: tuple[Quality, ...] = ()
    ext: Ext = Ext.NONE

    @property
    def empty(self) -> bool:
        return not self.stack and self.ext == Ext.NONE


@dataclass
class Engine:
    """One player. `voice_limit` is the internal MicroFreak cap.

    Use `voice_limit=None` for an external synth that can sound every tone.
    Several held roots share that cap. The newest roots are kept when there
    are more roots than voices.
    """

    voice_limit: int | None = 4
    sixth_up: bool = False
    arp_ms: int = 120
    key_mode: str | None = None
    tonic: int = 0

    q_stack: list[Quality] = field(default_factory=list)
    ext_held: set[Ext] = field(default_factory=set)
    latch: bool = False
    latch_mods: _Finger = field(default_factory=_Finger)
    inversion: int = 0
    bass: bool = False
    arp: bool = False
    roots: dict[int, tuple[int, int]] = field(default_factory=dict)
    sounding: set[int] = field(default_factory=set)
    arp_pos: int = 0
    arp_acc: int = 0
    _chord_signature: tuple[int, ...] = ()

    def modifier_down(self, key: Key) -> list[Event]:
        if key in QUALITY_KEYS:
            quality = QUALITY_KEYS[key]
            if quality not in self.q_stack:
                self.q_stack.append(quality)
        elif key in EXTENSION_KEYS:
            self.ext_held.add(EXTENSION_KEYS[key])
        elif key is Key.INV_DOWN:
            self.inversion = max(-12, self.inversion - 1)
        elif key is Key.INV_UP:
            self.inversion = min(12, self.inversion + 1)
        elif key is Key.BASS:
            self.bass = not self.bass
        elif key is Key.ARP:
            self.arp = not self.arp
            self.arp_pos = 0
            self.arp_acc = 0
        else:
            raise ValueError(key)
        return self._reconcile()

    def modifier_up(self, key: Key) -> list[Event]:
        if key in QUALITY_KEYS:
            quality = QUALITY_KEYS[key]
            if quality in self.q_stack:
                self.q_stack.remove(quality)
        elif key in EXTENSION_KEYS:
            self.ext_held.discard(EXTENSION_KEYS[key])
        elif key in (Key.INV_DOWN, Key.INV_UP, Key.BASS, Key.ARP):
            return []
        else:
            raise ValueError(key)
        return self._reconcile()

    def root_down(self, key: int, note: int, velocity: int = 100) -> list[Event]:
        if not 0 <= note <= 127:
            raise ValueError(note)
        velocity = min(127, max(1, velocity))
        events: list[Event] = []
        if key in self.roots:
            events.extend(self.root_up(key))
        self.roots[key] = (note, velocity)
        events.extend(self._reconcile())
        return events

    def root_up(self, key: int) -> list[Event]:
        if key not in self.roots:
            return []
        del self.roots[key]
        return self._reconcile()

    def set_latch(self, enabled: bool) -> list[Event]:
        self.latch = enabled
        if enabled:
            self.latch_mods = self._fingers()
        return self._reconcile()

    def set_key_mode(self, mode: str | None, tonic: int = 0) -> list[Event]:
        if mode not in (None, "major", "minor"):
            raise ValueError(mode)
        self.key_mode = mode
        self.tonic = tonic % 12
        return self._reconcile()

    def set_root_notes(self, updates: dict[int, tuple[int, int]]) -> list[Event]:
        """Change the pitch of keys already held, then reconcile once."""
        for key, value in updates.items():
            note, velocity = value
            if key not in self.roots:
                continue
            if not 0 <= note <= 127:
                raise ValueError(note)
            self.roots[key] = (note, min(127, max(1, velocity)))
        return self._reconcile()

    def panic(self) -> list[Event]:
        """Release every generated note and clear performance state."""
        events = [Event("off", note) for note in sorted(self.sounding)]
        self.sounding.clear()
        self.roots.clear()
        self.q_stack.clear()
        self.ext_held.clear()
        self.latch = False
        self.latch_mods = _Finger()
        self.inversion = 0
        self.bass = False
        self.arp = False
        self.arp_pos = 0
        self.arp_acc = 0
        self._chord_signature = ()
        return events

    def advance(self, ms: int) -> list[Event]:
        if ms < 0:
            raise ValueError(ms)
        if not (self.arp and self._arp_pool()):
            return []
        self.arp_acc += ms
        stepped = False
        while self.arp_acc >= self.arp_ms:
            self.arp_acc -= self.arp_ms
            self.arp_pos += 1
            stepped = True
        if stepped:
            return self._reconcile()
        return []

    def held_notes(self) -> tuple[int, ...]:
        return tuple(sorted(self.sounding))

    def _fingers(self) -> _Finger:
        return _Finger(tuple(self.q_stack), _combine(self.ext_held))

    def _mods(self) -> _Finger:
        fingers = self._fingers()
        if not self.latch:
            return fingers
        if not fingers.empty:
            self.latch_mods = fingers
            return fingers
        return self.latch_mods

    def _budgets(self) -> dict[int, int | None]:
        keys = list(self.roots)
        if self.voice_limit is None:
            return {key: None for key in keys}
        count = len(keys)
        if count == 0:
            return {}
        if count > self.voice_limit:
            silent = keys[: count - self.voice_limit]
            live = keys[count - self.voice_limit :]
            budgets = {key: 0 for key in silent}
            budgets.update({key: 1 for key in live})
            return budgets
        base, extra = divmod(self.voice_limit, count)
        budgets = {key: base for key in keys}
        for key in reversed(keys):
            if extra == 0:
                break
            budgets[key] += 1
            extra -= 1
        return budgets

    def _chord_for(self, key: int, limit: int | None) -> list[int]:
        note, _velocity = self.roots[key]
        mods = self._mods()
        shift = 0
        if mods.stack:
            quality = resolve_quality(mods.stack)
        elif self.key_mode:
            quality, shift = key_mode_choice(self.key_mode, note % 12, self.tonic)
        else:
            quality = Quality.MAJ
        sounded = note + shift
        if not 0 <= sounded <= 127 or limit == 0:
            return []
        # The bass is one of the notes already voiced, an octave lower.
        # It takes one of the four voices, so the chord is spelled into
        # the voices that remain.
        spell_limit = limit
        if self.bass and limit is not None and limit >= 2:
            spell_limit = limit - 1
        notes = spell(
            sounded,
            quality,
            mods.ext,
            sixth_up=self.sixth_up,
            inversion=self.inversion,
            voice_limit=spell_limit,
        )
        return self._with_bass(notes, limit)

    def _with_bass(self, notes: list[int], limit: int | None) -> list[int]:
        if not self.bass or not notes:
            return notes
        bass = min(notes) - 12
        if bass < 0 or bass in notes:
            return notes
        if limit is not None and len(notes) >= limit:
            return notes
        return sorted([*notes, bass])

    def _all_chords(self) -> dict[int, list[int]]:
        budgets = self._budgets()
        return {key: self._chord_for(key, budgets[key]) for key in self.roots}

    def _arp_pool(self) -> list[int]:
        pool: list[int] = []
        for notes in self._all_chords().values():
            for note in notes:
                if note not in pool:
                    pool.append(note)
        return pool

    def _signature(self) -> tuple[int, ...]:
        return tuple(self._arp_pool())

    def _wanted(self) -> dict[int, int]:
        chords = self._all_chords()
        if self.arp:
            pool = []
            for notes in chords.values():
                for note in notes:
                    if note not in pool:
                        pool.append(note)
            if not pool:
                return {}
            chosen = pool[self.arp_pos % len(pool)]
            velocity = max(vel for _note, vel in self.roots.values())
            return {chosen: velocity}
        wanted: dict[int, int] = {}
        for key, notes in chords.items():
            velocity = self.roots[key][1]
            for note in notes:
                wanted[note] = velocity
        return wanted

    def _reconcile(self) -> list[Event]:
        signature = self._signature()
        changed = signature != self._chord_signature
        if changed:
            self.arp_pos = 0
            self.arp_acc = 0
            self._chord_signature = signature
        wanted = self._wanted()
        events: list[Event] = []
        for note in sorted(self.sounding):
            if note not in wanted:
                events.append(Event("off", note))
                self.sounding.discard(note)
        for note in sorted(wanted):
            if note not in self.sounding:
                events.append(Event("on", note, wanted[note]))
                self.sounding.add(note)
        return events


def _combine(flags: set[Ext]) -> Ext:
    value = Ext.NONE
    for flag in flags:
        value |= flag
    return value
