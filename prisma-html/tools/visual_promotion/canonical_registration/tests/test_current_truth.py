from __future__ import annotations

import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

from prisma_html_test_bootstrap import import_engine


class CurrentTruthTests(unittest.TestCase):
    def setUp(self):
        self.engine=import_engine()
        from canonical_registration import current_truth as truth
        self.truth=truth
        self.root=Path(tempfile.mkdtemp())
        os.environ["GITHUB_SHA"]="a"*40

        pkg=types.ModuleType("visual_application")
        pkg.__path__=[]
        idx=types.ModuleType("visual_application.target_index")
        self.target={
            "targetId":"TGT.CENSUS.TABLET.TEST.V1",
            "recordKind":"VISUAL_CONTROL_CENSUS_TARGET",
            "enforcement":"DISCOVERY_ONLY",
            "surface":"tablet",
        }
        idx.build_index=lambda root: {"records":[self.target]}
        sys.modules["visual_application"]=pkg
        sys.modules["visual_application.target_index"]=idx

        self._write_json("prisma-html/authority/rifat/prisma-ui/visual-control/target-index/manifest.json",{"schema":"target-index"})
        self._write_json("prisma-html/authority/rifat/identity/registries/recipe.registry.json",{"recipes":[]})
        self._write_json("prisma-html/authority/rifat/identity/registries/element-bindings.registry.json",{"bindings":[]})
        self._write_json("prisma-html/authority/rifat/prisma-ui/routes.json",{"routes":[]})
        self._write_json("prisma-html/authority/rifat/prisma-ui/surfaces.json",{"surfaces":[]})
        self._write_json("prisma-html/authority/rifat/prisma-ui/visual-control/owners.json",{})
        self._write_json("prisma-html/authority/rifat/prisma-ui/visual-control/components.json",{})
        self._write_json("prisma-html/authority/rifat/prisma-ui/visual-control/editable-slots.json",{})
        self._write_json("prisma-html/authority/rifat/prisma-ui/visual-control/layers.json",{})
        self._write_json("apps/terminal-de-venta-system/docs/ndc/registry/ndc_catalog_registry.json",{"catalogs":[]})
        self._write_json("apps/terminal-de-venta-system/docs/ndc/registry/ndc_edge_type_registry.json",{"edgeTypes":[]})
        self._write_json("apps/terminal-de-venta-system/docs/ndc/registry/ndc_prefix_registry.json",{"prefixes":[]})
        self._write_json("prisma-html/authority/rifat/visual-source-manifest.json",{"projections":[]})

    def _write_json(self, relative, value):
        path=self.root/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value),encoding="utf-8")

    def snapshot(self):
        return self.truth.capture_current_truth(
            self.root,
            evidence_target_id=self.target["targetId"],
            authority_mesh_digest="f"*64,
            layer_map_digest="0"*64,
        )

    def test_capture_and_verify_current_truth(self):
        snapshot=self.snapshot()
        self.truth.verify_current_truth(
            self.root,
            snapshot,
            evidence_target_id=self.target["targetId"],
        )

    def test_unexpected_ndc_path_blocks_even_with_self_consistent_snapshot(self):
        snapshot=self.snapshot()
        row=snapshot["sources"]["ndc"][0]
        row["path"]="apps/terminal-de-venta-system/docs/ndc/registry/does-not-exist.json"
        row.pop("externalRef",None)
        snapshot["ndcDigest"]=self.truth.sha256_json(snapshot["sources"]["ndc"])
        snapshot["snapshotId"]=self.truth.sha256_json({k:v for k,v in snapshot.items() if k!="snapshotId"})
        with self.assertRaises(self.engine.CanonicalRegistrationError):
            self.truth.verify_current_truth(self.root,snapshot,evidence_target_id=self.target["targetId"])

    def test_traversal_rifat_path_blocks(self):
        snapshot=self.snapshot()
        snapshot["sources"]["rifat"]=[{
            "path":"prisma-html/authority/rifat/prisma-ui/../identity/registries/recipe.registry.json",
            "sha256":"a"*64,
            "bytes":1,
        }]
        snapshot["rifatDigest"]=self.truth.sha256_json(snapshot["sources"]["rifat"])
        snapshot["snapshotId"]=self.truth.sha256_json({k:v for k,v in snapshot.items() if k!="snapshotId"})
        with self.assertRaises(self.engine.CanonicalRegistrationError):
            self.truth.verify_current_truth(self.root,snapshot,evidence_target_id=self.target["targetId"])


if __name__=="__main__":
    unittest.main()