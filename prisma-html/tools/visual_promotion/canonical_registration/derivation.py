from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from .engine import CanonicalRegistrationError

def plan_derivation(repo_root: Path, target_id: str) -> dict[str, Any]:
    return {
        "schema": "prisma.visual.canonical-promotion-derivation-plan.v1",
        "targetId": target_id,
        "steps": [
            {
                "id": "IDENTITY_COMPILE",
                "command": [sys.executable, "prisma-html/tools/compile_identity_dictionary.py", "--write"],
                "authority": "identity",
                "mutation": "DERIVED_ONLY",
            },
            {
                "id": "TARGET_INDEX_REGENERATE",
                "command": [sys.executable, "-m", "visual_application.target_index", "--write"],
                "authority": "target-index",
                "mutation": "DERIVED_ONLY",
            },
        ],
        "verification": [
            [sys.executable, "prisma-html/tools/compile_identity_dictionary.py", "--check"],
            [sys.executable, "-m", "visual_application.target_index", "--check"],
            [sys.executable, "prisma-html/tools/validate_rifat_authority.py"],
        ],
        "runtimeMutationAuthorized": False,
        "wildcardMutation": False,
    }

def verify_derivation(repo_root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    results = []
    for command in plan["verification"]:
        proc = subprocess.run(
            command,
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        results.append({
            "command": command,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        })
        if proc.returncode != 0:
            raise CanonicalRegistrationError(f"DERIVATION_VERIFY_FAILED:{command}")
    return {
        "schema": "prisma.visual.canonical-promotion-derivation-verification.v1",
        "status": "VERIFIED",
        "targetId": plan["targetId"],
        "results": results,
    }
