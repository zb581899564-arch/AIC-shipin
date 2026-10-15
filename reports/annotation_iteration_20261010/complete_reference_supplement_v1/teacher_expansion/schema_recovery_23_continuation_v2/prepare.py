"""Project unused old40 into a fresh typed39-recovery route; never launch."""
from common import ROOT,BASE,read,sha,save,expected_core,scientific_core
from pathlib import Path
import ast,copy,json,uuid,subprocess
OLD=BASE/'schema_recovery_22_23_v1'

def put(p,b):
 with Path(p).open('xb') as f:f.write(b)

def project(v,old,new):
 if isinstance(v,str):return v.replace(str(old),str(new))
 if isinstance(v,list):return [project(x,old,new) for x in v]
 if isinstance(v,dict):return {k:project(x,old,new) for k,x in v.items()}
 return v

def main():
 assert not(ROOT/'plan.json').exists() and not any(BASE.rglob('call40/request.json'))
 old=OLD/'call40';oldfr=read(old/'freeze.json');oldidx=read(old/'index.json');oldliteral=read(old/'literal_execution_parameters.json')
 for p,h in oldfr['inputs'].items():assert sha(p)==h
 assert not(old/'request.json').exists()
 recovery=BASE.parent/'schema_recovery_CLI39_final_selfread_root_recovery_v1.json';confirmed=read(recovery)
 from launch import RECOVERY39_STATUS,previous39_documents_guard,command
 previous=OLD/'call39';w39=read(previous/'index.json')['windows'][0]
 previous39_documents_guard(read(previous/'terminal.json'),read(previous/'audit.json'),read(previous/'w22_completed_scope_audit.json'),confirmed,w39['window_id'],w39['proposal_path'])
 assert confirmed['status']==RECOVERY39_STATUS and sha(recovery)=='bf991024d851317d0d4dc7784622119d4e5478ed276c88b3d1e7e0d43fba684c'
 ledger=BASE/'global_CLI_ledger.jsonl';rows=[json.loads(x) for x in ledger.read_text(encoding='utf-8').splitlines()];assert max(x['global_count'] for x in rows)==39
 terms=[x for x in rows if x['global_count']==39 and x['event']=='TERMINAL'];assert len(terms)==1 and terms[0]['raw_sha256']==sha(previous/'stream.jsonl') and terms[0]['terminal_sha256']==sha(previous/'terminal.json')
 put(ROOT/'actual_global39_ledger_prefix.jsonl',ledger.read_bytes())
 prior=[recovery,Path(confirmed['independent_actual_scope_review']['path']),Path(confirmed['lawful_observation_binding']['path']),ROOT/'actual_global39_ledger_prefix.jsonl',*(previous/n for n in ('freeze.json','index.json','request.json','terminal.json','stream.jsonl','audit.json','actual_terminal_cost.json','w22_completed_scope_audit.json','stopped.json')),
        *(OLD/n for n in ('execution_code_binding.json','dry_run_acceptance.json','independent_CPU_negative_acceptance.json')),
        *(old/n for n in ('freeze.json','index.json','literal_execution_parameters.json','science_verbatim_program_only.txt'))]
 for b in (confirmed['independent_actual_scope_review'],confirmed['lawful_observation_binding']):assert sha(b['path'])==b['sha256']
 auth=BASE.parent/'schema_recovery_22_23_user_authorization_v1.json';prior.append(auth)
 bindings={str(p):sha(p) for p in prior}
 sources={str(p):sha(p) for p in list(ROOT.glob('*.py'))+[ROOT/'PROTOCOL.md']};assert len(list(ROOT.glob('*.py')))==10
 save(ROOT/'execution_code_binding.json',dict(sources=sources,actual_prior_bindings=bindings,user_authorization_sha256=sha(auth),previous39_recovery_sha256=sha(recovery),old39_whole_REJECT_preserved=True,old40_unused_preserved=True,new_model_calls=0))
 from prompt import piece,main_body,header_body,native_body,proposal_body
 a=ROOT/'call40';a.mkdir();(a/'text').mkdir();idx=project(copy.deepcopy(oldidx),old,a);w=idx['windows'][0];literal=project(copy.deepcopy(oldliteral),old,a);l=literal[0];parts=idx['text_fragments']
 science=(old/'science_verbatim_program_only.txt').read_bytes();headers=[p for p in parts if p['kind']=='header']
 for p in parts:
  body=main_body(science.decode(),headers,40,[23]) if p['kind']=='main' else header_body(w,[q for q in parts if q['kind']=='native_index'],l) if p['kind']=='header' else proposal_body(w) if p['kind']=='proposal_schema' else native_body(w,p['before_group'],l)
  ack=project(read(next(q for q in oldidx['text_fragments'] if q['part_id']==p['part_id'])['expected_ACK_path']),old,a);ack['marker']='CONT40_'+uuid.uuid4().hex
  payload=piece(body,ack,p['ack_path']).encode();assert len(payload)<30000 and payload.endswith(b'\n') and b'\r' not in payload and len(payload.splitlines())<=450 and max(map(len,payload.decode().splitlines()))<=1000
  save(p['expected_ACK_path'],ack);put(p['path'],payload);p.update(input_sha256=sha(p['path']),payload_bytes=len(payload),exact_Go_LF_lines=len(payload.split(b'\n')),Python_splitlines=len(payload.splitlines()),max_line_characters=max(map(len,payload.decode().splitlines())),expected_ACK_sha256=sha(p['expected_ACK_path']))
 assert len(parts)==19 and len(expected_core(idx))==128 and len(scientific_core(idx))==90
 save(a/'index.json',idx);save(a/'literal_execution_parameters.json',literal);put(a/'science_verbatim_program_only.txt',science)
 for n in ('original_v3_prompt35.txt','original_v3_prompt36.txt','prepared_original_pixel_clock_checks.json'):put(a/n,(old/n).read_bytes())
 save(a/'scientific_text_map.json',project(read(old/'scientific_text_map.json'),old,a))
 short=f"First view_file the ENTIRE file at AbsolutePath {idx['main_instruction_path']} once, no range. Follow its full single-window instructions; immediately write every text tail ACK. Only view_file/write_to_file. After final proposal write DONE naturally finish compact JSON, no more tools; never view proposal. Any ERROR/schema failure STOP, no retry."
 put(a/'short_prompt.txt',short.encode())
 fr=project(copy.deepcopy(oldfr),old,a);fr['self_read_whitelist']=[g['output_path'] for g in w['groups']]
 fr['inputs']=dict(oldfr['inputs']);fr['inputs'].update(bindings);fr['inputs'].update(sources);fr['inputs'][str(ROOT/'execution_code_binding.json')]=sha(ROOT/'execution_code_binding.json')
 for p in a.rglob('*'):
  if p.is_file():fr['inputs'][str(p)]=sha(p)
 fr.update(protocol_sha256=sha(ROOT/'PROTOCOL.md'),source_binding_sha256=sha(ROOT/'execution_code_binding.json'),previous39_recovery=dict(path=str(recovery),sha256=sha(recovery),status=RECOVERY39_STATUS),new_ROOT_gate_per_call_required=True,proposal_selfread_forbidden=True,fact_selfreads_only_before_final_proposal=True)
 assert not any(Path(p).exists() for p in fr['write_whitelist']);save(a/'freeze.json',fr)
 units=len(subprocess.list2cmdline(command(40,short)).encode('utf-16-le'))//2+1;assert units<1024
 for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
 route=dict(CLI=40,job=23,scope_core128=len(expected_core(idx)),window_core126=idx['core_per_window'],science90=len(scientific_core(idx)),parts19=len(parts),max_bytes=max(p['payload_bytes'] for p in parts),argv_units=units)
 save(ROOT/'plan.json',dict(status='PREPARED_FRESH_CLI40_JOB23_TYPED39_RECOVERY_NO_START',routes=[route],global_cap=40,no41=True,automatic_retry=False,timeout_seconds_each=3600,new_model_calls=0))
 save(ROOT/'dry_run_acceptance.json',dict(status='PASS_TYPED39_RECOVERY_SINGLE40_PATH_TEXT_AST_SHA_NO_MODEL_PENDING_ROOT',source_binding_sha256=sha(ROOT/'execution_code_binding.json'),routes=[route],freeze=dict(path=str(a/'freeze.json'),sha256=sha(a/'freeze.json'),inputs=len(fr['inputs'])),AST=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in ROOT.glob('*.py')],new_model_calls=0,new_decoder_calls=0,new_processor_calls=0,old51_24_68_repeated=False))
 print(json.dumps(dict(binding_sha256=sha(ROOT/'execution_code_binding.json'),dry_sha256=sha(ROOT/'dry_run_acceptance.json'),route=route)))

if __name__=='__main__':main()
