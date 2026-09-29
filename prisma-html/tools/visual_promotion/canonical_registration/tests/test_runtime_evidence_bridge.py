from __future__ import annotations
import unittest
from prisma_html_test_bootstrap import load_runtime_bridge

class RuntimeEvidenceBridgeTests(unittest.TestCase):
    def setUp(self):
        self.v=load_runtime_bridge()
    def evidence(self):
        return {
            "schema":"prisma.visual.runtime-evidence.v1",
            "target":{"targetId":"TGT.TEST","censusTargetId":"TGT.CENSUS.TABLET.TEST.V1","route":"/inventory"},
            "viewport":{"width":1280,"height":800,"dpr":1},
            "browser":{"name":"chromium","version":"test","device":"desktop"},
            "build":{"commitSha":"a"*40},
            "before":{"path":"before.png","sha256":"b"*64},
            "after":{"path":"after.png","sha256":"c"*64},
            "sourceProjection":{"commitSha":"a"*40,"digest":"d"*64},
            "runtimeState":"PASS","consoleState":"PASS","networkState":"PASS",
            "geometryVerdict":"PASS","accessibilityVerdict":"PASS","visualVerdict":"PASS",
            "gvaeVerifyState":"PASS","capturedAt":"2026-09-29T00:00:00Z",
        }
    def test_visual_certified_requires_all_runtime_dimensions(self):
        r=self.v.validate_runtime_evidence(self.evidence())
        self.assertEqual(r.certification_state,"VISUAL_CERTIFIED")
        self.assertTrue(r.change_assurance_ready)
    def test_gvae_alone_cannot_certify(self):
        e=self.evidence()
        e["runtimeState"]="NOT_RUN"; e["consoleState"]="NOT_RUN"; e["networkState"]="NOT_RUN"
        e["geometryVerdict"]="NOT_RUN"; e["accessibilityVerdict"]="NOT_RUN"; e["visualVerdict"]="NOT_RUN"
        r=self.v.validate_runtime_evidence(e)
        self.assertEqual(r.certification_state,"PENDING_RUNTIME_CERTIFICATION")
        self.assertFalse(r.change_assurance_ready)
    def test_source_projection_must_match_build(self):
        e=self.evidence(); e["sourceProjection"]["commitSha"]="c"*40
        with self.assertRaises(self.v.RuntimeEvidenceError):
            self.v.validate_runtime_evidence(e)
    def test_handoff_requires_certification(self):
        e=self.evidence(); e["visualVerdict"]="FAIL"
        r=self.v.validate_runtime_evidence(e)
        with self.assertRaises(self.v.RuntimeEvidenceError):
            self.v.build_change_assurance_handoff(e,r)

if __name__=="__main__":
    unittest.main()
