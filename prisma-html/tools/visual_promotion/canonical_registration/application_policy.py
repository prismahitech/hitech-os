from __future__ import annotations

from dataclasses import dataclass
from typing import Any

POLICIES={"EXACT_TARGET_ONLY","BOUNDED_EXACT_TARGET_WAVE"}
WRITERS={"CANONICAL_REGISTRATION","GVAE"}

class ApplicationPolicyError(ValueError):
    pass

@dataclass(frozen=True)
class ApplicationPolicy:
    implementation_layer_id:str
    application_layer_id:str
    policy:str
    writer_kind:str
    authority_domain:str
    decision_ref:str

def validate_application_policy(value:dict[str,Any]) -> ApplicationPolicy:
    if not isinstance(value,dict):
        raise ApplicationPolicyError("APPLICATION_POLICY_OBJECT_REQUIRED")
    implementation=value.get("implementationLayerId")
    application=value.get("applicationLayerId")
    policy=value.get("policy")
    writer=value.get("writerKind")
    domain=value.get("authorityDomain")
    decision=value.get("decisionRef")
    if not isinstance(implementation,str) or not implementation:
        raise ApplicationPolicyError("IMPLEMENTATION_LAYER_REQUIRED")
    if not isinstance(application,str) or not application.startswith("LYR."):
        raise ApplicationPolicyError("APPLICATION_LAYER_ID_INVALID")
    if policy not in POLICIES:
        raise ApplicationPolicyError("APPLICATION_POLICY_INVALID")
    if writer not in WRITERS:
        raise ApplicationPolicyError("WRITER_KIND_INVALID")
    if domain!="rifat":
        raise ApplicationPolicyError("APPLICATION_LAYER_AUTHORITY_MUST_BE_RIFAT")
    if not isinstance(decision,str) or not decision:
        raise ApplicationPolicyError("APPLICATION_LAYER_DECISION_REF_REQUIRED")
    if implementation==application:
        raise ApplicationPolicyError("IMPLEMENTATION_AND_APPLICATION_LAYER_MUST_BE_DISTINCT")
    return ApplicationPolicy(implementation,application,policy,writer,domain,decision)
