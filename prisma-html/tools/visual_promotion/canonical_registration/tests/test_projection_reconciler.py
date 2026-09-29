from __future__ import annotations
import unittest
from prisma_html_test_bootstrap import load_projection_reconciler

class ProjectionReconcilerTests(unittest.TestCase):
    def setUp(self):
        self.r=load_projection_reconciler()
        self.truth={"schema":"prisma.visual.current-truth-snapshot.v1","snapshotId":"a"*64}

    def test_missing_projection_registers_missing(self):
        d=self.r.reconcile_projection(target_id="TGT.X",current_truth=self.truth,projection_classification="CANONICAL_PROJECTION_REQUIRED_MISSING",canonical_source_sha256="b"*64,canonical_output_sha256="c"*64)
        self.assertEqual(d.decision,"REGISTER_MISSING_PROJECTION")

    def test_ambiguous_blocks(self):
        d=self.r.reconcile_projection(target_id="TGT.X",current_truth=self.truth,projection_classification="AMBIGUOUS")
        self.assertEqual(d.decision,"BLOCK_AMBIGUOUS")

    def test_unproven_newer_runtime_blocks(self):
        d=self.r.reconcile_projection(target_id="TGT.X",current_truth=self.truth,projection_classification="PRODUCT_CANDIDATE_AUTHORITY_RECONCILIATION_REQUIRED",newer_runtime={"provenanceVerified":False})
        self.assertEqual(d.decision,"BLOCK_UNSAFE")

    def test_approved_divergence_is_explicit(self):
        d=self.r.reconcile_projection(target_id="TGT.X",current_truth=self.truth,projection_classification="INTENTIONAL_DIVERGENCE",intentional_divergence={"approved":True,"decisionRef":"decision::x"})
        self.assertEqual(d.decision,"ACCEPT_INTENTIONAL_DIVERGENCE")

if __name__=="__main__":
    unittest.main()
