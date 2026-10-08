"""One exact developer alternative, then gated NONTEST8 and426 closure."""
import fcntl
import os
import socket
import subprocess
import traceback
import nr_common as c

def cpu(name,args):
    c.verify();c.state('RUNNING_CPU_'+name.upper())
    with (c.HERE/(name+'.cpu.log')).open('x') as log:
        result=subprocess.run([c.PY,'-B',*map(str,args)],cwd=c.RUN,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
    c.require(result.returncode==0,'CPU stage failed: '+name)

def gpu(name,args,maximum,planned):
    c.verify();c.state('RUNNING_GPU_'+name.upper())
    command=[c.PY,'-B',str(c.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
        '--name','aic_NRA_v1_'+name,'--max-seconds',str(maximum),'--planned-output-bytes',str(planned),
        '--capacity-reason','Existing fixed native sources and B weights; same-count native nearest ordinal alignment; live shared conflicts and actual capacity',
        '--queue-seconds','259200','--',c.PY,'-B',*map(str,args)]
    with (c.HERE/(name+'.wrapper.log')).open('x') as log:
        result=subprocess.run(command,cwd=c.RUN,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
    p=c.RUN/'controller'/('aic_NRA_v1_'+name+'.resource.json');v=c.read(p)
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
        charges['nontest']=gpu('nontest',[c.HERE/'nr_engine.py','nontest'],14400,500<<20)
        cpu('nontest_replay',[c.HERE/'nr_report.py','nontest'])
        for step in ('assemble','finish'):cpu('nontest_'+step,[c.HERE/'packager.py',step,'nontest'])
        charges['developer']=gpu('developer',[c.HERE/'nr_engine.py','developer'],14400,400<<20)
        cpu('developer_report',[c.HERE/'nr_report.py','developer'])
        report=c.read(c.HERE/'developer_01/report.json')
        if report['status']!='GO_ONE_NATIVE_ROUND_ALIGNMENT_RISK_PACKAGE':
            c.save(c.HERE/'scientific_stop.json',{'utc':c.utc(),'report':report,'resources':charges,
                'no_final_426_ZIP':True,'next':'FINITE_REGISTERED_INPUT_MECHANISMS_EXHAUSTED_KEEP_B_NO_FURTHER_PROMPT_PIXEL_DENSITY_SCAN'})
            c.state('STOP_ROUND_ALIGNMENT_INVESTMENT_FINITE_EVIDENCE_EXHAUSTED',resources=charges);return
        cpu('rematch_prepare',[c.HERE/'nr_engine.py','plan-rematch'])
        charges['rematch']=gpu('rematch',[c.HERE/'nr_engine.py','rematch'],43200,2000<<20)
        for step in ('assemble','finish'):cpu('rematch_'+step,[c.HERE/'packager.py',step,'rematch'])
        cpu('independent_final',[c.HERE/'final_acceptance.py'])
        final=c.read(c.HERE/'final_acceptance.json');c.require(final['status']=='PASS_INDEPENDENT_NATIVE_ROUND_ALIGNMENT_FINAL','final independent closure missing')
        c.save(c.HERE/'completion.json',dict(final,status='PASS_COMPLETE_426_NATIVE_ROUND_ALIGNMENT_ZIP_ON_LINUX',resources=charges))
        c.state('PASS_COMPLETE_426_NATIVE_ROUND_ALIGNMENT_ZIP_ON_LINUX',candidate=final['candidate'])
    except BaseException as error:
        c.save(c.HERE/'execution_failure.json',{'utc':c.utc(),'error':type(error).__name__+': '+str(error),
            'traceback':traceback.format_exc(),'successful_raw_unchanged':True,'resources':charges})
        c.state('STOP_ENGINEERING_AGENT_REPAIRS_IN_NEW_VERSION',error=str(error));raise

if __name__=='__main__':main()
