from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .policy import validate_target_id

class RequestBuilderError(ValueError):
    pass

def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def build_request_from_readiness(
    row: dict[str, Any],
    *,
    current_truth: dict[str, Any],
    expected_current_head: str,
    authorization: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    if row.get("promotionReadinessDecision") != "READY_FOR_CANONICAL_REGISTRATION":
        raise RequestBuilderError("READINESS_NOT_READY_FOR_CANONICAL_REGISTRATION")
    if row.get("surfaceKey") not in {"tablet","pc","mobile","shared-ui"}:
        raise RequestBuilderError("SURFACE_INVALID")
    target_id = row.get("targetId")
    if not isinstance(target_id,str) or not target_id.startswith("TGT.CENSUS."):
        raise RequestBuilderError("READINESS_MUST_REFERENCE_CENSUS_TARGET")

    meaning=row.get("canonicalMeaning") or {}
    identity=row.get("identity") or {}
    physical=row.get("physical") or {}
    application=row.get("application") or {}
    semantic_resolution=meaning.get("resolution")
    semantic_id=meaning.get("ndcPrimaryId") or meaning.get("visualMeaningId")
    if semantic_resolution not in {"REUSE_EXISTING","PROPOSE_NEW"}:
        raise RequestBuilderError("SEMANTIC_DECISION_REQUIRED")
    if not semantic_id:
        authority=row.get("semanticAuthority") or {}
        semantic_id=authority.get("canonicalMeaningId")
    authority=row.get("semanticAuthority") or {}
    if authority.get("authorityDomain")!="ndc" or authority.get("writerKind")!="NDC_CURATION":
        raise RequestBuilderError("NDC_ADJUDICATION_EVIDENCE_REQUIRED")
    if not authority.get("decisionRef"):
        raise RequestBuilderError("NDC_DECISION_REF_REQUIRED")

    for field in ("routeId","regionId","slotId","componentId","ownerId","implementationLayerId"):
        if not physical.get(field):
            raise RequestBuilderError(f"PHYSICAL_BINDING_REQUIRED:{field}")
    if not application.get("applicationLayerId") or not application.get("projectionPolicy"):
        raise RequestBuilderError("APPLICATION_POLICY_REQUIRED")
    recipe_id=identity.get("identityRecipeId")
    if not recipe_id:
        raise RequestBuilderError("IDENTITY_RECIPE_REQUIRED")

    # The canonical target allocator is deterministic but consumes the physical
    # census identity as evidence, never as a semantic guess.
    requested_target = authority.get("canonicalTargetId")
    if not requested_target:
        raise RequestBuilderError("CANONICAL_TARGET_ID_ADJUDICATION_REQUIRED")
    validate_target_id(
        requested_id=requested_target,
        semantic_key=semantic_id,
        census_target_id=target_id,
        surface_key=row["surfaceKey"],
        existing_ids=set(authority.get("existingCanonicalTargetIds") or []),
    )

    binding_target={
        "targetId":requested_target,
        "ownerId":physical["ownerId"],
        "routeId":physical["routeId"],
        "regionId":physical["regionId"],
        "slotId":physical["slotId"],
        "componentUiId":physical.get("componentUiId"),
        "layerId":authority.get("canonicalLayerId"),
        "ownerCssId":physical.get("ownerCssId"),
        "selector":physical.get("selector"),
        "missingBindings":[],
    }
    if not binding_target["componentUiId"]:
        raise RequestBuilderError("EXACT_COMPONENT_UI_ID_REQUIRED")
    if not binding_target["layerId"]:
        raise RequestBuilderError("CANONICAL_LAYER_ID_ADJUDICATION_REQUIRED")
    if not authority.get("applicationPolicy"):
        raise RequestBuilderError("APPLICATION_POLICY_ADJUDICATION_REQUIRED")

    decision={
        "semanticAction":"CREATE_NEW" if semantic_resolution=="PROPOSE_NEW" else "REUSE_EXISTING",
        "semanticDecisionId":authority.get("decisionId"),
        "approvalEvidenceRefs":authority.get("approvalEvidenceRefs") or [],
        "semanticAuthority":{
            "authorityDomain":"ndc",
            "writerKind":"NDC_CURATION",
            "canonicalMeaningId":semantic_id,
            "decisionRef":authority["decisionRef"],
        },
        "targetAction":{"action":"CREATE_NEW","existingCanonicalTargetIds":sorted(set(authority.get("existingCanonicalTargetIds") or []))},
        "recipeAction":{"action":"REUSE_EXISTING","recipeId":recipe_id,"semanticKey":recipe_id},
        "bindingAction":{"action":"CREATE_NEW","bindingId":authority.get("canonicalBindingId"),"semanticKey":f"{row['surfaceKey']}|{target_id}|{semantic_id}|{physical['implementationLayerId']}","exactBinding":{
            "selector":{"surfaceId":row["surfaceKey"],"neutralMeaningId":semantic_id},
            "status":"RESOLVED",
            "targets":[binding_target],
        }},
        "layerAction":{
            "applicationLayerId":application["applicationLayerId"],
            "policy":authority.get("applicationPolicy"),
            "writerKind":"CANONICAL_REGISTRATION",
            "authorityDomain":"rifat",
            "decisionRef":authority.get("applicationLayerDecisionRef"),
        },
        "projectionAction":{"mode":"DEFERRED_DERIVATION","authorized":False},
        "idInputs":{"selector":None,"implementationLayerId":None},
    }
    return {
        "schema":"prisma.visual.canonical-promotion-request.v1",
        "requestId":"cpr."+_digest({"targetId":requested_target,"source":source.get("digest"),"decision":decision})[:24],
        "target":{"targetId":requested_target,"censusTargetId":target_id,"surfaceKey":row["surfaceKey"]},
        "expectedCurrentHead":expected_current_head,
        "currentTruth":current_truth,
        "source":source,
        "decision":decision,
        "authorization":authorization,
    }
