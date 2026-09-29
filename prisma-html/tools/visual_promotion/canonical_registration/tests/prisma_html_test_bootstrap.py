from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def _load(name:str,path:Path,package:str|None=None):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    if package is not None: module.__package__=package
    sys.modules[name]=module
    assert spec.loader
    spec.loader.exec_module(module)
    return module

def import_engine():
    pkg=ROOT/"canonical_registration"
    package=types.ModuleType("canonical_registration")
    package.__path__=[str(pkg)]
    sys.modules["canonical_registration"]=package
    _load("canonical_registration.policy",pkg/"policy.py","canonical_registration")
    _load("canonical_registration.authority_adapters",pkg/"authority_adapters.py","canonical_registration")
    truth=_load("canonical_registration.current_truth",pkg/"current_truth.py","canonical_registration")
    sys.modules["current_truth"]=truth
    _load("canonical_registration.postconditions",pkg/"postconditions.py","canonical_registration")
    return _load("canonical_registration.engine",pkg/"engine.py","canonical_registration")
