"""Read-only CPU replay of the real new-format failed-window generation."""
import base64
import json
from register_b2_package_v1 import remote, REMOTE, RUN


def main():
    script = '''import sys,json,base64,datetime,socket
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
r=Path(%r);here=r/'teacher_student_autopilot_v11';sys.path.insert(0,str(here));import teacher_label as t
assert Path(t.__file__).resolve()==here/'teacher_label.py'
def forbid(*args,**kwargs):raise AssertionError('independent CPU replay cannot invoke a model or start a server')
t.inference=forbid;t.start_server=forbid
identity='complete_45666feb9bbc3d854e9d05c1'
proof=t.read(here/'pilot_01/new_format_real_probe.json')
assert proof['window_id']==identity and proof['fresh_model_calls']==1 and proof['old_success_model_calls']==0
assert proof['status']=='PASS_REAL_BF_PER_SEGMENT_EVIDENCE_GENERATION_NOT_SEMANTIC_ACCEPTANCE'
out=here/'teacher_01/windows'/identity
done=t.read(out/'done.json');annotation=t.read(out/'annotation.json');record=t.read(out/'validated_record.json')
assert t.sha(out/'done.json')==proof['done_sha256'] and t.sha(out/'annotation.json')==proof['annotation_sha256']
before={out/'done.json':t.sha(out/'done.json')}
for name,digest in done['files'].items():assert t.sha(out/name)==digest;before[out/name]=digest
lock=t.read(here/'source_lock.json')
for name in ('teacher_label.py','boundary_ids.py','supervision/validate_teacher.py'):
    path=here/name;assert t.sha(path)==lock['files'][str(path)]
config=t.read(here/'config.json');admission=t.read(here/'teacher_admission.json')
windows={w['window_id']:w for name in ('selected_train.jsonl','selected_dev.jsonl')
    for w in t.rows(here/'selection_01'/name)}
window=windows[identity];assert done['window_sha256']==t.canonical_sha(window)
assert t.sha(window['source_path'])==window['source_sha256']
raw=(out/'raw_answer.txt').read_bytes().decode('utf-8')
assert raw==annotation['model_raw_answer']==annotation['teacher']['model_raw_answer']
decision=t.verify_model_decision_projection(record)
assert not t.uses_legacy_interface(decision)
validator=t.validator_for(r)
replayed=validator.make_record(window,annotation['observation'],annotation['teacher'],annotation['canonical_answer'])
assert replayed==record and record['status']!='INVALID_TEACHER_OR_INPUT_RECEIPT'
assert annotation['teacher']['weight_files']==admission['weight_files']
assert annotation['teacher']['job_source_lock_sha256']==t.sha(here/'source_lock.json')
t.frame_content(annotation['observation'])
old=r/'teacher_student_autopilot_v10';old_failed=old/'teacher_01/windows'/identity
assert t.sha(old/'source_lock.json')=='b36e260ece5abc0267f24cedf534add67588fb01ebc3c10e1e7f8ea5d65960cc'
assert t.sha(old_failed/'raw_answer.txt')=='9977638522f91aa2661fd70b5179a7aed557ea816d5f451f6f50b010114f65fa'
assert t.read(old/'completion.json')['status']=='STOP_AUTOPILOT_PRESERVED'
handoff=t.read(here/'legacy_handoff.json')
assert handoff['fresh_model_calls']==0 and handoff['pilot_old_success_reuse_count']==0
for path,digest in before.items():assert t.sha(path)==digest
v=dict(status='PASS_V11_REAL_FAILED_WINDOW_BF_GENERATION_INDEPENDENT_CPU_REPLAY_NOT_SEMANTIC_OR_TRAINING',
    utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_lock_sha256=t.sha(here/'source_lock.json'),
    actual_new_model_calls=1,original_success_new_calls=0,original_probe_records_reused=2,
    independent_revalidation_model_calls=0,original_validator_and_canonical_record_byte_identity_pass=True,
    raw_prior_to_validation_preserved=True,complete_source_and_input_SHA_pass=True,physical_frame_SHA_pass=True,
    boundary_and_frame_namespaces_separate=True,every_KEEP_segment_has_model_selected_physical_witness=True,
    actual_label_status=record['status'],actual_prompt_tokens=annotation['observation']['input_sequence_length'],
    actual_generation_wall_sec=done['wall_sec'],accepted_done_sha256=t.sha(out/'done.json'),
    new_raw_answer_sha256=t.sha(out/'raw_answer.txt'),original_failed_raw_and_STOP_preserved=True,
    original_successful_and_new_accepted_records_unchanged=True,new_T_optimizer_updates=0,
    semantic_quality_or_training_admitted=False,raw_labels_or_per_frame_data_exported=False,large_transfers=0)
b=(json.dumps(v,ensure_ascii=False,indent=2)+chr(10)).encode();path=r/'controller/V11_real_first_generation_acceptance_20261008.json'
assert not path.exists();path.write_bytes(b);print(base64.b64encode(b).decode())
''' % REMOTE
    data = base64.b64decode(remote(script, echo=False))
    path = RUN/'controller/V11_real_first_generation_acceptance_20261008.json'
    assert not path.exists()
    path.write_bytes(data)
    print(json.dumps(json.loads(data), ensure_ascii=False))


if __name__ == '__main__':
    main()
