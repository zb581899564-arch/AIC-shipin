"""A new CPU candidate, gated by frozen external facts and one confirmed recipe."""
import hashlib
import json
import subprocess
import sys
import zipfile
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'reports/reliable_reference_20261012_v1'
PRIOR = ROOT / 'reports/boundary_refinement_20261012_v1'
INPUT = PRIOR / 'input_01'
DEPS = PRIOR / 'input_dependencies'
sys.path.insert(0, str(ROOT / 'improvement/boundary_refinement_v1'))
from intervals import expanded_windows, native_membership


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def save(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def write_rows(path, values):
    with path.open('x', encoding='utf-8') as handle:
        for value in values:
            handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False) + '\n')


def keymap(values):
    result = {(row['video_id'], p['frame']): p['bboxes'] for row in values for p in row['predictions']}
    assert len(result) == sum(len(row['predictions']) for row in values)
    return result


def main():
    comparison_path = REPORT / 'comparison_01/comparison_result.json'
    comparison = read(comparison_path)
    assert comparison['candidate_admitted'] is True
    admission_path = REPORT / 'reference_admission_01.json'
    assert read(admission_path)['reference_quality_pass'] is True
    assert sha(admission_path) == comparison['reference_admission_sha256']
    padding = comparison['padding_exact']
    names = {'A': 'FACT_REFERENCE_PRE100_POST050_8B', 'B': 'FACT_REFERENCE_PRE075_POST025_8B'}
    name = names[comparison['chosen']]
    assert padding == (['1', '1/2'] if comparison['chosen'] == 'A' else ['3/4', '1/4'])
    registration_path = REPORT / 'production_registration_01.json'
    save(registration_path, dict(candidate=name, padding_exact=padding,
                                selection_before_production_membership=True,
                                comparison_sha256=sha(comparison_path), model_parameters=8782459120,
                                new_model_calls=0, optimizer_updates=0, official_score='UNKNOWN'))
    prior_lock_path = PRIOR / 'production_source_lock.json'
    old_lock = read(prior_lock_path)
    for path, digest in old_lock['files'].items():
        assert sha(path) == digest, 'Changed inherited input: ' + path
    baseline_path = ROOT / 'deliveries/ASYMMETRIC_BOUNDARY_PRE075_POST050_8B_20261012/candidate_ASYMMETRIC_BOUNDARY_PRE075_POST050_8B.zip'
    assert sha(baseline_path) == 'cbfacd675aca7b6bbc3287ccebfd81e605945501cd1fef392681ff2e9761fec3'
    bound_paths = [admission_path, REPORT / 'aggregate_reference_01.json', REPORT / 'COMPARISON_POLICY.md',
                   comparison_path, registration_path, prior_lock_path, baseline_path,
                   Path(__file__), Path(__file__).with_name('validate_parameter_field.py')]
    lock_path = REPORT / 'production_source_lock_01.json'
    save(lock_path, dict(inherited_files=old_lock['files'],
                         new_files={str(path.resolve()): sha(path) for path in bound_paths},
                         model_parameters=8782459120, candidate=name, padding_exact=padding))
    output = REPORT / 'candidate_01'
    output.mkdir(exist_ok=False)
    save(output / 'launch_claim.json', dict(source_lock_sha256=sha(lock_path),
                                           purpose='ONE_CONFIRMED_RECIPE_CPU_PACKAGE', new_model_calls=0))
    with zipfile.ZipFile(baseline_path) as archive:
        assert archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None
        baseline = keymap([json.loads(line) for line in archive.read('predictions.jsonl').splitlines()])
    assert len(baseline) == 121266
    metadata = read(INPUT / 'metadata.json')
    meta = {row['video_id']: row for row in metadata['records']}
    clocks = read(INPUT / 'clocks.json')
    temporal = read(INPUT / 'temporal_inputs.json')
    original = {row['video_id']: row for row in temporal['records']}
    assert len(meta) == len(original) == len(clocks) == 426
    assert set(meta) == set(original) == set(clocks) == {str(i) for i in range(426)}
    field_rows = rows(INPUT / 'full_selected.jsonl')
    fields = {(row['video_id'], row['source_frame']): row for row in field_rows}
    assert len(fields) == len(field_rows) == 234158
    field_frames = defaultdict(list)
    for row in field_rows:
        source = meta[row['video_id']]
        assert row['source_path'] == source['source_path']
        assert row['source_n_frames'] == source['n_frames']
        assert row['source_width'] == source['width'] and row['source_height'] == source['height']
        assert row['target_ratio_wh'] == source['targetRatioWH']
        field_frames[row['video_id']].append(row['source_frame'])
    target, reproduced, core = set(), set(), set()
    proofs = []
    assert sum(len(row['windows']) for row in original.values()) == temporal['windows'] == 521
    for vid in sorted(meta):
        clock = clocks[vid]
        tick = F(clock['raw_time_base'])
        origin = clock['raw_first_pts_ticks'] * tick
        points = [p * tick - origin for p in clock['native_pts_ticks']]
        assert len(points) == meta[vid]['n_frames']
        ordinals = sorted(field_frames[vid])
        assert ordinals == list(range(ordinals[0], ordinals[-1] + 1))
        domain = (ordinals[0], ordinals[-1] + 1)
        windows = original[vid]['windows']
        for window in windows:
            assert window['clock_record_sha256'] == clock['clock_record_sha256']
            assert window['original_status'] == ('MODEL_OK' if window['segments'] else 'LEGAL_EMPTY')
        old_ids = native_membership(points, expanded_windows(windows, '3/4', '1/2'), domain)
        new_ids = native_membership(points, expanded_windows(windows, *padding), domain)
        core_ids = native_membership(points, expanded_windows(windows, '0', '0'), domain)
        assert core_ids <= new_ids
        if comparison['chosen'] == 'A':
            assert old_ids <= new_ids
        else:
            assert new_ids <= old_ids
        reproduced.update((vid, frame) for frame in old_ids)
        target.update((vid, frame) for frame in new_ids)
        core.update((vid, frame) for frame in core_ids)
        proofs.append(dict(video_id=vid, n_frames=len(points), field_domain=list(domain),
                           baseline_frames=len(old_ids), candidate_frames=len(new_ids),
                           added=len(new_ids-old_ids), removed=len(old_ids-new_ids),
                           independent_pts_predicate_equals_bisect=True))
    assert reproduced == set(baseline)
    assert len(core) == 102112 and core <= target
    assert target != reproduced and target <= set(fields)
    full_predictions = rows(INPUT / 'full_predictions.jsonl')
    all_boxes = keymap(full_predictions)
    assert set(all_boxes) == set(fields)
    assert all(all_boxes[key] == box for key, box in baseline.items())
    selected = [fields[key] for key in sorted(target)]
    predictions = [dict(row, model_params_b=8.78245912,
                        predictions=[p for p in row['predictions'] if (row['video_id'], p['frame']) in target])
                   for row in full_predictions]
    provenance = [row for row in rows(INPUT / 'full_provenance.jsonl')
                  if (row['video_id'], row['source_frame']) in target]
    assert len(provenance) == len(target)
    assert all(row['predictions'] for row in predictions)
    sys.path[:0] = [str(DEPS), str(INPUT / 'validator')]
    from package_contract import validate_predictions, package
    geometry_view = [{key: value for key, value in row.items() if key != 'model_params_b'} for row in predictions]
    geometry = validate_predictions(read(DEPS / 'legacy_spatial_manifest.json')['manifest'],
                                    geometry_view, target, provenance)
    for stem, values in [('predictions', predictions), ('selected', selected), ('provenance', provenance)]:
        write_rows(output / (stem + '.jsonl'), values)
    save(output / 'metadata.json', metadata)
    save(output / 'native_selection_acceptance.json', dict(rows=proofs, original_frames=len(core),
         baseline_frames=len(baseline), candidate_frames=len(target), added=len(target-reproduced),
         removed=len(reproduced-target), source_lock_sha256=sha(lock_path), all_retained_baseline_boxes_unchanged=True))
    del fields, field_rows, all_boxes, full_predictions, selected, geometry_view, clocks, temporal, original
    subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('validate_parameter_field.py')),
                    str(output / 'predictions.jsonl'), str(output / 'parameter_validation.json')], check=True)
    pending = output / ('candidate_' + name + '.PENDING.zip')
    package_info = package(output / 'predictions.jsonl', pending)
    subprocess.run([sys.executable, '-B', str(INPUT / 'validator/independent_validate.py'),
                    '--strict-loader-root', str(INPUT / 'validator/frozen_strict_loader'),
                    '--metadata', str(output / 'metadata.json'), '--selected', str(output / 'selected.jsonl'),
                    '--predictions', str(output / 'predictions.jsonl'), '--provenance', str(output / 'provenance.jsonl'),
                    '--zip', str(pending), '--report', str(output / 'independent_validation.json')], check=True)
    validation = read(output / 'independent_validation.json')
    assert len(validation['checks']) == 11 and all(validation['checks'].values())
    assert validation['video_records'] == 426 and validation['prediction_frames'] == len(target)
    assert validation['zip_sha256'] == sha(pending) == package_info['zip_sha256']
    assert validation['predictions_sha256'] == sha(output / 'predictions.jsonl')
    historical = list((ROOT / 'deliveries').rglob('candidate_*.zip'))
    assert all(sha(path) != sha(pending) for path in historical)
    final = output / ('candidate_' + name + '.zip')
    pending.rename(final)
    receipt = dict(status='PASS_ONE_NEW_EXTERNAL_FACT_SCREENED_RISK_ZIP', candidate=name,
                   padding_exact=padding, zip_path=str(final.resolve()), bytes=final.stat().st_size,
                   sha256=sha(final), frames=len(target), added=len(target-reproduced), removed=len(reproduced-target),
                   original_core_preserved=True, baseline_retained_boxes_preserved=True,
                   model_params_b=8.78245912, new_model_calls=0, optimizer_updates=0,
                   official_score='UNKNOWN', source_lock_sha256=sha(lock_path),
                   geometry_checks=geometry, independent_validation='independent_validation.json')
    save(output / 'completion.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
