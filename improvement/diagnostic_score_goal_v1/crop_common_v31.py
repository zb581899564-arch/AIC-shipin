"""Explicit31 shared bindings; no implicit latest-version discovery."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import WORK,RUN,read,save,sha,ref,bound,require,utc,signature,append_event,paths


def registration(root):
    root=Path(root);reg=read(root/'crop_CPU_registration_31.json')
    require(reg['schema']=='CROP_TRIPLET_CPU_V31','Explicit crop31 registration')
    require(bound(reg['common_code'])==Path(__file__).resolve(),'Exact crop31 common helper')
    for key in ('preparation_code','geometry_code','input_code','CPU_controller'):bound(reg[key])
    old=read(bound(reg['old_pair_registration']))
    for name,digest in old['new_code'].items():require(sha(root/'pair_code_17'/name)==digest,'Frozen original17 helper '+name)
    require(reg['new_original_decode']==0 and reg['old_source_processor_repeated']==0,'Adopt existing original media work')
    return reg
