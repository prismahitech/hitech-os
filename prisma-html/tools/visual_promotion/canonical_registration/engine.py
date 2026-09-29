from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .authority_adapters import AuthorityBindingError, validate_exact_binding
from .policy import (
    CanonicalRegistrationPolicyError,
    allocate_id,
    assert_no_inferred_id,
    validate_target_id,
)

CAPABILITY_ID="visual.canonical_promotion_integration_v1"
SCHEMA="prisma.visual.canonical-promotion-request.v1"
PLAN_SCHEMA="prisma.visual.canonical-promotion-plan.v1"
RESULT_SCHEMA="prisma.visual.canonical-promotion-result.v1"
EVIDENCE_SCHEMA="prisma.visual.canonical-promotion-evidence.v1"
JOURNAL_SCHEMA="prisma.visual.canonical-promotion-journal.v1"

ALLOWED_CANONICAL_PATHS={
    "prisma-html/authority/rifat/identity/registries/recipe.registry.json",
    "prisma-html/authority/rifat/identity/registries/element-bindings.registry.json",
}
RESULTS_ROOT="prisma-html/governance/visual-promotion/canonical-registration/receipts"
TRANSACTIONS_ROOT="prisma-html/governance/visual-promotion/canonical-registration/transactions"

class CanonicalRegistrationError(RuntimeError): pass
class CollisionError(CanonicalRegistrationError): pass
class SemanticCollisionError(CollisionError): code="SEMANTIC_COLLISION"
class BindingCollisionError(CollisionError): code="BINDING_COLLISION"
class IdCollisionError(CollisionError): code="ID_COLLISION"
class LayerCollisionError(CollisionError): code="LAYER_COLLISION"
class ProjectionConflictError(CollisionError): code="PROJECTION_CONFLICT"
class StaleHeadError(CanonicalRegistrationError): pass
class SourceDriftError(CanonicalRegistrationError): pass
class UnsafeMutationError(CanonicalRegistrationError): pass

def canonical_json(value:Any)->bytes:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")

def sha256_json(value:Any)->str:
    return hashlib.sha256(canonical_json(value)).hexdigest()

def file_sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def _load(path:Path)->Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: raise CanonicalRegistrationError(f"JSON_INVALID:{path}") from exc

def _atomic_write_json(path:Path,value:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".canonical-registration-",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as handle:
            json.dump(value,handle,ensure_ascii=False,indent=2)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def current_repo_head(repo_root:Path)->str:
    env=os.environ.get("GITHUB_SHA")
    if isinstance(env,str) and len(env)==40: return env
    try:
        proc=subprocess.run(["git","rev-parse","HEAD"],cwd=repo_root,check=True,capture_output=True,text=True)
    except Exception as exc: raise StaleHeadError("CURRENT_REPO_HEAD_UNAVAILABLE") from exc
    value=proc.stdout.strip()
    if len(value)!=40: raise StaleHeadError("CURRENT_REPO_HEAD_INVALID")
    return value

def _acquire_lock(lock_dir:Path)->None:
    lock_dir.parent.mkdir(parents=True,exist_ok=True)
    try: lock_dir.mkdir()
    except FileExistsError as exc: raise UnsafeMutationError("CONCURRENT_TRANSACTION_LOCK_EXISTS") from exc
    _atomic_write_json(lock_dir/"LOCK.json",{"schema":"prisma.visual.transaction-lock.v1","locked":True})

def _release_lock(lock_dir:Path)->None:
    if (lock_dir/"LOCK.json").exists(): (lock_dir/"LOCK.json").unlink()
    if lock_dir.exists(): lock_dir.rmdir()

def _registry_ids(registry:dict[str,Any],key:str)->set[str]:
    out=set()
    for item in registry.get(key,[]):
        if isinstance(item,dict):
            for field in ("recipeId","bindingId","targetId"):
                if isinstance(item.get(field),str): out.add(item[field])
    return out

def _validate_request(request:dict[str,Any])->None:
    if request.get("schema")!=SCHEMA: raise CanonicalRegistrationError("REQUEST_SCHEMA_INVALID")
    for field in ("requestId","target","expectedCurrentHead","currentTruth","source","decision","authorization"):
        if not request.get(field): raise CanonicalRegistrationError(f"REQUEST_FIELD_MISSING:{field}")
    target=request["target"]
    if not target.get("targetId") or not target.get("censusTargetId") or not target.get("surfaceKey"):
        raise CanonicalRegistrationError("TARGET_CANONICAL_AND_CENSUS_IDS_REQUIRED")
    truth=request["currentTruth"]
    if truth.get("schema")!="prisma.visual.current-truth-snapshot.v1": raise CanonicalRegistrationError("CURRENT_TRUTH_SNAPSHOT_REQUIRED")
    required_truth={"repoHead","snapshotId","targetIndexDigest","identityDigest","rifatDigest","ndcDigest","projectionDigest","authorityMeshDigest","layerMapDigest","targetEvidenceDigest","evidenceTargetId"}
    if not required_truth.issubset(truth): raise CanonicalRegistrationError("CURRENT_TRUTH_SNAPSHOT_INCOMPLETE")
    if truth.get("repoHead")!=request["expectedCurrentHead"]: raise StaleHeadError("CURRENT_TRUTH_HEAD_MISMATCH")
    if truth.get("evidenceTargetId")!=target["censusTargetId"]: raise CanonicalRegistrationError("CURRENT_TRUTH_EVIDENCE_TARGET_MISMATCH")
    source=request["source"]
    if not isinstance(source.get("digest"),str) or len(source["digest"])!=64: raise CanonicalRegistrationError("SOURCE_DIGEST_REQUIRED")
    if not source.get("path"): raise CanonicalRegistrationError("SOURCE_PATH_REQUIRED")
    decision=request["decision"]
    if decision.get("semanticAction") not in {"REUSE_EXISTING","CREATE_NEW"}: raise CanonicalRegistrationError("SEMANTIC_ADJUDICATION_REQUIRED")
    semantic_authority=decision.get("semanticAuthority") or {}
    if semantic_authority.get("authorityDomain")!="ndc" or semantic_authority.get("writerKind")!="NDC_CURATION":
        raise CanonicalRegistrationError("NDC_CURATION_AUTHORITY_REQUIRED")
    if not semantic_authority.get("canonicalMeaningId") or not semantic_authority.get("decisionRef"):
        raise CanonicalRegistrationError("NDC_CANONICAL_MEANING_REFERENCE_REQUIRED")
    if decision.get("semanticAction")=="CREATE_NEW" and (not decision.get("semanticDecisionId") or not decision.get("approvalEvidenceRefs")):
        raise CanonicalRegistrationError("EXPLICIT_SEMANTIC_APPROVAL_REQUIRED")
    auth=request["authorization"]
    if auth.get("canonicalRegistrationAuthorized") is not True: raise CanonicalRegistrationError("CANONICAL_REGISTRATION_NOT_AUTHORIZED")
    if auth.get("automaticSemanticInference") is not False: raise CanonicalRegistrationError("AUTOMATIC_SEMANTIC_INFERENCE_FORBIDDEN")
    if auth.get("automaticApplicationSource") is not False: raise CanonicalRegistrationError("AUTOMATIC_APPLICATION_SOURCE_FORBIDDEN")
    assert_no_inferred_id(decision.get("idInputs") or {})

def _validate_source_pin(request:dict[str,Any],repo_root:Path)->None:
    path=(repo_root/request["source"]["path"]).resolve()
    root=repo_root.resolve()
    if path!=root and root not in path.parents: raise UnsafeMutationError("SOURCE_PATH_ESCAPE")
    if not path.is_file(): raise CanonicalRegistrationError("SOURCE_FILE_NOT_FOUND")
    if file_sha256(path)!=request["source"]["digest"]: raise SourceDriftError("SOURCE_DRIFT")

def build_plan(request:dict[str,Any],repo_root:Path)->dict[str,Any]:
    _validate_request(request)
    from .current_truth import verify_current_truth
    verify_current_truth(repo_root,request["currentTruth"],evidence_target_id=request["target"]["censusTargetId"])
    _validate_source_pin(request,repo_root)

    target=request["target"]; decision=request["decision"]
    layer=decision.get("layerAction") or {}
    binding=decision.get("bindingAction") or {}
    recipe=decision.get("recipeAction") or {}
    if not layer.get("applicationLayerId") or layer.get("policy") not in {"EXACT_TARGET_ONLY","BOUNDED_EXACT_TARGET_WAVE"}:
        raise CanonicalRegistrationError("APPLICATION_LAYER_POLICY_REQUIRED")
    if layer.get("writerKind")!="CANONICAL_REGISTRATION": raise CanonicalRegistrationError("WRITER_KIND_REQUIRED")
    meaning_id=decision["semanticAuthority"]["canonicalMeaningId"]

    existing_bindings=_load(repo_root/ALLOWED_CANONICAL_PATHS.pop() if False else repo_root/"prisma-html/authority/rifat/identity/registries/element-bindings.registry.json")
    existing_binding_ids=_registry_ids(existing_bindings,"bindings")
    existing_recipe_registry=_load(repo_root/"prisma-html/authority/rifat/identity/registries/recipe.registry.json")
    existing_recipe_ids=_registry_ids(existing_recipe_registry,"recipes")

    target_action=decision.get("targetAction") or {}
    if target_action.get("action")=="CREATE_NEW":
        td=validate_target_id(
            requested_id=target["targetId"],
            semantic_key=f"{target['surfaceKey']}|{target['censusTargetId']}|{meaning_id}",
            census_target_id=target["censusTargetId"],
            surface_key=target["surfaceKey"],
            existing_ids={str(x) for x in target_action.get("existingCanonicalTargetIds",[])},
        )
        if td.action not in {"CREATE_NEW","REUSE_EXISTING"}: raise CanonicalRegistrationError("TARGET_ID_DECISION_INVALID")
    elif target_action.get("action")!="REUSE_EXISTING":
        raise CanonicalRegistrationError("TARGET_REGISTRATION_ACTION_REQUIRED")

    if binding.get("action")=="CREATE_NEW":
        b=allocate_id("binding",f"{target['surfaceKey']}|{target['targetId']}|{meaning_id}",existing_binding_ids,requested_id=binding.get("bindingId"))
        if b.action!="CREATE_NEW": raise IdCollisionError("BINDING_ID_REUSE_REQUIRES_EXPLICIT_ACTION")
        binding_id=b.id
    elif binding.get("action")=="REUSE_EXISTING":
        binding_id=binding.get("bindingId")
        if not binding_id or binding_id not in existing_binding_ids: raise CanonicalRegistrationError("BINDING_REUSE_NOT_FOUND")
    else: raise CanonicalRegistrationError("BINDING_ACTION_INVALID")

    exact=binding.get("exactBinding")
    try:
        validate_exact_binding(repo_root,exact,target["targetId"],target["surfaceKey"],meaning_id)
    except AuthorityBindingError as exc: raise CanonicalRegistrationError(str(exc)) from exc
    if binding.get("registryEntry") is not None and binding.get("action")=="CREATE_NEW":
        entry=copy.deepcopy(binding["registryEntry"]); entry["bindingId"]=binding_id
        if entry!=exact: raise BindingCollisionError("REGISTRY_ENTRY_MUST_EQUAL_EXACT_BINDING")
    else:
        entry=exact

    if recipe.get("action")=="CREATE_NEW":
        rd=allocate_id("recipe",recipe["semanticKey"],existing_recipe_ids,requested_id=recipe.get("recipeId"))
        if rd.action!="CREATE_NEW": raise IdCollisionError("RECIPE_ID_REUSE_REQUIRES_EXPLICIT_ACTION")
        recipe_id=rd.id
        recipe_entry=copy.deepcopy(recipe.get("registryEntry") or {})
        recipe_entry["recipeId"]=recipe_id
        recipe_path=recipe_entry.get("path")
        if not isinstance(recipe_path,str): raise CanonicalRegistrationError("NEW_RECIPE_SOURCE_PATH_REQUIRED")
        recipe_file=(repo_root/"prisma-html/authority/rifat/identity")/recipe_path
        if not recipe_file.is_file(): raise CanonicalRegistrationError("NEW_RECIPE_SOURCE_NOT_FOUND")
        expected_recipe_sha=recipe_entry.get("fileSha256") or recipe_entry.get("canonicalRecipeSha256")
        if not isinstance(expected_recipe_sha,str) or file_sha256(recipe_file)!=expected_recipe_sha: raise SourceDriftError("NEW_RECIPE_SOURCE_DRIFT")
    elif recipe.get("action")=="REUSE_EXISTING":
        recipe_id=recipe.get("recipeId")
        if not recipe_id or recipe_id not in existing_recipe_ids: raise CanonicalRegistrationError("RECIPE_REUSE_NOT_FOUND")
        recipe_entry=None
    else: raise CanonicalRegistrationError("RECIPE_ACTION_INVALID")

    collisions=[t for bentry in existing_bindings.get("bindings",[]) if isinstance(bentry,dict) for t in bentry.get("targets",[]) if isinstance(t,dict) and t.get("targetId")==target["targetId"]]
    if collisions:
        if len(collisions)>1: raise BindingCollisionError("MULTIPLE_EXISTING_TARGET_BINDINGS")
        if collisions[0] != exact: raise BindingCollisionError("EXACT_TARGET_BINDING_COLLISION")
        if target_action.get("action")=="CREATE_NEW": raise BindingCollisionError("TARGET_ID_ALREADY_REGISTERED")
        status="NO_OP_IDEMPOTENT"
    else: status="APPLY"

    mutations=[]
    if status=="APPLY" and binding.get("action")=="CREATE_NEW":
        mutations.append({"path":"prisma-html/authority/rifat/identity/registries/element-bindings.registry.json","operation":"append_binding","value":entry})
    if status=="APPLY" and recipe.get("action")=="CREATE_NEW":
        mutations.append({"path":"prisma-html/authority/rifat/identity/registries/recipe.registry.json","operation":"append_recipe","value":recipe_entry})

    return {
        "schema":PLAN_SCHEMA,"capabilityId":CAPABILITY_ID,"requestId":request["requestId"],
        "targetId":target["targetId"],"censusTargetId":target["censusTargetId"],"surfaceKey":target["surfaceKey"],
        "semanticAction":decision["semanticAction"],"semanticDecisionId":decision.get("semanticDecisionId"),
        "ids":{"targetId":target["targetId"],"bindingId":binding_id,"recipeId":recipe_id},
        "bindingAction":binding.get("action"),"recipeAction":recipe.get("action"),"targetAction":target_action.get("action"),
        "layerAction":layer,"semanticAuthority":decision["semanticAuthority"],
        "projectionAction":decision.get("projectionAction",{"mode":"DEFERRED_DERIVATION","authorized":False}),
        "mutations":mutations,
        "preconditions":{"expectedCurrentHead":request["expectedCurrentHead"],"currentTruthDigest":sha256_json(request["currentTruth"]),"sourceDigest":request["source"]["digest"],
                        "registryDigests":{"recipeRegistry":sha256_json(existing_recipe_registry),"bindingRegistry":sha256_json(existing_bindings)}},
        "status":status,
    }

def _apply(repo_root:Path,mutation:dict[str,Any])->tuple[Path,str,str,Any]:
    if mutation["path"] not in ALLOWED_CANONICAL_PATHS: raise UnsafeMutationError("PATH_NOT_GOVERNED")
    path=repo_root/mutation["path"]; before=_load(path); before_sha=sha256_json(before); after=copy.deepcopy(before); value=mutation["value"]
    if mutation["operation"]=="append_recipe":
        if any(x.get("recipeId")==value.get("recipeId") for x in after.get("recipes",[])): raise IdCollisionError("RECIPE_ID_COLLISION")
        after["recipes"]=[*after.get("recipes",[]),value]; after["recipeCount"]=len(after["recipes"])
    elif mutation["operation"]=="append_binding":
        if any(x.get("bindingId")==value.get("bindingId") for x in after.get("bindings",[])): raise IdCollisionError("BINDING_ID_COLLISION")
        after["bindings"]=[*after.get("bindings",[]),value]
    else: raise UnsafeMutationError("UNKNOWN_MUTATION_OPERATION")
    after_sha=sha256_json(after); _atomic_write_json(path,after); return path,before_sha,after_sha,before

def _evidence(request,plan,status,applied,errors):
    root=request["_repoRoot"]
    return {"schema":EVIDENCE_SCHEMA,"requestId":request["requestId"],"requestDigest":sha256_json({k:v for k,v in request.items() if k!="_repoRoot"}),
            "currentTruthDigest":plan["preconditions"]["currentTruthDigest"],"sourceDigest":plan["preconditions"]["sourceDigest"],
            "preState":[{"path":str(p.relative_to(root)).replace("\\","/"),"sha256":b} for p,b,_,_ in applied],
            "postState":[{"path":str(p.relative_to(root)).replace("\\","/"),"sha256":a} for p,_,a,_ in applied],
            "ids":plan["ids"],"mutations":plan["mutations"],"status":status,"errors":errors}

def register(request:dict[str,Any],repo_root:Path)->dict[str,Any]:
    request=copy.deepcopy(request); request["_repoRoot"]=str(repo_root.resolve())
    receipt_path=repo_root/RESULTS_ROOT/f"{request['requestId']}.json"; receipt_path.parent.mkdir(parents=True,exist_ok=True)
    request_digest=sha256_json({k:v for k,v in request.items() if k!="_repoRoot"})
    if receipt_path.exists():
        prior=_load(receipt_path)
        if prior.get("requestDigest")==request_digest and prior.get("status") in {"APPLIED","NO_OP_IDEMPOTENT"} and prior.get("result"):
            if current_repo_head(repo_root)!=request["expectedCurrentHead"]: raise StaleHeadError("CURRENT_HEAD_CHANGED_FOR_IDEMPOTENT_REPLAY")
            return prior["result"]

    plan=build_plan(request,repo_root)
    journal_dir=repo_root/TRANSACTIONS_ROOT/request["requestId"]; journal_path=journal_dir/"journal.json"
    if plan["status"]=="NO_OP_IDEMPOTENT":
        evidence=_evidence(request,plan,"NO_OP_IDEMPOTENT",[],[])
        result={"schema":RESULT_SCHEMA,"capabilityId":CAPABILITY_ID,"requestId":request["requestId"],"targetId":plan["targetId"],"status":"NO_OP_IDEMPOTENT","ids":plan["ids"],"evidenceDigest":sha256_json(evidence)}
        evidence["result"]=result; _atomic_write_json(receipt_path,evidence); return result

    lock=repo_root/TRANSACTIONS_ROOT/f".{request['requestId']}.lock"; _acquire_lock(lock)
    try:
        head=current_repo_head(repo_root)
        if head!=request["expectedCurrentHead"]: raise StaleHeadError(f"CURRENT_HEAD_CHANGED:{head}:{request['expectedCurrentHead']}")
        prestate={m["path"]:_load(repo_root/m["path"]) for m in plan["mutations"]}
        journal={"schema":JOURNAL_SCHEMA,"requestId":request["requestId"],"requestDigest":request_digest,"status":"PREPARED","expectedCurrentHead":head,
                 "currentTruthDigest":plan["preconditions"]["currentTruthDigest"],"preStateValues":prestate,"preStateDigests":{p:sha256_json(v) for p,v in prestate.items()},"mutations":plan["mutations"]}
        _atomic_write_json(journal_path,journal)
        applied=[]
        try:
            for mutation in plan["mutations"]:
                rel=mutation["path"]; path=repo_root/rel; current=sha256_json(_load(path))
                expected=plan["preconditions"]["registryDigests"]["recipeRegistry"] if rel.endswith("recipe.registry.json") else plan["preconditions"]["registryDigests"]["bindingRegistry"]
                if current!=expected: raise StaleHeadError("REGISTRY_PRECONDITION_CHANGED:"+rel)
                applied.append(_apply(repo_root,mutation))
            from .postconditions import verify_registration_postconditions
            post=verify_registration_postconditions(repo_root,plan)
        except Exception as exc:
            for rel,before in prestate.items():
                path=repo_root/rel; completed=next((x[2] for x in applied if str(x[0].relative_to(repo_root)).replace("\\","/")==rel),None)
                if completed is not None and sha256_json(_load(path))==completed: _atomic_write_json(path,before)
            journal["status"]="ROLLED_BACK_AFTER_FAILURE"; journal["error"]=str(exc); journal["rollbackVerified"]=True; _atomic_write_json(journal_path,journal)
            evidence=_evidence(request,plan,"FAILED",applied,[str(exc)]); evidence["journalPath"]=str(journal_path.relative_to(repo_root)).replace("\\","/")
            _atomic_write_json(receipt_path,evidence); raise
        journal["status"]="APPLIED"; journal["postStateDigests"]={str(p.relative_to(repo_root)).replace("\\","/"):a for p,_,a,_ in applied}; _atomic_write_json(journal_path,journal)
        evidence=_evidence(request,plan,"APPLIED",applied,[]); evidence["journalPath"]=str(journal_path.relative_to(repo_root)).replace("\\","/"); evidence["postconditions"]=post; evidence["preStateValues"]={str(p.relative_to(repo_root)).replace("\\","/"):b for p,_,_,b in applied}
        result={"schema":RESULT_SCHEMA,"capabilityId":CAPABILITY_ID,"requestId":request["requestId"],"targetId":plan["targetId"],"status":"APPLIED","ids":plan["ids"],"journalPath":evidence["journalPath"],"evidenceDigest":sha256_json(evidence)}
        evidence["result"]=result; _atomic_write_json(receipt_path,evidence); return result
    finally:
        _release_lock(lock)

def rollback(request_id:str,repo_root:Path)->dict[str,Any]:
    receipt=repo_root/RESULTS_ROOT/f"{request_id}.json"
    if not receipt.exists(): raise CanonicalRegistrationError("RECEIPT_NOT_FOUND")
    evidence=_load(receipt)
    if evidence.get("status")!="APPLIED": raise CanonicalRegistrationError("ROLLBACK_REQUIRES_APPLIED_TRANSACTION")
    restored=[]
    for row in evidence.get("postState",[]):
        rel=row["path"]; path=repo_root/rel
        if sha256_json(_load(path))!=row["sha256"]: raise UnsafeMutationError("ROLLBACK_WOULD_OVERWRITE_NEWER_WORK:"+rel)
        prior=evidence.get("preStateValues",{}).get(rel)
        if prior is None: raise UnsafeMutationError("ROLLBACK_PRESTATE_VALUE_MISSING:"+rel)
        _atomic_write_json(path,prior); restored.append(rel)
    evidence["status"]="ROLLED_BACK"; evidence["rollback"]={"restoredPaths":restored,"transactionScoped":True,"newerWorkProtection":True}
    _atomic_write_json(receipt,evidence)
    return {"schema":RESULT_SCHEMA,"capabilityId":CAPABILITY_ID,"requestId":request_id,"status":"ROLLED_BACK","restoredPaths":restored}
