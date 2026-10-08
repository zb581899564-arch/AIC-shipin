"""Actual sorted legacy failure regression and exact complete supervision resume."""
from pathlib import Path
import copy
import json
from unittest.mock import patch
import teacher_label as teacher
import v11_resume as resume

def main():
    value=resume.load_manifest();records=teacher.rows(resume.OLD/'teacher_01/validated/validated_records.jsonl')
    by_id={r['window_id']:r for r in records};validator=teacher.validator_for(resume.RUN);checks=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,TypeError,KeyError):checks.append(name)
        else:raise AssertionError('must reject: '+name)
    for record in records:
        teacher.verify_model_decision_projection(record)
        validator.validate_window(record['window']);validator.validate_observation(record['window'],record['actual_observation'])
        validator.validate_response(record['window'],record['actual_observation'],record['parsed_answer'])
        assert resume.entry(record,value)['teacher_record_sha256']==teacher.canonical_sha(record)
    for identity in sorted(resume.LEGACY):
        record=by_id[identity]
        from v10_cache_reuse import approved_canonical_projection
        exact=json.dumps(approved_canonical_projection(record),ensure_ascii=False,allow_nan=False,separators=(',',':'))
        assert exact==record['raw_answer'] and teacher.text_sha(exact)==record['teacher']['canonical_answer_sha256']
        assert json.dumps(record['parsed_answer'],ensure_ascii=False,allow_nan=False,separators=(',',':'))!=exact
        for field,suffix in (('parsed_answer','projection'),('raw_answer','canonical_bytes'),('model_raw_answer','model_raw')):
            altered=copy.deepcopy(record)
            if field=='parsed_answer':altered[field]['decision_reason']+=' changed'
            else:altered[field]+=' '
            reject(identity+':changed_'+suffix,lambda:teacher.verify_model_decision_projection(altered))
    admission=teacher.read(resume.OLD/'teacher_admission.json')
    with patch.object(teacher,'inference',side_effect=AssertionError('CPU resume must never generate')):
        for row in value['reviews']:
            record=by_id[row['window_id']];old_review=teacher.read(Path(row['directory'])/'review_receipt.json')
            assert resume.approved_review(record,admission)==old_review
            actual=teacher.compare_selections(record['model_decision'],old_review['model_decision'],record['actual_observation'],
                approved_legacy_first=teacher.approved_legacy_record(record))
            assert actual==old_review['comparison'] and actual['support_class']==old_review['support_class']
        assert sum(resume.approved_review(record,admission) is None for record in records)==132
    bad=copy.deepcopy(records[0]);bad['window_id']='unapproved_window'
    reject('foreign_label',lambda:resume.entry(bad,value))
    bad=copy.deepcopy(records[0]);bad['teacher']['job_source_lock_sha256']='0'*64
    reject('changed_label_source_lock',lambda:resume.entry(bad,value))
    for key in ('runtime_revision','model_revision','max_sequence_length'):
        changed=copy.deepcopy(admission);changed[key]='wrong'
        reject('changed_admission_'+key,lambda:resume.approved_review(records[0],changed))
    row=value['reviews'][0];record=by_id[row['window_id']];review=teacher.read(Path(row['directory'])/'review_receipt.json')
    native_read,native_sha=resume.read,resume.sha;current_lock='1'*64
    def mocked_read(path):
        return {'job_source_lock_sha256':current_lock} if Path(path)==resume.HERE/'teacher_admission.json' else native_read(path)
    def mocked_sha(path):
        return current_lock if Path(path)==resume.HERE/'source_lock.json' else native_sha(path)
    with patch.object(resume,'read',side_effect=mocked_read),patch.object(resume,'sha',side_effect=mocked_sha):
        for prior in value['reviews']:
            first=by_id[prior['window_id']]
            actual_review=teacher.read(Path(prior['directory'])/'review_receipt.json')
            assert teacher.verify_blind_review_projection(actual_review,first,validator)==actual_review['comparison']
        resume.verify_review_job_binding(review,record)
        new=copy.deepcopy(review);new['second_teacher']['job_source_lock_sha256']=current_lock
        resume.verify_review_job_binding(new,record)
        changed=copy.deepcopy(review);changed['reason']+=' altered'
        reject('modified_old_review',lambda:resume.verify_review_job_binding(changed,record))
        changed=copy.deepcopy(review);changed['second_teacher']['job_source_lock_sha256']='2'*64
        reject('unapproved_reviewer_lock',lambda:resume.verify_review_job_binding(changed,record))
    for name in ('boundary_ids.py','teacher_prompt.txt','review_prompt.txt','train_student.py','production_t.py','source_color.py',
        'supervision/validate_teacher.py','supervision/select_windows.py',
        'supervision/teacher_metadata_20261007.json','supervision/teacher_response.schema.json'):
        assert teacher.sha(resume.HERE/name)==teacher.sha(resume.OLD/name)
    result=dict(status='PASS_V13_ACTUAL_SORTED_LEGACY_PROJECTION_AND_EXACT_RESUME_CPU',
        actual_original_records_checked=160,legacy_JSONL_regressions=2,completed_reviews_replayed=28,
        remaining_review_calls=132,rejection_tests=len(checks),rejection_names=checks,
        original_manifest_sha256=resume.sha(resume.MANIFEST),production_teacher_sha256=teacher.sha(resume.HERE/'teacher_label.py'),
        production_legacy_sha256=teacher.sha(resume.HERE/'v10_cache_reuse.py'),production_resume_sha256=teacher.sha(resume.HERE/'v11_resume.py'),
        original_validation_and_label_objects_unchanged=True,review_comparisons_unchanged=True,
        current_binding_tests_explicitly_mocked=True,actual_current_blind_validator_replayed=28,exact_original_dependency_files=2,new_model_calls=0,GPU_started=False,new_T_updates=0)
    resume.write(resume.HERE/'resume_cpu_acceptance.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
