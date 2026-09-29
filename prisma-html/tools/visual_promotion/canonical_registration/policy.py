from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

ID_POLICIES = {
    "visualMeaning": {"prefix": "VIS.", "scope": "global", "allocator": "semantic-hash"},
    "binding": {"prefix": "BND.", "scope": "global", "allocator": "coordinate-hash"},
    "recipe": {"prefix": "REC.", "scope": "identity", "allocator": "semantic-hash"},
    "target": {"prefix": "TGT.", "scope": "target-index", "allocator": "canonical-composer"},
    "applicationLayer": {"prefix": "LYR.", "scope": "rifat", "allocator": "owner-authority-only"},
}

FORBIDDEN_ID_SOURCES = {
    "selector", "routeId", "regionId", "slotId", "componentUiId",
    "implementationLayerId", "filename", "atlasfinRecipeId", "visualSimilarity",
}

class CanonicalRegistrationPolicyError(ValueError):
    pass

@dataclass(frozen=True)
class IdDecision:
    action: str
    id: str
    reason: str

def _slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", ".", value.strip()).strip(".")
    if not value:
        raise CanonicalRegistrationPolicyError("EMPTY_SEMANTIC_SLUG")
    return value[:72]

def _hash_key(namespace: str, semantic_key: str) -> str:
    return hashlib.sha256(f"{namespace}|{semantic_key}".encode("utf-8")).hexdigest()[:12]

def allocate_id(
    namespace: str,
    semantic_key: str,
    existing_ids: set[str],
    *,
    requested_id: str | None = None,
) -> IdDecision:
    if namespace not in ID_POLICIES:
        raise CanonicalRegistrationPolicyError(f"UNKNOWN_ID_NAMESPACE:{namespace}")
    rule = ID_POLICIES[namespace]
    if requested_id is not None:
        if not requested_id.startswith(rule["prefix"]):
            raise CanonicalRegistrationPolicyError(f"ID_PREFIX_MISMATCH:{namespace}")
        if requested_id in existing_ids:
            return IdDecision("REUSE_EXISTING", requested_id, "exact-existing-id")
        return IdDecision("CREATE_NEW", requested_id, "explicit-authorized-id")
    if rule["allocator"] == "owner-authority-only":
        raise CanonicalRegistrationPolicyError(f"OWNER_AUTHORITY_REQUIRED:{namespace}")
    digest = _hash_key(namespace, semantic_key)
    if rule["allocator"] == "canonical-composer":
        candidate = f"{rule['prefix']}{_slug(semantic_key)}.{digest}.V1"
    else:
        candidate = f"{rule['prefix']}{_slug(semantic_key)}.{digest}"
    if candidate in existing_ids:
        return IdDecision("REUSE_EXISTING", candidate, "deterministic-existing-id")
    return IdDecision("CREATE_NEW", candidate, "deterministic-allocation")

def assert_no_inferred_id(source_fields: dict[str, Any]) -> None:
    bad = sorted(k for k, v in source_fields.items() if v and k in FORBIDDEN_ID_SOURCES)
    if bad:
        raise CanonicalRegistrationPolicyError("ID_MUST_NOT_BE_DERIVED_FROM:" + ",".join(bad))

def validate_target_id(
    *,
    requested_id: str,
    semantic_key: str,
    census_target_id: str,
    surface_key: str,
    existing_ids: set[str],
) -> IdDecision:
    canonical_key = f"{surface_key}|{census_target_id}|{semantic_key}"
    decision = allocate_id("target", canonical_key, existing_ids, requested_id=requested_id)
    expected = allocate_id("target", canonical_key, existing_ids).id
    if decision.action == "CREATE_NEW" and requested_id != expected:
        raise CanonicalRegistrationPolicyError("TARGET_ID_NOT_DETERMINISTIC")
    return decision


def collision_code(kind: str) -> str:
    codes = {
        "exact": "DUPLICATE_EXACT",
        "semantic": "SEMANTIC_COLLISION",
        "binding": "BINDING_COLLISION",
        "id": "ID_COLLISION",
        "layer": "LAYER_COLLISION",
        "projection": "PROJECTION_CONFLICT",
    }
    try:
        return codes[kind]
    except KeyError as exc:
        raise CanonicalRegistrationPolicyError(f"UNKNOWN_COLLISION_KIND:{kind}") from exc