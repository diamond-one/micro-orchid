"""Orchid-style chord performance for the Arturia MicroFreak.

The musical engine and the virtual MIDI host are implemented here.
Native firmware patching is a separate step and is not claimed by importing
this package.
"""

from orchid.chords import Ext, Quality, spell
from orchid.engine import Engine, Event
from orchid.layout import LAYOUT, ROOT_BASE_NOTE, physical_key
from orchid.midi_host import Host

__all__ = [
    "Engine",
    "Event",
    "Ext",
    "Host",
    "LAYOUT",
    "Quality",
    "ROOT_BASE_NOTE",
    "physical_key",
    "spell",
]

__version__ = "0.1.0"
