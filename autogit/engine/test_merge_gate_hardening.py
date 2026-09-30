from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "autogit/engine/autogit_engine/config.py"
PR_GATE = ROOT / "autogit/engine/autogit_engine/pr_gate.py"
GH = ROOT / "autogit/engine/autogit_engine/github_cli.py"

def test_admin_bypass_removed():
    assert "AUTOGIT_ALLOW_ADMIN_MERGE" not in CONFIG.read_text(encoding="utf-8")
    assert "admin=True" not in PR_GATE.read_text(encoding="utf-8")
    assert "--admin" not in GH.read_text(encoding="utf-8")

def test_exact_head_and_post_merge_proof_present():
    text = PR_GATE.read_text(encoding="utf-8")
    assert "def _require_pr_head" in text
    assert "def _post_merge_proof" in text
    assert "post_merge_proof.json" in text
