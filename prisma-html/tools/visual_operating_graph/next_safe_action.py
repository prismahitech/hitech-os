from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Iterable

from .graph_contract import PROCESS_MODEL_REL

NEXT_SCHEMA = "prisma.visual-operating-graph.next-safe-action.v1"
WHAT_IF_SCHEMA = "prisma.visual-operating-graph.what-if.v1"
TARGET_INDEX_REL = Path("prisma-html/authority/rifat/prisma-ui/visual-control/target-index/manifest.json")
TARGET_INDEX_ROOT = TARGET_INDEX_REL.parent
PROCESS_MODEL_DEFAULT = PROCESS_MODEL_REL

SAFE_ACTIONS = (
    "ACQUIRE_EVIDENCE",
    "RESOLVE_AUTHORITY_CONFLICT",
    "RESOLVE_SEMANTIC_AUTHORITY",
    "RESOLVE_BINDING",
    "RECONCILE_PROJECTION",
    "REVALIDATE_AUTHORITY",
    "STOP_BLOCKED",
)

# These aliases describe derived target-index blocker tokens conservatively.
# They do not create authority and fall back to UNCLASSIFIED_SOURCE_BLOCKER
# when the token is not explicitly covered here or by the canonical taxonomy.
TARGET_BLOCKER_ALIASES: dict[str, tuple[str, str]] = {
    "semantic": ("SEMANTIC_AUTHORITY_GAP", "identity"),
    "recipe": ("SEMANTIC_AUTHORITY_GAP", "identity"),
    "exact-binding": ("BINDING_GAP", "identity"),
    "binding": ("BINDING_GAP", "identity"),
    "adapter": ("APPLICATION_AUTHORITY_GAP", "identity"),
    "adapter-readiness": ("APPLICATION_AUTHORITY_GAP", "identity"),
    "layer-application-policy": ("APPLICATION_AUTHORITY_GAP", "work-entry-gvae"),
    "projection": ("PROJECTION_DEBT", "promotion-projection-readiness"),
    "projection-hash-drift": ("AUTHORITY_RECONCILIATION_REQUIRED", "visual-promotion"),
    "source-hash-drift": ("AUTHORITY_RECONCILIATION_REQUIRED", "rifat-prisma-ui"),
    "projection-mode": ("PROJECTION_DEBT", "promotion-projection-readiness"),
    "projection-policy": ("PROJECTION_DEBT", "promotion-projection-readiness"),
    "physical": ("PHYSICAL_DRIFT", "visual-promotion"),
    "region": ("LOCATION_CONFLICT", "visual-control"),
    "slot": ("LOCATION_CONFLICT", "visual-control"),
}

HYPOTHESIS_BLOCKERS: dict[str, tuple[str, ...]] = {
    "ndc_primary_meaning": ("ndc", "semantic"),
    "visual_meaning": ("semantic",),
    "valid_binding": ("exact-binding", "binding"),
    "application_layer_authority": ("layer-application-policy", "adapter", "adapter-readiness"),
    "projection_reconciled": (
        "projection",
        "projection-hash-drift",
        "source-hash-drift",
        "projection-mode",
        "projection-policy",
    ),
    "physical_reconciled": ("physical",),
    "location_reconciled": ("region", "slot"),
}

SOURCE_VERIFICATION_REFS = (
    "prisma-html/governance/visual-operating-graph/MASTER_MAP_SOURCESET.lock.json",
    "prisma-html/governance/visual-operating-graph/PRISMA_VISUAL_OPERATING_GRAPH_PROCESS_MODEL.registry.json",
)


class NextSafeActionBlocked(RuntimeError):
    """Raised when the requested read-only explanation cannot be proven."""


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _repo_root(repo_root: str | Path) -> Path:
    return Path(repo_root).resolve()


def _normalize_blockers(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({str(item).strip() for item in value if str(item).strip()})


def _canonical_node(graph: dict[str, Any], node_type: str, predicate=None) -> dict[str, Any] | None:
    rows = [
        row
        for row in graph.get("nodes") or []
        if isinstance(row, dict) and row.get("type") == node_type
    ]
    for row in rows:
        if predicate is None or predicate(row):
            return row
    return None


def _capability(graph: dict[str, Any]) -> dict[str, Any]:
    node = _canonical_node(graph, "CAPABILITY")
    if not node:
        raise NextSafeActionBlocked("CAPABILITY_NODE_MISSING")
    payload = node.get("payload")
    if not isinstance(payload, dict) or not payload.get("capabilityId"):
        raise NextSafeActionBlocked("CAPABILITY_PAYLOAD_INVALID")
    return payload


def load_target_record(repo_root: str | Path, target_id: str) -> dict[str, Any]:
    repo = _repo_root(repo_root)
    manifest_path = repo / TARGET_INDEX_REL
    if not manifest_path.is_file():
        raise NextSafeActionBlocked("TARGET_INDEX_MANIFEST_MISSING")
    manifest = _load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise NextSafeActionBlocked("TARGET_INDEX_MANIFEST_INVALID")
    if manifest.get("schema") != "prisma.visual.application.target-index.v1":
        raise NextSafeActionBlocked("TARGET_INDEX_SCHEMA_INVALID")
    if manifest.get("manualEditsForbidden") is not True:
        raise NextSafeActionBlocked("TARGET_INDEX_MANUAL_EDIT_POLICY_INVALID")

    surfaces = sorted((manifest.get("coverage") or {}).get("bySurface") or {})
    if not surfaces:
        raise NextSafeActionBlocked("TARGET_INDEX_SURFACES_MISSING")

    for surface in surfaces:
        view_path = repo / TARGET_INDEX_ROOT / f"{surface}.json"
        if not view_path.is_file():
            continue
        view = _load_json(view_path)
        if not isinstance(view, dict):
            raise NextSafeActionBlocked(f"TARGET_INDEX_VIEW_INVALID:{surface}")
        if view.get("schema") != "prisma.visual.application.target-index.surface.v1":
            raise NextSafeActionBlocked(f"TARGET_INDEX_VIEW_SCHEMA_INVALID:{surface}")
        if view.get("surface") != surface:
            raise NextSafeActionBlocked(f"TARGET_INDEX_VIEW_SURFACE_INVALID:{surface}")
        records = view.get("records")
        if not isinstance(records, list):
            raise NextSafeActionBlocked(f"TARGET_INDEX_RECORDS_INVALID:{surface}")
        for record in records:
            if isinstance(record, dict) and record.get("targetId") == target_id:
                return copy.deepcopy(record)
    raise NextSafeActionBlocked(f"TARGET_NOT_FOUND:{target_id}")


def _canonical_taxonomy(process_model: dict[str, Any] | None) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    mappings = ((process_model or {}).get("blockerTaxonomy") or {}).get("mappings") or []
    if not isinstance(mappings, list):
        return result
    for row in mappings:
        if not isinstance(row, dict):
            continue
        source_code = str(row.get("sourceCode") or "").strip()
        family = str(row.get("family") or "").strip()
        domain = str(row.get("sourceDomain") or "").strip()
        if source_code and family:
            result[source_code] = (family, domain)
    return result


def classify_blockers(
    blockers: Iterable[str],
    *,
    process_model: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    canonical = _canonical_taxonomy(process_model)
    out: list[dict[str, Any]] = []
    for raw in sorted({str(item).strip() for item in blockers if str(item).strip()}):
        if raw in canonical:
            family, domain = canonical[raw]
            out.append(
                {
                    "blocker": raw,
                    "family": family,
                    "owningAuthority": domain or None,
                    "classification": "CANONICAL",
                }
            )
            continue
        alias = TARGET_BLOCKER_ALIASES.get(raw)
        if alias:
            family, domain = alias
            out.append(
                {
                    "blocker": raw,
                    "family": family,
                    "owningAuthority": domain,
                    "classification": "DERIVED_TARGET_TOKEN",
                }
            )
            continue
        out.append(
            {
                "blocker": raw,
                "family": "UNCLASSIFIED_SOURCE_BLOCKER",
                "owningAuthority": None,
                "classification": "UNCLASSIFIED",
                "requiresTaxonomyUpdate": True,
            }
        )
    return out


def _recommend_action(
    *,
    blocker_rows: list[dict[str, Any]],
    stale_flags: list[str],
    unknown_flags: list[str],
    has_missing_evidence: bool,
) -> str:
    if stale_flags:
        return "REVALIDATE_AUTHORITY"
    if unknown_flags:
        return "STOP_BLOCKED"
    families = [str(row.get("family")) for row in blocker_rows]
    if "BINDING_GAP" in families:
        return "RESOLVE_BINDING"
    if "SEMANTIC_AUTHORITY_GAP" in families:
        return "RESOLVE_SEMANTIC_AUTHORITY"
    if "APPLICATION_AUTHORITY_GAP" in families or "LOCATION_CONFLICT" in families or "PHYSICAL_DRIFT" in families:
        return "RESOLVE_AUTHORITY_CONFLICT"
    if "PROJECTION_DEBT" in families or "PROJECTION_AMBIGUITY" in families or "AUTHORITY_RECONCILIATION_REQUIRED" in families:
        return "RECONCILE_PROJECTION"
    if "UNCLASSIFIED_SOURCE_BLOCKER" in families:
        return "STOP_BLOCKED"
    if has_missing_evidence:
        return "ACQUIRE_EVIDENCE"
    return "ACQUIRE_EVIDENCE"


def _allowed_tools(action: str) -> list[str]:
    mapping = {
        "ACQUIRE_EVIDENCE": ["Code Atlas evidence tooling", "domain verifier", "Mamastrophic evidence tooling"],
        "RESOLVE_AUTHORITY_CONFLICT": ["Authority Mesh / AutoMesh", "domain authority verifier"],
        "RESOLVE_SEMANTIC_AUTHORITY": ["Identity registries", "NDC authority readset", "Authority Mesh"],
        "RESOLVE_BINDING": ["Identity binding registry", "Authority Mesh", "visual-promotion candidate evidence"],
        "RECONCILE_PROJECTION": ["RIFAT projection verifier", "Target Index verifier", "Visual Promotion"],
        "REVALIDATE_AUTHORITY": ["Authority Mesh / AutoMesh v2"],
        "STOP_BLOCKED": [],
    }
    return list(mapping.get(action, []))


def _forbidden_actions() -> list[str]:
    return [
        "invent semantic, binding, recipe, region, slot, layer, target or adapter IDs",
        "treat candidate or derived graph output as canonical authority",
        "perform visual APPLY or GVAE mutation from this planner",
        "write NDC, Identity, RIFAT, Target Index, Visual Promotion, Work Entry or Factory Ledger",
        "treat possible next gates as authorization",
    ]


def _provenance(
    graph: dict[str, Any],
    target_record: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "observedCanonicalMain": graph.get("observedCanonicalMain"),
        "sourceSetDigest": graph.get("sourceSetDigest"),
        "graphStatus": graph.get("stateClass"),
        "graphSourceRefs": sorted(
            {
                str(ref)
                for row in graph.get("provenance") or []
                if isinstance(row, dict)
                for ref in [row.get("sourceRef")]
                if ref
            }
        ),
        "targetSourceRef": (
            TARGET_INDEX_ROOT.as_posix()
            if target_record is not None
            else None
        ),
        "targetId": target_record.get("targetId") if target_record else None,
    }


def _freshness_flags(
    graph: dict[str, Any],
    *,
    current_head: str | None = None,
) -> tuple[list[str], list[str]]:
    stale: list[str] = []
    unknown: list[str] = []
    if graph.get("productionCertified") is not False:
        unknown.append("GRAPH_PRODUCTION_CERTIFICATION_FLAG_INVALID")
    if graph.get("authorizationGranted") not in (None, False):
        unknown.append("GRAPH_AUTHORIZATION_FLAG_INVALID")
    observed = str(graph.get("observedCanonicalMain") or "").strip()
    if current_head and observed:
        if observed != current_head:
            stale.append("GRAPH_OBSERVED_MAIN_DIFFERS_FROM_CURRENT_HEAD")
    elif not observed:
        unknown.append("GRAPH_OBSERVED_MAIN_MISSING")
    if not graph.get("sourceSetDigest"):
        unknown.append("GRAPH_SOURCESET_DIGEST_MISSING")
    return stale, unknown


def next_safe_action(
    graph: dict[str, Any],
    *,
    target_record: dict[str, Any] | None = None,
    process_model: dict[str, Any] | None = None,
    current_head: str | None = None,
) -> dict[str, Any]:
    if not isinstance(graph, dict):
        raise NextSafeActionBlocked("GRAPH_OBJECT_REQUIRED")
    if graph.get("schema") != "prisma.visual-operating-graph.v1":
        raise NextSafeActionBlocked("GRAPH_SCHEMA_INVALID")
    capability = _capability(graph)
    stale_flags, unknown_flags = _freshness_flags(graph, current_head=current_head)

    target = copy.deepcopy(target_record) if target_record is not None else None
    target_blockers = _normalize_blockers(target.get("blockers")) if target else []
    graph_gaps = _normalize_blockers(
        [
            row.get("sourceCode") or row.get("reason")
            for row in graph.get("gaps") or []
            if isinstance(row, dict)
            and (row.get("status") in {"BLOCKED", "STALE", "CONFLICTED", "MISSING"} or row.get("sourceCode"))
        ]
    )
    blockers = sorted(set(target_blockers + graph_gaps))
    blocker_rows = classify_blockers(blockers, process_model=process_model)

    has_missing_evidence = bool(
        target
        and target.get("recordKind") == "EXACT_APPLICATION_TARGET"
        and not target.get("sourceSha256")
    )
    action = _recommend_action(
        blocker_rows=blocker_rows,
        stale_flags=stale_flags,
        unknown_flags=unknown_flags,
        has_missing_evidence=has_missing_evidence,
    )

    current_decision = {
        "capabilityId": capability.get("capabilityId"),
        "classification": capability.get("classification"),
        "status": capability.get("status"),
        "nextGate": capability.get("nextGate"),
        "targetId": target.get("targetId") if target else None,
        "targetStatus": target.get("status") if target else None,
        "recordKind": target.get("recordKind") if target else None,
        "enforcement": target.get("enforcement") if target else None,
        "promotionStatus": target.get("promotionStatus") if target else None,
        "workEntryDecision": target.get("workEntryDecision") if target else None,
    }

    missing_authorities = sorted(
        {
            str(row["owningAuthority"])
            for row in blocker_rows
            if row.get("owningAuthority")
        }
    )
    possible_next_gates: list[str] = []
    if target:
        if target.get("enforcement") == "DISCOVERY_ONLY" or target.get("recordKind") == "VISUAL_CONTROL_CENSUS_TARGET":
            possible_next_gates.append("REGISTER_TARGET_FIRST")
        elif not blockers:
            possible_next_gates.append("GVAE_EXACT_APPLY")
        else:
            possible_next_gates.append("BLOCKED")
    if capability.get("nextGate"):
        possible_next_gates.append(str(capability["nextGate"]))
    possible_next_gates = sorted(set(possible_next_gates))

    return {
        "schemaVersion": NEXT_SCHEMA,
        "query": "WHAT_CAN_I_DO_NEXT?" if target is None else "WHY_NOT_APPLY_READY(targetId)",
        "subject": {
            "capabilityId": capability.get("capabilityId"),
            "targetId": target.get("targetId") if target else None,
        },
        "currentDecision": current_decision,
        "preservedSourceBlockers": blockers,
        "blockerFamilies": blocker_rows,
        "missingAuthorities": missing_authorities,
        "owningAuthority": (
            blocker_rows[0].get("owningAuthority")
            if len({row.get("owningAuthority") for row in blocker_rows if row.get("owningAuthority")}) == 1
            and blocker_rows
            else None
        ),
        "recommendedNextSafeAction": action,
        "allowedTools": _allowed_tools(action),
        "forbiddenActions": _forbidden_actions(),
        "evidenceRequired": sorted(
            set(
                [
                    "fresh task-exact Authority Mesh when authority freshness is relevant",
                    "direct evidence for every claimed resolved authority",
                    "runtime evidence before runtime certification",
                ]
                + (["canonical source/output hash evidence"] if target and target.get("projectionMode") else [])
            )
        ),
        "possibleNextGates": possible_next_gates,
        "provenance": _provenance(graph, target),
        "staleUnknownFlags": {
            "stale": stale_flags,
            "unknown": unknown_flags,
        },
        "authorizationGranted": False,
        "productionCertified": False,
    }


def _remove_hypothetical_blockers(
    blockers: list[str],
    hypotheses: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    remaining = list(blockers)
    removed: list[dict[str, Any]] = []
    assumptions: list[str] = []
    requested: set[str] = set()

    resolutions = hypotheses.get("resolutions") if isinstance(hypotheses, dict) else None
    if isinstance(resolutions, list):
        for item in resolutions:
            if not isinstance(item, dict):
                assumptions.append("INVALID_HYPOTHESIS_ROW_IGNORED")
                continue
            kind = str(item.get("kind") or "").strip()
            if kind:
                requested.add(kind)
    for key in (
        "resolveNdcPrimaryMeaning",
        "resolveVisualMeaning",
        "addValidBinding",
        "addApplicationLayerAuthority",
        "markProjectionReconciled",
        "markPhysicalReconciled",
        "markLocationReconciled",
    ):
        if isinstance(hypotheses, dict) and hypotheses.get(key) is True:
            requested.add(
                {
                    "resolveNdcPrimaryMeaning": "ndc_primary_meaning",
                    "resolveVisualMeaning": "visual_meaning",
                    "addValidBinding": "valid_binding",
                    "addApplicationLayerAuthority": "application_layer_authority",
                    "markProjectionReconciled": "projection_reconciled",
                    "markPhysicalReconciled": "physical_reconciled",
                    "markLocationReconciled": "location_reconciled",
                }[key]
            )

    for kind in sorted(requested):
        token_candidates = HYPOTHESIS_BLOCKERS.get(kind)
        if token_candidates is None:
            assumptions.append(f"UNSUPPORTED_HYPOTHESIS_KIND:{kind}")
            continue
        matched = [token for token in remaining if token in token_candidates]
        if not matched:
            assumptions.append(f"HYPOTHESIS_NO_MODELED_EFFECT:{kind}")
            continue
        for token in matched:
            remaining.remove(token)
            removed.append(
                {
                    "hypothesis": kind,
                    "blocker": token,
                }
            )
    return sorted(set(remaining)), removed, assumptions


def what_if_digital_twin(
    graph: dict[str, Any],
    *,
    target_record: dict[str, Any] | None = None,
    hypotheses: dict[str, Any] | None = None,
    process_model: dict[str, Any] | None = None,
    current_head: str | None = None,
) -> dict[str, Any]:
    if not isinstance(graph, dict):
        raise NextSafeActionBlocked("GRAPH_OBJECT_REQUIRED")
    simulated_graph = copy.deepcopy(graph)
    simulated_target = copy.deepcopy(target_record) if target_record is not None else None
    assumptions_input = copy.deepcopy(hypotheses or {})
    before = next_safe_action(
        simulated_graph,
        target_record=simulated_target,
        process_model=process_model,
        current_head=current_head,
    )
    blockers = list(before["preservedSourceBlockers"])
    remaining, removed, assumptions = _remove_hypothetical_blockers(blockers, assumptions_input)

    if simulated_target is not None:
        simulated_target["blockers"] = remaining
        if not remaining:
            simulated_target["status"] = "HYPOTHETICAL_UNBLOCKED"
    simulated_graph["hypothetical"] = True
    simulated_graph["nonAuthoritative"] = True
    simulated_graph["simulationOnly"] = True
    simulated_graph["authorizationGranted"] = False

    after = next_safe_action(
        simulated_graph,
        target_record=simulated_target,
        process_model=process_model,
        current_head=current_head,
    )
    original_provenance = _provenance(graph, target_record)
    return {
        "schemaVersion": WHAT_IF_SCHEMA,
        "query": "WHY_NOT_APPLY_READY(targetId)" if target_record else "WHAT_CAN_I_DO_NEXT?",
        "hypothetical": True,
        "nonAuthoritative": True,
        "simulationOnly": True,
        "targetId": target_record.get("targetId") if target_record else None,
        "originalDecision": before["currentDecision"],
        "simulatedDecision": after["currentDecision"],
        "blockersRemoved": removed,
        "blockersRemaining": remaining,
        "newlyReachableCandidateGates": after["possibleNextGates"],
        "unresolvedAuthorities": sorted(
            set(
                before["missingAuthorities"]
            )
            | {
                row.get("owningAuthority")
                for row in after["blockerFamilies"]
                if row.get("owningAuthority")
            }
        ),
        "assumptions": assumptions,
        "hypothesisInput": assumptions_input,
        "originalProvenance": original_provenance,
        "staleUnknownFlags": after["staleUnknownFlags"],
        "authorizationGranted": False,
        "productionCertified": False,
    }


def load_process_model(repo_root: str | Path) -> dict[str, Any]:
    repo = _repo_root(repo_root)
    path = repo / PROCESS_MODEL_DEFAULT
    value = _load_json(path)
    if not isinstance(value, dict):
        raise NextSafeActionBlocked("PROCESS_MODEL_INVALID")
    return value


def load_graph(path: str | Path) -> dict[str, Any]:
    value = _load_json(Path(path))
    if not isinstance(value, dict):
        raise NextSafeActionBlocked("GRAPH_OBJECT_REQUIRED")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Explain the next safe PRISMA Visual Operating Graph action without granting authorization."
    )
    parser.add_argument("--graph", required=True)
    parser.add_argument("--query", required=True, choices=("WHAT_CAN_I_DO_NEXT?", "WHY_NOT_APPLY_READY(targetId)"))
    parser.add_argument("--repo-root")
    parser.add_argument("--target-id")
    parser.add_argument("--target-json")
    parser.add_argument("--hypotheses-json")
    parser.add_argument("--current-head")
    parser.add_argument("--json-out")
    args = parser.parse_args()

    repo = _repo_root(args.repo_root) if args.repo_root else None
    graph = load_graph(args.graph)
    process_model = load_process_model(repo) if repo is not None else None

    target: dict[str, Any] | None = None
    if args.target_json:
        value = _load_json(Path(args.target_json))
        if not isinstance(value, dict):
            raise SystemExit("TARGET_JSON_OBJECT_REQUIRED")
        target = value
    elif args.target_id:
        if repo is None:
            raise SystemExit("REPO_ROOT_REQUIRED_FOR_TARGET_ID")
        target = load_target_record(repo, args.target_id)

    if args.query == "WHY_NOT_APPLY_READY(targetId)" and target is None:
        raise SystemExit("TARGET_REQUIRED_FOR_QUERY")
    if args.query == "WHAT_CAN_I_DO_NEXT?" and args.target_id is not None:
        target = load_target_record(repo, args.target_id) if repo is not None else target

    current_head = args.current_head
    result = next_safe_action(
        graph,
        target_record=target,
        process_model=process_model,
        current_head=current_head,
    )
    if args.query == "WHY_NOT_APPLY_READY(targetId)":
        result["query"] = args.query

    if args.hypotheses_json:
        hypotheses = _load_json(Path(args.hypotheses_json))
        result = what_if_digital_twin(
            graph,
            target_record=target,
            hypotheses=hypotheses if isinstance(hypotheses, dict) else {},
            process_model=process_model,
            current_head=current_head,
        )
        result["query"] = args.query
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
