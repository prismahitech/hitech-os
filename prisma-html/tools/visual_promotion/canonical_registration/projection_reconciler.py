from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DECISIONS = {
    "RESTORE_CANONICAL_PROJECTION",
    "ACCEPT_NEWER_RUNTIME",
    "ACCEPT_INTENTIONAL_DIVERGENCE",
    "REGISTER_MISSING_PROJECTION",
    "BLOCK_AMBIGUOUS",
    "BLOCK_UNSAFE",
}
SUPPORTED_CLASSES = {
    "CURRENT",
    "CANONICAL_PROJECTION_REQUIRED_MISSING",
    "INTENTIONALLY_NON_PROJECTED",
    "REFERENCE_GOVERNOR_ONLY",
    "STALE_AUTHORITY",
    "RIFAT_AUTHORITATIVE_PRODUCT_STALE",
    "PRODUCT_CANDIDATE_AUTHORITY_RECONCILIATION_REQUIRED",
    "INTENTIONAL_DIVERGENCE",
    "AMBIGUOUS",
    "NOT_APPLICABLE",
}

class ProjectionReconciliationError(ValueError):
    pass

@dataclass(frozen=True)
class ProjectionDecision:
    decision: str
    reason: str
    target_id: str
    evidence_refs: tuple[str, ...]

def reconcile_projection(
    *,
    target_id: str,
    current_truth: dict[str, Any],
    projection_classification: str,
    canonical_source_sha256: str | None = None,
    current_source_sha256: str | None = None,
    canonical_output_sha256: str | None = None,
    current_output_sha256: str | None = None,
    newer_runtime: dict[str, Any] | None = None,
    intentional_divergence: dict[str, Any] | None = None,
    ambiguity: list[str] | None = None,
) -> ProjectionDecision:
    if not isinstance(target_id, str) or not target_id:
        raise ProjectionReconciliationError("TARGET_ID_REQUIRED")
    if current_truth.get("schema") != "prisma.visual.current-truth-snapshot.v1":
        raise ProjectionReconciliationError("CURRENT_TRUTH_REQUIRED")
    if not current_truth.get("snapshotId"):
        raise ProjectionReconciliationError("CURRENT_TRUTH_SNAPSHOT_ID_REQUIRED")
    if projection_classification not in SUPPORTED_CLASSES:
        raise ProjectionReconciliationError("PROJECTION_CLASSIFICATION_INVALID")

    evidence = [f"current-truth::{current_truth['snapshotId']}"]

    if ambiguity:
        return ProjectionDecision("BLOCK_AMBIGUOUS", "explicit-ambiguity", target_id, tuple(sorted(set(ambiguity)) + tuple(evidence)))

    if projection_classification == "CURRENT":
        return ProjectionDecision(
            "ACCEPT_NEWER_RUNTIME" if newer_runtime else "ACCEPT_CURRENT",
            "projection-already-current",
            target_id,
            tuple(evidence),
        )

    if projection_classification == "CANONICAL_PROJECTION_REQUIRED_MISSING":
        if not canonical_source_sha256 or not canonical_output_sha256:
            raise ProjectionReconciliationError("CANONICAL_PROJECTION_MISSING_DIGESTS")
        return ProjectionDecision("REGISTER_MISSING_PROJECTION", "canonical-projection-missing", target_id, tuple(evidence))

    if projection_classification == "RIFAT_AUTHORITATIVE_PRODUCT_STALE":
        if not canonical_output_sha256 or current_output_sha256 != canonical_output_sha256:
            raise ProjectionReconciliationError("RESTORE_CANONICAL_OUTPUT_EVIDENCE_REQUIRED")
        return ProjectionDecision("RESTORE_CANONICAL_PROJECTION", "rifat-authoritative-product-stale", target_id, tuple(evidence))

    if projection_classification == "PRODUCT_CANDIDATE_AUTHORITY_RECONCILIATION_REQUIRED":
        if not newer_runtime or newer_runtime.get("provenanceVerified") is not True:
            return ProjectionDecision("BLOCK_UNSAFE", "newer-runtime-not-proven", target_id, tuple(evidence))
        evidence.append(str(newer_runtime.get("evidenceRef", "runtime")))
        return ProjectionDecision("ACCEPT_NEWER_RUNTIME", "newer-runtime-proven", target_id, tuple(sorted(set(evidence))))

    if projection_classification == "INTENTIONAL_DIVERGENCE":
        if not intentional_divergence or intentional_divergence.get("approved") is not True:
            return ProjectionDecision("BLOCK_UNSAFE", "intentional-divergence-not-approved", target_id, tuple(evidence))
        ref = intentional_divergence.get("decisionRef")
        if not isinstance(ref, str) or not ref:
            raise ProjectionReconciliationError("INTENTIONAL_DIVERGENCE_DECISION_REF_REQUIRED")
        evidence.append(ref)
        return ProjectionDecision("ACCEPT_INTENTIONAL_DIVERGENCE", "explicitly-approved", target_id, tuple(sorted(set(evidence))))

    if projection_classification in {"AMBIGUOUS"}:
        return ProjectionDecision("BLOCK_AMBIGUOUS", "projection-classification-ambiguous", target_id, tuple(evidence))

    if projection_classification in {"INTENTIONALLY_NON_PROJECTED", "REFERENCE_GOVERNOR_ONLY", "STALE_AUTHORITY", "NOT_APPLICABLE"}:
        return ProjectionDecision("BLOCK_UNSAFE", "projection-policy-needs-explicit-owner-decision", target_id, tuple(evidence))

    if projection_classification == "RIFAT_AUTHORITATIVE_PRODUCT_STALE":
        return ProjectionDecision("RESTORE_CANONICAL_PROJECTION", "rifat-authoritative", target_id, tuple(evidence))

    raise ProjectionReconciliationError("PROJECTION_DECISION_NOT_REACHED")
