"""Receive only the small terminal summary; all raw/tensors remain Linux."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).parent
SCRIPT = '''import json,sys
from pathlib import Path
sys.path.insert(0,"/home/inspur/aic_video_work/t_branch_execution_20261022_v1/code")
from t_io import ROOT,WORK,check,identity,read,save
from frozen_branch46 import RUN
root=ROOT/'localized_query122'; terminal=ROOT/'localized_query_remaining123/completion.json'
if not terminal.exists():
 print(json.dumps(dict(state='NOT_TERMINAL_NO_RECEIPT_CREATED')));sys.exit(0)
done=read(terminal);cpu=read(check(done['first_CPU']))
job='T_fixed_local_native_visibility25_original8B_20261023_v122'
resource=read(RUN/'controller'/(job+'.resource.json'))
ledger=[json.loads(s) for s in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if s.strip()]
if resource['status']!='completed' or resource['exit_code']!=0 or [x for x in ledger if x.get('name')==job]!=[resource]:raise ValueError('Natural terminal/unique ledger differs')
protocol=read(ROOT/'code/parallel_protocol105.json')
protected={key:identity(check(protocol[key])) for key in ['protected_original','protected_best']}
target=ROOT/'short_localized122_123.json'
if not target.exists():
 gpu=read(root/'GPU_completion.json'); proofs=read(check(cpu['first_CPU']))
 save(target,dict(state=done['state'],terminal=identity(terminal),first_CPU=done['first_CPU'],
  actual_first_CPU_cases=len(proofs['first_proofs']),GPU_seconds=resource['charged_seconds'],unique_ledger=True,
  all_goal_GPU_seconds=done['all_goal_GPU_seconds'],actual_complete_parameters=gpu['actual_complete_parameters'],
  actual_new_logical_windows=25,actual_new_physical_forwards=50,actual_new_native_decisions=800,
  new_training_updates=0,metrics=cpu['metrics'],ranking=cpu['ranking'],
  original_unmasked120_metrics_adopted=cpu['original_unmasked120_metrics_adopted'],
  original_unmasked120_ranking_adopted=cpu['original_unmasked120_ranking_adopted'],
  native_F1_gain_over_unmasked120=cpu['native_F1_gain_over_unmasked120'],
  gate=cpu['preregistered_local_information_gate'],gate_pass=cpu['local_information_gate_pass'],
  protected=protected,confirmation_sources_read=0,new_T_ZIPs=0,
  peak_torch_bytes=gpu['peak_torch_bytes'],temporary_retirement=identity(root/'activation_retirement.json'),
  fresh_primary_review=identity(ROOT/'localized_query_remaining123/official_counter_only_review.json'),
  original_preGPU_failure_preserved=True,not_official_score_or_independent_validation=True))
ref=identity(target)
if ref['bytes']>12288:raise ValueError('Summary unexpectedly exceeds small receipt scope')
print(json.dumps(dict(receipt=ref,text=target.read_text())))
'''


def main():
    process = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
        '-o', 'ConnectTimeout=12', 'aic-inspur-tailscale',
        '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -'],
        input=SCRIPT, text=True, capture_output=True, timeout=45)
    if process.returncode:
        raise RuntimeError(process.stderr)
    packet = json.loads(process.stdout)
    if 'receipt' not in packet:
        print(packet); return
    data = packet['text'].encode('utf-8'); ref = packet['receipt']
    if len(data) != ref['bytes'] or hashlib.sha256(data).hexdigest() != ref['sha256']:
        raise ValueError('Small final receipt differs across Linux/Windows')
    target = HERE / Path(ref['path']).name
    if target.exists():
        if target.read_bytes() != data:
            raise ValueError('Existing receipt must not be overwritten')
    else:
        with target.open('xb') as stream:
            stream.write(data)
    print(json.dumps(dict(receipt=ref, content=json.loads(data)), ensure_ascii=False))


if __name__ == '__main__':
    main()
