from __future__ import annotations

import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from visual_promotion.promotion_readiness import (
    PHASE,
    PromotionReadinessError,
    check_all,
    compose_plan,
    validate_surface,
)

SURFACE_COUNTS = {"tablet": 2, "pc": 1, "mobile": 1, "shared-ui": 1}


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def certified_row(surface: str, target: str, sha: str):
    return {
        "schema": "prisma.visual-promotion.corpus-row.v1",
        "surfaceKey": surface,
        "targetId": target,
        "recordSha256": sha,
    }


def resolution(surface: str, target: str, sha: str, decision: str = "BLOCKED_MISSING_SEMANTIC_AUTHORITY"):
    blocked = decision.startswith("BLOCKED_")
    return {
        "schema": "prisma.visual-promotion.promotion-readiness-record.v1",
        "phase": PHASE,
        "surfaceKey": surface,
        "targetId": target,
        "sourceRecordSha256": sha,
        "promotionReadinessDecision": decision,
        "authorityReuseDisposition": "UNRESOLVED" if blocked else "REUSE_EXISTING",
        "projectionDebtClassification": "CURRENT",
        "canonicalMeaning": {
            "ndcPrimaryId": None if blocked else "ENT.sale",
            "visualMeaningId": None,
            "proposalKey": None,
            "resolution": "UNRESOLVED" if blocked else "REUSE_EXISTING",
        },
        "identity": {
            "identityRecipeId": None,
            "identityAdapterId": None,
            "existingBindingId": None,
            "bindingProposalKey": None,
        },
        "atlasfin": {"refs": [], "supportOnly": True},
        "physical": {
            "routeId": None, "regionId": None, "slotId": None, "componentId": None,
            "ownerId": None, "selector": "x", "implementationLayerId": "layer.x",
        },
        "application": {
            "applicationLayerId": None,
            "projectionPolicy": None,
            "exactTargetRegistrationReady": False,
        },
        "wouldPassWorkEntryAfterRegistration": None,
        "evidenceRefs": ["certified::" + target],
        "blockingAuthorityGaps": ["MISSING_NDC_PRIMARY_MEANING"] if blocked else [],
        "confidence": "high",
        "notes": [],
    }


class PromotionReadinessTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.cert = self.root / "cert"
        self.ready = self.root / "ready"
        rows = []
        n = 0
        for surface, count in SURFACE_COUNTS.items():
            for i in range(count):
                n += 1
                rows.append(certified_row(surface, f"TGT.{surface}.{i}", f"{n:064x}"))
        write_jsonl(self.cert / "CANDIDATE_CORPUS.jsonl", rows)
        self.cert_rows = {row["targetId"]: row for row in rows}

    def tearDown(self):
        self.td.cleanup()

    def _write_surface(self, surface: str, decisions=None):
        source = [row for row in self.cert_rows.values() if row["surfaceKey"] == surface]
        decisions = decisions or {}
        rows = [
            resolution(surface, row["targetId"], row["recordSha256"], decisions.get(row["targetId"], "BLOCKED_MISSING_SEMANTIC_AUTHORITY"))
            for row in source
        ]
        root = self.ready / surface
        write_jsonl(root / "RESOLUTION.jsonl", rows)
        write_jsonl(root / "REUSE.jsonl", [r for r in rows if r["promotionReadinessDecision"] == "READY_REUSE_EXISTING_AUTHORITY"])
        write_jsonl(root / "REGISTRATION_PROPOSALS.jsonl", [r for r in rows if r["promotionReadinessDecision"] == "READY_FOR_CANONICAL_REGISTRATION"])
        write_jsonl(root / "BLOCKED.jsonl", [r for r in rows if r["promotionReadinessDecision"].startswith("BLOCKED_")])
        write_jsonl(root / "PROJECTION_DEBT.jsonl", [])
        reuse = sum(r["promotionReadinessDecision"] == "READY_REUSE_EXISTING_AUTHORITY" for r in rows)
        register = sum(r["promotionReadinessDecision"] == "READY_FOR_CANONICAL_REGISTRATION" for r in rows)
        blocked = sum(r["promotionReadinessDecision"].startswith("BLOCKED_") for r in rows)
        manifest = {
            "schema": "prisma.visual-promotion.promotion-readiness-manifest.v1",
            "phase": PHASE,
            "surfaceKey": surface,
            "baseHead": "a" * 40,
            "certifiedCorpusManifestBlob": "b" * 40,
            "inputCount": len(rows),
            "resolutionCount": len(rows),
            "uniqueTargetCount": len(rows),
            "readyExistingAuthorityReuse": reuse,
            "readyCanonicalRegistration": register,
            "legitimatelyBlocked": blocked,
            "notApplicable": 0,
            "missingCount": 0,
            "extraCount": 0,
            "duplicateTargetIds": 0,
            "semanticMutationCount": 0,
            "materialityCatalogInspected": False,
            "productRuntimeMutationPerformed": False,
            "canonicalAuthorityMutationPerformed": False,
        }
        (root / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        (root / "SUMMARY.md").write_text("fixture\n", encoding="utf-8")
        return rows

    def _patch_expected_counts(self, module):
        return mock.patch.dict(module.SURFACE_COUNTS, SURFACE_COUNTS, clear=True)

    def test_source_record_sha_mismatch_fails_closed(self):
        import visual_promotion.promotion_readiness as module
        self._write_surface("tablet")
        path = self.ready / "tablet" / "RESOLUTION.jsonl"
        rows = [json.loads(x) for x in path.read_text().splitlines()]
        rows[0]["sourceRecordSha256"] = "f" * 64
        write_jsonl(path, rows)
        with self._patch_expected_counts(module):
            certified = module.load_certified_corpus(self.cert)
            with self.assertRaisesRegex(PromotionReadinessError, "SOURCE_RECORD_SHA_MISMATCH"):
                validate_surface("tablet", certified=certified, readiness_root=self.ready)

    def test_propose_new_cannot_embed_minted_canonical_id(self):
        import visual_promotion.promotion_readiness as module
        rows = self._write_surface("tablet")
        rows[0]["canonicalMeaning"] = {
            "ndcPrimaryId": "ENT.invented",
            "visualMeaningId": None,
            "proposalKey": "proposal.tablet.foo",
            "resolution": "PROPOSE_NEW",
        }
        write_jsonl(self.ready / "tablet" / "RESOLUTION.jsonl", rows)
        write_jsonl(self.ready / "tablet" / "BLOCKED.jsonl", rows)
        with self._patch_expected_counts(module):
            certified = module.load_certified_corpus(self.cert)
            with self.assertRaisesRegex(PromotionReadinessError, "PROPOSE_NEW_CANNOT_MINT_CANONICAL_ID"):
                validate_surface("tablet", certified=certified, readiness_root=self.ready)

    def test_ready_registration_requires_complete_exact_authority(self):
        import visual_promotion.promotion_readiness as module
        source = [row for row in self.cert_rows.values() if row["surfaceKey"] == "pc"][0]
        row = resolution("pc", source["targetId"], source["recordSha256"], "READY_FOR_CANONICAL_REGISTRATION")
        row["canonicalMeaning"] = {
            "ndcPrimaryId": "ENT.sale",
            "visualMeaningId": None,
            "proposalKey": None,
            "resolution": "REUSE_EXISTING",
        }
        row["authorityReuseDisposition"] = "REUSE_EXISTING"
        row["application"]["exactTargetRegistrationReady"] = True
        root = self.ready / "pc"
        write_jsonl(root / "RESOLUTION.jsonl", [row])
        write_jsonl(root / "REUSE.jsonl", [])
        write_jsonl(root / "REGISTRATION_PROPOSALS.jsonl", [row])
        write_jsonl(root / "BLOCKED.jsonl", [])
        write_jsonl(root / "PROJECTION_DEBT.jsonl", [])
        (root / "MANIFEST.json").write_text(json.dumps({
            "schema": "prisma.visual-promotion.promotion-readiness-manifest.v1",
            "phase": PHASE,
            "surfaceKey": "pc",
            "inputCount": 1,
            "resolutionCount": 1,
            "uniqueTargetCount": 1,
            "readyExistingAuthorityReuse": 0,
            "readyCanonicalRegistration": 1,
            "legitimatelyBlocked": 0,
            "notApplicable": 0,
            "missingCount": 0,
            "extraCount": 0,
            "duplicateTargetIds": 0,
            "semanticMutationCount": 0,
            "materialityCatalogInspected": False,
            "productRuntimeMutationPerformed": False,
            "canonicalAuthorityMutationPerformed": False,
        }), encoding="utf-8")
        with self._patch_expected_counts(module):
            certified = module.load_certified_corpus(self.cert)
            with self.assertRaisesRegex(PromotionReadinessError, "REGISTRATION_IDENTITY_RECIPE_REQUIRED"):
                validate_surface("pc", certified=certified, readiness_root=self.ready)


    def test_pending_is_not_fake_green(self):
        import visual_promotion.promotion_readiness as module
        with self._patch_expected_counts(module):
            result = check_all(cert_root=self.cert, readiness_root=self.ready)
        self.assertEqual(result["status"], "PENDING_SURFACE_HANDOFFS")
        self.assertFalse(result["canonicalAuthorityMutationAuthorized"])
        self.assertFalse(result["productRuntimeMutationAuthorized"])

    def test_complete_blocked_fixture_zero_loss_composes(self):
        import visual_promotion.promotion_readiness as module
        for surface in SURFACE_COUNTS:
            self._write_surface(surface)
        atlas = self.ready / "atlasfin-evidence"
        atlas.mkdir(parents=True)
        for name in (
            "REFERENCE_ANALYSIS.jsonl",
            "IDENTITY_RECIPE_REUSE_CANDIDATES.jsonl",
            "CROSS_SURFACE_EQUIVALENCE_EVIDENCE.jsonl",
            "VISUAL_ONLY_EQUIVALENCE.jsonl",
        ):
            (atlas / name).write_text("", encoding="utf-8")
        (atlas / "SUMMARY.md").write_text("fixture\n", encoding="utf-8")
        (atlas / "MANIFEST.json").write_text(json.dumps({
            "materialityCatalogInspected": False,
            "canonicalAuthorityMutationPerformed": False,
            "productRuntimeMutationPerformed": False,
        }), encoding="utf-8")
        with self._patch_expected_counts(module), mock.patch.object(module, "SURFACE_ORDER", tuple(SURFACE_COUNTS)):
            plan = compose_plan(cert_root=self.cert, readiness_root=self.ready)
        self.assertEqual(plan["status"], "READY_FOR_CANONICAL_PROMOTION_INTEGRATION")
        self.assertEqual(plan["blocked"], sum(SURFACE_COUNTS.values()))
        self.assertEqual(plan["readyCanonicalRegistration"], 0)
        self.assertFalse(plan["canonicalMutationAuthorized"])


if __name__ == "__main__":
    unittest.main()
