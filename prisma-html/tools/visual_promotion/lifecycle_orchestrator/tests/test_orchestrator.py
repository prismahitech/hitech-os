from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from visual_promotion.lifecycle_orchestrator import orchestrator


HEAD = "a" * 40


class LifecycleOrchestratorTests(unittest.TestCase):
    def test_cloud_center_is_known_but_has_no_visual_authority(self):
        self.assertEqual(
            orchestrator._surface_blocker("cloud-center"),
            "SURFACE_VISUAL_AUTHORITY_MISSING:cloud-center",
        )

    def test_discovery_requires_one_exact_target_and_reuses_work_entry_gate(self):
        census_id = "TGT.CENSUS.tablet.drawer.1"
        row = {
            "targetId": census_id,
            "surface": "tablet",
            "recordKind": "VISUAL_CONTROL_CENSUS_TARGET",
            "enforcement": "DISCOVERY_ONLY",
        }
        request = {"surface": "tablet", "expectedHead": HEAD, "targetIds": [census_id]}
        decision = {"decision": "REGISTER_TARGET_FIRST", "details": {"targetIds": [census_id]}}
        authority = {"index": {"records": [row]}}
        with patch.object(orchestrator, "_git_head", return_value=HEAD), patch.object(
            orchestrator.visual_work_entry_gate, "decide_request", return_value=decision
        ):
            result = orchestrator._discover(Path("."), request, authority=authority)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["target"]["targetId"], census_id)

    def test_discovery_fails_closed_for_multiple_candidates(self):
        first = "TGT.CENSUS.tablet.drawer.1"
        second = "TGT.CENSUS.tablet.drawer.2"
        request = {"surface": "tablet", "expectedHead": HEAD}
        decision = {"decision": "REGISTER_TARGET_FIRST", "details": {"targetIds": [first, second]}}
        with patch.object(orchestrator, "_git_head", return_value=HEAD), patch.object(
            orchestrator.visual_work_entry_gate, "decide_request", return_value=decision
        ):
            result = orchestrator._discover(Path("."), request, authority={"index": {"records": []}})
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("EXACTLY_ONE_TARGET_REQUIRED", result["blockers"])

    def test_advance_is_ordered_persisted_and_idempotent_on_replay(self):
        request = {
            "schema": orchestrator.SCHEMA,
            "lifecycleId": "vlo-test-001",
            "transition": "DISCOVER",
            "expectedHead": HEAD,
            "payload": {"workEntryRequest": {"surface": "tablet"}},
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(orchestrator, "_git_head", return_value=HEAD), patch.object(
            orchestrator, "_execute_stage", return_value={"status": "PASS", "target": {"targetId": "TGT.CENSUS.x"}}
        ):
            root = Path(tmp)
            first = orchestrator.advance_transition(request, root)
            replay = orchestrator.advance_transition(request, root)
            state = orchestrator.inspect_lifecycle(root, "vlo-test-001")
            self.assertEqual(first, replay)
            self.assertEqual(state["currentStage"], "DISCOVER")
            self.assertEqual(len(state["history"]), 1)
            out_of_order = {**request, "transition": "APPLY", "payload": {"applyKind": "product_visual"}}
            with self.assertRaisesRegex(orchestrator.LifecycleOrchestratorError, "TRANSITION_OUT_OF_ORDER"):
                orchestrator.advance_transition(out_of_order, root)

    def test_inspection_of_unstarted_lifecycle_has_no_side_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = orchestrator.inspect_lifecycle(root, "vlo-unstarted-01")
            self.assertEqual(state["status"], "NOT_STARTED")
            self.assertEqual(state["nextTransition"], "DISCOVER")
            self.assertFalse((root / orchestrator.LIFECYCLES_ROOT).exists())

    def test_product_visual_apply_is_blocked_without_invoking_registration_or_gvae(self):
        record = {"authorizationResult": {"canonicalRegistrationAuthorized": True}}
        with patch.object(orchestrator.engine, "register") as register:
            result = orchestrator._execute_stage(
                Path("."),
                "APPLY",
                record,
                {"applyKind": "product_visual"},
            )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("CAPABILITY_DOES_NOT_AUTHORIZE_PRODUCT_RUNTIME_MUTATION", result["blockers"])
        register.assert_not_called()

    def test_receipt_digest_drift_is_rejected(self):
        request = {
            "schema": orchestrator.SCHEMA,
            "lifecycleId": "vlo-receipt-001",
            "transition": "DISCOVER",
            "expectedHead": HEAD,
            "payload": {"workEntryRequest": {"surface": "tablet"}},
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(orchestrator, "_git_head", return_value=HEAD), patch.object(
            orchestrator, "_execute_stage", return_value={"status": "PASS"}
        ):
            root = Path(tmp)
            receipt = orchestrator.advance_transition(request, root)
            receipt_path = root / "prisma-html/governance/visual-promotion/lifecycle-orchestrator/receipts" / request["lifecycleId"] / f"{receipt['transitionId']}.json"
            data = json.loads(receipt_path.read_text(encoding="utf-8"))
            data["result"]["status"] = "BLOCKED"
            receipt_path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(orchestrator.LifecycleOrchestratorError, "RECEIPT_DIGEST_MISMATCH"):
                orchestrator.load_receipt(root, request["lifecycleId"], receipt["transitionId"])

    def test_supersession_uses_canonical_terminal_state_and_receipt(self):
        request = {
            "schema": orchestrator.SCHEMA,
            "lifecycleId": "vlo-old-001",
            "transition": "DISCOVER",
            "expectedHead": HEAD,
            "payload": {"workEntryRequest": {"surface": "tablet"}},
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(orchestrator, "_git_head", return_value=HEAD), patch.object(
            orchestrator, "_execute_stage", return_value={"status": "PASS"}
        ):
            root = Path(tmp)
            orchestrator.advance_transition(request, root)
            receipt = orchestrator.supersede_lifecycle(
                root,
                "vlo-old-001",
                superseded_by="vlo-next-001",
                decision_ref="NDC-DECISION-1",
            )
            state = orchestrator.inspect_lifecycle(root, "vlo-old-001")
            self.assertEqual(receipt["result"]["status"], "PASS")
            self.assertEqual(state["status"], "SUPERSEDED")
            self.assertEqual(state["supersession"]["supersededBy"], "vlo-next-001")
            self.assertEqual(state["receiptChecks"][-1]["integrity"], "VERIFIED")
            with self.assertRaisesRegex(orchestrator.LifecycleOrchestratorError, "LIFECYCLE_SUPERSEDED_TERMINAL"):
                orchestrator.advance_transition(request, root)

    def test_runtime_certification_requires_exact_gvae_verify_and_all_runtime_passes(self):
        target_id = "TGT.VISUAL.tablet.drawer.1"
        census_id = "TGT.CENSUS.tablet.drawer.1"
        record = {
            "transitionHead": HEAD,
            "registrationPlan": {"targetId": target_id, "censusTargetId": census_id, "surfaceKey": "tablet"},
            "registrationRequest": {
                "decision": {"bindingAction": {"exactBinding": {"targets": [{"routeId": "tablet.pos"}]}}}
            },
        }
        runtime = {
            "schema": "prisma.visual.runtime-evidence.v1",
            "target": {"targetId": target_id, "censusTargetId": census_id, "route": "tablet.pos"},
            "viewport": {"width": 1280, "height": 800},
            "browser": {"name": "Chromium"},
            "build": {"commitSha": HEAD},
            "sourceProjection": {"commitSha": HEAD},
            "before": {"sha256": "1" * 64, "path": "evidence/before.png"},
            "after": {"sha256": "2" * 64, "path": "evidence/after.png"},
            "runtimeState": "PASS",
            "consoleState": "PASS",
            "networkState": "PASS",
            "geometryVerdict": "PASS",
            "accessibilityVerdict": "PASS",
            "visualVerdict": "PASS",
        }
        payload = {
            "gvaeVerifyRequest": {"schema": "prisma.visual.application.request.v1", "mode": "VERIFY", "targetId": target_id, "authorityCommit": HEAD},
            "runtimeEvidence": runtime,
        }
        with patch.object(
            orchestrator,
            "gvae_verify",
            return_value={
                "status": "STATIC_GREEN",
                "targetId": target_id,
                "evidenceClassification": "SOURCE_STATIC_ONLY",
                "runtimeVisualGreen": False,
            },
        ) as verify:
            result = orchestrator._execute_stage(Path("."), "RUNTIME_VERIFY", record, payload)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["certification"]["certification_state"], "VISUAL_CERTIFIED")
        self.assertEqual(result["gvaeVerification"]["status"], "STATIC_GREEN")
        verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
