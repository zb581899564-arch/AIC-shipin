"""Exact pilot paths and identities; original labels never enter model inputs."""
from pathlib import Path
import sys
from common import ROOT as ADMISSION, WORK, read, ref, save

ROOT = ADMISSION / 'qv_pilot47'
ENGINEERING = WORK / 'i3d_umt_cross_domain_20261021_v1'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'author_qv24_late_visual_rank_20261022_v47'
sys.path.insert(0, str(ENGINEERING))
sys.path.insert(0, str(WORK / 'highlight_source_admission_20261021_v1/matched_hl_pilot16/code'))


def checked(record):
    value = ref(record['path'])
    if value['sha256'] != record['sha256'] or ('bytes' in record and value['bytes'] != record['bytes']):
        raise ValueError('Bound input or dependency identity changed: ' + record['path'])
    return Path(record['path'])
