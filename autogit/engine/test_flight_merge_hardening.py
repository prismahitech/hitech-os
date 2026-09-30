from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLIGHT = ROOT / "autogit/engine/autogit_engine/flight_cli.py"
DASHBOARD = ROOT / "autogit/engine/autogit_engine/ag98_dashboard.py"

def test_no_no_check_merge_flag_in_flight_cli():
    text = FLIGHT.read_text(encoding="utf-8")
    assert "--allow-merge-no-checks" not in text
    assert "def require_canonical_merge_check" in text
    assert "def read_pr_head" in text
    assert "--match-head-commit" in text

def test_dashboard_does_not_authorize_no_check_merge():
    text = DASHBOARD.read_text(encoding="utf-8")
    assert "decision["merge_allowed"] = False" in text
