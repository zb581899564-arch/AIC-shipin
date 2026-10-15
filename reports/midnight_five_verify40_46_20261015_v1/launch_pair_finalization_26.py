"""One CPU-only launch, only after the actual new supplemental eight-gate PASS."""
from pathlib import Path
import json
import subprocess

R = Path(__file__).resolve().parent
CODE = '''from pathlib import Path
import datetime as dt,hashlib,json,os,shutil,socket,subprocess
h=Path('/home/inspur/aic_video_work');r=h/'midnight_five_verify40_46_20261015_v1';n=h/'midnight_pair_applicability_20261015_v1'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert socket.gethostname()=='inspur-NP5570M5'
assert not (r/'pair_supplement_finalization_launch_26.json').exists()
assert not (r/'pair_supplement_finalization_25').exists()
assert not (r/'packages/package_REDUNDANT').exists()
complete=read(n/'control_01/completion.json');result=read(n/'policy_fresh_comparison.json')
assert complete['status']=='NATURAL_COMPLETE_FIRST_SHORT_SOURCE_PAIR_APPLICABILITY_CONFIRMATION'
assert result['status']=='FIRST_FRESH_POLICY_COMPARISON_COMPLETE' and result['selected_policies']==['PAIR_ONLY']
assert result['passed_policies']['PAIR_ONLY'] is True and result['policies']['PAIR_ONLY']['PASS'] is True
expected={'full_group','macro_F1_not_lower','macro_precision_not_lower','every_source_F1_loss_at_most_001','invalid_decisions_zero','full_original_rater_denominator','real_changed_sources','no_new_native_frames'}
assert set(result['policies']['PAIR_ONLY']['gates'])==expected and all(v is True for v in result['policies']['PAIR_ONLY']['gates'].values())
deployment=read(r/'pair_supplement_package_deployment_25.json')
for p,d in deployment['code_files'].items():assert sha(Path(p))==d
with (r/'pair_supplement_package_preflight_26.json').open('x') as f:
 json.dump(dict(host=socket.gethostname(),UTC=dt.datetime.now(dt.timezone.utc).isoformat(),meminfo=Path('/proc/meminfo').read_text(),disk=dict(zip(('total','used','free'),shutil.disk_usage(r))),actual_processes=subprocess.run(['ps','-eo','pid,ppid,stat,pcpu,pmem,args'],capture_output=True,text=True,check=True).stdout,scope='CPU_ONLY_NEW_FIFTH_NO_SHARED_GPU_CLAIM',no_external_process_changes=True),f)
argv=[str(h/'env/qwen3vl_isolated_20260910/bin/python'),'-B',str(r/'pair_supplement_package_code_v1/finalize_supplement.py')]
with (r/'pair_supplement_finalize_26.log').open('x') as log:
 p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
 actual=Path('/proc')/str(p.pid)
 value=dict(pid=p.pid,start_ticks=(actual/'stat').read_text().split()[21],argv=argv,actual_cmdline=[v.decode() for v in (actual/'cmdline').read_bytes().split(b'\\0') if v],UTC=dt.datetime.now(dt.timezone.utc).isoformat(),CUDA_VISIBLE_DEVICES='',new_model_calls=0,automatic_retry=False,actual_supplemental_comparison_sha256=sha(n/'policy_fresh_comparison.json'))
with (r/'pair_supplement_finalization_launch_26.json').open('x') as f:json.dump(value,f,indent=2)
print(json.dumps(value))
'''

if __name__ == '__main__':
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
        'aic-inspur-tailscale', 'python3', '-'], input=CODE, text=True, capture_output=True)
    receipt = dict(exit=result.returncode, stdout=result.stdout, stderr=result.stderr[-3000:])
    with (R / 'pair_finalization_launch_26_receipt.json').open('x', encoding='utf8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
    print(result.stdout)
    print(result.stderr[-1500:])
    result.check_returncode()
