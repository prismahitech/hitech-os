#!/usr/bin/env python3
"""Trusted PRISMA merge gate for pull_request_target."""
from __future__ import annotations
import argparse, importlib.util, json, os, re, sys, urllib.error, urllib.request
from pathlib import Path

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
VISUAL_PREFIXES = ("prisma-html/", "apps/terminal-de-venta-system/.prisma-ui/", "apps/terminal-de-venta-system/tools/quality/")
SYNC_PREFIXES = ("tools/prisma-sentinels/sync-sentinel/", "apps/terminal-de-venta-system/products/tablet/app/src/server/sync/", "apps/terminal-de-venta-system/products/pc/app/prisma/", "apps/terminal-de-venta-system/products/mobile/app/app/api/mobile/", "apps/terminal-de-venta-system/shared/contracts/", "apps/terminal-de-venta-system/shared/twin-kernel/src/sync/", "apps/terminal-de-venta-system/prisma/", "pnpm-lock.yaml")
FORGEOS_PREFIXES = ("forgeos/", "docs/forgeos-foundation/")

def api_get(url: str, token: str):
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token: headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GITHUB_API_ERROR:{exc.code}:{body[:500]}") from exc

def pr(repo: str, number: int, token: str):
    value = api_get(f"https://api.github.com/repos/{repo}/pulls/{number}", token)
    if not isinstance(value, dict): raise RuntimeError("INVALID_PR_RESPONSE")
    return value

def files(repo: str, number: int, token: str):
    out = []
    for page in range(1, 11):
        rows = api_get(f"https://api.github.com/repos/{repo}/pulls/{number}/files?per_page=100&page={page}", token)
        if not isinstance(rows, list): raise RuntimeError("INVALID_PR_FILES_RESPONSE")
        out.extend(str(x["filename"]).replace("\\", "/") for x in rows if isinstance(x, dict) and isinstance(x.get("filename"), str))
        if len(rows) < 100: break
    if len(out) > 1000: raise RuntimeError("PR_TOO_MANY_CHANGED_FILES")
    return sorted(set(out))

def fetch_head_file(repo: str, path: str, ref: str, token: str) -> str:
    from urllib.parse import quote
    row = api_get(f"https://api.github.com/repos/{repo}/contents/{quote(path, safe='/')}?ref={quote(ref, safe='')}", token)
    if not isinstance(row, dict) or not isinstance(row.get("content"), str):
        raise RuntimeError(f"CONTROL_PLANE_FILE_UNAVAILABLE:{path}")
    try:
        import base64
        return base64.b64decode(row["content"]).decode("utf-8")
    except Exception as exc:
        raise RuntimeError(f"CONTROL_PLANE_FILE_DECODE_FAILED:{path}:{type(exc).__name__}") from exc

def control_plane_safety(repo: str, head_sha: str, token: str, changed: list[str]) -> tuple[list[str], list[str]]:
    errors=[]; observations=[]
    workflow_files=[p for p in changed if p.startswith(".github/workflows/")]
    for path in workflow_files:
        text=fetch_head_file(repo,path,head_sha,token)
        low=text.lower()
        if "contents: write" in low:
            errors.append("CONTROL_PLANE_WORKFLOW_WRITE_PERMISSION:" + path)
        if "pull_request_target" in low and "github.event.pull_request.head.sha" in low and "actions/checkout" in low:
            errors.append("CONTROL_PLANE_TARGET_CHECKOUTS_PR_HEAD:" + path)
        if "pull_request_target" in low and "git push" in low:
            errors.append("CONTROL_PLANE_TARGET_GIT_PUSH:" + path)
        if "pull_request_target" in low and "secrets." in low and "pull_request.head.sha" in low:
            errors.append("CONTROL_PLANE_TARGET_PR_SECRET_BOUNDARY:" + path)
        observations.append("CONTROL_PLANE_WORKFLOW_SCANNED:" + path)
    return sorted(set(errors)), observations

def checks(repo: str, sha: str, token: str):
    value = api_get(f"https://api.github.com/repos/{repo}/commits/{sha}/check-runs?per_page=100", token)
    rows = value.get("check_runs") if isinstance(value, dict) else None
    if not isinstance(rows, list): raise RuntimeError("INVALID_CHECK_RUNS_RESPONSE")
    return [x for x in rows if isinstance(x, dict)]

def wait_for_required_checks(repo: str, sha: str, token: str, changed: list[str], timeout_seconds: int = 900, poll_seconds: int = 15):
    required = required_checks(changed)
    if not required: return [], []
    import time
    deadline = time.time() + timeout_seconds
    last_rows = []
    while True:
        last_rows = checks(repo, sha, token)
        blockers, observations = [], []
        for name, mode in required:
            row = resolve_check(last_rows, name, mode)
            if row is None:
                blockers.append("REQUIRED_CHECK_MISSING:" + name)
                continue
            status = str(row.get("status") or "").lower(); conclusion = str(row.get("conclusion") or "").lower()
            observations.append(f"CHECK:{name}:{status}:{conclusion}")
            if status != "completed":
                blockers.append(f"REQUIRED_CHECK_NOT_COMPLETE:{name}:{status}")
            elif conclusion != "success":
                blockers.append(f"REQUIRED_CHECK_NOT_GREEN:{name}:{conclusion}")
        if not blockers or all(x.startswith("REQUIRED_CHECK_NOT_GREEN:") for x in blockers):
            return blockers, observations
        if time.time() >= deadline:
            return blockers + ["REQUIRED_CHECK_WAIT_TIMEOUT"], observations
        time.sleep(poll_seconds)

def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None: raise RuntimeError(f"IMPORT_FAILED:{path}")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def is_control_plane(path: str) -> bool: return path in CONTROL_PLANE or path.startswith(".github/workflows/")

def governed(path: str, wc) -> bool: return wc.is_governed_path(path)
def prefix(path: str, prefixes) -> bool: return any(path == p.rstrip("/") or path.startswith(p) for p in prefixes)

def required_checks(changed):
    req = [("guardrails", "exact")]
    if any(prefix(p, VISUAL_PREFIXES) for p in changed): req.append(("visual authority / readiness gates", "exact"))
    if any(prefix(p, SYNC_PREFIXES) for p in changed): req.append(("Sentinel ", "prefix"))
    if any(prefix(p, FORGEOS_PREFIXES) for p in changed): req.append(("forgeos-source-quality", "exact"))
    return req

def resolve_check(rows, name, mode):
    matches = [r for r in rows if (str(r.get("name") or "") == name if mode == "exact" else str(r.get("name") or "").startswith(name))]
    if not matches: return None
    return max(matches, key=lambda r: str(r.get("completed_at") or r.get("started_at") or ""))

def evaluate(repo: str, number: int, token: str, expected_head: str):
    item = pr(repo, number, token)
    state = str(item.get("state") or "").lower()
    base = item.get("base") if isinstance(item.get("base"), dict) else {}
    head = item.get("head") if isinstance(item.get("head"), dict) else {}
    base_ref, base_sha, head_sha = str(base.get("ref") or ""), str(base.get("sha") or ""), str(head.get("sha") or "")
    head_repo = str((head.get("repo") or {}).get("full_name") or "") if isinstance(head.get("repo"), dict) else ""
    if state != "open": return {"result":"BLOCKED_PR_NOT_OPEN","errors":["PR_NOT_OPEN"]}
    if base_ref != "main": return {"result":"BLOCKED_WRONG_BASE","errors":[f"BASE_REF:{base_ref}"]}
    if not re.fullmatch(r"[0-9a-f]{40}", head_sha): return {"result":"BLOCKED_INVALID_HEAD","errors":["HEAD_SHA_INVALID"]}
    if expected_head and expected_head != head_sha: return {"result":"BLOCKED_HEAD_MISMATCH","errors":[f"EXPECTED_HEAD:{expected_head}",f"ACTUAL_HEAD:{head_sha}"]}
    changed = files(repo, number, token); run_rows = checks(repo, head_sha, token)
    errors = []; observations = []
    control_changed = [p for p in changed if is_control_plane(p)]
    if control_changed and head_repo != repo: errors.append("CONTROL_PLANE_CHANGE_FROM_FORK")
    if control_changed: observations.append("CONTROL_PLANE_CHANGED:" + ",".join(control_changed))
    if control_changed:
        cp_errors, cp_observations = control_plane_safety(repo, head_sha, token, changed)
        errors.extend(cp_errors)
        observations.extend(cp_observations)
    wc = import_module(WORKSTREAM_DIR / "workstream_collision.py", "prisma_workstream_collision")
    governed_scope = any(governed(p, wc) for p in changed)
    if governed_scope:
        client = wc.GitHubClient(repo, token)
        result = wc.evaluate(client, number, expected_head=head_sha)
        observations.append("WORKSTREAM:" + str(result.get("result")))
        if result.get("result") not in {"PASS_NO_COLLISION", "PASS_NO_COLLISIONS", "PASS_NOT_GOVERNED_SCOPE"}:
            errors.append("WORKSTREAM_COLLISION_BLOCK:" + str(result.get("result")))
        selected = result.get("workstream") or {}
        declaration_caps = selected.get("capabilities") if isinstance(selected, dict) else []
        if declaration_caps:
            factory = import_module(FACTORY_GATE, "prisma_factory_gate")
            authority = factory.read_authority(ROOT)
            request = {
                "schemaVersion": factory.SCHEMA, "mode": "PROPOSAL", "expectedHead": base_sha,
                "task": f"PR #{number}: {item.get('title', '')}",
                "capabilities": [{"id": str(x), "requestedAction": "VERIFY"} if isinstance(x, str) else {"id": str(x.get("id") or ""), "requestedAction": str(x.get("requestedAction") or "VERIFY")} for x in declaration_caps],
                "visualMutation": any(prefix(p, VISUAL_PREFIXES) for p in changed),
            }
            fres = factory.decide(ROOT, authority, request, current_head=base_sha, dirty=[])
            observations.append("FACTORY_LEDGER:" + str(fres.get("result")))
            if fres.get("result") != "PASS_ANTI_REWORK_GATE": errors.append("FACTORY_LEDGER_BLOCK:" + ";".join(fres.get("errors") or []))
    ext_errors, ext_observations = wait_for_required_checks(repo, head_sha, token, changed)
    errors.extend(ext_errors)
    observations.extend(ext_observations)
    final_item = pr(repo, number, token)
    final_head = str(((final_item.get("head") or {}) if isinstance(final_item.get("head"), dict) else {}).get("sha") or "")
    if final_head != head_sha: errors.append(f"HEAD_MOVED_DURING_GATE:{head_sha}:{final_head}")
    result = "PASS_PRISMA_CANONICAL_MERGE_GATE" if not errors else "BLOCKED_PRISMA_CANONICAL_MERGE_GATE"
    return {"schemaVersion":"prisma.required-merge-gate.v1","result":result,"repository":repo,"pr":number,"baseRef":base_ref,"baseSha":base_sha,"headSha":head_sha,"headRepository":head_repo,"changedFiles":changed,"controlPlaneChanged":control_changed,"checksObserved":observations,"errors":sorted(set(errors)),"adminMergeAllowed":False,"sourceExecutionFromPR":False,"postMergeProofRequired":True}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY","")); ap.add_argument("--pr-number", type=int, default=int(os.environ.get("PRISMA_PR_NUMBER","0") or 0)); ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN","")); ap.add_argument("--expected-head", default=os.environ.get("PRISMA_EXPECTED_HEAD","")); args = ap.parse_args()
    if not args.repo or not args.pr_number or not args.token: print(json.dumps({"result":"BLOCKED_PRISMA_CANONICAL_MERGE_GATE","errors":["REPOSITORY_PR_NUMBER_TOKEN_REQUIRED"]}, indent=2)); return 2
    try: result = evaluate(args.repo, args.pr_number, args.token, args.expected_head)
    except Exception as exc: result = {"result":"BLOCKED_PRISMA_CANONICAL_MERGE_GATE","errors":[f"{type(exc).__name__}:{exc}"]}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)); return 0 if result.get("result") == "PASS_PRISMA_CANONICAL_MERGE_GATE" else 2
if __name__ == "__main__": raise SystemExit(main())
