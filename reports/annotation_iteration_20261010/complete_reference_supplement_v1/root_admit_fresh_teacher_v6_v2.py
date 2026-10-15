"""ROOT reviewed immutable inputs; only unused teacher calls, no training admission."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,ast,sys,copy
from PIL import Image
R=Path(__file__).parent
V=R/'teacher_expansion/engineering_alias_remainder_v6_fresh_scope_prefix_v2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
 with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
binding=read(V/'execution_code_binding.json')
for k in ('sources','actual_prior_bindings'):
 for p,h in binding[k].items():assert sha(p)==h,p
for p in V.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
neg=read(V/'independent_CPU_negative_acceptance.json')
assert len(neg['negative_cases'])==32 and all(c['synthetic_memory_only'] for c in neg['negative_cases'])
assert neg['sources']==binding['sources']
assert (V.parent/'global_CLI_ledger.jsonl').read_bytes()==(V/'actual_global34_ledger_prefix.jsonl').read_bytes()
assert max(readrow['global_count'] for readrow in map(json.loads,(V.parent/'global_CLI_ledger.jsonl').read_text().splitlines()))==34
assert not list(V.parent.glob('*/call35/request.json')) and not list(V.parent.glob('*/call36/request.json'))
sys.path.insert(0,str(V))
from common import expected_core
from launch import command
import subprocess
pixels=0;checks=[]
for n,jobs in ((35,[19,20]),(36,[21,22,23])):
 a=V/f'call{n}';fr=read(a/'freeze.json');idx=read(a/'index.json')
 assert fr['fixed_job_indices']==jobs and fr['global_cap']==36 and fr['timeout_seconds']==7200 and not fr['automatic_retry']
 for p,h in fr['inputs'].items():assert sha(p)==h,p
 assert not any(Path(p).exists() for p in fr['write_whitelist'])
 old=read(V.parent/f'engineering_alias_remainder_v4_bootstrap_file/call{n}/index.json')
 for ow,w in zip(old['windows'],idx['windows']):
  projection=copy.deepcopy(ow)
  for g in projection['groups']:g['output_path']=g['output_path'].replace(str(V.parent/f'engineering_alias_remainder_v4_bootstrap_file/call{n}'),str(a))
  projection['proposal_path']=projection['proposal_path'].replace(str(V.parent/f'engineering_alias_remainder_v4_bootstrap_file/call{n}'),str(a))
  assert projection==w
  assert len(w['native_identity_all64'])==64 and len(w['groups'])==16 and len(w['student_previews'])==8
  for f in [f for g in w['groups'] for f in g['frames']]+w['student_previews']:
   assert Path(f['path']).read_bytes()==Path(f['original_path']).read_bytes()
   assert sha(f['path'])==f['png_sha256']
   with Image.open(f['path']) as im:
    assert list(im.size)==f['geometry']
    assert hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()==f['rgb_pixel_sha256']
   pixels+=1
  assert Path(w['clip_path']).read_bytes()==Path(w['original_clip_path']).read_bytes()
 body=Path(idx['bootstrap_instruction_path']).read_bytes()
 assert body.endswith(b'\n') and b'\r' not in body
 ack=read(idx['bootstrap_ack_expected_path']);short=(a/'short_prompt.txt').read_text()
 assert ack['marker'] not in short and ack['marker'] not in (a/'index.json').read_text(encoding='utf-8')
 assert body.decode('utf-8').rstrip().endswith(ack['marker'])
 assert len(expected_core(idx))==(183 if n==35 else 273)
 units=len(subprocess.list2cmdline(command(n,short)).encode('utf-16-le'))//2+1
 assert units<1024
 checks.append(dict(CLI=n,jobs=jobs,inputs=len(fr['inputs']),bootstrap_exact_LF_lines=len(body.split(b'\n')),argv_UTF16_units=units,freeze_sha256=sha(a/'freeze.json')))
gate=dict(status='ROOT_APPROVED_START_FRESH_SCOPE_V6_FIXED_CLI35_36',utc=datetime.now(timezone.utc).isoformat(),dry_run_sha256=sha(V/'dry_run_acceptance.json'),execution_binding_sha256=sha(V/'execution_code_binding.json'),negative_receipt_sha256=sha(V/'independent_CPU_negative_acceptance.json'),root_verifier_sha256=sha(__file__),actual_pixel_checks=pixels,calls=checks,scope_semantics_and_training_not_admitted=True,old34_FAILURE_preserved=True,no34_retry_no37=True,quality_protocol_unchanged=True,source_transfer_not_authorized_by_gate=True)
save(V/'root_start_admission.json',gate)
print(json.dumps(dict(path=str(V/'root_start_admission.json'),sha256=sha(V/'root_start_admission.json'),pixel_checks=pixels,calls=checks),ensure_ascii=False))

