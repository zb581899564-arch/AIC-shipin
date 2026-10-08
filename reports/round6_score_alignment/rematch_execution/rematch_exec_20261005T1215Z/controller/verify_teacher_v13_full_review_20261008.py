"""Independent terminal 160-review CPU replay; never invoke inference or train."""
import base64
import json
from register_b2_package_v1 import remote, REMOTE, RUN

SCRIPT = r'''from pathlib import Path
import sys,json,datetime,socket,collections,hashlib,math
r=Path(%r);h=r/'teacher_student_autopilot_v13'
assert socket.gethostname()=='inspur-NP5570M5'
sys.path.insert(0,str(h))
import teacher_label as t, v11_resume as resume, train_student as student
assert Path(t.__file__).resolve()==h/'teacher_label.py'
expected='620df12b8cd6bb85d3bf64fc120314d400d30aa9887dfc0a58d0d4152ede8159'
out=r/'controller/V13_real_full_review_acceptance_20261008.json'
assert not out.exists(),'preserve terminal acceptance; do not rerun'
assert t.sha(h/'source_lock.json')==expected
lock=t.read(h/'source_lock.json')
for name in ('teacher_label.py','boundary_ids.py','v11_resume.py','v10_cache_reuse.py','train_student.py','supervision/validate_teacher.py'):
    assert t.sha(h/name)==lock['files'][str(h/name)]
def forbid(*args,**kwargs):raise AssertionError('independent acceptance cannot infer, launch or train')
t.inference=forbid;t.start_server=forbid;student.execute=forbid
manifest=resume.load_manifest()
assert t.sha(h/'v11_resume_manifest.json')=='a0de013f0407197b129b074e3b20e159726a83ef64b2845e8f2d38998f0afad4'
assert len(manifest['labels'])==160 and len(manifest['reviews'])==28
resume.files_match(manifest['all_receipt_files'])
print('PASS_ORIGINAL_BOUND_FILES',flush=True)
teacher=h/'teacher_01';validated=teacher/'validated'
records=t.rows(validated/'validated_records.jsonl')
reviews=t.rows(teacher/'raw_semantic_review_receipts.jsonl')
semantic=t.read(teacher/'semantic_review.json');validation=t.read(validated/'validation_receipt.json')
assert len(records)==len(reviews)==160
by_id={v['window_id']:v for v in records};rb={v['window_id']:v for v in reviews}
assert len(by_id)==len(rb)==160 and set(by_id)==set(rb)=={v['window_id'] for v in manifest['labels']}
original=resume.OLD/'teacher_01'
for name in ('annotation_receipts.jsonl','teacher_completion.json','validated/validated_records.jsonl','validated/eligible_train.jsonl','validated/eligible_dev.jsonl','validated/validation_receipt.json'):
    assert (teacher/name).read_bytes()==(original/name).read_bytes()
old_reviews={v['window_id']:v for v in manifest['reviews']}
fresh_ids=set(by_id)-set(old_reviews)
assert len(fresh_ids)==132
assert {p.parent.name for p in (teacher/'reviews').glob('*/done.json')}==fresh_ids
assert not list((teacher/'reviews').glob('*/failure.json'))
assert not (teacher/'windows').exists()
admission=t.read(h/'teacher_admission.json');validator=t.validator_for(r)
bound={};frames=0;walls=[];tokens=[]
for index,record in enumerate(records):
    identity=record['window_id'];entry=resume.entry(record,manifest);directory=Path(entry['directory'])
    annotation=t.read(directory/'annotation.json')
    assert validator.make_record(record['window'],annotation['observation'],annotation['teacher'],annotation['raw_answer'])==record
    assert record['status']!='INVALID_TEACHER_OR_INPUT_RECEIPT'
    assert annotation['model_raw_answer']==(directory/'raw_answer.txt').read_bytes().decode('utf-8')
    assert t.sha(record['window']['source_path'])==record['window']['source_sha256']
    review=rb[identity]
    t.verify_blind_review_projection(review,record,validator)
    rd=Path(old_reviews[identity]['directory']) if identity in old_reviews else teacher/'reviews'/identity
    assert t.read(rd/'review_receipt.json')==review
    done=t.read(rd/'done.json');assert done['teacher_record_sha256']==t.canonical_sha(record)
    bound[str(rd/'done.json')]=t.sha(rd/'done.json')
    for name,digest in done['files'].items():
        assert t.sha(rd/name)==digest;bound[str(rd/name)]=digest
    assert review['model_raw_answer']==(rd/'raw_answer.txt').read_bytes().decode('utf-8')
    content=t.frame_content(record['actual_observation'],namespaced=True)
    schema,constraints,relation=t.generation_constraints(None,record['actual_observation'])
    request=t.read(rd/'http/request.json');response=t.read(rd/'server_response.json')
    assert request=={'model':t.TEACHER_ID,'messages':[{'role':'user','content':[{'type':'text','text':t.review_prompt(record)},*content]}],
        'temperature':0,'seed':20261007,'top_k':1,'max_tokens':admission['max_new_tokens'],'stream':False,
        'cache_prompt':False,'n_cache_reuse':0,'timings_per_token':True,'chat_template_kwargs':{'enable_thinking':False},**constraints}
    assert t.read(rd/'generation_schema.json')==schema and t.read(rd/'generation_relation_contract.json')==relation
    http=t.read(rd/'http/http_receipt.json')
    assert http['status']=='PASS_HTTP' and http['http_status']==200 and http['retry_performed'] is False
    assert http['request_sha256']==t.sha(rd/'http/request.json') and http['response_sha256']==t.sha(rd/'http/response.bin')
    assert json.loads((rd/'http/response.bin').read_bytes())==response
    assert response['choices'][0]['message']['content']==review['model_raw_answer']
    assert response['choices'][0]['finish_reason']=='stop' and response.get('truncated',False) is False
    settings=response['__verbose']['generation_settings']
    assert settings['grammar']==constraints['grammar'] and settings['grammar_lazy'] is False
    grids=t.parse_processor_log((rd/'processor.log').read_text(errors='replace'),len(record['actual_observation']['actual_pts_sec']))
    assert grids==review['actual_observation']['actual_teacher_processor_grids']
    assert response['usage']['prompt_tokens']==review['actual_observation']['input_sequence_length']
    wall=(datetime.datetime.fromisoformat(http['finished_utc'])-datetime.datetime.fromisoformat(http['started_utc'])).total_seconds()
    assert math.isfinite(wall) and wall>0
    if identity in fresh_ids:walls.append(wall);tokens.append(response['usage']['prompt_tokens'])
    frames+=len(record['actual_observation']['frame_files'])
    if (index+1)%%20==0:print('REPLAYED',index+1,flush=True)
eligible=t.rows(validated/'eligible_train.jsonl')+t.rows(validated/'eligible_dev.jsonl')
hashes={name:t.sha(validated/name) for name in ('eligible_train.jsonl','eligible_dev.jsonl','validated_records.jsonl')}
try:
    student.verify_semantic(semantic,t.sha(validated/'validation_receipt.json'),hashes,eligible,
        {t.canonical_sha(v):v for v in records},t,validator)
except ValueError as exc:
    assert str(exc)=='STOP_T_UNBOUND_OR_UNEXPLAINABLE_BLIND_REVIEW'
else:raise AssertionError('original diagnostic stage mismatch must be reproduced')
pilot=t.rows(resume.OLD/'pilot_01/raw_semantic_review_receipts.jsonl')
assert len(pilot)==24 and {v['window_id'] for v in pilot}=={v['window_id'] for v in reviews if v['diagnostic_only']}
assert all(rb[v['window_id']]==v for v in pilot)
supported={t.canonical_sha(v) for v in records if v['sft_eligible'] and rb[v['window_id']]['support_class']!='UNKNOWN'}
selected=[v for v in records if t.canonical_sha(v) in supported]
counts=lambda f:{split:sum(v['split']==split and f(v) for v in selected) for split in ('train','dev')}
stats=dict(selected_by_split={split:sum(v['split']==split for v in records) for split in ('train','dev')},
    supported_by_split=counts(lambda v:True),supported_positive_by_split=counts(lambda v:bool(v['retained_segments'])),
    supported_explicit_empty_by_split=counts(lambda v:v['explicit_no_highlight']),
    unknown_count=sum(v['support_class']=='UNKNOWN' for v in reviews),boundary_supported_count=sum(v['boundary_supported'] for v in reviews))
for key,value in stats.items():assert semantic[key]==value
assert set(semantic['supported_teacher_record_sha256'])==supported
assert len(supported)==79 and stats['selected_by_split']=={'train':128,'dev':32}
assert stats['supported_by_split']=={'train':65,'dev':14} and stats['unknown_count']==81
assert stats['supported_positive_by_split']=={'train':55,'dev':10}
assert stats['supported_explicit_empty_by_split']=={'train':10,'dev':4}
assert semantic['semantic_training_admitted'] is False and semantic['manual_ground_truth'] is False
campaign=r.parents[2]/'improvement_round1';lp=campaign/'gpu_ledger.jsonl'
ledger=t.rows(lp);name='rematch_TAUTO_v13_teacher_review'
resource=t.read(r/'controller'/(name+'.resource.json'))
assert [v for v in ledger if v['name']==name]==[resource]
assert resource['status']=='completed' and resource['exit_code']==0 and resource['stop_reason'] is None
assert resource['charged_seconds']>0 and resource['child_pid']==970357 and resource['runner_pid']==970353
assert t.read(original.parent/'completion.json')['status']=='STOP_AUTOPILOT_PRESERVED'
assert t.read(r/'controller/rematch_TAUTO_v11_teacher_full.resource.json')['charged_seconds']==6748.806357712485
resume.files_match(manifest['authority_files']);resume.files_match(bound)
value=dict(status='PASS_REAL_V13_COMPLETE_160_BLIND_REVIEWS_INDEPENDENT_CPU_REPLAY_NOT_HUMAN_TRUTH',
    utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_lock_sha256=expected,
    resume_manifest_sha256=t.sha(h/'v11_resume_manifest.json'),semantic_review_sha256=t.sha(teacher/'semantic_review.json'),
    raw_reviews_aggregate_sha256=t.sha(teacher/'raw_semantic_review_receipts.jsonl'),original_label_count=160,
    original_review_count=28,actual_fresh_review_model_calls=132,actual_new_label_calls=0,full_selected_denominator=160,
    engineering_failure_count=0,all_original_bound_file_SHA_pass=True,all_original_label_aggregate_bytes_equal=True,
    all_review_done_bound_file_SHA_pass=True,all_actual_HTTP_processor_grammar_raw_pass=True,
    original_validator_and_exact_native_projection_pass=True,physical_PNG_and_RGB_SHA_pass=True,
    physical_frames_checked=frames,supported_count=79,supported_by_split=stats['supported_by_split'],
    supported_positive_by_split=stats['supported_positive_by_split'],supported_empty_by_split=stats['supported_explicit_empty_by_split'],
    unknown_count=81,boundary_supported_count=stats['boundary_supported_count'],UNKNOWN_never_negative=True,
    full_160_denominator_preserved=True,same_teacher_consistency_is_weak_not_truth=True,
    actual_fresh_HTTP_wall_sum_seconds=sum(walls),actual_fresh_max_prompt_tokens=max(tokens),
    actual_GPU_charged_seconds=resource['charged_seconds'],resource_receipt_sha256=t.sha(r/'controller'/(name+'.resource.json')),
    actual_wrapper_status=resource['status'],exit_code=resource['exit_code'],stop_reason=resource['stop_reason'],
    ledger_sha256=t.sha(lp),ledger_record_count=len(ledger),historical_offset_seconds=7200,
    independent_CPU_model_calls=0,training_updates_by_this_verifier=0,successful_generation_repeated=False,
    original_student_diagnostic_stage_mismatch_reproduced=True,original_pilot_diagnostic_flags_preserved=24,
    original_student_training_admission=False,old_raw_STOP_costs_preserved=True,signals_sent=0,frozen_source_changes=0,large_transfers=0,
    raw_or_per_frame_exports=False,final_ZIP_acceptance=False)
with out.open('x',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(value),flush=True)
'''


def main():
    remote(SCRIPT % REMOTE)
    encoded = remote("from pathlib import Path\nimport base64\np=Path(%r)/'controller/V13_real_full_review_acceptance_20261008.json';print(base64.b64encode(p.read_bytes()).decode())" % REMOTE, echo=False)
    path = RUN / 'controller/V13_real_full_review_acceptance_20261008.json'
    assert not path.exists()
    path.write_bytes(base64.b64decode(encoded))


if __name__ == '__main__':
    main()
