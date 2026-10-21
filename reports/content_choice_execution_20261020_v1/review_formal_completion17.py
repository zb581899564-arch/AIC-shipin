"""Read only the completed formal aggregate, terminal ledger and frozen receipts."""
import json
from pathlib import Path
import subprocess

SOURCE = r'''
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, socket, subprocess, zipfile
W=Path('/home/inspur/aic_video_work');R=W/'content_choice_20261019_v1'
assert socket.gethostname()=='inspur-NP5570M5'
def load(p):return json.loads(Path(p).read_text())
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
parent=load(R/'production_contrast_controller_completion08.json')
assert parent['status']=='FORMAL_PRODUCTION_COMPLETE_PENDING_EXPLICIT_PACKAGE_REVIEW'
p=R/'production_contrast/completion.json';c=load(p)
assert c['status']=='COMPLETE_PRODUCTION_NOT_PACKAGED' and c['source_count']==426 and c['window_count']==522
assert c['candidate']=='contrast' and c['actual_pipeline_parameters']==8782557449
assert c['counts']['optimizer_steps']==0 and c['counts']['backward_calls']==0
assert len(list((R/'production_contrast').glob('window_*.json')))==522
frozen=load(c['frozen_verification_ref']['path'])
assert frozen['original_TIME_files_unchanged'] is True and frozen['changed_adapter_matrices']==0
assert frozen['optimizer_steps']==0 and frozen['backward_calls']==0
resource=load(parent['resource_ref']['path'])
assert resource['status']=='completed' and resource['exit_code']==0
ledger=[json.loads(s) for s in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if s.strip()]
assert [v for v in ledger if v.get('name')==resource['name']]==[resource]
selection=load(c['selection_ref']['path'])['sources']
assert set(selection)=={str(i) for i in range(426)}
assert all(x['status']=='ACCEPTED' and x['selected_ordinals']==sorted(set(x['selected_ordinals'])) for x in selection.values())
current={(sid,f) for sid,v in selection.items() for f in v['selected_ordinals']}
baseline=W/'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'
bref=ref(baseline)
assert bref['bytes']==384630 and bref['sha256']=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
with zipfile.ZipFile(baseline) as z:
 original=[json.loads(s) for s in z.read('predictions.jsonl').splitlines() if s.strip()]
old_by_source={v['video_id']:{p['frame'] for p in v['predictions']} for v in original}
old={(sid,f) for sid,frames in old_by_source.items() for f in frames}
assert current and current!=old
out=dict(status='MAIN_REVIEW_INPUTS_COMPLETE_NOT_PACKAGE_APPROVAL',utc=datetime.now(timezone.utc).isoformat(),production_ref=ref(p),
 source_count=426,window_count=522,counts=c['counts'],actual_pipeline_parameters=c['actual_pipeline_parameters'],
 frozen_verification=dict(original_TIME_files_unchanged=True,changed_adapter_matrices=0,base_hash=frozen['base']),
 unique_resource=resource,selection_ref=c['selection_ref'],frames=len(current),baseline_frames=len(old),
 added_frames=len(current-old),removed_frames=len(old-current),changed_sources=sum(set(v['selected_ordinals'])!=old_by_source[sid] for sid,v in selection.items()),
 empty_sources=[sid for sid,v in selection.items() if not v['selected_ordinals']],baseline_ref=bref,
 disk_free=shutil.disk_usage(W).free,gpu_apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip(),
 package_admitted=False,automatic_submission=False)
print(json.dumps(out))
'''
r=subprocess.run(['ssh','-o','ConnectTimeout=15','aic-inspur-tailscale','/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -'],input=SOURCE,text=True,capture_output=True,timeout=55)
print(r.stderr)
r.check_returncode()
d=json.loads(r.stdout)
p=Path(__file__).resolve().parent/'formal_completion_main_review_inputs17.json'
with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
print(json.dumps(d,ensure_ascii=False))
