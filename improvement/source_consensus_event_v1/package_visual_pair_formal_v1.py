"""One CPU package from accepted formal visual rejections; never run a model.

Run only after all316 outputs and the unique successful GPU wrapper are accepted.
Existing baseline, proposals, boxes, histories and packages remain immutable.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import datetime as dt
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
import traceback
import uuid
import zipfile

W = Path('/home/inspur/aic_video_work')
ROOT = W/'visual_pair_formal_20261018_v1'
RELATIVE = W/'relative_precision_event_20261018_v1'
EVENT = W/'meaningful_residual_20261018_v1'
OLD = W/'semantic_context_production_20261016_v1'
SOURCE_CLEAR = W/'source_clear_residual_20261018_v1'
RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY = W/'env/qwen3vl_isolated_20260910/bin/python'
PARAMETERS = 8782692681
BASE_SHA = 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def ref(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest.hexdigest())


def bound(value):
    path = Path(value['path'])
    actual = ref(path)
    require(actual['sha256'] == value['sha256'] and
            ('bytes' not in value or actual['bytes'] == value['bytes']), 'Changed binding: '+str(path))
    return path


def save(path, value):
    with Path(path).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def deadline(registration):
    fixed = dt.datetime(2026, 10, 18, 15, 50, tzinfo=dt.timezone.utc)
    registered = dt.datetime.fromisoformat(registration['production_cutoff_utc'].replace('Z', '+00:00'))
    require(dt.datetime.now(dt.timezone.utc) < min(fixed, registered), 'Production cutoff15:50Z reached')


def canonical(rows):
    value = [{key: row[key] for key in ('video_id', 'targetRatioWH', 'predictions')}
             for row in sorted(rows, key=lambda row: row['video_id'])]
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def histories(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in ('canonical_sha256', 'canonical_SHA256', 'prediction_sha256',
                       'canonical_prediction_sha256') and isinstance(child, str):
                yield child
            else:
                yield from histories(child)
    elif isinstance(value, list):
        for child in value:
            yield from histories(child)


def archive_rows(path):
    with zipfile.ZipFile(path) as archive:
        require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None,
                'Adopted package must have one CRC-valid JSONL member')
        return [json.loads(line) for line in archive.read('predictions.jsonl').splitlines() if line.strip()]


def frame_boxes(rows):
    result = {}
    require(len(rows) == 426 and {row['video_id'] for row in rows} == set(map(str, range(426))),
            'Complete exact426 source set')
    for row in rows:
        require(bool(row['predictions']), 'All426 sources must remain nonempty')
        for prediction in row['predictions']:
            key = row['video_id'], prediction['frame']
            require(type(key[1]) is int and key not in result, 'Unique integer native frame required')
            result[key] = prediction['bboxes']
    return result


def terminal_and_outputs(registration, acceptance):
    require(str(acceptance['status']).startswith('PASS'), 'First complete independent output QA required')
    completion_path = bound(acceptance['gpu_completion_ref'])
    require(completion_path.resolve() == (ROOT/'gpu_01/completion.json').resolve(), 'Use this formal GPU completion')
    completion = read(completion_path)
    require(completion['status'] == 'PASS_REGISTERED_ACTUAL_BASE_PREFERENCES_NO_OPTIMIZER'
            and len(completion['outputs']) == 316, 'Real316 successful formal BASE outputs required')
    bound(completion['identity_ref'])
    terminal_path = bound(acceptance['resource_ref'])
    terminal = read(terminal_path)
    require(terminal_path.resolve() == (RUN/'controller'/(terminal['name']+'.resource.json')).resolve(),
            'Exact shared-wrapper resource path')
    require(terminal['status'] == 'completed' and terminal.get('exit_code') == 0
            and terminal.get('stop_reason') is None, 'Only a naturally successful wrapper terminal admits packaging')
    command = terminal['command']
    require(len(command) == 4 and Path(command[0]).resolve() == PY.resolve() and command[1] == '-B'
            and command[3] == 'gpu' and Path(command[2]).resolve().is_relative_to(ROOT.resolve()),
            'GPU terminal must execute this formal root, including an explicit recovered code version')
    ledger_path = W/'improvement_round1/gpu_ledger.jsonl'
    matches = [json.loads(line) for line in ledger_path.read_text().splitlines()
               if line.strip() and json.loads(line).get('name') == terminal['name']]
    require(matches == [terminal], 'Unique ledger record must exactly equal the successful resource terminal')
    refs = acceptance['all316ref']
    require(isinstance(refs, list) and len(refs) == 316
            and len({value['path'] for value in refs}) == 316,
            'Acceptance must bind exactly316 unique output refs')
    require({json.dumps(value, sort_keys=True) for value in refs} ==
            {json.dumps(value, sort_keys=True) for value in completion['outputs']},
            'Accepted outputs must be exactly the real GPU completion outputs')
    choices = {}
    for value in refs:
        done = read(bound(value))
        key = done['sid'], done['order']
        require(key not in choices and done['status'] == 'ACTUAL_MODEL_PREFERENCE_OK'
                and done['choice'] in ('A', 'B', 'TIE', 'NEITHER'), 'Accepted output identity/order/choice')
        choices[key] = done['choice']
    cases = {case['sid']: case for case in registration['cases']}
    require(len(cases) == 158 and set(choices) == {(sid, order) for sid in cases for order in ('AB', 'BA')},
            'Exactly158 original proposals and their two orders')
    kept = acceptance['kept_sids']
    require(isinstance(kept, list) and len(kept) == len(set(kept)) and set(kept) <= set(cases),
            'Only unique registered proposal IDs may be kept')
    expected = {sid for sid in cases if choices[sid, 'AB'] == 'B' and choices[sid, 'BA'] == 'A'}
    require(set(kept) == expected, 'Kept IDs must equal the frozen AB=B and BA=A policy; no reranking')
    return cases, set(kept), ref(terminal_path)


def dump(path, rows):
    with Path(path).open('x', encoding='utf8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(',', ':'), allow_nan=False)+'\n')


def main():
    require(os.name == 'posix' and socket.gethostname() == 'inspur-NP5570M5', 'Registered Linux host only')
    require(os.environ['CUDA_VISIBLE_DEVICES'] == '', 'CPU-only package process')
    registration = read(ROOT/'registration_01.json')
    deadline(registration)
    require(registration['expected_sources'] == 158 and registration['expected_calls'] == 316
            and registration['actual_pipeline_parameters'] == PARAMETERS <= 9_000_000_000,
            'Exact fixed proposal, call and full parameter inventory')
    admission = read(bound(registration['admission_ref']))
    require(admission['status'] == 'EXPLICIT_LIMITED_EXTERNAL_OUTPUT_EVIDENCE_PRODUCTION_REVIEW',
            'Explicit formal visual-gate production review')
    bound(admission['official_rule_ref'])
    acceptance_path = ROOT/'output_acceptance_01.json'
    acceptance = read(acceptance_path)
    if 'registration_ref' in acceptance:
        require(bound(acceptance['registration_ref']).resolve() == (ROOT/'registration_01.json').resolve(),
                'Output acceptance registration binding')
    cases, kept, resource_ref = terminal_and_outputs(registration, acceptance)
    require(bool(kept), 'All-null result equals40.47 and must not be packaged as new')
    old_path = bound(admission['original_proposals_ref'])
    require(old_path.resolve() == (RELATIVE/'production_01/completion.json').resolve(), 'Only original fixed relative proposals')
    old = read(old_path)
    require(old['independent11strict'] is True and old['all_baseline_boxes_preserved'] is True
            and old['actual_resident_parameters'] == PARAMETERS, 'Adopt the genuinely accepted original relative package')
    decisions = {row['sid']: row for row in old['decisions']}
    require(len(decisions) == 426 and {sid for sid, row in decisions.items() if row['chosen'] is not None} == set(cases),
            'Formal gate covers every original158 chosen event and no replacement')
    for sid, case in cases.items():
        require(case['original_choice'] == decisions[sid], 'Registered proposal must equal unchanged original choice')
    base_ref = admission['original_baseline_ref']
    require(base_ref['sha256'] == BASE_SHA, 'Protect original40.47 archive')
    base = archive_rows(bound(base_ref)); baseline = frame_boxes(base)
    require(len(baseline) == 123506, 'Original123506 native frames')
    old_rows = archive_rows(bound(old['zip'])); old_boxes = frame_boxes(old_rows)
    require(canonical(old_rows) == old['canonical_sha256'] and set(baseline) <= set(old_boxes)
            and all(old_boxes[key] == box for key, box in baseline.items()), 'Original relative package identity and retained boxes')
    selected = set(baseline)
    for sid in kept:
        choice = decisions[sid]['chosen']
        require(type(choice['left']) is int and type(choice['right']) is int
                and 0 <= choice['left'] < choice['right'], 'Exact original native half-open event range')
        selected.update((sid, ordinal) for ordinal in range(choice['left'], choice['right']))
    additions = selected-set(baseline)
    require(0 < len(additions) <= 12350 and selected <= set(old_boxes), 'Only a subset of accepted original relative additions')
    out = ROOT/'package_01'
    out.mkdir(exist_ok=False)
    save(out/'start.json', dict(registration_ref=ref(ROOT/'registration_01.json'),
         admission_ref=registration['admission_ref'], output_acceptance_ref=ref(acceptance_path),
         resource_ref=resource_ref, original_relative_completion_ref=ref(old_path),
         producer_code_ref=ref(__file__), kept_sids=sorted(kept, key=int), utc=utc()))
    sys.path[:0] = [str(SOURCE_CLEAR/'code')]
    spec = importlib.util.spec_from_file_location('_pair_visual_original_renderer', SOURCE_CLEAR/'code/render.py')
    renderer = importlib.util.module_from_spec(spec); spec.loader.exec_module(renderer)
    rows, provenance, chosen, inputs = renderer.render(selected)
    current = frame_boxes(rows)
    require(set(current) == selected and all(current[key] == box for key, box in baseline.items()),
            'Every original40.47 frame and bbox remains exact')
    require(all(current[key] == old_boxes[key] for key in additions), 'Every new frame bbox equals original accepted relative ZIP')
    features = {row['id']: row for row in read(OLD/'feature_completion.json')['sources']}
    require(set(features) == set(map(str, range(426))), 'Original complete native-clock inventory')
    for sid in features:
        deadline(registration)
        clock_ref = dict(path=str(OLD/'inputs'/sid/'clock.json'), sha256=features[sid]['clock_sha256'])
        clock = read(bound(clock_ref)); points = list(map(Fraction, clock['normalized_exact_pts']))
        require(bool(points) and all(a < b for a, b in zip(points, points[1:]))
                and points[-1] < Fraction(clock['physical_end_exact']), 'Actual ordered native PTS domain')
        require(all(0 <= ordinal < len(points) for source, ordinal in selected if source == sid), 'Every selected ordinal is native')
        if sid in kept:
            require(cases[sid]['clock_ref']['sha256'] == clock_ref['sha256'], 'Gate and renderer bind the same original native clock')
    for row in rows:
        row['model_params_b'] = PARAMETERS/1e9
    digest = canonical(rows)
    old_admission = read(RELATIVE/'production_admission_02.json')
    protected_risks = old_admission['protected_risk_completion_refs']
    require(len(protected_risks) == 3 and len({value['path'] for value in protected_risks}) == 3,
            'Protect all three original risk packages')
    history_ref = old_admission['current_delivered_history_ref']
    history = set(histories(read(bound(history_ref))))
    history.update(histories(read(bound(inputs['history']))))
    history.update(read(OLD/'production_registration.json')['historical_prediction_sha256'])
    history.update((canonical(base), old['canonical_sha256'], read(SOURCE_CLEAR/'completion.json')['canonical_sha256']))
    for value in protected_risks:
        completion = read(bound(value)); bound(completion['zip'])
        history.add(completion['canonical_sha256'])
    for path in (EVENT/'packages').glob('*/completion.json'):
        history.add(read(path)['canonical_sha256'])
    require(digest not in history, 'New visual gate must differ from full historical and protected package union')
    save(out/'prediction_acceptance.json', dict(status='PASS_FIRST_VISUAL_GATE_NATIVE_BASELINE_BOX_DIFFERENCE_QA',
         records=426, frames=len(current), added_frames=len(additions), removed_frames=0,
         changed_sources=len(kept), original_baseline_frames_and_boxes_exact=True,
         added_boxes_equal_original_relative=True, original_relative_completion_ref=ref(old_path),
         clock_inventory_ref=ref(OLD/'feature_completion.json'), canonical_sha256=digest,
         historical_canonical_count=len(history), history_ref=history_ref, actual_resident_parameters=PARAMETERS, utc=utc()))
    dump(out/'predictions.jsonl', rows); dump(out/'selected.jsonl', chosen); dump(out/'provenance.jsonl', provenance)
    save(out/'metadata.json', read(bound(inputs['metadata'])))
    pending = out/'candidate_PAIRWISE_VISUAL_GATED_EVENT.PENDING.zip'
    deadline(registration)
    with zipfile.ZipFile(pending, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(out/'predictions.jsonl', 'predictions.jsonl')
    subprocess.run([str(PY), '-B', str(RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
        '--strict-loader-root', str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
        '--metadata', str(out/'metadata.json'), '--selected', str(out/'selected.jsonl'),
        '--predictions', str(out/'predictions.jsonl'), '--provenance', str(out/'provenance.jsonl'),
        '--zip', str(pending), '--report', str(out/'independent_validation.json')], check=True)
    checks = read(out/'independent_validation.json')['checks']
    require(len(checks) == 11 and all(value is True for value in checks.values()), 'Actual independent11strict required')
    member_sha = ref(out/'predictions.jsonl')['sha256']
    with zipfile.ZipFile(pending) as archive:
        require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None
                and hashlib.sha256(archive.read('predictions.jsonl')).hexdigest() == member_sha, 'Single JSONL, CRC and member SHA')
    bound(base_ref); bound(old['zip'])
    for value in protected_risks:
        bound(value); bound(read(bound(value))['zip'])
    deadline(registration)
    final = out/'candidate_PAIRWISE_VISUAL_GATED_EVENT.zip'
    require(not final.exists(), 'Never overwrite a completed ZIP')
    pending.rename(final)
    result = dict(status='NEW_ENGINEERING_ACCEPTED_PAIRWISE_VISUAL_GATED_EVENT_OFFICIAL_EFFECT_UNKNOWN',
        zip=ref(final), member_sha256=member_sha, canonical_sha256=digest, records=426,
        frames=len(current), added_frames=len(additions), removed_frames=0, changed_sources=len(kept),
        actual_added_seconds=sum(float(Fraction(decisions[sid]['chosen']['added_duration_exact'])) for sid in kept),
        actual_resident_parameters=PARAMETERS, all_baseline_boxes_preserved=True,
        added_boxes_equal_original_relative=True, original_three_risk_packages_preserved=True,
        independent11strict=True, kept_sids=sorted(kept, key=int), output_acceptance_ref=ref(acceptance_path),
        gpu_completion_ref=acceptance['gpu_completion_ref'], resource_ref=resource_ref,
        package_new_8B_calls=0, preceding_visual_BASE_calls=316, media_decode=0, processor_calls=0,
        official_labels_read=False, website_submitted=False, official_score='UNKNOWN', utc=utc())
    save(out/'completion.json', result)
    save(out/'delivery_receipt.json', {key: result[key] for key in (
        'status', 'zip', 'member_sha256', 'canonical_sha256', 'records', 'frames', 'added_frames',
        'removed_frames', 'changed_sources', 'actual_resident_parameters', 'independent11strict',
        'all_baseline_boxes_preserved', 'added_boxes_equal_original_relative', 'official_score', 'utc')})


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        if ROOT.is_dir():
            save(ROOT/('package_failure_'+uuid.uuid4().hex+'.json'), dict(error=repr(error),
                 traceback=traceback.format_exc(), successes_preserved=True, no_automatic_retry=True, utc=utc()))
        raise
