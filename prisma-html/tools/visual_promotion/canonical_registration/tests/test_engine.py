from __future__ import annotations
import json, tempfile, unittest
from pathlib import Path
from prisma_html_test_bootstrap import import_engine

class CanonicalRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.engine=import_engine(); self.root=Path(tempfile.mkdtemp())
        for name,data in [
            ("recipe.registry.json",{"schema":"prisma.identity.recipe.registry.v1","recipes":[],"recipeCount":0}),
            ("element-bindings.registry.json",{"schema":"prisma.identity.element-bindings.registry.v1","bindings":[]})]:
            p=self.root/"prisma-html/authority/rifat/identity/registries"/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(data),encoding="utf-8")
    def request(self):
        return {"schema":"prisma.visual.canonical-promotion-request.v1","requestId":"cpr-test-001",
        "target":{"targetId":"TGT.TEST.EXACT.V1","surfaceKey":"tablet"},"expectedCurrentHead":"a"*40,
        "currentTruth":{"schema":"prisma.visual.current-truth-snapshot.v1","repoHead":"a"*40,"targetIndexDigest":"b"*64},
        "source":{"digest":"c"*64,"candidateRef":"candidate.test"},
        "decision":{"semanticAction":"REUSE_EXISTING","idInputs":{},"recipeAction":{"action":"CREATE_NEW","semanticKey":"table.governed",
        "registryEntry":{"familyId":"FAM.test","presetId":"PRESET.test","identityProfileId":"profile.test"}},
        "bindingAction":{"action":"CREATE_NEW","semanticKey":"tablet.table.exact","exactBinding":{"bindingId":"BND.test.table",
        "selector":{"surfaceId":"tablet","neutralMeaningId":"VIS.test"},"targets":[{"targetId":"TGT.TEST.EXACT.V1","ownerId":"owner","routeId":"route","regionId":"region","slotId":"slot","componentUiId":"component","layerId":"LYR.test"}]},
        "registryEntry":{"bindingId":"BND.test.table","selector":{"surfaceId":"tablet","neutralMeaningId":"VIS.test"},"status":"RESOLVED",
        "targets":[{"targetId":"TGT.TEST.EXACT.V1","ownerId":"owner","routeId":"route","regionId":"region","slotId":"slot","componentUiId":"component","layerId":"LYR.test"}]}},
        "layerAction":{"applicationLayerId":"APP.test","policy":"EXACT_TARGET_ONLY"},"projectionAction":{"mode":"DEFERRED_DERIVATION","authorized":False}},
        "authorization":{"canonicalRegistrationAuthorized":True,"automaticSemanticInference":False,"automaticApplicationSource":False}}
    def test_requires_authorization(self):
        r=self.request(); r["authorization"]["canonicalRegistrationAuthorized"]=False
        with self.assertRaises(self.engine.CanonicalRegistrationError): self.engine.build_plan(r,self.root)
    def test_new_semantic_requires_adjudication(self):
        r=self.request(); r["decision"]["semanticAction"]="CREATE_NEW"
        with self.assertRaises(self.engine.CanonicalRegistrationError): self.engine.build_plan(r,self.root)
    def test_idempotent_repeat(self):
        r=self.request(); self.assertEqual(self.engine.register(r,self.root)["status"],"APPLIED"); self.assertEqual(self.engine.register(r,self.root)["status"],"NO_OP_IDEMPOTENT")
    def test_inferred_id_rejected(self):
        r=self.request(); r["decision"]["idInputs"]={"selector":".stockCell"}
        with self.assertRaises(Exception): self.engine.build_plan(r,self.root)

if __name__=="__main__": unittest.main()
