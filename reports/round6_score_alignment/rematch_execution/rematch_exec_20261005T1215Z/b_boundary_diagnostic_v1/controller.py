"""One owned GPU diagnostic followed by independent CPU replay and real cost."""
import fcntl
import os
import socket
import subprocess
import traceback
import bdiag_common as c


def main():
    c.require(socket.gethostname()=='inspur-NP5570M5','wrong host')
    guard=(c.HERE/'controller.lock').open('a');fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
    c.require(not (c.HERE/'registration.json').exists(),'already registered; never repeat')
    c.verify()
    c.save(c.HERE/'registration.json',{'utc':c.utc(),'pid':os.getpid(),'pgid':os.getpgrp(),
        'source_lock_sha256':c.sha(c.HERE/'source_lock.json'),'single_controller':True})
    try:
        c.progress('RUNNING_OWNED_32B_MATCHED_BOUNDARY_DIAGNOSTIC')
        command=[c.PY,'-B',str(c.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
            '--name','aic_BBOUND_v1_diagnostic','--max-seconds','14400','--planned-output-bytes',str(1500<<20),
            '--capacity-reason','Existing16 non-test event matched source contexts; lossless64 frames/receipts, no new weights/data; live shared conflicts and capacity',
            '--queue-seconds','259200','--',c.PY,'-B',str(c.HERE/'bdiag_engine.py')]
        with (c.HERE/'diagnostic.wrapper.log').open('x') as log:
            result=subprocess.run(command,cwd=c.RUN,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        c.require(result.returncode==0,'actual owned32B diagnostic failed, raw preserved')
        c.progress('RUNNING_CPU_FULL_MATCHED_DIAGNOSTIC_ACCEPTANCE')
        with (c.HERE/'report.cpu.log').open('x') as log:
            result=subprocess.run([c.PY,'-B',str(c.HERE/'report.py')],cwd=c.RUN,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        c.require(result.returncode==0,'independent matched CPU replay failed')
    except BaseException as error:
        c.save(c.HERE/'execution_failure.json',{'utc':c.utc(),'error':type(error).__name__+': '+str(error),
            'traceback':traceback.format_exc(),'all_original_and_successful_bytes_preserved':True,
            'next':'AGENT_REPRODUCE_REPAIR_IN_NEW_VERSION_WITH_EXACT_SUCCESS_REUSE'})
        c.progress('STOP_BOUNDARY_ENGINEERING_AGENT_REPAIRS',error=str(error))
        raise


if __name__=='__main__':main()
