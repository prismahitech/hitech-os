from __future__ import annotations
import hashlib
import re
from dataclasses import dataclass

ID_POLICIES = {
    "visualMeaning": {"prefix": "VIS.", "scope": "global"},
    "binding": {"prefix": "BND.", "scope": "global"},
    "recipe": {"prefix": "REC.", "scope": "identity"},
    "target": {"prefix": "TGT.", "scope": "target-index"},
    "applicationLayer": {"prefix": "LYR.", "scope": "rifat"},
}
FORBIDDEN_ID_SOURCES = {"selector", "routeId", "implementationLayerId", "filename", "atlasfinRecipeId"}

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
    return value[:80]

def allocate_id(namespace: str, semantic_key: str, existing_ids: set[str], *, requested_id: str | None = None) -> IdDecision:
    if namespace not in ID_POLICIES:
        raise CanonicalRegistrationPolicyError(f"UNKNOWN_ID_NAMESPACE:{namespace}")
    policy = ID_POLICIES[namespace]
    if requested_id is not None:
        if not requested_id.startswith(policy["prefix"]):
            raise CanonicalRegistrationPolicyError(f"ID_PREFIX_MISMATCH:{namespace}")
        if requested_id in existing_ids:
            return IdDecision("REUSE_EXISTING", requested_id, "exact-existing-id")
        return IdDecision("CREATE_NEW", requested_id, "explicit-authorized-id")
    if namespace in {"target", "applicationLayer"}:
        raise CanonicalRegistrationPolicyError(f"NO_GENERIC_ALLOCATION_RULE:{namespace}")
    slug = _slug(semantic_key)
    digest = hashlib.sha256(f"{namespace}|{semantic_key}".encode("utf-8")).hexdigest()[:12]
    candidate = f"{policy['prefix']}{slug}.{digest}"
    if candidate in existing_ids:
        return IdDecision("REUSE_EXISTING", candidate, "deterministic-existing-id")
    return IdDecision("CREATE_NEW", candidate, "deterministic-semantic-allocation")

def assert_no_inferred_id(source_fields: dict[str, str | None]) -> None:
    bad = sorted(k for k, v in source_fields.items() if v and k in FORBIDDEN_ID_SOURCES)
    if bad:
        raise CanonicalRegistrationPolicyError("ID_MUST_NOT_BE_DERIVED_FROM:" + ",".join(bad))
