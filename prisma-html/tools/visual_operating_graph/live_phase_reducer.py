from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "prisma.visual-operating-graph.live-phase-truth.v1"


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def reduce_live_phase_truth(
    canonical_graph: dict[str, Any],
    source_verification: dict[str, Any],
    *,
    live_overlay: list[dict[str, Any]] | None = None,
    now: str | datetime | None = None,
    freshness_seconds: int = 3600,
) -> dict[str, Any]:
    canonical_head = (
        canonical_graph.get("observedCanonicalMain")
        or source_verification.get("lockedObservedMain")
        or source_verification.get("repoHead")
    )
    phase_nodes = [
        row
        for row in canonical_graph.get("nodes") or []
        if isinstance(row, dict) and row.get("type") == "PHASE"
    ]
    canonical_phase = (
        phase_nodes[0].get("payload", {}).get("phase")
        if phase_nodes
        else None
    )
    findings: list[dict[str, Any]] = []

    if source_verification.get("status") != "PASS_SOURCESET_VERIFIED":
        findings.append(
            {
                "class": "CANONICAL_AUTHORITY_DRIFT",
                "code": "SOURCESET_NOT_VERIFIED",
                "blockingCanonical": True,
                "sourceRef": "prisma-html/governance/visual-operating-graph/MASTER_MAP_SOURCESET.lock.json",
            }
        )
    elif source_verification.get("headDisposition") == "NON_RELEVANT_DRIFT":
        findings.append(
            {
                "class": "NON_RELEVANT_DRIFT",
                "code": "CHECKOUT_HEAD_MOVED_LOCKED_SOURCES_UNCHANGED",
                "blockingCanonical": False,
                "sourceRef": "prisma-html/governance/visual-operating-graph/MASTER_MAP_SOURCESET.lock.json",
            }
        )

    rows = sorted(
        (live_overlay or []),
        key=lambda row: str(row.get("id") or "") if isinstance(row, dict) else "",
    )
    if isinstance(now, datetime):
        now_dt = (
            now.astimezone(timezone.utc)
            if now.tzinfo
            else now.replace(tzinfo=timezone.utc)
        )
    else:
        now_dt = _parse_time(now)

    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(rows, 1):
        if not isinstance(raw, dict):
            findings.append(
                {
                    "class": "LIVE_OVERLAY_DRIFT",
                    "code": "LIVE_ROW_OBJECT_REQUIRED",
                    "blockingCanonical": False,
                    "sourceRef": f"live:{index}",
                }
            )
            continue

        row = dict(raw)
        source_ref = str(row.get("sourceRef") or f"live:{row.get('id') or index}")
        row_id = str(row.get("id") or f"live-{index}")
        row["id"] = row_id
        row["canonicality"] = "LIVE_OVERLAY"
        normalized.append(row)

        base_head = row.get("baseHead")
        worker_head = row.get("workerHead")
        status_head = row.get("statusBranchHead")
        receipt_head = row.get("receiptHead")

        if base_head and canonical_head and base_head != canonical_head:
            findings.append(
                {
                    "class": "LIVE_OVERLAY_DRIFT",
                    "code": "STALE_WORKER_BASE",
                    "id": row_id,
                    "expected": canonical_head,
                    "actual": base_head,
                    "blockingCanonical": False,
                    "sourceRef": source_ref,
                }
            )
        if receipt_head and worker_head and receipt_head != worker_head:
            findings.append(
                {
                    "class": "LIVE_OVERLAY_DRIFT",
                    "code": "RECEIPT_WORKER_HEAD_DISAGREEMENT",
                    "id": row_id,
                    "expected": worker_head,
                    "actual": receipt_head,
                    "blockingCanonical": False,
                    "sourceRef": source_ref,
                }
            )
        if status_head and worker_head and status_head != worker_head:
            findings.append(
                {
                    "class": "LIVE_OVERLAY_DRIFT",
                    "code": "STATUS_WORKER_HEAD_DISAGREEMENT",
                    "id": row_id,
                    "expected": worker_head,
                    "actual": status_head,
                    "blockingCanonical": False,
                    "sourceRef": source_ref,
                }
            )

        writer_role = row.get("writerRole")
        if writer_role and writer_role != "STATUS_WRITER":
            findings.append(
                {
                    "class": "WRITER_DRIFT",
                    "code": "LIVE_STATUS_WRITER_ROLE_INVALID",
                    "id": row_id,
                    "expected": "STATUS_WRITER",
                    "actual": writer_role,
                    "blockingCanonical": False,
                    "sourceRef": source_ref,
                }
            )

        if now_dt is not None:
            observed = _parse_time(row.get("timestamp") or row.get("observedAt"))
            if observed is None:
                findings.append(
                    {
                        "class": "TEMPORAL_STALENESS",
                        "code": "LIVE_TIMESTAMP_MISSING_OR_INVALID",
                        "id": row_id,
                        "blockingCanonical": False,
                        "sourceRef": source_ref,
                    }
                )
            else:
                age = (now_dt - observed).total_seconds()
                if age > freshness_seconds:
                    findings.append(
                        {
                            "class": "TEMPORAL_STALENESS",
                            "code": "LIVE_OBSERVATION_STALE",
                            "id": row_id,
                            "ageSeconds": int(age),
                            "freshnessSeconds": int(freshness_seconds),
                            "blockingCanonical": False,
                            "sourceRef": source_ref,
                        }
                    )

    findings.sort(
        key=lambda row: (
            str(row.get("class")),
            str(row.get("code")),
            str(row.get("id")),
            str(row.get("sourceRef")),
        )
    )
    canonical_blocked = any(row.get("blockingCanonical") for row in findings)
    live_drift = any(
        row.get("class")
        in {"LIVE_OVERLAY_DRIFT", "TEMPORAL_STALENESS", "WRITER_DRIFT"}
        for row in findings
    )

    if canonical_blocked:
        status = "BLOCKED_CANONICAL_DRIFT"
    elif not rows:
        status = "CANONICAL_STATE_VERIFIED_LIVE_OVERLAY_NOT_OBSERVED"
    elif live_drift:
        status = "CANONICAL_STATE_VERIFIED_LIVE_DRIFT_PRESENT"
    else:
        status = "CANONICAL_STATE_VERIFIED_LIVE_OVERLAY_OBSERVED"

    return {
        "schemaVersion": SCHEMA,
        "status": status,
        "observedCanonicalMain": canonical_head,
        "canonicalPhase": canonical_phase,
        "canonicalState": {
            "sourceSetStatus": source_verification.get("status"),
            "headDisposition": source_verification.get("headDisposition"),
            "sourceSetDigest": source_verification.get("sourceSetDigest"),
        },
        "liveOverlayObserved": bool(rows),
        "liveOverlay": normalized,
        "findingCount": len(findings),
        "findings": findings,
        "authorizationGranted": False,
        "productionCertified": False,
        "mutationAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reduce PRISMA canonical process truth with a non-canonical live overlay."
    )
    parser.add_argument("--canonical-graph", required=True)
    parser.add_argument("--source-verification", required=True)
    parser.add_argument("--live-overlay")
    parser.add_argument("--now")
    parser.add_argument("--freshness-seconds", type=int, default=3600)
    parser.add_argument("--json-out")
    args = parser.parse_args()

    graph = json.loads(
        Path(args.canonical_graph).read_text(encoding="utf-8-sig")
    )
    verification = json.loads(
        Path(args.source_verification).read_text(encoding="utf-8-sig")
    )
    live: list[dict[str, Any]] | None = None
    if args.live_overlay:
        value = json.loads(
            Path(args.live_overlay).read_text(encoding="utf-8-sig")
        )
        if isinstance(value, dict):
            value = value.get("rows") or value.get("liveOverlay") or []
        if not isinstance(value, list):
            raise SystemExit("LIVE_OVERLAY_LIST_REQUIRED")
        live = value

    result = reduce_live_phase_truth(
        graph,
        verification,
        live_overlay=live,
        now=args.now,
        freshness_seconds=args.freshness_seconds,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 2 if result["status"] == "BLOCKED_CANONICAL_DRIFT" else 0


if __name__ == "__main__":
    raise SystemExit(main())
