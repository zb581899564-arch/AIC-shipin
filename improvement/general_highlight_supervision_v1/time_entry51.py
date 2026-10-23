"""Explicit remaining root and original dependency paths; no scientific recipe changes."""
from pathlib import Path
import runpy
import sys
from common import ROOT as ADMISSION,WORK


def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ['prepare','gpu','review']:
        raise ValueError('Only one explicit remaining stage accepted')
    run=WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
    for path in [run/'baseline_a_pts_v1',run/'temporal_sft8b_v1']:
        sys.path.insert(0,str(path))
    import time_control50_common as context
    context.ROOT=ADMISSION/'time_control51'
    target=Path(__file__).parent/('time_control50_'+sys.argv[1]+'.py')
    runpy.run_path(str(target),run_name='__main__')


if __name__=='__main__':main()
