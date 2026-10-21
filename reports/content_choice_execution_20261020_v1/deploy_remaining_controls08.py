"""Small controllers/current rule evidence only; does not launch production."""
import ast
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess

H=Path(__file__).resolve().parent
members={}
for name in ['production_controller08.py','package_controller09.py','official_track_current_07.md',
             'official_notice_current_07.md','official_notice_index_current_07.html']:
    b=(H/name).read_bytes()
    if name.endswith('.py'):ast.parse(b,filename=name)
    members[name]=dict(content=b.decode('utf-8'),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
source=r'''
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,socket
R=Path('/home/inspur/aic_video_work/content_choice_20261019_v1')
assert socket.gethostname()=='inspur-NP5570M5'
assert json.loads((R/'user_resume_01.json').read_text())['explicit_human_resume'] is True
assert not (R/'remaining_controls_deployment08.json').exists()
audit=R/'current_rule_audit07';audit.mkdir()
refs={}
for name,d in MEMBERS.items():
 b=d['content'].encode('utf-8');assert len(b)==d['bytes'] and hashlib.sha256(b).hexdigest()==d['sha256']
 p=(R if name.endswith('.py') else audit)/name
 with p.open('xb') as f:f.write(b)
 refs[name]=dict(path=str(p),bytes=len(b),sha256=d['sha256'])
rules=dict(status='CURRENT_BODY_NOTICE_INDEX_READ_NO_NEW_VIDEO_NOTICE_EXISTING_FULL_READ_ATTACHMENTS_ADOPTED',utc=datetime.now(timezone.utc).isoformat(),
 refs={k:v for k,v in refs.items() if not k.endswith('.py')},latest_relevant_notice='https://www.aicomp.cn/notice/notice-3/5307.html',
 rules_attachment='0930',current_attachment_links_unchanged=True,
 existing_full_read_receipt='/home/inspur/aic_video_work/meaningful_residual_20261018_v1/official_primary_02/receipt.json',
 new_full_PDF_downloads=0,official_label_reads=0,official_training=False,closed_API_official_data=False,
 interpretation='Registered private noncommercial external research only; official data automatic local inference; actual entire main+aux pipeline <=9B; no test manual correction, GT training, leaderboard reverse construction or website submission.',
 skill_backend='agent-reach Jina track/notice; Jina index Schannel failure preserved locally, direct official HTML fallback')
with (R/'official_rule_check_before_production07.json').open('x') as f:json.dump(rules,f,ensure_ascii=False,indent=2)
receipt=dict(utc=datetime.now(timezone.utc).isoformat(),status='CONTROLS_AND_RULE_EVIDENCE_ACCEPTED_NO_PRODUCTION_STARTED',refs=refs,bytes=sum(d['bytes'] for d in MEMBERS.values()),
 original_PR3_code_unchanged=True,automatic_production=False,automatic_package=False)
with (R/'remaining_controls_deployment08.json').open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(receipt))
'''
source='MEMBERS='+repr(members)+'\n'+source
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
r=subprocess.run(['ssh','-o','ConnectTimeout=15','aic-inspur-tailscale',PY+' -B -'],input=source,text=True,encoding='utf-8',capture_output=True,timeout=50)
print(r.stdout);print(r.stderr)
with (H/'remaining_controls_deployment_result08.json').open('x',encoding='utf8') as f:json.dump(dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr),f,ensure_ascii=False,indent=2)
r.check_returncode()
