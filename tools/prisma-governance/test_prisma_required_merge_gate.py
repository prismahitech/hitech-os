import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "tools/prisma-governance/prisma_required_merge_gate.py"
spec = importlib.util.spec_from_file_location("required_merge_gate", TARGET)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

def test_control_plane_detection():
    assert module.is_control_plane(".github/workflows/forgeos-quality-gate.yml")
    assert module.is_control_plane("tools/code-atlas/src/code_atlas/motors/prisma_mesh_gateway.py")
    assert not module.is_control_plane("README.md")

def test_required_checks_mapping():
    names = [x[0] for x in module.required_checks(["prisma-html/a.py", "pnpm-lock.yaml", "forgeos/a.py"])]
    assert names == ["guardrails", "visual authority / readiness gates", "Sentinel ", "forgeos-source-quality"]

def test_check_resolution_requires_completed_success():
    rows = [{"name":"guardrails","status":"completed","conclusion":"failure"},
            {"name":"visual authority / readiness gates","status":"completed","conclusion":"success"}]
    guardrail = module.resolve_check(rows, "guardrails", "exact")
    visual = module.resolve_check(rows, "visual authority / readiness gates", "exact")
    assert guardrail["conclusion"] == "failure"
    assert visual["conclusion"] == "success"

def test_required_gate_declares_trusted_execution_contract():
    source = TARGET.read_text(encoding="utf-8")
    assert '"sourceExecutionFromPR":False' in source
    assert '"adminMergeAllowed":False' in source
    assert "HEAD_MOVED_DURING_GATE" in source

def test_branch_protection_must_cover_admins_and_canonical_context():
    payload = {"protection": {"enabled": True, "required_status_checks": {"enforcement_level": "non_admins", "contexts": ["forgeos-quality-gate"]}}}
    assert module.branch_protection_errors(payload) == ["MAIN_REQUIRED_CHECKS_NOT_ENFORCED_FOR_ADMINS"]

def test_branch_protection_requires_canonical_context():
    payload = {"protection": {"enabled": True, "required_status_checks": {"enforcement_level": "everyone", "contexts": ["other"]}}}
    assert module.branch_protection_errors(payload) == ["MAIN_CANONICAL_GATE_CONTEXT_MISSING"]
