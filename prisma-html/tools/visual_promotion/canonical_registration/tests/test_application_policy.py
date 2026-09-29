from __future__ import annotations
import unittest
from prisma_html_test_bootstrap import load_application_policy

class ApplicationPolicyTests(unittest.TestCase):
    def setUp(self): self.v=load_application_policy()

    def test_valid_policy(self):
        p=self.v.validate_application_policy({"implementationLayerId":"physical.css.x","applicationLayerId":"LYR.APP.X","policy":"EXACT_TARGET_ONLY","writerKind":"CANONICAL_REGISTRATION","authorityDomain":"rifat","decisionRef":"rifat::policy.x"})
        self.assertEqual(p.writer_kind,"CANONICAL_REGISTRATION")

    def test_same_layer_is_rejected(self):
        with self.assertRaises(self.v.ApplicationPolicyError):
            self.v.validate_application_policy({"implementationLayerId":"LYR.APP.X","applicationLayerId":"LYR.APP.X","policy":"EXACT_TARGET_ONLY","writerKind":"CANONICAL_REGISTRATION","authorityDomain":"rifat","decisionRef":"rifat::policy.x"})

    def test_missing_decision_ref_is_rejected(self):
        with self.assertRaises(self.v.ApplicationPolicyError):
            self.v.validate_application_policy({"implementationLayerId":"physical.css.x","applicationLayerId":"LYR.APP.X","policy":"EXACT_TARGET_ONLY","writerKind":"CANONICAL_REGISTRATION","authorityDomain":"rifat","decisionRef":""})

if __name__=="__main__": unittest.main()
