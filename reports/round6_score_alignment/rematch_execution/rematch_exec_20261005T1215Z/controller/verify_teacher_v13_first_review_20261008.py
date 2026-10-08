"""Independently replay the first actual repaired legacy blind review; no model call."""
import base64,json
from register_b2_package_v1 import remote,REMOTE,RUN
SCRIPT=r'''from pathlib import Path
import sys,json,hashlib,datetime,socket,math
r=Path(%r);h=r/'teacher_student_autopilot_v13';sys.path.insert(0,str(h));import teacher_label as teacher
import v11_resume as resume
assert socket.gethostname()=='inspur-NP5570M5'
expected='620df12b8cd6bb85d3bf64fc120314d400d30aa9887dfc0a58d0d4152ede8159'
assert teacher.sha(h/'source_lock.json')==expected
proof=teacher.read(h/'teacher_01/first_review_generation.json');identity=proof['window_id']
assert identity=='complete_087af79e4b421be308d6cf6f' and proof['fresh_review_model_calls']==1 and proof['new_label_calls']==0
record=next(v for v in teacher.rows(h/'teacher_01/validated/validated_records.jsonl') if v['window_id']==identity)
directory=h/'teacher_01/reviews'/identity;done=teacher.read(directory/'done.json');review=teacher.read(directory/'review_receipt.json')
assert all(teacher.sha(directory/name)==digest for name,digest in done['files'].items())
assert teacher.sha(directory/'done.json')==proof['review_done_sha256'] and teacher.sha(directory/'review_receipt.json')==proof['review_receipt_sha256']
assert review['model_raw_answer']==(directory/'raw_answer.txt').read_bytes().decode('utf-8')
def no_generation(*args,**kwargs):raise AssertionError('independent CPU replay cannot generate')
teacher.inference=no_generation;teacher.start_server=no_generation
comparison=teacher.verify_blind_review_projection(review,record)
content=teacher.frame_content(record['actual_observation'],namespaced=True)
schema,constraints,relation=teacher.generation_constraints(None,record['actual_observation'])
admission=teacher.read(h/'teacher_admission.json')
request=teacher.read(directory/'http/request.json');response=teacher.read(directory/'server_response.json')
expected_request={'model':teacher.TEACHER_ID,'messages':[{'role':'user','content':[
 {'type':'text','text':teacher.review_prompt(record)},*content]}],
 'temperature':0,'seed':20261007,'top_k':1,'max_tokens':admission['max_new_tokens'],
 'stream':False,'cache_prompt':False,'n_cache_reuse':0,'timings_per_token':True,
 'chat_template_kwargs':{'enable_thinking':False},**constraints}
assert request==expected_request and teacher.read(directory/'generation_schema.json')==schema
assert teacher.read(directory/'generation_relation_contract.json')==relation
http=teacher.read(directory/'http/http_receipt.json')
assert http['status']=='PASS_HTTP' and http['http_status']==200 and http['retry_performed'] is False
assert http['request_sha256']==teacher.sha(directory/'http/request.json')
assert http['response_sha256']==teacher.sha(directory/'http/response.bin')
assert json.loads((directory/'http/response.bin').read_bytes())==response
assert response['choices'][0]['message']['content']==review['model_raw_answer']
assert response['choices'][0]['finish_reason']=='stop' and response.get('truncated',False) is False
settings=response['__verbose']['generation_settings']
assert settings['grammar']==constraints['grammar'] and settings['grammar_lazy'] is False
grids=teacher.parse_processor_log((directory/'processor.log').read_text(errors='replace'),len(record['actual_observation']['actual_pts_sec']))
assert grids==review['actual_observation']['actual_teacher_processor_grids']
assert response['usage']['prompt_tokens']==review['actual_observation']['input_sequence_length']
wall=(datetime.datetime.fromisoformat(http['finished_utc'])-datetime.datetime.fromisoformat(http['started_utc'])).total_seconds()
assert math.isfinite(wall) and wall>0
assert teacher.sha(record['window']['source_path'])==record['window']['source_sha256']
original=resume.entry(record);assert original['teacher_record_sha256']==teacher.canonical_sha(record)
resume.files_match(original['files'])
assert not (h/'teacher_01/windows').exists()
value=dict(status='PASS_REAL_V13_BLOCKED_LEGACY_BLIND_REVIEW_INDEPENDENT_CPU_REPLAY_NOT_TRAINING_OR_TRUTH',
 utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_lock_sha256=expected,
 first_review_receipt_sha256=teacher.sha(h/'teacher_01/first_review_generation.json'),
 actual_new_review_model_calls=1,new_label_model_calls=0,old_success_generation_repeated=False,
 independent_CPU_revalidation_model_calls=0,original_validator_and_input_and_raw_SHA_pass=True,
 actual_HTTP_request_processor_applied_grammar_and_response_SHA_pass=True,
 actual_review_HTTP_wall_seconds=wall,actual_teacher_weight_and_runtime_identity_pass=True,
 physical_frame_and_native_clock_SHA_pass=True,original_label_record_unchanged=True,
 actual_prompt_tokens=review['actual_observation']['input_sequence_length'],support_class=comparison['support_class'],
 original_review_status=review['review_status'],new_T_optimizer_updates=0,
 semantic_training_admitted=False,same_teacher_comparison_not_human_truth=True)
target=r/'controller/V13_real_first_review_acceptance_20261008.json'
with target.open('x',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(value))
'''

def main():
    remote(SCRIPT%(REMOTE,))
    raw=remote("from pathlib import Path\nimport base64\np=Path(%r)/'controller/V13_real_first_review_acceptance_20261008.json';print(base64.b64encode(p.read_bytes()).decode())"%REMOTE,echo=False)
    path=RUN/'controller/V13_real_first_review_acceptance_20261008.json';assert not path.exists();path.write_bytes(base64.b64decode(raw))

if __name__=='__main__':main()
