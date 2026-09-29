from __future__ import annotations

import unittest

from prisma_html_test_bootstrap import load_builder


class RequestBuilderTests(unittest.TestCase):
    def setUp(self):
        self.builder=load_builder()

    def row(self):
        return {
            "promotionReadinessDecision":"READY_FOR_CANONICAL_REGISTRATION",
            "surfaceKey":"tablet",
            "targetId":"TGT.CENSUS.TABLET.TEST.V1",
            "canonicalMeaning":{"resolution":"REUSE_EXISTING","ndcPrimaryId":"ACT.primary"},
            "identity":{"identityRecipeId":"REC.test.table"},
            "physical":{
                "routeId":"tablet.route","regionId":"tablet.region","slotId":"tablet.slot",
                "componentId":"component","componentUiId":"component.ui",
                "ownerId":"owner","implementationLayerId":"physical.layer","selector":".table",
            },
            "application":{"applicationLayerId":"LYR.APP.TEST"},
            "semanticAuthority":{
                "authorityDomain":"ndc","writerKind":"NDC_CURATION",
                "canonicalMeaningId":"ACT.primary","decisionRef":"ndc::decision.test",
                "canonicalTargetId":"TGT.test.canonical.V1","canonicalLayerId":"LYR.test",
                "applicationPolicy":"EXACT_TARGET_ONLY","applicationLayerDecisionRef":"rifat::policy.test",
            },
        }

    def test_builder_requires_exact_component_ui_id(self):
        row=self.row(); row["physical"].pop("componentUiId")
        with self.assertRaises(self.builder.RequestBuilderError):
            self.builder.build_request_from_readiness(
                row,current_truth={"schema":"prisma.visual.current-truth-snapshot.v1"},
                expected_current_head="a"*40,
                authorization={"canonicalRegistrationAuthorized":True,"automaticSemanticInference":False,"automaticApplicationSource":False},
                source={"digest":"b"*64,"path":"candidate.json"},
            )

    def test_builder_uses_explicit_application_policy(self):
        row=self.row()
        request=self.builder.build_request_from_readiness(
            row,current_truth={"schema":"prisma.visual.current-truth-snapshot.v1"},
            expected_current_head="a"*40,
            authorization={"canonicalRegistrationAuthorized":True,"automaticSemanticInference":False,"automaticApplicationSource":False},
            source={"digest":"b"*64,"path":"candidate.json"},
        )
        self.assertEqual(request["decision"]["layerAction"]["policy"],"EXACT_TARGET_ONLY")
        self.assertEqual(request["decision"]["layerAction"]["authorityDomain"],"rifat")
        self.assertEqual(request["decision"]["layerAction"]["decisionRef"],"rifat::policy.test")


if __name__=="__main__":
    unittest.main()

    def test_builder_does_not_supply_canonical_target_id(self):
        request=self.builder.build_request_from_readiness(
            self.row(),current_truth={"schema":"prisma.visual.current-truth-snapshot.v1"},
            expected_current_head="a"*40,
            authorization={"canonicalRegistrationAuthorized":True,"automaticSemanticInference":False,"automaticApplicationSource":False},
            source={"digest":"b"*64,"path":"candidate.json"},
        )
        self.assertIsNone(request["target"]["targetId"])
        self.assertEqual(request["target"]["censusTargetId"],"TGT.CENSUS.TABLET.TEST.V1")
