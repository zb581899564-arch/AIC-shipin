"""Wait for the registered first fresh result, then only publish its passing arms."""
from pathlib import Path
import datetime as dt,hashlib,json,os,subprocess,time,traceback
ROOT=Path('/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1')
PY=ROOT.parent/'env/qwen3vl_isolated_20260910/bin/python'
def read(p):return json.loads(p.read_text())
def save(p,d):
    with p.open('x') as f:json.dump(d,f,indent=2)
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
if __name__=='__main__':
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    deployment=read(ROOT/'quality_finalization_deployment_17.json')
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==deployment['source_SHA256']
    state=ROOT/'quality_finalization_17';state.mkdir(exist_ok=False)
    save(state/'started.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],UTC=utc()))
    fresh=ROOT/'relative_confirm/control_14'
    try:
        while not ((fresh/'completion.json').exists() and (ROOT/'package_inputs.json').exists()):
            for p in [fresh/'failure.json',ROOT/'risk_finalization_15/failure.json',ROOT/'production_unique_09/chain_failure.json']:
                if p.exists():raise RuntimeError('Actual dependency failed: '+str(p))
            if dt.datetime.now(dt.timezone.utc)>=dt.datetime.fromisoformat('2026-10-15T16:00:00+00:00'):raise RuntimeError('Taipei midnight reached before all actual dependencies')
            time.sleep(15)
        complete=read(fresh/'completion.json')
        assert complete['status']=='NATURAL_COMPLETE_FIRST_FRESH_TWO_FROZEN_POLICIES'
        for operation in ['admit_quality','package_quality']:
            with (state/(operation+'.log')).open('x') as log:
                subprocess.run([str(PY),'-B',str(ROOT/'finalization_code_v1/finalize.py'),operation],env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT,check=True)
        arms=read(ROOT/'quality_admission.json')['arms']
        save(state/'completion.json',dict(status='COMPLETED_FIXED_POLICY_QUALITY_DISPOSITION_AND_AVAILABLE_PACKAGES',quality_status={k:v['status'] for k,v in arms.items()},actual_total_new_packages=len(list((ROOT/'packages').glob('package_*/completion.json'))),required_new_packages=5,UTC=utc(),new_model_calls=0,old_scientific_gates_changed=False))
    except BaseException as e:
        save(state/'failure.json',dict(error=repr(e),traceback=traceback.format_exc(),UTC=utc(),automatic_retry=False,preserve_all_successful=True));raise
