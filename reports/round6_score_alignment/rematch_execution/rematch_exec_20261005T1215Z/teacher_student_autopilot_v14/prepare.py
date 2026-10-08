"""Freeze the exact complete teacher handoff and narrowly repaired consumer."""
from autopilot_common import *
import socket
import v13_full_resume as resume


def main():
    require(socket.gethostname() == 'inspur-NP5570M5', 'wrong preparation host')
    require(not any((HERE / n).exists() for n in ('source_lock.json', 'registration.json', 'start_receipt.json')), 'never reseal')
    accepted = read(HERE / 'full_resume_cpu_acceptance.json')
    require(accepted['status'] == 'PASS_V14_EXACT_PILOT_DIAGNOSTIC_STAGE_HANDOFF_CPU' and
            accepted['original_failure_reproduced'] is True and accepted['complete_reviews_checked'] == 160 and
            accepted['supported_by_split'] == {'train': 65, 'dev': 14} and accepted['unknown_count'] == 81 and
            accepted['approved_original_pilot_reviews'] == 24 and accepted['rejection_tests'] >= 10 and
            accepted['new_model_calls'] == 0 and accepted['new_T_updates'] == 0,
            'actual complete consumer acceptance required')
    for name, expected in accepted['production_files'].items():
        require(sha(HERE / name) == expected, 'accepted production changed: ' + name)
    manifest = resume.load_manifest()
    files = dict(read(resume.OLD / 'source_lock.json')['files'])
    files[str(resume.OLD / 'source_lock.json')] = sha(resume.OLD / 'source_lock.json')
    files.update(manifest['authority_files'])
    files.update(manifest['all_receipt_files'])
    for directory in ('selection_01', 'pilot_selection'):
        for p in (HERE / directory).rglob('*'):
            if p.is_file():
                original = resume.OLD / directory / p.relative_to(HERE / directory)
                require(p.read_bytes() == original.read_bytes(), 'original selection changed')
    for p in HERE.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.name != 'source_lock.json':
            files[str(p)] = sha(p)
    for path, expected in files.items():
        require(sha(path) == expected, 'immutable source/receipt changed: ' + path)
    write(HERE / 'source_lock.json', dict(schema='AIC_TEACHER_STUDENT_SOURCE_LOCK_V14', utc=utc(), files=files,
        predecessor_source_lock_sha256=resume.OLD_LOCK, exact_complete_teacher_manifest_sha256=sha(resume.MANIFEST),
        original_STOP_and_diagnostic_flags_preserved=True, original_labels=160, original_reviews=160,
        new_teacher_calls=0, same_teacher_consistency_not_truth=True, original_model_input_science_unchanged=True,
        actual_capacity_only=True, teacher_is_offline_only=True), fresh=True)
    print(json.dumps(dict(status='PASS_V14_COMPLETE_TEACHER_SOURCE_BINDING', files=len(files),
                          source_lock_sha256=sha(HERE / 'source_lock.json'))), flush=True)


if __name__ == '__main__':
    main()
