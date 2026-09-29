#!/usr/bin/env python3
"""PRISMA live workstream collision guard.

Coordination adapter only: it reads GitHub PR metadata and changed paths to
prevent concurrent governed writers from implementing the same workstream.
It does not create capability or authority truth and never mutates GitHub.
"""

from __future__ import annotations

import argparse
import base64
import fnmatch
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable

SCHEMA = "prisma.workstream-collision-gate.v1"
DECLARATION_RE = re.compile(r"<!--\s*PRISMA-WORKSTREAM\s*(?P<body>.*?)-->", re.IGNORECASE | re.DOTALL)
KEY_RE = re.compile(r"^(?P<key>[a-z_]+)\s*:\s*(?P<value>.*)$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,127}$")
CAP_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,127}$")
ACTION_VALUES = {"VERIFY", "ADVANCE", "FIX", "BUILD", "EXTERNAL", "REUSE", "REBUILD"}
ROLE_VALUES = {"canonical", "proposal", "continuation"}

EXCLUSIVE_PREFIXES = (
    "PRISMA Factory Ledger/",
    "apps/terminal-de-venta-system/tools/prisma-governance/",
    "prisma-html/tools/visual_promotion/canonical_registration/",
    "prisma-html/authority/rifat/",
    "prisma-html/authority/ndc/",
    "tools/code-atlas/src/code_atlas/motors/prisma_mesh_gateway.py",
    "tools/code-atlas/src/code_atlas/motors/prisma_mesh_revalidation.py",
    ".github/workflows/prisma-remote-automesh.yml",
    ".github/workflows/prisma-remote-automesh-revalidate.yml",
    ".github/workflows/prisma-factory-anti-rework-gate.yml",
)

GOVERNED_PREFIXES = EXCLUSIVE_PREFIXES + (
    ".github/workflows/",
    "prisma-html/tools/visual_promotion/",
    "prisma-html/tools/visual_operating_graph/",
    "tools/code-atlas/",
)

PROTECTED_METADATA_CAPABILITY_PATH = "PRISMA Factory Ledger/PRISMA_FACTORY_LEDGER.json"


class GateError(RuntimeError):
    pass


@dataclass(frozen=True)
class Declaration:
    workstream_id: str
    role: str
    requested_action: str
    capabilities: tuple[str, ...]
    surfaces: tuple[str, ...]
    scope: tuple[str, ...]
    owner: str | None = None


@dataclass
class PullRequestView:
    number: int
    title: str
    body: str
    state: str
    draft: bool
    head_sha: str
    base_sha: str
    created_at: str
    updated_at: str
    declaration: Declaration | None
    changed_files: list[str]

    @property
    def governed(self) -> bool:
        return any(is_governed_path(path) for path in self.changed_files)


class GitHubClient:
    def __init__(self, repo: str, token: str) -> None:
        self.repo = repo
        self.token = token

    def get(self, path: str, params: dict[str, str] | None = None) -> Any:
        query = urllib.parse.urlencode(params or {})
        url = f"https://api.github.com{path}"
        if query:
            url += "?" + query
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "prisma-workstream-collision-gate/1",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise GateError(f"GITHUB_API_ERROR:{exc.code}:{body[:500]}") from exc
        except urllib.error.URLError as exc:
            raise GateError(f"GITHUB_API_UNAVAILABLE:{exc}") from exc

    def open_pull_requests(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for page in range(1, 11):
            rows = self.get(
                f"/repos/{self.repo}/pulls",
                {"state": "open", "per_page": "100", "page": str(page), "sort": "created", "direction": "asc"},
            )
            if not isinstance(rows, list):
                raise GateError("INVALID_OPEN_PRS_RESPONSE")
            result.extend(row for row in rows if isinstance(row, dict))
            if len(rows) < 100:
                return result
        raise GateError("OPEN_PR_SET_EXCEEDS_SAFE_SCAN_LIMIT")

    def pull_request(self, number: int) -> dict[str, Any]:
        row = self.get(f"/repos/{self.repo}/pulls/{number}")
        if not isinstance(row, dict):
            raise GateError(f"INVALID_PR_RESPONSE:{number}")
        return row

    def pull_request_files(self, number: int) -> list[str]:
        result: list[str] = []
        for page in range(1, 11):
            rows = self.get(
                f"/repos/{self.repo}/pulls/{number}/files",
                {"per_page": "100", "page": str(page)},
            )
            if not isinstance(rows, list):
                raise GateError(f"INVALID_PR_FILES_RESPONSE:{number}:{page}")
            for row in rows:
                if isinstance(row, dict) and isinstance(row.get("filename"), str):
                    result.append(row["filename"].replace("\\", "/"))
            if len(rows) < 100:
                break
        if len(result) > 1000:
            raise GateError(f"PR_TOO_MANY_CHANGED_FILES:{number}:{len(result)}")
        return sorted(set(result))

    def search_prs(self, query: str) -> list[dict[str, Any]]:
        rows = self.get("/search/issues", {"q": query, "per_page": "30"})
        if not isinstance(rows, dict) or not isinstance(rows.get("items"), list):
            raise GateError("INVALID_SEARCH_RESPONSE")
        return [row for row in rows["items"] if isinstance(row, dict)]

    def canonical_ledger_capabilities(self) -> set[str]:
        encoded = urllib.parse.quote(PROTECTED_METADATA_CAPABILITY_PATH, safe="/")
        row = self.get(f"/repos/{self.repo}/contents/{encoded}", {"ref": "main"})
        if not isinstance(row, dict) or not isinstance(row.get("content"), str):
            raise GateError("FACTORY_LEDGER_CONTENT_MISSING")
        try:
            payload = json.loads(base64.b64decode(row["content"]).decode("utf-8"))
        except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
            raise GateError(f"FACTORY_LEDGER_INVALID:{type(exc).__name__}") from exc
        rows = payload.get("capabilities") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise GateError("FACTORY_LEDGER_CAPABILITIES_MISSING")
        return {str(row["id"]) for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)}


def split_values(value: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in re.split(r"[;,]", value.strip()) if x.strip())


def normalize_scope(value: str) -> str:
    value = value.replace("\\", "/").strip()
    if not value or value.startswith("/") or value.startswith("../") or "/../" in value:
        raise GateError(f"WORKSTREAM_SCOPE_UNSAFE:{value}")
    return value


def parse_declaration(body: str) -> Declaration | None:
    matches = list(DECLARATION_RE.finditer(body or ""))
    if not matches:
        return None
    if len(matches) != 1:
        raise GateError("WORKSTREAM_DECLARATION_COUNT_INVALID")
    match = matches[0]
    values: dict[str, str] = {}
    for raw_line in match.group("body").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parsed = KEY_RE.match(line)
        if not parsed:
            raise GateError(f"WORKSTREAM_DECLARATION_INVALID_LINE:{line[:120]}")
        key, value = parsed.group("key"), parsed.group("value").strip()
        if key in values:
            raise GateError(f"WORKSTREAM_DECLARATION_DUPLICATE_KEY:{key}")
        values[key] = value

    required = {"id", "role", "requested_action", "capabilities", "surfaces", "scope"}
    missing = sorted(required - set(values))
    if missing:
        raise GateError("WORKSTREAM_DECLARATION_MISSING:" + ",".join(missing))
    unknown = sorted(set(values) - (required | {"owner"}))
    if unknown:
        raise GateError("WORKSTREAM_DECLARATION_UNKNOWN_KEY:" + ",".join(unknown))

    workstream_id = values["id"].lower()
    role = values["role"].lower()
    action = values["requested_action"].upper()
    caps = split_values(values["capabilities"])
    surfaces = split_values(values["surfaces"])
    scope = tuple(sorted(set(normalize_scope(x) for x in split_values(values["scope"]))))
    if not ID_RE.fullmatch(workstream_id):
        raise GateError(f"WORKSTREAM_ID_INVALID:{workstream_id}")
    if role not in ROLE_VALUES:
        raise GateError(f"WORKSTREAM_ROLE_INVALID:{role}")
    if action not in ACTION_VALUES:
        raise GateError(f"WORKSTREAM_ACTION_INVALID:{action}")
    if not caps or any(not CAP_RE.fullmatch(x) for x in caps):
        raise GateError("WORKSTREAM_CAPABILITIES_INVALID")
    if not surfaces:
        raise GateError("WORKSTREAM_SURFACES_REQUIRED")
    if not scope:
        raise GateError("WORKSTREAM_SCOPE_REQUIRED")
    return Declaration(workstream_id, role, action, tuple(sorted(set(caps))), tuple(sorted(set(surfaces))), scope, values.get("owner") or None)


def is_governed_path(path: str) -> bool:
    path = path.replace("\\", "/")
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in GOVERNED_PREFIXES)


def is_exclusive_path(path: str) -> bool:
    path = path.replace("\\", "/")
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in EXCLUSIVE_PREFIXES)


def scope_matches(scope: str, path: str) -> bool:
    scope = normalize_scope(scope)
    path = path.replace("\\", "/")
    return fnmatch.fnmatchcase(path, scope) or fnmatch.fnmatchcase(path, scope.rstrip("/") + "/**")


def scope_matches_any(scopes: Iterable[str], path: str) -> bool:
    return any(scope_matches(scope, path) for scope in scopes)


def exclusive_overlap_paths(current: PullRequestView, other: PullRequestView) -> list[str]:
    return sorted(
        set(current.changed_files) & set(other.changed_files)
        & {p for p in set(current.changed_files) | set(other.changed_files) if is_exclusive_path(p)}
    )


def exclusive_scope_overlap(current: PullRequestView, other: PullRequestView) -> list[str]:
    current_paths = {p for p in current.changed_files if is_exclusive_path(p)}
    other_paths = {p for p in other.changed_files if is_exclusive_path(p)}
    prefixes = []
    for prefix in EXCLUSIVE_PREFIXES:
        prefix = prefix.rstrip("/")
        if any(p == prefix or p.startswith(prefix + "/") for p in current_paths) and any(p == prefix or p.startswith(prefix + "/") for p in other_paths):
            prefixes.append(prefix)
    return sorted(set(prefixes))


def declaration_conflict(current: PullRequestView, other: PullRequestView) -> tuple[bool, list[str], list[str]]:
    if not current.declaration or not other.declaration:
        return False, [], []
    a, b = current.declaration, other.declaration
    reasons: list[str] = []
    same_ws = a.workstream_id == b.workstream_id
    same_cap = bool(set(a.capabilities) & set(b.capabilities))
    exclusive_overlap = exclusive_overlap_paths(current, other)
    exclusive_scope = exclusive_scope_overlap(current, other)
    scoped_overlap = sorted(
        set(pa for pa in current.changed_files if scope_matches_any(a.scope, pa))
        & set(pb for pb in other.changed_files if scope_matches_any(b.scope, pb))
    )
    if same_ws:
        reasons.append("same_workstream_id")
    if same_cap and (scoped_overlap or exclusive_overlap or exclusive_scope):
        reasons.append("same_capability_overlapping_scope")
    if exclusive_overlap:
        reasons.append("same_exclusive_path")
    if exclusive_scope:
        reasons.append("same_exclusive_scope")
    return bool(reasons), reasons, (exclusive_overlap or scoped_overlap or exclusive_scope)


def pr_view(client: GitHubClient, row: dict[str, Any]) -> PullRequestView:
    number = int(row["number"])
    body = str(row.get("body") or "")
    declaration = parse_declaration(body)
    head = row.get("head") if isinstance(row.get("head"), dict) else {}
    base = row.get("base") if isinstance(row.get("base"), dict) else {}
    return PullRequestView(
        number=number,
        title=str(row.get("title") or ""),
        body=body,
        state=str(row.get("state") or ""),
        draft=bool(row.get("draft")),
        head_sha=str(head.get("sha") or ""),
        base_sha=str(base.get("sha") or ""),
        created_at=str(row.get("created_at") or ""),
        updated_at=str(row.get("updated_at") or ""),
        declaration=declaration,
        changed_files=client.pull_request_files(number),
    )


def merged_history_conflicts(client: GitHubClient, current: PullRequestView) -> list[dict[str, Any]]:
    if not current.declaration:
        return []
    ws = current.declaration.workstream_id
    query = f'repo:{client.repo} is:pr is:closed "PRISMA-WORKSTREAM" "{ws}" in:body'
    conflicts = []
    for hit in client.search_prs(query):
        number = int(hit.get("number") or 0)
        if number == current.number:
            continue
        full = client.pull_request(number)
        if not full.get("merged_at"):
            continue
        try:
            prior = parse_declaration(str(full.get("body") or ""))
        except GateError:
            prior = None
        if prior and prior.workstream_id == ws:
            conflicts.append({
                "number": number,
                "title": full.get("title"),
                "mergedAt": full.get("merged_at"),
                "url": full.get("html_url"),
            })
    return conflicts

def declaration_scope_gaps(declaration: Declaration, changed_files: Iterable[str]) -> list[str]:
    return sorted(path for path in changed_files if is_governed_path(path) and not scope_matches_any(declaration.scope, path))

def evaluate(client: GitHubClient, pr_number: int, expected_head: str = "") -> dict[str, Any]:
    current = pr_view(client, client.pull_request(pr_number))
    if current.state != "open":
        raise GateError(f"PR_NOT_OPEN:{current.number}:{current.state}")
    if expected_head and current.head_sha != expected_head:
        raise GateError(f"HEAD_MISMATCH:{current.head_sha}:{expected_head}")

    if not current.governed:
        out = {
            "schemaVersion": SCHEMA,
            "result": "PASS_NOT_GOVERNED_SCOPE",
            "pr": current.number,
            "headSha": current.head_sha,
            "changedFiles": len(current.changed_files),
            "workstream": None,
            "conflicts": [],
            "mergedHistoryConflicts": [],
            "declarationRequired": False,
        }
        out["decisionDigest"] = digest(out)
        return out

    try:
        declaration = parse_declaration(current.body)
    except GateError as exc:
        declaration = None
        declaration_error = str(exc)
    else:
        declaration_error = None

    if not declaration:
        out = {
            "schemaVersion": SCHEMA,
            "result": "BLOCKED_WORKSTREAM_DECLARATION_REQUIRED",
            "pr": current.number,
            "headSha": current.head_sha,
            "changedFiles": len(current.changed_files),
            "workstream": None,
            "conflicts": [],
            "mergedHistoryConflicts": [],
            "declarationRequired": True,
            "errors": [declaration_error or "WORKSTREAM_DECLARATION_MISSING"],
        }
        out["decisionDigest"] = digest(out)
        return out

    current.declaration = declaration
    scope_gaps = declaration_scope_gaps(declaration, current.changed_files)
    if scope_gaps:
        out = {
            "schemaVersion": SCHEMA,
            "result": "BLOCKED_WORKSTREAM_SCOPE_MISMATCH",
            "pr": current.number,
            "headSha": current.head_sha,
            "changedFiles": len(current.changed_files),
            "workstream": declaration.workstream_id,
            "capabilities": list(declaration.capabilities),
            "scopeGaps": scope_gaps,
            "declarationRequired": True,
        }
        out["decisionDigest"] = digest(out)
        return out

    unknown_caps = sorted(set(declaration.capabilities) - client.canonical_ledger_capabilities())
    if unknown_caps:
        out = {
            "schemaVersion": SCHEMA,
            "result": "BLOCKED_UNKNOWN_CANONICAL_CAPABILITY",
            "pr": current.number,
            "headSha": current.head_sha,
            "changedFiles": len(current.changed_files),
            "workstream": declaration.workstream_id,
            "capabilities": list(declaration.capabilities),
            "unknownCapabilities": unknown_caps,
            "declarationRequired": True,
        }
        out["decisionDigest"] = digest(out)
        return out

    others: list[PullRequestView] = []
    load_errors: list[str] = []
    for row in client.open_pull_requests():
        try:
            if int(row.get("number") or 0) == current.number:
                continue
            other = pr_view(client, row)
            if other.governed:
                others.append(other)
        except Exception as exc:
            load_errors.append(f"PR_LOAD_FAILED:{row.get('number')}:{exc}")

    if load_errors:
        out = {
            "schemaVersion": SCHEMA,
            "result": "BLOCKED_WORKSTREAM_PEER_SCAN_INCOMPLETE",
            "pr": current.number,
            "headSha": current.head_sha,
            "changedFiles": len(current.changed_files),
            "workstream": declaration.workstream_id,
            "loadErrors": load_errors,
            "declarationRequired": True,
        }
        out["decisionDigest"] = digest(out)
        return out

    conflicts: list[dict[str, Any]] = []
    for other in others:
        if other.declaration is None:
            conflicts.append({
                "pr": other.number,
                "title": other.title,
                "role": None,
                "workstreamId": None,
                "reasons": ["UNDECLARED_GOVERNED_PEER"],
                "overlapPaths": [],
                "overlapCount": 0,
                "disposition": "current_must_stop",
            })
            continue
        hard, reasons, overlap = declaration_conflict(current, other)
        if not hard:
            continue
        disposition = (
            "peer_must_stop"
            if current.declaration.role == "canonical" and other.declaration.role != "canonical"
            else "current_must_stop"
        )
        conflicts.append({
            "pr": other.number,
            "title": other.title,
            "role": other.declaration.role,
            "workstreamId": other.declaration.workstream_id,
            "reasons": reasons,
            "overlapPaths": overlap or sorted(set(current.changed_files) & set(other.changed_files))[:100],
            "overlapCount": len(overlap or (set(current.changed_files) & set(other.changed_files))),
            "disposition": disposition,
        })

    history = merged_history_conflicts(client, current)
    canonical_competitors = [x for x in conflicts if x.get("role") == "canonical" and x.get("disposition") == "current_must_stop"]
    current_stop = any(x.get("disposition") == "current_must_stop" for x in conflicts)

    if canonical_competitors:
        result = "BLOCKED_CONCURRENT_WORKSTREAM"
        errors = ["MULTIPLE_CANONICAL_WORKSTREAM_OWNERS"]
    elif history:
        result = "BLOCKED_REUSED_MERGED_WORKSTREAM_ID"
        errors = ["WORKSTREAM_ID_ALREADY_MERGED_NEW_ID_REQUIRED"]
    elif current_stop:
        result = "BLOCKED_CONCURRENT_WORKSTREAM"
        errors = ["ACTIVE_WORKSTREAM_CONFLICT"]
    elif current.declaration.role == "canonical":
        result = "PASS_CANONICAL_WORKSTREAM_OWNER"
        errors = []
    else:
        result = "PASS_WORKSTREAM_UNCONFLICTED"
        errors = []

    out = {
        "schemaVersion": SCHEMA,
        "result": result,
        "pr": current.number,
        "title": current.title,
        "headSha": current.head_sha,
        "baseSha": current.base_sha,
        "changedFiles": len(current.changed_files),
        "governed": True,
        "workstream": {
            "id": declaration.workstream_id,
            "role": declaration.role,
            "requestedAction": declaration.requested_action,
            "capabilities": list(declaration.capabilities),
            "surfaces": list(declaration.surfaces),
            "scope": list(declaration.scope),
            "owner": declaration.owner,
        },
        "conflicts": conflicts,
        "mergedHistoryConflicts": history,
        "loadErrors": load_errors,
        "errors": errors,
        "declarationRequired": True,
        "coordinationOnly": True,
        "factoryLedgerRemainsCapabilityAuthority": True,
        "semanticSimilarityIsNotAuthority": True,
        "readOnly": True,
    }
    out["decisionDigest"] = digest(out)
    return out


def digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def self_test() -> None:
    d = parse_declaration(
        """<!-- PRISMA-WORKSTREAM
id: visual-canonical-registration-g01
role: canonical
requested_action: ADVANCE
capabilities: visual.canonical_promotion_integration_v1
surfaces: prisma-html, governance
scope: prisma-html/tools/visual_promotion/canonical_registration/**
owner: engineer
-->"""
    )
    assert d and d.role == "canonical"
    assert is_exclusive_path("prisma-html/tools/visual_promotion/canonical_registration/engine.py")
    assert is_governed_path("tools/code-atlas/tests/test_x.py")
    assert not is_governed_path("README.md")
    assert scope_matches("foo/**", "foo/bar/baz.py")

    try:
        parse_declaration(
            """<!-- PRISMA-WORKSTREAM
id: alpha
role: proposal
requested_action: VERIFY
capabilities: visual.foo
surfaces: governance
scope: ../../unsafe
-->"""
        )
    except GateError:
        pass
    else:
        raise AssertionError("unsafe scope accepted")

    a = Declaration("alpha", "canonical", "ADVANCE", ("visual.foo",), ("governance",), ("foo/**",))
    b = Declaration("alpha", "proposal", "ADVANCE", ("visual.foo",), ("governance",), ("foo/**",))
    pa = PullRequestView(1, "A", "", "open", False, "a"*40, "b"*40, "", "", a, ["foo/bar.py"])
    pb = PullRequestView(2, "B", "", "open", False, "c"*40, "b"*40, "", "", b, ["foo/bar.py"])
    hard, reasons, paths = declaration_conflict(pa, pb)
    assert hard and "same_workstream_id" in reasons and paths == ["foo/bar.py"]

    print("PASS_PRISMA_WORKSTREAM_COLLISION_GATE_SELF_TEST")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--pr-number", type=int, default=int(os.environ.get("PRISMA_PR_NUMBER", "0") or 0))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    parser.add_argument("--expected-head", default=os.environ.get("PRISMA_EXPECTED_HEAD", ""))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.repo or not args.pr_number or not args.token:
        raise SystemExit("repo, pr-number and token are required")
    result = evaluate(GitHubClient(args.repo, args.token), args.pr_number, args.expected_head)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["result"].startswith("PASS_") else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GateError as exc:
        print(f"BLOCKED_WORKSTREAM_GATE_ERROR:{exc}", file=sys.stderr)
        raise SystemExit(3)
