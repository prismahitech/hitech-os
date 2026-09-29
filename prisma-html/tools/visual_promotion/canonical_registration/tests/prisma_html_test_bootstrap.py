from __future__ import annotations
import importlib.util, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def import_engine():
    pkg=ROOT/"canonical_registration"
    ps=importlib.util.spec_from_file_location("policy",pkg/"policy.py"); policy=importlib.util.module_from_spec(ps); sys.modules["policy"]=policy; ps.loader.exec_module(policy)
    spec=importlib.util.spec_from_file_location("canonical_registration.engine",pkg/"engine.py",submodule_search_locations=[str(pkg)])
    module=importlib.util.module_from_spec(spec); module.__package__="canonical_registration"; sys.modules["canonical_registration"]=module; sys.modules["canonical_registration.policy"]=policy; spec.loader.exec_module(module)
    ts=importlib.util.spec_from_file_location("current_truth",pkg/"current_truth.py")
    truth=importlib.util.module_from_spec(ts); truth.__package__="canonical_registration"; sys.modules["current_truth"]=truth; sys.modules["canonical_registration.current_truth"]=truth; ts.loader.exec_module(truth)
    return module
