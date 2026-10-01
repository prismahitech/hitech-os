from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CANONICAL_STATES={"NOT_STARTED","OPEN","READY_FOR_HANDOFF","CLOSED","SUPERSEDED","BLOCKED"}
SOURCE_STATES={"NOT_STARTED","IN_PROGRESS","BLOCKED","WAITING_EXTERNAL","READY_FOR_INTEGRATION","DONE","FAILED"}

@dataclass(frozen=True)
class LifecycleNormalization:
    canonical_state:str
    source_state:str
    blocker_codes:tuple[str,...]
    mutation_authorized:bool

def normalize_lifecycle(status:dict[str,Any])->LifecycleNormalization:
    source=status.get("state") or status.get("status")
    if source not in SOURCE_STATES:
        raise ValueError("LIFECYCLE_SOURCE_STATE_INVALID")
    if status.get("statusIsAuthority") is not False or status.get("statusMayAuthorizeMutation") is not False:
        raise ValueError("STATUS_CHANNEL_MUST_NOT_AUTHORIZE_MUTATION")
    mapping={
        "NOT_STARTED":"NOT_STARTED",
        "IN_PROGRESS":"OPEN",
        "BLOCKED":"BLOCKED",
        "WAITING_EXTERNAL":"BLOCKED",
        "READY_FOR_INTEGRATION":"READY_FOR_HANDOFF",
        "DONE":"CLOSED",
        "FAILED":"BLOCKED",
    }
    blockers=list(status.get("blockerCodes") or [])
    if source=="WAITING_EXTERNAL": blockers.append("WAITING_EXTERNAL")
    if source=="FAILED": blockers.append("FAILURE")
    return LifecycleNormalization(mapping[source],source,tuple(sorted(set(blockers))),False)

def assert_transition(previous:dict[str,Any]|None,current:dict[str,Any])->None:
    now=normalize_lifecycle(current)
    if previous is None: return
    before=normalize_lifecycle(previous)
    if before.canonical_state=="CLOSED" and now.canonical_state not in {"CLOSED","SUPERSEDED"}:
        raise ValueError("CLOSED_LIFECYCLE_REOPEN_FORBIDDEN")
    if before.canonical_state=="SUPERSEDED" and now.canonical_state!="SUPERSEDED":
        raise ValueError("SUPERSEDED_LIFECYCLE_REOPEN_FORBIDDEN")
