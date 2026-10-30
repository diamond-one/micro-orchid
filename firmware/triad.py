"""Place a one-root major triad on SuperFreaker's MIDI note path.

The channel callback at 0x080478EA calls midi_dispatch once per message.
That call becomes orchid_chord, which calls midi_dispatch for the root,
the third, and the fifth. The code sits in the tail of speech bank 4
after that bank's last word is retired.

This module does not write a device and does not copy a firmware image
into the repository.
"""

from __future__ import annotations

import struct
import subprocess
import tempfile
from pathlib import Path

BASE = 0x0800C000
HOOK_SITE = 0x080478EA
KEY_SITE = 0x0803AD9E
BUTTON_DOWN = 0x0804348C
BUTTON_UP = 0x080434A4
BUTTON_FN = 0x08043224
DISPATCH = 0x08048524
CAVE = 0x0807B264
CAVE_END = 0x0807B367
BANK4_SIZE_ADDR = 0x0807885C
BANK4_PTR = 0x0807A0A4
BANK4_SIZE = 0x12C2
BANK4_SIZE_AFTER = 0x11C0
INTERVALS = (0, 4, 7)

_ROOT = Path(__file__).resolve().parents[1]
_CLANG = Path(r"C:\Program Files\LLVM\bin\clang.exe")


def encode_bl(pc: int, target: int) -> bytes:
    """Thumb-2 BL at `pc`."""
    offset = target - (pc + 4)
    if offset % 2 or not -(1 << 24) <= offset < (1 << 24):
        raise ValueError(f"bl out of range: 0x{pc:08X} -> 0x{target:08X}")
    immediate = offset >> 1
    sign = (immediate >> 23) & 1
    i1 = (immediate >> 22) & 1
    i2 = (immediate >> 21) & 1
    first = 0xF000 | (sign << 10) | ((immediate >> 11) & 0x3FF)
    second = 0xD000 | (((~i1 ^ sign) & 1) << 13) | (((~i2 ^ sign) & 1) << 11) | (immediate & 0x7FF)
    return struct.pack("<HH", first, second)


def triad_notes(note: int) -> list[int]:
    """Major triad, dropping any tone past 127. Same rule as spell()."""
    return [tone for tone in (note + interval for interval in INTERVALS) if tone <= 127]


def expand_message(message: int) -> list[int]:
    """Packed MIDI word in, the words midi_dispatch should receive."""
    kind = message & 0xF0
    if kind not in (0x80, 0x90):
        return [message]
    note = (message >> 8) & 0xFF
    return [(message & 0xFFFF00FF) | (tone << 8) for tone in triad_notes(note)]


def compile_hook(clang: Path | None = None) -> bytes:
    """Assemble firmware/hook_triad.c at the cave address."""
    compiler = clang or _CLANG
    if not compiler.is_file():
        raise FileNotFoundError(f"clang is not at {compiler}")
    with tempfile.TemporaryDirectory() as directory:
        elf = Path(directory) / "hook.elf"
        blob = Path(directory) / "hook.bin"
        command = [
            str(compiler),
            "-target", "thumbv7em-none-eabi",
            "-mcpu=cortex-m4",
            "-mthumb",
            "-mfloat-abi=soft",
            "-Os",
            "-ffreestanding",
            "-fno-builtin",
            "-fno-exceptions",
            "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables",
            "-ffunction-sections",
            "-nostdlib",
            "-Wl,--gc-sections",
            f"-Wl,-T,{_ROOT / 'firmware' / 'hook_triad.ld'}",
            "-o", str(elf),
            str(_ROOT / "firmware" / "hook_triad.c"),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "clang failed")
        objcopy = compiler.with_name("llvm-objcopy.exe")
        copied = subprocess.run(
            [str(objcopy), "-O", "binary", str(elf), str(blob)],
            capture_output=True, text=True,
        )
        if copied.returncode != 0:
            raise RuntimeError(copied.stderr.strip() or "llvm-objcopy failed")
        code = blob.read_bytes()
    if not code or len(code) > CAVE_END - CAVE:
        raise RuntimeError(f"hook is {len(code)} bytes; the cave holds {CAVE_END - CAVE}")
    if CAVE + len(code) > CAVE_END:
        raise RuntimeError("hook crosses the live objects at 0x0807B367")
    return code


def _word(image: bytes, address: int) -> int:
    return struct.unpack_from("<I", image, address - BASE)[0]


def apply_triad(image: bytes, code: bytes) -> bytearray:
    """Return a payload with the hook, the branch, and the shortened bank.

    Refuses an image whose call site is not the stock bl, or whose bank 4
    is not the 22-word factory bank. The caller passes the SuperFreaker
    payload; this does not open a file.
    """
    if len(image) < BANK4_SIZE_ADDR - BASE + 4:
        raise ValueError("image is shorter than the speech descriptor")
    if image[HOOK_SITE - BASE:HOOK_SITE - BASE + 4] != encode_bl(HOOK_SITE, DISPATCH):
        raise ValueError("the channel callback does not call midi_dispatch")
    if _word(image, BANK4_SIZE_ADDR) != BANK4_SIZE:
        raise ValueError("bank 4 is not the 22-word factory bank")
    if BANK4_PTR + BANK4_SIZE_AFTER != CAVE:
        raise ValueError("retiring the last word does not land on the cave")
    if len(code) > CAVE_END - CAVE:
        raise ValueError("hook does not fit in the retired word")
    out = bytearray(image)
    out[HOOK_SITE - BASE:HOOK_SITE - BASE + 4] = encode_bl(HOOK_SITE, CAVE)
    struct.pack_into("<I", out, BANK4_SIZE_ADDR - BASE, BANK4_SIZE_AFTER)
    out[CAVE - BASE:CAVE - BASE + len(code)] = code
    return out


# The full mode retires 21 words of bank 4. The word boundary is
# 0x0807A0A4 + 0xC6 = 0x0807A16A. Code starts on the next 4-byte address.
MODE_CAVE = 0x0807A16C
MODE_CAVE_END = 0x0807B367
MODE_BANK_SIZE = 0xC6
STACK_TOP = 0x2001FE00
VECTOR_SP = 0x0800C000
STARTUP_SP = 0x0805F884
OLD_STACK = 0x20020000


def compile_mode(clang: Path | None = None) -> tuple[bytes, int, int, int]:
    """Assemble the full mode.

    Returns the flash bytes and the offsets of orchid_chord, orchid_key, and
    orchid_button. The linker does not put the MIDI entry first, so each bl
    uses its offset.
    """
    compiler = clang or _CLANG
    if not compiler.is_file():
        raise FileNotFoundError(f"clang is not at {compiler}")
    with tempfile.TemporaryDirectory() as directory:
        elf = Path(directory) / "mode.elf"
        blob = Path(directory) / "mode.bin"
        command = [
            str(compiler),
            "-target", "thumbv7em-none-eabi",
            "-mcpu=cortex-m4",
            "-mthumb",
            "-mfloat-abi=soft",
            "-Oz",
            "-flto",
            "-ffreestanding",
            "-fno-builtin",
            "-fno-exceptions",
            "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables",
            "-ffunction-sections",
            "-nostdlib",
            "-DORCHID_DEVICE",
            "-Wl,--gc-sections",
            f"-Wl,-T,{_ROOT / 'firmware' / 'hook_mode.ld'}",
            "-o", str(elf),
            str(_ROOT / "firmware" / "hook_mode.c"),
            str(_ROOT / "firmware" / "orchid_engine.c"),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "clang failed")
        objcopy = compiler.with_name("llvm-objcopy.exe")
        copied = subprocess.run(
            [str(objcopy), "-O", "binary", "-j", ".text", str(elf), str(blob)],
            capture_output=True, text=True,
        )
        if copied.returncode != 0:
            raise RuntimeError(copied.stderr.strip() or "llvm-objcopy failed")
        listed = subprocess.run(
            [str(compiler.with_name("llvm-nm.exe")), "--defined-only", str(elf)],
            capture_output=True, text=True,
        )
        if listed.returncode != 0:
            raise RuntimeError(listed.stderr.strip() or "llvm-nm failed")
        code = blob.read_bytes()
        chord_at = key_at = button_at = None
        for line in listed.stdout.splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            addr = int(parts[0], 16)
            name = parts[-1]
            if name == "orchid_key":
                key_at = addr
            elif name == "orchid_chord":
                chord_at = addr
            elif name == "orchid_button":
                button_at = addr
    if not code or MODE_CAVE + len(code) > MODE_CAVE_END:
        raise RuntimeError(f"mode is {len(code)} bytes and crosses 0x{MODE_CAVE_END:08X}")
    if chord_at is None or key_at is None or button_at is None:
        raise RuntimeError(f"entry points are chord {chord_at} key {key_at} button {button_at}")
    chord_offset = chord_at - MODE_CAVE
    key_offset = key_at - MODE_CAVE
    button_offset = button_at - MODE_CAVE
    offsets = (chord_offset, key_offset, button_offset)
    if any(not 0 <= item < len(code) for item in offsets):
        raise RuntimeError(f"entries sit outside the image {offsets}")
    if len(set(offsets)) != 3:
        raise RuntimeError("two entry points landed on the same address")
    return code, chord_offset, key_offset, button_offset


def apply_mode(image: bytes, code: bytes, chord_offset: int, key_offset: int,
                button_offset: int) -> bytearray:
    """Place the full mode, retire 21 speech words, and lower the stack."""
    if len(image) < STARTUP_SP - BASE + 4:
        raise ValueError("image is shorter than the startup literal")
    if image[HOOK_SITE - BASE:HOOK_SITE - BASE + 4] != encode_bl(HOOK_SITE, DISPATCH):
        raise ValueError("the channel callback does not call midi_dispatch")
    if image[KEY_SITE - BASE:KEY_SITE - BASE + 4] != encode_bl(KEY_SITE, DISPATCH):
        raise ValueError("the key note does not call midi_dispatch")
    for site in (BUTTON_DOWN, BUTTON_UP):
        if image[site - BASE:site - BASE + 4] != encode_bl(site, BUTTON_FN):
            raise ValueError(f"button edge at 0x{site:08X} does not call the handler")
    if _word(image, BANK4_SIZE_ADDR) != BANK4_SIZE:
        raise ValueError("bank 4 is not the 22-word factory bank")
    if _word(image, VECTOR_SP) != OLD_STACK or _word(image, STARTUP_SP) != OLD_STACK:
        raise ValueError("the stack top is not the stock value")
    if BANK4_PTR + MODE_BANK_SIZE > MODE_CAVE:
        raise ValueError("the kept speech words run into the hook")
    if MODE_CAVE + len(code) > MODE_CAVE_END:
        raise ValueError("mode crosses the live objects")
    offsets = (chord_offset, key_offset, button_offset)
    if any(not 0 <= item < len(code) for item in offsets):
        raise ValueError("an entry point is outside the mode image")
    out = bytearray(image)
    out[HOOK_SITE - BASE:HOOK_SITE - BASE + 4] = encode_bl(HOOK_SITE, MODE_CAVE + chord_offset)
    out[KEY_SITE - BASE:KEY_SITE - BASE + 4] = encode_bl(KEY_SITE, MODE_CAVE + key_offset)
    for site in (BUTTON_DOWN, BUTTON_UP):
        out[site - BASE:site - BASE + 4] = encode_bl(site, MODE_CAVE + button_offset)
    struct.pack_into("<I", out, BANK4_SIZE_ADDR - BASE, MODE_BANK_SIZE)
    struct.pack_into("<I", out, VECTOR_SP - BASE, STACK_TOP)
    struct.pack_into("<I", out, STARTUP_SP - BASE, STACK_TOP)
    out[MODE_CAVE - BASE:MODE_CAVE - BASE + len(code)] = code
    return out


def changed_spans(before: bytes, after: bytes) -> list[tuple[int, int]]:
    """Half-open addresses where `after` differs from `before`."""
    spans: list[tuple[int, int]] = []
    start = None
    for index, (left, right) in enumerate(zip(before, after)):
        if left != right and start is None:
            start = index
        elif left == right and start is not None:
            spans.append((BASE + start, BASE + index))
            start = None
    if start is not None:
        spans.append((BASE + start, BASE + len(before)))
    return spans
