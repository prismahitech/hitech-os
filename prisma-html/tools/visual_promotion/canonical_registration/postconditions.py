from __future__ import annotations

import json
from pathlib import Path

from .authority_adapters import AuthorityBindingError, validate_exact_binding
from .engine import CanonicalRegistrationError, sha256_json

def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def verify_registration_postconditions(repo_root: Path, plan: dict) -> dict:
    target_id=plan["targetId"]
    binding_id=plan["ids"]["bindingId"]
    recipe_id=plan["ids"]["recipeId"]
    bindings_path=repo_root/"prisma-html/authority/rifat/identity/registries/element-bindings.registry.json"
    recipes_path=repo_root/"prisma-html/authority/rifat/identity/registries/recipe.registry.json"
    bindings=_load(bindings_path); recipes=_load(recipes_path)

    binding_entries=[x for x in bindings.get("bindings",[]) if isinstance(x,dict) and x.get("bindingId")==binding_id]
    if len(binding_entries)!=1:
        raise CanonicalRegistrationError("POSTCONDITION_BINDING_ID_NOT_UNIQUE")
    try:
        validate_exact_binding(
            repo_root,
            binding_entries[0],
            target_id,
            plan["surfaceKey"],
            plan["semanticAuthority"]["canonicalMeaningId"],
        )
    except AuthorityBindingError as exc:
        raise CanonicalRegistrationError(str(exc)) from exc

    recipe_entries=[x for x in recipes.get("recipes",[]) if isinstance(x,dict) and x.get("recipeId")==recipe_id]
    if len(recipe_entries)!=1:
        raise CanonicalRegistrationError("POSTCONDITION_RECIPE_ID_NOT_UNIQUE")

    from visual_application.target_index import build_index
    target_rows=[x for x in build_index(repo_root).get("records",[]) if isinstance(x,dict) and x.get("targetId")==target_id]
    if len(target_rows)>1:
        raise CanonicalRegistrationError("POSTCONDITION_TARGET_INDEX_DUPLICATE")
    target_status="VERIFIED_EXACT_TARGET" if len(target_rows)==1 else "DERIVATION_PENDING_TARGET_INDEX"

    body={
        "targetId":target_id,
        "censusTargetId":plan["censusTargetId"],
        "bindingId":binding_id,
        "recipeId":recipe_id,
        "identityBinding":"VERIFIED",
        "rifatExactBinding":"VERIFIED",
        "targetIndex":target_status,
        "projection":"DERIVATION_DEFERRED",
        "runtimeCertification":"NOT_PERFORMED",
    }
    return {
        "schema":"prisma.visual.canonical-promotion-postconditions.v1",
        **body,
        "postconditionDigest":sha256_json(body),
    }
