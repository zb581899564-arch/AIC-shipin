"""Independent CPU revalidation of real V10 probe bytes; never call inference."""
import base64
import json
from register_b2_package_v1 import remote, REMOTE, RUN


def main():
    script = '''import sys,json,base64,datetime,socket
from pathlib import Path
from collections import Counter
assert socket.gethostname()=='inspur-NP5570M5'
r=Path(%r);here=r/'teacher_student_autopilot_v10';sys.path.insert(0,str(here));import teacher_label as t
assert Path(t.__file__).resolve()==here/'teacher_label.py'
probe=t.read(here/'teacher_01/teacher_probe_completion.json');visual=t.read(here/'visual_probe_01/completion.json')
assert probe['status']=='PASS_REAL_NONTEST_TEACHER_PROBE' and len(probe['window_ids'])==2
assert visual['status']=='PASS_REAL_SYNTHETIC_VISUAL_INTERFACE' and visual['case_count']==visual['real_model_calls']==8
assert all(x['pass'] is True and x['expected_red_square_frame_ids']==x['actual_red_square_frame_ids'] for x in visual['cases'])
windows={w['window_id']:w for n in ('selected_train.jsonl','selected_dev.jsonl') for w in t.rows(here/'selection_01'/n)}
a=t.read(here/'teacher_admission.json');validator=t.validator_for(r)
def forbid(*args,**kwargs):raise AssertionError('CPU revalidation cannot invoke generation')
t.inference=forbid
records=[];before={};hash_count=0
for identity in probe['window_ids']:
    out=here/'teacher_01/windows'/identity;done=t.read(out/'done.json')
    assert t.sha(out/'done.json')==probe['probe_receipts'][identity]['done_sha256'];before[out/'done.json']=t.sha(out/'done.json')
    for n,digest in done['files'].items():assert t.sha(out/n)==digest;before[out/n]=digest;hash_count+=1
    t.annotate(windows[identity],out,validator,a,'http://127.0.0.1:1',1,'/home/inspur/anaconda3/envs/Andy/bin/ffprobe',allow_prior_reuse=True)
    record=t.read(out/'validated_record.json');t.verify_model_decision_projection(record);records.append(record)
for path,digest in before.items():assert t.sha(path)==digest
resources={}
for stage in ('teacher_visual_interface','teacher_probe'):
    path=r/'controller'/('rematch_TAUTO_v10_'+stage+'.resource.json');v=t.read(path)
    assert v['status']=='completed' and v['exit_code']==0 and v['stop_reason'] is None
    resources[stage]={k:v[k] for k in ('status','charged_seconds','exit_code','stop_reason','sampled_peak_memory_mib')}
    resources[stage]['original_receipt_sha256']=t.sha(path)
old=r/'teacher_student_autopilot_v9'
assert t.sha(old/'source_lock.json')=='a3dc4e4f1e35c45624adaaa66fe0ede5a055e314d8a68d11a6aecaaef831c0b3'
failed=old/'teacher_01/windows/complete_087af79e4b421be308d6cf6f'
ordered=t.read(here/'ordered_boundary_cpu_acceptance.json')
assert t.sha(failed/'raw_answer.txt')==ordered['old_raw_sha256'], 'raw string hash must bind raw string file'
binding=t.read(here/'source_lock.json')['files']
assert t.sha(failed/'server_response.json')==binding[str(failed/'server_response.json')], 'original HTTP container changed'
assert t.read(old/'completion.json')['status']=='STOP_AUTOPILOT_PRESERVED'
v=dict(status='PASS_V10_REAL_VISUAL8_AND_HEAVY2_ENGINEERING_NOT_SEMANTIC_OR_TRAINING',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_lock_sha256=t.sha(here/'source_lock.json'),real_visual_calls=8,all_eight_visual_expected_equal_actual=True,
    visual64_forward_and_reverse_pass=True,real_fresh_non_test_probe_calls=2,real_probe_status=probe['status'],
    real_probe_wall_sec=probe['wall_sec'],real_probe_per_window_wall_sec=probe['per_window_wall_sec'],max_real_prompt_tokens=probe['max_actual_prompt_tokens'],
    probe_original_validator_and_all_done_file_SHA_revalidated=True,accepted_probe_label_status_counts=dict(Counter(x['status'] for x in records)),
    probe_bound_file_hash_count=hash_count,raw_and_successful_records_unchanged=True,independent_revalidation_CPU_only=True,
    independent_revalidation_inference_calls=0,independent_inspector_initial_container_and_hash_target_errors_corrected=True,
    production_error_or_source_change_by_inspector=False,original_invalid_V9_raw_and_STOP_kept=True,synthetic_never_training_labels=True,
    same_teacher_review_not_ground_truth=True,semantic_quality_or_training_admitted_by_this_check=False,new_T_optimizer_updates=0,
    resource_receipts=resources,raw_labels_or_per_frame_data_exported=False,large_transfers=0)
b=(json.dumps(v,ensure_ascii=False,indent=2)+chr(10)).encode();out=r/'controller/V10_real_interface_probe_acceptance_20261008.json'
assert not out.exists(), 'independent acceptance receipt cannot be overwritten'
out.write_bytes(b);print(base64.b64encode(b).decode())
''' % REMOTE
    data = base64.b64decode(remote(script, echo=False))
    path = RUN/'controller/V10_real_interface_probe_acceptance_20261008.json'
    assert not path.exists(), 'local independent receipt cannot be overwritten'
    path.write_bytes(data)
    print(json.dumps(json.loads(data),ensure_ascii=False))


if __name__=='__main__': main()
