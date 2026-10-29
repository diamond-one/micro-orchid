# Control mapping

## Shift + OCT | MOD

OCT | MOD is the button in the arpeggiator/sequencer section, not Octave Up
or Octave Down.

| Gesture | Result |
|---|---|
| Shift alone | Orchid stays as it was. The host marks the press as stock Shift. |
| OCT \| MOD alone | Orchid stays as it was. The host marks the press as stock OCT \| MOD. |
| Shift held, then OCT \| MOD | Toggle. Display `ORCHID ON` or `ORCHID OFF`. |
| Combo held, including extra downs | One toggle only. |
| Combo already down at `power_on` | Stays off. |
| Toggle off | Note-offs for every Orchid note. Latch, inversion, strum, and arp clear. |

Octave Up and Octave Down change the root octave. They do not toggle the mode.
Hold toggles latch.

The stock recovery combination, Shift + Arp + OCT | MOD at power-on, belongs
to the bootloader. This project does not patch `0x08000000`–`0x0800BFFF`.

## Keys

Index 0 is the left end of the 25-key bed.

| Index | Role |
|---|---|
| 0 | diminished |
| 1 | minor |
| 2 | major |
| 3 | suspended |
| 4 | sixth |
| 5 | minor seventh |
| 6 | major seventh |
| 7 | ninth |
| 8 | inversion down |
| 9 | inversion up |
| 10 | strum toggle |
| 11 | arpeggiator toggle |
| 12–24 | roots C, C#, D, … C |

At octave 0 the roots are MIDI 60 through 72. The host does not use the
incoming note number as the chord root. It uses the key index.

## MIDI channels

Input is channel 1 in the API's zero-based numbering (`input_channel=0`).
Chords are emitted on channel 2 (`output_channel=1`). A message on the
output channel is ignored, so a looped chord is not played as more keys.
