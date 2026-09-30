#!/usr/bin/env python3
"""Trusted PRISMA merge gate for pull_request_target."""
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WORKSTREAM_DIR = ROOT / "apps/terminal-de-venta-system/tools/prisma-governance"
FACTORY_GATE = ROOT / "PRISMA Factory Ledger/tools/verify_prisma_anti_rework_gate.py"

CONTROL_PLANE = {
    ".github/workflows/forgeos-quality-gate.yml",
    ".github/workflows/prisma-required-merge-gate.yml",
    ".github/workflows/prisma-workstream-collision-gate.yml",
    ".github/workflows/prisma-factory-anti-rework-gate.yml",
    ".github/workflows/prisma-remote-automesh.yml",
    ".github/workflows/prisma-remote-automesh-revalidate.yml",
    ".github/workflows/gvae-all-surface-authority.yml",
    ".github/workflows/viscore1-cert.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/prisma-sync-sentinel-watch.yml",
    "tools/prisma-governance/prisma_required_merge_gate.py",
    "apps/terminal-de-venta-system/tools/prisma-governance/workstream_collision.py",
    "PRISMA Factory Ledger/tools/verify_prisma_anti_rework_gate.py",
    "tools/code-atlas/src/code_atlas/motors/prisma_mesh_gateway.py",
    "tools/code-atlas/src/code_atlas/motors/prisma_mesh_revalidation.py",
}

VISUAL_PREFIXES = (
    "prisma-html/",
    "apps/terminal-de-venta-system/.prisma-ui/",
    "apps/terminal-de-venta-system/tools/quality/",
)

SYNC_PREFIXES = (
    "tools/prisma-sentinels/sync-sentinel/",
    "apps/terminal-de-venta-system/products/tablet/app/src/server/sync/",
    "apps/terminal-de-venta-system/products/pc/app/prisma/",
    "apps/terminal-de-venta-system/products/mobile/app/app/api/mobile/",
    "apps/terminal-de-venta-system/shared/contracts/",
    "apps/terminal-de-venta-system/shared/twin-kernel/src/sync/",
    "apps/terminal-de-venta-system/prisma/",
    "pnpm-lock.yaml",
)

FORGEOS_PREFIXES = (
    "forgeos/",
    "docs/forgeos-foundation/",
)

def api_get(url: str, token: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GITHUB_API_ERROR:{exc.code}:{body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GITHUB_API_UNAVAILABLE:{exc}") from exc

def get_pr(repo: str, number: int, token: str) -> dict[str, Any]:
    value = api_get(f"https://api.github.com/repos/{repo}/pulls/{number}", token)
    if not isinstance(value, dict):
        raise RuntimeError("INVALID_PR_RESPONSE")
    return value

def get_pr_files(repo: str, number: int, token: str) -> list[str]:
    out: list[str] = []
    for page in range(1, 11):
        rows = api_get(
            f"https://api.github.com/repos/{repo}/pulls/{number}/files?per_page=100&page={page}",
            token,
        )
        if not isinstance(rows, list):
            raise RuntimeError("INVALID_PR_FILES_RESPONSE")
        out.extend(
            str(row["filename"]).replace("\\", "/")
            for row in rows
            if isinstance(row, dict) and isinstance(row.get("filename"), str)
        )
        if len(rows) < 100:
            break
    if len(out) > 1000:
        raise RuntimeError("PR_TOO_MANY_CHANGED_FILES")
    return sorted(set(out))

def get_check_runs(repo: str, sha: str, token: str) -> list[dict[str, Any]]:
    value = api_get(
        f"https://api.github.com/repos/{repo}/commits/{sha}/check-runs?per_page=100",
        token,
    )
    rows = value.get("check_runs") if isinstance(value, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError("INVALID_CHECK_RUNS_RESPONSE")
    return [row for row in rows if isinstance(row, dict)]

def fetch_head_file(repo: str, path: str, ref: str, token: str) -> str:
    from urllib.parse import quote
    row = api_get(
        f"https://api.github.com/repos/{repo}/contents/{quote(path, safe='/')}?ref={quote(ref, safe='')}",
        token,
    )
    if not isinstance(row, dict) or not isinstance(row.get("content"), str):
        raise RuntimeError(f"CONTROL_PLANE_FILE_UNAVAILABLE:{path}")
    try:
        return base64.b64decode(row["content"]).decode("utf-8")
    except Exception as exc:
        raise RuntimeError(f"CONTROL_PLANE_FILE_DECODE_FAILED:{path}:{type(exc).__name__}") from exc

def branch_protection_errors(payload: dict[str, Any]) -> list[str]:
    protection = payload.get("protection")
    if not isinstance(protection, dict):
        return ["MAIN_BRANCH_PROTECTION_MISSING"]
    if protection.get("enabled") is not True:
        return ["MAIN_BRANCH_PROTECTION_DISABLED"]
    checks_cfg = protection.get("required_status_checks")
    if not isinstance(checks_cfg, dict):
        return ["MAIN_REQUIRED_STATUS_CHECKS_MISSING"]
    if str(checks_cfg.get("enforcement_level") or "") != "everyone":
        return ["MAIN_REQUIRED_CHECKS_NOT_ENFORCED_FOR_ADMINS"]
    contexts = {str(value) for value in (checks_cfg.get("contexts") or [])}
    if "forgeos-quality-gate" not in contexts:
        return ["MAIN_CANONICAL_GATE_CONTEXT_MISSING"]
    return []

def main_branch_protection(repo: str, token: str) -> dict[str, Any]:
    payload = api_get(f"https://api.github.com/repos/{repo}/branches/main", token)
    if not isinstance(payload, dict):
        raise RuntimeError("INVALID_MAIN_BRANCH_RESPONSE")
    return payload

def control_plane_safety(repo: str, head_sha: str, token: str, changed: list[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    observations: list[str] = []
    workflow_files = [path for path in changed if path.startswith(".github/workflows/")]
    for path in workflow_files:
        content = fetch_head_file(repo, path, head_sha, token)
        low = content.lower()
        if re.search(r"^\s*contents\s*:\s*write\b", content, re.MULTILINE):
            errors.append("CONTROL_PLANE_WORKFLOW_WRITE_PERMISSION:" + path)
        if "pull_request_target" in low and re.search(r"ref\\s*:\\s*\\${\\{\\s*github\\.event\\.pull_request\\.head\\.sha\\s*\\}\\}", content):
            errors.append("CONTROL_PLANE_TARGET_CHECKOUTS_PR_HEAD:" + path)
        if "pull_request_target" in low and re.search(r"\bgit\s+push\b", low):
            errors.append("CONTROL_PLANE_TARGET_GIT_PUSH:" + path)
        if "pull_request_target" in low and "secrets." in low and "pull_request.head.sha" in low:
            errors.append("CONTROL_PLANE_TARGET_PR_SECRET_BOUNDARY:" + path)
        observations.append("CONTROL_PLANE_WORKFLOW_SCANNED:" + path)
    return sorted(set(errors)), observations

def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def is_control_plane(path: str) -> bool:
    return path in CONTROL_PLANE or path.startswith(".github/workflows/")

def governed(path: str, workstream_module) -> bool:
    return workstream_module.is_governed_path(path)

def path_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in prefixes)

def required_checks(changed: list[str]) -> list[tuple[str, str]]:
    required: list[tuple[str, str]] = [("guardrails", "exact")]
    if any(path_prefix(path, VISUAL_PREFIXES) for path in changed):
        required.append(("visual authority / readiness gates", "exact"))
    if any(path_prefix(path, SYNC_PREFIXES) for path in changed):
        required.append(("Sentinel ", "prefix"))
    if any(path_prefix(path, FORGEOS_PREFIXES) for path in changed):
        required.append(("forgeos-source-quality", "exact"))
    return required

def resolve_check(rows: list[dict[str, Any]], name: str, mode: str) -> dict[str, Any] | None:
    matches = [
        row for row in rows
        if (str(row.get("name") or "") == name if mode == "exact" else str(row.get("name") or "").startswith(name))
    ]
    if not matches:
        return None
    return max(matches, key=lambda row: str(row.get("completed_at") or row.get("started_at") or ""))

def wait_for_required_checks(
    repo: str,
    sha: str,
    token: str,
    changed: list[str],
    timeout_seconds: int = 900,
    poll_seconds: int = 15,
) -> tuple[list[str], list[str]]:
    required = required_checks(changed)
    deadline = time.time() + timeout_seconds
    while True:
        rows = get_check_runs(repo, sha, token)
        blockers: list[str] = []
        observations: list[str] = []
        for name, mode in required:
            row = resolve_check(rows, name, mode)
            if row is None:
                blockers.append("REQUIRED_CHECK_MISSING:" + name)
                continue
            status = str(row.get("status") or "").lower()
            conclusion = str(row.get("conclusion") or "").lower()
            observations.append(f"CHECK:{name}:{status}:{conclusion}")
            if status == "completed":
                if conclusion != "success":
                    blockers.append(f"REQUIRED_CHECK_NOT_GREEN:{name}:{conclusion}")
            else:
                blockers.append(f"REQUIRED_CHECK_NOT_COMPLETE:{name}:{status}")
        if not blockers:
            return [], observations
        if any(item.startswith("REQUIRED_CHECK_NOT_GREEN:") for item in blockers):
            return blockers, observations
        if time.time() >= deadline:
            return blockers + ["REQUIRED_CHECK_WAIT_TIMEOUT"], observations
        time.sleep(poll_seconds)

def evaluate(repository: str, number: int, token: str, expected_head: str) -> dict[str, Any]:
    item = get_pr(repository, number, token)
    state = str(item.get("state") or "").lower()
    base = item.get("base") if isinstance(item.get("base"), dict) else {}
    head = item.get("head") if isinstance(item.get("head"), dict) else {}
    base_ref = str(base.get("ref") or "")
    base_sha = str(base.get("sha") or "")
    head_sha = str(head.get("sha") or "")
    head_repo = str((head.get("repo") or {}).get("full_name") or "") if isinstance(head.get("repo"), dict) else ""

    if state != "open":
        return {"result": "BLOCKED_PR_NOT_OPEN", "errors": ["PR_NOT_OPEN"]}
    if base_ref != "main":
        return {"result": "BLOCKED_WRONG_BASE", "errors": [f"BASE_REF:{base_ref}"]}
    if not re.fullmatch(r"[0-9a-f]{40}", head_sha):
        return {"result": "BLOCKED_INVALID_HEAD", "errors": ["HEAD_SHA_INVALID"]}
    if expected_head and expected_head != head_sha:
        return {
            "result": "BLOCKED_HEAD_MISMATCH",
            "errors": [f"EXPECTED_HEAD:{expected_head}", f"ACTUAL_HEAD:{head_sha}"],
        }

    protection = main_branch_protection(repository, token)
    errors = branch_protection_errors(protection)
    observations = ["MAIN_BRANCH_PROTECTION_CHECKED"]

    changed = get_pr_files(repository, number, token)
    if not changed:
        errors.append("NO_CHANGED_FILES")

    control_changed = [path for path in changed if is_control_plane(path)]
    if control_changed and head_repo != repository:
        errors.append("CONTROL_PLANE_CHANGE_FROM_FORK")
    if control_changed:
        observations.append("CONTROL_PLANE_CHANGED:" + ",".join(control_changed))
        cp_errors, cp_observations = control_plane_safety(repository, head_sha, token, changed)
        errors.extend(cp_errors)
        observations.extend(cp_observations)

    workstream_module = import_module(WORKSTREAM_DIR / "workstream_collision.py", "prisma_workstream_collision")
    governed_scope = any(governed(path, workstream_module) for path in changed)

    if governed_scope:
        client = workstream_module.GitHubClient(repository, token)
        declaration_result = workstream_module.evaluate(client, number, expected_head=head_sha)
        observations.append("WORKSTREAM:" + str(declaration_result.get("result")))
        if declaration_result.get("result") not in {
            "PASS_NO_COLLISION",
            "PASS_NO_COLLISIONS",
            "PASS_NOT_GOVERNED_SCOPE",
        }:
            errors.append("WORKSTREAM_COLLISION_BLOCK:" + str(declaration_result.get("result")))

        declaration = declaration_result.get("workstream") or {}
        caps = declaration.get("capabilities") if isinstance(declaration, dict) else []
        if caps:
            factory = import_module(FACTORY_GATE, "prisma_factory_gate")
            authority = factory.read_authority(ROOT)
            request = {
                "schemaVersion": factory.SCHEMA,
                "mode": "PROPOSAL",
                "expectedHead": base_sha,
                "task": f"PR #{number}: {item.get('title', '')}",
                "capabilities": [
                    {"id": str(cap), "requestedAction": "VERIFY"} if isinstance(cap, str)
                    else {
                        "id": str(cap.get("id") or ""),
                        "requestedAction": str(cap.get("requestedAction") or "VERIFY"),
                    }
                    for cap in caps
                ],
                "visualMutation": any(path_prefix(path, VISUAL_PREFIXES) for path in changed),
            }
            factory_result = factory.decide(
                ROOT,
                authority,
                request,
                current_head=base_sha,
                dirty=[],
            )
            observations.append("FACTORY_LEDGER:" + str(factory_result.get("result")))
            if factory_result.get("result") != "PASS_ANTI_REWORK_GATE":
                errors.append(
                    "FACTORY_LEDGER_BLOCK:" + ";".join(factory_result.get("errors") or [])
                )

    external_errors, external_observations = wait_for_required_checks(
        repository, head_sha, token, changed
    )
    errors.extend(external_errors)
    observations.extend(external_observations)

    final_item = get_pr(repository, number, token)
    final_head = str(
        ((final_item.get("head") or {}) if isinstance(final_item.get("head"), dict) else {}).get("sha") or ""
    )
    if final_head != head_sha:
        errors.append(f"HEAD_MOVED_DURING_GATE:{head_sha}:{final_head}")

    final_result = (
        "PASS_PRISMA_CANONICAL_MERGE_GATE"
        if not errors
        else "BLOCKED_PRISMA_CANONICAL_MERGE_GATE"
    )
    return {
        "schemaVersion": "prisma.required-merge-gate.v1",
        "result": final_result,
        "repository": repository,
        "pr": number,
        "baseRef": base_ref,
        "baseSha": base_sha,
        "headSha": head_sha,
        "headRepository": head_repo,
        "changedFiles": changed,
        "controlPlaneChanged": control_changed,
        "checksObserved": observations,
        "errors": sorted(set(errors)),
        "adminMergeAllowed": False,
        "sourceExecutionFromPR": False,
        "postMergeProofRequired": True,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--pr-number", type=int, default=int(os.environ.get("PRISMA_PR_NUMBER", "0") or 0))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    parser.add_argument("--expected-head", default=os.environ.get("PRISMA_EXPECTED_HEAD", ""))
    args = parser.parse_args()
    if not args.repo or not args.pr_number or not args.token:
        print(json.dumps({
            "result": "BLOCKED_PRISMA_CANONICAL_MERGE_GATE",
            "errors": ["REPOSITORY_PR_NUMBER_TOKEN_REQUIRED"],
        }, indent=2))
        return 2
    try:
        result = evaluate(args.repo, args.pr_number, args.token, args.expected_head)
    except Exception as exc:
        result = {
            "result": "BLOCKED_PRISMA_CANONICAL_MERGE_GATE",
            "errors": [f"{type(exc).__name__}:{exc}"],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("result") == "PASS_PRISMA_CANONICAL_MERGE_GATE" else 2

if __name__ == "__main__":
    raise SystemExit(main())
