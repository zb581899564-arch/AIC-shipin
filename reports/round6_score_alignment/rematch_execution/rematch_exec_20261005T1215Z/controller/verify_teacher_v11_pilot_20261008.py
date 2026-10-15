"""Replay the completed pilot on CPU without inference or frozen-source writes."""
import base64
import json
from register_b2_package_v1 import remote, REMOTE, RUN


def main():
    script = '''import sys,json,base64,datetime,socket,collections,subprocess
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
r=Path(%r);h=r/'teacher_student_autopilot_v11';sys.path.insert(0,str(h))
import teacher_label as t
import pilot
assert Path(t.__file__).resolve()==h/'teacher_label.py'
def forbid(*args,**kwargs):raise AssertionError('CPU acceptance cannot generate, launch or signal')
t.inference=forbid;t.start_server=forbid
out=r/'controller/V11_real_pilot_acceptance_20261008.json'
assert not out.exists(),'preserve existing acceptance; do not repeat'
assert t.sha(h/'source_lock.json')=='0ae09ec38ff589baa5e15e16b84457b06442195de502ec7ef6a19bab9b715578'
lock=t.read(h/'source_lock.json')
for name in ('teacher_label.py','boundary_ids.py','pilot.py','supervision/validate_teacher.py'):
    path=h/name;assert t.sha(path)==lock['files'][str(path)]
p=h/'pilot_01';terminal=t.read(p/'completion.json');validator=t.validator_for(r)
assert terminal==t.read(p/'pilot_semantic_quality.json')
assert terminal['status']=='PASS_REAL_PILOT_READY_FOR_FULL_RELABEL'
assert terminal['selected_denominator']==terminal['fresh_model_calls']==24
assert terminal['verified_probe_reused_windows']==0 and terminal['optimizer_steps']==0
assert terminal['student_training_admitted'] is False
assert t.sha(p/'validated/validation_receipt.json')==terminal['validation_sha256']
assert t.sha(p/'raw_semantic_review_receipts.jsonl')==terminal['raw_reviews_sha256']
records=t.rows(p/'validated/validated_records.jsonl')
reviews=t.rows(p/'raw_semantic_review_receipts.jsonl')
assert len(records)==len(reviews)==24
by_id={v['window_id']:v for v in records};review_by_id={v['window_id']:v for v in reviews}
assert len(by_id)==len(review_by_id)==24 and by_id.keys()==review_by_id.keys()
admission=t.read(h/'teacher_admission.json');before={};physical_frames=0
for record in records:
    identity=record['window_id'];directory=h/'teacher_01/windows'/identity
    done=t.read(directory/'done.json');annotation=t.read(directory/'annotation.json')
    assert not (directory/'failure.json').exists()
    assert t.read(directory/'validated_record.json')==record
    assert done['window_sha256']==t.canonical_sha(record['window'])
    before[directory/'done.json']=t.sha(directory/'done.json')
    for name,digest in done['files'].items():
        assert t.sha(directory/name)==digest;before[directory/name]=digest
    assert t.sha(record['window']['source_path'])==record['window']['source_sha256']
    raw=(directory/'raw_answer.txt').read_bytes().decode()
    assert raw==annotation['model_raw_answer']==annotation['teacher']['model_raw_answer']
    t.verify_model_decision_projection(record)
    assert validator.make_record(record['window'],annotation['observation'],annotation['teacher'],annotation['canonical_answer'])==record
    assert record['status']!='INVALID_TEACHER_OR_INPUT_RECEIPT'
    assert annotation['teacher']['weight_files']==admission['weight_files']
    assert annotation['teacher']['job_source_lock_sha256']==t.sha(h/'source_lock.json')
    t.frame_content(annotation['observation'])
    physical_frames+=len(annotation['observation']['frame_files'])
    rd=h/'teacher_01/reviews'/identity;review=review_by_id[identity];review_done=t.read(rd/'done.json')
    assert not (rd/'failure.json').exists() and t.read(rd/'review_receipt.json')==review
    assert review_done['teacher_record_sha256']==t.canonical_sha(record)
    before[rd/'done.json']=t.sha(rd/'done.json')
    for name,digest in review_done['files'].items():
        assert t.sha(rd/name)==digest;before[rd/name]=digest
    assert (rd/'raw_answer.txt').read_bytes().decode()==review['model_raw_answer']
    t.verify_blind_review_projection(review,record,validator)
reasons,unknown=pilot.reviewed_gate(records,reviews)
assert not reasons and unknown==terminal['unknown_window_ids']
supported=[v for v in records if review_by_id[v['window_id']]['support_class']!='UNKNOWN' and v['sft_eligible']]
positive={split:sum(v['split']==split and bool(v['retained_segments']) for v in supported) for split in ('train','dev')}
negative={split:sum(v['split']==split and v['explicit_no_highlight'] for v in supported) for split in ('train','dev')}
assert positive==terminal['positive_by_split'] and negative==terminal['explicit_empty_by_split']
near=[v['window_id'] for v in records if v['retained_segments'] and sum(s['end_sec']-s['start_sec'] for s in v['retained_segments'])/v['window']['window_duration_sec']>=0.99]
whole={split:all(len(v['retained_segments'])==1 and v['retained_segments'][0]['start_sec']==0 and v['retained_segments'][0]['end_sec']==v['window']['window_duration_sec'] for v in records if v['split']==split) for split in ('train','dev')}
collapse=len(near)>=22 or any(whole.values())
assert near==terminal['near_whole_window_ids'] and whole==terminal['original_all_whole_window_by_split']
assert collapse==terminal['systematic_near_whole_window_collapse'] and not collapse
assert positive['train'] and positive['dev'] and terminal['route_decision']=='COLLECT_COMPLETE_WINDOW_WEAK_SUPERVISION'
counts=dict(collections.Counter(v['support_class'] for v in reviews));assert counts==terminal['support_class_counts']
campaign=r.parents[2]/'improvement_round1';ledger_data=(campaign/'gpu_ledger.jsonl').read_bytes()
ledger=[json.loads(line) for line in ledger_data.splitlines() if line.strip()]
rows=[v for v in ledger if v['name']=='rematch_TAUTO_v11_teacher_pilot'];assert len(rows)==1
resource=t.read(r/'controller/rematch_TAUTO_v11_teacher_pilot.resource.json')
assert rows[0]==resource and resource['status']=='completed' and resource['exit_code']==0 and resource['stop_reason'] is None
assert t.read(p/'server_stop_receipt.json')['owned_server_pid']==571161
old=r/'teacher_student_autopilot_v10'
assert t.sha(old/'source_lock.json')=='b36e260ece5abc0267f24cedf534add67588fb01ebc3c10e1e7f8ea5d65960cc'
assert t.sha(old/'teacher_01/windows/complete_45666feb9bbc3d854e9d05c1/raw_answer.txt')=='9977638522f91aa2661fd70b5179a7aed557ea816d5f451f6f50b010114f65fa'
assert t.read(old/'completion.json')['status']=='STOP_AUTOPILOT_PRESERVED'
for path,digest in before.items():assert t.sha(path)==digest
value={'status':'PASS_V11_COMPLETED_PILOT_24_24_INDEPENDENT_CPU_REPLAY_COLLECTION_ONLY_NOT_TRAINING_OR_TRUTH',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_lock_sha256':t.sha(h/'source_lock.json'),
 'pilot_completion_sha256':t.sha(p/'completion.json'),'selected_denominator':24,'actual_label_calls':24,'actual_blind_second_selection_calls':24,
 'independent_replay_model_calls':0,'old_success_repeat_calls':0,'original_validator_and_record_projection_pass':True,
 'label_and_review_all_bound_file_sha_pass':True,'physical_frame_png_and_RGB_sha_pass':True,'physical_frames_checked':physical_frames,
 'supported_class_counts':counts,'supported_positive_by_split':positive,'supported_empty_by_split':negative,
 'unknown_count':len(unknown),'UNKNOWN_never_negative':True,'all_original_decisions_and_reviews_preserved':True,
 'near_whole_window_count':len(near),'systematic_collapse':collapse,'route_decision':terminal['route_decision'],
 'actual_gpu_charged_seconds':resource['charged_seconds'],'actual_wrapper_status':resource['status'],'exit_code':resource['exit_code'],'stop_reason':resource['stop_reason'],
 'resource_receipt_sha256':t.sha(r/'controller/rematch_TAUTO_v11_teacher_pilot.resource.json'),
 'ledger_sha256':t.sha(campaign/'gpu_ledger.jsonl'),'ledger_record_count':len(ledger),'historical_offset_seconds':7200,
 'original_failed_raw_and_STOP_preserved':True,'old_and_current_successful_artifacts_unchanged':True,
 'same_teacher_agreement_is_weak_evidence_not_truth':True,'full_160_review_and_training_admission_still_required':True,
 'new_T_optimizer_updates':0,'signals_sent':0,'frozen_source_changes':0,'raw_labels_or_per_frame_data_exported':False,'large_transfers':0}
data=(json.dumps(value,ensure_ascii=False,indent=2)+chr(10)).encode();out.write_bytes(data)
print(base64.b64encode(data).decode())
''' % REMOTE
    data=base64.b64decode(remote(script,echo=False))
    path=RUN/'controller/V11_real_pilot_acceptance_20261008.json'
    assert not path.exists()
    path.write_bytes(data)
    print(json.dumps(json.loads(data),ensure_ascii=False))


if __name__=='__main__':
    main()
