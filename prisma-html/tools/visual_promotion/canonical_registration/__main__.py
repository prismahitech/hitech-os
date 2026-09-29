from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .current_truth import capture_current_truth
from .engine import build_plan, register, rollback, CanonicalRegistrationError
from .derivation import plan_derivation

def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    parser=argparse.ArgumentParser(description="Governed PRISMA visual canonical registration.")
    parser.add_argument("--repo-root",type=Path,default=Path.cwd())
    sub=parser.add_subparsers(dest="command",required=True)

    snapshot=sub.add_parser("snapshot")
    snapshot.add_argument("--evidence-target-id",required=True)
    snapshot.add_argument("--authority-mesh-path")
    snapshot.add_argument("--layer-map-path")
    snapshot.add_argument("--authority-mesh-digest")
    snapshot.add_argument("--layer-map-digest")

    plan=sub.add_parser("plan")
    plan.add_argument("--request",type=Path,required=True)

    apply_cmd=sub.add_parser("register")
    apply_cmd.add_argument("--request",type=Path,required=True)

    rb=sub.add_parser("rollback")
    rb.add_argument("--request-id",required=True)

    der=sub.add_parser("derivation-plan")
    der.add_argument("--target-id",required=True)

    args=parser.parse_args()
    root=args.repo_root.resolve()
    tools_root=root/"prisma-html/tools" if (root/"prisma-html/tools").is_dir() else root/"tools"
    if tools_root.is_dir() and str(tools_root) not in sys.path:
        sys.path.insert(0,str(tools_root))
    try:
        if args.command=="snapshot":
            out=capture_current_truth(root,evidence_target_id=args.evidence_target_id,
                authority_mesh_path=args.authority_mesh_path,layer_map_path=args.layer_map_path,
                authority_mesh_digest=args.authority_mesh_digest,layer_map_digest=args.layer_map_digest)
        elif args.command=="plan":
            out=build_plan(_load(args.request),root)
        elif args.command=="register":
            out=register(_load(args.request),root)
        elif args.command=="rollback":
            out=rollback(args.request_id,root)
        else:
            out=plan_derivation(root,args.target_id)
        print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))
        return 0
    except (CanonicalRegistrationError, ValueError, OSError, json.JSONDecodeError) as exc:
        out={
            "schema":"prisma.visual.canonical-registration.cli-result.v1",
            "status":"BLOCKED",
            "errorCode":type(exc).__name__,
            "error":str(exc),
            "mutationAuthorized":False,
        }
        print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
