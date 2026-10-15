"""Independent no-model verification of the prepared fixed future plan."""
from pathlib import Path
from datetime import datetime, timezone
from importlib.util import spec_from_file_location,module_from_spec
import ast,json,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE/'remaining_CLI33_36_same_index_selfcheck_v2';OLD=BASE/'capacity_v4_tool_batches';PRIOR=BASE/'remaining_CLI32_36_literal_paths_v1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,p):
 s=spec_from_file_location(name,p);m=module_from_spec(s);s.loader.exec_module(m);return m
binding=read(ROOT/'execution_code_binding.json')
for p,s in {**binding['sources'],**binding['prior_failure_inputs']}.items():assert sha(p)==s
AST=[]
for p in ROOT.glob('*.py'):
 ast.parse(p.read_text(encoding='utf-8-sig'));AST.append(dict(path=str(p),sha256=sha(p)))
assert len(AST)==9
policy=load('verify_selfcheck_policy',ROOT/'supply_policy.py');prompt=load('verify_selfcheck_prompt',ROOT/'prompt.py')
def tool(i,name,p):return dict(step_index=i,tool_name=name,tool_info=dict(parameters={('AbsolutePath' if name=='view_file' else 'TargetFile'):str(p)}))
calls=[]
for n in range(7,11):
 a=ROOT/f'call{n:02d}';old=OLD/f'call{n:02d}';fr=read(a/'freeze.json');idx=read(a/'index.json')
 assert sha(a/'index.json')==sha(old/'index.json')==sha(PRIOR/f'call{n:02d}/index.json')
 assert fr['CLI_before']==25+n and fr['CLI_after']==26+n and fr['timeout_seconds']==7200
 assert fr['fixed_job_indices']==[2*n+2,2*n+3] and fr['global_cap']==36
 assert not (a/'request.json').exists() and not (a/'terminal.json').exists() and not (ROOT/'root_start_admission.json').exists()
 assert all(not Path(p).exists() for p in fr['write_whitelist'])
 for p,s in fr['inputs'].items():assert sha(p)==s,(p,'INPUT_SHA_DRIFT')
 text,literals=prompt.build_prompt(a);assert text==(a/'frozen_prompt.txt').read_text(encoding='utf-8')
 assert '建议整会话总读取≤5次' in text and '不是媒体准入次数门' in text
 expected=[('view_file',str(a/'index.json'))]
 for w,l in zip(idx['windows'],literals):
  assert len(w['groups'])==16 and sum(len(g['frames']) for g in w['groups'])==64
  assert len(w['student_previews'])==8 and [x['AbsolutePath'] for x in l['ordered_view_file_arguments']]==[f['path'] for f in w['student_previews']]
  for g in w['groups']:
   assert len(g['frames'])==4
   expected.extend(('view_file',f['path']) for f in g['frames']);expected.append(('write_to_file',g['output_path']))
  expected.append(('view_file',w['clip_path']));expected.extend(('view_file',f['path']) for f in w['student_previews']);expected.append(('write_to_file',w['proposal_path']))
 assert len(expected)==181
 synthetic=[tool(i,name,p) for i,(name,p) in enumerate(expected)]
 synthetic[90:90]=[tool(1000+i,'view_file',a/'index.json') for i in range(10)]
 filtered,checks=policy.index_selfchecks(synthetic,a/'index.json')
 assert checks['DONE_read_count']==11 and not checks['hard_count_limit']
 def pairs(ts):
  return [(t['tool_name'],str(Path(t['tool_info']['parameters'].get('AbsolutePath') or t['tool_info']['parameters'].get('TargetFile')))) for t in ts]
 assert pairs(filtered)==expected
 repeat=filtered+[tool(9999,'view_file',idx['windows'][0]['groups'][0]['frames'][0]['path'])]
 assert pairs(policy.index_selfchecks(repeat,a/'index.json')[0])!=expected
 outside=filtered+[tool(9998,'view_file',a/'other_index.json')]
 assert pairs(policy.index_selfchecks(outside,a/'index.json')[0])!=expected
 calls.append(dict(call=n,jobs=fr['fixed_job_indices'],CLI_after=fr['CLI_after'],input_count=len(fr['inputs']),index_sha256=sha(a/'index.json'),freeze_sha256=sha(a/'freeze.json'),prompt_sha256=sha(a/'frozen_prompt.txt'),literal_preview_arguments_sha256=sha(a/'literal_preview_arguments.json'),all_inputs_SHA_verified=True,synthetic_index11_does_not_change181_core=True,duplicate_media_and_other_path_retained_for_rejection=True))
assert sha(PRIOR/'call06/terminal.json')=='9ccbffb7815f96caf5060710fd4d1aff09742ecfafc895f75e7183bece822f11'
assert sha(PRIOR/'call06/stream.jsonl')=='77153ff662b93c550fe0933de9472e5af5bd44e03208a9e9fc21bb9cc3495a7a'
assert sha(PRIOR/'call06/audit.json')=='8f7f6c1907d38e77407896d3292b7389a2e87804c14edb9411b3b65831983298'
assert max(json.loads(s)['global_count'] for s in (BASE/'global_CLI_ledger.jsonl').read_text(encoding='utf-8').splitlines() if s.strip())==32
out=dict(utc=datetime.now(timezone.utc).isoformat(),status='PASS_INDEPENDENT_PREPARATION_ONLY_PENDING_ROOT_START',verifier_source_sha256=sha(Path(__file__)),AST=AST,calls=calls,execution_binding_sha256=sha(ROOT/'execution_code_binding.json'),dry_run_sha256=sha(ROOT/'dry_run_acceptance.json'),global_actual_CLI=32,new_model_calls=0,new_decoder=0,new_optimizer=0,original32_strict_failure_unchanged=True,unexecuted_draft_r0_preserved='Prior preparation draft preserved without launch; current reviewed version only at exact v2 root',root_start_gate_absent=True)
p=ROOT/'independent_preparation_acceptance.json'
with p.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(receipt=str(p),sha256=sha(p),protocol_sha256=sha(ROOT/'PROTOCOL.md'),AST_count=len(AST),calls=calls,global_CLI=32,new_model_calls=0),ensure_ascii=False))
