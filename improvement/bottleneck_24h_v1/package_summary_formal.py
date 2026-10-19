"""Conditional native-frame package from accepted whole-source summary outputs.

The learned temporal selection may add and delete. Spatial fields stay fixed.
Valid empty sources stop delivery; they are never replaced with an old mask.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import zipfile

os.environ['CUDA_VISIBLE_DEVICES'] = ''
W = Path('/home/inspur/aic_video_work')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def bound(reference):
    path = Path(reference['path']).resolve(strict=True)
    require(path.is_relative_to(W) and path.is_file() and sha(path) == reference['sha256'],
            'Changed or out-of-workspace artifact: ' + str(path))
    if 'bytes' in reference:
        require(path.stat().st_size == reference['bytes'], 'Artifact byte size changed')
    return path


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())


def lines(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def dump(path, rows):
    with Path(path).open('x') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')
        stream.flush(); os.fsync(stream.fileno())


def canonical(rows):
    value = [{key: row[key] for key in ('video_id', 'targetRatioWH', 'predictions')}
             for row in sorted(rows, key=lambda item: item['video_id'])]
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def union_accepted_ranges(details, expected_sources, expected_windows):
    """Adopt already QA-accepted native ranges; no output/model/pixel replay."""
    require(len(details) == expected_windows and len({row['uid'] for row in details}) == expected_windows,
            'All unique accepted window output proofs')
    selected = set()
    sources = set()
    for row in details:
        sid = row['sid']; sources.add(sid)
        for left, right in row['native_ranges']:
            require(type(left) is int and type(right) is int and 0 <= left <= right,
                    'Only exact accepted native ordinal ranges')
            selected.update((sid, index) for index in range(left, right))
    require(sources == set(expected_sources), 'Every registered source output, including valid empty sources')
    return selected


def eligible_spatial_selection(raw_selected, field_rows):
    """One fixed structural eligibility rule for every source, no new boxes.

    Raw model evidence is retained separately. A missing original spatial
    observation is never replaced by guessed interpolation/extrapolation.
    """
    domain = {(row['video_id'], row['source_frame']) for row in field_rows}
    require(len(domain) == len(field_rows), 'Original spatial field contains duplicate source ordinals')
    selected = raw_selected & domain
    return selected, raw_selected - domain


def main(registration_path):
    require(os.uname().nodename == 'inspur-NP5570M5', 'Only the registered Linux host')
    regpath = Path(registration_path).resolve(strict=True); reg = read(regpath)
    require(reg['schema'] == 'SUMMARY_TWO_VIEW_FORMAL_426_V14', 'Explicit production version')
    root = Path(reg['root']).resolve(strict=True)
    require(root.is_relative_to(W), 'Only the independent new production root')
    require(bound(reg['code']['package_summary_formal.py']) == Path(__file__).resolve(), 'Package code binding')
    admission = read(bound(reg['production_admission_ref']))
    require(admission['status'] == 'ADMIT_FIXED_SUMMARY_FINAL559_426'
            and admission['main_review_completed'] is True and admission['production_allowed'] is True,
            'Actual external capability review and explicit production admission')
    bound(reg['final_adapter_ref']); frozen = read(bound(reg['final_freeze_ref']))
    require(frozen['status'] == 'FINAL559_WEIGHTS_FROZEN_BEFORE_DEV_METRICS'
            and frozen['final_adapter_ref']['sha256'] == reg['final_adapter_ref']['sha256'], 'Fixed final559 only')
    rules = read(bound(reg['rule_check_before_package_ref']))
    require(rules['summary_production_scope_checked'] is True
            and rules['not_official_special_permission'] is True, 'Current official rules bound to actual method')
    actual = reg['actual_pipeline_parameters']
    require(type(actual) is int and 0 < reg['actual_resident_parameters'] <= actual <= 9_000_000_000,
            'All actual participating main and auxiliary model parameters <=9B')
    inventory = read(bound(reg['pipeline_inventory_ref']))
    require(inventory['actual_pipeline_parameters'] == actual and inventory['participating_roles_frozen'] is True,
            'Actual original spatial field and new temporal model provenance count')
    qa = read(bound(reg['formal_output_QA_ref']))
    require(qa['status'] == 'PASS_ALL426_FIRST_INDEPENDENT_SUMMARY_FORMAL_TOKEN_GRAMMAR_NATIVE_QA'
            and qa['model_role'] == 'SUMMARY_FINAL' and qa['sources'] == 426
            and qa['windows'] == reg['expected_windows'] and qa['invalid_outputs'] == 0
            and qa['unique_ledger_equal'] is True, 'All first independent output QA and natural unique ledger')
    completion = read(bound(qa['completion_ref'])); bound(qa['resource_ref'])
    require(completion['model_weights_ref']['sha256'] == reg['final_adapter_ref']['sha256']
            and completion['outputs'] == qa['outputs'], 'QA binds exact final model and all immutable outputs')
    for reference in qa['outputs']:
        bound(reference)
    expected = {str(i) for i in range(426)}
    raw_selected = union_accepted_ranges(qa['details'], expected, reg['expected_windows'])
    inp = read(bound(reg['package_inputs_ref']))
    fields = {name: bound(reference) for name, reference in inp['source_field_files'].items()}
    eligibility = read(bound(reg['spatial_eligibility_policy_ref']))
    require(eligibility['status'] == 'FIXED_PREOUTPUT_ORIGINAL_SPATIAL_DOMAIN_ELIGIBILITY_NOT_NEW_QUALITY_RULE'
            and eligibility['formal_outputs_read'] is False and eligibility['final_dev_metrics_read'] is False
            and eligibility['field_ref']['sha256'] == inp['source_field_files']['field_frames.jsonl']['sha256']
            and admission['fixed_spatial_eligibility_policy_ref'] == reg['spatial_eligibility_policy_ref'],
            'Pre-output all-source original-field eligibility must be explicitly adopted, never post-score repair')
    original_field_rows = lines(fields['field_frames.jsonl'])
    selected, excluded = eligible_spatial_selection(raw_selected, original_field_rows)
    empty_sources = sorted(expected - {sid for sid, index in selected}, key=int)
    require(not empty_sources, 'Valid whole-source empty predictions cannot pass nonempty426 delivery; no silent fallback: '
            + ','.join(empty_sources))
    chosen = [row for row in original_field_rows
              if (row['video_id'], row['source_frame']) in selected]
    require(len(chosen) == len(selected) and len({(r['video_id'], r['source_frame']) for r in chosen}) == len(selected),
            'Every delivery-eligible native frame must have one original accepted spatial field; never extrapolate')
    for reference in reg['renderer_code_refs'].values():
        bound(reference)
    sys.path[:0] = reg['renderer_import_paths']
    from field_contract import compose_from_field
    from pts_contract import legacy_manifest
    require(Path(sys.modules['field_contract'].__file__).resolve() == bound(reg['renderer_code_refs']['field_contract.py'])
            and Path(sys.modules['pts_contract'].__file__).resolve() == bound(reg['renderer_code_refs']['pts_contract.py']),
            'Only the frozen original spatial composition implementation')
    rows, provenance = compose_from_field(legacy_manifest(read(bound(inp['source_manifest']))), chosen,
        lines(fields['field_shots.jsonl']), lines(fields['anchor_requests.jsonl']), lines(fields['anchor_output.jsonl']))
    current = {(row['video_id'], item['frame']): item['bboxes'] for row in rows for item in row['predictions']}
    require(len(rows) == 426 and {r['video_id'] for r in rows} == expected
            and all(row['predictions'] for row in rows) and set(current) == selected,
            'All426 complete nonempty sources, native ordinals and unique model-selected frames')
    basepath = bound(reg['protected_baseline_ref'])
    require(reg['protected_baseline_ref']['sha256'] == 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3',
            'Original40.47 package identity')
    with zipfile.ZipFile(basepath) as archive:
        baseline = [json.loads(line) for line in archive.read('predictions.jsonl').splitlines()]
    old = {(row['video_id'], item['frame']): item['bboxes'] for row in baseline for item in row['predictions']}
    common = set(current) & set(old)
    require(all(current[key] == old[key] for key in common), 'All retained40.47 frames keep exactly original boxes')
    for row in rows:
        row['model_params_b'] = actual / 1e9
    checksum = canonical(rows)
    history = set(reg['historical_prediction_sha256']); history.add(canonical(baseline))
    require(checksum not in history, 'No renamed baseline or historical prediction')
    out = root / 'package_14'; out.mkdir(exist_ok=False)
    save(out/'fixed_field_eligibility.json', dict(policy_ref=reg['spatial_eligibility_policy_ref'],
        raw_model_native_frames=len(raw_selected), eligible_delivery_native_frames=len(selected),
        excluded_unavailable_field_frames=len(excluded),
        excluded_original_source_ordinals=[dict(sid=sid, source_frame=ordinal) for sid,ordinal in sorted(excluded)],
        model_raw_outputs_unchanged=True, no_new_spatial_model_or_guessed_box=True))
    dump(out / 'predictions.jsonl', rows); dump(out / 'selected.jsonl', chosen)
    dump(out / 'provenance.jsonl', provenance); save(out / 'metadata.json', read(bound(inp['metadata'])))
    pending = out / 'candidate_SOURCE_SUMMARY_FINAL559.PENDING.zip'
    with zipfile.ZipFile(pending, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(out / 'predictions.jsonl', 'predictions.jsonl')
    subprocess.run([reg['python'], '-B', str(bound(reg['independent_validator_ref'])),
        '--strict-loader-root', reg['strict_loader_root'], '--metadata', str(out / 'metadata.json'),
        '--selected', str(out / 'selected.jsonl'), '--predictions', str(out / 'predictions.jsonl'),
        '--provenance', str(out / 'provenance.jsonl'), '--zip', str(pending),
        '--report', str(out / 'independent_validation.json')], check=True)
    checks = read(out / 'independent_validation.json')['checks']
    require(len(checks) == 11 and all(checks.values()), 'Original independent11strict must all pass')
    with zipfile.ZipFile(pending) as archive:
        require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None
                and hashlib.sha256(archive.read('predictions.jsonl')).hexdigest() == sha(out / 'predictions.jsonl'),
                'One JSONL, ZIP CRC and exact member SHA')
    require(sha(basepath) == reg['protected_baseline_ref']['sha256'], 'Protected baseline unchanged')
    final = out / 'candidate_SOURCE_SUMMARY_FINAL559.zip'; pending.rename(final)
    save(out / 'completion.json', dict(status='NEW_SUMMARY_ENGINEERING_ACCEPTED_OFFICIAL_EFFECT_UNKNOWN',
        zip=ref(final), member_sha256=sha(out / 'predictions.jsonl'), canonical_sha256=checksum,
        records=426, frames=len(selected), added_frames=len(set(current)-set(old)),
        removed_frames=len(set(old)-set(current)), retained_baseline_boxes_exact=True,
        raw_model_native_frames=len(raw_selected), excluded_unavailable_field_frames=len(excluded),
        spatial_eligibility_ref=ref(out/'fixed_field_eligibility.json'),
        actual_pipeline_parameters=actual, independent11strict=True, output_QA_ref=reg['formal_output_QA_ref'],
        external_capability_admission_ref=reg['production_admission_ref'], official_score='UNKNOWN',
        website_submitted=False, utc=datetime.now(timezone.utc).isoformat()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--registration', required=True)
    args = parser.parse_args()
    try:
        main(args.registration)
    except BaseException as error:
        failure = Path(args.registration).resolve().parent / 'formal_package_failure_14.json'
        if not failure.exists():
            save(failure, dict(error=repr(error), traceback=traceback.format_exc(),
                preserve_all_outputs=True, automatic_retry=False, no_model_rerun=True,
                utc=datetime.now(timezone.utc).isoformat()))
        raise
