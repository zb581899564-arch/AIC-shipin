"""Retrieve only complete independent B20 evidence; no model or stage launcher."""
import hashlib
import io
import json
import shlex
import subprocess
import zipfile
from pathlib import Path

from deploy_confirm_cpu_02 import REPORT,PY,SSH
REMOTE='/home/inspur/aic_video_work/sparse_context_iteration_20261013_v1'
from sparse_stage_common_02 import sha


def main():
    out=REPORT/'new_confirm_export_05'
    if out.exists():raise ValueError('Export receiver already exists; inspect receipt, never repeat successful transfer')
    script='''import hashlib,io,json,pathlib,socket,sys,zipfile
b=pathlib.Path(REMOTE);assert socket.gethostname()=='inspur-NP5570M5'
chain=json.loads((b/'new_confirm_chain_04/completion.json').read_text())
assert chain['status']=='PASS_FRESH_B8_EXPORT_PENDING_FROZEN_SPARSE_CONFIRM_NOT_PACKAGE' and chain['registered_sources']==8
files={}
for name in ['new_confirm_chain_04/completion.json','new_confirm_gpu_04/completion.json','new_confirm_gpu_04/model_identity.json',
 'new_confirm_gpu_04/attempts.jsonl','new_confirm_replay_04/completion.json','new_confirm_export_acceptance.json','new_confirm_prediction_export.json',
 'new_confirm_source_lock_04.json','new_confirm_input_acceptance_04.json','new_confirm_inference_registration_04.json',
 'new_confirm_gpu_budget_04.json','new_confirm_CPU_02/completion.json','new_confirm_CPU_registration_02.json','source_scope_02.json','new_confirm_source_registration_01.json','screen_01/selection_before_new_confirm.json']:
 files[name]=b/name
accepted=json.loads((b/'new_confirm_input_acceptance_04.json').read_text())
for row in accepted['sources']:
 for key in ['native_clock_path','reference_path']:
  p=pathlib.Path(row[key]);assert p.resolve().is_relative_to(b.resolve());files[str(p.relative_to(b))]=p
for row in accepted['proofs']:
 p=pathlib.Path(row['proof_path']);assert p.resolve().is_relative_to(b.resolve());files[str(p.relative_to(b))]=p
for p in (b/'new_confirm_gpu_04').glob('*/*.json'):files[str(p.relative_to(b))]=p
for p in (b/'new_confirm_replay_04').glob('*.json'):files[str(p.relative_to(b))]=p
name='sparse_confirm8_original_b_native64_20261013_v1'
r=pathlib.Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller')/(name+'.resource.json')
resource=json.loads(r.read_text());assert resource['status']=='completed' and resource['exit_code']==0
matching=[json.loads(x) for x in pathlib.Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip() and json.loads(x)['name']==name]
assert matching==[resource];assert hashlib.sha256(r.read_bytes()).hexdigest()==chain['resource_terminal_sha256']
files['resource.json']=r
payload={name:p.read_bytes() for name,p in files.items()}
payload['matching_gpu_ledger.json']=json.dumps(matching,indent=2).encode()
manifest={name:{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for name,raw in payload.items()}
stream=io.BytesIO()
with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
 for name,raw in payload.items():z.writestr(name,raw)
 z.writestr('manifest.json',json.dumps(manifest,indent=2))
raw=stream.getvalue()
sys.stderr.write(json.dumps({'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'members':len(manifest)}))
sys.stdout.buffer.write(raw)'''.replace('REMOTE',repr(REMOTE))
    result=subprocess.run(SSH+[PY+' -B -c '+shlex.quote(script)],capture_output=True,check=True)
    receipt=json.loads(result.stderr);raw=result.stdout
    if len(raw)!=receipt['bytes'] or hashlib.sha256(raw).hexdigest()!=receipt['sha256']:
        raise ValueError('Actual remote and Windows export bytes differ')
    archive=zipfile.ZipFile(io.BytesIO(raw));manifest=json.loads(archive.read('manifest.json'))
    if archive.testzip() is not None or len(archive.namelist())!=len(set(archive.namelist())) or set(archive.namelist())!=set(manifest)|{'manifest.json'}:
        raise ValueError('Export CRC/member set invalid')
    for name,item in manifest.items():
        target=out/name
        if not target.resolve().is_relative_to(out.resolve()):raise ValueError('Unsafe export path')
        data=archive.read(name)
        if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('Export member mismatch')
    out.mkdir()
    for name in manifest:
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(archive.read(name))
    with (REPORT/'new_confirm_evidence_export_05.zip').open('xb') as stream:stream.write(raw)
    acceptance=dict(status='PASS_WINDOWS_LINUX_BYTES_SHA_CRC_AND_ALL_COHORT_EXPORT_MEMBERS',
                    **receipt,manifest=manifest,new_model_calls=0,new_optimizer_updates=0)
    with (out/'transfer_acceptance.json').open('x',encoding='utf-8') as stream:json.dump(acceptance,stream,indent=2)
    print(json.dumps({k:v for k,v in acceptance.items() if k!='manifest'}))


if __name__=='__main__':main()
