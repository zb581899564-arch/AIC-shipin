"""Adopt saved BCE checkpoint after failed reporting; train SET once."""
import datetime as dt
from pathlib import Path
import sys
import traceback
parent=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(parent/'code' if (parent/'code').is_dir() else parent))
from common import *
from controller import run,gpu


def main():
    here=ROOT/'recovery_05';reg=read(here/'registration.json')
    for name,digest in reg['code'].items():require(sha(here/name)==digest,'Remaining recovery code changed')
    require(sha(ROOT/'training/BCE.pt')==reg['adopted_BCE_sha256'],'Saved BCE checkpoint identity changed')
    require(not (ROOT/'training_completion.json').exists() and not (ROOT/'inputs_production').exists(),
            'This recovery only resumes the registered pre-production report failure')
    write(here/'started.json',dict(pid=os.getpid(),utc=utc(),prior_BCE_updates_repeated=0,old_feature_calls_repeated=0))
    run('train_head_remaining_report_05',[PYTHON,'-B','-u',here/'train_resume_v3.py','train'])
    run('prepare_production',[PYTHON,'-B','-u',ROOT/'code/data.py','production'])
    run('production_adoption_QA_02',[PYTHON,'-B',ROOT/'recovery_03/audit_02.py','adoption','production'])
    production=read(ROOT/'acceptance_production.json');budget=read(ROOT/'measured_scale_decision.json')
    require(production['window_count']==budget['production_windows'],'Production count differs from registered measured scale')
    gpu('production','production',21600,production['window_count']*32*8192*4+8_000_000)
    run('production_membership_QA_02',[PYTHON,'-B',ROOT/'recovery_03/audit_02.py','phase','production','--phase','production'])
    run('assemble_production',[PYTHON,'-B',here/'train_resume_v3.py','assemble','--scope','production'])
    run('apply_two_heads',[PYTHON,'-B',here/'train_resume_v3.py','apply'])
    selected=read(ROOT/'selection_completion.json')
    for arm in selected['arms']:
        result=read(checked(arm));count=sum(s['selected_frames'] for s in result['sources']);total=sum(s['native_frames'] for s in result['sources'])
        require(0<count<total,'STOP_COMPLETE_EMPTY_OR_ALL_FRAME_OUTPUT_COLLAPSE')
    run('package_two_candidates_04',[PYTHON,'-B','-u',ROOT/'package_04/package_v4.py'])
    completion=read(ROOT/'completion.json')
    replace_state(dict(status=completion['status'],delivered_remote=len(completion['deliveries']),utc=utc()))
    write(ROOT/'chain_completion.json',dict(status='NATURAL_COMPLETE_ALL_REGISTERED_STAGES_WITH_SAVED_BCE_ADOPTION',
          completion=reference(ROOT/'completion.json'),recovery=reference(here/'registration.json'),
          utc=utc(),goal_created=False,automation_created=False))


if __name__=='__main__':
    try:main()
    except BaseException as error:
        failure=ROOT/'recovery_05/failure.json'
        if not failure.exists():write(failure,dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()))
        replace_state(dict(status='FAILED_REMAINING_ONLY05_PRESERVE_SUCCESS',error=repr(error),utc=utc()))
        raise
