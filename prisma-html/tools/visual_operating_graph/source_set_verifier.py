from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable

LOCK_REL = Path("prisma-html/governance/visual-operating-graph/MASTER_MAP_SOURCESET.lock.json")
SCHEMA = "prisma.visual-operating-graph.sourceset-verification.v1"
REQUIRED_PINNED_INPUTS = (
    "prisma-html/governance/visual-operating-graph/FOUNDATION_MANIFEST.json",
    "prisma-html/governance/visual-operating-graph/PRISMA_VISUAL_OPERATING_GRAPH_PROCESS_MODEL.registry.json",
    "prisma-html/governance/visual-operating-graph/PRISMA_VISUAL_OPERATING_GRAPH_SCHEMA.json",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def git_blob_sha_bytes(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def git_blob_sha(path: Path) -> str:
    return git_blob_sha_bytes(path.read_bytes())


def find_repo_root(start: Path | None = None) -> Path:
    seed = (start or Path.cwd()).resolve()
    candidates = [seed, *seed.parents, *Path(__file__).resolve().parents]
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "prisma-html").is_dir() and (candidate / "PRISMA Factory Ledger").is_dir():
            return candidate
    raise RuntimeError("PRISMA_REPO_ROOT_NOT_FOUND")


def current_git_head(repo_root: Path) -> str | None:
    process = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    if process.returncode:
        return None
    value = process.stdout.strip()
    return value or None


def _contained(repo_root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"UNSAFE_SOURCE_PATH:{relative}")
    resolved = (repo_root / rel).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"SOURCE_PATH_ESCAPES_REPO:{relative}") from exc
    return resolved


def _schema_version(path: Path) -> tuple[str | None, str | None]:
    if path.suffix.lower() != ".json":
        return None, None
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None, None
    if not isinstance(value, dict):
        return None, None
    schema = value.get("schema") or value.get("schemaVersion") or value.get("$id")
    version = value.get("version")
    return (str(schema) if schema is not None else None, str(version) if version is not None else None)


def _generated_output_finding(path: Path, source_set_digest: str) -> dict[str, Any] | None:
    if not path.is_file():
        return {
            "class": "STALE_DERIVED_ARTIFACT",
            "code": "GENERATED_OUTPUT_MISSING",
            "path": path.as_posix(),
            "blocking": True,
        }
    try:
        if path.suffix.lower() == ".json":
            value = json.loads(path.read_text(encoding="utf-8-sig"))
            observed = value.get("sourceSetDigest") if isinstance(value, dict) else None
        else:
            observed = None
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:40]:
                if line.startswith("sourceSetDigest:"):
                    observed = line.split(":", 1)[1].strip().strip("`")
                    break
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "class": "STALE_DERIVED_ARTIFACT",
            "code": "GENERATED_OUTPUT_UNREADABLE",
            "path": path.as_posix(),
            "detail": str(exc),
            "blocking": True,
        }
    if observed != source_set_digest:
        return {
            "class": "STALE_DERIVED_ARTIFACT",
            "code": "GENERATED_OUTPUT_SOURCESET_DIGEST_MISMATCH",
            "path": path.as_posix(),
            "expected": source_set_digest,
            "actual": observed,
            "blocking": True,
        }
    return None


def verify_source_set(
    repo_root: str | Path,
    *,
    lock_path: str | Path | None = None,
    current_head_override: str | None = None,
    generated_outputs: Iterable[str | Path] = (),
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    lock_file = Path(lock_path) if lock_path is not None else repo / LOCK_REL
    if not lock_file.is_absolute():
        lock_file = repo / lock_file
    lock = json.loads(lock_file.read_text(encoding="utf-8-sig"))
    if not isinstance(lock, dict):
        raise ValueError("SOURCESET_LOCK_OBJECT_REQUIRED")

    findings: list[dict[str, Any]] = []
    sources = lock.get("sources")
    if not isinstance(sources, list):
        sources = []
        findings.append({"class": "CANONICAL_AUTHORITY_DRIFT", "code": "SOURCESET_SOURCES_LIST_REQUIRED", "blocking": True})
    declared_count = lock.get("sourceCount")
    if declared_count != len(sources):
        findings.append({
            "class": "CANONICAL_AUTHORITY_DRIFT",
            "code": "SOURCESET_COUNT_MISMATCH",
            "expected": declared_count,
            "actual": len(sources),
            "blocking": True,
        })

    verified = 0
    seen: set[str] = set()
    for row in sources:
        if not isinstance(row, dict):
            findings.append({"class": "CANONICAL_AUTHORITY_DRIFT", "code": "SOURCESET_ROW_OBJECT_REQUIRED", "blocking": True})
            continue
        relative = str(row.get("path") or "").strip()
        if not relative:
            findings.append({"class": "CANONICAL_AUTHORITY_DRIFT", "code": "SOURCESET_PATH_REQUIRED", "blocking": True})
            continue
        if relative in seen:
            findings.append({"class": "CANONICAL_AUTHORITY_DRIFT", "code": "SOURCESET_DUPLICATE_PATH", "path": relative, "blocking": True})
            continue
        seen.add(relative)
        try:
            path = _contained(repo, relative)
        except ValueError as exc:
            findings.append({"class": "CANONICAL_AUTHORITY_DRIFT", "code": str(exc), "path": relative, "blocking": True})
            continue
        if not path.is_file():
            findings.append({"class": "CANONICAL_AUTHORITY_DRIFT", "code": "SOURCE_MISSING", "path": relative, "blocking": True})
            continue
        expected_blob = str(row.get("gitBlobSha") or "").lower()
        actual_blob = git_blob_sha(path)
        if not expected_blob:
            findings.append({"class": "CANONICAL_AUTHORITY_DRIFT", "code": "SOURCE_GIT_BLOB_SHA_REQUIRED", "path": relative, "blocking": True})
            continue
        if actual_blob != expected_blob:
            findings.append({
                "class": "CANONICAL_AUTHORITY_DRIFT",
                "code": "SOURCE_GIT_BLOB_DRIFT",
                "path": relative,
                "expected": expected_blob,
                "actual": actual_blob,
                "blocking": True,
            })
            continue
        expected_schema = row.get("schema")
        expected_version = row.get("version")
        actual_schema, actual_version = _schema_version(path)
        if expected_schema is not None and str(expected_schema) != actual_schema:
            findings.append({
                "class": "CANONICAL_AUTHORITY_DRIFT",
                "code": "SOURCE_SCHEMA_DRIFT",
                "path": relative,
                "expected": str(expected_schema),
                "actual": actual_schema,
                "blocking": True,
            })
            continue
        if expected_version is not None and str(expected_version) != actual_version:
            findings.append({
                "class": "CANONICAL_AUTHORITY_DRIFT",
                "code": "SOURCE_VERSION_DRIFT",
                "path": relative,
                "expected": str(expected_version),
                "actual": actual_version,
                "blocking": True,
            })
            continue
        verified += 1

    for required in REQUIRED_PINNED_INPUTS:
        if required not in seen:
            findings.append({
                "class": "CANONICAL_AUTHORITY_DRIFT",
                "code": "REQUIRED_CANONICAL_INPUT_UNPINNED",
                "path": required,
                "blocking": True,
            })

    source_set_digest = sha256_json(lock)
    for output in generated_outputs:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = repo / output_path
        finding = _generated_output_finding(output_path, source_set_digest)
        if finding:
            try:
                finding["path"] = output_path.relative_to(repo).as_posix()
            except ValueError:
                pass
            findings.append(finding)

    blocking = [row for row in findings if row.get("blocking")]
    repo_head = current_head_override or current_git_head(repo)
    locked_head = str(lock.get("observedMainSha") or "") or None
    if blocking:
        head_disposition = "RELEVANT_DRIFT"
    elif repo_head and locked_head and repo_head == locked_head:
        head_disposition = "EXACT_HEAD"
    elif repo_head and locked_head:
        head_disposition = "NON_RELEVANT_DRIFT"
    else:
        head_disposition = "HEAD_NOT_OBSERVED"

    findings.sort(key=lambda row: (str(row.get("class")), str(row.get("code")), str(row.get("path"))))
    result = {
        "schemaVersion": SCHEMA,
        "status": "BLOCKED_SOURCESET_DRIFT" if blocking else "PASS_SOURCESET_VERIFIED",
        "repoHead": repo_head,
        "lockedObservedMain": locked_head,
        "headDisposition": head_disposition,
        "sourceSetDigest": source_set_digest,
        "sourceCountDeclared": declared_count,
        "sourceCountVerified": verified,
        "findingCount": len(findings),
        "blockingFindingCount": len(blocking),
        "findings": findings,
        "productionCertified": False,
        "authorizationGranted": False,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the PRISMA Visual Operating Graph source-set lock read-only.")
    parser.add_argument("--repo-root")
    parser.add_argument("--lock")
    parser.add_argument("--generated-output", action="append", default=[])
    parser.add_argument("--json-out")
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve() if args.repo_root else find_repo_root()
    result = verify_source_set(repo, lock_path=args.lock, generated_outputs=args.generated_output)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["status"] == "PASS_SOURCESET_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
