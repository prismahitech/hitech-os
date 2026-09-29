from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

from prisma_html_test_bootstrap import import_engine


class CanonicalRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.engine=import_engine()
        self.root=Path(tempfile.mkdtemp())
        os.environ["GITHUB_SHA"]="a"*40
        visual_pkg=types.ModuleType("visual_application")
        visual_pkg.__path__=[]
        ti=types.ModuleType("visual_application.target_index")
        ti.build_index=lambda root: self._fake_index(root)
        sys.modules["visual_application"]=visual_pkg
        sys.modules["visual_application.target_index"]=ti

        source=self.root/"candidate.json"
        source.write_text('{"candidate":true}',encoding="utf-8")
        self.source_digest=hashlib.sha256(source.read_bytes()).hexdigest()

        base=self.root/"prisma-html/authority/rifat/prisma-ui"
        (base/"visual-control").mkdir(parents=True)
        (base/"routes.json").write_text(json.dumps({"routes":[{"route_id":"route"}]}),encoding="utf-8")
        (base/"surfaces.json").write_text(json.dumps({"surfaces":[{"surface_id":"tablet"}]}),encoding="utf-8")
        (base/"visual-control/owners.json").write_text(json.dumps({
            "componentOwnerSamples":[{"component_id":"owner"}],
            "cssOwnerSamples":[{"owner_id":"css"}],
            "regionOwnerSamples":[{"region_id":"region"}],
        }),encoding="utf-8")
        (base/"visual-control/components.json").write_text(json.dumps({"components":[{"component_id":"component"}]}),encoding="utf-8")
        (base/"visual-control/editable-slots.json").write_text(json.dumps({"slotUnitSamples":[{"slot_unit_id":"slot"}]}),encoding="utf-8")
        (base/"visual-control/layers.json").write_text(json.dumps({
            "layerSamples":[{"layer_id":"LYR.test"}],"certifiedLayers":[]
        }),encoding="utf-8")

        ti=base/"visual-control/target-index"
        ti.mkdir(parents=True)
        (ti/"manifest.json").write_text(json.dumps({"fixture":True}),encoding="utf-8")
        self.census_target={
            "targetId":"TGT.CENSUS.TABLET.TEST.V1",
            "surface":"tablet",
            "recordKind":"VISUAL_CONTROL_CENSUS_TARGET",
            "enforcement":"DISCOVERY_ONLY",
        }
        self.canonical_target=None

        ndc=self.root/"apps/terminal-de-venta-system/docs/ndc/registry"
        ndc.mkdir(parents=True)
        for name in ("ndc_prefix_registry.json","ndc_edge_type_registry.json","ndc_catalog_registry.json"):
            (ndc/name).write_text("{}",encoding="utf-8")
        (self.root/"prisma-html/authority/rifat/visual-source-manifest.json").write_text("{}",encoding="utf-8")

        pkg=__import__("sys").modules["visual_application.target_index"]
        def build_index(root):
            bindings_path=root/"prisma-html/authority/rifat/identity/registries/element-bindings.registry.json"
            records=[self.census_target]
            if bindings_path.exists():
                doc=json.loads(bindings_path.read_text(encoding="utf-8"))
                for binding in doc.get("bindings",[]):
                    for target in binding.get("targets",[]):
                        if isinstance(target,dict) and target.get("targetId")!="TGT.CENSUS.TABLET.TEST.V1":
                            records.append({
                                "targetId":target["targetId"],
                                "surface":(binding.get("selector") or {}).get("surfaceId"),
                                "recordKind":"EXACT_APPLICATION_TARGET",
                                "enforcement":"GVAE_ENFORCED",
                            })
            return {"records":records}
        pkg.build_index=build_index

        reg=self.root/"prisma-html/authority/rifat/identity/registries"
        reg.mkdir(parents=True)
        (reg/"recipe.registry.json").write_text(json.dumps({
            "schema":"prisma.identity.recipe.registry.v1",
            "recipes":[{
                "recipeId":"REC.test.table",
                "familyId":"FAM.test","presetId":"PRESET.test",
                "identityProfileId":"profile.test",
                "path":"recipes/REC.test.table.json",
                "recipeCoverageStatus":"COMPLETE",
                "fileSha256":"0"*64,
            }],
            "recipeCount":1,
        }),encoding="utf-8")
        recipe_source=reg/"recipes/REC.new.recipe.json"
        recipe_source.parent.mkdir(parents=True,exist_ok=True)
        recipe_source.write_text("{\"recipe\":\"new\"}",encoding="utf-8")
        self.new_recipe_sha=hashlib.sha256(recipe_source.read_bytes()).hexdigest()
        (reg/"element-bindings.registry.json").write_text(json.dumps({
            "schema":"prisma.identity.element-bindings.registry.v1",
            "bindings":[],
        }),encoding="utf-8")
        self.current_truth=self._snapshot()


    def _fake_index(self, root):
        bindings_path=root/"prisma-html/authority/rifat/identity/registries/element-bindings.registry.json"
        records=[self.census_target]
        if bindings_path.exists():
            doc=json.loads(bindings_path.read_text(encoding="utf-8"))
            for entry in doc.get("bindings",[]):
                for target in entry.get("targets",[]):
                    if isinstance(target,dict):
                        records.append({
                            "targetId":target.get("targetId"),
                            "surface":(entry.get("selector") or {}).get("surfaceId"),
                            "recordKind":"EXACT_APPLICATION_TARGET",
                            "enforcement":"GVAE_ENFORCED",
                        })
        return {"records":records}

    def _snapshot(self):
        from canonical_registration.current_truth import capture_current_truth
        return capture_current_truth(
            self.root,
            evidence_target_id="TGT.CENSUS.TABLET.TEST.V1",
            authority_mesh_digest="d"*64,
            layer_map_digest="e"*64,
        )

    def request(self):
        exact_binding={
            "bindingId":"BND.test.table",
            "selector":{"surfaceId":"tablet","neutralMeaningId":"ACT.primary"},
            "status":"RESOLVED",
            "targets":[{
                "targetId":None,
                "ownerId":"owner","routeId":"route","regionId":"region","slotId":"slot",
                "componentUiId":"component","layerId":"LYR.test","implementationLayerId":"physical.layer","ownerCssId":"css",
                "selector":".table",
                "missingBindings":[],
            }],
        }
        return {
            "schema":"prisma.visual.canonical-promotion-request.v1",
            "requestId":"cpr-test-001",
            "target":{"targetId":None,"censusTargetId":"TGT.CENSUS.TABLET.TEST.V1","surfaceKey":"tablet"},
            "expectedCurrentHead":"a"*40,
            "currentTruth":self.current_truth,
            "source":{"digest":self.source_digest,"candidateRef":"candidate.test","path":"candidate.json"},
            "decision":{
                "semanticAction":"REUSE_EXISTING",
                "semanticAuthority":{
                    "authorityDomain":"ndc","writerKind":"NDC_CURATION",
                    "canonicalMeaningId":"ACT.primary","decisionRef":"ndc::decision.test",
                },
                "targetAction":{"action":"CREATE_NEW","existingCanonicalTargetIds":[]},
                "recipeAction":{"action":"REUSE_EXISTING","recipeId":"REC.test.table","semanticKey":"ACT.primary"},
                "bindingAction":{"action":"CREATE_NEW","bindingId":"BND.test.table","semanticKey":"tablet.table",
                                  "exactBinding":exact_binding,"registryEntry":exact_binding},
                "layerAction":{"applicationLayerId":"LYR.APP.TEST","policy":"EXACT_TARGET_ONLY","writerKind":"CANONICAL_REGISTRATION","authorityDomain":"rifat","decisionRef":"rifat::layer-policy.test"},
                "projectionAction":{"mode":"DEFERRED_DERIVATION","authorized":False},
                "idInputs":{},
            },
            "authorization":{
                "canonicalRegistrationAuthorized":True,
                "automaticSemanticInference":False,
                "automaticApplicationSource":False,
            },
        }

    def test_requires_authorization(self):
        request=self.request()
        request["authorization"]["canonicalRegistrationAuthorized"]=False
        with self.assertRaises(self.engine.CanonicalRegistrationError):
            self.engine.build_plan(request,self.root)


    def test_invalid_request_id_is_rejected_before_path_use(self):
        request=self.request()
        request["requestId"]="../escape"
        with self.assertRaises(self.engine.UnsafeMutationError):
            self.engine.register(request,self.root)

    def test_request_id_cannot_be_reused_for_different_payload(self):
        request=self.request()
        self.engine.register(request,self.root)
        changed=self.request()
        changed["requestId"]=request["requestId"]
        changed["source"]["digest"]="c"*64
        with self.assertRaises(self.engine.UnsafeMutationError):
            self.engine.register(changed,self.root)

    def test_new_semantic_requires_adjudication(self):
        request=self.request()
        request["decision"]["semanticAction"]="CREATE_NEW"
        with self.assertRaises(self.engine.CanonicalRegistrationError):
            self.engine.build_plan(request,self.root)

    def test_inferred_id_is_rejected(self):
        request=self.request()
        request["decision"]["idInputs"]={"selector":".stockCell"}
        with self.assertRaises(Exception):
            self.engine.build_plan(request,self.root)

    def test_target_id_is_deterministic(self):
        from canonical_registration.policy import allocate_id
        one=allocate_id("target","tablet|TGT.CENSUS.TABLET.TEST.V1|ACT.primary",set())
        two=allocate_id("target","tablet|TGT.CENSUS.TABLET.TEST.V1|ACT.primary",set())
        self.assertEqual(one.id,two.id)
        self.assertTrue(one.id.startswith("TGT."))

    def test_plan_persists_allocated_target_id(self):
        plan=self.engine.build_plan(self.request(),self.root)
        self.assertIsNotNone(plan["targetId"])
        self.assertEqual(plan["ids"]["targetId"],plan["targetId"])

    def test_existing_target_id_cannot_be_reused_as_create(self):
        request=self.request()
        from canonical_registration.policy import allocate_id
        request["decision"]["targetAction"]["existingCanonicalTargetIds"]=[allocate_id("target","tablet|TGT.CENSUS.TABLET.TEST.V1|ACT.primary",set()).id]
        with self.assertRaises(self.engine.IdCollisionError):
            self.engine.build_plan(request,self.root)


    def test_reuse_existing_target_requires_registered_target(self):
        request=self.request()
        request["decision"]["targetAction"]={"action":"REUSE_EXISTING"}
        request["target"]["targetId"]="TGT.MISSING"
        with self.assertRaises(self.engine.CanonicalRegistrationError):
            self.engine.build_plan(request,self.root)

    def test_reuse_existing_binding_requires_exact_match(self):
        request=self.request()
        first=self.engine.register(request,self.root)
        replay=self.request()
        replay["target"]["targetId"]=first["targetId"]
        replay["decision"]["targetAction"]={"action":"REUSE_EXISTING"}
        replay["decision"]["bindingAction"]["action"]="REUSE_EXISTING"
        replay["decision"]["bindingAction"]["bindingId"]=first["ids"]["bindingId"]
        replay["decision"]["bindingAction"].pop("registryEntry",None)
        plan=self.engine.build_plan(replay,self.root)
        self.assertEqual(plan["bindingAction"],"REUSE_EXISTING")
        self.assertEqual(plan["targetId"],first["targetId"])

    def test_reuse_existing_binding_rejects_mismatched_exact_target(self):
        request=self.request()
        first=self.engine.register(request,self.root)
        replay=self.request()
        replay["target"]["targetId"]=first["targetId"]
        replay["decision"]["targetAction"]={"action":"REUSE_EXISTING"}
        replay["decision"]["bindingAction"]["action"]="REUSE_EXISTING"
        replay["decision"]["bindingAction"]["bindingId"]=first["ids"]["bindingId"]
        replay["decision"]["bindingAction"]["exactBinding"]["targets"][0]["selector"]=".different"
        with self.assertRaises(self.engine.BindingCollisionError):
            self.engine.build_plan(replay,self.root)

    def test_source_drift_is_rejected(self):
        request=self.request()
        (self.root/"candidate.json").write_text('{"candidate":false}',encoding="utf-8")
        with self.assertRaises(self.engine.SourceDriftError):
            self.engine.build_plan(request,self.root)

    def test_idempotent_repeat(self):
        request=self.request()
        first=self.engine.register(request,self.root)
        second=self.engine.register(request,self.root)
        self.assertEqual(first["status"],"APPLIED")
        self.assertEqual(first["ids"]["targetId"],second["ids"]["targetId"])
        self.assertEqual(second["status"],"APPLIED")

    def test_ci_sha_is_authoritative_with_local_git_fallback(self):
        subprocess.run(["git","init"],cwd=self.root,check=True,capture_output=True)
        subprocess.run(["git","config","user.email","test@example.com"],cwd=self.root,check=True,capture_output=True)
        subprocess.run(["git","config","user.name","Test"],cwd=self.root,check=True,capture_output=True)
        marker=self.root/"head-marker.txt"
        marker.write_text("head",encoding="utf-8")
        subprocess.run(["git","add","head-marker.txt"],cwd=self.root,check=True,capture_output=True)
        subprocess.run(["git","commit","-m","fixture"],cwd=self.root,check=True,capture_output=True)
        actual=subprocess.run(["git","rev-parse","HEAD"],cwd=self.root,check=True,capture_output=True,text=True).stdout.strip()
        os.environ["GITHUB_SHA"]="b"*40
        self.assertEqual(self.engine.current_repo_head(self.root),"b"*40)
        del os.environ["GITHUB_SHA"]
        self.assertEqual(self.engine.current_repo_head(self.root),actual)

    def test_stale_head_blocks_replay(self):
        request=self.request()
        self.engine.register(request,self.root)
        os.environ["GITHUB_SHA"]="b"*40
        with self.assertRaises(self.engine.StaleHeadError):
            self.engine.register(request,self.root)

    def test_idempotent_replay_refuses_poststate_drift(self):
        request=self.request()
        self.engine.register(request,self.root)
        p=self.root/"prisma-html/authority/rifat/identity/registries/element-bindings.registry.json"
        doc=json.loads(p.read_text())
        doc["externalDrift"]=True
        p.write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaises(self.engine.UnsafeMutationError):
            self.engine.register(request,self.root)

    def test_register_and_rollback_share_transaction_lock_path(self):
        request_id="lock-contract"
        self.assertEqual(
            self.engine._transaction_lock_path(self.root,request_id),
            self.root/"prisma-html/governance/visual-promotion/canonical-registration/transactions"/f".{request_id}.lock",
        )

    def test_rollback_is_transaction_scoped(self):
        request=self.request()
        self.engine.register(request,self.root)
        rolled=self.engine.rollback(request["requestId"],self.root)
        self.assertEqual(rolled["status"],"ROLLED_BACK")
        bindings=json.loads((self.root/"prisma-html/authority/rifat/identity/registries/element-bindings.registry.json").read_text())
        self.assertEqual(bindings["bindings"],[])
        receipt=json.loads((self.root/"prisma-html/governance/visual-promotion/canonical-registration/receipts"/f"{request['requestId']}.json").read_text())
        journal=json.loads((self.root/receipt["journalPath"]).read_text())
        self.assertEqual(journal["status"],"ROLLED_BACK")

    def test_rollback_refuses_newer_work(self):
        request=self.request()
        self.engine.register(request,self.root)
        p=self.root/"prisma-html/authority/rifat/identity/registries/element-bindings.registry.json"
        doc=json.loads(p.read_text())
        doc["newerWork"]=True
        p.write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaises(self.engine.UnsafeMutationError):
            self.engine.rollback(request["requestId"],self.root)


    def test_rollback_receipt_cannot_escape_canonical_paths(self):
        request=self.request()
        self.engine.register(request,self.root)
        receipt_path=self.root/"prisma-html/governance/visual-promotion/canonical-registration/receipts"/f"{request['requestId']}.json"
        evidence=json.loads(receipt_path.read_text())
        outside="candidate.json"
        evidence["postState"]=[{"path":outside,"sha256":"0"*64}]
        receipt_path.write_text(json.dumps(evidence),encoding="utf-8")
        with self.assertRaises(self.engine.UnsafeMutationError):
            self.engine.rollback(request["requestId"],self.root)

    def test_postcondition_keeps_target_index_pending_until_persisted(self):
        request=self.request()
        plan=self.engine.build_plan(request,self.root)
        from canonical_registration.postconditions import verify_registration_postconditions
        self.engine._apply(self.root,plan["mutations"][0])
        post=verify_registration_postconditions(self.root,plan)
        self.assertEqual(post["targetIndex"],"DERIVATION_PENDING_TARGET_INDEX")

        target_index=self.root/"prisma-html/authority/rifat/prisma-ui/visual-control/target-index/manifest.json"
        target_index.write_text(json.dumps({
            "records":[{
                "targetId":plan["targetId"],
                "recordKind":"EXACT_APPLICATION_TARGET",
                "enforcement":"GVAE_ENFORCED"
            }]
        }),encoding="utf-8")
        post=verify_registration_postconditions(self.root,plan)
        self.assertEqual(post["targetIndex"],"VERIFIED_EXACT_TARGET")

    def test_partial_failure_rolls_back(self):
        request=self.request()
        original=self.engine._apply
        calls={"n":0}
        def failing_apply(root, mutation):
            calls["n"]+=1
            if calls["n"]==2:
                raise RuntimeError("fixture-partial-failure")
            return original(root, mutation)
        self.engine._apply=failing_apply
        request["decision"]["recipeAction"]={
            "action":"CREATE_NEW",
            "semanticKey":"new.recipe",
            "registryEntry":{
                "recipeId":"REC.placeholder",
                "familyId":"FAM.test","presetId":"PRESET.test","identityProfileId":"profile.test",
                "path":"recipes/REC.new.recipe.json","fileSha256":self.new_recipe_sha,
            },
        }
        with self.assertRaises(RuntimeError):
            self.engine.register(request,self.root)
        bindings=json.loads((self.root/"prisma-html/authority/rifat/identity/registries/element-bindings.registry.json").read_text())
        self.assertEqual(bindings["bindings"],[])
        self.engine._apply=original

if __name__=="__main__":
    unittest.main()
