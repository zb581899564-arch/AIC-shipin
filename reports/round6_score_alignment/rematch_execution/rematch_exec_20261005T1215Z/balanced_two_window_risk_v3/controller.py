"""One exact developer alternative, then gated NONTEST8 and426 closure."""
import fcntl
import os
import socket
import subprocess
import traceback
import bw_common as c

def cpu(name,args):
    c.verify();c.state('RUNNING_CPU_'+name.upper())
    with (c.HERE/(name+'.cpu.log')).open('x') as log:
        result=subprocess.run([c.PY,'-B',*map(str,args)],cwd=c.RUN,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
    c.require(result.returncode==0,'CPU stage failed: '+name)

def gpu(name,args,maximum,planned):
    c.verify();c.state('RUNNING_GPU_'+name.upper())
    command=[c.PY,'-B',str(c.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
        '--name','aic_BW_risk_v3_'+name,'--max-seconds',str(maximum),'--planned-output-bytes',str(planned),
        '--capacity-reason','Existing fixed native sources and B weights; same-count exact balanced two-window domains; live shared conflicts and actual capacity',
        '--queue-seconds','259200','--',c.PY,'-B',*map(str,args)]
    with (c.HERE/(name+'.wrapper.log')).open('x') as log:
        result=subprocess.run(command,cwd=c.RUN,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
    p=c.RUN/'controller'/('aic_BW_risk_v3_'+name+'.resource.json');v=c.read(p)
    c.require(result.returncode==0 and v['status']=='completed' and v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0,'actual GPU terminal failed')
    return {'path':str(p),'sha256':c.sha(p),'charged_seconds':v['charged_seconds']}

def main():
    c.require(socket.gethostname()=='inspur-NP5570M5','wrong host')
    lock=(c.HERE/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    c.require(not (c.HERE/'registration.json').exists(),'already registered; never restart')
    c.verify();c.save(c.HERE/'registration.json',{'utc':c.utc(),'pid':os.getpid(),'pgid':os.getpgrp(),
        'source_lock_sha256':c.sha(c.HERE/'source_lock.json')})
    charges={}
    try:
        handoff=c.read(c.HERE/'engineering_handoff.json')
        c.require(handoff['status']=='PASS_V2_TYPE_REPRESENTATION_REPAIR_EXACT_RAW_CPU_AND_NT_HANDOFF' and handoff['nontest_exact_acceptance_reused'],'exact previous successful NT handoff missing')
        c.state('PASS_EXACT_PREVIOUS_NONTEST_11_STRICT_HANDOFF')
        charges['developer']=gpu('developer',[c.HERE/'bw_engine.py','developer'],14400,400<<20)
        cpu('developer_report',[c.HERE/'bw_report.py','developer'])
        report=c.read(c.HERE/'developer_01/report.json')
        c.require(report['status']=='PASS_ENGINEERING_USER_ACCEPTED_RISK_CONTINUE_426','developer engineering not accepted')
        charges['rematch']=gpu('rematch',[c.HERE/'bw_engine.py','rematch'],43200,2000<<20)
        cpu('rematch_replay',[c.HERE/'bw_report.py','rematch'])
        for step in ('assemble','finish'):cpu('rematch_'+step,[c.HERE/'packager.py',step,'rematch'])
        cpu('independent_final',[c.HERE/'final_acceptance.py'])
        final=c.read(c.HERE/'final_acceptance.json');c.require(final['status']=='PASS_INDEPENDENT_BALANCED_TWO_WINDOW_RISK_FINAL','final independent closure missing')
        c.save(c.HERE/'completion.json',dict(final,status='PASS_COMPLETE_426_BALANCED_TWO_WINDOW_RISK_ZIP_ON_LINUX',resources=charges))
        c.state('PASS_COMPLETE_426_BALANCED_TWO_WINDOW_RISK_ZIP_ON_LINUX',candidate=final['candidate'])
    except BaseException as error:
        c.save(c.HERE/'execution_failure.json',{'utc':c.utc(),'error':type(error).__name__+': '+str(error),
            'traceback':traceback.format_exc(),'successful_raw_unchanged':True,'resources':charges})
        c.state('STOP_ENGINEERING_AGENT_REPAIRS_IN_NEW_VERSION',error=str(error));raise

if __name__=='__main__':main()
