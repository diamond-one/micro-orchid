"""Find bytes a MicroFreak image does not execute and does not load.

A PC-relative load is the only thing that counts as a reference. Scanning the
image for words that look like addresses treats instruction bytes as pointers
and reports live tables as empty. That mistake was already made once for the
region after the speech banks.

This module does not write a device and does not copy firmware into the repo.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from capstone import CS_ARCH_ARM, CS_GRP_CALL, CS_GRP_JUMP, CS_MODE_THUMB, Cs
from capstone.arm import ARM_OP_IMM, ARM_OP_MEM, ARM_REG_PC

_DISASM = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
_DISASM.detail = True


@dataclass(frozen=True)
class Gap:
    start: int
    end: int

    @property
    def size(self) -> int:
        return self.end - self.start


def thumb_literal_address(instruction: int, displacement: int) -> int:
    """Address a Thumb PC-relative load reads. PC is the instruction plus 4."""
    return ((instruction + 4) & ~3) + displacement


def gaps(image: bytes, base: int, follow_prologues: bool = False) -> list[Gap]:
    """Half-open runs that reachable code neither executes nor loads.

    `follow_prologues` also starts at undecoded `push` instructions. That
    finds routines reached only through a register, and it also decodes data
    whose bytes happen to match `push`. Leave it off when deciding that a
    gap is unused.
    """
    code, data, refs = _coverage(image, base, follow_prologues)
    live = _live_bytes(image, base, code, data, refs)
    return _runs(live, base, base + len(image))


def _coverage(image: bytes, base: int, follow_prologues: bool = False) -> tuple[set[int], set[int], set[int]]:
    end = base + len(image)
    code: set[int] = set()
    data: set[int] = set()
    refs: set[int] = set()
    queued = set(_entry_points(image, base, end))
    pending = list(queued)
    swept_prologues = False

    while True:
        if not pending:
            if swept_prologues or not follow_prologues:
                break
            swept_prologues = True
            for addr in _prologue_starts(image, base, code):
                if addr not in queued:
                    queued.add(addr)
                    pending.append(addr)
            continue
        addr = pending.pop()
        if addr in code or addr < base or addr >= end:
            continue
        offset = addr - base
        window = image[offset:offset + 16]
        decoded = list(_DISASM.disasm(window, addr, 1))
        if not decoded:
            continue
        ins = decoded[0]
        if ins.address != addr:
            continue
        for index in range(ins.size):
            code.add(addr + index)
        for pool, value in _literals(image, base, end, ins):
            for index in range(4):
                data.add(pool + index)
            if value is not None and base <= (value & ~1) < end:
                target = value & ~1
                refs.add(target)
                if value & 1 and target not in queued:
                    queued.add(target)
                    pending.append(target)
        for target in _branch_targets(ins):
            target &= ~1
            if base <= target < end and target not in queued:
                queued.add(target)
                pending.append(target)
        if _falls_through(ins):
            nxt = addr + ins.size
            if nxt not in queued:
                queued.add(nxt)
                pending.append(nxt)
    return code, data, refs


def _prologue_starts(image: bytes, base: int, code: set[int]) -> list[int]:
    """Functions the direct-branch walk never reached.

    A Thumb function almost always opens with `push` including `lr`. Starting
    a second walk there picks up routines that are only reached through a
    register. Data that happens to match the encoding can be marked too,
    which hides a gap rather than inventing one.
    """
    found = []
    limit = len(image) - 3
    offset = 0
    while offset < limit:
        addr = base + offset
        if addr in code:
            offset += 2
            continue
        first = struct.unpack_from("<H", image, offset)[0]
        if (first & 0xFF00) == 0xB500:
            found.append(addr)
            offset += 2
            continue
        if first == 0xE92D and (struct.unpack_from("<H", image, offset + 2)[0] & (1 << 14)):
            found.append(addr)
            offset += 4
            continue
        offset += 2
    return found


def _entry_points(image: bytes, base: int, end: int) -> list[int]:
    points = []
    # Word 0 is the initial stack pointer. Later words are handlers until the
    # table ends. A zero entry is a reserved vector, not the end of the table.
    for index in range(1, 128):
        at = (index * 4)
        if at + 4 > len(image):
            break
        word = struct.unpack_from("<I", image, at)[0]
        if word == 0:
            continue
        if word & 1 and base <= (word & ~1) < end:
            points.append(word & ~1)
            continue
        if points:
            break
    return points


def _literals(image: bytes, base: int, end: int, ins) -> list[tuple[int, int | None]]:
    found = []
    for op in ins.operands:
        if op.type != ARM_OP_MEM or op.mem.base != ARM_REG_PC or op.mem.index != 0:
            continue
        pool = thumb_literal_address(ins.address, op.mem.disp)
        if pool < base or pool + 4 > end:
            continue
        value = struct.unpack_from("<I", image, pool - base)[0]
        found.append((pool, value))
    return found


def _branch_targets(ins) -> list[int]:
    if not (ins.group(CS_GRP_JUMP) or ins.group(CS_GRP_CALL) or ins.mnemonic in ("cbz", "cbnz")):
        return []
    return [op.imm for op in ins.operands if op.type == ARM_OP_IMM]


def _falls_through(ins) -> bool:
    mnemonic = ins.mnemonic
    if mnemonic in ("b", "b.n", "b.w", "bx", "bx.w", "tbb", "tbh"):
        return False
    if mnemonic.startswith("pop") and "pc" in ins.op_str:
        return False
    return True


def _live_bytes(image: bytes, base: int, code: set[int], data: set[int], refs: set[int]) -> bytearray:
    end = base + len(image)
    live = bytearray(len(image))
    for addr in code:
        if base <= addr < end:
            live[addr - base] = 1
    for addr in data:
        if base <= addr < end:
            live[addr - base] = 1
    # A load names the start of an object. The bytes up to the next load or
    # the next instruction belong to that object. Marking only the first
    # byte is how a table gets reported as empty space.
    ordered = sorted(addr for addr in refs if base <= addr < end and not live[addr - base])
    stops = sorted(set(ordered) | {addr for addr in code} | {end})
    for start in ordered:
        stop = end
        for candidate in stops:
            if candidate > start:
                stop = candidate
                break
        for addr in range(start, stop):
            if not live[addr - base]:
                live[addr - base] = 1
    _chase_pointer_tables(image, base, live, ordered)
    return live


def _chase_pointer_tables(image: bytes, base: int, live: bytearray, starts: list[int]) -> None:
    """Follow {pointer, size} words stored in a loaded table, not in code."""
    end = base + len(image)
    seen = set(starts)
    pending = list(starts)
    while pending:
        start = pending.pop()
        offset = start - base
        if offset < 0 or offset + 4 > len(image) or live[offset] and start not in seen:
            continue
        run = 0
        missed = 0
        while offset + 4 <= len(image) and run < 64 and missed < 2:
            if _is_code_byte(live, offset) and run:
                break
            word = struct.unpack_from("<I", image, offset)[0]
            target = word & ~1
            pointer = base <= target < end and (word & 1 or (word & 3) == 0)
            if pointer and target not in seen and not _is_code_byte(live, target - base):
                seen.add(target)
                pending.append(target)
                missed = 0
            elif 0 < word < 0x00100000 and run:
                missed = 0
            else:
                missed += 1
                if missed >= 2 and run:
                    break
            run += 1
            offset += 4
    ordered = sorted(seen)
    stops = sorted(set(ordered) | {base + index for index, flag in enumerate(live) if flag} | {end})
    for start in ordered:
        stop = next((candidate for candidate in stops if candidate > start), end)
        for addr in range(start, min(stop, end)):
            live[addr - base] = 1


def _is_code_byte(live: bytearray, offset: int) -> bool:
    return 0 <= offset < len(live) and live[offset] == 1


def _runs(live: bytearray, base: int, end: int) -> list[Gap]:
    found: list[Gap] = []
    start = None
    for index, flag in enumerate(live):
        if not flag and start is None:
            start = index
        elif flag and start is not None:
            if index - start >= 4:
                found.append(Gap(base + start, base + index))
            start = None
    if start is not None and end - (base + start) >= 4:
        found.append(Gap(base + start, end))
    return found
