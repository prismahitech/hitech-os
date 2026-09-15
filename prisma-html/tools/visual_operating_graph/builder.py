from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .graph_contract import (
    CONTROL_PLANE_REL,
    FOUNDATION_REL,
    GRAPH_SCHEMA,
    LEDGER_REL,
    PROCESS_MODEL_REL,
    SCHEMA_REL,
    STATUS_INDEX_REL,
    SURFACES_REL,
    GraphBuildBlocked,
    _add_edge,
    _add_node,
    _edge,
    _load_json,
    _node,
    _source_node_id,
    _source_node_type,
    _surface_ids,
    validate_graph_contract,
)
from .source_set_verifier import LOCK_REL, canonical_json, find_repo_root, verify_source_set


def build_operating_graph(
    repo_root: str | Path,
    *,
    current_head_override: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    repo = Path(repo_root).resolve()
    verification = verify_source_set(repo, current_head_override=current_head_override)
    if verification["status"] != "PASS_SOURCESET_VERIFIED":
        raise GraphBuildBlocked("SOURCESET_BLOCKED:" + canonical_json(verification.get("findings") or []))

    lock = _load_json(repo / LOCK_REL)
    model = _load_json(repo / PROCESS_MODEL_REL)
    foundation = _load_json(repo / FOUNDATION_REL)
    schema = _load_json(repo / SCHEMA_REL)
    ledger = _load_json(repo / LEDGER_REL)
    surfaces_doc = _load_json(repo / SURFACES_REL)
    control_plane = _load_json(repo / CONTROL_PLANE_REL)
    status_index = _load_json(repo / STATUS_INDEX_REL)

    observed_main = verification.get("lockedObservedMain") or verification.get("repoHead")
    if not observed_main:
        raise GraphBuildBlocked("OBSERVED_CANONICAL_MAIN_REQUIRED")

    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    provenance: list[dict[str, Any]] = []
    source_id_by_path: dict[str, str] = {}

    for row in sorted(
        lock.get("sources") or [],
        key=lambda item: str(item.get("path")) if isinstance(item, dict) else "",
    ):
        if not isinstance(row, dict) or not row.get("path"):
            continue
        path = str(row["path"])
        node_id = _source_node_id(row)
        source_id_by_path[path] = node_id
        canonicality = "REFERENCE_ONLY" if row.get("authorityDomain") == "atlasfin" else "CANONICAL_AUTHORITY"
        _add_node(
            nodes,
            _node(
                node_id,
                _source_node_type(row),
                str(row.get("authorityDomain") or "unknown"),
                [path],
                {
                    "path": path,
                    "role": row.get("role"),
                    "schema": row.get("schema"),
                    "version": row.get("version"),
                    "gitBlobSha": row.get("gitBlobSha"),
                },
                canonicality,
            ),
        )
        provenance.append(
            {
                "authorityDomain": str(row.get("authorityDomain") or "unknown"),
                "sourceRef": path,
                "sourceRole": str(row.get("role") or "unknown"),
                "canonicality": canonicality,
                "gitBlobSha": row.get("gitBlobSha"),
                "artifactDigest": None,
                "observedHead": observed_main,
                "evidenceRefs": [],
            }
        )

    cap = next(
        (
            row
            for row in ledger.get("capabilities") or []
            if isinstance(row, dict) and row.get("id") == foundation.get("capabilityId")
        ),
        None,
    )
    if cap is None:
        raise GraphBuildBlocked("OPERATING_GRAPH_CAPABILITY_MISSING")

    ledger_ref = LEDGER_REL.as_posix()
    cap_id = f"CAPABILITY:{cap['id']}"
    state_id = f"LEDGER_STATE:{cap['id']}:{cap.get('status')}"
    _add_node(
        nodes,
        _node(
            cap_id,
            "CAPABILITY",
            "factory-ledger",
            [ledger_ref],
            {
                "capabilityId": cap["id"],
                "classification": cap.get("classification"),
                "status": cap.get("status"),
                "doNotRebuild": cap.get("doNotRebuild"),
                "nextGate": cap.get("nextGate"),
            },
            "CANONICAL_AUTHORITY",
        ),
    )
    _add_node(
        nodes,
        _node(
            state_id,
            "LEDGER_STATE",
            "factory-ledger",
            [ledger_ref],
            {
                "status": cap.get("status"),
                "classification": cap.get("classification"),
                "doNotRebuild": cap.get("doNotRebuild"),
            },
            "CANONICAL_AUTHORITY",
        ),
    )
    _add_edge(
        edges,
        _edge(cap_id, state_id, "represented_by", "factory-ledger", [ledger_ref], "CANONICAL_AUTHORITY"),
    )

    lock_node = "OUTPUT:MASTER_MAP_SOURCESET_LOCK"
    _add_node(
        nodes,
        _node(
            lock_node,
            "OUTPUT",
            "visual-operating-graph",
            [LOCK_REL.as_posix()],
            {
                "sourceSetDigest": verification["sourceSetDigest"],
                "headDisposition": verification["headDisposition"],
                "lockedObservedMain": observed_main,
            },
        ),
    )
    for source_id in sorted(source_id_by_path.values()):
        _add_edge(
            edges,
            _edge(
                lock_node,
                source_id,
                "derived_from",
                "visual-operating-graph",
                [LOCK_REL.as_posix()],
            ),
        )

    surface_ref = SURFACES_REL.as_posix()
    surface_ids = _surface_ids(surfaces_doc)
    for surface in surface_ids:
        _add_node(
            nodes,
            _node(
                f"SURFACE:{surface}",
                "SURFACE",
                "visual-control",
                [surface_ref],
                {"surfaceKey": surface},
                "CANONICAL_AUTHORITY",
            ),
        )

    for row in model.get("surfaceCohorts") or []:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        cohort_id = str(row["id"])
        source = str(row.get("membershipSource") or PROCESS_MODEL_REL.as_posix())
        if cohort_id == "VISUAL_CONTROL_ALL":
            members = surface_ids
        elif cohort_id == "PROMOTION_READINESS_V1":
            members = sorted(str(x) for x in (control_plane.get("surfaceKeys") or []))
        elif cohort_id == "PROMOTION_PROTECTED_V1":
            members = sorted(str(x) for x in (control_plane.get("protectedSurfaces") or []))
        else:
            members = []
        cohort_node = f"SURFACE_COHORT:{cohort_id}"
        _add_node(
            nodes,
            _node(
                cohort_node,
                "SURFACE_COHORT",
                str(row.get("authorityDomain") or "governance"),
                [source],
                {
                    "cohortId": cohort_id,
                    "membershipMode": row.get("membershipMode"),
                    "members": members,
                },
            ),
        )
        for member in members:
            surface_node = f"SURFACE:{member}"
            if surface_node in nodes:
                _add_edge(
                    edges,
                    _edge(
                        surface_node,
                        cohort_node,
                        "belongs_to",
                        str(row.get("authorityDomain") or "governance"),
                        [source],
                    ),
                )

    current_phase = status_index.get("currentPhase")
    if current_phase:
        _add_node(
            nodes,
            _node(
                f"PHASE:{current_phase}",
                "PHASE",
                "live-overlay",
                [STATUS_INDEX_REL.as_posix()],
                {
                    "phase": current_phase,
                    "canonicalSource": STATUS_INDEX_REL.as_posix(),
                },
                "CANONICAL_AUTHORITY",
            ),
        )

    for mapping in (model.get("blockerTaxonomy") or {}).get("mappings") or []:
        if not isinstance(mapping, dict):
            continue
        code = str(mapping.get("sourceCode") or "")
        family = str(mapping.get("family") or "")
        domain = str(mapping.get("sourceDomain") or "governance")
        if not code or not family:
            continue
        source_node = f"BLOCKER:{domain}:{code}"
        family_node = f"BLOCKER_FAMILY:{family}"
        _add_node(
            nodes,
            _node(
                source_node,
                "BLOCKER",
                domain,
                [PROCESS_MODEL_REL.as_posix()],
                {"sourceCode": code, "family": family, "role": "SOURCE_BLOCKER"},
            ),
        )
        _add_node(
            nodes,
            _node(
                family_node,
                "BLOCKER",
                "visual-operating-graph",
                [PROCESS_MODEL_REL.as_posix()],
                {"family": family, "role": "BLOCKER_FAMILY"},
            ),
        )
        _add_edge(
            edges,
            _edge(
                source_node,
                family_node,
                "belongs_to",
                "visual-operating-graph",
                [PROCESS_MODEL_REL.as_posix()],
            ),
        )

    for role in sorted(str(x) for x in (model.get("writerRoles") or [])):
        _add_node(
            nodes,
            _node(
                f"WRITER:{role}",
                "WRITER",
                "visual-operating-graph",
                [PROCESS_MODEL_REL.as_posix()],
                {"writerRole": role},
            ),
        )

    foundation_ref = FOUNDATION_REL.as_posix()
    tool_specs = [
        ("TOOL:OPERATING_GRAPH_BUILDER", "builder.py"),
        ("TOOL:SOURCESET_VERIFIER", "source_set_verifier.py"),
        ("TOOL:LIVE_PHASE_TRUTH_REDUCER", "live_phase_reducer.py"),
    ]
    output_specs = [
        ("OUTPUT:PRISMA_PROCESS_GRAPH", "PRISMA_PROCESS_GRAPH.generated.json"),
        ("OUTPUT:PRISMA_VISUAL_CHANGE_MASTER_MAP", "PRISMA_VISUAL_CHANGE_MASTER_MAP.generated.json"),
        ("OUTPUT:LIVE_PHASE_TRUTH", "LIVE_PHASE_TRUTH.generated.json"),
    ]
    for tool_id, file_name in tool_specs:
        _add_node(
            nodes,
            _node(
                tool_id,
                "TOOL",
                "visual-operating-graph",
                [foundation_ref],
                {"implementation": file_name, "readOnlyAgainstAuthority": True},
            ),
        )
    for output_id, file_name in output_specs:
        _add_node(
            nodes,
            _node(
                output_id,
                "OUTPUT",
                "visual-operating-graph",
                [foundation_ref],
                {"generatedFile": file_name, "manualEditsForbidden": True},
            ),
        )
        if "WRITER:GENERATED_WRITER" in nodes:
            _add_edge(
                edges,
                _edge(
                    output_id,
                    "WRITER:GENERATED_WRITER",
                    "owned_by",
                    "visual-operating-graph",
                    [PROCESS_MODEL_REL.as_posix()],
                ),
            )

    _add_edge(
        edges,
        _edge(
            "TOOL:OPERATING_GRAPH_BUILDER",
            "OUTPUT:PRISMA_PROCESS_GRAPH",
            "produces",
            "visual-operating-graph",
            [foundation_ref],
        ),
    )
    _add_edge(
        edges,
        _edge(
            "TOOL:OPERATING_GRAPH_BUILDER",
            "OUTPUT:PRISMA_VISUAL_CHANGE_MASTER_MAP",
            "produces",
            "visual-operating-graph",
            [foundation_ref],
        ),
    )
    _add_edge(
        edges,
        _edge(
            "TOOL:SOURCESET_VERIFIER",
            lock_node,
            "validates",
            "visual-operating-graph",
            [foundation_ref],
        ),
    )
    _add_edge(
        edges,
        _edge(
            "TOOL:LIVE_PHASE_TRUTH_REDUCER",
            "OUTPUT:LIVE_PHASE_TRUTH",
            "produces",
            "visual-operating-graph",
            [foundation_ref],
        ),
    )

    gate_specs = [
        (
            "GATE:FACTORY_ANTI_REWORK",
            "factory-ledger",
            "PRISMA Factory Ledger/PRISMA_FACTORY_LEDGER_AGENT_GATE.md",
        ),
        (
            "GATE:AUTHORITY_MESH",
            "authority-mesh",
            "apps/terminal-de-venta-system/docs/ops/PRISMA_AUTHORITY_MESH_AUTOMESH_V2_RUNBOOK.md",
        ),
        (
            "GATE:VISUAL_WORK_ENTRY",
            "work-entry-gvae",
            "prisma-html/tools/visual_application/visual_work_entry_gate.py",
        ),
    ]
    for gate_id, domain, source in gate_specs:
        if (repo / source).is_file():
            _add_node(
                nodes,
                _node(
                    gate_id,
                    "GATE",
                    domain,
                    [source],
                    {"gateId": gate_id.split(":", 1)[1]},
                    "CANONICAL_AUTHORITY",
                ),
            )
            _add_edge(
                edges,
                _edge(
                    cap_id,
                    gate_id,
                    "requires",
                    domain,
                    [source],
                    "CANONICAL_AUTHORITY",
                ),
            )

    graph = {
        "schema": GRAPH_SCHEMA,
        "observedCanonicalMain": observed_main,
        "sourceSetDigest": verification["sourceSetDigest"],
        "stateClass": "CANONICAL_STATE",
        "generatedAt": None,
        "productionCertified": False,
        "nodes": sorted(nodes.values(), key=lambda row: row["id"]),
        "edges": sorted(
            edges.values(),
            key=lambda row: (row["from"], row["to"], row["relation"], canonical_json(row)),
        ),
        "gaps": [
            {
                "id": f"GAP:{index + 1}",
                "reason": str(finding.get("code")),
                "sourceDomain": "source-set",
                "sourceCode": str(finding.get("code")),
                "status": "BLOCKED" if finding.get("blocking") else "UNKNOWN",
                "nextEvidence": "Regenerate or reconcile the owning canonical source before rebuilding the graph.",
            }
            for index, finding in enumerate(verification.get("findings") or [])
        ],
        "provenance": sorted(
            provenance,
            key=lambda row: (row["authorityDomain"], row["sourceRef"]),
        ),
    }
    validate_graph_contract(graph, schema)
    return graph, verification


def build_master_map(
    graph: dict[str, Any],
    verification: dict[str, Any],
    repo_root: str | Path,
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    foundation = _load_json(repo / FOUNDATION_REL)

    capability = next(
        (
            row.get("payload", {})
            for row in graph.get("nodes") or []
            if row.get("type") == "CAPABILITY"
            and row.get("payload", {}).get("capabilityId") == foundation.get("capabilityId")
        ),
        {},
    )
    phase = next(
        (
            row.get("payload", {}).get("phase")
            for row in graph.get("nodes") or []
            if row.get("type") == "PHASE"
        ),
        None,
    )
    surfaces = sorted(
        row.get("payload", {}).get("surfaceKey")
        for row in graph.get("nodes") or []
        if row.get("type") == "SURFACE" and row.get("payload", {}).get("surfaceKey")
    )
    cohorts = sorted(
        (
            {
                "cohortId": row.get("payload", {}).get("cohortId"),
                "members": row.get("payload", {}).get("members") or [],
            }
            for row in graph.get("nodes") or []
            if row.get("type") == "SURFACE_COHORT"
        ),
        key=lambda row: str(row.get("cohortId")),
    )
    blockers = sorted(
        (
            row.get("payload", {})
            for row in graph.get("nodes") or []
            if row.get("type") == "BLOCKER"
            and row.get("payload", {}).get("role") == "SOURCE_BLOCKER"
        ),
        key=lambda row: (str(row.get("family")), str(row.get("sourceCode"))),
    )
    return {
        "schemaVersion": "prisma.visual-operating-graph.master-map.v1",
        "status": "GENERATED_READ_ONLY_VIEW",
        "observedCanonicalMain": graph.get("observedCanonicalMain"),
        "sourceSetDigest": graph.get("sourceSetDigest"),
        "headDisposition": verification.get("headDisposition"),
        "capability": capability,
        "canonicalPhase": phase,
        "surfaces": surfaces,
        "surfaceCohorts": cohorts,
        "blockerTaxonomy": blockers,
        "nextAllowedGate": foundation.get("nextAllowedGate"),
        "authorizationGranted": False,
        "productionCertified": False,
    }


def render_master_map_markdown(master: dict[str, Any]) -> str:
    cap = master.get("capability") or {}
    lines = [
        "# PRISMA Visual Change Master Map generated operational view",
        "",
        "generated: true",
        "manualEditsForbidden: true",
        f"sourceSetDigest: `{master.get('sourceSetDigest')}`",
        f"observedCanonicalMain: `{master.get('observedCanonicalMain')}`",
        f"headDisposition: `{master.get('headDisposition')}`",
        "productionCertified: false",
        "authorizationGranted: false",
        "",
        "This file is a deterministic projection of locked authority. It is not a new authority source.",
        "",
        "## Capability",
        "",
        f"- `{cap.get('capabilityId')}`: classification `{cap.get('classification')}`, status `{cap.get('status')}`, doNotRebuild `{str(cap.get('doNotRebuild')).lower()}`",
        "",
        "## Canonical phase",
        "",
        f"- `{master.get('canonicalPhase')}`",
        "",
        "## Surfaces",
        "",
    ]
    lines.extend(f"- `{surface}`" for surface in master.get("surfaces") or [])
    lines.extend(["", "## Cohorts", ""])
    for row in master.get("surfaceCohorts") or []:
        members = ", ".join(f"`{item}`" for item in row.get("members") or []) or "_none_"
        lines.append(f"- `{row.get('cohortId')}`: {members}")
    lines.extend(["", "## Preserved blocker crosswalk", ""])
    for row in master.get("blockerTaxonomy") or []:
        lines.append(f"- `{row.get('sourceCode')}` → `{row.get('family')}`")
    lines.extend(
        [
            "",
            "## NEXT ALLOWED GATE",
            "",
            f"`{master.get('nextAllowedGate')}`",
            "",
        ]
    )
    return "\n".join(lines)


def expected_outputs(
    repo_root: str | Path,
    *,
    current_head_override: str | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    graph, verification = build_operating_graph(
        repo_root,
        current_head_override=current_head_override,
    )
    master = build_master_map(graph, verification, repo_root)
    outputs = {
        "PRISMA_PROCESS_GRAPH.generated.json": json.dumps(
            graph, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n",
        "PRISMA_VISUAL_CHANGE_MASTER_MAP.generated.json": json.dumps(
            master, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n",
        "PRISMA_VISUAL_CHANGE_MASTER_MAP.generated.md": render_master_map_markdown(master),
    }
    return outputs, verification


def write_outputs(
    repo_root: str | Path,
    out_dir: str | Path,
    *,
    current_head_override: str | None = None,
) -> dict[str, Any]:
    outputs, verification = expected_outputs(
        repo_root,
        current_head_override=current_head_override,
    )
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        target = destination / name
        temp = target.with_suffix(target.suffix + ".tmp")
        temp.write_text(content, encoding="utf-8")
        temp.replace(target)
    return {
        "status": "PASS_OPERATING_GRAPH_GENERATED",
        "outputCount": len(outputs),
        "outputs": sorted(outputs),
        "sourceSetDigest": verification["sourceSetDigest"],
        "productionCertified": False,
        "authorizationGranted": False,
    }


def check_outputs(
    repo_root: str | Path,
    out_dir: str | Path,
    *,
    current_head_override: str | None = None,
) -> dict[str, Any]:
    outputs, verification = expected_outputs(
        repo_root,
        current_head_override=current_head_override,
    )
    destination = Path(out_dir)
    drift = []
    for name, expected in outputs.items():
        target = destination / name
        if not target.is_file() or target.read_text(encoding="utf-8") != expected:
            drift.append(name)
    return {
        "status": "PASS_OPERATING_GRAPH_OUTPUTS_CURRENT"
        if not drift
        else "BLOCKED_OPERATING_GRAPH_OUTPUT_DRIFT",
        "drift": sorted(drift),
        "sourceSetDigest": verification["sourceSetDigest"],
        "productionCertified": False,
        "authorizationGranted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the deterministic read-only PRISMA Visual Operating Graph."
    )
    parser.add_argument("--repo-root")
    parser.add_argument("--out-dir", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve() if args.repo_root else find_repo_root()
    result = (
        write_outputs(repo, args.out_dir)
        if args.write
        else check_outputs(repo, args.out_dir)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if str(result.get("status", "")).startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
