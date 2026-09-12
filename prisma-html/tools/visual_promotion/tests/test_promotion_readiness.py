from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from visual_promotion.promotion_readiness import (
    PromotionReadinessError,
    compose_plan,
    validate_cross_surface_groups,
    validate_lane,
)

SURFACES = {"tablet": 929, "pc": 827, "mobile": 271, "shared-ui": 70}


def truth_row(surface: str, i: int) -> dict:
    return {
        "surfaceKey": surface,
        "targetId": f"TGT.TEST.{surface.upper().replace('-', '_')}.{i:04d}",
        "physicalStatus": "CURRENT",
        "projectionStatus": "CURRENT",
        "promotionStatus": "REGISTER_TARGET_FIRST",
        "workEntryDecision": "REGISTER_TARGET_FIRST",
    }


def write_truth(root: Path) -> dict[str, list[dict]]:
    grouped = {surface: [truth_row(surface, i) for i in range(count)] for surface, count in SURFACES.items()}
    payload = {
        "schema": "prisma.visual-promotion.certified-current-truth.v1",
        "status": "CERTIFIED_CORPUS_CURRENT_TRUTH",
        "recordCount": 2097,
        "records": [row for surface in SURFACES for row in grouped[surface]],
    }
    path = root / "prisma-html/governance/visual-promotion/contracts/corpus-certification"
    path.mkdir(parents=True)
    (path / "CURRENT_TRUTH.json").write_text(json.dumps(payload), encoding="utf-8")
    return grouped


def resolution(source: dict, *, status: str = "BLOCKED_MISSING_SEMANTIC_AUTHORITY") -> dict:
    ready = status == "READY_FOR_CANONICAL_REGISTRATION"
    return {
        "schema": "prisma.visual-promotion.promotion-resolution.v1",
        "phase": "CANONICAL_PROMOTION_READINESS_RESOLUTION",
        "surfaceKey": source["surfaceKey"],
        "targetId": source["targetId"],
        "input": {
            "certificationStatus": "VALID_REGISTER_TARGET_FIRST",
            "promotionStatus": source["promotionStatus"],
            "workEntryDecision": source["workEntryDecision"],
            "physicalStatus": source["physicalStatus"],
            "projectionStatus": source["projectionStatus"],
        },
        "canonicalMeaning": {
            "ndcPrimaryId": "ENT.TEST" if ready else None,
            "ndcResolutionStatus": "RESOLVED_EXISTING" if ready else "UNRESOLVED",
            "visualMeaningId": None,
            "visualMeaningStatus": "UNRESOLVED",
            "proposedMeaningSlug": None,
            "semanticAuthorityRefs": ["ndc::ENT.TEST"] if ready else [],
        },
        "identity": {
            "identityRecipeId": "REC.test" if ready else None,
            "identityAdapterId": "prisma.adapter.test.v1" if ready else None,
            "existingBindingId": None,
            "bindingStatus": "CANDIDATE" if ready else "BLOCKED",
        },
        "atlasfin": {"matchStatus": "NO_MATCH", "referenceIds": [], "semanticAuthorityGranted": False},
        "physicalTarget": {
            "routeId": None, "regionId": None, "slotId": None, "componentId": None,
            "ownerId": "owner.test" if ready else None,
            "implementationLayerId": "layer.test" if ready else None,
            "applicationLayerId": None,
        },
        "projectionResolution": {"classification": "NOT_APPLICABLE", "authorityRefs": []},
        "registration": {
            "registrationCandidateKey": "reg:" + source["targetId"] if ready else None,
            "deterministicRegistrationPossible": ready,
            "proposedCanonicalId": None,
        },
        "promotionReadinessStatus": status,
        "blockingAuthorityGaps": [] if ready else ["semantic-authority"],
        "postRegistrationWorkEntryPotential": (
            "MAY_REACH_GVAE_EXACT_APPLY_AFTER_REGISTRATION_AND_RERUN" if ready
            else "STILL_BLOCKED_AFTER_REGISTRATION"
        ),
        "crossSurfaceEvidenceRefs": [],
        "confidence": "high",
        "evidenceRefs": ["target-index::" + source["targetId"]],
        "notes": [],
    }


class PromotionReadinessTests(unittest.TestCase):
    def test_lane_requires_exact_zero_loss(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            grouped = write_truth(root)
            rows = [resolution(x) for x in grouped["tablet"]]
            result = validate_lane(root, "tablet", rows)
            self.assertEqual(result["resolutionCount"], 929)
            with self.assertRaisesRegex(PromotionReadinessError, "LANE_ZERO_LOSS_FAILED"):
                validate_lane(root, "tablet", rows[:-1])

    def test_ready_registration_requires_no_minted_canonical_id(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            grouped = write_truth(root)
            rows = [resolution(x) for x in grouped["pc"]]
            rows[0] = resolution(grouped["pc"][0], status="READY_FOR_CANONICAL_REGISTRATION")
            rows[0]["registration"]["proposedCanonicalId"] = "BND.ILLEGAL"
            with self.assertRaisesRegex(PromotionReadinessError, "WORKER_CANONICAL_ID_MINT_FORBIDDEN"):
                validate_lane(root, "pc", rows)

    def test_recipe_similarity_cannot_coalesce_without_semantic_authority(self):
        groups = [{
            "schema": "prisma.visual-promotion.cross-surface-semantic-group.v1",
            "groupKey": "g",
            "equivalenceType": "VISUAL_ONLY_SIMILARITY",
            "members": [
                {"surfaceKey": "tablet", "targetId": "A"},
                {"surfaceKey": "pc", "targetId": "B"},
            ],
            "semanticAuthorityRefs": [],
            "visualEvidenceRefs": ["atlasfin::REC.card.governed.v2"],
            "confidence": "medium",
            "canonicalCoalescingAllowed": True,
            "reason": "same recipe only",
        }]
        with self.assertRaisesRegex(PromotionReadinessError, "VISUAL_ONLY_COALESCING_FORBIDDEN"):
            validate_cross_surface_groups(groups, {"A", "B"})

    def test_compose_accounts_exact_2097(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            grouped = write_truth(root)
            lanes = {surface: [resolution(x) for x in rows] for surface, rows in grouped.items()}
            plan = compose_plan(root, lanes)
            self.assertEqual(plan["inputCount"], 2097)
            self.assertEqual(plan["accounting"]["sum"], 2097)
            self.assertEqual(plan["zeroLoss"]["missing"], 0)
            self.assertFalse(plan["canonicalMutationPerformed"])
            self.assertFalse(plan["productRuntimeMutationPerformed"])


if __name__ == "__main__":
    unittest.main()
