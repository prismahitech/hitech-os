from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

REQUIRED_RUNTIME_PASS={"PASS"}
SUPPORTED_STATES={"PASS","FAIL","NOT_RUN"}

class RuntimeEvidenceError(ValueError):
    pass

@dataclass(frozen=True)
class RuntimeCertification:
    certification_state:str
    target_id:str
    evidence_digest:str
    change_assurance_ready:bool

def _digest(value:Any)->str:
    import json
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def _require_state(value:dict[str,Any], field:str)->str:
    state=value.get(field)
    if state not in SUPPORTED_STATES:
        raise RuntimeEvidenceError(f"{field}_INVALID")
    return state

def validate_runtime_evidence(evidence:dict[str,Any]) -> RuntimeCertification:
    if evidence.get("schema")!="prisma.visual.runtime-evidence.v1":
        raise RuntimeEvidenceError("RUNTIME_EVIDENCE_SCHEMA_INVALID")
    target=evidence.get("target") or {}
    if not isinstance(target.get("targetId"),str) or not target["targetId"]:
        raise RuntimeEvidenceError("TARGET_ID_REQUIRED")
    if not isinstance(target.get("censusTargetId"),str) or not target["censusTargetId"].startswith("TGT.CENSUS."):
        raise RuntimeEvidenceError("CENSUS_TARGET_ID_REQUIRED")
    if not isinstance(target.get("route"),str) or not target["route"]:
        raise RuntimeEvidenceError("ROUTE_REQUIRED")
    viewport=evidence.get("viewport") or {}
    browser=evidence.get("browser") or {}
    for field in ("width","height"):
        if not isinstance(viewport.get(field),int) or viewport[field]<=0:
            raise RuntimeEvidenceError(f"VIEWPORT_{field.upper()}_INVALID")
    if not isinstance(browser.get("name"),str) or not browser["name"]:
        raise RuntimeEvidenceError("BROWSER_NAME_REQUIRED")
    build=evidence.get("build") or {}
    commit=build.get("commitSha")
    if not isinstance(commit,str) or len(commit)!=40:
        raise RuntimeEvidenceError("BUILD_COMMIT_REQUIRED")
    for artifact_name in ("before","after"):
        artifact=evidence.get(artifact_name) or {}
        if not isinstance(artifact.get("sha256"),str) or len(artifact["sha256"])!=64:
            raise RuntimeEvidenceError(f"{artifact_name.upper()}_ARTIFACT_DIGEST_REQUIRED")
        if not isinstance(artifact.get("path"),str) or not artifact["path"]:
            raise RuntimeEvidenceError(f"{artifact_name.upper()}_ARTIFACT_PATH_REQUIRED")
    source_projection=evidence.get("sourceProjection") or {}
    if not isinstance(source_projection.get("commitSha"),str) or len(source_projection["commitSha"])!=40:
        raise RuntimeEvidenceError("SOURCE_PROJECTION_COMMIT_REQUIRED")
    if source_projection["commitSha"] != commit:
        raise RuntimeEvidenceError("SOURCE_PROJECTION_COMMIT_MISMATCH")

    runtime_state=_require_state(evidence,"runtimeState")
    console_state=_require_state(evidence,"consoleState")
    network_state=_require_state(evidence,"networkState")
    geometry=_require_state(evidence,"geometryVerdict")
    accessibility=_require_state(evidence,"accessibilityVerdict")
    visual=_require_state(evidence,"visualVerdict")

    if evidence.get("gvaeVerifyState") not in {None,*SUPPORTED_STATES}:
        raise RuntimeEvidenceError("GVAE_VERIFY_STATE_INVALID")

    covered={
        "target":target,
        "viewport":viewport,
        "browser":browser,
        "build":build,
        "before":evidence["before"],
        "after":evidence["after"],
        "sourceProjection":source_projection,
        "runtimeState":runtime_state,
        "consoleState":console_state,
        "networkState":network_state,
        "geometryVerdict":geometry,
        "accessibilityVerdict":accessibility,
        "visualVerdict":visual,
    }
    evidence_digest=_digest(covered)

    all_pass=all(x=="PASS" for x in (runtime_state,console_state,network_state,geometry,accessibility,visual))
    if all_pass:
        state="VISUAL_CERTIFIED"
        ready=True
    else:
        state="PENDING_RUNTIME_CERTIFICATION"
        ready=False

    return RuntimeCertification(state,target["targetId"],evidence_digest,ready)

def build_change_assurance_handoff(evidence:dict[str,Any], certification:RuntimeCertification)->dict[str,Any]:
    if certification.certification_state!="VISUAL_CERTIFIED":
        raise RuntimeEvidenceError("CHANGE_ASSURANCE_HANDOFF_REQUIRES_VISUAL_CERTIFIED")
    return {
        "schema":"prisma.visual.runtime-evidence.change-assurance-handoff.v1",
        "targetId":certification.target_id,
        "evidenceDigest":certification.evidence_digest,
        "changeAssuranceReady":True,
        "sourceBuildCommitSha":(evidence.get("build") or {}).get("commitSha"),
    }
