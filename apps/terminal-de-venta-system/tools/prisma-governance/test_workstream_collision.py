from __future__ import annotations

import unittest

from workstream_collision import (
    Declaration,
    GateError,
    PullRequestView,
    declaration_conflict,
    declaration_scope_gaps,
    exclusive_overlap_paths,
    exclusive_scope_overlap,
    is_exclusive_path,
    is_governed_path,
    parse_declaration,
    scope_matches,
)


class TestWorkstreamCollision(unittest.TestCase):
    def test_parse_declaration(self):
        d = parse_declaration(
            """<!-- PRISMA-WORKSTREAM
id: visual-canonical-registration-g01
role: canonical
requested_action: ADVANCE
capabilities: visual.canonical_promotion_integration_v1
surfaces: prisma-html, governance
scope: prisma-html/tools/visual_promotion/canonical_registration/**
owner: engineer
-->"""
        )
        self.assertEqual(d.workstream_id, "visual-canonical-registration-g01")
        self.assertEqual(d.role, "canonical")

    def test_multiple_declarations_rejected(self):
        with self.assertRaises(GateError):
            parse_declaration(
                """<!-- PRISMA-WORKSTREAM
id: alpha
role: proposal
requested_action: VERIFY
capabilities: visual.foo
surfaces: governance
scope: foo/**
-->

<!-- PRISMA-WORKSTREAM
id: beta
role: proposal
requested_action: VERIFY
capabilities: visual.foo
surfaces: governance
scope: bar/**
-->"""
            )

    def test_unsafe_scope_rejected(self):
        with self.assertRaises(GateError):
            parse_declaration(
                """<!-- PRISMA-WORKSTREAM
id: alpha
role: proposal
requested_action: VERIFY
capabilities: visual.foo
surfaces: governance
scope: ../../unsafe
-->"""
            )

    def test_protected_paths(self):
        self.assertTrue(is_governed_path("tools/code-atlas/tests/test_x.py"))
        self.assertTrue(is_exclusive_path("prisma-html/tools/visual_promotion/canonical_registration/engine.py"))
        self.assertFalse(is_governed_path("README.md"))

    def test_same_workstream_conflicts(self):
        a = Declaration("alpha", "canonical", "ADVANCE", ("visual.foo",), ("governance",), ("foo/**",))
        b = Declaration("alpha", "proposal", "ADVANCE", ("visual.foo",), ("governance",), ("foo/**",))
        pa = PullRequestView(1, "A", "", "open", False, "a"*40, "b"*40, "", "", a, ["foo/bar.py"])
        pb = PullRequestView(2, "B", "", "open", False, "c"*40, "b"*40, "", "", b, ["foo/bar.py"])
        hard, reasons, _ = declaration_conflict(pa, pb)
        self.assertTrue(hard)
        self.assertIn("same_workstream_id", reasons)

    def test_undeclared_exclusive_overlap_is_detectable(self):
        d = Declaration("alpha", "canonical", "ADVANCE", ("visual.foo",), ("governance",), ("foo/**",))
        pa = PullRequestView(1, "A", "", "open", False, "a"*40, "b"*40, "", "", d, [
            "prisma-html/tools/visual_promotion/canonical_registration/engine.py",
        ])
        pb = PullRequestView(2, "B", "", "open", False, "", "b"*40, "", "", None, [
            "prisma-html/tools/visual_promotion/canonical_registration/engine.py",
        ])
        self.assertEqual(
            exclusive_overlap_paths(pa, pb),
            ["prisma-html/tools/visual_promotion/canonical_registration/engine.py"],
        )

    def test_declared_scope_covers_governed_paths(self):
        d = Declaration("alpha", "canonical", "ADVANCE", ("visual.foo",), ("governance",), ("foo/**",))
        self.assertEqual(
            declaration_scope_gaps(
                d,
                ["foo/bar.py", "prisma-html/tools/visual_promotion/canonical_registration/engine.py"],
            ),
            ["prisma-html/tools/visual_promotion/canonical_registration/engine.py"],
        )

    def test_exclusive_scope_overlap_blocks_different_files(self):
        d = Declaration("alpha", "canonical", "ADVANCE", ("visual.foo",), ("governance",), (
            "prisma-html/tools/visual_promotion/canonical_registration/**",
        ))
        pa = PullRequestView(1, "A", "", "open", False, "a"*40, "b"*40, "", "", d, [
            "prisma-html/tools/visual_promotion/canonical_registration/engine.py",
        ])
        pb = PullRequestView(2, "B", "", "open", False, "c"*40, "b"*40, "", "", d, [
            "prisma-html/tools/visual_promotion/canonical_registration/policy.py",
        ])
        self.assertEqual(
            exclusive_scope_overlap(pa, pb),
            ["prisma-html/tools/visual_promotion/canonical_registration"],
        )

    def test_scope_match(self):
        self.assertTrue(scope_matches("foo/**", "foo/bar/baz.py"))


if __name__ == "__main__":
    unittest.main()
