from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .policy import allocate_id, assert_no_inferred_id
from .authority_adapters import AuthorityBindingError, validate_exact_binding

CAPABILITY_ID = "visual.canonical_promotion_integration_v1"
SCHEMA = "prisma.visual.canonical-promotion-request.v1"
PLAN_SCHEMA = "prisma.visual.canonical-promotion-plan.v1"
RESULT_SCHEMA = "prisma.visual.canonical-promotion-result.v1"
EVIDENCE_SCHEMA = "prisma.visual.canonical-promotion-evidence.v1"
JOURNAL_SCHEMA = "prisma.visual.canonical-promotion-journal.v1"

ALLOWED_CANONICAL_PATHS = {
    "prisma-html/authority/rifat/identity/registries/recipe.registry.json",
    "prisma-html/authority/rifat/identity/registries/element-bindings.registry.json",
}
RESULTS_ROOT = "prisma-html/governance/visual-promotion/canonical-registration/receipts"
TRANSACTIONS_ROOT = "prisma-html/governance/visual-promotion/canonical-registration/transactions"


class CanonicalRegistrationError(RuntimeError):
    pass


class CollisionError(CanonicalRegistrationError):
    pass


class SemanticCollisionError(CollisionError):
    code = "SEMANTIC_COLLISION"


class BindingCollisionError(CollisionError):
    code = "BINDING_COLLISION"


class IdCollisionError(CollisionError):
    code = "ID_COLLISION"


class LayerCollisionError(CollisionError):
    code = "LAYER_COLLISION"


class ProjectionConflictError(CollisionError):
    code = "PROJECTION_CONFLICT"


class StaleHeadError(CanonicalRegistrationError):
    pass


class SourceDriftError(CanonicalRegistrationError):
    pass


class UnsafeMutationError(CanonicalRegistrationError):
    pass


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CanonicalRegistrationError(f"JSON_INVALID:{path}") from exc


def _atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".canonical-registration-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _acquire_lock(lock_dir: Path) -> None:
    lock_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_dir.mkdir()
    except FileExistsError as exc:
        raise UnsafeMutationError("CONCURRENT_TRANSACTION_LOCK_EXISTS") from exc
    _atomic_write_json(lock_dir / "LOCK.json", {"schema": "prisma.visual.transaction-lock.v1", "locked": True})


def _release_lock(lock_dir: Path) -> None:
    lock_file = lock_dir / "LOCK.json"
    if lock_file.exists():
        lock_file.unlink()
    if lock_dir.exists():
        lock_dir.rmdir()


def current_repo_head(repo_root: Path) -> str:
    env_head = os.environ.get("GITHUB_SHA")
    if isinstance(env_head, str) and len(env_head) == 40:
        return env_head
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception as exc:
        raise StaleHeadError("CURRENT_REPO_HEAD_UNAVAILABLE") from exc
    value = proc.stdout.strip()
    if len(value) != 40:
        raise StaleHeadError("CURRENT_REPO_HEAD_INVALID")
    return value


def _registry_ids(registry: dict[str, Any], key: str) -> set[str]:
    out: set[str] = set()
    for item in registry.get(key, []):
        if not isinstance(item, dict):
            continue
        for field in ("recipeId", "bindingId", "targetId"):
            value = item.get(field)
            if isinstance(value, str):
                out.add(value)
    return out


def _validate_request(request: dict[str, Any]) -> None:
    if request.get("schema") != SCHEMA:
        raise CanonicalRegistrationError("REQUEST_SCHEMA_INVALID")
    for field in (
        "requestId",
        "target",
        "expectedCurrentHead",
        "currentTruth",
        "source",
        "decision",
        "authorization",
    ):
        if not request.get(field):
            raise CanonicalRegistrationError(f"REQUEST_FIELD_MISSING:{field}")

    target = request["target"]
    if not target.get("targetId") or not target.get("surfaceKey"):
        raise CanonicalRegistrationError("EXACT_TARGET_IDENTITY_REQUIRED")

    truth = request["currentTruth"]
    if truth.get("schema") != "prisma.visual.current-truth-snapshot.v1":
        raise CanonicalRegistrationError("CURRENT_TRUTH_SNAPSHOT_REQUIRED")
    required_truth = {
        "repoHead",
        "targetIndexDigest",
        "identityDigest",
        "rifatDigest",
        "ndcDigest",
        "projectionDigest",
        "authorityMeshDigest",
        "layerMapDigest",
        "targetEvidenceDigest",
    }
    if not required_truth.issubset(truth):
        raise CanonicalRegistrationError("CURRENT_TRUTH_SNAPSHOT_INCOMPLETE")
    if truth.get("repoHead") != request["expectedCurrentHead"]:
        raise StaleHeadError("CURRENT_TRUTH_HEAD_MISMATCH")

    source = request["source"]
    if not isinstance(source.get("digest"), str) or len(source["digest"]) != 64:
        raise CanonicalRegistrationError("SOURCE_DIGEST_REQUIRED")
    if not source.get("path"):
        raise CanonicalRegistrationError("SOURCE_PATH_REQUIRED")

    decision = request["decision"]
    if decision.get("semanticAction") not in {"REUSE_EXISTING", "CREATE_NEW"}:
        raise CanonicalRegistrationError("SEMANTIC_ADJUDICATION_REQUIRED")
    if decision.get("semanticAction") == "CREATE_NEW":
        if not decision.get("semanticDecisionId") or not decision.get("approvalEvidenceRefs"):
            raise CanonicalRegistrationError("EXPLICIT_SEMANTIC_APPROVAL_REQUIRED")
        authority = decision.get("semanticAuthority") or {}
        if authority.get("authorityDomain") != "ndc":
            raise CanonicalRegistrationError("NEW_SEMANTIC_MUST_REFERENCE_NDC_AUTHORITY")
        if authority.get("writerKind") != "NDC_CURATION":
            raise CanonicalRegistrationError("NEW_SEMANTIC_WRITER_MUST_BE_NDC_CURATION")
        if not authority.get("canonicalMeaningId") or not authority.get("decisionRef"):
            raise CanonicalRegistrationError("NDC_ADJUDICATION_REFERENCE_REQUIRED")

    auth = request["authorization"]
    if auth.get("canonicalRegistrationAuthorized") is not True:
        raise CanonicalRegistrationError("CANONICAL_REGISTRATION_NOT_AUTHORIZED")
    if auth.get("automaticSemanticInference") is not False:
        raise CanonicalRegistrationError("AUTOMATIC_SEMANTIC_INFERENCE_FORBIDDEN")
    if auth.get("automaticApplicationSource") is not False:
        raise CanonicalRegistrationError("AUTOMATIC_APPLICATION_SOURCE_FORBIDDEN")
    assert_no_inferred_id(decision.get("idInputs") or {})


def _validate_source_pin(request: dict[str, Any], repo_root: Path) -> None:
    source_path = repo_root / request["source"]["path"]
    root = repo_root.resolve()
    resolved = source_path.resolve()
    if resolved != root and root not in resolved.parents:
        raise UnsafeMutationError("SOURCE_PATH_ESCAPE")
    if not resolved.is_file():
        raise CanonicalRegistrationError("SOURCE_FILE_NOT_FOUND")
    actual = file_sha256(resolved)
    if actual != request["source"]["digest"]:
        raise SourceDriftError("SOURCE_DRIFT")


def _find_target_conflicts(bindings: dict[str, Any], target_id: str) -> list[dict[str, Any]]:
    return [
        target
        for entry in bindings.get("bindings", [])
        if isinstance(entry, dict)
        for target in entry.get("targets", [])
        if isinstance(target, dict) and target.get("targetId") == target_id
    ]


def build_plan(request: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    _validate_request(request)
    _validate_source_pin(request, repo_root)

    decision = request["decision"]
    target = request["target"]
    recipe_action = decision.get("recipeAction") or {}
    binding_action = decision.get("bindingAction") or {}
    layer_action = decision.get("layerAction") or {}

    if not layer_action.get("applicationLayerId") or not layer_action.get("policy"):
        raise CanonicalRegistrationError("APPLICATION_LAYER_POLICY_REQUIRED")
    if layer_action.get("policy") not in {"EXACT_TARGET_ONLY", "BOUNDED_EXACT_TARGET_WAVE"}:
        raise CanonicalRegistrationError("APPLICATION_POLICY_INVALID")
    if layer_action.get("writerKind") not in {"CANONICAL_REGISTRATION", "GVAE"}:
        raise CanonicalRegistrationError("WRITER_KIND_REQUIRED")
    try:
        validate_exact_binding(repo_root, binding_action.get("exactBinding"), target["targetId"])
    except AuthorityBindingError as exc:
        raise CanonicalRegistrationError(str(exc)) from exc

    recipe_path = repo_root / "prisma-html/authority/rifat/identity/registries/recipe.registry.json"
    binding_path = repo_root / "prisma-html/authority/rifat/identity/registries/element-bindings.registry.json"
    recipes = _load(recipe_path)
    bindings = _load(binding_path)

    if recipe_action.get("action") == "CREATE_NEW":
        allocation = allocate_id(
            "recipe",
            recipe_action["semanticKey"],
            _registry_ids(recipes, "recipes"),
            requested_id=recipe_action.get("recipeId"),
        )
        if allocation.action != "CREATE_NEW":
            raise IdCollisionError("RECIPE_ID_REUSE_REQUIRES_EXPLICIT_ACTION")
        recipe_id = allocation.id
    elif recipe_action.get("action") == "REUSE_EXISTING":
        recipe_id = recipe_action.get("recipeId")
        if not recipe_id or not any(
            item.get("recipeId") == recipe_id for item in recipes.get("recipes", [])
        ):
            raise CanonicalRegistrationError("RECIPE_REUSE_NOT_FOUND")
    else:
        raise CanonicalRegistrationError("RECIPE_ACTION_INVALID")

    if binding_action.get("action") == "CREATE_NEW":
        allocation = allocate_id(
            "binding",
            binding_action["semanticKey"],
            _registry_ids(bindings, "bindings"),
            requested_id=binding_action.get("bindingId"),
        )
        if allocation.action != "CREATE_NEW":
            raise IdCollisionError("BINDING_ID_REUSE_REQUIRES_EXPLICIT_ACTION")
        binding_id = allocation.id
    elif binding_action.get("action") == "REUSE_EXISTING":
        binding_id = binding_action.get("bindingId")
        if not binding_id or not any(
            item.get("bindingId") == binding_id for item in bindings.get("bindings", [])
        ):
            raise CanonicalRegistrationError("BINDING_REUSE_NOT_FOUND")
    else:
        raise CanonicalRegistrationError("BINDING_ACTION_INVALID")

    requested_target = (binding_action["exactBinding"].get("targets") or [None])[0]
    existing_targets = _find_target_conflicts(bindings, target["targetId"])
    if existing_targets:
        if len(existing_targets) > 1:
            raise BindingCollisionError("MULTIPLE_EXISTING_TARGET_BINDINGS")
        if existing_targets[0] != requested_target:
            raise BindingCollisionError("EXACT_TARGET_BINDING_COLLISION")
        return {
            "schema": PLAN_SCHEMA,
            "capabilityId": CAPABILITY_ID,
            "requestId": request["requestId"],
            "targetId": target["targetId"],
            "surfaceKey": target["surfaceKey"],
            "semanticAction": decision["semanticAction"],
            "semanticDecisionId": decision.get("semanticDecisionId"),
            "ids": {"recipeId": recipe_id, "bindingId": binding_id},
            "bindingAction": binding_action["action"],
            "recipeAction": recipe_action["action"],
            "layerAction": layer_action,
            "projectionAction": decision.get("projectionAction", {"mode": "DEFERRED_DERIVATION", "authorized": False}),
            "mutations": [],
            "preconditions": {
                "expectedCurrentHead": request["expectedCurrentHead"],
                "currentTruthDigest": sha256_json(request["currentTruth"]),
                "sourceDigest": request["source"]["digest"],
                "registryDigests": {
                    "recipeRegistry": sha256_json(recipes),
                    "bindingRegistry": sha256_json(bindings),
                },
            },
            "status": "NO_OP_IDEMPOTENT",
        }

    mutations: list[dict[str, Any]] = []
    if binding_action["action"] == "CREATE_NEW":
        entry = copy.deepcopy(binding_action["registryEntry"])
        entry["bindingId"] = binding_id
        mutations.append({
            "path": "prisma-html/authority/rifat/identity/registries/element-bindings.registry.json",
            "operation": "append_binding",
            "value": entry,
        })
    if recipe_action["action"] == "CREATE_NEW":
        entry = copy.deepcopy(recipe_action["registryEntry"])
        entry["recipeId"] = recipe_id
        mutations.append({
            "path": "prisma-html/authority/rifat/identity/registries/recipe.registry.json",
            "operation": "append_recipe",
            "value": entry,
        })

    for mutation in mutations:
        if mutation["path"] not in ALLOWED_CANONICAL_PATHS:
            raise UnsafeMutationError("PATH_NOT_GOVERNED")

    return {
        "schema": PLAN_SCHEMA,
        "capabilityId": CAPABILITY_ID,
        "requestId": request["requestId"],
        "targetId": target["targetId"],
        "surfaceKey": target["surfaceKey"],
        "semanticAction": decision["semanticAction"],
        "semanticDecisionId": decision.get("semanticDecisionId"),
        "ids": {"recipeId": recipe_id, "bindingId": binding_id},
        "bindingAction": binding_action["action"],
        "recipeAction": recipe_action["action"],
        "layerAction": layer_action,
        "projectionAction": decision.get("projectionAction", {"mode": "DEFERRED_DERIVATION", "authorized": False}),
        "mutations": mutations,
        "preconditions": {
            "expectedCurrentHead": request["expectedCurrentHead"],
            "currentTruthDigest": sha256_json(request["currentTruth"]),
            "sourceDigest": request["source"]["digest"],
            "registryDigests": {
                "recipeRegistry": sha256_json(recipes),
                "bindingRegistry": sha256_json(bindings),
            },
        },
        "status": "APPLY",
    }


def _apply(repo_root: Path, mutation: dict[str, Any]) -> tuple[Path, str, str, Any]:
    rel = mutation["path"]
    if rel not in ALLOWED_CANONICAL_PATHS:
        raise UnsafeMutationError("PATH_NOT_GOVERNED")
    path = repo_root / rel
    before = _load(path)
    before_sha = sha256_json(before)
    after = copy.deepcopy(before)
    value = mutation["value"]

    if mutation["operation"] == "append_recipe":
        if any(item.get("recipeId") == value.get("recipeId") for item in after.get("recipes", [])):
            raise IdCollisionError("RECIPE_ID_COLLISION")
        after["recipes"] = [*after.get("recipes", []), value]
        after["recipeCount"] = len(after["recipes"])
    elif mutation["operation"] == "append_binding":
        if any(item.get("bindingId") == value.get("bindingId") for item in after.get("bindings", [])):
            raise IdCollisionError("BINDING_ID_COLLISION")
        after["bindings"] = [*after.get("bindings", []), value]
    else:
        raise UnsafeMutationError("UNKNOWN_MUTATION_OPERATION")

    after_sha = sha256_json(after)
    _atomic_write_json(path, after)
    return path, before_sha, after_sha, before


def _evidence(
    request: dict[str, Any],
    plan: dict[str, Any],
    status: str,
    applied: list[tuple[Path, str, str, Any]],
    errors: list[str],
) -> dict[str, Any]:
    return {
        "schema": EVIDENCE_SCHEMA,
        "requestId": request["requestId"],
        "requestDigest": sha256_json(request),
        "currentTruthDigest": plan["preconditions"]["currentTruthDigest"],
        "sourceDigest": plan["preconditions"]["sourceDigest"],
        "preState": [
            {"path": str(path.relative_to(request["_repoRoot"])).replace("\\", "/"), "sha256": before_sha}
            for path, before_sha, _, _ in applied
        ],
        "postState": [
            {"path": str(path.relative_to(request["_repoRoot"])).replace("\\", "/"), "sha256": after_sha}
            for path, _, after_sha, _ in applied
        ],
        "ids": plan["ids"],
        "mutations": plan["mutations"],
        "status": status,
        "errors": errors,
    }


def register(request: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    request = copy.deepcopy(request)
    request["_repoRoot"] = str(repo_root.resolve())
    plan = build_plan(request, repo_root)

    receipt_path = repo_root / RESULTS_ROOT / f"{request['requestId']}.json"
    journal_dir = repo_root / TRANSACTIONS_ROOT / request["requestId"]
    journal_path = journal_dir / "journal.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)

    request_digest = sha256_json({k: v for k, v in request.items() if k != "_repoRoot"})
    if receipt_path.exists():
        prior = _load(receipt_path)
        if prior.get("requestDigest") == request_digest and prior.get("result"):
            return prior["result"]

    if plan["status"] == "NO_OP_IDEMPOTENT":
        evidence = _evidence(request, plan, "NO_OP_IDEMPOTENT", [], [])
        evidence["requestDigest"] = request_digest
        result = {
            "schema": RESULT_SCHEMA,
            "capabilityId": CAPABILITY_ID,
            "requestId": request["requestId"],
            "targetId": plan["targetId"],
            "status": "NO_OP_IDEMPOTENT",
            "ids": plan["ids"],
            "evidenceDigest": sha256_json(evidence),
        }
        evidence["result"] = result
        _atomic_write_json(receipt_path, evidence)
        return result

    lock_dir = repo_root / TRANSACTIONS_ROOT / f".{request['requestId']}.lock"
    _acquire_lock(lock_dir)
    try:
        current_head = current_repo_head(repo_root)
        if current_head != request["expectedCurrentHead"]:
            raise StaleHeadError(f"CURRENT_HEAD_CHANGED:{current_head}:{request['expectedCurrentHead']}")

        prestate: dict[str, Any] = {}
        for mutation in plan["mutations"]:
            rel = mutation["path"]
            path = repo_root / rel
            prestate[rel] = _load(path)

        journal = {
            "schema": JOURNAL_SCHEMA,
            "requestId": request["requestId"],
            "requestDigest": request_digest,
            "status": "PREPARED",
            "expectedCurrentHead": request["expectedCurrentHead"],
            "currentHeadAtPrepare": current_head,
            "currentTruthDigest": plan["preconditions"]["currentTruthDigest"],
            "preStateValues": prestate,
            "preStateDigests": {path: sha256_json(value) for path, value in prestate.items()},
            "mutations": plan["mutations"],
        }
        _atomic_write_json(journal_path, journal)

        applied: list[tuple[Path, str, str, Any]] = []
        try:
            for mutation in plan["mutations"]:
                rel = mutation["path"]
                path = repo_root / rel
                current = sha256_json(_load(path))
                expected = (
                    plan["preconditions"]["registryDigests"]["recipeRegistry"]
                    if rel.endswith("recipe.registry.json")
                    else plan["preconditions"]["registryDigests"]["bindingRegistry"]
                )
                if current != expected:
                    raise StaleHeadError("REGISTRY_PRECONDITION_CHANGED:" + rel)
                applied.append(_apply(repo_root, mutation))
        except Exception as exc:
            for rel, before_value in prestate.items():
                path = repo_root / rel
                current = sha256_json(_load(path))
                completed = next(
                    (row[2] for row in applied if str(row[0].relative_to(repo_root)).replace("\\", "/") == rel),
                    None,
                )
                if completed is not None and current == completed:
                    _atomic_write_json(path, before_value)
            journal["status"] = "ROLLED_BACK_AFTER_FAILURE"
            journal["error"] = str(exc)
            journal["rollbackVerified"] = True
            _atomic_write_json(journal_path, journal)
            evidence = _evidence(request, plan, "FAILED", applied, [str(exc)])
            evidence["requestDigest"] = request_digest
            evidence["journalPath"] = str(journal_path.relative_to(repo_root)).replace("\\", "/")
            _atomic_write_json(receipt_path, evidence)
            raise

        journal["status"] = "APPLIED"
        journal["postStateDigests"] = {
            str(path.relative_to(repo_root)).replace("\\", "/"): after_sha
            for path, _, after_sha, _ in applied
        }
        _atomic_write_json(journal_path, journal)

        evidence = _evidence(request, plan, "APPLIED", applied, [])
        evidence["requestDigest"] = request_digest
        evidence["journalPath"] = str(journal_path.relative_to(repo_root)).replace("\\", "/")
        evidence["preStateValues"] = {
            str(path.relative_to(repo_root)).replace("\\", "/"): before
            for path, _, _, before in applied
        }
        result = {
            "schema": RESULT_SCHEMA,
            "capabilityId": CAPABILITY_ID,
            "requestId": request["requestId"],
            "targetId": plan["targetId"],
            "status": "APPLIED",
            "ids": plan["ids"],
            "journalPath": evidence["journalPath"],
            "evidenceDigest": sha256_json(evidence),
        }
        evidence["result"] = result
        _atomic_write_json(receipt_path, evidence)
        return result
    finally:
        _release_lock(lock_dir)


def rollback(request_id: str, repo_root: Path) -> dict[str, Any]:
    receipt_path = repo_root / RESULTS_ROOT / f"{request_id}.json"
    if not receipt_path.exists():
        raise CanonicalRegistrationError("RECEIPT_NOT_FOUND")
    evidence = _load(receipt_path)
    if evidence.get("status") != "APPLIED":
        raise CanonicalRegistrationError("ROLLBACK_REQUIRES_APPLIED_TRANSACTION")

    restored: list[str] = []
    for row in evidence.get("postState", []):
        rel = row["path"]
        path = repo_root / rel
        current = sha256_json(_load(path))
        if current != row["sha256"]:
            raise UnsafeMutationError("ROLLBACK_WOULD_OVERWRITE_NEWER_WORK:" + rel)
        prior_value = evidence.get("preStateValues", {}).get(rel)
        if prior_value is None:
            raise UnsafeMutationError("ROLLBACK_PRESTATE_VALUE_MISSING:" + rel)
        _atomic_write_json(path, prior_value)
        restored.append(rel)

    evidence["status"] = "ROLLED_BACK"
    evidence["rollback"] = {
        "restoredPaths": restored,
        "transactionScoped": True,
        "newerWorkProtection": True,
    }
    evidence["evidenceDigestAfterRollback"] = sha256_json(evidence)
    _atomic_write_json(receipt_path, evidence)

    journal_path = repo_root / evidence["journalPath"]
    journal = _load(journal_path)
    journal["status"] = "ROLLED_BACK"
    journal["restoredPaths"] = restored
    _atomic_write_json(journal_path, journal)

    return {
        "schema": RESULT_SCHEMA,
        "capabilityId": CAPABILITY_ID,
        "requestId": request_id,
        "status": "ROLLED_BACK",
        "restoredPaths": restored,
    }
