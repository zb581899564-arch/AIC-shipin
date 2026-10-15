"""Receive the completed existing chain once; never start inference or CPU replay."""
import hashlib
import json
import shlex
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

from evaluate_candidates_v3 import REPORT, read, sha, save

REMOTE = r'''
from pathlib import Path
import datetime,hashlib,json,socket,sys,zipfile
b=Path('/home/inspur/aic_video_work/human_reference_iteration_20261013_v1')
run=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
name='human_summe20_original_b_native64_20261013_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2)
if socket.gethostname()!='inspur-NP5570M5':raise ValueError('Remote host differs')
for rel in ['human_chain_01/failure.json','human_gpu_01/failure.json','human_replay_01/failure.json']:
 if (b/rel).exists():
  print(json.dumps({'status':'EXISTING_CHAIN_FAILED_NO_TRANSFER_OR_RESTART','failure':rel,'detail':read(b/rel)}));sys.exit(3)
if not (b/'human_chain_01/completion.json').exists():
 print(json.dumps({'status':'PENDING_EXISTING_CHAIN_NO_TRANSFER_OR_RESTART'}));sys.exit(0)
files={rel:b/rel for rel in ['native_input_acceptance.json','developer_prediction_export.json',
 'developer_export_acceptance.json','human_chain_01/completion.json','human_gpu_01/completion.json',
 'human_replay_01/completion.json']}
resource_path=run/('controller/'+name+'.resource.json');resource=read(resource_path)
ledger=[json.loads(x) for x in Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
 if x.strip() and json.loads(x)['name']==name]
c=read(files['human_chain_01/completion.json']);g=read(files['human_gpu_01/completion.json'])
r=read(files['human_replay_01/completion.json']);e=read(files['developer_export_acceptance.json'])
a=read(files['native_input_acceptance.json'])
if (ledger!=[resource] or resource['status']!='completed' or resource['exit_code']!=0 or
 c['status']!='PASS_EXTERNAL_B_EXPORT_PENDING_LOCAL_HUMAN_QUALITY_COMPARISON' or
 g['status']!='PASS_COMPLETE_ORIGINAL_B_EXTERNAL_NATIVE64_CALLS_NOT_QUALITY' or
 r['status']!='PASS_ALL_HUMAN_EXTERNAL_B_INDEPENDENT_CPU_REPLAYS' or
 e['status']!='PASS_COMPLETE_B_EXPORT_AND_INDEPENDENT_CPU_REPLAY' or
 not g['actual_model_calls']==g['successful_windows']==r['windows']==a['accepted_windows']==116 or
 len(r['proofs'])!=116 or len({x['case_id'] for x in r['proofs']})!=116 or
 c['resource_terminal_sha256']!=sha(resource_path) or r['resource_terminal_sha256']!=sha(resource_path) or
 e['unique_resource_terminal_sha256']!=sha(resource_path) or
 c['developer_export_acceptance_sha256']!=sha(files['developer_export_acceptance.json']) or
 c['prediction_export_sha256']!=sha(files['developer_prediction_export.json']) or
 e['developer_prediction_export_sha256']!=sha(files['developer_prediction_export.json']) or
 e['independent_replay_completion_sha256']!=sha(files['human_replay_01/completion.json']) or
 e['native_input_acceptance_sha256']!=sha(files['native_input_acceptance.json']) or
 r['gpu_completion_sha256']!=sha(files['human_gpu_01/completion.json'])):
 raise ValueError('Complete actual export/CPU/unique resource/ledger lineage differs')
for proof in r['proofs']:
 if sha(Path(proof['proof_path']))!=proof['proof_sha256']:raise ValueError('Successful independent CPU proof changed')
out=b/'export_receipts_01';out.mkdir(exist_ok=True)
matching=out/'matching_gpu_ledger.json'
if not matching.exists():save(matching,ledger)
if read(matching)!=ledger:raise ValueError('Existing matching ledger receipt differs')
files.update({'resource.json':resource_path,'matching_gpu_ledger.json':matching})
audit=out/'terminal_audit.json'
if not audit.exists():save(audit,dict(status='PASS_COMPLETE_UNIQUE_GPU_AND_CPU_EXPORT_CHAIN',
 hostname=socket.gethostname(),gpu_name=name,actual_model_calls=116,CPU_replays=116,
 resource_sha256=sha(resource_path),charged_seconds=resource['charged_seconds'],
 new_model_calls=0,new_CPU_replays=0,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
if read(audit)['resource_sha256']!=sha(resource_path):raise ValueError('Existing terminal audit differs')
files['terminal_audit.json']=audit
manifest={rel:{'bytes':p.stat().st_size,'sha256':sha(p)} for rel,p in files.items()}
packed=out/'external_export_01.zip'
if not packed.exists():
 with zipfile.ZipFile(packed,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for rel,p in files.items():z.write(p,rel)
  z.writestr('_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(packed) as z:
 if z.testzip() is not None or set(z.namelist())!=set(manifest)|{'_MANIFEST.json'} or json.loads(z.read('_MANIFEST.json'))!=manifest:
  raise ValueError('Existing export receipt archive/CRC/manifest differs')
 for rel,v in manifest.items():
  raw=z.read(rel)
  if len(raw)!=v['bytes'] or hashlib.sha256(raw).hexdigest()!=v['sha256']:raise ValueError('Existing archived export differs')
print(json.dumps(dict(status='PASS_COMPLETED_EXPORT_RECEIPTS_READY',path=str(packed),
 bytes=packed.stat().st_size,sha256=sha(packed),manifest=manifest,new_model_calls=0,new_CPU_replays=0)))
'''


def main():
    destination = REPORT/'external_export_01'
    if (destination/'transfer_receipt.json').exists():
        raise FileExistsError('Completed export transfer already accepted; use its existing result')
    command = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
               '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=15', 'aic-inspur-home',
               'python3 -c '+shlex.quote(REMOTE)]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=55)
    if result.returncode:
        print(result.stdout, result.stderr, file=sys.stderr)
        raise RuntimeError('Existing chain failed or strict SSH/read-only terminal inspection failed')
    metadata = json.loads(result.stdout)
    if metadata['status'] == 'PENDING_EXISTING_CHAIN_NO_TRANSFER_OR_RESTART':
        print(json.dumps(metadata))
        return
    if metadata['status'] != 'PASS_COMPLETED_EXPORT_RECEIPTS_READY':
        raise ValueError('Remote export receipt is not accepted')
    archive = REPORT/'external_export_01.zip'
    if not archive.exists():
        partial = REPORT/'external_export_01.zip.part'
        subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
            '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=15',
            'aic-inspur-home:'+metadata['path'], str(partial)], check=True, timeout=55)
        if partial.stat().st_size != metadata['bytes'] or sha(partial) != metadata['sha256']:
            raise ValueError('Transferred export archive size/SHA differs from Linux')
        partial.rename(archive)
    if archive.stat().st_size != metadata['bytes'] or sha(archive) != metadata['sha256']:
        raise ValueError('Existing local export archive differs from Linux')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None or set(z.namelist()) != set(metadata['manifest'])|{'_MANIFEST.json'}:
            raise ValueError('Export receipt archive CRC/member set differs')
        if json.loads(z.read('_MANIFEST.json')) != metadata['manifest']:
            raise ValueError('Transferred internal manifest differs')
        for member, expected in metadata['manifest'].items():
            parts = PurePosixPath(member)
            if parts.is_absolute() or '..' in parts.parts or '\\' in member or ':' in member:
                raise ValueError('Unsafe export receipt member')
            raw = z.read(member)
            if len(raw) != expected['bytes'] or hashlib.sha256(raw).hexdigest() != expected['sha256']:
                raise ValueError('Transferred export member size/SHA differs')
            path = destination.joinpath(*parts.parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                if path.read_bytes() != raw:
                    raise ValueError('Existing extracted export member differs')
            else:
                with path.open('xb') as stream:
                    stream.write(raw)
    receipt = dict(metadata, status='PASS_WINDOWS_LINUX_BYTES_SHA_CRC_AND_ALL_EXPORT_MEMBER_SHA',
                   local_archive=str(archive.resolve()), new_model_calls=0, new_CPU_replays=0)
    save(destination/'transfer_receipt.json', receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='manifest'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
