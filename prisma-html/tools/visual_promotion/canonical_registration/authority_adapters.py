from __future__ import annotations
import json
from pathlib import Path
from typing import Any

class AuthorityBindingError(ValueError):
    pass


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise AuthorityBindingError(f"EXPANDED_AUTHORITY_MISSING:{path}")
    rows=[]
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            value=json.loads(line)
        except Exception as exc:
            raise AuthorityBindingError(f"JSONL_INVALID:{path}") from exc
        if not isinstance(value,dict):
            raise AuthorityBindingError(f"JSONL_OBJECT_REQUIRED:{path}")
        rows.append(value)
    return rows


def _expanded_surface_indexes(repo_root: Path, surface: str) -> dict[str, dict[str, Any]]:
    base=repo_root/"prisma-html/authority/rifat/prisma-ui/visual-control/expanded"/surface
    def index(rows,key):
        return {str(row[key]):row for row in rows if isinstance(row.get(key),str) and row.get(key)}
    return {
        "routes":index(_load_jsonl(base/"routes.jsonl"),"route_id"),
        "componentOwners":index(_load_jsonl(base/"owners-componentOwners.jsonl"),"component_id"),
        "regionOwners":index(_load_jsonl(base/"owners-regionOwners.jsonl"),"region_id"),
        "slots":index(_load_jsonl(base/"editable-slots.jsonl"),"slot_unit_id"),
    }

def _load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AuthorityBindingError(f"JSON_INVALID:{path}") from exc

def rifat_indexes(repo_root: Path) -> dict[str, dict[str, Any]]:
    base = repo_root / "prisma-html/authority/rifat/prisma-ui"
    sources = {
        "surfaces": (base / "surfaces.json", "surfaces", "id"),
        "routes": (base / "routes.json", "routes", "route_id"),
        "componentOwners": (base / "visual-control/owners.json", "componentOwnerSamples", "component_id"),
        "cssOwners": (base / "visual-control/owners.json", "cssOwnerSamples", "owner_id"),
        "regionOwners": (base / "visual-control/owners.json", "regionOwnerSamples", "region_id"),
        "components": (base / "visual-control/components.json", "components", "component_id"),
        "slots": (base / "visual-control/editable-slots.json", "slotUnitSamples", "slot_unit_id"),
    }
    indexes: dict[str, dict[str, Any]] = {}
    for name,(path,section,key) in sources.items():
        doc=_load(path)
        indexes[name]={str(item[key]):item for item in doc.get(section,[]) if isinstance(item,dict) and isinstance(item.get(key),str)}
    layers=_load(base/"visual-control/layers.json")
    layer_records=[item for item in [*layers.get("layerSamples",[]),*layers.get("certifiedLayers",[])] if isinstance(item,dict) and isinstance(item.get("layer_id"),str)]
    indexes["layers"]={str(item["layer_id"]):item for item in layer_records}
    indexes["layerEvidence"]=layer_records
    return indexes

def validate_exact_binding(repo_root: Path, binding: dict[str, Any], target_id: str, expected_surface: str, expected_meaning_id: str) -> None:
    if not isinstance(binding,dict): raise AuthorityBindingError("EXACT_BINDING_REQUIRED")
    if binding.get("status") not in {None,"RESOLVED"}: raise AuthorityBindingError("EXACT_BINDING_NOT_RESOLVED")
    targets=binding.get("targets")
    if not isinstance(targets,list) or len(targets)!=1: raise AuthorityBindingError("EXACT_BINDING_MUST_HAVE_ONE_TARGET")
    target=targets[0]
    required=("ownerId","routeId","regionId","slotId","componentUiId","layerId","implementationLayerId")
    if not isinstance(target,dict) or target.get("targetId")!=target_id: raise AuthorityBindingError("EXACT_BINDING_TARGET_ID_MISMATCH")
    if any(not isinstance(target.get(f),str) or not target[f] or target[f]=="*" for f in required): raise AuthorityBindingError("EXACT_BINDING_TRACE_FIELDS_MUST_BE_EXPLICIT")
    if target.get("missingBindings"): raise AuthorityBindingError("EXACT_BINDING_HAS_MISSING_FIELDS")
    selector=binding.get("selector") or {}
    if selector.get("surfaceId")!=expected_surface: raise AuthorityBindingError("EXACT_BINDING_SURFACE_MISMATCH")
    if selector.get("neutralMeaningId")!=expected_meaning_id: raise AuthorityBindingError("EXACT_BINDING_SEMANTIC_MISMATCH")
    if not isinstance(target.get("selector"),str) or not target["selector"]: raise AuthorityBindingError("EXACT_BINDING_SELECTOR_REQUIRED")
    idx=rifat_indexes(repo_root)
    if expected_surface not in idx["surfaces"]: raise AuthorityBindingError(f"EXACT_BINDING_ORPHAN_SURFACE:{expected_surface}")
    expanded=_expanded_surface_indexes(repo_root,expected_surface)
    lookup={"ownerId":"componentOwners","routeId":"routes","regionId":"regionOwners","slotId":"slots","componentUiId":"componentOwners","layerId":"layers"}
    for field,bucket in lookup.items():
        authority_index=expanded[bucket] if bucket in expanded else idx[bucket]
        if target[field] not in authority_index: raise AuthorityBindingError(f"EXACT_BINDING_ORPHAN_{field.upper()}:{target[field]}")
    route_record=expanded["routes"][target["routeId"]]
    if route_record.get("surface")!=expected_surface:
        raise AuthorityBindingError("EXACT_BINDING_ROUTE_SURFACE_MISMATCH")
    component_record=expanded["componentOwners"][target["componentUiId"]]
    region_record=expanded["regionOwners"][target["regionId"]]
    slot_record=expanded["slots"][target["slotId"]]
    owner_record=expanded["componentOwners"][target["ownerId"]]
    for label,record in (("OWNER",owner_record),("COMPONENT",component_record),("REGION",region_record),("SLOT",slot_record)):
        if record.get("surface")!=expected_surface:
            raise AuthorityBindingError(f"EXACT_BINDING_{label}_SURFACE_MISMATCH")
    owner_css=target.get("ownerCssId")
    if owner_css is not None and owner_css not in idx["cssOwners"]: raise AuthorityBindingError(f"EXACT_BINDING_ORPHAN_OWNERCSSID:{owner_css}")
    implementation_layer=target["implementationLayerId"]
    evidence_matches=[
        row for row in idx["layerEvidence"]
        if row.get("surface")==expected_surface
        and row.get("layer_id")==target["layerId"]
        and row.get("implementationLayerId")==implementation_layer
        and row.get("selector")==target["selector"]
    ]
    if len(evidence_matches)!=1:
        raise AuthorityBindingError("EXACT_BINDING_IMPLEMENTATION_LAYER_MUST_MATCH_RIFAT_EVIDENCE")
