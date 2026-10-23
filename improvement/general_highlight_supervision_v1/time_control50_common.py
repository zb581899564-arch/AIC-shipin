"""First strong original-TIME control on the externally held diving recording."""
from pathlib import Path
import sys
from common import ROOT as ADMISSION, WORK, read, ref, save

ROOT=ADMISSION/'time_control50'
RUN=WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY=WORK/'env/qwen3vl_isolated_20260910/bin/python'
LEGACY=WORK/'temporal_refinement_pilot_20261011/dev_01'
WRAPPER=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
JOB='sportclip_diving_original_TIME_control_20261022_v50'
SPORT=WORK/'highlight_source_admission_20261021_v1/matched_hl_pilot16'


def checked(identity):
    actual=ref(identity['path'])
    if actual['sha256']!=identity['sha256'] or ('bytes' in identity and actual['bytes']!=identity['bytes']):
        raise ValueError('Bound actual source/cache changed')
    return Path(identity['path'])


def runtime():
    sys.path.insert(0,str(LEGACY))
    import runtime as original
    if Path(original.__file__).resolve()!=LEGACY/'runtime.py':raise ValueError('Wrong original B runtime module')
    return original
