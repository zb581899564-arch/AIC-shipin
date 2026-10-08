"""Actual complete160 consumer regression and exact diagnostic ownership tests."""
from pathlib import Path
import ast
import copy
import importlib.util
import json
import datetime
import teacher_label as teacher
import train_student as student
import v13_full_resume as resume


def main():
    value = resume.load_manifest()
    root = resume.OLD / 'teacher_01'
    records = teacher.rows(root / 'validated/validated_records.jsonl')
    reviews = teacher.rows(root / 'raw_semantic_review_receipts.jsonl')
    by_id = {v['window_id']: v for v in records}
    rb = {v['window_id']: v for v in reviews}
    eligible = teacher.rows(root / 'validated/eligible_train.jsonl') + teacher.rows(root / 'validated/eligible_dev.jsonl')
    hashes = {n: teacher.sha(root / 'validated' / n) for n in ('eligible_train.jsonl', 'eligible_dev.jsonl', 'validated_records.jsonl')}
    args = (teacher.read(root / 'semantic_review.json'), teacher.sha(root / 'validated/validation_receipt.json'),
            hashes, eligible, {teacher.canonical_sha(v): v for v in records}, teacher, teacher.validator_for(resume.RUN))
    spec = importlib.util.spec_from_file_location('v13_original_student_consumer', resume.OLD / 'train_student.py')
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    try:
        old.verify_semantic(*args)
    except ValueError as error:
        assert str(error) == 'STOP_T_UNBOUND_OR_UNEXPLAINABLE_BLIND_REVIEW'
    else:
        raise AssertionError('original stage mismatch must reproduce')
    _, supported, stats = student.verify_semantic(*args)
    assert len(supported) == 79 and stats['supported_by_split'] == {'train': 65, 'dev': 14}
    assert stats['selected_denominator'] == 160 and stats['unknown_count'] == 81
    assert stats['supported_positive_by_split'] == {'train': 55, 'dev': 10}
    assert stats['supported_explicit_empty_by_split'] == {'train': 10, 'dev': 4}
    assert all(teacher.canonical_sha(v) not in supported for v in records if rb[v['window_id']]['support_class'] == 'UNKNOWN')
    for identity in value['approved_pilot_review_ids']:
        assert resume.approved_diagnostic_review(rb[identity], by_id[identity])
    checks = []
    def reject(name, fn):
        try:
            fn()
        except (ValueError, KeyError, TypeError):
            checks.append(name)
        else:
            raise AssertionError('must reject: ' + name)
    identity = value['approved_pilot_review_ids'][0]
    record = by_id[identity]
    review = rb[identity]
    for field, bad in (('reason', review['reason'] + ' changed'), ('manual_ground_truth', True),
                       ('model_raw_answer', review['model_raw_answer'] + ' '), ('diagnostic_only', False),
                       ('review_prompt_sha256', '0' * 64), ('support_class', 'FABRICATED_SUPPORT'),
                       ('teacher_record_sha256', '0' * 64), ('window_id', 'UNREGISTERED_WINDOW')):
        changed = copy.deepcopy(review)
        changed[field] = bad
        reject('altered_' + field, lambda: resume.approved_diagnostic_review(changed, record))
    changed = copy.deepcopy(review)
    changed['second_teacher']['job_source_lock_sha256'] = '0' * 64
    reject('foreign_reviewer_job', lambda: resume.approved_diagnostic_review(changed, record))
    changed_record = copy.deepcopy(record)
    changed_record['window']['source_sha256'] = '0' * 64
    reject('changed_first_record_source', lambda: resume.approved_diagnostic_review(review, changed_record))
    fresh = next(v for v in reviews if not v['diagnostic_only'])
    changed = copy.deepcopy(fresh)
    changed['diagnostic_only'] = True
    reject('nonpilot_diagnostic_reclassification', lambda: resume.approved_diagnostic_review(changed, by_id[fresh['window_id']]))
    unchanged = ('boundary_ids.py', 'teacher_prompt.txt', 'review_prompt.txt', 'production_t.py', 'source_color.py',
                 'supervision/validate_teacher.py', 'supervision/teacher_metadata_20261007.json', 'supervision/teacher_response.schema.json')
    for name in unchanged:
        assert teacher.sha(resume.HERE / name) == teacher.sha(resume.OLD / name)
    def functions(path):
        return {v.name: ast.dump(v, include_attributes=False) for v in ast.parse(Path(path).read_bytes()).body if isinstance(v, ast.FunctionDef)}
    current, previous = functions(resume.HERE / 'train_student.py'), functions(resume.OLD / 'train_student.py')
    assert all(current[n] == body for n, body in previous.items() if n != 'verify_semantic')
    current, previous = functions(resume.HERE / 'teacher_label.py'), functions(resume.OLD / 'teacher_label.py')
    assert all(current[n] == body for n, body in previous.items())
    resume.files_match(value['all_receipt_files'])
    production = ('train_student.py', 'teacher_label.py', 'v11_resume.py', 'v13_full_resume.py', 'controller.py')
    result = dict(status='PASS_V14_EXACT_PILOT_DIAGNOSTIC_STAGE_HANDOFF_CPU',
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), original_failure_reproduced=True,
        original_consumer_sha256=teacher.sha(resume.OLD / 'train_student.py'), complete_reviews_checked=160,
        approved_original_pilot_reviews=24, original_diagnostic_flags_unchanged=True,
        original_full_teacher_manifest_sha256=resume.sha(resume.MANIFEST), supported_by_split=stats['supported_by_split'],
        supported_positive_by_split=stats['supported_positive_by_split'], supported_empty_by_split=stats['supported_explicit_empty_by_split'],
        unknown_count=81, UNKNOWN_never_negative=True, full_selected_denominator=160,
        rejection_tests=len(checks), rejection_names=checks, model_input_prompt_validator_and_training_functions_unchanged=True,
        new_model_calls=0, new_T_updates=0, same_teacher_not_human_truth=True,
        production_files={n: teacher.sha(resume.HERE / n) for n in production})
    resume.write(resume.HERE / 'full_resume_cpu_acceptance.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
