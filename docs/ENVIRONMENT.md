# Environment

Checked on this Windows machine during the first implementation pass. No tool
version below was taken from an earlier agent's notes without looking.

| Tool | Result |
|---|---|
| Python | 3.12.10, `C:\Users\thisi\AppData\Local\Programs\Python\Python312\python.exe` |
| Git | 2.53.0.windows.2 |
| Java | OpenJDK 26.0.2 at `C:\Java\openjdk-26.0.2` |
| GitHub CLI | logged in as `diamond-one` |
| uv | 0.13.6. The emulator venv uses CPython 3.14.10 from uv |
| Renode | 1.17.0 portable, .NET 8.0.10, under `.tools/renode-1.17.0/`. Winget only offers 1.16.0, and that build cannot load this platform file |
| `mfreak` | not installed |
| REA | not installed |
| Ghidra | not installed |
| clang | 23.1.4 at `C:\Program Files\LLVM\bin\clang.exe`. No `arm-none-eabi-gcc` |
| WSL | not installed |

Origin (Cursor-hosted git) is not supported on native Windows. This repo is
on GitHub: `https://github.com/diamond-one/micro-orchid`.

## Reference checkouts

Cloned with `--depth 1` under `third_party/`. That directory is gitignored.
Do not commit it. ChoralRoot contains audio assets and is GPL-3; it was read
for musical behavior and was not copied into this tree.

| Repo | Commit |
|---|---|
| [gbryant/microfreak-emu](https://github.com/gbryant/microfreak-emu) | `9f80bc344936be4de67cd9ce92c59e8dbe16ddec` |
| [gbryant/microfreak-tools](https://github.com/gbryant/microfreak-tools) | `396fcf46090691f82560ddbe7deaa94d9bf5272f` |
| [Quixotic7/ChoralRootFM1](https://github.com/Quixotic7/ChoralRootFM1) | `bd7f431bd7bfe6202d931b8245a821eaf711fa64` |

`microfreak-emu` expects `microfreak-tools` as its sibling
`../microfreak-tools`. Both checkouts are under `third_party/`, so that
path is already right. `uv sync` has been run in `third_party/microfreak-emu`.

Windows cannot run the extensionless `renode` binary the emulator looks up,
and Renode 1.16.0 rejects the platform file this checkout ships (it was
adjusted for 1.17). `tools/renode_win.cs` is a small launcher. Point
`MF_RENODE` at the directory that contains the compiled launcher, and set
`TMPDIR` to the Windows temp directory before `uv run`:

```
$env:MF_RENODE = "C:\Users\thisi\dev\micro-orchid\.tools\renode-launch"
$env:TMPDIR = $env:TEMP
uv run mfemu boot --firmware C:\Users\thisi\Downloads\MicroFreak_Firmware_Update_5_0_0_2084.mff
```

`tools/microfreak-emu-windows.patch` is the local change to the gitignored
checkout: forward slashes in Renode scripts, a longer socket wait, the
compiler cache left off on Windows, and the QUADSPI JEDEC id built without
a static byte-array initializer. Reapply it after a fresh clone. Do not
commit `third_party/` or `.tools/`.

## Stock firmware

The user's `MicroFreak_Firmware_Update_5_0_0_2084.mff` was hashed in place.
It was not copied into the repo.

- container sha256: `c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c`
- main payload: 473,695 bytes, sha256 `54be2e0b695e2279602513e1a9ed39906408ba221a45e782b61273f0ef55d15f`

Those are different objects. The first is the whole `.mff`. The second is
the main application after the 64-byte header and trailing XOR are removed.
SuperFreaker 0.1.2 is diffed in `docs/SUPERFREAKER.md`. Both images have
been booted in Renode from those Downloads paths. Neither was copied into
the repo and neither was written to a device.

Stock 5.0.0.2084 reached `main()` at 6,915,574 instructions. The PC after
boot was `0x08023444`. SuperFreaker 0.1.2 reached `main()` at 6,915,727
instructions, with the PC at `0x08024FB6`. `SystemInit` was 2 instructions
and `__libc_init_array` was 160,218 on both. No bootloader was loaded; the
core entered the application at `0x0800C000`.
