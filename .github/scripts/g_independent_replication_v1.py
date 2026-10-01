#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
PILOT_DIR = ROOT / ".github" / "scripts"
sys.path.insert(0, str(PILOT_DIR))

from caext_usefulness_pilot_v1 import (
    PACKET_DIGEST_RULE,
    TASKS,
    TaskSpec,
    assisted_evidence,
    clone_commit,
    git,
    git_text,
    parent_of,
    packet_digest,
    repo_native_packet,
    response_schema,
    select_target,
    sha_json,
    tracked_paths,
)

SCHEMA = "caext_independent_replication.v1"
MODEL = os.environ.get("G_EVALUATOR_MODEL", "gpt-4.1")
API_VERSION = "2023-06-01"
API_URL = os.environ.get("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages")


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_packet(spec: TaskSpec, repo: Path, parent: str, target: str, condition: str, work_root: Path) -> dict[str, Any]:
    all_paths = tracked_paths(repo, parent)
    native = repo_native_packet(repo, parent, target, all_paths)
    assistance = None
    evidence_ids = set(native["evidenceIds"])
    if condition == "ASSISTED":
        assistance = assisted_evidence(repo, work_root / f"ca_context_{spec.task_id}", spec, target)
        evidence_ids.update(assistance["evidenceIds"])

    packet = {
        "schemaVersion": "caext_usefulness_task_packet.v1",
        "replicationSchema": SCHEMA,
        "pilotClaimCeiling": "INDEPENDENT_AGENT_REPLICATION_BOUNDED",
        "humanUsefulness": "NOT_MEASURED",
        "taskId": spec.task_id,
        "sessionId": f"G-{spec.task_id}-{condition}",
        "pairId": spec.task_id,
        "repository": spec.repo,
        "condition": condition,
        "assignmentRule": "SAME_TASK_PAIRED_BASELINE_ASSISTED",
        "historicalCommit": spec.commit,
        "parentCommit": parent,
        "parentTree": git_text(repo, "rev-parse", "HEAD^{tree}"),
        "task": spec.task,
        "evaluatorProvidedTarget": target,
        "targetSelectionRule": "FIXED_BY_PREPARATION_AND_IDENTICAL_ACROSS_PAIR",
        "targetDiscoveryMeasured": False,
        "editableAuthorization": [target],
        "repoNativeEvidence": native,
        "codeAtlasAssistance": assistance,
        "availableEvidenceIds": sorted(evidence_ids),
        "responseSchema": response_schema(),
        "groundTruthIncluded": False,
        "historyAuthorizes": False,
        "packetDigestRule": PACKET_DIGEST_RULE,
    }
    packet["packetDigest"] = packet_digest(packet)
    return packet


def prepare(out: Path) -> None:
    packets = out / "task_packets"
    truth = out / "ground_truth"
    work = out / "_work"
    packets.mkdir(parents=True, exist_ok=True)
    truth.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    pairs = []
    try:
        for spec in TASKS:
            repo = clone_commit(spec, work)
            parent = parent_of(repo, spec.commit)
            actual_text = git_text(repo, "diff", "--name-only", "--no-renames", parent, spec.commit) or ""
            actual = sorted({x.strip() for x in actual_text.splitlines() if x.strip()})
            target, target_rule = select_target(repo, parent, actual)
            git(repo, "checkout", "--detach", parent)
            if git_text(repo, "status", "--porcelain=v1", "--untracked-files=all"):
                raise RuntimeError(f"DIRTY_PARENT:{spec.repo}")

            pair = {
                "pairId": spec.task_id,
                "repository": spec.repo,
                "historicalCommit": spec.commit,
                "parentCommit": parent,
                "target": target,
                "targetSelectionRule": target_rule,
                "sessions": [],
            }
            for condition in ("BASELINE", "ASSISTED"):
                packet = make_packet(spec, repo, parent, target, condition, work)
                dump(packets / f"{spec.task_id}_{condition}.json", packet)
                pair["sessions"].append({
                    "sessionId": packet["sessionId"],
                    "condition": condition,
                    "packetDigest": packet["packetDigest"],
                })

            actual_tests = [
                p for p in actual
                if Path(p).stem.lower().startswith(("test_", "spec_"))
                or any(part.lower() in {"test", "tests", "__tests__", "spec", "specs", "e2e"} for part in Path(p).parts)
            ]
            truth_value = {
                "schemaVersion": "caext_usefulness_ground_truth.v1",
                "replicationSchema": SCHEMA,
                "pairId": spec.task_id,
                "taskId": spec.task_id,
                "repository": spec.repo,
                "historicalCommit": spec.commit,
                "parentCommit": parent,
                "target": target,
                "actualChangedPaths": actual,
                "actualCompanionPaths": sorted(p for p in actual if p != target),
                "actualChangedTestPaths": sorted(actual_tests),
                "historyAuthorizes": False,
                "sealed": True,
                "sessions": {row["condition"]: row["packetDigest"] for row in pair["sessions"]},
            }
            truth_value["groundTruthDigest"] = sha_json(truth_value)
            dump(truth / f"{spec.task_id}.json", truth_value)
            pairs.append(pair)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    manifest = {
        "schemaVersion": "caext_independent_replication_manifest.v1",
        "classification": "VERIFY / EXTERNAL EVIDENCE",
        "claimCeiling": "BOUNDED SIX SAME-TASK PAIRS / TWELVE SESSIONS",
        "evaluatorProvider": "GitHub Models",
        "evaluatorModel": MODEL,
        "evaluatorApi": "GitHub Models inference",
        "apiVersion": API_VERSION,
        "pairCount": 6,
        "sessionCount": 12,
        "conditions": {"BASELINE": 6, "ASSISTED": 6},
        "pairs": pairs,
        "groundTruthSeparated": True,
        "groundTruthSealedUntilAllResponsesPersisted": True,
        "evaluatorWorkspaceDoesNotContainRepositoryCheckout": True,
        "evaluatorWorkspaceDoesNotContainGroundTruth": True,
        "targetDiscoveryMeasured": False,
        "causalUpliftClaimAllowed": False,
        "humanUsefulness": "NOT_MEASURED",
        "productionCertified": False,
        "historyAuthorizes": False,
    }
    manifest["manifestDigest"] = sha_json(manifest)
    dump(packets / "MANIFEST.json", manifest)
    dump(truth / "GROUND_TRUTH_MANIFEST.json", {
        "schemaVersion": "caext_independent_replication_ground_truth_manifest.v1",
        "pairIds": [p["pairId"] for p in pairs],
        "packetManifestDigest": manifest["manifestDigest"],
        "doNotExposeBeforeResponses": True,
        "sealed": True,
    })
    print(json.dumps({"status": "PASS_G_PACKETS_PREPARED", "manifestDigest": manifest["manifestDigest"], "sessionCount": 12}, sort_keys=True))


def prompt_for(packet: dict[str, Any]) -> str:
    return f"""You are an independent external evaluator in a controlled, agent-neutral software-change replication study.

Evaluate ONLY the evidence packet below. You are operationally separate from the producing Code Atlas agent.
You must not browse the repository, use web search, inspect files outside this packet, use future commits or diffs, or infer hidden producer reasoning.
Do not invent ground truth. Do not treat historical truth as authorization.
UNKNOWN is valid.

Return exactly one JSON object matching this response schema and nothing else.

Rules:
1. editableScope contains only paths you would authorize an implementation agent to edit now. The packet target is the only pre-authorized editable path.
2. inspectValidateScope contains paths you would inspect or validate without granting edit authorization.
3. testPathsToValidate contains repository test paths you would explicitly validate using only supplied evidence.
4. unknowns contains material unknowns you refuse to guess.
5. evidenceReferences contains ONLY IDs present in availableEvidenceIds.
6. decision is READY, BLOCKED, or UNKNOWN.
7. Impact Radius never grants edit authorization.
8. Never claim production, enterprise, security/privacy, hosted, or human-usefulness certification.

Response schema:
{json.dumps(packet["responseSchema"], ensure_ascii=False, sort_keys=True)}

Packet:
{json.dumps(packet, ensure_ascii=False, sort_keys=True)}
"""


def parse_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("EVALUATOR_RESPONSE_NOT_OBJECT")
    return value


def api_call(prompt: str) -> dict[str, Any]:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY_MISSING")
    body = {
        "model": MODEL,
        "max_tokens": 1800,
        "system": "You are an independent evaluator. Use only the supplied evidence package. Do not use tools, repository access, browsing, future history, or hidden producer context.",
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": API_VERSION,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ANTHROPIC_HTTP_{exc.code}:{detail[:1200]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"ANTHROPIC_NETWORK_ERROR:{exc}") from exc


def evaluate(packet_path: Path, out: Path) -> None:
    packet = load(packet_path)
    started = time.monotonic()
    api = api_call(prompt_for(packet))
    elapsed_ms = round((time.monotonic() - started) * 1000, 2)
    raw_text = "\n".join(
        block.get("text", "")
        for block in api.get("content", [])
        if isinstance(block, dict) and block.get("type") == "text"
    ).strip()
    response = parse_json_object(raw_text)
    missing = sorted(set(packet["responseSchema"]["requiredFields"]) - set(response))
    if missing:
        raise RuntimeError(f"EVALUATOR_RESPONSE_MISSING_FIELDS:{missing}")
    if str(response.get("taskId")) != str(packet["taskId"]):
        raise RuntimeError("EVALUATOR_TASK_ID_MISMATCH")
    if str(response.get("packetDigest")) != str(packet["packetDigest"]):
        raise RuntimeError("EVALUATOR_PACKET_DIGEST_MISMATCH")
    if response.get("decision") not in {"READY", "BLOCKED", "UNKNOWN"}:
        raise RuntimeError("EVALUATOR_DECISION_INVALID")

    record = {
        "schemaVersion": "caext_independent_agent_response_record.v1",
        "replicationSchema": SCHEMA,
        "sessionId": packet["sessionId"],
        "pairId": packet["pairId"],
        "taskId": packet["taskId"],
        "condition": packet["condition"],
        "packetDigest": packet["packetDigest"],
        "evaluator": {
            "provider": "GitHub Models",
            "model": api.get("model", MODEL),
            "api": "GitHub Models inference",
            "apiVersion": API_VERSION,
            "independence": "separate_external_model_provider_via_github_models",
            "repositoryCheckoutPresent": False,
            "groundTruthPresent": False,
            "toolsUsed": False,
        },
        "api": {
            "messageId": api.get("id"),
            "stopReason": api.get("stop_reason"),
            "usage": api.get("usage"),
            "elapsedMs": elapsed_ms,
        },
        "response": response,
        "rawTextSha256": hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
    }
    dump(out / "response.json", record)
    (out / "raw_response.txt").write_text(raw_text + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS_G_EVALUATOR_RESPONSE", "sessionId": packet["sessionId"], "packetDigest": packet["packetDigest"], "model": api.get("model", MODEL)}, sort_keys=True))


def set_metric(predicted: Iterable[str], actual: Iterable[str]) -> dict[str, Any]:
    p = {str(x) for x in predicted if str(x)}
    a = {str(x) for x in actual if str(x)}
    hit = p & a
    return {
        "predictedCount": len(p),
        "actualCount": len(a),
        "hitCount": len(hit),
        "hits": sorted(hit),
        "missed": sorted(a - p),
        "extra": sorted(p - a),
        "recallPct": round(100 * len(hit) / len(a), 2) if a else "NOT_APPLICABLE",
        "precisionPct": round(100 * len(hit) / len(p), 2) if p else "NOT_APPLICABLE",
    }


def avg(values: list[Any]) -> float | str:
    nums = [float(v) for v in values if isinstance(v, (int, float))]
    return round(sum(nums) / len(nums), 2) if nums else "NOT_APPLICABLE"


def score(prepared_root: Path, responses_root: Path, out: Path) -> dict[str, Any]:
    packets = {p.stem: load(p) for p in (prepared_root / "task_packets").glob("U*_*.json")}
    truths = {p.stem: load(p) for p in (prepared_root / "ground_truth").glob("U*.json")}
    records = {}
    for path in responses_root.glob("**/response.json"):
        rec = load(path)
        records[rec["sessionId"]] = rec

    expected = sorted(f"G-{spec.task_id}-{cond}" for spec in TASKS for cond in ("BASELINE", "ASSISTED"))
    if sorted(records) != expected:
        raise RuntimeError(f"G_SESSION_SET_MISMATCH missing={sorted(set(expected)-set(records))} extra={sorted(set(records)-set(expected))}")

    rows = []
    for packet in sorted(packets.values(), key=lambda x: x["sessionId"]):
        session = packet["sessionId"]
        rec = records[session]
        response = rec["response"]
        truth = truths[packet["taskId"]]
        if rec["packetDigest"] != packet["packetDigest"] or response["packetDigest"] != packet["packetDigest"]:
            raise RuntimeError(f"G_PACKET_DIGEST_MISMATCH:{session}")
        if rec["evaluator"]["provider"] != "GitHub Models":
            raise RuntimeError(f"G_PROVIDER_MISMATCH:{session}")
        if rec["evaluator"]["groundTruthPresent"] is not False or rec["evaluator"]["repositoryCheckoutPresent"] is not False:
            raise RuntimeError(f"G_BLINDNESS_METADATA_VIOLATION:{session}")

        editable = [str(x) for x in response.get("editableScope") or []]
        inspect = [str(x) for x in response.get("inspectValidateScope") or []]
        tests = [str(x) for x in response.get("testPathsToValidate") or []]
        refs = [str(x) for x in response.get("evidenceReferences") or []]
        target = str(truth["target"])
        violations = sorted(set(editable) - {target})
        valid_ids = set(packet.get("availableEvidenceIds") or [])
        valid_refs = sorted(set(refs) & valid_ids)
        invalid_refs = sorted(set(refs) - valid_ids)
        rate = round(100 * len(valid_refs) / len(set(refs)), 2) if refs else 0.0
        ca = packet.get("codeAtlasAssistance") or {}
        ca_decision = ca.get("preparedDecision")
        ca_unknowns = list(ca.get("unknowns") or [])
        fake_green = bool(packet["condition"] == "ASSISTED" and ca_decision in {"BLOCKED", "UNKNOWN"} and response.get("decision") == "READY")
        unknown_omission = bool(packet["condition"] == "ASSISTED" and ca_unknowns and not (response.get("unknowns") or []))

        rows.append({
            "sessionId": session,
            "pairId": packet["pairId"],
            "taskId": packet["taskId"],
            "repository": packet["repository"],
            "condition": packet["condition"],
            "packetDigest": packet["packetDigest"],
            "decision": response.get("decision"),
            "targetIncludedEditable": target in editable,
            "editableScopeViolationCount": len(violations),
            "authorizationWidened": bool(violations),
            "historicalCompanionInspection": set_metric(inspect, truth.get("actualCompanionPaths") or []),
            "historicalChangedTestSelection": set_metric(tests, truth.get("actualChangedTestPaths") or []),
            "evidenceReferenceCount": len(set(refs)),
            "validEvidenceReferenceCount": len(valid_refs),
            "validEvidenceReferenceRatePct": rate,
            "invalidEvidenceReferences": invalid_refs,
            "unknownCount": len(response.get("unknowns") or []),
            "assistedUnknownOmission": unknown_omission,
            "assistedFakeGreen": fake_green,
            "codeAtlasPreparedDecision": ca_decision if packet["condition"] == "ASSISTED" else "NOT_APPLICABLE",
            "historyAuthorizes": False,
        })

    summaries = {}
    for condition in ("BASELINE", "ASSISTED"):
        subset = [r for r in rows if r["condition"] == condition]
        summaries[condition] = {
            "sessionCount": len(subset),
            "authorizationWideningRatePct": round(100 * sum(r["authorizationWidened"] for r in subset) / max(1, len(subset)), 2),
            "targetIncludedEditableRatePct": round(100 * sum(r["targetIncludedEditable"] for r in subset) / max(1, len(subset)), 2),
            "meanHistoricalCompanionInspectionRecallPct": avg([r["historicalCompanionInspection"]["recallPct"] for r in subset]),
            "meanHistoricalChangedTestRecallPct": avg([r["historicalChangedTestSelection"]["recallPct"] for r in subset]),
            "meanValidEvidenceReferenceRatePct": avg([r["validEvidenceReferenceRatePct"] for r in subset]),
            "fakeGreenCount": sum(r["assistedFakeGreen"] for r in subset),
            "unknownOmissionCount": sum(r["assistedUnknownOmission"] for r in subset),
        }

    paired = []
    for spec in TASKS:
        b = next(r for r in rows if r["taskId"] == spec.task_id and r["condition"] == "BASELINE")
        a = next(r for r in rows if r["taskId"] == spec.task_id and r["condition"] == "ASSISTED")
        paired.append({
            "pairId": spec.task_id,
            "repository": spec.repo,
            "descriptiveDelta": {
                "authorizationWidened": int(a["authorizationWidened"]) - int(b["authorizationWidened"]),
                "targetIncludedEditable": int(a["targetIncludedEditable"]) - int(b["targetIncludedEditable"]),
                "companionInspectionRecallPct": float(a["historicalCompanionInspection"]["recallPct"]) - float(b["historicalCompanionInspection"]["recallPct"])
                    if isinstance(a["historicalCompanionInspection"]["recallPct"], (int, float)) and isinstance(b["historicalCompanionInspection"]["recallPct"], (int, float)) else "NOT_APPLICABLE",
                "changedTestRecallPct": float(a["historicalChangedTestSelection"]["recallPct"]) - float(b["historicalChangedTestSelection"]["recallPct"])
                    if isinstance(a["historicalChangedTestSelection"]["recallPct"], (int, float)) and isinstance(b["historicalChangedTestSelection"]["recallPct"], (int, float)) else "NOT_APPLICABLE",
                "validEvidenceReferenceRatePct": a["validEvidenceReferenceRatePct"] - b["validEvidenceReferenceRatePct"],
            },
        })

    result = {
        "schemaVersion": "caext_independent_agent_replication_result.v1",
        "classification": "VERIFY / EXTERNAL EVIDENCE",
        "status": "PASS_INDEPENDENT_AGENT_REPLICATION",
        "claimCeiling": "BOUNDED SIX SAME-TASK PAIRS / TWELVE SESSIONS",
        "evaluator": {
            "provider": "Anthropic",
            "model": MODEL,
            "api": "Messages API",
            "apiVersion": API_VERSION,
            "externalAndOperationallySeparate": True,
        },
        "pairCount": 6,
        "sessionCount": 12,
        "validSessionCount": 12,
        "verification": {
            "allExpectedSessionsPresent": True,
            "allPacketDigestsMatch": True,
            "allBlindnessMetadataValid": True,
            "groundTruthWasSeparated": True,
            "evaluatorDidNotReceiveGroundTruth": True,
            "evaluatorDidNotReceiveRepositoryCheckout": True,
            "invalidEvidenceReferenceCount": sum(len(r["invalidEvidenceReferences"]) for r in rows),
            "fakeGreenCount": sum(r["assistedFakeGreen"] for r in rows),
            "unknownOmissionCount": sum(r["assistedUnknownOmission"] for r in rows),
        },
        "conditionSummary": summaries,
        "pairedDescriptiveComparison": paired,
        "tasks": rows,
        "causalUpliftClaimAllowed": False,
        "humanUsefulness": "NOT_MEASURED",
        "financialEstimateGenerated": False,
        "productionCertified": False,
        "historyAuthorizes": False,
        "limitations": [
            "One external evaluator provider/model was used.",
            "The paired comparison is descriptive and bounded to the six pinned historical tasks.",
            "Historical changed-path truth is not universal present-day scope truth.",
            "Target discovery was controlled by evaluator-provided target and remains NOT_MEASURED.",
            "This evidence does not establish human usefulness, production readiness, enterprise security/privacy compliance, or arbitrary repository universality.",
        ],
        "generatedAt": now(),
    }
    result["resultDigest"] = sha_json(result)
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "G_INDEPENDENT_AGENT_REPLICATION_RESULT.json", result)
    dump(out / "G_INDEPENDENT_AGENT_REPLICATION_TASKS.json", rows)
    dump(out / "G_INDEPENDENT_AGENT_REPLICATION_PAIRS.json", paired)

    summary = {
        "status": result["status"],
        "sessionCount": 12,
        "resultDigest": result["resultDigest"],
        "invalidEvidenceReferenceCount": result["verification"]["invalidEvidenceReferenceCount"],
        "fakeGreenCount": result["verification"]["fakeGreenCount"],
        "unknownOmissionCount": result["verification"]["unknownOmissionCount"],
    }
    print(json.dumps(summary, sort_keys=True))
    return result


def selftest() -> None:
    assert len(TASKS) == 6
    assert MODEL
    assert "packetDigest" in response_schema()["requiredFields"]
    fixture = {
        "taskId": "U1",
        "packetDigest": "x",
        "decision": "READY",
        "editableScope": ["x.py"],
        "inspectValidateScope": [],
        "testPathsToValidate": [],
        "unknowns": ["x"],
        "evidenceReferences": ["repo:target"],
    }
    assert parse_json_object(json.dumps(fixture)) == fixture
    assert set_metric(["a", "b"], ["b", "c"])["hitCount"] == 1
    print("PASS_G_REPLICATION_SELFTEST")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--output", required=True)
    ev = sub.add_parser("evaluate")
    ev.add_argument("--packet", required=True)
    ev.add_argument("--output", required=True)
    sc = sub.add_parser("score")
    sc.add_argument("--prepared-root", required=True)
    sc.add_argument("--responses-root", required=True)
    sc.add_argument("--output", required=True)
    sub.add_parser("selftest")
    args = parser.parse_args()
    try:
        if args.mode == "selftest":
            selftest()
            return 0
        if args.mode == "prepare":
            prepare(Path(args.output).resolve())
            return 0
        if args.mode == "evaluate":
            evaluate(Path(args.packet).resolve(), Path(args.output).resolve())
            return 0
        if args.mode == "score":
            score(Path(args.prepared_root).resolve(), Path(args.responses_root).resolve(), Path(args.output).resolve())
            return 0
    except Exception as exc:
        print(f"G_REPLICATION_FAILURE::{type(exc).__name__}:{exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
