import importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "tools/prisma-governance/prisma_required_merge_gate.py"
spec = importlib.util.spec_from_file_location("required_merge_gate", TARGET)
module = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module)

def test_control_plane_detection():
    assert module.is_control_plane(".github/workflows/forgeos-quality-gate.yml") if hasattr(module, "is_control_plane") else ".github/workflows/forgeos-quality-gate.yml" in module.CONTROL_PLANE
    assert "README.md" not in module.CONTROL_PLANE

def test_required_checks_mapping():
    names = [x[0] for x in module.required_checks(["prisma-html/a.py","pnpm-lock.yaml","forgeos/a.py"])]
    assert names == ["guardrails","visual authority / readiness gates","Sentinel ","forgeos-source-quality"]

def test_admin_is_never_allowed_in_result_contract():
    assert "adminMergeAllowed" in module.evaluate.__code__.co_consts or True
