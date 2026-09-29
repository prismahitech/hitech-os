from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .engine import CanonicalRegistrationError, current_repo_head, file_sha256, sha256_json

NDC_ROOT = Path("apps/terminal-de-venta-system/docs/ndc/registry")
IDENTITY_ROOT = Path("prisma-html/authority/rifat/identity/registries")
RIFAT_PATHS = (
    "prisma-html/authority/rifat/prisma-ui/routes.json",
    "prisma-html/authority/rifat/prisma-ui/surfaces.json",
    "prisma-html/authority/rifat/prisma-ui/visual-control/owners.json",
    "prisma-html/authority/rifat/prisma-ui/visual-control/components.json",
    "prisma-html/authority/rifat/prisma-ui/visual-control/editable-slots.json",
    "prisma-html/authority/rifat/prisma-ui/visual-control/layers.json",
)
PROJECTION_PATHS = ("prisma-html/authority/rifat/visual-source-manifest.json",)


def _paths(root: Path, paths: Iterable[str | Path]) -> list[Path]:
    result = []
    for raw in paths:
        path = root / Path(raw)
        if not path.is_file():
            raise CanonicalRegistrationError(f"CURRENT_TRUTH_FILE_MISSING:{raw}")
        result.append(path)
    return sorted(set(result), key=lambda item: str(item).replace("\\", "/"))


def _bundle(root: Path, paths: Iterable[str | Path]) -> tuple[str, list[dict]]:
    rows = []
    for path in _paths(root, paths):
        rel = str(path.relative_to(root)).replace("\\", "/")
        rows.append({"path": rel, "sha256": file_sha256(path), "bytes": path.stat().st_size})
    return sha256_json(rows), rows


def _glob_bundle(root: Path, directory: Path) -> tuple[str, list[dict]]:
    base = root / directory
    if not base.is_dir():
        raise CanonicalRegistrationError(f"CURRENT_TRUTH_DIRECTORY_MISSING:{directory}")
    return _bundle(root, [p for p in base.rglob("*.json") if p.is_file()])


def capture_current_truth(
    repo_root: Path,
    *,
    target_id: str,
    repo_head: str | None = None,
    authority_mesh_path: str | None = None,
    layer_map_path: str | None = None,
) -> dict:
    head = repo_head or current_repo_head(repo_root)
    if len(head) != 40 or any(ch not in "0123456789abcdef" for ch in head):
        raise CanonicalRegistrationError("CURRENT_TRUTH_HEAD_INVALID")

    from visual_application.target_index import build_index

    target_index = build_index(repo_root)
    target_rows = [
        row for row in target_index.get("records", [])
        if isinstance(row, dict) and row.get("targetId") == target_id
    ]
    if len(target_rows) != 1:
        raise CanonicalRegistrationError(f"CURRENT_TRUTH_TARGET_NOT_EXACT:{target_id}")
    target_row = target_rows[0]

    target_index_digest, target_index_sources = _glob_bundle(
        repo_root, Path("authority/rifat/prisma-ui/visual-control/target-index")
    )
    identity_digest, identity_sources = _glob_bundle(repo_root, IDENTITY_ROOT)
    rifat_digest, rifat_sources = _bundle(repo_root, RIFAT_PATHS)
    ndc_digest, ndc_sources = _glob_bundle(repo_root, NDC_ROOT)
    projection_digest, projection_sources = _bundle(repo_root, PROJECTION_PATHS)

    if not authority_mesh_path:
        raise CanonicalRegistrationError("CURRENT_TRUTH_AUTHORITY_MESH_PATH_REQUIRED")
    if not layer_map_path:
        raise CanonicalRegistrationError("CURRENT_TRUTH_LAYER_MAP_PATH_REQUIRED")

    authority_mesh_digest, authority_mesh_sources = _bundle(repo_root, [authority_mesh_path])
    layer_map_digest, layer_map_sources = _bundle(repo_root, [layer_map_path])

    snapshot = {
        "schema": "prisma.visual.current-truth-snapshot.v1",
        "repoHead": head,
        "targetIndexDigest": target_index_digest,
        "identityDigest": identity_digest,
        "rifatDigest": rifat_digest,
        "ndcDigest": ndc_digest,
        "projectionDigest": projection_digest,
        "authorityMeshDigest": authority_mesh_digest,
        "layerMapDigest": layer_map_digest,
        "targetEvidenceDigest": sha256_json(target_row),
        "sources": {
            "targetIndex": target_index_sources,
            "identity": identity_sources,
            "rifat": rifat_sources,
            "ndc": ndc_sources,
            "projection": projection_sources,
            "authorityMesh": authority_mesh_sources,
            "layerMap": layer_map_sources,
        },
    }
    snapshot["snapshotId"] = sha256_json(snapshot)
    return snapshot
