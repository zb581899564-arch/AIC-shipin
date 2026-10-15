from mf_common import *

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
