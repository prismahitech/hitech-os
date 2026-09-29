from __future__ import annotations

import copy
import unittest

from visual_operating_graph.next_safe_action import (
    NEXT_SCHEMA,
    WHAT_IF_SCHEMA,
    next_safe_action,
    what_if_digital_twin,
)


def synthetic_graph():
    return {
        "schema": "prisma.visual-operating-graph.v1",
        "observedCanonicalMain": "a" * 40,
        "sourceSetDigest": "digest",
        "stateClass": "CANONICAL_STATE",
        "productionCertified": False,
        "authorizationGranted": False,
        "nodes": [
            {
                "id": "CAPABILITY:visual.operating_graph_v1",
                "type": "CAPABILITY",
                "canonicality": "CANONICAL_AUTHORITY",
                "authorityDomain": "factory-ledger",
                "sourceRefs": ["PRISMA Factory Ledger/PRISMA_FACTORY_LEDGER.json"],
                "payload": {
                    "capabilityId": "visual.operating_graph_v1",
                    "classification": "BUILD",
                    "status": "WAVE1_SOURCE_READY",
                    "doNotRebuild": False,
                    "nextGate": "IMPLEMENT_READ_ONLY_GRAPH_BUILDER_SOURCESET_VERIFIER_AND_LIVE_PHASE_TRUTH_REDUCER",
                },
                "authorizationGranted": False,
            }
        ],
        "edges": [],
        "gaps": [],
        "provenance": [
            {
                "authorityDomain": "factory-ledger",
                "sourceRef": "PRISMA Factory Ledger/PRISMA_FACTORY_LEDGER.json",
                "sourceRole": "canonical-authority",
                "canonicality": "CANONICAL_AUTHORITY",
                "gitBlobSha": "a" * 40,
            }
        ],
    }


def synthetic_process_model():
    return {
        "blockerTaxonomy": {
            "mappings": [
                {
                    "family": "BINDING_GAP",
                    "sourceDomain": "visual-promotion",
                    "sourceCode": "BLOCKED_MISSING_BINDING",
                },
                {
                    "family": "SEMANTIC_AUTHORITY_GAP",
                    "sourceDomain": "visual-promotion",
                    "sourceCode": "BLOCKED_MISSING_SEMANTIC_AUTHORITY",
                },
            ]
        }
    }


class VisualOperatingGraphWave2Tests(unittest.TestCase):
    def test_capability_level_next_action_preserves_non_authorizing_boundary(self):
        result = next_safe_action(
            synthetic_graph(),
            process_model=synthetic_process_model(),
            current_head="a" * 40,
        )
        self.assertEqual(result["schemaVersion"], NEXT_SCHEMA)
        self.assertEqual(result["recommendedNextSafeAction"], "ACQUIRE_EVIDENCE")
        self.assertFalse(result["authorizationGranted"])
        self.assertFalse(result["productionCertified"])
        self.assertEqual(result["preservedSourceBlockers"], [])

    def test_exact_binding_blocker_recommends_binding_resolution(self):
        target = {
            "targetId": "TGT.CENSUS.PC.EXAMPLE.V1",
            "recordKind": "VISUAL_CONTROL_CENSUS_TARGET",
            "enforcement": "DISCOVERY_ONLY",
            "status": "BLOCKED",
            "blockers": ["semantic", "exact-binding", "projection-hash-drift"],
        }
        result = next_safe_action(
            synthetic_graph(),
            target_record=target,
            process_model=synthetic_process_model(),
            current_head="a" * 40,
        )
        self.assertEqual(result["recommendedNextSafeAction"], "RESOLVE_BINDING")
        self.assertIn("semantic", result["preservedSourceBlockers"])
        self.assertIn("BINDING_GAP", [row["family"] for row in result["blockerFamilies"]])
        self.assertIn("identity", result["missingAuthorities"])
        self.assertIn("REGISTER_TARGET_FIRST", result["possibleNextGates"])
        self.assertFalse(result["authorizationGranted"])

    def test_unknown_blocker_is_fail_closed(self):
        target = {
            "targetId": "TGT.UNKNOWN.V1",
            "recordKind": "VISUAL_CONTROL_CENSUS_TARGET",
            "enforcement": "DISCOVERY_ONLY",
            "status": "BLOCKED",
            "blockers": ["made-up-blocker"],
        }
        result = next_safe_action(
            synthetic_graph(),
            target_record=target,
            process_model=synthetic_process_model(),
            current_head="a" * 40,
        )
        self.assertEqual(result["recommendedNextSafeAction"], "STOP_BLOCKED")
        self.assertIn("UNCLASSIFIED_SOURCE_BLOCKER", [row["family"] for row in result["blockerFamilies"]])
        unknown_family = next(row for row in result["blockerFamilies"] if row["family"] == "UNCLASSIFIED_SOURCE_BLOCKER")
        self.assertTrue(unknown_family["requiresTaxonomyUpdate"])
        self.assertEqual(result["staleUnknownFlags"]["unknown"], [])

    def test_stale_graph_requires_revalidation(self):
        result = next_safe_action(
            synthetic_graph(),
            current_head="b" * 40,
            process_model=synthetic_process_model(),
        )
        self.assertEqual(result["recommendedNextSafeAction"], "REVALIDATE_AUTHORITY")
        self.assertIn(
            "GRAPH_OBSERVED_MAIN_DIFFERS_FROM_CURRENT_HEAD",
            result["staleUnknownFlags"]["stale"],
        )

    def test_what_if_is_copy_only_and_removes_only_modeled_blockers(self):
        graph = synthetic_graph()
        target = {
            "targetId": "TGT.CENSUS.PC.EXAMPLE.V1",
            "recordKind": "VISUAL_CONTROL_CENSUS_TARGET",
            "enforcement": "DISCOVERY_ONLY",
            "status": "BLOCKED",
            "blockers": ["semantic", "exact-binding", "projection-hash-drift"],
        }
        hypotheses = {
            "addValidBinding": True,
            "markProjectionReconciled": True,
        }
        before = copy.deepcopy(target)
        result = what_if_digital_twin(
            graph,
            target_record=target,
            hypotheses=hypotheses,
            process_model=synthetic_process_model(),
            current_head="a" * 40,
        )
        self.assertEqual(result["schemaVersion"], WHAT_IF_SCHEMA)
        self.assertTrue(result["hypothetical"])
        self.assertTrue(result["nonAuthoritative"])
        self.assertTrue(result["simulationOnly"])
        self.assertFalse(result["authorizationGranted"])
        self.assertEqual(sorted(result["blockersRemoved"], key=lambda row: row["blocker"]), [
            {"hypothesis": "addValidBinding", "blocker": "exact-binding"},
            {"hypothesis": "markProjectionReconciled", "blocker": "projection-hash-drift"},
        ])
        self.assertEqual(result["blockersRemaining"], ["semantic"])
        self.assertEqual(target, before)
        self.assertEqual(graph["authorizationGranted"], False)

    def test_what_if_unknown_hypothesis_is_not_authorization(self):
        result = what_if_digital_twin(
            synthetic_graph(),
            hypotheses={"resolutions": [{"kind": "invent_magic_authority"}]},
            process_model=synthetic_process_model(),
            current_head="a" * 40,
        )
        self.assertTrue(any("UNSUPPORTED_HYPOTHESIS_KIND" in x for x in result["assumptions"]))
        self.assertFalse(result["authorizationGranted"])


if __name__ == "__main__":
    unittest.main()
