"""Frozen40.47 branch on one new external source; isolated original modules only."""
from pathlib import Path
import importlib.util
import sys
from common import ROOT as ADMISSION,WORK,read,ref,save
from time_control50_common import RUN,PY,WRAPPER,checked

ROOT=ADMISSION/'baseline_bridge57'
DATA=ADMISSION/'time_control53'
SEM=WORK/'semantic_context_production_20261016_v1'
CAMPAIGN=WORK/'twenty_hour_five_20261014_v1'
JOB='sportclip_diving_full_VERIFY_semantic_baseline_20261022_v57'


def legacy_runtime():
    from time_entry53 import original_runtime
    return original_runtime()[0]


def exact_module(name,path):
    path=Path(path).resolve(strict=True)
    if name in sys.modules:
        if Path(sys.modules[name].__file__).resolve()!=path:raise ValueError('Frozen module name collision: '+name)
        return sys.modules[name]
    specification=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(specification);sys.modules[name]=module
    specification.loader.exec_module(module)
    return module


def verify_modules():
    directory=CAMPAIGN/'candidate_verify_v2/code';sys.path.insert(0,str(directory))
    contract=exact_module('cv_contract',directory/'cv_contract.py')
    grammar=exact_module('cv_grammar',directory/'cv_grammar.py')
    protocol=exact_module('_frozen_tp_contract57',CAMPAIGN/'temporal_production_inputs_v4/code/tp_contract.py')
    return contract,grammar,protocol


def semantic_modules():
    directory=SEM/'code';sys.path.insert(0,str(directory))
    exact_module('common_runtime',directory/'common_runtime.py')
    exact_module('semantic09',directory/'semantic09.py')
    production=exact_module('_frozen_semantic_production57',directory/'production_semantic10.py')
    transform=exact_module('semantic_oof09',directory/'semantic_oof09.py')
    head=exact_module('monotone_head06',directory/'monotone_head06.py')
    return production,transform,head
