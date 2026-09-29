from __future__ import annotations
import hashlib, json, os, sys, tempfile, types, unittest
from pathlib import Path
from prisma_html_test_bootstrap import import_engine

class CanonicalRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.engine=import_engine(); self.root=Path(tempfile.mkdtemp())
        source=self.root/"candidate.json"; source.write_text("{\"candidate\":true}",encoding="utf-8")
        self.source_digest=hashlib.sha256(source.read_bytes()).hexdigest()
        base=self.root/"prisma-html/authority/rifat/prisma-ui"
        (base/"visual-control").mkdir(parents=True)
        (base/"routes.json").write_text(json.dumps({"routes":[{"route_id":"route"}]}),encoding="utf-8")
        owners={"componentOwnerSamples":[{"component_id":"owner"}],"cssOwnerSamples":[{"owner_id":"css"}],"regionOwnerSamples":[{"region_id":"region"}]}
        (base/"visual-control/owners.json").write_text(json.dumps(owners),encoding="utf-8")
        (base/"visual-control/components.json").write_text(json.dumps({"components":[{"component_id":"component"}]}),encoding="utf-8")
        (base/"visual-control/editable-slots.json").write_text(json.dumps({"slotUnitSamples":[{"slot_unit_id":"slot"}]}),encoding="utf-8")
        (base/"visual-control/layers.json").write_text(json.dumps({"layerSamples":[{"layer_id":"LYR.test"}],"certifiedLayers":[]}),encoding="utf-8")
        os.environ["GITHUB_SHA"]="a"*40
        ti=base/"visual-control/target-index"
        ti.mkdir(parents=True)
        target={"targetId":"TGT.TEST.EXACT.V1","surface":"tablet","recordKind":"EXACT_APPLICATION_TARGET","enforcement":"GVAE_ENFORCED"}
        (ti/"manifest.json").write_text(json.dumps(target),encoding="utf-8")
        fake_pkg=types.ModuleType("visual_application")
        fake_ti=types.ModuleType("visual_application.target_index")
        fake_ti.build_index=lambda root: {"records":[target]}
        fake_ti.build_index.__module__="visual_application.target_index"
        sys.modules["visual_application"]=fake_pkg
        sys.modules["visual_application.target_index"]=fake_ti
        ndc=self.root/"apps/terminal-de-venta-system/docs/ndc/registry"
        ndc.mkdir(parents=True)
        for name in ("ndc_prefix_registry.json","ndc_edge_type_registry.json","ndc_catalog_registry.json"):
            (ndc/name).write_text("{}",encoding="utf-8")
        (self.root/"prisma-html/authority/rifat/visual-source-manifest.json").write_text("{}",encoding="utf-8")
        self.current_truth = None
        for name,data in [
            ("recipe.registry.json",{"schema":"prisma.identity.recipe.registry.v1","recipes":[],"recipeCount":0}),
            ("element-bindings.registry.json",{"schema":"prisma.identity.element-bindings.registry.v1","bindings":[]})]:
            p=self.root/"prisma-html/authority/rifat/identity/registries"/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(data),encoding="utf-8")
    def request(self):
        from current_truth import capture_current_truth
        self.current_truth=capture_current_truth(self.root,target_id="TGT.TEST.EXACT.V1",authority_mesh_digest="d"*64,layer_map_digest="e"*64)
        return {"schema":"prisma.visual.canonical-promotion-request.v1","requestId":"cpr-test-001",
        "target":{"targetId":"TGT.TEST.EXACT.V1","surfaceKey":"tablet"},"expectedCurrentHead":"a"*40,
        "currentTruth":self.current_truth,
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
        p=self.root/"prisma-html/authority/rifat/identity/registries/recipe.registry.json"; newer=json.loads(p.read_text()); newer["newerWork"]=True; p.write_text(json.dumps(newer),encoding="utf-8")
        with self.assertRaises(self.engine.UnsafeMutationError): self.engine.rollback(r["requestId"],self.root)
    def test_inferred_id_rejected(self):
        r=self.request(); r["decision"]["idInputs"]={"selector":".stockCell"}
        with self.assertRaises(Exception): self.engine.build_plan(r,self.root)

if __name__=="__main__": unittest.main()
