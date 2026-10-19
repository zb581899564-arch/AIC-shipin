import hashlib,json,subprocess,zipfile
from pathlib import Path
from remote_control import ROOT,REPORT,OPTIONS
status=json.loads((REPORT/'status_02.json').read_text())
assert status['live'] is None and status['completion.json']['status']=='COMPLETE_TWO_TRAJECTORY_RISKS'
basepath=ROOT/'deliveries/CONTEXT_SEMANTIC_RESIDUAL_8B_20261016/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'
assert hashlib.sha256(basepath.read_bytes()).hexdigest()=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
with zipfile.ZipFile(basepath) as z:base=[json.loads(x) for x in z.read('predictions.jsonl').splitlines()]
b={(r['video_id'],p['frame']):p['bboxes'] for r in base for p in r['predictions']}
delivered=[]
for receipt in status['completion.json']['packages']:
 method=receipt['method'];d=ROOT/'deliveries'/f'{method}_8B_20261017';d.mkdir(exist_ok=False)
 local=d/Path(receipt['path']).name
 subprocess.run(['scp']+OPTIONS+['aic-inspur-tailscale:'+receipt['path'],str(local)],check=True,timeout=90)
 assert local.stat().st_size==receipt['bytes'] and hashlib.sha256(local.read_bytes()).hexdigest()==receipt['sha256']
 with zipfile.ZipFile(local) as z:
  assert z.namelist()==['predictions.jsonl'] and z.testzip() is None
  member=z.read('predictions.jsonl');assert hashlib.sha256(member).hexdigest()==receipt['member_sha256']
 rows=[json.loads(x) for x in member.splitlines()];a={(r['video_id'],p['frame']):p['bboxes'] for r in rows for p in r['predictions']}
 assert len(rows)==426 and len({r['video_id'] for r in rows})==426 and all(r['predictions'] for r in rows)
 assert a.keys()==b.keys() and len(a)==123506 and all(a[k][2]==v[2] for k,v in b.items())
 assert sum(a[k]!=v for k,v in b.items())==receipt['changed_boxes']
 assert all(r['model_params_b']==8782557449/1e9 for r in rows)
 value=dict(receipt,path=str(local),CRC=True,same_as_linux=True,windows_verified=True,time_set_exact40_47=True,all_original_widths_retained=True,transport='USER_AUTHORIZED_TAILSCALE_SMALL_CONTROL_FINAL_ZIP_ONLY')
 (d/'windows_acceptance.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
 delivered.append(value)
state=dict(stage='TWO_TRAJECTORY_RISK_ZIPS_DELIVERED',baseline_user_feedback=40.47,delivered=delivered,new_GPU_calls=0,new_training_updates=0,new_media_decodes=0,goal_created=False,automation_created=False,website_submitted=False,quality_improvement_achieved='UNKNOWN',discussion_paused=True,protocol='PROTOCOL.md')
(REPORT/'current_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(state,ensure_ascii=False,indent=2))
