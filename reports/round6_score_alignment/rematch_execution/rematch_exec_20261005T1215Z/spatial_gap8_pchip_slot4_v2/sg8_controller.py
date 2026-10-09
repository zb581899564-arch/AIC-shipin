"""One autonomous finite route; failed fixed science never triggers another recipe."""
import fcntl
import os
import socket
import subprocess
import traceback
from sg8_common import HERE,RUN,PY,read,sha,save,require,state,utc,verify
from sg8_final import terminal


def cpu(name,args):
    verify(full=False);state('RUNNING_CPU_'+name.upper())
    with (HERE/(name+'.cpu.log')).open('x') as log:
        result=subprocess.run([PY,'-B',*map(str,args)],cwd=HERE,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
    require(result.returncode==0,'CPU stage failed: '+name)


def main():
    require(socket.gethostname()=='inspur-NP5570M5','wrong host')
    lock=(HERE/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(not (HERE/'registration.json').exists(),'already registered; do not restart')
    verify(full=False)
    save(HERE/'registration.json',dict(utc=utc(),pid=os.getpid(),pgid=os.getpgrp(),source_lock_sha256=sha(HERE/'source_lock.json')))
    try:
        admission=read(HERE/'g0_admission.json');state('QUEUED_SHARED_GPU_REAL_SG8_PROBES')
        command=[PY,'-B',str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),'--name','aic_SG8_slot4_v2_diagnostic',
            '--max-seconds',str(admission['operational_job_timeout_seconds']),
            '--planned-output-bytes',str(admission['planned_remaining_output_bytes']),
            '--capacity-reason','Finite 53 missing original 8B single-frame probes plus independent CPU replay and full-field serialization estimated from actual source/frame artifacts; live shared conflicts and physical capacity',
            '--queue-seconds',str(admission['queue_seconds']),'--',PY,'-B',str(HERE/'sg8_engine.py')]
        with (HERE/'diagnostic.wrapper.log').open('x') as log:
            result=subprocess.run(command,cwd=HERE,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        require(result.returncode==0,'actual GPU diagnostic failed; preserve successful raw and STOP')
        resource=terminal();cpu('g2_report',[HERE/'sg8_report.py']);report=read(HERE/'diagnostic_01/report.json')
        if report['status']!='PASS_G2_NUMERIC_ONLY_G3_PENDING':
            save(HERE/'scientific_stop.json',dict(status='NO_426_SG8_FIXED_NUMERIC_GATE',utc=utc(),
                report_sha256=sha(HERE/'diagnostic_01/report.json'),resource=resource,complete_groups=8,complete_phases=56,
                no_final_426_ZIP=True,finite_route_exhausted=True,no_automatic_new_recipe=True))
            state('NO_426_FINITE_SG8_EVIDENCE_COMPLETE',resource=resource);return
        cpu('g3_nontest',[HERE/'sg8_packager.py','nontest']);nt=read(HERE/'nontest_01/package.stage.json')
        if nt['status']=='NO_EFFECT':
            save(HERE/'scientific_stop.json',dict(status='NO_EFFECT_FIXED_NONTEST_SELECTED_INTEGER_BOXES',utc=utc(),
                resource=resource,no_final_426_ZIP=True,finite_route_exhausted=True,no_automatic_new_recipe=True))
            state('NO_EFFECT_FINITE_SG8_EVIDENCE_COMPLETE');return
        cpu('g4_rematch',[HERE/'sg8_packager.py','rematch']);cpu('g5_independent_final',[HERE/'sg8_final.py'])
        final=read(HERE/'final_acceptance.json');require(final['status']=='PASS_INDEPENDENT_SG8_PCHIP_FINAL','independent final failed')
        save(HERE/'completion.json',dict(final,status='PASS_COMPLETE_426_SG8_PCHIP_ZIP_ON_LINUX',
            independent_final_sha256=sha(HERE/'final_acceptance.json')))
        state('PASS_COMPLETE_426_SG8_PCHIP_ZIP_ON_LINUX',candidate=final['candidate'])
    except BaseException:
        save(HERE/'execution_failure.json',dict(utc=utc(),traceback=traceback.format_exc(),successful_raw_preserved=True))
        state('STOP_ENGINEERING_NEW_VERSION_REQUIRED');raise


if __name__=='__main__':main()
