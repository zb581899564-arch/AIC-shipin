"""Main-agent explicit review, only after actual CPU/asset/plan completion."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

HERE = Path(__file__).resolve().parent
W = '/home/inspur/aic_video_work'
R = W + '/content_choice_20261019_v1'
PY = W + '/env/qwen3vl_isolated_20260910/bin/python'
SHA = 'cb6095cc3156319054f23e5a3ad5baeb5ed9d0c1'
now = datetime.now(timezone.utc).isoformat()
docs = {}
for name in ['official_track_current_01.md', 'official_notice_current_01.md', 'official_notice_index_current_01.md']:
    data = (HERE / name).read_bytes()
    docs[name] = dict(content=data.decode('utf-8'), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
review = dict(utc=now, implementation_sha=SHA, reviewed_by='Current execution main agent plus two independent read-only implementation reviewers',
    approved_check_collection=True, no_confirmed_blocker_for_check=True,
    review_scopes=['runtime/causal hidden/rotation/cache/selection/critic/evaluate/driver',
        'adoption/observation/nativePTS/NO_EFFECT/verification/reuse/render/admission'],
    limitations=['Real private asset and new Torch gates must actually pass before GPU.',
        'Before any train collection, main must inspect oracle/headroom and all8 non-tied ranking coverage.',
        'Ranking diagnostics deduplicate native actions to first slot; actual choose retains all4 slots. Report both accurately.',
        'Observation package verification relies on first processor QA plus immutable refs; no repeated inference is evidence of independent QA.'],
    stage_scope='COMMON8_COMPLETE43_CHECK_POOL_ONLY_THEN_CPU_CONTRAST_REVIEW',
    max_new_generations=86, max_new_teacher_forced=344, max_gpu_seconds=3600,
    original_time_control_adoption=43, automatic_train_collection=False,
    automatic_production=False, new_goals=0, new_automations=0)
rules = dict(utc=now, status='CURRENT_TRACK_NOTICE_AND_NOTICE_INDEX_READ_EXISTING_ATTACHMENTS_ADOPTED',
    current_urls=['https://www.aicomp.cn/tracks/tracks-6/4267.html',
        'https://www.aicomp.cn/notice/notice-3/5307.html','https://www.aicomp.cn/notice/notice-3/'],
    no_new_video_supplement_in_current_index=True, current_0930_and_submission_attachment_links_unchanged=True,
    prior_full_attachment_receipt=W+'/meaningful_residual_20261018_v1/official_primary_02/receipt.json',
    actual_attachment_bytes_not_re_fetched_this_round=True,
    interpretation='Registered lawful public original human summary research; no official/test labels, training, third-party API, per-source hand tuning or leaderboard reward; actual entire inference pipeline <=9B; no official score guarantee.',
    documents={k:{'bytes':v['bytes'],'sha256':v['sha256']} for k,v in docs.items()})
source = '''
import hashlib,json,os,pathlib,socket,subprocess
R=pathlib.Path(RUN_ROOT)
assert socket.gethostname()=='inspur-NP5570M5'
def read(p):return json.loads(p.read_text())
def save(p,d):
 with p.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def ref(p):return dict(path=str(p.resolve(strict=True)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
completion=read(R/'cpu_control_completion.json')
assert completion['status']=='PASS_NEW_CPU_ASSET_PLAN'
assert not (R/'cpu_control_failure.json').exists()
assert read(R/'linux_synthetic_cpu.json')['status']=='PASS_SYNTHETIC_CPU'
torch=read(R/'torch_cpu_checks.json')
assert torch['status']=='PASS' and torch['torch_checks']==13 and torch['pure_checks']==30 and torch['failed_checks']==0
assert read(R/'plan/plan.json')['status']=='READY_FOR_EXPLICIT_BOUNDED_STAGES'
audit=R/'execution_review01';audit.mkdir()
for name,data in DOCS.items():
 blob=data['content'].encode('utf-8')
 assert len(blob)==data['bytes'] and hashlib.sha256(blob).hexdigest()==data['sha256']
 with (audit/name).open('xb') as f:f.write(blob)
RULES['document_refs']={name:ref(audit/name) for name in DOCS}
save(audit/'official_rule_check_01.json',RULES)
REVIEW['code_manifest_ref']=ref(R/'code/improvement/content_choice_v1/code_manifest.json')
REVIEW['cpu_control_ref']=ref(R/'cpu_control_completion.json')
REVIEW['official_rule_check_ref']=ref(audit/'official_rule_check_01.json')
save(R/'execution_review_admission.json',REVIEW)
assert not (R/'check_launch.json').exists() and not (R/'check_control_started.json').exists()
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1')
with (R/'check_control_parent.log').open('x') as log:
 p=subprocess.Popen([PYTHON,'-B',str(R/'control.py'),'--mode','check'],cwd=R/'code',env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 ticks=pathlib.Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19]
receipt=dict(status='CURRENT_CPU_ASSET_PLAN_PASS_EXPLICIT_CHECK_STARTED',pid=p.pid,start_ticks=ticks,
 implementation_sha=IMPLEMENTATION_SHA,cpu_completion_ref=ref(R/'cpu_control_completion.json'),
 execution_review_ref=ref(R/'execution_review_admission.json'),automatic_production=False)
save(R/'check_launch.json',receipt);print(json.dumps(receipt))
'''
values = dict(RUN_ROOT=R, PYTHON=PY, IMPLEMENTATION_SHA=SHA, DOCS=docs, RULES=rules, REVIEW=review)
source = '\n'.join(k+'='+repr(v) for k,v in values.items())+'\n'+source
result = subprocess.run(['ssh','-o','ConnectTimeout=15','aic-inspur-tailscale',PY+' -B -'],
    input=source,text=True,encoding='utf-8',capture_output=True,timeout=60)
print(result.stdout);print(result.stderr)
with (HERE/'check_launch_result_01.json').open('x',encoding='utf-8') as f:
    json.dump(dict(utc=now,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr),f,ensure_ascii=False,indent=2)
result.check_returncode()
