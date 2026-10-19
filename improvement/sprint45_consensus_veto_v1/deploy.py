"""Deploy exactly one small CPU control under the human's current route scope."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPORT = HERE.parents[1] / 'reports/sprint45_20261016_v1'
source = HERE / 'package_veto.py'
ast.parse(source.read_text(encoding='utf-8'))
digest = hashlib.sha256(source.read_bytes()).hexdigest()
remote = '/home/inspur/aic_video_work/incoming_consensus_veto_last_risk_01.py'
options = ['-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', '-o',
           'ProxyCommand="C:/Program Files/Tailscale/tailscale.exe" nc %h %p']
subprocess.run(['scp'] + options + [str(source), 'aic-inspur-tailscale:' + remote], check=True, timeout=90)
code = r'''
import ast,datetime,hashlib,json,os,pathlib,shutil,subprocess
W=pathlib.Path('/home/inspur/aic_video_work');root=W/'sprint45_consensus_veto_last_risk_20261016_v1'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def save(p,v):
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
assert subprocess.check_output(['hostname']).decode().strip()=='inspur-NP5570M5'
incoming=pathlib.Path(REMOTE);assert incoming.stat().st_size==SIZE and sha(incoming)==SHA
ast.parse(incoming.read_text())
assert not root.exists(),'Do not duplicate existing root or launch'
global_root=W/'sprint45_global_context_20261016_v1'
assert json.loads((global_root/'chain_completion.json').read_text())['status']=='GLOBAL_LOCAL_TWO_RISK_DIRECTIONS_NATURAL_COMPLETE'
root.mkdir();(root/'code').mkdir();(root/'code/package_veto.py').write_bytes(incoming.read_bytes())
run=W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
adopt=W/'semantic_context_production_20261016_v1'
authorization=dict(user_request='现在还有一个小时到明天，你还可以做一个包，另外你现在这个tailscale只能传输最后的zip，你看看现在怎么安排',
 user_route_answer='允许SSH控制和必要小代码，仅下载最终ZIP',
 declared_method='40.47 baseline intersect(saved_global_mask OR saved_payoff_mask); delete only both0, all retained original boxes unchanged',
 unknown_online_effect=True,no_claim_of_judge_improvement=True,not_independent_judges=True,
 no_training_or_model_calls=True,one_candidate_only=True,no_threshold_scan=True)
save(root/'user_authorization_01.json',authorization)
reg=dict(schema='CONSENSUS_VETO_LAST_RISK_20261016_V1',selection='BASELINE_FRAME_AND_GLOBAL_OR_PAYOFF',
 actual_total_parameters=8782557449,offline_effect_validation=False,online_effect='UNKNOWN',
 user_authorization=ref(root/'user_authorization_01.json'),
 baseline=ref(adopt/'package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'),
 rule_check=ref(W/'sprint45_current_official_rules_20261016_v1/official_rule_check_before_package.json'),
 generation_terminal=ref(global_root/'chain_completion.json'),GPU_resource=ref(global_root/'GPU_resource.json'),
 unique_resource=ref(global_root/'unique_resource_verified.json'),output_QA=ref(global_root/'output_acceptance.json'),
 field_inputs=ref(W/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json'),
 run_root=str(run),historical_canonical_sha256=json.loads((adopt/'production_registration.json').read_text())['historical_prediction_sha256'],
 current_candidate_completions=[ref(global_root/'packages_01/GLOBAL_CONTEXT/completion.json'),
 ref(global_root/'packages_01/EVENT_PAYOFF/completion.json'),
 ref(W/'sprint45_width_packages_20261016_v1/packages_01/NATIVE16_LEARNED_WIDTH/completion.json')],
 source_code=ref(root/'code/package_veto.py'))
save(root/'registration.json',reg)
py=W/'env/qwen3vl_isolated_20260910/bin/python'
env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
command=[str(py),'-B','-u',str(root/'code/package_veto.py'),'--root',str(root)]
with (root/'stdout.log').open('xb') as out,(root/'stderr.log').open('xb') as err:
 p=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err,env=env,start_new_session=True)
receipt=dict(root=str(root),pid=p.pid,start_ticks=pathlib.Path('/proc',str(p.pid),'stat').read_text().split()[21],
 command=command,code_bytes=SIZE,code_sha256=SHA,registration=ref(root/'registration.json'),
 free_bytes=shutil.disk_usage(root).free,CPU_only=True,new_model_calls=0,new_optimizer_updates=0,
 utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save(root/'launch.json',receipt);print(json.dumps(receipt))
'''
code = 'REMOTE=' + repr(remote) + '\nSIZE=' + str(source.stat().st_size) + '\nSHA=' + repr(digest) + '\n' + code
result = subprocess.run(['ssh'] + options + ['aic-inspur-tailscale', 'python3 -'],
                        input=code, capture_output=True, text=True, timeout=45)
(REPORT / 'veto_deploy_stdout.txt').write_text(result.stdout, encoding='utf-8')
(REPORT / 'veto_deploy_stderr.txt').write_text(result.stderr, encoding='utf-8')
print(result.stdout)
print(result.stderr)
result.check_returncode()
(REPORT / 'veto_launch.json').write_text(json.dumps(json.loads(result.stdout), ensure_ascii=False, indent=2), encoding='utf-8')
