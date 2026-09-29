from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from prisma_html_test_bootstrap import import_engine


class CurrentTruthTests(unittest.TestCase):
    def setUp(self):
        self.engine=import_engine()
        from canonical_registration import current_truth as truth
        self.truth=truth
        self.root=Path("/tmp/prisma-current-truth-fixture")
        self.root.mkdir(parents=True,exist_ok=True)
        os.environ["GITHUB_SHA"]="a"*40
        import sys
        import types
        pkg=types.ModuleType("visual_application")
        pkg.__path__=[]
        idx=types.ModuleType("visual_application.target_index")
        self.target={"targetId":"TGT.CENSUS.TABLET.TEST.V1","recordKind":"VISUAL_CONTROL_CENSUS_TARGET","enforcement":"DISCOVERY_ONLY","surface":"tablet"}
        idx.build_index=lambda root: {"records":[self.target]}
        sys.modules["visual_application"]=pkg
        sys.modules["visual_application.target_index"]=idx

    def snapshot(self):
        buckets={
            "targetIndex":"a"*64,
            "identity":"b"*64,
            "rifat":"c"*64,
            "ndc":"d"*64,
            "projection":"e"*64,
            "authorityMesh":"f"*64,
            "layerMap":"0"*64,
        }
        sources={k:[{"externalRef":k,"sha256":v}] for k,v in buckets.items()}
        snapshot={
            "schema":"prisma.visual.current-truth-snapshot.v1",
            "repoHead":"a"*40,
            "targetIndexDigest":buckets["targetIndex"],
            "identityDigest":buckets["identity"],
            "rifatDigest":buckets["rifat"],
            "ndcDigest":buckets["ndc"],
            "projectionDigest":buckets["projection"],
            "authorityMeshDigest":buckets["authorityMesh"],
            "layerMapDigest":buckets["layerMap"],
            "targetEvidenceDigest":self.truth.sha256_json(self.target),
            "evidenceTargetId":"TGT.CENSUS.TABLET.TEST.V1",
            "sources":sources,
        }
        snapshot["snapshotId"]=self.truth.sha256_json(snapshot)
        return snapshot

    def test_unexpected_authority_bucket_path_blocks(self):
        snapshot=self.snapshot()
        snapshot["sources"]["ndc"]=[{
            "path":"prisma-html/authority/rifat/identity/registries/recipe.registry.json",
            "sha256":"a"*64,
            "bytes":1,
        }]
        snapshot["snapshotId"]=self.truth.sha256_json({k:v for k,v in snapshot.items() if k!="snapshotId"})
        with self.assertRaises(self.engine.CanonicalRegistrationError):
            self.truth.verify_current_truth(self.root,snapshot,evidence_target_id="TGT.CENSUS.TABLET.TEST.V1")

    def test_traversal_authority_path_blocks(self):
        snapshot=self.snapshot()
        snapshot["sources"]["rifat"]=[{
            "path":"prisma-html/authority/rifat/prisma-ui/../identity/registries/recipe.registry.json",
            "sha256":"a"*64,
            "bytes":1,
        }]
        snapshot["snapshotId"]=self.truth.sha256_json({k:v for k,v in snapshot.items() if k!="snapshotId"})
        with self.assertRaises(self.engine.CanonicalRegistrationError):
            self.truth.verify_current_truth(self.root,snapshot,evidence_target_id="TGT.CENSUS.TABLET.TEST.V1")

    def test_valid_external_evidence_still_passes(self):
        snapshot=self.snapshot()
        self.truth.verify_current_truth(self.root,snapshot,evidence_target_id="TGT.CENSUS.TABLET.TEST.V1")


if __name__=="__main__":
    unittest.main()
