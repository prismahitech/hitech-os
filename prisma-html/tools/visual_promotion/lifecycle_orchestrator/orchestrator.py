from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_application import authority as visual_authority
from visual_application import verify as gvae_verify
from visual_application import target_index, visual_work_entry_gate
from visual_application.security import TASK_ID_RE
from visual_promotion.canonical_registration import (
    authority_adapters,
    current_truth,
    derivation,
    engine,
    lifecycle_state,
    postconditions,
    projection_reconciler,
    request_builder,
    runtime_evidence_bridge,
    target_status,
    write_preflight,
)


SCHEMA = "prisma.visual.lifecycle-transition.v1"
RECEIPT_SCHEMA = "prisma.visual.lifecycle-receipt.v1"
STAGES = (
    "DISCOVER",
    "ASSESS_RESOLVE",
    "REGISTER_TARGET",
    "CANONICAL_BINDING",
    "AUTHORIZATION",
    "APPLY",
    "DERIVE",
    "RECONCILE",
    "RUNTIME_VERIFY",
    "VISUAL_CERTIFY",
    "CHANGE_ASSURANCE",
    "CLOSE",
)
TRANSITION_PAYLOAD_FIELDS = {
    "DISCOVER": {"workEntryRequest"},
    "ASSESS_RESOLVE": {"readinessRecord", "authority", "projectionEvidence"},
    "REGISTER_TARGET": {"authority", "authorization", "source"},
    "CANONICAL_BINDING": set(),
    "AUTHORIZATION": {"authority"},
    "APPLY": {"applyKind"},
    "DERIVE": {"executeDerivedSteps"},
    "RECONCILE": {"authority", "projectionEvidence"},
    "RUNTIME_VERIFY": {"gvaeVerifyRequest", "runtimeEvidence"},
    "VISUAL_CERTIFY": set(),
    "CHANGE_ASSURANCE": {"changeAssurance"},
    "CLOSE": set(),
}
LIFECYCLE_ID_RE = re.compile(r"^vlo-[a-z0-9][a-z0-9-]{2,95}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
CANONICAL_REGISTRATION_SURFACES = {"tablet", "pc", "mobile", "shared-ui"}
CAPABILITY_ID = "visual.canonical_promotion_integration_v1"
LIFECYCLE_ROOT = Path("prisma-html/governance/visual-promotion/lifecycle-orchestrator")
LIFECYCLES_ROOT = LIFECYCLE_ROOT / "lifecycles"
RECEIPTS_ROOT = LIFECYCLE_ROOT / "receipts"


class LifecycleOrchestratorError(ValueError):
    """Invalid or unsafe lifecycle request. The canonical authorities remain owners."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _json_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LifecycleOrchestratorError(f"{label}_OBJECT_REQUIRED")
    return value


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleOrchestratorError(f"{label}_UNREADABLE:{path}:{exc}") from exc
    return _json_object(value, label)


def _git_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )
    if result.returncode:
        raise LifecycleOrchestratorError("GIT_HEAD_UNAVAILABLE:" + result.stderr.strip()[:300])
    head = result.stdout.strip()
    if not HEX40_RE.fullmatch(head):
        raise LifecycleOrchestratorError("GIT_HEAD_INVALID")
    return head


def _authority_refs(repo_root: Path) -> dict[str, Any]:
    paths = {
        "factoryLedger": "PRISMA Factory Ledger/PRISMA_FACTORY_LEDGER.json",
        "ndcAuthorityMap": "apps/terminal-de-venta-system/docs/ndc/governance/ndc_authority_map.json",
        "identityBindings": "prisma-html/authority/rifat/identity/registries/element-bindings.registry.json",
        "identityRecipes": "prisma-html/authority/rifat/identity/registries/recipe.registry.json",
        "rifatRoutes": "prisma-html/authority/rifat/prisma-ui/routes.json",
        "targetIndex": "prisma-html/authority/rifat/prisma-ui/visual-control/target-index/manifest.json",
        "visualWorkEntry": "prisma-html/tools/visual_application/visual_work_entry_gate.py",
        "canonicalRegistration": "prisma-html/tools/visual_promotion/canonical_registration/engine.py",
        "runtimeEvidence": "prisma-html/tools/visual_promotion/canonical_registration/runtime_evidence_bridge.py",
        "changeAssuranceContract": "tools/code-atlas/CODE_ATLAS_CHANGE_ASSURANCE_CONTRACT.json",
    }
    result: dict[str, Any] = {}
    for name, relative in paths.items():
        path = repo_root / relative
        result[name] = {
            "path": relative,
            "sha256": file_digest(path) if path.is_file() and not path.is_symlink() else None,
            "present": path.is_file() and not path.is_symlink(),
        }
    return result


def _surface(work_entry_request: dict[str, Any]) -> str:
    surface = work_entry_request.get("surface")
    surfaces = work_entry_request.get("surfaces")
    if isinstance(surface, str):
        return surface
    if isinstance(surfaces, list) and len(surfaces) == 1 and isinstance(surfaces[0], str):
        return surfaces[0]
    return ""


def _surface_blocker(surface: str) -> str | None:
    if surface == "cloud-center":
        return "SURFACE_VISUAL_AUTHORITY_MISSING:cloud-center"
    if surface not in set(target_index.SURFACES):
        return f"SURFACE_VISUAL_AUTHORITY_UNKNOWN:{surface or 'missing'}"
    if surface not in CANONICAL_REGISTRATION_SURFACES:
        return f"SURFACE_CANONICAL_PROMOTION_UNSUPPORTED:{surface}"
    return None


def _candidate_ids(decision: dict[str, Any]) -> list[str]:
    details = decision.get("details") if isinstance(decision.get("details"), dict) else {}
    found: list[str] = []
    for key in ("targetIds", "matchedTargets"):
        value = details.get(key)
        if isinstance(value, list):
            found.extend(str(item) for item in value if isinstance(item, str) and item)
    return sorted(set(found))


def _classify_index_target(row: dict[str, Any]) -> target_status.TargetStatus:
    normalized = dict(row)
    if row.get("recordKind") == target_index.CENSUS_KIND or row.get("enforcement") == target_index.DISCOVERY_ONLY:
        return target_status.classify_target_status(normalized)
    if row.get("status") == "APPLY_READY":
        normalized["lifecycleStatus"] = "APPLY_READY"
    elif row.get("status") == "RUNTIME_VERIFIED":
        normalized["lifecycleStatus"] = "RUNTIME_VERIFIED"
    elif row.get("status") == "APPLIED":
        normalized["lifecycleStatus"] = "APPLIED"
    elif row.get("status") == "BLOCKED":
        normalized["lifecycleStatus"] = "BLOCKED"
    else:
        normalized["lifecycleStatus"] = "REGISTER_TARGET_FIRST"
    return target_status.classify_target_status(normalized)


def _discover(repo_root: Path, work_request: dict[str, Any], *, authority: dict[str, Any] | None = None) -> dict[str, Any]:
    surface = _surface(work_request)
    blocker = _surface_blocker(surface)
    if blocker:
        return {"status": "BLOCKED", "blockers": [blocker], "surface": surface}
    head = _git_head(repo_root)
    expected = work_request.get("expectedHead")
    if expected != head:
        return {
            "status": "BLOCKED",
            "blockers": ["EXPECTED_HEAD_MISMATCH"],
            "expectedHead": expected,
            "currentHead": head,
            "surface": surface,
        }
    loaded_authority = authority if authority is not None else visual_work_entry_gate.load_authority()
    decision = visual_work_entry_gate.decide_request(work_request, authority=loaded_authority, current_head=head)
    candidate_ids = _candidate_ids(decision)
    if len(candidate_ids) != 1:
        return {
            "status": "BLOCKED",
            "blockers": ["EXACTLY_ONE_TARGET_REQUIRED" if candidate_ids else "EXACT_TARGET_NOT_RESOLVED"],
            "candidateTargetIds": candidate_ids,
            "workEntryDecision": decision,
            "surface": surface,
            "expectedHead": head,
            "authorities": _authority_refs(repo_root),
        }
    target_id = candidate_ids[0]
    index = loaded_authority.get("index") if isinstance(loaded_authority.get("index"), dict) else {}
    records = [row for row in index.get("records", []) if isinstance(row, dict) and row.get("targetId") == target_id]
    if len(records) != 1:
        return {
            "status": "BLOCKED",
            "blockers": ["TARGET_INDEX_EXACT_RECORD_NOT_UNIQUE"],
            "candidateTargetIds": candidate_ids,
            "workEntryDecision": decision,
            "surface": surface,
            "expectedHead": head,
        }
    row = records[0]
    try:
        classified = _classify_index_target(row)
    except ValueError as exc:
        return {
            "status": "BLOCKED",
            "blockers": [str(exc)],
            "candidateTargetIds": candidate_ids,
            "workEntryDecision": decision,
            "surface": surface,
            "expectedHead": head,
        }
    if decision.get("decision") != "REGISTER_TARGET_FIRST":
        decision_blocker = "EXACT_APPLY_OUTSIDE_CANONICAL_REGISTRATION_LIFECYCLE" if decision.get("decision") == "GVAE_EXACT_APPLY" else "WORK_ENTRY_DID_NOT_AUTHORIZE_EXACT_TARGET_LIFECYCLE"
        blockers = [decision_blocker, *list(decision.get("reasons") or [])]
        return {
            "status": "BLOCKED",
            "blockers": blockers,
            "candidateTargetIds": candidate_ids,
            "targetStatus": classified.lifecycle,
            "workEntryDecision": decision,
            "surface": surface,
            "expectedHead": head,
        }
    if classified.blocker_codes:
        return {
            "status": "BLOCKED",
            "blockers": list(classified.blocker_codes),
            "candidateTargetIds": candidate_ids,
            "targetStatus": classified.lifecycle,
            "workEntryDecision": decision,
            "surface": surface,
            "expectedHead": head,
        }
    if decision.get("decision") == "REGISTER_TARGET_FIRST" and not (
        row.get("recordKind") == target_index.CENSUS_KIND
        and row.get("enforcement") == target_index.DISCOVERY_ONLY
    ):
        return {
            "status": "BLOCKED",
            "blockers": ["REGISTER_TARGET_FIRST_REQUIRES_CENSUS_TARGET"],
            "candidateTargetIds": candidate_ids,
            "workEntryDecision": decision,
            "surface": surface,
            "expectedHead": head,
        }
    census_id = row.get("censusTargetId") or (target_id if row.get("recordKind") == target_index.CENSUS_KIND else None)
    return {
        "status": "PASS",
        "blockers": [],
        "target": {
            "targetId": target_id,
            "censusTargetId": census_id,
            "surface": row.get("surface"),
            "recordKind": row.get("recordKind"),
            "enforcement": row.get("enforcement"),
            "status": row.get("status"),
            "bindingId": row.get("bindingId"),
            "semanticMeaningId": row.get("semanticMeaningId"),
            "applicationLayerId": row.get("applicationLayerId"),
            "routeId": row.get("routeId"),
            "componentUiId": row.get("componentUiId"),
            "regionId": row.get("regionId"),
            "slotId": row.get("slotId"),
            "ownerId": row.get("ownerId"),
            "implementationLayerId": row.get("implementationLayerId"),
        },
        "targetStatus": classified.lifecycle,
        "targetRecordDigest": digest(row),
        "workEntryDecision": decision,
        "surface": surface,
        "expectedHead": head,
        "authorities": _authority_refs(repo_root),
    }


def _safe_lifecycle_id(value: Any) -> str:
    if not isinstance(value, str) or not LIFECYCLE_ID_RE.fullmatch(value):
        raise LifecycleOrchestratorError("LIFECYCLE_ID_INVALID")
    return value


def _lifecycle_path(repo_root: Path, lifecycle_id: str) -> Path:
    return _safe_local_path(repo_root, LIFECYCLES_ROOT / f"{_safe_lifecycle_id(lifecycle_id)}.json")


def _receipt_dir(repo_root: Path, lifecycle_id: str) -> Path:
    return _safe_local_path(repo_root, RECEIPTS_ROOT / _safe_lifecycle_id(lifecycle_id))


def _safe_local_path(repo_root: Path, relative: Path) -> Path:
    root = repo_root.resolve()
    path = root / relative
    resolved = path.resolve(strict=False)
    if resolved != root and root not in resolved.parents:
        raise LifecycleOrchestratorError("LIFECYCLE_STORAGE_PATH_ESCAPE")
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise LifecycleOrchestratorError("LIFECYCLE_STORAGE_SYMLINK_FORBIDDEN")
    return path


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".visual-lifecycle-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_lifecycle(repo_root: Path, lifecycle_id: str) -> dict[str, Any] | None:
    path = _lifecycle_path(repo_root, lifecycle_id)
    if not path.is_file():
        return None
    record = _load_json(path, "LIFECYCLE")
    if record.get("schema") != SCHEMA or record.get("lifecycleId") != lifecycle_id:
        raise LifecycleOrchestratorError("LIFECYCLE_RECORD_IDENTITY_INVALID")
    return record


def _verify_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise LifecycleOrchestratorError("TRANSITION_RECEIPT_SCHEMA_INVALID")
    expected = digest({
        "lifecycleId": receipt.get("lifecycleId"),
        "transition": receipt.get("transition"),
        "requestDigest": receipt.get("requestDigest"),
        "repoHead": receipt.get("repoHead"),
        "result": receipt.get("result"),
    })
    if receipt.get("receiptDigest") != expected:
        raise LifecycleOrchestratorError("TRANSITION_RECEIPT_DIGEST_MISMATCH")
    return receipt


def _save_receipt(repo_root: Path, lifecycle_id: str, receipt: dict[str, Any]) -> Path:
    receipt_id = str(receipt.get("transitionId") or "")
    if not re.fullmatch(r"[0-9]{3}-[A-Z_]+-[0-9a-f]{12}", receipt_id):
        raise LifecycleOrchestratorError("TRANSITION_RECEIPT_ID_INVALID")
    path = _safe_local_path(repo_root, RECEIPTS_ROOT / lifecycle_id / f"{receipt_id}.json")
    if path.exists():
        prior = _verify_receipt(_load_json(path, "TRANSITION_RECEIPT"))
        if digest(prior) != digest(receipt):
            raise LifecycleOrchestratorError("TRANSITION_RECEIPT_REPLAY_CONFLICT")
        return path
    _atomic_json(path, receipt)
    return path


def _maintenance_receipt(
    repo_root: Path,
    record: dict[str, Any],
    operation: str,
    request_body: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    lifecycle_id = _safe_lifecycle_id(record.get("lifecycleId"))
    request_digest = digest(request_body)
    storage_key = "supersession" if operation == "SUPERSEDE" else operation.lower()
    prior = record.get(storage_key) or {}
    if prior.get("requestDigest") == request_digest and isinstance(prior.get("receiptId"), str):
        return load_receipt(repo_root, lifecycle_id, prior["receiptId"])
    sequence = len(record.get("history", [])) + 1
    transition_id = f"{sequence:03d}-{operation}-{digest({'lifecycleId': lifecycle_id, 'requestDigest': request_digest})[:12]}"
    repo_head = _git_head(repo_root)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "transitionId": transition_id,
        "lifecycleId": lifecycle_id,
        "transition": operation,
        "requestDigest": request_digest,
        "repoHead": repo_head,
        "createdAt": _utc_now(),
        "result": result,
        "receiptDigest": digest({
            "lifecycleId": lifecycle_id,
            "transition": operation,
            "requestDigest": request_digest,
            "repoHead": repo_head,
            "result": result,
        }),
    }
    path = _save_receipt(repo_root, lifecycle_id, receipt)
    item = {
        "transitionId": transition_id,
        "transition": operation,
        "requestDigest": request_digest,
        "receiptPath": str(path.relative_to(repo_root)).replace("\\", "/"),
        "receiptDigest": receipt["receiptDigest"],
        "status": result.get("status"),
        "repoHead": repo_head,
    }
    record.setdefault("history", []).append(item)
    record[storage_key] = {**result, "requestDigest": request_digest, "receiptId": transition_id}
    record["updatedAt"] = _utc_now()
    return receipt


def _verified_authority_bundle(repo_root: Path, authority: dict[str, Any], expected_head: str) -> dict[str, Any]:
    if not isinstance(authority, dict):
        raise LifecycleOrchestratorError("AUTHORITY_BUNDLE_REQUIRED")
    commit = authority.get("authorityCommit")
    if commit != expected_head or not isinstance(commit, str) or not HEX40_RE.fullmatch(commit):
        raise LifecycleOrchestratorError("AUTHORITY_MESH_EXPECTED_HEAD_MISMATCH")
    mesh_input = {
        "authorityTaskId": authority.get("authorityTaskId"),
        "authorityMeshArtifact": authority.get("authorityMeshArtifact"),
        "authorityMeshArtifactSha256": authority.get("authorityMeshArtifactSha256"),
        "authorityMeshRequestDigest": authority.get("authorityMeshRequestDigest"),
    }
    try:
        mesh = visual_authority.verify_mesh_artifact(mesh_input, repo_root, commit)
    except Exception as exc:
        raise LifecycleOrchestratorError(f"AUTHORITY_MESH_BLOCKED:{exc}") from exc
    artifact_relative = authority.get("authorityMeshArtifact")
    if not isinstance(artifact_relative, str) or Path(artifact_relative).is_absolute() or ".." in Path(artifact_relative).parts:
        raise LifecycleOrchestratorError("AUTHORITY_MESH_PATH_INVALID")
    artifact_path = repo_root / artifact_relative
    if artifact_path.is_symlink() or not artifact_path.is_file():
        raise LifecycleOrchestratorError("AUTHORITY_MESH_ARTIFACT_NOT_REGULAR_FILE")
    task_id = authority.get("authorityTaskId")
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        raise LifecycleOrchestratorError("AUTHORITY_TASK_ID_REQUIRED")
    layer_name = f"tasks/{task_id}/authority_mesh/reports/LAYERS_MAP.json"
    try:
        with zipfile.ZipFile(artifact_path) as outer:
            composed_bytes = outer.read("prisma-automesh-composed-result.zip") if "prisma-automesh-composed-result.zip" in outer.namelist() else artifact_path.read_bytes()
        with zipfile.ZipFile(io.BytesIO(composed_bytes)) as composed:
            legacy_bytes = composed.read("legacy_surface_mesh.zip")
        with zipfile.ZipFile(io.BytesIO(legacy_bytes)) as legacy:
            layer_bytes = legacy.read(layer_name)
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise LifecycleOrchestratorError(f"AUTHORITY_LAYER_MAP_UNREADABLE:{exc}") from exc
    layer_digest = hashlib.sha256(layer_bytes).hexdigest()
    supplied_layer_digest = authority.get("layerMapSha256")
    if supplied_layer_digest is not None and supplied_layer_digest != layer_digest:
        raise LifecycleOrchestratorError("AUTHORITY_LAYER_MAP_DIGEST_MISMATCH")
    return {**mesh, "layerMapDigest": layer_digest, "authorityTaskId": task_id}


def _factory_mutation_gate(repo_root: Path, expected_head: str, mesh: dict[str, Any]) -> dict[str, Any]:
    gate_path = repo_root / "PRISMA Factory Ledger" / "tools" / "verify_prisma_anti_rework_gate.py"
    spec = importlib.util.spec_from_file_location("prisma_factory_anti_rework_gate_lifecycle", gate_path)
    if spec is None or spec.loader is None:
        raise LifecycleOrchestratorError("FACTORY_LEDGER_GATE_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        authority = module.read_authority(repo_root)
        request = {
            "schemaVersion": module.SCHEMA,
            "mode": "MUTATION",
            "expectedHead": expected_head,
            "task": "Advance one exact PRISMA visual lifecycle target through canonical promotion authorities.",
            "capabilities": [{"id": CAPABILITY_ID, "requestedAction": "ADVANCE"}],
            "authorityMesh": {
                key: mesh[key]
                for key in ("status", "repoHead", "requiredAuthorityCoveragePct", "blockers", "requestDigest", "artifactDigest", "layerMapPresent")
            },
            "visualMutation": True,
        }
        result = module.decide(repo_root, authority, request)
    except Exception as exc:
        raise LifecycleOrchestratorError(f"FACTORY_LEDGER_GATE_FAILED:{exc}") from exc
    if result.get("result") != "PASS_ANTI_REWORK_GATE":
        raise LifecycleOrchestratorError("FACTORY_LEDGER_MUTATION_BLOCKED:" + ",".join(result.get("errors") or []))
    return result


def _registration_request(repo_root: Path, record: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    discovery = record.get("discovery") or {}
    target = discovery.get("target") or {}
    if discovery.get("workEntryDecision", {}).get("decision") != "REGISTER_TARGET_FIRST":
        raise LifecycleOrchestratorError("CANONICAL_REGISTRATION_REQUIRES_REGISTER_TARGET_FIRST")
    authority = _verified_authority_bundle(repo_root, payload.get("authority"), _git_head(repo_root))
    truth = current_truth.capture_current_truth(
        repo_root,
        evidence_target_id=str(target.get("censusTargetId") or target.get("targetId") or ""),
        repo_head=_git_head(repo_root),
        authority_mesh_digest=authority["artifactDigest"],
        layer_map_digest=authority["layerMapDigest"],
    )
    readiness = (record.get("assessment") or {}).get("readinessRecord")
    if not isinstance(readiness, dict):
        raise LifecycleOrchestratorError("PROMOTION_READINESS_RECORD_REQUIRED")
    authorization = payload.get("authorization")
    source = payload.get("source")
    if not isinstance(authorization, dict) or not isinstance(source, dict):
        raise LifecycleOrchestratorError("REGISTRATION_AUTHORIZATION_AND_SOURCE_REQUIRED")
    handoff = {
        "gate": "visual_application.visual_work_entry_gate",
        "decision": "REGISTER_TARGET_FIRST",
        "targetId": target.get("censusTargetId") or target.get("targetId"),
        "evaluatedHead": _git_head(repo_root),
    }
    try:
        request = request_builder.build_request_from_readiness(
            readiness,
            current_truth=truth,
            expected_current_head=_git_head(repo_root),
            authorization=authorization,
            source=source,
            work_entry_handoff=handoff,
        )
        plan = engine.build_plan(request, repo_root)
    except Exception as exc:
        raise LifecycleOrchestratorError(f"CANONICAL_REGISTRATION_PLAN_BLOCKED:{exc}") from exc
    preflight_context = {
        "expectedCurrentHead": request["expectedCurrentHead"],
        "currentHead": _git_head(repo_root),
        "automaticSemanticInference": authorization.get("automaticSemanticInference"),
        "automaticApplicationSource": authorization.get("automaticApplicationSource"),
        "writerKind": "CANONICAL_REGISTRATION",
        "authorityDomain": "canonical-registration",
        "targetId": target.get("censusTargetId") or target.get("targetId"),
        "sourcePath": source.get("path"),
        "sourceDigest": source.get("digest"),
        "runtimeMutationAllowed": False,
    }
    try:
        preflight = write_preflight.validate_write_preflight(repo_root, preflight_context)
    except Exception as exc:
        raise LifecycleOrchestratorError(f"CANONICAL_WRITE_PREFLIGHT_BLOCKED:{exc}") from exc
    return {
        "request": request,
        "plan": plan,
        "currentTruth": truth,
        "authorityMesh": authority,
        "writePreflight": preflight.__dict__,
    }


def _expected_transition(record: dict[str, Any] | None) -> str:
    if record is None:
        return STAGES[0]
    if record.get("lifecycleState") == "SUPERSEDED":
        return "TERMINAL_SUPERSEDED"
    if (record.get("rollback") or {}).get("status") == "ROLLED_BACK":
        return "SUPERSEDE_ONLY"
    blocked_at = record.get("blockedAt")
    if isinstance(blocked_at, str) and blocked_at in STAGES:
        return blocked_at
    current = record.get("currentStage")
    if current not in STAGES:
        raise LifecycleOrchestratorError("LIFECYCLE_CURRENT_STAGE_INVALID")
    position = STAGES.index(current) + 1
    return STAGES[position] if position < len(STAGES) else "COMPLETE"


def _runtime_target(record: dict[str, Any]) -> dict[str, Any]:
    plan = record.get("registrationPlan") or {}
    request = record.get("registrationRequest") or {}
    decision = request.get("decision") or {}
    binding = (decision.get("bindingAction") or {}).get("exactBinding") or {}
    exact_targets = binding.get("targets") or []
    exact = exact_targets[0] if len(exact_targets) == 1 and isinstance(exact_targets[0], dict) else {}
    return {
        "targetId": plan.get("targetId"),
        "censusTargetId": plan.get("censusTargetId"),
        "routeId": exact.get("routeId"),
        "surfaceKey": plan.get("surfaceKey"),
    }


def _execute_stage(repo_root: Path, stage: str, record: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if stage == "DISCOVER":
        work_request = payload.get("workEntryRequest")
        if not isinstance(work_request, dict):
            raise LifecycleOrchestratorError("WORK_ENTRY_REQUEST_REQUIRED")
        return _discover(repo_root, work_request)

    if stage == "ASSESS_RESOLVE":
        from visual_promotion import promotion_readiness

        discovery = record.get("discovery") or {}
        if discovery.get("status") != "PASS":
            raise LifecycleOrchestratorError("DISCOVERY_PASS_REQUIRED")
        readiness = payload.get("readinessRecord")
        if not isinstance(readiness, dict):
            raise LifecycleOrchestratorError("PROMOTION_READINESS_RECORD_REQUIRED")
        target = discovery.get("target") or {}
        census_target = target.get("censusTargetId") or target.get("targetId")
        if readiness.get("targetId") != census_target:
            raise LifecycleOrchestratorError("READINESS_CENSUS_TARGET_MISMATCH")
        try:
            certified = promotion_readiness.load_certified_corpus()
            promotion_readiness.validate_resolution_row(
                readiness,
                expected_surface=str(target.get("surface") or ""),
                certified=certified,
            )
        except Exception as exc:
            raise LifecycleOrchestratorError(f"PROMOTION_READINESS_BLOCKED:{exc}") from exc
        if readiness.get("promotionReadinessDecision") != promotion_readiness.READY_REGISTER:
            return {
                "status": "BLOCKED",
                "blockers": ["PROMOTION_READINESS_NOT_READY"],
                "readinessDecision": readiness.get("promotionReadinessDecision"),
            }
        authority = _verified_authority_bundle(repo_root, payload.get("authority"), _git_head(repo_root))
        truth = current_truth.capture_current_truth(
            repo_root,
            evidence_target_id=str(census_target),
            repo_head=_git_head(repo_root),
            authority_mesh_digest=authority["artifactDigest"],
            layer_map_digest=authority["layerMapDigest"],
        )
        projection_evidence = payload.get("projectionEvidence") or {}
        try:
            projection = projection_reconciler.reconcile_projection(
                target_id=str(census_target),
                current_truth=truth,
                projection_classification=str(readiness.get("projectionDebtClassification") or ""),
                canonical_source_sha256=projection_evidence.get("canonicalSourceSha256"),
                current_source_sha256=projection_evidence.get("currentSourceSha256"),
                canonical_output_sha256=projection_evidence.get("canonicalOutputSha256"),
                current_output_sha256=projection_evidence.get("currentOutputSha256"),
                newer_runtime=projection_evidence.get("newerRuntime"),
                intentional_divergence=projection_evidence.get("intentionalDivergence"),
                ambiguity=projection_evidence.get("ambiguity"),
            )
        except Exception as exc:
            raise LifecycleOrchestratorError(f"PROJECTION_RECONCILIATION_BLOCKED:{exc}") from exc
        if projection.decision in {"BLOCK_AMBIGUOUS", "BLOCK_UNSAFE"}:
            return {"status": "BLOCKED", "blockers": [projection.reason], "projectionReconciliation": projection.__dict__}
        return {
            "status": "PASS",
            "readinessRecord": readiness,
            "readinessDigest": digest(readiness),
            "currentTruth": truth,
            "authorityMesh": authority,
            "projectionReconciliation": projection.__dict__,
            "nextTransition": "REGISTER_TARGET",
        }

    if stage == "REGISTER_TARGET":
        assessed = record.get("assessment") or {}
        if not assessed:
            raise LifecycleOrchestratorError("ASSESS_RESOLVE_PASS_REQUIRED")
        built = _registration_request(repo_root, record, payload)
        if built["plan"].get("status") not in {"APPLY", "NO_OP_IDEMPOTENT"}:
            raise LifecycleOrchestratorError("CANONICAL_REGISTRATION_PLAN_STATUS_INVALID")
        return {
            "status": "PASS",
            "registrationRequest": built["request"],
            "registrationPlan": built["plan"],
            "currentTruth": built["currentTruth"],
            "authorityMesh": built["authorityMesh"],
            "writePreflight": built["writePreflight"],
            "nextTransition": "CANONICAL_BINDING",
        }

    if stage == "CANONICAL_BINDING":
        request = record.get("registrationRequest")
        expected_plan = record.get("registrationPlan")
        if not isinstance(request, dict) or not isinstance(expected_plan, dict):
            raise LifecycleOrchestratorError("CANONICAL_REGISTRATION_PLAN_REQUIRED")
        plan = engine.build_plan(request, repo_root)
        if digest(plan) != digest(expected_plan):
            raise LifecycleOrchestratorError("CANONICAL_REGISTRATION_PLAN_DRIFT")
        decision = request.get("decision") or {}
        exact = (decision.get("bindingAction") or {}).get("exactBinding")
        if not isinstance(exact, dict):
            raise LifecycleOrchestratorError("EXACT_BINDING_REQUIRED")
        authority_adapters.validate_exact_binding(
            repo_root,
            exact,
            plan["targetId"],
            plan["surfaceKey"],
            (decision.get("semanticAuthority") or {}).get("canonicalMeaningId"),
        )
        return {
            "status": "PASS",
            "targetId": plan["targetId"],
            "bindingId": plan["ids"]["bindingId"],
            "recipeId": plan["ids"]["recipeId"],
            "exactBindingDigest": digest(exact),
            "nextTransition": "AUTHORIZATION",
        }

    if stage == "AUTHORIZATION":
        request = record.get("registrationRequest")
        if not isinstance(request, dict):
            raise LifecycleOrchestratorError("CANONICAL_REGISTRATION_REQUEST_REQUIRED")
        authorization = request.get("authorization") or {}
        if authorization.get("canonicalRegistrationAuthorized") is not True:
            return {"status": "BLOCKED", "blockers": ["CANONICAL_REGISTRATION_AUTHORIZATION_REQUIRED"]}
        expected_head = request.get("expectedCurrentHead")
        current_head = _git_head(repo_root)
        if current_head != expected_head:
            return {"status": "BLOCKED", "blockers": ["EXPECTED_HEAD_MISMATCH"], "expectedHead": expected_head, "currentHead": current_head}
        work_request = record.get("workEntryRequest")
        if not isinstance(work_request, dict):
            raise LifecycleOrchestratorError("ORIGINAL_WORK_ENTRY_REQUEST_REQUIRED")
        refreshed_discovery = _discover(repo_root, work_request)
        expected_target = request.get("target", {}).get("censusTargetId")
        if (
            refreshed_discovery.get("status") != "PASS"
            or (refreshed_discovery.get("target") or {}).get("targetId") != expected_target
            or refreshed_discovery.get("workEntryDecision", {}).get("decision") != "REGISTER_TARGET_FIRST"
        ):
            return {
                "status": "BLOCKED",
                "blockers": ["WORK_ENTRY_AUTHORITY_CHANGED_SINCE_DISCOVERY"],
                "refreshedDiscovery": refreshed_discovery,
            }
        mesh = _verified_authority_bundle(repo_root, payload.get("authority"), expected_head)
        try:
            factory = _factory_mutation_gate(repo_root, expected_head, mesh)
        except LifecycleOrchestratorError as exc:
            return {"status": "BLOCKED", "blockers": [str(exc)], "authorityMesh": mesh}
        return {
            "status": "PASS",
            "canonicalRegistrationAuthorized": True,
            "productVisualApplyAuthorized": False,
            "productVisualApplyBlocker": "CAPABILITY_DOES_NOT_AUTHORIZE_PRODUCT_RUNTIME_MUTATION",
            "authorityMesh": mesh,
            "factoryLedgerDecisionDigest": factory.get("decisionDigest"),
            "factoryLedgerResult": factory.get("result"),
            "nextTransition": "APPLY",
        }

    if stage == "APPLY":
        apply_kind = payload.get("applyKind")
        if apply_kind == "product_visual":
            return {
                "status": "BLOCKED",
                "blockers": ["CAPABILITY_DOES_NOT_AUTHORIZE_PRODUCT_RUNTIME_MUTATION"],
                "gvaeApplyInvoked": False,
            }
        if apply_kind != "canonical_registration":
            raise LifecycleOrchestratorError("APPLY_KIND_EXPLICIT_REQUIRED")
        authorization = record.get("authorizationResult") or {}
        if authorization.get("canonicalRegistrationAuthorized") is not True or authorization.get("factoryLedgerResult") != "PASS_ANTI_REWORK_GATE":
            return {"status": "BLOCKED", "blockers": ["CANONICAL_REGISTRATION_AUTHORIZATION_PASS_REQUIRED"]}
        request = record.get("registrationRequest")
        if not isinstance(request, dict):
            raise LifecycleOrchestratorError("CANONICAL_REGISTRATION_REQUEST_REQUIRED")
        result = engine.register(request, repo_root)
        registration_plan = record.get("registrationPlan")
        if not isinstance(registration_plan, dict):
            raise LifecycleOrchestratorError("CANONICAL_REGISTRATION_PLAN_REQUIRED")
        postcondition_result = postconditions.verify_registration_postconditions(repo_root, registration_plan)
        return {
            "status": "PASS",
            "applyKind": apply_kind,
            "registrationResult": result,
            "registrationPostconditions": postcondition_result,
            "canonicalMutationPerformed": result.get("status") == "APPLIED",
            "productRuntimeMutationPerformed": False,
            "nextTransition": "DERIVE",
        }

    if stage == "DERIVE":
        registration = record.get("applyResult", {}).get("registrationResult") or {}
        target_id = registration.get("targetId")
        if not isinstance(target_id, str) or not target_id:
            raise LifecycleOrchestratorError("REGISTERED_TARGET_ID_REQUIRED")
        if payload.get("executeDerivedSteps") is not True:
            return {"status": "BLOCKED", "blockers": ["DERIVED_STEP_EXECUTION_NOT_AUTHORIZED"]}
        plan = derivation.plan_derivation(repo_root, target_id)
        results = []
        for step in plan.get("steps", []):
            command = step.get("command")
            if not isinstance(command, list) or not command:
                raise LifecycleOrchestratorError("DERIVATION_COMMAND_INVALID")
            completed = subprocess.run(
                command,
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
            )
            results.append({
                "stepId": step.get("id"),
                "command": command,
                "returncode": completed.returncode,
                "stdout": completed.stdout[-3000:],
                "stderr": completed.stderr[-3000:],
            })
            if completed.returncode != 0:
                return {"status": "BLOCKED", "blockers": [f"DERIVATION_STEP_FAILED:{step.get('id')}"], "plan": plan, "results": results}
        verification = derivation.verify_derivation(repo_root, plan)
        return {"status": "PASS", "plan": plan, "results": results, "verification": verification, "nextTransition": "RECONCILE"}

    if stage == "RECONCILE":
        target = _runtime_target(record)
        if not target.get("targetId"):
            raise LifecycleOrchestratorError("EXACT_CANONICAL_TARGET_REQUIRED")
        authority = _verified_authority_bundle(repo_root, payload.get("authority"), _git_head(repo_root))
        truth = current_truth.capture_current_truth(
            repo_root,
            evidence_target_id=str(target.get("censusTargetId") or ""),
            repo_head=_git_head(repo_root),
            authority_mesh_digest=authority["artifactDigest"],
            layer_map_digest=authority["layerMapDigest"],
        )
        evidence = payload.get("projectionEvidence") or {}
        decision = projection_reconciler.reconcile_projection(
            target_id=str(target["targetId"]),
            current_truth=truth,
            projection_classification=str(evidence.get("classification") or ""),
            canonical_source_sha256=evidence.get("canonicalSourceSha256"),
            current_source_sha256=evidence.get("currentSourceSha256"),
            canonical_output_sha256=evidence.get("canonicalOutputSha256"),
            current_output_sha256=evidence.get("currentOutputSha256"),
            newer_runtime=evidence.get("newerRuntime"),
            intentional_divergence=evidence.get("intentionalDivergence"),
            ambiguity=evidence.get("ambiguity"),
        )
        if decision.decision in {"BLOCK_AMBIGUOUS", "BLOCK_UNSAFE"}:
            return {"status": "BLOCKED", "blockers": [decision.reason], "decision": decision.__dict__}
        return {"status": "PASS", "decision": decision.__dict__, "currentTruth": truth, "nextTransition": "RUNTIME_VERIFY"}

    if stage == "RUNTIME_VERIFY":
        evidence = payload.get("runtimeEvidence")
        if not isinstance(evidence, dict):
            raise LifecycleOrchestratorError("RUNTIME_EVIDENCE_REQUIRED")
        gvae_request = payload.get("gvaeVerifyRequest")
        if not isinstance(gvae_request, dict) or gvae_request.get("mode") != "VERIFY":
            raise LifecycleOrchestratorError("EXACT_GVAE_VERIFY_REQUEST_REQUIRED")
        target = _runtime_target(record)
        if gvae_request.get("targetId") != target.get("targetId"):
            raise LifecycleOrchestratorError("GVAE_VERIFY_EXACT_TARGET_MISMATCH")
        transition_head = record.get("transitionHead")
        if gvae_request.get("authorityCommit") != transition_head:
            raise LifecycleOrchestratorError("GVAE_VERIFY_AUTHORITY_HEAD_MISMATCH")
        gvae_result = gvae_verify(
            gvae_request,
            lambda: target_index.build_index(repo_root),
            repo_root,
        )
        if (
            gvae_result.get("status") != "STATIC_GREEN"
            or gvae_result.get("targetId") != target.get("targetId")
            or gvae_result.get("evidenceClassification") != "SOURCE_STATIC_ONLY"
            or gvae_result.get("runtimeVisualGreen") is not False
        ):
            return {
                "status": "BLOCKED",
                "blockers": ["GVAE_SOURCE_STATIC_VERIFY_NOT_GREEN"],
                "gvaeVerification": gvae_result,
            }
        evidence = copy.deepcopy(evidence)
        supplied_gvae_state = evidence.get("gvaeVerifyState")
        if supplied_gvae_state not in (None, "PASS"):
            raise LifecycleOrchestratorError("RUNTIME_EVIDENCE_GVAE_VERIFY_STATE_NOT_PASS")
        evidence["gvaeVerifyState"] = "PASS"
        try:
            certification = runtime_evidence_bridge.validate_runtime_evidence(evidence)
        except Exception as exc:
            raise LifecycleOrchestratorError(f"RUNTIME_EVIDENCE_INVALID:{exc}") from exc
        if certification.target_id != target.get("targetId"):
            raise LifecycleOrchestratorError("RUNTIME_EVIDENCE_EXACT_TARGET_MISMATCH")
        evidence_target = evidence.get("target") or {}
        if evidence_target.get("censusTargetId") != target.get("censusTargetId"):
            raise LifecycleOrchestratorError("RUNTIME_EVIDENCE_CENSUS_TARGET_MISMATCH")
        if evidence_target.get("route") != target.get("routeId"):
            raise LifecycleOrchestratorError("RUNTIME_EVIDENCE_ROUTE_MISMATCH")
        if (evidence.get("build") or {}).get("commitSha") != transition_head:
            raise LifecycleOrchestratorError("RUNTIME_EVIDENCE_BUILD_HEAD_MISMATCH")
        if certification.certification_state != "VISUAL_CERTIFIED":
            return {
                "status": "BLOCKED",
                "blockers": ["RUNTIME_EVIDENCE_NOT_ALL_PASS"],
                "certification": certification.__dict__,
                "evidenceDigest": certification.evidence_digest,
            }
        return {
            "status": "PASS",
            "runtimeEvidence": evidence,
            "gvaeVerification": gvae_result,
            "gvaeVerificationDigest": digest(gvae_result),
            "certification": certification.__dict__,
            "changeAssuranceHandoff": runtime_evidence_bridge.build_change_assurance_handoff(evidence, certification),
            "nextTransition": "VISUAL_CERTIFY",
        }

    if stage == "VISUAL_CERTIFY":
        runtime = record.get("runtimeVerification") or {}
        evidence = runtime.get("runtimeEvidence")
        if not isinstance(evidence, dict):
            raise LifecycleOrchestratorError("RUNTIME_VERIFY_PASS_REQUIRED")
        certification = runtime_evidence_bridge.validate_runtime_evidence(evidence)
        if certification.certification_state != "VISUAL_CERTIFIED":
            return {"status": "BLOCKED", "blockers": ["VISUAL_CERTIFICATION_REQUIRES_ALL_RUNTIME_CHECKS_PASS"]}
        return {
            "status": "PASS",
            "state": certification.certification_state,
            "targetId": certification.target_id,
            "evidenceDigest": certification.evidence_digest,
            "certificationAuthority": "visual_promotion.canonical_registration.runtime_evidence_bridge",
            "nextTransition": "CHANGE_ASSURANCE",
        }

    if stage == "CHANGE_ASSURANCE":
        source_root = str((repo_root / "tools" / "code-atlas" / "src").resolve())
        if source_root not in sys.path:
            sys.path.insert(0, source_root)
        from code_atlas.change_intelligence.universal_binding import prepare_change, verify_prepared_change

        request = payload.get("changeAssurance")
        if not isinstance(request, dict):
            raise LifecycleOrchestratorError("CHANGE_ASSURANCE_REQUEST_REQUIRED")
        policy = request.get("policy")
        if not isinstance(policy, dict) or not isinstance(policy.get("requiredAuthorities"), list) or not policy.get("policyDigest"):
            raise LifecycleOrchestratorError("CHANGE_ASSURANCE_AUTHORITY_POLICY_REQUIRED")
        target_paths = request.get("targetPaths")
        changed_paths = request.get("changedPaths")
        if not isinstance(target_paths, list) or not target_paths or not isinstance(changed_paths, list) or not changed_paths:
            raise LifecycleOrchestratorError("CHANGE_ASSURANCE_EXACT_PATHS_REQUIRED")
        if any(not isinstance(path, str) or not path for path in [*target_paths, *changed_paths]):
            raise LifecycleOrchestratorError("CHANGE_ASSURANCE_PATH_INVALID")
        allowed_scope = request.get("additionalAllowedScope") or []
        if not isinstance(allowed_scope, list) or any(not isinstance(path, str) or not path for path in allowed_scope):
            raise LifecycleOrchestratorError("CHANGE_ASSURANCE_ALLOWED_SCOPE_INVALID")
        change_request = request.get("changeRequest")
        if not isinstance(change_request, str) or not change_request.strip():
            raise LifecycleOrchestratorError("CHANGE_ASSURANCE_REQUEST_TEXT_REQUIRED")
        produced_evidence = request.get("producedEvidence") or []
        if not isinstance(produced_evidence, list):
            raise LifecycleOrchestratorError("CHANGE_ASSURANCE_PRODUCED_EVIDENCE_LIST_REQUIRED")
        output_root = Path(request.get("outputRoot") or Path(tempfile.gettempdir()) / "prisma-visual-lifecycle-change-assurance").resolve()
        resolved_root = repo_root.resolve()
        if output_root == resolved_root or resolved_root in output_root.parents:
            raise LifecycleOrchestratorError("CHANGE_ASSURANCE_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
        preparation = prepare_change(
            repo_root,
            change_request=change_request,
            target_paths=target_paths,
            output_root=output_root,
            policy=policy,
            domain="PRISMA visual lifecycle",
            intent="VERIFY",
            additional_allowed_scope=allowed_scope,
        )
        if preparation.get("decision") != "PASS":
            return {"status": "BLOCKED", "blockers": preparation.get("reasonCodes") or ["CHANGE_ASSURANCE_PREPARATION_BLOCKED"], "preparation": preparation}
        verification = verify_prepared_change(
            preparation,
            repo_root,
            changed_paths=changed_paths,
            produced_evidence=[
                (record.get("runtimeVerification") or {}).get("changeAssuranceHandoff"),
                {
                    "kind": "gvae-source-static-verify",
                    "digest": (record.get("runtimeVerification") or {}).get("gvaeVerificationDigest"),
                },
                *(request.get("producedEvidence") or []),
            ],
            output_root=output_root,
            policy=policy,
        )
        if verification.get("decision") != "PASS":
            return {"status": "BLOCKED", "blockers": ["CHANGE_ASSURANCE_VERIFICATION_BLOCKED"], "preparation": preparation, "verification": verification}
        return {"status": "PASS", "preparation": preparation, "verification": verification, "nextTransition": "CLOSE"}

    if stage == "CLOSE":
        certification = record.get("visualCertification") or {}
        assurance = record.get("changeAssurance") or {}
        if certification.get("state") != "VISUAL_CERTIFIED":
            return {"status": "BLOCKED", "blockers": ["VISUAL_CERTIFICATION_REQUIRED"]}
        if assurance.get("verification", {}).get("decision") != "PASS":
            return {"status": "BLOCKED", "blockers": ["CHANGE_ASSURANCE_PASS_REQUIRED"]}
        lifecycle_status = lifecycle_state.normalize_lifecycle({
            "state": "DONE",
            "statusIsAuthority": False,
            "statusMayAuthorizeMutation": False,
            "blockerCodes": [],
        })
        previous = record.get("lifecycleStateEvidence")
        lifecycle_state.assert_transition(previous, {
            "state": "DONE",
            "statusIsAuthority": False,
            "statusMayAuthorizeMutation": False,
            "blockerCodes": [],
        })
        return {
            "status": "PASS",
            "state": lifecycle_status.canonical_state,
            "targetId": certification.get("targetId"),
            "receiptDigest": digest(record.get("history") or []),
            "g01Closed": False,
            "g01ClosureEvidenceRequired": "Independent operational evidence must be accepted by the capability owner.",
        }

    raise LifecycleOrchestratorError(f"TRANSITION_NOT_IMPLEMENTED:{stage}")


def advance_transition(request: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    """Execute exactly the next lifecycle transition and persist an immutable receipt."""
    if not isinstance(request, dict) or request.get("schema") != SCHEMA:
        raise LifecycleOrchestratorError("LIFECYCLE_TRANSITION_SCHEMA_INVALID")
    allowed_request_fields = {"schema", "lifecycleId", "transition", "expectedHead", "payload"}
    if set(request) - allowed_request_fields:
        raise LifecycleOrchestratorError("LIFECYCLE_TRANSITION_UNKNOWN_FIELDS")
    lifecycle_id = _safe_lifecycle_id(request.get("lifecycleId"))
    stage = request.get("transition")
    if stage not in STAGES:
        raise LifecycleOrchestratorError("TRANSITION_INVALID")
    payload = request.get("payload") or {}
    if not isinstance(payload, dict):
        raise LifecycleOrchestratorError("TRANSITION_PAYLOAD_OBJECT_REQUIRED")
    if set(payload) - TRANSITION_PAYLOAD_FIELDS[stage]:
        raise LifecycleOrchestratorError(f"TRANSITION_PAYLOAD_UNKNOWN_FIELDS:{stage}")
    current_head = _git_head(repo_root)
    expected_head = request.get("expectedHead")
    if expected_head != current_head:
        raise LifecycleOrchestratorError("EXPECTED_HEAD_MISMATCH")
    prior = _load_lifecycle(repo_root, lifecycle_id)
    if prior and prior.get("lifecycleState") == "SUPERSEDED":
        raise LifecycleOrchestratorError("LIFECYCLE_SUPERSEDED_TERMINAL")
    if prior and _expected_transition(prior) == "SUPERSEDE_ONLY":
        raise LifecycleOrchestratorError("LIFECYCLE_ROLLED_BACK_CANNOT_ADVANCE")
    request_digest = digest({key: value for key, value in request.items() if key not in {"createdAt"}})
    if prior:
        for item in prior.get("history", []):
            if item.get("transition") == stage and item.get("requestDigest") == request_digest:
                receipt_path = _safe_local_path(repo_root, RECEIPTS_ROOT / lifecycle_id / f"{item['transitionId']}.json")
                if receipt_path.is_file():
                    return load_receipt(repo_root, lifecycle_id, item["transitionId"])
    expected = _expected_transition(prior)
    if stage != expected:
        raise LifecycleOrchestratorError(f"TRANSITION_OUT_OF_ORDER:{stage}:{expected}")
    sequence = len(prior.get("history", [])) + 1 if prior else 1
    transition_id = f"{sequence:03d}-{stage}-{digest({'lifecycleId': lifecycle_id, 'stage': stage, 'requestDigest': request_digest})[:12]}"
    mutable = copy.deepcopy(prior) if prior else {
        "schema": SCHEMA,
        "lifecycleId": lifecycle_id,
        "createdAt": _utc_now(),
        "currentStage": None,
        "lifecycleState": "IN_PROGRESS",
        "lifecycleStateEvidence": {
            "state": "IN_PROGRESS",
            "statusIsAuthority": False,
            "statusMayAuthorizeMutation": False,
            "blockerCodes": [],
        },
        "history": [],
        "blockers": [],
    }
    if stage == "DISCOVER":
        mutable["expectedHead"] = expected_head
        mutable["workEntryRequestDigest"] = digest(payload.get("workEntryRequest"))
    mutable["transitionHead"] = current_head
    try:
        result = _execute_stage(repo_root, stage, mutable, payload)
    except Exception as exc:
        result = {"status": "FAIL", "blockers": [str(exc)], "errorType": type(exc).__name__}
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "transitionId": transition_id,
        "lifecycleId": lifecycle_id,
        "transition": stage,
        "requestDigest": request_digest,
        "repoHead": current_head,
        "createdAt": _utc_now(),
        "result": result,
        "receiptDigest": digest({"lifecycleId": lifecycle_id, "transition": stage, "requestDigest": request_digest, "repoHead": current_head, "result": result}),
    }
    receipt_path = _save_receipt(repo_root, lifecycle_id, receipt)
    history_item = {
        "transitionId": transition_id,
        "transition": stage,
        "requestDigest": request_digest,
        "receiptPath": str(receipt_path.relative_to(repo_root)).replace("\\", "/"),
        "receiptDigest": receipt["receiptDigest"],
        "status": result.get("status"),
        "repoHead": current_head,
    }
    mutable["history"].append(history_item)
    mutable["updatedAt"] = _utc_now()
    mutable["lastReceipt"] = history_item
    if result.get("status") == "PASS":
        mutable["currentStage"] = stage
        mutable.pop("blockedAt", None)
        mutable["blockers"] = []
        mutable["lifecycleState"] = "CLOSED" if stage == "CLOSE" else "IN_PROGRESS"
        mutable["lifecycleStateEvidence"] = {
            "state": "DONE" if stage == "CLOSE" else "IN_PROGRESS",
            "statusIsAuthority": False,
            "statusMayAuthorizeMutation": False,
            "blockerCodes": [],
        }
        if stage == "DISCOVER":
            mutable["discovery"] = result
            mutable["workEntryRequest"] = copy.deepcopy(payload["workEntryRequest"])
            mutable["authorities"] = result.get("authorities", {})
        elif stage == "ASSESS_RESOLVE":
            mutable["assessment"] = result
        elif stage == "REGISTER_TARGET":
            mutable["registrationRequest"] = result["registrationRequest"]
            mutable["registrationPlan"] = result["registrationPlan"]
            mutable["currentTruth"] = result["currentTruth"]
            mutable["authorityMesh"] = result["authorityMesh"]
        elif stage == "AUTHORIZATION":
            mutable["authorizationResult"] = result
        elif stage == "APPLY":
            mutable["applyResult"] = result
        elif stage == "DERIVE":
            mutable["derivation"] = result
        elif stage == "RECONCILE":
            mutable["reconciliation"] = result
        elif stage == "RUNTIME_VERIFY":
            mutable["runtimeVerification"] = result
        elif stage == "VISUAL_CERTIFY":
            mutable["visualCertification"] = result
        elif stage == "CHANGE_ASSURANCE":
            mutable["changeAssurance"] = result
        elif stage == "CLOSE":
            mutable["closure"] = result
            mutable["lifecycleStateEvidence"] = {"state": "DONE", "statusIsAuthority": False, "statusMayAuthorizeMutation": False, "blockerCodes": []}
    else:
        mutable["blockedAt"] = stage
        mutable["lifecycleState"] = "BLOCKED"
        mutable["blockers"] = list(result.get("blockers") or ["TRANSITION_FAILED"])
        mutable["lifecycleStateEvidence"] = {
            "state": "BLOCKED",
            "statusIsAuthority": False,
            "statusMayAuthorizeMutation": False,
            "blockerCodes": mutable["blockers"],
        }
    _atomic_json(_lifecycle_path(repo_root, lifecycle_id), mutable)
    return receipt


def inspect_lifecycle(repo_root: Path, lifecycle_id: str | None = None) -> dict[str, Any]:
    """Read lifecycle state and receipts without creating or updating files."""
    if lifecycle_id is not None:
        safe_id = _safe_lifecycle_id(lifecycle_id)
        record = _load_lifecycle(repo_root, safe_id)
        if record is None:
            return {
                "schema": "prisma.visual.lifecycle-inspection.v1",
                "status": "NOT_STARTED",
                "lifecycleId": safe_id,
                "currentStage": None,
                "nextTransition": "DISCOVER",
                "blockers": [],
                "receipts": [],
            }
        return {
            "schema": "prisma.visual.lifecycle-inspection.v1",
            "status": record.get("lifecycleState", "IN_PROGRESS"),
            "lifecycleId": safe_id,
            "currentStage": record.get("currentStage"),
            "nextTransition": _expected_transition(record),
            "target": _runtime_target(record) if record.get("registrationPlan") else (record.get("discovery") or {}).get("target"),
            "blockers": record.get("blockers", []),
            "authorities": record.get("authorities") or (record.get("discovery") or {}).get("authorities") or {},
            "certification": record.get("visualCertification"),
            "receipt": record.get("closure"),
            "rollback": record.get("rollback"),
            "supersession": record.get("supersession"),
            "history": record.get("history", []),
            "receiptChecks": [
                {
                    "transitionId": item["transitionId"],
                    "transition": item["transition"],
                    "receiptDigest": _verify_receipt(load_receipt(repo_root, safe_id, item["transitionId"]))["receiptDigest"],
                    "integrity": "VERIFIED",
                }
                for item in record.get("history", [])
            ],
        }
    base = repo_root / LIFECYCLES_ROOT
    ids = sorted(path.stem for path in base.glob("vlo-*.json")) if base.is_dir() else []
    return {
        "schema": "prisma.visual.lifecycle-inspection.v1",
        "status": "PASS",
        "lifecycles": [inspect_lifecycle(repo_root, item) for item in ids],
        "nextTransition": "DISCOVER" if not ids else None,
    }


def load_receipt(repo_root: Path, lifecycle_id: str, transition_id: str) -> dict[str, Any]:
    safe_id = _safe_lifecycle_id(lifecycle_id)
    if not isinstance(transition_id, str) or not re.fullmatch(r"[0-9]{3}-[A-Z_]+-[0-9a-f]{12}", transition_id):
        raise LifecycleOrchestratorError("TRANSITION_RECEIPT_ID_INVALID")
    path = _safe_local_path(repo_root, RECEIPTS_ROOT / safe_id / f"{transition_id}.json")
    receipt = _load_json(path, "TRANSITION_RECEIPT")
    if receipt.get("lifecycleId") != safe_id or receipt.get("transitionId") != transition_id:
        raise LifecycleOrchestratorError("TRANSITION_RECEIPT_IDENTITY_INVALID")
    return _verify_receipt(receipt)


def diagnose(repo_root: Path, request: dict[str, Any] | None = None, lifecycle_id: str | None = None) -> dict[str, Any]:
    """Read-only diagnostic for authority files, the optional exact request, and lifecycle state."""
    checks: list[dict[str, Any]] = []
    head = None
    try:
        head = _git_head(repo_root)
        checks.append({"id": "repo-head", "status": "PASS", "evidence": head})
    except Exception as exc:
        checks.append({"id": "repo-head", "status": "FAIL", "evidence": str(exc)})
    missing = [entry for entry in _authority_refs(repo_root).values() if not entry["present"]]
    checks.append({"id": "canonical-authority-files", "status": "PASS" if not missing else "BLOCKED", "missing": missing})
    try:
        gate_path = repo_root / "PRISMA Factory Ledger" / "tools" / "verify_prisma_anti_rework_gate.py"
        spec = importlib.util.spec_from_file_location("prisma_factory_anti_rework_gate_doctor", gate_path)
        if spec is None or spec.loader is None:
            raise LifecycleOrchestratorError("FACTORY_LEDGER_GATE_UNAVAILABLE")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        live = module.validate_live(module.read_authority(repo_root))
        checks.append({
            "id": "factory-ledger-authority",
            "status": "PASS" if live.get("result") == "PASS_PRISMA_ANTI_REWORK_AUTHORITY" else "FAIL",
            "result": live.get("result"),
            "errors": live.get("errors", []),
            "validationDigest": live.get("validationDigest"),
            "mutationGate": "PENDING_FRESH_TASK_EXACT_AUTHORITY_MESH_AND_LAYER_MAP",
        })
    except Exception as exc:
        checks.append({"id": "factory-ledger-authority", "status": "FAIL", "evidence": str(exc)})
    if lifecycle_id is not None:
        try:
            state = inspect_lifecycle(repo_root, lifecycle_id)
            checks.append({"id": "lifecycle-state", "status": "PASS" if state.get("status") not in {"BLOCKED", "FAILED"} else "BLOCKED", "state": state})
        except Exception as exc:
            checks.append({"id": "lifecycle-state", "status": "FAIL", "evidence": str(exc)})
    if request is not None:
        work_request = request.get("workEntryRequest") if isinstance(request, dict) else None
        if not isinstance(work_request, dict):
            checks.append({"id": "work-entry", "status": "BLOCKED", "blockers": ["WORK_ENTRY_REQUEST_REQUIRED"]})
        else:
            try:
                decision = _discover(repo_root, work_request)
                checks.append({
                    "id": "work-entry",
                    "status": "PASS" if decision.get("status") == "PASS" else "BLOCKED",
                    "decision": decision,
                })
            except Exception as exc:
                checks.append({"id": "work-entry", "status": "FAIL", "evidence": str(exc)})
        authority = request.get("authority") if isinstance(request, dict) else None
        if isinstance(authority, dict) and head:
            try:
                mesh = _verified_authority_bundle(repo_root, authority, head)
                gate = _factory_mutation_gate(repo_root, head, mesh)
                checks.append({
                    "id": "mutation-authorization",
                    "status": "PASS" if gate.get("result") == "PASS_ANTI_REWORK_GATE" else "BLOCKED",
                    "authorityMesh": mesh,
                    "factoryLedgerDecisionDigest": gate.get("decisionDigest"),
                    "result": gate.get("result"),
                    "errors": gate.get("errors", []),
                })
            except Exception as exc:
                checks.append({"id": "mutation-authorization", "status": "BLOCKED", "evidence": str(exc)})
        else:
            checks.append({
                "id": "mutation-authorization",
                "status": "WARN",
                "blockers": ["FRESH_TASK_EXACT_AUTHORITY_MESH_AND_LAYER_MAP_REQUIRED"],
            })
    statuses = {item["status"] for item in checks}
    overall = "FAIL" if "FAIL" in statuses else "BLOCKED" if "BLOCKED" in statuses else "WARN" if request is None or "WARN" in statuses else "PASS"
    return {
        "schema": "prisma.visual.lifecycle-doctor.v1",
        "status": overall,
        "readOnly": True,
        "repoHead": head,
        "checks": checks,
        "nextAction": (
            "Resolve the blocker details above before advancing."
            if overall in {"BLOCKED", "FAIL"}
            else "Provide one exact Work Entry request and fresh authority evidence."
            if overall == "WARN"
            else "Advance DISCOVER after reviewing the exact target receipt."
        ),
    }


def rollback_registration(repo_root: Path, lifecycle_id: str) -> dict[str, Any]:
    safe_id = _safe_lifecycle_id(lifecycle_id)
    record = _load_lifecycle(repo_root, safe_id)
    if record is None:
        raise LifecycleOrchestratorError("LIFECYCLE_NOT_FOUND")
    if record.get("currentStage") != "APPLY":
        raise LifecycleOrchestratorError("ROLLBACK_REGISTRATION_ONLY_ALLOWED_IMMEDIATELY_AFTER_APPLY")
    registration = (record.get("applyResult") or {}).get("registrationResult") or {}
    request_id = registration.get("requestId")
    if not isinstance(request_id, str):
        raise LifecycleOrchestratorError("APPLIED_CANONICAL_REGISTRATION_REQUIRED")
    try:
        result = engine.rollback(request_id, repo_root)
    except Exception as exc:
        failure = {"status": "BLOCKED", "requestId": request_id, "blockers": [str(exc)]}
        receipt = _maintenance_receipt(repo_root, record, "ROLLBACK", {"lifecycleId": safe_id, "requestId": request_id}, failure)
        record["lifecycleState"] = "BLOCKED"
        record["blockers"] = failure["blockers"]
        record["blockedAt"] = "APPLY"
        record["lifecycleStateEvidence"] = {
            "state": "BLOCKED",
            "statusIsAuthority": False,
            "statusMayAuthorizeMutation": False,
            "blockerCodes": record["blockers"],
        }
        _atomic_json(_lifecycle_path(repo_root, safe_id), record)
        return receipt
    rollback_result = {
        "status": result.get("status"),
        "requestId": request_id,
        "restoredPaths": result.get("restoredPaths", []),
        "createdAt": _utc_now(),
    }
    receipt = _maintenance_receipt(repo_root, record, "ROLLBACK", {"lifecycleId": safe_id, "requestId": request_id}, rollback_result)
    record["lifecycleState"] = "BLOCKED"
    record["blockers"] = ["CANONICAL_REGISTRATION_ROLLED_BACK"]
    record["blockedAt"] = "APPLY"
    record["lifecycleStateEvidence"] = {
        "state": "BLOCKED",
        "statusIsAuthority": False,
        "statusMayAuthorizeMutation": False,
        "blockerCodes": record["blockers"],
    }
    lifecycle_state.assert_transition(
        {"state": "IN_PROGRESS", "statusIsAuthority": False, "statusMayAuthorizeMutation": False, "blockerCodes": []},
        record["lifecycleStateEvidence"],
    )
    _atomic_json(_lifecycle_path(repo_root, safe_id), record)
    return receipt


def supersede_lifecycle(repo_root: Path, lifecycle_id: str, *, superseded_by: str, decision_ref: str) -> dict[str, Any]:
    safe_id = _safe_lifecycle_id(lifecycle_id)
    successor = _safe_lifecycle_id(superseded_by)
    if successor == safe_id:
        raise LifecycleOrchestratorError("SUPERSEDED_BY_MUST_BE_DIFFERENT_LIFECYCLE")
    if not isinstance(decision_ref, str) or not decision_ref.strip():
        raise LifecycleOrchestratorError("SUPERSESSION_DECISION_REF_REQUIRED")
    record = _load_lifecycle(repo_root, safe_id)
    if record is None:
        raise LifecycleOrchestratorError("LIFECYCLE_NOT_FOUND")
    if record.get("lifecycleState") == "SUPERSEDED":
        current = record.get("supersession") or {}
        if current.get("supersededBy") == successor and current.get("decisionRef") == decision_ref.strip() and current.get("receiptId"):
            return load_receipt(repo_root, safe_id, current["receiptId"])
        raise LifecycleOrchestratorError("LIFECYCLE_ALREADY_SUPERSEDED")
    before = record.get("lifecycleStateEvidence")
    after = {
        "state": "SUPERSEDED",
        "statusIsAuthority": False,
        "statusMayAuthorizeMutation": False,
        "blockerCodes": [],
    }
    lifecycle_state.assert_transition(before, after)
    supersession = {"status": "PASS", "supersededBy": successor, "decisionRef": decision_ref.strip()}
    receipt = _maintenance_receipt(
        repo_root,
        record,
        "SUPERSEDE",
        {"lifecycleId": safe_id, "supersededBy": successor, "decisionRef": decision_ref.strip()},
        supersession,
    )
    record["lifecycleState"] = "SUPERSEDED"
    record["lifecycleStateEvidence"] = after
    _atomic_json(_lifecycle_path(repo_root, safe_id), record)
    return receipt
