"""Local-only discussion packets and ledger; never operates a browser."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]
TASK = 'AIC-VIDEO-REMATCH-NEXT-20261005'

def write_new(path, text):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(text)

def info(path):
    b=path.read_bytes()
    return {'path': str(path), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

sources = ['AGENTS.md','ROADMAP.md',
 'reports/round6_score_alignment/PROJECT_CONTEXT_AND_ATTRIBUTION_20260921.md',
 'reports/round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z/REPORT.md',
 'reports/round6_score_alignment/rematch_intake/REMATCH_STRATEGY_20261005.md']

packet = (ROOT/'opening.md').read_text(encoding='utf-8')
source_meta=[]
for rel in sources:
    path=PROJECT/rel
    body=path.read_text(encoding='utf-8-sig')
    # Only disclosed anonymization of unnecessary account/test-item identifiers.
    body=body.replace('AIC-2026-29124269','[队伍编号已脱敏]')
    body=body.replace('队伍“我说的都对”','队伍[名称已脱敏]')
    body=body.replace('队伍名：我说的都对','队伍名：[已脱敏]')
    body=body.replace('视频 97','[测试视频编号未共享]')
    meta=info(path); meta['relative_path']=rel;source_meta.append(meta)
    packet+=f'\n\n---\n\n# 附录原文：{rel}\n\n源文件 SHA256：{meta["sha256"]}。历史状态按开头勘误解释。\n\n'+body

url='https://huggingface.co/api/models/Qwen/Qwen3-VL-8B-Instruct'
data=json.load(urllib.request.urlopen(url,timeout=25))
public_meta={'source':url,'read_utc':datetime.now(timezone.utc).isoformat(),
 'id':data['id'],'revision':data['sha'],'safetensors':data.get('safetensors'),
 'scope':'Public metadata only; weights not downloaded or loaded'}
write_new(ROOT/'qwen8b_public_metadata.json',json.dumps(public_meta,ensure_ascii=False,indent=2)+'\n')
packet+='\n\n# 附录：Qwen8B公共元数据\n\n```json\n'+json.dumps(public_meta,ensure_ascii=False,indent=2)+'\n```\n'
write_new(ROOT/'context-r00.md',packet)
write_new(ROOT/'source-manifest.json',json.dumps(source_meta,ensure_ascii=False,indent=2)+'\n')
ledger={'task_id':TASK,'created_utc':datetime.now(timezone.utc).isoformat(),
 'authorization':'User explicitly invokes skill and authorizes AI discussion; no new training/inference/submission',
 'pro_already_used':0,'pro_confirmation':'User answer in current chat: 本任务还没问过 Pro（0 次）',
 'packets':{'r00':info(ROOT/'context-r00.md')},'rounds':[],
 'participants':{
 'pro':{'browser':'Chrome','tab_id':'1769566567','url':'https://chatgpt.com/g/g-p-6ab0f33aae10819190801ea5ae9e5194/project','model':'Pro','verification':'UI menu Pro; 研究 project; no message sent'},
 'tibo':{'browser':'Chrome','tab_id':'1769566566','url':'https://chatgpt.com/dots/01a0f089-8f7d-7137-b9a7-249ad0fa701a','model':'Tibo之父','verification':'UI dot identity, underlying model unspecified'},
 'sol':{'browser':'Edge','tab_id':'364493872','url':'https://chatgpt.com/','model':'5.6 sol','mode':'高','verification':'High UI; base model explicitly confirmed by user'},
 'grok':{'browser':'Edge','tab_id':'364493847','url':'https://grok.com/','model':'Grok','mode':'Expert','verification':'UI checked Expert'},
 'gemini':{'browser':'Edge','tab_id':'364493882','url':'https://gemini.google.com/app?hl=zh-cn','model':'3.8 Flash','mode':'扩展思考','verification':'UI selected 3.8 Flash, then Flash 扩展; user directed Edge; Chrome ERR_CONNECTION_CLOSED retained'}},
 'status':'PREPARED_NOT_SENT'}
write_new(ROOT/'ledger.json',json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'project':str(PROJECT),'packet':info(ROOT/'context-r00.md'),'lines':len(packet.splitlines())},ensure_ascii=False,indent=2))
