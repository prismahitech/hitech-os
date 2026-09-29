from __future__ import annotations

from pathlib import Path
from typing import Any

class AuthorityBindingError(ValueError):
    pass

def _load(path: Path) -> dict[str, Any]:
    import json
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AuthorityBindingError(f"JSON_INVALID:{path}") from exc

def rifat_indexes(repo_root: Path) -> dict[str, dict[str, Any]]:
    base = repo_root / "prisma-html/authority/rifat/prisma-ui"
    sources = {
        "routes": (base / "routes.json", "routes", "route_id"),
        "componentOwners": (base / "visual-control/owners.json", "componentOwnerSamples", "component_id"),
        "cssOwners": (base / "visual-control/owners.json", "cssOwnerSamples", "owner_id"),
        "regionOwners": (base / "visual-control/owners.json", "regionOwnerSamples", "region_id"),
        "components": (base / "visual-control/components.json", "components", "component_id"),
        "slots": (base / "visual-control/editable-slots.json", "slotUnitSamples", "slot_unit_id"),
    }
    indexes: dict[str, dict[str, Any]] = {}
    for name, (path, section, key) in sources.items():
        document = _load(path)
        indexes[name] = {
            str(item[key]): item for item in document.get(section, [])
            if isinstance(item, dict) and isinstance(item.get(key), str)
        }
    layer_doc = _load(base / "visual-control/layers.json")
    indexes["layers"] = {
        str(item["layer_id"]): item
        for item in [*layer_doc.get("layerSamples", []), *layer_doc.get("certifiedLayers", [])]
        if isinstance(item, dict) and isinstance(item.get("layer_id"), str)
    }
    return indexes

def validate_exact_binding(repo_root: Path, binding: dict[str, Any], target_id: str) -> None:
    if not isinstance(binding, dict):
        raise AuthorityBindingError("EXACT_BINDING_REQUIRED")
    if binding.get("status") not in {None, "RESOLVED"}:
        raise AuthorityBindingError("EXACT_BINDING_NOT_RESOLVED")
    targets = binding.get("targets")
    if not isinstance(targets, list) or len(targets) != 1:
        raise AuthorityBindingError("EXACT_BINDING_MUST_HAVE_ONE_TARGET")
    target = targets[0]
    if not isinstance(target, dict) or target.get("targetId") != target_id:
        raise AuthorityBindingError("EXACT_BINDING_TARGET_ID_MISMATCH")
    fields = ("ownerId", "routeId", "regionId", "slotId", "componentUiId", "layerId")
    if any(not isinstance(target.get(field), str) or not target[field] or target[field] == "*" for field in fields):
        raise AuthorityBindingError("EXACT_BINDING_TRACE_FIELDS_MUST_BE_EXPLICIT")
    if target.get("missingBindings"):
        raise AuthorityBindingError("EXACT_BINDING_HAS_MISSING_FIELDS")
    indexes = rifat_indexes(repo_root)
    lookup = {
        "ownerId": "componentOwners",
        "routeId": "routes",
        "regionId": "regionOwners",
        "slotId": "slots",
        "componentUiId": "components",
        "layerId": "layers",
    }
    for field, bucket in lookup.items():
        if target[field] not in indexes[bucket]:
            raise AuthorityBindingError(f"EXACT_BINDING_ORPHAN_{field.upper()}:{target[field]}")
    owner_css = target.get("ownerCssId")
    if owner_css is not None and owner_css not in indexes["cssOwners"]:
        raise AuthorityBindingError(f"EXACT_BINDING_ORPHAN_OWNERCSSID:{owner_css}")
    selector = binding.get("selector") or {}
    if selector.get("surfaceId") not in {"tablet", "pc", "mobile", "shared-ui"}:
        raise AuthorityBindingError("EXACT_BINDING_SURFACE_INVALID")
    if not isinstance(target.get("selector"), str) or not target["selector"]:
        raise AuthorityBindingError("EXACT_BINDING_SELECTOR_REQUIRED")
