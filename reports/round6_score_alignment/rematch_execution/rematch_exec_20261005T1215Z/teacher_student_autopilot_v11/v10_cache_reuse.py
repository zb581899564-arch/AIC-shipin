"""Exact two-record V10 import; frozen old validation runs in a separate process.

The old model answers, annotations and records retain their original bytes and
job identities. This is no general compatibility decoder for integer IDs.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
OLD = RUN / 'teacher_student_autopilot_v10'
MANIFEST = HERE / 'accepted_resume_manifest.json'
SCHEMA = 'AIC_EXACT_V10_TWO_SUCCESS_REUSE_V1'
OLD_LOCK_SHA = 'b36e260ece5abc0267f24cedf534add67588fb01ebc3c10e1e7f8ea5d65960cc'
PINS = {
    'complete_087af79e4b421be308d6cf6f': {
        'done.json': '28770e2c99799903728fccc1fb95d3a0bc257ac6269793eed9a7bcd68b056310',
        'annotation.json': 'b00829f037648333a835269e0a59477850e4ccd3de89a2db1d5ece3f2e6d8153',
        'validated_record.json': 'bf56f2e3004baf62df5db3ccbaa93a2bc3d7df2d11ed8c4962663ae77324e46a',
        'raw_answer.txt': '9a69daf5c853630802933c38cb5c717eb8eefa79f395963d23a0e251419c1852'},
    'complete_8ab21c80e0bff423c3ce016b': {
        'done.json': 'd1c70a5f957d2b022890d2a31692298915dcf51bb987d4a130e0be615dba746e',
        'annotation.json': 'fa5ba1c8e7f961bc370b9a109f66d2bcc857179b5c4a273e53126299fad17466',
        'validated_record.json': '69d5f238b9be12806ebfdb6cc93652da2bc4d297910fe0bc71dc936dabd9f24b',
        'raw_answer.txt': '63e1e9151161e2c11f52811eabbec7c67f364fa0b155f3927b9141eddeaa2375'},
}
FAILED_ID = 'complete_45666feb9bbc3d854e9d05c1'
_VALIDATED = None


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            result.update(chunk)
    return result.hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def original_directory(identity):
    require(identity in PINS, 'legacy window is not one of the two exact successes')
    return OLD / 'teacher_01/windows' / identity


def directory_snapshot(directory):
    require(directory.is_dir() and not directory.is_symlink(), 'original legacy directory missing or redirected')
    paths = sorted(path for path in directory.rglob('*') if path.is_file())
    require(all(not path.is_symlink() and directory.resolve() in path.resolve().parents for path in paths),
            'legacy file must remain inside its original directory')
    return {str(path): sha(path) for path in paths}


def evidence_paths():
    return [OLD/'source_lock.json', OLD/'completion.json', OLD/'teacher_01/teacher_probe_completion.json',
            OLD/'teacher_01/teacher_admission.json', OLD/'teacher_admission.json',
            OLD/'visual_probe_01/completion.json',
            RUN/'controller/rematch_TAUTO_v10_teacher_probe.resource.json',
            RUN/'controller/rematch_TAUTO_v10_teacher_visual_interface.resource.json']


def _validate_child():
    """No current teacher/boundary imports and no writes, model load or generation."""
    require(socket.gethostname() == 'inspur-NP5570M5', 'actual legacy validation is Linux-only')
    require(sha(OLD/'source_lock.json') == OLD_LOCK_SHA, 'frozen V10 source lock changed')
    lock = read(OLD/'source_lock.json')
    verified_hashes = {}
    # One complete frozen-lock audit per consumer process, never once per review.
    for path, digest in lock['files'].items():
        verified_hashes[path] = sha(path)
        require(verified_hashes[path] == digest, 'frozen original source bytes changed: ' + path)
    sys.path.insert(0, str(OLD))
    import teacher_label as old_teacher
    import boundary_ids as old_boundary
    require(Path(old_teacher.__file__).resolve() == (OLD/'teacher_label.py').resolve() and
            Path(old_boundary.__file__).resolve() == (OLD/'boundary_ids.py').resolve(), 'legacy helper module identity mixed')
    validator = old_teacher.validator_for(RUN)
    require(Path(validator.__file__).resolve() == (OLD/'supervision/validate_teacher.py').resolve(),
            'original structural validator identity mixed')
    probe = read(OLD/'teacher_01/teacher_probe_completion.json')
    require(probe['status'] == 'PASS_REAL_NONTEST_TEACHER_PROBE' and set(probe['window_ids']) == set(PINS),
            'original two successful heavy probes differ')
    require(probe['admission_sha256'] == sha(OLD/'teacher_01/teacher_admission.json'), 'old probe admission binding changed')
    require(read(OLD/'completion.json')['status'] == 'STOP_AUTOPILOT_PRESERVED', 'old scientific/engineering STOP missing')
    full = {window['window_id']:window for split in ('train','dev')
            for window in rows(OLD/'selection_01'/('selected_'+split+'.jsonl'))}
    pilot = {window['window_id']:window for split in ('train','dev')
             for window in rows(OLD/'pilot_selection'/('selected_'+split+'.jsonl'))}
    accepted = []
    for identity in sorted(PINS):
        directory = original_directory(identity)
        before = directory_snapshot(directory)
        require(len(before) == 82 and all(sha(directory/name) == digest for name,digest in PINS[identity].items()),
                'pinned original successful bytes changed')
        done, annotation, original = (read(directory/name) for name in ('done.json','annotation.json','validated_record.json'))
        require(len(done['files']) == 17 and all(sha(directory/name) == digest for name,digest in done['files'].items()),
                'all original done-file SHA bindings required')
        frame_paths = {str(Path(frame['path'])) for frame in annotation['observation']['frame_files']}
        require(set(before) == {str(directory/name) for name in done['files']} | frame_paths | {str(directory/'done.json')},
                'original complete 82-file set differs')
        require(done['window_sha256'] == canonical_sha(original['window']) and original['window'] == full[identity] and
                identity not in pilot, 'old success must be exact full160 member and not pilot24')
        require(probe['probe_receipts'][identity]['done_sha256'] == sha(directory/'done.json') and
                probe['probe_receipts'][identity]['annotation_sha256'] == sha(directory/'annotation.json'),
                'original heavy probe receipt SHA differs')
        require(original['status'] == 'PASS_WEAK_COMPLETE_WINDOW_TARGET' and original['sft_eligible'] is True and
                annotation['teacher']['job_source_lock_sha256'] == OLD_LOCK_SHA, 'only original valid weak targets can be reused')
        require(annotation['model_raw_answer'] == (directory/'raw_answer.txt').read_bytes().decode('utf-8'), 'exact old raw alias differs')
        recomputed = validator.make_record(original['window'], annotation['observation'], annotation['teacher'], annotation['raw_answer'])
        require(recomputed == original, 'isolated frozen original validator does not reproduce the exact record')
        old_teacher.verify_model_decision_projection(original)
        old_teacher.frame_content(annotation['observation'])
        require(sha(original['window']['source_path']) == original['window']['source_sha256'], 'old source video bytes changed')
        for weight in annotation['teacher']['weight_files']:
            if weight['path'] not in verified_hashes:
                verified_hashes[weight['path']] = sha(weight['path'])
            require(Path(weight['path']).is_file() and Path(weight['path']).stat().st_size == weight['bytes'] and
                    verified_hashes[weight['path']] == weight['sha256'], 'actual official teacher weight bytes changed')
        request, response = read(directory/'http/request.json'), read(directory/'server_response.json')
        require(request.get('grammar') == response['__verbose']['generation_settings']['grammar'] ==
                (directory/'generation_grammar.gbnf').read_text(encoding='utf-8') and 'response_format' not in request and
                response['__verbose']['generation_settings']['grammar_lazy'] is False and
                response['choices'][0]['message']['content'] == annotation['model_raw_answer'], 'original applied grammar/response binding differs')
        require(directory_snapshot(directory) == before, 'original directory changed during CPU revalidation')
        accepted.append({'window_id':identity, 'split':original['split'], 'directory':str(directory),
            'source_format':'V10_GLOBAL_INTEGER_EVIDENCE_IDS', 'files':before,
            'teacher_record_sha256':canonical_sha(original), 'window_sha256':canonical_sha(original['window']),
            'observation_sha256':canonical_sha(annotation['observation']), 'teacher_sha256':canonical_sha(annotation['teacher']),
            'canonical_answer_sha256':hashlib.sha256(annotation['raw_answer'].encode()).hexdigest(),
            'source_sha256':original['window']['source_sha256'], 'original_validator_sha256':sha(OLD/'supervision/validate_teacher.py'),
            'in_full160':True, 'in_pilot24':False, 'original_record_exactly_reproduced':True,
            'isolated_original_validator':True, 'old_bytes_unchanged':True})
    visual = read(OLD/'visual_probe_01/completion.json')
    require(visual['status'] == 'PASS_REAL_SYNTHETIC_VISUAL_INTERFACE' and visual['case_count'] == visual['real_model_calls'] == 8 and
            all(case['pass'] is True for case in visual['cases']), 'original eight visual cases incomplete')
    for path in evidence_paths()[-2:]:
        require(read(path)['status'] == 'completed', 'original successful GPU resource evidence missing')
    return {'schema':SCHEMA, 'status':'PASS_EXACT_V10_SUCCESS_REUSE_CPU', 'old_source_lock_sha256':OLD_LOCK_SHA,
        'accepted':accepted, 'failed_window_ids':[FAILED_ID], 'evidence_files':{str(path):sha(path) for path in evidence_paths()},
        'GPU_started':False, 'real_model_calls':0, 'old_successful_generation_repeated':False,
        'original_complete_source_lock_SHA_verified':True, 'original_validator_sha256':sha(OLD/'supervision/validate_teacher.py')}


def _isolated_validation():
    result = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), '--validate-child'],
        cwd=OLD, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=7200)
    require(result.returncode == 0, 'isolated frozen V10 CPU validation failed: ' + result.stderr[-2000:])
    value = json.loads(result.stdout)
    require(value.get('status') == 'PASS_EXACT_V10_SUCCESS_REUSE_CPU' and value.get('GPU_started') is False,
            'isolated legacy validation returned no real proof')
    return value


def _load_manifest():
    require(MANIFEST.is_file(), 'exact legacy reuse manifest not prepared')
    current_lock = HERE/'source_lock.json'
    if current_lock.exists():
        require(read(current_lock)['files'].get(str(MANIFEST)) == sha(MANIFEST), 'current job did not freeze this exact legacy manifest')
    elif any((HERE/name).exists() for name in ('registration.json','start_receipt.json')):
        raise ValueError('registered legacy consumer lacks a frozen manifest')
    value = read(MANIFEST)
    require(value.get('schema') == SCHEMA and value.get('status') == 'PASS_EXACT_V10_SUCCESS_REUSE_CPU' and
            value.get('old_source_lock_sha256') == OLD_LOCK_SHA and value.get('GPU_started') is False and
            len(value.get('accepted', [])) == 2 and {row.get('window_id') for row in value['accepted']} == set(PINS),
            'exact two-record legacy manifest differs')
    for row in value['accepted']:
        directory = original_directory(row['window_id'])
        require(row.get('directory') == str(directory) and len(row.get('files', {})) == 82 and
                all(row['files'].get(str(directory/name)) == digest for name,digest in PINS[row['window_id']].items()) and
                row.get('in_full160') is True and row.get('in_pilot24') is False, 'legacy manifest cannot authorize changed or failed data')
    return value


def _ensure_authority(manifest):
    global _VALIDATED
    require(sha(OLD/'source_lock.json') == OLD_LOCK_SHA, 'original frozen V10 authority changed')
    if _VALIDATED is None:
        _VALIDATED = _isolated_validation()
    require(manifest == _VALIDATED, 'legacy manifest differs from isolated original SHA/validator proof')
    for path,digest in manifest['evidence_files'].items():
        require(sha(path) == digest, 'original probe/model/resource identity changed: ' + path)


def _approved_entry(identity):
    manifest = _load_manifest()
    _ensure_authority(manifest)
    row = next(row for row in manifest['accepted'] if row['window_id'] == identity)
    require(directory_snapshot(original_directory(identity)) == row['files'], 'original successful legacy directory bytes changed')
    return row


def verify_approved_annotation(window):
    identity = window.get('window_id') if isinstance(window, dict) else None
    if identity not in PINS:
        return None
    row = _approved_entry(identity)
    require(canonical_sha(window) == row['window_sha256'], 'approved legacy window changed; cannot regenerate a prior success')
    annotation = read(original_directory(identity)/'annotation.json')
    require(canonical_sha(annotation['observation']) == row['observation_sha256'] and
            canonical_sha(annotation['teacher']) == row['teacher_sha256'], 'approved original annotation projection changed')
    return annotation


def verify_approved_record(record):
    identity = record.get('window_id') if isinstance(record, dict) else None
    if identity not in PINS:
        return False
    manifest = _load_manifest()
    row = next(row for row in manifest['accepted'] if row['window_id'] == identity)
    if canonical_sha(record) != row['teacher_record_sha256']:
        return False
    row = _approved_entry(identity)
    require(record == read(original_directory(identity)/'validated_record.json'), 'legacy approval requires exact original record')
    return True


def approved_original_record(window, observation, teacher, canonical_answer):
    identity = window.get('window_id') if isinstance(window, dict) else None
    if identity not in PINS:
        return None
    row = next(row for row in _load_manifest()['accepted'] if row['window_id'] == identity)
    if (canonical_sha(window) != row['window_sha256'] or canonical_sha(observation) != row['observation_sha256'] or
            canonical_sha(teacher) != row['teacher_sha256'] or not isinstance(canonical_answer, str) or
            hashlib.sha256(canonical_answer.encode()).hexdigest() != row['canonical_answer_sha256']):
        return None
    _approved_entry(identity)
    original = read(original_directory(identity)/'validated_record.json')
    require(original['raw_answer'] == canonical_answer, 'original canonical answer bytes differ')
    return original


def approved_canonical_projection(record):
    require(verify_approved_record(record), 'canonical projection requires exact approved original record')
    return copy.deepcopy(record['parsed_answer'])


def original_probe_evidence():
    manifest = _load_manifest()
    _ensure_authority(manifest)
    for identity in PINS:
        _approved_entry(identity)
    return (read(OLD/'teacher_01/teacher_probe_completion.json'),
            read(RUN/'controller/rematch_TAUTO_v10_teacher_probe.resource.json'),
            read(RUN/'controller/rematch_TAUTO_v10_teacher_visual_interface.resource.json'))


def prepare_manifest():
    global _VALIDATED
    require(socket.gethostname() == 'inspur-NP5570M5', 'manifest preparation is Linux CPU only')
    require(not any((HERE/name).exists() for name in ('source_lock.json','registration.json','start_receipt.json')),
            'cannot prepare or rewrite a frozen/registered reuse manifest')
    if MANIFEST.exists():
        existing = read(MANIFEST)
        if existing.get('schema') == SCHEMA:
            _ensure_authority(_load_manifest())
            return existing
        require(existing.get('accepted') == [], 'refuse to replace any preexisting nonempty authorization')
    value = _isolated_validation()
    require(all(sha(path) == digest for path,digest in value['evidence_files'].items()), 'legacy evidence changed before manifest write')
    temporary = MANIFEST.with_suffix('.json.tmp')
    with temporary.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    temporary.replace(MANIFEST)
    _VALIDATED = value
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--validate-child', action='store_true')
    args = parser.parse_args()
    value = _validate_child() if args.validate_child else prepare_manifest()
    if args.validate_child:
        print(json.dumps(value, ensure_ascii=False, allow_nan=False))
    else:
        print(json.dumps({'status':value['status'], 'accepted_count':len(value['accepted']),
            'manifest_sha256':sha(MANIFEST), 'GPU_started':False, 'old_bytes_changed':False}))
