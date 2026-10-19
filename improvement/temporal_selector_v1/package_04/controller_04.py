"""Explicit remaining-only chain with exact final parameter inventory."""
import datetime as dt
from pathlib import Path
import subprocess
import sys
import time
import traceback
parent=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(parent/'code' if (parent/'code').is_dir() else parent))
from common import *
from controller import run,gpu


def main():
    recovery=ROOT/'recovery_03';current=ROOT/'package_04'
    reg=read(current/'registration.json')
    for name,digest in reg['code'].items():
        require(sha(current/name)==digest,'Frozen remaining-chain code differs')
    write(current/'started.json',dict(pid=os.getpid(),utc=utc(),explicit_remaining_only=True))
    handoff=read(ROOT/'controlled_parent_handoff_04.json');old=handoff['original_parent'];active=handoff['current_stage']
    require(active['stage']=='gpu_remaining_external','Handoff04 only adopts this exact active registered phase')
    child=Path('/proc',str(active['pid']))
    while child.exists():
        raw=(child/'stat').read_text();tail=raw[raw.rfind(')')+2:].split()
        require(tail[19]==active['start_ticks'],'Inherited shared wrapper PID identity differs')
        if tail[0]=='Z':
            require(int(tail[-1])==0,'Inherited shared GPU wrapper actually failed')
            break
        require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(read(ROOT/'protocol.json')['deadline_utc']),
                'Registered20h window ended')
        time.sleep(3)
    resource=gpu_terminal('temporal_selector_remaining_external_20261018_v1')
    require((ROOT/'remaining_external_feature_completion.json').exists(),'Inherited successful GPU outputs missing')
    retirement="""from pathlib import Path
import os,signal,json
r=Path('/home/inspur/aic_video_work/temporal_selector_20261018_v1')
h=json.loads((r/'controlled_parent_handoff_04.json').read_text());old=h['original_parent'];p=Path('/proc',str(old['pid']))
assert p.exists()
raw=(p/'stat').read_text();tail=raw[raw.rfind(')')+2:].split()
assert tail[0]=='T' and tail[19]==old['start_ticks']
assert [x.decode() for x in (p/'cmdline').read_bytes().split(b'\\0') if x]==old['command']
fd=os.pidfd_open(old['pid']);signal.pidfd_send_signal(fd,signal.SIGKILL);os.close(fd)
"""
    subprocess.run(['python3','-c',retirement],check=True)
    write(current/'retired_waiting_parent.json',dict(status='EXACT_OWNED_WAITING_PARENT_RETIRED_AFTER_WRAPPER_NATURAL_EXIT0',
          inherited_wrapper=active,original_parent=old,old_CONTROL5_touched=False,successful_GPU_repeated=False,utc=utc()))
    # Prior controller had not yet recorded/QA'd this successful GPU phase.
    write(ROOT/'remaining_external_resource_acceptance.json',resource)
    run('output_QA_remaining_external',[PYTHON,'-B',ROOT/'code/features.py','qa','external','remaining_external'])
    run('external_membership_QA_02',[PYTHON,'-B',recovery/'audit_02.py','phase','external','--phase','remaining_external'])
    run('assemble_external',[PYTHON,'-B',recovery/'train_v2.py','assemble','--scope','external'])
    run('train_two_heads',[PYTHON,'-B','-u',recovery/'train_v2.py','train'])
    run('prepare_production',[PYTHON,'-B','-u',ROOT/'code/data.py','production'])
    run('production_adoption_QA_02',[PYTHON,'-B',recovery/'audit_02.py','adoption','production'])
    production=read(ROOT/'acceptance_production.json');budget=read(ROOT/'measured_scale_decision.json')
    require(production['window_count']==budget['production_windows'],'Production count differs from measured registration')
    gpu('production','production',21600,production['window_count']*32*8192*4+8_000_000)
    run('production_membership_QA_02',[PYTHON,'-B',recovery/'audit_02.py','phase','production','--phase','production'])
    run('assemble_production',[PYTHON,'-B',recovery/'train_v2.py','assemble','--scope','production'])
    run('apply_two_heads',[PYTHON,'-B',recovery/'train_v2.py','apply'])
    selected=read(ROOT/'selection_completion.json')
    for arm in selected['arms']:
        source=read(checked(arm))
        count=sum(s['selected_frames'] for s in source['sources']);total=sum(s['native_frames'] for s in source['sources'])
        require(0<count<total,'STOP_COMPLETE_EMPTY_OR_COMPLETE_ALL_FRAME_COLLAPSE_NO_PACKAGE')
    run('package_two_candidates_04',[PYTHON,'-B','-u',current/'package_v4.py'])
    completion=read(ROOT/'completion.json')
    replace_state(dict(status=completion['status'],delivered_remote=len(completion['deliveries']),utc=utc()))
    write(ROOT/'chain_completion.json',dict(status='NATURAL_COMPLETE_ALL_REGISTERED_STAGES_WITH_EXPLICIT_FINAL_PARAMETER_FIX',
          completion=reference(ROOT/'completion.json'),final_entry=reference(current/'registration.json'),
          utc=utc(),goal_created=False,automation_created=False))


if __name__=='__main__':
    try:main()
    except BaseException as error:
        failure=ROOT/'package_04/failure.json'
        if not failure.exists():write(failure,dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()))
        replace_state(dict(status='FAILED_FINAL_CHAIN_PRESERVE_ALL_SUCCESS',error=repr(error),utc=utc()))
        raise
