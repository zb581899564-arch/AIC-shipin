"""Preparation only: new prospective route, bounded lossless scientific inputs."""
from common import ROOT,BASE,read,sha,save,key,expected_core,scientific_core
from pathlib import Path
import ast,copy,json,uuid,hashlib,subprocess
V6=BASE/'engineering_alias_remainder_v6_fresh_scope_prefix_v2'
V3=BASE/'engineering_alias_remainder_v3'

def put(p,b):
 with Path(p).open('xb') as f:f.write(b)

def main():
 assert not(ROOT/'plan.json').exists() and not(ROOT/'root_start_admission.json').exists()
 assert len(list(ROOT.glob('*.py')))==10
 capacity=BASE.parent/'root_actual_teacher_capacity_v1.json';authorization=BASE.parent/'teacher_dispatch_capacity_v5_split_recovery_authorization.json';constraints=BASE.parent/'teacher_split_v5_continuation_constraints.json'
 assert sha(capacity)=='45412115f7fbd8a721abee8bfaf726e2317e9454691028a4ea2e3825f8ef4e1a'
 assert sha(authorization)=='6ea3f2bcbffe9ac9083610f1965b894da044204b9fb6bb27d43fd3e0de9b7650'
 assert sha(constraints)=='7ce78ca785723e5f4468b189cf981d47d644ba30e676b83cdaf40aad0f4cfe34'
 gap=BASE.parent/'root_cli35_stop_full_reference_gap_v1.json';assert sha(gap)=='af49b0cb1aa7a6089e05ef9799a0c5b8c45b8cf628a89ed6127e405db1ad744c'
 oldraw=V6/'call35/stream.jsonl';raw=oldraw.read_bytes();rows=[json.loads(x) for x in raw.splitlines()];latest={r['step_update']['step_index']:r['step_update'] for r in rows if r.get('step_update',{}).get('step_type')=='tool'}
 assert len(latest)==1 and next(iter(latest.values()))['tool_name']=='view_file' and next(iter(latest.values()))['state']=='DONE'
 old35=read(V6/'call35/index.json');assert not any(Path(p).exists() for p in read(V6/'call35/freeze.json')['write_whitelist'])
 assert not any(BASE.glob('*/call36/request.json')) and not any(BASE.glob('*/call37/request.json'))
 ledger=BASE/'global_CLI_ledger.jsonl';lr=[json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines()];assert max(r['global_count'] for r in lr)==35
 t=[r for r in lr if r['global_count']==35 and r['event']=='TERMINAL'];assert len(t)==1 and t[0]['raw_sha256']==sha(oldraw)
 put(ROOT/'actual_global35_ledger_prefix.jsonl',ledger.read_bytes())
 prior=[BASE/'engineering_CLI36_37_split_fragment_v8v4/execution_code_binding.json',BASE/'engineering_CLI36_37_split_fragment_v8v4/prepare_path_projection_failure_preserved.json',BASE/'engineering_CLI36_37_split_fragment_v8v4/path_projection_recovery_v1/execution_code_binding.json',BASE/'engineering_CLI36_37_split_fragment_v8v4/path_projection_recovery_v1/dry_run_acceptance.json',BASE/'engineering_CLI36_37_split_fragment_v8v4/path_projection_recovery_v1/independent_CPU_negative_acceptance.json',BASE/'engineering_CLI36_37_split_fragment_v8v4/path_projection_recovery_v1/call36/freeze.json',BASE/'engineering_CLI36_37_split_fragment_v8v4/path_projection_recovery_v1/call37/freeze.json',BASE.parent/'plan_review/v8v4_ack_order_memory_counterexample_v1.json',BASE.parent/'plan_review/v8v3_independent_start_review_v1.md',BASE/'engineering_CLI36_37_split_fragment_v8v3/execution_code_binding.json',BASE/'engineering_CLI36_37_split_fragment_v8v3/dry_run_acceptance.json',BASE/'engineering_CLI36_37_split_fragment_v8v3/independent_CPU_negative_acceptance.json',BASE/'engineering_CLI36_37_split_fragment_v8v3/call36/freeze.json',BASE/'engineering_CLI36_37_split_fragment_v8v3/call37/freeze.json',BASE/'engineering_CLI36_37_split_fragment_v8v3/scientific_text_map.json',BASE/'engineering_CLI36_37_split_fragment_v8v2/CPU_negative_fixture_failure_preserved.json',BASE/'engineering_CLI36_37_split_fragment_v8v2/execution_code_binding.json',BASE/'engineering_CLI36_37_split_fragment_v8v2/dry_run_acceptance.json',BASE/'engineering_CLI36_37_split_fragment_v8v2/call36/freeze.json',BASE/'engineering_CLI36_37_split_fragment_v8v2/call37/freeze.json',*(srcp for srcp in [BASE/'engineering_CLI36_37_split_fragment_v8/execution_code_binding.json',BASE/'engineering_CLI36_37_split_fragment_v8/dry_run_acceptance.json',BASE/'engineering_CLI36_37_split_fragment_v8/call36/freeze.json',BASE/'engineering_CLI36_37_split_fragment_v8/call37/freeze.json']),capacity,authorization,constraints,ROOT/'actual_fresh_barrier_positive_proof.json',gap,oldraw,V6/'call35/terminal.json',V6/'call35/audit.json',V6/'call35/actual_terminal_cost.json',V6/'actual_CLI35_terminal_classification_v1.json',V6/'stopped.json',V6/'root_start_admission.json',V6/'execution_code_binding.json',V6/'call35/freeze.json',V6/'call36/freeze.json',V6/'call35/index.json',V6/'call36/index.json',ROOT/'actual_global35_ledger_prefix.jsonl',BASE/'PROTOCOL.md',BASE.parent/'PROTOCOL.md',V3/'PROTOCOL.md',BASE/'engineering_alias_remainder_v4_bootstrap_file/PROTOCOL.md']
 prior.extend(Path(p['path']) for p in read(ROOT/'actual_fresh_barrier_positive_proof.json')['sources'])
 prior.append(ROOT/'prior_native_barrier_positive_proof.json')
 bindings={str(p):sha(p) for p in prior}
 save(ROOT/'readiness_actual35.json',dict(status='OLD35_ZERO_MEDIA_STOP_NEW_SPLIT36_37_PENDING_ROOT_GATE',actual_bindings=bindings,actual_global=35,old35_media_done=0,old35_ACK_written=0,old35_facts=0,old35_proposals=0,prior36_requests=0,old35_whole_REJECT_preserved=True,quality_gap_receipt_sha256=sha(gap),fixed_denominator=24,teacher_supplement_denominator=21,new_model_calls=0,cash_cost='UNKNOWN_NOT_ZERO'))
 sources={str(p):sha(p) for p in list(ROOT.glob('*.py'))+[ROOT/'PROTOCOL.md']};save(ROOT/'execution_code_binding.json',dict(sources=sources,actual_prior_bindings=bindings,readiness_sha256=sha(ROOT/'readiness_actual35.json'),requires_root_prospective_route_gate=True,previous_registered35_preserved=True,new_model_calls=0))
 drafts=[];routes=[]
 for number,oldnumber,jobs in ((36,35,[19,20]),(37,36,[21,22,23])):
  a=ROOT/f'call{number}';a.mkdir();(a/'text').mkdir()
  windows=[];literal=[];oldwindows=[];inputs={}
  for n in (oldnumber,):
   old=V6/f'call{n}';inputs.update(read(old/'freeze.json')['inputs'])
   for w,l in zip(read(old/'index.json')['windows'],read(old/'literal_execution_parameters.json')):
    original=copy.deepcopy(w);oldwindows.append(original);w=copy.deepcopy(w);l=copy.deepcopy(l)
    project=lambda p:p.replace(str(old),str(a))
    for g,lg in zip(w['groups'],l['native_groups']):g['output_path']=project(g['output_path']);lg['write_to_file']['TargetFile']=g['output_path']
    w['proposal_path']=project(w['proposal_path']);l['proposal_write_to_file']['TargetFile']=w['proposal_path']
    windows.append(w);literal.append(l)
  assert [w['job_index'] for w in windows]==jobs
  from prompt import scientific_text,piece,main_body,header_body,native_body,compact_records
  originals=[];maps=[]
  for n in (35,36):
   p=V3/f'call{n}/frozen_prompt.txt';b=p.read_bytes();put(a/f'original_v3_prompt{n}.txt',b);originals.append(b.decode('utf-8'))
   classified=[]
   for i,line in enumerate(b.decode('utf-8').splitlines()):
    if line.startswith('先view_file本会话index '):category='OLD_ENGINEERING_INDEX_PREFIX_REPLACED_SCIENTIFIC_TAIL_VERBATIM';selected='窗口依固定顺序'+line.split('窗口依固定顺序',1)[1]
    elif line.startswith('本会话literal执行表：'):category='GIANT_DUPLICATED_LITERAL_LOSSLESS_IDENTITY_AND_LITERAL_PARTS';selected=None
    elif line.startswith('仅job17为明确成功观察移交：'):category='OLD_ENGINEERING_17_TRANSFER_CONDITION_NOT_IN_FIXED19_23';selected=None
    elif line.startswith('读取白名单 '):category='GIANT_EXPANDED_DUPLICATE_WHITELIST_REPLACED_FROZEN_PROGRAM_WHITE_AND_LITERAL_PARTS';selected=None
    else:category='SCIENTIFIC_PARAGRAPH_VERBATIM';selected=line
    classified.append(dict(source_line=i+1,original_bytes=len(line.encode('utf-8')),original_line_sha256=hashlib.sha256(line.encode()).hexdigest(),category=category,scientific_selected_sha256=hashlib.sha256(selected.encode()).hexdigest() if selected else None,scientific_selected_text=selected))
   maps.append(dict(original_path=str(p),original_sha256=sha(p),all_original_lines_classified=classified))
  science=scientific_text(originals[0]);assert science==scientific_text(originals[1]);put(a/'science_verbatim_program_only.txt',science.encode())
  parts=[]
  def part(pid,kind,job,before_group=None):
   p=dict(part_id=pid,kind=kind,job_index=job,path=str(a/'text'/f'{pid}.txt'),ack_path=str(a/f'{pid}_ACK.json'),expected_ACK_path=str(a/'text'/f'{pid}_expected_ACK.json'),insertion_point='MAIN' if kind=='main' else 'WINDOW_HEADER' if kind=='header' else f'NATIVE_FRAME_START_{before_group*4:02d}',before_group=before_group,before_native_frame_id=f'F{before_group*4:02d}' if before_group is not None else None)
   parts.append(p);return p
  mainp=part('main','main',None);headers=[]
  for w in windows:
   h=part(f"w{w['job_index']:02d}_header",'header',w['job_index']);headers.append(h);w['header_fragment_id']=h['part_id'];w['native_fragment_ids']=[part(f"w{w['job_index']:02d}_native{s*4:02d}_{(s+4)*4-1:02d}",'native_index',w['job_index'],s)['part_id'] for s in range(0,16,4)]
  index=dict(index_path=str(a/'index.json'),windows=windows,text_fragments=parts,main_fragment_id='main',bootstrap_instruction_path=mainp['path'],bootstrap_ack_path=mainp['ack_path'],bootstrap_ack_expected_path=mainp['expected_ACK_path'],main_instruction_path=mainp['path'],model_identity_forbidden=True,original_science_unchanged=True,program_only_index_not_teacher_whitelisted=True,core_per_window=100,scope_core_counts=[2+100*i for i in range(1,len(jobs)+1)],scientific_source_plan_unchanged=True)
  for p in parts:
   w=next((w for w in windows if w['job_index']==p['job_index']),None);l=next((l for l in literal if l['job_index']==p['job_index']),None)
   if p['kind']=='main':body=main_body(science,headers,number,jobs);groups=[];counts=dict(native=64*len(jobs),effective=8*len(jobs));anchor=dict(first_header=headers[0]['path'],last_header=headers[-1]['path'])
   elif p['kind']=='header':
    nativeparts=[q for q in parts if q['job_index']==p['job_index'] and q['kind']=='native_index'];body=header_body(w,nativeparts,l);groups=list(range(16));counts=dict(native=64,effective=8);anchor=dict(first_native=w['groups'][0]['frames'][0]['path'],last_native=w['groups'][-1]['frames'][-1]['path'],clip=w['clip_path'],proposal=w['proposal_path'])
   else:
    s=p['before_group'];body=native_body(w,s,l);groups=list(range(s,s+4));counts=dict(native=16,effective=0);anchor=dict(first_native=w['groups'][s]['frames'][0]['path'],last_native=w['groups'][s+3]['frames'][-1]['path'],last_fact_output=w['groups'][s+3]['output_path'])
   oldpart=read(BASE/'engineering_CLI36_37_split_fragment_v8v3'/f'call{number}'/'text'/f"{p['part_id']}_expected_ACK.json");ack=dict(marker=oldpart['marker'],part_id=p['part_id'],fixed_job_indices=jobs if w is None else [w['job_index']],group_indices=groups,frame_count=counts,route_anchor=anchor);save(p['expected_ACK_path'],ack);payload=piece(body,ack,p['ack_path']).encode('utf-8');put(p['path'],payload)
   assert len(payload)<30000 and payload.endswith(b'\n') and b'\r' not in payload and len(payload.splitlines())<=450 and max(map(len,payload.decode().splitlines()))<=1000,(p['part_id'],len(payload),len(payload.splitlines()))
   oldtext=BASE/'engineering_CLI36_37_split_fragment_v8v3'/f'call{number}'/'text'/f"{p['part_id']}.txt"
   oldroot=str(BASE/'engineering_CLI36_37_split_fragment_v8v3');newroot=str(ROOT)
   expected_payload=oldtext.read_text(encoding='utf-8').replace(json.dumps(oldroot,ensure_ascii=False)[1:-1],json.dumps(newroot,ensure_ascii=False)[1:-1]).replace(oldroot,newroot).encode('utf-8')
   assert payload==expected_payload,(p['part_id'],'NOT_BYTE_EXACT_PRIOR_TEXT_PATH_PROJECTION')
   inputs[str(oldtext)]=sha(oldtext);inputs[str(BASE/'engineering_CLI36_37_split_fragment_v8v3'/f'call{number}'/'text'/f"{p['part_id']}_expected_ACK.json")]=sha(BASE/'engineering_CLI36_37_split_fragment_v8v3'/f'call{number}'/'text'/f"{p['part_id']}_expected_ACK.json")
   p.update(original_text_path=str(oldtext),original_text_sha256=sha(oldtext),only_directory_path_projection=True,input_sha256=sha(p['path']),payload_bytes=len(payload),exact_Go_LF_lines=len(payload.split(b'\n')),Python_splitlines=len(payload.splitlines()),max_line_characters=max(map(len,payload.decode().splitlines())),expected_ACK_sha256=sha(p['expected_ACK_path']))
  assert len(parts)==1+5*len(jobs) and len(expected_core(index))==2+100*len(jobs) and len(scientific_core(index))==90*len(jobs)
  save(a/'index.json',index);save(a/'literal_execution_parameters.json',literal)
  short=f"First view_file the ENTIRE file at AbsolutePath {mainp['path']} exactly once, no range. Follow its full scientific instructions and fragmented fixed-window routes; immediately write each file's tail ACK before proceeding. Any missing ACK/error/truncation: STOP, no retry. Only view_file/write_to_file."
  put(a/'short_prompt.txt',short.encode());assert all(read(p['expected_ACK_path'])['marker'] not in short and read(p['expected_ACK_path'])['marker'] not in (a/'index.json').read_text(encoding='utf-8') for p in parts)
  save(a/'scientific_text_map.json',dict(status='ALL_ORIGINAL_LINES_CLASSIFIED_SCIENTIFIC_SELECTION_VERBATIM_BOTH_PROMPTS_EQUAL',sources=maps,science_program_file=str(a/'science_verbatim_program_only.txt'),science_sha256=sha(a/'science_verbatim_program_only.txt'),main_fragment_path=mainp['path'],main_contains_verbatim_science_once=Path(mainp['path']).read_bytes().count(science.encode())==1,selected_scientific_lines=6,only_engineering_exceptions_explicit=True))
  save(a/'lossless_index_fragment_reconstruction.json',dict(status='PROGRAM_INDEX_ORIGINAL_WINDOWS_ONLY_NEW_OUTPUT_PATH_PROJECTION_TEXT_PARTS_LOSSLESS',original_index_paths=[str(V6/f'call{n}/index.json') for n in (35,36)],fixed_job_indices=jobs,new_window_field_projection_unchanged=True,native_frame_records=64*len(windows),native_identity_records=64*len(windows),student_preview_records=8*len(windows),clip_records=len(windows),literal_view_parameters=73*len(windows),fragment_count=len(parts)))
  original_cpu=BASE/'engineering_CLI36_37_split_fragment_v8'/f'call{number}'/'prepared_original_pixel_clock_checks.json'
  original_checks=read(original_cpu)
  assert [x['job_index'] for x in original_checks['windows']]==jobs
  for w,pc,cc in zip(windows,original_checks['windows'],original_checks['clips']):
   frames=[*([f for g in w['groups'] for f in g['frames']]),*w['student_previews']]
   assert len(pc['checks'])==72
   for f,c in zip(frames,pc['checks']):assert f['path']==c['alias_path'] and f['png_sha256']==c['png_sha256'] and f['rgb_pixel_sha256']==c['rgb_pixel_sha256'] and f['geometry']==c['geometry'] and sha(f['path'])==c['png_sha256']
   assert w['clip_path']==cc['alias'] and w['original_clip_path']==cc['original'] and sha(cc['alias'])==cc['sha256']==sha(cc['original'])
  save(a/'prepared_original_pixel_clock_checks.json',dict(status='EXACT_PRIOR_SUCCESSFUL_CPU_PIXEL_GEOMETRY_CLIP_CHECKS_REFERENCED_NO_REPEAT_DECODE',original_receipt_path=str(original_cpu),original_receipt_sha256=sha(original_cpu),actual_PNG_count=72*len(windows),native_PNG_count=64*len(windows),effective_PNG_count=8*len(windows),clip_count=len(windows),windows=original_checks['windows'],clips=original_checks['clips'],new_model_calls=0,new_video_decode=0,new_CPU_PNG_decode=0))
  inputs[str(original_cpu)]=sha(original_cpu)
  inputs.update(sources);inputs.update(bindings)
  for p in (ROOT/'execution_code_binding.json',ROOT/'readiness_actual35.json',a/'scientific_text_map.json',a/'lossless_index_fragment_reconstruction.json',a/'prepared_original_pixel_clock_checks.json'):inputs[str(p)]=sha(p)
  for p in a.rglob('*'):
   if p.is_file():inputs[str(p)]=sha(p)
  reads=[p['path'] for p in parts]+[x for w in windows for x in [w['clip_path'],*(f['path'] for g in w['groups'] for f in g['frames']),*(f['path'] for f in w['student_previews'])]];outputs=[p['ack_path'] for p in parts]+[x for w in windows for x in [*(g['output_path'] for g in w['groups']),w['proposal_path']]]
  selfreads=[x for w in windows for x in [*(g['output_path'] for g in w['groups']),w['proposal_path']]]
  fr=dict(inputs=inputs,automatic_retry=False,read_whitelist=reads,self_read_whitelist=selfreads,write_whitelist=outputs,fixed_job_indices=jobs,CLI_before=number-1,CLI_after=number,timeout_seconds=7200,model='gemini-3.8-flash-high',global_cap=37,expected_core_tool_calls=2+100*len(jobs),scientific_media_fact_tool_calls=90*len(jobs),fragment_count=len(parts),core_per_window=100,scope_core_counts=[2+100*i for i in range(1,len(jobs)+1)],main_instruction_path=mainp['path'],protocol_sha256=sha(ROOT/'PROTOCOL.md'),parent_protocol_sha256=sha(BASE/'PROTOCOL.md'),source_binding_sha256=sha(ROOT/'execution_code_binding.json'),old35_ZERO_media_preserved=True,prior36_not_started=True,new_prospective_route_requires_root_gate=True)
  assert not any(Path(p).exists() for p in outputs);assert key(a/'index.json') not in {key(p) for p in reads+selfreads};drafts.append((a,fr,parts))
  from launch import command
  units=len(subprocess.list2cmdline(command(number,short)).encode('utf-16-le'))//2+1;assert units<1024 and units<32767
 
  if not (ROOT/'scientific_text_map.json').exists():save(ROOT/'scientific_text_map.json',read(a/'scientific_text_map.json'))
  routes.append(dict(CLI=number,jobs=jobs,core=len(expected_core(index)),scope_cores=index['scope_core_counts'],parts=len(parts),max_text_bytes=max(p['payload_bytes'] for p in parts),argv_units=units))
 for a,fr,parts in drafts:
  fr['inputs'][str(ROOT/'scientific_text_map.json')]=sha(ROOT/'scientific_text_map.json');save(a/'freeze.json',fr)
 AST=[]
 for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'));AST.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size))
 save(ROOT/'plan.json',dict(status='PREPARED_SPLIT36_37_PENDING_ROOT_ACTUAL_REVIEW_NO_START',routing=routes,text_parts=27,total_tool_calls=504,science_core=450,actual_global=35,global_cap=37,timeout_seconds_each=7200,capacity_risk='ACTUAL_FRESH29_32_BOUND_ESTIMATE_NOT_GUARANTEE',actual_capacity_path=str(capacity),actual_capacity_sha256=sha(capacity),engineering_limit37_is_ROOT_decision_not_human_numeric_quote=True,new_model_calls=0))
 save(ROOT/'dry_run_acceptance.json',dict(status='PASS_10_AST_27_BOUNDED_COMPLETE_FRAGMENTS_EXACT_SCIENCE_ORIGINAL_MEDIA_CPU_ONLY_PENDING_ROOT',AST=AST,execution_binding_sha256=sha(ROOT/'execution_code_binding.json'),routing=routes,freezes=[dict(path=str(a/'freeze.json'),sha256=sha(a/'freeze.json'),inputs=len(fr['inputs'])) for a,fr,parts in drafts],scientific_text_map_sha256=sha(ROOT/'scientific_text_map.json'),actual_barrier_positive_sha256=sha(ROOT/'actual_fresh_barrier_positive_proof.json'),actual_capacity_sha256=sha(capacity),runtime_capacity_PASS=False,new_model_calls=0,new_video_decode=0,cash_cost='UNKNOWN_NOT_ZERO'))
 print(json.dumps(dict(root=str(ROOT),routes=routes,binding_sha256=sha(ROOT/'execution_code_binding.json'),dry_run_sha256=sha(ROOT/'dry_run_acceptance.json')),ensure_ascii=False))
if __name__=='__main__':main()
