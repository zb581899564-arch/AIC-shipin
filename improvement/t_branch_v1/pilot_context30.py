"""Pinned paths and original four-control adoption shared by the97-window chain."""
from pathlib import Path
import sys
from t_io import ROOT, WORK, check, identity, read, save
OUT = ROOT / 'pilot_control30'
CODE = Path(__file__).parent
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_original_TIME_whole97_remaining93_20261022_v30'
sys.path.insert(0, str(WORK / 'general_highlight_supervision_20261021_v1/code'))
from baseline_bridge57_common import legacy_runtime

def original_outputs():
    original = read(ROOT / 'pilot_cost25/gpu_completion.json')
    if original['first_calls'] != 4:
        raise ValueError('Original four successful controls differ')
    return {read(check(ref))['case']: ref for ref in original['outputs']}

