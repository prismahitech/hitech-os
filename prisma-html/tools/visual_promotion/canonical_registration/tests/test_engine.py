from __future__ import annotations
import hashlib, json, tempfile, unittest
from pathlib import Path
from prisma_html_test_bootstrap import import_engine

class CanonicalRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.engine=import_engine(); self.root=Path(tempfile.mkdtemp())
        source=self.root/"candidate.json"; source.write_text("{\"candidate\":true}",encoding="utf-8")
        self.source_digest=hashlib.sha256(source.read_bytes()).hexdigest()
        for name,data in [
            ("recipe.registry.json",{"schema":"prisma.identity.recipe.registry.v1","recipes":[],"recipeCount":0}),
            ("element-bindings.registry.json",{"schema":"prisma.identity.element-bindings.registry.v1","bindings":[]})]:
            p=self.root/"prisma-html/authority/rifat/identity/registries"/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(data),encoding="utf-8")
    def request(self):
        return {"schema":"prisma.visual.canonical-promotion-request.v1","requestId":"cpr-test-001",
        "target":{"targetId":"TGT.TEST.EXACT.V1","surfaceKey":"tablet"},"expectedCurrentHead":"a"*40,
        "currentTruth":{"schema":"prisma.visual.current-truth-snapshot.v1","repoHead":"a"*40,"targetIndexDigest":"b"*64,"identityDigest":"b"*64,"rifatDigest":"b"*64,"ndcDigest":"b"*64,"projectionDigest":"b"*64,"authorityMeshDigest":"b"*64,"layerMapDigest":"b"*64,"targetEvidenceDigest":"b"*64},
        "source":{"digest":self.source_digest,"candidateRef":"candidate.test","path":"candidate.json"},
        "decision":{"semanticAction":"REUSE_EXISTING","idInputs":{},"recipeAction":{"action":"CREATE_NEW","semanticKey":"table.governed",
        "registryEntry":{"familyId":"FAM.test","presetId":"PRESET.test","identityProfileId":"profile.test"}},
        "bindingAction":{"action":"CREATE_NEW","semanticKey":"tablet.table.exact","exactBinding":{"bindingId":"BND.test.table",
        "selector":{"surfaceId":"tablet","neutralMeaningId":"VIS.test"},"targets":[{"targetId":"TGT.TEST.EXACT.V1","ownerId":"owner","routeId":"route","regionId":"region","slotId":"slot","componentUiId":"component","layerId":"LYR.test"}]},
        "registryEntry":{"bindingId":"BND.test.table","selector":{"surfaceId":"tablet","neutralMeaningId":"VIS.test"},"status":"RESOLVED",
        "targets":[{"targetId":"TGT.TEST.EXACT.V1","ownerId":"owner","routeId":"route","regionId":"region","slotId":"slot","componentUiId":"component","layerId":"LYR.test"}]}},
        "layerAction":{"applicationLayerId":"APP.test","policy":"EXACT_TARGET_ONLY","writerKind":"CANONICAL_REGISTRATION"},"projectionAction":{"mode":"DEFERRED_DERIVATION","authorized":False}},
        "authorization":{"canonicalRegistrationAuthorized":True,"automaticSemanticInference":False,"automaticApplicationSource":False}}
    def test_requires_authorization(self):
        r=self.request(); r["authorization"]["canonicalRegistrationAuthorized"]=False
        with self.assertRaises(self.engine.CanonicalRegistrationError): self.engine.build_plan(r,self.root)
    def test_new_semantic_requires_adjudication(self):
        r=self.request(); r["decision"]["semanticAction"]="CREATE_NEW"
        with self.assertRaises(self.engine.CanonicalRegistrationError): self.engine.build_plan(r,self.root)
    def test_idempotent_repeat(self):
        r=self.request(); self.assertEqual(self.engine.register(r,self.root)["status"],"APPLIED"); self.assertEqual(self.engine.register(r,self.root)["status"],"NO_OP_IDEMPOTENT")
    def test_source_drift_rejected(self):
        r=self.request(); (self.root/"candidate.json").write_text("{\"candidate\":false}",encoding="utf-8")
        with self.assertRaises(self.engine.CanonicalRegistrationError): self.engine.build_plan(r,self.root)
    def test_rollback_is_transaction_scoped(self):
        r=self.request(); self.engine.register(r,self.root)
        rolled=self.engine.rollback(r["requestId"],self.root); self.assertEqual(rolled["status"],"ROLLED_BACK")
        data=json.loads((self.root/"prisma-html/authority/rifat/identity/registries/recipe.registry.json").read_text())
        self.assertEqual(data["recipeCount"],0)
    def test_rollback_refuses_newer_work(self):
        r=self.request(); self.engine.register(r,self.root)
        p=self.root/"prisma-html/authority/rifat/identity/registries/recipe.registry.json"; p.write_text(p.read_text().replace("}",",\"newerWork\":true}"),encoding="utf-8")
        with self.assertRaises(self.engine.UnsafeMutationError): self.engine.rollback(r["requestId"],self.root)
    def test_inferred_id_rejected(self):
        r=self.request(); r["decision"]["idInputs"]={"selector":".stockCell"}
        with self.assertRaises(Exception): self.engine.build_plan(r,self.root)

if __name__=="__main__": unittest.main()
