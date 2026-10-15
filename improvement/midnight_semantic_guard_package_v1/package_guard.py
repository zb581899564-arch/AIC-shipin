"""Independent remaining REDUNDANT renderer after new supplemental confirmation.

Only the new authorized root is writable.  No launcher, model, media decoder,
optimizer, remote connection or metric-based risk-arm selection is present.
"""
import argparse
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

from package_math import (ARMS, QUALITY_ARMS, RISK_ARMS, combine, deterministic_policy_for,
                          require, validate_deletion_policy_map)
from production_evidence import validate_production_evidence
from production_evidence import same_ref
from supplement_quality import SCOPE, validate_quality

HOME = Path('/home/inspur/aic_video_work')
ROOT = HOME / 'midnight_five_verify40_46_20261015_v1'
INPUTS_FILE = ROOT / 'package_inputs_pair_supplement.json'
QUALITY_FILE = ROOT / 'quality_admission_pair_supplement.json'
ORIGINAL_INPUTS_FILE = ROOT / 'package_inputs.json'
ORIGINAL_QUALITY_FILE = ROOT / 'quality_admission.json'
ORIGINAL_CONFIRMATION_FILE = ROOT / 'relative_confirm/policy_fresh_comparison.json'
PRODUCTION_FILE = ROOT / 'production_unique_09/completion.json'
PUBLICATION_FILE = ROOT / 'publication_protocol_13.json'
EXISTING_ARMS = frozenset(('ORDINARY', 'ACTION', 'REACTION', 'INFORMATION'))
EXPECTED_COUNTS = dict(logical_cases=519, actual_model_calls=518, adopted_identical_input_aliases=1,
                       first_model_output_QA_count=518, alias_application_QA_count=1)
OLD = HOME / 'twenty_hour_five_20261014_v1/temporal_family_native_package_v3'
RUN = HOME / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PARAMETERS = 8782459120
BASELINE_SHA = '86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543'
BASELINE_BYTES = 380199
BASELINE_FRAMES = 122002


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


def save(path, value):
    with Path(path).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def write(path, values):
    with Path(path).open('x', encoding='utf8') as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')
        stream.flush(); os.fsync(stream.fileno())


def ref_path(ref, lock=None):
    require(isinstance(ref, dict) and isinstance(ref.get('path'), str) and isinstance(ref.get('sha256'), str), 'Missing path/SHA256 reference')
    path = Path(ref['path'])
    require(path.is_absolute() and path.resolve().is_relative_to(HOME), 'Reference escaped Linux work root')
    require(lock is None or lock.get(str(path)) == ref['sha256'], 'Reference absent from original source lock: ' + str(path))
    require(sha(path) == ref['sha256'], 'Referenced bytes changed: ' + str(path))
    if 'bytes' in ref:
        require(path.stat().st_size == ref['bytes'], 'Referenced size changed: ' + str(path))
    return path


def canonical(values):
    relevant = [{key: value[key] for key in ('video_id', 'targetRatioWH', 'predictions')}
                for value in sorted(values, key=lambda value: value['video_id'])]
    return hashlib.sha256(json.dumps(relevant, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def unzip_predictions(path):
    with zipfile.ZipFile(path) as archive:
        require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None, 'Archive single member or CRC failed')
        return [json.loads(line) for line in archive.read('predictions.jsonl').splitlines() if line.strip()]


def checked_inputs():
    require(sys.platform == 'linux' and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Linux CPU-only packaging required')
    require(Path(__file__).resolve().is_relative_to(ROOT), 'Only independent new campaign code may execute')
    input_path = INPUTS_FILE
    inputs = read(input_path)
    names = ('old_package_inputs_ref', 'old_source_package_lock_ref', 'protected_baseline_zip_ref',
             'production_completion_ref', 'history_ref', 'protocol_ref', 'authorization_ref',
             'official_rule_check_ref', 'package_admission_ref', 'original_package_inputs_ref',
             'original_quality_admission_ref', 'quality_admission_ref')
    paths = {name: ref_path(inputs[name]) for name in names}
    require(paths['old_package_inputs_ref'] == OLD / 'package_inputs.json' and
            paths['old_source_package_lock_ref'] == OLD / 'source_package_lock.json' and
            paths['protected_baseline_zip_ref'] == OLD / 'package_VERIFY/candidate_TEMPORAL_VERIFY.zip', 'Protected original roots changed')
    require(paths['original_package_inputs_ref'] == ORIGINAL_INPUTS_FILE and
            paths['original_quality_admission_ref'] == ORIGINAL_QUALITY_FILE and
            paths['quality_admission_ref'] == QUALITY_FILE and
            paths['production_completion_ref'] == PRODUCTION_FILE and paths['protocol_ref'] == PUBLICATION_FILE,
            'Supplement must use distinct new inputs/quality files and the exact original production/publication')
    original_inputs = read(paths['original_package_inputs_ref'])
    for name in ('old_package_inputs_ref', 'old_source_package_lock_ref', 'protected_baseline_zip_ref',
                 'production_completion_ref', 'protocol_ref'):
        same_ref(inputs[name], original_inputs[name], 'Original frozen production or baseline binding changed: ' + name)
    baseline_path = paths['protected_baseline_zip_ref']
    require(sha(baseline_path) == BASELINE_SHA and baseline_path.stat().st_size == BASELINE_BYTES, 'Protected 40.46 original ZIP changed')
    code_files = inputs['code_files']
    require({str(Path(__file__).resolve()), str(Path(__file__).with_name('package_math.py').resolve()),
             str(Path(__file__).with_name('production_evidence.py').resolve()),
             str(Path(__file__).with_name('supplement_quality.py').resolve())} <= set(code_files), 'New CPU code is not bound')
    for path, digest in code_files.items():
        require(Path(path).resolve().is_relative_to(ROOT), 'New code lock escaped independent root')
        ref_path(dict(path=path, sha256=digest))
    permit = read(paths['package_admission_ref'])
    require(permit['status'] == 'PASS_NEW_FIVE_WAY_CPU_PACKAGE_ENGINEERING_ADMISSION' and
            permit['actual_parameters'] == PARAMETERS and
            permit['production_completion_sha256'] == inputs['production_completion_ref']['sha256'] and
            permit['automatic_removal_and_recall_authorized'] is True and
            permit['three_risk_arms_without_offline_quality_screening'] is True and
            permit['test_labels_or_manual_edits_used'] is False and
            permit['current_official_rules_rechecked'] is True and
            permit['history_complete_for_all_preexisting_deliveries'] is True, 'Current authorization/engineering admission incomplete')
    same_ref(permit['original_package_inputs_ref'], inputs['original_package_inputs_ref'], 'Supplement permit must protect original frozen inputs')
    same_ref(permit['original_quality_admission_ref'], inputs['original_quality_admission_ref'], 'Supplement permit must protect original failed quality admission')
    same_ref(permit['supplementary_quality_admission_ref'], inputs['quality_admission_ref'], 'Supplement permit must bind its own new quality admission')
    existing_refs = inputs['existing_four_package_refs']
    require(isinstance(existing_refs, list) and len(existing_refs) == 4 and
            permit['existing_four_package_refs'] == existing_refs, 'Supplement permit must bind all four actually published packages')
    existing = {}
    for reference in existing_refs:
        path = ref_path(reference)
        receipt = read(path)
        arm = receipt['arm']
        require(arm in EXISTING_ARMS and arm not in existing and
                path == ROOT / 'packages' / ('package_' + arm) / 'completion.json',
                'Exactly ORDINARY and three existing risk receipts must be preserved')
        existing[arm] = receipt
    require(set(existing) == EXISTING_ARMS, 'Four previous successful packages are incomplete')
    protocol = read(paths['protocol_ref'])
    require(protocol['arms'] == list(ARMS) and protocol['empty_source_guard'] == 'PRESERVE_ORIGINAL_VERIFY40_46_SOURCE_SELECTION' and
            protocol['test_content_or_leaderboard_parameter_selection'] is False, 'Frozen five-arm recipe changed')
    deletion_policy_map = protocol.get('deletion_application_policy')
    validate_deletion_policy_map(deletion_policy_map)
    require(deletion_policy_map is not None and deletion_policy_map['REDUNDANT'] == 'WORST_PAIR_ONLY',
            'Supplement applies only the unchanged original WORST_PAIR_ONLY policy')
    completion = read(paths['production_completion_ref'])
    entries = completion['entries']
    require(completion['status'] == 'COMPLETE_NEW_FIVE_WAY_INFERENCE_ENGINEERING_NOT_QUALITY' and
            completion['actual_parameters'] == PARAMETERS and completion['first_input_QA_complete'] is True and
            completion['first_output_QA_complete'] is True and
            entries and completion.get('engineering_failed_requests', 0) == 0 and
            completion.get('missing_requests', 0) == 0, 'Real complete new production and first QA required')
    ref_path(completion['unique_gpu_terminal_ref'])
    accepted_entries, evidence_counts = validate_production_evidence(
        completion, lambda reference: read(ref_path(reference)), PARAMETERS)
    original_permit = read(ref_path(original_inputs['package_admission_ref']))
    require(evidence_counts == permit['production_evidence_counts'] == original_permit['production_evidence_counts'] == EXPECTED_COUNTS,
            'Supplement must adopt exactly the original successful 518 calls and one alias, without another call or QA')
    old_inputs, old_lock = read(paths['old_package_inputs_ref']), read(paths['old_source_package_lock_ref'])['files']
    refs = {name: ref_path(old_inputs[name], old_lock) for name in
            ('events', 'endpoints', 'verification', 'source_clocks', 'metadata', 'source_manifest')}
    structural_skips = completion.get('structural_skips', [])
    require(isinstance(structural_skips, list), 'Structural skips must be explicitly enumerated')
    for skip in structural_skips:
        old_ref = skip['old_decision_ref']
        require(old_ref['path'] == old_inputs['verification']['path'] and
                old_ref['sha256'] == old_inputs['verification']['sha256'] and
                ref_path(old_ref, old_lock) == refs['verification'], 'Structural skip is not bound to the actual frozen old verification export')
    field = {name: ref_path(ref, old_lock) for name, ref in old_inputs['source_field_files'].items()}
    require(set(field) == {'field_frames.jsonl', 'field_shots.jsonl', 'anchor_requests.jsonl', 'anchor_output.jsonl'}, 'Complete original continuous spatial field required')
    # Reuse only pure existing helpers, never an old launcher or package entry.
    dependencies = (RUN / 'b_score_aligned_package_v4', RUN / 'baseline_a_pts_v1', RUN / 'baseline_a_pts_v1/vendor')
    dependency_code = {path for directory in dependencies for path in directory.glob('*.py')}
    dependency_code.update((RUN / 'baseline_a_pts_v1/vendor/frozen_strict_loader').rglob('*.py'))
    helper = OLD / 'code/combine_events.py'
    dependency_code.add(helper)
    for path in dependency_code:
        require(str(path) in old_lock, 'Reused Python dependency absent from original lock: ' + str(path))
        ref_path(dict(path=str(path), sha256=old_lock[str(path)]), old_lock)
    return inputs, paths, permit, accepted_entries, structural_skips, refs, field, helper, dependencies, deletion_policy_map, evidence_counts, existing


def expected_events(refs, helper_path):
    spec = importlib.util.spec_from_file_location('frozen_original_verify_math', helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    events, endpoints, verification = (read(refs[name]) for name in ('events', 'endpoints', 'verification'))
    require(len(events) == 665 and len({event['event_id'] for event in events}) == 665, 'Original 665 candidate denominator changed')
    result = {}
    for event in events:
        value = helper.candidate(event, endpoints, verification, 'VERIFY')
        old = verification[event['event_id']]
        no64 = (old.get('actual_model_call') is False and
                old.get('applied_decision') == 'UNKNOWN_SHORT_ORIGINAL_VISUAL_CONTEXT_UNAVAILABLE' and
                old.get('predeclared_skip') is True and old.get('declared_before_model') is True and
                type(old.get('original_visual_sample_count')) is int and 0 < old['original_visual_sample_count'] < 64 and
                old.get('required_distinct_native_frames') == 64 and old.get('successful_model_call_required') is False and
                old.get('verify_view_kind') == 'PREDECLARED_SHORT_ORIGINAL_VIEW_NO_MODEL_CONTEXT' and
                old.get('decision') == 'UNKNOWN')
        result[event['event_id']] = dict(source_id=event['source_id'], original_interval_exact=value['original_interval_exact'],
            selected_interval_exact=value['selected_interval_exact'], decision=value['verification_decision'],
            original_case_id=old['original_case_id'], old_structural_no64=no64)
    require(sum(value['old_structural_no64'] for value in result.values()) == 1,
            'Frozen original single NO64 structural witness changed')
    return result


def admitted_quality_arm(arm, expected_policy, protocol_ref, inputs):
    """Read only the separate new supplemental admission, keeping old FAIL."""
    require(arm == 'REDUNDANT' and expected_policy == 'WORST_PAIR_ONLY', 'Only the remaining frozen pair policy may be published')
    path = QUALITY_FILE
    if not path.exists():
        return False, 'QUALITY_ADMISSION_ABSENT'
    require(ref_path(inputs['quality_admission_ref']) == path, 'New supplemental quality bytes changed')
    admission = read(path)
    require(set(admission['arms']) == {'REDUNDANT'}, 'Supplemental admission is scoped only to REDUNDANT')
    value = admission.get('arms', {}).get(arm, {})
    if value.get('status') != 'PASS':
        return False, 'QUALITY_ARM_NOT_PASS'
    require(value.get('reference_scope'), 'Quality PASS must declare external reference scope')
    for name in ('development_ref', 'confirmation_ref', 'frozen_rule_ref'):
        ref_path(value[name])
    frozen = value['frozen_rule_ref']
    require(frozen['path'] == protocol_ref['path'] and frozen['sha256'] == protocol_ref['sha256'],
            'Quality PASS is bound to another frozen policy protocol')
    require(value.get('deterministic_deletion_policy') == expected_policy and
            value.get('actual_model_parsed_unchanged') is True,
            'Quality PASS does not admit this exact deterministic policy over unchanged actual model answers')
    require(value.get('independent_confirmation') is True and value.get('test_labels_used') is False,
            'Quality PASS needs independent non-test confirmation')
    require(Path(value['original_nonapplicable_confirmation_ref']['path']) == ORIGINAL_CONFIRMATION_FILE,
            'The original nonapplicable four-source result may not be substituted')
    scope = validate_quality(value, read(ref_path(inputs['original_quality_admission_ref'])),
                             protocol_ref, read(ref_path(protocol_ref)), lambda reference: read(ref_path(reference)))
    return True, dict(path=str(path), sha256=sha(path), arm=arm, reference_scope=value['reference_scope'],
                      deterministic_deletion_policy=expected_policy, actual_model_parsed_unchanged=True, supplemental_evidence=scope)


def existing_packages(package_root):
    results = []
    if not package_root.exists():
        return results
    for path in sorted(package_root.glob('package_*/completion.json')):
        value = read(path)
        require(value['arm'] in ARMS and value['records'] == 426 and value['independent11strict'] is True and
                value['actual_parameters'] == PARAMETERS, 'Existing new-package completion malformed')
        archive = Path(value['zip'])
        require(archive.parent == path.parent and archive.resolve().is_relative_to(ROOT), 'Existing package path escaped new root')
        require(archive.stat().st_size == value['bytes'] and sha(archive) == value['SHA256'] and
                canonical(unzip_predictions(archive)) == value['canonical_SHA256'], 'Existing successfully packaged bytes changed')
        results.append(value)
    require(len({value['arm'] for value in results}) == len(results) and
            len({value['canonical_SHA256'] for value in results}) == len(results), 'Existing five-arm packages duplicate')
    return results


def main(requested):
    require(requested == ['REDUNDANT'], 'This independent entry may publish only the remaining REDUNDANT arm')
    remaining_directory = ROOT / 'packages/package_REDUNDANT'
    require(not remaining_directory.exists(), 'Remaining REDUNDANT directory already exists; never overwrite, resume, or repeat it')
    inputs, paths, permit, entries, structural_skips, refs, field_paths, helper, dependencies, deletion_policy_map, evidence_counts, existing = checked_inputs()
    package_root = ROOT / 'packages'
    package_root.mkdir(exist_ok=True)
    require(not package_root.is_symlink() and package_root.resolve().is_relative_to(ROOT), 'Output directory escaped independent new root')
    require(not (package_root / '.package.lock').is_symlink(), 'Output lock may not redirect writes')
    import fcntl
    with (package_root / '.package.lock').open('a') as process_lock:
        fcntl.flock(process_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not remaining_directory.exists(), 'Remaining REDUNDANT directory appeared before locked publication; stop without overwrite')
        baseline = unzip_predictions(paths['protected_baseline_zip_ref'])
        baseline_boxes = {(value['video_id'], prediction['frame']): prediction['bboxes']
                          for value in baseline for prediction in value['predictions']}
        baseline_keys = set(baseline_boxes)
        source_ids = {str(index) for index in range(426)}
        require(len(baseline) == 426 and {value['video_id'] for value in baseline} == source_ids and
                len(baseline_keys) == BASELINE_FRAMES and all(value['predictions'] for value in baseline), 'Protected 426/nonempty/122002 membership changed')
        clocks = read(refs['source_clocks'])
        require(set(clocks) == source_ids, 'Full original source-clock denominator changed')
        choices = combine(entries, baseline_keys, clocks, expected_events(refs, helper), structural_skips,
                          deletion_policy_map=deletion_policy_map)
        history_rows = read(paths['history_ref'])
        if isinstance(history_rows, dict):
            history_rows = history_rows['records']
        require(isinstance(history_rows, list) and history_rows, 'Actual full historical predictions are not registered')
        require(len(history_rows) == 25, 'Supplement history must include 21 old and all four current deliveries')
        history = set()
        for value in history_rows:
            digest = value['canonical_SHA256']
            require(isinstance(digest, str) and len(digest) == 64, 'Historical prediction digest malformed')
            if 'zip_ref' in value:
                require(canonical(unzip_predictions(ref_path(value['zip_ref']))) == digest, 'History digest differs from actual old predictions')
            history.add(digest)
        require(len(history) == 23 and {value['canonical_SHA256'] for value in existing.values()} <= history,
                'Actual 25 historical records with 23 distinct canonical predictions, including the four current packages, must be bound')
        history.add(canonical(baseline))
        published = existing_packages(package_root)
        published_by_arm = {value['arm']: value for value in published}
        require(set(published_by_arm) == set(EXISTING_ARMS) and
                all(published_by_arm[arm] == receipt for arm, receipt in existing.items()),
                'Supplement must preserve the existing four successful packages without recreating or replacing them')
        history.update(value['canonical_SHA256'] for value in published)
        done_arms = {value['arm'] for value in published}
        skipped, pending = [], []
        quality_bindings = {}
        for arm in requested:
            if arm in done_arms:
                skipped.append(dict(arm=arm, status='ALREADY_SUCCESSFUL_NOT_REPEATED'))
                continue
            if arm in QUALITY_ARMS:
                try:
                    okay, binding = admitted_quality_arm(arm, deterministic_policy_for(arm, deletion_policy_map), inputs['protocol_ref'], inputs)
                except (KeyError, ValueError, OSError) as error:
                    okay, binding = False, 'INVALID_QUALITY_ADMISSION: ' + str(error)
                if not okay:
                    skipped.append(dict(arm=arm, status='NOT_PUBLISHABLE_WITHOUT_QUALITY_PASS', reason=binding))
                    continue
                quality_bindings[arm] = binding
            if choices[arm]['selected_keys'] == baseline_keys:
                skipped.append(dict(arm=arm, status='NOT_PUBLISHABLE_UNCHANGED_ACTUAL_PREDICTIONS'))
                continue
            pending.append(arm)
        if pending:
            metadata, manifest = read(refs['metadata']), read(refs['source_manifest'])
            by_id = {value['video_id']: value for value in metadata['records']}
            manifest_by_id = {value['video_id']: value for value in manifest['records']}
            require(len(by_id) == len(metadata['records']) == len(manifest_by_id) == len(manifest['records']) == 426 and
                    set(by_id) == set(manifest_by_id) == source_ids, 'Original metadata/source-manifest identities differ')
            fields = ('video_id', 'source_path', 'source_sha256', 'width', 'height', 'n_frames', 'fps_num', 'fps_den', 'targetRatioWH')
            require(all(all(by_id[source][key] == manifest_by_id[source][key] for key in fields) and
                        len(clocks[source]['normalized_exact_pts']) == by_id[source]['n_frames'] and
                        clocks[source]['source_sha256'] == by_id[source]['source_sha256'] and
                        clocks[source]['source_path'] == by_id[source]['source_path'] for source in source_ids), 'Original source geometry/count/clock binding changed')
            field = rows(field_paths['field_frames.jsonl'])
            field_by_key = {(value['video_id'], value['source_frame']): value for value in field}
            require(len(field_by_key) == len(field), 'Duplicate accepted spatial field frame')
            all_selected = set().union(*(choices[arm]['selected_keys'] for arm in pending))
            require(all_selected <= set(field_by_key), 'New frame outside accepted continuous source field')
            sys.path[:0] = [str(path) for path in dependencies]
            from field_contract import compose_from_field
            from pts_contract import legacy_manifest
            composed, provenance = compose_from_field(legacy_manifest(manifest), [field_by_key[key] for key in sorted(all_selected)],
                rows(field_paths['field_shots.jsonl']), rows(field_paths['anchor_requests.jsonl']), rows(field_paths['anchor_output.jsonl']))
            provenance_by_key = {(value['video_id'], value['source_frame']): value for value in provenance}
            composed_boxes = {(value['video_id'], prediction['frame']): prediction['bboxes']
                              for value in composed for prediction in value['predictions']}
            require(set(composed_boxes) == all_selected and all(composed_boxes[key] == baseline_boxes[key] for key in all_selected & baseline_keys),
                    'A retained protected 40.46 frame box changed')
            for arm in pending:
                require(len(published) < 5, 'New five-package publication limit reached')
                selection = choices[arm]; keys = selection['selected_keys']
                predictions = [dict(video_id=value['video_id'], targetRatioWH=value['targetRatioWH'], model_params_b=PARAMETERS / 1e9,
                                    predictions=[prediction for prediction in value['predictions'] if (value['video_id'], prediction['frame']) in keys]) for value in composed]
                require(len(predictions) == 426 and all(value['predictions'] for value in predictions), 'New package must contain 426 nonempty sources')
                digest = canonical(predictions)
                if digest in history:
                    skipped.append(dict(arm=arm, status='NOT_PUBLISHABLE_DUPLICATE_ACTUAL_PREDICTIONS', canonical_SHA256=digest))
                    continue
                out = package_root / ('package_' + arm)
                out.mkdir(exist_ok=False)
                write(out / 'selected.jsonl', [field_by_key[key] for key in sorted(keys)])
                write(out / 'predictions.jsonl', predictions)
                write(out / 'provenance.jsonl', [provenance_by_key[key] for key in sorted(keys)])
                save(out / 'metadata.json', metadata)
                audit = {key: value for key, value in selection.items() if key != 'selected_keys'}
                save(out / 'automatic_decisions.json', dict(arm=arm, **audit))
                temporary = out / ('candidate_MIDNIGHT_' + arm + '.PENDING.zip')
                with zipfile.ZipFile(temporary, 'x', zipfile.ZIP_DEFLATED) as archive:
                    archive.write(out / 'predictions.jsonl', 'predictions.jsonl')
                subprocess.run([sys.executable, '-B', str(RUN / 'baseline_a_pts_v1/vendor/independent_validate.py'),
                    '--strict-loader-root', str(RUN / 'baseline_a_pts_v1/vendor/frozen_strict_loader'),
                    '--metadata', str(out / 'metadata.json'), '--selected', str(out / 'selected.jsonl'),
                    '--predictions', str(out / 'predictions.jsonl'), '--provenance', str(out / 'provenance.jsonl'),
                    '--zip', str(temporary), '--report', str(out / 'independent_validation.json')], check=True, stdout=subprocess.DEVNULL,
                    env={**os.environ, 'CUDA_VISIBLE_DEVICES': '', 'PYTHONDONTWRITEBYTECODE': '1'})
                validation = read(out / 'independent_validation.json')
                require(len(validation['checks']) == 11 and all(validation['checks'].values()) and
                        validation['status'] == 'PASS_INDEPENDENT_STRICT_VALIDATION' and validation['video_records'] == 426 and
                        validation['prediction_frames'] == len(keys) and validation['duplicate_frames'] == 0 and
                        validation['zip_sha256'] == sha(temporary) and validation['predictions_sha256'] == sha(out / 'predictions.jsonl'), 'Independent11strict failed')
                member_sha = sha(out / 'predictions.jsonl')
                with zipfile.ZipFile(temporary) as archive:
                    require(archive.namelist() == ['predictions.jsonl'] and archive.testzip() is None and
                            hashlib.sha256(archive.read('predictions.jsonl')).hexdigest() == member_sha, 'Single JSONL/CRC/member SHA failed')
                # Publication must still bind the unchanged original files and
                # this separate new supplemental quality admission.
                ref_path(inputs['original_package_inputs_ref']); ref_path(inputs['original_quality_admission_ref'])
                ref_path(inputs['quality_admission_ref'])
                final = out / ('candidate_MIDNIGHT_' + arm + '.zip')
                temporary.rename(final)
                receipt = dict(status='PASS_NEW_DISTINCT_FIVE_WAY_ENGINEERING_ZIP_NOT_OFFICIAL_SCORE', arm=arm,
                    zip=str(final), bytes=final.stat().st_size, SHA256=sha(final), member_SHA256=member_sha, canonical_SHA256=digest,
                    records=426, frame_count=len(keys), added_frames=selection['added_frames'], removed_frames=selection['removed_frames'],
                    empty_source_format_guard=selection['empty_source_format_guard'], retained_original_boxes_exact=True,
                    new_frames_from_accepted_continuous_field=True, new_spatial_model_calls=0, independent11strict=True,
                    independent_validation_sha256=sha(out / 'independent_validation.json'), actual_parameters=PARAMETERS,
                    production_completion_ref=inputs['production_completion_ref'], package_inputs_sha256=sha(INPUTS_FILE),
                    actual_new_model_calls=evidence_counts['actual_model_calls'], **evidence_counts,
                    structural_skip_records=len(structural_skips),
                    protected_baseline_SHA256=BASELINE_SHA, quality_pass_claimed=arm in QUALITY_ARMS,
                    quality_admission_ref=quality_bindings.get(arm), risk_quality_screening_performed=False if arm in RISK_ARMS else None,
                    old_scientific_gates_changed=False, official_score='UNKNOWN', model_calls_in_packaging=0, website_submitted=False)
                if arm in QUALITY_ARMS:
                    receipt.update(actual_model_parsed_unchanged=selection['actual_model_parsed_unchanged'],
                                   deterministic_deletion_policy=selection['deterministic_deletion_policy'])
                receipt.update(supplemental_scope_only=True, reference_scope_kind=SCOPE,
                    original_package_inputs_ref=inputs['original_package_inputs_ref'],
                    original_quality_admission_ref=inputs['original_quality_admission_ref'],
                    supplementary_quality_admission_ref=inputs['quality_admission_ref'],
                    existing_four_package_refs=inputs['existing_four_package_refs'],
                    old_result_unchanged=True, policy_and_gates_unchanged=True,
                    original_failed_confirmation_promoted=False, previous_four_packages_repeated=False)
                scope = quality_bindings[arm]['supplemental_evidence']
                receipt.update(original_nonapplicable_confirmation_ref=scope['original_nonapplicable_confirmation_ref'],
                               supplemental_confirmation_ref=scope['supplemental_confirmation_ref'])
                save(out / 'completion.json', receipt)
                history.add(digest); published.append(receipt)
                print(json.dumps(dict(event='NEW_READY', **receipt)), flush=True)
        result = dict(status='COMPLETE_REQUESTED_AVAILABLE_DISTINCT_FIVE_WAY_PACKAGES', requested_arms=requested,
                      packages=published, unpublished=skipped, actual_packages=len(published), required_packages=5,
                      production_evidence_counts=evidence_counts,
                      all_five_engineering_packages_ready=len(published) == 5, official_score='UNKNOWN', goal_complete_claimed=False)
        result.update(supplemental_scope_only=True, original_failed_confirmation_promoted=False,
                      previous_four_packages_repeated=False, only_new_publication_arm='REDUNDANT')
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
        save(package_root / ('run_' + stamp + '_' + str(os.getpid()) + '.json'), result)
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arms', nargs='+', default=['REDUNDANT'], help='Only REDUNDANT is accepted')
    args = parser.parse_args()
    requested = [arm.upper() for group in args.arms for arm in group.split(',')]
    require(requested == ['REDUNDANT'], 'Only REDUNDANT is accepted by the independent supplement entry')
    main(requested)
