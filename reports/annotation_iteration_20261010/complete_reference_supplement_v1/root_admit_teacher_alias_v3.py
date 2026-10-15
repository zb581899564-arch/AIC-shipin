from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,ast,struct
BASE=Path(__file__).parent
D=BASE/'teacher_expansion/engineering_alias_remainder_v3'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(p):return str(Path(p)).replace('\\','/').lower()
assert not(D/'root_start_admission.json').exists()
e=read(D/'execution_code_binding.json')
for p,s in {**e['sources'],**e['prior_failure_and_transfer_inputs']}.items():assert sha(p)==s,p
sources=list(D.glob('*.py'));assert len(sources)==9
for p in sources:ast.parse(p.read_text(encoding='utf-8-sig'))
a=read(D/'alias_original_payload_binding.json');assert len(a['rows'])==479
assert sum(r['payload_bytes'] for r in a['rows'])==90040493
for r in a['rows']:
 assert Path(r['alias_path']).read_bytes()==Path(r['original_path']).read_bytes()
 assert sha(r['alias_path'])==(r.get('png_sha256') or r['payload_sha256'])
 if r['kind']!='clip':
  blob=Path(r['alias_path']).read_bytes();assert blob[:8]==b'\x89PNG\r\n\x1a\n'
  assert list(struct.unpack('>II',blob[16:24]))==r['geometry']
original={}
for n in (7,8,9,10):
 p=BASE/f'teacher_expansion/capacity_v4_tool_batches/call{n:02d}/index.json'
 assert p.read_bytes()==(D/f'original_indices/call{n:02d}.json').read_bytes()
 for w in read(p)['windows']:original[w['job_index']]=w
proof=read(D/'prior17/actual_prior32_native_facts_provenance.json')
pkg=read(D/'prior17/prior32_facts.json');pb=(D/'prior17/prior32_facts.json').read_bytes()
prefix=Path(proof['immutable_prior32_prefix']['path']).read_bytes()
oldraw=Path(proof['original_CLI33_raw']['path']).read_bytes()
assert oldraw.startswith(prefix) and sha(proof['immutable_prior32_prefix']['path'])==proof['immutable_prior32_prefix']['sha256']
updates=[r['step_update'] for r in map(json.loads,prefix.splitlines()) if r.get('step_update',{}).get('step_type')=='tool']
latest={t['step_index']:t for t in updates}
assert not any(t.get('state') in ('ACTIVE','ERROR') for t in latest.values())
wanted=[];wantedset=set()
for group in proof['groups']:
 assert group['group'] in range(8)
 fpath=group['facts']['path'];blob=Path(fpath).read_bytes()
 assert sha(fpath)==group['facts']['sha256'] and pb.count(blob)==1
 assert pkg['groups'][group['group']]==read(fpath)
 for r in group['native_reads']:
  p=r['identity']['path'];wanted.append(('view_file',key(p)));wantedset.add(key(p))
  assert sha(p)==r['identity']['png_sha256']
 wanted.append(('write_to_file',key(fpath)));wantedset.add(key(fpath))
got=[]
for t in latest.values():
 pp=t.get('tool_info',{}).get('parameters',{});p=key(pp.get('AbsolutePath') or pp.get('TargetFile') or '')
 if p in wantedset:got.append((t['tool_name'],p))
assert got==wanted and len(got)==40
assert proof['old_F35_actual_DONE_steps']==[193] and proof['old_group8_not_successful']
calls=[]
for n,jobs in ((34,[17,18]),(35,[19,20]),(36,[21,22,23])):
 c=D/f'call{n}';f=read(c/'freeze.json');ix=read(c/'index.json');lit=read(c/'literal_execution_parameters.json')
 assert not(c/'request.json').exists()
 assert [w['job_index'] for w in ix['windows']]==jobs
 assert f['CLI_after']==n and f['timeout_seconds']==7200
 for p,s in f['inputs'].items():assert sha(p)==s,p
 assert all(not Path(p).exists() for p in f['write_whitelist'])
 for w,l in zip(ix['windows'],lit):
  ow=original[w['job_index']];ofs=[f for g in ow['groups'] for f in g['frames']]
  assert len(ofs)==64 and len(w['native_identity_all64'])==64
  for nf,of in zip(w['native_identity_all64'],ofs):
   assert nf['original_path']==of['path']
   assert all(nf[k]==of[k] for k in ('frame_id','source_ordinal','global_seconds_exact','local_seconds_exact','geometry','png_sha256','rgb_pixel_sha256'))
  assert [x['AbsolutePath'] for g in l['native_groups'] for x in g['view_file']]==[x['path'] for g in w['groups'] for x in g['frames']]
  assert [x['AbsolutePath'] for batch in l['effective_preview_batches'] for x in batch]==[f['path'] for f in w['student_previews']]
  assert [f['original_path'] for f in w['student_previews']]==[f['path'] for f in ow['student_previews']]
  assert sha(w['clip_path'])==sha(ow['clip_path'])
  assert sha(w['original_student_receipt']['path'])==w['original_student_receipt']['sha256']
  assert sha(w['original_source_manifest']['path'])==w['original_source_manifest']['sha256']
  assert sha(w['original_source_manifest']['native_clock']['path'])==w['original_source_manifest']['native_clock']['sha256']
 calls.append(dict(CLI=n,jobs=jobs,input_count=len(f['inputs']),freeze_sha256=sha(c/'freeze.json')))
ledger=read(D/'plan.json')
global_rows=[json.loads(s) for s in (BASE/'teacher_expansion/global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
assert max(r['global_count'] for r in global_rows)==33
assert ledger['global_cap']==36
out=dict(utc=datetime.now(timezone.utc).isoformat(),status='ROOT_APPROVED_START_ALIAS_V3_FIXED_CLI34_36',dry_run_sha256=sha(D/'dry_run_acceptance.json'),execution_binding_sha256=sha(D/'execution_code_binding.json'),root_verifier_source_sha256=sha(__file__),root_read_protocol_controller_launch_audit_observer_prepare_verify_prompt=True,root_all479_byte_exact_aliases_and_original64_identities_verified=True,root_actual_old32_prefix40_tool_sequence_and_rawfacts_verified=True,old_CLI33_failure_cost_preserved=True,prior_F35_DONE_without_fact_reprovide_is_plan_exception_not_future_actual_evidence=True,calls=calls,global_CLI_before=33,global_cap=36,automatic_retry=False,new_model_calls_at_gate=0,semantic_admission=False,training_admitted=False)
with (D/'root_start_admission.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(status=out['status'],sha256=sha(D/'root_start_admission.json'),calls=calls),ensure_ascii=False))

