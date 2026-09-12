from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

PHASE = "CANONICAL_PROMOTION_READINESS_RESOLUTION"
SURFACE_COUNTS = {"tablet": 929, "pc": 827, "mobile": 271, "shared-ui": 70}
SURFACE_ORDER = tuple(SURFACE_COUNTS)
READY_REUSE = "READY_REUSE_EXISTING_AUTHORITY"
READY_REGISTER = "READY_FOR_CANONICAL_REGISTRATION"
NOT_APPLICABLE = "NOT_APPLICABLE"
DECISIONS = {
    READY_REUSE,
    READY_REGISTER,
    "BLOCKED_MISSING_SEMANTIC_AUTHORITY",
    "BLOCKED_MISSING_BINDING",
    "BLOCKED_MISSING_APPLICATION_AUTHORITY",
    "BLOCKED_PROJECTION_AUTHORITY",
    "BLOCKED_PHYSICAL_DRIFT",
    "BLOCKED_MULTI_REGION_CONFLICT",
    "BLOCKED_NDC_AMBIGUITY",
    NOT_APPLICABLE,
}
REUSE_DISPOSITIONS = {"REUSE_EXISTING", "PROPOSE_NEW", "UNRESOLVED", NOT_APPLICABLE}
PROJECTION_CLASSES = {
    "CURRENT",
    "CANONICAL_PROJECTION_REQUIRED_MISSING",
    "INTENTIONALLY_NON_PROJECTED",
    "REFERENCE_GOVERNOR_ONLY",
    "STALE_AUTHORITY",
    "RIFAT_AUTHORITATIVE_PRODUCT_STALE",
    "PRODUCT_CANDIDATE_AUTHORITY_RECONCILIATION_REQUIRED",
    "INTENTIONAL_DIVERGENCE",
    "AMBIGUOUS",
    NOT_APPLICABLE,
}
BLOCKING_GAPS = {
    "MISSING_NDC_PRIMARY_MEANING",
    "MISSING_VISUAL_MEANING",
    "MISSING_IDENTITY_RECIPE",
    "MISSING_IDENTITY_ADAPTER",
    "MISSING_BINDING",
    "MISSING_ROUTE",
    "MISSING_REGION",
    "MISSING_SLOT",
    "MISSING_COMPONENT",
    "MISSING_OWNER",
    "MISSING_APPLICATION_LAYER",
    "MISSING_LAYER_APPLICATION_POLICY",
    "MISSING_EXACT_TARGET_AUTHORITY",
    "PROJECTION_MISSING",
    "PROJECTION_DRIFT",
    "PHYSICAL_DRIFT",
    "MULTI_REGION_CONFLICT",
    "NDC_AMBIGUITY",
    "SEMANTIC_AMBIGUITY",
    "AUTHORITY_RECONCILIATION_REQUIRED",
}
NON_DEBT_PROJECTION = {"CURRENT", NOT_APPLICABLE}
ROOT = Path(__file__).resolve().parents[2]
CERT_ROOT = ROOT / "governance" / "visual-promotion" / "contracts" / "corpus-certification"
READINESS_ROOT = ROOT / "governance" / "visual-promotion" / "promotion-readiness"


class PromotionReadinessError(RuntimeError):
    pass


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PromotionReadinessError(f"JSON_INVALID:{path}:{exc}") from exc


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise PromotionReadinessError(f"FILE_MISSING:{path}")
    rows: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PromotionReadinessError(f"JSONL_INVALID:{path}:{line_no}:{exc}") from exc
        if not isinstance(row, dict):
            raise PromotionReadinessError(f"JSONL_OBJECT_REQUIRED:{path}:{line_no}")
        rows.append(row)
    return rows


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _unique_strings(values: Iterable[Any], *, field: str) -> list[str]:
    out: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value:
            raise PromotionReadinessError(f"STRING_REQUIRED:{field}")
        out.append(value)
    if len(out) != len(set(out)):
        raise PromotionReadinessError(f"DUPLICATE_VALUE:{field}")
    return out


def load_certified_corpus(cert_root: Path = CERT_ROOT) -> dict[str, dict[str, Any]]:
    path = cert_root / "CANDIDATE_CORPUS.jsonl"
    rows = _load_jsonl(path)
    if len(rows) != 2097:
        raise PromotionReadinessError(f"CERTIFIED_CORPUS_COUNT:{len(rows)}")
    by_target: dict[str, dict[str, Any]] = {}
    counts = Counter()
    for row in rows:
        target = row.get("targetId")
        surface = row.get("surfaceKey")
        if not isinstance(target, str) or not target:
            raise PromotionReadinessError("CERTIFIED_TARGET_ID_REQUIRED")
        if surface not in SURFACE_COUNTS:
            raise PromotionReadinessError(f"CERTIFIED_SURFACE_INVALID:{surface}")
        if target in by_target:
            raise PromotionReadinessError(f"CERTIFIED_DUPLICATE_TARGET:{target}")
        record_sha = row.get("recordSha256")
        if not isinstance(record_sha, str) or len(record_sha) != 64:
            raise PromotionReadinessError(f"CERTIFIED_RECORD_SHA_REQUIRED:{target}")
        by_target[target] = row
        counts[surface] += 1
    if dict(counts) != SURFACE_COUNTS:
        raise PromotionReadinessError(f"CERTIFIED_SURFACE_COUNTS:{dict(counts)}")
    return by_target


def _validate_proposal_semantics(row: dict[str, Any]) -> None:
    target = row["targetId"]
    meaning = row.get("canonicalMeaning")
    if not isinstance(meaning, dict):
        raise PromotionReadinessError(f"CANONICAL_MEANING_REQUIRED:{target}")
    resolution = meaning.get("resolution")
    proposal = meaning.get("proposalKey")
    ndc = meaning.get("ndcPrimaryId")
    visual = meaning.get("visualMeaningId")
    if resolution == "PROPOSE_NEW":
        if ndc is not None or visual is not None:
            raise PromotionReadinessError(f"PROPOSE_NEW_CANNOT_MINT_CANONICAL_ID:{target}")
        if not isinstance(proposal, str) or not proposal.startswith("proposal."):
            raise PromotionReadinessError(f"PROPOSAL_KEY_REQUIRED:{target}")
    elif resolution == "REUSE_EXISTING":
        if proposal is not None:
            raise PromotionReadinessError(f"REUSE_EXISTING_CANNOT_HAVE_PROPOSAL_KEY:{target}")
        if ndc is None and visual is None:
            raise PromotionReadinessError(f"REUSE_EXISTING_MEANING_ID_REQUIRED:{target}")
    elif resolution in {"UNRESOLVED", NOT_APPLICABLE}:
        if proposal is not None:
            raise PromotionReadinessError(f"UNRESOLVED_CANNOT_HAVE_PROPOSAL_KEY:{target}")
    else:
        raise PromotionReadinessError(f"MEANING_RESOLUTION_INVALID:{target}:{resolution}")

    identity = row.get("identity")
    if not isinstance(identity, dict):
        raise PromotionReadinessError(f"IDENTITY_REQUIRED:{target}")
    binding = identity.get("existingBindingId")
    binding_proposal = identity.get("bindingProposalKey")
    if binding is not None and binding_proposal is not None:
        raise PromotionReadinessError(f"BINDING_REUSE_AND_PROPOSAL_CONFLICT:{target}")
    if binding_proposal is not None and (not isinstance(binding_proposal, str) or not binding_proposal.startswith("proposal.")):
        raise PromotionReadinessError(f"BINDING_PROPOSAL_KEY_INVALID:{target}")


def validate_resolution_row(
    row: dict[str, Any],
    *,
    expected_surface: str,
    certified: dict[str, dict[str, Any]],
) -> None:
    target = row.get("targetId")
    if row.get("schema") != "prisma.visual-promotion.promotion-readiness-record.v1":
        raise PromotionReadinessError(f"ROW_SCHEMA_INVALID:{target}")
    if row.get("phase") != PHASE:
        raise PromotionReadinessError(f"ROW_PHASE_INVALID:{target}")
    if row.get("surfaceKey") != expected_surface:
        raise PromotionReadinessError(f"ROW_SURFACE_INVALID:{target}:{row.get('surfaceKey')}")
    if target not in certified:
        raise PromotionReadinessError(f"EXTRA_TARGET:{expected_surface}:{target}")
    source = certified[target]
    if source["surfaceKey"] != expected_surface:
        raise PromotionReadinessError(f"TARGET_SURFACE_MISMATCH:{target}")
    if row.get("sourceRecordSha256") != source.get("recordSha256"):
        raise PromotionReadinessError(f"SOURCE_RECORD_SHA_MISMATCH:{target}")
    decision = row.get("promotionReadinessDecision")
    if decision not in DECISIONS:
        raise PromotionReadinessError(f"DECISION_INVALID:{target}:{decision}")
    if row.get("authorityReuseDisposition") not in REUSE_DISPOSITIONS:
        raise PromotionReadinessError(f"REUSE_DISPOSITION_INVALID:{target}")
    projection = row.get("projectionDebtClassification")
    if projection not in PROJECTION_CLASSES:
        raise PromotionReadinessError(f"PROJECTION_CLASS_INVALID:{target}:{projection}")
    gaps = row.get("blockingAuthorityGaps")
    if not isinstance(gaps, list) or any(x not in BLOCKING_GAPS for x in gaps):
        raise PromotionReadinessError(f"BLOCKING_GAP_INVALID:{target}")
    if len(gaps) != len(set(gaps)):
        raise PromotionReadinessError(f"BLOCKING_GAP_DUPLICATE:{target}")
    evidence = row.get("evidenceRefs")
    if not isinstance(evidence, list):
        raise PromotionReadinessError(f"EVIDENCE_REFS_REQUIRED:{target}")
    _unique_strings(evidence, field=f"evidenceRefs:{target}")
    atlasfin = row.get("atlasfin")
    if not isinstance(atlasfin, dict) or atlasfin.get("supportOnly") is not True:
        raise PromotionReadinessError(f"ATLASFIN_SUPPORT_ONLY_REQUIRED:{target}")
    _validate_proposal_semantics(row)

    if decision.startswith("BLOCKED_") and not gaps:
        raise PromotionReadinessError(f"BLOCKED_REQUIRES_AUTHORITY_GAP:{target}")
    if decision in {READY_REUSE, READY_REGISTER} and gaps:
        raise PromotionReadinessError(f"READY_CANNOT_HAVE_BLOCKING_GAPS:{target}")
    if decision == READY_REGISTER:
        app = row.get("application")
        if not isinstance(app, dict) or app.get("exactTargetRegistrationReady") is not True:
            raise PromotionReadinessError(f"REGISTRATION_READY_FLAG_REQUIRED:{target}")
        meaning = row["canonicalMeaning"]
        if meaning.get("resolution") not in {"REUSE_EXISTING", "PROPOSE_NEW"}:
            raise PromotionReadinessError(f"REGISTRATION_MEANING_NOT_RESOLVED:{target}")


def _target_set(rows: list[dict[str, Any]], path: Path) -> set[str]:
    targets: list[str] = []
    for row in rows:
        target = row.get("targetId")
        if not isinstance(target, str) or not target:
            raise PromotionReadinessError(f"TARGET_ID_REQUIRED:{path}")
        targets.append(target)
    if len(targets) != len(set(targets)):
        raise PromotionReadinessError(f"DUPLICATE_TARGET_IN_FILE:{path}")
    return set(targets)


def validate_surface(
    surface: str,
    *,
    certified: dict[str, dict[str, Any]],
    readiness_root: Path = READINESS_ROOT,
) -> dict[str, Any]:
    if surface not in SURFACE_COUNTS:
        raise PromotionReadinessError(f"SURFACE_INVALID:{surface}")
    root = readiness_root / surface
    if not (root / "RESOLUTION.jsonl").is_file():
        return {"surfaceKey": surface, "status": "PENDING", "expectedInputCount": SURFACE_COUNTS[surface]}

    rows = _load_jsonl(root / "RESOLUTION.jsonl")
    expected = {target for target, row in certified.items() if row["surfaceKey"] == surface}
    actual = _target_set(rows, root / "RESOLUTION.jsonl")
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        raise PromotionReadinessError(f"MISSING_TARGETS:{surface}:{len(missing)}:{missing[:3]}")
    if extra:
        raise PromotionReadinessError(f"EXTRA_TARGETS:{surface}:{len(extra)}:{extra[:3]}")
    if len(rows) != SURFACE_COUNTS[surface]:
        raise PromotionReadinessError(f"RESOLUTION_COUNT:{surface}:{len(rows)}")

    by_target = {row["targetId"]: row for row in rows}
    for row in rows:
        validate_resolution_row(row, expected_surface=surface, certified=certified)

    expected_subsets = {
        "REUSE.jsonl": {t for t, r in by_target.items() if r["promotionReadinessDecision"] == READY_REUSE},
        "REGISTRATION_PROPOSALS.jsonl": {t for t, r in by_target.items() if r["promotionReadinessDecision"] == READY_REGISTER},
        "BLOCKED.jsonl": {t for t, r in by_target.items() if str(r["promotionReadinessDecision"]).startswith("BLOCKED_")},
        "PROJECTION_DEBT.jsonl": {t for t, r in by_target.items() if r["projectionDebtClassification"] not in NON_DEBT_PROJECTION},
    }
    for name, expected_targets in expected_subsets.items():
        path = root / name
        subset = _load_jsonl(path) if path.is_file() else []
        actual_targets = _target_set(subset, path)
        if actual_targets != expected_targets:
            raise PromotionReadinessError(
                f"SUBSET_MISMATCH:{surface}:{name}:expected={len(expected_targets)}:actual={len(actual_targets)}"
            )

    counts = Counter(r["promotionReadinessDecision"] for r in rows)
    ready_reuse = counts[READY_REUSE]
    ready_register = counts[READY_REGISTER]
    blocked = sum(v for k, v in counts.items() if k.startswith("BLOCKED_"))
    not_applicable = counts[NOT_APPLICABLE]
    if ready_reuse + ready_register + blocked + not_applicable != len(rows):
        raise PromotionReadinessError(f"ACCOUNTING_MISMATCH:{surface}")

    manifest_path = root / "MANIFEST.json"
    if not manifest_path.is_file():
        raise PromotionReadinessError(f"MANIFEST_MISSING:{surface}")
    manifest = _load_json(manifest_path)
    expected_manifest = {
        "schema": "prisma.visual-promotion.promotion-readiness-manifest.v1",
        "phase": PHASE,
        "surfaceKey": surface,
        "inputCount": SURFACE_COUNTS[surface],
        "resolutionCount": len(rows),
        "uniqueTargetCount": len(actual),
        "readyExistingAuthorityReuse": ready_reuse,
        "readyCanonicalRegistration": ready_register,
        "legitimatelyBlocked": blocked,
        "notApplicable": not_applicable,
        "missingCount": 0,
        "extraCount": 0,
        "duplicateTargetIds": 0,
        "semanticMutationCount": 0,
        "materialityCatalogInspected": False,
        "productRuntimeMutationPerformed": False,
        "canonicalAuthorityMutationPerformed": False,
    }
    for key, value in expected_manifest.items():
        if manifest.get(key) != value:
            raise PromotionReadinessError(f"MANIFEST_FIELD_MISMATCH:{surface}:{key}:{manifest.get(key)}:{value}")

    return {
        "surfaceKey": surface,
        "status": "PASS",
        "inputCount": len(rows),
        "readyExistingAuthorityReuse": ready_reuse,
        "readyCanonicalRegistration": ready_register,
        "legitimatelyBlocked": blocked,
        "notApplicable": not_applicable,
        "projectionDebtCount": len(expected_subsets["PROJECTION_DEBT.jsonl"]),
        "resolutionDigest": _sha256_json(rows),
    }


def validate_atlasfin_evidence(readiness_root: Path = READINESS_ROOT) -> dict[str, Any]:
    root = readiness_root / "atlasfin-evidence"
    manifest_path = root / "MANIFEST.json"
    if not manifest_path.is_file():
        return {"status": "PENDING"}
    required = (
        "REFERENCE_ANALYSIS.jsonl",
        "IDENTITY_RECIPE_REUSE_CANDIDATES.jsonl",
        "CROSS_SURFACE_EQUIVALENCE_EVIDENCE.jsonl",
        "VISUAL_ONLY_EQUIVALENCE.jsonl",
        "SUMMARY.md",
    )
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise PromotionReadinessError("ATLASFIN_EVIDENCE_FILES_MISSING:" + ",".join(missing))
    manifest = _load_json(manifest_path)
    if manifest.get("materialityCatalogInspected") is not False:
        raise PromotionReadinessError("ATLASFIN_MATERIALITY_MUST_REMAIN_UNINSPECTED")
    if manifest.get("canonicalAuthorityMutationPerformed") is not False:
        raise PromotionReadinessError("ATLASFIN_AUTHORITY_MUTATION_FORBIDDEN")
    if manifest.get("productRuntimeMutationPerformed") is not False:
        raise PromotionReadinessError("ATLASFIN_RUNTIME_MUTATION_FORBIDDEN")

    semantic = _load_jsonl(root / "CROSS_SURFACE_EQUIVALENCE_EVIDENCE.jsonl")
    visual = _load_jsonl(root / "VISUAL_ONLY_EQUIVALENCE.jsonl")
    for row in semantic:
        sources = row.get("semanticAuthoritySources")
        if not isinstance(sources, list) or not sources:
            raise PromotionReadinessError("CROSS_SURFACE_SEMANTIC_AUTHORITY_REQUIRED")
        if row.get("evidenceBasis") == "ATLASFIN_RECIPE_EQUALITY_ONLY":
            raise PromotionReadinessError("RECIPE_EQUALITY_CANNOT_BE_SEMANTIC_AUTHORITY")
    for row in visual:
        if row.get("canonicalCoalescingAllowed") is True:
            raise PromotionReadinessError("VISUAL_ONLY_CANNOT_COALESCE")
    return {
        "status": "PASS",
        "semanticEvidenceRows": len(semantic),
        "visualOnlyRows": len(visual),
    }


def check_all(
    *,
    cert_root: Path = CERT_ROOT,
    readiness_root: Path = READINESS_ROOT,
) -> dict[str, Any]:
    certified = load_certified_corpus(cert_root)
    surfaces = [validate_surface(s, certified=certified, readiness_root=readiness_root) for s in SURFACE_ORDER]
    atlasfin = validate_atlasfin_evidence(readiness_root)
    pending = [row["surfaceKey"] for row in surfaces if row["status"] == "PENDING"]
    if atlasfin["status"] == "PENDING":
        pending.append("atlasfin-evidence")
    passed = [row for row in surfaces if row["status"] == "PASS"]
    accounted = sum(row["inputCount"] for row in passed)
    return {
        "schema": "prisma.visual-promotion.promotion-readiness-check.v1",
        "phase": PHASE,
        "status": "PENDING_SURFACE_HANDOFFS" if pending else "PASS_PROMOTION_READINESS_INPUTS",
        "certifiedInputCount": len(certified),
        "validatedInputCount": accounted,
        "pending": pending,
        "surfaces": surfaces,
        "atlasfinEvidence": atlasfin,
        "productRuntimeMutationAuthorized": False,
        "canonicalAuthorityMutationAuthorized": False,
    }


def compose_plan(
    *,
    cert_root: Path = CERT_ROOT,
    readiness_root: Path = READINESS_ROOT,
) -> dict[str, Any]:
    checked = check_all(cert_root=cert_root, readiness_root=readiness_root)
    if checked["status"] != "PASS_PROMOTION_READINESS_INPUTS":
        raise PromotionReadinessError("SURFACE_HANDOFFS_PENDING:" + ",".join(checked["pending"]))

    all_rows: list[dict[str, Any]] = []
    for surface in SURFACE_ORDER:
        all_rows.extend(_load_jsonl(readiness_root / surface / "RESOLUTION.jsonl"))
    if len(all_rows) != 2097:
        raise PromotionReadinessError(f"GLOBAL_COUNT:{len(all_rows)}")
    targets = [row["targetId"] for row in all_rows]
    if len(targets) != len(set(targets)):
        raise PromotionReadinessError("GLOBAL_DUPLICATE_TARGET_ID")

    counts = Counter(row["promotionReadinessDecision"] for row in all_rows)
    ready_reuse = counts[READY_REUSE]
    ready_register = counts[READY_REGISTER]
    blocked = sum(v for k, v in counts.items() if k.startswith("BLOCKED_"))
    not_applicable = counts[NOT_APPLICABLE]
    if ready_reuse + ready_register + blocked + not_applicable != 2097:
        raise PromotionReadinessError("GLOBAL_ZERO_LOSS_ACCOUNTING_FAILED")

    registration_keys = sorted(
        row["canonicalMeaning"]["proposalKey"]
        for row in all_rows
        if row["promotionReadinessDecision"] == READY_REGISTER
        and row["canonicalMeaning"].get("proposalKey") is not None
    )
    if len(registration_keys) != len(set(registration_keys)):
        raise PromotionReadinessError("DUPLICATE_CANONICAL_PROPOSAL_KEY")

    return {
        "schema": "prisma.visual-promotion.canonical-promotion-plan.v1",
        "phase": PHASE,
        "status": "READY_FOR_CANONICAL_PROMOTION_INTEGRATION",
        "inputCount": 2097,
        "readyExistingAuthorityReuse": ready_reuse,
        "readyCanonicalRegistration": ready_register,
        "blocked": blocked,
        "notApplicable": not_applicable,
        "missingCount": 0,
        "extraCount": 0,
        "duplicateTargetIds": 0,
        "semanticMutationCount": 0,
        "safeExactReuseTargets": sorted(
            row["targetId"] for row in all_rows if row["promotionReadinessDecision"] == READY_REUSE
        ),
        "safeExactRegistrationProposalKeys": registration_keys,
        "blockedTargets": sorted(
            row["targetId"] for row in all_rows if str(row["promotionReadinessDecision"]).startswith("BLOCKED_")
        ),
        "crossSurfaceSemanticGroups": sorted(canonical_group_keys),
        "canonicalMutationAuthorized": False,
        "productRuntimeMutationAuthorized": False,
        "resolutionCorpusDigest": _sha256_json(all_rows),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate/compose PRISMA canonical promotion readiness evidence.")
    ap.add_argument("--cert-root", type=Path, default=CERT_ROOT)
    ap.add_argument("--readiness-root", type=Path, default=READINESS_ROOT)
    ap.add_argument("--compose", action="store_true")
    ns = ap.parse_args()
    try:
        out = compose_plan(cert_root=ns.cert_root, readiness_root=ns.readiness_root) if ns.compose else check_all(
            cert_root=ns.cert_root, readiness_root=ns.readiness_root
        )
    except PromotionReadinessError as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    if ns.compose and out["status"] != "READY_FOR_CANONICAL_PROMOTION_INTEGRATION":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
