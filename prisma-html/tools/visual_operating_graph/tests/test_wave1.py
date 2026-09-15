from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from visual_operating_graph.builder import build_operating_graph, build_master_map
from visual_operating_graph.live_phase_reducer import reduce_live_phase_truth
from visual_operating_graph.source_set_verifier import (
    canonical_json,
    find_repo_root,
    git_blob_sha_bytes,
    verify_source_set,
)


class VisualOperatingGraphWave1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = find_repo_root(Path(__file__))

    def test_real_sourceset_is_fail_closed_and_usable_on_branch(self) -> None:
        result = verify_source_set(self.repo)
        self.assertEqual(result["status"], "PASS_SOURCESET_VERIFIED")
        self.assertEqual(result["blockingFindingCount"], 0)
        self.assertIn(result["headDisposition"], {"EXACT_HEAD", "NON_RELEVANT_DRIFT"})
        self.assertFalse(result["authorizationGranted"])
        self.assertFalse(result["productionCertified"])

    def test_builder_is_deterministic_and_non_authorizing(self) -> None:
        graph_a, verification_a = build_operating_graph(self.repo)
        graph_b, verification_b = build_operating_graph(self.repo)
        self.assertEqual(canonical_json(graph_a), canonical_json(graph_b))
        self.assertEqual(canonical_json(verification_a), canonical_json(verification_b))
        self.assertEqual(graph_a["stateClass"], "CANONICAL_STATE")
        self.assertFalse(graph_a["productionCertified"])
        self.assertGreater(len(graph_a["nodes"]), 0)
        self.assertGreater(len(graph_a["edges"]), 0)
        self.assertTrue(all(row.get("authorizationGranted") is False for row in graph_a["nodes"]))
        self.assertTrue(all(row.get("authorizationGranted") is False for row in graph_a["edges"]))

    def test_master_map_is_deterministic(self) -> None:
        graph, verification = build_operating_graph(self.repo)
        master_a = build_master_map(graph, verification, self.repo)
        master_b = build_master_map(copy.deepcopy(graph), copy.deepcopy(verification), self.repo)
        self.assertEqual(canonical_json(master_a), canonical_json(master_b))
        self.assertFalse(master_a["authorizationGranted"])
        self.assertFalse(master_a["productionCertified"])

    def test_live_overlay_never_overwrites_canonical(self) -> None:
        graph, verification = build_operating_graph(self.repo)
        canonical_phase = next(
            (
                row.get("payload", {}).get("phase")
                for row in graph["nodes"]
                if row.get("type") == "PHASE"
            ),
            None,
        )
        result = reduce_live_phase_truth(
            graph,
            verification,
            live_overlay=[
                {
                    "id": "worker-1",
                    "baseHead": graph["observedCanonicalMain"],
                    "workerHead": "1" * 40,
                    "statusBranchHead": "2" * 40,
                    "receiptHead": "3" * 40,
                    "writerRole": "STATUS_WRITER",
                }
            ],
        )
        self.assertEqual(result["canonicalPhase"], canonical_phase)
        self.assertEqual(result["liveOverlay"][0]["canonicality"], "LIVE_OVERLAY")
        self.assertTrue(any(row["code"] == "RECEIPT_WORKER_HEAD_DISAGREEMENT" for row in result["findings"]))
        self.assertFalse(result["authorizationGranted"])
        self.assertFalse(result["mutationAllowed"])

    def test_temporal_staleness_is_explicit(self) -> None:
        graph, verification = build_operating_graph(self.repo)
        result = reduce_live_phase_truth(
            graph,
            verification,
            live_overlay=[
                {
                    "id": "worker-stale",
                    "baseHead": graph["observedCanonicalMain"],
                    "workerHead": graph["observedCanonicalMain"],
                    "writerRole": "STATUS_WRITER",
                    "timestamp": "2026-09-15T00:00:00+00:00",
                }
            ],
            now="2026-09-15T03:00:01+00:00",
            freshness_seconds=3600,
        )
        self.assertTrue(any(row["class"] == "TEMPORAL_STALENESS" for row in result["findings"]))

    def test_git_blob_hash_matches_git_object_contract(self) -> None:
        self.assertEqual(
            git_blob_sha_bytes(b"test content\n"),
            "d670460b4b4aece5915caf5c68d12f560a9fe3e4",
        )

    def test_canonical_json_is_order_stable(self) -> None:
        self.assertEqual(
            canonical_json({"b": 2, "a": {"y": 2, "x": 1}}),
            canonical_json({"a": {"x": 1, "y": 2}, "b": 2}),
        )

    def test_unknown_live_writer_is_drift_not_authority(self) -> None:
        graph, verification = build_operating_graph(self.repo)
        result = reduce_live_phase_truth(
            graph,
            verification,
            live_overlay=[
                {
                    "id": "bad-writer",
                    "baseHead": graph["observedCanonicalMain"],
                    "workerHead": graph["observedCanonicalMain"],
                    "writerRole": "CANONICAL_WRITER",
                }
            ],
        )
        self.assertTrue(any(row["class"] == "WRITER_DRIFT" for row in result["findings"]))
        self.assertFalse(result["authorizationGranted"])


if __name__ == "__main__":
    unittest.main()
