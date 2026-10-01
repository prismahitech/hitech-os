from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import orchestrator


REPO_ROOT = Path(__file__).resolve().parents[4]


def _read_object(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return value


def _emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Coordinate one exact PRISMA visual lifecycle.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect", help="Read current lifecycle state and receipts.")
    inspect.add_argument("--lifecycle-id")

    doctor = commands.add_parser("doctor", help="Run read-only lifecycle and authority diagnostics.")
    doctor.add_argument("--lifecycle-id")
    doctor.add_argument("--request", help="JSON object containing workEntryRequest for an exact Work Entry check.")

    advance = commands.add_parser("advance", help="Execute exactly one next lifecycle transition.")
    advance.add_argument("--request", required=True, help="Transition request JSON file.")

    receipt = commands.add_parser("receipt", help="Read a persisted transition receipt.")
    receipt.add_argument("--lifecycle-id", required=True)
    receipt.add_argument("--transition-id", required=True)

    rollback = commands.add_parser("rollback-registration", help="Rollback one canonical registration transaction.")
    rollback.add_argument("--lifecycle-id", required=True)

    supersede = commands.add_parser("supersede", help="Mark a lifecycle superseded with an explicit decision reference.")
    supersede.add_argument("--lifecycle-id", required=True)
    supersede.add_argument("--superseded-by", required=True)
    supersede.add_argument("--decision-ref", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path(args.repo_root).resolve()
    try:
        if args.command == "inspect":
            result = orchestrator.inspect_lifecycle(root, args.lifecycle_id)
        elif args.command == "doctor":
            request = _read_object(args.request) if args.request else None
            result = orchestrator.diagnose(root, request=request, lifecycle_id=args.lifecycle_id)
        elif args.command == "advance":
            result = orchestrator.advance_transition(_read_object(args.request), root)
        elif args.command == "receipt":
            result = orchestrator.load_receipt(root, args.lifecycle_id, args.transition_id)
        elif args.command == "rollback-registration":
            result = orchestrator.rollback_registration(root, args.lifecycle_id)
        else:
            result = orchestrator.supersede_lifecycle(
                root,
                args.lifecycle_id,
                superseded_by=args.superseded_by,
                decision_ref=args.decision_ref,
            )
    except Exception as exc:
        _emit({"status": "FAIL", "error": str(exc), "errorType": type(exc).__name__})
        return 3
    _emit(result)
    status = result.get("status") if isinstance(result, dict) else None
    result_status = (result.get("result") or {}).get("status") if isinstance(result, dict) else None
    if status in {"BLOCKED", "FAIL"} or result_status in {"BLOCKED", "FAIL"}:
        return 2 if status == "BLOCKED" or result_status == "BLOCKED" else 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
