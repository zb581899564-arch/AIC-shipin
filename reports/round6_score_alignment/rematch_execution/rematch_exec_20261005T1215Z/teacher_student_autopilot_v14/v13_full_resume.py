"""Exact full-teacher handoff; diagnostic flags and UNKNOWN stay unchanged."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil
import socket
import sys

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
OLD = RUN / 'teacher_student_autopilot_v13'
MANIFEST = HERE / 'v13_full_resume_manifest.json'
OLD_LOCK = '620df12b8cd6bb85d3bf64fc120314d400d30aa9887dfc0a58d0d4152ede8159'
SCHEMA = 'AIC_EXACT_V13_COMPLETE_TEACHER_STAGE_HANDOFF_V1'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8-sig').splitlines() if x.strip()]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def files_match(files):
    for name, expected in files.items():
        p = Path(name)
        require(p.is_file() and not p.is_symlink() and sha(p) == expected,
                'complete teacher evidence changed: ' + name)


def load_manifest():
    value = read(MANIFEST)
    require(value['schema'] == SCHEMA and value['original_source_lock_sha256'] == OLD_LOCK and
            value['original_label_count'] == value['original_review_count'] == 160 and
            len(value['reviews']) == 160 and len(value['approved_pilot_review_ids']) == 24 and
            value['new_teacher_calls'] == 0 and value['manual_ground_truth'] is False,
            'complete teacher stage authority differs')
    if (HERE / 'source_lock.json').exists():
        require(read(HERE / 'source_lock.json')['files'].get(str(MANIFEST)) == sha(MANIFEST),
                'complete teacher authority not source-bound')
    files_match(value['authority_files'])
    return value


def review_entry(review, record, value=None):
    value = value or load_manifest()
    matches = [v for v in value['reviews'] if v['window_id'] == record.get('window_id')]
    require(len(matches) == 1, 'review outside exact complete160 authority')
    item = matches[0]
    require(item['teacher_record_sha256'] == digest(record) and item['review_sha256'] == digest(review),
            'review or original label differs from exact authority')
    require(review['teacher_record_sha256'] == item['teacher_record_sha256'] and
            review['second_teacher']['job_source_lock_sha256'] == item['original_reviewer_job_lock_sha256'] and
            review['diagnostic_only'] is item['diagnostic_only'], 'original review ownership/diagnostic flag changed')
    files_match(item['files'])
    require(read(Path(item['directory']) / 'review_receipt.json') == review,
            'complete review differs from original immutable file')
    return item


def verify_review_binding(review, record):
    review_entry(review, record)


def approved_diagnostic_review(review, record):
    require(review.get('diagnostic_only') is True, 'diagnostic stage exception requires original True flag')
    value = load_manifest()
    item = review_entry(review, record, value)
    require(item['window_id'] in value['approved_pilot_review_ids'] and
            item['directory'].startswith(str(RUN / 'teacher_student_autopilot_v11/teacher_01/reviews') + '/') and
            item['original_reviewer_job_lock_sha256'] == '0ae09ec38ff589baa5e15e16b84457b06442195de502ec7ef6a19bab9b715578',
            'only exact successful registered original pilot24 may cross stages')
    return True


def prepare_manifest():
    require(socket.gethostname() == 'inspur-NP5570M5', 'original evidence is Linux only')
    require(not any((HERE / n).exists() for n in ('source_lock.json', 'registration.json', 'start_receipt.json')) and
            not MANIFEST.exists(), 'never reseal a complete teacher authority')
    require(sha(OLD / 'source_lock.json') == OLD_LOCK, 'original V13 lock differs')
    terminal = read(OLD / 'completion.json')
    cpu_failure = read_cpu_failure(OLD / 'student_admission.cpu.log')
    require(terminal['status'] == 'STOP_AUTOPILOT_PRESERVED' and
            terminal['reason'] == 'CPU stage did not complete: student_admission' and
            cpu_failure['failure'] == 'ValueError: STOP_T_UNBOUND_OR_UNEXPLAINABLE_BLIND_REVIEW' and
            cpu_failure['training_started'] is False and cpu_failure['optimizer_steps'] == 0,
            'unexpected original student admission failure')
    require(not (OLD / 'student_01').exists(), 'original student unexpectedly ran')
    completed = OLD / 'teacher_01'
    semantic = read(completed / 'semantic_review.json')
    require(semantic['status'] == 'PASS_AUTOMATED_WEAK_SEMANTIC_REVIEW' and
            semantic['selected_denominator'] == 160 and semantic['unknown_count'] == 81 and
            semantic['supported_by_split'] == {'train': 65, 'dev': 14} and
            semantic['manual_ground_truth'] is False, 'original complete weak review differs')
    old_manifest = read(OLD / 'v11_resume_manifest.json')
    old_by_id = {v['window_id']: v for v in old_manifest['reviews']}
    records = {v['window_id']: v for v in rows(completed / 'validated/validated_records.jsonl')}
    reviews = rows(completed / 'raw_semantic_review_receipts.jsonl')
    require(len(records) == len(reviews) == 160, 'full denominator differs')
    pilot = RUN / 'teacher_student_autopilot_v11/pilot_01'
    pilot_terminal = read(pilot / 'completion.json')
    require(pilot_terminal['status'] == 'PASS_REAL_PILOT_READY_FOR_FULL_RELABEL' and
            pilot_terminal['selected_denominator'] == 24 and pilot_terminal['student_training_admitted'] is False,
            'original pilot collection evidence differs')
    pilot_ids = {v['window_id'] for v in rows(pilot / 'raw_semantic_review_receipts.jsonl')}
    require(len(pilot_ids) == 24, 'registered pilot set differs')
    entries = []
    all_files = {}
    for review in reviews:
        identity = review['window_id']
        directory = Path(old_by_id[identity]['directory']) if identity in old_by_id else completed / 'reviews' / identity
        done = read(directory / 'done.json')
        require(read(directory / 'review_receipt.json') == review and
                done['teacher_record_sha256'] == digest(records[identity]), 'original done/raw aggregate differs')
        files = {str(directory / n): s for n, s in done['files'].items()}
        files[str(directory / 'done.json')] = sha(directory / 'done.json')
        files_match(files)
        require(review['diagnostic_only'] is (identity in pilot_ids), 'diagnostic stage set differs')
        entries.append(dict(window_id=identity, directory=str(directory), files=files,
                            teacher_record_sha256=digest(records[identity]), review_sha256=digest(review),
                            diagnostic_only=review['diagnostic_only'],
                            original_reviewer_job_lock_sha256=review['second_teacher']['job_source_lock_sha256']))
        all_files.update(files)
    resource = RUN / 'controller/rematch_TAUTO_v13_teacher_review.resource.json'
    cost = read(resource)
    require(cost['status'] == 'completed' and cost['exit_code'] == 0 and cost['stop_reason'] is None and
            cost['charged_seconds'] == 5493.750158078037, 'actual teacher termination/cost differs')
    originals = [OLD / 'source_lock.json', OLD / 'completion.json', OLD / 'student_admission.cpu.log',
                 OLD / 'teacher_admission.json', OLD / 'v11_resume_manifest.json', resource,
                 completed / 'semantic_review.json', completed / 'raw_semantic_review_receipts.jsonl',
                 completed / 'annotation_receipts.jsonl', completed / 'teacher_completion.json',
                 pilot / 'completion.json', pilot / 'raw_semantic_review_receipts.jsonl',
                 RUN / 'controller/V11_real_pilot_acceptance_20261008.json',
                 *sorted((completed / 'validated').glob('*.json*'))]
    value = dict(schema=SCHEMA, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 original_source_lock_sha256=OLD_LOCK, original_label_count=160, original_review_count=160,
                 original_completed_review_calls=28, V13_actual_new_review_calls=132,
                 approved_pilot_review_ids=sorted(pilot_ids), reviews=entries,
                 authority_files={str(p): sha(p) for p in originals}, all_receipt_files=all_files,
                 original_gpu_charged_seconds=cost['charged_seconds'], new_teacher_calls=0,
                 manual_ground_truth=False, original_diagnostic_flags_and_UNKNOWN_unchanged=True)
    write(MANIFEST, value)
    print(json.dumps(dict(status='PASS_EXACT_COMPLETE160_MANIFEST_REGISTERED', sha256=sha(MANIFEST),
                         diagnostic_stage_exception_count=24, new_teacher_calls=0)), flush=True)


def read_cpu_failure(path):
    lines = Path(path).read_text().splitlines()
    require(len(lines) == 1, 'unexpected student failure log')
    return json.loads(lines[0])


def handoff():
    import autopilot_common as common
    import teacher_label as t
    import train_student as student
    common.verify()
    value = load_manifest()
    files_match(value['all_receipt_files'])
    target = HERE / 'teacher_01'
    require(not target.exists() and not (HERE / 'teacher_admission.json').exists(), 'complete handoff is once-only')
    (target / 'validated').mkdir(parents=True)
    for name in ('annotation_receipts.jsonl', 'teacher_completion.json', 'semantic_review.json', 'raw_semantic_review_receipts.jsonl',
                 'validated/validated_records.jsonl', 'validated/eligible_train.jsonl', 'validated/eligible_dev.jsonl',
                 'validated/validation_receipt.json'):
        src = OLD / 'teacher_01' / name
        shutil.copyfile(src, target / name)
        require((target / name).read_bytes() == src.read_bytes(), 'complete aggregate copy differs')
    shutil.copyfile(OLD / 'teacher_admission.json', HERE / 'teacher_admission.json')
    records = t.rows(target / 'validated/validated_records.jsonl')
    eligible = t.rows(target / 'validated/eligible_train.jsonl') + t.rows(target / 'validated/eligible_dev.jsonl')
    hashes = {n: t.sha(target / 'validated' / n) for n in ('eligible_train.jsonl', 'eligible_dev.jsonl', 'validated_records.jsonl')}
    _, supported, stats = student.verify_semantic(t.read(target / 'semantic_review.json'),
        t.sha(target / 'validated/validation_receipt.json'), hashes, eligible,
        {t.canonical_sha(v): v for v in records}, t, t.validator_for(RUN))
    require(len(supported) == 79 and stats['unknown_count'] == 81 and stats['supported_by_split'] == {'train': 65, 'dev': 14},
            'exact full review support differs')
    write(HERE / 'full_resume_handoff.json', dict(status='PASS_EXACT_V13_COMPLETE_TEACHER_HANDOFF_NO_NEW_CALLS',
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), manifest_sha256=sha(MANIFEST),
        original_labels=160, original_reviews=160, registered_pilot_diagnostic_flags_preserved=24,
        supported_by_split=stats['supported_by_split'], unknown_count=81, new_teacher_calls=0,
        new_T_updates_by_handoff=0, original_GPU_charged_seconds=value['original_gpu_charged_seconds'],
        same_teacher_consistency_not_human_truth=True, all_original_bytes_unchanged=True))
    print('PASS_COMPLETE_TEACHER_CPU_HANDOFF', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-manifest', action='store_true')
    parser.add_argument('--handoff', action='store_true')
    args = parser.parse_args()
    if args.prepare_manifest:
        prepare_manifest()
    elif args.handoff:
        handoff()
    else:
        parser.error('choose --prepare-manifest or --handoff')
