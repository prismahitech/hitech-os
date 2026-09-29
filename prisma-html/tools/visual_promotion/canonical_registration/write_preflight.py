from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class WritePreflight:
    status:str
    writer_kind:str
    authority_domain:str
    expected_head:str
    source_digest:str
    target_id:str
    mutation_allowed:bool

class WritePreflightError(ValueError): pass

def _sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def validate_write_preflight(repo_root:Path, context:dict[str,Any])->WritePreflight:
    expected=context.get("expectedCurrentHead")
    actual=context.get("currentHead")
    if not isinstance(expected,str) or len(expected)!=40: raise WritePreflightError("EXPECTED_HEAD_REQUIRED")
    if expected!=actual: raise WritePreflightError("STALE_HEAD")
    if context.get("automaticSemanticInference") is not False: raise WritePreflightError("AUTOMATIC_SEMANTIC_INFERENCE_FORBIDDEN")
    if context.get("automaticApplicationSource") is not False: raise WritePreflightError("AUTOMATIC_APPLICATION_SOURCE_FORBIDDEN")
    writer=context.get("writerKind")
    domain=context.get("authorityDomain")
    if writer != "CANONICAL_REGISTRATION": raise WritePreflightError("WRITER_KIND_INVALID")
    if domain != "canonical-registration": raise WritePreflightError("AUTHORITY_DOMAIN_INVALID")
    target_id=context.get("targetId")
    if not isinstance(target_id,str) or not target_id.startswith("TGT."): raise WritePreflightError("TARGET_ID_REQUIRED")
    source_path=context.get("sourcePath")
    source_digest=context.get("sourceDigest")
    if not isinstance(source_path,str) or not isinstance(source_digest,str) or len(source_digest)!=64: raise WritePreflightError("SOURCE_PIN_REQUIRED")
    path=(repo_root/source_path).resolve()
    root=repo_root.resolve()
    if path!=root and root not in path.parents: raise WritePreflightError("SOURCE_PATH_ESCAPE")
    if not path.is_file() or path.is_symlink(): raise WritePreflightError("SOURCE_FILE_NOT_FOUND")
    if _sha(path)!=source_digest: raise WritePreflightError("SOURCE_DRIFT")
    if context.get("runtimeMutationAllowed") is not False: raise WritePreflightError("RUNTIME_MUTATION_FORBIDDEN")
    return WritePreflight("PASS",writer,domain,expected,source_digest,target_id,True)
