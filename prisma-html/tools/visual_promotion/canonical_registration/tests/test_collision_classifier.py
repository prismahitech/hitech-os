from __future__ import annotations

import unittest

from prisma_html_test_bootstrap import load_collision_classifier


class CollisionClassifierTests(unittest.TestCase):
    def setUp(self):
        self.classifier=load_collision_classifier()

    def test_exact_record_is_classified(self):
        root=self._fixture({
            "records":[{"targetId":"TGT.TEST","semanticMeaningId":"ACT.primary","layerId":"LYR.test","bindingId":"BND.test"}],
            "bindings":[]
        })
        result=self.classifier.classify_collisions(
            root,target_id="TGT.TEST",surface_key="tablet",semantic_meaning_id="ACT.primary",
            proposed_binding_target={"ownerId":"o","routeId":"r","regionId":"g","slotId":"s","componentUiId":"c","selector":".x","implementationLayerId":"p"},
            proposed_binding_id="BND.test",proposed_layer_id="LYR.test")
        self.assertEqual([x["code"] for x in result],["DUPLICATE_EXACT"])

    def test_semantic_collision_is_not_resolved(self):
        root=self._fixture({
            "records":[{"targetId":"TGT.TEST","semanticMeaningId":"ACT.other","layerId":"LYR.test","bindingId":"BND.test"}],
            "bindings":[]
        })
        result=self.classifier.classify_collisions(
            root,target_id="TGT.TEST",surface_key="tablet",semantic_meaning_id="ACT.primary",
            proposed_binding_target={"ownerId":"o","routeId":"r","regionId":"g","slotId":"s","componentUiId":"c","selector":".x","implementationLayerId":"p"},
            proposed_binding_id="BND.test",proposed_layer_id="LYR.test")
        self.assertIn("SEMANTIC_COLLISION",[x["code"] for x in result])

    def _fixture(self, target_index):
        import json, tempfile
        from pathlib import Path
        root=Path(tempfile.mkdtemp())
        base=root/"prisma-html/authority/rifat/prisma-ui/visual-control/target-index"
        base.mkdir(parents=True)
        (base/"manifest.json").write_text("{}",encoding="utf-8")
        rifat=root/"prisma-html/authority/rifat"
        reg=rifat/"identity/registries"
        reg.mkdir(parents=True)
        (rifat/"prisma-ui/routes.json").write_text(json.dumps({"routes":[]}),encoding="utf-8")
        (rifat/"prisma-ui/surfaces.json").write_text(json.dumps({"surfaces":[]}),encoding="utf-8")
        (rifat/"prisma-ui/visual-control/owners.json").parent.mkdir(parents=True,exist_ok=True)
        (rifat/"prisma-ui/visual-control/owners.json").write_text(json.dumps({"componentOwnerSamples":[],"cssOwnerSamples":[],"regionOwnerSamples":[]}),encoding="utf-8")
        (rifat/"prisma-ui/visual-control/components.json").write_text(json.dumps({"components":[]}),encoding="utf-8")
        (rifat/"prisma-ui/visual-control/editable-slots.json").write_text(json.dumps({"slotUnitSamples":[]}),encoding="utf-8")
        (rifat/"prisma-ui/visual-control/layers.json").write_text(json.dumps({"layerSamples":[],"certifiedLayers":[]}),encoding="utf-8")
        (reg/"element-bindings.registry.json").write_text(json.dumps({"bindings":[]}),encoding="utf-8")
        fake=__import__("sys").modules["visual_application.target_index"]
        fake.build_index=lambda root: target_index
        return root

if __name__=="__main__":
    unittest.main()
