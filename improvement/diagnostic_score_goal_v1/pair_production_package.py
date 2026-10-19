"""Conditional new-pair inference QA and add-only package; never launches models."""
import argparse
from pathlib import Path
import sys
import subprocess
import zipfile
_support = Path(__file__).resolve().parents[1]/'pair_code_17'
if _support.is_dir(): sys.path.insert(0, str(_support))
from pair_common import *
from pair_preference_math import select_addition, apply_selection


def lines(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def write_lines(path, rows):
    with Path(path).open('x', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(',', ':'), allow_nan=False)+'\n')
        stream.flush(); os.fsync(stream.fileno())


def canonical(rows):
    data = [{k:r[k] for k in ('video_id','targetRatioWH','predictions')} for r in sorted(rows, key=lambda x:x['video_id'])]
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'New independent package is CPU only')
    import numpy as np
    import torch
    torch.set_num_threads(2)
    reg = read(root/'pair_package_registration_23.json')
    require(reg['schema'] == 'EXPLICIT_FROZEN_PAIR_NEW_PACKAGE_V23' and bound(reg['code']) == Path(__file__).resolve(),
            'Explicit exact packaging runtime required')
    admission = read(bound(reg['GPU_admission']))
    require(admission['production_admitted'] is True and admission['baseline_40_47'] == reg['baseline_40_47'],
            'Actual separate model and protected baseline admission')
    production_registration = read(bound(admission['production_registration']))
    import pair_preference_math
    require(bound(production_registration['helper_code']['pair_preference_math']) == Path(pair_preference_math.__file__).resolve(),
            'Actual selection implementation must be the frozen CPU21 helper')
    require(read(bound(reg['official_rule_check']))['status'] == 'CURRENT_ALL3_FULL_BYTES_MATCH_PRIOR_FULL_READ',
            'Bound current official rule check')
    terminal = read(bound(reg['GPU_resource']))
    record = terminal['record']
    ledger = [json.loads(x) for x in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if x.strip() and json.loads(x).get('name') == admission['GPU_job']]
    require(ledger == [record] and record['status'] == 'completed' and record['exit_code'] == 0,
            'Unique actual natural completed production GPU terminal')
    gate = read(bound(reg['input_acceptance']))
    require(gate['status'] == 'PASS_ALL426_NEW_TWO_VIDEO_PRODUCTION_INPUTS' and gate['sources'] == 426 and
            gate['registration'] == admission['production_registration'] and
            reg['input_acceptance'] == admission['input_acceptance'], 'All426 first actual production input QA')
    prepared = read(bound(gate['prepared']))
    completion = read(bound(reg['inference_completion']))
    require(completion['status'] == 'COMPLETE_ALL_ROLE_INPUTS_RAW_LOGITS_NOT_QUALITY' and
            completion['model_role'] == admission['role'] and completion['total_sources'] == 426 and
            completion['GPU_admission'] == reg['GPU_admission'] and
            completion['input_acceptance'] == reg['input_acceptance'] and
            completion['production_registration'] == admission['production_registration'] and
            completion['quality'] == admission['quality'] and
            completion['training_completion'] == admission['training_completion'] and
            completion['baseline_40_47'] == prepared['protected_baseline'] == gate['protected_baseline'] == reg['baseline_40_47'],
            'Exact one-chain production model, input, baseline and quality bindings')
    identity = read(bound(completion['model_identity']))
    cfg = read(bound(admission['model_config']))
    require(identity['model_role'] == admission['role'] and identity['inventory'] == completion['inventory'] and
            identity['base'] == completion['base_fingerprint'] and
            completion['base_fingerprint']['sha256'] == cfg['expected_base_sha256'] and
            completion['inventory']['conservative_pipeline'] == 8790225161 and
            completion['original_TIME_unchanged'] is True and completion['labels_read'] is False and
            completion['new_optimizer_updates'] == 0 and
            (admission['role'] != 'TRAINED' or (completion['adapter_all288_unchanged'] is True and
             identity['adapter_weights'] == admission['adapter_weights'])), 'Actual immutable BASE/PAIR and complete model inventory')
    expected = {x['id']:x for x in prepared['dev_inputs']}
    require(len(expected) == len(prepared['dev_inputs']) == len(completion['entries']) == completion['expected_inputs'] == gate['inputs'],
            'Exact unique input and output sets')
    require(completion['inventory']['conservative_pipeline'] <= 9_000_000_000, 'All actual pipeline components exceed9B')
    parameter_count = completion['inventory']['conservative_pipeline']
    out = root/'pair_production_21'/'package_23'; out.mkdir(exist_ok=False)
    probability, seen, calls, aliases = {}, {}, 0, 0
    for entry in completion['entries']:
        require(entry['id'] in expected and entry['id'] not in probability and entry['input'] == expected[entry['id']]['input'],
                'New production output request set mismatch')
        receipt = read(bound(entry['receipt'])); request = read(bound(entry['input']))
        require(receipt['id'] == entry['id'] and receipt['input'] == entry['input'] and
                receipt['source_id'] == request['source_id'] == expected[entry['id']]['source_id'] and
                receipt['model_role'] == admission['role'] and receipt['input_signature'] == request['input_signature'] and
                receipt['class_token_ids'] == request['class_token_ids'], 'Independent production source/input/model binding')
        tokens = torch.load(bound(request['tokens']), map_location='cpu', weights_only=True)
        require(signature(tokens) == {k:request['input_signature'][k] for k in ('input_ids','attention_mask')},
                'Bound actual prediction prefix changed')
        raw = torch.load(bound(receipt['raw_logits']), map_location='cpu', weights_only=True)
        ids = request['class_token_ids']
        require(raw.ndim == 1 and raw.dtype == torch.float32 and torch.isfinite(raw).all() and len(raw) == receipt['full_vocabulary_size'] and
                len(ids) == len(set(ids)) == 3 and all(type(k) is int and 0 <= k < len(raw) for k in ids),
                'Finite first stored full raw production logits/class mapping')
        three = raw[ids].double(); p = torch.softmax(three, 0).numpy()
        require(np.array_equal(three.numpy(), np.asarray(receipt['class_logits'], dtype=np.float64)) and
                np.allclose(p, receipt['probabilities'], rtol=0, atol=5e-15) and
                int(np.argmax(p)) == receipt['predicted_index'], 'Independent production3class extraction and decision')
        if receipt['actual_new_forward']:
            require(receipt['alias_of'] is None, 'Actual new forward cannot also be an alias'); calls += 1
        else:
            previous = seen.get(receipt['alias_of']['path'])
            require(previous is not None and receipt['alias_of'] == previous['reference'] and
                    receipt['input_signature'] == previous['receipt']['input_signature'] and
                    receipt['raw_logits'] == previous['receipt']['raw_logits'], 'Only same-role exact input aliases allowed')
            aliases += 1
        seen[entry['receipt']['path']] = dict(reference=entry['receipt'], receipt=receipt)
        probability[entry['id']] = p.tolist()
    require(set(probability) == set(expected) and calls == completion['actual_forward_calls'] and aliases == completion['aliases'],
            'Complete independent actual production input/output counts')
    save(out/'output_acceptance.json', dict(status='PASS_FIRST_ALL_NEW_PAIR_PRODUCTION_OUTPUTS',
        inference=reg['inference_completion'], input_acceptance=reg['input_acceptance'], inputs=len(expected),
        actual_new_forwards=calls, exact_input_aliases=aliases, new_model_calls=0, no_GT=True))
    baseline_zip = bound(reg['baseline_40_47'])
    require(reg['baseline_40_47']['sha256'] == 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3',
            'Protected40.47 exact archive only')
    with zipfile.ZipFile(baseline_zip) as archive:
        require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None, 'Protected baseline single-member CRC')
        baseline = [json.loads(x) for x in archive.read('predictions.jsonl').splitlines()]
    b = {(r['video_id'],p['frame']):p['bboxes'] for r in baseline for p in r['predictions']}
    require(len(baseline) == 426 and {r['video_id'] for r in baseline} == {str(i) for i in range(426)} and
            len(b) == 123506 and all(r['predictions'] for r in baseline), 'Original complete40.47 baseline identity')
    origin = read(bound(reg['source_field_package_inputs']))
    manifest = read(bound(origin['source_manifest'])); metadata = read(bound(origin['metadata']))
    clocks = read(bound(origin['source_clocks']))
    require(set(clocks) == {str(i) for i in range(426)}, 'Complete original native source clocks')
    require(len(prepared['sources']) == 426 and {s['id'] for s in prepared['sources']} == set(clocks),
            'Complete source statuses, including valid abstentions')
    selected_keys, source_results = set(), []
    for source in prepared['sources']:
        sid = source['id']; clock = clocks[sid]
        own_clock = read(bound(source['clock']))
        require(source['source_sha256'] == clock['source_sha256'] == own_clock['source_sha256'] and
                own_clock['normalized_exact_pts'] == clock['normalized_exact_pts'], 'Actual new policy native PTS/source binding')
        with np.load(bound(source['baseline_mask']), allow_pickle=False) as data:
            mask_base = data['baseline'].copy()
        original = np.zeros(clock['n_frames'], dtype=bool)
        indices = [frame for video,frame in b if video == sid]
        require(all(type(i) is int and 0 <= i < len(original) for i in indices), 'Original baseline frame outside native domain')
        original[indices] = True
        require(mask_base.dtype == np.bool_ and np.array_equal(mask_base, original),
                'Production must preserve full40.47, never substitute old40.46 native.baseline')
        groups = np.load(bound(source['native_groups']), allow_pickle=False)
        with np.load(bound(source['native']), allow_pickle=False) as data: cells = data['groups'].copy()
        votes = [dict(start_group=c['clip']['start_group'], candidate_first=probability[c['first_id']],
                      anchor_first=probability[c['reverse_id']]) for c in source['candidates']]
        decision = select_addition(groups, cells, original, votes)
        mask = apply_selection(original, decision)
        require(np.all(mask[original]) and mask.any(), 'No deletion or empty original source is permitted')
        chosen = set((sid,int(i)) for i in np.flatnonzero(mask)); selected_keys.update(chosen)
        path = out/(sid+'.selection.npz')
        with path.open('xb') as stream: np.savez(stream, selected_native=mask)
        source_results.append(dict(id=sid, source_sha256=source['source_sha256'], output=ref(path),
            added_native_frames=decision['added_native_frames'], decision=decision, baseline_mask=source['baseline_mask']))
    require(set(b) <= selected_keys, 'Full protected baseline native collection must be a subset')
    save(out/'selection_acceptance.json', dict(status='PASS_FIRST_FULL426_NATIVE_ADD_ONLY_POLICY_REPLAY',
        sources=source_results, inference=reg['inference_completion'], baseline=reg['baseline_40_47'], new_model_calls=0))
    if selected_keys == set(b):
        save(out/'completion.json', dict(status='STOP_ZERO_PREDICTION_DIFFERENCE_NO_RENAMED_BASELINE', package_created=False)); return
    field = {name:lines(bound(reference)) for name,reference in origin['source_field_files'].items()}
    field_map = {(r['video_id'],r['source_frame']):r for r in field['field_frames.jsonl']}
    require(len(field_map) == len(field['field_frames.jsonl']) and selected_keys <= field_map.keys(),
            'No duplicate or missing frame in the accepted full-source spatial field')
    paths()
    from field_contract import compose_from_field
    from pts_contract import legacy_manifest
    chosen = [field_map[k] for k in sorted(selected_keys)]
    predictions, provenance = compose_from_field(legacy_manifest(manifest), chosen, field['field_shots.jsonl'],
        field['anchor_requests.jsonl'], field['anchor_output.jsonl'])
    for row in predictions: row['model_params_b'] = parameter_count/1e9
    final = {(r['video_id'],p['frame']):p['bboxes'] for r in predictions for p in r['predictions']}
    require(len(predictions) == 426 and all(r['predictions'] for r in predictions) and set(final) == selected_keys and
            all(final[k] == b[k] for k in b), 'Exact426/native selection and all original40.47 boxes unchanged')
    digest = canonical(predictions)
    history = set(reg['historical_canonical_sha256']) | {canonical(baseline)}
    if digest in history:
        save(out/'completion.json', dict(status='STOP_HISTORICAL_DUPLICATE_PREDICTION', canonical_sha256=digest, package_created=False)); return
    for name,rows in [('predictions.jsonl',predictions),('selected.jsonl',chosen),('provenance.jsonl',provenance)]:
        write_lines(out/name, rows)
    save(out/'metadata.json', metadata)
    pending = out/'candidate_PAIR_PREFERENCE.PENDING.zip'
    with zipfile.ZipFile(pending, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(out/'predictions.jsonl', 'predictions.jsonl')
    validator = RUN/'baseline_a_pts_v1/vendor/independent_validate.py'
    subprocess.run([sys.executable, str(validator), '--strict-loader-root',str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
        '--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),'--predictions',str(out/'predictions.jsonl'),
        '--provenance',str(out/'provenance.jsonl'),'--zip',str(pending),'--report',str(out/'independent_validation.json')],check=True)
    checks = read(out/'independent_validation.json')['checks']
    require(len(checks) == 11 and all(checks.values()), 'Independent actual11strict checks')
    with zipfile.ZipFile(pending) as archive:
        require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None and
                hashlib.sha256(archive.read('predictions.jsonl')).hexdigest() == sha(out/'predictions.jsonl'), 'ZIP single-member CRC/SHA')
    zip_path = out/'candidate_PAIR_PREFERENCE.zip'; pending.rename(zip_path)
    save(out/'completion.json', dict(status='PASS_ENGINEERING_NEW_ADD_ONLY_PAIR_CANDIDATE_OFFICIAL_EFFECT_UNKNOWN',
        zip=str(zip_path), bytes=zip_path.stat().st_size, sha256=sha(zip_path), member_sha256=sha(out/'predictions.jsonl'),
        canonical_sha256=digest, records=426, frames=len(final), added_native_frames=len(set(final)-set(b)),
        removed_native_frames=0, empty_sources=0, original_baseline_all_boxes_unchanged=True,
        actual_conservative_pipeline_parameters=parameter_count, independent11strict=True,
        model_role=admission['role'], inference=reg['inference_completion'], quality=admission['quality'],
        old_spatial_field_source=origin['source_field_files'], online_score='UNKNOWN', website_submitted=False,
        no_official_GT_read=True, local_delivery_not_yet_verified=True))
    require(not torch.cuda.is_initialized(), 'CPU packaging must not initialize CUDA')


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,required=True); run(p.parse_args().root)
