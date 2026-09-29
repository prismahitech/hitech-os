from __future__ import annotations
from pathlib import Path
from typing import Iterable
from .engine import CanonicalRegistrationError, current_repo_head, file_sha256, sha256_json

NDC_ROOT=Path("apps/terminal-de-venta-system/docs/ndc/registry")
IDENTITY_ROOT=Path("prisma-html/authority/rifat/identity/registries")
RIFAT_PATHS=("prisma-html/authority/rifat/prisma-ui/routes.json","prisma-html/authority/rifat/prisma-ui/surfaces.json","prisma-html/authority/rifat/prisma-ui/visual-control/owners.json","prisma-html/authority/rifat/prisma-ui/visual-control/components.json","prisma-html/authority/rifat/prisma-ui/visual-control/editable-slots.json","prisma-html/authority/rifat/prisma-ui/visual-control/layers.json")
PROJECTION_PATHS=("prisma-html/authority/rifat/visual-source-manifest.json",)

def _paths(root:Path, paths:Iterable[str|Path])->list[Path]:
    out=[]
    root_resolved=root.resolve()
    for raw in paths:
        path=(root/Path(raw)).resolve()
        if path!=root_resolved and root_resolved not in path.parents:
            raise CanonicalRegistrationError(f"CURRENT_TRUTH_PATH_ESCAPE:{raw}")
        if not path.is_file(): raise CanonicalRegistrationError(f"CURRENT_TRUTH_FILE_MISSING:{raw}")
        out.append(path)
    return sorted(set(out),key=lambda p:str(p).replace("\\","/"))

def _bundle(root:Path, paths:Iterable[str|Path])->tuple[str,list[dict]]:
    rows=[]
    for p in _paths(root,paths):
        rel=str(p.relative_to(root)).replace("\\","/")
        rows.append({"path":rel,"sha256":file_sha256(p),"bytes":p.stat().st_size})
    return sha256_json(rows),rows

def _bucket_allowed_path(bucket:str, relative:str)->bool:
    path=Path(relative)
    if path.is_absolute() or ".." in path.parts:
        return False
    normalized=path.as_posix()
    if bucket=="targetIndex":
        return normalized.startswith("prisma-html/authority/rifat/prisma-ui/visual-control/target-index/") and normalized.endswith(".json")
    if bucket=="identity":
        return normalized.startswith("prisma-html/authority/rifat/identity/registries/") and normalized.endswith(".json")
    if bucket=="ndc":
        return normalized.startswith(NDC_ROOT.as_posix()+"/") and normalized.endswith(".json")
    if bucket=="rifat":
        return normalized in set(RIFAT_PATHS)
    if bucket=="projection":
        return normalized in set(PROJECTION_PATHS)
    return bucket in {"authorityMesh","layerMap"}

def _glob_bundle(root:Path, directory:Path)->tuple[str,list[dict]]:
    base=root/directory
    if not base.is_dir(): raise CanonicalRegistrationError(f"CURRENT_TRUTH_DIRECTORY_MISSING:{directory}")
    return _bundle(root,[p for p in base.rglob("*.json") if p.is_file()])

def capture_current_truth(repo_root:Path, *, evidence_target_id:str, repo_head:str|None=None, authority_mesh_path:str|None=None, layer_map_path:str|None=None, authority_mesh_digest:str|None=None, layer_map_digest:str|None=None)->dict:
    head=repo_head or current_repo_head(repo_root)
    from visual_application.target_index import build_index
    matches=[r for r in build_index(repo_root).get("records",[]) if isinstance(r,dict) and r.get("targetId")==evidence_target_id]
    if len(matches)!=1: raise CanonicalRegistrationError(f"CURRENT_TRUTH_TARGET_NOT_EXACT:{evidence_target_id}")
    target_row=matches[0]
    tid,ts=_glob_bundle(repo_root,Path("prisma-html/authority/rifat/prisma-ui/visual-control/target-index"))
    iid,isrc=_glob_bundle(repo_root,IDENTITY_ROOT)
    rid,rsrc=_bundle(repo_root,RIFAT_PATHS)
    nd,nsrc=_glob_bundle(repo_root,NDC_ROOT)
    pd,psrc=_bundle(repo_root,PROJECTION_PATHS)
    if authority_mesh_path: am,amsrc=_bundle(repo_root,[authority_mesh_path])
    elif authority_mesh_digest: am,amsrc=authority_mesh_digest,[{"externalRef":"authority-mesh","sha256":authority_mesh_digest}]
    else: raise CanonicalRegistrationError("CURRENT_TRUTH_AUTHORITY_MESH_REQUIRED")
    if layer_map_path: lm,lmsrc=_bundle(repo_root,[layer_map_path])
    elif layer_map_digest: lm,lmsrc=layer_map_digest,[{"externalRef":"layer-map","sha256":layer_map_digest}]
    else: raise CanonicalRegistrationError("CURRENT_TRUTH_LAYER_MAP_REQUIRED")
    snap={"schema":"prisma.visual.current-truth-snapshot.v1","repoHead":head,"targetIndexDigest":tid,"identityDigest":iid,"rifatDigest":rid,"ndcDigest":nd,"projectionDigest":pd,"authorityMeshDigest":am,"layerMapDigest":lm,"targetEvidenceDigest":sha256_json(target_row),"evidenceTargetId":evidence_target_id,"sources":{"targetIndex":ts,"identity":isrc,"rifat":rsrc,"ndc":nsrc,"projection":psrc,"authorityMesh":amsrc,"layerMap":lmsrc}}
    snap["snapshotId"]=sha256_json(snap)
    return snap

def verify_current_truth(repo_root:Path, snapshot:dict, *, evidence_target_id:str)->None:
    if snapshot.get("schema")!="prisma.visual.current-truth-snapshot.v1": raise CanonicalRegistrationError("CURRENT_TRUTH_SCHEMA_INVALID")
    if snapshot.get("evidenceTargetId")!=evidence_target_id: raise CanonicalRegistrationError("CURRENT_TRUTH_EVIDENCE_TARGET_MISMATCH")
    sid=snapshot.get("snapshotId")
    if not sid or sid!=sha256_json({k:v for k,v in snapshot.items() if k!="snapshotId"}): raise CanonicalRegistrationError("CURRENT_TRUTH_SNAPSHOT_ID_INVALID")
    sources=snapshot.get("sources") or {}
    fields={"targetIndex":"targetIndexDigest","identity":"identityDigest","rifat":"rifatDigest","ndc":"ndcDigest","projection":"projectionDigest","authorityMesh":"authorityMeshDigest","layerMap":"layerMapDigest"}
    canonical_internal={"targetIndex","identity","rifat","ndc","projection"}
    for bucket,field in fields.items():
        rows=sources.get(bucket)
        if not isinstance(rows,list) or not rows:
            raise CanonicalRegistrationError(f"CURRENT_TRUTH_SOURCE_SET_MISSING:{bucket}")

        if bucket in canonical_internal:
            if any(isinstance(row,dict) and row.get("externalRef") for row in rows):
                raise CanonicalRegistrationError(f"CURRENT_TRUTH_EXTERNAL_REF_FOR_CANONICAL_BUCKET:{bucket}")
            if bucket=="targetIndex":
                expected_digest,expected_rows=_glob_bundle(
                    repo_root,
                    Path("prisma-html/authority/rifat/prisma-ui/visual-control/target-index"),
                )
            elif bucket=="identity":
                expected_digest,expected_rows=_glob_bundle(repo_root,IDENTITY_ROOT)
            elif bucket=="ndc":
                expected_digest,expected_rows=_glob_bundle(repo_root,NDC_ROOT)
            elif bucket=="rifat":
                expected_digest,expected_rows=_bundle(repo_root,RIFAT_PATHS)
            else:
                expected_digest,expected_rows=_bundle(repo_root,PROJECTION_PATHS)
            normalized=[]
            for row in rows:
                if not isinstance(row,dict):
                    raise CanonicalRegistrationError(f"CURRENT_TRUTH_SOURCE_ROW_INVALID:{bucket}")
                relative=str(row.get("path","") or "")
                if not _bucket_allowed_path(bucket,relative):
                    raise CanonicalRegistrationError(f"CURRENT_TRUTH_UNEXPECTED_SOURCE_PATH:{bucket}:{relative}")
                normalized.append({
                    "path":relative,
                    "sha256":row.get("sha256"),
                    "bytes":row.get("bytes"),
                })
            normalized.sort(key=lambda x:x["path"])
            if normalized!=expected_rows:
                raise CanonicalRegistrationError(f"CURRENT_TRUTH_SOURCE_SET_DRIFT:{bucket}")
            if snapshot.get(field)!=expected_digest:
                raise CanonicalRegistrationError(f"CURRENT_TRUTH_DIGEST_DRIFT:{bucket}")
            continue

        actual=[]
        for row in rows:
            if not isinstance(row,dict): raise CanonicalRegistrationError(f"CURRENT_TRUTH_SOURCE_ROW_INVALID:{bucket}")
            if row.get("externalRef"):
                actual.append({"externalRef":row["externalRef"],"sha256":row["sha256"]})
            else:
                relative=str(row.get("path","") or "")
                if not _bucket_allowed_path(bucket,relative):
                    raise CanonicalRegistrationError(f"CURRENT_TRUTH_UNEXPECTED_SOURCE_PATH:{bucket}:{relative}")
                raw_path=repo_root/relative
                if raw_path.is_symlink():
                    raise CanonicalRegistrationError(f"CURRENT_TRUTH_SOURCE_SYMLINK:{bucket}:{relative}")
                path=raw_path.resolve()
                root=repo_root.resolve()
                if path!=root and root not in path.parents:
                    raise CanonicalRegistrationError(f"CURRENT_TRUTH_PATH_ESCAPE:{relative}")
                if not path.is_file(): raise CanonicalRegistrationError(f"CURRENT_TRUTH_FILE_MISSING:{relative}")
                actual.append({"path":relative,"sha256":file_sha256(path),"bytes":path.stat().st_size})
        actual.sort(key=lambda x:str(x.get("path") or x.get("externalRef")))
        if len(actual)==1 and "externalRef" in actual[0]:
            if actual[0].get("sha256") != snapshot.get(field):
                raise CanonicalRegistrationError(f"CURRENT_TRUTH_DIGEST_DRIFT:{bucket}")
        elif sha256_json(actual)!=snapshot.get(field):
            raise CanonicalRegistrationError(f"CURRENT_TRUTH_DIGEST_DRIFT:{bucket}")
    from visual_application.target_index import build_index
    matches=[r for r in build_index(repo_root).get("records",[]) if r.get("targetId")==evidence_target_id]
    if len(matches)!=1 or sha256_json(matches[0])!=snapshot.get("targetEvidenceDigest"): raise CanonicalRegistrationError("CURRENT_TRUTH_TARGET_EVIDENCE_DRIFT")
    if current_repo_head(repo_root)!=snapshot.get("repoHead"): raise CanonicalRegistrationError("CURRENT_TRUTH_REPO_HEAD_DRIFT")