from __future__ import annotations
import hashlib
import tempfile
import unittest
from pathlib import Path
from prisma_html_test_bootstrap import load_write_preflight

class WritePreflightTests(unittest.TestCase):
    def setUp(self):
        self.v=load_write_preflight()
        self.root=Path(tempfile.mkdtemp())
        self.src=self.root/"candidate.json"
        self.src.write_text('{"candidate":true}',encoding="utf-8")
        self.sha=hashlib.sha256(self.src.read_bytes()).hexdigest()
    def ctx(self):
        return {
            "expectedCurrentHead":"a"*40,"currentHead":"a"*40,
            "automaticSemanticInference":False,"automaticApplicationSource":False,
            "writerKind":"CANONICAL_REGISTRATION","authorityDomain":"canonical-registration",
            "targetId":"TGT.X","sourcePath":"candidate.json","sourceDigest":self.sha,
            "runtimeMutationAllowed":False,
        }
    def test_valid_preflight_passes(self):
        p=self.v.validate_write_preflight(self.root,self.ctx())
        self.assertTrue(p.mutation_allowed)
    def test_gvae_writer_is_rejected_here(self):
        c=self.ctx();c["writerKind"]="GVAE"
        with self.assertRaises(self.v.WritePreflightError): self.v.validate_write_preflight(self.root,c)
    def test_stale_head_blocks(self):
        c=self.ctx();c["currentHead"]="b"*40
        with self.assertRaises(self.v.WritePreflightError): self.v.validate_write_preflight(self.root,c)
    def test_source_drift_blocks(self):
        c=self.ctx();self.src.write_text('{"candidate":false}',encoding="utf-8")
        with self.assertRaises(self.v.WritePreflightError): self.v.validate_write_preflight(self.root,c)

if __name__=="__main__":
    unittest.main()
