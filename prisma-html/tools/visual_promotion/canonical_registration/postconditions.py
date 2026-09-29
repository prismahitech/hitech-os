from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .authority_adapters import validate_exact_binding
from .engine import CanonicalRegistrationError, sha256_json

def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def verify_registration_postconditions(repo_root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    target_id = plan["targetId"]
    binding_id = plan["ids"]["bindingId"]
    recipe_id = plan["ids"]["recipeId"]

    bindings_path = repo_root / "prisma-html/authority/rifat/identity/registries/element-bindings.registry.json"
    recipes_path = repo_root / "prisma-html/authority/rifat/identity/registries/recipe.registry.json"
    bindings = _load(bindings_path)
    recipes = _load(recipes_path)

    binding_entries = [item for item in bindings.get("bindings", []) if item.get("bindingId") == binding_id]
    if len(binding_entries) != 1:
        raise CanonicalRegistrationError("POSTCONDITION_BINDING_ID_NOT_UNIQUE")
    binding = binding_entries[0]
    exact_targets = [item for item in binding.get("targets", []) if item.get("targetId") == target_id]
    if len(exact_targets) != 1:
        raise CanonicalRegistrationError("POSTCONDITION_TARGET_NOT_UNIQUE")
    validate_exact_binding(repo_root, binding, target_id)

    if plan["recipeAction"] == "CREATE_NEW":
        recipe_entries = [item for item in recipes.get("recipes", []) if item.get("recipeId") == recipe_id]
        if len(recipe_entries) != 1:
            raise CanonicalRegistrationError("POSTCONDITION_RECIPE_ID_NOT_UNIQUE")
    else:
        if not any(item.get("recipeId") == recipe_id for item in recipes.get("recipes", [])):
            raise CanonicalRegistrationError("POSTCONDITION_REUSED_RECIPE_MISSING")

    from visual_application.target_index import build_index
    target_rows = [row for row in build_index(repo_root).get("records", []) if row.get("targetId") == target_id]
    target_index_status = "VERIFIED_EXACT_TARGET" if len(target_rows) == 1 else "DERIVATION_PENDING_TARGET_INDEX"
    if len(target_rows) > 1:
        raise CanonicalRegistrationError("POSTCONDITION_TARGET_INDEX_DUPLICATE")

    return {
        "schema": "prisma.visual.canonical-promotion-postconditions.v1",
        "targetId": target_id,
        "bindingId": binding_id,
        "recipeId": recipe_id,
        "identityBinding": "VERIFIED",
        "rifatExactBinding": "VERIFIED",
        "targetIndex": target_index_status,
        "derivedProjectionRegeneration": "DEFERRED",
        "postconditionDigest": sha256_json({
            "targetId": target_id,
            "bindingId": binding_id,
            "recipeId": recipe_id,
            "identityBinding": "VERIFIED",
            "rifatExactBinding": "VERIFIED",
            "targetIndex": target_index_status,
        }),
    }
