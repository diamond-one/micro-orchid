# micro-orchid

Orchid-style chord playing for the Arturia MicroFreak.

The chord engine and a virtual MIDI host run here and are covered by tests.
A native firmware patch does not exist yet. Nothing in this repository
flashes an instrument.

## Play the musical model

Keys are indexes `0..24`. Twelve modifier keys on the left, thirteen chromatic
roots on the right. Shift plus OCT | MOD toggles the mode. A root alone plays
a major triad. The internal engine keeps four notes.

```python
from orchid.midi_host import Host
from orchid.layout import MODIFIER_COUNT

host = Host()
host.button("shift", True)
host.button("oct_mod", True)          # ORCHID ON
host.note("on", host.input_base + MODIFIER_COUNT)
host.engine.held_notes()              # (60, 64, 67)
```

`input_base` defaults to 48 so tests can pretend the 25 keys are one MIDI
range. That number is not a measured MicroFreak scan map. Generated notes
leave on MIDI channel 2. Playing is read on channel 1.

## Check

```powershell
python scripts/verify_orchid.py
```

Unit tests must pass. Missing firmware, Renode, or a native image is reported
as BLOCKED or NOT RUN, never as a pass.

## Layout

| Path | Role |
|---|---|
| `src/orchid/chords.py` | Chord spelling and four-voice reduction |
| `src/orchid/engine.py` | Latch, inversion, strum, arp, note on/off |
| `src/orchid/midi_host.py` | Shift+OCT\|MOD and virtual MIDI |
| `firmware/boundaries.py` | Addresses that must not change, verified hashes |
| `firmware/coexist.py` | Rejects an Orchid patch that would overwrite SuperFreaker |
| `docs/SUPERFREAKER.md` | What SuperFreaker 0.1.2 changed, and how both can coexist |
| `docs/MILESTONES.md` | What has actually been shown |

Study notes from microfreak-emu, microfreak-tools, and ChoralRoot were used
to choose intervals and to learn the firmware map. Their code is not vendored.
ChoralRoot is GPL-3. This project's own code is the files outside `third_party/`.

## Safety

Do not flash a MicroFreak from this tree. The bootloader and the factory-data
sector stay untouched. Details are in `docs/SAFETY.md`.
