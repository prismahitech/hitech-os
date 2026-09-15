from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .source_set_verifier import canonical_json

PROCESS_MODEL_REL = Path("prisma-html/governance/visual-operating-graph/PRISMA_VISUAL_OPERATING_GRAPH_PROCESS_MODEL.registry.json")
FOUNDATION_REL = Path("prisma-html/governance/visual-operating-graph/FOUNDATION_MANIFEST.json")
SCHEMA_REL = Path("prisma-html/governance/visual-operating-graph/PRISMA_VISUAL_OPERATING_GRAPH_SCHEMA.json")
LEDGER_REL = Path("PRISMA Factory Ledger/PRISMA_FACTORY_LEDGER.json")
SURFACES_REL = Path("apps/terminal-de-venta-system/.prisma-ui/surfaces.json")
CONTROL_PLANE_REL = Path("prisma-html/governance/visual-promotion/contracts/control-plane.contract.json")
STATUS_INDEX_REL = Path("apps/terminal-de-venta-system/docs/ops/visual-promotion-parallel-status/STATUS_INDEX.json")
GRAPH_SCHEMA = "prisma.visual-operating-graph.v1"


class GraphBuildBlocked(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise GraphBuildBlocked(f"JSON_OBJECT_REQUIRED:{path.as_posix()}")
    return value


def _surface_ids(value: Any) -> list[str]:
    if isinstance(value, dict):
        if isinstance(value.get("surfaces"), list):
            value = value["surfaces"]
        elif isinstance(value.get("surfaces"), dict):
            return sorted(str(key) for key in value["surfaces"])
        else:
            return []
    if not isinstance(value, list):
        return []
    out: set[str] = set()
    for row in value:
        if isinstance(row, str):
            out.add(row)
        elif isinstance(row, dict):
            candidate = row.get("id") or row.get("surfaceKey") or row.get("surface")
            if candidate:
                out.add(str(candidate))
    return sorted(out)


def _add_node(store: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    node_id = str(node["id"])
    prior = store.get(node_id)
    if prior is not None and canonical_json(prior) != canonical_json(node):
        raise GraphBuildBlocked(f"NODE_ID_COLLISION:{node_id}")
    store[node_id] = node


def _add_edge(store: dict[str, dict[str, Any]], edge: dict[str, Any]) -> None:
    key = canonical_json(edge)
    store[key] = edge


def _node(node_id: str, node_type: str, domain: str, source_refs: list[str], payload: dict[str, Any], canonicality: str = "CANONICAL_DERIVED") -> dict[str, Any]:
    return {
        "id": node_id,
        "type": node_type,
        "canonicality": canonicality,
        "authorityDomain": domain,
        "sourceRefs": sorted(set(source_refs)),
        "payload": payload,
        "gaps": [],
        "authorizationGranted": False,
    }


def _edge(source: str, target: str, relation: str, domain: str, source_refs: list[str], canonicality: str = "CANONICAL_DERIVED") -> dict[str, Any]:
    return {
        "from": source,
        "to": target,
        "relation": relation,
        "canonicality": canonicality,
        "authorityDomain": domain,
        "sourceRefs": sorted(set(source_refs)),
        "evidenceRefs": [],
        "authorizationGranted": False,
    }


def _source_node_id(row: dict[str, Any]) -> str:
    role = str(row.get("role") or "")
    path = str(row.get("path") or "")
    domain = str(row.get("authorityDomain") or "unknown")
    kind = "DOCUMENT" if role.startswith("manual-") else ("EVIDENCE" if "evidence" in role else "AUTHORITY")
    return f"{kind}:{domain}:{path}"


def _source_node_type(row: dict[str, Any]) -> str:
    role = str(row.get("role") or "")
    if role.startswith("manual-"):
        return "DOCUMENT"
    if "evidence" in role:
        return "EVIDENCE"
    return "AUTHORITY"


def validate_graph_contract(graph: dict[str, Any], schema: dict[str, Any]) -> None:
    defs = schema.get("$defs") if isinstance(schema, dict) else {}
    node_types = set(((defs or {}).get("nodeType") or {}).get("enum") or [])
    relations = set(((defs or {}).get("relation") or {}).get("enum") or [])
    canonicalities = set(((defs or {}).get("canonicality") or {}).get("enum") or [])
    if graph.get("schema") != GRAPH_SCHEMA:
        raise GraphBuildBlocked("GRAPH_SCHEMA_MISMATCH")
    if graph.get("productionCertified") is not False:
        raise GraphBuildBlocked("PRODUCTION_CERTIFIED_MUST_BE_FALSE")
    node_ids: set[str] = set()
    for node in graph.get("nodes") or []:
        if node.get("type") not in node_types:
            raise GraphBuildBlocked(f"NODE_TYPE_INVALID:{node.get('type')}")
        if node.get("canonicality") not in canonicalities:
            raise GraphBuildBlocked(f"NODE_CANONICALITY_INVALID:{node.get('id')}")
        if not node.get("sourceRefs"):
            raise GraphBuildBlocked(f"NODE_PROVENANCE_REQUIRED:{node.get('id')}")
        if node.get("authorizationGranted") is not False:
            raise GraphBuildBlocked(f"NODE_CANNOT_AUTHORIZE:{node.get('id')}")
        if node.get("id") in node_ids:
            raise GraphBuildBlocked(f"DUPLICATE_NODE:{node.get('id')}")
        node_ids.add(str(node.get("id")))
    for edge in graph.get("edges") or []:
        if edge.get("relation") not in relations:
            raise GraphBuildBlocked(f"EDGE_RELATION_INVALID:{edge.get('relation')}")
        if edge.get("canonicality") not in canonicalities:
            raise GraphBuildBlocked("EDGE_CANONICALITY_INVALID")
        if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
            raise GraphBuildBlocked(f"EDGE_ENDPOINT_MISSING:{edge.get('from')}:{edge.get('to')}")
        if not edge.get("sourceRefs"):
            raise GraphBuildBlocked("EDGE_PROVENANCE_REQUIRED")
        if edge.get("authorizationGranted") is not False:
            raise GraphBuildBlocked("EDGE_CANNOT_AUTHORIZE")
