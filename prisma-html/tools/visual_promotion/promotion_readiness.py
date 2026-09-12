from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

PHASE = "CANONICAL_PROMOTION_READINESS_RESOLUTION"
ROW_SCHEMA = "prisma.visual-promotion.promotion-resolution.v1"
GROUP_SCHEMA = "prisma.visual-promotion.cross-surface-semantic-group.v1"
PLAN_SCHEMA = "prisma.visual-promotion.canonical-promotion-plan.v1"
EXPECTED_COUNTS = {"tablet": 929, "pc": 827, "mobile": 271, "shared-ui": 70}
EXPECTED_TOTAL = 2097

READINESS = {
    "READY_REUSE_EXISTING_AUTHORITY",
    "READY_FOR_CANONICAL_REGISTRATION",
    "BLOCKED_MISSING_SEMANTIC_AUTHORITY",
    "BLOCKED_MISSING_RECIPE_AUTHORITY",
    "BLOCKED_MISSING_ADAPTER_AUTHORITY",
    "BLOCKED_MISSING_BINDING",
    "BLOCKED_PROJECTION_AUTHORITY",
    "BLOCKED_PHYSICAL_DRIFT",
    "BLOCKED_MULTI_REGION_CONFLICT",
    "BLOCKED_NDC_AMBIGUITY",
    "BLOCKED_UNRESOLVED_AUTHORITY",
    "NOT_APPLICABLE",
}
BLOCKED = {x for x in READINESS if x.startswith("BLOCKED_")}
POST_REGISTRATION = {
    "MAY_REACH_GVAE_EXACT_APPLY_AFTER_REGISTRATION_AND_RERUN",
    "STILL_BLOCKED_AFTER_REGISTRATION",
    "UNKNOWN_REQUIRES_RERUN",
    "NOT_APPLICABLE",
}
PC_PROJECTION = {
    "CANONICAL_PROJECTION_REQUIRED_MISSING",
    "INTENTIONALLY_NON_PROJECTED",
    "REFERENCE_OR_GOVERNOR_ONLY",
    "STALE_AUTHORITY",
    "UNRESOLVED",
    "NOT_APPLICABLE",
}
MOBILE_PROJECTION = {
    "RIFAT_AUTHORITATIVE_PRODUCT_STALE",
    "PRODUCT_LIKELY_NEWER_AUTHORITY_RECONCILIATION_REQUIRED",
    "INTENTIONAL_DIVERGENCE",
    "AMBIGUOUS",
    "NOT_APPLICABLE",
}
EQUIVALENCE = {
    "CANONICAL_SEMANTIC_EQUIVALENCE",
    "VISUAL_ONLY_SIMILARITY",
    "NO_PROVEN_EQUIVALENCE",
}


class PromotionReadinessError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PromotionReadinessError(f"JSON_OBJECT_REQUIRED:{path}")
    return data


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PromotionReadinessError(f"JSONL_INVALID:{path}:{line_no}:{exc.msg}") from exc
        if not isinstance(row, dict):
            raise PromotionReadinessError(f"JSONL_OBJECT_REQUIRED:{path}:{line_no}")
        rows.append(row)
    return rows


def corpus_truth(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "prisma-html/governance/visual-promotion/contracts/corpus-certification/CURRENT_TRUTH.json"
    data = load_json(path)
    if data.get("schema") != "prisma.visual-promotion.certified-current-truth.v1":
        raise PromotionReadinessError("CURRENT_TRUTH_SCHEMA_INVALID")
    if data.get("status") != "CERTIFIED_CORPUS_CURRENT_TRUTH":
        raise PromotionReadinessError("CURRENT_TRUTH_STATUS_INVALID")
    if data.get("recordCount") != EXPECTED_TOTAL:
        raise PromotionReadinessError(f"CURRENT_TRUTH_COUNT_INVALID:{data.get('recordCount')}")
    records = data.get("records")
    if not isinstance(records, list) or len(records) != EXPECTED_TOTAL:
        raise PromotionReadinessError("CURRENT_TRUTH_RECORDS_INVALID")
    return data


def truth_by_surface(repo_root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    truth = corpus_truth(repo_root)
    out = {surface: {} for surface in EXPECTED_COUNTS}
    for row in truth["records"]:
        surface = row.get("surfaceKey")
        target = row.get("targetId")
        if surface not in out or not isinstance(target, str) or not target:
            raise PromotionReadinessError(f"CURRENT_TRUTH_ROW_INVALID:{surface}:{target}")
        if target in out[surface]:
            raise PromotionReadinessError(f"CURRENT_TRUTH_DUPLICATE_TARGET:{target}")
        out[surface][target] = row
    actual = {surface: len(rows) for surface, rows in out.items()}
    if actual != EXPECTED_COUNTS:
        raise PromotionReadinessError(f"CURRENT_TRUTH_SURFACE_COUNTS_INVALID:{actual}")
    return out


def _require_string(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PromotionReadinessError(code)
    return value


def _exact_physical_target(row: Mapping[str, Any]) -> bool:
    physical = row.get("physicalTarget")
    if not isinstance(physical, Mapping):
        return False
    return all(isinstance(physical.get(key), str) and bool(physical.get(key))
               for key in ("ownerId", "implementationLayerId"))


def _semantic_evidence(row: Mapping[str, Any]) -> bool:
    meaning = row.get("canonicalMeaning")
    if not isinstance(meaning, Mapping):
        return False
    existing = bool(meaning.get("ndcPrimaryId") or meaning.get("visualMeaningId"))
    proposal = bool(meaning.get("proposedMeaningSlug"))
    refs = meaning.get("semanticAuthorityRefs")
    return bool((existing or proposal) and isinstance(refs, list) and refs)


def validate_resolution(row: Mapping[str, Any], *, expected_surface: str, truth_row: Mapping[str, Any]) -> None:
    target = str(row.get("targetId") or "")
    if row.get("schema") != ROW_SCHEMA:
        raise PromotionReadinessError(f"ROW_SCHEMA_INVALID:{target}")
    if row.get("phase") != PHASE:
        raise PromotionReadinessError(f"ROW_PHASE_INVALID:{target}")
    if row.get("surfaceKey") != expected_surface:
        raise PromotionReadinessError(f"ROW_SURFACE_INVALID:{target}:{row.get('surfaceKey')}")
    if target != truth_row.get("targetId"):
        raise PromotionReadinessError(f"ROW_TARGET_TRUTH_MISMATCH:{target}")

    inp = row.get("input")
    if not isinstance(inp, Mapping):
        raise PromotionReadinessError(f"ROW_INPUT_REQUIRED:{target}")
    expected_pairs = {
        "promotionStatus": truth_row.get("promotionStatus"),
        "workEntryDecision": truth_row.get("workEntryDecision"),
        "physicalStatus": truth_row.get("physicalStatus"),
        "projectionStatus": truth_row.get("projectionStatus"),
    }
    for key, expected in expected_pairs.items():
        if inp.get(key) != expected:
            raise PromotionReadinessError(f"INPUT_TRUTH_MUTATION:{target}:{key}:{inp.get(key)}:{expected}")
    if not isinstance(inp.get("certificationStatus"), str):
        raise PromotionReadinessError(f"INPUT_CERTIFICATION_STATUS_REQUIRED:{target}")

    atlasfin = row.get("atlasfin")
    if not isinstance(atlasfin, Mapping) or atlasfin.get("semanticAuthorityGranted") is not False:
        raise PromotionReadinessError(f"ATLASFIN_SEMANTIC_AUTHORITY_FORBIDDEN:{target}")

    registration = row.get("registration")
    if not isinstance(registration, Mapping):
        raise PromotionReadinessError(f"REGISTRATION_OBJECT_REQUIRED:{target}")
    if registration.get("proposedCanonicalId") is not None:
        raise PromotionReadinessError(f"WORKER_CANONICAL_ID_MINT_FORBIDDEN:{target}")

    status = row.get("promotionReadinessStatus")
    if status not in READINESS:
        raise PromotionReadinessError(f"READINESS_STATUS_INVALID:{target}:{status}")
    gaps = row.get("blockingAuthorityGaps")
    if not isinstance(gaps, list) or any(not isinstance(x, str) or not x for x in gaps):
        raise PromotionReadinessError(f"BLOCKING_GAPS_INVALID:{target}")
    if status in BLOCKED and not gaps:
        raise PromotionReadinessError(f"BLOCKED_STATUS_REQUIRES_GAP:{target}:{status}")
    if status in {"READY_REUSE_EXISTING_AUTHORITY", "READY_FOR_CANONICAL_REGISTRATION"} and gaps:
        raise PromotionReadinessError(f"READY_STATUS_CANNOT_RETAIN_BLOCKING_GAPS:{target}:{status}")

    post = row.get("postRegistrationWorkEntryPotential")
    if post not in POST_REGISTRATION:
        raise PromotionReadinessError(f"POST_REGISTRATION_STATUS_INVALID:{target}:{post}")

    identity = row.get("identity")
    if not isinstance(identity, Mapping):
        raise PromotionReadinessError(f"IDENTITY_OBJECT_REQUIRED:{target}")

    if status == "READY_REUSE_EXISTING_AUTHORITY":
        if not _semantic_evidence(row):
            raise PromotionReadinessError(f"READY_REUSE_SEMANTIC_EVIDENCE_REQUIRED:{target}")
        for key in ("identityRecipeId", "identityAdapterId", "existingBindingId"):
            _require_string(identity.get(key), f"READY_REUSE_{key.upper()}_REQUIRED:{target}")
        if identity.get("bindingStatus") != "EXISTING_RESOLVED":
            raise PromotionReadinessError(f"READY_REUSE_BINDING_NOT_RESOLVED:{target}")
        if not _exact_physical_target(row):
            raise PromotionReadinessError(f"READY_REUSE_EXACT_PHYSICAL_TARGET_REQUIRED:{target}")

    if status == "READY_FOR_CANONICAL_REGISTRATION":
        if registration.get("deterministicRegistrationPossible") is not True:
            raise PromotionReadinessError(f"READY_REGISTRATION_DETERMINISM_REQUIRED:{target}")
        _require_string(registration.get("registrationCandidateKey"),
                        f"READY_REGISTRATION_CANDIDATE_KEY_REQUIRED:{target}")
        if not _semantic_evidence(row):
            raise PromotionReadinessError(f"READY_REGISTRATION_SEMANTIC_EVIDENCE_REQUIRED:{target}")
        for key in ("identityRecipeId", "identityAdapterId"):
            _require_string(identity.get(key), f"READY_REGISTRATION_{key.upper()}_REQUIRED:{target}")
        if not _exact_physical_target(row):
            raise PromotionReadinessError(f"READY_REGISTRATION_EXACT_PHYSICAL_TARGET_REQUIRED:{target}")

    projection = row.get("projectionResolution")
    if not isinstance(projection, Mapping):
        raise PromotionReadinessError(f"PROJECTION_RESOLUTION_REQUIRED:{target}")
    classification = projection.get("classification")
    if expected_surface == "pc" and truth_row.get("projectionStatus") == "MISSING":
        if classification not in PC_PROJECTION:
            raise PromotionReadinessError(f"PC_PROJECTION_CLASSIFICATION_INVALID:{target}:{classification}")
    if expected_surface == "mobile" and truth_row.get("projectionStatus") == "DRIFT":
        if classification not in MOBILE_PROJECTION:
            raise PromotionReadinessError(f"MOBILE_PROJECTION_CLASSIFICATION_INVALID:{target}:{classification}")


def validate_lane(repo_root: Path, surface: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if surface not in EXPECTED_COUNTS:
        raise PromotionReadinessError(f"SURFACE_INVALID:{surface}")
    truth = truth_by_surface(repo_root)[surface]
    expected_targets = set(truth)
    targets = [str(row.get("targetId") or "") for row in rows]
    duplicate = sorted(target for target, count in Counter(targets).items() if target and count > 1)
    if duplicate:
        raise PromotionReadinessError("DUPLICATE_TARGET_IDS:" + ",".join(duplicate))
    actual_targets = set(targets)
    missing = sorted(expected_targets - actual_targets)
    extra = sorted(actual_targets - expected_targets)
    if missing or extra or len(rows) != EXPECTED_COUNTS[surface]:
        raise PromotionReadinessError(
            f"LANE_ZERO_LOSS_FAILED:{surface}:count={len(rows)}:missing={len(missing)}:extra={len(extra)}"
        )
    for row in rows:
        validate_resolution(row, expected_surface=surface, truth_row=truth[str(row["targetId"])])
    statuses = Counter(str(row["promotionReadinessStatus"]) for row in rows)
    return {
        "status": "PASS_PROMOTION_READINESS_LANE",
        "surfaceKey": surface,
        "inputCount": EXPECTED_COUNTS[surface],
        "resolutionCount": len(rows),
        "uniqueTargetIds": len(actual_targets),
        "missing": 0,
        "extra": 0,
        "duplicateTargetIds": 0,
        "readinessStatusCounts": dict(sorted(statuses.items())),
    }


def validate_cross_surface_groups(groups: Sequence[Mapping[str, Any]], all_targets: set[str]) -> dict[str, Any]:
    keys: set[str] = set()
    semantic = visual_only = no_equivalence = 0
    for row in groups:
        key = _require_string(row.get("groupKey"), "GROUP_KEY_REQUIRED")
        if key in keys:
            raise PromotionReadinessError(f"DUPLICATE_CROSS_SURFACE_GROUP:{key}")
        keys.add(key)
        if row.get("schema") != GROUP_SCHEMA:
            raise PromotionReadinessError(f"GROUP_SCHEMA_INVALID:{key}")
        eq = row.get("equivalenceType")
        if eq not in EQUIVALENCE:
            raise PromotionReadinessError(f"GROUP_EQUIVALENCE_INVALID:{key}:{eq}")
        members = row.get("members")
        if not isinstance(members, list) or len(members) < 2:
            raise PromotionReadinessError(f"GROUP_MEMBERS_INVALID:{key}")
        surfaces = set()
        for member in members:
            if not isinstance(member, Mapping):
                raise PromotionReadinessError(f"GROUP_MEMBER_OBJECT_REQUIRED:{key}")
            target = str(member.get("targetId") or "")
            surface = member.get("surfaceKey")
            if target not in all_targets:
                raise PromotionReadinessError(f"GROUP_UNKNOWN_TARGET:{key}:{target}")
            surfaces.add(surface)
        if len(surfaces) < 2:
            raise PromotionReadinessError(f"GROUP_NOT_CROSS_SURFACE:{key}")
        semantic_refs = row.get("semanticAuthorityRefs")
        if not isinstance(semantic_refs, list):
            raise PromotionReadinessError(f"GROUP_SEMANTIC_REFS_INVALID:{key}")
        if row.get("canonicalCoalescingAllowed") is True and not semantic_refs:
            raise PromotionReadinessError(f"GROUP_COALESCING_WITHOUT_SEMANTIC_AUTHORITY:{key}")
        if eq == "VISUAL_ONLY_SIMILARITY":
            visual_only += 1
            if row.get("canonicalCoalescingAllowed") is not False:
                raise PromotionReadinessError(f"VISUAL_ONLY_COALESCING_FORBIDDEN:{key}")
        elif eq == "CANONICAL_SEMANTIC_EQUIVALENCE":
            semantic += 1
            if not semantic_refs:
                raise PromotionReadinessError(f"SEMANTIC_GROUP_REQUIRES_AUTHORITY:{key}")
        else:
            no_equivalence += 1
            if row.get("canonicalCoalescingAllowed") is not False:
                raise PromotionReadinessError(f"NO_EQUIVALENCE_COALESCING_FORBIDDEN:{key}")
    return {
        "status": "PASS_CROSS_SURFACE_GROUP_VALIDATION",
        "groupCount": len(groups),
        "canonicalSemanticEquivalenceCount": semantic,
        "visualOnlySimilarityCount": visual_only,
        "noProvenEquivalenceCount": no_equivalence,
    }


def compose_plan(
    repo_root: Path,
    rows_by_surface: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    cross_surface_groups: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    lane_results = []
    all_rows: list[Mapping[str, Any]] = []
    for surface in EXPECTED_COUNTS:
        rows = list(rows_by_surface.get(surface) or [])
        lane_results.append(validate_lane(repo_root, surface, rows))
        all_rows.extend(rows)

    targets = [str(row["targetId"]) for row in all_rows]
    if len(all_rows) != EXPECTED_TOTAL or len(set(targets)) != EXPECTED_TOTAL:
        raise PromotionReadinessError("GLOBAL_ZERO_LOSS_TARGET_ACCOUNTING_FAILED")
    group_result = validate_cross_surface_groups(cross_surface_groups, set(targets))

    status_counts = Counter(str(row["promotionReadinessStatus"]) for row in all_rows)
    ready_existing = status_counts["READY_REUSE_EXISTING_AUTHORITY"]
    ready_registration = status_counts["READY_FOR_CANONICAL_REGISTRATION"]
    not_applicable = status_counts["NOT_APPLICABLE"]
    blocked = EXPECTED_TOTAL - ready_existing - ready_registration - not_applicable

    candidate_keys: dict[str, list[str]] = defaultdict(list)
    for row in all_rows:
        if row["promotionReadinessStatus"] != "READY_FOR_CANONICAL_REGISTRATION":
            continue
        key = str(row["registration"].get("registrationCandidateKey") or "")
        candidate_keys[key].append(str(row["targetId"]))
    collisions = {
        key: sorted(targets_for_key)
        for key, targets_for_key in sorted(candidate_keys.items())
        if key and len(targets_for_key) > 1
    }

    post_counts = Counter(str(row["postRegistrationWorkEntryPotential"]) for row in all_rows)
    status = (
        "READY_FOR_CANONICAL_PROMOTION_INTEGRATION"
        if not collisions
        else "BLOCKED_PROMOTION_READINESS_INCOMPLETE"
    )
    return {
        "schema": PLAN_SCHEMA,
        "phase": PHASE,
        "inputCount": EXPECTED_TOTAL,
        "laneValidation": lane_results,
        "accounting": {
            "readyExistingAuthorityReuse": ready_existing,
            "readyCanonicalRegistrationProposals": ready_registration,
            "legitimatelyBlocked": blocked,
            "notApplicable": not_applicable,
            "sum": ready_existing + ready_registration + blocked + not_applicable,
            "readinessStatusCounts": dict(sorted(status_counts.items())),
        },
        "zeroLoss": {
            "missing": 0,
            "extra": 0,
            "duplicateTargetIds": 0,
            "semanticMutationCount": 0,
        },
        "collisions": {
            "registrationCandidateKeyCollisionCount": len(collisions),
            "registrationCandidateKeyCollisions": collisions,
        },
        "crossSurfaceGroups": list(cross_surface_groups),
        "crossSurfaceValidation": group_result,
        "workEntry": {
            "postRegistrationPotentialCounts": dict(sorted(post_counts.items())),
            "rerunPerformed": False,
            "note": "Potential only. Exact Work Entry must be rerun after canonical registration authority exists.",
        },
        "materialityCatalogInspected": False,
        "canonicalMutationPerformed": False,
        "productRuntimeMutationPerformed": False,
        "runtimeVisualGreen": False,
        "status": status,
    }


def baseline(repo_root: Path) -> dict[str, Any]:
    truth = corpus_truth(repo_root)
    rows = truth["records"]
    surface_counts = Counter(str(row.get("surfaceKey")) for row in rows)
    promotion = Counter(str(row.get("promotionStatus")) for row in rows)
    work = Counter(str(row.get("workEntryDecision")) for row in rows)
    physical = Counter(str(row.get("physicalStatus")) for row in rows)
    projection = Counter(str(row.get("projectionStatus")) for row in rows)
    return {
        "schema": "prisma.visual-promotion.promotion-readiness-baseline.v1",
        "phase": PHASE,
        "status": "PASS_PROMOTION_READINESS_BASELINE",
        "recordCount": len(rows),
        "surfaceCounts": dict(sorted(surface_counts.items())),
        "promotionStatusCounts": dict(sorted(promotion.items())),
        "workEntryDecisionCounts": dict(sorted(work.items())),
        "physicalStatusCounts": dict(sorted(physical.items())),
        "projectionStatusCounts": dict(sorted(projection.items())),
        "runtimeVisualGreen": False,
        "canonicalMutationPerformed": False,
        "productRuntimeMutationPerformed": False,
        "materialityCatalogInspected": False,
    }
