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
    blockers, _ = module.check_external_gates(["prisma-html/a.py"], rows)
    assert "REQUIRED_CHECK_NOT_GREEN:guardrails:failure" in blockers
    assert not any("visual authority" in x for x in blockers)

def test_required_gate_declares_trusted_execution_contract():
    source = TARGET.read_text(encoding="utf-8")
    assert '"sourceExecutionFromPR":False' in source
    assert '"adminMergeAllowed":False' in source
    assert "HEAD_MOVED_DURING_GATE" in source
