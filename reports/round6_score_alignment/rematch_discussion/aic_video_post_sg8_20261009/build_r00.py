from pathlib import Path
import hashlib,json,shutil
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]/'rematch_execution'/'rematch_exec_20261005T1215Z'
OLD=HERE.parent/'aic_video_replan_20261009'
sources=[ROOT/'controller/SG8_FINITE_CONCLUSION_20261009.md',
 ROOT/'controller/SG8_scientific_stop_acceptance_20261009_summary.json',
 ROOT/'spatial_gap8_pchip_slot4_v2/PROTOCOL.md',
 ROOT/'spatial_gap8_pchip_slot4_v2/sg8_math.py',
 ROOT/'spatial_gap8_pchip_slot4_v2/sg8_report.py',
 ROOT/'spatial_gap8_pchip_slot4_v2/sg8_sampling.py',HERE/'host-r00.md']
prior=(OLD/'context-final2.md').read_bytes()
assert hashlib.sha256(prior).hexdigest()=='442036c60c2fe2a48b050679acbd41f7e1d80ee879e14f4810107a5cb64c0c7c'
body=bytearray(prior)
meta=[]
for p in sources:
 d=p.read_bytes(); meta.append(dict(file=str(p),bytes=len(d),sha256=hashlib.sha256(d).hexdigest()))
 body.extend(('\n\n# POST-SG8 新增完整依据 '+p.name+'\n\n').encode())
 if p.suffix in ('.py','.json'):body.extend(('```'+p.suffix[1:]+'\n').encode())
 body.extend(d)
 if p.suffix in ('.py','.json'):body.extend(b'\n```\n')
body.extend(b'\n\n# END_POST_SG8_R00\n')
out=HERE/'context-r00.md'
with out.open('xb') as f:f.write(body)
info=dict(utc=datetime.now(timezone.utc).isoformat(),task='AIC-VIDEO-REMATCH-NEXT-20261005',node='POST-SG8-20261009',file=out.name,bytes=len(body),lines=body.count(b'\n'),sha256=hashlib.sha256(body).hexdigest(),prior_exact_prefix=True,appended=meta)
(HERE/'packet-r00-receipt.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
(HERE/'ledger.json').write_text(json.dumps(dict(task_id=info['task'],node=info['node'],created_utc=info['utc'],user_request='那你继续用一锅炖这个skill去讨论，pro还剩4次可用，讨论出来直接安排工作',pro=dict(continuous_limit=8,used_or_reserved_before_node=4,remaining_before_node=4,budget_directory=str(HERE.parent/'aic_video_rematch_20261005T1044Z/pro-budget'),new_grant=False),packets=[info],participants={},rounds={},implementation_status='NOT_STARTED_DISCUSSION_ONLY'),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(info,ensure_ascii=False))
