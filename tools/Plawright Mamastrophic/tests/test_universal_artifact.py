#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "ci" / "build_universal_artifact.py"


def write_png(path: Path, width: int = 7, height: int = 5) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, data: bytes) -> bytes:
        payload = kind + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    path.write_bytes(signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class UniversalArtifactTests(unittest.TestCase):
    def run_builder(self, raw: Path, out: Path, exit_code: int = 0):
        return subprocess.run([
            sys.executable,
            str(SCRIPT),
            "--raw-root", str(raw),
            "--out-root", str(out),
            "--surface", "pc",
            "--mode", "screenshots",
            "--repo-head", "a" * 40,
            "--run-id", "123",
            "--run-attempt", "1",
            "--launch-strategy", "next-dev-ci",
            "--port", "3130",
            "--capture-exit-code", str(exit_code),
        ], text=True, capture_output=True, check=False)

    def fixture(self, root: Path, status: str = "PASS", with_png: bool = True):
        reports = root / "reports"
        reports.mkdir(parents=True)
        (reports / "summary.json").write_text(json.dumps({
            "status": status,
            "surface": "pc",
            "mode": "screenshots",
            "targetCount": 1,
            "screenshotCount": 1 if with_png else 0,
        }), encoding="utf-8")
        (reports / "capture-manifest.json").write_text(json.dumps({
            "recordCount": 1,
            "capturedCount": 1 if with_png else 0,
            "failedCount": 0,
            "skippedCount": 0,
            "missingCount": 0,
            "captured": [{"route": "/"}] if with_png else [],
            "failed": [], "skipped": [], "missing": [],
        }), encoding="utf-8")
        (reports / "surf8.capture-plan.json").write_text(json.dumps({
            "targetCount": 1,
            "macros": [{"id": "pc", "port": 3130}],
        }), encoding="utf-8")
        if with_png:
            write_png(root / "screens" / "pc" / "home.png", 11, 9)

    def test_pass_bundle_has_manifest_index_hashes_and_png_dimensions(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            raw, out = base / "raw", base / "out"
            self.fixture(raw)
            result = self.run_builder(raw, out)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            manifest = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "PASS")
            self.assertEqual(manifest["screenshotCount"], 1)
            rows = list(csv.DictReader((out / "INDEX.csv").open(encoding="utf-8-sig")))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["width"], "11")
            self.assertEqual(rows[0]["height"], "9")
            self.assertTrue((out / "screenshots" / rows[0]["file"]).is_file())
            self.assertIn("MANIFEST.json", (out / "SHA256SUMS.txt").read_text(encoding="utf-8"))

    def test_pass_without_png_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            raw, out = base / "raw", base / "out"
            self.fixture(raw, with_png=False)
            result = self.run_builder(raw, out)
            self.assertEqual(result.returncode, 2)
            manifest = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "FAIL")
            self.assertIn("NO_PNG_SCREENSHOTS_FOR_SCREENSHOT_MODE", manifest["failureReasons"])

    def test_missing_summary_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            raw, out = base / "raw", base / "out"
            raw.mkdir()
            write_png(raw / "screens" / "orphan.png")
            result = self.run_builder(raw, out)
            self.assertEqual(result.returncode, 2)
            manifest = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "FAIL")
            self.assertIn("MISSING_OR_INVALID_MAMASTROPHIC_SUMMARY_STATUS", manifest["failureReasons"])

    def test_nonzero_capture_exit_forces_fail(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            raw, out = base / "raw", base / "out"
            self.fixture(raw)
            result = self.run_builder(raw, out, exit_code=7)
            self.assertEqual(result.returncode, 2)
            manifest = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "FAIL")
            self.assertIn("MAMASTROPHIC_EXIT_CODE_7", manifest["failureReasons"])

    def test_partial_pass_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            raw, out = base / "raw", base / "out"
            self.fixture(raw, status="PARTIAL_PASS")
            result = self.run_builder(raw, out)
            self.assertEqual(result.returncode, 0)
            manifest = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "PARTIAL_PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
