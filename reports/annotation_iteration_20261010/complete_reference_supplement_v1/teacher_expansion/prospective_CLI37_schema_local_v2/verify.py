"""Necessary new transport/schema CPU checks; prior68/RGB/decoder exact referenced."""
from common import ROOT,BASE,read,sha,save,key,expected_core,scientific_core,bootstrap_metadata
from pathlib import Path
import ast,copy,json,hashlib,subprocess,io
from unittest.mock import patch
import observer,engine

OLD=BASE/'engineering_CLI36_37_split_fragment_v8v5'

def necessary_schema_cases(index):
 import common,launch
 w=index['windows'][0];a=ROOT/'call37';cases=[]
 good=dict(segments=[dict(decision='UNKNOWN',start_seconds=0,end_seconds=30,reason='MEMORY_ONLY',fact_support=[],start_uncertainty_range_seconds=[0,0],end_uncertainty_range_seconds=[30,30])],events=[],student_visibility='MEMORY_ONLY',limitations='MEMORY_ONLY')
 for name,doc,want in [('closed_proposal_memory_positive',good,True),('descriptive_proposal_without_decision_STOP',dict(segments=[dict(description='MEMORY_ONLY',start_seconds=0,end_seconds=30)],events=[],student_visibility='MEMORY_ONLY',limitations='MEMORY_ONLY'),False),('extra_proposal_field_STOP',dict(good,window_id='EXTRA'),False),('missing_proposal_support_STOP',dict(good,segments=[{k:v for k,v in good['segments'][0].items() if k!='fact_support'}]),False)]:
  with patch.object(common,'read',return_value=doc):d=observer.proposal_path_guard('MEMORY_ONLY',w)
  assert d['accepted']==want;cases.append(dict(name=name,accepted=d['accepted'],synthetic_memory_only=True))
 # A real-function observer simulation uses memory-only bytes and ownedpid;
 # neither synthetic output, stoprequest nor model is created on disk.
 def simulate(kind,scope_rejected=False,valid=False):
  target=Path(w['proposal_path']);bad=(json.dumps(dict(job_index=21,segments=[]))+'\n').encode();payload=(json.dumps(good)+'\n').encode() if scope_rejected or valid else bad
  tool=dict(step_index=2,step_type='tool',tool_name='write_to_file',tool_info=dict(parameters={'TargetFile':str(target)},output='written'))
  rows=[dict(step_update=dict(step_index=1,step_type='agent_response',state='DONE'))]+[dict(step_update=dict(tool,state=s)) for s in ('ACTIVE','DONE')]
  raw=b'\n'.join(json.dumps(x).encode() for x in rows)+b'\n';saved={};written={};oldread=Path.read_bytes;oldopen=Path.open;oldexists=Path.exists
  def fake_read(p):
   if key(p)==key(a/'index.json'):return index
   if key(p)==key(a/'process.json'):return dict(pid=987654)
   return read(p)
  def fake_bytes(p):
   if key(p)==key(a/'stream.jsonl'):return raw
   if key(p)==key(target):return payload
   return oldread(p)
  class Capture(io.BytesIO):
   def __init__(self,p):super().__init__();self.path=str(p)
   def __exit__(self,*args):written[self.path]=self.getvalue();self.close()
  def fake_open(p,*args,**kwargs):return Capture(p) if (args and args[0]=='xb') else oldopen(p,*args,**kwargs)
  def fake_exists(p):return False if ('immediate_proposal_schema' in p.name or p.name=='owned_stop_request.json') else oldexists(p)
  def fake_sha(p):return hashlib.sha256(fake_bytes(Path(p))).hexdigest() if key(p)==key(target) else hashlib.sha256(written[str(p)]).hexdigest() if str(p) in written else sha(p)
  with patch.object(observer,'read',side_effect=fake_read),patch.object(observer,'save',side_effect=lambda p,v:saved.update({str(p):v})),patch.object(observer,'sha',side_effect=fake_sha),patch.object(Path,'read_bytes',fake_bytes),patch.object(Path,'open',fake_open),patch.object(Path,'exists',fake_exists):
   if scope_rejected:
    result=dict(status='REJECT_ACTUAL_SCOPE_KEEP_RAW_NO_RETRY',immutable_prefix=dict(bytes=len(raw)))
    with patch.object(observer,'seal_scope',return_value=result) as sealed:observer.seal_observed_scopes(37);assert sealed.call_count==1
   else:
    with patch.object(common,'read',return_value=json.loads(payload)):observer.schema_scan(37)
  if valid:
   assert str(a/'owned_stop_request.json') not in saved and not written and saved[str(a/f"w{w['job_index']:02d}_immediate_proposal_schema.json")]['decision']['accepted'] is True
   cases.append(dict(name=kind,passed=True,synthetic_memory_only=True,on_disk_synthetic_outputs=0));return
  signal=saved[str(a/'owned_stop_request.json')];assert signal['owned_AGY_pid']==987654 and signal['reason']['accepted'] is False and signal['freeze_sha256']==sha(a/'freeze.json') and signal['observer_source_sha256']==sha(ROOT/'observer.py')
  assert written[str(a/'first_schema_or_raw_failure_prefix.jsonl')]==raw and written[str(a/'first_failed_proposal_original_bytes.json')]==payload
  assert signal['reason']['reason']==('ACTUAL_SCOPE_REJECT_REQUIRES_OWNED_STOP' if scope_rejected else 'ORIGINAL_CLOSED_PROPOSAL_SCHEMA_REJECTED')
  cases.append(dict(name=kind,passed=True,synthetic_memory_only=True,on_disk_synthetic_outputs=0))
 simulate('proposal_DONE_valid_schema_receipt_no_STOP',valid=True)
 simulate('proposal_DONE_bad_schema_preserves_raw_payload_owned_STOP')
 simulate('scope_REJECT_immediate_owned_STOP_not_seal_next_scope',True)
 cases.extend(recovery_cases())
 return cases

def recovery_cases():
 # No actual ROOT gate or acceptance is fabricated: only synthetic in-memory
 # documents exercise the launcher helper; actual required receipt stays pending.
 import launch
 cases=[]
 reference=dict(window_id=launch.W20_WINDOW,reference_kind=launch.W20_REFERENCE_KIND,source_sha256='SOURCE_MEMORY_SHA',training_admitted=False,consequential_unknowns=[dict(first=15,last=18,reason='MEMORY_ONLY')],unknown_global_exact=[['1','2']])
 source=dict(jobs=[dict(role='locked_evaluation',training_admitted=False,window=dict(window_id=launch.W20_WINDOW,source_sha256='SOURCE_MEMORY_SHA'))])
 binding=dict(path='MEMORY_REFERENCE',sha256='REFERENCE_MEMORY_SHA',window_id=launch.W20_WINDOW,reference_kind=launch.W20_REFERENCE_KIND,source_sha256='SOURCE_MEMORY_SHA',source_window=dict(path='MEMORY_SOURCEWINDOW',sha256='SOURCEWINDOW_MEMORY_SHA'),training_admitted=False)
 receipt=dict(status=launch.W20_STATUS,window_id=launch.W20_WINDOW,original_silver_contract_actual_verified=True,reference_binding=binding,training_admitted=False,**{'consequential15_18UNKNOWN_preserved':True})
 gate=dict(ROOT_w20_complete_independent_semantic_recovery_PASS=True,w20_semantic_recovery_receipt=dict(path='MEMORY_RECOVERY',sha256='RECOVERY_MEMORY_SHA',status=launch.W20_STATUS),w20_reference_binding=binding)
 def check(name,rec,ref,src,g,want):
  docs={'MEMORY_RECOVERY':rec,'MEMORY_REFERENCE':ref,'MEMORY_SOURCEWINDOW':src};hashes={'MEMORY_RECOVERY':'RECOVERY_MEMORY_SHA','MEMORY_REFERENCE':'REFERENCE_MEMORY_SHA','MEMORY_SOURCEWINDOW':'SOURCEWINDOW_MEMORY_SHA'}
  accepted=True
  try:
   with patch.object(launch,'read',side_effect=lambda p:docs[str(p)]),patch.object(launch,'sha',side_effect=lambda p:hashes[str(p)]):launch.verify_w20_recovery(g)
  except (AssertionError,KeyError):accepted=False
  assert accepted==want,(name,accepted);cases.append(dict(name=name,accepted=accepted,synthetic_memory_only=True))
 check('exact_ROOT20_reference_type_positive',receipt,reference,source,gate,True)
 for name,updates in [('STATIC_PASS_STOP',dict(status='PASS_STATIC')),('media_only_PASS_STOP',dict(status='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC')),('wrong_window_STOP',dict(window_id='WRONG')),('silver_false_STOP',dict(original_silver_contract_actual_verified=False)),('training_true_STOP',dict(training_admitted=True)),('UNKNOWN_not_preserved_STOP',{'consequential15_18UNKNOWN_preserved':False})]:check(name,dict(receipt,**updates),reference,source,gate,False)
 for name,updates in [('reference_window_STOP',dict(window_id='WRONG')),('reference_kind_STOP',dict(reference_kind='GOLD')),('reference_training_STOP',dict(training_admitted=True)),('reference_source_SHA_STOP',dict(source_sha256='WRONG')),('missing_consequential_UNKNOWN_STOP',dict(consequential_unknowns=[]))]:check(name,receipt,dict(reference,**updates),source,gate,False)
 gb=copy.deepcopy(gate);gb['w20_reference_binding']['sha256']='WRONG';check('gate_reference_binding_mismatch_STOP',receipt,reference,source,gb,False)
 badsource=copy.deepcopy(source);badsource['jobs'][0]['window']['window_id']='WRONG';check('source_window_identity_STOP',receipt,reference,badsource,gate,False)
 badsource=copy.deepcopy(source);badsource['jobs'][0]['role']='train';check('source_window_role_STOP',receipt,reference,badsource,gate,False)
 for name,field in [('actual_reference_SHA_mismatch_STOP','sha256'),('actual_sourceplan_SHA_mismatch_STOP','source_window')]:
  badreceipt=copy.deepcopy(receipt);badgate=copy.deepcopy(gate)
  if field=='sha256':badreceipt['reference_binding']['sha256']='WRONG'
  else:badreceipt['reference_binding']['source_window']['sha256']='WRONG'
  badgate['w20_reference_binding']=copy.deepcopy(badreceipt['reference_binding']);check(name,badreceipt,reference,source,badgate,False)
 return cases

def main():
 binding=read(ROOT/'execution_code_binding.json');assert len(list(ROOT.glob('*.py')))==10
 for p,h in binding['sources'].items():assert sha(p)==h;ast.parse(Path(p).read_text(encoding='utf-8')) if p.endswith('.py') else None
 for p,h in binding['actual_prior_bindings'].items():assert sha(p)==h
 a=ROOT/'call37';idx=read(a/'index.json');fr=read(a/'freeze.json');literal=read(a/'literal_execution_parameters.json');assert [w['job_index'] for w in idx['windows']]==[21,22,23] and fr['automatic_retry'] is False
 for p,h in fr['inputs'].items():assert sha(p)==h,(p,'SHA_DRIFT')
 oldidx=read(OLD/'call37/index.json');oldliteral=read(OLD/'call37/literal_execution_parameters.json')
 for ow,w,l,ol in zip(oldidx['windows'],idx['windows'],literal,oldliteral):
  projected=copy.deepcopy(ow)
  for g in projected['groups']:g['output_path']=g['output_path'].replace(str(OLD/'call37'),str(a))
  projected['proposal_path']=projected['proposal_path'].replace(str(OLD/'call37'),str(a))
  for name in ('header_fragment_id','native_fragment_ids'):projected.pop(name,None)
  assert projected=={k:v for k,v in w.items() if k not in ('header_fragment_id','native_fragment_ids','proposal_fragment_id','proposal_template_path')}
  for g,lg in zip(w['groups'],l['native_groups']):assert lg['view_file']==[dict(AbsolutePath=f['path']) for f in g['frames']] and lg['write_to_file']==dict(TargetFile=g['output_path'])
  assert l['clip_view_file']==ol['clip_view_file'] and l['effective_preview_batches']==ol['effective_preview_batches']
  assert l['proposal_write_to_file']==dict(TargetFile=w['proposal_path'])
 from prompt import scientific_text,piece,main_body,header_body,native_body,proposal_body,proposal_example
 science=scientific_text((BASE/'engineering_alias_remainder_v3/call35/frozen_prompt.txt').read_text(encoding='utf-8'));assert science==scientific_text((BASE/'engineering_alias_remainder_v3/call36/frozen_prompt.txt').read_text(encoding='utf-8'))
 # No previous68 rerun: unchanged actual audit guards and scientific parser helpers.
 oldengine=(OLD/'engine.py').read_text(encoding='utf-8');newengine=(ROOT/'engine.py').read_text(encoding='utf-8');assert oldengine.replace('count=100;local_complete=',"count=index['core_per_window'];local_complete=")==newengine
 oldcommon=(OLD/'common.py').read_text(encoding='utf-8');newcommon=(ROOT/'common.py').read_text(encoding='utf-8')
 guard_reuse={}
 for name in ('bootstrap_metadata','fact_items','proposal_schema','scientific_core'):
  oldf=next(x for x in ast.parse(oldcommon).body if isinstance(x,ast.FunctionDef) and x.name==name);newf=next(x for x in ast.parse(newcommon).body if isinstance(x,ast.FunctionDef) and x.name==name);ob=ast.get_source_segment(oldcommon,oldf);nb=ast.get_source_segment(newcommon,newf);assert ob==nb;guard_reuse[name]=hashlib.sha256(nb.encode()).hexdigest()
 parts=idx['text_fragments'];headers=[p for p in parts if p['kind']=='header'];short=(a/'short_prompt.txt').read_text(encoding='utf-8');white={key(p) for p in fr['read_whitelist']+fr['self_read_whitelist']};checks=[]
 for p in parts:
  w=next((w for w in idx['windows'] if w['job_index']==p['job_index']),None);l=next((l for l in literal if l['job_index']==p['job_index']),None);ack=read(p['expected_ACK_path'])
  body=main_body(science,headers,37,[21,22,23]) if w is None else header_body(w,[q for q in parts if q['job_index']==w['job_index'] and q['kind']=='native_index'],l) if p['kind']=='header' else proposal_body(w) if p['kind']=='proposal_schema' else native_body(w,p['before_group'],l)
  b=Path(p['path']).read_bytes();assert b==piece(body,ack,p['ack_path']).encode() and len(b)<30000 and len(b.splitlines())<=450 and max(map(len,b.decode().splitlines()))<=1000 and bootstrap_metadata(b,f'{len(b)} bytes, {len(b.split(bytes([10])))} lines')
  assert ack['marker'] not in short and ack['marker'] not in (a/'index.json').read_text(encoding='utf-8') and key(p['expected_ACK_path']) not in white
  if p['kind']=='native_index':assert '禁止输出裸数组' in body and '每条且仅有slot/subject/composition/subtitle_visible/subtitle_text/visible_fact' in body
  if p['kind']=='proposal_schema':assert 'Qwen3-VL-8B' in body and '绝不指学校学生' in body and set(proposal_example())=={'segments','events','student_visibility','limitations'}
  checks.append(dict(part_id=p['part_id'],bytes=len(b),sha256=sha(p['path']),full_body_regeneration_exact=True,clarification_only_no_actual_labels=True))
 assert len(parts)==19 and len(expected_core(idx))==308 and len(scientific_core(idx))==270 and [len(expected_core(idx,w['job_index'])) for w in idx['windows']]==[104,206,308]
 # Three inserted template read+ACK pairs are exactly after8effective andbeforeproposal.
 for w in idx['windows']:
  seq=expected_core(idx,w['job_index']);part=next(p for p in parts if p['part_id']==w['proposal_fragment_id']);assert seq[-4:]==[('view_file',key(w['student_previews'][-1]['path'])),('view_file',key(part['path'])),('write_to_file',key(part['ack_path'])),('write_to_file',key(w['proposal_path']))]
 assert not any(Path(p).exists() for p in fr['write_whitelist']) and not(a/'request.json').exists() and not(ROOT/'root_start_admission.json').exists()
 from launch import command
 units=len(subprocess.list2cmdline(command(37,short)).encode('utf-16-le'))//2+1;assert units<1024
 cases=necessary_schema_cases(idx)
 save(ROOT/'independent_CPU_negative_acceptance.json',dict(status='PASS_ONLY_NECESSARY_NEW_TEXT_SCHEMA_OBSERVER_CPU_NO_MODEL_PENDING_ROOT20_AND_GATE',source_binding_sha256=sha(ROOT/'execution_code_binding.json'),new_cases=cases,parts=checks,guard_helpers_byte_exact_reused=guard_reuse,old68_CPU_receipt_path=str(OLD/'independent_CPU_negative_acceptance.json'),old68_CPU_receipt_sha256=sha(OLD/'independent_CPU_negative_acceptance.json'),old68_repeated=False,prior_v1_7case_receipt_path=str(BASE/'prospective_CLI37_schema_local_v1/independent_CPU_negative_acceptance.json'),prior_v1_7case_receipt_sha256=sha(BASE/'prospective_CLI37_schema_local_v1/independent_CPU_negative_acceptance.json'),prior_v1_7case_repeated=False,new_PNG_decode=0,new_video_decode=0,new_model_calls=0,core=308,scope_cores=[104,206,308],argv_units=units))
 print(json.dumps(dict(receipt_sha256=sha(ROOT/'independent_CPU_negative_acceptance.json'),new_cases=len(cases),parts=len(parts),max_text_bytes=max(p['bytes'] for p in checks),core=308,argv_units=units)))
if __name__=='__main__':main()
