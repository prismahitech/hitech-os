from __future__ import annotations

from dataclasses import dataclass
from typing import Any

LIFECYCLE={"DISCOVERY_ONLY","REGISTER_TARGET_FIRST","BLOCKED","APPLY_READY","APPLIED","RUNTIME_VERIFIED"}

@dataclass(frozen=True)
class TargetStatus:
    lifecycle:str
    blocker_codes:tuple[str,...]
    mutation_eligible:bool

def classify_target_status(record:dict[str,Any])->TargetStatus:
    kind=record.get("recordKind")
    enforcement=record.get("enforcement")
    explicit_blockers=tuple(sorted(set(record.get("blockerCodes") or record.get("blockers") or [])))
    if kind=="VISUAL_CONTROL_CENSUS_TARGET" and enforcement=="DISCOVERY_ONLY":
        return TargetStatus(
            "BLOCKED" if explicit_blockers else "DISCOVERY_ONLY",
            explicit_blockers,
            False,
        )
    if explicit_blockers:
        return TargetStatus("BLOCKED",explicit_blockers,False)
    state=record.get("lifecycleStatus")
    if state not in LIFECYCLE:
        raise ValueError("TARGET_LIFECYCLE_STATE_REQUIRED")
    if state=="REGISTER_TARGET_FIRST":
        return TargetStatus(state,explicit_blockers,False)
    if state=="APPLY_READY":
        required=("targetId","bindingId","applicationLayerId")
        if any(not record.get(x) for x in required):
            raise ValueError("APPLY_READY_REQUIRES_EXPLICIT_AUTHORITY")
        return TargetStatus(state,(),True)
    if state in {"APPLIED","RUNTIME_VERIFIED"}:
        return TargetStatus(state,(),True)
    return TargetStatus(state,(),False)
