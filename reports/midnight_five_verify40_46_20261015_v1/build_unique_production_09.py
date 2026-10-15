"""Pre-GPU unique-input adoption, preserving all 519 completed token QA receipts."""
from pathlib import Path
import ast

W=Path(__file__).resolve().parents[2]
D=W/'improvement/midnight_production_unique_v3'
D.mkdir(exist_ok=False)
for p in (W/'improvement/midnight_production_runtime_v2').glob('*.py'):
    (D/p.name).write_text(p.read_text(encoding='utf8'),encoding='utf8')

(D/'alias_contract.py').write_text('''from mf_common import *

def semantic(req):
    keys=('source_sha256','source_ordinals','exact_pts','window_exact','window_native_end_ordinal','window_native_end_exact')
    return {**{k:req[k] for k in keys},'candidate_events':[{k:v[k] for k in ('original_interval_exact','selected_interval_exact','decision')} for v in req['candidate_events']]}

def accepted_cpu(reg):
    cpu=read(checked(reg['adopted_CPU_completion_ref']))
    old=read(checked(reg['original_CPU_registration_ref']))
    require(cpu['status']=='PASS_ALL_FIRST_INPUT_QA' and cpu['registration_ref']==reg['original_CPU_registration_ref'],'Original completed CPU registration binding differs')
    require(old['requests_ref']==reg['requests_ref'] and cpu['actual_count']==reg['logical_count']==len(cpu['entries']),'Adopted denominator differs')
    old_prompt=[v for k,v in old['code_files'].items() if Path(k).name=='mf_common.py']
    require(old_prompt==[sha(Path(__file__).parent/'mf_common.py')],'Accepted prompt helper changed')
    table=read(checked(reg['identical_input_alias_table_ref']))
    require(table['cpu_completion_ref']==reg['adopted_CPU_completion_ref'] and table['registered_before_GPU'] is True,'PreGPU alias table must bind original CPU completion')
    require(table['logical_count']==len(cpu['entries']) and table['model_count']==reg['expected_actual_model_calls'],'Alias denominator differs')
    by_id={v['case_id']:v for v in cpu['entries']};require(len(by_id)==len(cpu['entries']),'Duplicate logical IDs')
    aliases={v['alias_case_id']:v for v in table['aliases']}
    require(len(aliases)==len(table['aliases']) and len(cpu['entries'])-len(aliases)==table['model_count'],'Alias cardinality differs')
    order=list(by_id)
    for alias in aliases.values():
        a,c=alias['alias_case_id'],alias['canonical_case_id']
        require(c not in aliases and order.index(c)<order.index(a),'Aliases cannot chain or precede canonical')
        ra,rc=by_id[a],by_id[c]
        require(ra['input_ref']==alias['alias_input_ref'] and rc['input_ref']==alias['canonical_input_ref'],'Alias input reference differs')
        qa,qc=read(checked(ra['input_ref'])),read(checked(rc['input_ref']))
        checked(ra['first_qa_ref']);checked(rc['first_qa_ref'])
        require(qa['retarget']['full_tensor_signature']==qc['retarget']['full_tensor_signature']==alias['input_signature'],'Actual complete input signatures differ')
        require(semantic(qa)==semantic(qc) and len(qa['candidate_events'])==alias['candidate_count'],'Actual native/candidate identity differs')
        require(alias['native_identity_equal'] is True and alias['candidate_semantics_equal'] is True,'Explicit equality flags required')
    return cpu,aliases
''',encoding='utf8')

p=D/'stages.py';s=p.read_text(encoding='utf8')
s=s.replace('from mf_common import *','from mf_common import *\nfrom alias_contract import accepted_cpu')
old="root,reg=setup(stage);cpu=read(root/'cpu_01/completion.json');require(cpu['status']=='PASS_ALL_FIRST_INPUT_QA','All new input acceptance required before GPU')"
assert s.count(old)==1
s=s.replace(old,"root,reg=setup(stage);cpu,aliases=accepted_cpu(reg)")
old="eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos);entries=[]"
assert s.count(old)==1
s=s.replace(old,old+";actual_count=0;done_by_case={}")
needle="        values=original(req);new=torch.load(checked(req['token_ref']),map_location='cpu',weights_only=True)"
replacement="""        if case in aliases:
            alias=aliases[case];canonical_ref=done_by_case[alias['canonical_case_id']];canonical=read(checked(canonical_ref))
            save(folder/'done.json',dict(status='ADOPTED_IDENTICAL_NEW_INPUT_MODEL_OUTPUT_NO_NEW_CALL',actual_model_call=False,case_id=case,alias_of=alias['canonical_case_id'],canonical_model_done_ref=canonical_ref,identical_input_equality_ref=reg['identical_input_alias_table_ref'],input_ref=row['input_ref'],first_input_qa_ref=row['first_qa_ref'],raw_ref=canonical['raw_ref'],parsed=canonical['parsed']))
            done_ref=ref(folder/'done.json');done_by_case[case]=done_ref
            entries.append(dict(case_id=case,decision_ref=done_ref,input_ref=row['input_ref'],actual_model_call=False,alias_of=alias['canonical_case_id']))
            append(out/'journal.jsonl',dict(event='ALIAS_ADOPTED_NO_MODEL_CALL',case_id=case,canonical_case_id=alias['canonical_case_id'],utc=utc()))
            continue
        values=original(req);new=torch.load(checked(req['token_ref']),map_location='cpu',weights_only=True)"""
assert s.count(needle)==1;s=s.replace(needle,replacement)
s=s.replace("save(folder/'done.json',dict(case_id=case,parsed=parsed", "save(folder/'done.json',dict(actual_model_call=True,case_id=case,parsed=parsed")
old="        entries.append(dict(case_id=case,decision_ref=ref(folder/'done.json'),input_ref=row['input_ref']))"
new="        done_by_case[case]=ref(folder/'done.json');actual_count+=1\n        entries.append(dict(case_id=case,decision_ref=done_by_case[case],input_ref=row['input_ref'],actual_model_call=True))"
assert s.count(old)==1;s=s.replace(old,new)
old="    save(out/'completion.json',dict(status='PASS_ALL_NEW_INFERENCE_NOT_QUALITY',actual_model_calls=len(entries),"
new="    require(actual_count==reg['expected_actual_model_calls'] and len(entries)==reg['logical_count'],'Actual new-call denominator differs')\n    save(out/'completion.json',dict(status='PASS_ALL_NEW_INFERENCE_NOT_QUALITY',actual_model_calls=actual_count,logical_cases=len(entries),adopted_identical_input_aliases=len(aliases),identical_input_alias_table_ref=reg['identical_input_alias_table_ref'],"
assert s.count(old)==1;s=s.replace(old,new)
old="    entries=[]\n    for row in gpu['entries']:\n        done=read(checked(row['decision_ref']));raw=read(checked(done['raw_ref']));req=read(checked(row['input_ref']))"
new="""    cpu,aliases=accepted_cpu(reg);entries=[];qa_by_case={};actual_qa_count=0
    for row in gpu['entries']:
        done=read(checked(row['decision_ref']));req=read(checked(row['input_ref']))
        if row['case_id'] in aliases:
            alias=aliases[row['case_id']];canonical_qa=qa_by_case[alias['canonical_case_id']]
            previous=read(checked(canonical_qa));canonical=read(checked(done['canonical_model_done_ref']))
            require(done['actual_model_call'] is False and done['alias_of']==alias['canonical_case_id'],'Alias is not a new model call')
            require(previous['done_ref']==done['canonical_model_done_ref'] and done['parsed']==canonical['parsed']==previous['parsed'],'Alias must reuse exactly already QA accepted canonical output')
            proof=out/(row['case_id']+'.json');save(proof,dict(status='PASS_IDENTICAL_INPUT_ALIAS_NATIVE_APPLICATION_QA',done_ref=row['decision_ref'],canonical_model_done_ref=done['canonical_model_done_ref'],canonical_output_QA_ref=canonical_qa,identical_input_equality_ref=reg['identical_input_alias_table_ref'],first_input_qa_ref=done['first_input_qa_ref'],parsed=done['parsed'],CPU_only=True,new_model_calls=0))
            kept={k:v for k,v in req.items() if k not in ('retarget','original_signature','full_signature','original_prompt','prompt')}
            entries.append(dict(kept,decision_ref=row['decision_ref'],output_qa_ref=ref(proof),actual_model_call=False,alias_of=alias['canonical_case_id'],canonical_model_done_ref=done['canonical_model_done_ref'],canonical_output_QA_ref=canonical_qa,identical_input_equality_ref=reg['identical_input_alias_table_ref']))
            continue
        raw=read(checked(done['raw_ref']))
        require(done['actual_model_call'] is True and raw['actual_model_call'] is True,'Canonical must have a real new call')"""
assert s.count(old)==1;s=s.replace(old,new)
old="        entries.append(dict(kept,decision_ref=row['decision_ref'],output_qa_ref=ref(proof)))"
new="        qa_by_case[row['case_id']]=ref(proof);actual_qa_count+=1\n        entries.append(dict(kept,decision_ref=row['decision_ref'],output_qa_ref=ref(proof),actual_model_call=True))"
assert s.count(old)==1;s=s.replace(old,new)
old="actual_model_calls=len(entries),first_input_QA_complete=True,first_output_QA_complete=True,entries=entries,"
new="actual_model_calls=gpu['actual_model_calls'],logical_cases=len(entries),adopted_identical_input_aliases=len(aliases),first_model_output_QA_count=actual_qa_count,alias_application_QA_count=len(aliases),alias_application_QA_complete=True,identical_input_alias_table_ref=reg['identical_input_alias_table_ref'],adopted_CPU_completion_ref=reg['adopted_CPU_completion_ref'],first_input_QA_complete=True,first_output_QA_complete=True,entries=entries,"
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s,encoding='utf8')
p=D/'controller.py';s=p.read_text(encoding='utf8').replace('from mf_common import *','from mf_common import *\nfrom alias_contract import accepted_cpu')
start=s.index("        if reg.get('cpu_prepared_separately'):")
end=s.index("        wrapper=RUN/",start)
s=s[:start]+"        accepted_cpu(reg) # Adopt all completed real CPU input checks; never repeat preparation.\n"+s[end:]
p.write_text(s,encoding='utf8')
for p in D.glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
print('PRE_GPU_UNIQUE_RUNTIME_SYNTAX_PASS',len(list(D.glob('*.py'))))
