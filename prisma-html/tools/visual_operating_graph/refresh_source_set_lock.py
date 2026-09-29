from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

LOCK_REL = Path("prisma-html/governance/visual-operating-graph/MASTER_MAP_SOURCESET.lock.json")


def canonical_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def repo_root(start: Path | None = None) -> Path:
    seed = (start or Path.cwd()).resolve()
    for candidate in [seed, *seed.parents, *Path(__file__).resolve().parents]:
        if (candidate / "prisma-html").is_dir() and (candidate / "PRISMA Factory Ledger").is_dir():
            return candidate
    raise RuntimeError("PRISMA_REPO_ROOT_NOT_FOUND")


def current_head(root: Path) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=30,
    )
    if proc.returncode:
        return None
    value = proc.stdout.strip()
    return value or None


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def refresh(lock: dict[str, Any], root: Path) -> dict[str, Any]:
    sources = lock.get("sources")
    if not isinstance(sources, list):
        raise ValueError("SOURCESET_SOURCES_LIST_REQUIRED")

    refreshed: list[dict[str, Any]] = []
    for row in sources:
        if not isinstance(row, dict):
            raise ValueError("SOURCESET_ROW_OBJECT_REQUIRED")
        relative = str(row.get("path") or "").strip()
        if not relative:
            raise ValueError("SOURCESET_PATH_REQUIRED")
        target = (root / relative).resolve()
        target.relative_to(root.resolve())
        if not target.is_file():
            raise FileNotFoundError(relative)
        updated = dict(row)
        updated["gitBlobSha"] = git_blob_sha(target)
        refreshed.append(updated)

    result = dict(lock)
    result["sources"] = refreshed
    head = current_head(root)
    if head:
        result["observedMainSha"] = head
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh the generated PRISMA Visual Operating Graph source-set lock from tracked canonical inputs."
    )
    parser.add_argument("--repo-root")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root()
    lock_path = root / LOCK_REL
    current = json.loads(lock_path.read_text(encoding="utf-8-sig"))
    expected = refresh(current, root)

    if args.write:
        lock_path.write_text(canonical_text(expected), encoding="utf-8", newline="\n")
        print(json.dumps({"status": "PASS_SOURCESET_LOCK_REFRESHED", "lock": LOCK_REL.as_posix(), "sourceCount": len(expected["sources"])}, indent=2))
        return 0

    comparison = dict(expected)
    comparison["observedMainSha"] = current.get("observedMainSha")
    if current != comparison:
        print(json.dumps({"status": "DRIFT_SOURCESET_LOCK", "reason": "canonical source blob pins do not match tracked files"}, indent=2))
        return 2

    print(json.dumps({"status": "PASS_SOURCESET_LOCK_CURRENT", "sourceCount": len(expected["sources"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
