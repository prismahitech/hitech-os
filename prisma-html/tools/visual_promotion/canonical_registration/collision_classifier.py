from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .engine import CanonicalRegistrationError
from .policy import collision_code

class CollisionClassificationError(CanonicalRegistrationError):
    pass

def _load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CollisionClassificationError(f"JSON_INVALID:{path}") from exc

def _physical_signature(target: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(target.get(field) for field in (
        "ownerId", "routeId", "regionId", "slotId", "componentUiId",
        "selector", "implementationLayerId",
    ))

def classify_collisions(
    repo_root: Path,
    *,
    target_id: str,
    surface_key: str,
    semantic_meaning_id: str,
    proposed_binding_target: dict[str, Any],
    proposed_binding_id: str | None,
    proposed_layer_id: str | None,
    projection_expectation: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    collisions: list[dict[str, Any]] = []

    target_index_records: list[dict[str, Any]] = []
    try:
        from visual_application.target_index import build_index
        target_index_records = [
            row for row in build_index(repo_root).get("records", [])
            if isinstance(row, dict)
        ]
    except Exception as exc:
        raise CollisionClassificationError("TARGET_INDEX_UNREADABLE") from exc

    exact = [row for row in target_index_records if row.get("targetId") == target_id]
    for row in exact:
        row_meaning = row.get("semanticMeaningId")
        if row_meaning and row_meaning != semantic_meaning_id:
            collisions.append({
                "code": collision_code("semantic"),
                "targetId": target_id,
                "existingMeaningId": row_meaning,
                "requestedMeaningId": semantic_meaning_id,
                "basis": "target-index.semanticMeaningId",
            })
        row_layer = row.get("layerId")
        if proposed_layer_id and row_layer and row_layer != proposed_layer_id:
            collisions.append({
                "code": collision_code("layer"),
                "targetId": target_id,
                "existingLayerId": row_layer,
                "requestedLayerId": proposed_layer_id,
                "basis": "target-index.layerId",
            })
        row_binding = row.get("bindingId")
        if proposed_binding_id and row_binding and row_binding != proposed_binding_id:
            collisions.append({
                "code": collision_code("binding"),
                "targetId": target_id,
                "existingBindingId": row_binding,
                "requestedBindingId": proposed_binding_id,
                "basis": "target-index.bindingId",
            })
        if (
            row.get("semanticMeaningId") in (None, semantic_meaning_id)
            and (not proposed_layer_id or row.get("layerId") in (None, proposed_layer_id))
            and (not proposed_binding_id or row.get("bindingId") in (None, proposed_binding_id))
        ):
            collisions.append({
                "code": collision_code("exact"),
                "targetId": target_id,
                "basis": "target-index.exact-record",
            })

    bindings_path = repo_root / "prisma-html/authority/rifat/identity/registries/element-bindings.registry.json"
    bindings = _load(bindings_path)
    proposed_signature = _physical_signature(proposed_binding_target)
    for binding in bindings.get("bindings", []):
        if not isinstance(binding, dict):
            continue
        existing_binding_id = binding.get("bindingId")
        for existing_target in binding.get("targets", []):
            if not isinstance(existing_target, dict):
                continue
            existing_signature = _physical_signature(existing_target)
            if existing_signature != proposed_signature:
                continue
            if existing_target.get("targetId") == target_id and existing_binding_id == proposed_binding_id:
                continue
            existing_selector = binding.get("selector") or {}
            if existing_selector.get("surfaceId") != surface_key:
                continue
            existing_meaning = existing_selector.get("neutralMeaningId")
            if existing_meaning and existing_meaning != semantic_meaning_id:
                collisions.append({
                    "code": collision_code("semantic"),
                    "existingBindingId": existing_binding_id,
                    "existingTargetId": existing_target.get("targetId"),
                    "existingMeaningId": existing_meaning,
                    "requestedMeaningId": semantic_meaning_id,
                    "basis": "identity.binding.selector.neutralMeaningId",
                })
            if existing_binding_id != proposed_binding_id:
                collisions.append({
                    "code": collision_code("binding"),
                    "existingBindingId": existing_binding_id,
                    "requestedBindingId": proposed_binding_id,
                    "existingTargetId": existing_target.get("targetId"),
                    "basis": "identity.binding.physical-signature",
                })

    expectation = projection_expectation or {}
    record = exact[0] if exact else None
    if record is not None:
        expected_source = expectation.get("sourceSha256")
        expected_output = expectation.get("outputSha256")
        if expected_source and record.get("sourceSha256") and record["sourceSha256"] != expected_source:
            collisions.append({
                "code": collision_code("projection"),
                "targetId": target_id,
                "existingSourceSha256": record["sourceSha256"],
                "requestedSourceSha256": expected_source,
                "basis": "target-index.sourceSha256",
            })
        if expected_output and record.get("outputSha256") and record["outputSha256"] != expected_output:
            collisions.append({
                "code": collision_code("projection"),
                "targetId": target_id,
                "existingOutputSha256": record["outputSha256"],
                "requestedOutputSha256": expected_output,
                "basis": "target-index.outputSha256",
            })

    unique: dict[str, dict[str, Any]] = {}
    for item in collisions:
        key = json.dumps(item, sort_keys=True, separators=(",", ":"))
        unique[key] = item
    return [unique[key] for key in sorted(unique)]
