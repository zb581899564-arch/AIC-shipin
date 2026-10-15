"""One non-test engineering run, then one 426-video experimental candidate."""
import datetime as dt,fcntl,json,os,subprocess,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;D=H/'contest_v1'
ROOT=Path('/home/inspur/aic_video_work');PY=ROOT/'env/qwen3vl_isolated_20260910/bin/python'
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z';RUNNER=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def save(name,value):
    p=D/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(value,indent=2));t.replace(p)
def stage(mode,scope):
    name=mode+'_'+scope;save('state.json',{'utc':utc(),'stage':name});args=[str(PY),'-B',str(H/'contest_engine.py'),mode,scope]
    start=time.monotonic()
    if mode=='generate':
        job='aic_ANNSEL10_'+scope+'_01'
        args=[str(PY),'-B',str(RUNNER),'--name',job,'--max-seconds','14400','--planned-output-bytes',str(512<<20),
          '--capacity-reason','Qualified separate image-score selector; CPU native PNGs prepared on existing disk, same 8B measured generation peaks, actual shared conflicts/capacity; old full spatial field exact reuse',
          '--',*args]
    with (D/(name+'.log')).open('x') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'USE_TF':'0'})
    if mode=='generate':
        receipt=json.loads((RUN/'controller'/(job+'.resource.json')).read_text())
        ledger=[json.loads(s) for s in (ROOT/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()]
        matches=[v for v in ledger if v['name']==job];assert len(matches)==1 and matches[0]==receipt
        save(job+'.resource.json',receipt);assert receipt['status']=='completed' and receipt['exit_code']==0
    else:save(name+'.cpu.json',{'utc':utc(),'seconds':time.monotonic()-start,'exit_code':r.returncode,'GPU_model_calls':0})
    assert r.returncode==0,(name,r.returncode)
def main():
    D.mkdir(exist_ok=True);lock=(D/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (D/'started.json').exists();assert json.loads((H/'quality_result.json').read_text())['stage2_pass'] is True
    save('started.json',{'utc':utc(),'pid':os.getpid(),'authorization':'主控替Pro，独立讨论、通过预定投入门后非测试8与一次426实验候选，交付可提交ZIP',
      'no_recipe_tuning_after_dev':True,'threshold_x20':49,'production_replaced':False})
    for scope in ('nontest','rematch'):
        for mode in ('prepare','generate','replay','finish'):stage(mode,scope)
        receipt=json.loads((D/(scope+'_01/package_receipt.json')).read_text());assert receipt['videos']==(8 if scope=='nontest' else 426)
    save('completion.json',{'utc':utc(),'status':'PASS_COMPLETE_ONE_426_NEW_TRAINED_IMAGE_SELECTOR_EXPERIMENTAL_ZIP',
      'nontest':json.loads((D/'nontest_01/package_receipt.json').read_text()),'rematch':json.loads((D/'rematch_01/package_receipt.json').read_text()),
      'production_replaced':False,'official_score':None,'uploaded':False,'prior_costs_preserved':True})
    save('state.json',{'utc':utc(),'stage':'COMPLETE_ZIP_READY_FOR_INDEPENDENT_FINAL_ACCEPTANCE'})
if __name__=='__main__':
    try:main()
    except BaseException:
        save('failure.json',{'utc':utc(),'traceback':traceback.format_exc()});save('state.json',{'utc':utc(),'stage':'FAILED_PRESERVE_RAW_AND_SUCCESS'});raise
