"""Explicit remaining-only handoff after reproduced pre-training precision bug."""
import datetime as dt
import os
from pathlib import Path
import signal
import sys
import time
import traceback
parent=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(parent/'code' if (parent/'code').is_dir() else parent))
from common import *
from controller import run,gpu


def main():
    recovery=ROOT/'recovery_02'
    reg=read(recovery/'registration.json')
    for name,digest in reg['code'].items():
        require(sha(recovery/name)==digest,'Frozen recovery code differs')
    write(recovery/'started.json',dict(pid=os.getpid(),utc=utc(),explicit_recovery=True,old_controller_resumed=False))
    handoff=read(ROOT/'controlled_parent_handoff_02.json');old=handoff['original_parent'];active=handoff['current_stage']
    require(active['stage']=='prepare_external','Recovery02 only covers the observed pre-training preparation handoff')
    # Let the already-started preparation naturally finish; never duplicate it.
    child=Path('/proc',str(active['pid']))
    while child.exists():
        raw=(child/'stat').read_text();tail=raw[raw.rfind(')')+2:].split()
        require(tail[19]==active['start_ticks'],'Inherited CPU child PID identity changed')
        if tail[0]=='Z':
            require(int(tail[-1])==0,'Inherited CPU preparation actually failed; no input rerun')
            break
        require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(read(ROOT/'protocol.json')['deadline_utc']),
                '20h window ended while awaiting original CPU child')
        time.sleep(2)
    require((ROOT/'source_lock_external.json').is_file() and (ROOT/'acceptance_external.json').is_file(),
            'Original preparation has no successful terminal acceptance')
    old_proc=Path('/proc',str(old['pid']))
    if old_proc.exists():
        raw=(old_proc/'stat').read_text();tail=raw[raw.rfind(')')+2:].split()
        require(tail[19]==old['start_ticks'] and tail[0]=='T' and
                [x.decode() for x in (old_proc/'cmdline').read_bytes().split(b'\0') if x]==old['command'],
                'Only the specifically stopped owned waiting parent may be retired')
        fd=os.pidfd_open(old['pid']);signal.pidfd_send_signal(fd,signal.SIGKILL);os.close(fd)
    write(recovery/'original_parent_retired.json',dict(status='CONTROLLED_PARENT_ONLY_RETIREMENT_AFTER_CHILD_NATURAL_SUCCESS',
           original_parent=old,successful_preparation=reference(ROOT/'source_lock_external.json'),
           old_CONTROL5_touched=False,no_child_stopped=True,utc=utc()))
    run('threshold_regression_02',[PYTHON,'-B',recovery/'test_threshold_02.py'])
    run('external_adoption_QA_02',[PYTHON,'-B',recovery/'audit_02.py','adoption','external'])
    gpu('pilot32','external',3600,32*32*8192*4+8_000_000)
    run('pilot_membership_QA_02',[PYTHON,'-B',recovery/'audit_02.py','phase','external','--phase','pilot32'])
    pilot=read(ROOT/'pilot32_acceptance.json');acceptance=read(ROOT/'acceptance_external.json')
    from mapping import window_schedule
    old_inputs=read(PRODUCTION/'cpu_acceptance.json')
    production_windows=sum(len(window_schedule(s['feature_cells'])) for s in old_inputs['sources'])
    estimate=(acceptance['window_count']-32+production_windows)*pilot['mean_forward_seconds']*2+4*3600
    remaining=(dt.datetime.fromisoformat(read(ROOT/'protocol.json')['deadline_utc'])-dt.datetime.now(dt.timezone.utc)).total_seconds()
    write(ROOT/'measured_scale_decision.json',dict(pilot=reference(ROOT/'pilot32_acceptance.json'),
         external_windows=acceptance['window_count'],production_windows=production_windows,
         measured_compute_plus_CPU_QA_buffer_seconds=estimate,remaining_registered_seconds=remaining,
         permitted=estimate<remaining,dynamic_capacity_bytes=__import__('shutil').disk_usage(WORK).free,
         extra_feature_estimate_bytes=(acceptance['window_count']+production_windows)*32*8192*4+600_000_000))
    require(estimate<remaining,'Measured scale exceeds the total20h window')
    gpu('remaining_external','external',7200,acceptance['window_count']*32*8192*4+8_000_000)
    run('external_membership_QA_02',[PYTHON,'-B',recovery/'audit_02.py','phase','external','--phase','remaining_external'])
    run('assemble_external',[PYTHON,'-B',recovery/'train_v2.py','assemble','--scope','external'])
    run('train_two_heads',[PYTHON,'-B','-u',recovery/'train_v2.py','train'])
    run('prepare_production',[PYTHON,'-B','-u',ROOT/'code/data.py','production'])
    run('production_adoption_QA_02',[PYTHON,'-B',recovery/'audit_02.py','adoption','production'])
    production=read(ROOT/'acceptance_production.json')
    require(production['window_count']==production_windows,'Production count differs from measured registration')
    gpu('production','production',21600,production_windows*32*8192*4+8_000_000)
    run('production_membership_QA_02',[PYTHON,'-B',recovery/'audit_02.py','phase','production','--phase','production'])
    run('assemble_production',[PYTHON,'-B',recovery/'train_v2.py','assemble','--scope','production'])
    run('apply_two_heads',[PYTHON,'-B',recovery/'train_v2.py','apply'])
    run('package_two_candidates',[PYTHON,'-B','-u',ROOT/'code/package.py'])
    completion=read(ROOT/'completion.json')
    replace_state(dict(status=completion['status'],delivered_remote=len(completion['deliveries']),utc=utc()))
    write(ROOT/'chain_completion.json',dict(status='NATURAL_COMPLETE_ALL_REGISTERED_STAGES_WITH_EXPLICIT_RECOVERY02',
          completion=reference(ROOT/'completion.json'),recovery=reference(recovery/'registration.json'),
          utc=utc(),goal_created=False,automation_created=False))


if __name__=='__main__':
    try:main()
    except BaseException as error:
        failure=ROOT/'recovery_02/failure.json'
        if not failure.exists():write(failure,dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()))
        replace_state(dict(status='FAILED_RECOVERY02_PRESERVE_ALL_SUCCESS',error=repr(error),utc=utc()))
        raise
