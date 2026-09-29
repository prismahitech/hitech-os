from __future__ import annotations
import copy, hashlib, json, os, tempfile
from pathlib import Path
from typing import Any
from .policy import allocate_id, assert_no_inferred_id

CAPABILITY_ID = "visual.canonical_promotion_integration_v1"
SCHEMA = "prisma.visual.canonical-promotion-request.v1"
RESULT_SCHEMA = "prisma.visual.canonical-promotion-result.v1"
EVIDENCE_SCHEMA = "prisma.visual.canonical-promotion-evidence.v1"
ALLOWED_CANONICAL_PATHS = {
    "prisma-html/authority/rifat/identity/registries/recipe.registry.json",
    "prisma-html/authority/rifat/identity/registries/element-bindings.registry.json",
}
RESULTS_ROOT = "prisma-html/governance/visual-promotion/canonical-registration/receipts"

class CanonicalRegistrationError(RuntimeError): pass
class CollisionError(CanonicalRegistrationError): pass
class StaleHeadError(CanonicalRegistrationError): pass
class UnsafeMutationError(CanonicalRegistrationError): pass

def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()

def _load(path: Path) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: raise CanonicalRegistrationError(f"JSON_INVALID:{path}") from exc

def _atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".canonical-registration-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def _registry_ids(registry: dict[str, Any], key: str) -> set[str]:
    out = set()
    for item in registry.get(key, []):
        if isinstance(item, dict):
            out.update(v for k,v in item.items() if k in {"recipeId","bindingId","targetId"} and isinstance(v,str))
    return out

def _validate_request(request: dict[str, Any]) -> None:
    if request.get("schema") != SCHEMA: raise CanonicalRegistrationError("REQUEST_SCHEMA_INVALID")
    for field in ("requestId","target","expectedCurrentHead","currentTruth","source","decision","authorization"):
        if not request.get(field): raise CanonicalRegistrationError(f"REQUEST_FIELD_MISSING:{field}")
    target = request["target"]
    if not target.get("targetId") or not target.get("surfaceKey"): raise CanonicalRegistrationError("EXACT_TARGET_IDENTITY_REQUIRED")
    truth = request["currentTruth"]
    if truth.get("schema") != "prisma.visual.current-truth-snapshot.v1": raise CanonicalRegistrationError("CURRENT_TRUTH_SNAPSHOT_REQUIRED")
    if truth.get("repoHead") != request["expectedCurrentHead"]: raise StaleHeadError("CURRENT_TRUTH_HEAD_MISMATCH")
    if not isinstance(request["source"].get("digest"),str) or len(request["source"]["digest"]) != 64: raise CanonicalRegistrationError("SOURCE_DIGEST_REQUIRED")
    if not request["source"].get("path"): raise CanonicalRegistrationError("SOURCE_PATH_REQUIRED")
    decision = request["decision"]
    if decision.get("semanticAction") not in {"REUSE_EXISTING","CREATE_NEW"}: raise CanonicalRegistrationError("SEMANTIC_ADJUDICATION_REQUIRED")
    if decision.get("semanticAction") == "CREATE_NEW" and (not decision.get("semanticDecisionId") or not decision.get("approvalEvidenceRefs")):
        raise CanonicalRegistrationError("EXPLICIT_SEMANTIC_APPROVAL_REQUIRED")
    auth = request["authorization"]
    if auth.get("canonicalRegistrationAuthorized") is not True: raise CanonicalRegistrationError("CANONICAL_REGISTRATION_NOT_AUTHORIZED")
    if auth.get("automaticSemanticInference") is not False: raise CanonicalRegistrationError("AUTOMATIC_SEMANTIC_INFERENCE_FORBIDDEN")
    if auth.get("automaticApplicationSource") is not False: raise CanonicalRegistrationError("AUTOMATIC_APPLICATION_SOURCE_FORBIDDEN")
    assert_no_inferred_id(decision.get("idInputs") or {})

def build_plan(request: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    _validate_request(request)
    source_path = repo_root / request["source"]["path"]
    if not source_path.is_file(): raise CanonicalRegistrationError("SOURCE_FILE_NOT_FOUND")
    actual_source = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if actual_source != request["source"]["digest"]: raise CanonicalRegistrationError("SOURCE_DRIFT")
    d, target = request["decision"], request["target"]
    recipe_action, binding_action, layer_action = d.get("recipeAction",{}), d.get("bindingAction",{}), d.get("layerAction",{})
    if not layer_action.get("applicationLayerId") or not layer_action.get("policy"): raise CanonicalRegistrationError("APPLICATION_LAYER_POLICY_REQUIRED")
    if not binding_action.get("exactBinding"): raise CanonicalRegistrationError("EXACT_BINDING_REQUIRED")
    recipe_path = repo_root / "prisma-html/authority/rifat/identity/registries/recipe.registry.json"
    binding_path = repo_root / "prisma-html/authority/rifat/identity/registries/element-bindings.registry.json"
    recipes, bindings = _load(recipe_path), _load(binding_path)
    if recipe_action.get("action") == "CREATE_NEW":
        recipe_id = allocate_id("recipe",recipe_action["semanticKey"],_registry_ids(recipes,"recipes"),requested_id=recipe_action.get("recipeId")).id
    elif recipe_action.get("action") == "REUSE_EXISTING":
        recipe_id = recipe_action.get("recipeId")
        if not recipe_id or not any(x.get("recipeId")==recipe_id for x in recipes.get("recipes",[])): raise CanonicalRegistrationError("RECIPE_REUSE_NOT_FOUND")
    else: raise CanonicalRegistrationError("RECIPE_ACTION_INVALID")
    if binding_action.get("action") == "CREATE_NEW":
        binding_id = allocate_id("binding",binding_action["semanticKey"],_registry_ids(bindings,"bindings"),requested_id=binding_action.get("bindingId")).id
    elif binding_action.get("action") == "REUSE_EXISTING":
        binding_id = binding_action.get("bindingId")
        if not binding_id or not any(x.get("bindingId")==binding_id for x in bindings.get("bindings",[])): raise CanonicalRegistrationError("BINDING_REUSE_NOT_FOUND")
    else: raise CanonicalRegistrationError("BINDING_ACTION_INVALID")
    collisions = [t for b in bindings.get("bindings",[]) for t in b.get("targets",[]) if t.get("targetId")==target["targetId"]]
    if collisions and collisions[0] != binding_action["exactBinding"]: raise CollisionError("EXACT_TARGET_BINDING_COLLISION")
    status = "NO_OP_IDEMPOTENT" if collisions else "APPLY"
    mutations=[]
    if status=="APPLY":
        if binding_action["action"]=="CREATE_NEW":
            entry=copy.deepcopy(binding_action["registryEntry"]); entry["bindingId"]=binding_id
            mutations.append({"path":str(binding_path.relative_to(repo_root)).replace("\\","/"),"operation":"append_binding","value":entry})
        if recipe_action["action"]=="CREATE_NEW":
            entry=copy.deepcopy(recipe_action["registryEntry"]); entry["recipeId"]=recipe_id
            mutations.append({"path":str(recipe_path.relative_to(repo_root)).replace("\\","/"),"operation":"append_recipe","value":entry})
    if any(m["path"] not in ALLOWED_CANONICAL_PATHS for m in mutations): raise UnsafeMutationError("PATH_NOT_GOVERNED")
    return {"schema":"prisma.visual.canonical-promotion-plan.v1","capabilityId":CAPABILITY_ID,"requestId":request["requestId"],
            "targetId":target["targetId"],"surfaceKey":target["surfaceKey"],"semanticAction":d["semanticAction"],
            "semanticDecisionId":d.get("semanticDecisionId"),"ids":{"recipeId":recipe_id,"bindingId":binding_id},
            "bindingAction":binding_action["action"],"recipeAction":recipe_action["action"],"layerAction":layer_action,
            "projectionAction":d.get("projectionAction",{"mode":"DEFERRED_DERIVATION","authorized":False}),
            "mutations":mutations,"preconditions":{"expectedCurrentHead":request["expectedCurrentHead"],
            "currentTruthDigest":sha256_json(request["currentTruth"]),"sourceDigest":request["source"]["digest"]},"status":status}

def _apply(repo_root: Path, mutation: dict[str,Any]) -> tuple[Path,str,str,Any]:
    if mutation["path"] not in ALLOWED_CANONICAL_PATHS: raise UnsafeMutationError("PATH_NOT_GOVERNED")
    path=repo_root/mutation["path"]; before=_load(path); before_sha=sha256_json(before); after=copy.deepcopy(before); value=mutation["value"]
    if mutation["operation"]=="append_recipe":
        if any(x.get("recipeId")==value.get("recipeId") for x in after.get("recipes",[])): raise CollisionError("RECIPE_ID_COLLISION")
        after["recipes"]=[*after.get("recipes",[]),value]; after["recipeCount"]=len(after["recipes"])
    elif mutation["operation"]=="append_binding":
        if any(x.get("bindingId")==value.get("bindingId") for x in after.get("bindings",[])): raise CollisionError("BINDING_ID_COLLISION")
        after["bindings"]=[*after.get("bindings",[]),value]
    else: raise UnsafeMutationError("UNKNOWN_MUTATION_OPERATION")
    after_sha=sha256_json(after); _atomic_write_json(path,after); return path,before_sha,after_sha,before

def _evidence(request,plan,status,applied,errors):
    return {"schema":EVIDENCE_SCHEMA,"requestId":request["requestId"],"requestDigest":sha256_json(request),
            "currentTruthDigest":plan["preconditions"]["currentTruthDigest"],"sourceDigest":plan["preconditions"]["sourceDigest"],
            "preState":[{"path":str(p),"sha256":b} for p,b,_,_ in applied],"postState":[{"path":str(p),"sha256":a} for p,_,a,_ in applied],
            "ids":plan["ids"],"mutations":plan["mutations"],"status":status,"errors":errors}


def rollback(request_id: str, repo_root: Path) -> dict[str, Any]:
    receipt = repo_root / RESULTS_ROOT / f"{request_id}.json"
    if not receipt.exists():
        raise CanonicalRegistrationError("RECEIPT_NOT_FOUND")
    evidence = _load(receipt)
    if evidence.get("status") != "APPLIED":
        raise CanonicalRegistrationError("ROLLBACK_REQUIRES_APPLIED_TRANSACTION")
    restored = []
    for row in evidence.get("postState", []):
        path = repo_root / row["path"]
        current = sha256_json(_load(path))
        if current != row["sha256"]:
            raise UnsafeMutationError("ROLLBACK_WOULD_OVERWRITE_NEWER_WORK:" + row["path"])
        prior_value = evidence.get("preStateValues", {}).get(row["path"])
        if prior_value is None:
            raise UnsafeMutationError("ROLLBACK_PRESTATE_VALUE_MISSING:" + row["path"])
        _atomic_write_json(path, prior_value)
        restored.append(row["path"])
    evidence["status"] = "ROLLED_BACK"
    evidence["rollback"] = {"restoredPaths": restored, "transactionScoped": True}
    _atomic_write_json(receipt, evidence)
    return {"schema": RESULT_SCHEMA, "capabilityId": CAPABILITY_ID, "requestId": request_id, "status": "ROLLED_BACK", "restoredPaths": restored}


def register(request: dict[str,Any], repo_root: Path) -> dict[str,Any]:
    plan=build_plan(request,repo_root)
    receipt=repo_root/RESULTS_ROOT/f"{request['requestId']}.json"; receipt.parent.mkdir(parents=True,exist_ok=True)
    if receipt.exists():
        prior=_load(receipt)
        if prior.get("requestDigest")==sha256_json(request) and prior.get("status") in {"APPLIED","NO_OP_IDEMPOTENT"}: return prior["result"]
    if plan["status"]=="NO_OP_IDEMPOTENT":
        evidence=_evidence(request,plan,"NO_OP_IDEMPOTENT",[],[])
        result={"schema":RESULT_SCHEMA,"capabilityId":CAPABILITY_ID,"requestId":request["requestId"],"targetId":plan["targetId"],"status":"NO_OP_IDEMPOTENT","ids":plan["ids"],"evidenceDigest":sha256_json(evidence)}
        evidence["result"]=result; _atomic_write_json(receipt,evidence); return result
    applied=[]
    try:
        for mutation in plan["mutations"]: applied.append(_apply(repo_root,mutation))
    except Exception:
        # V1 fails closed. Persist pre/post hashes for any mutation that completed; do not overwrite newer work.
        raise
    evidence=_evidence(request,plan,"APPLIED",applied,[])
    evidence["preStateValues"]={str(p):before for p,_,_,before in applied}
    result={"schema":RESULT_SCHEMA,"capabilityId":CAPABILITY_ID,"requestId":request["requestId"],"targetId":plan["targetId"],"status":"APPLIED","ids":plan["ids"],"evidenceDigest":sha256_json(evidence)}
    evidence["result"]=result; _atomic_write_json(receipt,evidence); return result
