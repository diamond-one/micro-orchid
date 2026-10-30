"""Run the checks this machine can actually perform.

Firmware boot, Renode, and a native patch are reported BLOCKED or NOT RUN.
They are never reported as a pass when the stock image or the tool is absent.
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from firmware.boundaries import (  # noqa: E402
    PATCH_MANIFEST,
    STOCK_MFF_SHA256,
    STOCK_PAYLOAD_SHA256,
    STOCK_PAYLOAD_SIZE,
)


def _tool(name: str) -> dict:
    path = shutil.which(name)
    return {"name": name, "status": "PASS" if path else "BLOCKED", "path": path}


def _firmware() -> dict:
    folder = ROOT / "firmware" / "stock"
    found = []
    if folder.exists():
        found = [str(path) for path in folder.iterdir() if path.is_file()]
    if not found:
        return {
            "status": "BLOCKED",
            "detail": (
                "Stock 5.0.0.2084 was hashed outside this repo and is not "
                "copied here. A separate Renode boot reached main(); this "
                "script does not repeat that boot."
            ),
            "expected_mff_sha256": STOCK_MFF_SHA256,
            "expected_payload_sha256": STOCK_PAYLOAD_SHA256,
            "expected_payload_bytes": STOCK_PAYLOAD_SIZE,
        }
    return {"status": "NOT RUN", "detail": "Image present but not hashed by this pass.", "files": found}


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    unit = {
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "ran": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
    }
    tools = [_tool(name) for name in ("python", "git", "uv", "renode", "java")]
    firmware = _firmware()
    native = {
        "status": "BLOCKED",
        "detail": (
            "scripts/release_recipe.py builds the image in memory. "
            "This script does not boot it and does not write a device."
        ),
        "manifest_entries": len(PATCH_MANIFEST),
    }
    report = {
        "unit": unit,
        "tools": tools,
        "firmware": firmware,
        "emulator_boot": {"status": "BLOCKED", "detail": "Renode and the stock image are required."},
        "native_patch": native,
        "hardware_flash": {"status": "NOT RUN", "detail": "Physical flashing is not authorized."},
        "python": sys.version,
        "platform": platform.platform(),
    }
    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    (out / "verify.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"unit tests: {unit['status']} ({unit['ran']} ran, {unit['failures']} failed, {unit['errors']} errors)",
        f"stock firmware: {firmware['status']}",
        f"emulator boot: {report['emulator_boot']['status']}",
        f"native patch: {native['status']}",
        f"hardware flash: {report['hardware_flash']['status']}",
    ]
    for tool in tools:
        lines.append(f"tool {tool['name']}: {tool['status']}")
    text = "\n".join(lines) + "\n"
    (out / "verify.txt").write_text(text, encoding="utf-8")
    print(text, end="")
    if not result.wasSuccessful():
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
