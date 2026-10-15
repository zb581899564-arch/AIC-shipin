"""CPU-only deterministic union PREVIEW; publication is never authorized here.

Reads accepted ACTION/REACTION/INFORMATION packages and their immutable proof
references.  No model, decoder, processor, QA replay or quality metric is run.
Only the new combination receives one independent strict format validation.
"""
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

sys.dont_write_bytecode = True

HOME = Path('/home/inspur/aic_video_work')
ROOT = HOME / 'midnight_five_verify40_46_20261015_v1'
OLD = HOME / 'twenty_hour_five_20261014_v1/temporal_family_native_package_v3'
RUN = HOME / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
INPUTS = ROOT / 'semantic_union_review_inputs_27.json'
OUT = ROOT / 'semantic_union_review_27'
SOURCES = ('ACTION', 'REACTION', 'INFORMATION')
CURRENT = frozenset(('ORDINARY', *SOURCES))
PARAMETERS = 8782459120
BASELINE_SHA = '86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543'
COUNTS = dict(logical_cases=519, actual_model_calls=518, adopted_identical_input_aliases=1,
              first_model_output_QA_count=518, alias_application_QA_count=1)
MEMBER = 'predictions.jsonl'
SOURCE_FILES = dict(predictions_ref=MEMBER, selected_ref='selected.jsonl',
    provenance_ref='provenance.jsonl', metadata_ref='metadata.json',
    independent_validation_ref='independent_validation.json')


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf8').splitlines() if line.strip()]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def ref(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def checked(reference):
    require(isinstance(reference, dict) and isinstance(reference.get('path'), str) and
            isinstance(reference.get('sha256'), str), 'Actual path/SHA reference required')
    path = Path(reference['path'])
    require(path.is_absolute() and path.resolve().is_relative_to(HOME) and
            sha(path) == reference['sha256'], 'Referenced actual bytes/path changed: ' + str(path))
    if 'bytes' in reference:
        require(path.stat().st_size == reference['bytes'], 'Referenced file size differs')
    return path


def same_ref(left, right, reason):
    require((left['path'], left['sha256']) == (right['path'], right['sha256']), reason)


def save(path, value):
    require(Path(path).parent.resolve() == OUT, 'Preview writes are confined to the new review directory')
    with Path(path).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def write_rows(path, values):
    require(Path(path).parent.resolve() == OUT, 'Preview writes are confined to the new review directory')
    with Path(path).open('x', encoding='utf8') as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')
        stream.flush(); os.fsync(stream.fileno())


def canonical(values):
    body = [{name: value[name] for name in ('video_id', 'targetRatioWH', 'predictions')}
            for value in sorted(values, key=lambda value: value['video_id'])]
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def predictions_from_archive(path):
    with zipfile.ZipFile(path) as archive:
        require(archive.namelist() == [MEMBER] and archive.testzip() is None, 'Source single JSONL/CRC differs')
        payload = archive.read(MEMBER)
    return [json.loads(line) for line in payload.splitlines() if line.strip()], hashlib.sha256(payload).hexdigest()


def prediction_index(values):
    headers, frames = {}, {}
    for value in values:
        source = value['video_id']
        require(isinstance(source, str) and source not in headers and value['predictions'] and
                value['model_params_b'] == PARAMETERS / 1e9, 'Source output identity/nonempty/actual parameter count differs')
        headers[source] = {name: field for name, field in value.items() if name != 'predictions'}
        for prediction in value['predictions']:
            frame = prediction['frame']; key = source, frame
            require(type(frame) is int and frame >= 0 and key not in frames, 'Duplicate or invalid actual native frame')
            frames[key] = prediction
    require(set(headers) == {str(index) for index in range(426)}, 'Exactly 426 nonempty original sources required')
    return headers, frames


def frame_index(values, label):
    result = {}
    for value in values:
        key = value['video_id'], value['source_frame']
        require(isinstance(key[0], str) and type(key[1]) is int and key[1] >= 0 and key not in result,
                'Duplicate or invalid source-native identity in ' + label)
        result[key] = value
    return result


def merge_exact(destination, values, label):
    for key, value in values.items():
        if key in destination:
            require(destination[key] == value, 'Overlapping complete row/box differs in ' + label + ': ' + str(key))
        else:
            destination[key] = value


def refs_by_arm(values, expected):
    require(isinstance(values, list) and len(values) == len(expected), 'Complete fixed package receipt reference list required')
    result = {}
    for reference in values:
        arm = read(checked(reference))['arm']
        require(arm in expected and arm not in result, 'Unknown or repeated fixed source package arm')
        result[arm] = reference
    require(set(result) == set(expected), 'Fixed package reference set incomplete')
    return result


def accepted_current(receipt_ref, arm, production_ref, original_inputs_sha):
    path = checked(receipt_ref)
    folder = ROOT / 'packages' / ('package_' + arm)
    require(path == folder / 'completion.json', 'Current package receipt must be the fixed original actual file')
    value = read(path)
    require(value['arm'] == arm and value['records'] == 426 and value['actual_parameters'] == PARAMETERS and
            value['independent11strict'] is True and value['retained_original_boxes_exact'] is True and
            value['new_spatial_model_calls'] == 0 and value['model_calls_in_packaging'] == 0 and
            value['package_inputs_sha256'] == original_inputs_sha and
            all(value[name] == count for name, count in COUNTS.items()), 'Actual original production/package identity differs')
    same_ref(value['production_completion_ref'], production_ref, 'Current package used another production completion')
    archive = Path(value['zip'])
    require(archive == folder / ('candidate_MIDNIGHT_' + arm + '.zip') and
            archive.stat().st_size == value['bytes'] and sha(archive) == value['SHA256'], 'Original current ZIP bytes/SHA differ')
    predictions, member_sha = predictions_from_archive(archive)
    require(member_sha == value['member_SHA256'] and canonical(predictions) == value['canonical_SHA256'], 'Original current actual predictions/member SHA differ')
    headers, frames = prediction_index(predictions)
    require(len(frames) == value['frame_count'], 'Original current frame count differs')
    return dict(receipt=value, receipt_ref=receipt_ref, folder=folder, archive=archive,
                predictions=predictions, headers=headers, frames=frames)


def check_source_files(source, references):
    folder, receipt, frames = source['folder'], source['receipt'], source['frames']
    paths = {}
    for name, filename in SOURCE_FILES.items():
        paths[name] = checked(references[name])
        require(paths[name] == folder / filename, 'Source component reference must be its original actual package file')
    require(sha(paths['predictions_ref']) == receipt['member_SHA256'] and
            rows(paths['predictions_ref']) == source['predictions'], 'ZIP member differs from actual source predictions.jsonl')
    report = read(paths['independent_validation_ref'])
    require(sha(paths['independent_validation_ref']) == receipt['independent_validation_sha256'] and
            report['status'] == 'PASS_INDEPENDENT_STRICT_VALIDATION' and len(report['checks']) == 11 and
            all(check is True for check in report['checks'].values()) and report['video_records'] == 426 and
            report['prediction_frames'] == len(frames) and report['duplicate_frames'] == 0 and
            report['missing'] == report['extra'] == 0 and report['zip_sha256'] == receipt['SHA256'] and
            report['predictions_sha256'] == sha(paths['predictions_ref']) and
            report['provenance_sha256'] == sha(paths['provenance_ref']), 'Original accepted 11-strict proof or its actual artifacts differ')
    selected = frame_index(rows(paths['selected_ref']), 'selected')
    provenance = frame_index(rows(paths['provenance_ref']), 'provenance')
    require(set(selected) == set(provenance) == set(frames) and
            all(provenance[key]['box_xyw'] == frames[key]['bboxes'] and provenance[key]['legal'] is True and
                provenance[key]['spatial_source'] in {'QWEN_ANCHOR_SAME_FRAME', 'SHOT_LINEAR_INTERPOLATION'} for key in frames),
            'Original selected/provenance/native predictions are not the same accepted frame set/boxes')
    require(receipt['quality_pass_claimed'] is False and receipt['risk_quality_screening_performed'] is False,
            'Union adopts the three actual risk packages without metric-based selection')
    return selected, provenance, read(paths['metadata_ref']), paths


def main():
    require(sys.platform == 'linux' and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Linux CPU-only review preview required')
    require(Path(__file__).resolve() == ROOT / 'semantic_union_review_code_v1/preview_union.py' and not OUT.exists(),
            'Preview code must be separately deployed; old preview/partial output may not be repeated')
    inputs = read(INPUTS)
    require(inputs.get('publication_authorized', False) is False, 'This entry supports an unauthorized review preview only')
    code_files = inputs['code_files']
    pure_paths = {str(ROOT / 'package_code_v2/production_evidence.py'),
                  str(ROOT / 'package_code_v2/package_math.py')}
    require(set(code_files) == {str(Path(__file__).resolve()), *pure_paths},
            'Only current preview and the two original read-only proof helpers must be frozen')
    for path, digest in code_files.items():
        require(Path(path).resolve().is_relative_to(ROOT), 'Preview code escaped campaign root')
        checked(dict(path=path, sha256=digest))
    original_ref = inputs['original_package_inputs_ref']
    require(checked(original_ref) == ROOT / 'package_inputs.json', 'Original frozen production inputs required')
    original = read(original_ref['path'])
    production_ref = original['production_completion_ref']
    require(checked(production_ref) == ROOT / 'production_unique_09/completion.json', 'Only completed original 518+1 production may be adopted')
    # Load only JSON proof validators from the frozen original package code.
    # No old renderer, model, tokenizer, decoder, or first-QA operation is run.
    for path, digest in original['code_files'].items():
        checked(dict(path=path, sha256=digest))
    proof_path = ROOT / 'package_code_v2/production_evidence.py'
    math_path = proof_path.with_name('package_math.py')
    require(str(proof_path) in original['code_files'] and str(math_path) in original['code_files'], 'Original pure evidence helpers are not bound')
    require(all(code_files[path] == original['code_files'][path] for path in pure_paths),
            'Adopted original pure evidence helper SHA differs from frozen production inputs')
    sys.path.insert(0, str(proof_path.parent))
    specification = importlib.util.spec_from_file_location('_original_union_production_evidence', proof_path)
    module = importlib.util.module_from_spec(specification); specification.loader.exec_module(module)
    production = read(production_ref['path'])
    require(production['status'] == 'COMPLETE_NEW_FIVE_WAY_INFERENCE_ENGINEERING_NOT_QUALITY' and
            production['actual_parameters'] == PARAMETERS and production['first_input_QA_complete'] is True and
            production['first_output_QA_complete'] is True, 'Actual complete original QA production required')
    _, counts = module.validate_production_evidence(production, lambda reference: read(checked(reference)), PARAMETERS)
    require(counts == COUNTS, 'Actual 518 calls/1 alias/519 logical cases must remain separate')
    checked(production['unique_gpu_terminal_ref'])
    same_ref(inputs['protected_baseline_zip_ref'], original['protected_baseline_zip_ref'], 'Protected baseline reference changed')
    baseline_path = checked(inputs['protected_baseline_zip_ref'])
    require(baseline_path == OLD / 'package_VERIFY/candidate_TEMPORAL_VERIFY.zip' and
            baseline_path.stat().st_size == 380199 and sha(baseline_path) == BASELINE_SHA, 'Protected original 40.46 ZIP bytes changed')
    baseline, _ = predictions_from_archive(baseline_path)
    _, baseline_frames = prediction_index(baseline)
    require(len(baseline_frames) == 122002, 'Actual protected 40.46 122002 native frames required')
    refs = refs_by_arm(inputs['current_four_package_refs'], CURRENT)
    current = {arm: accepted_current(reference, arm, production_ref, original_ref['sha256']) for arm, reference in refs.items()}
    source_completions = refs_by_arm(inputs['source_package_completion_refs'], set(SOURCES))
    source_refs = {}
    for arm in SOURCES:
        source_refs[arm] = dict(completion_ref=source_completions[arm],
            **{name: ref(current[arm]['folder'] / filename) for name, filename in SOURCE_FILES.items()})
    all_frames, all_selected, all_provenance = {}, {}, {}
    metadata, metadata_sha, headers = None, None, None
    component_refs = {}
    for arm in SOURCES:
        same_ref(source_refs[arm]['completion_ref'], refs[arm], 'Source risk completion differs from current delivered package')
        source = current[arm]
        selected, provenance, meta, paths = check_source_files(source, source_refs[arm])
        require(set(baseline_frames) <= set(source['frames']) and
                all(source['frames'][key]['bboxes'] == value['bboxes'] for key, value in baseline_frames.items()),
                'A source risk package lost or changed a protected 40.46 frame/box')
        if metadata is None:
            metadata, metadata_sha, headers = meta, sha(paths['metadata_ref']), source['headers']
        else:
            require(meta == metadata and sha(paths['metadata_ref']) == metadata_sha and source['headers'] == headers,
                    'The three original package metadata/header bytes and values must be identical')
        merge_exact(all_frames, source['frames'], 'predictions')
        merge_exact(all_selected, selected, 'selected')
        merge_exact(all_provenance, provenance, 'provenance')
        component_refs[arm] = dict(source_refs[arm])
    require(set(all_frames) == set(all_selected) == set(all_provenance) and
            set(baseline_frames) <= set(all_frames) and all(all_frames[key]['bboxes'] == value['bboxes']
            for key, value in baseline_frames.items()), 'Union original frame/box retention failed')
    metadata_by_id = {value['video_id']: value for value in metadata['records']}
    require(len(metadata_by_id) == len(metadata['records']) == 426 and set(metadata_by_id) == set(headers), 'Metadata 426 source identity differs')
    field_keys = {'video_id', 'source_frame', 'source_path', 'source_width', 'source_height', 'source_n_frames', 'fps', 'target_ratio_wh'}
    for (source, frame), selected in all_selected.items():
        meta = metadata_by_id[source]
        ratio = meta['targetRatioWH'] if isinstance(meta['targetRatioWH'], list) else list(map(int, meta['targetRatioWH'].split()))
        require(set(selected) == field_keys and 0 <= frame < meta['n_frames'] and
                selected['source_path'] == meta['source_path'] and selected['source_width'] == meta['width'] and
                selected['source_height'] == meta['height'] and selected['source_n_frames'] == meta['n_frames'] and
                selected['target_ratio_wh'] == ratio and abs(selected['fps'] - meta['fps_num'] / meta['fps_den']) <= 1e-6,
                'Unchanged selected frame/source geometry differs from frozen metadata')
    by_source = {source: [] for source in headers}
    for (source, _), prediction in sorted(all_frames.items()):
        by_source[source].append(prediction)
    predictions = [dict(headers[source], predictions=by_source[source]) for source in sorted(headers)]
    digest = canonical(predictions)
    history = read(checked(inputs['history_ref']))
    history_rows = history['records'] if isinstance(history, dict) else history
    require(isinstance(history_rows, list) and len(history_rows) == 25, '25 actual historical records required, retaining their genuine duplicates')
    historical = {value['canonical_SHA256'] for value in history_rows}
    require(len(historical) == 23 and {value['receipt']['canonical_SHA256'] for value in current.values()} <= historical,
            '25 records/23 canonical identities must include the four current delivered packages')
    require(digest not in historical and digest != canonical(baseline), 'Union is an unchanged/duplicate actual prediction; no preview ZIP may be counted or renamed')
    differences = {}
    for arm, source in current.items():
        keys = set(source['frames'])
        added, removed = set(all_frames) - keys, keys - set(all_frames)
        require(added or removed, 'Union must differ by actual native frames from each existing delivered package')
        require(all(all_frames[key]['bboxes'] == source['frames'][key]['bboxes'] for key in keys & set(all_frames)),
                'A common original current-package box changed')
        differences[arm] = dict(added_native_frames=len(added), removed_native_frames=len(removed))
    # One new format/provenance validator invocation, only after composition.
    old_lock = read(checked(original['old_source_package_lock_ref']))['files']
    validator = RUN / 'baseline_a_pts_v1/vendor/independent_validate.py'
    loader = RUN / 'baseline_a_pts_v1/vendor/frozen_strict_loader'
    for path in [validator, *loader.rglob('*.py')]:
        require(str(path) in old_lock, 'Original independent strict validator is not frozen')
        checked(dict(path=str(path), sha256=old_lock[str(path)]))
    OUT.mkdir(exist_ok=False)
    require(OUT.resolve() == OUT and not OUT.is_symlink(), 'Review output cannot redirect into another directory')
    try:
        save(OUT / 'started.json', dict(pid=os.getpid(), UTC=dt.datetime.now(dt.timezone.utc).isoformat(),
             publication_authorized=False, model_calls=0, first_QA_operations=0))
        write_rows(OUT / MEMBER, predictions)
        write_rows(OUT / 'selected.jsonl', [all_selected[key] for key in sorted(all_selected)])
        write_rows(OUT / 'provenance.jsonl', [all_provenance[key] for key in sorted(all_provenance)])
        save(OUT / 'metadata.json', metadata)
        temporary = OUT / 'candidate_MIDNIGHT_SEMANTIC_UNION_RISK.PENDING.zip'
        info = zipfile.ZipInfo(MEMBER, date_time=(2026, 10, 15, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        with zipfile.ZipFile(temporary, 'x') as archive:
            archive.writestr(info, (OUT / MEMBER).read_bytes())
        subprocess.run([sys.executable, '-B', str(validator), '--strict-loader-root', str(loader),
            '--metadata', str(OUT / 'metadata.json'), '--selected', str(OUT / 'selected.jsonl'),
            '--predictions', str(OUT / MEMBER), '--provenance', str(OUT / 'provenance.jsonl'),
            '--zip', str(temporary), '--report', str(OUT / 'independent_validation.json')], check=True,
            stdout=subprocess.DEVNULL, env={**os.environ, 'CUDA_VISIBLE_DEVICES': '', 'PYTHONDONTWRITEBYTECODE': '1'})
        report = read(OUT / 'independent_validation.json')
        require(report['status'] == 'PASS_INDEPENDENT_STRICT_VALIDATION' and len(report['checks']) == 11 and
                all(value is True for value in report['checks'].values()) and report['video_records'] == 426 and
                report['prediction_frames'] == len(all_frames) and report['duplicate_frames'] == 0 and
                report['missing'] == report['extra'] == 0 and
                report['zip_sha256'] == sha(temporary) and report['predictions_sha256'] == sha(OUT / MEMBER) and
                report['provenance_sha256'] == sha(OUT / 'provenance.jsonl'), 'New union independent 11-strict failed')
        archived, member_sha = predictions_from_archive(temporary)
        require(archived == predictions and member_sha == sha(OUT / MEMBER) and canonical(archived) == digest,
                'New preview single-member CRC/member SHA/canonical roundtrip failed')
        for source in current.values():
            checked(source['receipt_ref'])
            require(sha(source['archive']) == source['receipt']['SHA256'], 'Original four ZIPs changed during preview')
        checked(original_ref)
        final = OUT / 'candidate_MIDNIGHT_SEMANTIC_UNION_RISK.zip'
        temporary.rename(final)
        receipt = dict(status='PASS_ENGINEERING_PREVIEW_ONLY_PUBLICATION_NOT_AUTHORIZED',
            publication_authorized=False, maximum_previous_risk_count=3, proposed_risk_count=4,
            original4unchanged=True, no_new_modelcalls=True, new_model_calls=0, new_media_decodes=0,
            new_processor_calls=0, first_input_QA_repeated=False, first_output_QA_repeated=False,
            adopted_proof_validation_only=True, quality_pass_claimed=False, risk_effect_quality_screening_performed=False,
            official_effect='UNKNOWN', official_score='UNKNOWN', published=False, counted_as_fifth_delivery=False,
            windows_delivery_performed=False, actual_parameters=PARAMETERS, production_evidence_counts=counts,
            production_completion_ref=production_ref, original_package_inputs_ref=original_ref,
            source_package_refs=component_refs, current_four_package_refs=refs, history_ref=inputs['history_ref'],
            preview_inputs_ref=ref(INPUTS), zip=str(final), bytes=final.stat().st_size, SHA256=sha(final),
            member_SHA256=member_sha, canonical_SHA256=digest, records=426, frame_count=len(all_frames),
            baseline_frames=122002, added_native_frames_vs_baseline=len(set(all_frames)-set(baseline_frames)),
            removed_native_frames_vs_baseline=0, kept_baseline_boxes_exact=True, overlapping_rows_and_boxes_exact=True,
            native_frame_ordinals_changed=False, no_new_spatial_inference=True, differences_vs_current_four=differences,
            independent11strict=True, independent_validation_ref=ref(OUT / 'independent_validation.json'),
            historical_records=25, distinct_historical_canonical=23,
            union_rule='UNWEIGHTED_EXACT_NATIVE_KEY_UNION_OF_ACTION_REACTION_INFORMATION_ONLY',
            UTC=dt.datetime.now(dt.timezone.utc).isoformat())
        save(OUT / 'review_receipt.json', receipt)
        print(json.dumps(receipt), flush=True)
    except BaseException as error:
        if not (OUT / 'failure.json').exists():
            save(OUT / 'failure.json', dict(status='FAILED_REVIEW_ONLY_NOT_PUBLISHED', error=repr(error),
                 publication_authorized=False, keep_all_original_packages=True, automatic_retry=False))
        raise


if __name__ == '__main__':
    main()
