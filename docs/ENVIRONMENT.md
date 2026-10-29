# Environment

Checked on this Windows machine during the first implementation pass. No tool
version below was taken from an earlier agent's notes without looking.

| Tool | Result |
|---|---|
| Python | 3.12.10, `C:\Users\thisi\AppData\Local\Programs\Python\Python312\python.exe` |
| Git | 2.53.0.windows.2 |
| Java | OpenJDK 26.0.2 at `C:\Java\openjdk-26.0.2` |
| GitHub CLI | logged in as `diamond-one` |
| uv | not installed |
| Renode | not installed |
| `mfreak` | not installed |
| REA | not installed |
| Ghidra | not installed |
| `gcc` / `clang` / `arm-none-eabi-gcc` | not installed |
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

`microfreak-emu` expects `microfreak-tools` as a sibling checkout named
`../microfreak-tools` before `uv sync`. The copies here live under
`third_party/` instead, so a later emulator setup must either move them or
point uv at those paths. `uv sync` was not run.

## Stock firmware

Not on this machine. Nothing was downloaded.

`microfreak-tools` 0.1.0 accepts one payload, and only that payload:

- name: `fw 5.0.0.2084 (nanowave_main__fw5_0_0_2084__2023_05_30.bin)`
- size: 473,695 bytes
- sha256: `54be2e0b695e2279602513e1a9ed39906408ba221a45e782b61273f0ef55d15f`

The mission notes also quote `c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c`.
That digest was not checked against a file. It is recorded in
`firmware/boundaries.py` as unverified. Do not treat the two hashes as the
same object.

Put an officially obtained `.mff` in `firmware/stock/` when one is available.
The verify script will still report the image as not booted until Renode is
installed and a boot is actually run.
