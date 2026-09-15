#!/usr/bin/env python3
"""Build a uniform, fail-closed GitHub artifact from Mamastrophic raw capture output.

This is a thin packaging adapter. It does not discover routes, launch apps, capture
screens, or invent runtime truth. Those remain owned by PRISMA Plawright
Mamastrophic.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "prisma.mamastrophic.universal-screenshot-artifact.v1"
ALLOWED_STATUS = {"PASS", "PARTIAL_PASS", "FAIL"}
ALLOWED_SURFACES = {"pc", "tablet", "mobile", "web", "chart-lab", "control-center"}
ALLOWED_MODES = {"screenshots", "screenshotsqa"}
MAX_SCREENSHOT_FILENAME_BYTES = 180


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def png_size(path: Path) -> tuple[int | None, int | None]:
    try:
        with path.open("rb") as fh:
            header = fh.read(24)
        if len(header) >= 24 and header[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", header[16:24])
    except Exception:
        pass
    return None, None


def safe_token(value: str) -> str:
    out = []
    for ch in value:
        out.append(ch if ch.isalnum() or ch in "._-" else "_")
    token = "".join(out).strip("._-")
    return token or "item"


def _utf8_prefix(value: str, max_bytes: int) -> str:
    if len(value.encode("utf-8")) <= max_bytes:
        return value
    return value.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore").rstrip("._-")


def unique_screenshot_name(rel: str, used: set[str]) -> str:
    p = Path(rel)
    stem = safe_token("__".join(p.with_suffix("").parts))
    base = f"{stem}.png"
    if len(base.encode("utf-8")) > MAX_SCREENSHOT_FILENAME_BYTES or base in used:
        digest = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:12]
        suffix = f"__{digest}.png"
        room = MAX_SCREENSHOT_FILENAME_BYTES - len(suffix.encode("utf-8"))
        bounded = _utf8_prefix(stem, room) or "item"
        base = f"{bounded}{suffix}"
    if base in used:
        raise RuntimeError(f"Deterministic screenshot filename collision for {rel!r}: {base!r}")
    used.add(base)
    return base


def copy_non_png_evidence(raw_root: Path, evidence_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for src in sorted(p for p in raw_root.rglob("*") if p.is_file() and p.suffix.lower() != ".png"):
        rel = src.relative_to(raw_root)
        dst = evidence_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        rows.append({
            "path": rel.as_posix(),
            "bytes": dst.stat().st_size,
            "sha256": sha256(dst),
        })
    return rows


def normalize_route_status(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        return {
            "captured": [],
            "failed": [],
            "skipped": [],
            "missing": [],
            "sourceAvailable": False,
        }
    return {
        "captured": manifest.get("captured") if isinstance(manifest.get("captured"), list) else [],
        "failed": manifest.get("failed") if isinstance(manifest.get("failed"), list) else [],
        "skipped": manifest.get("skipped") if isinstance(manifest.get("skipped"), list) else [],
        "missing": manifest.get("missing") if isinstance(manifest.get("missing"), list) else [],
        "sourceAvailable": True,
        "counts": {
            "recordCount": manifest.get("recordCount"),
            "targetRecordCount": manifest.get("targetRecordCount"),
            "screenshotCount": manifest.get("screenshotCount"),
            "capturedCount": manifest.get("capturedCount"),
            "failedCount": manifest.get("failedCount"),
            "skippedCount": manifest.get("skippedCount"),
            "missingCount": manifest.get("missingCount"),
            "scrollCoverageCompleteCount": manifest.get("scrollCoverageCompleteCount"),
            "scrollCoveragePartialCount": manifest.get("scrollCoveragePartialCount"),
            "scrollCoverageFailedCount": manifest.get("scrollCoverageFailedCount"),
        },
    }


def write_readme(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        "\n".join([
            "# PRISMA Mamastrophic universal screenshot artifact",
            "",
            f"- Surface: \`{data['surface']}\`",
            f"- Mode: \`{data['mode']}\`",
            f"- Status: **{data['status']}**",
            f"- Repo HEAD: \`{data['repoHead']}\`",
            f"- GitHub run: \`{data['runId']}\` attempt \`{data['runAttempt']}\`",
            f"- Screenshots: **{data['screenshotCount']}**",
            f"- Runtime launch strategy: \`{data['launchStrategy']}\`",
            "",
            "## Contract",
            "",
            "- \`screenshots/\`: one normalized PNG file per captured visual image.",
            "- \`INDEX.csv\`: screenshot filename, original Mamastrophic path, hash, bytes and PNG dimensions.",
            "- \`MANIFEST.json\`: artifact status and capture summary.",
            "- \`ROUTE_STATUS.json\`: captured / failed / skipped / missing route evidence from Mamastrophic.",
            "- \`PROVENANCE.json\`: GitHub run, commit, surface, mode and launch provenance.",
            "- \`SHA256SUMS.txt\`: integrity hashes for every packaged file except itself.",
            "- \`evidence/\`: original non-PNG Mamastrophic reports/logs used to derive the bundle.",
            "",
            "This artifact is evidence, not mutation authority. PASS means the selected runtime capture completed under the",
            "Mamastrophic contract. It does not by itself prove production deployment, customer data, or visual correctness.",
            "",
        ]) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-root", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--surface", required=True, choices=sorted(ALLOWED_SURFACES))
    ap.add_argument("--mode", required=True, choices=sorted(ALLOWED_MODES))
    ap.add_argument("--repo-head", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--run-attempt", required=True)
    ap.add_argument("--workflow", default="mamastrophic-universal-screenshots")
    ap.add_argument("--launch-strategy", required=True)
    ap.add_argument("--port", required=True, type=int)
    ap.add_argument("--capture-exit-code", required=True, type=int)
    args = ap.parse_args()

    raw = Path(args.raw_root).resolve()
    out = Path(args.out_root).resolve()
    if not raw.is_dir():
        print(f"RAW_ROOT_MISSING={raw}", file=sys.stderr)
        return 2
    if out.exists():
        shutil.rmtree(out)
    shots_dir = out / "screenshots"
    evidence_dir = out / "evidence"
    shots_dir.mkdir(parents=True)
    evidence_dir.mkdir(parents=True)

    summary_path = raw / "reports" / "summary.json"
    capture_manifest_path = raw / "reports" / "capture-manifest.json"
    plan_path = raw / "reports" / "surf8.capture-plan.json"
    summary = read_json(summary_path, {})
    capture_manifest = read_json(capture_manifest_path, {})
    plan = read_json(plan_path, {})

    raw_status = summary.get("status") if isinstance(summary, dict) else None
    reasons: list[str] = []
    partial_reasons: list[str] = []
    status = raw_status if raw_status in ALLOWED_STATUS else "FAIL"
    if raw_status not in ALLOWED_STATUS:
        reasons.append("MISSING_OR_INVALID_MAMASTROPHIC_SUMMARY_STATUS")
    if status == "PASS" and isinstance(summary, dict):
        try:
            partial_scroll_count = int(summary.get("scrollCoveragePartialCount") or 0)
        except (TypeError, ValueError):
            partial_scroll_count = 0
        if partial_scroll_count > 0:
            status = "PARTIAL_PASS"
            partial_reasons.append("SCROLL_COVERAGE_PARTIAL")
    if args.capture_exit_code != 0:
        status = "FAIL"
        reasons.append(f"MAMASTROPHIC_EXIT_CODE_{args.capture_exit_code}")

    used: set[str] = set()
    screenshot_rows: list[dict[str, Any]] = []
    for src in sorted(p for p in raw.rglob("*.png") if p.is_file()):
        rel = src.relative_to(raw).as_posix()
        name = unique_screenshot_name(rel, used)
        dst = shots_dir / name
        shutil.copy2(src, dst)
        width, height = png_size(dst)
        screenshot_rows.append({
            "file": name,
            "original_path": rel,
            "sha256": sha256(dst),
            "bytes": dst.stat().st_size,
            "width": width,
            "height": height,
        })

    if status in {"PASS", "PARTIAL_PASS"} and not screenshot_rows:
        status = "FAIL"
        reasons.append("NO_PNG_SCREENSHOTS_FOR_SCREENSHOT_MODE")

    evidence_rows = copy_non_png_evidence(raw, evidence_dir)
    route_status = normalize_route_status(capture_manifest)
    route_status["surface"] = args.surface
    route_status["mode"] = args.mode
    (out / "ROUTE_STATUS.json").write_text(
        json.dumps(route_status, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with (out / "INDEX.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["file", "original_path", "sha256", "bytes", "width", "height"],
        )
        writer.writeheader()
        writer.writerows(screenshot_rows)

    provenance = {
        "schema": SCHEMA,
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "repoHead": args.repo_head,
        "workflow": args.workflow,
        "runId": str(args.run_id),
        "runAttempt": str(args.run_attempt),
        "surface": args.surface,
        "mode": args.mode,
        "port": args.port,
        "launchStrategy": args.launch_strategy,
        "captureExitCode": args.capture_exit_code,
        "productionCertified": False,
        "mutationAuthority": False,
        "notes": [
            "Mobile means the existing PRISMA Mobile/PWA web runtime surface on port 3140.",
            "The universal artifact adapter does not mutate product source or runtime data.",
        ],
    }
    (out / "PROVENANCE.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "schema": SCHEMA,
        "status": status,
        "sourceStatus": raw_status,
        "failureReasons": reasons,
        "partialReasons": partial_reasons,
        "surface": args.surface,
        "mode": args.mode,
        "repoHead": args.repo_head,
        "runId": str(args.run_id),
        "runAttempt": str(args.run_attempt),
        "port": args.port,
        "launchStrategy": args.launch_strategy,
        "captureExitCode": args.capture_exit_code,
        "screenshotCount": len(screenshot_rows),
        "evidenceFileCount": len(evidence_rows),
        "mamastrophicSummary": summary if isinstance(summary, dict) else {},
        "capturePlan": {
            "targetCount": plan.get("targetCount") if isinstance(plan, dict) else None,
            "macros": plan.get("macros") if isinstance(plan, dict) else None,
        },
        "noFakeGreen": status == "FAIL" or len(screenshot_rows) > 0,
        "productionCertified": False,
    }
    (out / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme(out / "README.md", manifest)

    sum_rows: list[str] = []
    for p in sorted(x for x in out.rglob("*") if x.is_file() and x.name != "SHA256SUMS.txt"):
        sum_rows.append(f"{sha256(p)}  {p.relative_to(out).as_posix()}")
    (out / "SHA256SUMS.txt").write_text("\n".join(sum_rows) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": status,
        "surface": args.surface,
        "mode": args.mode,
        "screenshots": len(screenshot_rows),
        "evidenceFiles": len(evidence_rows),
        "out": str(out),
        "reasons": reasons,
        "partialReasons": partial_reasons,
    }, ensure_ascii=False))
    return 0 if status in {"PASS", "PARTIAL_PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
